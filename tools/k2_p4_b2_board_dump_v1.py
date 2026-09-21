#!/usr/bin/env python3
"""K2 · B2 —— 板件几何 **只读** 导出器 v1（pcbnew · 供容量/布线分析消费）。

用途：把 .kicad_pcb 的关键几何（各层走线段 / 过孔 span / 焊盘 bbox / 钻孔 / 规则区）
导出为确定性 JSON，供**系统 python3 + numpy/scipy** 的分析器消费（与 pcbnew 环境解耦）。

用法（解释器 = `AppDir/usr/bin/python3.11`，**不是** `AppDir/bin/python3.11`）：
  PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/usr/bin/python3.11 \
    k2/tools/k2_p4_b2_board_dump_v1.py --board <pcb> --out <json>

判据/证据口径：本器只导出原始几何，不含任何阈值判断。
"""
from __future__ import annotations
import argparse, json

import pcbnew

MM = pcbnew.ToMM
LAYERS = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    b = pcbnew.LoadBoard(a.board)
    name = {n.GetNetCode(): n.GetNetname() for n in b.GetNetInfo().NetsByNetcode().values()}
    lid = {L: b.GetLayerID(L) for L in LAYERS}
    segs = {L: [] for L in LAYERS}
    pads, vias, holes = [], [], []
    for t in b.GetTracks():
        nm = name.get(t.GetNetCode(), "")
        if t.GetClass() == "PCB_VIA":
            v = t.Cast()
            sp = set(v.GetLayerSet().Seq())
            vias.append({"x": MM(v.GetPosition().x), "y": MM(v.GetPosition().y), "net": nm,
                         "r": MM(v.GetWidth()) / 2, "drill": MM(v.GetDrillValue()) / 2,
                         "top": b.GetLayerName(int(v.TopLayer())), "bot": b.GetLayerName(int(v.BottomLayer())),
                         "layers": [L for L in LAYERS if lid[L] in sp]})
            holes.append({"x": MM(v.GetPosition().x), "y": MM(v.GetPosition().y),
                          "r": MM(v.GetDrillValue()) / 2, "net": nm, "kind": "via"})
            continue
        L = b.GetLayerName(int(t.GetLayer()))
        if L not in segs:
            continue
        segs[L].append([MM(t.GetStart().x), MM(t.GetStart().y), MM(t.GetEnd().x), MM(t.GetEnd().y),
                        MM(t.GetWidth()) / 2, nm])
    for fp in b.GetFootprints():
        for p in fp.Pads():
            nm = p.GetNetname()
            pth = p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
            bb = p.GetBoundingBox()
            sp = set(p.GetLayerSet().Seq())
            rec = {"ref": fp.GetReference(), "num": p.GetNumber(), "net": nm,
                   "box": [MM(bb.GetX()), MM(bb.GetY()), MM(bb.GetRight()), MM(bb.GetBottom())],
                   "cx": MM(p.GetPosition().x), "cy": MM(p.GetPosition().y),
                   "pth": pth, "layers": [L for L in LAYERS if lid[L] in sp],
                   "drill": (MM(p.GetDrillSize().x) / 2 if pth else None),
                   "shape": int(p.GetShape()), "sx": MM(p.GetSize().x), "sy": MM(p.GetSize().y)}
            pads.append(rec)
            if pth:
                holes.append({"x": rec["cx"], "y": rec["cy"], "r": rec["drill"], "net": nm,
                              "kind": "pad", "ref": fp.GetReference() + "." + p.GetNumber()})
    ruleareas = []
    for z in b.Zones():
        try:
            if not z.GetIsRuleArea():
                continue
        except Exception:
            continue
        o = z.Outline()
        polys = []
        for i in range(o.OutlineCount()):
            ch = o.Outline(i)
            polys.append([[MM(ch.CPoint(j).x), MM(ch.CPoint(j).y)] for j in range(ch.PointCount())])
        ruleareas.append({"polys": polys, "no_vias": bool(z.GetDoNotAllowVias()),
                          "no_tracks": bool(z.GetDoNotAllowTracks()),
                          "layers": [b.GetLayerName(l) for l in range(pcbnew.PCB_LAYER_ID_COUNT) if z.IsOnLayer(l)][:12]})
    bb = b.GetBoardEdgesBoundingBox()
    ds = b.GetDesignSettings()
    json.dump({"segs": segs, "ruleareas": ruleareas, "pads": pads, "vias": vias, "holes": holes,
               "layers": LAYERS,
               "bbox": [MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())],
               "design": {"hole_clearance": MM(ds.m_HoleClearance), "hole_to_hole": MM(ds.m_HoleToHoleMin),
                          "mask_exp": MM(ds.m_SolderMaskExpansion), "mask_min_width": MM(ds.m_SolderMaskMinWidth),
                          "copper_edge_clearance": MM(ds.m_CopperEdgeClearance)},
               "board": a.board}, open(a.out, "w"), ensure_ascii=False, indent=1)
    print("segs", {k: len(v) for k, v in segs.items()}, "pads", len(pads), "vias", len(vias))


if __name__ == "__main__":
    main()
