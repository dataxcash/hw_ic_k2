# m13 v57 — W3 开工卡 **v1.22**（ROOT-15：A-CN.1b 清零 + stub 度量修正 + river 扇出 → FEASIBLE_ALL）

> 版本 bump（新文件）。取代 v1.21（`57f49e020e67ffad…`，保留不动）。授权：ROOT-15 执行令（监督）。
> 冻结四源未动；零坐标搜索纪律不变；引擎 rev **W3-CN.10**。

## R-80 R1 顺序确定性放置（清 A-CN.1b）
- 消费离线 F-13 v1.2 对域（`m13_v57_f13_r1_pair_coupling_v1_2.json`，`3a08c463…`）。
- 每页按固定键 `(|Px−pad_P.x| + |Nx−pad_N.x|, Px, Nx)` 在「对距 ≥0.525 ∧ stagger ≥0.38 ∧ 0.525 净空」谓词
  过滤后的行集上**单遍 argmin**（常数域、固定 tie-break；无试错/回溯/迭代修正）⇒ 64 via 两两 ≥0.525，R1 **32/32**。

## R-81 证书作废语义（修 verdict 卡死）
- `CONSTRUCTION_INFEASIBLE` = 「本构造下该页无法赋位」；顺序放置已赋位的页，其证书即失效。
- 实现 `certs = [c for c in certs if page_or_pad not in out]`。

## R-82 same_layer_crossings 全类口径（合 C17）
- `same_layer_crossings = r1_5 + stub`；两类分列报告。修 (a) stub 循环守卫键（`"<conn_ref>|<net>"`）；
  (b) 旧实现只取 `r1_5` 导致 stub 未计入的缺陷。

## R-83 连接器扇出 T-2 river（闭合 46 残余）
- 路由：`F.Cu pad → via1(F/B) → B.Cu 逃逸竖段 → corner via(B/In2) → In2.Cu run → via_drop(In2/B) → B.Cu drop → via_land(B/F) → F.Cu landing → pad`。
- 段型分层；同层异 x（竖）/异 y（横）⇒ 同层交叉 0；每线 **4 via ≤5**；不新增层。

## R-84 收口实测
| 配置 | r1_5 | stub | R1 | verdict |
|---|---|---|---|---|
| rev W3-CN.6/7（stub 守卫恒真 ⇒ 空集） | 0 | **0(vacuous)** | 32/32 | CERTIFICATE（陈旧证书）|
| rev W3-CN.9（修守卫+全类口径，未改扇出） | 0 | **46** | 32/32 | UPSTREAM_CHANGE_REQUEST（诚实残余）|
| **rev W3-CN.10（river 扇出）** | **0** | **0** | **32/32** | **FEASIBLE_ALL** |

- 34 页（32 data + 2 refclk）；F-12 landing 原子重发射；W4 解封。
- 未清项 D8：T-2/river 感知独立验证器 + 重生成 `m13_v57_w3_validation.json`。

End of ROOT-15 v1.22.
