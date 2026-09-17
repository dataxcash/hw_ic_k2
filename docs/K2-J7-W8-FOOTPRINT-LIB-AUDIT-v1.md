# K2 · J-7 / W-8「封装 = 库」电气级逐件审计（v1）

> 生成器：`k2/tools/k2_w8_footprint_audit_v1.py`（确定性只读；sha256 前16 = `75404d706413d546`）

> 板：`k2/hw/k2_v4_8L.l5.kicad_pcb`（sha256 前16 = `62cecafe810c637f`）；标准库根 `/home/fila/jqdDev_2025/ic_hw/AppDir/share/kicad/footprints`；项目库根 `/home/fila/jqdDev_2025/ic_hw/k2/hw/lib`

> 口径（监理 #K2-19 §二 W-8）：**以板为准**；判据容忍**图形级**差异；**电气级必须 0**
> （pad 数 / 名 / 尺寸 / 旋转 / 位置逐件比）。本件只交测量，判定权归监理。

| 量 | 值 |
|---|---|
| 板上 footprint 总数 | 59 |
| 电气级完全一致 | **2** |
| **电气级存在差异** | **31** |
| 仅 pad 名集合不同 | 2 |
| 无库链接（无 nickname，KiCad 不比对） | 24 |
| 库不可加载 | 0 |

## 逐条登记

| ref | 库 ID | pads 板/库 | 差异 pad 数 | 相对几何同 | 电气结论 | 差异字段 |
|---|---|---|---|---|---|---|
| C73 | Capacitor_SMD:C_0402_1005Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| C74 | Capacitor_SMD:C_0402_1005Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| C75 | Capacitor_SMD:C_0402_1005Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| C76 | Capacitor_SMD:C_0402_1005Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| C77 | Capacitor_SMD:C_0402_1005Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| C78 | Capacitor_SMD:C_0603_1608Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| C79 | Capacitor_SMD:C_0402_1005Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| C80 | Capacitor_SMD:C_0402_1005Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| C81 | Capacitor_SMD:C_0402_1005Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| C82 | Capacitor_SMD:C_0402_1005Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| C83 | Capacitor_SMD:C_0603_1608Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| C84 | Capacitor_SMD:C_0805_2012Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| C85 | Capacitor_SMD:C_0402_1005Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| C86 | Capacitor_SMD:C_0603_1608Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| C87 | Capacitor_SMD:C_0402_1005Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| C88 | Capacitor_SMD:C_0603_1608Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| C89 | Capacitor_SMD:C_0603_1608Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| C90 | Capacitor_SMD:C_0402_1005Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| D1 | LED_SMD:LED_0603_1608Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| E2 | ForgeOS:SOIC8_FRU | 8/8 | 4 | 否 | **差异** | pad:dy; pad:dy; pad:dy; pad:dy |
| J2 | ForgeOS:SlimSAS_x8_SFF-8654_74pin_RASide | 74/74 | 74 | 否 | **差异** | pad:sx/sy/dx/dy; pad:sx/sy/dx/dy; pad:sx/sy/dx/dy; pad:sx/sy/dx/dy; pa |
| J3 | ForgeOS:MCIO_4i_SFF-1016_RASide | 38/38 | 0 | - | **名集合差异** | pad_name_set |
| J4 | ForgeOS:MCIO_4i_SFF-1016_RASide | 38/38 | 0 | - | **名集合差异** | pad_name_set |
| R1 | Resistor_SMD:R_0603_1608Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| R21 | Resistor_SMD:R_0603_1608Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| R28 | Resistor_SMD:R_0603_1608Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| R29 | Resistor_SMD:R_0603_1608Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| R3 | Resistor_SMD:R_0603_1608Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| R31 | Resistor_SMD:R_0603_1608Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| R32 | Resistor_SMD:R_0603_1608Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| R33 | Resistor_SMD:R_0603_1608Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| R34 | Resistor_SMD:R_0603_1608Metric | 2/2 | 2 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx |
| U2 | Package_SO:SOIC-8_5.3x5.3mm_P1.27mm | 8/8 | 8 | 否 | **差异** | pad:shape/sx/sy/dx; pad:shape/sx/sy/dx; pad:shape/sx/sy/dx; pad:shape/ |
| U4 | ForgeOS:SOT23_BAT54C | 3/3 | 0 | 是 | **一致** |  |
| U5 | ForgeOS:OPTO_LTV356T | 4/4 | 0 | 是 | **一致** |  |

## 单件明细（电气差异者）

### C73 · `Capacitor_SMD:C_0402_1005Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=-0.45`；库 `shape=4, sx=0.56, sy=0.62, dx=-0.48`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=0.45`；库 `shape=4, sx=0.56, sy=0.62, dx=0.48`

### C74 · `Capacitor_SMD:C_0402_1005Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=-0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=-0.48`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=0.48`

### C75 · `Capacitor_SMD:C_0402_1005Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=-0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=-0.48`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=0.48`

### C76 · `Capacitor_SMD:C_0402_1005Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=-0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=-0.48`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=0.48`

### C77 · `Capacitor_SMD:C_0402_1005Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=-0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=-0.48`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=0.48`

### C78 · `Capacitor_SMD:C_0603_1608Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=-0.45`；库 `shape=4, sx=0.9, sy=0.95, dx=-0.775`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=0.45`；库 `shape=4, sx=0.9, sy=0.95, dx=0.775`

### C79 · `Capacitor_SMD:C_0402_1005Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=-0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=-0.48`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=0.48`

### C80 · `Capacitor_SMD:C_0402_1005Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=-0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=-0.48`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=0.48`

### C81 · `Capacitor_SMD:C_0402_1005Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=-0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=-0.48`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=0.48`

### C82 · `Capacitor_SMD:C_0402_1005Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=-0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=-0.48`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=0.48`

### C83 · `Capacitor_SMD:C_0603_1608Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=-0.45`；库 `shape=4, sx=0.9, sy=0.95, dx=-0.775`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=0.45`；库 `shape=4, sx=0.9, sy=0.95, dx=0.775`

### C84 · `Capacitor_SMD:C_0805_2012Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.8, sy=0.9, dx=-0.6`；库 `shape=4, sx=1.0, sy=1.45, dx=-0.95`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.8, sy=0.9, dx=0.6`；库 `shape=4, sx=1.0, sy=1.45, dx=0.95`

### C85 · `Capacitor_SMD:C_0402_1005Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=-0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=-0.48`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=0.48`

### C86 · `Capacitor_SMD:C_0603_1608Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=-0.45`；库 `shape=4, sx=0.9, sy=0.95, dx=-0.775`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=0.45`；库 `shape=4, sx=0.9, sy=0.95, dx=0.775`

### C87 · `Capacitor_SMD:C_0402_1005Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=-0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=-0.48`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=0.48`

### C88 · `Capacitor_SMD:C_0603_1608Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=-0.45`；库 `shape=4, sx=0.9, sy=0.95, dx=-0.775`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=0.45`；库 `shape=4, sx=0.9, sy=0.95, dx=0.775`

### C89 · `Capacitor_SMD:C_0603_1608Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=-0.45`；库 `shape=4, sx=0.9, sy=0.95, dx=-0.775`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=0.45`；库 `shape=4, sx=0.9, sy=0.95, dx=0.775`

### C90 · `Capacitor_SMD:C_0402_1005Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=-0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=-0.48`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.4, sy=0.5, dx=0.35`；库 `shape=4, sx=0.56, sy=0.62, dx=0.48`

### D1 · `LED_SMD:LED_0603_1608Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=-0.45`；库 `shape=4, sx=0.875, sy=0.95, dx=-0.7875`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=0.45`；库 `shape=4, sx=0.875, sy=0.95, dx=0.7875`

### E2 · `ForgeOS:SOIC8_FRU`

- 板 pads 8 / 库 pads 8；差异 pad = 4；相对几何同 = False
  - pad `5`：差异字段 `dy`；板 `dy=1.905`；库 `dy=-1.905`
  - pad `6`：差异字段 `dy`；板 `dy=0.635`；库 `dy=-0.635`
  - pad `7`：差异字段 `dy`；板 `dy=-0.635`；库 `dy=0.635`
  - pad `8`：差异字段 `dy`；板 `dy=-1.905`；库 `dy=1.905`

### J2 · `ForgeOS:SlimSAS_x8_SFF-8654_74pin_RASide`

- 板 pads 74 / 库 pads 74；差异 pad = 74；相对几何同 = False
  - pad `1`：差异字段 `sx/sy/dx/dy`；板 `sx=1.3, sy=0.35, dx=-1.175, dy=-10.8`；库 `sx=0.35, sy=1.0, dx=-11.4, dy=1.5`
  - pad `10`：差异字段 `sx/sy/dx/dy`；板 `sx=1.3, sy=0.35, dx=1.175, dy=-8.4`；库 `sx=0.35, sy=1.0, dx=-6.0, dy=1.5`
  - pad `11`：差异字段 `sx/sy/dx/dy`；板 `sx=1.3, sy=0.35, dx=-1.175, dy=-7.8`；库 `sx=0.35, sy=1.0, dx=-5.4, dy=1.5`
  - pad `12`：差异字段 `sx/sy/dx/dy`；板 `sx=1.3, sy=0.35, dx=1.175, dy=-7.8`；库 `sx=0.35, sy=1.0, dx=-4.8, dy=1.5`
  - pad `13`：差异字段 `sx/sy/dx/dy`；板 `sx=1.3, sy=0.35, dx=-1.175, dy=-7.2`；库 `sx=0.35, sy=1.0, dx=-4.2, dy=1.5`
  - pad `14`：差异字段 `sx/sy/dx/dy`；板 `sx=1.3, sy=0.35, dx=1.175, dy=-7.2`；库 `sx=0.35, sy=1.0, dx=-3.6, dy=1.5`

### R1 · `Resistor_SMD:R_0603_1608Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=-0.45`；库 `shape=4, sx=0.8, sy=0.95, dx=-0.825`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=0.45`；库 `shape=4, sx=0.8, sy=0.95, dx=0.825`

### R21 · `Resistor_SMD:R_0603_1608Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=-0.45`；库 `shape=4, sx=0.8, sy=0.95, dx=-0.825`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=0.45`；库 `shape=4, sx=0.8, sy=0.95, dx=0.825`

### R28 · `Resistor_SMD:R_0603_1608Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=-0.45`；库 `shape=4, sx=0.8, sy=0.95, dx=-0.825`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=0.45`；库 `shape=4, sx=0.8, sy=0.95, dx=0.825`

### R29 · `Resistor_SMD:R_0603_1608Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=-0.45`；库 `shape=4, sx=0.8, sy=0.95, dx=-0.825`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=0.45`；库 `shape=4, sx=0.8, sy=0.95, dx=0.825`

### R3 · `Resistor_SMD:R_0603_1608Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=-0.45`；库 `shape=4, sx=0.8, sy=0.95, dx=-0.825`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=0.45`；库 `shape=4, sx=0.8, sy=0.95, dx=0.825`

### R31 · `Resistor_SMD:R_0603_1608Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=-0.45`；库 `shape=4, sx=0.8, sy=0.95, dx=-0.825`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=0.45`；库 `shape=4, sx=0.8, sy=0.95, dx=0.825`

### R32 · `Resistor_SMD:R_0603_1608Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=-0.45`；库 `shape=4, sx=0.8, sy=0.95, dx=-0.825`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=0.45`；库 `shape=4, sx=0.8, sy=0.95, dx=0.825`

### R33 · `Resistor_SMD:R_0603_1608Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=-0.45`；库 `shape=4, sx=0.8, sy=0.95, dx=-0.825`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=0.45`；库 `shape=4, sx=0.8, sy=0.95, dx=0.825`

### R34 · `Resistor_SMD:R_0603_1608Metric`

- 板 pads 2 / 库 pads 2；差异 pad = 2；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=-0.45`；库 `shape=4, sx=0.8, sy=0.95, dx=-0.825`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.7, dx=0.45`；库 `shape=4, sx=0.8, sy=0.95, dx=0.825`

### U2 · `Package_SO:SOIC-8_5.3x5.3mm_P1.27mm`

- 板 pads 8 / 库 pads 8；差异 pad = 8；相对几何同 = False
  - pad `1`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.9, dx=-1.95`；库 `shape=4, sx=1.625, sy=0.65, dx=-3.5875`
  - pad `2`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.9, dx=-1.95`；库 `shape=4, sx=1.625, sy=0.65, dx=-3.5875`
  - pad `3`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.9, dx=-1.95`；库 `shape=4, sx=1.625, sy=0.65, dx=-3.5875`
  - pad `4`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.9, dx=-1.95`；库 `shape=4, sx=1.625, sy=0.65, dx=-3.5875`
  - pad `5`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.9, dx=1.95`；库 `shape=4, sx=1.625, sy=0.65, dx=3.5875`
  - pad `6`：差异字段 `shape/sx/sy/dx`；板 `shape=1, sx=0.6, sy=0.9, dx=1.95`；库 `shape=4, sx=1.625, sy=0.65, dx=3.5875`

