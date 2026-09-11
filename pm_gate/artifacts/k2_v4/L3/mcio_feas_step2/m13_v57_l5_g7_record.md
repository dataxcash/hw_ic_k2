# G7 / L5 记录 — k2 v57（8L）

> revision **L5-G7.7**｜图纸 **W3-CN.41** `d8fc88d6f4133fba`｜L4 板 `0e636a67c1472462`（含 SPEC 逃逸区规则域 CO-37）
> 产生：`tools/p3_v57_l5_signoff.py`（kicad-cli 10.0.5，L5-DFM.6）——**随 L5 每次重跑确定性重生成**
> ｜历史 FAIL 叙事见 CO-37/CO-43/CO-44/CO-45 变更单与 git（本件取代 L5-G7.5 的 new=60 口径）。

## 1. 结论（G7 PASS）
- SI（对内等长）：**PASS** — `max_intra_pair_skew_mm(加权电气长度) = 0.1300 <= 0.15`（34 页，含 REFCLK）。
  几何实测（CO-53）：对内中心 `0.5` mm（边距 `0.295`）vs SPEC p_gap `0.175`；对间最小中心 `0.55` vs SPEC inter_pair `0.875` ⇒ **阻抗符合性 NOT_DEMONSTRATED**（开放项 CO-53）。
- DFM：**PASS** — `new_total = 0`；L4 违规 by_type `{'silk_edge_clearance': 1, 'lib_footprint_mismatch': 29, 'lib_footprint_issues': 12}`（= 冻结基线 lib/silk，计入不计）。
- DFT（施工连通性，CO-47 谓词）：在册网未连项 **0/68**（CO-47：在册（L4 施工）网必须 0 未连项（kicad-cli unconnected_items 网名解析）；范围外网不计）。
- EMC：solder_mask_bridge `0` / copper_edge `0`；
  PI：hole_clearance `0`；pdn_status `reserved_not_poured`（铜铺铜 zone：冻结源 `0` / L4 `0` ⇒ 保留层未铺铜，CO-50）。
- **裁决（CO-69）**：无需回上层（G4..G7 全 PASS）。里程碑 tag `k2-v57-g7-l5-pass`（**仅在前述全 PASS 时**适用）；收口声明件 W3 boundary v1.36（CO-67/CO-68）。

## 2. 量（8L）
| 项 | 值 |
|---|---|
| copper layers | 8 = F/B/In1/In2/In3/In4/In5/In6（In1/In3/In6=GND、In4=P3V3；方案(a) 层数/平面数/电源域不变）|
| tracks / vias | 2523 / 252（drill ['0.2']）|
| L4 rule areas（非铜） | 4 = ESC_J2 / ESC_J3 / ESC_J4 / ESC_U6（F.Cu；SPEC 逃逸域）|
| 在册网（L4 施工） | 68（来源 `m13_v57_l4_construction.json: nets`）|
| 未连项（全板） | 348（范围外 GND/P3V3/NO_CONNECT/MCU_VDD 等，见 boundary §6.4）|
| DRC baseline（冻结板，无 .kicad_dru） | 42 = {'silk_edge_clearance': 1, 'lib_footprint_mismatch': 29, 'lib_footprint_issues': 12} |
| DRC L4（含 .kicad_dru） | 42 = {'silk_edge_clearance': 1, 'lib_footprint_mismatch': 29, 'lib_footprint_issues': 12} |
| **new violations** | **0** {}（多重集差；基线消失 **0**）|

## 3. 判据（未放宽）
- `.kicad_dru` `3148703240d54420`：实现 SPEC `constraints.escape_transition_zone`（ECN-001，`escape_clearance_mm=0.075`）+ 4 具名 rule area（J2/J3/J4/U6 pad 场）。
- **条件显式排除 `PCIE_REFCLK*`** ⇒ REFCLK 仍按 shop/netclass 判据；其 0 违规由 CO-40..CO-45 几何收敛达成（**非**借道放宽；见 CO-45 §5）。
- 域工件 `m13_v57_co37_escape_domain.json` `5616a9f873c9b844`；冻结基线板不加载 `.kicad_dru`。

## 4. 独立复算
- G5 `p3_v57_w3_constructive_validator_v2.py`（不 import 引擎）：`m13_v57_w3_validation.json` `26313087acce4d3d`（G-M1..6、A1.2/A1.3/A1.4、frozen）。
- G6 `p3_v57_l4_validator.py`：`m13_v57_l4_validation.json` `094f21a3db4e1533`（L4-A..E viol=0）。
- 跨层 DRC：`kicad-cli pcb drc --format json --severity-all --refill-zones`（冻结板 vs L4，按类型差分；CO-47 起退出码=判定）。

## 5. 指纹
图纸 `d8fc88d6f4133fba`｜landing `fcfa5c3c32ca7f87`｜G5 `26313087acce4d3d`
｜L4 construction `a9f96a458f94f820`｜L4 validation `094f21a3db4e1533`｜L4 板 `0e636a67c1472462`
｜fab `73a9d22a4adeee6d`｜dfm `40445f87be664f31`｜si `73f9b59ed5f6f3ce`
｜`.kicad_dru` `3148703240d54420`
冻结四源 `0bd52ed48e720b8c / a8ef3ea8ecff99d7 / fb07d25ac426ff84 / 0a459839e15960b8`（未改）。

End of G7 record（L5-G7.6，机器生成）。
