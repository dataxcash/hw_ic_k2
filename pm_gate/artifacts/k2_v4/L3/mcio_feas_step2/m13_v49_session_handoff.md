# M14 v49 承接 — ② col-stack 构造谓词首片（C-1 载体两轮 + C-3 跨带包络）落地；K2 e2e 零净增 → 残余=stub 形态缺 → 停机上报

> 承接 v48。任务：把 v48 N4 的 col 构造 P/N 相向交叉归因落成 ②施工图层构造谓词 → e2e 净增验证。
> 结论：谓词首片已落码+单测绿；K2 e2e **solved_pairs 仍 = 2（净指标未增，REFCLK0/1 全保）**；
> **段级真相（v49 修正）**：真解段 4→15（DN0-4/6/7 input + UP0-3/6/7 out_J2 + REFCLK×2，全部 REFCLK 行合规）；
> v48 的 UP input SOLVED = 撞 REFCLK In6 行 0.04mm 的场层隔离盲区假象 → C-3 清除（物理正确化，非回归）；
> 唯一真回退 = UP4 out_J2（v48 合法解 → v49 INFEASIBLE，贪婪序共享占位，新缺口）；
> 归因定案 = col-stack **stub/via₁ 障碍域形态缺** + UP 芯片西列 REFCLK 合规硬缺口 + 段级占用协调缺 → 停机上报，kb 已更新。

---

## 0. 一句话状态

ENG `_shared` HEAD `97ce81c` + 4 文件改动（hs_route_model / route_input / solve_pipeline / 2 测试文件，v49 待 commit）；
kb.sqlite3 +1 模板（col_stack_obstacle_stub_gap）；k2 报告 = v49 引擎证据（solved 2 / alloc 34 / 16 lane INFEASIBLE）；
单测 test_escape_envelope 11 + test_hs_route_model TestColStackTailCarrier 4 = 15 绿；test_solve_pipeline 1 failed = pre-existing（97ce81c 复验）。

## 1. 钉死事实（v49 增量；勿重推）

| # | 事实 | 依据 |
|---|---|---|
| N1 | 16 lane 全 INFEASIBLE reason = 「via 换层 P/N 极性不一致（flip … 逃逸出口排序与轨道分配相向交叉 -0.2050 < 0.175 @ 轨行/逃逸区）」——引擎自带分类即 **出口排序(flip) 层**；交叉点 x95-98（DN input）、x85-92/y55.7（旧 UP out_J2） | e2e solve_base_reasons + fail_forms 双 flip |
| N2 | 交叉段定位：-0.2050 = width 0.205 全叠（中心距 0）；DN5 flip_T @(97.748,64.299)=轨行中心（尾/出口区）、flip_F @(98.502,61.022)；**非** col 竖腿区（col_stack stub/腿 x≤pad+1.65≤92.8，够不到 x97+）→ 交叉来自 VIA 对称族（Form A/C）强制出口端点与展开侧序矛盾 | report fail_forms + 引擎符号定点（_escape_pair/_pn_ok/_sym_via 1101-1106 方向一致性注释同源 -0.205） |
| N3 | col_stack（竖排对角对 dx0.3/dy0.52 触发）在 v48 引擎返回 None（无任何 field 检查通过的候选）——真阻塞在 stub/via₁ **路径域**：alloc E3(a) 判"存在合法 via 点"（点可入）≠ col_stack 需 pad→stub→via₁ 连续净空（路径不可入，U6 pad 墙+邻族+去耦墙簇） | v49 合成单测证 C-1/C-3 逻辑自洽但 e2e 零净增；k2 e2e 对照 |
| N4 | ②首片（C-1 尾段载体两轮 F.Cu→In2 + C-3 跨带 via 包络 keepout 注入）落地后 e2e：**逐 net 状态全同（无净增无回归）**，失败段左右侧归属/交叉点重分布（旧 UP out_J2 左逃逸交叉 → 现 input 右逃逸 无净空/新交叉点）——谓词使 col-stack 前进到不同失败点，仍未到 SOLVED | 97ce81c 纯净复跑（k2 HEAD 报告逐字节一致）vs v49 引擎报告 diff |
| N5 | 参考：97ce81c 纯净复跑报告与 k2 已 commit 报告逐字节一致 → v48 报告未陈旧、引擎确定性保持 | sha1 对照 + git diff 空 |

## 2. 停机上报（形态缺，v49 纪律勿现场试）

- **判据**：col-stack 残余阻塞 = stub/via₁ 构造域（N3），属**形态缺**而非出口排序/列差/极性 flip 构造缺陷（N2 已证 flip 交叉为 VIA 族表层，col-stack 是正确形态但路径域不满足）。新增谓词（C-1/C-3）为**必要非充分**（N4）。
- **处置**：kb 新模板 `col_stack_obstacle_stub_gap`（category bga_fanout）落库，记录 gap/形态候选方向：① pad 列障碍簇内可布 stub/via 形态；② per-ball 落点驱动（chip_landing VIA_IN2 球旁 via）；③ alloc 行序让行 ty≥64.54 / 列东移（DN5 C82 死局同源，v44 chip_col_stack limitation）。
- **e2e 预算**：run#1 = v49 引擎（零净增）；run#2 = 97ce81c 纯净对照（确定性验证）。未试任何暴力变体（同参 ≤2 带依据纪律）。

## 3. 交付资产

| 项 | 状态 |
|---|---|
| ENG `_shared`（97ce81c 之上） | hs_route_model._col_stack_escape：C-1 尾段载体两轮（tail_rounds: F.Cu→carrier In2，F.Cu 通过即原路径返回=已解 lane 字节不变）+ C-3 跨带 via 包络守卫（via₁/via₂，dormant: keepout≤0 恒过）；route_input.ModelConfig + escape_env_* 4 字段；solve_pipeline.run_solve 从 channel_alloc.escape_check 注入（keepout 0.37/half_track/pair_half/band_spans refclk[60,133]） |
| 单测 | test_hs_route_model TestColStackTailCarrier 4 绿（F.Cu 挡→In2 载体解 / F.Cu 通→F.Cu 轮保 / C-3 拒 via₂ / dormant 零 keepout 恒过）；test_escape_envelope 11 绿（含 v48 遗留未提交 2 用例本轮一并提交） |
| kb | `col_stack_obstacle_stub_gap` 模板已入库（_shared/knowledge/kb.sqlite3，PUT 2026-09-08） |
| k2 报告 | p3_real_board_e2e_report.json（v49 引擎证据：solve_base_reasons + fail_forms 双 flip + escape_gap；solved_pairs=2） |

**G5 自检**：
- 消费资产：3 必读（v48 handoff/m14 §0+§2.8/e2e 报告）+ e2e 定点 + kb 模板（chip_col_stack/refclk）+ 引擎定点符号（_escape_pair/_col_stack_escape/_sym_via/_pn_ok/cross_evidence/E3(b) 同源）。
- 未消费（守纪律）：v43-v47 handoff 全文 ✗、kb 模板全文（仅读取相关 limitation）✗、v44 失败矩阵口径（N5 作废）✗、整读引擎大段 ✗（只 grep 定点）、临时脚本消融归因 ✗（归因靠 e2e fail_forms + 合成单测）。
- 熔断：run#1 零净增即转「形态缺→停机上报」分支（勿现场试），run#2 仅作 97ce81c 对照（确定性/报告未陈旧），未试第 3 个引擎变体。

**勿做**：勿按 v44 F.Cu 尾段口径推断当前失败（In2 载体 + 本批谓词后尾段/跨带已闭环）；勿往 alloc 加构造逻辑（§2.8）；勿在形态缺未补前暴力改 col-stack stub 域（须先 kb 新模板→新卡）；勿 commit 非绿态。
