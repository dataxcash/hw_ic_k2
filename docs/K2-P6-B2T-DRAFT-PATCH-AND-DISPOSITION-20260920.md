# K2 · P6/B2-T 13 项既有隐藏失败 · **甲案草稿补丁 + 逐项定性**（ENG / ARCHER）

> 状态：**草稿（/tmp 影子，真源零改动）**；判定归监理 · 施工前需批2 授权（碰 `_shared` / 测试锚）。
> 机读：`k2/pm_gate/artifacts/k2_v4/P6_execution/B2T_DRAFT_PATCH_v1.json` · diff：`/tmp/opencode/b2t_draft_patch_v1.diff`
> 生成：`python3 k2/tools/k2_p6_b2t_draft_patch_v1.py --verify-determinism`
> **补记（同一会话续作）**：测试锚**承载形态**验证见
> `k2/docs/K2-P6-B2T-ANCHOR-CARRIER-AND-FAILCLOSED-20260920.md` —— 结论：**运行期自建 alloc 不可行**
> （现行 8L 输入下 alloc 阶段 0 解），锚迁移须走「具名冻结载体（P3 Sept-9 alloc，血缘登记）」或
> 「合成现行 fixture」；B1 同族 fail-closed 普查 = 单点缺陷（33 API × 2 载体仅 B1 抛异常）。

## 0. 五棵树读数（同一测试文件、同一板锚；差异只在 alloc 锚 / 补丁 / 引擎守卫）

| 树 | 含义 | passed | failed | skipped |
|---|---|---|---|---|
| base | 遗留 alloc 锚（现状） | 43 | 13 | 12 |
| anchor | 仅重锚现行 pipeline alloc | 41 | 15 | 12 |
| draft | anchor + 甲案测试补丁 | 50 | 6 | 12 |
| **draft_b1** | draft + B1 引擎守卫（/tmp 影子） | **54** | **2** | 12 |
| negctl | draft_b1 + 逐项 mutation | 41 | 15 | 12 |

牙齿（负控）总判：**PASS**（改错期望必 FAIL ⇒ 补丁不是"改绿"）
确定性（两跑逐字节同）：**MATCH**

## 1. 13 项逐项定性（状态 = 各树实测）

| test | 定性 | base(遗留锚) | anchor(仅重锚) | draft_b1(甲案+B1) | negctl | 处置 |
|---|---|---|---|---|---|---|
| `test_probe_escape_capacity_dn0` | 甲 | FAILED | FAILED | PASSED | FAILED | 期望重基线 + 走廊 id（status=BLOCKED） |
| `test_probe_reports_via_gap_fact` | 甲 | FAILED | FAILED | PASSED | FAILED | 期望重基线（0.6 中心距；保留 edge=中心距−0.35 不变量） |
| `test_capacity_regions_derived` | 甲 | FAILED | FAILED | PASSED | FAILED | 期望重基线（2 区域 connector，数据驱动） |
| `test_probe_region_capacity_structure` | 甲 | FAILED | FAILED | PASSED | FAILED | 输入重锚：区域由 _capacity_regions() 自推导 |
| `test_capacity_map_persist` | 甲 | FAILED | FAILED | PASSED | FAILED | 期望重基线（2 区域 / 6 走廊） |
| `test_corridor_clear_span` | 甲 | FAILED | FAILED | PASSED | FAILED | 期望重基线（无器件缩进；保留含于 x_range 不变量） |
| `test_chain_no_pn_zero_spacing` | 丙 | FAILED | FAILED | FAILED | FAILED | 能力缺口（REFCLK0 实测 INFEASIBLE：左逃逸极性交叉 -0.205）⇒ 保持 RED |
| `test_flip_polarity_cross_rejected` | 甲 | FAILED | FAILED | PASSED | FAILED | 场景/事故点重锚：EAST 几何 (64.300,43.060) 仍是 INFEASIBLE+证据 |
| `test_drawing_only_refuses_no_node` | 甲 | FAILED | FAILED | PASSED | FAILED | 输入重锚（走廊角色解析）；断言不变 |
| `test_escape_deterministic_byte_identical` | 甲 | FAILED | FAILED | PASSED | FAILED | 输入重锚（走廊角色解析）；断言不变 |
| `test_board_level_consistency` | 丙 | FAILED | FAILED | FAILED | FAILED | 能力缺口（现行 alloc 实测 1/18 SOLVED）⇒ 保持 RED，具名登记 |
| `test_link_topology_crossing_old_topology` | 甲+B1 | FAILED | FAILED | PASSED | FAILED | 期望重基线（4 对 crossing）+ 需 B1 引擎守卫 |
| `test_correct_polarity_solves_clean` | 甲 | FAILED | PASSED | PASSED | PASSED | 输入重锚后 DN4 input 段 SOLVED（无需改文本） |

**读法**：`甲` = 期望重基线 / 输入重锚（可施工，须监理批）；`丙` = 能力缺口（禁改绿，具名登记）。
`draft_b1` 列 FAILED 的 `丙` 项 = **故意保持 RED** 的真实缺口。

## 2. 甲案补丁逐项（含期望值来源；全部实测）

| # | test | 定性 | 改测试 | 负控 | draft_b1 | negctl | 期望值来源（实测） |
|---|---|---|---|---|---|---|---|
| A1 | `test_capacity_regions_derived` | 甲-期望重基线 | 是 | 是 | PASSED | FAILED | m._capacity_regions() 实测 = 2 区域 connector |
| A2 | `test_capacity_map_persist` | 甲-期望重基线 | 是 | 是 | PASSED | FAILED | m.capacity_map() 实测 = 2 区域 / 6 走廊（2 廊道 × 3 band） |
| A3 | `test_corridor_clear_span` | 甲-期望重基线 | 是 | 是 | PASSED | FAILED | m._corridor_clear_span() 实测 = 各走廊 x_range 原值（无器件缩进） |
| A4 | `test_probe_escape_capacity_dn0` | 甲-期望重基线 | 是 | 是 | PASSED | FAILED | probe_escape_capacity(DN0,"input") 实测 status=BLOCKED / corridor=EAST_CHIP_TO_J2 |
| A5 | `test_probe_reports_via_gap_fact` | 甲-期望重基线 | 是 | 是 | PASSED | FAILED | DN0 芯片侧实测 pn_pad_center_dist=0.6（0.4 脚距属旧代际引脚区） |
| A6 | `test_probe_region_capacity_structure` | 甲-输入重锚(数据驱动) | 是 | 是 | PASSED | FAILED | m._capacity_regions() 的 J2_region（corridor=EAST_CHIP_TO_J2, side=right, out_J2, band=up）实测 CAPACITY_OK/8 对 |
| A7 | `test_flip_polarity_cross_rejected` | 甲-场景/事故点重锚 | 是 | 是 | PASSED | FAILED | UP0+EAST_CHIP_TO_J2 flip=False 实测 INFEASIBLE(kind=VIA) min_edge=-0.205 @ (64.300,43.060)；原 WEST 场景实测已 SOLVED(LSWAP_V) |
| A8 | `test_drawing_only_refuses_no_node` | 甲-输入重锚(角色解析) | 是 | 是 | PASSED | FAILED | WEST_MCIO_TO_CHIP + track_y 可解析 ⇒ kind=NO_DRAWING_NODE（断言不变） |
| A9 | `test_escape_deterministic_byte_identical` | 甲-输入重锚(角色解析) | 是 | 是 | PASSED | FAILED | WEST_MCIO_TO_CHIP + track_y 可解析 ⇒ 同一逃逸两次输出逐字节同 |
| A10 | `test_correct_polarity_solves_clean` | 甲-输入重锚(无需改文本) | — | — | PASSED | PASSED | 重锚现行 alloc 后 DN4 input 段实测 SOLVED 且 P/N 最小边缘距 ≥0.155 |
| A11 | `test_link_topology_crossing_old_topology` | 甲-期望重基线(+B1 守卫) | 是 | — | PASSED | FAILED | 现行 alloc(+B1 守卫) 实测 CROSSING_FOUND / crossing=[UP4..UP7] / DN0-3·UP0-3·REFCLK0-1 ALIGNED |
| A12 | `test_board_level_consistency` | 甲-输入筛选修正（测试仍 RED：能力缺口 C1） | 是 | — | FAILED | FAILED | 现行 alloc 含 16 个 *_OUT* 条目 ⇒ 原 base 筛选得 34（应为 18）；筛选修正后断言暴露真实『未全解』 |

**牙齿逐项**（draft_b1=PASSED 且 negctl=FAILED 才算✅）：
| # | draft_b1 | negctl | 牙齿 |
|---|---|---|---|
| A1 | PASSED | FAILED | ✅ |
| A2 | PASSED | FAILED | ✅ |
| A3 | PASSED | FAILED | ✅ |
| A4 | PASSED | FAILED | ✅ |
| A5 | PASSED | FAILED | ✅ |
| A6 | PASSED | FAILED | ✅ |
| A7 | PASSED | FAILED | ✅ |
| A8 | PASSED | FAILED | ✅ |
| A9 | PASSED | FAILED | ✅ |

## 3. 引擎缺陷 B1（真缺陷 · 需授权修）

- **现象**：现行 schema alloc（34 条，含 `*_OUT*`）下 `probe_link_topology` 抛
  `ValueError: min() arg is an empty sequence`（`x_l = min(... for s in segs if "end_left" in s)`）。
- **影响**：`link_topology_map` 全灭 ⇒ 4 个拓扑用例连带失败（遗留锚下不触发 ⇒ 长期隐藏）。
- **最小修**（fail-closed，2 处）：空序列 → `None` + cap_wall 判定加 `None` 守卫。
- **影子验证**：`draft_b1` 树拓扑 4 用例 **4 FAIL → 全 PASS**（crossing=[UP4..UP7]）。
- **授权**：改 `_shared` ⇒ 属批2（与 B2-2/B2-3 同批）。

## 4. 能力缺口（禁重基线至绿）

| # | test | 实测 | 定性 |
|---|---|---|---|
| C1 | `test_board_level_consistency` | 现行 alloc 锚 `solve_all_v4` = **1/18 SOLVED**（PCIE_DN6） | 整板 18 链全解 = 能力缺口（P3 E2E 已登记 D4 形态卡：对级对称逃逸无净空 / via 换层极性交叉 −0.205）；保持 RED + 具名登记 |
| C2 | `test_chain_no_pn_zero_spacing` | `REFCLK0` = INFEASIBLE（−0.205 @ (58.900,45.560)） | 同 C1；其守护性质由 `test_no_solved_segment_carries_crossing`（PASS）覆盖 |

## 5. 工具/口径缺陷（本轮发现，供监理）

- **C-19 影子 import 缺陷**：`k2_p6_shadow_verify_v1.py` 的 `run_pytest(cwd=REPO)` 在容器根运行
  `python3 -m pytest` ⇒ cwd 进 `sys.path[0]` ⇒ `import eda_core` 命中容器根符号链接
  `eda_core -> _shared/eda_core`（**真源**），对 `_shared` 的影子补丁静默失效。
  本工具已修：cwd=影子树根 + `tests/conftest.py` 断言 `eda_core.__file__` 在影子树内（fail-closed）。
  既有 `SHADOW_VERIFY_v1` 结论**不受影响**（其补丁集只碰 `pm_gate`，pytest 腿内容与真源逐字节同）。
- **前会话读数修正**："18/18 端点不在走廊 ⇒ 遗留 API 前提不成立"**不准确**：
  ① `probe_escape_capacity` 实测**命中走廊** `EAST_CHIP_TO_J2`，`NO_CORRIDOR` 的真因是
  `_track_y_for` 在**遗留 alloc**（corridor `J2_TO_U`/band `lower`/track 值旧代）解析失败；
  ② 换现行 alloc 锚后，13 项中 **10 项转为可实现**（实测），说明主因是**输入锚过时**+
  命名/几何代际漂移，而非"几何前提不成立"；③ 剩余真实缺口 = B1（崩溃）+ C1/C2（能力）。

## 6. §6 三处 ENG 定性（实测闭合）

| # | 议题 | 结论（实测） |
|---|---|---|
| Q1 | `INFRA_ERROR` vs `INSUFFICIENT` | **INFRA_ERROR = 输入契约错**（走廊 id `J2_TO_U` 不存在于 SPEC → "无走廊 J2_TO_U"；或段名 `out_U7` 与现行链段 `['input','out_J2']` 不符）——与容量无关；**INSUFFICIENT = 真实容量判定**（现行 id+段名 ⇒ CAPACITY_OK；旧段名 ⇒ INSUFFICIENT 且 pair 级 INFRA_ERROR）。原用例自相矛盾输入 ⇒ INFRA_ERROR 属正确 fail-closed。 |
| Q2 | `solve_all_v4` 0/18 的成因 | **主因 = 输入锚过时**：遗留 `channel_alloc_v2` 的 corridor id（`J2_TO_U`/`U_TO_MCIO`）、band 名（`lower`/`upper`）、track 值三代与现行 SPEC 错位 ⇒ `_track_y_for`=None ⇒ NO_CORRIDOR/INFEASIBLE。换**现行 pipeline alloc** 后链路可解，实测 **1/18 SOLVED**（PCIE_DN6），其余为 D4 形态能力缺口（对级对称逃逸无净空 / via 换层极性交叉 −0.205，P3 E2E gaps 已登记）。**非**"端点不在走廊"、**非**"SPEC 前提不成立"。 |
| Q3 | 端点取法 `pair_endpoints(...)['P'][0]` | 取法**正确**（P[0]=最左=P 网芯片侧焊盘：DN0 84.85 / UP0 64.3 / REFCLK0 58.9）；但走廊选择用 **pair 中点/全跨度**（`_pair_center`+`_corridor_for_x`），非单 pad ⇒ "18/18 chip 侧 pad x ∉ 走廊"为真但不导致 NO_CORRIDOR（见 Q2）。caveat 关闭。 |

## 7. 授权项（单列，等监理/批2）

1. **测试锚**：`K2V4_ALLOC` 由遗留 `channel_alloc_v2` 改指现行 pipeline alloc（承载形态待裁：
   落库再生成 or 测试内自建 `SolvePipeline.run_alloc`）。
2. **`_shared` 改动**：B1 守卫（2 处，fail-closed）。
3. **测试期望重基线批**：A1–A12（11 项期望/输入重锚）。
4. **不申请**：C1/C2 改绿（能力缺口，禁缩口径）。

—— ENG（ARCHER）· 2026-09-20 · 真源零改动（`_shared` / `criteria/` / 冻结四源 / 交付锚未动）· diff 232 行
