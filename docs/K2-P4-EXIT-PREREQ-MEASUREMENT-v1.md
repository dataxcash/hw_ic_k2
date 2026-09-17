# K2 · P4 出门前置三项实测（铺铜 / 钻孔 / 平面落图）· v1 · 2026-09-17

> 对象：《K2 整体整改计划》§P4 的三条「完工判据（前置）」在**五步复合板**上的实测。
> 板 = `/tmp/opencode/silk-6/silk-fixed.kicad_pcb`（sha256/16 **`6ff49da5678c2108`**，= ① 待落件目标）；
> 舞台 = `/tmp/opencode/gerber-1/`（同名 pro + `fp-lib-table` + `lib/`，T-8/T-40）。**未落仓库、未下单。**

## 1. 铺铜前置：`zone_filled`
| 项 | 实测 |
|---|---|
| zone 总数 | **18** = **10 铜平面** + **8 规则区（keepout）** |
| 铜平面（**10/10 已填充**） | `In1.Cu` GND · `In3.Cu` GND · `In6.Cu` GND · `In4.Cu` ×7（12V_IN ×2 · P3V3_AUX ×2 · P3V3 ×2 · MCU_VDD ×1） |
| 规则区（8，**按定义无填充**） | 4 区在 `F.Cu`；4 区为多层（`GetLayer()=UNDEFINED`，layer set 含多铜层） |
| 判定器现报 | `zone_filled: 已填充 10/18` → **FAIL** |

**结论**：铜平面填充率 = **10/10**；`zone_filled` 的「10/18」是把**规则区**计入分母所致 —— 规则区是排除区、KiCad 不为其生成 `filled_polygon`，
故**非板缺陷，属判据口径误判**（新登记项；`criteria/` 属主 `ic_hw_gate`、ENG 只读 ⇒ 出路：判据侧修正分母，或 manifest 记具名豁免，均属 owner/gate 通道）。

## 2. 钻孔前置：`NPTH ≥ 4` 且 `PTH ≥ 插件件引脚数`
| 项 | 实测 | 判 |
|---|---|---|
| NPTH | Excellon `-NPTH.drl`：`T1 3.200mm` × **4** 孔（安装孔）；板侧 `PAD_ATTRIB_NPTH` = 4 | **≥4 ✓** |
| PTH 插件引脚 | 板侧通孔 pad = **16** = `J13 4 · J9 4 · J11 4 · J6 2 · J12 2`；Excellon `-PTH.drl` `T2 0.800mm` × 16 hits | **= 引脚数 ✓** |
| 通孔 via | `-PTH.drl` `T1 0.200mm` × 310 | 合法（min_through_hole 0.20） |
| HDI 盲埋孔（**按层对分文件**） | `F–In1` 130 · `F–In2` 127 · `F–In4` 4 · `F–In5` 16（blind）· `In2–In5` 92 · `B–In5` 32（buried） | 齐备 ✓ |

## 3. 平面落图前置（**N-01**）：平面层 Gerber `G36 > 0`
`kicad-cli pcb export gerbers`（8 铜 + 阻焊 + 丝印 + 边框，未用 `--check-zones`，即**按板内既有填充**如实作图）后逐层计数：

| 层 | 角色 | `G36`（区域填充指令） |
|---|---|---|
| `In1.Cu` | GND 平面 | **1** |
| `In3.Cu` | GND 平面 | **1** |
| `In6.Cu` | GND 平面 | **1** |
| `In4.Cu` | 电源平面（4 网 7 区） | **8** |
| `F.Cu` / `B.Cu` / `In2.Cu` / `In5.Cu` | 信号层（无 zone） | 0（**非缺陷**：本就无平面区） |

**结论**：四条平面层全部 `G36 > 0` ⇒ 计划 §P4「平面落图前置」**达标**；`N-01`（交付 Gerber 无平面铜）在本板上不再复现。

## 4. 顺带核对：P4 交付清单（owner ③）
- 已产出：**8 铜层** + `F/B_Mask` + `F/B_Silkscreen` + `Edge_Cuts` + **`*.gbrjob`** + Excellon（含 HDI 盲埋孔分文件）✓。
- **paste 未产出**：请求 15 层实绘 13 层，`F.Paste`/`B.Paste` 被 kicad-cli **静默跳过**（板侧 `F.Paste` 有 666 pad，无报错，rc=0）。
  owner ③ 清单**不含** paste ⇒ 不阻塞；**若后续走 JLC SMT**（钢网/BOM/CPL）需另出并查明跳过原因。
- 未做（属 P4 收口/交付打包，留待 P4 判定后）：叠层图 · 阻抗表 · MANIFEST · JLC HDI 通道 DFM 逐项。

## 5. 复跑命令
```bash
cd /home/fila/jqdDev_2025/ic_hw
S=/tmp/opencode/gerber-1; mkdir -p $S
cp <五步复合板> $S/k2_v4_8L.l5.kicad_pcb; cp k2/hw/k2_v4_8L.l5.kicad_pro $S/
cp k2/hw/fp-lib-table $S/; ln -sfn $(pwd)/k2/hw/lib $S/lib
AppDir/bin/kicad-cli pcb export gerbers -o $S/gerber/ \
  -l "F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,In5.Cu,In6.Cu,B.Cu,F.Paste,B.Paste,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts" \
  $S/k2_v4_8L.l5.kicad_pcb
AppDir/bin/kicad-cli pcb export drill -o $S/drill/ --format excellon -u mm \
  --excellon-separate-th --generate-report --report-path $S/drill/drill.rpt $S/k2_v4_8L.l5.kicad_pcb
for L in 1 3 4 6; do echo -n "In$L.Cu G36="; grep -c G36 $S/gerber/k2_v4_8L.l5-In${L}_Cu.g${L}; done   # 期望 1 1 8 1
```

## 6. 更新后的 P4 未决清单（**未全绿，fail-closed 不变**）
| # | 项 | 归属 |
|---|---|---|
| 1 | ① 落件批准（目标 `6ff49da5678c2108`，落件器 v2 台账） | 监理 |
| 2 | `zone_filled` 判据口径（规则区计入分母） | **判据 owner（ic_hw_gate）** |
| 3 | `rule_severity_manifest` 9 条 ignore 台账 + `not_countersigned→false` 签认 | 监理 |
| 4 | `pipeline_present`（`k2/pipeline.yaml` 安装，W-9） | 监理 |
| 5 | `refdes_sets_equal` 板有图无 4（H1–H4） | **真源/原理图侧（owner 闸）** |
| 6 | ④ `missing_courtyard` 40 口径（T-39 联合不可满足） | 监理 |
| 7 | `lib_footprint_mismatch` 35（W-8/O-2，以板为准） | 监理/owner |
