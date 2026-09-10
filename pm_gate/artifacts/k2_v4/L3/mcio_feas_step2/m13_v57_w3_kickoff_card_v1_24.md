# m13 v57 — W3 开工卡 **v1.24**（ROOT-16：完整度量 + A；残余 80）

> 版本 bump（新文件）。取代 v1.23（commit `88c74f1`，保留不动）。授权：ROOT-16（owner 授权代裁 A）。
> 冻结四源未动；零坐标搜索；引擎 rev **W3-CN.12**。

## R-100 完整度量（强制口径）
- `same_layer_crossings` = 真交叉 **+ 共线重叠（短路）**，覆盖整条页路由：
  chip pad stub / via / 过渡段 / 走廊 lane / connector stub / landing→pad。**禁止空集/未度量口径**。
- 实现：`paths` 增 `#fcu_pad`（pad→via1, F.Cu）与 `#fcu_land`（landing→pad, F.Cu）；
  `count_crossings` 返回 (真交叉, 共线重叠)；同层异网；同网相邻段不互比。
- 实测未测前：`283`；A 后：**`80`**。

## R-101 A：J2 逃逸 x 域（版本化域修订）
- 新件 `m13_v57_f8_r3_gap_candidates_j2x1.json`（旧件不动）；producer `p3_v57_f8_r3_gap_candidates_j2x1.py`。
- J2 pad 唯一逃逸槽 fan：内列(132.65)向左 `131.65 − k×0.6`；外列(135.0)向右 `136.0 + k×0.6`（依 SPEC 拓扑）。
- 效果：落段重叠 236 → **0**；总 283 → **80**；R3 72/72、REFCLK 2/2 不变。

## R-102 残余（未收敛，如实）
- chip pad stub 真交叉 **43**（via 赋位非保序）；R1 逃逸竖段重叠 **4**；J3/J4 落段重叠 **33**。
- 未达 `FEASIBLE_ALL`；`landing` 未重发射；**W4 不解封**。

## R-103 下一步（项目层、预授权、零搜索）
1. chip 逃逸扇**保序谓词**（via 序 = pad 序）或 T-1 出逃扇构造 → 清 43。
2. J3/J4 落段展开（同 A 手法；注意同 y 多 pad 的 slot 序）→ 清 33。
3. R1 放置谓词加「同 x 竖段不重叠」→ 清 4。

End of ROOT-16 v1.24.
