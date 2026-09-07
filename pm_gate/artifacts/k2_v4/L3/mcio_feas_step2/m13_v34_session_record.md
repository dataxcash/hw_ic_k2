# M14 v33+ 承接记录 — DIRECT_F.CU 形态修复 + 残留三类根因分类

> 状态：v33 handoff 承接的「DIRECT_F.CU 芯片侧逃逸」已实现并孤立验证；
> 全量 18/18 未达（3 次全量 run 后按纪律停）。本文 = 确定性分类证据 + 下步裁决输入。
> 纪律：前台自跑、无委派；ECN-008 已建；冻结区已 lock 0/0/0；单测 43 passed 零回归。

## 1. 本 session 改动（已 lock 保留，ECN-008）

- `_shared/eda_core/hs_route_model.py`：新增 `_col_stack_escape`（竖排主导对 |dy|≥0.45≥|dx| 的
  In2/In1 列下穿逃逸，`_escape_pair` W6-D 之后触发，确定性固定序，pn_ok 校验）+ `cs_alt_field/
  cs_alt_layer` 传递（方向分层用替换场）。
- `_shared/eda_core/route_input.py`：`ModelConfig.col_stack_escape_layer`（None=行为不变）。
- `k2/pm_gate/artifacts/k2_v4/L2/route_model_config.json`：`col_stack_escape_layer="In1.Cu"`。
- 依据（探针实证）：DIRECT 球列 F.Cu 竖线被同列邻族 pad 挡死（A_PET 上=B_PET pad / B_PER 下=GND
  网），pad 行→间隙列 In2/In1 床净空；方向分层 = 东族(VIA_IN2→J2) In2.Cu 与西族(DIRECT→MCIO)
  In1.Cu 隔离共享 BGA 列资产。

## 2. 全量 run 记录（禁暴力迭代，3 次停）

| run | 引擎 | SOLVED 链 | 说明 |
|---|---|---|---|
| solve_v33e | 无 col_stack | 0 | DIRECT 芯片侧 16 段全 INFEASIBLE（现状基线） |
| solve_v33f | col_stack In2 | UP1 | 芯片侧 DIRECT 多段 SOLVED；out_J2/远 lane 被共享挤占 |
| solve_v33g | col_stack In1(分层) | UP1, DN0 | 分层未解决共享顺序；REFCLK 独立 |

证据目录：`/tmp/solve_v33e|f|g/hs_rebuild_summary.json`。

## 3. 残留根因分类（只读定位，非猜）

**A. 数据对 16 对 = 纯共享顺序调度问题（画法已完备）**
孤立单段（零共享 solve_pair_v4）全 SOLVED：DN1/DN7 out_MCIO、UP0/UP7 out_J2 均 SOLVED。
全量按 UP0→UP7→DN0→DN7 顺序跑时，先解段占用内层/F.Cu 资产（In1/In2 腿、via、F.Cu 轨尾段），
后解段 fail-closed / P/N cross 于共享列（如 UP0 out_J2 landing cross@(91.9,55.13)）。
→ 缺的是**芯片逃逸区 In1/In2 通道资产分配**（哪族/哪 lane 用哪列 gutter），类 channel_alloc 但
面向芯片逃逸区；属 L2/方案层输入，非引擎画法。

**B. REFCLK0/1 = MCIO 连接器区真·形态缺口（独立，不经芯片）**
孤立单段也 INFEASIBLE：REFCLK0 input 左逃逸 flip=True VIA cross @(58.9,45.56)。
几何：REFCLK pin P(58.9,45.75)/N(58.3,45.75)（0.3×0.7 竖 pad，dx=0.6 dy=0）落在轨行对
45.51/45.89 **之间**（带内 pad），最近 GND pad d=-0.075 贴邻 → DIRECT 预检必败、via/LSWAP 全败。
→ 需 MCIO REFCLK 专用 dogbone-via 逃逸形态（独立于 A 类，勿混改）。

**C. 关联现象**：UP2/4 input、DN2/4/5 out_MCIO 全量失败点亦在 x55-62 MCIO 连接器区
（非芯片侧）→ 与 B 同区，判定为 MCIO 区共用瓶颈的连锁表现，归 B 类统一处理。

## 4. 建议（下步裁决点）

1. A 类：方案层补「芯片逃逸区 In1/In2 gutter 资产分配」输入（谁先占哪列），或引入
   共享冲突回溯求解；数据源 = 各段孤立解 + 共享占用矩阵（本记录已给出分类方法）。
2. B 类：MCIO 连接器 REFCLK/数据区 dogbone 逃逸形态（按连接器参考设计），独立小改动。
3. 器件成熟方案对照已确认：DS320PR1601(ZDG) 球图 Table 5-1 官方信号名与工程完全一致
   （A_PER/B_PET=Diff Out…见 datasheet SNLS683），side A/B 分组、TX/RX 分置确认；
   方向分层逃逸符合 TI 布局指南（SPRAAR7 表层/就近 via 原则）。
