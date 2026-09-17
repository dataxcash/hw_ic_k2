# K2 · P4 · `drc_warning_disposition`（J-1 后半）**ENG 测量件** · v1 · 2026-09-17

> 性质：**ENG 只提供测量**（计划 §3.2：J 类由监理出判据、ENG 只交测量）。**处置结论（disposition）留空 = 监理填**。
> 本件**不改**任何件；`criteria/` 未动；板 = `k2/hw/k2_v4_8L.l5.kicad_pcb` `d9813bc554a2d611`。
> 口径（T-8）：仓库路径 + 同名 `.kicad_pro` + `fp-lib-table` 同目录。

## 1. 总账

| severity | 类型 | 条数 |
|---|---|---|
| **warning** | `lib_footprint_mismatch` | **35** |
| **warning** | `hole_to_hole` | **1** |
| **合计 warning** | | **36** |
| error | （另计 15 条；全板违规 51） | — |

⇒ **台账 36 条 = 2 组，各绑一条 owner 裁决**：
- **35 条 `lib_footprint_mismatch`** ⇒ 依赖 **O-2**（W-8/J-7：判据容忍 pad 级 or 源侧按库重落）
- **1 条 `hole_to_hole`**（`J12` pad1 `[12V_IN]` ↔ `H3` NPTH，**实际 0.0000mm**）⇒ 依赖 **O-1**（H3 机械输入；孔位移后应消失）

## 2. `lib_footprint_mismatch` 逐条签名（35 条）

| refdes | 库 nickname | 器件位置 (mm) |
|---|---|---|
| `C73` | `Capacitor_SMD` | (28.0,47.9) |
| `C74` | `Capacitor_SMD` | (91.0,40.0) |
| `C75` | `Capacitor_SMD` | (91.0,41.0) |
| `C76` | `Capacitor_SMD` | (91.0,42.0) |
| `C77` | `Capacitor_SMD` | (91.0,43.0) |
| `C78` | `Capacitor_SMD` | (91.0,38.5) |
| `C79` | `Capacitor_SMD` | (91.0,61.0) |
| `C80` | `Capacitor_SMD` | (91.0,59.0) |
| `C81` | `Capacitor_SMD` | (91.0,60.0) |
| `C82` | `Capacitor_SMD` | (91.0,64.0) |
| `C83` | `Capacitor_SMD` | (91.0,62.0) |
| `C84` | `Capacitor_SMD` | (44.0,40.0) |
| `C85` | `Capacitor_SMD` | (29.7,54.5) |
| `C86` | `Capacitor_SMD` | (32.4,36.0) |
| `C87` | `Capacitor_SMD` | (44.0,35.0) |
| `C88` | `Capacitor_SMD` | (29.5,41.5) |
| `C89` | `Capacitor_SMD` | (44.0,37.5) |
| `C90` | `Capacitor_SMD` | (30.0,53.0) |
| `D1` | `LED_SMD` | (48.5,66.5) |
| `E2` | `ForgeOS` | (44.0,60.0) |
| `J2` | `ForgeOS` | (133.825,53.7) |
| `J3` | `ForgeOS` | (59.5,44.5) |
| `J4` | `ForgeOS` | (59.5,62.7) |
| `R1` | `Resistor_SMD` | (50.5,37.0) |
| `R3` | `Resistor_SMD` | (53.5,37.0) |
| `R21` | `Resistor_SMD` | (45.5,66.5) |
| `R28` | `Resistor_SMD` | (50.5,41.0) |
| `R29` | `Resistor_SMD` | (53.5,41.0) |
| `R31` | `Resistor_SMD` | (55.5,66.5) |
| `R32` | `Resistor_SMD` | (55.5,67.5) |
| `R33` | `Resistor_SMD` | (55.5,68.5) |
| `R34` | `Resistor_SMD` | (55.5,69.5) |
| `U2` | `Package_SO` | (33.0,37.0) |
| `U4` | `ForgeOS` | (40.0,37.0) |
| `U5` | `ForgeOS` | (44.5,52.0) |

> 逐条明细（KiCad 原始 description + uuid）见复跑产物 `/tmp/w36.json`（易失）。
> 与 `K2-J7-W8-FOOTPRINT-LIB-AUDIT-v1.md` 的 35 件登记**逐件对应**（W-8 已逐条登记；本表给 DRC 侧签名）。
> ⚠ **覆盖缺口**（提交件 §3.3 / F-1）：本 35 条**只覆盖带库 nickname 的封装**；本板另有 **24 件无 nickname**（`U1 · U6 · J6 · J9..J13 · R35..R45 · D2 · L1 · H1..H4`）KiCad **完全不做库比对** ⇒ 既不出 warning 也不出 error，**不在本台账内**（若采覆盖守卫，需另行裁定）。

## 3. `hole_to_hole` 逐条签名（1 条）

| 对象 A | 对象 B | 约束 | 实测 |
|---|---|---|---|
| `J12` 的 PTH 焊盘 1 `[12V_IN]` @(26.67,35.32) | `H3` 的 NPTH 焊盘 @(26.10,36.10) | ≥ 0.2495mm | **0.0000mm** |

⇒ 与 `drc_errors` 的 H3 组（`hole_clearance 8` · `pth_inside_courtyard 3` · `courtyards_overlap 2` · `solder_mask_bridge 2`）**同源**；解 **O-1**（H3 位移）后应同时消失。

## 4. 复跑命令（确定性）

```bash
cd /home/fila/jqdDev_2025/ic_hw
AppDir/bin/kicad-cli pcb drc --format json --severity-error --severity-warning \
  --output /tmp/w36.json k2/hw/k2_v4_8L.l5.kicad_pcb
python3 -c "
import json
from collections import Counter
d = json.load(open('/tmp/w36.json'))
w = [v for v in d['violations'] if v.get('severity') == 'warning']
print('warning', len(w), Counter(x['type'] for x in w))
for v in w:
    if v['type'] != 'lib_footprint_mismatch':
        print(v['description'], [i['description'] for i in v['items']])
"
#   期望: warning 36 Counter({'lib_footprint_mismatch': 35, 'hole_to_hole': 1})
```

## 5. 监理待填（本件不代填）

- 35 条 `lib_footprint_mismatch` 的 disposition（口径归监理）—— 依 **O-2** 结果；
- 1 条 `hole_to_hole` 的 disposition —— 依 **O-1** 结果；
- 台账最终落 `criteria/manifest.k2.yaml → drc_warning_dispositions`（属主侧版本 bump）。

—— ENG（ARCHER）· 2026-09-17 · 只读测量
