# M13 v21 — 引擎资产覆盖审计（G1/G2）+ 规则语义冲突发现

> 状态：**审计工件（非最终裁决）**。本 session 在进入"真实 6L 路由验证"前，
> 按 EXECUTION_GATES G1/G2 盘点引擎（edacore）既有能力与本任务形态的覆盖关系。
> 结论：**走廊/容量/分配层可通用消费；DS320PR1601 球栅逃逸形态未覆盖（模型缺口）**。
> 另发现**规则语义冲突**（inter_pair_spacing），按 GATES §3.5 须先对账。
> 数据源分级：`[L0]` 真板 BoardParser｜`[DS]` datasheet SNLS683 Table 5-1（本 session 逐球解析）｜
> `[E]` edacore 源码/契约｜`[kb]` kb.sqlite3。

---

## 0. 纪律锚（为何先审计，不先写求解器）

- 任务要求"用引擎既有求解验证器（edacore/引擎只读调用，勿改引擎）"。若我自写 ballmap→走廊
  求解器 = 替代工具 = 撞宪法第八章第 1/2 条（禁止用脚本代替规划/模型空转）。
- 故本工件 = G1 真实检索 + G2 覆盖三态，不发明等价结论。

## 1. 引擎既有能力盘点（G1）

引擎有完整高速管道，均通用（`route_model_config.json` + SPEC 注入，代码零板级字面量）：

| 模块 | 职责 | 输入契约 | 本形态可消费? |
|---|---|---|---|
| `route_input.RouteInput/ChannelInput` | 声明式路由输入 | spec.corridors[].bands[].tracks_y[] + pads + config | ✅ 通用 |
| `channel_alloc` | 走廊→通道资源分配 | channels / nets | ✅ 通用 |
| `capacity_audit.CapacityAudit` | 轨道/via/墙 三阶段闭式容量 | AuditInput(corridors/via_zones/demands)+CapacityRules | ✅ 通用 |
| `corridor.CorridorBudgeter` | 物理走廊容量预算 | 走廊几何 | ✅ 通用 |
| `segment_corridor` | 段廊道几何 | corridor_id/band | ✅ 通用 |
| `escape_landing` | 逃逸 via 落点分配 | columns/rows/row_pitch + landing rules | ⚠️ 需 DS320PR1601 球栅几何 |
| `hs_route_model` | 高速路径重建 | RouteInput | 部分 |

**关键**：`capacity_audit` / `channel_alloc` 是纯通用算法（注："纯通用算法，零板级特判，
规则与几何全部由 CapacityRules / AuditInput 注入"）——走廊闭合可被工具验证（前提：喂入
正确的 6L corridor SPEC）。

## 2. 覆盖三态判定（G2）

| 层 | 引擎能力 | 本形态 → 输入缺口 | 覆盖 |
|---|---|---|---|
| **走廊/容量/分配** | ✅ 通用（capacity_audit/channel_alloc） | 现有 SPEC corridors 是旧 8L/38mm/WQFN 拓扑；**6L corridor SPEC 尚未写** | **部分覆盖**：缺的是**设计输入**（规划件，我可产） |
| **逃逸落点/球栅** | `escape_landing` 读 columns/rows/row_pitch | **DS320PR1601 354-BGA 球栅几何资产缺失**（sch_gate 仅 `DS160PR810.yaml`）；datasheet 行距矛盾 | **未覆盖（决定性模型缺口）** |
| kb 模板 | `conn_escape_mcio`=DS160PR810(U3/U7)、`corridor_pair_dual_band`=In6(8L) | 均为旧 redriver/8L 形态 | 仅参考，非直接消费 |

**决定性判据（precheck §6）**：6L 是否会闭合，真正决定项是**逃逸 stub 密度**（75% 球需 via、
球下 0.6 pitch via 落点 与翼带 keepout 冲突时缺 In6 就回 8L）——这正是逃生 `escape_landing`
的球栅逃逸验证，**被本模型缺口挡住**。走廊容量（§2 横截）precheck 已判闭合，非决定性。

## 3. 发现 A — DS320PR1601 球栅几何模型缺口（决定性）

- `escape_landing` 需 columns/rows/row_pitch（球栅几何）。DS320PR1601 该资产**不存在**。
- 我从 datasheet Table 5-1 逐球解析了全 128 信号球 + 354 球，**列带结构确定性确认**：
  - 全 16 lane 逐 lane 一致：**A_PER@col1-2、B_PET@col7-10、A_PET@col26-29、B_PER@col34-35**。
  - 由此 25%（col1/col35 外环 16 球）可 F.Cu 直出、75% 需 via、50%（16 对=32 网）穿越 ——
    由**列位**驱动，与行距无关，**稳健确认**。
- **行距阻塞**：datasheet 行标签 A..FJ（130 个非比例示意图标签）vs 8.9mm 实体矛盾——130 行
  在 0.6 pitch 下需 77.4mm，物理上不可能。**物理球栅行距只能从 TI CAD footprint 才能定**，
  datasheet 无法推导（librarian 外部核实亦确认图纸非比例、内部不一致）。
- **处置**（G2 未覆盖 → STOP + 缺口上报）：模型层需补 `DS320PR1601` 物理球栅资产（TI CAD
  footprint 提取 rows×cols×pitch），`escape_landing` 才能验证决定性逃逸项。**禁止自造行距**。

## 4. 发现 B — 规则语义冲突：inter_pair_spacing（GATES §3.5 先对账）

同一规则多处取值，语义未裁定前不得用其跑工具：

| 来源 | inter_pair_spacing 语义 | 数值 |
|---|---|---|
| drc_rules.json `diff_pair.inter_pair_spacing` + 引擎 `capacity_audit` 注释（L69） | **对间中心距**（轨道 packing min_pitch） | 0.875 |
| precheck §2 / 强条 R3-2（"对间铜边净空 0.875"） | **对间铜边净空**（→中心距 0.585+0.875=1.46） | 0.875(铜边)/1.46(中心) |
| 冻结 L2_STRUCTURE / SPEC_k2_v4 corridors `track_pitch_mm` | 轨道实际中心距 | **1.08** |

- 引擎语义（0.875 中心距）→ 铜隙仅 0.29mm（0.875-0.585），带容量最松；
- 强条语义（0.875 铜边）→ 中心距 1.46mm，带容量最紧；
- 冻结 SPEC 实际轨距 1.08mm，居中。
- **三值差 ~1.67 倍**，直接影响带容量与 via packing。按 EXECUTION_PROCESS §3.5
  （"每条净距/口径必须标来源；0.6 vs 0.38 之类歧义未裁定前不得开跑"）+ GATES G0/G2
  （"检索发现权威文档/既有结论与本会话假设冲突 → 冲突即停机，先对账"），**须先裁定**。
- **对走廊闭合的影响**：两种口径下 8 对带（1.46 口径=10.80mm / 0.875 口径=6.71mm）均
  < N 16.2 / S 20.8 → **走廊闭合结论在两种口径下均成立（robust）**；故该冲突不翻转走廊结论，
  但属**工具规则正确性待确项**（引擎 0.875 中心距若与强条 0.875 铜边矛盾，引擎容量数值需复核）。

## 5. 本 session 可做 & 不可做（诚实边界）

- **可做（合法消费工具）**：设计 6L corridor SPEC（规划件，板级几何+precheck 结构）→ 喂
  `capacity_audit` → 权威走廊闭合。但该结论**非决定性**（走廊已判闭合）。
- **不可做（否决）**：① 自写 ballmap→逃逸求解器（替代工具）；② 自造 DS320PR1601 行距（无据）；
  ③ 在 inter_pair_spacing 三值未裁定前用其跑工具算 knife-edge。
- **决定性项**（逃逸密度）被模型缺口（发现 A）挡住 → per G2，**6L-闭合最终判定无法在本 session
  由工具达成**，其为"工具待补 DS320PR1601 球栅能力"的模型层任务。

## 6. 待用户/架构裁决（按序）

1. **发现 A**：是否取得 TI CAD DS320PR1601 footprint（Ultra Librarian / LCSC EDA / 开源），
   以补模型层球栅资产 → 让 `escape_landing` 验证决定性逃逸项。这是"做发展工具"的正向输入。
2. **发现 B**：inter_pair_spacing 语义裁定（0.875 = 中心距 vs 铜边净空 vs 1.08）——这是
   工具规则正确性 + 后续所有带容量计算的定性依据。
