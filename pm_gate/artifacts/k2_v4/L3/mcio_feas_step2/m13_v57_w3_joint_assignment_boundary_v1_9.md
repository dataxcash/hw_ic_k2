# m13 v57 — W3 Boundary **v1.9**（ROOT-15 纠正：严格度量下**未收敛**，撤回 v1.8 的 FEASIBLE_ALL）

> 契约 `m13_v57_w3_kickoff_card_v1_23.md`｜引擎 rev **W3-CN.11**（`42f3eee8fab4d9f7…`）
> ｜取代 v1.8（`m13_v57_w3_joint_assignment_boundary_v1_8.md`，commit `e550df9`，保留不动）。
> 授权来源：ROOT-15 执行令（监督）；**冻结四源未动**；零坐标搜索。

## 0. 纠正声明（重要，诚实留痕）
- v1.8（commit `e550df9`）宣称 `FEASIBLE_ALL`。该结论**被独立子代理复核证伪**，本版**撤回**。
- 证伪依据：v1.8 的 `same_layer_crossings` 度量**遗漏「同层异网共线重叠」（= 短路）**，
  只计真交叉（transversal）；且 stub 类在更早版本曾因守卫 bug 为空集。
- 本版改用**严格冲突度量**：真交叉 **+ 共线重叠**（同层异网），并修一处真实缺陷
  （页面/节点对 P/N 用了同一个 R3 landing；现改为**按极性**取各自 landing）。

## 1. 本次纠正后的真实计量（rev W3-CN.11）
- `verdict = UPSTREAM_CHANGE_REQUEST`（**未达 FEASIBLE_ALL**）；`certificates = []`（R1 无证书）。
- `same_layer_crossings = 240`；`crossings_by_class = {r1_5: 0, stub: 0}`；
  `overlaps_by_class = {r1_5: 4, stub: 236}`。
- R1 **32/32**（64 via 两两 ≥0.525）、R3 **72/72**、REFCLK **2/2**、每线 **4 via ≤5**。
- `landing_rows` **未重发射**（F-12 仅在 FEASIBLE_ALL 时发射）；v1.8 的 landing 已归档为
  `m13_v57_w3_chip_landing_rows_W3-CN.10.json`（superseded，不再作为当前交付）。**W4 不解封**。

## 2. 本轮真实修正（相对 v1.8）
1. **严格冲突度量**：`count_crossings` 现返回 (真交叉, 共线重叠) 两套按类计数；`same_layer_crossings`
   = 两者之和；同网（同 base pid + 同 pol）相邻段不互比。
2. **按极性 R3 landing**：页面/节点/stub 路由对 N 使用 `nets["N"]` 的 R3 落点（此前误用 P 的）。
3. **river 扇出**保留（真交叉 46→0），但其暴露的**共线重叠 236** 是资源不足的直接表现（见 §3）。

## 3. 残余根因（上游，闭式）
- J2 一条隙列仅 2 个 x 候选、中距 **2.35mm**，却有 **16 net** 需逃逸；
  `needed_span = (16−1)×0.525 = 7.875mm` ≫ 2.35mm ⇒ **隙列 x 域放不下** ⇒ 落段共 x 重叠。
- 另 4 处 = R1 逃逸竖段同 x 重叠（A-CN.1 只约束 via 两两间距，未约束竖段）。
- 结论：信号层内、不扩域、不改四源的可达路径**未找到**；须 owner 裁上游项（见请求卡）。

## 4. 方法门（G-M）
- **G-M1** 去注释/去字符串 NAME 令牌 0 命中（含 while/enumerate）→ PASS。
- **G-M2** `while`=0、自调用=0、itertools/random import=0 → PASS。
- **G-M3** `work_units==公式`；`--scale` work(2)=1052 / work(4)=2104 = K×526（线性）；wall ≈6.5s ≤120s。
- **G-M6** 工件无 alternatives/options/tried/branch/attempts 键。
- **G-M4** `m13_v57_w3_validation.json` 仍为 T-2 前快照（D8 未清）。

## 5. 指纹
| 项 | 值 |
|---|---|
| 冻结四源（MATCH） | SPEC `0bd52ed48e720b8c` / manifest `a8ef3ea8ecff99d7` / PCB `f6273de613f43d05` / rules `0a459839e15960b8` |
| engine | `tools/p3_v57_w3_constructive.py` rev **W3-CN.11** `42f3eee8fab4d9f7…` |
| main artifact | `m13_v57_w3_joint_assignment.json` rev W3-CN.11 `46c90a5efbf38464…`（UPSTREAM_CHANGE_REQUEST）|
| resource / R-23 gate | `m13_v57_w3_resource_gate.json` `5a0ab3e33f3446a9…` |
| F-13 v1.2 pair 域 | `3a08c4634bbd1d5c…` |

End of boundary v1.9.
