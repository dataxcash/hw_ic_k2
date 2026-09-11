# CO-23 — 【L2 自裁】板边真带（33.0/79.0）落地：D1 `copper_edge` 12→0、D2 `hole_to_hole` 3→0；DFM new 88→73（余=REFCLK 独立变更单）

> 2026-09-12｜裁判：ARCHER（L2：叠层/走廊分配/过孔策略/等长，自裁）｜引擎 **W3-CN.37**｜分配工件 **CO16-ALLOC.4** `e5d30cd4eac83e16`
> 取代：`m13_v57_CO22_lane_plane_partial_landing.md`（其「残留 12 = 西 33.4 + 东 78.619」只覆盖 8/12，且未识别同网钻孔距属西侧）

## 0. 更正 CO-22 的两处口径

1. **`copper_edge_clearance 12` 有三源（CO-22 只报 2 源）**：实测板边 **x=143.0** 亦为 Edge.Cuts 实线。
   | 源 | 条数 | 机理 |
   |---|---|---|
   | 西最低 lane 33.4 | 3 | `PCIE_UP3_N` 逃逸/落位/run 三件皆越带（真带下界 33.4025，差 0.0025） |
   | 东最高 lane 78.619 | 5 | `PCIE_DN7_P` escape/stub/2 via/run（真带上界 78.5975，超 0.0215） |
   | **J2 外列 x=142.6** | 4 | `PCIE_DN0_N` land(F.Cu)+via+stub+run：`136.0+0.6*11=142.6`，边界 143.0 ⇒ 0.2975/0.2250（**CO-22 未识别**） |
2. **`hole_to_hole 3` 全为西侧，且分两类**（CO-22 归因于东侧带 × stub/landing 耦合）：
   | 项 | 机理 |
   |---|---|
   | `PCIE_UP2_P` | 同页同极性 **drop(lane)↔land** 竖段 0.0865：lane 33.4 起带后 lane_y 恰压 J3-U landing 行 `FANY_J3[U]=34.5` |
   | `PCIE_UP6_N` / `PCIE_UP7_P` | 同页同极性 **via1↔corner** 逃逸竖段 0.311/0.3325：西 lane 带顶（49.2/50.3）与芯片 pad 行（49.76/50.28）重叠 ⇒ 逃逸段被压至 < 0.4495 |

## 1. 三条根因（本次裁定）

- **R-A（东 y 带）**：东 lane 平面整块下移（`EDELTA -0.15 → -0.10`）即可（32/32、上界 78.569）。**无需**东侧索引置换（CO-22 §2 的 (a)/(b) 选项均不需要）。
- **R-B（x 带）**：J2 **落列步长 0.6→0.58**（外列 `136.0+0.58*11=142.38`，含 via 半径离边 0.445 ≥ 0.3）。
  区间图着色色数不变（外/内各 12 色），仅步长收紧。
- **R-C（西侧同网钻孔距 · 结构根因）**：西 16 条 lane 的 y 跨度（≥15×1.025）**必然**跨越 J3-U 的 landing 行 34.5 与芯片 pad 行 49.76/50.28：
  - landing 行固定在 connector 侧 ⇒ 「lane_y 距所属页 landing ≥0.4495」只能在**索引分配层**解，不能靠挪带；
  - lane 带顶若进入 pad 行 ⇒ 逃逸竖段被压到 <0.4495，且 corner via 落进 pad 阵列。
  裁定：**把西 lane 带整体压到 pad 行之下**（`WLO 33.70 / WSTEP 1.05`，带 33.45..49.70，顶值低于 49.76 行 0.06）+ **定点置换**（帧序位置 1 的 lane 必在 `34.5±0.4495` 内，且 J3-U/J3-L/J4-L 三组共享落列均不可用 ⇒ 只可与无共享落列的 J4-U 页交换：`WSWAP=1-11`，UP2 ⇄ DN7）。

## 2. 落地参数（CO16-ALLOC.4；全部为 L2 参数）

| 参数 | 值 | 事由 |
|---|---|---|
| `CO16_STEP` | 1.449 | 沿用 CO-22 |
| `CO16_EDELTA` | **-0.10** | R-A：东带下移，上界 78.569（余量 0.0285）|
| `CO16_WLO` / `CO16_WSTEP` | **33.70 / 1.05** | R-C：西带压下（下界 33.45，余量 0.0475）；相邻 lane 交叉极性 via/run 间距 = 1.05-0.5 = 0.55 ≥ 0.525 |
| `CO16_J2STEP` | **0.58** | R-B：x 带 |
| `CO10_WSWAP` | **1-11**（UP2 ⇄ DN7）| R-C 定点置换 |
| `CO10_COLMODE=pol` | 开 | J2 落列区间图改用**该 pad 实际极性 via y**（`lane_y + pol_off`）——修 P/N 偏移 0.25 导致的同色列漏判 |
| `CO10_HOLE_GAP` | **0.4495** | 同网钻孔距判据：逃逸竖段（via1↔corner）+ 落位竖段（drop↔land），同点叠层（<1e-6）除外（L4 合并为单孔）|
| 其它 | `FANY_J3=34.5,51.5`、`STUB=J3L`、`POLMODE=lx`、`EASTSPLIT=in2c`、`PAIR=v1.5` | 沿用 CO-22 |

**引擎同批**：`BOARD_Y_MIN/MAX 32.95/79.05 → 33.0/79.0`（板边真带 `[33.4025,78.5975]`，蛇形顶点钳位口径随之更正）；`CO16_ALLOC → ALLOC.4` + sha 强校验；`REVISION_CO16 = W3-CN.37`。

**判据强化（工具层，默认关、保旧修订逐字节可复现）**：探针 `check()` 增 `hh_intra`（同极性 via 对 ≥ `CO10_HOLE_GAP`，同点叠层豁免）；探针 J2 着色增 `CO10_COLMODE=pol`；探针增 `CO10_WSWAP`；`p3_v57_co16_emit_allocation.py` 透传三旋钮（仅显式指定时写入 `config`）；验证器 v2.4 的 G-M4 改按引擎 `inputs_sha` 解析 lane 工件（不再硬编码修订号）。

## 3. 门控链

| 门 | 判定 | 证据 |
|---|---|---|
| G4 / W3 | **PASS** | canonical `m13_v57_w3_joint_assignment.json` = **W3-CN.37** `37d2d05db8418526`，FEASIBLE_ALL，certs=0，crossings 0/0，work 546/546 |
| G5 / W4 | **PASS** | `m13_v57_w3_validation.json` = **W3-VALv2.4** PASS（G-M1..M6、A1.2 三序逐字节、A1.3 0 viol、A1.4、frozen、metric 0、via_viol 0；G-M4 min inter-net via = 0.595） |
| G6 / L4 | **PASS** | `m13_v57_l4_validation.json` L4-A..E viol=0（68 网/2408 段/248 via）；板 `k2_v4_8L.l4.kicad_pcb` `70f3fdc4149db146` |
| G7 / L5 | **SI PASS / DFM FAIL(new 73)** | SI skew 0.0031；DFM `new 73 = clearance 18 + tracks_crossing 5 + shorting 8 + solder_mask_bridge 42`（**copper_edge 0 / hole_to_hole 0**）|

## 4. G7 归因（**逐对**差分，OLD = `53fde64` 的 L4 板，同一 `k2_v4_8L.kicad_pro` 口径）

**移除 28 条**（`88 → 88-28+13 = 73`）：
- **D1+D2 = 15**：`copper_edge_clearance` ×12（`PCIE_DN0_N`×4 / `PCIE_DN7_P`×5 / `PCIE_UP3_N`×3）+ `hole_to_hole` ×3（`PCIE_UP2_P` / `PCIE_UP6_N` / `PCIE_UP7_P`）；
- **REFCLK 族重分类 = 13**：`shorting_items` ×11、`clearance` ×2（`GND×PCIE_DN_OUT7_N_MCIO`、`PCIE_DN_OUT7_N_MCIO×PCIE_DN_OUT7_P_MCIO`）——同物理对随几何微移改变了 KiCad 报类。

**新增 13 条**，**全部为既有 `PCIE_REFCLK0/1` 路线族**（非 CO-16 拓扑）：`tracks_crossing` ×5、`shorting_items` ×4、`clearance` ×4；涉及网络仅 `PCIE_REFCLK0/1_P/N` × `PCIE_DN_OUT*_MCIO` / `PCIE_UP_OUT*_J2` / `GND` / `PCIE_REFCLK*` 自对。

⇒ **本变更未在自网新增任何违规**；`new 88 → 73` 的净减 15 = D1+D2 全消，余 73 即 D3（既有 REFCLK 布线），分类随几何重排但总数不变（42 mask 不变）。

## 5. 未决项

| # | 项 | 现状 | 下一步 |
|---|---|---|---|
| D3 | REFCLK 族 73 | 既有 `PCIE_REFCLK0/1` 路线 × 数据 pad/GND/P3V3（样例 `REFCK0_N × DN_OUT0_*` @(64.0,51.5)–(82.35,45.71)）| **独立变更单**（改既有 refclk 布线；非本批） |
| D4 | 里程碑 | DFM new=0 未达 | D3 消后重跑 G4→G7 → milestone tag（`pm_gate/TAG_POLICY.md`） |
| 备注 | 既往溯源瑕疵 | `m13_v57_co16_channel_allocation_v3.json` 记录的 `verification.sha16=1d05c2bf…` ≠ 现盘 `m13_v57_co22_placement_verification.json` 实算 `7ab00c86…`（该复核件在 ALLOC.3 发射后被重生成，几何内容一致）| 后续合并/重发射时统一 |

## 6. 红线 / 未改物
冻结四源**未改**：`SPEC 0bd52ed48e720b8c` / `manifest a8ef3ea8ecff99d7` / `k2_v4_8L.kicad_pcb fb07d25ac426ff84` / `drc_rules 0a459839e15960b8`。
零坐标搜索（引擎 AST 无 while/无回填）；一次求解；未放宽净距/等长阈值；GND/PWR 平面未动；无 partial pass / 无伪造 sign-off。

## 7. 指纹
引擎 W3-CN.37｜canonical `37d2d05db8418526`｜landing `78c0e181ee64ee0a`｜W4 `8de4d423df203d4b`（A1.2 `cee5b80e1f618e1b` / A1.3 `c18c818a634622b6` / A1.4 `fb52613c9751c122`）
｜ALLOC.4 `e5d30cd4eac83e16`｜CO-23 geom `6c0ff05c7e9c2d90`｜CO-23 verify `ebb804cce35ac494`（320/320，0 违规 PASS）
｜L4 construction `ca9becc1593028c0`｜L4 validation `1571aac4b3b78a99`｜L4 板 `70f3fdc4149db146`
｜L5 fab `fb1f921f4bf476c3`｜dfm `f3f23a07a98dd7ed`（new 73）｜si `f1f5cc48002cdb28`（skew 0.0031）

## 8. 独立复核（续接会话 ARCHER-2，2026-09-12）
本裁定由**另一会话独立重放**后收口入库（原会话在 CO-23 完成后 context 耗尽、未提交）：
- **引擎逐字节复现**：`python3 tools/p3_v57_w3_constructive.py --r1-5-shape co16 --out TMP --landing-out TMP`
  ⇒ `37d2d05db8418526` FEASIBLE_ALL（certs=0, crossings 0/0, work 546/546，A-CN.1..9 全 PASS）；landing `78c0e181ee64ee0a` 逐字节同。
- **分配工件复现**：探针 32/32；`p3_v57_co11_placement_verify.py` 320 via/320 段/0 违规 PASS；`geom` 与 §7 工件**逐页同字节**（仅 dump 元数据字段差异）。
- **W4 复现**：validator v2.4 PASS，`8de4d423df203d4b`；A1.2 `cee5b80e1f618e1b` / A1.3 `c18c818a634622b6` / A1.4 `fb52613c9751c122`。
- **L4 复现**：`--board` 重跑 + validator ⇒ L4-A..E viol=0 PASS。**注意**：`k2_v4_8L.l4.kicad_pcb` / `l4_construction.json` **非逐字节可复现**（pcbnew 重存 UUID 重发 + track 次序不同；几何集合相同），故保留 §7 指纹版本（`70f3fdc4149db146` / `ca9becc1593028c0`）。
- **G7 独立 DRC**（同 `k2_v4_8L.kicad_pro` 口径，`kicad-cli 10.0.5`，`--severity-all --refill-zones`）：
  frozen 42；HEAD L4 **new 88 = shorting 15 + clearance 16 + copper_edge 12 + mask 42 + hole_to_hole 3**；
  CO-23 L4 **new 73 = clearance 18 + tracks_crossing 5 + shorting 8 + mask 42**（copper_edge 0 / hole_to_hole 0）。与 §3/§4 完全一致。
- **SI 独立复算**：由 canonical 图纸 P/N 折线长 ⇒ `max|skew| = 0.0031mm`（页 `PCIE_UP2/input`）≤ 0.15。
- **红线复核**：引擎 AST `while=0`；四冻结源 sha 未变；A-CN.9 阈值断言通过（未放宽净距/等长）。
- **既有偏差（非本批）**：`m13_v57_w3_joint_assignment_W3-CN.30.json`（t2 默认）自 ECO SPEC-REV-2 起与引擎现输出不同（HEAD 已如此；t2 现输出 `c2d201f030b49efd`，HEAD 工件 `05f7bd10ab3b45b6`）；本批**未改**该工件，留待统一处置。
