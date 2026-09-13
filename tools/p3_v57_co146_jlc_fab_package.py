#!/usr/bin/env python3
"""CO-146 A3 — JLC 打样包（Gerber RS-274X + 钻孔 Excellon + 叠层图 + 阻抗表 + 层序 + 下单备注）。

性质：**只出交付物，不改板/SPEC/冻结四源**（读交付板 `k2_v4_8L.l4.kicad_pcb`）。
产出目录：`pm_gate/artifacts/k2_v4/L5/jlc_package/`
  01_gerber_rs274x/*.gbr(.gbrjob)   kicad-cli pcb export gerbers --board-plot-params --no-x2
  02_drill_excellon/*.drl + *.drl 图 + report
  03_stackup/JLC08161H_stackup.svg + .md      叠层图（由 SPEC dielectrics 确定性绘制）
  04_impedance/impedance_table.md|json        CO-146 阻抗表副本
  05_layer_sequence.txt                       层序 + 层角色
  ORDER_NOTES.md                              下单备注（含 DFM 阻塞项，如实）
  MANIFEST.json                               每文件 sha256 + 计数
  06_rulings/*                                ORDER_NOTES 声明随单提交的 L2 裁定件 + DFM 记录（CO-158）
牙齿：① 跑两次 MANIFEST 必须逐字节同（幂等）；② 必须存在 8 个铜层 .gbr + 钻孔文件；
      ③ 目录内任何 sha 缺失即 FAIL。
"""
from __future__ import annotations
import copy, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path("/home/fila/jqdDev_2025/ic_hw")
K2 = ROOT / "k2"
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
OUT = K2 / "pm_gate/artifacts/k2_v4/L5/jlc_package"
CLI = ROOT / "AppDir/bin/kicad-cli"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
PRO = K2 / "k2_v4_8L.l4.kicad_pro"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json"
COPPER = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]
PLOT_LAYERS = ",".join(COPPER + ["F.Paste", "B.Paste", "F.Silkscreen", "B.Silkscreen",
                                 "F.Mask", "B.Mask", "Edge.Cuts"])

# CO-172（F-1..F-6）来源记录 + 冻结规则；OZ_TO_MM = 1oz 铜标称厚度（叠层图几何换算）
CO147 = STEP2 / "m13_v57_co147_l2_ruling.json"
CO148 = STEP2 / "m13_v57_co148_thermal_ruling.json"
CO149 = STEP2 / "m13_v57_co149_u6_thermal_mitigation.json"
CAP = STEP2 / "m13_v57_co146_jlc8_capability.json"
RULES = Path("/home/fila/jqdDev_2025/ic_hw/_shared/eda_core/drc_rules.json")
OZ_TO_MM = 0.035
MASK_EXPANSION_REWORK_MM = 0.02   # CO-172：R3 回退方案名义新开窗量（L2 提案，非记录字段）
MIL_MM = 0.0254


CANON_DATE = "2026-09-12T00:00:00+08:00"
TS_PAT = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:\d{2})?")


def canonicalize(d: Path) -> int:
    """KiCad 导出件内嵌墙钟时间戳 ⇒ 规范化（可复现性；制造语义不受影响）。"""
    n = 0
    for p in sorted(d.rglob("*")):
        if not p.is_file():
            continue
        try:
            t = p.read_text()
        except UnicodeDecodeError:
            continue
        t2 = TS_PAT.sub(CANON_DATE, t)
        if t2 != t:
            p.write_text(t2)
            n += 1
    return n


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha16(p) -> str:
    return sha256(Path(p))[:16]


def run(cmd: list[str]) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {' '.join(cmd)}\n{r.stdout}\n{r.stderr}")
    return r.stdout


def export_gerbers(d: Path) -> None:
    d.mkdir(parents=True, exist_ok=True)
    run([str(CLI), "pcb", "export", "gerbers", "--board-plot-params", "--no-x2",
         "--layers", PLOT_LAYERS, "--output", str(d), str(BOARD)])


def export_drill(d: Path) -> None:
    d.mkdir(parents=True, exist_ok=True)
    run([str(CLI), "pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm",
         "--generate-map", "--map-format", "svg", "--generate-report",
         "--report-path", str(d / "drill_report.txt"), "--output", str(d), str(BOARD)])


def stackup_svg(spec: dict, binding: dict | None = None) -> str:
    """叠层图（CO-170 / CO-172 F-6）：铜厚矩形**几何**与标题铜厚均由**声明定值表** copper oz 派生
    （1oz = 0.035mm 标称），非硬编码字面量 ⇒ 声明铜厚变更即随动，并由 t11c 几何牙齿复核。"""
    _cu = (binding or {}).get("copper") or {}
    outer_oz, inner_oz = float(_cu.get("outer_oz", 1.0)), float(_cu.get("inner_oz", 0.5))
    th_outer, th_inner = outer_oz * OZ_TO_MM, inner_oz * OZ_TO_MM
    dz = spec["stackup"]["dielectric_8l"]
    order = ["F.Cu", "d(F.Cu-In1.Cu)", "In1.Cu", "d(In1.Cu-In2.Cu)", "In2.Cu", "d(In2.Cu-In3.Cu)",
             "In3.Cu", "d(In3.Cu-In4.Cu)", "In4.Cu", "d(In4.Cu-In5.Cu)", "In5.Cu",
             "d(In5.Cu-In6.Cu)", "In6.Cu", "d(In6.Cu-B.Cu)", "B.Cu"]
    scale, top, h, w = 600.0, 40.0, 0.0, 560.0
    rows, y = [], top
    for name in order:
        if name.endswith("Cu"):
            th, fill, label = (th_outer if name in ("F.Cu", "B.Cu") else th_inner), "#c8811e", name
        else:
            c = dz[name]
            th, fill, label = c["mm"], "#d8e8d8", f'{c["material"]} {c["mm"]}mm er={c["er"]}'
        px = max(6.0, th * scale)
        rows.append(f'<rect x="40" y="{y:.2f}" width="{w}" height="{px:.2f}" fill="{fill}" '
                    f'stroke="#333" stroke-width="0.4"/>')
        rows.append(f'<text x="{w + 50}" y="{y + px / 2 + 3:.2f}" font-size="11">{name}  —  {label}</text>')
        y += px
    total = y - top
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{total + 80:.0f}">'
            f'<rect width="100%" height="100%" fill="white"/>'
            f'<text x="40" y="24" font-size="15" font-weight="bold">JLC08161H 8L 1.6mm 叠层（南亚 NP-155F）'
            f'｜外层 {outer_oz:g}oz / 内层 {inner_oz:g}oz｜总厚 {spec["stackup"]["total_thickness_mm"]}mm｜单边比例 {scale:.0f}px/mm</text>'
            + "".join(rows) + '</svg>')


def layer_sequence(spec: dict) -> str:
    imp = spec["impedance"]["per_layer"]
    lines = ["# 层序（top → bottom）｜交付板 k2_v4_8L.l4.kicad_pcb", ""]
    for i, ln in enumerate(COPPER, 1):
        role = spec["stackup"][ln]
        extra = ""
        if ln in imp:
            c = imp[ln]
            extra = (f"｜阻抗 {c['kind']} w={c['w_mm']}mm 对内净距{ c['gap_mm_delivered']}mm "
                     f"er={c['er']} ⇒ 85Ω±10%（见 04_impedance）")
        lines.append(f"{i}. {ln} — {role}{extra}")
    lines += ["", "介质：见 03_stackup/JLC08161H_stackup.svg｜铜厚：外层 1oz / 内层 0.5oz｜成品厚 1.6mm ±10%",
              "表面处理：ENIG 沉金（JLC：6 层及以上不支持 HASL）"]
    return "\n".join(lines) + "\n"


# CO-163（G-1/G-2）：下单参数**声明定值表**（监理指令 #10 绑定）与来源 pin。
JP = K2 / "pm_gate/artifacts/k2_v4/L2" / "jlc_prototype_parameters_v1.json"
INSTRUCTION = K2.parent / ".omo/supervision/ledger/instruction-10-jlc-prototype-ready.md"


def binding_tokens(binding: dict) -> dict:
    """把声明定值表渲染成 ORDER_NOTES 内使用的记号（:`g` 数字格式与备注文本一致）。"""
    imp_b = binding.get("impedance") or {}
    cu = binding.get("copper") or {}
    return {"stackup_code": str(binding.get("stackup", "")).split("（")[0],
            "thickness": f"{float(binding.get('total_thickness_mm', 0)):g} mm",
            "outer_copper": f"外层 {float(cu.get('outer_oz', 0)):g}oz",
            "inner_copper": f"内层 {float(cu.get('inner_oz', 0)):g}oz",
            "zdiff": f"{float(imp_b.get('target_zdiff', 0)):g}Ω",
            "tolerance": f"±{float(imp_b.get('tolerance_pct', 0)):g}%",
            "surface": "沉金" if "ENIG" in str(binding.get("surface_finish", "")).upper() else str(binding.get("surface_finish", ""))}


def _tok_re(tok: str) -> str:
    """CO-167（F-4/F-5）：把记号渲染为**有锚正则** —— 柔性空白（防排版噪声）+ 数值边界
    （防无锚子串，如 `185Ω` 命中 `85Ω`、`11.6 mm` 命中 `1.6 mm`）。"""
    frag = ""
    for i, ch in enumerate(tok):
        prev = tok[i - 1] if i else ""
        if i and "." not in (prev, ch) and prev.isdigit() != ch.isdigit():
            frag += r"\s*"          # 数字↔单位 边界允许柔性空白（`85 Ω` / `10 %`），不改数值
        frag += re.escape(ch)
    r = frag.replace(r"\ ", r"\s*")
    if re.match(r"^[0-9]", tok):
        r = r"(?<![0-9.])" + r + r"(?![0-9])"
    return r


def _tok_match(text: str, tok: str) -> bool:
    """CO-170：记号是否出现（复用 CO-167 的有锚正则）。"""
    return bool(tok) and re.search(_tok_re(tok), text) is not None


# CO-170（G-1）：03_stackup 图（**随单提交的制造输入**）须携带的声明记号子集
STACKUP_SVG_BINDING_KEYS = ("stackup_code", "thickness", "outer_copper", "inner_copper")


def stackup_svg_binding_checks(svg_text: str, binding: dict) -> dict:
    """CO-170（G-1）：叠层图（03_）须逐项携带声明定值表的记号。

    缘起：`stackup_svg(spec)` **只接收 SPEC**，其「外层 1oz / 内层 0.5oz」为硬编码字面量 ——
    声明定值表即使改铜厚，叠层图也不会跟随，且当时无任何牙齿覆盖该图（t09 只读 ORDER_NOTES）。
    """
    t = binding_tokens(binding)
    return {k: _tok_match(svg_text, t[k]) for k in STACKUP_SVG_BINDING_KEYS}


SVG_CU_RECT_RE = re.compile(r'<rect x="40"[^>]*?fill="#c8811e"[^>]*/>')
SVG_SCALE_RE = re.compile(r"单边比例 (\d+)px/mm")


def stackup_svg_copper_geometry_checks(svg_text: str, binding: dict) -> dict:
    """CO-172（F-6）：叠层图**铜厚矩形几何**须与声明定值表 copper oz 一致（1oz=0.035mm 标称 × 比例）。

    缘起：t11 只绑**文本**（「外层 1oz」）；铜厚矩形高度原为硬编码 `0.035`/`0.0175`（现改由声明派生），
    若未来声明变动而几何未随动，图与声明在**几何上**脱钩、制造侧按图施工 ⇒ 本牙齿把「几何 vs 声明」纳入机判。
    """
    cu = binding.get("copper") or {}
    outer_oz, inner_oz = float(cu.get("outer_oz", 1.0)), float(cu.get("inner_oz", 0.5))
    m = SVG_SCALE_RE.search(svg_text)
    scale = float(m.group(1)) if m else 0.0
    hs = [float(re.search(r'height="([0-9.]+)"', r).group(1)) for r in SVG_CU_RECT_RE.findall(svg_text)]
    exp = ([outer_oz * OZ_TO_MM * scale] + [inner_oz * OZ_TO_MM * scale] * 6
           + [outer_oz * OZ_TO_MM * scale])
    return {"n_copper_rects": len(hs), "scale_px_per_mm": scale,
            "geometry_matches_binding": bool(scale) and len(hs) == 8
                                          and all(abs(a - b) <= 0.01 for a, b in zip(hs, exp))}


def impedance_spread_pct(imp: dict) -> float | None:
    """CO-172（F-1）：watch（最宽间距）下**模型间**相对 spread%（以同几何模型最小值归一）。"""
    best = None
    for w in (imp.get("watch") or []):
        vals = []
        for zs in (w.get("zdiff") or {}).values():
            vals += [float(z) for z in (zs if isinstance(zs, list) else [zs])
                     if isinstance(z, (int, float)) and z > 0]
        if len(vals) >= 2:
            sp = (max(vals) - min(vals)) / min(vals) * 100.0
            best = sp if best is None or sp > best else best
    return round(best, 2) if best is not None else None


def via_census_figures(dfm: dict) -> dict:
    """CO-172（F-2）：**非通孔**过孔逐 span 计数（来源 = DFM 记录 `as_built.via_type_census`）。"""
    vc = ((dfm.get("as_built") or {}).get("via_type_census") or {})
    out = {}
    for key, n in vc.items():
        span, _, kind = str(key).partition("|")
        if kind != "THROUGH" and isinstance(n, int):
            out[span.replace("->", "→")] = n
    return out


# CO-172：§2 备注排版中每个 span 计数之后的字面分隔（防前缀匹配；亦为备注事实的一部分）
VIA_SPAN_SUFFIX = {"F.Cu→In2.Cu": "、", "In2.Cu→In5.Cu": "（埋孔）", "In5.Cu→B.Cu": "、", "F.Cu→In5.Cu": "）"}


def mask_clearance_figures(co147: dict) -> dict:
    """CO-172（F-3）：阻焊开窗-邻铜净距（来源 = CO-147 裁定记录 `mask_measure`）。"""
    m = co147.get("mask_measure") or {}
    gap = (m.get("closest") or {}).get("gap_mm")
    exp = m.get("mask_expansion_mm")
    rework = (round(gap + exp - MASK_EXPANSION_REWORK_MM, 4)
              if isinstance(gap, (int, float)) and isinstance(exp, (int, float)) else None)
    return {"gap_mm": gap, "shortfall_mm": m.get("shortfall_mm"), "jlc_min_mm": m.get("jlc_min_mm"),
            "mask_expansion_mm": exp, "rework_gap_mm": rework}


def thermal_figures(co148: dict, co149: dict) -> dict:
    """CO-172（F-4）：U6 热数字（来源 = CO-148 热裁定 + CO-149 缓解派生）。"""
    ps = [c.get("P_U6_W") for c in (co148.get("cases") or {}).values()
          if isinstance(c.get("P_U6_W"), (int, float))]
    return {"P_min_W": min(ps) if ps else None, "P_max_W": max(ps) if ps else None,
            "theta_ja_datasheet_C_per_W": (co149.get("routes") or {}).get("datasheet_theta_ja"),
            "Tj_limit_C": co148.get("Tj_limit_C"),
            "Tj_best_C": (co148.get("best") or {}).get("Tj_C"),
            "Tj_worst_C": (co148.get("worst") or {}).get("Tj_C"),
            "psi_jb_route_Tj_C": (co148.get("paths_cross_check") or {}).get("psi_jb_plus_board_route_Tj_C"),
            "ta_C": co149.get("ta_C")}


def _num(x) -> bool:
    return isinstance(x, (int, float))


def order_notes_record_figures(note: str, imp: dict, dfm: dict, co147: dict | None = None,
                               co148: dict | None = None, co149: dict | None = None,
                               cap: dict | None = None, rules: dict | None = None) -> dict:
    """CO-171 + CO-172：`ORDER_NOTES` 内**记录派生数字**须与来源记录一致（有锚正则）。

    CO-171（t12）覆盖 §5 阻抗偏离% 与 §7 DRC 计数；CO-172 扩到 §5 模型间 spread、§2 过孔 span 分解、
    §3 阻焊净距/欠量/回退净距、§6 U6 热数字、§4 JLC 限值 / 板规铜-板边、§7 silk 计数。
    扩展项仅在**来源记录齐备**时参与判定（缺件即不产出该项 —— 不以缺失冒充通过）。
    """
    fig = impedance_watch_figure(imp)
    drc = dfm.get("drc_as_designed") or {}
    by = drc.get("by_type") or {}
    n = drc.get("n")
    lf = sum(v for k, v in by.items() if str(k).startswith("lib_footprint") and isinstance(v, int))
    silk = by.get("silk_edge_clearance")
    out = {"impedance_watch_dev_pct": bool(fig) and _tok_match(note, f"{abs(fig['dev_pct']):.1f}%"),
           "drc_as_designed_total": isinstance(n, int) and _tok_match(note, f"{n} 项"),
           "drc_lib_footprint_sum": bool(by) and _tok_match(note, f"({lf})"),
           "drc_silk_edge_clearance": isinstance(silk, int)
                                       and _tok_match(note, f"`silk_edge_clearance`({silk})")}
    spread = impedance_spread_pct(imp)
    if spread is not None:
        out["impedance_spread_pct"] = _tok_match(note, f"spread ≈{spread:.1f}%")
    for span, cnt in (via_census_figures(dfm) if co147 is not None else {}).items():
        out[f"via_census_{span}"] = _tok_match(note, f"`{span}` {cnt}{VIA_SPAN_SUFFIX.get(span, '')}")
    if co147 is not None:
        mf = mask_clearance_figures(co147)
        if _num(mf["gap_mm"]):
            out["mask_gap_mm"] = _tok_match(note, f"{mf['gap_mm']:g}mm")
        if _num(mf["shortfall_mm"]):
            out["mask_shortfall_mm"] = _tok_match(note, f"{mf['shortfall_mm']:g}")
        if _num(mf["jlc_min_mm"]):
            out["mask_jlc_min_mm"] = _tok_match(note, f"{mf['jlc_min_mm']:g}mm")
        if _num(mf["mask_expansion_mm"]) and _num(mf["rework_gap_mm"]):
            out["mask_rework_path"] = _tok_match(
                note, f"{mf['mask_expansion_mm']:g}→{MASK_EXPANSION_REWORK_MM:g}mm")
            out["mask_rework_gap_mm"] = _tok_match(note, f"{mf['rework_gap_mm']:g}")
    if co148 is not None and co149 is not None:
        tf = thermal_figures(co148, co149)
        for key, probe in (("thermal_P_range", lambda t: f"{t['P_min_W']:.1f}–{t['P_max_W']:.1f}W"),
                           ("thermal_theta_ja_datasheet",
                            lambda t: f"θJA(high-K) {t['theta_ja_datasheet_C_per_W']:g}°C/W"),
                           ("thermal_Tj_limit", lambda t: f"Tj 上限 {t['Tj_limit_C']:g}°C"),
                           ("thermal_ta", lambda t: f"{t['ta_C']:g}°C 自然对流"),
                           ("thermal_Tj_best_worst", lambda t: f"Tj {t['Tj_best_C']:g}–{t['Tj_worst_C']:g}°C"),
                           ("thermal_psi_jb_route", lambda t: f"路线 {t['psi_jb_route_Tj_C']:g}°C")):
            try:
                out[key] = _tok_match(note, probe(tf))
            except (TypeError, ValueError):
                pass
    if cap is not None and rules is not None:
        try:
            c = cap["capability"]
            tw = c["min_track_width_mm"]["value"]
            vh = c["min_via_hole_mm"]["value"]
            vd = c["min_via_diameter_mm"]["value"]
            ann = c["via_annular_note"]["value"]
            h2h = c["via_hole_to_hole_mm"]["value"]
            edge = c["copper_edge_clearance_mm"]["value"]
            redge = rules["manufacturing"]["min_copper_edge_clearance"]
            out["jlc_min_track_width_mil"] = _tok_match(note, f"≥{tw / MIL_MM:.1f}mil")
            out["jlc_min_via_hole"] = _tok_match(note, f"孔 ≥{vh:g}")
            out["jlc_min_via_diameter"] = _tok_match(note, f"盘径 ≥{vd:g}")
            out["jlc_via_annular_note"] = _tok_match(note, f"孔径+{ann:g}")
            out["jlc_via_hole_to_hole"] = _tok_match(note, f"mm(≥{h2h:g})")
            out["rule_copper_edge_clearance"] = _tok_match(note, f"板规铜-板边 {redge:.2f}mm")
            out["jlc_copper_edge_clearance"] = _tok_match(note, f"mm(≥{edge:g})")
        except (KeyError, TypeError, ValueError):
            pass
    return out


def impedance_watch_figure(imp: dict) -> dict:
    """CO-171（G-1）：从阻抗表记录派生「watch（最宽间距）下模型相对目标的**最大偏离%**」及其来源。

    实测缺口：`ORDER_NOTES` §5 曾写死「model-spread 观察值（+11.6%）」—— 该串**不存在于任何记录**，
    而记录自身在 s=0.395mm 处 M2(HJ)=94.94Ω 对目标 85Ω 即 **+11.69%**（且「模型间 spread」≈4.8%，措辞亦失实）。
    """
    tgt = float(imp.get("target_zdiff") or 0)
    best, best_dev = {}, None
    for w in (imp.get("watch") or []):
        for model, zs in (w.get("zdiff") or {}).items():
            for z in (zs if isinstance(zs, list) else [zs]):
                if not isinstance(z, (int, float)) or tgt <= 0:
                    continue
                dev = (float(z) - tgt) / tgt * 100.0
                if best_dev is None or abs(dev) > abs(best_dev):
                    best_dev = dev
                    best = {"layer": w.get("layer"), "model": model, "gap_mm": w.get("gap_mm"),
                            "zdiff": z, "target_zdiff": tgt, "dev_pct": round(dev, 2)}
    return best


def binding_param_checks(note: str, binding: dict) -> dict:
    """CO-163（G-1）+ CO-167（F-4/F-5）：ORDER_NOTES 必须逐项含声明定值表的参数记号。"""
    t = binding_tokens(binding)
    _has = lambda tok: _tok_match(note, tok)

    # CO-167（F-4）：容差记号须出现在 zdiff 记号**邻域**内（防被厚度公差「（公差 ±10%）」误满足）
    _tol_near = False
    _m = re.search(_tok_re(t["zdiff"]), note) if t["zdiff"] else None
    if _m and t["tolerance"]:
        _tol_near = re.search(_tok_re(t["tolerance"]), note[_m.end():_m.end() + 40]) is not None
    return {"stackup": _has(t["stackup_code"]), "thickness": _has(t["thickness"]),
            "outer_copper": _has(t["outer_copper"]), "inner_copper": _has(t["inner_copper"]),
            "zdiff": _has(t["zdiff"]), "tolerance": _has(t["tolerance"]) and _tol_near,
            "surface": _has(t["surface"])}


def order_notes(spec: dict, dfm: dict, imp: dict) -> str:
    b = dfm["as_built"]
    try:
        probe_shorts = json.loads((STEP2 / "m13_v57_co146_through_via_probe.json").read_text())[
            "delta_by_type"].get("shorting_items")
    except Exception:
        probe_shorts = "N/A"
    return f"""# JLC（嘉立创）8 层打样下单备注 — k2_v4_8L.l4

> 生成：tools/p3_v57_co146_jlc_fab_package.py｜板 `{b['board_sha16']}`｜SPEC rev-19
> 定值来源：监理指令 #10「JLC 8 层打样就绪」定值表（叠层/铜厚/阻抗/表面处理/压降/环境）

## 1. 下单参数（监理定值）
| 项 | 值 |
|---|---|
| 层数 | 8 |
| 叠层 | **JLC08161H**（南亚 NP-155F） |
| 成品厚 | 1.6 mm（公差 ±10%） |
| 铜厚 | 外层 1oz / 内层 0.5oz |
| 尺寸 | {b['board_size_mm'][0]} × {b['board_size_mm'][1]} mm |
| 阻抗 | **85Ω 差分 ±10%，下单勾选「阻抗控制」** |
| 表面处理 | 沉金 ENIG |
| 文件 | Gerber RS-274X（01_）+ Excellon 钻孔（02_）+ 本叠层图（03_）+ 阻抗表（04_） |

## 2. 下单渠道（CO-147 L2 裁定 R1，生效）
本板 {b['n_non_through_vias']}/{b['n_vias']} 支过孔为**非通孔**（`F.Cu→In2.Cu` 92、`In2.Cu→In5.Cu` 88（埋孔）、
`In5.Cu→B.Cu` 32、`F.Cu→In5.Cu` 8）；JLC 公布能力页明写 *"Blind/Buried Vias Not supported … only make through holes"*，
FAQ 将 blind/buried 列为 **advanced options（须 DFM review，成本/交期上升）**。

⇒ **下单走 JLC advanced / 盲埋孔通道**（L2 自裁 = 过孔策略），随单提交：本备注 + 叠层图(03_) + 阻抗表(04_) +
L2 裁定件 `06_rulings/L2_RULING_via_channel_and_interpair_domain_v1.md`（R1/R2/R3 全文）；接受其 DFM review 与重报价。
若只接受标准通孔工艺 ⇒ 须重开 W3 **通孔化派生**（独立 L2 候选；前置 = 引擎通孔模型 + 可行性证明；
原地通孔化实测 {probe_shorts} 项 shorting_items ⇒ 不可直接降级）。

## 3. 板级 DFM 项（CO-147 L2 裁定 R3，随板厂评审提交）
**阻焊开窗-邻铜净距 1 处**：`R3.pad2`(`PWR_BTN_ISO`) 开窗缘 ↔ `PCIE_UP3_N` 铜缘 = **0.0695mm** < JLC 0.09mm
（欠 0.0205mm）。裁定 = **ACCEPT_L2_WITH_FAB_REVIEW**（并入同一工程评审；不触铜几何、不改板）。
若板厂拒绝 ⇒ 回退最小修法：R3 开窗 0.05→0.02mm（净距 → 0.0995 ≥ 0.09）+ G4 全链重基线。

## 4. 其余 DFM 项（对照 JLC 8 层能力，实测 PASS）
最小线宽 {b['min_track_width_mm']}mm(≥3.5mil)；过孔 {b['min_via_drill_mm']}/{b['min_via_diameter_mm']}mm（孔 ≥0.15、盘径 ≥0.25、环宽 0.075=JLC「盘径 ≥ 孔径+0.15」）；
孔到孔 {b['min_via_hole_to_hole_mm']}mm(≥0.2)；板规铜-板边 0.30mm(≥0.2)；层数/尺寸/铜厚/板厚/表面处理均落 JLC 能力。
逐项见包内 `06_rulings/m13_v57_co146_jlc_dfm_gate.json`。

## 5. 阻抗
85Ω 差分两套独立闭式模型（IPC-2141 族 / Hammerstad–Jensen+Cohn）均落 ±10%（as-built 对内净距），
设计名义最宽间距下有 1 项模型偏离观察值（M2(HJ) 相对目标 **+11.7%**；模型间 spread ≈4.8%），已列下单备注：
**请 JLC 阻抗表覆盖最宽对内间距（0.6mm 中心）的几何**。终判 = JLC 阻抗控制服务。
见 04_impedance/。

## 6. 系统级事项（非制造/非本单阻塞，但影响可用性）
**U6（DS320PR1601）热超限（CO-148）**：手册 PACT 4.7–7.0W / θJA(high-K) 17.4°C/W / Tj 上限 120°C；
按监理定值 40°C 自然对流 ⇒ Tj 121.8–161.8°C **全档超限**（ψJB+h 交叉路线 173.6°C）。
⇒ 须（a）系统强制风冷/顶部散热片 或（b）环境降额，并在下一轮几何修订中补强 U6 域 GND via 阵列。
详见包内 `06_rulings/L2_RULING_u6_thermal_v1.md`（缓解口径 `06_rulings/L2_RULING_u6_thermal_mitigation_v1.md`）与登记簿 HIGH 项。本板仍建议打样（散热路径实证需要实板）。

## 7. 已知板级非 DFM 事实（如实登记，非本单阻塞）
- 本板无 PTH/NPTH 焊盘：`J6/J9/J11/J12/J13` 为无焊盘占位（netlist 骨架），板上无安装孔。
- DRC（as-designed，含逃逸域 dru）：42 项，全部为 `lib_footprint_*`(41) + `silk_edge_clearance`(1)，无铜几何违规。
"""


# CO-158（H-1）：ORDER_NOTES 声明「随单提交」的附件必须**在包内**（否则下单时会静默漏交）。
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
RULINGS = [
    (L2 / "L2_RULING_via_channel_and_interpair_domain_v1.md", "L2_RULING_via_channel_and_interpair_domain_v1.md"),
    (L2 / "L2_RULING_u6_thermal_v1.md", "L2_RULING_u6_thermal_v1.md"),
    (L2 / "L2_RULING_u6_thermal_mitigation_v1.md", "L2_RULING_u6_thermal_mitigation_v1.md"),
    (STEP2 / "m13_v57_co146_jlc_dfm_gate.json", "m13_v57_co146_jlc_dfm_gate.json"),
]


def manifest(root: Path) -> dict:
    files = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.json":
            files[str(p.relative_to(root))] = {"sha256": sha256(p), "bytes": p.stat().st_size}
    return files


def main() -> int:
    spec = json.loads(SPEC.read_text())
    dfm = json.loads((STEP2 / "m13_v57_co146_jlc_dfm_gate.json").read_text())
    imp = json.loads((STEP2 / "m13_v57_co146_impedance_table.json").read_text())
    jp = json.loads(JP.read_text()) if JP.exists() else {}
    jp_binding = jp.get("binding") or {}
    if OUT.exists():
        shutil.rmtree(OUT)
    gdir, ddir = OUT / "01_gerber_rs274x", OUT / "02_drill_excellon"
    export_gerbers(gdir)
    export_drill(ddir)
    n_canon = canonicalize(gdir) + canonicalize(ddir)
    (OUT / "03_stackup").mkdir(parents=True, exist_ok=True)
    _svg = stackup_svg(spec, jp_binding)                                 # CO-170/CO-172（F-6）
    (OUT / "03_stackup" / "JLC08161H_stackup.svg").write_text(_svg)
    (OUT / "04_impedance").mkdir(parents=True, exist_ok=True)
    shutil.copy(STEP2 / "m13_v57_co146_impedance_table.md", OUT / "04_impedance/impedance_table.md")
    shutil.copy(STEP2 / "m13_v57_co146_impedance_table.json", OUT / "04_impedance/impedance_table.json")
    (OUT / "05_layer_sequence.txt").write_text(layer_sequence(spec))
    (OUT / "06_rulings").mkdir(parents=True, exist_ok=True)
    for _src, _dst in RULINGS:
        shutil.copy(_src, OUT / "06_rulings" / _dst)
    (OUT / "ORDER_NOTES.md").write_text(order_notes(spec, dfm, imp))
    m1 = manifest(OUT)
    # 幂等：重出 gerber/drill，比较
    tmpg, tmpd = OUT / "_rerun_gerber", OUT / "_rerun_drill"
    export_gerbers(tmpg); export_drill(tmpd)
    canonicalize(tmpg); canonicalize(tmpd)
    ident = True
    for sub, tmp in (("01_gerber_rs274x", tmpg), ("02_drill_excellon", tmpd)):
        for p in sorted(tmp.iterdir()):
            q = OUT / sub / p.name
            if not q.exists() or sha256(p) != sha256(q):
                ident = False
    shutil.rmtree(tmpg); shutil.rmtree(tmpd)
    gbr = sorted(p.name for p in gdir.glob("*.gbr"))
    cu = [n for n in gbr if any(n.endswith(f"-{l.replace('.', '_')}.gbr") for l in COPPER)]
    drl = sorted(p.name for p in ddir.glob("*.drl"))
    notes_txt = (OUT / "ORDER_NOTES.md").read_text()
    # CO-172：记录派生数字的全部来源记录（缺件即不产出该项判据）
    _co147 = json.loads(CO147.read_text()) if CO147.exists() else None
    _co148 = json.loads(CO148.read_text()) if CO148.exists() else None
    _co149 = json.loads(CO149.read_text()) if CO149.exists() else None
    _cap = json.loads(CAP.read_text()) if CAP.exists() else None
    _rules = json.loads(RULES.read_text()) if RULES.exists() else None
    _figs = order_notes_record_figures(notes_txt, imp, dfm, _co147, _co148, _co149, _cap, _rules)

    def _perturb(base, path, val):
        """CO-172：内存注入（零落盘）—— 沿 path 复制并改一个值，供灵敏度牙齿使用。"""
        d = copy.deepcopy(base)
        cur = d
        for k in path[:-1]:
            cur = cur[k]
        cur[path[-1]] = val
        return d
    refs = sorted(set(re.findall(r"`(06_rulings/[A-Za-z0-9_.\-]+)`", notes_txt)))
    # CO-159（F-9）：ORDER_NOTES 里的**目录级**声明（`01_`..`06_`）也须落包内（原先只覆盖 `06_rulings/*` 文件引用）
    dir_refs = sorted(set(re.findall(r"\b(0[1-6]_)", notes_txt)))
    # CO-159（F-8）：随单附件副本须与来源**内容一致**（防「来源已修订而包内副本陈旧」——J-1 同类已实测发生）
    rulings_parity = {d: (sha256(OUT / "06_rulings" / d) == sha256(src)) for src, d in RULINGS}
    # t07 灵敏度负控：不同文件必须比较为不等（否则 parity 函数恒真）
    parity_sensitivity = (sha256(OUT / "06_rulings" / RULINGS[0][1]) != sha256(OUT / "ORDER_NOTES.md"))
    teeth = {"t01_idempotent": ident,
             "t05_declared_rulings_packaged": all((OUT / "06_rulings" / d).exists() for _, d in RULINGS),
             "t06_order_notes_refs_resolve_in_package": bool(refs) and all((OUT / r).exists() for r in refs),
             "t07_packaged_rulings_match_sources": all(rulings_parity.values()),
             "t07b_parity_detector_sensitivity": parity_sensitivity,
             "t08_declared_dirs_present": bool(dir_refs) and all(any(OUT.glob(f"{d}*")) for d in dir_refs),
             # CO-163（G-1）：下单参数须与声明定值表一致（t09 正控 + t09b 灵敏度）
             "t09_order_notes_binding_params": all(binding_param_checks(notes_txt, jp_binding).values()),
             "t09b_binding_param_detector_sensitivity": (
                 not all(binding_param_checks(notes_txt.replace(binding_tokens(jp_binding).get("zdiff", "\0"), "999Ω"),
                                              jp_binding).values())),
             # CO-163（G-2）：定值来源 pin（声明表 → 监理指令件）必须可核验（t10 正控 + t10b 判据可辨）
             "t10_declared_binding_source_pinned": bool(INSTRUCTION.exists()) and bool(jp.get("supervisor_instruction"))
                 and sha16(INSTRUCTION) == jp["supervisor_instruction"].get("sha16"),
             "t10b_binding_source_pin_discriminates": bool(jp.get("supervisor_instruction"))
                 and sha16(JP) != jp["supervisor_instruction"].get("sha16"),
             # CO-170（G-1）：叠层图（03_，随单提交的制造输入）须与声明定值表绑定
             "t11_stackup_svg_declared_binding": all(stackup_svg_binding_checks(_svg, jp_binding).values()),
             "t11b_stackup_svg_binding_sensitivity": (not all(stackup_svg_binding_checks(
                 _svg, {**jp_binding, "copper": {**(jp_binding.get("copper") or {}), "outer_oz": 2.0}}).values())),
             # CO-171（G-1/G-2）：ORDER_NOTES 内的**记录派生数字**须与来源记录一致
             "t12_order_notes_record_figures": all(_figs.values()),
             "t12b_record_figure_binding_sensitivity": (not all(order_notes_record_figures(
                 notes_txt, imp, {**dfm, "drc_as_designed": {**(dfm.get("drc_as_designed") or {}), "n": 9999}},
                 _co147, _co148, _co149, _cap, _rules).values())),
             # CO-172（F-1..F-5）：逐来源记录的**灵敏度**（任一来源漂移即须判不通过）
             "t12c_impedance_spread_binding_sensitivity": (not all(order_notes_record_figures(
                 notes_txt, _perturb(imp, ["watch", 0, "zdiff", "M2_HJ_Cohn"], [100.0]),
                 dfm, _co147, _co148, _co149, _cap, _rules).values())),
             "t12d_via_census_binding_sensitivity": (not all(order_notes_record_figures(
                 notes_txt, imp,
                 _perturb(dfm, ["as_built", "via_type_census", "F.Cu->In2.Cu|BLIND_BURIED"], 93),
                 _co147, _co148, _co149, _cap, _rules).values())),
             "t12e_mask_facts_binding_sensitivity": (not all(order_notes_record_figures(
                 notes_txt, imp, dfm,
                 _perturb(_co147, ["mask_measure", "closest", "gap_mm"], 0.0694),
                 _co148, _co149, _cap, _rules).values())),
             "t12f_thermal_figures_binding_sensitivity": (not all(order_notes_record_figures(
                 notes_txt, imp, dfm, _co147, _perturb(_co148, ["worst", "Tj_C"], 165.0),
                 _co149, _cap, _rules).values())),
             "t12g_jlc_capability_binding_sensitivity": (not all(order_notes_record_figures(
                 notes_txt, imp, dfm, _co147, _co148, _co149,
                 _perturb(_cap, ["capability", "min_track_width_mm", "value"], 0.10), _rules).values())),
             "t12h_drc_rules_edge_binding_sensitivity": (not all(order_notes_record_figures(
                 notes_txt, imp, dfm, _co147, _co148, _co149, _cap,
                 _perturb(_rules, ["manufacturing", "min_copper_edge_clearance"], 0.25)).values())),
             # CO-172（F-6）：叠层图**铜厚矩形几何** vs 声明定值（正控 + 灵敏度）
             "t11c_stackup_svg_copper_geometry_binding": all(
                 stackup_svg_copper_geometry_checks(_svg, jp_binding).values()),
             "t11d_stackup_svg_copper_geometry_sensitivity": (not all(stackup_svg_copper_geometry_checks(
                 _svg, {**jp_binding, "copper": {**(jp_binding.get("copper") or {}), "outer_oz": 2.0}}).values())),
             "t02_8_copper_gerbers": len(cu) >= 8,
             "t03_drill_present": len(drl) >= 1,
             "t04_all_hashed": all(v.get("sha256") for v in m1.values())}
    rec = {"artifact": "m13_v57_co146_jlc_fab_package", "schema": 1, "revision": "CO146-PKG.8",
           "nature": "JLC 打样包（监理指令 #10 动作 3）；只出交付物，不改板/SPEC",
           "board": BOARD.name, "board_sha16": sha16(BOARD),
           "package_dir": str(OUT.relative_to(K2)), "n_files": len(m1),
           "commands": {
               "gerber": f"{CLI.name} pcb export gerbers --board-plot-params --no-x2 --layers {PLOT_LAYERS}",
               "drill": f"{CLI.name} pcb export drill --format excellon --excellon-units mm --generate-map --map-format svg --generate-report"},
           "kicad_version": subprocess.run([str(CLI), "--version"], capture_output=True, text=True).stdout.strip(),
           "gerbers": gbr, "drills": drl,
           "canonicalization": {"date_pattern": TS_PAT.pattern, "replacement": CANON_DATE,
                               "files_normalized": n_canon,
                               "reason": "KiCad 导出件内嵌墙钟时间戳 ⇒ 规范化以保证命令+sha 可复现；制造语义不受影响"},
           "stackup_svg_sha16": sha16(OUT / "03_stackup/JLC08161H_stackup.svg"),
           "teeth": teeth,
           "declared_refs": {"files": refs, "dirs": dir_refs, "rulings_parity": rulings_parity},
           "record_figures": {"impedance_watch": impedance_watch_figure(imp),
                              "impedance_spread_pct": impedance_spread_pct(imp),
                              "drc_as_designed_n": (dfm.get("drc_as_designed") or {}).get("n"),
                              "via_census": via_census_figures(dfm),
                              "mask_clearance": mask_clearance_figures(_co147) if _co147 else None,
                              "thermal": thermal_figures(_co148, _co149) if (_co148 and _co149) else None,
                              "order_notes_checks": _figs},
           "declared_binding": {"table": str(JP.relative_to(K2)), "tokens": binding_tokens(jp_binding),
                                "order_notes_checks": binding_param_checks(notes_txt, jp_binding),
                                "stackup_svg_checks": stackup_svg_binding_checks(_svg, jp_binding),
                                "stackup_svg_copper_geometry_checks": stackup_svg_copper_geometry_checks(_svg, jp_binding),
                                "record_figure_sources": {"co147": str(CO147.relative_to(K2)), "co148": str(CO148.relative_to(K2)),
                                                          "co149": str(CO149.relative_to(K2)), "jlc_capability": str(CAP.relative_to(K2)),
                                                          "drc_rules": str(RULES)},
                                "source_instruction": {"path": str(INSTRUCTION), "available": INSTRUCTION.exists(),
                                                       "declared_sha16": (jp.get("supervisor_instruction") or {}).get("sha16")}},
           "orderable_at_jlc_standard": not dfm["fails"],
           "blockers": dfm["fails"],
           "manifest": m1,
           "redline": "只读板；零坐标搜索；不改板/图纸/SPEC/冻结四源（输出全在 L5 交付目录）。"}
    (OUT / "MANIFEST.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    (STEP2 / "m13_v57_co146_jlc_fab_package.json").write_text(json.dumps(
        {k: v for k, v in rec.items() if k != "manifest"}, ensure_ascii=False, indent=1) + "\n")
    print("files:", len(m1), "| gerbers:", len(gbr), "| copper gerbers:", len(cu), "| drills:", len(drl))
    print("teeth:", teeth)
    print("package:", OUT)
    return 0 if all(teeth.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
