# CO-08 — 【整改 #07】L2 定层纠正：叠层重排/过孔预算 = **L2**（本裁定取代 CO-07 的 owner 请求）

> 2026-09-11｜裁判：ARCHER（L2 域）｜性质：**变更单**（版本 bump；冻结四源**原件不动**）
> ｜触发：整改通知 #07 —— CO-07 把 (A) 叠层重排 / (B) SPEC via 预算 误列为 L1 owner 决策（第二次定层错误）。

## 0. 撤回
**撤回** CO-07 §6 / §"结论(owner)" 中对 owner 的升级请求。按 `LAYOUT_CONSTITUTION` 第二章：
- **(A) 叠层（信号层）分配 / 重排 = L2**
- **(B) SPEC `high_speed.max_per_line`（过孔策略/SI）= L2**
- 仅 **(C) 拓扑 / 球重映射 = L1**（触器件分区/信号流向/球映射）。

## 1. L2 裁定
### (A) 叠层重排 — **评估后不采用**（闭合反证）
平面隔开的叠层中，从 F.Cu 出发**不穿透其它信号层**（1-hop）可达的内层**至多 1 个**（首个内层信号层）。
交换信号层次序只能把这个"唯一 1-hop 内层"在 In2/In6/B 间挪动，**不能让两个内层同时 1-hop**。
⇒ 两带 escape 无法各自 1-hop 落不同层 ⇒ 逃逸密度/安全 hop 冲突**不因 (A) 消除**。故 (A) 单独**不可行**（闭合）。

### (B) SPEC `high_speed.max_per_line` — **采用：2 → 4**
采用**安全 hop 链**：`F↔In2 → In2↔In6 → In6↔In2 → In2↔F`（4 via/线；所有 hop 不穿透信号层）。
- dn/up 统一拓扑：`chip pad --F.Cu 逃逸扇--> via1(F↔In2)@(vx,ly) --In2 短横--> corner(In2↔In6)@(cx,ly)
  --In6 lane--> (lx,ly) --drop(In6↔In2)--> (lx,ly_l) --land(In2↔F)--> conn pad`。
- 层职能：**F.Cu** = 芯片逃逸扇 + 落列 breakout；**In2** = 短横段 + 落列竖段(stub)；**In6** = 走廊 lane。
- **容量判据（确定性）**：
  - In6 lane 按 R2 lane 槽（1.46mm）单层可行（互异 y）；
  - In2 仅"短横段(在 ly) + stub(在 lx)"，二者 x 域不相交（cx < min lx）⇒ 不交；
  - F.Cu 逃逸扇须**平面**（单调 fan：按 lane 序与 pad 序一致 ⇒ 无交叉）；
  - via 全部 ∈ {F↔In2, In2↔In6} ⇒ 端点层检查**即精确**（无跨层桶风险）。
- 对比：CO-07 实测 A（escape 竖段落 In2）失败根因是**竖段密度**；本拓扑把竖段改为 F.Cu 扇出+In2 短横，**取消 In2 上的长竖段** ⇒ 密度约束解除。

### (C) 仅在 (A)+(B) 组合仍闭合反证不可行时才上抛 owner（本轮不触发，若实现出现证书再评估）。

## 2. 变更落地（版本 bump，原件不动）
- 引擎 `tools/p3_v57_w3_constructive.py` rev **W3-CN.32**（安全 hop 拓扑）。
- SPEC 修订**不改原件**：以本 CO-08 + 版本化 ECO 记录 `high_speed.max_per_line: 2→4`；引擎以**显式常量**采用并在工件标注 CO-08。
- 冻结四源：SPEC `0bd52ed4` / manifest `a8ef3ea8` / PCB `fb07d25a` / rules `0a459839` 均**不动**（4/4 MATCH）。

## 3. 验收
- 本裁定可复核（本章 §1 闭合论证 + CO-07 实测 A/B 证据）；
- (B) 变更落地（引擎 W3-CN.32 + ECO）；
- 重跑 G4→G7：G4/G5/G6 PASS、G7 评估（DFM new 目标 0）。
