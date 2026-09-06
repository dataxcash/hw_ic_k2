# L2 冻结：结构方案 V2 — 6 层 × 单芯片走廊（ECN v20→v21）

> 状态：**已冻结（2026-09-05，ECN v21，用户授权；2026-09-06 v26 评审降级补记）**。
> 为 L3 施工图的约束包络，超脱并替代 `L2_STRUCTURE_v1.0.md`（8 层/电容墙/WQFN 方案，作废，git 存档）。
> 变更依据：L1_TOPOLOGY_v2.0（单 DS320PR1601/46mm/6L 试用/单面）+ v20 叠层重估。
> **层数 = 6L 判定流程终定（per-ball 容量/净空/首发判定，2026-09-05 per-ball 逃逸引擎验证；
> 2026-09-06 非执行者双路对抗评审 = PASS_WITH_CONDITIONS；v28 ECO 范围 A C1-C5 闭合升格）**
> ——v25 取得真实 354 球坐标，v26 用模型层新增 per-ball 逃逸引擎（⑦）逐球判定 FEASIBLE；
> v26 对抗评审确认容量账稳健不翻转（PASS_WITH_CONDITIONS），C1-C5 已闭合（C1 via 兜底 ✅/
> C2 引擎口径 ✅/C3 SPEC 再生+⑦ evaluated ✅/C4 文档 ✅/C5 连接器级实测 + 芯片级期望一致 ✅，
> v28 ECO 范围 A）；判定链可下传 L3（详见"层数定案闸"）。
> **范围 A 诚实边界**：真板物理 ECO（sch/PCB 换 DS320PR1601）+ L3 施工 = scope-B；C5 芯片级
> 实测核对随 scope-B 按期望矩阵一次执行（当前 = per_ball 注入与期望矩阵机器一致，同源
> 354 ballmap）。
> v21 初始"6L 闭合"判定曾被非执行者对抗评审 FAIL（见 v21_realroute/REVIEW_ADVERSARIAL_v21.md）；
> v26 的引擎级判定为工具级 per-ball 验证后结论，非评审 FAIL 前状态复辟，但同样不豁免条件闭合。
> 与 L2_STRUCTURE_v1.0 冲突以本文件为准。

## 叠层分配（冻结）

| 层 | 分配 | 依据 |
|---|---|---|
| F.Cu | PCIe 差分微带（参考 In1 GND）+ 芯片逃逸 + 外围低速 | L1 v2.0 硬约束；微带参考 In1 |
| In1.Cu | **GND 完整平面** | F.Cu 微带参考面 |
| In2.Cu | **唯一内部信号层（带状线）**：PCIe 穿越翼带 + 局部短潜 stub + REFCLK 分带 + 低速 | 6L 下 In2 上下皆 GND（带状线，双 GND 参考） |
| In3.Cu | GND 完整平面 | 走廊/平面完整 |
| In4.Cu | 电源分区 3.3V（VCC1-4）/ GND | 芯片单 3.3V |
| B.Cu | 空置（单面贴）；允许边带作 L3 选项 | L1 v2.0 |

> **6L vs 8L 层语义**：8L 增 In6（第二内部信号层 + 额外 GND）。v26 per-ball 引擎判定
> 6L 的 In2 已满足穿越 + REFCLK + stub 承载力（引擎级 FEASIBLE，容量账 64≤69 兜底）；
> 8L（In6）仅作回退候选，重入触发条件见本文件「8L 重入 ECN 触发条款」。

## 阻抗参数（冻结，过渡基准）

- 主选：w=0.205/g=0.175 → 85.1Ω（PCIe85，JLC SI9000 重算，强条）。
- **L3 前置强制**：JLC SI9000 重算终值（H1=5.0mil/Er1=4.3）冻结后才定 L3 线宽。
- 对内等长 <0.15mm；对间间距 = **1.46mm 对中心距**（已裁决 v22：0.585 铜跨 + 0.875 铜边净空，
  见 L1 v2.0 硬约束 2）——本冻结结构用 1.46 保守轨距，比旧 8 对/8.0mm 更紧，两口径结论一致。

## 走廊分配（冻结）

**每侧 16 对 / 32 网（东 J2 16 对；西 MCIO 16 对 = J3 8 + J4 8）+ REFCLK0/1（不经芯片）。**

| 走廊 | x 净跨 | F.Cu 数据带 | In2 翼带（穿越） | REFCLK |
|---|---|---|---|---|
| 西（MCIO↔芯片） | 17.30mm（65.05→82.35） | J3 北带 8 对 + J4 南带 8 对（各 8×1.46=11.68mm < N16.2/S20.8） | J3/J4 输入网 8 对/翼穿越 | REFCLK0/1 直通 |
| 东（芯片↔J2） | 27.40mm（105.25→132.65） | DN 进 8 对 + UP_OUT 出 8 对（两带各 8×1.46=11.68mm） | UP/DN 输入网 8 对/翼穿越 | — |

- **逃逸过渡**：F.Cu 焊盘→走廊带 45° dogbone；球下 via 至 In2。过渡 x 深度 ≈10–12mm < 西 17.3 / 东 27.4。
- **In2 翼带**：穿越 16 对（A 带西半球东穿）按 N/S 翼分工各 8 对，对中心距口径
  inter_pair_spacing 1.46 → 需 8×1.46=11.68mm < N 16.2 / S 18.8（20.8−2.0 REFCLK 预留，
  v26 评审 C2 口径修正后仍过）；REFCLK 在 S 翼与穿越同层分带（+2.0mm guard）。
- **端区 stub**：非穿越输出对（B_PET/B_PER 直出球若改判 via 的 In2 短潜）集中在端区
  （x<6mm），与中段翼带穿越不争带宽（C1-b 复核：改判 via 预算 40/64 ≤ 69 不翻，见
  mcio_feas_step2/c1_via_reclass_report.json）。

## 过孔策略（冻结）

- **受控过孔 ≤2/网**（F→In2→F 单次换层）；0.20/0.35 标准孔、孔环 ≥0.075、背钻消残桩；
  差分 via 成对对称、GND 伴行孔 ≥1（L2 v1.0 v1.2b 结转，PM 裁决 2026-08-16 取消"0 过孔"绝限）。
- 芯片逃逸：0.6 名义 pitch，NSMD Ø0.3 焊盘，**球下 0.3 开始 via、禁 via-in-pad**、每差分对轨距 ≥ 最紧口径。
- 高速换层保持阻抗连续（In2 双 GND 参考带状线）。

## 逃逸区（Intel retimer common footprint，本文件新件）

- **封装 = Intel PCIe5 retimer common footprint（354 球 8.9×22.8，非均匀分组/balls-anywhere
  逃逸优化阵列）**——lane 分组 + 组间 0.3/0.4/0.8/1.2mm 布线通道，目的 = 每差分对单层逃逸。
- **带结构**（v25 真实 ballmap 校准，column-based）：4 带沿**短轴**按 x_mm 排 ——
  A_PER(x≈−3.68)→B_PET(−1.78)→A_PET(+1.68)→B_PER(+3.68)，各带 32 球=16 对（8 lane × P/N）；
  带间通道中心距 1.9~3.5mm。K2 lanes 0-7 有效信号球 64 = **32 F.Cu 直出（B_PET/B_PER 西半）
  + 32 ball-via→In2（A_PER/A_PET 西半球东穿）**，穿越 16 对 = 100% A 带（非旧 25/75% 外环游标口径）。
- **逃逸精确逐球求解 = 引擎级已闭合（v25 坐标 + v26 per-ball 引擎，2026-09-05；C2 口径
  修订 2026-09-06 重跑 FEASIBLE 不变）**：v25 从 UltraLibrarian 取得
  `ds320pr1601_ballmap.json`（354 真实逐球 x/y mm,vendor-validated），v26 新增模型层
  per-ball 逃逸引擎（⑥⑦）逐球判定 FEASIBLE。**不再是 known_gap、不再"非工具精确解"**；
  逃逸验证（L3 开工前硬门）容量级已过闸（全程穿线 C1 以 VIA 兜底复核闭合，逐段可布性归 L3）。

## PDN（冻结）

- 单 3.3V（VCC1-4=30 球，内部 LDO）；去耦 0402/0603 就近 VCC 球；B.Cu 空置。
- 禁止电源网拉细线（checklist C.3 结转）。

## 层数定案闸（L3 开工前硬门，非运行时回退）——6L 判定流程终定（v28 ECO 范围 A 升格）

**层数（6L vs 8L）= 6L 判定流程终定（C1-C5 闭合，2026-09-06 v28 ECO 范围 A）**。
原定案闸：在取得 Intel footprint 物理坐标资产后，用引擎跑一次精确逃逸求解（禁暴力迭代）。
本 m14 v26 已执行该闸，经非执行者双路对抗评审 = PASS_WITH_CONDITIONS（v26 评审 §0）：
容量级判定稳健、不翻转；C1-C5 条件于 v27（C1/C2/C4）+ v28 ECO 范围 A（C3/C5）全部闭合
（C1 全程穿线/VIA 兜底复核已按路径 b 闭合：c1_via_reclass_report.json FEASIBLE_UNCHANGED
40/64≤69；C2 引擎口径修订已 ECN 完成；C3 SPEC 再生 = 生产 SPEC 本体描述层对齐
DS320PR1601 + ⑦ 生产 plan() evaluated FEASIBLE，not_configured 假静默消除；C4 文档修订
完成；C5 = 连接器级真板实测一致 + 芯片级 per_ball 注入与期望矩阵机器一致）：
mcio_feas 已 advance（planned→plan→review）。**判定链流程终定，可下传 L3（施工/真板物理
ECO = scope-B，C5 芯片级实测核对随 scope-B 执行）。**

- **闸前**：v25 取得 UltraLibrarian 真实 354 球坐标（vendor-validated）→ 原"物理球栅资产不可得"
  阻塞解除（v22/v23 缺口闭合）。
- **闸中**：模型层 Per-ball 逃逸引擎（路径 a ECN：`routing_topology_gate.py` ⑦
  `BGA_PER_BALL_ESCAPE` v1.4 + `escape_landing.py` `bga_per_ball_escape`）消费
  `ds320pr1601_ballmap.json` + U1@(93.8,53.7) 逐球判定一次对。
- **引擎判定（FEASIBLE）**：K2 8-of-16 lane 64 信号球 = 32 F.Cu 直出 + 32 ball-via→In2，
  穿越 16 对；每带 8 对 fan-out 1.2→1.46（11.68≤23.36），N/S 翼各 8 对按 ipair 口径
  11.68≤16.2/18.8（C2 修订后重跑仍过），via 净空全 354 球 worst 0.6≥0.427，deficits 0。
- **条件闭合状态**：C1（b 路径 VIA 兜底）✅ 2026-09-06 证书复核 40/64≤69；C2（引擎口径）✅
  2026-09-06 ECN 修订重跑 FEASIBLE 不变；C3（SPEC 再生⑦真执行）✅ 2026-09-06 v28 ECO
  生产 SPEC 本体描述层再生（DS320PR1601 + per_ball 注入）+ ⑦ evaluated FEASIBLE
  （not_configured 假静默消除）；C4（stale 清理/死指针/8L 重入条款）✅ 2026-09-06；
  C5（网表核对）✅ v28 ECO 范围 A = 连接器级真板实测一致（v27）+ 芯片级 per_ball 注入与
  期望矩阵机器一致（同源 354 ballmap；真板物理 ECO 后实测核对随 scope-B）。
  **6L 判定流程终定（v28 ECO 范围 A，用户授权）；mcio_feas 已 advance
  （planned→plan→review）。施工/真板物理 ECO = scope-B，届时按期望矩阵一次实测核对
  C5 芯片级，禁运行时改判。**

## 8L 重入 ECN 触发条款（宪法 Ch6#5 回退裁决性补全，v26 评审 §2-E）

8L（增 In6 层）候选在流程终定后仍保持"回退通道"（非禁用）。以下任一触发条件出现时，
须走变更单（ECN）回 L2/L1 重开层数裁决（禁止运行时 fallback / 私下妥协）：

1. **L3 逃逸逐段布线（dogbone router）实证**：B_PER row1 等直出球 F.Cu 全程穿线（C1 的
   a 路径验证）发现硬性不可路由，且 VIA 改判预算（最坏 64 ≤ 69）在施工细节下超支；
2. **In2 穿越 + stub 实测超载**：In2 翼带/端区 stub 在真实布线下容不下 16 对穿越 + 改判 stub；
3. **SI9000 重算轨距收紧溢出**：阻抗终值致 inter_pair_spacing 1.46 放不下 8 对/带。

触发即 ECN → 回 L2（叠层分配）或 L1（层数裁决）重开；重开须重新过对抗评审，
不得以本闸已过为由免审。未触发前 6L 保持流程终定状态。

## 硬约束（L3 必须满足）

1. 高速受控过孔 ≤2/网、F.Cu 主层、对称 + GND 伴行。
2. REFCLK 独立、包地 ≥2mm、不交叉。
3. 对间 / 轨距 = inter_pair_spacing = **1.46mm 对中心距**（已裁决 v22 用户 2026-09-05：R3-2「0.875」
   = 对间铜边净空 → 0.585+0.875=1.46；L3 跑引擎经 route_model_config.json
   `capacity_audit.inter_pair_spacing` 注入 1.46，勿用 drc_rules.json 0.875；冻结轨距 1.08 为实际排轨居中值）。
   不确定性已消除，禁再下传"待裁定"。
4. **逃逸验证 = L3 开工前硬门**（见"层数定案闸"）；未过闸不得定案层数、不得下传 6L 闭合。
5. 板边铜 ≥0.30mm；M3 孔 3.0mm keepout（结转）。
6. AC 集成于芯片内，无板上 AC 电容墙（cap_wall_ac 本板关闭）。

## 版本

- v1.0/v1.1/v1.2/v1.2b（2026-08-13~16，8L/电容墙/WQFN）——作废，git 存档。
- v2.0（2026-09-05 冻结，6L/单芯片 DS320PR1601）——本文件。
- v2.0 修订补记（2026-09-06，v26 对抗评审 C4 + 裁决点1 授权）：
  ① 层数表述由「已定案 6L」降级为「引擎级 FEASIBLE，待 C1-C3-C5 闭合后流程终定」；
  ② stale 文本清理（25/75% 游标口径 → 32/32 真实逃逸法、col-band 表按 v25 短轴 column-based
  修正、19mm → 18.8 REFCLK 预留口径、走廊/翼带口径统一 1.46=11.68）；
  ③ 死指针「§回退 8L」修复 → 新增「8L 重入 ECN 触发条款」；
  ④ C1-b 闭合记录引用（c1_via_reclass_report.json）。
- v2.0 升格补记（2026-09-06，v28 ECO 范围 A，用户授权）：C1-C5 条件闭合 → 层数表述
  「引擎级 FEASIBLE（待条件闭合）」升格为「6L 判定流程终定」；条件闭合状态表更新
  （C3/C5 ⏳ → ✅ 范围 A）；mcio_feas advance（planned→plan→review）。范围 A 边界：
  真板物理 ECO + L3 施工 = scope-B，C5 芯片级实测核对随 scope-B 按期望矩阵一次执行。
