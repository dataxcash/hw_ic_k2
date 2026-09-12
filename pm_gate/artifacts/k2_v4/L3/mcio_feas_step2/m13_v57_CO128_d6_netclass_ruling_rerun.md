# CO-128 — D-6 定案（`12V_IN` → POWER）+ ① 按新类复判

- verdict：**D6_RULED_AND_1_FEASIBLE_UNDER_NEW_CLASS**
- 层级：**L2**（网级净距/线宽口径 + PDN 承载；无 L1 面）
- 裁定：`net_classes_override = {'net': '12V_IN', 'class': 'POWER'}`；改网名方案已否决
- 后果：线宽下限 0.15→0.5；净距 0.1→0.2（required 0.375）；施加归 rev-17 并强制跑 co124

| 口径 | feat | 判定 | 区域矩形 | 最小矩形 | 覆盖3/3 | 宿主连续 | ok |
|---|---|---|---|---|---|---|---|
| 新类 POWER | 0.5 | FEASIBLE_BY_DETERMINISTIC_ROUTER | 8 | 0.57 | True | True | True |

牙齿：{"T3_determinism_reproduced": true, "T1_structural_infeasible_detected": true, "T2_output_clearance_recheck": true, "T4_coverage_3of3": true}

算法/根因/完备性见 CO-127；本件零 SPEC/板改动（施加归 rev-17）。