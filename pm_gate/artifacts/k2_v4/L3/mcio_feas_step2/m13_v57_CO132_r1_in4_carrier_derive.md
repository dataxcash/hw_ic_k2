# CO-132 — R1 In4 承载几何派生 + 施加 rev-18（L2 自裁）

- out：`SPEC_k2_v4.spec-rev-18.json` `500f3da8179fe19c`；src `SPEC_k2_v4.spec-rev-17.json` `9fea9fd20149c736`
- whitelist_ok=True（changed_paths 311，unexpected 0）

| zone | net | 区域矩形 | verdict | 级 | min-dim | 覆盖 | 净距复算 | 本网搭接 | 宿主 |
|---|---|---|---|---|---|---|---|---|---|
| P3V3_BCU_BRIDGE_IN4 | P3V3 | 13 | FEASIBLE_BY_DETERMINISTIC_ROUTER | 0 | 0.54 | True | True | True | {'MCU_VDD_WEST': True, 'P3V3_EAST': True} |
| P3V3_AUX_BCU_BRIDGE_IN4 | P3V3_AUX | 4 | FEASIBLE_BY_DETERMINISTIC_ROUTER | 0 | 0.6286 | True | True | True | {'P3V3_EAST': True, 'MCU_VDD_WEST': True} |
| 12V_IN_IN4_CARRIER | 12V_IN | 8 | FEASIBLE_BY_DETERMINISTIC_ROUTER | 0 | 0.57 | True | True | True | {'MCU_VDD_WEST': True} |

模型/白名单见记录；期望 L4 板逐字节不变。