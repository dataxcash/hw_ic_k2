# CO-130 — SPEC rev-16 → **rev-17**（L2 自裁 · 声明层施加）

- out：`SPEC_k2_v4.spec-rev-17.json` `9fea9fd20149c736`
- changed_paths：119（unexpected 0）
- D-6：`net_classes_override = {"12V_IN": "POWER"}`（CO-128 L2 定案）
- 退役 B.Cu 载体声明：P3V3_BCU_BRIDGE_IN4, P3V3_AUX_BCU_BRIDGE_IN4, MCU_VDD_BCU_RESISTORS_IN4（bridge_layer → In4.Cu；旧 carrier_change 移入 retired_carrier_change_bcu）
- stackup In4 文本：`POWER_PLANE (P3V3 east / MCU_VDD west / P3V3_AUX island)`（对齐实际网集 P3V3/MCU_VDD/P3V3_AUX）
- R1 证据：{"C84.1": {"verdict": "FEASIBLE", "co": "CO-122", "ref": "m13_v57_co122_bridge_target_recarrier_gate.json"}, "U4.3": {"verdict": "FEASIBLE", "co": "CO-122", "ref": "m13_v57_co122_bridge_target_recarrier_gate.json"}, "U2.5": {"verdict": "FEASIBLE_BY_DETERMINISTIC_ROUTER", "co": "CO-127", "ref": "m13_v57_co127_multires_router.json"}, "J4.A9": {"verdict": "FEASIBLE_BY_DETERMINISTIC_ROUTER", "co": "CO-127", "ref": "m13_v57_co127_multires_router.json"}}

白名单断言见记录；期望 L4 板逐字节不变（施加后全链复核）。