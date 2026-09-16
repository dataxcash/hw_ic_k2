# P2 · R1/R2 改动集**纠偏**：网表侧漏项 9 件（`R35–R39`,`R42–R45`）—— **不得删，须「图 + 板」双补** v1

- **性质**：只读取证 + 对**已交回件**（`K2-P2-R1-64item-classification-v1.md` §5/§6）的事实**纠偏**。
  未动原理图 / 网表 / 板 / SPEC / 生成器 / `criteria/` / `.omo/supervision/**`；导出物仅 `/tmp/opencode`。
- **缘起**：E1 是**三源**等式（板 ↔ 图 ↔ 网表）。分类表只做了「**图-板 64**」方向，**漏核「网表-板」方向**。
  本轮逐向复核得：**网表(55) − 板(42) = 13 件**，其中 4 件 = `B` 类（`D2/L1/R40/R41`，已在册），
  **另 9 件既不在原理图、也不在板** ⇒ 前回件未覆盖，且其归零点被默认为「无」（= 危险）。

## 1. 事实（实测）

| 检查 | 结果 |
|---|---|
| 网表 `hw/data/k2_sch.yaml` refs（`sheets[*].placements`） | **55** |
| 板 `d4e81f64…` fps（`pcbnew`） | **42** |
| 网表−板（13） | `D2`, `L1`, `R40`, `R41`（=B 类）+ **`R35`,`R36`,`R37`,`R38`,`R39`,`R42`,`R43`,`R44`,`R45`** |
| 板−网表 | **0** |
| 上述 9 件是否在原理图 | **不在**（`kicad-cli sch export netlist` 103 件清单实测，逐件判定 = 否） |
| 上述 9 件是否在板 | **不在**（`pcbnew` 位号集） |

⇒ 9 件**只在网表里存在**；且它们**不在**「图-板 64 件」中（故前回件不可能覆盖）。

## 2. 定性 —— **设计意图（三源交叉），不得删**

| # | 证据 | 内容 |
|---|---|---|
| ① | **网表**（生成器网表权威） | 9 条 strap 网，节点 = `U6/<strap 球>` + `Rxx/A`：`DS320_STRAP_MODE`→`U6/MODE`+`R35/A`；`…_A_ADDR0_7-0`→`R36`；`…_A_ADDR1_7-0`→`R37`；`…_B_ADDR0_7-0`→`R38`；`…_B_ADDR1_7-0`→`R39`；`…_A_ADDR0_15-8`→`R42`；`…_A_ADDR1_15-8`→`R43`；`…_B_ADDR0_15-8`→`R44`；`…_B_ADDR1_15-8`→`R45`（各 `R../B`→`GND`） |
| ② | **冻结 SPEC rev-19** `layer_plan.strap_domain_v32.resistors`（**9 条记录**） | 逐件给出 **球名 / 球板坐标 / net / 值 / `r_b_net=GND` / side**：`R35`(FF24,MODE,6.19k,E96)、`R36`(B23,1k)、`R37`(G1,1k)、`R38`(B25,8.25k)、`R39`(F34,1k)、`R42`(FF5,1k)、`R43`(FJ3,1k)、`R44`(FJ28,1k)、`R45`(FF30,1k)；`placement` = `south_strip_concentrated(甲案)`、`Resistor_SMD:R_0603_1608Metric`、zone `x[83,104] y[58.5,66]`、`row_plan 2 rows x 5/4 stagger`；`exec_gate = low_speed_apply … DRC 归零为核对` |
| ③ | **真源球映射**（354 球） | 9 个 strap 球**全部存在**：`MODE=FF24`、`A_ADDR0_7-0=B23`、`A_ADDR1_7-0=G1`、`B_ADDR0_7-0=B25`、`B_ADDR1_7-0=F34`、`A_ADDR0_15-8=FF5`、`A_ADDR1_15-8=FJ3`、`B_ADDR0_15-8=FJ28`、`B_ADDR1_15-8=FF30` |
| ④ | **与板侧缺陷吻合** | 板侧实测：`U6` **15 球无网/未连**，`DS320_STRAP_*` 属其中；板侧 `0 焊盘的网` 含 `DS320_STRAP_MODE` + 6×`DS320_STRAP_*_ADDR*` |

⇒ 结论：**9 件是「单颗 `U6` 自有 strap 域」的取真源意图**（网表 + 冻结 SPEC + 球映射三方一致）。
按 Z1 §2 规则 4「陈旧件不得反向约束设计」，**不得因原理图（双颗 `U3/U7` 时代）没有它们而删**；
它们与 `C` 类（18 件 `U3/U7` strap 电阻，**确属陈旧**）**方向相反**：`C` 类是「旧的 strap 网」该删，
本 9 件是「新的 strap 网」该**补** —— 即 **strap 域由 `U3/U7` 迁址到 `U6`**。
**删之即同时掩盖两个缺陷**：(a) 源侧缺单颗 strap 域；(b) 板侧 15 球未连。

## 3. 纠偏（对本轮已交两件的订正）

| 项 | 前回件口径 | **订正口径** |
|---|---|---|
| R1 **删** | 52（A34+C18）→ D8 补证后 **60** | **60（A34+C18+D8）不变** |
| R1 **补入** | 3（`C88`/`C89`/`U6`） | **12**（`C88`/`C89`/`U6` **+ 9 件 strap R**） |
| R2 **删** | 无（A/C/D 不在网表） | **无（仍 0 删）** —— 网表 55 件**全数保留**（其中 9 件须在图/板落地） |
| **E1 预期** | 图 `103−60+3=46` vs 板 42 ⇒ 图-板 4 | **图 `103−60+12=55` = 网表 55**；板 42 ⇒ **板缺 13（=B4 + 9R）= P4 补** |
| **P4 板侧清单** | `B`4 + `U6` strap 球未连 | `B`4 **+ 9 件 strap R 补件** + `U6` 15 球连线（含 `SCL`/`SDA`/`PD_*`） |
| **E1 归零完整条件** | R1 + P4 补 B4 | **R1(−60, **+12**) + P4(板 +13 件 + `U6` 球连线)** |

> **不纠偏的后果**：按旧口径执行 ⇒ 图 46 **≠** 网表 55 ⇒ **E1 永不可达**（且会被误报为「接近归零」）；
> 若把这 9 件误判为陈旧而删 ⇒ **删真源意图**（违反「不得以删差异达成归零」红线）。

## 4. 边界与复现

- 只读取证：未改任何源/判据/生成器；未写 `.omo/supervision/**`；未派 WORKER。
- 复现：
```bash
# ① 网表-板 差集（含 9 件）
AppDir/usr/bin/python3.11 -c "
import yaml,pcbnew;d=yaml.safe_load(open('k2/hw/data/k2_sch.yaml'))
refs={p['ref'] for s in d['sheets'] for p in s['placements']}
b=pcbnew.LoadBoard('k2/hw/k2_v4_8L.l4.kicad_pcb');brd={f.GetReference() for f in b.GetFootprints()}
print(len(refs),len(brd),sorted(refs-brd))"
# ② 这 9 件不在原理图
kicad-cli sch export netlist --format kicadsexpr -o /tmp/opencode/k2p1/d8/k2_sch.net k2/hw/sch/k2_sch.kicad_sch
grep -c '(ref "R35")' /tmp/opencode/k2p1/d8/k2_sch.net     # → 0
# ③ 冻结 SPEC 的 strap 域（9 条）
python3 -c "
import json;d=json.load(open('k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json'))
s=d['layer_plan']['strap_domain_v32'];print(len(s['resistors']),[r['resistor'] for r in s['resistors']])"
```

## 5. 四向闭合校验（v1 追加，2026-09-16 15:1x）—— 纠偏口径的**独立**验证

| 量 | 实测 | 结论 |
|---|---|---|
| `|图| / |网表| / |板|` | `103 / 55 / 42`（`图∩网表 = 43`） | — |
| **`图 − 网表`** | **60** = `A34∪C18∪D8`（逐件相同） | **删除集 == 图−网表（恒等）** ⇒ 删这 60 件后图侧不再有网表外件 |
| **`网表 − 图`** | **12** = `{C88,C89,U6} ∪ {R35–R39,R42–R45}`（逐件相同） | **补入集 == 网表−图（恒等）** |
| **`R1(−60,+12)` 后 `图 == 网表`** | **True** | 源侧同构达成（`55 == 55`） |
| `网表 − 板` | **13** = `B4 ∪ 9R` | 板侧差（P4 补，含 `U6` 球连线） |
| `板 − 网表` | **0** | 板侧无网表外件 |

> 该四项**互相独立**地指向同一改动集：`图−板 64 = A34∪B4∪C18∪D8`、`图−网表 60 = A34∪C18∪D8`、
> `网表−图 12`、`网表−板 13 = B4∪9R` ⇒ **R1(−60,+12)** 是**唯一**能使 `图==网表` 的改动集，
> 且**每个集逐件相等**（非按数量凑）。任何「少删/多删/漏补」都会使等式破。

**复现**：
```bash
AppDir/usr/bin/python3.11 - <<'PY'
import yaml,pcbnew,re
d=yaml.safe_load(open('k2/hw/data/k2_sch.yaml'))
net={p['ref'] for s in d['sheets'] for p in s['placements']}
sch=set(re.findall(r'\(comp\s+\(ref\s+"([^"]+)"\)',open('/tmp/opencode/k2p1/d8/k2_sch.net',encoding='utf-8').read()))
brd={f.GetReference() for f in pcbnew.LoadBoard('k2/hw/k2_v4_8L.l4.kicad_pcb').GetFootprints()}
print(len(sch),len(net),len(brd));print('图-网表',len(sch-net));print('网表-图',len(net-sch))
print('图-板',len(sch-brd));print('网表-板',len(net-brd),'板-网表',len(brd-net))
PY
```
