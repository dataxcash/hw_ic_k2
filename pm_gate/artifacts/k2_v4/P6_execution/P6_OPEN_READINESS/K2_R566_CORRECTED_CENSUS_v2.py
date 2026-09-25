#!/usr/bin/env python3
"""K2 · R566 -- READ-ONLY corrected census (unit-defect fix of R564b/R565).
DISCLOSED DEFECT: R564b/R565 tested POSITIONS (c*NY+r) against full node ids on layer 1,
so every layer-1 field there is void (layer-0 fields were valid because pos == 0*NID+pos).
This command recomputes with the correct unit (L*NID + c*NY + r) and adds the feasibility
check for the corrected scheme S2 = "belt-row direct run to col60 on In5".
New command; no construction, no drawing, no rerun."""
import sys, os, json, types, importlib, time, hashlib

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
OUT = "K2_R566_CORRECTED_CENSUS_v2.json"
LOGF = "/tmp/opencode/r566/census.log"
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
ST = ["COMB", "BELT", "WALL", "FIELD"]
def main():
    open(LOGF, "w").close(); t0 = time.time()
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names)
    master = json.load(open(os.path.join(HERE, "K2_R529_WOVEN_COMPLETE_MASTER_v1.json")))
    ent = json.load(open(os.path.join(HERE, "K2_R550_CONSTRUCTION_DRAWING_v1.json")))["entrance_channel_table"]
    def on4(nm, st): return 1 if ST[st] in master["schedule"][nm]["stations_on_In4"] else 0
    adj = {nm: g2.build_lane(nm)["adj"] for nm in names}
    CELL = {(nm, L): set(u for u in adj[nm] if u < TERM and u // NID == L) for nm in names for L in (0, 1)}
    def rows(nm, L, c0, c1, lo, hi):
        cs = CELL[(nm, L)]
        return [r for r in range(lo, hi + 1)
                if all((L * NID + x * NY + r) in cs for x in range(c0, c1 + 1))]
    rep = {"artifact": "k2_r566_corrected_census_v2", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "read-only corrected census (unit-defect fix of R564b/R565); no construction run",
           "disclosed_defect": {"in": "K2_R564_BLOCKER_ATTRIBUTION_v1, K2_R565_CORRECTED_SCHEME_CENSUS_v1",
                                "what": "layer-1 fields tested position ids against layer-1 node ids => void",
                                "fixed_by": "this artifact (correct unit L*NID + c*NY + r)",
                                "still_valid_in_R565": "in5_* fields (layer 0, where pos == node id)"},
           "solve_calls": 0, "construction_runs": 0, "drawings": 0, "per_lane": {}}
    for nm in names:
        Lc = on4(nm, 0); Lb = on4(nm, 1); d = int(ent[nm]["d"]); top = int(ent[nm]["top"])
        rep["per_lane"][nm] = {
            "L_comb": Lc, "on4": [on4(nm, k) for k in range(4)], "d": d, "top": top, "H_r550": int(ent[nm]["H"]),
            "desc_col_d_free_rows_on_comb_layer_35_59": [r for r in range(35, 60)
                                                         if (Lc * NID + d * NY + r) in CELL[(nm, Lc)]],
            "in5_belt_rows_2_60": rows(nm, 0, 2, 60, 38, 59),
            "in4_belt_rows_2_60": rows(nm, 1, 2, 60, 38, 59),
            "in5_gap_rows_53_59": rows(nm, 0, 53, 59, 24, 59),
            "in4_gap_rows_53_59": rows(nm, 1, 53, 59, 24, 59),
            "col60_free_rows_in5": rows(nm, 0, 60, 60, 36, 59),
            "col60_free_rows_in4": rows(nm, 1, 60, 60, 36, 59),
            "col60_free_rows_reg_layer": rows(nm, Lb, 60, 60, 36, 59),
            "north_band_blocked_cells_rows24_37_cols42_80": {"in5": sum(1 for r in range(24, 38) for x in range(42, 81)
                                                                       if (0 * NID + x * NY + r) not in CELL[(nm, 0)]),
                                                              "in4": sum(1 for r in range(24, 38) for x in range(42, 81)
                                                                         if (1 * NID + x * NY + r) not in CELL[(nm, 1)])}}
    u = sorted({r for nm in names for r in rep["per_lane"][nm]["in5_belt_rows_2_60"]})
    deficit = {nm: rep["per_lane"][nm]["in5_belt_rows_2_60"] for nm in names}
    # greedy 16-distinct-row assignment feasibility on In5 (row descending; per-lane span [d,60])
    order = sorted(names, key=lambda n: -int(ent[n]["d"]))
    used = set(); asg = {}; fails = []
    for nm in order:
        cand = [r for r in rep["per_lane"][nm]["in5_belt_rows_2_60"] if r not in used]
        if not cand:
            fails.append(nm); continue
        r = min(cand)          # smallest free row => keeps larger rows for the west-most (large-d) lanes
        used.add(r); asg[nm] = r
    rep["S2_feasibility"] = {"in5_union_belt_rows_2_60": u, "n_supply": len(u), "n_lanes": len(names),
                             "greedy_distinct_row_assignment": asg, "greedy_fails": fails,
                             "verdict": "PASS (16 distinct rows exist on In5 across [d,60])" if not fails else "FAIL"}
    rep["north_bus_refutation"] = {
        "method": "riser column c requires (c, r) free on the COMB layer for r in range(bus_row, H); bus_row in 24..37",
        "in5_free_cols_42_52_rows_24_to_H": {nm.split("PCIE_UP_")[1]: rows(nm, 0, 42, 52, 24, int(ent[nm]["H"]))
                                             for nm in names},
        "note": "computed correctly here; R564's own FAIL shows the same exhaustion for 11 In5 lanes"}
    rep["elapsed_s"] = round(time.time() - t0, 1)
    body = json.dumps(rep, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(os.path.join(HERE, OUT), "w"), ensure_ascii=False, indent=1, default=str)
    for nm in names:
        p = rep["per_lane"][nm]
        log("%-10s Lc=%d Lb=%d d=%2d desc_free=%d in5b2_60=%2d in4b2_60=%2d gap5=%d gap4=%d c60_5=%2d c60_4=%2d reg=%2d" % (
            nm.split("PCIE_UP_")[1], p["L_comb"], p["on4"][1], p["d"], len(p["desc_col_d_free_rows_on_comb_layer_35_59"]),
            len(p["in5_belt_rows_2_60"]), len(p["in4_belt_rows_2_60"]), len(p["in5_gap_rows_53_59"]),
            len(p["in4_gap_rows_53_59"]), len(p["col60_free_rows_in5"]), len(p["col60_free_rows_in4"]),
            len(p["col60_free_rows_reg_layer"])))
    log("In5 union belt rows (2..60): %s (n=%d)" % (u, len(u)))
    log("greedy 16-row assignment fails: %s" % rep["S2_feasibility"]["greedy_fails"])
    log("WROTE %s hash=%s" % (OUT, rep["artifact_hash16"])); log("OWNER-ITEMS: 0")
    return 0
if __name__ == "__main__":
    sys.exit(main())
