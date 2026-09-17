# K2 · P4 · ③ 9 条 `ignore` 朝严摘除（已落仓库 pro）· v1 · 2026-09-17

> 依据监理 **#K2-21 §二③**：「8 条授权摘除；第 9 条 `missing_courtyard` 恢复 KiCad 默认 `warning`；
> **目标 = `ignore` 条数 0**」＋ 常设规则「severity 只可**朝严**由 ENG 落改（`ignore`→`warning`/`error`）」。
> 本件为**朝严落改**（`ignore` → `warning`，方向单向更严），并报**前后值 + sha**。

## 1. 落改实况（文本级最小改动，保原格式）
| 规则 | 改前 | 改后 |
|---|---|---|
| `copper_sliver` | `ignore` | `warning` |
| `footprint_filters_mismatch` | `ignore` | `warning` |
| `footprint_type_mismatch` | `ignore` | `warning` |
| `tuning_profile_track_geometries` | `ignore` | `warning` |
| `missing_courtyard` | `ignore` | `warning`（#K2-21 明定恢复默认） |
| `silk_over_copper` | `ignore` | `warning` |
| `silk_overlap` | `ignore` | `warning` |
| `track_not_centered_on_via` | `ignore` | `warning` |
| `via_dangling` | `ignore` | `warning` |

| 项 | 值 |
|---|---|
| 文件 | `k2/hw/k2_v4_8L.l5.kicad_pro` |
| sha16 改前 | **`f68a5fb2f82bd02d`**（备份 `/tmp/opencode/pro-before-ignore-removal.kicad_pro`） |
| sha16 改后 | **`d5e0ca067a7b585e`** |
| `ignore` 条数 | **9 → 0** |
| 板 | 未动（`k2/hw/k2_v4_8L.l5.kicad_pcb` = `6ff49da5678c2108`） |

**为何 8 条取 `warning`**：监理已实测「最严 `error` 仍 0 条」（#K2-21 §〇②），故 8 条取值对结果**无影响**；
取 `warning` 使仓库仪器的语义与本项目全过程所用探针口径一致（避免同一板在两套语义下数字不可比）。
若监理裁定改取 `error`（更严）或删键回落内置默认，均为一条命令可复现，ENG 不擅自选择。

## 2. 落改后复算（三份证据）
| 仪器 | 结果 |
|---|---|
| `kicad-cli pcb drc`（新 pro 语义，落件板） | **error 0 · warning 75**（`missing_courtyard` 40 + `lib_footprint_mismatch` 35）· 未连接 **0** |
| 冻结判定器 `criteria/adjudicate.py` | **PASS 7 / FAIL 3**（原 6/4）：`rule_severity_manifest` **0/62 → PASS**；余 FAIL = `zone_filled`(10/18) · `refdes_sets_equal`(H1–H4) · `pipeline_present`(6 目录) |
| 草案判定器 v2（②④⑤ 补丁 + §三 新检查） | **14 PASS / 1 FAIL**：`zone_filled` **10/10 PASS** · `refdes_sets_equal` **PASS**（排除 H*）· `drc_errors` **0** · `drc_warning_dispositions` **0/2 未登记** · `unconnected_zero` **PASS** · `fp_lib_table_present` **PASS** · `keepout_active` **PASS**；唯一 FAIL = `pipeline_present`（`k2/pipeline.yaml` 属 gate 安装项，草案已备） |

⇒ 余下 FAIL 全部且仅有「待 gate 安装的判据实现/接线」，**板侧已无可修项**。

## 3. 顺带发现：偏离的**源头在工艺模板**
`k2/tools/k2_jlc_template.kicad_pro` 的 `rule_severities` 与改前板 pro **逐键完全一致（含同样 9 条 `ignore`）**
⇒ 该偏离是**模板继承**，不是板级个案。计划 §P6 亦要求「模板整改后模板 ignore 集 == manifest 应然集」。
**本件不改模板**（P6 属「若获批」项）：仅登记，整改 = 同一条朝严替换（9 条 `ignore`→`warning`），命令与本节 §1 同构。

## 4. 边界
未改板/SPEC/判据原件（`criteria/` 两份 sha 未变）；未安装 `criteria/` 草案、未安装 `k2/pipeline.yaml`；未落新件；模板未动。
