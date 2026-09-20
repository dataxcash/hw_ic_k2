# K2 · B2-T 续作 · **CLI 子命令 fail-closed 普查（j）**（ENG / ARCHER · 只读）

> 机读：`k2/pm_gate/artifacts/k2_v4/P6_execution/B2T_CLI_FAILCLOSED_SWEEP_v1.json`
> 生成：`python3 k2/tools/k2_p6_cli_failclosed_sweep_v1.py --verify-determinism`
> 真源零改动（输出落 /tmp；B1 守卫仅在 /tmp 影子）

| 载体 | 守卫 | 子命令 | exit | status | 异常 | 用时 s |
|---|---|---|---|---|---|---|
| legacy_alloc | 无 | `chain_UP0` | 1 | None | RuntimeError: 可见性图求解超限（fail-closed，非设计结论） | 25.6 |
| legacy_alloc | 无 | `chain_REFCLK0` | 1 | INFEASIBLE | — | 7.3 |
| legacy_alloc | 无 | `chain_v2_UP0` | 1 | INFEASIBLE | — | 0.1 |
| legacy_alloc | 无 | `capacity_map` | 1 | INSUFFICIENT | — | 0.2 |
| legacy_alloc | 无 | `all_v4` | 1 | PARTIAL | — | 0.1 |
| legacy_alloc | 无 | `link_topology` | 1 | CROSSING_FOUND | — | 0.1 |
| legacy_alloc | 有 | `chain_UP0` | 1 | None | RuntimeError: 可见性图求解超限（fail-closed，非设计结论） | 24.9 |
| legacy_alloc | 有 | `chain_REFCLK0` | 1 | INFEASIBLE | — | 7.4 |
| legacy_alloc | 有 | `chain_v2_UP0` | 1 | INFEASIBLE | — | 0.1 |
| legacy_alloc | 有 | `capacity_map` | 1 | INSUFFICIENT | — | 0.1 |
| legacy_alloc | 有 | `all_v4` | 1 | PARTIAL | — | 0.1 |
| legacy_alloc | 有 | `link_topology` | 1 | CROSSING_FOUND | — | 0.1 |
| p3_current_schema | 无 | `chain_UP0` | 1 | None | RuntimeError: 可见性图求解超限（fail-closed，非设计结论） | 25.5 |
| p3_current_schema | 无 | `chain_REFCLK0` | 1 | INFEASIBLE | — | 7.2 |
| p3_current_schema | 无 | `chain_v2_UP0` | 0 | SOLVED | — | 0.1 |
| p3_current_schema | 无 | `capacity_map` | 0 | CAPACITY_OK | — | 3.1 |
| p3_current_schema | 无 | `all_v4` | 1 | PARTIAL | — | 69.0 |
| p3_current_schema | 无 | `link_topology` | 1 | None | ValueError: min() arg is an empty sequence | 0.1 |
| p3_current_schema | 有 | `chain_UP0` | 1 | None | RuntimeError: 可见性图求解超限（fail-closed，非设计结论） | 25.0 |
| p3_current_schema | 有 | `chain_REFCLK0` | 1 | INFEASIBLE | — | 7.2 |
| p3_current_schema | 有 | `chain_v2_UP0` | 0 | SOLVED | — | 0.1 |
| p3_current_schema | 有 | `capacity_map` | 0 | CAPACITY_OK | — | 3.1 |
| p3_current_schema | 有 | `all_v4` | 1 | PARTIAL | — | 69.2 |
| p3_current_schema | 有 | `link_topology` | 1 | CROSSING_FOUND | — | 0.2 |

**结论**
- 现行 schema 载体 + **无守卫**：崩溃 **2** 处（['chain_UP0', 'link_topology']）⇒ CLI 崩溃面集中于 `--link-topology`（B1）。
- 遗留载体：无/有守卫一致 ⇒ B1 修复**零语义回退**。
- ⚠ exit code 不可单独判定（崩溃与「非 TOPOLOGY_OK/未全解」同为 1）⇒ 须并联 `status`/stderr；建议 B1 授权件补 CLI 异常语义。
- **发现 B2**（载体无关）：`--chain UP0` 4 组合均抛 `RuntimeError: 可见性图求解超限（fail-closed，非设计结论）`
  （`hs_route_model.py:347`；刻意 fail-closed 抛错）⇒ **CLI 层未包装**，rc=1 与「正常未解」不可机辨。
- **发现 B3**（判据口径，需监理裁定）：`--capacity-map` 现行载体下 `status=CAPACITY_OK`/exit 0，而走廊
  `EAST_CHIP_TO_J2_refclk = INSUFFICIENT` ⇒ CLI 只看 region、忽略 corridor ⇒ 潜在 fail-open（ENG 不改口径）。
- 确定性两跑：**MATCH**。

—— ENG（ARCHER）· 2026-09-20 · 引擎 sha16 `b6f88d35bc0669e4` · 阶段：**P6 未开（只出计划件）**
