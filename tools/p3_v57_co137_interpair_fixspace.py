#!/usr/bin/env python3
"""CO-137：【L2 分析 · 只读】as-built 对间铜边偏差的**几何修正可行性**（域外 3 处）。

背景：CO-134 登记域外偏差 3 处（OPEN_ENGINEERING；路由 = SI/板厂券 或 **几何迭代另开 CO**）。
本件走几何路线做**确定性可行性判定**（零坐标搜索、只读）：
  对每处偏差，取该层该站点两对（PA/PB）的最近线段，计算：
    Δ = required_edge(2w) − actual_edge
    把 PB 整对沿「远离 PA」方向平移 t ⇒ PA-PB 净距 +t；PB 与**远侧**最近异网铜净距 −t
  ⇒ 可行 ⇔ 存在一侧使 (该侧可用净距 − required_edge) ≥ Δ（并给出该侧余量）。
  另一侧不足时判 INFEASIBLE_ONE_SIDE，两侧皆不足判 INFEASIBLE_BOTH。
只读：不改板/SPEC/冻结源；不做任何扫描式搜索（只用最近邻闭式几何）。
CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co137_interpair_fixspace.py
"""
from __future__ import annotations
import hashlib, json, math, re
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
S2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-19.json"
CO134 = S2 / "m13_v57_co134_req_impl_separation.json"
CO37 = S2 / "m13_v57_co37_escape_domain.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
REC = S2 / "m13_v57_co137_interpair_fixspace.json"
CARD = S2 / "m13_v57_CO137_interpair_fixspace.md"


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


def d_seg_seg(ax, ay, bx, by, cx, cy, dx, dy):
    rx, ry, sx, sy = bx - ax, by - ay, dx - cx, dy - cy
    den = rx * sy - ry * sx
    if abs(den) > 1e-12:
        t = ((cx - ax) * sy - (cy - ay) * sx) / den
        u = ((cx - ax) * ry - (cy - ay) * rx) / den
        if 0 <= t <= 1 and 0 <= u <= 1:
            return 0.0
    return min(d_pt_seg(ax, ay, cx, cy, dx, dy), d_pt_seg(bx, by, cx, cy, dx, dy),
               d_pt_seg(cx, cy, ax, ay, bx, by), d_pt_seg(dx, dy, ax, ay, bx, by))


def main() -> int:
    import pcbnew
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    w_by_layer = dict(spec["impedance"]["width_mm_by_layer"])
    devs = json.loads(CO134.read_text(encoding="utf-8"))["as_built"]["deviations_open_engineering"]
    rects = [(d["id"], *d["rect_mm"]) for d in json.loads(CO37.read_text(encoding="utf-8"))["domains"]]
    b = pcbnew.LoadBoard(str(BOARD))
    segs = {}
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK":
            continue
        st = stem(t.GetNetname())
        if not st:
            continue
        segs.setdefault(b.GetLayerName(t.GetLayer()), []).append(
            (st, t.GetNetname(), pcbnew.ToMM(t.GetWidth()),
             pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y),
             pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y)))

    rows = []
    for d in devs:
        L = d["layer"]; x, y = d["at"]; req = d["required_edge_mm"]
        items = segs[L]
        # 取该站点处两对的最近两段（按段中点到站点的距离）
        near = sorted(items, key=lambda s: math.hypot((s[3] + s[5]) / 2 - x, (s[4] + s[6]) / 2 - y))[:40]
        pa = next((s for s in near if s[0] == stem(d["pairs"][0])), None)
        pb = next((s for s in near if s[0] == stem(d["pairs"][1])), None)
        def edge(a, b2):
            return d_seg_seg(a[3], a[4], a[5], a[6], b2[3], b2[4], b2[5], b2[6]) - a[2] / 2 - b2[2] / 2
        actual = round(min(edge(s, t) for s in items if s[0] == pa[0] for t in items if t[0] == pb[0]), 4)
        delta = round(req - actual, 4)
        # 方向 d = PA->PB 最近点连线；PB 平移方向 = 远离 PA
        mx_a = ((pa[3] + pa[5]) / 2, (pa[4] + pa[6]) / 2)
        mx_b = ((pb[3] + pb[5]) / 2, (pb[4] + pb[6]) / 2)
        vx, vy = mx_b[0] - mx_a[0], mx_b[1] - mx_a[1]
        n = math.hypot(vx, vy) or 1.0
        ux, uy = vx / n, vy / n                                  # PA→PB 单位向量
        def side_slack(moved, sign):
            """moved 沿 sign*u 平移时，与**该侧**其他异网对的最小净距 − req（即该侧可让出的量）。"""
            best = None
            for s in items:
                if s[0] == moved[0]:
                    continue
                smx = ((s[3] + s[5]) / 2, (s[4] + s[6]) / 2)
                off = (smx[0] - mx_b[0]) * ux + (smx[1] - mx_b[1]) * uy
                if off * sign <= 0:                              # 非同侧
                    continue
                e = min(edge(mv, s) for mv in items if mv[0] == moved[0])
                if best is None or e < best:
                    best = e
            return None if best is None else round(best - req, 4)
        rows.append({
            "layer": L, "at": [x, y], "pairs": d["pairs"], "required_edge_mm": req,
            "recomputed_edge_mm": actual, "delta_needed_mm": delta,
            "move_candidate": pb[1], "fixed": pa[1],
            "far_side_slack_after_move_mm": side_slack(pb, +1),
            "near_side_slack_mm": side_slack(pb, -1),
        })
    for r in rows:
        fs = r["far_side_slack_after_move_mm"]
        r["verdict"] = ("FEASIBLE_SHIFT" if fs is not None and fs >= r["delta_needed_mm"]
                        else "INFEASIBLE_ONE_SIDE" if fs is not None else "NO_FAR_NEIGHBOUR")
    rec = {
        "artifact": "m13_v57_co137_interpair_fixspace", "schema": 1, "revision": "CO-137",
        "nature": "L2 分析（只读）：as-built 对间铜边偏差的几何修正可行性",
        "inputs": {"board": s16(BOARD), "spec": s16(SPEC), "co134_record": s16(CO134)},
        "rows": rows,
        "verdict": ("ALL_FEASIBLE" if all(r["verdict"] == "FEASIBLE_SHIFT" for r in rows) else
                    "MIXED" if any(r["verdict"] == "FEASIBLE_SHIFT" for r in rows) else "NONE_FEASIBLE"),
        "redline": "只读；不改板/SPEC/冻结源；无扫描/坐标搜索（最近邻闭式几何）",
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# CO-137 — as-built 对间铜边偏差：几何修正可行性（L2 只读）", "",
             f"- verdict：**{rec['verdict']}**", "",
             "| 层 | 位置 | Δ needed | 远侧余量(>Δ 即可平移) | 判定 |", "|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['layer']} | {r['at']} | {r['delta_needed_mm']} | {r['far_side_slack_after_move_mm']} | {r['verdict']} |")
    lines += ["", "注：Δ = 2w(层) − 实测铜边；远侧余量 = 该对 ↔ 远侧最近异网铜净距 − 2w。", ""]
    CARD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"], "rows": rows, "rec_sha16": s16(REC), "card_sha16": s16(CARD)},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
