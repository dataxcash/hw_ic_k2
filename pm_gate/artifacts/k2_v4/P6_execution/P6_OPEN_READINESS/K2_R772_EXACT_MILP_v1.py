#!/usr/bin/env python3
"""K2 R772 --- #K2-300 sec.5 : ONE EXACT solve (method-family switch to an exact MILP; same declared domain;
must terminate in a binary). Solver = HiGHS via scipy.optimize.milp (termination guaranteed by B&B)."""
import sys, os, json, types, importlib, hashlib, time, collections
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "K2_R772_EXACT_MILP_v1.json")
LOGF = os.path.join(HERE, "K2_R772_solve.log")
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
def main():
    t0 = time.time()
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full"); names = list(g2.names)
    T = json.load(open(os.path.join(HERE,"K2_R613_FINAL_TABLE_VIA_OK_v1.json")))["per_lane"]
    REG = json.load(open(os.path.join(HERE,"K2_L1_A_EXIT_REGISTRATION_REVISION_v1.json")))
    GATES = [(114,r) for r in REG["revised_gate_sets"]["W_col114_rows"]] + [(c,36) for c in REG["revised_gate_sets"]["E_row36_cols"]]
    EL = {nm: int(T[nm]["exit_layer"]) for nm in names}
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
        if t!=eL: vias.append((Xt,e_row))
        w.append((eL,(Xt,e_row))); w+=[(eL,(x,e_row)) for x in range(Xt-1,e_col-1,-1)]
        if len(set(w))!=len(w) or w[-1]!=(eL,(e_col,e_row)): return None
        for (L,cp) in w:
            if cp not in node_ok[nm][L]: return None
        for cp in vias:
            if cp not in via_ok[nm]: return None
        return w
    cand=[]; lane_idx={nm:i for i,nm in enumerate(names)}
    for nm in names:
        seen=set()
        for gate in GATES:
            e_col,e_row=gate
            Xts=(list(range(116,138)) if e_col==114 else [e_col-3,e_col-2,e_col-1,e_col+1,e_col+2,e_col+3,e_col+4])
            for cl in (0,1):
                for t in (0,1):
                    for Xt in Xts:
                        if e_col!=114 and Xt<=e_col: continue
                        for H in range(e_row+2,60):
                            w=build(nm,gate,cl,t,Xt,H)
                            if w is None: continue
                            k=frozenset(w)
                            if k in seen: continue
                            seen.add(k); cand.append((nm,gate,w,k))
        log("%-13s candidates=%d"%(nm.replace("PCIE_UP_",""),len(seen)))
    cellix={}
    for (_,_,_,k) in cand:
        for cp in k:
            if cp not in cellix: cellix[cp]=len(cellix)
    N=len(cand); R=16+len(cellix)
    A=lil_matrix((R,N),dtype=float)
    for j,(nm,gate,w,k) in enumerate(cand):
        A[lane_idx[nm],j]=1.0
        for cp in k: A[16+cellix[cp],j]=1.0
    lb=np.zeros(R); ub=np.ones(R); lb[:16]=1.0
    cons=LinearConstraint(A.tocsr(),lb,ub)
    res=milp(c=np.zeros(N), constraints=[cons], integrality=np.ones(N), bounds=Bounds(0,1),
             options={"time_limit":3000,"disp":False,"mip_rel_gap":0.0})
    log("MILP status=%s message=%s time=%.1fs"%(res.status,res.message,time.time()-t0))
    solved = (res.status==0 and res.x is not None)
    sol={}
    if solved:
        for j,(nm,gate,w,k) in enumerate(cand):
            if res.x[j]>0.5: sol[nm]=(gate,w)
    own=collections.Counter(); 
    for nm,(g,w) in sol.items():
        for x in w: own[x]+=1
    ov=[k for k,v in own.items() if v>1]
    reg_old={("PCIE_UP_"+r["lane"]): tuple(r["gate_registered"]["cell"]) for r in REG["rows"]}
    try: base13=sorted(json.load(open(os.path.join(HERE,"K2_R652_JOINT_TABLE_16OF16_PHYSICAL_v1.json"))).get("per_lane",{}).keys())
    except Exception: base13=[]
    recon={nm.replace("PCIE_UP_",""):{"in_R652_13of16_baseline":nm.replace("PCIE_UP_","") in base13,
             "registered_exit":list(reg_old[nm]),"assigned_gate":list(sol[nm][0]) if nm in sol else None,
             "changed":list(reg_old[nm])!=list(sol[nm][0]) if nm in sol else None,
             "reason":"exact MILP assignment (revised mirror-complete gate set)"} for nm in names}
    rep={"artifact":"k2_r772_exact_milp_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
     "authority":"#K2-300 sec.3 (1) restricted form: ONE method-family switch to an EXACT solver, same declared domain, must terminate in a binary",
     "method":"exact MILP (HiGHS via scipy.optimize.milp): one binary per candidate route; per-lane sum = 1; per-cell sum <= 1 (mutual exclusion); termination guaranteed by branch-and-bound",
     "construction_runs":1,"drawings":0,"gerber_exported":False,"p5":False,"order":False,
     "model":{"lanes":16,"candidates":N,"cell_constraints":len(cellix),"rows":R},
     "solver":{"name":"HiGHS (scipy.optimize.milp)","status":int(res.status),"message":str(res.message),"time_limit_s":3000,"elapsed_s":round(time.time()-t0,1)},
     "binary":("SAT_16of16" if (solved and len(sol)==16 and not ov) else ("UNSAT_EXACT_INFEASIBLE" if res.status==2 else "NO_BINARY_TIME_LIMIT")),
     "witness":({nm.replace("PCIE_UP_",""):{"gate":list(g),"walk":[[L,list(cp)] for (L,cp) in w]} for nm,(g,w) in sol.items()} if solved else None),
     "merged_verification":({"conflicts":len(ov),"cells_distinct":len(own),"lanes":len(sol)} if solved else None),
     "baseline_reconciliation_vs_R652_13of16":recon,
     "scope_note":"exact solver over the DECLARED candidate domain (same as R770); SAT = witness; UNSAT = exact infeasibility of this declared model",
     "elapsed_s":round(time.time()-t0,1)}
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(OUT,"w"),ensure_ascii=False,indent=1,default=str)
    log("binary=%s hash=%s"%(rep["binary"],rep["artifact_hash16"])); log("OWNER-ITEMS: 0")
    return 0
if __name__=="__main__": sys.exit(main())
