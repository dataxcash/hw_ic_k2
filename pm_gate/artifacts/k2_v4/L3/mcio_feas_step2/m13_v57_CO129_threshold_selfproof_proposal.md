# CO-129 — ③ 对间铜边净空 0.875 自证 + 口径提案

- verdict：**THRESHOLD_0p875_PROVED_UNREACHABLE_PROPOSAL_ISSUED**
- identity：`净空 = 走廊轨距(pitch) − 铜跨(span) ⇒ pitch_required = span + 0.875（CO-86 恒等式）`
- span_min(带内最小) = **0.355**（w_min=0.09，Z≈93.24Ω）；span_nom(名义85Ω) = 0.407；pitch caps = {'WEST_MCIO_TO_CHIP': 1.05, 'EAST_CHIP_TO_J2': 1.449, 'pad_field': 0.6}

| span | pitch_required | 缺额 WEST | 缺额 EAST | 缺额焊盘场 | 全过 |
|---|---|---|---|---|---|
| delivered_0.705 | 1.58 | 0.53 | 0.131 | 0.98 | False |
| option_p_gap_0.585 | 1.46 | 0.41 | 0.011 | 0.86 | False |
| impedance_band_span_min | 1.23 | 0.18 | -0.219 | 0.63 | False |
| impedance_nominal_85ohm | 1.282 | 0.232 | -0.167 | 0.682 | False |

**完备性**：焊盘场 = 模型自由全 span 不可达（0.600 < 0.875）；WEST = 声明阻抗模型下 span ≥ 0.355 ⇒ 缺额 ≥ 0.18（区间单调，非抽样）。

**提案 P1（建议）**：以 3W **原义**为主口径：对间铜边净空 ≥ 2·w_对（等价于中心距 ≥ 3W）；0.875 降为「w ≥ 0.4375 时的推论」。
**提案 P2（备选）**：保留绝对阈值但改为**分域可达上限**（cap − span_min）：WEST_MCIO_TO_CHIP ≤ 0.695；EAST_CHIP_TO_J2 ≤ 1.094；pad_field ≤ 0.245。

牙齿：{"T3_impedance_monotone_decreasing": true, "T1_pad_field_span_independent": true, "T2_hypothetical_control_reachable": true, "T4_co86_reproduced_byte_identical": true}
失败/异常：[]

本件零 SPEC/阈值/板改动；口径修订批准归 owner。
