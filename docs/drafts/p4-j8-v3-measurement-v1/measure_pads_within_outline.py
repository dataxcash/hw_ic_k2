#!/usr/bin/env python3
"""K2 · P4 · J-8「出框」测量实现（**只出测量，无 verdict**；供 gate 侧判定器消费）。

判据维度（登记册 §C J-8「器件位置合理性 … 出框 …」；P3-4 = 接口焊盘不出框，内缩 0.3mm）。
本件按已定实现设计（`K2-P4-CRITERIA-DRAFT-AND-MANIFEST-V2.md` §2）：
  ① 解析 `Edge.Cuts` → 外框 AABB，按 `--inset-mm`（默认 0.3）内缩；
  ② 逐 pad 取 AABB（**矩形/梯形/圆角按旋转外接框；圆按半径；椭圆按「矩形段 ⊕ 两端半圆」精确**）；
  ③ 判 pad AABB 是否完全落在内缩框内；另给**真外框多边形**（`GetBoardPolygonOutlines` + `Inflate(-inset)`）的更强口径。
输出 JSON **不含 `verdict` 字段**（`§3.3-3`：结论由判定器派生）。`--fail-on-violation` 仅在 gate 侧需要 rc 时使用。

用法：
  AppDir/usr/bin/python3.11 measure_pads_within_outline.py --board <板> [--inset-mm 0.3] [--json out.json] [--fail-on-violation]
"""
import argparse
import hashlib
import json
import math
import os
import sys

import pcbnew

NM = 1_000_000
INTERFACE_DEFAULT = ["J2", "J3", "J4", "J6", "J9", "J11", "J12", "J13"]


def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def _rot(x, y, deg):
    a = math.radians(deg)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def _union(boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def _rect_box(cx, cy, w, h, deg):
    pts = [_rot(sx * w / 2.0, sy * h / 2.0, deg) for sx in (-1, 1) for sy in (-1, 1)]
    return _union([(cx + p[0], cy + p[1], cx + p[0], cy + p[1]) for p in pts])


def pad_aabb_nm(pad):
    """精确/保守 AABB（nm）。形状口径：circle=半径；oval=矩形段⊕两端半圆；其余=旋转外接框（保守）。"""
    p = pad.GetPosition()
    s = pad.GetSize()
    ang = pad.GetOrientationDegrees()
    cx, cy, w, h = p.x, p.y, s.x, s.y
    shape = pad.GetShape()
    if shape == pcbnew.PAD_SHAPE_CIRCLE:
        r = max(w, h) / 2.0
        return (cx - r, cy - r, cx + r, cy + r), "circle"
    if shape == pcbnew.PAD_SHAPE_OVAL:
        r = min(w, h) / 2.0
        seg = abs(w - h) / 2.0
        boxes = []
        for sx in (-1, 1):
            dx, dy = _rot(sx * seg, 0.0, ang)
            boxes.append((cx + dx - r, cy + dy - r, cx + dx + r, cy + dy + r))
        return _union(boxes), "oval"
    label = {pcbnew.PAD_SHAPE_RECT: "rect", pcbnew.PAD_SHAPE_ROUNDRECT: "roundrect",
             pcbnew.PAD_SHAPE_TRAPEZOID: "trapezoid", pcbnew.PAD_SHAPE_CUSTOM: "custom"}.get(shape, str(shape))
    return _rect_box(cx, cy, w, h, ang), label + "(外接框)"


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


def polyset_of_box(box):
    x0, y0, x1, y1 = box
    ps = pcbnew.SHAPE_POLY_SET()
    ch = pcbnew.SHAPE_LINE_CHAIN()
    for pt in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        ch.Append(pcbnew.VECTOR2I(int(pt[0]), int(pt[1])))
    ch.SetClosed(True)
    ps.AddOutline(ch)
    return ps


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--inset-mm", type=float, default=0.3)
    ap.add_argument("--interface-refs", default=",".join(INTERFACE_DEFAULT))
    ap.add_argument("--json", default=None)
    ap.add_argument("--fail-on-violation", action="store_true")
    a = ap.parse_args(argv)
    inset = int(round(a.inset_mm * NM))
    bd = pcbnew.LoadBoard(a.board)
    edges = edge_aabb_nm(bd)
    if edges is None:
        print("[INFRA] no Edge.Cuts", file=sys.stderr)
        return 2
    frame = (edges[0] + inset, edges[1] + inset, edges[2] - inset, edges[3] - inset)
    # 真外框多边形（更强口径）
    inner_poly = None
    try:
        outline = pcbnew.SHAPE_POLY_SET()
        bd.GetBoardPolygonOutlines(outline, True)
        outline.Inflate(-inset, 32, 5_000)   # (amount, circle_segments, max_error_nm)
        inner_poly = outline
    except Exception as e:  # pragma: no cover
        inner_poly = None
        poly_err = f"{type(e).__name__}: {e}"
    iface = set(x.strip() for x in a.interface_refs.split(",") if x.strip())
    rows, bad_aabb, bad_poly, bad_aabb_iface = [], [], [], []
    for f in bd.GetFootprints():
        ref = f.GetReference()
        for pad in f.Pads():
            box, how = pad_aabb_nm(pad)
            rec = {"ref": ref, "pad": pad.GetPadName(), "net": pad.GetNetname(),
                   "box_mm": [round(v / NM, 4) for v in box], "aabb_rule": how,
                   "interface": ref in iface}
            out = not (box[0] >= frame[0] and box[1] >= frame[1] and box[2] <= frame[2] and box[3] <= frame[3])
            rec["out_of_frame_aabb"] = out
            if inner_poly is not None:
                cand = polyset_of_box(box)
                cand.BooleanSubtract(inner_poly)
                out2 = cand.OutlineCount() > 0
                rec["out_of_frame_polygon"] = out2
            else:
                out2 = None
                rec["out_of_frame_polygon"] = None
            if out:
                bad_aabb.append(rec)
                if ref in iface:
                    bad_aabb_iface.append(rec)
            if out2:
                bad_poly.append(rec)
            rows.append(rec)
    res = {
        "check": "pads_within_outline",
        "board": os.path.abspath(a.board),
        "board_sha16": sha16(a.board),
        "inset_mm": a.inset_mm,
        "frame_inset_mm": [round(v / NM, 4) for v in frame],
        "n_pads": len(rows),
        "aabb_scope": {"n_out_of_frame": len(bad_aabb),
                       "n_out_of_frame_interface": len(bad_aabb_iface),
                       "refs_out_of_frame": sorted({r["ref"] for r in bad_aabb}),
                       "violations": bad_aabb},
        "polygon_scope": {"n_out_of_frame": len(bad_poly),
                          "violations": bad_poly},
        "per_pad": rows,
    }
    if inner_poly is None:
        res["polygon_scope"]["error"] = poly_err
    if a.json:
        json.dump(res, open(a.json, "w"), ensure_ascii=False, indent=1)
    print(f"[pads_within_outline] board={os.path.basename(a.board)} sha16={res['board_sha16']} "
          f"inset={a.inset_mm}mm pads={res['n_pads']}")
    print(f"  AABB 口径：出框 {len(bad_aabb)}（其中接口件 {len(bad_aabb_iface)}）refs={res['aabb_scope']['refs_out_of_frame']}")
    print(f"  真框多边形口径：出框 {len(bad_poly)}")
    for r in bad_aabb[:12]:
        print(f"    AABB {r['ref']}.{r['pad']} {r['net']} box={r['box_mm']} rule={r['aabb_rule']}")
    if a.fail_on_violation and (bad_aabb or bad_poly):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
