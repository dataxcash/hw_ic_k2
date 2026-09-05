# M14 v24 — TOPO 模型能力提升：routing_topology_gate 强约束⑥ BGA 分组阵列逃逸（拓扑/通道级）

> 状态：本 session = **提升 TOPO 模型能力（ECN，用户授权）**，交付于共享引擎
> `_shared/eda_core/routing_topology_gate.py`（v1.0 → v1.1）。**层数（6L vs 8L）仍维持
> INDETERMINATE**——本能力是模型新形态（组/通道级逃逸判定），**非 per-ball 物理闭合**，
> 不改变 v23 的资产缺口结论；消费它（注入 DS320PR1601 bga_escape → 重跑 gate）是下一步。
> 引擎改动走 ECN unlock→改→lock；`_shared` 已 push（805f3cf）+ 容器指针（d384d85）。

## 0. 交付了什么（诚实边界）

`routing_topology_gate` 新增**强约束⑥ `BGA_GROUP_ESCAPE`**：
- 消费 spec 注入的 `components.redriver.<ref>.bga_escape` 描述符（BGA 分组阵列逃逸结构）。
- 确定性校验（每组带）：组带槽位 `pairs ≤ escape_slots`；via 总需求
  （method∈{via,crossing} 的 pairs）≤ `via_zone_capacity`；In2 穿越
  `crossing pairs × nominal_pair_pitch ≤ in2_band_mm - refclk_mm`。
- 输出 `level=topology_channel`（**明示 = 拓扑/通道级，非 per-ball 物理闭合**）；任一缺口 →
  INFEASIBLE 带 per_group deficit 证据。
- **无任何 bga_escape 声明 → `not_configured`（ok=True，不改变既有裁决）**——向后兼容，
  t1-t5/eco1 单测零回归 + 新增 t6（可行 / 组带缺口 / In2 缺口 / not_configured）。

> 这次改进了**模型能做的判定形态**（从"逃逸只按容量计数"到"能按 BGA 组带/通道做拓扑级
> 判定"），是真实模型能力进步；**不是**造物理坐标、**不是**假闭合。数据源 = TI ZDG0354A /
> Intel PCIe5 retimer common footprint 的已知组带结构，零板级字面量（全部 spec 注入）。

## 1. 注入契约（bga_escape 描述符 Schema）

```json
"components": {"redriver": {"<ref>": {
   "bga_escape": {
     "package": "nfBGA-354", "pitch_mm": 0.6,
     "array_mm": [8.9, 22.8], "ball_count": 354,
     "nominal_pair_pitch_mm": 0.6,        // 名义对距（0.6，datasheet）
     "via_zone_capacity": 69,             // In2 逃逸 via 容量（球下 via 上限）
     "in2_band_mm": 8.0, "refclk_mm": 2.0, // In2 穿越带 + REFCLK 余量
     "group_bands": [                      // 列带结构（全 lane 一致，datasheet）
       {"name": "A_PER@row1-2",  "method": "crossing", "pairs": 8, "escape_slots": 8},
       {"name": "B_PET@row7-10", "method": "via",      "pairs": 8, "escape_slots": 8},
       {"name": "A_PET@row26-29","method": "via",      "pairs": 8, "escape_slots": 8},
       {"name": "B_PER@row34-35","method": "direct",   "pairs": 8, "escape_slots": 8}
     ]
   }
}}}
```
- `escape_slots` = 组带名义逃逸槽位数（带内 ball 列位置 / 2，保守数据驱动）；`method` ∈
  {direct, via, crossing}（25% 外环 direct / 75% via / 50% crossing）。
- 读取 = `@ RoutingTopologyGate.plan()['constraints']['BGA_GROUP_ESCAPE']`；资源可见 =
  `plan()['resources']['bga_escape']`。

## 2. 关键发现：K2_SPEC 仍为旧双芯片（滞后）

`k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json` 的 `components.redriver` = **U3 + U7
（WQFN-64_10x5.5mm_P0.4mm）**，**尚无 DS320PR1601（U1 BGA-354）**——L1/L2 冻结层面已定
单 DS320PR1601/46mm/6L，但 SPEC 器件/组带数据滞后于此决策。因此当前 K2_SPEC **无 bga_escape
声明** → ⑥ 为 `not_configured`（兼容，t5 真实集成单测不受影响）。

## 3. 传导下 session（按序）

1. **更新 K2_SPEC redriver → DS320PR1601（U1）并注入 `bga_escape` 描述符**（用上述 Schema +
   v22 的 354 球名集列带/0.6/8.9×22.8）。**注意**：若 spec 仍保留 U3/U7 需先裁决 refdes/器件
   归属（L1 frozen 指 U1 DS320PR1601；SPEC 与 L1 对齐是件独立工件）。
2. 重跑 `routing_topology_gate` → 读 `constraints.BGA_GROUP_ESCAPE` → 得到 DS320PR1601 在
   6L 下的**拓扑/通道级**逃逸判定（组带槽位 / via 总需求 / In2 穿越+REFCLK）。
3. **诚实边界**：该判定升级的是"结构级 → 拓扑/通道级"（递进），**仍非 per-ball 物理闭合**
   （后者仍需 Astera `PTx16xx_supplemental_info.xlsx`/CAD 资产）。层数定案（过闸冻 6L/回 8L）
   **仍待 per-ball 物理精确验证**；⑥ 是提升置信度的合法模型证据，不是绕过物理资产的后门。

## 4. G5 收尾自检

- **消费资产**：`routing_topology_gate.py`（1.0 契约，读全）、`test_routing_topology_gate.py`
  （约定）、`hs_route_model._track_y_from_alloc`（1.1 已有）、K2_SPEC（确认无 bga_escape）、
  冻结纪律（EXECUTION_PROCESS §5 解锁通道）。
- **产出**：引擎 ⑥ 约束 + t6 单测（7 passed）；`_shared` 805f3cf、容器 d384d85 已 push。
- **未消费/缺口**：DS320PR1601 的实际 `escape_slots`（组带槽位数）**未填入**——需从 datasheet
  组带结构精算（或 CAD 资产），本文档只提供契约未填真实值（禁臆造槽位数 = 禁假数据喂 ⑥）。
  `k2/_shared` 嵌套副本（b48d3f4）与容器 `_shared`（9a46176→805f3cf）**已分歧**（前者缺
  `_track_y_from_alloc`、无本 ⑥）——若 k2 门禁实际跑 k2/_shared 需另行同步（本轮以容器
  `_shared` 为权威，kb_writeback 先例支撑）。
- **G2/G4**：未触发（无求解卡点）；本次为 ECN 模型能力改动，非几何求解。
- **禁违反项**：✅ 零违反（未造物理坐标、未宣布闭合、未动 L1/L2 frozen 层数行、引擎改动走
  ECN unlock→lock、仅提交本 2 文件、未触碰预存 _shared 未提交改动）。

## 5. commit

- `_shared` `9a46176..805f3cf`（⑥ 约束+t6）；容器 `af7f370..d384d85`（bump _shared 指针）。
- 冻结区已复锁（freeze_ctl.sh status = 0/0/0）。
