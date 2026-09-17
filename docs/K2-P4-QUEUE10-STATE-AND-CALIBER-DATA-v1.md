# K2 · P4 · **决策队列第 10 项的现状复测 + 口径候选数据**（D-6 / N-03 / Z2·KO-7 / S-6a·M-12 / W-8 / 闭环表 3 处）· v1 · 2026-09-18

> 缘起：handoff inc60 §6-3-(i)「§5-10 各登记项现状复测 ⇒ 产出『择一即所需数据』」。本会话**无监理放行** ⇒ ENlegal 面；
> **只读复测 + `/tmp` 计算**，仓库零载体改动（仅新增本证据件）。锚：受审板 `6ff49da5678c2108` · 生成器 `d8d15a31061f450f` · l5 pro `d5e0ca067a7b585e` · 模板 pro `206dd0f26e245658`。

## 0. 结论（五条）

1. **`D-6` 实测确认**：生成器自检**声称 8 项、实际登记 6 项**（`S3`/`S7` 全文件 0 命中），运行输出亦印 `(8/8)` 但只列 6 行（`S1,S2,S4,S5,S6,S8`）⇒ **声称≠实际 + 编号跳号**。修法两选（改声称/补实现），见 §1。
2. **`N-03` 实测扩展**：`schematic.sheets` 为 **null**；`top_level_sheets` **指向不存在的文件**，且**存在两个变体**：l5 pro → `k2_v4_8L.l4.kicad_sch`（全仓 0 命中）、**模板 pro 与设计源 pro → `k2_eco22.kicad_sch`（0 命中）**；生成器 `shutil.copy(tmpl,dst)` 逐字复制模板 ⇒ **产物 pro 实测带同款悬挂指针**。⇒ **修必须含模板**（否则每次生成复发）；k1 同族两件亦带。
3. **`Z2·KO-7` 已有规则载体**：l5 pro `board.design_settings.rules.min_copper_edge_clearance = 0.3`，与图纸 `KO-7`（`shape: frame inset edge_copper_min=0.3mm`）/`keepout_geometry.edge_copper_min_mm=0.3` 一致 ⇒ **板侧无需补实体 zone**；请监理确认此口径（若判需实体 zone，则属新增生成段 + 判据，须另行说明，涉 owner ②）。
4. **`S-6a/M-12` 密度口径**：已交**参数化实测数据**（§4）——口径需先定 **4 个参数**（`cell_mm` / `cell_origin` / `metric` / band 定义）。实测复现既有记录（10mm 峰值：`absolute_zero` **5** / `frame_origin` **7**），并给出 5/10/15/20mm × 两原点的**完整曲线**与**峰值格内容**（7 件全为去耦/上拉小件）。**口径陷阱**：本板 `F.CrtYd` 实体仅 **3 件** ⇒「courtyard 口径」**不可全域计算**，其来源须先定。
5. **闭环表 3 处修正＝「主表与 §12.1 自相矛盾」**：闭环表 **§12.1 自纠表已写明** M-02「载体已修」、F-12「两半均就绪」、N-07「伪缺陷/前提不成立」、N-03「悬挂指针」；但 **§1..§11 主表行仍写「未修/未闭」** ⇒ 修正＝把 §12.1 结论**并入主表 ⑤ 列**（N-07 判 **OUT 具名**、并把 N-07 移出「载体未修 30 条」清单）。**ENG 不改该表**（采纳权归监理）。

## 1. `D-6`：生成器自检「声称 8 / 实际 6」（静态 + 动态）

| 检 | 静态命中（`k2/tools/k2_gen_v5.py`） |
|---|---|
| `S1`/`S2`/`S4`/`S5`/`S6`/`S8` | 各 **1**（已登记） |
| **`S3`/`S7`** | **各 0**（未实现、无登记） |

**动态实测**（`K2_OUT_PCB` 定向 `/tmp`）：输出 `k2_gen_v5 自检结果 (8/8):`，随后仅 **6 行**（`S1 焊盘重叠` · `S2 refdes 对齐` · `S4 缺失器件` · `S5 坐标范围` · `S6 网表一致性` · `S8 排针坐标冻结`）。
**声称点**：`:742` 注释「8 项 fail-fast 自检」· `:786` `print("… 自检结果 (8/8):")`。

**修法（供裁）**：**(a)** 把 `:742`/`:786` 改为实际 **6** 项并**连续重编号**（`S1..S6`）——代价：重编号会改动文档/判据中对 `S4/S5/S6/S8` 的既有引用；**(b)** 补实现 `S3`/`S7` 使真有 8 项——代价：新增检查齿（**owner ② 禁**）⇒ **ENG 建议 (a)**，但归监理。

## 2. `N-03`：pro 的 sch 指针（两处悬挂 + sheets 空 + 模板传播）

| 载体 | `schematic.sheets` | `schematic.top_level_sheets` | 目标文件是否存在 |
|---|---|---|---|
| **l5 pro** `k2/hw/k2_v4_8L.l5.kicad_pro` | **null** | `k2_v4_8L.l4.kicad_sch`（name `k2_v4_8L.l4`） | **否**（全仓 `find` 0 命中） |
| **模板** `k2/tools/k2_jlc_template.kicad_pro` | null | **`k2_eco22.kicad_sch`** | **否**（0 命中） |
| **设计源** `k2/hw/k2_v4_8L.kicad_pro` | null | `k2_eco22.kicad_sch` | 否 |
| **产物**（本会话生成）`/tmp/opencode/inc61/g.kicad_pro` | null | `k2_eco22.kicad_sch` | 否（**模板逐字复制**） |
| k1 同族 `k1/k1_v1.kicad_pro` · `k1/tools/k1_jlc_template.kicad_pro` | null | `k2_eco22.kicad_sch` | 否 |

**传播链**：`k2_gen_v5.py:767` `shutil.copy(tmpl, dst)` ⇒ **修模板**是根；l5 pro 是**另一变体**（名字不同但同样悬挂）。
**处置候选（供裁）**：① 置空 `top_level_sheets`（`[]`）＝「板不挂图页」显式化；或 ② 指向**真实存在**的 sch（如 `hw/sch/k2_sch.kicad_sch`）+ 填 `sheets`；③ 连同 k1 同族一并修。**判定口径**（`schematic_parity` 是否在岗）属 gate/监理。

## 3. `Z2·KO-7`：边铜约束的载体（规则 vs 实体 zone）

| 载体 | 值 |
|---|---|
| l5 pro `board.design_settings.rules.min_copper_edge_clearance` | **0.3** |
| 图纸 `keepouts[KO-7]` | `shape: "frame inset edge_copper_min=0.3mm"`, `count: 4`, `tracks/vias/copper_pour: blocked(<0.30mm)`, `pads/footprints: allowed` |
| 图纸 `keepout_geometry` | `edge_copper_min_mm: 0.3`, `edge_inset_rect_mm: [23.3, 33.3, 142.7, 78.7]` |
| 板实体 zone | **无 KO-7 实体 zone**（板 zone 总数 18 = 8 keepout〔4×ESC F.Cu + 4×孔全层〕+ 10 有网铜区） |

⇒ **KO-7 现有载体＝设计规则**（`min_copper_edge_clearance=0.3`），语义与图纸 KO-7 一致 ⇒ **建议：不补实体 zone**（口径声明式）。
**待监理确认**；若判需实体 zone，属**新增生成段 + 判据**（owner ②）。

## 4. `S-6a / M-12` 密度口径：参数化候选数据

**口径 4 参数**：`cell_mm`（格边长）· `cell_origin`（绝对零点 或 框原点 (23,33)）· `metric`（器件数 / 覆盖面积比）· band 定义（横向带如何切）。

**实测 4.1 —— `max_fp_per_cell` 曲线（59 件 footprint）**：

| `cell_mm` | origin (0,0) 峰值 / 有器件格数 | origin (23,33) 峰值 / 有器件格数 |
|---|---|---|
| 5 | 5 / 38 | 4 / 42 |
| **10** | **5** / 27 | **7** / 25 |
| 15 | 7 / 18 | 10 / 16 |
| 20 | 9 / 14 | 13 / 12 |

⇒ 复现既有记录（10mm：`absolute_zero`=5、`frame_origin`=7 ✓）。**峰值格内容**（10mm）：`frame_origin` 7 件 = `{R44,R43,C81,R35,C80,C79,C83}`（**全为去耦/上拉小件**，非大件堆叠）；`absolute_zero` 5 件 = `{C81,C79,R42,C82,C83}`。
⇒ 若阈值取「10mm/框原点 ≤7」：当前 **恰好 =7（零余量）**；取「≤8」有余量 1。**阈值定多少属判据应然 ⇒ owner/监理**。

**实测 4.2 —— 横向带占用（ENG 自定口径：设计框 `y[33,79]` 3 等分；覆盖 = Σ(器件 bbox∩带)/带面积）**：

| 口径 | 带 1 / 带 2 / 带 3（%） | 峰值 |
|---|---|---|
| **pad bbox** | 11.732 / **20.146** / 3.056 | **20.146%** |
| courtyard bbox | 5.496 / 13.019 / 0.966 | 13.019%（**仅 3 件有 `F.CrtYd`** ⇒ 不可作全域依据） |

**口径陷阱（须监理/ENG 先对齐）**：本板 `F.CrtYd` **仅 3 件** ⇒「courtyard 口径」需先定**courtyard 来源**（KiCad courtyard 实体 / 求解器侧 AABB / 库件 courtyard）；既有记录「courtyard 口径中带 27.84%」与本表 13.019% **不同口径**，不可直接比较。另本表「3 等分带」定义与既有「横带 7.586%」亦非同一带切法 ⇒ **口径必须先定，再谈阈值**。

## 5. `W-8`「放置帧归一」：草案 + 三案正负控（供裁采纳/驳回）

| 件 | sha16 |
|---|---|
| `k2/docs/drafts/p4-j7b-w8-pose-normalized-v1/w8_audit.draft-v2.py` | **`34b83cff5fe8ade7`**（＝verdict 链 16P/1F 那一档） |
| 同目录 `README.md` | `45c2e411d9a8ae60` |
| 现安装件 `k2/tools/k2_w8_footprint_audit_v1.py` | `75404d706413d546`（**未动**） |

**机理**：v1 直比**文件内存储值**（`GetFPRelativePosition`/`GetOrientationDegrees`）⇒ 对「有旋转」（板存绝对 pad 朝向 / 库存局部）与「背面镜像」两类**约定差异误报**；v2 = 把库件**按板位姿放置**（位置/朝向/`Flip` 背面）后在**放置帧**内取电气签名。

| 案 | v1 | **v2 草案** | 说明 |
|---|---|---|---|
| ① 基线（仓库板 + 仓库库） | `31+2`（33） | **`31+2`（33，逐件相同）** | **不放松判据** |
| ② ⑦ 候选（按板重建库） | `8+0`（8，全为约定） | **`0+0`** | 归一后 J-7b ⇒ PASS |
| ③ 合成负控（`C73` pad1 宽 +0.05mm） | `9+0`（8 伪 + 1 真） | **`1+0`（恰 `['C73']`）** | 真差异仍被抓 |

**待裁 3 点**：**(1)** 采纳/驳回（属「判据语义澄清」＝监理职权）；**(2)** 若采纳 ⇒ gate 属主侧**版本 bump 安装**到 `tools/`（或 `criteria/` 侧消费口径）+ 登记 sha 与锚 rev；**(3)** 若驳回 ⇒ `lib_electrical_level` 的 8 件差异须另定口径（否则该维恒 FAIL，但**已证明 8 件非 land pattern 问题**）。

## 6. 闭环表「3 处修正」：主表 vs §12.1 自纠表（实测复核）

| 条 | §1..§11 主表现写 | 本会话只读实测 | §12.1 自纠表已写 | 修正动作（监理采纳） |
|---|---|---|---|---|
| **M-02** | `README`/`01-architecture`「未修（仍写 dual DS160PR810）」 | `README.md`：`DS160PR810`=**0** · `DS320PR1601`=4 · `dual\|双颗`=**0**；`01-architecture.md`：0 / 1 / 0 ⇒ **载体已修** | 同（「表内陈旧：载体已修」） | 主表 ⑤ 改「**载体已修**（待判据）」 |
| **F-12** | 「**部分修**：库表侧闭；7 个未标注 refdes 未修」 | `k2/hw/fp-lib-table` 存在 `d731638859be9a08` · `ForgeOS` 1 条 · 库 **20** 件（DRC 侧 `lib_footprint_issues` 6→0）；「7 个 refdes」**前提不成立**（见 N-07） | 「**两半均就绪**」 | 主表 ⑤ 改「**载体已修**」 |
| **N-07** | 「原理图仍有 7 个未标注 refdes…**未修**」 | 排除 `(lib_symbols …)` 子树后**实例未标注 = 0**（55 实例全标注）；31 个 `?` 全在 `lib_symbols`；「7」=7 个**前缀**；netlist `?`=**0** / 705 ref 条目 | 「**现象不成立＝伪缺陷** ⇒ 建议判 **OUT（具名：前提实测不成立）**」 | 主表 ⑤ 判 **OUT（具名）**，并把 N-07 移出 §0「载体未修 30 条」清单 |

**另**：`N-03` 的悬挂指针在 §12.1 亦已记（与 §2 实测一致）；主表 ⑤ 仍「未闭」⇒ 是否改判取决于 §2 的处置裁定。
⇒ 结构性问题：**闭环表内部（主表 vs §12.1）自相矛盾** ⇒ 采纳后须**同版更新**（v1.4/v1.5），避免两处并存。

## 7. 汇总：每项「监理择一即所需数据」

| 队列项 | 现状（本件实测） | 监理需给的**一句** | 之后 ENG 可一次做 |
|---|---|---|---|
| §5-10 `D-6` | 声称 8 / 实际 6（S3/S7 缺） | 修法 (a) 改声称+重编号 / (b) 补实现 | 一行改动 + 文档同步 |
| §5-10 `N-03` | 两处悬挂指针 + sheets null；模板是传播源 | 置空 `[]` / 指向真实 sch / 是否连 k1 | 模板 + 源 pro + l5 pro（+k1） |
| §5-3 `Z2·KO-7` | 规则 `min_copper_edge_clearance=0.3` 已存在 | 确认「规则承载、不补实体 zone」 | 图纸口径登记 |
| §5-10 `S-6a/M-12` | 参数化曲线（10mm：5/7）+ courtyard 仅 3 件 | 定 4 参数（`cell_mm`/`origin`/`metric`/band）+ 阈值 | 判据阈值实现 + 复算 |
| §5-10 `W-8` | 草案 `34b83cff5fe8ade7` + 三案正负控 | 采纳/驳回（＋安装归属） | 版本 bump 安装 / 另定口径 |
| §5-10 闭环表 3 处 | 主表 vs §12.1 自相矛盾 | 采纳 3 处修正 | 同版更新主表 ⑤ |

## 8. 复跑

```bash
cd /home/fila/jqdDev_2025/ic_hw
# D-6 静态+动态：见 §1（grep "\[S$n \|S$n\]" + 跑生成器数行）
# N-03：python3 -c "import json;d=json.load(open('k2/hw/k2_v4_8L.l5.kicad_pro'));print(d['schematic'])"
#       + find k2 -name 'k2_v4_8L.l4.kicad_sch' -o -name 'k2_eco22*'
# KO-7：python3 -c "import json;print(json.load(open('k2/hw/k2_v4_8L.l5.kicad_pro'))['board']['design_settings']['rules']['min_copper_edge_clearance'])"
# 密度：见 §4 表（本件 §4 的步进脚本：cell×origin 网格计数 + pad bbox 带覆盖）
# W-8：三案命令见 k2/docs/drafts/p4-j7b-w8-pose-normalized-v1/README.md §2
# 闭环表 3 处：grep -n 'DS160PR810' k2/README.md k2/docs/01-architecture.md ; ls k2/hw/fp-lib-table
python3 -c "
import json;d=json.load(open('k2/hw/k2_v4_8L.l5.kicad_pro'))
print('l5 pro sheets:',json.dumps(d['schematic'].get('sheets')),'| top_level:',json.dumps(d['schematic'].get('top_level_sheets')))
print('min_copper_edge_clearance =',d['board']['design_settings']['rules']['min_copper_edge_clearance'])"
```

## 9. 边界

本件**只读复测 + `/tmp` 计算**：未改生成器/板/pro/库/模板/SPEC/真源/图纸/`criteria/**`/`_shared/**`/闭环表；
未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode`；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 受审板 `6ff49da5678c2108` · 生成器 `d8d15a31061f450f` · l5 pro `d5e0ca067a7b585e`
