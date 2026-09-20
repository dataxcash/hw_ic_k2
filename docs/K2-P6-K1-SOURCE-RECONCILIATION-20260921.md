# K2 · P6 跨板复用：**K1 同源对账 + 原理图侧残项**（2026-09-21 · 监理自动续推轮）

**性质**：只读审计 + 提案。**未改 `k1/` 任何文件**；**不新增判据维、不主张新增检查齿**（owner ②）；未派 WORKER。

## A. 四源/六件对账（ENG 直读）
| 源 | 件数 | 与板比较 |
|---|---|---|
| 板 `k1/k1_v1.kicad_pcb` | **42** | 基准 |
| `boards/k1_board.yaml#devices` | **42** | 逐件一致 ✅ |
| `boards/k1_pinmap.yaml#pins` | **42** | 逐件一致 ✅ |
| `boards/k1_nets.yaml` 端点 refs | **42** | 逐件一致 ✅ |
| `boards/k1_sch.yaml#sheets[].placements` | **37** | **缺 5** ❌ |
| `k1/sch/*.kicad_sch` refs | **37** | **缺 5** ❌ |

- **唯一失配面 = 原理图侧（输入 + 产物）缺 `Q1 · Q2 · R38 · R39 · U13`**；反向**幽灵件 = ∅**。
- 缺的 5 件在板上均为真实件（ENG 直读封装）：`Q1`=WSON-10-1EP · `Q2`=SOT-23 · `R38/R39`=R_0402 · `U13`=DFN-6；来源见 `k1_board.yaml.reconciliation.sch_sync_v1` 明列的**②补充件**（Q1 轨B 开关 / WORK_EN / SBU 串 R+ESD / SBU 网拆分）。
- ⇒ **权威 = 板侧**（与 K2 E1 同模式：三源 + 板 42/42/42/42 一致，仅原理图侧落后）。

## B. 原理图侧具名残项（**板已修、图仍旧件**）
| # | 级别 | 发现 |
|---|---|---|
| **K1-S1** | **高**（承 BLOCKING 的 **OPEN-1** 在**原理图面**未闭合） | `k1/sch/v5_connectors.kicad_sch` 的 **J1 Footprint 仍 = `USB_C_Receptacle_HRO_TYPE-C-31-M-12`**（16-pin USB2-only，**无 SS 差分焊盘**）；**板上已换** `USB_C_Receptacle_Amphenol_12401548E4-2A`（30 pad，含 **A2/A3/A10/A11/B2/B3/B10/B11** + 4 SH + 2 NPTH）。`k1_board.yaml` 的 OPEN-1 裁定与「yaml 已同步」**只落在板 + yaml**，**原理图侧未同步** |
| **K1-S2** | 中（承 OPEN-2） | `k1/sch/v5_power_…kicad_sch` 的 **U10 Footprint 仍 = `SOT-23`**（3 pad）；**板上 = `SOT-23-5`**（5 pad，与符号 5 pin 匹配）。`open_issues[OPEN-2].action` =『原理图 footprint 修正**待 ECO**』⇒ 该 ECO 未落 |
| K1-S3 | 低 | `k1_board.yaml.reconciliation.device_count` 自述 `schematic_sch_k1: 42 · diff: []`，**与盘上 37 不符**（K2 曾因同类「声明与盘上不符」被点名 ⇒ 建议随再生订正） |

## C. 可复用修法族（仅提案）
与 K2 **E1 四源归零**同族 = **由单一真源再生**：K1 侧真源 = `k1_board.yaml`；已具名生成器 = `k1/pm_gate/tools/k1_sch_sync_v1.py`。
预期：原理图侧 37 → **42**（回填 5 件）+ J1/U10 footprint 同步 ⇒ `refdes_sets_equal` 的 5 件差归零；可一并核算 `k1_nets_yaml_missing_nodes`(7) 与 `nc_pairs` 差 4。
**边界**：修法属 K1 项目改动 ⇒ 需授权；本件未动 k1。

## D. 与 K2 对照（同源面）
K2 已归零：canonical 19 实测 **原理图 54 / 板 54（差 0）** · `lib_electrical_level` 电气级 **0**；**K1 侧仍 37 / 42** 且原理图侧两处封装属性陈旧。

## E. 交件
`K1_SOURCE_RECONCILIATION_AND_SCH_SIDE_RESIDUAL_20260921_v1.json`（`bbee43f7b92ea52a`）
