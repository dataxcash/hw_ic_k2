# W6-C INFEASIBLE 证据表（停机文档）

- 求解：hs_route_model --all-v4 等价单次（v11，板 `6c387dff`，求解器 `049e0eec` = W6-B 后）
- 结果：18 对 → 1 SOLVED（REFCLK0）/ 17 INFEASIBLE；39 个 INFEASIBLE 段（30 极性交叉 + 9 净空失败）
- 停机条件触发：任一 INFEASIBLE → 本表落盘停机，禁止同输入重跑（已遵守，仅 1 次求解）

| 对 | 段 | flip | 类型 | 最近点坐标 (mm) | 缺口 | 最近障碍 | 归属 |
|---|---|---|---|---|---|---|---|
| PCIE_DN0 | out_MCIO | True | 极性交叉 | 64.364,45.596 | -0.205 (req 0.175) | pad:GND pad:GND (F.Cu) | out_MCIO 段逃逸 — 预存类A 极性缺口 |
| PCIE_DN1 | out_U3 | True | 极性交叉 | 79.183,58.376 | -0.205 (req 0.175) | pad:PCIE_DN_OUT1_N_MCIO pad:PCIE_DN_OUT1_N_MCIO (F.Cu) | out_U3 段逃逸 — 预存类A 极性缺口 |
| PCIE_DN1 | out_MCIO | True | 极性交叉 | 62.522,45.574 | -0.205 (req 0.175) | pad:GND pad:GND (F.Cu) | out_MCIO 段逃逸 — 预存类A 极性缺口 |
| PCIE_DN2 | out_U3 | True | 极性交叉 | 81.981,58.474 | -0.205 (req 0.175) | pad:PCIE_DN_OUT2_N_MCIO pad:PCIE_DN_OUT2_N_MCIO (F.Cu) | out_U3 段逃逸 — 预存类A 极性缺口 |
| PCIE_DN2 | out_MCIO | True | 极性交叉 | 57.105,45.563 | -0.205 (req 0.175) | pad:GND pad:GND (F.Cu) | out_MCIO 段逃逸 — 预存类A 极性缺口 |
| PCIE_DN3 | out_U3 | True | 极性交叉 | 84.416,58.337 | -0.205 (req 0.175) | pad:PCIE_DN_OUT3_N_MCIO pad:PCIE_DN_OUT3_N_MCIO (F.Cu) | out_U3 段逃逸 — 预存类A 极性缺口 |
| PCIE_DN3 | out_MCIO | True | 极性交叉 | 55.304,45.563 | -0.205 (req 0.175) | pad:GND pad:GND (F.Cu) | out_MCIO 段逃逸 — 预存类A 极性缺口 |
| PCIE_DN4 | out_U3 | True | 极性交叉 | 75.988,63.57 | -0.205 (req 0.175) | pad:PCIE_DN_OUT4_N_MCIO pad:PCIE_DN_OUT4_N_MCIO (F.Cu) | out_U3 段逃逸 — 预存类A 极性缺口 |
| PCIE_DN4 | out_MCIO | True | 极性交叉 | 55.3,61.64 | -0.205 (req 0.175) | pad:GND pad:GND (F.Cu) | out_MCIO 段逃逸 — 预存类A 极性缺口 |
| PCIE_DN5 | out_U3 | True | 极性交叉 | 78.586,64.764 | -0.205 (req 0.175) | pad:PCIE_DN_OUT5_N_MCIO pad:PCIE_DN_OUT5_N_MCIO (F.Cu) | out_U3 段逃逸 — 预存类A 极性缺口 |
| PCIE_DN5 | out_MCIO | True | 极性交叉 | 61.008,64.699 | -0.205 (req 0.175) | pad:GND pad:GND (F.Cu) | out_MCIO 段逃逸 — 预存类A 极性缺口 |
| PCIE_DN6 | out_U3 | True | 极性交叉 | 81.187,65.953 | -0.205 (req 0.175) | pad:PCIE_DN_OUT6_N_MCIO pad:PCIE_DN_OUT6_N_MCIO (F.Cu) | out_U3 段逃逸 — 预存类A 极性缺口 |
| PCIE_DN6 | out_MCIO | True | 极性交叉 | 63.436,65.891 | -0.205 (req 0.175) | pad:PCIE_UP7_P pad:PCIE_UP7_P (F.Cu) | out_MCIO 段逃逸 — 预存类A 极性缺口 |
| PCIE_DN7 | out_U3 | None | 净空失败 | - | 0 | - | out_U3 段逃逸 — 预存类A 极性缺口 |
| PCIE_DN7 | out_MCIO | True | 极性交叉 | 64.324,67.077 | -0.205 (req 0.175) | pad:GND pad:GND (F.Cu) | out_MCIO 段逃逸 — 预存类A 极性缺口 |
| PCIE_REFCLK1 | input | True | 极性交叉 | 60.544,60.707 | -0.205 (req 0.175) | seg:PCIE_REFCLK0_P seg:PCIE_REFCLK0_P (In6.Cu) | input 段逃逸（MCIO 侧）— 预存类A 极性/构造缺口 |
| PCIE_UP0 | input | True | 极性交叉 | 64.321,43.389 | -0.205 (req 0.175) | pad:GND pad:GND (F.Cu) | input 段逃逸（MCIO 侧）— 预存类A 极性/构造缺口 |
| PCIE_UP0 | out_U7 | True | 净空失败 | - | 0.4 (req 0.175) | pad:GND pad:GND (F.Cu) | out_U7 段逃逸 — 预存净空缺口 |
| PCIE_UP0 | out_J2 | True | 极性交叉 | 100.994,39.314 | -0.205 (req 0.175) | pad:PCIE_UP_OUT0_P_U7 pad:PCIE_UP_OUT0_P_U7 (F.Cu) | UP out_J2 左逃逸（cap 墙侧）— 预存 cap-wall 逃逸缺口 |
| PCIE_UP1 | input | True | 极性交叉 | 62.521,43.387 | -0.205 (req 0.175) | pad:PCIE_DN_OUT0_P_MCIO pad:PCIE_DN_OUT0_P_MCIO (F.Cu) | input 段逃逸（MCIO 侧）— 预存类A 极性/构造缺口 |
| PCIE_UP1 | out_U7 | True | 净空失败 | - | 0.4 (req 0.2) | pad:P3V3 pad:P3V3 (F.Cu) | out_U7 段逃逸 — 预存净空缺口 |
| PCIE_UP1 | out_J2 | True | 极性交叉 | 103.595,39.313 | -0.205 (req 0.175) | pad:PCIE_UP_OUT1_P_U7 pad:PCIE_UP_OUT1_P_U7 (F.Cu) | UP out_J2 左逃逸（cap 墙侧）— 预存 cap-wall 逃逸缺口 |
| PCIE_UP2 | input | True | 极性交叉 | 57.519,43.737 | -0.205 (req 0.175) | pad:PCIE_DN_OUT0_N_MCIO pad:PCIE_DN_OUT0_N_MCIO (F.Cu) | input 段逃逸（MCIO 侧）— 预存类A 极性/构造缺口 |
| PCIE_UP2 | out_U7 | True | 净空失败 | - | 0.375 (req 0.175) | pad:GND pad:GND (F.Cu) | out_U7 段逃逸 — 预存净空缺口 |
| PCIE_UP2 | out_J2 | True | 极性交叉 | 106.483,40.233 | -0.205 (req 0.175) | pad:PCIE_UP_OUT2_P_U7 pad:PCIE_UP_OUT2_P_U7 (F.Cu) | UP out_J2 左逃逸（cap 墙侧）— 预存 cap-wall 逃逸缺口 |
| PCIE_UP3 | input | True | 极性交叉 | 55.3,43.06 | -0.205 (req 0.175) | pad:GND pad:GND (F.Cu) | input 段逃逸（MCIO 侧）— 预存类A 极性/构造缺口 |
| PCIE_UP3 | out_U7 | True | 净空失败 | - | 0.4 (req 0.2) | pad:VREG1_U7 pad:VREG1_U7 (F.Cu) | out_U7 段逃逸 — 预存净空缺口 |
| PCIE_UP3 | out_J2 | True | 极性交叉 | 109.089,40.229 | -0.205 (req 0.175) | pad:PCIE_UP_OUT3_P_U7 pad:PCIE_UP_OUT3_P_U7 (F.Cu) | UP out_J2 左逃逸（cap 墙侧）— 预存 cap-wall 逃逸缺口 |
| PCIE_UP4 | input | True | 极性交叉 | 55.193,63.212 | -0.205 (req 0.175) | pad:GND pad:GND (F.Cu) | input 段逃逸（MCIO 侧）— 预存类A 极性/构造缺口 |
| PCIE_UP4 | out_U7 | True | 净空失败 | - | 0.4 (req 0.175) | pad:GND pad:GND (F.Cu) | out_U7 段逃逸 — 预存净空缺口 |
| PCIE_UP4 | out_J2 | True | 极性交叉 | 111.697,40.224 | -0.205 (req 0.175) | pad:PCIE_UP_OUT4_P_U7 pad:PCIE_UP_OUT4_P_U7 (F.Cu) | UP out_J2 左逃逸（cap 墙侧）— 预存 cap-wall 逃逸缺口 |
| PCIE_UP5 | input | True | 极性交叉 | 56.911,63.201 | -0.205 (req 0.175) | pad:PCIE_DN_OUT0_P_MCIO pad:PCIE_DN_OUT0_P_MCIO (F.Cu) | input 段逃逸（MCIO 侧）— 预存类A 极性/构造缺口 |
| PCIE_UP5 | out_U7 | True | 净空失败 | - | 0.4 (req 0.2) | pad:P3V3 pad:P3V3 (F.Cu) | out_U7 段逃逸 — 预存净空缺口 |
| PCIE_UP5 | out_J2 | True | 极性交叉 | 114.276,40.235 | -0.205 (req 0.175) | pad:PCIE_UP_OUT5_P_U7 pad:PCIE_UP_OUT5_P_U7 (F.Cu) | UP out_J2 左逃逸（cap 墙侧）— 预存 cap-wall 逃逸缺口 |
| PCIE_UP6 | input | True | 极性交叉 | 62.219,63.209 | -0.205 (req 0.175) | pad:GND pad:GND (F.Cu) | input 段逃逸（MCIO 侧）— 预存类A 极性/构造缺口 |
| PCIE_UP6 | out_U7 | True | 净空失败 | - | 0.4 (req 0.2) | pad:VREG2_U7 pad:VREG2_U7 (F.Cu) | out_U7 段逃逸 — 预存净空缺口 |
| PCIE_UP6 | out_J2 | True | 极性交叉 | 116.883,39.976 | -0.205 (req 0.175) | pad:PCIE_UP_OUT6_P_U7 pad:PCIE_UP_OUT6_P_U7 (F.Cu) | UP out_J2 左逃逸（cap 墙侧）— 预存 cap-wall 逃逸缺口 |
| PCIE_UP7 | input | True | 极性交叉 | 64.017,63.209 | -0.205 (req 0.175) | pad:PCIE_DN_OUT7_N_MCIO pad:PCIE_DN_OUT7_N_MCIO (F.Cu) | input 段逃逸（MCIO 侧）— 预存类A 极性/构造缺口 |
| PCIE_UP7 | out_U7 | True | 净空失败 | - | 0.4 (req 0.2) | pad:VREG2_U7 pad:VREG2_U7 (F.Cu) | out_U7 段逃逸 — 预存净空缺口 |

## 段级完整 reason（几何证据原文）

- **PCIE_DN0 / out_MCIO**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (64.364,45.596)）
- **PCIE_DN1 / out_U3**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (79.183,58.376)）
- **PCIE_DN1 / out_MCIO**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (62.522,45.574)）
- **PCIE_DN2 / out_U3**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (81.981,58.474)）
- **PCIE_DN2 / out_MCIO**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (57.105,45.563)）
- **PCIE_DN3 / out_U3**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (84.416,58.337)）
- **PCIE_DN3 / out_MCIO**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (55.304,45.563)）
- **PCIE_DN4 / out_U3**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (75.988,63.570)）
- **PCIE_DN4 / out_MCIO**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (55.300,61.640)）
- **PCIE_DN5 / out_U3**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (78.586,64.764)）
- **PCIE_DN5 / out_MCIO**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (61.008,64.699)）
- **PCIE_DN6 / out_U3**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (81.187,65.953)）
- **PCIE_DN6 / out_MCIO**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (63.436,65.891)）
- **PCIE_DN7 / out_U3**（净空失败）：短段直连无净空（F.Cu 直连 + In2 错开 via 均失败）
- **PCIE_DN7 / out_MCIO**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (64.324,67.077)）
- **PCIE_REFCLK1 / input**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (60.544,60.707)）
- **PCIE_UP0 / input**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (64.321,43.389)）
- **PCIE_UP0 / out_U7**（净空失败）：对级对称逃逸无净空（M=(98.825,48.700) → cv=(98.825,48.700) dir=1 flip=True pn_dist=0.400）
- **PCIE_UP0 / out_J2**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (100.994,39.314)）
- **PCIE_UP1 / input**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (62.521,43.387)）
- **PCIE_UP1 / out_U7**（净空失败）：对级对称逃逸无净空（M=(98.825,47.500) → cv=(98.825,47.500) dir=1 flip=True pn_dist=0.400）
- **PCIE_UP1 / out_J2**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (103.595,39.313)）
- **PCIE_UP2 / input**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (57.519,43.737)）
- **PCIE_UP2 / out_U7**（净空失败）：对级对称逃逸无净空（M=(98.825,46.300) → cv=(98.825,46.300) dir=1 flip=True pn_dist=0.400）
- **PCIE_UP2 / out_J2**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (106.483,40.233)）
- **PCIE_UP3 / input**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (55.300,43.060)）
- **PCIE_UP3 / out_U7**（净空失败）：对级对称逃逸无净空（M=(98.825,45.100) → cv=(98.825,45.100) dir=1 flip=True pn_dist=0.400）
- **PCIE_UP3 / out_J2**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (109.089,40.229)）
- **PCIE_UP4 / input**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (55.193,63.212)）
- **PCIE_UP4 / out_U7**（净空失败）：对级对称逃逸无净空（M=(98.825,43.900) → cv=(98.825,43.900) dir=1 flip=True pn_dist=0.400）
- **PCIE_UP4 / out_J2**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (111.697,40.224)）
- **PCIE_UP5 / input**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (56.911,63.201)）
- **PCIE_UP5 / out_U7**（净空失败）：对级对称逃逸无净空（M=(98.825,42.700) → cv=(98.825,42.700) dir=1 flip=True pn_dist=0.400）
- **PCIE_UP5 / out_J2**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (114.276,40.235)）
- **PCIE_UP6 / input**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (62.219,63.209)）
- **PCIE_UP6 / out_U7**（净空失败）：对级对称逃逸无净空（M=(98.825,41.500) → cv=(98.825,41.500) dir=1 flip=True pn_dist=0.400）
- **PCIE_UP6 / out_J2**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (116.883,39.976)）
- **PCIE_UP7 / input**（极性交叉）：via 换层 P/N 极性不一致（flip=True 逃逸出口排序与轨道分配相向交叉 min 边缘距 -0.2050 < 0.175 @ (64.017,63.209)）
- **PCIE_UP7 / out_U7**（净空失败）：对级对称逃逸无净空（M=(98.825,40.300) → cv=(98.825,40.300) dir=1 flip=True pn_dist=0.400）

## SOLVED 段（11，零交叉契约 edge≥0.155 全过）

| 对 | 段 | edge (mm) | lenP | lenN | skew |
|---|---|---|---|---|---|
| PCIE_DN0 | input | 0.175 | 37.2242 | 38.5589 | 1.3347 |
| PCIE_DN0 | out_U3 | 0.1732 | 13.4128 | 14.1987 | 0.7859 |
| PCIE_DN1 | input | 0.175 | 38.7495 | 37.3431 | 1.4064 |
| PCIE_DN2 | input | 0.1553 | 34.8117 | 36.6756 | 1.8639 |
| PCIE_DN3 | input | 0.175 | 37.7464 | 36.1678 | 1.5786 |
| PCIE_DN4 | input | 0.1553 | 34.9079 | 36.7731 | 1.8652 |
| PCIE_DN5 | input | 0.175 | 38.236 | 36.7535 | 1.4825 |
| PCIE_DN6 | input | 0.1729 | 35.6254 | 37.2071 | 1.5817 |
| PCIE_DN7 | input | 0.175 | 37.5066 | 36.0835 | 1.4231 |
| PCIE_REFCLK0 | input | 0.1749 | 74.2999 | 76.5106 | 2.2107 |
| PCIE_UP7 | out_J2 | 0.1732 | 28.0399 | 28.4834 | 0.4435 |

- UP7 out_J2 右（J2 侧）逃逸 = **LSWAP（W6-B 层换位）**，via 证据：(131.7,53.1)→(131.57,40.11) P / (134.05,53.1)→(132.17,40.49) N — v10 时代 UP out_J2 全 INFEASIBLE，此为 W6-B 新解。
- REFCLK0 skew 2.21 等长不达标 = 既有事实（v10 同口径），非本任务引入。
