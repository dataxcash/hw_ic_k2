# K2 · R432 —— **A 分支求解工作面就绪**（`#K2-146` 教令之作业准备 · 只读/工作面）

- **ts** 2026-09-23T16:56:21 · **from** ENG·ARCHER（续接）· **to** 监理 · **owner 闸口 0**
- **authority**：**#K2-146**（§一~§五）· **#K2-145** 裁定①/指令1（预声明 + 停手维持）· #K2-143 §四 · 宪法第十五条
- **边界**：**未编码真实实例 · 未对真实数据求解 · 未改任何仓内件（除本件）**；依赖装在 `/tmp` venv（依教令 §四）

## 0. 一句话
A 分支工作面**已就绪、证书双形式实测可用**（ortools 9.15.6755 · SAT **7.5ms** / **UNSAT 1.8ms 附机器可核 unsat core**）；且**教令方法并非新造** —— R260 F-3 早已判定『(b) 仅剩**精确计数（MILP/CP-SAT）型** ⇒ 须监理具名方法』，**#K2-146 正是该具名落地**。

## 1. 依赖就绪（教令 §四）
| 项 | 读数 |
|---|---|
| venv | `/tmp/opencode/r432venv`（python 3.10.12） |
| ortools | **9.15.6755** |
| SAT（玩具） | `OPTIMAL` · **7.5 ms** · 模型已导出 `sat_model.textproto` |
| UNSAT（玩具） | `INFEASIBLE` · **1.8 ms** · **unsat core = ['a_z0_eq_z1']** |

⇒ 教令 §四 验收#2『图纸规格 + 求解证书（SAT 模型文件 **或** UNSAT 证明）』之**工具前提已满足**。
> 冒烟仅为**玩具实例**（4 变量）；**未**对真实 16 对建模/求解。

## 2. 方法对齐（教令 §二 = 在册诊断之具名）
> `K2_R260_…CENSUS` §3 **F-3** 原文：『**(b) 仅剩「精确计数（MILP/CP-SAT）型」⇒ 须监理具名方法**（#K2-131 §三(乙)② / #K2-132 §二(乙)①）』

## 3. 编码规格（草案 · 供一次性窗口直接用）
**变量**：['每对：车道槽 s ∈ S（东通道 17 槽）', '每对：层（= In5 单层 · 长走不换层）', '每对：过孔数 k ≤ 2', '次序/嵌套变量：A 排 x 序 ⇄ y 层序（洋葱层 · 承 R260 §六 P-1）']

**约束**：
- ②-UP 两条：①每对 ≤2 过孔 ②长走单层（F→In5→F · 0 换层）
- 束间 pitch ≥ **0.435**（**口径已钉死** · #K2-143 · 只管束间）
- 对内 P/N：冻结 SPEC ≥0.175 + DRC（同 #K2-143）
- 容量：|S| = 17 ≥ 16（东通道可用宽 7.35 ⇒ ⌊7.35/0.435⌋+1 = 17 · R260 F-4）
- 障碍场（**真墙** · 三者合一 ⇒ 强制南→东→北 · 唯一连通口 x≈135.4–142.62）：缝合孔场(x≈82–118 · y≈48–55.5) · `PERSTA#` In5 带(y≈55.15–56.10 · x≈105.6–133.7) · 连接器通孔列(x≈133.2–136.3)
- 端点不动：**端点位移 0**（`no_move` · R331 要件③ / R401 硬条件④）
- ref_plane_continuity：不动平面铜与缝合孔（#K2-136 §二(i) 守恒级）
- 板边：`copper_edge_clearance` 0.300（R260 §六 P-1 明示模型须含）

**目标**：可行即可（可选：最小化总长）—— 教令 §二

**两产物**：['**图纸规格**：每对 → {车道槽, 层, 过孔数}（机器可核 · 施工=连连看）', '**求解证书**：SAT ⇒ 模型 textproto + 指派；UNSAT ⇒ `INFEASIBLE` + **unsat core**（机器可验的守恒级不可行证书）', '（若 UNSAT：证书须基于**真实几何**，**禁**以模型类上界冒充 —— #K2-136 §三 项5(b)）']

**验收口径**（**不新造**）：R401 预登记 `1300a0d7c1cca174` —— 验收口径**不再新造**：R401 预登记（`1300a0d7c1cca174`）PASS = exact_gate 全 16 条 互距0 ∧ 净距0 ∧ 端点0；硬条件含『单层 F→In5→F · ≤2 过孔 · 端点位移 0 · 禁换层/加孔』。

## 4. 数据源（逐件核实 · **原始 sha256**）
| 件 | 路径 | sha256[:16] |
|---|---|---|
| `model_dump_tool` | `k2/tools/k2_p4_b2_board_in5_model_dump_v1.py` | `5f1ce15a33f644fd` |
| `corridor_census_tool` | `k2/tools/k2_p4_b2_in5_corridor_structure_census_v1.py` | `3707b150cf2c97ea` |
| `R260_census` | `/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K2_R260_UP_OUT_IN5_CORRIDOR_STRUCTURE_AND_CAPACITY_CENSUS.json` | `5e5ce7e5f021ab45` |
| `BATCH6_freeband` | `/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/BATCH6_CORRIDOR_FREEBAND_CENSUS_v1.json` | `5303a3aa7cc744d6` |
| `R401_prereg` | `/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K2_R401_V2_CRITERIA_PREREGISTRATION_v1.json` | `1300a0d7c1cca174` |
| `R331_objlist` | `/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K2_R331_CW_RELOCATION_OBJECT_LIST_v1.json` | `89eabed0de4e86b6` |
| `R402_negative` | `/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K2_R402_CONSTRUCTOR_V2_OBSTACLE_AWARE_v1.py` | `7c48c05845edb1a6` |
| `board_l8` | `k2/hw/k2_v4_8L.l8.kicad_pcb` | `7a5c89913d6e5d0a` |

> **口径如实**：本件一律引**原始文件 sha256**（可独立复算）。在册件所标『约定A』sha16（如 R260 标 `35e3b4e7…`、R331 标 `1a51ba6a…`）系另一套约定、与本值不同（**#K2-136 O-1** 已登记不可直采）⇒ 本件不引用。

## 5. 反面教材教训（R402 · 必须避开）
- **反面教材形态**：R402『构造性』实为**一遍贪心投影**（竖直腿遇阻断格 ⇒ 固定半径 1.0mm 内取最近全通列 · 同距取西），**无**枚举/回溯/rip-up ⇒ 结果 **12/16**。
- **R260 F-5 归因**：未布 4 网之失败系**布线序**（先布者占东通道**外槽**、后布者无位）⇒ 缺者 = **nesting-aware（洋葱层）**，**非**空间不足。
- **对 CP-SAT 编码之直接教训**：序/嵌套耦合**必须显式建为全局约束**（禁局部贪心规则）；且**同参重跑 ≥2 = FAIL**（变体重跑 R384/R387/R388 已登记 FAIL 级 · 禁再犯）。

## 6. 一次性窗口执行顺序（**owner 选 A 后**生效）
① 按 **#K2-145 预声明**回退到 l8 干净版（R429 执行单 · 1–5 同笔 + 文字对齐）
② 以**在册普查件**为输入编码（见 `data_sources_verified`；模型 dump 由在册工具从 l8 重生成并记**原始 sha256**）
③ **一次**求解（教令 §四#1：一次成件 · ms 级问题上跑几分钟即违规）
④ 落**两产物**（图纸规格 + 求解证书）
⑤ 按 **R401 预登记口径**验收（`1300a0d7c1cca174` · exact_gate 全 16 条）

## 6b. **`exact_gate` 接口契约**（验收闸之**输入** = 窗口成败关键 · 只读摘录 `k2/tools/k2_p4_b2_in5_lane_router_v3.py` `98ad53eb958d67a5`）
**入口**：`exact_gate(model, routes, anchors, layer, hw, movable_tracks, movable_vias, pitch, movable_copper=frozenset())`（行 265）

| 输入键 | 契约 |
|---|---|
| `model` | In5 模型 dump（`segs`/`pads`/`vias`/`bbox`/`layers`/`design`/`board`）· 由**在册** `k2/tools/k2_p4_b2_board_in5_model_dump_v1.py` 从受审板重生成（确定性） |
| `routes` | **每网一条折线**：`routes[net] = {"pts": [[x,y], …]}` —— **这就是『图纸规格』本身** |
| `anchors` | `lane_anchors(model)`（可经 `--a-sites/--b-sites` 覆盖；端点即由它核） |
| `layer` | `"In5.Cu"`（单层硬条件） |
| `hw` | 半线宽 = `lane_w/2` = 0.16/2 = **0.080** |
| `pitch_eff` | `pitch + margin` = 0.335 + 0.100 = **0.435**（= #K2-143 钉死之束间口径） |
| `movable` | 本窗口 `movable_tracks/vias/copper = 空`（**不动他人铜** ⇒ 障碍场 = 除 16 lane 外全部） |

**闸内口径**：`EFF_MIN = 0.175` · `HOLE_CLR = 0.25`（行 31–32）
**PASS**：`n_lane_pitch_viol==0 ∧ n_clearance_viol==0 ∧ endpoint_max_dev_mm==0`（**全 16 条**）—— 即 R401 预登记 `1300a0d7c1cca174` 之『互距0 ∧ 净距0 ∧ 端点0』
**返回**：`lane_pitch_min_gap_mm` · `lane_pitch_min_pair` · `n_lane_pitch_viol(+violations)` · `clearance_min_mm` · `n_clearance_viol(+violations)` · `endpoint_max_dev_mm` · `per_lane{net:{margin_min_mm,blocker}}` · `n_obs{seg,via,pad}`

**设计含义**：
- **求解器只需产出「每网折线点列」** ⇒ 一次求解之产物**即闸可直接消费之物** ⇒ 施工=连连看（承教令 §二）
- **不需**求解器产出铜/Gerber/层叠 ⇒ 消除『出图后再对不上闸』之返工源
- 障碍场定义 = 模型内 **非 lane 且非 movable** 之 In5 走线 + 过孔 + 焊盘 ⇒ 与 R260 F-2『真墙』一致（缝合孔场 + `PERSTA#` In5 带 + 连接器通孔列）
- **端点**由 `anchors` 之 A/B 位核（`endpoint_max_dev_mm`）⇒ CP-SAT 之端点变量须**逐网钉死**为 anchor 点（承 R401 硬条件④ 端点位移 0）

**⇒ 一次性窗口之含义**：⇒ **一次求解**须直接产出「闸-ready 折线」：模型里把 `pitch_eff=0.435`、`EFF_MIN=0.175`、`HOLE_CLR=0.25`、`hw=0.080`、端点 anchor 一并编码为约束，使 gate 三项**由构造满足**（而非跑完再修）。

## 7. 阶段门
**停手令维持**（#K2-145 指令1）：owner 回件前**禁一切生产动作** ⇒ 本件**不执行** ①–⑤；owner 选 A（维持）⇒ 上表生效；owner 选 B（放宽）⇒ 本件自然失效（#K2-146 首段）。

## 8. 自检
- **未**对真实实例建模/求解 · **未**改任何仓内件（本轮唯一落件 = 本件 + 冒烟副产物）
- 依赖装 `/tmp` venv、未全局安装（教令 §四）
- **未**把『工作面就绪』写成『已求解/已得证』；验收仍用 **R401 在册预登记**、未新造判据、未新增齿

---
—— ENG（ARCHER）· 2026-09-23T16:56 · 工作面就绪（未求解）· owner 闸口 0 · sha16 `297686e6308ae44c`
