# G7 / L5 记录 — k2 v57（8L）

> 2026-09-12｜revision **L5-G7.4**｜图纸 **W3-CN.38** `0261e0b0a598df6d`｜本件取代旧版（旧版 `new=73`/W3-CN.37 内容；历史见 git）
> 产生：`tools/p3_v57_l5_signoff.py`（KiCad 10.0.5）+ 逐对差分复核（CO-36 §16.4）

## 1. 结论
- **SI（对内等长）：PASS** — `max_intra_pair_skew_mm = 0.0031 ≤ 0.15`。
- **DFM/DFT：FAIL** — `new_total = 65`（shop 规则 `k2_v4_8L.kicad_pro` 口径）。**G7 保持 OPEN**。
- 处置：**D3a 独立变更单**（既有 `PCIE_REFCLK0/1` 路线族 60 条，上游 W0-R 阻塞）+ **数据/其他 5**（D3c 域判定）+ **D3c**（`.kicad_dru` 逃逸区规则域）。

## 2. 量（8L）
| 项 | 值 |
|---|---|
| copper layers | 8 = F/B/In1..In6（In1/In3/In5=GND、In4=P3V3 平面未动）|
| tracks / vias | 2408 / 248（同点叠层合并；drill 全部 0.2）|
| SI | width 0.205 ✓；skew 0.0031 ✓（rule 0.15）|
| EMC | 信号层 F/In2/In6/B（LID.1 8L）；参考平面邻接闭合 |
| DRC baseline（冻结 8L 空板）| 42（lib_footprint 12 + mismatch 29 + silk 1，既有）|
| DRC L4 | 107（= 42 既有 + 65 新）|
| **new violations** | **65** = `clearance 13` / `tracks_crossing 5` / `shorting_items 9` / `solder_mask_bridge 38`；**`copper_edge_clearance 0`、`hole_to_hole 0`** |
| 归因分类 | REFCLK 族 **60**（仅 REFCLK 11 + REFCLK×数据 49）+ 数据/其他 **5** |

## 3. 归因（逐对差分，OLD = `70f3fdc4149db146`（CO-23 / ALLOC.4 L4 板））
**消 14 / 增 6，净 −8**：
- **消 8 = D3b 数据件全消**（J4 焊盘场 land）：`DN_OUT4 P×N` shorting、`DN_OUT4_N 盲孔 × DN_OUT4_P` clearance、
  `DN_OUT5_N×GND` 与 `DN_OUT5_P×DN_OUT5_N` clearance、`DN_OUT4_P×GND`/`DN_OUT4_P×N`/`DN_OUT6_P×GND`/`DN_OUT6_P×N` mask bridge。
  ⇒ 数据类由 13 → 5（余 5 非 J4 land 场：J2 pad 19/70/71/16、R3 pad 2）。
- **消/增各 4 = 同一 REFCLK 冲突点随 land 列平移**（`DN1 P/N × REFCLK0_N` crossing、`DN6 P/N × REFCLK1_P` shorting；类型/网对不变）。
- **消/增各 2 = J2 逃逸区 REFCLK 报类重归属**（`REFCLK*_N(28.243) × J2 pad 14/32` clearance ↔ `× J2 pad 11/29` shorting）。
  已证 **REFCLK 铜几何两版完全相同**（18 基元逐项一致）⇒ KiCad 分组/归属差异，**非新缺陷**。
- ⇒ 自网（32 页数据网）仅 D3b 8 条被消；`REFCLK0/1` 路线族 60 条保持（D3a，上游变更单）。
- **新增 D3a 证据**：J2 `REFCLK0_P` pad 11 × `REFCLK0_N` 逃逸段真值铜距 **−0.0875mm（实铜重叠）**（pad 29 同值）；两版板相同 ⇒ 既有缺陷。

## 4. 独立复算
- `p3_v57_co11_placement_verify.py`：32 页 / 320 via / 320 段 / **0 违规 PASS**，centerline（`add6f9918a17ea3d`）与 `CO11_PAD_UNITS=copper`（`03fad029e6709f28`）双口径均 0；
- `p3_v57_w3_constructive_validator_v2.py`（W3-VALv2.4）：PASS，G-M1..6 全 True，via 违例 0，A1.3 0 viol；A1.2 序无关（三枚举序同 sha）；
- 跨层 DRC 由 `kicad-cli pcb drc`（KiCad 10.0.5，`--severity-all --refill-zones`）给出，逐对差分含位置键。

## 5. 指纹
图纸 `0261e0b0a598df6d`｜landing `6a42a329a0e75a31`｜G5 validation `b0ff500448e7b54b`｜A1.2 `454df5b5abb905ee`
｜ALLOC.5 `0bf6cdc203887a48`｜CO-36 geom `6610557070a37960`｜L4 construction `512192df1f1e8f84`｜L4 validation `efc07c52a93c08a4`｜L4 板 `5e8d88d405126014`
｜fab `3b91202b1e5dd1a4`｜dfm `9f7158f2634df815`｜si `03cc5b67430fb3e8`
冻结四源 `0bd52ed48e720b8c / a8ef3ea8ecff99d7 / fb07d25ac426ff84 / 0a459839e15960b8`（未改）。
