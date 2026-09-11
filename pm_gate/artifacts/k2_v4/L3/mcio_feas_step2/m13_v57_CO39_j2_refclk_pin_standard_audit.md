# CO-39 — 【L1 闸口更正 + owner 一问收窄】J2 侧 REFCLK 引脚由连接器 pinout 真源锁定 ⇒ 选项 (B) **撤回**；(A)/(C) 请 owner 裁定

> 2026-09-12｜提出：ARCHER（续接会话，context 归零）｜性质：**对 CO-38 前提的独立复核 + 决策收窄**（只读复核，零几何改动，未改任何源）
> 触发：续接会话按 handoff §8.1 先查 owner 闸口 ⇒ **未裁**（ledger 尾仍为 09:25 handoff；k2 HEAD 仍 `c72c342`；无裁定件）⇒ 依纪律**停候**；停候期间复核闸口**前提**，出本件。
> 前置：`m13_v57_CO38_refclk_j2_access_ruling.md` `3863b22451d90e57`。**本件取代其 §0 的选项集与 §1.1 的"来源"定性**；其 §1.2（内列墙不可穿）/§1.3（自由通道）/§1.4（互封）**结论不变、本次复核无异议**。

## 0. 结论（三行）
1. CO-38 §1.1 "J2 侧引脚选择 = 模型补录、未经审计 ⇒ 可变" **不成立**：J2 侧 REFCLK 端点由**原理图网表**定义（`J2/REFCLK0_P` …），pad 号 11/12/29/30 由**连接器 pinout 真源**给定，与全板数据对**同构**。`s0_method_net_join` 补录只做 symbol-pin → footprint-pad 解析，非自由选择。
2. 故 **选项 (B) 撤回**：11/13 中 `13=GND`、12/14 中 `14=RX2_P`；且对插件仍按 SFF-8654 在 11/12 送 REFCLK，单板不能单方面改触点含义。
3. 请 owner 在 **(A)**（拆对 + F.Cu 单层绕行）与 **(C)**（把 REFCLK 纳入既有 J2 外列逃逸拓扑 = 单次 F→In2→F）间裁定。

## 1. 复核证据（四层一致；sha16 均为本次实读）
### 1.1 原理图网表（权威）`k2/boards/k2_sch.yaml` `70448241caa6f04a`
- `nets:` → `PCIE_REFCLK0_P: [J3/REFCLK_P, J2/REFCLK0_P]`；`PCIE_REFCLK0_N: [J3/REFCLK_N, J2/REFCLK0_N]`；REFCLK1 同构（`J4/REFCLK_P/N` ↔ `J2/REFCLK1_P/N`）。
- J2 符号 `SlimSAS_x8`（value `SlimSAS_x8_SFF8654`，footprint `ForgeOS:SlimSAS_x8_SFF-8654_74pin_RASide`）**自带引脚功能**：`11=REFCLK0_P, 12=REFCLK0_N, 13=GND, 14=RX2_P, 15=RX2_N, 29=REFCLK1_P, 30=REFCLK1_N`。
⇒ 端点 = 网表事实，引脚功能 = 符号事实。二者均在被冻结的 k2_sch 源内。

### 1.2 连接器 pinout 真源 `_shared/eda_core/sch_gate/datasheets/SlimSAS_x8_SFF8654.yaml` `9ca3639b2aab255f`
- `source: "SFF-8654 SlimSAS 8X 74-position, A1-A37/B1-B37, row-major"`。
- `11: REFCLK0_P` / `12: REFCLK0_N` / `13: GND` / `14: RX2_P` / `15: RX2_N` / `29: REFCLK1_P` / `30: REFCLK1_N`。
⇒ 与 1.1 符号**逐一吻合**（符号由该真源生成）。引脚号 = **标准定义**，非设计自由参数。

### 1.3 冻结板 `k2_v4_8L.kicad_pcb` `fb07d25ac426ff84`（**与四源钉值 MATCH**）
- 42 个 footprint **全部 pad 无网**（本板是纯几何/放置件，网表在 manifest）。
- J2 = 74 pad；`11` 内列 (132.65, 45.90)、`12` 外列 (135.00, 45.90)、`29/30` y=51.30（内/外列）；pad 尺寸 1.3×0.35、0.6 节距（与 CO-38 §1.1/§1.2 一致）。
⇒ **CO-38 的坐标与"内列墙"判据正确**；仅"来源 = 未审计补录"的定性有误。

### 1.4 与数据对同构（决定性反证）
| page | P pad / 列 | N pad / 列 | datasheet 对照 |
|---|---|---|---|
| `PCIE_DN0/input` | 39 内 (132.65) | 40 外 (135.00) | 39=TX0_P / 40=TX0_N |
| `PCIE_DN1/input` | 42 外 (135.00) | 43 内 (132.65) | 42=TX1_P / 43=TX1_N |
| `PCIE_DN2/input` | 51 内 | 52 外 | 51=TX2_P / 52=TX2_N |
| `PCIE_DN3/input` | 54 外 | 55 内 | 54=TX3_P / 55=TX3_N |
| `PCIE_DN4/input` | 57 内 | 58 外 | 57=TX4_P / 58=TX4_N |
| `PCIE_DN5/input` | 60 外 | 61 内 | 60=TX5_P / 61=TX5_N |

全板规律：**奇 pad = 内列（A 排）、偶 pad = 外列（B 排）**；**数据对本来就跨列**（既有 8 层拓扑即 "P 内列西出 / N 外列东出"）。
⇒ REFCLK 的 11/12、29/30 与**每一个数据对完全同构**：跨列是**标准形态**，不是异常，也不是补录错误。

## 2. 为什么 (B) 不可行（逐子项，均可机检）
- **(B1) 内列 11/13**：`13 = GND`（1.2 + 1.1 同名）⇒ 等于把时钟接到接地触点。
- **(B2) 外列 12/14**：`14 = RX2_P`，属既有数据网 `PCIE_UP_OUT2_P_J2` ⇒ 抢触点。
- **(B3) 标准/对插件**：REFCLK0 在 SFF-8654 上定义在 11/12；主机/线缆仍按标准在该触点输出 ⇒ 单板改动无法改变系统级触点含义（要改只能换非标连接器/线缆，超出单板 ECO 范畴）。
- **(B4) 红线**：改网表即动冻结源 ⇒ 须版本化 ECO；但即使 ECO 也不解决 B3。
⇒ **(B) 撤回**。CO-38 §0 的"二选一"实为"一真一假"。

## 3. 更正后的 owner 选项（L1）
### (A) 拆对 + F.Cu 单层绕行（= CO-38 §3 见证件 v2 路径）
保持 REFCLK 隔离（F.Cu 独占）。代价（CO-38 §1.4 已证）：N 绕连接器端部、两对互封、对内 4 种轨/进出侧组合穷举均交叉 ⇒ 需引擎新布线族 + 绕行等长补偿。属 **L1 拓扑/信号流向**。

### (C) 把 J2 侧 REFCLK 纳入**本板既有的外列逃逸拓扑**（新增项，几何代价最小）
本板 SPEC `j2_escape_topology` 原文即含："`outer_escape`: 外列焊盘右侧绕行至 In2 走廊"（数据对即 **F→In2→F 单次换层**）。做法：P（内列）直接西出 F.Cu；N（外列）东绕 → **单次 via** → In2 走廊 → 西侧回 F.Cu 与 P 成对。
- 几何可行区间已测（CO-38 §1.3）：两列缝 `x≈133.825` **全 y 自由**；In2 为既有数据扇通道。
- **待一次闭式核**：In2 走廊余量（CO-33 曾在此域遇 lane-end via 间距冲突）。若余量不足 ⇒ (C) 亦不可行，届时只剩 (A)。
- **代价 = 解除 REFCLK 隔离契约**：`constraints.refclk_isolated = true`（SPEC `0bd52ed48e720b8c`）+ `corridors[EAST_CHIP_TO_J2].bands[refclk].layer = 'F.Cu'`（`layer_note: 'per D0-2'`，SPEC 与 `spec-rev-2 0a7ad112ac4c57e3` 皆有）+ `escape_transition_zone.no_via = true`；须 SPEC 版本化修订（spec-rev-3）。REFCLK 将与数据扇共用 In2（串扰/隔离风险）——**这正是该契约设立的原因**。
- **定层**：按标准裁定，"走廊/过孔策略/判据域"名义属 **L2**；但红线明示唯一豁免 = CO-37 逃逸区且**排除 REFCLK**（`.kicad_dru 3148703240d54420` 含 `!(A.NetName == 'PCIE_REFCLK*')`）⇒ 触碰该豁免须 **owner 一句话授权**方可自裁落地。

### (D) 维持现状
= 接受 `L5-DFM.3` new 60（无法达 D4 milestone）。仅作对照列出。

## 4. 本轮未改物 / 红线
- 未改四源：`0bd52ed48e720b8c / a8ef3ea8ecff99d7 / fb07d25ac426ff84 / 0a459839e15960b8`（其中板源本次实读复核 = MATCH）；未改引擎/见证件/板/图纸/ALLOC/判据/`.kicad_dru`。
- **几何零落地：DFM 仍 = 60 = 100% REFCLK**；引擎 AST `while=0`；无坐标搜索、无暴力迭代、无 partial pass。
- 附带（**文档覆盖缺口，非缺陷**）：`m13_v57_s0_endpoint_model.json` `614bc90740cfbb31` 的 `connector_audit`（`checked=68`）= J2 数据扇 32 条 + J3 18 + J4 18；`chip_audit.pass_through=4`（= J3/J4 的 REFCLK_P/N）。**J2 侧 REFCLK 4 条（REFCLK0/1 × P/N）不在审计内**（其 endpoint source = `s0_method_net_join`）。按 1.2 真源，这 4 条若审计**会 PASS**（11/12/29/30 与真源逐一吻合）⇒ 纯记账缺口，不是缺陷。建议后续以**版本化 addendum** 补齐（不改原件，以免破坏 manifest 的 `inputs_sha` 钉值）。

## 5. 下一步
1. **待 owner 裁定 (A)/(C)**。
2. **(A)** ⇒ handoff §8.2 三步：① 见证件 v2（版本化；keepout 须含数据扇 F.Cu 接入铜包络 + 逐 page 接入窗口）→ ② 引擎 `refclk_place()` 修订（rev bump `W3-CN.38`）→ ③ 重跑 G4→G7，期望 **new 60→0**（验收：仅 REFCLK 族消失、数据/其他保持 0、无 <0.075 项消失）。
3. **(C)** ⇒ ① SPEC spec-rev-3（放开 REFCLK 逃逸区/单次换层，附 In2 共走廊量化代价）→ ② `.kicad_dru` v2（去掉 REFCLK 排除，域限 J2 逃逸区）→ ③ In2 余量闭式核 → ④ 引擎 rev → ⑤ 重跑 G4→G7，同样期望 new 60→0。
4. `new=0` ⇒ **D4 milestone tag**（`pm_gate/TAG_POLICY.md`）；每步收尾：ledger + tag + handoff 续更。
