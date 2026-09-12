#!/usr/bin/env python3
"""CO-138：【L2 分析 · 只读】as-built 对间偏差的**耦合几何画像**（角度 + 平行耦合长度）。

动机：SPEC `inter_pair_derivation_v1.scope` 明文「域外对间**长平行**」；而 CO-134 板实测量（co134）取
「异对任意两段的最小铜边」，**不区分平行/斜交** ⇒ 可能把弯折处的短程斜交计入「对间间距」。
本件不改任何阈值/判定，只把每处偏差的**客观几何**量出来，供 SI 判「长平行」阈值与串扰可接受性：
  - 站点最小铜边 + 该点两段夹角；
  - 沿 A 对按声明步长采样（0.02mm，确定性、非搜索）：|edge| ≤ req+0.1mm 的**耦合长度**，
    以及其中夹角 ≤ 10°/20° 的**平行占比**。
只读：不改板/SPEC/冻结源；无随机、无坐标搜索（固定步长积分式测量）。
CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co138_interpair_scope_probe.py
"""
from __future__ import annotations
import hashlib, json, math, re
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
S2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-19.json"
CO134 = S2 / "m13_v57_co134_req_impl_separation.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
REC = S2 / "m13_v57_co138_interpair_scope_probe.json"
CARD = S2 / "m13_v57_CO138_interpair_scope_probe.md"
STEP = 0.02          # mm，声明步长
PROX = 0.1           # mm，耦合判定余量（edge ≤ req + PROX）


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


def ang_diff(a, b):
    aa = math.degrees(math.atan2(a[6] - a[4], a[5] - a[3])) % 180.0
    ab = math.degrees(math.atan2(b[6] - b[4], b[5] - b[3])) % 180.0
    d = abs(aa - ab) % 180.0
    return min(d, 180.0 - d)


def main() -> int:
    import pcbnew
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    wby = dict(spec["impedance"]["width_mm_by_layer"])
    devs = json.loads(CO134.read_text(encoding="utf-8"))["as_built"]["deviations_open_engineering"]
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
        L, x, y, req = d["layer"], d["at"][0], d["at"][1], d["required_edge_mm"]
        sa = stem(d["pairs"][0]); sb = stem(d["pairs"][1])
        win = 1.5
        def near(s):      # 站点到**线段**的距离（长段中点可能远）
            return d_pt_seg(x, y, s[3], s[4], s[5], s[6]) < win
        A = [s for s in segs[L] if s[0] == sa and near(s)]
        B = [s for s in segs[L] if s[0] == sb and near(s)]
        coupled_len = par10 = par20 = 0.0
        best = None
        for a in A:
            ln = math.hypot(a[5] - a[3], a[6] - a[4]); n = max(1, int(ln / STEP))
            for i in range(n):
                t0, t1 = i / n, (i + 1) / n
                px = a[3] + t0 * (a[5] - a[3]); py = a[4] + t0 * (a[6] - a[4])
                dl = ln / n
                mn = None
                for c in B:
                    e = d_pt_seg(px, py, c[3], c[4], c[5], c[6]) - a[2] / 2 - c[2] / 2
                    if mn is None or e < mn[0]:
                        mn = (e, ang_diff(a, c))
                if mn is None:
                    continue
                e, ang = mn
                if best is None or e < best[0]:
                    best = (round(e, 4), round(ang, 1))
                if e <= req + PROX:
                    coupled_len += dl
                    if ang <= 10.0:
                        par10 += dl
                    if ang <= 20.0:
                        par20 += dl
        rows.append({
            "layer": L, "at": [x, y], "pairs": d["pairs"], "required_edge_mm": req,
            "min_edge_mm": best[0] if best else None, "angle_at_min_deg": best[1] if best else None,
            "coupled_len_mm": round(coupled_len, 3),
            "parallel_frac_le10deg": round(par10 / coupled_len, 3) if coupled_len else None,
            "parallel_frac_le20deg": round(par20 / coupled_len, 3) if coupled_len else None,
        })
    rec = {
        "artifact": "m13_v57_co138_interpair_scope_probe", "schema": 1, "revision": "CO-138",
        "nature": "L2 分析（只读）：as-built 对间偏差的耦合几何画像（角度 / 平行耦合长度）",
        "declared_basis": {"spec_scope": spec["net_classes"]["PCIe85"]["inter_pair_derivation_v1"]["scope"],
                           "step_mm": STEP, "proximity_mm": PROX,
                           "note": "「长平行」的**量化阈值**属 SI 域（工程未声明）⇒ 本件只给客观量，不擅自定阈值"},
        "inputs": {"board": s16(BOARD), "spec": s16(SPEC), "co134_record": s16(CO134)},
        "rows": rows,
        "verdict": "DATA_ONLY",
        "redline": "只读；不改板/SPEC/冻结源；无随机、无坐标搜索（固定 0.02mm 步长积分式测量）",
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# CO-138 — as-built 对间偏差：耦合几何画像（L2 只读）", "",
             f"- verdict：**DATA_ONLY**（不改阈值/判定；「长平行」量化阈值 = SI 域）", "",
             "| 层 | 位置 | 最小铜边 | req | 该点夹角 | 耦合长度 | 平行占比(≤10°) | 平行占比(≤20°) |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['layer']} | {r['at']} | {r['min_edge_mm']} | {r['required_edge_mm']} | "
                     f"{r['angle_at_min_deg']}° | {r['coupled_len_mm']} | {r['parallel_frac_le10deg']} | {r['parallel_frac_le20deg']} |")
    lines += ["", f"步长 {STEP}mm；耦合判定 edge ≤ req+{PROX}mm。", ""]
    CARD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"], "rows": rows, "rec_sha16": s16(REC), "card_sha16": s16(CARD)},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
