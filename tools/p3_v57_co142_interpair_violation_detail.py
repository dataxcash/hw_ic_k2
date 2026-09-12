#!/usr/bin/env python3
"""CO-142：【L2 分析 · 只读】对间 3W/2w 违规**逐条明细 + 构造阶段归因**。

CO-141 只报计数；本件枚举全部 <2w 的**平行(<=10°)** 异对段对，给出坐标/网络/层/铜边距，
并把每条段归因到构造阶段（via1 逃生列 / lane / stub / pad-access / land），用于定位
「逃生列距漏 3W」的真实产生阶段。

只读；不改板/SPEC/冻结源；零坐标搜索。
CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co142_interpair_violation_detail.py
"""
from __future__ import annotations
import collections, hashlib, json, math, re
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
S2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-19.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
ALLOC = S2 / "m13_v57_co16_channel_allocation_v7.json"
REC = S2 / "m13_v57_co142_interpair_violation_detail.json"
CARD = S2 / "m13_v57_CO142_interpair_violation_detail.md"
PAR_DEG = 10.0
R3, EPS = 3.0, 1e-9


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def stem(n):
    m = re.match(r"^(.*)_(P|N)(_\w+)?$", n)
    return (m.group(1) + (m.group(3) or "")) if m else None


def pol_of(n):
    m = re.match(r"^.*_(P|N)(_\w+)?$", n)
    return m.group(1) if m else None


def d_pt_seg(px, py, sx, sy, ex, ey):
    vx, vy, wx, wy = ex - sx, ey - sy, px - sx, py - sy
    L = vx * vx + vy * vy
    t = 0.0 if L == 0 else max(0.0, min(1.0, (wx * vx + wy * vy) / L))
    return math.hypot(px - (sx + t * vx), py - (sy + t * vy))


def dss(ax, ay, bx, by, cx, cy, dx, dy):
    rx, ry, sx, sy = bx - ax, by - ay, dx - cx, dy - cy
    den = rx * sy - ry * sx
    if abs(den) > 1e-12:
        t = ((cx - ax) * sy - (cy - ay) * sx) / den
        u = ((cx - ax) * ry - (cy - ay) * rx) / den
        if 0 <= t <= 1 and 0 <= u <= 1:
            return 0.0
    return min(d_pt_seg(ax, ay, cx, cy, dx, dy), d_pt_seg(bx, by, cx, cy, dx, dy),
               d_pt_seg(cx, cy, ax, ay, bx, by), d_pt_seg(dx, dy, ax, ay, bx, by))


def ang(a, c):
    aa = math.degrees(math.atan2(a[6] - a[4], a[5] - a[3])) % 180.0
    ac = math.degrees(math.atan2(c[6] - c[4], c[5] - c[3])) % 180.0
    d = abs(aa - ac) % 180.0
    return min(d, 180.0 - d)


def build_netmap(manifest):
    nm = {}
    for pg in manifest["pages"]:
        if pg.get("kind") != "data" or "chip" not in (pg.get("anchors") or {}):
            continue
        for pol in ("P", "N"):
            nm[pg["anchors"]["chip"][pol]["net"]] = (pg["page_id"], pol)
    return nm


def classify(net, x1, y1, x2, y2, geo, netmap):
    """把段归因到构造阶段（基于 manifest 网络->页 映射 + ALLOC 几何端点匹配）。"""
    tags = []
    hit = netmap.get(net)
    if hit is None:
        return tags
    pid, p = hit
    if pid not in geo:
        return tags
    g = geo[pid]
    if True:
        vx = g["via1"][p][0]
        ly = g["lane_y"][p]
        lx, ll = g["landing"][p]
        pad = g["chip_pad"][p]
        cp = g["conn_pad"][p]
        def ends(ax, ay, bx, by, cx, cy, dx2, dy2):
            return (abs(ax-cx) < 0.02 and abs(ay-cy) < 0.02 and abs(bx-dx2) < 0.02 and abs(by-dy2) < 0.02) or \
                   (abs(ax-dx2) < 0.02 and abs(ay-dy2) < 0.02 and abs(bx-cx) < 0.02 and abs(by-cy) < 0.02)
        if abs(x1 - vx) < 0.02 and abs(x2 - vx) < 0.02 and min(y1, y2) < ly + 1e-6 < max(y1, y2) + 1e-6:
            tags.append(("escape_vert", pid, p, g["escape_layer"]))
        if ends(x1, y1, x2, y2, pad[0], pad[1], vx, g["via1"][p][1]):
            tags.append(("pad_access", pid, p, "F.Cu"))
        if ends(x1, y1, x2, y2, vx, ly, lx, ly):
            tags.append(("lane", pid, p, "In5.Cu"))
        if abs(x1 - lx) < 0.02 and abs(x2 - lx) < 0.02:
            tags.append(("stub", pid, p, g["stub_layer"]))
        if ends(x1, y1, x2, y2, lx, ll, cp[0], cp[1]):
            tags.append(("land", pid, p, "F.Cu"))
    return tags


def main() -> int:
    import pcbnew
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    wby = dict(spec["impedance"]["width_mm_by_layer"])
    geo = json.loads(ALLOC.read_text())["pages"]
    netmap = build_netmap(json.loads((S2 / "m13_v57_s1_page_manifest.json").read_text()))
    b = pcbnew.LoadBoard(str(BOARD))
    segs = collections.defaultdict(list)
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK":
            continue
        st = stem(t.GetNetname())
        if not st:
            continue
        segs[b.GetLayerName(t.GetLayer())].append(
            (st, t.GetNetname(), pcbnew.ToMM(t.GetWidth()),
             pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y),
             pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y)))
    viol = []
    for L in sorted(segs):
        w = wby.get(L)
        if w is None:
            continue
        req = R3 * w  # 3W 中心距
        for i in range(len(segs[L])):
            for j in range(i + 1, len(segs[L])):
                a, c = segs[L][i], segs[L][j]
                if a[0] == c[0]:
                    continue
                cc = dss(a[3], a[4], a[5], a[6], c[3], c[4], c[5], c[6])
                e = cc - a[2] / 2 - c[2] / 2
                if cc >= req - 1e-9:
                    continue
                ag = ang(a, c)
                viol.append({
                    "layer": L, "w_mm": w, "two_w_mm": round(2 * w, 4), "three_w_center_mm": round(req, 4),
                    "center_mm": round(cc, 4), "edge_mm": round(e, 4),
                    "angle_deg": round(ag, 2), "parallel_le10": ag <= PAR_DEG,
                    "net_a": a[1], "net_b": c[1],
                    "seg_a": [round(v, 4) for v in a[3:7]], "seg_b": [round(v, 4) for v in c[3:7]],
                    "class_a": classify(a[1], a[3], a[4], a[5], a[6], geo, netmap),
                    "class_b": classify(c[1], c[3], c[4], c[5], c[6], geo, netmap),
                })
    par = [v for v in viol if v["parallel_le10"]]
    cls = collections.Counter()
    for v in par:
        ka = v["class_a"][0][0] if v["class_a"] else "?"
        kb = v["class_b"][0][0] if v["class_b"] else "?"
        cls[f"{ka}|{kb}"] += 1
    rec = {"artifact": "m13_v57_co142_interpair_violation_detail", "schema": 1, "revision": "CO-142",
           "nature": "L2 分析（只读）：<3W 中心距异对段对逐条明细 + 构造阶段归因",
           "inputs": {"board": s16(BOARD), "spec": s16(SPEC), "alloc": s16(ALLOC)},
           "parallel_angle_cutoff_deg": PAR_DEG,
           "n_violations_all": len(viol), "n_violations_parallel": len(par),
           "class_histogram_parallel": dict(cls), "violations": viol,
           "verdict": "DATA_ONLY", "redline": "只读；不改板/SPEC/冻结源；零坐标搜索"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# CO-142 — 对间 <3W 违规明细（L2 只读）", "",
             f"- 全量 <3W 段对：{len(viol)}；其中平行(≤10°)：{len(par)}", "",
             "| # | 层 | 中心 | 铜边 | 2w | 3w | 角度 | 网络A | 网络B | 阶段A | 阶段B |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, v in enumerate(par):
        lines.append(f"| {k+1} | {v['layer']} | {v['center_mm']} | {v['edge_mm']} | {v['two_w_mm']} | "
                     f"{v['three_w_center_mm']} | {v['angle_deg']} | {v['net_a']} | {v['net_b']} | "
                     f"{(v['class_a'][0][0] if v['class_a'] else '?')} | {(v['class_b'][0][0] if v['class_b'] else '?')} |")
    lines += ["", f"阶段直方图：{json.dumps(dict(cls), ensure_ascii=False)}", ""]
    CARD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"n_all": len(viol), "n_parallel": len(par),
                      "hist": dict(cls), "rec_sha16": s16(REC)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
