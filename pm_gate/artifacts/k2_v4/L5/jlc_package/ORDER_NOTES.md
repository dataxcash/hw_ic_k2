# JLC（嘉立创）8 层打样下单备注 — k2_v4_8L.l4

> 生成：tools/p3_v57_co146_jlc_fab_package.py｜板 `d4e81f647be7f980`｜SPEC rev-19
> 定值来源：监理指令 #10「JLC 8 层打样就绪」定值表（叠层/铜厚/阻抗/表面处理/压降/环境）

## 1. 下单参数（监理定值）
| 项 | 值 |
|---|---|
| 层数 | 8 |
| 叠层 | **JLC08161H**（南亚 NP-155F） |
| 成品厚 | 1.6 mm（公差 ±10%） |
| 铜厚 | 外层 1oz / 内层 0.5oz |
| 尺寸 | 120.1 × 46.1 mm |
| 阻抗 | **85Ω 差分 ±10%，下单勾选「阻抗控制」** |
| 表面处理 | 沉金 ENIG |
| 文件 | Gerber RS-274X（01_）+ Excellon 钻孔（02_）+ **背钻钻孔文件** + 本叠层图（03_）+ 阻抗表（04_） |

## 2. 下单渠道（CO-204 L2 裁定 → **CO-206 §0 更正**）
**标准通道不支持盲/埋孔**：JLC 能力页明文 *"Blind/Buried Vias Not supported … only make through holes"*；
同页明文 **Backdrill 支持**（4–32 层 / 板厚 ≥0.8mm / D 0.2–0.5mm / W = D+0.2mm / T ≥0.15mm / S ≥0.2mm，
anchor 逐条为抓取件归一原文子串）。

> ⚠️ **更正（CO-206 / 监理指令 #13）**：本段原写「⇒ **不存在**「JLC advanced / 盲埋孔通道」；该表述及据其之旧裁定**已撤销**」**有误，该表述已撤销**。
> 准确表述：**advanced 通道支持**盲/埋孔与 **HDI（激光孔）** —— 同页 FAQ 原文 *"Advanced options such as blind/buried vias,
> HDI (laser vias), … typically require DFM review and may increase both cost and production time."*
> ⇒ 「JLC 做不了」**不成立**；正确命题 =「**HDI 能做但贵，评估更便宜的路**」。
> 路径 A/B/C 对比与定案见 `06_rulings/L2_RULING_process_route_selection_v2.md`。

本板 220/493 支过孔为**非通孔**（`F.Cu→In2.Cu` 92、`In2.Cu→In5.Cu` 88（埋孔）、
`In5.Cu→B.Cu` 32、`F.Cu→In5.Cu` 8）⇒ **本包不可按「标准通道」下单**；
**打样路径（CO-206 定案）= A：JLC advanced/HDI 通道**（须 DFM review 与重报价；阶数/孔径限值待板厂确认）；
标准通道口径下既非可造、亦不满足残桩 <0.15mm（In2→In5 残桩 0.3664mm）。
闸 = `p3_v57_co204_fab_capability_binding_gate.py`（现行板对标准通道预期 FAIL；改挂 HDI 能力源后须重跑）。
随单文件（重派生后）：Gerber(01_) + 钻孔(02_) + **背钻钻孔文件** + 叠层图(03_) + 阻抗表(04_) + 本备注 + 散热要求。

## 3. 板级 DFM 项（CO-147 L2 裁定 R3，随板厂评审提交）
**阻焊开窗-邻铜净距 1 处**：`R3.pad2`(`PWR_BTN_ISO`) 开窗缘 ↔ `PCIE_UP3_N` 铜缘 = **0.0695mm** < JLC 0.09mm
（欠 0.0205mm）。裁定 = **ACCEPT_L2_WITH_FAB_REVIEW**（并入同一工程评审；不触铜几何、不改板）。
若板厂拒绝 ⇒ 回退最小修法：R3 开窗 0.05→0.02mm（净距 → 0.0995 ≥ 0.09）+ G4 全链重基线。

## 4. 其余 DFM 项（对照 JLC 8 层能力，实测 PASS）
最小线宽 0.16mm(≥3.5mil)；过孔 0.2/0.35mm（孔 ≥0.15、盘径 ≥0.25、环宽 0.075=JLC「盘径 ≥ 孔径+0.15」）；
孔到孔 0.25mm(≥0.2)；板规铜-板边 0.30mm(≥0.2)；层数/尺寸/铜厚/板厚/表面处理均落 JLC 能力。
逐项见包内 `06_rulings/m13_v57_co146_jlc_dfm_gate.json`。

## 5. 阻抗
85Ω 差分两套独立闭式模型（IPC-2141 族 / Hammerstad–Jensen+Cohn）均落 ±10%（as-built 对内净距），
设计名义最宽间距下有 1 项模型偏离观察值（M2(HJ) 相对目标 **+11.7%**；模型间 spread ≈4.8%），已列下单备注：
**请 JLC 阻抗表覆盖最宽对内间距（0.6mm 中心）的几何**。终判 = JLC 阻抗控制服务。
见 04_impedance/。

## 6. 系统级事项（非制造/非本单阻塞，但影响可用性）
**U6（DS320PR1601）热 — 问题定性（CO-148）+ 定案 O2（CO-204）**
- **问题**：手册 PACT 4.7–7.0W / θJA(high-K) 17.4°C/W / Tj 上限 120°C；按监理定值 40°C 自然对流 ⇒
  Tj 121.8–161.8°C **全档超限**（ψJB+h 交叉路线 173.6°C）。
- **定案（O2）**：**30×30mm 铝散热片 + 界面垫 1.0 ℃/W + ~2 m/s 风冷** ⇒ **θJA_eff = 11.0 ℃/W**；
  四工况 Tj = 91.7 / 106.0 / 103.8 / 117.0 ℃（限 120.0 ℃）**全部 PASS**（最重工况余量 3.0 ℃）。
- ⇒ **系统装配须按 O2 实施**（顶部散热 + 风冷）；**U6 域 GND via 阵列不在 rev-19 交付范围**，为**条件动作**（**以 CO-222 为准** / boundary §95）：**T1** 首件实测 `Tj(U6) > 117.0 ℃` 或未按 O2 实施 ⇒ 立即开新 rev，量化目标 `θJA_eff ≤ 9.5 ℃/W`；**T2** U6 域几何因他因修订 ⇒ 同 rev 一并补阵。
- 详见包内 `06_rulings/L2_RULING_u6_thermal_mitigation_v2.md`（**定案**；取代 v1.0 之「推荐/待定」口径）
  与 `06_rulings/L2_RULING_u6_thermal_v1.md`（问题定性）。登记簿该项 = **CLOSED**（CO-149 / CO-150 关闭）。
  本板仍建议打样（散热路径实证需要实板）。

## 7. 已知板级非 DFM 事实（如实登记，非本单阻塞）
- 本板无 PTH/NPTH 焊盘：`J6/J9/J11/J12/J13` 为无焊盘占位（netlist 骨架），板上无安装孔。
- DRC（as-designed，含逃逸域 dru）：42 项，全部为 `lib_footprint_*`(41) + `silk_edge_clearance`(1)，无铜几何违规。
