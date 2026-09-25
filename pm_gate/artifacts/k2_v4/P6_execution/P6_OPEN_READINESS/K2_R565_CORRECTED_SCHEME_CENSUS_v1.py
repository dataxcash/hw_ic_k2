#!/usr/bin/env python3
"""K2 · R565 -- READ-ONLY feasibility census of the corrected transfer scheme
("belt-row direct run to col60 on In5"), the fix implied by R564b's refutation of premise v2 P3'.
New command; no construction, no drawing, no rerun."""
import sys, os, json, types, importlib, time, hashlib

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
OUT = "K2_R565_CORRECTED_SCHEME_CENSUS_v1.json"
LOGF = "/tmp/opencode/r565/census.log"
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
    C = {}
    for nm in names:
        for L in (0, 1):
            C[(nm, L)] = set(u for u in adj[nm] if u < TERM and u // NID == L)
    rep = {"artifact": "k2_r565_corrected_scheme_census_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "read-only census of the corrected transfer scheme implied by R564b; no construction run",
           "solve_calls": 0, "construction_runs": 0, "drawings": 0, "scheme": {
               "S1": "entrance pocket descent on the lane's COMB layer (registered)",
               "S2": "belt-row direct run (d -> 60) on In5 (the only layer where cols 53..59 are free in the belt band)",
               "S3": "col60 slot row = the lane's belt row (distinct, decreasing in pi); layer change only at the registered col60 node",
               "S4": "col60 -> exit -> pad : registered (as before)"},
           "per_lane": {}}
    for nm in names:
        Lc = on4(nm, 0); Lb = on4(nm, 1); d = int(ent[nm]["d"])
        c0 = C[(nm, 0)]; c1 = C[(nm, 1)]
        def rows(cs, c0_, c1_, lo, hi):
            return [r for r in range(lo, hi + 1) if all((x * NY + r) in cs for x in range(c0_, c1_ + 1))]
        rep["per_lane"][nm] = {
            "L_comb": Lc, "on4": [on4(nm, k) for k in range(4)], "d": d, "H_r550": int(ent[nm]["H"]),
            "in5_belt_rows_2_60": rows(c0, 2, 60, 38, 59),
            "in4_belt_rows_2_52": rows(c1, 2, 52, 38, 59),
            "in5_gap_rows_53_59": rows(c0, 53, 59, 24, 59),
            "col60_free_rows_in5": rows(c0, 60, 60, 36, 59),
            "col60_free_rows_in4": rows(c1, 60, 60, 36, 59),
            "col60_free_rows_registered_layer": rows(C[(nm, Lb)], 60, 60, 36, 59),
            "blocked_cells_rows24_37_cols42_80_in5": sum(1 for r in range(24, 38) for x in range(42, 81) if (x * NY + r) not in c0),
            "blocked_cells_rows24_37_cols42_80_in4": sum(1 for r in range(24, 38) for x in range(42, 81) if (x * NY + r) not in c1)}
    # union availability on In5 (the layer the corrected scheme routes the belt run on)
    u = sorted({r for nm in names for r in rep["per_lane"][nm]["in5_belt_rows_2_60"]})
    rep["in5_union"] = {"belt_rows_2_60": u, "n": len(u)}
    need = len(names)
    rep["verdict_hint"] = {"S2_realizable_per_lane": {nm: (len(rep["per_lane"][nm]["in5_belt_rows_2_60"]) > 0) for nm in names},
                           "in5_distinct_rows_supply": len(u), "lanes": need,
                           "cap_ok": len(u) >= need}
    rep["elapsed_s"] = round(time.time() - t0, 1)
    body = json.dumps(rep, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(os.path.join(HERE, OUT), "w"), ensure_ascii=False, indent=1, default=str)
    for nm in names:
        p = rep["per_lane"][nm]
        log("%-10s Lc=%d Lb=%d d=%2d in5belt2_60=%2d in4belt2_52=%2d gap53_59(In5)=%s c60in5=%d c60reg=%d"
            % (nm.split("PCIE_UP_")[1], p["L_comb"], p["on4"][1], p["d"], len(p["in5_belt_rows_2_60"]),
               len(p["in4_belt_rows_2_52"]), p["in5_gap_rows_53_59"][:4], len(p["col60_free_rows_in5"]),
               len(p["col60_free_rows_registered_layer"])))
    log("In5 union belt rows (2..60): %s" % u)
    log("WROTE %s hash=%s" % (OUT, rep["artifact_hash16"])); log("OWNER-ITEMS: 0")
    return 0
if __name__ == "__main__":
    sys.exit(main())
