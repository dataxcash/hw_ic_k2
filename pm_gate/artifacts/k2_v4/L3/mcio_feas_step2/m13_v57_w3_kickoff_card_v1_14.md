# m13 v57 — W3 开工卡 **v1.14**（W3-C13：owner 授权 F-13 重发射 + §R-37 构造收口）

> 版本 bump（v1–v1.13 不动）。**授权来源：owner（经监督工单 W3-C13）**——D1/D0 溯源据此标注为 owner。
> 边界（不可越）：不改冻结四源（SPEC/manifest/PCB/rules）；不改层叠/层用途（In4 仍电源平面，In2/B 为信号层）；
> 每线 via ≤2；所有候选位仍逐点过 DRC 谓词（异球铜 + clearance 0.175/0.2 + via-via 0.525）。

## R-49（F-13 域重发射，合法最小项）

- 新 producer `tools/p3_v57_s1_r1_via_verdict_r2.py`；扫描窗口 `WIN ±1.5mm → ±2.5mm`；
  新工件 `m13_v57_s1_r1_via_verdict_r2.json`（`f2e26325…`），**旧件 `m13_v57_s1_r1_via_verdict.json`（`2a3c8cf4…`）不动**。
- 实测：32/32 ESCAPABLE；参数口径不变（`clr 0.2 / via_od 0.35 / via_via 0.525`）；候选数显著增加。

## R-50（构造方法 = §R-37，W3-C11 已验证方向）

每 `(frame, polarity)` 于常数候选行集（冻结 0.05 域）**单遍 argmin（R-40 口径：固定键、固定 tie-break、
无试错/回溯/迭代修正）**选共线行；行承载列单遍 argmin 吸附 + **前缀单调 x** + **极性同侧**；
R1.5 **直线段**（零折角）；层 = **反演图 2 色**（`up→In2.Cu`, `dn→B.Cu`；实测反演边仅 `(J3dn,J4up)/(J4dn,J4up)`）。

## R-51（验收目标）

`same_layer_crossings = 0 ∧ R1 32/32 ∧ R2/R3(72/72)/REFCLK 不劣化` ⇒ `FEASIBLE_ALL`
⇒ **原子重发射** `m13_v57_w3_chip_landing_rows.json`（F-12，同提交同 SHA 链）+ 34 页图纸 + boundary 版本化 + 解封 W4。

End of W3-C13 v1.14.
