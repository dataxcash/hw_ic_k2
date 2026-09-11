# CO-20 — 【L2】lane 平面重整实测：与**冻结 pair 域 v1.5 强耦合** ⇒ 需 pair 域 v1.6 重派生（本周期不落地）

> 2026-09-12｜裁判：ARCHER（L2：走廊分配/叠层/过孔策略，自裁）｜性质：**实测归因 + 有序下一步**（未改冻结四源）

## 0. 目标与结论
目标：消 CO-19 的 `copper_edge_clearance` 14（lane 平面超板边净空带）与 `hole_to_hole` 3（同网 via 钻孔间距）。
**结论：两者均不可由现有冻结输入（pair 域 v1.5 + 单侧旋钮）闭合**；须先**重派生 pair 域 v1.6**（新 lane 平面 + 逃逸竖段下限），再重发射分配/引擎。属 L2，无需 owner。

## 1. 需求量化（由 CO-19 归因）
- 板 bbox y∈[32.95,79.05]；0.3mm 板边间距 + 0.1025 半线宽 ⇒ **lane 中心须 ∈ [33.3525, 78.6475]**（跨度 45.295mm）。
- 现西 lane 最低 **33.05**（需 ≥33.3525 ⇒ 西平面抬 ≥0.3025；`WLO ≥ 33.6025`）。
- 现东 lane 最高 **78.81**（需 ≤78.6475 ⇒ 东平面降 ≥0.1625，或东步距 ≤1.445）。
- 逃逸竖段：`|lane_y − via1_y| ≥ 0.2 + 0.2495 = 0.4495`（kicad `hole_to_hole` 0.2495 边距 + 0.2 钻；A-CN.9 的 vv **同网豁免**，故此为判据缺口）。

## 2. 实测（只读探针；`rule=fan order=rev`，其余旋钮 = ALLOC.2）
| 试验 | 结果 |
|---|---|
| 西平面抬升（`WLO=33.65/34.0`，东不动） | **32/32** + `p3_v57_co11_placement_verify.py` **320/320 0 违规 PASS** ⇒ 西侧可单独修 |
| 东平面降（`CO10_EDELTA=0.15..0.25`）或东步距（`CO10_STEP=1.43..1.445`） | **30-31/32**（`PCIE_UP0/out_J2` 必失；另偶失 `DN5/DN3/input`） |
| `CO10_HOLE_GAP=0.4495` 候选过滤（`WLO`×`EDELTA` 28 组合扫描） | 最高 **29/32**（失 `DN5/input`、`UP0/out_J2`、`UP7/input`） |

**根因**：冻结 pair 域 `m13_v57_f13_r1_pair_coupling_v1_5.json`（引擎 `FROZEN_SHA.pair_coupling = 82e11c4c…`）的候选行 y 是按现有 lane 平面派生并被其耦合；东平面一动，`PCIE_UP0/out_J2` 等页在冻结候选集内无合法行。

## 3. 下一步（单一批次，避免半个平面跨版本）
1. **pair 域 v1.6 重派生**：以新 lane 平面（西 `WLO≥33.61`；东降 0.17 或步距 ≤1.445）为输入，重跑 pair 域生成器（`tools/p3_v57_f13_pair_coupling_r2_v5.py` 系）；
   候选行须含**逃逸竖段 ≥0.4495** 与 `pad_y ± YWIN` 约束。
2. 探针复跑（`CO10_WSTEP/CO10_WLO/CO10_EDELTA` + `CO10_HOLE_GAP=0.4495`）→ 32/32 → `p3_v57_co11_placement_verify.py` PASS → 发 `CO16-ALLOC.3`。
3. 引擎侧：`F`/`FROZEN_SHA.pair_coupling` 版本化同步（**ECO 同批**，含变更单）+ `CO16_ALLOC` 指向 ALLOC.3 + REVISION bump → one-shot → G4..G7。
4. 目标：`copper_edge 14 → 0`、`hole_to_hole 3 → 0`（其余 74 = 既有 `PCIE_REFCLK0/1` 路线整改，独立变更单）。

## 4. 本周期落地物
- 探针新增**默认中性**旋钮：`CO10_EDELTA`（东 lane 平面平移）、`CO10_HOLE_GAP`（逃逸竖段候选下限）。默认 0 时几何**逐字节复现** ALLOC.2（geom sha16 `54bb2017da270b0c`，回归已验）。
- 未改任何冻结四源；未改 canonical（W3-CN.35 `248b504c4cca8f49` 保持）。
