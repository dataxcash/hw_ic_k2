# m13 v57 — W3 开工卡 **v1.26**（ROOT-17：三杠杆清零 → 完整度量 FEASIBLE_ALL）

> 版本 bump（新文件）。取代 v1.25（commit `a76922a`，保留不动）。授权：ROOT-16 A + ROOT-17（预授权）。
> 冻结四源未动；零坐标搜索；引擎 rev **W3-CN.16**。

## R-105（ROOT-17 三杠杆；均项目层、闭式、零搜索）
1. **chip 逃逸扇保序**：R1 via 目标键由「交替 ±0.6/±1.2」改为 **pad 对齐**（`_tP=padP.x, _tN=padN.x`），
   使 pad→via 引线近垂直、按 pad 序单调 ⇒ 引线不再互交。**真交叉 38 → 0**。
2. **J3/J4 落段展开**：版本化域件 `m13_v57_f8_r3_gap_candidates_r3x2.json`（旧件不动），
   J2 唯一逃逸槽（同 A）+ **J3/J4 连接器全局唯一槽**（0.6 网格，按 (pad 列 x, y, pol, net) 定序）
   ⇒ 同列多 net 落段互异 x。**落段重叠 33 → 0**。
3. **R1 同 x 竖段不重叠**：顺序放置谓词新增「逃逸竖段同 x 不重叠」；并以 **O(1) 空间索引**（x 分桶 +
   x→span 表，逐页重建）实现，保持单遍、无搜索。**竖段重叠 4 → 0**。

## R-106 收口（完整度量，可由工件独立重算）
- `same_layer_crossings = 0` = 真交叉 `{r1_5:0, stub:0}` + 共线重叠 `{r1_5:0, stub:0}`。
- R1 **32/32**（min via 距 0.617 ≥ 0.525，0 违例）、R3 **72/72**、REFCLK **2/2**、34 页（32 data + 2 refclk）。
- `verdict = FEASIBLE_ALL`；`certificates = []`；全谓词 PASS。
- **F-12 原子重发射** `m13_v57_w3_chip_landing_rows.json`（64 行；`authority.main_sha256 == main sha`）。
- **W4 解封**。
- wall ≈ **2.6s**（≤120s 护栏）；`--scale` work(2)=1052 / work(4)=2104 = K×526（线性）；
  三个谓词 O(1) ⇒ 全域 wall 线性。

## R-107 纪律
- 零坐标搜索（G-M1 NAME 令牌 0 命中；G-M2 while=0/自调用=0）；四源 MATCH；版本 bump 新件；
  **独立验证器复验后方可宣称 FEASIBLE_ALL**（已执行，见 boundary v1.12）。
- 未清：D8（T-2/river 感知独立验证器 + 重生成 `m13_v57_w3_validation.json`）。

End of ROOT-17 v1.26.
