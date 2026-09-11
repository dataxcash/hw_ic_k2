# CO-48 — 【L2/L3 自裁】L5 补齐 G7 评审记录产出（L5-G7.6：G7 PASS / new=0 / 在册 0 未连）

> 2026-09-12｜性质：**评审记录同步**（零几何改动、零判据放宽）｜无 L1 变更
> 前置：CO-47 `031fc91aa520cb92`（L5-DFM.4）｜触发：核实 L5 产出齐备性时发现 G7 记录陈旧。

## 1. 现象（两处不一致）
1. `tools/p3_v57_l5_signoff.py` 的 docstring 声明产出 `m13_v57_l5_g7_record.md`（G7 记录：verdict → 是否回上层），
   但 `main()` 只写 3 个 json —— **声明与实现不一致**。
2. 该 md 自 **CO-37（`3b2e00a`）** 起未再更新，内容仍为 **L5-G7.5 / 图纸 W3-CN.38 / DFM FAIL new=60**，并写「**G7 保持 OPEN**」；
   与当前实际（G7 PASS、DFM new=0、tag `k2-v57-g7-l5-pass` @ `b5afe47`）**直接矛盾**。
   违反宪法第七章第 2 条（里程碑评审报告须与裁决一致）与第五章可追溯性。

## 2. 修正
`main()` 现按**确定性文本**生成 `m13_v57_l5_g7_record.md`（revision **L5-G7.6**，每次 L5 重跑自动重生成）：
- §1 结论：`G7 PASS`（SI `skew 0.0031 ≤ 0.15`（34 页含 REFCLK）；DFM `new_total=0`；DFT 在册网 `0/68` 未连；
  EMC mask_bridge 0 / copper_edge 0；PI hole_clearance 0；**裁决：无需回上层**）；
- §2 量（8L）：copper 8 / tracks 2441 / vias 252（drill 0.2）/ 4 rule area / 在册网 68 / 全板未连 348 /
  baseline 42 = L4 42 / **new 0**；
- §3 判据（未放宽）：`.kicad_dru` 实现 SPEC `escape_transition_zone` 0.075 + **显式排除 `PCIE_REFCLK*`**；
- §4 独立复算（G5/G6 记录 sha + kicad-cli 命令）；
- §5 指纹（图纸/landing/G5/L4 construction/L4 validation/板/fab/dfm/si/dru + 冻结四源）。
- **不含墙钟时间** ⇒ 重跑幂等；日期/沿革由 git 与 CO-* 变更单承载。

## 3. 验证（实测）
- `../AppDir/usr/bin/python3.11 tools/p3_v57_l5_signoff.py` ⇒ 退出码 **0**；
  连跑两次，4 个产出（fab/dfm/si/g7 md）**逐字节一致**（幂等性实测）。
- 指纹：l5_signoff `bd025762e44396b0`｜G7 记录 `2d4299a242742aa1`（L5-G7.6）；fab `12d1f3944944550a`、dfm `f5a691f4cda234df`、si `a3187aed93c48b6b` 均未变。

## 4. 未改物 / 红线
零几何改动：drawing `dfa1d7c4a811b0da`、板 `4d36212f6492262b`；G4/G5/G6 未触碰；四冻结源 **4/4 MATCH**；无搜索/迭代。
W3 boundary v1.17 仍有效（其引用的 dfm/board sha 未变），故不 bump。
