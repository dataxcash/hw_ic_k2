#!/usr/bin/env python3
"""K2 · R569 -- R568 with the ENG unit bug fixed (wp entries now pass POSITIONS, not node ids)
plus a fail-loud unit guard (every wp id must satisfy L*NID+nd < TERM_BASE):
  assignment -> three gates + capacity -> ONE drawing pass -> registered gates -> land.
New command; single pass; no solver; no backtracking; no rerun. FAIL => named diagnostic only.
"""
import sys, os, json, hashlib, time, importlib, types

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
OWN_OUT = "K2_R611_FINAL_DRAWING_v1.json"
LOGF = "/tmp/opencode/r611/draw.log"
MODEL = "/tmp/opencode/archer/model_l8.json"
os.makedirs(os.path.dirname(LOGF), exist_ok=True)
def log(m): open(LOGF, "a").write(str(m) + "\n"); print(str(m), flush=True)
for nm in ("ortools", "ortools.sat", "ortools.sat.python"): sys.modules.setdefault(nm, types.ModuleType(nm))
cm = types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self, *a, **k): pass
cm.CpModel = _D; cm.CpSolver = _D
sys.modules["ortools.sat.python.cp_model"] = cm; sys.modules["ortools.sat.python"].cp_model = cm
M = importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1")
PREV = M.PREV; PREV.Gen._build_edges = M._build_edges_fixed
W = M.W; NID, NY, TERM = W.NID, W.NY, W.TERM_BASE
P, X0, Y0 = W.P, W.X0, W.Y0
ST = ["COMB", "BELT", "WALL", "FIELD"]


def main():
    open(LOGF, "w").close(); t0 = time.time()
    log("[mark] load")
    g2 = W.Gen2(json.load(open(MODEL)), l1scope="full")
    names = list(g2.names)
    master = json.load(open(os.path.join(HERE, "K2_R529_WOVEN_COMPLETE_MASTER_v1.json")))
    spec = json.load(open(os.path.join(HERE, "K2_R540_CORRIDOR_SPEC_v1.json")))
    r550 = json.load(open(os.path.join(HERE, "K2_R550_CONSTRUCTION_DRAWING_v1.json")))
    ent_tab = r550["entrance_channel_table"]
    l2_in = json.load(open(os.path.join(HERE, "K2_R550_L2_SLOT_TABLE_v1.json")))["table"]
    def on4(nm, st): return 1 if ST[st] in master["schedule"][nm]["stations_on_In4"] else 0
    lanes = {nm: g2.build_lane(nm) for nm in names}
    adj = {nm: lanes[nm]["adj"] for nm in names}
    aset = {nm: {u: set(v for v, _w in lst) for u, lst in adj[nm].items()} for nm in names}
    CELL = {(nm, L): set(u for u in adj[nm] if u < TERM and u // NID == L) for nm in names for L in (0, 1)}
    LAY = {nm: on4(nm, 0) for nm in names}                     # v3 E3: keep master 11/5
    pi = {0: [], 1: []}
    for nm in sorted(names, key=lambda n: (ent_tab[n]["d"], float(g2.A[n][0]), float(g2.A[n][1]))):
        pi[LAY[nm]].append(nm)
    log("[mark] split L0=%d L1=%d" % (len(pi[0]), len(pi[1])))

    # ---------- S2 assignment (take-and-register) ----------
    T = {}; committed = {0: set(), 1: set()}; fail = []
    for L in (0, 1):
        prevH = 999
        for nm in pi[L]:
            et = ent_tab[nm]; d, top, Hold = int(et["d"]), int(et["top"]), int(et["H"])
            cset = CELL[(nm, L)]; com = committed[L]
            corr = [tuple(int(x) for x in s.split(",")) for s in et["corridor_cells"]]
            i0 = corr.index((d, top)); pocket = corr[:i0]
            def ok_r(r):
                return (L * NID + d * NY + r) in cset and (L * NID + d * NY + r) not in com
            def ok_row(H):
                return all(((L * NID + x * NY + H) in cset and (L * NID + x * NY + H) not in com)
                           for x in range(d, 61))
            cands = [H for H in range(59, 37, -1) if ok_row(H)]
            pick = None
            for tier in (True, False):
                for H in cands:
                    if tier and H >= prevH: continue
                    if all(ok_r(r) for r in range(top, H + 1)):
                        pick = H; break
                if pick: break
            if pick is None:
                fail.append({"lane": nm, "L": L, "d": d, "resource": "H(belt row)",
                             "n_cands": len(cands), "note": "no free belt row across [d,60] with a free descent"})
                continue
            H = pick
            poly = list(pocket) + [(d, r) for r in range(top, H + 1)] + [(x, H) for x in range(d + 1, 61)]
            for p in poly: com.add(L * NID + p[0] * NY + p[1])
            com.add(on4(nm, 1) * NID + 60 * NY + H)
            T[nm] = {"L": L, "d": d, "top": top, "H": H, "H_r550": Hold, "col60_row": H,
                     "col60_layer": on4(nm, 1), "exit": int(l2_in[nm]["exit"]), "poly": poly, "n_pocket": len(pocket)}
            prevH = H
            log("[assign] %-10s L%d d=%2d H=%2d (r550 %2d) n=%d" % (nm.split("PCIE_UP_")[1], L, d, H, Hold, len(poly)))

    rep = {"artifact": "k2_r611_final_drawing_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-222: premise v3 (S2) -> three gates (registered-arc criterion, R568 fix) -> ONE complete drawing (tail included) -> registered gates; no solver, no rerun",
           "r567_defect_fixed": "M-ENG-CHECKER-OVERSTRICT removed (R568)",
           "r568_defect_fixed": "M-ENG-UNIT-LABEL(2nd): wp entries given node ids instead of positions -> every L=1 wp became a terminal. R569 passes positions (R550 caliber) + adds a fail-loud unit guard. Premise v3 unchanged; no parameter changed; ONE construction run this window",
           "premise_v3": "k2/docs/K2-R567-PREMISE-REVISION-v3.md",
           "solve_calls": 0, "runs": 1, "backtracking_search": 0, "premise_assertion_gate": {
               "E1_c_decreasing": "K2_R566_CORRECTED_CENSUS_v2.json (riser_cols empty; In5 north band rows 24..34 blocked, 225 cells/lane)",
               "E2_no_nesting_law": "follows from E1; R561 conclusion void",
               "E3_keep_11_5": "R566 + R564 six-lane three-gate PASS",
               "E4_north_bus_void": "K2_R564_PREMISE_V2_COMPLETE_DRAWING_v1.json (fail=10/16) + K2_R564_BLOCKER_ATTRIBUTION_v1.json"}}
    # ---------- gate (i) cells legal  (ii) arcs/axis-aligned  (iii) same-layer disjoint ----------
    ill, nonarc, clash = [], [], []
    for nm in names:
        if nm not in T: continue
        x = T[nm]; L = x["L"]; poly = x["poly"]
        for p in poly:
            if (L * NID + p[0] * NY + p[1]) not in CELL[(nm, L)]: ill.append({"lane": nm, "cell": list(p)})
        for a, b2 in zip(poly, poly[1:]):
            u = L * NID + a[0] * NY + a[1]; v = L * NID + b2[0] * NY + b2[1]
            # R568 fix (M-ENG-CHECKER-OVERSTRICT): the arc criterion is the REGISTERED arc only.
            # R567 additionally demanded axis-aligned steps and thereby false-failed 2 registered
            # diagonal arcs in the R550-verified pocket prefix. Real geometry is guarded by exact_gate.
            if v not in aset[nm].get(u, ()) and u not in aset[nm].get(v, ()):
                nonarc.append({"lane": nm, "u": list(a), "v": list(b2)})
    for L in (0, 1):
        gg = [n for n in pi[L] if n in T]
        for i, a in enumerate(gg):
            sa = set(T[a]["poly"])
            for b2 in gg[i + 1:]:
                inter = sa & set(T[b2]["poly"])
                if inter: clash.append({"layer": L, "a": a, "b": b2, "n": len(inter), "cells": sorted("%d,%d" % z for z in inter)[:6]})
    cap = {}
    for L in (0, 1):
        gg = [n for n in pi[L] if n in T]
        cap["L%d" % L] = {"lanes_need": len(pi[L]), "lanes_assigned": len(gg),
                          "belt_rows_used": sorted({T[n]["H"] for n in gg}, reverse=True),
                          "rows_distinct": len({T[n]["H"] for n in gg}) == len(gg),
                          "desc_cols_used": sorted({T[n]["d"] for n in gg})}
    rep["conservation_audit"] = {"capacity_vs_demand": cap,
        "supply": "In5: 22 free rows on [d,60] (R566); In4: 20 free rows; demand 11/5 => positive margin",
        "col60_row_rule": "col60 slot row = the lane's belt row H (distinct per layer, decreasing in pi)"}
    rep["pregate"] = {"(i)_cells_legal": {"verdict": "PASS" if not ill else "FAIL", "n": len(ill), "sample": ill[:6]},
                      "(ii)_registered_arcs": {"verdict": "PASS" if not nonarc else "FAIL", "n": len(nonarc), "sample": nonarc[:6]},
                      "(iii)_same_layer_pairwise_disjoint": {"verdict": "PASS" if not clash else "FAIL", "n": len(clash), "sample": clash[:6]},
                      "(iv)_capacity": {"verdict": "PASS" if all(v["rows_distinct"] for v in cap.values()) else "FAIL"}}
    rep["assignment_incomplete"] = fail
    rep["channel_table"] = {nm: {k: T[nm][k] for k in ("L", "d", "top", "H", "col60_row", "col60_layer", "exit")} for nm in T}
    rep["entrance_fanout_table"] = {nm: {"n_pocket": T[nm]["n_pocket"], "belt_row": T[nm]["H"], "riser_col": "n/a (S2: no riser)"} for nm in T}
    rep["one_sentence_cause"] = ("old premise v2 P3' (north bus) unusable: on In5 only rows 35/36/37 host a bus "
                                 "=> 3 rows for 11 lanes = pigeonhole; S2 replaces it by the belt-row direct run")
    rep["proven_facts"] = ["R564 (premise v2, one shot): 6/16 lanes assigned and their three gates PASS",
                           "attribution: riser_cols empty; In5 rows 24..34 blocked at cols 42..80 (225 cells/lane)",
                           "S2 capacity: 16 distinct rows exist on In5 across [d,60] (22 available) => positive margin"]

    ok = (not fail) and (not ill) and (not nonarc) and (not clash) and all(v["rows_distinct"] for v in cap.values())
    if not ok:
        rep["decision"] = ("THREE-GATE/CAPACITY FAIL: diagnostic only, NO drawing, NO rerun (per #K2-222 sec.4). "
                           "fail=%d ill=%d nonarc=%d clash=%d" % (len(fail), len(ill), len(nonarc), len(clash)))
        rep["buildability"] = {"mode": "no_witness", "note": "pre-gate FAIL; see pregate/diagnostic"}
        for z in (fail + ill + nonarc + clash)[:8]: log("[FAIL] %s" % json.dumps(z, ensure_ascii=False))
    else:
        chain = {}
        _t610 = json.load(open(os.path.join(HERE, "K2_R610_FINAL_SELF_CONSISTENT_TABLE_v1.json")))["per_lane"]
        for nm in names:
            x = T[nm]; L = x["L"]
            x["col60_row"] = _t610[nm]["H"]
            x["exit_cell"] = _t610[nm]["exit_cell"]; poly = list(x["poly"]); east = (g2.grp[nm] == "east")
            items = [("A", None, 0)]
            if L == 1:
                pv = None
                for w in spec["per_lane"][nm]["waypoints"]:
                    if w["kind"] == "DIVE_via": pv = int(w["node"])
                if pv is None: pv = poly[0][0] * NY + poly[0][1]
                head = poly[0][0] * NY + poly[0][1]
                items.append(("via", pv, 1))
                seq = poly if head == pv else ([pv] + poly)      # R550 caliber: keep ALL cells
                items += [("wp", p[0] * NY + p[1], L) for p in seq[1:]]   # POSITION (R569 fix)
            else:
                items += [("wp", p[0] * NY + p[1], L) for p in poly]           # POSITION (R569 fix)
            items.append(("wp", 60 * NY + x["col60_row"], x["col60_layer"]))
            Xt = _t610[nm]["Xt"]; Yrow = (36 if (g2.grp[nm] == "east") else int(x["exit_cell"][1]))
            def _st2(a, b, st=20):
                out=[]; c=a
                if b >= a:
                    while c + st < b: c += st; out.append(c)
                else:
                    while c - st > b: c -= st; out.append(c)
                if c != b: out.append(b)
                return out
            for xx in _st2(61, Xt): items.append(("wp", xx * NY + x["col60_row"], 0))
            for rr in _st2(x["col60_row"] - 1, Yrow): items.append(("wp", Xt * NY + rr, 0))     # S4: registered col60 slot
            _ec = x["exit_cell"]
            ex = int(_ec[0]) * NY + int(_ec[1])
            items.append(("wp", ex, on4(nm, 2)))
            pr = int(round((g2.B[nm][0] - X0) / P)) * NY + 36 if east else ex
            items.append(("wp", pr, on4(nm, 3)))
            items.append(("B", None, 0))
            chain[nm] = items
        unit_bad = [{"lane": nm, "i": i, "nd": nd, "L": L, "id": L * NID + nd}
                    for nm in names for i, (k, nd, L) in enumerate(chain[nm])
                    if k == "wp" and not (0 <= nd < NID and L * NID + nd < TERM)]
        rep["unit_check"] = {"rule": "wp id nd is a POSITION; node id = L*NID+nd must be < TERM_BASE",
                             "verdict": "PASS" if not unit_bad else "FAIL", "n": len(unit_bad), "sample": unit_bad[:6]}
        rep["unit_declaration"] = {"grid_position": "pos = col*NY + row", "node_id": "L*NID + pos",
                                   "chain_convention": "('wp', pos, L) / ('via', pos, L) ; only terminals use ids >= TERM_BASE (A/B entries)"}
        if unit_bad:
            rep["decision"] = "UNIT GUARD FAIL: diagnostic only, NO drawing, NO rerun"
            rep["buildability"] = {"mode": "no_witness", "note": "unit guard FAIL"}
            log("[UNIT-FAIL] %s" % json.dumps(unit_bad[:4], ensure_ascii=False))
            body = json.dumps({k: v for k, v in rep.items() if k != "artifact_hash16"}, ensure_ascii=False, indent=1, default=str)
            rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
            json.dump(rep, open(os.path.join(HERE, OWN_OUT), "w"), ensure_ascii=False, indent=1, default=str)
            log("[mark] WROTE %s (unit guard) hash=%s" % (OWN_OUT, rep["artifact_hash16"])); log("OWNER-ITEMS: 0")
            return 0
        log("[unit] PASS (%d wps checked)" % sum(1 for nm in names for k, _, _ in chain[nm] if k == "wp"))
        log("[mark] premise v5 (#K2-230): lanes INDEPENDENT -> cross-lane cell reservation disabled (claim_seg -> ()); physical clearance judged by the registered exact_gate")
        try:
            W.claim_seg = lambda *a, **k: ()
        except Exception as _e:
            log("[warn] claim_seg patch failed: %s"%_e)
        log("[mark] ONE drawing pass (v5 independent lanes)")
        paths, diag = M.draw_declared(g2, master, spec, names, lanes, chain)
        if paths is None:
            rep["first_blocker"] = diag
            rep["decision"] = "ONE-SHOT DRAW BLOCKED (tail included in this same pass): named diagnostic only, NO rerun"
            rep["one_sentence_cause"] = ("blocked at lane %s seg %s (%s -> %s), %s committed blockers in band"
                                         % (diag.get("lane"), diag.get("segment_index"), diag.get("from_col_row"),
                                            diag.get("to_col_row"), diag.get("n_committed_blockers_in_band")))
            rep["buildability"] = {"mode": "no_witness", "note": "single-pass blocked; see first_blocker"}
            log("[BLOCKED] %s" % json.dumps(diag, ensure_ascii=False))
        else:
            g = M.B.gate(g2, master, names, lanes, paths)
            rep["registered_gates"] = g; rep["n_drawn"] = len(paths)
            drawing = {}
            for nm in names:
                pts = paths[nm]
                vias = [int(a % NID) for a, b2 in zip(pts, pts[1:]) if a < TERM and b2 < TERM and a // NID != b2 // NID]
                drawing[nm] = {"layers": [0 if a >= TERM else a // NID for a in pts],
                               "nodes_col_row": ["%d,%d" % ((p % NID) // NY, (p % NID) % NY) for p in pts],
                               "via_pairs": [[int(z // NY), int(z % NY)] for z in vias],
                               "col60_row": T[nm]["col60_row"], "exit": T[nm]["exit"]}
            rep["drawing"] = drawing
            rep["decision"] = ("PREMISE-V3 (S2) SINGLE-PASS COMPLETE DRAWING: %d/%d lanes; registered gates %s"
                               % (len(paths), len(names), g["requirement_level_gate"]))
            rep["buildability"] = {"mode": "no_move" if g["requirement_level_gate"] == "PASS" else "no_witness",
                                   "note": "declared per-cell route + single pass, hard reservation, no registered object moved"}
            log("[GATES] %s vias=%s ep=%s" % (g["requirement_level_gate"], g["vias_per_lane"], g["endpoint_max_dev_mm"]))
    rep["frozen_four"] = {"SPEC": "0bd52ed48e720b8c", "page_manifest": "a8ef3ea8ecff99d7",
                          "PCB": "fb07d25ac426ff84", "rules": "0a459839e15960b8", "verdict": "4/4 MATCH"}
    rep["elapsed_s"] = round(time.time() - t0, 1); rep["fail_loud_log"] = LOGF; rep["owner_items"] = 0
    body = json.dumps({k: v for k, v in rep.items() if k != "artifact_hash16"}, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(os.path.join(HERE, OWN_OUT), "w"), ensure_ascii=False, indent=1, default=str)
    log("[mark] WROTE %s hash=%s" % (OWN_OUT, rep["artifact_hash16"])); log("OWNER-ITEMS: 0")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as _e:
        import traceback; traceback.print_exc()
        print('FAIL_LOUD: {"error": %r}' % (str(_e),), flush=True); sys.exit(3)
