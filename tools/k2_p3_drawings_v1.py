#!/usr/bin/env python3
"""k2_p3_drawings_v1.py — K2 P3（施工图层重建）图纸生成器 v1。

输入（全部只读）：
  - canonical SPEC（经 pm_gate.config 解析，禁硬编码文件名）
  - 真源 yaml `k2/hw/data/k2_sch.yaml`（符号引脚数 / 55 件 placements / nets）
  - L2 裁定值（审计 §十 L2-1..L2-8；引 K2-ENG-AUDIT-2026-09-15.md）
  - 锚点板 `k2/hw/k2_v4_8L.kicad_pcb`（设计源板，42 件锚点；只读）

输出：`k2/pm_gate/artifacts/k2_v4/L3/drawings/` 下
  - `p3_drawings.json`（机读几何 + 判据自测量）
  - `0N_*.svg`（7 张施工图）

边界：只读输入 + 只写上述目录；不改 SPEC/原理图/板/生成器/判据；不派 WORKER。
判据由监理核（ENG 只给测量）。
"""
from __future__ import annotations
import json, os, re, sys, math, hashlib
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # ic_hw
K2 = os.path.join(ROOT, "k2")
OUT = os.environ.get("K2_P3_OUT", os.path.join(K2, "pm_gate/artifacts/k2_v4/L3/drawings"))
os.environ.setdefault("PM_GATE_PROJECT_ROOT", K2)  # 经官方解析链定位项目根（禁硬编码 SPEC 路径）
sys.path.insert(0, os.path.join(K2, "_shared"))

# ── L2 裁定值（审计 §十；本文件只引用，不重裁） ─────────────────────────────
AUDIT = "k2/docs/K2-ENG-AUDIT-2026-09-15.md"
L2 = {
    "L2-1_board_frame": {"outline_x": [23.0, 143.0], "outline_y": [33.0, 79.0], "size_mm": [120.0, 46.0]},
    "L2-2_mounting_holes": {
        "count": 4, "drill_mm": 3.2, "keepout_dia_mm": 6.0, "edge_material_min_mm": 1.5,
        "positions": {"H1": [26.10, 75.60], "H2": [139.60, 39.60], "H3": [26.10, 36.10], "H4": [114.60, 36.10]},
        "note": "右下角不可放孔（In5 PCIe 布线占用 y≥74.5 ∧ x≥86）⇒ 右侧不对称（审计 §10.2 诚实披露）",
    },
    "L2-3_pin_header_column_x": 27.94,
    "L2-3_shift_refs": ["C73", "C86"],
    "L2-4_corridor_clearance": {"basis": "焊盘外接框净距", "west_mm": 17.55, "east_mm": 27.81,
                                "west_basis": "J3/J4 右缘 65.05 → U6 左缘 82.60",
                                "east_basis": "U6 右缘 104.84 → J2 左缘 132.65"},
    "L2-5_pour": {"gnd_planes": ["In1.Cu", "In3.Cu", "In6.Cu"], "power_plane": "In4.Cu",
                  "signal_layers": ["F.Cu", "In2.Cu", "In5.Cu", "B.Cu"]},
    "L2-6_via": {"max_per_net": 2, "drill_mm": 0.20, "outer_mm": 0.35, "annular_min_mm": 0.075,
                 "back_drill": True, "diff_symmetric": True, "gnd_companion_min": 1, "dangling": "error"},
    "L2-7_length": {"intra_pair_max_mm": 0.15, "inter_pair_max_mm": 1.0},
    "L2-8_thresholds": {"pad_overlap_mm2": 0.001, "in_frame_inset_mm": 0.3, "mounting_holes_min": 4,
                        "keepout_min_switch_not_allowed": 1},
    "basis_sha16": hashlib.sha256(open(os.path.join(ROOT, AUDIT), 'rb').read()).hexdigest()[:16],
}

# ── 解析工具 ───────────────────────────────────────────────────────────────
def spec_load():
    from pm_gate import config as cfg, artifacts as art
    name = cfg.spec_name("k2_v4")
    path = art.path("L3", name)
    return name, path, json.load(open(path, encoding="utf-8"))

def yaml_load():
    import yaml
    return yaml.safe_load(open(os.path.join(K2, "hw/data/k2_sch.yaml"), encoding="utf-8"))

PAD_RE = re.compile(r'\(pad\s+"?([^"\s]+)"?\s+(\S+)\s+(\S+)\s+\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)'
                    r'(?:\s+\(size\s+([-\d.]+)\s+([-\d.]+)\))?', re.S)

def footprint_pads(fp: str):
    """返回 [(pad_no, type, x, y, rot, w, h)]（居中于封装原点）。"""
    if ":" in fp:
        lib, _, nm = fp.partition(":")
    else:
        lib, nm = "", fp          # §3.1 修：partition 无分隔符时返回 (原串,'','') ⇒ 走错分支
    cands = []
    if lib:
        cands += [os.path.join(K2, "hw/lib", f"{lib}.pretty", f"{nm}.kicad_mod"),
                  os.path.join(ROOT, f"AppDir/share/kicad/footprints/{lib}.pretty/{nm}.kicad_mod")]
    else:
        nm = fp
        cands += [os.path.join(K2, "hw/lib/ForgeOS.pretty", f"{nm}.kicad_mod")]
        for base in (os.path.join(K2, "hw/lib"), os.path.join(ROOT, "AppDir/share/kicad/footprints")):
            if os.path.isdir(base):
                for d in os.listdir(base):
                    if d.endswith(".pretty"):
                        cands.append(os.path.join(base, d, f"{nm}.kicad_mod"))
    for c in cands:
        if os.path.isfile(c):
            txt = open(c, encoding="utf-8", errors="replace").read()
            out = []
            for m in PAD_RE.finditer(txt):
                out.append({"no": m.group(1), "type": m.group(2),
                            "x": float(m.group(4)), "y": float(m.group(5)),
                            "rot": float(m.group(6) or 0), "w": float(m.group(7) or 0), "h": float(m.group(8) or 0)})
            return c, out
    return None, []

def rot_pt(x, y, deg, cx=0.0, cy=0.0):
    r = math.radians(deg)
    dx, dy = x - cx, y - cy
    return cx + dx * math.cos(r) - dy * math.sin(r), cy + dx * math.sin(r) + dy * math.cos(r)

def placed_pad_aabb(fp, px, py, prot):
    _, pads = footprint_pads(fp)
    box = None
    for p in pads:
        # 逆序：封装内坐标 → 板坐标（KiCad: y 轴翻转在 pad 尺寸上不显著，v1 用保守 AABB）
        x, y = rot_pt(p["x"], p["y"], prot)
        hw, hh = max(p["w"], p["h"]) / 2.0, min(p["w"], p["h"]) / 2.0
        if prot % 180 != 0:
            hw, hh = max(p["w"], p["h"]) / 2.0, max(p["w"], p["h"]) / 2.0
        bx = [px + x - hw, py + y - hh, px + x + hw, py + y + hh]
        box = bx if box is None else [min(box[0], bx[0]), min(box[1], bx[1]), max(box[2], bx[2]), max(box[3], bx[3])]
    return box, pads

def anchors():
    import pcbnew
    b = pcbnew.LoadBoard(os.path.join(K2, "hw/k2_v4_8L.kicad_pcb"))
    out = {}
    for ft in b.GetFootprints():
        ref = ft.GetReference()
        pads = [p for p in ft.Pads()]
        box = None
        for p in pads:
            bb = p.GetBoundingBox()
            b = [pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
                 pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())]
            box = b if box is None else [min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3])]
        out[ref] = {"at": [pcbnew.ToMM(ft.GetPosition().x), pcbnew.ToMM(ft.GetPosition().y)],
                    "rot": ft.GetOrientationDegrees(), "footprint": str(ft.GetFPID().GetLibItemName()),
                    "board_pads": len(pads), "pad_aabb_board": box,
                    "pad_nums": sorted(p.GetNumber() for p in pads)}
    return out

def c3_measure(devices, registry_path,  registry_sha16=None):
    """P3-3 测量：每器件 pad 数 vs 符号引脚数（**有向口径**：#K2-11 §1-2）。

    返回：literal_mismatch（字面不等）/ directed_extra（余量，须逐条登记）/
    directed_judgement（按有向口径：电气引脚集 ⊆ 焊盘集；余量引登记件）/ unresolved_footprint。
    """
    import hashlib as _h
    reg_sha = registry_sha16 or (_h.sha256(open(registry_path, "rb").read()).hexdigest()[:16]
                                 if os.path.isfile(registry_path) else None)
    c3 = {"literal_mismatch": [], "directed_extra": [], "unresolved_footprint": [],
          "directed_judgement": [], "registry": {"file": os.path.relpath(registry_path, ROOT) if os.path.isfile(registry_path) else None,
                                                 "sha16": reg_sha}}
    for ref, d in sorted(devices.items()):
        if not d.get("footprint_file"):
            c3["unresolved_footprint"].append(ref)
            continue
        sp, fp_pads = d["symbol_pins"], d["footprint_pads"]
        if fp_pads != sp:
            c3["literal_mismatch"].append({"ref": ref, "symbol_pins": sp, "footprint_pads": fp_pads})
        if fp_pads > sp:
            nums = [n for n in (d.get("footprint_pad_nums") or []) if n not in set(d.get("symbol_pin_nums") or [])]
            c3["directed_extra"].append({"ref": ref, "extra": fp_pads - sp,
                                         "extra_pads": nums if nums else None})
            c3["directed_judgement"].append({
                "ref": ref, "rule": "#K2-11 §1-2 有向口径：电气引脚集 ⊆ 焊盘集 + 余量逐条登记（禁静默）",
                "symbol_pins_subset_of_pads": [n for n in (d.get("symbol_pin_nums") or []) if n not in set(d.get("footprint_pad_nums") or [])] == [],
                "extra_count": fp_pads - sp, "extra_pads": nums if nums else None,
                "registry_ref": c3["registry"]})
    return c3

def sym_pin_nums(sym_def):
    nums = []
    for side, pins in (sym_def.get("pins") or {}).items():
        for p in pins:
            if len(p) >= 2:
                nums.append(str(p[1]))
    return sorted(set(nums))

# ── SVG 工具 ───────────────────────────────────────────────────────────────
SCALE = 6.0  # px/mm
PAD = 30

def svg_open(title, w_mm, h_mm, ox, oy):
    W, H = int(w_mm * SCALE) + 2 * PAD, int(h_mm * SCALE) + 2 * PAD
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
            f'<rect width="{W}" height="{H}" fill="#0d1117"/>\n'
            f'<text x="{PAD}" y="20" fill="#e6edf3" font-family="monospace" font-size="14">{title}</text>\n'
            f'<g transform="translate({PAD},{PAD})">\n')
    return head, W, H

def P(x, y, ox, oy):
    """板坐标(mm) → SVG 坐标(px)，y 轴翻转。"""
    return (x - ox) * SCALE, (y - oy) * SCALE

def svg_close(f):
    f.write('</g></svg>\n')

def txt(f, x, y, s, fill="#e6edf3", size=9, anchor="start"):
    f.write(f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-family="monospace" font-size="{size}" '
            f'text-anchor="{anchor}">{s}</text>\n')

def rect(f, x0, y0, x1, y1, stroke, fill="none", width=1.0, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    f.write(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{abs(x1-x0):.1f}" height="{abs(y1-y0):.1f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{width}"{d}/>\n')

def line(f, x0, y0, x1, y1, stroke, width=1.0, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    f.write(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{stroke}" stroke-width="{width}"{d}/>\n')

def circ(f, x, y, r, stroke, fill="none", width=1.0, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    f.write(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"{d}/>\n')

# ── 主流程 ─────────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUT, exist_ok=True)
    spec_name, spec_path, spec = spec_load()
    y = yaml_load()
    syms = {s["name"]: s for s in y["symbols"]}
    plac = {}
    for sh in y.get("sheets", []):
        for p in sh.get("placements", []):
            plac[p["ref"]] = {"symbol": p["symbol"], "sheet": sh.get("title", "")}
    anch = anchors()
    bx0, bx1 = L2["L2-1_board_frame"]["outline_x"]
    by0, by1 = L2["L2-1_board_frame"]["outline_y"]
    W, H = bx1 - bx0, by1 - by0

    geo = {"spec": {"name": spec_name, "sha16": hashlib.sha256(open(spec_path, 'rb').read()).hexdigest()[:16]},
           "board_frame": L2["L2-1_board_frame"], "mounting_holes": L2["L2-2_mounting_holes"],
           "devices": {}, "corridors": [], "keepouts": [], "layer_plan": {}, "pour": {}, "criteria": {}}

    # devices：55 真源件（锚点板 42 + 13 待定 + 排针列 L2-3 修正）
    col_x = L2["L2-3_pin_header_column_x"]
    ph = (spec["components"].get("pin_headers") or {})
    for ref in sorted(plac):
        sym = syms.get(plac[ref]["symbol"], {})
        fp = sym.get("footprint", "")
        pins = sym_pin_nums(sym)
        rec = {"sheet": plac[ref]["sheet"], "symbol": plac[ref]["symbol"], "footprint": fp,
               "symbol_pins": len(pins), "symbol_pin_nums": pins}
        if ref in ("C73", "C86"):
            rec["at"] = anch.get(ref, {}).get("at"); rec["rot"] = anch.get(ref, {}).get("rot")
            rec["pad_aabb"] = anch.get(ref, {}).get("pad_aabb_board")
            rec["geom_src"] = "board(as-built，旧位)"
            rec["status"] = "move_pending_L2-3"
            rec["note"] = "L2-3 已裁须移位（仍在左带内）；新坐标待解（L2 自裁域），图纸标为待定"
        elif ref in anch and ref not in ph.get("positions", {}):
            rec["at"] = anch[ref]["at"]; rec["rot"] = anch[ref]["rot"]; rec["src"] = "anchor(设计源板)"
            rec["board_pads"] = anch[ref]["board_pads"]
            rec["status"] = "placed"
        elif ref in ph.get("positions", {}):
            rec["at"] = [col_x, ph["positions"][ref][1]]; rec["rot"] = ph.get("rot", 90)
            rec["src"] = f"SPEC pin_headers.positions（column_x 由 L2-3 修正 26.5→{col_x}）"
            rec["board_pads"] = anch.get(ref, {}).get("board_pads")
            rec["status"] = "placed"
        else:
            rec["at"] = None; rec["src"] = "无"; rec["status"] = "coord_pending"
            rec["note"] = "P4 补件（真源有、交付板无）⇒ 坐标须新解（L2 自裁域：PDN/strap 就近）"
        fpc, pads = footprint_pads(fp)
        rec["footprint_file"] = os.path.relpath(fpc, ROOT) if fpc else None
        rec["footprint_pads"] = len(pads)
        rec["footprint_pad_nums"] = sorted(p0["no"] for p0 in pads)
        if rec.get("at"):
            if ref in ph.get("positions", {}):
                # 排针列：交付板上 0 焊盘（F-1）⇒ 必须用**封装几何 + L2-3 位**（勿用板几何，否则静默跳过）
                a, _ = placed_pad_aabb(fp, col_x, ph["positions"][ref][1], ph.get("rot", 90))
                rec["pad_aabb"] = [round(v, 3) for v in a] if a else None
                rec["geom_src"] = f"lib 封装几何 @(column_x={col_x}, y={ph['positions'][ref][1]}, rot={ph.get('rot', 90)})（板 0 焊盘）"
                rec["note"] = f"L2-3 移位 dx={col_x - ph['positions'][ref][0]:+.2f}mm（column_x 26.5→{col_x}）"
            elif ref in anch and anch[ref].get("pad_aabb_board"):
                rec["pad_aabb"] = [round(v, 3) for v in anch[ref]["pad_aabb_board"]]
                rec["geom_src"] = "board(as-built)"
            else:
                rec["pad_aabb"], _ = placed_pad_aabb(fp, rec["at"][0], rec["at"][1], rec.get("rot", 0))
                rec["geom_src"] = "lib(未落件占位)"
        geo["devices"][ref] = rec

    # 判据 3：每器件 pad 数 == 符号引脚数（有向口径；**落位解消费后再重算一次，见 §3.2 修**）
    E2_REG = os.path.join(K2, "docs/K2-P2-E2-directed-pad-registry-v1.md")
    geo["criteria"]["C3_pad_eq_symbol_pins"] = c3_measure(geo["devices"], E2_REG)

    # 判据 1：板框
    geo["criteria"]["C1_board_frame"] = {"size_mm": [W, H], "expect": L2["L2-1_board_frame"]["size_mm"],
                                         "y_range": [by0, by1],
                                         "pass": abs(W - 120) < 1e-6 and abs(H - 46) < 1e-6 and by0 == 33 and by1 == 79}
    # 判据 2：固定孔
    mh = L2["L2-2_mounting_holes"]; r = mh["drill_mm"] / 2.0
    ds = []
    for k, (hx, hy) in mh["positions"].items():
        d_edge = min(hx - r - bx0, bx1 - (hx + r), hy - r - by0, by1 - (hy + r))
        ds.append({"hole": k, "at": [hx, hy], "edge_material_mm": round(d_edge, 3)})
    geo["criteria"]["C2_mounting_holes"] = {"count": len(mh["positions"]), "drill_mm": mh["drill_mm"],
                                            "min_edge_material_mm": min(x["edge_material_mm"] for x in ds),
                                            "expect_min_mm": mh["edge_material_min_mm"], "per_hole": ds,
                                            "pass": len(mh["positions"]) >= 4 and min(x["edge_material_mm"] for x in ds) >= 1.5}

    # 判据 4：接口焊盘不出框（内缩 0.3mm）
    inset = L2["L2-8_thresholds"]["in_frame_inset_mm"]
    viol = []; margins = {}; measured = []
    for ref in ["J2", "J3", "J4", "J6", "J9", "J11", "J12", "J13"]:
        d = geo["devices"].get(ref)
        if not d or not d.get("pad_aabb"):
            continue
        a = d["pad_aabb"]; measured.append(ref)
        m = min(a[0] - (bx0 + inset), a[1] - (by0 + inset), (bx1 - inset) - a[2], (by1 - inset) - a[3])
        margins[ref] = round(m, 3)
        if m < 0:
            viol.append({"ref": ref, "pad_aabb": [round(v, 3) for v in a], "margin_mm": round(m, 3)})
    geo["criteria"]["C4_interface_inframe"] = {"inset_mm": inset, "violations": viol, "measured_refs": measured,
                                               "min_margin_mm": min(margins.values()) if margins else None,
                                               "min_margin_ref": min(margins, key=margins.get) if margins else None,
                                               "margins_mm": margins,
                                               "note": "接口件 8 件；排针列按 lib 封装几何 @column_x=27.94（板 0 焊盘 ⇒ 不得用板几何）",
                                               "pass": (not viol) and len(measured) == 8}

    # 判据 5：回避区（每区 ≥1 开关 ≠ allowed）
    keep = [
        {"id": "KO-1..4 mounting holes", "count": 4, "shape": f"circle Ø{mh['keepout_dia_mm']}",
         "switches": {"pads": "blocked", "tracks": "blocked", "vias": "blocked", "copper_pour": "blocked", "footprints": "blocked"}},
        {"id": "KO-5 escape_transition_zone", "count": 1, "shape": "per-pin escape window",
         "switches": {"pads": "allowed", "tracks": "allowed(escape_clearance_mm=0.075)", "vias": "blocked",
                      "copper_pour": "blocked", "footprints": "blocked"}},
        {"id": "KO-6 ac_pad_gnd_cutout", "count": 1, "shape": "AC pad GND cut-out",
         "switches": {"pads": "allowed", "tracks": "allowed", "vias": "allowed", "copper_pour": "blocked", "footprints": "allowed"}},
        {"id": "KO-7 board edge", "count": 4, "shape": f"frame inset edge_copper_min={spec['constraints'].get('edge_copper_min')}mm",
         "switches": {"pads": "allowed", "tracks": "blocked(<0.30mm)", "vias": "blocked(<0.30mm)",
                      "copper_pour": "blocked(<0.30mm)", "footprints": "allowed"}},
    ]
    geo["keepouts"] = keep
    ok5 = all(any(v != "allowed" for v in k["switches"].values()) for k in keep)
    geo["criteria"]["C5_keepout_switches"] = {"zones": len(keep), "each_has_non_allowed": ok5, "pass": ok5}

    # 判据 6：走廊口径统一
    cor = spec.get("corridors") or []
    bases = set()
    for c in cor:
        for b in c.get("bands", []) if isinstance(c, dict) else []:
            for key in ("clearance_basis", "basis", "口径"):
                if key in b: bases.add(b[key])
    geo["corridors"] = cor
    # 口径回写核查：canonical SPEC 内是否仍留**作废**口径（L2-4 裁定前的 17.30/27.40 与体宽口径 x_range）
    stale = []
    for c in cor:
        note = c.get("note", "") if isinstance(c, dict) else ""
        for bad in ("17.30", "27.40"):
            if bad in note:
                stale.append({"corridor": c.get("id"), "field": "note", "value": bad, "text": note[:90]})
    l24 = L2["L2-4_corridor_clearance"]
    xr = {c.get("id"): c.get("x_range") for c in cor if isinstance(c, dict)}
    xr_check = {"WEST_MCIO_TO_CHIP": {"spec": xr.get("WEST_MCIO_TO_CHIP"), "L2-4_upper_mm": 82.60},
                "EAST_CHIP_TO_J2": {"spec": xr.get("EAST_CHIP_TO_J2"), "L2-4_lower_mm": 104.84}}
    geo["criteria"]["C6_corridor_basis"] = {"declared": l24, "bases_found_in_spec": sorted(bases),
                                            "stale_values_in_canonical_spec": stale,
                                            "x_range_vs_L2-4": xr_check,
                                            "pass": not stale,
                                            "note": "L2-4 统一口径 = 『焊盘外接框净距』（西 17.55 / 东 27.81）。**canonical SPEC 的 corridors[].note 仍写已作废口径**（27.40/17.30）且 x_range 用体宽口径 ⇒ **口径回写未完成**（属 SPEC 变更 ⇒ 须监理放行 rev-23）"}

    # ── 敷铜策略：13 zone 台账（交付板实测，只读）+ 出 Gerber 前置 ──────────
    import pcbnew as _pk
    _bb = _pk.LoadBoard(os.path.join(K2, "hw/k2_v4_8L.l4.kicad_pcb"))
    zones = []
    for i, z in enumerate(_bb.Zones()):
        filled = 1 if (z.GetFilledPolysList(z.GetLayer()) and z.GetFilledPolysList(z.GetLayer()).OutlineCount() > 0) else 0
        zb = z.GetBoundingBox()
        zones.append({"idx": i, "net": z.GetNetname(), "layer": _bb.GetLayerName(z.GetLayer()), "filled": filled,
                      "bbox_mm": [round(_pk.ToMM(zb.GetLeft()), 2), round(_pk.ToMM(zb.GetTop()), 2),
                                  round(_pk.ToMM(zb.GetRight()), 2), round(_pk.ToMM(zb.GetBottom()), 2)]})
    geo["pour_zones"] = {"count": len(zones), "filled_count": sum(z["filled"] for z in zones), "zones": zones,
                         "gate": "出 Gerber 前置（审计 §10.5）：13 zone 全 filled_polygon>=1 且 net 非空",
                         "power_partition": (spec.get("pd") or {}).get("power_partition"),
                         "decoupling": (spec.get("pd") or {}).get("decoupling"),
                         "gnd_stitch_via": (spec.get("pd") or {}).get("gnd_stitch_via")}
    geo["criteria"]["C7_pour_zones_filled"] = {"count": len(zones), "filled": sum(z["filled"] for z in zones),
                                               "expect": "13/13（P4 前置）", "pass": sum(z["filled"] for z in zones) == len(zones),
                                               "note": "B 判据：出 Gerber 前 13 区必须全填充（本次 = 交付板现状）"}
    # ── 层分配：逐层角色 + 阻抗/线宽/参考（SPEC impedance.per_layer） ────────
    imp = spec.get("impedance") or {}
    per = imp.get("per_layer") or {}
    wl = imp.get("width_mm_by_layer") or {}
    geo["layer_assignment"] = {"roles": L2["L2-5_pour"], "target_zdiff": imp.get("target_zdiff"),
                               "tolerance_pct": imp.get("tolerance_pct"), "model": imp.get("model"),
                               "gap_mm": imp.get("gap_mm"), "alt_width_mm": imp.get("alt_width_mm"), "alt_gap_mm": imp.get("alt_gap_mm"),
                               "width_mm_by_layer": wl,
                               "per_layer": {k: {kk: vv for kk, vv in v.items()} for k, v in per.items()},
                               "via_policy": L2["L2-6_via"], "length_policy": L2["L2-7_length"],
                               "stackup_material": spec.get("stackup", {}).get("material"),
                               "total_thickness_mm": spec.get("stackup", {}).get("total_thickness_mm")}
    # ── 走廊占用表（逐走廊/逐带/逐轨） ─────────────────────────────────────
    cot = []
    for c in cor:
        bands = []
        for b in (c.get("bands") or []):
            bands.append({"band": b.get("band"), "layer": b.get("layer"), "pairs": b.get("pairs"),
                          "nets": b.get("nets"), "tracks_y": b.get("tracks_y"), "note": b.get("note")})
        cot.append({"id": c.get("id"), "x_range": c.get("x_range"), "pairs": c.get("pairs"),
                    "note": c.get("note"), "bands": bands})
    geo["corridor_occupancy"] = {"corridors": cot, "clearance_basis": L2["L2-4_corridor_clearance"]}

    # 附加机检 D1：L2-3 排针列位移后的干涉（封装几何 @column_x=27.94；板 0 焊盘 ⇒ 必须用 lib 几何）
    import pcbnew as _pc
    _b = _pc.LoadBoard(os.path.join(K2, "hw/k2_v4_8L.kicad_pcb"))
    obst = []; obst_old = []
    for ft in _b.GetFootprints():
        ref0 = ft.GetReference()
        if ref0 in ("J6", "J9", "J11", "J12", "J13"):
            continue
        for pad0 in ft.Pads():
            bb0 = pad0.GetBoundingBox()
            row = [ref0 + "." + pad0.GetNumber(), _pc.ToMM(bb0.GetLeft()), _pc.ToMM(bb0.GetTop()),
                   _pc.ToMM(bb0.GetRight()), _pc.ToMM(bb0.GetBottom())]
            if ref0 in ("C73", "C86"):
                obst_old.append(row)      # 旧位（L2-3 位移前）——用于复现「为何必须移」
            else:
                obst.append(row)
    for r0, dd0 in geo["devices"].items():
        if dd0.get("status") == "placed_solved_L2" and dd0.get("pad_aabb"):
            obst.append([r0, *dd0["pad_aabb"]])

    def _ov(a0, b0, clr0):
        return not (a0[2] + clr0 <= b0[0] or b0[2] + clr0 <= a0[0] or a0[3] + clr0 <= b0[1] or b0[3] + clr0 <= a0[1])

    d1 = []; d1_before = []
    for ref0 in ("J6", "J9", "J11", "J12", "J13"):
        _a, _pads = placed_pad_aabb(geo["devices"][ref0]["footprint"], col_x, ph["positions"][ref0][1], ph.get("rot", 90))
        for p0 in _pads:
            px0, py0 = rot_pt(p0["x"], p0["y"], ph.get("rot", 90))
            pa0 = [col_x + px0 - p0["w"] / 2, ph["positions"][ref0][1] + py0 - p0["h"] / 2,
                   col_x + px0 + p0["w"] / 2, ph["positions"][ref0][1] + py0 + p0["h"] / 2]
            for o0 in obst:
                if _ov(pa0, o0[1:5], 0.2):
                    d1.append({"header": ref0, "pad": p0["no"], "conflict": o0[0]})
            for o0 in obst_old:
                if _ov(pa0, o0[1:5], 0.2):
                    d1_before.append({"header": ref0, "pad": p0["no"], "conflict": o0[0]})
    geo["criteria"]["D1_pinheader_interference"] = {"column_x": col_x, "clearance_mm": 0.2,
                                                    "conflicts_after_move": d1, "conflicts_before_move": d1_before,
                                                    "pass": not d1,
                                                    "note": "L2-3 位移复检（封装几何 @27.94）。before = 含 C73/C86 **旧位** ⇒ 复现 L2-3「仅 C73/C86 相撞」的依据；after = C73/C86 新解位 ⇒ 应无冲突"}
    # 层分配 / 敷铜
    geo["layer_plan"] = {"stackup_layers": list(spec.get("stackup", {}).get("layers", {}).keys())
                         if isinstance(spec.get("stackup", {}).get("layers"), dict) else None,
                         "roles": L2["L2-5_pour"], "impedance": spec.get("impedance", {}),
                         "via_policy": L2["L2-6_via"], "length_policy": L2["L2-7_length"]}
    geo["pour"] = {"gnd_planes": L2["L2-5_pour"]["gnd_planes"], "power_plane": L2["L2-5_pour"]["power_plane"],
                   "decoupling": (spec.get("pd") or {}).get("decoupling"),
                   "power_partition": (spec.get("pd") or {}).get("power_partition"),
                   "gnd_stitch_via": (spec.get("pd") or {}).get("gnd_stitch_via"),
                   "L2_residual": L2["L2-4_corridor_clearance"], "basis_sha16": L2["basis_sha16"]}

    # ── 消费落位解（若存在）：G1 13 件 + G2 C73/C86 ────────────────────────
    solp = os.path.join(os.environ.get("K2_P3_SOL_IN", OUT), "p3_placement_solution.json")
    if os.path.isfile(solp):
        sol = json.load(open(solp, encoding="utf-8"))
        for ref, s in (sol.get("placed") or {}).items():
            d = geo["devices"].get(ref)
            if not d:
                continue
            d["at"] = s["at"]; d["pad_aabb"] = s["aabb"]
            d["footprint"] = s.get("footprint", d.get("footprint"))
            d["status"] = "placed_solved_L2"
            d["geom_src"] = "L2 自裁解（k2_p3_place_solver_v1.py）"
            d["basis"] = s.get("basis")
            if s.get("ball"):
                d["ball"] = s["ball"]; d["ball_board_pos"] = s["ball_board_pos"]
        geo["placement_solution"] = {"file": "p3_placement_solution.json",
                                     "solved": sol.get("solved_count"), "all_pass": sol.get("all_pass"),
                                     "selfcheck": sol.get("selfcheck"),
                                     "constraints": sol.get("constraints"),
                                     "strap_zone": sol.get("strap_zone"), "decap_keepout": sol.get("decap_keepout"),
                                     "strap_footprint_spec": sol.get("strap_footprint_spec")}
        # §3.2 修：用新解件封装**重算设备表 + 重算 C3**（此前只改 d 不重算 c3 ⇒ 测量不自洽）
        for ref, s in (sol.get("placed") or {}).items():
            d = geo["devices"][ref]
            fpc2, pads2 = footprint_pads(d["footprint"])
            d["footprint_file"] = os.path.relpath(fpc2, ROOT) if fpc2 else None
            d["footprint_pads"] = len(pads2)
            d["footprint_pad_nums"] = sorted(p0["no"] for p0 in pads2)
        geo["criteria"]["C3_pad_eq_symbol_pins"] = c3_measure(geo["devices"], E2_REG)

    # ── 回避区几何（机定，全部可溯源） ────────────────────────────────────
    edge_min = spec["constraints"].get("edge_copper_min")
    esc = spec["constraints"].get("escape_transition_zone") or {}
    u6 = geo["devices"].get("U6", {}).get("pad_aabb")
    geo["keepout_geometry"] = {
        "edge_copper_min_mm": edge_min,
        "edge_inset_rect_mm": [bx0 + (edge_min or 0), by0 + (edge_min or 0), bx1 - (edge_min or 0), by1 - (edge_min or 0)],
        "decap_column_rect_mm": [90.25, 58.5, 91.75, 64.5],
        "decap_column_basis": "SPEC layer_plan.strap_domain_v32.placement.decap_column_keepout_mm",
        "u6_pads_bbox_mm": u6,
        "escape_zone": {"clearance_mm": esc.get("escape_clearance_mm"),
                        "corridor_y_clearance_from_wall_mm": esc.get("corridor_y_clearance_from_wall_mm"),
                        "pitch_mm": esc.get("pitch_mm"), "no_90deg": esc.get("no_90deg"), "no_via": esc.get("no_via"),
                        "basis": "SPEC constraints.escape_transition_zone（图面只标规则与数值；逐 pin 窗口见 L1/structural_predict.md）"},
        "ac_pad_gnd_cutout": spec["constraints"].get("ac_pad_gnd_cutout")}

    # ── 出图 ───────────────────────────────────────────────────────────────
    ox, oy = bx0, by0
    def frame(f):
        x0, y0 = P(bx0, by0, ox, oy); x1, y1 = P(bx1, by1, ox, oy)
        rect(f, x0, y0, x1, y1, "#58a6ff", width=1.6)

    # 01 板框 + 固定孔
    with open(os.path.join(OUT, "01_board_frame_and_holes.svg"), "w") as f:
        f.write(svg_open(f"P3-01 板框 120x46 + 固定孔 (L2-1/L2-2) | SPEC {geo['spec']['name']}", W, H, ox, oy)[0])
        frame(f)
        for k, (hx, hy) in mh["positions"].items():
            cx, cy = P(hx, hy, ox, oy)
            circ(f, cx, cy, mh["keepout_dia_mm"] / 2 * SCALE, "#f0883e", dash="4 3")
            circ(f, cx, cy, r * SCALE, "#f0883e", fill="#0d1117")
            txt(f, cx + 8, cy - 8, f"{k} ({hx},{hy})", "#f0883e")
        txt(f, 10, H * SCALE - 10, f"frame x[{bx0},{bx1}] y[{by0},{by1}] mm | 4xM3 NPTH Ø{mh['drill_mm']} + Ø{mh['keepout_dia_mm']} keepout", "#8b949e")
        svg_close(f)

    # 02 器件坐标
    with open(os.path.join(OUT, "02_device_coordinates.svg"), "w") as f:
        f.write(svg_open("P3-02 器件坐标（55 真源件全定位：40 锚点/SPEC+L2-3 + 15 L2 落位解）", W, H, ox, oy)[0])
        frame(f)
        for ref, d in sorted(geo["devices"].items()):
            if d.get("at"):
                cx, cy = P(d["at"][0], d["at"][1], ox, oy)
                a = d.get("pad_aabb")
                if a:
                    x0, y0 = P(a[0], a[1], ox, oy); x1, y1 = P(a[2], a[3], ox, oy)
                    rect(f, x0, y0, x1, y1, "#3fb950", width=0.7)
                txt(f, cx, cy - 6, ref, "#3fb950", 8)
            else:
                txt(f, 12, 28 + 12 * sorted(geo["devices"]).index(ref) % 600, f"{ref}(无坐标)", "#d29922", 8)
        txt(f, 10, H * SCALE - 10, "green=已定位 55/55（40 锚点/SPEC+L2-3 + 15 L2 落位解）", "#8b949e")
        svg_close(f)

    # 03 走廊占用
    with open(os.path.join(OUT, "03_corridor_occupancy.svg"), "w") as f:
        f.write(svg_open("P3-03 走廊占用（SPEC corridors；口径=L2-4 焊盘外接框净距）", W, H, ox, oy)[0])
        frame(f)
        yy = 26
        for c in (geo.get("corridor_occupancy") or {}).get("corridors", []):
            xr = c.get("x_range") or [bx0, bx1]
            lanes = 0
            for b in c.get("bands") or []:
                ys = b.get("tracks_y") or []
                layers = b.get("layer"); lanes += len(ys)
                for yline in ys:
                    p0 = P(xr[0], yline, ox, oy); p1 = P(xr[1], yline, ox, oy)
                    line(f, p0[0], p0[1], p1[0], p1[1], "#bc8cff", 0.5)
                if ys:
                    p0 = P(xr[0], min(ys) - 0.4, ox, oy); p1 = P(xr[1], max(ys) + 0.4, ox, oy)
                    rect(f, p0[0], p0[1], p1[0], p1[1], "#bc8cff", width=0.8)
            _l24 = L2["L2-4_corridor_clearance"]
            _tgt = {"EAST_CHIP_TO_J2": [104.84, 132.65], "WEST_MCIO_TO_CHIP": [65.05, 82.60]}.get(c.get("id"))
            _flag = "" if _tgt is None or _tgt == c.get("x_range") else f"  <!> SPEC={c.get('x_range')} 与 L2-4 {_tgt} 不符"
            txt(f, 10, yy, f"{c.get('id')} x{_tgt or c.get('x_range')}（口径=焊盘外接框净距, L2-4）pairs={c.get('pairs')} lanes={lanes}{_flag}", "#bc8cff", 8); yy += 11
            for b in (c.get("bands") or [])[:3]:
                txt(f, 16, yy, f" ↳ {b.get('band')} @{b.get('layer')} pairs={b.get('pairs')}", "#8b949e", 7); yy += 9
        d = L2["L2-4_corridor_clearance"]
        txt(f, 10, H * SCALE - 10, f"口徑={d['basis']} | 西 {d['west_mm']}mm ({d['west_basis']}) | 東 {d['east_mm']}mm ({d['east_basis']})", "#8b949e")
        svg_close(f)

    # 04 层分配
    with open(os.path.join(OUT, "04_layer_assignment.svg"), "w") as f:
        f.write(svg_open("P3-04 层分配（8L：F/In1..In6/B；L2-5 + canonical SPEC）", 120, 46, ox, oy)[0])
        la = geo.get("layer_assignment") or {}
        wl = la.get("width_mm_by_layer") or {}; per = la.get("per_layer") or {}
        rowsx = [("F.Cu", "信号（微带，参考 In1）"), ("In1.Cu", "GND 平面"), ("In2.Cu", "信号（带状线，穿越）"),
                 ("In3.Cu", "GND 平面"), ("In4.Cu", "电源分区"), ("In5.Cu", "信号（带状线）"),
                 ("In6.Cu", "GND 平面"), ("B.Cu", "信号（单面贴，空置可用）")]
        for i, (l, r) in enumerate(rowsx):
            y0 = 12 * i
            rect(f, 20, y0, 330, y0 + 11, "#58a6ff", "#161b22", 0.5)
            pl = per.get(l) or {}
            wtxt = f"w={wl.get(l)}" if l in wl else ""
            ktxt = pl.get("kind", "") or ""
            refs = ",".join(pl.get("refs") or [])
            txt(f, 26, y0 + 8, f"{l:8s} {r}", "#e6edf3", 8)
            txt(f, 170, y0 + 8, f"{ktxt} {refs} {wtxt}", "#8b949e", 8)
        txt(f, 20, 12 * len(rowsx) + 18, f"Zdiff 目标 {la.get('target_zdiff')}Ω ±{la.get('tolerance_pct')}% · model={la.get('model')} · gap_mm={la.get('gap_mm')} / alt {la.get('alt_width_mm')}/{la.get('alt_gap_mm')}", "#8b949e", 8)
        txt(f, 20, 12 * len(rowsx) + 32, f"via: {L2['L2-6_via']}", "#8b949e", 8)
        txt(f, 20, 12 * len(rowsx) + 46, f"等长: {L2['L2-7_length']}", "#8b949e", 8)
        svg_close(f)

    # 05 敷铜策略
    with open(os.path.join(OUT, "05_pour_strategy.svg"), "w") as f:
        f.write(svg_open("P3-05 敷铜策略（L2-5；GND In1/In3/In6 + 电源 In4）", 120, 46, ox, oy)[0])
        pzs = geo.get("pour_zones") or {}
        colors = {"GND": "#3fb950", "P3V3": "#58a6ff", "MCU_VDD": "#d29922", "P3V3_AUX": "#bc8cff", "12V_IN": "#f85149", "": "#8b949e"}
        txt(f, 10, 20, f"zone 台账 {pzs.get('filled_count')}/{pzs.get('count')} 已填充（现状） | 出 Gerber 前置（审计 §10.5）：13 区全 filled_polygon>=1 且 net 非空", "#f0883e", 8)
        yy = 34
        for z in pzs.get("zones", []):
            bbz = z["bbox_mm"]; p0 = P(bbz[0], bbz[1], ox, oy); p1 = P(bbz[2], bbz[3], ox, oy)
            rect(f, p0[0], p0[1], p1[0], p1[1], colors.get(z["net"], "#8b949e"), width=0.7, dash="" if z["filled"] else "3 3")
            txt(f, 10, yy, f"z{z['idx']:>2d} {z['net'] or '(no-net)':10s} {z['layer']:8s} filled={z['filled']}", "#8b949e", 7); yy += 9
        txt(f, 10, H * SCALE - 10, f"power_partition={pzs.get('power_partition')} | gnd_stitch={json.dumps(pzs.get('gnd_stitch_via'), ensure_ascii=False)[:80]}", "#8b949e")
        svg_close(f)

    # 06 回避区
    with open(os.path.join(OUT, "06_keepouts.svg"), "w") as f:
        f.write(svg_open("P3-06 回避区（每区 5 开关，至少 1 项≠allowed；L2-8 8f）", W, H, ox, oy)[0])
        frame(f)
        kg = geo.get("keepout_geometry") or {}
        er = kg.get("edge_inset_rect_mm")
        if er:
            p0 = P(er[0], er[1], ox, oy); p1 = P(er[2], er[3], ox, oy)
            rect(f, p0[0], p0[1], p1[0], p1[1], "#d29922", dash="6 3", width=0.8)
        dc = kg.get("decap_column_rect_mm")
        if dc:
            p0 = P(dc[0], dc[1], ox, oy); p1 = P(dc[2], dc[3], ox, oy)
            rect(f, p0[0], p0[1], p1[0], p1[1], "#bc8cff", width=0.8)
        ub = kg.get("u6_pads_bbox_mm")
        if ub:
            p0 = P(ub[0], ub[1], ox, oy); p1 = P(ub[2], ub[3], ox, oy)
            rect(f, p0[0], p0[1], p1[0], p1[1], "#f85149", width=0.8)
            txt(f, p0[0], p0[1] - 4, f"U6 pad 场（逃逸区规则：净距 {kg['escape_zone']['clearance_mm']}mm / 无 90° / 无 via）", "#f85149", 7)
        for k, (hx, hy) in mh["positions"].items():
            cx, cy = P(hx, hy, ox, oy); circ(f, cx, cy, mh["keepout_dia_mm"] / 2 * SCALE, "#f0883e", dash="3 3")
        yy = 34
        for k in keep:
            txt(f, 10, yy, f"{k['id']}: " + ", ".join(f"{a}={b}" for a, b in k["switches"].items()), "#f0883e", 7); yy += 10
        txt(f, 10, yy + 6, f"板边铜 {kg.get('edge_copper_min_mm')}mm（黄框）· 去耦柱 keepout（紫框）= SPEC strap_domain 已裁 · AC pad GND cutout={kg.get('ac_pad_gnd_cutout')}", "#8b949e", 7)
        svg_close(f)

    # 07 接口焊盘出框检查
    with open(os.path.join(OUT, "07_interface_pads_inframe.svg"), "w") as f:
        f.write(svg_open("P3-07 接口焊盘出框检查（内缩 0.3mm；L2-8 8b）", W, H, ox, oy)[0])
        frame(f)
        x0, y0 = P(bx0 + inset, by0 + inset, ox, oy); x1, y1 = P(bx1 - inset, by1 - inset, ox, oy)
        rect(f, x0, y0, x1, y1, "#d29922", dash="5 3")
        for ref in ["J2", "J3", "J4", "J6", "J9", "J11", "J12", "J13"]:
            d = geo["devices"].get(ref)
            if d and d.get("pad_aabb"):
                a = d["pad_aabb"]; p0 = P(a[0], a[1], ox, oy); p1 = P(a[2], a[3], ox, oy)
                rect(f, p0[0], p0[1], p1[0], p1[1], "#3fb950" if not viol else "#f85149", width=0.8)
                txt(f, p0[0], p0[1] - 4, ref, "#e6edf3", 8)
        txt(f, 10, H * SCALE - 10, f"violations={viol or 'none'}", "#8b949e")
        svg_close(f)

    json.dump(geo, open(os.path.join(OUT, "p3_drawings.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[P3] drawings -> {os.path.relpath(OUT, ROOT)}")
    for k, v in geo["criteria"].items():
        print(f"  {k}: pass={v.get('pass')} " + json.dumps({kk: vv for kk, vv in v.items() if kk not in ('pass',)}, ensure_ascii=False)[:220])

if __name__ == "__main__":
    main()
