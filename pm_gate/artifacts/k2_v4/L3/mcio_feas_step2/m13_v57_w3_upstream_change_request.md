# Upstream change request — W3（canonical, regenerated at ROOT-15 / rev W3-CN.10）

> 语义：`UPSTREAM_CHANGE_REQUEST` / `CERTIFICATE` = **升级触发器**，不是终点。
> 门判据（R-23 验证式）：`SUFFICIENT iff same_layer_crossings == 0 and lanes_needed <= lanes_avail`。
> 引擎自 rev W3-CN.10 起只写**版本化**请求卡（`..._<REVISION>.md`），不再覆盖本 canonical 件。

## 当前状态：**无未决上游变更请求（gate SUFFICIENT）**
- W3 rev **W3-CN.10** 实测：`same_layer_crossings = 0`，`crossings_by_class = {r1_5: 0, stub: 0}`（两类均有实段）；
  R1 32/32、R3 72/72、REFCLK 2/2、每线 via 4 ≤ 5 ⇒ `verdict = FEASIBLE_ALL`。
- 连接器扇出 46 处残余已由 **T-2 river 构造**（项目层，预授权）闭合，未动冻结四源、未改层叠/层用途。

## Rejected（不得再提）
- `In4.Cu` 作信号层 — **已驳回**（SPEC：In4 = 电源平面 P3V3；In2 = 唯一内层信号层；PD/SI 红线；
  实测退化 29/32 → 8/32）。层用途**不可改**。

## Legal levers（仅信号层内路由/拓扑）+ 计量状态
| 杠杆 | 状态 |
|---|---|
| lane 序按源序 | WITHDRAWN（= card v1.3 §R-8 闭式不可行证明）|
| no_90deg 通道化折线 | MEASURED worse（319 > 264）→ 回退 |
| 逐帧自适应步长 | MEASURED neutral |
| R1 逃逸域放宽 ±1.5→±2.5mm | **已行使**（owner 经 W3-C13 授权；F-13 r2 域 `f2e26325…`）|
| T-2 通道 + dogleg / river 扇出（赋位×着色）| **已行使 ✓ 闭合 46 残余**（rev W3-CN.10）|
| R1 顺序确定性放置（F-13 v1.2 对域固定键 argmin）| **已行使 ✓ R1 29/32 → 32/32** |

## Gate measurement (verification-based, R-23)
```json
{
 "same_layer_crossings": 0,
 "crossings_by_class": {"r1_5": 0, "stub": 0},
 "r1_assigned": 32,
 "r1_required": 32,
 "capacity_ok": true,
 "closed_form": "SUFFICIENT iff same_layer_crossings == 0 and capacity ok"
}
```

## Next（唯一未清项，非上游）
- **D8**：版本 bump 出 T-2/river 感知的**独立验证器**并重生成 `m13_v57_w3_validation.json`
  （旧件为 T-2 之前快照；card v1.3 已记录 G-M4 的 197 处契约↔实现漂移）。属项目工件层，无需 owner。

End of canonical request card (ROOT-15).
