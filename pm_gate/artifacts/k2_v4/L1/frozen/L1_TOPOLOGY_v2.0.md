# L1 冻结：整体方案 V2 — 单 DS320PR1601 × 46mm × 6L（ECN v20→v21）

> 状态：**已冻结（2026-09-05，ECN v21，用户授权；2026-09-06 v26 评审降级补记）**。
> 本文件为 L2 结构设计的约束包络，超脱并替代 `L1_TOPOLOGY_v1.0.md`（双侧对称电容墙/WQFN 方案，
> 作废，git 保留存档）。
> 变更依据：v19 器件选型冻结（DS320PR1601）+ v20 用户裁决（板加高 46mm、单面贴、6L 先试不闭合回 8L）。
> **层数（6L vs 8L）= 6L 判定流程终定（[CACHE_STABLE] 对抗评审 PASS_WITH_CONDITIONS +
> C1-C5 条件闭合，v28 ECO 范围 A 升格，2026-09-06）**——本文件由「6L 试用 + 8L 兜底」
> 升级为「引擎级 FEASIBLE（待条件闭合）」（2026-09-06 降级修正，v26 评审 §0），再经
> C1-C5 闭合升格为「判定流程终定」（v28 ECO 范围 A：C1 via 兜底 ✅/C2 引擎口径 ✅/
> C3 SPEC 再生+⑦ evaluated ✅/C4 文档 ✅/C5 连接器级实测 + 芯片级期望一致 ✅）。
> **范围 A 诚实边界**：C5 芯片级 = per_ball 注入与期望矩阵机器一致（同源 354 ballmap）；
> 真板物理 ECO（sch/PCB 换 DS320PR1601）+ L3 施工在 scope-B 执行，届时按期望矩阵一次实测
> 核对。6L 判定链可下传 L3；8L 兜底仍为回退候选（重入条件见 L2「8L 重入 ECN 触发条款」）。
> v21 初始"闭合"判定曾被非执行者对抗评审 FAIL 退回（见 v21_realroute/REVIEW_ADVERSARIAL_v21.md，
> 因决定性逃逸项未做工具级验证）。
> **本 m14 v26 以真实 354 球坐标（v25）+ 模型层新增 per-ball 逃逸引擎（⑥ BGA_GROUP_ESCAPE
> 拓扑级 + ⑦ BGA_PER_BALL_ESCAPE per-ball 物理几何）逐球判定 FEASIBLE**：K2 8-of-16 lane
> 64 信号球 = 32 F.Cu 直出 + 32 ball-via→In2，穿越 16 对（A_PER+A_PET 板级 In2 东穿，
> B_PET/B_PER 直出）；每带 8 对 fan-out 阵列 1.2mm→走廊 1.46mm（transition 段扩张，
> 11.68≤23.36）；N/S 翼各 8 对按 ipair 口径 11.68mm≤16.2/18.8（C2 修订后重跑仍过，REFCLK
> 2.0 预留）；via 净空全 354 球 worst 0.6mm≥0.427 阈值；deficits 0 → **6L 判定流程终定
> （容量级稳健 + C1-C5 闭合，v28 ECO 范围 A 升格）**；8L 兜底仅作回退候选（重入条件见
> L2「8L 重入 ECN 触发条款」）。
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

> **[CACHE_STABLE] v2.0 对账修正（scope-B 裁决点，2026-09-06，用户/架构裁决）**：
> A/B 前缀 = TI **方向通道组**（非空间端口组）——SNLA425 Table 1-2/1-3（Downstream = CPU→A-Side→EP
> ↔ A_PEx；Upstream = EP→B-Side→CPU ↔ B_PEx）+ SNLU300 §2.4（Downstream/Upstream channel 定义）+
> SNLS683 Table 5-1（A_PER=receive/A_PET=transmit side A, Diff Input/Output）+ 功能框图（1-Channel of 16
> ×2：A 通道 = A_PER 入→A_PET 出；B 通道 = B_PER 入→B_PET 出）三重源钉死。
> 通道语义：**A 通道 = downstream（host 端 A_PER 收 → device 端 A_PET 发）；B 通道 = upstream
> （device 端 B_PER 收 → host 端 B_PET 发）**。→ **host(J2) 端球 = A_PER + B_PET；device(MCIO) 端球 =
> A_PET + B_PER**。
> 修正前本文（及 C5 矩阵 v28）按「A 组球(A_PER+A_PET)→J2、B 组球→MCIO」编码 = A_PET/B_PET 角色对调
> （若照布 → 芯片下游输出 A_PET 误接 host、上游输出 B_PET 误接 device → 链路环回失效）；本行起按
> TI 硅片真实语义。容量账中性（穿越/直出仍各 16 对、32 via/32 直出、8 对/带 fan-out 不变）。

- DN（8 lane，J2 x8 → J3/J4 x4+x4）= A 通道（downstream）：J2 host TX（PCIE_DN0-7）→ 芯片 **A_PER**
  （A 通道入，host 端收）→ 芯片内部 A 通道 → 芯片 **A_PET**（A 通道出，device 端发）→ MCIO J3(0-3)/J4(4-7)。
- UP（8 lane，J3/J4 → J2）= B 通道（upstream）：MCIO device TX（PCIE_UP0-7）→ 芯片 **B_PER**
  （B 通道入，device 端收）→ 芯片内部 B 通道 → 芯片 **B_PET**（B 通道出，host 端发）→ J2。
- **网名↔球组（对账修正后）**：J2 侧 = PCIE_DN*（→A_PER）+ PCIE_UP_OUT*_J2（←B_PET）；MCIO 侧 =
  PCIE_UP*（→B_PER）+ PCIE_DN_OUT*_MCIO（←A_PET）。
- **穿越（板级语义，v26 引擎口径 + 2026-09-06 对账修正成员）**：K2 lanes 0-7 全部落在西半球
  （bx<93.8），J2 侧网球组（**A_PER + B_PET** 各 8 对 = 16 对）西半球球经 ball-via→In2 **东穿**至东走廊
  （J2 侧，F→In2→F，2 via ≤2 硬限）；MCIO 侧网球组（**A_PET + B_PER** 各 8 对 = 16 对）西半球球 F.Cu
  **直出**西走廊（MCIO 侧）。——本行取代旧 die 级表述「DN/UP 各 8 输入侧网（A_PER/B_PER）跨芯片全长」；
  §信号流 DN/UP 方向为 die 级通道流（A 通道/J2、B 通道/MCIO），与板级穿越集合
  （J2 侧网 16 对 In2 东穿）是不同计数口径（前者 16=DN8+UP8、后者 16=A_PER8+B_PET8），
  二者并存不冲突但**禁止混用**（v26 评审 B 语义漂移修正 + scope-B 对账修正）。
- **[CACHE_STABLE] 对账修正前旧文（保留可追溯，勿引用）**：DN「J2→A_PER→B_PET→MCIO」/UP
  「MCIO→B_PER→A_PET→J2」及「A 带(A_PER+A_PET)东穿」为 A_PET/B_PET 对调版本，已被本行取代。
- REFCLK0/1：**直通，不经芯片**（redriver 协议透明零 REFCLK，v19 §3#2）。REFCLK0=J2↔J3、
  REFCLK1=J2↔J4，In2 S 翼分带 + 包地 ≥2mm。
- 低速/边带 24 网：I2C/UART/PERST#/USB/GPIO 等，走 In2 端区/B.Cu/F.Cu 外围，不争 PCIe 走廊。

## 板框 / 叠层 / 贴面（冻结）

| 项 | 值 | 依据 |
|---|---|---|
| 板框 | x∈[23,143]（120mm）；**y∈[33,79]（46mm）** | v20 用户裁决 H1 |
| 贴面 | **单面（F.Cu），B.Cu 空置** | v20 用户裁决（真板 101 件本就在 F.Cu 单面） |
| 叠层 | **6 层 F/G/S/G/P/B = 6L 判定流程终定（2026-09-05 per-ball 引擎 FEASIBLE；v26 对抗评审 PASS_WITH_CONDITIONS；v28 ECO 范围 A C1-C5 闭合升格）；8L 兜底仅回退候选（重入见 L2 条款）** | v20 用户裁决 + v21 + m14 v26 per-ball 逃逸引擎（⑦ FEASIBLE）+ v26 评审降级 + v28 ECO 升格 |
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
- v2.0 修订补记（2026-09-06，v26 对抗评审 C4 + 裁决点1 授权）：
  ① 层数表述由「已定案 6L 正式冻结」降级为「引擎级 FEASIBLE（PASS_WITH_CONDITIONS），
  待 C1-C3-C5 闭合后流程终定」；② 「穿越」语义统一为板级（A_PER+A_PET In2 东穿 16 对），
  与 die 级端口流（DN/UP 各 8 输入侧网）区分并禁混用；③ 引用 L2「8L 重入 ECN 触发条款」。
- v2.0 升格补记（2026-09-06，v28 ECO 范围 A，用户授权）：C1-C5 条件闭合 → 层数表述
  「引擎级 FEASIBLE（待条件闭合）」升格为「6L 判定流程终定」（C3: 生产 SPEC 再生
  DS320PR1601 + ⑦ evaluated FEASIBLE；C5: 连接器级真板实测一致 + 芯片级期望矩阵一致）。
  范围 A 边界：真板物理 ECO + L3 施工 = scope-B，C5 芯片级实测核对随 scope-B 一次执行。
- v2.0 对账修正补记（2026-09-06，scope-B 裁决点，用户/架构裁决）：
  ① A/B 前缀语义 = TI 方向通道组（A=downstream/CPU→EP、B=upstream/EP→CPU，SNLA425 T1-2/1-3 +
  SNLU300 §2.4 + SNLS683 T5-1 三重源），非「A 组球全朝 host」空间端口组；host(J2) 端球 =
  A_PER+B_PET，device(MCIO) 端球 = A_PET+B_PER。
  ② §信号流向 DN/UP + 穿越成员按修正后语义重写（A_PET/B_PET 角色对调）；容量账中性，6L 判定
  流程终定不变（未触发 8L 重入条款）。
  ③ C5 期望矩阵 v28 同批修正（见 c5_chip_level_expect_matrix_v28.json 补记段）。
  ④ footprint 放置帧裁决：DS320PR1601.kicad_mod（ballmap 原帧）rot-270 落位 (93.8,53.7)
  （A1→西南角），拟合本文件体包络；引擎 per_ball 帧与之 N-S 镜像、容量良性（Oracle 复核）。
