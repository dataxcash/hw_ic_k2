# m13 v55 — 施工方案模块结构性复查报告

> 范围：`_shared/eda_core` 的施工方案模块（route_input 装配 → 阶段①feasibility →
> ②capacity_audit → ③channel_alloc → ④escape_landing → ⑤hs_route_model 施工，
> 含 v53/v54 预留系统 column_book/escape_table/escape_allocator/construction_fact）。
> 复查方式：全量代码接线核对 + 真板 e2e 三次复现（16/18 失败集与钉死证据全吻合）+
> 实验性修复反证。结论均为结构级，非症状级。

---

## A. 架构级：绘图算法缺"第一段"（全局联合可行性不存在）

### A1. 全局可行性从未被自动计算
- 阶段① `RoutingTopologyGate.plan()`（solve_pipeline.py `run_feasibility`）标注
  "软依赖：三档定性交人裁决，不进自动数据流"。
- 真板实测：①=FEASIBLE、②轨道压强 **1.0（恰满）却 ok=True**、⑤却有 15+ 段
  INFEASIBLE。①/②的资源模型只数走廊轨道 + via zone + cap wall，**不数真实瓶颈
  （芯片侧出逃缝密度）**。
- 影响：可行性声明与施工结果属于两套世界，"可行"无预测力。

### A2. 阶段⑤为纯串行贪心、无 rip-up、顺序决定结果
- `solve_all_v4`（hs_route_model.py）固定序 UP0→UP7→DN0→DN7→REFCLK；已解段累积为
  障碍（shared_segs），后解撞墙即 INFEASIBLE，从不重布。
- 本会话直接反证：在 `_escape_pair` 尾加"逐极性直连尾段"兜底 → 转化 7 条
  （DN0/1/2/3 out_MCIO、DN7 input、UP4/5 out_J2）的同时，**4 条原本 SOLVED 变
  INFEASIBLE（DN1/2/3 input、DN6 out_MCIO），2 条仍 SOLVED 但字节漂移（DN0 input、
  REFCLK0 input）**。"解了前面的会改后面"——顺序耦合铁证。此前被误记为
  "alloc 已知账"，实为算法类别错误（应两段式：先全局分配、后机械展开）。

---

## B. 预留/登记系统是装饰品（"先登记后展开"从未接线）

### B1. column_book / escape_table / escape_allocator / construction_fact 无人消费
- 全仓 grep（非测试）：仅 construction_fact→escape_table 一条内部 import；
  solve_pipeline.py import 区只接 channel_alloc / escape_landing / capacity_audit /
  hs_route_model；hs_route_model 亦不读这些模块。
- 结论：v53/v54 建的登记簿**从未进入数据流**，"先登记后展开"只有 schema 没有接线。

### B2. 登记系统用"已解路径反演"自证（循环论证）
- p3_v53_phase2_gate.py docstring："反演 pinned EscapeTable（几何 = report solve
  SOLVED path）→ ColumnBook 只读预载"。
- 即用贪心求解器的**成功产物**反推登记簿来验收登记簿——只复述贪心已做到的事，
  从未被要求规划贪心做不到的事（现 18 条失败）。gate 全绿因此零预测力。

---

## C. 覆盖断裂：板子被切成"有登记 / 没登记"两个世界

### C1. U3/U7 落点区在 config 层面即残疾
- route_model_config.json escape_landing.regions：U3/U7 区 **corridor_id=null**
  （落点按 alloc 轨道锚定，无 corridor 则无法派生）→ 实测两区 **0 assigned**。
- config 声明了区却无轨道锚 = 宣告"本区不做"，但本区正是失败高发区。

### C2. 芯片侧出逃列结构性无人认领
- MCIO 需求按 suffix_only（`*_MCIO` 网）派生 → 芯片侧 cap/U6→U3 系 pad
  （x≈84-93）不在其列；J2 只管 x≥132；U3 区又无锚。结果 12×−0.205 + 5×无净空
  全部落在"无登记"那一半，退化为顺序耦合自搜。
- 区域窗口互相重叠（MCIO x∈[50,90] ⊃ U3 x∈[74,90]），pad 归属本身有二义。
- 证据：PCIE_UP0_P/N、PCIE_UP4_P/N 等在 landing allocation 中 **NO landing row**。

---

## D. 分配器自身一致性缺陷

### D1. 落点同列冲突不拦（133.825 家族）
- landing 把 DN0_P=(133.825,54.3)、DN6_P=(133.825,63.3)、DN7_P=(133.825,63.9) 分到
  同一 via 列 x=133.825（y 仅差 0.6/0.9）→ 消费阶段 fail-closed。
- 分配器无同列邻域/密度自检（ColumnBook 有 reservation 能力但未接线，未生效）。

### D2. D3 极性硬约束是纸面的
- adapter 断言 "ASSIGNED 必 polarity_consistent=true"，实测 52 行 ASSIGNED 中
  **48 行 polarity_consistent=None（unchecked）、仅 4 行 true**——硬约束 92% 未执行。

---

## E. 数据单一真源缺失与"后推账"清单

### E1. SPEC band.nets(list) vs ChannelInput.nets(str) 形状错配
- _alloc_nets 会把 list 字符串化成伪网名 → 首跑 3 伪网全 INFEASIBLE；现靠
  config nets_path 显式覆写规避，底层错配记为 WARN 留"上层 ECO"（官方报告自认）。
- 典型"把问题往后推"。

### E2. 引擎双副本、基线不锁定
- 容器 `_shared`(f15b03e，活动) vs k2/`_shared`（陈旧 84b613d）各一套；e2e 依赖
  sys.path 硬编码容器路径才绕开（env WARN 缺口）。
- 容器 `_shared` 工作树本身不干净（escape_closure_analysis.py 等有未提交改动 +
  未跟踪 .bak_v33_perball）→ "引擎真源"不是锁定物。

### E3. 阶段⑤度量误导
- `solved_pairs` 按"整 base 全段 SOLVED"计（实测=3），段级实解 16/19 在报表不可见
  → 验收只看整 base 数，鼓励"全有或全无"的局部优化、掩盖部分进展。

---

## 附带结论（与修复方案的衔接）
1. 18 条失败的**共同病灶** = 芯片侧出逃列无预留 + 施工用顺序贪心 → 缝里对穿。
2. 单改施工几何（v55 路线）已被证伪：转化必扰动（A2 反证）。
3. 修复必须按依赖序：基线固化 → 数据形状/覆盖 → 登记簿接线 → 全局可行性层 →
   分配器自洽 → 单调收敛闭环；每阶段开工前先交"为什么可行"的证明（见
   m13_v56_remediation_plan.md）。

## 最小证实实验（每条缺陷的快速再验证，供红队复核）
- A2：把 solve_all_v4 顺序倒置/按密度排序重跑 → 若失败集随顺序变化 = 顺序耦合坐实。
- B1：grep 复核（本报告已给出结果）。
- C1/C2：给 U3/U7 区补 corridor 锚后重跑 landing → 若 −0.205 类消失或转为
  NO_ESCAPE = 覆盖断裂坐实。
- D1：在 ColumnBook 写入期断言同列最小间距 → 133.825 家族应在分配期被拦。
