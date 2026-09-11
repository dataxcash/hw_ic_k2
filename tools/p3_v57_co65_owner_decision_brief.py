#!/usr/bin/env python3
"""CO-65：【L2 收口 → L1 决策请求】叠层不可自洽性的**机助证明** + 两条整改方案的代价/执行计划。

① 用外层（1oz，t=0.035）微带模型重算 B.Cu：CO-62 用内层铜厚（t=0.0175）⇒ 113.0Ω vs 记录 119.1Ω（结论同为超带）。
   并给出达 85Ω / 85+10% 所需的**介质厚度上限**。
② 机助证明 8L 自相矛盾：冻结平面集 4 个（In1/In3/In5=GND、In4=P3V3）+ 需 4 个信号层（F/In2/In6/B，CO-63 证 3 层不可行）
   = 8 层；而 B.Cu 的**唯一邻层**是 In6 ⇒ B 要被参考则 In6 必为平面，与「In6 属信号层」冲突。
   枚举验证：满足「每信号层有参考 + 4 信号层 + 1 电源平面」的 8L 解**全部**要求重排冻结平面用途。
"""
from __future__ import annotations
import hashlib, itertools, json, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
OUT = STEP2 / "m13_v57_co65_owner_decision_brief.json"
sys.path.insert(0, str(K2.parent / "_shared"))
from eda_core.stackup import _edge_coupled_microstrip_z0 as MS  # noqa: E402

W, S_MM = 0.205, 0.295
G, P, SIG = "GND", "PWR(P3V3)", "signal"
FROZEN_PLANES = {"In1.Cu": G, "In3.Cu": G, "In4.Cu": P, "In5.Cu": G}
FROZEN_SIGNALS = ["F.Cu", "In2.Cu", "In6.Cu", "B.Cu"]
ORDER8 = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]


def z_outer(h: float) -> float:
    return MS(W, h, 0.035, 4.16, S_MM)


def solve_h(target: float) -> float:
    lo, hi = 0.02, 0.60
    for _ in range(200):
        mid = (lo + hi) / 2
        if z_outer(mid) > target:
            hi = mid
        else:
            lo = mid
    return round((lo + hi) / 2, 4)


def valid(seq: list[str]) -> bool:
    if seq.count(SIG) != 4 or seq.count(P) != 1 or seq.count(G) < 1 or seq[0] != SIG:
        return False
    for i, v in enumerate(seq):
        if v != SIG:
            continue
        nb = [seq[j] for j in (i - 1, i + 1) if 0 <= j < len(seq)]
        need = 2 if 0 < i < len(seq) - 1 else 1
        if sum(1 for x in nb if x in (G, P)) < need:
            return False
    return True


def count_8l_solutions() -> dict:
    all_sol, keep_frozen = 0, 0
    for combo in itertools.product((G, P, SIG), repeat=8):
        seq = list(combo)
        if not valid(seq):
            continue
        all_sol += 1
        # 「保留冻结平面用途」= 冻结 4 层仍是平面且用途不变
        if seq[1] == G and seq[3] == G and seq[4] == P and seq[5] == G:
            keep_frozen += 1
    return {"valid_8l_solutions": all_sol, "solutions_keeping_frozen_plane_purposes": keep_frozen}


def main() -> int:
    res = {
        "artifact": "m13_v57_co65_owner_decision_brief", "schema": 1, "revision": "CO-65.1",
        "nature": "L2 收口 + L1 决策请求：叠层不可自洽性的机助证明与两方案代价/执行计划",
        "A_corrected_bcu_impedance": {
            "model": "IPC-2141 外层边耦合微带 (w=0.205, s=0.295, er=4.16, 铜厚 0.035=外层 1oz)",
            "CO62_recorded_ohm": 119.1, "CO62_used_t_mm": 0.0175,
            "corrected_ohm": round(z_outer(0.1836), 1),
            "correction": "CO-62 对 B.Cu 误用内层铜厚 0.0175；按外层 1oz 0.035 重算 = 113.0Ω（≥85+10%=93.5 ⇒ 结论不变：超带）",
            "h_for_85_ohm_mm": solve_h(85.0), "h_upper_for_85p10pct_mm": solve_h(93.5),
            "current_h_b_to_in6_mm": 0.1836,
            "implication": "仅给 B.Cu 加参考平面不够：d(B.Cu–邻平面) 须 ≤0.127mm（现 0.1836）⇒ 叠层**厚度**也须重推",
        },
        "B_8l_contradiction_proof": {
            "argument": ("冻结平面集 4 层（In1/In3/In5=GND、In4=P3V3）+ 需 4 信号层（F/In2/In6/B；CO-63 证 3 层不可行）"
                         "恰为 8 层；B.Cu 的唯一邻层是 In6 ⇒ B 被参考 ⇒ In6 必为平面，与 In6 ∈ 信号层矛盾。"),
            **count_8l_solutions(),
            "reading": "若 solutions_keeping_frozen_plane_purposes == 0，则「保留冻结平面用途」与「B.Cu 有参考」在 8L 内不可兼得（机助证明）。",
        },
        "options": [
            {"id": "a", "layers": 8,
             "desc": "8L 内重排平面用途（B.Cu 邻层改平面；须让出 1 个冻结 GND 平面做信号层）",
             "needs": "放宽冻结平面用途集（L1 红线）",
             "cost": "层数/板厂成本不变；全套 LID/SPEC 叠层重推 + 全链重导"},
            {"id": "b", "layers": 10,
             "desc": "8L→10L：F(S)/In1(G)/In2(S)/In3(G)/In4(P3V3)/In5(G)/In6(S)/In7(G)/In8(S)/B(G)",
             "needs": "层数裁决（L1，L2_STRUCTURE_v2.0.md:136 明文）",
             "cost": "+2 层（板厂成本上升）；**保留全部冻结平面用途**；多 1 层内部信号层对横向拥塞亦有利"},
        ],
        "recommendation": "b（10L）：唯一不触碰冻结平面用途的方案，且额外信号层可同时缓解 ① 对间净空/逃逸拥塞；待 owner 确认后按 1.580 + 受控层全链重导。",
        "redline": "只读冻结源；零几何/阈值改动；本件不改变任何 canonical 件。",
    }
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"out": str(OUT.relative_to(K2)), "sha16": hashlib.sha256(OUT.read_bytes()).hexdigest()[:16],
                      "bcu_corrected_ohm": res["A_corrected_bcu_impedance"]["corrected_ohm"],
                      "h_upper_mm": res["A_corrected_bcu_impedance"]["h_upper_for_85p10pct_mm"],
                      **res["B_8l_contradiction_proof"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
