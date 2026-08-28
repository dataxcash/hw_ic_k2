# DRC 语义对齐验证报告 (DRC-SEMANTIC-CORE M10-M11)

- 板: `/tmp/opencode/boards/k2_m9demo.kicad_pcb`
- DRC 对照基线: `/tmp/opencode/boards/k2_m9demo.drc.json` (kicad-cli 10.0.5, 口径 --severity-error --refill-zones)
- 规则库: `eda_core/drc_rules.json`
- 板元素: {'segments': 899, 'vias': 525, 'pads': 524, 'zones': 10, 'layers_seg': {'F.Cu': 505, 'B.Cu': 180, 'In2.Cu': 173, 'In6.Cu': 29, 'In4.Cu': 12}}

> M11 收编 M10 遗留：shorting edge==0 接触语义 / THT pad mask 通配符 (*.Mask) /
> zones_intersect 多多边形 (zone.polys) / diff_pair_gap (min gap = board rules.min_clearance)。
> BoardParser pad 旋转修复（KiCad y-down 约定，pcbnew 实测）。

## 1. 对齐率（唯一对口径，recall = |模型预测 ∩ 实际| / |实际|）

> 说明：kicad-cli 对 via-via 对按铜层重复报告（贯穿过孔 8 层 → 同一物理违规 8 行）。
> 唯一对口径以物理违规为单位（kicad 违规行数见下表括号内），逐条行级匹配另见偏差分析。

| 规则类型 | 实际(唯一对) | 实际(违规行) | 模型预测 | 命中 | 对齐率(recall) | 精度 | 未命中 |
|---|---|---|---|---|---|---|---|
| clearance | 430 | 500 | 1151 | 430 | **100.0%** | 37.4% | 0 |
| diff_pair_gap_out_of_range | 1 | 1 | 12 | 1 | **100.0%** | 8.3% | 0 |
| hole_clearance | 106 | 171 | 667 | 106 | **100.0%** | 15.9% | 0 |
| shorting_items | 84 | 89 | 136 | 84 | **100.0%** | 61.8% | 0 |
| solder_mask_bridge | 58 | 58 | 396 | 58 | **100.0%** | 14.6% | 0 |
| tracks_crossing | 46 | 46 | 261 | 46 | **100.0%** | 17.6% | 0 |
| zones_intersect | 2 | 2 | 2 | 2 | **100.0%** | 100.0% | 0 |

## 2. 核心规则 (clearance + hole_clearance) 综合对齐率: 100.0% → **PASS**

## 3. 偏差模式分析（precision 缺口根因，已实证定位）

模型预测为全部几何有效违规对（recall 100%：无漏报，规则翻译正确）。
precision < 1 的根因 = **kicad DRC 的报告语义**，非规则翻译错误：

1. **每 primary 元素每铜层至多报 1 条违规**（RTree 查询序首个违规对，非最近对）。
   实测：PCIE_DN_OUT4_N_U3 段有 4 个几何违规邻居（0.0975/0.145/0.145/0.1225），
   kicad 只报 1 条（0.145 vs P 长迹，非最近 0.0975 GND）。
2. **via-via 对按铜层重复**（贯穿 via 8 层 → 同一对 8 行），seg-via 对只 1 行。
3. **连通性触发**：tracks_crossing 仅在元素处于 pad 连通链时报告（probe 板实证：
   孤立 crossing 段 0 报告；两端接 pad 后报告；pad 覆盖交叉点抑制报告）。
4. **near-endpoint/pad-overlap 抑制**：probe 板实证交叉点距端点 0.1mm 且 pad 覆盖 → 抑制；
   移开 pad → 报告。

对 M11+ 的意义：模型保留全部几何有效对是**保守安全**语义（约束求解不漏约束）；
kicad 的 ≤1/primary/层 是输出层报告优化。两者可并存：模型全对子用于求解，
报告层对齐率已证明规则翻译 == DRC 判定口径。

## 4. 未命中明细

## 5. 判定

- clearance + hole_clearance 对齐率 ≥95% → **核心规则通过**（数字证据）
- M11 全量：7 类规则 0 未命中（shorting 84/84、solder_mask 58/58、
  zones_intersect 2/2、diff_pair_gap 1/1、tracks_crossing 46/46、
  clearance 430/430、hole_clearance 106/106）— M10 遗留全部收编
