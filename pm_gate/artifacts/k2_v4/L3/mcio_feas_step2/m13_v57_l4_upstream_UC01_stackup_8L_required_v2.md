# UC-01（v2）— owner 裁决请求：叠层 binding 冲突（M14 v30 的 6L 物理 ECO ↔ 整改 #03 派生 8L）

> 2026-09-11｜发起：ARCHER（续接会话，独立复核；本轮未改任何冻结源/canonical）｜级别：**owner / L1-L2（结构性、涉制造）**
> ｜状态：**待裁决**。本卡并入并取代 v1 §1 的「owner 二选一」表述；v1
> `m13_v57_l4_upstream_UC01_stackup_8L_required.md` 与 `m13_v57_l4_UC01_provenance_addendum_v1.md` 保留为证据链（不删）。

## 1. 要裁决什么
冻结 PCB 基线 = **6L（3 信号层）**；已收口的 W3 图纸（W3-CN.27）= **4 信号层**，其中 up 逃逸带落在 `In6.Cu`。
`In6.Cu` 在冻结板上**不存在** ⇒ G6/L4-E 结构性不可能（实测写入 192 处未声明层）。请裁定哪条约束 binding。

## 2. 归因：两条裁决冲突，非"owner 选错"
- 6L 来自 **`0db5183`「M14 v30 真板物理 ECO + A/B 端口对账（用户/架构裁决）」** 删除 In5/In6；
- 8L 来自 **整改 #03**「层数/层用途 = 容量闭合**派生输出**，无 owner/工单参数特权」的确定性结果（LID.1）。
- 两者皆有效力 ⇒ 只能在 owner 层消解；L3 无权私了（宪法第九章）。

## 3. 本轮独立复核的事实（命令 → 结果）
| # | 事实 | 证据 |
|---|---|---|
| F1 | 冻结四源 **4/4 MATCH** | `sha256sum`：`0bd52ed48e720b8c` / `a8ef3ea8ecff99d7` / `f6273de613f43d05` / `0a459839e15960b8` |
| F2 | 冻结 PCB = **6 层铜、裸骨架** | 层表 `F/In1/In2/In3/In4/B`；`grep -c`：segment=0 / via=0 / zone=0 / footprint=42 |
| F3 | 冻结 PCB 板框**撕裂** | Edge.Cuts：顶 `(23,33)-(143,33)`、左 `(23,71)-(23,33)`、右 `(143,33)-(143,79)`、底 `(143,79)-(23,79)` ⇒ 左边止于 y=71、底边在 y=79（与 SPEC `outline_y=[33,79]` 亦不符） |
| F4 | LID.1 派生**可复现** | `tools/p3_v57_layer_intent_derive.py --out /tmp/opencode/lid1_verify.json` ⇒ 与 `m13_v57_layer_intent_derived_v1.json` JSON 等价；`L_escape=4`、`signal_layers=[F,B,In2,In6]`、`total_layers_derived=8`、`frozen_stackup_signal_layers=3`、`frozen_stackup_sufficient=false` |
| F5 | 生成器 natively 8L 但**已陈旧** | `tools/k2_gen_v5.py:427-434` HEADER 含 In5/In6；`:47` `BOARD y=[33,71]` ≠ SPEC `y=[33,79]` ⇒ 运行即写盘阻断 |
| F6 | canonical W3-CN.27 = FEASIBLE_ALL | `gate_status.failed=[]`；`upstream_change_request=null`；`route_geometry` 320 段：F 128 / B 64 / In2 64 / **In6 64** |

## 4. 【本轮新增，直接进裁决】A′ 的真实制造代价：192/256 过孔为非通孔
W3-CN.27 的 256 个过孔（32/34 页）按层对统计：

| 层对 | 数量 | 类型（`tools/p3_v57_l4_apply_drawing.py:104-113` 派生） | 可制造性 |
|---|---|---|---|
| `F.Cu↔B.Cu` | 64 | THROUGH | 常规 |
| `F.Cu↔In6.Cu` | 64 | BLIND | 盲孔**或**通孔+背钻（外层可达） |
| `B.Cu↔In2.Cu` | 64 | BLIND | 盲孔**或**通孔+背钻（外层可达） |
| `In2.Cu↔In6.Cu` | 64 | BLIND（实为**埋孔**） | **埋孔：背钻不可达 ⇒ 必须顺序层压（HDI，≥2 次压合）** |

⇒ **强制结论**：`In2.Cu↔In6.Cu` 64 孔为内层↔内层，无法用背钻或通孔替代（背钻会把该孔切断成悬空残桩）。
故 **A′ 隐含 HDI 顺序层压 + 埋孔能力**，不是"普通 8 层通孔板"。
- 参考层穿孔：`F↔In6` 穿越 In1/In2/In3/In4/In5；`B↔In2` 与 `In2↔In6` 各穿越 In3/In4/In5
  ⇒ 每根非通孔须在穿越的 GND/PWR 层开反焊盘（涉 SI/PI 与平面完整性）。
- 根因属结构必然：4 信号层逃逸（`L_escape=4`）自顶层焊盘场起钻，必然产生内层横跨。
- 若 owner 不接受 HDI/埋孔：唯一出路是**重开 W3 派生**（在 via 策略中禁内层↔内层跨层后重解并重证可行性），
  不存在"不改 W3 就降级"的路径。

## 5. 两选项与后果
### (A′) 派生优先（ARCHER 推荐；与已收口的 W3-CN.27 一致）
确认整改 #03 派生叠层（8L）binding ⇒
1. 以**新版本化骨架**替换冻结 PCB 基线（当前 SPEC 板框 y=79 + LID.1 8L；骨架 0 track ⇒ 仅放置与板框保持），
   同步修 `k2_gen_v5.py` 陈旧常量（`BOARD` y=71→79）与 8L 层表；
2. 并入 **O4**（§6）为**同一次修订**，避免 W3 二次收口；
3. 重跑 **W3 → W4 → L4(G6) → L5(G7)**，重签 G4/G5/G6/G7。
代价：板厚/叠层/阻抗变更；**HDI/埋孔（§4）**；成本/交期；冻结四源变更（版本化）。
**前置确认**：owner 须一并接受 §4 的 HDI 后果（明示"允许盲孔+埋孔/顺序层压"）。

### (B′) 物理约束优先
确认 M14 v30 的 6L 为**硬物理约束** ⇒ 将「冻结叠层 binding」升格为 LID 派生的一个冻结硬输入并重跑派生。
已知后果：3 信号层下 **A-CN.9 完整净距已被实证不可行**（ledger：W3-CN.23/24 探针 R1 31/32；②加大逃逸域
WIN2.5→3.5、对域 195,916→571,904 rows 仍 31/32；3 种输入序 natural/reverse/hash 同结果 ⇒ 与域、与序无关，属拓扑级）。
⇒ 不闭合则按第九章升级（资源域 / 净距 / 回 L1），**禁 partial pass**。
表述纪律：(B′) **不得**表述为"放宽净距"——那是整改 #03 明文撤销的 owner 参数特权。

## 6. 并入项 O4（与 UC-01 同一次修订）
- 32/32 差分对超差，最差 **24.539mm**（≫ 0.150mm）；`skew ≈ |column_x(N) − column_x(P)|`（两列相距约 20–25mm）。
- 根因：`r3_place`「每 pad 取 min(gap_candidates)」把同一对 P/N 落到连接器扇出区**两端**（不配对落列）。
- 修法：**pair-aware 落列**（同列/长度等价列，仍取冻结 r3x2 域子集）⇒ 属落地方案（L2）+ R3 规则，需 L2 认可；
  改 R3 会作废 W3 图纸 ⇒ 必须与 UC-01 合并为一次修订。
- 证据：`m13_v57_o4_intra_pair_skew_root_cause_v1.md`。

## 7. 现状与不做的事（红线）
- 门态：G4 PASS（W3-CN.27 / `13dfb9f4d74224d9`）、G5 PASS（W4 重签）、**G6 BLOCKED（UC-01）**、G7 未执行。
- 未裁决前**不动 L4/L5**（跑了只产无效板/无意义读数）；不改冻结四源；不伪造 L4-E / G6 sign-off；
  不以 6L 板承载 In6 图纸；canonical 未被本会话覆写；探针仅落 `/tmp/opencode`。
- 旁证：**O3（L4 REFCLK 网名）已修**（`tools/p3_v57_l4_apply_drawing.py:60-67`，construction 含 `PCIE_REFCLK0/1_P/N`）⇒ 项外移除。

## 8. 请 owner 回复
选 **(A′)** 或 **(B′)**；若选 (A′)，请一并确认是否**允许盲孔 + 埋孔（顺序层压/HDI）**（§4）。
