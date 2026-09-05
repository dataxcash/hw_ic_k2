# M13 v22 — 6L 走廊闭合工具背书（capacity_audit，走廊闭合已被工具验证）

> 状态：**生产链 ③计算/⑦冻结 工具级背书**（EXECUTION_PROCESS §2）。替代 v21 前 precheck §2 的
> "1.46 手推口径"——评审阻塞项 §2.3（"走廊闭合需工具背书"）**已闭合**。
> 引擎 = edacore `capacity_audit`（只读调用，零引擎改动）。数据源分级：`[L0]` 真板几何 /
> `[L1-L2 frozen]` 走廊表 + 已裁 inter_pair_spacing（v22 用户裁决）/ `[E]` 引擎契约。

## 0. 本轮裁决前提（脱待裁定）

- **inter_pair_spacing 已裁决（v22 用户 2026-09-05）**：R3-2「0.875」= 对间铜边净空 →
  对中心距 = 0.585 + 0.875 = **1.46mm**。引擎 `capacity_audit` 按对中心距计，经
  `route_model_config.json → capacity_audit.inter_pair_spacing = 1.46` 注入（勿用 drc_rules.json 0.875）。
  已回写 L1/L2 frozen 硬约束 2/3（"语义待裁定" → 已裁）。

## 1. 审计输入（6L corridor SPEC，由 L2 frozen 走廊表 + 真板几何编码）

- 板框 y∈[33,79]=46mm；芯片 U1 体包络 y[49.2,58.2]，x[82.35,105.25] → **N 窗 [33,49.2]=16.2mm、
  S 窗 [58.2,79]=20.8mm**。
- F.Cu 数据带（每侧 16 对/32 网 split 2 带 × 8 对）：
  | 走廊 | x 净跨 | band | 窗 | 轨距 |
  |---|---|---|---|---|
  | 东(芯片↔J2) | [105.25,132.65] | UP_OUT / DN_IN | N / S | 1.46 |
  | 西(MCIO↔芯片) | [65.05,82.35] | J3_N / J4_S | N / S | 1.46 |
- In2 翼带（穿越 32 网）：via_zones WING_N(span 16.2)、WING_S(span 20.8)；16 对穿越按 N/S 翼各 8 对。
- **非循环口径**：N/S 窗以 0.1mm 密排喂入，引擎按 inter_pair_spacing=1.46 `_pack_lanes`
  求窗内真实可容纳对数（非手塞 8 对接 8 需求）。

## 2. 引擎结果（`capacity_audit_6L_corridor_report.json`）

```
verdict = FEASIBLE   global_pressure = 0.64   bottleneck_stage = TRACK
TRACK: capacity_total=50  demand_total=32  ok=true  pressure=0.64
  E_J2|UP_OUT   窗内 packed_capacity=11  demand=8   N 窗(16.2mm)
  E_J2|DN_IN    窗内 packed_capacity=14  demand=8   S 窗(20.8mm)
  W_MCIO|J3_N   窗内 packed_capacity=11  demand=8   N 窗
  W_MCIO|J4_S   窗内 packed_capacity=14  demand=8   S 窗
VIA: capacity_total=69  demand_total=32  ok=true  pressure=0.464
```

## 3. 判定（走廊闭合 = 工具背书 ✓）

1. **每侧 16 对 / 32 网**：东 J2（UP_OUT 8 + DN_IN 8）、西 MCIO（J3_N 8 + J4_S 8）——每侧 16 对。
   F.Cu 数据带 8 对/带 × 2 带；带内轨距 1.46（已裁口径）。
2. **窗内容量**：N 窗 16.2mm → 11 对（>8，余 3）；S 窗 20.8mm → 14 对（>8，余 6）。
   带内 8 对显著富余；**非 knife-edge**（precheck "0.6 均匀网格 knife-edge" 的过度保守已由引擎校正）。
3. **In2 穿越**：via_zones 容量 69 > 需求 32（压力 0.464），穿越 16 对（32 网）放得下。
4. **无禁区阻碍**：数据带全部在芯片体之外（x 上不穿越芯片，y 上在 N/S 窗外），`encroachment` 仅
   沿窗边的 2 条边界轨（微小贴边，已被 packed 容量扣减），不影响带内 8 对。

**结论：走廊宏观闭合 = 引擎工具级背书（FEASIBLE，压力 0.64，余量 N≈3 对 / S≈6 对）。**
走廊（横截 + x 净跨 + In2 翼带 + via≤2）不再是层数决定性项；**决定性项仍只有逃逸密度（见 ESCAPE_GAP_v22）**。

## 4. 关联

- 数据源：L2_STRUCTURE_v2.0 走廊表（冻结）、真板几何（[L0] precheck §2）、规则 = drc_rules.json +
  route_model_config.json capacity_audit.inter_pair_spacing=1.46（v22 裁决注入）。
- 引擎 = edacore 只读调用（`from eda_core.capacity_audit import ...` 语义；零引擎改动，符合"勿改引擎"）。
- 产出供：本工件 + ESCAPE_GAP_v22（层数定案的决定性缺口 = 逃逸，非走廊）。
