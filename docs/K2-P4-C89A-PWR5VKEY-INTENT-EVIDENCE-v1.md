# K2 · P4 · `⑤ C89/A`／`PWR_5V_KEY` **意图证据包 + 两选项改动面**（含「裁定属 L1」判定）· v1 · 2026-09-18

> 缘起：handoff inc58 §6-3-(f)「为 §5-A5（`C89/A`）与 §5-A8（甲/乙）预置『裁定后一次可做』的补丁草稿骨架」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读 + `/tmp` 语义验证**，仓库零载体改动（仅新增本证据件）。
> 锚：真源 `dd794c54f7ce7417`（errata-1 `17d540f058631a5e`）· SPEC rev-47 `9ba09cbc148d6836` · 受审板 `6ff49da5678c2108` · l4 Gerber（L5/jlc_package）。

## 0. 结论（五条；第 3 条是**放行判断**级）

1. **决定性证据：`PWR_5V_KEY` 是 **K1 的网**，在 K2 只残留一个节点。**
   K1 真源 `k1/boards/k1_sch.yaml`：`PWR_5V_KEY = ["U8/VOUT","U12/IN","C89/A","U10/VIN","U10/EN"]`（5 节点、真实 5V 轨）；
   K2 真源 `k2/hw/data/k2_sch.yaml`：`PWR_5V_KEY = ["C89/A"]` —— **同一个 ref `C89`、同一个 pin `A`**，K2 不存在的其余 4 节点全部消失。
   ⇒ K2 的该网是 **K1 跨项目残留**（连同 refdes `C89` 一起带过来），不是 K2 的电气需求。
2. **K2 侧无 5V 域、无 key 接口、且该网在原理图中从未声明**：K2 电源页（`power_12v_dc_in_dcdc_5v_ldo_3v3.kicad_sch`）的网标仅 `12V_IN / GND / P3V3 / P3V3_AUX / MCU_VDD / SW_U2 / FB_U2`（U2 = `DCDC_12V_3V3`）；
   全仓 `grep PWR_5V_KEY` 在 `k2/hw/sch/**` **0 命中**；`C89` 为 4.7uF（`C_4R7`）输出侧电容，**pin A 悬空、pin B = GND**。
3. **【放行判断】该裁定属 L1（电源域/网范围口径）⇒ 需 owner**：
   本项**不是**纯数据修补 —— `PWR_5V_KEY` 同时被 **SPEC `layer_plan.low_speed_nets.nets`（rev-7…rev-47 **全部 rev** 均含）**、**l4 交付 Gerber**（`F_Cu`：`%TO.P,C89,1*% / %TO.N,PWR_5V_KEY*%`）、
   **受审板 `.kicad_pro` `netclass_assignments`（`PWR_5V_KEY → ["POWER"]`）** 承载；且容器内**既有 CO 件已具名登记**：
   `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_joint_assignment_boundary_v1_*.md` 「CO-90 F3」写：
   「…**属 SPEC `layer_plan.low_speed_nets`、68 网范围外** ⇒ 该 pad 不在分母亦无决策…『哪些网计入 PDN 覆盖』属**网范围/电源域口径 ⇒ 待 PM/owner**，不得由 L2 静默重定义」。
   ⇒ **⑤ 与既有登记一致地指向 owner**；ENG 本件只出证据与两选项改动面，**不择一**。
4. **两选项已量化，且 `①` 可让 `乙` 链一次转绿（`/tmp` 实测）**：
   - **① 数据/口径侧**（删该网 + `C89/A` 声明 NC）⇒ **三检查 3/3 PASS**（`sch_structural` / `bom_consistent` / `netlist_connect`：`全部 100 个网连接完整 + 反向断言 0 非声明悬空`）。
   - **② 连接/拓扑侧**（把 `C89/A` 接到 K2 的某条轨，如 `P3V3`）⇒ **仅动真源仍 FAIL 2 处**（`网 'P3V3': 节点 C89/A 未连接` + `非声明悬空: C89/A_1`）⇒ 必须**同时改原理图并布线（现 0 走线）** ⇒ 触及拓扑/信号流向。
5. **副作用提醒（供 owner 一次裁清）**：① 之下 `C89` 成为**单端悬空电容**（电气无效）；故 ① 有三个子档：**①a** 保留 C89（DNP/悬空）、**①b** 连 C89 到 K2 既有轨（＝②）、**①c** **删 C89**（BOM/板同步）。
   同源提醒：K2 的 `C89` 与网名**同批来自 K1**，若判「K1 携带物」，①c 可能才是正解；此属 owner 域。

## 1. 证据：五源对照（`C89/A`／`PWR_5V_KEY`）

| 载体 | `PWR_5V_KEY` | `C89/A` | 说明 |
|---|---|---|---|
| **K1 真源** `k1/boards/k1_sch.yaml` | 5 节点（含 `U8/VOUT` `U10/VIN/EN` `U12/IN`） | 在网内 | **K1 真实 5V 轨**（名字来源） |
| **K2 真源** `k2_sch.yaml` / `errata-1` | **1 节点**：`["C89/A"]` | 该网唯一节点 | 残留 |
| **K2 原理图** `hw/sch/*.kicad_sch` | **0 命中** | pin A 无 label/wire（pin B = GND） | 从未声明该网 |
| **K2 SPEC** rev-7…rev-47 | `layer_plan.low_speed_nets.nets` 含之 | — | **全部 rev 一致** |
| **K2 受审板 l5** | 1 处（`C89.1` pad net） | pad 有 net 名 | **0 走线**（`segment` 0） |
| **K2 l4 Gerber** `…l4-F_Cu.gbr` | `%TO.N,PWR_5V_KEY*%` | `%TO.P,C89,1*%` | 交付 Gerber 已冻结该名 |
| **K2 `.kicad_pro`** | `netclass_assignments: PWR_5V_KEY → ["POWER"]` | — | POWER 类 |
| **K2 电源页网标** | 无 | 悬空 | 页内仅 `12V_IN/GND/P3V3/P3V3_AUX/MCU_VDD/SW_U2/FB_U2` |

## 2. 两选项改动面清单（裁定后**一次可做**）

**① 数据/口径侧**（推荐候选；`/tmp` 已验 3/3 PASS）
| # | 件 | 动作 | 归属 |
|---|---|---|---|
| 1 | 真源 `k2_sch.errata-*.yaml` | 删 `nets.PWR_5V_KEY`；`C89/A` 入 `nc`（`sheets[].placements[].nc` 或 top-level，D-7 ①② 皆认） | ENG（须放行） |
| 2 | SPEC（bump） | `layer_plan.low_speed_nets.nets` 删 `PWR_5V_KEY`（否则 SPEC↔真源漂移，且属 Z4 权威源议题） | 放行范围 |
| 3 | 受审板 `.kicad_pro` | `netclass_assignments` 删 `PWR_5V_KEY`（POWER 类） | 板侧（落件手续） |
| 4 | CO-90 F3 登记 | 更新该口径登记（pad 不再存在 ⇒ 分母问题消失） | 监理/PM |
| 5 | `C89` 自身 | **①a** 保留（悬空/DNP）／**①b** 接到 K2 既有轨（＝②）／**①c** 删 C89 + BOM + 板 | **owner** |

**② 连接/拓扑侧**（若判 `C89` 本应在 K2 轨上）
| # | 件 | 动作 | 归属 |
|---|---|---|---|
| 1 | 原理图（电源页） | 在 C89/A 处补 `label` + `wire` 至目标轨（须先定轨：K2 无 5V ⇒ 候选 `P3V3` / `P3V3_AUX`） | **L1/owner** |
| 2 | 真源 | 该节点并入目标轨网（`P3V3` 47→48 节点等） | ENG（须放行） |
| 3 | 受审板 | **布线该节点（现 0 走线）** + 重填/重算 | 板侧 |
| 4 | SPEC / netclass | `low_speed_nets` 与 `netclass_assignments` 同步 | 放行范围 |

## 3. `/tmp` 语义验证（真 check 实现 + 真 sch；装置＝inc58 全修共享树）

| 案 | 真源改动 | `sch_structural` | `bom_consistent` | `netlist_connect` |
|---|---|---|---|---|
| **基线 `乙`**（errata-1 原样） | — | PASS | PASS | **FAIL 2 处**（`PWR_5V_KEY` 缺网 + `C89/A_1` 非声明悬空） |
| **①** | 删 `PWR_5V_KEY` + `C89/A` 入 nc | PASS | PASS | **PASS**（`全部 100 个网连接完整 + 反向断言 0 非声明悬空`） |
| **②（仅真源）** | 删 `PWR_5V_KEY` + `C89/A` 并入 `P3V3` | — | — | **FAIL 2 处**（`网 'P3V3': 节点 C89/A 未连接` + `C89/A_1` 非声明悬空）⇒ 须同改原理图+板 |

⇒ **`①` 是唯一能让 `乙` 链一次转绿的纯数据路径**；`②` 结构性需要原理图/板改动（L1）。

## 4. 与「判据安装」链的接口（承 inc58）

| 前置 | 状态 | 备注 |
|---|---|---|
| ⑤ 裁定（本件） | **需 owner（L1/电源域口径）** | 无它则 `pipeline.yaml` 装后 k2 每次提交 rc=1（inc58 §2） |
| ① 落件（若选 `①`） | 裁定后一次可做 | 真源 + SPEC bump + pro + CO-90 F3 + （C89 子档） |
| `k2/fab/k2_v4_bom.csv` | 不存在 | 生成脚本骨架见 §5（口径＝**每行一 ref**） |
| 共享层 5 修 + pin 前移 | 未落 | inc57 §0-3 / inc58 §3 |

**顺序**：`⑤ owner 裁定` →（若①）真源+SPEC+pro+CO 更新 → BOM 生成 → 共享层 5 修 + pin → 装 `pipeline.yaml`（此时 `乙` 链 3/3 绿）。

## 5. `k2/fab/k2_v4_bom.csv` 生成脚本骨架（口径＝每行一 ref；`/tmp` 已验证产出可 PASS）

```bash
#!/usr/bin/env bash
# 生成 k2/fab/k2_v4_bom.csv（来源＝真 sch netlist；口径＝每行一个 ref，避免 csv.reader 拆列）
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCH="$ROOT/k2/hw/sch/k2_sch.kicad_sch"; OUT="$ROOT/k2/fab/k2_v4_bom.csv"
TMP="${TMPDIR:-/tmp}/opencode/k2_bom_net.kicadsexpr"; mkdir -p "$(dirname "$TMP")"
"$ROOT/AppDir/sharun" kicad-cli sch export netlist "$SCH" --format kicadsexpr --output "$TMP"
python3 - "$TMP" "$OUT" <<'PY'
import re,sys,pathlib
t=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
refs=sorted({m.group(1) for m in re.finditer(r'\(comp\s+\(ref "([^"]+)"\)',t)})
if not refs: raise SystemExit("netlist 0 器件 — fail-closed")
pathlib.Path(sys.argv[2]).write_text("Ref\n"+"\n".join(refs)+"\n",encoding='utf-8')
print(f"wrote {len(refs)} refs -> {sys.argv[2]}")
PY
```
**禁**：不要把多 ref 放在同一行且不加引号（`csv.reader` 会拆列，实测只读到第一个 → 误报不同步）。

## 6. 复跑

```bash
cd /home/fila/jqdDev_2025/ic_hw
# ① 五源对照：见 §1 各命令（grep 真源/sch/SPEC/Gerber/pro + netclass）
python3 -c "
import yaml,json
k1=yaml.safe_load(open('k1/boards/k1_sch.yaml'))['nets']['PWR_5V_KEY']
k2=yaml.safe_load(open('k2/hw/data/k2_sch.yaml'))['nets']['PWR_5V_KEY']
print('K1:',k1); print('K2:',k2)"
grep -rc 'PWR_5V_KEY' k2/hw/sch/ | grep -v ':0' || echo "sch 0 命中 ✓"
grep -c 'PWR_5V_KEY' k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-{7,12,25,47}.json
# ② 两选项语义：见 §3（inc58 全修共享树 + opt1/opt2 YAML；opt1 期望 3/3 PASS、opt2 期望 2 处 FAIL）
```
（`/tmp/opencode/inc59/{opt1,opt2}.yaml` 为本会话产物，易失；按 §3 的改动语义重建即可。）

## 7. 边界

本件**只读 + `/tmp` 语义验证**：未改真源/SPEC/原理图/图纸/板/pro/生成器/模板/库/`fp-lib-table`/`pm_gate/**`/`criteria/**`/`_shared/**`；
未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode`；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 受审板 `6ff49da5678c2108` · 真源 `dd794c54f7ce7417` · SPEC rev-47 `9ba09cbc148d6836`
