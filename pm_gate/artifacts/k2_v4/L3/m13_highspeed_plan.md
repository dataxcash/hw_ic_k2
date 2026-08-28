# M13 高速域重建 — 方案级论证报告（第一阶段交付）

> 日期：2026-08-25 · 板：`k2_v4.kicad_pcb`（现状盘点用 m9demo 快照，与 DRC 基线同源）
> 承接：M10（规则库对齐 100%）+ M11（统一障碍场/通道分配）+ M12（drc_locator 反向定位）
> 定位：**方案先于施工**——本报告为 M13 高速域重建的方案级论证（可布性预检 + 规模 + 顺序 + 阻塞点），
> 施工层重建（拉线/落板）在论证通过后另起施工任务，严格走 sregress/sadvance 正规流程。

---

## 0. 一句话结论

高速域 385 条违规的根因 = **高速段 527 段中仅 227 段（43%）在 F.Cu，300 段散落
In2/B.Cu/In6/In4**（宪法"F.Cu 为主"被违反）+ **15/16 差分对等长违规**（skew 目标
<0.15mm，最差 UP4 差 58.4mm——P 段近乎缺失）+ **via 密度 185 个**（芯片区 103 个，
via_clearance 159 条违规的根）。重建 = 18 对差分全量 F.Cu 拉回 + 通道落位 + 等长/过孔受控化。
**硬阻塞 1 个**：REFCLK 2 对无通道声明（channel_alloc INFEASIBLE，M11 已证）→ 需 PM 裁决 SPEC 输入。

---

## 1. 现状盘点（全部带数字证据）

### 1.1 高速域 385 条违规构成（M12 drc_locator，芯片区 U3U7 口径）

| 根因族 | 条数 | 根因（M11/M12 已证语义） |
|---|---|---|
| via_clearance | **159** | 高速过孔 vs 异网元素铜净距不足（via 密度过大，芯片区 103 个） |
| pad_clearance | **78** | U3/U7 焊盘 vs 异网（0.4mm 脚距电容墙逃逸窗口不足） |
| seg_clearance | **70** | 高速段 vs 异网段/zone 净距不足 |
| smd_mask_bridge | **42** | 高速焊盘阻焊桥 <0.05 |
| hole_clearance | **15** | 孔距 0.25 不足（via_via_hole 7 + via_hole 8） |
| seg_crossing | **6** | 段交叉 |
| via_via_layer_dup | 13 | via-via 铜净距（含按层重复行） |
| diff_pair_intra_gap | 1 | PCIE_UP1 对内间距 0.095 < 0.1 |
| via_short | 1 | 过孔接触短路 |

高危（间距<50%）34 条：pad_clearance 13 + seg_clearance 8 + via_via 7 + via_clearance 6。

### 1.2 高速段层分布（527 段，k2_m9demo 快照 = k2_v4 真源一致）

| 层 | 段数 | 占比 | 宪法要求 |
|---|---|---|---|
| **F.Cu** | **227** | **43%** | ✅ 主层 |
| In2.Cu | 173 | 33% | ❌ 需拉回 |
| B.Cu | 88 | 17% | ❌ 需拉回 |
| In6.Cu | 27 | 5% | ❌ 需拉回 |
| In4.Cu | 12 | 2% | ❌ 需拉回 |

芯片区 x∈[60,100]：357 段 = F.Cu 124（**仅 35%**）+ In2 114 + B.Cu 82 + In6 25 + In4 12。

### 1.3 差分对等长现状（`diff_pair_groups`，skew 目标 <0.15mm）

**15/16 对等长违规**：

| 对 | \|P-N\| skew (mm) | 段数 | 严重度 |
|---|---|---|---|
| PCIE_UP4 | **58.380** | 18 | 灾难（P 段仅 0.8mm，N 段 59.18） |
| PCIE_UP5 | **52.281** | 14 | 灾难（P 段仅 2.5mm） |
| PCIE_UP6 | 18.470 | 24 | 严重 |
| PCIE_UP7 | 14.601 | 36 | 严重 |
| PCIE_UP1 | 4.189 | 19 | 重 |
| PCIE_DN1 | 3.268 | 8 | 重 |
| PCIE_DN0 | 2.893 | 8 | 中 |
| PCIE_DN3 | 2.201 | 8 | 中 |
| PCIE_DN2 | 1.819 | 8 | 中 |
| PCIE_REFCLK0 | 1.090 | 7 | 中 |
| PCIE_REFCLK1 | 0.990 | 7 | 中 |
| PCIE_DN5 | 1.040 | 8 | 中 |
| PCIE_DN4 | 0.661 | 8 | 轻 |
| PCIE_DN6 | 0.434 | 8 | 轻 |
| PCIE_DN7 | 0.176 | 8 | 近达标 |
| PCIE_UP0 | 0.131 | 24 | ✅ 唯一达标 |

### 1.4 高速过孔（via 密度）

- 高速网 via 总数：185（芯片区 x∈[60,100] 103 个）
- via_clearance 159 条 = 过孔位置/密度问题
- 宪法：每线 ≤2 受控过孔、对称、GND 伴行、JLC 背钻

---

## 2. 走廊容量论证（通道分配硬约束）

| 走廊 | x 范围 | 通道数 | 需求 | 结论 |
|---|---|---|---|---|
| J2_TO_U | [98.83, 132.65] | 16（upper 8 对 UP + lower 8 对 DN，pitch 1.08mm） | 16 数据对 | **1:1 零余量**（channel_alloc 16/16 SOLVED） |
| U_TO_MCIO | [64.9, 88.83] | 16（同结构） | 16 数据对 | **1:1 零余量** |
| REFCLK | — | **SPEC 无通道声明** | 2 对 | **INFEASIBLE**（M11 已证，16 通道全占用） |

走廊内现状（拉回 F.Cu 的工作量分布）：
- J2_TO_U 区：134 段 = F.Cu 89（66%）+ 非 F.Cu 45
- U_TO_MCIO 区：275 段 = F.Cu 74（**27%**）+ 非 F.Cu 201 ← 主要拉回工作在此

**推论**：数据对通道 1:1 满配（零余量）→ 任何一对的通道变更都会挤压邻对；
重建必须严格按 channel_alloc 通道表落位（16 SOLVED 的 track_y 是唯一合法坐标源）。

---

## 3. 重建方案设计（18 对差分全量）

### 3.1 每对重建路径（三段式）

```
U3/U7 pin（0.45×0.25，脚距 0.4）
  → 逃逸段（F.Cu，逐 Pin 窗口预检，电容墙 x 75-90/93-128）
  → AC 耦合电容（32×C_220N，mcio 侧 C17-C32 / j2 侧 C49-C64）
  → 走廊通道（channel_alloc track_y：J2_TO_U upper 40.92-48.48 / lower 58.92-66.48）
  → 连接器（J3/J4 MCIO @x=59.5 / J2 SlimSAS @x=133.82）
```

### 3.2 重建约束（宪法 + SPEC 真源）

| 约束 | 值 | 来源 |
|---|---|---|
| 层 | F.Cu 为主 + 受控过孔换层（每线 ≤2、对称、GND 伴行、背钻） | AGENTS.md 防线 2 |
| 线宽 | 0.205mm（alt 0.215） | SPEC net_classes.PCIe85 |
| 对内间距 | P/N 边缘净距 ≥0.1（board_min）；中心线 gap 0.175 | M11 diff_pair 语义 |
| 对间间距 | ≥0.875mm | SPEC inter_pair_spacing |
| 等长 | 对内 skew <0.15mm | SPEC intra_pair_skew_mm |
| 阻抗 | 85Ω ±10%（JLC_SI9000 叠层模型） | SPEC impedance |
| 逃逸 | 近距去耦短线（0.37-0.97mm）可手工补；跨墙长链须逐 Pin 可布窗口预检 | AGENTS.md 修正条款 3 |

### 3.3 重建顺序（先难后易，skew 最重先）

| Phase | 对 | 理由 |
|---|---|---|
| 1 | UP4 / UP5 | skew 52-58mm，P 段近乎缺失 → 结构性重建 |
| 2 | UP1 / UP6 / UP7 | skew 14-18mm |
| 3 | DN0-7 | skew 0.2-3.3mm（相对轻，8 段/对） |
| 4 | REFCLK0/1 | 需通道裁决（硬阻塞） |

---

## 4. 硬阻塞与裁决请求（修订走输入，禁止硬编码）

1. **REFCLK 通道缺口**（阻塞 Phase 4 + 全量归零）：
   channel_alloc 已输出 16 通道全占用证据（16 SOLVED + REFCLK0/1 INFEASIBLE，
   `artifacts/L3/model_solves/channel_alloc/`）。REFCLK 2 对需 SPEC corridors 增补
   通道声明（或裁决走非走廊路径）。**待 PM 裁决 SPEC 输入**。

2. **S2 锁定段重建授权**：高速域重建触碰 S2 已锁定段（226/226 locked，锁定≠合规）。
   需走 `sregress S2` → 重建 → `sadvance S2` 正规流程。**待 PM 确认启动**。

3. **逐 Pin 可布窗口预检**（Phase 1 前置）：UP4/UP5 P 段缺失的根因是 U3/U7 引脚
   逃逸被电容墙（x 75-90/93-128）阻断。需逐 Pin 预检 F.Cu 可布窗口——若物理容量
   不足（0.4mm 脚距 + 0.5mm 焊盘行距仅剩 0.12mm 窗口），按 AGENTS.md 修正条款 3
   出论证报告上报，不硬凑。

---

## 5. 工具链就绪度（M13 施工前置条件全具备）

| 能力 | 模块 | 状态 |
|---|---|---|
| F.Cu 视角障碍场 | `unified_field.build_field_from_board(layer="F.Cu")` | ✅ 层参数化 |
| 差分对语义（对内/对间/等长） | `unified_field` RULE_DIFF + `diff_pair_groups` | ✅ |
| 通道分配 | `channel_alloc`（16 SOLVED + REFCLK 证据） | ✅ |
| 逐条定位证据 | `drc_locator` report.json（元素 uuid/坐标） | ✅ M12 |
| 等长检查 | `diff_pair_groups`（skew 报告） | ✅ |
| 合法性门禁 | `model_gate`（solve_ref 强制） | ✅ M4-M5 |
| 状态机 | `pm_gate/cli.py sregress/sadvance` | ✅ |

---

## 6. 验收标尺（M13 计划定义）

- 高速域方案 100% 模型来源（每条设计段带 solve_ref + input_fp）
- 重建后高速域 385 条 → 目标 0（或带证明残余：物理容量极限时出论证报告上报）
- 电源地 266 条 → 0（M13 第二阶段，S3 PDN 铺铜）

---

## 7. 铁律遵守

- **方案即模型输出**：本论证全部基于模型输出（channel_alloc 通道表 / diff_pair_groups
  等长 / drc_locator 定位）；施工段将由模型求解产生，带 solve_ref
- **DRC 只核对不驱动**：本报告是分析，0 改走线
- **结论带证明**：全部数字来自模型工具输出，可复现
- **修订走输入**：REFCLK 缺口 → 裁决请求（未硬编码）
- **不预先拍板**：重建范围由 Phase 论证（逐 Pin 预检）判定后确认
