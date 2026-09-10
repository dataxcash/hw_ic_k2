# 上游变更请求卡 — W3 层意图资源不足（W3-C4）

> 触发：`m13_v57_w3_resource_gate` verdict = UPSTREAM_CHANGE_REQUEST（闭式门）。
> 语义：CERTIFICATE/门失败 = **升级触发器**，不是终点；本卡即升级件。

## 门实测（闭式）
```json
{
 "verdict": "UPSTREAM_CHANGE_REQUEST",
 "rule": "available transition-eligible signal layers x corridor/band fan capacity vs demand",
 "transition_eligible_layers": [
  "B.Cu",
  "In2.Cu"
 ],
 "layer_intent": {
  "B.Cu": "transition_eligible",
  "F.Cu": "stub_only",
  "In1.Cu": "gnd_plane",
  "In2.Cu": "transition_eligible",
  "In3.Cu": "gnd_plane",
  "In4.Cu": "power_plane(P3V3, spec)"
 },
 "layer_demand_peak_overlap": 3,
 "layer_demand_ok": false,
 "lane_capacity": {
  "needed": {
   "WEST_MCIO_TO_CHIP": 16,
   "EAST_CHIP_TO_J2": 16
  },
  "available": {
   "WEST_MCIO_TO_CHIP": 32,
   "EAST_CHIP_TO_J2": 32
  },
  "ok": true
 },
 "fan_groups": [
  {
   "group": "EAST_CHIP_TO_J2/dn",
   "source_y_range": [
    57.12,
    57.64
   ],
   "lane_region_y": [
    56.66,
    78.56
   ],
   "fan_y_extent": [
    56.66,
    78.56
   ],
   "x_extent_chip_zone": [
    82.35,
    105.25
   ]
  },
  {
   "group": "EAST_CHIP_TO_J2/up",
   "source_y_range": [
    55.13,
    55.823
   ],
   "lane_region_y": [
    56.66,
    78.56
   ],
   "fan_y_extent": [
    55.13,
    78.56
   ],
   "x_extent_chip_zone": [
    82.35,
    105.25
   ]
  },
  {
   "group": "WEST_MCIO_TO_CHIP/dn",
   "source_y_range": [
    51.673,
    52.366
   ],
   "lane_region_y": [
    33.3,
    55.2
   ],
   "fan_y_extent": [
    33.3,
    55.2
   ],
   "x_extent_chip_zone": [
    82.35,
    105.25
   ]
  },
  {
   "group": "WEST_MCIO_TO_CHIP/up",
   "source_y_range": [
    49.76,
    50.28
   ],
   "lane_region_y": [
    33.3,
    55.2
   ],
   "fan_y_extent": [
    33.3,
    55.2
   ],
   "x_extent_chip_zone": [
    82.35,
    105.25
   ]
  }
 ],
 "closed_form": "verdict = SUFFICIENT iff peak(fan y-extent overlap in chip-zone x) <= |transition_eligible_layers| and lanes_needed <= lanes_avail",
 "insufficiency_basis": {
  "same_layer_crossings": 264,
  "minimal_core": [
   [
    "PCIE_DN0/input/N",
    "PCIE_DN0/input/P"
   ],
   [
    "PCIE_DN0/input/N",
    "PCIE_DN1/input/N"
   ],
   [
    "PCIE_DN0/input/N",
    "PCIE_DN1/input/P"
   ],
   [
    "PCIE_DN0/input/N",
    "PCIE_DN2/input/N"
   ],
   [
    "PCIE_DN0/input/N",
    "PCIE_DN2/input/P"
   ],
   [
    "PCIE_DN0/input/N",
    "PCIE_DN3/input/N"
   ]
  ],
  "structural_reason": "intended construction (signal-layer-only intent, band layer rule, polarity same-side, adaptive step) still leaves same-layer crossings"
 },
 "producer": "k2/tools/p3_v57_w3_constructive.py:resource_gate",
 "verification_check": {
  "same_layer_crossings": 264,
  "r1_assigned": 29,
  "r1_required": 32,
  "capacity_ok": true,
  "closed_form": "SUFFICIENT iff same_layer_crossings == 0 and capacity ok"
 }
}
```

## 待 L2 裁决的层意图项（每项附闭式依据）
1. **In4.Cu 可否作信号层**：当前 SPEC 记 In4 为电源分区；若放行，可用过渡层 2→3，
   闭式依据：`peak(fan y-extent overlap) <= |transition_eligible_layers|`。
2. **no_90deg 是否放宽**：若放宽，R1.5 可走确定性通道化折线（新增 R1.5 资源层字段），
   闭式依据：折线通道互斥谓词（同层同 y 通道唯一占用）。
3. **lane 序可否改**：若允许按源序排 lane，chip 侧扇面可直接对齐，
   闭式依据：`sign(src_y_a - src_y_b) == sign(lane_y_a - lane_y_b) forall a,b`。
4. **R1 x 序准入约束**（hatch ①，已在 v1.1 域内）：若需全局单调 x，须放宽 ±1.5mm 逃逸域。

## 当前层意图结论
- 可用过渡层：B.Cu, In2.Cu
- 层需求（扇面 y 重叠峰值）：3
- 判定：UPSTREAM_CHANGE_REQUEST
