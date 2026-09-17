# K2 · P4 · 判据侧交付草案 v2（②④⑤ 实现修正 + §三 manifest 补齐）· 2026-09-17

> 依据监理 **#K2-21**（§二②④⑤、§三、§六-3/4）。**全部为草案：未安装、未改 `criteria/` 原件、未签认。**
> 落盘位置 `k2/docs/drafts/K2-P4-criteria-draft-v2/`（ENG 起草区）；安装须「监理正/负控复验 → gate 版本 bump → 监理登记 sha」。

## 1. 交付物
| 件 | sha256/16 | 内容 |
|---|---|---|
| `drafts/.../adjudicate.py` | `7cf8a50eb832c284` | 判定器草案：② zone 分母 · ④ pipeline scope · ⑤ refdes 排除 H* · `drill_count` npth_min · 新增 `drc_errors` / `drc_warning_dispositions` / `unconnected_zero` / `fp_lib_table_present` / `keepout_active` |
| `drafts/.../manifest.k2.yaml` | `0da2fb9d173fac2d` | 判据清单 v2 草案（18 检查项，其中 4 项 `enabled:false` + `pending` 理由） |
| `drafts/.../pipeline.yaml.draft` | `3d69d40208bc630e` | k2 域门禁接入草案（**符合 eda_core 管线 schema**：`phases` + 3 项必选 sch 检查 + ④ 段判据机器化表达式）；安装时复制为 `k2/pipeline.yaml` |
| `drafts/.../run_controls.py` | `2ee1e5bdee408b5a` | 正/负控复跑脚本（7 案） |

## 2. 逐项实现
| 裁定 | 实现 | 说明 |
|---|---|---|
| ② `zone_filled` 分母 | 分母 = **有网且非 keepout** 铜区；`keepout_all_allowed` 继续用全量 | 实测 **10/10 PASS**（keepout 8 个另计，不入分母） |
| ④ `pipeline_present` | manifest `scope: k2`；判定器按 scope 过滤，**范围外目录单列**（他项目阶段门判） | 正控：k2 域内 0 缺 + 范围外 1 列出；负控：k2 域内缺 ⇒ FAIL |
| ⑤ `refdes_sets_equal` | 双侧排除 `H\d+`，**逐条列名**入 detail | 实测 `['H1','H2','H3','H4']` ⇒ 55/55 PASS |
| §三-6 `drill_count` | `npth_min: 4`（expect + 代码读取） | 沿用原 `npth >= 1` 会放过 NPTH=1..3，属口径不足 |
| §三-1 J-1 | 新增 `drc_errors`（`--drc-cli` 实跑，缺则 fail-closed）+ `drc_warning_dispositions`（板上 warning 类型 ⊆ manifest 登记） | 实跑 staged 同名 pro（T-8）后解析 JSON |
| §三-2 J-2/V1 | 新增 `unconnected_zero`（同一次 DRC 实跑的 `unconnected_items`） | 与 J-1 共用一次 DRC 调用，避免重复仪器调用 |
| §三-3 J-7 | `fp_lib_table_present`（实现）· **`lib_electrical_level` 已实现并启用** | 消费 W-8 电气级审计 JSON（`--w8-audit-json`）；**审计板 sha16 须 == 受审板**（证据陈旧即 fail-closed）；**实测当前 = FAIL（电气级差异 31 + 仅 pad 名差异 2 ⇒ J-7「电气级 = 0」未达成，与 ⑥⑦ 登记一致）** |
| §三-4 J-8 | `keepout_active`（实现）；`pads_within_outline` / `density_and_clearance` **声明 pending** | 出框需 P3-4 定义 + pcbnew 检查器；密度/间距需 P3 阈值 |
| §三-5 V3 | `ref_plane_continuity` **声明 pending** | 需 pcbnew 侧「段投影 ∩ 相邻层平面多边形 = 全长」检查器（下一增量） |

**剩余 pending（实现设计已定，下一增量落地）**：`pads_within_outline`（J-8 出框）= 解析 `Edge.Cuts` 外框 AABB（内缩 0.3mm）与 pad AABB（矩形/椭圆按旋转精确、圆形按半径）逐焊盘比对；
`density_and_clearance`（J-8 密度/关键间距）= 需 P3 图纸阈值；`ref_plane_continuity`（V3）= 需 pcbnew 侧「高速段投影 ∩ 相邻层平面多边形 = 全长」检查器（新工具）。

**其余 3 项 pending 的处理方式**：manifest 中 `enabled:false` + `pending: <口径/实现路径>`；判定器跳过。**不假装实现、不缩口径、不静默改数。**

## 3. 正/负控实测（7 案，全按设计命中）
| 案 | 输入 | 结果 |
|---|---|---|
| POS-main | 落件板 `6ff49da5` + 仓库 pro + `--drc-cli` | 13P/2F：**唯一实质 FAIL = `pipeline_present`**（`k2/pipeline.yaml` 尚未安装，本草案已备）+ `rule_severity_manifest`（9 条 ignore，由 ③ 处理） |
| POS-pipe-k2scope | 同上 + `--root` 含 `k2/pipeline.yaml` + 他项目 `k1/sch` | **14P/1F**：`pipeline_present` **PASS**（范围外 1 个 `k1/sch` 单列） |
| NEG-pipe-nok2yaml | k2 域内无 `pipeline.yaml` | `pipeline_present` **FAIL** ✅ |
| NEG-zone-l4 | 冻结受审板 `l4`（只读） | `zone_filled` **FAIL 0/9**（分母修正非「一律 PASS」） |
| NEG-refdes-X99 | 落件板改名一件为 `X99` | `refdes_sets_equal` **FAIL**（图有板无 `['C89']` / 板有图无 `['X99']`） |
| NEG-drc-errors | 落件板 + `missing_courtyard=error` | `drc_errors` **FAIL**（error=40） |
| NEG-warn-empty | `drc_warning_dispositions: []` | `drc_warning_dispositions` **FAIL**（未登记 `lib_footprint_mismatch`） |
| J-7b real | 真审计 JSON（33 件 pad 级差异） | `lib_electrical_level` **FAIL**（31+2；J-7 未达成，如实反映） |
| J-7b green | 合成审计（差异 0，板 sha 一致） | `lib_electrical_level` **PASS**（机制可用） |
| J-7b stale | 合成审计（`board_sha16` 不匹配） | **FAIL**（证据陈旧 fail-closed） |
| J-7b none | 未给 `--w8-audit-json` | **FAIL**（缺件 fail-closed） |

复跑：`python3 k2/docs/drafts/K2-P4-criteria-draft-v2/run_controls.py`（cwd = 仓库根）。

## 4. 安装流程（请监理执行；ENG 不安装）
1. 监理以正/负控**复验**本草案（含独立复算）；
2. gate 属主侧以**版本 bump** 安装 `criteria/adjudicate.py` + `criteria/manifest.k2.yaml`（`manifest_version: 2`）；
3. `k2/pipeline.yaml` 落地（k2 域）；
4. 监理登记两份新 sha + 判据锚 `rev=2`；`not_countersigned` 仍由监理签认。

## 5. 落地新发现（④ 的硬约束）
仓库 `k2/_shared/eda_core/pipeline/required.py`（meta-gate，pre-commit 钩子）要求：**含 `.kicad_sch` 的项目必须在 `pipeline.yaml.phases` 的 checks/verify 里声明
`sch_structural` / `netlist_connect` / `bom_consistent` 三项**，且 `config.py` 要求 `phases` 为非空列表、`id` 唯一。
⇒ 本草案已按该 schema 写就（否则**连提交都会被拒**，实测已复现一次）；示例可参 `key_v2/key_v2/pipeline.yaml`。
⇒ 若把草案文件直接放在仓库内且命名为 `pipeline.yaml`，会被 `find_all_projects` 当**第二个 k2 项目**扫到（同名冲突），**故草案以 `.draft` 后缀存放**，安装时才复制为 `k2/pipeline.yaml`。

## 6. 边界
- 未改 `criteria/` 原件（0444 只读，sha `897e8bfd…`/`7ce08757…` 未变）；未改板/SPEC/生成器；未安装 `pipeline.yaml`。
- 本草案**不含**任何新阈值（`thresholds: {}`），只做「已裁维度 → 机器可判表达式」的转写。
