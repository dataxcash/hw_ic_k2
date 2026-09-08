# NEW SESSION PROMPT — v52（粘贴即用，勿加戏；全前台，禁 task()/oracle/后台）

## 任务
承接 v51（m13_v51_session_handoff.md，先读；再读 v50 handoff §1 拿 F1-F7 坐标）：
DN out_MCIO 剩段净增。v51 已实证 ENG-α pad-row dip 与 ENG-β 归属门有效（DN6 全解
PAD_ROW_DIP 首hit、DN5 out_MCIO 门后 col_stack 解锁，段级 15→17）。**本卡单点收窄到
DN0/1/3 三段的 out_MCIO chip 侧**（与已解的 DN6 同属"芯片竖排型西行逃逸"，但 chip col
84.4-85.8 更西，col_stack/dip 全 None）——先差分取证定案，再选最小修复；禁预设根因
（v50 教训：预设归因会被实测推翻）。**全程前台**，禁 task()/禁 oracle/禁后台。

## 必读（只读最小集，其余一律不读）
1. `m13_v51_session_handoff.md`（同目录：F8-F12 钉死事实 + 下一卡方向，勿重推重探）。
2. `m13_v50_session_handoff.md` §1 表格（仅 F1-F7 坐标，37 行短文件，勿读 v43-v49）。
3. 代码定点符号（grep，勿整读）：
   - `_pad_row_dip_escape`（v51 新形态：门/枚举/错列规则）；
   - `_escape_pair` col_stack→dip 挂钩段 + VIA(Form A/C)→LSWAP→LSWAP_V→col_stack 的
     触发序（DN0-3 的 reason 显示 VIA 极性交叉 = VIA 形态拒 + col_stack/dip 全 None 的终态）；
   - `_col_stack_escape`；`_solve_pair_centerline_v4` 的 `_field()`(clear_hs_nets 语义) 与
     shared_segs/shared_vias 注入位；
   - `solve_chain_v4`/`solve_all_v4`（跨 base 共享只在 base 全 SOLVED 时前馈 —— DN7 input
     回退机制，勿在本卡动）。
4. e2e 报告**只读对比两段**（勿整读）：`p3_real_board_e2e_report.json` 中 DN0 vs DN6 的
   out_MCIO 结果段（reason/escape kind/路径）。字节保集合以 `git show HEAD:` 同文件为基准
   （28 段 P/N 段端，v51 F10）。

## 事实（v51 已钉死，勿重推勿重探；数字即证据）
- 已解 out_MCIO：DN5（chip 侧 COL_STACK——归属门移除错锚消费后自搜解锁）、DN6
  （chip 侧 **PAD_ROW_DIP**：chip pad 91.8/92.2 y52.37/51.67 → stub 西 0.6 → via@pad 行 →
  In2 pad 行横走 8.45mm → drop 列 82.75/82.35 错列 → ty 行 66.09/65.71）。
- 未解 DN0/1/3 out_MCIO chip 侧：VIA 自搜极性交叉 @(84.660,52.919)/(85.785,52.914)/
  (84.384,58.838)，且 **col_stack 与 dip 均返 None**（竖排型 84.6/85.0 y52.37/51.67，
  与 DN6 同构但 col 更西 ~7mm，drop 可用列区间 [corr_x=82.35 … via≤84.3] 仅 ~1-2mm 宽）。
- DN2/4/7 卡在 J3 **左逃逸**（VIA 交叉 @57.1/55.3、DN7 无净空）→ 连接器侧形态/alloc 重锚
  域，**本卡排除**（除非取证显示为简单左形态缺口且一行可证——否则记下一卡）。
- DN7 input 段回退 = J2 列 133.825 同列堆叠（DN6 全解共享），v51 已知开项，属 alloc 占用
  协调域，**本卡不修**；字节保集合排除 DN7 input 段。
- 保锚：REFCLK0/1 + UP0-3/6/7 out_J2 + DN0-4/6 input = 27 段 P/N 段端必须零变更。

## 施工（最小可证；kb 只在本卡定案形态落地后更新，勿先写）
1. **差分取证（第一步，前台 ENG 场 API）**：对 DN0 与 DN6 的 out_MCIO chip 侧（右逃逸，
   direction<0），分别取 col_stack 与 dip 的**逐候选首拒证据**（每候选：拒于哪个检查 =
   fcu stub seg / via point / esc pad 行横走 / drop 竖腿 / band 尾段 / pn_ok；最近障碍
   net/dist/req）。取证可用一次性诊断脚本调用现成模型实例 + 场 API（产物标注"非引擎结论，
   仅取证"），净空判断一律走 ENG seg_ok/point_ok。产出：DN0 vs DN6 差异表 → 定案根因属于：
   (a) drop 可用列区间 < P/N 错列最小需求（DN6 靠 8.45mm 横走才有空间，DN0 只有 ~1-2mm）；
   (b) 同 base 自身 input 段几何（异名网 PCIE_DN0_* vs PCIE_DN_OUT0_*_MCIO，clear_hs_nets
   不清对方）在 84.0-84.7 列占位；(c) 其它。
2. **最小修复（依定案选一，合成板单测先行，零真板依赖）**：
   R1 若 (a)：dip 加性扩展一档——stub 枚举 0.3/0.6/0.9/1.2/1.5 或 drop 列下限放宽/换载体层
     腿组合（In1 竖腿 + In2 carrier，镜像 col_stack 载体语义），先合成板证逻辑再真板；
   R2 若 (b)：`_solve_pair_centerline_v4` `_field` 段族清网——同 base 段级网族（base 前缀
     相同）互不清为障碍的共享注入修正（加性 dormant：默认行为不变，仅显式声明时生效），
     28 段保锚必须实测零变更；
   R3 若 (c)：停机 + handoff（G4 熔断，证据留档）。
   禁 alloc/channel_alloc/escape_landing 改动（B1/占用协调 = 后续卡）。
3. **单测**：既有 23 绿保（test_escape_envelope 11 + TestColStackTailCarrier 4 + v51 新 8）；
   R 落码 +1~3 合成用例（dip 扩展档 / 段族清网三态）。全量失败集 pre≡after（16 项环境/
   工具链 pre-existing 勿修勿动）。
4. **e2e 一次性（≤2）**：`python3 tools/p3_k2_real_board_e2e.py`（k2 仓库根，全前台）。
   验收 = 段级真解 ≥17 且 out_MCIO SOLVED ≥3（DN0/1/3 中至少 +1，期望 +2/+3）+
   27 段保锚零变更（git diff 脚本 segmap 比对 HEAD vs new）+
   零新增 REFCLK 冲突 + alloc/landing 无回归（34/34、FEASIBLE）。
   solved_pairs 3→4+ 为加分非硬指标（DN5/6 input 未全解挡 base）。
   净增 0 → 停机 handoff（不在本卡续形态）。

## 合规
unlock→改→单测→e2e→lock 0/0/0→commit（_shared ENG+kb 若变 + k2 报告/handoff）→push（两仓）
→写 m13_v52_session_handoff.md（G5 自检）。freeze_ctl.sh 在 k2/pm_gate（status 0/0/0 终态）。

## 勿做 / 勿加载（省 CONTEXT，逐条遵守）
- 勿读 v43-v49 任一 handoff/kb 全文、Oracle 长文、topview、设计文档、escape_learner/
  matcher/ls_route_model/channel_alloc/solve_pipeline/p3 e2e 驱动全文、git log、k2 其它
  artifacts、测试全量输出。
- 勿整读 hs_route_model.py/escape_landing.py（只 grep 定点 + 读函数窗口）；勿 init-deep /
  勿建 codegraph 索引（定点 grep 足够）。
- 勿跑全量 pytest（只跑上述 23 绿文件/类 + 新用例）。
- 勿 task()/oracle/后台/explore/librarian —— **全部前台**（bash/pytest/git 直跑）。
- 勿再 probe 重证 v50 F1-F7 / v51 F8-F12 数字；勿改 alloc/channel_alloc/escape_landing/
  SPEC/K2 板文件；勿 stage `_shared` 的 escape_closure_analysis.py / pipeline/hooks/* /
  .bak_v33_perball（freeze chmod mode 假 dirty + v49 前 untracked 残留，内容零变化，勿动）。
- 禁暴力迭代：形态参数调整 ≤2 次带依据；缺形态 = 停机 + kb 模板 + 下轮按模板施工。
- 勿往 ENG 加 K2 坐标/网名特判（段族清网若做，必须 base 前缀通用推导，零单板字面量）。
