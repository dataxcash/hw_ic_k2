# m13 v57 — W3 (G4) 构造式联合赋位 Boundary Declaration **v1.2**

> Revision **W3-CN.1**｜Schema 1｜Artifact `m13_v57_w3_joint_assignment.json`
> 契约 `m13_v57_w3_kickoff_card_v1_2.md`（W3-C2，sha `78a96a7fc4daaa9f…`）
> 生产者 `k2/tools/p3_v57_w3_constructive.py`（闭式构造，零搜索）
> 独立验证器 `k2/tools/p3_v57_w3_constructive_validator.py`（不 import 引擎）
> 依据：L2 铁律「确定性一次算对，不搜索 / 禁暴力求解与暴力迭代」+ 批准的计划 v2。
> 本文件取代 v1.1 boundary（`a317662a…`）；旧引擎 `p3_v57_w3_joint_assign.py` 标
> `superseded_non_conforming`（留档不改，见工件 `supersedes_method`）。

## 1. 结果

**`verdict = "CERTIFICATE"`**：**R2 / R3 / REFCLK 全部构造可行**，R1 赋位 32/32 且帧内单调，
但 **2 项谓词在本构造规则下不可行**（→ 2 张 `CONSTRUCTION_INFEASIBLE` 证书）：
① R1.5 单层扇面平面性（交叉 454）；② R1 跨页互斥残余 3 对（晶格吸附后 < 0.525）。
按 F-12：CERTIFICATE 态**不重发射** landing（`landing_rows=null` / `NOT_REEMITTED`）、不发射节点。

| 层 | status | 构造规则 | 结果 |
|---|---|---|---|
| R1 | 32/32 赋位（2 残余对） | `frame_prefix_monotone_x + band_escape_y`（单遍前缀，步长 0.6/槽 0.6） | 帧内每极性 x 单调 ✓；via 全 ∈ 冻结候选 ✓；两两 ≥0.525 ✗3 对 |
| R1.5 | **CERTIFICATE** | `single_straight_segment`（零折角、域内零 via） | 交叉 **454** → 证书（构造域） |
| R2 | FEASIBLE | `frame_contiguous_blocks`（分段区：西走廊 0..15 / 东走廊 16..31） | 走廊内严格递增 ✓；双端 ≤45.4 ✓ |
| R3 | FEASIBLE 72/72 | `gap_column_prefix_recurrence` | 同 gap 列 ≥0.525 ✓；落点 ∈ F-8 `y_band` ✓ |
| REFCLK | FEASIBLE | `witness_window_polyline`（F.Cu，消费 W0-R 见证） | 段与 11 keepout 盒零交 ✓；页间 5.4 ≥1.46 ✓ |

## 2. 方法级门（G-M1..G-M6）

| 门 | 结果 |
|---|---|
| G-M1 去注释/去字符串 NAME 令牌零搜索词 | **PASS（0 命中）**：`dfs/backtrack/csp/search/enumerate/permutations/combinations/product/itertools/random/shuffle/while/recursion/node_cap/alternatives/candidates_tried` 全无 |
| G-M2 AST | **PASS**：0 自调用、0 `while`、imports = `argparse/bisect/hashlib/json/pathlib/numpy`（无 itertools/random） |
| G-M3 闭式复杂度 | **PASS**：`work_units = 526 = 11·n_pages(32) + 2·n_landing(72) + 6·n_refclk(2) + 3·n_frames(6)`；`--scale K` → K=2: 740 = 11·64+3·12 ✓、K=4: 1480 = 11·128+3·24 ✓（逐步精确线性；wall-time 比 0.728/0.536 = 1.36 ≤ 2K） |
| G-M4 独立重导 | 由独立验证器按闭式公式重算（见 `m13_v57_w3_validation.json`） |
| G-M5 不变量/证书 | 不变量全部为纯检查；未通过项 → 证书（仅闭式条件名 + 数值） |
| G-M6 零备选痕迹 | **PASS**：工件零 `alternatives/options/tried/attempts/node` 键；`branch_sites` 改名 `decision_points`（因 G-M6 的 `branch` 子串禁令，见 §5 NOTE-1） |

## 3. 证书（2 张，均 `CONSTRUCTION_INFEASIBLE`）

1. **R1_5** `frame_monotone_fan_single_layer_straight_segment`：
   `closed_form_condition = "∃ p ∈ segments: p_x monotone per frame ∧ 所有段对不相交（平面扇面）"`；
   `observed = {crossings: 454, minimal_core: [...6 页对...]}`。
   **结构性原因（可闭式陈述）**：WEST 的 up 带两帧（J3up conn_row 43.25 与 J4up conn_row 63.95）
   **共用同一 chip 源行 y≈49.8**，而 F-5 单调 lane 序强制二者分居帧块两端（Δindex ≥ 9 → Δy ≥ 13.14mm）
   ⇒ 源序与靶序反转 ⇒ 单层直线扇面必交叉。EAST 亦有同型（up 扇面下探入 dn 源行区）。
2. **R1** `x_lattice_snap_mutual_clearance`：3 对 via 在 0.05 网格吸附后互距 < 0.525
   （例 `PCIE_DN3/input.N ↔ PCIE_DN4/input.P` = 0.3162）。

> 证书语义（L2 补充要求）：**仅表示"本构造规则下不可行"，非全局不可能性证明**；
> 字段仅闭式条件名 + 数值，零"重试/回退/备选"痕迹。

## 4. 验收谓词（`gate_status`）

PASS：A-CN.1d / .1a / .1c / .2a / .2b / .3a / .3b / .3c / .5a / .5b / .6 / .7(vacuous) / .8 / .method
FAIL（已由证书归因）：A-CN.1b（3 对）、A-CN.4（454 交叉）。

## 5. 备注

- **NOTE-1**：契约 v1.2 §R-6 写 `method.branch_sites`，因 G-M6 禁止键名含 `branch` 子串，
  实现改名为 `method.decision_points`（语义相同，值 `{per_rule_max: 2}`）。属契约自相冲突的技术性收敛。
- **NOTE-2**：R3 落点键 = `"<connector>|<net>"`（4 个 REFCLK 网在 J2 与 J3/J4 各出现一次，
  单用 net 名会塌缩 68 < 72）。验证器须按复合键对齐。
- **NOTE-3**：`--scale K` 为 G-M3 规模探针（复制页集 K 份，x 偏移 300mm，仅计 work_units）。

## 6. 位置与逃生门（**待 L2 裁决**）

达成 `FEASIBLE_ALL` 需要上游输入变更（本卡不改）：
1. **R1.5**：① 允许过渡段用第二铜层（放宽 `vias.high_speed.max_per_line`）；
   ② 放宽 `no_via`/`no_90deg` 让渡到「通道化多折线 + 新资源层字段」；
   ③ 改 F-5 帧/lane 序约束（使源序与靶序可分块对齐）；④ 上游重排 U6 ball→corridor 归属。
2. **R1 残余互斥**：① 把槽步长由 0.6 提到 1.2（帧内 8 页 → 9.6mm，仍在 ±1.5 窗口内）；
   ② 或允许 0.05 网格外的 0.025 微调（须上游授权）。
