# NEW SESSION PROMPT — v49（粘贴即用，勿加戏）

## 任务
承接 M14 K2。目标：把 e2e 实证的 col 构造 P/N 相向交叉（v48 N4）归因 → 落成 ②施工图层构造谓词 → e2e 净增验证。**全前台推进，禁 task() 委派、禁后台长跑、禁暴力迭代（同参≤2 带依据）、禁 chmod、禁临时脚本消融归因（P4）**。

## 必读（只读这 3 件，其余一律不读）
1. `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v48_session_handoff.md`（最新状态/事实 N1-N5/主线/勿做）
2. `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m14_alloc_escape_precheck_design.md` 的 §0+§2.8（E3 归②纪律）
3. e2e 报告（唯一数据源，勿重跑 alloc）：`k2/pm_gate/artifacts/k2_v4/L3/p3_real_board_e2e/p3_real_board_e2e_report.json` 的 `solve_base_reasons`（交叉坐标已落盘，直接定点）

## 事实（已钉死，勿重推勿重探）
- 真板芯片=U6（x84-92 PCIE pad 全属 U6）；电容墙 C79-C83；当前 SPEC 走廊载体 In2（EAST_CHIP_TO_J2 x[105.25,132.65] / WEST_MCIO_TO_CHIP x[65.05,82.35]），REFCLK In6 行 45.7/50.5。
- K2 config 已激活（channel_alloc half_pitch 0.19 + escape_check：chip_refs=["U6"]/band_spans refclk[60,133]/keepout 0.37/pair_half 0.19）。alloc 34/34 无回归，E2/E3 全过。
- solve 基线 solved_pairs=2；16 bases INFEASIBLE 主因 = **col 构造 P/N 相向交叉**：DN0-3 input @(x95.1-97.7, 58.3-64.3 轨行)、DN5 @(97.748,64.299)、DN* out_MCIO @(55-60, 各轨行)、UP0-7 out_J2 @(85-92,55.7) 等（坐标以 report 为准）。
- **v44 的"F.Cu 尾段穿电容墙"口径已作废**（In2 载体绕开墙，N5）——归因一律以 v48 e2e 交叉坐标为准。
- ENG `_shared` HEAD `97ce81c`；单测：test_escape_envelope.py 11 用例全绿基线；freeze 当前 0/0/0（改动前 unlock、后 lock，git 前 unlock）。

## 动作序列
1. 读必读 3 件 → 用 report 的 cross_evidence.point 定点 2-3 段（DN5 input / DN0 input / UP5 out_J2）判交叉发生在 col In1 竖腿段、In2 尾段、还是出口排序(flip)（solve reason 已带 flip 与坐标，勿整读引擎，只 grep 定点符号：`_col_stack_escape` / `_escape_pair` / cross_evidence / `_pn_ok`）。
2. 落 ②构造谓词：修 col-stack P/N 交叉（若判为出口排序/列差/极性 flip 构造缺陷 → 构造层解析修复；若属形态缺 → 停机上报 + kb 新模板，勿现场试）。
3. 单测（含新交叉回归用例）→ e2e 一次性（≤2 次）→ 目标 solved_pairs 净增 + REFCLK0/1 全保。
4. 合规：lock 0/0/0 → commit（_shared ENG 改动 + k2 报告/handoff）→ push（两仓）。写 m13_v49_session_handoff.md（含 G5 自检：消费资产/未消费/熔断）。

## 勿做 / 勿加载（省 CONTEXT）
- 勿读 v43-v47 任一 handoff 全文、kb 模板全文、v44 失败矩阵（口径已废）；勿读历史源码大段（只 grep 定点符号）。
- 勿重跑 alloc/勿重做已证归因/勿跑 p3 e2e 之外的全量（≤2 次纪律）。
- 勿往 alloc 加构造逻辑（§2.8：构造谓词归②，alloc 行位层已证无责）。
- 勿改 SPEC/corridor 冻结物；勿 commit 非绿态。
