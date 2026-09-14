# DFM 逐项判定 — 交付板 vs **JLC HDI 通道**（DIR-14 / 工艺 A 冻结）

> 复现：`python3 tools/p3_v57_co146_jlc_dfm_hdi_report.py`｜板 `d4e81f647be7f980`｜判据值锚 = pinned 抓取件 + 已裁定件

**verdict = PASS_HDI**｜17 项：**16 PASS + 1 ACCEPT + 0 FAIL**｜前置 P0..P3 = [True, True, True, True]

| 项 | JLC 限（标准页） | 本板实测 | 机器(标准通道) | **HDI 通道** | 依据 |
|---|---|---|---|---|---|
| 板尺寸 | ≤656×586mm 且 ≥3×3mm | 120.1×46.1mm | PASS | **PASS** | 沿用机器实测（通道无关） |
| 层数 | 1–32 层（阻抗控制支持 4/6/8/10/12/32） | 8 层 | PASS | **PASS** | 沿用机器实测（通道无关） |
| 外层铜厚 | 1 oz / 2 oz | 1 oz（SPEC stackup / 监理定值） | PASS | **PASS** | 沿用机器实测（通道无关） |
| 内层铜厚 | 0.5 oz / 1 oz / 2 oz | 0.5 oz（SPEC stackup / JLC 默认） | PASS | **PASS** | 沿用机器实测（通道无关） |
| 成品板厚 | 1.6mm ±10% | 1.6mm（JLC08161H） | PASS | **PASS** | 沿用机器实测（通道无关） |
| 最小线宽 | ≥0.09mm (3.5mil) | 0.16mm | PASS | **PASS** | 沿用机器实测（通道无关） |
| 最小线距（域外，netclass 0.1/0.175/0.2 全 ≥3.5mil） | ≥0.09mm | JLC 限 DRC clearance 违规 = 0 | PASS | **PASS** | 沿用机器实测（通道无关） |
| 最小过孔孔壁 | ≥0.15mm（本板按 JLC 建议值 ≥0.2mm 判） | 0.2mm | PASS | **PASS** | 沿用机器实测（通道无关） |
| 最小过孔盘径 | ≥0.25mm | 0.35mm | PASS | **PASS** | 沿用机器实测（通道无关） |
| 过孔环宽（单边） | 盘径 ≥ 孔径+0.15mm（⇒ 单边 ≥0.075mm） | 0.075mm | PASS | **PASS** | 沿用机器实测（通道无关） |
| 过孔孔到孔 | ≥0.2mm | 0.25mm | PASS | **PASS** | 沿用机器实测（通道无关） |
| NPTH 最小孔径 | ≥0.5mm | Nonemm（[]） | PASS | **PASS** | 沿用机器实测（通道无关） |
| 铜到板边 | ≥0.2mm | 板规 min_copper_edge_clearance=0.30mm；JLC 限 DRC copper_edge_clearance 违规 = 0 | PASS | **PASS** | 沿用机器实测（通道无关） |
| 阻焊桥 / 阻焊-铜净距 | 桥 ≥0.1mm；开窗到邻近铜 ≥0.09mm | JLC 限 DRC solder_mask_bridge 违规 = 1 | FAIL | **ACCEPT_L2_WITH_FAB_REVIEW** | 既有 L2 裁定（CO-147 R3）：随板厂工程评审提交，不触铜几何（P3） |
| 表面处理 | 6 层及以上不支持 HASL ⇒ 须 ENIG | 沉金 ENIG | PASS | **PASS** | 沿用机器实测（通道无关） |
| 阻抗控制 | 支持层数 4/6/8/10/12/.../32，公差 ±10% | 8 层 + 85Ω±10%（见 CO-146 阻抗表） | PASS | **PASS** | 沿用机器实测（通道无关） |
| **过孔类型（盲/埋孔）** | **不支持盲/埋孔（仅通孔）** | **非通孔 220/493 支**：F.Cu->In2.Cu|BLIND_BURIED=92；F.Cu->In5.Cu|BLIND_BURIED=8；In2.Cu->In5.Cu|BLIND_BURIED=88；In5.Cu->B.Cu|BLIND_BURIED=32 | FAIL | **PASS** | HDI/advanced 通道支持盲埋孔（抓取件归一原文锚；P2） |

> `ACCEPT` = 已由 L2 裁定接受并随单提交板厂工程评审（**非** PASS，**非**静默通过）；兜底修法已预先授权（见裁定件）。
> FAIL 项 = 0 ⇒ 可送样。原始机器实测见包内 `06_rulings/m13_v57_co146_jlc_dfm_gate.json`（sha16 `0f548bf44d041512`）。
