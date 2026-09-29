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


def clear_subrect_containing(rect, obstacles, clearance, point):
    """**纯函数 · 确定性 · 零搜索**。返回 `(subrect | None, blockers)`：
    - `subrect` = `rect` 内**含 `point`**、且与全部 `obstacles⊕clearance` 不相交的**最大**轴对齐子矩（唯一）；
    - 缩不出 ⇒ `(None, blockers)`，`blockers` = **其（膨胀）矩形含 `point` 的占位者**（= 必须让路的清单）。
    """
    x0, y0, x1, y1 = [float(v) for v in rect]
    px, py = float(point[0]), float(point[1])
    infl = [_inflate([float(v) for v in o], clearance) for o in obstacles]
    cand_x, cand_y = {x0, x1}, {y0, y1}
    for o in infl:
        for v in (o[0], o[2]):
            if x0 <= v <= x1:
                cand_x.add(v)
        for v in (o[1], o[3]):
            if y0 <= v <= y1:
                cand_y.add(v)
    cand_x, cand_y = sorted(cand_x), sorted(cand_y)
    cands = []
    for i, xl in enumerate(cand_x):
        if xl > px + 1e-12:
            continue
        for xr in cand_x[i + 1:]:
            if xr < px - 1e-12:
                continue
            band = (xl, y0, xr, y1)
            blk = [o for o in infl if _ovl_x(o, band)]
            if any(o[1] <= py <= o[3] for o in blk):        # the endpoint itself is inside an inflated occupant
                continue
            below = [o[3] for o in blk if o[3] <= py]
            above = [o[1] for o in blk if o[1] >= py]
            yl = max([y0] + below)
            yh = min([y1] + above)
            if yh - yl <= 1e-12 or not (yl - 1e-9 <= py <= yh + 1e-9):
                continue
            cands.append((xl, yl, xr, yh))
    if not cands:
        blockers = [o for o in infl if o[0] - 1e-9 <= px <= o[2] + 1e-9 and o[1] - 1e-9 <= py <= o[3] + 1e-9]
        return None, blockers
    cands.sort(key=lambda r: (-(r[2] - r[0]) * (r[3] - r[1]), r[0], r[1], r[2], r[3]))
    return cands[0], []


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
