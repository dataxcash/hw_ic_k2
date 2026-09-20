# K2 · **下一批（批 3）裁定请求单 + 一键执行序** · v1 · 2026-09-20 · ENG（ARCHER）

> 用途：把 handoff §3 的 **8 项未决**压成**一张单**，供**监理**一次裁定 → ENG 一批落件 → 一次三元验收。
> 依据：C-6（**禁零散补丁**：共享层/测试锚/工具改动一律同批升版）· 宪法第十一条（**全属监理职权**）。
> **owner 闸口 = 无**：本单**无 L1 项**（无拓扑/接口/信号流向/球重映射），亦**不动 owner 系统/账号/预算**。
> 红线自检：冻结四源/`criteria/`/交付锚未动 · 未派 WORKER · 临时件仅 `/tmp/opencode` · `criteria/` ENG **只读**。

## 0. 本会话（ENG）已推进的三件（**新增**，把手上的"预期/散文"变成"实测/件"）

| # | 件 | 读数 | 件（sha16） |
|---|---|---|---|
| 1 | **板锚修实测**（原为"预期"） | 容器根布局全量套件 **492P/28F/42S → 512P/30F/20S**；归因 **22 项状态变更 = 20 skip→PASS + 2 skip→FAIL（C1/C2 具名）**；**回退 0**（无 PASS→FAIL） | `NATURAL_LAYOUT_ANCHOR_FIX_MEASURED_v1.json` `23e88403a42df1b8` |
| 2 | **同伴件**（原仅散文："2 行工具容忍"） | 已成**可用补丁**（`patch -p1 --dry-run` 过）＋**实测证明其必要性**：落锚后**现状工具必 `AssertionError`**（验收门 D 腿失效）；同伴件后两态皆通、且形态不识别时**仍 fail-closed** | `P6_OPEN_READINESS/companion/{K2P6_SHADOW_VERIFY_ANCHOR_TOLERANCE.diff,COMPANION_PROBE_v1.json}` `0bc59be8dc154be8`/`c4b4c29b450099e7` |
| 3 | **残留 20 项 SKIP 全登记**（收尾面） | 20 = **17**（m9demo 族/3 模块，与既有"17 项"逐项对上）+ **2**（v5/v6 外部 fixture）+ **1（新发现）** 路径缺陷**永久掩盖**用例：解锁后 **FAIL**（旧代际期望） | `BATCH3_RESIDUAL_SKIP_REGISTER_v1.json` `1b6d5b7d36746399` |

> 实测方法学（可复现）：实体板锚修**瞬时落**→ 跑全量套件 → `git checkout` **无条件回退**（trap）；回退后逐 sha/`git status` 复核**逐字节复原**（`_shared` 与 `k2/_shared` test 文件 sha256 回到 `93af4803…`，HEAD 仍 `fc59771`）。第二法 = `/tmp/opencode/natfix` **容器布局副本**独立复跑，两法互证（副本 vs 真容器 差 = **恰 2 项具名环境差**）。

## 1. 裁定请求（逐项：现状 → ENG 建议 → 一键命令 → 期望读数 → 回滚）

| # | 事项 | 现状 | **ENG 建议** | 一键执行 | 期望读数 | 回滚 |
|---|---|---|---|---|---|---|
| 1 | **板锚修 + 同伴件** 落件时机 | 批 2 已落件；本项属**同族修正件**（测试锚） | **并入批 3 同批落**（C-6）；落件范围 = `_shared`×2 + 同伴件 | ① `cd k2/_shared && patch -p3 < …/K2V4_REAL_BOARD_absolute.diff`；② `cd _shared && patch -p3 < <同>`；③ `cd k2 && patch -p1 < …/companion/…diff` | 容器根 512/30/20；k2 检出零变化；`--expect-patched` PASS | 3 文件级 `git checkout` |
| 2 | **G-c2** `criteria/manifest.k1.yaml` | 缺 ⇒ `adjudicate.py:536` fail-closed | **按 #K2-41 §三-⑥ 已裁内容**，由**gate 属主**于 P6 开闸时**原子落件**（ENG 对 `criteria/` 只读，不代笔） | 监理侧落件 | 应然集 = `ignore_without_ruling(9)/no_pipeline(1)/no_fp_lib_table(1)/sheets_empty(1)` | 删该文件 |
| 3 | **P6-1 `--nets` 口径** | `k1_nets.yaml` **实测崩溃**（`KeyError:'symbols'`）；`k1_sch.yaml` 同构可跑 | 用 **`k1/boards/k1_sch.yaml`**；判据 = 命中四项同源缺陷（不缩口径） | 见 `results_template.json` P6-1 段（`--nets k1/boards/k1_sch.yaml`） | PROBE 参考 `n_pass=3/n_fail=16`（未签认）+ 四项命中 | 无（只读运行） |
| 4 | **P6-2 模板整改** O1/O2/O3 | 7/10 合规、3 mismatch；模板单改（A′）更差 = 7 mismatch | **O1 全集合一**（补丁已备、dry-run 全 OK）；**子问题**：`archive/k2_v4_6L/*` 两件历史记录**是否纳入**（不纳入 ⇒ O1 变体） | `cd k2 && for d in …/O1_fullset/*.diff; do patch -p3 < $d; done` | 结构差异 = 0；重跑重签 CO-81 | 6 文件 9 行 |
| 5 | **12 SKIP 处置** S1–S4（+ 新发现 C 类） | 12 项 = /tmp m9demo 基线 + 6L 旧 SPEC + RETIRED alloc | **S1 具名接受（登记退役）**，并**显式登记** `solve_pair_segment`/`solve_chain_v2` **覆盖真空**；**新发现** `test_cap_wall_upgrade::test_window_params_k2_data_driven` 归 **S3/S4**（解锁即 FAIL，非路径修） | 落"退役+覆盖真空"登记件（ENG 出件，监理签） | skip 数不充绿、逐条具名 | 文档级 |
| 6 | **B2-4 撤 K1 `G1.5` WAIVER** | 前置已满足（`RULES_DOC` 项目根化）；幂等（`patched→already`） | **撤**（一条命令） | `python3 …/apply_k1_g15_waiver_retraction_v1.py --root <k1> --apply` | `is_waiver` 标记消失；K1 G1.5 真机 PASS | 2 文件（含原 WAIVER 归档键） |
| 7 | **B2-1 / B2-2 授权口径** | v3 表标"授权=无"，附注"共享层改动须监理批" ⇒ **口径冲突** | 按 **#K2-41 §三-② 同例**：`_shared` 改动**须监理批**；B2-1/B2-2 建议**并入批 3** 同批落 | 批 3 补丁集（与 1 同批） | `_shared` 通用（零单板特判）+ G-d 必过 | 文件级 |
| 8 | **外部首件** P5 V4–V7 | 8/8 `NOT_RUN` | **不由 ENG 自证**；回件后由监理/外部填 `L6/first_article/results_template.json` | — | — | — |

## 2. 批 3 落件后**唯一**验收（每步后 / 收尾各一次）

① `cd k2 && PYTHONPATH=$PWD/_shared:$PWD python3 _shared/eda_core/pipeline/engine.py verify k2` ⇒ `preflight`+3 **PASS**
② canonical 19 维（命令见 `L4/E3-standard-call-l7-20260919/MANIFEST.md`；须**全新 `--drc-work-dir`**）⇒ **19 OK / 0 FAIL**（未连接 0 / error 0 / `zone_filled` 10/10）· **两跑逐字节同**
③ `AppDir/bin/python3.11 k2/tools/k2_p6_acceptance_gate_v1.py --expect-patched` ⇒ **PASS**（A 4/4 · C K1=14/K2=14 · 回退 0 · D hidden=2 = 具名 C1/C2）
> **C1/C2 保持 RED**（禁改绿）；`skipped` 不充绿；**两跑不逐字节同者不得入库**。

## 3. ENG 立即可动 vs 需裁定

- **需裁定后才动**：上表 1–7（全为**监理自裁项**；ENG 已把它们的"件/命令/期望值/回滚"备到**一条命令级**）。
- **无裁定也可动**：本表 §0 三件已完成；后续同类"把预期变实测"的活（如 v5/v6 fixture 生成路径普查）ENG 可续做。

—— ENG（ARCHER）· 2026-09-20 · k2 `8f7fae8`（本节仅 docs+artifacts）· 共享层 `fc59771` · 判据 rev=3 · **P6 交付阶段仍关闭**
