# 类 A 修复验证报告 — via 换层 P/N 极性几何预检（hs_route_model --all-v4, k2_v6, v10）

> 结论：**类 A 缺陷（P/N 相向交叉假 SOLVED）已消除 — v8 的 44 个假 SOLVED 段 → v10 为 0；
> 14 个类 A 网全部为「正确 INFEASIBLE（带几何原因）」，无一假 SOLVED**。
> 单测：4 个新增全绿 + 零回归（8 个既有失败与修复无关，见 §5）。

## 1. 修复内容（_shared/eda_core/hs_route_model.py，零 revA 特判）

| 位置 | 改动 |
|---|---|
| 模块级 | 新增 `_seg_intersection` / `_seg_closest_mid` / `_path_pn_min_edge_pt`（两路径同层最小边缘距 + 交叉/最近点；`_pn_spacing_check` 同源语义） |
| `_pn_spacing_check` | 重构为复用 `_path_pn_min_edge_pt`（语义逐字节不变） |
| `_escape_pair`（via 形态） | 每候选构造完成即验 P/N 同层边缘距（阈值 0.155）；交叉 → 弃候选，记录几何证据（min 边缘距 + 交叉点）；该 flip 全候选被拒 → INFEASIBLE「via 换层 P/N 极性不一致（相向交叉）…」带 `cross_evidence`。DIRECT 形态未动 |
| `_solve_pair_centerline_v4`（段组装） | 组装后全段同层复检（逃逸×走廊跨段交叉，如 F.Cu pad→via 竖线穿对侧轨）；交叉 → 弃该 flip（INFEASIBLE 带证据） |

机制 = 任务要求 2（每候选构造期 P/N 间距检查，交叉即弃）落地于两个层级（逃逸级 + 段组装级），
并产出任务要求 1 的「带几何证据」INFEASIBLE。固定候选序不变（确定性）。

## 2. 单测（test_hs_route_model.py::TestV6ViaPolarityPrecheck，4/4 绿）

| 测试 | 断言 |
|---|---|
| `test_flip_polarity_cross_rejected` | UP0 input 左逃逸 flip=False → INFEASIBLE，reason 含「极性/相向交叉」，cross_evidence.min_edge ≤ -0.2，交叉点 = 事故记录点 (64.317, 49.077)（与 v8 §4.1 证据表逐点一致） |
| `test_correct_polarity_solves_clean` | DN4 input 段（flip=True 与 pad 排序一致）→ SOLVED 且 P/N 边缘距 ≥ 0.155 |
| `test_no_solved_segment_carries_crossing` | REFCLK0 + DN4 链：SOLVED 段一律无交叉（edge ≥ 0.155） |
| `test_escape_deterministic_byte_identical` | 同一逃逸两次求解 json 逐字节一致 |

## 3. 求解执行（合法单次：模型改动 = 新输入，每次模型版本仅跑一次）

- v8（修复前，已存）→ v9（修复 v1）→ v10（修复 v2 = 段组装门补全，**最终**）
- v10 命令与任务参数逐字一致（CWD=容器根，理由见 v8 报告 §1）；`solve_time_s = 30.755`，进程 1 次
- 输入指纹不变：board `9b6e28c3…`（模型 input_fp 一致）、SPEC `7eaad223…`、alloc `3f8fb6fc…`、config `54b187f7…`、rules `0a459839…`、求解器（本修复后）`5464d8f0…` 所在文件

## 4. 验收核对（k2_v6, v10 输出）

### 4.1 逐对耗时（per_pair_timing.json，实测 wall-clock）— 全部 < 5s

| UP0..UP7 | s | DN0..DN7 | s | REFCLK | s |
|---|---|---|---|---|---|
| UP0 1.268 UP1 1.193 UP2 2.463 UP3 2.971 UP4 1.625 UP5 2.024 UP6 2.192 UP7 2.602 | | DN0 1.582 DN1 1.599 DN2 2.161 DN3 1.647 DN4 2.281 DN5 2.260 DN6 1.225 DN7 1.363 | | REFCLK0 0.009 REFCLK1 0.291 | |

max = 2.971s（UP3）< 5s ✓；无暴力求解结构（确定性折线 + VGraph 兜底单次）。

### 4.2 零交叉契约（核心验收）

- **v8：44 个假 SOLVED 段 P/N edge < 0.155**（其中 22 个 = -0.205 精确交叉；其余 -0.03 ~ -0.19 近交叉）——
  被链级 `_pn_spacing_check`（仅取链内最小值）遮蔽
- **v10：0 个违规** — 全部 SOLVED 段 P/N edge ≥ 0.155：DN0 out_U3 0.1732、DN2 input 0.1553、
  DN4 input 0.1553、DN6 input 0.1729、REFCLK0 input 0.1749
- 链级 `pn_spacing` 断言触发 = **0**（交叉在构造期被拒，不再有「模型缺陷证明」降级）

### 4.3 类 A 14 对（v8 pn_spacing=-0.205）→ v10

| 网 | v8 | v10 | v10 段级（极性=极性交叉被拒 / 净空=净空失败 / SOL=edge） |
|---|---|---|---|
| UP0-7 | INFEASIBLE（假 SOLVED 段×3） | INFEASIBLE | input:极性 out_U7:净空 out_J2:极性（8 对同构） |
| DN1 | INFEASIBLE（假 SOLVED 段×3） | INFEASIBLE | input:极性 out_U3:极性 out_MCIO:极性 |
| DN2 | INFEASIBLE（假 SOLVED 段×3） | INFEASIBLE | **input:SOL(0.1553)** out_U3:极性 out_MCIO:极性 |
| DN4 | INFEASIBLE（假 SOLVED 段×3） | INFEASIBLE | **input:SOL(0.1553)** out_U3:极性 out_MCIO:极性 |
| DN5 | INFEASIBLE（假 SOLVED 段×3） | INFEASIBLE | input:极性 out_U3:极性 out_MCIO:极性 |
| DN6 | INFEASIBLE（假 SOLVED 段×3） | INFEASIBLE | **input:SOL(0.1729)** out_U3:极性 out_MCIO:极性 |
| REFCLK1 | INFEASIBLE（假 SOLVED） | INFEASIBLE | input:极性 |

**结论：14/14 为「正确 INFEASIBLE（带原因）」— 无一假 SOLVED**；其中 3 对 input 段已转为干净 SOLVED。
INFEASIBLE 段全带证据：36×极性交叉（含 `cross_evidence` 坐标）+ 9×净空失败（含 `nearest`）。

### 4.4 关键事实（非回归核验）

- v8 的 UP0-7 out_U7（曾「SOLVED」）实为**假 SOLVED**：In2 收敛段 P/N edge -0.036 ~ -0.101（例 UP0
  out_U7 P[1]×N[1] dist 0.104 → edge -0.101）→ v10 正确拒绝。非修复引入的回归。
- v9 中 DN7 out_U7 的段组装交叉（F.Cu pad→via 竖线穿 N 走廊轨 @ (84.25,67.29)）→ v10 段组装门拦截。
- REFCLK0 修复前后不变（SOLVED, edge 0.175, skew 2.21 等长不达标为既有事实）。

## 5. 测试套件状态（_shared/eda_core/tests/test_hs_route_model.py）

- **34 passed（基线 30 + 新增 4）/ 8 failed（与基线完全一致，零新增、零回归）**
- 8 个既有失败均与本次修复无关（修复前即红）：
  5× v2 引擎（m9demo 基线板，走 `_escape_polyline` 路径，本次未触碰）；
  2× v4 探针（`NO_CORRIDOR`——探针走廊查找，未触碰）；
  1× 整板一致性（k2_v4 18/18 断言——类 B 逃逸净空 + 引脚区缺口仍在，非本任务范围）

## 6. MUST NOT 合规

- ✅ 未改 DIRECT 形态几何（`_direct_escape` 逐字节未动，其预检保留）
- ✅ 未改轨道分配 / channel_alloc / SPEC / config
- ✅ 未手改求解结果；每次模型版本仅跑一次（v8/v9/v10 各自单次，模型改动 = 新输入）
- ✅ 未触碰 git

## 7. 停机说明（类 A 修复完成，类 B 不在本任务范围）

类 A 的「正确 INFEASIBLE」根因：连接器/MCIO 侧 P/N 同排同 y 焊盘 + 走廊上/下轨分配，
当前 via 形态候选空间（H-V/V-H/DIAG × 对称 via）无法构造无交叉逃逸（双 flip 均交叉被拒）。
此为**逃逸构造能力缺口**（非模型缺陷假 SOLVED），属后续形态扩展（如非对称 via / 竖线异 x 模板）
的输入，不在本任务「补极性预检」范围。类 B（DN0/DN3/DN7 out_MCIO 逃逸净空 vs 同链先解段/GND pad）
维持停机待人工裁决。
