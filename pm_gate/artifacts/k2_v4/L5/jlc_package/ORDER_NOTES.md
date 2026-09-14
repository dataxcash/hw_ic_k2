# JLC（嘉立创）8 层打样**制造备注** — k2_v4_8L.l4

> 生成：tools/p3_v57_co146_jlc_fab_package.py｜板 `d4e81f647be7f980`｜SPEC rev-19
> 定值来源：监理指令 #10「JLC 8 层打样就绪」定值表（叠层/铜厚/阻抗/表面处理/压降/环境）

## 1. 制造参数（监理定值）
| 项 | 值 |
|---|---|
| 层数 | 8 |
| 叠层 | **JLC08161H**（南亚 NP-155F） |
| 成品厚 | 1.6 mm（公差 ±10%） |
| 铜厚 | 外层 1oz / 内层 0.5oz |
| 尺寸 | 120.1 × 46.1 mm |
| 阻抗 | **85Ω 差分 ±10%（商务下单时勾选「阻抗控制」）** |
| 表面处理 | 沉金 ENIG |
| 工艺通道 | **A：JLC HDI 盲埋孔（叠层阶数 ≥2）—— 监理指令 #14 owner 冻结** |
| 文件 | Gerber RS-274X（01_）+ Excellon 钻孔（02_：含 4 类盲埋孔分片 .drl + drill map SVG）+ **HDI 叠层/阶数图（03_）** + 阻抗表（04_）+ 本制造备注 + 随单裁定（06_） |

## 2. 制造通道（**监理指令 #14：工艺冻结为 A**）
**通道 = JLC HDI 盲埋孔（advanced/HDI 专属通道），叠层阶数 ≥2。** 本板 220/493 支为**非通孔**
（`F.Cu→In2.Cu` 92、`In2.Cu→In5.Cu` 88（埋孔）、`In5.Cu→B.Cu` 32、`F.Cu→In5.Cu` 8）；`F.Cu→B.Cu` 通孔 273 支。
其中 `In2.Cu→In5.Cu`（埋孔）需 **3 次层压**（阶数 ≥2）；标准通道口径下亦不满足残桩 <0.15mm（`In2.Cu→In5.Cu` 残桩 0.3664mm）——A 冻结后该点由 HDI 通道消解。
- **标准通道（仅通孔）不使用**；其能力页明文 *"Blind/Buried Vias Not supported"* 与 *Backdrill* 支持，均与 A 冻结后之口径无关。
- JLC 页 FAQ 原文 *"Advanced options such as blind/buried vias, HDI (laser vias), … typically require DFM review and may increase both cost and production time."* ⇒ HDI/advanced **支持**盲埋孔，须 **HDI DFM review**。
- 路径 A/B/C 之对比已成历史：**A 由 owner（监理指令 #14）冻结**，B/C 闭项。定案见 `06_rulings/L2_RULING_process_route_A_frozen_hdi_v1.md`。
- 报价 / 交期 / 下单 / 凭据 = **商务范畴，非 ENG 任务**（**监理指令 #15**）：不作 ENG 交付项、不作 ENG 阻塞项（判据件单价参数保持 null）。
- DFM 逐项对 HDI 通道之日判见 `06_rulings/` 同包之 `m13_v57_co146_jlc_dfm_gate.json` 与本备注 §3/§4。

> **监理指令 #14 终止项**：不再新增检查齿（t45+）；「每轮复评上轮 CO」之复评债机制**本轮终止**；残余复评债 = **owner 豁免（关闭）**，不阻塞交付。**完工定义（#15）= Gerber 包齐**（本包 01_/02_/03_/04_ + `MANIFEST.json`；逐文件 sha256 在案）。

## 3. 板级 DFM 项（CO-147 L2 裁定 R3，随板厂评审提交）
**阻焊开窗-邻铜净距 1 处**：`R3.pad2`(`PWR_BTN_ISO`) 开窗缘 ↔ `PCIE_UP3_N` 铜缘 = **0.0695mm** < JLC 0.09mm
（欠 0.0205mm）。裁定 = **ACCEPT_L2_WITH_FAB_REVIEW**（并入同一工程评审；不触铜几何、不改板）。
若板厂拒绝 ⇒ 回退最小修法：R3 开窗 0.05→0.02mm（净距 → 0.0995 ≥ 0.09）+ G4 全链重基线。

## 4. 其余 DFM 项（对照 JLC 8 层能力，实测 PASS）
最小线宽 0.16mm(≥3.5mil)；过孔 0.2/0.35mm（孔 ≥0.15、盘径 ≥0.25、环宽 0.075=JLC「盘径 ≥ 孔径+0.15」）；
孔到孔 0.25mm(≥0.2)；板规铜-板边 0.30mm(≥0.2)；层数/尺寸/铜厚/板厚/表面处理均落 JLC 能力。
**逐项（对 JLC HDI 通道）见包内 `06_rulings/m13_v57_co146_jlc_dfm_hdi.json`**（`PASS_HDI`：16 PASS + 1 ACCEPT（§3）+ 0 FAIL；`ACCEPT` = 已裁定接受并随单评审，非 PASS、非静默）。底层机器实测（标准通道口径）见 `06_rulings/m13_v57_co146_jlc_dfm_gate.json`。

## 5. 阻抗
85Ω 差分两套独立闭式模型（IPC-2141 族 / Hammerstad–Jensen+Cohn）均落 ±10%（as-built 对内净距），
设计名义最宽间距下有 1 项模型偏离观察值（M2(HJ) 相对目标 **+11.7%**；模型间 spread ≈4.8%），已列制造备注：
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

## 8. 制造参数清单（JLC HDI 通道；供 fab / 商务）
| 字段 | 值 |
|---|---|
| 板子类型 | 8 层 **HDI（盲埋孔）** |
| 叠层 | JLC08161H（南亚 NP-155F）；成品厚 1.6mm ±10% |
| 铜厚 | 外层 1oz / 内层 0.5oz |
| 尺寸 | 120.1 × 46.1 mm |
| 盲埋孔阶数 | **≥2 阶**（设计需 3 次层压：`In2.Cu→In5.Cu`） |
| 过孔 | 0.2mm 孔 / 0.35mm 盘（环宽 0.075mm）；孔到孔 0.25mm |
| 最小线宽 / 线距 | 0.16mm / ≥0.09mm（JLC 限 DRC clearance 违规 = 0） |
| 阻抗 | 勾选「**阻抗控制**」；**85Ω 差分 ±10%**（见 `04_impedance/`；请覆盖最宽对内间距 0.6mm 中心几何） |
| 表面处理 | 沉金 ENIG |
| 文件 | Gerber（`01_gerber_rs274x/`）+ 钻孔（`02_drill_excellon/`）+ **HDI 叠层/阶数图（`03_stackup/`）** + 阻抗表（`04_impedance/`） |
| 工程评审 | ① 阻焊开窗 1 处（`R3.pad2` ↔ `PCIE_UP3_N` = 0.0695mm < 0.09mm，见 §3）；② HDI 阶数/孔径/介质厚限值确认 |
