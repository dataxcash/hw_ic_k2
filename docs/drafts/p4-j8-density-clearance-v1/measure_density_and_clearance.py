#!/usr/bin/env python3
"""K2 · P4 · J-8「密度分布 / 关键间距」测量实现（**只出测量，无 verdict**；供 gate 侧判定器消费）。

判据维度（登记册 §C J-8「器件位置合理性：重叠/出框/**密度分布**/**关键间距**/固定孔/回避区」）。
本件补齐 J-8 末项 `density_and_clearance`（v2/v3 manifest 中恒为 `enabled:false, pending`）的**测量侧**：
  ① 密度：多口径网格（默认 5/10/20mm，按件中心）峰值 + 直方图；**三横带占用比**
     （M-12 口径的明确定义版：横带 = Edge.Cuts 外框 AABB 沿 y 三等分；占用 = 焊盘 AABB 并集 ∩ 带 / 带面积）；
  ② 关键间距：异网 pad AABB 最小间隙（保守下界）、孔-孔最小边距、courtyard 最小间隙、pad 到板边最小距；
  ③ 工艺极限实达值（线宽/过孔直径/钻孔/孔环），供 JLC HDI 余量口径判断。
输出 JSON **不含 `verdict` 字段**（结论由判定器派生）。**阈值/口径一律归监理** —— 本件不择一、不设阈。

用法：
  AppDir/usr/bin/python3.11 measure_density_and_clearance.py --board <板> [--json out.json]
"""
import argparse
import json
import math
import os
import sys
from collections import Counter

import pcbnew

from j8_dc_common import NM, collect, edge_aabb_nm, gap_mm, sha16, union_area


def density(fps, frame, cell_mm, origin_mode):
    g = int(round(cell_mm * NM))
    ox, oy = (0, 0) if origin_mode == "absolute_zero" else (frame[0], frame[1])
    fc, pc = Counter(), Counter()
    for f in fps:
        fc[(int((f["x"] - ox) // g), int((f["y"] - oy) // g))] += 1
        for p in f["pads"]:
            cx = (p["box"][0] + p["box"][2]) / 2.0
            cy = (p["box"][1] + p["box"][3]) / 2.0
            pc[(int((cx - ox) // g), int((cy - oy) // g))] += 1
    top = lambda c, n: [{"cell_mm": [round((k[0] * g + ox) / NM, 3), round((k[1] * g + oy) / NM, 3)],
                         "n": v} for k, v in c.most_common(n)]
    return {"cell_mm": cell_mm, "origin_mode": origin_mode,
            "origin_mm": [round(ox / NM, 3), round(oy / NM, 3)],
            "fp_peak_per_cell": max(fc.values()),
            "fp_hist": {str(k): v for k, v in sorted(Counter(fc.values()).items())},
            "fp_top_cells": top(fc, 3), "pad_peak_per_cell": max(pc.values()), "pad_top_cells": top(pc, 2)}


def band_occupancy(fps, frame, n_bands):
    y0, y1 = frame[1], frame[3]
    h = (y1 - y0) / float(n_bands)
    out = []
    for i in range(n_bands):
        by0, by1 = y0 + i * h, y0 + (i + 1) * h
        rects = []
        for f in fps:
            for p in f["pads"]:
                b = p["box"]
                if b[3] < by0 or b[1] > by1:
                    continue
                rects.append((b[0], max(b[1], by0), b[2], min(b[3], by1)))
        area = union_area(rects) / float(NM * NM)
        band_area = (by1 - by0) / NM * (frame[2] - frame[0]) / NM
        out.append({"band": i + 1, "y0_mm": round(by0 / NM, 3), "y1_mm": round(by1 / NM, 3),
                    "pad_coverage_ratio": round(area / band_area, 5)})
    return {"n_bands": n_bands, "axis": "y（Edge.Cuts AABB 沿 y 等分）",
            "definition": "焊盘 AABB 并集 ∩ 带 / 带面积（板框宽度）", "bands": out,
            "max_ratio": max(b["pad_coverage_ratio"] for b in out)}


def clearances(fps, frame):
    pads = [(f["ref"], p) for f in fps for p in f["pads"]]
    best = None
    for i in range(len(pads)):
        r1, p1 = pads[i]
        for j in range(i + 1, len(pads)):
            r2, p2 = pads[j]
            if r1 == r2 or (p1["net"] and p1["net"] == p2["net"]):
                continue
            g = gap_mm(p1["box"], p2["box"])
            if best is None or g < best["gap_mm"]:
                best = {"gap_mm": round(g, 4), "a": f"{r1}.{p1['num']}({p1['net'] or '-'})",
                        "b": f"{r2}.{p2['num']}({p2['net'] or '-'})",
                        "a_mm": [round(v / NM, 3) for v in p1["box"]],
                        "b_mm": [round(v / NM, 3) for v in p2["box"]]}
    holes = []
    for r, p in pads:
        if p["drill"][0] > 0 or p["drill"][1] > 0:
            cx = (p["box"][0] + p["box"][2]) / 2.0
            cy = (p["box"][1] + p["box"][3]) / 2.0
            holes.append((r, p["num"], cx, cy, max(p["drill"]) / 2.0))
    hh = None
    for i in range(len(holes)):
        for j in range(i + 1, len(holes)):
            r1, n1, x1, y1, d1 = holes[i]
            r2, n2, x2, y2, d2 = holes[j]
            edge = (math.hypot(x1 - x2, y1 - y2) - d1 - d2) / NM
            if hh is None or edge < hh[0]:
                hh = (edge, f"{r1}.{n1}", f"{r2}.{n2}")
    cy = [(f["ref"], f["courtyard"]) for f in fps if f["courtyard"]]
    cybest, cyoverlap = None, 0
    for i in range(len(cy)):
        for j in range(i + 1, len(cy)):
            g = gap_mm(cy[i][1], cy[j][1])
            cyoverlap += 1 if g <= 0.0 else 0
            if cybest is None or g < cybest[0]:
                cybest = (g, f"{cy[i][0]}", f"{cy[j][0]}")
    eb = None
    for r, p in pads:
        b = p["box"]
        d = min(b[0] - frame[0], b[1] - frame[1], frame[2] - b[2], frame[3] - b[3]) / NM
        if eb is None or d < eb[0]:
            eb = (d, f"{r}.{p['num']}")
    return {"min_copper_gap_mm": (best or {}).get("gap_mm"), "min_copper_gap_pair": best,
            "min_hole_to_hole_edge_mm": round(hh[0], 4) if hh else None,
            "min_hole_pair": [hh[1], hh[2]] if hh else [], "n_holes": len(holes),
            "courtyard": {"n_with": len(cy), "n_overlap_pairs": cyoverlap,
                          "min_gap_mm": round(cybest[0], 4) if cybest else None,
                          "min_gap_pair": [cybest[1], cybest[2]] if cybest else []},
            "min_pad_to_edge_mm": round(eb[0], 4) if eb else None,
            "min_pad_to_edge_pad": eb[1] if eb else None,
            "scope": "AABB 保守下界（真值 ≥ 本值）；异网跨封装 pad 对"}


def process_min(bd):
    tracks = [t for t in bd.GetTracks() if t.GetClass() != "PCB_VIA"]
    vias = [t for t in bd.GetTracks() if t.GetClass() == "PCB_VIA"]
    vd = [v.GetWidth(pcbnew.F_Cu) for v in vias]
    vdr = [v.GetDrillValue() for v in vias]
    hd = []
    for f in bd.GetFootprints():
        for pad in f.Pads():
            if pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                dr = pad.GetDrillSize()
                hd.append(min(dr.x, dr.y))
    def _mn(vals):
        """空集 ⇒ None（**不崩**）：无对象可测（如放置态板无走线/无过孔）时按 null 上报。"""
        return round(min(vals) / NM, 4) if vals else None
    return {"min_track_width_mm": _mn([t.GetWidth() for t in tracks]),
            "n_tracks": len(tracks),
            "min_via_diameter_mm": _mn(vd), "n_vias": len(vd),
            "min_via_drill_mm": _mn(vdr),
            "min_via_annular_mm": (_mn([(min(vd) - min(vdr)) / 2.0]) if (vd and vdr) else None),
            "min_hole_drill_mm": _mn(hd), "n_holes": len(hd)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--cell-mm", default="5,10,20")
    ap.add_argument("--bands", type=int, default=3)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    bd = pcbnew.LoadBoard(a.board)
    frame = edge_aabb_nm(bd)
    if frame is None:
        print("[INFRA] no Edge.Cuts", file=sys.stderr)
        return 2
    fps = collect(bd)
    cells = [float(x) for x in a.cell_mm.split(",") if x.strip()]
    res = {"check": "density_and_clearance", "board": os.path.abspath(a.board),
           "board_sha16": sha16(a.board), "n_footprints": len(fps),
           "n_pads": sum(len(f["pads"]) for f in fps), "frame_mm": [round(v / NM, 4) for v in frame],
           "grids": [density(fps, frame, c, m) for c in cells
                     for m in ("absolute_zero", "frame_origin")],
           "band_occupancy": band_occupancy(fps, frame, a.bands),
           "clearance": clearances(fps, frame), "process_min": process_min(bd),
           "note": "测量件：不含 verdict 字段；阈值/口径归监理（登记册 §C J-8）"}
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        json.dump(res, open(a.json, "w"), ensure_ascii=False, indent=1)
    print(f"[density_and_clearance] board={os.path.basename(a.board)} sha16={res['board_sha16']} "
          f"fps={res['n_footprints']} pads={res['n_pads']}")
    for g in res["grids"]:
        print(f"  {g['cell_mm']:g}mm 格[{g['origin_mode']}]：封装峰值 {g['fp_peak_per_cell']} {g['fp_top_cells'][:2]}"
              f" · pad 峰值 {g['pad_peak_per_cell']} · 直方图 {g['fp_hist']}")
    bo = res["band_occupancy"]
    print("  三横带占用: " + " · ".join(f"带{b['band']} {b['pad_coverage_ratio']:.4f}" for b in bo["bands"])
          + f" ⇒ max {bo['max_ratio']:.4f}")
    cl = res["clearance"]
    if cl["min_copper_gap_pair"]:
        print(f"  间距：异网 pad 最小 {cl['min_copper_gap_mm']}mm "
              f"{cl['min_copper_gap_pair']['a']}↔{cl['min_copper_gap_pair']['b']}")
    print(f"        孔-孔 {cl['min_hole_to_hole_edge_mm']}mm（{cl['n_holes']} 孔）· courtyard "
          f"{cl['courtyard']['n_with']} 件 min {cl['courtyard']['min_gap_mm']}mm"
          f"（重叠 {cl['courtyard']['n_overlap_pairs']}）· pad 到边 {cl['min_pad_to_edge_mm']}mm")
    pm = res["process_min"]
    print(f"  工艺实达：线宽 {pm['min_track_width_mm']} · 过孔 Ø{pm['min_via_diameter_mm']}/钻 "
          f"{pm['min_via_drill_mm']} ⇒ 孔环 {pm['min_via_annular_mm']} · 最小孔钻 {pm['min_hole_drill_mm']}mm")
    return 0


if __name__ == "__main__":
    sys.exit(main())
