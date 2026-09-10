# m13 v57 — W3 开工卡 **v1.23**（ROOT-15 纠正：严格度量 → UPSTREAM_CHANGE_REQUEST）

> 版本 bump（新文件）。取代 v1.22（`m13_v57_w3_kickoff_card_v1_22.md`，commit `e550df9`，保留不动）。
> 授权：ROOT-15 执行令（监督）。冻结四源未动；零坐标搜索；引擎 rev **W3-CN.11**。

## R-90 撤回 v1.22 的 FEASIBLE_ALL（独立复核证伪）
- 证伪：v1.8/v1.22 的 `same_layer_crossings` 仅计真交叉，**未计同层异网共线重叠（短路）**。

## R-91 严格冲突度量（本版）
- `count_crossings` 返回 (真交叉, 共线重叠)；`same_layer_crossings = 真交叉 + 共线重叠`；同网相邻段不互比。
- 实测：`same_layer_crossings = 240`；`crossings = {r1_5:0, stub:0}`；`overlaps = {r1_5:4, stub:236}`。

## R-92 按极性 R3 landing（真实缺陷修正）
- 页面/stub 路由/node 对 P、N 各取 `nets[pol]` 的 R3 落点（此前 N 误用 P 的落点）。

## R-93 T-2 river 扇出（保留；真交叉 46→0）
- 路由：`F.Cu pad → via1 → B.Cu 逃逸竖段 → corner via → In2.Cu run → via_drop → B.Cu 落段 → via_land → F.Cu landing → pad`；每线 4 via ≤5。

## R-94 残余 = 上游资源不足（闭式）
- J2 隙列：2 个 x 候选、跨度 2.35mm，16 net 逃逸需 `(16−1)×0.525 = 7.875mm` ⇒ 放不下 ⇒ 落段共 x 重叠 236。
- 另 4 = R1 逃逸竖段同 x 重叠（A-CN.1 未约束竖段）。
- 结论：未达 `FEASIBLE_ALL`；`landing` 未重发射；**W4 不解封**；上游项见请求卡（推荐增大 J2 逃逸 x 域）。
- 已披露度量边界：chip 侧 pad→via 斜引线 + connector landing→pad 未纳入当前度量（待监督确认口径）。

## R-95 已清 / 未清
- 已清：R1 32/32、R3 72/72、REFCLK、真交叉两类=0、按极性 landing、严格度量落地。
- 未清：D8（T-2/river 感知独立验证器 + 重生成 `m13_v57_w3_validation.json`）。

End of ROOT-15 (corrective) v1.23.
