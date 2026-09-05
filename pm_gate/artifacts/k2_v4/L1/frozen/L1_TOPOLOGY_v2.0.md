# L1 冻结：整体方案 V2 — 单 DS320PR1601 × 46mm × 6L（ECN v20→v21）

> 状态：**已冻结（2026-09-05，ECN v21，用户授权）**。本文件为 L2 结构设计的约束包络，
> 超脱并替代 `L1_TOPOLOGY_v1.0.md`（双侧对称电容墙/WQFN 方案，作废，git 保留存档）。
> 变更依据：v19 器件选型冻结（DS320PR1601）+ v20 用户裁决（板加高 46mm、单面贴、6L 先试不闭合回 8L）。
> **层数定案（6L vs 8L）= 已定案 6L 正式冻结（2026-09-05，per-ball 工具级逃逸验证通过）**；
> 本文件由「6L 试用 + 8L 兜底」升级为「6L 定案」。v21 初始"闭合"判定曾被非执行者对抗评审
> FAIL 退回（见 v21_realroute/REVIEW_ADVERSARIAL_v21.md，因决定性逃逸项未做工具级验证）。
> **本 m14 v26 以真实 354 球坐标（v25）+ 模型层新增 per-ball 逃逸引擎（⑥ BGA_GROUP_ESCAPE
> 拓扑级 + ⑦ BGA_PER_BALL_ESCAPE per-ball 物理几何）逐球判定 FEASIBLE**：K2 8-of-16 lane
> 64 信号球 = 32 F.Cu 直出 + 32 ball-via→In2，穿越 16 对（A_PER+A_PET，B_PET/B_PER 直出）；
> 每带 8 对 fan-out 阵列 1.2mm→走廊 1.46mm（transition 段扩张，11.68≤23.36）；N/S 翼各 8 对
> 4.8mm≤16.2/18.8（REFCLK 2.0 预留）；via 净空 0.6mm≥0.427 阈值；deficits 0 → **6L 闭合，
> 8L 兜底不启用**。
> 引用：任何 L2/L3 不得违反本文件任何决策；与 L1_TOPOLOGY_v1.0 冲突以本文件为准。

## 器件分区（冻结）

| 区 | 器件 | 位置 | 说明 |
|---|---|---|---|
| 右 | J2 SlimSAS x8 (SFF-8654) | @ (133.8,53.7)，74p，焊盘 x∈[132.65,135] y∈[42.9,64.5] | 东缘，host 侧 |
| 中 | **U1 DS320PR1601**（nfBGA-354 22.9×9.0，pitch0.6 名义，Intel retimer common footprint） | 中心 **(93.8, 53.7)**，orient-0；体包络 x∈[82.35,105.25] y∈[49.20,58.20] | 单芯片替代 U3/U7 + 32 电容墙（≥v19 §3） |
| 左 | J3 MCIO x4 (SFF-1016) @ (59.5,44.5)；J4 MCIO x4 @ (59.5,62.7) | 38p，x∈[54.1,64.9] | 西缘，device 侧；J3=北带 y43-46、J4=南带 y61-64 |
| 外围低速 | U1 MCU/U2 DCDC/U5/E2/边带排针等（101 件真板既有） | 不变 | [L0] |

- **U1 refdes 说明**：真板 `MCU` 用 U1（见 L2 v1.2 器件完整性）；本芯片在原理图 refdes 以
  最终 YAML 为准。**本文件以「DS320PR1601」指代该 redriver**，避免与 MCU U1 混淆。

## 接口朝向（冻结）

- J2 朝右（东）、J3/J4 朝左（西）；**信号流**：host→device（DN）J2→DS320PR1601→MCIO J3/J4；
  device→host（UP）J3/J4→DS320PR1601→J2。DS320PR1601 双向线性 redriver，每 PCIe lane 双向。
- **芯片摆放 orient-0**（列 col1-10 朝西 MCIO、col26-35 朝东 J2），中心 (93.8,53.7)；
  裁决依据 v21 placement bid（P-A：B_PET→MCIO、A_PET→J2 输出组就近）。180/滑移 候选淘汰见 bid。

## 信号流向（冻结）

- DN（8 lane，J2 x8 → J3/J4 x4+x4）：J2 → 芯片 A_PORT（A_PER west 端入）→ 芯片内部 →
  芯片 B_PORT（B_PET west 端出）→ MCIO J3(0-3)/J4(4-7)。
- UP（8 lane，J3/J4 → J2）：MCIO → 芯片 B_PORT（B_PER east 端入）→ 芯片内部 → 芯片 A_PORT
  （A_PET east 端出）→ J2。
- **穿越**：DN/UP 各 8 输入侧网（A_PER/B_PER）跨芯片全长，走 In2 内层（F→In2→F，2 via ≤2 硬限）。
- REFCLK0/1：**直通，不经芯片**（redriver 协议透明零 REFCLK，v19 §3#2）。REFCLK0=J2↔J3、
  REFCLK1=J2↔J4，In2 S 翼分带 + 包地 ≥2mm。
- 低速/边带 24 网：I2C/UART/PERST#/USB/GPIO 等，走 In2 端区/B.Cu/F.Cu 外围，不争 PCIe 走廊。

## 板框 / 叠层 / 贴面（冻结）

| 项 | 值 | 依据 |
|---|---|---|
| 板框 | x∈[23,143]（120mm）；**y∈[33,79]（46mm）** | v20 用户裁决 H1 |
| 贴面 | **单面（F.Cu），B.Cu 空置** | v20 用户裁决（真板 101 件本就在 F.Cu 单面） |
| 叠层 | **6 层 F/G/S/G/P/B = 已定案（2026-09-05 per-ball 逃逸引擎验证 FEASIBLE）；8L 兜底不启用** | v20 用户裁决 + v21 + m14 v26 per-ball 逃逸引擎（⑦ FEASIBLE） |
| 电容墙 | 32×220nF 0402 **全部移除**（64 AC 集成于 DS320PR1601 TX 脚，220nF typ） | v19 §3 #2 |

## 电源域划分（冻结）

- 单 3.3V 供电（DS320PR1601 VCC1-4=30 球，内部 LDO，无 0.85/1.0V 外轨）[v20 §3]。
- 去耦：VCC 侧 + 每向 TX 的 AC（已集成）+ 电源去耦（0402/0603），B.Cu 空置可用。
- 原 P3V3/P3V3_AUX/MCU_VDD 分区语义（L1 v1.0 §电源域）结转。

## 硬约束（L2/L3 必须满足）

1. **受控过孔 ≤2/网**（F→In2→F 单换层），0.20/0.35 标准孔、孔环 ≥0.075、背钻消残桩、
   差分对称 + GND 伴行孔（L2 v1.0 v1.2b 结转）。
2. 85Ω 差分：w/g 待 JLC SI9000 重算终值冻结后定 L3 线宽；对内等长 <0.15mm；
   **对间间距 = inter_pair_spacing，已裁决（v22 用户裁决，2026-09-05）：R3-2「0.875」= 对间铜边净空
   → 对中心距 = 0.585(对铜跨) + 0.875(铜边净空) = **1.46mm**。引擎 capacity_audit 按中心距计，
   L3 跑引擎时经 route_model_config.json `capacity_audit.inter_pair_spacing` 注入 **1.46**（勿用
   冻结 drc_rules.json 的 0.875，其为铜边净空口径）；冻结轨距仍 1.08（实际排轨居中值）。**口径统一 = 1.46**。
3. REFCLK0/1 独立、包地 ≥2mm、不交叉。
4. JLC06161H 工艺极限（线宽/距 ≥0.09/0.10、过孔、板边铜 ≥0.30）。
5. B.Cu 保持空行（单面贴原则；B.Cu 允许走边带作为 L3 选项，非必需）。

## 版本

- v1.0（2026-08-13 冻结，双侧电容墙/WQFN/8L）——**作废，git 存档**。
- v2.0（2026-09-05 冻结，DS320PR1601/46mm/6L/单面）——本文件。
