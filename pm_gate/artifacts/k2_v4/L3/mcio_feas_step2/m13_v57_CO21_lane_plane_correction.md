# CO-21 — 【L2 更正】lane 平面重整：**机制更正**（非 pair 域耦合，而是东侧 J2 stub/landing 几何耦合）

> 2026-09-12｜裁判：ARCHER（L2，自裁）｜性质：**更正裁定**（更正 `m13_v57_CO20_lane_plane_pairdomain_coupling.md` 的机制与结论）

## 0. 更正点
CO-20 断言「冻结 pair 域 v1.5 的候选行与 lane 平面强耦合 ⇒ 须重派生 pair 域 v1.6」。**机制错误**：
`m13_v57_f13_r1_pair_coupling_v1_5.json` 的候选行由**冻结 via verdict r2**（`m13_v57_s1_r1_via_verdict_r2.json`）派生，
与 lane 平面**无关**（生成器 `p3_v57_f13_pair_coupling_r2_v5.py` 只读 verdict/manifest/pad_field/v1.4）。
⇒ **无需** pair 域 v1.6。

## 1. 实际机制（实测）
东侧 lane 带（16 页，idx 16..31）位置一变，**东侧 stub 竖段长度与 lane×escape/stub 交叉关系随之改变**，
在**冻结候选行集**内产生**跨页净距/交叉冲突**（顺序敏感）：

| 失败样例（`CO10_EDELTA=0.17`，order=rev） | 冲突 |
|---|---|
| `PCIE_UP0/out_J2` | `vt2_placed` (In6 lane × `PCIE_UP7/out_J2.N` 0.417)、`vt_placed` 0.2、`vv_placed` 0.45、`vv_intra` (P×N 同页 0.45) |
| `PCIE_DN5/input` | `vv_placed` 0.39 (× `PCIE_UP2/out_J2.P`) |

## 2. 扫描证据（满足板边带 ⇒ 恒缺页）
东侧须 `top lane_y ≤ 78.6475`（`base=33.3+31·STEP`，`+POL_OFF 0.25`）。
| STEP | EDELTA | 东 top lane_y | 最好 placed（4 种 order：engine/laneidx/rev/fewest）|
|---|---|---|---|
| 1.46 | 0 | 78.810 ✗ | **32/32**（但越板边带）|
| 1.46 | 0.05 | 78.760 ✗ | 32/32 |
| 1.46 | 0.10 | 78.710 ✗ | 31/32 |
| 1.456 | 0.00/0.05/0.10 | 78.686 ✗ / 78.636 ✓ / 78.586 ✓ | 31/32 |
| 1.452 | 0/0.05/0.10 | 78.562/78.512/78.462 ✓ | 31/32 |
| 1.448 | 0 / 0.05 / 0.10 | 78.438/78.388/78.338 ✓ | 31/32 / 30/32 / 31/32 |
| 1.444 | 0 / 0.05 / 0.10 | 78.314/78.264/78.214 ✓ | 30/32 / 31/32 / 31/32 |

**结论**：在冻结候选行集 + 现东侧 stub/landing 几何下，**「满足板边带」与「32/32 可落位」不可同时成立**（恒缺 ≥1 页）。
这不是 pair 域问题，而是**东侧 band 位置 × J2 stub/landing 几何**的联合约束。

## 3. 已确证的可行部分
- **西侧 lane 平面抬升**（`WLO=33.65/34.0`）：**32/32** + `p3_v57_co11_placement_verify.py` **320/320 0 违规 PASS** ⇒ 西侧 `copper_edge` 可单独消。
- 东侧须与 **J2 stub/landing 派生**（`r3_build` 的 east 分支 / `land_x`）**同批**重派生，或改用**东侧 lane 索引置换**（把 x 跨度大的页放到低 lane）+ 相应 stub 重派生。

## 4. 下一步（L2；单一批次）
1. **东侧联合重派生**（任选其一，均为 L2）：
   (a) lane 带压缩/下移 **与** 东侧 stub/landing y 同步重派生（保持 stub 长度与交叉关系不变，仅整体降 0.16-0.2）；
   (b) **东侧 lane 索引置换**：按页 x 跨度排序分配 idx，使 `PCIE_DN7` 等大跨度页不落在 top lane。
2. 探针复跑 → 32/32 + 独立复核 PASS → 发 `CO16-ALLOC.3` → 引擎 `CO16_ALLOC` + REVISION bump → G4..G7。
3. `hole_to_hole` 3 项：在 (1) 的新平面上加 `CO10_HOLE_GAP=0.4495` 一并解（CO-20 扫描显示其与旧平面冲突；新平面须同时纳入）。
4. `PCIE_REFCLK0/1`（74）独立变更单。

## 5. 未改物
冻结四源、canonical（W3-CN.35 `248b504c4cca8f49`）、ALLOC.2 均未动。本件仅为**机制更正 + 有序下一步**。
