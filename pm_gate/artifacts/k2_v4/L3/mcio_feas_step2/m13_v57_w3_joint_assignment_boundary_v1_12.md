# m13 v57 — W3 Boundary **v1.12**（ROOT-17 收口：**FEASIBLE_ALL**，完整度量）

> 契约 `m13_v57_w3_kickoff_card_v1_26.md`｜引擎 rev **W3-CN.16**
> ｜取代 v1.11（commit `a76922a`，保留不动）。授权：ROOT-16 A + ROOT-17（预授权）。**冻结四源未动**。

## 1. 收口结论（完整度量，机器可判 + 可独立重算）
- `verdict = FEASIBLE_ALL`；`gate_status.failed = []`；`certificates = []`。
- `same_layer_crossings = 0`：真交叉 `{r1_5:0, stub:0}` + 共线重叠（短路）`{r1_5:0, stub:0}`；
  覆盖**整条页路由**（chip pad stub / via / 过渡段 / 走廊 lane / connector stub / landing→pad）。
- R1 **32/32**（64 via 两两 ≥0.525，min 0.617）；R3 **72/72**（0 cert / 0 越带 / 0 同列 <0.525）；
  REFCLK **2/2**（与 keepout 零交）；34 页（32 data 含节点 + 2 refclk）。
- **F-12 原子重发射**：`m13_v57_w3_chip_landing_rows.json`（rev W3-CN.16，64 行），
  `authority.main_sha256 == sha256(m13_v57_w3_joint_assignment.json)`。
- **W4 解封**。

## 2. ROOT-17 三杠杆（逐个实测）
| 杠杆 | 前 → 后 |
|---|---|
| ① chip 逃逸扇保序（pad 对齐引线）| 真交叉 38 → **0** |
| ② J3/J4 落段展开（版本化域 `r3x2`）| 落段重叠 33 → **0** |
| ③ R1 同 x 竖段谓词（O(1) 索引）| 竖段重叠 4 → **0** |
| **合计** | **80 → 0** |

## 3. 可验证性（ROOT-16 R-104 延续）
- 主件持久化 `pages[*].nodes` + `route_geometry`（320 段）+ `resource_gate.verification_check`；
- **独立重算**（仅用主件 JSON）：真交叉 0 + 共线重叠 0 = **0**，与主件一致。
- **独立验证器复验**：见下（先改并 commit，再由子代理冻结复验）。

## 4. 复杂度 / 性能
- wall ≈ **2.6s**（≤120s 护栏）；`--scale` work(2)=1052 / work(4)=2104 = K×526（线性）；
  三个新谓词 O(1)（x 分桶 + x→span 表，逐页重建）⇒ 全域 wall 线性（此前 O(n²) 17.5s → 现线性 2.6s）。

## 5. 方法门（G-M）
- **G-M1** 去注释/去字符串 NAME 令牌 0 命中（含 while/enumerate）→ PASS。
- **G-M2** `while`=0、自调用=0、itertools/random import=0 → PASS。
- **G-M3** `work_units==公式`；`--scale` 线性；预算护栏生效。
- **G-M6** 工件无 alternatives/options/tried/branch/attempts 键；**G-M4** 仍为 T-2 前快照（D8 未清）。

## 6. 指纹
| 项 | 值 |
|---|---|
| 冻结四源（MATCH） | SPEC `0bd52ed48e720b8c` / manifest `a8ef3ea8ecff99d7` / PCB `f6273de613f43d05` / rules `0a459839e15960b8` |
| engine | rev **W3-CN.16** |
| main artifact | `m13_v57_w3_joint_assignment.json` rev W3-CN.16（FEASIBLE_ALL）|
| landing | `m13_v57_w3_chip_landing_rows.json`（authority sha == main sha）|
| 域 | `m13_v57_f8_r3_gap_candidates_r3x2.json`（旧 F-8 件不动）|

End of boundary v1.12.
