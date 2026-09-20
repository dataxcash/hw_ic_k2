# K2 · B2-T 续作 · **板别名消费者普查 + B1 CLI 行为差异面**（ENG / ARCHER · 只读）

> 机读：`k2/pm_gate/artifacts/k2_v4/P6_execution/B2T_BOARD_ALIAS_AND_CLI_AUDIT_v1.json`
> 生成：`python3 k2/tools/k2_p6_board_alias_and_cli_audit_v1.py --verify-determinism`
> 真源零改动（只读；CLI 输出落 /tmp；守卫仅在 /tmp 影子）

## 1. (g) 板别名与消费者

`k2/k2_v4.kicad_pcb` = 符号链接 → `hw/k2_v4_8L.kicad_pcb`（解析后 sha16 `fb07d25ac426ff84` = **冻结设计源板** fb07d25a）。
消费者 .py 共 **63** 个：{"HIST(历史分析/复现脚本)": 27, "LIVE(共享层)": 30, "TOOL": 2, "TOOL(本轮/前轮 ENG 工具)": 4}

**LIVE（现役：共享层/判据）**：

| 文件 | 板身份字面量 | 命中行 |
|---|---|---|
| `_shared/eda_core/board_low_speed_sync.py` | — | 行 [32] |
| `_shared/eda_core/board_spec_consistency.py` | — | 行 [34] |
| `_shared/eda_core/cap_wall_apply.py` | — | 行 [53] |
| `_shared/eda_core/connector_geometry.py` | — | 行 [18] |
| `_shared/eda_core/jlc_deliver/package.py` | — | 行 [19] |
| `_shared/eda_core/tests/conftest.py` | — | 行 [59] |
| `_shared/eda_core/tests/test_escape_landing.py` | — | 行 [22, 564, 668] |
| `_shared/eda_core/tests/test_hs_route_model.py` | — | 行 [321] |
| `_shared/pm_gate/check_qa.py` | — | 行 [21, 87] |
| `_shared/pm_gate/cli.py` | — | 行 [532] |
| `_shared/pm_gate/config.py` | — | 行 [26, 83] |
| `_shared/pm_gate/tools_escape_predict.py` | — | 行 [46] |
| `_shared/pm_gate/tools_executor_single_pair.py` | — | 行 [17] |
| `_shared/pm_gate/tools_measure_l1.py` | — | 行 [2, 16, 108] |
| `_shared/pm_gate/wp1_semantics_check.py` | — | 行 [13, 46] |
| `k2/_shared/eda_core/board_low_speed_sync.py` | — | 行 [32] |
| `k2/_shared/eda_core/board_spec_consistency.py` | — | 行 [34] |
| `k2/_shared/eda_core/cap_wall_apply.py` | — | 行 [53] |
| `k2/_shared/eda_core/connector_geometry.py` | — | 行 [18] |
| `k2/_shared/eda_core/jlc_deliver/package.py` | — | 行 [19] |
| `k2/_shared/eda_core/tests/conftest.py` | — | 行 [59] |
| `k2/_shared/eda_core/tests/test_escape_landing.py` | — | 行 [22, 564, 668] |
| `k2/_shared/eda_core/tests/test_hs_route_model.py` | — | 行 [321] |
| `k2/_shared/pm_gate/check_qa.py` | — | 行 [21, 87] |
| `k2/_shared/pm_gate/cli.py` | — | 行 [532] |
| `k2/_shared/pm_gate/config.py` | — | 行 [26, 83] |
| `k2/_shared/pm_gate/tools_escape_predict.py` | — | 行 [46] |
| `k2/_shared/pm_gate/tools_executor_single_pair.py` | — | 行 [17] |
| `k2/_shared/pm_gate/tools_measure_l1.py` | — | 行 [2, 16, 108] |
| `k2/_shared/pm_gate/wp1_semantics_check.py` | — | 行 [13, 46] |

**HIST（历史分析/复现脚本，含板身份字面量者重点标注）**：

| 文件 | 板身份字面量 | 命中行 |
|---|---|---|
| `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/gen_chip_landing_v33.py` | — | 行 [13, 38] |
| `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_step2_layout_feasibility.py` | — | 行 [6, 27] |
| `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/mcio_geom_dump.py` | — | 行 [20] |
| `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/mcio_q2_fanout.py` | — | 行 [26, 33] |
| `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/mcio_q2_solve.py` | — | 行 [36] |
| `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/mcio_step2_definitive.py` | — | 行 [25] |
| `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/mcio_step2_feas.py` | — | 行 [26] |
| `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/packing_scan.py` | — | 行 [7] |
| `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/reproduce_eco_c5_verify.py` | — | 行 [2] |
| `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/reproduce_eco_full_clearance.py` | — | 行 [3] |
| `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/reproduce_eco_geom_angle.py` | — | 行 [2] |
| `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/reproduce_eco_phase1_delete_legacy.py` | — | 行 [2] |
| `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/reproduce_eco_phase2_insert_ds320_wire.py` | — | 行 [2] |
| `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/reproduce_k2_sch_v31_parity.py` | — | 行 [4, 19] |
| `k2/tools/p3_v56_p1_chip_coverage.py` | — | 行 [40] |
| `k2/tools/p3_v57_big_w0r_corridor_model.py` | — | 行 [38] |
| `k2/tools/p3_v57_big_w0r_validator.py` | — | 行 [32] |
| `k2/tools/p3_v57_l1_struct_preflight_v2.py` | f6273de6 | 行 [11, 25] |
| `k2/tools/p3_v57_layer_intent_derive.py` | f6273de6 | 行 [26] |
| `k2/tools/p3_v57_s0_audit_derived.py` | — | 行 [38] |
| `k2/tools/p3_v57_s0_endpoint_model.py` | — | 行 [28] |
| `k2/tools/p3_v57_s1_a14_gate.py` | — | 行 [9] |
| `k2/tools/p3_v57_s1_page_manifest.py` | — | 行 [33] |
| `k2/tools/p3_v57_s1_r1_via_verdict.py` | — | 行 [20] |
| `k2/tools/p3_v57_s1_r1_via_verdict_r2.py` | — | 行 [20] |
| `k2/tools/p3_v57_stackup_realign_8L.py` | f6273de6 | 行 [19] |
| `k2/tools/p3_v57_w3_constructive_validator_v2.py` | f6273de6, fb07d25a | 行 [27, 35] |

⇒ **LIVE 读到 8L 板 = 与 handoff §1 一致（非缺陷）**；**HIST 中带旧板字面量者按此路径重跑会静默换板** —— 须逐脚本标注（本笔不改脚本）。

## 2. (i) B1 修复前后 `--link-topology` 行为

| 载体 | 守卫 | exit | status | crossing | stderr 尾 |
|---|---|---|---|---|---|
| legacy_alloc | 无守卫 | 1 | CROSSING_FOUND | ['UP4', 'UP5', 'UP6', 'UP7'] |  |
| legacy_alloc | 有守卫 | 1 | CROSSING_FOUND | ['UP4', 'UP5', 'UP6', 'UP7'] |  |
| p3_current_schema | 无守卫 | 1 | None | None | ValueError: min() arg is an empty sequence |
| p3_current_schema | 有守卫 | 1 | CROSSING_FOUND | ['UP4', 'UP5', 'UP6', 'UP7'] |  |

⇒ 现行 schema 载体：**无守卫 = 崩溃（fail-open 缺口）→ 有守卫 = 正常返回 `CROSSING_FOUND`**；
遗留载体两态一致 ⇒ 修复无既存语义回退。确定性两跑：**MATCH**。

⚠ **附带发现（建议并入 B1 授权件）**：崩溃态与「非 TOPOLOGY_OK」**exit code 同为 1** ⇒ 调用方仅凭 rc
无法分辨崩溃与正常判定（fail-open 隐患）；建议同时要求异常路径返回 `status=INFRA_ERROR` + 可机辨退出码。

## 3. 待监理裁定（不阻塞）

① 锚承载形态（具名冻结载体 vs 合成现行 fixture）② B1 守卫（`_shared`）③ A1–A13 重基线批
④ HIST 脚本板身份标注批（只读报告，不改脚本）。

—— ENG（ARCHER）· 2026-09-20 · 引擎 sha16 `b6f88d35bc0669e4` · 阶段：**P6 未开（只出计划件）**
