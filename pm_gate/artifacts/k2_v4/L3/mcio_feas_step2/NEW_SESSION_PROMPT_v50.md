# NEW SESSION PROMPT — v50（粘贴即用，勿加戏）

## 任务
承接 M14 K2 v50：把 v49 缺口三连中**最高杠杆单一形态** = DN out_MCIO ×7（DN0-7 MCIO 侧；
DN0-4/6/7 的 input 已 SOLVED，只差此段 → 全通 ≈ +7 solved_pairs）的「落点驱动逃逸无净空」做
**ENG 形态补全**。产出物 = EDA TOPO ENG 能力（解析构造谓词 + kb 模板入库），K2 仅是验证项目：
任何解必须是 ENG（hs_route_model/escape_landing/solve_pipeline + kb）的结果——**禁临时脚本、
禁 K2 特判、禁现场枚举试**。全前台推进，禁 task() 委派、禁后台长跑、禁暴力迭代（同参≤2 带依据）。

## 必读（只读最小集，其余一律不读）
1. `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v49_session_handoff.md`（状态/缺口三连/勿做；
   v49 教训：勿手推几何、勿整读引擎大段）。
2. e2e 报告（唯一数据源，勿重跑 alloc）：`.../p3_real_board_e2e/p3_real_board_e2e_report.json`
   的 `stages.solve.results`（段级 fail_forms）+ `stages.landing`（落点表）+ `solve_base_reasons`
   ——已落盘证据，定点读不整读。
3. kb 模板 3 件（只读 structure/validation 段，sqlite 定点查询，勿读全文）：
   `col_stack_obstacle_stub_gap`（缺口清单/候选形态方向）、`chip_col_stack_band_tail_carrier`
   （C-1 limitation）、`refclk_band_data_via_coordination`（REFCLK 硬约束，勿违背）、
   `conn_escape_mcio`（MCIO 侧历史形态参照）。
4. m14 设计文档 §2.8（纪律：构造谓词归②/alloc 勿加）——只需纪律，勿重读全文。

## 事实（已钉死，勿重推勿重探）
- ENG `_shared` HEAD `48fa14f`（97ce81c + b860740 = ②C-1 尾段载体两轮 + C-3 跨带 via 包络）；
  单测 15 绿（test_escape_envelope 11 + TestColStackTailCarrier 4）；freeze 0/0/0 lock。
- e2e（v49 引擎，input fp 5113681d…）：solved_pairs=2（REFCLK0/1）；**段级 SOLVED 15/34** =
  DN0-4/6/7.input + REFCLK0/1.input + UP0-3/6/7.out_J2，**全部 REFCLK In6 行合规（真解）**。
- 剩余 19 段 INFEASIBLE = 缺口三连（v49 归因定案，勿重做）：
  N1 **DN out_MCIO ×7**：全报「落点驱动逃逸无净空（落点 P=(66.555,52.366) N=(66.555,51.673)，
  sx 66.555→64.3）」同模 → **单一 landing→corridor 衔接形态缺口，v50 主目标**。DN5.input 另因
  C82 col-top 死局（勿与 out 混为一谈）。
  N2 UP.input ×8：REFCLK 合规硬缺口（v48 的 SOLVED = via₁ 撞 REFCLK1 行 50.69 @0.04mm 场盲区
  假象，C-3 已按物理正确清除；**勿追求恢复非法 SOLVED**）。
  N3 UP4/UP5.out_J2：VIA 族出口排序交叉残余 + UP4 被贪婪序占用挤出（solve 序/占用协调 = 另卡）。
- alloc 34/34 E2/E3 无回归；config 已激活（half_pitch 0.19 + escape_check keepout 0.37 /
  chip_refs U6 / band_spans refclk[60,133]）。

## 动作序列（全前台；ENG 形态补全循环：归因→缺形态即停机→LLM 构造入库→ENG 落码→验证）
1. **归因定点（只读 ≤1 轮）**：取报告 `stages.landing` 中 DN0 out_MCIO 落点记录（net/method/
   landing x,y/polarity）+ 该段 fail_forms；grep 定点符号（`_landing_escape` / `_LANDING_IN2_SHAPES`
   / `_escape_pair` / `_in2` / `landing_pair`）判「落点→走廊 In2 衔接」净空缺失段：同 x P/N 竖段
   重叠需错列？shape（H-V/V-H/DIAG）直连无绕行域？corridor 西界外 In2 西段障碍？净空证据一律走
   **ENG 现成 API**（`model.probe_path_clearance` / `_probe_fields`），禁手推、禁临时脚本。
2. **缺形态即停机 → 形态补全（不现场试）**：缺口 = landing→corridor 衔接形态缺 → **LLM 从 kb
   案例库（conn_escape_mcio 等）+ 开源 SAMPLE + 几何逻辑直接构造**新形态（参考向：P/N 落点错列/
   In1 腿列差语义复用/落点 x 域收进 corridor/西段绕障）；先落 **kb 模板**（structure=形态几何+
   defect+fix+构造前提，validation，provenance=v50）→ 再 **ENG 落码**为加性构造谓词（dormant
   安全，缺省零行为变化，K2 由 config 激活）。
3. 单测：新形态合成板回归用例（零真板依赖）→ 全绿。
4. e2e 一次性（≤2 次）：目标 **solved_pairs 净增（DN out_MCIO 通 → ≈+7）** + REFCLK0/1 全保 +
   段级零新增 REFCLK 冲突（N2 假象不得复活）。
5. 合规：lock 0/0/0 → commit（_shared ENG + kb + k2 报告/handoff）→ push（两仓）→
   写 m13_v50_session_handoff.md（含 G5 自检：消费资产/未消费/熔断）。

## 勿做 / 勿加载（省 CONTEXT）
- 勿读 v43-v49 任一 handoff/kb 模板全文、设计文档除 §2.8；勿整读引擎（只 grep 定点符号）；
  勿在对话里反复手工几何推演（几何验证用 ENG probe API / 单测）。
- 勿重跑 alloc / 勿重做 v49 已证归因；勿跑 p3 e2e 之外全量（≤2 次纪律）。
- 勿现场硬解形态（禁暴力迭代）；缺形态 = 停机 + kb 模板入库 + 下轮按模板施工。
- 勿追求恢复 v48 的 UP input 非法 SOLVED（撞 REFCLK 0.04 = 场盲区假象，保持 C-3 正确拒绝）。
- 勿往 alloc 加构造逻辑（§2.8）；勿往 ENG 加 K2 坐标/网名特判（K2 只做输入与验证消费）；
  勿 commit 非绿态；产出物一律为 ENG 能力（形态 = ENG 谓词 + kb 模板；证据 = report/probe 等
  ENG 输出），禁临时脚本消融归因（P4）。
