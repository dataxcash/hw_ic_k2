# K2 · P4 · **判据「19 维」正/负控现状汇总 ＋ 清单归属复核草案** · v1 · 2026-09-18

> 缘起：handoff inc71 §6-3-(aa)「把 v4 判定器 19 维各自的正控/负控现状汇总为一张可裁表（纯只读汇总，接既有 v3/v4 草案文档）」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读汇总**，仓库零载体改动（仅新增本证据件）。
> 锚：`criteria/manifest.k2.yaml` **`7ce08757eff25557`**（9 维、在库、`not_countersigned: true`）· v2 草案 `manifest.k2.draft-v2.yaml`（17 维）· v3 草案 `manifest.k2.draft-v3.yaml`（18 维）· **v4 安装候选 `manifest.k2.v4.yaml`（18 维 / 16 enabled）** · **v4 控制件 `manifest.k2.control-v4.yaml`（18 维 / 全 enabled，示例阈值）** · 判定器 `adjudicate.draft-v4.py` **`1cda68521d0e56be`**。
> **归属**：清单与阈值/口径＝**监理**；本件只做只读汇总与结构复核，**不新增检查齿**（owner ②）。

## 0. 结论（四条，含两项结构发现）

1. **【结构发现 1】现存 4 份判据清单，维度数互不相等**：在库安装件 **9** 维（`not_countersigned: true`，唯一实际在岗口径）· v2 草案 **17** · v3 草案 **18** · v4 安装候选 **18（16 enabled）**／v4 控制件 **18（全 enabled）** ⇒ **安装前须由监理指定唯一 canonical 清单 + 锚 rev**，否则「19P/0F」在跨件引用时不可复现。
2. **【结构发现 2】两族命名不一致**：v4 族与 v3 族对**同一语义**使用**不同维名**（见 §2 对照表，如 `lib_electrical_level` ↔ `lib_footprint_electrical`、`density_and_clearance` ↔ `density_and_spacing`、`ref_plane_continuity` ↔ `v3_reference_continuity`、`drc_warning_dispositions`(复数) ↔ `drc_warning_disposition`(单数)）⇒ 两族的维数**不可直接相加**，且**别名映射须钉死**。
3. **【「19」的构成】**：17P/0F rehearsal 的 **19 PASS = v4 控制件的 18 维 ＋ `rule_severity_manifest`** —— 后者在 `adjudicate.draft-v4.py:248-254` 为**无条件执行**（仅以 `meas['rule_severities'] is None` 作 fail-closed，**无 `C.get(...).enabled` 守卫**），即**不在 `checks` 清单内、无法由 manifest 关闭**。⇒ 监理须明确：把它**纳入清单**（可开关）还是**登记为无条件维**（并说明理由）。
4. **2 维 `enabled:false` 只差阈值**：`density_and_clearance`（键：`cell_mm`/`cell_origin`/`max_fp_per_cell`/`min_copper_clearance_mm`/可选 3 键）与 `ref_plane_continuity`（`scope`/`min_coverage`）；两维**机制已实现且有正负控装置**（`run_controls_v4.py` 七案 A–G / V3 nominal-strict 两口径），**给阈值即可启用**。

## 1. 19 维状态与正/负控证据（只读汇总）

| # | 维度 | 族/来源 | 在库安装件? | enabled（v4 候选） | 正控证据 | 负控证据 |
|---|---|---|---|---|---|---|
| 1 | `zone_filled` | 冻结（P1） | ✅ | ✅ | inc62 KiCad 级 `zone_filled 10/10` | 冻结期负控（闭环表 F 段） |
| 2 | `device_has_pads` | 冻结 | ✅ | ✅ | 55 件全 ≥1 pad（板实测） | 见 `K2-P4-MANIFEST-COMPLETION-SUBMISSION-v1.md` |
| 3 | `drill_count` | 冻结 | ✅ | ✅ | 4×NPTH Ø3.2（inc63 NPTH 件实测） | 删孔 ⇒ FAIL（闭环表 M-11） |
| 4 | `net_declared_realized` | 冻结 | ✅ | ✅ | 真源网集落地（P2 归零件） | **控制语境命中件 = 0（待补/散见）** |
| 5 | `pin_map_complete` | 冻结 | ✅ | ✅ | 板 pad↔引脚全映射 | 见 `drafts/p4-manifest-completion-v2/README.md` |
| 6 | `non45_segments` | 冻结 | ✅ | ✅ | 实测 0 条非 45° | 见 `K2-P4-MANIFEST-COMPLETION-SUBMISSION-v1.md` |
| 7 | `refdes_sets_equal` | 冻结 | ✅ | ✅ | 55 == 55（P2 归零） | **改名 `X99` ⇒ FAIL**（闭环表 M-01 ④） |
| 8 | `pipeline_present` | 冻结 | ✅ | ✅ | 装件后存在性 PASS | **缺 `pipeline.yaml` ⇒ FAIL**（inc46/57 矩阵） |
| 9 | `verdict_schema` | 冻结 | ✅ | ✅ | 各件无 `verdict` 键 | 见 `K2-P1-criteria-execution-evidence.md` |
| 10 | `drc_errors` | 草案 | ❌ | ✅ | DRC 违规 0（l5 pro） | 见 `K2-P4-CRITERIA-DRAFT-AND-MANIFEST-V2.md` |
| 11 | `drc_warning_dispositions` | 草案 | ❌ | ✅ | 75 条 warning 已登记（courtyard/lib 类） | 同上 |
| 12 | `unconnected_zero` | 草案 | ❌ | ✅ | 未连接 0 | 同上 |
| 13 | `fp_lib_table_present` | 草案 | ❌ | ✅ | 库表 `d7316388…` 存在 | **四案**：real→PASS / 缺失或陈旧→FAIL（J-7 件） |
| 14 | `lib_electrical_level` | 草案 | ❌ | ✅ | **W-8 三案**：⑦ 候选 → 0 差异 | 基线 33 件逐件相同（不放松）· 合成负控恰 `['C73']` |
| 15 | `pads_within_outline` | 草案 | ❌ | ✅ | pad AABB 全在框内 | 见 P3-4 出框件 / `K2-P4-J8-V3-MEASUREMENT-AND-M02-DOC-FIX-v1.md` |
| 16 | `keepout_active` | 草案 | ❌ | ✅ | inc62/63：8 keepout、0 个全 allowed | 闭环表相关行 |
| 17 | `density_and_clearance` | 草案（**pending 阈值**） | ❌ | **❌** | `run_controls_v4.py` 七案 A–G（示例阈值） | 同上（含负控造件） |
| 18 | `ref_plane_continuity` | 草案（**pending 阈值**） | ❌ | **❌** | V3 名义口径 `3653/3653` | **strict 口径 ⇒ 83.5%（`≥1.0` 不可同时成立）** |
| 19 | `rule_severity_manifest` | 判定器**无条件** | ❌ | **不受 `checks` 控制** | l5 pro `ignore = 0` ⇒ PASS | l4 板 **9 条 ignore ⇒ FAIL**（deny-by-default 负控） |

> 「控制语境命中件 = 0」的第 4 项（`net_declared_realized`）＝本件只读扫描未找到带「正/负控」措辞的记录 ⇒ **标记为待补**，不假设已有证据。

## 2. 两族命名对照（同一语义、不同维名）

| v4 族 | v3/v2 族 | 备注 |
|---|---|---|
| `lib_electrical_level` | `lib_footprint_electrical` | J-7 电气级 |
| `density_and_clearance` | `density_and_spacing` | J-8 密度/间距 |
| `ref_plane_continuity` | `v3_reference_continuity` | V3 参考平面连续性 |
| `drc_warning_dispositions` | `drc_warning_disposition` | 仅复数/单数之差 |
| `pads_within_outline` | `board_frame_and_keepout`（部分语义） | v3 侧把板框/keepout 合并命名 |
| `keepout_active` | （v3 侧无同名项） | v4 新增 |
| `—` | `gerber_plane_g36` | v3 新增（平面落图前置） |
| `—` | `board_frame_and_keepout` | v3 新增 |
| `rule_severity_manifest` | `rule_severity_manifest` | 两族同名；v4 判定器**无条件**执行 |

## 3. 复跑（只读）

```bash
cd /home/fila/jqdDev_2025/ic_hw
# 清单维度与开关（4 份）
python3 - <<'PY'
import yaml
for f in ('criteria/manifest.k2.yaml','k2/docs/drafts/p4-manifest-completion-v2/manifest.k2.draft-v2.yaml',
          'k2/docs/drafts/p4-manifest-completion-v3/manifest.k2.draft-v3.yaml',
          'k2/docs/drafts/p4-j8-density-clearance-v1/manifest.k2.v4.yaml',
          'k2/docs/drafts/p4-j8-density-clearance-v1/manifest.k2.control-v4.yaml'):
    d=yaml.safe_load(open(f)); ck=d.get('checks') or {}
    print(f"{f.split('/')[-1]:34s} 维度={len(ck):2d} enabled={sum(1 for v in ck.values() if v.get('enabled')):2d}")
PY
# 「19」构成：v4 控制件 18 维 + 无条件维
grep -n "rule_severity_manifest" -B3 -A6 k2/docs/drafts/p4-j8-density-clearance-v1/adjudicate.draft-v4.py | head -20
```

## 4. 边界

本件**只读汇总**：未改判据/SPEC/生成器/板/pro/真源/图纸/模板/库/`fp-lib-table`/`pm_gate/**`/`criteria/**`/`_shared/**`/闭环表；
**未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`**；未落件；未出 Gerber；未派 WORKER；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 判定器草案 `1cda68521d0e56be` · 在库清单 `7ce08757eff25557`
