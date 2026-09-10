# m13 v57 — W3 开工卡 **v1.27**（ROOT-17 纠正：撤回 FEASIBLE_ALL；段冲突 1 / via 违例 0）

> 版本 bump（新文件）。取代 v1.26（commit `0643771`，保留不动）。授权：ROOT-16 A + ROOT-17。引擎 rev **W3-CN.18**。

## R-110 撤回 v1.26 的 FEASIBLE_ALL
- 独立验证器证伪：river 扇出新增的 corner/drop/land via 未纳入 via–via 0.525（9 对，min 0.170）。

## R-111 全 via 间距谓词（ROOT-17 追加，本项目层）
- 放置谓词覆盖**全部 via**（via1/corner/drop/land；异网；同网豁免），O(1) 空间索引（x 分桶）。
- 实测 via–via 违例 **9 → 0**。

## R-112 当前计量（完整度量 + 全 via 间距）
- `same_layer_crossings = 1`（真交叉 1 + 共线重叠 0）；全 via 间距违例 0；R1 32/32、R3 72/72、REFCLK 2/2、34 页。
- 残余 1 = chip F.Cu pad→via 引线互交（2D BGA ball field 多行同向逃逸）。
- `verdict = UPSTREAM_CHANGE_REQUEST`；`landing` 未重发射；**W4 不解封**。

## R-113 下一项（项目层、预授权、零搜索）
- **T-1 出逃扇**（拓扑样板库）：外行先逃、内行经行间缝隙嵌套出逃；或放宽 chip via 域加「缝隙」候选位。
- 未清：D8（T-2/river 感知独立验证器 + 重生成 `m13_v57_w3_validation.json`）。

End of ROOT-17 (corrective) v1.27.
