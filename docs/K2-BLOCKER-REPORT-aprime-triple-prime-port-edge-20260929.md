# 卡点报告 · A‴ 第三边（端口感知目标）实现 — #K2-392 §二.1

- 授权：#K2-392 §二.1「实现方案第三边：端口感知目标（增量、带单测、一窗一件）」；**零 exam 跑**
- 件：`L2/EDA_ENG_EXAM_A_TRIPLE_PRIME_PORT_EDGE_MEASUREMENT_v1.json` · `L2/EXAM_A_TRIPLE_PRIME_AUTHORISATION_APPLICATION_v2.json` · `L2/EDA_ENG_TESTS_86_v1.txt`

## 一、人类口径三问

1. **信号怎么走**：小片器件挪位 → 清框内铜 → **框内**重接 22 条网 → 复敷铜 → 孤岛处置 → 判九行。
2. **挡路的是什么**：**18 处接不上**，且**全部卡在端点**；其中**多数端点在"框外"**（框被 C35 封死 ⇒ 迷宫在界内找不到该网可落的格）。
3. **人类方案（本窗已实现）**：把**框边被切开的残段（端口）当目标** —— 该网铜在框外继续，**接到端口＝恢复连通**；迷宫不再跨框另猜目标。

## 二、实现（**不改迷宫本体** · wrapper 运行期打补丁）

- `tools/k2_reroute_router_floor_v1.py :: _install_port_aware_goals`：`solve_edge` 正常失败
  （`no-free-start/goal-node`）时，取**同网 ∂R 端口**（∂R 上的 track 端点，按 `(layer,x,y,uuid)` **确定性**排序）
  作**目标或起点**重试；并对**端口点**做**定向 snap 松绑**（允许落在端口格），**最终仍由放行闸 `seg_exact/via_exact` 判定**。

## 三、实测（A‴ 擦铜板 · 同参数 · dry-run）

| | edges | added | blocked | reasons |
|---|---|---|---|---|
| 补丁前 | 80 | 59 | **21** | no-free-start 17 ／ no-free-goal 4 |
| 补丁后 | 80 | **73** | **7** | no-free-start 6 ／ no-free-goal 1 |

⇒ **端口这一边关掉 14/21**（added +14）。

**残余 7 的具名归因（诚实）**：**端点拥塞，不是没有端口** —— 以 `PERSTA#` 端口 `(51.5,37.5,In5.Cu)` 直测：
`node_in_island=True` 但 `snap_node=None`（边界格因邻近异网铜被剪枝）；且这些边**另一端本身也埋** ⇒「a→端口」「端口→b」皆不通；
`P3V3` 则**根本没有 ∂R 端口**。⇒ **C1 预期由 18 改善到约 7，但本边独自不可能到 0。**

## 四、单测（增量 · 先 RED 后 GREEN）

- `test_C392_port_aware_goals_use_the_wall_ports`（**桩对象**：端口重试命中 ⇒ `ok-port*`；非同网 ⇒ 行为不变）
- `test_C392_the_floor_wrapper_installs_port_goals_only_with_a_wall`（**仅在设框时**安装 ⇒ C35 域内语义不放松）
- 套件 **86/86**。RED 证据：`fe6621a` 版 wrapper **无** `_install_port_aware_goals`。

## 五、结论与申请

- 第三边**已实现并实测有效**；A‴ 的 **C2 仍应 PASS**（R1082 已证），**C1 预期改善但**（据实测）**不一定归零**。
- 已按 #K2-392 §二.2 **申请**新考卷窗（`run 1/1`，申请 ≠ 自跑）：见 `L2/EXAM_A_TRIPLE_PRIME_AUTHORISATION_APPLICATION_v2.json`（**含诚实预期读数**）。
- **本窗零 exam 跑**；板面冻结（板只在 `/tmp`）· 四源 4/4 · 判据表一毫米不改 · 禁 WORKER。
- 仍待裁：`regen.exam_a_chain` 未定义名 `rp`/`blocked`（既有 · 未修 · 越窗）。
