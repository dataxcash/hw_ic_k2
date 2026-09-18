# K2 · P4 · **`D-7` 九案回归复核草案**（D-7-only 树 vs 合并全修树；逐案一致）· v1 · 2026-09-18

> 缘起：handoff inc69 §6-3-(y)「`D-7` 九案矩阵**回归复核**（inc50 九案在 inc58 全修树上重跑，纯 `/tmp`）」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读 + `/tmp` 两树复跑**，仓库零载体改动（仅新增本证据件）。
> 锚：D-7-only 树 `/tmp/opencode/inc50/eda_core/pipeline/checks.py` **`37ae7c15e977f4ad`**（＝`_shared` 副本 ＋ `K2_NC_SOURCES` 选源补丁）· 合并全修树 `/tmp/opencode/inc58/shared_full/eda_core/pipeline/checks.py` **`0cbd9a478c694a12`**（＝D-7 开关式 ＋ `D-2` 缺件 guard）· 真源 `dd794c54f7ce7417` · `errata-1` `17d540f058631a5e` · 既有记录 `K2-P4-D7-CONTROL-MATRIX-AND-C1-TRUTH-BINDING-v1.md` §5。
> 装置（`/tmp`，易失）：`/tmp/opencode/inc63/d7_matrix.py` **`9965773fe2887cb8`** → 输出 `d7_matrix.txt` **`9482f746891529b5`**；fixture `inc50/{sb_e1,sb_e2,sb_bogus}`。
> **归属**：`D-7` 语义（①②/③）＝**监理**；本件只做**合并后回归**证据，**不新增检查齿**（owner ②）。

## 0. 结论（四条）

1. **合并不回归**：九案在 **D-7-only 树**与**合并全修树**上**逐案结果完全一致**（下表），且与 inc50 §5 的既有期望一致（表中 `0` 与 `PASS` 同义）⇒ 把 `D-2`（缺件 guard）与 `D-3/D-4/D-4b`（hook/engine）并入后，**`D-7` 的三源开关语义未被破坏**。
2. **三源开关行为（实测）**：`sb_e1` 下 `top,placements,pintype`=**1** · `top`=**106** · `placements`=**2** · `pintype`=**1** · `none`=**106**；`sb_e2` 下 `top,placements,pintype`=**PASS(0)** · `top`=**PASS(0)** · `none`=**105**；`sb_bogus`=**2**。
3. **对乙路径的含义（复述既有结论，非新增判定）**：采 `乙`（`errata-1`）时**必须**开 ①②（`D-7a`）才能把 105 条非声明悬空消掉（`sb_e1 none` 106 → `top,placements` 2）；**③（`pintype`）仅影响个别计数**（`sb_e1` 2 → 1），且 ③ 属 **C-1 违规口径**（把被验对象当判据真源）⇒ 既有结论「③ 救不了 ⑤」不变。
4. **证据可复现**：`d7_matrix.py` 两树对跑、退出码按「逐案一致 ∧ 与期望一致（0≡PASS）」判定（rc=0）；两树 engine 亦各自随树（D-7-only 用 inc50 engine，合并树用 `a015f8cfcc24c581`）。

## 1. 九案矩阵（两树逐案）

| # | fixture | `K2_NC_SOURCES` | **D-7 only（inc50）** | **合并全修（inc58）** | inc50 §5 期望 |
|---|---|---|---|---|---|
| ① | `sb_e1` | `top,placements,pintype` | 1 | 1 | 1 |
| ② | `sb_e1` | `top` | 106 | 106 | 106 |
| ③ | `sb_e1` | `placements` | 2 | 2 | 2 |
| ④ | `sb_e1` | `pintype` | 1 | 1 | 1 |
| ⑤ | `sb_e1` | `none` | 106 | 106 | 106 |
| ⑥ | `sb_e2` | `top,placements,pintype` | **PASS(0)** | **PASS(0)** | 0 |
| ⑦ | `sb_e2` | `top` | **PASS(0)** | **PASS(0)** | 0 |
| ⑧ | `sb_e2` | `none` | 105 | 105 | 105 |
| ⑨ | `sb_bogus` | `top,placements,pintype` | 2 | 2 | 2 |

**判定**：两树逐案一致 = **True** · 与期望一致（`0≡PASS`）= **True**。

## 2. 复跑（仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw
sha256sum /tmp/opencode/inc50/eda_core/pipeline/checks.py /tmp/opencode/inc58/shared_full/eda_core/pipeline/checks.py | cut -c1-16
python3 /tmp/opencode/inc63/d7_matrix.py ; echo "rc=$?"      # 期望 rc=0（两树逐案一致 ∧ 与期望一致）
```

## 3. 边界

本件**只读 + `/tmp` 两树/fixture**：未改 `_shared/**`、判据、生成器、模板、板、pro、库、`fp-lib-table`、`pm_gate/**`、SPEC、真源、`criteria/**`；
**未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`**；未落件；未出 Gerber；未派 WORKER；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · D-7 only `37ae7c15e977f4ad` · 合并全修 `0cbd9a478c694a12`
