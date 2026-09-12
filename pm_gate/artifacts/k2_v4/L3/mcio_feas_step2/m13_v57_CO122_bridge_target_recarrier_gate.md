# CO-122 — L2 机判：CO-118 R1（4 target 改 In4 承载）可行性

- verdict：**R1_INFEASIBLE_SOME**
- 净距 0.375mm / 搭接 ≥ 0.3mm / 零坐标搜索

| target | net | 宿主区 | 家族成员 | 判定 | chosen |
|---|---|---|---|---|---|
| C84.1(P3V3) | P3V3 | MCU_VDD_WEST | 30 | FEASIBLE | C84.1|w1.0|h0.8|dy-1.0 |
| U2.5(P3V3) | P3V3 | MCU_VDD_WEST | 30 | NOT_FEASIBLE_WITHIN_DECLARED_FAMILY | - |
| U4.3(P3V3) | P3V3 | MCU_VDD_WEST | 30 | FEASIBLE | U4.3|w0.75|h0.5|dy+0.5 |
| J4.A9(P3V3_AUX) | P3V3_AUX | P3V3_EAST | 30 | NOT_FEASIBLE_WITHIN_DECLARED_FAMILY | - |

后果：R1 家族内**未全过**：可行 target 可由 In4 承载；未过者**仅证「本声明式家族内无合法成员」**（家族受限；未证明不存在 —— 同 CO-94『family-limit 命中』口径，禁把家族不足写成不可行）。未过者归 owner（R2 放宽 B.Cu 红线 / L1 变更），或由后继以**更细声明 palette** 复核（逼近搜索红线须先自证不越界）

施加（若 R1 成立）另开 CO-122b；本件零 SPEC/板改动。
