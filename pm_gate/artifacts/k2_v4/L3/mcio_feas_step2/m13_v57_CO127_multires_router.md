# CO-127 — ④ R1 `U2.5`/`J4.A9`：多分辨率 + 中线厚度模型确定性绕障复判

- verdict：**R1_FEASIBLE_ALL_BY_MULTIRES_ROUTER**
- 定义件：《BASIC_SKILL_VS_REDLINE v1.0》`9ad91da8a49510a5`

| target | net | netclass | feat | 级 | 格 | 清晰 | 路径格 | 区域矩形 | 最小矩形 | 本网搭接mm² | 判定 ok |
|---|---|---|---|---|---|---|---|---|---|---|---|
| U2.5 | P3V3 | POWER | 0.5 | 0 | 37584 | 30087 | 71 | 5 | 0.825 | 0.5647 | True |
| J4.A9 | P3V3_AUX | POWER | 0.5 | 0 | 8874 | 7398 | 45 | 5 | 0.6286 | 0.1996 | True |

牙齿：{"T5_determinism_reproduced": true, "T1_structural_infeasible_detected": true, "T3_own_plane_removed_negative_control": true, "T2_output_clearance_recheck": true, "T4_refinement_monotone": true, "T6_refinement_stability": true}

算法/根因/完备性论证见记录 `algorithm`；本件零 SPEC/板改动；结论若为可行，SPEC 写入（rev-17）另开 CO。
