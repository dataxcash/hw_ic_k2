# M14 v38 分支状态总结 + NEW SESSION PROMPT

> 本文件 = v38 session 全部结论 + 下一步（v39）启动 PROMPT。
> v38 已达成：G4 容量判定（可解）+ 16 对失败根因实测（P/N 极性错配）+ 实施计划（极性不变式）。
> v39 = 执行极性不变式方案（拓扑层建立 + 轨道/flip 派生 + 全量 ≤2 次 + 合规）。

---

## A. 分支状态快照（v38 结束）

| 项 | 值 | 依据 |
|---|---|---|
| 权威板 | `k2/k2_v4.kicad_pcb` sha `f6273de6`（rot90，只读） | F6 / v36 §9 |
| 引擎源 | **容器根** `_shared/eda_core/`（非 k2 内嵌陈旧副本） | p3 头注释 |
| 引擎整体 | `SolvePipeline`（①routing_topology_gate ②capacity_audit ③channel_alloc ④escape_landing ⑤hs_route_model） | solve_pipeline.py |
| G4 容量门 | **FEASIBLE（可解）** deficits=[] | `bga_per_ball_escape` 跑 K2 |
| 16 对失败根因 | **P/N 极性错配**（min 边缘距 -0.2050 < 0.175） | v33g summary（板 f6273de6） |
| 冻结 | 0/0/0（全锁） | freeze_ctl status |
| 单测基线 | 43 passed / 7 failed 既有同集 | handoff §5（v33+ 实测） |
| ECN | ECN-008 open / ECN-009 open（均影响 G4） | state_k2_v4.json |

### 关键已钉死事实（勿重推）
- **F1**（逃逸密度 0.100<0.450 → 必走内层 gutter）；**F4**（每段孤立单跑全 SOLVED=画法够）；**F5**（col_stack 方向分层 In1西/In2东）；**F6**（板 f6273de6）。
- **R3**（失败=极性错配，非容量/列槽）；**R4**（芯片侧 A_PER = N上P下）；**R5**（轨道 `_expand_pair` 写死 P上N下）；**R6**（连接器侧 `_check_pn_polarity` 只测 x 侧）。

---

## B. 勿加载清单（省 CONTEXT，v39 强烈遵守）

**必读（唯一）**：`m13_v38_plan_polarity_invariant.md` + `m13_v38_capacity_gate_record.md` §6-§7（根因+结论）。
**勿读全文**：`m13_v10`~`m13_v36` 任一 handoff；v33 系列 /tmp 中间产物（只引用 v33g summary 已提取的 R3 结论）。
**勿整读源码**，只 grep：
- `routing_topology_gate.py` → `_check_pn_polarity` / `plan` / `track_resources`
- `hs_route_model.py` → `_expand_pair` / `_track_y_for` / `_escape_pair` / `_col_stack_escape` / `solve_all_v4`
- `solve_pipeline.py` → `run_feasibility` / `run_solve` / `_capacity_gate` / `FeasibilityVerdict`
- `channel_alloc.py` → `_assign_deterministic` / `alloc_channels_from_input`
**勿重读**：SNLU300/ds320 文本、page-*.png、ds_ball*/ds_lay*、各种 .md 背景记录。
**勿重跑**：`bga_per_ball_escape`（已判 FEASIBLE）；`--all-v4`（仅 Step1-4 落地后第 1 次）。

---

## C. 下一步（v39）执行清单（按 plan 顺序，前台自跑）

- [ ] **Step1** 拓扑层 `routing_topology_gate.py`：扩展 `_check_pn_polarity`，建立每 base 全链极性不变式（芯片侧 chip_landing+ballmap + 连接器侧 + 轨道极性），输出 `polarity_invariant` 进 `FeasibilityVerdict.evidence`。
- [ ] **Step2** `hs_route_model.py` `_expand_pair`/`_track_y_for`：track_y 由极性派生（不写死 P 上 N 下）。
- [ ] **Step3** `_escape_pair`/`_col_stack_escape`：flip 由极性派生（不再 flip 靠碰，无相向交叉）。
- [ ] **Step4** `solve_pipeline.py`：极性不变式 ①→⑤ 传递进 HSRouteModel。
- [ ] **Step5** 全量 `run_all` 第 1 次（≤2 次）→ 18 对 SOLVED + skew<0.15 + P/N 净空≥0.175 + 坐标 JSON。
- [ ] **Step6** 合规 ECN-009：unlock→备份→改→单测 43 passed 零回归(7 failed 既有同集)→lock→status 0/0/0 → 归档裁决。

**停止判据**：Step5 第 2 次仍非 18 SOLVED → 立即停，带极性不变式诊断（哪些 base 三端矛盾）+ 证据回设计层，不续命。

---

## D. NEW SESSION PROMPT（可直接粘贴）

---
承接 M14 v38。只读 `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v38_plan_polarity_invariant.md`（唯一必读=细化实施计划）+
`m13_v38_capacity_gate_record.md`（§6-§7 根因+结论）。勿读 m13_v10~v36 全文、勿整读 hs_route_model/routing_topology_gate/solve_pipeline（只 grep 计划 §6 列的符号）。

背景：G4 容量门已由引擎 `bga_per_ball_escape` 判 **FEASIBLE（可解）**；16 对失败真根因 = **P/N 极性错配**（v33g 实测 min 边缘距 -0.2050 < 0.175，非容量/列槽）。
产出物 = 整体 EDA TOPO ENG（`SolvePipeline`），K2 是验证项目；你是在**引擎拓扑层**修极性，不是写旁路脚本。

主任务：按计划 Step1→Step6 前台自跑推进——①拓扑层 `routing_topology_gate._check_pn_polarity` 建**每 base 全链一致极性不变式**（芯片侧 chip_landing_v33+ballmap 的 P/N 位序 + 连接器侧 + 轨道极性），输出 `polarity_invariant` 进 `FeasibilityVerdict.evidence`；
②`hs_route_model._expand_pair`/`_track_y_for` 的 track_y 由极性派生（不再写死 P 上 N 下）；
③`_escape_pair`/`_col_stack_escape` 的 flip 由极性派生（不再 flip 靠碰、无相向交叉）；
④`solve_pipeline.run_solve` 传递极性不变式①→⑤；
⑤全量 `run_all` ≤2 次 → 18 对 SOLVED + skew<0.15 + P/N 净空≥0.175 + 坐标 JSON 落盘；
⑥合规 ECN-009：unlock(`freeze_ctl.sh unlock`)→备份→改→单测 43 passed 零回归(7 failed 既有同集)→lock→status 0/0/0。

纪律：**全前台自跑，禁 task() 委派，禁后台长跑，禁暴力迭代（同参≤2 带依据），禁 chmod，禁无依据 --all-v4**。
停止判据：Step5 第 2 次仍非 18 SOLVED → 立即停，带极性不变式诊断（哪些 base 三端冲突）+ 证据回设计层（加层/放宽净空/减 lane/换器件），不续命。每步原始输出贴出不加工。
---

## E. v38 已清理
- 删除方向错误零散脚本 `cap_model_v38.py/.json`（用户否决独立脚本）。
- `m13_v38_capacity_gate_record.md` 重写为最终版（§6-§7 正确，§0-§5 早期被证伪段已标注）。
