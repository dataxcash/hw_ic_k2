# m13 v57 — **W4/G5 开工卡 v1**（真图验证：A1.2 / A1.3 / A1.4）

> 2026-09-11｜依 `EDA_AUTONOMOUS_EXECUTION_PLAN_v2.md` G5 行｜DOR：W3 完成（FEASIBLE_ALL）
> DOD：A1.2/A1.3/A1.4 报告覆盖**全部 34 页与所有强节点**；**不接受 partial pass**；独立验证。

## 1. 范围与输入
- 输入：`m13_v57_w3_joint_assignment.json`（rev W3-CN.22，FEASIBLE_ALL）+ `m13_v57_w3_chip_landing_rows.json`（F-12）
  + 冻结四源（SPEC/manifest/PCB/rules，MATCH）。
- 覆盖：34 页 = 32 data + 2 REFCLK；强节点 = 每 data 页 chip/conn 锚 ×2 + 全部 via + 每 REFCLK 页 witness 锚 ×2。

## 2. 三条验收（机器可判，独立于发射器）
| 门 | 判据 | 工具 |
|---|---|---|
| **A1.2 序无关** | 同输入三枚举序（natural/reverse/hash，**输入页序置换**）→ 主件 + landing **逐字节一致**（sha256 相同） | `p3_v57_w3_constructive_validator_v2.py`（黑盒 subprocess） |
| **A1.3 生成即合法** | 图纸节点过几何不变量套件 **V1–V7**（V1 锚定只读 / V2 via 数 / V3 via 在层翻转点 / V4 段层长度 / V5 差分对中心距 0.38 / V6 P/N 铜边距 ≥0.155 / **V7 REFCLK 路径端点=witness 锚、层 F.Cu**）**零违例** | `p3_v57_s1_invariants.py`（套件，独立于引擎）+ v2 验证器 |
| **A1.4 单向性** | 生成器无 `x-window/max-x/board-file 反猜`；运行期不读板文件；锚字段引用白名单 = 冻结输入 | v2 验证器 grep 门 |

## 3. W3 契约修订（按 ROOT-1 生命周期，**版本化记录**、不原地改）
- **V2 `max_vias_per_net` = 5**（原 S1 = 2）：依 **ROOT-2 R-74**（受影响线 via ≤5 = 2 次 hop），并经 owner A 授权链。
- **V3 `LAYER_PAIRS_OK`** = {F.Cu, B.Cu, In2.Cu} 两两合法对（原仅 F.Cu↔In2.Cu）：依 **ROOT-16/ROOT-1** 可用信号层 =
  {F.Cu, In2.Cu, B.Cu}（In4 仍电源平面，HARD）。
- **V7 新增（REFCLK）**：REFCLK 页纳入本套件（补偿 caveat：REFCLK 不在 W3 两度量口径内）。

## 4. 判定准则
- 三报告 verdict 均 `PASS` **且** v2 验证器 `verdict=PASS`（G-M1..G-M6 + 双度量 + 序无关 + 四源）⇒ **G5 PASS**。
- 任一 FAIL ⇒ 退回 W3（不得 partial pass）。
