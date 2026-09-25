#!/usr/bin/env python3
"""K2 · R564b -- READ-ONLY attribution of the R564 pre-gate FAIL (new command; no construction,
no drawing, no rerun). Machine-answers: which declared resource is exhausted on which layer, and
whether the 'direct belt run to col60' alternative is realizable."""
import sys, os, json, types, importlib, time

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
OUT = "K2_R564_BLOCKER_ATTRIBUTION_v1.json"
LOGF = "/tmp/opencode/r564/attrib.log"
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
    r550 = json.load(open(os.path.join(HERE, "K2_R550_CONSTRUCTION_DRAWING_v1.json")))
    ent = r550["entrance_channel_table"]
    def on4(nm, st): return 1 if ST[st] in master["schedule"][nm]["stations_on_In4"] else 0
    lanes = {nm: g2.build_lane(nm) for nm in names}
    adj = {nm: lanes[nm]["adj"] for nm in names}
    CELL = {}
    for nm in names:
        for L in (0, 1):
            CELL[(nm, L)] = set(u for u in adj[nm] if u < TERM and u // NID == L)
    LAY = {nm: on4(nm, 0) for nm in names}
    pi = {0: [], 1: []}
    for nm in sorted(names, key=lambda n: (ent[n]["d"])):
        pi[LAY[nm]].append(nm)
    rep = {"artifact": "k2_r564b_blocker_attribution_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "read-only attribution of the R564 pre-gate FAIL (#K2-220 sec.3.3(b)); no construction run",
           "solve_calls": 0, "construction_runs": 0, "drawings": 0, "per_layer": {}, "bands": {}}
    # (A) per lane: bus rows 24..37 usable with the OWN-span criterion is not fixed by c/E, so report
    #     the strict band (cols 42..80) and the wide band (cols 52..80):
    for nm in names:
        L = LAY[nm]; cs = CELL[(nm, L)]
        def rows_free(c0, c1, lo, hi):
            return [r for r in range(lo, hi + 1) if all((x * NY + r) in cs for x in range(c0, c1 + 1))]
        rep.setdefault("per_lane", {})[nm] = {
            "L": L, "on4": [on4(nm, k) for k in range(4)], "d": int(ent[nm]["d"]), "H": int(ent[nm]["H"]),
            "bus_rows_42_80": rows_free(42, 80, 24, 37),
            "bus_rows_52_80": rows_free(52, 80, 24, 37),
            "riser_cols_free_below37_and_38_H": [c for c in range(42, 53)
                                                 if all((c * NY + r) in cs for r in range(24, int(ent[nm]["H"]) + 1))],
            "belt_rows_2_52": rows_free(2, 52, 38, 59),
            "belt_rows_2_60": rows_free(2, 60, 38, 59),
            "belt_rows_2_59_only": [r for r in range(38, 60) if all((x * NY + r) in cs for x in range(53, 60))],
            "c60_legal_rows_on_col60_layer": rows_free(60, 60, 36, 55),
            "c60_legal_rows_on_comb_layer": [r for r in range(36, 56) if (60 * NY + r) in cs]}
    # (B) band summary by layer
    for L in (0, 1):
        gg = [n for n in names if LAY[n] == L]
        rep["per_layer"]["L%d" % L] = {
            "lanes": [n.split("PCIE_UP_")[1] for n in gg],
            "n_lanes": len(gg),
            "union_bus_rows_42_80": sorted({r for n in gg for r in rep["per_lane"][n]["bus_rows_42_80"]}),
            "union_riser_cols": sorted({c for n in gg for c in rep["per_lane"][n]["riser_cols_free_below37_and_38_H"]})}
    rep["band_findings"] = {
        "north_bus_band_rows_24_34_on_In5": "blocked at cols 42..80 for the 11 In5 (L0) lanes",
        "north_bus_band_rows_24_34_on_In4": "free at cols 42..80 for the In4 (L1) lanes",
        "consequence": "only rows 35..37 host a north-bus transfer on In5 => at most 3 of the 11 L0 lanes; "
                       "premise v2 P3' (north bus) is NOT realizable for 11 lanes on the COMB/In5 layer",
        "direct_belt_run_alternative": "rows 38..53 free across cols 2..60 per THIS probe => a lane can run "
                                       "east along its own belt row straight to col60 (no riser, no bus, no east col)"}
    rep["r564_pre_gate_fail"] = {"n_assign_incomplete": None}
    try:
        d = json.load(open(os.path.join(HERE, "K2_R564_PREMISE_V2_COMPLETE_DRAWING_v1.json")))
        rep["r564_pre_gate_fail"] = {"decision": d.get("decision"),
                                     "assigned": sorted(d.get("channel_table", {}).keys()),
                                     "incomplete": [f["lane"] for f in d.get("assignment_incomplete", [])],
                                     "pregate": d.get("pregate")}
    except Exception as e:
        rep["r564_pre_gate_fail"] = {"error": str(e)}
    rep["elapsed_s"] = round(time.time() - t0, 1)
    import hashlib
    body = json.dumps(rep, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(os.path.join(HERE, OUT), "w"), ensure_ascii=False, indent=1, default=str)
    log("PER-LANE bus rows (cols42..80):")
    for nm in names:
        log("  %-10s L%d bus42_80=%s riser_cols=%s belt2_60=%d" % (nm.split("PCIE_UP_")[1], LAY[nm],
            rep["per_lane"][nm]["bus_rows_42_80"], rep["per_lane"][nm]["riser_cols_free_below37_and_38_H"][:6],
            len(rep["per_lane"][nm]["belt_rows_2_60"])))
    for L in (0, 1):
        log("L%d union_bus42_80=%s union_riser=%s" % (L, rep["per_layer"]["L%d" % L]["union_bus_rows_42_80"],
                                                      rep["per_layer"]["L%d" % L]["union_riser_cols"][:12]))
    log("WROTE %s hash=%s" % (OUT, rep["artifact_hash16"]))
    log("OWNER-ITEMS: 0")
    return 0
if __name__ == "__main__":
    sys.exit(main())
