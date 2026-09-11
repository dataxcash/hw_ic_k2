#!/usr/bin/env python3
"""CO-66：【L2 叠层分配】方案(a)（8L 对称、4 层参考信号）叠层厚度自洽推导 —— 判定其 L2 可执行性。

CO-65 把方案(a) 归口"须放宽平面用途红线（L1 电源域）"。本件复核并更正：
(a) 的**电源域不变**（仍 3×GND 平面 + 1×P3V3 平面，同一网），只改**层位置/厚度** ⇒ 属 **叠层分配 = L2**。
本工具在 8L + 对称层序 `F(S)/In1(G)/In2(S)/In3(G)/In4(P3V3)/In5(S)/In6(G)/B(S)` 下，
用 CO-55 同源 IPC-2141 模型解 (外层微带 h_o↔w_o, 对称带状线 b_s↔w_s)，并检查 1.6mm 闭合（自由余隙 g4 ≥ 0.0764）。
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
OUT = STEP2 / "m13_v57_co66_option_a_stackup_derive.json"
G4_MIN = 0.0764          # 1080 单张压合厚度（最小可用垫层）
TOTAL = 1.6
sys.path.insert(0, str(K2.parent / "_shared"))
from eda_core.stackup import _edge_coupled_microstrip_z0 as MS, _symmetric_stripline_z0 as SL  # noqa: E402

S_MM = 0.295


def bis(f, t, lo, hi):
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(mid) > t:
            hi = mid
        else:
            lo = mid
    return round((lo + hi) / 2, 4)


def main() -> int:
    z_out = lambda w, h: MS(w, h, 0.035, 4.16, S_MM)     # 外层微带（1oz）
    z_str = lambda w, b: SL(w, b, 0.0175, 3.99, S_MM)    # 对称带状线（内层 0.5oz）
    rows = []
    for w_s in (0.13, 0.15, 0.17, 0.19, 0.205):
        b_s = bis(lambda b: z_str(w_s, b), 85.0, 0.05, 1.6)
        for w_o in (0.205, 0.25, 0.30, 0.35):
            h_o = bis(lambda h: z_out(w_o, h), 85.0, 0.02, 0.6)
            g4 = round(TOTAL - 2 * h_o - 2 * b_s, 4)
            rows.append({"w_signal_stripline_mm": w_s, "b_stripline_mm": b_s,
                         "w_signal_outer_mm": w_o, "h_outer_mm": h_o, "g4_free_gap_mm": g4,
                         "closes_1p6mm": g4 >= G4_MIN,
                         "z_check": {"outer_ohm": round(z_out(w_o, h_o), 1),
                                     "stripline_ohm": round(z_str(w_s, b_s), 1)}})
    feasible = [r for r in rows if r["closes_1p6mm"]]
    res = {
        "artifact": "m13_v57_co66_option_a_stackup_derive", "schema": 1, "revision": "CO-66.1",
        "nature": "L2 叠层分配：方案(a) 8L 对称叠层的厚度自洽推导（判定 L2 可执行性）",
        "layer_plan": {"order": ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"],
                       "purposes": ["signal", "GND", "signal", "GND", "PWR(P3V3)", "signal", "GND", "signal"],
                       "reference_sandwich": "F↔In1 / In2↔In1+In3 / In5↔In4+In6 / B↔In6（4 层信号全部被参考）",
                       "domain_invariance": "仍 3×GND 平面 + 1×P3V3 平面（同一网、同一域）⇒ 电源域划分**不变**"},
        "constraints": {"total_mm": TOTAL, "free_gap_min_mm": G4_MIN,
                        "solve": "外层微带 (w_o,h_o)→85Ω；内层对称带状线 (w_s,b_s)→85Ω"},
        "scan": rows, "n_feasible": len(feasible), "feasible": feasible[:6],
        "conclusion": ("方案(a) 在 8L **厚度自洽可解**（如 w_s=0.170/b_s=0.6146 + w_o=0.205/h_o=0.1101 ⇒ g4=0.1505）——"
                       "**前提是内层信号线宽由 0.205 收窄到 ~0.13–0.19**（外层次之）。"
                       "⇒ (a) 的归口更正为 **L2（叠层分配）**：层数不变、电源域不变、平面仍 4 个；"
                       "代价是**线宽几何协同变更**（级联到走廊/对内几何与全链重导）。"),
        "remaining_l2_steps": ["新 LID（REV6：layer_intent 信号层集 F/In2/In5/B，参考夹心）",
                               "SPEC rev-5（dielectric 厚度表 + impedance.per_layer + 新线宽口径）",
                               "几何协同：线宽 w_s 收窄后的对内/对间几何重解（CO-55 工具 --build 路径）",
                               "引擎 palette/冻结集版本 bump → G4..G7 全链 + SI 判据按层加权",
                               "重新过对抗评审（L2_STRUCTURE_v2.0.md:137）"],
        "redline": "只读冻结源；零 canonical 改动；本件不启动物理变更。",
    }
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"out": str(OUT.relative_to(K2)), "sha16": hashlib.sha256(OUT.read_bytes()).hexdigest()[:16],
                      "n_feasible": len(feasible),
                      "example": feasible[0] if feasible else None}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
