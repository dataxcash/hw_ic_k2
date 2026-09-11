# CO-22 — 【L2】lane 平面重整**部分落地**（W3-CN.36，DFM 91→88）+ 板边带**标定更正**

> 2026-09-12｜裁判：ARCHER（L2：走廊分配/过孔策略/等长，自裁）｜引擎 rev **W3-CN.36**｜ALLOC.3 `238eb812a05eeac6`

## 0. 本周期落地
1. **`CO16-ALLOC.3`**：西 `WLO 33.3→33.65`；东 `STEP 1.46→1.449` + 平面平移 `EDELTA=-0.15`（探针新旋钮）；`FANY_J3=34.5,51.5` 板内保持。
   探针 **32/32** + `p3_v57_co11_placement_verify.py` **320/320 0 违规 PASS**（`m13_v57_co22_placement_verification.json`）。
2. **引擎 W3-CN.36**：FEASIBLE_ALL，certs=0，crossings 0/0，A-CN.9 0/0/0，320 via，max|skew| 0.00306mm；
   新增 **CO-22 板边带约束**：蛇形顶点 `lane_y±A ∈ [LANE_Y_LO, LANE_Y_HI]`，且鼓出方向不得指向越界侧。
3. **G4/G5/G6 PASS**；**G7 SI PASS（skew 0.0031）/ DFM FAIL new=88**（91→88；`copper_edge 14→12`）。
4. **L4-E 判据修正**：pcbnew 以 nm 存盘，浮点往返有 ~1e-5mm 噪声 ⇒ 两侧统一 **0.1µm** 粒度比对（原 5 位小数在 `.515` 半值处不稳定）。修正后 L4-A..E viol=0。

## 1. 标定更正（关键）
板边 **Edge.Cuts 实线在 y=33.0 / 79.0**（`board_bbox=y[32.95,79.05]` 含线宽/其余段 ⇒ 偏宽 0.05）。
⇒ lane 中心真带 = **[33.0+0.3+0.1025, 79.0−0.3−0.1025] = [33.4025, 78.5975]**（此前误用 bbox ⇒ 带偏宽 0.05/侧）。
**实测**：真带下 `STEP×EDELTA` 细扫（1.444..1.455 × −0.18..+0.22，order=engine/laneidx/rev/fewest）
**无 32/32 配置**（最好 31/32）；满足真带的越界配置仍是 32/32。
⇒ 真带 ∧ 冻结候选行集 ∧ 现东侧 stub/landing 几何 **不可同时满足**。
残留 `copper_edge 12` = 西最低 lane 33.4（差 0.0025）+ 东 top 78.619（超 0.0215）。

## 2. 下一步（L2；已收敛为单一选择题）
东侧：(a) lane 带与 **J2 stub/landing y 同批平移**（保 stub 长度与交叉关系）；或 (b) **东侧 lane 索引置换**（按页 x 跨度排序）；
随后 `WLO≥33.71`（西最低 ≥33.41）一并落地 ⇒ 目标 `copper_edge → 0`。
另：`hole_to_hole 3`（同网钻孔距 `|lane_y−via1_y|≥0.4495`）在 (a)/(b) 的新平面上加 `CO10_HOLE_GAP=0.4495` 一并解。
`shorting 15 + mask 42 + clearance 16` = 既有 `PCIE_REFCLK0/1` 路线（独立变更单）。

## 3. 红线
冻结四源原件未动；零坐标搜索（AST while=0）；未放宽净距/等长阈值；无 partial pass/伪造 sign-off。
