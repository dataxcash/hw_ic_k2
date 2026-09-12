# CO-80（L2 可审计性）— L4 工程文件规则对齐；独立 kicad-cli 复现 DFM 判定

> 日期 2026-09-12｜工具 `tools/p3_v57_co80_l4_project_rule_align.py`｜记录 `d617a4c5e4e4523f`｜boundary **v1.45**

## 1. 缺陷 F-80-1（受控工件与意图不自洽，制造审计陷阱）

`k2_v4_8L.l4.kicad_pro` 是**受版本控制**的工件，并且是 `kicad-cli` 对 `k2_v4_8L.l4.kicad_pcb`
做 DRC 时**自动选取**的工程文件；但它的设计规则与工艺意图（`k2_v4_8L.kicad_pro` 及
`_shared/eda_core/drc_rules.json`）不一致：

| 规则 | 意图 | `.l4.kicad_pro`（原） |
|---|---|---|
| `min_track_width` | 0.09 | **0.2** |
| `min_via_diameter` | 0.35 | **0.5** |
| `min_via_annular_width` | 0.075 | **0.1** |
| `min_through_hole_diameter` | 0.2 | **0.3** |
| `min_copper_edge_clearance` | 0.3 | **0.5** |
| `min_clearance` | 0.1 | **0.0** |

另 `rule_severities`：`copper_sliver` / `silk_over_copper` / `silk_overlap` / `via_dangling`
意图为 `ignore`，`.l4.kicad_pro` 为 `warning`。

**实测后果（最自然的独立命令）**：`kicad-cli pcb drc k2_v4_8L.l4.kicad_pcb` 报 **880 条违规**
（`annular_width` / `drill_out_of_range` / `track_width` / `via_diameter` 各 199、
`copper_edge_clearance` 11、silk 警告等）⇒ 审计者会**误判板子不合格**。
项目 PASS 依赖 signoff 里**换成另一个工程文件**（`k2_v4_8L.kicad_pro`）——声称与工件不自洽。

## 2. 独立复现（先证伪自己的怀疑）

在**正确 staged**（工程文件 = 意图件；L4 板另加 `.kicad_dru`）下，用外部工具独立重跑并**自算多重集差**：

| | 违规数 | by_type |
|---|---|---|
| 冻结基线 `k2_v4_8L.kicad_pcb` | 42 | 29 `lib_footprint_mismatch` + 12 `lib_footprint_issues` + 1 `silk_edge_clearance` |
| L4 板 `k2_v4_8L.l4.kicad_pcb` | 42 | 同上 |

**多重集差 new=0 / disappeared=0**（独立实现，非项目 harness）⇒ 项目 DFM 判定**被外部工具复现**；
880 条确系**规则设置产物**，非板缺陷。

## 3. 修复（对齐，非放宽）

把意图工程文件的 `rules` 与 `rule_severities` 对齐进 `.l4.kicad_pro`（其余键不动，文件仍 `indent=2` 逐字节风格）：

- `.l4.kicad_pro`：`62132712a65853b0` → **`4704dec4dd043c59`**
- 修复后**最自然的命令**（`kicad-cli pcb drc k2_v4_8L.l4.kicad_pcb`，自动选取工程）实测：
  baseline **42** / L4 **42**，**new=0 / disappeared=0** ⇒ 审计陷阱消除。

**未放宽任何阈值**：对齐方向 = 采用**意图件**（= JLC 工艺极限 `drc_rules.json`）的既有值。

## 4. 链不受影响（已核）

| 检查 | 结果 |
|---|---|
| L4 apply 后板 sha | **`0e636a67c1472462`（逐字节不变）** |
| L5 signoff | **FAB ok / DFM PASS new=0 / SI 0.1300** |
| DFM / SI 记录 sha | `40445f87be664f31` / `73f9b59ed5f6f3ce`（均逐字节不变） |
| L4 工程文件是否被 applier 覆写 | 否（仍 `4704dec4dd043c59`） |

## 5. 残余

- ① 对间净空 0.875 仍为 **L1**；非执行者 pass 2/2、板厂券仍欠（外部）。
