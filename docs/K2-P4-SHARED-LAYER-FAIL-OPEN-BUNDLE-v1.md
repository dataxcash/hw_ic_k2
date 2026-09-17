# K2 · P4 · **共享层 fail-open 修复包**（`D-2` · `D-3` · `D-4` · `D-5` · `D-7`）——可一次派单 · v1 · 2026-09-18

> 缘起：handoff inc51 §6-3-(d)「凑齐引擎侧 fail-open 四联交付共享层」。本件把**分散在 4 份证据件**的缺陷**收敛为一次可派单的修复包**（含逐项复现、修正候选、正/负控、验收配方）。
> 本会话仍**无监理放行** ⇒ ENlegal 面。全部复现/修正仅在 `/tmp` 副本；**仓库零写入**（`_shared/**` 未动）。

## 0. 结论

- 共享层存在 **5 处 fail-open / 口径缺陷**，**全部已复现 + 修正候选已验证**（含正/负控）；它们同属 `_shared/eda_core/{pipeline/checks.py, pipeline/engine.py, pipeline/hooks/pre-commit}`。
- **对 P4 的直接后果**：只要 `D-3`/`D-4` 未修，**「安装 `k2/pipeline.yaml`」= 形式在岗**（3 项必选 sch 检查在任何提交路径都不会被执行）⇒ **J-9 的「门禁接入」实质不成立**。
- **耦合**：`D-5`（k2 挂 `k2/_shared` 旧 pin `9a67d9e`）⇒ 修入共享仓后**必须同步前移 k2 的 `_shared` pin**，否则 k2 提交仍跑旧 `engine.py`。
- 交付形态：**建议单笔共享 commit 修 D-2/D-3/D-4/D-7 + 一处 pin 前移（D-5）**，本件即其验收依据。

## 1. 五缺陷总表

| ID | 现象 | 载体（共享层） | 复现装置 | 修正候选 | 正控 / 负控 | 详见 |
|---|---|---|---|---|---|---|
| **D-2** | 声明产物缺件时**抛未捕获异常**（verify 中止），而非干净 FAIL | `checks.py::check_netlist_connect`（`nets_yaml`）· `::check_bom_consistent`（`bom_csv`） | `/tmp/opencode/inc52/sb_miss`、`sb_miss_bom` | 两处各加**存在性判据 → `return False, "缺件: … — fail-closed"`** | 正控 happy path 3/3 PASS；负控 nets/BOM/sch 三种缺件→干净 FAIL | 本件 §2 |
| **D-3** | per-project `engine verify` **永不触发**（`affected` 恒空） | `hooks/pre-commit` 的 affected 判定 | `/tmp/opencode/inc51/d3A`（仓根=项目根）、`d3B`（容器式+真 gitlink）· **真 hook 实跑** | `rel=='.' → hit`（仓根即项目根）+ 兼认裸 gitlink（`c == rel`） | 正控：正控标记 `verify/cmd: PASS` 在两路径均跑到；负控：原版两路径**无**「受影响项目」行 | `K2-P4-D3-D4-…` §1 |
| **D-4** | `phases[].checks` **引擎不执行**（纯声明） | `engine.py::cmd_run` 只跑 `cmd`/`verify` | `/tmp/opencode/inc51/d4`（`checks=[cmd false]`） | `cmd_run` 在 `cmd`/`verify` **之前**执行 `checks`，失败即 phase FAIL | 正控 `checks=[cmd true]`→rc0 PASS；负控 `checks=[cmd false]`→rc1 FAIL；**隔离对照** `verify=[cmd false]` 原版 rc1 | 同上 §2 |
| **D-5** | k2 挂 `k2/_shared`(`9a67d9e`) ≠ 容器 `_shared`(`0ec324b`)；`pipeline/checks.py` 分叉 | 子模块 pin | sha 对比（本件 §4） | **前移 k2 的 `_shared` pin** 至修复后 commit | —（属落件手续） | 同上 §3 |
| **D-7** | NC 白名单**只读 top-level `nc`** ⇒ 对合规真源批量误报（本板 **105** 条） | `checks.py::check_netlist_connect` | `/tmp/opencode/inc49`（复现）、`inc50`（控制仪器） | 白名单改读 **①top-level + ②`sheets[].placements[].nc`**（**不启用 ③**，见下） | 正控 errata-1 三源→1 处；负控 none→106、注入伪网→2；**9 案矩阵** | `K2-P4-D7-CONTROL-MATRIX-…` §1 |
| **D-6** | 生成器打印「自检结果 (8/8)」实为 6 项（`S3`/`S7` 0 命中） | `k2/tools/k2_gen_v5.py`（非共享层） | 静态计数 | 改注释/打印为实际项数 | — | `K2-P4-GROOT-LIVE-REPRODUCTION-…` §0-6 |
| **D-1** | `docs/drafts/…/pipeline.yaml.draft` 为非 pipeline.yaml（无 `phases`），README 失实 | 项目侧草案 | `/tmp/opencode/inc46/d1` C0 | 作废/改标签（监理裁） | C0 `PipelineError` | `K2-P4-PIPELINE-INSTALL-PATH-…` §3 |

> **D-7 的 ③（netlist `pintype no_connect`）为何不启用**：该源取自 **netlist 自身** ⇒ 「判据真源 = 被验对象」，属 **C-1 自证**（`_shared/eda_core/truth_binding.py::SelfSourceError`，sha `0683713df1003df3`）。①② 均落在**真源网表 yaml** 内 ⇒ 外部真源，符合 C-1。若共享层属主选择启用 ③，须**显式登记 C-1 例外**。

## 2. `D-2` 复现 + 修正（本件新增；含正/负控）

装置 `/tmp/opencode/inc52`（`_shared/eda_core` 副本 + 修正）：

| 案 | 装置 | 原版 engine | 修正 engine |
|---|---|---|---|
| A | `netlist_connect` 的 `nets_yaml` 缺件 | **未捕获 `FileNotFoundError`**（traceback；无 `verify/… : FAIL` 行） | `verify/netlist_connect: FAIL` + `netlist_connect 缺件: … — fail-closed` |
| B | `bom_consistent` 的 `bom_csv` 缺件 | **未捕获 `FileNotFoundError`** | `bom_consistent: FAIL` + `缺件: … — fail-closed` |
| C | **正控** happy path（`errata-2` + BOM 齐备） | 3/3 PASS | **3/3 PASS（修正不破坏正常路径）** |
| D | **负控** `sch` 缺件（新增判据） | （`load_netlist` 侧未捕获） | `缺件: …/NOPE.kicad_sch — fail-closed` |

**修正（候选，仅 `/tmp`）**：

```diff
     nets_yaml = config.abs_path(cfg, spec["nets_yaml"])
+    if not Path(nets_yaml).is_file():      # D-2: 缺件 fail-closed（旧实现抛未捕获 FileNotFoundError）
+        return False, f"netlist_connect 缺件: {nets_yaml} — fail-closed"
+    if not Path(sch).is_file():
+        return False, f"netlist_connect 缺件: {sch} — fail-closed"
     nets, _comps = load_netlist(str(sch), sharun=SHARUN)
@@
     bom_csv = config.abs_path(cfg, spec["bom_csv"])
+    if not Path(bom_csv).is_file():        # D-2: 缺件 fail-closed
+        return False, f"bom_consistent 缺件: {bom_csv} — fail-closed"
+    if not Path(sch).is_file():
+        return False, f"bom_consistent 缺件: {sch} — fail-closed"
     tmp = "/tmp/opencode/pipeline_bom_net.kicadsexpr"
```

## 3. 统一验收配方（共享层修后逐项跑；期望值即验收判据）

```bash
cd /home/fila/jqdDev_2025/ic_hw; export SHARUN=$PWD/AppDir/sharun
# D-2 —— 期望：正控 3/3 PASS；三种缺件均「干净 FAIL」（无 traceback）
(cd /tmp/opencode/inc52/sb_miss      && PYTHONPATH=/tmp/opencode/inc52 python3 -c "import sys;from eda_core.pipeline import engine;sys.exit(engine.main(['verify','k2']))")  # 缺件→FAIL（非 traceback）
(cd /tmp/opencode/inc52/sb_miss_bom  && PYTHONPATH=/tmp/opencode/inc52 python3 -c "import sys;from eda_core.pipeline import engine;sys.exit(engine.main(['verify','k2']))")  # 缺件→FAIL
(cd /tmp/opencode/inc50/sb_e2        && PYTHONPATH=/tmp/opencode/inc52 python3 -c "import sys;from eda_core.pipeline import engine;sys.exit(engine.main(['verify','k2']))")  # 正控→3/3 PASS
# D-3 —— 期望：两 fixture 均打印「受影响项目: k2」且正控标记 verify/cmd: PASS
(cd /tmp/opencode/inc51/d3A && bash /tmp/opencode/inc51/pre-commit.d3fix) 2>&1 | grep -E '受影响项目|verify'
(cd /tmp/opencode/inc51/d3B && bash /tmp/opencode/inc51/pre-commit.d3fix) 2>&1 | grep -E '受影响项目|verify'
# D-4 —— 期望：rc 0（checks true）/ 1（checks false）
(cd /tmp/opencode/inc52/d4ok && PYTHONPATH=/tmp/opencode/inc51 python3 -c "import sys;from eda_core.pipeline import engine;sys.exit(engine.main(['preflight','k2']))")
(cd /tmp/opencode/inc51/d4   && PYTHONPATH=/tmp/opencode/inc51 python3 -c "import sys;from eda_core.pipeline import engine;sys.exit(engine.main(['preflight','k2']))")
# D-7 —— 期望：errata-1 三源→1 处；none→106；伪网→2（详见 D-7 矩阵件 §5 的 9 案循环）
```
（路径即本件**控制仪器**：`inc52` = 含 D-2 修正的 `eda_core` 副本；`inc51` = 含 D-4 修正的 `eda_core` 副本与含 D-3 修正的 `pre-commit.d3fix`；共享层正式修后请替换为共享仓路径）

## 4. 耦合与建议顺序

| 步骤 | 内容 | 归属 |
|---|---|---|
| 1 | 共享仓单笔修 **D-2 + D-3 + D-4 + D-7**（四处同文件/同族，宜同批判） | 共享层属主 |
| 2 | 跑 §3 统一验收（正/负控全绿） | 共享层属主 + 监理 |
| 3 | **前移 k2 子模块的 `_shared` pin**（`9a67d9e` → 修复后 commit） | 落件手续（监理侧） |
| 4 | 再装 `k2/pipeline.yaml`（含前置 `errata-*` + BOM）⇒ 此时「门禁接入」方为**实质** | gate 属主 |

**未做此序的后果（具名）**：只装 `pipeline.yaml` 而 D-3/D-4 未修 ⇒ `受影响项目` 恒空、`checks` 恒不跑 ⇒ **J-9 形式在岗、实质 fail-open**（C-12 同型风险，须避免）。

**D-5 现状值**（本件复算，供 pin 前移时比对）：
| 检查点 | 容器 `_shared`（`0ec324b`） | k2 `_shared`（`9a67d9e`） |
|---|---|---|
| `pipeline/hooks/pre-commit` | `62dc6a4e476f6b55` | `62dc6a4e476f6b55`（同） |
| `pipeline/engine.py` | `97baca95a0b9bda7` | `97baca95a0b9bda7`（同） |
| `pipeline/required.py` | `42af2b11e25fd9d2` | `42af2b11e25fd9d2`（同） |
| **`pipeline/checks.py`** | `02b41e8b6d6d9b3a` | **`e88c70aaa56ce22f`（分叉）** |

## 5. 边界

本件**只读 + `/tmp` 副本（未落库）**：未改 `_shared/**`（D-2/D-3/D-4/D-7 补丁仅作用于 `/tmp` 副本）、生成器、模板、板、pro、库、`fp-lib-table`、`pm_gate/**`、SPEC、真源、`criteria/**`；未创建 `k2/pipeline.yaml`；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode`；未新增仓库内判据/脚本（避新增检查齿，owner ②）。
证据出处：`K2-P4-D3-D4-REPRO-AND-FIX-CANDIDATES-v1.md` `70cae98e2433ec64` · `K2-P4-D7-CONTROL-MATRIX-AND-C1-TRUTH-BINDING-v1.md` `205685121d743974` · `K2-P4-NC-PROVENANCE-AND-D7-CALIBER-v1.md` `ba0db199bc19c4ed` · `K2-P4-PIPELINE-INSTALL-PATH-EVIDENCE-v1.md` `25ec153e4472e61c` · `K2-P4-GROOT-LIVE-REPRODUCTION-v1.md` `0daf263d1842b894`。
—— ENG（ARCHER）· 2026-09-18 · 容器 `_shared` `0ec324b` / k2 `_shared` `9a67d9e` / hook `62dc6a4e476f6b55`
