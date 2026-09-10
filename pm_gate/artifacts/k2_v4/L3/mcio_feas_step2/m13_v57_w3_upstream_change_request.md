# Upstream change request — W3（canonical, ROOT-17 corrective / rev W3-CN.18）

> 语义：`UPSTREAM_CHANGE_REQUEST` = 升级触发器。门判据（R-23）：`SUFFICIENT iff same_layer_crossings == 0 and capacity ok`。

## 当前状态：**UPSTREAM_CHANGE_REQUEST（未收敛；v1.26 的 FEASIBLE_ALL 已撤回）**
- rev **W3-CN.18**：`same_layer_crossings = 1`（真交叉 1 + 共线重叠 0）；**全 via 间距违例 = 0**（覆盖 via1/corner/drop/land）。
- R1 32/32、R3 72/72、REFCLK 2/2、34 页；`landing` 未重发射；W4 不解封。
- 残余 1 = chip 侧 F.Cu pad→via 引线互交（2D BGA ball field，多行同向逃逸）。

## 已行使（合法、有效）
| 杠杆 | 效果 |
|---|---|
| T-2 逃逸+走廊 | r1_5 真交叉 217→0 |
| R1 顺序确定性放置（F-13 v1.2 + 0.525 净空）| R1 29/32→32/32 |
| A：J2 逃逸 x 域 | J2 落段重叠 236→0 |
| ROOT-17 ①：chip 引线 pad 对齐 | chip 真交叉 38→1 |
| ROOT-17 ②：J3/J4 落段展开（域 r3x2）| 落段重叠 33→0 |
| ROOT-17 ③：R1 同 x 竖段谓词 | 竖段重叠 4→0 |
| ROOT-17 追加：全 via 间距谓词 | via-via 违例 9→0 |

## Rejected（不得再提）
- `In4.Cu` 作信号层（SPEC：电源平面 P3V3；PD/SI 红线）。层用途不可改。

## 待裁决 / 下一步（项目层预授权、闭式零搜索）
1. **T-1 出逃扇**（chip 2D ball field）：外行先逃、内行经行间缝隙嵌套出逃；或放宽 chip via 域加缝隙候选位。

## 未清（非上游）
- D8：T-2/river 感知独立验证器 + 重生成 `m13_v57_w3_validation.json`。

## 计量（rev W3-CN.18）
```json
{"same_layer_crossings": 1, "crossings_by_class": {"r1_5": 1, "stub": 0},
 "overlaps_by_class": {"r1_5": 0, "stub": 0},
 "r1_assigned": 32, "r1_required": 32, "capacity_ok": true}
```

End of canonical request card (ROOT-17 corrective).
