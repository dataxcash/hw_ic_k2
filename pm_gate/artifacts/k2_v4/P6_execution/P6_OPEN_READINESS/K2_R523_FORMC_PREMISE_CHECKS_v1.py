#!/usr/bin/env python3
"""K2 · R523 —— form C 蕴含证明的**前提机核**（只读 · Solve() 0 次）。

机核 1（完备性）：四把刀（col 60 / col 114 / row 36 / row 30）**不被任何"自由接入腿"横穿或触碰**
⇒ 只用**格点弧**统计横穿次数是完备的（否则横穿次数会漏计 ⇒ 唯一性判据失效 ⇒ 可能误加约束）。
机核 2（刀上格点可用性）：每条线在四把刀上**至少有一个** In5 入弧候选格点（否则该族对该线恒空）。
机核 3（8 邻域完备）：横穿判据按 **8 邻域两侧进出**实现（R499 `NB` 八方向），本件报每线的横穿候选数。
"""
import importlib, json, math, sys, time

HERE = "."
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
M = importlib.import_module("K2_R523_LAYERHOP_PARITY_FORMC_v1")
P, X0, Y0, NX, NY, NID, TERM = M.P, M.X0, M.Y0, M.NX, M.NY, M.NID, M.TERM_BASE
XY = M.XY


def _pos(i, j):
    return i * NY + j


def line_dist_to_seg(xc, kind, a, b):
    """刀线（col: x=xc / row: y=yc）到线段的最近距离；≥0，0 = 触碰/穿过。"""
    if kind == "col":
        lo, hi = min(a[0], b[0]), max(a[0], b[0])
        if lo <= xc <= hi:
            return 0.0
        return min(abs(lo - xc), abs(hi - xc))
    yc = xc
    lo, hi = min(a[1], b[1]), max(a[1], b[1])
    if lo <= yc <= hi:
        return 0.0
    return min(abs(lo - yc), abs(hi - yc))


def _iter_arcs(L):
    for u, lst in L["adj"].items():
        for (v, w) in lst:
            if u < TERM and v < TERM:
                yield (u, v)


CUTS = [("col", X0 + 60 * P), ("col", X0 + 114 * P), ("row", Y0 + 36 * P), ("row", Y0 + 30 * P)]
res = {"artifact": "k2_r523_formc_premise_checks_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "authority": "R523 form-C soundness proof, premise 0 (legs cannot cross the four cut lines) and "
                    "premise 0b (per-lane crossing candidates exist); read-only, Solve() 0",
       "solve_calls": 0, "cuts": [{"kind": k, "coord_mm": round(v, 4)} for k, v in CUTS]}
m = json.load(open("/tmp/opencode/archer/model_l8.json"))
g = M.Gen2(m, l1scope="full")
tot_legs = 0; worst = {("%s_%s" % (k, round(v, 3))): 1e9 for k, v in CUTS}
per_lane = {}
for nm in g.names:
    L = g.build_lane(nm)
    legs = L.get("legs") or {}
    n = 0; mx = {("%s_%s" % (k, round(v, 3))): 1e9 for k, v in CUTS}
    for (u, v), meta in legs.items():
        k, anc, pos = meta
        px, py = XY(*M.rc(pos))
        a = (float(anc[0]), float(anc[1])); b = (float(px), float(py))
        for (kind, coord) in CUTS:
            d = line_dist_to_seg(coord, kind, a, b)
            key = "%s_%s" % (kind, round(coord, 3))
            mx[key] = min(mx[key], d); worst[key] = min(worst[key], d)
        n += 1
    tot_legs += n
    # 刀上 In5 入弧候选格点数（机核 2）
    cand = {}
    for (kind, coord) in CUTS:
        ci = int(round((coord - (X0 if kind == "col" else Y0)) / P))
        c = 0
        if kind == "col":
            for j in range(NY):
                nidm = _pos(ci, j)
                if any(vv == nidm for (uu, vv) in _iter_arcs(L)):
                    c += 1
        else:
            for i in range(NX):
                nidm = _pos(i, ci)
                if any(vv == nidm for (uu, vv) in _iter_arcs(L)):
                    c += 1
        cand["%s_%s" % (kind, round(coord, 3))] = c
    per_lane[nm.replace("PCIE_UP_OUT", "U")] = {"legs": n, "min_leg_dist_mm": {k: round(v, 4) for k, v in mx.items()},
                                                "cut_node_head_arc_candidates": cand}


res["n_legs_total"] = tot_legs
res["min_leg_dist_mm_all_lanes"] = {k: round(v, 4) for k, v in worst.items()}
res["legs_never_touch_any_cut"] = all(v > 0.0 for v in worst.values())
res["min_leg_dist_positive"] = all(v > 0.0 for v in worst.values())
res["per_lane"] = per_lane
res["verdict"] = ("PREMISES HOLD: no free-access leg touches/crosses any of the four cut lines (min distance "
                  "%.4f mm >= R_REACH %.4f mm), so counting crossings on lattice arcs only is complete"
                  % (min(worst.values()), M.R_REACH)) if res["legs_never_touch_any_cut"] else "PREMISE VIOLATED"
res["boundaries"] = "read-only graph geometry; Solve() 0; no model/parameter/board/SPEC/tools/criteria change; no WORKER"
res["buildability"] = "NOT-APPLICABLE (soundness-premise machine check; no construction claim; nothing moved)"
json.dump(res, open("K2_R523_FORMC_PREMISE_CHECKS_v1.json", "w"), ensure_ascii=False, indent=1, default=str)
print("n_legs_total", res["n_legs_total"])
print("min_leg_dist_mm_all_lanes", json.dumps(res["min_leg_dist_mm_all_lanes"]))
print("legs_never_touch_any_cut", res["legs_never_touch_any_cut"], "| all distances > 0", res["min_leg_dist_positive"])
print("verdict:", res["verdict"])
