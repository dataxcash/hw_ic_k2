# Upstream change request — W3（canonical, ROOT-15 corrective / rev W3-CN.11）

> 语义：`UPSTREAM_CHANGE_REQUEST` / `CERTIFICATE` = **升级触发器**，不是终点。
> 门判据（R-23）：`SUFFICIENT iff same_layer_crossings == 0 and capacity ok`。
> 引擎自 W3-CN.10 起只写**版本化**请求卡（`..._<REVISION>.md`），不覆盖本 canonical 件。

## 当前状态：**UPSTREAM_CHANGE_REQUEST（未收敛；本轮以严格度量重测）**
- rev **W3-CN.11** 采用严格冲突度量（真交叉 **+ 共线重叠 = 同层异网短路**）：
  `same_layer_crossings = 240`，`overlaps_by_class = {r1_5: 4, stub: 236}`，真交叉 = 0；
  R1 **32/32**、R3 **72/72**、REFCLK **2/2**、每线 4 via ≤ 5。
- 根因（上游）：**连接器逃逸资源不足**。J2 一条隙列仅 2 个 x 候选、中距 **2.35mm**，
  却有 **16 条 net** 需逃逸；每 net 0.525mm 间距需 `(16-1)×0.525 = 7.875mm ≥ 8.4mm` 量级 ⇒
  现有隙列 x 域放不下 ⇒ 落段被迫共 x 重叠。闭式依据：`needed_span = (n_col − 1) × 0.525`。

## Rejected（不得再提）
- `In4.Cu` 作信号层 — **已驳回**（SPEC：In4 = 电源平面 P3V3；PD/SI 红线；实测退化）。层用途不可改。

## 已行使（合法、有效、真交叉显著下降）
| 杠杆 | 结果 |
|---|---|
| T-2 逃逸+走廊（段型分层 B.Cu/In2.Cu）| r1_5 真交叉 217 → **0** |
| R1 顺序确定性放置（F-13 v1.2 域固定键 argmin + 0.525 净空）| R1 29/32 → **32/32** |
| T-2 river 连接器扇出（B.Cu 竖 + In2 横 + B.Cu 落）| stub 真交叉 46 → **0**（但引出共线重叠 236 = 资源不足的表现）|

## 待 owner 裁决（上游项，附闭式依据）
1. **J2 连接器逃逸资源**：`needed_span=(16−1)×0.525=7.875mm` vs 现有隙列跨度 **2.35mm**。
   选项：(a) 增大 J2 逃逸 x 域/隙列宽；(b) 指定第 4 信号层；(c) 连接器 ball/网表重映射。
   （物理合法性：需保证 0.525 线间距与逃逸区 keepout。）
2. **R1 逃逸竖段同 x 重叠（4 处）**：A-CN.1 仅约束 via 两两 ≥0.525，未约束同 x 竖段。
   可加确定性放置谓词（同 x 竖段不重叠）闭合 —— 项目层、**预授权**、待令即可实施。

## 已披露的度量边界（诚实登记）
- 严格度量覆盖 `r1_5`（逃逸竖段 + 走廊横段）与 `stub`（落段）两类（= 监督 C17 口径）。
- chip 侧 F.Cu pad→via 斜引线与 connector 侧 landing→pad 短段**未纳入**该度量（独立复核提示另有冲突）；
  纳入与否需监督确认口径。

## 计量（rev W3-CN.11，R-23）
```json
{
 "same_layer_crossings": 240,
 "crossings_by_class": {"r1_5": 0, "stub": 0},
 "overlaps_by_class": {"r1_5": 4, "stub": 236},
 "r1_assigned": 32,
 "r1_required": 32,
 "capacity_ok": true,
 "closed_form": "SUFFICIENT iff same_layer_crossings == 0 and capacity ok"
}
```

## Next
在信号层内、不扩域、不改四源的前提下，合法构造族已穷尽；残余为**上游资源不足**，
须 owner 在上述 3 项中裁决（推荐 (a) 增大 J2 逃逸 x 域，最小且不触层叠）。
End of canonical request card (ROOT-15 corrective).
