# 卡点报告 · EDGE IV 步①（端口可达性预检）＝ 已交 · 步②③ 需监理择路 — #K2-394 §二

- 授权：#K2-394 §二（**零考跑窗** · 语义硬约束）；本窗**零 exam 跑**
- 件：`L2/EDA_ENG_PORT_REACHABILITY_PRECHECK_A_TRIPLE_PRIME_v1.json` · `L2/EDA_ENG_TESTS_87_v1.txt` · 方案件 `L2/A_DOUBLE_PRIME_PLACEMENT_POUR_PLAN_v1.json :: edge_iv_status`

## 一、步①「端口可达性预检」＝ 已实现并实测

- **落点**：`tools/k2_reroute_router_floor_v1.py`（wrapper）——`_install_port_aware_goals` 现**返回预检记录**，`main` 落盘 `<ledger>.precheck.json`；**不改在册迷宫**。
- **读数（A‴ 擦铜板 · 同参数 · dry-run）**：失败边 **21** ⇒ **14 可达某个同网框端口**（端口这一边已把它们接上）· **7 不可达（具名）**。
- **具名 7 + 子因**：

| 网 | 框端口数 | 子因（预检实录） |
|---|---|---|
| NRST | 1 | goal 向：`no-path-coarse(exhausted)`；start 向：`no-free-goal-node` |
| PERSTA# | 1 | goal 向：`no-free-start-node`；start 向：`no-path-coarse(start-blocked)` |
| GND | 1 | goal 向：`no-free-start-node`；start 向：`no-path-coarse(start-blocked)` |
| MCU_VDD | 3 | 三端口：`no-free-start-node` ＋ `no-path-coarse(start-blocked)` |
| NRST | 1 | `no-free-start-node` ＋ `no-free-goal-node` |
| P3V3_AUX | 4 | 四端口：`no-free-start-node` ＋ `no-free-goal-node` |
| **P3V3** | **0** | **无框端口**（须全在块内另导 —— §二.3 子例） |

## 二、步②③「确定性开端口」的**可行性实测**（诚实 · 需监理择路）

- **实测**：这 7 个端点**0.6mm 内没有异网（含变更集网）铜** ⇒ 「**消费变更集铜来开端口**」在本例**不适用**。
- 真实子因是：**(a) 另一端本身 snap 不上**（挪位后拥塞把内侧 pad/残段埋了）· **(b) 端口格即便 snap 松绑，仍被粗 A* 判 `start-blocked`**。
- ⇒ 依 #K2-394 §二.2／§二.3，触达这 7 条需下列**三者之一**（**均属方案层**，超出本窗步①）：
  1. **A* 级**接受拥塞端口格 ＋ 拥塞疏解；
  2. **扩成员集**（新围邻入集 → 块边界重画 → **C7 互斥重校** → **C6 重述为「新框外 diff=0」**）；
  3. **微调该端点所属成员件**（§二.3 自治）。

## 三、结论

- **步① 已交且有效**（14/21 由端口闭合；不可达 7 具名）。
- **步②③ 不可在变更集内完成** ⇒ **未申请末跑**（现在跑必再 FAIL ⇒ 违「禁同因重跑」）。
- **请裁**：批**一次「零考跑」方案层窗**，从上列 1／2／3 中择一（建议先做 **2 扩成员集**，因其同时覆盖 `P3V3` 无端口子例与内侧埋压）；随后**过验再申请** `N=1` 末跑。
- 板面冻结 · 四源 4/4 · 判据表一毫米不改 · 禁 WORKER · 链跑合计＝0（本窗零考跑）。
