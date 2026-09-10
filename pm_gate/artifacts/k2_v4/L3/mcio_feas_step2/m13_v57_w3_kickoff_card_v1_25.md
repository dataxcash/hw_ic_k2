# m13 v57 — W3 开工卡 **v1.25**（ROOT-16：工件自可验证 + 完整度量 + A；残余 80）

> 版本 bump（新文件）。取代 v1.24（commit `f621595`，保留不动）。授权：ROOT-16（owner 授权代裁 A）。
> 冻结四源未动；零坐标搜索；引擎 rev **W3-CN.13**。

## R-100 完整度量（强制口径）
- `same_layer_crossings` = 真交叉 **+ 共线重叠（短路）**，覆盖整条页路由：
  chip pad stub / via / 过渡段 / 走廊 lane / connector stub / landing→pad。**禁止空集/未度量口径**。

## R-101 A：J2 逃逸 x 域（版本化域修订）
- 新件 `m13_v57_f8_r3_gap_candidates_j2x1.json`（旧 F-8 件不动）；J2 pad 唯一逃逸槽 fan（内列向左/外列向右）。
- 效果：`same_layer_crossings 283 → 80`（J2 落段重叠 236 → 0）；R3 72/72、REFCLK 2/2 不变。

## R-104 工件**自可验证**（本版新增，强制）
- 无论 verdict（含 UPSTREAM_CHANGE_REQUEST），主件**必须**持久化：
  `pages[*].nodes`（每页段型分层路由）+ `route_geometry`（全部段，含层/端点）+ `resource_gate.verification_check`。
- **禁止**“trust-me 标量”/空 `pages`/空 `layers`。冲突计数必须能由主件**独立重算**。
- 实测：由 `route_geometry` 独立重算 = `43 (真交叉 r1_5) + 4 (重叠 r1_5) + 33 (重叠 stub) = 80`，与主件一致。

## R-102 残余（未收敛，如实）
- chip pad stub 真交叉 **43**（via 赋位非保序）；R1 逃逸竖段重叠 **4**；J3/J4 落段重叠 **33**。
- 未达 `FEASIBLE_ALL`；`landing` 未重发射；**W4 不解封**。

## R-103 下一步（项目层、预授权、零搜索）
1. chip 逃逸扇**保序谓词**（via 序 = pad 序）或 T-1 出逃扇 → 清 43。
2. J3/J4 落段展开（同 A 手法）→ 清 33。
3. R1 放置谓词「同 x 竖段不重叠」→ 清 4。

End of ROOT-16 v1.25.
