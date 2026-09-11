# CO-19 — 【L2】CO16-ALLOC.2（板内 fan）+ DFM 残留精确归因裁定

> 2026-09-12｜裁判：ARCHER（L2：走廊分配/过孔策略/等长，自裁）｜性质：**变更单 + 归因**
> ｜引擎 rev **W3-CN.35**｜canonical `248b504c4cca8f49`｜ALLOC.2 `236c72bc7d228fbf`

## 0. 本周期结果
1. **CO16-ALLOC.2**：`CO10_FANY_J3=34.5,51.5`（原 31.5 出板；板 bbox y∈[32.95,79.05]）→ 西 J3 上排 landing 回到板内（min landing y=34.5）。
   探针 32/32 + `p3_v57_co11_placement_verify.py` **320/320 0 违规 PASS**（`35e9b0c67a766a96`）。
2. **引擎 W3-CN.35**：`FEASIBLE_ALL`，certs=0，crossings 0/0，A-CN.9 0/0/0，320 via，**max|skew| = 0.00000mm**，三序逐字节，wall ≤120s。
3. **G4/G5/G6 PASS**（validator W3-VALv2.3 PASS；L4 248 via；L4-A..E viol=0）。
4. **G7 SI PASS**（`max_intra_pair_skew_mm = 0.0`）；**DFM new 426 → 91**（ALLOC.1 为 103；`tracks_crossing` 1→0）。

## 1. DFM 残留归因（实测于 ALLOC.2 L4 板；逐项含坐标/网名）
| 簇 | new | 归因（证据） | 处置层 |
|---|---|---|---|
| `copper_edge_clearance` | **14** | **lane 平面超出板边净空带**：西最低 `PCIE_UP3/input N` lane y=**33.05**（WLO 33.3 − POL_OFF 0.25；下缘 32.95+0.3+0.1025 ⇒ 需 ≥**33.3525**）；东最高 `PCIE_DN7/input P` lane y=**78.81**（base 78.56 + 0.25；上缘 79.05−0.4025 ⇒ 需 ≤**78.6475**）。lane 中心可用带 45.295mm **<** 实际跨度（东 31·1.46+0.5=45.76；西 31·1.1265+0.5=35.42 但下限由 POL_OFF 定） | L2（lane 平面重整） |
| `hole_to_hole` | **3** | (a) 同页 via1×corner 竖向过短：`PCIE_UP6/input N` `|lane_y−via1_y|`=**0.039mm**（需 ≥ 0.2+0.2495=0.4495）；(b) 2× 同页 via 对 0.18/0.32mm。A-CN.9 的 vv 对**同网豁免**，KiCad `hole_to_hole` **不豁免** ⇒ 判据缺口 | L2（引擎判据 + lane_y/via1_y 间距） |
| `shorting_items` 15 + `solder_mask_bridge` 42 + `clearance` 17 | **74** | **既有 `PCIE_REFCLK0/1` 路线**与 J2/J3/J4 数据 pad、GND、P3V3 冲突（样例：`PCIE_REFCLK0_P` × `PCIE_DN_OUT0_P_MCIO` @(64.0,51.5)–(82.35,45.71)；`REFCK1_N`×`REFCK1_P` @(135.0,51.49)–(132.65,51.3)） | 既有 refclk 布线（独立工作流；非 CO-16 拓扑） |

**合计 91 = 14 + 3 + 74。**

## 2. 下一步（L2 自裁，按收益排序）
1. **lane 平面重整（消 14）**：东 lane 步距 1.46 → **≤1.445**（中心带需 ≤45.295mm）或整平面临时平移；西最低 lane 需 ≥33.3525（即 `WLO ≥ 33.61` 或改用对称 POL_OFF）。须同批复验 A-CN.2b（双端谓词 ≤45.4）与 corridor 容量。
2. **引擎补同网钻孔间距判据（消 3）**：`vv` 对**同页同极性**不再豁免到 0（改 ≥0.4495 drill-edge 口径），并约束 `|lane_y − via1_y| ≥ 0.4495`。
3. **REFCLK 路线整改（消 74）**：属既有 refclk 走线，产出独立变更单。

## 3. 红线遵守
冻结四源**原件未动**（ECO SPEC-REV-2 走版本化新文件 `0a7ad112ac4c57e3`）；零坐标搜索（AST while=0）；未放宽阈值；无 partial pass / sign-off；证据落 ledger。
