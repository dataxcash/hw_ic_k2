# CO-117 — **L2 自裁 · 施加**：band In4 铺铜归属分配 + SPEC **rev-15**（更正 rev-14 错误键 + 闭合 In5 走廊参考缺失）

- 判定：**`L2_ALLOCATED_REV15_WRITTEN`**
- 层级裁定（**L2，非 L1**）：《宪法》ch.2 把 **走廊分配 / PDN 架构** 列 L2，且 L2 **裁判标准**明含「**参考平面**」；
  冻结 L1（`L1_TOPOLOGY_v2.0.md` §电源域 / `pd.power_partition`）= **粗分区（东=P3V3 / 西=P3V3_AUX_MCU_VDD）+ 域集合**，
  本件**不改域集合**（P3V3 / P3V3_AUX / MCU_VDD 不变）⇒ 项目先例 **CO-74**「层数/平面数/**电源域集合**/信号层数全不变 ⇒ L2」适用。
  **CO-115 / CO-116 的「band 归属 = L1」归口判定过高，本件更正。**
- 输入：SPEC rev-14 `188b01deb34c9fba`｜图纸 `m13_v57_w3_joint_assignment.json`｜板 `0e636a67c1472462`｜冻结四源 4/4 MATCH
- 工具 `tools/p3_v57_co117_band_allocation_rev15.py`｜记录 `m13_v57_co117_band_allocation_rev15.json`
- 复现：`python3 tools/p3_v57_co117_band_allocation_rev15.py`（幂等；改路径白名单断言）

## 1. 分配（零搜索：声明坐标 + 固定 POWER clearance 0.2，闭式）

| 项 | 读数 | 声明源 |
|---|---|---|
| 走廊空洞 | x`(49.8, 88.37)` = 退役 keepout band 两侧 0.2 内缩 | CO-115 |
| MCU_VDD 强制东界 | **57.75** = R29/R31–R34 东缘 **57.55** + 0.2 | `power_zones.MCU_VDD_BCU_RESISTORS_IN4` |
| P3V3 强制西界 | **85.20** = U6 P3V3 球/孔西缘 **85.40** − 0.2 | `plane_reachability_status.unresolved` × `power_pad_connect` |
| **自由区间** | x`(57.75, 85.20)` 宽 **27.45mm**，无任何声明目标 | 闭式 |
| **裁定** | 自由区间 **归东侧既有权域 P3V3**（MCU_VDD 只扩到自身目标，最小位移；P3V3_EAST basis 本已声明覆盖 U6 P3V3 球） | L2 |

⇒ `MCU_VDD_WEST` 东缘 **49.8 → 57.75**；`P3V3_EAST` 西缘 **88.37 → 57.95**（= 57.75 + 0.2）；界面中值 **57.85**。
P3V3_AUX 在 band 内的特征（via 55.6 / 57.8 / 58.9）= 桥区**簿记**（桥接层 B.Cu，CO-109 R1）⇒ 不需 In4 铜、不改域集合。

## 2. SPEC rev-15 变更（白名单断言；仅 5 类路径）

1. `in4_corridor_void_by_design_v1`（CO-115 判为事实错误）→ 退役留存 `retired_in4_corridor_void_by_design_v1`
2. 新增 `in4_band_copper_allocation_v1`（本件 L2 分配 + L2 层级依据 + L3 派生义务）
3. `power_zones[0].polygon`(P3V3_EAST) / `power_zones[1].polygon`(MCU_VDD_WEST) 边界按 §1
4. `plane_reachability_status`：P3V3 由 `unresolved` → `resolved_by_co117`（U6 6 球）；`na_scope_v1.in5_corridor_reference` 更新
5. `spec_version` → `1.1.spec-rev-15`（sha `48d6fc7c565c8862`）

阈值 / 网 / 层角色 / 坐标集 / vias / blocked / impedance / stackup / 冻结源 **未动**；板 **不存在 In4 铜**（L4 zone 0）⇒ 声明层修复。

## 3. 验证（全链重基线，rev-15）

- G4 **FEASIBLE_ALL**（34 页 / crossings 0 / work 546/546 / certs 0）主件 `8575714eb77247ca`（`route_geometry/pages/landing_rows` 与 rev-14 逐字节同）
- G5 **PASS** `frozen=True`；G6 **PASS** viol 0；G7 FAB ok / **DFM new=0** / **SI skew 0.1300** / 在册未连 0/68；板 **`0e636a67c1472462` 逐字节不变**
- **In5 参考（核心成效）**：单参考暴露 **1094.8/2727.3mm = 40.14% → 5.8mm = 0.21%**，且残余段中点 x=57.9229 **全部落在 57.75–57.95 的 0.2mm POWER 异网净距缝内**（强制，不可消除）
- 闸：co69 10/10｜co99 PASS(0/0/0/0)｜co91 PASS｜co92 candidate｜co102 42/76(+34)/42(+0)｜co88 PASS｜co104 ACCEPT_L2_NO_HDI｜co105 CLOSE_NO_SCOPE_EXTENSION｜co106 INDETERMINATE_REGION_SCOPED｜co78/81/84/97 全 PASS｜co87 参考平面行证据更新（F-2）｜co95 仅余 P3V3_AUX 西区 3 项（既有 L1）｜co98 三态 **45 / 4 / 6**（原 35/14/6）

## 4. CO-114 发现处置

- **F-1**（high）已闭合：错误键退役留存 + 取代声明键
- **F-2**（medium）已闭合：co87「参考平面」行证据文本更正（删「按设计」，改指 CO-115 更正 + 0.2mm 净距缝）
- **F-3**（low）本件记录显式补登 CO-113 漏声明的 `bcu_bridge_bands_source`（历史记录按红线不改）
- **F-4**（low）本件记录措辞收敛为「**区域条件阻抗未验**」（历史 CO-111 记录按红线不改）
- **F-6**（medium）**部分闭合**：live 链 pin 已刷新（co98←co95、co105←co98，重基线重跑）；`co109←co106` / `co110←co106` / `co110←co87` 为**已被 CO-115 取代的历史记录**，按红线「历史工件不改」**显式标注为历史 pin**（本卡 + CO-117 记录 `historical_pins`）

## 5. 非声明

不改板/阈值/冻结源；历史工件不改；零坐标搜索；不代填 L1 输入；**L3 几何（含贯通孔反焊盘净距）仍为施工确定性派生**，本件只定网归属与边界约束；
**复评债 = CO-114 rev-15 半程（须另一会话，禁自评）**；残余 0.2mm 分割 = 新增 L2 登记 SI 项（终判 SI9000 + 板厂券）。
