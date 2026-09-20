# K2 · **批 3 落件报告**（#K2-42 全量放行 · S1→S8） · 2026-09-20 · ENG（ARCHER）

- 放行件：**#K2-42**（批 3 全量放行 + P6-1 `sheets_empty`=R1 + G-c2 监理落件 + C-20 自纠）；判据锚 **rev=3（MATCH）**。
- 执行序：`k2/docs/K2-BATCH3-ONE-SHOT-SEQUENCE-v1.md`（S1→S8，含 S3b + ⑫-F0）。
- commit：k2 = **本件所在提交**（落件前 `f308222`）· k1 `dc720fd`（前 `16d7b7c`）· 容器 `_shared` / `k2/_shared` 均 `443dc23`（前 `fc59771`，**两检出同 commit id ⇒ 内容逐字节同**）。

## 逐步读数（全部实测）

| 步 | 事项 | 落件面 | **实测读数** |
|---|---|---|---|
| S1 | 板锚修（两处 `_shared`，`-p3`）+ 同伴件（`k2`，`-p1`） | `test_hs_route_model.py` `94447d3d3ee6b69f`（= 备料预测值）；`k2_p6_shadow_verify_v1.py` `f4bacc61ea9fb80a` | 容器根布局 **512P/30F/20S**（= 期望）；**逐用例状态变更 0**（对前基线 `natfix_real_post.xml`）⇒ 回退 0 |
| S2 | 密度工具空集守卫（`k2`，`-p1`） | `measure_density_and_clearance.py` `ff763e6865bac843` | K2 `l7` 密度件 **两跑逐字节同 = `95034499aad26454`**（= 册内值）⇒ **零扰动**；K1 `k1_v1.kicad_pcb` **rc=0**（原崩），`process_min` = `{min_track_width_mm:null,n_tracks:0,min_via_*:null,n_vias:0,min_hole_drill_mm:0.4,n_holes:30}` |
| S3b | C-19 conftest provenance 守卫（两处 `_shared`，`-p3`） | `conftest.py` `06ed4d3a21097bc0` | 合法布局照常（512/30/20 于 cwd=容器根）；**cwd=/tmp ⇒ RuntimeError「C-19 provenance 失败」**（假绿路径被封） |
| ⑫-F0 | `test_topology_gate.py` SPEC 路径锚 → 容器绝对锚（两处 `_shared`，`-p3`） | `c74a4d20f936e73c`（= 备料 after 值） | t5 **仍 skip**（板/links 仍缺，符合「只修路径锚」设计）；状态变更 0 |
| S3 | **B2-1** pad 契约显式化 + **B2-2** 项目维度分派显式化（两处 `_shared`） | `hs_route_model.py` `8f9bd6c7fa033039` → **`dcd1f65f4b549527`** | 第 0 步行号复核 = 范围界定件（4519/4412/4705/4811/4821/:43）；新增契约测试 **10 passed**（正控 + **负控**：pad 真源冲突 ⇒ 显式登记 `PAD_GEOM_MISMATCH`；维度缺失 ⇒ `ValueError`，**非静默取 K2**）；`py_compile` OK |
| S4 | P6-2 模板整改 **O1**（k2 五件 + k1 一件，`-p2`） | 6 件 .kicad_pro 全落 | k2 受控集 **结构差异 3→0**；两模板 ignore 集 **∅ == 应然集 ∅** ⇒ `k2_p6_2_acceptance_v1.py --expect-zero` **PASS**（k1 非模板 pro 的 9 项 ignore 属 **K1 manifest** 裁定面＝信息项） |
| S5 | B2-4 撤 K1 `G1.5` WAIVER（**L1 钉 sha 覆盖**） | `k1_closeout_l2_v1.py` `7a27fdc19665334c` · `state_k1.json` `05ee9799023bd5cd`（均 = 演练产出钉定值，先副本复算再覆盖） | 复跑工具 ⇒ **already/already**；`check_g15()` ⇒ **passed=True**，evidence=「结构预检 + 工艺常识强条全 PASS（3 份报告）」（**两跑同文**）；`evidence_waiver_archived` 留痕在册 |
| S6 | SKIP 处置登记（A→S1 · B→F2 · C→S3/S4） | `BATCH3_SKIP_RETIREMENT_SIGNOFF_v1.json` | `k2_skip_registry_check_v1.py` ⇒ **实测 skip 20 · 登记 20 ⇒ 未登记 0** **PASS**；覆盖真空 `solve_pair_segment`/`solve_chain_v2` 在册；C 类**不退役** |
| S7 | **G-c2** `criteria/manifest.k1.yaml`（**监理/gate 属主**） | 已落地（属主 `ic_hw_gate`，444/555），`not_countersigned:false` + `countersigned_by=监理(OpenCode) #K2-42` | `adjudicate.py --project k1` 不再 fail-closed；k1 verdict `provisional=False` |

## S8 收尾四验（**全 PASS**）

| # | 验收 | 命令 | 读数 |
|---|---|---|---|
| ① | 交付链 | `cd k2 && PYTHONPATH=$PWD/_shared:$PWD python3 _shared/eda_core/pipeline/engine.py verify k2` | `preflight`+3 **PASS** |
| ② | canonical 19 维（**全新 `--drc-work-dir` ×2**） | `criteria/adjudicate.py --project k2 … --drc-work-dir /tmp/opencode/s8/drc{1,2} …` | **19 OK / 0 FAIL** · `passed=True` · `provisional=False` · **两跑 verdict 逐字节同 = `190b73be0f728a56`**（= 在岗签认值） |
| ③ | 变更后验收门 | `AppDir/bin/python3.11 k2/tools/k2_p6_acceptance_gate_v1.py --expect-patched` | **PASS**：A 4/4 · B verify PASS · C K1=14/K2=14 · **回退 0** · D `hidden_failures=2` = 具名 C1/C2 |
| ④ | P6 阶段门判据 | P6-1 / P6-2 / skip 完备性 三件 | **P6-1 PASS**（四项命中 OK + `dim_set_is_19` OK + manifest 已签认）· **P6-2 PASS**（结构差异 0）· **skip PASS**（未登记 0） |

- 套件全量（容器根布局，cwd=容器根）：**522P/30F/20S**（较落件前 512P 增 **10** = 新增契约测试；**红集/跳集不变** ⇒ 零回退）。
- **C1/C2 保持 RED**（`hidden_failures=2` 具名）；`skipped` 不充绿。
- 交付锚未动（`MANIFEST 6ee7495d…` / 受审板 `l7 c5a7df90…`）；**未重建包**。冻结四源原件未改（`l4 d4e81f64…`）。

## 一处口径对齐（**报备监理，可否决**）

`k2/tools/k2_p6_1_acceptance_v1.py` 的**非判据维**完整性检查 `dim_set_is_19` 原为**硬编码 19**；而监理落件 `criteria/manifest.k1.yaml` 时**显式**将 K1 的 `ref_plane_continuity` 置 `enabled:false`（K1 vacuous）⇒ k1 verdict 合法为 **18 维**。
本件把该检查改为**manifest 驱动**（**强化**，非缩口径）：维集须 **⊆ 19 维基准**，且缺维**只能**是在**已签认** manifest 中显式 `enabled:false` 者；否则仍 FAIL。⇒ 既守住防漂移，又对齐监理的 K1 口径。**若监理认为应改回硬编码 19，请裁定，本件即刻回退**（1 行）。

—— ENG（ARCHER）· 2026-09-20 · 判据 rev=3 · 放行件 #K2-42
