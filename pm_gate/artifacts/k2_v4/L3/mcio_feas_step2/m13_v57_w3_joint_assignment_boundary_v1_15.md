# m13 v57 — W3 Boundary **v1.15**（ROOT-21 收口：**FEASIBLE_ALL under A-CN.9 完整净距**）

> 契约 `m13_v57_w3_kickoff_card_v1_28.md`（冻结，未改）｜引擎 rev **W3-CN.27**
> ｜取代 v1.14（W3-CN.20，旧口径）。授权：ROOT-21（本会话，整改 #03 的 8L/LID.1 派生叠层延续）。**冻结四源未动（4/4 MATCH）**。

## 1. 收口结论（完整度量，机器可判 + 工件可独立重算）
- `verdict = FEASIBLE_ALL`；`gate_status.failed = []`；`certificates = []`；`resource_gate.verdict = SUFFICIENT`。
- `same_layer_crossings = 0`（真交叉 `{r1_5:0, stub:0}`；共线重叠 `{r1_5:0, stub:0}`）。
- **A-CN.9 完整净距 = 0/0/0**：`track−track 0` / `via−track 0` / `via−via 0`；
  **异网 via 最小中心距 0.527898 ≥ 0.525**（256 个 via：via1/corner/drop/land）。
- R1 **32/32**、R2 FEASIBLE、R3 **72/72**、REFCLK **2/2**、34 页（32 data 含 nodes + 2 refclk）、`route_geometry` **320** 段。
- **F-12 原子重发射** `m13_v57_w3_chip_landing_rows.json`（rev W3-CN.27，64 行），
  `authority.main_sha256 == sha256(m13_v57_w3_joint_assignment.json)`。**W4 解封**。

## 2. ROOT-21 三处根因修复（全部为“谓词/语义”修复，非调参）
1. **删 stale seed**（引擎 `r1_place`）：phase-2 会重放**全部 32 页**，但 `_placed` 原先由 phase-1
   投机解 `out` 播种 ⇒ 每页都在规避**随后会移动**的旧坐标（伪障碍）⇒ 级联外推
   （典型：`UP1/out_J2.N via` 被推到 2.15mm 外，长 breakout 扫过邻网 pad ⇒ tt/vt）。
   修复：`_placed = {}`（真顺序构造：只规避**已定稿**页）。
2. **补齐 A-CN.9(vt/tt) 谓词**（引擎 `r1_place` 候选检查）：原构造只查 via−via(0.525) 与
   竖段−竖段(0.38)，**缺 via−track(0.4525) 与 pad−track(0.3525)** ⇒ L5 暴露的净距在构造期不可见。
   修复：候选 via 顶点 × 已放置同层 track、候选 track × 已放置同层 via，双向检查；
   `#fcu_pad/#fcu_land`（pad-access）用 `escape_clearance_mm=0.075` 档（ECN-001）。
   阈值为**冻结 SPEC 派生常量**，`main()` 内断言与 SPEC 一致（drift ⇒ exit 3，不静默放行）。
3. **全局 pad 障碍**：chip pad 是**固定 F.Cu 实体**（manifest 几何），与放置顺序无关；
   仅索引“已放置页”的 pad 会漏掉**尚未放置页**的 pad ⇒ 长 breakout 扫过邻页 pad（0.072 短路类）。
   修复：`_PADALL` 全页 pad 分桶索引，候选 `#fcu_pad` 对**所有异页 pad** 检查 0.3525。

附：**发射层一致性修复**——t2 节点/via 发射原先硬编码 `B.Cu`，与内部“dn→B.Cu / up→In6.Cu”
分层规则不一致，导致**工件与度量几何不符（工件不自洽）**。修复为按带取 `_L`（节点、via layers、
`r3.layer_chain`、`decision_contract.data_layer_chain_by_band` 同步）。

## 3. 可验证性（R-104 延续）
- 主件持久化 `pages[*].nodes` + `pages[*].vias` + `route_geometry`（320 段）+ `verification_check`。
- **独立重算器**（仅读主件 JSON、自带几何核与阈值、不 import 引擎）：
  `viol_track_track = 0 / viol_via_track = 0 / viol_via_via = 0`，`n_via_points = 256`，与主件一致。
  （修复前同一重算器命中 36 tt / 82 vt ⇒ 证明该重算器**非静默零**。）
- **序无关 A-CN.6**：`--enum-order natural|reverse|hash` 三跑 **byte-identical**
  （sha256 `74276c0b1a0125b7…`，47–63s）。

## 4. 复杂度 / 性能
- wall ≈ **47s** ≤ 120s 护栏（构造 `_vt_*` 检查在 `_va`/`_vb` 预筛后触发，索引 O(1) 分桶）。
- `--scale`：work(K=2)=**1076**、work(K=4)=**2152** = K×538（线性），`matches_formula=True`。

## 5. 方法门（G-M）
- **G-M1** AST `while=0`、`enumerate=0`、无自调用 → PASS；**G-M2** 无回溯/无备选枚举；
  **G-M3** work 公式匹配且线性；**G-M6** 无禁用键。
- 无搜索、无重试、无 fallback 挪件；候选域 = 离线 F-13 域 ∪ 固定 pad 障碍（常量时间）。

## 6. 指纹
| 项 | 值 |
|---|---|
| 冻结四源（MATCH） | SPEC `0bd52ed48e720b8c` / manifest `a8ef3ea8ecff99d7` / PCB `f6273de613f43d05` / rules `0a459839e15960b8` |
| engine | rev **W3-CN.27**（`tools/p3_v57_w3_constructive.py`） |
| main artifact | `m13_v57_w3_joint_assignment.json` rev W3-CN.27 / FEASIBLE_ALL / sha16 `13dfb9f4d74224d9` |
| landing | `m13_v57_w3_chip_landing_rows.json` rev W3-CN.27 / 64 行 / sha16 `e096740627a0101d`（authority sha == main sha） |
| 派生叠层 | LID.1 8L（`m13_v57_layer_intent_rev5.json`；signal=F/In2/In6/B） |
| 域 | `m13_v57_f13_r1_pair_coupling_v1_4.json`（F13-R1PAIR.6，未改） |

End of boundary v1.15.
