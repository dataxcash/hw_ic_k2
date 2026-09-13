# CO-207 — 非执行者对抗复评（CO-202..CO-206c）｜as-found 钉 `add6e33`

- verdict：**PASS_WITH_FINDINGS**｜findings：3（全 low）｜观察项：2
- 方法：正控 V1..V9（独立复算：自板 pcbnew 普查 / 自算术 / 自源 AST / 自跑闸与探针）+ 负控 P1..P8（内存注入、零落盘）

| 控 | 结论 |
|---|---|
| V1_via_census_independent | **False** |
| V2_thermal_recompute | True |
| V3_oracle_reproduced | **False** |
| V4_runner_check_and_registry | **False** |
| V5_frozen_four_and_board | True |
| V6_register_recompute | True |
| V7_criteria_no_fabricated_numbers | True |
| V8_package_integrity | **False** |
| V9_l2_family_independent_reproduction | True |
| P1_revision_extractor_discriminates | True |
| P2_stale_number_detector_discriminates | True |
| P3_boundary_section_detector_discriminates | True |
| P4_fabrication_detector_discriminates | True |
| P5_stub_tooth_discriminates | True |
| P6_thermal_tooth_discriminates | True |
| P7_census_tooth_discriminates | True |
| P8_key_literal_extractor_discriminates | True |

## 独立复算（L2 核心量）

| 配置 | placed/pages | 失败页 |
|---|---|---|
| v9_default | 32/32 | — |
| candC_BRCOL | 24/32 | PCIE_DN2/input, PCIE_DN3/input, PCIE_DN4/input, PCIE_DN5/input, PCIE_UP0/input, PCIE_UP2/input, PCIE_UP3/input, PCIE_UP6/input |
| candC_BRCOL_COLFIX | 23/32 | PCIE_DN2/input, PCIE_DN3/input, PCIE_DN4/input, PCIE_DN5/input, PCIE_UP0/input, PCIE_UP0/out_J2, PCIE_UP2/input, PCIE_UP3/input, PCIE_UP6/input |
| Bpath_lane_outer | 24/32 | PCIE_DN0/out_MCIO, PCIE_DN2/out_MCIO, PCIE_DN5/out_MCIO, PCIE_DN7/out_MCIO, PCIE_UP0/input, PCIE_UP2/input, PCIE_UP4/input, PCIE_UP6/input |

## Findings（as-found）

- **F-1（low）· CO-206b/c**：**B 路「现行模型」数值之口径修正不完整（声明↔内容不同步）**：CO-206b 已把主判据字段更正为 **24/32**（`F4_route_predicates.B.measured` 与 `feasibility.basis`），但**同族**之「现行模型」引用仍滞留 **26/32** —— 实测残留：`artifact.recommendation.basis[0]`、`artifact.routes.B.risk[0]`、`card.md`、`criteria.risk_catalog.B[0]`、`tool.recommend.basis①`。⇒ 决策证据件（`.json`/`.md`）在**同一文件内**对同一量给两个值（`measured`=24/32 vs `risk`=26/32），且该量正被用于「B 是否更便宜可行」之判读（承 R-CO203-1「内容升级须同步」/ R-CO194-1「声明↔实现」）；另：该工具内容经 CO-206b/c 升级而自声明 `revision` 仍 `CO-206.1`（自声明面滞留）。
  - 处置：CO-208（L2 自裁）：① `recommend()` basis① 与判据件 `risk_catalog.B[0]` 之 26/32 → **24/32**（并显式注明口径）；② 自声明面 sync：工具 `revision` **CO-206.1 → CO-206.2**、判据件 **v1.2 → v1.3**（含 changelog）；③ 重生成 `m13_v57_co206_process_route_selection.{json,md}`。红线 **R-CO208-1**。
- **F-2（low）· CO-203（R-CO203-1）**：**R-CO203-1 之登记条款与静态齿 t33 互斥（该条款无齿）**：R-CO203-1 文义要求「**新增此类工具**须入 runner `TOOL_REVISION_DECLARED`」，而 t33 断言 `set(TOOL_REVISION_DECLARED) == {_orc_rel}`（**恒等于单件** {不动点 oracle}）⇒ 依规则登记任一新工具必致 t33 FAIL。实测：`tools/p3_v57_*.py` 中含 `revision` dict 字面量者 **155** 个（含 CO-203 之后新建之 `p3_v57_co206_process_route_select.py`，自声明 `revision="CO-206.1"`）⇒ 该条款既不可满足、又无齿检出未登记者；且该工具自声明面已因 CO-206b/c 内容升级而滞留（见 F-1）。
  - 处置：CO-208（L2 自裁）：① 收窄 R-CO203-1 之**登记适用域** = 「其自声明 `revision` 为**机判/记录消费面**者」（现 = 不动点 oracle：其记录由 t28/t33 消费），并以 t33 之单件断言为**显式不变量**；② 该域新增工具时，`TOOL_REVISION_DECLARED` 与 t33 断言集须**同 commit 同源扩容**（禁单侧更新）。红线 **R-CO208-2**。
- **F-3（low）· CO-204..CO-206c**：**canonical 记录链缺口：CO-204..CO-206c 无 boundary §**（boundary 仍 v2.48、末节 = §76 CO-203；而 §1..§76 每 CO 皆有节，含全部复评/处置）。实测缺失：CO-204、CO-205、CO-206。⇒ 冻结四源/gate 链态只能从手交件与散件读取，boundary 不再是**自足**的收口面（承 CO-135/CO-136 记录卫生链）。
  - 处置：CO-208（L2 自裁）：补 §77（CO-204 绑 JLC 标准=通孔+背钻 + 两闸 + U6 热 O2）、§78（CO-205 + r/s/t 层分配族与工具缺陷 ③④）、§79（CO-206 + b/c 工艺选型 A/B/C 定案与口径修正）、§80（CO-207 本复评）、§81（CO-208 处置）；boundary **v2.48 → v2.49**。红线 **R-CO208-3**。

## 观察（不改判 verdict）

- **O-1（交接件，记录面表述陈旧（非缺陷））**：z71 §2 称打样包「牙齿 25/25」，实测生成器自检齿数 **29**（全 True，含 t11c/t11d/t15b/t16b 等后续增齿）⇒ 交接件之齿数表述滞后于工具；无功能影响。
- **O-2（CO-205t，残余（L2 已穷尽之自证））**：「增内层不改变 24/32 结论」属**结构性论证**（竖段/lane 须异层且皆须内层 ⇒ corner 内层↔内层），本件以 V9 复算其**现有量**（24/32）但未构造 10L 反例（无 10L 叠层输入）⇒ 该论证之反证责任留在 B 路（须 32/32 全落位方可选）。

## 红线

- **R-CO207-1**：复评件须钉**被评态快照**（本件 `add6e33`）且一切「现行态」判定皆由该快照重放；禁内嵌处置态之 sha（承 R-CO193-3）。
