# M14 架构转向 + ① alloc 出厂解析预检 设计

> 状态：M14 v46 会话。承接 m13_v45_session_handoff.md。本文件 = 用户批准的架构转向记录 + 步骤①设计。
> 路线（用户 2026-09-08 拍板）：**求解层解析构造（无搜索）；缺形态=停机上报；形态补全=LLM+案例库+开源 SAMPLE 直接构造，验证后入库；施工端退化为纯执行（读施工图落板，零几何决策）**。
> 建筑业类比：可行性=结构图；实施层=施工图+工程计划（本层缺位 = 反复现场摸的总根因）；现场只分工执行，不画图不排计划。

---

## 0. 一句话现状

alloc（channel_alloc）D2 段廊道窗口验证**只覆盖走廊 x_range 内**（K2 数据带走廊 In2.Cu，EAST_CHIP_TO_J2 x∈[105.25,132.65]）；DN0-3 撞电容墙 C79-C83、DN5 col-top via 撞 C82、REFCLK1 被 UP7 through-via 挤出——**全部发生在走廊 x_range 之外的逃逸区**（pad 列 x84.85-91.15 → 走廊入口 105.25），D2 结构性不可见 → 行位缺陷流到施工端，施工端被迫现场补形态（v43-v45 反复摸的总根因）。

---

## 1. 架构转向（取代 v46 旧计划的"补丁施工"定位）

| 项 | 旧路线（废弃） | 新路线（批准） |
|---|---|---|
| 缺形态时 | 施工端现场发明（探针+消融，v43-45 模式） | **停机上报**，LLM 形态层补形态→验证→入库 |
| 求解方式 | 形态库枚举 + 现场搜索 | **解析构造**（公式一步算，天然终止） |
| 行位冲突 | 施工端替 alloc 还债 | **alloc 出厂解析预检**（上游消化） |
| 施工端职责 | 现场定形态/定序/画路径 | 读施工图纯执行，零决策 |

C-1/C-3（kb 模板 784034b）从"待落码补丁"改定位为：**形态库已入库的形态条目**（含行位可行性判据），供 alloc 预检 + 施工图构造消费。DN5/REFCLK1 的行位根因按新路线在 ① 解决，不靠施工端形态硬解。

---

## 2. 步骤①：alloc 出厂解析预检 — 设计

### 2.1 问题域（实测证据，勿重推）

K2 v4（U6 rot90，真板 sha f6273de6）：
- 数据带走廊载体 **In2.Cu**；EAST_CHIP_TO_J2 x_range [105.25,132.65]、WEST_MCIO_TO_CHIP [65.05,82.35]；dn/up 轨行 58.3…66.7 / 40.3…48.7（各 8 轨）。
- REFCLK 带 **In6.Cu**，轨行 45.7/50.5，P/N 行 50.31/50.69，x 跨 60-133 全域。
- U6 东侧去耦电容墙 C79-C83（F.Cu 0402/0603，P3V3/GND，x90.45-91.55 / y58.75-64.25）。
- 三类施工端爆出的行位缺陷（均走廊 x_range 外）：
  1. **DN0-3**（轨行 58.3/59.5/60.7/61.9）：F.Cu 尾段 x91→105 横穿 C79-C83 必拒（fcu_tail_seg，dist -0.07~0.24）。已解 DN4/6/7 仅因轨行落电容间隙/上方（运气非设计）。
  2. **DN5**（轨行 64.3）：pad 列 col-top via（x90.85/91.15）与 C82 净空 0.24 < 0.475（via 中心到 pad 边 annulus 要求）→ **该轨行对任何形态都不可行**（via₁ 在所有载体轮共享）；行位须 ≥64.54 或列东移。
  3. **REFCLK1**（In6 轨行 50.5，P/N 行 50.31/50.69）：被数据 lane UP7 chip 列 col-top through-via (93.25,50.73) 挤出：|50.73−50.69|=0.04 < via_keepout(~0.37)+track_half。through via 打穿所有层；REFCLK 行 x 域与数据 lane 逃逸列 x 域重叠 → **跨带 via 包络协调**，D2 单层走廊语义无此维度。

### 2.2 缺口根因

`channel_alloc._candidate_window_validation` → `segment_corridor.corridor_window_ok` 只验证走廊窗口
（段 x 投影 = SPEC corridor x_range，内滑语义镜像 solve）。**逃逸区（endpoint pad 列 bbox → corridor x_lo）不在任何上游模型的验证范围**；且走廊 In2 化后，D2 用的场只含走廊 band 层（K2: In2/In6），**F.Cu 障碍（电容墙/焊盘列/top via 邻 pad）数据未注入**。

### 2.3 设计目标

alloc 候选行位出厂时，除 D2 走廊窗外，再做**逃逸包络解析核验**——保证该行位存在至少一个**行位级可施工证明**（不依赖具体施工形态的逐点路径）。不达标 → 确定性跳过该轨行（下一候选），全败 → INFEASIBLE 附逃逸包络证据。**冲突在 alloc 阶段解析排除，不流到施工端。**

### 2.4 三层检查（E1-E3，全部数据驱动，零单板特判）

对候选 (net, band, track_y)，行位级可施工证明 = E1 ∧ E2 ∧ E3：

- **E1 走廊窗口**（既有 D2，保留）：走廊 x_range 内轨行可内滑净空。零改动。
- **E2 逃逸尾段载体可行性**（新）：对 net 全端点列区（数据源：板 pad 按网聚类，经 endpoint provider 注入），在**逃逸 x 段** [endpoint 列区外侧界, corridor x_lo] 内，轨行 ty±half_pitch 双轨在该带走廊载体层（In2）净空可达（corridor_window_ok 同语义扩展 x_lo→列区）。语义 = 至少存在一种**形态库尾段载体轮**的构造前提成立（载体层行位净空）。
- **E3 逃逸 via 包络核验**（新，含跨带协调）：
  - (a) **同带 top via annulus**：轨行 P/N 经 pad 列区（net 端点 pad 列 bbox + 形态 jog 域）落 via 时，via annulus 对 F.Cu 障碍（电容墙 P3V3/GND pad、邻 pad）净空 ≥ rules 要求。DN5@64.3 在此必拒（对 C82 0.24<0.475）。
  - (b) **跨带 through-via 包络**：net 端点在 x 域与**其他 alloc 声明带**（异层，REFCLK In6 等，含行位已知）重叠时，该列区可能落 via 的 y 包络须避让异带行位：
    `|via_y_env − band_row| ≥ via_keepout + track_half`。alloc 定序时把**已分带行位**纳入后续候选的 E3 检查（数据驱动：全部带行位 + keepout 常量来自 rules/config，零板坐标）。

### 2.5 输入与接口（加性，缺省降级不破坏既有）

```
alloc_channels_from_input(..., escape_check: Optional[dict] = None)
escape_check = {
  "endpoint_pads": callable(net) -> [pad 列区 {x0,x1,y0,y1,层}...]   # 板 pad 按网
  "morphology_rows": callable(band, track_y) -> 形态库行位可行性判据（载体轮/禁列）
  "via_keepout": float    # rules/config 注入（through via 对轨行包络）
}
```
- fields（static_sources）须扩展**逃逸层**（F.Cu + col_stack_escape_layer(配置) + 走廊带层全集）——`_alloc_static_sources` 现仅走廊 band 层，须加逃逸层（改 solve_pipeline provider，F.Cu 必含；电容墙 pad 为 P3V3/GND 非 hs 网，不被 clear_hs_pads 豁免，天然在障）。
- 缺 endpoint_pads / 场层缺失 → E2/E3 该检查项降级为 pass 并记 evidence（fail-open 只限"数据未注入"，**数据注入后检查本身 fail-closed**）；缺 morphology_rows → E2 退化为走廊载体层净空直判。
- 每候选附证据 `escape_validation: [{check, ok, evidence}]`；全败 → INFEASIBLE reason="escape_validation" + 逐项 blocked_by（与 D2 track_validation 同格式纪律）。

### 2.6 期望效果（K2 验收口径）

- DN0-3@58.3-61.9：E3(a) 仍会拒（via₁ 在墙列）？→ 否：DN0-3 死因是 F.Cu 尾段穿墙（E2 round-1），形态库两轮载体使 In2 尾段可行 → E2 pass、E3(a) 的 via₁ 位于 pad 列 x≤91.15 且 C79-C83 x≥90.45 有 y 交叠 → via₁ 是否撞墙取决列 x 与墙 x 域。**逐行位由解析判据定，不以旧探针结论替代**（v45 P4：归因一律以真 shared 重验为准）。
- DN5@64.3：E3(a) 必拒（C82 annulus）→ alloc 确定性跳 64.3 → 该行释放/次优轨行；无可用 → INFEASIBLE 附证据（真实缺口，交上层行序裁决，不再流施工端）。
- REFCLK1@50.5：E3(b) 使 UP 列区 via 包络与 REFCLK 行 50.31/50.69 冲突的行位在 alloc 阶段被解析处理（行位错位或带序协调）→ e2e 无挤出回归。

### 2.7 范围边界（勿扩）

- 本步骤只做 **alloc 行位出厂核验**，不改 SPEC/不改行序策略/不动 corridor 冻结物；alloc 若因 E3 拒分 → 证据级 INFEASIBLE 回报，行序修正是 alloc 上层（链序/带序策略）另一工作，不在此混入。
- C-1/C-3 形态实现（kb 模板）属施工图构造层（②），不在本步骤落码；本步骤仅消费其"行位级可行性判据"（morphology_rows 注入）。
- 零单板特判：K2 坐标/网名一律经 SPEC/config/rules/板数据注入。

### 2.8 实施勘误（v47 实证，E3 依赖 ② 形态谓词）

E3(a)/(b) 的"逐侧 col-top via 存在性"判定**依赖形态归属**（该 net 该侧用 col_stack 还是
landing/direct——pads provider 返回全链段 pad（含 J2/MCIO 连接器侧），全局 ∃ 判据会因连接器
侧 pad 必合法而退化假过，且芯片侧判别（竖排 dy≥0.45 触发）是 col_stack 形态的内禀属性）。
按新路线：**E3 全量判据 = 形态注册表的行位可行性谓词（② 首片：编码 C-1 载体两轮 + C-3
跨带包络的逐侧适用判据），不在 alloc 层内造半个注册表**。因此：
- E2（逃逸载体行位净空，与形态无关的走廊外可达性）= alloc 层稳健可落地；K2 激活
  = config half_pitch(0.19) 同时开启 D2（E1）+E2。
- E3(a)/E3(b) 代码框架已入 ENG（0b056e8），**默认休眠**（keepout=0/无 e3 激活键）；
  全量激活条件 = ② 形态谓词注册后按侧注入（工程 commit 待 e2e 绿）。
- 序列修正：①（E2+D2 激活）→ ②首片（形态注册表 + C-1/C-3 谓词）→ ①E3+K2 e2e 一并验证。

---

## 3. 测试计划（实现后）

1. 单测（channel_alloc/segment_corridor 同集）：E2/E3 判据纯函数用例——构造含"电容墙式 F.Cu pad 列"与"异层轨行带"的合成 SPEC（零 K2 依赖），断言 DN5 式行位被 E3(a) 拒、跨带 via 包络被 E3(b) 拒、可逃逸行位通过。
2. 回归：既有 alloc 单测全绿（D2 语义零改动）；test_solve_pipeline 1 failed pre-existing 勿修。
3. K2 e2e（一次性验证）：alloc 重跑 → 观察 DN0-3/DN5/REFCLK1 行位处置 + solve 段结果净增；≤2 次纪律。
4. 合规：ECN-009 流程（unlock→备份→改→单测→e2e→lock 0/0/0→commit+push）。

---

## 4. 待决 Gate（实现前需裁决）

- alloc 属冻结区 + 上层裁决（v45 纪律"勿动 alloc，行序另卡"）→ 本设计作为 ECN 立项申请，需 PM 批准后方可 unlock 实现。
- F.Cu 场注入到 alloc static_sources 会改变 D2 现有场内容（加层）→ 需回归确认 D2 行为字节不变（加层只增查用层，不改既有层判定）。
