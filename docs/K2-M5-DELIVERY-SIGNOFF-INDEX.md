# K2 · M5《交付签核索引》（一页纸）—— #K2-315 §三 唯一交付

> 只读 · **零运行** · **零板变更** · 无 WORKER · 不触冻结四源。
> 机读件：`K2_R798_DELIVERY_SIGNOFF_INDEX_v1.json`（hash16 **`b821a17cacef1c1e`** · `binary = SIGNOFF_INDEX_PASS` · **89 项逐项挂 `路径 + sha16`** · `CONSISTENT = true`）。
> **受审板**：`k2_v4_8L.l8.kicad_pcb` · sha16 **`7a5c89913d6e5d0a`**（R794 ⇄ JLC 包 ⇄ R792 **三方一致** ✓）。

## 1. 制造包（下单就绪 · JLC 结构）

| 组 | 件数 | 位置（在册路径） |
|---|---|---|
| Gerber（RS-274X） | **14** | `L6/jlc_package_l8r3/01_gerber_rs274x/` |
| 钻孔（Excellon ＋ HDI 分对） | **15** | `…/02_drill_excellon/` |
| **叠层图** | **2** | `…/03_stackup/` |
| **阻抗表** | **2** | `…/04_impedance/`（目标 **85Ω ±10%** · `w 0.205 / gap 0.175` · 模型 `JLC_SI9000_H1_5.0mil_Er1_4.3` · 需阻抗券） |
| 层序 | 1 | `…/05_layer_sequence.txt` |
| 随单裁定 | **8** | `…/06_rulings/` |
| 验证件 | **9** | `…/07_verify/` |
| 订单备注 / 披露 / MANIFEST | 3 | `ORDER_NOTES.md` · `DISCLOSURE.md` · `MANIFEST.json` |

**工艺**：**JLC08161H**（南亚 NP-155F）· 8L · 1.6mm ±10% · 外层 1oz/内层 0.5oz · **工艺冻结 A：HDI 盲埋孔（阶数 ≥2）** · ENIG · 尺寸 120.1×46.1mm。

## 2. 独立复算导出（R794 · 同一受审板）

`P6_OPEN_READINESS/gerber_r794/` **29 件**（8 铜层 ＋ 阻焊 ×2 ＋ 丝印 ×2 ＋ 边框 ＋ job ＋ Excellon ×7 ＋ 钻孔图 ×7 ＋ 钻孔报告 1）· `K2_R794_GERBER_MANIFEST_v1.json` ＋ `_addendum.json` 逐件 bytes/sha16。

## 3. DFM ＋ 170 处置（签核证据）

| 项 | 读数 | 件 |
|---|---|---|
| DRC | **170**（**error 0** / warning 170）· `unconnected 0` · `clearance 0` | `K2_R794_board_drc.json` |
| **170 逐条处置** | **162** 分类（courtyard/silk/lib/track_not_centered）归 DFM 闸 · **8 真实缺陷具名豁免** | `K2_R794_WARNING_DISPOSITIONS_v1.json` |
| **DFM 目标通道** | **16/16 PASS** | `K2_R794_DFM_AND_CHECKUP_v1.json` |
| 全版体检 | 供 owner/商务 | 同上 |

### 3.1 八条具名豁免（1:1 挂证据）

| # | 类型 | 网/位置 | 理由（摘） |
|---|---|---|---|
| 1 | `track_dangling` | GND (F.Cu) x≈44.45 | MCU/低速域残留短桩；**删件级联**（离线 smoke 实测） |
| 2-7 | `via_dangling` ×6 | `PERSTA# / UART_TX / SWCLK_BOOT0 / P3V3×2 / LED_A`（x 29–50） | **非目标通道**（侧带/电源域）悬空过孔；同上 |
| 8 | `copper_sliver` | In4.Cu | 铺铜毛刺；归 DFM/铺铜重整 |

（逐条 `uuid/pos/reason` 见机读件 `eight_named_exemptions_1to1`。）

## 4. 覆盖范围声明（承 C12）

**目标通道 16/16 `FULL_CHAIN`**：`器件球(U6) → 入段 → 廊道 → 门 → 连接器焊盘(J2)`（两端皆落焊盘）。
件：`K2_R792_FULLCHAIN_DRAWING_FROM_BOARD_v1.json`（全链施工图 · 逐线几何）。

## 5. 散热要求（如实标注）

**SPEC rev-56 未声明热设计字段**（检索 thermal/散热/温度/theta/watt/dissipat = **0 命中**）。
散热要求**以 JLC 工艺冻结 A ＋ `ORDER_NOTES.md` 制造参数为准**；如需热设计件（铜面/散热孔/温升），须**另件**（属新增交付面，本索引不代造）。

## 6. 机核对账（`CONSISTENT = true`）

`board_sha16` 三方一致 ✓ · `DRC total = dispositions total = 170` ✓ · `真实缺陷 8 = 豁免登记 8` ✓ · `DFM 16/16 PASS` ✓ · `覆盖 16/16 FULL_CHAIN` ✓ · **89 项全有 sha16** ✓ · **0 缺件** ✓。

## 7. 签核位（人类）

- [ ] 制造包核对（Gerber/钻孔/叠层/阻抗）　- [ ] DFM 目标通道确认　- [ ] **8 条豁免逐条认否**　- [ ] 叠层/阻抗/工艺通道确认　- [ ] **商务下单（owner）**
- **下单闸**：本索引**只递签核**；**下单 = 商务**（owner 2026-09-14 口径）⇒ **下单维持停线**，等 owner 拍板。

OWNER-ITEMS: 0
