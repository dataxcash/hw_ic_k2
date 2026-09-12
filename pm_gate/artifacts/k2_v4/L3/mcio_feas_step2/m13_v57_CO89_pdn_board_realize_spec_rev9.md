# CO-89（L2 自裁）— SPEC rev-9：PDN live 决策**板实化**（CO-88 FAIL → 闭合）+ 全链重基线

> 日期 2026-09-12｜工具 `tools/p3_v57_co89_pdn_board_realize_spec_rev9.py`（需 AppDir pcbnew；确定性）
> 记录 `m13_v57_co89_pdn_board_realize_rev9.json` `4f94df5981aaab45`（§7 引用）｜SPEC **rev-9** `77f5c54df88bb0ca`（rev-8 `3ec8e35e676cf89d` 原件未动）

## 1. 施加内容（CO-88 修复候选）
| 项 | rev-8（现状） | rev-9 |
|---|---|---|
| `power_pad_connect.entries` | 173（含 **55 孤儿**）| **223（0 孤儿）** |
| `power_pad_connect.blocked` | 9（含 2 孤儿）| **86（全板实，带 reason）** |
| 决策总数 / 板实覆盖 | 190（有效 118+7）| **309 = 板实 SMD 电源/地 pad 数（100%）** |
| `pd.decoupling` | `C67_C68_C72_via_to_plane`（3/3 板上不存在）| **板实按网集合**（P3V3{C74-C84}/MCU_VDD{C85,C86}/12V_IN{C88}/P3V3_AUX{C90}，机器派生）|
| 旧 BOM 决策 | —— | **`retired_superseded_bom`**（173 entries + 9 blocked）**留存对账**；解耦旧串/旧 vias 转 `decoupling_legacy_retired` / `retired_vias_superseded_bom` |

**根因已文档化**：红驱动 **U3(DN,DS160PR810 WQFN-64)+U7(UP) → U6(DS320PR1601, 354 球)** 合并；旧 ppc 基准 = 101 fp 重建板（U3=DN@62.7/U7=UP@44.7）。
**不变量机判**：L2 不变量（8 层 / 4 平面 / 3 域 / 4 信号层）不变；`pd` 以外**逐值等于 rev-8**（`unexpected=[]`）⇒ 属 **L2**。

## 2. 全链重基线（rev-9 下重跑 G4→G7）
| 件 | CO-85 基线 | rev-9 后 | 说明 |
|---|---|---|---|
| drawing | `22c2a15835857f99` | **`3d452429bbc934c3`** | 几何段（`route_geometry/pages/decision_contract/layers/method/gate_status/verdict`）**逐字节同**；唯一 delta = `inputs_sha.spec` + `frozen_sha_check` |
| landing | `b71834b43a8f2455` | `da21d0186a9c643c` | 随主件指纹 |
| G5 validation | `eac5eee6f8203d01` | `7acb3186c3b68848` | PASS、G-M1..6 True、frozen=True（含 `spec=77f5c54d…`）|
| construction / L4 val | `082fc5ae…` / `c5845039…` | `ca2ff16f6445424c` / `a87b8d17bef6edca` | L4-A..F True、viol 0 |
| **板** | `0e636a67c1472462` | **`0e636a67c1472462`（逐字节不变）** | 物理交付件未动 |
| DFM / SI | `40445f87…` / `73f9b59e…` | **不变** | DFM new=0、SI skew 0.1300 ≤ 0.15 |
| fab / G7 | `9501f66f…` / `4c9fe4ea…` | `6d85160413770fa5` / `14d4cfab81e34899` | 随构建链指纹 |

## 3. 闸态（随 rev-9 重跑）
co78 `b736a0df7226f155` PASS ｜ co81 `16b262663238a60a` PASS ｜ co84 `b927acbe46ec3007` PASS（域 ESC_J2/J3/J4/U6）｜
co87 `24aeb57f71a716f4`（3 CLOSED / 2 open 不变；扫描字段 3962→5995）｜ **co88 `f90d65369cab92dc`：FAIL → PASS**（A 0 孤儿 / B 223 覆盖 + 86 显式 blocked / C 解耦目标全板实）｜
co69 探针 `18a86c998dd6b4de` **10/10 不变** ｜ co77 引用闸 `68a5ca50f1c24abb` **PASS**（v1.54）。

## 4. 残余（如实，不得掩盖）
1. **86 个 blocked 中 U6 占 63** —— 0.5mm 球栅场内 GND 球无法落 pad→via（规则允许的显式 blocked）。若要改判为「可连接」（via-in-pad / 平面直连等），
   需 **DS320PR1601 器件资料 + SI/PI 依据** ⇒ 属有内容的 PDN 设计决策（L2，但需输入）。
2. **本次重基线使 CO-85 的复现基线失效** ⇒ **新基线的非执行者复评欠**（CO-85 证书仅对旧基线有效）。
3. PDN 压降 / 热仍 **NOT_DEMONSTRATED（缺输入）**（CO-87 §6-8）。

## 5. 非声明
零几何（板逐字节不变）、零阈值改动、冻结四源与 L1 冻结源未动、历史件不触碰、无 while/坐标搜索；
不触 L1（器件分区/接口朝向/信号流向/电源域划分/球重映射均未动）；不声称 PDN 压降/热已闭合。
