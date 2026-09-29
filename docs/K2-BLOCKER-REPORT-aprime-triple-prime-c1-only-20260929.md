# 卡点报告 · A‴ = **只差 C1**（C2 首次通过）— #K2-390 §七 两序步执行

- 授权：#K2-390 §七（步① 零考跑孤岛处置 ＋ 步② 授权跑恰一次 `N=1`）
- 件：判卷 `L2/EDA_ENG_EXAM_A_TRIPLE_PRIME_ATTEMPT1_VERDICT_v1.json` · 记录 `…_ATTEMPT1_RECORD_v1.json` · 方案件 `L2/A_DOUBLE_PRIME_PLACEMENT_POUR_PLAN_v1.json` · 测试 `L2/EDA_ENG_TESTS_84_v1.txt`

## 一、人类口径三问

1. **信号怎么走**：小片器件按新布局挪位 → 清掉框内铜 → 框内用仓里流程重接 22 条网 → 复敷铜 → **把复铜后成孤岛的填充确定性处置掉** → **板干净才准入判卷** → 判九行。
2. **挡路的是什么**（本次只剩一条）：**18 处线头接不上**，且**全部卡在端点**（迷宫在这些点**找不到空起点/空终点**：`no-free-start-node` 14 · `no-free-goal-node` 4）。**阻焊桥与孤岛铜两处已归零。**
3. **人类方案（下一次一次做 · 确定性）**：**把框边被切开的 stub 当「合法端口」直接发给迷宫**（起点/终点就用这些 stub），**不要跨块另猜目标点** —— 这是方案件 **edge iii（端口层）**，**本窗未授权实施**。

## 二、本窗两序步（逐条）

| 步 | 交付 | 机证 |
|---|---|---|
| **步①（零考跑）孤岛的确定性处置** | `route.dispose_isolated_copper()` ＋ CLI `dispose-islands` ＋ 链内阶段 `isolated_copper_disposed`（**在落板前置之前**）：**DRC 点名的每个孤岛 ⇒ 按其 zone UUID 定位 ⇒ 移除该 zone 填充 ⇒ 仅其余 zone 重填**（一次 · 确定性 · 不搜索）。回归两例（有孤岛⇒拒 / 无孤岛⇒放行）＋ 路径感知/顺序回归 | 实验：**强制 `IslandRemovalMode=ALWAYS` ＋ 重填＝无效**（KiCad 保留挂到焊盘的岛）；**移除该 zone 填充＝有效**（隔离铜 3→0，unconnected 不增）。A‴ 实跑：`n_disposed=2` · 落板前置 `n=0 pass=True` |
| **步②（授权跑 · 恰一次 `1/1`）** | 入口 `exam A --run --chain wipe_resolve --from-placed <A‴ gate-clean 板>`；**C34 闸命中入口＝PASS** | **九行齐**（含 `C8`）· `run_count=1/1` · `verdict=FAIL` |

## 三、判卷读数（**九行齐** · 首次 C2 通过）

| 行 | 读数 | 判 |
|---|---|---|
| C1 未接 | **18**（attempt2/3 为 22） | ❌ |
| **C2** | **136 vs 148（raw 190/168）· `new_classes = []`** · 排除库解析类 | **✅（首次）** |
| C3／C4／C5 | 0.0788mm ≤ 0.15 ／ 2843 ≥ 2637 ／ diff 1674 | ✅ |
| C6／C7 | **0 ／ 0** | ✅ |
| **C8** | **0**（成员零越框） | ✅ |
| C9 | 摘要已报（`678d0cbe91f8ba87`） | ✅ |

**几何类净增 −12**。终板 DRC：`solder_mask_bridge = 0` · `isolated_copper = 0` · 无 clearance/shorting。**C2 首次通过**（两类新违规**全消**）。

## 四、归因（只有一条残余 · 且是新一层）

- **已关（本窗）**：阻焊桥类（**布局闸补规则＋重出布局**）· 孤岛铜类（**确定性处置＋落板前置**）。
- **残余**：**C1＝端点层**（`no-free-start/goal-node`）⇒ **方案件 edge iii（端口层）未实施**。
- **裁决分支**：**FAIL ⇒ 停 ＋ 当件回方案层（§16）**；`C35`／`M-ENG-POUR-MASK-AWARENESS(ii)` **保持开**（关账判据＝A‴ 全表 C1–C9 PASS）。

## 五、产物路径机器核（承 #K2-390 §六 `M-ENG-EVIDENCE-PATH`）

| 路径 | 实测 |
|---|---|
| `L2/EDA_ENG_EXAM_A_TRIPLE_PRIME_ATTEMPT1_VERDICT_v1.json` | 存在 |
| `L2/EDA_ENG_EXAM_A_TRIPLE_PRIME_ATTEMPT1_RECORD_v1.json` | 存在 |
| `L2/A_DOUBLE_PRIME_PLACEMENT_POUR_PLAN_v1.json` | 存在 |
| `L2/EDA_ENG_TESTS_84_v1.txt` | 存在 |
| 终板（**derived · /tmp · sha `c95da3b8eb14b13d`**） | `/tmp/opencode/aprime_triple_final/s3c_disposed.kicad_pcb`（**不入库**：仓规禁止无 SPEC 变更提交 `.kicad_pcb`） |
| A‴ 见证板（**derived · /tmp · sha `32d3c644692c564d` · 重导配方在场景件内**） | `/tmp/opencode/aprime_triple_witness/placed.kicad_pcb` |

> 说明：**派生件一律显式标注 `/tmp` ＋ sha ＋ 重导配方**（本表即 `M-ENG-EVIDENCE-PATH` 的关闭动作；下窗报告继续逐条机核）。

## 六、纪律 / 边界

- **本窗链跑合计＝1**（步②恰一次 `1/1`；步①零考跑）；`aprime_witness` 冻结维持；**无新授权而跑＝违规**。
- 板面冻结（板只在 `/tmp`）· 冻结四源 4/4 · 判据表一毫米不改 · 禁 WORKER · 收尾脚本每收执一次。
- 仍待裁：`regen.exam_a_chain` 未定义名 `rp`/`blocked`（既有 · 未修 · 越窗）。
