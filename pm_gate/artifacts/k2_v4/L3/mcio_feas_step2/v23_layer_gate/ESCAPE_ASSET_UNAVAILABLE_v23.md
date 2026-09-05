# M14 层数定案（6L vs 8L）— Step-0 门禁 STOP：机器球栅资产仍不可得 → 层数维持 INDETERMINATE

> 状态：**G2 门禁 STOP（资产不可得，未宣布任何闭合）**。本 session 为层数定案（6L vs 8L）执行轮，
> 前提 = 取得 DS320PR1601 机器球栅（x,y）mm 资产。**实检工作区：该资产仍不存在，且本环境
> （无 FAE 通道 / 无 CAD 登录态）无法于会话内取得。** 依任务 Step 0 硬性处置：
> 禁再盲找 / 禁自建（宪法第八章第 8 条 + v21 对抗评审"假成功"签名：置信度提升≠验证能力提升）→
> **直接 STOP，写本报告，层数维持 INDETERMINATE（6L 试用 + 8L 兜底）**。
> **未跑 escape_landing（无物理 x/y 输入），未动 L1/L2 frozen，未回写 kb produced=true，未宣布"6L 闭合"。**

## 0. 本 session 动作与结论（一句话）

对工作区做**机器球栅物理资产**全量实检（glob/find/grep/git-log 交叉），确认**唯一资产形态 = 逻辑球名集
（列字母 + 行号），无任何物理 (x,y) mm 逐球坐标**。决定性逃逸项（75% via / 50% 穿越密度）**仍无法由引擎
工具精确验证** → **层数维持 INDETERMINATE**。本 session 不产闭合，只落"资产不可得"报告 + v23 handoff。

## 1. Step-0 门禁实检记录（资产全量排查，禁凭印象）

| # | 排查对象 | 实测结果 | 判定 |
|---|---|---|---|
| 1 | `ds320pr1601_ballmap_354name.json`（v22 工件） | 354 球**名集**（col+row，n=354）；`extraction_verdict` 明文"exact per-ball mm X/Y NOT machine-extractable — label positions are tabular(readability), not physical" | ❌ 逻辑名集，非物理 |
| 2 | `ds320pr1601_ballmap_signal_balls.json`（v21 工件） | 128 信号球，字段 = name/row/col/side/kind/pol/lane（row=M,col=26 等**逻辑标签**） | ❌ 逻辑标签，无 (x,y) |
| 3 | `zdg_geom_raw.json` / `spec_6L_corridor_audit_input_ns.json` | zdg_geom_raw 为**图像像素坐标**（如 229.7px,163.0px）；轴 scale 比 ≈7.0（列轴/行轴），非物理可读网格，不可校准为 mm（v22 已证） | ❌ 像素/非物理 |
| 4 | 全容器 `*.xlsx` | 仅 layout 需求说明 / datasheet checklist / scheme 文档；**无 Astera `PTx16xx_supplemental_info.xlsx`** | ❌ 无 vendor-declared 机器资产 |
| 5 | 全容器 `*.kicad_mod` / `*.kicad_sym` | 仅 Arduino template；**无任何 retimer/354-ball footprint**（grep.app 类检索 v22 已 0 命中，不重跑） | ❌ 无 footprint |
| 6 | git log | 链条止于 v22（b9205c3）；**无任何"取得物理资产"commit** | ❌ 无新资产入库 |

> **结论：机器球栅物理 (x,y) mm 资产不存在。** 与 v22 ESCAPE_GAP §6 穷举终判一致——唯一机器级资产 =
> Astera `PTx16xx_supplemental_info.xlsx`（vendor-declared 逐 pad 坐标，**FAE-gated**；ampheo 镜像/asteralabs
> wp-content/GitHub 全 404），其余（KiCad/grep.app/GitHub、SnapEDA/UL/SamacSys、Intel raster figure、
> TI ZDG0354A 非物理可读网格）全部**不含机器可读逐球 X/Y**。

## 2. 决定性逃逸项状态（诚实定位，与 v22 一致，未变）

| 层级 | 状态 |
|---|---|
| 封装设计级 | ✓（Intel PCIe5 retimer common footprint，每差分对单层逃逸；lane 分组 + 组间通道） |
| 结构级 | ✓（25% 外环 F.Cu 直出 / 75% 需 via / 50% = 16 对 32 网穿越；列位驱动，确定性确认） |
| **工具精确解** | ✗（决定性项：缺物理逐球 X/Y → `escape_landing.analyze_pad_heap` 无法输入） |
| **层数（6L vs 8L）** | **INDETERMINATE**（6L 试用 / 8L 兜底；逃逸验证 = L3 开工前硬门） |

## 3. 为什么本环境不能推进（禁动作对照）

1. **禁再盲找**：v22 §6 已穷举 5 类来源 + 加分项得"无公开机器资产"终判；本 session 重跑检索 =
   空间浪费 + 违反任务显式"禁再盲找"。唯一可得渠道 = **外部人工输入**（超出会话边界）。
2. **禁自建/禁视神投影**：用 Intel Fig3-5 / TI ZDG0354A raster **vision 投影**造"派生球栅 JSON"喂引擎，
   即 v21 对抗评审点名的"**结论跑赢证据 / 置信度提升≠验证能力提升**"假成功复刻。**坚决不做。**
3. **禁暴力迭代**：层数定案须"一次对"；无资产前提下任何一次求解都是参数猜测 = 违第八章第 8 条。
4. **禁改引擎（edacore）+ 禁自写独立求解器**：逃逸验证必须走 `escape_landing`（只读调用）；缺输入时
   既不改引擎也不自写替代物。引擎契约（`analyze_pad_heap` 按 `p["x"]/p["y"]/p["w"]/p["h"]`(mm) 聚列/行/行距，
   行 154-167）已实读确认 = **必须物理坐标**，逻辑名集不可喂（喂了即非物理、非验证）。

## 4. 下一步唯一路径（外部输入，属人类/渠道动作）

1. 经 **Astera FAE** 索 `PTx16xx_supplemental_info.xlsx`（vendor-declared 逐 pad 坐标，同 footprint，最高可信）。
2. 或取得**登录态 CAD**（Ultra Librarian / SnapEDA / Intel PCIe5 retimer spec registration）导出机器球栅。
→ 资产到位 → 落 `ds320pr1601_ballmap`（354 or 128）球栅 JSON（(x,y)mm；交叉验证 = ①354 count 对齐
ZDG0354A 名集 ②列带结构 A_PER@row1-2/B_PET@row7-10/A_PET@row26-29/B_PER@row34-35 ③0.6 pitch/8.9×22.8
尺寸闭合。任一失败 → 禁下传）→ `escape_landing` 一次精确求解（禁暴力迭代）→ 过闸冻 6L / 不过回 8L（不重跑）。

## 5. G2/G4 触发记录（写入 handoff G5）

- **G2 触发**：决定性逃逸项（逐球精确形态）**未覆盖**（引擎接口有无形、资产缺）→ 上报缺口（本报告）。
- **G4 未触发（本 session 无几何卡点空转）**：未做任何几何求解迭代（无资产即无求解输入，故无"连续 2 轮
  同卡点"情形）；资产排查为一次性确定动作，非迭代试错。
- **无暴力迭代、无假成功、无违规**：未运行求解器、未宣布闭合、未动冻结区、未 chmod 自解、未改引擎。

## 6. 关联

- 上游：m13_v22_session_handoff.md（全部状态）、ESCAPE_GAP_v22.md（决定性缺口 + §6 资产可得性终判）、
  CORRIDOR_CLOSURE_v22.md（走廊闭合=工具背书 ✓，决定性项只剩逃逸）。
- 冻结约束包络：L1_TOPOLOGY_v2.0（层数未定案，6L 试用 + 8L 兜底）、L2_STRUCTURE_v2.0（"层数定案闸"：
  取得物理坐标后跑引擎精确求解判定，禁把 6L 闭合下传 L3）。
- 铁律源：LAYOUT_CONSTITUTION 第八章（禁暴力迭代 #8 / 禁脚本做设计决策 #2 / 禁跳层 #3）、
  REVIEW_ADVERSARIAL_v21（假成功签名：置信度提升≠验证能力提升）。
