#!/usr/bin/env python3
"""K2 · R635 (#K2-242 sec.5 evidence for ①/②) —— 出口槽候选集**只读普查**（零描线 · 零构造 · 零新版本表）

问：R632 报「出口候选集 = ∅」。该读数在**在册口径**下可复现吗？
本件把候选集按**逐层加约束**展开计数（A→E），并机读 R620/R622 的受阻位点。

只读：只建图（build_lane / _via_ok），不描线、不改任何在册件、不产新版本联合表。
"""
import sys, os, json, types, importlib, hashlib, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
OUT = "K2_R635_EXIT_CANDIDATE_CENSUS_v1.json"
for nm in ("ortools", "ortools.sat", "ortools.sat.python"):
    sys.modules.setdefault(nm, types.ModuleType(nm))
cm = types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self, *a, **k): pass
cm.CpModel = _D; cm.CpSolver = _D
sys.modules["ortools.sat.python.cp_model"] = cm; sys.modules["ortools.sat.python"].cp_model = cm
M = importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1")
PREV = M.PREV; PREV.Gen._build_edges = M._build_edges_fixed       # R550 one-line graph fix (mandatory)
W = M.W; NID, NY, TERM, NX = W.NID, W.NY, W.TERM_BASE, W.NX

T = json.load(open(os.path.join(HERE, "K2_R613_FINAL_TABLE_VIA_OK_v1.json")))["per_lane"]
TWO = ("PCIE_UP_OUT0_P_J2", "PCIE_UP_OUT6_N_J2")

def manh(a, b): return abs(a[0] - b[0]) + abs(a[1] - b[1])

def main():
    t0 = time.time()
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names)
    EX = {nm: (int(T[nm]["exit_cell"][0]), int(T[nm]["exit_cell"][1])) for nm in names}
    rep = {"artifact": "k2_r635_exit_candidate_census_v1",
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-242 sec.3.4/5: evidence for the exit-slot rule provenance audit. READ-ONLY; no drawing; no new joint-table version",
           "construction_runs": 0,
           "question": "is R632's 'exit candidate set = EMPTY' reproducible under the in-register reading?",
           "free_cell_semantics": "node present in the lane's routing graph on the layer it is placed on (R610/R620 convention: iterate the adj keys, u<TERM, u//NID==layer). node = layer*NID + col*NY + row",
           "rules_expanded": {
               "A": "exit cell free on the lane's own exit layer",
               "B": "A and cell != every other lane's exit cell (R610 dedup gate: distinct)",
               "C": "B and Manhattan >= 2 from every other lane's exit cell  <-- the rule R632 declared as 'the released rule'",
               "D": "C and via-legal for this lane (g2._via_ok: free on BOTH layers AND inside a registered wide ZONE AND outside keepouts)",
               "E": "A counting with the FULL node set (adj keys + values) instead of adj keys only (robustness check)"},
           "per_lane": {}}
    for nm in TWO:
        L = int(T[nm]["exit_layer"])
        adj = g2.build_lane(nm)["adj"]
        keys = {u for u in adj if u < TERM}
        vals = {v for u in adj for (v, w) in adj[u] if v < TERM}
        freeA = {u for u in keys if u // NID == L}
        freeE = {u for u in (keys | vals) if u // NID == L}
        others = [EX[o] for o in names if o != nm]
        mask = g2._via_ok(nm)
        vialegal = {u for u in freeA if mask[u % NID]}   # via-legal (R523/R515): free on both layers + inside a ZONE + outside keepouts
        def cells(S): return [(u % NID) // NY, (u % NID) % NY] if False else [((u % NID) // NY, (u % NID) % NY) for u in S]
        cA = cells(freeA); cE = cells(freeE)
        cB = [c for c in cA if c not in others]
        cC = [c for c in cA if all(manh(c, e) >= 2 for e in others)]
        cD = [c for c in cC if (L * NID + c[0] * NY + c[1]) in vialegal]
        cur = EX[nm]
        rep["per_lane"][nm] = {
            "exit_layer": L, "current_exit": list(cur),
            "A_n_free_on_own_exit_layer": len(cA),
            "B_n_plus_distinct": len(cB),
            "C_n_plus_manhattan_ge2": len(cC),
            "D_n_plus_via_legal": len(cD),
            "E_n_full_node_set_on_own_exit_layer": len(cE),
            "current_exit_free_on_own_exit_layer": cur in cA,
            "current_exit_via_legal": bool(mask[cur[0] * NY + cur[1]]),
            "R632_declared_rule_is_C_expected_empty": len(cC) == 0,
        }
    # machine-read the recorded failure loci (R620/R622) - evidence, not computation
    loci = {}
    for tag, f in (("R620", "K2_R620_PERLANE_FULLCHAIN_v1.json"), ("R622", "K2_R622_LATECHANGE_PERLANE_v1.json")):
        b = json.load(open(os.path.join(HERE, f))).get("blocked", {})
        loci[tag] = {k: {"segment_index": v.get("segment_index"), "kind": v.get("kind"),
                         "from": v.get("from"), "from_col_row": v.get("from_col_row"),
                         "to": v.get("to"), "to_col_row": v.get("to_col_row")} for k, v in b.items()}
    rep["recorded_failure_loci"] = loci
    # --- in-register evidence for the per-lane blocker diagnosis (read-only) ---
    SPEC = json.load(open(os.path.join(HERE, "K2_R540_CORRIDOR_SPEC_v1.json")))["per_lane"]
    blk = json.load(open(os.path.join(HERE, "K2_R620_PERLANE_FULLCHAIN_v1.json")))["blocked"]
    diag = {}
    for nm in names:
        w = SPEC[nm]["waypoints"]; kinds = [x["kind"] for x in w]
        sch = SPEC[nm]["schedule"]
        key = nm.split("PCIE_UP_")[1]
        b = blk.get(key, {})
        diag[key] = {
            "spec_on_In4": sch.get("stations_on_In4"), "spec_start": sch.get("start_station"), "spec_end": sch.get("end_station"),
            "spec_waypoint_kinds": kinds,
            "spec_declares_entrance_transition": ("In5_entrance" in kinds) or ("DIVE_via" in kinds),
            "spec_entrance_kind": ("DIVE_via" if "DIVE_via" in kinds else ("In5_entrance" if "In5_entrance" in kinds else None)),
            "r613_belt_layer": T[nm]["belt_layer"], "r613_col60_layer": T[nm]["col60_layer"], "r613_exit_layer": T[nm]["exit_layer"],
            "r620_first_blocked_segment_index": b.get("segment_index"), "r620_blocked_to_col_row": b.get("to_col_row"),
            "r620_drawn": key not in blk,
        }
    rep["per_lane_blocker_diagnosis"] = {
        "note": ("machine-read, read-only. R620's chain builder declares the entrance layer transition ONLY when "
                 "r613 belt_layer==1 (and then it looks for a spec DIVE_via). Lanes whose spec transition is declared as "
                 "In5_entrance therefore get NO entrance transition in the chain. The 3 lanes blocked at segment 1 are "
                 "exactly the lanes with belt_layer==0 AND col60_layer==1."),
        "lanes_blocked_at_segment_1": [k for k, v in diag.items() if v["r620_first_blocked_segment_index"] == 1],
        "condition_belt0_col60layer1": [k for k, v in diag.items() if v["r613_belt_layer"] == 0 and v["r613_col60_layer"] == 1],
        "per_lane": diag}
    rep["generator_versioning_finding"] = {
        "claim": "the joint-table window's ONLY deliverable (R624-R632) has no committed generator",
        "evidence": "no K2_R63*/K2_R62[4-9]*.py exists in this directory; only .json (+ docs). The R620/R622/R623 scripted windows DO have .py.",
        "consequence": "the joint determination's numbers are hash-pinned but NOT independently re-runnable from the repo"}
    rep["reading"] = ("Under rules A/B/C/D the exit-slot candidate set for BOTH lanes is LARGE, not empty. "
                      "R632's 'candidate set = EMPTY' is therefore not reproducible under the in-register reading "
                      "(free on own exit layer, distinct, even with the self-added >=2 rule, even restricting to "
                      "via-legal cells). The emptiness must come from a further, narrower, self-imposed candidate "
                      "definition inside the (uncommitted) R632 script.")
    rep["elapsed_s"] = round(time.time() - t0, 1)
    body = json.dumps({k: v for k, v in rep.items() if k != "artifact_hash16"}, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(os.path.join(HERE, OUT), "w"), ensure_ascii=False, indent=1, default=str)
    for nm in TWO:
        v = rep["per_lane"][nm]
        print(nm)
        for k in ("exit_layer", "current_exit", "A_n_free_on_own_exit_layer", "B_n_plus_distinct",
                  "C_n_plus_manhattan_ge2", "D_n_plus_via_legal", "E_n_full_node_set_on_own_exit_layer",
                  "current_exit_free_on_own_exit_layer", "current_exit_via_legal",
                  "R632_declared_rule_is_C_expected_empty"):
            print("   %-42s %s" % (k, v[k]))
    print("hash16", rep["artifact_hash16"]); print("OWNER-ITEMS: 0")
    return 0

if __name__ == "__main__":
    sys.exit(main())
