# CO-40 — 【L2 自裁并落地规划】D3a 根因 = 引擎 `pad_field_transit` 未定义（N 被当直线西行）；采纳方案 (C) 并给出闭式换层规格

> 2026-09-12｜提出：ARCHER（续接会话）｜性质：**L2 自裁**（走廊分配/过孔策略/资源层裁判）——**不需 owner**，闸口 CLOSED
> 依凭：`_shared/docs/LAYOUT_CONSTITUTION.md` 第二章（L2 = 物理承载：叠层分配/PDN/**走廊分配**/**过孔策略**/等长窗口/热机械；裁判权 = 高速信号/电源完整性工程师）
> 佐证（引擎自带）：`m13_v57_big_w0r_corridor_model.json` `legal_escape_hatches[3]` = `{"change": "REFCLK resource-layer ruling (currently F.Cu, separate from the In2.Cu data layer)", "target_layer": "L2"}`；`refclk_resource_domain.conflicting_resources.data_bands_cross_layer.note` = "any layer-transition via is R3/R4 construction, not a corridor row resource"
> 前置：CO-38 `3863b22451d90e57`（几何/自由通道）、CO-39 `9372802ce8f6f9be`（(B) 撤回）。本件**取代** CO-38 §0 与 CO-39 §3 的"待 owner (A)/(C)"：**(A) 不采用（属 L1 信号流向，无需触发）**。

## 0. 结论
1. **D3a 根因（机械级）** = `m13_v57_w3_joint_assignment.json`（`0261e0b0a598df6d`）中 REFCLK 两页的 **`pad_field_transit` 字段为 "delegated to connector side (W2/R3-R4)"，即"未定义"**；引擎把 N 线画成**从外列焊盘直线西行 F.Cu**，L4 施工照直线实现 ⇒ 60 条 DFM。
2. 该直线**物理不可能**：内列墙同排缝 `0.6−0.35=0.25mm`，最小可通 = `0.205+2×0.075=0.355 > 0.25`（店规 0.175 更甚）；实测 N 线 y=46.09 距内列 pad 11 北缘（46.075）仅 **0.015mm**。
3. **采纳 (C)**：REFCLK N（外列 pad）在 J2 逃逸区内做**一次换层 dip**（F.Cu → In2 → F.Cu），从两列缝下穿内列墙；P（内列 pad）保持 F.Cu 直出。规格见 §2，全部按**闭式**给出、零搜索。
4. **owner 无需裁定**（(B) 已撤回、无 L1 变更）：闸口由 L2 自裁关闭。**DFM 仍 = 60（本轮零几何落地）**。

## 1. 现状（引擎模型实读）
| 页 | 引擎 N 路径（节选） | 说明 |
|---|---|---|
| `PCIE_REFCLK0/input` | `[135.0,45.9] → [135.0,46.09] → [106.757,46.09] → [82.35,46.09] → [58.3,45.75]` | 直线西行穿过内列墙 |
| `PCIE_REFCLK1/input` | `[135.0,51.3] → [135.0,51.49] → [106.757,51.49] → …` | 同上 |

J2 逃逸区现场占用（引擎模型，x∈[131.0,135.0] y∈[44.0,53.5]）：
- **F.Cu 数据扇接地段（`#fcu_land`，P 侧 x 至 132.65）**：UP1 P y[43.85,44.10]、UP2 N y[46.85,47.10]、UP3 P y[47.45,47.70]、UP4 N y[48.65,48.90](x≥131.65)、UP5 P y[49.25,49.50]、UP6 N y[52.25,52.50]、UP7 P y[52.85,53.10]。
- **In2 竖直 stub 列**：x=130.49 y[47.45,60.68]（UP3 P）、x=131.07 y[52.85,66.48]（UP7 P）、x=131.65 y[48.65,62.13]（UP4 N）。
- **两列缝 x∈[133.3,134.35] 全 y 无铜**；**In2 在 x∈[131.0,134.6] y∈[44,47.6] 无铜**；F.Cu 自由 y 槽 = [44.10,46.85]（REFCLK0）与 [49.50,52.25]（REFCLK1）。

## 2. 闭式规格（transit spec，实施依据）
**通用**：N 线 = 外列焊盘 → F.Cu 短 stub 进两列缝 → **via#1 下到 In2** → In2 西行下穿内列墙 → **via#2 上到 F.Cu**（x ≤ 131.525）→ 汇入既有 F.Cu 轨。P 线不变（内列直出）。轨 y 不变（N: 46.09 / 51.49；P: 45.71 / 51.11）。

| 项 | REFCLK0（pad 12, y=45.9） | REFCLK1（pad 30, y=51.3） |
|---|---|---|
| via#1（下） | `(133.825, 46.09)`：缝内，距 pad 11/12 边 **0.35** ≥ pad_edge_clearance 0.3 ✓ | `(133.825, 51.49)`：同 ✓ |
| In2 路径 | 直线西行 `y=46.09`，`x 133.825→131.45`（该 y 无任何 In2 铜）✓ | **U 形绕行**（避 x=131.65 列 y≥48.65）：`(133.825,51.49)`→西至 `x≈132.4`→北至 `y=48.30`（跨 x=131.65 处该列未起，净 0.2475 ✓）→西至 `x=131.07`→南降至 `y=51.49`（落在 130.49/131.65 两列间通道，宽 0.955，两侧净 0.375 ✓） |
| via#2（上） | `(131.45, 46.09)`：距内列西缘 132.0 → **0.375** ≥0.3 ✓ | `(131.07, 51.49)`：距内列西缘 **0.755** ✓；距 UP7 P 接地段角 1.185 ✓、UP6 N 0.585 ✓ |
| In2 dip 长度 | ≈2.4mm | ≈8.0mm |
| 新过孔 | 2（每线 ≤2 ✓） | 2（✓） |

**约束核验**：`vias.std` drill 0.2 / annular 0.075（外径 0.35）✓；`vias.high_speed` `no_via_in_pad` ✓（via 均在缝/焊盘西侧）、`pad_edge_clearance_mm 0.3` ✓、`back_drill` ✓（through + 背钻，与数据扇 F↔In2 同工艺类）、`每线 ≤2` ✓；In2 = "stripline dual GND ref (In1/In3)" ⇒ SI 参考平面合格（**这是不选 B.Cu 的原因**：8L LID.1 中 B.Cu 参考层为 In6 信号层，非定阻抗环境）。
**等长**：N 增 ~2.4mm(REFCLK0)/~8.0mm(REFCLK1) ⇒ 须 **P 侧等长补偿**（幂绕）使 `intra_pair_skew_mm ≤ 0.15`；F.Cu 轨 x∈[82,131] 约 49mm，幂绕容量足够（沿用 CO-17 o4 幂绕机制）。层间速度差（微带/带状线）二次项，计入幂绕刻度。
**过孔预算**：受控过孔 214 → 218 ≤ 300 ✓；按 `gnd_stitch_via=True` 须在 REFCLK 每对 via 旁加对称 GND 伴行孔。

## 3. 须版本化的判据/资源变更（红线："判据改动一律版本 bump 新文件 + 变更单"）
1. **`SPEC_k2_v4.spec-rev-3.json`**：`escape_transition_zone` 作用域纳入 **REFCLK J2 侧 transit**（`no_via` 对该域放宽为"≤2 via/线"，其余保持 `no_90deg` 等）；In2 加入该域可通行层；`refclk_isolated` 语义收窄为"J2 逃逸区外维持隔离"（区内只允许本次规定的单次换层，不与数据扇共走廊）。
2. **`.kicad_dru` v2**（CO-37 生成器 `p3_v57_co37_emit_dru.py` 扩展）：`ESC_J2` 域内去掉 `!(A/B.NetName == 'PCIE_REFCLK*')` 排除（**仅 ESC_J2**；ESC_J3/J4/U6 保持排除）；域外维持 shop/PCIe85。判据数值不变（0.075 仅在域内）。
3. **见证件 v2**：`pad_field_transit` 由 "delegated" 改为本件 §2 的闭式形状（含 `via1/via2` 坐标、In2 waypoints、`layer_seq`），并保留 CO-25 要求的**数据扇 F.Cu 接入铜包络**入 keepout。

## 4. 未改物 / 红线
未改四源（`0bd52ed48e720b8c / a8ef3ea8ecff99d7 / fb07d25ac426ff84 / 0a459839e15960b8`，本会话实读 MATCH）、未改引擎/见证件/板/图纸/ALLOC/判据/`.kicad_dru`；**几何零落地 ⇒ DFM 仍 = LAYOUT 60（new: clearance 8 + shorting 9 + tracks_crossing 5 + mask 38）**；`LAYOUT` 未放宽任何净距/skew 阈值；无坐标搜索、无暴力迭代、`while=0`、无 partial pass。

## 5. 下一步（实施顺序，L2）
1. 出 `spec-rev-3` + `.kicad_dru` v2（版本化 + 变更单）。
2. 引擎 `refclk` 页 `pad_field_transit` 实施 §2 闭式形状（rev bump `W3-CN.38`），并出见证件 v2 → 引擎 pin sha。
3. 重跑 G4→G7，**验收：`new 60 → 0`，且 only-REFCLK 族消失、数据/其他保持 0、无 <0.075 项消失**（若 In2 dip 引入新项 ⇒ 转缺口报告，禁迭代）。
4. `new=0` ⇒ **D4 milestone tag**。
