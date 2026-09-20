# K2 · P6 · **K1-D8（新·功能级）**：Q1/U12 的 VBIAS（器件偏置电源）未接

- 工件：`k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K1_BOARD_LEVEL_DEFECT_WORKLIST_20260921_v1.json`（sha16 `eafe45f704489d47`，新增 K1-D8/K1-D9）
- 关联：`N3_K1_SCH_REGEN_EXECUTABILITY_20260921_v1.json`（新增 **N3-G5**）· `PENDING_RULINGS_DELTA_..._v6.json`（`f1cc42694a946c4e`）
- 性质：**只读发现**。未动 `k1/`、`criteria/`、冻结源、交付锚。
- 日期：2026-09-21 · ENG(ARCHER)

## 0. 一句话
K1 板上 **Q1(TPS22990)** 与 **U12(TPS22965)** 的 **pin 4 = VBIAS（器件偏置电源）`net=None`**；手册明示 VBIAS 为**必需电源** ⇒ **两枚负载开关功能不可实现**。**根因在真源 `k1_board.yaml#net_coverage` 本身缺该网**（非布线中间态）。**本会话新发现**（全仓 `VBIAS` 仅见于 2 份手册 YAML ⇒ 先前 K1 对账/工作清单均未登记）。

## 1. 证据链（三重独立）
### ① 板直读（`k1/k1_v1.kicad_pcb`，pcbnew-free）
| 件 | pin4 (VBIAS) | 其余脚（现状） |
|---|---|---|
| `Q1` TPS22990 | **`net=None`** | 3/11=PWR_5V_MAIN(VIN) · 5=WORK_EN(ON) · 6=GND · 8/9/10=VBUS(VOUT) |
| `U12` TPS22965 | **`net=None`** | 1/2=PWR_5V_MAIN(VIN) · 3=TPS_EN(ON) · 5=GND · 7/8=VBUS(VOUT) · 9=GND(EP) |

### ② 手册（**下载件 sha256 与在册 `doc_sha256` 逐字节同 ⇒ 同版**）
| 手册 | sha256（前 16） | pin 4 原文 |
|---|---|---|
| `tps22990.pdf` SLVSDK1C | `ea198776524544eb` | **VBIAS** — *"Bias voltage. Power supply to the device"*；§7.3 推荐 **2.5–5.5 V**，且 **VIN 0.6 V – VBIAS** |
| `tps22965.pdf` SLVSBJ0F | `3300eef743d7871f` | **VBIAS** — *"Bias voltage. Power supply to the device. Recommended voltage range for this pin is 2.5 V to 5.7 V"* |

### ③ 脚号对应交叉验证（排除「pad 编号 ≠ 手册脚号」的误判）
- **Q1**：手册 pin3=VIN ∧ **EP=VIN**；板 pinmap `IN→{3,11}`（3=VIN ∧ 11=EP）✓；`ON→5` ✓ · `GND→6` ✓ · `VOUT→8/9/10` ✓ ⇒ **pad 4 必为 VBIAS**。
- **U12**：手册 *"VIN … Must be connected to Pin 1 and Pin 2"*；板 `IN→{1,2}` ✓；`ON→3` ✓ · `GND→5` ✓ · `VOUT→7/8` ✓ · 9=EP(thermal,GND) ✓ ⇒ **pad 4 必为 VBIAS**。
- 另：板用 footprint = 库 `WSON-10-1EP_...`（pads 1–11 + 4 无名，与板完全一致）⇒ 编号体系可信。

## 2. 性质：**功能级**，非「未布线中间态」
K1-D5 的 156 未连接 = **有网未布**（板 0 track，属中间态）。本项**网表中即无该网**（`k1_board.yaml#net_coverage` Q1/U12 各仅 4 网）⇒ 与中间态**性质不同**；即使完成布线也不会接通。

## 3. 影响与修法（**须授权**）
- **影响**：Q1 = 轨B **工作态 10A 通路**；U12 = **轨A 预鉴权轨**。二者失效 ⇒ `PWR_5V_WORK` / `PWR_5V_PREAUTH` 不可达。
- **修法候选**：VBIAS 接 **`PWR_5V_MAIN`(5 V)**（两件均在 5V 域；2.5–5.7V 合规且 ≥VIN）← ENG 倾向；或接 `12V_IN` 经降压（须新增器件）。
- **顺序**：**先修真源 `k1_board.yaml`（加 VBIAS 网）→ 再执行 N-3 再生**（见 N3-G5）；否则 N-3 会把缺陷机械固化。

## 4. 同源观察 K1-D9（不阻塞）
Q1 `CT`(pad1)/`PG`(pad7) 与 U12 `CT`(pad6) 空接：TPS22965 手册明示 CT *"Can be left floating"* ⇒ U12-CT 合规；TPS22990 CT 与 PG（*"Tie to GND if not used"*）**待确认设计意图**——设计要求明示 Q1『带 PG』而 PG 空置，宜复核。

## 5. 边界
只读发现；**未改 k1/**；未新增判据维/检查齿；未动 `criteria`/冻结源/交付锚。**属设计连接决策 ⇒ 交监理裁定（无 owner 闸口）**。
