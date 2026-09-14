# K2 channel_alloc_v4 轨道分配容量冲突诊断报告

> 任务卡 1（诊断—测量现状）| 日期 2026-08-30 | 落位板 sha=`6c387dff`
> 方法：**模型 API 只读分析**（`probe_path_clearance` / `nearest_obstacle` / `build_hs_field`），零手算坐标、零代码改动、未动 git
> 输入：落位板 `k2/k2_v4.kicad_pcb` + `SPEC_k2_v4.json` + `channel_alloc_v4/channel_alloc.json` + `drc_rules.json` + `k2_v4.kicad_pro` + `L2/route_model_config.json`
> 证据 JSON：`channel_alloc_capacity_diag.json`（逐条冲突含位置/侵占量/障碍）

## 0. 执行摘要

- **J2 侧逃逸冲突：31/32 条逃逸路径被 J2 pad 堆阻挡**（UP out_J2 16/16、DN input 15/16；仅 DN7 N 1 条净空）
- **走廊轨道行：144/144 线全净空**（18 对 × center/P/N 三线，不撞 pad 堆/电容墙/via）
- **精确侵占量：最近障碍边缘距 -0.075mm，相对 PCIe85 净距 0.175mm → 侵占 0.25mm**（1 档：[0.25]）
- 根因：**① 轨道/逃逸落点策略缺陷（可修）**；走廊带内轨道分配无缺陷，J2 逃逸区非物理极限（列间 1.0mm + 外侧 7.35mm 空间存在）

## 1. WORKER 报告验证（UP1-6 out_J2 vs J2 pad 堆）

**结论：方向正确、范围不全、冲突点定位偏差。**

| 项 | WORKER 报告 | 模型验证（本报告） |
|---|---|---|
| 冲突对 | UP1-6 | **UP0-7 全 8 对**（UP1-6 之外 UP0/UP7 同样被挡） |
| 冲突位置 | "轨行 41.5-47.5 vs pad 堆 42.9-53.1"（y 区间重叠直觉） | 走廊轨行全净空；**冲突在 J2 逃逸段 x∈[131.5,135.65]**（走廊右端→pad 堆） |
| 侵占量 | 未量化 | **最近障碍边缘距 -0.075mm，侵占 0.25mm**（req 0.175 - dist -0.075） |
| 障碍 | J2 pad 堆 | GND 伴行 pad（12 条）/ 邻 lane PCIE pad（3 条）/ REFCLK0_P（1 条） |
| 遗漏 | — | DN input（J2 TX 下半）**15/16 同样被挡** |

## 2. 全量诊断：18 对 × 各段轨道行 vs pad 堆 / 电容墙 / via 阵列

### 2.1 走廊轨道行检查（54 线全净空）

| 段类 | 段 | 走廊 | 轨道 y 带 | 结果 | 最近障碍证据 |
|---|---|---|---|---|---|
| UP input | 8 对 | U_TO_MCIO | 40.7-49.1 | 8/8 ✓ | VREG/P3V3/GND pad d≥0.375（芯片电源 pad，净距足够） |
| UP out_U7 | 8 对 | J2_TO_U | 40.3-48.7 | 8/8 ✓ | GND/P3V3/VREG d≥0.38（电容墙 y=39.4 未挡轨） |
| UP out_J2 | 8 对 | J2_TO_U | 40.3-48.7 | 8/8 ✓ | GND/VREG d≥0.38（走廊带内无 pad 堆） |
| DN input | 8 对 | J2_TO_U | 58.3-66.7 | 8/8 ✓ | VREG/GND d≥0.345 |
| DN out_U3 | 8 对 | U_TO_MCIO | 58.7-67.1 | 8/8 ✓ | VREG/GND d≥0.345 |
| DN out_MCIO | 8 对 | U_TO_MCIO | 58.7-67.1 | 8/8 ✓ | VREG d≥0.345（DN 电容墙双行 y=57.8/68.0 未挡轨） |
| REFCLK | 2 轨 | 两走廊 | 45.7/50.5 | 2/2 ✓ | In6.Cu 无 pad 障碍（走廊层隔离） |

**轨道行结论**：channel_alloc 分配的 18 条走廊轨道（SPEC `tracks_y` 真源）在走廊带内**全部净空**——
不撞 pad 堆、不撞电容墙（UP 墙 y=39.4 / DN 墙 y=57.8/68.0 均在轨带外）、不撞 via 阵列。

### 2.2 J2 逃逸区冲突（32 条路径，31 条 BLOCKED）

**J2 逃逸区几何（模型提取，74 pad 全网格）**：双列 x=132.65/135.0，pad 1.3×0.35；
36 信号 pad（UP RX 上半 y∈[42.9,53.1] + DN TX 下半 y∈[54.3,64.5] + REFCLK y=45.9/51.3）+ 38 非信号 pad
（GND 伴行 34、I2C1_SCL/SDA、PERSTA#/PERSTB#、NO_CONNECT ×2）——**列间无连续空隙，全网格交错填充**。

- UP out_J2（U7→J2，RX 堆 y∈[42.9,53.1]）：**16/16 BLOCKED**，障碍 = GND 伴行 10 / 邻 lane pad / REFCLK0_P
- DN input（J2 TX 堆 y∈[54.3,64.5]→U3）：**15/16 BLOCKED**，障碍 = GND 伴行 / 邻 pad / I2C1_SCL / NO_CONNECT；唯一净空 = **DN7 N → (132.65,64.5)**（列末 pad 下方，GND d=0.35）

| 障碍类型 | 命中数 | 典型障碍 net | edge_dist | 侵占量 |
|---|---|---|---|---|
| GND 伴行 pad（1.3×0.35 同列交错） | 18 | J2 双列间 y 交错 GND | -0.075mm | 0.25mm |
| 邻 lane PCIE pad（同网类） | 13 | PCIE_UP_OUT*_J2 / PCIE_DN* | -0.075mm | 0.25mm |

### 2.3 逐对冲突清单（节选，全量见 JSON）

| net | seg | track_y | P/N | 目标 pad | 障碍 | dist | 侵占 |
|---|---|---|---|---|---|---|---|
| PCIE_DN0 | input | 58.3 | P | PCIE_DN0_P (132.65,54.30) | GND | -0.075 | **0.250** |
| PCIE_DN0 | input | 58.3 | N | PCIE_DN0_N (135.00,54.30) | PCIE_DN1_P | -0.075 | **0.250** |
| PCIE_DN1 | input | 59.5 | P | PCIE_DN1_P (135.00,54.90) | GND | -0.075 | **0.250** |
| PCIE_DN1 | input | 59.5 | N | PCIE_DN1_N (132.65,55.50) | I2C1_SCL | -0.075 | **0.250** |
| PCIE_DN2 | input | 60.7 | P | PCIE_DN2_P (132.65,57.90) | GND | -0.075 | **0.250** |
| PCIE_DN2 | input | 60.7 | N | PCIE_DN2_N (135.00,57.90) | PCIE_DN3_P | -0.075 | **0.250** |
| PCIE_DN3 | input | 61.9 | P | PCIE_DN3_P (135.00,58.50) | GND | -0.075 | **0.250** |
| PCIE_DN3 | input | 61.9 | N | PCIE_DN3_N (132.65,59.10) | PCIE_DN4_P | -0.075 | **0.250** |
| PCIE_DN4 | input | 63.1 | P | PCIE_DN4_P (132.65,59.70) | GND | -0.075 | **0.250** |
| PCIE_DN4 | input | 63.1 | N | PCIE_DN4_N (135.00,59.70) | PCIE_DN5_P | -0.075 | **0.250** |
| PCIE_DN5 | input | 64.3 | P | PCIE_DN5_P (135.00,60.30) | GND | -0.075 | **0.250** |
| PCIE_DN5 | input | 64.3 | N | PCIE_DN5_N (132.65,60.90) | NO_CONNECT | -0.075 | **0.250** |
| … | | | | 共 31 条，全量见 JSON | | | |

## 3. 根因分类

### ① 轨道分配算法缺陷（可修）— **J2 端逃逸落点策略缺口**

`channel_alloc._assign_deterministic` 只按「通道占用 + 相邻轨道 pitch」分配走廊轨道，
**不做 pad/障碍几何校验**（本报告 §2.1 证明走廊带内恰好全净空——当前 SPEC 轨道带与 pad 堆无交集，
故未触发缺陷；但逃逸接入完全未建模）。J2 逃逸路径形态（直线/L 形直插 pad 中心）必穿 pad 堆。

**可修性证据**（capacity_analysis §2.2 模型探针，非本报告新算）：
- 列间空隙 x∈[133.35,134.35]（**1.0mm**）——单线 0.205 + 2×0.175 净距 = 0.555 可容纳
- 外侧空间 x∈[135.65,143]（**7.35mm**）——多线 + via 落点可行
→ 36 信号逃逸 = 落点策略缺口（缺陷 1 修复：via 落点列间空隙/外侧锚定），**非物理不可行**。

### ② 物理极限（需改拓扑）— **本走廊不成立，但存在容量上限边界**

- 走廊带内 18 轨全净空 → 该走廊「塞得下」，**无需改拓扑**
- **边界警示**：J2 全网格（74 pad，列间仅 1.0mm）意味着每空隙仅容 1 线；36 信号需在列间 + 外侧 + 上下侧分摊。
  若双侧分摊后仍不足 → 升级为物理极限（需逃逸拓扑重排，如 J2 外侧双排 via 或 In2 换层），但**当前证据不支持**。

## 4. 结论

1. **WORKER 报告确认**：UP out_J2 与 J2 pad 堆冲突真实存在，精确侵占量 **0.25mm**；但范围应为 **UP0-7 全 8 对 + DN0-7 input 15/16**，冲突点在逃逸段非走廊轨行。
2. **走廊轨道分配健康**：18 对轨道行全净空（含电容墙/via 检查），channel_alloc 带内分配无缺陷。
3. **根因 = ① 逃逸落点策略缺陷（可修）**，非物理极限；修复方向 = J2 逃逸 via 落点列间空隙/外侧策略 + seg_tracks J2 端接入形态。
4. 证据 JSON 与本文同目录落盘，全部判定出自模型 API，可复跑审计。

## 5. 证据索引

- `channel_alloc_capacity_diag.json` — 全量结构化证据（conflicts/track_checks/统计）
- 模型输入：`k2_v4.kicad_pcb`(sha256 前缀 6c387dff) + SPEC + alloc + rules + pro + config
- 探针口径：`probe_path_clearance`（clear_nets=段实际 P/N 网+关联网，PCIe85 0.175）
