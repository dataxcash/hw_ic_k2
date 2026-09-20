# K2 · **P6 / 学习环批 2 · 可执行计划 v2**（满足 **#K2-40 §四-1**：具名动作 + 责任 + 可复现验收命令 + fail-closed 门 + 授权项）· 2026-09-20

> **性质**：**计划件（不施工）**。v1（`26a47e8a…`）保留为历史件；本 v2 取代其 §1 并补 **只读回归基线** 与 **验收自检**。
> 依据：`K2-RECTIFICATION-PLAN-v1.md` §P6 · `.omo/supervision/ledger/CAPABILITY-GAP-LEDGER-v1.md`（C-1..C-18）· `notice-20260916-k1-pause.md` · **#K2-40 §三/§四** · owner #14。
> **禁令**：学习环**只在项目外、慢、人闸**动（根因 **C-6**）；**P6 只可出计划件，不得施工**（#K2-40 §四-3）；未获批不得改 `_shared`/生成器/SPEC/判据/冻结件。

## 0. 门禁（未满则本件保持"计划"态）
| 闸 | 现状 | 说明 |
|---|---|---|
| P5 外部完成 | **未完**（下单/打样 + V4–V7 实测未回件） | 计划 §P6 依赖表：P6 依赖 P1（已满足），但**阶段门序**要求 P5 过后 |
| owner 优先级 | **待定**（K1 复归与否 = owner） | `notice-20260916-k1-pause.md` |
| 学习环授权 | 需监理裁定批次 + 回归判据；**模板整改须获批** | 计划 §P6 责任栏 |

## 1. 批次表（学习环批 2 = K1 复归前置；**每项含可复现验收命令 + fail-closed 门 + 授权项**）

| # | 具名动作（文件:行） | 责任 | 可复现验收命令 | **fail-closed 门（期望值）** | 授权项 |
|---|---|---|---|---|---|
| **B2-1** | `_shared/eda_core/hs_route_model.py` — `_escape_smd_via` 定义 `:4513`（调用点 `:892`）：**pad 契约**显式化（pad 几何真源 = 板 as-built 优先；库/YAML 交叉核对；不一致**登记**，**禁静默 None/默认值**） | ENG | `python3 -m pytest -q _shared/eda_core/tests/test_hs_route_model.py` ＋ `PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 -c "import sys;sys.path.insert(0,'_shared');import eda_core.hs_route_model"` | ① 新增/改动的契约断言用例**全绿**；② **`skipped` 不得计入绿**（见 §1.5：现状 34 skipped）⇒ 涉及该项的 skipped 用例须**转为实跑**或**具名接受**；③ 不一致输入 ⇒ **显式登记**（负控） | 无（共享层改动须监理批） |
| **B2-2** | 同文件 — `solve_all_v4` `:4406` · CLI `--all-v4` `:4699` · 分派 `:4796`/`:4806`：**分派显式化（项目维度）**，**禁**隐式默认落 K2；`routing_topology_gate.py` 同步 | ENG | 同上 ＋ K1 维度分派断言：`python3 -c "..."`（构造 K1 项目维度参数 ⇒ 分派到 K1） | ① 分派断言用例绿；② **K2 既有行为逐字节不回退**（同输入同输出 sha）；③ 负控：非法/缺失项目维度 ⇒ **报错**（非静默取 K2） | 无（同上） |
| **B2-3** | `_shared/pm_gate/{check_l2,check_l3,check_qa}.py` ＋ **13 处** `SPEC_k2_v4` 站点（§1.5 具名）：改由 `pm_gate/project.yaml: spec_name` 解析 | ENG | `cd k2 && PYTHONPATH=k2/_shared:$PWD/k2 python3 _shared/eda_core/pipeline/engine.py verify k2`（期望 **4/4**）＋ K1 维度跑通 | ① K2 `engine verify` **4/4**；② K2 canonical **19/19 不回退**（未连接 0 / error 0 / `zone_filled` 10/10 / 两跑逐字节同）；③ K1 侧三项在 **K1 维度**跑通（**不再读 K2 件**）；④ 负控：`spec_name` 指向不存在件 ⇒ **fail-closed 报错** | **需监理批**（碰判据件） |
| **B2-4** | `_shared/pm_gate/check_l1.py:193` `RULES_DOC`（路径由 `__file__` 三级上溯 + `..`/`doc/PCB_DESIGN_RULES.md`）＋ `check_g15()` `:196` **撤 G1.5 waiver** | ENG | K1：`check_l1` 在**无 waiver** 下跑通；K2：`check_l1` 不回退 | ① K2 `verify` 4/4 不回退；② K1 `G1.5` **真判**（不再 PASS-by-waiver）；③ 负控：规则文档缺失/无「强条」⇒ **FAIL** | **需监理批**（撤 waiver 属判据收紧） |

- **K1 复跑序（恢复条件原文）**：B2-1..B2-4 全绿 ⇒ 复跑模型链 ⇒ **全 51 网折线** ⇒ **DRC error=0** ⇒ `G3.3` ⇒ Gerber。
- **整批原则**：四项**同批升版**、**同批回归**（禁零散补丁 = C-6）。

## 1.5 只读回归基线（**本轮实测**，供升版后 before/after）
| 项 | 基线（2026-09-20 实测） | 命令 |
|---|---|---|
| 共享模型单测 | **34 passed / 34 skipped**（skip 原因 = `k2_v4 真板缺失`）⇒ **回归网弱于表面**，升版门必须排除 skipped 充绿 | `python3 -m pytest -q _shared/eda_core/tests/test_hs_route_model.py` |
| 五载体可编译 | **5/5 OK** | `python3 -m py_compile _shared/eda_core/hs_route_model.py _shared/pm_gate/check_{l1,l2,l3,qa}.py` |
| `SPEC_k2_v4` 站点 | **13 处**：`freeze_wp1.py:45` · `wp1_semantics_check.py:45` · `red_team.py:49` · `closure_check.py:112` · `tools_escape_predict.py:15,39` · `config.py:27,120` · `check_l3.py:3,26,28,46,53` · `review.py:105`（含若干 docstring 站点，实施时逐处判） | `grep -rn "SPEC_k2_v4" --include=*.py _shared \| grep -v __pycache__` |
| `check_l1` RULES_DOC | `_shared/pm_gate/check_l1.py:193`（`__file__` 三级上溯 + `../doc/PCB_DESIGN_RULES.md`） | `sed -n '188,215p' _shared/pm_gate/check_l1.py` |
| B2-1/B2-2 符号位 | `_escape_smd_via` `:4513`（调用 `:892`）· `solve_all_v4` `:4406` · `--all-v4` `:4699` · 分派 `:4796/:4806` | `grep -n "_escape_smd_via\|all-v4\|solve_all_v4" _shared/eda_core/hs_route_model.py` |

> **基线发现（须在升版时处置）**：34 条 skip ⇒ **"pytest 全绿"是空门**；且其成因（真板/输入件缺失）与 **N-05「生成器不可复跑」同族**。

## 2. P6 完工判据（计划原文；机判）与执行序
| 项 | 判据 | 命令 |
|---|---|---|
| P6-1 | `adjudicate.py --project k1` 出 verdict 且**必须命中**同源项 `ignore_without_ruling(9)` · `no_pipeline(1)` · `no_fp_lib_table(1)` · `sheets_empty(1)` `[结构]` | `python3 criteria/adjudicate.py --project k1 …`（**只读**） |
| P6-2 | `k1\|k2_jlc_template.kicad_pro` 的 **ignore 集 == manifest 应然集**（`[结构=0 差异]`） | 同上 + 模板解析 |

**执行序**：① 基线 verdict（只读）→ ② 逐项对账同源项 → ③ **模板整改（须获批）** → ④ 复判 `ignore 集 == 应然集`。

## 3. C-1..C-18 收口映射（现状 × 批次 × 归属）
> 现状引自账本（2026-09-15）＋ #K2-39/#K2-40 更新。归属：ENG=共享层/工具；监理=判定/流程/模板/巡检；owner=优先级/系统账号/预算。

| # | 坑 | 现状 | 批次 | 归属 |
|---|---|---|---|---|
| C-1 | 自己给自己打分 | ❌ 未拦 | **批 1（已裁定：C-1+C-2）** | ENG + 监理 |
| C-2 | 红线不守 | ❌ 未拦 | **批 1** | ENG + 监理 |
| C-3 | 工具路径/分派过时 | ❌ 未拦 | **批 2 = B2-2/B2-3/B2-4** | ENG |
| C-4 | 同层重做不支持 | ❌ 未拦 | 批 2 | 监理（流程）→ ENG |
| C-5 | 投递不达（无回执） | ⚠️ 部分 | 批 3（运维） | 监理 |
| C-6 | 学习环跑在执行环内 | ✅ 已立闸 | — | 监理 |
| C-7 | 回程不达 / 全局误压 | ✅ #K2-39 修；**上游根因 = C-18** | — | 监理（上游已闭） |
| C-8..C-10 | 双副本 / 会话跨项目 / 开会话风暴 | ✅ 已修 | — | 监理 |
| C-11 | PCB 段完工判据缺席 | ❌ 未拦 | 批 1（建议）；**K2 侧已由 rev=3 canonical 19 维实证收口** | ENG + 监理 |
| C-12 | 门禁吞数 / 判据自废 | ❌ 未拦 | 批 1（建议）；**K2 侧已由 rev=3 登记制 + 禁 ignore 收口** | ENG + 监理 |
| C-13 | 产物↔方案无回对 | ❌ 未拦 | 批 1（建议）；**与 B2-1 同源** | ENG |
| C-14 | 监理以被审输出为审据 | ⚠️ 部分 | 批 1（建议）；**#K2-36/40 已实证独立复算** | 监理 |
| C-15 | 巡检器静默失效 | ❌ 未拦 | 批 1（建议）；#K2-38/39 已修部分 | 监理 |
| C-16 | 监理无开工仪式 | ❌ 未拦 | 批 1（建议） | 监理 |
| C-17 | 监理过度升级 | ⚠️ 部分 | 批 1（建议）；#K2-36..40 连续自裁（owner 项=0） | 监理 |
| **C-18** | **哨兵/投递会话身份识别缺失**（cwd+新近 ⇒ 误报停摆 + 续推投错线程 + 裁定可误投 owner） | ✅ **#K2-40 已修**（`ARCHER_MARK`/`rollout_is_archer` + `archer_only=True` 三处调用）· **待重启载入** | — | 监理 |

## 4. 开闸前置（全绿方可施工）
1. **P5 外部完成**（下单/打样 + V4–V7 回件 + 监理判定，含 T1/T2 触发与否）。
2. **owner 优先级**：K1 复归与否。
3. **学习环授权**：批次 + 回归判据；**模板整改**获批。
4. **回归不破 K2**：任一 `_shared` 改动后 `engine verify k2` **4/4** + canonical **19/19 不回退**（未连接 0 / error 0 / `zone_filled` 10/10 / 两跑逐字节同）。

## 5. 不做清单
- ❌ 不在执行环内改 `_shared`/生成器/SPEC（C-6）；❌ 不代 owner 决定 K1 复归；❌ **P6 不施工**（#K2-40 §四-3）；❌ 不新增检查齿（owner #14②）；❌ 不改冻结四源；❌ **不重建交付包**（`MANIFEST 6ee7495d…` / tarball `0e88e107…` 冻结）。

## 6. 本件对 **#K2-40 §四** 的自检
| #K2-40 §四 要求 | 本件 |
|---|---|
| 1 具名动作 + 责任 + 可复现验收命令 + fail-closed 门 + 授权项单列 | ✅ §1 四列齐（含负控与反空转条款）；**无 L1/owner 系统类** ⇒ 无「单列并停」项 |
| 2 交付锚不变 / 不重建包 | ✅ 本件为 `docs/` 追加；锚实测未动（见 ledger 同笔） |
| 3 不越阶段门（P6 只出计划） | ✅ §0/§5 明示不施工 |
| 4 红线 | ✅ §5 + 本件未触任何载体 |
| 5 禁以 HOLD 结案 | ✅ 本件为**推进物**，非停等声明 |
