# K2 · P3 施工图集 v1（施工图层重建；**交监理核图**）

> **依据**：监理 **#K2-15 §二**（P2 正式关门、**P3 开**）+ 整改计划 **§P3**（产出/完工判据）+ **L2 裁定值**（`c3ee574455cf6633`… 见 `k2/docs/K2-ENG-AUDIT-2026-09-15.md` §十 L2-1..L2-8）。
> **边界（ENG 只出图 + 只给测量）**：未改 SPEC / 原理图 / 板 / 生成器 / `criteria/`；未动冻结件（交付板 `d4e81f64…`、设计源板 `fb07d25a…`）；未派 WORKER；输出仅 `L3/drawings/` 与 `/tmp`。
> **判据归属**：**P3 判据由监理核，ENG 不自判** —— 下表「结论」列只写 **ENG 测量值 + 待核**。

## 1. 交付物

| 件 | sha256(16) | 说明 |
|---|---|---|
| `k2/tools/k2_p3_drawings_v1.py` | `43e14cc8b16f7e30` | 图纸生成器（纯 stdlib SVG；只读输入；SPEC 经 `pm_gate.config` 解析，**无硬编码文件名**） |
| `k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_drawings.json` | `c54a4d910d432d38` | **机读图纸**（板框/四孔/55 件/走廊/回避区/层分配/敷铜/判据测量） |
| `k2/pm_gate/artifacts/k2_v4/L3/drawings/01_board_frame_and_holes.svg` | — | 板框图 + 固定孔（L2-1 / L2-2） |
| `k2/pm_gate/artifacts/k2_v4/L3/drawings/02_device_coordinates.svg` | — | 器件坐标图（55 真源件：40 已落 + 2 待移 + 13 待解） |
| `k2/pm_gate/artifacts/k2_v4/L3/drawings/03_corridor_occupancy.svg` | — | 走廊占用图（口径 = L2-4） |
| `k2/pm_gate/artifacts/k2_v4/L3/drawings/04_layer_assignment.svg` | — | 层分配图（8L）+ 过孔/等长策略 |
| `k2/pm_gate/artifacts/k2_v4/L3/drawings/05_pour_strategy.svg` | — | 敷铜策略（In1/In3/In6 GND + In4 电源） |
| `k2/pm_gate/artifacts/k2_v4/L3/drawings/06_keepouts.svg` | — | 回避区图（每区 5 开关） |
| `k2/pm_gate/artifacts/k2_v4/L3/drawings/07_interface_pads_inframe.svg` | — | 接口焊盘出框检查图 |

## 2. 判据对账（计划 §P3；ENG 测量，**待监理核**）

| # | 判据（计划原文） | 阈值 | ENG 实测（本件） | ENG 结论 |
|---|---|---|---|---|
| **P3-1** | 板框 = 120×46（`y[33,79]`） | `[冻结值]` | **120.0 × 46.0**，`x[23,143]` `y[33,79]`（L2-1；与 canonical SPEC `board` 字段逐字符一致） | 测量值如上，**待核** |
| **P3-2** | 固定孔 ≥4 个 NPTH，Ø3.2；距板边 ≥1.5mm 材料 | ≥4 / Ø3.2 / ≥1.5mm | **4 孔**（H1 26.10/75.60、H2 139.60/39.60、H3 26.10/36.10、H4 114.60/36.10；L2-2 几何解）；**最小边料 1.50mm**（H1/H3 贴限）；每孔 Ø6.0 回避区 | 测量值如上，**待核**（注：右侧不对称 = L2-2 已披露） |
| **P3-3** | 每器件 pad 数 == 符号引脚数 | 差异 = 0 `[结构=0]` | **53/55 逐值相等**；字面不符 2 件：`U1` 27(符号) vs **49**(`MCU_STM32G0_LQFP48`=48+EP49)、`U2` 6 vs 8（SOIC-8 含 2 未用脚）。按 #K2-12 §一-1 **有向口径**（电气引脚集 ⊆ 焊盘集 + 余量逐条登记）二者均属**已登记余量**（U1 余 22 = 未用 LQFP48 脚 + EP49；U2 余 2 = pad7/8 NC），登记件 = `K2-P2-E2-directed-pad-registry-v1.md`（v1.1） | 字面 2 项差异 = **有向口径登记项**；**请监理按 §一-1 口径核** |
| **P3-4** | 接口焊盘不出框（内缩 0.3mm） | 出框数 = 0 | 8 个接口件（`J2/J3/J4` + 排针 `J6/J9/J11/J12/J13`）**出框 0**；几何 = **板实测（as-built）+ L2-3 位移**（排针列 `column_x` 26.5 → **27.94**） | 测量值如上，**待核** |
| **P3-5** | 回避区生效：每 keepout 区 ≥1 开关 ≠ `allowed` | 每区 ≥1 | **4 区**（KO-1..4 固定孔 Ø6.0；KO-5 逃逸区；KO-6 AC pad GND cutout；KO-7 板边 0.30mm）**每区均有非 allowed 开关** | 测量值如上，**待核** |
| **P3-6** | 走廊口径统一（全部按「焊盘外接框净距」表述，字面一致） | 字面一致 | **L2-4 统一口径 = 焊盘外接框净距**；as-built **西 17.55mm / 东 27.81mm**；原冻结值 17.30 / 27.40 **作废**；本图集全部走廊表述按此口径 | 测量值如上，**待核** |

> **P3-3 诚实说明**：canonical SPEC `refdes_authority = "boards/ioconvert_v2.yaml sheets (禁止自造)"` ⇒ 器件集合以真源 yaml 55 件为准；符号为「仅用脚」表示法时，`pad 数 == 引脚数` 只在**有向口径**下成立（#K2-12 §一-1 已裁）。

## 3. 口径统一的落点（L2-4）

- 走廊净跨一律表述为**「焊盘外接框净距」**：西 `J3/J4 右缘 65.05 → U6 左缘 82.60 = 17.55mm`；东 `U6 右缘 104.84 → J2 左缘 132.65 = 27.81mm`。
- 与 L1 v2.0 硬约束 2 的「对间间距 **1.46mm**（对中心距）」为**不同口径**（前者 = 走廊器件净跨，后者 = 差分对间距），图集内禁止混用（已在 `p3_drawings.json.criteria.C6_corridor_basis` 机读留痕）。

## 4. **P3 未闭项（2 项，均属 L2 自裁域；交监理知悉）**

| # | 项 | 现状 | 处置（ENG 计划） |
|---|---|---|---|
| **G1** | **13 件 P4 补件坐标**（`D2`、`L1`、`R35–R39`、`R40`、`R41`、`R42–R45`） | 真源 yaml 有件**无坐标**；锚点板无此 13 件 ⇒ 图纸标 `coord_pending`（不臆造） | 下一轮以**约束求解器**解位（0.1mm 栅格；约束 = 板框内缩 0.3 + 无焊盘重叠（L2-8 8a）+ 就近其网端点：strap 9 件就近 U6 对应 strap 球、`D2/L1/R40/R41` 就近 U2 开关/反馈域）；解出后回写本图集 v2 |
| **G2** | `C73`、`C86` **移位新坐标**（L2-3 已裁须移位） | 旧位保留、标 `move_pending_L2-3` | 同上求解器（左带内、无重叠、不触 L1） |

> 两项**不阻塞** P3-1/2/4/5/6 的机判（均已给测量）；P3-3 亦已给 55 件对账。**未以「须 owner」为由停下** —— 均属 L2（PDN/布局），按 #K2-14/LAYOUT_CONSTITUTION 由 ENG 自裁执行。

## 5. 冲突登记（**请监理核图时一并裁定**）

- **L1/L2 冻结文档写 6 层**：`L1_TOPOLOGY_v2.0.md`（「6L 判定流程终定；8L 兜底仅回退候选」）与 `L2_STRUCTURE_v2.0.md`（§8L 重入 ECN 触发条款）**文本均为 6L**；而 **canonical SPEC `rev-22` = 8L**、交付板 = `k2_v4_8L`、计划 **Z3** 判据明文「SPEC 必须反映 8L」且已在 P2 判 **✅ 达成**（#K2-13 / #K2-14 §一）。
- **本图集按 8L 出**（`04_layer_assignment.svg`：F/In1..In6/B，信号 F/In2/In5/B、平面 In1/In3/In6、电源 In4），依据 = **canonical + 计划 Z3 + owner 指令 #14 ①（工艺冻结 = JLC HDI 盲埋孔，免 HDI/改叠层议题作废）**。
- **ENG 不自改 L1/L2 冻结件**（越权）；建议监理裁定其 **errata 或版本 bump**（与 #K2-12 §四「canonical 载陈旧内容」同型）。

## 6. 复跑（只读输入；输出到 `L3/drawings/`）

```bash
cd /home/fila/jqdDev_2025/ic_hw
AppDir/usr/bin/python3.11 k2/tools/k2_p3_drawings_v1.py      # 重新出图 + 重算判据
K2_P3_OUT=/tmp/opencode/p3/drawings AppDir/usr/bin/python3.11 k2/tools/k2_p3_drawings_v1.py   # 沙箱复跑（不动仓）
```
