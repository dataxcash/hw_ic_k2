# NEW SESSION PROMPT — v51（粘贴即用，勿加戏）

## 任务
承接 v50 归因定案（m13_v50_session_handoff.md，先读它，本文为其施工版）：DN out_MCIO ×7
(DN0-4/6/7 out_MCIO；input 已 SOLVED) 从 INFEASIBLE 解出。v50 已推翻 v49「单一 landing→corridor
形态缺」归因 → 实为 **B1 alloc 锚错端点 + B2 alloc 缺 stub 可达门 + A 消费侧锁死** 三层，且芯片侧
需**新逃逸形态**。v51 = 最小可证两件套落码 + 单测 + e2e≤2 实测净增。禁 task()/禁 oracle/禁后台，
**全部前台**。产出物 = ENG 能力（形态谓词 + kb 模板），K2 仅输入/验证消费。

## 必读（只读最小集，其余一律不读）
1. `m13_v50_session_handoff.md`（同目录：F1-F7 钉死事实 + 根因定案 + 字节锚清单，勿重推重探）。
2. 代码定点符号（grep，勿整读）：
   - `_solve_pair_centerline_v4` L3368-3377（landing_pair 只传 idx1/右逃逸 —— A 缺陷位）；
   - `_escape_pair` L1293-1315（chip_landing→landing_pair 消费分支，L1305 有效记录即 fail-closed）；
   - `_landing_escape` L1620-1627（`_stub`：pad→(via.x,pad.y)→via，横走@pad 行 —— 无竖爬变体）；
   - `_col_stack_escape` L1553-1568 触发与调用位（新形态挂其 None 之后、direction<0）；
   - `escape_landing.allocate` `_verify`（B2 缺陷位：无 F.Cu stub seg_ok 门）。
3. e2e 报告只读已解字节锚对照（report solved 段，见 handoff F7；勿整读）。

## 事实（v50 已钉死，勿重推勿重探；数字即证据，勿再 probe 重证）
- out_MCIO 端点：ep[0]=J3 pad P(64.3,45.75)/N(63.7,45.75) 西；ep[1]=U6 chip pad
  P(84.6,52.366)/N(85.0,51.673) 东。corridor WEST_MCIO_TO_CHIP x[65.05,82.35] In2 track 58.7
  (P/N 58.89/58.51)。落点表记录 pad 锚=芯片 pad、via 在 x66.555（18mm 不可达，stub 被 GND 0.05 挡；
  In2 走廊自落点全净空 → C 排除）。
- 反证 F5：剥落点后芯片侧 col_stack 两 flip None → 芯片侧需新形态，消费门不足以单独解锁。
- 可行几何 F6：(a) 芯片侧 pad-row dip：pad→F.Cu stub 西 0.3-0.6→via@pad 行(84.3/84.0 或
  84.7/84.4/84.1)→In2 沿 pad 行西行→corridor 东界 82.35 下钻→轨行：净空已证；
  (b) 连接器侧 V-jog：J3 pad→pad 列竖爬 46.5-49→横走至(66.555,jog)→via→In2 上行：净空已证
  （45.75 本行横走被挡，须先竖爬；且 In2 只走 H-V，V-H@66.555 会撞同列已解 via）。

## 施工（最小可证两件套；kb 先行 → ENG 落码 → 单测 → e2e≤2）
1. **kb 模板**入库：`landing_pair_geometric` 域新模板（category connector_escape）记录两形态
   structure/defect/fix/构造前提 + validation + provenance v51（同 col_stack_obstacle_stub_gap 的
   sqlite PUT 流程）。
2. **ENG-α 芯片侧 pad-row dip 形态**（加性，dormant）：挂 `_col_stack_escape` 返 None 之后、
   仅 `direction<0` 且 pad 东于 corr_x 时尝试（防东向 col_stack 字节漂移）；枚举 stub 0.3/0.6/0.9 →
   via@pad 行 → In2 西行 → corr_x(82.35 侧) 下钻至 ty；逐段 seg_ok + _pn_ok(≥0.155)；垂直方向
   sign(track_y−pad_y)（覆盖 DN7 北行）；flip 仅换 ty_P/ty_N。候选序确定性 first-clear。
3. **ENG-β 消费侧归属门**：消费 landing_pair 前校验 (a) 记录 pad ≈ 本逃逸 ep pad(ε 0.02，
   同 _chip_pair_for) 且 (b) F.Cu pad→via stub 可达（H 或 V-jog seg_ok）；任一失败 → **落回自搜**
   （不改记录、不 fail-closed 死锁）。`landing_pair` 传参改侧自适应（谁 pad 归属谁接）。**字节锚**
   F7 必须逐字节不变（J2/东走廊记录 pad=idx1 恒过门 → 行为不变）。
4. **单测**（合成板，零真板依赖）：新形态合成用例 + 消费门三态（过/归属失败回自搜/stub 不可达
   回自搜）+ 既有 15 绿保（test_escape_envelope 11 + TestColStackTailCarrier 4）。
5. **e2e 一次性（≤2）**：目标 **solved_pairs 净增**（期望部分/全 7，DN7 北行+同列堆叠为风险，勿预设
   全通）+ REFCLK0/1 全保 + UP out_J2 保 + input col_stack 字节保 + 零新增 REFCLK 冲突
   （v48 UP input 假象不得复活）。净增<7 → 记入 handoff 作下一卡（alloc 重锚 B1/V-jog stub 消费），
   **不在本卡暴力迭代**。
6. 合规：unlock→改→单测→e2e→lock 0/0/0→commit（_shared ENG+kb + k2 报告/handoff）→push（两仓）→
   写 m13_v51_session_handoff.md（含 G5 自检）。

## 勿做 / 勿加载（省 CONTEXT）
- 勿读 v43-v50 任一 handoff/kb 全文、设计文档除 §2.8 纪律、Oracle 长文、topview；勿整读引擎。
- 勿重跑 alloc / 勿重做 v50 已证归因 / 勿再 probe 重证 F1-F7 数字；净空证据一律走 ENG 场 API。
- 勿现场硬解形态（禁暴力迭代，同参≤2 带依据）；缺形态 = 停机 + kb 模板 + 下轮按模板施工。
- 勿往 alloc/channel_alloc 加构造逻辑（§2.8）；勿往 ENG 加 K2 坐标/网名特判；勿 commit 非绿态；
  e2e 只跑 p3 卡（≤2）。
