# K2 · P4 · **缺陷登记：C86 ⊂ U2 机械碰撞（P4 期间新引入）+ courtyard 曲线口径缺陷** · 2026-09-18

> 性质：**只读取证 + 缺陷登记**（本件**未改任何件**：板 / pro / SPEC / `criteria` 逐字节未动）。
> 计量口径：`pcbnew` 封装 padCu 包络（焊盘铜的 AABB）+ 落位解 `selfcheck` 字段 + 冻结判定器。
> 结论：**P4 存在 1 项硬阻断（机械碰撞）**，非「口径」可消；须先清，否则「可制造」不成立（owner ③）。

## 0. 一句话

P4 板（l5）上 **C86（C_0603）整体落在 U2（`SOIC-8_5.3x5.3mm_P1.27mm`）封装本体之内**，
两封装焊盘并不同位但**本体相撞** ⇒ 该 0603 无法装配。设计源板与**冻结交付板 `l4` 均无此问题**
（系统性扫描 0 命中）⇒ **P4 施工期间新引入**，且因 40 件缺 F.CrtYd（`courtyards_overlap` 无法触发）而长期不可见。

**重现**（只读；不改板）：
```bash
AppDir/usr/bin/python3.11 k2/tools/k2_p4_defect_scan_v1.py nested --board k2/hw/k2_v4_8L.l5.kicad_pcb
# => {"nested_hits": 1, "hits": [{"inner":"C86", ..., "outer":"U2", "outer_lib":"SOIC-8_5.3x5.3mm_P1.27mm"}]}
AppDir/usr/bin/python3.11 k2/tools/k2_p4_defect_scan_v1.py courtyard --board <板> --pro <同名 pro> \
  --kicad-cli AppDir/bin/kicad-cli --work-dir /tmp/opencode/scan   # => 按面曲线（§2 表右行）
```
工具：`k2/tools/k2_p4_defect_scan_v1.py` sha256 前16 **`2eef5647d8fdecd9`**。

## 1. D-1：C86 ⊂ U2（实测）

| 项 | 值 |
|---|---|
| `C86` padCu 包络 | x[31.650, 33.150] y[35.650, 36.350]（`C_0603_1608Metric`，2 pad） |
| `U2` padCu 包络 | x[30.750, 35.250] y[34.645, 39.355]（`SOIC-8_5.3x5.3mm_P1.27mm`，8 pad，双排） |
| 关系 | **C86 包络 ⊂ U2 包络（四边严格内含）** |
| U2↔C86 最近 pad 中心距 | **0.971 mm**（pad 净距通过 ⇒ 只看焊盘查不出） |
| 物理含义 | U2 为双排 8 脚，**两排焊盘之间即本体**；C86 位于该区间 ⇒ 实体相撞 |

### 1.1 系统性扫描（判据：某封装 padCu 包络 ⊂ 另一封装 padCu 包络，且外层 ≥4 pad）

| 板 | 命中 |
|---|---|
| 设计源板 `k2/hw/k2_v4_8L.kicad_pcb` | **0** |
| 冻结交付板 `k2/hw/k2_v4_8L.l4.kicad_pcb`（`d4e81f647be7f980`） | **0** |
| **P4 板 `k2/hw/k2_v4_8L.l5.kicad_pcb`**（`37019705ef994ccc`） | **1：`C86` ⊂ `U2`** |

⇒ **P4 期间新引入**（设计源板/`l4` 上 C86 = (31.05,56.0)，距 U2 17.1 mm）。

### 1.2 来源与根因

- **落位解**：`k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_placement_solution.json`
  `C86 = {at:[32.4,36.0], rot:0, footprint:"C_0402_1005Metric", old_at:[31.05,56.0],
  basis:"L2-3 已裁须移位（排针列 column_x 26.5→27.94）；L2 自裁新坐标：左带内就近原位、避既有 pad"}`；
  `solved_count=15 / all_pass=true`。
- **落板**：P4 增量 2（板 `1b8400a255fe90fd`），SPEC **rev-27** 留痕块明写「13 补件落板 + **C73/C86 移位** + 逐 pad 赋网」；
  ledger 记落点 `C86 (32.4,36.0)`（与板上 pad 中点一致）。
- **根因（口径缺口）**：该落位解的约束集 = `{inset_mm:0.3, pad_clearance_mm:0.2, part_spacing_mm:0.5, hole_keepout_dia_mm:6.0}`，
  `selfcheck` 只检 `in_frame / pad_clearance_violations / part_spacing_violations / hole_ko_violations / decap_ko_violations`
  —— **未把「与既有封装本体/外框重叠」列为障碍**。C86 与 U2 **焊盘**相距 0.971 mm（pad_clearance 0.2 通过），
  而**本体**落在 U2 双排焊盘之间 ⇒ 自检「全过」仍产生实体碰撞。
- **与自身 basis 冲突**：basis 写「**左带内就近原位**」（原位 (31.05,56.0)），而实际落点 (32.4,36.0) **距原位 20.0 mm**。
- **与 canonical SPEC 冲突**：SPEC `pd` 声明 `C86.1 MCU_VDD pad_pos [31.05,56.0] / via_pos [30.275,56.0]`、
  `C86.2 GND pad_pos [31.95,56.0] / via_pos [32.725,56.0]` ⇒ **板上位置与 SPEC 声明不一致**；
  原位还残留孤立铜段（`F.Cu MCU_VDD (31.050,56.000)→(30.987,56.063)` 等）。
- **不可见性**：40 件缺 F.CrtYd ⇒ `courtyards_overlap` 无法触发；且该规则**不在** 9 条 `ignore` 登记内（无人盯）。

## 2. D-2：`missing_courtyard` 曲线的口径缺陷（连带修正）

现曲线工具（`k2_p4_courtyard_margin_sweep_v1.py`）对**所有**缺 courtyard 的封装一律补 **`F.CrtYd`**，
但其中 **5 件在背面**（`J13/J9/J6/J11/J12`）⇒ 产生**幻影重叠**（背面件被当作正面件比对）。按面补 courtyard 后实测：

| margin (mm) | 0.00 | 0.05 | 0.10 | 0.15 | 0.20 | **0.25(KLC)** | 0.30 |
|---|---|---|---|---|---|---|---|
| 原曲线 overlap(error) | 4 | 5 | 6 | 8 | 11 | **15** | 23 |
| **按面修正后** | **3** | **4** | **5** | **5** | **8** | **10** | **18** |

`missing_courtyard` 两者在全部档位均 = **0**。⇒ T-39「`missing_courtyard=0` 与 `courtyards_overlap=0` 联合不可满足」
**在修正口径下仍成立**（最小 3），但**原曲线的条数偏高**，须以修正曲线为准。
m=0 的 3 对：`U4↔D2`（重叠 2.55×0.70 mm）· `D2↔U2`（0.10×1.755 mm）· **`C86↔U2`（1.55×0.75 mm = 本节 D-1）**。

## 3. 修复方案（L2，ENG 自裁域内可做；本件未执行）

按「原落位解约束 + **既有封装本体不重叠**」重解 C86 落点，实测**可行**（free-space 网格 0.1 mm；
障碍 = 全部既有封装非文字 bbox + pad 净距 0.2 + 件间距 0.5 + 孔禁布 φ6 + 板框内缩 0.3）：

| 候选 | 距原位 | 备注 |
|---|---|---|
| **(31.55, 58.85)** | **2.89 mm** | 首选：最贴近 basis「左带内就近原位」 |
| (30.05, 59.05) | 3.21 mm | |
| (28.55, 58.45) | 3.50 mm | |

配套（与本阶段既有增量同法）：
① 移 `C86` → 选定落点（rot 0）；
② 为 2 pad 各加 **1 支 F.Cu→In6 通孔**（0.35 盘 / 0.2 孔，板内既有 308 支同类；`MCU_VDD` 平面在 In4、`GND` 平面在 In1/In3/In6）；
③ 各加 1 段 **0/45/90° 引线**（宽 0.20，≥0.05 mm）接 pad→孔；
④ 清理 `C86` **现位** 3 段孤立走线（否则移件后转 `track_dangling`）；
⑤ 复算：`pcbmon` 嵌套扫描须为 **0**、error 0、`unconnected` 0、5 类残项不回退、判定器 FAIL 集不变；两次复跑逐字节同。

## 4. 对 P4 状态的影响

**P4 仍未全绿**，且关键路径除既有 4 项口径裁定外，**新增 1 项硬阻断（D-1）**：
在 D-1 清除之前，板**不具备可制造性**（owner ③「完工=可制造 Gerber」），fail-closed 不变。

—— ENG（ARCHER）· 2026-09-18 · 只读取证（板 `37019705ef994ccc` / SPEC rev-46 `dea36093ba2b4031` **未动**）· 未派 WORKER
