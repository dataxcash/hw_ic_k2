# K2 · **走廊命名分歧 · 影响面核对与「是否开 rev」判定输入**（v1 · 2026-09-20）

> 性质：**只读证据包**（判定归监理）。回答监理三问之③「该分歧对 **P3/L3 冻结件与 P5 交付锚**的影响面 ⇒ 是否需要开 rev」。
> 机读真源：`pm_gate/artifacts/k2_v4/P6_execution/NAMING_IMPACT_CHECK_v1.json` **`02de9e11…`**（两次连跑逐字节同）
> 工具：`k2/tools/k2_p6_naming_impact_check_v1.py` · 根因件：`HIDDEN_FAILURES_TRIAGE_v1.json` **`ac01c7d4…`**（前版 `6db5ba75…` 因载体**误名**「L3 求解真源」已更正，见 §4）

## 1. 四问核对（机读 flags 全 True）
| 问 | 证据 | 结论 |
|---|---|---|
| ① P5 交付锚（`L6/` 全树，**61 件**）是否含走廊 id？ | **0 命中**（旧/新皆无） | **交付件（Gerber/叠层/阻抗/DFM/清单）与命名无关** |
| ② P3/P4 **冻结四源**是否含走廊 id？ | `l4` 板 / 设计源板 / `k2_sch.yaml` 均 **0 命中** | **冻结件不受影响** |
| ③ 现役项目配置用哪套 id？ | `L2/route_model_config.json`：旧 **0** / 新 **4** | **现役链已对齐现行 SPEC 命名** |
| ④ 现役工具链是否读遗留 `model_solves/channel_alloc*`？ | 仅**测试**与本 P6 triage 工具引用；`k2/tools`、`_shared/eda_core`、`_shared/pm_gate` 的现役模块 **无引用** | **现役链与该遗留件零耦合** |

## 2. 遗留 alloc 族清点
| 版本 | 旧 id | 新 id | 首次入库 | 说明 |
|---|---|---|---|---|
| `channel_alloc/` | 128 | 0 | `1a883b8` | 建独立 K2 工程时**自 `strix-halo-ioconvert` 字节复制**（提交信息自述「字节一致」） |
| `channel_alloc_v2/`（**测试钉住**） | 108 | 0 | `1a883b8` | 同上；**从未重生成**（该路径在 git 中仅此一笔） |
| `channel_alloc_v3/` · `channel_alloc_v4/` | 108 | 0 | `1a883b8` | 同上 |

## 3. 判定输入（供监理）
- **不需因命名分歧开 rev**：物理交付件与冻结四源**零命中**走廊 id；现役配置/工具链已对齐新 id 且不读遗留件。命名分歧的落点**仅在测试输入与判据期望集**。
- 13 项隐藏失败的性质随之收敛为：**测试输入漂移**（钉在 08-28 字节导入、从未重生成的遗留 alloc v2）＋ **判据期望漂移**（`check_l3.SPEC_EXPECTS` 旧名）——**非引擎缺陷、非交付缺陷**。
- 建议处置（**须授权**）：① 测试重钉现行真源（SPEC 派生通道 / `route_model_config.json`）；② 遗留 alloc 族标注 `RETIRED`（**N-05 卫生**，防再次被当"真源"引用）；③ 判据期望集随命名裁定同步。

## 4. 记录更正（诚实记账）
前版 triage 件（`6db5ba75…`）把 `channel_alloc_v2` 称作「**L3 求解真源**」——**不准确**：该件为遗留导入、现役工具链不读。已更名为 `legacy_alloc_v2_pinned_by_tests` 并重出机读件 **`ac01c7d4…`**（本件取代前版）。

## 5. 零改动声明
未触 `_shared`/`criteria/`/冻结四源/交付锚/生成器/SPEC/原理图；未派 WORKER；临时仅 `/tmp/opencode`。
