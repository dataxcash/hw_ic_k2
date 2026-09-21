#!/usr/bin/env python3
"""k2_layout_quality_check_v1 — **K2 布局/可装配/可测试 质量测量器**（#K2-66 §三 阈值表）。

定位（同 #K2-66 §五-2 / CR-74 先例）：
  - **只测量、不判定**（不再新增判据维；判定权归监理）。
  - 输出：人读报告（stdout）+ 机读 JSON（--json-out）。
  - **失败即如实报缺口**；不充绿、不为变绿放宽阈值。

子项（阈出处 = #K2-66 §三）：
  A1 fiducial ≥2（Ø1.0mm · 开窗 2× · 距边 ≥3.35mm）      B1 90° 直角 = 0（强条 R4-1）
  A2 测试点 ≥1/电源轨 + 高速通道 · 周围 2.5mm 无器件     B2 高速线过孔 ≤2/线（R1-5/R5-1）
  A3 极性/1 脚丝印 100%                                   B3 对间 3W ≥0.875mm（R3-2）
  A4 器件轮廓丝印 100%                                    B4 蛇形窗口/对内等长（自证项）
  A5 板卡信息（板名+版本+日期）                           C1 铜平衡 40–60%/层 · 层间差 ≤15–20%
  A6 silk 压铜 = 0                                        C2 安装孔阵列对称/有依据
  A7 courtyard 100% · 无重叠                              C6 阻焊坝 ≥0.10mm
  A8 板框圆角 ≥1–2mm

用法：
  PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 \
      k2/tools/k2_layout_quality_check_v1.py [--board P] [--json-out P]
"""
from __future__ import annotations
import argparse, json, math, re, sys

try:
    import pcbnew  # type: ignore
except Exception as e:  # noqa: BLE001
    sys.stderr.write(f"pcbnew 不可用（须 AppDir python+pcbnew）：{e}\n")
    raise SystemExit(2)

MM = pcbnew.ToMM
IU = 1e6  # 1mm = 1e6 nm


def _xy(v):
    return (MM(v.x), MM(v.y))


def _bbox(box):
    return (MM(box.GetX()), MM(box.GetY()), MM(box.GetRight()), MM(box.GetBottom()))


def _bb_overlap(a, b, tol=0.0):
    return not (a[2] < b[0] - tol or b[2] < a[0] - tol or a[3] < b[1] - tol or b[3] < a[1] - tol)


def _seg_angle_deg(p0, p1):
    return math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0])) % 180.0


POLAR_PREFIX = ("D", "LED", "Q", "U", "J", "K", "BT", "Y")


def analyze(board_path: str) -> dict:
    b = pcbnew.LoadBoard(board_path)
    out: dict = {"board": board_path}

    bbox = _bbox(b.GetBoardEdgesBoundingBox())
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]

    # ---------- footprints 分类 ----------
    feet = list(b.GetFootprints())
    def fp_name(fp):
        try:
            return str(fp.GetFPID().GetLibItemName())
        except Exception:  # noqa: BLE001
            return ""

    fid = [fp for fp in feet if re.search(r"fiducial", fp_name(fp) + str(fp.GetValue()) + fp.GetReference(), re.I)]
    tp = [fp for fp in feet if re.search(r"testpoint|test_point|^TP\d", fp_name(fp) + fp.GetReference(), re.I)]

    # A1 fiducial
    a1 = {"n": len(fid), "items": []}
    edges = [_bbox(d.GetBoundingBox()) for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
    for fp in fid:
        pads = list(fp.Pads())
        dia = pad_mask = dist_edge = None
        if pads:
            s = pads[0].GetSize()
            dia = round(MM(s.x), 3) if abs(MM(s.x) - MM(s.y)) < 1e-6 else [round(MM(s.x), 3), round(MM(s.y), 3)]
            pad_mask = pads[0].GetLayerSet().Contains(pcbnew.F_Mask)
        p = _xy(fp.GetPosition())
        if edges:
            dist_edge = round(min(abs(p[0] - bbox[0]), abs(p[1] - bbox[1]),
                                  abs(bbox[2] - p[0]), abs(bbox[3] - p[1])), 3)
        a1["items"].append({"ref": fp.GetReference(), "dia_mm": dia, "has_mask": bool(pad_mask),
                            "dist_edge_mm": dist_edge, "at": [round(p[0], 2), round(p[1], 2)]})

    # A2 test points
    a2 = {"n": len(tp), "refs": [fp.GetReference() for fp in tp]}

    # A3/A4/A7 丝印 & courtyard 覆盖
    silk_graphic_fp, crtyd_fp, polar_fp = [], [], []
    for fp in feet:
        gm = list(fp.GraphicalItems())
        has_silk_g = any(g.GetLayer() == pcbnew.F_SilkS for g in gm)
        has_crtyd = any(g.GetLayer() == pcbnew.F_CrtYd for g in gm)
        if has_silk_g:
            silk_graphic_fp.append(fp.GetReference())
        if has_crtyd:
            crtyd_fp.append(fp.GetReference())
        if fp.GetReference().startswith(POLAR_PREFIX) or re.search(r"polar|diode|led|e-?cap", fp_name(fp), re.I):
            polar_fp.append(fp)
    # A3: 极性件中是否有 1 脚/极性丝印（丝印图元，或非 Reference 的丝印文本）
    a3_items = []
    for fp in polar_fp:
        gm = list(fp.GraphicalItems())
        g_silk = [g for g in gm if g.GetLayer() == pcbnew.F_SilkS]
        ref_txt = fp.GetReference()
        t_silk = [t for t in (fp.Reference(), fp.Value())
                  if t.GetLayer() == pcbnew.F_SilkS and t.GetText() != ref_txt]
        a3_items.append({"ref": fp.GetReference(), "has_silk_marker": bool(g_silk) or bool(t_silk)})
    a3 = {"polar_total": len(a3_items), "with_marker": sum(1 for x in a3_items if x["has_silk_marker"]),
          "missing": [x["ref"] for x in a3_items if not x["has_silk_marker"]], "items": a3_items}
    a4 = {"covered": len(silk_graphic_fp), "total": len(feet),
          "missing_n": len(feet) - len(silk_graphic_fp)}
    a7 = {"with_courtyard": len(crtyd_fp), "total": len(feet),
          "missing_n": len(feet) - len(crtyd_fp)}

    # A5 板卡信息
    title = b.GetTitleBlock()
    tinfo = {}
    for k in ("GetTitle", "GetDate", "GetRevision", "GetCompany"):
        try:
            tinfo[k] = getattr(title, k)()
        except Exception:  # noqa: BLE001
            tinfo[k] = ""
    gr_silk_text = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.F_SilkS and d.GetClass().startswith("PCB_TEXT")]
    a5 = {"title_block": tinfo, "board_silk_text_n": len(gr_silk_text),
          "texts": [d.GetText() for d in gr_silk_text][:20]}

    # A6 silk 压铜（丝印图元/文本 bbox 与 焊盘/过孔/走线 bbox 相交）
    cu_boxes = []
    for fp in feet:
        for pd in fp.Pads():
            cu_boxes.append((("pad", fp.GetReference(), pd.GetNumber()), _bbox(pd.GetBoundingBox())))
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA) or t.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu):
            cu_boxes.append((("track" if not isinstance(t, pcbnew.PCB_VIA) else "via", t.GetNetname(), ""),
                             _bbox(t.GetBoundingBox())))
    silk_items = []
    for fp in feet:
        for g in fp.GraphicalItems():
            if g.GetLayer() == pcbnew.F_SilkS:
                silk_items.append(("fp.graphic", fp.GetReference(), g.GetClass(), _bbox(g.GetBoundingBox())))
        for t in (fp.Reference(), fp.Value()):
            if t.GetLayer() == pcbnew.F_SilkS:
                silk_items.append(("fp.text", fp.GetReference(), "", _bbox(t.GetBoundingBox())))
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.F_SilkS:
            silk_items.append(("board.graphic", "", d.GetClass(), _bbox(d.GetBoundingBox())))
    def _hits(kinds):
        n = 0
        for kind, ref, cls, sb in silk_items:
            for (ckind, cref, cnum), cb in cu_boxes:
                if ckind in kinds and _bb_overlap(sb, cb, tol=-0.02):  # 0.02mm 视觉容差
                    n += 1; break
        return n
    a6 = {"n_silk_items": len(silk_items),
          "n_silk_over_pad": _hits(("pad",)),
          "n_silk_over_copper": _hits(("pad", "track", "via"))}

    # A8 板框圆角
    ec = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
    arcs = [d for d in ec if d.GetClass() == "PCB_SHAPE" and d.GetShape() == pcbnew.SHAPE_T_ARC]
    a8 = {"edge_items": len(ec), "arcs": len(arcs)}

    # ---------- B1 90° 拐角 ----------
    from collections import defaultdict
    seg_by = defaultdict(list)
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA) or isinstance(t, pcbnew.PCB_ARC):
            continue
        seg_by[(t.GetNetname(), t.GetLayer())].append((_xy(t.GetStart()), _xy(t.GetEnd())))
    def key(p):
        return (round(p[0], 4), round(p[1], 4))
    right_angles = 0
    corners = 0
    for (net, layer), segs in seg_by.items():
        ends = defaultdict(list)
        for i, (p0, p1) in enumerate(segs):
            ends[key(p0)].append(i); ends[key(p1)].append(i)
        for pt, idxs in ends.items():
            if len(idxs) != 2:
                continue
            corners += 1
            i, j = idxs
            def other(seg_i, pt):
                p0, p1 = segs[seg_i]
                return p1 if key(p0) == pt else p0 if key(p1) == pt else None
            oi, oj = other(i, pt), other(j, pt)
            if oi is None or oj is None:
                continue
            a1v = _seg_angle_deg(pt, oi); a2v = _seg_angle_deg(pt, oj)
            d = abs(a1v - a2v) % 180.0
            ang = 180.0 - d if d > 90.0 else d
            if abs(ang - 90.0) < 0.5:
                right_angles += 1
    b1 = {"corners": corners, "right_angle_90": right_angles,
          "pct": round(100.0 * right_angles / corners, 1) if corners else 0.0}

    # ---------- B2 高速线过孔 ----------
    via_by_net = defaultdict(int)
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            via_by_net[t.GetNetname()] += 1
    hs = {n: c for n, c in via_by_net.items() if n and re.search(r"PCIE_(DN|UP)_OUT|PCIE_REFCLK", n)}
    all_over2 = {n: c for n, c in via_by_net.items() if c > 2 and n and n != "GND"}
    b2 = {"high_speed_nets": len(hs), "max_via": max(hs.values()) if hs else 0,
          "hs_hist": {str(k): sum(1 for c in hs.values() if c == k) for k in sorted(set(hs.values()))},
          "n_nets_over2_excl_gnd": len(all_over2),
          "all_over2_hist": {str(k): sum(1 for c in all_over2.values() if c == k) for k in sorted(set(all_over2.values()))},
          "max_via_any": max(via_by_net.values()) if via_by_net else 0}

    # ---------- C1 铜平衡 ----------
    board_area = bw * bh
    layer_cu, layer_detail = {}, {}
    for ln, lname in ((pcbnew.F_Cu, "F.Cu"), (pcbnew.B_Cu, "B.Cu")):
        za = ta = pa = 0.0
        for z in b.Zones():
            if z.GetLayer() == ln:
                za += z.GetFilledArea() / 1e12
        for t in b.GetTracks():
            if isinstance(t, pcbnew.PCB_VIA) or t.GetLayer() != ln:
                continue
            ta += MM(t.GetLength()) * MM(t.GetWidth())
        for fp in feet:
            for pd in fp.Pads():
                if pd.IsOnLayer(ln):
                    sz = pd.GetSize()
                    pa += MM(sz.x) * MM(sz.y)
        layer_cu[lname] = round(100.0 * (za + ta + pa) / board_area, 2) if board_area else 0.0
        layer_detail[lname] = {"zone_mm2": round(za, 1), "track_mm2": round(ta, 1),
                               "pad_mm2": round(pa, 1), "board_mm2": round(board_area, 1),
                               "zones_filled": sum(1 for z in b.Zones() if z.GetLayer() == ln and z.IsFilled())}
    c1 = {"per_layer_pct": layer_cu, "board_mm": [round(bw, 2), round(bh, 2)], "detail": layer_detail}

    # ---------- C2 安装孔 ----------
    mh = [fp for fp in feet if re.search(r"mountinghole|mounting_hole|^H\d", fp_name(fp) + fp.GetReference(), re.I)]
    c2 = {"n": len(mh), "at": [[fp.GetReference(), [round(_xy(fp.GetPosition())[0], 2), round(_xy(fp.GetPosition())[1], 2)]] for fp in mh]}

    # ---------- C6 阻焊坝 ----------
    ds = b.GetDesignSettings()
    c6 = {"solder_mask_min_width_mm": round(MM(ds.m_SolderMaskMinWidth), 4) if hasattr(ds, "m_SolderMaskMinWidth") else None}

    out.update({"A1_fiducial": a1, "A2_testpoint": a2, "A3_polar_silk": a3, "A4_outline_silk": a4,
                "A5_board_info": a5, "A6_silk_over_copper": a6, "A7_courtyard": a7, "A8_edge_arcs": a8,
                "B1_right_angles": b1, "B2_hs_vias": b2, "C1_copper_balance": c1, "C2_mounting_holes": c2,
                "C6_mask": c6, "board_bbox_mm": [round(v, 3) for v in bbox]})
    return out


def render(r: dict) -> str:
    L = []
    L.append("== K2 布局/可装配/可测试 质量测量（**只测量 · 不判定** · 判定权归监理）==")
    L.append(f"板: {r['board']}  bbox(mm): {r['board_bbox_mm']}")
    a1 = r["A1_fiducial"]; L.append(f"[A1] fiducial: {a1['n']} 个" + ("" if a1['n'] else "  ❌ 缺（SMT 无法对位）"))
    a2 = r["A2_testpoint"]; L.append(f"[A2] 测试点: {a2['n']} 个" + ("" if a2['n'] else "  ❌ 缺（V5/V6 不可测）"))
    a3 = r["A3_polar_silk"]; L.append(f"[A3] 极性/1脚丝印: {a3['with_marker']}/{a3['polar_total']}  缺 {len(a3['missing'])}")
    a4 = r["A4_outline_silk"]; L.append(f"[A4] 器件轮廓丝印: {a4['covered']}/{a4['total']}（缺 {a4['missing_n']}）")
    a5 = r["A5_board_info"]; L.append(f"[A5] 板卡信息: title={a5['title_block']} board_silk_text={a5['board_silk_text_n']}")
    a6 = r["A6_silk_over_copper"]; L.append(f"[A6] silk 压焊盘: {a6['n_silk_over_pad']} 处 · 压铜(含线): {a6['n_silk_over_copper']} 处 / 丝印件 {a6['n_silk_items']}")
    a7 = r["A7_courtyard"]; L.append(f"[A7] courtyard: {a7['with_courtyard']}/{a7['total']}（缺 {a7['missing_n']}）")
    a8 = r["A8_edge_arcs"]; L.append(f"[A8] 板框圆角: arcs={a8['arcs']} / edge items={a8['edge_items']}")
    b1 = r["B1_right_angles"]; L.append(f"[B1] 90° 直角: {b1['right_angle_90']} 处（拐角 {b1['corners']} · {b1['pct']}%）")
    b2 = r["B2_hs_vias"]; L.append(f"[B2] 过孔: PCIE 网 {b2['high_speed_nets']}（hist {b2['hs_hist']}）· >2/线(非GND) {b2['n_nets_over2_excl_gnd']} 网 · 最大 {b2['max_via_any']}")
    c1 = r["C1_copper_balance"]; L.append(f"[C1] 铜平衡: {c1['per_layer_pct']}  detail {c1['detail']}")
    c2 = r["C2_mounting_holes"]; L.append(f"[C2] 安装孔: {c2['n']} 个 {[x[0] for x in c2['at']]}")
    L.append(f"[C6] 阻焊坝 min width: {r['C6_mask']['solder_mask_min_width_mm']} mm")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="K2 布局/可装配/可测试 质量测量器（只测量 · 判定归监理）")
    ap.add_argument("--board", default="k2/hw/k2_v4_8L.l8.kicad_pcb")
    ap.add_argument("--json-out")
    a = ap.parse_args(argv)
    r = analyze(a.board)
    print(render(r))
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as fh:
            json.dump(r, fh, ensure_ascii=False, indent=1)
        print(f"\n[json] {a.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
