#!/usr/bin/env python3
"""K2 · P4 · J-8 密度/间距测量 · 共用几何层（只读；与 `measure_pads_within_outline.py` 同源 pad AABB 口径）。

pad AABB 口径：circle = 半径；oval = 矩形段 ⊕ 两端半圆；其余（rect/roundrect/trapezoid/custom）= 旋转外接框（保守）。
坐标单位 = nm（KiCad 内部单位）；导出时换算 mm。
"""
import hashlib
import math

import pcbnew

NM = 1_000_000


def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def rot(x, y, deg):
    a = math.radians(deg)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def union(boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def rect_box(cx, cy, w, h, deg):
    pts = [rot(sx * w / 2.0, sy * h / 2.0, deg) for sx in (-1, 1) for sy in (-1, 1)]
    return union([(cx + p[0], cy + p[1], cx + p[0], cy + p[1]) for p in pts])


def pad_aabb_nm(pad):
    p = pad.GetPosition()
    s = pad.GetSize()
    ang = pad.GetOrientationDegrees()
    cx, cy, w, h = p.x, p.y, s.x, s.y
    shape = pad.GetShape()
    if shape == pcbnew.PAD_SHAPE_CIRCLE:
        r = max(w, h) / 2.0
        return (cx - r, cy - r, cx + r, cy + r)
    if shape == pcbnew.PAD_SHAPE_OVAL:
        r = min(w, h) / 2.0
        seg = abs(w - h) / 2.0
        boxes = []
        for sx in (-1, 1):
            dx, dy = rot(sx * seg, 0.0, ang)
            boxes.append((cx + dx - r, cy + dy - r, cx + dx + r, cy + dy + r))
        return union(boxes)
    return rect_box(cx, cy, w, h, ang)


def edge_aabb_nm(bd):
    xs, ys = [], []
    for d in bd.GetDrawings():
        if pcbnew.LayerName(d.GetLayer()) != "Edge.Cuts":
            continue
        try:
            p1, p2 = d.GetStart(), d.GetEnd()
            xs += [p1.x, p2.x]
            ys += [p1.y, p2.y]
        except Exception:
            b = d.GetBoundingBox()
            xs += [b.GetLeft(), b.GetRight()]
            ys += [b.GetTop(), b.GetBottom()]
    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def union_area(rects):
    """矩形并集面积（nm²）：x 坐标压缩 + y 区间合并。"""
    if not rects:
        return 0.0
    xs = sorted({r[0] for r in rects} | {r[2] for r in rects})
    total = 0.0
    for i in range(len(xs) - 1):
        x0, x1 = xs[i], xs[i + 1]
        if x1 <= x0:
            continue
        mid = (x0 + x1) / 2.0
        ivs = sorted((r[1], r[3]) for r in rects if r[0] <= mid <= r[2])
        h, cur = 0.0, None
        for a, b in ivs:
            if cur is None:
                cur = [a, b]
            elif a <= cur[1]:
                cur[1] = max(cur[1], b)
            else:
                h += cur[1] - cur[0]
                cur = [a, b]
        if cur is not None:
            h += cur[1] - cur[0]
        total += (x1 - x0) * h
    return total


def gap_mm(a, b):
    """两 AABB 的最小间隙（mm）；相交时为 0。"""
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy) / NM


def collect(bd):
    """逐封装取：位置/朝向/封装 AABB/courtyard AABB/逐 pad（名、网、AABB、属性、钻孔）。"""
    fps = []
    for f in bd.GetFootprints():
        pos = f.GetPosition()
        cy_boxes = []
        for g in f.GraphicalItems():
            if g.GetLayer() not in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                continue
            try:
                bb = g.GetBoundingBox()
            except Exception:
                continue
            cy_boxes.append((bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
        pads = []
        for pad in f.Pads():
            dr = pad.GetDrillSize()
            pads.append({"num": pad.GetPadName(), "net": pad.GetNetname(), "box": pad_aabb_nm(pad),
                         "attr": pad.GetAttribute(), "drill": (dr.x, dr.y)})
        fps.append({"ref": f.GetReference(), "x": pos.x, "y": pos.y,
                    "rot": f.GetOrientationDegrees(),
                    "box": union([p["box"] for p in pads]) if pads else None,
                    "courtyard": union(cy_boxes) if cy_boxes else None, "pads": pads})
    return fps
