# G7 / L5 记录 — k2 v57（8L）

> 2026-09-12｜revision **L5-G7.3**｜图纸 **W3-CN.37** `37d2d05db8418526`｜本件取代旧版（旧版 `new=426`/W3-CN.30 内容；历史见 git）
> 产生：`tools/p3_v57_l5_signoff.py`（KiCad 10.0.5）+ 逐对差分复核（CO-23 §4）

## 1. 结论
- **SI（对内等长）：PASS** — `max_intra_pair_skew_mm = 0.0031 ≤ 0.15`。
- **DFM/DFT：FAIL** — `new_total = 73`（shop 规则 `k2_v4_8L.kicad_pro` 口径）。**G7 保持 OPEN**。
- 处置：**D3 独立变更单**（既有 `PCIE_REFCLK0/1` 路线族 73 条；本批 CO-23 已消 `copper_edge` 与 `hole_to_hole`）。

## 2. 量（8L）
| 项 | 值 |
|---|---|
| copper layers | 8 = F/B/In1..In6（In1/In3/In5=GND、In4=P3V3 平面未动）|
| tracks / vias | 2408 / 248（同点叠层合并；drill 全部 0.2）|
| SI | width 0.205 ✓；skew 0.0031 ✓（rule 0.15）|
| EMC | 信号层 F/In2/In6/B（LID.1 8L）；参考平面邻接闭合 |
| DRC baseline（冻结 8L 空板）| 42（lib_footprint 12 + mismatch 29 + silk 1，既有）|
| DRC L4 | 115（= 42 既有 + 73 新）|
| **new violations** | **73** = `clearance 18` / `tracks_crossing 5` / `shorting_items 8` / `solder_mask_bridge 42`；**`copper_edge_clearance 0`、`hole_to_hole 0`** |

## 3. 归因（逐对差分，OLD = `53fde64` 的 L4 板）
- 移除 28 = **D1+D2 15**（`copper_edge` 12：`PCIE_DN0_N`×4/`PCIE_DN7_P`×5/`PCIE_UP3_N`×3；`hole_to_hole` 3：`UP2_P`/`UP6_N`/`UP7_P`）+ REFCLK 族重分类 13；
- 新增 13 **全部**为既有 REFCLK 族（`tracks_crossing` 5 / `shorting` 4 / `clearance` 4）；
- ⇒ 73 全为 **D3**（`PCIE_REFCLK0/1` × 数据 pad/GND/P3V3；样例 `REFCK0_N × DN_OUT0_*`）。自网（32 页数据网）**零新增违规**。

## 4. 独立复算
- `p3_v57_co11_placement_verify.py`（自带几何核）：32 页 / 320 via / 320 段 / **0 违规 PASS**（`m13_v57_co23_placement_verification.json` `ebb804cce35ac494`）；
- `p3_v57_w3_constructive_validator_v2.py`（W3-VALv2.4）：段冲突 total=0、via 违例 0（min inter-net 0.595）、A1.3 0 viol；
- 跨层口经由 `kicad-cli pcb drc`（KiCad 10.0.5）给出。

## 5. 指纹
图纸 `37d2d05db8418526`｜landing `78c0e181ee64ee0a`｜G5 validation `8de4d423df203d4b`（W3-VALv2.4 PASS）
｜ALLOC.4 `e5d30cd4eac83e16`｜L4 construction `ca9becc1593028c0`｜L4 validation `1571aac4b3b78a99`（L4-A..E PASS）｜L4 板 `70f3fdc4149db146`
｜fab `fb1f921f4bf476c3`｜dfm `f3f23a07a98dd7ed`｜si `f1f5cc48002cdb28`
冻结四源 `0bd52ed48e720b8c / a8ef3ea8ecff99d7 / fb07d25ac426ff84 / 0a459839e15960b8`（未改）。
