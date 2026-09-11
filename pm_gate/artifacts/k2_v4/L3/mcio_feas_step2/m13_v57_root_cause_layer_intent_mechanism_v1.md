# 根因分析 — 板层意图由「工单/修订卡参数」设定，未参与容量闭合派生（整改 #03）

> 2026-09-11｜作者：ARCHER（执行侧）｜层级：**机制（methodology）**，非参数
> 触发：整改通知 #03（撤销 owner 参数特权请求）。证据全部指向已入库工件；本件不改冻结四源、不动 canonical W3-CN.25。

## 0. 结论（一句话）
**层意图（哪些层作信号 / 共几层）从来不是求解器的输出，而是被外部（工单/修订卡/用户裁决）灌入的输入参数；
闭式只做 `SUFFICIENT iff D ≤ |给定层集|` 的**验算**，算法**不能派生最小层集**。给定集不足时机制无自主路径 →
退化为「要特权加层」。**

## 1. 证据链（逐条可复核）
| # | 事实 | 工件/字段 |
|---|---|---|
| E1 | 层意图 rev1 的 authority = **D1 修订卡** | `m13_v57_layer_intent_rev1.json:authority=m13_v57_d1_layer_intent_revision_card.md` |
| E2 | 该卡把 `In4.Cu` 放行作过渡信号层，只改 `transition_eligible` 集合（A:2→3） | `m13_v57_d1_layer_intent_revision_card.md §1` |
| E3 | rev2 的 `authorization_source = "supervision work order W3-C5 (NOT L2)"` | `m13_v57_layer_intent_rev2.json` |
| E4 | rev4 的 `authorization_source = "supervision work order W3-C7"` | `m13_v57_layer_intent_rev4.json` |
| E5 | 闭式 = **只验算给定集合**：`verdict = SUFFICIENT iff D <= |transition_eligible_layers|` | rev1 json `closed_form` |
| E6 | 层数（6L）由 **v20 用户裁决**设定：「6L 先试不闭合回 8L」 | `L1_TOPOLOGY_v2.0.md:6` |
| E7 | 6L 后来被「升格」为「判定流程终定」，依据是 **C1-C5 条件闭合**（per-ball 引擎 FEASIBLE）——**容量级/球级口径**，不含完整净距套件与对内等长 | `L1_TOPOLOGY_v2.0.md:7-14, 114-124` |
| E8 | 拓扑/过孔策略仍按 **8L** 冻结：「2026-08-19 **8 层定案**」「8 层：In2 独立走廊…B.Cu 释放」(j2_escape_topology / gnd_stitch_via)；但 stackup 已是 6L；`pd.gnd_planes` 仍含 In5 | `SPEC_k2_v4.json /constraints, /pd`；`L1-PF.2` §2/§3 |

## 2. 三个追问的答复
**(1) 层意图为何由工单/修订卡设定？**
因为它是 L1/L2 的**冻结决策**（宪法 Ch.2 L1=层数、L2=叠层/层用途），而 L1/L2 的候选竞标在该板上**从未真正做过**
（宪法序言：历史上 L1/L2 从未竞标，默认拓扑直接进 L3）。L1/L2 的产物以 SPEC/冻结文档形式**被消费**，
求解器只读不改 → 层集天然成为**外生参数**。修订卡/工单是「事后补参数」的通道。

**(2) 为何不参与容量闭合派生？**
现有 `closed_form` 是**谓词**（给定集合够不够），不是**生成器**（最小集合是几）。缺一条 `层集 = derive(需求, 容量)` 的机制；
且 `transition_eligible_layers` 由意图件直接给出 ⇒ 生成器被短路。

**(3) 8L→6L 何时、以何依据被"砍"而未重推导？**
- **何时**：2026-08-23~09-05（`stackup 8L->6L` 出现在 SPEC regen scope；`in6_usage` 记录 "removed: 8L In6.Cu semantics"）。
- **依据**：**v20 用户裁决**「6L 先试」（E6）→ 之后 C1-C5 条件闭合升格为「流程终定」(E7)。
- **为何未重推导**：C1-C5 用 **per-ball 逃逸引擎（容量级）** 判 FEASIBLE，**没有**把「完整净距套件 + 对内等长 + 层意图派生」纳入；
  即**判定口径不完整** + **层集是给定参数**（无派生器）⇒ 层数从未被容量闭合重新推导，拓扑（8L）与叠层（6L）留成互相矛盾的冻结态。

## 3. 业务影响（机制级）
- 每次守恒墙（净距/逃逸/等长）都只能靠人工给参数（保留/放宽/加层）→ **不可扩展、不可自治**。
- 学习无用：被纠正的量（层集/层数）**不在模型变量集**里，样本无法覆盖。
- 与宪法 Ch.1 规则二/三冲突：**强条未在设计阶段内嵌**，QA/QC 成了探照灯。

## 4. 修复方向（本件只定根因；实现见机制规格）
把**层意图变成容量闭合的派生输出**：
`L_signal = max( L_escape , L_capacity , L_conflict , 3 )`，`total = 2·L_signal`；
层集、层用途、拓扑全部由**冻结四源 + 规则**确定性推出（零搜索、零工单参数）。
详见 `m13_v57_layer_intent_mechanism_spec_v1.md` + 引擎 `k2/tools/p3_v57_layer_intent_derive.py`
+ 输出 `m13_v57_layer_intent_derived_v1.json`。

## 5. 红线 / 纪律
冻结四源 **未改**；canonical `W3-CN.25` **未改**；零搜索（引擎全 O(n) 闭式）；层意图派生件**版本化新文件**。
