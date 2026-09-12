# CO-99（L2 自裁 · PDN 施工就绪性）计划集**互相冲突**闸 + 施工 dry-run 取证 —— 新缺陷类：既有 PDN 闸的**覆盖缺口**

> 日期 2026-09-12｜工具 `tools/p3_v57_co99_pdn_mutual_conflict_gate.py` `73860501ec7ffea3`
> 记录 `m13_v57_co99_pdn_mutual_conflict_gate.json` `aef9f5be5282e06b`
> 基线：SPEC rev-11 `d85f10f722ba22b0`｜板 `0e636a67c1472462`（**交付板逐字节不变**；dry-run 用 scratch 副本）
> **verdict = `FAIL_MUTUAL_SHORT`**

## 1. 新缺陷类（为何此前全绿）
所有既有 PDN 闸（CO-88 引用/覆盖、CO-91 净距、CO-92 修复候选、CO-95 可达性、CO-98 义务状态）与 CO-96 非执行者复评，
**都只判「计划几何 vs 板*已有*铜」**。CO-91 的 `Scene` 仅由板的 pads/segs/vias 构成 ⇒ **对「计划集*互相*（via-via / stub-via / stub-stub）零判**。
⇒ **CO-91 PASS 不蕴含可施工**。本件把工件驱动过其真实消费面（`eda_core.pdn_apply` + `kicad-cli pcb drc`）后坐实。

## 2. 机判结果（确定性；半径/宽度 = `pdn_apply.VIA_DIA=0.35` / SPEC `stub_width_mm`）
| 量 | SPEC 声明宽 **0.2mm** | `pdn_apply` 实落宽 **0.5mm** |
|---|---|---|
| 异网 **overlap（=短路）** | **7**（3 via-via + 4 stub-via） | 13 |
| 异网净距违规 | 35（28 via-via + 3 stub-stub + 4 stub-via） | 127 |

- 全部 7 个 overlap 位于 **U6 0.5mm 球栅场**（x∈[84.57,103.03]，y∈[53.5,54.19]），如 `P3V3@(84.775,53.5)` vs `GND@(84.574,53.59)`：**d=0.2202mm < via 直径 0.35mm ⇒ 两 via 重叠 = 电气短路**。
- 牙齿 2/2（合成 0.20mm 对必抓 / 0.60mm 对必放行）。

## 3. 施工 dry-run 取证（scratch 板；`pdn_apply --stage all` = zones 5 / vias 246 / tracks 189 / blocked 60）
| 量 | baseline（未施工） | 施工后 |
|---|---|---|
| kicad-cli DRC violations | **42** | **274**（**+232**）|
| 未连项 | 348 | 191 |

逐类型增量（**参考值**；随 zone refill/UUID 分组浮动，故不入记录）：`clearance` ~124–131、`shorting_items` ~43–47、`hole_to_hole` **37**、`hole_clearance` ~19–22、`holes_co_located` **2**；
其中 `holes_co_located` 两处为 (133.83,59.1) GND×2 与 P3V3_AUX [47.0,49.0]×2 —— **正是 CO-96 曾记为「声明共享单孔/非缺陷」的重坐位**：声明层可解释为共享孔，但 `pdn_apply` 会**逐字落两个 via** ⇒ 实际同址钻孔。

## 4. 根因（三条，均可复现）
1. **计划集互避缺失**：`pad_connect_gen` 逐 pad 独立放置 via/stub，未把**已放置的计划件**当障碍；在 0.5mm U6 球栅场产生异网重叠。
2. **施工侧短段宽未同步**：`pdn_apply.add_track(..., width=0.5)` 为**字面量**，未读 SPEC `stub_width_mm=0.2`（CO-93 §④ 已登记，本件**量化**：0.5→13 overlap / 127 净距 违规；0.2→7 / 35）。
3. **stitch 互距/去重缺失**：`gnd_stitch_gen` 产物不避让自身先前落孔 ⇒ 37 `hole_to_hole`（0.05/0.00mm，需 0.2495）+ 2 `holes_co_located`。

## 5. L2 裁定与归口（不触 L1）
- **属 L2**（过孔策略/PDN 施工就绪性；3 个重叠对全在 U6 BGA 场，**网归属未变** ⇒ 非 L1）。
- **修补路径（二选一，均属后续变更单/施工期引擎）**：(a) **计划集重导**（rev-12）——以「板 + 已放置计划件」为互障、按声明 palette 确定性重放；U6 场若仍无合法位则须归入 CO-94 的 **via-in-pad/HDI** 升级（工艺/L1）；(b) **施工期引擎避让 + 短段宽读 SPEC + 去重/互距**（= 已自裁的「项目内引擎承载」项）。**本件不施加**。
- **闸侧立即可用**：本闸为**计划集互判**，可与 CO-91（板侧重）**并列**作为施工就绪性前置闸（同一规则源）。

## 6. 非声明
只读 SPEC/板（dry-run 用 scratch 副本，交付板**逐字节不变**）；不改 SPEC/板/阈值/冻结源；零坐标搜索、无 while；
本件**不施加**任何修补、**不改** CO-91/92/95 记录；dry-run 的**逐类型明细**为参考值（记录仅存稳定量）。
**对既有结论的影响（如实）**：rev-11 的**布线链**（G4..G7）PASS 不变；但 **PDN 的「可施工」性 = FAIL**，且该结论**不因任何既有闸的 PASS 而撤回**。
