#!/usr/bin/env python3
"""K2 R770 --- #K2-299 sec.2 : ONE bounded-COMPLETE JOINT search = (lane -> gate ASSIGNMENT) x (route), inside the
revised mirror-complete gate set. Complete method (exhaustive candidate sets + MRV + forward checking + backtracking);
NO heuristic first-fit, NO parameter iteration. One execution, one binary."""
import sys, os, json, types, importlib, hashlib, time, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "K2_R770_JOINT_ASSIGN_ROUTE_SEARCH_v1.json")
LOGF = os.path.join(HERE, "K2_R770_solve.log")
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
TIME_CAP = 2400.0
def main():
    t0 = time.time()
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full"); names = list(g2.names)
    T = json.load(open(os.path.join(HERE,"K2_R613_FINAL_TABLE_VIA_OK_v1.json")))["per_lane"]
    REG = json.load(open(os.path.join(HERE,"K2_L1_A_EXIT_REGISTRATION_REVISION_v1.json")))
    Wr = REG["revised_gate_sets"]["W_col114_rows"]; Ec = REG["revised_gate_sets"]["E_row36_cols"]
    GATES = [(114, r) for r in Wr] + [(c, 36) for c in Ec]
    EL = {nm: int(T[nm]["exit_layer"]) for nm in names}
    node_ok = {}; via_ok = {}
    for nm in names:
        node_ok[nm] = {L: {rc(i) for i in np.nonzero(g2._nok[(nm,L)] & g2.region_ok(nm,L))[0]} for L in (0,1)}
        via_ok[nm] = {rc(i) for i in np.nonzero(g2._viaok[nm])[0]}
    def build(nm, gate, cl, t, Xt, H):
        e_col, e_row = gate; eL = EL[nm]
        if H <= e_row + 1: return None
        w = [(cl,(60,H))]; vias = []
        if t != cl:
            via = None
            for c in range(60, Xt+1):
                if all((cl,(x,H)) in node_ok[nm][cl] for x in range(60,c+1)) and (t,(c,H)) in node_ok[nm][t]: via=c; break
            if via is None: return None
            w += [(cl,(x,H)) for x in range(61,via+1)]; w.append((t,(via,H))); vias.append((via,H))
            w += [(t,(x,H)) for x in range(via+1,Xt+1)]
        else:
            w += [(t,(x,H)) for x in range(61,Xt+1)]
        w += [(t,(Xt,r)) for r in range(H-1,e_row,-1)]
        if t != eL: vias.append((Xt,e_row))
        w.append((eL,(Xt,e_row)))
        w += [(eL,(x,e_row)) for x in range(Xt-1,e_col-1,-1)]
        if len(set(w)) != len(w) or w[-1] != (eL,(e_col,e_row)): return None
        for (L,cp) in w:
            if cp not in node_ok[nm][L]: return None
        for cp in vias:
            if cp not in via_ok[nm]: return None
        return w
    cand = {}
    for nm in names:
        seen=set(); lst=[]
        for gate in GATES:
            e_col, e_row = gate
            Xts = (list(range(116,138)) if e_col==114 else [e_col-3,e_col-2,e_col-1,e_col+1,e_col+2,e_col+3,e_col+4])
            for cl in (0,1):
                for t in (0,1):
                    for Xt in Xts:
                        if e_col != 114 and Xt <= e_col: continue
                        for H in range(e_row+2, 60):
                            w = build(nm, gate, cl, t, Xt, H)
                            if w is None: continue
                            k = frozenset(w)
                            if k in seen: continue
                            seen.add(k); lst.append((gate, w))
        cand[nm] = lst
        log("%-13s candidates=%d (gates=%d)" % (nm.replace("PCIE_UP_",""), len(lst), len({g for g,_ in lst})))
    sets = {nm: [(g, frozenset(w)) for g,w in cand[nm]] for nm in names}
    order0 = sorted(names, key=lambda n: len(sets[n]))
    sol = {}; nodes=[0]
    def dfs(i, used, chosen):
        if time.time()-t0 > TIME_CAP: raise TimeoutError
        if i == len(order0): sol.update(chosen); return True
        nm = order0[i]
        pool = [(g,c) for (g,c) in sets[nm] if not (c & used)]
        pool.sort(key=lambda gc: len(gc[1]))
        for g,c in pool:
            nodes[0]+=1; chosen[nm]=(g,c)
            if dfs(i+1, used|c, chosen): return True
            del chosen[nm]
        return False
    tmo=False
    try: ok=dfs(0, frozenset(), {})
    except TimeoutError: ok=False; tmo=True
    log("search nodes=%d timeout=%s solved=%s %.1fs" % (nodes[0],tmo,ok,time.time()-t0))
    solved=bool(sol)
    own=collections.Counter()
    for nm,(g,c) in sol.items():
        for x in c: own[x]+=1
    ov=[k for k,v in own.items() if v>1]
    reg_old={("PCIE_UP_"+r["lane"]): tuple(r["gate_registered"]["cell"]) for r in REG["rows"]}
    diff=[{"lane":nm.replace("PCIE_UP_",""),"registered_exit":list(reg_old[nm]),"assigned_gate":list(sol[nm][0])} for nm in sorted(sol)] if solved else None
    rep={"artifact":"k2_r770_joint_assign_route_search_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
     "authority":"#K2-299 sec.2 (ONE bounded-complete JOINT search: assignment x route, inside the revised mirror-complete gate set)",
     "method":"per-lane EXHAUSTIVE candidate sets over (gate in revised set) x (layer pair) x (descent column) x (run row), legality + layer-pair only; then COMPLETE DFS with MRV + forward checking + backtracking",
     "construction_runs":1,"drawings":0,"gerber_exported":False,"p5":False,"order":False,
     "revised_gate_set":{"W_rows":Wr,"E_cols":Ec,"size":len(GATES)},
     "candidate_counts":{nm.replace("PCIE_UP_",""):len(cand[nm]) for nm in names},
     "search":{"nodes":nodes[0],"timeout":tmo,"solved":solved,"time_cap_s":TIME_CAP},
     "binary":("SAT_16of16" if solved else ("EXHAUSTED_NO_SOLUTION_IN_JOINT_SPACE" if not tmo else "SEARCH_BOUND_HIT")),
     "witness":({nm.replace("PCIE_UP_",""):{"gate":list(g),"walk":[[L,list(cp)] for (L,cp) in w]} for nm,(g,c) in sol.items() for w in [sorted(c)]} if solved else None),
     "registration_diff_old_to_new":diff,
     "merged_verification":({"conflicts":len(ov),"cells_distinct":len(own),"capacity_ge_demand":len(own)>=sum(len(c) for _,c in sol.values())} if solved else None),
     "scope_note":"candidate sets are BOUNDED (declared ranges) and the gate set is the revised mirror-complete set; solving = witness; exhausting = exhaustion-level evidence over THIS bounded joint space only",
     "elapsed_s":round(time.time()-t0,1)}
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(OUT,"w"),ensure_ascii=False,indent=1,default=str)
    log("binary=%s hash=%s"%(rep["binary"],rep["artifact_hash16"])); log("OWNER-ITEMS: 0")
    return 0
if __name__=="__main__": sys.exit(main())
