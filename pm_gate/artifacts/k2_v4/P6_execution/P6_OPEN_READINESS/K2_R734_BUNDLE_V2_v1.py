#!/usr/bin/env python3
"""K2 R734 --- #K2-278 sec.3.4 : WHOLE-VERSION BUNDLE RE-ASSIGNMENT v2, ONE run, product paradigm.

Method switch in force (#K2-278 sec.3.3): no per-line patch. Product order = BUNDLE GROUPING -> EXIT ALLOCATION ->
ESCAPE-BAND ALLOCATION (REF-CASE-LIBRARY sec.A.1 + R633 three rules).
Level (#K2-278 sec.3.2): exit gates may be re-allocated ONLY among the ALREADY REGISTERED wall gaps of the SAME
group - no wall-gap physical opening is moved/added/removed; no cross-wall / cross-group move.

Declared construction (domain = 1 per lane given the declared order):
  * groups      : W = the 8 lanes exiting through the col-114 wall gaps ; E = the 8 lanes exiting on row 36
  * lane order  : within a group, ascending by the lane's REGISTERED run row H (the fan-out order)
  * exit alloc  : the group's registered gates sorted by row (W) / by column (E); lane k gets gate k (ordered escape)
  * layer split : W -> run + descent on layer 1 ; E -> run + descent on layer 0 ; the escape always lands on the
                  gate's registered exit layer (corner via if the layers differ)
  * escape band : E descends at (gate column + 1) so the escape is one cell; W descends at an even column east of the
                  wall, the escape runs west along the gate row to col 114
  * monotone    : within a group H and the descent column both INCREASE with the lane order  => the bundle cannot cross
"""
import sys, os, json, types, importlib, hashlib, time, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "K2_R734_BUNDLE_V2_v1.json")
LOGF = os.path.join(HERE, "K2_R734_solve.log")
LH = open(LOGF, "w")
def log(m): LH.write(str(m) + "\n"); LH.flush(); print(str(m), flush=True)
for nm in ("ortools", "ortools.sat", "ortools.sat.python"): sys.modules.setdefault(nm, types.ModuleType(nm))
cm = types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self, *a, **k): pass
cm.CpModel = _D; cm.CpSolver = _D
sys.modules["ortools.sat.python.cp_model"] = cm; sys.modules["ortools.sat.python"].cp_model = cm
M = importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1"); PREV = M.PREV; PREV.Gen._build_edges = M._build_edges_fixed
W = M.W; NID = W.NID
def rc(u): u %= NID; return u // W.NY, u % W.NY
def sh16(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
def adj(a, b):
    if a[0] == b[0]: return abs(a[1][0] - b[1][0]) + abs(a[1][1] - b[1][1]) == 1
    return a[1] == b[1]

def main():
    t0 = time.time()
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full"); names = list(g2.names)
    T = json.load(open(os.path.join(HERE, "K2_R613_FINAL_TABLE_VIA_OK_v1.json")))["per_lane"]
    EX = {nm: (int(T[nm]["exit_cell"][0]), int(T[nm]["exit_cell"][1])) for nm in names}
    EL = {nm: int(T[nm]["exit_layer"]) for nm in names}
    Hreg = {nm: int(T[nm]["H"]) for nm in names}
    frozen = [("SPEC", "/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json", "0bd52ed48e720b8c"),
              ("manifest", "/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_s1_page_manifest.json", "a8ef3ea8ecff99d7"),
              ("PCB", "/home/fila/jqdDev_2025/ic_hw/k2/k2_v4_8L.kicad_pcb", "fb07d25ac426ff84"),
              ("rules", "/home/fila/jqdDev_2025/ic_hw/_shared/eda_core/drc_rules.json", "0a459839e15960b8")]
    froz = {k: {"sha16": sh16(p), "expected": e, "match": sh16(p) == e} for k, p, e in frozen}
    node_ok = {}; via_ok = {}
    for nm in names:
        node_ok[nm] = {L: {rc(i) for i in np.nonzero(g2._nok[(nm, L)] & g2.region_ok(nm, L))[0]} for L in (0, 1)}
        via_ok[nm] = {rc(i) for i in np.nonzero(g2._viaok[nm])[0]}
    # ---- groups + registered gates ----
    Wl = sorted([nm for nm in names if EX[nm][0] == 114], key=lambda nm: Hreg[nm])
    El = sorted([nm for nm in names if EX[nm][1] == 36], key=lambda nm: Hreg[nm])
    Wgates = sorted([EX[nm][1] for nm in Wl]); Egates = sorted([EX[nm][0] for nm in El])
    log("group W (%d): %s | gates(rows) %s" % (len(Wl), [n.replace('PCIE_UP_', '') for n in Wl], Wgates))
    log("group E (%d): %s | gates(cols) %s" % (len(El), [n.replace('PCIE_UP_', '') for n in El], Egates))
    committed = set(); routes = {}; assign = {}; fails = []
    def tryroute(nm, eL, t, cl, c, H, e_col, e_row, committed):
        cells = [(cl, (60, H))]; vias = []
        if cl != t: vias.append((60, H)); cells.append((t, (60, H)))
        cells += [(t, (x, H)) for x in range(61, c + 1)]
        cells += [(t, (c, r)) for r in range(H - 1, e_row, -1)]
        if t != eL: vias.append((c, e_row))
        cells.append((eL, (c, e_row)))
        cells += [(eL, (x, e_row)) for x in range(c - 1, e_col - 1, -1)]
        if len(set(cells)) != len(cells): return None
        for (L, cp) in cells:
            if cp not in node_ok[nm][L] or (L, cp) in committed: return None
        for cp in vias:
            if cp not in via_ok[nm] or cp not in node_ok[nm][0] or cp not in node_ok[nm][1]: return None
        return cells
    def assign_group(lanes, gates, kind):
        nonlocal committed
        prevH = -1; prevC = -1
        for k, nm in enumerate(lanes):
            eL = EL[nm]
            if kind == "W":
                gate = gates[k]; c_cands = [c for c in range(116, 138, 2) if c > prevC]
                H_cands = [h for h in range(41, 60) if h > prevH]
                e_col, e_row, t, cl = 114, gate, 1, 1
            else:
                gate = gates[k]; c_cands = [gate + 1, gate + 2, gate + 3]
                c_cands = [c for c in c_cands if c > prevC and c < 138]
                H_cands = [h for h in range(39, 60) if h > prevH]
                e_col, e_row, t, cl = gate, 36, 0, 0
            got = None
            for c in c_cands:
                for H in H_cands:
                    cells = tryroute(nm, eL, t, cl, c, H, e_col, e_row, committed)
                    if cells: got = (c, H, cells); break
                if got: break
            if got is None:
                fails.append([nm, kind, gate, "no feasible bundle route in the declared monotone order"]); continue
            c, H, cells = got
            routes[nm] = cells; committed |= set(cells); prevH = H; prevC = c
            assign[nm] = {"gate": [e_col, e_row], "gate_layer": eL, "run_layer": t, "slot_layer": cl,
                          "descent_column": c, "run_row": H, "cells": len(cells)}
            log("%-13s %s gate(%d,%d)@L%d run L%d row %2d descent col %3d  (%d cells)" %
                (nm.replace("PCIE_UP_", ""), kind, e_col, e_row, eL, t, H, c, len(cells)))
    assign_group(Wl, Wgates, "W")
    assign_group(El, Egates, "E")
    # ---- gates ----
    own = collections.Counter()
    for nm in routes:
        for cp in set(routes[nm]): own[cp] += 1
    ov = [c for c, v in own.items() if v > 1]
    noncont = [nm for nm in routes if any(not adj(routes[nm][i - 1], routes[nm][i]) for i in range(1, len(routes[nm])))]
    gates_used = [tuple(assign[nm]["gate"]) for nm in routes]
    registered = set(EX.values())
    cons = {"lanes": 16, "rows_assigned": len(routes), "rows_failed": [f[0].replace("PCIE_UP_", "") for f in fails],
            "merged_0_conflict": len(ov) == 0, "conflict_cells": len(ov), "conflicts": [[c[0], list(c[1])] for c in ov[:20]],
            "FOURTH_KEY_physical_disjoint": len(ov) == 0, "rows_continuous": 16 - len(fails) - len(noncont),
            "non_continuous": [n.replace("PCIE_UP_", "") for n in noncont],
            "exit_gates_all_registered": all(g in registered for g in gates_used),
            "exit_gates_distinct": len(set(gates_used)) == len(gates_used),
            "col60_slots_distinct": len({(routes[nm][0][0], routes[nm][0][1][1]) for nm in routes}) == len(routes),
            "cells_distinct": len(own), "capacity_ge_demand": len(own) >= sum(len(set(routes[nm])) for nm in routes)}
    gate_realloc = {nm.replace("PCIE_UP_", ""): {"registered_exit": list(EX[nm]), "allocated_exit": assign[nm]["gate"]}
                    for nm in routes if list(EX[nm]) != assign[nm]["gate"]}
    ok = (len(routes) == 16 and len(ov) == 0 and not noncont and cons["exit_gates_all_registered"]
          and cons["exit_gates_distinct"] and all(v["match"] for v in froz.values()))
    rep = {"artifact": "k2_r734_bundle_v2_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-278 sec.3.4: whole-version bundle re-assignment v2 (L2, product order: bundle grouping -> exit allocation -> escape-band allocation), ONE run",
           "hard_declaration": {"wall_gap_physical_opening_changes": 0,
                                "note": "exit gates are re-allocated ONLY among the ALREADY REGISTERED wall gaps of the same group; no physical wall-gap opening is moved, added or removed; no cross-wall / cross-group move"},
           "cause_of_death": "the 5-window per-line patch route is machine-proved infeasible; the 16 lanes must be allocated as ONE bundle in the product order (grouping -> exit allocation -> escape band)",
           "construction_runs": 1, "drawings": 0, "gerber_exported": False, "p5": False, "order": False,
           "frozen_four_distance": froz, "changes_to_frozen_sources": 0 if all(v["match"] for v in froz.values()) else "FROZEN MISMATCH",
           "bundle": {"groups": {"W": [n.replace("PCIE_UP_", "") for n in Wl], "E": [n.replace("PCIE_UP_", "") for n in El]},
                      "declared_gates": {"W_rows": Wgates, "E_cols": Egates},
                      "order": "within a group ascending by the registered run row; lane k gets the k-th gate (ordered escape)",
                      "layer_split": "W -> layers run/descent L1; E -> L0; the escape lands on the gate's registered exit layer",
                      "monotone": "within a group H and the descent column both increase with the lane order"},
           "exit_gate_reallocation": gate_realloc,
           "routes": {nm.replace("PCIE_UP_", ""): dict(assign[nm], walk=[[L, list(cp)] for (L, cp) in routes[nm]]) for nm in routes},
           "conservation": cons, "failures": fails,
           "buildability": {"mode": "relocation_listed",
                            "note": "all 16 rows re-assigned as one bundle; exit gates re-allocated among registered wall gaps of the same group only"},
           "product_comparison_column": {nm.replace("PCIE_UP_", ""):
                        ("W bundle: long run on L1, monotone descent, short escape west along the gate row on the registered exit layer"
                         if nm in Wl else
                         "E bundle: long run on L0, descent one column east of the gate, one-cell escape; bundles ordered so none crosses")
                        for nm in routes},
           "product_three_questions": {"①same_kind": "PEX88096 PCIe4 switch GPU baseboard kit (REF-CASE-LIBRARY sec.A.1)",
               "②copyable": "BGA fan-out, lane grouping/routing, 1OZ layer-change escape; one group one bundle / long straight run / one layer change at the fan-out / no overlap between bundles",
               "③differences": "now copied: bundle grouping + exit allocation + escape-band allocation in the product order; the previously shared row-36 escape band is now allocated per bundle with monotone ordering"},
           "verdict": ("BUNDLE_16OF16_PASS" if ok else "BOUNCE_DRAWING_LAYER"),
           "binary": ("BUNDLE_16OF16_PASS" if ok else "BOUNCE_DRAWING_LAYER"),
           "elapsed_s": round(time.time() - t0, 1)}
    body = json.dumps(rep, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(OUT, "w"), ensure_ascii=False, indent=1, default=str)
    log("assigned %d/16 | failed=%s | conflicts=%d | continuous=%s | gates_registered=%s" %
        (len(routes), [f[0].replace("PCIE_UP_", "") for f in fails], len(ov), cons["rows_continuous"], cons["exit_gates_all_registered"]))
    log("WROTE %s hash=%s binary=%s" % (OUT, rep["artifact_hash16"], rep["binary"]))
    log("OWNER-ITEMS: 0")
    return 0

if __name__ == "__main__":
    sys.exit(main())
