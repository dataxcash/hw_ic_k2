# Upstream change request — W3（canonical, ROOT-17 / rev W3-CN.16）

> 语义：`UPSTREAM_CHANGE_REQUEST` = 升级触发器。门判据（R-23）：`SUFFICIENT iff same_layer_crossings == 0 and capacity ok`。
> 引擎只写**版本化**请求卡（`..._<REVISION>.md`），不覆盖本 canonical 件。

## 当前状态：**无未决上游变更请求（gate SUFFICIENT；verdict = FEASIBLE_ALL）**
- rev **W3-CN.16** 完整度量实测：`same_layer_crossings = 0`
  （真交叉 `{r1_5:0, stub:0}` + 共线重叠 `{r1_5:0, stub:0}`）；R1 32/32、R3 72/72、REFCLK 2/2、34 页。
- F-12 landing 已原子重发射（authority sha == main sha）；**W4 解封**。

## 已闭合的杠杆（全部合法、闭式、零搜索）
| 杠杆 | 效果 |
|---|---|
| T-2 逃逸+走廊（段型分层）| r1_5 真交叉 217 → 0 |
| R1 顺序确定性放置（F-13 v1.2 固定键 argmin + 0.525 净空）| R1 29/32 → 32/32 |
| **A**：J2 逃逸 x 域（版本化域）| J2 落段重叠 236 → 0 |
| **ROOT-17 ①**：chip 逃逸扇保序（pad 对齐引线）| 真交叉 38 → 0 |
| **ROOT-17 ②**：J3/J4 落段展开（版本化域 `r3x2`）| 落段重叠 33 → 0 |
| **ROOT-17 ③**：R1 同 x 竖段谓词（O(1) 索引）| 竖段重叠 4 → 0 |

## Rejected（不得再提）
- `In4.Cu` 作信号层 — **已驳回**（SPEC：In4 = 电源平面 P3V3；PD/SI 红线）。层用途不可改。

## 未清（非上游）
- **D8**：T-2/river 感知独立验证器 + 重生成 `m13_v57_w3_validation.json`（旧件为 T-2 前快照）。
- 口径说明：REFCLK 段另见 A-CN.5（已 PASS，与 keepout 零交）。

## 计量（rev W3-CN.16，R-23）
```json
{
 "same_layer_crossings": 0,
 "crossings_by_class": {"r1_5": 0, "stub": 0},
 "overlaps_by_class": {"r1_5": 0, "stub": 0},
 "r1_assigned": 32, "r1_required": 32, "capacity_ok": true,
 "closed_form": "SUFFICIENT iff same_layer_crossings == 0 and capacity ok"
}
```

End of canonical request card (ROOT-17, FEASIBLE_ALL).
