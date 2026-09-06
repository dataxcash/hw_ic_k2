# M14 v27 — 层数定案流程终定：v26 对抗评审条件 C1-C5 闭合处置 + 流程状态登记

> 状态：**本 session = 承接 v26 PASS_WITH_CONDITIONS 的条件闭合（TASK MGR 终定流程）**。
> 用户/架构授权两项（2026-09-06）：① L1/L2 frozen 层数表述降级（评审 §0 强制）；② C1 走
> 路径 b（VIA 改判 + In2 stub 容量复核）。本 session 结果：**C1✅ C2✅ C4✅（含 L1/L2 降级）
> + kb 降级✅；C3/C5 机制实证 + 缺口登记（L3 前置）**。6L 判定维持引擎级 FEASIBLE 不变；
> **流程终定状态：C3/C5 未闭 → mcio_feas 维持 planned/S0，不 advance**（不假闭合）。

## 0. 裁决与授权（用户/架构）

- **裁决点1**：授权 L1/L2 frozen 层数表述降级（"6L 正式冻结/已定案" → "引擎级 FEASIBLE
  （per-ball 容量/净空/首发判定，PASS_WITH_CONDITIONS），待 C1-C3-C5 闭合后流程终定"）。
- **裁决点2（C1 路径）**：用户裁决走 **b（改判 VIA+In2 stub 复核，via 预算 64≤69 兜底）**，
  不走 a（L3 dogbone 逐段布线——模型层缺 BGA 阵内 rat-trace 工具，硬走违反禁自写求解器）。

## 1. C2 闭合（引擎修订 ECN，2026-09-06，仅容器根 `_shared/eda_core` 本 2 文件）

> 权威引擎 = 容器根 `_shared`（v26 ECN 所在，commit 5f6af89）；k2 内嵌 `_shared` 为陈旧
> 镜像（无 per-ball 引擎，v24/v26 已声明容器根为权威，未动）。

| 文件 | 改动 | 评审对应 |
|---|---|---|
| `escape_landing.py` `bga_per_ball_escape` | ① 投影分两层：`all_pts`=全 354 球（含 GND/VCC/NC 非信号邻球，净空障碍集）、`pts`=信号球（分类/组带用）；逐球净空测距源 `pts`→`all_pts`。② per_wing 带宽口径 `pair_pitch`(0.6)→`ipair`(1.46)；删除死变量 `pair_pitch`，docstring 键注"兼容保留，口径=inter_pair_spacing" | 评审 §2-B（per_wing 低估 2.4×）/ §2-C（净空漏非信号邻球） |
| `routing_topology_gate.py` | ⑦ `_check_bga_per_ball_escape` docstring 补 C2 口径注记；`plan()` version 1.3→1.4 | ECN 版本追溯 |

**验证（C2 后重跑，禁删可复现）**：`reproduce_per_ball_escape.py` → `per_ball_escape_6L_report.json`
更新：`verdict=FEASIBLE, ok=True, direct=32, via=32, crossing=16, deficits=0`；
**per_wing N/S crossing_need_mm = 11.68 ≤ 16.2/18.8**（旧 4.8 → 修正）；per_ball 全 354 球
净空 `worst min_neighbor = 0.6 ≥ via_min_center 0.427`，全 clearance_ok=True → **FEASIBLE 不变**。
单测：`test_routing_topology_gate.py` + `test_escape_landing.py` **27/27 绿**；全套件 351 绿
（14 failed + 3 collection error 均 pre-existing：pcbnew 环境缺 wx 库 + hs/ls_route_model
真板相关，与 C2 零涉——stash 前后同失败已证）。

## 2. C1 闭合（路径 b：改判 VIA+In2 stub 容量复核，证书求解器）

- 引擎 `VIA_IN2` 语义 = A 带东穿（crossing）；直出球改判属 **west 侧 In2 stub（不穿越）**，
  force 引擎分类会误翻 crossing → 按 G3 边界写**证书求解器**（非引擎、仅几何判定证据）：
  `c1_via_reclass_review.py`（可复跑禁删）→ `c1_via_reclass_report.json`。
- **结果 FEASIBLE_UNCHANGED**：S0 基线 via=32 ≤69；S1（B_PER row1 by57.12 8 球改判）via=40≤69；
  S2（最坏 32 直出全改判）via=64≤69（margin 5）；三场景 crossing=16 对不变（stub 型不东穿）。
  与评审 §1/§2-D 独立复核（64≤69）一致 → **C1 按路径 b 闭合**；B_PER row1 若走 stub 的
  In2 逐段落点登记为 L3 dogbone 级（评审 §4 诚实边界：容量已答，逐段归 L3）。

## 3. C4 闭合（冻结文档修订，unlock→改→lock，freeze_ctl.sh）

- **L2_STRUCTURE_v2.0.md**：① 层数表述降级（状态头/层数定案闸/硬约束引用）；② stale 清理
  ——25/75% 游标口径 → 32/32 真实逃逸法、带结构按 v25 短轴 column-based（A_PER x≈−3.68 →
  B_PER +3.68，各带 32 球=16 对）、走廊/F.Cu 数据带 10.80(1.35 旧轨距) → 11.68(1.46 口径)、
  19mm → 18.8（REFCLK 预留后 S 翼可用）；③ 死指针"§回退 8L" → 新增 **「8L 重入 ECN 触发
  条款」**（三触发条件：dogbone 硬不可路由 + via 预算超支 / In2 stub 实测超载 / SI9000 轨距
  收紧溢出 → ECN 回 L2/L1 重开，禁运行时回退）；④ 版本补记。
- **L1_TOPOLOGY_v2.0.md**：① 层数表述降级（状态头/叠层行）；② 「穿越」语义统一为**板级**
  （A 带 A_PER+A_PET 16 对 In2 东穿），与 die 级端口流（DN/UP 输入侧网）区分、禁混用——
  修正 v26 评审 B 指出的 L1 L42（旧 die 级）vs L11（新板级）并存冲突；③ 版本补记。
- **kb `corridor_pair_ds320pr1601_dual_band`**（knowledge_base.py put-template，v4→v5）：
  `validation.layer_count` "6L 定案" → "6L 引擎级 FEASIBLE（PASS_WITH_CONDITIONS）— 流程终定
  待 C1-C3-C5"；`per_ball_evidence` 更新 C2 口径（11.68/全 354 球净空）；known_gaps 扩 3 项
  （C1 已闭注记 / C3 / C5）。
- 冻结区复锁 **0/0/0**（status 验证）。

## 4. C3 闭合处置（SPEC 再生对齐 = 机制实证 + 缺口登记，⏳ L3 前置）

- **基线复现**：生产 `plan()`（board=/tmp/opencode/boards/k2_v6.kicad_pcb + 生产 SPEC + alloc_v4）
  → ⑥⑦ 均 `not_configured`（ok=True 静默过）= 评审 C 段"生产接线断裂"机器实证。
- **机制实证（POC）**：/tmp SPEC 变体注入 `components.redriver.DS320PR1601.bga_escape.per_ball`
  （真实 354 ballmap + U1@93.8,53.7 + 走廊/翼带/容量）→ 生产 plan() v1.4 真执行 → **⑦ =
  evaluated, verdict=FEASIBLE**（64 球 32/32/16 deficits 0）→ 修复路径机器证明（消除假
  not_configured）。注入样张落 C3_SPEC_REGEN_v27.md。
- **SPEC 本体再生 = 缺口登记**：生产 SPEC（13254 行）与真板 `k2_v4.kicad_pcb` + 全部 sch
  仍为 **U3/U7 WQFN 双芯片旧拓扑**（DS320PR1601 在 sch 0 命中）；DS320PR1601/46mm/6L = L1/L2
  v2.0 冻结规划、原理图 ECO 未落地 → 全面再生 SPEC 会产生描述/网表分裂（假对齐）。**C3 与
  真板 ECO 同批，超出本 session**：登记 L3 前置，未以 POC 冒充再生完成。

## 5. C5 闭合处置（真板网表核对 = 部分可核 + 缺口登记）

- **可核对部分 ✅**：真板 `k2_v4.kicad_pcb`（BoardParser L0，非手抄）J3/J4/J2 pad→net：
  J3=DN_OUT0-3_MCIO+UP0-3+REFCLK0（lanes **0-3**）、J4=DN_OUT4-7+UP4-7+REFCLK1（lanes **4-7**）、
  J2=DN0-7/UP0-7 → **与 L1 frozen（J3 0-3/J4 4-7）一致，映射无差异**，引擎无需重跑 lane 子集。
  记录落 C5_NETLIST_CHECK_v27.md。
- **不可核对 ⏳**：DS320PR1601 ball→ASIC 内部 lane 映射——现行真板无该芯片网表（U3/U7 旧
  布局），登记 L3 前置（与 C3 同根：原理图 ECO 落地后一次核对）。评审已背书引擎对 lane
  子集不敏感，将来若映射微调引擎单次重跑即可（禁暴力）。

## 6. G5 收尾自检

- **消费资产**：REVIEW_ADVERSARIAL_v26（C1-C5 全清单）+ m13_v26 handoff §7；生产
  routing_topology_gate v1.3 基线复现（not_configured 实证）；ds320pr1601_ballmap.json（354 球）；
  c1_via_reclass/reproduce_per_ball 引擎；L1/L2 frozen；kb corridor_pair_ds320pr1601_dual_band
  （v4→v5）；EXECUTION_PROCESS §5 freeze_ctl + EXECUTION_GATES G0-G5；宪法 §8.8（禁暴力/禁
  自写独立求解器→C1-b 走证书复核非引擎重判）；KNOWLEDGE_REUSE_SDD（kb put-template 唯一入口）。
- **未消费/缺口**：C3（SPEC 本体再生）、C5（DS320 芯片级网表核对）= 依赖 DS320PR1601 原理图
  ECO 落地 → 登记 L3 前置，非本 session 假闭合。mcio_feas 维持 planned/S0 不 advance。
- **停止/熔断**：G4 未触发（C1-b 单次确定性复核，无几何卡点空转）；stash 事故（freeze 锁
  444 致 stash push 失败）已即时恢复——工作区 diff 完整、无残留 stash、复锁 0/0/0。
- **禁违反项**：✅ 未翻 6L 判定（C3/C5 未闭不宣布终定）；未以"C1 未闭"反向宣布 8L；未假闭合；
  未 chmod 自解（全走 freeze_ctl unlock→改→lock）；C2 仅改本 2 引擎文件走 ECN；未把"6L 已
  终定"下传 L3。⚠️ 单测 14 failed + 3 collection error 为 pre-existing（pcbnew 环境/真板相关，
  stash 前后同失败），如实记录。
- **边界声明**：本 session 后 6L = **引擎级 FEASIBLE + C1/C2/C4 闭合 + kb/L1/L2 降级一致**；
  流程终定（= mcio_feas advance + kb produced 终态 + 可下传 L3）**仍待 C3/C5**（DS320PR1601
  真板 ECO → SPEC 再生 → ⑦ evaluated + 芯片级网表核对）。

## 7. commit 预备

- `_shared`（容器根 ic_hw_eda，git 前 unlock 后 lock）：escape_landing.py + routing_topology_gate.py
  （C2 ECN v1.4）+ kb.sqlite3（v5）。→ commit 后容器根 bump gitlink。
- `k2`：L1/L2 frozen（C4/降级）+ per_ball_escape_6L_report.json（C2 重跑更新）+
  c1_via_reclass_review.py + c1_via_reclass_report.json（C1-b）+ C3_SPEC_REGEN_v27.md +
  C5_NETLIST_CHECK_v27.md + SPEC_k2_v4_c3poc.json + reproduce_c3_plan_poc.py（C3 POC
  可复跑资产，v27 补记落盘）+ 本文件。→ commit 后容器根 bump gitlink。
- 注意：_shared 内 escape_closure_analysis.py + pipeline/hooks 的 mode-only 漂移（100755→100644）
  为 freeze lock 副作用（444 剥 exec bit），非内容修改，**不纳入本 commit**（避免夹带）。
- 容器根：bump _shared + k2 gitlink。
- 冻结区在 git 前 unlock、后 lock（freeze_ctl.sh status = 0/0/0）。
