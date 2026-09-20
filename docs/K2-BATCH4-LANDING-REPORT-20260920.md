# K2 批 4 落件报告（学习环收口批）· #K2-43 · 2026-09-20

> 裁定：#K2-43（ENG 侧 3 项：**C-1 残面 · C-4 · C-22**，**同批升版 C-6**）。
> 判据锚 **rev=3**（`eb244d81…`/`1937a40a…`/`e2b49fdd…`）在岗未动；owner 项 = 0。
> 落地形态：**两 `_shared` 同 commit id**（`02459f5`，逐字节同）⇒ `k2/_shared` 指针随 k2 提交推进。

## 一、逐项落件（载体 × 修法 × 负控 × 正控 × 回滚）

| # | 载体（pre → post sha16） | 修法 | 负控（修复前必红 / 异常路径） | 正控 | 回滚 |
|---|---|---|---|---|---|
| **C-22** | `eda_core/pipeline/config.py` `c9703f0f…` → **`16a771db…`** | `abs_path()` 基准由进程级 `REPO_ROOT`（cwd 派生）改为 **`project_root(cfg)`**（= pipeline.yaml 所在目录），**与 cwd 解耦**；绝对路径仍原样返回 | 修复前从**容器根**跑 `engine.py verify k2` ⇒ `FileNotFoundError: <容器根>/hw/sch/k2_sch.kicad_sch`（本轮已实测复现）；修复后同命令 **PASS** | 从 k2 根跑：`preflight`+3 **PASS**（不回退） | `git checkout 443dc23 -- eda_core/pipeline/config.py` |
| **C-4** | `eda_core/process_gate/state_machine.py` `8310ad4a…` → **`6be31691…`**<br>`cli.py` `a3eb5827…` → **`6b5e03a4…`**<br>`__init__.py` `afc53fb5…` → **`2e95633e…`** | 新增 **`redo_stage()`**（ECN 同阶段重做）：**不改阶段号**（`s_state` 保持 = 目标阶段）、不触碰更早阶段产物哈希、目标及其后阶段复位 `pending`、留痕 `redo_counts[stage]` + append 式 `regress_trace.md`；CLI 增 `redo [P0..P6] [--reason]` | 重做**尚未到达**的阶段（`P6` @ 当前 `P4`）⇒ `ProcessGateError`（fail-closed）；旧 `state.json` 无 `redo_counts` ⇒ 读盘补齐不炸 | `process_gate/tests` **12 passed**；`verify k2` 不回退 | `git checkout 443dc23 -- eda_core/process_gate/` |
| **C-1 残面** | `eda_core/truth_binding.py` `0683713d…` → **`5fdbbc6f…`** | 新增 **`dimension_source_bindings()` + `check_dimension_sources()` + CLI `check-dimensions`**：逐判据维要求 `source_of_truth` 声明（支持维内键与顶层 `dim_source_of_truth` 同构块），真源解析回**被验对象自身** ⇒ **拒**（`SelfSourceError`，非告警）；缺声明 ⇒ 拒；`enabled:false` 维跳过 | ① 缺声明 ⇒ `ok=False`；② `source_of_truth` 指向受审板自身 ⇒ **拒**；③ CLI 违规 ⇒ **退出码 1** | 真源为外部件 ⇒ `ok=True`；CLI 合规 ⇒ 退出码 0；**现行 19 维 verdict 逐字节不变** | `git checkout 443dc23 -- eda_core/truth_binding.py` |

**契约测试**：`eda_core/tests/test_batch4_contracts.py`（新件 `bfe69582…`，9,345 B）＝**14 passed**（含 C-22 端到端、C-4 CLI 冒烟与兼容、C-1 CLI 退出码）。

## 二、收尾四验（**全 PASS**）

| 项 | 命令 | 读数 |
|---|---|---|
| ① G-d | `cd k2 && PYTHONPATH=$PWD/_shared:$PWD python3 _shared/eda_core/pipeline/engine.py verify k2` | `preflight`+3 **PASS** |
| ② canonical 19 | `criteria/adjudicate.py …`（`l7` 册六件，**两次全新 `--drc-work-dir`**） | **19 OK / 0 FAIL** · `passed=true` · `provisional=false` · **两跑逐字节同** · verdict sha16 = **`190b73be0f728a56`（MATCH）** |
| ③ 验收门 | `AppDir/bin/python3.11 k2/tools/k2_p6_acceptance_gate_v1.py --expect-patched` | **PASS**（A 4/4 · B verify PASS · C K1=14/K2=14 **回退 0** · D hidden_failures=2 = 具名 C1/C2） |
| ④ C-22 专项 | **从容器根**跑 `verify k2` | `preflight`+3 **PASS**（修复前 = `FileNotFoundError`） |

## 三、零回退证据（套件）

- 容器根布局全量：**536 passed / 30 failed / 20 skipped**（批 3 基线 522P/30F/20S ⇒ **+14 = 本批新增契约测试**；**红集 30 / 跳集 20 逐数不变**）。
- 30 条红集分布：`test_verify_checks`6 · `test_redteam_evidence`6 · `test_closure_check`5 · `test_verify_cli_cache`4 · `test_verify_cli_smoke`3 · `test_env_fingerprint`3 · `test_hs_route_model`2 · `test_solve_pipeline`1 —— **与批 4 改动文件（config/process_gate/truth_binding）交集 = 0**。
- `process_gate` 自测：**12 passed**。
- **交付锚未动**：`MANIFEST 6ee7495d…` · tarball `0e88e107…` · 受审板 `l7 c5a7df90…`；冻结四源未动；`criteria/` 只读。

## 四、提交

| 仓 | commit | 内容 |
|---|---|---|
| `_shared`（容器） | **`02459f5`** | 批 4 三件同批一笔 + 契约测试 |
| `k2/_shared` | **`02459f5`**（**同 commit id**，逐字节同） | 同上 |
| `k2` | **`46f65f4`** | `_shared` 指针推进 `443dc23 → 02459f5` |
| `k2` | **`1dfc229`** | K1 复跑只读取证件 ×7（真源零改，非批 4 范围） |

## 五、未闭 / 待批（不属本批）

- **K1 三项解析器缺陷仍待批**：① `drc_rules.py` `rot=prot`（替代原「板改角」提案，后者经 pcbnew 真值判定会**制造真缺陷**）；② 无 net / 空号 pad 入几何域 + 显式登记 + 负控；④ `hs_route_model.py` 退化守卫（零长段）。
- **对级耦合**（`_k1_escape` 单网 VG → 成对）PoC 已证 2/3 链打通，待批落件。
- **P6 交付外部面仍关闭**（外部首件 V4–V7 8/8 `NOT_RUN`，ENG 不自证）。

—— ENG（ARCHER）· 2026-09-20 · 批 4 落件 · `_shared` `02459f5` · k2 `1dfc229` · 判据 rev=3
