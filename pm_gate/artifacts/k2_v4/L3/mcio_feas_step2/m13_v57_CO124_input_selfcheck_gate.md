# CO-124 — 输入自检闸（规格/规则自身）

- verdict：**PASS**
- 定义件：`pm_gate/artifacts/k2_v4/L2/BASIC_SKILL_VS_REDLINE_v1.0.md` `9ad91da8a49510a5`（v1.0 提议件）
- findings：9（未登记 0）
- 牙齿：{"T1_netclass_drift": true, "T3_threshold_unregistered": true, "T4_doc_anchor_missing": true, "T2_unregistered_finding_detected": true}

| # | check | finding | detail | 已登记 |
|---|---|---|---|---|
| | K3 | stackup_text_omits_in4_nets | {"layer": "In4.Cu", "in4_nets": ["MCU_VDD", "P3V3", "P3V3_AUX"], "stackup_text": "POWER_PLANE (P3V3)", "missing": ["MCU_VDD", "P3V3_AUX"]} | 是 |
| | K4 | bcu_policy_vs_zone_carrier:P3V3_BCU_BRIDGE_IN4 | {"zone": "P3V3_BCU_BRIDGE_IN4", "net": "P3V3"} | 是 |
| | K4 | bcu_policy_vs_zone_carrier:P3V3_AUX_BCU_BRIDGE_IN4 | {"zone": "P3V3_AUX_BCU_BRIDGE_IN4", "net": "P3V3_AUX"} | 是 |
| | K4 | bcu_policy_vs_zone_carrier:MCU_VDD_BCU_RESISTORS_IN4 | {"zone": "MCU_VDD_BCU_RESISTORS_IN4", "net": "MCU_VDD"} | 是 |
| | K6 | threshold_unproved_unregistered:pair_copper_edge_clearance_mm | {"rule_key": "pair_copper_edge_clearance_mm", "value": 0.875, "source": "L1_TOPOLOGY_v1.0 硬约束3 / R3-2 3W 强条"} | 是 |
| | K6 | threshold_unproved_unregistered:pair_cross_mm | {"rule_key": "pair_cross_mm", "value": 0.585, "source": "L1_TOPOLOGY_v2.0 硬约束2（0.585+0.875=1.46）"} | 是 |
| | K6 | threshold_unproved_unregistered:power_clearance_mm | {"rule_key": "power_clearance_mm", "value": 0.2, "source": "drc_rules.clearance.net_classes[POWER]"} | 是 |
| | K6 | threshold_unproved_unregistered:pcb_edge_copper_min_mm | {"rule_key": "pcb_edge_copper_min_mm", "value": 0.3, "source": "L1_TOPOLOGY_v2.0 硬约束4 / drc_rules.manufacturing"} | 是 |
| | K6 | threshold_unproved_unregistered:m3_keepout_mm | {"rule_key": "m3_keepout_mm", "value": 3.0, "source": "L1_TOPOLOGY_v2.0 硬约束5"} | 是 |

扫描范围与零遗漏声明见记录 `scan_scope_zero_omission`。
