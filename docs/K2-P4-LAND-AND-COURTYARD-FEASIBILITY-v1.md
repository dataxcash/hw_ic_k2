# K2 · P4 · land 真伪占位复核 + courtyard 补全可行性（W-7 × J-8b × W-8 联动测量）

| 项 | 值 |
|---|---|
| 阶段 | **P4**（计划 §②；未越阶段、未下单、未出交付 Gerber） |
| 依据 | W-7 `missing_courtyard`（40 条，待监理批「修/具名豁免」）· J-8b 器件重叠（本会话已证 40 件无 courtyard ⇒ DRC 不可判）· W-8/J-7 (甲′)/(乙)（待监理重裁） |
| 性质 | **ENG 只交测量**（无阈值、无裁定、不改板） |
| 板态 | `k2/hw/k2_v4_8L.l5.kicad_pcb` = `37019705ef994ccc`（**未改**）· pro = `f68a5fb2f82bd02d`（**未改**） |
| 工具 | `k2_p4_courtyard_completion_v1.py` `e1e91289cee3e9a1` · `k2_p4_upstream_land_fit_v1.py` `25487ec65a1ac1ca`（纯 stdlib、只读、确定性） |

## 1. courtyard 补全可行性（W-7 `missing_courtyard` 40 件 × J-8b）
- 覆盖：**有 19 / 无 40**（与 DRC `missing_courtyard` 副本实跑 40 条逐一对应）。
- 候选 = ∪(pad 外接框, Fab 图形外接框) + margin；既有 courtyard 用其真实图形框。**全板 59 件两两碰撞**：

| margin | 碰撞对数 | 涉件数 |
|---|---|---|
| 0.10mm | **7** | **10** |
| 0.25mm（KLC nominal） | **16** | **23** |
| 0.50mm | 32 | 32 |

- 0.25mm 全量 16 对（含 8 对 new-vs-new）：`C85↔J9` · `U4↔D2` · `U6↔C80` · `C79↔C83` · `C73↔J13` · `R41↔J12` · `D2↔U2` · `R42↔C83` · `R31↔R32` · `C86↔U2` · `L1↔U2` · `R33↔R32` · `R33↔R34` · `R40↔J6` · `U1↔J13` · `U1↔J9`。
- **既存侵占（今日即存在，非本增量引入）**：`D2` 的真实 courtyard 与 `U2` 现铜外接框重叠 **0.05mm**；`L1` 的真实 courtyard 与 `U2` 现铜外接框重叠 **0.005mm**
  ⇒ 若给 U2 补 courtyard，将与 D2/L1 的既有 courtyard 相碰（DRC `courtyards_overlap` = error）。
- 结论：**「修 `missing_courtyard`」不是零成本**；需监理在 **(a) KLC 0.25** / **(b) 项目 0.10** / **(c) 本体贴合** 三口径中择一（或对该 10–23 件具名豁免）。J-8b「器件重叠」在补 courtyard 前**不能被宣称已验证**（现状仅能说：铜级重叠 = 0）。

## 2. 上游真 land 占位复核 —— **(乙) 的真实代价**
方法：29 件「上游库名件」→ 取上游 `.kicad_mod` 的 pad 几何，按板上该件 `(x,y,rot)` 摆放
⇒ 与其余 58 件**现铜**做**逐 pad 精确相交（SAT）**；另以「外接框」给出上界候选。

**精确铜↔铜冲突 = 6 条（硬证据）**：

| 件对 | 重合 pad 对 | 说明 |
|---|---|---|
| `C86 ↔ U2` | 2 | C86(4.7uF,0603 真 land) vs U2 现 pad |
| `U2 ↔ D2` | 1 | U2 真 land vs D2(SS34) 现 pad |
| `U2 ↔ J12` | 2 | U2 真 land vs J12(J_12V_IN) 现 pad |
| `U2 ↔ J6` | 1 | U2 真 land vs J6(J_PWR_CTRL) 现 pad |
| `U2 ↔ R40` | 2 | U2 真 land vs R40(10K,0402) 现 pad |
| `C83 ↔ R42` | 1 | C83(1uF,0603 真 land) vs R42(1K) 现 pad（重叠 0.15×0.50mm） |

- **`U2`（`DCDC_12V_3V3`，链接 `Package_SO:SOIC-8_5.3x5.3mm_P1.27mm`）是唯一硬阻塞点**：其真 land 的 pad 外接框为 x∈[28.6,37.4]（生成器简化 land 仅 [30.75,35.25]）；
  在**现位置**按真 land 落 ⇒ 与西侧 `R40`/`J12`/`J6`、东侧 `D2` 的现铜**逐 pad 重叠**，
  且 `C86`(4.7uF) 整体位于其真实封装体/引线区之内。
  ⇒ **(甲′)**：保留「体下 pad」（可焊性风险，见隔离件 §7）；**(乙)**：U2 必须**先搬位/重构放置并重解该区走线**，不是「重落 pad」即可。
- **`C83 ↔ R42`**：C83 按真 land 落会与 `R42`（本 P4 增量 18 **strap 位移**件）现铜重叠 0.15×0.50mm ⇒ (乙) 对 C83 与 R42 需联动处理。
- 旁证：`E2`（`FRU_EEPROM`，`ForgeOS:SOIC8_FRU`，同形简化 land）按其位置做真 SOIC-8 占位复核 ⇒ **与邻件 0 冲突**（该点位有余量）；U2 点位不具备。
- 另有 **32 条「外接框上界」候选**（真 land/courtyard 外接框 vs 现铜/courtyard 外接框；**上界、非精确**，全量见 `--json`）。

## 3. 联动结论（ENG 不择一）
W-7（`missing_courtyard` 修/豁免）× J-8b（重叠可判性）× W-8（(甲′)/(乙)）是**一组耦合裁定**：

| 选项 | 代价（本件实测） |
|---|---|
| **补 courtyard（严格 KLC 0.25）** | 新增 **16 条 `courtyards_overlap` error**、涉 23 件；并暴露 D2/L1↔U2 的既存侵占 |
| **补 courtyard（项目 0.10）** | 新增 **7 对**、涉 10 件（含 `R42↔C83`） |
| **(甲′) 以板为准** | 铜 0 改动（本会话已验证 35→0），但保留简化 land：U2 点位无法容纳所命名的 SOIC-8 真封装 |
| **(乙) 按上游真 land** | **6 条逐 pad 铜冲突**（U2 涉 5 条）⇒ U2 需搬位 + C83/R42 联动 + 该区走线重解 |

⇒ 建议监理**把三项作为一组裁定**；ENG 不择一、不缩口径。

## 4. 自审更正（本会话内我修掉自身三处工具缺陷，均已复跑）
1. 覆盖率件把 J-8b 写成「由 DRC `courtyards_overlap` 覆盖」= **过宽**（40/59 无 courtyard 不可判）→ 已在原件加更正块（`261f9ddcba57fbd0` → `e6191320c3adf47f`）并改注覆盖工具（→ `43acfd15201a390b`）。
2. 本件首版把「本体/外接框占位」与「铜交叠」混为一类（union-AABB 会把 U2 真 land 外接框含 `C86` 误报为铜冲突：精确核对 **C86↔U2 上游真 land = 0 铜对**）→ 已拆为**逐 pad 精确 SAT**（硬证据）与**外接框上界**（标注为上界）两列。
3. SAT 角点按 `(-1,-1),(-1,1),(1,-1),(1,1)` 生成 ⇒ **自交多边形**、边法线错误 ⇒ 假冲突；
   正序（`(-1,-1),(1,-1),(1,1),(-1,1)`）修正后精确铜冲突由 16 条降为 **6 条**（`R31/R32/R33/R34` 一族的假冲突消失）。

## 5. 复跑
```bash
cd /home/fila/jqdDev_2025/ic_hw
python3 k2/tools/k2_p4_courtyard_completion_v1.py --margins 0.10,0.25,0.50 --json /tmp/opencode/crt.json
python3 k2/tools/k2_p4_upstream_land_fit_v1.py --json /tmp/opencode/fit.json
```

## 6. 边界
只读测量；板/pro/SPEC/真源/生成器/冻结件 `d4e81f64…`/`criteria/` **逐字节未动**；未安装任何判据；未新增判据维度；
未派 WORKER；未写 `.omo/supervision/**`；未下单、未出交付 Gerber。本件为**测量**，不含任何阈值或裁定。

—— ENG（ARCHER）· 2026-09-18
