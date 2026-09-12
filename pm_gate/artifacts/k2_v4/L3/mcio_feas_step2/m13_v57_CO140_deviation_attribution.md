# CO-140 — as-built 对间偏差归因（L2 只读）

- 计数：{"INHERENT_INTERFACE_PITCH": 1, "OBLIQUE_OUT_OF_LONG_PARALLEL": 1, "ROUTING_FIXABLE": 1}

| 层 | 位置 | 焊盘距 | 3w | 最小可达铜边 | 2w | 平行占比 | 归因 |
|---|---|---|---|---|---|---|---|
| B.Cu | [92.15, 47.912] | 1.0583 | 0.615 | 0.8533 | 0.41 | 1.0 | ROUTING_FIXABLE |
| F.Cu | [137.24, 59.575] | 0.6 | 0.615 | 0.395 | 0.41 | 1.0 | INHERENT_INTERFACE_PITCH |
| In5.Cu | [74.75, 40.8] | 1.0583 | 0.48 | 0.8983 | 0.32 | 0.0 | OBLIQUE_OUT_OF_LONG_PARALLEL |

归因：接口固有 = 焊盘中心距 < 3w（路由无法消除）；斜交 = 耦合区平行占比 ≈ 0；路由可改 = 其余。
