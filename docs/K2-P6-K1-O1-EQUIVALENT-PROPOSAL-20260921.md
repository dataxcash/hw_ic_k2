# K2 · P6 跨板复用：**K1 O1 等价整改提案 + 实测**（2026-09-21 · 监理自动续推轮）

**性质**：提案 + **只读实测**（/tmp 副本）。**未改 `k1/` 任何文件**（`git -C k1 status` 洁净）；未新增判据维/规则；未派 WORKER。

## 1. 同源发现
K2 经 **O1 模板整改**取消的 9 条 `rule_severities=ignore` 与 **`k1/k1_v1.kicad_pro` 现存 9 条同名**：
`copper_sliver · footprint_filters_mismatch · footprint_type_mismatch · missing_courtyard · silk_over_copper · silk_overlap · track_not_centered_on_via · tuning_profile_track_geometries · via_dangling`

- K1 **模板** `k1/tools/k1_jlc_template.kicad_pro`：**ignore=0（已整改）**
- **残项 = 板 pro** `k1/k1_v1.kicad_pro`：ignore=**9**（= `k2_p6_2_acceptance` 报的「k1 侧非模板 pro」信息项）

## 2. 提案（机械可应用）
`K1_O1_EQUIVALENT_PROPOSAL_v1.patch`（`f056d18de0c3c53b`）：**9 行 `"<rule>": "ignore"` → `"warning"`**，与 K2 O1 **同语义**（零新增规则、零新增检查齿）。
目标件：`k1/k1_v1.kicad_pro`（`d6528227fc9aa763` → 打补丁后 `f9d1d8e63fc5d499`）。应用需 **K1 项目授权**（跨项目改动）。

## 3. /tmp 实测（真判定器 · 现行 `criteria/manifest.k1.yaml` c175be51 · countersigned）
| 维 | 前 | 后 |
|---|---|---|
| `rule_severity_manifest` | **FAIL**（未登记 ignore 9/62，9 条具名） | **OK（0/62）** |
| `drc_errors` | error **13** · 违规总 **30** | error **13（类型不变）** · 违规总 **90**（+60 条原被 ignore 的 warning **保持可见**） |
| `drc_warning_dispositions` | OK（已登记 2 类） | **OK（0/5 未登记）** — 新暴露的 `missing_courtyard`/`silk_over_copper`/`silk_overlap` **已在 K1 manifest 登记** ⇒ **无需新增登记** |
| 合计 | n_pass **5** / n_fail **13** | n_pass **6** / n_fail **12** |

**Δ = +1 维修复 · 0 维新增失败 · error 数不变 · 零新增登记需求**；两次全新 `--drc-work-dir` 跑 verdict **逐字节同**（`7a648a2e12dfbddd`）。

## 4. 后果与边界
- 改 `k1/k1_v1.kicad_pro` ⇒ 该件 sha16 变更 ⇒ **K1 项目自身**的 pro 锚/读数需重新基线（K1 项目面，**非 K2 交付**）。
- 整改后 K1 DRC 多暴露 60 条 warning（**保持可见、登记制**）——**未新增任何规则**，不触 owner ②（禁新增检查齿）。
- K1 实质缺陷（13 error · unconnected 156 · 缺 `fp-lib-table` · `k1/sch` 无 pipeline · NPTH=2<4 …）**不受本整改影响**，仍属 K1 自身 P4 工作。
- 本件**不改 k1 仓库**；应用与否 = **监理裁定**（跨项目改动）。

## 5. 交件
`K1_O1_EQUIVALENT_PROPOSAL_v1.json`（`f46121fc8c648e0b`）· `K1_O1_EQUIVALENT_PROPOSAL_v1.patch`（`f056d18de0c3c53b`）
