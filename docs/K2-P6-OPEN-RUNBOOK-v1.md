# K2 · **P6 开闸一次性执行单（Runbook v1）** · 2026-09-20 · ENG（ARCHER）

> 用途：把批 2 落件后**已备料但须放行**的动作排成一条可执行序列，供监理放行后**一条条跑、逐条留痕**。
> 现状：**批 2 = 已落件**（`shared fc59771` · `k2 12ab8b4`）· **P6 交付阶段 = 仍关闭**（P6-1/P6-2 · K1 复跑 · 外部首件 未放行）。
> 红线：冻结件 `d4e81f64…` 永不改 · `criteria/` ENG 只读 · 未获批不改生成器/SPEC/原理图 · 禁派 WORKER · 冲突即停机。

## §0 前置门（任一未过则不得进入 §1）
| 门 | 态 | 归属 |
|---|---|---|
| G-d 回归门（`engine verify k2` preflight+3 · canonical 19/19 · 两跑逐字节同） | ✅ **PASS**（本会话实测，`ACCEPTANCE_GATE_v1.json` = PASS） | ENG |
| **G-c2** `criteria/manifest.k1.yaml`（应然集） | ❌ 缺 ⇒ `adjudicate.py:536` fail-closed（已实测） | **监理**（P6 开闸时原子落件） |
| P6-2 模板整改方案 | ⏸ 三选一未裁（**O1/O2/O3**，见 §1.3） | **监理** |

## §1 执行序（放行后逐步执行，禁跳步）

### 1.1 G-c2 落件后 —— 跑 P6-1 出 verdict
- **输入口径（须监理先裁）**：`results_template.json` 原文用 `--nets k1/boards/k1_nets.yaml`，**实测崩溃**（`KeyError: 'symbols'`，`adjudicate.py:149`）；同目录 `k1/boards/k1_sch.yaml` 与 K2 `errata-2` **同构可跑**（PROBE 实测 `n_pass=3 / n_fail=16`）。
- 命令（选定 `--nets` 后）：
  ```
  python3 criteria/adjudicate.py --project k1 --board k1/k1_v1.kicad_pcb --pro k1/k1_v1.kicad_pro \
    --nets <裁定输入> --sch-dir k1/sch --root . \
    --measure-out /tmp/opencode/k1_measure.json --out /tmp/opencode/k1_verdict.json
  ```
- 判据：verdict **须命中四项同源缺陷** = `ignore_without_ruling(9)` · `no_pipeline(1)` · `no_fp_lib_table(1)` · `sheets_empty(1)`（四项**已逐项实测取证**：9/62 具名 · `k1/sch` · `k1/` 缺 fp-lib-table · `k1_v1.kicad_pro.sheets==[]`）。
- PROBE 参考读数（未签认，供对照）：`n_pass=3 / n_fail=16`，其余维须由监理在 `manifest.k1.yaml` 中裁定 enabled / 豁免 / 补测量件。

### 1.2 P6-2 —— 模板整改（**三选一**，见 `P6_OPEN_READINESS/co81_vs_template_matrix.json`）
- **冲突事实**：CO-81（L2 回归闸）要求**每个 tracked `*.kicad_pro` 的 `rule_severities` == `tools/k2_jlc_template.kicad_pro`**。现状 **7/10 合规、3 mismatch**（`hw/k2_v4_8L.l5/l6/l7.kicad_pro` = 0 ignore vs 模板 9，**自 P4 起静默失守**）；模板单独改（A′）会**连带 7 个 mismatch**（含 `archive/k2_v4_6L/*` 两件历史记录 + 设计源/冻结板配套 pro）。
- **O1 全集合一**（模板 + 其余 9-ignore 真实文件一次性 →`warning`，**含 archive/6L 两件**）：
  `P6_OPEN_READINESS/P6_2_template_proposal/O1_fullset/*.diff`（6 件）⇒ 应用后 **重跑并重签 CO-81**。
  - ⚠ **更正 #1（2026-09-20 实测）**：补丁头为 `a/k2/…`、`a/k1/…` ⇒ **须用 `-p2`**：k2 五件在 **k2 仓库根**（`cd k2 && patch --posix -p2 < …`），k1 模板在 **k1 仓库根**。原文 `-p3` **会 strip 到文件名** ⇒ 交互提示 `File to patch:`，非交互下即挂住（并可能留半打补丁树）。
  - ✅ **实测（scratch 镜像，真源零改）**：k2 10 件受控 pro 结构差异 **3 → 0**；两模板 ignore 集 **∅ == manifest 应然集 ∅**（`rule_severity_manifest.expect` + `rule_severity_exemptions: []`）⇒ **满足计划 P6 判据②**；补丁外科性 = **54 字段全 `ignore→warning`、非 `rule_severities` 字段 0**；受审板 `l7` pro **不在补丁集**。件：`P6_execution/P6_2_O1_MEASURED_v1.json`（`bf7b8d91cb4f384c`）。
- **O2 闸改口径**：CO-81 的 severity 子句 `== 模板` → `== manifest 应然集`（与 P6-2 判据同源）⇒ 改工具 + 重跑重签。
- **O3 维持现状**：P6-2 判据不成立（模板仍 9）⇒ 不建议。
- 落件后复核：`P6-2 结构差异 = 0`（模板 ignore 集 == manifest 应然集）。

### 1.3 板锚修（1 行）+ 工具容忍（配套 2 行）—— **建议并入下一批**（C-6）
- 事实：`K2V4_REAL_BOARD` 相对锚 ⇒ 容器 `_shared` 检出下 **22 项静默 skip**（框架自身基线工具读到 mask 视图 `41P/34S`）。
- 命令：应用 `P6_OPEN_READINESS/anchors/K2V4_REAL_BOARD_absolute.diff`（**须在 `_shared` 检出内跑**：`-p3` strip 后为 `eda_core/tests/…`，**两处** `_shared` 各一次；不在 `_shared` 根跑会提示 `File to patch:`）**并**把 `k2_p6_shadow_verify_v1.py` 的板锚补丁改容忍（否则验收门 D 腿 AssertionError）。
- 读数（**2026-09-20 实测，非期望**）：容器根布局 `492P/28F/42S → 512P/30F/20S`；归因 **22 = 20 skip→PASS + 2 skip→FAIL（具名 C1/C2）**、**回退 0**；k2 检出版零变化。件：`P6_execution/NATURAL_LAYOUT_ANCHOR_FIX_MEASURED_v1.json`（`23e88403a42df1b8`）+ `evidence_anchor_fix/*.xml`。
  配套件（**必随本修同批**）：`P6_OPEN_READINESS/companion/K2P6_SHADOW_VERIFY_ANCHOR_TOLERANCE.diff`（`cd k2 && patch --posix -p1 < …`）—— 实测：**不落此件则落锚后验收门 D 腿必 `AssertionError`**（`COMPANION_PROBE_v1.json`）。

### 1.4 批 2 收口件（其余两项）
- **12 SKIP 处置**（四选 `S1–S4`，见 `BATCH2_SKIP12_DISPOSITION_v1.json`）：`S1` 具名接受 ⇒ 在册登记退役 + 显式登记 `solve_pair_segment`/`solve_chain_v2` **覆盖真空**。
- **B2-4 撤 K1 `G1.5` WAIVER**（一条命令，见 §2 索引）：`python3 .../apply_k1_g15_waiver_retraction_v1.py --root <k1> --apply` ⇒ 复跑 `check_g15` 与 `k2_p6_readonly_baseline_v1.py`（`is_waiver` 标记消失）。

### 1.5 收尾（每步之后）
复跑三元验收：① `cd k2 && PYTHONPATH=$PWD/_shared:$PWD python3 _shared/eda_core/pipeline/engine.py verify k2` = preflight+3 PASS；② canonical 19 维（命令见落件报告 §0）；③ `--expect-patched` 验收门 PASS（A 4/4 · C 回退 0 · D hidden=2 具名 C1/C2）。**两跑逐字节同**方可入库。

## §2 已备料件索引（sha16 · 一条命令级）
| 件 | sha16 | 用途 |
|---|---|---|
| `P6_OPEN_READINESS_v1.json` | `d1715de0b2e6b165` | P6-1/P6-2 就绪全量（含四项取证、PROBE 读数、跨板普查） |
| `P6_OPEN_READINESS/co81_vs_template_matrix.json` | `01f7220311480cda` | CO-81 × P6-2 冲突矩阵 + O1/O2/O3 |
| `P6_OPEN_READINESS/P6_2_template_proposal/O1_fullset/*.diff` | 见 `META.json` | O1 全集合补丁 6 件（dry-run OK） |
| `P6_OPEN_READINESS/anchors/K2V4_REAL_BOARD_absolute.diff` | `310b5f80892e8f54` | 板锚修（1 行） |
| `P6_OPEN_READINESS/apply_k1_g15_waiver_retraction_v1.py` | `fc0cbd71b4d6701b` | B2-4 撤 waiver（幂等；默认 --check） |
| `P6_OPEN_READINESS/B2_4_K1_G15_WAIVER_RETRACTION_v1.json` | `647c6dd7688abb47` | B2-4 证据包 |
| `BATCH2_SKIP12_DISPOSITION_v1.json` | `fdbb8f3a099e0600` | 12 SKIP 逐条具名 + S1–S4 |
| `SUITE_BASELINE_AND_BATCH2_DELTA_v1.json` | `9e5ec990e00eed61` | 套件级前/后（零回退、净修 11） |
| `SUITE_LAYOUT_ASYMMETRY_AND_ANCHOR_FIX_v1.json` | `beb0a82c51015c25` | 双布局差异取证 |
| `CROSSBOARD_GATE_DELTA_v1.json` | `8404572a8275cfb0` | K1 4→14 / K2 12→14（回退 0） |

## §3 回滚
各步均为**单点、可 git revert 的文件级变更**：模板（O1）= 6 文件 9 行；锚修 = 1 行；B2-4 = 2 文件（含原 WAIVER 归档键）；工具容忍 = 2 行。**无一步触及冻结 `.kicad_pcb` / 交付锚 / `criteria/`。**

—— ENG（ARCHER）· 2026-09-20 · 计划件（**非交付件**）
