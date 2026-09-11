# CO-04 — O4 对内等长：L2 落地列裁定 + 可行性证据（G7 并入项）

> 2026-09-11｜发起：ARCHER｜依据：**整改 #06**（L2 裁判权：叠层/走廊/过孔策略/等长窗口）｜级别：**L2**
> ｜状态：**裁定完成 + 可行性已证**；构造件与全链重跑（W3→W4→L4→L5）为后续动作。

## 1. 根因更正（推翻 v1 的"L3 r3_place 取 min"归因）
- `m13_v57_f8_r3_gap_candidates_r3x2.json` 实测：**72/72 pad 的 `gap_candidates` 为单元素（singleton）**
  ⇒ `r3_place()` 的 `min(gap_candidates)` **无选择空间**，不是根因。
- 真正来源（L2 域）：
  1. **R3X2 槽规则**：J2 内列向左、外列向右，各 pad 按 rank 以 0.6mm 递推唯一槽
     （`slot = base + sgn*rank*0.6`）⇒ 同一差分对 P（内列）与 N（外列）落在**相反方向**：实测
     `PCIE_DN0_P → 125.65`、`PCIE_DN0_N → 142.0`（相距 **16.35mm**）。
  2. **SPEC 约束**：`SPEC.constraints.j2_escape_topology` = `{inner_escape:left, outer_escape:right}`（P/N 反向逃逸）。
  3. 二者叠加 ⇒ 走廊 run 同 `lane_y`、落列横距 16~25mm ⇒ skew ≈ |column_x(N) − column_x(P)|（15.6~24.5mm）。
- F-8 `conflict_graph` 把**成对同槽**（如 `gap_x=133.825, pad_a=PCIE_DN0_P, pad_b=PCIE_DN0_N, dy_mm=0`）标为冲突（required 0.525），
  故域主动把 P/N 分向两侧 —— 这是**域的保守建模**（未计入 R3 前缀递推可给出 0.6mm 纵向分离）。

## 2. 独立长度核（可复算，非引擎自证）
按图纸 nodes 构造 t2 路径长：`L = d(pad,v1) + |ly−v1y| + |lx−v1x| + |ly_l−ly| + d(conn,(lx,ly_l))`。
- **校验**：对 canonical W3-CN.27 全部 64 网，`|L_formula − Σ|node_i−node_{i+1}||` **误差 = 0.0**（逐网精确）。
- 现状：32/32 对超差（>0.15mm），与 O4 文档一致。

## 3. 可行性（裁定依据）
在**合法落列窗口**（各对两个候选点 ±3mm）内自由选 `lx`，并在**各自 y_band**（±0.3mm）内调 `ly_l`：
| 页 | min\|ΔL\| | 取解 (lxP, lxN, Δx) |
|---|---|---|
| PCIE_UP6/input | **0.0000** | (57.8, 59.6, 1.8) |
| PCIE_UP7/input | **0.0000** | (60.2, 60.6, 0.4) |
| PCIE_DN0/input | **0.0000** | (133.25, 122.65, 10.6) |
| PCIE_DN0/out_MCIO | **0.0000** | (60.2, 60.2, 0.0) |
- 另：限制为**成对相邻槽**（Δx ≤ 1.2mm）时 31/32 可达 ≤0.15mm（worst 1.71）⇒ 需要**成对局部、幅度受限**的落地方案。
- 结论：**落列 + 带内 y 调优的 L2 方案空间存在 ≤0.15mm 解**（且余量为 0 而非"放宽预算"）。

## 4. L2 裁定（本单）
1. **采纳成对局部落列**：同一差分对的 P/N 落在**成对局部窗口**内的互异槽（0.6mm 网格、互异 ⇒ 自动满足 via↔via 0.525），
   并按其 y_band 内**闭式长度均衡**选 `ly_l`，使 `|ΔL| ≤ 0.15mm`（SPEC `intra_pair_skew_mm`）。
2. **修订 J2 逃逸拓扑**：`inner_escape/outer_escape` 的同向或成对可共用方向，须以"成对局部窗口"为准（版本化 SPEC 修订件，原件不动）。
3. **构造必须闭式/确定性**（零搜索）：槽分配 = 成对序号 → 连续槽位；`ly_l` = 由 `L_P(lx_P,y)=L_N(lx_N,y)` 解析求解（分段线性 + 单变量单调）。
4. **不得**以放宽 `intra_pair_skew_mm` 取代构造（属"参数特权/放水"红线）。
5. 域器件版本化：`m13_v57_f8_r3_gap_candidates_r3x3.json`（新件；r3x2 不动）+ 引擎 `layer_intent/r3_gaps` 输入与 `FROZEN_SHA` 版本 bump。

## 5. 后续动作（G7 并入）
`W3(REV bump: W3-CN.28 成对局部落列) → W4(G5 重签) → L4(G6 重跑, 期望 L4-A..E True) → L5(G7 重签，SI 判据 max_intra_pair_skew ≤ 0.15)`；
每步按 TAG_POLICY 先 commit+push（k2 → 父仓 bump），证据落 ledger。

## 6. 红线
冻结四源原件不动（仅新增版本化件）；canonical 未被本单改写；零搜索；零参数放水；L2 裁定依据可追溯（#06 + 宪法第二章 L2 域含"走廊分配/过孔策略/等长窗口"）。
