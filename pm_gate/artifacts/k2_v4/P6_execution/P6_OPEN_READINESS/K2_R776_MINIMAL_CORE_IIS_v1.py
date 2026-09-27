#!/usr/bin/env python3
"""K2 R776 --- #K2-301 sec.2 : ONE minimal-conflict-core (IIS) extraction on the EXACT declared model
of R774 (revised mirror-complete gate set x declared candidate family), re-using the SAME exact solver
(HiGHS via scipy.optimize.milp) to re-verify infeasibility at every step.

Method (bounded by #constraints):
  step 0  verify the full model is infeasible (reference).
  step 1  coarse pass -- remove the WHOLE cell-constraint family; if still infeasible the cell rows
          are NOT needed by the core.
  step 2  deletion filter over the GATE constraints (one at a time, re-solve each step).
  step 3  deletion filter over the LANE constraints (one at a time, re-solve each step).
  step 4  irreducibility proof: for every constraint in the extracted core, removing it singly makes
          the model FEASIBLE.
  step 5  named census: reachable vs declared-but-unroutable openings; routable corridors not declared.
  step 6  targeted reading: minimise the number of EXTRA openings used (one MILP) -> the minimal
          opening change that dissolves the deadlock; emit the 16/16 witness.
"""
import sys, os, json, types, importlib, hashlib, time, collections
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix, vstack

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "K2_R776_MINIMAL_CORE_IIS_v1.json")
LOGF = os.path.join(HERE, "K2_R776_solve.log")
LH = open(LOGF, "w")
def log(m): LH.write(str(m)+"\n"); LH.flush(); print(str(m), flush=True)

for nm in ("ortools","ortools.sat","ortools.sat.python"): sys.modules.setdefault(nm, types.ModuleType(nm))
cm = types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self, *a, **k): pass
cm.CpModel = _D; cm.CpSolver = _D
sys.modules["ortools.sat.python.cp_model"] = cm; sys.modules["ortools.sat.python"].cp_model = cm
M = importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1"); PREV = M.PREV; PREV.Gen._build_edges = M._build_edges_fixed
W = M.W; NID = W.NID
def rc(u): u %= NID; return u // W.NY, u % W.NY

def load_ctx():
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full"); names = list(g2.names)
    T = json.load(open(os.path.join(HERE,"K2_R613_FINAL_TABLE_VIA_OK_v1.json")))["per_lane"]
    REG = json.load(open(os.path.join(HERE,"K2_L1_A_EXIT_REGISTRATION_REVISION_v1.json")))
    EL = {nm: int(T[nm]["exit_layer"]) for nm in names}
    node_ok={}; via_ok={}
    for nm in names:
        node_ok[nm]={L:{rc(i) for i in np.nonzero(g2._nok[(nm,L)] & g2.region_ok(nm,L))[0]} for L in (0,1)}
        via_ok[nm]={rc(i) for i in np.nonzero(g2._viaok[nm])[0]}
    return names, EL, node_ok, via_ok, REG

def build(nm, gate, cl, t, Xt, H, EL, node_ok, via_ok):
    e_col,e_row=gate; eL=EL[nm]
    if H<=e_row+1: return None
    w=[(cl,(60,H))]; vias=[]
    if t!=cl:
        via=None
        for c in range(60,Xt+1):
            if all((cl,(x,H)) in node_ok[nm][cl] for x in range(60,c+1)) and (t,(c,H)) in node_ok[nm][t]: via=c; break
        if via is None: return None
        w+=[(cl,(x,H)) for x in range(61,via+1)]; w.append((t,(via,H))); vias.append((via,H))
        w+=[(t,(x,H)) for x in range(via+1,Xt+1)]
    else:
        w+=[(t,(x,H)) for x in range(61,Xt+1)]
    w+=[(t,(Xt,r)) for r in range(H-1,e_row,-1)]
    if t!=eL:
        vias.append((Xt,e_row)); w.append((t,(Xt,e_row)))
    w.append((eL,(Xt,e_row))); w+=[(eL,(x,e_row)) for x in range(Xt-1,e_col-1,-1)]
    if len(set(w))!=len(w) or w[-1]!=(eL,(e_col,e_row)): return None
    for (L,cp) in w:
        if cp not in node_ok[nm][L]: return None
    for cp in vias:
        if cp not in via_ok[nm]: return None
    return w

def gen_cands(gates, names, EL, node_ok, via_ok):
    cands=[]
    for nm in names:
        seen=set()
        for gate in gates:
            e_col,e_row=gate
            Xts=(list(range(116,138)) if e_col==114 else [e_col-3,e_col-2,e_col-1,e_col+1,e_col+2,e_col+3,e_col+4])
            for cl in (0,1):
                for t in (0,1):
                    for Xt in Xts:
                        if e_col!=114 and Xt<=e_col: continue
                        for H in range(e_row+2,60):
                            w=build(nm,gate,cl,t,Xt,H,EL,node_ok,via_ok)
                            if w is None: continue
                            k=frozenset(w)
                            if k in seen: continue
                            seen.add(k)
                            cands.append({"lane":nm,"gate":gate,"walk":w,"cells":k})
    return cands

def make_model(cands, names, keep_lanes=None, use_cells=True, keep_gates=None):
    """Build the sparse MILP data. Returns (A,lb,ub,N,meta). keep_* default = all."""
    if keep_lanes is None: keep_lanes=set(names)
    if keep_gates is None: keep_gates=set(tuple(c["gate"]) for c in cands)
    cells=sorted({cp for c in cands if c["lane"] in keep_lanes for cp in c["cells"]}) if use_cells else []
    jj=[j for j,c in enumerate(cands) if c["lane"] in keep_lanes]
    remap={j:i for i,j in enumerate(jj)}; N=len(jj)
    lane_by={nm:i for i,nm in enumerate(names)}
    rows=[]; lbs=[]; ubs=[]
    # lane rows (eq 1)
    for nm in names:
        if nm not in keep_lanes: continue
        r=lil_matrix((1,N))
        for j in jj:
            if cands[j]["lane"]==nm: r[0,remap[j]]=1.0
        rows.append(r.tocsr()); lbs.append(1.0); ubs.append(1.0)
    # cell rows (<=1) -- only cells touched by >=2 kept lanes (others are non-binding)
    if use_cells:
        cell_lanes=collections.defaultdict(set)
        for j in jj:
            for cp in cands[j]["cells"]: cell_lanes[cp].add(cands[j]["lane"])
        cellix={cp:i for i,cp in enumerate(sorted(cells))}
        for cp in cells:
            if len(cell_lanes[cp])<2: continue
            r=lil_matrix((1,N))
            for j in jj:
                if cp in cands[j]["cells"]: r[0,remap[j]]=1.0
            rows.append(r.tocsr()); lbs.append(0.0); ubs.append(1.0)
    # gate rows (<=1)
    gids=collections.defaultdict(list)
    for j in jj: gids[tuple(cands[j]["gate"])].append(j)
    for g in sorted(keep_gates):
        if not gids[g]: continue
        r=lil_matrix((1,N))
        for j in gids[g]: r[0,remap[j]]=1.0
        rows.append(r.tocsr()); lbs.append(0.0); ubs.append(1.0)
    A=vstack(rows).tocsr() if rows else lil_matrix((0,N)).tocsr()
    return A, np.array(lbs), np.array(ubs), N, len(jj)

def solve(A,lb,ub,N,tl=3000):
    if N==0: return None
    return milp(c=np.zeros(N),constraints=[LinearConstraint(A,lb,ub)] if A.shape[0] else [],
                integrality=np.ones(N),bounds=Bounds(0,1),
                options={"time_limit":tl,"disp":False,"mip_rel_gap":0.0})

def status(A,lb,ub,N,tl=3000):
    if N==0: return 0
    r=solve(A,lb,ub,N,tl); 
    return r.status

def main():
    t0=time.time()
    names, EL, node_ok, via_ok, REG = load_ctx()
    DECL=[(114,r) for r in REG["revised_gate_sets"]["W_col114_rows"]]+[(c,36) for c in REG["revised_gate_sets"]["E_row36_cols"]]
    cands=gen_cands(DECL, names, EL, node_ok, via_ok)
    log("declared model: lanes=%d gates=%d candidates=%d (gen %.1fs)"%(len(names),len(DECL),len(cands),time.time()-t0))
    log("gate candidate census:")
    gc=collections.Counter(tuple(c["gate"]) for c in cands)
    reach_gates=sorted([g for g in DECL if gc[g]>0])
    dead_gates=sorted([g for g in DECL if gc[g]==0])
    for g in DECL: log("   gate %s candidates=%d"%(g,gc[g]))
    log("reachable gates (%d): %s"%(len(reach_gates),reach_gates))
    log("declared-but-UNROUTABLE gates (%d): %s"%(len(dead_gates),dead_gates))

    # step 0: full model infeasible (reference)
    A,lb,ub,N,NC=make_model(cands,names)
    s0=status(A,lb,ub,N); log("[step0] full model status=%s (infeasible=%s) %.1fs"%(s0,s0==2,time.time()-t0))
    # step 1: coarse -- drop all cell rows
    A1,lb1,ub1,N1,NC1=make_model(cands,names,use_cells=False)
    s1=status(A1,lb1,ub1,N1); log("[step1] cell-free model status=%s (infeasible=%s) -> cells in core: %s"%(s1,s1==2,s1==0))
    # step 2: deletion filter over gates (cell-free)
    keep_gates=list(reach_gates); removed_gates=[]
    for g in list(reach_gates):
        trial=[x for x in keep_gates if x!=g]
        Ag,lbg,ubg,Ng,_=make_model(cands,names,use_cells=False,keep_gates=set(trial))
        sg=status(Ag,lbg,ubg,Ng)
        if sg==2: keep_gates=trial; removed_gates.append(g)
        log("   [gate-filter] remove %s -> status=%s %s"%(g,sg,"REMOVED" if sg==2 else "keep"))
    log("[step2] minimal gate set (%d): %s ; removed %s"%(len(keep_gates),keep_gates,removed_gates))
    # step 3: deletion filter over lanes (cell-free, minimal gate set)
    keep_lanes=list(names); removed_lanes=[]
    for nm in list(names):
        trial=[x for x in keep_lanes if x!=nm]
        Al,lbl,ubl,Nl,_=make_model(cands,names,keep_lanes=set(trial),use_cells=False,keep_gates=set(keep_gates))
        sl=status(Al,lbl,ubl,Nl)
        if sl==2: keep_lanes=trial; removed_lanes.append(nm)
        log("   [lane-filter] remove %s -> status=%s %s"%(nm,sl,"REMOVED" if sl==2 else "keep"))
    log("[step3] minimal lane set (%d): %s ; removed %s"%(len(keep_lanes),keep_lanes,removed_lanes))
    # step 4: irreducibility of the extracted core
    Ac,lbcn,ubc,Nc,_=make_model(cands,names,keep_lanes=set(keep_lanes),use_cells=False,keep_gates=set(keep_gates))
    sc=status(Ac,lbcn,ubc,Nc)
    log("[step4] core model status=%s (infeasible=%s)"%(sc,sc==2))
    irr=[]; redundant=[]
    for nm in keep_lanes:
        trial=[x for x in keep_lanes if x!=nm]
        Al,lbl,ubl,Nl,_=make_model(cands,names,keep_lanes=set(trial),use_cells=False,keep_gates=set(keep_gates))
        sl=status(Al,lbl,ubl,Nl)
        (irr if sl==0 else redundant).append(("lane",nm))
    for g in keep_gates:
        trial=[x for x in keep_gates if x!=g]
        Ag,lbg,ubg,Ng,_=make_model(cands,names,keep_lanes=set(keep_lanes),use_cells=False,keep_gates=set(trial))
        sg=status(Ag,lbg,ubg,Ng)
        (irr if sg==0 else redundant).append(("gate",g))
    log("[step4] irreducibility: necessary=%d non-necessary=%d -> %s"%(len(irr),len(redundant),"IRREDUCIBLE (IIS)" if not redundant else "NOT-minimal"))
    core={"infeasible_status":int(sc),"irreducible":(len(redundant)==0),
          "lane_constraints":[nm for nm in keep_lanes],
          "gate_constraints":[list(g) for g in keep_gates],
          "cell_constraints":0,
          "size":len(keep_lanes)+len(keep_gates),
          "interpretation":"pigeonhole: %d lanes require %d pairwise-distinct exit openings but only %d declared openings are routable"
                           %(len(keep_lanes),len(keep_lanes),len(keep_gates))}

    # step 5: routable-corridor census (scan corridors beyond the declared set)
    scanW=[(114,y) for y in range(0,64)]; scanE=[(x,36) for x in range(115,138)]
    routW=[]; routE=[]
    for g in scanW:
        n=sum(1 for c in gen_cands([g],names,EL,node_ok,via_ok))
        if n>0: routW.append([g[1],n])
    for g in scanE:
        n=sum(1 for c in gen_cands([g],names,EL,node_ok,via_ok))
        if n>0: routE.append([g[0],n])
    declaredW=set(REG["revised_gate_sets"]["W_col114_rows"]); declaredE=set(REG["revised_gate_sets"]["E_row36_cols"])
    extraW=[[y,n] for y,n in routW if y not in declaredW]
    extraE=[[x,n] for x,n in routE if x not in declaredE]
    log("[step5] routable W corridors %d, E corridors %d ; extra-not-declared W=%d E=%d"%(len(routW),len(routE),len(extraW),len(extraE)))

    # step 6: targeted reading -- minimal number of EXTRA openings + witness
    EXW=[(114,y) for y,_ in extraW]; EXE=[(x,36) for x,_ in extraE]
    ALLR=reach_gates+EXW+EXE
    cands_all=gen_cands(ALLR,names,EL,node_ok,via_ok)
    lane_by={nm:i for i,nm in enumerate(names)}
    cellix={}
    for c in cands_all:
        for cp in c["cells"]:
            if cp not in cellix: cellix[cp]=len(cellix)
    allg=sorted(set(tuple(c["gate"]) for c in cands_all))
    EXSET=set(EXW+EXE); extra_g=[g for g in allg if g in EXSET]; zpos={g:i for i,g in enumerate(extra_g)}
    N=len(cands_all); NZ=len(extra_g); Ntot=N+NZ; zoff=N
    rows=[]; lbs=[]; ubs=[]
    for nm in names:
        r=lil_matrix((1,Ntot))
        for j,c in enumerate(cands_all):
            if c["lane"]==nm: r[0,j]=1.0
        rows.append(r.tocsr()); lbs.append(1.0); ubs.append(1.0)
    cell_lanes=collections.defaultdict(set)
    for c in cands_all:
        for cp in c["cells"]: cell_lanes[cp].add(c["lane"])
    for cp in cellix:
        if len(cell_lanes[cp])<2: continue
        r=lil_matrix((1,Ntot))
        for j,c in enumerate(cands_all):
            if cp in c["cells"]: r[0,j]=1.0
        rows.append(r.tocsr()); lbs.append(0.0); ubs.append(1.0)
    for g in allg:
        r=lil_matrix((1,Ntot))
        for j,c in enumerate(cands_all):
            if tuple(c["gate"])==g: r[0,j]=1.0
        rows.append(r.tocsr()); lbs.append(0.0); ubs.append(1.0)
    for g in extra_g:
        r=lil_matrix((1,Ntot))
        for j,c in enumerate(cands_all):
            if tuple(c["gate"])==g: r[0,j]=1.0
        r[0,zoff+zpos[g]]=-1.0
        rows.append(r.tocsr()); lbs.append(-np.inf); ubs.append(0.0)
    A2=vstack(rows).tocsr()
    cobj=np.zeros(Ntot)
    for g in extra_g: cobj[zoff+zpos[g]]=1.0
    t=time.time()
    res=milp(c=cobj,constraints=[LinearConstraint(A2,np.array(lbs),np.array(ubs))],integrality=np.ones(Ntot),
             bounds=Bounds(0,1),options={"time_limit":3000,"disp":False,"mip_rel_gap":0.0})
    log("[step6] min-extra-openings MILP status=%s obj=%s %.1fs"%(res.status,res.fun,time.time()-t))
    target={}; witness=None
    if res.status==0:
        sol={c["lane"]:c for j,c in enumerate(cands_all) if res.x[j]>0.5}
        used=sorted(set(tuple(c["gate"]) for c in sol.values()))
        ex_used=[g for g in used if g in EXSET]
        own=collections.Counter()
        for c in sol.values():
            for cp in c["cells"]: own[cp]+=1
        witness={nm:{"gate":list(c["gate"]),"walk":[[L,list(cp)] for L,cp in c["walk"]]} for nm,c in sol.items()}
        target={"min_extra_openings":int(len(ex_used)),"extra_openings_used":[list(g) for g in ex_used],
                "declared_openings_used":[list(g) for g in used if g not in EXSET],
                "witness_lanes":len(sol),"gate_multiplicity_max":max(collections.Counter(tuple(c["gate"]) for c in sol.values()).values()),
                "cell_overlaps":int(sum(1 for k,v in own.items() if v>1)),
                "verdict":"ADD %d routable opening(s) %s to the 15 declared-routable set => 16/16 feasible (witness), cells 0-overlap, gates distinct"%(
                          len(ex_used),[list(g) for g in ex_used])}
        log("[step6] TARGETED READING: %s"%target["verdict"])

    rep={"artifact":"k2_r776_minimal_core_iis",
     "ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
     "authority":"#K2-301 sec.2 (1)(2): ONE minimal-conflict-core (IIS) extraction + targeted reading; same exact solver (HiGHS/scipy.optimize.milp) re-verifies infeasibility each step",
     "method":"structured deletion filter (coarse family removal + per-constraint filtering over gates then lanes) + irreducibility proof + min-extra-openings MILP",
     "construction_runs":1,"drawings":0,"gerber_exported":False,"p5":False,"order":False,
     "declared_model":{"lanes":len(names),"gates_declared":len(DECL),"candidates":len(cands),
                       "reachable_gates":len(reach_gates),"unroutable_declared_gates":len(dead_gates)},
     "reachable_gates":[list(g) for g in reach_gates],
     "unroutable_declared_gates":[list(g) for g in dead_gates],
     "minimal_core":core,
     "full_model_infeasible_status":int(s0),
     "cell_free_model_infeasible_status":int(s1),
     "routable_corridors":{"W":routW,"E":routE},
     "extra_routable_not_declared":{"W":extraW,"E":extraE},
     "targeted_reading":target,
     "witness":witness,
     "solver":{"name":"HiGHS (scipy.optimize.milp)","time_limit_s":3000},
     "scope_note":"core/live only inside the DECLARED candidate family (revised mirror-complete gate set x single-run/one-drop/one-escape template); not extrapolated to all possible routing",
     "elapsed_s":round(time.time()-t0,1)}
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(OUT,"w"),ensure_ascii=False,indent=1,default=str)
    log("artifact=%s hash=%s elapsed=%.1fs"%(OUT,rep["artifact_hash16"],time.time()-t0))
    log("OWNER-ITEMS: 0")
    return 0

if __name__=="__main__": sys.exit(main())
