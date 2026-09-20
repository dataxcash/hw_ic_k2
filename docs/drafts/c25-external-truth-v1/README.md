# C-25 外部真源草案包（**gate 属主安装目标**）· 2026-09-21

> 依据：**#K2-47 §三**「残面（C-25）：`density_and_clearance` / `lib_electrical_level` **无独立外部真源**
> ⇒ 须落 `criteria/jlc_hdi_capability.yaml` + `criteria/parts_electrical_truth.yaml`（含出处三件套
> `doc_id`/`doc_url`/`doc_sha256`）」。
> ENG 落件人：ARCHER。**ENG 对 `criteria/` 只读** ⇒ 本包为**草案**，安装归 **gate 属主（`ic_hw_gate`）**。

## 0. 本包内容
| 文件 | 说明 |
|---|---|
| `criteria__jlc_hdi_capability.yaml` | → 安装为 `criteria/jlc_hdi_capability.yaml`；`density_and_clearance` 的外部能力真源（JLC 工艺能力，出处 = 抓取页 sha256）。 |
| `criteria__parts_electrical_truth.yaml` | → 安装为 `criteria/parts_electrical_truth.yaml`；`lib_electrical_level` 的器件电气级真源。**当前状态 = PARTIAL（见 §3）**。 |
| `manifest.k2.dim_source_of_truth.patch` | 对 `criteria/manifest.k2.yaml` 的**纯增量**补丁：`dim_source_of_truth` 加 2 条。 |

## 1. 安装步骤（gate 属主）
```bash
cd /home/fila/jqdDev_2025/ic_hw
sudo install -m 0444 k2/docs/drafts/c25-external-truth-v1/criteria__jlc_hdi_capability.yaml   criteria/jlc_hdi_capability.yaml
sudo install -m 0444 k2/docs/drafts/c25-external-truth-v1/criteria__parts_electrical_truth.yaml criteria/parts_electrical_truth.yaml
sudo patch -p1 -d . < k2/docs/drafts/c25-external-truth-v1/manifest.k2.dim_source_of_truth.patch
# 正控：
PYTHONPATH=_shared python3 -m eda_core.truth_binding check-dimensions \
  --manifest criteria/manifest.k2.yaml --base-dir . \
  --artifact k2/hw/k2_v4_8L.l7.kicad_pcb
# 期望：19/19 维已声明 · 违规 0 ⇒ PASS
```
安装后须同步 `criteria/CHANGELOG` + `adjudication-ledger.jsonl`（rev=6），并**重跑 canonical 19** 复核
verdict 仍 == `190b73be0f728a56`（判据语义不应变）。

## 2. 联合验证（ENG 侧 · 本包已实测）
沙箱（`/tmp`，仓库零写）施加本包后：

| 场景 | 结果 |
|---|---|
| 基线（现行 rev=5） | 17/19 已声明 · 违规 2（`density_and_clearance` / `lib_electrical_level` 未声明） ⇒ FAIL |
| **施加本包** | **19/19 已声明 · 违规 0 ⇒ PASS** |
| 负控①（真源改指受审板自身） | 被拦（自证循环，fail-closed） |
| 负控②（真源文件不存在） | 被拦（fail-closed） |

## 3. ⚠ `parts_electrical_truth.yaml` 当前为 **PARTIAL** —— 安装前须补全
- 该维 `expect` = `n_electrical_diff == 0 ∧ n_pad_name_set_only == 0`（**逐器件、逐引脚电气级**）。
- 本草案已给出 **schema** + **出处登记册**（仓库既有 6 件已转录手册，均含 `doc_id`/`doc_url`/`doc_sha256`）。
- **未覆盖**器件（连接器 / MUX / Redriver / EEPROM / TVS / MCU 等）的引脚电气级**尚未转录**。
- ⇒ **未补全前不得安装**（安装后该维仍不可达，且**不得以部分覆盖充绿**，C-12 / skipped 不充绿）。
- 补全路径：按 `provenance_registry` 同构扩充（每器件：手册三件套 + 逐引脚 `name`/`electrical` + `where/page/excerpt`）。

## 4. 红线
ENG 只读 `criteria/`（本包未写 `criteria/`）；未新增判据维、未改任何阈值（本包只声明**外部真源**）；
未动冻结四源 / 交付锚。**无 owner 闸口**（C-25 为 gate 属主落件项，见 #K2-47 §五）。
