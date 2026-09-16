# P2 · R1 前置补证：D 类（`C65–C72`）定性 —— **陈旧件，删除成立** v1

- **性质**：**只读取证**（补 #K2-11 §二-3 要求的 D8 定性；#K2-11 §五 要求「**8×100nF 未定性前不得删**」）。
  未动原理图 / 网表 / 板 / SPEC / 生成器 / `criteria/`；导出物仅落 `/tmp/opencode/k2p1/`。
- **目标问题**（`K2-P2-R1-64item-classification-v1.md` §5）：`C65–C72`（100nF，图上 `v5_connectors` 页）是
  **链路耦合件 / 连接器侧去耦 / 随 U3/U7 陈旧**？—— 三选一决定「删 或 保留（板侧 P4 修）」。

## 1. 方法（两条独立证据链，均指向真源）

| # | 证据链 | 命令/来源 |
|---|---|---|
| E-a | **原理图网表化逐脚实连**（不经 `hw/data/k2_sch.yaml`，独立导出） | `kicad-cli sch export netlist --format kicadsexpr -o /tmp/opencode/k2p1/d8/k2_sch.net k2/hw/sch/k2_sch.kicad_sch`（Eeschema 10.0.5；103 元件 / 145 真实网 + 21 `unconnected-*`） |
| E-b | **厂商球映射真源**（L2 真源层，Z1 §1） | `…/mcio_feas_step2/ds320pr1601_ballmap.json`（354 球；`validation.n_balls=354, duplicates=0`） |

## 2. 实测（E-a）：`C65–C72` 逐件逐脚

| ref | pin1 | pin2 | 说明 |
|---|---|---|---|
| `C65` | **`VREG1_U3`** | `GND` | U3（下行 `DS160PR810`）内部稳压器 1 输出去耦 |
| `C66` | **`VREG2_U3`** | `GND` | 稳压器 2 |
| `C67` | **`VREG1_U3`** | `GND` | 同上（并联） |
| `C68` | **`VREG2_U3`** | `GND` | 同上 |
| `C69` | **`VREG1_U7`** | `GND` | U7（上行 `DS160PR810`）稳压器 1 |
| `C70` | **`VREG2_U7`** | `GND` | 稳压器 2 |
| `C71` | **`VREG1_U7`** | `GND` | 同上 |
| `C72` | **`VREG2_U7`** | `GND` | 同上 |

⇒ 八件**全部**接在 **`U3`/`U7`（双颗 `DS160PR810`）的 `VREG1`/`VREG2` 内部稳压器输出**上。
它们**不是** PCIe 链路耦合（链路耦合 = 220nF **且已内置**，见分类表 §2-A1），
**也不是** 连接器侧去耦（`P3V3_AUX` 网实连 = `C90`/`J11.4`/`J3.17`/`J4.17`/`R1.2`/`U1.15`，**不含** `C65–C72`）。

## 3. 实测（E-b）：真源（单颗 `DS320PR1601`）**没有** `VREG` 球

- 354 球标签集（166 个唯一标签）中，**电源类标签仅** `VCC1/VCC2/VCC3/VCC4`（7/8/8/7 = **30 球**）；
- 按 `REG|CAP|LDO|VCC|VDD|PWR|3V3|AUX|IN` 正则检索：命中仅 `VCC1..VCC4`；**`VREG*` / `LDO*` / `CAP*` 命中 = ∅**；
- 与真源链一致：canonical 叠层注记 = `DS320PR1601 … VCC1-4 30 balls internal LDO`（稳压器**全内置、无外露输出脚**）。

⇒ 真源**根本不存在** `VREG1/VREG2` 这一网络域 ⇒ `C65–C72` 所去耦的对象（U3/U7 的 VREG 输出）**在单颗架构下不存在**。

## 4. 交叉核对（防「以删源掩盖板缺陷」）

| 检查 | 实测 | 结论 |
|---|---|---|
| 单颗芯片的 VCC 去耦是否已在板上/源上具备 | 板上 `C74–C83`（10×100nF）接 `P3V3`；SPEC rev-19 `components.must_add.redriver_vcc_decoupling = [C74…C83]` | **覆盖 `VCC1–4`（30 球）⇒ 无功能缺口** |
| 真源 SPEC 是否已把这三件判为退役 | `_spec_rev_9`：`pd.decoupling: C67_C68_C72（板上不存在）-> 板实按网集合（P3V3/C84 等）；旧串转 decoupling_legacy_retired` | 真源侧**已定性为板外陈旧件**（一致） |
| 删这八件会不会掩盖板侧缺陷 | 板侧缺陷（`U6` 8 strap 球未连 / `MODE`/`SDA`/`SCL`/`PD_*` 共 15 球；`B` 类 `D2/L1/R40/R41` 缺件）**与本八件无关** | **不掩盖**：须在 P4 板侧缺陷清单**独立保留**（同 C 类防掩条件） |

## 5. 结论与对 R1/R2 的影响

1. **`C65–C72` 定性 = 陈旧件**（随 `U3/U7` 双颗 `DS160PR810` 作废）⇒ **归零点 = 源侧删**，与 C 类（18 件 strap）**同族**；**不是**板侧缺陷、**不是**待补板件。
2. ⇒ **R1 改动集** = `A`34 + `C`18 + `D`8 = **删 60** + 补入 **3**（`C88`/`C89`/`U6`）；`B`4（`D2/L1/R40/R41`）**图上保留**、P4 板侧修。
3. ⇒ **E1 预期（订正）**：原理图 `103 − 60 + 3 = 46`；板 42 ⇒ **板-图 0 / 图-板 4（= `B` 类）**。
   **E1 归零完整条件 = R1（−60, +3） + P4 补 `B`4**（`D` 类已定性，不再挂账）。
4. **本补证不构成落盘**：R1/R2 仍**须监理复核后方可动**（#K2-11 §三/§五）；本条仅**消解分类表中最后一个「定性未决」项**（分类表 v1 §5 之「待补证」二路径中，路径①已由本轮完成）。

## 6. 边界与复现

- 未动：原理图 / 网表 / 板 / SPEC / 生成器 / `criteria/` / `.omo/supervision/**`；未派 WORKER；导出物仅 `/tmp/opencode/k2p1/d8/`。
- 复现：
```bash
kicad-cli sch export netlist --format kicadsexpr -o /tmp/opencode/k2p1/d8/k2_sch.net k2/hw/sch/k2_sch.kicad_sch
python3 - <<'PY'
import json,re,collections
src=open("/tmp/opencode/k2p1/d8/k2_sch.net",encoding="utf-8").read()
nets=re.findall(r'\(net\s+\(code\s+"?(\d+)"?\)\s+\(name\s+"([^"]*)"\)\s+\(class\s+"[^"]*"\)(.*?)(?=\(net\s+\(code|\Z)',src,re.S)
pin=collections.defaultdict(list)
for c,n,b in nets:
    if n.startswith("unconnected-"): continue
    for m in re.finditer(r'\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)',b): pin[m.group(1)].append((m.group(2),n))
for i in range(65,73): print(f"C{i}",sorted(pin[f"C{i}"]))
d=json.load(open("k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/ds320pr1601_ballmap.json"))
print("VREG/LDO/CAP 标签:",[b["signal"] for b in d["ballmap"] if re.search(r'VREG|LDO|CAP',b["signal"],re.I)])
PY
```
