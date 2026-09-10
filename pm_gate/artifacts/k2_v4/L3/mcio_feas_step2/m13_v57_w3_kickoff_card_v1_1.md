# m13 v57 — W3（G4）开工卡 **v1.1**（W3-C1 v1.1）

> 版本 bump（**v1 原文与指纹不动**：`m13_v57_w3_kickoff_card.md` sha `97a8084bb73f3af2…`）。
> 补丁来源：W3-JA.1 实跑 + 独立验证器（`m13_v57_w3_validation.json`）+ 架构复核登记的三项契约缺陷。
> 日期：2026-09-10｜基线 HEAD：`7e3f92e`。

**v1 未变部分**：§1 输入白名单、§2 决策契约、§3 层语义、§5 验收谓词（除 A-W3.1 条件化）、
§6 禁令、§7 逃生门 **全部继承**。以下三处修订。

## 修订 R-1（§3 R3 落点规则）— 采用 F-8 `y_band` 权威口径

- **v1 规则（作废）**：落点 = `(gap 列 x, pad y)`（y 固定于 pad 行）。
- **v1.1 规则（生效）**：落点 = `(gap 列 x, y)`，其中 `y ∈ y_band(entry)`（**F-8 已发射的
  `entries[*].y_band`**，即 pad 行 ± 半行距；J2 half=0.3 / J3-J4 half=1.25）；同 gap 列内
  `|Δy| ≥ 0.525`（via 外径 + PCIe85 clearance），且落点两两不重合。
- **依据**：F-8 定义原文即「隙候选 = pad 行 y ± 半行距内可落 via 的 x 列」——v1 把 y 写死为
  pad y 是**本卡的过度收窄**，非 F-8 口径。实跑证明该收窄在 J3/J4 产生 **鸽笼不可行**
  （最小核示例 `PCIE_UP2_N`/`PCIE_UP3_P`：同 y=43.25、唯一候选列 55.9），而 `y_band` 口径下
  **32/32 页可行**（W3-JA.1 诊断探针：J2 36 节点 / J3 19 节点 / J4 19 节点，见
  `layers.R3.strict_rule_finding`）。
- v1 严格规则下的不可行性**保留为口径取证**（`strict_rule_finding`），不再作为阻塞证书。

## 修订 R-2（§4 输出 schema）— 与实现一致化（冻结为 v1.1 schema）

- `layers.R2.assignment` = **按走廊嵌套**：`{<corridor>: {<page_id>: {lane_index, lane_y,
  conn_delta_mm, chip_delta_mm, reach_avail_mm, ok}}}`（原 v1 写法 `{<page_id>: …}` 未定走廊域）。
- `layers.R2.objective` = `{objective_mm: <total>, per_corridor: {<cid>: mm}}`
  （原 v1 `total_abs_delta_mm` 更名；定义不变 = Σ|lane_y − conn_row_y|）。
- `layers.R3.assignment` = `{<net>: {ref, pad:[x,y], y, column_x, landing:[x,y], kind, page, pol,
  gap_column_candidates}}`，`landing[1]` 为求解出的 `y_band` 内 y。
- 其余键与 §4 v1 相同；`contract.id` 记 `"W3-C1 v1.1"`，`contract.card_md` 指向本文件，并附
  `contract.supersedes` = v1 sha。

## 修订 R-3（§5 A-W3.1）— 条件化，消除与 A-W3.6 的内部矛盾

- **A-W3.1（72/72 落点）仅在 `verdict == FEASIBLE_ALL` 时判 PASS/FAIL。**
- 当 `verdict == CERTIFICATE` 时：A-W3.1 记为 `N/A(CERTIFICATE)`，但**必须**满足：
  ① 未达成守恒的每一层/连接器在 `certificates[]` 有对应条目（含 `minimal_core` +
  `why_no_alloc_possible` + `escape_hatches`）；② `landing_rows=null` 且
  `landing_rows_status="NOT_REEMITTED"`（A-W3.6）。
  > 理由：v1 同时要求「72/72」与「证书态禁发射」在不可行场景下自相矛盾；证书态的正确验收
  > 是「不可行须被证明并归因」，不是「必须可行」。

## 状态

| 项 | v1 | v1.1 |
|---|---|---|
| R3 落点 y | 固定 pad y（J3/J4 不可行） | `y_band` 内求解（32/32 页可行） |
| R2 schema | flat（未定走廊域） | 走廊嵌套 |
| A-W3.1 | 恒要求 72/72 | 条件化 + 证书归因 |
| A-W3.5/6/7/8 | 不变 | 不变 |
| 门控 | — | 本卡发布后 W3 以 **W3-JA.2** 重发射 |

End of W3-C1 v1.1.
