# 变更单 — SPEC-REV-3 应用记录（ECO：REFCLK J2 侧 pad 场 transit 的过孔/层策略）

> 2026-09-12｜依据 `m13_v57_CO40_refclk_j2_transit_l2_ruling.md`（`7be78b59cdff4380`）
> ｜权限：**L2**（走廊分配 / 过孔策略 / 资源层 = L2；见 `_shared/docs/LAYOUT_CONSTITUTION.md` 第二章 + 引擎 `legal_escape_hatches[3]`）

## 1. 应用方式（原件不动）
- **新版本化文件**：`pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-3.json`（`2d6dbd8bd8d667d7`）。
- **发射器**：`tools/p3_v57_co40_emit_spec_rev3.py`（确定性：`sort_keys` + indent=1；零搜索，常数全部来自 CO-40 §2 闭式规格）。
- 原 `SPEC_k2_v4.json`（`0bd52ed48e720b8c`）与 `SPEC_k2_v4.spec-rev-2.json`（`0a7ad112ac4c57e3`）**逐字节未动**。

## 2. 增量（仅声明字段）
| path | from | to |
|---|---|---|
| `spec_version` | `1.1.spec-rev-2` | `1.1.spec-rev-3` |
| `constraints.escape_transition_zone.refclk_j2_transit` | — | **新增**（ECS-001 闭式规格：`layer_seq F.Cu→In2.Cu→F.Cu`、`max_vias_per_line 2`、`no_via false`、`via1_x 133.825`、`via2_x_max 131.525`、`pad_edge_clearance_mm 0.3`、`in2_channel_x [130.5925,131.5475]`、`skew_compensation`） |
| `constraints.escape_transition_zone.no_via` | `true` | `true`（语义收窄：域默认仍禁 via，`refclk_j2_transit` 为**显式唯一例外**） |
| `constraints.refclk_isolated_scope` | — | 新增：隔离 = **J2 逃逸区外**；区内仅允许 ECS-001 单次换层 |
| `corridors[EAST_CHIP_TO_J2].bands[refclk].j2_transit` | — | 新增注记（`layer` 仍 `F.Cu`、`tracks_y` **未改**） |

**明确的"未改"**：`stackup` / `impedance` / `net_classes`（PCIe85 仍 0.175）/ `vias`（含 `max_per_line`、`pad_edge_clearance_mm`、`no_via_in_pad`、`back_drill`）/ `pd` / 其余 corridors & bands / 其余全部字段。
⇒ **本 ECO 不放宽任何数值净距阈值**（0.075 仍是域内既有值，未扩大适用范围）。

## 3. 与既有 `vias.high_speed.basis` 的一致性
SPEC 原文 basis 已声明受控过孔机制 = **"每线 ≤2 过孔 = 单次换层 (F→In2→F)，每对差分 4 过孔"**。ECS-001 正是该机制：REFCLK 每根 N 线恰 2 个 via（一对 4 个），单次 F→In2→F。故本 ECO 是**已在册机制的适用范围澄清**，而非新机制。

## 4. `.kicad_dru` 不改（相对 CO-40 §3 第 2 条的收窄）
CO-40 曾拟发 `.kicad_dru` v2 去掉 `ESC_J2` 域的 REFCLK 排除。复核实测后**决定不发**：
- 新 transit 的实测铜距（via#1 距两侧 pad 边 0.35；via#2 距内列 0.375/0.755；In2 通道两侧 0.375；跨 131.65 列端 0.2475）**全部 ≥ shop 0.175**，无需 0.075 域内放宽；
- 保留 `!(NetName=='PCIE_REFCLK*')` 排除可**维持 `refclk_isolated` 的隔离意图**（REFCLK 不搭顺风车共享放宽）。
⇒ `.kicad_dru` 维持 `3148703240d54420`（CO-37 版），判据面更小。

## 5. 引擎消费（下一步，未在本批落地）
引擎 `tools/p3_v57_w3_constructive.py` 的 REFCLK 页 `refclk.pad_field_transit` 须由 `"delegated to connector side (W2/R3-R4)"` 改为 ECS-001 闭式形状（含 `via1/via2` 坐标与 In2 waypoints）；同日更新其 `F["spec"]`/`FROZEN_SHA["spec"]` 指向本 rev-3 并 bump `REVISION_CO16`，然后重跑 G4→G7（**验收 new 60→0**）。

## 6. rollback
删除 `SPEC_k2_v4.spec-rev-3.json`；引擎/验证器 `FROZEN spec` 指回 `SPEC_k2_v4.json`（`0bd52ed48e720b8c`）或 rev-2（`0a7ad112ac4c57e3`）。原两版文件始终未动。
