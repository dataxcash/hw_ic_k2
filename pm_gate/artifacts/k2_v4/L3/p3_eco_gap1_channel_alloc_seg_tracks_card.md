# 任务卡 P3-ECO-1 — 修复 gap1：③→⑤ 数据流断层（channel_alloc 段级 seg_tracks）

> 阶段：P3 验证暴露缺口 gap1 的回上层 ECO（SOLVE_PIPELINE_CONTRACT 层 3 边界改动）
> 施工位置：`_shared/eda_core/channel_alloc.py`（+ 可能 hs_route_model._track_y_for / SOLVE_PIPELINE_CONTRACT）
> 角色：WORKER 施工，TASK MGR 复核
> 与 P3-ECO-2 并行（不同引擎：本卡 channel_alloc，ECO-2 escape_landing）
> 铁律：SDD 驱动禁止事件驱动（先设计后施工）、问题回模型、冲突即停机

## 现象（P3-B 真板端到端实测，勿重跑论证）

solve 阶段 **16/18 数据对 INFEASIBLE**，根因是阶段③→⑤ 数据流断层：
channel_alloc 产物每网**单 track_y**（落 J2_TO_U 带内），无 `seg_tracks`；
`hs_route_model._track_y_for` 假定两廊道 bands 完全相同直接复用，但真板 SPEC
upper/lower 两廊道轨道**偏移 0.4mm**（J2_TO_U 40.3/41.5/… vs U_TO_MCIO 40.7/41.9/…）
→ U_TO_MCIO 段全部「无通道分配」（INFRA_ERROR）。REFCLK 两廊道轨道相同（45.7/50.5）故 REFCLK0 能 SOLVED。

## 根因（已实证，见报告 evidence）

- `channel_alloc` 现版本产出每网单 `track_y`，无段级 `seg_tracks`（M13 v5 曾有，现版本无）
- `hs_route_model._track_y_for` 把单 track_y 直接复用到所有段（假定 bands 跨廊道完全相同），
  真板两廊道轨道偏移 0.4mm 打破该假定

## 业务影响

16/18 高速差分对无法施工，K2 真板端到端卡死在 solve 阶段——这是「模板驱动 K2 确定性通过」的最大障碍。

## 修复方向（先设计后施工，二选一并论证）

回 SDD 改边界，二选一（或论证后择一）：
1. **③ 产出段级 `seg_tracks`**：channel_alloc 每网每段（J2_TO_U / U_TO_MCIO）独立轨道，
   契约层 `AllocTable` 扩展 `seg_tracks` 字段（SOLVE_PIPELINE_CONTRACT §2 阶段③ 改动）
2. **`_track_y_for` 按廊道独立解析**：hs_route_model 消费段所属廊道，按该廊道 bands 独立查轨道

**必须先写设计说明（改 SOLVE_PIPELINE_CONTRACT §2/§3 或 docstring 字段级契约），
TASK MGR 复核设计后再施工。禁止直接打补丁。**

## 验收（按序）

A. 设计说明：字段级契约改动（AllocTable.seg_tracks 或 _track_y_for 解析规则）写进 docstring/契约文档
B. 单测：① 两廊道轨道偏移 0.4mm 场景，U_TO_MCIO 段能解析到正确轨道 ② 同廊道场景不回归 ③ 确定性
C. 真板重跑：`p3_k2_real_board_e2e.py` 重跑，solve 数据对 INFEASIBLE 从 16 下降（目标 16/18 SOLVED 或明确剩余归因）
D. 零单板特判（轨道偏移是 SPEC 事实，引擎按 SPEC 消费，不硬编码 0.4mm）
E. `pytest` 相关套件全绿 + 零新增失败

## 禁止

- 禁止把 0.4mm 偏移硬编码进引擎（须从 SPEC corridors 各 band 轨道读）
- 禁止改真板/SPEC 数值来绕过断层（问题回模型，修订走输入）
- 禁止直接改 hs_route_model 绕契约（契约层改边界优先）
- 禁止假成功（残留 INFEASIBLE 如实归因）
