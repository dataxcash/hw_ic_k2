# CO-101（L2 自裁 · PDN 施加）rev-11 → **rev-12 计划集互障重导**（依 CO-99/CO-100）

> 日期 2026-09-12｜工具 `tools/p3_v57_co101_pdn_rev12_derive.py` `977ee54f0ecdb414`
> 记录 `m13_v57_co101_pdn_rev12_derive.json` `cdeea6a3950f04f6`｜**SPEC rev-12** `1a381b06454dbe2c`（rev-11 `d85f10f722ba22b0` 原件未动）
> 依据：CO-100 记录 `11e21f3b97bac66b`（互障感知重放）｜板 `0e636a67c1472462`（**逐字节不变**）

## 1. 施加内容（rev-12）
- **ppc**：entries **189 → 185**（kept 124 / **relocated 61** / **新增 blocked 4**；blocked 120 → **124**）；`clearance` 按板侧 Scene 重算。
- **gnd_stitch_via**：**relocated 5** / **新增 blocked 1**（原 60 blocked 保留）。
- **power_zones[].vias**：**relocated 4**。
- **退役留存**：rev-11 原坐标显式留存于 `retired_superseded_mutual_conflict_v1`（ppc/stitch）+ `power_zones_via_retired_mutual_conflict_v1`（禁静默放弃）。
- **CO-96 F5 同步**：`board_realized` 更新为 rev-12 决策数（消除 223/86 陈旧矛盾）。
- **CO-96 F1 残余闭合**：自 rev-9 回填 `retired_superseded_bom`（随本次 SPEC bump）。
- `spec_version = 1.1.spec-rev-12`；`pd` 外无改动。

## 2. 验证（rev-12 新基线）
- **链**：G4 `FEASIBLE_ALL` `cb955e9af8782d08`（34 页 / crossings 0 / work 546/546 / certs 0）｜G5 PASS `frozen=True` `6fe5283990115227`｜L4 **viol 0**｜L5 FAB ok + **DFM new=0** + **SI 0.1300**；**板逐字节 `0e636a67c1472462` 不变**。
- **PDN 闸**：**CO-99 = `PASS`**（互异重叠 **0** / 净距 **0** / 孔距 **0** —— CO-99 的核心缺陷已清除）；CO-91 PASS（0/0）；CO-92 = `CANDIDATE`；CO-95 `OPEN`(35/8/6/6)；CO-98 `OPEN…`(35/14/6) 三态不变（可达性分类与本次重导无关）。
- **回归闸**：co77（对 v1.67）/ co78 / co81 / co84 / co87 / co88 / co97 / co69 全 PASS。

## 3. 残余（如实，非 PASS）
- **施工侧（引擎）未同步**：`pdn_apply.add_track(..., width=0.5)` 字面量 + 不去重 ⇒ rev-12 的 **dry-run 仍 +34 违规**（rev-11 为 +232）——属 CO-93 §④ / CO-99 根因②③，须**项目内引擎承载**时修（施工期激活）。
- **6 项新增 blocked（5 ppc + 1 stitch，全 GND，全在 U6 0.5mm 场）**：已并入 blocked 台账；保连接数须 **via-in-pad（工艺）/ HDI（层数，L1）**（CO-94 同张力）。

## 4. 复评债 / 非声明
- **rev-12 非执行者复评欠（CO-102）**：本件为执行者，按 `L2_STRUCTURE_v2.0.md:137` 不得自评；CO-96 的 rev-11 证书随本次重基线失效（**co96 现按 fail-closed 报 `BASELINE_MISMATCH`**，属预期）。
- 零几何**搜索**（坐标全部来自 CO-100 的声明 palette 重放）；不改板/阈值/冻结源；**不改 rev-11 及以前历史件**。
