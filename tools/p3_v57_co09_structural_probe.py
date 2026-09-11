#!/usr/bin/env python3
"""CO-09 D1 结构可行性探针（只读）。

用途：复核 CO-08(B) 前提（F.Cu 长逃逸扇）与若干 river 方案的可行性。
- 读 canonical W3-CN.30 工件 + 冻结 8L PCB footprint；不写任何生产工件。
- 输出：F1 pad 场行型、F2 F.Cu 逃逸穿越判定、F3/F4 river 交叉计数、F5 层密度。

CLI: python3 tools/p3_v57_co09_structural_probe.py [--json OUT]
"""
from __future__ import annotations
import argparse, json, math, re
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
S = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3" / "mcio_feas_step2"
PCB = K2 / "k2_v4_8L.kicad_pcb"
MANIFEST = S / "m13_v57_s1_page_manifest.json"
CANON = S / "m13_v57_w3_joint_assignment_W3-CN.30.json"
POL, STEP, LANE_LO, VIA_VIA, LAND_INNER, LAND_OUTER = 0.19, 1.46, 33.3, 0.525, 131.65, 136.0


def seg_int(a, b, c, d):
    def o(p, q, r):
        return (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    d1, d2, d3, d4 = o(a, b, c), o(a, b, d), o(c, d, a), o(c, d, b)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def pt_seg(p, a, b):
    ax, ay = a; bx, by = b; px, py = p; dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def seg_seg(a, b, c, d):
    if seg_int(a, b, c, d):
        return 0.0
    return min(pt_seg(a, c, d), pt_seg(b, c, d), pt_seg(c, a, b), pt_seg(d, a, b))


def pof(cp, pol):
    base = -POL if (cp["N"]["pad_global"][1] - cp["P"]["pad_global"][1]) > 0 else POL
    return base if pol == "P" else -base


def chip_pad_rows():
    t = PCB.read_text()
    i = t.index('(footprint "DS320PR1601"')
    depth = 0; j = i
    while True:
        c = t[j]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                break
        j += 1
    block = t[i:j + 1]
    fx, fy, ang = 93.8, 53.7, math.radians(90.0)
    pads = []
    for m in re.finditer(r'\(pad "([^"]+)" (\w+) (\w+)\s*\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)\s*\(size ([-\d.]+) ([-\d.]+)\)', block):
        lx, ly = float(m.group(4)), float(m.group(5))
        pads.append((round(fx - ly, 3), round(fy + lx, 3)))  # rot90: (gx,gy)=(fx-ly, fy+lx)
    rows = {}
    for x, y in pads:
        rows.setdefault(round(y, 2), []).append(round(x, 2))
    out = []
    for y in sorted(rows):
        xs = sorted(set(rows[y]))
        step = round((xs[-1] - xs[0]) / (len(xs) - 1), 3) if len(xs) > 1 else 0.0
        out.append({"y": y, "n": len(xs), "step": step, "kind": "full" if len(xs) >= 30 else "sparse"})
    return out


def load():
    man = {p["page_id"]: p for p in json.load(open(MANIFEST))["pages"] if p["kind"] == "data"}
    can = {p["page_id"]: p for p in json.load(open(CANON))["pages"] if p.get("kind") == "data"}
    return man, can


def nets(man, can):
    out = []
    for pid, c in can.items():
        cp = man[pid]["anchors"]["chip"]
        for pol in ("P", "N"):
            out.append(dict(pid=pid, pol=pol, side=c["side"], band=c["band"],
                            cp=cp, px=c["r1"][pol]["via"][0], py=c["r1"][pol]["via"][1],
                            ly=round(c["lane"]["y"] + pof(cp, pol), 6),
                            lx=c["r3_by_pol"][pol]["column_x"], ll=c["r3_by_pol"][pol]["landing"][1],
                            chx=(cp["P"]["pad_global"][0] + cp["N"]["pad_global"][0]) / 2,
                            chy=(cp["P"]["pad_global"][1] + cp["N"]["pad_global"][1]) / 2))
    return out


def river_crossings(ns, band, layer_kind):
    """merge river（escape+lane+stub 同层）真交叉计数。"""
    segs = []
    for n in ns:
        if n["band"] != band:
            continue
        pts = [(n["px"], n["py"]), (n["px"], n["ly"]), (n["lx"], n["ly"]), (n["lx"], n["ll"])]
        for i in range(3):
            segs.append((n, pts[i], pts[i + 1]))
    xc = 0
    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            ni, a, b = segs[i]; nj, c, d = segs[j]
            if ni["pid"] == nj["pid"]:
                continue
            if seg_int(a, b, c, d):
                xc += 1
    return xc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args()
    rows = chip_pad_rows()
    man, can = load()
    ns = nets(man, can)
    rep = {
        "artifact": "m13_v57_co09_structural_probe_result",
        "schema": 1,
        "F1_pad_rows": rows,
        "F1_full_rows": [r["y"] for r in rows if r["kind"] == "full"],
        "F1_sparse_step": sorted({r["step"] for r in rows if r["kind"] == "sparse"}),
        "F2_east_pad_y": sorted({n["cp"][p]["pad_global"][1] for n in ns if n["side"] == "east" for p in ("P", "N")}),
        "F2_east_lane_y": sorted({n["ly"] for n in ns if n["side"] == "east"}),
        "F2_note": "east pad y < east lane y ⇒ F.Cu escape 必穿满行 y=57.12/57.64",
        "F3_merge_river_crossings": {
            "In2_dn": river_crossings(ns, "dn", "In2"),
            "In6_up": river_crossings(ns, "up", "In6"),
        },
        "F5_escape_density": {
            "ver_per_side": 32, "per_layer_16_x_lattice_mm": round(15 * 0.38, 3),
            "both_bands_one_layer_mm": round(31 * 0.38, 3), "available_chip_span_mm": 8.95,
        },
        "redline": "read-only; four frozen sources untouched",
    }
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    if a.json:
        Path(a.json).write_text(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
