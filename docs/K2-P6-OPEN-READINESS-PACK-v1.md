# K2 · **P6 开闸就绪件 v1**（计划/测量件；**P6 交付阶段仍关闭**）· 2026-09-20

> 依据：**《K2 整体整改计划》P6 完工判据**（`k2/docs/K2-RECTIFICATION-PLAN-v1.md` §P6）+ **#K2-41 §三-⑥**（G-c2 内容已裁、由 gate 属主于 P6 开闸时原子落件）。
> 性质：**ENG 只提供测量**（计划 §3.2：J 类判据归监理）；本件**不改**任何判据 / 模板 / SPEC / 原理图 / 生成器，不越阶段。
> 机读件：`k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS_v1.json`；原始证据同目录 `P6_OPEN_READINESS/`。

## 0. 一句话

P6-1 的**唯一缺件** = 监理持有的 `criteria/manifest.k1.yaml`（G-c2，fail-closed 已验证）；此外发现**两处**开闸前必须裁定的口径：
① `results_template.json` 里 P6-1 命令的 `--nets k1/boards/k1_nets.yaml` **会崩溃**（`KeyError: 'symbols'`），同目录 `k1/boards/k1_sch.yaml` 可跑；
② P6-2 的整改对象 = **两模板各 9 条 ignore**（逐条相同，计划 §7.1 根因）。
四项「同源缺陷」已**逐项实测取证**（下面 §1.2）。

## 1. P6-1 就绪

### 1.1 前置件态（机核）

| 件 | 态 |
|---|---|
| `criteria/manifest.k1.yaml`（**应然集**，监理） | **缺** ⇒ `adjudicate.py:536` 缺件即 fail-closed（实测 rc=1，`[FAIL] manifest 缺失`） |
| `criteria/manifest.k2.yaml` / `adjudicate.py` / `CHANGELOG` | 在岗 **rev=3**（`eb244d81` / `1937a40a` / `e2b49fdd`）；**ENG 只读，未动** |
| `k1/k1_v1.kicad_pcb` / `k1_v1.kicad_pro` / `k1/sch`（5 sheets） | 在 |
| `k1/boards/k1_nets.yaml` | **在但 schema 不符**（顶层 `['nets','nc','source','k1_device_count']`）⇒ 判定器 `KeyError: 'symbols'`（`adjudicate.py:149`）**崩溃** |
| `k1/boards/k1_sch.yaml` | 在且**同构**（`['symbols','nets','sheets','strap_intents','links']`，symbols 40 / sheets 4）⇒ 判定器**可跑**（本件已实测） |
| 测量输入（DRC / W-8 / 出框 / 参考连续性 / 密度间距） | **P6-1 命令原文未提供** ⇒ 对应 6 维 fail-closed（K1 侧尚无这些测量件） |

### 1.2 应然集四项：**逐项实测取证**

| 应然项 | 维 | 实测 | 载体/根因 |
|---|---|---|---|
| `ignore_without_ruling(9)` | `rule_severity_manifest` | **9/62**：`copper_sliver`·`footprint_filters_mismatch`·`footprint_type_mismatch`·`missing_courtyard`·`silk_over_copper`·`silk_overlap`·`track_not_centered_on_via`·`tuning_profile_track_geometries`·`via_dangling` | `k1/k1_v1.kicad_pro` 的 `board.design_settings.rule_severities`；**根因 = 共享模板默认值**（两模板逐条相同，计划 §7.1） |
| `no_pipeline(1)` | `pipeline_present` | scope=k1 内 **1 个**：`['k1/sch']`（5 sheets 无 `pipeline.yaml`）；范围外 6 个（他项目阶段门判） | `k1/sch` |
| `no_fp_lib_table(1)` | `fp_lib_table_present` | `k1/` **缺** `fp-lib-table`（K2 侧 `k2/hw/fp-lib-table` 在） | 项目根 |
| `sheets_empty(1)` | 结构项（计划 §7.1） | `k1/k1_v1.kicad_pro.sheets == []` | 板未挂原理图；K2 交付板 `l7.kicad_pro` 已清（`sheets=None`、`ignore=0`） |

### 1.3 PROBE 读数（**未签认**，仅供监理写应然集时对照）

- 命令：`--nets k1/boards/k1_sch.yaml` + PROBE manifest（复刻 `manifest.k2.yaml` 语义，`project/scope→k1`，`not_countersigned=true`；**未落 `criteria/`**）
- 读数：**n_pass = 3 / n_fail = 16**（`provisional=true`）
  - OK：`device_has_pads`·`non45_segments`·`verdict_schema`
  - FAIL：`zone_filled`(0/0)·`drill_count`(NPTH=2 < 4)·`rule_severity_manifest`·`net_declared_realized`(0 焊盘 3 · <2 焊盘 12)·`pin_map_complete`(16)·`refdes_sets_equal`(图 37 / 板 42；板有图无 `Q1,Q2,R38,R39,U13`)·`pipeline_present`·`fp_lib_table_present`·`keepout_active`(0)·DRC 3 维 + 测量 4 维（未提供输入 ⇒ fail-closed）
- ⇒ **须监理裁定**：K1 处于中间态（未布线、未挂原理图、无测量件）⇒ 哪些维 `enabled:false`、哪些登记豁免、哪些须补测量件；`--nets` 用 `k1_sch.yaml` 抑或判据侧容错 `k1_nets.yaml`。

## 1.4 B2-4 收口件：撤 K1 `G1.5` WAIVER（**已备料 + 副本演练；落件须监理批**）

- **前置已完成**：F-1/B2-4 已落共享层 `fc59771` —— `check_l1.RULES_DOC → <框架根>/docs/PCB_DESIGN_RULES.md`，K1 侧解析 = `_shared/docs/PCB_DESIGN_RULES.md` ✓。
- **机判复跑（ENG 实测，两跑逐字节同）**：`cd k1 && PM_GATE_PROJECT_ROOT=$PWD PYTHONPATH=<容器>/_shared python3 -c "...check_l1.check_g15()"` ⇒ **`passed=True`，`evidence=「结构预检 + 工艺常识强条全 PASS（3 份报告）」`** ⇒ K1 `G1.5` 已是**真机判**（不再依赖路径缺陷豁免）。
- **撤 waiver 依据（既有监理裁定，非本轮发明）**：`K1-RULING-r03-gbid` + 监理指令 `#K1-02` 第 3 条原文 =「**待学习环批 2 修工具后重跑机判并撤 waiver**（RISK-001）」；CHECKLIST B2-4 授权列 = **需监理批**（撤 waiver = 判据收紧）。
- **备料（幂等，默认 `--check` 不写盘、拒绝对真源 apply）**：`P6_OPEN_READINESS/apply_k1_g15_waiver_retraction_v1.py`
  - 改 `k1/pm_gate/tools/k1_closeout_l2_v1.py`（**写者**：G15_EVIDENCE + RISK-001 文案 → 真机判口径，避免复跑回填 WAIVER）
  - 改 `k1/pm_gate/state_k1.json`（`L1.gates.G1.5.evidence` → 真机判；`risks[RISK-001]` → `closed`；**原 WAIVER 原文两处归档保留**便于追溯）
  - **副本演练**：`--apply` ×2 = `patched → already`（幂等）· 副本 JSON 可解析 · 副本工具 `py_compile` ✓
- **影响面**：G1.5 本已 `passed` ⇒ **语义不变、判据收紧**；`k2_p6_readonly_baseline_v1.py` 的 `is_waiver` 标记自然消失（零代码改动）。

## 2. P6-2 就绪（模板整改）

| 件 | ignore 数 | `sheets` |
|---|---|---|
| `k1/tools/k1_jlc_template.kicad_pro` | **9** | `[]` |
| `k2/tools/k2_jlc_template.kicad_pro` | **9**（与 K1 **逐条相同**） | `None` |
| `k1/k1_v1.kicad_pro`（板） | 9 | `[]` |
| `k2/hw/k2_v4_8L.l7.kicad_pro`（交付板） | **0** | `None` |
| `k2/hw/k2_v4_8L.l4.kicad_pro` | 9 | `[]` |

- **根因**（计划 §7.1）：「判据被成批关闭」**不是 K2 偶发**，是**模板默认值** —— 每块新板天生带 9 条 ignore。
- **整改备选（须监理择一）**：
  - **A（收紧，计划 §7.2-2 原文）**：模板 `rule_severities` 改为**由 manifest 派生**/删除这 9 条 ⇒ 模板 ignore 集 = ∅ = 应然集 ⇒ 结构差异 0，且根因消除。改动面：2 文件 × 9 行（**未动，待批**）。
  - **B（声明）**：`manifest.rule_severity_exemptions` 逐条登记这 9 条 ⇒ 差异 0，但根因仍在（与 §7.2-2 相悖）。
- 整改落件 = 一次性、可复现（`rule_severities` 单点改动），**须先获批**（模板件）。

### 2.1 整改方案 A′（**已备料、dry-run 通过；未落件**）

- 内容：两模板 9 条 `rule_severities` 由 `ignore` → `warning`。
- 依据（**既有先例，非新口径**）：已签认交付板 `k2/hw/k2_v4_8L.l7.kicad_pro`（`33b4eb6cae8359a9`）的 62 条 = **33 error / 29 warning / 0 ignore**，其 9 条同 id 取值**均为 `warning`** ⇒ 逐条可复算。
- 落件面：2 文件 × 9 行；预告读数 = `ignore 0 / warning 29 / error 33`（与 l7 分布逐 id 同值）。
- 补丁件：`P6_OPEN_READINESS/P6_2_template_proposal/{k1,k2}_jlc_template.kicad_pro.diff`；**`patch -p1 --dry-run` 两件均 OK**（真源零改动）。
- 放行后动作 = 应用该 diff → 复核模板 ignore 集 = ∅ → 待 G-c2 应然集落件后核 P6-2「结构差异 0」。

## 2.2 跨板同源普查（计划 §7「跨板复用」；**判定器自身口径**测量）

| 项目 | 板 pro `ignore` | 模板 `ignore` | `fp-lib-table` | `pipeline.yaml` 未覆盖（scope 内，祖先链≤3 层） | `sheets` |
|---|---|---|---|---|---|
| **k1** | **9** | **9** | 缺 | **1** = `k1/sch` | `[]`（空） |
| **k2** | **0**（交付板 `l7`） | **9** | 有（`k2/hw`） | **0** ⊂ 覆盖 | key 缺 |
| key_v2 | 0（无 severities 表，n=0） | 无模板 | 有 | 0 | 非空（3 sheets） |
| pciesw4 | 9（`aic`；`gpu` 同） | 无模板 | 缺 | **4** = `aic`·`aic/sch_kicad`·`gpu`·`gpu/sch_kicad` | `[]`（空） |

- **读数**：9 条 ignore 在 k1（板+模板）· k2（模板）· pciesw4（板）重复出现 ⇒ 计划 §7.1「根因 = 模板默认值」在**全容器层面**成立；pipeline 未覆盖当前合计 **5 个目录**（k1 1 + pciesw4 4；k2 = 0）。
- 口径说明：pipeline 覆盖 = 判定器 `pipeline_present` 的**祖先链≤3 层**口径（非"同目录在否"）；本普查**只读**，不对 key_v2/pciesw4 作阶段判定（各项目阶段门自判）。
- 机读：`P6_OPEN_READINESS/crossboard_census.json`。

## 2.3 ⚠ 冲突：P6-2 模板整改 × 既有 L2 回归闸 **CO-81**（须监理排序；ENG 未动任何件）

**CO-81 口径**（`k2/tools/p3_v57_co81_project_rules_gate.py`）：对 `git ls-files *.kicad_pro` 的每个文件，`rule_severities` 逐规则**须等于** `tools/k2_jlc_template.kicad_pro`（另加 7 项 DRC 规则 = `_shared/eda_core/drc_rules.json:manufacturing`）。

| 事实 | 读数 |
|---|---|
| 受控 `.kicad_pro`（tracked） | **10 条**（其中 `k2_v4_8L.kicad_pro` / `k2_v4_8L.l4.kicad_pro` 为符号链接 → 真实文件 **8**） |
| **现状**（模板 9 ignore） | **7/10 合规 · 3 个 mismatch** = `hw/k2_v4_8L.l5/l6/l7.kicad_pro`（0 ignore）⇒ **CO-81 的『== 模板』子句自 P4 起实际已不成立**（其记录件是 5 文件时代快照，模板 sha16 `206dd0f2` 与现行一致，但文件集已扩到 10） |
| **方案 A′ 后**（模板 9→warning） | **3/10 合规 · 7 个 mismatch** ⇒ 模板**不能单独移动**：会连带 `archive/k2_v4_6L/*`（历史 6L 记录）· `hw/k2_v4_8L.kicad_pro`（设计源 pro）· `hw/k2_v4_8L.l4.kicad_pro`（冻结板配套 pro）等失配 |

**监理三选一**（ENG 不代裁；机读矩阵 `P6_OPEN_READINESS/co81_vs_template_matrix.json`）：

- **O1 全集合一**：模板 + 6 个 9-ignore 真实文件一次性 → `warning`；随之重跑/重签 CO-81 记录 ⇒ 触及历史与设计源**配套**记录件（不动任何 `.kicad_pcb`）。
- **O2 闸改口径**：CO-81 的 severity 子句由「== 模板」改为「== manifest 应然集（deny-by-default）」——与 **P6-2 判据同源**（单一真源）；属 L2 回归闸口径变更 ⇒ 须监理裁 + 记录重签。
- **O3 维持现状**：P6-2 判据不成立（模板仍 9 条）⇒ 与 G-c「模板整改批」自相矛盾。

> **顺带发现（新，未见他处登记）**：CO-81 现状 3 个 mismatch = **既有回归闸静默失守**（l5/l6/l7 的 pro 在 P4 被清理为 0 ignore，模板未随动，闸未重跑）。建议随 O1/O2 一并处置并留痕。

## 3. 未越阶段声明

批 2 已落件（`shared fc59771` · `k2 b58f53a/e019faa`）；**P6-1/P6-2 未启动**（G-c2 未落、模板未批）· **K1 复跑未启动** · **外部首件回件属外部**。冻结件 `d4e81f64…` 等未动 · `criteria/` 未动 · 模板未动 · 生成器/SPEC/原理图未动 · 未派 WORKER。

—— ENG（ARCHER）· 2026-09-20 · 计划/测量件（**非交付件**）
