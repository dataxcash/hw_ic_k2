# K2 · P6 · **C-25 外部真源草案**（density_and_clearance / lib_electrical_level）

- 工件：`k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/C25_EXTERNAL_TRUTH_DRAFT_20260921_v1.json`（sha16 `eebff754dab6ce37`）
- 草案包：`k2/docs/drafts/c25-external-truth-v1/`
- 依据：**#K2-47 §三**（监理 2026-09-20 · criteria **rev=5** `2da49b56a1b329ad`）
- 性质：**只读起草**。ENG 对 `criteria/` 只读 ⇒ 安装归 **gate 属主**；**未新增判据维、未改阈值**、未动冻结源/交付锚。
- 日期：2026-09-21 · ENG(ARCHER)

## 0. 一句话
`#K2-47` 登记 C-25：两维无独立外部真源。本件交付**可直接安装的草案包**（1 个外部能力真源 + 1 个器件电气真源 schema/登记册 + manifest 增量补丁），并在 `/tmp` 沙箱用**真 CLI** 实测：**施加前 17/19 FAIL → 施加后 19/19 PASS**，且自证/缺件两类负控**均被拦**。唯一未尽：`parts_electrical_truth` 为 **PARTIAL**（须补全器件覆盖面，否则不得安装）。

## 1. 为何是这两维「无外部真源」
| 维 | 判据 expect | 现状真源 | 缺口 |
|---|---|---|---|
| `density_and_clearance` | `fp_peak_per_cell<=8 ∧ min_copper_clearance_mm>=0.100` | 阈值在 manifest；**能力下限无外部件** | 需 **JLC 工艺能力**外部件（最小线宽/间距/孔/边距…） |
| `lib_electrical_level` | `n_electrical_diff==0 ∧ n_pad_name_set_only==0`（**以板为准**） | **受审板自身** | 需 **器件手册电气级**外部件（否则即自证） |

## 2. 草案内容
| 文件 | 安装目标 | 要点 |
|---|---|---|
| `criteria__jlc_hdi_capability.yaml` | `criteria/jlc_hdi_capability.yaml` | 出处三件套：`doc_id`=JLCPCB PCB Capabilities · `doc_url`=jlcpcb.com/capabilities/pcb-capabilities · `doc_sha256`=`7d1d5a91…`（抓取页 135508 B）；附关键能力值 + **阈值绑定说明** |
| `criteria__parts_electrical_truth.yaml` | `criteria/parts_electrical_truth.yaml` | schema（逐器件逐引脚 `name/electrical` + `where/page/excerpt`）+ **出处登记册**（仓库既有 6 件已转录手册：Bourns SRP6060FA / JST VH / TPD2E001 / TPS22965 / TPS22990 / TPS54628，均含三件套）。**状态 = PARTIAL** |
| `manifest.k2.dim_source_of_truth.patch` | `criteria/manifest.k2.yaml` | **纯增量**：`dim_source_of_truth` 加 2 条（patch `-p1` dry-run **rc=0**；实测应用后 → 19 声明） |
| `README.md` | — | 安装 4 步 + 验证 + PARTIAL 门 + 红线 |

## 3. 联合验证（ENG 侧 · **真 CLI** · `/tmp` 沙箱）
命令：`PYTHONPATH=_shared python3 -m eda_core.truth_binding check-dimensions --manifest <M> --base-dir <SB> --artifact k2/hw/k2_v4_8L.l7.kicad_pcb`

| 场景 | 结果 |
|---|---|
| 基线（现行 rev=5） | **17/19** 已声明 · 违规 2 ⇒ **FAIL**（逐字复现 #K2-47 §三「正控 17/19」） |
| **施加本草案** | **19/19** 已声明 · 违规 **0** ⇒ **PASS** |
| 负控① 真源改指受审板自身 | **被拦**（`SelfSourceError`，fail-closed） |
| 负控② 真源文件不存在 | **被拦**（`MissingProvenanceError`，fail-closed） |

## 4. 必须由 gate 属主补全/把关的三点
1. **`parts_electrical_truth.yaml` 须补全器件覆盖面**（覆盖 == `lib_electrical_level` 审计所涉器件全集）——**未补全不得安装**；**不得以部分覆盖充绿**（C-12 · skipped 不充绿）。
2. 安装后须同步 `criteria/CHANGELOG` + `adjudication-ledger.jsonl`（rev=6），并**重跑 canonical 19** 复核 verdict 仍 == `190b73be0f728a56`。
3. JLC 能力页明示 `blind_buried.supported=false`（HDI/激光孔属 advanced options、须 **DFM review**）——本工程工艺冻结=A，此为**须随单确认的工艺前置**，已在真源内显式登记，**不是本维阈值**。

## 5. 边界
ENG **未写 `criteria/`**（本包为其草案）；未新增判据维、未改阈值；未动冻结四源 / 交付锚 / `_shared`。**无 owner 闸口**（C-25 属 gate 属主落件项）。
