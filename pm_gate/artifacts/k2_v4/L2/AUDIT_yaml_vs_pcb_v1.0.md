# 审计：YAML 原理图权威 vs k2_v4.kicad_pcb 产物（v1.0 → 已裁决）

> 日期：2026-08-16。审计人：PM 门禁（Sisyphus 编排，WORKER 反思触发）。
> 目的：产出"重写权威生成器"的权威输入清单——封装/几何/走廊/网表全对齐，消灭 L3 打地鼠。
> 结论先行：**U1 封装无矛盾（产物=QFN32 与 YAML 一致）；真正矛盾在 ① ReDriver refdes 错位 ② AC 耦合电容规格脱节 ③ 缺失器件 18 个**。
> **裁决状态：5 项全部批准（2026-08-16）→ 已落纸 L2_STRUCTURE v1.2 + SPEC v1.1 + ECN-004。**

---

## 1. 权威源定义（三件套）

| 权威源 | 文件 | 角色 |
|---|---|---|
| 原理图权威 | `revA/boards/ioconvert_v2.yaml` | 网表事实源（160 nets / 115 器件 / 34 symbols） |
| L3 冻结施工图 | `revA/pcb/pm_gate/artifacts/L3/SPEC_k2_v4.json` | 几何/走廊/阻抗约束包络 |
| L2 冻结结构 | `revA/pcb/pm_gate/artifacts/L2/frozen/L2_STRUCTURE_v1.0.md` | 叠层/走廊/PDN 冻结决策 |

---

## 2. ✅ 无矛盾项（产物与权威一致）

| 项 | YAML 权威 | k2_v4.kicad_pcb 产物 | 判定 |
|---|---|---|---|
| U1 封装 | `ForgeOS:MCU_STM32G0_QFN32`（STM32G0B1KBU6 UFQFPN32） | `MCU_STM32G0_QFN32` @(36.0,52.0)，Value=STM32G0B1KBU6 | ✅ 一致 |
| ReDriver 封装 | `Package_DFN_QFN:WQFN-64_10x5.5mm_P0.4mm` ×2 | `DS160PR810_WQFN64` ×2 @(93.825,44.7)/(93.825,62.7) | ✅ 封装一致 |
| J2 | `Connector:SlimSAS_x8_SFF-8654_74pin_RASide` | `CONN_J2` @(133.825,53.7) | ✅ |
| J3/J4 | `Connector:MCIO_4i_SFF-1016_RASide` ×2 | `MCIO_4X_38P_RA` ×2 @(59.5,44.5)/(59.5,62.7) | ✅ |
| 去耦 C67/C68/C72 | L2 冻结明确 MLCC_0603 | `MLCC_0603` @(91.0,49/52/55) | ✅ 与 L2 一致 |
| 板框 | SPEC x∈[23,143] y∈[33,71] | 实测器件范围符合 | ✅ |

---

## 3. ❌ 矛盾项（必须裁决后修正）

### 3.1 ReDriver refdes 错位（U3/U4/U6/U7）— 网表级硬伤

| 器件 | YAML 权威（原理图） | k2_v4.kicad_pcb 产物（PCB） | 问题 |
|---|---|---|---|
| ReDriver 下行(DN, J2→MCIO) | **U3**（连 C17-C32, PCIE_DN*） | **U4** @(93.825,62.7) 连 PCIE_DN* | refdes 错位 |
| ReDriver 上行(UP, MCIO→J2) | **U7**（连 C49-C64, PCIE_UP*） | **U3** @(93.825,44.7) 连 PCIE_UP* | refdes 错位 |
| BAT54C ORing | **U4** | **U6** @(40.0,37.0) | refdes 错位 |
| MUX TS3USB221A | **U6**（K2 卡 DNP） | 无 | K2 正确 DNP |

**影响**：YAML nets 中 `U7/` 引用 46 处、`U3/` 引用 46 处——PCB 若直接对网表，U3/U4/U6/U7 全部对不上。SPEC 走廊 bands 也写 "upper y=44.7→PCIE_UP*"（与 PCB U3 一致），即 SPEC 沿用了错误 refdes。
**裁决需求**：以 YAML 为权威 → PCB 应命名 **U3=下行(DN)、U7=上行(UP)、U4=BAT54C**。新生成器必须从 YAML 读 refdes，禁止自造。

### 3.2 AC 耦合电容规格脱节（ECO #25 未落地）

| 项 | YAML 权威 | PCB 产物 | 问题 |
|---|---|---|---|
| 容值 | **220nF**（C_220N，ECO #25 升级，TI SNLS658 §8.2.1.1） | **100nF**（37×MLCC_0201 全部 Value=100nF） | 容值错 |
| 封装 | `Capacitor_SMD:C_0402_1005Metric` | `MLCC_0201`（0.6×0.3mm 而非 1.0×0.5mm） | 封装错 |
| 数量 | 32×C_220N（C17-C32, C49-C64） | 37×MLCC_0201（含去耦被误用 0201） | 封装混用 |

**根因**：k2_build_v4.py 是 100nF/0201 时代产物，ECO #25 只改了 YAML 未改 PCB 生成器。
**裁决需求**：AC 耦合 = 32× C_220N **0402 220nF**（YAML 权威）；去耦 C_100N 用 0402，C67/C68/C72 用 0603（L2 冻结）。

### 3.3 缺失器件 18 个（PCB 应有而产物没有）

| 类别 | 缺失 refdes | YAML 归属 |
|---|---|---|
| ReDriver VCC 去耦（ECO #25 强制：每片 4×0.1µF+1×1µF） | C74,C75,C76,C77,C78 / C79,C80,C81,C82,C83 | Power Decoupling 页 |
| P3V3 总线 bulk | C84(10µF) | Power Decoupling 页 |
| P3V3_AUX 去耦 | C90 | Power Decoupling 页 |
| I2C pull-up（ECO #25: 4.7K） | R31,R32,R33,R34 | MCU & Sideband 页 |
| **第二片 ReDriver** | **U7**（被错误命名为 U4） | AC-Coupling Upstream 页 |

**影响**：ReDriver 8 个 VCC pin 去耦缺失 = PDN 违规（TI SNLS658 §6.6 强制），I2C 无上拉 = 边带通信失效。

### 3.4 PCB 有而 YAML-K2 清单外（8 个，需逐项裁决）

D1(LED)、R1(10K)、R3(220R)、R21(1K)、R28/R29(10K)、U4(应为U7)、U6(应为U4)。
注：R1/R3/R21/R28/R29 属 MCU & Sideband 页 K1/K2 共用电路，K2 卡是否需要待裁决（R28/R29 = BOOT0/NRST strap，ECO #24 明确 K2 需要）。

---

## 4. 几何约束清单（重写生成器的冻结输入）

来源：SPEC_k2_v4.json + L2_STRUCTURE_v1.0.md + ECN-001/002/003 裁决。**生成器零自由度，全部从本清单读取。**

### 4.1 板几何
- 板框：x∈[23.0,143.0]、y∈[33.0,71.0]（120×38mm）
- J2@(133.825,53.7)、U3/U7@(93.825,44.7/62.7)、J3/J4@(59.5,44.5/62.7)
- U1@(36.0,52.0)、E2@(44.0,60.0)、U5@(44.5,52.0)、U2@(33.0,37.0)、U4(BAT54C)@(40.0,37.0)

### 4.2 走廊（SPEC 冻结）
- J2_TO_U：x∈[98.83,132.65]、y∈[40.10,64.50]、8 对
  - upper band y=44.7 (PCIE_UP*, 4 对)、lower band y=62.7 (PCIE_DN*, 4 对)、带距 ≥2.0mm
- U_TO_MCIO：x∈[64.90,88.83]、y∈[40.10,67.30]、8 对
  - upper y=44.7 (UP)、lower y=62.7 (DN)、带距 ≥2.0mm

### 4.3 电容墙（SPEC 冻结）
- symmetric_bands=true；MCIO 侧 x∈[75,90]、J2 侧 x∈[93,128]
- upper_band_y∈[44.0,47.0]、lower_band_y∈[60.0,66.0]
- 32×C_220N 对称分布（16 下行 + 16 上行）

### 4.4 阻抗/网类（SPEC 冻结）
- PCIe85：w=0.205/g=0.175、85Ω±10%、对间 ≥0.875mm、对内等长 <0.15mm
- LOW_SPEED：w=0.15/c=0.1；POWER：w=0.5/c=0.2
- 高速 0 过孔、F.Cu 全程、AC 焊盘下 GND 挖空

### 4.5 逃逸过渡区（ECN-001 裁决）
- 焊盘墙→走廊带每 pin 独立垂直逃逸段（0.4mm 节距）
- 走廊带 y 避开焊盘墙 ±0.1025mm；无 via、无 90° 直角

### 4.6 电容位置约束（ECN-003 裁决，禁止硬编码）
- C63→(100.8,42.9)、C30→(84.0,60.85)、C31→(86.0,61.65)、C65→(93.625,58.9)、C71→(90.0,48.0)
- **必须由生成器从 capacitor_walls + 间距预算几何推导复验，非坐标硬编码**

---

## 5. 重写权威生成器输入/输出契约（草案）

```
输入:
  YAML (nets + symbols + sheets placements)  → 网表/器件/refdes 唯一事实源
  SPEC_k2_v4.json                            → 几何/走廊/阻抗/过孔约束
  L2_STRUCTURE_v1.0.md                       → 叠层/PDN/逃逸过渡区决策
  ECN-001/002/003 裁决                        → 增补约束（逃逸区/坐标复核/电容推导）

输出:
  k2_v4.kicad_pcb                             → 117 器件 + 32×C_220N(0402) + 全 nets
  写盘前 fail-fast 自检:
    1. 焊盘重叠 == 0（几何）
    2. refdes 与 YAML 100% 对齐（U3/U7/U4 命名修正）
    3. AC 电容 32× 0402 220nF（封装+容值+数量）
    4. 缺失器件 == 0（C74-C84/C90/R31-R34 补齐）
    5. 走廊/电容墙坐标 ∈ SPEC 冻结范围
    6. 网表一致性：每个 pad 的 net ∈ YAML nets
```

---

## 6. 裁决结果（2026-08-16 PM 批准，ECN-004）

| # | 裁决项 | 结论 |
|---|---|---|
| 1 | ReDriver refdes | ✅ **批准**：U3=DN(93.825,62.7)、U7=UP(93.825,44.7)、U4=BAT54C(40.0,37.0)，YAML 权威 |
| 2 | AC 电容 | ✅ **批准**：32×C_220N 0402 220nF（ECO #25 落地，C17-C32 + C49-C64） |
| 3 | 缺失器件 | ✅ **批准补齐**：C74-C84 + C90 + R31-R34 + U7（ReDriver VCC 去耦/P3V3 bulk/P3V3_AUX/I2C pull-up） |
| 4 | 多余器件 | ✅ **确认保留**：R1/R3/R21/D1/R28/R29（K1/K2 共用，R28/R29=BOOT0/NRST strap ECO#24） |
| 5 | 清单冻结 | ✅ **冻结**：L2_STRUCTURE v1.2 + SPEC v1.1 增补完成 |

**执行锁定**：以上裁决已写入冻结物，L3 生成器（重写中）必须 100% 遵守，禁止回退旧命名/旧规格。

### 6.1 实施追加裁决（2026-08-16，生成器 DRC 验证暴露，已全部冻结进 SPEC v1.1）

| # | 裁决 | 内容 | 验证 |
|---|---|---|---|
| 6.1.1 | 排针列公式修正 | 初版冻结公式"相邻中心距=半跨和+0.3"遗漏 pad 直径 1.5mm（S1 自检拦截 24 短路）；修正为 **相邻 pad 中心距 = 1.5 + 0.3 = 1.8mm** → J12@35.32/J6@39.66/J13@46.54/J9@55.96/J11@65.38 | shorting 24→0 |
| 6.1.2 | AC 电容墙最小中心距 | 0402 封装同 y 行相邻中心距 ≥ **1.3mm**（0.4 pad + 0.2 clearance + 余量；旧 1.2mm → 0.1mm 间距违规）→ C17-C32 四行全部 1.30mm | clearance 非固有归零 |
| 6.1.3 | 锚点修正 anchor_fixes | 产物锚点既有违规：C66↔U3 0.025mm、C63↔C64 0.10mm → **C66@(89.8,61.25)、C64@(99.825,43.6)**；追加 C66↔C82 交互冲突 → **C82@(91.0,64.0)**（移入 ECN-004 备用带 [64,66]） | 非固有 clearance = 0 |
| 6.1.4 | 生成器缺陷修复 | pad_bboxes 旋转 pad 中心未随 footprint 旋转（rot 90/180 器件 S1 静默失真）→ 按 KiCad 约定修正 | S1 首次真实检出排针重叠 |

**终态（k2_v5.kicad_pcb, 101 器件/524 pads）**：DRC = **shorting 0 / 非固有 clearance 0 / hole_to_hole 0 / 仅剩 WQFN64 自身 0.4mm 脚距固有 118 条 + J12 板边 0.30 vs 0.50 Board Setup 核对项 1 条**。生成器 `k2_gen_v5.py`：8 项 fail-fast 自检（S1-S8）全 PASS，SPEC 三份约束零硬编码读取，S8 排针坐标冻结精确匹配。

## 7. 下一步（待 PM 裁决后执行）

1. **[裁决] ReDriver refdes**：批准 U3=DN/U7=UP/U4=BAT54C 命名修正（YAML 权威）
2. **[裁决] AC 电容**：批准 32×C_220N 0402 220nF（ECO #25 落地）
3. **[裁决] 缺失器件**：批准补齐 C74-C84/C90/R31-R34/U7
4. **[裁决] 多余器件**：R1/R3/R21/D1/R28/R29 逐项确认 K2 是否保留
5. 冻结本清单为 `L2_frozen_refdes_capacitors_v1.0` 增补 → 重写权威生成器
