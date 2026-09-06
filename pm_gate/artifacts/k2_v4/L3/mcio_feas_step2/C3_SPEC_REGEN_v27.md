# C3 记录 — SPEC 再生对齐评估 + ⑦ 生产接线修复路径（2026-09-06）

> 状态：**机制级实证 = evaluated FEASIBLE；SPEC 本体再生 = 缺口登记（依赖真板 ECO）**。
> 评审条件 C3：「SPEC_k2_v4.json 再生对齐 L1/L2 v2.0（DS320PR1601/6L/46mm 单面）+ 注入
> components.redriver.<ref>.bga_escape.per_ball → 跑真实 routing_topology_gate.plan() →
> ⑦ = evaluated FEASIBLE（消除 not_configured 假静默）」。

## 1. 基线复现（2026-09-06，生产接线断裂机器实证）

对生产工件跑 `RoutingTopologyGate.plan()`（v1.3 → v1.4 ECN 后）：

| 输入 | 路径 |
|---|---|
| board | /tmp/opencode/boards/k2_v6.kicad_pcb（卡0落位板） |
| spec | k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json（**旧 U3/U7/8L**） |
| alloc | .../L3/model_solves/channel_alloc_v4/channel_alloc.json |
| rules/config | _shared/eda_core/drc_rules.json + L2/route_model_config.json |

基线：`verdict=FEASIBLE_WITH_MORPH_GAP`，**⑥=not_configured、⑦=not_configured**
（ok=True 静默过）——评审 C 段"生产接线断裂"实证。

## 2. 机制级实证（POC，SPEC 变体注入，可复跑禁删）

`SPEC_k2_v4_c3poc.json`（生产 SPEC 副本 + `components.redriver.DS320PR1601.bga_escape.
per_ball` 注入真实 354 ballmap + U1@(93.8,53.7) + 走廊/翼带/容量数字）+ `reproduce_c3_plan_poc.py`
（复跑脚本，输出 POC_PASS）→ 生产 plan() v1.4 真执行：

```
BGA_PER_BALL_ESCAPE: ok=True  status=evaluated  level=per_ball
  -> DS320PR1601: verdict=FEASIBLE  signal=64  direct=32  via=32  crossing=16  deficits=0
```

**结论**：⑦ 描述符注入契约正确、生产 plan() 消费路径打通——SPEC 再生后 ⑦ 即真执行
evaluated FEASIBLE（消除 not_configured 假静默）。此为 C3 修复的**机器路径证明**。

## 3. SPEC 本体再生 = 缺口登记（⏳ L3 前置，非本 session 可闭）

- **事实约束**：SPEC_k2_v4.json（13254 行）与真板 k2_v4.kicad_pcb + 全部 sch 仍为
  **U3/U7 WQFN 双芯片旧拓扑**（stackup 8L、outline_y=[33,71]=38mm、capacitor_walls、
  redriver.U3/U7、`PCIE_DN*_U3` 网名）。DS320PR1601/46mm/6L/单面 = L1/L2 v2.0 **冻结的
  规划**，原理图/PCB 尚未 ECO 落地。
- **根因**：SPEC 是"生产 spec"，必须与真板网表/落位一致；DS320PR1601 布局未落地 → 全面
  再生 SPEC 会产生**描述与网表分裂**（新 spec 旧板），属假对齐。SPEC 再生与真板 ECO
  （原理图换 DS320PR1601 + 46mm 板框 + 单面）**必须同批**，超出本 session 授权/能力。
- **登记**：C3 = L3 前置（DS320PR1601 原理图 ECO 后：SPEC 再生 → plan() ⑦=evaluated
  FEASIBLE，本记录 §2 路径直接复用）。**未以 POC 冒充 SPEC 已完成再生**。
- **复跑（v27 补记）**：`SPEC_k2_v4_c3poc.json`（POC SPEC 变体）+ `reproduce_c3_plan_poc.py`
  （复跑脚本，输出 POC_PASS）落盘本目录为**可复跑资产（禁删）**，供 SPEC 再生 session 直接复用。

## 4. 附：⑦ 描述符注入样张（供 SPEC 再生 session 复用）

`components.redriver.DS320PR1601.bga_escape.per_ball = {
  ballmap: ds320pr1601_ballmap.json 的 ballmap 数组（354 球 {name,signal,x_mm,y_mm}）,
  chip_center: [93.8, 53.7], axis: {board_x: ball_y, board_y: ball_x},
  selected_lanes: [0..7], inter_pair_spacing: 1.46,
  port_to_corridor: {A: east, B: west}, corridor_edge: {east: 105.25, west: 82.35},
  band_corridor_capacity: {east: 16, west: 16}, via_zone_capacity: 69,
  in2_wings: [{N, 16.2, 0}, {S, 20.8, refclk 2.0}],
  pair_pitch_mm: 0.6(兼容保留), pad_mm: 0.305, via_mm: 0.35, clearance_mm: 0.10,
  signal_bands: [A_PER, B_PET, A_PET, B_PER] }`

> 注入注意：新增 ref `DS320PR1601`（勿覆盖 U3/U7 遗留项直至原理图 ECO 完成换名）；
> engine v1.4 per_wing 口径已按 inter_pair_spacing=1.46（C2），报告 crossing_need=11.68。

## 5. v28 ECO 执行补记（2026-09-06，用户授权路径 b 范围 A）——C3 闭合

- **生产 SPEC 本体再生完成**：`SPEC_k2_v4.json`（sha `7eaad223` → **`8732cb75`**，备份
  `.bak_v28_eco`）——描述层对齐：① redriver U3/U7(WQFN-64)→**DS320PR1601 主条目** +
  `bga_escape.per_ball` 注入（354 ballmap，契约 1:1 v27 POC）；U3/U7 降级
  **legacy_alloc_holder**（alloc 段名 `out_U3/out_U7` + u3_side_bridges 折线映射所需，
  scope-B alloc 重解后移除）；② stackup 8L→6L（F/G/S/G/P/B）；③ board outline_y
  38→46mm；④ capacitor_walls 移除；⑤ 顶层 `_v28_eco` 注记（scope + legacy_note）。
- **生产模型验证**：`RoutingTopologyGate.plan()` v1.4 真执行 → verdict
  **FEASIBLE_WITH_MORPH_GAP**（与 v27 基线同 verdict，无回归；PN polarity 混合 = 既有
  形态缺口，评审已接受）+ **⑦ BGA_PER_BALL_ESCAPE = evaluated → DS320PR1601 FEASIBLE
  （64/32/32/16/deficits 0）** → **not_configured 假静默消除（生产本体级）**。
- **C3 闭合**（范围 A）：SPEC 再生对齐 + ⑦ evaluated FEASIBLE = 评审条件达成；
  可复跑资产 `reproduce_c3_spec_regen_draft.py`（REGEN_DRAFT_PASS）。
  scope-B（真板物理 ECO + U3/U7 全移除 + alloc 重解 + layer_plan 施工段 6L 化）随 L3。
