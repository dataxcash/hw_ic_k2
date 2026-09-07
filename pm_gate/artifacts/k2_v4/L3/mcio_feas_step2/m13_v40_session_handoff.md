# M14 v40 承接 — ENG 几何语义统一（capacity 门禁 vs solve 滑动）+ NEW SESSION PROMPT

> 承接 v39。v39 已交付并 commit+push（`ic_hw` a83ab77 → `_shared` 7faef51 D2 fix + 84c8d9d route_input fix）。
> 唯一必读 = 本文件。**产出物 = 整体 EDA TOPO ENG（拓扑引擎），K2 仅作验证项目** ——
> K2 实现过程全部应是 ENG 的结果，不是临时脚本/单板特判。
> 纪律延续：**全前台自跑，禁 task() 委派，禁后台长跑，禁暴力迭代（同参≤2 带依据），禁无依据 --all-v4**。

---

## 0. 一句话状态（ENG 视角）

v39 修正了 **ENG 的 D2 通道分配净空验证语义**（从"全跨度净空"→"可内滑出净空子窗"，对齐 solve 的 L816-853 滑动）。但打通全量 e2e 后暴露**更上游的 ENG 不一致**：`capacity_audit` 的 TRACK 车道有效性仍用**全跨度严格**，导致 `max_flow=0`（36 对需求、0 可用道）→ W6-D1 门禁拒 alloc → 管道全量 **capacity INFEASIBLE，未达 18 SOLVED**。

**这是同一根因（"全跨度 vs 滑动"）在 ENG 内三个阶段的不一致**：capacity_audit 严格 / channel_alloc D2 已滑 / solve 滑动。下一步 = 统一。

---

## 1. 已钉死事实（勿重推）

| # | 事实 | 依据 |
|---|---|---|
| F1 | 权威板 `k2/k2_v4.kicad_pcb` sha=`f6273de6`（rot90，只读） | v39 实测 + F6 |
| F2 | e2e 脚本 `sha_expected=6c387dff` 是**旧板**，已过期（勿用） | v39 实测 |
| F3 | corridor_window_ok 已修 = 内滑（0.3mm 步进，镜像 solve `_pt_ok/_corr_ok`），`segment_x_span` 已修 = config 链模式派生 base 的 OUT 前缀（`PCIE_DN2→PCIE_DN_OUT2`）覆盖 input+output 双走廊 | `_shared` 7faef51 |
| F4 | route_input concat_entries 已加 `isinstance(v, list)` 守卫（防 `extend(dict)` 崩溃） | `_shared` 84c8d9d |
| F5 | D2 语义修正后：**隔离 alloc = 18/0**（真板 f6273de6，每 base 校验 EAST+WEST 双走廊，half_pitch=0.19） | v39 探针 |
| F6 | 单测基线 = 9 failed（7 hs_route_model + 1 routing_topology + 1 solve_pipeline，皆 pre-existing） | /tmp/opencode/baseline_failed.txt |
| F7 | **capacity 门禁 INFEASIBLE/TRACK**：`total_demand_pairs=36`、`max_flow_pairs=0`、`stage_pressures.TRACK=1.0`、`pair_fit=True`(0.38≤0.875) | 现行 e2e 报告 |
| F8 | `capacity_audit._encroached` L310-324：障碍 x 与 band.x_range 重叠 + y 与 `track_y±(w+g)/2` 重叠 → 判"被占"，**无滑动** → `usable=[]` → `capacity=0` | v39 读源码 |

---

## 2. 省 CONTEXT 清单（NEW SESSION 强烈遵守）

**必读（唯一）**：本文件。

**勿读全文 / 勿重做**：
- m13_v10~v39 任一 .md 全文（事实已钉死在 §1，勿重推）。
- D2 根因诊断（已证伪"handoff D2 退化"推论，已修复 commit 7faef51）。勿重跑 alloc 隔离探针（D2 已验证 alloc=18）。
- 板 sha 6c387dff / 走廊名 J2_TO_U,U_TO_MCIO（旧 spec，已过期，勿引用）。
- v33 系列 / tmp 中间产物。

**勿整读源码，只 grep**：
- `capacity_audit.py` → `_encroached` / `_audit_track` / `pair_envelope` / `_capacity_input`（本 session 核心）。
- `segment_corridor.py` → `corridor_window_ok`（已修版，**滑动镜像基准**）。
- `hs_route_model.py` → `_corr_ok` / `_pt_ok` / L816-853（solve 滑动参考）。
- `channel_alloc.py` → `_candidate_window_validation` / `_assign_deterministic`（已修版，勿改）。

**勿加载 / 勿重跑**：`bga_per_ball_escape`（已判 FEASIBLE）；全量 `--all-v4`（仅统一 fix 落地 & 单测零回归后第 1 次）。

**勿新建独立零散脚本**（探针内联 python -c，用后即弃）。

---

## 3. 下一步（ENG 级，唯一主线）

### 目标：统一 ENG 的"车道有效性"语义（全跨度 vs 可滑出窗）
capacity_audit（严格）/ channel_alloc D2（已滑）/ solve（滑）三者不一致 → capacity 门禁 over-conservative 挡停可路由设计。

1. **读 capacity_audit._encroached + _audit_track**：确认其"usable"判定是否仅因目标 pad 列（J2@132.65 / chip@65.05 / x=10 界）被判占（全跨度），而 solve/alloc 内滑可绕（`corridor_window_ok` 已证明：x_hi 132.65→131.5 由 False→True）。
2. **设计语义统一**（二选一，需依据 + 单测零回归）：
   - (A) 让 `_encroached`（或 usable 判定）镜像内滑：车道若存在 P/N 双轨净空子窗则计 usable（与 D2/solve 一致）。
   - (B) 若认定 capacity 门禁应保持"保守 fail-closed"，则按 handoff 停止判据带证据回设计层（加层/放宽净空/减 lane/换器件）——**不暴力续修**。
   - 依据：F7 (max_flow=0) vs F5 (alloc=18)；solve 实滑（DN2@60.7→WEST 61.1 window_ok=True）。
3. **落 fix**：改 capacity_audit（若走 A），保持 ENG 通用（零 K2 坐标字面量，走 config/rules 注入）。
4. **单测**：新增"capacity TRACK 判定与 D2 滑动一致"用例（构造边占轨，断言计入 usable）；既有 9 failed 同集零新增回归核对。
5. **全量 ≤2 次**：统一后第 1 次 → 目标 capacity FEASIBLE + alloc 18 + solve 18 SOLVED + skew<0.15 + P/N≥0.175 + 坐标 JSON 落盘。
6. **合规 ECN-009**：unlock→备份→改→单测零回归→lock→status 0/0/0→commit+push。

### 不再做（已证伪/已闭环）
- corridor_window_ok / segment_x_span / route_input：已修（勿重改）。
- "handoff D2 退化(L142 return True)"假设：已证伪。
- 极性 R3 早期"极性错配"：已证伪。

---

## 4. 停止判据

- 统一 fix 全量第 2 次仍非 18 SOLVED → **立即停**，带"capacity usable 车道净空矩阵（哪些 base 的分道在 capacity 视图被占 + D2/solve 视图可用）"证据回设计层（加层/放宽净空/减 lane/换器件），不续命。
- 单测回归失败 → 回查该步，不带依据不重跑全量。

---

## 5. ENG 资产现状（已 commit+push）

| 资产 | commit | 状态 |
|---|---|---|
| `ic_hw` 容器 | a83ab77 | `_shared` 指针 bump |
| `_shared` D2 段廊道内滑+双走廊 | 7faef51 | 已 push |
| `_shared` route_input concat_entries 防御 | 84c8d9d | 已 push |
| engine 未达成端到端 18 SOLVED | — | capacity 门禁阻塞(§1 F7) |

---

## 6. NEW SESSION PROMPT（可直接粘贴）

---
承接 M14 v40。只读 `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v40_session_handoff.md`（唯一必读）。
**产出物 = 整体 EDA TOPO ENG（拓扑引擎），K2 仅作验证项目**；K2 过程必须是 ENG 结果，非临时脚本/单板特判。

背景：v39 已修 D2 段廊道净空语义（`_shared` 7faef51：corridor_window_ok 内滑 + segment_x_span 双走廊）并打通 route_input（84c8d9d）。隔离 alloc=18/0（真板 f6273de6）。但现行 e2e 全量**capacity 门禁 INFEASIBLE/TRACK**：`total_demand_pairs=36`、`max_flow_pairs=0`、`pair_fit=True(0.38≤0.875)` —— `capacity_audit._encroached` 全跨度把**所有道**判被占（usable=[]→capacity=0），而 solve/D2 内滑可绕（DN2@60.7 全跨度 False/内滑 True）。**根因 = ENG 内"车道有效性"语义不一致**：capacity_audit 严格 / D2 已滑 / solve 滑。

任务（唯一主线）：
1. 只 grep `capacity_audit.py` 的 `_encroached`/`_audit_track`/`pair_envelope`，对照 `segment_corridor.corridor_window_ok`(已修滑动基准) + `hs_route_model` L816-853，确认 capacity usable 判定过严原因。
2. 统一语义（二选一，带依据+单测零回归）：(A) `_encroached`/usable 改内滑（与 D2/solve 一致，ENG 通用零 K2 字面量）；(B) 或按停止判据带证据回设计层（加层/放宽净空/减 lane/换器件），不暴力续修。
3. 落 fix → 单测新增"capacity TRACK 判定与 D2 滑动一致"用例 + 既有 9 failed(baseline) 零新增回归核对。
4. 全量 ≤2 次 → capacity FEASIBLE + alloc 18 + solve 18 SOLVED + skew<0.15 + P/N≥0.175 + 坐标 JSON 落盘。
5. 合规 ECN-009：unlock→备份→改→单测零回归→lock→status 0/0/0→commit+push。

省 CONTEXT：勿读 m13_v10~v39 .md 全文；勿重做 D2 诊断/勿重跑 alloc 隔离探针；勿用旧板 6c387dff/旧走廊 J2_TO_U；勿整读源码（只 grep §2 符号）；勿新建独立零散脚本（探针内联 python -c 用后即弃）；勿重跑 bga_per_ball_escape。

纪律：全前台自跑、禁 task() 委派、禁后台长跑、禁暴力迭代（同参≤2 带依据）、禁 chmod 自解、禁无依据 --all-v4。停止判据：统一 fix 全量第 2 次仍非 18 SOLVED → 立即停带证据回设计层，不续命。每步原始输出贴出不加工。
---
