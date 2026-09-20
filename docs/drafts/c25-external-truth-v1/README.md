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

## 5. ⛔ `parts_electrical_truth.yaml` 的**真源可得性普查**（阻塞点量化）
承 §3 PARTIAL 门：已盘点仓库内既有『器件引脚真源』是否满足 C-25 的**出处三件套**。
证据件：`k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/C25_PARTS_TRUTH_SOURCE_CENSUS_20260921_v1.json`（`c2003dd1c11a6ec8`）。

| 来源 | 件数 | `pins` | **出处三件套** | 可否直接用 |
|---|---|---|---|---|
| `_shared/eda_core/sch_gate/datasheets/*.yaml`（两树同） | **33** | 32 | **0**（仅自由文本 `source`，如「TI SNLS658 Rev B」） | ❌ 不合 C-25 要求；且 `pins` 为**物理脚名**非**电气级** |
| `k1/…/L1/inputs/datasheets/*.yaml` | 6 | — | **6**（`doc_id`/`doc_url`/`doc_sha256`） | ✅ 合要求，但仅 6 器件且属 K1 |

⇒ **`parts_electrical_truth.yaml` 的补全不是"填表"，而是"取文献+哈希+转录电气级"**。三条补全路径（须监理择一）：

- **(a) 就地升级 33 件出处**：补三件套 + 电气级。**动 `_shared` ⇒ 须两树同步 + 零单板特判**。工作量高、版本错配风险中。
- **(b) K2 侧独立转录 → `criteria/parts_electrical_truth.yaml`**：**不动 `_shared`**。工作量高、风险低。← **ENG 建议**
- **(c) 缩面声明**：仅覆盖 `lib_electrical_level` 审计实际涉及器件（须先由审计件定出器件全集）。工作量中。

**选路前该维维持不可达（`check-dimensions` 保持 17/19，不得部分覆盖充绿）。**

## 6. 路径 (b) 的**可执行范围**（器件全集已定）
证据件：`k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/C25_PARTS_TRUTH_SCOPE_OPTIONB_20260921_v1.json`（`66a317fca84e7c7d`）
- 基准 = `lib_electrical_level` 实际消费的 W-8 审计件（`…/E3-standard-call-l7-20260919/w8_audit_board_l7_c5a7df90.json` · tool `75404d706413d546`）：**58 footprint / 24 唯一 lib_id**；RAW `n_electrical_diff=2 · n_pad_name_set_only=1`（dim 经 `_reclassify_w8` 具名口径后判 PASS）。
- **精确映射 9/24** 到仓库既有引脚真源（→ 其待取文献 `source:` 引证）：`MCIO_4i_SFF1016` · `STM32G0B1CBT6` · `OPTO_LTV356T` · `J_OOB_HEADER` · `DCDC_12V_5V` · `FRU_EEPROM` · `BAT54C` · `SlimSAS_x8_SFF8654`（+ `MCIO` 两个 variant）。
- **未精确映射 15/24**：R/C/L/LED/排针/安装孔（无源/机械/通用件）+ **`DS320PR1601`**（其真源文件为 `DS160PR810.yaml`，疑**命名不一致** ⇒ 须人工确认）。
- ⚠ 方法学登记：曾用模糊/子串回退 ⇒ **电阻件误配 MCU**（假阳）⇒ 已弃用，改用**精确匹配**并显式列出未映射项。
- **须监理确认**：(i) 采用路径 (b)？(ii) 外部真源的**器件纳入面**是否含无源件？(iii) `DS320PR1601`↔`DS160PR810` 命名对应。

## 7. ⭐ 语义厘清 ⇒ `parts_electrical_truth.yaml` **v2（tier1 完整）**
读判据代码后确认（`criteria/adjudicate.py` `_reclassify_w8`，rev=3 起逐字节同 `1937a40a`）：
`lib_electrical_level` 消费 `w8_audit_json`，实际比对的是 **板封装 ↔ 库封装**（pad 名集/几何/旋转；`(B)` 口径把『中心对称 rot∈{0,180}』与『无号 F.Paste』豁免为非电气）。
> ⇒ 该维的**天然外部真源 = 库封装语料**（对本板是独立件），**不是**「器件手册电气级」字面义。#K2-47 §三 的措辞需监理确认口径。

证据件：`…/P6_OPEN_READINESS/C25_LIB_ELECTRICAL_TRUTH_CANDIDATE_20260921_v1.json`（`be296ee29e43f60f`）
- **tier1（库语料）覆盖 24/24**：受审 24 个 lib_id **全部**命中 `k2/hw/lib/ForgeOS.pretty/*.kicad_mod`（逐件 sha16 已录）。
- tier2（手册上溯）：`sch_gate/datasheets/*.yaml` 33 件**缺三件套** ⇒ 仅登记 `source:` 引证（增强项，非阻塞）。

**v2 草案再验证（真 CLI · /tmp 沙箱）**
| 场景 | 结果 |
|---|---|
| 基线 rev=5 | 17/19 · 违规 2 ⇒ FAIL |
| **v2 草案（jlc + parts tier1 + manifest 补丁）** | **19/19 · 违规 0 ⇒ PASS** |
| 负控① 真源=受审板自身 | 被拦（fail-closed） |
| 负控② 真源缺件 | 被拦（fail-closed） |

**⇒ 若监理确认口径为 tier1（库语料），本包可即时落件**（gate 属主 3 步：install×2 + patch），装后 rev=6 + 重跑 canonical 19 复核 == `190b73be0f728a56`。
