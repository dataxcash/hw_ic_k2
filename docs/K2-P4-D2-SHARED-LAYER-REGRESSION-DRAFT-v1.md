# K2 · P4 · **共享层 `D-2` 回归复核草案**（缺件 → 干净 FAIL；A/B 两臂 × 三案）· v1 · 2026-09-18

> 缘起：handoff inc68 §6-3-(w)「`D-2` 回归复核（以 inc58 全修树复跑缺件/缺目录负控，纯 `/tmp`）」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读 + `/tmp` 两臂副本**，仓库零载体改动（仅新增本证据件）。
> 锚：**修版 checks** `/tmp/opencode/inc58/shared_full/eda_core/pipeline/checks.py` **`0cbd9a478c694a12`**（＝inc50 D-7 开关式 ＋ inc52 D-2 各处缺件 guard）· **未修版 checks** 容器 `_shared/eda_core/pipeline/checks.py` **`02b41e8b6d6d9b3a`**（D-2 未修）· **engine 固定** `/tmp/opencode/inc58/shared_full/…/engine.py` **`a015f8cfcc24c581`**（D-4+D-4b，**两臂同 engine 以隔离 checks**）。
> 装置（`/tmp`，易失）：`/tmp/opencode/inc63/sandbox/d2/{shared_d2,shared_nod2,root,gen/*.yaml}`。
> **归属**：`D-2` 属**共享层 5 修之一**（与 `D-3`/`D-4`/`D-4b`/`D-7` 同笔）；本件只做回归复核，**不改 `_shared/**`**（须放行）。

## 0. 结论（四条）

1. **`D-2` 修正前**：`nets_yaml` 或 `bom_csv` 指向缺件时，check **抛未捕获 `FileNotFoundError`**（进程以 traceback 结束）——这是 **fail-open 型**行为：`cmd_verify` 的「干净 FAIL + 拒绝提交」语义被破坏，hook 侧只能看到异常。
2. **`D-2` 修正后**：同一对负控给出**干净 FAIL**：`netlist_connect 缺件: <绝对路径> — fail-closed` / `bom_consistent 缺件: <绝对路径> — fail-closed`，`rc=1`，与既有「拒绝提交」路径一致。
3. **正控不受影响**：BOM 存在时 `bom_consistent: PASS`（`rc=0`）；`nets_yaml` 指向存在的 `errata-1` 时行为与既有 ⑤ 判定一致（`netlist_connect: FAIL`，2 行）。
4. **隔离性**：两臂 **engine 同一份**（`a015f8cf`），仅 `checks.py` 不同（`0cbd9a47` vs `02b41e8b`）⇒ 差异**只归因 `D-2`**。

## 1. 回归矩阵（2 臂 × 3 案；`K2_NC_SOURCES=top,placements`）

| 案（探针改法） | **修版 `0cbd9a478c694a12`** | **未修版 `02b41e8b6d6d9b3a`** |
|---|---|---|
| `nets_yaml` → 缺件（`…errata-2.yaml`） | rc=1 · **`netlist_connect 缺件: … — fail-closed`** | rc=1 · **`FileNotFoundError`**（traceback） |
| `bom_csv` → 缺件（`…missing.csv`，单 `bom_consistent` 探针） | rc=1 · **`bom_consistent 缺件: … — fail-closed`** | rc=1 · **`FileNotFoundError`**（traceback） |
| 正控：BOM 存在（单 `bom_consistent` 探针） | rc=0 · `bom_consistent: PASS` | rc=0 · `bom_consistent: PASS` |
| 正控：件齐备（含 `netlist_connect`） | rc=1 · `netlist_connect: FAIL`（**既有 ⑤**，2 行）※ | rc=1 · 同左 ※ |

※ ⑤（`PWR_5V_KEY` ＋ `C89/A_1`）与本件无关，仅说明探针仓的既有状态；**BOM 分支须用单检查探针**才能绕过 `cmd_verify` 的「首个 FAIL 即 return」。

## 2. 与共享层一次派单件的关系

| 项 | 现状 | 本件贡献 |
|---|---|---|
| `D-2`（缺件 → 干净 FAIL） | 修版候选已验证（inc52）；**未落共享仓** | 两臂 A/B 回归矩阵（engine 隔离） |
| 落库序 | 见 `K2-P4-G11-D3-D4-MERGED-LANDING-DRAFT-v1.md` §3 | 与 `D-3/D-4/D-4b/D-7` **同一笔**；随后 **`D-5` pin 前移**，hook 才用得上 |
| 前置件 | `errata-*` + `k2/fab/k2_v4_bom.csv` | 缺件负控的存在性即由这两件引入（见 (m)/(n) 件） |

## 3. 复跑（仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw
sha256sum /tmp/opencode/inc58/shared_full/eda_core/pipeline/{engine.py,checks.py} \
          /tmp/opencode/inc63/sandbox/d2/shared_nod2/eda_core/pipeline/checks.py | cut -c1-16
python3 /tmp/opencode/inc63/d2_matrix.py     # 期望：修版两负控=干净「缺件…fail-closed」；未修版=FileNotFoundError；正控两臂 rc=0 PASS
```
（`d2_matrix.py` 与本件同源：engine 固定 `a015f8cfcc24c581`，仅换 `checks.py` 两版 ⇒ 差异只归因 `D-2`。）

## 4. 边界

本件**只读 + `/tmp` 两臂副本/探针仓**：未改 `_shared/**`、判据、生成器、模板、板、pro、库、`fp-lib-table`、`pm_gate/**`、SPEC、真源、`criteria/**`；
**未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`**；未落件；未出 Gerber；未派 WORKER；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 修版 checks `0cbd9a478c694a12` · 未修版 `02b41e8b6d6d9b3a` · engine `a015f8cfcc24c581`
