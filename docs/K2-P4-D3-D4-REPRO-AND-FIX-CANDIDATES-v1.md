# K2 · P4 · `D-3` / `D-4` **最小复现包 + 修正候选**（真 hook 实跑；两提交路径）· v1 · 2026-09-18

> 缘起：handoff inc50 §6-3-(a)「D-3/D-4 引擎侧最小复现包（k2 侧 + 容器侧两提交路径各一例）」。
> 本会话仍**无监理放行** ⇒ ENlegal 面。仪器：`/tmp/opencode/inc51/`（fixture `d3A`/`d3B`/`d4`/`d4v` + 修正副本 `pre-commit.d3fix`、`eda_core`）+ **真 hook 脚本** `_shared/eda_core/pipeline/hooks/pre-commit`（`62dc6a4e476f6b55`）。**仓库零写入。**

## 0. 结论

1. **D-3 复现成立（两条提交路径，真 hook 实跑）**：`受影响项目` 行**均不出现** ⇒ per-project `engine verify` 被跳过。**修正候选在两条路径上均使其恢复**（出现 `受影响项目: k2` 且 verify 真跑到正控标记）。
2. **D-4 复现成立并已隔离**：`preflight.checks=[cmd false]` 下**原版 engine 报 `✓ phase 'preflight' PASS`（rc=0）** ⇒ `checks` 段**从未执行**；隔离对照（`verify=[cmd false]`）rc=1 ⇒ 引擎**并非**坏掉，缺陷专属 `checks`。**修正候选**使其 rc=1（`check [cmd]: FAIL`）。
3. 两项均属**共享引擎**（hook + engine，非本板补丁）；且因 **D-5**（k2 挂 `k2/_shared` 旧 pin），修完须**同时推进 k2 子模块的 `_shared` pin** 方对 k2 生效。

## 1. `D-3`：per-project `engine verify` 永不触发 —— 复现 + 修正（真 hook）

**fixture**：A =「仓根即项目根」（复刻 k2 子模块内提交）；B =「容器式 + 真 submodule gitlink」（复刻父仓提交）。
两者 `pipeline.yaml` 的 `verify` 段放**正控标记** `{type: cmd, cmd: "echo D3_VERIFY_RAN"}` ⇒ 「verify 真的跑了」可见。

| fixture | staged 名 | 原版 hook | **修正 hook** |
|---|---|---|---|
| **A**（仓根=项目根，`prefix='./'`） | `pipeline.yaml`, `docs/x.md` | **无** `受影响项目` 行 ⇒ verify 跳过 | **`受影响项目: k2`** + `k2 verify ...` + `verify/cmd: PASS` |
| **B**（容器式，`prefix='core/'`） | **`core`**（裸 gitlink）, `docs/readme.md` | **无** `受影响项目` 行 ⇒ verify 跳过 | **`受影响项目: k2`** + `k2 verify ...` + `verify/cmd: PASS` |

**修正（候选，仅 `/tmp`）** —— `hooks/pre-commit` 的 affected 计算：

```diff
-    root = str(yaml_path.parent.relative_to(config.REPO_ROOT)) + "/"
-    if any(c.startswith(root) for c in staged):
+    # D-3 修正: ① 仓根即项目根(str(rel)==".") ⇒ 本仓全部 staged 属该项目
+    #          ② 兼认 submodule gitlink（父仓内该子仓仅以裸名出现, 无 "/" 尾）
+    rel = str(yaml_path.parent.relative_to(config.REPO_ROOT))
+    if rel == ".":
+        hit = True
+    else:
+        hit = any(c == rel or c.startswith(rel + "/") for c in staged)
+    if hit:
         print(name)
```

**两半的必要性**（各自对应一条提交路径，均实测）：
- `rel == "."` → 修 **A**（k2 子模块内提交）；不加则 k2 自身提交**永远**看不到 verify。
- `c == rel` → 修 **B**（父仓对子仓只暂存裸 gitlink `core`，无 `/` 尾）；不加则父仓提交看不到 verify。
**副作用（可接受，须登记）**：多项目仓中「项目根恰好=仓根」的那一项会因任意 staged 路径而命中（略过触发，无害：仅多跑一次 verify）。

## 2. `D-4`：`phases[].checks` 引擎不执行 —— 复现 + 修正（三案，含隔离对照）

| # | 装置 | `engine` 调用 | rc | 输出结论行 | 性质 |
|---|---|---|---|---|---|
| 1 | `d4`：`preflight.checks=[cmd false]` | **原版** `preflight k2` | **0** | `✓ phase 'preflight' PASS` | **D-4 复现**（该失败的 checks 被跳过） |
| 2 | 同上 | **修正** `preflight k2` | **1** | `✗ phase 'preflight' 前置检查未通过 — 状态置 FAIL`（含 `check [cmd]: FAIL`） | **修正生效** |
| 3 | `d4v`：`verify=[cmd false]` | **原版** `verify k2` | **1** | `verify/cmd: FAIL` | **隔离对照**（引擎会执行 `verify`） |

⇒ 缺陷**专属** `checks` 段（`cmd_run` 只跑 `cmd`/`verify`），与 `verify` 无关。

**修正（候选，仅 `/tmp`）** —— `pipeline/engine.py::cmd_run`，插在「前序 phase 全 passed」之后、执行 `cmd` 之前：

```diff
+    # D-4 修正: checks = 该 phase 的前置门禁, 必须在 cmd/verify 之前执行
+    for spec in ph.get("checks", []):
+        print(f"  check [{spec.get('type')}]: ", end="", flush=True)
+        ok, detail = _run_check(cfg, spec)
+        if ok:
+            print("PASS")
+        else:
+            print("FAIL")
+            st.set_phase(stt, args.phase, "failed", {"error": detail})
+            st.save(stf, stt)
+            print(f"\n✗ phase '{args.phase}' 前置检查未通过 — 状态置 FAIL")
+            return 1
+
     # 执行阶段命令
     if ph.get("cmd"):
```

## 3. 与 `D-5` 的耦合（修完须推 pin 才对 k2 生效）

| | 值 |
|---|---|
| k2 提交实际执行的 hook | `k2/_shared/eda_core/pipeline/hooks/pre-commit`（k2 `_shared` pin `9a67d9e`） |
| 容器提交执行的 hook | `_shared/eda_core/pipeline/hooks/pre-commit`（容器 `_shared` HEAD `0ec324b`） |
| 二者 `pre-commit` | 同 sha `62dc6a4e476f6b55`（D-5 的差异只在 `pipeline/checks.py`） |

⇒ D-3/D-4 修在共享仓后，**k2 子模块的 `_shared` pin 必须同步前移**，否则 k2 提交仍跑旧 `engine.py`（D-4 仍复现）。**修 pin 属落件手续**（监理侧）。

## 4. 复跑（每处实测）

```bash
cd /home/fila/jqdDev_2025/ic_hw; M=/tmp/opencode/inc51
H=/home/fila/jqdDev_2025/ic_hw/_shared/eda_core/pipeline/hooks/pre-commit
# D-3：两路径 原版 vs 修正（期望 原版无「受影响项目」行；修正有且 verify 跑出 PASS）
(cd $M/d3A && bash $H) 2>&1 | grep -E '受影响项目|verify'
(cd $M/d3A && bash $M/pre-commit.d3fix) 2>&1 | grep -E '受影响项目|verify'
(cd $M/d3B && bash $H) 2>&1 | grep -E '受影响项目|verify'
(cd $M/d3B && bash $M/pre-commit.d3fix) 2>&1 | grep -E '受影响项目|verify'
# D-4：三案（期望 rc 0 / 1 / 1）
export SHARUN=/home/fila/jqdDev_2025/ic_hw/AppDir/sharun
(cd $M/d4  && PYTHONPATH=/home/fila/jqdDev_2025/ic_hw/_shared python3 -c "import sys;from eda_core.pipeline import engine;sys.exit(engine.main(['preflight','k2']))"); echo "rc=$?  # 原版 → 0(D-4 复现)"
(cd $M/d4  && PYTHONPATH=$M                                  python3 -c "import sys;from eda_core.pipeline import engine;sys.exit(engine.main(['preflight','k2']))"); echo "rc=$?  # 修正 → 1"
(cd $M/d4v && PYTHONPATH=/home/fila/jqdDev_2025/ic_hw/_shared python3 -c "import sys;from eda_core.pipeline import engine;sys.exit(engine.main(['verify','k2']))");    echo "rc=$?  # 隔离对照 → 1"
```

## 5. 边界

本件**只读 + `/tmp` fixture/副本（未落库）**：未改 `_shared/**`（D-3/D-4 补丁仅作用于 `/tmp` 副本）、生成器、模板、板、pro、库、`fp-lib-table`、`pm_gate/**`、SPEC、真源、`criteria/**`；未创建 `k2/pipeline.yaml`；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode`；未新增仓库内判据/脚本（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · hook `62dc6a4e476f6b55` · 容器 `_shared` `0ec324b` / k2 `_shared` `9a67d9e`
