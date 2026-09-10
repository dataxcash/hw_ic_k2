# m13 v57 — W3 Boundary **v1.10**（ROOT-16：完整度量 + A 实施；未收敛，残余 80）

> 契约 `m13_v57_w3_kickoff_card_v1_24.md`｜引擎 rev **W3-CN.12**（`c0aa47b212d41f30…`）
> ｜取代 v1.9（`m13_v57_w3_joint_assignment_boundary_v1_9.md`，commit `88c74f1`，保留不动）。
> 授权来源：**ROOT-16（owner 授权代裁 A）**；**冻结四源未动**；零坐标搜索。

## 1. 完整度量（ROOT-16 强制口径，本版落地）
- `same_layer_crossings` = **整条页路由**的同层异网铜冲突 = 真交叉 **+ 共线重叠（短路）**；
  覆盖 chip pad stub (F.Cu) / via / 过渡段 / 走廊 lane (In2) / connector stub (B.Cu) / landing→pad (F.Cu)。
- **禁止空集口径**：stub 类此前曾为空集（守卫恒真）——已修，本版类段非空且逐段可比。
- 实测（rev W3-CN.12）：`same_layer_crossings = 80`；`crossings_by_class = {r1_5:43, stub:0}`；
  `overlaps_by_class = {r1_5:4, stub:33}`。

## 2. A 已实施（版本化 F-8/R3 域修订）
- 新件 `m13_v57_f8_r3_gap_candidates_j2x1.json`（sha `ace489a3594bd31c…`），旧 F-8 件不动；
  producer `tools/p3_v57_f8_r3_gap_candidates_j2x1.py`。
- 依据 `SPEC.constraints.j2_escape_topology`：J2 内列(132.65)向左、外列(135.0)向右逃逸；
  把每个 J2 pad 的 `gap_candidates` 重写为**唯一逃逸槽**（fan，pitch 0.6，`slot_x = base ± rank×0.6`）⇒
  同一 pad 列的多 net 各得互异 x ⇒ 落段不再共线重叠。
- 效果：`same_layer_crossings 283 → 80`（J2 落段重叠 236 → 0）。R3 仍 72/72（0 cert、0 越带、0 同列 <0.525）。

## 3. 残余分解（未收敛，如实）
| 类 | 数 | 位置 | 根因 |
|---|---|---|---|
| chip pad stub 真交叉 | 43 | chip 侧 F.Cu pad→via | via 赋位非保序（candidate 键只看距离，不看与邻 pad 的序）|
| R1 逃逸竖段共线重叠 | 4 | B.Cu 同 x | A-CN.1 只约束 via 间距，未约束竖段 |
| connector 落段共线重叠 | 33 | B.Cu | J3/J4 同 pad 列多 net 共享同一 gap x（J2 已由 A 清零）|
- 结论：**未达 FEASIBLE_ALL**；`landing_rows` 未重发射；**W4 不解封**；上游/下一步见请求卡。

## 4. 方法门（G-M）
- **G-M1** 去注释/去字符串 NAME 令牌 0 命中（含 while/enumerate）→ PASS。
- **G-M2** `while`=0、自调用=0、itertools/random import=0 → PASS。
- **G-M3** `work_units==公式`；`--scale` work(2)=1052 / work(4)=2104 = K×526；wall ≈6.6s ≤ 120s 护栏。
- **G-M6** 工件无 alternatives/options/tried/branch/attempts 键；**G-M4** 仍为 T-2 前快照（D8 未清）。

## 5. 指纹
| 项 | 值 |
|---|---|
| 冻结四源（MATCH） | SPEC `0bd52ed48e720b8c` / manifest `a8ef3ea8ecff99d7` / PCB `f6273de613f43d05` / rules `0a459839e15960b8` |
| engine | `tools/p3_v57_w3_constructive.py` rev **W3-CN.12** `c0aa47b212d41f30…` |
| main artifact | `m13_v57_w3_joint_assignment.json` rev W3-CN.12 `22211d0ae7373f9e…`（UPSTREAM_CHANGE_REQUEST）|
| J2X1 域 | `m13_v57_f8_r3_gap_candidates_j2x1.json` `ace489a3594bd31c…`（旧 F-8 `8a316329…` 不动）|
| resource / R-23 gate | `m13_v57_w3_resource_gate.json` `7c4bcb30ec698fc0…` |

End of boundary v1.10.
