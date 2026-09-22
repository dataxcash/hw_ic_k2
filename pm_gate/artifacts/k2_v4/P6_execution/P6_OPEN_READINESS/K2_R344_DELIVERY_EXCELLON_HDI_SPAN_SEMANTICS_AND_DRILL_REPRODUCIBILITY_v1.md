# K2 · R344 · 交付包 **Excellon/HDI 盲埋孔语义核** + **独立重跑一致** + mask 修法之钻孔中性（只读）

**件**：`K2_R344_DELIVERY_EXCELLON_HDI_SPAN_SEMANTICS_AND_DRILL_REPRODUCIBILITY_v1.json`（约定A `7b42cbd6f2839a1d`）

## 逐 span 语义核（owner #14③「Excellon 含 HDI 盲埋孔」）
| 文件 | 层跨 | 孔数 | via census | 合 |
|---|---|---|---|---|
| `-front-in1.drl` | F.Cu->In1.Cu | **171** | 171 | ✓ |
| `-front-in2.drl` | F.Cu->In2.Cu | **132** | 132 | ✓ |
| `-front-in4.drl` | F.Cu->In4.Cu | **4** | 4 | ✓ |
| `-front-in5.drl` | F.Cu->In5.Cu | **19** | 19 | ✓ |
| `-in2-in5.drl` | In2.Cu->In5.Cu | **92** | 92 | ✓ |
| `-back-in5.drl` | In5.Cu->B.Cu | **37** | 37 | ✓ |
| `.drl(合并)` | through 279 + PTH 16 + NPTH 4 | **299** | 299 | ✓ |
**合计**：盲埋孔 **455** == census `n_non_through_vias` 455 ✓ · 合并件 **299** == through 279 + PTH 16 + NPTH 4 ✓ · `drill_total 754` == 734 vias + 16 PTH + 4 NPTH ✓

## 独立重跑一致
`kicad-cli pcb export drill`（同板同参 · /tmp）⇒ 与交付包 **7/7 Excellon 逐字节一致**（仅剥注释行 + 日期归一化）；drill_map.svg / drill_report.txt 经工程名+日期归一化后亦一致。

## mask 修法（DFM 处置 ii）之中性 —— 全输出类
`pad_to_mask_clearance 0.05→0.02`：**8 铜层 + 2 丝印 + 边框 + 7 钻孔件 全部逐字节相同**，**仅 F.Mask/B.Mask 变更**。
（Mask Gerber 多边形分解整体重算 —— 阻焊坝消失致开窗连片之预期结果；图层归属不变，非扩散性改动。）

## 边界
只读 · **未重建/未覆盖旧包** · 未烙板 · 未改 `criteria/`/生成器/SPEC/原理图 · 未派 WORKER。冻结四源 4/4 未动。

---
—— ENG（ARCHER）· 2026-09-22 · owner 闸口 **0**
