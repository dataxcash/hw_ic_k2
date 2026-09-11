# CO-07 — L2 裁定：8L 层/过孔策略（逃逸拓扑仅允许信号层相邻 hop）

> 2026-09-11｜ARCHER（L2 裁决权内）｜依据：`m13_v57_CO06_dfm_clearance_model_gaps.md` §5 的构造不可行证书

## 裁定
信号层物理序 `F(1)–In2(4)–In6(7)–B(8)`（In1/In3/In4/In5 为 GND/P3V3）下：
1. **允许**过孔：`F↔In2`、`In2↔In6`、`In6↔B`（不穿透任何**其它**信号层）。
2. **禁止**过孔：`F↔In6`、`F↔B`、`In2↔B`（穿透 In2 或 In6 信号层 ⇒ 与 foreign 铜短路）。
3. 由此，**每线 ≤2 过孔（SPEC）⇒ 只能用单一内层 In2**（F→In2→F）。
   W3 的 escape/lane/stub 须重新派生为 **In2 单层平面 river**；R1/R2 的 frame/lane 行序可作为初值。
4. 若单层 river 不可行、或需改每线过孔数 / 信号层次序 / 反钻 ⇒ 属 **L1**，上抛 owner（叠层/拓扑）。

## 影响文件（下一工作周期）
- `tools/p3_v57_w3_constructive.py`：R1.5/R2/R3 拓扑（escape/stub 层、corner/drop via 语义）、`_mk_index`/`_vt_*` 谓词。
- `p3_v57_w3_constructive_validator_v2.py`：合法层对/重导契约同步。
- SPEC `high_speed.max_per_line` 若走 (b) 需 owner 修订（冻结源 → 只走变更单）。
- 冻结四源：**均不改**（走新版本工件 + 变更单）。
