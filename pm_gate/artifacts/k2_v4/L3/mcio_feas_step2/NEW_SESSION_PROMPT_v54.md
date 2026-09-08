# NEW SESSION PROMPT — v54 Phase 2（粘贴即用，勿加戏；全程前台，禁 task()/禁 oracle/禁后台/禁委派）

## 任务
承接 v53（先读 m13_v53_session_handoff.md F20-F27，勿重推重探；再读 m13_v53_p01_spec.md
全文，它是 Phase 2 唯一权威规格，**所有架构裁决已定，禁止再做架构决策**）：
实现 `_shared/eda_core/escape_allocator.py`（out_MCIO Local EscapeAllocator：MRV + L1/L2
两级净空 + ColumnBook 写 + EscapeTable 产出行），合成板单测先行，K2 e2e 验收 ≤2。
**禁实现 Phase 3 fallback 关闭；禁改 alloc/landing/P1 三模块；禁做 DN0/1/3 必解承诺**
（NO_ESCAPE 带 reason/evidence = 合法输出）。**全前台零委派**。

## 必读（只读最小集，其余一律不读）
1. `m13_v53_session_handoff.md`（F20-F27，钉死勿重推）。
2. `m13_v53_p01_spec.md`（§0-§7 = Phase 2 规格全量，照抄执行）。
3. P1 已落码模块（**import 复用，勿重读勿重写**）：`_shared/eda_core/column_book.py`、
   `escape_table.py`（enum/reason/evidence 全在此）、`construction_fact.py`。
4. 代码定点符号（grep，勿整读）：
   - `build_hs_field`（hs_route_model.py L200，逐层场构建语义）；
   - `_escape_pair`/`_col_stack_escape`/`_pad_row_dip_escape`（v51 引擎签名为 L2 候选构造参照；
     escape_allocator 是方案层新模块，不调用施工形态函数，只消费 build_hs_field 场 API）；
   - `spec_to_route_input`/`SolvePipeline.run_alloc/run_landing`（e2e 驱动 tools/p3_k2_real_board_e2e.py
     的输入组装，照抄其 5 段装配即可复用 alloc/landing）。
5. 验收基线数字：m13_v53_p0_audit.json（alloc checksum `fab63768…`、landing `4f9f24db…`）、
   m13_v53_p1_audit.json（16 pinned 反演行、DN5/6 traceable）。

## 事实（v53 已钉死，勿重推勿重探；数字即证据）
- 16 SOLVED = 14 保锚 + DN5/6 out_MCIO，全 pinned；chip 侧判定 EAST_CHIP_*→left /
  WEST_MCIO_TO_CHIP→right；REFCLK0 input = DIRECT 直连无 via1。
- fallback gap：dip pn 331740 rej / col_stack 42360 rej —— Phase 2 目标是让 DN0/1/3 这些
  枚举在方案层消化或明确 NO_ESCAPE，P3 才关施工路径。
- ColumnBook 簿语义：0.01 lattice / reservation=±0.36 闭区间（整数索引含端点，0.37 才出界）
  / 差分对原子 / via 独立维度 / ball 非 owner。单测已锁（26 绿）。
- MRV tie-break 元组 = `(len(cands)↑, chip_pad_x_P↑, base 数字↑, segment 秩↑)`，秩
  [input, out_MCIO, out_J2]。

## 施工（最小可证，合成板先行，零真板依赖）
1. `freeze_ctl.sh unlock`（k2/pm_gate）→ 写 `_shared/eda_core/escape_allocator.py`
   （按 spec §2 结构；禁 set 迭代；候选列表排序；dict 插入序；禁 K2 坐标/网名字面量）。
2. 合成单测 `tests/test_escape_allocator.py`（spec §5 六组用例，零 K2 依赖）：
   pytest 三组 26 绿保 + 新组全绿（全量失败集 pre≡after）。
3. K2 真实板 gate `tools/p3_v53_phase2_gate.py`（spec §6 验收，前台一次性 ≤2）；
   产出 `m13_v53_p2_audit.json`。
4. **单测先行**：L2 场 API 判据先在合成板证逻辑，再跑真板；净空一律走 build_hs_field。
5. 失败语义按 spec §4 enum；evidence 必带 nearest_obstacle。

## 合规
unlock→改→单测→e2e≤2→lock 0/0/0→commit（_shared escape_allocator+test；k2 gate+audit+
handoff）→push（双仓）→写 m13_v54_session_handoff.md（G5 自检）。

## 勿做 / 勿加载（省 CONTEXT，逐条遵守）
- 勿读 v43-v52 任一 handoff/architecture_target/irg_readiness 全文（v53 handoff+spec 已含裁决）；
  勿读 topview/设计文档/kb 案例库/Oracle 长文。
- 勿整读 hs_route_model.py/escape_landing.py/channel_alloc.py/solve_pipeline.py/P1 三模块
  （只 grep 定点 + 读函数窗口；P1 模块 import 复用）。
- 勿 init-deep/勿建 codegraph 索引；勿跑全量 pytest（只跑 26+新组指定文件）。
- 勿 task()/oracle/后台/explore/librarian —— **全部前台**（bash/pytest/git 直跑）。
- 勿改 alloc/channel_alloc/escape_landing/ModelConfig/hs_route_model/P1 三模块/SPEC/K2 板文件；
  勿 stage `_shared` 的 4 个 mode-only M 与 `.bak_v33_perball`（v49 前残留，勿动）。
- 禁暴力迭代：L2 场参数调整 ≤2 次带依据；缺净空 = 按 NO_ESCAPE 语义落 evidence，不硬闯。
- 勿往 ENG 加 K2 坐标/网名特判（全部经 SPEC/config/真板注入）。
