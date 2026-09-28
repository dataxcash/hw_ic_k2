# K2 · 方案闸阈值来源件（C17′ · 取件记录 ＋ 原文引用）

> 依据：#K2-336 §四.1「阈值齐备：P1–P7 每条注明**出处**（AI+WEB 取厂商／PCIe 规范／JLC 工厂能力文件）」· 本窗（R848）执行。
> 纪律：**只引原文，不发明阈值**；取不到 ⇒ 记 `PENDING` 并具名缺哪个输入。
> 取件日期 2026-09-28 · 取件机 `curl -sSL` · **HTTP 200** 逐条记录。

## 1. PCIe CEM 规范（权威 SI 阈值）

| 项 | 值 |
|---|---|
| 件 | `PCI Express Card Electromechanical Specification, Revision 5.0, Version 1.0, June 9, 2021`（PCI-SIG） |
| URL | `https://image.lceda.cn/attachments/2025/1/cC9ZlhB8zD2bXInsUm1R6XsieT6oV0VdRs5lGeLw.pdf`（成品库 §A′⑥「PCIe5.0CEM 官方白皮书.pdf」直链） |
| 机核 | **HTTP 200 / 9,168,040 B** · sha256[:16] `91c722e621cb52d3` |
| 本地 | `/tmp/k2dev/pcie5_cem.pdf`（临时 · 非入库） |

**原文（§4.7 电气要求 · 页 59–62）**

- **§4.7.6 对内歪斜（Skew within the Differential Pair）**：「the skew within differential pairs is less than **0.064 mm (2.5 mil) for the Add-in Card** and **0.127 mm (5 mil) for the system board**」
- **§4.7.5 线对间歪斜（Table 4-8, 页 59）**：`Total Interconnect Skew ST = 1.6 ns`；`PCI Express Add-in Card SA = 0.35 ns — Estimates about a 2-inch trace length delta on FR-4 boards`；`System Board SS = 1.25 ns — about a 7-inch trace length delta`。
- **§4.7.8 差分阻抗（Differential Data Trace Impedance）**：「16.0 GT/s and higher … in the range of **72.5 Ω to 97.5 Ω**」（8 GT/s 70–100 Ω · 5 GT/s 68–105 Ω）
- **§4.7.9 传播延迟（Differential Data Trace Propagation Delay）**：「The propagation delay for an Add-in Card data trace from the edge-finger to the Receiver/Transmitter **must not exceed 750 ps**」
- **§4.7.10 AIC 插损（32.0 GT/s）**：「The insertion loss from the top of the edge-finger to the silicon die pad **must not exceed −9.5 dB at 16 GHz**」（16 GT/s：−8.0 dB @ 8 GHz）
- **Annex C（热测试）**：approach ambient 取 **25 °C → 50 °C（65 °C 优先）** 六点。

**FR-4 尺度（规范自带）**：`0.35 ns ≈ 2 inch` ⇒ **1 mm = 175 ps / 25.4 = 6.8898 ps/mm**（⇒ 750 ps = **108.86 mm**；0.35 ns = **50.8 mm** ✓ 自洽）。

## 2. TI DS320PR1601 datasheet（主器件厂商锚）

| 项 | 值 |
|---|---|
| 件 | `DS320PR1601, SNLS683 – JUNE 2023`（TI） |
| URL | `https://www.ti.com/lit/ds/symlink/ds320pr1601.pdf`（成品库 §A1①直链） |
| 机核 | **HTTP 200 / 2,225,981 B** · sha256[:16] **`f61599c4356edb39`** —— 与成品库 §A1 记录的本地副本 hash **逐字节一致** ✓ |
| 本地 | `/tmp/k2dev/snls683.pdf` + 文本 `/tmp/k2dev/snls683.txt`（临时 · 非入库） |

**原文**

- **§1.1 Features**：「**Flow-through layout P2P with Intel retimer common footprint**」·「8.90 mm × 22.80 mm BGA package」（§5：ZDG nfBGA 354 · package size 22.89 mm × 8.9 mm）
- **§6.4 Thermal Information**：`RθJA-High K = 17.4 ℃/W` · `RθJC(top) = 6.5 ℃/W` · `RθJB = 6.1 ℃/W` · `ψJT = 3.6` · `ψJB = 5.9 ℃/W`；`TJ operating max = 120 °C`（abs max 150）
- **§6.5 DC Electrical**：`PACT = 4.7/6.0 W`（32-ch, EQ=0-2）· `PACT = 5.8/7.0 W`（EQ=5-19）· `PRXDET 660 mW` · `PSTBY 92 mW`
- **§9.4.1 Layout Guidelines**（**5 条厂商版图规范**）：
  1. 「Decoupling capacitors should be placed **as close to the VCC pins as possible**. Placing the decoupling capacitors **directly underneath the device is recommended** if the board design permits.」
  2. 「High-speed differential signals … should be **tightly coupled, skew matched, and impedance controlled**.」
  3. 「**Vias should be avoided** when possible on the high-speed differential signals. When vias must be used, take care to **minimize the via stub**, either by transitioning through most or all layers or by back drilling.」
  4. 「GND relief can be used (but is not required) beneath the high-speed differential signal pads…」
  5. 「**GND vias should be placed directly beneath the device**, connecting the GND plane attached to the device to the GND planes on other layers. This has the added benefit of improving **thermal conductivity**…」
- **§9.4.2 Layout Example**：`Figure 9-7. Top Layer View of TI PCIe Riser Card Using DS320PR1601 with CEM Connectors` · `Figure 9-8` 底面 —— **厂商自家 riser 版图 = 本板框架的第二样板**。

## 3. 在册件（in-register · 无需取件）

| 判据 | 阈值 | 出处 |
|---|---|---|
| P3 机械框架 | 孔距最近角 ≤ **3.0 mm** · 边缘 ≥ **0.3 mm** | `#K2-322 §三.1` ＋ SPEC `constraints.edge_copper_min` |
| P6 DFM 最小间距 | clearance 0 违例 | `_shared/eda_core/drc_rules.json`（冻结四源）＋ `kicad-cli pcb drc` |
| P4 拥塞（断面法） | 供给 ≥ 需求 | R537 方法（在册）· 供给侧**以「已布线见证」判定**（见下） |
| 对内等长（项目规则） | **0.15 mm** | `drc_rules.json diff_pair.intra_pair_skew_mm`（**注意**：PCIe 5.0 CEM AIC 要求 **0.064 mm** ⇒ 项目规则**宽松 2.3 倍** · 见报告 §五） |
| 对间间距 | 0.875 mm（铜边净空）/ 1.46 mm（对中心距） | `drc_rules.json` ＋ `route_model_config.json capacity_audit` |
