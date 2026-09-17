# K2 · P4 · **「判据安装」端到端预演**（真 sch 产物 + 真 check 实现 + 真 hook）· v1 · 2026-09-18

> 缘起：handoff inc57 §6-3-(e)「`/tmp` 端到端预演骨架（按 inc57 §0-3 的 5 步）」。本会话**无监理放行** ⇒ ENlegal 面。
> 本件把前几件的**装置级**结论（inc57 四案）升级为**真产物级**预演：用 `k2/hw/sch/*.kicad_sch`（真文件）+ `kicad-cli 10.0.5`
> + 真 check 实现 + 真 hook，跑通「装 `pipeline.yaml` → 提交 → 判定」的完整链。**仓库零载体改动**（仅新增本证据件）。
> 装置：`/tmp/opencode/inc58{,b}/`（全修共享树 `shared_full` + 镜像仓 `root`）。锚：hook `62dc6a4e476f6b55` / D-3 修正 hook / engine `a015f8cfcc24c581`（D-4+D-4b）/ checks `0cbd9a478c694a12`（D-2×2 + D-7 ①②③ 开关式）。

## 0. 结论（六条，其中 3 条改变放行判断）

1. **变体② draft **原样**不可安装（实测自锁）**：`k2/hw/data/k2_sch.errata-2.yaml` **不存在**、`k2/fab/` 目录 **不存在** ⇒ 装后 k2 每次提交 rc=1
   （`netlist_connect 缺件: …k2_sch.errata-2.yaml — fail-closed`）。**前置件必须与 `pipeline.yaml` 同批落库。**
2. **`D-4b` 在真产物上生效（端到端确认）**：Case A/B 输出均含 **`preflight/check[project_sch_coverage]: PASS`** —— 该行在 D-4b 之前**不可能出现**
   （inc57 已证 `cmd_verify` 只跑 `verify:`）；即「提交期真强制」已被端到端打通。
3. **【放行判断】`乙`（`errata-1` + `D-7a` + BOM 齐备、共享层全修）**仍**不可安装**：`netlist_connect` **FAIL**，且失败项**唯一**＝ **⑤ `C89/A`**：
   - ①②（`D-7a`，③ 关）→ **2 行**：`网 'PWR_5V_KEY' 在 KiCad netlist 中不存在` ＋ `非声明悬空: C89/A_1 (unconnected-(C89-A-Pad1)) — 不在 YAML nc 白名单`
   - ①②③（③ 开，**C-1 违规**口径）→ **1 行**（仅 `PWR_5V_KEY` 缺网）⇒ **③ 救不了 ⑤** ⇒ **无须为 ③ 破 C-1**。
   ⇒ **⑤ 是「判据安装」的硬前置**：`甲`/`乙` 两条路都绕不开；`pipeline.yaml` 不得先于 ⑤ 裁定安装。
4. **【放行判断】`甲` 不可行性再确认**：`errata-2` 不在库（第 1 条）；创建它＝删真源声明的网 + 把真源连接脚声明 NC（**C-12 同型风险**，须先证）。
5. **【前置口径】BOM 前置可满足，但 schema 有坑（实测踩中）**：`check_bom_consistent` 用 `csv.reader` + **`row[0].split(",")`** ⇒
   未加引号的「逗号分隔多 ref」被 `csv` 拆成多列 ⇒ **只读到第一个 ref**（实测报 `netlist 独有 ['C74','C75',…]`）。
   **正确口径＝每行一个 ref（或整字段加引号）**；修正后 **`bom_consistent: True（55 器件）`**、`sch_structural: True（0 warnings）`。
6. **`D-3` 作用域修正（实测）**：**容器式布局（项目在子目录，如本题镜像 `k2/`）不受 D-3 影响** —— 原版 hook 的 `startswith("k2/")` **命中**，`受影响项目: k2` 正常出现。
   D-3 只在「**项目根 == 仓根**」（k2 子模块内提交）时触发。⇒ 判据安装必须**分别验证两条提交路径**（inc57 的 `d3A` 覆盖「仓根即项目根」，本件覆盖容器式）。

## 1. 装置（全修共享树 + 真产物镜像）

| 组件 | 值 / 来源 |
|---|---|
| hook（旧 pin） | 仓库 `_shared/eda_core/pipeline/hooks/pre-commit` `62dc6a4e476f6b55`（D-3 未修） |
| hook（新 pin） | `/tmp/opencode/inc51/pre-commit.d3fix`（D-3 修正：`rel=='.'` + 裸 gitlink） |
| engine（全修） | `/tmp/opencode/inc58/shared_full/eda_core/pipeline/engine.py` **`a015f8cfcc24c581`**（inc51 D-4 = `cmd_run` ＋ **本会话 D-4b = `cmd_verify`**） |
| checks（全修） | `…/checks.py` **`0cbd9a478c694a12`** ＝ inc50 版（D-7，`K2_NC_SOURCES` 开关）＋ inc52 版 **D-2** 四处缺件 guard（`patch` 合并；语法/标记复核通过） |
| 真 sch | `k2/hw/sch/*.kicad_sch` 6 件（**复制为真文件**，非 symlink：`Path.rglob` 不跟随符号链接目录） |
| 真源 | `k2/hw/data/k2_sch.errata-1.yaml`（`17d540f058631a5e`）、`k2_sch.yaml` |
| `pipeline.yaml` | 变体② draft `f049a4d97e6fe9cb` 原样（Case A）／改 `nets_yaml→errata-1`（Case B） |
| kicad-cli | `AppDir/sharun kicad-cli` **10.0.5** |
| 镜像保真纪律 | 复制树须 `export SHARUN=<repo>/AppDir/sharun`；否则 `find_sharun()` 回落字面量 `sharun` → `FileNotFoundError`（**实测踩中**）。真仓库路径上 `find_sharun()` 在容器根与 k2 子模块内**均解析正确**（实测） |

**提交路径**：镜像仓 `root/` 内 `k2/pipeline.yaml` 落于子目录 ⇒ 走**容器式**路径（项目根 ≠ 仓根），由修正 hook 的 `c.startswith("k2/")` 命中。

## 2. 三案实测（真 hook + 真 engine + 真 sch）

| 案 | `pipeline.yaml` | 前置件 | hook | 实测 rc | 关键输出 |
|---|---|---|---|---|---|
| **A** | 变体② **原样**（`errata-2`） | 无（errata-2 / BOM 均缺） | D-3 修正 | **1** | `preflight/check[project_sch_coverage]: PASS` · `verify/sch_structural: PASS` · **`verify/netlist_connect: FAIL`** → `缺件: …k2_sch.errata-2.yaml — fail-closed` |
| **B** | `nets_yaml → errata-1`（**乙**） | errata-1 ✓ + `k2/fab/k2_v4_bom.csv` ✓（55 refs） | D-3 修正 | **1** | `preflight/check[…]: PASS` · `sch_structural: PASS` · **`netlist_connect: FAIL`** → **2 行**（`PWR_5V_KEY` 缺网 ＋ `C89/A_1` 非声明悬空） |
| **B′** | 同 B，但 `K2_NC_SOURCES=top,placements,pintype`（**③ 开＝C-1 违规**） | 同 B | D-3 修正 | **1** | `netlist_connect: FAIL` → **1 行**（仅 `PWR_5V_KEY` 缺网） |
| **C** | 同 B | 同 B | **仓库原版 hook**（D-3 未修） | **1** | **`受影响项目: k2` 照常出现** ⇒ **容器式路径不受 D-3 影响**（见 §0-6） |
| **D** | 单跑 check（不设 `K2_NC_SOURCES`，③ 开） | 同 B | — | — | `sch_structural: True（0 warnings）` · **`bom_consistent: True（55 器件）`** · `netlist_connect: False（1 处：PWR_5V_KEY 缺网）` |

**⑤ 的两行是同一真项**：真源声明 `PWR_5V_KEY`（唯一节点 `C89/A`），而原理图侧 `C89/A` 实为 unconnected ⇒ 两行互为一体。

## 3. 前置清单（放行后一次投递必须齐备；本会话实测「现状缺什么」）

| # | 前置件 | 现状 | 缺则后果 | 生成/裁定归属 |
|---|---|---|---|---|
| 1 | 真源选择：`甲`=`errata-2.yaml`（新件）／`乙`=`errata-1`+`D-7a` | **未裁**（§5-8） | 装 `pipeline.yaml` 即自锁（案 A） | 监理裁 |
| 2 | **⑤ `C89/A` 具名裁定** | **未裁**（唯一真项） | **两条路均 rc=1**（案 B/B′） | 监理（判属 L1 则升级 owner） |
| 3 | `k2/fab/k2_v4_bom.csv` | **不存在**（`k2/fab/` 无） | `bom_consistent` FAIL | ENG 可生成；**口径见 §0-5（每行一 ref）** |
| 4 | `k2/pipeline.yaml`（变体②） | 不存在（红线：须放行） | 门禁不在岗 | gate 属主 |
| 5 | 共享层 5 修（D-2/D-3/D-4/**D-4b**/D-7） + pin 前移 | 未落 | 形式在岗（inc57） | 共享层属主／监理 |

**顺序**：`⑤ 裁定` ∧ `真源裁定` → 生成/落 `errata-*` + BOM → 共享层 5 修 → pin 前移 → 装 `pipeline.yaml`（inc57 §0-3 的 5 步，本件为其实测证据）。

## 4. 复跑（每处实测）

```bash
cd /home/fila/jqdDev_2025/ic_hw; R=$PWD; W=/tmp/opencode/inc58b
# ① 全修共享树（engine 见 inc57 §2 的 D-4+D-4b；checks = inc50 D-7 + inc52 D-2 的 patch 合并）
#    mkdir -p /tmp/opencode/inc58/shared_full && cp -a /tmp/opencode/inc57c/shared_fix2/eda_core /tmp/opencode/inc58/shared_full/eda_core
#    cp /tmp/opencode/inc50/eda_core/pipeline/checks.py /tmp/opencode/inc58/shared_full/eda_core/pipeline/
#    diff -u $R/_shared/eda_core/pipeline/checks.py /tmp/opencode/inc52/eda_core/pipeline/checks.py > d2.patch
#    patch /tmp/opencode/inc58/shared_full/eda_core/pipeline/checks.py < d2.patch
# ② 镜像仓（真 sch 复制为真文件；非 symlink）
mkdir -p $W/root/k2/{docs,hw/sch,hw/data,fab} && cd $W/root
cp $R/k2/hw/sch/*.kicad_sch k2/hw/sch/
cp $R/k2/hw/data/k2_sch.errata-1.yaml $R/k2/hw/data/k2_sch.yaml k2/hw/data/
cp $R/k2/docs/drafts/p4-pipeline-yaml-disambiguation-v1/pipeline.phases-only.draft.yaml k2/pipeline.yaml
echo probe > k2/docs/PROBE.md; ln -sfn /tmp/opencode/inc58/shared_full _shared
git init -q && git add k2/pipeline.yaml k2/docs/PROBE.md
export SHARUN=$R/AppDir/sharun            # ← 复制树必须显式指定（否则 find_sharun 回落 'sharun'）
# ③ 案 A（原样）→ 期望 rc=1、缺件 errata-2
K2_NC_SOURCES=top,placements bash /tmp/opencode/inc51/pre-commit.d3fix
# ④ 案 B（乙）：改 nets_yaml→errata-1；BOM 每行一 ref
sed -i 's#errata-2.yaml#errata-1.yaml#' k2/pipeline.yaml
$R/AppDir/sharun kicad-cli sch export netlist k2/hw/sch/k2_sch.kicad_sch --format kicadsexpr --output $W/net.kicadsexpr
python3 -c "
import re,pathlib;t=pathlib.Path('$W/net.kicadsexpr').read_text()
r=sorted({m.group(1) for m in re.finditer(r'\(comp\s+\(ref \"([^\"]+)\"\)',t)})
pathlib.Path('k2/fab/k2_v4_bom.csv').write_text('Ref\n'+'\n'.join(r)+'\n');print(len(r),'refs')"
git add k2/pipeline.yaml k2/fab/k2_v4_bom.csv
K2_NC_SOURCES=top,placements bash /tmp/opencode/inc51/pre-commit.d3fix   # 期望 rc=1、2 行（⑤）
K2_NC_SOURCES=top,placements,pintype bash /tmp/opencode/inc51/pre-commit.d3fix  # 期望 rc=1、1 行（③ 不救 ⑤）
# ⑤ 案 C（旧 pin，容器式）：仓库 hook 仍能命中 ⇒ D-3 作用域结论
bash $R/_shared/eda_core/pipeline/hooks/pre-commit
```

## 5. 边界

本件**只读 + `/tmp` 副本/镜像（未落库）**：未改 `_shared/**`、生成器、模板、板、pro、库、`fp-lib-table`、`pm_gate/**`、SPEC、真源、`criteria/**`；
**未创建 `k2/pipeline.yaml`**、未创建 `k2/fab/**`；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode`；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · hook `62dc6a4e476f6b55` · engine `a015f8cfcc24c581` · checks `0cbd9a478c694a12` · kicad-cli 10.0.5
