# K2 · **N-05「生成器不可复跑」复现链健康度普查**（v1 · 2026-09-20 · 只读）

> 性质：把 N-05 从「登记」变成**可执行清单**（机读 `P6_execution/REPRO_CHAIN_HEALTH_v1.json`，工具 `k2/tools/k2_p6_repro_chain_health_v1.py`，工具内**自校验 determinism=True**）。
> 缘起：批 2 triage 发现遗留 `channel_alloc*`（`1a883b8` 自 `strix-halo-ioconvert` **字节复制、从未重生成**）⇒ 追问「这种件有多少」。

## 1. 方法（口径可与监理复核）
- **出处**：`git log --reverse --diff-filter=A` 首增提交；**触及数** = 触及该路径的提交数（**1 ⇒ 首次之后从未变更**）。
- **引用**：父目录名（>3 字符）命中，或文件主干（**≥8 字符**，排除 `report/summary/data` 等泛词误命中）出现在**现役代码**（`k2/tools/*.py`（除本批 P6 工具）、`_shared/eda_core`、`_shared/pm_gate` 非测试模块、项目配置）。
- 分类：`STALE_IMPORT_ORPHAN` / `STALE_IMPORT_REFERENCED` / `IMPORT_ORIGIN_EVOLVED` / `RECENT_ORPHAN` / `LIVE`。
- **诚实边界**：`referenced` 是**词面启发式**（目录名/长主干命中）⇒ 656 为**上界**；「导入后未变更」**不等于**错误（复制来的输入可能本来就有效）⇒ 本件是**分诊清单**，不是判决。

## 2. 结果（1993 件已跟踪产物）
| 类 | 件数 | 体积 | 含义 |
|---|---|---|---|
| **STALE_IMPORT_ORPHAN** | **121** | 1.0 MB | `1a883b8` 字节导入 ∧ 从未变更 ∧ 现役代码不引用 ⇒ **RETIRED 候选** |
| **STALE_IMPORT_REFERENCED** | **656** | 3.7 MB | 同上但**被现役代码引用** ⇒ **现役链仍依赖遗留字节副本**（N-05 的机制本体） |
| IMPORT_ORIGIN_EVOLVED | 4 | 0.2 MB | 导入后被正常演进（非卫生项） |
| RECENT_ORPHAN | 113 | 18.9 MB | 后续新增但现役不引用（含 `SPEC` 历史 rev、大 JSON/PDF） |
| LIVE | 1099 | 155 MB | 现役引用 |
⇒ **777/1993 = 39% 的产物为「导入后从未变更」**；其中 **656 件仍在现役链上**。

## 3. 关键读法
1. **N-05 不是一个孤例，是一个面**：`channel_alloc*` 只是 656 件的一例；批量「字节复制 + 从未重生成」是 K2 建目录时的普遍形态（`1a883b8`）。
2. **风险不在「旧」，在「不可复现」**：引用它们的现役代码无法由现行 SPEC/配置重生成同样结果 ⇒ 任何 SPEC/命名演进都会**静默**制造分歧（本轮走廊命名分歧即此机制）。
3. **不建议一刀切**：656 件中多数可能是**仍然有效**的复制输入（图纸/数据/PDF）。处置应按**是否在现役判定路径上**排序，而非按体积。

## 4. 建议处置（**须授权**；ENG 不擅自改产物）
| 优先 | 动作 | 范围 |
|---|---|---|
| P1 | 对 **`STALE_IMPORT_REFERENCED` 中被「批 2 相关载体」直接消费**的子集（如 `model_solves/channel_alloc*`）**重生成或重钉** | 与命名裁定同批 |
| P2 | 对 **121 件 `STALE_IMPORT_ORPHAN`** 出 **RETIRED 清单**（仅登记，不删不迁） | 卫生；防再次被当"真源"引用 |
| P3 | 给 `STALE_IMPORT_*` 加**溯源字段规范**（「导入来源 + 是否可重生成」）写入后续产物 | 流程（监理侧模板） |

## 5. 零改动声明
仅读 git/文件；未触 `_shared`/`criteria/`/冻结四源/交付锚/生成器/SPEC/原理图；未派 WORKER；临时仅 `/tmp/opencode`。
