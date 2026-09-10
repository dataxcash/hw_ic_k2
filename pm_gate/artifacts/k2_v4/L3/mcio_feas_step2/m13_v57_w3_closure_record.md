# m13 v57 — **W3（G4）收口记录：FEASIBLE_ALL**（rev W3-CN.20）

> 2026-09-11｜契约 `m13_v57_w3_kickoff_card_v1_28.md`｜boundary `m13_v57_w3_joint_assignment_boundary_v1_14.md`
> ｜独立验证：read-only 子代理复核 **confirmed**（k2 `04476b3`）｜**W4 已解封**

## 1. 结果
- `verdict = FEASIBLE_ALL`；`certificates = []`；`gate_status.failed = []`。

## 2. 关键数据（可由主件独立重算）
- 34 页 = 32 data（含节点）+ 2 REFCLK；R1 **32/32**；R2 帧内严格递增 + 双端 ≤45.4mm；R3 **72/72**；REFCLK **2/2**。
- **完整段度量** `same_layer_crossings = 0`（真交叉 0 + 共线重叠 0；覆盖 chip pad stub / via / 过渡段 / 走廊 lane /
  connector stub / landing→pad；320 段，两类非空）。
- **全 via 间距违例 0**（256 via：via1/corner/drop/land 各 64；异网最小中心距 **0.527152 ≥ 0.525**）。
- **F-12**：`m13_v57_w3_chip_landing_rows.json` 原子重发射（64 行；`authority.main_sha256 == main sha`）。
- 性能：wall ≈ 9.0s ≤120s；`--scale` K×526 线性；每页候选检查常数 ⇒ O(n)。

## 3. 关键构造（零坐标搜索）
- T-2 逃逸+走廊（段型分层 B.Cu/In2.Cu）：r1_5 真交叉 217 → 0。
- R1 顺序确定性放置（F-13 v1.2 固定键 argmin + 0.525 净空）：R1 29/32 → 32/32。
- A：J2 逃逸 x 域（版本化域 `…_j2x1.json`）：J2 落段重叠 236 → 0。
- ROOT-17 ②：J3/J4 落段展开（域 `…_r3x2.json`，连接器全局唯一槽）：落段重叠 33 → 0。
- ROOT-17 ③：R1 同 x 竖段谓词（O(1) 空间索引）：竖段重叠 4 → 0。
- 全 via 间距谓词（via1/corner/drop/land；O(1) 分桶）：via-via 违例 9 → 0。
- **ROOT-18 T-1 chip 出逃扇**：径向 homothety 目标 + pad 对齐 x + breakout 平面性谓词（贪心保序）：chip 互交 1 → 0。

## 4. 独立验证与 3 次过早声明的撤回
| # | 过早声明 | 证伪点 | 处置 |
|---|---|---|---|
| 1 | ROOT-9/14 "crossings=0" | 度量只取 r1_5、stub 类空集（vacuous） | 完整度量引入 → 240；修守卫/全类口径 |
| 2 | `e550df9`（ROOT-15）FEASIBLE_ALL | 漏计共线重叠 → 283 | 撤回（boundary v1.9） |
| 3 | `0643771`（ROOT-17）FEASIBLE_ALL | 全 via 间距违例 9（min 0.170） | 撤回（boundary v1.13） |
- 终态 `04476b3`（ROOT-18）：独立验证 confirmed；重算器自校验 `_CN.13→80 / _CN.18→1 / _CN.20→0`。

## 5. 过程缺陷（记档）
- ROOT-11 的 11 分钟 100% CPU = **缺陷**（G-M3 wall 线性 + 变相搜索）；处置：预算护栏 `--max-wall`(120s) + 离线预计算 O(1) 查表 + O(1) 空间索引（wall 17.5s→9.0s）。

## 6. Caveats（诚实登记）
1. REFCLK 不在两度量口径内（无 nodes/vias、不在 route_geometry）；"不劣化" 依 `layers.REFCLK`（A-CN.5 PASS）。
2. R3 同 `(ref,column_x)` 子检为空集，但全局同 `column_x` 最小 dy=9.0 ≥0.525，无违例。

## 7. 指纹
- 主件 `m13_v57_w3_joint_assignment.json` rev W3-CN.20 `493e39b481cb7446`
- landing `m13_v57_w3_chip_landing_rows.json` rev W3-CN.20 `4f323bc4372a26d3`（authority == main sha）
- card `m13_v57_w3_kickoff_card_v1_28.md` `0ae3016379cd1db2`｜boundary `…_v1_14.md` `b9cb87a99ae658a9`
- 域 `m13_v57_f8_r3_gap_candidates_r3x2.json` `5511c8c30c21f914`（旧 F-8 `8a316329…` 不动）
- 冻结四源 SPEC `0bd52ed48e720b8c` / manifest `a8ef3ea8ecff99d7` / PCB `f6273de613f43d05` / rules `0a459839e15960b8`
- k2 `d9e6161`｜ic_hw `0ff37f3`

## 8. 下一步
- D8：T-2/river 感知独立验证器 + 重生成 `m13_v57_w3_validation.json`（项目层）。
- G5（W4 真图验证）→ G6（L4）→ G7（L5）。
