# O4 对内等长（intra-pair skew）根因定位 v1 — **P/N 落在相距 ~25mm 的不同连接器列**

> 2026-09-11｜作者：ARCHER｜对象：W3-CN.27 图纸（`m13_v57_w3_joint_assignment.json`，FEASIBLE_ALL）
> SPEC `net_classes.PCIe85.intra_pair_skew_mm = 0.15`｜结论：**32/32** 对全部超差，根因单一且可判。

## 1. 量化（由图纸 nodes 独立重算）
- **32/32** 对内 P/N 路径长度差 > 0.15mm；最差 **PCIE_DN7/input = 24.539mm**（P 99.97 / N 75.43）。
- 全部超差对的 `|len(P) − len(N)|` ≈ **|column_x(N) − column_x(P)|**（同一 lane_y 上的水平走廊段差）。

| 页 | len(P) | len(N) | skew | colx(P) | colx(N) |
|---|---|---|---|---|---|
| PCIE_DN7/input | 99.97 | 75.43 | **24.539** | 146.20 | 121.45 |
| PCIE_DN6/input | 74.10 | 98.46 | **24.361** | 122.05 | 145.60 |
| PCIE_DN5/input | 98.49 | 74.83 | **23.659** | 145.00 | 122.65 |
| PCIE_DN4/input | 75.02 | 95.46 | **20.441** | 123.25 | 144.40 |

## 2. 根因（单一）
- 每对差分对的 **P 与 N 被指派到不相同的连接器落位列**：`r3_by_pol.P.column_x` 与 `r3_by_pol.N.column_x`
  相差 **≈ 20–25mm**（E/W 两侧同型，J2 与 J3/J4 皆然）。
- 走廊 run 与 connector stub 都跑在同一 `lane_y`，故两者**路径长差 ≈ 两列 x 之差** ⇒ 直接把 skew 打到 20–25mm。
- 来源：`r3_place()` 的规则「每 pad 取 **min(gap_candidates)** 归组」——r3x2 域对 P、N 各自给出的
  gap 候选集不同，取最小后 P/N 落到连接器扇出区的**两端**，而非相邻列。

## 3. 修复方向（方案层，需 L2/owner 认可后实施）
1. **配对落列（pair-aware）**：同一差分对的 P/N 必须落在**同一列**（或长度等价的相邻列），
   run 长度差即由构造保证 ≈0；域仍取冻结 r3x2 的 **gap_candidates 子集**（不新增自由度）。
2. 若连接器侧 P/N pad 本身不在同一 gap 列，则须由 L2 给出**成对分配到同一/对称列**的落地方案
   （当前候选集是否含"成对同列"解，需在 L2 冻结前裁定）。
3. 复核项：改动 R3 会改变 R1（R1 依赖 R3 landing）⇒ 需重跑 **W3→W4→L4→L5** 一整链，并重签 G4/G5/G6/G7。
4. 与 UC-01 的关系：**O4 与叠层问题正交**（落位列与逃逸层无关）；但两者都会使 W3 图纸失效，
   建议 **合并为一次方案修订**（叠层 + 落位列），避免 W3 收口两次。

## 4. 证据可复算
```python
# 由图纸独立重算（无引擎依赖）：
#   对每 data 页取 nodes[pol] 折线长 len(pol)；skew = |len(P)-len(N)|
#   比对 r3_by_pol[pol].column_x 之差
```
- 全 32 对超差；最差 24.539mm；`skew ≈ |colxN - colxP|`（见 §1 表）。
