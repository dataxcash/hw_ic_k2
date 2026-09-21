#!/usr/bin/env python3
"""K2 · (a) B.Cu 收紧版 —— **拥塞感知 + rip-up 布线器 v1**（只读生成工作令；系统 python3 + numpy）。

职责（#K2-68 §2.4(a)-4 · #K2-69 §六）：为 32 条 `PCIE_(UP|DN)_OUT` 车道在 **B.Cu** 上求
`V1(F–B) → V4(F–B 同位换 span)` 之新长走，输出**确定性工作令 JSON**（供 pcbnew 侧套用）。
本器**不改板**：只读 dump + 出线。

要点：
- 自由空间 = **B.Cu 探针语义**（其他网铜按 net 取 req；车道自身铜/孔视为可拆）+ 已布车道占位；
- 车道间距门 = `w_B + 2*req = 0.205 + 0.35 = 0.555mm`（中心距）；
- **禁用顺序贪心**（#K2-68 §10.8：难者先行 + 无 rip-up ⇒ 必败）⇒ 本器 = 难度排序 + 迭代 **rip-up 重布**；
- 时延/等长不在本器（§7-3 另批）。

CLI:
  python3 k2/tools/k2_p4_b2_bcu_router_v1.py --model <dump.json> --out <workorder.json> \
      [--cell 0.10] [--iters 6] [--max-expand 900000]
"""
from __future__ import annotations
import argparse, heapq, json, math, sys

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from k2_p4_b2_in5_capacity_probe_v1 import Field, lanes_of, req, is_lane, VIA_R  # noqa: E402

HW_B = 0.205 / 2.0
PITCH_B = 0.205 + 0.175              # 0.380mm 中心距门（= w + 边到边 req；对照 In5: 0.16+0.175=0.335 ✓）
LANE_W = 0.205


def occ_radius_cells(cell):
    """占位半径（格）：使被屏蔽邻域 ≥ PITCH_B 中心距之**最小**整数半径（R=0 即仅屏蔽本格，
    此时相邻格中心距 = cell ≥ PITCH_B 即合法）。"""
    return max(0, int(math.ceil(PITCH_B / cell)) - 1)


def snap_free(field, bad, pt):
    ci, cj = field.cell(pt[0], pt[1])
    best = None
    for r in range(0, 40):
        for di in range(-r, r + 1):
            for dj in range(-r, r + 1):
                if max(abs(di), abs(dj)) != r:
                    continue
                i, j = ci + di, cj + dj
                if 0 <= i < field.NX and 0 <= j < field.NY and not bad[i, j]:
                    d = di * di + dj * dj
                    if best is None or d < best[0]:
                        best = (d, i, j)
        if best is not None:
            return best[1], best[2]
    return None, None


def astar(field, bad, occ, start, goal, cell, w_cong=6.0, w_margin=3.0, max_expand=900000, pres_fac=1.0, hard=False, conn=8):
    """8 邻接 A*（代价 = 长度 + 拥塞惩罚 + 贴边惩罚）。返回 [(i,j),…] 或 None。"""
    NX, NY = field.NX, field.NY
    margin = getattr(field, "_margin_cache", None)
    if margin is None:
        # 距最近障碍之“名义余量”（单位：格）：用 distance_transform 近似
        from scipy import ndimage
        margin = ndimage.distance_transform_edt(~bad)
        field._margin_cache = margin
    (si, sj), (gi, gj) = start, goal
    if bad[si, sj] or bad[gi, gj]:
        return None
    h = lambda i, j: math.hypot(i - gi, j - gj)
    g = {(si, sj): 0.0}
    prev = {}
    pq = [(h(si, sj), 0.0, si, sj)]
    seen = 0
    NB = ((1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0))
    if conn == 8:      # 4 邻接（曼哈顿）= 无对角步 ⇒ 连续几何间距 = 栅格间距（可保证 ≥ PITCH_B）
        NB = NB + ((1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142))
    while pq:
        f, gc, i, j = heapq.heappop(pq)
        if (i, j) == (gi, gj):
            path = [(i, j)]
            while (i, j) in prev:
                i, j = prev[(i, j)]
                path.append((i, j))
            path.reverse()
            return path
        if gc > g.get((i, j), 1e18) + 1e-9:
            continue
        seen += 1
        if seen > max_expand:
            return None
        for di, dj, step in NB:
            ni, nj = i + di, j + dj
            if not (0 <= ni < NX and 0 <= nj < NY) or bad[ni, nj]:
                continue
            if hard and occ[ni, nj] > 0:          # 硬带：已布车道占位区禁行（真两两分离）
                continue
            m = margin[ni, nj]
            n_clear = m * cell                       # 该格到障碍之名义距离
            pen = pres_fac * w_cong * max(0.0, float(occ[ni, nj]) - 1.0)   # 过用（>1 网共享）才罚 ⇒ PathFinder 协商
            if n_clear < HW_B + req("PCIE"):         # 贴限（< 要求）⇒ 禁行
                continue
            pen += w_margin * max(0.0, 2.0 - n_clear)  # 贴边惩罚
            ng = gc + step * cell + pen * cell
            if ng < g.get((ni, nj), 1e18) - 1e-9:
                g[(ni, nj)] = ng
                prev[(ni, nj)] = (i, j)
                heapq.heappush(pq, (ng + h(ni, nj) * cell, ng, ni, nj))
    return None


def simplify(path):
    """栅格路径 → 45°/90° 折线（合并共线/同向）。返回 [(x,y),…] mm。"""
    if not path:
        return []
    pts = [path[0]]
    for k in range(1, len(path)):
        pts.append(path[k])
    # 合并共线
    out = [pts[0]]
    for k in range(1, len(pts) - 1):
        (a, b, c) = (out[-1], pts[k], pts[k + 1])
        d1 = (b[0] - a[0], b[1] - a[1]); d2 = (c[0] - b[0], c[1] - b[1])
        if d1[0] * d2[1] - d1[1] * d2[0] != 0 or d1[0] * d2[0] + d1[1] * d2[1] <= 0:
            out.append(b)
    out.append(pts[-1])
    return out


def _pt_seg(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _ccw(p, q, r):
    return (r[1] - p[1]) * (q[0] - p[0]) - (q[1] - p[1]) * (r[0] - p[0])


def _seg_seg(A, B, C, D):
    if ((_ccw(C, D, A) > 0) != (_ccw(C, D, B) > 0)) and ((_ccw(A, B, C) > 0) != (_ccw(A, B, D) > 0)):
        return 0.0
    return min(_pt_seg(*A, *C, *D), _pt_seg(*B, *C, *D), _pt_seg(*C, *A, *B), _pt_seg(*D, *A, *B))


def _pt_rect(px, py, lo, hi):
    dx = max(lo[0] - px, 0.0, px - hi[0]); dy = max(lo[1] - py, 0.0, py - hi[1])
    return math.hypot(dx, dy)


def _seg_rect(A, B, lo, hi):
    if lo[0] <= A[0] <= hi[0] and lo[1] <= A[1] <= hi[1]:
        return 0.0
    if lo[0] <= B[0] <= hi[0] and lo[1] <= B[1] <= hi[1]:
        return 0.0
    e = ((lo[0], lo[1]), (hi[0], lo[1])), ((hi[0], lo[1]), (hi[0], hi[1])), ((hi[0], hi[1]), (lo[0], hi[1])), ((lo[0], hi[1]), (lo[0], lo[1]))
    for (C, D) in e:
        if _seg_seg(A, B, C, D) == 0.0:
            return 0.0
    return min(_seg_seg(A, B, C, D) for (C, D) in e)


def verify_routes(field, routes, movable=()):
    """**几何精确闸**（连续几何 · 非栅格）：① 车道互检（中心距 ≥ w+req）② 逐段 vs 他网铜（边到边 ≥ req）。

    返回 {lane_min_gap, pair_min, clearance_min{net:…}, n_viol_lane, n_viol_obs, worst}"""
    segs = {}                                    # net -> [((x1,y1),(x2,y2)),…]（含半宽）
    for n, r in routes.items():
        pts = [tuple(p) for p in r["pts"]]
        segs[n] = [((pts[k][0], pts[k][1]), (pts[k + 1][0], pts[k + 1][1])) for k in range(len(pts) - 1)]
    pair_min = (1e9, None); lane_min = {}
    names = sorted(segs)
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            best = 1e9
            for (A1, A2) in segs[names[a]]:
                for (B1, B2) in segs[names[b]]:
                    d = _seg_seg(A1, A2, B1, B2) - LANE_W
                    if d < best:
                        best = d
                        if d <= 0.0:
                            break
                if best <= 0.0:
                    break
            if best < pair_min[0]:
                pair_min = (best, (names[a], names[b]))
    for n in names:
        m = 1e9
        for (A1, A2) in segs[n]:
            for (B1, B2) in segs[n]:
                if B1 is A1 or B2 is A2:
                    continue
            for o in names:
                if o == n:
                    continue
                for (B1, B2) in segs[o]:
                    d = _seg_seg(A1, A2, B1, B2) - LANE_W
                    if d < m:
                        m = d
        lane_min[n] = round(m, 4)
    obs = []                                     # 障碍清单（非车道网 · 非可腾挪）
    for (ax, ay, bx, by, shw, nm) in field.segs:
        if is_lane(nm) or nm in movable:
            continue
        obs.append(("seg", ((ax, ay), (bx, by)), shw, nm))
    for v in field.vias:
        if is_lane(v["net"]) or v["net"] in movable:
            continue
        obs.append(("via", ((v["x"], v["y"]), (v["x"], v["y"])), v["r"], v["net"]))
    for p in field.pads:
        if is_lane(p["net"]) or p["net"] in movable:
            continue
        obs.append(("pad", p["box"], 0.0, p["net"]))
    clr = {}; viol = []
    for n in names:
        worst = (1e9, None)
        for (A1, A2) in segs[n]:
            for (kind, geo, rr, nm) in obs:
                if kind == "seg":
                    d = _seg_seg(A1, A2, geo[0], geo[1]) - rr
                elif kind == "via":
                    d = _pt_seg(geo[0][0], geo[0][1], A1[0], A1[1], A2[0], A2[1]) - rr
                else:
                    d = _seg_rect(A1, A2, geo[:2], geo[2:])
                need = req(nm)
                m = d - need
                if m < worst[0]:
                    worst = (m, nm)
                if m < -1e-9:
                    viol.append((n, nm, round(m, 4)))
        clr[n] = {"margin_min": round(worst[0], 4), "blocker": worst[1]}
    return {"lane_pitch_min_gap_mm": round(pair_min[0], 4), "lane_pitch_min_pair": pair_min[1],
            "lane_pitch_violations": sorted(n for n, v in lane_min.items() if v < PITCH_B - LANE_W - 1e-9),
            "lane_min_gap_per_net": lane_min,
            "clearance_min_mm": min((v["margin_min"] for v in clr.values()), default=None),
            "clearance_violations": sorted(set(viol)), "per_lane_clearance": clr}


def maxflow_routes(field, bad, lanes, cell, rloc=1.0, conn=4):
    """**router v4 核心**：4 邻接 · 节点容量 1 之最大流 ⇒ 路径即**节点不相交** ⇒ 曼哈顿栅格下
    两两中心距 ≥ 栅格距（cell ≥ PITCH_B 即**连续几何合法**）。返回 {net: [(i,j),…]}。"""
    from scipy import sparse
    from scipy.sparse.csgraph import maximum_flow
    GNX = int((field.NX - 1) * field.step / cell) + 1
    GNY = int((field.NY - 1) * field.step / cell) + 1
    ii = np.clip(np.round(np.arange(GNX) * cell / field.step).astype(int), 0, field.NX - 1)
    jj = np.clip(np.round(np.arange(GNY) * cell / field.step).astype(int), 0, field.NY - 1)
    free = ~bad[np.ix_(ii, jj)]
    idx = np.full(free.shape, -1, dtype=np.int64)
    a, b = np.nonzero(free); idx[a, b] = np.arange(len(a)); N = len(a)
    k = np.arange(N)
    rows = [2 * k]; cols = [2 * k + 1]; data = [np.ones(N, dtype=np.int32)]
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)] + ([] if conn == 4 else [(1, 1), (1, -1), (-1, 1), (-1, -1)])
    for di, dj in dirs:
        u = a + di; v = b + dj
        m = (u >= 0) & (u < GNX) & (v >= 0) & (v < GNY)
        ku = idx[u[m], v[m]]; ok = ku >= 0
        rows.append(2 * k[m][ok] + 1); cols.append(2 * ku[ok]); data.append(np.full(int(ok.sum()), 10 ** 6, dtype=np.int32))
    n = len(lanes)
    NA = 2 * N
    SRC, SNK = NA + 2 * n, NA + 2 * n + 1
    rr = max(1, int(round(rloc / cell)))
    offs = [(di, dj) for di in range(-rr, rr + 1) for dj in range(-rr, rr + 1) if di * di + dj * dj <= rr * rr + 1e-9]
    def fan(pt):
        ci = int(round((pt[0] - field.X0) / cell)); cj = int(round((pt[1] - field.Y0) / cell))
        out = []
        for di, dj in offs:
            p_, q_ = ci + di, cj + dj
            if 0 <= p_ < GNX and 0 <= q_ < GNY and idx[p_, q_] >= 0:
                out.append(int(idx[p_, q_]))
        return out
    fans = []
    for x, l in enumerate(lanes):
        ca, cb = fan(l["A"]), fan(l["B"])
        fans.append((ca, cb))
        if not ca or not cb:
            continue
        rows.append(np.array([SRC])); cols.append(np.array([NA + 2 * x])); data.append(np.array([1], dtype=np.int32))
        rows.append(np.full(len(ca), NA + 2 * x)); cols.append(2 * np.array(ca)); data.append(np.ones(len(ca), dtype=np.int32))
        rows.append(np.array([NA + 2 * x + 1])); cols.append(np.array([SNK])); data.append(np.array([1], dtype=np.int32))
        rows.append(2 * np.array(cb) + 1); cols.append(np.full(len(cb), NA + 2 * x + 1)); data.append(np.ones(len(cb), dtype=np.int32))
    rows = np.concatenate(rows); cols = np.concatenate(cols); data = np.concatenate(data)
    M = sparse.csr_matrix((data, (rows, cols)), shape=(SNK + 1, SNK + 1))
    res = maximum_flow(M, SRC, SNK)
    fl = res.flow
    cellidx = {int(idx[i_, j_]): (int(i_), int(j_)) for i_, j_ in zip(a, b)}   # cell k -> (i,j)
    def arcs_from(u):
        row = fl[u]
        p, q = row.indices, row.data
        return [(int(c), float(d)) for c, d in zip(p, q) if d > 0.5]
    routes = {}
    for x, l in enumerate(lanes):
        ca, cb = fans[x]
        if not ca or not cb:
            continue
        nxt = [c // 2 for c, d in arcs_from(NA + 2 * x)]
        if not nxt:
            continue
        c = int(nxt[0]); path = [c]; guard = 0
        while guard < 100000:
            guard += 1
            outs = arcs_from(2 * c + 1)
            tgt = None
            for c2, d in outs:
                if c2 == NA + 2 * x + 1:
                    tgt = "END"; break
                if c2 % 2 == 0:
                    tgt = c2 // 2; break
            if tgt == "END":
                break
            if tgt is None:
                break
            path.append(int(tgt)); c = int(tgt)
        routes[l["net"]] = [cellidx[c] for c in path]
    return routes, int(res.flow_value), N


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cell", type=float, default=0.10)
    ap.add_argument("--iters", type=int, default=6)
    ap.add_argument("--max-expand", type=int, default=900000)
    ap.add_argument("--keepouts", default="", help="额外 keepout 线段(JSON): [[x1,y1,x2,y2],…]（走廊 ECO 预留）")
    ap.add_argument("--movable-nets", default="", help="逗号分隔：视为可腾挪之缝合孔/走线网（§2.4(a)-2 量化）")
    ap.add_argument("--conn", type=int, default=8, choices=[4, 8],
                    help="4=曼哈顿（无对角步 ⇒ 连续几何两两间距=栅格间距 · 可证合法）")
    ap.add_argument("--extra-margin", type=float, default=0.0,
                    help="额外真余量门（mm）：自由格须距障碍 ≥ hw+req+该值 ⇒ 输出余量下限具名且 ≥ 判据")
    ap.add_argument("--algo", default="pathfinder", choices=["pathfinder", "hard", "maxflow"],
                    help="pathfinder=软罚协商；hard=硬带 + 多轮全量重排（保证两两分离）")
    a = ap.parse_args()
    model = json.load(open(a.model))
    field = Field(model, hw=HW_B, step=a.cell, layer="B.Cu",
                  movable_nets=[x for x in a.movable_nets.split(',') if x])
    bad = field.other.copy()
    if a.extra_margin > 0:                       # 真余量门：`other`（已按 net 取 req 膨胀）再按格膨胀 +extra
        from scipy import ndimage
        it = max(1, int(round(a.extra_margin / field.step)))
        bad = ndimage.binary_dilation(field.other, iterations=it)
        print("  [余量门] other 再膨胀 %d 格（≈%.2fmm）" % (it, it * field.step))
    for seg in (json.loads(a.keepouts) if a.keepouts else []):
        field._seg(bad, seg[0], seg[1], seg[2], seg[3], LANE_W / 2 + 0.175)
    lanes = lanes_of(model)
    occ = np.zeros(bad.shape, dtype=np.float32)
    R = occ_radius_cells(a.cell)
    goal = {}
    sl = {}
    for l in lanes:
        s_ = snap_free(field, bad, l["A"]); g_ = snap_free(field, bad, l["B"])
        if s_[0] is None or g_[0] is None:
            sl[l["net"]] = {"status": "NO_FREE_ENDPOINT"}; continue
        sl[l["net"]] = {"status": "PENDING", "start": s_, "goal": g_}
    pend = [n for n, v in sl.items() if v["status"] == "PENDING"]
    order = sorted(pend, key=lambda n: -math.hypot(sl[n]["goal"][0] - sl[n]["start"][0],
                                                   sl[n]["goal"][1] - sl[n]["start"][1]))
    print("车道 %d · 待布 %d · 栅格 %dx%d cell=%.2f · R=%d" % (len(lanes), len(pend), field.NX, field.NY, a.cell, R))

    def stamp(pth, sign):
        for (i, j) in pth:
            i0, i1 = max(0, i - R), min(field.NX - 1, i + R)
            j0, j1 = max(0, j - R), min(field.NY - 1, j + R)
            occ[i0:i1 + 1, j0:j1 + 1] += sign

    routed = {}
    best = None
    if a.algo == "maxflow":
        rr_, fval, NN = maxflow_routes(field, bad, lanes, a.cell, a.rloc if hasattr(a, "rloc") else 1.0, a.conn)
        print("  [maxflow] flow=%d/32 · 路径给出 %d 条（节点不相交）" % (fval, len(rr_)))
        routed = rr_
        for l in lanes:
            sl[l["net"]]["status"] = "ROUTED" if l["net"] in routed else "FAILED"
    if a.algo == "hard":
        # 硬带：每轮按 (上轮失败者优先) 顺序重排全部车道；occ>0 处禁行 ⇒ 输出天然两两分离
        ord2 = list(order)
        for it in range(a.iters):
            occ[:] = 0.0
            routed = {}
            for n in ord2:
                p = astar(field, bad, occ, sl[n]["start"], sl[n]["goal"], a.cell,
                          max_expand=a.max_expand, hard=True, conn=a.conn)
                if p:
                    routed[n] = p; stamp(p, +1.0)
            over = float(np.maximum(occ - 1.0, 0.0).sum())
            print("  [hard %d] routed=%d/32 overuse=%.0f" % (it, len(routed), over))
            sc = (len(routed), -over)
            if best is None or sc > best[0]:
                best = (sc, {k: list(v) for k, v in routed.items()})
            if len(routed) == len(order):
                break
            fail = [n for n in ord2 if n not in routed]
            ord2 = fail + [n for n in ord2 if n in routed]      # 失败者优先重排
        routed = best[1]
        for n in routed:
            sl[n]["status"] = "ROUTED"
        for n in order:
            if n not in routed and sl[n]["status"] != "NO_FREE_ENDPOINT":
                sl[n]["status"] = "FAILED"
    for it in range(a.iters) if a.algo == "pathfinder" else ():
        pres_fac = 0.6 * (2.0 ** it)                     # 历史/现存代价双递增
        for n in order:
            if n in routed:                              # 全量 rip-up：先撤后重布
                stamp(routed[n], -1.0); del routed[n]
            p = astar(field, bad, occ, sl[n]["start"], sl[n]["goal"], a.cell,
                      max_expand=a.max_expand, pres_fac=pres_fac, conn=a.conn)
            if p:
                routed[n] = p; stamp(p, +1.0)
        over = float(np.maximum(occ - 1.0, 0.0).sum())
        sc = (len(routed), -over)
        print("  [pf %d] pres=%.1f routed=%d/32 overuse=%.0f" % (it, pres_fac, len(routed), over))
        if best is None or sc > best[0]:
            best = (sc, {k: list(v) for k, v in routed.items()})
        if len(routed) == len(order) and over == 0:
            break
    if a.algo != "maxflow":
        routed = best[1]
    for n in routed:
        sl[n]["status"] = "ROUTED"
    for n in order:
        if n not in routed and sl[n]["status"] != "NO_FREE_ENDPOINT":
            sl[n]["status"] = "FAILED"
    # 输出
    routes = {}
    for n, pth in routed.items():
        pts = simplify([(field.X0 + i * a.cell, field.Y0 + j * a.cell) for (i, j) in pth])
        routes[n] = {"pts": [[round(x, 4), round(y, 4)] for (x, y) in pts],
                     "len_mm": round(sum(math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1])
                                         for k in range(len(pts) - 1)), 3),
                     "cells": len(pth)}
    ok = sorted(routes); ng = sorted(n for n in order if n not in routes)
    ver = verify_routes(field, routes, movable=getattr(field, "movable", ())) if routes else {}
    if ver:
        print("  [精确闸] 车道互检最小间隙 %.4f mm（判据 ≥%.3f）· 违规 %d 条 · 障碍最小余量 %.4f mm · 余量违规 %d" % (
            ver["lane_pitch_min_gap_mm"], PITCH_B - LANE_W, len(ver["lane_pitch_violations"]),
            ver["clearance_min_mm"], len(ver["clearance_violations"])))
    wo = {"artifact": "k2_p4_b2_bcu_router_v1_workorder", "model": a.model, "cell_mm": a.cell,
          "layer": "B.Cu", "lane_w_mm": LANE_W, "pitch_mm": PITCH_B, "conn": a.conn, "algo": a.algo,
          "movable_nets": sorted(getattr(field, "movable", [])),
          "method": "B.Cu 单层 · 8 邻接 A*（长度 + **PathFinder 协商拥塞**（过用罚·pres_fac 逐轮加倍）+ 贴边惩罚 + 贴限禁行）+ 难度排序 + **每轮全量 rip-up-and-reroute**",
          "n_lanes": len(lanes), "n_routed": len(ok), "n_failed": len(ng),
          "routed": ok, "failed": ng, "routes": routes, "geometric_gate": ver,
          "extra_margin_mm": a.extra_margin,
          "vias": {"V1": "F.Cu-B.Cu 原地保留", "V4": "F.Cu-In2.Cu → 同位换 span 为 F.Cu-B.Cu",
                   "delete": ["V2(In5-B)", "V3(In2-In5)"]},
          "note": "本件为**只读工作令**：未改板；真余量下限须由 apply 后之 DRC + 几何复核具名（禁贴限交付）"}
    json.dump(wo, open(a.out, "w"), ensure_ascii=False, indent=1, sort_keys=True)
    print("routed %d/%d · failed=%s" % (len(ok), len(order), ng))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
