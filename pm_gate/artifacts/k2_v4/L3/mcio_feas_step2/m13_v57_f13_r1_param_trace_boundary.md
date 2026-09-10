# m13 v57 — F-13-R1TRACE Boundary Declaration

> Revision: **F13-R1TRACE.1 / F13-R1PAIR.1** ｜ Schema: 1
> Producer: `k2/tools/p3_v57_f13_r1_param_trace.py`
> Artifacts: `m13_v57_f13_r1_param_trace.json`、`m13_v57_f13_r1_pair_coupling.json`
> Independent verifier: `k2/tools/p3_v57_f13_trace_validator.py`（**不 import 生产者**）
> 范围：G3 前置项 F-13（R1 矩阵 V-2/V-3）。只读消费冻结件；**零分配、零冻结件改动**。

## 0. 冻结指纹（全 64hex，运行期硬校验）

| input | sha256 | match |
|---|---|---|
| `SPEC_k2_v4.json` | `0bd52ed48e720b8cb6a7869379f6c0a220f3e141e1514ab159f9f5f3b8b02233` | ✅ |
| `m13_v57_s1_page_manifest.json` | `a8ef3ea8ecff99d7549d4122043c972c1bb68346dc4dcc3f36fdd9bacde49890` | ✅ |
| `_shared/eda_core/drc_rules.json` | `0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448` | ✅ |
| `m13_v57_s1_r1_via_verdict.json`（只读，**判定结果不变**） | `2a3c8cf465c0ac1f808c1fdf7409725ab04862e4a8002f7ff71cfa299770bb5b` | ✅ |

drift → 非零退出（`freeze_check().drift != []`）。

## 1. 可重放断言

| # | 断言 | 期望 | 观测 |
|---|---|---|---|
| A1 | `via_od` 溯源 | 0.35 == SPEC.vias.std.outer == rules.manufacturing.min_via_diameter | ✅ |
| A2 | `clr` 溯源 | 0.2 == rules.clearance.net_classes[POWER].clearance ≥ SPEC PCIe85 0.175 ≥ board_min 0.1 | ✅ |
| A3 | `via_via` 恒等 | 0.525 == 0.35 + 0.175（via-via 铜净空 → 圆心距） | ✅ |
| A4 | 列对错距双口径 | 0.36 − 0.205 = 0.155；0.38 − 0.205 = 0.175 | ✅ |
| A5 | params_mapping 全 holds | 4/4 | 4/4 |
| A6 | 每页双约束域非空 | 32/32（>0 admissible pair） | 32/32 |
| A7 | 冻结 verdict `pair` 满足列对错距 | — | **16/32**（16 页 `\|dx\|=0.30`）→ 发现项 |
| A8 | 双跑逐字节一致 | identical | ✅（sort_keys 确定性 JSON） |
| A9 | 零分配 | 无 `assigned/selected_lane/lane_assignment` 键 | `leaked=[]` |

## 2. 字段语义

- `pair_domain`：由 verdict 的**逐网** cands 交叉重算的 pair 级域，双约束
  `dist ≥ 0.525 ∧ |dx| ≥ 0.38`；附 `dist_hist_mm` 与 `x_columns_P/N`（W3 指派消费）。
- `admissible_pair_witness`：最小 dist 的存在性见证（确定性 tie-break）——**不是分配**
  （`field_spec.allocation=false`），W3 必须在联合约束下重选（禁反演）。
- `verdict_pair`：冻结 verdict `pair` 字段的只读复读（不改写），附 `dist_ok/stagger_ok_*`。
- `caliber_differences`：CAL-1（clr 边距 vs 中心线膨胀）、CAL-2（0.36 vs 0.38）、
  CAL-3（verdict inputs_sha 仅 ballmap → 由本工件补全指纹链）。

## 3. 发现项（交 W3 / S2 / 架构师）

1. **verdict `pair` 不是列对可行解**：16/32 页 `|dx|=0.30 < 0.36/0.38`。冻结 verdict 未施加
   列对约束（V-3 GAP 的实证）。→ 由其派生的 PROVISIONAL `chip_landing_rows` 在列对口径
   **不可继承**（与 F-12「W3 必须重发射」一致）。
2. 32/32 页在双约束下域非空 → **R1 单页层面无不可行页**；但跨页 via 独占仍需联合指派
   （见 W3 卡 A-W3.2；F-13 范围外）。
3. `clr=0.2` 的权威 = POWER/GND 网类最坏值，非任意常数；判定比 PCIe85 专值更严，
   故 verdict 结论不被削弱。

## 4. 非断言 / 禁反演

- 不重判 R1 页级 verdict（ESCAPABLE/CERTIFICATE 结论不动）。
- 不从 `admissible_pair_witness` 反推 W3 指派；不把 `pair_domain` 计数当容量证明。
- 不覆盖 R1.5 过渡段、R2 lane、R3 落点（各归其层）。
- 变异测试覆盖（见验证器）：参数值扰动、源指纹扰动、域计数扰动、见证对越界 → 必须 FAIL。
