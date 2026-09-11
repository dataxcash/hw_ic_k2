# m13 v57 — **G5（W4 真图验证）收口记录：PASS**

> 2026-09-11｜卡：`m13_v57_w4_kickoff_card_v1.md`｜验证器：`tools/p3_v57_w3_constructive_validator_v2.py`（rev v2.1）
> ｜主体：`m13_v57_w3_joint_assignment.json` rev **W3-CN.22**（FEASIBLE_ALL）｜**独立验证：见 §5**

## 1. 结论
- **G5 PASS**（三报告 + v2 验证器 全 PASS）；**无 partial pass**。

## 2. 产物（版本化新件）
| 文件 | 判定 | 关键数 |
|---|---|---|
| `m13_v57_w4_a12_report.json` | **PASS** | 3 枚举序 → 主件 sha `caa516abdaf8e823…` + landing sha 完全一致 |
| `m13_v57_w4_a13_report.json` | **PASS** | 覆盖 **34 页**（32 data + 2 REFCLK）；强节点 **388**；V1–V7 **0 违例** |
| `m13_v57_w4_a14_report.json` | **PASS** | 0 命中；运行期不读板文件 |
| `m13_v57_w3_validation.json` | **PASS** | G-M1..G-M6 全 PASS；双度量 0（段 0 + 全 via 间距 0）；序无关 PASS；四源 MATCH |

## 3. 覆盖与强节点
- 34 页全覆盖：32 data（V1–V6）+ 2 REFCLK（V7）。
- 强节点普查 **388** = 32 data 页 × 2 极性 × (chip 锚 1 + conn 锚 1 + via 4) = 384，+ 2 REFCLK 页 × witness 锚 2 = 4。

## 4. 契约修订（ROOT-1 生命周期，版本化）
- V2 via ≤ **5**（ROOT-2 R-74）；V3 层对 = {F.Cu, B.Cu, In2.Cu}（ROOT-16）；**V7 REFCLK 新增**（补偿 caveat ①）。

## 5. 独立验证（必须）
- read-only 子代理复核（见 ledger / handoff）：三报告与 v2 验证器可独立重跑；双度量 0 可由主件重算；
  `--enum-order` 输入置换非空转；A1.3 套件独立于引擎实现。
- 反例自检：v2 验证器对 `_W3-CN.13/18`（80 / 1）历史件给出非 0，对 W3-CN.22 给 0（非静默零）。

## 6. 指纹
- 主件 `m13_v57_w3_joint_assignment.json` rev W3-CN.22 `caa516abdaf8e823`
- landing `m13_v57_w3_chip_landing_rows.json` rev W3-CN.22 `5f2dc768c872cafc`（authority == main sha）
- validation `eb5496f0c6c18bb4`｜a12 `787ef5fe325a8afb`｜a13 `b7e9f425e9525c6d`｜a14 `fb52613c9751c122`
- 冻结四源 SPEC `0bd52ed48e720b8c` / manifest `a8ef3ea8ecff99d7` / PCB `f6273de613f43d05` / rules `0a459839e15960b8`

## 7. 下一步
- G6（L4 图纸直构：PCB 原样消费图纸、每节点按处方连接）→ G7（L5 SI/PI/EMC + DFM/DFT + 知识提升评审）。

## ROOT-21 修订（O1b + O3 实施；2026-09-11）
- 图纸 rev **W3-CN.25**（`c17c5a42`）：**REFCLK 差分对 P/N 补齐**（原只布 P；现 2 页 × P/N = 4 条，P/N 分离
  ≥0.38、成对中心取见证 `pair_centre_window_y`/`channel_y`、keepout 零交 A-CN.5a PASS）；net 名取
  manifest（`PCIE_REFCLK*_P/N`）。
- L4 重发：**68 网 / 338 段 / 256 via**（construction `6fb043a1`；validation `9abcc836` PASS；板 `b63e6c09`）。
- D8/G5 验证器 v2：**PASS**（G-M1..G-M6 + 双度量 0 + A1.2/A1.3/A1.4；A1.3 现覆盖 REFCLK P/N）。
- L5 重测：DFM **479**（含新增 N 轨的 26 条）；SI 等长 **skew 24.476mm** 不变 ⇒ **G7 仍 FAIL**；
  **O1**（净距不可行，已实证与域/序无关）与 **O2**（板既有铜/读板）仍待 owner。

## W3-CN.27 复核（G5 重签；2026-09-11，ROOT-21 之后）
- 触发：canonical 由 W3-CN.25（旧口径）→ **W3-CN.27（A-CN.9 完整净距 FEASIBLE_ALL）**，G5 必须对新主件重跑。
- 验证器升 **W3-VALv2.2**（两处契约修订，均版本化记录、不原地改语义）：
  1. **R3 独立重导**纳入 **列序交替偏置 ±0.1 + band clamp + 前缀递推**（该规则由 W3 8L 波次引入，
     见 `m13_v57_w3_8l_progress_v2/v3.md`；旧重导只做 `y = pad_y - 0.3` ⇒ 对新主件 64/64 误报失配）。
  2. **V3 合法层对**扩为 **LID.1 8L 信号层集 {F.Cu, B.Cu, In2.Cu, In6.Cu}**（依据
     `m13_v57_layer_intent_adoption_v1.json`；旧集仅 F/B/In2 ⇒ 对 up 带 In6 段 128 条误报）。
- 重跑结果（**PASS**，无 partial pass）：
  | 门 | 结果 |
  |---|---|
  | G-M1..G-M6 | 全 PASS（G-M4 独立重导 R2/R3 失配 **0/0**；双度量 0；via 间距 0，min 0.527898） |
  | A1.2 序无关 | PASS（validator 以 3 枚举序独立重跑引擎，main/landing sha 逐字节一致） |
  | A1.3 生成即合法 | PASS（**0** 违例；覆盖 34 页，强节点普查 **388**） |
  | A1.4 单向性 | PASS |
  | 四源 / stale_state / misleading_success | 全 PASS |
- 指纹：
  - 主件 `m13_v57_w3_joint_assignment.json` rev **W3-CN.27** `13dfb9f4d74224d9`
  - landing `m13_v57_w3_chip_landing_rows.json` rev W3-CN.27 `e096740627a0101d`（authority == main sha，64 行）
  - validation `9c9510422e730e63`｜a12 `246a86a646496d31`｜a13 `597fa06f949641ce`｜a14 `fb52613c9751c122`
  - validator `tools/p3_v57_w3_constructive_validator_v2.py` rev **W3-VALv2.2**
- 结论：**G5 PASS（W3-CN.27 口径）**。下一步 G6（L4 图纸直构）→ G7（L5 重签，含 O4 对内等长）。
