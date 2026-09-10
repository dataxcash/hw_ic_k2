# m13 v57 — W3 Boundary **v1.14**（ROOT-18 收口：**FEASIBLE_ALL**，T-1 chip 出逃扇）

> 契约 `m13_v57_w3_kickoff_card_v1_28.md`｜引擎 rev **W3-CN.20**
> ｜取代 v1.13（commit `c5a6312`，保留不动）。授权：ROOT-16 A + ROOT-17 + ROOT-18（预授权）。**冻结四源未动**。

## 1. 收口结论（完整度量 + 全 via 间距，机器可判 + 可独立重算）
- `verdict = FEASIBLE_ALL`；`gate_status.failed = []`；`certificates = []`。
- `same_layer_crossings = 0`：真交叉 `{r1_5:0, stub:0}` + 共线重叠（短路）`{r1_5:0, stub:0}`；
  覆盖整条页路由（chip pad stub / via / 过渡段 / 走廊 lane / connector stub / landing→pad）。
- **全 via 间距违例 = 0**（256 个 via 跨 via1/corner/drop/land；异网最小中心距 **0.5272 ≥ 0.525**）。
- R1 **32/32**、R3 **72/72**、REFCLK **2/2**、34 页（32 data 含节点 + 2 refclk）。
- **F-12 原子重发射** `m13_v57_w3_chip_landing_rows.json`（rev W3-CN.20，64 行），
  `authority.main_sha256 == sha256(m13_v57_w3_joint_assignment.json)`。**W4 解封**。

## 2. T-1 chip 出逃扇（ROOT-18）
- chip 焊盘 = 2D BGA ball field（4 双行 × 8 列 × P/N）；ROOT-17 残余 1 = 相邻行同向逃逸引线互交。
- 实现（确定性、单遍、零搜索）：
  1. **径向出逃目标**：via 目标 = pad + 0.05·(pad − pad 场质心)（homothety ⇒ 保序/平面）；
  2. 放置键**以 pad 对齐 x 为主**、径向 y 为次（近垂直引线 ⇒ 同层异网引线平行不交）；
  3. **breakout 平面性谓词**：候选 chip 引线（F.Cu）对已放置引线做**空间分桶**冲突检查（真交叉+共线重叠），
     拒绝一切会互交的候选 ⇒ 贪心保序出逃（T-1「外行先逃、内行不穿」）。
- 效果：chip 段冲突 **1 → 0**。

## 3. 可验证性（R-104 延续）
- 主件持久化 `pages[*].nodes` + `route_geometry`（320 段）+ `resource_gate.verification_check`。
- **独立重算**（仅用主件 JSON）：真交叉 0 + 共线重叠 0 = **0**；全 via 间距违例 0（min 0.5272）。与主件一致。

## 4. 复杂度 / 性能
- wall ≈ **9.0s** ≤ 120s 护栏；`--scale` work(2)=1052 / work(4)=2104 = K×526（线性），scale wall 比 1.43 ≤ 2K。
- 每页候选检查为**常数**（域大小固定），合计 O(n) ⇒ 全域 wall 线性。

## 5. 方法门（G-M）
- **G-M1** 去注释/去字符串 NAME 令牌 0 命中（含 while/enumerate）→ PASS；**G-M2** while=0、自调用=0；
  **G-M3** work 公式 + 线性；**G-M6** 无禁用键；**G-M4** 仍为 T-2 前快照（D8 未清）。

## 6. 指纹
| 项 | 值 |
|---|---|
| 冻结四源（MATCH） | SPEC `0bd52ed48e720b8c` / manifest `a8ef3ea8ecff99d7` / PCB `f6273de613f43d05` / rules `0a459839e15960b8` |
| engine | rev **W3-CN.20** |
| main artifact | `m13_v57_w3_joint_assignment.json` rev W3-CN.20（FEASIBLE_ALL）|
| landing | `m13_v57_w3_chip_landing_rows.json`（authority sha == main sha）|
| 域 | `m13_v57_f8_r3_gap_candidates_r3x2.json`（旧 F-8 件不动）|

End of boundary v1.14.
