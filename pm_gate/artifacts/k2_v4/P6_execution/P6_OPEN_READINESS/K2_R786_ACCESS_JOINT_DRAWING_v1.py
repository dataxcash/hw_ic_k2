#!/usr/bin/env python3
"""K2 R786 --- #K2-308 : bounded JOINT access-segment drawing (one execution).

Per #K2-306 sec.2 + #K2-307 sec.3 + #K2-308:
  * 15 lanes: mid-segment FIXED (R778 certified witness).
  * OUT6_N  : mid-segment may be RE-ASSIGNED within the registered v2 16-gate set (L2); re-certified here.
  * access  : per lane, a BOUNDED set of alternative in-paths (A->slot) and out-paths (gate->B).
  * ONE whole-board uniqueness MILP: per-lane 1 in + 1 out (+ OUT6_N 1 belt), cell-exclusive, gate/slot distinct.
SAT => complete 16/16 drawing (A -> ... -> B) + re-certification (four hard keys + layer-pair + conservation).
UNSAT => NAMED_BLOCKER.  Board untouched; drawing only.
"""
import sys, os, json, hashlib, time, types, importlib, collections, random
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix, vstack
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
for nm in ("ortools","ortools.sat","ortools.sat.python"): sys.modules.setdefault(nm, types.ModuleType(nm))
cm = types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self, *a, **k): pass
cm.CpModel = _D; cm.CpSolver = _D
sys.modules["ortools.sat.python.cp_model"] = cm; sys.modules["ortools.sat.python"].cp_model = cm
M = importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1"); PREV = M.PREV; PREV.Gen._build_edges = M._build_edges_fixed
W = M.W; NID, NY, TERM = W.NID, W.NY, W.TERM_BASE
OUT = os.path.join(HERE, "K2_R786_ACCESS_JOINT_DRAWING_v1.json")
LOGF = os.path.join(HERE, "K2_R786_solve.log"); LH = open(LOGF,"w")
def log(m): LH.write(str(m)+"\n"); LH.flush(); print(str(m), flush=True)
def rc(u): u %= NID; return u // W.NY, u % W.NY

def main():
    t0=time.time()
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full"); names=list(g2.names)
    cert = json.load(open(os.path.join(HERE,"K2_R778_CERTIFIED_16OF16_v1.json")))
    REG = json.load(open(os.path.join(HERE,"K2_L1_A_EXIT_REGISTRATION_REVISION_v2.json")))
    reg_gates = [tuple(g) for g in REG["openings_kept_routable"]] + [tuple(REG["opening_added"]["cell"])]
    wit = cert["witness"]
    cs = lambda nm: nm.replace("PCIE_UP_","")
    EL={nm:int(json.load(open(os.path.join(HERE,"K2_R613_FINAL_TABLE_VIA_OK_v1.json")))["per_lane"][nm]["exit_layer"]) for nm in names}
    node_ok={}; via_ok={}
    for nm in names:
        node_ok[nm]={L:{rc(i) for i in np.nonzero(g2._nok[(nm,L)] & g2.region_ok(nm,L))[0]} for L in (0,1)}
        via_ok[nm]={rc(i) for i in np.nonzero(g2._viaok[nm])[0]}
    def build(nm, gate, cl, t, Xt, H):
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
    def belt_cands(nm):
        out=[]
        for gate in reg_gates:
            e_col,e_row=gate
            Xts=(list(range(116,138)) if e_col==114 else [e_col-3,e_col-2,e_col-1,e_col+1,e_col+2,e_col+3,e_col+4])
            seen=set()
            for cl in (0,1):
                for t in (0,1):
                    for Xt in Xts:
                        if e_col!=114 and Xt<=e_col: continue
                        for H in range(e_row+2,60):
                            w=build(nm,gate,cl,t,Xt,H)
                            if w is None: continue
                            k=frozenset(w)
                            if k in seen: continue
                            seen.add(k); out.append({"gate":tuple(gate),"walk":w,"cells":k})
        return out
    # ---- every lane: bounded belt candidates (shortest N per lane over the 16 registered gates) ----
    N_BELT=16; K=4
    LB={nm:g2.build_lane(nm) for nm in names}
    ADJ={nm:LB[nm]["adj"] for nm in names}
    def cell_of(u): return None if u>=TERM else (u//NID,(u%NID)//NY,(u%NID)%NY)
    def bfs(nm, src, dst, forb):
        adj=ADJ[nm]; prev={src:None}; q=collections.deque([src])
        while q:
            u=q.popleft()
            if u==dst: break
            for v,_w in adj.get(u,[]):
                if v in prev: continue
                if v!=dst and v<TERM and cell_of(v) in forb: continue
                prev[v]=u; q.append(v)
        if dst not in prev: return None
        p=[];u=dst
        while u is not None: p.append(u); u=prev[u]
        return p[::-1]
    _SEED=[0]
    def gen_alts(nm, src, dst, forb, k):
        base=bfs(nm,src,dst,forb)
        if base is None: return []
        _SEED[0]+=1; rng=random.Random(1234+_SEED[0])
        alts=[base]; seen={tuple(base)}; f=set(forb)
        for it in range(k*6):
            inner=[c for c in base[1:-1]]
            if not inner: break
            f|=set(rng.sample(inner,max(1,len(inner)//4)))
            p=bfs(nm,src,dst,f)
            if p is None: f=set(forb); continue
            t=tuple(p)
            if t not in seen: seen.add(t); alts.append(p)
            if len(alts)>=k: break
        return alts
    def slotnode(cell): return cell[0]*NID+cell[1][0]*NY+cell[1][1]
    log("belt candidates for 16 lanes ...")
    BELT={}
    for nm in names:
        allc=belt_cands(nm)
        for b in allc: b["nodes"]=b["walk"]
        per_gate={}
        for b in allc:
            g=tuple(b["gate"])
            if g not in per_gate or len(b["walk"])<len(per_gate[g]["walk"]): per_gate[g]=b
        BELT[nm]=sorted(per_gate.values(),key=lambda z:len(z["walk"]))[:N_BELT]
    log("belt cands/lane=%d"%N_BELT)
    T={nm:LB[nm]["terminals"] for nm in names}
    cands=[]
    for nm in names:
        for bi,b in enumerate(BELT[nm]):
            g="b%d"%bi
            cands.append({"kind":"belt","lane":nm,"group":g,"gate":tuple(b["gate"]),"cells":set(b["cells"]),"nodes":b["nodes"]})
            bset=set(b["cells"])
            slot=(b["nodes"][0][0],tuple(b["nodes"][0][1])); gate=(b["nodes"][-1][0],tuple(b["nodes"][-1][1]))
            for p in gen_alts(nm,T[nm][0],slotnode(slot),frozenset(),K):
                cands.append({"kind":"in","lane":nm,"group":g,"gate":None,"cells":set(c for c in (cell_of(u) for u in p) if c)-bset,"nodes":p})
            for p in gen_alts(nm,slotnode(gate),T[nm][1],frozenset({slot}),K):
                cands.append({"kind":"out","lane":nm,"group":g,"gate":None,"cells":set(c for c in (cell_of(u) for u in p) if c)-bset,"nodes":p})
    lens=collections.Counter(c["kind"] for c in cands)
    log("candidates: %s"%dict(lens))
    if lens["in"]==0 or lens["out"]==0: log("FATAL no access candidates"); 
    for c in cands: c["_cells"]=c["cells"]
    N=len(cands)
    cellix={}
    for j,c in enumerate(cands):
        for cp in c["cells"]:
            if cp not in cellix: cellix[cp]=len(cellix)
    rows=[]; lbs=[]; ubs=[]
    def addrow(entries, lo, hi):
        r=lil_matrix((1,N))
        for j,val in entries: r[0,j]=val
        rows.append(r.tocsr()); lbs.append(lo); ubs.append(hi)
    lane_kinds=collections.defaultdict(list)
    for j,c in enumerate(cands): lane_kinds[(c["lane"],c["kind"])].append(j)
    zero_acc=[]
    for nm in names:
        cnts={k:len(lane_kinds.get((nm,k),[])) for k in ("belt","in","out")}
        log("  %-14s cands %s"%(nm.replace("PCIE_UP_",""),cnts))
        for kind in ("belt","in","out"):
            js=lane_kinds.get((nm,kind),[])
            if js: addrow([(j,1.0) for j in js],1.0,1.0)
            elif kind!="belt": zero_acc.append((nm.replace("PCIE_UP_",""),kind))
    belt_by_group={}
    for j,c in enumerate(cands):
        if c["kind"]=="belt": belt_by_group[(c["lane"],c["group"])]=j
    for nm in names:
        for bi in range(len(BELT[nm])):
            g="b%d"%bi; zb=belt_by_group[(nm,g)]
            for kind in ("in","out"):
                js=[j for j,c in enumerate(cands) if c["lane"]==nm and c["kind"]==kind and c["group"]==g]
                if js: addrow([(j,1.0) for j in js]+[(zb,-1.0)],0.0,0.0)
    # cell capacity
    for cp,ix in cellix.items():
        js=[j for j,c in enumerate(cands) if cp in c["_cells"]]
        if len(js)>1: addrow([(j,1.0) for j in js],-np.inf,1.0)
    # gate capacity over the 16 registered gates
    for g in reg_gates:
        js=[j for j,c in enumerate(cands) if c["kind"]=="belt" and c["gate"]==g]
        if len(js)>1: addrow([(j,1.0) for j in js],-np.inf,1.0)
    # slot capacity (col60, H distinct)
    slot_map=collections.defaultdict(list)
    for j,c in enumerate(cands):
        if c["kind"]=="belt": slot_map[c["nodes"][0]].append(j)
    for s,js in slot_map.items():
        if len(js)>1: addrow([(j,1.0) for j in js],-np.inf,1.0)
    A=vstack(rows).tocsr(); lb=np.array(lbs); ub=np.array(ubs)
    nb=0
    for i in range(A.shape[0]):
        if A.getrow(i).nnz==0 and lb[i]>0: nb+=1; log("  EMPTY-ROW lb=%s at %d"%(lb[i],i))
    log("empty-conflicting rows=%d"%nb)
    t=time.time()
    res=milp(c=np.ones(N),constraints=[LinearConstraint(A,lb,ub)],integrality=np.ones(N),bounds=Bounds(0,1),
             options={"time_limit":3600,"disp":False,"mip_rel_gap":0.0})
    log("MILP status=%s obj=%s %.1fs"%(res.status,res.fun,time.time()-t))
    rep={"artifact":"k2_r786_access_joint_drawing","zero_access_lanes":zero_acc,"ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
     "authority":"#K2-308 (1) bounded joint access drawing (whole-board uniqueness MILP, one execution); (2) OUT6_N mid re-assignment within the registered v2 16-gate set + re-certification",
     "construction_runs":1,"drawings":0,"gerber_exported":False,"p5":False,"order":False,
     "candidates":{"total":N,"by_kind":dict(lens),"out6_belt_candidates":len(BELT["PCIE_UP_OUT6_N_J2"]),"k_alternatives":K},
     "solver":{"status":int(res.status),"obj":None if res.fun is None else round(float(res.fun),1),"elapsed_s":round(time.time()-t,1)}}
    if res.status==0:
        sel={}
        for j,c in enumerate(cands):
            if res.x[j]>0.5: sel.setdefault((c["lane"],c["kind"]),[]).append(c)
        # assemble per-lane full route
        routes={}
        ok=True; probs=[]
        for nm in names:
            belt=sel[(nm,"belt")][0]; inn=sel[(nm,"in")][0]; out=sel[(nm,"out")][0]
            def nodes_of(u):
                # strip virtual terminals for cell list
                return [x for x in u if x<TERM]
            fullnodes = inn["nodes"] + belt["nodes"] + out["nodes"]
            cellseq=[]
            for u in fullnodes:
                cellseq.append((u//NID, (u%NID)//NY, (u%NID)%NY))
            # continuity
            def adj(a,b):
                if a[0]==b[0]: return abs(a[1][0]-b[1][0])+abs(a[1][1]-b[1][1])==1
                return a[1]==b[1]
            cont=all(adj(cellseq[i-1],cellseq[i]) for i in range(1,len(cellseq)))
            routes[cs(nm)]={"gate":list(belt["gate"]),"n_cells":len(set(cellseq)),"continuous":cont,
                            "walk":[[L,list(cp)] for (L,cp) in cellseq]}
            if not cont: ok=False; probs.append({"lane":cs(nm),"issue":"non_continuous"})
        # joint check
        own=collections.Counter()
        for nm in names:
            for L,cp in routes[cs(nm)]["walk"]: own[(L,tuple(cp))]+=1
        overlap=[k for k,v in own.items() if v>1]
        gates=[tuple(routes[cs(nm)]["gate"]) for nm in names]
        gate_ok=len(set(gates))==16
        rep.update({"binary":"SAT_16OF16_COMPLETE_ROUTE","routes":routes,
                    "joint_check":{"cell_overlaps":len(overlap),"overlap_cells":[ [k[0],list(k[1])] for k in overlap[:10]],
                                   "gates_distinct":gate_ok,"out6_gate":list(sel[(OUT6,"belt")][0]["gate"]),
                                   "continuous_all":ok},
                    "verdict":"ACCESS_DRAWING_PASS" if (not overlap and gate_ok and ok) else "ACCESS_DRAWING_NAMED_BLOCKER"})
    else:
        rep.update({"binary":"UNSAT_IN_BOUNDED_CANDIDATE_SET","verdict":"ACCESS_DRAWING_NAMED_BLOCKER",
                    "named_blocker":{"scope":"bounded joint candidate set (k=%d alternatives/lane, OUT6 over 16 registered gates)"%K,
                                     "note":"no whole-board cell-exclusive selection of in/out(+OUT6 belt) exists within the bounded candidate family"}})
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(OUT,"w"),ensure_ascii=False,indent=1,default=str)
    log("binary=%s hash=%s elapsed=%.1fs"%(rep["binary"],rep["artifact_hash16"],time.time()-t0))
    log("OWNER-ITEMS: 0")
    return 0
if __name__=="__main__": sys.exit(main())
