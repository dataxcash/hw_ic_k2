#!/usr/bin/env python3
"""K2 · R327 · ②-UP **联合（PathFinder）布线器** 一次实现 —— 只读 · 端点不动 · 见证只由 exact_gate 判。
16 条 lane **同时**协商（软罚→硬罚 · 每 sweep 换序遍历）· 非序贯 · 非参数扫描。
障碍 = 他网铜 + 固定孔/盘 + 禁布线区 + 他 lane 锚孔(中心线排除 r=pitch)；自网旧铜按 no-move 全转可拆。
用法: python3 joint_pathfinder.py <model_l8.json> <out.json> [cell] [sweeps]
"""
import sys, json, math, importlib.util, hashlib
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

V3 = "k2/tools/k2_p4_b2_in5_lane_router_v3.py"
LANES = {f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N", "P")}
spec = importlib.util.spec_from_file_location("v3", V3)
v3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v3)
v3.is_lane = lambda n: n in LANES
MODEL, OUT = sys.argv[1], sys.argv[2]
CELL = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05
SW = int(sys.argv[4]) if len(sys.argv) > 4 else 8
HW, P = 0.08, 0.435
model = json.load(open(MODEL))
bbox = (82.0, 36.0, 144.0, 66.0)
rast = v3.Raster(bbox, CELL)
bad = v3.build_base(rast, model, "In5.Cu", frozenset(), frozenset(), HW, frozenset())
ad = {a["net"]: a for a in v3.lane_anchors(model)}
NX, NY = rast.NX, rast.NY
anchor_bad = np.zeros((NX, NY), bool); own = {}
for n in LANES:
    a = ad[n]; mm = np.zeros((NX, NY), bool)
    v3.Raster.cir(rast, mm, a["A"][0], a["A"][1], P); v3.Raster.cir(rast, mm, a["B"][0], a["B"][1], P)
    own[n] = mm; anchor_bad |= mm

LANE_ORD = sorted(LANES, key=lambda k: -ad[k]["A"][0])   # 东→西
G_, COO_, NODE_, ENDS_ = {}, {}, {}, {}
for n in LANE_ORD:
    allowed = (~bad) & (~(anchor_bad & ~own[n]))
    G, idx = v3.build_topology(allowed, CELL)
    ii, jj = np.nonzero(allowed)
    coo = G.tocoo()
    G_[n] = G.tocsr(); COO_[n] = (coo.row.astype(np.int64), coo.col.astype(np.int64),
                                 coo.data.astype(np.float64),
                                 (ii[coo.col] * NY + jj[coo.col]).astype(np.int64))
    NODE_[n] = (ii, jj); ENDS_[n] = (rast.cell(*ad[n]["A"]), rast.cell(*ad[n]["B"]))
    if idx[ENDS_[n][0]] < 0 or idx[ENDS_[n][1]] < 0:
        print("!! %s endpoint blocked" % n)
print("built %d lane-graphs | cell=%.3f window=%s | free=%.3f" % (len(G_), CELL, bbox, 1 - bad.mean()))

occ = np.zeros(NX * NY, np.float64)
paths = {}   # n -> node list
for n in LANE_ORD: paths[n] = None
RAD = int(P / CELL) + 1
offs = []
for dx in range(-RAD, RAD + 1):
    for dy in range(-RAD, RAD + 1):
        d = math.hypot(dx * CELL, dy * CELL)
        if d <= P: offs.append((dx, dy, 1.0 - d / P))

def stamp(n, sign, w=1.0):
    p = paths[n]
    if p is None: return
    ii, jj = NODE_[n]; I = ii[np.array(p)]; J = jj[np.array(p)]
    for (dx, dy, g) in offs:
        occ[np.clip(I + dx, 0, NX - 1) * NY + np.clip(J + dy, 0, NY - 1)] += sign * w * g

def route(n, coeff):
    r, c, dl, cellcol = COO_[n]
    w = dl * (1.0 + coeff * occ[cellcol])
    Gc = csr_matrix((w, (r, c)), shape=G_[n].shape)
    s = int(np.where((NODE_[n][0] == ENDS_[n][0][0]) & (NODE_[n][1] == ENDS_[n][0][1]))[0][0]) \
        if False else None
    # node id via allowed mask index map
    return Gc

# proper node-id lookup
IDX_ = {}
for n in LANE_ORD:
    allowed = (~bad) & (~(anchor_bad & ~own[n]))
    ii, jj = NODE_[n]
    m = np.full(NX * NY, -1, np.int64)
    m[ii * NY + jj] = np.arange(len(ii), dtype=np.int64)
    IDX_[n] = m

def route2(n, coeff):
    r, c, dl, cellcol = COO_[n]
    w = dl * (1.0 + coeff * occ[cellcol])
    Gc = csr_matrix((w, (r, c)), shape=G_[n].shape)
    s = int(IDX_[n][ENDS_[n][0][0] * NY + ENDS_[n][0][1]])
    g = int(IDX_[n][ENDS_[n][1][0] * NY + ENDS_[n][1][1]])
    d, pred = dijkstra(Gc, directed=True, indices=s, return_predecessors=True)
    if not np.isfinite(d[g]): return None
    return v3.path_from_pred(pred, s, g)

hist = np.zeros(NX * NY, np.float64)
CA, CB = 0.5, 1.0          # cost_mult = 1 + CA*occ + CB*hist   （canonical PathFinder 形）
def build_occ():
    occ[:] = 0.0
    for n in LANE_ORD:
        if paths[n] is None: continue
        ii, jj = NODE_[n]; I = ii[paths[n]]; J = jj[paths[n]]
        for (dx, dy, g) in offs:
            occ[np.clip(I + dx, 0, NX - 1) * NY + np.clip(J + dy, 0, NY - 1)] += g
    return occ

def route3(n):
    r, c, dl, cellcol = COO_[n]
    w = dl * (1.0 + CA * occ[cellcol] + CB * hist[cellcol])
    Gc = csr_matrix((w, (r, c)), shape=G_[n].shape)
    s_ = int(IDX_[n][ENDS_[n][0][0] * NY + ENDS_[n][0][1]])
    g_ = int(IDX_[n][ENDS_[n][1][0] * NY + ENDS_[n][1][1]])
    d, pred = dijkstra(Gc, directed=True, indices=s_, return_predecessors=True)
    if not np.isfinite(d[g_]): return None
    return v3.path_from_pred(pred, s_, g_)

# 初始布线
for n in LANE_ORD:
    paths[n] = route3(n)
best = None
for it in range(SW):
    build_occ()
    order = LANE_ORD if it % 2 == 0 else LANE_ORD[::-1]
    for n in order:
        pp = route3(n)
        if pp is not None: paths[n] = np.array(pp, np.int64)
    # hist 累积（被占用者）
    for n in LANE_ORD:
        if paths[n] is None: continue
        ii, jj = NODE_[n]; I = ii[paths[n]]; J = jj[paths[n]]
        for (dx, dy, g) in offs:
            hist[np.clip(I + dx, 0, NX - 1) * NY + np.clip(J + dy, 0, NY - 1)] += g
    # 用 exact_gate 判（权威）
    rr = {}
    for n in LANE_ORD:
        if paths[n] is None: continue
        ii, jj = NODE_[n]; a = ad[n]
        pts = [(a["A"][0], a["A"][1])] + [(rast.X0 + int(ii[k]) * CELL, rast.Y0 + int(jj[k]) * CELL) for k in paths[n]] + [(a["B"][0], a["B"][1])]
        rr[n] = {"pts": [[round(x, 4), round(y, 4)] for x, y in v3.simplify(pts)]}
    an = [a for a in v3.lane_anchors(model) if a["net"] in rr]
    gg = v3.exact_gate(model, rr, an, "In5.Cu", HW, frozenset(), frozenset(), P, frozenset())
    nv = gg["n_lane_pitch_viol"] + gg["n_clearance_viol"]
    print("sweep %2d placed=%d pitch_viol=%d clr_viol=%d min_gap=%.4f" % (
        it, len(rr), gg["n_lane_pitch_viol"], gg["n_clearance_viol"], gg["lane_pitch_min_gap_mm"]))
    if best is None or nv < best[0]:
        best = (nv, {k: list(v) for k, v in rr.items()}, gg)
    if nv == 0 and len(rr) == 16: break

# --- 取最佳解 ---
routes = {n: {"pts": v} for n, v in best[1].items()}
anchors = [a for a in v3.lane_anchors(model) if a["net"] in routes]
g = v3.exact_gate(model, routes, anchors, "In5.Cu", HW, frozenset(), frozenset(), P, frozenset())
print("RESULT placed=%d/16 | exact_gate: 互距违例=%d(min %.4f) 净距违例=%d(min %.4f) 端点=%.4f" % (
    len(routes), g["n_lane_pitch_viol"], g["lane_pitch_min_gap_mm"], g["n_clearance_viol"],
    g["clearance_min_mm"] if g["clearance_min_mm"] is not None else -1, g["endpoint_max_dev_mm"]))
LEN = {n: round(sum(math.dist(r["pts"][k], r["pts"][k + 1]) for k in range(len(r["pts"]) - 1)), 3) for n, r in routes.items()}
out = {"schema": 1, "artifact": "k2_r327_joint_pathfinder_one_shot", "to": "监理", "from": "ENG · ARCHER",
       "method": "PathFinder 联合协商（软→硬 · 换序遍历）· 端点不动 · cell=%.3f" % CELL,
       "board_sha16": "7a5c89913d6e5d0a", "pitch_mm": P, "hw_mm": HW,
       "placed": len(routes), "missing": sorted(n[10:-3] for n in LANES - set(routes)),
       "exact_gate": {k: g[k] for k in ("lane_pitch_req_mm", "lane_pitch_min_gap_mm", "lane_pitch_min_pair",
                                        "n_lane_pitch_viol", "clearance_min_mm", "n_clearance_viol", "endpoint_max_dev_mm")},
       "lengths_mm": {n[10:-3]: LEN[n] for n in sorted(LEN)},
       "routes_pts": {n[10:-3]: routes[n]["pts"] for n in sorted(routes)},
       "self_sha16": {"convention": "#K2-72 §五 约定A", "convention_A_sha16": ""}}
if LEN:
    ls = sorted(LEN.values()); out["length_spread_mm"] = round(ls[-1] - ls[0], 3)
txt = json.dumps(out, indent=1, ensure_ascii=False)
out["self_sha16"]["convention_A_sha16"] = hashlib.sha256(txt.strip().encode()).hexdigest()[:16]
json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("[sha16 约定A]", out["self_sha16"]["convention_A_sha16"], "->", OUT)
