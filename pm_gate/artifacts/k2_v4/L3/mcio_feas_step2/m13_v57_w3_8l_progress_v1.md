# W3 8L（LID.1 派生叠层）重跑进展 — 波 1→2（整改 #03 落地）

> 2026-09-11｜作者：ARCHER｜引擎 rev **W3-CN.26**｜契约：LID.1 8L 派生（signal=F/In2/In6/B）
> 依据：`m13_v57_layer_intent_derived_v1.json`(LID.1) + `m13_v57_layer_intent_adoption_v1.json` + CO-02 R-04。
> 纪律：不改冻结四源原件；canonical `m13_v57_w3_joint_assignment.json` **未改**（W3-CN.25/FEASIBLE_ALL/c17c5a42）。

## 1. 引擎改动（8L：3 通道层 + 4 信号层）
| 项 | 旧（CN.25，2 通道层） | 新（CN.26，派生 8L） |
|---|---|---|
| layer_intent | rev4（工单参数，{In2,B}） | **rev5（LID.1 派生，{In2,In6,B}）** |
| 通道层分配 | 硬编码 B(up)/In2(dn) | **按带分层：dn→B.Cu，up→In6.Cu**；run→In2.Cu |
| LAYER_PALETTE | F/In2/B | **F/In2/In6/B** |
| 净距度量 | same-layer 交叉 + via-via | **+ 完整净距套件**（track-track 0.38 / via-track 0.4525 / via-via 0.525，A-CN.9） |

## 2. 实测（完整净距口径；`--out /tmp`，canonical 未动）
| 指标 | CN.25（旧口径） | CN.26（完整口径） |
|---|---|---|
| same_layer_crossings | 0（旧，未含净距） | **0** |
| R1 赋位 | 32/32 | **32/32** |
| R2/R3 | 72/72 | **72/72** |
| 完整净距违例 (tt/vt/vv) | 未度量（L5 才暴露） | **12 / 27 / 0 = 39** |
| verdict | FEASIBLE_ALL（旧口径） | **UPSTREAM_CHANGE_REQUEST**（诚实；A-CN.9 FAIL） |

**结论**：LID.1 派生 8L 把**同层交叉 264→0**、**R1 29→32**（层资源不再是瓶颈）；
残余 **39 条完整净距违例**集中在 **chip 侧 F.Cu breakout / 连接器 F.Cu landing**（局部 fanout 微几何），
非层数问题。域件升 v1.3（min+max 实现）已把 via-via 3→0、tt 13→12。

## 3. 残余根因（已定位）
- 残余 `tt`（如 `PCIE_DN2/input ↔ PCIE_UP2/out_J2 @0.15`）源于 **chip 4 行相邻行的 pad 在 x 上差 0.15mm**，
  而 R1 的 `_key` 优先「via x=pad x」→ 竖直 breakout 仅 0.15mm 间距 < 0.38。
- `vt` 同类（via 落点贴近邻网 track）。
- 需在 R1 候选键中加入**净距感知**（令 breakout 以 ≥0.38 分离；允许对角/让位），保持 0 交叉 + 32/32。

## 4. 产物 / 指纹
- 引擎 `tools/p3_v57_w3_constructive.py` rev **W3-CN.26**（AST 0 while / 0 enumerate）。
- 层意图 `m13_v57_layer_intent_rev5.json`（派生，非工单）。
- 域件 `m13_v57_f13_r1_pair_coupling_v1_3.json`（F13-R1PAIR.5，min+max；producer `p3_v57_f13_pair_coupling_r2_v3.py`）。
- 四源 MATCH；canonical 未改；探针临时物 /tmp。

## 5. 下一步（同波，无需 owner）
在 R1 候选键中加入净距感知（breakout/via 与已放置的 ≥0.38/0.4525），使 A-CN.9 残余→0；
达 FEASIBLE_ALL 后原子重发射 landing（F-12）→ W4→L4→L5 重签 G7。
