# K2 · P4 · **`schematic_parity` 59/226 分类草案**（226 条逐条归类：口径差异 / 已登记缺陷投影 / 机械孔）· v1 · 2026-09-18

> 缘起：handoff inc68 §6-3-(v)「把 D/G 两案的条目按 `net_conflict` 的『网名路径差异 vs 真实连接差异』分类，给出可裁的三档处置，纯 `/tmp` 复算」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读 + `/tmp` DRC 复算**，仓库零载体改动（仅新增本证据件）。
> 锚：受审板 `6ff49da5678c2108` · D 案 `D.json` **`707132d319c07774`**（完整图树、226 条）· G 案 `G.json` **`32dc8394464659d3`**（仅根页、59 条）· 既有判据归一约定 `_shared/eda_core/pipeline/checks.py:89`（`n["name"].split("/")[-1]`）。
> 装置（`/tmp`，易失）：`/tmp/opencode/inc63/parity_classify.py`（分类器）· `/tmp/opencode/inc63/schparity/{D,G}.json`。
> **归属**：口径归类与是否入判＝**监理**；ENG 只出分类与证据，**不新增检查齿**（owner ②）。

## 0. 结论（五条）

1. **D 案 226 条可逐条归入五类，且 0 条需新登记**：口径差异 **85**（56 网名层级前缀 ＋ 29 封装库昵称前缀）· 已登记缺陷投影 **137**（J3/J4 双向 34+34+34+34 ＝ 136 ＋ `C89` 1）· 机械孔 **4**（`H1..H4`）。
2. **口径差异一类有既有先例**：板侧 `PCIE_REFCLK0_P` vs 图侧 `/Connectors/PCIE_REFCLK0_P`；**既有判据 `netlist_connect` 正是用 `split("/")[-1]` 归一**（`checks.py:89`）⇒ 本 56 条属**同一口径族**，建议按同一归一处理（不计真实缺陷）。封装类 29 条同理（板裸名 vs 符号 `Resistor_SMD:` 前缀）。
3. **137 条引脚级差异集中在 `J3`/`J4`（双向各 34）＋ `C89` 1**：与 **U-03**（J3/J4 库↔板 pad 名集 `A1..A19/B1..B19` vs `1..38`）及 **⑤ `C89/A`** 同族（**须逐条比对确认**，本件只出分布与样例）⇒ 属**已登记缺陷在 parity 维度的投影**，不是新缺陷类。
4. **`extra_footprint` 4 条 = `H1..H4`**（板有图无的机械固定孔）⇒ 结构性/机械，非电气连接缺陷（豁免候选）。
5. **G 案 59 条不可用于计数**：全部为 `extra_footprint`（子页未解析 ⇒ 板侧 59 件全部「多余」）⇒ **退化读数**；只有 D 案（完整图树）的口径可用。**全部 226 条 severity 均为 `warning`**（若入判须定义 severity 门槛）。

## 1. 分类表（D 案 226 条）

| 类 | 条数 | 样例 | 归因 / 对应登记项 | 建议档 |
|---|---|---|---|---|
| `net_path_prefix_only` | **56** | `焊盘网络 (PCIE_REFCLK0_P) 与原理图 (/Connectors/PCIE_REFCLK0_P) 指定的网络不匹配` | 层级路径前缀差异；**既有归一先例** `checks.py:89` `split("/")[-1]` | **档1 口径** |
| `fp_lib_prefix` | **29** | `R_0603_1608Metric 与符号 (Resistor_SMD:R_0603_1608Metric) 指定的封装不匹配` | 库昵称前缀（板裸名 vs 符号带库前缀）；与 DRC `lib_footprint_mismatch` **同数（29）**，ref 集未逐条比对 | **档1 口径** |
| `pin_missing_in_sch` | **69** | `在原理图中未找到对应的引脚`（ref 分布：`J3` 34 · `J4` 34 · `C89` 1） | **U-03**（J3/J4 pad 名集）＋ **⑤ `C89/A`** | **档2 已登记投影** |
| `pad_missing_on_board` | **68** | `未找到原理图中引脚 23 (/Connectors/PCIE_REFCLK0_N) 对应的焊盘`（ref 分布：`J3` 34 · `J4` 34） | **U-03 反向** | **档2 已登记投影** |
| `extra_footprint` | **4** | `封装 H4` / `H2` / `H1` / `H3` | 机械固定孔（板有图无） | **档3 豁免候选** |
| **合计** | **226** | — | **0 条需新登记** | — |

**三档处置建议（供裁）**：
- **档1（85 条）**：按既有归一简化口径处理后**不计真实缺陷**（网名取末段、封装名去库前缀）；若监理认为须逐条留痕，可登记为「口径差异」并给归一规则。
- **档2（137 条）**：**不新开缺陷条目**，随 U-03（⑦ 库重建）与 ⑤（L1 裁定）**同批收敛**；收敛后 parity 数应显著下降（可作回归指标）。
- **档3（4 条）**：机械孔，建议**具名豁免**（板侧 H1–H4 属结构件，图侧不建模）；若监理要求图侧建件，则属图纸侧动作、另批。

## 2. G 案（59 条）为何不可用

`G` 案只挂根页（子页未解析）⇒ 根页无器件 ⇒ **板侧 59 件全部报 `extra_footprint`**（含 `C73..R45`、`J2/J3/J4/J6/J9/J11/J12/J13`、`U1/U2/U4/U5/U6`、`H1..H4`）。
⇒ 该读数是**结构不完整导致的退化**，不代表 59 个真实问题；**任何以 G 案计数为「59 个缺陷」的推断都不成立**。

## 3. 与既有维度的关系（避免重复计数）

| parity 类 | 既有维度 | 关系 |
|---|---|---|
| `fp_lib_prefix` 29 | DRC `lib_footprint_mismatch` 29 | **同数**；是否同源须逐条比对（本件不下结论）；两者若同源，应在同一档（库侧/⑦）处理 |
| `pin_missing_in_sch` / `pad_missing_on_board` 137 | `pin_map_complete` / `net_declared_realized` / U-03 / ⑤ | 引脚级；与既有引脚维**同族**，须避免同一缺陷被两维重复计入 |
| `net_path_prefix_only` 56 | `netlist_connect`（`split("/")[-1]` 归一） | **口径已解决** ⇒ parity 侧若入判应复用同一归一 |

## 4. 复跑（仓库零写入；需先建 `/tmp` 镜像见 inc68 (t) 件 §5）

```bash
cd /home/fila/jqdDev_2025/ic_hw
python3 /tmp/opencode/inc63/parity_classify.py            # 期望：D=226（56/29/69/68/4）· G=59（全 extra_footprint）
python3 - <<'PY'
import json, collections
d=json.load(open('/tmp/opencode/inc63/schparity/D.json'))
print(collections.Counter(e['type'] for e in d['schematic_parity']))
print(collections.Counter(e['severity'] for e in d['schematic_parity']))
PY
```

## 5. 边界

本件**只读 + `/tmp` DRC 复算**：未改判据/SPEC/生成器/板/pro/真源/图纸/模板/库/`fp-lib-table`/`pm_gate/**`/`criteria/**`/`_shared/**`/闭环表；
**未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`**；未落件；未出 Gerber；未派 WORKER；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 受审板 `6ff49da5678c2108` · D `707132d319c07774` · G `32dc8394464659d3`
