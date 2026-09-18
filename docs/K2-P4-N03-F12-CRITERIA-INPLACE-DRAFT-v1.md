# K2 · P4 · **`N-03` / `F-12` 判据在岗口径草案**（含 `schematic_parity` 激活实测：59–226 条）· v1 · 2026-09-18

> 缘起：handoff inc67 §6-3-(t)「`N-03`/`F-12` **判据在岗口径草案**（§5-10 末项；`schematic_parity` 是否在岗、以何口径判定，纯文档/草案）」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读 + `/tmp` DRC 复算**，仓库零载体改动（仅新增本证据件）。
> 锚：判据安装件 `criteria/manifest.k2.yaml` **`7ce08757eff25557`**（**9 维、不含 `fp_lib_table_present` / `lib_electrical_level`**，`not_countersigned: true`）· 判据草案 v2 `0da2fb9d173fac2d`（18 检查项，含 `fp_lib_table_present`）· 判据草案 v3 `manifest.k2.v3.yaml`（18 维，含 `lib_electrical_level: {consume: w8_audit_json}`）· `criteria/adjudicate.py` **`897e8bfde60e2cfe`** · l5 pro **`d5e0ca067a7b585e`** · 受审板 **`6ff49da5678c2108`**。
> 装置（`/tmp`，易失）：`/tmp/opencode/inc63/schparity/{A,Ap,B,Bp,D,F,G}.json`（五案矩阵，kicad-cli 10.0.5 `pcb drc --schematic-parity`）。
> **归属**：判据在岗口径＝**监理**；ENG 只出实测与候选口径，**不新增检查齿**（owner ②）。

## 0. 结论（六条）

1. **「判据在岗」现状总账**：安装件 `criteria/manifest.k2.yaml` 为 **9 维**且 `not_countersigned: true`；`fp_lib_table_present` 与 `lib_electrical_level` **只在草案里**（v2/v3，18 维）⇒ 两条对应维度的「在岗」＝**待安装 + 待签认**，不是「已实现即可用」。
2. **`F-12` 口径可一次说清（两半）**：① 库表半边 ⇒ 判据 `fp_lib_table_present`（草案已实现：`fp-lib-table exists`；四案 real→PASS / 缺失或陈旧→FAIL）；② refdes 半边 ⇒ **伪缺陷**（`N-07`，判 OUT 具名，见 inc66 闭环表 diff 草案）。⇒ `F-12` 的「载体已修 + 防复发判据在岗」**只差安装**该维（＋⑧ 号签认）。
3. **`N-03` 口径（本轮新实测，决定性）**：KiCad DRC JSON 有独立数组 **`schematic_parity`**；现状 = **0 条且是「空跑」**（KiCad 打印「无法获取用于校验测试的原理图网表。请先将原理图批注完整…」）。**修 `top_level_sheets` 并不能让它在岗**（见 §3 矩阵）。
4. **激活条件（实测钉死）**：`--schematic-parity` 仅在**根 sch 与 `.kicad_pro` 同目录且同名**（`<proj>.kicad_sch`）时才运行；此时立即给出 **59 条**（子页仅 `sch/`、未解析）/ **226 条**（子页齐全、同目录）一致性问题（示例：`net_conflict`「焊盘网络 `PCIE_REFCLK0_P` 与原理图 `/Connectors/PCIE_REFCLK0_P` 指定的网络不匹配」）。
5. **DRC 规则侧不受影响**：五案 `violations` **恒为 75**（`missing_courtyard 40 / lib_footprint_mismatch 29 / lib_footprint_issues 6`）⇒ 挂图与否只改 `schematic_parity` 这一**独立数组**，不改常规 DRC 判项。
6. **⇒ `N-03` 处置须显式三选一（监理）**：**(i) 入判**：做工程布局变更（根 sch 与板同目录同名）使 `schematic_parity` 真在岗，并**同批处置**首次暴露的 59–226 条（这是**新维度 + 新缺陷面**，量大）；**(ii) 规则承载/豁免**：只消除悬挂指针（inc66 (q) 案①/②），并**具名登记**「`schematic_parity` 不在岗」；**(iii) OUT 具名**：判 N-03 不阻塞可制造性。**新增判据覆盖 `.kicad_pro` 指针**＝新增检查齿 ⇒ 与 owner ② 冲突，须监理明确。

## 1. 判据在岗总账（安装件 vs 草案）

| 维度 | 安装件 `criteria/manifest.k2.yaml`（9 维） | 草案 v2/v3（18 维） | 与本件两条的关系 |
|---|---|---|---|
| `fp_lib_table_present` | **无** | 有（`fp-lib-table exists`） | **`F-12` 库表半边** |
| `lib_electrical_level` | **无** | 有（`consume: w8_audit_json`；板 sha 一致 + 差异 0） | （J-7 电气级，见 inc67 W-8 件）|
| `schematic_parity` | **无（且非判据）** | **无** | **`N-03`**：KiCad DRC 的独立数组，**当前无任何判据消费它** |
| 其余 | 9 维（`zone_filled` … `verdict_schema`） | +`drc_errors`/`unconnected_zero`/`keepout_active`/`density_and_spacing` 等 | — |

## 2. `F-12` 判据口径（建议表述）

| 半边 | 载体 | 判据 | 口径 | 现状 |
|---|---|---|---|---|
| 库表 | `k2/hw/fp-lib-table` `d731638859be9a08` | `fp_lib_table_present` | `fp-lib-table exists`（板工程目录内）；（四案：**real→PASS** · 缺失/陈旧→FAIL） | **载体已修**、判据**待安装** |
| refdes | `k2/hw/sch/*` | （无独立判据） | `N-07` 伪缺陷（实例未标注 = 0；31 个 `?` 全在 `lib_symbols`；netlist `?` = 0/705） | **OUT 具名**（待 inc66 (p) 采纳） |

## 3. `N-03`：`schematic_parity` 激活矩阵（五案实测；kicad-cli 10.0.5）

| 案 | pro 的 `top_level_sheets` | 根 sch 位置 / 命名 | 子页位置 | `schematic_parity` | `violations` | 日志/证据 |
|---|---|---|---|---|---|---|
| **A** | 原值（`k2_v4_8L.l4.kicad_sch`，**不存在**） | — | `sch/` | **0（空跑）** | 75 | 打印「无法获取原理图网表」· `A.json 460cbe2b09fdf74b` |
| **Ap** | 同 A ＋ `--schematic-parity` | — | `sch/` | **0（同上）** | 75 | `Ap.json 98982252f968a56e` |
| **B** | inc66 (q) **案②**（`../hw/sch/k2_sch.kicad_sch`） | `sch/`，名 `k2_sch` | `sch/` | **0（仍空跑）** | 75 | `B.json 4606304d3bb38b18` |
| **F** | `sch/k2_v4_8L.l5.kicad_sch` | `sch/`，**同名**但与 pro **不同目录** | `sch/` | **0（仍空跑）** | 75 | `F.json 98d7bf66ef7260d7` |
| **G** | `k2_v4_8L.l5.kicad_sch` | **pro 同目录** `hw/`，**同名** | 仅 `sch/`（子页未解析） | **59** | 75 | `G.json 32dc8394464659d3` |
| **D** | `k2_v4_8L.l5.kicad_sch` | **pro 同目录** `hw/`，**同名** | **同目录**（子页齐全） | **226** | 75 | `D.json 707132d319c07774` |

**读法**：①**指针值本身**（含 inc66 案②）**不足以**让 parity 在岗；②**同名 + 同目录**是必要条件（F vs G 对照）；③一旦在岗，一致性问题是**量大且此前从未跑过**的面（59→226 随子页解析度上升）；④常规 DRC 规则违规**不变**（75），说明这是**新增维度**而非既有维度恶化。

**示例条目（D 案）**：`type=net_conflict`，`description=焊盘网络 (PCIE_REFCLK0_P) 与原理图 (/Connectors/PCIE_REFCLK0_P) 指定的网络不匹配`（⚠️ 含「网名路径差异」一类，属**口径**问题：KiCad 全局网名 vs 分层路径名）。

## 4. 候选口径（三选一；ENG 不择一）

| 候选 | 内容 | 代价/依赖 | 触 owner ②? |
|---|---|---|---|
| **(i) 入判** | 把根 sch 变为 `<proj>.kicad_sch` 且与 pro 同目录 ⇒ `schematic_parity` 真在岗；同时**同批处置 59–226 条**（分类：网名路径差异 / 真实连接差异） | 工程布局变更（**须监理/owner 同意**）+ 大额新缺陷面 + 判据侧需定义阈值（`schematic_parity == 0`?） | 定义阈值/维度 ⇒ **是**（须监理明示） |
| **(ii) 规则承载 + 具名登记** | 采 inc66 (q) 案①/② 消除悬挂指针；**具名登记**「`schematic_parity` 不在岗（KiCad 需同名同目录）」+ 理由 | 最小改动；但 N-03 的「防复发判据在岗」仍为**否** ⇒ 只能记「载体已修、判据缺岗（具名）」 | 否（登记非新齿） |
| **(iii) OUT 具名** | 判 N-03 不阻塞可制造性（P4 交付面），并注明「板↔图对比维度整体缺岗」 | 需监理判「不阻塞」；风险：P5 交付面之外可能仍有价值 | 否（判定归监理） |

## 5. 复跑（仓库零写入；需先建 `/tmp` 镜像 k2/hw + k2/hw/sch）

```bash
cd /tmp/opencode/inc63/schparity/k2/hw
SHARUN=/home/fila/jqdDev_2025/ic_hw/AppDir/sharun
$SHARUN kicad-cli pcb drc --format json --severity-all [--schematic-parity] -o /tmp/out.json k2_v4_8L.l5.kicad_pcb
python3 -c "import json;d=json.load(open('/tmp/out.json'));print('parity',len(d['schematic_parity']),'violations',len(d['violations']))"
# 期望：原 pro/案②/同名异目录 ⇒ parity 0（空跑）；同名同目录(+子页) ⇒ 59 / 226；violations 恒 75
```

## 6. 边界

本件**只读 + `/tmp` DRC 复算**：未改判据/SPEC/生成器/板/pro/真源/图纸/模板/库/`fp-lib-table`/`pm_gate/**`/`criteria/**`/`_shared/**`/闭环表；
**未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`**；未落件；未出 Gerber；未派 WORKER；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 受审板 `6ff49da5678c2108` · 判据安装件 `7ce08757eff25557`
