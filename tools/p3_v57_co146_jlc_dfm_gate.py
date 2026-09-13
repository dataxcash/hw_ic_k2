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
import hashlib, html, json, re, shutil, subprocess, sys, tempfile
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
# CO-172（F-5）：板规铜-板边净距须由**冻结 drc_rules** 派生（原为硬编码 "0.30mm" 字面量）
RULES_FILE = ROOT / "_shared/eda_core/drc_rules.json"
BOARD_RULES = json.loads(RULES_FILE.read_text())
EDGE_CLEARANCE_RULE_MM = float(BOARD_RULES["manufacturing"]["min_copper_edge_clearance"])
MIL_MM = 0.0254   # CO-178：mil↔mm 换算（禁在限值文本内硬编码 mil 数）
# CO-176（G-2）：能力表引证须**逐条绑定**抓取件 —— 每条给一个**原文子串**锚点；非原文引证须**显式标注**。
CAP_SRC_HTML = STEP2 / "m13_v57_co146_jlc_capability_source.html"
CAPABILITY_ANCHORS = {
    "layer_count": "Layer count 1-32 Layers",
    "impedance_control_layers": "Controlled Impedance 4/6/8/10/12/14/16/18/20/.../32 layers",
    "impedance_tolerance_pct": "Impedance Tolerance ±10%",
    "board_max_mm": "FR4(6-layer and above): 656 × 586 mm",
    "board_min_mm": "Minimum Dimensions FR4/Rogers/PTFE: 3 × 3 mm",
    "thickness_mm": "Thickness 0.4 – 4.5 mm",
    "outer_copper_oz": "Multi-layer: 1 oz / 2 oz",
    "inner_copper_oz": "Finished Inner Layer Copper 0.5 oz / 1 oz / 2 oz",
    "min_track_width_mm": "Multilayer: 0.09 / 0.09 mm (3.5 / 3.5 mil)",
    "min_track_spacing_mm": "3 mil is acceptable in BGA fan-outs.",
    "min_via_hole_mm": "② Preferred Min. Via hole size: 0.2mm",
    "min_via_diameter_mm": "Min. Via hole size/diameter 0.15mm / 0.25mm",
    "via_annular_note": "① Via diameter should be 0.1mm(0.15mm preferred) larger than Via hole size",
    "via_hole_to_hole_mm": "Via Hole-to-Hole Spacing 0.2mm",
    "pad_hole_to_hole_mm": "Pad Hole-to-Hole Spacing 0.45mm",
    "min_npth_mm": "Min. Non-plated holes 0.50mm",
    "min_plated_slot_mm": "Multi-layer: 0.35mm",
    "copper_edge_clearance_mm": "Copper clearance from routed board edges: ≧0.2 mm",
    "solder_mask_to_copper_mm": "Keep at least 0.09 mm clearance between soldermask openings",
    "solder_mask_bridge_mm": "Soldermask bridge 0.10mm 1oz: Min. pad spacing: 0.10 mm",
    "surface_finish": "Surface Finish HASL",
    "er_table": "FR-4 Dielectric Constants",
    "blind_buried": "Blind/Buried Vias Not supported",
    "blind_buried_faq": "Advanced options such as blind/buried vias, HDI (laser vias)",
}
# 非原文引证：须**显式**列出并给理由（CO-176 查获 3 条**静默删改**：outer_copper_oz / min_track_width_mm / …）
CAPABILITY_QUOTE_NOT_VERBATIM = {
    "thickness_mm": "原文跨段（板厚范围 / FR-4 档位 / 公差三段）⇒ 引证为省略式",
    "outer_copper_oz": "**静默删改**（省略 2-layer 档位：1 oz / 2 oz / 2.5 oz / 3.5 oz / 4.5oz）⇒ 现显式标注",
    "inner_copper_oz": "省略式（亦含 0.5oz by default 段）",
    "min_track_width_mm": "**静默删改**（省略 1-/2-layer 档 0.10 / 0.10 mm）⇒ 现显式标注",
    "min_track_spacing_mm": "非引文：由同段 width/spacing 行**改写**（中文）；原文见 anchor",
    "min_via_hole_mm": "省略式（省略 1-/2-layer 档与 ② Preferred…）",
    "min_plated_slot_mm": "省略式（省略 2-layer: 0.5mm）",
    "surface_finish": "省略式（省略 6 层及以上不支持 HASL 的完整句）",
    "er_table": "表格扁平化 ⇒ 引证为省略式",
    "blind_buried_faq": "省略式（省略 require DFM review 尾）",
}


def _norm(s: str) -> str:
    return re.sub(r"[\s\u00a0]+", " ", str(s)).strip()


def _page_text(path: Path) -> str:
    try:
        raw = path.read_text(errors="replace")
    except OSError:
        return ""
    return _norm(html.unescape(re.sub(r"<[^>]+>", " ", raw)))


def capability_citation_checks(page_text: str, capability: dict, anchors: dict, not_verbatim: dict) -> dict:
    """CO-176（G-2）：能力表引证可核验性判据（纯函数）。

    ① 锚点须覆盖全部能力条目且**均非空**；② 每条锚点须为抓取件**原文子串**；
    ③ **实测**非原文引证集须与**声明的**集**完全一致**（禁静默删改/改写）；④ 声明项须有理由；⑤ 原文引证数须 ≥ 下限。
    """
    keys = sorted(capability)
    out = {"anchors_cover_capability": set(anchors) == set(capability),
           "anchors_nonempty": all(str(anchors.get(k) or "").strip() for k in keys)}
    for k in keys:
        a = _norm(anchors.get(k) or "")
        out[f"{k}.anchor_verbatim"] = bool(a) and a in page_text
    measured = sorted(k for k in keys
                      if not (capability[k].get("quote") and _norm(capability[k]["quote"]) in page_text))
    out["not_verbatim_declared_exactly"] = (measured == sorted(not_verbatim))
    out["not_verbatim_reasons_present"] = all(str(not_verbatim.get(k, "")).strip() for k in measured)
    out["verbatim_floor"] = (len(keys) - len(measured)) >= 10
    return out


# CO-177：能力表的**数值/文本主张**须由抓取件**原文抽取**核验（正则捕获 ↔ 声明值）。
# 形如 [(pattern, [expected...]), ...] 或 ["literal substring"]；见 capability_value_bind_checks()。
CAPABILITY_VALUE_BIND = {
    "layer_count": [("Layer count (1)-(32) Layers", ["1", "32"])],
    "impedance_control_layers": ["Controlled Impedance 4/6/8/10/12/14/16/18/20/.../32 layers"],
    "impedance_tolerance_pct": [("Impedance Tolerance ±(10)%", ["10"])],
    "board_max_mm": [("FR4\\(6-layer and above\\): (656) × (586) mm", ["656", "586"])],
    "board_min_mm": [("Minimum Dimensions FR4/Rogers/PTFE: (3) × (3) mm", ["3", "3"])],
    "thickness_mm": [("Thickness (0\\.4) – (4\\.5) mm", ["0.4", "4.5"]),
                     ("Thickness Tolerance \\(Thickness≥1\\.0mm\\) ± (10)%", ["10"]),
                     ("0\\.4/0\\.6/0\\.8/1\\.0/1\\.2/(1\\.6)/2\\.0 mm", ["1.6"])],
    "outer_copper_oz": [("Multi-layer: (1) oz / (2) oz", ["1", "2"])],
    "inner_copper_oz": [("Finished Inner Layer Copper (0\\.5) oz / (1) oz / (2) oz", ["0.5", "1", "2"])],
    "min_track_width_mm": [("Multilayer: (0\\.09) / 0\\.09 mm \\(3\\.5 / 3\\.5 mil\\)", ["0.09"])],
    "min_track_spacing_mm": [("Multilayer: 0\\.09 / (0\\.09) mm \\(3\\.5 / 3\\.5 mil\\)", ["0.09"])],
    "min_via_hole_mm": [("Min\\. Via hole size/diameter (0\\.15)mm / 0\\.25mm", ["0.15"]),
                        ("Preferred Min\\. Via hole size: (0\\.2)mm", ["0.2"])],
    "min_via_diameter_mm": [("Min\\. Via hole size/diameter 0\\.15mm / (0\\.25)mm", ["0.25"])],
    "via_annular_note": [("0\\.1mm\\((0\\.15)mm preferred\\) larger than Via hole size", ["0.15"])],
    "via_hole_to_hole_mm": [("Via Hole-to-Hole Spacing (0\\.2)mm", ["0.2"])],
    "pad_hole_to_hole_mm": [("Pad Hole-to-Hole Spacing (0\\.45)mm", ["0.45"])],
    "min_npth_mm": [("Min\\. Non-plated holes (0\\.50)mm", ["0.50"])],
    "min_plated_slot_mm": [("Min\\. Plated Slots Width 2-layer: 0\\.5mm Multi-layer: (0\\.35)mm", ["0.35"])],
    "copper_edge_clearance_mm": [("Copper clearance from routed board edges: ≧(0\\.2) mm", ["0.2"])],
    "solder_mask_to_copper_mm": [("Keep at least (0\\.09) mm clearance between soldermask openings", ["0.09"])],
    "solder_mask_bridge_mm": [("Soldermask bridge (0\\.10)mm 1oz", ["0.10"])],
    "surface_finish": ["Surface Finish HASL (leaded / lead-free), ENlG, OSP"],
    "er_table": ["7628 Prepreg 4.4 3313 Perpreg 4.1 2116 Perpreg 4.16"],
    "blind_buried": ["Blind/Buried Vias Not supported"],
    "blind_buried_faq": ["Advanced options such as blind/buried vias, HDI (laser vias)"],
}


def _val_eq(a, b) -> bool:
    """数值按 float 比较（0.50 == 0.5），否则字符串归一比较。"""
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return str(a).strip() == str(b).strip()


ANCHOR_WINDOW = 400      # CO-184：值绑定匹配须落在其锚点定位处的邻域内（字符）


def capability_value_bind_checks(page_text: str, capability: dict, bind: dict, anchors: dict) -> dict:
    """CO-177/CO-184：能力表的**值**须**可由抓取件原文抽取**得到，且**上下文受约束**。

    ① 绑定须覆盖全部条目且非空；② 每条字面量须出现 / 每条正则须匹配；③ 捕获组数须与期望数一致且**逐值相等**；
    ④ 捕获组总数须 ≥ 下限（防退化绑定，如正则恒不捕获）；
    ⑤ **CO-184**：锚点须在抓取件中**唯一**定位（否则「原文子串」不可定位值）；⑥ 值绑定匹配须落在
    锚点邻域（±`ANCHOR_WINDOW`）内 —— 防「同锚多处时取到远处置同值数字」。
    """
    keys = sorted(capability)
    out = {"bind_covers_capability": set(bind) == set(capability),
           "bind_nonempty": all(bind.get(k) for k in keys)}
    n_groups, ok = 0, True
    for k in keys:
        for r in (bind.get(k) or []):
            if isinstance(r, str):
                if r not in page_text:
                    ok = False; out[f"{k}.literal_missing"] = False
            else:
                pat, exp = r
                m = re.search(pat, page_text)
                if not m:
                    ok = False; out[f"{k}.nomatch"] = False; continue
                g = list(m.groups()); n_groups += len(g)
                if len(g) != len(exp) or not all(_val_eq(x, y) for x, y in zip(g, exp)):
                    ok = False; out[f"{k}.value_mismatch"] = False
    out["bind_all_resolved"] = ok
    out["bind_group_floor"] = n_groups >= 25
    # CO-184：上下文约束（锚点唯一定位 + 值须在锚点邻域）—— fail-closed
    uniq, local = True, True
    for k in keys:
        a = _norm(anchors.get(k) or "")
        if not a or page_text.count(a) != 1:
            uniq = False; out[f"{k}.anchor_not_uniquely_located"] = False
            continue
        a0 = page_text.index(a)
        for r in (bind.get(k) or []):
            pat = re.escape(r) if isinstance(r, str) else r[0]
            mm = re.search(pat, page_text)
            if mm is not None and abs(mm.start() - a0) > ANCHOR_WINDOW:
                local = False; out[f"{k}.value_outside_anchor_window"] = False
    out["anchor_localizes_uniquely"] = uniq
    out["value_within_anchor_window"] = local
    return out


def edge_rule_bound_checks(items: list, rule_mm: float) -> dict:
    """CO-172（F-5）：DFM 记录的「铜到板边」实测文本须携带**由冻结规则派生的**板规值。"""
    txt = next((it.get("measured", "") for it in items if it.get("item") == "铜到板边"), "")
    return {"measured_carries_board_rule": f"{rule_mm:.2f}mm" in txt}


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


def _items(m: dict, asd: dict, jlcrun: dict, j: dict | None = None) -> list[dict]:
    """CO-178：全部限值**由能力表派生**（禁内嵌硬编码派生值）；`j` 可注入（供牙齿 t08 的扰动证明）。"""
    j = j or JLC8
    out = []

    def add(item, limit, measured, ok, note=""):
        out.append({"item": item, "jlc_limit": limit, "measured": measured,
                    "verdict": "PASS" if ok else "FAIL", "note": note})

    size = m["board_size_mm"]
    add("板尺寸", f"≤{j['board_max_mm']['w']:g}×{j['board_max_mm']['h']:g}mm"
                  f" 且 ≥{j['board_min_mm']['w']:g}×{j['board_min_mm']['h']:g}mm",
        f"{size[0]}×{size[1]}mm", size[0] <= j["board_max_mm"]["w"] and size[1] <= j["board_max_mm"]["h"]
        and size[0] >= j["board_min_mm"]["w"] and size[1] >= j["board_min_mm"]["h"])
    _imp_layers = sorted({int(x) for x in re.findall(r"\d+", j["impedance_control_layers"]["value"])})
    add("层数", f"{j['layer_count']['min']}–{j['layer_count']['max']} 层"
                f"（阻抗控制支持 {'/'.join(str(x) for x in _imp_layers)}）",
        f"{m['n_copper_layers']} 层", m["n_copper_layers"] in _imp_layers)
    add("外层铜厚", j["outer_copper_oz"]["allowed"], "1 oz（SPEC stackup / 监理定值）", True, "声明值=监理定值")
    add("内层铜厚", j["inner_copper_oz"]["allowed"], "0.5 oz（SPEC stackup / JLC 默认）", True, "声明值=监理定值")
    add("成品板厚", f"{j['thickness_mm']['value']}mm ±{j['thickness_mm']['tol_pct']}%", "1.6mm（JLC08161H）", True, "声明值")
    add("最小线宽", f"≥{j['min_track_width_mm']['value']}mm ({j['min_track_width_mm']['value']/MIL_MM:.1f}mil)",
        f"{m['min_track_width_mm']}mm", m["min_track_width_mm"] >= j["min_track_width_mm"]["value"])
    add("最小线距（域外，netclass 0.1/0.175/0.2 全 ≥3.5mil）", f"≥{j['min_track_spacing_mm']['value']}mm",
        f"JLC 限 DRC clearance 违规 = {jlcrun['by_type'].get('clearance', 0)}",
        jlcrun["by_type"].get("clearance", 0) == 0, "含逃逸域按 0.09mm 收紧后重跑")
    add("最小过孔孔壁", f"≥{j['min_via_hole_mm']['value']}mm（本板按 JLC 建议值 ≥{j['min_via_hole_mm']['preferred']}mm 判）",
        f"{m['min_via_drill_mm']}mm", m["min_via_drill_mm"] >= j["min_via_hole_mm"]["preferred"])
    add("最小过孔盘径", f"≥{j['min_via_diameter_mm']['value']}mm", f"{m['min_via_diameter_mm']}mm",
        m["min_via_diameter_mm"] >= j["min_via_diameter_mm"]["value"])
    add("过孔环宽（单边）", f"盘径 ≥ 孔径+{j['via_annular_note']['value']}mm"
                           f"（⇒ 单边 ≥{j['via_annular_note']['value'] / 2:.3f}mm）",
        f"{m['min_via_annular_mm']}mm",
        m["min_via_diameter_mm"] - m["min_via_drill_mm"] >= j["via_annular_note"]["value"] - 1e-9)
    add("过孔孔到孔", f"≥{j['via_hole_to_hole_mm']['value']}mm", f"{m['min_via_hole_to_hole_mm']}mm",
        m["min_via_hole_to_hole_mm"] >= j["via_hole_to_hole_mm"]["value"])
    add("NPTH 最小孔径", f"≥{j['min_npth_mm']['value']}mm",
        f"{m['min_npth_drill_mm']}mm（{list(m['npth_drill_hist_mm'])}）",
        m["min_npth_drill_mm"] is None or m["min_npth_drill_mm"] >= j["min_npth_mm"]["value"])
    add("铜到板边", f"≥{j['copper_edge_clearance_mm']['value']}mm",
        f"板规 min_copper_edge_clearance={EDGE_CLEARANCE_RULE_MM:.2f}mm；JLC 限 DRC copper_edge_clearance 违规 = "
        f"{jlcrun['by_type'].get('copper_edge_clearance', 0)}",
        jlcrun["by_type"].get("copper_edge_clearance", 0) == 0)
    add("阻焊桥 / 阻焊-铜净距", f"桥 ≥{j['solder_mask_bridge_mm']['value']}mm；开窗到邻近铜 ≥{j['solder_mask_to_copper_mm']['value']}mm",
        f"JLC 限 DRC solder_mask_bridge 违规 = {jlcrun['by_type'].get('solder_mask_bridge', 0)}",
        jlcrun["by_type"].get("solder_mask_bridge", 0) == 0)
    _hasl = re.search(r"with (\d+) or more layers", j["surface_finish"].get("quote", ""))
    add("表面处理", f"{_hasl.group(1) if _hasl else '?'} 层及以上不支持 HASL ⇒ 须 {j['surface_finish']['value']}",
        f"沉金 {j['surface_finish']['value']}", True, "监理定值一致")
    add("阻抗控制", f"支持层数 {j['impedance_control_layers']['value']}，公差 ±{j['impedance_tolerance_pct']['value']}%",
        "8 层 + 85Ω±10%（见 CO-146 阻抗表）", True, "终判 = JLC 阻抗控制服务")
    nt = m["n_non_through_vias"]
    add("**过孔类型（盲/埋孔）**", "**不支持盲/埋孔（仅通孔）**",
        f"**非通孔 {nt}/{m['n_vias']} 支**：" + "；".join(
            f"{k}={v}" for k, v in m["via_type_census"].items() if "BLIND" in k),
        nt == 0,
        "JLC 公布能力页：Blind/Buried Vias Not supported / 仅通孔；FAQ 列为 advanced option 须 DFM review")
    return out


# CO-178：`_items()` 的限值文本**必须**由能力表派生。判据为**成分级**（非「文本是否变化」）：
# 扰动后，该项 `jlc_limit` 须**含**由扰动值派生出的**具体成分串**，且**基线文本不含该串**。
# 缘起（自测加严）：首版仅查「文本是否变化」⇒ **部分硬编码**（如把 `3.5mil` 写死而 mm 段仍派生）可逃逸；
# 改为成分级断言 + 基线否定后，「mil 写死」类回归必被击穿。
ITEM_DERIVATION_CASES = [
    ("板尺寸", {"board_min_mm": {"w": 9.0, "h": 9.0}}, ["≥9×9mm"]),
    ("板尺寸", {"board_max_mm": {"w": 10.0, "h": 10.0}}, ["≤10×10mm"]),
    ("层数", {"impedance_control_layers": {"value": "4/6/8/10/12/14/16/18/20/24/32"}}, ["20/24"]),
    ("最小线宽", {"min_track_width_mm": {"value": 0.075}}, ["≥0.075mm", "(3.0mil)"]),
    ("最小过孔孔壁", {"min_via_hole_mm": {"value": 0.12, "preferred": 0.18}}, ["≥0.12mm", "≥0.18mm"]),
    ("最小过孔盘径", {"min_via_diameter_mm": {"value": 0.20}}, ["≥0.2mm"]),
    ("过孔环宽（单边）", {"via_annular_note": {"value": 0.20}}, ["单边 ≥0.100mm"]),
    ("过孔孔到孔", {"via_hole_to_hole_mm": {"value": 0.25}}, ["≥0.25mm"]),
    ("NPTH 最小孔径", {"min_npth_mm": {"value": 0.60}}, ["≥0.6mm"]),
    ("铜到板边", {"copper_edge_clearance_mm": {"value": 0.25}}, ["≥0.25mm"]),
    ("阻焊桥 / 阻焊-铜净距", {"solder_mask_bridge_mm": {"value": 0.15}}, ["≥0.15mm"]),
    ("表面处理", {"surface_finish": {"value": "沉金"}}, ["须 沉金"]),
    ("阻抗控制", {"impedance_tolerance_pct": {"value": 5}}, ["±5%"]),
]


def item_limit_derivation_checks(m: dict, asd: dict, jlcrun: dict) -> dict:
    """CO-178：**成分级**派生性判据（含基线否定，防「部分硬编码」逃逸）。

    对每个情形：扰动能力表字段 ⇒ 该项 `jlc_limit` 须**含**由扰动值派生的**具体成分串**（`must`），
    且**基线文本不得含该串**。若该成分被硬编码，扰动后不会出现新成分串 ⇒ 判不通过。
    """
    base = {it["item"]: it for it in _items(m, asd, jlcrun)}
    out = {}
    for i, (item, patch, must) in enumerate(ITEM_DERIVATION_CASES):
        pert = {k: ({**JLC8[k], **v} if k in JLC8 else v) for k, v in patch.items()}
        cand = {it["item"]: it for it in _items(m, asd, jlcrun, j={**JLC8, **pert})}
        b, c = base.get(item), cand.get(item)
        bt = b["jlc_limit"] if b else ""
        ct = c["jlc_limit"] if c else ""
        out[f"case{i}_{item}"] = bool(b and c and all(s in ct for s in must) and not any(s in bt for s in must))
    out["items_present"] = len(base) >= 12
    return out



def _backdrill_capability(page: str) -> dict:
    """CO-204（监理指令 #12 动作 1）：JLC 能力页**同页明文**之 Backdrill 规则（anchor = 归一原文子串）。"""
    i = page.find("Backdrill Backdrill uses a secondary drilling process")
    seg = page[i:i + 2000] if i >= 0 else ""

    def g(pat):
        m = re.search(pat, seg)
        return m.group(0) if m else None

    a = {"intro": g(r"Backdrill uses a secondary drilling process[^\u2460]*"),
         "layers_thickness": g(r"Supports 4-32-layer FR4 boards with a thickness of \u22650\.8mm"),
         "diameter": g(r"Through-Hole Diaemter\(D\):\s*0\.2-0\.5mm"),
         "w_over": g(r"Backdrill Diameter\(W\):\s*typically 0\.2mm larger than through-hole diameter"),
         "depth": g(r"Backdrill Depth\(L\):\s*layers with backdrilling, customizable"),
         "dielectric_t": g(r"Dielectric Thickness\(T\):\s*\u22650\.15mm"),
         "safety_s": g(r"Safety Distance\(S\):\s*\u22650\.2mm")}
    return {"supported": bool(i >= 0 and all(a.values())),
            "layers_min": 4, "layers_max": 32, "thickness_min_mm": 0.8,
            "via_drill_d_mm": [0.2, 0.5], "backdrill_w_over_d_mm": 0.2,
            "dielectric_t_min_mm": 0.15, "safety_s_min_mm": 0.2,
            "anchor": a,
            "note": "背钻 = 二次钻控深、去余铜以降信号干扰（JLC 能力页明文）；冻结过孔策略 = 通孔 + 背钻（CO-204）。"}



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
    edge_bound = edge_rule_bound_checks(items, EDGE_CLEARANCE_RULE_MM)
    teeth3_ok = all(edge_bound.values()) and not all(
        edge_rule_bound_checks(items, EDGE_CLEARANCE_RULE_MM + 0.05).values())
    # CO-176（G-2）：能力表引证逐条绑定抓取件（anchor 原文子串 + 非原文引证显式标注）+ 灵敏度
    _page = _page_text(CAP_SRC_HTML)
    _cite = capability_citation_checks(_page, JLC8, CAPABILITY_ANCHORS, CAPABILITY_QUOTE_NOT_VERBATIM)
    _cite_sens = not all(capability_citation_checks(
        _page, JLC8,
        {**CAPABILITY_ANCHORS, "layer_count": CAPABILITY_ANCHORS["layer_count"] + "ZZZZ"},
        CAPABILITY_QUOTE_NOT_VERBATIM).values())
    # CO-177：能力表**值**须可由抓取件原文抽取核验（正则捕获 ↔ 声明值）+ 灵敏度
    _bind = capability_value_bind_checks(_page, JLC8, CAPABILITY_VALUE_BIND, CAPABILITY_ANCHORS)
    _bind_sens = not all(capability_value_bind_checks(
        _page, JLC8,
        {**CAPABILITY_VALUE_BIND,
         "min_track_width_mm": [("Multilayer: (0\\.09) / 0\\.09 mm \\(3\\.5 / 3\\.5 mil\\)", ["0.10"])]},
        CAPABILITY_ANCHORS).values())
    # CO-184：上下文约束判据的**合成正/负控**（数据无关）——唯一锚点+邻近⇒True；锚点重复⇒不唯一；值远置⇒越窗
    _syn_cap = {"k": {"value": 0.09, "quote": "Beta 0.09 mm"}}
    _syn_anc = {"k": "Beta 0.09 mm"}
    _syn_bind = {"k": [("Beta (0\\.09) mm", ["0.09"])]}
    _pg_ok = "Prefix Beta 0.09 mm suffix"
    _pg_dup = "Beta 0.09 mm " + ("pad " * 150) + "Beta 0.09 mm"
    _pg_far = "Beta 0.09 mm " + ("pad " * 150) + "Other 0.09 mm"
    _syn_far = {"k": [("Other (0\\.09) mm", ["0.09"])]}
    _ok_chk = capability_value_bind_checks(_pg_ok, _syn_cap, _syn_bind, _syn_anc)
    _ctx_ok = bool(_ok_chk["anchor_localizes_uniquely"] and _ok_chk["value_within_anchor_window"]
                   and _ok_chk["bind_all_resolved"])
    _ctx_dup = not capability_value_bind_checks(_pg_dup, _syn_cap, _syn_bind, _syn_anc)["anchor_localizes_uniquely"]
    _ctx_far = not capability_value_bind_checks(_pg_far, _syn_cap, _syn_far, _syn_anc)["value_within_anchor_window"]
    _ctx_sens = _ctx_ok and _ctx_dup and _ctx_far
    # CO-178：`_items()` 限值须由能力表派生（逐项扰动证明）
    _deriv = item_limit_derivation_checks(m, asd, jlcrun)
    fails = [i["item"] for i in items if i["verdict"] == "FAIL"]
    # 牙齿②：过孔类型项必须 FAIL（本板 220 非通孔）
    teeth2_ok = "**过孔类型（盲/埋孔）**" in fails
    rec = {
        "artifact": "m13_v57_co146_jlc_dfm_gate", "schema": 1, "revision": "CO146-JLC-DFM.6",
        "nature": "L2 只读机判：DFM 对照 JLC 8 层公布能力（监理指令 #10 动作 4）",
        "board": BOARD.name, "board_sha16": sha16(BOARD), "board_sha256": sha(BOARD),
        "as_built": m,
        "drc_as_designed": asd,
        "drc_jlc_limits": jlcrun,
        "items": items,
        "verdict": "PASS" if not fails else "FAIL",
        "fails": fails,
        "teeth": {"t01_track_width_limit_teeth": {"ok": teeth_ok, "evidence": tooth["by_type"]},
                  "t02_blind_via_item_fails": {"ok": teeth2_ok},
                  "t03_board_rule_edge_bound": {"ok": teeth3_ok, "checks": edge_bound,
                                                "board_rule_mm": EDGE_CLEARANCE_RULE_MM,
                                                "source": str(RULES_FILE.relative_to(ROOT))},
                  "t04_capability_citation_bound": {"ok": all(_cite.values()), "checks": _cite,
                                                    "anchors": len(CAPABILITY_ANCHORS),
                                                    "not_verbatim": sorted(CAPABILITY_QUOTE_NOT_VERBATIM)},
                  "t05_capability_citation_sensitivity": {"ok": _cite_sens},
                  "t06_capability_value_bound": {"ok": all(_bind.values()), "checks": _bind,
                                                 "rules": sum(len(CAPABILITY_VALUE_BIND[k]) for k in CAPABILITY_VALUE_BIND)},
                  "t07_capability_value_bind_sensitivity": {"ok": _bind_sens},
                  "t07b_anchor_localization_sensitivity": {"ok": _ctx_sens,
                                                           "window_chars": ANCHOR_WINDOW,
                                                           "controls": {"unique_and_near": _ctx_ok,
                                                                        "duplicate_anchor_detected": _ctx_dup,
                                                                        "far_value_detected": _ctx_far}},
                  "t08_drc_item_limits_derived": {"ok": all(_deriv.values()),
                                                  "cases": len(ITEM_DERIVATION_CASES), "checks": _deriv}},
        "redline": "只读：仅读板/kicad-cli DRC；坐标零搜索；不改板/图纸/SPEC/冻结四源。",
    }
    (STEP2 / "m13_v57_co146_jlc_dfm_gate.json").write_text(
        json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    srcfile = CAP_SRC_HTML
    cap = {"artifact": "m13_v57_co146_jlc8_capability", "schema": 1, "revision": "CO146-CAP.4",
           "source_url": JLC_URL, "fetched": JLC_FETCH_DATE,
           "source_page_file": srcfile.name,
           "source_page_sha256": sha(srcfile) if srcfile.exists() else None,
           "source_page_bytes": srcfile.stat().st_size if srcfile.exists() else None,
           "value_bind": {"n_rules": sum(len(CAPABILITY_VALUE_BIND[k]) for k in CAPABILITY_VALUE_BIND),
                          "n_capture_groups": 29, "floor": 25,
                          "scheme": "值/文本主张须由抓取件原文**正则抽取**得到（t06 逐条核验；t07 灵敏度）",
                          "checks": _bind},
           "note": "抓取件为 JLC 公布能力页（jlcpcb.com/capabilities/pcb-capabilities）。CO-176（G-2）订正："
                   "每条 `anchor` 为抓取件**原文子串**（机判 t04 逐条核验）；`quote` 为可读引文，"
                   "**非原文者**列于 `citation.not_verbatim` 并给理由（禁静默删改/改写）。",
           "citation": {"anchor_scheme": "anchor 须为抓取件（去标签+空白归一）原文子串；非原文引证须显式标注",
                        "n_entries": len(JLC8),
                        "n_verbatim": len(JLC8) - len([k for k in JLC8
                                                       if not (JLC8[k].get("quote")
                                                               and _norm(JLC8[k]["quote"]) in _page)]),
                        "not_verbatim": {k: v for k, v in sorted(CAPABILITY_QUOTE_NOT_VERBATIM.items())},
                        "checks": _cite},
           "capability": JLC8, "backdrill_capability": _backdrill_capability(_page)}   # CO-204
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
             f"- T2 过孔类型项必须 FAIL：ok={teeth2_ok}",
             f"- T3 板规铜-板边值须由冻结 drc_rules 派生（{EDGE_CLEARANCE_RULE_MM:.2f}mm）：ok={teeth3_ok}",
             f"- T4 能力表引证逐条绑定抓取件（anchor 原文子串 + 非原文显式标注）：ok={all(_cite.values())}",
             f"- T5 引证判据灵敏度（篡改 anchor 即判不通过）：ok={_cite_sens}",
             f"- T6 能力表**值**可由抓取件原文抽取核验（29 捕获组 ↔ 声明值）：ok={all(_bind.values())}",
             f"- T7 值绑定灵敏度（篡改期望值即判不通过）：ok={_bind_sens}",
             f"- T8 逐项限值须由能力表派生（{len(ITEM_DERIVATION_CASES)} 扰动情形）：ok={all(_deriv.values())}", ""]
    (STEP2 / "m13_v57_co146_jlc_dfm_gate.md").write_text("\n".join(card) + "\n")
    print("verdict:", rec["verdict"], "| fails:", fails)
    print("as-designed:", asd["n"], asd["by_type"])
    print("jlc-limits :", jlcrun["n"], jlcrun["by_type"])
    print("min track:", m["min_track_width_mm"], "| min via drill/dia:", m["min_via_drill_mm"], m["min_via_diameter_mm"],
          "| annular:", m["min_via_annular_mm"], "| via h2h:", m["min_via_hole_to_hole_mm"])
    print("non-through vias:", m["n_non_through_vias"], m["via_type_census"])
    print("teeth:", teeth_ok, teeth2_ok, teeth3_ok, all(_cite.values()), _cite_sens, all(_bind.values()),
          _bind_sens, all(_deriv.values()))
    # CO-159（F-7）：R-CO158-3 —— 退出码须反映 verdict（本件 verdict 允许为 FAIL（DFM 阻塞项）⇒ rc=1；
    # 此前 `return 0 if teeth else 1` 使 FAIL 时 rc 仍 0，复现序无法 fail-fast）。
    return 0 if (rec["verdict"] == "PASS" and teeth_ok and teeth2_ok and teeth3_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
