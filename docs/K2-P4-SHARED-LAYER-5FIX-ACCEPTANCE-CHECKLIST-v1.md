# K2 · P4 · **共享层 5 修「一次派单件」验收清单**（D-2/D-3/D-4/D-4b/D-7；一键跑通 13/13）· v1 · 2026-09-18

> 缘起：handoff inc70 §6-3-(x)「共享层 5 修整包『一次派单件』的**验收清单细化**（逐项验收命令 + 期望输出，整合 inc51/57/58/68/69 的既有矩阵，纯文档）」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读 + `/tmp` 仪器**，仓库零载体改动（仅新增本证据件）。
> 锚：`K2-P4-SHARED-LAYER-FAIL-OPEN-BUNDLE-v1.md` **`e22c2e4423bab287`**（§3 原清单，**未含 D-4b**）· 修版 engine `a015f8cfcc24c581`（D-4+D-4b）· 修版 checks `0cbd9a478c694a12`（D-2+D-7 开关式）· hook 修正 `pre-commit.d3fix` **`61331e0bb17fa477`** · repo hook `62dc6a4e476f6b55` · k2 `_shared` pin `9a67d9e`（`checks.py` 分叉 `e88c70aaa56ce22f`）。
> 装置（`/tmp`，易失）：**一键验收器** `/tmp/opencode/inc63/accept5.py` **`088b0a7ce04a3f90`** → 日志 `accept5.log` **`713b5f16a6b9d753`**。
> **归属**：共享层属主修 + 验收；本件只出**验收清单与实测结果**，**不新增检查齿**（owner ②）。

## 0. 结论（三条）

1. **一键统一验收跑通：13/13 PASS**（`D-2` 1 · `D-3` 3 · `D-4` 3 · `D-4b` 5 · `D-7` 1），各子项均有**正控 + 负控**（避免「全绿即通过」的假绿）。
2. 本清单**补全 bundle §3 的缺口**：① 纳入 **`D-4b`**（提交路径 `cmd_verify` 执行 `checks`，bundle 原清单**未含**）；② `D-3` 扩为**三路径**（原清单仅两 fixture）；③ `D-2` 采用 **engine 固定、仅换 checks** 的隔离式两臂（而非只跑成功路径）。
3. **落库硬序不变**：共享仓单笔修 5 项 → 本清单验收 → **前移 k2 `_shared` pin（D-5）** → 前置件（`errata-*` + `k2/fab/k2_v4_bom.csv`）→ 装 `k2/pipeline.yaml`。**未按此序只装 pipeline.yaml ⇒ J-9 形式在岗、实质 fail-open**。

## 1. 逐项验收表（期望＝判据；实测＝本会话）

| 修 | 装置 / 命令 | 期望 | 实测 |
|---|---|---|---|
| **D-2** 缺件→干净 FAIL | `python3 /tmp/opencode/inc63/d2_matrix.py`（engine 固定 `a015f8cf`；臂 `0cbd9a47` vs `02b41e8b`） | 修版：`nets_yaml`/`bom_csv` 缺件均 **RC=1 + 「缺件…fail-closed」**（无 traceback）；正控 rc=0 PASS。未修版两负控 **FileNotFoundError** | **PASS**（6 行矩阵逐项符合） |
| **D-3** hook `affected` 三路径 | `bash <hook>` × {A 仓根即项目根 `inc51/d3A` · B 容器式裸 gitlink `inc51/d3B` · C 容器式子目录 `inc63/sandbox/mirror`} | A/B：原版**不命中**、d3fix **命中**；C：原版**已命中**、d3fix 命中 | **PASS（3/3）** |
| **D-4** `cmd_run` 执行 `checks` | `engine preflight k2`：`inc52/d4ok`（`cmd:true`）+ 修版引擎 ⇒ rc0；（`inc51/d4`，`cmd:false`）+ 修版 ⇒ **rc1**；同 fixture + **未修引擎** ⇒ **rc0（fail-open 复现）** | 0 / 1 / 0 | **PASS（3/3）** |
| **D-4b** `cmd_verify` 执行 `checks`（**提交路径**） | `bash pre-commit.d3fix` × 4 案（`inc57c/d3c1..4`）：案1 原版 hook+未修引擎 ⇒ rc0 无「受影响项目」；案2 D-3 修 ⇒ rc0 有；案3 +D-4 ⇒ **rc0（fail-open 复现）**；案4 +D-4b ⇒ **rc1 拒绝提交**；**隔离对照**：案3 走 `run k2 verify` ⇒ rc1 | 0 / 0 / 0 / 1 / 1 | **PASS（5/5）** |
| **D-7** NC 白名单开关（①②，不启③） | `python3 /tmp/opencode/inc63/d7_matrix.py`（D-7-only 树 vs **合并全修树**，九案） | 两树逐案一致且＝`1 106 2 1 106 PASS PASS 105 2` | **PASS** |

## 2. 落库顺序（与 `D-5` pin 前移的耦合）

| 步 | 内容 | 归属 | 验收证据 |
|---|---|---|---|
| 1 | 共享仓**单笔**修 `D-2 + D-3 + D-4 + D-4b + D-7` | 共享层属主 | 本件 §1 全表 |
| 2 | 跑 §1 一键验收（13/13 PASS） | 共享层属主 + 监理 | `accept5.py` / `accept5.log` |
| 3 | **前移 k2 `_shared` pin**（`9a67d9e` → 修复后 commit；消 `checks.py` 分叉 `e88c70aaa56ce22f`） | 落件手续（监理侧） | 见 bundle §4 的 D-5 现状表 |
| 4 | 落前置件：`errata-*`（甲/乙）＋ `k2/fab/k2_v4_bom.csv` | 待裁/ENG 已备件 | inc64 (m)/(n) |
| 5 | 装 `k2/pipeline.yaml`（变体②）⇒ 门禁**实质**在岗 | gate 属主 | inc58 端到端 + inc64 §4 |

## 3. 一键复跑（仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw
python3 /tmp/opencode/inc63/accept5.py ; echo "rc=$?"      # 期望 rc=0，汇总 13/13 PASS
```
（前置：`/tmp/opencode/{inc50,inc51,inc52,inc57c,inc63}` 仪器树存在；易失，按各件 §复跑 重建。）

## 4. 边界

本件**只读 + `/tmp` 仪器**：未改 `_shared/**`、判据、生成器、模板、板、pro、库、`fp-lib-table`、`pm_gate/**`、SPEC、真源、`criteria/**`；
**未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`**；未落件；未出 Gerber；未派 WORKER；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 验收器 `088b0a7ce04a3f90` · 日志 `713b5f16a6b9d753`
