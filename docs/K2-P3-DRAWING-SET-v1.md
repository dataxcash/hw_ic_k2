# K2 · P3 施工图集 v2（含 G1/G2 落位解；**交监理核图**）

> **依据**：监理 **#K2-15 §二**（P2 正式关门、**P3 开**）+ 整改计划 **§P3** + L2 裁定（`c3ee574455cf6633` `k2/docs/K2-ENG-AUDIT-2026-09-15.md` §十 L2-1..L2-8）。
> **边界**：未改 SPEC / 原理图 / 板 / 生成器（既有）/ `criteria/` / 冻结件；未派 WORKER；输出 = `L3/drawings/`（+ `/tmp` 沙箱复跑）。
> **判据归属**：**P3 判据由监理核，ENG 不自判** —— 下表只给 **ENG 测量值**。
> **v2 变更**：G1/G2 **已解**（新增 `k2_p3_place_solver_v1.py`，确定性 + 五项机验全零）⇒ 55 件坐标齐备。

## 1. 交付物

| 件 | sha256(16) | 说明 |
|---|---|---|
| `k2/tools/k2_p3_drawings_v1.py` | `262d931bf5ed887f` | 图纸生成器（纯 stdlib SVG；SPEC 经 `pm_gate.config` 解析） |
| **`k2/tools/k2_p3_place_solver_v1.py`** | **`79eaf8772d8e62f8`** | **落位求解器**（L2 自裁域；栅格 0.05–0.1mm + 五项约束机验） |
| `k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_drawings.json` | `8bb574532499b0e7` | 机读图纸（板框/4 孔/**55 件全坐标**/走廊/回避区/层分配/敷铜/判据） |
| `k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_placement_solution.json` | `dea2fa79648b96a2` | **落位解**（15 件 = 13 补件 + 2 移位；含 selfcheck 全零） |
| `k2/pm_gate/artifacts/k2_v4/L3/drawings/01..07_*.svg` | — | 7 张施工图（板框+孔 / 器件坐标 / 走廊 / 层分配 / 敷铜 / 回避区 / 接口出框） |

## 2. 判据对账（计划 §P3；ENG 测量，**待监理核**）

| # | 判据 | 阈值 | ENG 实测 | 结论 |
|---|---|---|---|---|
| **P3-1** | 板框 = 120×46（`y[33,79]`） | `[冻结值]` | **120.0 × 46.0**；`x[23,143]` `y[33,79]` | 测量值如上，**待核** |
| **P3-2** | 固定孔 ≥4 NPTH Ø3.2，距边 ≥1.5mm 材料 | ≥4 / Ø3.2 / ≥1.5 | **4 孔**（H1 26.10/75.60、H2 139.60/39.60、H3 26.10/36.10、H4 114.60/36.10；L2-2 解）；**最小边料 1.50mm** | 测量值如上，**待核** |
| **P3-3** | 每器件 pad 数 == 符号引脚数 | 差异 = 0 | **53/55 逐值相等**；字面不符 = `U1`（27 vs 49 = LQFP48 48+EP49）、`U2`（6 vs 8 = SOIC-8 含 2 未用脚）⇒ 按 **#K2-12 §一-1 有向口径**（符号 ⊆ 焊盘 + 余量逐条登记）二者为**已登记余量**（见 `K2-P2-E2-directed-pad-registry-v1.md` v1.1） | 字面 2 项 = 有向口径登记项，**请按 §一-1 核** |
| **P3-4** | 接口焊盘不出框（内缩 0.3mm） | 出框 = 0 | 8 接口件（`J2/J3/J4` + 排针 `J6/J9/J11/J12/J13`）**出框 0**（几何 = 板实测 + L2-3 `column_x` 26.5→**27.94**） | 测量值如上，**待核** |
| **P3-5** | 回避区每区 ≥1 开关 ≠ `allowed` | 每区 ≥1 | **4 区**（固定孔 Ø6.0 / 逃逸区 / AC pad GND cutout / 板边 0.30mm）均有非 allowed 开关 | 测量值如上，**待核** |
| **P3-6** | 走廊口径统一 | 字面一致 | **焊盘外接框净距**；西 **17.55** / 东 **27.81**（原 17.30/27.40 作废） | 测量值如上，**待核** |

## 3. G1/G2 落位解（**L2 自裁**；确定性 + 五项机验全零）

**约束（全部机验）**：板框内缩 0.3mm（L2-8 8b）· 与既有 pad 净距 ≥0.2mm · 新件间 ≥0.5mm（SPEC `row_plan`）· 避 4×固定孔 Ø6.0（L2-2）· 避 SPEC 去耦柱 keepout · **不触 L1**（器件分区/接口朝向不变）。
**机验结果**：`in_frame=0 ∨ pad_clearance=0 ∨ part_spacing=0 ∨ hole_ko=0 ∨ decap_ko=0` —— **全零违规**，15/15 解出。

| 件 | 坐标 (mm) | 封装 | 依据 |
|---|---|---|---|
| `C73` | (28.0, 46.1) | `C_0402_1005Metric` | L2-3 已裁须移位（排针列 column_x 26.5→27.94）；L2 自裁新坐标：左带内就近原位、避既有 pad |
| `C86` | (32.4, 36.0) | `C_0402_1005Metric` | L2-3 已裁须移位（排针列 column_x 26.5→27.94）；L2 自裁新坐标：左带内就近原位、避既有 pad |
| `D2` | (38.7, 34.6) | `D_SMA` | buck 续流二极管（SW↔GND）；L2 自裁：就近 SW pad |
| `L1` | (33.0, 40.2) | `L_0805_2012Metric` | buck 电感（SW→P3V3）；L2 自裁：就近 SW/P3V3 pad 中点 |
| `R35` | (83.6, 60.95) | `R_0603_1608Metric` | SPEC layer_plan.strap_domain_v32.placement（域/排法/0603 已裁）+ 就近 |
| `R36` | (100.4, 58.95) | `R_0603_1608Metric` | SPEC layer_plan.strap_domain_v32.placement（域/排法/0603 已裁）+ 就近 |
| `R37` | (103.4, 58.95) | `R_0603_1608Metric` | SPEC layer_plan.strap_domain_v32.placement（域/排法/0603 已裁）+ 就近 |
| `R38` | (103.4, 60.95) | `R_0603_1608Metric` | SPEC layer_plan.strap_domain_v32.placement（域/排法/0603 已裁）+ 就近 |
| `R39` | (100.4, 60.95) | `R_0603_1608Metric` | SPEC layer_plan.strap_domain_v32.placement（域/排法/0603 已裁）+ 就近 |
| `R40` | (29.5, 38.2) | `R_0402_1005Metric` | FB 分压上臂；L2 自裁：就近 FB pad |
| `R41` | (29.7, 34.7) | `R_0402_1005Metric` | FB 分压下臂；L2 自裁：就近 FB pad |
| `R42` | (86.6, 58.95) | `R_0603_1608Metric` | SPEC layer_plan.strap_domain_v32.placement（域/排法/0603 已裁）+ 就近 |
| `R43` | (83.6, 58.95) | `R_0603_1608Metric` | SPEC layer_plan.strap_domain_v32.placement（域/排法/0603 已裁）+ 就近 |
| `R44` | (86.6, 60.95) | `R_0603_1608Metric` | SPEC layer_plan.strap_domain_v32.placement（域/排法/0603 已裁）+ 就近 |
| `R45` | (93.0, 58.95) | `R_0603_1608Metric` | SPEC layer_plan.strap_domain_v32.placement（域/排法/0603 已裁）+ 就近 |

- **9× strap R**：**域/排法/封装由 canonical SPEC `layer_plan.strap_domain_v32.placement` 已裁**（南带 `x[83,104] y[58.5,66]`、**2 排 5/4 交错**、间距 ≥0.5mm）⇒ 求解器**只在已裁域内**就近各自球排布（球坐标取 SPEC `resistors[].ball_board_pos`），最终排布 = 第 1 排 5 件 / 第 2 排 4 件，与 SPEC 完全一致。
- **`D2`/`L1`/`R40`/`R41`**：buck 域**无既有裁值** ⇒ 按 **L2 自裁**（PDN/布局）就近 `U2` 的 `SW`(pad1)/`FB`(pad3)/`P3V3`(pad5) 求解。
- **`C73`/`C86`**：L2-3 已裁须移位 ⇒ 新坐标为左带内就近原位、避既有 pad 之解（原位移除）。
- **`strap` 封装口径冲突（请监理核图时一并裁）**：SPEC `strap_domain_v32.placement.footprint = Resistor_SMD:R_0603_1608Metric`（0603，附 strip 排布可行性理由）vs 真源 yaml 符号 footprint = `R_0402_1005Metric`/`Resistor_SMD:R_0402_1005Metric`（0402，**且 9 件中 6 件为无库前缀的裸名**）。本图解与求解器**按 SPEC 0603** 出（L2 已裁 + 排布可行性依据），**BOM 影响须监理确认**；若改判 0402，重跑求解器即可（域内更宽裕）。

## 4. 冲突登记（请监理核图时一并裁定）

- `L1_TOPOLOGY_v2.0.md` / `L2_STRUCTURE_v2.0.md` 文本为 **6L**（「6L 判定流程终定；8L 兜底」）；canonical `rev-22` = **8L**、交付板 `k2_v4_8L`、计划 **Z3** 判据已判 ✅。**本图集按 8L 出**（依据 = canonical + 计划 Z3 + owner #14 ① HDI 冻结）；**ENG 不自改 L1/L2 冻结件**，建议裁定 errata 或版本 bump。

## 5. 复跑

```bash
cd /home/fila/jqdDev_2025/ic_hw
AppDir/usr/bin/python3.11 k2/tools/k2_p3_place_solver_v1.py     # 落位解（含 5 项自检）
AppDir/usr/bin/python3.11 k2/tools/k2_p3_drawings_v1.py        # 出图 + 判据测量（消费落位解）
# 沙箱复跑（**解与图须同目录**：生成器默认从 `$K2_P3_OUT` 读解，可用 `K2_P3_SOL_IN` 另指）
K2_P3_SOL_OUT=/tmp/opencode/p3 K2_P3_OUT=/tmp/opencode/p3 AppDir/usr/bin/python3.11 k2/tools/k2_p3_place_solver_v1.py
K2_P3_OUT=/tmp/opencode/p3 AppDir/usr/bin/python3.11 k2/tools/k2_p3_drawings_v1.py
# ⇒ 复现仓内 sha：solution dea2fa79648b96a2 / drawings 8bb574532499b0e7（实测）
```
