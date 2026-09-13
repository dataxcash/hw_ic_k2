# CO-206.3 工艺选型 / 性价比对比（A/B/C）

板 `k2_v4_8L.l4.kicad_pcb` sha16 `d4e81f647be7f980`｜判据件 `pm_gate/artifacts/k2_v4/L2/process_route_criteria_v1.json` sha16 `e4654aeda2cab72d`｜介质总厚 1.425mm

过孔普查：493 支；通孔+背钻可制 **405**；需盲/埋孔 **88**（其中两端内层=埋孔，层压次数下界 >= 3）

| 类 | 支数 | 外层锚定 | 残桩 mm | 通孔+背钻可制 |
|---|---|---|---|---|
| F.Cu->B.Cu | 273 | 是 | 0.0 | 可 |
| F.Cu->In2.Cu | 92 | 是 | 0.0 | 可 |
| F.Cu->In5.Cu | 8 | 是 | 0.0 | 可 |
| In2.Cu->In5.Cu | 88 | **否** | 0.3664 | **不可** |
| In5.Cu->B.Cu | 32 | 是 | 0.0 | 可 |

## A/B/C 对比

| 路 | 可行性 | 成本 | 交期 | 性能（残桩/SI） | 风险（摘要） |
|---|---|---|---|---|---|
| **A** JLC advanced/HDI 盲埋孔（专属通道） | FEASIBLE_PENDING_DFM | INPUT_REQUIRED | INPUT_REQUIRED | 盲埋孔为设计意图形态，无背钻残桩；SI 按现行 SPEC 不变 | DFM review 结论未知（可能退回改设计） |
| **B** 加信号层全通孔（如 10L） | UNPROVEN | INPUT_REQUIRED | INPUT_REQUIRED | 全通孔+背钻 ⇒ 残桩可至 0；但 lane 落外层 = 微带，须重签阻抗与 SI | 可行性未证：lane 落外层口径 **24/32**（CO-206b 口径修正；原 26/32 系 lane 置**私有内层** In6 所取之乐观值） |
| **C** 盘中孔 via-in-pad（6+ 层成熟工艺） | PARTIAL_INSUFFICIENT_ALONE | INPUT_REQUIRED | INPUT_REQUIRED | 不改变残桩性质；解决的是布线密度 | 不能替代 88 支埋孔 ⇒ 单独不足以解阻断 |

## 依据（可行性）

**A**
- 需盲/埋孔支数 = 88（不在标准通道可制集内）
- 物理层序推得**层压次数下界 = 3**（In2..In5 腔：上方跳 F,In1 / 下方跳 In6,B 各 2 层）
- 等效 HDI 阶数 >= 2（指示性映射，须板厂确认；本工程抓取件未声明阶数上限）
- 抓取件 FAQ 明列 advanced options 含 blind/buried vias 与 HDI (laser vias)，须 DFM review

**B**
- 充分条件：存在层分配使每支孔外层锚定（F1 全过）
- 必要条件（确定性）：lane 必须落外层，否则 corner 为内层<->内层 ⇒ 该路无解
- 实测（修正 span）：lane 落外层候选 = **26/32**；但 lane 落外层须吃**外层 3W(0.615)**，按外层口径复测（CO10_LANE_OUTER）⇒ **24/32** ⇒ 未达全落位，可行性未证

**C**
- 可替代：仅**盲孔**（一端外层）= 132 支
- 不可替代：**埋孔**（两端内层）= 88 支 —— 埋孔不在任何外层焊盘之下
- 抓取件明列 Via-in-Pad Process（epoxy/copper paste filled & capped，4-32 层，可在 BGA 焊盘内放孔）

## 推荐

**A**（次选 B）

- ① 可行性：A 是本设计**唯一无需重派生**即可落地的路（现行图纸即盲埋孔形态；B 可行性未证 —— lane 落外层口径 **24/32**（CO-206b）；C 不能替埋孔）
- ② 性能：A 无背钻残桩，SI 按现行 SPEC 不变；B 需把 lane 移外层（微带）并重签阻抗
- ③ 风险：A 的风险集中在**报价与 DFM review 结论**（可询价收敛）；B 的风险是整层重派生回归 + 可行性未证
- ④ 成本（**已求值**，非声明）：B **可行性未证**（须 32/32 全落位；现行最优 24/32）⇒ **规则前置不满足**；判据序 = 可行性 > 性能 > 风险 > 成本

可复现决策规则：`B_feasible_proven AND C_B(+重派生) < C_A` ⇒ `B`；否则 `A`。

