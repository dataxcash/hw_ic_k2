# CO-116 — **L2 预备 + L1 升级**：band x∈(50.0,88.17) 的 In4 铺铜**归属界面**（一句话可裁简报）

- 判定：**`L1_INTERFACE_REQUIRED__L2_RECOMMENDATION_READY`**
- 触发：handoff z13 §4-3「唯一硬停点」+ CO-115 §3（band 归属界面 = L1）
- 输入：SPEC **rev-14** `188b01deb34c9fba`｜板 `0e636a67c1472462`｜冻结四源 **4/4 MATCH**
- 工具：`tools/p3_v57_co116_band_ownership_interface_brief.py`｜记录：`m13_v57_co116_band_ownership_interface_brief.json` `4e9ed311f91817bf`
- 复现：`python3 tools/p3_v57_co116_band_ownership_interface_brief.py`（两次逐字节一致）

## 1. 为什么本件停在 L1（宪法依据，非本会话偏好）

《`_shared/docs/LAYOUT_CONSTITUTION.md`》ch.2 裁定表：**L1 = 板级拓扑（器件分区 / 接口朝向 / 信号流向 / 电源域划分）**；
L2 = 物理承载（叠层分配 / PDN 架构 / **走廊分配** / 过孔策略 / 等长窗口 / 热机械）。ch.1 规则一：
**「下层永远不发明决策，只执行上层已固化的决策。」** ⇒ band 内铜的**网归属拆分 = 电源域划分 = L1**，
L2 不得以「走廊分配」名义自裁；但 L2 可把该裁决压缩成**可一句话确认**的约束简报（本件）。

## 2. 机判读数（全部取自声明源；零搜索）

| 项 | 读数 | 声明源 |
|---|---|---|
| keepout band | x`[50.0, 88.17]` y`[43.44, 65.1]`（CO-95 退役） | `pd.zone_defs.retired_in4_keepout_band_6l` |
| 走廊空洞 | x`(49.8, 88.37)`（= band 两侧 0.2mm 内缩，算术吻合） | CO-115 / 两 zone polygon 边界 |
| **MCU_VDD 必须覆盖至** | **x ≥ 57.75** = 目标 R29/R31–R34 东缘 **57.55** + **0.2** | `power_zones.MCU_VDD_BCU_RESISTORS_IN4.{targets,bcu_bridge_bands}` |
| **P3V3 必须覆盖至** | **x ≤ 85.20** = U6 P3V3 球/孔西缘 **85.40** − **0.2** | `plane_reachability_status.unresolved[P3V3]` × `power_pad_connect.entries.pad_pos/via_pos` |
| P3V3_AUX band 特征 | 桥区 in-band via x = **55.6 / 57.8 / 58.9**（桥接层 = B.Cu，CO-109 R1 ⇒ 不产生该带 In4 铜） | `power_zones.P3V3_AUX_BCU_BRIDGE_IN4.vias` |
| **自由区间** | **x∈(57.75, 85.20)，宽 27.45mm — 无任何声明目标** | 上式闭式算术 |
| In5 单参考暴露（复算） | `1094.812/2727.316 = 0.401425`（declared 0.4014，16 网全 PCIe） | `in4_corridor_void_by_design_v1.evidence_in5_pcie` |

## 3. L1 问题（**一句话**）与 L2 建议

> **Q（OWNER / L1）**：band x∈(50.0,88.17) 的 In4 铺铜是否按 **「MCU_VDD 扩至 57.75 / 余下走廊归 P3V3」**
> （**单边界、全填**）裁决？

- **建议（L2 推荐，非代填）**：`MCU_VDD_WEST` 东缘 `49.8 → 57.75`；`P3V3_EAST` 西缘 `88.37 → 57.95`；
  界面中值 `x≈57.85`（L3 在自由区间内按异网反焊盘净距定精确 x）。
  ⇒ **band 内除 0.2mm 异网净距外 100% 有铜**（覆盖率 **99.48%**），**零新增 zone、单条新边界**；
  **CO-111 的 In5 40.14% 单参考暴露由此可修**（非永久缺口）。
- **备选**：各网仅扩至自身目标 ⇒ 中间 `x∈(57.75,85.2)` 仍无铜；CO-109 记录 In5←In4 miss 点
  **y 峰 35–50 / x 峰 60–80 正落此区** ⇒ 只能部分修复。
- **副带项（L3，非本件）**：精确边界须避开 P3V3_AUX in-band via（55.6/57.8/58.9）反焊盘净距；
  本件不派生几何。

## 4. 裁定后的既定路径（不新增决定）

界面一定 ⇒ 进入 **rev-15**（L2）：① 更正 rev-14 错误键 `in4_corridor_void_by_design_v1`
（→「失效 keepout 残留 ⇒ 待 L3 派生」）；② 按上述界面**派生 band 铺铜**（L3 施工确定性派生 +
DRC 核对，非求解器）；③ 一并处理 CO-114 **F-2/F-3/F-4**（措辞/声明完整性）与 **F-6**（4 记录 5 处
`inputs.*_record` provenance pin 陈旧）；④ **全链重基线 + 全部回归闸**；⑤ 换会话复评（CO-114 rev-15 半程）。

## 5. 非声明

只读；不改 SPEC/板/阈值/冻结源；**不把 band 归属写入任何 SPEC 键**（未代填界面）；不派生几何；
不重做 CO-90..CO-115；不再断言「走廊空洞 = 按设计」。
