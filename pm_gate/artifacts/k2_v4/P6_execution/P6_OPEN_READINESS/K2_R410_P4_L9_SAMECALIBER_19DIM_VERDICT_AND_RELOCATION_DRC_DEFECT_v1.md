# K2 · R410 —— P4 残余（R270 项1/项4/项9）**l9 同口径重跑**：l9 **16 OK / 3 FAIL** · 落搬迁缺陷具名

- **ts** 2026-09-22T22:56+0800 · **from** ENG·ARCHER（续接会话 · context 归零）· **to** 监理 · **owner 闸口 0**
- **authority**：**#K2-142 §四**（准 P4 残余门项之**只读测量**）· R270 §一 项1/项4/项9（『l9 同口径重跑』）· handoff R409 §4/§8.4
- **首动作**：已读 `.omo/supervision/ledger/`（含 `sent/`/`outbox/`）**全部** `K2-RULING-*` ⇒ **最新 = #K2-142 · 无更晚之裁定、无 owner 回件** ⇒ 未越其 §四（禁新法/变体/扫描/派工/烙板），本轮做其**明文允许**之残余门项只读测量。
- **仪器复原（非新法）**：`AppDir/bin/kicad-cli` 10.0.5 + `AppDir/bin/python3.11` pcbnew 10.0.5（历史 l7/l8 在册册即用此仪器）⇒ 补齐 R376 自陈『本机无 pcbnew ⇒ 未做全量 LoadBoard/DRC』之缺口。
- 锚：l9 **`77aaa63fe016b450`** · l8 对照 **`7a5c89913d6e5d0a`** · pro `k2/hw/k2_v4_8L.l8.kicad_pro c009058005829f09`（**如实**：l9 未含同批 pro）· SPEC rev-55 `964101b19015f6d7` · nets errata-3 `5dc7b82a901d11c8` · 判据 **rev=6 MATCH**（独立复算）· 冻结四源 **4/4 未动**

## 0. 一句话
**l9 标准调用 = 16 OK / 3 FAIL**（l8 同仪器 = 19 OK / 0 FAIL）⇒ **当前受审板 l9 未过 P4 标准调用门**；三条 FAIL 全落在 **#K2-137 已准之「项2 落搬迁」新生/改动之铜**（DS320 两条 strap 网 + I2C1_SDA），且 **21/59 处 error 系『落搬迁后未回填铺铜』**。

## 1. 三条 FAIL（具名）
| 维 | l9 | l8 对照 |
|---|---|---|
| `non45_segments` | **FAIL 11/5456** | 0/5180 |
| `drc_errors` | **FAIL error=59**（clearance 21 · shorting 19 · hole_clearance 13 · crossing 6 · 总 233 · unconn 0） | error=0（170 全 warning） |
| `density_and_clearance` | **FAIL 最小铜间距 `None`**（<0.100） | `[0.100, 0.105]` OK |

**OK 14 项**（摘）：`ref_plane_continuity` **non_antipad_gap 0.0 mm²**（= l8）· `drill_count` NPTH=4/PTH=16 · `zone_filled` 10/10 · `pads_within_outline` 0 · `lib_electrical_level` 0 · `unconnected` 0。

## 2. 最小铜间距（item9 核心 · DRC bracket · 同工具 A/B）
| T | l9 | l8 |
|---|---|---|
| 0.100 | **16** | **0** |
| 0.105 | 22 | 6 |
| 0.150 | 37 | 16 |
| 0.200 | 259 | 233 |
| 区间 | `[None, 0.100]` | `[0.100, 0.105]` |

l9 最紧：`ADDR1_7-0(In2)↔GND via` **0.0390mm** · `I2C1_SDA(B.Cu)↔DN_OUT7_P via` **0.0405mm** · `ADDR1_15-8(In2)↔ADDR1_7-0(In2)` **0.0415mm**。

## 3. 铺铜回填归因（/tmp 副本实验 · **未入库**）
`ZONE_FILLER` 回填 18 区 ⇒ error **59 → 38**（clearance 21→14 · hole 13→5 · shorting 19→16 · crossing 6→3）
⇒ **21 处 = 陈旧铺铜假违例**（落地程序未回填）；**38 处 = 真几何冲突**。

## 4. 真冲突三簇（回填后 38 error 之去向）
| # | 对象 | 类型 | 数 |
|---|---|---|---|
| **C1** | `DS320_STRAP_B_ADDR1_7-0`(In2) × `PCIE_UP0_N/1_N/2_P/3_P/4_N/5_N`(In2 走线 + F.Cu→In2 盲孔) + `ADDR1_15-8`(In2) | crossing / shorting / clearance | 20 |
| **C2** | `I2C1_SDA` via(F.Cu–B.Cu) + B.Cu stub × `PCIE_DN_OUT7_P_MCIO`(B.Cu) + U6.`BT29` | shorting / clearance / hole | 5 |
| **C3** | `DS320_STRAP_B_ADDR0_15-8`(F/B.Cu) × `DN_OUT7_N`(B.Cu) · `P3V3` via · `GND` via | clearance / hole | 13 |

**差分 census**（l8→l9）：段 5180→5456（+276：`PERSTA#@In5 59→324` 等）；孔 742→740；非 45° 0→**11**（全在上述两条 strap 网）。

## 5. 人类语义（第十三条）
**「施工队照这张图能不能直接连？」→ 不能。** 3 簇**真短路/交叉** + 21 处**陈旧铺铜**假短路 + 11 段非 45°。⇒ **图纸层缺图，且板层有短路缺陷。**

## 6. 可施工性（⑧）
1. 落搬迁后**必须回填铺铜**（18 区）；2. 改走 `ADDR1_7-0` In2 4 段（避 PCIE_UP In2 束）；3. 移 `I2C1_SDA` via + 改 B.Cu stub（避 DN_OUT7_P / U6.BT29）；4. 移 `ADDR0_15-8` F/B.Cu stub（避 DN_OUT7_N / P3V3 / GND 过孔）；5. 11 段 45° 化。
**审批**：#K2-142 §四 **禁烙板在效** ⇒ 上述修复+重落（新受审板 revision + 同批 SPEC 声明回填）**须监理放行**；受审板锚变更将连带 SPEC rev-55 之 board_sha16 声明 ×3 与 P4 派生模型指纹。**未施工**（仅列清单）。

## 7. 口径缺口（如实）
`C-PRO-L9`：l9 落件未含同批 `.kicad_pro`，本轮以 l8 pro 代跑（搬迁不改规则 ⇒ 规则口径等价；且三 FAIL 皆几何/铺铜，与规则值无关）。建议监理钉死 l9′ 之 pro 口径。

## 8. 件
见同批 `L4/E3-standard-call-l9-20260922/`（MANIFEST + 10 件）。本件 sha16 见 `.sha16.txt`。

---
—— ENG（ARCHER）· 2026-09-22T22:56+0800 · 只读 · 未烙板 · owner 闸口 0
