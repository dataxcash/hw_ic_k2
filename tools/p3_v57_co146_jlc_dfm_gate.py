#!/usr/bin/env python3
"""CO-146 A4 — DFM 对照嘉立创(JLC) 8 层能力（监理指令 #10 要求动作 4）。

性质：**只读机判**（不改板/图纸/SPEC/冻结四源）。判据来源 = JLC 公布能力页
（`https://jlcpcb.com/capabilities/pcb-capabilities`，2026-09-12 抓取；逐条引用见
`m13_v57_co146_jlc8_capability.json`）。测量 = 交付板实几何 + 两次 kicad-cli DRC：
  (a) as-designed（L4 board + l4 dru）
  (b) JLC-limit 变体（dru 逃逸域 0.075→0.090；板规地板改 JLC 下限）⇒ 违规即真 DFM 缺口

产出：
  m13_v57_co146_jlc8_capability.json   能力表出处 + 逐条引用 + 抓取件 sha
  m13_v57_co146_jlc_dfm_gate.json      逐项判定（实测 vs JLC 限）
  m13_v57_co146_jlc_dfm_gate.md        卡（人读）
牙齿：① 空侧对照（把 JLC 轨道宽度限设为 0.5mm 必须触发 PASS→FAIL）；② 过孔类型项必须判 FAIL（本板 220 非通孔）。
"""
from __future__ import annotations
import hashlib, json, re, shutil, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path

ROOT = Path("/home/fila/jqdDev_2025/ic_hw")
K2 = ROOT / "k2"
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2DIR = K2 / "pm_gate/artifacts/k2_v4/L2"
CLI = ROOT / "AppDir/bin/kicad-cli"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
PRO = K2 / "k2_v4_8L.l4.kicad_pro"
DRU = K2 / "k2_v4_8L.l4.kicad_dru"
JLC_URL = "https://jlcpcb.com/capabilities/pcb-capabilities"
JLC_FETCH_DATE = "2026-09-12"

# JLC 公布能力（1oz 外层 / 多层 FR-4；逐条与引用原文对应，见 capability json）
JLC8 = {
    "layer_count": {"min": 1, "max": 32, "quote": "Layer count 1-32 Layers"},
    "impedance_control_layers": {"value": "4/6/8/10/12/.../32", "quote": "Controlled Impedance 4/6/8/10/12/14/16/18/20/.../32 layers"},
    "impedance_tolerance_pct": {"value": 10, "quote": "Impedance Tolerance ±10%"},
    "board_max_mm": {"w": 656.0, "h": 586.0, "quote": "FR4(6-layer and above): 656 × 586 mm"},
    "board_min_mm": {"w": 3.0, "h": 3.0, "quote": "Minimum Dimensions FR4/Rogers/PTFE: 3 × 3 mm"},
    "thickness_mm": {"value": 1.6, "range": "0.4 – 4.5", "tol_pct": 10,
                     "quote": "Thickness 0.4 – 4.5 mm ... 1.6 ... Thickness Tolerance (Thickness≥1.0mm) ± 10%"},
    "outer_copper_oz": {"value": 1.0, "allowed": "1 oz / 2 oz", "quote": "Finished Outer Layer Copper Multi-layer: 1 oz / 2 oz"},
    "inner_copper_oz": {"value": 0.5, "allowed": "0.5 oz / 1 oz / 2 oz", "quote": "Finished Inner Layer Copper 0.5 oz / 1 oz / 2 oz ... 0.5oz by default"},
    "min_track_width_mm": {"value": 0.09, "quote": "Min. track width and spacing (1 oz) Multilayer: 0.09 / 0.09 mm (3.5 / 3.5 mil). 3 mil is acceptable in BGA fan-outs."},
    "min_track_spacing_mm": {"value": 0.09, "quote": "同上（3.5 mil）；BGA fan-out 可 3 mil (0.0762mm)"},
    "min_via_hole_mm": {"value": 0.15, "preferred": 0.2, "quote": "Min. Via hole size/diameter 0.15mm / 0.25mm ... ② Preferred Min. Via hole size: 0.2mm"},
    "min_via_diameter_mm": {"value": 0.25, "quote": "Min. Via hole size/diameter 0.15mm / 0.25mm"},
    "via_annular_note": {"value": 0.15, "quote": "① Via diameter should be 0.1mm(0.15mm preferred) larger than Via hole size"},
    "via_hole_to_hole_mm": {"value": 0.2, "quote": "Via Hole-to-Hole Spacing 0.2mm"},
    "pad_hole_to_hole_mm": {"value": 0.45, "quote": "Pad Hole-to-Hole Spacing 0.45mm"},
    "min_npth_mm": {"value": 0.5, "quote": "Min. Non-plated holes 0.50mm"},
    "min_plated_slot_mm": {"value": 0.35, "quote": "Min. Plated Slots Width ... Multi-layer: 0.35mm"},
    "copper_edge_clearance_mm": {"value": 0.2, "quote": "Copper clearance from routed board edges: ≧0.2 mm"},
    "solder_mask_to_copper_mm": {"value": 0.09, "quote": "Keep at least 0.09 mm clearance between soldermask openings and neighboring traces"},
    "solder_mask_bridge_mm": {"value": 0.10, "quote": "Soldermask bridge 0.10mm 1oz: Min. pad spacing: 0.10 mm"},
    "surface_finish": {"value": "ENIG", "quote": "Surface Finish HASL ... FR-4/HDI boards with 6 or more layers ... do not support HASL"},
    "er_table": {"2116": 4.16, "3313": 4.1, "7628": 4.4,
                 "quote": "FR-4 Dielectric Constants ... 7628 Prepreg 4.4 3313 Perpreg 4.1 2116 Perpreg 4.16"},
    "blind_buried": {"supported": False,
                     "quote": "Blind/Buried Vias Not supported Currently we don't support Blind/Buried Vias, only make through holes."},
    "blind_buried_faq": {"note": "FAQ：blind/buried、HDI(laser vias) 属 advanced options，须 DFM review，成本/交期上升",
                         "quote": "Advanced options such as blind/buried vias, HDI (laser vias) ... require DFM review and may increase both cost and production time."},
}


def sha16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def mm(v) -> float:
    import pcbnew
    return round(pcbnew.ToMM(v), 4)


def measure_as_built() -> dict:
    import pcbnew
    b = pcbnew.LoadBoard(str(BOARD))
    tracks, vias = [], []
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            vias.append(t)
        else:
            tracks.append(t)
    widths = Counter(round(pcbnew.ToMM(t.GetWidth()), 4) for t in tracks)
    via_pairs = Counter()
    for v in vias:
        top, bot = b.GetLayerName(v.TopLayer()), b.GetLayerName(v.BottomLayer())
        through = (v.GetViaType() == pcbnew.VIATYPE_THROUGH) and top == "F.Cu" and bot == "B.Cu"
        via_pairs[(top + "->" + bot, "THROUGH" if through else "BLIND_BURIED")] += 1
    vdrills = Counter(mm(v.GetDrill()) for v in vias)
    vdias = Counter(mm(v.GetWidth(pcbnew.F_Cu)) for v in vias)
    # via hole-to-hole edge clearance (min over all via pairs)
    pts = sorted((v.GetPosition().x, v.GetPosition().y, v.GetDrill()) for v in vias)
    h2h = None
    for i, (x1, y1, d1) in enumerate(pts):
        for x2, y2, d2 in pts[i + 1:]:
            dx = abs(x2 - x1)
            if dx > 1.0:
                break
            c = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            g = pcbnew.ToMM(c - (d1 + d2) / 2)
            h2h = g if h2h is None else min(h2h, g)
    # pads: PTH / NPTH holes
    pth, npth, npth_d = Counter(), Counter(), []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            d = p.GetDrillSize()
            if d.x <= 0:
                continue
            key = mm(d.x)
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                npth[key] += 1
                npth_d.append(key)
            else:
                pth[key] += 1
    bb = b.GetBoardEdgesBoundingBox()
    return {
        "board": BOARD.name, "board_sha16": sha16(BOARD),
        "n_copper_layers": b.GetCopperLayerCount(),
        "copper_layers": [b.GetLayerName(i) for i in b.GetEnabledLayers().CuStack()],
        "board_size_mm": [round(pcbnew.ToMM(bb.GetWidth()), 3), round(pcbnew.ToMM(bb.GetHeight()), 3)],
        "n_tracks": len(tracks), "n_vias": len(vias),
        "min_track_width_mm": min(widths), "track_width_hist": {str(k): v for k, v in sorted(widths.items())},
        "min_track_width_by_layer": _min_w_by_layer(b, tracks),
        "via_drill_hist_mm": {str(k): v for k, v in sorted(vdrills.items())},
        "via_diameter_hist_mm": {str(k): v for k, v in sorted(vdias.items())},
        "min_via_drill_mm": min(vdrills), "min_via_diameter_mm": min(vdias),
        "min_via_annular_mm": round((min(vdias) - min(vdrills)) / 2, 4),
        "via_type_census": {f"{a}|{t}": c for (a, t), c in sorted(via_pairs.items())},
        "n_non_through_vias": sum(c for (a, t), c in via_pairs.items() if t != "THROUGH"),
        "min_via_hole_to_hole_mm": None if h2h is None else round(h2h, 4),
        "pth_drill_hist_mm": {str(k): v for k, v in sorted(pth.items())},
        "min_pth_drill_mm": min(pth) if pth else None,
        "npth_drill_hist_mm": {str(k): v for k, v in sorted(npth.items())},
        "min_npth_drill_mm": min(npth) if npth else None,
        "n_zones": len(list(b.Zones())),
    }


def _min_w_by_layer(b, tracks) -> dict:
    import pcbnew
    d = {}
    for t in tracks:
        ln = b.GetLayerName(t.GetLayer())
        w = round(pcbnew.ToMM(t.GetWidth()), 4)
        d[ln] = min(d.get(ln, w), w)
    return {k: d[k] for k in sorted(d)}


def _run_drc(board_text: str, pro_text: str, dru_text: str | None) -> dict:
    with tempfile.TemporaryDirectory() as td:
        b = Path(td) / "probe.kicad_pcb"
        b.write_text(board_text)
        b.with_suffix(".kicad_pro").write_text(pro_text)
        if dru_text is not None:
            b.with_suffix(".kicad_dru").write_text(dru_text)
        out = Path(td) / "d.json"
        subprocess.run([str(CLI), "pcb", "drc", "--format", "json", "--severity-all",
                        "--refill-zones", "--output", str(out), str(b)],
                       capture_output=True, text=True, timeout=1800)
        d = json.loads(out.read_text())
        return {"n": len(d["violations"]),
                "by_type": dict(sorted(Counter(v["type"] for v in d["violations"]).items())),
                "unconnected": len(d.get("unconnected_items", [])),
                "samples": [{"type": v["type"], "description": v["description"],
                             "where": [i.get("description") for i in v.get("items", [])]}
                            for v in d["violations"] if v["type"] in
                            ("clearance", "track_width", "via_diameter", "annular_width",
                             "hole_to_hole", "hole_clearance", "copper_edge_clearance",
                             "solder_mask_bridge", "shorting_items")][:12]}


def jlc_limit_drc(board_text: str, pro_text: str, dru_text: str,
                  jlc: dict | None = None) -> dict:
    """把判据地板换成 JLC 下限后重跑 DRC：违规 = 真 DFM 缺口（不是放宽板规）。"""
    j = jlc or JLC8
    pro = json.loads(pro_text)
    r = pro["board"]["design_settings"]["rules"]
    r["min_clearance"] = j["min_track_spacing_mm"]["value"]
    r["min_track_width"] = j["min_track_width_mm"]["value"]
    r["min_via_diameter"] = j["min_via_diameter_mm"]["value"]
    r["min_via_annular_width"] = round(j["via_annular_note"]["value"] / 2, 4)
    r["min_hole_to_hole"] = j["via_hole_to_hole_mm"]["value"]
    r["min_copper_edge_clearance"] = j["copper_edge_clearance_mm"]["value"]
    r["solder_mask_to_copper_clearance"] = j["solder_mask_to_copper_mm"]["value"]
    dru = dru_text.replace("(min 0.075mm)", f"(min {j['min_track_spacing_mm']['value']:.3f}mm)")
    return _run_drc(board_text, json.dumps(pro, indent=2), dru)


def _items(m: dict, asd: dict, jlcrun: dict) -> list[dict]:
    j = JLC8
    out = []

    def add(item, limit, measured, ok, note=""):
        out.append({"item": item, "jlc_limit": limit, "measured": measured,
                    "verdict": "PASS" if ok else "FAIL", "note": note})

    size = m["board_size_mm"]
    add("板尺寸", f"≤{j['board_max_mm']['w']}×{j['board_max_mm']['h']}mm 且 ≥3×3mm",
        f"{size[0]}×{size[1]}mm", size[0] <= j["board_max_mm"]["w"] and size[1] <= j["board_max_mm"]["h"]
        and size[0] >= 3.0 and size[1] >= 3.0)
    add("层数", f"{j['layer_count']['min']}–{j['layer_count']['max']} 层（阻抗控制支持 4/6/8/…）",
        f"{m['n_copper_layers']} 层", m["n_copper_layers"] in (4, 6, 8, 10, 12, 14, 16, 18, 20, 32))
    add("外层铜厚", j["outer_copper_oz"]["allowed"], "1 oz（SPEC stackup / 监理定值）", True, "声明值=监理定值")
    add("内层铜厚", j["inner_copper_oz"]["allowed"], "0.5 oz（SPEC stackup / JLC 默认）", True, "声明值=监理定值")
    add("成品板厚", f"{j['thickness_mm']['value']}mm ±{j['thickness_mm']['tol_pct']}%", "1.6mm（JLC08161H）", True, "声明值")
    add("最小线宽", f"≥{j['min_track_width_mm']['value']}mm (3.5mil)",
        f"{m['min_track_width_mm']}mm", m["min_track_width_mm"] >= j["min_track_width_mm"]["value"])
    add("最小线距（域外，netclass 0.1/0.175/0.2 全 ≥3.5mil）", f"≥{j['min_track_spacing_mm']['value']}mm",
        f"JLC 限 DRC clearance 违规 = {jlcrun['by_type'].get('clearance', 0)}",
        jlcrun["by_type"].get("clearance", 0) == 0, "含逃逸域按 0.09mm 收紧后重跑")
    add("最小过孔孔壁", f"≥{j['min_via_hole_mm']['value']}mm（建议 ≥{j['min_via_hole_mm']['preferred']}mm）",
        f"{m['min_via_drill_mm']}mm", m["min_via_drill_mm"] >= j["min_via_hole_mm"]["preferred"])
    add("最小过孔盘径", f"≥{j['min_via_diameter_mm']['value']}mm", f"{m['min_via_diameter_mm']}mm",
        m["min_via_diameter_mm"] >= j["min_via_diameter_mm"]["value"])
    add("过孔环宽（单边）", f"盘径 ≥ 孔径+{j['via_annular_note']['value']}mm（⇒ 单边 ≥0.075mm）",
        f"{m['min_via_annular_mm']}mm",
        m["min_via_diameter_mm"] - m["min_via_drill_mm"] >= j["via_annular_note"]["value"] - 1e-9)
    add("过孔孔到孔", f"≥{j['via_hole_to_hole_mm']['value']}mm", f"{m['min_via_hole_to_hole_mm']}mm",
        m["min_via_hole_to_hole_mm"] >= j["via_hole_to_hole_mm"]["value"])
    add("NPTH 最小孔径", f"≥{j['min_npth_mm']['value']}mm",
        f"{m['min_npth_drill_mm']}mm（{list(m['npth_drill_hist_mm'])}）",
        m["min_npth_drill_mm"] is None or m["min_npth_drill_mm"] >= j["min_npth_mm"]["value"])
    add("铜到板边", f"≥{j['copper_edge_clearance_mm']['value']}mm",
        f"板规 min_copper_edge_clearance=0.30mm；JLC 限 DRC copper_edge_clearance 违规 = "
        f"{jlcrun['by_type'].get('copper_edge_clearance', 0)}",
        jlcrun["by_type"].get("copper_edge_clearance", 0) == 0)
    add("阻焊桥 / 阻焊-铜净距", f"桥 ≥{j['solder_mask_bridge_mm']['value']}mm；开窗到邻近铜 ≥{j['solder_mask_to_copper_mm']['value']}mm",
        f"JLC 限 DRC solder_mask_bridge 违规 = {jlcrun['by_type'].get('solder_mask_bridge', 0)}",
        jlcrun["by_type"].get("solder_mask_bridge", 0) == 0)
    add("表面处理", "6 层及以上不支持 HASL ⇒ 须 ENIG", "沉金 ENIG", True, "监理定值一致")
    add("阻抗控制", f"支持层数 {j['impedance_control_layers']['value']}，公差 ±{j['impedance_tolerance_pct']['value']}%",
        "8 层 + 85Ω±10%（见 CO-146 阻抗表）", True, "终判 = JLC 阻抗控制服务")
    nt = m["n_non_through_vias"]
    add("**过孔类型（盲/埋孔）**", "**不支持盲/埋孔（仅通孔）**",
        f"**非通孔 {nt}/{m['n_vias']} 支**：" + "；".join(
            f"{k}={v}" for k, v in m["via_type_census"].items() if "BLIND" in k),
        nt == 0,
        "JLC 公布能力页：Blind/Buried Vias Not supported / 仅通孔；FAQ 列为 advanced option 须 DFM review")
    return out


def main() -> int:
    board_text = BOARD.read_text()
    pro_text = PRO.read_text()
    dru_text = DRU.read_text()
    m = measure_as_built()
    asd = _run_drc(board_text, pro_text, dru_text)
    jlcrun = jlc_limit_drc(board_text, pro_text, dru_text)
    # 牙齿①：把线宽限抬到 0.5mm，必须出现 track_width 违规（证明判据有牙）
    tooth_pro = json.loads(pro_text)
    tooth_pro["board"]["design_settings"]["rules"]["min_track_width"] = 0.5
    tooth = _run_drc(board_text, json.dumps(tooth_pro, indent=2), dru_text)
    teeth_ok = tooth["by_type"].get("track_width", 0) > 0
    items = _items(m, asd, jlcrun)
    fails = [i["item"] for i in items if i["verdict"] == "FAIL"]
    # 牙齿②：过孔类型项必须 FAIL（本板 220 非通孔）
    teeth2_ok = "**过孔类型（盲/埋孔）**" in fails
    rec = {
        "artifact": "m13_v57_co146_jlc_dfm_gate", "schema": 1, "revision": "CO146-JLC-DFM.1",
        "nature": "L2 只读机判：DFM 对照 JLC 8 层公布能力（监理指令 #10 动作 4）",
        "board": BOARD.name, "board_sha16": sha16(BOARD), "board_sha256": sha(BOARD),
        "as_built": m,
        "drc_as_designed": asd,
        "drc_jlc_limits": jlcrun,
        "items": items,
        "verdict": "PASS" if not fails else "FAIL",
        "fails": fails,
        "teeth": {"t01_track_width_limit_teeth": {"ok": teeth_ok, "evidence": tooth["by_type"]},
                  "t02_blind_via_item_fails": {"ok": teeth2_ok}},
        "redline": "只读：仅读板/kicad-cli DRC；坐标零搜索；不改板/图纸/SPEC/冻结四源。",
    }
    (STEP2 / "m13_v57_co146_jlc_dfm_gate.json").write_text(
        json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    srcfile = STEP2 / "m13_v57_co146_jlc_capability_source.html"
    cap = {"artifact": "m13_v57_co146_jlc8_capability", "schema": 1,
           "source_url": JLC_URL, "fetched": JLC_FETCH_DATE,
           "source_page_file": srcfile.name,
           "source_page_sha256": sha(srcfile) if srcfile.exists() else None,
           "source_page_bytes": srcfile.stat().st_size if srcfile.exists() else None,
           "note": "抓取件为 JLC 公布能力页（jlcpcb.com/capabilities/pcb-capabilities）；下表逐条引用原文。",
           "capability": JLC8}
    (STEP2 / "m13_v57_co146_jlc8_capability.json").write_text(
        json.dumps(cap, ensure_ascii=False, indent=1) + "\n")
    card = [f"# CO-146 卡 · DFM 对照 JLC 8 层能力（监理指令 #10 动作 4）", "",
            f"- 板：`{BOARD.name}` `{sha16(BOARD)}`｜判据源：{JLC_URL}（{JLC_FETCH_DATE} 抓取）",
            f"- as-designed DRC：**{asd['n']}** {asd['by_type']}（unconnected {asd['unconnected']}）",
            f"- JLC 下限 DRC：**{jlcrun['n']}** {jlcrun['by_type']}",
            f"- **verdict = {rec['verdict']}**；FAIL 项：{fails}", "",
            "| # | 项 | JLC 限 | 实测 | 判 |", "|---|---|---|---|---|"]
    for i, it in enumerate(items, 1):
        card.append(f"| {i} | {it['item']} | {it['jlc_limit']} | {it['measured']} | **{it['verdict']}** |")
    card += ["", "## 牙齿", f"- T1 线宽限抬到 0.5mm ⇒ track_width 违规 {tooth['by_type'].get('track_width',0)}（>0 ok={teeth_ok}）",
             f"- T2 过孔类型项必须 FAIL：ok={teeth2_ok}", ""]
    (STEP2 / "m13_v57_co146_jlc_dfm_gate.md").write_text("\n".join(card) + "\n")
    print("verdict:", rec["verdict"], "| fails:", fails)
    print("as-designed:", asd["n"], asd["by_type"])
    print("jlc-limits :", jlcrun["n"], jlcrun["by_type"])
    print("min track:", m["min_track_width_mm"], "| min via drill/dia:", m["min_via_drill_mm"], m["min_via_diameter_mm"],
          "| annular:", m["min_via_annular_mm"], "| via h2h:", m["min_via_hole_to_hole_mm"])
    print("non-through vias:", m["n_non_through_vias"], m["via_type_census"])
    print("teeth:", teeth_ok, teeth2_ok)
    return 0 if (teeth_ok and teeth2_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
