# m13 v57 — **G6（L4 图纸直构）收口记录：PASS**

> 2026-09-11｜卡：`m13_v57_l4_kickoff_card_v1.md`｜applier：`tools/p3_v57_l4_apply_drawing.py`
> ｜验证器：`tools/p3_v57_l4_validator.py`（KiCad pcbnew 10.0.5）｜独立验证：见 §4

## 1. 结论
- **G6 PASS**：PCB **原样消费** W3 图纸；**每节点按处方连接**；**图纸只读**；冻结四源未动。

## 2. 产物与量
| 文件 | 关键数 / sha |
|---|---|
| `m13_v57_l4_construction.json` | **66 网 / 328 段 / 256 via**（128 through F↔B + 128 **blind** In2↔B）；sha `34ce1be4bb9d5f61` |
| `k2_v4.l4.kicad_pcb`（新版板，冻结板不动）| sha `33ded90443f2e2c2`；src 冻结板 sha `f6273de613f43d05`（未变） |
| `m13_v57_l4_validation.json` | **verdict=PASS**；L4-A..E 全 True；0 违例；sha `6eb6e7a7a9acb759` |

## 3. 验收结果（L4-A..E）
- **L4-A 图纸只读**：construction.authority.drawing_sha256 == 图纸 `caa516abdaf8e823`；冻结板 sha 未变。
- **L4-B 几何=图纸**：由图纸独立重算的 (points, seg_layers, vias) 与 construction 逐段一致（0 差异）。
- **L4-C 链连续**：66 网段链端点相接（内点度=2，端点数=2）；256 via 均落于 ≥2 段异层交点。
- **L4-D 端点处方**：64 data 网链端 = chip pad / conn pad；2 REFCLK 链端 = j2_pad / far_pad。
- **L4-E 板已消费**：pcbnew 读回 `k2_v4.l4.kicad_pcb` 的 track **与 via（位置 + 物理层跨）** 与记录逐条一致
  （10 nm 容差；64.475 vs 64.474999 已归一）。板 via 层跨直方图 = `{F↔B:128, In2↔B:128}` == 图纸。

## 3.1 修复（独立验证器发现，已修）
- 独立验证器发现：初版把 256 via 全部落成 **through**，且 `construction.vias` 无层字段 ⇒ L4-E 未覆盖 via，图纸的
  blind In2↔B 意图丢失（"geometry == drawing" 对 via 失真）。
- 修复：`collapse()` 记录每个 via 的**层跨**（层变点前后层，按物理层序）；`construction.vias` 带 `layers`；
  applier 按 span 设 `VIATYPE_THROUGH`(F↔B) / `VIATYPE_BLIND`(In2↔B) + `SetLayerPair` + `LSET`；
  L4-E 增加 **via 位置 + 层跨** 对拍。修复后板直方图 = 图纸直方图。

## 4. 独立验证（必须）
- read-only 子代理复核：重跑 applier + 验证器；确认图纸 sha 只读、冻结板 sha 未变、L4-A..E 可独立重算；
  对比历史/反例给出非零即失败（非静默零）。见 ledger / handoff。

## 5. 指纹
- 图纸 `m13_v57_w3_joint_assignment.json` rev W3-CN.22 `caa516abdaf8e823`
- construction `e50e2becaa921f09`｜validation `a8bf6c0f064dbc8a`｜dst board `8266989a38802ddd`
- 冻结四源 SPEC `0bd52ed48e720b8c` / manifest `a8ef3ea8ecff99d7` / PCB `f6273de613f43d05` / rules `0a459839e15960b8`

## 6. 下一步
- **G7（L5 sign-off + learning review）**：SI/PI/EMC、DFM/DFT、制造记录 + 知识提升评审（记录是证据，不是修理许可）。

## ROOT-21 修订（O1b + O3 实施；2026-09-11）
- 图纸 rev **W3-CN.25**（`c17c5a42`）：**REFCLK 差分对 P/N 补齐**（原只布 P；现 2 页 × P/N = 4 条，P/N 分离
  ≥0.38、成对中心取见证 `pair_centre_window_y`/`channel_y`、keepout 零交 A-CN.5a PASS）；net 名取
  manifest（`PCIE_REFCLK*_P/N`）。
- L4 重发：**68 网 / 338 段 / 256 via**（construction `6fb043a1`；validation `9abcc836` PASS；板 `b63e6c09`）。
- D8/G5 验证器 v2：**PASS**（G-M1..G-M6 + 双度量 0 + A1.2/A1.3/A1.4；A1.3 现覆盖 REFCLK P/N）。
- L5 重测：DFM **479**（含新增 N 轨的 26 条）；SI 等长 **skew 24.476mm** 不变 ⇒ **G7 仍 FAIL**；
  **O1**（净距不可行，已实证与域/序无关）与 **O2**（板既有铜/读板）仍待 owner。

## W3-CN.27 复核（G6 重评：**BLOCKED / 上游变更单 UC-01**；2026-09-11，ROOT-21 之后）
- 触发：图纸由 W3-CN.25 → **W3-CN.27**（LID.1 派生 8L；up 带逃逸层 = **In6.Cu**）。G6 必须对新图纸重跑。
- L4 工具按 8L 物理叠层更新（`PHYS` 8 层；`LM` 动态映射 `In5_Cu/In6_Cu`）。

| 检查 | 结果 |
|---|---|
| L4-A 图纸只读 | **True**（drawing sha == `13dfb9f4d74224d9`；冻结板 sha `f6273de613f43d05` 未变） |
| L4-B 几何=图纸 | **True**（独立 collapse 逐段/逐 via 一致） |
| L4-C 链连续 | **True** |
| L4-D 端点处方 | **True**（64 data 网 + 2 REFCLK×2） |
| **L4-E 板已消费** | **False** ⇒ G6 **BLOCKED** |

- L4 构造记录（机械展开，零设计决策）：**68 网 / 338 段 / 256 via**
  （按层：F.Cu 146、B.Cu 64、In2.Cu 64、**In6.Cu 64**）sha `e275689aedebf399`。
- **L4-E 根因（硬阻塞，非本层可修）**：冻结源 PCB `k2_v4.kicad_pcb`（四源之一，`f6273de613f43d05`）
  为 **6 层铜** = `F.Cu/In1.Cu/In2.Cu/In3.Cu/In4.Cu/B.Cu`，**不存在 In5.Cu/In6.Cu**。
  实测：对冻结板施加 8L 图纸后，板文件仍声明 6 层铜，却含 **192 处 `In6.Cu` 线段/过孔**
  ⇒ **无效板**（落在未声明层上）。故 `board != record`（64 网 + 64 via 失配），L4-E 不可能通过。
- 上游依据（既有文献，非本会话新造）：`m13_v57_layer_intent_derived_v1.json` (LID.1) 明示
  `frozen_stackup_signal_layers = 3`、**`frozen_stackup_sufficient = false`**、`total_layers_derived = 8`；
  `m13_v57_layer_intent_adoption_v1.json` 采用该 8L。即：**8L 叠层是派生需求，冻结板尚未重发**。
- 处置：按宪法「下层发现问题无权私下妥协，必须升级变更单」⇒ **不修改冻结板**、不伪造 L4-E；
  开 **UC-01**（见 `m13_v57_l4_upstream_UC01_stackup_8L_required.md`）等 owner 裁决：
  (a) 授权 **8 层板重发**（加 In5 GND + In6 signal；叠层/阻抗/板厚/成本变更）→ 重跑 L4；或
  (b) 授权 **6L 约束下重做**（仅 3 信号层），此时须由 owner 就 A-CN.9 完整净距（SPEC 0.175）放行或修订。
- 现状：`k2_v4.l4.kicad_pcb`（sha `b63e6c09aa57e76d`）为 **上一版 W3-CN.25（6L）** 的产物，
  **不得用于本图纸**；本会话未对其就地覆写（避免产生无效板）。
- 指纹：construction `e275689aedebf399`｜validation `c1fe0eeb3876ed5c`（L4-A..D True / L4-E False，viol=1）

## G6 复核 → **PASS**（CO-03；2026-09-11，整改 #06 之后）
- 触发：整改 #06 定层纠正 ⇒ UC-01 owner 升级撤回，叠层按 **L2 容量闭合**裁定为派生 8L；
  版本化新基线 `k2_v4_8L.kicad_pcb`（sha16 `fb07d25ac426ff84`；原 `k2_v4.kicad_pcb` 不动）。
- 工具：L4 `SRC_PCB`→`k2_v4_8L.kicad_pcb`、`DST_PCB`→`k2_v4_8L.l4.kicad_pcb`；L4-A 期望 sha 同步。
- 结果（`AppDir/bin/python3.11`）：
  - `p3_v57_l4_apply_drawing.py --board`：`nets=68 segs=338 vias=256 board=k2_v4_8L.l4.kicad_pcb`
  - `p3_v57_l4_validator.py`：**`verdict=PASS  checks={L4-A: True, L4-B: True, L4-C: True, L4-D: True, L4-E: True}  viol=0`**
- ⇒ 上一节「L4-E 不可能（冻结 6L 板无 In5/In6）」的硬阻塞**已消除**（以版本化 8L 基线对齐工件）。
- 举证：`m13_v57_co03_stackup_realign.json`｜变更单：`m13_v57_CO03_stackup_baseline_realign.md`
- 备注：G7(L5) 待 **O4**（成对局部落列）并入后重签；见 `m13_v57_CO04_o4_l2_landing_ruling.md`。
