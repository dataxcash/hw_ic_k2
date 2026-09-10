# m13 v57 — W3 Boundary **v1.13**（ROOT-17 纠正：撤回 v1.12 的 FEASIBLE_ALL；残余 1 + via 修正）

> 契约 `m13_v57_w3_kickoff_card_v1_27.md`｜引擎 rev **W3-CN.18**
> ｜取代 v1.12（commit `0643771`，保留不动）。授权：ROOT-16 A + ROOT-17。**冻结四源未动**。

## 0. 纠正声明（诚实留痕）
- v1.12（commit `0643771`）宣称 `FEASIBLE_ALL`。**独立验证器证伪**，本版**撤回**。
- 证伪：v1.12 的器具化几何含 **9 对异网 via–via 中心距 < 0.525**（最小 0.170），
  而 A-CN.1b 只覆盖 R1 的 64 个 via，**未覆盖** river 扇出新增的 corner/drop/land via。
- 本轮已把 **via–via 0.525 覆盖到全部 via**（via1/corner/drop/land，异网；同网豁免）：**9 → 0**。

## 1. 当前真实计量（rev W3-CN.18，完整度量 + 全 via 间距）
- `verdict = UPSTREAM_CHANGE_REQUEST`（**未达 FEASIBLE_ALL**）。
- `same_layer_crossings = 1`（真交叉）+ 共线重叠 0；全 via 间距违例 **0**。
- 残余 1 = **chip 侧 F.Cu pad→via 引线真交叉**：`PCIE_DN7/out_MCIO#fcu_pad/N` × `PCIE_UP7/input#fcu_pad/N`
  （相邻 BGA 行同向逃逸、落 via 落入内侧行 → 引线互交）。
- R1 **32/32**、R3 **72/72**、REFCLK **2/2**、34 页；`landing` **未重发射**（F-12）；**W4 不解封**。

## 2. 本轮三杠杆（逐项实测；对应 ROOT-17）
| 杠杆 | 效果 |
|---|---|
| ① chip 逃逸扇 pad 对齐（近垂直引线）| chip 真交叉 38 → 1 |
| ② J3/J4 落段展开（版本化域 `r3x2`，全局唯一槽）| 落段重叠 33 → 0 |
| ③ R1 同 x 竖段谓词（O(1) 索引）| 竖段重叠 4 → 0 |
| 追加：**全 via 间距谓词**（ROOT-17 独立验证发现）| via–via 违例 9 → 0 |
| **合计** | 段冲突 80 → **1**；via 违例 **9 → 0** |

## 3. 残余根因与最小下一项（诚实、闭式）
- chip 焊盘是 **2D BGA ball field**（4 行 × 16 列），多行**同向**逃逸时内行引线必穿外行 ⇒ 需
  **T-1 出逃扇**（拓扑样板库 T-1）：外行先逃、内行经行间缝隙嵌套出逃，闭式确定序、零搜索。
- 或：放宽 chip via 候选域使其含「行间缝隙」候选位（需 DRC 校验）。**均项目层，预授权**。

## 4. 方法门（G-M）
- **G-M1** 0 命中（含 while/enumerate）；**G-M2** while=0/自调用=0；**G-M3** work 公式 + `--scale` 线性；
  **G-M6** 无禁用键；**G-M4** 仍为 T-2 前快照（D8 未清）。

## 5. 指纹
| 项 | 值 |
|---|---|
| 冻结四源（MATCH） | SPEC `0bd52ed48e720b8c` / manifest `a8ef3ea8ecff99d7` / PCB `f6273de613f43d05` / rules `0a459839e15960b8` |
| engine | rev **W3-CN.18** |
| main artifact | `m13_v57_w3_joint_assignment.json` rev W3-CN.18（UPSTREAM_CHANGE_REQUEST；含 pages/route_geometry/resource_gate）|
| 域 | `m13_v57_f8_r3_gap_candidates_r3x2.json`（旧 F-8 件不动）|
| landing | v1.12 的 landing 已归档 `m13_v57_w3_chip_landing_rows_W3-CN.16.json`（superseded）|

End of boundary v1.13.
