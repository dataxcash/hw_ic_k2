#!/usr/bin/env python3
"""K2 · R563 —— 前提 v2 所需**自由资源盘点**（新命令 · 只读盘点 · 不描线 · 一次）
对 8/8 层划分后的每一层，盘点构造式指派所需的四类资源是否够用：
 A) 下钻列 d：cells (c, 35..59) 全合法的列；B) 断面列 c：cells (c, 38..48) 全合法的列；
 C) 北巴士行 b：row r(24..37) 上 cells (42..75, r) 全合法的行；D) 东列 E：cells (E, 38..59) 全合法的列（>=60）。
输出每层每类资源的可用集合与"每线可取数"，判断 8 线/层是否够。"""
import sys, os, json, time, types, importlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
for nm in ("ortools", "ortools.sat", "ortools.sat.python"): sys.modules.setdefault(nm, types.ModuleType(nm))
cm = types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self, *a, **k): pass
cm.CpModel = _D; cm.CpSolver = _D
sys.modules["ortools.sat.python.cp_model"] = cm; sys.modules["ortools.sat.python"].cp_model = cm
LOGF = "/tmp/opencode/r563/census.log"; os.makedirs(os.path.dirname(LOGF), exist_ok=True)
def log(m): open(LOGF, "a").write(str(m) + "\n"); print(str(m), flush=True)
def main():
    open(LOGF, "w").close()
    M = importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1")
    PREV = M.PREV; PREV.Gen._build_edges = M._build_edges_fixed
    W = M.W; NID, NY, TERM = W.NID, W.NY, W.TERM_BASE
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names)
    r550 = json.load(open(os.path.join(HERE, "K2_R550_CONSTRUCTION_DRAWING_v1.json")))
    ent = r550["entrance_channel_table"]
    dord = sorted(names, key=lambda n: ent[n]["d"])
    LAY = {nm: (0 if i < 8 else 1) for i, nm in enumerate(dord)}
    adj = {nm: g2.build_lane(nm)["adj"] for nm in names}
    def cells(nm, L): return set(u % NID for u in adj[nm] if u < TERM and u // NID == L)
    CS = {nm: cells(nm, LAY[nm]) for nm in names}
    res = {}
    for L in (0, 1):
        gg = [n for n in names if LAY[n] == L]
        res["L%d" % L] = {"n_lanes": len(gg), "lanes": [n.split("PCIE_UP_")[1] for n in gg], "resources": {}}
        for nm in gg:
            c = CS[nm]
            desc = [x for x in range(1, 40) if all((x*NY+r) in c for r in range(35, 60))]
            sect = [x for x in range(38, 60) if all((x*NY+r) in c for r in range(38, 49))]
            bus = [r for r in range(24, 38) if all((x*NY+r) in c for x in range(42, 76))]
            east = [x for x in range(60, 90) if all((x*NY+r) in c for r in range(38, 60))]
            res["L%d" % L]["resources"][nm.split("PCIE_UP_")[1]] = {"descent_cols": desc, "section_cols": sect, "bus_rows": bus, "east_cols": east}
        u = {k: sorted({v for nm in gg for v in res["L%d" % L]["resources"][nm.split("PCIE_UP_")[1]][k]}) for k in ("descent_cols", "section_cols", "bus_rows", "east_cols")}
        res["L%d" % L]["union"] = u
        res["L%d" % L]["capacity_ok"] = {k: (len(u[k]) >= len(gg)) for k in u}
    rep = {"artifact": "k2_r563_free_resource_census_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "premise v2 (8/8 layers) free-resource inventory for the constructive assignment; read-only census, NO drawing",
           "layer_assignment_8_8": {("L%d" % L): [n.split("PCIE_UP_")[1] for n in names if LAY[n] == L] for L in (0, 1)},
           "census": res}
    body = json.dumps(rep, ensure_ascii=False, indent=1, default=str)
    import hashlib; rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(os.path.join(HERE, "K2_R563_FREE_RESOURCE_CENSUS_v1.json"), "w"), ensure_ascii=False, indent=1, default=str)
    for L in (0, 1):
        r = res["L%d" % L]
        log("L%d lanes=%d capacity_ok=%s" % (L, r["n_lanes"], r["capacity_ok"]))
        for k in ("descent_cols", "section_cols", "bus_rows", "east_cols"):
            log("   union %-13s n=%2d %s" % (k, len(r["union"][k]), r["union"][k][:24]))
    log("OWNER-ITEMS: 0")
    return 0
if __name__ == "__main__":
    sys.exit(main())
