# K2 · **P6 / 学习环批 2 · 执行检查表**（人读 · 与 `results_template.json` 一一对应）

> 计划真源：`k2/docs/K2-P6-LEARNING-LOOP-BATCH2-AND-CAPABILITY-GAP-CLOSURE-PLAN-v3.md`
> 判据：**#K2-40 §四-1**（具名动作 + 责任 + 可复现验收命令 + fail-closed 门 + 授权项单列）· owner #14
> **状态：计划态 —— 施工前四项授权门全绿方可开工**（#K2-40 §四-3：P6 未开 ⇒ 只可出计划件）。执行人：__________ 日期：__________

## 0. 授权门（**未全绿 ⇒ 不得施工**）
| 门 | 现状（2026-09-20 实测） | 归属 | 绿？ |
|---|---|---|---|
| **G-a** P5 外部完成（下单/打样 + V4–V7 回件） | **UNMET**：`L6/first_article/results_template.json` 逐项 `NOT_RUN` | 外部 + 监理判定 | ☐ |
| **G-b** owner 优先级（K1 复归） | **待 owner**（`notice-20260916-k1-pause.md`） | owner | ☐ |
| **G-c** 学习环批 2 升版授权 + 模板整改批 | **未获批** | 监理 | ☐ |
| **G-c2** `criteria/manifest.k1.yaml`（P6-1 的**应然集**，监理持有） | **不存在**（实测：`criteria/` 仅有 `manifest.k2.yaml`；`adjudicate.py:536` 缺件即 FAIL-closed） | 监理 | ☐ |
| **G-d** 回归不破 K2 | **可用**：`engine verify k2` = `preflight`+3 全 PASS（本表基线） | ENG | ☑ |

## 1. 批次项（B2-1..B2-4：**同批升版、同批回归**，禁零散补丁）
| # | 具名动作（文件:行） | 可复现验收命令 | fail-closed 门（期望值）+ 负控 | 授权 | ☐ |
|---|---|---|---|---|---|
| **B2-1** | `_shared/eda_core/hs_route_model.py` `_escape_smd_via` 定义 `:4513` / 调用 `:892`：pad 契约显式化（真源=板 as-built 优先；库/YAML 交叉核对；不一致**登记**，禁静默 None/默认） | `python3 -m pytest -q _shared/eda_core/tests/test_hs_route_model.py`；`python3 -m py_compile _shared/eda_core/hs_route_model.py` | ① 涉项用例**实跑**绿 —— **`skipped` 不得充绿**（基线 34P/**34S**，skip 因「k2_v4 真板缺失」）；② 负控：pad 真源冲突 ⇒ **显式登记**（非静默） | 无 | ☐ |
| **B2-2** | 同文件：`solve_all_v4` 定义 `:4406` · CLI `--all-v4` `:4796` · **项目分派** `:4800-4804`（`config.chain_segments`（K1）↔ `alloc["alloc"]` PCIE_ 前缀（K2））· 调用 `:4806`（+ 另一路径 `:4842-4846`）：分派显式化，**禁**隐式落 K2；`routing_topology_gate.py` 同步 | 同 B2-1 ＋ K1 维度分派断言（构造 K1 链基 ⇒ 分派 K1） | ① 分派断言绿；② **K2 同输入同输出（逐字节不回退）**；③ 负控：非法/缺失项目维度 ⇒ **报错** | 无 | ☐ |
| **B2-3a** | `check_l3.py:26`（错误文案 `:28/:46/:53`）硬编码 `SPEC_k2_v4.json` ⇒ 改 `config.spec_name(artifacts.active_project())`；**且** `check_l2/l3/qa` 的 `artifacts.read_text(...)` 全体补 `project=_proj()`（T13 仅改了 `check_l1`）⇒ 否则非默认项目恒读 `<proj>/pm_gate/artifacts/k2_v4/...` | `cd k2 && PYTHONPATH=$PWD/_shared:$PWD python3 _shared/eda_core/pipeline/engine.py verify k2`（期望 `preflight`+3 **PASS**）＋ K1 维度逐 gate 跑通 | ① K2 `verify k2` 不回退；② K1 `G2.x/G3.x/G4.x` 读**K1 自己的**产物（现状：G2.1 报缺 `measurements.md`，而 `k1/.../L2/measurements.md` **实际存在**）；③ 负控：`spec_name` 指向不存在件 ⇒ **fail-closed 报错** | **需监理批**（碰门禁实现） | ☐ |
| **B2-3b** | `check_qa.py:35` `config.spec_name()` **空参** ⇒ 取 `DEFAULT_PROJECT`（`k2_v4`）而非 active project（**全 `_shared` 唯一空参点**：`grep -rn "spec_name()" _shared`） | `grep -rn "spec_name()" _shared --include=*.py`（期望：**0 命中**）＋ K1 `G4.1` | ① K1 `G4.1` 不再报「SPEC 缺失」（实测：K1 有 `L3/SPEC_k1.json`，仍报缺）；② K2 不回退 | 同上 | ☐ |
| **B2-3c** | `closure_check.py:110-113`：`DEFAULT_SPEC` / `ESCAPE_SPEC_PATH` 为**框架相对**（`_shared/pm_gate/artifacts/...`，该目录**不存在**）⇒ `check_l3.check_g35` 对**任何**项目不可跑（M-14 基址钉子未覆盖这 2 处） | `python3 -c "import ...; print(os.path.isfile(cc.DEFAULT_SPEC))"`（期望 True）＋ K1/K2 `G3.5` 可跑 | ① 两项目 `G3.5` 均**可跑**（现状均 FAIL「SPEC 读取失败 `_shared/pm_gate/artifacts/L3/...`」）；② 负控：项目根缺失 ⇒ 明确报错 | 同上 | ☐ |
| **B2-3d** | `check_l3.SPEC_EXPECTS["corridors"] = ["J2_TO_U","U_TO_MCIO"]` **陈旧**：现行 spec 走廊 `id` 实为 `EAST_CHIP_TO_J2` / `WEST_MCIO_TO_CHIP`（plain 与 rev-52 同）⇒ 修好解析后 K2 `G3.1` **仍 FAIL**。**期望值属判据侧** | 修后 K2 `G3.1` 判定 | 门：**须监理先裁定**走廊期望集（改名承接 or 保留双名），**不得 ENG 自定**（C-12 禁为变绿缩口径） | **需监理裁定** | ☐ |
| **B2-3c（新 F-2c）** | `check_qa.py:24` 板路径 `board_abspath()` **空参** ⇒ 改 `board_abspath(_proj())`（原取 `DEFAULT_PROJECT`；真源基线被 SPEC 失败掩盖） | 同 B2-3a | ① K1 `G4.1` 指 `k1_v1.kicad_pcb`（**影子已验**：报「尚未按 SPEC 布线」= 真实判定）；② K2 不回退 | **需监理批** | ☐ |
| **B2-3d（新 F-2d）** | `gates.py:141` `scheme_closure_check` 的 `artifacts.read_text(stage, *parts)` 未注入项目维度 ⇒ K1 `G2.6` 误报缺产物（**该件实存**） | 同 B2-3a | K1 `G2.6` PASS（**影子已验**） | **需监理批** | ☐ |
| **B2-T（triaged）** | **22 skip 解锁后 13 项既有隐藏失败**（`hs_route_model` 域；清单见 `docs/K2-P6-SHADOW-VERIFICATION-BATCH2-20260920.md` §4） | `PYTHONPATH=AppDir/... AppDir/bin/python3.11 k2/tools/k2_p6_shadow_verify_v1.py` | 逐项定性：**引擎真缺陷**（ENG 修）vs **期望漂移**（**监理裁定**，C-12 禁缩口径） | **须监理裁定**（期望值类） | ☐ |
| **B2-4** | `check_l1.py:193` `RULES_DOC`：现解析为 `<项目根>/../doc/PCB_DESIGN_RULES.md` ⇒ **越出容器**（实测 K1/K2 **双双 FAIL**）；真源 = `_shared/docs/PCB_DESIGN_RULES.md`（K1 `state_k1.json` 的 G1.5 WAIVER 原文即如此指认）＋ 撤 `G1.5` waiver（RISK-001） | K1：`check_g15` **无 waiver 机判 PASS**；K2：`verify k2` 不回退 | ① K1 `G1.5` 真判 PASS（**标注须撤**，不再 PASS-by-waiver）；② 负控：规则文档缺失/无「强条」⇒ **FAIL** | **需监理批**（撤 waiver = 判据收紧） | ☐ |

> **影子预验证（授权前已完成，真源零改动）**：`k2/tools/k2_p6_shadow_verify_v1.py` ⇒ K1 框架闸 **4→12 PASS（+8）** · K2 **12→13 PASS** · 零回退 · 控制组归因**零测试回归**；机读件 `SHADOW_VERIFY_v1.json` `844f2266…`。
> **SPEC 站点普查修正**：v2 记「13 处」；本轮实测 `_shared` 内 **43 处**（`pm_gate/` 内 **16**、`eda_core/` 内 27；含 `review.py:121`、`check_qa.py:34`、`config.py:120` 等）⇒ 实施时**逐处定性**（应项目化 / 应具名豁免），**禁**一把梭（C-12）。

## 2. P6 完工判据（机判 · 执行序全部**只读**起手）
| 项 | 命令 | fail-closed 门 | 前置 |
|---|---|---|---|
| **P6-1** | `python3 criteria/adjudicate.py --project k1 --board k1/k1_v1.kicad_pcb …`（**只读**；见 `results_template.json` 完整命令行） | verdict 必须命中 `ignore_without_ruling(9)` · `no_pipeline(1)` · `no_fp_lib_table(1)` · `sheets_empty(1)` | **G-c2**（`manifest.k1.yaml` = 应然集，监理持有；缺 ⇒ `adjudicate.py:536` FAIL-closed） |
| **P6-2** | 同上 + 模板解析 | `k1\|k2` `ignore 集 == manifest 应然集`（0 差异） | **模板整改获批**（G-c） |

## 3. 改前基线（**升版后须逐项复算对比**；真源 = `BASELINE_pm_gate_k1_k2_readonly_v1.json` `27d79e46…`）
| 观测 | 改前值（2026-09-20） |
|---|---|
| 共享模型单测 | **34 passed / 34 skipped**（skip = 「k2_v4 真板缺失」⇒「pytest 全绿」是**空门**） |
| 五载体 `py_compile` | **5/5 OK** |
| K2 交付链门 | `verify k2` = `preflight`+3 **全 PASS**（不得回退） |
| K1 `G1.5` | **WAIVER**（框架路径缺陷；实条件已核） |
| K1 框架维度 `check_l*` | 仅 `G1.1-1.4` PASS；`G1.5`+`G2.1-2.6`+`G3.1-3.5`+`G4.1-4.2` **FAIL**（其中 G2.x 系「读错项目维度」缺陷所致，非 K1 缺件） |
| K2 框架维度 `check_l*` | `G1.1-1.4`/`G2.1-2.5`/`G3.2-3.4` PASS；`G1.5`/`G2.6`/`G3.1`/`G3.5`/`G4.1-4.2` FAIL |
| 交付锚 | `MANIFEST.json` `6ee7495d…` · tarball `0e88e107…`（422,709 B）· 受审板 `l7 c5a7df90…` — **未动，禁重建** |

## 4. 不做清单（红线）
☐ 不在执行环内改 `_shared`（C-6）｜☐ 不重建交付包（锚冻结）｜☐ 不改冻结四源｜☐ `criteria/` 只读｜☐ 不新增检查齿｜☐ 不为变绿缩口径（C-12）｜☐ 未连接 0 / error 0 / `zone_filled` 10/10 不得回退｜☐ 冲突即停机

**责任**：ENG 执行 ｜ **判定归监理** ｜ 签字 __________
