# CO-213 — 非执行者对抗复评（CO-207..CO-212）｜as-found 钉 `f0016ae`

- verdict：**PASS_WITH_FINDINGS**｜findings：4（全 low）｜观察项：3
- 方法：正控 V1..V11（独立复算：自板 pcbnew 普查 / 自跑闸 / as-found 工具内存重放 / 自源扫描）+ 负控 P1..P4（内存注入、零落盘）

| 控 | 结论 |
|---|---|
| V1_frozen_four_match | True |
| V2_delivery_board_pinned | True |
| V3_runner_check_all_true | True |
| V4_co206_af_independent_recompute | True |
| V5_co209_family_replay_byte_identical | True |
| V6_l5_records_pin_board | True |
| V7_package_teeth | True |
| V8_register_counts_rederived | True |
| V9_packaged_rulings_parity | True |
| V10_spec_rev7_rev19_impedance_identical | True |
| V11_boundary_sections_contiguous | True |
| P1_pin_resolver_discriminates | True |
| P2_same_sha_multi_label_detector | True |
| P3_precondition_data_flip_probe | True |
| P4_l5_board_pin_consumer_absent | True |

## Findings（as-found）

- **F-1（low，TOOL_DEFECT）· CO-211（执行器）**：**决策前置仍是代码常量（「声明↔实现」漂移的上一层）**：CO-211 把**成本臂**求值化了，但 `recommend()` 之 B **可行性前置**取 `_proven = {"B": False}` 字面量（实测 as-found 源：无 `b_feasibility`、不读 `measured_placement`），判据件 `decision.precondition_note` 仅为散文 ⇒ **判据件侧任何编辑（含把 `measured` 改为 32/32）皆不能改判**；唯一可翻转者为改 Python 常量或 t04 之内存注入 ⇒ 与 R-CO211-1「规则与其前置同处声明、实现与声明同源」不符（前置已声明但未求值；t04 之正控行使的是**不可达态**）。
  - 处置：CO-213：判据件增机读 `F4_route_predicates.B.measured_placement{placed,total}` + `decision.precondition`（谓词 `placed == total`；缺字段/退化 ⇒ fail-closed 未证）；执行器 **CO-206.3 → CO-206.4** 由该字段求值 `proven` + **数据驱动**齿 t07（只改判据件数据即改判 B / placed<total 或缺失 ⇒ A）；判据件 **v1.4 → v1.5**；重出证据件（7 齿全 True）。**R-CO213-1**。
- **F-2（low，RECORD_HYGIENE）· z77（交接件 §1）**：**政策层 pin 陈旧**：z77 §1 之 `L2_RULING_process_route_selection_v2.md` = `1542a84cf4859de6`，而该值系 CO-206b（`14bd37c`）之内容；CO-211（`86d612b`）追加 §2 R3′ 前置注记后现行 = `d258f67957a448d0` ⇒ z77 自称修正 2 处陈旧 pin 后**仍残留 1 处**（实测：全篇 36 枚 pin token 中 34 枚可解析，1 枚即此；另 1 枚为收敛快照 sha）。影响 = 续接会话之「写件时复核」指向**被取代**之裁定版本。
  - 处置：CO-213：于 **z78** 更正该 pin；「写件时复核」由 canonical 工件表扩至**政策层表格**（勿只查交付板/登记簿/判据件）。
- **F-3（low，RECORD_HYGIENE）· boundary（写入器机制）**：**「现行态 pin 再对齐」只改 sha、不改同排历史版本标签 ⇒ 同排标签↔sha 可不同版**（系统性）：实测 §79 两行标 `CO-206.2`/`v1.3` 而 pin 已为 CO-206.3/v1.4 之内容（`git show a5cbcb6` = `dea2bbeb89e6fe54`/`e53fc2354e8efd59`；`86d612b` 起被再对齐）；全表同文件同 sha 对多枚历史标签之行**数十处**（负控 P2 探测器实测冲突文件数 = **60**）。§79 并残留 CO-211 已证伪之「（已编码，填参后自动复算）」表述**且无 §84 指针** ⇒ 读者可据行内标签误判版本。
  - 处置：CO-213：机制**不改**（现行态对齐为有意设计；逐行改写 456 处历史标签反致伪史）⇒ §79 补**追注**（标签 = 成文时口径 / sha = 现行实件）+ §86 显式登记该语义。**R-CO213-2**。
- **F-4（low，TOOL_DEFECT）· CO-212（L5 自检）**：**板指纹判别齿过弱 + 消费面无机判**：CO-212 之 `board_pin_discriminates` 只判「`board_sha256` ≠ 全零哨兵」，**不判别「评的是冻结源还是交付板」**（二者互换而齿不响）；且全工具集扫描：读三件 L5 记录者 **14** 件、含 `board_sha256` 者 **4** 件，**消费者（读记录 ∩ 含板指纹，除生产者）= ∅** ⇒ 板变更后记录不刷新仍**只对人眼可见**（序内/各闸皆不验）。
  - 处置：CO-213：自检改**真判别**（DFM `baseline_sha256` 须 = 冻结源板、被评板 ≠ 冻结源、三件皆钉被评板且非退化 ⇒ 「评错板」即 rc≠0）；记录 **L5-DFM.8 / L5-SI.8 / L5-G7.8**；**消费面机判**列**有据延后**（触发 = 板变更或下次 L5 重跑）。

## 观察（不改判 verdict）

- **O-1（z77 §2，记录面表述易误读（非缺陷））**：z77 称「收敛 sha … report `.archer_tmp/co164_order_report.json` sha16 `645d544efcdacbdf`」—— 该值实为报告内 `iterations[*].sha`（**受控集快照**），非报告文件自身 sha（实测文件 sha16 另一值）；判定一致，仅措辞易误读（z78 改称「收敛快照 sha」）。
- **O-2（CO-209，已直接行使（复核通过））**：「band 级列×桥孔 x 联合形态」之族闭合已由**直接行使**证（19–20/32 < 24/32），本件逐字节重放其求解器（V5）复核数值与结论一致；残余自由度 = 跨页 y 交错（须改几何，非旋钮可达）与 L1（球重映射/信号流向）—— 与 z77 §6 一致。
- **O-3（复评覆盖边界，诚实边界）**：本件复评 CO-207..CO-212（CO-202..CO-206c 已由 CO-207 复评）；**未**复核 B 路 10L 叠层之实做与外部报价面（前者须 L1/几何，后者为外部输入）。

## 红线

- **R-CO213-1**：决策规则之**前置**须与规则同处声明并由**判据件机读字段**求值（禁代码常量）。
- **R-CO213-2**：boundary 为**现行态对齐**；同排历史版本标签不得作为 sha 之版本判据（判版本读该节现行版本注）。
- **R-CO213-3**：复评件须钉被评态快照（承 R-CO207-1）；findings 之「修后」证据须为本会话实测。
