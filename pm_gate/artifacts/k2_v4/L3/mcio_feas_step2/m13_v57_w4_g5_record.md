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
