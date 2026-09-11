# CO-43 — 实施记录：远端（J3/J4）接入形态落地（带内接入）→ DFM 54→38

> 2026-09-12｜性质：**L2 实施**（依 CO-42 `8c725a16c263e954` 裁定）｜引擎 rev **W3-CN.39**（不 bump：远端为同一 rev 的补全）
> 图纸 canonical `m13_v57_w3_joint_assignment.json` `466da0c9a0def536`

## 1. 改动（引擎 `tools/p3_v57_w3_constructive.py`）
新增 `_far_row_span()`（从 manifest 锚点闭式取远端两排 pad 行 y）+ `refclk_far_transit()`（远端接入），并在 `refclk_place()` 中以它替换原「直线入 pad」的末段：
1. **抬升列** `x_j` = max(manifest 已引用 pad 东端 + 0.5, witness `west_rise_in_corridor.x_centre_range[0]=65.517`) 向上取整到 0.05 栅格 ⇒ **65.55 / 66.05**（东于 A 排 pad 场，且落在 witness 认证的自由抬升带内）；
2. **带内两线** line_a = 行对自由带下界 + 0.28、line_b = line_a + 0.38（J3：44.1575 / 44.5375；J4：62.3575 / 62.7375）；
3. **分配规则（2 选 1 闭式判定）**：far-pad x 较小的极性走 line_a 并取更东抬升列；函数内含交叉判定（水平段×竖直段相交）自检，若候选 1 相交而候选 2 不相交则翻转为候选 2；
4. **垂直接入**各焊盘 x（J3 A11 58.9 / A12 58.3；J4 A11 60.1 / A12 60.7）。

**已修的两处实现缺陷（记录在案）**：① 初版把 line_a/line_b 的远近标签按目标行高低分支写反 ⇒ J3 会嵌套相交（引擎交叉指标不覆盖 REFCLK，故只有实跑 DRC 才暴露）；② 初版抬升列只由 manifest 已引用 pad 推得（64.8，落在 A 排内）⇒ 改用 witness 认证的自由抬升列。

## 2. 门禁实测
| 门 | 结果 |
|---|---|
| W3-CN.39（引擎） | **FEASIBLE_ALL**；A-CN.1..9 全 PASS；crossings 0/0；work 546/546；sha `466da0c9a0def536` |
| L4（构造+验证） | **PASS**（L4-A..E viol 0；segs 2419、vias 252 不变） |
| L5 | FAB ok；SI **PASS**（skew 0.0031）；DFM **new 54 → 38**（`solder_mask_bridge 18`（54 态为 36）、`shorting_items 7`（5）、`clearance 8`、`tracks_crossing 5`） |

## 3. 残余 38 的分布（明细件 `m13_v57_co43_refclk_drc_after.json` `be10106d9173f4e8`（CO-41 件为 `d720cc53ad390c7c`，同口径））
| 归属 | 数 | 内容 |
|---|---|---|
| 远端 J3 | 12 | `mask_bridge` 10（A1..A11）+ `shorting` 1（A1[GND]）+ 1 |
| 远端 J4 | 8 | `mask_bridge` 7（A13..A19）+ `shorting` 1（A13） |
| 西侧/走廊 | 16 | REFCLK vs `DN_OUT*_MCIO` 交叉/短路、`C82[P3V3]`、P/N 对内互距、N via#2 vs P 轨 |
| J2 pad 场 | 2 | P 侧 0.19mm jog vs GND pad 9/27 |
**诊断要点（下一步的起点）**：残余 J3/J4 项的 `items[].pos` 报的是**轨道锚点**（`(82.35,46.09)` / `(82.35,63.47)`，即西走廊端点）与**焊盘中心**，并非违规点坐标 ⇒ 需用 `kicad-cli` 的完整报告（含 violation 坐标）或对轨道逐段做 N 点采样定位；**不得**据此盲改几何。

## 4. 下一步（L2）
① 用完整 violation 坐标（非 item 锚点）定位 J3/J4 残余 20 条的真实违规段；② 处理对内间距（0.38→≥0.45，须配 witness v2 keepout 校正）以消 N-via-vs-P 与对内互距；③ J2 P 侧 jog=0；④ `C82[P3V3]` 与 REFCLK1_N 的落位/净距；⑤ 重跑 G4→G7 验收 `new → 0`。
