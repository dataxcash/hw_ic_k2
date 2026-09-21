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
PITCH_B = 0.205 + 2 * 0.175          # 0.555mm 中心距门
LANE_W = 0.205


def occ_radius_cells(cell):
    return max(1, int(math.ceil((PITCH_B - LANE_W) / 2.0 / cell)))


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


def astar(field, bad, occ, start, goal, cell, w_cong=6.0, w_margin=3.0, max_expand=900000):
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
    NB = ((1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
          (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142))
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
            m = margin[ni, nj]
            n_clear = m * cell                       # 该格到障碍之名义距离
            pen = w_cong * occ[ni, nj]
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cell", type=float, default=0.10)
    ap.add_argument("--iters", type=int, default=6)
    ap.add_argument("--max-expand", type=int, default=900000)
    ap.add_argument("--keepouts", default="", help="额外 keepout 线段(JSON): [[x1,y1,x2,y2],…]（走廊 ECO 预留）")
    a = ap.parse_args()
    model = json.load(open(a.model))
    field = Field(model, hw=HW_B, step=a.cell, layer="B.Cu")
    bad = field.other.copy()
    for seg in (json.loads(a.keepouts) if a.keepouts else []):
        field._seg(bad, seg[0], seg[1], seg[2], seg[3], LANE_W / 2 + 0.175)
    lanes = lanes_of(model)
    occ = np.zeros(bad.shape, dtype=np.float32)
    R = occ_radius_cells(a.cell)
    goal = {}
    sl = {}
    for l in lanes:
        s = snap_free(field, bad, l["A"]); g = snap_free(field, bad, l["B"])
        if s[0] is None or g[0] is None:
            sl[l["net"]] = {"status": "NO_FREE_ENDPOINT"}; continue
        goal[l["net"]] = g
        sl[l["net"]] = {"status": "PENDING", "start": s, "goal": g}
    pend = [n for n, v in sl.items() if v["status"] == "PENDING"]
    order = sorted(pend, key=lambda n: -math.hypot(sl[n]["goal"][0] - sl[n]["start"][0],
                                                   sl[n]["goal"][1] - sl[n]["start"][1]))
    print("车道 %d · 待布 %d · 栅格 %dx%d cell=%.2f" % (len(lanes), len(pend), field.NX, field.NY, a.cell))
    routed = {}
    for it in range(a.iters):
        changed = 0
        for n in order:
            if sl[n]["status"] == "ROUTED":
                continue
            occ[:] = 0.0
            for m, pth in routed.items():
                for (i, j) in pth:
                    for di in range(-R, R + 1):
                        for dj in range(-R, R + 1):
                            ii, jj = i + di, j + dj
                            if 0 <= ii < occ.shape[0] and 0 <= jj < occ.shape[1]:
                                occ[ii, jj] += 1.0
            p = astar(field, bad, occ, sl[n]["start"], sl[n]["goal"], a.cell, max_expand=a.max_expand)
            if p:
                routed[n] = p
                sl[n]["status"] = "ROUTED"
                sl[n]["iter"] = it
                changed += 1
                print("  [it%d] ROUTED %-26s cells=%d" % (it, n, len(p)))
        if not changed:
            break
    # rip-up：对失败网，撤掉“冲突最多”的已布网（占位重叠最高者）后重试
    for it in range(a.iters):
        fail = [n for n in order if sl[n]["status"] != "ROUTED"]
        if not fail:
            break
        for n in fail:
            best = None
            occ[:] = 0.0
            for m, pth in routed.items():
                c = 0
                for (i, j) in pth:
                    for di in range(-R, R + 1):
                        for dj in range(-R, R + 1):
                            ii, jj = i + di, j + dj
                            if 0 <= ii < occ.shape[0] and 0 <= jj < occ.shape[1]:
                                occ[ii, jj] += 1.0
            for m, pth in routed.items():
                c = sum(occ[i, j] for (i, j) in pth)
                if best is None or c > best[0]:
                    best = (c, m)
            if not best:
                break
            del routed[best[1]]
            sl[best[1]]["status"] = "PENDING"
            occ[:] = 0.0
            for m, pth in routed.items():
                for (i, j) in pth:
                    for di in range(-R, R + 1):
                        for dj in range(-R, R + 1):
                            ii, jj = i + di, j + dj
                            if 0 <= ii < occ.shape[0] and 0 <= jj < occ.shape[1]:
                                occ[ii, jj] += 1.0
            p = astar(field, bad, occ, sl[n]["start"], sl[n]["goal"], a.cell, max_expand=a.max_expand)
            if p:
                routed[n] = p
                sl[n]["status"] = "ROUTED"
                sl[n]["iter"] = 100 + it
                print("  [ripup%d] %-26s routed (rewound %s)" % (it, n, best[1]))
    # 输出
    routes = {}
    for n, pth in routed.items():
        pts = simplify([(field.X0 + i * a.cell, field.Y0 + j * a.cell) for (i, j) in pth])
        routes[n] = {"pts": [[round(x, 4), round(y, 4)] for (x, y) in pts],
                     "len_mm": round(sum(math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1])
                                         for k in range(len(pts) - 1)), 3),
                     "cells": len(pth)}
    ok = sorted(routes); ng = sorted(n for n in order if n not in routes)
    wo = {"artifact": "k2_p4_b2_bcu_router_v1_workorder", "model": a.model, "cell_mm": a.cell,
          "layer": "B.Cu", "lane_w_mm": LANE_W, "pitch_mm": PITCH_B,
          "method": "B.Cu 单层 · 8 邻接 A*（长度 + 拥塞惩罚 + 贴边惩罚 · 贴限禁行）+ 难度排序 + rip-up 重布",
          "n_lanes": len(lanes), "n_routed": len(ok), "n_failed": len(ng),
          "routed": ok, "failed": ng, "routes": routes,
          "vias": {"V1": "F.Cu-B.Cu 原地保留", "V4": "F.Cu-In2.Cu → 同位换 span 为 F.Cu-B.Cu",
                   "delete": ["V2(In5-B)", "V3(In2-In5)"]},
          "note": "本件为**只读工作令**：未改板；真余量下限须由 apply 后之 DRC + 几何复核具名（禁贴限交付）"}
    json.dump(wo, open(a.out, "w"), ensure_ascii=False, indent=1, sort_keys=True)
    print("routed %d/%d · failed=%s" % (len(ok), len(order), ng))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
