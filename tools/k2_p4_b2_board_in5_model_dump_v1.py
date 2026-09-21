#!/usr/bin/env python3
"""K2 · B2 —— **全板 In5 模型 dump**（pcbnew · 只读）。

用途：为 `k2_p4_b2_in5_corridor_structure_census_v1.py` 提供**可复现**输入
（替代 /tmp 之 `model_crop.json`；四源/受审板逐字节不动，仅读）。
须以 pcbnew 解释器运行（`AppDir/usr/bin/python3.11` + `PYTHONPATH=AppDir/shared/lib/...`）。
输出 schema 与既有 `model_crop.json` 同构（segs/ruleareas/pads/vias/holes/layers/bbox/design/board）。
"""
import pcbnew, json, sys
MM = pcbnew.ToMM
board, out = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(board)
name = {n.GetNetCode(): n.GetNetname() for n in b.GetNetInfo().NetsByNetcode().values()}
LAYERS = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]
lid = {L: b.GetLayerID(L) for L in LAYERS}
segs = {L: [] for L in LAYERS}; pads = []; vias = []; holes = []
for t in b.GetTracks():
    nm = name.get(t.GetNetCode(), "")
    if t.GetClass() == "PCB_VIA":
        v = t.Cast()
        x, y = MM(v.GetPosition().x), MM(v.GetPosition().y)
        top, bot = int(v.TopLayer()), int(v.BottomLayer())
        sp = set(v.GetLayerSet().Seq())
        vias.append({"x": x, "y": y, "net": nm, "r": MM(v.GetWidth(pcbnew.F_Cu)) / 2, "drill": MM(v.GetDrillValue()) / 2,
                     "top": b.GetLayerName(top), "bot": b.GetLayerName(bot),
                     "layers": [L for L in LAYERS if lid[L] in sp]})
        holes.append({"x": x, "y": y, "r": MM(v.GetDrillValue()) / 2, "net": nm, "kind": "via"})
        continue
    L = b.GetLayerName(t.GetLayer())
    if L not in segs:
        continue
    segs[L].append([MM(t.GetStart().x), MM(t.GetStart().y), MM(t.GetEnd().x), MM(t.GetEnd().y), MM(t.GetWidth()) / 2, nm])
for fp in b.GetFootprints():
    for p in fp.Pads():
        nm = p.GetNetname(); pth = p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
        bb = p.GetBoundingBox(); sp = set(p.GetLayerSet().Seq())
        rec = {"ref": fp.GetReference(), "num": p.GetNumber(), "net": nm,
               "box": [MM(bb.GetX()), MM(bb.GetY()), MM(bb.GetRight()), MM(bb.GetBottom())],
               "cx": MM(p.GetPosition().x), "cy": MM(p.GetPosition().y),
               "pth": pth, "layers": [L for L in LAYERS if lid[L] in sp],
               "drill": (MM(p.GetDrillSize().x) / 2 if pth else None),
               "sx": MM(p.GetSize().x), "sy": MM(p.GetSize().y)}
        pads.append(rec)
        if pth:
            holes.append({"x": rec["cx"], "y": rec["cy"], "r": rec["drill"], "net": nm, "kind": "pad",
                          "ref": fp.GetReference() + "." + p.GetNumber()})
ruleareas = []
for z in b.Zones():
    try:
        if not z.GetIsRuleArea():
            continue
    except Exception:
        continue
    o = z.Outline(); polys = []
    for i in range(o.OutlineCount()):
        ch = o.Outline(i)
        polys.append([[MM(ch.CPoint(j).x), MM(ch.CPoint(j).y)] for j in range(ch.PointCount())])
    ruleareas.append({"polys": polys, "no_vias": bool(z.GetDoNotAllowVias()), "no_tracks": bool(z.GetDoNotAllowTracks()),
                      "layers": [b.GetLayerName(l) for l in range(pcbnew.PCB_LAYER_ID_COUNT) if z.IsOnLayer(l)][:12]})
bb = b.GetBoardEdgesBoundingBox()
design = {}
try:
    ds = b.GetDesignSettings()
    for k, g in (("copper_edge_clearance", "m_CopperEdgeClearance"),
                 ("hole_clearance", "m_HoleClearance"),
                 ("hole_to_hole", "m_HoleToHoleMin")):
        try:
            design[k] = MM(getattr(ds, g))
        except Exception:
            pass
except Exception:
    pass
json.dump({"segs": segs, "ruleareas": ruleareas, "pads": pads, "vias": vias, "holes": holes, "layers": LAYERS,
           "bbox": [MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())],
           "design": design, "board": board}, open(out, "w"), ensure_ascii=False)
print("wrote", out, "segs(In5)=%d vias=%d pads=%d" % (len(segs["In5.Cu"]), len(vias), len(pads)))
