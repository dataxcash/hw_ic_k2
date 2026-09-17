# K2 · P4 · `G11` + `D-3`/`D-4` **合并落地草案**（放行后一次投递 · 含「形式 vs 实质在岗」整合预演）· v1 · 2026-09-18

> 缘起：handoff inc56 §6-3-(d)「`G11` 与 `D-3`/`D-4` 的合并落地草案（供放行后一次投递）」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读 + `/tmp` 副本**，仓库零载体改动（仅新增本证据件）。
> 锚（sha16）：hook `62dc6a4e476f6b55` · 引擎 repo `97baca95a0b9bda7` / inc51 修正 `3dd370795a09cce2` / 本件补全 `a015f8cfcc24c581` · 生成器 `d8d15a31061f450f`。

## 0. 结论（五句）

1. **新增缺陷 `D-4b`（本会话发现）**：`D-4` 的 inc51 修正**必要但不充分**。提交期**唯一**判定入口是 hook 末段
   `PYTHONPATH=… python3 "$SHARED/eda_core/pipeline/engine.py" verify "$proj"` → `cmd_verify`；而 inc51 的 checks 门禁只加在 **`cmd_run`**。
   ⇒ `phases[].checks` 在**提交路径**上仍是纯声明 ⇒ **即使 D-3 与 D-4(inc51) 全修，装 `k2/pipeline.yaml` 依然＝「形式在岗」**（C-12 同型风险未消）。
2. **整合预演（真 hook + 真 engine，`/tmp`，4 案）**：案1（全未修）⇒ rc **0** 且无「受影响项目」行；案2（仅 D-3 修）⇒ rc **0**；
   案3（D-3 + inc51-D-4）⇒ **rc 0（fail-open 依旧）**；案4（再加 **D-4b**）⇒ **rc 1 拒绝提交**。
   **隔离对照**：同一案3 的引擎若走 `run <proj> verify`（`cmd_run` 路径）⇒ rc **1**（`check [cmd]: FAIL`）⇒ 证明 D-4 修正本身有效、缺口**专属 `cmd_verify`**。
3. **落地硬序（5 步）**：共享仓单笔修 **D-2 + D-3 + D-4 + D-4b + D-7** → §3 统一验收 → **前移 k2 的 `_shared` pin（D-5）** → 满足「`errata-*` + BOM」前置 → 装 `k2/pipeline.yaml`。
   **`G11` 与本链同批，但必须排在真源路径裁定（§5-8 甲/乙）之后**（见第 4 句）。
4. **交叉绑定风险（新登记，须同批处理）**：G11 实施后生成器读 `project.yaml::nets_yaml`（**现值 `errata-1`**），而变体② `pipeline.yaml` 的 `netlist_connect`
   指 `k2/hw/data/k2_sch.errata-2.yaml`（**甲**）⇒ **生成器与判据将指向不同真源**。故 **G11 不得先于 §5-8 裁定单独落**；若裁**乙**，`pipeline.yaml` 必须同步改指 `errata-1` + `D-7a`。
5. 本件**不新增检查齿**（owner ②）。`D-4b` 的**语义**问题（`cmd_verify` 应执行**全部 phase** 的 `checks`，还是**仅 verify phase** 的）属
   **判据语义澄清 ＝ 监理自有权**（#K2-19 §〇 二分），**请监理一并裁**；ENG 本件只出候选与证据。

## 1. 交付面与归属（一次投递的完整清单）

| 项 | 载体 | 归属 | 依据件 | 现状 |
|---|---|---|---|---|
| **D-2** 缺件→干净 FAIL（`checks.py` netlist/BOM） | 共享层 | 共享层属主 | `K2-P4-SHARED-LAYER-FAIL-OPEN-BUNDLE-v1.md` §2 | 复现 + 修正候选已验证 |
| **D-3** hook `affected`（仓根即项目根 / 裸 gitlink） | 共享层 `hooks/pre-commit` | 同上 | `K2-P4-D3-D4-REPRO-AND-FIX-CANDIDATES-v1.md` §1 | 已验证（两路径） |
| **D-4** `checks` 引擎不执行（**`cmd_run`**） | 共享层 `pipeline/engine.py` | 同上 | 同上 §2 | 已验证 |
| **D-4b** `checks` 在**提交路径**仍不执行（**`cmd_verify`**） | 共享层 `pipeline/engine.py` | 同上 | **本件 §2** | **本会话复现 + 修正候选已验证** |
| **D-7** NC 白名单只读 top-level（①②，不启用③） | 共享层 `checks.py` | 同上 | `K2-P4-D7-CONTROL-MATRIX-AND-C1-TRUTH-BINDING-v1.md` | 已验证（9 案） |
| **D-5** 前移 k2 的 `_shared` pin | k2 子模块 | **落件手续（监理侧）** | 本件 §4；bundle §4 | 待放行 |
| `k2/pipeline.yaml` 安装（**变体② phases-only**） | 项目侧 | gate 属主 | `drafts/p4-pipeline-yaml-disambiguation-v1/pipeline.phases-only.draft.yaml` `f049a4d97e6fe9cb` | 待放行 |
| **G11** 生成器 `nets_yaml` 配置驱动（约 3 行） | k2 生成器 | ENG（**须放行**） | `K2-P4-G9-GEOMETRY-BLOCKER-AND-G11-PATCH-v1.md` §1 | `/tmp` 已验证（A≡B、C 负控） |
| **P-1** `parse_ref_pcb` pad 正则 fail-open | k2 生成器 | ENG（**须放行**） | `K2-P4-U6-ZERO-PAD-CARRIER-ATTRIBUTION-v1.md` | `/tmp` 已验证（262→616） |
| 前置：`errata-*` 真源 + `k2/fab/k2_v4_bom.csv` | 项目侧 | 待裁（§5-8 甲/乙） | 安装面证据件 §4 | **未决** |

## 2. `D-4b`：复现 + 修正（本件核心）

**机制**：hook 末段只调用 `engine.py verify <proj>` ⇒ `cmd_verify`；其实现（repo 与 inc51 修正版**相同**）逐 phase 仅跑 `ph.get("verify", [])`，**从不读 `checks`**：

```python
def cmd_verify(args) -> int:          # hook 的唯一入口
    for ph in cfg["phases"]:
        for spec in ph.get("verify", []):   # ← 只有 verify；ph.get("checks") 从未被读
```

**整合预演（真 hook + 真 engine；同一 fixture，仅换 hook 变体 / `_shared` 树；`pipeline.yaml` 的 verify phase 内置探针 `checks:[{type:cmd, cmd:false}]` + `verify:[{type:cmd, cmd:echo D3_VERIFY_RAN}]`）**：

| 案 | hook | `_shared` 引擎 | 提交 hook **rc** | `受影响项目` | `checks` 是否执行 | 判定 |
|---|---|---|---|---|---|---|
| 1 | 原版（D-3 未修） | repo `97baca95` | **0** | **无** | 否（verify 根本没跑） | 形式在岗 |
| 2 | D-3 修正 | repo `97baca95` | **0** | `k2` ✓ | 否 | verify 跑了，但仍 fail-open |
| **3** | D-3 修正 | inc51 修正 `3dd37079`（仅 `cmd_run`） | **0** | `k2` ✓ | **否（hook 走 `cmd_verify`）** | **fail-open 依旧 ← `D-4b` 复现** |
| **3′** | —（隔离对照：引擎走 `run <proj> verify` ＝ `cmd_run` 路径） | inc51 修正 `3dd37079` | **1** | — | 是（`check [cmd]: FAIL`） | 证明 D-4 修正**本身有效** |
| **4** | D-3 修正 | **`D-4b` 修正 `07cc74af`**（`cmd_run` + `cmd_verify`） | **1** | `k2` ✓ | 是（`verify/check[cmd]: FAIL`） | **fail-closed ＝ 实质在岗** |

**修正候选（`D-4b`，仅 `/tmp` 副本；`engine.py::cmd_verify`，插在 verify 循环之前）**：

```diff
 def cmd_verify(args) -> int:
     ...
     for ph in cfg["phases"]:
+        # D-4b 修正: checks 是提交期前置门禁 ⇒ cmd_verify (hook 唯一入口) 必须先跑,
+        #            否则 checks 段在**提交路径**上永远是纯声明 (fail-open)
+        for spec in ph.get("checks", []):
+            ok, detail = _run_check(cfg, spec)
+            print(f"  {ph['id']}/check[{spec.get('type')}]: {'PASS' if ok else 'FAIL'}")
+            if not ok:
+                print("    " + detail.replace("\n", "\n    "))
+                return 1
         for spec in ph.get("verify", []):
             ok, detail = _run_check(cfg, spec)
             print(f"  {ph['id']}/{spec.get('type')}: {'PASS' if ok else 'FAIL'}")
```

**语义待裁（监理）**：候选**遍历全部 phase** 的 `checks`（视为「提交前必须成立的前置条件集」）。替代口径是**只跑 verify phase** 的 `checks`。
本板实际影响：变体② 把 `project_sch_coverage` 放在 **`preflight.checks`** ⇒ 若采「仅 verify phase」口径，该必选检查**仍不会在提交路径执行** ⇒ J-9「门禁接入」仍不成立。**ENG 建议采「全部 phase」**，但**归属监理裁定**。

## 3. 统一验收矩阵（每步过门才进下一步；不新增齿）

| 步 | 动作 | 验收（正控 + 负控） | 判定 |
|---|---|---|---|
| 1 | 共享仓单笔修 D-2/D-3/D-4/D-4b/D-7 | 复用 `SHARED-LAYER-FAIL-OPEN-BUNDLE` §3 全部正/负控 **＋ 本件 §2 案3/案4** | 全绿 |
| 2 | 前移 k2 `_shared` pin（D-5） | k2 提交路径 `engine.py` sha ＝ 修复后 commit 的 `engine.py`；`checks.py` 单侧分叉消失 | MATCH |
| 3 | 前置件：`errata-*`（按 §5-8 裁定）+ `k2/fab/k2_v4_bom.csv` | `netlist_connect`/`bom_consistent` 在**缺件负控**下干净 FAIL、在正控下 PASS | 全绿 |
| 4 | 装 `k2/pipeline.yaml`（变体②） | k2 内一次真提交：`受影响项目: k2` 出现 + `preflight/check[project_sch_coverage]` 执行 + 3 项 verify 全跑 | 实质在岗 |
| 5 | G11（+ P-1，同批） | A≡B 产物 sha 相同（inc48 §1）；C（无 `boards/`）rc=1；P-1 后 262→616 | 全绿 |

## 4. 硬顺序、回滚与「跳过后果」（具名）

```
[判据侧] 1 共享仓修 D-2/D-3/D-4/D-4b/D-7 → 2 统一验收 → 3 前移 k2 _shared pin → 4 装 k2/pipeline.yaml
[生成器侧] 5 裁 §5-8 甲/乙 → 6 G11 + P-1（同批）→ 7 生成器 /tmp 复跑（A≡B、C 负控、262→616）
```
- **跳过 3（不推 pin）**：k2 提交仍跑旧 `engine.py` ⇒ **D-4/D-4b 对 k2 无效** ⇒ 门禁是形式。
- **跳过 1 的 `D-4b`**：即使 pin 前移、`pipeline.yaml` 在库，`checks` 仍不在提交路径执行 ⇒ **J-9 形式在岗**（本件 §2 案3 实测 rc=0）。
- **先 6 后 5（G11 早于甲/乙裁定）**：生成器读 `errata-1`、判据读 `errata-2` ⇒ **两真源漂移**（本件 §0-4）。
- **回滚**：每步均为单文件/单 commit 级；`k2/pipeline.yaml` 删除即退出强制（状态文件 `pipeline.state.json` 随之失效，须一并清理）。

## 5. 交叉绑定（本件新增，须监理知悉）

| 绑定 | 内容 | 后果 |
|---|---|---|
| G11 ↔ `pipeline.yaml::nets_yaml` | `project.yaml::nets_yaml` 现为 `errata-1`；变体② 判据指 `errata-2`（甲） | 生成器与判据**不同源** ⇒ 先裁 §5-8，再决定 `pipeline.yaml` 指向 |
| G11 ↔ D-7 白名单 | D-7 ①②（top-level + `sheets[].placements[].nc`）决定 `errata-1` 的 105 误报是否收敛 | 若走乙（`errata-1`），D-7a **必须同批**，否则 k2 每次提交被 105 条自锁 |
| P-1 ↔ G9 | 同文件同段（`parse_ref_pcb` / pad 来源段） | 宜同批，避免二次动生成器（inc56 §6） |

## 6. 复跑（每处实测；仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw; W=/tmp/opencode/inc57; mkdir -p $W && cd $W
# ⓪ 三份引擎副本（自 repo `_shared/eda_core` 派生；两份补丁文本见 inc51 §2 与本件 §2）
#    shared_repo   = 仓库 _shared 原样（案1/案2 用）
#    shared_fixed  = repo 副本 + D-4(cmd_run)          ⇒ engine.py 期望 sha16 3dd370795a09cce2
#    shared_fix2   = repo 副本 + D-4(cmd_run) + D-4b(cmd_verify) ⇒ 期望 sha16 a015f8cfcc24c581
mkdir -p shared_fixed shared_fix2
cp -a ../inc51/eda_core shared_fixed/  2>/dev/null || { echo "先按 inc51 §2 打 D-4"; }
cp -a shared_fixed/eda_core shared_fix2/eda_core 2>/dev/null || true
#   （若 /tmp 已清空：cp -a $PWD_of_repo/_shared/eda_core 再按 inc51 §2 / 本件 §2 打补丁）
# ① 探针 pipeline.yaml（verify phase 内置 D-4 探针）
cat > probe.yaml <<'Y'
project: k2
phases:
  - id: preflight
    checks: [{type: project_sch_coverage}]
  - id: verify
    checks: [{type: cmd, cmd: "false"}]
    verify: [{type: cmd, cmd: "echo D3_VERIFY_RAN"}]
Y
# ② 四个 fixture（仓根＝项目根；真 .git；staged 含 pipeline.yaml+docs/x.md）
for c in 1 2 3 4; do
  mkdir -p d3c$c/docs && cp probe.yaml d3c$c/pipeline.yaml && echo x > d3c$c/docs/x.md
  git -C d3c$c init -q
  case $c in
    1|2) ln -sfn /home/fila/jqdDev_2025/ic_hw/_shared d3c$c/_shared ;;          # 未修引擎
    3)   ln -sfn $W/shared_fixed                      d3c$c/_shared ;;          # 仅 D-4(cmd_run)
    4)   ln -sfn $W/shared_fix2                       d3c$c/_shared ;;          # + D-4b
  esac
  git -C d3c$c add -A
done
# ③ 逐案：案1=仓库 hook（D-3 未修）；案2/3/4=/tmp/opencode/inc51/pre-commit.d3fix（需按 inc51 §1 重建）
H=/home/fila/jqdDev_2025/ic_hw/_shared/eda_core/pipeline/hooks/pre-commit; HF=/tmp/opencode/inc51/pre-commit.d3fix
for c in 1 2 3 4; do [ $c -eq 1 ] && HOOK=$H || HOOK=$HF;   (cd d3c$c && bash "$HOOK" > case$c.log 2>&1); echo "case$c rc=$?";   grep -E '受影响项目|check \[|verify/|拒绝提交' d3c$c/case$c.log; done
# ④ 隔离对照：案3 引擎走 cmd_run 路径 ⇒ 期望 rc=1
cd d3c3 && PYTHONPATH=$W/shared_fixed:$PWD python3 $W/shared_fixed/eda_core/pipeline/engine.py run k2 verify; echo "rc=$?"
```

**期望**：案1 rc0 / **无**「受影响项目」· 案2 rc0 / 有「受影响项目」· 案3 **rc0**（`D-4b` 复现）· 案4 **rc1**（拒绝提交）· 隔离对照 **rc1**（`check [cmd]: FAIL`）。
**sha 自校验**：`shared_fixed/eda_core/pipeline/engine.py` = `3dd370795a09cce2`（inc51 的 D-4 修正）；`shared_fix2/…/engine.py` = `a015f8cfcc24c581`（= **本件 §2 diff 逐字**（含注释行）应用之结果；补丁文本（含注释）改一字即 sha 变 ⇒ 比对 sha 前先逐字对齐 §2）。

## 7. 边界

本件**只读 + `/tmp` 副本/fixture（未落库）**：未改 `_shared/**`、生成器、模板、板、pro、库、`fp-lib-table`、`pm_gate/**`、SPEC、真源、`criteria/**`；
**未创建 `k2/pipeline.yaml`**；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode`；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · hook `62dc6a4e476f6b55` · 引擎 repo `97baca95a0b9bda7` / inc51 `3dd370795a09cce2` / D-4b `a015f8cfcc24c581`
