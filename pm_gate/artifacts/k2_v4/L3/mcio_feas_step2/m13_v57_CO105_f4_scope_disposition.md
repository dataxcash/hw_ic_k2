# CO-105 L2 自裁（PDN 建模）：CO-96 F4（可达性 requirement scope）落定 = `CLOSE_NO_SCOPE_EXTENSION`

- 依据：`LAYOUT_CONSTITUTION` 第二章 —— PDN 承载/建模属 **L2**；区域归属、电源域划分属 **L1**。
- 对象：CO-96 **F4（中·范围）**「`plane_reachability_requirement` 仅覆盖 ppc 非 GND entry（55），而 `gnd_stitch_via_realized`(40) / `power_zones[].vias`(17) 无闸」；CO-98 以「声明排除」处置，本件把该处置**机判化并落定**。
- 结论：**不需 scope 扩展动作**；F4 关闭。**零 SPEC / 板 / 阈值 / 冻结源改动；不需重基线；不需新复评**（L2 自裁、非几何变更）。

## 机判（4/4 通过，牙齿 2/2）

| 面 | 判据 | 结果 |
|---|---|---|
| V1 语义不可适用 | requirement 判据 = 「via 是否落在**本网 In4 铜**内」；GND 的平面层 = `In1/In3/In6`，In4 仅 `P3V3/MCU_VDD/P3V3_AUX` | GND 无 In4 区 ⇒ 对 **130 GND ppc entry + 40 GND stitch via** 该判据**无可判定**（≠「未覆盖」）；requirement 对象 = **非 GND ppc entry 55** |
| V2 几何待 L3 | 17 个 `power_zones[].vias` 所在 zone 是否已有派生几何 | **17/17** 位于 3 个 **bridge zone**（`P3V3_BCU_BRIDGE_IN4` 3 / `P3V3_AUX_BCU_BRIDGE_IN4` 8 / `MCU_VDD_BCU_RESISTORS_IN4` 6），其 `polygons=[]`、`geometry_status=L3_CONSTRUCTION_DERIVED` ⇒ 与 CO-98 `declared_pending_l3` **同桶**；扩 scope 只会把这 17 项并入待派生清单，**不新增可判缺陷** |
| V3 生成端 latent | 施工路径是否**代码引用** `gnd_stitch_gen` | 代码引用 **0**（散文复盘 1 处）⇒ 施工只读 SPEC `gnd_stitch_via.coordinates`（rev-12 由 CO-101 声明 palette 重放 + 退役留存）；生成端缺陷若重生成须同批修 |
| V4 F3/R1.2 归层 | `R1.2` 判据根因 | 依赖自由文本的裁决根因 = **电源域 / 区域归属 = L1** ⇒ 不在 L2 范围（一句话升级，不在此展开） |

牙齿：`gnd_in4_detector`（GND 平层集合不含 In4，而 In4 确被其他网占用 ⇒ 检测器非空真）、`empty_geom_detector`（17/17 空几何，且板/SPEC 中确存在**有**几何的 zone ⇒ 检测器有区分度）。

## 落定后的未决面

- **L1 三项**：`12V_IN` 承载（无 In4 区）、`P3V3_AUX` 西区归属（与西区名义网 `MCU_VDD` 冲突）、L1 ① 对间净空 0.875（A/C）。
- **外部输入**：PM ⇒ PDN 压降 / 热（CO-87 两项 NOT_DEMONSTRATED）；板厂阻抗券 ⇒ `CO-71 --build`。
- **L2 已无在办项**（F4 本件关闭；F3 归 L1；`gnd_stitch_gen` latent 登记；CO-103/CO-104 已完成）。

## 复现

```bash
cd /home/fila/jqdDev_2025/ic_hw/k2
../AppDir/usr/bin/python3.11 tools/p3_v57_co105_f4_scope_disposition.py     # 期望 CLOSE_NO_SCOPE_EXTENSION / 4 检查全过
python3 tools/p3_v57_co77_closure_declaration_sweep.py                    # 对象 = 最新 boundary（v1.71）⇒ 期望 PASS
```

## 非声明

- 本件**不**扩大 requirement 的判定对象；若未来要把 In4 电源 zone vias 纳入机判，应先派生 L3 几何（`polygons=[]` → 非空），否则只会得到「待派生」结论。
- 本件不重审 CO-95/CO-98 的判据实现（其 PIP/牙齿已由 CO-98 覆盖）。
