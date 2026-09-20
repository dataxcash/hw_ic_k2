# K2 · P6 §8.2③ —— P5 回件模板 **预填 + 预验**

- 预验工件：`k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/P5_RESULTS_TEMPLATE_PREFILL_AND_PREVALIDATION_20260921_v1.json`（sha16 `b8e93a8be58521df`）
- 预填件（**供外部方直接填**）：`…/P6_OPEN_READINESS/P5_RESULTS_TEMPLATE_PREFILLED_20260921_v1.json`（sha16 `eb6bcac1261707ff`）
- 性质：**只读**。未改 `criteria/`、未改阈值、未动 L6 交付锚/包内件、未改生成器。
- 日期：2026-09-21 · ENG(ARCHER)

## 0. 一句话
P5（唯一未闭阶段门）回件包**预填完成**：RULES 的逐项测点/方法/证据要求与**已裁定期望值**写入只读副本的 `measurement_guide`/`expected`，**全部 `measured` 槽保持空**（机核未改）；预验读数为 **结构 8/8 齐备 · 阈值 token 19/19 在 RULES 与模板双侧命中 · 锚三项相符 · 板侧测点独立复核全 OK**；并具名登记 2 处**须外部方填**的缺口。

## 1. 结构预验（A）
- 8 项（V4 · V5 · V6-1..5 · V7）· `required` 全 true · `status_enum` = {NOT_RUN,PASS,FAIL,INCONCLUSIVE} · `criterion`/`status`/`evidence` 槽 8/8 齐备。

## 2. 阈值交叉核对（B）
19 个关键 token（`76.5`/`93.5`/`0.2825`/`3%`/`±5%`/`120.0`/`117.0`/`9.5`/四工况 `4.7·6.0·5.8·7.0` 与预测 `91.7·106.0·103.8` …）：
- **RULES.md 命中 19/19**；**模板（全文）命中 19/19**。
- 说明：其中 9 个不在 `criterion` 字符串里而落在 `measured.*`（如轨名 `12V_IN`、`SWDIO`、`U1`、四工况 `P_W`/`Tj_pred_C`）⇒ 属**字段位置差异**，非缺项。

## 3. 锚核对（C）
| 项 | 值 | 判 |
|---|---|---|
| 受审板 sha16 | `c5a7df90aadb66e0` | ✅ |
| 交付锚 MANIFEST | `6ee7495de61f749f` | ✅ |
| tarball | `0e88e107e2da8192` | ✅ |
| RULES / 模板 / 自检 / CHECKLIST sha16 | `8bee09616020d5a9` / `c688b7daf9953b30` / `3f89dec1a6481fe5` / `d7dda9a82c5d06f3` | 记录 |

## 4. 板侧测点独立复核（D · pcbnew-free 直读 l7）
| refdes | 核对 | 实测 | 判 |
|---|---|---|---|
| `J13` | pad1..4 | SWDIO / SWCLK_BOOT0 / GND / MCU_VDD | ✅ |
| `U1` | pad10 | `NRST` | ✅ |
| `E2`（FRU EEPROM） | pad1..8 | GND / MCU_VDD / GND / GND / I2C1_SDA / I2C1_SCL / GND / MCU_VDD | ✅ |
| `J2` / `J3` / `J4` / `U6` | 存在性 | 全在 | ✅ |

> **订正**：RULES §V6-3 未具名 FRU 器件；**K2 板上 FRU EEPROM = `E2`**（K1 才叫 E1）。已写入预填件的 `expected.refdes`。

## 5. 预填内容（E）
只读副本新增三块（`measured` 一律不动）：
1. **`measurement_guide`**（8/8）：逐项测点/方法/证据清单（逐条源自 RULES）。
2. **`expected`**（8/8）：**已裁定期望值**，例：V4 `76.5–93.5Ω`（nominal 85Ω±10%）· V5 `≤3%`（In4.Cu 电源面）· V6-1 `±5%` · V6-4 `x4 Gen4 16GT/s` · V6-5 `30min · AER=0` · V7 `Tj≤120℃`（T1 触发 `>117℃`，θJA_eff≤9.5，四工况 P_W/Tj_pred）。
3. **`prefill_gaps`**（2 项具名）。

## 6. 须外部方填 / 未预填的缺口（F · **诚实登记，禁自定**）
| 缺口 | 处置 |
|---|---|
| `V6_2.expected_device_id` | 仓库**无出处** ⇒ 外部方按 `STM32G0B1KBU6` 手册填（本件不代填，免自定判据）。 |
| `V6_3.expected_address` | 仓库**无出处**；本件给**板侧实测 strapping**：`E2` A0=GND · A1=MCU_VDD · A2=GND ⇒ 对 1010xx 族期望 **7-bit `0x52`**。**须按实际器件/FRU 规格确认**（仅给客观 strapping + 推导，不代定判据）。 |
| V5/V6-1 轨**标称值** | 仓库**无出处** ⇒ **未预填**（C-12 禁自定阈值）；外部方按轨名/手册填。 |

## 7. 边界
P5 为**外部实测项，ENG 不得自证**；本件只做**预填与预验**，判定归监理。未越阶段（P5 仍 `PENDING_EXTERNAL`）；未新增判据维/检查齿。
