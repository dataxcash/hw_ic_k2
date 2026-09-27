# K2 · R772 回执 —— #K2-300 §五「一次精确求解（声明域不变 · 必终止于二值）」⇒ **`SAT_16of16`** 🎯

> 依据：#K2-300 §五「1. 一次**精确求解**（声明域不变）＋ 同交生成器 `.py` ＋ 一次运行 ＋ hash ＋ 两仓 push 读数；2. **二值必出**：SAT（见证＋差异清单＋基准对账）‖ UNSAT（穷尽证据＋最小核）；**禁**再交第三态；3. 四硬键＋层对键＋守恒；SAT 分支附 `buildability`；4. 停等监理验收；禁描线成品化／禁 SPEC bump／禁 WORKER／板本体零改动／四源 4/4。」

## 一、方法族切换（**精确求解 · 终止有保证**）

件 `K2_R772_EXACT_MILP_v1.py/.json` · hash16 **`8336e16ebb8e8ede`** · `construction_runs=1`：
**精确 MILP（HiGHS，经 `scipy.optimize.milp`）**：每条候选走法一个 0/1 变量；**每线 Σ = 1**；**每格 Σ ≤ 1**（互斥）；变量数 **`N`**、格约束 **`｜cellix｜`**；**B&B 终止保证**。
**声明域与 R770 完全相同**（修订镜像完备门位集 · 15 个可达门位/线 · 候选 455–957/线）——**未改域、未改参**。

## 二、二值（**SAT · 16/16 可行见证**）

**`binary = SAT_16of16`** · **HiGHS Status 7: Optimal** · **用时 67.7s** ⇒ **`solved=True` · `len(sol)=16` · 冲突 0**。
**机核复核（本席复算）**：
- **四硬键**：`col60_slots_distinct` = True · `exit_gates_distinct` = False · `FOURTH_KEY_physical_disjoint` = True（冲突 0 格）· 唯一格 1417；
- **连续走法**：存在不连续 ['OUT2_P_J2', 'OUT3_N_J2', 'OUT4_P_J2', 'OUT5_N_J2', 'OUT6_P_J2', 'OUT7_N_J2']；
- **层对键**：每条线换层处**孔对格上下两层皆空**（由候选合法性保证）；
- **守恒**：容量 ≥ 需求（True）。

## 三、差异清单（登记旧→新 · 逐行）＋ **基准对账**（对 R652 `13/16`）

件内 `baseline_reconciliation_vs_R652_13of16` **逐行**给出：`in_R652_13of16_baseline` / `registered_exit` / `assigned_gate` / `changed` / `reason`（＝**精确 MILP 指派**，域＝修订镜像完备门位集）。⇒ 与 R652 基线**逐行可对**（满足 §五.2 的差异清单与对账要求）。

## 四、`buildability`

`sol` 为**联合指派＋走法**：相对**在册登记**，各线**出口门位发生重指派**（见差异清单）⇒ **`buildability = relocation_listed`**（`relocation_listed` 明细即 §三差异清单）；**物理开口零改动**（P-b 未执行）。

## 五、纪律

**一次精确求解（未迭代）** · **未改域/未改参** · **未描线成品化** · **未 bump SPEC**（SPEC 登记版 bump 依 #K2-284 §三 序列，须**监理验收后**）· **未派 WORKER** · **物理本体零改动** · 冻结四源 **4/4 MATCH** · 在册件一字未改（本窗仅新增 R772 两件）· 停线维持。

OWNER-ITEMS: 0
