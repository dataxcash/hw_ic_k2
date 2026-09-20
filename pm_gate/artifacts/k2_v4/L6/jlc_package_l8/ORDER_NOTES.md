# JLC（嘉立创）8 层打样**制造备注** — k2_v4_8L.l8

> 生成：tools/k2_p5_jlc_package_l8_v1.py｜受审板 `7a5c89913d6e5d0a`｜SPEC rev-53｜判据锚 rev=6
> 定值来源：监理指令 #10 定值表 + **owner #14 工艺冻结 A**（JLC HDI 盲埋孔 ≥2 阶）

## 1. 制造参数
| 项 | 值 |
|---|---|
| 层数 | 8（F/In1..In6/B） |
| 叠层 | **JLC08161H**（南亚 NP-155F）；成品厚 1.6mm ±10% |
| 铜厚 | 外层 1oz / 内层 0.5oz |
| 尺寸 | 120.1 × 46.1 mm |
| 阻抗 | **85Ω 差分 ±10%**（下单勾选「阻抗控制」；见 04_impedance/） |
| 表面处理 | 沉金 ENIG（JLC：≥6 层不支持 HASL） |
| 工艺通道 | **A：JLC HDI 盲埋孔（阶数 ≥2）** |
| 文件 | Gerber（01_）+ Excellon 钻孔（02_，含 HDI 盲埋孔分对）+ HDI 叠层/阶数图（03_）+ 阻抗表（04_）+ 本备注 + 随单裁定（06_）+ 验证件（07_） |

## 2. HDI 事实（as-built 普查，754 孔）
- 过孔 734 支，其中 **非通孔 455 支（62.0%）**：
- `F.Cu->B.Cu|THROUGH` = 279
- `F.Cu->In1.Cu|BLIND_BURIED` = 171
- `F.Cu->In2.Cu|BLIND_BURIED` = 132
- `F.Cu->In4.Cu|BLIND_BURIED` = 4
- `F.Cu->In5.Cu|BLIND_BURIED` = 19
- `In2.Cu->In5.Cu|BLIND_BURIED` = 92
- `In5.Cu->B.Cu|BLIND_BURIED` = 37
- PTH 焊盘孔 = 16 个（0.8mm）；NPTH = 4 个（3.2mm 安装孔）
- 盲埋孔 ⇒ 需 **多次层压**（`In2.Cu->In5.Cu` 埋孔 = 3 次层压）⇒ 依 **HDI/advanced 通道**下单并走 **HDI DFM review**（承 owner #14①）。

## 3. DFM 逐项（对 JLC HDI 通道；机器实测）
**汇总：16 PASS / 1 ACCEPT / 0 FAIL**（逐项见 `06_rulings/jlc_dfm_hdi_l8.md`）。
- **ACCEPT（1 项）**：阻焊坝共 9 处 < 0.09mm（阈值扫描：4∈[0.05,0.06)·1∈[0.06,0.07)·4∈[0.08,0.09)）。JLC 能力表 0.10mm 系**最小可保证桥宽**（非必须存在桥）⇒ 板厂按「无阻焊坝」印制；承 CO-147 R3 先例 **ACCEPT 随单工程评审**；影响面 = 装配焊接注意，**不阻塞 Gerber 可制造性**。
  若板厂拒绝：回退修法**已实证** = `pad_to_mask_clearance` 0.05→0.02mm ⇒ 缺口 **9→0**（`07_verify/mask_accept_fix_proof.json`）；该修法属**改板** ⇒ 须另开 rev + 重跑全链（本次打样不做）。
- **过孔类型项**：标准通道页明文不支持盲埋孔，本板走 **HDI 通道 A** ⇒ 判 PASS（非缩口径：通道语义不同，owner #14 已冻结 A）。
- **阻抗几何（具名）**：F.Cu 最紧**真平行**耦合段净距 **0.2825mm < SPEC 窗下界 0.295mm（−4.24%）**（位点 `PCIE_UP3` 逃逸域）；线性化 ΔZ ≈ −0.84% ⇒ **仍落 85Ω±10%**。In2/In5 精确落窗（0.34–0.44mm）。B.Cu 无 as-built 耦合 run（SPEC 对称声明行）。详见 `04_impedance/`。

## 4. 系统级事项（非制造/非本单阻塞）
U6（DS320PR1601）热：定案 O2 = 30×30mm 铝散热片 + 界面垫 1.0℃/W + ~2m/s 风冷 ⇒ θJA_eff 11.0℃/W，四工况 Tj ≤117.0℃（限 120.0℃）全 PASS。**系统装配须按 O2 实施**。详见 `06_rulings/L2_RULING_u6_thermal_mitigation_v2.md`。

## 5. 已知板级事实（如实登记）
- DRC（在册 canonical）：违规 **167 全 warning** / error **0** / unconnected **0**；9 类全登记（`drc_warning_dispositions`）。
- 丝印图形级 warning（silk_over_copper 37 / silk_overlap 15 / silk_edge_clearance 2）：按板厂惯例对焊盘上丝印**自动裁剪**，不影响制造。
- 排针 J6/J9/J11/J12/J13 为无焊盘占位（netlist 骨架）—— 3D 预览属 OUT #5 族（证据层，不阻塞可制造性）。
- **正面丝印越出板框 4 处**（H4 +1.848mm · R41 +1.798mm · D2 +1.198mm · C87 +0.798mm）：板厂按边框裁剪 ⇒ 该 4 个位号图例可能缺损（装饰/可追溯性，不影响制造）；**铜层越界 0**。见 `07_verify/silk_overhang.json`。
