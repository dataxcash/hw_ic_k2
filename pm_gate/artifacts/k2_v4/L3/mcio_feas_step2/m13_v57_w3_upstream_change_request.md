# Upstream change request — W3（canonical, ROOT-16 / rev W3-CN.12）

> 语义：`UPSTREAM_CHANGE_REQUEST` = 升级触发器。门判据（R-23）：`SUFFICIENT iff same_layer_crossings == 0 and capacity ok`。
> 引擎只写**版本化**请求卡（`..._<REVISION>.md`），不覆盖本 canonical 件。

## 当前状态：**UPSTREAM_CHANGE_REQUEST（未收敛；完整度量 + A 已实施）**
- rev **W3-CN.12**：`same_layer_crossings` = **完整页路由**同层异网铜冲突 = 真交叉 **+ 共线重叠（短路）**，
  覆盖 chip pad stub / via / 过渡段 / 走廊 lane / connector stub / landing→pad。**不再有空集口径**。
- **A 已实施**：版本化 F-8/R3 域修订 `m13_v57_f8_r3_gap_candidates_j2x1.json`（J2 逃逸 x 域 fan 展开，
  pitch 0.6，内列向左 / 外列向右，依 SPEC `j2_escape_topology`），引擎按唯一槽赋位 ⇒ 落段互异 x。
- 实测：`same_layer_crossings = 80`（A 前 283 → A 后 **80**）；`{真交叉 r1_5:43, stub:0}` + `{共线重叠 r1_5:4, stub:33}`。
  R1 **32/32**、R3 **72/72**（0 cert、0 越带、0 同列 <0.525）、REFCLK **2/2**。

## 残余分解（rev W3-CN.12，完整度量）
| 类 | 数 | 位置 | 说明 |
|---|---|---|---|
| chip pad stub 真交叉 | **43** | chip 侧 F.Cu pad→via 引线 | via 赋位非保序 ⇒ 引线互交（chip 逃逸扇 / T-1 需平面化）|
| R1 逃逸竖段共线重叠 | **4** | B.Cu，同 x | A-CN.1 只约束 via 两两 ≥0.525，未约束竖段 |
| connector 落段共线重叠 | **33** | B.Cu | J3/J4 同 pad 列多 net 共享同一 gap x（J2 已由 A 清零）|

## 已行使（合法、有效）
- **A（J2 逃逸 x 域）**：`283 → 80`（J2 落段重叠 236 → 0）。旧 F-8 件不动。
- T-2 逃逸+走廊（段型分层）：r1_5 真交叉 217 → 0。
- R1 顺序确定性放置（F-13 v1.2 固定键 argmin + 0.525 净空）：R1 29/32 → 32/32。

## 待裁决 / 下一步（合法杠杆，附闭式依据）
1. **chip 逃逸扇平面化（43）**：对 (pad, via) 赋位加**保序谓词**（同侧 fan 的 via 序 = pad 序），
   或按 T-1 出逃扇构造；闭式、单遍。项目层、预授权。
2. **J3/J4 落段展开（33）**：同 A 手法（per-connector 唯一逃逸槽 + land-stub 去共线）；
   注意 J3/J4 存在**同 y 多 pad**，需 slot 序与 pad 列序一致以避免 land-stub 共线。
3. **R1 逃逸竖段（4）**：放置谓词加「同 x 竖段不重叠」；项目层、预授权。

## 已披露的度量边界
- 完整度量含 chip pad stub / connector stub / landing→pad；REFCLK 段另见 A-CN.5（未纳入本计数）。

## Next
先做 1（43，最大且最“上游化”），再做 2、3；全部为项目层预授权、零坐标搜索。
End of canonical request card (ROOT-16).
