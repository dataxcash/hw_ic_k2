# K2 · P5 执行包可用性核对（2026-09-21 · 监理自动续推轮）

**性质**：只读核对（当前阶段 P6 推进；**P5 = 唯一未闭阶段门**）。不动交付包、不改真源/判据/生成器、未新增判据维、未派 WORKER。

## A. 四件一致性（计划 ↔ 规程 ↔ 检查表 ↔ 回填模板）
- 计划 §2 的 **V4 / V5 / V6-1..5 / V7 = 8 项** ↔ 模板 8 项一一对应（`V4_impedance_coupon · V5_pdn_dc_drop · V6_1_rail_voltages · V6_2_mcu_swd_id · V6_3_fru_i2c · V6_4_link_gen4_x4 · V6_5_stability_30min_aer · V7_thermal_o2`）
- 阈值逐项落字于模板 `criterion`：**85Ω±10%**（76.5–93.5）· PDN **≤3%** · 轨电压 **±5%** · 二值项 4 条（SWD device ID / FRU EEPROM / x4 Gen4 训练 / AER=0）· 热 **Tj ≤120.0℃** 且 **T1 触发 >117.0℃**
- 计划 §3 具名观察 4 条：2 条入 `observations_p5_named`（阻焊坝 9 处 · 丝印越框 4 处）、1 条纳入 V4 判据（F.Cu 0.2825mm）、1 条标注无需动作（B.Cu 无 as-built run）⇒ **无漏项**

## B. 测点指向核验（板直读，**11/11 通过**）
ENG 以 pcbnew-free 解析器直读受审板 `l7`（58 footprint / pad→net）核对规程与检查表所引每一点：

| 检查 | 实测 | 判 |
|---|---|---|
| `J13` pad1..4 | SWDIO / SWCLK_BOOT0 / GND / MCU_VDD | ✅ |
| `NRST` 测点 `U1.pad10` / `R29.pad1` / `C73.pad1` | 三者网名均 = NRST | ✅（规程「NRST **不在 J13**」的纠正性说明正确） |
| V6-4 端口 `J2`/`J3`/`J4` | 存在 · PCIE 网 36 / 18 / 18 条 | ✅ |
| 中继 `U6` | 存在 · 354 pad · 77 网 | ✅ |
| 四轨网（12V_IN/P3V3/P3V3_AUX/MCU_VDD 等） | `INSTRUMENT_SELFCHECK.json` `all_nets_present=True` | ✅ |
| 模板 8 项 × (criterion+evidence+status) | 8/8 齐 | ✅ |
| 责任边界 | `measured_by=<实测方>` · `judged_by=监理` | ✅ |
| 交付锚一致性 | `6ee7495de61f749f…` / `0e88e107e2da8192…`（= 现行包） | ✅ |

## C. 具名发现（**2 项**）
| # | 级别 | 发现 | 处置选项 |
|---|---|---|---|
| **P5-1** | **中**（P5 输入风险） | **V4 阻抗券未在随单件中索取**：`ORDER_NOTES.md` 只写「下单勾选阻抗控制」，索取动作写在**到货后**的 `RULES.md §V4`。若板厂默认不出券 ⇒ V4 无输入（只能记 INCONCLUSIVE） | (a) `ORDER_NOTES §1` 补一行索取 ⇒ **触交付锚** ⇒ 需监理授权重出包；(b) **不动包**，由商务下单页备注索取 ⇒ 需监理在册面确认口径。**两案均属交付口径 = 监理自裁项**，ENG 不擅自改包 |
| P5-2 | 装饰级 | `DISCLOSURE.md §5b` 条目编号乱序（1·2·3·**5**·**4**） | 随 (a) 修正；或不动包、册面记录 |

## D. 结论
**P5 执行包可用**：验收项/阈值/证据位/触发条款齐备，四件同口径，**全部测点指向在受审板上实证存在且网名相符**。唯一输入风险 = **P5-1（阻抗券索取渠道）**，处置不动真源几何。
阶段门态不变：P0–P4 与 P6 判据面 PASS；**P5 仍为唯一未闭阶段门（外部实测 V4–V7 NOT_RUN）**；**未越阶段**。

## E. 交件
`P5_EXECUTION_PACK_READINESS_AUDIT_20260921_v1.json`（`a8da226a5d96f3b9`）
