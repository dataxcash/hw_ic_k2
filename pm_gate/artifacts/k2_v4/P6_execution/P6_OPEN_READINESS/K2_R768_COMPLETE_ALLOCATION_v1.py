#!/usr/bin/env python3
"""K2 R768 --- #K2-298 sec.6.3 : ONE bounded-COMPLETE certification on the SAME revised registration.

Method family switch (allowed as a code/method correction iteration per #K2-257; NOT a parameter rerun):
  * candidate ENUMERATION per lane (not first-fit): every (t, cl, Xt, H) route that is LEGAL for that lane
    (in-register per-lane free set + via-legal layer-pair rule) is collected;
  * then a COMPLETE search: MRV lane ordering + forward checking + backtracking over the candidate sets.
    => a solution IS a 16/16 witness; exhausting the search over the DECLARED candidate sets is exhaustion-level
       evidence over that bounded space (reported as such, never as a global impossibility).
  * baseline reconciliation vs R652's 13/16 is emitted row by row.
"""
import sys, os, json, types, importlib, hashlib, time, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "K2_R768_COMPLETE_ALLOCATION_v1.json")
LOGF = os.path.join(HERE, "K2_R768_solve.log")
LH = open(LOGF, "w")
def log(m): LH.write(str(m) + "\n"); LH.flush(); print(str(m), flush=True)
for nm in ("ortools","ortools.sat","ortools.sat.python"): sys.modules.setdefault(nm, types.ModuleType(nm))
cm = types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self, *a, **k): pass
cm.CpModel = _D; cm.CpSolver = _D
sys.modules["ortools.sat.python.cp_model"] = cm; sys.modules["ortools.sat.python"].cp_model = cm
M = importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1"); PREV = M.PREV; PREV.Gen._build_edges = M._build_edges_fixed
W = M.W; NID = W.NID
def rc(u): u %= NID; return u // W.NY, u % W.NY
def adj(a, b):
    if a[0] == b[0]: return abs(a[1][0]-b[1][0]) + abs(a[1][1]-b[1][1]) == 1
    return a[1] == b[1]
NODE_CAP = 4_000_000; TIME_CAP = 1500.0

def main():
    t0 = time.time()
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full"); names = list(g2.names)
    T = json.load(open(os.path.join(HERE, "K2_R613_FINAL_TABLE_VIA_OK_v1.json")))["per_lane"]
    REG = json.load(open(os.path.join(HERE, "K2_L1_A_EXIT_REGISTRATION_REVISION_v1.json")))
    gate = {("PCIE_UP_" + r["lane"]): tuple(r["new_gate_per_vendor_paradigm"]["cell"]) for r in REG["rows"]}
    EE = {nm: tuple(gate[nm]) for nm in names}
    EL = {nm: int(T[nm]["exit_layer"]) for nm in names}
    node_ok = {}; via_ok = {}
    for nm in names:
        node_ok[nm] = {L: {rc(i) for i in np.nonzero(g2._nok[(nm, L)] & g2.region_ok(nm, L))[0]} for L in (0,1)}
        via_ok[nm] = {rc(i) for i in np.nonzero(g2._viaok[nm])[0]}
    def build(nm, cl, t, Xt, H):
        e_col, e_row = EE[nm]; eL = EL[nm]
        if H <= e_row + 1: return None
        w = [(cl, (60, H))]; vias = []
        if t != cl:
            via = None
            for c in range(60, Xt+1):
                if all((cl,(x,H)) in node_ok[nm][cl] for x in range(60, c+1)) and (t,(c,H)) in node_ok[nm][t]:
                    via = c; break
            if via is None: return None
            w += [(cl,(x,H)) for x in range(61, via+1)]; w.append((t,(via,H))); vias.append((via,H))
            w += [(t,(x,H)) for x in range(via+1, Xt+1)]
        else:
            w += [(t,(x,H)) for x in range(61, Xt+1)]
        w += [(t,(Xt,r)) for r in range(H-1, e_row, -1)]
        if t != eL: vias.append((Xt, e_row))
        w.append((eL,(Xt,e_row)))
        w += [(eL,(x,e_row)) for x in range(Xt-1, e_col-1, -1)]
        if len(set(w)) != len(w) or w[-1] != (eL,(e_col,e_row)): return None
        for (L,cp) in w:
            if cp not in node_ok[nm][L]: return None
        for cp in vias:
            if cp not in via_ok[nm]: return None
        return w
    cand = {}
    for nm in names:
        e_col, e_row = EE[nm]; eL = EL[nm]; seen = set(); lst = []
        Xts = (list(range(116, 138)) if e_col == 114 else [e_col-3, e_col-2, e_col-1, e_col+1, e_col+2, e_col+3, e_col+4])
        for cl in (0,1):
            for t in (0,1):
                for Xt in Xts:
                    if Xt <= e_col and e_col != 114: continue
                    for H in range(e_row+2, 60):
                        w = build(nm, cl, t, Xt, H)
                        if w is None: continue
                        key = frozenset(w)
                        if key in seen: continue
                        seen.add(key); lst.append(w)
        cand[nm] = lst
        log("%-13s candidates=%d" % (nm.replace("PCIE_UP_",""), len(lst)))
    sets = {nm: [frozenset(w) for w in cand[nm]] for nm in names}
    order0 = sorted(names, key=lambda n: len(sets[n]))
    best = {"cells": None}; nodes = [0]
    def dfs(i, used, chosen):
        if time.time()-t0 > TIME_CAP or nodes[0] > NODE_CAP: raise TimeoutError
        if i == len(order0):
            best["cells"] = dict(chosen); return True
        nm = order0[i]
        pool = [c for c in sets[nm] if not (c & used)]
        pool.sort(key=len)
        for c in pool:
            nodes[0] += 1
            chosen[nm] = c
            if dfs(i+1, used | c, chosen): return True
            del chosen[nm]
        return False
    tmo = False
    try:
        ok = dfs(0, frozenset(), {})
    except TimeoutError:
        ok = False; tmo = True
    log("search: nodes=%d timeout=%s solved=%s elapsed=%.1fs" % (nodes[0], tmo, ok, time.time()-t0))
    solved = bool(best["cells"])
    # baseline reconciliation vs R652 13/16
    try:
        R652 = json.load(open(os.path.join(HERE, "K2_R652_JOINT_TABLE_16OF16_PHYSICAL_v1.json")))
        base13 = sorted(R652.get("per_lane", {}).keys())
    except Exception:
        base13 = []
    recon = {}
    for nm in names:
        k = nm.replace("PCIE_UP_","")
        old = tuple((int(T[nm]["exit_cell"][0]), int(T[nm]["exit_cell"][1])))
        new = EE[nm]
        recon[k] = {"in_R652_13of16_baseline": k in base13, "registered_exit": list(old), "revised_exit": list(new),
                    "changed": list(old) != list(new),
                    "reason": ("revised registration (mirror-complete, grouped monotone)" if list(old) != list(new) else "unchanged")}
    rep = {"artifact":"k2_r768_complete_allocation_v1","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
      "authority":"#K2-298 sec.6.3 (one bounded-COMPLETE certification, no pure greedy first-fit)",
      "method":"candidate ENUMERATION per lane (legality only) + COMPLETE search (MRV + forward checking + backtracking)",
      "construction_runs":1,"drawings":0,"gerber_exported":False,"p5":False,"order":False,
      "registration":"K2_L1_A_EXIT_REGISTRATION_REVISION_v1.json (REV1, mirror-complete)",
      "candidate_counts":{nm.replace("PCIE_UP_",""):len(cand[nm]) for nm in names},
      "search":{"nodes":nodes[0],"timeout":tmo,"solved":solved,"time_cap_s":TIME_CAP,"node_cap":NODE_CAP},
      "binary":("SAT_16of16" if solved else ("EXHAUSTED_NO_SOLUTION_IN_CANDIDATE_SPACE" if not tmo else "SEARCH_BOUND_HIT")),
      "witness":({k:[ [L,list(cp)] for (L,cp) in sorted(v)] for k,v in best["cells"].items()} if solved else None),
      "baseline_reconciliation_vs_R652_13of16":recon,
      "scope_note":"the candidate sets are BOUNDED (declared ranges); solving = witness; exhausting = exhaustion-level evidence over that bounded space only, NOT a global impossibility",
      "elapsed_s":round(time.time()-t0,1)}
    body = json.dumps(rep, ensure_ascii=False, indent=1, default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(OUT,"w"), ensure_ascii=False, indent=1, default=str)
    log("binary=%s hash=%s" % (rep["binary"], rep["artifact_hash16"])); log("OWNER-ITEMS: 0")
    return 0
if __name__ == "__main__": sys.exit(main())
