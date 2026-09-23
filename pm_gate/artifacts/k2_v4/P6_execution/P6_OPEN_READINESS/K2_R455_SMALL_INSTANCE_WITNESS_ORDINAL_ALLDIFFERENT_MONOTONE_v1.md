# K2 · R455 —— **小实例见证**（序变量 + AllDifferent + 单调序）· #K2-155 硬闸 (a) 达成

- **ts** 2026-09-24T00:34:24 · **from** ENG·ARCHER · **to** 监理 · **owner 闸口 0**
- **authority**：#K2-155 §四.1/§四.3a（小实例见证先行）+ #K2-154 §四②（新形；禁候选集+互斥堆叠）

## 0. 一句话
**小实例见证 PASS**：新形（**序变量 + AllDifferent + 单调序**）在 ≤4 线小实例上**可解**且**与手算答案 `[0,1,2,3]` 完全一致**；**四类负控**（座位不足 / 层不足 / 强制同位 / 强制同层）**全部被拦**（INFEASIBLE）；`Validate()` 零错。⇒ **#K2-155 硬闸 (a) 达成**，全量一次性受证求解之**前置已落**。

## 1. 形（form）
ordinal vars + AllDifferent + monotone order (CP-SAT standard form)
（**无候选集**）

## 2. 可解见证
{"status": "OPTIMAL", "wall_ms": 6.8, "got": {"seat": [0, 1, 2, 3], "layer": [0, 1, 2, 3]}, "hand_known": [0, 1, 2, 3], "match": true}

## 3. 四类负控（全拦）
{"neg_A_seats_shortage": {"status": "INFEASIBLE", "expect": "INFEASIBLE", "ok": true}, "neg_B_layers_shortage": {"status": "INFEASIBLE", "expect": "INFEASIBLE", "ok": true}, "neg_C_forced_same_seat": {"status": "INFEASIBLE", "expect": "INFEASIBLE", "ok": true}, "neg_D_forced_same_layer": {"status": "INFEASIBLE", "expect": "INFEASIBLE", "ok": true}}

## 4. Validate
{"m1": true, "neg_ok": true}

## 5. 为何此形
分离性**由构造保证**（座位互异 ⇒ 门口 x 向 ≥0.435；层互异 ⇒ 带内 y 向 ≥0.435），**无需**任何「候选集 + 逐对/逐点互斥」约束 ⇒ 根除反复 0.0 秒自相矛盾之病因（#K2-154 §四②）。

## 6. 下一步（全量·一次）
按同一形上全量：每线 `seat_i ∈ 可用 18 门口位子`（IntVar）· `layer_i ∈ 南北带可用层`（IntVar）· `via_i ≤ 2`；约束 = AllDifferent(seat) + AllDifferent(layer) + 座次/层随 A 锚 x 序单调 + **几何允许值表（域过滤）**；路径由 (seat_i, layer_i) 确定性生成；**一次**求解 ⇒ 两件产物（图纸规格 + 求解证书）⇒ **在册闸验收**（全 16 条三项全 0）；跑不通 ⇒ 出**不可行证书（含不可满足核）**，**严禁删约束换 SAT**。

## 7. 边界
冻结四源 4/4 未动 · criteria/ rev=6 未动 · 未改在册工具/生成器/SPEC 设计/原理图 · 未派 WORKER · 本件仅跑**小实例玩具**（非全量求解）。

---
—— ENG（ARCHER）· 2026-09-24T00:34 · sha16 `a5b602b426d79a36`
