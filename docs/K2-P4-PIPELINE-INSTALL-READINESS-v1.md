# K2 · P4 · `pipeline_present`（判据集**最后一个 FAIL**）**安装就绪度** · 证据件 v1 · 2026-09-18

> 缘起：⑥+⑦ 复合候选板 `9682dd026f48c04a` 下，草案 v4 判定器唯一 FAIL = `pipeline_present`（**gate 安装项**）。
> ENG 只做**只读验证 + 安装就绪度报告**（安装属 gate 属主侧；本件未写仓库任何路径）。判定归监理。

## 1. 判据侧实证（沙箱；仓库零写入）

沙箱 = `/tmp/opencode/p4gate*`（仓外树：`k2/hw/sch/*.kicad_sch` 软链 + 一个 `k2/pipeline.yaml`）。

| 案 | 装置 | 判定器（草案 v4 安装件 + W-8 v2 口径 + 复合候选板） |
|---|---|---|
| A | 装 `k2/pipeline.yaml` | **17 PASS / 0 FAIL**（`=> PASS（PROVISIONAL：manifest 未经监理签认）`） |
| B（负控） | 抽掉该文件 | **16 PASS / 1 FAIL**，FAIL = `pipeline_present`（证明沙箱扫描生效，非空跑） |

`pipeline_present` 的实现（`adjudicate.draft-v4.py:278-298`）：对 scope 内每个含 `.kicad_sch` 的目录，
**自身 + 最多 3 层祖先**查找 `pipeline.yaml` ⇒ 文件放 `k2/pipeline.yaml` 即覆盖 `k2/hw/sch`（实测）。
⇒ **P4 判据集最后一个 FAIL 已证明只是「安装动作」**；ENG 侧无未证明判据。

## 2. ⚠️ 两个互不兼容的 pipeline 草案（**安装前必须先消歧**；缺陷登记 D-1）

| 件 | sha16 | 装置实测 | 判定 |
|---|---|---|---|
| `docs/drafts/K2-P4-criteria-draft-v2/pipeline.yaml.draft`（357 B） | `cef091317438eacd` | 框架 `config.load_config("k2")` ⇒ **`PipelineError: 缺少 phases 列表`**（`_shared/eda_core/pipeline/config.py`：`phases` 必填非空唯一 id） | **不可安装** |
| `docs/drafts/j9-wiring-option-a/pipeline.k2.draft.yaml`（859 B） | `b74d1f1e883c2ca3` | 框架 meta-gate `required.check_all_projects_coverage()` ⇒ **PASS「全部 1 项目 sch 必选检查声明完整」**；引擎 `preflight k2` ⇒ PASS | **合规安装件** |

**D-1（载体/文档失配）**：前者 README 自称「k2 域门禁接入草案（**符合 eda_core 管线 schema**：含 `phases` + 3 项必选
sch 检查；安装时复制为 `k2/pipeline.yaml`）」，但其**实际文件无 `phases`、无任何 sch 检查声明**（内容为
`version/project/scope/fail_closed/criteria/artifacts` 的判据侧描述符）。若按该 README 安装，**框架 commit 期
meta-gate 会直接抛错**（不是干净 FAIL）。⇒ 须监理明确「作废改标签」或「补 `phases`+3 checks 后改用」。

## 3. ⚠️ 安装前提：合规件自身引用 **2 个不在库的产物**；且引擎**缺件未 fail-closed**（缺陷登记 D-2）

合规件声明（`phases[verify]`）：
`sch_structural` ◀ `k2/hw/sch/k2_sch.kicad_sch`（在库 ✓）·
`netlist_connect` ◀ **`k2/hw/data/k2_sch.errata-2.yaml`**（**不在库**，仅草案 `docs/drafts/j9-wiring-option-a/…` `bdacbf944ca0c796`）·
`bom_consistent` ◀ **`k2/fab/k2_v4_bom.csv`**（**不在库**，`k2/fab/` 目录亦不存在；仅草案 CSV `ce2bb814f31be54b`）。

**引擎实测**（沙箱装合规件后跑 `pipeline verify k2`）：
```
verify/sch_structural: PASS
FileNotFoundError: '/tmp/opencode/p4gateB/k2/hw/data/k2_sch.errata-2.yaml'
```
**D-2（共享引擎缺陷）**：`_shared/eda_core/pipeline/checks.py` 的
`check_netlist_connect`（:74-91 `nets_yaml.read_text`）与 `check_bom_consistent`（:221-234 `open(bom_csv)`）
**均无存在性判据** ⇒ 声明产物缺失时**抛未捕获异常**（`verify` 中止）而非「fail-closed 干净 FAIL」。
（本件**未改** `_shared/eda_core`：共享层 + 非本阶段写权限；仅登记，供监理派单。）

## 4. 推荐安装包与两条路径（**监理 / gate 属主择一**；ENG 不择）

- **路径甲（推荐）**：先批准提升两份草案到声明的库内路径
  （`k2/hw/data/k2_sch.errata-2.yaml` ◀ `bdacbf944ca0c796`；
  `k2/fab/k2_v4_bom.csv` ◀ `ce2bb814f31be54b`），再把合规件 `b74d1f1e883c2ca3`
  装为 `k2/pipeline.yaml` ⇒ 判据 17P/0F + meta-gate PASS + `verify` 可跑通。
  **注**：`errata-2` 属「nc 声明 / F-10」议题 ⇒ 需监理放行（涉真源侧新增）。
- **路径乙**：改合规件的 check 参数指向**现存**产物（`netlist_connect.nets_yaml` → `k2/hw/data/k2_sch.errata-1.yaml`
  `17d540f058631a5e`）；但 `bom_consistent.bom_csv` **无现存替身** ⇒ 仍须先产出 BOM。
  ⇒ 属「门禁参数/判据」变更，须监理裁。
- **两路径共同前置**：`k2/fab/k2_v4_bom.csv` 必须存在（`check_bom_consistent` 直接 `open`）。

## 5. 复跑链

```bash
cd /home/fila/jqdDev_2025/ic_hw
# ① 判据侧（沙箱）：装/抽 pipeline.yaml → 17P/0F vs 16P/1F
G=/tmp/opencode/p4gate; mkdir -p $G/k2/hw/sch; for f in k2/hw/sch/*.kicad_sch; do ln -sf $PWD/$f $G/$f; done
cp k2/docs/drafts/j9-wiring-option-a/pipeline.k2.draft.yaml $G/k2/pipeline.yaml
python3 k2/docs/drafts/p4-j8-density-clearance-v1/adjudicate.draft-v4.py --board <COMPOSITE> \
  --manifest k2/docs/drafts/p4-j8-density-clearance-v1/manifest.k2.v4.yaml --pro k2/hw/k2_v4_8L.l5.kicad_pro \
  --nets k2/hw/data/k2_sch.errata-1.yaml --sch-dir k2/hw/sch --drc-cli AppDir/bin/kicad-cli \
  --drc-work-dir $G/drc --root $G --w8-audit-json <W8v2> --pads-outline-json <PADS> --out $G/verdict.json
# ② 框架 meta-gate / 引擎（沙箱须自带 .git 目录，REPO_ROOT 取 cwd）
(cd $G && python3 -c "import sys;sys.path.insert(0,'/home/fila/jqdDev_2025/ic_hw/_shared');
from eda_core.pipeline import required, engine; print(required.check_all_projects_coverage()); engine.main(['preflight','k2'])")
(cd $G && python3 -c "import sys;sys.path.insert(0,'/home/fila/jqdDev_2025/ic_hw/_shared');
from eda_core.pipeline import engine; engine.main(['verify','k2'])")   # 期望：errata-2 缺失 ⇒ 未捕获 FileNotFoundError
```

## 6. 边界（本笔未动）

仓库板/pro/库/`fp-lib-table` / 冻结件 `d4e81f647be7f980`·`fb07d25ac426ff84` / 真源 yaml / SPEC rev-19..47 /
`criteria/` 两份 / 各判据安装件 / `_shared/eda_core/**` / `k2/pipeline.yaml`（**不存在，未创建**）**均未改**；
未派 WORKER；临时仅 `/tmp/opencode`。结论：**P4 关门剩余四件手续** = ① ⑥+⑦ 落件放行 ② W-8 口径裁定
③ `pipeline.yaml` 安装（含 §3/§4 前提）④ manifest 签认。

—— ENG（ARCHER）· 2026-09-18 · 复合候选 `9682dd026f48c04a`
