# K2 · P4 · **`D-3` 三路径回归复核草案**（hook `affected`：原版 vs 修正版）· v1 · 2026-09-18

> 缘起：handoff inc70 §6-3-(z)「`D-3` **两路径**回归复核（容器式 + 仓根即项目根）在全修树上重跑」；本件按实测**扩为三路径**（新增「容器式裸 gitlink」）。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读 + `/tmp` fixture**，仓库零载体改动（仅新增本证据件）。
> 锚：原版 hook `_shared/eda_core/pipeline/hooks/pre-commit` **`62dc6a4e476f6b55`** · 修正 hook `/tmp/opencode/inc51/pre-commit.d3fix` **`61331e0bb17fa477`** · fixture `/tmp/opencode/inc51/{d3A,d3B}`、`/tmp/opencode/inc63/sandbox/mirror`。
> **归属**：`D-3` 属共享层 5 修之一；本件只出回归矩阵，**不改 `_shared/**`**（须放行）。

## 0. 结论（三条）

1. **原版 hook 在两种提交布局下均不命中**：**A 仓根即项目根**（`git -C k2 commit`，staged 名如 `docs/x.md`，`prefix='./'`）⇒ `受影响项目` **缺失**；**B 容器式裸 gitlink**（staged 名 `k2`，无 `/` 后缀，`prefix='k2/'`）⇒ 同样缺失。
2. **修正 hook（`rel=='.'` ＋ 裸 gitlink 处理）在两布局下均命中**：`受影响项目: k2` 出现，且**项目 verify 真被执行**（A/B 均打印 `verify/cmd: PASS`）。
3. **C 容器式子目录（项目为普通子目录、staged 为 `k2/...` 真文件）原版即命中**（与 inc58 §0-6 实测一致）⇒ `D-3` 的修正**只补 A/B 两支**，对 C 支**无回归**（两 hook 行为同为「命中」，差异仅在随后执行的 verify 结果，取决于引擎/判据）。

## 1. 三路径 × 两 hook 矩阵（实测）

| 路径 | fixture | staged（节选） | **原版 hook `62dc6a4e`** | **修正 hook `61331e0b`** |
|---|---|---|---|---|
| **A** 仓根即项目根（k2 子模块内提交） | `inc51/d3A` | `docs/x.md`, `pipeline.yaml` | rc=0 · **受影响项目 = 无** | rc=0 · **受影响项目 = k2** ＋ `verify/cmd: PASS` |
| **B** 容器式裸 gitlink | `inc51/d3B` | `core`, `docs/readme.md` | rc=0 · **受影响项目 = 无** | rc=0 · **受影响项目 = k2** ＋ `verify/cmd: PASS` |
| **C** 容器式子目录（真文件） | `inc63/sandbox/mirror` | `k2/pipeline.yaml`, `k2/docs/PROBE.md`, `k2/hw/**`, `k2/fab/**` | rc=1 · 受影响项目 = k2（`verify/sch_structural: PASS`，随后 `netlist_connect` ⑤ FAIL） | rc=1 · 同左（逐项一致） |

⇒ 判定：A/B **修正必要**（原版 fail-open）；C **无回归**（两版同命中；差异只在后续 check 结果，属 ⑤ 既有状态）。

## 2. 机制（为何 A/B 漏）

hook 计算 `affected` 时先取项目根相对仓根的 `prefix`，再要求 staged 路径 `startswith(prefix)`：
- **A**：`ROOT=k2`、`REPO_ROOT=k2` ⇒ `relative_to` 得 `.` ⇒ `prefix='./'`，而 staged 名是 `docs/x.md` ⇒ 不命中；
- **B**：容器级提交时 submodule 变更的 staged 名是 **gitlink `k2`**（无 `/` 后缀）⇒ `startswith('k2/')=False` ⇒ 不命中；
- **C**：staged 名为 `k2/...` ⇒ 命中。
修正 = ① `rel=='.'` 时用空前缀/当前目录语义；② 裸 gitlink（`k2`）视为命中该项目。**两者缺一都会漏**（A/B 各对应一支）。

## 3. 复跑（仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw
OLD=_shared/eda_core/pipeline/hooks/pre-commit; NEW=/tmp/opencode/inc51/pre-commit.d3fix
for fx in /tmp/opencode/inc51/d3A /tmp/opencode/inc51/d3B /tmp/opencode/inc63/sandbox/mirror; do
  for h in $OLD $NEW; do printf "%-52s %-22s " "$fx" "$(basename $h)";     (cd $fx && bash $h 2>&1 | grep -cE '受影响项目'); done
done
# 期望：A/B 原版=0、修正=1；C 两版=1
# 或一键：python3 /tmp/opencode/inc63/accept5.py   （该件含 D-3 三路径断言）
```

## 4. 边界

本件**只读 + `/tmp` fixture**：未改 `_shared/**`、判据、生成器、模板、板、pro、库、`fp-lib-table`、`pm_gate/**`、SPEC、真源、`criteria/**`；
**未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`**；未落件；未出 Gerber；未派 WORKER；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 原版 hook `62dc6a4e476f6b55` · 修正 hook `61331e0bb17fa477`
