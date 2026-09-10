# m13 v57 — W3（G4）开工卡 **v1.2**（W3-C2，构造式·零搜索）

> 版本 bump（**v1/v1.1 原文与指纹不动**：v1 `97a8084b…`、v1.1 `4555f8b6…`）。
> 依据：L2 审查意见（2026-09-10）铁律「确定性一次算对，不搜索 / 禁暴力求解与暴力迭代」+
> L2 批准的计划 `.omo/plans/k2-v57-w3-feasible-all.md`（计划 v2 通过）。
> 日期：2026-09-10｜基线 HEAD：`9e6f19e`。

**继承**：v1 §1 输入白名单（增至含 F-13 v1.1）、§2 决策契约、§6 禁令、§7 逃生门；
v1.1 的 R-1（R3 落点 y ∈ F-8 `y_band`）、R-3（验收条件化）。以下为 v1.2 增量与替换。

## R-4（替换 §3/§4 求解方法）— 全部改为**闭式构造**，零搜索

| 层 | 构造规则（O(1)/页，单遍、只前进、不回退） | 闭式常数（SPEC 先例） |
|---|---|---|
| R1 | 帧内按 F-5 序**前缀单调赋位**：`P_x :=` 该页可用 x 集中第一个 `≥ prev_P_x + 0.6`（递减帧取 `≤ prev − 0.6`）；`N_x` 同法且须与 `P_x` 构成 F-13 v1.1 `x_column_pairs` 的可容许列对；`y := pad_y + e_band·0.05·k`，`k∈{0,1}` 取最先可用；`e_band` = 带逃逸方向（up→−y、dn→+y） | `Δx_min = 0.6`（= 相邻 pad 中点距，SPEC `strap_domain_v32.route_strategy.escape` "ball-gap via (0.35) at adjacent-pad midpoint (pad-edge clr 0.125)"）；`e_band·0.05` = 网格步 |
| R1.5 | 每页**单直线段** `via₁ → (entry_x, lane_y ± 0.19)`（零折角、域内零 via） | — |
| R2 | 帧连续块：`base = floor((N_lanes − n_used)/2) = 8`（N_lanes=32、n_used=16），帧内按 F-5 序 `lane_index = block_start + j`，`lane_y = 33.3 + lane_index·1.46` | `8`、`1.46`（drc_rules diff_pair 口径） |
| R3 | 每 pad 先按**最小 gap 候选**归组，组内按 `(pad_y, net)` 前缀递推 `y_k := max(pad_y_k − 0.3, y_{k−1} + 0.6)` | `−0.3 = −0.6/2`、`0.6 = via_od + clearance`（0.35+0.175 上取整到网格） |
| REFCLK | 层 = **F.Cu**（维持 D0-2）；路径 = 消费 W0-R `refclk_passage_witness` 自由通道的闭式折线（见 `m13_v57_refclk_crossing_ruling.md`） | 通道窗口/keepout 盒 = W0-R 权威值 |

**hatch ① 作用域（L2 批准）**：R1 via x 单调 = **frame = (corridor, conn_ref, band) 内**单调
（整走廊不可行：WEST lane 序上 pad_x 先减后增；跨 frame 扇面 y 域不重叠）。

## R-5（§5 验收谓词替换）

| 谓词 | 内容 |
|---|---|
| **A-CN.1** | R1：64 via ∈ 冻结候选集；列对 `dist ≥ 0.525 ∧ \|Δx\| ≥ 0.38`；两两 ≥0.525；**帧内每极性 x 单调** |
| **A-CN.2** | R2：走廊内 lane_index 严格递增（块+帧内序）；双端谓词 `\|Δ\| ≤ 45.4` |
| **A-CN.3** | R3：72/72；同 gap 列 `\|Δy\| ≥ 0.525`；落点 ∈ F-8 `gap_candidates × y_band` |
| **A-CN.4** | R1.5：交叉数 = 0（O(n²) 纯检查，非搜索） |
| **A-CN.5** | REFCLK：段 ∈ W0-R 自由通道；与 11 keepout 盒零相交；页间 ≥1.46 |
| **A-CN.6** | 序无关：3 枚举序输出逐字节一致 |
| **A-CN.7** | `verdict = FEASIBLE_ALL ⇒ 34 页齐 + chip_landing_rows 原子重发射`（F-12，同提交同 SHA 链） |

## R-6（§4 schema 增量）

- `method`: `{name:"closed_form_construction", per_layer:{...规则名...}, closed_form_constants:{...},
  spec_precedent:{delta_x:"SPEC strap_domain_v32...", r3_off:"0.6/2", lane_base:"floor((32-16)/2)"},
  work_units:{total, formula, per_layer}, branch_sites:{per_rule_max:2}}`。
- `certificates[]`: `kind ∈ {CONSTRUCTION_INFEASIBLE}`（**禁止**表述为全局不可能性）；
  字段仅允许 `{kind, layer, rule, closed_form_condition, observed, required, page_or_pad, scope_note}`；
  `scope_note` 固定语义："本构造规则下不可行；非全局不可能性证明"。
- `contract.id = "W3-C2"`，`contract.supersedes = {v1 `97a8084b…`, v1.1 `4555f8b6…`}`。
- `supersedes_method`: `{artifact:"m13_v57_w3_joint_assignment.json", revision:"W3-JA.2",
  sha256:"d081618c…", reason:"method-level iron-law violation (search-based); 留档不改"}`。

## R-7（方法级门 G-M1..G-M6，验证器必须给出可观测证据）

G-M1 去注释/去字符串后 NAME 令牌零命中：`dfs/backtrack/csp/branch_and_bound/search/enumerate/
permutations/combinations/product/itertools/random/shuffle/while/recursion/node_cap/alternatives/
candidates_tried`（L2 确认 `enumerate/while` 为刻意收严，引擎用 `range(len(..))`/`for` 实现）。
G-M2 AST：零自调用、零 `while`、零 `itertools`/`random` import、每规则分支点 ≤2（常量）。
G-M3 闭式复杂度：`work_units == a·n + b`；`--scale K`（K=1,2,4）下 `work_units` 比 = K、耗时比 ≤ 2K。
G-M4 语义独立重导：验证器按闭式公式独立重算每页赋位/落点/路径，逐字段一致（1e-9）。
G-M5 不变量与证书：A-CN.1..5 全 PASS，或证书满足 R-6 字段约束（零"重试/回退"痕迹）。
G-M6 零备选痕迹：工件键零 `alternatives/options/tried/branch/attempts/node`；引擎零同名函数。

End of W3-C2 v1.2.
