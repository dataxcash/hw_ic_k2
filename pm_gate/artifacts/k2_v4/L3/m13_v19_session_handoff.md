# M13 v19 续接 — 承接纪律立法 + 学习闸实检 + 布局/器件架构转向（interim，待用户裁决方向）

> **状态**：本 session **未出布局/器件最终裁决**，但完成三件里程碑：
> ① **承接纪律立法落地**（EXECUTION_PROCESS + 物理强制锁，下 session 必须遵守，无法绕过）；
> ② **学习闸实检 kb.sqlite3**（修正"未覆盖"误判 → 命中 K2 自家模板，本任务定位 = 补 known_gap 实证）；
> ③ **问题从"几何求解器死磕"上升为"布局/器件选型架构"**（用户多轮引导结论：单层单走廊建模错误、
>    MCIO 卧式应 X 并排可两面、redriver 单向汇聚必然交叉 → **先器件选型后布局**）。
> **承接必读（按序）**：① `k2/pm_gate/EXECUTION_PROCESS.md`（★ 法，v1.1）+ `EXECUTION_GATES.md`
> ② 本文件 ③ `m13_v18_session_handoff.md`（几何复核权威）④ `m13_v17_session_handoff.md`
> ⑤ `L3/mcio_feas_step2/mcio_learning_gate.md`（学习闸报告，本 session 产物）
> ⑥ `_shared/docs/LAYOUT_CONSTITUTION.md` + `IMPLEMENTATION_LAYER_PHASING.md` + `KNOWLEDGE_REUSE_SDD.md`

## 0. 本 session 已 commit（勿重做；commit 号见 git log）

立法 + 任务资产落盘（引擎/宪法零改动，冻结区只读见 §5）。

## 1. 承接纪律立法（★ 下 session 最高约束）

- `k2/pm_gate/EXECUTION_PROCESS.md` v1.1（法）：执行流程 = 定位闸→学习闸→生产链 8 步(宪法第四章)
  →对抗评审→变更单；8 条禁令；判定场景表；物理强制三件套。
- `k2/pm_gate/EXECUTION_GATES.md`：G0-G5 禁令附录。
- **物理强制（不可绕开，实测）**：冻结区（`_shared/docs`、`_shared/eda_core`、`_shared/knowledge`、
  `L1/L2 frozen`、真板 `k2_v4.kicad_pcb`、PROCESS/GATES）文件 444 + 目录 555，bash/write/edit 全部
  Permission denied。锁管理 `k2/pm_gate/freeze_ctl.sh {lock|unlock|status}`（git 操作前 unlock 后 lock）。
- PreToolUse hook（`~/.opencode/hooks/guard_constitution.py` + `~/.claude/settings.json`）已配置但
  OhMyOpenCode dev 运行时未加载（配置迁移 ~/.omo/omo.jsonc）——第二层，勿依赖。
- pm_gate 状态机登记：`tasks.json` → `mcio_feas`（phase=planned，plan_artifacts 未建前不得 advance）。

## 2. Q2 求解器改造 = 反面教材（已废弃方向，勿重推）

- `mcio_q2_solve.py` v19 改造（簇 x 右推 + 簇 y 下沉采样 + 多布线序）120 布局全败，**暴力迭代违宪**
  （宪法第八章第 8 条）→ STOP。根因：把 16 线锁死在单层 F.Cu 走廊建模本身错误（见 §3/§4）。
- **该求解器与"单层 16 线走廊"建模一并作废**，仅留档教训。勿在其上继续。

## 3. 学习闸实检结论（kb.sqlite3 真实检索，2026-09-04）

- 命中 K2 自家模板：`corridor_pair_dual_band`(produced) + `conn_escape_mcio`(produced)：
  形态 = **F.Cu 数据带 + In2.Cu 受控换层走廊**、dual_band、band_gap≥2.0、8对/带(7.765<8.0)。
  known_gap 原文 = "8 条跨区网络在 U_TO_MCIO MCIO 端逃逸区**垂直爬升容量未实证**" ← 本任务 = 补此实证。
- `cap_wall_ac` **produced=false**（摆位对 alloc 压轨，历史 BOTH_INFEASIBLE 停机）——前置缺口。
- 判定：**部分覆盖**（修正 v1.0 误写的"未覆盖"）。详见 `mcio_learning_gate.md`。
- 真板角色查实：J3(MCIO)=DN0-3、J4(MCIO)=DN4-7、U3(16-lane)=DN redriver 收 DN0-7、U7=UP redriver、
  J2(SlimSAS x133.8)=UP 侧；8 层 F/G/S/G/P/G/S/B；**101 件全单面贴顶**；板框 x∈[23,143] y∈[33,71]。

## 4. 架构转向（用户多轮引导，本 session 最重要结论）

1. **单层单走廊建模错误**：真实 K2 设计（SPEC/模板）本就 F.Cu + In2.Cu 多层、lane 分散，非 16 线挤一走廊。
2. **背面可用（用户裁决）**：贴装无约束，B.Cu 可布局 → 双面贴是合法方向。
3. **MCIO 卧式布局约束（用户裁决）**：两个 MCIO 的 X 不能相同，卧式应 X 方向并排（一左一右），
   可同面或两面；本卡**两个 MCIO 都从板上缘(y=33 侧)出线缆，上部空间留给硬接头**。
4. **两面分置方案（用户拍板方向）**：一面 = MCIO(朝上缘)+电容+redriver；另一面 = MCIO(朝下缘)+电容+redriver；
   两 MCIO 的 X 错开 ~1cm。
5. **redriver 单向汇聚矛盾（用户点破）**：DN 是单向流（MCIO→redriver→下游），16 lane 需汇聚单点
   （现 U3 单 16-lane 芯片），两 MCIO 分散摆放 → 平面 fan-in **必然交叉**，摆位无解。
6. **结论 = 先器件选型后布局**。用户给出三个考虑维度：
   ① RETIMER vs REDRIVER（retimer 可集成 AC 耦合、作有源枢纽）；② 最好选**双向 + 板上 AC 电容需求极少**
   的器件（电容墙死结可能直接消失）；③ 性价比。**此决策归用户/选型，AGENT 不得擅自定型号。**

## 5. 冻结/保护现状（勿违反）

- 冻结只读：宪法文档族、引擎、知识库、L1/L2 frozen、真板、PROCESS/GATES —— 已 chmod 只读。
- 解锁仅 `freeze_ctl.sh unlock`（git 操作/立法修订前），完事必 lock；**AGENT 禁止 chmod 自解**。
- 任务资产可写：`L3/mcio_feas_step2/`、`L3/m13_v19_session_handoff.md`、`tasks.json`。

## 6. 待用户/选型裁决清单（下 session 第一步，逐条等裁决，勿自行推进）

| # | 待裁 | 背景 |
|---|---|---|
| 1 | RETIMER vs REDRIVER | 单向 redriver 汇聚必交叉；retimer 双向+集成 AC 可重构拓扑 |
| 2 | 器件须双向、板上 AC 电容需求极少 | 电容墙（32×0402 密排）是几何死结源头，可能随器件消除 |
| 3 | 性价比/候选型号 | 用户/选型定（如 16-lane 单 vs 8-lane×2 vs 每口独立） |
| 4 | 下游是否必须单口汇聚 16 lane | 决定"单点 fan-in"是否不可避免（影响布局自由度） |
| 5 | PCIe 代次/速率 | redriver 够否/必须 retimer 的判据 |
| 6 | 两面分置布局确认（MCIO 上/下缘+X 错开 1cm） | 用户已倾向，待器件定后落坐标 |

## 7. 下 session 入口（新 PROMPT 由用户提供；AGENT 侧执行纪律）

- 先读 §承接必读（EXECUTION_PROCESS 为法）。
- 等用户/选型对 §6 逐条裁决 → 器件方向定后：
  (a) 若选 retimer 集成 AC（电容墙消失）→ 布局可行性 = "连接器↔retimer↔下游"新拓扑测算，
      不再有 32 电容墙走廊死结；
  (b) 若仍 redriver + 板上电容 → 按 §4.4 两面分置 + 每 MCIO 段独立布局重做空间账（含分层吸收 fan-in）。
- 所有几何用 BoardParser 真板解析（零硬编码）；结论走对抗评审 + 变更单；产出入库 + 回写 kb 学习闭环。
- 禁止：暴力迭代 / 运行时设计决策 / 改引擎与冻结物 / 单层 16 线走廊旧建模复辟。

## 8. G5 收尾自检

- 消费资产：kb.sqlite3（实检 6 模板）、SPEC_k2_v4.json（层叠/走廊/电容墙）、LAYOUT_CONSTITUTION/
  IMPLEMENTATION_LAYER_PHASING/KNOWLEDGE_REUSE_SDD（法）、真板 BoardParser 几何、v17/v18 handoff。
- 未消费/缺口：器件选型数据（待用户）、escape_learner 外部案例（几何前提不同，仅参考）。
- 熔断记录：Q2 求解器 120 布局全败触发 G4（已废弃方向）；hook 运行时未加载（OS 锁兜底）。
