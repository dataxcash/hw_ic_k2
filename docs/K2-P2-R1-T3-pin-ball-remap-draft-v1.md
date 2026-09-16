# T3 · `U3/U7`（原理图）↔ `U6`（真源单颗）脚↔球 重映**草表**（ENG 草案，待监理批；**未落地**）

- 生成：`/tmp/opencode/k2p1/r1_pinball_remap_table.draft.py`（断言全过：输入 32 / 输出 32）

## ① 输入侧重映（32：`U3/U7` RX 脚 → `U6` `A/B_PER*` 球）

| 网 | 图侧器件 | 图侧 pin(pinfunction) | U6 球 |
|---|---|---|---|
| `PCIE_DN0_P` | `U3` | `1` (RX0P_1) | `A_PERP0` |
| `PCIE_UP0_P` | `U7` | `1` (RX0P_1) | `B_PERP0` |
| `PCIE_DN0_N` | `U3` | `2` (RX0N_2) | `A_PERN0` |
| `PCIE_UP0_N` | `U7` | `2` (RX0N_2) | `B_PERN0` |
| `PCIE_DN1_P` | `U3` | `4` (RX1P_4) | `A_PERP1` |
| `PCIE_UP1_P` | `U7` | `4` (RX1P_4) | `B_PERP1` |
| `PCIE_DN1_N` | `U3` | `5` (RX1N_5) | `A_PERN1` |
| `PCIE_UP1_N` | `U7` | `5` (RX1N_5) | `B_PERN1` |
| `PCIE_DN2_P` | `U3` | `7` (RX2P_7) | `A_PERP2` |
| `PCIE_UP2_P` | `U7` | `7` (RX2P_7) | `B_PERP2` |
| `PCIE_DN2_N` | `U3` | `8` (RX2N_8) | `A_PERN2` |
| `PCIE_UP2_N` | `U7` | `8` (RX2N_8) | `B_PERN2` |
| `PCIE_DN3_P` | `U3` | `10` (RX3P_10) | `A_PERP3` |
| `PCIE_UP3_P` | `U7` | `10` (RX3P_10) | `B_PERP3` |
| `PCIE_DN3_N` | `U3` | `11` (RX3N_11) | `A_PERN3` |
| `PCIE_UP3_N` | `U7` | `11` (RX3N_11) | `B_PERN3` |
| `PCIE_DN4_P` | `U3` | `13` (RX4P_13) | `A_PERP4` |
| `PCIE_UP4_P` | `U7` | `13` (RX4P_13) | `B_PERP4` |
| `PCIE_DN4_N` | `U3` | `14` (RX4N_14) | `A_PERN4` |
| `PCIE_UP4_N` | `U7` | `14` (RX4N_14) | `B_PERN4` |
| `PCIE_DN5_P` | `U3` | `16` (RX5P_16) | `A_PERP5` |
| `PCIE_UP5_P` | `U7` | `16` (RX5P_16) | `B_PERP5` |
| `PCIE_DN5_N` | `U3` | `17` (RX5N_17) | `A_PERN5` |
| `PCIE_UP5_N` | `U7` | `17` (RX5N_17) | `B_PERN5` |
| `PCIE_DN6_P` | `U3` | `19` (RX6P_19) | `A_PERP6` |
| `PCIE_UP6_P` | `U7` | `19` (RX6P_19) | `B_PERP6` |
| `PCIE_DN6_N` | `U3` | `20` (RX6N_20) | `A_PERN6` |
| `PCIE_UP6_N` | `U7` | `20` (RX6N_20) | `B_PERN6` |
| `PCIE_DN7_P` | `U3` | `22` (RX7P_22) | `A_PERP7` |
| `PCIE_UP7_P` | `U7` | `22` (RX7P_22) | `B_PERP7` |
| `PCIE_DN7_N` | `U3` | `23` (RX7N_23) | `A_PERN7` |
| `PCIE_UP7_N` | `U7` | `23` (RX7N_23) | `B_PERN7` |

## ② 输出侧重映（32：退役网 `*_U3`/`*_U7` 的 TX 脚 → 并网后 `U6` `A/B_PET*` 球）

| 退役网 | 图侧 | pin(pinfunction) | 并入保留网 | U6 球 |
|---|---|---|---|---|
| `PCIE_DN_OUT0_P_U3` | `U3` | `55` (TX0P_55) | `PCIE_DN_OUT0_P_MCIO` | `A_PETP0` |
| `PCIE_UP_OUT0_P_U7` | `U7` | `55` (TX0P_55) | `PCIE_UP_OUT0_P_J2` | `B_PETP0` |
| `PCIE_DN_OUT0_N_U3` | `U3` | `54` (TX0N_54) | `PCIE_DN_OUT0_N_MCIO` | `A_PETN0` |
| `PCIE_UP_OUT0_N_U7` | `U7` | `54` (TX0N_54) | `PCIE_UP_OUT0_N_J2` | `B_PETN0` |
| `PCIE_DN_OUT1_P_U3` | `U3` | `52` (TX1P_52) | `PCIE_DN_OUT1_P_MCIO` | `A_PETP1` |
| `PCIE_UP_OUT1_P_U7` | `U7` | `52` (TX1P_52) | `PCIE_UP_OUT1_P_J2` | `B_PETP1` |
| `PCIE_DN_OUT1_N_U3` | `U3` | `51` (TX1N_51) | `PCIE_DN_OUT1_N_MCIO` | `A_PETN1` |
| `PCIE_UP_OUT1_N_U7` | `U7` | `51` (TX1N_51) | `PCIE_UP_OUT1_N_J2` | `B_PETN1` |
| `PCIE_DN_OUT2_P_U3` | `U3` | `49` (TX2P_49) | `PCIE_DN_OUT2_P_MCIO` | `A_PETP2` |
| `PCIE_UP_OUT2_P_U7` | `U7` | `49` (TX2P_49) | `PCIE_UP_OUT2_P_J2` | `B_PETP2` |
| `PCIE_DN_OUT2_N_U3` | `U3` | `48` (TX2N_48) | `PCIE_DN_OUT2_N_MCIO` | `A_PETN2` |
| `PCIE_UP_OUT2_N_U7` | `U7` | `48` (TX2N_48) | `PCIE_UP_OUT2_N_J2` | `B_PETN2` |
| `PCIE_DN_OUT3_P_U3` | `U3` | `46` (TX3P_46) | `PCIE_DN_OUT3_P_MCIO` | `A_PETP3` |
| `PCIE_UP_OUT3_P_U7` | `U7` | `46` (TX3P_46) | `PCIE_UP_OUT3_P_J2` | `B_PETP3` |
| `PCIE_DN_OUT3_N_U3` | `U3` | `45` (TX3N_45) | `PCIE_DN_OUT3_N_MCIO` | `A_PETN3` |
| `PCIE_UP_OUT3_N_U7` | `U7` | `45` (TX3N_45) | `PCIE_UP_OUT3_N_J2` | `B_PETN3` |
| `PCIE_DN_OUT4_P_U3` | `U3` | `43` (TX4P_43) | `PCIE_DN_OUT4_P_MCIO` | `A_PETP4` |
| `PCIE_UP_OUT4_P_U7` | `U7` | `43` (TX4P_43) | `PCIE_UP_OUT4_P_J2` | `B_PETP4` |
| `PCIE_DN_OUT4_N_U3` | `U3` | `42` (TX4N_42) | `PCIE_DN_OUT4_N_MCIO` | `A_PETN4` |
| `PCIE_UP_OUT4_N_U7` | `U7` | `42` (TX4N_42) | `PCIE_UP_OUT4_N_J2` | `B_PETN4` |
| `PCIE_DN_OUT5_P_U3` | `U3` | `40` (TX5P_40) | `PCIE_DN_OUT5_P_MCIO` | `A_PETP5` |
| `PCIE_UP_OUT5_P_U7` | `U7` | `40` (TX5P_40) | `PCIE_UP_OUT5_P_J2` | `B_PETP5` |
| `PCIE_DN_OUT5_N_U3` | `U3` | `39` (TX5N_39) | `PCIE_DN_OUT5_N_MCIO` | `A_PETN5` |
| `PCIE_UP_OUT5_N_U7` | `U7` | `39` (TX5N_39) | `PCIE_UP_OUT5_N_J2` | `B_PETN5` |
| `PCIE_DN_OUT6_P_U3` | `U3` | `37` (TX6P_37) | `PCIE_DN_OUT6_P_MCIO` | `A_PETP6` |
| `PCIE_UP_OUT6_P_U7` | `U7` | `37` (TX6P_37) | `PCIE_UP_OUT6_P_J2` | `B_PETP6` |
| `PCIE_DN_OUT6_N_U3` | `U3` | `36` (TX6N_36) | `PCIE_DN_OUT6_N_MCIO` | `A_PETN6` |
| `PCIE_UP_OUT6_N_U7` | `U7` | `36` (TX6N_36) | `PCIE_UP_OUT6_N_J2` | `B_PETN6` |
| `PCIE_DN_OUT7_P_U3` | `U3` | `34` (TX7P_34) | `PCIE_DN_OUT7_P_MCIO` | `A_PETP7` |
| `PCIE_UP_OUT7_P_U7` | `U7` | `34` (TX7P_34) | `PCIE_UP_OUT7_P_J2` | `B_PETP7` |
| `PCIE_DN_OUT7_N_U3` | `U3` | `33` (TX7N_33) | `PCIE_DN_OUT7_N_MCIO` | `A_PETN7` |
| `PCIE_UP_OUT7_N_U7` | `U7` | `33` (TX7N_33) | `PCIE_UP_OUT7_N_J2` | `B_PETN7` |

## ③ 全域网（无逐脚映射；球集合直接对齐）

- `GND`：图侧 `U3/U7` → U6 球 **154 个**（全 GND/全 P3V3 域）
- `P3V3`：图侧 `U3/U7` → U6 球 **32 个**（全 GND/全 P3V3 域）

## ④ 新增（43 网，随补入 12 件落地）

- `DS320_STRAP_A_ADDR0_15-8` → `U6/A_ADDR0_15-8`
- `DS320_STRAP_A_ADDR0_7-0` → `U6/A_ADDR0_7-0`
- `DS320_STRAP_A_ADDR1_15-8` → `U6/A_ADDR1_15-8`
- `DS320_STRAP_A_ADDR1_7-0` → `U6/A_ADDR1_7-0`
- `DS320_STRAP_B_ADDR0_15-8` → `U6/B_ADDR0_15-8`
- `DS320_STRAP_B_ADDR0_7-0` → `U6/B_ADDR0_7-0`
- `DS320_STRAP_B_ADDR1_15-8` → `U6/B_ADDR1_15-8`
- `DS320_STRAP_B_ADDR1_7-0` → `U6/B_ADDR1_7-0`
- `DS320_STRAP_MODE` → `U6/MODE`
- `I2C2_SCL` → `U6/SCL`
- `I2C2_SDA` → `U6/SDA`
- `PCIE_DN_OUT0_N_MCIO` → `U6/A_PETN0`
- `PCIE_DN_OUT0_P_MCIO` → `U6/A_PETP0`
- `PCIE_DN_OUT1_N_MCIO` → `U6/A_PETN1`
- `PCIE_DN_OUT1_P_MCIO` → `U6/A_PETP1`
- `PCIE_DN_OUT2_N_MCIO` → `U6/A_PETN2`
- `PCIE_DN_OUT2_P_MCIO` → `U6/A_PETP2`
- `PCIE_DN_OUT3_N_MCIO` → `U6/A_PETN3`
- `PCIE_DN_OUT3_P_MCIO` → `U6/A_PETP3`
- `PCIE_DN_OUT4_N_MCIO` → `U6/A_PETN4`
- `PCIE_DN_OUT4_P_MCIO` → `U6/A_PETP4`
- `PCIE_DN_OUT5_N_MCIO` → `U6/A_PETN5`
- `PCIE_DN_OUT5_P_MCIO` → `U6/A_PETP5`
- `PCIE_DN_OUT6_N_MCIO` → `U6/A_PETN6`
- `PCIE_DN_OUT6_P_MCIO` → `U6/A_PETP6`
- `PCIE_DN_OUT7_N_MCIO` → `U6/A_PETN7`
- `PCIE_DN_OUT7_P_MCIO` → `U6/A_PETP7`
- `PCIE_UP_OUT0_N_J2` → `U6/B_PETN0`
- `PCIE_UP_OUT0_P_J2` → `U6/B_PETP0`
- `PCIE_UP_OUT1_N_J2` → `U6/B_PETN1`
- `PCIE_UP_OUT1_P_J2` → `U6/B_PETP1`
- `PCIE_UP_OUT2_N_J2` → `U6/B_PETN2`
- `PCIE_UP_OUT2_P_J2` → `U6/B_PETP2`
- `PCIE_UP_OUT3_N_J2` → `U6/B_PETN3`
- `PCIE_UP_OUT3_P_J2` → `U6/B_PETP3`
- `PCIE_UP_OUT4_N_J2` → `U6/B_PETN4`
- `PCIE_UP_OUT4_P_J2` → `U6/B_PETP4`
- `PCIE_UP_OUT5_N_J2` → `U6/B_PETN5`
- `PCIE_UP_OUT5_P_J2` → `U6/B_PETP5`
- `PCIE_UP_OUT6_N_J2` → `U6/B_PETN6`
- `PCIE_UP_OUT6_P_J2` → `U6/B_PETP6`
- `PCIE_UP_OUT7_N_J2` → `U6/B_PETN7`
- `PCIE_UP_OUT7_P_J2` → `U6/B_PETP7`

## ⑤ 退役（22 网，随 C/D 类删除）

```
ALL_DONE_N_U3, ALL_DONE_N_U7, PD0_U3, PD0_U7, PD1_U3, PD1_U7, STRAP_EQ0_1_U3, STRAP_EQ0_1_U7, STRAP_EQ0_U3, STRAP_EQ0_U7, STRAP_EQ1_1_U3, STRAP_EQ1_1_U7, STRAP_EQ1_U3, STRAP_EQ1_U7, STRAP_MODE_U3, STRAP_MODE_U7, STRAP_READ_EN_U3, STRAP_READ_EN_U7, VREG1_U3, VREG1_U7, VREG2_U3, VREG2_U7
```
