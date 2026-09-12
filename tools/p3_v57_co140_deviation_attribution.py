#!/usr/bin/env python3
"""CO-140：【L2 分析 · 只读】as-built 对间偏差的**归因分类**（接口固有 / 路由可改 / 斜交）。

对 CO-134 登记的域外 3 处，判定其「能否由路由消除」：
  - 若 A/B 两网**最近焊盘中心距 < 3w(层)** ⇒ 3W 在该接口焊盘墙**数学不可能**（封装/接口固有）；
    最小可达铜边 = 焊盘中心距 − w < 2w ⇒ 路由无法消除。
  - 否则若该点耦合区**平行占比 ≈ 0**（斜交扇出）⇒ 属 SPEC「域外长平行」口径之外。
  - 否则 ⇒ **路由可改**（走廊/间距构造性调整可满足 2w）。
附带：站点是否落在已声明逃逸域 rect 内（ECN-001，frozen）。
只读；不改板/SPEC；零坐标搜索。
CLI: ../AppDir/usr/bin/python3.11 tools/p3_v57_co140_deviation_attribution.py
"""
from __future__ import annotations
import hashlib, json, math, re
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
S2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-19.json"
CO134 = S2 / "m13_v57_co134_req_impl_separation.json"
CO138 = S2 / "m13_v57_co138_interpair_scope_probe.json"
CO37 = S2 / "m13_v57_co37_escape_domain.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
REC = S2 / "m13_v57_co140_deviation_attribution.json"
CARD = S2 / "m13_v57_CO140_deviation_attribution.md"


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main() -> int:
    import pcbnew
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    wby = dict(spec["impedance"]["width_mm_by_layer"])
    devs = json.loads(CO134.read_text(encoding="utf-8"))["as_built"]["deviations_open_engineering"]
    scope = {tuple(r["at"]): r for r in json.loads(CO138.read_text(encoding="utf-8"))["rows"]}
    rects = [(d["id"], d["rect_mm"]) for d in json.loads(CO37.read_text(encoding="utf-8"))["domains"]]
    b = pcbnew.LoadBoard(str(BOARD))

    def pads_of(net):
        out = []
        for m in b.GetFootprints():
            for p in m.Pads():
                if p.GetNetname() == net:
                    out.append((m.GetReference(), p.GetNumber(),
                                pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)))
        return out

    rows = []
    for d in devs:
        L, x, y = d["layer"], d["at"][0], d["at"][1]
        w = wby[L]; need = 3 * w
        A, B = pads_of(d["pairs"][0]), pads_of(d["pairs"][1])
        best = None
        for a in A:
            for c in B:
                dd = math.hypot(a[2] - c[2], a[3] - c[3])
                if best is None or dd < best[0]:
                    best = (round(dd, 4), a[0], a[1], c[0], c[1])
        pitch = best[0] if best else None
        in_esc = [i for i, (x0, y0, x1, y1) in rects if x0 - 1e-9 <= x <= x1 + 1e-9 and y0 - 1e-9 <= y <= y1 + 1e-9]
        g = scope.get((x, y), {})
        pf = g.get("parallel_frac_le10deg")
        if pitch is not None and pitch < need - 1e-9:
            cls, why = "INHERENT_INTERFACE_PITCH", (
                f"两网最近焊盘中心距 {pitch} < 3w={need:.4f} ⇒ 3W 在该焊盘墙数学不可能；"
                f"最小可达铜边 = {round(pitch - w, 4)} < 2w={round(2 * w, 4)} ⇒ 路由无法消除")
        elif pf is not None and pf <= 0.2:
            cls, why = "OBLIQUE_OUT_OF_LONG_PARALLEL", (
                f"耦合区平行占比(≤10°)={pf}（该点夹角 {g.get('angle_at_min_deg')}°）⇒ 不属 SPEC「长平行」口径")
        else:
            cls, why = "ROUTING_FIXABLE", (
                f"焊盘中心距 {pitch} ≥ 3w={need:.4f} 且耦合区平行（占比 {pf}）⇒ 走廊/间距构造性调整可满足 2w")
        rows.append({"layer": L, "at": [x, y], "pairs": d["pairs"], "w_mm": w, "three_w_mm": round(need, 4),
                     "min_pad_pitch_mm": pitch, "pad_pair": best[1:] if best else None, "in_escape_rect": in_esc,
                     "min_achievable_edge_mm": round(pitch - w, 4) if pitch is not None else None,
                     "parallel_frac_le10deg": pf, "angle_at_min_deg": g.get("angle_at_min_deg"),
                     "delta_needed_mm": d["margin_mm"], "classification": cls, "why": why})
    counts = {c: sum(1 for r in rows if r["classification"] == c)
              for c in ("INHERENT_INTERFACE_PITCH", "OBLIQUE_OUT_OF_LONG_PARALLEL", "ROUTING_FIXABLE")}
    rec = {"artifact": "m13_v57_co140_deviation_attribution", "schema": 1, "revision": "CO-140",
           "nature": "L2 分析（只读）：as-built 对间偏差归因分类（接口固有 / 斜交 / 路由可改）",
           "inputs": {"board": s16(BOARD), "spec": s16(SPEC), "co134_record": s16(CO134), "co138_record": s16(CO138)},
           "rows": rows, "counts": counts, "verdict": "ATTRIBUTED",
           "redline": "只读；不改板/SPEC/冻结源；零坐标搜索"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# CO-140 — as-built 对间偏差归因（L2 只读）", "",
             f"- 计数：{json.dumps(counts, ensure_ascii=False)}", "",
             "| 层 | 位置 | 焊盘距 | 3w | 最小可达铜边 | 2w | 平行占比 | 归因 |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['layer']} | {r['at']} | {r['min_pad_pitch_mm']} | {r['three_w_mm']} | "
                     f"{r['min_achievable_edge_mm']} | {round(2*r['w_mm'],4)} | {r['parallel_frac_le10deg']} | {r['classification']} |")
    lines += ["", "归因：接口固有 = 焊盘中心距 < 3w（路由无法消除）；斜交 = 耦合区平行占比 ≈ 0；路由可改 = 其余。", ""]
    CARD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"], "counts": counts, "rows": rows,
                      "rec_sha16": s16(REC), "card_sha16": s16(CARD)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
