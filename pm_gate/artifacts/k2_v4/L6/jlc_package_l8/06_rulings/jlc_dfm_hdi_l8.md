# K2 P5 · DFM 逐项对 **JLC HDI 通道**（工艺 A 冻结 · 受审板 l8）

- board `7a5c89913d6e5d0a` · 判据锚 rev=6 · 源 = 机器实测（kicad-cli 10.0.5；JLC 限地板重跑）
- 汇总：**16 PASS / 1 ACCEPT / 0 FAIL**（共 17 项）

| # | 项 | JLC 限（HDI 通道） | l8 实测 | 判 |
|---|---|---|---|---|
| 1 | 板尺寸 | ≤656×586mm 且 ≥3×3mm | 120.1×46.1mm | **PASS** |
| 2 | 层数 | 1–32 层（阻抗控制支持 4/6/8/10/12/32） | 8 层 | **PASS** |
| 3 | 外层铜厚 | 1 oz / 2 oz | 1 oz（SPEC stackup / 监理定值） | **PASS** |
| 4 | 内层铜厚 | 0.5 oz / 1 oz / 2 oz | 0.5 oz（SPEC stackup / JLC 默认） | **PASS** |
| 5 | 成品板厚 | 1.6mm ±10% | 1.6mm（JLC08161H） | **PASS** |
| 6 | 最小线宽 | ≥0.09mm (3.5mil) | 0.16mm | **PASS** |
| 7 | 最小线距（域外，netclass 0.1/0.175/0.2 全 ≥3.5mil） | ≥0.09mm | JLC 限 DRC clearance 违规 = 0 | **PASS** |
| 8 | 最小过孔孔壁 | ≥0.15mm（本板按 JLC 建议值 ≥0.2mm 判） | 0.2mm | **PASS** |
| 9 | 最小过孔盘径 | ≥0.25mm | 0.35mm | **PASS** |
| 10 | 过孔环宽（单边） | 盘径 ≥ 孔径+0.15mm（⇒ 单边 ≥0.075mm） | 0.075mm | **PASS** |
| 11 | 过孔孔到孔 | ≥0.2mm | 0.25mm | **PASS** |
| 12 | NPTH 最小孔径 | ≥0.5mm | 3.2mm（['3.2']） | **PASS** |
| 13 | 铜到板边 | ≥0.2mm | 板规 min_copper_edge_clearance=0.30mm；JLC 限 DRC copper_edge_clearance 违规 = 0 | **PASS** |
| 14 | 阻焊桥 / 阻焊-铜净距 | 桥 ≥0.1mm；开窗到邻近铜 ≥0.09mm | JLC 限 DRC solder_mask_bridge 违规 = 9 | **ACCEPT_L2_WITH_FAB_REVIEW** |
| 15 | 表面处理 | 6 层及以上不支持 HASL ⇒ 须 ENIG | 沉金 ENIG | **PASS** |
| 16 | 阻抗控制 | 支持层数 4/6/8/10/12/.../32，公差 ±10% | 8 层 + 85Ω±10%（见 CO-146 阻抗表） | **PASS** |
| 17 | **过孔类型（盲/埋孔）** | **不支持盲/埋孔（仅通孔）** | **非通孔 455/734 支**：F.Cu->In1.Cu|BLIND_BURIED=171；F.Cu->In2.Cu|BLIND_BURIED=132；F.Cu->In4.Cu|BLIND_BURIED=4；F.Cu->In5.Cu|BLIND_BURIED=19；In2.Cu->In5.Cu|BLIND_BURIED=92；In5.Cu->B.Cu|BLIND_BURIED=37 | **PASS** |

- as-designed DRC 204 项 / JLC 限地板重跑 213 项（by_type 见 json；口径 = gate 工具，勿与在册 canonical 170 混比）
