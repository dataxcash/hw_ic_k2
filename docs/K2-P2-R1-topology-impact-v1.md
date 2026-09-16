# P2 · R1 落地前置「网拓扑影响」核查 v1（**只读取证**；R1 动作清单须据本件补全）

- **动机**：R1 现口径 = 「原理图删 60 + 补 12」。删除**串联**元件会**断开链路**；若不并网，`E1/E3` 表面「差距变小」而**实际静默断链**
  （= 红线「不得以删差异达成归零」的机器可检形态）。本件逐件核**删除侧的网拓扑后果**，不落盘。
- **仪器/数据**：`kicad-cli sch export netlist`（Eeschema 10.0.5，`/tmp/opencode/k2p1/d8/k2_sch.net`）
  + 网表 `hw/data/k2_sch.yaml`；分析脚本输出 `/tmp/opencode/k2p1/r1_topology_impact.json`。
- **边界**：未动原理图/网表/板/SPEC/生成器；未写 `.omo/supervision/**`；未派 WORKER；P3 未开。

## 1. 结论（三项，均须并入 R1 动作清单）

| # | 结论 | 后果若忽略 |
|---|---|---|
| **T1** | **32×220nF（`C17–C32`,`C49–C64`）全部为「串联」器件**（两脚分属**两个不同网**）⇒ R1 必须**并网 32 对**，保留 **yaml 侧网名**、退役 `*_U3`/`*_U7` 名 | 删符号即**断开 32 条 PCIe 链路**（J2↔U6↔J3/J4），E3 会新增 32 条不一致而 E1 反而「变好」 |
| **T2** | C 类 18 件中 **4 件非接地 strap**：`R4`(`P3V3`↔`STRAP_READ_EN_U3`)、`R9`(`P3V3`↔`STRAP_READ_EN_U7`)、`R26`(`P3V3`↔`ALL_DONE_N_U3`)、`R27`(`P3V3`↔`ALL_DONE_N_U7`)；其余 14 件 = 一端 `GND` | 删除本 4 件与**真源一致**：冻结 SPEC `strap_domain_v32.non_strap_sideband` 明载 `ALL_DONE_FF27 = NC no-action`、`READ_EN_FJ25 = NC no-action` ⇒ **无上拉需求**，删除成立（须在图注中留痕） |
| **T3** | 删除 `U3`/`U7` 并补入单颗 `U6` **不是「增删符号」**：原理图链路网名/节点目前绑定 `U3`/`U7` 脚位，真源 yaml 绑定 `U6` **球名** ⇒ 须做 **脚 ↔ 球 重映**（如 `PCIE_DN0_P`: 原理图 `J2↔U3.pin` → yaml `J2/TX0_P ↔ U6/A_PERP0`） | 只删不映 ⇒ 链路网在单颗下**无对端**（悬空网），E3 全面破 |

## 2. T1 明细：32 对并网表（节选；全表见 JSON）

| 串联件 | 网 A | 网 B | **保留名**（= yaml 网名） |
|---|---|---|---|
| `C17` | `PCIE_DN_OUT0_P_MCIO` | `PCIE_DN_OUT0_P_U3` | **`PCIE_DN_OUT0_P_MCIO`** |
| `C18` | `PCIE_DN_OUT0_N_MCIO` | `PCIE_DN_OUT0_N_U3` | **`PCIE_DN_OUT0_N_MCIO`** |
| `C19` | `PCIE_DN_OUT1_P_MCIO` | `PCIE_DN_OUT1_P_U3` | **`PCIE_DN_OUT1_P_MCIO`** |
| `C20` | `PCIE_DN_OUT1_N_MCIO` | `PCIE_DN_OUT1_N_U3` | **`PCIE_DN_OUT1_N_MCIO`** |
| … | …（`C21–C32` 同型：MCIO 侧 ↔ `_U3`） | | |
| … | …（`C49–C64` 同型：`_J2` ↔ `_U7`） | | |

**统计**：32 对中「**恰一侧名 == yaml 网名**」= **32 / 32**（无例外）⇒ 保留名唯一确定，退役名 = `*_U3` / `*_U7`。
⇒ R1 的并网动作**完全可机检**：`并网后 (退役名 == ∅) 且 (保留名节点数 +1)`。

## 3. 对 R1 动作清单的补全（**待监理裁定口径**）

| # | 动作 | 件/对 | 备注 |
|---|---|---|---|
| R1-a | 删符号 | **60** | A34（32 串联电容 + `U3`/`U7`）+ C18 + D8 |
| R1-b | **并网**（T1） | **32 对** | 保留 yaml 名；退役 `*_U3`/`*_U7` |
| R1-c | **脚 ↔ 球 重映**（T3，`U3`/`U7` → `U6`） | 28+28 HS 网 + strap/电源域 | 依 `DS320PR1601` 球映射真源 |
| R1-d | 补入件 | **12** | `C88`/`C89`/`U6` + `R35–R39`,`R42–R45` |
| R1-e | 新增网 | **9** | `DS320_STRAP_*`（U6 strap 域，见 SPEC `strap_domain_v32`） |

> **实施路径二选一（须监理裁）**：
> **(i) 局部编辑**：按 R1-a…e 手工改 3 个 `.kicad_sch`（量大、易错，但零新增工具）；
> **(ii) 由真源再生**：以 `hw/data/k2_sch.yaml`（+ SPEC/球映射）**再生**原理图（Z1 §2 规则 2 的「派生」语义），
> 需**新增工具**（= 改工具链 ⇒ 另案放行）。
> 二者都**不含** E1 目标变化（仍 **55**）；本件不选边，只把「静默断链」风险显式化。

## 4. 复现

```bash
kicad-cli sch export netlist --format kicadsexpr -o /tmp/opencode/k2p1/d8/k2_sch.net k2/hw/sch/k2_sch.kicad_sch
python3 - <<'PY'   # 逐件列两脚网名，判定 串联/接地
import re,collections
src=open('/tmp/opencode/k2p1/d8/k2_sch.net',encoding='utf-8').read()
nets=re.findall(r'\(net\s+\(code\s+"?(\d+)"?\)\s+\(name\s+"([^"]*)"\)\s+\(class\s+"[^"]*"\)(.*?)(?=\(net\s+\(code|\Z)',src,re.S)
pin=collections.defaultdict(dict)
for c,n,b in nets:
    if n.startswith('unconnected-'): continue
    for m in re.finditer(r'\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)',b): pin[m.group(1)][m.group(2)]=n.split('/')[-1]
for r in [f'C{i}' for i in list(range(17,33))+list(range(49,65))]: print(r, sorted(set(pin[r].values())))
PY
```

## 5. 网名收口闭合校验（v1 追加，2026-09-16 15:5x）—— 并**更正 T4「新增 9 网」为 10 网**

以**网名**维度做 R1 前后闭合推演（原理图真实网 145 vs 网表 101，交集 **91**）：

| 方向 | 条数 | 逐条归属 | R1 后的处理 |
|---|---|---|---|
| **网表有、图无** | **10** | 9×`DS320_STRAP_*`（`MODE`+8×`*_ADDR*`，节点 = `U6/<球>` + `R../A`）+ **`PWR_5V_KEY`**（节点 = `C89`） | **须新增**（含 `C88`/`C89` 补入件的网） |
| **图有、网表无** | **54** | ① **32** = 串联退役网 `PCIE_DN_OUT*_U3` / `PCIE_UP_OUT*_J2`↔`_U7`（由 **T1 并网**吸收）；② **18** = `U3/U7` strap 网（`STRAP_*`/`PD0/PD1`/`ALL_DONE_N_*`，随 C 类件删除）；③ **4** = `VREG1/2_U3`、`VREG1/2_U7`（随 D 类件删除） | **全部消失**（32 并入保留名 / 22 随件移除） |

**闭合结论**：`145 − 54（图-only 全消）= 91` ⇒ `91 ∪ 10（网表-only 全增）= 101 = 网表` **恒等闭合**（网名维度 R1 后**零缺口**）。
⇒ **T4 更正**：新增网 = **10**（9 strap + `PWR_5V_KEY`），非 §3 表所载 9；`PWR_5V_KEY` 即 `C89`（4.7µF）之网，随「补入 3 件」一并落地。
⇒ **节点级**闭合仍依赖 **T3 脚↔球重映**（如 `PCIE_DN0_P`: `J2↔U3` → `J2/TX0_P ↔ U6/A_PERP0`）与 T2 处置，本件不重复。

**复现**：
```bash
python3 - <<'PY'
import re,collections,yaml
src=open('/tmp/opencode/k2p1/d8/k2_sch.net',encoding='utf-8').read()
nets=re.findall(r'\(net\s+\(code\s+"?(\d+)"?\)\s+\(name\s+"([^"]*)"\)\s+\(class\s+"[^"]*"\)(.*?)(?=\(net\s+\(code|\Z)',src,re.S)
S={n.split('/')[-1] for c,n,b in nets if not n.startswith('unconnected-')}
Y=set(yaml.safe_load(open('k2/hw/data/k2_sch.yaml'))['nets'])
print(len(S),len(Y),len(S&Y));print('网表-图',sorted(Y-S));print('图-网表',len(S-Y))
PY
```

## 6. 节点（网 × 器件）维度闭合校验（v1 追加，2026-09-16 16:0x）

**方法**：取 91 个交集网，施加计划动作后逐网比较「器件集合」——
① 并网 32 对（退役名并入保留名、节点取并集）；② 删 60 件（从各网移除）；③ `U3`/`U7` → `U6`；④ 补入 12 件；再与网表逐网比 `refs`。

**结果**：仍不一致 **79** 条，且**全部为「计划内」**（差异集 ⊆ `{U6}` ∪ `{C88,C89}` ∪ `{R35–R39,R42–R45}`），
**计划外差异 = 0**。典型形态：`PCIE_DN0_P` 图侧 `{J2}` vs 网表 `{J2,U6}`（缺 `U6`）；`PWR_5V_KEY` 图侧 `∅` vs 网表 `{C89}`；
`GND` 缺 12 件（`C88/C89` + 9 件 strap R + `U6`）。

**含义**：R1 在 **「网 × 器件」维度零缺口** —— 凡差异皆由**计划自身**的补入件解释，**无任何计划外遗漏**。
**仍欠维度**：**引脚级（脚 ↔ 球）映射**（§3 T3）本件**未验**（需 `DS320PR1601` 球映射 + 设计意图逐脚对齐），R1 落地时须与并网一并完成。

**复现**：
```bash
python3 - <<'PY'
import re,collections,yaml,json
src=open('/tmp/opencode/k2p1/d8/k2_sch.net',encoding='utf-8').read()
nets=re.findall(r'\(net\s+\(code\s+"?(\d+)"?\)\s+\(name\s+"([^"]*)"\)\s+\(class\s+"[^"]*"\)(.*?)(?=\(net\s+\(code|\Z)',src,re.S)
sch=collections.defaultdict(set)
for c,n,b in nets:
    if n.startswith('unconnected-'): continue
    for m in re.finditer(r'\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)',b): sch[n.split('/')[-1]].add(m.group(1))
yn={k:{re.sub(r'/.*','',x) for x in v} for k,v in yaml.safe_load(open('k2/hw/data/k2_sch.yaml'))['nets'].items()}
merge={p['net_b']:p['net_a'] for p in json.load(open('/tmp/opencode/k2p1/r1_topology_impact.json'))['merge_pairs']}
DEL={f'C{i}' for i in list(range(17,33))+list(range(49,73))}|{'U3','U7','R4','R5','R6','R7','R9','R10','R11','R12','R17','R18','R19','R20','R22','R23','R24','R25','R26','R27'}
ADD={'C88','C89','U6'}|{'R35','R36','R37','R38','R39','R42','R43','R44','R45'}
t=collections.defaultdict(set)
for n,refs in sch.items(): t[merge.get(n,n)] |= refs
bad=0
for n in set(t)|set(yn):
    a={('U6' if x in ('U3','U7') else x) for x in t.get(n,set())-DEL}; b=yn.get(n,set())
    if a!=b and not (b-a <= ADD and not a-b): bad+=1
print('计划外差异 =',bad)
PY
```
