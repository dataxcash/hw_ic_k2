# K2 · P6 §⑦ 承接 N-3 —— **K1 refdes 逐件对账（引脚级）+ 原理图再生可执行性实测**

- 工件：`k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K1_REFDES_PINLEVEL_RECONCILIATION_20260921_v1.json`（sha16 `49b028430fd0cc83`）
- 性质：**只读审计 + 可行性实测**。未写 `k1/` 任何文件；未动冻结源/交付锚/`criteria`；不新增判据维、不加检查齿（owner ②）。
- 渲染器实测输出**仅在 `/tmp`**。
- 日期：2026-09-21 · ENG(ARCHER)

## 0. 一句话
K1 **板级真源引脚级自洽**（板 42 == `k1_board.yaml` 42 == `k1_pinmap.yaml` 42；**零个带网 pad 未被 pinmap 覆盖**）；缺口**全部在原理图侧**：少 5 件 + 3 处符号陈旧 + 1 处型号错（U12）。且实测证明**原理图可再生**（共享 `schlib` 端到端 rc=0、逐字节确定性），但 **N-3 原述的生成器不存在**，须先把 `k1_sch.yaml` 重建为 42。

## 1. 计数对账（A）
| 源 | 件数 |
|---|---|
| 板 `k1_v1.kicad_pcb` footprints | **42** |
| `k1_board.yaml#devices` | **42** |
| `k1_pinmap.yaml#pins` | **42** |
| `k1_nets.yaml` 端点 refs | 42 |
| `k1_sch.yaml` placements | **37** |
| `k1/sch/*.kicad_sch` 编号 refs | **37** |

- 板侧四源**逐件一致**（42/42/42/42）。
- 唯一失配：**原理图侧（输入+产物）37 vs 板侧 42**，缺 **`Q1 · Q2 · R38 · R39 · U13`**；无板外幽灵件。

## 2. 引脚级覆盖对账（B）—— **板级自洽**
对每件检查「板上有名 pad 是否被 `k1_pinmap.yaml` 覆盖、未覆盖者是否带网」：

- **零个带网 pad 未被 pinmap 覆盖**（`uncovered_with_net = ∅`）。
- 未覆盖的 pad 全部 `net=None`（NC / EP / 机械），涉及 8 件（`J1,B6/B7` · `J14,A2…` · `Q1,1/2/4/7` · `U11,4/14/19/21/39/41` · `U12,4/6` · `U13,2/5` · `U8,7/8` · `U9,1/2/3/4/6/10`）。
- 反向：pinmap 中**无任何 pad 号**在板上不存在。
⇒ 板真源三件（pcb ↔ board.yaml ↔ pinmap）**引脚级自洽**，N-3 的「板为权威」前提成立。

## 3. 五件缺失件 · **引脚级全映射**（C）（符号脚名 → 板 pad → 网）
| 件 | 板 footprint | 板 pad 数 | 引脚级映射 |
|---|---|---|---|
| **Q1** | `WSON-10-1EP_2.5x2.5mm_P0.5mm_EP1.2x2mm`（TPS22990） | 15（11 名 + 4 无名 EP） | IN→3,11(PWR_5V_MAIN) · VOUT→8,9,10(VBUS) · ON→5(WORK_EN) · GND→6(GND)；pad 1/2/4/7 与 4 个无名 pad = `net=None` |
| **Q2** | `SOT-23`（2N7002） | 3 | G→1(KEY_DET_EN) · S→2(GND) · D→3(KEY_DET_RET) |
| **R38** | `R_0402_1005Metric` | 2 | A→1(SBU1) · B→2(SBU1_INT) |
| **R39** | `R_0402_1005Metric` | 2 | A→1(SBU2) · B→2(SBU2_INT) |
| **U13** | `DFN-6_1.6x1.3mm_P0.4mm`（TPD2E001） | 6 | VCC→1(P3V3_AUX) · IO1→3(SBU1) · GND→4(GND) · IO2→6(SBU2)；pad 2/5 = `nc` |

> 权威来源 = `k1_pinmap.yaml`（板侧机械派生的脚名↔pad 映射），与 `k1_board.yaml#devices[*].nets` 的网集一致。

## 4. 原理图侧残项（D）
| id | 件 | 严重度 | 事实 | 引脚级判读 |
|---|---|---|---|---|
| **K1-S1** | J1 | 高/BLOCKING | 原理图 Footprint = HRO_TYPE-C-31-M-12(16-pin USB2-only) vs 板 = Amphenol_12401548E4-2A(30 pad · SS 8/8) | 符号 16 脚名已由 pinmap 正确落到板 30 pad；**仅 Footprint 属性陈旧**（非脚缺失） |
| **K1-S2** | U10 | 中/WARN | 原理图 Footprint = SOT-23(3 pad) vs 板 = SOT-23-5 | 符号 5 脚(VIN1/GND2/EN3/NC_ADJ4/VOUT5) 与板 pad 1-5 **逐一对应且网一致** ⇒ **符号正确，仅 Footprint 属性陈旧** |
| **K1-S3** | — | 低 | `k1_board.yaml#reconciliation.device_count` 自述 `schematic_sch_k1=42/diff=[]` | 盘上实测 37 ⇒ 自述与盘上不符 |
| **K1-S4** | U12 | **高（新登记）** | 原理图 U12 = `IOCONVERT:TPS22919`（6 pin #1-6：IN/GND/ON/NC/QOD/VOUT）vs **板侧冻结值 U12 = TPS22965（DSG WSON-8）** | 按 pad 号 join 会错接：pin2(GND)↔pad2(IN)**✗** · pin6(VOUT)↔pad6(NC)**✗** · pad7/8(VOUT)、pad9(GND/EP) 无符号脚 ⇒ **网表断裂** |
| **K1-S5** | — | **高（N-3 可执行性更正）** | `k1_sch_sync_v1.py` **只写** `k1_board.yaml`/`k1_nets.yaml`（且二者已同步）；**全仓无工具写 `k1/sch/*.kicad_sch`** | 见 §5 |
| **K1-S6** | J10 | 中（**自我更正·先前遗漏**） | 原理图 `HEADER_2PIN_12V` Footprint=`ForgeOS:PinHeader_1x02` vs 板侧真值=`Connector_JST:JST_VH_B2P-VH_1x02_P3.96mm_Vertical` | 2 脚(VIN_12V/GND) 与板 pad 1/2 对应；**仅 Footprint 属性陈旧**（同 S1/S2/S4 家族） |

**K1-S4 依据**：`k1_board.yaml#devices.U12.value=TPS22965` + 真源 `TPS22965.yaml`（抬头即『U12: 轨A 预鉴权轨负载开关』）；生成器 `k1_sch_sync_v1.py` 的 `U12_NEW` 块已把 value 改为 TPS22965（旧文本 `PWR_OLD` 仍留 `TPS22919` 字样）。⇒ 承「①方案冻结态、板为权威」，**原理图符号陈旧**。

## 5. 原理图再生 · **可执行性实测**（F）
**真路径**：原理图侧真源 = `k1/boards/k1_sch.yaml`（与 `k2/hw/data/k2_sch.yaml` **schema 逐键相同**）→ 共享层 `_shared/schlib`（`k1/_shared` 为其符号链接）→ 薄 driver `k2/tools/k2_sch_gen_v1.py`（env `K2_SCH_YAML`/`K2_OUT_SCH`）。

**冒烟（输出仅 `/tmp`，仓库零写）**：
```
K2_SCH_YAML=<abs>/k1/boards/k1_sch.yaml K2_OUT_SCH=/tmp/k1rec/sch_out \
  python3 k2/tools/k2_sch_gen_v1.py     # rc=0
```
| sheet | components | bytes | sha16 |
|---|---|---|---|
| Connectors (A2) | 3 | 50003 | `63dc35f88e03213f` |
| MCU & Sideband (A3) | 21 | 70756 | `7fef503676912685` |
| Power Decoupling (ReDriver VCC) (A4) | 1 | 2608 | `8814c503948e8014` |
| Power (12V DC-in DCDC 5V LDO 3V3) (A4) | 12 | 30126 | `1e35c9dadf39806a` |

- **确定性**：同输入连跑两次 ⇒ 输出**逐字节相同**（`diff -rq` 无差异）。
- root 元数据由 driver 常量 `EXISTING_ROOT` 取自 **k2** root ⇒ K1 落地须注入 K1 root（低风险小改）。

**`k1_sch.yaml` 陈旧点**（再生前必须修）：
1. placements **37 → 42**（补 Q1/Q2/R38/R39/U13 的 symbol def + placement + net）；
2. symbol def `USB_C_RECEPT`：fp `…HRO_TYPE-C-31-M-12` → `…Amphenol_12401548E4-2A`（K1-S1）；
3. symbol def `LDO_5V_3V3`：fp `Package_TO_SOT_SMD:SOT-23` → `:SOT-23-5`（K1-S2）；
4. symbol def `TPS22919` → **TPS22965**（含正确 WSON-8 footprint 映射）（K1-S4）。

## 6. 交监理的 N-3 范围更正（H · **监理自裁项，非 owner**）
原 N-3 述『由 `k1_board.yaml` 经既有 `k1_sch_sync_v1.py` 再生原理图』**不成立**（该脚本不含原理图生成）。建议拆两步：
1. **重建 `k1_sch.yaml` 42**：补 5 件 symbol def/placement/net + 修 §5 的 3 处符号（K1-S1/S2/S4）；订正 `device_count` 自述（K1-S3）。
2. **再生 + 落地**：用共享 `schlib` 再生 4 页 `.kicad_sch` + 注入 K1 root ⇒ `refdes_sets_equal` 5 件差归零；**一笔提交 + K1 锚重基线**。

- 不新增判据维/检查齿；不动 K2 交付锚；**无 owner 闸口**。
- 回滚点：`k1 dc720fd`（未动）；本件 `k2` 提交为纯新增件。

## 7. 【更正】K1-S6 —— 先前遗漏的 J10
本会话新建的 N-3 验收核（`k2/docs/drafts/n3-k1-sch-regen-v1/k1_sch_regen_acceptance_v1.py`）在**逐件 footprint basename 对 `k1_board.yaml`** 的检查（C 项）中**当场暴露**：`J10` 的 symbol `HEADER_2PIN_12V` footprint 仍为 `ForgeOS:PinHeader_1x02`，而板侧冻结真值 = `Connector_JST:JST_VH_B2P-VH_1x02_P3.96mm_Vertical`（JST VH 3.96mm 2P · 10A/250V · 需求冻结 v1 §2.6）。
⇒ 具名登记为 **K1-S6**（与 K1-S1/S2/S4 同族：原理图侧 footprint 未随板侧更新）。
**诚实登记**：此为 ENG 先前审计的**遗漏**（原 D_residuals 仅 S1..S5），不影响既有结论、canonical 读数与交付锚。
