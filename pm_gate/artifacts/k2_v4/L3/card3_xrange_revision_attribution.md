# Card 3 INPUT_REVISION 归属声明 — SPEC 走廊 x_range 修订

> 日期：2026-08-27 ｜ 触发：W2（capacity_map_v7）容量重探结论 + PM 裁决批准

## 修订内容（2 行，主链唯一改动）

| 字段 | 旧值 | 新值 | 根因（证据见 capacity_map_v7/） |
|---|---|---|---|
| corridors J2_TO_U `x_range[1]` | 132.65 | **131.5** | x1 踩 J2 左列 GND 伴行脚（板实测 x=132.65 列含 17 GND），净空至 x≈131.72 |
| corridors U_TO_MCIO `x_range[0]` | 64.9 | **65.5** | x0 踩 J3/J4 最右列纯 GND 脚（板实测 x=64.9 列，y=45.75/43.25、63.95/61.45），净空自 x≈65.33 |

## 修订性质判定
- **输入层修正，非 workaround**：SPEC 走廊 x_range 原声明越过连接器 GND 脚列，
  轨道 P/N 线（ty±0.19）在走廊口与 GND 脚重叠（−0.10〜+0.11 vs 需求 0.175）。
- 连接器侧逃逸机制 = via→In2 下穿 GND 列 → 弹回 F.Cu 走廊（solve_summary 实测路径
  `[64.3,43.25]→via→In2→[64.9,49.29]→[88.83]`），弹起点右移 0.6mm 物理可行。
- 修订后 in-memory 验证（revision_verify.json）：4 区 6 走廊全 CAPACITY_OK + 跨区 4/4
  + 10 处 BLOCKED 全解锁 + 11/11 SOLVED 对零回归。

## 遗留（记入 Card 3 求解核实，不阻塞）
- 走廊口→连接器信号脚约 2.4mm 扇出不在逃逸模板内（与现有 SOLVED 对同级现状），
  M-E 求解以真实路径验证。

## 后果提示
- SPEC hash 变更 → verify_cli --quick 指纹 / escape_spec 需按正规流程复签（关联 Card 5B 指纹漂移）。
