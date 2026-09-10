# m13 v57 — G3 冻结契约 v1.3：F-13 R1 参数溯源 + P/N 列对耦合字段

> 版本 bump（v1.2 原文**不动**，指纹保持 `c8f380c184976fb5…`）。
> 补丁来源：F-13-R1TRACE 工件（`m13_v57_f13_r1_param_trace.json` /
> `m13_v57_f13_r1_pair_coupling.json`）+ R1 矩阵 V-2/V-3 GAP 行。
> 基线 HEAD：`54587b6`｜日期：2026-09-10。

## 1. V-2 关闭：verdict 参数 ↔ 规则/设计口径 映射（可重放断言）

冻结 verdict `m13_v57_s1_r1_via_verdict.json`（sha `2a3c8cf465c0ac1f…`）的 `params` 逐项溯源：

| param | 值 | 权威源 | 关系 | 结论 |
|---|---|---|---|---|
| `via_od` | 0.35 | `SPEC.vias.std.outer` = 0.35；`drc_rules.manufacturing.min_via_diameter` = 0.35 | 等值 | **exact** |
| `clr` | 0.2 | `drc_rules.clearance.net_classes[POWER].clearance` = 0.2；`SPEC.net_classes.PCIe85.clearance` = 0.175；`rules.clearance.board_min` = 0.1 | 保守包络（0.2 ≥ 0.175 ≥ 0.1） | **conservative_envelope** |
| `via_via` | 0.525 | `via_od + PCIe85 clearance` = 0.35 + 0.175；RULES `clearance.geometry_translation`（过孔/过孔 = 圆心距 − (od1+od2)/2） | 恒等式 | **identity** |

**clr 口径判读（CAL-1）**：verdict 的 `clr=0.2` 是**铜边到铜边**净距，取 GND/POWER 网类最坏值
（verdict docstring 自注「GND/POWER netclass 保守」）。R1 设计 §推导2 的
「clearance 0.175 + 半线宽 0.1025 = 0.2775」是**中心线膨胀**（用于禁列判据），两者不同基准；
verdict 边距 0.2 ≥ 0.175 即合规，**不要求**复制 0.2775。→ 差异已注明，非缺陷。

## 2. V-3 关闭：P/N 列对耦合字段（新增，W3 消费）

**字段权威** = `m13_v57_f13_r1_pair_coupling.json`（只读 verdict 重算，不重写 verdict）。

- **双约束**（W3 指派 R1 列对时**必须同时满足**）：
  1. `dist_mm ≥ 0.525` —— via-via 圆心距（= `via_od + PCIe85 clearance`，与 F-8 冲突图同口径）；
  2. `|dx| ≥ 0.38` —— 列对错距（`p_gap + p_width = 0.175 + 0.205`），等价竖腿边缘净距
     `0.38 − 0.205 = 0.175`（= PCIe85 netclass clearance 真源）。
- **口径 NOTE（CAL-2）**：S1 设计 §R1 文本写 `≥ 0.36`（对应边缘距 0.155，见 S1 A1.3 不变量）。
  W3 准入取**真源 0.38**；0.36/0.155 作为逃逸域宽松口径保留为 NOTE，不用于准入。
- **字段**：`pages.{page_id}.pair_domain{n_pairs_dist_ok, n_pairs_admissible_stagger_{036,038},
  dist_min/max_mm, dist_hist_mm, x_columns_P/N}`；`admissible_pair_witness`；
  `verdict_pair{dist_mm, stagger_mm, dist_ok, stagger_ok_*}`。
- **`admissible_pair_witness` = 存在性见证，不是分配**（`field_spec.allocation=false`）。
  W3 必须在联合约束下**重新选取**，禁止把它当既定指派（禁反演）。
- **F-13 实测发现（须随 W3 与 S2 引用）**：冻结 verdict 的 `pair` 字段只满足 `dist ≥ 0.525`，
  **16/32 页不满足列对错距**（16 页 input 侧 `|dx|=0.30`）。故由该字段派生的
  `chip_landing_rows`（PROVISIONAL）在列对口径上**不可继承**，与 F-12 的
  「W3 联合指派必须取代之并重发射」一致。全部 32 页在双约束下**域非空**（无不可行页）。

## 3. 证据协议承接（V-2 修订项）

- verdict 的 `inputs_sha` 仅含 ballmap（缺 SPEC/manifest/rules）→ **不由本卡改写 verdict**（F-13 范围），
  改由 `m13_v57_f13_r1_param_trace.json` 提供 `spec/manifest/rules/verdict` 全 64hex 指纹链
  （CAL-3），并运行期硬校验 4 源指纹（drift → 非零退出）。
- 本卡与 F-11 口径一致：新工件一律全 64hex + schema/revision/producer 字段。

## 4. 状态

| 项 | 状态 |
|---|---|
| F-13 R1 参数溯源（V-2） | **已闭**（本文 §1，生产者+独立验证器） |
| F-13 列对耦合字段（V-3） | **已闭**（本文 §2，字段域交付 W3） |
| G3 其余（F-1..F-12） | 保持 v1/v1.1/v1.2 裁决（原文与指纹不动） |
| G3 整体 | **收口**（见 `m13_v57_g3_closure_record.md`） |
| G4/W3 | **解封**（`m13_v57_w3_kickoff_card.md`） |

## 5. 禁令

不改 SPEC / 冻结放置 / PCB 铜 / `_shared`；不改 verdict 判定结果；不原地改写 v1–v1.2 契约；
本卡不产出任何 page→lane/列/via 的资源选择（分配属 W3）。

End of G3 freeze contract v1.3.
