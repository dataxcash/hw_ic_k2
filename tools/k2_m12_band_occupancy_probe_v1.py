#!/usr/bin/env python3
"""K2 · M-12「三横带占用 19–27%」**口径归因探针**（只读取证，确定性；无 verdict）。

登记册 M-12 原文：「布局：左 30/右 12；三横带占用 **19–27%**（ENG 复算 5.3%/17.8%/0.7% ⇒ 口径不明）」。
本器把可疑口径**枚举穷举**，看哪一族能落在该量级（不择一、不给判定；口径与阈值归监理）。

枚举维度：板（l4 冻结 / l5 仓库 / 复合候选）× 轴（y 三等分 = 三横带 / x 三等分）
× 定义（焊盘 AABB · 焊盘真多边形 · courtyard AABB · courtyard 真多边形）
占用 = 该带内**并集面积** / 带面积（带面积 = 带厚 × 板框正交跨度）。

用法：
  AppDir/usr/bin/python3.11 k2/tools/k2_m12_band_occupancy_probe_v1.py \
      --board <l4> --board <l5> [--board <composite>] [--bands 3] [--json /tmp/out.json]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import pcbnew

NM = 1_000_000
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs",
                                "drafts", "p4-j8-density-clearance-v1"))
import j8_dc_common as C  # noqa: E402  （pad AABB 口径与 J-8 测量件同源）


def sha16(path):
    import hashlib
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def rect_poly(x0, y0, x1, y1):
    ps = pcbnew.SHAPE_POLY_SET()
    ch = pcbnew.SHAPE_LINE_CHAIN()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        ch.Append(pcbnew.VECTOR2I(int(x), int(y)))
    ch.SetClosed(True)
    ps.AddOutline(ch)
    return ps


def pad_poly(p):
    sz, pos = p.GetSize(), p.GetPosition()
    hw, hh = sz.x / 2.0, sz.y / 2.0
    if p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:          # 圆盘按外接方（保守）
        hw = hh = max(sz.x, sz.y) / 2.0
    a = math.radians(p.GetOrientationDegrees())
    ca, sa = math.cos(a), math.sin(a)
    return [(pos.x + dx * ca - dy * sa, pos.y + dx * sa + dy * ca)
            for dx, dy in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))]


def court_polys(fp):
    out = []
    for lay in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
        ps = fp.GetCourtyard(lay)
        for i in range(ps.OutlineCount()):
            ol = ps.Outline(i)
            out.append([(ol.CPoint(k).x, ol.CPoint(k).y) for k in range(ol.PointCount())])
    return out


def union_area(polys, clip):
    ps = pcbnew.SHAPE_POLY_SET()
    for pts in polys:
        ch = pcbnew.SHAPE_LINE_CHAIN()
        for x, y in pts:
            ch.Append(pcbnew.VECTOR2I(int(x), int(y)))
        ch.SetClosed(True)
        ps.AddOutline(ch)
    ps.BooleanIntersection(clip)
    return abs(ps.Area())


def measure(bd, axis, kind, n):
    fr = C.edge_aabb_nm(bd)
    if axis == "y":
        lo, hi, o0, o1 = fr[1], fr[3], fr[0], fr[2]
    else:
        lo, hi, o0, o1 = fr[0], fr[2], fr[1], fr[3]
    h = (hi - lo) / float(n)
    out = []
    for i in range(n):
        b0, b1 = lo + i * h, lo + (i + 1) * h
        clip = rect_poly(o0, b0, o1, b1) if axis == "y" else rect_poly(b0, o0, b1, o1)
        polys = []
        for f in bd.GetFootprints():
            if kind == "pad_aabb":
                for p in f.Pads():
                    b = C.pad_aabb_nm(p)
                    polys.append([(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])])
            elif kind == "pad_true":
                polys += [pad_poly(p) for p in f.Pads()]
            elif kind == "court_aabb":
                for pts in court_polys(f):
                    xs = [x for x, _ in pts]
                    ys = [y for _, y in pts]
                    polys.append([(min(xs), min(ys)), (max(xs), min(ys)),
                                  (max(xs), max(ys)), (min(xs), max(ys))])
            elif kind == "court_true":
                polys += court_polys(f)
        area = union_area(polys, clip) / float(NM * NM)
        band = (b1 - b0) / NM * (o1 - o0) / NM
        out.append(round(area / band, 5) if band else 0.0)
    return out


AXES = ("y", "x")
KINDS = ("pad_aabb", "pad_true", "court_aabb", "court_true")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", action="append", required=True)
    ap.add_argument("--bands", type=int, default=3)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    res = {"bands": a.bands, "boards": []}
    for path in a.board:
        bd = pcbnew.LoadBoard(path)
        rec = {"board": path, "board_sha16": sha16(path),
               "n_footprints": len(list(bd.GetFootprints())),
               "n_with_courtyard": sum(1 for f in bd.GetFootprints() if court_polys(f)),
               "table": {}}
        for axis in AXES:
            for kind in KINDS:
                r = measure(bd, axis, kind, a.bands)
                rec["table"]["%s_%s" % (axis, kind)] = {"bands": r, "max": max(r)}
        res["boards"].append(rec)
        print("== %s (sha16 %s, fps %d, 有 courtyard %d 件)"
              % (os.path.basename(path), rec["board_sha16"], rec["n_footprints"],
                 rec["n_with_courtyard"]))
        for k, v in rec["table"].items():
            hit = "  <== 落 19–27%" if all(0.19 <= x <= 0.27 for x in v["bands"]) else (
                "  (含 19–27% 值)" if any(0.19 <= x <= 0.27 for x in v["bands"]) else "")
            print("   %-20s %s  max=%.4f%s"
                  % (k, " ".join("%.4f" % x for x in v["bands"]), v["max"], hit))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1, ensure_ascii=False)
        print("json:", a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
