# m13 v57 — W3 Boundary **v1.11**（ROOT-16：完整度量 + A + 工件自可验证；残余 80）

> 契约 `m13_v57_w3_kickoff_card_v1_25.md`｜引擎 rev **W3-CN.13**
> ｜取代 v1.10（commit `f621595`，保留不动）。授权：ROOT-16（owner 授权代裁 A）。**冻结四源未动**。

## 1. 本版相对 v1.10 的关键修正：工件**自可验证**
- 独立复核指出 v1.10 的 UPSTREAM 主件 `pages=[]`/`layers={}` ⇒ 计数（80 及分解）**无法由工件独立重算**（trust-me 标量）。
- 现改为：无论 verdict，主件始终持久化 `pages[*].nodes` + `route_geometry`（全部段/层/端点）+ `resource_gate.verification_check`；
  并**取消**早退（不再丢掉几何）。**禁止**空 `pages`/空 `layers`。
- 实测：由主件 `route_geometry` **独立重算** = `43 + 4 + 33 = 80`，与主件 `verification_check.same_layer_crossings` 一致。

## 2. 完整度量（ROOT-16 口径）
- `same_layer_crossings` = 真交叉 **+ 共线重叠（短路）**，覆盖 chip pad stub / via / 过渡段 / 走廊 lane /
  connector stub / landing→pad；同层异网；同网相邻段不互比。
- 实测：`80` = `crossings {r1_5:43, stub:0}` + `overlaps {r1_5:4, stub:33}`。

## 3. A 已实施（版本化 F-8/R3 域修订）
- `m13_v57_f8_r3_gap_candidates_j2x1.json`（旧 F-8 `8a316329…` 不动）；J2 唯一逃逸槽 fan；
  `283 → 80`（J2 落段重叠 236 → 0）。R3 **72/72**（0 cert / 0 越带 / 0 同列 <0.525）、REFCLK 2/2、R1 32/32。

## 4. 残余（未收敛，如实）
| 类 | 数 | 位置 | 根因 |
|---|---|---|---|
| chip pad stub 真交叉 | 43 | chip 侧 F.Cu pad→via | via 赋位非保序 |
| R1 逃逸竖段共线重叠 | 4 | B.Cu 同 x | A-CN.1 未约束竖段 |
| connector 落段共线重叠 | 33 | B.Cu | J3/J4 同 pad 列多 net 共享 gap x |
- **未达 FEASIBLE_ALL**；`landing` 未重发射；**W4 不解封**。

## 5. 方法门（G-M）
- **G-M1** 0 命中（含 while/enumerate）→ PASS；**G-M2** while=0/自调用=0；**G-M3** work 公式+线性（K×526），wall ≈6.4s ≤120s；
- **G-M6** 无 alternatives/options/tried/branch/attempts；**G-M4** 仍为 T-2 前快照（D8 未清）。

## 6. 指纹
| 项 | 值 |
|---|---|
| 冻结四源（MATCH） | SPEC `0bd52ed48e720b8c` / manifest `a8ef3ea8ecff99d7` / PCB `f6273de613f43d05` / rules `0a459839e15960b8` |
| engine | rev **W3-CN.13** |
| main artifact | `m13_v57_w3_joint_assignment.json` rev W3-CN.13（UPSTREAM_CHANGE_REQUEST；含 pages/route_geometry/resource_gate）|
| J2X1 域 | `m13_v57_f8_r3_gap_candidates_j2x1.json` `ace489a3594bd31c…` |

End of boundary v1.11.
