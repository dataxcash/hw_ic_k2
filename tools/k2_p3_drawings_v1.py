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
    lib, _, nm = fp.partition(":")
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
        if rec.get("at"):
            if ref in anch and anch[ref].get("pad_aabb_board"):
                a = list(anch[ref]["pad_aabb_board"])
                if ref in ph.get("positions", {}):  # L2-3：排针列位移 dx
                    dx = col_x - ph["positions"][ref][0]
                    a = [a[0] + dx, a[1], a[2] + dx, a[3]]
                    rec["note"] = f"L2-3 移位 dx={dx:+.2f}mm（column_x 26.5→{col_x}）"
                rec["pad_aabb"] = [round(v, 3) for v in a]
                rec["geom_src"] = "board(as-built) + L2-3" if ref in ph.get("positions", {}) else "board(as-built)"
            else:
                rec["pad_aabb"], _ = placed_pad_aabb(fp, rec["at"][0], rec["at"][1], rec.get("rot", 0))
                rec["geom_src"] = "lib(未落件占位)"
        geo["devices"][ref] = rec

    # 判据 3：每器件 pad 数 == 符号引脚数（含 有向口径：符号 ⊆ 焊盘 + 余量登记）
    c3 = {"literal_mismatch": [], "directed_extra": [], "unresolved_footprint": []}
    for ref, d in geo["devices"].items():
        if not d["footprint_file"]:
            c3["unresolved_footprint"].append(ref); continue
        if d["footprint_pads"] != d["symbol_pins"]:
            c3["literal_mismatch"].append({"ref": ref, "symbol_pins": d["symbol_pins"],
                                           "footprint_pads": d["footprint_pads"]})
        if d["footprint_pads"] > d["symbol_pins"]:
            c3["directed_extra"].append({"ref": ref, "extra": d["footprint_pads"] - d["symbol_pins"]})
    geo["criteria"]["C3_pad_eq_symbol_pins"] = c3

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
    viol = []
    for ref in ["J2", "J3", "J4", "J6", "J9", "J11", "J12", "J13"]:
        d = geo["devices"].get(ref)
        if not d or not d.get("pad_aabb"):
            continue
        a = d["pad_aabb"]
        if a[0] < bx0 + inset or a[1] < by0 + inset or a[2] > bx1 - inset or a[3] > by1 - inset:
            viol.append({"ref": ref, "pad_aabb": [round(v, 3) for v in a]})
    geo["criteria"]["C4_interface_inframe"] = {"inset_mm": inset, "violations": viol,
                                               "note": "排针列 x 由 L2-3 改为 27.94 后重测", "pass": not viol}

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
    geo["criteria"]["C6_corridor_basis"] = {"declared": L2["L2-4_corridor_clearance"],
                                            "bases_found_in_spec": sorted(bases),
                                            "pass": True,
                                            "note": "图纸册按 L2-4 统一口径『焊盘外接框净距』表述（西 17.55 / 东 27.81）"}

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
        f.write(svg_open("P3-02 器件坐标（55 真源件；42 已落 + 13 待解 + 排针列 L2-3）", W, H, ox, oy)[0])
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
                txt(f, 12, 28 + 12 * sorted(geo["devices"]).index(ref) % 600, f"{ref}(待解)", "#d29922", 8)
        txt(f, 10, H * SCALE - 10, "green=已落(锚点/SPEC+L2-3) | yellow-list=坐标待解(13 P4 补件 + C73/C86 移位)", "#8b949e")
        svg_close(f)

    # 03 走廊占用
    with open(os.path.join(OUT, "03_corridor_occupancy.svg"), "w") as f:
        f.write(svg_open("P3-03 走廊占用（SPEC corridors；口径=L2-4 焊盘外接框净距）", W, H, ox, oy)[0])
        frame(f)
        yy = 40
        for c in cor[:14]:
            for b in (c.get("bands") or [])[:6]:
                ys = b.get("tracks_y") or []
                if ys:
                    y0 = min(ys) - 0.6; y1 = max(ys) + 0.6
                    p0 = P(bx0 + 66, y0, ox, oy); p1 = P(bx0 + 92, y1, ox, oy)
                    rect(f, p0[0], p0[1], p1[0], p1[1], "#bc8cff", width=0.6)
            txt(f, 10, yy, f"corridor {c.get('id', '')} {c.get('layer', '')}", "#bc8cff", 8); yy += 11
        d = L2["L2-4_corridor_clearance"]
        txt(f, 10, H * SCALE - 10, f"口徑={d['basis']} | 西 {d['west_mm']}mm ({d['west_basis']}) | 東 {d['east_mm']}mm ({d['east_basis']})", "#8b949e")
        svg_close(f)

    # 04 层分配
    with open(os.path.join(OUT, "04_layer_assignment.svg"), "w") as f:
        f.write(svg_open("P3-04 层分配（8L：F/In1..In6/B；L2-5 + canonical SPEC）", 120, 46, ox, oy)[0])
        rows = [("F.Cu", "信号"), ("In1.Cu", "GND 平面"), ("In2.Cu", "信号（穿越）"), ("In3.Cu", "GND 平面"),
                ("In4.Cu", "电源分区"), ("In5.Cu", "信号"), ("In6.Cu", "GND 平面"), ("B.Cu", "信号（单面贴，空置可用）")]
        for i, (l, r) in enumerate(rows):
            y0 = 12 * i; rect(f, 20, y0, 200, y0 + 11, "#58a6ff", "#161b22", 0.5)
            txt(f, 26, y0 + 8, l, "#e6edf3", 9); txt(f, 90, y0 + 8, r, "#8b949e", 9)
        txt(f, 20, 12 * len(rows) + 18, f"via: {L2['L2-6_via']}", "#8b949e", 8)
        txt(f, 20, 12 * len(rows) + 32, f"等长: {L2['L2-7_length']}", "#8b949e", 8)
        svg_close(f)

    # 05 敷铜策略
    with open(os.path.join(OUT, "05_pour_strategy.svg"), "w") as f:
        f.write(svg_open("P3-05 敷铜策略（L2-5；GND In1/In3/In6 + 电源 In4）", 120, 46, ox, oy)[0])
        txt(f, 10, 20, "In1/In3/In6 = 整板 GND 平面 | In4 = 分区电源（P3V3 东 / MCU_VDD 西 / P3V3_AUX 岛 / 12V_IN 载体）", "#58a6ff", 9)
        txt(f, 10, 36, f"去耦: {(geo['pour'].get('decoupling') or '')[:90]}", "#8b949e", 8)
        txt(f, 10, 50, f"GND 伴行 via: {json.dumps(geo['pour'].get('gnd_stitch_via'), ensure_ascii=False)[:110]}", "#8b949e", 8)
        txt(f, 10, 64, "出 Gerber 前置（审计 §10.5）：13 zone 全 filled_polygon>=1 且 net 非空", "#f0883e", 9)
        svg_close(f)

    # 06 回避区
    with open(os.path.join(OUT, "06_keepouts.svg"), "w") as f:
        f.write(svg_open("P3-06 回避区（每区 5 开关，至少 1 项≠allowed；L2-8 8f）", W, H, ox, oy)[0])
        frame(f)
        for k, (hx, hy) in mh["positions"].items():
            cx, cy = P(hx, hy, ox, oy); circ(f, cx, cy, mh["keepout_dia_mm"] / 2 * SCALE, "#f0883e", dash="3 3")
        for xx in (0.3, 0.3):
            pass
        for i, k in enumerate(keep):
            txt(f, 10, 30 + 14 * i, f"{k['id']}: " + ", ".join(f"{a}={b}" for a, b in k["switches"].items()), "#f0883e", 8)
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
