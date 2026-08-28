# WP1 规划输入（确定性输入源，禁止手改）

## 文件
- `wp1_anchors.json` — 26 网锚点（ref/pad/终点/分组），**ECN-005 已修正 A/B 排位**（三源权威）
- `wp1_groups.json` — 四组拓扑参数（lane/X/gap/left_x/top_y/ret_x + same_dn cap_x/cap_y）
  - ⚠️ same_dn cap_x/cap_y 当前为**旧坐标**（83.97/60.05…），cap 墙重排后必须由
    `cap_wall_solver.py` 输出同步（见 .omo/plans/k2-wp1-capwall-complete.md Task 6c）

## 同步规则
- 变更走确定性工具（cap_wall_solver / route_allocator / cap_wall_apply），禁止手改
- 输入变更 → 重新 freeze（指纹变化是预期信号，不是错误）
