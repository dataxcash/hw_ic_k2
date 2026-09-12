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
| 文件 | Gerber RS-274X（01_）+ Excellon 钻孔（02_）+ 本叠层图（03_）+ 阻抗表（04_） |

## 2. 下单渠道（CO-147 L2 裁定 R1，生效）
本板 220/493 支过孔为**非通孔**（`F.Cu→In2.Cu` 92、`In2.Cu→In5.Cu` 88（埋孔）、
`In5.Cu→B.Cu` 32、`F.Cu→In5.Cu` 8）；JLC 公布能力页明写 *"Blind/Buried Vias Not supported … only make through holes"*，
FAQ 将 blind/buried 列为 **advanced options（须 DFM review，成本/交期上升）**。

⇒ **下单走 JLC advanced / 盲埋孔通道**（L2 自裁 = 过孔策略），随单提交：本备注 + 叠层图(03_) + 阻抗表(04_) +
L2 裁定件 `L2_RULING_via_channel_and_interpair_domain_v1.md`；接受其 DFM review 与重报价。
若只接受标准通孔工艺 ⇒ 须重开 W3 **通孔化派生**（独立 L2 候选；前置 = 引擎通孔模型 + 可行性证明；
原地通孔化实测 111 项 shorting_items ⇒ 不可直接降级）。

## 3. 板级 DFM 项（CO-147 L2 裁定 R3，随板厂评审提交）
**阻焊开窗-邻铜净距 1 处**：`R3.pad2`(`PWR_BTN_ISO`) 开窗缘 ↔ `PCIE_UP3_N` 铜缘 = **0.0695mm** < JLC 0.09mm
（欠 0.0205mm）。裁定 = **ACCEPT_L2_WITH_FAB_REVIEW**（并入同一工程评审；不触铜几何、不改板）。
若板厂拒绝 ⇒ 回退最小修法：R3 开窗 0.05→0.02mm（净距 → 0.0995 ≥ 0.09）+ G4 全链重基线。

## 4. 其余 DFM 项（对照 JLC 8 层能力，实测 PASS）
最小线宽 0.16mm(≥3.5mil)；过孔 0.2/0.35mm（孔 ≥0.15、盘径 ≥0.25、环宽 0.075=JLC「盘径 ≥ 孔径+0.15」）；
孔到孔 0.25mm(≥0.2)；板规铜-板边 0.30mm(≥0.2)；层数/尺寸/铜厚/板厚/表面处理均落 JLC 能力。
逐项见 `m13_v57_co146_jlc_dfm_gate.json`。

## 5. 阻抗
85Ω 差分两套独立闭式模型（IPC-2141 族 / Hammerstad–Jensen+Cohn）均落 ±10%（as-built 对内净距），
设计名义最宽间距下有 1 项 model-spread 观察值（+11.6%），已列下单备注：
**请 JLC 阻抗表覆盖最宽对内间距（0.6mm 中心）的几何**。终判 = JLC 阻抗控制服务。
见 04_impedance/。

## 6. 系统级事项（非制造/非本单阻塞，但影响可用性）
**U6（DS320PR1601）热超限（CO-148）**：手册 PACT 4.7–7.0W / θJA(high-K) 17.4°C/W / Tj 上限 120°C；
按监理定值 40°C 自然对流 ⇒ Tj 121.8–161.8°C **全档超限**（ψJB+h 交叉路线 173.6°C）。
⇒ 须（a）系统强制风冷/顶部散热片 或（b）环境降额，并在下一轮几何修订中补强 U6 域 GND via 阵列。
详见 `L2/L2_RULING_u6_thermal_v1.md` 与登记簿 HIGH 项。本板仍建议打样（散热路径实证需要实板）。

## 7. 已知板级非 DFM 事实（如实登记，非本单阻塞）
- 本板无 PTH/NPTH 焊盘：`J6/J9/J11/J12/J13` 为无焊盘占位（netlist 骨架），板上无安装孔。
- DRC（as-designed，含逃逸域 dru）：42 项，全部为 `lib_footprint_*`(41) + `silk_edge_clearance`(1)，无铜几何违规。
