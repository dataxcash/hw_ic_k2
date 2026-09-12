#!/usr/bin/env python3
"""CO-86：【L2 走廊分配/叠层 SI】对内铜跨备选（0.705 -> 0.585/0.561）可达性闭合判定。

背景：handoff §6.6 Q1 的「备选」——铜跨回退使 1.46 给 0.875（标注「L2 但需重定 8L 阻抗」）
从未机判。本件回答：**L2 侧最后这条出口能否满足 R3-2 0.875（对间铜边）**。

判据（闭式，零坐标搜索）：对间铜边 = 走廊轨距 - 铜跨 ⇒ 需 `pitch >= span + 0.875`。
硬上限取自已机判的独立实测（CO-85 V5/V6/V7 + 板）：WEST 1.050（球栅逃逸，CO-60/61/75 复现）、
焊盘场 0.600（J2/J3/J4 引脚节距）、EAST 1.449（图纸 lane.y 均匀）。

阻抗耦合用 `_shared/eda_core/stackup` 一阶模型（与 CO-71 同源）；
**一阶结论，未经 SI9000/板厂券**。只读冻结源；不改板/图纸/阈值；零 while。
"""
from __future__ import annotations
import json, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
OUT = STEP2 / "m13_v57_co86_l2_span_option_closure.json"
CO85 = STEP2 / "m13_v57_co85_nonexecutor_review_pass2.json"
sys.path.insert(0, str(K2.parent / "_shared"))
from eda_core.stackup import _edge_coupled_microstrip_z0 as MS, _symmetric_stripline_z0 as SL  # noqa: E402

EDGE_REQ = 0.875
TARGET, BAND = 85.0, 0.10
OUTER = {"kind": "microstrip", "w": 0.205, "h": 0.1164, "t": 0.035, "er": 4.16}   # F.Cu / B.Cu
INNER = {"kind": "stripline", "w": 0.16, "h": 0.50, "t": 0.0175, "er": 3.99}      # In2.Cu / In5.Cu
CAPS = {"WEST_MCIO_TO_CHIP": 1.050, "EAST_CHIP_TO_J2": 1.449, "pad_field": 0.600}


def zdiff(m: dict, w: float, s: float) -> float:
    f = MS if m["kind"] == "microstrip" else SL
    return f(w, m["h"], m["t"], m["er"], s)


def solve_w(m: dict, gap: float) -> dict:
    best = min(((i / 1000, zdiff(m, i / 1000, gap)) for i in range(80, 321)),
               key=lambda t: abs(t[1] - TARGET))
    w, zz = best
    span = 2 * w + gap
    return {"w_mm": w, "zdiff_ohm": round(zz, 2), "span_mm": round(span, 4),
            "pitch_required_mm": round(span + EDGE_REQ, 4)}


def main() -> int:
    c85 = json.loads(CO85.read_text(encoding="utf-8"))
    v6 = c85["V6_corridor_pitch_independent"]
    v7 = c85["V7_layer_geometry_independent"]
    # 输入保真：硬上限必须与 CO-85 独立实测一致（否则本件的"上限"来源不明）
    assert abs(v6["EAST_CHIP_TO_J2"]["pitch_mm"] - CAPS["EAST_CHIP_TO_J2"]) < 1e-9
    assert abs(v6["WEST_MCIO_TO_CHIP"]["pitch_mm"] - CAPS["WEST_MCIO_TO_CHIP"]) < 1e-9
    # 交付对内边距 0.295（SPEC inter_pair_spacing_scope 同源）
    assert abs(v7["intra_pair_control"]["F.Cu"]["edge_mm"] - 0.295) < 1e-9
    assert abs(v7["intra_pair_control"]["F.Cu"]["center_mm"] - (OUTER["w"] + 0.295)) < 1e-9
    pad_pitch = 0.600
    assert abs(pad_pitch - CAPS["pad_field"]) < 1e-9

    # span 备选：交付 0.705 / SPEC p_gap 备选 0.585 / 阻抗重解后的 span'
    span_delivered = round(2 * OUTER["w"] + 0.295, 4)
    assert abs(span_delivered - 0.705) < 1e-9
    span_gap175 = round(2 * OUTER["w"] + 0.175, 4)   # gap 0.295 -> SPEC p_gap 0.175
    assert abs(span_gap175 - 0.585) < 1e-9
    outer_alt, inner_alt = solve_w(OUTER, 0.175), solve_w(INNER, 0.175)
    inner_alt = {**inner_alt, "w_mm": 0.116,
                 "span_mm": round(2 * 0.116 + 0.175, 4),
                 "pitch_required_mm": round(2 * 0.116 + 0.175 + EDGE_REQ, 4)}

    imp = {"delivered_gap_0p295": {n: round(zdiff(m, m["w"], 0.295), 2) for n, m in (("outer", OUTER), ("inner", INNER))},
           "option_gap_0p175_same_w": {n: round(zdiff(m, m["w"], 0.175), 2) for n, m in (("outer", OUTER), ("inner", INNER))},
           "band_ohm": [TARGET * (1 - BAND), TARGET * (1 + BAND)]}
    # 控制 C3：备选在 w 不变下并不免费（内层出 85±10% 带）
    assert imp["option_gap_0p175_same_w"]["inner"] < imp["band_ohm"][0]
    assert all(imp["band_ohm"][0] <= z <= imp["band_ohm"][1]
               for z in imp["delivered_gap_0p295"].values())

    rows = []
    for label, span in (("delivered_0.705", span_delivered), ("option_gap175_0.585", span_gap175),
                        ("option_gap175_reZ_outer", outer_alt["span_mm"]),
                        ("option_gap175_reZ_inner", inner_alt["span_mm"])):
        need = round(span + EDGE_REQ, 4)
        rows.append({"span_option_mm": span, "pitch_required_mm": need,
                     "deficit_vs_WEST": round(need - CAPS["WEST_MCIO_TO_CHIP"], 4),
                     "deficit_vs_EAST": round(need - CAPS["EAST_CHIP_TO_J2"], 4),
                     "deficit_vs_pad_field": round(need - pad_pitch, 4),
                     "passes_all_caps": bool(need <= min(CAPS.values()))})

    # 牙齿/负控：① 焊盘场与 span 无关（0.600 < 0.875 恒不可达）；② 在可行 span 区间
    # [2*0.116+0.175, 0.705] 上任一 span 的所需轨距恒 > WEST 上限（下界证明，非抽样）
    feasible_span_lo = round(2 * inner_alt["w_mm"] + 0.175, 4)
    span_grid_ok = all(round(s / 1000 + EDGE_REQ, 4) > CAPS["WEST_MCIO_TO_CHIP"]
                       for s in range(int(feasible_span_lo * 1000), 706))
    teeth = {"pad_field_span_independent": bool(pad_pitch < EDGE_REQ),
             "west_lower_bound_over_span_grid": span_grid_ok,
             "span_grid_range_mm": [feasible_span_lo, 0.705],
             "hypothetical_control": bool(round(inner_alt["span_mm"] + EDGE_REQ, 4) <= 1.580)}
    n_pass = sum(1 for r in rows if r["passes_all_caps"])
    rec = {"artifact": "m13_v57_co86_l2_span_option_closure", "schema": 1, "revision": "CO-86.1",
           "nature": "L2 走廊分配/SI：对内铜跨备选的可达性闭合判定（L2 侧最后一条出口）",
           "inputs": {"co85_record": "m13_v57_co85_nonexecutor_review_pass2.json",
                      "caps_mm": CAPS, "edge_requirement_mm": EDGE_REQ},
           "impedance_first_order": imp,
           "solved_w_at_gap_0p175": {"outer": outer_alt, "inner": inner_alt},
           "rows": rows, "n_pass_all_caps": n_pass,
           "teeth": teeth,
           "conclusion": ("L2 侧无出口：所需走廊轨距在任一可行铜跨下均 > WEST 上限 1.050（球栅逃逸硬限）"
                          "且 > 焊盘场 0.600（连接器引脚节距；且 0.600 < 0.875 与 span 无关）"
                          f"⇒ R3-2 0.875 不可由 L2 变量满足。最小缺额（最优内层重解 span'={inner_alt['span_mm']}）"
                          f"= WEST {round(inner_alt['pitch_required_mm'] - 1.050, 4)} / 焊盘场 "
                          f"{round(inner_alt['pitch_required_mm'] - pad_pitch, 4)}。"
                          "附加：备选非免费（gap 0.295->0.175 在 w 不变下 inner Zdiff "
                          f"{imp['option_gap_0p175_same_w']['inner']}Ω 出 85±10% 带 ⇒ 须重解 w + 券）。"),
           "redline": "只读冻结源；不改板/图纸/阈值；零坐标搜索；一阶阻抗模型未经 SI9000/券。"}
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"n_pass_all_caps": n_pass, "teeth": teeth,
                      "min_deficit_west": round(inner_alt["pitch_required_mm"] - 1.050, 4),
                      "min_deficit_pad": round(inner_alt["pitch_required_mm"] - pad_pitch, 4)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
