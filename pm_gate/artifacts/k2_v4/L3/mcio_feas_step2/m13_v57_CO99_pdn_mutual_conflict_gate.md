# CO-99（L2 自裁 · PDN 施工就绪性）计划集**互相冲突**闸 + 施工 dry-run —— 两个覆盖缺口

> 日期 2026-09-12｜工具 `tools/p3_v57_co99_pdn_mutual_conflict_gate.py` `5886c684352af019`
> 记录 `m13_v57_co99_pdn_mutual_conflict_gate.json` `83349bbb1f048c8f`
> 基线：SPEC rev-11 `d85f10f722ba22b0`｜板 `0e636a67c1472462`（**交付板逐字节不变**；dry-run 用 scratch）
> **verdict = `FAIL_MUTUAL_SHORT`**

## 1. 两个覆盖缺口（为何此前全绿）
所有既有 PDN 闸（CO-88/91/92/95/98）与 CO-96 复评都只判 **「计划几何 vs 板*已有*铜」**，因此有两处看不见：
- **G1 计划集内部互冲**：CO-91 `Scene` 仅由板 pads/segs/vias 构造 ⇒ **via-via / stub-via / stub-stub 互相零判**。
- **G2 孔-孔（net-agnostic）**：项目规则源 `_shared/eda_core/drc_rules.json` 的 `hole_clearance.same_net_exempt=True`，**不含** KiCad 板配置的 `min_hole_to_hole`；
  而交付板 `.kicad_pro` 有 `rules.min_hole_to_hole=0.25`（severity=warning）且**不分网** ⇒ 同网 stitch via 靠太近在 CO-91 下不可见、在 kicad-cli 下报 37 `hole_to_hole`。
⇒ **CO-91 PASS 不蕴含可施工**。

## 2. 机判结果（确定性；via dia 0.35 / drill 0.2 / SPEC `stub_width_mm`）
| 量 | SPEC 声明宽 **0.2** | 引擎实落宽 **0.5** |
|---|---|---|
| 异网 **overlap（=短路）** | **7**（3 via-via + 4 stub-via） | 13 |
| 异网净距违规 | 35（28 via-via + 3 stub-stub + 4 stub-via） | 127 |

- **孔-孔（net-agnostic，阈值 0.2+0.25=0.45）**：**39** 项，其中 **2 项同址**（co-located）——即 CO-96 曾记为「声明共享单孔/非缺陷」的 `(133.83,59.1)` GND×2 与 `P3V3_AUX [47.0,49.0]`×2。
  声明层可解释为共享孔，`pdn_apply` 仍**逐字落两个 via** ⇒ 同址钻孔。
- 7 个异网 overlap 全在 **U6 0.5mm 球栅场**（x∈[84.57,103.03]，y∈[53.5,54.19]）：如 `P3V3@(84.775,53.5)` vs `GND@(84.574,53.59)`，**d=0.2202 < 0.35mm 直径**。
- 牙齿 2/2。

## 3. 施工 dry-run（scratch；`pdn_apply --stage all` = zones 5 / vias 246 / tracks 189 / blocked 60）
| 量 | baseline | 施工后 |
|---|---|---|
| kicad-cli DRC violations | **42** | **274**（**+232**）|
| 未连项 | 348 | 191 |

逐类型参考（随 refill/UUID 浮动，不入记录）：`clearance` ~124–131、`shorting_items` ~43–47、`hole_to_hole` **37**、`hole_clearance` ~19–22、`holes_co_located` **2**。

## 4. 根因
1. **计划集互避缺失**：`pad_connect_gen` 逐 pad 独立放置 via/stub，未把**已放置计划件**当障碍（G1）。
2. **施工侧短段宽未同步**：`pdn_apply.add_track(..., width=0.5)` 字面量、未读 SPEC `0.2`（CO-93 §④ 的量化）。
3. **stitch 互距/去重缺失**：`gnd_stitch_gen` 不避让自身先前落孔、不去重（G1+G2）。
4. **规则源不含 `min_hole_to_hole`**（G2，见 §1）。

## 5. 归口与非声明
- **修复可行性已由 CO-100 机判**（互障感知 + 孔距约束的声明 palette 重放）：可达 **residual 0**，但需 **6 项新增 blocked**（5 ppc + 1 stitch，**全在 U6 0.5mm 场**）⇒ 属 L2 可解 + U6 场工艺/L1 张力。
- L2（3 个重叠对网归属未变 ⇒ 非 L1）。只读 SPEC/板（dry-run 用 scratch）；**交付板逐字节不变**；零坐标搜索；**本件不施加**。
- **影响**：rev-11 **布线链 G4..G7 PASS 不变**；但 **PDN「可施工」= FAIL**，不被任何既有闸的 PASS 撤回。
