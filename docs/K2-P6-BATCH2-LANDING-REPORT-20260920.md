# K2 · 学习环**批 2 落件报告**（S1–S5 一笔）· 2026-09-20 · 放行件 #K2-41

> 范围：`#K2-41 §三` 批准批（G-c 开闸）+ `§四` 验收。**P6 交付阶段仍关**（未启动 P6-1/P6-2）。
> 真源 = 两份同源检出 `k2/_shared`（K2 框架）与容器 `_shared`（K1 框架，`k1/_shared -> ../_shared`）；落件后**逐字节同**。

## 0. 一步到位读数（fail-closed 门，全为 ENG 实跑）

| 门 | 命令 | 读数 | 判 |
|---|---|---|---|
| **G-d 交付链** | `cd k2 && PYTHONPATH=$PWD/_shared:$PWD python3 _shared/eda_core/pipeline/engine.py verify k2` | `preflight`+3 全 PASS（`project_sch_coverage` / `sch_structural` / `netlist_connect` / `bom_consistent`） | ✅ 不回退 |
| **canonical 19 维** | `python3 criteria/adjudicate.py --project k2 --board k2/hw/k2_v4_8L.l7.kicad_pcb --pro …l7.kicad_pro --nets k2/hw/data/k2_sch.errata-2.yaml --sch-dir k2/hw/sch --root . --drc-cli AppDir/bin/kicad-cli --drc-work-dir <全新> --w8-audit-json/--pads-outline-json/--v3-plane-json/--refplane-gap-json/--density-json/--min-clearance-json = `L4/E3-standard-call-l7-20260919/` 六件` | **19 OK / 0 FAIL** · `passed=true` · `provisional=false` · `zone_filled 10/10` · `drc_errors 0` · `unconnected 0` · `verdict sha256[:16] = 190b73be0f728a56` | ✅ 与在岗签认件**逐字节同** |
| **两跑逐字节同** | 上条连跑 2 次（`/tmp/opencode/canon19_verdict_run{1,2}.json`） | `cmp` **byte-identical**（sha16 `190b73be0f728a56` ×2） | ✅ |
| **变更后验收门** | `AppDir/bin/python3.11 k2/tools/k2_p6_acceptance_gate_v1.py --expect-patched` | `A 4/4` · `B PASS` · `C K1=14 / K2=14 PASS` · **`regressions=0`** · `D shadow hidden_failures=2`（具名 C1/C2） | ✅ **PASS** |
| **影子（施工后期望态）** | `AppDir/bin/python3.11 k2/tools/k2_p6_shadow_verify_v1.py` | **pytest 61 PASS / 2 FAIL / 12 SKIP** · 对照组同（`same_result=true` ⇒ 零测试回归）· 唯二 FAIL = `test_board_level_consistency`(C1) + `test_chain_no_pn_zero_spacing`(C2) | ✅ 具名保持 RED |
| **b2t 复现归档** | `python3 k2/tools/k2_p6_b2t_draft_patch_v1.py --verify-determinism` | 五树 base 43/13 · anchor 41/15 · draft 57/6 · **draft_b1 61/2** · negctl 45/18 · **牙齿 12/12** · **确定性 MATCH** | ✅ 施工前唯一剩余风险已消除 |

## 1. 落件清单（同批一笔；禁零散补丁 C-6）

| # | 件 | 变更 |
|---|---|---|
| S1 | `_shared/eda_core/hs_route_model.py` | **B1** 空序列 → `None` + cap_wall `None` 守卫（link_topology 崩溃 → `CROSSING_FOUND[UP4..UP7]`）· **B2** CLI 层包装 ⇒ `status=INFRA_ERROR` + **rc=3**（≠1「正常未解」）· **B3** `--capacity-map` 总判 = worst-of(region, corridor)（吞数 → `INSUFFICIENT` + `insufficient_corridors`）· **B4** `_corridor_clear_span` x_range 形状校验 ⇒ 引擎 sha16 **`8f9bd6c7fa033039`** |
| S3 | `_shared/eda_core/tests/test_hs_route_model.py` | **A1–A12** 期望/输入重锚（**混合锚**）· **A13/A14/A15** 合成现行 fixture 补覆盖 · 锚改**现行 pipeline alloc 具名冻结载体** |
| S3 | `k2/pm_gate/artifacts/k2_v4/L3/model_solves/pipeline_alloc_current_v1/{alloc.json,LINEAGE.json}`（新） | 冻结载体（34 条）+ 血缘：内容 sha16 `547c9513ff67b470` · 引擎 sha · SPEC sha · 板 sha · 生成命令 · 两跑逐字节同 |
| S3 | `…/channel_alloc_v2/RETIRED.md`（新） | 遗留锚标 **RETIRED**（仅标注，禁再作锚；N-05 卫生） |
| S2 | `_shared/pm_gate/{check_l1,check_l2,check_l3,check_qa,gates,closure_check}.py` | 影子已验 11 项：项目维度注入 + SPEC 名去硬编码 + `check_qa` 板路径 + `closure_check` 默认值 → 项目根 |
| S2 | `_shared/pm_gate/{check_l3,review,freeze_wp1,tools_escape_predict,config}.py` | **#K2-41 §三-⑦**：G3.1 期望集 = **项目域派生**（`project.yaml: l3_spec_fields/l3_spec_expects`；K1 不再被要求 K2 专有键 `capacitor_walls`）· 走廊期望 = **现行 id** `EAST_CHIP_TO_J2`/`WEST_MCIO_TO_CHIP` · G3.2 内容期望 = 项目域 · G3.5 判定源 = `config.spec_name(active)` · 余 4 处写死 SPEC 名去硬编码 |
| S4 | `k2/pm_gate/project.yaml` | `board_path` → **`hw/k2_v4_8L.l7.kicad_pcb`**（G4 施工对象 = 规范裁定板；旧别名 → 设计源板不得作 G4 对象）+ 项目域期望集声明 |
| S4 | `k1/pm_gate/project.yaml` | 同（K1 自身 8 字段集，无 `capacitor_walls`） |
| S4 | 27 件 HIST 脚本 | 血缘头标注（类别/作者期板/别名风险；含旧字面量者标**不可重放**）——**零行为改动** |
| 工具 | `k2/tools/k2_p6_shadow_verify_v1.py` | ① 补丁**幂等**（落真源后不再断言命中）② **C-19**：`run_pytest` cwd = 影子树根 + `eda_core` 影子链接（AppDir python 重写 `PYTHONPATH`）+ conftest provenance 断言 |
| 工具 | `k2/tools/k2_p6_acceptance_gate_v1.py` | D 腿期望值修正：隐藏失败须**恰为具名例外 C1/C2**（#K2-41 §三-④；**非**缩口径——原「==0」是对既有能力缺口的旧期望） |

## 2. 逐处定性（禁一把梭 · C-12）

- **SPEC 站点普查 43 处**（`SPEC_SITE_CENSUS_v1.json`）已按类定性：`NAME_ONLY_HARDCODE` 6 处**全部项目化**（check_l3 ×2 / review ×2 / freeze_wp1 / tools_escape_predict）；`STALE_LEGACY_BASE` 4 处中与门禁相关的 `closure_check` 已项目根化（其余 `cap_wall_*`/`wp1_semantics_check` 非本轮判据面，**未动**，留档）；`DOCSTRING_MESSAGE`/`CLI_CONTRACT`/`TEST_ANCHOR`/`NEGATIVE_CONTROL`/`PROJECT_CONFIG` 属正当项，**不改**。
- **走廊命名同步面**：`check_l3.SPEC_EXPECTS` **2 处** → 现行 id（改名承接，**禁双名**，`#K2-41 §三-⑦`）。测试文件旧 id 共 **37 处**：A1–A12 已同步**真源承载 10 处**；余 **27 处 = 合成 fixture `_ECO1_SPEC` 自洽命名**（非真源 SPEC id，改名无判定意义）+ **3 处 = A1/A3 内的映射说明注释**（有意保留，记录旧→新角色）。⇒ 属**逐处定性**，非漏改。
- **G3.2 期望口径（具名披露）**：期望 token = `config.spec_name(active_project())` 的**基名**（去 `.<rev>` 后缀）。依据：L3 产物以基名指称 SPEC（K1 `L3/SPEC_k1.json`；K2 `SPEC_k2_v4.json`），rev 后缀由 `project.yaml` 承载。若用精确 rev 名 ⇒ K2 `G3.2` 由 PASS 变 FAIL（**违反同件 §四「零回退」**）；基名口径**仍为项目域**（K1 无法被 K2 名满足），且不动任何产物件。

## 3. 红线自检

冻结四源原件未改（`l4 d4e81f64` / 设计源 `fb07d25a` / `k2_sch dd794c54`）· 交付锚未动（`MANIFEST 6ee7495d` / tarball `0e88e107` / 受审板 `l7 c5a7df90` / `l7.kicad_pro 33b4eb6c`）· `criteria/` **只读未动**（rev=3 `eb244d81 / 1937a40a / e2b49fdd`）· 不重建包 · 不放松 DRC 下限 · 未连接 0 / error 0 / zone_filled 10/10 未回退 · `skipped` 未充绿 · C1/C2 未改绿 · **未派 WORKER** · 临时件仅 `/tmp/opencode` · 未写 `.omo/supervision/**`。

—— ENG（ARCHER）· 2026-09-20 · 放行件 **#K2-41** · 批 2 落件完成，**P6 交付阶段仍关闭**

## 4. S3 收口：批 2 残留 **12 个 SKIP** 逐条具名（`skipped 不得充绿`）

施工后 pytest = 61 PASS / 2 FAIL（具名 C1/C2）/ **12 SKIP**。12 项**全部**同一 skipif 族（`BASELINE_PCB.exists()`，基线板 = `/tmp/opencode/boards/k2_m9demo.kicad_pcb`，**不在库**）⇒ 结构上仍可能「skip 充绿」，故逐条定性：

| skipif 站点 | 用例数 | 打的 API | 该 API 是否仍在引擎 | 该 API 的**其他**测试覆盖 |
|---|---|---|---|---|
| `:171` `test_up4_input_segment_solved` | 1 | `solve_pair_segment` | ✅ 在册 | **0**（覆盖真空） |
| `:195` `TestV2CorridorDeterministic` | 3 | `solve_chain_v2` | ✅ 在册 | **0** |
| `:217` `TestV2PairSymmetry` | 2 | `_pair_expand` | ❌ **引擎已删**（解锁必 AttributeError） | 0 |
| `:237` `TestV2RefclkIn6` | 2 | `solve_chain_v2` | ✅ 在册 | 0 |
| `:269` `TestV3EscapeIn2` | 4 | `solve_chain_v2` | ✅ 在册 | 0 |

- 基线三件套**全部非现役**：`/tmp` 板（**不在库**、仓库无生成器 ⇒ N-05「生成物不可复跑」同族）+ 6L 旧 `SPEC_k2_v4.json`（README-canonical 标「陈旧读取」）+ `channel_alloc_v2`（本批已标 **RETIRED**）。
- 结论：**10 项**打**仍在册**的 `solve_pair_segment` / `solve_chain_v2`，且这两个 API **仅有这些被跳过的用例覆盖** ⇒ 属**覆盖真空**（非「已被新套件取代」）；**2 项**打**已删**私有 API。
- 处置四选（**监理裁**）：**S1** 具名接受（登记退役 + 显式登记覆盖真空）· **S2** 补 fixture 生成步骤（涉生成器/SPEC/冻结件）· **S3** 随代际退役删 API（共享层改动）· **S4** 重锚到现役 8L 基线（期望重基线）。
- 机读：`P6_execution/BATCH2_SKIP12_DISPOSITION_v1.json`（`fdbb8f3a0…`）。ENG **未改**测试/引擎/记录件。

## 5. 套件级回归基线（新增 · 逐用例对比）——批 2 **零回退，净修 11 项**

K2 此前只有**单文件** PYTESTERS（`test_hs_route_model.py`）。本件首次做**全量套件**逐用例对比：

| 观测 | 批 2 前（`k2/_shared@935fb25` 经 `git archive` 解到 /tmp） | 批 2 后（`fc59771` 影子） | Δ |
|---|---|---|---|
| 用例总数 | 555 | 562 | **+7**（A13/A14/A15 合成覆盖） |
| passed | 492 | 510 | **+18** |
| failed | **42** | **31** | **−11** |
| skipped | 21 | 21 | 0（**集合逐条相同**） |
| **新增失败** | — | **0** | ✅ 零回退 |
| **新增跳过** | — | **0** | ✅ |

- **修复的 11 项** = B2-T 13 项 − 具名保持 RED 的 C1/C2（`test_probe_escape_capacity_dn0` · `test_probe_reports_via_gap_fact` · `test_capacity_regions_derived` · `test_probe_region_capacity_structure` · `test_capacity_map_persist` · `test_corridor_clear_span` · `test_link_topology_crossing_old_topology` · `test_correct_polarity_solves_clean` · `test_drawing_only_refuses_no_node` · `test_escape_deterministic_byte_identical` · `test_flip_polarity_cross_rejected`）。
- **残留 31 项失败**（`base` 同有，**不在批 2 放行范围**）分布：`test_closure_check` 5 · `test_verify_checks` 6 · `test_redteam_evidence` 6 · `test_env_fingerprint` 4 · `test_verify_cli_cache` 4 · `test_verify_cli_smoke` 3 · `test_solve_pipeline` 1 · `test_hs_route_model` 2（= C1/C2）⇒ 建议入账为**套件级既有失败基线**交监理排期。
- **21 项 skip 分类**：**17 项 = `k2_m9demo` 基线板不在库**（`test_hs_route_model` 12 · `test_ls_migration` 3 · `test_drc_locator` 2 ⇒ 比先前只知 `hs_route_model` 12 更广）+ 4 项其他（K2 真实工件缺失 ×2 · K2 真源数据缺失 ×1 · 影子树无 git HEAD ×1）。
- **口径**：解释器必须 `AppDir/bin/python3.11`（ambient `python3` 会在 3 个模块 `ImportError: pcbnew`）；命令 `-m pytest -q --tb=no -p no:cacheprovider --junitxml=<out> shared/eda_core/tests/`；全量与单文件跑法结论一致（无顺序依赖差异）。
- 机读：`P6_execution/SUITE_BASELINE_AND_BATCH2_DELTA_v1.json`（`9e5ec990e…`）。

### 5.1 ⚠ 套件级发现：**同一测试文件在两种检出布局下行为不同**（22 项静默 skip）

| 布局 | cwd | passed | failed | skipped |
|---|---|---|---|---|
| **k2 检出布局**（影子树） | 影子树根 | 510 | 31 | 21 |
| **容器根布局**（框架基线工具 `k2_p6_readonly_baseline_v1.py` 的口径） | `REPO` | 492 | **28** | **42** |

- **归因**：`K2V4_REAL_BOARD = REPO / "k2_v4.kicad_pcb"`（`REPO=parents[3]`）——在 **k2 检出**下 = `k2/` ⇒ 命中 8L 板；在**容器 `_shared` 检出**下 = `ic_hw/` ⇒ 该路径**恒不存在** ⇒ **22 项（含 B2-T 全族）静默 skip**。同文件注释本就要求「两处 checkout 必须同一解析」，`K2V4_SPEC`/`K2V4_ALLOC` 已用绝对锚，**仅板锚漏改**。
- ⇒ **框架自身的基线工具读到 mask 视图**（`tests.test_hs_route_model`: 41 passed / **34 skipped**），验收门 C 腿的 pytest 基线因此低估。
- 差集完全可归因：natural-only skip **22 项全在** `test_hs_route_model`；shadow-only failure 3 项 = C1/C2（natural 下被 skip 掩盖）+ `test_env_fingerprint::test_default_paths_repo_relative_no_tmp`（影子根非 git 仓库的环境差，**非产品缺陷**）；shadow-only skip 1 项 = `test_verify_cache::test_init_cleanup_auto_git_head`。
- **备料（未落件，C-6：批 2 已落 ⇒ 建议并入下一批）**：1 行锚修（`K2V4_REAL_BOARD` → 绝对锚）+ **配套 2 行**（影子工具板锚补丁改容忍，否则验收门 D 腿会 AssertionError）；`patch -p3 --dry-run` 已过。
  预期（容器根布局）：**passed 492→512 · failed 28→30（新增 = 具名 C1/C2）· skipped 42→20**；k2 检出版零变化。
- 机读：`P6_execution/SUITE_LAYOUT_ASYMMETRY_AND_ANCHOR_FIX_v1.json` + `P6_OPEN_READINESS/anchors/K2V4_REAL_BOARD_absolute.diff`。
