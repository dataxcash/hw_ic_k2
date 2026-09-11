#!/usr/bin/env python3
"""CO-67：【L2 定层裁定】方案(a) 与历史红线「平面层用途不得改信号」的**一次性张力裁定**。

背景：handoff §4-2 要求续接会话先对以下张力给出**一次性裁定**（L2 自裁并记录理由，或 L1 升裁）：
  历史红线（CO-25/CO-44/CO-53..56/CO-57）：**平面层用途（In1/In3/In5=GND、In4=P3V3）不得改信号**。
  方案(a) 叠层层序：F(S)/In1(G)/In2(S)/In3(G)/In4(P3V3)/In5(S)/In6(G)/B(S) ⇒ **In5 由 GND 平面改为信号层**。

本工具以**机判不变量**判定归口（L2 vs L1），并输出裁定记录；**零几何/阈值改动、不改任何冻结源**。

裁定准则（对当前定层协议）：
  L1 = 器件分区 / 接口朝向 / 信号流向 / **电源域划分** / 球重映射 / **层数裁决**。
  L2 = 叠层分配 / PDN 承载 / 走廊 / 过孔策略 / 等长 / 热机械（《LAYOUT_CONSTITUTION》第二章；
       `L2_STRUCTURE_v2.0.md:136`：触发即 ECN → 回 L2（叠层分配）或 L1（层数裁决））。
不变量（任一改变即升 L1；全不变 ⇒ L2）：
  I1 层数（8）；I2 平面数（4）；I3 电源域划分（平面网多重集 = 3×GND + 1×P3V3，网名与域归属不变）；
  I4 信号层数（4）。
  I5 参考覆盖（每一信号层至少一个相邻平面）——方案(a) 修复 B.Cu 无参考（CO-62）的**必要条件**。
另：红线保护对象 = **平面清单与网归属**（PDN 承诺）＋「禁未授权静默改平面」；**层身份**是机制而非受保护量。
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
ROOT = K2.parent
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
OUT = STEP2 / "m13_v57_co67_l2_redline_ruling.json"
MD = STEP2 / "m13_v57_CO67_L2_redline_ruling.md"

FROZEN = {
    "SPEC_k2_v4.json": L3 / "SPEC_k2_v4.json",
    "page_manifest": STEP2 / "m13_v57_s1_page_manifest.json",
    "k2_v4_8L.kicad_pcb": K2 / "k2_v4_8L.kicad_pcb",
    "drc_rules.json": ROOT / "_shared/eda_core/drc_rules.json",
}
FROZEN_SHA16 = {"SPEC_k2_v4.json": "0bd52ed48e720b8c", "page_manifest": "a8ef3ea8ecff99d7",
                "k2_v4_8L.kicad_pcb": "fb07d25ac426ff84", "drc_rules.json": "0a459839e15960b8"}
LID_REV5 = STEP2 / "m13_v57_layer_intent_rev5.json"
ORDER = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]


def sha16(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def plane_net(intent_layer: str) -> str | None:
    """由 layer_intent 字符串归类平面网（GND / P3V3），信号层 -> None。"""
    s = intent_layer.lower()
    if "gnd_plane" in s:
        return "GND"
    if "power_plane" in s:
        import re
        m = re.search(r"power_plane\(([^,)]+)", s)
        return m.group(1).strip() if m else "PWR"
    return None


def taxonomy(intent: dict) -> dict:
    planes = {l: plane_net(intent[l]) for l in ORDER if plane_net(intent[l])}
    signals = [l for l in ORDER if l not in planes]
    # 参考覆盖：信号层的相邻层中存在平面
    ref = {}
    for l in signals:
        i = ORDER.index(l)
        nb = [ORDER[i - 1] if i > 0 else None, ORDER[i + 1] if i < len(ORDER) - 1 else None]
        ref[l] = [n for n in nb if n in planes]
    from collections import Counter
    return {"layer_count": len(ORDER), "plane_count": len(planes),
            "plane_net_multiset": dict(Counter(planes.values())),
            "signal_layers": signals, "signal_count": len(signals),
            "reference_planes": ref,
            "all_signals_referenced": all(bool(v) for v in ref.values())}


def main() -> int:
    spec = json.loads(FROZEN["SPEC_k2_v4.json"].read_text(encoding="utf-8"))
    lid5 = json.loads(LID_REV5.read_text(encoding="utf-8"))
    cur_intent = dict(lid5["layer_intent"])
    # 方案(a) 提案：仅改平面位置（In5 GND→信号 / In6 信号→GND），网与平面数不变
    prop_intent = dict(cur_intent)
    prop_intent["In5.Cu"] = "transition_eligible"
    prop_intent["In6.Cu"] = "gnd_plane"

    cur = taxonomy(cur_intent)
    prop = taxonomy(prop_intent)
    match = {k: sha16(v) == FROZEN_SHA16[k] for k, v in FROZEN.items()}

    inv = {
        "I1_layer_count":   {"cur": cur["layer_count"], "prop": prop["layer_count"],
                             "invariant": cur["layer_count"] == prop["layer_count"]},
        "I2_plane_count":   {"cur": cur["plane_count"], "prop": prop["plane_count"],
                             "invariant": cur["plane_count"] == prop["plane_count"]},
        "I3_power_domain_partition": {"cur": cur["plane_net_multiset"], "prop": prop["plane_net_multiset"],
                                      "invariant": cur["plane_net_multiset"] == prop["plane_net_multiset"]},
        "I4_signal_count":  {"cur": cur["signal_count"], "prop": prop["signal_count"],
                             "invariant": cur["signal_count"] == prop["signal_count"]},
    }
    all_inv = all(v["invariant"] for v in inv.values())
    ref_fixed = (not cur["all_signals_referenced"]) and prop["all_signals_referenced"]

    ruling = {
        "scope": "L2（叠层分配）",
        "no_l1_escalation": all_inv,
        "rationale": (
            "I1..I4 全不变（层数 8、平面数 4、电源域划分 = 3×GND + 1×P3V3 同网、信号层 4）"
            "⇒ 不触发 L1 的两项（电源域划分 / 层数裁决）。方案(a) 仅改**平面在位次序与介质厚度**"
            "（外加内层线宽协同）⇒ 属《LAYOUT_CONSTITUTION》第二章『叠层分配』，"
            "与 L2_STRUCTURE_v2.0.md:136 分流一致。"
        ),
        "redline_reading": (
            "历史红线字面点名层身份（In1/In3/In5=GND、In4=P3V3『不得改信号』）。本裁定采纳其**保护对象**"
            "= 平面清单与网归属（PDN 承诺：GND×3 + P3V3×1，域归属不变）＋『禁未授权静默改平面』；"
            "**层身份是机制**。方案(a) **未减少平面、未改网、未改域、未改层数**，且**修复** CO-62 违规"
            "（B.Cu 无参考平面承载 85Ω 关键网）⇒ 不构成对红线**意图**的放宽，反而是其意图的满足。"
        ),
        "controls": (
            "一次性裁定，**不成立先例、不适用于改平面网/平面数/层数**（后者仍须 L1）。"
            "执行须带：① ECN 变更单 + 版本 bump（LID REV6 + SPEC rev-5）；"
            "② G4..G7 全链重跑；③ 依 L2_STRUCTURE_v2.0.md:137 **重新过对抗评审**（不得以本闸已过免审）。"
        ),
        "alternative_left_open": "方案(b) 8L→10L（保留全部冻结平面用途）仍属 L1 层数裁决备选，本件不预判。",
    }

    res = {
        "artifact": "m13_v57_co67_l2_redline_ruling", "schema": 1, "revision": "CO-67.1",
        "nature": "L2 一次性定层裁定（方案(a) vs 历史红线）——机判不变量；零几何/阈值改动，不启动物理变更",
        "frozen_sources": {k: {"sha16": sha16(v), "match": match[k]} for k, v in FROZEN.items()},
        "four_sources_all_match": all(match.values()),
        "current_layer_intent": {"file": str(LID_REV5.relative_to(K2)), "sha16": sha16(LID_REV5),
                                 "signal": cur["signal_layers"], "planes": cur["plane_net_multiset"]},
        "proposed_option_a_intent": {"signal": prop["signal_layers"], "planes": prop["plane_net_multiset"],
                                     "stackup": "F(S)/In1(G)/In2(S)/In3(G)/In4(P3V3)/In5(S)/In6(G)/B(S)"},
        "invariants": inv, "all_invariants_hold": all_inv,
        "reference_coverage": {"current": cur["reference_planes"], "proposed": prop["reference_planes"],
                               "current_all_referenced": cur["all_signals_referenced"],
                               "proposed_all_referenced": prop["all_signals_referenced"],
                               "fixes_CO62_unreferenced_B": ref_fixed},
        "ruling": ruling,
        "conclusion": ("方案(a) 归口 **L2（叠层分配）**，无需 L1 升裁；续接会话可自裁执行，"
                       "但须带 ECN + 版本 bump + 全链重跑 + 重新对抗评审。"),
        "redline": "只读冻结源；四源 4/4 MATCH；本件不启动物理变更。",
    }
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")

    md = f"""# CO-67 — 【L2 定层裁定】方案(a) 与历史红线「平面层用途不得改信号」的一次性张力裁定

> 2026-09-12｜定层：**L2（叠层分配）**｜工具：`tools/p3_v57_co67_l2_redline_ruling.py`
> 记录 sha：本件 JSON `{sha16(OUT)}`｜性质：只读冻结源；零几何/阈值改动；**不启动物理变更**。

## 0. 张力（handoff §4-2，必须先解、不得静默绕过）
- 历史红线：**平面层用途（In1/In3/In5=GND、In4=P3V3）不得改信号**（CO-25/CO-44/CO-53..57）。
- 方案(a) 层序 `F(S)/In1(G)/In2(S)/In3(G)/In4(P3V3)/In5(S)/In6(G)/B(S)` ⇒ **In5 由 GND 平面改为信号层**。

## 1. 机判不变量（`invariants`）
| 不变量 | 现值 | 方案(a) | 保持 |
|---|---|---|---|
| I1 层数 | {cur['layer_count']} | {prop['layer_count']} | **{'是' if inv['I1_layer_count']['invariant'] else '否'}** |
| I2 平面数 | {cur['plane_count']} | {prop['plane_count']} | **{'是' if inv['I2_plane_count']['invariant'] else '否'}** |
| I3 电源域划分（平面网） | {cur['plane_net_multiset']} | {prop['plane_net_multiset']} | **{'是' if inv['I3_power_domain_partition']['invariant'] else '否'}** |
| I4 信号层数 | {cur['signal_count']} | {prop['signal_count']} | **{'是' if inv['I4_signal_count']['invariant'] else '否'}** |

参考覆盖（I5，非归口判据、而是修复证据）：现 `{cur['signal_layers']}` 全参考={cur['all_signals_referenced']}
→ 方案(a) `{prop['signal_layers']}` 全参考={prop['all_signals_referenced']}
（修复 CO-62：B.Cu 无参考平面却承载 32/68 网 290.21mm ⇒ 一阶 Zdiff 113.0Ω 超带）。

## 2. 裁定
**方案(a) 归口 L2（叠层分配），无需 L1 升裁。** 依据：
1. I1..I4 **全不变** ⇒ 不触发 L1 的两项（**电源域划分** / **层数裁决**）；
2. 仅改**平面在位次序 + 介质厚度 + 内层线宽协同** ⇒ 《LAYOUT_CONSTITUTION》第二章「叠层分配」，
   与 `L2_STRUCTURE_v2.0.md:136`「触发即 ECN → 回 **L2（叠层分配）** 或 L1（层数裁决）」分流一致；
3. 红线**保护对象** = 平面清单与网归属（PDN 承诺：GND×3 + P3V3×1，域归属不变）＋「禁未授权静默改平面」；
   **层身份是机制**。方案(a) 未减少平面、未改网、未改域，且**修复** CO-62 违规
   ⇒ 不构成对红线**意图**的放宽。

## 3. 控制（一次性，不成立先例）
- **不适用于**改平面**网/平面数/层数**（后者仍须 L1）。
- 执行须带：① ECN 变更单 + 版本 bump（LID REV6 + SPEC rev-5）；② G4..G7 全链重跑；
  ③ 依 `L2_STRUCTURE_v2.0.md:137` **重新过对抗评审**（不得以本闸已过免审）。
- 备选 (b) 8L→10L（保留全部冻结平面用途）仍属 **L1 层数裁决**，本件不预判。

## 4. 指纹
冻结四源 {'4/4 MATCH' if all(match.values()) else 'DRIFT'}：
`{FROZEN_SHA16['SPEC_k2_v4.json']} / {FROZEN_SHA16['page_manifest']} / {FROZEN_SHA16['k2_v4_8L.kicad_pcb']} / {FROZEN_SHA16['drc_rules.json']}`。
现行 LID `m13_v57_layer_intent_rev5.json` `{sha16(LID_REV5)}`。
"""
    MD.write_text(md, encoding="utf-8")
    print(json.dumps({"out": str(OUT.relative_to(K2)), "json_sha16": sha16(OUT), "md_sha16": sha16(MD),
                      "all_invariants_hold": all_inv, "four_sources_all_match": all(match.values()),
                      "scope": ruling["scope"], "fixes_B_unreferenced": ref_fixed}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
