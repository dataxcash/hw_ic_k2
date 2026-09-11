# W3 8L 重跑进展 v3 — 残余净距 12 → 10（zone-aware）

> 引擎 rev **W3-CN.26**｜LID.1 8L｜canonical `m13_v57_w3_joint_assignment.json` 未改（W3-CN.25/c17c5a42）。

## 净距残余
| 迭代 | crossings | R1 | tt | vt | vv | 合计 |
|---|---|---|---|---|---|---|
| v2 最佳 | 0 | 32 | 3 | 8 | 1 | 12 |
| **+ zone-aware 净距**（pad-access 段按 SPEC `escape_transition_zone.escape_clearance_mm=0.075` ⇒ 中心 0.28/0.3525；其余 0.38/0.4525） | 0 | 32 | **1** | 8 | 1 | **10** |

## 残余 10（已定位）
- **tt 1**：`UP0/UP1 out_J2 @0.2458`（chip 同带相邻 breakout；<0.28）。
- **vt 8**：连接器 landing 微几何（`DN6/DN7 out_MCIO @0.3162`、`UP1/input @0.3162`）+ `UP1/out_J2 @0.3278`。

## 下一步
连接器 landing 的 gap-candidate 域放宽（版本化）+ chip 同带 breakout 强制 0.28 间距 → 残余清零 ⇒ `FEASIBLE_ALL`。
