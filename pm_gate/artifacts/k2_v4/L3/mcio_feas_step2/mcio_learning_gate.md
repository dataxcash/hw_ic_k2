# mcio_feas 学习闸检索报告（EXECUTION_PROCESS.md 第 2 章工件）

> 检索执行：2026-09-04，kb.sqlite3 只读查询（`_shared/knowledge/kb.sqlite3`，immutable 副本）。
> 目的：本任务（MCIO 16 lane 电容墙→U3 布局可行性）先问案例库"怎么走"，再进生产链。

## 1. 检索方法

- 数据源：kb.sqlite3（唯一事实源），templates + template_features 两表全量。
- 特征提取：connector=MCIO/SFF、diff_pairs=16、AC cap wall 0402×32、dual_band corridor、F.Cu。

## 2. 命中模板（3 个 K2 项目模板 + 3 个 learned 外部）

| template_id | produced | 与任务相关性 |
|---|---|---|
| **conn_escape_mcio** | true | MCIO 4i SFF1016 芯片侧逃逸，16 对，F.Cu；structure=chip_side vertical escape to corridor；via_layers **F.Cu→B.Cu→F.Cu**；closure 26/26 冻结 PASS |
| **corridor_pair_dual_band** | true | U_TO_MCIO corridor；structure=**dual_band + F.Cu 数据带 + In2.Cu 受控换层走廊**（85Ω 0.205 双 GND 参考）；band_gap≥2.0；8对/带：8×0.205+7×0.875=**7.765<8.0 放得下** |
| cap_wall_ac | **false** | AC 墙 symmetric_bands；known_gap=复摆对 alloc 轨道压轨 → BOTH_INFEASIBLE，停机未落板 → 仅候选参考 |
| conn_escape_slimsas_x8 / learned_* | — | 同构参考（SlimSAS x8 / AIC / PEX8748），几何前提不同（稀疏墙） |

## 3. 三态判定：**部分覆盖**

- **已覆盖（形态先例）**：F.Cu 数据带 + In2.Cu 受控换层走廊；dual_band 上下带分工
  （corridor_pair_dual_band.band_assignment + direction_rule：rot 分工非 lane 分工）；
  每带 8 对数学闭合（7.765 < 带高 8.0）。
- **未实证（= 本任务定位）**：corridor_pair_dual_band.known_gaps = "8 条跨区网络在
  U_TO_MCIO MCIO 端逃逸区**垂直爬升容量未实证**" —— 本任务即补此实证。
- **前置缺口（不在本任务内）**：cap_wall_ac produced=false —— 摆位对 alloc 轨道压轨
  （v7 问题），属另一条线。

## 4. 对任务形态的强制含义

1. **禁止再用"单层 F.Cu 16 线同走廊"建模**——与模板 layer_plan（F.Cu 数据带 + In2.Cu
   受控换层走廊）冲突。多 lane 分散 + 多层使用是模板已冻结的形态，不是可选项。
2. 模板参数（生产过/结构冻结）：track_pitch 1.08 / pair_half_pitch 0.19 / clearance 0.175 /
   band_gap_min 2.0 / 8对带高 7.765-8.0 —— 作生产链 ②约束 的出处引用。
3. known_gap 实证的验收：MCIO 端逃逸区（U_TO_MCIO corridor 西端、电容墙出口）每 lane
   垂直爬升通道容量闭合 → 回写模板 known_gaps（学习闭环）。

## 5. 遗留裁决项（进 §4 判定场景，不属学习闸）

- 同对线距 0.6 vs 0.38（v18 裕量 vs 真值）；线-via 规则；P/N via x 错列 —— 待 Oracle/用户，
  以模板参数（pair_half_pitch 0.19 → 同对线中心距 ~0.38 语义）为参照。

## 6. 关联

- 生产链入口：`EXECUTION_PROCESS.md` §2；本任务登记 pm_gate tasks.json `mcio_feas`（planned）。
