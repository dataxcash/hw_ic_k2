# CO-123 — L2 复核：④ R1 的 U2.5 / J4.A9（障碍派生有界绕行 palette）

- verdict：**R1_DETOUR_INFEASIBLE_SOME**
- 净距 0.375mm / 搭接 ≥ 0.3mm / 直走廊对照须 FAIL

| target | net | 宿主区 | 阻塞者 | 家族成员 | 判定 | chosen |
|---|---|---|---|---|---|---|
| U2.5 | P3V3 | MCU_VDD_WEST | C84.2(GND) | 12 | NOT_FEASIBLE_IN_DETOUR_PALETTE | - |
| J4.A9 | P3V3_AUX | P3V3_EAST | J4.A7(GND) | 12 | NOT_FEASIBLE_IN_DETOUR_PALETTE | - |

牙齿（直走廊对照须全 FAIL）：{"U2.5(P3V3)": {"straight_all_fail": true, "n_straight": 4}, "J4.A9(P3V3_AUX)": {"straight_all_fail": true, "n_straight": 4}}

本件零 SPEC/板改动；若 R1 全可行，其施加须另开 CO（含 B.Cu 桥声明退役）。
