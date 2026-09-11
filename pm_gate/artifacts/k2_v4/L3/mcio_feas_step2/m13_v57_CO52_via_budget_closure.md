# CO-52 — 【L2 过孔策略自裁】过孔预算闭合 L4-F（每网 via <= SPEC 显式上限）

> 2026-09-12｜性质：**L2 过孔策略闭包机判**（宪法第五章第 4 条「过孔预算闭合」）｜零几何改动、零判定变更
> 前置：CO-51 `922feaf4b5c8c143`｜触发：核查 L2/过孔策略时发现 SPEC 每线上限**从未被机上校验**。

## 1. 现象（宪法硬条款未被机判）
宪法第五章第 4 条要求「过孔预算闭合」。SPEC (rev-3) 已给出**显式字段**：
- `vias.high_speed.max_per_line = {"bandX_escape_In2": 4, "bandY_escape_B": 6}`（basis：CO-09 §3 + CO-11 §8 L2 过孔策略）；
- `constraints.escape_transition_zone.refclk_j2_transit.max_vias_per_line = 2`（ECS-001）。
但 L4 验证器（L4-A..E）只校验链连续与层变 via，**无任何每网 via 数上限校验**；板上实际用量只有人读。

## 2. band 归属（可由 via 层确定，非猜测）
`rec["vias"][net]` 的 `layers` 集合：含 `B.Cu` ⇒ `bandY_escape_B`；否则含 `F.Cu↔In2` / `In2↔In6` ⇒ `bandX_escape_In2`；
`PCIE_REFCLK*` ⇒ 走 `refclk_j2_transit`。实测分布（层对）：`F-In2`×92 / `In2-In6`×88 / `F-B`×32 / `In6-B`×32 / `F-In6`×8。

## 3. 实施（L4 验证器新增 **L4-F**，rev `L4-V1 → L4-V2`）
对 `rec["vias"]` 逐网判定 band 族并对比 SPEC 显式上限；输出 `via_budget`（`classes{limit,max_used,nets,over}` + `total_vias` + `source`）；
超限即 `viol` ⇒ verdict FAIL。

## 4. 实测（全合规；机判）
| 类 | 上限 | 实测最大值 | 网数 | over |
|---|---|---|---|---|
| `bandX_escape_In2` | 4 | **4** | 32 | [] |
| `bandY_escape_B` | 6 | **4** | 32 | [] |
| `refclk_j2_transit` | 2 | **2** | 4 | [] |
| 合计 | — | — | 68 | **total_vias = 252** |

⇒ `L4 VAL: verdict=PASS checks={L4-A..**L4-F**: True} viol=0`。
指纹：validator `a2f80b3cffe14a82`｜l4_validation `9521321baf7ff2b0`（L4-V2）｜G7 记录 `f52972e4c4bc4198`；fab `9a223923b029a1f9` / dfm `de14f887a7819c11` / si `305c237c88762b94` 未变。

## 5. 未改物 / 红线
零几何改动：drawing `dfa1d7c4a811b0da`、板 `cdcb869e9827ec87`；四冻结源未动；无阈值放宽（只用 SPEC 既有显式字段）。
