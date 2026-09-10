# Upstream change request — W3（canonical, ROOT-16 / rev W3-CN.13）

> 语义：`UPSTREAM_CHANGE_REQUEST` = 升级触发器。门判据（R-23）：`SUFFICIENT iff same_layer_crossings == 0 and capacity ok`。
> 引擎只写**版本化**请求卡（`..._<REVISION>.md`），不覆盖本 canonical 件。

## 当前状态：**UPSTREAM_CHANGE_REQUEST（未收敛；完整度量 + A + 工件自可验证）**
- rev **W3-CN.13**：`same_layer_crossings` = **完整页路由**同层异网铜冲突 = 真交叉 **+ 共线重叠（短路）**，
  覆盖 chip pad stub / via / 过渡段 / 走廊 lane / connector stub / landing→pad。**禁止空集/未度量口径**。
- **工件自可验证**：主件始终持久化 `pages[*].nodes` + `route_geometry` + `resource_gate.verification_check`；
  计数可由工件**独立重算**（实测独立重算 = 80，与主件一致）。**不再有 trust-me 标量**。
- **A 已实施**：版本化 F-8/R3 域 `m13_v57_f8_r3_gap_candidates_j2x1.json`（J2 逃逸 x 域 fan 展开；
  SPEC `j2_escape_topology`：内列向左 / 外列向右）⇒ `283 → 80`（J2 落段重叠 236 → 0）。
- R1 **32/32**、R3 **72/72**（0 cert/0 越带/0 同列<0.525）、REFCLK **2/2**。

## 残余分解（rev W3-CN.13，完整度量，可由主件重算）
| 类 | 数 | 位置 | 根因 |
|---|---|---|---|
| chip pad stub 真交叉 | **43** | chip 侧 F.Cu pad→via | via 赋位非保序（键只看距离）|
| R1 逃逸竖段共线重叠 | **4** | B.Cu 同 x | A-CN.1 未约束竖段 |
| connector 落段共线重叠 | **33** | B.Cu | J3/J4 同 pad 列多 net 共享同一 gap x |

## 已行使（合法、有效）
- A（J2 逃逸 x 域）：283 → 80。T-2 逃逸+走廊：r1_5 真交叉 217 → 0。
- R1 顺序确定性放置（F-13 v1.2 固定键 argmin + 0.525 净空）：R1 29/32 → 32/32。

## 待裁决 / 下一步（合法杠杆，闭式，项目层预授权）
1. **chip 逃逸扇平面化（43）**：加保序谓词（同侧 fan 的 via 序 = pad 序）或 T-1 出逃扇。
2. **J3/J4 落段展开（33）**：同 A 手法；注意同 y 多 pad 的 slot 序与 pad 列序一致。
3. **R1 逃逸竖段（4）**：放置谓词加「同 x 竖段不重叠」。

## Next
按 1 → 2 → 3 顺序做（均项目层预授权、零坐标搜索）；此前不宣称 FEASIBLE_ALL。
End of canonical request card (ROOT-16).
