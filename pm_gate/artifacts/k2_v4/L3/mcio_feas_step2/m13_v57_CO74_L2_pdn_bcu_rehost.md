# CO-74（L2 PDN）— B.Cu 电力铜退役 + In4 承载（SPEC rev-8）；**CO-72-PDN-1 归口 L1 → L2 并闭合**

> 日期 2026-09-12｜定层 **L2**（PDN / 叠层分配）｜SPEC **rev-8** `3ec8e35e676cf89d`｜记录 `m13_v57_co74_pdn_bcu_rehost.json` `8e3bbfb0e197cf67`｜全链记录 `m13_v57_co74_chain.json` `9b1a284d2bb61e67`

## 1. 冲突（CO-72 登记、CO-73 未解）

`pd.zone_defs.power_zones[2..4]` 把 P3V3 / P3V3_AUX / MCU_VDD 铺到 **B.Cu**：

| idx | zone | net | 形态 |
|---|---|---|---|
| 2 | `P3V3_BCU_BRIDGE` | P3V3 | 顶带 `y∈[33.3,35.0] x∈[23.3,90]` + 西 pocket |
| 3 | `P3V3_AUX_BCU_BRIDGE` | P3V3_AUX | 上/下带 + 西区 + **In6 搭桥 `in6_segments`** |
| 4 | `MCU_VDD_BCU_RESISTORS` | MCU_VDD | 0.3mm 短段 ×3（R29/R31-34 上拉） |

而在 **LID REV6** 下 **B.Cu = 高速信号层**（dn 带逃逸/落段；CO-62 实测 32/68 高速网 290.21mm 铜）
⇒ 铺铜即冲突；`in6_segments` 更甚（REV6 下 **In6=GND 平面**，搭桥 = 短路）。

原裁决（T2-ECN-1/2，2026-08-23）的前提是 6L 时代 **『In4 走线带 x∈[50,88.17] 阻断跨带铜皮』**
+ SPEC 明示 B.Cu=POWER_POUR ⇒ 必须借 B.Cu 绕行。

## 2. 机判（两条，均可独立重算）

| 探针 | 结论 | 证据 |
|---|---|---|
| **P1** 引擎层集 | `LAYER_PALETTE = ["F.Cu","In2.Cu","In5.Cu","B.Cu"]` ⇒ **In4 不是布线层** | `tools/p3_v57_w3_constructive.py:154`（CO-68/69） |
| **P2** 交付板段层 | `In4.Cu` 段数 **0**（F 174 / In2 106 / In5 2204 / B 39，合 2523） | `k2_v4_8L.l4.kicad_pcb` `0e636a67c1472462` |

⇒ **REV6 下不存在 In4 走线带** ⇒ T2-ECN-1/2 绕行前提**消失**，B.Cu 电力铜无存在理由。

## 3. 归口（L1 → L2）

CO-72 曾把 `CO-72-PDN-1` 记为 **L1（电源域划分/层数）**，因其三选项 a/b/c 各触边界。本件更正：

- 按 **CO-67 已记录的 L2 不变量** —— 层数 8 / 平面数 4（3×GND + 1×P3V3）/ 电源域集合 `{P3V3, P3V3_AUX, MCU_VDD}` /
  信号层 4 —— 本件**全部不变**（`pd.power_plane_layer` 仍 `In4.Cu`）；改的只是**电力铜的承载层与分区几何** ⇒ **L2**。
- 备选 **b（增设内部电源层）= 层数**、**c（B.Cu 信号改层）= 信号流向**，二者仍属 **L1**，本件**不选**（不擅自越界）。

## 4. 改法（SPEC rev-8）

1. `power_zones[2..4]`：`layer` B.Cu → **In4.Cu**；zone 名加 `_IN4`；新增 `carrier_change.basis` / `voided_premise` / `direction_scope`。
2. 6L 口径几何**原样留存**于 `retired_polygons_bcu` / `retired_segments_bcu` / `retired_in6_segments_bcu`
   （**禁止静默放弃**）；`vias` 坐标保留 + `vias_note`（须改落 In4，L3 重导）。
3. 新几何 `polygons/segments = []` + `geometry_status = L3_CONSTRUCTION_DERIVED` + `derivation`（4 条硬要求）+
   `targets`（列明须覆盖的 pad）。
4. 新增 `pd.bcu_power_copper_policy = PROHIBITED`。
5. `pd.ecn_pending_items[CO-72-PDN-1]`：`ruled = true`，`resolution_scope` 更正为 **L2**，附裁定全文。
6. **未动**：`stackup` / `impedance` / `net_classes` / `vias` / `corridors` / `board` / `components` /
   `pd.gnd_planes` / `pd.power_plane_layout` / `pd.power_partition` / `constraints`；历史件（`_spec_rev_*`、`appendix`、
   `ecn_pending_items` 的 T2-ECN-1/2/3 原文）不触碰。

## 5. 全链重基线（G4..G7，SPEC rev-8）

| 门 | 判定 | 证据 |
|---|---|---|
| G4/W3 | **FEASIBLE_ALL**（34 页 / crossings 0 / work 546-546） | 主件 `918cc528e4a81467`；landing `74d0b085dd728288` |
| G5/W4 | **PASS**（G-M1..6 True、A1.2/.3/.4 True、frozen=True） | `m13_v57_w3_validation.json` `a6e033b4aba59e5b` |
| G6/L4 | **PASS**（L4-A..F True、viol 0；68 网 / 2523 段 / 252 via） | 板 **`0e636a67c1472462`（逐字节同基线）** |
| G7/L5 | **PASS**（DFM new=0 / disappeared=0 / 在册未连 0；SI 电气 skew **0.1300** ≤ 0.15） | dfm `40445f87be664f31`、si `73f9b59ed5f6f3ce`（均与基线逐字节同） |

**几何不变性机判（硬断言）**：`route_geometry` / `pages` / `decision_contract` / `layers` 四键哈希
与 rev-7 基线 `3cc123056a7319ff` **逐字节同**（`d39becad4f51f3af` / `e659edaa6608f3d2` / `c0e018ec4102fa72` /
`db2ee692c03204da`）；图纸 sha 变（`3cc12305…` → `918cc528…`）仅因 `inputs_sha` / `frozen_sha_check` 记 spec sha。

## 6. 性质与限制（如实）

- 本件为 **声明层修正**：引擎不消费 `pd.zone_defs.power_zones` / `ecn_pending_items`（探针 P3）⇒ 板/图纸几何**零变化**。
- **一阶结论，未经 SI9000/板厂券**；`pd` 电力铜实体（In4 分区多边形 + 反焊盘净空 + 同网连续性）=
  **L3 施工确定性派生**，须以 DRC 归零为核对（非本件宣称已建）。
- 备选 (b) 10L 仍属 **L1 层数裁决**，未触发。
