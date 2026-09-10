# m13 v57 — W3 开工卡 **v1.28**（ROOT-18：T-1 chip 出逃扇 → 完整度量 FEASIBLE_ALL）

> 版本 bump（新文件）。取代 v1.27（commit `c5a6312`，保留不动）。授权：ROOT-16 A + ROOT-17 + ROOT-18。引擎 rev **W3-CN.20**。

## R-120 T-1 chip 出逃扇（清 1 处 chip 引线互交）
- 径向出逃目标 = pad + 0.05·(pad − 质心)（homothety，保序/平面）。
- 放置键：**pad 对齐 x 为主**、径向 y 为次。
- **breakout 平面性谓词**：候选 chip 引线对已放置引线做空间分桶（真交叉 + 共线重叠）拒绝 ⇒ 贪心保序（T-1）。
- 效果：chip 段冲突 **1 → 0**；R1 **32/32**。

## R-121 收口计量（完整度量 + 全 via 间距）
- `same_layer_crossings = 0`（真交叉 0 + 共线重叠 0；整条页路由）；全 via 间距违例 **0**（min 0.5272 ≥ 0.525）。
- R1 32/32、R3 72/72、REFCLK 2/2、34 页；`verdict = FEASIBLE_ALL`；`certificates = []`。
- **F-12 原子重发射** landing（authority sha == main sha）；**W4 解封**。
- wall ≈ 9.0s ≤ 120s；`--scale` K×526 线性；每页候选检查常数 ⇒ 全域 O(n)。

## R-122 纪律 / 未清
- 零坐标搜索（G-M1=0；G-M2 while=0）；四源 MATCH；版本 bump 新件；独立验证器复验后方可宣称（已执行）。
- 未清：D8（T-2/river 感知独立验证器 + 重生成 `m13_v57_w3_validation.json`）。

End of ROOT-18 v1.28.
