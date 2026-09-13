# L2 裁定 v2.0（CO-206）— 工艺选型 / 性价比对比 + 打样路径 A/B/C

> 层级：**L2**（过孔策略 / 叠层分配 / 工艺类别 —— 宪章第二章 L2 职权明列）｜**更正并取代 CO-204 R1 之定性**
> 板 `d4e81f647be7f980`（**未改动**）｜SPEC rev-19 `5f72182a2616392c`（未改动）｜零坐标搜索｜只读分析
> 依据：监理指令 #13（工艺选型/性价比对比 立为 ENG 常规功能 + 打样路径 A/B/C 对比定案）

## §0 更正 CO-204/Var#12 定性（**本件最高优先级项**）

**撤销**下列表述及其一切派生表述：

| 撤销的表述 | 出现在 |
|---|---|
| 「**JLC 无该通道**」 | `L2_RULING_jlc_standard_through_backdrill_v1.md` R1 |
| 「**不存在**「JLC advanced / 盲埋孔通道」；该表述及据其之旧裁定已撤销」 | `L5/jlc_package/ORDER_NOTES.md` |
| 「JLC advanced / 盲埋孔通道**不存在**」 | `m13_v57_co204_l2_ruling.json` R1 |
| 「CO-204 已判**不存在**」 | `m13_v57_co205t_per_polarity_cursor.json` |

**更正后的准确表述**（三层，勿再合并）：

1. **标准通道**（即时报价流程）**不支持**盲/埋孔：抓取件能力表原文
   *“Blind/Buried Vias — Not supported. Currently we don't support Blind/Buried Vias, only make through holes.”*
2. **advanced 通道支持**（同一抓取件 FAQ 原文）：
   *“Advanced options such as **blind/buried vias**, **HDI (laser vias)**, heavy copper (up to 3oz), and tight impedance control
   provide higher design density and performance but **typically require DFM review** and **may increase both cost and production time**.”*
   ⇒ **盲/埋孔与 HDI（激光孔）是「能做但更贵、须 DFM review」**，不是「做不了」。
3. **未获证项（本工程抓取件未声明，须板厂确认，禁自行补数）**：HDI **阶数上限**、**激光孔径范围**（#13 提及 0.075–0.15mm）、
   盲/埋孔 **DFM 限值**（环宽 / 层对 / 介质厚 / 纵横比）、交期与加价幅度。
   ⇒ 本工程 2026-09-14 复抓（`/tmp/jlc_{cap,hdi,advanced-pcb}.html`，三页均为同一 SPA 外壳）亦**未**含上述数值 ⇒ 记为 `INPUT_REQUIRED`。

> 结论：CO-204 R1 的**推论**（「只能走标准通道 ⇒ 必须消盲埋孔」）不成立；正确命题是
> **「HDI 能做但贵，须评估更便宜的路」**。CO-147（原「绑定 JLC advanced/盲埋孔通道」）方向本无误，但其时无成本依据。

## §1 打样路径 A/B/C（判据先行、可复现）

判据件 `L2/process_route_criteria_v1.json`；执行器 `tools/p3_v57_co206_process_route_select.py`（**ENG 常规功能**，见 §4）。

**设计事实（机判，板 `d4e81f647be7f980`）**：493 via = 通孔+背钻可制 **405** / 需盲埋孔 **88**（全部为 `In2.Cu->In5.Cu` 两端内层 ⇒ **埋孔**）；
物理层序 F|In1|In2|In3|In4|In5|In6|B ⇒ 该埋孔腔 `In2..In5` 上方跳 F,In1、下方跳 In6,B 各 2 层 ⇒ **层压次数下界 = 3**
（等效 HDI 阶数 ≥2 ⇒ 指示性映射，须板厂确认）。

| 路 | 可行性（确定性判据） | 成本 | 交期 | 性能（残桩 / SI） | 主要风险 |
|---|---|---|---|---|---|
| **A** JLC advanced/HDI 盲埋孔 | **FEASIBLE_PENDING_DFM**：88 支埋孔落在 advanced 通道（抓取件有原文）；阶数/孔径限值未获证 | INPUT_REQUIRED（`k_hdi_order`/`k_adv_review`/`k_via_nonstd`） | INPUT_REQUIRED | **残桩 0**；SI 按现行 SPEC 不变 | DFM 结论、加价、交期 |
| **B** 加信号层全通孔（10L） | **UNPROVEN**：充分条件 = 存在层分配使每支孔外层锚定；**必要**条件（确定性）= lane 须落外层（否则 corner 必为内层↔内层 ⇒ 该路无解）；实测 lane 落外层候选 = **24/32**（CO-206b 口径修正：lane 落外层须吃外层 3W=0.615；原 26/32 系探针把 lane 置于**私有内层** In6 所取的乐观值），未达全落位 | INPUT_REQUIRED（`k_layer`） | INPUT_REQUIRED（含重派生 `t_derivation`） | 残桩可至 0；但 lane 移外层=微带 ⇒ 须重签阻抗 | 整层重派生回归面大；可行性未证 |
| **C** 盘中孔 via-in-pad | **PARTIAL_INSUFFICIENT_ALONE**：可替代**仅盲孔**（一端外层）**132** 支；**埋孔 88 支不可替**（埋孔不在任何外层焊盘之下） | INPUT_REQUIRED（`k_vipp`） | INPUT_REQUIRED | 不改残桩性质（解决布线密度） | 单独不足以解阻断 |

## §2 裁决

- **R1′（渠道）**：**不再预先绑定单一渠道**。三路并行按 §1 判据评估；能否送样由「选定路的闸」判定。
  撤销 CO-204「绑定标准通道」之排他性；CO-204 的**技术要求**（外层锚定 / 残桩控制）保留为**择优目标**而非工艺不可能性。
- **R2′（择优目标）**：仍以 **0 盲埋孔 + 残桩 <0.15mm** 为**首选**（SI 最优、标准通道最省）；该目标现定性为
  **成本/性能偏好**，**非**板厂能力边界。
- **R3′（推荐）**：**推荐 A 为默认打样路径**（唯一无需重派生的路；现行图纸即盲埋孔形态；SI 不变）；
  **B 为成本优化候选**，其优先级由可复现决策规则给出：
  `若 quote(10L 标准) + cost(重派生) < quote(HDI 8L) ⇒ 取 B，否则取 A`（参数填入 `cost_model` 后由 CO-206 工具自动复算）。
  **C 单独不可行**，仅可作为 A 或 B 的**辅助**（缓解近焊盘布线密度），不与 A/B 并列。
- **R4′（成本/交期禁编造）**：三路单价/交期参数在本工程语料中**均无验证来源** ⇒ 一律记 `INPUT_REQUIRED`；
  CO-206 工具在缺参时**只输出模型与所需输入清单**，不输出伪数字。

## §2b 口径修正（CO-206b）

B 路的 lane 既须落外层，就必须吃**外层 3W = 0.615**；探针 `_V2B` 把 lane 置于私有内层 In6 ⇒ 3W 取内层 0.48，
所测 26/32 为**乐观值**。按外层口径复测（`CO10_LANE_OUTER`）⇒ **24/32**。本件 §1 表与 CO-206 证据件已同步更正。

## §3 更正域（本件生效后须一致）

`L2_RULING_jlc_standard_through_backdrill_v1.md`（R1 行）、`L5/jlc_package/ORDER_NOTES.md`、
`L5/jlc_package/06_rulings/L2_RULING_jlc_standard_through_backdrill_v1.md`（随包副本）、
`m13_v57_co204_l2_ruling.json`（R1）、`m13_v57_co205t_per_polarity_cursor.json`（next[1]）、
`L2/input_defect_register_v1.json`（该 IMPLEMENTATION_DEVIATION 项 disposition）。

## §4 【常规功能】工艺选型 / 性价比对比（入库，可复用）

- 判据件：`L2/process_route_criteria_v1.json`（判据/参数，换板换厂可替换；零板级特判）
- 执行器：`tools/p3_v57_co206_process_route_select.py`
  `--criteria <json> [--board <pcb>] [--out <json>] [--md <md>]`
- 输出：`可行性 / 成本 / 交期 / 性能 / 风险` 对比 + 推荐 + **所需输入清单**；同输入 ⇒ 同输出（确定性、幂等）。
- 单一真源：过孔普查/层距/残桩复用板厂能力绑定闸同一实现（避免两处口径漂移）。
- 红线：只读；零坐标搜索；不改板/图纸/SPEC/冻结四源；禁编造单价。

## §5 影响与后续（聚焦「定打样路径 + 出包」，停自我验证循环）

- **定案**：打样路径 = **A（JLC advanced/HDI）**；**B** 为报价驱动的替代项；**C** 仅辅助。
- **实施 = WORKER**：按 A 走 HDI 通道询价 + DFM review + 与板厂对齐阶数/孔径限值 ⇒ 出最终打样包
  （Gerber + 钻孔 + 叠层图 + 阻抗表 + ORDER_NOTES + 散热要求）。**本件不动板**。
- **闸**：现行交付板对**标准通道**仍 FAIL（预期，`inner_inner_via_class(88)`）；改挂 **HDI 能力源**后须重跑板厂能力绑定闸。
- **复评债**：本件 + CO-204 + CO-205r/s/t（须另一会话，禁自评）。
