# K2 · **N-2 落件阻塞（bom_consistent）** + **N-1/N-6/N-7 册面落档**（#K2-48）

- 阻塞件：`…/P6_OPEN_READINESS/N2_K1_LANDING_BLOCKER_BOM_CONSISTENT_20260921_v1.json`（sha16 `c94114c0edf01d5c`）
- 落档件：`…/P6_OPEN_READINESS/N1_N6_N7_RECORD_20260921_v1.json`（sha16 `8fa73a0b8eefe18f`）
- 日期：2026-09-21 · ENG(ARCHER)

## A. N-2 **停机**（冲突即停机·第九条）
3 件机制包**已备齐并实测**，但 **pre-commit meta-gate 拒绝提交**（`k1: 漏声明必选 sch checks ['bom_consistent']`）⇒ **未入库**；`k1` 已回退至洁净 `dc720fd`。

**根因**：`_shared/eda_core/pipeline/required.py` 的 `REQUIRED_SCH_CHECKS = ("sch_structural","netlist_connect","bom_consistent")` 是**常量**；凡含 `.kicad_sch` 的项目必须**全声明**，否则拒绝提交。而 `bom_consistent` 需 `bom_csv`，**K1 仓无任何 BOM**（`k1/fab/` 不存在）⇒ 只声明不加件会让 `verify` fail-closed。

> 提案件**已预警**此点（『样例未含 bom_consistent … 须 K1 侧定』）。

**已实测（落件前）**：K1 判定 18 维（`ref_plane_continuity` enabled=false）：**基线 4 PASS/14 FAIL → 落件 7 PASS/11 FAIL**；翻转维 = `rule_severity_manifest` · `fp_lib_table_present` · `pipeline_present`（**恰为 3 目标维**）；**0 新失败**。（提案镜像记 5→8 = **常数 +1 偏移**；已诚实登记。）

**择一（监理自裁·无 owner 闸口）**
- **(a) ENG 建议**：补 `k1/fab/k1_v1_bom.csv`（**ref 集由 sch netlist 机械派生**，格式同 `k2/fab/k2_v4_bom.csv`）+ 声明 `bom_consistent`；并**建议 N-2 与 N-3 合为同批**（BOM ref 集随 37→42 一次成型）。
- (b) 覆写必选清单 ⇒ 改 `_shared` ⇒ 须监理批 + 两树同步。
- (c) 撤回 N-2（不推荐）。

**重放命令**（裁定后一步到位）：见阻塞件 `measured_before_block.reapply_cmds`。

## B. N-1 / N-6 / N-7 册面落档
| 项 | 裁定 | 落档要点 |
|---|---|---|
| **N-1** | **(a) 接受 + 随单注明**（**不动交付锚**） | **未重建包**（`6ee7495d…`/`0e88e107…` 冻结）；B-1 叠层以 `03_stackup` 为准（job 内 MaterialStackup 系工具默认）；B-2 ENIG / P5-1 阻抗券 = **商务下单页**（#14④ 非 ENG）；P5-2 编号乱序接受（以 §5b-**标题**为准）。**因包冻结，注明不写入包内，本件即唯一落档。** |
| **N-6** | **接受** | `measure_source_reconcile.py` 未落件 ⇒ 注明『**判据换址、非缺失**』，由 rev=3 三维承接。 |
| **N-7** | **确认达成** | P6-1 `k1` verdict `provisional=False` 四项同源命中 PASS · P6-2 `k2` ignore=0/结构差异 0/10 PASS；**P5 外部门仍关**（未越阶段）。 |
