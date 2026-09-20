# K2 · 独立复核发现 · `STM32G0B1KBU6` 脚位真源整体旋转（KBU6-PINROT-1 / K1-D13）

- 机读件：`pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/STM32G0B1KBU6_PIN_ROTATION_DEFECT_20260921_v1.json`（sha16 `b23ac49fa5f805fd`）
- 日期：2026-09-20 · ENG（ARCHER）· **只读登记，未改动任何受保护件**
- 缘起：续接会话按 handoff §7-4「只读造活（同族自查）」复核 sch_gate 器件真源。

## 一、结论（一句话）

`_shared/eda_core/sch_gate/datasheets/STM32G0B1KBU6.yaml` 的 **物理脚 25..32 映射比厂商真源整体旋转一位**；K1 板 U1(=STM32G0B1KBU6) 的 pinmap 与 N-3 再生的原理图符号**继承了该错位**。K2 现役板用 `STM32G0B1CBT6`（其真源正确）⇒ **K2 交付面不受影响**。

## 二、真值比对（厂商 DS13560 · Table 12 · 列 `LQFP32/UFQFPN32 - GP`）

| pad | 厂商真值 | 现 YAML | 判定 |
|---|---|---|---|
| 25 | PA14-BOOT0 | PA15 | ✗ |
| 26 | PA15 | PB3 | ✗ |
| 27 | PB3 | PB4 | ✗ |
| 28 | PB4 | PB5 | ✗ |
| 29 | PB5 | PB6 | ✗ |
| 30 | PB6 | PB7 | ✗ |
| 31 | PB7 | PB8 | ✗ |
| 32 | PB8 | PA14 | ✗ |

形态：`yaml[25..32] = truth[26..32] + truth[25]`（**循环右移一位**）。脚 1..24 两侧**逐脚一致**。

## 三、为何以 Table 12 为准（证据链）

1. **表结构解析**：`pdftotext -layout` 下行 token = `[c1..c11 封装列][pin name][type][AF…]`；`c1 = LQFP32/UFQFPN32-GP`（表头最左列），`c3 = LQFP48/UFQFPN48-GP`。
2. **完备性**：`c1` 取值覆盖 1..32（2/3 = PC14/PC15 因行长名未匹配，由 Fig 12 补认）⇒ 确为 32 脚封装列。
3. **解析器交叉校验（关键）**：同一解析器对 `c3`(LQFP48) 的输出与**受信文件** `STM32G0B1CBT6.yaml` **逐脚 30/30 一致**（PC13=1·NRST=10·PA0=11·PA4=15·PB0=19·PA8=28·PA10=32·PA13=35·PA14=36·PA15=37·PB3=42·PB6=45·PB8=47·PB9=48…）。
4. **单调性判据（决定性）**：嵌套封装的「小脚号↔大脚号」沿同一边应单调。Table 12 给出 `25→36·26→37·27→42·28→43·29→44·30→45·31→46·32→47` **单调**；Figure 12 文本流两种配对（正/逆序）**均非单调** ⇒ **以 Table 12 为准**。
5. 同源 Figure 9(LQFP48) 文本流同样呈「名字块与编号块顺序相反」⇒ 图形文本抽取**不可**按位置配对。

## 四、影响面

- **K1（受影响）**：U1 符号/pinmap 中 `SWCLK_BOOT0 32→25`、`I2C1_SCL 29→30`、`I2C1_SDA 30→31`、`PB3 26→27`、`PB4 27→28`、`PB5 28→29`、`PB8 31→32` 全部错位；
  且 pinmap 中 `KEY_DET_EN: 25`，物理 pad 25 = **PA14-BOOT0** ⇒ pad 25 用途本表 SWD/BOOT0 语义冲突（= **球重映射 = L1**）。
- **N-3 再生**：`k1 9e283bf` 的 `sch/` 沿用上述脚号 ⇒ 该批含 7 脚错（若成立，须重出 BOM + 判定）。
- **K2（不受影响）**：现役 hw = `STM32G0B1CBT6`（LQFP48，真源经 c3 列 30/30 校验正确）⇒ 交付锚 `6ee7495de61f749f` 与 canonical 19 不动。

## 五、待批动作（ENG 不自行动手）

1. **监理自裁**：订正 `_shared/.../STM32G0B1KBU6.yaml` pins 25..32（`_shared` 件 ⇒ 须批 + **同批升版**）。
2. **owner（L1）**：K1 MCU pad 配对（`{9,25}` 与 KEy_DET_EN / SWD-BOOT0 物理脚归属）。
3. 订正后重跑 K1 链：`k1_sch_regen_v1.py` → `k1_sch_gen_v1.py --install` → `k1_p4_bom_gen_v1.py` → `verify k1` → K1 判定，并复核 pinmap 校验器判定。
4. 同族机检：`sch_gate/datasheets/` 其余 32 件排查同型「图形转写」错位。

## 六、诚实边界

- 取回镜像为 **DS13560 Rev 1**（引证为 **Rev 6**）；封装脚位为硅片/封装固有、跨 revision 不应变化，仍建议以 Rev-6 原件二次确认（与 T2-F1/T2-F7 同族引证面）。
- **禁充绿**：本件为**登记**，不声称已修复；未改动任何受保护件。
