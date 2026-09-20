# K2 · **P6 / 学习环批 2 · 可执行计划 v3**（满足 **#K2-40 §四-1**）· 2026-09-20

> **性质**：**计划件（不施工）**。v1 `26a47e8a…`、v2 `ee3b1679…` 保留为历史件；**v3 取代 v2 的 §1**（批次表细化）并新增 §1.6/§1.7。
> 依据：`K2-RECTIFICATION-PLAN-v1.md` §P6 · `CAPABILITY-GAP-LEDGER-v1.md`（C-1..C-18）· `notice-20260916-k1-pause.md` · **#K2-40 §三/§四** · owner #14 ·
> 新增实证：`k2/docs/K2-P6-K1-READONLY-BASELINE-AND-FRAMEWORK-DEFECTS-20260920.md`（F-1/F-2/F-3）。
> **禁令**：学习环**只在项目外、慢、人闸**动（C-6）；**P6 只可出计划件，不得施工**（#K2-40 §四-3）；未获批不改 `_shared`/生成器/SPEC/判据/冻结件。

## 0. 门禁（未满 ⇒ 本件保持"计划"态）
| 闸 | 现状 | 归属 |
|---|---|---|
| **G-a** P5 外部完成（下单/打样 + V4–V7 回件） | **UNMET**（`L6/first_article/results_template.json` 逐项 `NOT_RUN`） | 外部 + 监理判定 |
| **G-b** owner 优先级（K1 复归） | **待 owner** | owner |
| **G-c** 学习环批 2 升版授权 + 模板整改批 | **未获批** | 监理 |
| **G-c2** `criteria/manifest.k1.yaml`（P6-1 应然集） | **缺件**（实测；`adjudicate.py:536` ⇒ `--project k1` FAIL-closed） | 监理 |
| **G-d** 回归不破 K2 | **可用**（`engine verify k2` = `preflight`+3 PASS） | ENG |

## 1. 批次表（v3 细化；**同批升版、同批回归**，禁零散补丁 = C-6）
> 行内载体为**实测行号**（机器校验：`pm_gate/artifacts/k2_v4/P6_execution/INSTRUMENT_SELFCHECK.json`，13/13 锚在）。

| # | 具名动作（文件:行） | 责任 | 可复现验收命令 | **fail-closed 门（期望值）** | 授权项 |
|---|---|---|---|---|---|
| **B2-1** | `_shared/eda_core/hs_route_model.py` — `_escape_smd_via` 定义 `:4513`/调用 `:892`：pad 契约显式化（真源 = 板 as-built 优先；库/YAML 交叉核对；不一致**登记**，禁静默 None/默认） | ENG | `python3 -m pytest -q _shared/eda_core/tests/test_hs_route_model.py` ＋ `python3 -m py_compile _shared/eda_core/hs_route_model.py` | ① 涉项用例**实跑**绿；② **`skipped` 不得充绿**（基线 **34P/34S**，skip=「k2_v4 真板缺失」）；③ 负控：pad 真源冲突 ⇒ **显式登记** | 无（共享层改动须监理批） |
> **基线归因**：34 skip = **22**（`K2V4_REAL_BOARD` 锚错，**一行可修 ⇒ 转实跑**）+ 12（`/tmp` fixture = N-05 同族）。见 SOC §7。
| **B2-2** | 同文件：`solve_all_v4` 定义 `:4406` · CLI `--all-v4` `:4796` · **项目分派** `:4800-4804`（`config.chain_segments`(K1) ↔ `alloc["alloc"]` PCIE_ 前缀(K2)）· 调用 `:4806` · 第二路径 `:4842-4846`；`routing_topology_gate.py:43` 同步 | ENG | 同 B2-1 ＋ K1 维度分派断言（构造 K1 链基 ⇒ 分派 K1） | ① 分派断言绿；② **K2 同输入同输出逐字节不回退**；③ 负控：非法/缺失项目维度 ⇒ **报错**（非静默取 K2） | 无 |
| **B2-3a** | `check_l3.py:26`（文案 `:28/:46/:53`）硬编码 `SPEC_k2_v4.json` ⇒ 改 `config.spec_name(artifacts.active_project())`；**且** `check_l2/l3/qa` 全部 `artifacts.read_text(...)` 补 `project=_proj()`（**T13 仅改了 `check_l1`** ⇒ F-2） | ENG | `cd k2 && PYTHONPATH=$PWD/_shared:$PWD python3 _shared/eda_core/pipeline/engine.py verify k2`（`preflight`+3 全 PASS）＋ K1 维度逐 gate 跑通 | ① K2 不回退；② K1 `G2.x/G3.x/G4.x` 读 **K1 自己**产物（现状：`G2.1` 报缺 `measurements.md`，而 `k1/.../L2/measurements.md` **实存**）；③ 负控：`spec_name` 指向不存在件 ⇒ **fail-closed** | **需监理批** |
| **B2-3b** | `check_qa.py:35` `config.spec_name()` **空参** ⇒ 取 `DEFAULT_PROJECT` 而非 active（`_shared` **唯一空参点** ⇒ F-2b） | ENG | `grep -rn "spec_name()" _shared --include=*.py`（期望 **0 命中**）＋ K1 `G4.1` | ① K1 `G4.1` 不再报「SPEC 缺失」（实存 `L3/SPEC_k1.json`）；② K2 不回退 | **需监理批** |
| **B2-3c** | `closure_check.py:110-113` `DEFAULT_SPEC`/`ESCAPE_SPEC_PATH` **框架相对且目录不存在** ⇒ `check_g35` 对任何项目不可跑（F-3；M-14 未覆盖这 2 处） | ENG | `python3 -c "import pm_gate.closure_check as cc, os; print(cc.DEFAULT_SPEC, os.path.isfile(cc.DEFAULT_SPEC))"`（期望 `True`）＋ K1/K2 `G3.5` 判定 | ① 两项目 `G3.5` **可跑**；② 负控：项目根缺 ⇒ 明确报错 | **需监理批** |
| **B2-3d** | `check_l3.SPEC_EXPECTS`（`:17-22`）走廊期望 `J2_TO_U`/`U_TO_MCIO` **陈旧**；现行 spec `corridors[].id` = `EAST_CHIP_TO_J2`/`WEST_MCIO_TO_CHIP`（plain 与 rev-52 同）⇒ 修好解析后 K2 `G3.1` **仍 FAIL** | ENG（**裁定期望值归监理**） | 修后 K2 `G3.1` 判定 | 门 = **监理先裁定期望集**（改名承接 / 双名兼容）；**禁 ENG 自定**（C-12） | **需监理裁定** |
| **B2-4** | `check_l1.py:193` `RULES_DOC`：现解 `<项目根>/../doc/PCB_DESIGN_RULES.md` ⇒ **越出容器**（实测 K1/K2 **双 FAIL**，F-1）；真源 = `_shared/docs/PCB_DESIGN_RULES.md`（K1 WAIVER 原文同指）＋ `:196` `check_g15` 撤 K1 waiver（RISK-001） | ENG | K1：`check_g15` **无 waiver 机判 PASS**；K2：`verify k2` 不回退 | ① K1 `G1.5` **真判 PASS**（撤 waiver）；② 负控：规则文档缺失/无「强条」⇒ **FAIL** | **需监理批**（撤 waiver = 判据收紧） |

- **K1 复跑序（恢复条件原文）**：B2-1..B2-4 全绿 ⇒ 复跑模型链 ⇒ **全 51 网折线** ⇒ **DRC error=0** ⇒ `G3.3` ⇒ Gerber。

## 1.5 只读回归基线（**改前**；真源 = 机读件，v2 数据保留）
| 项 | 基线（2026-09-20 实测） | 命令 |
|---|---|---|
| 共享模型单测 | **34 passed / 34 skipped** ⇒「pytest 全绿」是**空门**；升版门须**排除 skipped 充绿** | `python3 -m pytest -q _shared/eda_core/tests/test_hs_route_model.py` |
| 五载体可编译 | **5/5 OK** | `python3 -m py_compile _shared/eda_core/hs_route_model.py _shared/pm_gate/check_{l1,l2,l3,qa}.py` |
| K2 交付链门 | `verify k2` = `preflight`+3 **全 PASS**（**不得回退**） | `cd k2 && PYTHONPATH=$PWD/_shared:$PWD python3 _shared/eda_core/pipeline/engine.py verify k2` |
| K1/K2 框架维度 `check_l*` | 逐 gate 现状读数（含 F-1/F-2/F-3 命中项） | `…/k2/tools/k2_p6_readonly_baseline_v1.py` |
| 交付锚 | `MANIFEST 6ee7495d…` · tarball `0e88e107…`（422,709 B）· 板 `l7 c5a7df90…` | 只读 sha256 |

## 1.6 只读基线（**机读 + 可复现**）
- 机读真源：`pm_gate/artifacts/k2_v4/P6_execution/BASELINE_pm_gate_k1_k2_readonly_v1.json` sha256 **`27d79e4608…`**（**两次连跑逐字节同** ⇒ 可入库判据）。
- 仪器：`P6_execution/{README.md, CHECKLIST.md, results_template.json, INSTRUMENT_SELFCHECK.json}`（**不属于交付锚**，与 `L6/first_article/` 平级同构）。
- 机核入口：`k2/tools/k2_p6_instruments_selfcheck_v1.py`（13/13 锚 + 基线可复现；**负控已验**：篡改 1 锚 ⇒ verdict FAIL / 退出码 1）。
- 普查件：`P6_execution/SPEC_SITE_CENSUS_v1.json` sha256 **`6df3d557…`**（43 站点逐处定性 + 34 skip 归因 + K1 waiver 复算；两次连跑逐字节同）· 普查器 `k2/tools/k2_p6_spec_site_census_v1.py`。

## 1.7 SPEC 站点普查修正（范围差异，须具名）
v2 记「13 处」；实测 `_shared` **43 处**（`pm_gate/` **16**、`eda_core/` 27）⇒ **已逐处定性（8 类 · 0 未定性）**，真源 `P6_execution/SPEC_SITE_CENSUS_v1.json` `6df3d557…`：
**STALE_LEGACY_BASE 4**（`cap_wall_apply.py:56` · `cap_wall_solver.py:608` · `closure_check.py:112` · `wp1_semantics_check.py:45`，基址仍为旧 `revA/pcb` 布局 ⇒ M-14 钉子须扩面）·
**NAME_ONLY_HARDCODE 6**（`check_l3.py:26,:53` · `freeze_wp1.py:45` · `review.py:105,:121` · `tools_escape_predict.py:39`）·
**TEST_ANCHOR 13** · DOCSTRING_MESSAGE 9（具名豁免）· CLI_CONTRACT 7 · NEGATIVE_CONTROL 2（禁令门**仅扫 1 模块**，扩面须监理批）· PROJECT_CONFIG 1 · LEGACY_OTHER_PROJECT 1。**禁**一把梭（C-12）。

## 1.8 影子预验证（**授权前已完成**；真源零改动）
- 工具：`k2/tools/k2_p6_shadow_verify_v1.py`（`/tmp/opencode/shadow` 建框架影子 → 施加补丁集 → 跑验收 + 控制组归因）；机读件 `P6_execution/SHADOW_VERIFY_v1.json` **`844f2266…`**（两次连跑逐字节同）；报告 `k2/docs/K2-P6-SHADOW-VERIFICATION-BATCH2-20260920.md`。
- **结果**：K1 框架闸 **5→12 PASS** · K2 **12→13 PASS** · **零回退** · 控制组（零补丁）测试计数**相同** ⇒ **补丁集零测试回归**。
- **新增两项并入 B2-3**：**B2-3c（新 F-2c）** `check_qa.py:24` 板路径 `board_abspath()` 空参；**B2-3d（新 F-2d）** `gates.py:141` `scheme_closure_check` 产物读取未注入项目维度（⇒ K1 G2.6 PASS 的关键）。
- **22 skip 解锁实验**：非「一行白捡」——锚 `k2/k2_v4_8L.kicad_pcb` 或 `k2/hw/k2_v4_8L.kicad_pcb` ⇒ **9 通过 / 13 失败**（两锚一致 ⇒ 与锚无关）；锚 `k2/k2_v4.kicad_pcb` ⇒ 21 error（缺 `.kicad_pro`）。
- **13 项既有隐藏失败**（`hs_route_model` 域：契约漂移/区域集/`INFRA_ERROR`/多次 `StopIteration`/`solve_all_v4` 18 链未解/拓扑集）⇒ **纳入 B2-1/B2-2 triage**；**期望值类须监理裁定**。
- **待监理裁定的判定源/期望值**：G3.1 字段集 + 走廊期望（`J2_TO_U` vs 现行 `EAST_CHIP_TO_J2`）· G3.2 内容期望 · G3.5 判定源（`spec-rev-52` vs plain）· G4 施工对象（受审板 `l7` vs `project.yaml` 的 `k2_v4.kicad_pcb`）。

## 2. P6 完工判据（机判）与执行序
| 项 | 判据 | 命令 |
|---|---|---|
| P6-1 | `adjudicate.py --project k1` 出 verdict 且**必须命中** `ignore_without_ruling(9)` · `no_pipeline(1)` · `no_fp_lib_table(1)` · `sheets_empty(1)` `[结构]` | `python3 criteria/adjudicate.py --project k1 --board k1/k1_v1.kicad_pcb --pro k1/k1_v1.kicad_pro --nets k1/boards/k1_nets.yaml --sch-dir k1/sch …`（**只读**；输入件待监理确认，**G-c2**） |
| P6-2 | `k1\|k2_jlc_template.kicad_pro` 的 **ignore 集 == manifest 应然集**（0 差异） | 同上 + 模板解析 |
**执行序**：① 基线 verdict（只读）→ ② 逐项对账同源项 → ③ **模板整改（须获批）** → ④ 复判 `ignore 集 == 应然集`。

## 3. C-1..C-18 收口映射
见 v2 §3（未变）。**新增**：C-3 的**三个具体载体**已实证（F-1 `check_l1.py:193` · F-2a/b `check_l3.py:26`/`check_qa.py:35` · F-3 `closure_check.py:110-113`）；C-13 与 B2-1 同源。

## 4. 开闸前置（全绿方可施工）
1. **P5 外部完成**（下单/打样 + V4–V7 回件 + 监理判定，含 T1/T2）。
2. **owner 优先级**：K1 复归与否。
3. **学习环授权**：批次 + 回归判据；**模板整改**获批；**B2-3d 期望集裁定**；**G-c2** `manifest.k1.yaml`。
4. **回归不破 K2**：任一动 `_shared` ⇒ `verify k2` **4/4** ＋ canonical **19/19 不回退**（未连接 0 / error 0 / `zone_filled` 10/10 / 两跑逐字节同）。

## 5. 不做清单
❌ 不在执行环内改 `_shared`/生成器/SPEC（C-6）；❌ 不代 owner 决定 K1 复归；❌ **P6 不施工**；❌ 不新增检查齿（owner #14②）；❌ 不改冻结四源；❌ **不重建交付包**；❌ 不为变绿缩口径（C-12）。

## 6. 本件对 **#K2-40 §四** 的自检
| §四 要求 | 本件 |
|---|---|
| 1 具名动作 + 责任 + 可复现验收命令 + fail-closed 门 + 授权项单列 | ✅ §1 四列齐（含负控与反空转条款）；B2-3a/b/c 与 B2-4 已**单列授权**，B2-3d = **判据期望值单列待裁** |
| 2 交付锚不变 / 不重建包 | ✅ 本件为 `docs/` 追加；锚实测未动 |
| 3 不越阶段门（P6 只出计划） | ✅ §0/§5 |
| 4 红线 | ✅ §5；未触任何载体 |
| 5 禁以 HOLD 结案 | ✅ 本件为**推进物**（v2→v3 细化 + 机读仪器 + 只读基线） |
| **L1/owner 系统类** | **无** ⇒ 无「单列并停」项（L1 拓扑/接口/信号流向/球重映射未被触及） |
| 基线/普查可复现 | ✅ 机读件**两次连跑逐字节同**（`91ca2cc3…` / `6df3d557…` / `844f2266…`）；普查器/自检器/影子验证器**负控均已验** |
| 补丁集可施工性 | ✅ §1.8 影子预验证：+7/+1 PASS、零回退、零测试回归（控制组归因） |

—— ENG（ARCHER）· 2026-09-20 · 判据锚 rev=3（只读）
