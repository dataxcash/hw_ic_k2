# K2 · P4 · `pipeline_present` 安装路径（甲/乙）**证据锚** + D-1 消歧两变体 + 门禁有效性复证 · v1 · 2026-09-18

> 缘起：handoff inc45 §5-5（`k2/pipeline.yaml` 安装路径甲/乙 · D-1 消歧）与 §6-3（ENlegal 候选化准备）。
> 本件 = **ENlegal 面**（沙箱只读复算 + 草案），**未安装任何 `pipeline.yaml`、未改仓库任何载体**。判定归监理。
> 仪器：`AppDir/bin/kicad-cli` 10.0.5 · `_shared/eda_core/pipeline/{config,required,engine,checks}.py` · 沙箱 `/tmp/opencode/inc46/d1`（仓外树，自带 `.git` 使 `REPO_ROOT` 生效）。

## 0. 结论（三条，供监理逐条裁）

1. **路径乙「改 check 参数指向现存产物」实测不可行。**
   把 `netlist_connect.nets_yaml` 指向 `k2/hw/data/k2_sch.errata-1.yaml`（`17d540f058631a5e`，即 `pm_gate/project.yaml` 现行 `nets_yaml`）⇒ `engine verify k2` **FAIL 106 处**。
   ⇒ **唯一可绿的安装 = 路径甲**（先提升 `errata-2` + BOM，再装合规件）。
2. **`netlist_connect` 在 errata-2 下 PASS 完全归因 errata-2 的真源修正**（−1 网 + 105 条 `nc`，见 §2）。
   ⇒ `F-10`（nc 声明 / 真源侧新增）是 `pipeline_present` 的**实质闸口**；这 105 条 NC 是否属**设计意图**，ENG 不判（§一 铁律：判据只读 / 判定归监理）。
3. **D-1 消歧两变体均实测合规**（§3）；**但**「装 `pipeline.yaml` ⇒ 提交期强制」在当前布局下**不成立**（§5，新登记 D-3/D-4）：
   3 项必选 sch 检查在**任何提交路径**都不会被执行 ⇒ 只装文件 = `pipeline_present` 形式在岗、**实质 fail-open**（C-12 同型）。

## 1. 沙箱实测矩阵（D-1 两变体 × 甲/乙）

装置：`/tmp/opencode/inc46/d1`（`.git` + `k2/hw/sch/*.kicad_sch` 实拷 + `k2/hw/data/{errata-1,errata-2}` + `k2/fab/k2_v4_bom.csv` ← 草案 `ce2bb814f31be54b`）。

| 案 | `pipeline.yaml` | load_config | meta-gate | `engine preflight` | `engine verify`（3 项） |
|---|---|---|---|---|---|
| C0 负控 | Draft A 原样（`cef091317438eacd`） | **`PipelineError: 缺少 phases 列表`** | 同左（抛错，非干净 FAIL） | — | — |
| C1 变体①合并 + 甲 | `pipeline.merged.draft.yaml` | PASS | PASS（1 项目声明完整） | PASS | **3/3 PASS** |
| C2 变体②分离 + 甲 | `pipeline.phases-only.errata2.draft.yaml` | PASS | PASS | PASS | **3/3 PASS** |
| C3 变体②分离 + **乙** | `pipeline.phases-only.errata1.draft.yaml` | PASS | PASS | PASS | **FAIL**（`netlist_connect` 106 处） |
| C4 D-2 负控（nets_yaml 指向缺件） | `pipeline.missing-artifact.draft.yaml` | PASS | PASS | PASS | `sch_structural` PASS 后 **未捕获 `FileNotFoundError`**，verify 中止 |

C3 的 106 处构成：1 条「网 `PWR_5V_KEY` 在 KiCad netlist 中不存在」+ 105 条「非声明悬空」（如 `J3/SMB_CLK_16`、`U6/A_PERN8_CL1`、`C89/A_1` …）。

## 2. 真源三方差异量化（F-10 决策锚）

| 件 | sha16 | `nets` | `nc` 声明 | 相对真源的差 |
|---|---|---|---|---|
| `k2/hw/data/k2_sch.yaml`（真源，冻结） | `dd794c54f7ce7417` | 101 | **无 `nc` 键** | — |
| `k2/hw/data/k2_sch.errata-1.yaml` | `17d540f058631a5e` | 101 | **无 `nc` 键** | **与真源逐项相同**（nets 集合差 = ∅） |
| `k2/docs/drafts/j9-wiring-option-a/k2_sch.errata-2.draft.yaml`（草案） | `bdacbf944ca0c796` | **100** | **105** | **−1 网（`PWR_5V_KEY`）+ 105 条 `nc`** |

即：`errata-2 = 真源 − PWR_5V_KEY + 105 NC`。而 §1-C3 中 `netlist_connect` 对 errata-1 报的「非声明悬空」**恰为 105 条**、另加 `PWR_5V_KEY` 缺失 1 条。
⇒ `netlist_connect` 的 PASS/FAIL **在本板 100% 由该真源修正决定**，与板/图几何无关。
⇒ 两条互斥读法（ENG 不择一，交监理/owner）：
 **(a) 正解**：`PWR_5V_KEY` 确为「声明未落地」的伪网，105 引脚确为设计 NC ⇒ errata-2 是真源纠错，路径甲成立；
 **(b) 缩口径**：为过判据而删网 + 批量声明 NC ⇒ C-12 同型，**禁**（owner 铁律 §一「明确不计入」）。
判定所需输入 = **105 引脚的设计意图**（原理图侧，非 ENG 可自证）。

## 3. D-1 消歧：两个合规变体（文件见 `docs/drafts/p4-pipeline-yaml-disambiguation-v1/`）

D-1 实况复核：`docs/drafts/K2-P4-criteria-draft-v2/pipeline.yaml.draft`（`cef091317438eacd`）**不是 pipeline.yaml**，
其 `criteria:` / `fail_closed:` / `artifacts:` 三键在 `_shared/eda_core/**` 与 `criteria/**` 中**实测零消费者**（`grep -rn` 无命中）；
其 README 描述的是**另一件**（j9 合规件的 `phases` + 3 检查）。⇒ 归类：**载体/文档失配**（描述符被标为流程件）。

| 变体 | 做法 | 实测 | 取舍点（交监理） |
|---|---|---|---|
| **① 合并单件** | Draft A 保留 `criteria/fail_closed/artifacts`，补 `phases` + 必选三联 | §1-C1 全 PASS | 单件承载「描述符 + 流程」；但三键仍**无消费者** ⇒ 保留即有「声明在岗、实际无人读」风险 |
| **② 职责分离** | Draft A **改标签**为 criteria-descriptor（不作 pipeline.yaml 安装）；安装 phases-only 件（= j9 合规件口径） | §1-C2 全 PASS | 判据清单语义归 `criteria/manifest.k2.yaml`（已有 `checks:` 段）⇒ 无死键；**推荐** |

两变体均含：`phases:[preflight(project_sch_coverage), verify(sch_structural, netlist_connect, bom_consistent)]`；
差异仅在是否把 Draft A 的描述符键并入 pipeline.yaml。**两变体都不新增检查齿**（仅复用 `REQUIRED_SCH_CHECKS` 三类）。

## 4. 安装前置与顺序硬约束

- **共同前置（甲/乙都绕不开）**：`k2/hw/data/k2_sch.errata-2.yaml`（甲）**或** 等效一致网表 + **`k2/fab/k2_v4_bom.csv`**（`k2/fab/` 目录现不存在）。
  缺任一 ⇒ `netlist_connect`/`bom_consistent` 命中 **D-2**：抛未捕获 `FileNotFoundError`（§1-C4），**不是**干净 FAIL。
- **顺序硬约束**：`k2/pipeline.yaml` 一旦在库，`k2/hw/sch/**` 的项目即被 `required` 覆盖（已实测）；若 verify 生效（见 §5 则不然），
  每次 k2 提交都会跑 3 项 sch 检查 ⇒ 必须在 `errata-2`+BOM 落库**之后**再装 `pipeline.yaml`，否则 k2 提交会被自锁。
- **参考**：`netlist_connect` 的 `nc` 白名单消费 `spec_data.get("nc")`（`checks.py:88-90`）；BOM 比对只看 sch netlist 的 ref 集（与 nets_yaml 无关）。

## 5. 门禁有效性复证 —— **新登记 D-3 / D-4 / D-5**（只读取证，未改 `_shared/**`）

> 目的：确认「装 `pipeline.yaml`」是否真的产生**提交期强制**。结论：**否**。

- **D-3（per-project verify 永不触发）**：`pre-commit` 的 `affected` 计算
  `prefix = str(yaml_path.parent.relative_to(REPO_ROOT)) + '/'`，随后要求 staged 路径 `startswith(prefix)`。
  · **k2 内部提交**（`git -C k2 commit`，`core.hooksPath=_shared/...` 相对路径）⇒ `ROOT=k2`、`REPO_ROOT=k2` ⇒ `prefix='./'`，
    staged 名为 `docs/...` ⇒ **不命中**（沙箱复刻 `/tmp/opencode/inc46/hook` 实测 `affected=[]`）。
  · **容器级提交**（`ROOT=ic_hw`）⇒ `prefix='k2/'`，但 submodule 变更的 staged 名是 **gitlink `k2`**（无 `/` 后缀）⇒ `startswith('k2/')=False` ⇒ **同样不命中**（实测 `git diff --name-only` → `k2`）。
  ⇒ **两条路径都不触发 `engine verify`**；3 项必选 sch 检查在任何提交都不执行。
- **D-4（`phases[].checks` 引擎不执行）**：`engine.cmd_run` 只执行 `ph['cmd']` 与 `ph['verify']`；`checks` 段**仅**被 `required.declared_checks` 读取（声明用），
  `cmd_preflight` 也走 `cmd_run` ⇒ **`checks:` 是纯声明，无执行路径**。
- **D-5（`_shared` 双份分叉）**：k2 子模块挂的是 `k2/_shared`（`HEAD=9a67d9e03acaafa2`），与容器 `_shared`（`HEAD=0ec324b54e688233`）**不同 commit**；实测 `pipeline/checks.py` 二者分叉
  （差异仅 `check_gate` 的落盘路径 `/tmp` vs `/tmp/opencode`，C-2 红线批）。⇒ 实际执行的是**较旧**一份；本件全部实测结论不受影响（未使用 `check_gate`）。

⇒ 对 J-9 的后果：装件可令草案判据 `pipeline_present`（文件存在性）PASS，**但** J-9 的「门禁接入」实质（③必选检查真被执行）**不成立**。
**只装文件 = 形式在岗**；请监理把 D-3/D-4/D-5 与既有 D-2 一并派单（共享层，非本板补丁——计划 §⑥-4「ENG 不逐板打补丁」）。

## 6. 复跑（每处实测）

```bash
cd /home/fila/jqdDev_2025/ic_hw; S=/tmp/opencode/inc46/d1
# 沙箱（仓外树 + .git + sch 实拷 + errata-1/2 + 草案 BOM）；变体文件见 docs/drafts/p4-pipeline-yaml-disambiguation-v1/
cp docs/drafts/p4-pipeline-yaml-disambiguation-v1/pipeline.phases-only.draft.yaml $S/k2/pipeline.yaml
(cd $S && PYTHONPATH=/home/fila/jqdDev_2025/ic_hw/_shared python3 -c "
from eda_core.pipeline import engine; engine.main(['verify','k2'])")
# 乙不可行（期望 netlist_connect FAIL 106 处）：
#   把该件 nets_yaml 改为 k2/hw/data/k2_sch.errata-1.yaml 后重跑
# 真源三方计数：# python3 -c "import yaml;d=yaml.safe_load(open('<件>'));print(len(d.get('nets') or {}),len(d.get('nc') or []))"
# 死键检索（Draft A 的 criteria:/fail_closed:/artifacts: 三键无消费者；引擎只按类型读 phases）：
#   grep -rn '"criteria"\|"fail_closed"\|"artifacts"' _shared/eda_core/pipeline/*.py   # 期望 0
#   grep -n 'pipeline.yaml' criteria/adjudicate.py    # 仅 os.path.exists（存在性），不解析三键
# D-3 复刻：见本件 §5（沙箱 ${S%/*}/hook 为「REPO_ROOT=项目仓根」的忠实复刻）
```

## 7. 边界

本件**只读 + 沙箱草案**：未创建/安装 `k2/pipeline.yaml`；未改板/pro/库/`fp-lib-table`/`pm_gate/**`/真源 yaml/SPEC/生成器/`criteria/**`/`_shared/**`；未派 WORKER；临时仅 `/tmp/opencode`。
—— ENG（ARCHER）· 2026-09-18 · 复合候选 `9682dd026f48c04a`
