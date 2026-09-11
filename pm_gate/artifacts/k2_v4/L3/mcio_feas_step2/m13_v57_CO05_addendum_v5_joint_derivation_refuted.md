# CO-05 追加 v5 — 自纠 v3：O4 **不可**由纯 R1.5+R3 联合 (via1, landing) 派生闭合

> 2026-09-11｜发起：ARCHER（L2 裁判，依整改 #06）｜性质：**自纠 + 单次预登记引擎实验（负结果）**｜级别：L2
> ｜结论：追加 v3 的"O4 可闭合（32/32）"**撤回**。联合派生在**长度侧可达**，但平衡所需的
> via1 位移（|Δv1x| ≈ 落列分离 4~10mm）**破坏平面扇与净距**；O4 需 **L3 长度补偿** 或 **L2/L1 结构变更**。
> **禁**放宽 `intra_pair_skew_mm`。

## 1. 更正 v3（v3 遗漏的两个约束）
追加 v3 的"32/32 可达 min|ΔL|=0"只用 (lxP,lxN) ∈ {声明 gap} 与 via1 ∈ verdict 盒，**未计入**：
1. **落列竖段唯一性**：同带（dn=B.Cu / up=In6.Cu）内每个落列竖段 `(lx,ly)->(lx,ly_l)` 都跨越
   近全 lane 高度 ⇒ 任意两 pad 的落列 **x 必须互异（≥0.38mm track-track）**；同列即共线重叠 = 短路。
   引擎实测确认（把 PCIE_DN0/input 的 N 落到 P 同列）⇒ `A-CN.3b FAIL + A-CN.9 FAIL + stub overlap=1`。
2. **平衡所需 via1 位移量级**：`L = |pad−v1| + |ly−v1y| + |lx−v1x| + |ly_l−ly| + |conn−(lx,ly_l)|`，
   其余项小且固定 ⇒ 令 `|ΔL|≤0.15` 须 `|Δv1x| ≈ |Δlx|`（4~10mm），远超"pad 邻近、近垂直 breakout"区间。

## 2. 合法落列几何与分离下界（F-8 域，`tools/p3_v57_f8_r3_gap_candidates.py:94-104`）
- J2 两列 132.65(inner)/135.0(outer) ⇒ 合法列仅 **left 半无穷 (≤131.65)**、**唯一 between 中缝 (133.825 ±0.175)**、
  **right 半无穷 (≥136.0)**；SPEC `j2_escape_topology` 定 inner→left、outer→right。
- 落列竖段唯一 ⇒ 每对分离 `sep = lx_right − lx_left`。
  ⇒ 至多 1 对可 sep=2.175（占唯一中缝）；其余 7 对 `sep ≥ 4.35 + 0.38·(p+q)`（p,q ∈ 0..7 互异）
  ⇒ **存在一对 sep ≥ 4.35+0.38·6 = 6.63mm**。

## 3. 长度侧独立核（工具 + 版本化证据）
`tools/p3_v57_o4_joint_feasibility.py`（独立长度核，不 import 引擎构造路径）⇒
`m13_v57_o4_joint_feasibility_probe.json`：16 个 J2 页各自 `dx_max = 8.53~9.67mm`（≤dx_max 即可达 ≤0.15mm）；
秩分配（sep 4.35..9.67）**两带均可行** ⇒ **长度侧 FEASIBLE**。
⇒ 长度侧不是瓶颈；瓶颈是**几何**（见 §4）。

## 4. 引擎联合探针（CO-05b prototype；单次预登记运行，产物仅 /tmp + 版本化证据）
实现：`r3_place` 成对落列（inner/outer 分侧、同带列互异）+ `r1_place` 选键优先 `|L_P−L_N|`（仍走引擎净距/平面扇谓词）。
| 项 | 实测 |
|---|---|
| verdict | **UPSTREAM_CHANGE_REQUEST** |
| failed | **A-CN.1b / A-CN.4 / A-CN.9** |
| same-layer crossings | **5**（`#fcu_pad` 扇面失效：DN↔UP 与同页 P/N）|
| A-CN.9 | tt 8 / vt 74 / vv 3 |
| A-CN.1b | 例 `PCIE_UP6/input.N ↔ PCIE_UP7/input.P = 0.335 < 0.525` |
| max intra-pair skew | **10.9145mm**（24/32 页 >0.15）|
归因：平衡 O4 所需的 via1 位移使 F.Cu breakout 扫过邻页 ⇒ 平面扇失效、via/track 净距违例。
证据：`m13_v57_co05b_joint_probe_result.json`、`m13_v57_co05b_probe_engine_W3-CN.28.py.txt`（引擎已**回退 W3-CN.27**）。

## 5. 裁定（L2）
- **O4 不可由纯 R1.5+R3 联合 (via1, landing) 派生闭合**（同盘内长度与平面扇/净距冲突）。追加 v3 **撤回**。
- **不得**放宽 `intra_pair_skew_mm`（红线）。
- O4 与 UC-01(叠层) 正交；本裁定不改 G6（L4）已 PASS 的状态。

## 6. 后续可选路径（按代价排序，均属我方 L2/L3 可裁决）
1. **L3 长度补偿（推荐先做可行性预检）**：成对落列取最小 sep（4.35~9.67），残余 ~4~10mm 由
   **短极 serpentine** 吸收；须先证 lane 1.46mm（run 层 In2）下绕线空间（节距≥3w、±0.35mm 横摆）。
   预检一次（预登记判据）→ 若可行再进施工。
2. **L2 结构变更**：J2 逃逸拓扑/落列层规则重开（如分极落列层），或连接器球重映射（**触权威网表 → L1/owner**）。
3. **owner 裁决**：R1 逃逸窗 >2.5mm（O1 类）以扩大 via1 位移能力——但 §4 表明位移本身破坏平面扇，**不解决**。

## 7. 红线 / 状态
未改冻结四源；canonical `13dfb9f4d74224d9` 未动；resource_gate `9b23c657dd4d72c1` 未动；引擎已回退；
单次预登记运行（非扫描）；探针产物仅 /tmp；**G7(O4) 仍 OPEN**。
件：`tools/p3_v57_o4_joint_feasibility.py`、`m13_v57_o4_joint_feasibility_probe.json`、
`m13_v57_co05b_joint_probe_result.json`、`m13_v57_co05b_probe_engine_W3-CN.28.py.txt`。
