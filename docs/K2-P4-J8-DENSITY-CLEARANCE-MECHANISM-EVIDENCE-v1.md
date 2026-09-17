# K2 · P4 · **J-8 密度/间距（`density_and_clearance`）机制落地证据** · v1 · 2026-09-17

> 缘起：监理自动续推「按已批准《K2 整体整改计划》推进当前阶段（P4，未全绿）」+ handoff inc37 §3-5
> 「余 `density_and_clearance` 仍 pending」⇒ 本件补齐 J-8 末项的**机制**（测量 + 判定块），使 J-8 三项
> （`keepout_active` / `pads_within_outline` / `density_and_clearance`）**全部有机制**，只剩监理给阈值。
> **禁新增检查齿**：`density_and_clearance` 是 v2/v3 manifest 已有的具名检查项（`enabled:false, pending`），
> 本件只实现其机制，**不新增维度**；登记册 §C J-8 原文即含「密度分布 / 关键间距」。
> **未动** `criteria/` 原件 · v2/v3 草案 · 冻结件 · 仓库板/pro · 生成器/SPEC/原理图/网表；未派 WORKER；临时仅 `/tmp/opencode`。

## 1. 交付物（ENG 起草区；**未安装**）

| 件 | sha256/16 | 说明 |
|---|---|---|
| `k2/docs/drafts/p4-j8-density-clearance-v1/adjudicate.draft-v4.py` | **`1cda68521d0e56be`** | **v3 的严格超集**：对 v3 `b77eacb11a261925` 的 diff = **3 hunk，全为新增**（`--density-json`/`--min-clearance-json` 参数 · 两测量装载 · `density_and_clearance` 检查块），共 +43 行，0 删改 |
| `…/manifest.k2.v4.yaml` | **`004f7ac2666da437`** | **安装件**：`density_and_clearance` 仍 `enabled:false` + `consume: [density_json, min_clearance_json]` + `pending: <阈值键已定>`（机制齐备） |
| `…/manifest.k2.control-v4.yaml` | **`2531d4c616d855e9`** | **仅正负控**（示例阈值，非政策提案） |
| `…/measure_density_and_clearance.py` | **`dccaaa476c807def`** | 测量件（无 `verdict`）：多口径密度 + 三横带 + 间距 + 工艺实达值 |
| `…/j8_dc_common.py` | **`c5f708932d4e5cd5`** | 共用几何层（pad AABB 口径与 J-8 出框测量同源） |
| `…/measure_min_clearance_drc.py` | **`a294a396a8747f71`** | 测量件（无 `verdict`）：DRC bracket 全板最小铜间距 |
| `…/run_controls_v4.py` · `…/README.md` | `8c9d3bd46d1ceb9b` · 见件内 | 七案正负控驱动 · 跑法与阈值键 |

## 2. 测量口径与实测（落件板 `k2/hw/k2_v4_8L.l5.kicad_pcb` = **`6ff49da5678c2108`**，未改）

板框 `[23.0, 33.0, 143.0, 79.0]`（120 × 46 mm）· 59 件 · 687 pad。

**2.1 密度（件中心分格；两种原点口径）**

| 网格 | `absolute_zero` 峰值 | `frame_origin` 峰值 | 备注 |
|---|---|---|---|
| 5 mm | **5** 件/格（(90,60)） | 4 | — |
| **10 mm** | **5** 件/格（(90,60)、(50,60) 各 5）· 直方图 `{1:11, 2:6, 3:6, 4:2, 5:2}` | **7**（(83,53)）· `{1:13,2:4,4:4,5:3,7:1}` | **复现登记提案（峰值 5）**；原点改口径 ⇒ 峰值 7 |
| 20 mm | 9 | 13 | — |
| （pad/10mm） | 141 pad/格 | 106 | 仅报数 |

> **口径敏感性（归监理）**：同一块板，10mm 格峰值随原点 = 5 或 7 ⇒ 监理须择一（默认 `absolute_zero`，与登记提案一致）。

**2.2 三横带占用（M-12 口径的**明确定义版**；S-6a 待监理择一）**

定义：横带 = Edge.Cuts AABB 沿 y 三等分；占用 = **焊盘 AABB 并集 ∩ 带 / 带面积（板框宽度）**。
实测：带1 `y∈[33.0,48.33]` = **4.78%** · 带2 `[48.33,63.67]` = **7.59%** · 带3 `[63.67,79.0]` = **2.19%** ⇒ max **7.59%**。
（登记册 M-12 原文「三横带占用 19–27%」与任何已知口径均不符，仍须监理补定义 ⇒ 本件只给可复算的明确定义版。）

**2.3 关键间距 / 工艺实达（本板）**

| 项 | 实达 | 口径 |
|---|---|---|
| 异网 pad AABB 最小间隙 | **0.200 mm**（`U4.3 (P3V3)` ↔ `D2.2 (SW_U2)`） | AABB 保守下界 |
| **全板最小铜间距（DRC bracket）** | **∈ [0.100, 0.105] mm**（0.100 ⇒ 0 违规；0.105 ⇒ 3；0.110 ⇒ 3；0.120 ⇒ 9；0.150 ⇒ 19；0.200 ⇒ 196） | 最紧样本 = `I2C1_SCL` ↔ `I2C1_SDA`（F.Cu）、实际 **0.1000 mm** |
| 孔-孔最小边距 | 1.74 mm（20 孔） | 钻孔边到边 |
| courtyard | 19 件有；AABB 重叠 **3 对**（`R44↔R35` 等），min 0.0 mm | AABB（DRC `courtyards_overlap` 现 0 ⇒ AABB 为保守上界口径） |
| pad 到板边 | **0.38 mm**（`J13.1`） | pad AABB 到板框 |
| 最小线宽 | 0.160 mm（4721 track） | 板实达 |
| 最小过孔 Ø / 钻 / 孔环 | **0.350 / 0.200 / 0.075 mm**（711 via） | 三项**零余量**（恰在声明下限） |
| 最小孔钻 | 0.80 mm | — |

> 与旧件 `K2-P4-J8-REMAINING-MEASUREMENT-v1.md` 的差异：旧件板 sha 为 `37019705ef994ccc`（**旧板**）⇒ 本件为落件板 `6ff49da5678c2108` 的复算（0.200mm 处 198→**196** 违规；pad 峰值口径明确为两种原点）。

## 3. 判定式（`adjudicate.draft-v4.py`）与 fail-closed

`density_and_clearance` 启用时（`manifest.checks.density_and_clearance.enabled: true`）全部满足才 PASS：
① 密度峰值（`cell_mm` + `cell_origin` 指定格）≤ `max_fp_per_cell`；
② DRC bracket 的 `min_copper_clearance_mm_lower_bound` ≥ `min_copper_clearance_mm`；
③（可选）三横带 `max_ratio` ≤ `max_band_occupancy_ratio`；
④（可选）孔环 ≥ `min_via_annular_mm`；⑤（可选）pad 到边 ≥ `min_pad_to_edge_mm`。
**fail-closed**：`--density-json`/`--min-clearance-json` 缺件 ⇒ FAIL；两 JSON 的 `board_sha16` ≠ 受审板 ⇒ FAIL（证据陈旧）；
**必填阈值（`cell_mm`/`max_fp_per_cell`/`min_copper_clearance_mm`）未给 ⇒ FAIL**（不假装实现、不缩口径）。
⇒ 与 v3 的 `ref_plane_continuity` 同构：**机制齐备、阈值归监理**。

## 4. 正负控矩阵（`python3 k2/docs/drafts/p4-j8-density-clearance-v1/run_controls_v4.py`，实跑全命中）

| 案 | 板 | manifest | 整判 | `density_and_clearance` |
|---|---|---|---|---|
| **A** 安装件 | l5 `6ff49da5678c2108` | `manifest.k2.v4.yaml` | **15P/2F** | 未启用（`enabled:false`）⇒ 与 v3 A 案同分，**FAIL 集不变** |
| **B** POS | l5 | control-v4 | **17P/2F** | **OK**：峰值 5（≤6）· 0.1（≥0.1）mm · 带 0.0759（≤0.1）· 环 0.075（≥0.075）· pad 到边 0.38（≥0.3） |
| **C** NEG-density | 合成拥挤板 `8ee51fe7f86499d2`（`R31–R38` 移至最空处 84.95,72.95 ⇒ 10mm 格峰值 **8**） | control-v4 | 13P/6F | **FAIL（隔离命中）**：峰值 8 > 6，其余子值全 OK（0.1≥0.1 · 带 0.0726≤0.1 · 环 0.075≥0.075 · 边 0.38≥0.3） |
| **D** NEG-clearance | l5 | control-v4 改 `min_copper_clearance_mm: 0.12` | 16P/3F | **FAIL（隔离命中）**：0.1 < 0.12，密度子值 OK（峰值 5≤6） |
| **E** STALE | l4 `d4e81f647be7f980` + **l5 测量** | control-v4 | 4P/15F | **FAIL**：数值全 OK（峰值 5≤6 · 0.1≥0.1）但 `sha16 6ff49da5… vs d4e81f64… ⇒ 不一致（证据陈旧，fail-closed）` |
| **F** MISSING | l5，无两测量 JSON | control-v4 | 14P/5F | **FAIL**：`缺 J-8 密度/间距测量 JSON ⇒ fail-closed` |
| **G** THRESH-NULL | l5 | control-v4 删 `thresholds.density_and_clearance` | 16P/3F | **FAIL**：`阈值未定 ⇒ fail-closed（机制齐备，启用须监理给阈值）` |

- **A 案整判 FAIL 集** = `pipeline_present`（gate 安装项）· `lib_electrical_level`（⑦ 库侧待裁）—— 与 v3 A 案一致。
- **B 案 = A + 2**：`ref_plane_continuity`（v3 控制件）转 OK + 本轮 `density_and_clearance` 转 OK。
- 负控合成板仅用于**判据区分度**验证（其自身另触其它检查，如未连接；不构成板侧结论）。

## 5. 对 S-6a / 闭环表的口径更新（判据归监理、应然值归监理）

1. **S-6a（J-8 密度登记来源）**：ENG 现交**两个可复算口径** —— ① 10mm 格峰值（`absolute_zero` = **5**，与登记提案一致；`frame_origin` = 7）；
   ② 三横带占用比（定义见 §2.2，实测 **4.78/7.59/2.19%**）。**M-12「19–27%」仍复现不出**，请监理在 ①/②/其它 中择一并给阈值。
2. **闭环表 J-8 行**：④「pending：`pads_within_outline`、`density_and_clearance`」⇒ 现三项**机制全部在岗（草案区）**；但 `criteria/` 未安装 + manifest 未签认 + 阈值未定 ⇒ **⑤ 仍为「未闭」**（不因本件改判）。
3. **禁新增检查齿**：本件无新维度（J-8 原文含密度/间距）；「`max_fp_per_cell`/`cell_origin`/`max_band_occupancy_ratio`/`min_via_annular_mm`/`min_pad_to_edge_mm`」均为**既有维度的阈值键**，非新齿。

## 6. 复现

```bash
cd /home/fila/jqdDev_2025/ic_hw
K=AppDir/usr/bin/python3.11; D=k2/docs/drafts/p4-j8-density-clearance-v1
B=k2/hw/k2_v4_8L.l5.kicad_pcb; P=k2/hw/k2_v4_8L.l5.kicad_pro
$K $D/measure_density_and_clearance.py --board $B --json /tmp/opencode/dc/dc.json
python3 $D/measure_min_clearance_drc.py --board $B --pro $P --kicad-cli AppDir/bin/kicad-cli \
  --work-dir /tmp/opencode/dc/clr --json /tmp/opencode/dc/mc.json
diff -u k2/docs/drafts/p4-j8-v3-criteria-v3/adjudicate.draft-v3.py $D/adjudicate.draft-v4.py   # 应为 3 hunk / 全新增
python3 $D/run_controls_v4.py                                                                  # 七案矩阵
```

## 7. 边界

未动：`criteria/` 原件（`897e8bfde60e2cfe` · `7ce08757eff25557`）· v2 草案（`7cf8a50eb832c284`）· v3 草案（`b77eacb11a261925`）·
冻结板 `d4e81f647be7f980` · 仓库板 `6ff49da5678c2108` / pro `d5e0ca067a7b585e` · 生成器 / SPEC / 原理图 / 网表真源 · `.omo/supervision/**`。
写操作仅 `/tmp/opencode/dc`。**P4 仍未全绿**（`pipeline_present` + `lib_electrical_level` 未闭 + G-ROOT-1/2/3 未修 + 5 项阈值待监理）
⇒ fail-closed 不变：P4 未全绿不下单、不出交付 Gerber（owner #14 ③）。

—— ENG（ARCHER）· 2026-09-17
