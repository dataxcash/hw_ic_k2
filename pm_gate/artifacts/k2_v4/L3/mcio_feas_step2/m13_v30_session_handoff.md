# M14 v30 — 层数定案流程终定后 scope-B：真板物理 ECO 落地 + A/B 端口对账修正 + C5 芯片级实测

> 状态：**本 session = scope-B（真板物理 ECO + C5 芯片级实测核对）**。承接 m13_v29_session_handoff.md
> （6L 判定流程终定，C1-C5 范围 A 闭合，mcio_feas task closed）。
> 结果：**裁决门 2 项（A/B 端口语义 + footprint 放置帧）→ 用户/架构裁决 → L1/L2 frozen 对账修正 +
> C5 期望矩阵更新 + 真板物理 ECO 落地（备份+记录）+ C5 芯片级实测 130 断言 PASS**。
> L3 施工验证/QA/S 状态机 = 体量超本 session 可靠边界，登记 open gap（详见 §3）。

## 0. 裁决门与授权（用户/架构）

- **裁决点1（A/B 端口语义，session 目标项 3 预设冲突场景）**：TI 三重主源（SNLS683 Table 5-1 +
  SNLA425 Table 1-2/1-3 + SNLU300 §2.4）显示 **A/B 前缀 = 方向通道组而非空间端口组**：
  A 通道 = downstream（host 端 A_PER 收 → device 端 A_PET 发）；B 通道 = upstream（device 端 B_PER 收 →
  host 端 B_PET 发）。→ **host(J2) 端球 = A_PER + B_PET；device(MCIO) 端球 = A_PET + B_PER**。
  与冻结 C5 矩阵/L1 编码「A 带(A_PER+A_PET)→J2、B 带→MCIO」冲突（A_PET/B_PET 角色对调；照布 →
  芯片下行输出 A_PET 误接 host、上行输出 B_PET 误接 device → 链路环回失效）。
  **用户/架构裁决 = 对账修正：A_PET↔B_PET 换位**（J2↔A_PER+B_PET；MCIO↔A_PET+B_PER）。
- **裁决点2（footprint 放置帧）**：现存 DS320PR1601.kicad_mod（ballmap 原帧，354 球=ballmap x/y）直插
  不符冻结包络 x∈[82.35,105.25] y∈[49.2,58.2]；纯旋转不可达引擎转置帧（det+1 vs −1，Oracle 复核）。
  **用户/架构裁决 = 资产不改，按裁决语义放置**。**执行注记：裁决文字「rot-270/A1→西南」在 KiCad 的
  实际角度 = 90°**（KiCad 角度 90：A1→板 (82.75,57.64) = 西-南角；lanes0-7 全西半 bx<93.8 → A 组 In2
  东穿/直出西 与冻结几何一致。KiCad 角度 270 会把 lanes0-7 放东半、违反冻结穿越计划 → 不取）。
- C79/C83 去耦冲突 = 执行中发现，登记（见 §2 open gap B），未擅移冻结位。

## 1. 对账修正落地（L1/L2 frozen + C5 矩阵，unlock→edit→lock）

- **L1_TOPOLOGY_v2.0.md**：§信号流向 按 TI 通道语义重写（DN=A 通道 J2→A_PER→A_PET→MCIO；UP=B 通道
  MCIO→B_PER→B_PET→J2）+ §穿越 成员修正（J2 侧网 = A_PER+B_PET 16 对 In2 东穿；MCIO 侧网 =
  A_PET+B_PER 直出西）+ 版本追加「v2.0 对账修正补记」。
- **L2_STRUCTURE_v2.0.md**：走廊分配表/In2 翼带/带结构/端区 stub 成员按修正语义更新（走廊表行按方向
  语义 DN/UP/DN_OUT/UP_OUT 表述即对）+ 版本追加补记。容量账中性（每侧 16 对/32 网、8 对/带×1.46、
  32 via/32 直出不变）→ **6L 判定流程终定不变，未触发 8L 重入条款**。
- **c5_chip_level_expect_matrix_v28.json**：新增 `_v30_scopeB_correction` 段（证据/语义/修正说明）+
  port_roles 重写（A: A_PER(host TX 入)+B_PET(host RX 出)；B: A_PET(device RX 出)+B_PER(device TX 入)）
  + check_items 扩为 7 条（4 带分列核对 + 方向 + REFCLK + 冲突停机条款）。
- 冻结纪律：freeze_ctl.sh unlock → edit → lock；备份 /tmp/opencode/*.bak_scopeB（不入库）。

## 2. 真板物理 ECO（k2/k2_v4.kicad_pcb，pcbnew 驱动，先备份后改）

- **备份**：`pm_gate/artifacts/k2_v4/L3/k2_v4.kicad_pcb.bak_scopeB_v29`
  （sha 6c387dff2d7ebdde97a753eb0a5294197785b3a0ad241152a5969a2f9bffdc24，= 原板 sha）。
- **删除 60 件（旧 DS160PR810 域）**：U3、U7 + AC 电容墙 C17-C32（DN 输出 AC，桥 _U3↔_MCIO）+
  C49-C64（UP 输出 AC，桥 _U7↔_J2）+ VREG 去耦 C65-C72 + 旧 strap 电阻 R4-R7/R9-R12/R17-R20/R22-R27。
  保留：C74-C84（ECN-004 DS320 VCC 去耦 + P3V3 bulk）、R31-R34（I2C 上拉）、R1/R3/R21/R28/R29（MCU
  域）等。
- **插入 U6 = DS320PR1601**（ForgeOS.pretty 库资产，354 smd pads）@ (93.8,53.7)，KiCad **rot 90**
  （= 裁决「A1→西南」语义；A1 板位 (82.75,57.64)）。
- **网表接线（修正后 C5 矩阵逐球）**：64 信号球 = A_PER lane L P/N→PCIE_DN{L}_{P,N}；B_PET→
  PCIE_UP_OUT{L}_{P,N}_J2；A_PET→PCIE_DN_OUT{L}_{P,N}_MCIO；B_PER→PCIE_UP{L}_{P,N}。
  VCC1-4 30 球→P3V3；GND 152→GND。（lanes8-15 64 球 + 侧带 17 + RSVD 15 + N/C 12 未接 = 108）
- **板框**：Edge.Cuts y 33→79（46mm），x 23/143 不变。
- **叠层**：8L→6L（SetCopperLayerCount(6)，文件 (layers) 块 In5/In6 定义随保存移除）。
- **C5 芯片级实测核对（eco_c5_verify.py）**：**130 断言 0 失败 PASS**——64 球网名逐球精确 +
  J2/J3/J4 端共享网核对（含 lane<4→J3、lane≥4→J4 分界）+ REFCLK 断言（REFCLK0: J2↔J3、REFCLK1:
  J2↔J4 直通，U6 无 REFCLK 球）+ 旧 *_U3/_U7 网零残留 + 板 reload 验证（6L、42 fp、bbox
  y[32.95,79.05]）。
- 记录：`eco_scopeB_physical_record.json`（操作/验证/open_gaps 全量，入库）。

## 3. G5 收尾自检

- **消费资产**：m13_v29 handoff（§0 范围/§5 commit/§7 环境）；c5_chip_level_expect_matrix_v28.json
  （修正后作 ECO 网表接线基准）；ds320pr1601_ballmap.json（逐球信号）；ForgeOS.pretty/DS320PR1601
  .kicad_mod（插装）；L1/L2 v2.0 frozen（包络/穿越约束）；TI SNLS683/SNLA425/SNLU300 主源（裁决证据，
  /tmp/opencode 下载）；Oracle 复核（fp 帧数学）；EXECUTION_PROCESS/GATES（冻结纪律 G0-G5）。
- **未消费/缺口（open gaps，如实登记）**：
  A. **DS320PR1601 侧带 17 球未接线**（SDA/SCL/A_ADDR0/1_7-0+_15-8/B_ADDR0/1_7-0+_15-8/PD_3-0,7-4,11-8,
     15-12/READ_EN_#/MODE/ALL_DONE_#）——冻结资产（k2_sch.yaml strap_intents 等）无 DS320 侧带设计
     意图（全为 DS160PR810 时代）→ 需 sch 层设计裁决后才能接续；禁运行时伪造。
  B. **C79/C83 去耦冲突**：ECN-004 预置 redriver VCC 去耦位 (91,57)/(91,58) 落入 DS320 rot-90 球域
     （6 处 pad 净空违规，worst C83-BM2 中心距 0.12mm < 0.55 需求）→ 需 L3 PDN 去耦重排（冻结位，
     不擅移）。
  C. **SPEC bga_escape.per_ball port_to_corridor {A:east,B:west}** = 带前缀键，无法表达修正后逐带映射
     （A_PER/B_PET→east、A_PET/B_PER→west）→ L3 前引擎 desc ECN 候选。
  D. **sch 侧**（k2_sch.yaml + kicad_sch sheets）仍 U3/U7 DS160PR810——DS320 符号集成 + 网表对齐待
     侧带设计（gap A）后执行。
  E. **L3 施工验证**（SPEC layer_plan 6L 化再生 + 引擎链 escape_connect_gen 布线 + DRC 归零 + QA 门禁 +
     S 状态机 srun/sadvance）未启动——前置 = A/B/C 缺口闭合；体量超本 session 可靠边界，禁暴力迭代，
     不假闭合。
- **停止/熔断**：无 G4 触发。一次 pcbnew 脚本崩溃（FootprintLoad 插件句柄丢失）= 单次技术故障，拆
  两阶段干净进程解决，非盲试。裁决门证据收集阶段图像不可读（模型无视觉）→ 改纯文本主源 + 数值几何
  证书定案。
- **禁违反项**：✅ 冻结区写全走 unlock→edit→lock（L1/L2 对账修正 + 真板 ECO 用户授权 + 备份）；未
  chmod 自解；未伪造 DS320 侧带设计（登记 gap）；未擅移 C79/C83（登记）；未暴力迭代；未触发 8L 重入；
  ECO 前后 sha 记录齐全。⚠ 执行注记：裁决文字「rot-270」与 KiCad 实际角度 90 的约定差已在本文件 §0
  与 eco record 中显式登记（语义一致：A1→西南 + A 组西半球东穿）。

## 4. commit 预备

- `_shared`（容器根 ic_hw_eda）：**本 session 无内容改动**（kb 未更新；仅 freeze lock 的 chmod 模式噪音，
  不入库）→ 无 commit。
- `k2`：L1/L2 frozen（对账补记）+ c5_chip_level_expect_matrix_v28.json（_v30 修正）+ k2_v4.kicad_pcb
  （真板物理 ECO，已锁）+ L3/k2_v4.kicad_pcb.bak_scopeB_v29（备份）+ eco_scopeB_physical_record.json +
  本文件 + 遗留 m13_v29_session_handoff.md §7 未入库补记（28 行，v29 遗留，随本批补入）→ commit →
  容器 bump gitlink。
- 容器根：bump k2。冻结区 git 前 unlock、后 lock（0/0/0）。

## 5. 边界声明

6L = **判定流程终定**（不变，未触发 8L 重入条款）。scope-B 已落地 = 真板物理 ECO（U3/U7 域 → 单
DS320PR1601 @93.8,53.7 rot90）+ C5 芯片级实测 PASS + A/B 端口对账修正（L1/L2/C5 文档同批）。
未闭合 = L3 施工全链（gap A-E），如实登记，下 session 承接：先闭 gap A（侧带设计）/B（去耦重排）/C
（port_to_corridor ECN）→ SPEC layer_plan 6L 化 → 引擎链布线 → DRC 归零 → QA → S 状态机。
