# K2 · P5 首件实测 **投递说明（单一入口）** · **l8 版**（2026-09-21）

> **用途**：外部实测方执行 P5（打样首件 bring-up）时，本件为**唯一入口索引**：受审对象、随单件锚、逐项规程、回件格式、边界与责任人。
> **性质**：ENG 侧文档（**未改交付包** · 交付锚 `4b610baed4f4752c` 未动）。

## 1. 受审对象（实测对象 = 唯一）
| 项 | 值 |
|---|---|
| 板 | `k2/hw/k2_v4_8L.l8.kicad_pcb`（revision **l8**） |
| 板 sha16 | **`7a5c89913d6e5d0a`** |
| 层数/工艺 | 8 铜层 · JLC HDI（盲埋孔 · 阶数≥2） |

## 2. 随单件（**冻结 · 只读 · 本件不重建**）
| 项 | 路径 | 锚 |
|---|---|---|
| 交付包 MANIFEST | `k2/pm_gate/artifacts/k2_v4/L6/jlc_package_l8/MANIFEST.json` | `4b610baed4f4752c` |
| 打包件 | `k2/pm_gate/artifacts/k2_v4/L6/DELIVERY_l8/k2_v4_8L.l8_gerber_package.tar.gz` | `36a6b276b4f7e465` |
| 完整性 | `sha256sum -c DELIVERY/SHA256SUMS.txt`（自 `L6/` 运行） | **55/55 OK** |
| DFM | `pass 16 / accept 1（阻焊坝 · 已 L2 裁 ACCEPT_WITH_FAB_REVIEW + 有确定性修法证明）/ fail 0` | 见 `06_rulings/mask_accept_fix_proof.json` |

> **随单件 ≠ 可用性证明**：可用性只能由 P5 实测（V4–V7）证明。

## 3. 逐项规程与回件（**权威件**）
| 件 | 路径 | sha16 |
|---|---|---|
| 逐项操作规程（V4·V5·V6-1..5·V7 + 通用要求 + 回件格式） | `k2/pm_gate/artifacts/k2_v4/L6/first_article_l8/RULES.md` | `42013771b1358954` |
| 现场检查表 | `k2/pm_gate/artifacts/k2_v4/L6/first_article_l8/CHECKLIST.md` | `b97ac43fc0f99c31` |
| 回填模板（8 项 · criterion/measured/evidence/status） | `k2/pm_gate/artifacts/k2_v4/L6/first_article_l8/results_template.json` | `d125c5eac50c933f` |
| 测点自查（pcbnew 直读 · 11/11 通过） | `k2/pm_gate/artifacts/k2_v4/L6/first_article_l8/INSTRUMENT_SELFCHECK.json` | `432125b50d6f5590` |
| 验收计划（阈值来源） | `k2/docs/K2-P5-FIRST-ARTICLE-ACCEPTANCE-PLAN-v1.md` | `b002ec9829a53f12` |

**8 项与阈值**：V4 阻抗券 **85.0Ω ±10%**（须覆盖 0.6mm 中心几何 + 最紧 0.2825mm `PCIE_UP3`）· V5 PDN 压降 **≤3%** · V6-1 各轨 **±5%** · V6-2 SWD device ID（二值）· V6-3 FRU I2C 地址应答（二值）· V6-4 **双路 x4 Gen4 训练成功**（二值 + LTSSM 终态）· V6-5 **30min AER = 0** · V7 热 **Tj ≤ 120.0℃**（四工况；`Tj(U6) > 117.0℃` 或未按 O2 实施 ⇒ **T1 触发**开新 rev，目标 `θJA_eff ≤ 9.5℃/W`）。

## 4. 回件与判定
- 回件 = 回填后的 `results_template.json`（`status ∈ {NOT_RUN, PASS, FAIL, INCONCLUSIVE}` + `measured` + `evidence[]`，每项附**原始件 + sha256**；二值项禁「基本正常」类表述）。
- 责任：**实测方**填写（`measured_by`）· **监理**判定（`judged_by`）· **ENG 不得自证**。

## 5. 商务面（**非 ENG 任务** · owner #14④）
- 阻抗券（V4）**索取动作在下单页**注明（#K2-48 N-1 (a)：接受 + 随单注明，**不动交付锚**）

> **本件为 l8 版**：与 `…-TRANSMITTAL-v1.md`（l7 版，**保留不删**）并列；l8 = `#K2-57` 新 rev（CR-26/CR-27 修复载体），其**几何与 l7 相同**，仅 `U4/2,3` 与 `D1/1,2` 之 pad→net 不同 ⇒ **8 项验收阈值与测点均不变**。。

## 6. 已知具名观察（**不新增判据** · 见 RULES §已知具名项）
- 阻焊坝 9 处（`U1` pad23/24 · `U6` FG1 · `J13` pad1/2 等）：焊接后桥连检查；若证实桥连 ⇒ **T1 触发**（修法 `pad_to_mask_clearance=0.02mm`，须**另开 rev**）。
- 正面丝印 4 处越框（`H4`/`R41`/`D2`/`C87`）：确认位号可读性（预期缺损 · 非缺陷）。

## 7. 红线
ENG 不参与自证 · 禁改冻结随单件/重建包 · 禁为变绿改阈值（C-12）· 结果未经监理判定不得宣称 P5 通过。

## 8. V5 具名关注点（**设计侧预判 · 非证据 · 不新增判据**）
- 几何核算（`PDN_DESIGN_PRECHECK_V5_20260921_v1.json` · 100bc34f2980d86d）显示：**P3V3_AUX 平面仅为小岛**（38.7+42.5 mm²），该轨以迹线分配，最坏单跳 **In5 20.789mm / 0.2mm / 0.5oz ⇒ 125.3 mΩ@85℃**（相当于 0.79A 即用尽 3% 预算）。
- **建议**：V5 实测请**明确覆盖 `J3`/`J4`（PCIe 槽）端的 `P3V3_AUX`**，并记录该端**源→负载**压降（其余轨按计划常规测）。
- **边界**：该预判**不是** V5 判据、**不是** P5 结论；`V5` 维持 `NOT_RUN`，**判定归监理**。
- **【CR-48 · l8 基准补充】**：`MCU_VDD` 之迹线几何在 l8 **显著变化**（`U4` pad 交换致该网重布：seg **63→168** · L **33.11→54.10mm** · via **12→15** ⇒ 迹线电阻 **130.65→236.57 mΩ · +81%**）；`P3V3_AUX` 与 `12V_IN` **逐项不变**（故上条 `P3V3_AUX` 125.3 mΩ 读数**仍有效**）。⇒ **建议 V5 实测一并覆盖 `MCU_VDD` 之源→负载**（`In4` 大平面可分担，真实压降应仍远低于迹线数；本条为设计侧预判，`PDN_DESIGN_PRECHECK_V5` 原件系 l7 基准，l8 复算见 `P6_execution/P6_OPEN_READINESS/P5_PDN_PRECHECK_REVBASIS_L8_20260921_v1.json`）。若实测超限 ⇒ 确定性修法为加宽该跳/补岛 stitching（**改板 = 须 ECO + 监理授权，不在 P5 范围内**）。

## 9. 预期值（V6-2 / V6-3）—— 设计侧推导（**非实测**）
- **V6-3 FRU EEPROM**：`E2`（AT24C02 类 · SOIC8）在 **I2C1**；strapping `A0=GND` · `A1=MCU_VDD` · `A2=GND` ⇒ **7-bit 地址 `0x52`**（8-bit 写 `0xA4` / 读 `0xA5`）；`WP=GND`。板侧（l8 `7a5c89913d6e5d0a` 的 E2 pad1/2/3/5/6/7 网名）与**原理图侧**（`k2_sch.yaml`：`E2/A0,A2,WP`⊂GND · `E2/A1,VCC`⊂MCU_VDD · `E2/SDA,SCL`⊂I2C1）**双侧一致**。
- **V6-2 MCU SWD**：`U1 = STM32G0B1KBU6`；记录 **(a) SW-DP IDCODE**（预期 **`0x0BC11477`** · Cortex-M0+ CoreSight 标准）与 **(b) DBGMCU_IDCODE @ `0x40015800`**（DEV_ID/REV_ID）。**DEV_ID 的规范值须以 ST `RM0454 §DBG` 对照**（本环境 `st.com` = HTTP 567 ⇒ 离线不可得，**登记为手册依赖项**，本包不臆断数值）。
- 依据件：`k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/P5_EXPECTED_VALUES_DESIGN_SIDE_20260921_v1.json`（825112398ff1ef76）。**边界**：预期值为设计侧推导 ⇒ **不构成 P5 证据**，判定归监理。

## 10. 标称值（V6-1）—— **已裁定（#K2-55 §一）**
| 轨 | 标称 | 主判窗（±5%） | 依据 |
|---|---|---|---|
| `12V_IN` | 12.0 V | 11.40–12.60 V | 轨名 + `J12/VIN_12V` |
| `P3V3` | 3.3 V | 3.135–3.465 V | 轨名 + `U6` 3.3V VCC 域（设定件 `U2/FB` 分压 `R40/R41`） |
| `P3V3_AUX` | 3.3 V | 3.135–3.465 V | 主机 PCIe 槽 aux（`J3`/`J4`） |
| `MCU_VDD` | **3.0 V**（主判） | **2.85–3.15 V** | #K2-55：主判工况 = **独立运行（`J13/VCC` 不接外供）** ⇒ `P3V3`(3.3V) − `U4`(BAT54C) Vf ≈0.3V |

- **主判工况（必须）**：**独立运行** —— `J13/VCC` **不接**外部供电；此时 `MCU_VDD` 应在 **2.85–3.15 V**。
- **辅助读数（须同记、不改主判）**：`J13/VCC` 供 3.3V 时测 `MCU_VDD`，按 **3.3V ±5% = 3.135–3.465 V** 记录。
- 另核：**轨集合完整**（板上电源轨恰为上述 4 条 + GND，无漏轨）。
- 依据件：`k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/P5_V6_1_NOMINALS_AND_MCU_VDD_CALIBER_20260921_v1.json`（b3c72f6dec777497）· 裁定 **#K2-55**。**边界**：标称/工况为监理裁定；实测与判定归实测方 + 监理（**ENG 不得自证**）。

## 11. **下单就绪**（监理 `#K2-58` R1：`STOP-1` 已解除 · 商务渠道）

> 监理 **#K2-58 R1**：`l8` 独立复核 = **PASS**（19/0 · 全锚复算 · 包 55/55 · DFM 16/1/0 · 差异恰好 4 条且语义正确 · 保真对照成立）⇒ **ENG 侧 `STOP-1` 解除**。本 §11 即 ENG 侧「**可下单**」之唯一索引；**实际下单/报价/交期 = 商务渠道**（owner #14④），**ENG 不自采购、不承诺**。

| 下单要素 | 值 |
|---|---|
| 受审板 | `k2_v4_8L.l8.kicad_pcb` · sha16 **`7a5c89913d6e5d0a`** |
| 交付包（**唯一上传件**） | `L6/DELIVERY_l8/k2_v4_8L.l8_gerber_package.tar.gz` · sha16 **`36a6b276b4f7e465`** |
| MANIFEST | `L6/jlc_package_l8/MANIFEST.json` · sha16 **`4b610baed4f4752c`** · `revision P5-L8.1` |
| 完整性 | `sha256sum -c DELIVERY_l8/SHA256SUMS.txt`（自 `L6/`）= **55/55 OK** |
| 叠层 / 工艺 | **8 铜层** · JLC HDI 盲埋孔（**阶数 ≥2**：含 `F.Cu→In1` 盲孔 · `In2→In5` 埋孔）· 成品厚 1.6mm（JLC08161H）· 外层 1oz / 内层 0.5oz |
| 阻抗 | **85Ω ±10%**（3 条耦合 run：`F.Cu|0.205` · `In2.Cu|0.16` · `In5.Cu|0.16`）⇒ **下单须注记阻抗控制 + 索取 V4 阻抗券**（见 §5） |
| 钻孔 | Excellon **7 文件**（6 组盲/埋孔对 + 通孔）· 总 **754 孔** · board↔drl 全对 |
| DFM | JLC HDI 通道 **16 PASS / 1 ACCEPT / 0 FAIL**（唯一 ACCEPT = 阻焊坝，承 l7 既有已裁项 + 有确定性修法证明） |
| 旧板保留面 | `l7`（缺 CR-26 修复）若已在外 ⇒ **按缺陷复现样处理 · 不得作合格首件**；`l8` 方为合格首件候选 |

**边界**：本注**不改**交付包（锚 `4b610bad`/`36a6b276` 逐字节未动）· 不改验收阈值/测点 · **P5 仍 `PENDING_EXTERNAL`**（可用性由外部实测 + 监理判定，**ENG 不自证**）。
