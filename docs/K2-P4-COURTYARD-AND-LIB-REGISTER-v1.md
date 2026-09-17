# K2 · P4 · ⑥ courtyard 40 / ⑦ lib 35 **逐条列名登记** · v1 · 2026-09-17

> 依据监理 **#K2-21 §二⑥⑦** 与 **§六-5**。对象 = 已落件五步复合板 **`6ff49da5678c2108`**（`k2/hw/k2_v4_8L.l5.kicad_pcb`）。
> 仪器：`kicad-cli 10.0.5` DRC（severity 全开，报告 `/tmp/opencode/pro-check/drc.json`）· W-8 电气级审计器 `k2_w8_footprint_audit_v1.py`（sha `75404d706413d546`）。
> 本件为**登记与结论**，不含豁免裁定；**未改板/库/判据**。

## 1. ⑥ `missing_courtyard` 40 件 —— 逐条列名 + 处置结论

处置结论（40 件同构，逐条适用）：**库与板均未定义 `CrtYd`**；监理已实测「补则必生 `courtyards_overlap` error（margin 0 即 3 对；`J9↔U1` 需 1.55mm 分离）」⇒ 与 **J-1「error = 0」硬冲突**。
故本条**不整维豁免**（= 判据自废）、**不以「接受 overlap error」收口**、**不以接近 0 宣称归零**；登记为 **J-7 图形级已知缺口 + L2 placement 项**（见 §2）。

| # | ref | 面 | 处置 |
|---|---|---|---|
| 1 | `C73` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 2 | `C74` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 3 | `C75` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 4 | `C76` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 5 | `C77` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 6 | `C78` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 7 | `C79` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 8 | `C80` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 9 | `C81` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 10 | `C82` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 11 | `C83` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 12 | `C84` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 13 | `C85` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 14 | `C86` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 15 | `C87` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 16 | `C88` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 17 | `C89` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 18 | `C90` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 19 | `D1` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 20 | `E2` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 21 | `J11` | B | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 22 | `J12` | B | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 23 | `J13` | B | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 24 | `J2` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 25 | `J3` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 26 | `J4` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 27 | `J6` | B | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 28 | `J9` | B | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 29 | `R1` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 30 | `R21` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 31 | `R28` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 32 | `R29` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 33 | `R3` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 34 | `R31` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 35 | `R32` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 36 | `R33` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 37 | `R34` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 38 | `U2` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 39 | `U4` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |
| 40 | `U5` | F | 未定义 CrtYd；登记 J-7 图形级缺口 + L2 项 |

**合计 40 件**（与监理 #K2-21 §〇③ 清单逐条一致：C73–C90 18 · J2/J3/J4/J6/J9/J11/J12/J13 8 · R1/R3/R21/R28/R29/R31–R34 9 · U2/U4/U5 3 · D1/E2 2）。

## 2. ⑥ 碰撞对 + L2 最小集微调方案（含守恒闸）

| 碰撞对 | 本体重叠（实测，margin 0） | 所需分离 | 建议动件 | 该件可用域（实测） | 可行性 |
|---|---|---|---|---|---|
| `U4↔D2` | 2.500 × 0.675 mm | ≈0.7–0.9 | `D2`（2 pad 2 网） | 见下注 | 可行 |
| `D2↔U2` | 0.120 × 1.730 mm | ≈0.6–0.8 | `D2`（同上，一并解） | 见下注 | 可行 |
| `J9↔U1` | 1.675 × 1.500 mm | **1.55** | `J9`（4 pad 4 网；列内 y 向平移，**`column_x=27.94` 不动**） | **y 松弛 7.92mm**（J13 上限 47.29 → J9 下限 55.21） | **可行（余量 4.8×）** |
| `L1↔U2` | 3.550 × 0.030 mm（margin 0；margin 0.05 时为 0.055） | ≈0.2–0.3 | `L1`（2 pad） | 小位移即可 | 可行 |

**`J9↔U1` 特别条款判定（监理要求）**：所需分离 1.55mm **只能沿 y** 取得（`J9` 在冻结排针列 `x=27.94`）；
可用 y 域 = 相邻 `J13` 本体现大边 `y=47.29` 到 `J9` 本体现小边 `y=55.21` ⇒ **7.92mm**，扣双件 courtyard 余量 0.50mm ⇒ **可用 7.42mm > 所需 1.55mm**（余量 4.8×）。
⇒ **非几何不可分**：无需升级 owner，按 L2 placement 项执行（移 `J9` + 重接其 4 网 + 逐项守恒复算）。

**守恒闸（每件移动后逐项复算，任一不达即回报）**：出框 P3-4（接口焊盘不出框，内缩 0.3mm）· 排针列 `column_x=27.94` 不变 · 走廊口径（P3-5/C5b）· 等长（高速对）· `85Ω ±10%` · 非 45° = 0 · 未连接 = 0 · `courtyards_overlap` = 0。

## 3. ⑦ `lib_footprint_mismatch` 35 件 —— 逐条列名 + 处置结论

口径（维持 #K2-19 §二 W-8 / #K2-21 §二⑦）：**以板为准**；**电气级必须 0**（pad 数/名/尺寸/旋转/位置）· 图形/属性级容忍 · 35 件逐条登记 · `fp-lib-table` 已建（F-12 收口）。
实测（W-8 电气级审计器，59 件）：**电气级一致 2**（U4/U5）· 电气级差异 **31** · 仅 pad 名集合差异 2 · 无库链接 24。
⇒ 被判 DRC 的 35 件中，**33 件为 pad 级差异**（非图形/属性级）⇒ **J-7「电气级 = 0」当前未达成**。

| # | ref | lib_id | W-8 判决 | 差异类/字段 | 处置结论 |
|---|---|---|---|---|---|
| 1 | `C73` | `Capacitor_SMD:C_0402_1005Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 2 | `C74` | `Capacitor_SMD:C_0402_1005Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 3 | `C75` | `Capacitor_SMD:C_0402_1005Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 4 | `C76` | `Capacitor_SMD:C_0402_1005Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 5 | `C77` | `Capacitor_SMD:C_0402_1005Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 6 | `C78` | `Capacitor_SMD:C_0603_1608Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 7 | `C79` | `Capacitor_SMD:C_0402_1005Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 8 | `C80` | `Capacitor_SMD:C_0402_1005Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 9 | `C81` | `Capacitor_SMD:C_0402_1005Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 10 | `C82` | `Capacitor_SMD:C_0402_1005Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 11 | `C83` | `Capacitor_SMD:C_0603_1608Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 12 | `C84` | `Capacitor_SMD:C_0805_2012Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 13 | `C85` | `Capacitor_SMD:C_0402_1005Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 14 | `C86` | `Capacitor_SMD:C_0603_1608Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 15 | `C87` | `Capacitor_SMD:C_0402_1005Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 16 | `C88` | `Capacitor_SMD:C_0603_1608Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 17 | `C89` | `Capacitor_SMD:C_0603_1608Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 18 | `C90` | `Capacitor_SMD:C_0402_1005Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 19 | `D1` | `LED_SMD:LED_0603_1608Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 20 | `E2` | `ForgeOS:SOIC8_FRU` | electrical_diff | pad / dy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 21 | `J2` | `ForgeOS:SlimSAS_x8_SFF-8654_74pin_RASide` | electrical_diff | pad / dx,dy,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 22 | `J3` | `ForgeOS:MCIO_4i_SFF-1016_RASide` | pad_name_set_only | pad_name_set / - | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 23 | `J4` | `ForgeOS:MCIO_4i_SFF-1016_RASide` | pad_name_set_only | pad_name_set / - | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 24 | `R1` | `Resistor_SMD:R_0603_1608Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 25 | `R21` | `Resistor_SMD:R_0603_1608Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 26 | `R28` | `Resistor_SMD:R_0603_1608Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 27 | `R29` | `Resistor_SMD:R_0603_1608Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 28 | `R3` | `Resistor_SMD:R_0603_1608Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 29 | `R31` | `Resistor_SMD:R_0603_1608Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 30 | `R32` | `Resistor_SMD:R_0603_1608Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 31 | `R33` | `Resistor_SMD:R_0603_1608Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 32 | `R34` | `Resistor_SMD:R_0603_1608Metric` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 33 | `U2` | `Package_SO:SOIC-8_5.3x5.3mm_P1.27mm` | electrical_diff | pad / dx,shape,sx,sy | 以板为准（板为权威 land）；**库侧待按板重建并让 board `lib_id` 指向项目库**后才能判「电气级 = 0」⇒ 登记为 J-7 缺口，不阻塞铜/几何收敛 |
| 34 | `U4` | `ForgeOS:SOT23_BAT54C` | electrical_identical | - / - | 以板为准：电气级一致，无需动作 |
| 35 | `U5` | `ForgeOS:OPTO_LTV356T` | electrical_identical | - / - | 以板为准：电气级一致，无需动作 |

**合计 35 件**。

## 4. 结论与下一步（ENG）

1. ⑥ 40 件：**登记**（J-7 图形级缺口 + L2 项）；**不豁免**。L2 最小集 = 动 `D2`（解 `U4↔D2` 与 `D2↔U2`）+ 动 `L1`（解 `L1↔U2`）+ 移 `J9` 于列内 y 向 1.6–2.0mm（解 `J9↔U1`，**不越 `column_x`**）；四对解后 40 件补 `CrtYd` 可望 `missing_courtyard=0` **且** `courtyards_overlap=0`。
2. ⑦ 35 件：**登记**（J-1 warning 处置结论 = 以板为准 + 库侧重建路线）。
3. 待监理裁定/授权项：**库侧「按板重建 + 重指 `lib_id`」**是否由 ENG 执行（涉及板侧 `lib_id` 属性改动 ⇒ 需走 SPEC 版本 bump + 落件批准）；⑥ 的 L2 执行亦需批准后落件（届时板 sha 变更、需新 SPEC rev）。
4. 本件未改任何文件（板/库/SPEC/判据/生成器均未动）。
