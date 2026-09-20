# K2 · P6 跨板复用：**K1 机制类覆盖包（3 件）+ 镜像实测**（2026-09-21 · 监理自动续推轮）

**性质**：提案 + **/tmp 镜像实测**。**未改 `k1/` 任何文件**（`git -C k1 status` 洁净）；未新增规则/判据维；未派 WORKER。
**范围依据**：计划 §1.3 #7「**K1 当前『未布线』状态本身不是缺陷**；只覆盖其**机制缺陷**（模板/门禁/接线/sheets）」+ §⑦ 跨板复用。

## 1. 覆盖包（3 件，均为 K2 已落件修法的同源复用）
| ID | 目标件 | 形式 | K2 同源 | 修复的判据维 |
|---|---|---|---|---|
| **K1-M1** | `k1/k1_v1.kicad_pro` | 9 行 `ignore→warning` | K2 批 3 ④ **O1 模板整改**（已落件） | `rule_severity_manifest` |
| **K1-M2** | `k1/fp-lib-table`（**新建**） | 3 行 fp_lib_table：注册 `ForgeOS` → `${KIPRJMOD}/lib/ForgeOS.pretty`（**K1 库目录已存在**） | K2 对应件 `k2/hw/fp-lib-table`；缺陷册 **M-10**（无 fp-lib-table ⇒ ForgeOS 未注册） | `fp_lib_table_present` |
| **K1-M3** | `k1/pipeline.yaml`（**新建**） | preflight `project_sch_coverage`；verify `sch_structural` + `netlist_connect`→`boards/k1_sch.yaml`（样例**未含** `bom_consistent`：K1 仓无 BOM csv，须 K1 侧定） | K2 对应件 `k2/pipeline.yaml`；缺陷册 **M-13**（无 pipeline.yaml ⇒ 门禁从未运行） | `pipeline_present` |

样例件：`K1_fp-lib-table.sample`（`13ddfa53…`）· `K1_pipeline.yaml.sample`（`eaff19fe…`）· `K1_O1_EQUIVALENT_PROPOSAL_v1.patch`（`f056d18d…`，上一轮）。

## 2. 镜像实测（真判定器 · 现行 `criteria/manifest.k1.yaml` `c175be51` countersigned · 真源零改）
| 步骤 | n_pass | n_fail | 翻转的判据维 |
|---|---|---|---|
| 现行 K1（基线） | **5** | **13** | — |
| + O1 | 6 | 12 | `rule_severity_manifest` |
| + fp-lib-table + pipeline.yaml | 7 | 11 | `fp_lib_table_present` · `pipeline_present` |
| **三件齐** | **8** | **10** | **上面 3 维全 OK** |

**副作用 = 0**：`drc_errors` 仍 **13 error（类型不变）**；`drc_warning_dispositions` 仍 **OK**（O1 新暴露的 3 类已在 K1 manifest 登记）；其余 FAIL 维逐项不变。原始读数：`fp-lib-table @ <mirror>: 存在` · `含 .kicad_sch 但无 pipeline.yaml 的目录 0 个` · `未登记豁免的 ignore 0/62`。

## 3. K1 剩余 FAIL 的分类（**如实区分机制 vs 板级**）
| 维 | 类 | 说明 |
|---|---|---|
| `unconnected_zero` 156 | **板级/布线推进** | 计划 §1.3 #7 明示**不是缺陷** ⇒ K1 P4 面 |
| `drc_errors` 13（5 类）· `zone_filled` 0/0 · `keepout_active` 0 · `drill_count` NPTH 2<4 · `pads_within_outline` 2（`J1` pad `SH`） | 板级几何 | 不受机制包影响；K1 自身整改 |
| `refdes_sets_equal`（图 37 / 板 42；板有图无 5 件）· `net_declared_realized` · `pin_map_complete` | 输入/来源一致性 | 同 K2 **E1 四源对账**族（K2 已归零）；K1 须回上游对账 |
| `density_and_clearance`（缺测量件 fail-closed） | 工具接入 | K2 已有 J-8 测量生产者可复用 |
> ENG 独立复核与判定器一致项：PTH **28**（0.4×12 · 0.8×10 · 1.7×2 · 槽 0.5×1.1×4）· NPTH **2**（Ø0.65×1 · 槽 0.95×0.65×1）· 板 **42** refdes · **0** zones / **0** keepout · 无 `fp-lib-table` / 无 `pipeline.yaml`。

## 4. 边界
- 三件落件属**跨项目改动 ⇒ 需监理裁定**；落件后 **K1 自身锚需重基线**。
- 本件**未动 k1 仓库**（`k1/k1_v1.kicad_pro` 仍 `d6528227fc9aa763`）；不改任何生产件。
- 不触 owner ②（**未新增任何规则/检查齿**，仅取消 9 条 deny-by-default 的 ignore + 接上门禁/库表）。

## 5. 交件
`K1_MECHANISM_COVERAGE_BUNDLE_PROPOSAL_v1.json`（`70930aff60101c26`）· `K1_fp-lib-table.sample`（`13ddfa5331d67e13`）· `K1_pipeline.yaml.sample`（`eaff19fedec99811`）
