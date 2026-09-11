# CO-76（非执行者侧对抗评审 pass 1/2）— 对象 CO-67..CO-75；发现 F1/F2/F3 并修复

> 日期 2026-09-12｜记录 `m13_v57_co76_nonexecutor_review.json` `cf5b4ec0e880e5d2`｜链 `m13_v57_co74_chain.json` `51dbb2076bc379e4`｜探针 `m13_v57_co69_adversarial_review.json` `6daec5df8bf0d118`
> 宪法依据 `L2/frozen/L2_STRUCTURE_v2.0.md:137`（重开层须重新过对抗评审）；CO-69 仅**执行者侧**。

## 0. 评审者独立性

本会话与 CO-67..CO-73 执行者**非同一会话**（context 归零后仅据 handoff/ledger 续接）⇒ 对该链具非执行者资格。
CO-74/CO-75 为本会话改动，**已排除**在评审对象外。本件为 **pass 1/2**；修复后 revision 的第二路非执行者评审仍欠。

## 1. 发现

| # | 严重度 | 类 | 内容 |
|---|---|---|---|
| **F1** | 中 | 声明/工件正确性 | 引擎把**陈旧层角色写进生产图纸**：`p3_v57_w3_constructive.py` 的 `decision_contract.r1_5_layer_rule` = `... (dn=B.Cu, up=In6.Cu) ...`。LID REV6 下 **In6=GND 平面**，且引擎实现本即 `up -> In5.Cu`（`"B.Cu" if band=="dn" else "In5.Cu"`）⇒ 声明与实现/叠层相互矛盾。**与 CO-72/73 同类缺陷，但落在引擎/图纸**（CO-73 只扫了 SPEC 文本）。 |
| **F2** | 中 | 验证覆盖洞 | CO-69 的 A5 探针断言 `'"In6.Cu"' not in eng`（**带引号**字面量）。CO-68 已把代码字面量改成 `"In5.Cu"` ⇒ 该断言恒真，**结构上无法**发现未加引号的层角色文本（实测 **14 处**裸 `In6`）。 |
| **F3** | 低 | 文档 | 10+ 处注释/docstring 仍以 In6 为信号/通道层，且**与同行代码矛盾**（如 `n.append(..., "In5.Cu")  # ... In6`）。 |

## 2. 修复（文本类，零几何）

- **F1**：`up=In6.Cu` → `up=In5.Cu`（引擎文本；图纸 `decision_contract` 随之更新）。
- **F3**：10 处 In6 信号层表述 → In5；修毕引擎仅剩 1 处 `In6`，且为**显式迁移注**（`CO16-ALLOC.7（CO-69：stub 层 In6->In5，随 LID REV6）`）。
- **F2**：A5 改为**裸 token 扫描 + 显式豁免 `In6->In5` 迁移注**（`in6_unallowed`）。**修复前的强化断言会 FAIL ⇒ 有齿**（非事后合理化）。

## 3. 机判校验（11 项，全 PASS）

| # | 校验 | 结果 |
|---|---|---|
| C1 | 引擎 palette = `F/In2/In5/B`；无未豁免 In6 文本 | PASS |
| C2 | 图纸 `decision_contract` 无 `In6`、含 `up=In5.Cu` | PASS |
| C3 | 图纸**零** `In6.Cu` 层字段；`route_geometry/pages/layers` 与 rev-7 基线逐字节同 | PASS |
| C4 | 板段层 ⊆ {F,In2,In5,B}；**In4/In6 段 = 0**；zone 仅 F.Cu（keepout 规则域 `ESC_J2/J3/J4/U6`） | PASS |
| C5 | A5 加固在位 + CO-69 记录 verdict PASS、无 failed | PASS |
| C6 | 引擎消费 `ALLOC.7`（非陈旧 ALLOC.5）；LID 域不变量（8 层/4 平面/3×GND+1×P3V3/4 信号层） | PASS |
| C7 | ① 负结果在位（CO-75：23 探针 / 0 命中 / 基线 32/32） | PASS |
| C8 | 四冻结源 4/4 MATCH | PASS |
| C9 | 本会话工具**无 `while`**（闭式、零坐标搜索） | PASS |
| C10 | 阈值未放宽（`capacity_audit.inter_pair_spacing=1.46`、`pitch_fallback=1.08`、`drc_rules 0.875`） | PASS |
| C11 | SPEC rev-8：power_zones 全 In4、B.Cu 电力铜 PROHIBITED、`in6_segments` 退役、3 条 `retired_*` 留存、`CO-72-PDN-1` ruled | PASS |

## 4. 全链重基线（文本修正后）

| 门 | 判定 | 证据 |
|---|---|---|
| G4 | **FEASIBLE_ALL**（34 页 / crossings 0 / work 546-546） | 图纸 `22c2a15835857f99`；landing `b71834b43a8f2455` |
| G5 | **PASS**（G-M1..6 True、A1.2/.3/.4 True、frozen=True） | `m13_v57_w3_validation.json` `eac5eee6f8203d01` |
| G6 | **PASS** (viol 0; 68 网/2523 段/252 vias) | 板 **`0e636a67c1472462`（逐字节同）** |
| G7 | **PASS**（DFM new=0 / SI skew 0.1300） | dfm `40445f87be664f31`、si `73f9b59ed5f6f3ce`（均同基线） |

**delta 精确性**：与修改前图纸（`918cc528` @ v1.40）相比，`pages` / `route_geometry` **逐字节同**，
`decision_contract` 仅 `r1_5_layer_rule` 一字符串变化（`up=In6.Cu` → `up=In5.Cu`）；板字节不变。
链记录工具已改钉 CO-76 后值并注明该声明层 delta。

## 5. 结论与残余

- 评审**通过**（11/11），F1/F2/F3 已修复；**非执行者 pass 1/2 完成**，第二路仍欠。
- ① 对间净空 0.875（=中心距 1.580）**维持 L1**，证据见 CO-75；无 L2 剩余。
- 一阶结论，未经 SI9000/板厂券；阈值全程未放宽。
