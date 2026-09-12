# CO-121 — L2 自裁 · 裁定：西区 P3V3_AUX In4 承载归属（+ 施加计划）

- 判定层级：**L2**（PDN 架构/走廊分配；冻结 L1 的域集合与粗分区均不变）
- 更正：boundary v1.82 附二 ②『L1 待裁』归口 = 过高归口
- 机判 verdict：**FEASIBLE_WITHIN_DECLARED_FAMILY**
- 净距判据：区域边 → 异网 via 圆心 ≥ **0.375** mm（闭式取自冻结 drc_rules）
- 可制造搭接判据：块↔带↔柱↔臂 面积搭接深度 ≥ **0.3** mm
- 可行候选：['K1_below_h0.5_cw0.2_off+0.675', 'K1_below_h0.5_cw0.3_off+0.775', 'K1_below_h0.7_cw0.2_off+0.675', 'K1_below_h0.7_cw0.3_off+0.775']
- 牙齿：{'K6': True, 'K4': True, 'K5': True}

## 家族机判（(a) 覆盖 / (b) 净距 / (c) MCU_VDD 连续 / (d) AUX 连通）

| 候选 | a | b | c | d | ok |
|---|---|---|---|---|---|
| K0_islands_cw0.3 | PASS | PASS | PASS | FAIL | NG |
| K1_direct_h0.5_cw0.3_off+0.000 | PASS | FAIL | PASS | PASS | NG |
| K1_direct_h0.7_cw0.3_off+0.000 | PASS | FAIL | PASS | PASS | NG |
| K1_below_h0.5_cw0.3_off+0.000 | PASS | FAIL | PASS | PASS | NG |
| K1_below_h0.7_cw0.3_off+0.000 | PASS | FAIL | PASS | PASS | NG |
| K1_above_h0.5_cw0.3_off+0.000 | PASS | FAIL | PASS | FAIL | NG |
| K1_above_h0.7_cw0.3_off+0.000 | PASS | FAIL | FAIL | FAIL | NG |
| K1_direct_h0.5_cw0.3_off+0.775 | PASS | FAIL | PASS | PASS | NG |
| K1_direct_h0.7_cw0.3_off+0.775 | PASS | FAIL | PASS | PASS | NG |
| K1_below_h0.5_cw0.3_off+0.775 | PASS | PASS | PASS | PASS | OK |
| K1_below_h0.7_cw0.3_off+0.775 | PASS | PASS | PASS | PASS | OK |
| K1_above_h0.5_cw0.3_off+0.775 | PASS | FAIL | PASS | FAIL | NG |
| K1_above_h0.7_cw0.3_off+0.775 | PASS | FAIL | FAIL | FAIL | NG |
| K1_direct_h0.5_cw0.3_off-0.775 | PASS | FAIL | PASS | PASS | NG |
| K1_direct_h0.7_cw0.3_off-0.775 | PASS | FAIL | PASS | PASS | NG |
| K1_below_h0.5_cw0.3_off-0.775 | PASS | FAIL | PASS | PASS | NG |
| K1_below_h0.7_cw0.3_off-0.775 | PASS | FAIL | PASS | PASS | NG |
| K1_above_h0.5_cw0.3_off-0.775 | PASS | FAIL | PASS | FAIL | NG |
| K1_above_h0.7_cw0.3_off-0.775 | PASS | FAIL | FAIL | FAIL | NG |
| K0_islands_cw0.2 | PASS | PASS | PASS | FAIL | NG |
| K1_direct_h0.5_cw0.2_off+0.000 | PASS | FAIL | PASS | PASS | NG |
| K1_direct_h0.7_cw0.2_off+0.000 | PASS | FAIL | PASS | PASS | NG |
| K1_below_h0.5_cw0.2_off+0.000 | PASS | FAIL | PASS | PASS | NG |
| K1_below_h0.7_cw0.2_off+0.000 | PASS | FAIL | PASS | PASS | NG |
| K1_above_h0.5_cw0.2_off+0.000 | PASS | FAIL | PASS | FAIL | NG |
| K1_above_h0.7_cw0.2_off+0.000 | PASS | FAIL | FAIL | FAIL | NG |
| K1_direct_h0.5_cw0.2_off+0.675 | PASS | FAIL | PASS | PASS | NG |
| K1_direct_h0.7_cw0.2_off+0.675 | PASS | FAIL | PASS | PASS | NG |
| K1_below_h0.5_cw0.2_off+0.675 | PASS | PASS | PASS | PASS | OK |
| K1_below_h0.7_cw0.2_off+0.675 | PASS | PASS | PASS | PASS | OK |
| K1_above_h0.5_cw0.2_off+0.675 | PASS | FAIL | PASS | FAIL | NG |
| K1_above_h0.7_cw0.2_off+0.675 | PASS | FAIL | FAIL | FAIL | NG |
| K1_direct_h0.5_cw0.2_off-0.675 | PASS | FAIL | PASS | PASS | NG |
| K1_direct_h0.7_cw0.2_off-0.675 | PASS | FAIL | PASS | PASS | NG |
| K1_below_h0.5_cw0.2_off-0.675 | PASS | FAIL | PASS | PASS | NG |
| K1_below_h0.7_cw0.2_off-0.675 | PASS | FAIL | PASS | PASS | NG |
| K1_above_h0.5_cw0.2_off-0.675 | PASS | FAIL | PASS | FAIL | NG |
| K1_above_h0.7_cw0.2_off-0.675 | PASS | FAIL | FAIL | FAIL | NG |
| K6_thin_merge_NEGCTRL | PASS | PASS | PASS | PASS | NG |
| K4_fullheight_NEGCTRL | PASS | FAIL | FAIL | PASS | NG |
| K5_missing_U1.15_NEGCTRL | FAIL | PASS | PASS | FAIL | NG |

## 施加计划（后继 CO-122，本件未施加）

SPEC rev-16 + 全链 G4→G7 + 全部回归闸 + PDN 闸 + 非执行者复评。本件零 SPEC/板改动、不重基线。
