# M14 v38 实施计划 — 极性不变式（P/N 极性三端统一）作为 EDA TOPO ENG 拓扑层不变量

> 计划状态：**批准待执行**（已与用户对齐方向，待本 NEW SESSION 前台推进）。
> 承接：m13_v37_session_handoff.md + 本文件。范围 = 修"16 对 P/N 极性错配"根因，
> 不碰"容量"（引擎 `bga_per_ball_escape` 已判 FEASIBLE，deficits=[]）。
> 纪律：全前台自跑、禁 task() 委派、禁后台长跑、禁暴力迭代（同参≤2 带依据）、禁 chmod、禁无依据 --all-v4。

---

## 1. 根因（已实测确认，勿重推）

| # | 事实 | 证据 |
|---|---|---|
| R1 | 引擎容量门 G4 = FEASIBLE（可解），deficits=[] | `bga_per_ball_escape`(escape_landing) 跑 K2 → verdict=FEASIBLE direct=32 via=32 crossing=16 |
| R2 | `solve_all_v4` 全量现状：solved 仅 **PCIE_UP1** 1 对 | `/tmp/solve_v33g/hs_rebuild_summary.json`（base fpsha=`f6273de6`=当前权威板） |
| R3 | **失败根因 = P/N 极性错配**（非列槽容量）：80% base 报 `flip=True via 换层 P/N 极性不一致（相向交叉 min 边缘距 -0.2050 < 0.175 @ 逃逸点）` 或 `落点驱动逃逸 P/N 相向交叉（-0.2050）` | v33g summary 逐 base reason（DN0-7/UP0-7/REFCLK0-1 全部同族） |
| R4 | **芯片侧极性**：A_PER 系 `N 上 P 下`（`PCIE_DN0_N` ball R1 y=57.64 / `_P` ball N2 y=57.12） | `chip_landing_v33.json` + `ds320pr1601_ballmap.json` |
| R5 | **轨道侧写死**：`_expand_pair`(hs_route_model L740) = "P=`track_y-0.19`(上)、N=`track_y+0.19`(下)" | hs_route_model.py |
| R6 | **连接器侧**：`RoutingTopologyGate._check_pn_polarity`(L592) 已判 P 右 N 左/x 侧符号，但**只测连接器侧，未与芯片侧/轨道侧拟合** | routing_topology_gate.py |

**冲突链路**：芯片侧(N上P下) ↔ 轨道侧(写死P上N下) → 逃逸出口遭跨相交 → min 边缘距 -0.2050（P/N 重叠）→ INFEASIBLE。
轨道 `_expand_pair` 的"P 上 N 下"写死 + 布线 flip 靠碰 = 下游补丁；**真正病根 = 极性未在前端(拓扑层)建立为全链一致不变量**。

---

## 2. 目标

在 **EDA TOPO ENG 拓扑层**（`RoutingTopologyGate`）把三端极性统一为**每 base 全链一致极性不变式**，并向下游（③channel_alloc / ⑤布线）传递，使：
- 芯片侧 P/N 位序 == 轨道侧 P/N 位序 == 连接器侧 P/N 位序（沿同一链路不交叉）；
- 布线 flip 由极性**派生**（不再 flip 靠碰，不产生相向交叉）；
- 全量 18 对 SOLVED + skew<0.15 + P/N 净空≥0.175。

---

## 3. 分步实施（每步独立可验，单测零回归 + 渐进验证）

### Step 1 — 拓扑层：极性不变式建立（`routing_topology_gate.py`）
- 扩展 `_check_pn_polarity`（L592）：把现有"连接器侧 x 侧符号"判定，与"芯片侧球图 y 位序"（chip_landing+ballmap 的每 base 每 P/N ball 坐标）拟合为每 base 的**唯一 P/N 极性**：
  - 输入：`chip_landing_v33.json`（每 base P/N pad/ball 位序）+ `ds320pr1601_ballmap.json`（球图权威坐标）+ 现有连接器侧 demands。
  - 输出：`polarity_invariant{ base -> {chip_side: "P_top"/"P_bottom", conn_side: "P_right"/"P_left", track_polarity: "+0.19"/"-0.19"} }`，进 `FeasibilityVerdict.evidence`（字段 `polarity_ok` 已存在）。
  - 判定语义：全链一致 → `polarity_ok=True` + 不变式表；不一致（某 base 三端矛盾）→ `polarity_ok=False` + 冲突 base 证据（禁止下游继续跨交叉）。
- 单测：`test_routing_topology_gate.py` 新增极性不变式用例（构造三端已知 bit 序的 base，断言不变式唯一 & 一致性布尔）。

### Step 2 — 轨道侧：P/N 上下由极性派生（`hs_route_model.py` `_expand_pair`/`_track_y_for`）
- 改造 `_expand_pair`（L737-758）：由 `polarity_invariant[base].track_polarity` 决定 P/N 的 `±PAIR_HALF_PITCH` 方向（不再硬编码 P 上 N 下）。
- `_track_y_for`（L702）：返回 track_y 同时携带该 base 极性标记，供下游 flip 派生。
- 单测：`test_hs_route_model.py`（或新增 polarity 用例）断言：同 base 给定极性 → `_expand_pair` 输出 P/N 位序与不变式一致，不再相向交叉。

### Step 3 — 布线侧：flip 由极性派生（`hs_route_model.py` `_escape_pair`）
- `_escape_pair`/`_col_stack_escape`：flip 参数改为由 `polarity_invariant[base]` 派生（芯片侧位序 + 轨道位序 → flip 唯一解），不再独立尝试两 flip。
- 单测：断言给定极性不变式 → 逃逸路径出口 P/N 顺序 == 轨道顺序（min 边缘距 ≥0.175，无相向交叉）。

### Step 4 — 数据流传递（`solve_pipeline.py`）
- `run_feasibility` 产出的 `polarity_invariant` 存 `FeasibilityVerdict.evidence`；`run_solve` 消费进 `HSRouteModel`。
- 单测：`test_solve_pipeline.py` 断言极性不变式从①流向⑤（context 传递完整）。

### Step 5 — 全量验证（≤2 次，带依据）
- 用容器 `_shared` 引擎 + 当前板 `f6273de6`，跑 `SolvePipeline.run_all`（经 `p3_k2_real_board_e2e.py` 组装，注：该脚本 sha_expected=`6c387dff` 为旧文档，仅记录不硬校验，board 路径指向当前 `k2_v4.kicad_pcb`=`f6273de6`，可跑）。
- 判据：18 对 SOLVED + skew<0.15 + P/N 净空≥0.175 + 坐标 JSON 落盘。

### Step 6 — 合规（ECN-009）
- `bash k2/pm_gate/freeze_ctl.sh unlock` → 备份 → 改（Step1-4）→ 单测 43 passed 零回归(7 failed 既有同集) → `lock` → status 0/0/0。
- ECN-009 裁决：把方向定为「极性不变式（拓扑层）」，归档。

---

## 4. 停止/回退判据（防暴力迭代）

- 任一 Step 单测回归失败 → 回查该 Step，**不带依据不重跑全量**。
- Step5 全量第 2 次仍未 18 SOLVED → **立即停**，带极性不变式诊断（哪些 base 三端仍矛盾）+ 证据回设计层（加层/放宽净空/减 lane/换器件），不续命。
- REFCLK0/1：v33g 里它也极性问题（`flip=True P/N 极性不一致 @ (58.9,45.5)`）→ 应随 Step3 一并解决；若独立残留 → 归 G5，单列。

---

## 5. 产物（本计划批准后）
- `routing_topology_gate.py` / `hs_route_model.py` / `solve_pipeline.py` 改动
- 新增单测用例
- `run_all` 全量 summary + 坐标 JSON
- ECN-009 归档记录

---

## 6. 勿加载清单（省 CONTEXT，NEW SESSION 必读）

**必读**：本计划 + `m13_v37_session_handoff.md`（§1 F1-F6，已钉死）。
**勿读全文**：`m13_v10`~`m13_v36` 任一 handoff（v36 只读 §9）；`m13_v31`~`v36` inner 运行细节。
**勿整读**：`hs_route_model.py`（只 grep `_expand_pair`/`_track_y_for`/`_escape_pair`/`_col_stack_escape`/`solve_all_v4`）；`routing_topology_gate.py`（只 `_check_pn_polarity`/`plan`）；`solve_pipeline.py`（只 `run_feasibility`/`run_solve`/`_capacity_gate`）。
**勿重读原始扫描产物**：SNLU300/ds320 文本、page-*.png、ds_ball*/ds_lay*（只需 F1-F6 + R1-R6）。
**勿重跑**：`bga_per_ball_escape`（已判 FEASIBLE）；`--all-v4`（只在 Step1-4 全部落地后跑第 1 次）。
