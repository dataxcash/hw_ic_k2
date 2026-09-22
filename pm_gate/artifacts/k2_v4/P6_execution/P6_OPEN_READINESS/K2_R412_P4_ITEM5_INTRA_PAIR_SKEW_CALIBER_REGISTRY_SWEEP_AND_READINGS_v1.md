# K2 · R412 —— P4 项5『对内等长』：**在册阈值册证 + 辖域缺口 + l9 同口径读数**

- **ts** 2026-09-22T23:1x+0800 · **from** ENG·ARCHER（续接 · 应 #K2-142 §四 只读残余）· **to** 监理 · **owner 闸口 0**
- **authority**：#K2-142 §四 · R270 §一 项5（等长：l9 同口径重测 + 阈值具名）· R408（自纠）· **owner #14⑦（口径澄清 = 监理自裁）**
- **边界**：纯只读查册 + 读数。**未自定/未调阈值、未改判据、未改真源/受审板**、未派 WORKER、未烙板。

## 1. 册证：唯一在册『对内等长阈值』= **0.15mm**，其**选择器** = `prefix PCIE` + **`suffix (_P,_N)`**
| 源（冻结/受审） | 字段 |
|---|---|
| `_shared/eda_core/drc_rules.json`（**冻结四源之一**） | `diff_pair.intra_pair_skew_mm = 0.15` · `enabled=true` · `net_prefix="PCIE"` · `pair_suffix=["_P","_N"]` |
| `L3/SPEC_k2_v4.spec-rev-55.json` | `net_classes.PCIe85.intra_pair_skew_mm = 0.15` |
| `L3/SPEC_…rev-55` | `REFCLK-ECS-001『补偿至 intra_pair_skew_mm <= 0.15』`（**主体 = PCIE_REFCLK0/1** —— 与 R408 自纠一致） |
| `criteria/manifest.k2.yaml`（rev=6） | **19 维内无『对内等长』维** ⇒ 本项属**计划项**，非判定器维 |

## 2. 实名对照：**selector 与 ②-UP 具名网不一致**（册内自指不一致）
| 族 | 具名 | 满足 suffix `_P/_N`？ | 在辖域？ |
|---|---|---|---|
| **A** | `PCIE_UP<N>_{P,N}`（16 条） | **是** | **在** |
| **B（②-UP 具名）** | `PCIE_UP_OUT<N>_{P,N}_J2`（16 条） | **否**（尾 `_J2`） | **不在**（字面） |

- 但 `drc_rules.json::diff_pair.gap_check` 之举例为 `PCIE_UP1 P/N`（族 A 之名）⇒ 册内选择器与举例**自指不一致**。
- 而 **R270 §一 项5 之在册基线 `6.002mm@pair4` 只在『族 B × In5-only』口径下可复算**（见 §3）⇒ 计划侧实际把**族 B** 当项5 主体。

## 3. l9 同口径读数（只报读数 · 不复判 PASS/FAIL）
| 族 | 口径 | l9 | l8 对照 |
|---|---|---|---|
| **B**（②-UP 具名） | **In5-only** | **6.0017mm** @pair4 | 6.0017mm（逐位同） |
| **B** | 全层（端到端） | 0.6135mm @pair4 | 0.6135mm |
| **A** | In5-only | 1.72mm @pair6 | 同 |
| **A** | 全层（端到端） | **0.0216mm** @pair7 | 同 |

**关键复算**：本件『族 B × In5-only』= **6.0017mm @pair4** ⇒ **与 R270/R259 在册基线 `6.002mm@pair4` 逐位一致** ⇒ 证实此项在册口径 = **族 B × In5-only**；且 **l9 = l8**（落搬迁未动此二族）。

## 4. 口径问题单（**监理自裁** · owner #14⑦）
- **Q1 辖域**：`diff_pair` selector 是 **suffix 字面** 还是 **substring**？若不改 selector ⇒ ②-UP 16 条字面**不在辖域**。
- **Q2 口径**：『对内等长』= **端到端总长差** 还是 **In5-only 差**？（族 A 两者相差 80×：0.0216 vs 1.72）
- **Q3 族**：项5 之『②-UP 16 条』= 仅族 B，抑或两族全计？
- **ENG 声明**：不自裁、不改判据、不代填阈值、不缩口径（C-12）。

## 5. 件
`K2_R412_…_v1.json`（全量读数 + 册证 + 问题单）· `.sha16.txt`。baseline 复算详表见件内 `readings_l9_same_caliber.detail`。

—— ENG（ARCHER）· 2026-09-22 · 只读 · owner 闸口 0
