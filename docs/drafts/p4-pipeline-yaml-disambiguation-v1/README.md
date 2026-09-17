# D-1 消歧：`k2/pipeline.yaml` 两个合规变体（ENG 草案，**未安装**）

归属：安装属 **gate 属主侧**；本目录只放候选件。判定归监理。
证据：`docs/K2-P4-PIPELINE-INSTALL-PATH-EVIDENCE-v1.md`（含实测矩阵、真源三方差异、门禁有效性复证）。

| 文件 | 对应 | 实测 |
|---|---|---|
| `pipeline.phases-only.draft.yaml` | **变体②（推荐）**：Draft A 改标签为 criteria-descriptor，不安装；本件装为 `k2/pipeline.yaml` | `load_config` PASS · meta-gate PASS · preflight PASS · verify **3/3 PASS** |
| `pipeline.merged.draft.yaml` | **变体①**：Draft A 的描述符键 + `phases` 合并单件 | 同上；但 `criteria/fail_closed/artifacts` 三键**无消费者** |

被消歧的原件：`docs/drafts/K2-P4-criteria-draft-v2/pipeline.yaml.draft`（`cef091317438eacd`）——
**不是 pipeline.yaml**（无 `phases` ⇒ 框架 `PipelineError: 缺少 phases 列表`），其 README 描述的是另一件。

## 安装前置（甲/乙共同）
1. `k2/hw/data/k2_sch.errata-2.yaml`（草案 `bdacbf944ca0c796`）落库 —— **真源侧新增，须监理放行（F-10）**；
2. `k2/fab/k2_v4_bom.csv`（草案 `ce2bb814f31be54b`）落库 —— `k2/fab/` 目录现不存在；
3. **先 1+2 后** 装 `k2/pipeline.yaml`（否则 D-2 抛未捕获 `FileNotFoundError` 并自锁 k2 提交）。

## 路径乙（已实测排除）
把 `netlist_connect.nets_yaml` 指向现存 `k2/hw/data/k2_sch.errata-1.yaml`（`17d540f058631a5e`，即 `pm_gate/project.yaml` 现行值）
⇒ `engine verify` **FAIL 106 处**（1 网缺失 + 105 非声明悬空）⇒ 不可行。

> 两变体均**未新增检查齿**：仅复用 `_shared/eda_core/pipeline/required.py::REQUIRED_SCH_CHECKS` 三类。
