# CO-146 卡 · DFM 对照 JLC 8 层能力（监理指令 #10 动作 4）

- 板：`k2_v4_8L.l4.kicad_pcb` `d4e81f647be7f980`｜判据源：https://jlcpcb.com/capabilities/pcb-capabilities（2026-09-12 抓取）
- as-designed DRC：**42** {'lib_footprint_issues': 12, 'lib_footprint_mismatch': 29, 'silk_edge_clearance': 1}（unconnected 178）
- JLC 下限 DRC：**43** {'lib_footprint_issues': 12, 'lib_footprint_mismatch': 29, 'silk_edge_clearance': 1, 'solder_mask_bridge': 1}
- **verdict = FAIL**；FAIL 项：['阻焊桥 / 阻焊-铜净距', '**过孔类型（盲/埋孔）**']

| # | 项 | JLC 限 | 实测 | 判 |
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
| 12 | NPTH 最小孔径 | ≥0.5mm | Nonemm（[]） | **PASS** |
| 13 | 铜到板边 | ≥0.2mm | 板规 min_copper_edge_clearance=0.30mm；JLC 限 DRC copper_edge_clearance 违规 = 0 | **PASS** |
| 14 | 阻焊桥 / 阻焊-铜净距 | 桥 ≥0.1mm；开窗到邻近铜 ≥0.09mm | JLC 限 DRC solder_mask_bridge 违规 = 1 | **FAIL** |
| 15 | 表面处理 | 6 层及以上不支持 HASL ⇒ 须 ENIG | 沉金 ENIG | **PASS** |
| 16 | 阻抗控制 | 支持层数 4/6/8/10/12/.../32，公差 ±10% | 8 层 + 85Ω±10%（见 CO-146 阻抗表） | **PASS** |
| 17 | **过孔类型（盲/埋孔）** | **不支持盲/埋孔（仅通孔）** | **非通孔 220/493 支**：F.Cu->In2.Cu|BLIND_BURIED=92；F.Cu->In5.Cu|BLIND_BURIED=8；In2.Cu->In5.Cu|BLIND_BURIED=88；In5.Cu->B.Cu|BLIND_BURIED=32 | **FAIL** |

## 牙齿
- T1 线宽限抬到 0.5mm ⇒ track_width 违规 199（>0 ok=True）
- T2 过孔类型项必须 FAIL：ok=True
- T3 板规铜-板边值须由冻结 drc_rules 派生（0.30mm）：ok=True
- T4 能力表引证逐条绑定抓取件（anchor 原文子串 + 非原文显式标注）：ok=True
- T5 引证判据灵敏度（篡改 anchor 即判不通过）：ok=True
- T6 能力表**值**可由抓取件原文抽取核验（29 捕获组 ↔ 声明值）：ok=True
- T7 值绑定灵敏度（篡改期望值即判不通过）：ok=True
- T8 逐项限值须由能力表派生（13 扰动情形）：ok=True

