#!/usr/bin/env python3
"""k2_corridor_redraw_v1.py --- **图纸层（B1）重画引擎**（#K2-412 §四.1 的 §16.3 element③「修正后完整施工图」）。

WHY（大白话）：v1 的 8 条走廊是照"空板"画的，对本板 8/8 被异网铜压住（R1160）。本件给出**确定性、零搜索**
的重画规则：把每条走廊缩成"**含端点、且完全避开（占位者 AABB ⊕ 净空）的最大轴对齐子矩**"；若缩不出
（端点被围死）⇒ 返回**围死它的那几件**，即"必须让路"的**具名清单**。

确定性：候选边界 = 走廊四边 ∪ 每个（已膨胀）占位者的四条边，**枚举所有含端点的 x 带取该带内最大 y 区间**，
按 (-面积, x0, y0, x1, y1) 取唯一最优；**不搜索、不试参、不迭代**。纯函数，不碰板。
"""
from __future__ import annotations
import argparse, json, sys


def _inflate(o, cl):
    return (o[0] - cl, o[1] - cl, o[2] + cl, o[3] + cl)


def _ovl_x(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0])


def clear_subrect_containing_pts(rect, obstacles, clearance, pts):
    """**纯函数 · 确定性 · 零搜索**（多点版）。返回 `(subrect | None, blockers)`：
    `subrect` = `rect` 内**同时含全部 `pts`**、且与 `obstacles⊕clearance` 不相交的**最大**轴对齐子矩（唯一）；
    缩不出 ⇒ `(None, blockers)`，`blockers` = **膨胀后含 pts 中点的占位者**（= 必须让路的清单）。
    候选边 = 走廊四边 ∪ 膨胀占位者四边；枚举含全部 pts 的 x 带，取带内**同时含全部 pts** 的最大 y 区间。"""
    x0, y0, x1, y1 = [float(v) for v in rect]
    P = [(float(a), float(b)) for a, b in pts]
    py_lo, py_hi = min(p[1] for p in P), max(p[1] for p in P)
    infl = [_inflate([float(v) for v in o], clearance) for o in obstacles]
    cand_x = {x0, x1}
    for o in infl:
        for v in (o[0], o[2]):
            if x0 <= v <= x1:
                cand_x.add(v)
    cand_x = sorted(cand_x)
    best = None
    for i, xl in enumerate(cand_x):
        for xr in cand_x[i + 1:]:
            if any(not (xl - 1e-9 <= p[0] <= xr + 1e-9) for p in P):
                continue                                   # the band must contain every point's x
            band = (xl, y0, xr, y1)
            blk = [o for o in infl if _ovl_x(o, band)]
            if any(not (o[3] < py_lo - 1e-9 or o[1] > py_hi + 1e-9) for o in blk):
                continue                                   # a blocker sits inside [py_lo, py_hi] for this band
            below = [o[3] for o in blk if o[3] <= py_lo + 1e-9]
            above = [o[1] for o in blk if o[1] >= py_hi - 1e-9]
            yl, yh = max([y0] + below), min([y1] + above)
            if yh - yl <= 1e-12 or yl > py_lo + 1e-9 or yh < py_hi - 1e-9:
                continue
            cand = (xl, yl, xr, yh)
            area = (xr - xl) * (yh - yl)
            if best is None or area > best[0] + 1e-12 or (abs(area - best[0]) <= 1e-12 and cand < best[1]):
                best = (area, cand)
    if best is None:
        mx = sum(p[0] for p in P) / len(P); my = sum(p[1] for p in P) / len(P)
        blockers = [o for o in infl if o[0] - 1e-9 <= mx <= o[2] + 1e-9 and o[1] - 1e-9 <= my <= o[3] + 1e-9]
        return None, blockers
    return best[1], []


def clear_subrect_containing(rect, obstacles, clearance, point):
    """单点版（= `clear_subrect_containing_pts` 的 1 元素特例；API 不变）。"""
    return clear_subrect_containing_pts(rect, obstacles, clearance, [point])


def redraw_corridors(gaps, occupants_by_gap, clearance, point_of):
    """把 v2 规则逐条套到 8 个 gap：`point_of(gap)` 取该 gap 的**域内起点**。
    返回 list（每条：net / v2_subrect / status=usable|ENDPOINT_BOXED / blockers_n）。"""
    out = []
    for g in gaps:
        p = point_of(g)
        rect = g["rect"]
        occ = occupants_by_gap.get(g["net"], [])
        sub, blk = clear_subrect_containing(rect, occ, clearance, p)
        out.append({"net": g["net"], "v1_rect": rect, "point": list(p),
                    "v2_subrect": list(sub) if sub else None,
                    "status": "usable" if sub else "ENDPOINT_BOXED",
                    "n_blockers_at_point": len(blk)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True, help="json: {gaps:[{net,rect}], occupants:{net:[[x0,y0,x1,y1],...]}, points:{net:[x,y]}, clearance}")
    a = ap.parse_args()
    p = json.load(open(a.params, encoding="utf-8"))
    res = redraw_corridors(p["gaps"], p["occupants"], float(p["clearance"]),
                           lambda g: p["points"][g["net"]])
    print(json.dumps({"artifact": "k2_corridor_redraw_v1", "corridors": res}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
