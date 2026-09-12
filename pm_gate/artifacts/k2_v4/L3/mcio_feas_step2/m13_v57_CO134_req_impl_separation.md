# CO-134（L2 自裁 · 需求/实现分家）：③ = 工程换算错误；REQ-R3-2 忠实实现

- **撤回 owner 升级**：③ 定性 = 工程问题（0.875 = legacy 换算，按错误线宽 0.4375）⇒ 不作 owner 决策项。
- **忠实实现**（REQ-R3-2「3W 原则」= 对间中心距 ≥ 3×线宽）：**edge_min(layer) = 2×w(layer)** ⇒ 外层 0.41 / 内层 0.320；
  带内下界 0.18；旧 0.875 退役留存。SPEC **rev-19** `5f72182a2616392c`（白名单外 0 改动）。
- **可达性**：REACHABLE —— 域外 0.355+0.41=0.765 ≤ cap（WEST 1.05 / EAST 1.449）；
  焊盘场属 ECN-001 escape 域（已声明放宽）。
- **板实实测**：域外偏差 **3** 处（见记录 `as_built`；显式登记为工程开放项，路由 = SI/板厂券 或后续几何迭代）。
- **规矩入库**：`L2/REQUIREMENT_IMPLEMENTATION_SEPARATION_v1.0.md` `53153475e37dcb72` + 台账 `L2/derived_value_ledger_v1.json` `e96d799710b6ae4d`；
  机判 = co124 **K9**（负控 T5/T6/T7）。
