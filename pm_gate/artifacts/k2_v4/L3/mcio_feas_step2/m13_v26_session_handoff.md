# M14 v26 — 层数定案（6L vs 8L）：per-ball 逃逸引擎 FEASIBLE → 6L 正式冻结

> 状态：**本 session = 层数定案（路径 a：补模型层 per-ball 逃逸引擎，ECN）**。承接 v25
> （真实 354 球坐标已解决）+ v22/23（决定性逃逸缺口）。经用户裁决选**路径 a**，走
> EXECUTION_PROCESS §5 unlock→改引擎→lock（仅 `_shared/eda_core` 本 2 文件），新增
> 模型层 **per-ball 逃逸引擎**；以 `ds320pr1601_ballmap.json`（354 真实逐球 + U1@(93.8,53.7)）
> 逐球判定**一次对 → FEASIBLE** → **层数定案 6L（8L 兜底不启用）**，已回写 L1/L2 frozen
> 层数行 + kb `corridor_pair_ds320pr1601_dual_band` produced=true。**逃逸验证（L3 开工前硬门）已过闸。**

## 0. 裁决与路径（用户/架构授权）

- 用户选**路径 a**：补芯片 BGA 逐球逃逸引擎（模型层能力，ECN/unlock-lock），产出决定性
  FEASIBLE/INFEASIBLE；非路径 b（⑥ 拓扑级，仅倾向性、不能当闭合）。
- 理由：⑥（BGA_GROUP_ESCAPE）输出 `level=topology_channel`，docstring 自证靠**声明式
  escape_slots 计数**、非 per-ball 物理可布性；`escape_landing.analyze_pad_heap` 是 J2 连接器
  单侧→板边，非芯片 BGA 逐球。**层数定案闸要求 per-ball 工具级判定**，故须补引擎。

## 1. 引擎改动（ECN，仅本 2 文件，完事 lock；冻结区复锁 0/0/0）

| 文件 | 改动 |
|---|---|
| `_shared/eda_core/escape_landing.py` | 新增模块级 `bga_per_ball_escape(desc)`（确定性逐球判定：投影→分类→逐球净空→组带承载→In2 穿越/REFCLK） |
| `_shared/eda_core/routing_topology_gate.py` | 新增约束⑦ `_check_bga_per_ball_escape`（消费 `bga_escape.per_ball`→调引擎→level=per_ball）+ 接入 `plan()` hard_ok + version 1.2→1.3 |

- **契约（数据驱动零板级字面量）**：`bga_escape.per_ball` = {ballmap, chip_center, axis,
  selected_lanes, inter_pair_spacing, port_to_corridor, corridor_edge, band_corridor_capacity,
  via_zone_capacity, in2_wings, pair_pitch_mm, pad_mm/via_mm/clearance_mm, signal_bands}。
- **合规**：确定性（固定序+显式净空，零搜索零随机），符合宪法 §8.8 禁暴力/指数搜索；
  逐球净空显式验证；输出 `level=per_ball`（诚实边界，非假成功）。

## 2. 测量①（真实球栅几何，v25 资产 + 本 session 补测）

- 结构高度规则：**16 lane 沿长轴 1.2mm 距**、每 lane **0.55mm 宽板片**、4 带（A_PER/B_PET/
  A_PET/B_PER）沿短轴全高 7.88mm；lane 距 1.2mm < 互对距 1.46mm（**需 transition 段 fan-out 扩张**）。
- K2 用 lanes 0-7（L1 冻结 J3 0-3/J4 4-7）：64 信号球，每带 8 对；每带 P/N 沿短轴 0.52~0.69mm 交错。
- **逃逸法分类**（side vs bx 半侧，lanes 0-7 全在西半 bx<93.8）：B_PET/B_PER → 西(MCIO) **F.Cu直出 16 对**；
  A_PER/A_PET → 东(J2) **ball-via→In2 穿越 16 对**（球在西半、需东穿）。直出 32 / via 32，穿越 16 对。

## 3. 引擎判定（per-ball，一次对，禁暴力迭代）→ **FEASIBLE**

`per_ball_escape_6L_report.json`（`reproduce_per_ball_escape.py` 可复跑，禁删）：

```
verdict=FEASIBLE  ok=True  level=per_ball  signal_balls=64  direct=32  via=32  crossing_pairs=16
per_band: 各带 pairs=8  array_lane_pitch=1.2mm ≤ ipair(1.46)  fanout_ok=True
          needed=11.68mm ≤ corridor_width=23.36mm  fit=True
per_wing: N 8对 4.8mm ≤ 16.2mm ; S 8对 4.8mm ≤ (20.8-2.0 REFCLK)=18.8mm  ok=True
clearance: worst min_neighbor=0.6mm ≥ via_min_center=0.427mm
deficits=[] (NONE)
```

**判定通过 → 层数定案 6L（8L 兜底不启用）**。修正 v22 假设（原 25% 直出/75% via 为
v25/v26 真实几何校准为 12% 直出游标 /88% via 计数口径；实际 K2 per-ball 直出/via=32/32）。

## 4. 冻结回写（unlock→写→lock，冻结区复锁 0/0/0）

- `L1_TOPOLOGY_v2.0.md`：层数行「6L 试用+8L 兜底」→「**6L 已定案**（2026-09-05 per-ball
  引擎 FEASIBLE）」；叠层 6L 试用 → 6L 定案（8L 兜底不启用）。
- `L2_STRUCTURE_v2.0.md`：状态头「未定案」→「**已定案 6L**」；层数定案闸改写为「已触发并定案」
  （per-ball FEASIBLE 证据）；逃逸区 known_gap（非工具精确解）→「工具级已闭合」。
- kb `corridor_pair_ds320pr1601_dual_band`：`validation.produced=true`+
  `per_ball_verdict=FEASIBLE`+`layer_count=6L 定案`+`machine_ballmap_public=true`；
  known_gaps 收窄为 2 项次要（lane 行位/去耦清单）。

## 5. G5 收尾自检

- **消费资产**：v25 `ds320pr1601_ballmap.json`（354 球真实坐标）+ `reproduce_ultralibrarian_ballmap.py`；
  L1_TOPOLOGY_v2.0/L2_STRUCTURE_v2.0（层数未定案+走廊表+inter_pair=1.46）；v22 CORRIDOR_CLOSURE
  （走廊/in2 via 容量已工具背书：压 0.64、via 69>32，决定性项只剩逃逸）；v21 REVIEW_ADVERSARIAL
  （预设"未工具验证=FAIL"）；宪法 §8.8/§2 禁暴力迭代 + KNOWLEDGE_REUSE_SDD（kb 模板 produced 网关）；
  ESCAPE_GAP_v22/ESCAPE_ASSET_UNAVAILABLE_v23（资产缺口定位，v25 已解）。
- **未消费/缺口**：⑧-of-16 lane 行位选择采用 lanes 0-7（L1 冻结），ASIC 内部 lane 映射待真板网表
  核对；去耦对象清单（VCC1-4）未细化（→ L3 PDN 项）。`k2/_shared` 内嵌陈旧副本（缺 ⑥/`_track_y_from_alloc`）
  与容器 `_shared` 分歧——本 session 以容器 `_shared` 为权威（v24 定案），若 k2 生产链路实际跑
  k2/_shared 需另行同步（超出本任务边界）。**引擎 per-ball 判定未以 ⑥ 拓扑级越位替代**——⑥ 只作
  拓扑级兜底，per-ball 为唯一定案源。
- **停止/熔断**：G2 未触发（引擎能力已补，接口可消费）；G4 未触发（一次对判定，无几何卡点空转）。
- **禁违反项**：✅ 零违反（未造坐标、未越权改非本 2 引擎文件、未 chmod 自解——走 freeze_ctl.sh
  unlock→改→lock；未宣布 8L；未假成功；逃逸判定走引擎非自写独立求解器）。
- **边界声明**：per-ball 判定为工具级物理几何解（真实球栅驱动），**不是**"6L 施工图已可出"——
  层数定案仅是 L2 层数闸闭合；L3 施工仍须按 L1/L2 冻结包络+SI9000 重算+z 源。

## 6. commit 预备

- `_shared`：escape_landing.py + routing_topology_gate.py（⑦ per-ball，v1.3）+ kb.sqlite3。
- `k2`：L1/L2 frozen 层数行 + `reproduce_per_ball_escape.py` + `per_ball_escape_6L_report.json`
  + `direct_escape_wedge_report.json` + `reproduce_direct_escape_wedge.py` + 本文件。
- 冻结区在 git 前 unlock、后 lock（freeze_ctl.sh）。

## 7. 对抗评审补记（v26 后置，必读——修订本文件 §3/§4 的"干净闭合"表述）

> **6L 判定经非执行者双路对抗评审 = PASS_WITH_CONDITIONS，非干净 PASS**。详见
> `REVIEW_ADVERSARIAL_v26.md`（本目录）。评审过程缺陷如实记录：两路裁定者均耗尽输出预算、
> 未独立交付最终裁决，由执行者补查合成。**承接本任务的下一 session 必须：**
>
> 1. **L1/L2 frozen 层数表述须降级修正**：现文"6L 正式冻结/已定案"（本文件 §4 回写）
>    → "**引擎级 FEASIBLE（per-ball 容量/净空/首发判定），待条件 C1-C3-C5 闭合后流程终定**"；
>    mcio_feas 任务维持 planned/S0 不 advance（本次评审后未推进状态机）。
> 2. **闭合条件 C1-C5**（评审 §3，均不翻转 6L 判定，但为下传 L3 前必修/前置）：
>    - C1 直出球（重点 B_PER row1 by57.12 8 球，仅 4.5~12° 南向楔形）F.Cu 全程穿线 → L3
>      dogbone 逐段验证或改判 VIA+In2 stub 复核（最坏 64≤69 via 预算兜底）；
>    - C2 per_wing 口径修正（pair_pitch 0.6→ipair 1.46 呈现）+ 引擎净空改测全 354 球；
>    - **C3 SPEC_k2_v4.json 再生对齐 DS320PR1601 + 注入 per_ball 描述符 → ⑦ 在生产 plan() 真执行**
>      （现 SPEC 仍 U3/U7 → plan() 得 not_configured，可验证性断裂）；
>    - C4 L2 stale 文本清理（25/75%、col-band 表、19mm）+ 死指针"§回退 8L"修复 + 8L 重入
>      ECN 触发条款 + L1"穿越"die级/板级语义统一；
>    - C5 lanes 0-7 ↔ MCIO/ASIC 真板网表核对（引擎可单次重跑任一 lane 子集）。
> 3. 补查证据可复现：`reproduce_direct_escape_wedge.py` → 32/32 直出球首发楔形可行；
>    B_PER row2(顶行) 107.4° 北向出阵（物理直出 ✓）；B_PER row1 仅南向窄楔 → C1。
> 4. **评审未触发 G4 熔断**（两路裁定者卡点为同一几何点第 3 轮以上，补查为有界确定性检查、
>    non-bruteforce；已按纪律停止、问题回模型登记为 C1）。
> 5. 本轮 commit 仅 k2（评审/补查/本补记）+ 容器 bump；_shared 无新改动（C2 引擎修订未做，
>    留待条件闭合 session 走 ECN）。
