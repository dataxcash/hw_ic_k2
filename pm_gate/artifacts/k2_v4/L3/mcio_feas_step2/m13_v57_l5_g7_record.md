# G7 / L5 记录 — k2 v57（8L）

> 2026-09-12｜revision **L5-G7.5**｜图纸 **W3-CN.38** `0261e0b0a598df6d`｜L4 板含 **SPEC 逃逸区规则域**（CO-37）
> 本件取代旧版（旧版 `new=73`/W3-CN.37、`new=65`/W3-CN.38 内容；历史见 git）
> 产生：`tools/p3_v57_l5_signoff.py`（KiCad 10.0.5，L5-DFM.3）+ 逐对差分复核（CO-36 §16.4 / CO-37 §17）

## 1. 结论
- **SI（对内等长）：PASS** — `max_intra_pair_skew_mm = 0.0031 ≤ 0.15`。
- **DFM/DFT：FAIL** — `new_total = 60`（shop 判据 + CO-37 SPEC 逃逸区域）。**G7 保持 OPEN**。
- 残余 **60 = 100% `PCIE_REFCLK0/1` 路线族**（D3a，上游 W0-R 阻塞）⇒ 里程碑路径唯一化：
  **D3a 几何重派生（60）→ new=0 → milestone**（D3c 已落地，无剩余判据项）。

## 2. 量（8L）
| 项 | 值 |
|---|---|
| copper layers | 8 = F/B/In1..In6（In1/In3/In5=GND、In4=P3V3 平面未动）|
| tracks / vias | 2408 / 248（同点叠层合并；drill 全部 0.2）|
| L4 rule areas（非铜） | 4 = `ESC_J2` / `ESC_J3` / `ESC_J4` / `ESC_U6`（F.Cu；SPEC 逃逸区域）|
| SI | width 0.205 ✓；skew 0.0031 ✓（rule 0.15）|
| EMC | 信号层 F/In2/In6/B（LID.1 8L）；参考平面邻接闭合 |
| DRC baseline（冻结 8L 空板，无 `.kicad_dru`）| 42（lib_footprint 12 + mismatch 29 + silk 1，既有）|
| DRC L4 | 102（= 42 既有 + 60 新）|
| **new violations** | **60** = `clearance 8` / `tracks_crossing 5` / `shorting_items 9` / `solder_mask_bridge 38`；**`copper_edge_clearance 0`、`hole_to_hole 0`** |

## 3. 判据变更（CO-37，L2 自裁；实现 SPEC，非放宽）
- 依据：`SPEC.constraints.escape_transition_zone`（ECN-001，`escape_clearance_mm=0.075`）+ CO-25 §3 裁定（域 = J2/J3/J4/U6 pad 场）。
- 实现：`k2_v4_8L.l4.kicad_dru`（版本化规则文件）+ 板上 4 个具名 rule area（域工件 `m13_v57_co37_escape_domain.json` `5616a9f873c9b844`，pad 场 bbox + 0.5mm，F.Cu）。
- **REFCLK 排除**：`SPEC.constraints.refclk_isolated=true` ⇒ 条件内 `!(A/B.NetName == 'PCIE_REFCLK*')`，REFCLK 冲突不享受放宽（属 D3a 几何缺陷）。
- 域外维持 shop/netclass（PCIe85 0.175 / POWER 0.2）；冻结基线板不加载 `.kicad_dru`（判据变更仅随 L4 实现）。
- 量纲校验：SPEC 以铜距 0.075 计 ⇒ 实测准入项间隙 0.1211–0.1522mm（≥0.075，且 ≥ JLC 线距极限 0.10）。

## 4. 归因（逐对差分）
- **CO-36（几何，D3b）**：OLD = `70f3fdc4149db146`（CO-23 L4）→ 消 8 条 J4 焊盘场数据件（`DN_OUT4/5/6` land），其铜距已 ≥ shop 0.175。
- **CO-37（判据，D3c）**：OLD = `5e8d88d405126014`（W3-CN.38 L4，无域）→ **消 5 条数据逃逸区 clearance**（`J2 19/70/71/16 × UP_OUT4_N/DN7_P/DN7_N/UP_OUT3_N`、`R3.2 × UP3_N`，实测 0.1211–0.1522），**0 新增**；`unconnected` 348 不变；总 65→60（连跑 2 次稳定，无域重建板亦稳定 65）。
- REFCLK 族总数为 **60**（净不变）：其条目/报类归属随 KiCad 分组在同一几何下抖动（±4，clearance↔shorting；已证 REFCLK 铜几何两版 18 基元逐项相同），**非几何变化**。

## 5. 独立复算
- `p3_v57_co11_placement_verify.py`：32 页 / 320 via / 320 段 / **0 违规 PASS**（centerline `add6f9918a17ea3d` 与 `CO11_PAD_UNITS=copper` `03fad029e6709f28` 双口径）；
- `p3_v57_w3_constructive_validator_v2.py`（W3-VALv2.4）：PASS（`b0ff500448e7b54b`，G-M1..6 True）；
- `p3_v57_l4_validator.py`：L4-A..E viol=0 PASS（`9bbb15fc88b2723f`）；
- 跨层 DRC 由 `kicad-cli pcb drc`（KiCad 10.0.5，`--severity-all --refill-zones`）给出，逐对差分含位置键。

## 6. 指纹
图纸 `0261e0b0a598df6d`｜landing `6a42a329a0e75a31`｜G5 validation `b0ff500448e7b54b`｜A1.2 `454df5b5abb905ee`
｜ALLOC.5 `0bf6cdc203887a48`｜CO-36 geom `6610557070a37960`｜CO-36 verify `add6f9918a17ea3d`｜CO-36 copper audit `03fad029e6709f28`
｜域工件 `5616a9f873c9b844`｜`.kicad_dru` `3148703240d54420`
｜L4 construction `d65cbcf8a993f2c5`｜L4 validation `9bbb15fc88b2723f`｜L4 板 `9e6b4839669e941a`
｜fab `b572226abd5bb8ea`｜dfm `7790f0eb2f4c256b`｜si `03cc5b67430fb3e8`
冻结四源 `0bd52ed48e720b8c / a8ef3ea8ecff99d7 / fb07d25ac426ff84 / 0a459839e15960b8`（未改）。
