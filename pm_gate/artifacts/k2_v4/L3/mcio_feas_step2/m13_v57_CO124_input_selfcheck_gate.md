# CO-124 — 输入自检闸（规格/规则自身）

- verdict：**PASS**
- 定义件：`pm_gate/artifacts/k2_v4/L2/BASIC_SKILL_VS_REDLINE_v1.1.md` `348735156c9d9b1d`（v1.0 提议件）
- findings：4（未登记 0）
- 牙齿：{"T1_netclass_drift": true, "T3_threshold_unregistered": true, "T4_doc_anchor_missing": true, "T2_unregistered_finding_detected": true, "T5_derived_without_principle": true, "T6_unreachable_derived": true, "T7_requirement_carries_value": true}

| # | check | finding | detail | 已登记 |
|---|---|---|---|---|
| | K6 | threshold_unproved_unregistered:pair_cross_mm | {"rule_key": "pair_cross_mm", "value": 0.585, "source": "L1_TOPOLOGY_v2.0 硬约束2（0.585+0.875=1.46）"} | 是 |
| | K6 | threshold_unproved_unregistered:power_clearance_mm | {"rule_key": "power_clearance_mm", "value": 0.2, "source": "drc_rules.clearance.net_classes[POWER]"} | 是 |
| | K6 | threshold_unproved_unregistered:pcb_edge_copper_min_mm | {"rule_key": "pcb_edge_copper_min_mm", "value": 0.3, "source": "L1_TOPOLOGY_v2.0 硬约束4 / drc_rules.manufacturing"} | 是 |
| | K6 | threshold_unproved_unregistered:m3_keepout_mm | {"rule_key": "m3_keepout_mm", "value": 3.0, "source": "L1_TOPOLOGY_v2.0 硬约束5"} | 是 |

扫描范围与零遗漏声明见记录 `scan_scope_zero_omission`。
