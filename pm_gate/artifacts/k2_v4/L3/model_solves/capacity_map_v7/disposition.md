# capacity_map_v7 — 复摆后容量重探 + 剩余 BLOCKED 逐网形态枚举处置

> 日期：2026-08-27 ｜ 输入板：`/tmp/opencode/boards/k2_v6.kicad_pcb`（sha256 `9b6e28c3…5110ff`，
> 电容墙复摆后：DN 墙 C17-C32 双行 y=57.8/68.0 x∈[75.15,84.95]，UP 墙 C49-C64 单行 y=39.4 x∈[99.15,119.35]）
> 上一代证据：`model_solves/capacity_map_v6/`（复摆前，板 fp `aa8b3f07…`）
> 本报告为只读分析：不改 SPEC/alloc/yaml/求解器，不摸 git，不跑 `--all-v4`。

## 0. 执行摘要（一句话）

**复摆后容量重探：跨区 8 网 5 处 BLOCKED（UP5/DN2/UP3/DN4/DN5）全部复现，全量地图另见
J2_region UP7、U7_region UP0/2/3/5——电容复摆未解锁任何一处（探针视野中 HS 电容整体清出，
障碍全为 PDN/连接器脚）。逐网挖真几何后：10 处 BLOCKED 全部同因——**分配轨道的 P/N 线在
走廊口撞连接器 GND 脚列**（U_TO_MCIO 走廊 x=64.9 的 J3/J4 GND 脚；J2_TO_U 走廊 x=132.65 的
J2 GND 脚），而走廊 `x_range` 声明越过了该脚列。内存副本修订 `SPEC corridors.x_range`
（U_TO_MCIO `[64.9,88.83]→[65.5,88.83]`；J2_TO_U `[98.83,132.65]→[98.83,131.5]`）后：
**4 区 6 走廊全量 CAPACITY_OK，跨区 8 网 4/4 OK，10 处 BLOCKED 全解锁，零回归**。
结论 = 全部 INPUT_REVISION（2 行 SPEC diff），无 MODEL_GAP，不触发方案级缺口报告（Task D）。**

## 1. 输入现场与探针口径（同 v6，逐字节）

| 输入 | 路径 | 说明 |
|---|---|---|
| 板 | `/tmp/opencode/boards/k2_v6.kicad_pcb`（fp `9b6e28c3…`） | 101 器件/508 pads；电容已复摆 |
| spec | `pm_gate/artifacts/L3/SPEC_k2_v4.json` | corridors bands 方向分组（未改） |
| alloc | `model_solves/channel_alloc_v4/channel_alloc.json` | 18/18 SOLVED，seg_tracks 段级轨道（未改） |
| rules | `_shared/eda_core/drc_rules.json` | diff_pair p_width 0.205 / p_gap 0.38 / PCIe85 clearance 0.175 |
| pro/config | `k2_v4.kicad_pro` / `L2/route_model_config.json` | hs_prefixes=PCIE/REFCLK；pdn_yield=GND/P3V3/MCU_/VREG/PWR_5V |

探针口径（`hs_route_model.py` L1524-1671 复刻）：`_probe_escape_region_pair` 用
`_escape_pair`（flip=False→True 固定序）枚举形态；障碍场 `build_hs_field(clear_hs_pads=True,
clear_hs_nets=None)` → **全部 HS pads（含复摆后电容）清出**，仅 PDN/低速 pads 为障碍；
走廊段检查 = `(corr_x,ty±0.19)→(bound_x,ty±0.19)` 全段净空。
**关键口径差异**：走廊带探针 `_probe_corridor_capacity` 只要求"存在净空窗口"（滑窗取
entry_x），而逃逸模板 `_escape_pair` 要求**全段净空到 bound_x**——本报告的阻塞全部来自
这个差异（走廊窗口存在但全段不净空）。

## 2. Task A — 复摆后容量地图（v7，与 v6 对照）

### 2.1 跨区 8 网逃逸（`cross_region_8nets_escape_v2.json`）

| 逃逸区 | v6（复摆前） | v7（复摆后） | 变化 |
|---|---|---|---|
| J4→U7 输入 UP4-7 | UP5 BLOCKED（VREG2_U7 0.40/0.2） | **UP5 BLOCKED**（同因） | 无 |
| U3→J3 输出 DN0-3 | DN2 BLOCKED（VREG2_U3 0.35/0.2） | **DN2 BLOCKED**（同因） | 无 |
| J3→U7 输入 UP0-3 | UP3 BLOCKED（GND 0.40/0.175） | **UP3 BLOCKED**（同因） | 无 |
| U3→J4 输出 DN4-7 | DN4/DN5 BLOCKED（GND 0.31/0.072） | **DN4/DN5 BLOCKED**（同因） | 无 |

### 2.2 全量容量地图（`capacity_map.json`，v7）

| 区域 | v6 | v7 |
|---|---|---|
| MCIO_region | 5/8 | **5/8**（DN2/DN4/DN5 BLOCKED） |
| U3_region | 8/8 | 8/8 |
| J2_region | 7/8 | **7/8**（UP7 BLOCKED） |
| U7_region | 4/8 | **4/8**（UP0/UP2/UP3/UP5 BLOCKED） |
| 走廊 J2_TO_U upper/lower | 4/8、3/8 | **4/8、3/8**（42.7/45.1/46.3/48.7；58.3/60.7/61.9/63.1/64.3） |
| 走廊 U_TO_MCIO upper/lower/refclk | 8/8、8/8、2/2 | 8/8、8/8、2/2 |

> **复摆结论**：跨区 5 处 + 全量地图附加 5 处 = **10 处 BLOCKED 与复摆前完全一致**。
> 电容墙复摆（v8 upgrade 目标=给轨道让位）不改变逃逸级容量：探针清出 HS 电容，
> 障碍全部是 PDN/连接器脚，复摆前后位置未变。v6 报告的"共性=芯片电源垫排挤占"
> 在 v7 得到精确化：**电源垫分两类——芯片脚（VREG2/GND/P3V3）在引脚区排内交错，
> 连接器 GND 脚（J2/J3/J4）在走廊口列**；真正的硬阻塞在走廊口（见 §3）。

## 3. Task B — 逐网真几何归因（严禁共性签名，逐网到器件/坐标）

### 3.1 两机制判定框架（先测后判，模型探针为唯一权威）

- **M1 走廊口连接器 GND 脚列拦截**：分配的 track 的 P/N 轨（ty±0.19）在走廊末端
  （U_TO_MCIO 的 bound_x=64.9；J2_TO_U 的 bound_x=132.65）与连接器 GND 脚（尺寸 0.3×0.7
  或 1.3×0.35，整列位于走廊 x_range 端点上）碰撞，净距为负（−0.10〜−0.01）。
- **M2 引脚区电源脚挤占**：DIRECT/via 的 F.Cu 段在 pad 行内与相邻芯片/连接器电源脚
  （0.4mm 脚距，邻脚距本对 0.6mm）净距不足。
- **判定法**：`_direct_escape` 单独取证（探针 fail_forms 只记 via 最终失败，DIRECT 原因
  被覆盖）+ via 候选逐点诊断 + 走廊段暴力扫描最近障碍 + **走廊 x_range 修订对照实验**
  （修订后若解 → 阻塞在走廊口而非 pad 行）。

### 3.2 逐网证据表（障碍身份全部钉到 ref/pin/坐标/尺寸）

| 网/段 | pair_center | track_y | 走廊口障碍（轨净距） | DIRECT 形态 | via 形态 | 修订后 |
|---|---|---|---|---|---|---|
| **UP5** input（U7 RX 列） | (88.825,43.1) | 43.1 | **J3/B1 GND @(64.9,43.25)** sz0.3×0.7：P −0.1025 / N −0.1025 | flip=False 失败（最近 VREG2_U7 pin15 @(88.825,43.7) 0.20/0.2，恰好及格但走廊死）；flip=True 极性不适配 | 100 候选 0 解（via_cc<0.525×56 / fcu_seg_pad_to_via×30-40 / via_point×10 / direction×4） | **DIRECT SOLVED** |
| **DN2** out_MCIO（C21/C22 垫） | (81.7,57.8) | 61.1 | **J4/A19 GND @(64.9,61.45)** sz0.3×0.7：P −0.1025 / N 0.0875 | 双 flip 极性不适配（cap 垫 y=57.8 距轨 3.3mm，竖线必穿对侧轨） | 100/100 候选净空，**唯一失败=走廊段** | **L-H-V SOLVED**（via @(83.13,57.50)） |
| **UP3** input（U7 RX 列） | (88.825,45.5) | 45.5 | **J3/A1 GND @(64.9,45.75)**：P −0.1025 / N −0.0125 | flip=False 失败（最近 GND pin9 @(88.825,46.1) 0.20/0.175）；flip=True 极性不适配 | 100 候选 0 解（同 UP5 模式） | **DIRECT SOLVED** |
| **DN4** out_MCIO（C25/C26 垫） | (76.5,68.0) | 63.5 | **J4/B19 GND @(64.9,63.95)**：P −0.1025（N ok 0.1825 U3/44） | 双 flip 极性不适配 | 100/100 候选净空，唯一失败=走廊段 | **L-H-V SOLVED**（via @(77.48,67.24)） |
| **DN5** out_MCIO（C27/C28 垫） | (79.1,68.0) | 64.7 | **J4/B19 GND @(64.9,63.95)**：N 0.1075<0.175（P ok 0.1825 P3V3 U3/38） | 双 flip 极性不适配 | 100/100 候选净空，唯一失败=走廊段 | **L-H-V SOLVED**（via @(80.10,67.25)） |
| **UP7** out_J2（J2 脚） | (133.825,53.1) | 40.3 | 走廊 rails **OK**（VREG2_U7 pin35 0.1825/0.5625） | 双 flip 极性不适配（J2 脚距轨 12.8mm） | pad→via F.Cu 段穿 J2 GND 脚列（37@(132.65,53.7)/34@(135,52.5)/38@(135,53.7) 包夹） | **SOLVED**（corridor 修订后） |
| **UP0** out_U7（U7 TX 列） | (98.825,48.7) | 48.7 | **J2/19 GND @(132.65,48.3)**：N −0.0675 | flip=False 失败（最近 GND pin53 @(98.825,48.1) 0.20/0.175） | 100 候选 0 解 | **SOLVED** |
| **UP2** out_U7（U7 TX 列） | (98.825,46.3) | 46.3 | **J2/13 GND @(132.65,46.5)**：P −0.1025 / N 0.1125 | flip=False 失败（最近 P3V3 pin50 @(98.825,46.9) 0.20/0.2） | 100 候选 0 解 | **SOLVED** |
| **UP3** out_U7（U7 TX 列） | (98.825,45.1) | 45.1 | **J2/9 GND @(132.65,45.3)** P −0.1025 + **J2/7 GND @(132.65,44.7)** N −0.0675 | flip=False 失败（VREG1 pin47 @(98.825,45.7) 0.20/0.2） | 100 候选 0 解 | **SOLVED** |
| **UP5** out_U7（U7 TX 列） | (98.825,42.7) | 42.7 | **J2/1 GND @(132.65,42.9)**：P −0.1025 / N 0.1125 | flip=False 失败（P3V3 pin38 @(98.825,42.1) 0.20/0.2） | 100 候选 0 解 | **SOLVED** |

> **"0.4脚距 vs 0.38轨距共性签名"证伪**：复摆前 UP4/6/7 与 UP5 同为 0.4mm 脚距、
> 同列同轨距，UP4/6/7 DIRECT 全通而 UP5 阻——脚距不是判据。真因：UP4/6/7 的轨道
> P/N 线（ty=44.3/41.9/40.7）在 x=64.9 处避开 J3 GND 脚列（B1@43.25/A1@45.75 之外的
> 净空带），UP5 的轨道（ty=43.1）恰好压在该列 y 覆盖带内；同样 UP3（45.5）压
> J3/A1@45.75。轨道 y 与连接器 GND 脚列 y 带的**几何重合**才是唯一判据。

## 4. Task B — 形态枚举证据（每候选模型验证，全落盘 `evidence_deepdive.json`）

| 候选形态 | 结果 | 证据 |
|---|---|---|
| flip 双极性（False/True） | flip=True 恒"极性几何不适配"（对中心=轨 → P 竖线必穿 N 轨，几何禁用）；flip=False 是唯一可走极性 | `_direct_escape` 单取（L967-1040 语义） |
| In2 换层（esc_layer In4/In6） | 全部失败，与 In2 同因（障碍在 F.Cu pad 行/走廊口，不在 In2 段） | via_esc_layer 段 |
| 轨道重分配（同 band 8 轨枚举） | DN2/DN4/DN5→58.7/59.9/62.3/65.9/67.1 单侧可解；**双向交换全 NO**（61.1/63.5/64.7/45.5/43.1/48.7/40.3 为死轨，任何对不可用）；UP5-in/UP2-out/UP3-out/UP5-out 0 解 | track_swap + 双向互验 25 组 |
| stagger via（0.4 脚距自动启用，±0.6 侧滑） | 芯片侧 100 候选中 56 个 via_cc<0.525（同侧滑），44 个错开后 via 点/pad→via 段仍撞邻电源脚或走廊死 → 双 via 逃逸不可行 | via_diag 逐候选失败分类 |
| **走廊 x_range 修订（内存副本）** | **全解锁**（见 §5） | revision_verify.json |

## 5. Task C — 结论：全部 INPUT_REVISION（2 行 SPEC diff，模型验证证据）

### 5.1 修订建议（不落盘，等 PM 裁决）

```
文件: pm_gate/artifacts/L3/SPEC_k2_v4.json  →  corridors[]
①  id="U_TO_MCIO"  →  x_range: [64.9, 88.83]  →  [65.5, 88.83]
②  id="J2_TO_U"    →  x_range: [98.83, 132.65] →  [98.83, 131.5]
```

- 数值来源（数据驱动，非拍脑袋）：① x0 需 ≥ J3/J4 GND 脚列右缘 65.05 + 线半宽 0.1025
  + 净距 0.175 = 65.33 → 取 65.5（余量 0.17）；② x1 需 ≤ J2 GND 脚列左缘 132.0 − 0.1025
  − 0.175 = 131.72 → 取 131.5（余量 0.22）。
- 语义：走廊声明跨度越过连接器 GND 脚列（U_TO_MCIO x0=64.9 恰为 J3/J4 末列；
  J2_TO_U x1=132.65 恰为 J2 末列）——`x_range` 是输入缺陷，修订使其与物理净空对齐；
  alloc（只赋 track_y）与 bands/方向分组不变；U3_region/J2_region 逃逸起点（corr_x）
  随修订右/左移 0.6/1.15mm，连接器侧扇出仍由既有机制承接（与 SOLVED 对现状一致）。

### 5.2 模型验证证据（revision_verify.json，内存副本，未落盘）

| 验证项 | 修订前（v7 基线） | 修订后 |
|---|---|---|
| 4 区域 | MCIO 5/8、U3 8/8、J2 7/8、U7 4/8 | **MCIO/U3/J2/U7 全 CAPACITY_OK** |
| 6 走廊 | J2_TO_U up/low INSUFFICIENT | **全 CAPACITY_OK** |
| 跨区 8 网 | UP5/DN2/UP3/DN4/DN5 BLOCKED | **4/4 区全 OK**（UP5/UP3 DIRECT，DN2/DN4/DN5 L-H-V） |
| 无回归 | — | 修订前后 SOLVED 对逐一复验：DN0/1/3/6/7、UP0/1/2/4/6/7 全保持 SOLVED（11/11） |

### 5.3 逐网结论（任务 C 三选一）

| 网 | 结论 | 依据 |
|---|---|---|
| UP5 / DN2 / UP3 / DN4 / DN5（跨区 5 处） | **INPUT_REVISION** | 走廊 x_range 修订后 DIRECT/L-H-V 全解（模型探针） |
| UP7（J2_region）/ UP0/UP2/UP3/UP5（U7_region） | **INPUT_REVISION** | 同因同修（全量地图修订后全绿） |
| 无网需要 MODEL_GAP | — | 现有模板（DIRECT/L-H-V + flip + stagger + In2/4/6）在修订输入下全覆盖；未发现需要新参数化模板的形态 |
| 不触发 Task D 方案级缺口 | — | 全部输入可修，非"无解且非输入可修" |

> ⚠ 遗留提示（非本任务范围，供 PM 知悉）：① 修订后走廊 `[65.5,88.83]` 左端至 J3/J4
> 信号脚（x≤63.1）的 2.4mm 连接扇出不在逃逸模板覆盖内——此与 SOLVED 对现状同级（连接器
> 侧扇出历来由连接器逃逸/后续路由承接），需在 Card 3 步骤 3 求解时核实；② 走廊带探针
> 与逃逸模板的"窗口 vs 全段"口径差异建议后续在模型侧统一（能力改进候选，非本任务处置）。

## 6. 合规声明

- 每输入恰探 1 次；形态枚举 = 不同参数候选（flip/esc_layer/track_y/stagger/bound_x），
  非同参重跑；修订验证 = 内存副本 SPEC（`revision_verify.json` 明示未落盘）。
- 未改 hs_route_model / SPEC / alloc / yaml；未跑 `--all-v4`；未摸 git；未手补走线。
- 归因全部到 ref/pin/坐标/尺寸（§3.2 表），无面状归因。

## 7. 产物清单（model_solves/capacity_map_v7/）

| 文件 | 内容 |
|---|---|
| `capacity_map.json` | 复摆后全量容量地图（fp 9b6e28c3…，4 区 6 走廊） |
| `cross_region_8nets_escape_v2.json` | 跨区 8 网逃逸（UP5/DN2/UP3/DN4/DN5 BLOCKED 复现，fail_forms 齐全） |
| `evidence_deepdive.json` | 逐对深挖：DIRECT 单取证 / via 逐候选诊断 / esc_layer / track 交换 / 障碍身份 |
| `revision_verify.json` | INPUT_REVISION 模型验证（内存副本，4 区 6 走廊全绿 + 求解形态） |
| `disposition.md` | 本文件 |
