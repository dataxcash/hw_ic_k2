# K2 · **B2-T 处置草案：(甲) 重基线 / (乙) 具名退役** · 2026-09-20（只读 · 裁量权归监理）

> 机读真源：`P6_execution/B2T_REMEDY_OPTIONS_v1.json`（工具 `k2/tools/k2_p6_b2t_remedy_v1.py`：**现跑失败清单 + 现测真源量 + 人工处置表**）
> 前提（已证）：`docs/K2-P6-B2T-EXPERIMENT-NAMING-SYNC-INSUFFICIENT-20260920.md` —— **命名同步不足**，真因 = 几何/代际漂移。
> 用法：监理选定 **(甲)/(乙)/混合** 后，ENG 按所选逐项落件；**ENG 不擅自改期望**（C-12）。

## 1. 现行真源测量（重基线的「期望值来源」）
| 量 | 实测（现行板 + 现行 SPEC） |
|---|---|
| 走廊 | `WEST_MCIO_TO_CHIP x=[65.05,82.35]` · `EAST_CHIP_TO_J2 x=[105.25,132.65]` |
| `PCIE_DN0_P` pad x | **84.85** ⇒ 不在任一走廊内（`_corridor_for_x` = **None**） |
| `_capacity_regions()` | **['J2_region','MCIO_region']**（仅连接器区） |
| `solve_all_v4`（18 base） | **0/18 SOLVED** |
| `link_topology_map` | verdict=`CROSSING_FOUND`，crossing=**['UP4','UP5','UP6','UP7']**（4 对，非期望 8 对） |
| `_corridor_clear_span` | 两走廊 span **== x_range**（无器件缩进） |
| `probe_region_capacity`（同形 region） | **INSUFFICIENT**（测试内构造则为 `INFRA_ERROR` ⇒ 待 ENG 定性） |


## 1.1 追加测量：**18/18 链的端点都不在现行走廊内**（选案前须 ENG 定性）
| 事实 | 值 |
|---|---|
| 18 链端点（`pair_endpoints(...)[P][0]` 取法）chip 侧 pad x 跨度 | **[54.70, 93.55]** |
| 走廊 | `WEST_MCIO_TO_CHIP [65.05,82.35]` · `EAST_CHIP_TO_J2 [105.25,132.65]` |
| 无走廊命中 | **18 / 18**（8 条落在走廊间带 82.35–105.25；其余在 WEST 走廊以西 x<65.05） |
⇒ **遗留 probe/escape API 的前提（net 端点落走廊）在现行 SPEC 下不成立** ⇒ 13 项确属**旧代际语义**（非"SPEC/板不兼容"缺陷）。
**caveat（诚实边界）**：端点取法依 `pair_endpoints(...)[P][0]`；**定案前须 ENG 复核取法**（已列入待定性项 ③）。

## 2. 逐项草案（13 项）
| # | 用例 | (甲) 重基线：新期望 + 来源 | (乙) 具名退役理由 | ENG 建议 |
|---|---|---|---|---|
| 1 | `test_probe_escape_capacity_dn0` | `status ∈ (SOLVED,BLOCKED,**NO_CORRIDOR**)`；来源 = 走廊覆盖几何 | 旧代际探针期望（pad 必落走廊） | 甲 |
| 2 | `test_probe_reports_via_gap_fact` | 仅 `status≠NO_CORRIDOR` 时校验边距事实 | 物理事实属旧几何 | 甲 |
| 3 | `test_capacity_regions_derived` | `regions == {J2_region, MCIO_region}`；来源 = 实测推导 | U7/U3 pin_region 属旧命名/分段 | 甲（或 ENG 论证补 pin_region） |
| 4 | `test_capacity_map_persist` | regions/corridors 数按**实测** | 4 区域/6 走廊为旧代际 | 甲 |
| 5 | `test_probe_region_capacity_structure` | `status ∈ (CAPACITY_OK,INSUFFICIENT)` | 旧代际 region 契约 | 甲 + ENG 定性 INFRA_ERROR 差异 |
| 6 | `test_corridor_clear_span` | `span == x_range`（无缩进） | 器件缩进属旧布局 | 甲 |
| 7 | `test_chain_no_pn_zero_spacing` | 允许 `INFEASIBLE` 并记录原因 | 旧可解性假设 | 甲 |
| 8 | `test_flip_polarity_cross_rejected` | 入参在当前几何返回 `None`（需重写输入） | 事故锚点 (64.317,49.077) 属旧场景 | 乙（同族 9/10/11） |
| 9 | `test_drawing_only_refuses_no_node` | 同上 | drawing_only 红线需按现行逃逸域重写 | 乙 |
| 10 | `test_correct_polarity_solves_clean` | 前提不成立 | 旧正极性可解假设 | 乙 |
| 11 | `test_escape_deterministic_byte_identical` | **确定性属「性质」**，应在**现行可解输入**上重写 | —（不建议退役） | 甲（优先保留性质） |
| 12 | `test_board_level_consistency` | 以**现行真源可解子集**为对象（当前 0/18） | —（整板一致性重要，不建议退役） | 甲（+ENG 分析 0/18 是真缺陷还是输入所致） |
| 13 | `test_link_topology_crossing_old_topology` | `crossing == ['UP4','UP5','UP6','UP7']`；来源 = 实测拓扑 | 8 对期望属旧拓扑判定 | 甲（或 ENG 论证应报 8） |

## 3. 提请监理裁定
1. **选案**：(甲) / (乙) / **混合**（本表「ENG 建议」列即混合方案：11 项甲、3 项乙）。
2. **退役须具名**：写入 `results_template.json` 与回归网说明，**禁静默 skip**（C-12）。
3. **三处须 ENG 先定性再定案**：① §1 的 `INFRA_ERROR` vs `INSUFFICIENT` 差异（初步定位：测试内 region 把 **J2/东侧走廊 id 与 U7 侧 bases 配对** ⇒ 自相矛盾 ⇒ INFRA_ERROR；同形但走廊 id 正确时实测 INSUFFICIENT）；② `solve_all_v4` **0/18** 与 §1.1 **18/18 无走廊命中** 的关系（判定为「旧 API 前提不成立」or 引擎真缺陷）；③ 端点取法 `pair_endpoints(...)[P][0]` 复核。

## 4. 零改动声明
真源 `_shared`/`criteria/`/冻结四源/交付锚/生成器/SPEC/原理图**均未触**；实验与测量全在 `/tmp/opencode/shadow_b3`；未派 WORKER。
