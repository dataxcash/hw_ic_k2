#!/usr/bin/env python3
"""K2 R260 · ②-UP —— **协商拥塞（PathFinder 型）单层（In5）束布线器**（独立方法 · 一次实现）。

用途：作为『②-UP 16/16』之**独立新方法**（非既有 `construct_router` 之次序枚举/硬避让）：
  · **同时性**：每轮对 **16 条网全部**各求一条最短路；拥塞以**费用**（present+history）表达；
  · **分离**：本轮内已布道按 `--sep-hard`（默认 0.44mm）硬禁（车道中心距硬下限），
    跨轮以历史拥塞收敛；
  · **定序**：内建**固定几何序**（按 B 锚 y 降序 = 「南锚先布」之洋葱层序），**非扫描**。
口径（未改）：物理 keepout 0.5300 · lane_w 0.16 · pitch 要求 0.435 · cell 默认 0.05 · 自网全转。
用法：k2_p4_b2_in5_pf_lane_router_v1.py <out.json> [iters] [cell] [sep_hard]
说明：本器**不保证**连续精确互距（cell 级硬禁 ≠ 段级分离）；末闸以 `v3.exact_gate` 复核并如实报数。
"""

import json, math, os, sys, time
import numpy as np
import importlib.util
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.ndimage import distance_transform_edt

HERE = "/home/fila/jqdDev_2025/ic_hw/k2"
spec = importlib.util.spec_from_file_location("v3m", HERE + "/tools/k2_p4_b2_in5_lane_router_v3.py")
v3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v3)
LANES = [f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N", "P")]
v3.is_lane = lambda n: n in set(LANES)
model = json.load(open("/tmp/opencode/archer/model_crop.json"))
A = json.load(open("/tmp/opencode/archer/sites_phys.json"))
B = json.load(open("/tmp/opencode/archer/sites_b_board_v1.json"))
OUT = sys.argv[1]
NIT = int(sys.argv[2]) if len(sys.argv) > 2 else 20
CELL = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05
SEP = float(sys.argv[4]) if len(sys.argv) > 4 else 0.44
HW = 0.08; MARGIN = 0.100; PITCH = 0.435; HALF = SEP      # 车道中心距硬下限（本轮内硬禁半径）

v3.PAD_EXTRA = MARGIN
rast = v3.Raster(model["bbox"], CELL)
anchors = v3.lane_anchors(model)
for an in anchors:
    an["A"] = tuple(A[an["net"]]); an["B"] = tuple(B[an["net"]])
base = v3.build_base(rast, model, "In5.Cu", frozenset(), frozenset(), HW, frozenset())
c_all, own = v3.anchor_keepout(rast, anchors, HW)
free = (~base)
NX, NY = free.shape
x0, y0 = model["bbox"][0], model["bbox"][1]
# disk struct for pitch/2 dilation
r = int(math.ceil(HALF / CELL))
yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
DISK = (np.hypot(xx * CELL, yy * CELL) <= HALF + 1e-9)
print("grid", free.shape, "cell", CELL, "disk r", r, "pitch", PITCH, flush=True)

G, idx = v3.build_topology(free, CELL)
coo = G.tocoo()
ES = coo.row.astype(np.int64); ET = coo.col.astype(np.int64); ED = coo.data.astype(np.float64)
NN = idx.max() + 1
print("nodes(free cells)", NN, "edges", len(ES), flush=True)


def cellidx(x, y):
    return int(round((x - x0) / CELL)), int(round((y - y0) / CELL))


def route_one(nm, cost):
    G.data = ED * (0.5 * (cost[ES] + cost[ET]))
    si, sj = cellidx(*[a for a in anchors if a["net"] == nm][0]["A"])
    gi, gj = cellidx(*[a for a in anchors if a["net"] == nm][0]["B"])
    s = idx[si, sj]; g = idx[gi, gj]
    dist, pred = dijkstra(G, directed=True, indices=int(s), return_predecessors=True)
    if not np.isfinite(dist[g]):
        return None
    pp = v3.path_from_pred(pred, int(s), int(g))
    return None if not pp else pp


def edt_dil(m, rad):
    from scipy.ndimage import distance_transform_edt
    if not m.any():
        return np.zeros_like(m, bool)
    return distance_transform_edt(~m, sampling=(CELL, CELL)) <= rad


def resolve(pp):
    return [(int(idx_flat // NY), int(idx_flat % NY)) for idx_flat in pp]  # placeholder (replaced below)


def flat_to_cells(flat):
    ii, jj = np.nonzero(free)
    return [(int(ii[k]), int(jj[k])) for k in flat]


nest_order = sorted(LANES, key=lambda n: (-B[n][1], -B[n][0]))
nets = list(nest_order)
hist = np.zeros(NN, np.float64)
last_failed = []
best = None
t0 = time.time()
for it in range(NIT):
    present = np.zeros(NN, np.float64)
    present_hard = np.zeros((NX, NY), bool)
    paths = {}
    if it > 0 and last_failed:
        nets = [n for n in nest_order if n in last_failed] + [n for n in nest_order if n not in last_failed]
    pfac = 1.0 + 0.3 * it          # 标准 PathFinder：present 罚随时间增大
    for nm in nets:
        c = 1.0 + pfac * present + 1.0 * hist
        ci = np.full((NX, NY), 1e9); ci[free] = 0.0
        bad = (c_all - own[nm].astype(np.int16)) > 0
        nodes_bad = idx[bad & free]
        if len(nodes_bad):
            c[nodes_bad] = 1e9      # 他道锚孔 keepout（硬）
        c2 = c.copy(); c2[idx[present_hard & free]] = np.inf   # 本轮内已布道之**真硬禁**（不可跨越）
        pp = route_one(nm, c2)
        if pp is None:
            continue
        paths[nm] = pp
        cells = flat_to_cells(pp)
        m = np.zeros((NX, NY), bool)
        for (i, j) in cells:
            m[i, j] = True
        md = edt_dil(m, HALF)
        present_hard |= md
        present[idx[md & free]] += 1.0
    # overuse: cells covered by >=2 nets' thickened paths
    cover = np.zeros((NX, NY), np.int32)
    for nm in nets:
        if nm not in paths:
            continue
        m = np.zeros((NX, NY), bool)
        for (i, j) in flat_to_cells(paths[nm]):
            m[i, j] = True
        cover[edt_dil(m, PITCH / 2.0)] += 1
    last_failed = [n for n in nets if n not in paths]
    over = np.maximum(0, cover - 1)
    n_over = int(over.sum())
    print("it %2d  routed=%2d  overuse_cells=%6d  t=%.0fs" % (it, len(paths), n_over, time.time() - t0), flush=True)
    iiF, jjF = np.nonzero(free)
    hist[idx[iiF, jjF]] += over[iiF, jjF].astype(np.float64)
    if best is None or (len(paths), -n_over) > (best[3], -best[0]):
        best = (n_over, it, {k: list(v) for k, v in paths.items()}, len(paths))
    if n_over == 0 and len(paths) == 16:
        break

# ---- 取 best 迭代，做**连续精确闸**复核并输出 ----
n_over, it_best, best_paths, n_rtd = best
routes = {}
pts_by_net = {}
for nm, pp in best_paths.items():
    an = [a for a in anchors if a["net"] == nm][0]
    cells = flat_to_cells(pp)
    pts = [tuple(an["A"])] + [(x0 + i * CELL, y0 + j * CELL) for (i, j) in cells] + [tuple(an["B"])]
    pts = v3.simplify(pts)
    routes[nm] = {"pts": [[round(a, 4), round(b, 4)] for (a, b) in pts],
                  "len_mm": round(sum(math.dist(pts[q], pts[q + 1]) for q in range(len(pts) - 1)), 3)}
gate = v3.exact_gate(model, routes, anchors, "In5.Cu", HW, frozenset(), frozenset(), PITCH, frozenset())
print("GATE:", json.dumps({k: gate[k] for k in ("lane_pitch_min_gap_mm", "n_lane_pitch_viol", "clearance_min_mm",
                                                "n_clearance_viol", "endpoint_max_dev_mm")}, ensure_ascii=False), flush=True)
wo = {"artifact": "k2_r260_pathfinder_bundle_router", "layer": "In5.Cu", "cell_mm": CELL, "lane_w_mm": 0.16,
      "pitch_mm": PITCH, "caliber": "physical (0.5300)", "iters": NIT, "best_iter": it_best,
      "n_routed": len(routes), "failed": sorted(n for n in nets if n not in routes),
      "n_lane_pitch_viol": gate.get("n_lane_pitch_viol"), "n_clearance_viol": gate.get("n_clearance_viol"),
      "geometric_gate": gate, "routes": routes,
      "anchors": [{"net": a["net"], "A": list(a["A"]), "B": list(a["B"]), "disp_mm": 0.0} for a in anchors]}
json.dump(wo, open(OUT, "w"), ensure_ascii=False, indent=1, sort_keys=True)
print("wrote", OUT, flush=True)
