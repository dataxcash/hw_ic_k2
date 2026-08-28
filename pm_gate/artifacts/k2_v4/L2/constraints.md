# L2 约束清单 constraints（2026-08-13）

> 宪法第四章 ②约束：每条带出处（工艺手册条款/规范章节）。约束是"手册说"，不是"我们认为"。

## 板厂工艺（JLC06161H-3313，出处：嘉立创 6 层板工艺极限表 + K2-worker-pcb-checklist.md）

- 线宽/线距 ≥ 0.09/0.10mm（出处：JLC06161H 极限工艺；checklist B 节）
- 过孔内径/外径 0.20/0.35mm，孔环 ≥0.075mm（出处：JLC 工艺极限；AGENTS.md 修正条款 1——0.15/0.30 亦可满足环宽）
- 板边铜 ≥0.30mm（出处：JLC 工艺；checklist A.3）
- M3 孔周围 3.0mm keepout（禁走线/过孔/铺铜）（出处：stackup-impedance-report.md）
- 板厚 1.6mm，6 层（出处：k2_v4.kicad_pcb general.thickness）
- **阻焊桥（solder mask dam）≥0.1mm；0.4mm pitch 及以下细脚距封装（WQFN64 等）由板厂惯例去桥处理**（出处：JLC 官方工艺能力 2026-05/06——LPI 绿油 min dam 0.1mm、支持 0.4mm pitch 及以下细脚距；JLC DFM 实测对 0.4mm QFN 移除 pad 间 mask，0.15mm 铜间隙远大于线距极限 0.10mm。2026-08-16 State 1 核对归档）

## 电气（PCIe Gen4 16GT/s，出处：PCIe CEM 规范 / ECO #12 裁定）

- 差分阻抗 85Ω ±10%（出处：PCIe CEM 4.0）
- 对内等长 <0.15mm（出处：ECO #12 / checklist B.5）
- 对间间距 ≥0.875mm = 5×线距，3W 原则（出处：PCB_DESIGN_RULES R3-2，2026-08-15 强条明确；checklist B.6 的 0.5 为旧口径）
- 18 对 PCIe 差分全 F.Cu 微带，零过孔（出处：ECO #12 Option B 裁定——零过孔消除残桩反射）
- REFCLK0/1 独立路由，不共网不交叉（出处：checklist B.3）
- AC 耦合焊盘下方 GND 挖空（出处：checklist B.7）

## 叠层与阻抗（出处：stackup-impedance-report.md + 6 项复核报告 #5）

- 结构：F.Cu 微带，参考 In1 GND，H≈0.1175mm（IPC-2141 近似）
- 计算基准：w=0.227/g=0.15 → 85.0Ω（网类 PCIe85）；备选 w=0.248/g=0.20 → 84.9Ω
- **警告**：JLC 官方 SI9000 模型 H1=5.0mil/Er1=4.3，IPC-2141 近似不可直接用，需重算（出处：复核报告 #5 / checklist D.1）
- 打样前强制项：板厂阻抗测试条（coupon）实测（出处：stackup-impedance-report.md）

## 结构层映射（出处：AGENTS.md 修正条款 4——PM 的 L2/L4=GND、L3/L5=电源 映射到真实 6 层）

| 层 | 分配 | 依据 |
|---|---|---|
| F.Cu | 高速 PCIe 差分（18 对）+ 逃逸 | ECO #12：微带参考 In1 |
| In1.Cu | GND 完整平面 | F.Cu 微带参考面（checklist C.1） |
| In2.Cu | 低速/边带路由（I2C/GPIO/PERST#） | AGENTS.md 修正条款 3：BcuRouter 语义 |
| In3.Cu | GND 完整平面 | checklist C.1 |
| In4.Cu | 电源分区（P3V3/P3V3_AUX/MCU_VDD） | checklist C.2（对应 PM 的 L3/L5 电源） |
| B.Cu | 低速边带 + 电源铺铜 | BcuRouter 语义 |

## 版本

- v1.0（2026-08-13，L2 G2.2 输入）
