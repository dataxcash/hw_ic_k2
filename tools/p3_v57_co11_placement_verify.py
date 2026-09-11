#!/usr/bin/env python3
"""CO-11 独立复核器（非探针 producer）：读探针 geom dump，**全对全**重算净距。

判据（与 SPEC/引擎 A-CN.9 一致）：
  vv(异网) = 0.525；vt = 0.4525（pad 邻接段 0.3525）；tt = 0.38（pad 邻接 0.28）；pad 边距 = 0.075。
覆盖：via-via / via-track / track-track（全层）/ via-pad / track-pad（豁免本页 4 pad）。
只读。"""
from __future__ import annotations
import json, os, sys
from pathlib import Path
import numpy as np

VV, VT, VTE, TT, TTE, ESC, TOL = 0.525, 0.4525, 0.3525, 0.38, 0.28, 0.075, 1e-9
# CO-25（D3b 判据修正，**opt-in**）：SPEC `escape_transition_zone.escape_clearance_mm=0.075` 是**铜距**下限。
#   本复核器 v1 的 `pad_gap_pt/seg_pad_gap` 返回的是**中心距**，却直接与 ESC 比较 ⇒ 少减 width/2(0.1025)/via_r(0.175)，判据被放宽。
#   `CO11_PAD_UNITS=copper` 时改为铜距口径（默认 `centerline` = 旧行为，保 W3-CN.37/ALLOC.4 证据可复现）。
PAD_UNITS = os.environ.get("CO11_PAD_UNITS", "centerline")
TRACK_HALF = 0.205 / 2.0      # PCIe85 线宽 0.205
VIA_R = 0.35 / 2.0            # via dia 0.35
PAD_CENTER_THR_TRACK = ESC + TRACK_HALF   # 铜距 ESC ⇔ 中心距 ESC+width/2
PAD_CENTER_THR_VIA = ESC + VIA_R          # 铜距 ESC ⇔ 中心距 ESC+via_r
LI = {"B.Cu": 0, "In2.Cu": 1, "In6.Cu": 2, "F.Cu": 3}


def load_pads(p):
    P = [(q["x"], q["y"], q["sx"] / 2, q["sy"] / 2, max(q["sx"], q["sy"]) / 2, q["shape"] == 0, q["ref"], q["pad"])
         for q in p["pads"]]
    return P


def pad_gap_pt(px, py, pads, exempt):
    g = 9e9
    for (x, y, hx, hy, r, circ, ref, pn) in pads:
        if (round(x, 2), round(y, 2)) in exempt:
            continue
        if circ:
            d = max(np.hypot(px - x, py - y) - r, 0.0)
        else:
            ex = max(abs(px - x) - hx, 0.0); ey = max(abs(py - y) - hy, 0.0)
            d = float(np.hypot(ex, ey))
        g = min(g, d)
    return g


def seg_pad_gap(a, b, pads, exempt):
    g = 9e9
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay; L2 = max(dx * dx + dy * dy, 1e-12)
    for (x, y, hx, hy, r, circ, ref, pn) in pads:
        if (round(x, 2), round(y, 2)) in exempt:
            continue
        t = min(max(((x - ax) * dx + (y - ay) * dy) / L2, 0.0), 1.0)
        qx, qy = ax + t * dx, ay + t * dy
        if circ:
            d = max(np.hypot(qx - x, qy - y) - r, 0.0)
        else:
            ex = max(abs(qx - x) - hx, 0.0); ey = max(abs(qy - y) - hy, 0.0)
            d = float(np.hypot(ex, ey))
        g = min(g, d)
    return g


def _orient(ax, ay, bx, by, cx, cy):
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


def seg_cross(a, b, c, d):
    o1 = _orient(a[0], a[1], b[0], b[1], c[0], c[1]); o2 = _orient(a[0], a[1], b[0], b[1], d[0], d[1])
    o3 = _orient(c[0], c[1], d[0], d[1], a[0], a[1]); o4 = _orient(c[0], c[1], d[0], d[1], b[0], b[1])
    return o1 * o2 < -1e-18 and o3 * o4 < -1e-18


def _pt_in_rect(px, py, x, y, hx, hy):
    return abs(px - x) <= hx + 1e-12 and abs(py - y) <= hy + 1e-12


def seg_rect_gap(a, b, x, y, hx, hy, circ=False, r=0.0):
    """CO-25: 线段到 pad 的**真**最短距离（旧 seg_pad_gap 用 pad 中心投影近似，**高估**净距 ⇒ 假阴性）。"""
    if circ:
        return max(pt_seg(x, y, a[0], a[1], b[0], b[1]) - r, 0.0)
    if _pt_in_rect(a[0], a[1], x, y, hx, hy) or _pt_in_rect(b[0], b[1], x, y, hx, hy):
        return 0.0
    cs = [(x - hx, y - hy), (x + hx, y - hy), (x + hx, y + hy), (x - hx, y + hy)]
    g = 9e9
    for i in range(4):
        c, d = cs[i], cs[(i + 1) % 4]
        if seg_cross(a, b, c, d):
            return 0.0
        g = min(g, seg_seg(a, b, c, d))
    return g


def seg_pad_gap_true(a, b, pads, exempt):
    g = 9e9
    for (x, y, hx, hy, r, circ, ref, pn) in pads:
        if (round(x, 2), round(y, 2)) in exempt:
            continue
        g = min(g, seg_rect_gap(a, b, x, y, hx, hy, circ, r))
    return g


def pt_seg(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1; L2 = dx * dx + dy * dy
    if L2 < 1e-12:
        return float(np.hypot(px - x1, py - y1))
    t = min(max(((px - x1) * dx + (py - y1) * dy) / L2, 0.0), 1.0)
    return float(np.hypot(px - (x1 + t * dx), py - (y1 + t * dy)))


def seg_seg(a, b, c, d):
    return min(pt_seg(c[0], c[1], a[0], a[1], b[0], b[1]), pt_seg(d[0], d[1], a[0], a[1], b[0], b[1]),
               pt_seg(a[0], a[1], c[0], c[1], d[0], d[1]), pt_seg(b[0], b[1], c[0], c[1], d[0], d[1]))


def main():
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/co10s/g32.json")
    doc = json.loads(src.read_text())
    pads = load_pads(json.loads(Path("pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co09_pad_field.json").read_text()))
    G = doc["geom"]
    vias, segs, own = [], [], {}
    for pid, g in G.items():
        own[pid] = {(round(g["pad"]["P"][0], 2), round(g["pad"]["P"][1], 2)),
                    (round(g["pad"]["N"][0], 2), round(g["pad"]["N"][1], 2)),
                    (round(g["conn"]["P"][0], 2), round(g["conn"]["P"][1], 2)),
                    (round(g["conn"]["N"][0], 2), round(g["conn"]["N"][1], 2))}
        for (x, y, pol, lays) in g["vias"]:
            vias.append((pid, x, y, pol, set(lays)))
        for (lay, x1, y1, x2, y2, pa, pol) in g["segs"]:
            segs.append((pid, lay, x1, y1, x2, y2, pa, pol))
    bad = []
    # via-via (异网 or 同页异 pol)
    for i in range(len(vias)):
        for j in range(i + 1, len(vias)):
            pi, xi, yi, poli, lsi = vias[i]; pj, xj, yj, polj, lsj = vias[j]
            if pi == pj and poli == polj:
                continue
            if not (lsi & lsj):
                continue
            d = float(np.hypot(xi - xj, yi - yj))
            if d < VV - TOL:
                bad.append(("vv", pi, poli, pj, polj, round(d, 4)))
    # via-track
    for (pi, x, y, pol, ls) in vias:
        for (pj, lay, x1, y1, x2, y2, pa, p2) in segs:
            if pi == pj and pol == p2:
                continue
            if lay not in ls:
                continue
            d = pt_seg(x, y, x1, y1, x2, y2)
            thr = VTE if pa else VT
            if d < thr - TOL:
                bad.append(("vt", pi, pol, lay, pj, p2, round(d, 4)))
    # track-track (transversal crossing, proper intersection) — engine count_crossings 语义
    def _cross(a, b, c, d):
        def o(p, q, r):
            v = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
            return 0 if abs(v) < 1e-12 else (1 if v > 0 else 2)
        def on(p, q, r):
            return (min(p[0], r[0]) - 1e-9 <= q[0] <= max(p[0], r[0]) + 1e-9 and
                    min(p[1], r[1]) - 1e-9 <= q[1] <= max(p[1], r[1]) + 1e-9)
        o1, o2, o3, o4 = o(a, b, c), o(a, b, d), o(c, d, a), o(c, d, b)
        if o1 != o2 and o3 != o4:
            return 1
        if o1 == 0 and on(a, c, b): return 1
        if o2 == 0 and on(a, d, b): return 1
        if o3 == 0 and on(c, a, d): return 1
        if o4 == 0 and on(c, b, d): return 1
        return 0
    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            pi, li, x1, y1, x2, y2, pai, poli = segs[i]
            pj, lj, u1, v1, u2, v2, paj, polj = segs[j]
            if li != lj:
                continue
            if pi == pj and poli == polj:
                continue
            if _cross((x1, y1), (x2, y2), (u1, v1), (u2, v2)):
                bad.append(("cross", li, pi, poli, pj, polj))
    # track-track
    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            pi, li, x1, y1, x2, y2, pai, poli = segs[i]
            pj, lj, u1, v1, u2, v2, paj, polj = segs[j]
            if li != lj:
                continue
            if pi == pj and poli == polj:
                continue
            d = seg_seg((x1, y1), (x2, y2), (u1, v1), (u2, v2))
            thr = TTE if (pai or paj) else TT
            if d < thr - TOL:
                bad.append(("tt", li, pi, poli, pj, polj, round(d, 4)))
    # via-pad / track-pad
    for (pi, x, y, pol, ls) in vias:
        if "F.Cu" not in ls:
            continue                                       # CO-25: pad 在 F.Cu（SMD）；埋孔(In2/In6)与 pad 无共层，不构成铜冲突
        g = pad_gap_pt(x, y, pads, own[pi])
        _thr = PAD_CENTER_THR_VIA if PAD_UNITS == "copper" else ESC
        if g < _thr - TOL:
            bad.append(("vp", pi, pol, round(g - (VIA_R if PAD_UNITS == "copper" else 0.0), 4)))
    for (pi, lay, x1, y1, x2, y2, pa, pol) in segs:
        if lay != "F.Cu":
            continue                                       # pad 在 F.Cu；内层可穿行于 pad 之下
        # CO-25: copper 模式仅豁免「本段落点的自有 pad + 芯片 pad」；否则同页对侧极性 pad 的 P/N 侵入会被掩盖
        _ex = own[pi]
        if PAD_UNITS == "copper":
            _g = G[pi]
            _ex = {(round(_g["pad"]["P"][0], 2), round(_g["pad"]["P"][1], 2)),
                   (round(_g["pad"]["N"][0], 2), round(_g["pad"]["N"][1], 2)),
                   (round(_g["conn"][pol][0], 2), round(_g["conn"][pol][1], 2))}
        g = (seg_pad_gap_true if PAD_UNITS == "copper" else seg_pad_gap)((x1, y1), (x2, y2), pads, _ex)
        _thr = PAD_CENTER_THR_TRACK if PAD_UNITS == "copper" else ESC
        if g < _thr - TOL:
            bad.append(("sp", pi, pol, lay, round(g - (TRACK_HALF if PAD_UNITS == "copper" else 0.0), 4)))
    res = {"artifact": "m13_v57_co11_placement_verification", "src": str(src),
           "n_vias": len(vias), "n_segs": len(segs), "n_pages": len(G),
           "n_violations": len(bad), "pad_units": PAD_UNITS, "escape_clearance_mm": ESC,
           "verdict": "PASS" if not bad else "FAIL",
           "violations": bad[:40]}
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else \
        Path("pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co11_placement_verification.json")
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("n_pages", "n_vias", "n_segs", "n_violations", "verdict")}))
    if bad:
        for b in bad[:12]:
            print(" ", b)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
