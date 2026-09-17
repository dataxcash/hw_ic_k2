# K2 · P4 · `N-03`（pro 根图指针悬挂）**沙箱预演 + 载体核验 + 影响面** · v1 · 2026-09-18

> 缘起：handoff inc45 §5-6（`N-03` 修复排程）与 §6-3（ENlegal 候选化准备）。
> 闭环表 v1.4 §12.1 已锐化 `N-03` = 「pro `top_level_sheets` 指向**不存在的** l4 根图」。本件补三件它缺的：
> ① 修复**沙箱预演**（候选 sha + 单键 diff）；② **根因载体核验**（判「一行修复」够不够）；③ 影响面/排程清单。
> 只读 + 沙箱；**未改仓库 pro/板**。判定归监理。

## 0. 结论（两条）

1. **修复本身可预演、可验证**：候选 pro sha16 = **`d5371257db333541`**（repo `d5e0ca067a7b585e`），**只动 `schematic.top_level_sheets` 一个键**（3 行），板 sha `6ff49da5678c2108` **不变**。
   指针改为 `sch/k2_sch.kicad_sch` + `name=k2_sch` + `uuid=3ed817d0-4e3b-4e02-8b5f-dfcb6e6144b9`（= 根图自身 uuid）。
2. **但「只改 l5 pro」= 板面修补 ⇒ 按 owner 铁律（OWNER-DIRECTIVE-20260917 §一「板面修补单独成立 ⇒ 判未根除」）判 `未闭`**：
   载体侧有三处造成/维持该悬挂（§3），其中 `pcbnew.SaveBoard` 侧车副作用**项目内已有记录**（CO-133）但**未成为生成链的强制不变量**。

## 1. 现状负控 + 校验器自证（避免自造判据）

校验器口径（本件内联，**未落仓库**、不新增检查齿）：对每条 `top_level_sheets` 项验 ① `filename` 相对 **pro 所在目录**可解析；② `uuid` == 该根图文件的**顶层** `uuid`；③ `name` == 文件名干。

| 样本 | `filename` | ① 可解析 | ② uuid 匹配 | ③ name==stem | 判 |
|---|---|---|---|---|---|
| `key_v2/key_v2/key_v2.kicad_pro`（**已知良好**，用于自证校验器） | `sch/key_v2.kicad_sch` | ✅ | ✅ (`86386b49…`) | ✅ | 校验器可信 |
| `k2/hw/k2_v4_8L.l5.kicad_pro`（**受审**，`d5e0ca067a7b585e`） | `k2_v4_8L.l4.kicad_sch` | ❌ 不存在 | ❌ (`00000000…`) | ✅ | **悬挂** |
| `k2/hw/k2_v4_8L.kicad_pro`（非-l5 参考） | `k2_eco22.kicad_sch` | ❌ | ❌ | ✅ | 悬挂（同类） |

⇒ 两处关键旁证：`key_v2` 证明**约定**为「`filename` 含子目录前缀、`uuid` 必须等于根图 uuid」（不是空 uuid）；
`find . -name 'k2_v4_8L.l4.kicad_sch'` = **0 命中**（`0` 个 l4 根图，全仓唯一根图为 `k2/hw/sch/k2_sch.kicad_sch`）。

## 2. 沙箱预演（候选）

- 候选：`/tmp/opencode/inc46/n03/k2_v4_8L.l5.n03.kicad_pro`（`json.dump(indent=2)` 复刻 KiCad 写盘），sha16 = **`d5371257db333541`**。
- diff = **仅 3 行**（`@@ -811,5 +811,5 @@` 的 filename/name/uuid)：

```diff
-        "filename": "k2_v4_8L.l4.kicad_sch",
-        "name": "k2_v4_8L.l4",
-        "uuid": "00000000-0000-0000-0000-000000000000"
+        "filename": "sch/k2_sch.kicad_sch",
+        "name": "k2_sch",
+        "uuid": "3ed817d0-4e3b-4e02-8b5f-dfcb6e6144b9"
```

- 与**共享生成器**的既有正确写法一致：`_shared/eda_core/sch_gate/generate_sch_v5.py:566-578` 写
  `pro["project"]["sch_file_name"] = f"sch/{project}.kicad_sch"`、`top_level_sheets[0] = {filename: f"sch/{project}.kicad_sch", name: project, uuid: root_uuid}`，
  且 `:570 root_uuid = "3ed817d0-4e3b-4e02-8b5f-dfcb6e6144b9"`（硬编码，恰等于 k2 根图 uuid）。
  ⇒ 候选值与载体生成逻辑**同源**，非 ENG 自造。

## 3. 根因载体核验（决定「一行修复」是否成立）—— **不成立**

| # | 载体 | 实测 | 对 l5 pro 的影响 |
|---|---|---|---|
| ① | `_shared/eda_core/sch_gate/generate_sch_v5.py:553-580` `_sync_project_file` | 目标 pro = `dirname(dirname(yaml))/{yaml_stem}.kicad_pro`；k2 的 yaml 为 `boards/k2_sch.yaml` ⇒ 目标 `k2/k2_sch.kicad_pro`；**该文件不存在** ⇒ 打印 `! ... not found — skipping project sync` 并 return | **从不校正** l5 pro（对 l5 pro 是 no-op） |
| ② | **l4 pro 复制继承** | `k2/.co99_dryrun/k2_v4_8L.l4.kicad_pro` 的值同为 `k2_v4_8L.l4.kicad_sch` ⇒ l5 pro 由 l4 pro 复制而来，悬挂项**跨 revision 继承** | 引入并维持悬挂 |
| ③ | `pcbnew.SaveBoard` **侧车副作用**（项目内已记录） | `k2/tools/p3_v57_co133_pdn_construction_apply.py:229-231`：`# 只回写**板**：pcbnew SaveBoard 会顺带重写 .kicad_pro（追加 top_level_sheets 幻影项）⇒ 侧车工程文件（受控工件，CO-80/81/84）不得被施工副作用污染（CO-133 实测并回退）` | 会**再次**写入幻影项 ⇒ 只手工改 pro 会被下一次板写盘覆盖 |

⇒ 修复必须**含载体侧**（否则复发即同缺陷）：
 (a) `_sync_project_file` 的 pro 目标改为**配置驱动/按板名归一**（现按 yaml 文件名推定，k2 下永不命中）；
 (b) 声明并强制「板写盘工具不得污染侧车 pro」的不变量（CO-133 已给出范式 = `shutil.copy(work, board)` 只回写板）；
 (c) 模板族同缺陷需一并处理：`k2/tools/k2_jlc_template.kicad_pro`、`k1/tools/k1_jlc_template.kicad_pro`、`k1/k1_v1.kicad_pro` **均为** `k2_eco22.kicad_sch`（不存在）。
     其中 `k2/tools/k2_jlc_template.kicad_pro` **已在册**（计划 §1.2#7 / §P6「模板仍含 9 条 ignore，须获批」；`206dd0f26e245658`）⇒ 与本项**同批**处理最省手续。
 **注**：`(a)(b)(c)` 均属**生成器/共享层/模板**改动 ⇒ 按红线**须监理放行**（本件只给载体清单，**未动源码**）。

## 4. 根图本身**无缺陷**（把缺陷面收敛到 pro 指针）

`AppDir/bin/kicad-cli sch erc --severity-error k2/hw/sch/k2_sch.kicad_sch` ⇒ **0 条违规**，
报告列出 6 页全解析：`Sheet /` · `/Connectors/` · `/Power Decoupling (ReDriver VCC)/` · `/ReDriver DS320PR1601 & Sideband Strap/` · `/Power (12V DC-in DCDC 5V LDO 3V3)/` · `/MCU & Sideband/`。
⇒ 原理图层级树完整 ⇒ `N-03` 的缺陷**仅是 pro 指针**（`J-2` 侧连通性不由指针决定，见下）。

**相邻发现（具名登记，本件不修）**：根图 `k2_sch.kicad_sch` 的 `instances` 项目名为 **`"ioconvert"`**（非 `k2`/`k2_v4_8L.l5`）。
`generate_sch_v5` 的 `pro["project"]["sch_file_name"]` 亦另写一套 ⇒ 「pro ↔ sch 项目名口径」未归一。是否缺陷归监理；若裁为缺陷，载体同属 ①。

## 5. 影响面与排程

- **sha 影响**：pro `d5e0ca067a7b585e` → `d5371257db333541`；**board `6ff49da5678c2108` 不变**（本项只动 pro）。
- **对已钉测量**：判据要求「测量板 sha16 == 受审板」⇒ 只钉 board；本项**不使**任何 board-钉测量失效。
  但 **T-8「DRC 必取同名 pro」**⇒ 若在 DRC 之前改 pro，须**重跑一次 DRC**（pro 参与规则解码），并把新 pro sha 入账。
- **与待批落件（⑥+⑦）的排程**：落件只写 board（§7 复跑链：L2 placement + lib snapshot），**不写 pro** ⇒ 两项**无 sha 冲突**；
  但 `inc45 §5-6` 要求「排在待批落件之后」，本件**遵从**：给的是候选，不落库。
- **建议顺序**：⑥+⑦ 落件 → （若放行）本法 (a)/(b)/(c) 载体修 + l5 pro 归一 → 重跑 DRC + 五件测量（钉新 board）→ 复算判定器。

## 6. 复跑（每处实测）

```bash
cd /home/fila/jqdDev_2025/ic_hw
# ① 现状负控 + 校验器自证（内联，见 §1 口径）
python3 - <<'PY'
import json,re,pathlib
def ru(p):
    m=re.search(r'\(uuid\s+"([0-9a-f-]+)"',pathlib.Path(p).read_text(encoding='utf-8')[:400]);return m.group(1) if m else None
for pro in ['key_v2/key_v2/key_v2.kicad_pro','k2/hw/k2_v4_8L.l5.kicad_pro']:
    p=pathlib.Path(pro)
    for e in json.loads(p.read_text())['schematic']['top_level_sheets']:
        f=p.parent/e['filename']
        print(pro,e['filename'],'resolves=',f.is_file(),'uuid_ok=',ru(f)==e['uuid'] if f.is_file() else False)
PY
# ② 根图无缺陷（期望 0 违规 + 6 页列出）
./AppDir/bin/kicad-cli sch erc --severity-error --output /tmp/opencode/inc46/erc.rpt k2/hw/sch/k2_sch.kicad_sch
# ③ l4 根图不存在（期望 0 命中）
find . -name 'k2_v4_8L.l4.kicad_sch' -not -path './AppDir/*'
# ④ 载体：生成器 pro 目标推定 / SaveBoard 侧车记录
sed -n '558,580p' _shared/eda_core/sch_gate/generate_sch_v5.py
sed -n '229,231p' k2/tools/p3_v57_co133_pdn_construction_apply.py
```

## 7. 边界

本件**只读 + 沙箱**（候选 pro 仅在 `/tmp/opencode/inc46/n03/`）：未改仓库板/pro/库/`fp-lib-table`/`pm_gate/**`/真源 yaml/SPEC/生成器/模板/`criteria/**`/`_shared/**`；
未创建 `k2/pipeline.yaml`；未派 WORKER；临时仅 `/tmp/opencode`。未新增仓库内判据/脚本（避免新增检查齿）。
—— ENG（ARCHER）· 2026-09-18 · 受审板 `6ff49da5678c2108`
