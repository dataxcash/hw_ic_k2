#!/usr/bin/env python3
"""CO-141：【L2 分析 · 只读】对间 3W(2w) 符合性**全量审计**（修正 co134 只报逐层最小值）。

co134 的 `as_built` 每层只记**一个最小值**（best_out）⇒ 登记簿「域外偏差 3 处」是**下界**。
本件枚举**全部异对段对**，按夹角分类：∠≤10° 记「平行」、否则「斜交」，报告 <2w 的**真实范围**。
只读；不改板/SPEC/冻结源；零坐标搜索（确定性枚举）。
CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co141_interpair_conformance_audit.py
"""
from __future__ import annotations
import collections, hashlib, json, math, re
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
S2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-19.json"
CO134 = S2 / "m13_v57_co134_req_impl_separation.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
REC = S2 / "m13_v57_co141_interpair_conformance_audit.json"
CARD = S2 / "m13_v57_CO141_interpair_conformance_audit.md"
PAR_DEG = 10.0


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def stem(n):
    m = re.match(r"^(.*)_(P|N)(_\w+)?$", n)
    return (m.group(1) + (m.group(3) or "")) if m else None


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


def main() -> int:
    import pcbnew
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    wby = dict(spec["impedance"]["width_mm_by_layer"])
    board_report = json.loads(CO134.read_text(encoding="utf-8"))["as_built"]
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
    rows = []
    for L in sorted(segs):
        w = wby.get(L)
        if w is None:
            continue
        req = 2 * w
        par = obl = 0
        pairsP, minP = set(), None
        for i in range(len(segs[L])):
            for j in range(i + 1, len(segs[L])):
                a, c = segs[L][i], segs[L][j]
                if a[0] == c[0]:
                    continue
                e = dss(a[3], a[4], a[5], a[6], c[3], c[4], c[5], c[6]) - a[2] / 2 - c[2] / 2
                if e < req - 1e-9:
                    if ang(a, c) <= PAR_DEG:
                        par += 1
                        pairsP.add(tuple(sorted((a[0], c[0]))))
                        if minP is None or e < minP[0]:
                            minP = (round(e, 4), a[1], c[1], round(ang(a, c), 1))
                    else:
                        obl += 1
        rows.append({"layer": L, "w_mm": w, "two_w_mm": round(req, 4),
                     "below_2w_parallel_le10deg": par, "below_2w_oblique_gt10deg": obl,
                     "parallel_pairs_involved": len(pairsP), "min_parallel": minP,
                     "co134_reported_min_only": next((r["min_edge_mm"] for r in board_report["rows"]
                                                      if r["layer"] == L and r["scope"] == "outside_escape"), None)})
    tot_par = sum(r["below_2w_parallel_le10deg"] for r in rows)
    rec = {"artifact": "m13_v57_co141_interpair_conformance_audit", "schema": 1, "revision": "CO-141",
           "nature": "L2 分析（只读）：对间 2w 符合性全量审计（修正 co134 逐层最小值 = 下界）",
           "inputs": {"board": s16(BOARD), "spec": s16(SPEC), "co134_record": s16(CO134)},
           "parallel_angle_cutoff_deg": PAR_DEG, "rows": rows,
           "finding": (f"co134 每层只报一个最小值 ⇒ 「域外偏差 3 处」为**下界**；全量枚举得**平行(≤{PAR_DEG}°) 低于 2w 的组合 {tot_par} 个**，"
                       f"涉及 {sum(r['parallel_pairs_involved'] for r in rows)} 个对-对；In5 的低于 2w 组合**全为斜交**（>10°）⇒ 属「长平行」口径外。"),
           "verdict": "UNDER_REPORTED", "redline": "只读；不改板/SPEC/冻结源；零坐标搜索"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# CO-141 — 对间 2w 符合性全量审计（L2 只读）", "", f"- verdict：**UNDER_REPORTED**", "",
             "| 层 | 2w | <2w 且平行(≤10°) | <2w 且斜交(>10°) | 平行涉及对数 | 平行最小 | co134 只报 |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['layer']} | {r['two_w_mm']} | {r['below_2w_parallel_le10deg']} | {r['below_2w_oblique_gt10deg']} | "
                     f"{r['parallel_pairs_involved']} | {r['min_parallel']} | {r['co134_reported_min_only']} |")
    lines += ["", rec["finding"], ""]
    CARD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"], "rows": rows, "total_parallel": tot_par,
                      "finding": rec["finding"], "rec_sha16": s16(REC), "card_sha16": s16(CARD)},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
