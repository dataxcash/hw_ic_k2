# K2 · B2-T 续作 · **异常路径 fail-closed 普查（l）**（ENG / ARCHER · 只读）

> 机读：`k2/pm_gate/artifacts/k2_v4/P6_execution/B2T_EXCEPTION_PATH_SWEEP_v1.json`
> 生成：`python3 k2/tools/k2_p6_exception_path_sweep_v1.py --verify-determinism`
> 真源零改动（输出落 /tmp）

## A. CLI 层（10 运行 = 2 载体 × 5 用例）

| 载体 | 用例 | exit | status | 异常 | stdout 尾 |
|---|---|---|---|---|---|
| legacy_alloc | `nets_ok` | 0 | SOLVED | — | {"net_p": "PCIE_UP0_P", "net_n": "PCIE_UP0_N", "status": "SO |
| legacy_alloc | `nets_unknown` | 1 | INFRA_ERROR | — | {"net_p": "PCIE_NOPE_P", "net_n": "PCIE_NOPE_N", "status": " |
| legacy_alloc | `nets_bad_arity` | 2 | None | — | [infra] 需要恰好 2 个网（一对差分），收到 1 |
| legacy_alloc | `all_v2` | 1 | PARTIAL | — | {"status": "PARTIAL", "solved": [], "infeasible": ["PCIE_DN0 |
| legacy_alloc | `link_topology_mapping` | 0 | TOPOLOGY_OK | — | {"status": "TOPOLOGY_OK", "links": {"DN0": "ALIGNED", "UP0": |
| p3_current_schema | `nets_ok` | 0 | SOLVED | — | {"net_p": "PCIE_UP0_P", "net_n": "PCIE_UP0_N", "status": "SO |
| p3_current_schema | `nets_unknown` | 1 | INFRA_ERROR | — | {"net_p": "PCIE_NOPE_P", "net_n": "PCIE_NOPE_N", "status": " |
| p3_current_schema | `nets_bad_arity` | 2 | None | — | [infra] 需要恰好 2 个网（一对差分），收到 1 |
| p3_current_schema | `all_v2` | 0 | SOLVED | — | {"status": "SOLVED", "solved": ["PCIE_DN0", "PCIE_DN1", "PCI |
| p3_current_schema | `link_topology_mapping` | 0 | TOPOLOGY_OK | — | {"status": "TOPOLOGY_OK", "links": {"DN0": "ALIGNED", "UP0": |

## B. API 层（22 调用 = 2 载体 × 11 用例）

| 载体 | 用例 | 异常 | status |
|---|---|---|---|
| legacy_alloc | `solve_pair_segment[unknown]` | — | INFRA_ERROR |
| legacy_alloc | `solve_chain_v4[unknown]` | — | INFRA_ERROR |
| legacy_alloc | `solve_all_v4[empty]` | — | None |
| legacy_alloc | `probe_escape_capacity[unknown]` | — | INFRA_ERROR |
| legacy_alloc | `probe_path_clearance[empty_path]` | — | INFRA_ERROR |
| legacy_alloc | `probe_path_clearance[unknown_net]` | — | BLOCKED |
| legacy_alloc | `probe_region_capacity[unknown_corridor]` | — | INFRA_ERROR |
| legacy_alloc | `probe_region_capacity[missing_keys]` | — | INFRA_ERROR |
| legacy_alloc | `link_topology_virtual_map[empty]` | — | None |
| legacy_alloc | `link_topology_virtual_map[bad_ref]` | — | None |
| legacy_alloc | `_corridor_clear_span[malformed]` | ValueError: not enough values to unpack (expected 2, got 1) | None |
| p3_current_schema | `solve_pair_segment[unknown]` | — | INFRA_ERROR |
| p3_current_schema | `solve_chain_v4[unknown]` | — | INFRA_ERROR |
| p3_current_schema | `solve_all_v4[empty]` | — | None |
| p3_current_schema | `probe_escape_capacity[unknown]` | — | INFRA_ERROR |
| p3_current_schema | `probe_path_clearance[empty_path]` | — | INFRA_ERROR |
| p3_current_schema | `probe_path_clearance[unknown_net]` | — | BLOCKED |
| p3_current_schema | `probe_region_capacity[unknown_corridor]` | — | INFRA_ERROR |
| p3_current_schema | `probe_region_capacity[missing_keys]` | — | INFRA_ERROR |
| p3_current_schema | `link_topology_virtual_map[empty]` | — | None |
| p3_current_schema | `link_topology_virtual_map[bad_ref]` | — | None |
| p3_current_schema | `_corridor_clear_span[malformed]` | ValueError: not enough values to unpack (expected 2, got 1) | None |

## 结论

- 抛异常用例（2 个）：['legacy_alloc/_corridor_clear_span[malformed]', 'p3_current_schema/_corridor_clear_span[malformed]']
- 判定：CLI `--nets` 元数错误 = **优雅 `[infra]`/rc=2**（合规）；其余见上表。
  抛异常者属「**异常路径未 fail-closed**」⇒ 建议并入 B1 授权件的 CLI/API 异常语义整改
  （`status=INFRA_ERROR` + 可机辨码）。
- **发现 B4（低严重度）**：私有 API `_corridor_clear_span` 对畸形 corridor 抛 `ValueError`（非 fail-closed 状态）；
  该 API 为内部函数、输入来自 SPEC 真源 ⇒ 风险低（建议随手加形状校验，非阻塞）。
- 注：`link_topology_virtual_map` 返回 **verdict 键**（非 status），表中 status=None 属预期；`--nets` 输入校验合规
  （未知网 ⇒ 优雅 `INFRA_ERROR`；元数错误 ⇒ `[infra]`/rc=2）。
- 确定性两跑：**MATCH**。

—— ENG（ARCHER）· 2026-09-20 · 引擎 sha16 `b6f88d35bc0669e4` · 阶段：**P6 未开（只出计划件）**
