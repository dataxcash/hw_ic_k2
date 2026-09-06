# M14 v29 — 层数定案流程终定执行：路径 b（范围 A 流程贯通验证）C3/C5 闭合 + 状态机 advance

> 状态：**本 session = 用户授权路径 b（范围 A：流程贯通验证）**。用户裁决（2026-09-06）：
> 「修改 REDRIVER 已讨论确定，授权把需要修改的地方都修改了，尽快验证工具的功能流程能力」
> → 范围 A（真板物理 ECO/L3 施工 = scope-B，用户确认）。
> 本 session 结果：**C3 ✅ C5（范围 A）✅ → 6L 判定流程终定升格（L1/L2）+ mcio_feas
> advance（planned→plan→review）+ kb v6 终态 + 生产 SPEC 本体再生（sha 8732cb75）**。
> 全链 = 模型/状态机/门禁工具驱动（生产 routing_topology_gate v1.4 + task_gate + kb），
> 零新求解器、零引擎改动、零暴力迭代。

## 0. 裁决与授权（用户/架构）

- **裁决点1（路径）**：v28 判 c（ECO 未落地维持缺口）；用户随后授权 **路径 b + 范围 A**
  ——"修改 REDRIVER 已讨论确定，授权修改，尽快验证工具的功能流程能力"；范围 A =
  描述层 ECO（SPEC 再生/模型/状态机/门禁链贯通），真板物理 ECO + L3 施工 = scope-B。
- **范围 A 诚实边界（贯穿全部产物）**：C5 芯片级 = per_ball 注入与期望矩阵机器一致
  （同源 354 ballmap），非物理 ECO 网表实测；scope-B 按矩阵一次实测核对。

## 1. C3 闭合（生产 SPEC 本体再生 + ⑦ evaluated，模型驱动）

- **备份**：`SPEC_k2_v4.json.bak_v28_eco`（sha 7eaad223）。
- **再生（sha 8732cb75）**：redriver U3/U7→DS320PR1601 主条目 + `bga_escape.per_ball`
  注入（354 ballmap 契约 1:1 v27 POC）+ **U3/U7 降级 legacy_alloc_holder**（alloc 段名
  `out_U3/out_U7` + u3_side_bridges 折线映射所需；强删曾致 ESCAPE_SLOT UNKNOWN
  INFEASIBLE——模型诚实输出，legacy 占位恢复后消解）+ stackup 8L→6L + board 46mm +
  capacitor_walls 移除 + 顶层 `_v28_eco` 注记（scope/legacy_note）。
- **生产模型验证**：`plan()` v1.4 → **verdict FEASIBLE_WITH_MORPH_GAP**（与 v27 基线
  同 verdict，无回归；PN polarity 混合 = 既有形态缺口，评审已接受）+ **⑦ evaluated →
  DS320PR1601 FEASIBLE（64/32/32/16/deficits 0）** → not_configured 假静默消除。
- 记录：C3_SPEC_REGEN_v27.md §5（v28 执行补记）；可复跑资产 reproduce_c3_spec_regen_draft.py。

## 2. C5 闭合（范围 A：连接器级实测 + 芯片级期望矩阵一致）

- 连接器级：v27 BoardParser 真板实测（J3=0-3/J4=4-7，板文件无 git diff → 仍有效）。
- 芯片级（范围 A）：per_ball 注入 vs `c5_chip_level_expect_matrix_v28.json` **机器比对
  C5_SCOPE_A_MATCH**（64 球全名/signal 逐球一致 + selected_lanes 0-7 + A=east=host +
  无 REFCLK 球）。scope-B：真板物理 ECO 后按矩阵 5 条 check_items 一次实测核对。
- 记录：C5_NETLIST_CHECK_v27.md §4（v28 执行补记）。

## 3. 流程终定链（状态机/门禁/文档/kb，工具驱动）

| 项 | 动作 | 结果 |
|---|---|---|
| SPEC 再生 | 生产本体描述层对齐 | sha 8732cb75（.bak_v28_eco 备份）|
| 模型 plan() | 生产 RoutingTopologyGate v1.4 | FEASIBLE_WITH_MORPH_GAP + ⑦ evaluated FEASIBLE |
| C5 核对 | 期望矩阵机器比对 | C5_SCOPE_A_MATCH |
| **mcio_feas advance** | pm_gate task_gate（容器根权威 _shared，cwd=k2 项目根）| **planned → plan → review**（iterations=1，plan_hash 0ba97e2d，review_gate 过 = plan 工件齐 + 43 falsifications 全 rebutted/resolved 无 open）|
| tasks.json 登记修正 | stale 工件路径（2026-08 早期规划，从未建）→ 真实产物（mcio_feas_step2 链）| plan_artifacts=3 / outputs=3（.bak_v28 备份）|
| L1 frozen 升格 | 层数表述「引擎级 FEASIBLE 待条件闭合」→「6L 判定流程终定」+ 范围 A 边界注记 | L1_TOPOLOGY_v2.0.md（unlock→改→lock）|
| L2 frozen 升格 | 同 + 层数定案闸条件闭合状态表（C3/C5 ⏳→✅）+ 8L 条款措辞 | L2_STRUCTURE_v2.0.md（unlock→改→lock）|
| **kb 终态** | knowledge_base.put-template（唯一入口）| corridor_pair_ds320pr1601_dual_band **v5→v6**：layer_count「6L 判定流程终定」+ known_gaps 6 项（C1/C3/C5 闭合记录 + 去耦 + scope-B×2）|

## 4. G5 收尾自检

- **消费资产**：m13_v28 handoff（缺口登记）；c5_chip_level_expect_matrix_v28.json +
  spec_regen_diff_checklist_v28.json（v28 对齐准备直接复用）；生产 RoutingTopologyGate
  v1.4 + escape_landing（⑦ 判定唯一来源）；ds320pr1601_ballmap.json（354 球）；
  SPEC_k2_v4_c3poc.json（注入契约）；pm_gate task_gate/state（容器根权威，cwd=k2 项目根
  解析——首次发现 CLI 须在项目根跑，容器根 cwd 会回退老目录误读）；kb v5→v6（put-template
  唯一入口）；EXECUTION_GATES G0-G5；LAYOUT_CONSTITUTION（冻结纪律/ECN）。
- **未消费/缺口**：scope-B 全部（真板物理 ECO/符号封装资产/U3-U7 全移除/alloc 重解/
  layer_plan 施工段 6L 化/C5 芯片级实测）——登记 kb known_gaps 2 项 + 本文件 §0 边界，
  非本 session 范围（用户范围 A 裁决）。
- **停止/熔断**：G4 未触发。一次模型诚实输出（强删 U3/U7 → ESCAPE_SLOT UNKNOWN
  INFEASIBLE）即时识别为 alloc 段名断裂 → 恢复 legacy 占位，非盲试（单次修正，无重试循环）。
- **禁违反项**：✅ 未翻 8L；未假闭合（C5 范围 A 边界如实标注，scope-B 显式登记）；引擎
  零改动（零 ECN，全走既有模型/状态机/kb 工具）；生产 SPEC 改动前备份；L1/L2/kb 走
  unlock→改/put→lock（freeze_ctl）；task advance 走 task_gate 机械 gate（非手改状态文件）；
  未把 L0-L3 已有答案抛用户（仅 2 次范围裁决问询：路径 c→b 授权、范围 A/B）。
- **边界声明**：6L = **判定流程终定**（C1-C5 闭合范围 A + mcio_feas review + L1/L2 升格 +
  kb v6）；scope-B（真板物理 ECO + L3 施工 + C5 芯片级实测）待后续 session；8L 重入条款
  保持（L2）。

## 5. commit 预备

- `_shared`（容器根 ic_hw_eda）：**kb.sqlite3（v6）** → commit → 容器 bump gitlink。
- `k2`：SPEC_k2_v4.json（再生 sha 8732cb75）+ .bak_v28_eco + tasks.json（登记修正）+
  tasks/mcio_feas.json（advance 状态）+ L1/L2 frozen（升格）+ C3_SPEC_REGEN_v27.md §5 +
  C5_NETLIST_CHECK_v27.md §4 + m13_v29_session_handoff.md → commit → 容器 bump gitlink。
- 容器根：bump _shared + k2。冻结区 git 前 unlock、后 lock（0/0/0）。

## 6. v29 补记（同 session 延续：pm_gate task 状态机完整闭环，2026-09-06）

> 用户「继续」：把工具链最后一段未验证流程走通 = task 状态机四段闭环能力验证。

- **mcio_feas task 全链闭环**：planned → plan → review → **build → drc → closed**
  （task_gate 机械 gate 逐段过：build/drc 查 outputs 产物 c1_via_reclass_report.json +
  c5_chip_level_expect_matrix_v28.json + spec_regen_diff_checklist_v28.json 在位；
  closed 终态）。history = [planned, plan, review, build, drc, closed]，iterations=1。
  **语义**：mcio_feas 判定任务登记闭合（判定链完成，可下传 L3 = scope-B）。
- **kb v6→v7**（put-template）：provenance.mcio_feas_phase review→**closed** +
  layer_count 补「mcio_feas task closed」（知识库 = 唯一事实源，保持与状态机一致）。
- **S 状态机（S0-S5）不动**：项目级施工阶段机，属 scope-B（L3 施工）领域；mcio_feas 作为
  L2 判定任务 closed 即完成使命。
- commit 面（v29 补记）：k2 = tasks/mcio_feas.json（closed）+ 本文件 §6；_shared =
  kb.sqlite3（v7）。容器 bump。git 前 unlock 后 lock。
