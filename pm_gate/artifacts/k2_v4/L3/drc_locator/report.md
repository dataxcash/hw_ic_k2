# DRC 反向定位报告 (drc_locator, DRC-SEMANTIC-CORE M12)

- DRC 基线: `k2_m9demo.kicad_pcb`
- 违规总数: 867 条 / items 1734
- 聚类: 117 族 (域×区域×规则×根因)
- 高危(间距<50%): 78 条
- 覆盖度自检: unknown_kind_items=0 unknown_rule=0 unclassified_family=0 unmapped_uuid_items=0

> 结论带证明：每条 finding 的 uuid→元素 映射见 report.json items[].uuid/elem；
> 聚类报告带逐类数字；本报告为分析工具，不驱动修复（DRC 只核对不驱动）。

## 1. 按域（条数）

| 域 | 条数 |
|---|---|
| hs | 294 |
| hs+pwr | 181 |
| pwr+ls | 162 |
| ls | 146 |
| pwr | 45 |
| hs+ls | 39 |

## 2. 按规则类型（条数）

| 类型 | 条数 | 根因族数 |
|---|---|---|
| clearance | 500 | 4 |
| hole_clearance | 171 | 2 |
| shorting_items | 89 | 3 |
| solder_mask_bridge | 58 | 2 |
| tracks_crossing | 46 | 1 |
| zones_intersect | 2 | 1 |
| diff_pair_gap_out_of_range | 1 | 1 |

## 3. 聚类清单（域×区域×规则×根因，条数降序）

| # | 条数 | 域 | 区域 | 规则 | 根因族 | 高危 | 路径 |
|---|---|---|---|---|---|---|---|
| 1 | 82 | hs | 中-U3U7/下 | clearance | via_clearance | 0 | C_VIA |
| 2 | 42 | hs | 中-U3U7/上 | clearance | via_clearance | 0 | C_VIA |
| 3 | 35 | hs | 中-U3U7/下 | clearance | seg_clearance | 0 | E_SCHEME |
| 4 | 29 | ls | 中-U3U7/下 | hole_clearance | via_via_hole | 0 | C_VIA |
| 5 | 24 | hs+pwr | 中-U3U7/下 | clearance | pad_clearance | 5 | E_SCHEME |
| 6 | 24 | hs+pwr | 中-U3U7/上 | clearance | pad_clearance | 5 | E_SCHEME |
| 7 | 23 | ls | 中-U3U7/下 | hole_clearance | via_hole | 2 | C_VIA |
| 8 | 22 | hs+pwr | 中-U3U7/下 | solder_mask_bridge | smd_mask_bridge | 0 | C_MFG |
| 9 | 21 | hs | 中-U3U7/下 | clearance | pad_clearance | 2 | E_SCHEME |
| 10 | 20 | hs+pwr | 中-U3U7/上 | solder_mask_bridge | smd_mask_bridge | 0 | C_MFG |
| 11 | 19 | hs | 中-U3U7/上 | clearance | seg_clearance | 0 | E_SCHEME |
| 12 | 18 | hs | 右-SlimSAS/上 | clearance | via_clearance | 0 | C_VIA |
| 13 | 16 | hs | 右-SlimSAS/上 | clearance | via_via_layer_dup | 0 | C_VIA |
| 14 | 16 | pwr+ls | 左-MCIO/下 | shorting_items | via_short | 0 | E_SCHEME |
| 15 | 16 | pwr+ls | 右-SlimSAS/上 | shorting_items | via_short | 0 | E_SCHEME |
| 16 | 15 | ls | 中-U3U7/上 | hole_clearance | via_hole | 0 | C_VIA |
| 17 | 15 | ls | 中-U3U7/上 | hole_clearance | via_via_hole | 0 | C_VIA |
| 18 | 14 | hs+pwr | 中-U3U7/下 | clearance | via_clearance | 5 | C_VIA |
| 19 | 14 | pwr+ls | 左-MCIO/上 | shorting_items | via_short | 0 | E_SCHEME |
| 20 | 14 | pwr | 左-MCIO/下 | clearance | via_via_layer_dup | 0 | C_VIA |
| 21 | 13 | pwr+ls | 左-MCIO/下 | clearance | via_via_layer_dup | 7 | C_VIA |
| 22 | 12 | hs+pwr | 右-SlimSAS/上 | hole_clearance | via_via_hole | 12 | C_VIA |
| 23 | 11 | hs+pwr | 中-U3U7/下 | clearance | seg_clearance | 7 | E_SCHEME |
| 24 | 11 | hs | 左-MCIO/下 | clearance | via_clearance | 0 | C_VIA |
| 25 | 10 | ls | 中-U3U7/下 | tracks_crossing | seg_crossing | 0 | A_LOWSPEED |
| 26 | 10 | ls | 左-MCIO/下 | hole_clearance | via_hole | 0 | C_VIA |
| 27 | 10 | pwr+ls | 左-MCIO/上 | clearance | via_clearance | 4 | C_VIA |
| 28 | 9 | ls | 中-U3U7/上 | tracks_crossing | seg_crossing | 0 | A_LOWSPEED |
| 29 | 9 | hs+ls | 中-U3U7/下 | clearance | via_clearance | 0 | C_VIA |
| 30 | 9 | hs | 中-U3U7/上 | clearance | pad_clearance | 1 | E_SCHEME |
| 31 | 9 | pwr+ls | 中-U3U7/下 | hole_clearance | via_hole | 0 | C_VIA |
| 32 | 9 | ls | 中-U3U7/下 | solder_mask_bridge | smd_mask_bridge | 0 | C_MFG |
| 33 | 8 | ls | 左-MCIO/上 | tracks_crossing | seg_crossing | 0 | A_LOWSPEED |
| 34 | 8 | hs | 右-SlimSAS/下 | clearance | via_clearance | 0 | C_VIA |
| 35 | 8 | pwr | 中-U3U7/下 | clearance | via_via_layer_dup | 0 | C_VIA |
| 36 | 8 | pwr+ls | 左-MCIO/上 | hole_clearance | via_hole | 1 | C_VIA |
| 37 | 8 | pwr+ls | 中-U3U7/上 | hole_clearance | via_via_hole | 0 | C_VIA |
| 38 | 7 | ls | 中-U3U7/下 | shorting_items | seg_seg_edge0_short | 0 | E_SCHEME |
| 39 | 7 | hs | 右-SlimSAS/下 | clearance | via_via_layer_dup | 0 | C_VIA |
| 40 | 7 | hs+pwr | 中-U3U7/上 | clearance | via_clearance | 1 | C_VIA |
| 41 | 7 | pwr+ls | 中-U3U7/上 | shorting_items | via_short | 0 | E_SCHEME |
| 42 | 7 | hs | 中-U3U7/上 | clearance | via_via_layer_dup | 7 | C_VIA |
| 43 | 7 | hs+pwr | 中-U3U7/上 | hole_clearance | via_via_hole | 0 | C_VIA |
| 44 | 6 | ls | 左-MCIO/下 | tracks_crossing | seg_crossing | 0 | A_LOWSPEED |
| 45 | 6 | pwr+ls | 左-MCIO/下 | clearance | pad_clearance | 1 | E_SCHEME |
| 46 | 6 | hs | 左-MCIO/上 | clearance | via_clearance | 0 | C_VIA |
| 47 | 6 | pwr+ls | 中-U3U7/下 | clearance | via_via_layer_dup | 0 | C_VIA |
| 48 | 6 | pwr+ls | 中-U3U7/下 | shorting_items | via_short | 0 | E_SCHEME |
| 49 | 6 | hs+pwr | 中-U3U7/下 | clearance | via_via_layer_dup | 0 | C_VIA |
| 50 | 5 | hs+pwr | 右-SlimSAS/上 | clearance | via_clearance | 0 | C_VIA |
| 51 | 5 | hs+pwr | 中-U3U7/上 | clearance | seg_clearance | 1 | E_SCHEME |
| 52 | 5 | hs+ls | 中-U3U7/上 | tracks_crossing | seg_crossing | 0 | A_LOWSPEED |
| 53 | 5 | pwr+ls | 中-U3U7/上 | clearance | via_clearance | 2 | C_VIA |
| 54 | 5 | hs+ls | 中-U3U7/上 | clearance | via_clearance | 0 | C_VIA |
| 55 | 5 | pwr+ls | 左-MCIO/下 | hole_clearance | via_hole | 1 | C_VIA |
| 56 | 5 | hs+pwr | 右-SlimSAS/上 | hole_clearance | via_hole | 0 | C_VIA |
| 57 | 5 | hs+pwr | 中-U3U7/下 | hole_clearance | via_hole | 0 | C_VIA |
| 58 | 4 | hs+pwr | 右-SlimSAS/下 | clearance | via_clearance | 2 | C_VIA |
| 59 | 4 | hs+ls | 右-SlimSAS/上 | shorting_items | via_short | 0 | E_SCHEME |
| 60 | 4 | pwr+ls | 左-MCIO/下 | clearance | via_clearance | 2 | C_VIA |
| 61 | 4 | pwr | 左-MCIO/上 | clearance | via_via_layer_dup | 0 | C_VIA |
| 62 | 3 | pwr+ls | 中-U3U7/下 | clearance | pad_clearance | 0 | E_SCHEME |
| 63 | 3 | hs+ls | 左-MCIO/上 | tracks_crossing | seg_crossing | 0 | A_LOWSPEED |
| 64 | 3 | hs+ls | 右-SlimSAS/上 | clearance | via_clearance | 2 | C_VIA |
| 65 | 3 | ls | 中-U3U7/下 | shorting_items | pad_short | 0 | E_SCHEME |
| 66 | 3 | hs | 右-SlimSAS/上 | clearance | seg_clearance | 0 | E_SCHEME |
| 67 | 3 | pwr+ls | 左-MCIO/下 | tracks_crossing | seg_crossing | 0 | A_LOWSPEED |
| 68 | 3 | pwr+ls | 中-U3U7/下 | clearance | via_clearance | 0 | C_VIA |
| 69 | 3 | pwr+ls | 中-U3U7/上 | hole_clearance | via_hole | 1 | C_VIA |
| 70 | 3 | pwr | 左-MCIO/上 | hole_clearance | via_via_hole | 0 | C_VIA |
| 71 | 3 | pwr | 中-U3U7/下 | hole_clearance | via_hole | 1 | C_VIA |
| 72 | 2 | hs+ls | 左-MCIO/上 | clearance | via_clearance | 0 | C_VIA |
| 73 | 2 | pwr+ls | 左-MCIO/上 | clearance | pad_clearance | 0 | E_SCHEME |
| 74 | 2 | hs | 右-SlimSAS/下 | clearance | pad_clearance | 0 | E_SCHEME |
| 75 | 2 | hs+pwr | 右-SlimSAS/下 | clearance | seg_clearance | 2 | E_SCHEME |
| 76 | 2 | hs | 右-SlimSAS/上 | clearance | pad_clearance | 0 | E_SCHEME |
| 77 | 2 | pwr+ls | 左-MCIO/下 | shorting_items | pad_short | 0 | E_SCHEME |
| 78 | 2 | ls | 左-MCIO/上 | hole_clearance | via_hole | 0 | C_VIA |
| 79 | 2 | pwr+ls | 左-MCIO/下 | shorting_items | seg_seg_edge0_short | 0 | E_SCHEME |
| 80 | 2 | hs+ls | 左-MCIO/上 | shorting_items | seg_seg_edge0_short | 0 | E_SCHEME |
| 81 | 2 | pwr | 中-U3U7/下 | clearance | via_clearance | 0 | C_VIA |
| 82 | 2 | hs+pwr | 右-SlimSAS/上 | clearance | via_via_layer_dup | 2 | C_VIA |
| 83 | 2 | pwr | 左-MCIO/下 | hole_clearance | via_hole | 0 | C_VIA |
| 84 | 2 | hs | 右-SlimSAS/上 | hole_clearance | via_hole | 0 | C_VIA |
| 85 | 2 | pwr | 左-MCIO/上 | zones_intersect | zone_multi_poly_overlap | 0 | B_PDN |
| 86 | 2 | pwr+ls | 中-U3U7/下 | solder_mask_bridge | smd_mask_bridge | 0 | C_MFG |
| 87 | 2 | pwr+ls | 中-U3U7/上 | solder_mask_bridge | smd_mask_bridge | 0 | C_MFG |
| 88 | 1 | pwr | 中-U3U7/上 | clearance | pad_clearance | 0 | E_SCHEME |
| 89 | 1 | hs+pwr | 右-SlimSAS/下 | shorting_items | via_short | 0 | E_SCHEME |
| 90 | 1 | pwr+ls | 左-MCIO/上 | clearance | seg_clearance | 0 | E_SCHEME |
| 91 | 1 | pwr+ls | 左-MCIO/上 | shorting_items | pad_short | 0 | E_SCHEME |
| 92 | 1 | hs+ls | 中-U3U7/下 | tracks_crossing | seg_crossing | 0 | A_LOWSPEED |
| 93 | 1 | hs+ls | 左-MCIO/下 | clearance | pad_clearance | 0 | E_SCHEME |
| 94 | 1 | hs+ls | 左-MCIO/下 | shorting_items | via_short | 0 | E_SCHEME |
| 95 | 1 | hs+ls | 左-MCIO/下 | tracks_crossing | seg_crossing | 0 | A_LOWSPEED |
| 96 | 1 | hs+ls | 左-MCIO/下 | clearance | via_clearance | 0 | C_VIA |
| 97 | 1 | hs+ls | 左-MCIO/下 | clearance | seg_clearance | 0 | E_SCHEME |
| 98 | 1 | hs+pwr | 左-MCIO/上 | clearance | via_clearance | 0 | C_VIA |
| 99 | 1 | pwr+ls | 左-MCIO/上 | shorting_items | seg_seg_edge0_short | 0 | E_SCHEME |
| 100 | 1 | hs | 左-MCIO/下 | clearance | seg_clearance | 0 | E_SCHEME |
| 101 | 1 | hs+pwr | 左-MCIO/下 | shorting_items | via_short | 0 | E_SCHEME |
| 102 | 1 | hs+pwr | 中-U3U7/下 | shorting_items | via_short | 0 | E_SCHEME |
| 103 | 1 | pwr | 左-MCIO/下 | clearance | via_clearance | 1 | C_VIA |
| 104 | 1 | pwr | 左-MCIO/上 | shorting_items | via_short | 0 | E_SCHEME |
| 105 | 1 | pwr | 左-MCIO/下 | shorting_items | via_short | 0 | E_SCHEME |
| 106 | 1 | hs+pwr | 右-SlimSAS/上 | shorting_items | via_short | 0 | E_SCHEME |
| 107 | 1 | pwr | 左-MCIO/上 | clearance | via_clearance | 1 | C_VIA |
| 108 | 1 | hs+pwr | 中-U3U7/上 | hole_clearance | via_hole | 0 | C_VIA |
| 109 | 1 | pwr | 中-U3U7/上 | hole_clearance | via_hole | 0 | C_VIA |
| 110 | 1 | pwr+ls | 右-SlimSAS/上 | hole_clearance | via_hole | 0 | C_VIA |
| 111 | 1 | pwr | 左-MCIO/上 | shorting_items | seg_seg_edge0_short | 0 | E_SCHEME |
| 112 | 1 | hs | 中-U3U7/下 | hole_clearance | via_hole | 0 | C_VIA |
| 113 | 1 | hs | 中-U3U7/上 | hole_clearance | via_hole | 0 | C_VIA |
| 114 | 1 | pwr+ls | 左-MCIO/下 | solder_mask_bridge | smd_mask_bridge | 0 | C_MFG |
| 115 | 1 | pwr+ls | 左-MCIO/下 | solder_mask_bridge | tht_mask_wildcard | 0 | C_MFG |
| 116 | 1 | pwr+ls | 左-MCIO/上 | solder_mask_bridge | smd_mask_bridge | 0 | C_MFG |
| 117 | 1 | hs | 中-U3U7/上 | diff_pair_gap_out_of_range | diff_pair_intra_gap | 0 | E_SCHEME |

### 聚类明细（含根因细节/顶层网/样例）

#### [82 条] hs 中-U3U7/下 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: PCIE_DN_OUT7_N_U3, PCIE_DN_OUT2_N_U3, PCIE_DN_OUT4_N_U3, PCIE_DN_OUT7_P_MCIO, PCIE_DN_OUT6_P_MCIO
- 高危(severe): 0 / 中(mid): 55 / 临界(crit): 27
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1475 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1475 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1233 mm)

#### [42 条] hs 中-U3U7/上 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: PCIE_UP0_N, PCIE_UP6_N, PCIE_UP1_P, PCIE_UP4_N, PCIE_UP2_P
- 高危(severe): 0 / 中(mid): 39 / 临界(crit): 3
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1230 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1225 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1225 mm)

#### [35 条] hs 中-U3U7/下 clearance → seg_clearance
- 根因: 走线段 vs 异网元素铜净距不足
- 顶层网: PCIE_DN_OUT7_N_U3, PCIE_UP6_N, PCIE_UP7_N, PCIE_DN_OUT4_N_U3, PCIE_DN_OUT7_P_U3
- 高危(severe): 0 / 中(mid): 27 / 临界(crit): 8
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1650 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1450 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.0950 mm)

#### [29 条] ls 中-U3U7/下 hole_clearance → via_via_hole
- 根因: 过孔互距不足 0.25（钻孔-钻孔边缘净距，171 系统性）
- 顶层网: STRAP_EQ0_1_U3, PD1_U3, STRAP_EQ1_U3, NO_CONNECT, PD0_U3
- 高危(severe): 0 / 中(mid): 21 / 临界(crit): 8
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2452 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2452 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2452 mm)

#### [24 条] hs+pwr 中-U3U7/下 clearance → pad_clearance
- 根因: 焊盘 vs 异网元素铜净距不足
- 顶层网: GND, P3V3, VREG2_U3, VREG1_U3, PCIE_DN_OUT4_N_U3
- 高危(severe): 5 / 中(mid): 14 / 临界(crit): 5
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.0250 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1725 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1725 mm)

#### [24 条] hs+pwr 中-U3U7/上 clearance → pad_clearance
- 根因: 焊盘 vs 异网元素铜净距不足
- 顶层网: GND, P3V3, VREG1_U7, PCIE_UP0_N, PCIE_UP1_P
- 高危(severe): 5 / 中(mid): 10 / 临界(crit): 9
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.0250 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1725 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1725 mm)

#### [23 条] ls 中-U3U7/下 hole_clearance → via_hole
- 根因: 过孔钻孔 vs 异网铜元素净距不足
- 顶层网: STRAP_MODE_U3, STRAP_EQ1_U3, STRAP_EQ0_U3, NO_CONNECT, PD1_U3
- 高危(severe): 2 / 中(mid): 15 / 临界(crit): 6
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2350 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2450 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2150 mm)

#### [22 条] hs+pwr 中-U3U7/下 solder_mask_bridge → smd_mask_bridge
- 根因: SMD 异网开窗边缘净距 < 0.05（阻焊桥）
- 顶层网: GND, P3V3, PCIE_DN3_N, PCIE_DN4_P, PCIE_DN1_N
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: C_MFG
- 样例: 顶层阻焊开窗区域与不同网络的项目相连
- 样例: 顶层阻焊开窗区域与不同网络的项目相连
- 样例: 顶层阻焊开窗区域与不同网络的项目相连

#### [21 条] hs 中-U3U7/下 clearance → pad_clearance
- 根因: 焊盘 vs 异网元素铜净距不足
- 顶层网: PCIE_DN_OUT4_N_U3, PCIE_DN_OUT4_P_MCIO, PCIE_DN3_N, PCIE_DN3_P, PCIE_DN_OUT6_N_U3
- 高危(severe): 2 / 中(mid): 7 / 临界(crit): 12
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.0750 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.0778 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1707 mm)

#### [20 条] hs+pwr 中-U3U7/上 solder_mask_bridge → smd_mask_bridge
- 根因: SMD 异网开窗边缘净距 < 0.05（阻焊桥）
- 顶层网: GND, P3V3, PCIE_UP6_N, PCIE_UP7_P, PCIE_UP_OUT5_P_U7
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: C_MFG
- 样例: 顶层阻焊开窗区域与不同网络的项目相连
- 样例: 顶层阻焊开窗区域与不同网络的项目相连
- 样例: 顶层阻焊开窗区域与不同网络的项目相连

#### [19 条] hs 中-U3U7/上 clearance → seg_clearance
- 根因: 走线段 vs 异网元素铜净距不足
- 顶层网: PCIE_UP1_P, PCIE_UP0_N, PCIE_UP1_N, PCIE_UP0_P, PCIE_UP2_P
- 高危(severe): 0 / 中(mid): 19 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1450 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.0950 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1450 mm)

#### [18 条] hs 右-SlimSAS/上 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: PCIE_UP_OUT6_N_U7, PCIE_UP_OUT5_P_J2, PCIE_UP_OUT0_N_J2, PCIE_UP_OUT7_P_J2, PCIE_UP_OUT4_N_J2
- 高危(severe): 0 / 中(mid): 15 / 临界(crit): 3
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1025 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1025 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1025 mm)

#### [16 条] hs 右-SlimSAS/上 clearance → via_via_layer_dup
- 根因: via-via 对按铜层重复报告（贯穿过孔 8 层 → 同一物理违规多行，对齐报告 §3.2）
- 顶层网: PCIE_REFCLK0_N, PCIE_REFCLK0_P, PCIE_REFCLK1_N, PCIE_REFCLK1_P
- 高危(severe): 0 / 中(mid): 16 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1200 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1200 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1200 mm)

#### [16 条] pwr+ls 左-MCIO/下 shorting_items → via_short
- 根因: 过孔铜 vs 异网元素接触短路
- 顶层网: GND, STRAP_EQ1_1_U7, I2C2_SDA, MCU_VDD, STRAP_EQ0_1_U7
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 MCU_VDD 和 UART_RX)
- 样例: 短路了两个不同网络的项目 (网络 MCU_VDD 和 STRAP_EQ0_1_U7)
- 样例: 短路了两个不同网络的项目 (网络 MCU_VDD 和 STRAP_EQ0_1_U7)

#### [16 条] pwr+ls 右-SlimSAS/上 shorting_items → via_short
- 根因: 过孔铜 vs 异网元素接触短路
- 顶层网: GND, I2C1_SCL, PERSTB#
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 I2C1_SCL 和 GND)
- 样例: 短路了两个不同网络的项目 (网络 PERSTB# 和 GND)
- 样例: 短路了两个不同网络的项目 (网络 PERSTB# 和 GND)

#### [15 条] ls 中-U3U7/上 hole_clearance → via_hole
- 根因: 过孔钻孔 vs 异网铜元素净距不足
- 顶层网: PD1_U7, STRAP_MODE_U7, STRAP_EQ0_1_U7, STRAP_EQ0_U7, NO_CONNECT
- 高危(severe): 0 / 中(mid): 12 / 临界(crit): 3
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2300 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2200 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2239 mm)

#### [15 条] ls 中-U3U7/上 hole_clearance → via_via_hole
- 根因: 过孔互距不足 0.25（钻孔-钻孔边缘净距，171 系统性）
- 顶层网: PD1_U7, STRAP_EQ0_1_U7, NO_CONNECT, STRAP_READ_EN_U7
- 高危(severe): 0 / 中(mid): 7 / 临界(crit): 8
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2250 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2250 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2250 mm)

#### [14 条] hs+pwr 中-U3U7/下 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: GND, VREG2_U3, P3V3, PCIE_DN_OUT6_P_U3, PCIE_DN_OUT6_N_U3
- 高危(severe): 5 / 中(mid): 9 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1475 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1475 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1225 mm)

#### [14 条] pwr+ls 左-MCIO/上 shorting_items → via_short
- 根因: 过孔铜 vs 异网元素接触短路
- 顶层网: GND, PD0_U7, I2C1_SDA, P3V3_AUX, STRAP_EQ1_U7
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 MCU_VDD 和 I2C1_SDA)
- 样例: 短路了两个不同网络的项目 (网络 STRAP_EQ1_U7 和 P3V3_AUX)
- 样例: 短路了两个不同网络的项目 (网络 P3V3_AUX 和 STRAP_EQ1_U7)

#### [14 条] pwr 左-MCIO/下 clearance → via_via_layer_dup
- 根因: via-via 对按铜层重复报告（贯穿过孔 8 层 → 同一物理违规多行，对齐报告 §3.2）
- 顶层网: GND, P3V3_AUX
- 高危(severe): 0 / 中(mid): 14 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1702 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1702 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1702 mm)

#### [13 条] pwr+ls 左-MCIO/下 clearance → via_via_layer_dup
- 根因: via-via 对按铜层重复报告（贯穿过孔 8 层 → 同一物理违规多行，对齐报告 §3.2）
- 顶层网: GND, I2C2_SDA, I2C1_SDA
- 高危(severe): 7 / 中(mid): 6 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.1000 mm; 实际 0.0508 mm)
- 样例: 间距违规 ( 间距 0.1000 mm; 实际 0.0508 mm)
- 样例: 间距违规 ( 间距 0.1000 mm; 实际 0.0508 mm)

#### [12 条] hs+pwr 右-SlimSAS/上 hole_clearance → via_via_hole
- 根因: 过孔互距不足 0.25（钻孔-钻孔边缘净距，171 系统性）
- 顶层网: GND, PCIE_UP_OUT3_P_J2, PCIE_UP_OUT6_N_J2
- 高危(severe): 12 / 中(mid): 0 / 临界(crit): 0
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1050 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1050 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1050 mm)

#### [11 条] hs+pwr 中-U3U7/下 clearance → seg_clearance
- 根因: 走线段 vs 异网元素铜净距不足
- 顶层网: P3V3, GND, PCIE_DN6_N, PCIE_DN2_P, PCIE_DN_OUT6_P_U3
- 高危(severe): 7 / 中(mid): 0 / 临界(crit): 4
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.0475 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.0475 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.0475 mm)

#### [11 条] hs 左-MCIO/下 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: PCIE_DN_OUT5_P_MCIO, PCIE_DN_OUT5_N_MCIO, PCIE_UP4_N, PCIE_DN_OUT6_P_MCIO, PCIE_DN_OUT4_N_MCIO
- 高危(severe): 0 / 中(mid): 6 / 临界(crit): 5
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1264 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1725 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1225 mm)

#### [10 条] ls 中-U3U7/下 tracks_crossing → seg_crossing
- 根因: 两铜段中心线几何相交（连通性触发报告，对齐报告 §3.3）
- 顶层网: STRAP_EQ0_1_U3, PD0_U3, STRAP_EQ1_1_U3, STRAP_READ_EN_U3, STRAP_EQ1_U3
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: A_LOWSPEED
- 样例: Tracks crossing
- 样例: Tracks crossing
- 样例: Tracks crossing

#### [10 条] ls 左-MCIO/下 hole_clearance → via_hole
- 根因: 过孔钻孔 vs 异网铜元素净距不足
- 顶层网: STRAP_EQ0_1_U7, I2C1_SDA, STRAP_EQ1_1_U7, I2C2_SDA, I2C2_SCL
- 高危(severe): 0 / 中(mid): 9 / 临界(crit): 1
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2250 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2058 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1750 mm)

#### [10 条] pwr+ls 左-MCIO/上 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: I2C1_SDA, P3V3_AUX, P3V3, MCU_VDD, I2C1_SCL
- 高危(severe): 4 / 中(mid): 6 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1500 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1500 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.0250 mm)

#### [9 条] ls 中-U3U7/上 tracks_crossing → seg_crossing
- 根因: 两铜段中心线几何相交（连通性触发报告，对齐报告 §3.3）
- 顶层网: PD1_U3, STRAP_EQ0_1_U7, STRAP_EQ1_1_U7, STRAP_MODE_U7, STRAP_EQ0_1_U3
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: A_LOWSPEED
- 样例: Tracks crossing
- 样例: Tracks crossing
- 样例: Tracks crossing

#### [9 条] hs+ls 中-U3U7/下 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: STRAP_READ_EN_U3, PCIE_UP7_N, PD1_U3, STRAP_EQ0_1_U7, PCIE_DN6_P
- 高危(severe): 0 / 中(mid): 7 / 临界(crit): 2
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1157 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1000 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1000 mm)

#### [9 条] hs 中-U3U7/上 clearance → pad_clearance
- 根因: 焊盘 vs 异网元素铜净距不足
- 顶层网: PCIE_UP_OUT7_N_U7, PCIE_UP_OUT4_P_U7, PCIE_UP_OUT7_P_U7, PCIE_UP0_N, PCIE_UP0_P
- 高危(severe): 1 / 中(mid): 0 / 临界(crit): 8
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1725 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.0750 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1725 mm)

#### [9 条] pwr+ls 中-U3U7/下 hole_clearance → via_hole
- 根因: 过孔钻孔 vs 异网铜元素净距不足
- 顶层网: GND, STRAP_EQ1_U3, STRAP_MODE_U3, STRAP_EQ0_1_U7, PD1_U3
- 高危(severe): 0 / 中(mid): 7 / 临界(crit): 2
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2250 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2092 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1750 mm)

#### [9 条] ls 中-U3U7/下 solder_mask_bridge → smd_mask_bridge
- 根因: SMD 异网开窗边缘净距 < 0.05（阻焊桥）
- 顶层网: STRAP_EQ1_1_U3, STRAP_MODE_U3, STRAP_EQ0_1_U3, STRAP_EQ0_U3, PD0_U3
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: C_MFG
- 样例: 顶层阻焊开窗区域与不同网络的项目相连
- 样例: 顶层阻焊开窗区域与不同网络的项目相连
- 样例: 顶层阻焊开窗区域与不同网络的项目相连

#### [8 条] ls 左-MCIO/上 tracks_crossing → seg_crossing
- 根因: 两铜段中心线几何相交（连通性触发报告，对齐报告 §3.3）
- 顶层网: I2C1_SCL, PERSTA#, STRAP_EQ0_1_U3, I2C1_SDA, STRAP_MODE_U3
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: A_LOWSPEED
- 样例: Tracks crossing
- 样例: Tracks crossing
- 样例: Tracks crossing

#### [8 条] hs 右-SlimSAS/下 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: PCIE_DN7_N, PCIE_DN7_P, PCIE_DN5_N, PCIE_DN5_P, PCIE_DN4_P
- 高危(severe): 0 / 中(mid): 8 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1225 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1225 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1225 mm)

#### [8 条] pwr 中-U3U7/下 clearance → via_via_layer_dup
- 根因: via-via 对按铜层重复报告（贯穿过孔 8 层 → 同一物理违规多行，对齐报告 §3.2）
- 顶层网: GND, P3V3
- 高危(severe): 0 / 中(mid): 8 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1110 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1110 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1110 mm)

#### [8 条] pwr+ls 左-MCIO/上 hole_clearance → via_hole
- 根因: 过孔钻孔 vs 异网铜元素净距不足
- 顶层网: GND, I2C1_SDA, STRAP_EQ1_U7, PD1_U3, MCU_VDD
- 高危(severe): 1 / 中(mid): 5 / 临界(crit): 2
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2000 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2250 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2250 mm)

#### [8 条] pwr+ls 中-U3U7/上 hole_clearance → via_via_hole
- 根因: 过孔互距不足 0.25（钻孔-钻孔边缘净距，171 系统性）
- 顶层网: GND, STRAP_EQ1_1_U7
- 高危(severe): 0 / 中(mid): 8 / 临界(crit): 0
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1778 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1778 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1778 mm)

#### [7 条] ls 中-U3U7/下 shorting_items → seg_seg_edge0_short
- 根因: 段-段铜边缘接触短路 edge==0（M11 修复：kicad DRCE_SHORTING_ITEMS 判定 actual==0）
- 顶层网: STRAP_EQ1_1_U3, STRAP_MODE_U3, PD0_U3, STRAP_READ_EN_U3, STRAP_EQ0_1_U3
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 STRAP_EQ1_1_U3 和 STRAP_MODE_U3)
- 样例: 短路了两个不同网络的项目 (网络 STRAP_EQ1_1_U3 和 STRAP_MODE_U3)
- 样例: 短路了两个不同网络的项目 (网络 STRAP_READ_EN_U3 和 PD0_U3)

#### [7 条] hs 右-SlimSAS/下 clearance → via_via_layer_dup
- 根因: via-via 对按铜层重复报告（贯穿过孔 8 层 → 同一物理违规多行，对齐报告 §3.2）
- 顶层网: PCIE_DN7_N, PCIE_DN7_P
- 高危(severe): 0 / 中(mid): 7 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1089 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1089 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1089 mm)

#### [7 条] hs+pwr 中-U3U7/上 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: P3V3, PCIE_UP5_N, VREG2_U7, PCIE_UP1_P, VREG1_U7
- 高危(severe): 1 / 中(mid): 6 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1225 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.0975 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1725 mm)

#### [7 条] pwr+ls 中-U3U7/上 shorting_items → via_short
- 根因: 过孔铜 vs 异网元素接触短路
- 顶层网: GND, PD0_U3, I2C1_SDA, P3V3, PD1_U7
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 P3V3 和 I2C1_SDA)
- 样例: 短路了两个不同网络的项目 (网络 GND 和 PD1_U7)
- 样例: 短路了两个不同网络的项目 (网络 PD0_U3 和 GND)

#### [7 条] hs 中-U3U7/上 clearance → via_via_layer_dup
- 根因: via-via 对按铜层重复报告（贯穿过孔 8 层 → 同一物理违规多行，对齐报告 §3.2）
- 顶层网: PCIE_UP_OUT0_N_U7, PCIE_UP_OUT0_P_U7
- 高危(severe): 7 / 中(mid): 0 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.0866 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.0866 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.0866 mm)

#### [7 条] hs+pwr 中-U3U7/上 hole_clearance → via_via_hole
- 根因: 过孔互距不足 0.25（钻孔-钻孔边缘净距，171 系统性）
- 顶层网: GND, PCIE_UP0_N
- 高危(severe): 0 / 中(mid): 7 / 临界(crit): 0
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1250 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1250 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1250 mm)

#### [6 条] ls 左-MCIO/下 tracks_crossing → seg_crossing
- 根因: 两铜段中心线几何相交（连通性触发报告，对齐报告 §3.3）
- 顶层网: I2C2_SDA, I2C2_SCL, STRAP_EQ1_1_U3, STRAP_EQ0_U7, STRAP_EQ0_U3
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: A_LOWSPEED
- 样例: Tracks crossing
- 样例: Tracks crossing
- 样例: Tracks crossing

#### [6 条] pwr+ls 左-MCIO/下 clearance → pad_clearance
- 根因: 焊盘 vs 异网元素铜净距不足
- 顶层网: P3V3, STRAP_READ_EN_U7, GND, I2C2_SDA, STRAP_READ_EN_U3
- 高危(severe): 1 / 中(mid): 5 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.1000 mm; 实际 0.0750 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1750 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.0750 mm)

#### [6 条] hs 左-MCIO/上 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: PCIE_DN_OUT3_P_MCIO, PCIE_DN_OUT2_P_MCIO, PCIE_UP2_P, PCIE_DN_OUT2_N_MCIO, PCIE_DN_OUT3_N_MCIO
- 高危(severe): 0 / 中(mid): 6 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1225 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1225 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1225 mm)

#### [6 条] pwr+ls 中-U3U7/下 clearance → via_via_layer_dup
- 根因: via-via 对按铜层重复报告（贯穿过孔 8 层 → 同一物理违规多行，对齐报告 §3.2）
- 顶层网: STRAP_READ_EN_U3, VREG1_U3
- 高危(severe): 0 / 中(mid): 6 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1485 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1485 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1485 mm)

#### [6 条] pwr+ls 中-U3U7/下 shorting_items → via_short
- 根因: 过孔铜 vs 异网元素接触短路
- 顶层网: GND, PD0_U3, STRAP_MODE_U3, STRAP_READ_EN_U3
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 PD0_U3 和 GND)
- 样例: 短路了两个不同网络的项目 (网络 PD0_U3 和 GND)
- 样例: 短路了两个不同网络的项目 (网络 GND 和 STRAP_READ_EN_U3)

#### [6 条] hs+pwr 中-U3U7/下 clearance → via_via_layer_dup
- 根因: via-via 对按铜层重复报告（贯穿过孔 8 层 → 同一物理违规多行，对齐报告 §3.2）
- 顶层网: GND, PCIE_DN_OUT4_P_U3
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 6
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1654 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1654 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1654 mm)

#### [5 条] hs+pwr 右-SlimSAS/上 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: GND, PCIE_UP_OUT3_N_J2, PCIE_UP_OUT0_N_J2, PCIE_REFCLK1_N, PCIE_UP_OUT4_P_J2
- 高危(severe): 0 / 中(mid): 4 / 临界(crit): 1
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1025 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1025 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1725 mm)

#### [5 条] hs+pwr 中-U3U7/上 clearance → seg_clearance
- 根因: 走线段 vs 异网元素铜净距不足
- 顶层网: P3V3, PCIE_UP6_P, PCIE_UP5_N, GND, PCIE_UP6_N
- 高危(severe): 1 / 中(mid): 0 / 临界(crit): 4
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.0475 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1950 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1950 mm)

#### [5 条] hs+ls 中-U3U7/上 tracks_crossing → seg_crossing
- 根因: 两铜段中心线几何相交（连通性触发报告，对齐报告 §3.3）
- 顶层网: STRAP_EQ1_U7, PCIE_UP0_N, PCIE_DN_OUT2_N_MCIO, STRAP_EQ0_U7, PCIE_UP7_P
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: A_LOWSPEED
- 样例: Tracks crossing
- 样例: Tracks crossing
- 样例: Tracks crossing

#### [5 条] pwr+ls 中-U3U7/上 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: GND, P3V3, STRAP_EQ1_U7, PERSTB#, STRAP_EQ0_U7
- 高危(severe): 2 / 中(mid): 3 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.0100 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1000 mm)
- 样例: 间距违规 ( 间距 0.1000 mm; 实际 0.0750 mm)

#### [5 条] hs+ls 中-U3U7/上 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: STRAP_EQ1_U7, PCIE_UP7_N, PCIE_UP7_P, PCIE_UP6_N
- 高危(severe): 0 / 中(mid): 5 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1250 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1200 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1100 mm)

#### [5 条] pwr+ls 左-MCIO/下 hole_clearance → via_hole
- 根因: 过孔钻孔 vs 异网铜元素净距不足
- 顶层网: GND, I2C2_SDA, I2C1_SDA, MCU_VDD, STRAP_EQ1_1_U3
- 高危(severe): 1 / 中(mid): 3 / 临界(crit): 1
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2258 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2000 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.0500 mm)

#### [5 条] hs+pwr 右-SlimSAS/上 hole_clearance → via_hole
- 根因: 过孔钻孔 vs 异网铜元素净距不足
- 顶层网: GND, PCIE_REFCLK1_N, PCIE_UP_OUT0_N_J2, PCIE_UP_OUT6_P_J2, PCIE_UP_OUT3_P_J2
- 高危(severe): 0 / 中(mid): 5 / 临界(crit): 0
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1975 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1775 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1775 mm)

#### [5 条] hs+pwr 中-U3U7/下 hole_clearance → via_hole
- 根因: 过孔钻孔 vs 异网铜元素净距不足
- 顶层网: GND, PCIE_DN_OUT5_N_MCIO, PCIE_DN_OUT7_N_MCIO, PCIE_DN_OUT4_P_U3, P3V3
- 高危(severe): 0 / 中(mid): 4 / 临界(crit): 1
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2475 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1775 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1654 mm)

#### [4 条] hs+pwr 右-SlimSAS/下 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: P3V3, PCIE_DN2_P, GND, PCIE_DN4_N, PCIE_DN0_N
- 高危(severe): 2 / 中(mid): 2 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1225 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.0781 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1225 mm)

#### [4 条] hs+ls 右-SlimSAS/上 shorting_items → via_short
- 根因: 过孔铜 vs 异网元素接触短路
- 顶层网: I2C1_SCL, PCIE_REFCLK0_P, PCIE_UP_OUT4_P_J2, PERSTA#, PCIE_DN1_P
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 PCIE_REFCLK0_P 和 I2C1_SCL)
- 样例: 短路了两个不同网络的项目 (网络 PERSTA# 和 PCIE_UP_OUT4_P_J2)
- 样例: 短路了两个不同网络的项目 (网络 I2C1_SCL 和 PCIE_DN1_P)

#### [4 条] pwr+ls 左-MCIO/下 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: GND, I2C2_SDA, STRAP_EQ1_1_U7, UART_RX
- 高危(severe): 2 / 中(mid): 2 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.1000 mm; 实际 0.0500 mm)
- 样例: 间距违规 ( 间距 0.1000 mm; 实际 0.0500 mm)
- 样例: 间距违规 ( 间距 0.1000 mm; 实际 0.0110 mm)

#### [4 条] pwr 左-MCIO/上 clearance → via_via_layer_dup
- 根因: via-via 对按铜层重复报告（贯穿过孔 8 层 → 同一物理违规多行，对齐报告 §3.2）
- 顶层网: GND, MCU_VDD
- 高危(severe): 0 / 中(mid): 4 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1500 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1500 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1500 mm)

#### [3 条] pwr+ls 中-U3U7/下 clearance → pad_clearance
- 根因: 焊盘 vs 异网元素铜净距不足
- 顶层网: GND, STRAP_EQ1_U3, ALL_DONE_N_U3, VREG1_U3
- 高危(severe): 0 / 中(mid): 3 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.1000 mm; 实际 0.0592 mm)
- 样例: 间距违规 ( 间距 0.1000 mm; 实际 0.0750 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1475 mm)

#### [3 条] hs+ls 左-MCIO/上 tracks_crossing → seg_crossing
- 根因: 两铜段中心线几何相交（连通性触发报告，对齐报告 §3.3）
- 顶层网: I2C1_SCL, PCIE_DN_OUT3_P_MCIO, PCIE_UP3_P, PCIE_DN_OUT4_N_MCIO
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: A_LOWSPEED
- 样例: Tracks crossing
- 样例: Tracks crossing
- 样例: Tracks crossing

#### [3 条] hs+ls 右-SlimSAS/上 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: I2C1_SDA, PCIE_REFCLK0_N, PCIE_UP_OUT4_P_J2, PERSTB#, PCIE_REFCLK1_N
- 高危(severe): 2 / 中(mid): 1 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.0700 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1300 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.0700 mm)

#### [3 条] ls 中-U3U7/下 shorting_items → pad_short
- 根因: 焊盘 vs 异网元素接触短路
- 顶层网: STRAP_EQ1_1_U3, STRAP_MODE_U3, STRAP_EQ0_1_U3, STRAP_EQ0_U3, PD0_U3
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 STRAP_EQ1_1_U3 和 STRAP_MODE_U3)
- 样例: 短路了两个不同网络的项目 (网络 STRAP_EQ0_1_U3 和 STRAP_EQ0_U3)
- 样例: 短路了两个不同网络的项目 (网络 STRAP_READ_EN_U3 和 PD0_U3)

#### [3 条] hs 右-SlimSAS/上 clearance → seg_clearance
- 根因: 走线段 vs 异网元素铜净距不足
- 顶层网: PCIE_UP_OUT6_N_U7, PCIE_UP_OUT7_P_U7
- 高危(severe): 0 / 中(mid): 3 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1050 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1050 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1050 mm)

#### [3 条] pwr+ls 左-MCIO/下 tracks_crossing → seg_crossing
- 根因: 两铜段中心线几何相交（连通性触发报告，对齐报告 §3.3）
- 顶层网: MCU_VDD, STRAP_EQ0_1_U7, I2C2_SDA, GND
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: A_LOWSPEED
- 样例: Tracks crossing
- 样例: Tracks crossing
- 样例: Tracks crossing

#### [3 条] pwr+ls 中-U3U7/下 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: STRAP_READ_EN_U3, VREG1_U3, P3V3, STRAP_EQ1_1_U7
- 高危(severe): 0 / 中(mid): 3 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1000 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1050 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1750 mm)

#### [3 条] pwr+ls 中-U3U7/上 hole_clearance → via_hole
- 根因: 过孔钻孔 vs 异网铜元素净距不足
- 顶层网: GND, PERSTB#, STRAP_EQ1_1_U7, PD0_U7
- 高危(severe): 1 / 中(mid): 2 / 临界(crit): 0
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1750 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1028 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1868 mm)

#### [3 条] pwr 左-MCIO/上 hole_clearance → via_via_hole
- 根因: 过孔互距不足 0.25（钻孔-钻孔边缘净距，171 系统性）
- 顶层网: GND, MCU_VDD
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 3
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2250 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2250 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2250 mm)

#### [3 条] pwr 中-U3U7/下 hole_clearance → via_hole
- 根因: 过孔钻孔 vs 异网铜元素净距不足
- 顶层网: GND, P3V3
- 高危(severe): 1 / 中(mid): 2 / 临界(crit): 0
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2034 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1908 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1110 mm)

#### [2 条] hs+ls 左-MCIO/上 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: I2C1_SDA, PCIE_DN_OUT3_N_MCIO, PCIE_DN_OUT4_P_MCIO
- 高危(severe): 0 / 中(mid): 2 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1000 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1000 mm)

#### [2 条] pwr+ls 左-MCIO/上 clearance → pad_clearance
- 根因: 焊盘 vs 异网元素铜净距不足
- 顶层网: GND, PD1_U3, MCU_VDD, NO_CONNECT
- 高危(severe): 0 / 中(mid): 2 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.1000 mm; 实际 0.0750 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1000 mm)

#### [2 条] hs 右-SlimSAS/下 clearance → pad_clearance
- 根因: 焊盘 vs 异网元素铜净距不足
- 顶层网: PCIE_DN7_N, PCIE_DN7_P, PCIE_DN3_N, PCIE_DN3_P
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 2
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1725 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1725 mm)

#### [2 条] hs+pwr 右-SlimSAS/下 clearance → seg_clearance
- 根因: 走线段 vs 异网元素铜净距不足
- 顶层网: P3V3, PCIE_DN6_P, PCIE_DN5_N
- 高危(severe): 2 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.0475 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.0475 mm)

#### [2 条] hs 右-SlimSAS/上 clearance → pad_clearance
- 根因: 焊盘 vs 异网元素铜净距不足
- 顶层网: PCIE_UP_OUT4_N_J2, PCIE_UP_OUT4_P_U7, PCIE_UP_OUT6_N_J2, PCIE_UP_OUT6_P_U7
- 高危(severe): 0 / 中(mid): 1 / 临界(crit): 1
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1736 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1291 mm)

#### [2 条] pwr+ls 左-MCIO/下 shorting_items → pad_short
- 根因: 焊盘 vs 异网元素接触短路
- 顶层网: GND, UART_RX, MCU_VDD, STRAP_EQ1_1_U3
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 GND 和 UART_RX)
- 样例: 短路了两个不同网络的项目 (网络 STRAP_EQ1_1_U3 和 MCU_VDD)

#### [2 条] ls 左-MCIO/上 hole_clearance → via_hole
- 根因: 过孔钻孔 vs 异网铜元素净距不足
- 顶层网: PERSTA#, PWR_BTN_ISO, PD0_U3, PD0_U7
- 高危(severe): 0 / 中(mid): 1 / 临界(crit): 1
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2250 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1750 mm)

#### [2 条] pwr+ls 左-MCIO/下 shorting_items → seg_seg_edge0_short
- 根因: 段-段铜边缘接触短路 edge==0（M11 修复：kicad DRCE_SHORTING_ITEMS 判定 actual==0）
- 顶层网: P3V3, STRAP_MODE_U7, GND, STRAP_EQ1_1_U7
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 P3V3 和 STRAP_MODE_U7)
- 样例: 短路了两个不同网络的项目 (网络 STRAP_EQ1_1_U7 和 GND)

#### [2 条] hs+ls 左-MCIO/上 shorting_items → seg_seg_edge0_short
- 根因: 段-段铜边缘接触短路 edge==0（M11 修复：kicad DRCE_SHORTING_ITEMS 判定 actual==0）
- 顶层网: I2C1_SCL, PCIE_DN_OUT4_N_MCIO
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 I2C1_SCL 和 PCIE_DN_OUT4_N_MCIO)
- 样例: 短路了两个不同网络的项目 (网络 I2C1_SCL 和 PCIE_DN_OUT4_N_MCIO)

#### [2 条] pwr 中-U3U7/下 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: GND, P3V3
- 高危(severe): 0 / 中(mid): 2 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1000 mm)
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1158 mm)

#### [2 条] hs+pwr 右-SlimSAS/上 clearance → via_via_layer_dup
- 根因: via-via 对按铜层重复报告（贯穿过孔 8 层 → 同一物理违规多行，对齐报告 §3.2）
- 顶层网: GND, PCIE_UP_OUT6_N_J2
- 高危(severe): 2 / 中(mid): 0 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.0300 mm)
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.0300 mm)

#### [2 条] pwr 左-MCIO/下 hole_clearance → via_hole
- 根因: 过孔钻孔 vs 异网铜元素净距不足
- 顶层网: GND, P3V3_AUX
- 高危(severe): 0 / 中(mid): 2 / 临界(crit): 0
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1702 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1702 mm)

#### [2 条] hs 右-SlimSAS/上 hole_clearance → via_hole
- 根因: 过孔钻孔 vs 异网铜元素净距不足
- 顶层网: PCIE_UP_OUT6_N_J2, PCIE_UP_OUT6_P_U7, PCIE_UP_OUT4_N_J2, PCIE_UP_OUT4_P_U7
- 高危(severe): 0 / 中(mid): 1 / 临界(crit): 1
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2041 mm)
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2486 mm)

#### [2 条] pwr 左-MCIO/上 zones_intersect → zone_multi_poly_overlap
- 根因: 同网 zone 多多边形重叠（M11 修复 Zone.polys 全量收集，kicad 要求不同优先级）
- 顶层网: P3V3_AUX, P3V3
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: B_PDN
- 样例: 覆铜区相交 (相交的填充区必须具有不同的优先级)
- 样例: 覆铜区相交 (相交的填充区必须具有不同的优先级)

#### [2 条] pwr+ls 中-U3U7/下 solder_mask_bridge → smd_mask_bridge
- 根因: SMD 异网开窗边缘净距 < 0.05（阻焊桥）
- 顶层网: GND, NO_CONNECT, ALL_DONE_N_U3
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: C_MFG
- 样例: 顶层阻焊开窗区域与不同网络的项目相连
- 样例: 顶层阻焊开窗区域与不同网络的项目相连

#### [2 条] pwr+ls 中-U3U7/上 solder_mask_bridge → smd_mask_bridge
- 根因: SMD 异网开窗边缘净距 < 0.05（阻焊桥）
- 顶层网: GND, NO_CONNECT, ALL_DONE_N_U7
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: C_MFG
- 样例: 顶层阻焊开窗区域与不同网络的项目相连
- 样例: 顶层阻焊开窗区域与不同网络的项目相连

#### [1 条] pwr 中-U3U7/上 clearance → pad_clearance
- 根因: 焊盘 vs 异网元素铜净距不足
- 顶层网: GND, P3V3
- 高危(severe): 0 / 中(mid): 1 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1750 mm)

#### [1 条] hs+pwr 右-SlimSAS/下 shorting_items → via_short
- 根因: 过孔铜 vs 异网元素接触短路
- 顶层网: GND, PCIE_DN5_P
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 PCIE_DN5_P 和 GND)

#### [1 条] pwr+ls 左-MCIO/上 clearance → seg_clearance
- 根因: 走线段 vs 异网元素铜净距不足
- 顶层网: I2C1_SDA, MCU_VDD
- 高危(severe): 0 / 中(mid): 1 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1750 mm)

#### [1 条] pwr+ls 左-MCIO/上 shorting_items → pad_short
- 根因: 焊盘 vs 异网元素接触短路
- 顶层网: MCU_VDD, SWCLK_BOOT0
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 SWCLK_BOOT0 和 MCU_VDD)

#### [1 条] hs+ls 中-U3U7/下 tracks_crossing → seg_crossing
- 根因: 两铜段中心线几何相交（连通性触发报告，对齐报告 §3.3）
- 顶层网: PCIE_UP7_P, STRAP_EQ0_U7
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: A_LOWSPEED
- 样例: Tracks crossing

#### [1 条] hs+ls 左-MCIO/下 clearance → pad_clearance
- 根因: 焊盘 vs 异网元素铜净距不足
- 顶层网: PCIE_UP4_P, PERSTB#
- 高危(severe): 0 / 中(mid): 1 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1250 mm)

#### [1 条] hs+ls 左-MCIO/下 shorting_items → via_short
- 根因: 过孔铜 vs 异网元素接触短路
- 顶层网: PCIE_UP5_N, PERSTB#
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 PCIE_UP5_N 和 PERSTB#)

#### [1 条] hs+ls 左-MCIO/下 tracks_crossing → seg_crossing
- 根因: 两铜段中心线几何相交（连通性触发报告，对齐报告 §3.3）
- 顶层网: PCIE_UP5_N, PERSTB#
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: A_LOWSPEED
- 样例: Tracks crossing

#### [1 条] hs+ls 左-MCIO/下 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: I2C1_SCL, PCIE_UP4_N
- 高危(severe): 0 / 中(mid): 1 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1000 mm)

#### [1 条] hs+ls 左-MCIO/下 clearance → seg_clearance
- 根因: 走线段 vs 异网元素铜净距不足
- 顶层网: I2C1_SCL, PCIE_UP4_N
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 1
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1725 mm)

#### [1 条] hs+pwr 左-MCIO/上 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: P3V3_AUX, PCIE_DN_OUT2_P_MCIO
- 高危(severe): 0 / 中(mid): 1 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.1725 mm)

#### [1 条] pwr+ls 左-MCIO/上 shorting_items → seg_seg_edge0_short
- 根因: 段-段铜边缘接触短路 edge==0（M11 修复：kicad DRCE_SHORTING_ITEMS 判定 actual==0）
- 顶层网: P3V3_AUX, STRAP_EQ1_U7
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 STRAP_EQ1_U7 和 P3V3_AUX)

#### [1 条] hs 左-MCIO/下 clearance → seg_clearance
- 根因: 走线段 vs 异网元素铜净距不足
- 顶层网: PCIE_DN_OUT4_N_MCIO, PCIE_DN_OUT5_P_MCIO
- 高危(severe): 0 / 中(mid): 1 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 间距违规 ( 间距 0.1750 mm; 实际 0.1450 mm)

#### [1 条] hs+pwr 左-MCIO/下 shorting_items → via_short
- 根因: 过孔铜 vs 异网元素接触短路
- 顶层网: P3V3_AUX, PCIE_DN_OUT5_P_MCIO
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 P3V3_AUX 和 PCIE_DN_OUT5_P_MCIO)

#### [1 条] hs+pwr 中-U3U7/下 shorting_items → via_short
- 根因: 过孔铜 vs 异网元素接触短路
- 顶层网: GND, PCIE_DN_OUT4_N_MCIO
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 PCIE_DN_OUT4_N_MCIO 和 GND)

#### [1 条] pwr 左-MCIO/下 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: GND, P3V3_AUX
- 高危(severe): 1 / 中(mid): 0 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.0952 mm)

#### [1 条] pwr 左-MCIO/上 shorting_items → via_short
- 根因: 过孔铜 vs 异网元素接触短路
- 顶层网: GND, MCU_VDD
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 MCU_VDD 和 GND)

#### [1 条] pwr 左-MCIO/下 shorting_items → via_short
- 根因: 过孔铜 vs 异网元素接触短路
- 顶层网: GND, P3V3_AUX
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 GND 和 P3V3_AUX)

#### [1 条] hs+pwr 右-SlimSAS/上 shorting_items → via_short
- 根因: 过孔铜 vs 异网元素接触短路
- 顶层网: GND, PCIE_UP_OUT4_P_J2
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 PCIE_UP_OUT4_P_J2 和 GND)

#### [1 条] pwr 左-MCIO/上 clearance → via_clearance
- 根因: 过孔 vs 异网元素铜净距不足
- 顶层网: GND, MCU_VDD
- 高危(severe): 1 / 中(mid): 0 / 临界(crit): 0
- 路径: C_VIA
- 样例: 间距违规 ( 间距 0.2000 mm; 实际 0.0750 mm)

#### [1 条] hs+pwr 中-U3U7/上 hole_clearance → via_hole
- 根因: 过孔钻孔 vs 异网铜元素净距不足
- 顶层网: GND, PCIE_UP0_N
- 高危(severe): 0 / 中(mid): 1 / 临界(crit): 0
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1975 mm)

#### [1 条] pwr 中-U3U7/上 hole_clearance → via_hole
- 根因: 过孔钻孔 vs 异网铜元素净距不足
- 顶层网: GND, P3V3
- 高危(severe): 0 / 中(mid): 1 / 临界(crit): 0
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1908 mm)

#### [1 条] pwr+ls 右-SlimSAS/上 hole_clearance → via_hole
- 根因: 过孔钻孔 vs 异网铜元素净距不足
- 顶层网: GND, I2C1_SDA
- 高危(severe): 0 / 中(mid): 1 / 临界(crit): 0
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.2050 mm)

#### [1 条] pwr 左-MCIO/上 shorting_items → seg_seg_edge0_short
- 根因: 段-段铜边缘接触短路 edge==0（M11 修复：kicad DRCE_SHORTING_ITEMS 判定 actual==0）
- 顶层网: GND, MCU_VDD
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 短路了两个不同网络的项目 (网络 GND 和 MCU_VDD)

#### [1 条] hs 中-U3U7/下 hole_clearance → via_hole
- 根因: 过孔钻孔 vs 异网铜元素净距不足
- 顶层网: PCIE_DN_OUT2_P_MCIO, PCIE_DN_OUT2_P_U3
- 高危(severe): 0 / 中(mid): 1 / 临界(crit): 0
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1500 mm)

#### [1 条] hs 中-U3U7/上 hole_clearance → via_hole
- 根因: 过孔钻孔 vs 异网铜元素净距不足
- 顶层网: PCIE_UP_OUT4_P_U7, PCIE_UP_OUT7_N_U7
- 高危(severe): 0 / 中(mid): 1 / 临界(crit): 0
- 路径: C_VIA
- 样例: 孔间距违规 (<电路板配置> 中的 "孔" 约束 间距 0.2500 mm; 实际 0.1500 mm)

#### [1 条] pwr+ls 左-MCIO/下 solder_mask_bridge → smd_mask_bridge
- 根因: SMD 异网开窗边缘净距 < 0.05（阻焊桥）
- 顶层网: MCU_VDD, STRAP_EQ1_1_U3
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: C_MFG
- 样例: 顶层阻焊开窗区域与不同网络的项目相连

#### [1 条] pwr+ls 左-MCIO/下 solder_mask_bridge → tht_mask_wildcard
- 根因: THT pad 开窗通配符 '*.Mask'（M11 修复 _pad_has_mask 展开，如 J9）
- 顶层网: GND, UART_RX
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: C_MFG
- 样例: 底层阻焊开窗区域与不同网络的项目相连

#### [1 条] pwr+ls 左-MCIO/上 solder_mask_bridge → smd_mask_bridge
- 根因: SMD 异网开窗边缘净距 < 0.05（阻焊桥）
- 顶层网: MCU_VDD, SWCLK_BOOT0
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: C_MFG
- 样例: 顶层阻焊开窗区域与不同网络的项目相连

#### [1 条] hs 中-U3U7/上 diff_pair_gap_out_of_range → diff_pair_intra_gap
- 根因: 差分对内 P/N 间距 < min gap = board rules.min_clearance 0.1（M11 修复：非 netclass diff_pair_gap 0.175，后者仅 Opt 目标）
- 顶层网: PCIE_UP1_N, PCIE_UP1_P
- 高危(severe): 0 / 中(mid): 0 / 临界(crit): 0
- 路径: E_SCHEME
- 样例: 差分对间隙超出范围 (网络类 'PCIe85' (差分对) 最小间隙 0.1000 mm; 实际 0.0950 mm)

## 4. 高危清单（间距 < 50%，severe）

共 78 条（按间距比例升序，越靠前越危险）：

| 序 | 类型 | 域 | 区域 | 实际/要求 | 比例 | 网对 |
|---|---|---|---|---|---|---|
| 382 | clearance | pwr+ls | 中-U3U7/上 | 0.0100/0.2000 | 5.00% | P3V3/STRAP_EQ1_U7 |
| 652 | clearance | pwr+ls | 中-U3U7/上 | 0.0100/0.1000 | 10.00% | GND/STRAP_EQ1_U7 |
| 666 | clearance | pwr+ls | 左-MCIO/下 | 0.0110/0.1000 | 11.00% | GND/STRAP_EQ1_1_U7 |
| 367 | clearance | pwr+ls | 左-MCIO/上 | 0.0250/0.2000 | 12.50% | P3V3/PWR_BTN_ISO |
| 381 | clearance | hs+pwr | 中-U3U7/上 | 0.0250/0.2000 | 12.50% | P3V3/PCIE_UP_OUT1_N_U7 |
| 384 | clearance | hs+pwr | 中-U3U7/上 | 0.0250/0.2000 | 12.50% | P3V3/PCIE_UP6_P |
| 385 | clearance | hs+pwr | 中-U3U7/下 | 0.0250/0.2000 | 12.50% | P3V3/PCIE_DN_OUT2_P_U3 |
| 388 | clearance | hs+pwr | 中-U3U7/上 | 0.0250/0.2000 | 12.50% | P3V3/PCIE_UP1_N |
| 389 | clearance | hs+pwr | 中-U3U7/上 | 0.0250/0.2000 | 12.50% | P3V3/PCIE_UP_OUT6_P_U7 |
| 391 | clearance | hs+pwr | 中-U3U7/下 | 0.0250/0.2000 | 12.50% | P3V3/PCIE_DN6_P |
| 4 | clearance | hs+pwr | 中-U3U7/下 | 0.0250/0.1750 | 14.29% | GND/PCIE_DN6_N |
| 9 | clearance | hs+pwr | 中-U3U7/上 | 0.0250/0.1750 | 14.29% | GND/PCIE_UP_OUT5_P_U7 |
| 657 | clearance | hs+pwr | 中-U3U7/下 | 0.0275/0.1750 | 15.71% | GND/PCIE_UP6_P |
| 707 | clearance | hs+pwr | 右-SlimSAS/上 | 0.0300/0.1750 | 17.14% | GND/PCIE_UP_OUT6_N_J2 |
| 708 | clearance | hs+pwr | 右-SlimSAS/上 | 0.0300/0.1750 | 17.14% | GND/PCIE_UP_OUT6_N_J2 |
| 785 | hole_clearance | pwr+ls | 左-MCIO/下 | 0.0500/0.2500 | 20.00% | MCU_VDD/STRAP_EQ1_1_U3 |
| 698 | clearance | hs+pwr | 右-SlimSAS/下 | 0.0373/0.1750 | 21.31% | GND/PCIE_DN0_N |
| 125 | clearance | hs+pwr | 中-U3U7/下 | 0.0475/0.2000 | 23.75% | P3V3/PCIE_DN6_P |
| 126 | clearance | hs+pwr | 右-SlimSAS/下 | 0.0475/0.2000 | 23.75% | P3V3/PCIE_DN6_P |
| 128 | clearance | hs+pwr | 右-SlimSAS/下 | 0.0475/0.2000 | 23.75% | P3V3/PCIE_DN5_N |
| 131 | clearance | hs+pwr | 中-U3U7/下 | 0.0475/0.2000 | 23.75% | P3V3/PCIE_DN5_N |
| 387 | clearance | hs+pwr | 中-U3U7/下 | 0.0475/0.2000 | 23.75% | P3V3/PCIE_DN_OUT6_P_U3 |
| 393 | clearance | hs+pwr | 中-U3U7/下 | 0.0475/0.2000 | 23.75% | P3V3/PCIE_DN2_P |
| 518 | clearance | pwr+ls | 左-MCIO/上 | 0.0500/0.2000 | 25.00% | I2C1_SCL/P3V3_AUX |
| 521 | clearance | pwr+ls | 左-MCIO/上 | 0.0500/0.2000 | 25.00% | I2C1_SCL/P3V3_AUX |
| 632 | clearance | pwr+ls | 左-MCIO/下 | 0.0250/0.1000 | 25.00% | GND/I2C2_SDA |
| 634 | clearance | pwr+ls | 左-MCIO/上 | 0.0250/0.1000 | 25.00% | GND/UART_RX |
| 635 | clearance | pwr+ls | 左-MCIO/下 | 0.0250/0.1000 | 25.00% | GND/I2C2_SDA |
| 636 | clearance | pwr+ls | 左-MCIO/下 | 0.0250/0.1000 | 25.00% | GND/I2C2_SDA |
| 637 | clearance | pwr+ls | 左-MCIO/下 | 0.0250/0.1000 | 25.00% | GND/I2C2_SDA |
| 638 | clearance | pwr+ls | 左-MCIO/下 | 0.0250/0.1000 | 25.00% | GND/I2C2_SDA |
| 640 | clearance | pwr+ls | 左-MCIO/下 | 0.0250/0.1000 | 25.00% | GND/I2C2_SDA |
| 641 | clearance | pwr+ls | 左-MCIO/下 | 0.0250/0.1000 | 25.00% | GND/I2C2_SDA |
| 18 | clearance | hs+pwr | 中-U3U7/上 | 0.0475/0.1750 | 27.14% | GND/PCIE_UP6_N |
| 114 | clearance | hs+pwr | 中-U3U7/下 | 0.0475/0.1750 | 27.14% | GND/PCIE_DN7_P |
| 117 | clearance | hs+pwr | 中-U3U7/下 | 0.0475/0.1750 | 27.14% | GND/PCIE_DN6_N |
| 120 | clearance | hs+pwr | 中-U3U7/下 | 0.0475/0.1750 | 27.14% | GND/PCIE_DN6_N |
| 628 | clearance | hs+pwr | 中-U3U7/下 | 0.0475/0.1750 | 27.14% | GND/PCIE_DN_OUT5_P_U3 |
| 689 | clearance | hs+pwr | 中-U3U7/下 | 0.0475/0.1750 | 27.14% | GND/PCIE_DN_OUT6_P_U3 |
| 797 | hole_clearance | ls | 中-U3U7/下 | 0.0750/0.2500 | 30.00% | STRAP_EQ0_1_U3/STRAP_EQ0_U3 |
| 378 | clearance | hs+pwr | 中-U3U7/下 | 0.0725/0.2000 | 36.25% | P3V3/PCIE_DN_OUT5_P_U3 |
| 343 | clearance | pwr+ls | 左-MCIO/下 | 0.0750/0.2000 | 37.50% | P3V3/STRAP_READ_EN_U7 |
| 694 | clearance | pwr | 左-MCIO/上 | 0.0750/0.2000 | 37.50% | GND/MCU_VDD |
| 75 | clearance | hs+pwr | 中-U3U7/下 | 0.0799/0.2000 | 39.95% | P3V3/PCIE_DN_OUT4_N_U3 |
| 60 | clearance | hs+ls | 右-SlimSAS/上 | 0.0700/0.1750 | 40.00% | I2C1_SDA/PCIE_REFCLK0_N |
| 503 | clearance | hs+ls | 右-SlimSAS/上 | 0.0700/0.1750 | 40.00% | I2C1_SDA/PCIE_REFCLK1_N |
| 768 | hole_clearance | pwr+ls | 中-U3U7/上 | 0.1028/0.2500 | 41.12% | GND/STRAP_EQ1_1_U7 |
| 713 | hole_clearance | hs+pwr | 右-SlimSAS/上 | 0.1050/0.2500 | 42.00% | GND/PCIE_UP_OUT6_N_J2 |
| 716 | hole_clearance | hs+pwr | 右-SlimSAS/上 | 0.1050/0.2500 | 42.00% | GND/PCIE_UP_OUT6_N_J2 |
| 719 | hole_clearance | hs+pwr | 右-SlimSAS/上 | 0.1050/0.2500 | 42.00% | GND/PCIE_UP_OUT6_N_J2 |
| 725 | hole_clearance | hs+pwr | 右-SlimSAS/上 | 0.1050/0.2500 | 42.00% | GND/PCIE_UP_OUT6_N_J2 |
| 728 | hole_clearance | hs+pwr | 右-SlimSAS/上 | 0.1050/0.2500 | 42.00% | GND/PCIE_UP_OUT6_N_J2 |
| 756 | hole_clearance | hs+pwr | 右-SlimSAS/上 | 0.1050/0.2500 | 42.00% | GND/PCIE_UP_OUT3_P_J2 |
| 759 | hole_clearance | hs+pwr | 右-SlimSAS/上 | 0.1050/0.2500 | 42.00% | GND/PCIE_UP_OUT3_P_J2 |
| 760 | hole_clearance | hs+pwr | 右-SlimSAS/上 | 0.1050/0.2500 | 42.00% | GND/PCIE_UP_OUT3_P_J2 |
| 765 | hole_clearance | hs+pwr | 右-SlimSAS/上 | 0.1050/0.2500 | 42.00% | GND/PCIE_UP_OUT3_P_J2 |
| 766 | hole_clearance | hs+pwr | 右-SlimSAS/上 | 0.1050/0.2500 | 42.00% | GND/PCIE_UP_OUT3_P_J2 |
| 769 | hole_clearance | hs+pwr | 右-SlimSAS/上 | 0.1050/0.2500 | 42.00% | GND/PCIE_UP_OUT3_P_J2 |
| 770 | hole_clearance | hs+pwr | 右-SlimSAS/上 | 0.1050/0.2500 | 42.00% | GND/PCIE_UP_OUT3_P_J2 |
| 48 | clearance | hs | 中-U3U7/下 | 0.0750/0.1750 | 42.86% | PCIE_DN_OUT2_P_MCIO/PCIE_DN_OUT2_P_U3 |
| 174 | clearance | hs | 中-U3U7/上 | 0.0750/0.1750 | 42.86% | PCIE_UP_OUT4_P_U7/PCIE_UP_OUT7_N_U7 |
| 306 | clearance | hs+pwr | 中-U3U7/下 | 0.0750/0.1750 | 42.86% | GND/PCIE_DN_OUT5_P_U3 |
| 784 | hole_clearance | pwr | 中-U3U7/下 | 0.1110/0.2500 | 44.40% | GND/P3V3 |
| 49 | clearance | hs | 中-U3U7/下 | 0.0778/0.1750 | 44.46% | PCIE_DN_OUT2_P_MCIO/PCIE_DN_OUT2_P_U3 |
| 678 | clearance | pwr+ls | 左-MCIO/下 | 0.0445/0.1000 | 44.50% | GND/UART_RX |
| 142 | clearance | hs+pwr | 右-SlimSAS/下 | 0.0781/0.1750 | 44.63% | GND/PCIE_DN4_N |
| 695 | clearance | hs+pwr | 中-U3U7/下 | 0.0794/0.1750 | 45.37% | GND/PCIE_DN_OUT5_N_MCIO |
| 611 | clearance | pwr | 左-MCIO/下 | 0.0952/0.2000 | 47.60% | GND/P3V3_AUX |
| 377 | clearance | hs+pwr | 中-U3U7/上 | 0.0975/0.2000 | 48.75% | P3V3/PCIE_UP0_N |
| 575 | clearance | hs | 中-U3U7/上 | 0.0866/0.1750 | 49.49% | PCIE_UP_OUT0_N_U7/PCIE_UP_OUT0_P_U7 |
| 576 | clearance | hs | 中-U3U7/上 | 0.0866/0.1750 | 49.49% | PCIE_UP_OUT0_N_U7/PCIE_UP_OUT0_P_U7 |
| 585 | clearance | hs | 中-U3U7/上 | 0.0866/0.1750 | 49.49% | PCIE_UP_OUT0_N_U7/PCIE_UP_OUT0_P_U7 |
| 586 | clearance | hs | 中-U3U7/上 | 0.0866/0.1750 | 49.49% | PCIE_UP_OUT0_N_U7/PCIE_UP_OUT0_P_U7 |
| 587 | clearance | hs | 中-U3U7/上 | 0.0866/0.1750 | 49.49% | PCIE_UP_OUT0_N_U7/PCIE_UP_OUT0_P_U7 |
| 588 | clearance | hs | 中-U3U7/上 | 0.0866/0.1750 | 49.49% | PCIE_UP_OUT0_N_U7/PCIE_UP_OUT0_P_U7 |
| 591 | clearance | hs | 中-U3U7/上 | 0.0866/0.1750 | 49.49% | PCIE_UP_OUT0_N_U7/PCIE_UP_OUT0_P_U7 |
| 791 | hole_clearance | pwr+ls | 左-MCIO/上 | 0.0000/0.2500 | 0.00% | MCU_VDD/SWCLK_BOOT0 |
| 800 | hole_clearance | ls | 中-U3U7/下 | 0.0000/0.2500 | 0.00% | STRAP_EQ1_1_U3/STRAP_MODE_U3 |

## 5. 规则→根因映射证据

| 规则类型 | 规则库声明键 | 根因族 | M11 证据 |
|---|---|---|---|
| tracks_crossing | tracks_crossing | seg_crossing | 两铜段中心线几何相交（连通性触发报告，对齐报告 §3.3） |
| clearance | clearance | pad_clearance | 焊盘 vs 异网元素铜净距不足 |
| shorting_items | clearance | seg_seg_edge0_short | 段-段铜边缘接触短路 edge==0（M11 修复：kicad DRCE_SHORTING_ITEMS 判定 actual==0） |
| hole_clearance | hole_clearance | via_hole | 过孔钻孔 vs 异网铜元素净距不足 |
| clearance | clearance | via_clearance | 过孔 vs 异网元素铜净距不足 |
| clearance | clearance | seg_clearance | 走线段 vs 异网元素铜净距不足 |
| clearance | clearance | via_via_layer_dup | via-via 对按铜层重复报告（贯穿过孔 8 层 → 同一物理违规多行，对齐报告 §3.2） |
| shorting_items | clearance | via_short | 过孔铜 vs 异网元素接触短路 |
| shorting_items | clearance | pad_short | 焊盘 vs 异网元素接触短路 |
| hole_clearance | hole_clearance | via_via_hole | 过孔互距不足 0.25（钻孔-钻孔边缘净距，171 系统性） |
| zones_intersect | zone | zone_multi_poly_overlap | 同网 zone 多多边形重叠（M11 修复 Zone.polys 全量收集，kicad 要求不同优先级） |
| solder_mask_bridge | solder_mask | smd_mask_bridge | SMD 异网开窗边缘净距 < 0.05（阻焊桥） |
| solder_mask_bridge | solder_mask | tht_mask_wildcard | THT pad 开窗通配符 '*.Mask'（M11 修复 _pad_has_mask 展开，如 J9） |
| diff_pair_gap_out_of_range | diff_pair | diff_pair_intra_gap | 差分对内 P/N 间距 < min gap = board rules.min_clearance 0.1（M11 修复：非 netclass diff_pai |
