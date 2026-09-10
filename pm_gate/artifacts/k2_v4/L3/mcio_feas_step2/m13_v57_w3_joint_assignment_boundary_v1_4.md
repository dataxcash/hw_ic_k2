# m13 v57 — W3 Boundary **v1.4**（W3-C4：上游资源充分性门已生效）

> 契约 `m13_v57_w3_kickoff_card_v1_4.md`（W3-C4，sha `be15305c…`）｜引擎 rev **W3-CN.3**
> 本文件取代 v1.3 boundary（`7c5775b3…`）。

## 1. 门实测（W3 入口，闭式 O(n)）

| 量 | 值 |
|---|---|
| 过渡可用信号层 `A` | **2**（`In2.Cu`, `B.Cu`；`F.Cu`=stub_only，`In4.Cu`=power_plane(SPEC)） |
| 层需求 `D`（chip 过渡 x 带 `[82.35,105.25]` 内扇面 y 区间最大重叠） | **3**（y≈55.15 处 `EAST/up + WEST/up + WEST/dn`；EAST 两扇面在 [56.66,78.56] 重合） |
| 走廊/带容量 | 16/16 ≤ 32 ✓ |
| 判定 | **`UPSTREAM_CHANGE_REQUEST`**（缺口 **Δ=1 层**） |

**门生效行为**：`main()` 在 R1/R1.5 之前返回 → 工件 `layers={}`, `pages=[]`（**未进入求解**），
`landing_rows=null`/`NOT_REEMITTED`，并同时产出
**上游变更请求卡 `m13_v57_w3_upstream_change_request.md`**（升级触发器语义）。

## 2. 请求卡待裁项（每项附闭式依据）

| # | 层意图项 | 改了就能过的闭式依据 |
|---|---|---|
| 1 | **In4.Cu 作信号层** | `D(3) ≤ A` ⟹ `A ≥ 3` |
| 2 | **放宽 `no_90deg`** | R1.5 走通道化折线：同层同 y 通道唯一占用谓词 |
| 3 | **lane 序按源序排** | `sign(Δsrc_y) = sign(Δlane_y) ∀a,b`（则可单层对齐） |
| 4 | **R1 全局单调 x** | 须放宽 ±1.5mm 逃逸域以容纳全局 ramp |

## 3. 验收对照（W3-C4）

| 要求 | 证据 |
|---|---|
| 门可观测 | 工件 `resource_gate{verdict, D, A, gap, fan_groups, closed_form}` |
| 不足 → 出变更请求而非继续 W3 | `layers={}`/`pages=[]` + `m13_v57_w3_upstream_change_request.md` |
| 契约版本 bump（新文件） | card v1.4（`be15305c…`），v1–v1.3 未动 |
| 冻结四源不动 | SPEC `0bd52ed4…` / manifest `a8ef3ea8…` / PCB `f6273de6…` / rules `0a459839…` MATCH |
| 零搜索 | G-M1 令牌扫描 = 0 命中 |

## 4. 附带修正（随 v1.4）

- 门的 `lane_region` 意图与实现同序（按走廊 chip 源行均值升序），故 `D=3` 而非按字母序的 4。
- R1 极性同侧规则（§R-15）已写入引擎（待门放行后生效）。
- 未达项（264 同层交叉 / 3 页无赋位）**不再在 W3 内处理**，全部归入本卡的请求卡（天条：停机回上层）。
