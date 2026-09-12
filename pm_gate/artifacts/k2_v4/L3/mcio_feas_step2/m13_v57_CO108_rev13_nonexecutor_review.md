# CO-108 — rev-13 新基线**非执行者**对抗复评（L2 · 对象 = CO-106/107 + 链 pin 前移 + 几何/板不变性）

- 判定：**`PASS_WITH_FINDINGS`**（F-A 已在本件校正；F-B 信息性；F-C 已声明待办；F-D 未决前提，须 L3 派生前澄清）
- 复评人：非执行者会话（rev-13 施加者之外的独立会话；`L2_STRUCTURE_v2.0.md:137` 禁自评）
- 对象基线：SPEC rev-13 `7943be727a4f8ef9`｜图纸主件 `73c0066df83fa8c2`（rev-12 blob `cb955e9af8782d08`）｜板 `0e636a67c1472462`
- 工具（本件产物）：`tools/p3_v57_co108_rev13_nonexecutor_review.py`｜记录：`m13_v57_co108_rev13_nonexecutor_review.json`
- 复现：`../AppDir/usr/bin/python3.11 tools/p3_v57_co108_rev13_nonexecutor_review.py`

## 1. 六项独立机判（全部 True）

| 面 | 判据 | 读数 |
|---|---|---|
| **A** SPEC 差分 | rev-13 vs rev-12 的标量差分 **恰为**预期集（10 polygon 顶点 + `spec_version`），无增删键 | n_changed=11；`1.1.spec-rev-12` → `1.1.spec-rev-13`；`added/removed` = ∅（除退役键） |
| **A2** 退役留存 | 5 项 retired：`old_polygon` 逐值 = rev-12、`new_polygon` 逐值 = rev-13；rev-12 无 70.7 顶点未登记、rev-13 无 70.7 残留 | n_retired=5（3×GND In1/In3/In6 + P3V3_EAST + MCU_VDD_WEST）；uncovered=0；left=0 |
| **B** 几何/板不变性 | `route_geometry`/`pages`/`landing_rows` 与 rev-12 **逐字节同**；板逐字节不变；frozen drift=∅ | `c27d9f5b29c82ba2`/`2535f3306cebe6eb`/`74234e98afe7498f`；板 `0e636a67c1472462` |
| **C** 链 pin | 无工具仍以 rev-12 SPEC 为现行（仅 CO-103 历史件合法持有）；记录内 `inputs.*_record` provenance pin 全数一致 | stale=∅；pins_ok=true（co104→co103 / co105→co98 / co98→co95） |
| **D** 参考平面（独立**点级全量**重算） | GND 整面层（In1/In3/In6）缺铜点 = **0**；残余仅 `In5←In4` 54 段 / 1260 点，**100%** 落 x∈(49.8, 88.37) | `class_counts={region_scoped_indeterminate:54}`；outside=0 |
| **E** rev-12 FAIL 复现 + 板实佐证 | 独立复现 CO-106 的 FAIL 读数；板实已用该带 | 60 项/36 段（In2←In1 24 + In2←In3 24 + In5←In6 12）；板实 (70.7,79.0] = In5 **316** / In2 **12** / VIA **24** |
| **F** 牙齿 | 差分 / 连续性 / pin 漂移 检测器负控均触发 | teeth_ok=true（3/3） |

## 2. 发现

- **F-A（low，已校正）**：CO-105 记录的 provenance pin `inputs.co98_record` 在执行者提交态 `04d0ee1` 为 `267f86b5c02b8fc3`，**既非**当时已重基线的 co98 记录 `48b5bd29009a9eb8`、**亦非**任何已提交 co98 版本 ⇒ 记录内部身份引用漂移。CO-77 只校验收口件内 `file`+`sha16` 邻接引用，不覆盖记录内 provenance pin（同 CO-103 F-C 指出的盲区）。
  - **校正**：确定性重跑既有工具 `p3_v57_co105_f4_scope_disposition.py`（无新代码路径、语义不变）⇒ pin 恢复 `48b5bd29009a9eb8`；记录 sha `1e9c5872d1480225` → `a53f7e3b75d3d427`；boundary **v1.73/v1.74** 同步更新引用 + co77 PASS。
- **F-B（informational）**：CO-106 记录字段 `n_declared_copper_missing_points` / `class_counts` 实计 **(段,参考层) 项数**而非采样点数，且分类仅取每 (段,参考层) 的**首个**缺失点。判据成立性不受影响（本件点级全量重算 GND 面缺铜 = 0，与 CO-106 一致）。建议后续 rev 更名或注明计法。
- **F-C（low，已声明待办）**：CO-87 L2 合格标准覆盖矩阵仍为五行、**无「参考平面」行**；CO-106 的 D 项 `ok` 恒真（『补全动作本身』）⇒ **登记册**本身仍不完整（属 CO-106 已明示的缺口，非静默）。建议下一 rev 给 co87 矩阵补行。
- **F-D（medium，未决前提）**：CO-106/CO-98 把 In5←In4 残余 54 段归入 `region_scoped_indeterminate`（语义＝『几何待 L3 派生，非缺陷』）；但 3 个 bridge zone 的**自身声明互矛盾**：
  `layer` 字段 = `In4.Cu`，而 zone 名含 `BCU`、basis 明文经 **B.Cu** 桥接（`P3V3_BCU_BRIDGE_IN4` 更明示『In4 走线带 x∈[50,88.17] 不跨』）⇒『L3 派生会补出该带 In4 铜』这一分类前提**未证实且与 basis 冲突**。
  **若**派生对象取 basis 口径（B.Cu），则 54 段 In5←In4 属**永久**参考缺失，应升级 **L2**（参考平面/阻抗建模）裁定，而非继续标注 `declared_pending_l3`。
  **本件不改判**：CO-98 已明示该桶『≠ 已满足』（非静默掩护），故列为**须在 L3 桥区派生 work order 前澄清**的未决前提：先裁 bridge zone 派生层归属（In4 vs B.Cu）。

## 3. 结论与残余

- rev-13 的改动**确为**「仅多边形顶点 + 版本号」，退役留存完整，几何与板**逐字节不变**，链 pin 全数前移（除 F-A 一处已被本件校正）。
- **CO-106 分类诚实**：`declared_copper_missing=0` 与 `region_scoped_indeterminate` 分类**成立、不以分类掩护缺陷** —— 独立复现了 rev-12 的真 FAIL（3 张 GND 整面层平面在 8.3mm 带无铜，而板实已用该带），CO-107 为真修复。
- **未闭合（非本件责任）**：
  - **L3 桥区几何派生**（与 CO-98 的 14 项同桶，一次 rev 重基线）—— **但须先回答 F-D**：bridge zone 派生对象层是 In4 还是 B.Cu？若是 B.Cu，则 54 段 In5←In4 = 永久参考缺失，须 L2（参考平面/阻抗）裁定；**且该 work order 须由另一会话复评**。
  - PDN 压降/热 = 外部输入（PM）；L1 三项（12V_IN 承载 / P3V3_AUX 西区归属 / L1① 0.875）= owner。
- 非声明：一阶点采样（端点 + 相邻中点），不做网格/有限元；未重跑 L3 桥区几何派生。
