# K2 · P4 · **`G11` ↔ `pipeline.yaml` 真源绑定草案**（同源校验 ＋ 甲/乙 改动面矩阵）· v1 · 2026-09-18

> 缘起：handoff inc64 §6-3-(m)「`G11`↔`pipeline.yaml` 真源绑定**草案**（§5-D(iii)，接 inc57 §5；纯文档/草案，不落件）」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读 + `/tmp` 校验脚本**，仓库零载体改动（仅新增本证据件）。
> 锚：生成器 `k2/tools/k2_gen_v5.py` **`d8d15a31061f450f`** · `pm_gate/project.yaml` `9cee872bd6fbdc67` · 真源 `k2/hw/data/k2_sch.yaml` **`dd794c54f7ce7417`** · `k2_sch.errata-1.yaml` **`17d540f058631a5e`**（语义同真源）· errata-2 草案 `bdacbf944ca0c796` · 变体② `pipeline.yaml` 草案 **`f049a4d97e6fe9cb`** · 图纸 `21e8891ea3fc4c06` · 判据 `897e8bfde60e2cfe`。
> 仪器（`/tmp`，易失）：`/tmp/opencode/inc63/truth_source_binding_check.py` **`67dacb2aab6ed5fa`** · 乙变体件 `pipeline.yi.draft.yaml` **`ff53da93b738b34a`**。

## 0. 结论（五条）

1. **绑定链共 4 个**消费**载体**（第 5 个 `criteria/manifest.k2.yaml` **实测无 `nets_yaml` 键** ⇒ 判据侧不经它消费；`criteria/adjudicate.py` 的 `nets_yaml` 是**入参**、由外层喂 ⇒ 源头仍是下列 4 者）：
   ① `pm_gate/project.yaml::nets_yaml` ② `k2/pipeline.yaml::phases[verify].netlist_connect.nets_yaml` ③ 生成器 `k2_gen_v5.py::YAML_PATH` ④ `p3_drawings.json::nets_yaml`（判据入参来源）。
2. **「同源」不能用字节 sha 判**：冻结真源 `k2_sch.yaml`（`dd794c54f7ce7417`）与 `k2_sch.errata-1.yaml`（`17d540f058631a5e`）**字节不同、语义完全相同**（本件实测语义 digest 均 `2d2e18a25f4f2722`：nets 101 / nc 0 / symbols / sheets 一致）。
   ⇒ ENG 建议的判定口径＝**语义 digest 相同 ＋ 登记 path/sha16**（脚本 `truth_source_binding_check.py` 已实现，只读、不进 `criteria/`）。
3. **现状实测：`甲` 一装即 fail-closed**——候选草案 `f049a4d97e6fe9cb` 指 `k2/hw/data/k2_sch.errata-2.yaml`，**该件不存在**（nets 100 / nc 105 的草案在 `docs/drafts/j9-wiring-option-a/`）⇒ 校验 **FAIL**，与 inc58 §0-1「原样装即自锁」互证。
4. **`乙` 版校验 PASS**（`--pipeline /tmp/opencode/inc63/pipeline.yi.draft.yaml`：4 载体全落 `2d2e18a25f4f2722`）——但 `乙` 的**实质前置是 `D-7a`**（否则 `errata-1` 105 条非声明悬空 ⇒ 每次 k2 提交自锁），且 **⑤ `C89/A` 两路都绕不开**。
5. **`G11` 不得单独先落**（inc57 §0-4 的交叉绑定风险本件实测确认：生成器现走 `ROOT/boards/k2_sch.yaml`（symlink → `k2_sch.yaml`），一旦改成 `project_config()["nets_yaml"]` 就会跟随 §5-8 的甲/乙裁定；**`G11` 必须排在真源裁定之后、与 `pipeline.yaml` 同批**）。本件**不新增检查齿**（owner ②）。

## 1. 绑定链与现状实测（脚本输出，`rc=1`）

| 载体 | 现声明 | 解析后 sha16 | 语义 digest | nets/nc |
|---|---|---|---|---|
| `pm_gate/project.yaml::nets_yaml` | `hw/data/k2_sch.errata-1.yaml` | `17d540f058631a5e` | `2d2e18a25f4f2722` | 101/0 |
| `pipeline` 候选 DRAFT `f049a4d97e6fe9cb::…nets_yaml` | `k2/hw/data/k2_sch.errata-2.yaml` | **MISSING** | — | — |
| `k2_gen_v5.py::YAML_PATH = ROOT/boards/k2_sch.yaml` | symlink → `hw/data/k2_sch.yaml` | `dd794c54f7ce7417` | `2d2e18a25f4f2722` | 101/0 |
| `p3_drawings.json::nets_yaml` | `k2/hw/data/k2_sch.errata-1.yaml` | `17d540f058631a5e` | `2d2e18a25f4f2722` | 101/0 |

**同源校验：FAIL** —— 2 个语义源：`2d2e18a25f4f2722`（①②③ 中已存在的 3 者）· `MISSING`（候选 pipeline 的 `errata-2` 声明件不存在 ⇒ fail-closed）。
⇒ 现状**不是**「生成器与判据不同源」（二者语义相同），而是「**候选 pipeline.yaml 与其余三者不同源 ＋ 声明件缺失**」；一旦按 inc58 装上共享层修正件，该不同源就会**真执行**（`netlist_connect` 读 `errata-2`）。

## 2. 甲/乙 改动面矩阵（每载体必须**同批**落库，任何单点落库即产生异源）

| # | 载体 | **甲**（`errata-2`） | **乙**（`errata-1` + `D-7a`） | 现状 |
|---|---|---|---|---|
| 1 | `k2/hw/data/k2_sch.errata-2.yaml`（**新件**） | **须落库**（＝草案 `bdacbf944ca0c796`；删 `PWR_5V_KEY` ＋ 105 NC） | 不建 | 不存在 |
| 2 | `k2/hw/data/k2_sch.errata-1.yaml` | 保留（不消费） | **消费**（现值即可，`17d540f058631a5e`） | 存在 |
| 3 | `pm_gate/project.yaml::nets_yaml` | 改 → `hw/data/k2_sch.errata-2.yaml` | **不改**（现 `errata-1`） | `errata-1` |
| 4 | `k2/pipeline.yaml::netlist_connect.nets_yaml` | 保持草案 `errata-2` | 改指 `errata-1`（`ff53da93b738b34a` 版） | 文件不存在 |
| 5 | `k2_gen_v5.py::YAML_PATH`（**G11**） | `ROOT/_PMCFG.project_config()["nets_yaml"]` ⇒ 得 `errata-2` | 同左 ⇒ 得 `errata-1` | 硬编码 `ROOT/boards/k2_sch.yaml` |
| 6 | `p3_drawings.json::nets_yaml`（path/sha16） | 随 Z4 整族刷新改指 `errata-2` | **不改**（已 `errata-1`/`17d540f058631a5e`） | `errata-1` |
| 7 | `criteria/**` | **不动**（判据只读；`manifest.k2.yaml` 无 `nets_yaml` 键 ⇒ 零改动） | 同左 | — |
| 8 | 共享层 `D-7` | 不需要（`errata-2` 自带 105 NC） | **必须 `D-7a`（①②）**，③ **禁**（C-1） | 未修 |

**取舍要点（ENG 只陈述，不择一）**：`甲` 的 105 NC ＋ 删网属**真源侧新增**（F-10），须先证明其属**设计意图**（否则 C-12 同型：为过判据而缩口径）；`乙` 不动真源、只修判据读取口径（`D-7a` 读 top-level ＋ `sheets[].placements[].nc`），但**每次提交都在 105 条口径上依赖 `D-7a` 已修**。
**⑤ 与甲/乙无关**：inc58 §2 实测 —— 乙（`D-7a`）仍 FAIL 2 行、启用 ③ 后仍 FAIL 1 行 ⇒ **⑤ 是硬前置**（须具名裁定；判属 L1 则升级 owner）。

## 3. 同源校验（ENG 侧投递前自证；只读、不进仓库）

```bash
cd /home/fila/jqdDev_2025/ic_hw
python3 /tmp/opencode/inc63/truth_source_binding_check.py                      # 当前（甲草案）⇒ 期望 rc=1 / FAIL
python3 /tmp/opencode/inc63/truth_source_binding_check.py --pipeline /tmp/opencode/inc63/pipeline.yi.draft.yaml   # 乙 ⇒ 期望 rc=0 / PASS
```
口径：解析 `nets`/`nc`/`symbols`/`sheets` 四者 → 规范化 JSON → sha256 前 16 位（语义 digest）；**MISSING ＝ 独立失败桶**（fail-closed）。
产出为一次性 ENG 自证；**不写入 `criteria/`、不新增检查齿**（owner ②）。

## 4. 落库顺序（硬序；与 inc57 §3 / inc58 §3 对齐）

```
Step 0  监理裁：§5-8 真源路径（甲/乙）＋ ⑤ `C89/A`（+ 是否连 D-7a / 是否触 C-1）
Step 1  共享层单笔修 5 项（D-2/D-3/D-4/D-4b/D-7）→ 统一验收（inc58 端到端预演）
Step 2  前移 k2 `_shared` pin（D-5）
Step 3  前置件落库：甲 ⇒ `errata-2.yaml`；乙 ⇒ 不动真源。**两路都要**：`k2/fab/k2_v4_bom.csv`（见 inc63 BOM 件）
Step 4  装 `k2/pipeline.yaml`（变体② phases-only；`nets_yaml` 按 Step 0 裁定）
Step 5  改生成器 `G11`（3 行 accessor；`YAML_PATH = ROOT/_PMCFG.project_config()["nets_yaml"]`）＋ 去锚板依赖同批
Step 6  同源校验（§3）⇒ PASS ＋ `engine verify k2` 3/3 PASS ⇒ 才可继续 P4 关门四件
```
**禁**：Step 4 早于 Step 3（D-2 抛未捕获 `FileNotFoundError` ＋ 自锁提交）；Step 5 早于 Step 0（G11 落成后生成器与判据会指不同真源，inc57 §0-4）。

## 5. 与 `D-7a` 的同批约束（乙路径专有）

- `D-7a`（①②：读 top-level `nc` ＋ `sheets[].placements[].nc`）→ `errata-1` 的 105 条非声明悬空被正确白名单化；`③`（`pintype` 推断）**禁**（C-1：把被验对象当判据真源）。
- `D-7` 属共享层（`checks.py`），须与 `D-2/D-3/D-4/D-4b` **同笔**落，避免多次改同一函数（`checks.py` 现 k2 pin 为 `e88c70aaa56ce22f` ≠ 容器 `02b41e8b6d6d9b3a`，＝ D-5 分叉）。

## 6. 复跑（每处实测；仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw
python3 /tmp/opencode/inc63/truth_source_binding_check.py            # 甲 ⇒ rc=1；乙 ⇒ rc=0（见 §3）
# 真源三方计数（甲/乙 差异量化）：
python3 -c "
import yaml
for f in ('k2/hw/data/k2_sch.yaml','k2/hw/data/k2_sch.errata-1.yaml','k2/docs/drafts/j9-wiring-option-a/k2_sch.errata-2.draft.yaml'):
    d=yaml.safe_load(open(f)); print(f, len(d.get('nets') or {}), len(d.get('nc') or []))"
# 判据侧零消费复核：manifest 应 0 命中；criteria/ 命中应仅 adjudicate.py 的入参名（非自读路径）：
grep -rn 'nets_yaml' criteria/manifest.k2.yaml || echo "manifest.k2.yaml 无该键 ✓"
grep -rc 'nets_yaml' criteria/adjudicate.py   # 期望仅作为函数入参名出现（无自读路径/无文件路径常量）
```

## 7. 边界

本件**只读 + `/tmp` 校验脚本**：未改真源/SPEC/图纸/生成器/模板/板/pro/库/`fp-lib-table`/`pm_gate/**`/`criteria/**`/`_shared/**`；
**未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`、未建 `errata-2`**；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode/inc63`；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 生成器 `d8d15a31061f450f` · 校验脚本 `67dacb2aab6ed5fa`
