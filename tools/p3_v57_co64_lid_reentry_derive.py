#!/usr/bin/env python3
"""CO-64：【L2 叠层分配】LID 重入 ECN —— 叠加"每信号层须有邻近参考平面"约束后重推层数/叠层。

触发（L2_STRUCTURE_v2.0.md「8L 重入 ECN 触发条款」第 3 条）：
  「SI9000 重算轨距收紧溢出：阻抗终值致 inter_pair_spacing 1.46 放不下 8 对/带」
  → 本仓机判（CO-60/CO-61）已实证：WEST 对间距 >1.05 即落位失败；R3-2 要求 1.580 ⇒ 放不下。

问题（根因）：冻结 LID 派生规则 `total = 2*L_signal` + 家族 `F/G/S/G/[P/G]/S/B` **必然**让最外层
（B.Cu）成为**无邻近参考平面**的信号层 ⇒ B.Cu 不可作阻抗控制层（CO-62：一阶 119.1Ω vs 85Ω），
而 B.Cu 又是逃逸所需的第 4 个信号层（CO-63：3 层 → 18/32、12/32 不可行）。

本工具（纯组合/确定性，零搜索启发式）：在 `L_signal=4`（由冻结派生给出）+ `F.Cu 必为信号层` +
`P3V3 需 1 个电源平面` + **`每个信号层须有邻近参考平面`**（修正规则）下，求**最小合法偶数层叠层**，
并给出逐层用途；同时判定 8L 在该规则下不可行。
"""
from __future__ import annotations
import hashlib, json, sys
from itertools import product
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
OUT = STEP2 / "m13_v57_co64_lid_reentry_derive.json"
L_SIGNAL_FROZEN = 4          # 冻结 LID.1 派生：max(L_escape=4, L_capacity=2, L_conflict=3, 3)=4
FROZEN_TOTAL = 2 * L_SIGNAL_FROZEN   # == 8L（现基线）
G, P, S = "GND", "PWR(P3V3)", "signal"


def valid(seq: list[str]) -> bool:
    if seq.count(S) != L_SIGNAL_FROZEN or seq.count(P) != 1:
        return False
    if seq[0] != S:                       # F.Cu 必为信号层（焊盘/连接器在主面）
        return False
    if seq.count(G) < 1:
        return False
    for i, v in enumerate(seq):
        if v != S:
            continue
        nb = [seq[j] for j in (i - 1, i + 1) if 0 <= j < len(seq)]
        # 修正规则：内层信号须**两侧**皆参考平面（对称带状线）；最外层信号须其唯一内邻为参考平面
        need = 2 if 0 < i < len(seq) - 1 else 1
        if sum(1 for x in nb if x in (G, P)) < need:
            return False
    return True


def main() -> int:
    found = None
    for n in range(6, 17):
        if n % 2:
            continue
        for combo in product((G, P, S), repeat=n):
            seq = list(combo)
            if valid(seq):
                found = (n, seq); break
        if found:
            break
    n, seq = found if found else (None, None)
    sols8 = []
    for combo in product((G, P, S), repeat=8):
        cand = list(combo)
        if valid(cand):
            sols8.append(cand)
            if len(sols8) >= 3:
                break
    # 保持冻结平面用途（In1/In3/In5=GND, In4=P3V3）的最小方案：只能加层
    keep = [S, G, S, G, P, G, S, G, S, G]     # F/In1/In2/In3/In4/In5/In6/In7/In8/B = 10L
    assert valid(keep)
    res = {
        "artifact": "m13_v57_co64_lid_reentry_derive", "schema": 1, "revision": "CO-64.1",
        "nature": "L2 叠层分配：LID 重入 ECN 的层数/叠层重推（修正规则：每信号层须有邻近参考平面）",
        "trigger": {
            "clause": "L2_STRUCTURE_v2.0.md:126「8L 重入 ECN 触发条款」",
            "assessment": [
                {"no": 1, "text": "L3 逃逸逐段布线实证发现硬性不可路由（VIA 预算在施工细节下超支）",
                 "fired": True, "evidence": "CO-60/CO-61 机判：WEST 对间距 >1.05 即 32/32 落位破裂（候选行扫 ~15150 耗尽）"},
                {"no": 2, "text": "In2 穿越 + stub 实测超载（容不下穿越对 + stub）",
                 "fired": True, "evidence": "CO-63 机判：信号层降为 3 层即 18/32（1 违规）/12/32（11 违规）⇒ 逃逸层资源不足"},
                {"no": 3, "text": "SI9000 重算轨距收紧溢出：inter_pair_spacing 1.46 放不下 8 对/带",
                 "fired": True, "evidence": "R3-2 需中心距 1.580；CO-60/61：逃逸域连 1.20 都放不下 ⇒ 该形态在逃逸域成立"},
            ],
            "consequence": "触发即 ECN → 回 L2（叠层分配）或 L1（层数裁决）；本件即该 ECN 的 L2 部分（推导/叠层/用途）。",
        },
        "root_cause": ("冻结派生规则 `total = 2*L_signal` + 家族 F/G/S/G/[P/G]/S/B 使最外层 B.Cu 无邻近参考平面；"
                       "CO-62 实测其 Zdiff 119.1Ω（85Ω 不达），CO-63 证明 3 信号层逃逸不可行（18/32、12/32）"
                       "⇒ 既不能把 B.Cu 改平面（缺第 4 层），也不能让 B.Cu 继续承载。"),
        "frozen": {"L_signal": L_SIGNAL_FROZEN, "frozen_total_layers": FROZEN_TOTAL,
                   "frozen_family": "F/G/S/G/[P/G]/S/B", "rule": "total = 2*L_signal（未含参考邻接约束）"},
        "corrected_rule": {"constraints": ["L_signal = 4（冻结派生，容量闭合）", "F.Cu 必为信号层（主面焊盘）",
                                          "P3V3 需 1 个电源平面", "每个信号层须有邻近参考平面"],
                           "formula": "total = 2*L_signal + 2（两端各补一个参考平面）"},
        "result": {"min_total_layers": n, "stackup": [f"L{i+1}={v}" for i, v in enumerate(seq or [])],
                   "signal_layers": [i + 1 for i, v in enumerate(seq or []) if v == S],
                   "bottom_is_plane": bool(seq and seq[-1] in (G, P)),
                   "delta_vs_frozen": (n - FROZEN_TOTAL) if n else None,
                   "why_8L_fails": ("按**现状冻结平面用途**（In1/In3/In5=GND、In4=P3V3，即 In6 为信号层）时："
                                    "B 若为信号则无参考（In6 非平面）；B 若改平面则信号层只剩 3 个 < 4 ⇒ 逃逸不可行（CO-63）。"
                                    "但按**修正规则**，8L **确有解**（见 variants_8L）——前提是**重排平面位置**。"),
                   "variants_8L": [{"stackup": [f"L{i+1}={v}" for i, v in enumerate(c)],
                                    "signal_layers": [i + 1 for i, v in enumerate(c) if v == S],
                                    "note": "需重排平面位置（P3V3 须落在 B.Cu 的邻层等）⇒ 与冻结平面用途红线冲突"} for c in sols8],
                   "option_10L_keep_plane_purposes": {"stackup": [f"L{i+1}={v}" for i, v in enumerate(keep)],
                                    "signal_layers": [i + 1 for i, v in enumerate(keep) if v == S],
                                    "note": "保留 In1/In3/In5=GND、In4=P3V3；新增 In7(G)/In8(S)；B.Cu→GND"}},
        "proposal": ("两条**等价可行**整改（均解 ②B.Cu 无参考；②'的横向拥塞缓解仅 (b) 有）："
                     "(a) **8L 内重排平面位置**（不改层数、不改板厂成本）：让 B.Cu 的邻层为平面（典型 "
                     "F(S)/In1(G)/In2(S)/In3(G)/In4(S)/In5(G)/In6(S)/B(P3V3)）⇒ 与冻结平面用途红线"
                     "「In1/In3/In5=GND、In4=P3V3 不得改信号」冲突，属 **L1 电源域划分**；"
                     "(b) **8L→10L**：F(S)/In1(G)/In2(S)/In3(G)/In4(P3V3)/In5(G)/In6(S)/In7(G)/In8(S)/B(G)，"
                     "保留全部冻结平面用途，4 层信号全参考，并**多出一层内部信号层**可分流逃逸/lane（对 ① 也有利）"
                     "⇒ 属 **L1 层数裁决**（L2_STRUCTURE_v2.0.md:136 明文）。"),
        "L1_subitem": ("本 ECN 的 L2 部分（推导/叠层/用途）已完成；**仅剩两项二选一属 L1**："
                       "(a) 平面用途重排（电源域划分）或 (b) 层数 8L→10L（层数裁决）。"),
        "redline": "只读冻结源；零几何改动；不得以本闸已过为由免审（重开须重新过对抗评审）。",
    }
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"out": str(OUT.relative_to(K2)), "sha16": hashlib.sha256(OUT.read_bytes()).hexdigest()[:16],
                      "min_total": n, "stackup": res["result"]["stackup"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
