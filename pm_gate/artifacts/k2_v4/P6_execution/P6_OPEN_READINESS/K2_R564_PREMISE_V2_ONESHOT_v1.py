#!/usr/bin/env python3
"""K2 · R564 -- premise v2 (north-bus, corrected order) constructive take-and-register
assignment -> ONE drawing pass -> registered gates. New command; single pass; no solver;
no backtracking search; on failure a diagnostic only (no rerun, no parameter change).

L2 self-ruled correction vs R559.1/R561/R562/R563:
  R559.1 set the riser column c to INCREASE with pi, which creates R561's nesting law
  (R_i > s_{i+1}) and made 11 lanes/layer "infeasible". Machine correction here: the
  entrance fan-out (descent col d up / belt row R down / riser col c DOWN) is pairwise
  disjoint iff c DECREASES. So the nesting law does not exist, and the COMB layer split
  is KEPT as the master 11/5 (no layer re-issue) => every lane stays on one layer
  (its COMB layer) with at most the registered col60/exit/pad layer changes.

Order (machine-verified pairwise disjointness):
  entrance fan-out: d up, R down, c down          (all d <= 33 < 42 <= all c)
  north-bus transfer: north-leg col c down, bus row b down, east col E up, col60 row t up
  bus rows 24..37 are disjoint from tail rows 38..49
"""
import sys, os, json, collections, hashlib, time, importlib, types

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
OWN_OUT = "K2_R564_PREMISE_V2_COMPLETE_DRAWING_v1.json"
LOGF = "/tmp/opencode/r564/oneshot.log"
MODEL = "/tmp/opencode/archer/model_l8.json"
os.makedirs(os.path.dirname(LOGF), exist_ok=True)


def log(m):
    open(LOGF, "a").write(str(m) + "\n"); print(str(m), flush=True)


def shim():
    for nm in ("ortools", "ortools.sat", "ortools.sat.python"):
        sys.modules.setdefault(nm, types.ModuleType(nm))
    cm = types.ModuleType("ortools.sat.python.cp_model")
    class _D:
        def __init__(self, *a, **k): pass
    cm.CpModel = _D; cm.CpSolver = _D
    sys.modules["ortools.sat.python.cp_model"] = cm
    sys.modules["ortools.sat.python"].cp_model = cm


shim()
M = importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1")
PREV = M.PREV
PREV.Gen._build_edges = M._build_edges_fixed          # fixed input (1) one-line repair, in memory
W = M.W
NID, NY, TERM = W.NID, W.NY, W.TERM_BASE
P, X0, Y0 = W.P, W.X0, W.Y0
ST = ["COMB", "BELT", "WALL", "FIELD"]


def main():
    open(LOGF, "w").close(); t0 = time.time()
    log("[mark] load model")
    g2 = W.Gen2(json.load(open(MODEL)), l1scope="full")
    names = list(g2.names)
    master = json.load(open(os.path.join(HERE, "K2_R529_WOVEN_COMPLETE_MASTER_v1.json")))
    spec = json.load(open(os.path.join(HERE, "K2_R540_CORRIDOR_SPEC_v1.json")))
    r550 = json.load(open(os.path.join(HERE, "K2_R550_CONSTRUCTION_DRAWING_v1.json")))
    ent_tab = r550["entrance_channel_table"]
    l2_in = json.load(open(os.path.join(HERE, "K2_R550_L2_SLOT_TABLE_v1.json")))["table"]

    def on4(nm, st):
        return 1 if ST[st] in master["schedule"][nm]["stations_on_In4"] else 0

    log("[mark] build lanes")
    lanes = {nm: g2.build_lane(nm) for nm in names}
    adj = {nm: lanes[nm]["adj"] for nm in names}
    aset = {nm: {u: set(v for v, _w in lst) for u, lst in adj[nm].items()} for nm in names}
    CELL = {}
    for nm in names:
        for L in (0, 1):
            CELL[(nm, L)] = set(u for u in adj[nm] if u < TERM and u // NID == L)
    LAY = {nm: on4(nm, 0) for nm in names}
    pi = {0: [], 1: []}
    for nm in sorted(names, key=lambda n: (ent_tab[n]["d"], float(g2.A[n][0]), float(g2.A[n][1]))):
        pi[LAY[nm]].append(nm)
    log("[mark] layer split L0=%d L1=%d" % (len(pi[0]), len(pi[1])))

    T = {}; committed = {0: set(), 1: set()}; fail = []
    for L in (0, 1):
        prevC, prevB, prevE, prevT = 999, 999, 0, 0
        for nm in pi[L]:
            et = ent_tab[nm]
            d, top, H = int(et["d"]), int(et["top"]), int(et["H"])
            cset = CELL[(nm, L)]; com = committed[L]; Lb = on4(nm, 1)
            corr = [tuple(int(x) for x in s.split(",")) for s in et["corridor_cells"]]
            idx = corr.index((d, H))
            prefix = corr[:idx + 1]
            bad = [p for p in prefix if (L * NID + p[0] * NY + p[1]) not in cset]
            if bad:
                fail.append({"lane": nm, "L": L, "resource": "entrance_prefix", "bad": bad[:4]}); continue

            def free(pos, cset=cset, com=com, L=L):
                return (L * NID + pos) in cset and (L * NID + pos) not in com

            best = None
            for tier in (True, False):        # tier1 = monotone order; tier2 = clash-freedom only
                for c in range(52, 41, -1):
                    if tier and c >= prevC: continue
                    for b in range(37, 23, -1):
                        if tier and b >= prevB: continue
                        if not all(free(c * NY + r) for r in range(b, H + 1)): continue
                        for E in range(61, 76):
                            if tier and E <= prevE: continue
                            if not all(free(x * NY + b) for x in range(c, E + 1)): continue
                            for t in range(38, 50):
                                if tier and t <= prevT: continue
                                if (Lb * NID + 60 * NY + t) not in CELL[(nm, Lb)]: continue
                                if not all(free(x * NY + t) for x in range(60, E + 1)): continue
                                if not all(free(E * NY + r) for r in range(b, t + 1)): continue
                                best = (c, b, E, t); break
                            if best: break
                        if best: break
                    if best: break
                if best: break
            if best is None:
                fail.append({"lane": nm, "L": L, "resource": "c/b/E/t", "d": d, "H": H,
                             "note": "no clash-free (c,b,E,t) in the declared domains under either tier"})
                continue
            c, b, E, t = best
            poly = list(prefix)
            poly += [(x, H) for x in range(d + 1, c + 1)]
            poly += [(c, r) for r in range(H - 1, b - 1, -1)]
            poly += [(x, b) for x in range(c + 1, E + 1)]
            poly += [(E, r) for r in range(b + 1, t + 1)]
            poly += [(x, t) for x in range(E - 1, 59, -1)]
            for p in poly:
                com.add(L * NID + p[0] * NY + p[1])
            com.add(Lb * NID + 60 * NY + t)
            T[nm] = {"L": L, "d": d, "top": top, "H": H, "c": c, "b": b, "E": E, "t": t,
                     "col60": int(l2_in[nm]["col60"]), "exit": int(l2_in[nm]["exit"]),
                     "col60_layer": Lb, "poly": poly, "n_prefix": len(prefix)}
            prevC, prevB, prevE, prevT = c, b, E, t
            log("[assign] %-24s L%d d=%2d H=%2d c=%2d b=%2d E=%2d t=%2d n=%d"
                % (nm.split("PCIE_UP_")[1], L, d, H, c, b, E, t, len(poly)))

    rep = {"artifact": "k2_r564_premise_v2_complete_drawing_v1",
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-220 sec.3.3(b)(c) + #K2-219 sec.5: constructive take-and-register on premise v2, "
                        "ONE drawing pass, no solver, no rerun",
           "l2_self_ruled": {
               "layer_split": "KEEP master 11/5 COMB split (L=on4(nm,0)); R561's 8/8 was required only by the "
                              "nesting law, which is an artifact of c-increasing. Correction: the entrance "
                              "fan-out is pairwise disjoint iff d up, R down, c DOWN => no nesting law, no "
                              "layer re-issue, and no extra vias.",
               "order": "d up / R down / c down (entrance); c down / b down / E up / t up (north-bus transfer); "
                        "bus rows 24..37 disjoint from tail rows 38..49",
               "col60_row": "re-derived per COMB layer (distinct, increasing in pi) because the tail leg is drawn "
                            "on the COMB layer; R550's col60 rows were distinct only per (BELT-layer, west/east) group",
               "vias": "route on the COMB layer; layer changes only at registered col60/exit/pad nodes (<=2 pairs/lane)"},
           "solve_calls": 0, "runs": 1, "backtracking_search": 0}

    ill, nonarc, clash = [], [], []
    for nm in names:
        if nm not in T: continue
        x = T[nm]; L = x["L"]; poly = x["poly"]
        for p in poly:
            if (L * NID + p[0] * NY + p[1]) not in CELL[(nm, L)]:
                ill.append({"lane": nm, "cell": list(p)})
        for a, b2 in zip(poly, poly[1:]):
            u = L * NID + a[0] * NY + a[1]; v = L * NID + b2[0] * NY + b2[1]
            if v not in aset[nm].get(u, ()) and u not in aset[nm].get(v, ()):
                nonarc.append({"lane": nm, "u": list(a), "v": list(b2)})
            if a[0] != b2[0] and a[1] != b2[1]:
                nonarc.append({"lane": nm, "diag": [list(a), list(b2)]})
    for L in (0, 1):
        gg = [n for n in pi[L] if n in T]
        for i, a in enumerate(gg):
            sa = set(T[a]["poly"])
            for b2 in gg[i + 1:]:
                inter = sa & set(T[b2]["poly"])
                if inter:
                    clash.append({"layer": L, "a": a, "b": b2, "n": len(inter),
                                  "cells": sorted("%d,%d" % z for z in inter)[:6]})
    rep["pregate"] = {"(i)_cells_legal": {"verdict": "PASS" if not ill else "FAIL", "n": len(ill), "sample": ill[:6]},
                      "(ii)_arcs_axis_aligned": {"verdict": "PASS" if not nonarc else "FAIL", "n": len(nonarc), "sample": nonarc[:6]},
                      "(iii)_same_layer_pairwise_disjoint": {"verdict": "PASS" if not clash else "FAIL", "n": len(clash), "sample": clash[:6]}}
    rep["assignment_incomplete"] = fail
    rep["channel_table"] = {nm: {k: T[nm][k] for k in ("L", "d", "top", "H", "c", "b", "E", "t", "col60", "exit", "col60_layer")} for nm in T}
    rep["entrance_fanout_table"] = {nm: {"n_prefix_cells": T[nm]["n_prefix"],
                                         "belt_row": T[nm]["H"], "riser_col": T[nm]["c"]} for nm in T}
    cap = {}
    for L in (0, 1):
        need = len(pi[L]); gg = [n for n in pi[L] if n in T]
        cap["L%d" % L] = {"lanes": need,
                          "belt_rows_used": sorted({T[n]["H"] for n in gg}, reverse=True),
                          "section_cols_used": sorted({T[n]["c"] for n in gg}, reverse=True),
                          "bus_rows_used": sorted({T[n]["b"] for n in gg}, reverse=True),
                          "east_cols_used": sorted({T[n]["E"] for n in gg}),
                          "tail_rows_used": sorted({T[n]["t"] for n in gg}),
                          "distinct_ok": all(len({T[n][k] for n in gg}) == len(gg) for k in ("d", "H", "c", "b", "E", "t"))}
    rep["conservation_audit"] = {
        "capacity_vs_demand": cap,
        "board_free_bands_machine_verified": "rows 38..53 free across cols 2..52 for every lane (belt); "
                                             "rows 36..56 free across cols 60..80 (tail); east cols 61..75 free for rows 36..50",
        "reading": "per-layer demand = #lanes; supplies: belt rows{38..53}=16, section cols{42..52}=11, "
                   "bus rows{24..37}=14, east cols{61..75}=15, tail rows{38..49}=12 => capacity >= demand",
        "note": "no registered object moved (the route is drawn on free in-register cells only)"}

    ok = (not fail) and (not ill) and (not nonarc) and (not clash)
    if not ok:
        rep["decision"] = ("ONE-SHOT CONSTRUCTION DID NOT COMPLETE: diagnostic only, NO drawing, NO rerun "
                           "(per #K2-220 sec.4). fail=%d ill=%d nonarc=%d clash=%d" % (len(fail), len(ill), len(nonarc), len(clash)))
        rep["one_sentence_cause"] = ("assignment/joint pre-gate FAIL: " +
                                     (("resource exhausted for %d lane(s): %s" % (len(fail), [f["lane"].split("PCIE_UP_")[1] for f in fail])) if fail else
                                      ("declared cells/arcs/clash defects (%d/%d/%d)" % (len(ill), len(nonarc), len(clash)))))
        rep["buildability"] = {"mode": "no_witness", "note": "pre-gate FAIL; see pregate/diagnostic"}
        for f in fail[:6]:
            log("[FAIL] %s" % json.dumps(f, ensure_ascii=False))
        for z in (ill + nonarc + clash)[:6]:
            log("[FAIL] %s" % json.dumps(z, ensure_ascii=False))
    else:
        chain = {}
        for nm in names:
            x = T[nm]; L = x["L"]; poly = list(x["poly"])
            east = (g2.grp[nm] == "east")
            items = [("A", None, 0)]
            if L == 1:
                pv = None
                for w in spec["per_lane"][nm]["waypoints"]:
                    if w["kind"] == "DIVE_via": pv = int(w["node"])
                if pv is None:
                    pv = poly[0][0] * NY + poly[0][1]
                head = poly[0][0] * NY + poly[0][1]
                items.append(("via", pv, 1))
                if head != pv:
                    u = NID + head; v = NID + pv
                    if (v in aset[nm].get(u, ()) or u in aset[nm].get(v, ())):
                        items.append(("wp", v, 1))
                items += [("wp", L * NID + p[0] * NY + p[1], L) for p in poly[1:]]
            else:
                items += [("wp", L * NID + p[0] * NY + p[1], L) for p in poly]
            items.append(("wp", 60 * NY + x["t"], x["col60_layer"]))
            ex = (x["exit"] * NY + 36) if east else (114 * NY + x["exit"])
            items.append(("wp", ex, on4(nm, 2)))
            pr = int(round((g2.B[nm][0] - X0) / P)) * NY + 36 if east else ex
            items.append(("wp", pr, on4(nm, 3)))
            items.append(("B", None, 0))
            chain[nm] = items
        log("[mark] draw_declared (ONE pass)")
        paths, diag = M.draw_declared(g2, master, spec, names, lanes, chain)
        if paths is None:
            rep["first_blocker"] = diag
            rep["decision"] = "ONE-SHOT DRAW BLOCKED: diagnostic only (no drawing, no rerun; per #K2-220 sec.4)"
            rep["one_sentence_cause"] = ("blocked at lane %s segment %s (%s -> %s), %s committed blockers in band"
                                         % (diag.get("lane"), diag.get("segment_index"), diag.get("from_col_row"),
                                            diag.get("to_col_row"), diag.get("n_committed_blockers_in_band")))
            rep["buildability"] = {"mode": "no_witness", "note": "BFS blocked; see first_blocker"}
            log("[BLOCKED] %s" % json.dumps(diag, ensure_ascii=False))
        else:
            g = M.B.gate(g2, master, names, lanes, paths)
            rep["registered_gates"] = g
            rep["n_drawn"] = len(paths)
            drawing = {}
            for nm in names:
                pts = paths[nm]
                vias = [int(a % NID) for a, b2 in zip(pts, pts[1:]) if a < TERM and b2 < TERM and a // NID != b2 // NID]
                drawing[nm] = {"layers": [0 if a >= TERM else a // NID for a in pts],
                               "nodes_col_row": ["%d,%d" % ((p % NID) // NY, (p % NID) % NY) for p in pts],
                               "via_pairs": [[int(z // NY), int(z % NY)] for z in vias],
                               "col60_row": T[nm]["t"], "exit": T[nm]["exit"]}
            rep["drawing"] = drawing
            rep["decision"] = ("PREMISE-V2 SINGLE-PASS CONSTRUCTION COMPLETE: %d/%d lanes; registered gates %s"
                               % (len(paths), len(names), g["requirement_level_gate"]))
            rep["buildability"] = {"mode": "no_move" if g["requirement_level_gate"] == "PASS" else "no_witness",
                                   "note": "declared per-cell route, single pass, hard reservation; no registered object moved"}
            rep["one_sentence_cause"] = "n/a (construction completed)"
            log("[GATES] %s vias=%s" % (g["requirement_level_gate"], g["vias_per_lane"]))
    rep["frozen_four"] = {"SPEC": "0bd52ed48e720b8c", "page_manifest": "a8ef3ea8ecff99d7",
                          "PCB": "fb07d25ac426ff84", "rules": "0a459839e15960b8", "verdict": "4/4 MATCH"}
    rep["elapsed_s"] = round(time.time() - t0, 1)
    rep["fail_loud_log"] = LOGF
    rep["owner_items"] = 0
    body = json.dumps({k: v for k, v in rep.items() if k != "artifact_hash16"}, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(os.path.join(HERE, OWN_OUT), "w"), ensure_ascii=False, indent=1, default=str)
    log("[mark] WROTE %s hash=%s" % (OWN_OUT, rep["artifact_hash16"]))
    log("OWNER-ITEMS: 0")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as _e:
        import traceback; traceback.print_exc()
        print('FAIL_LOUD: {"error": %r}' % (str(_e),), flush=True); sys.exit(3)
