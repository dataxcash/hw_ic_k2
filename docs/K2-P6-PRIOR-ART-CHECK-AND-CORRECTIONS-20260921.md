# K2 · P6 · **『先查册再声明』+ 本会话发现的重复更正**

- 索引件：`k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/PRIOR_ART_REGISTRY_INDEX_20260921_v1.json`（sha16 `2c2da4332e48e9fa`）
- 性质：**只读**；流程改进件。未动 `k1/`、`_shared`、`criteria/`、交付锚。
- 日期：2026-09-21 · ENG(ARCHER)

## 0. 问题
本会话**3 次**在声明"新发现"时与**既有登记册**重叠：
| 我的编号 | 实为已在册 | 判定 |
|---|---|---|
| `K1-S6`（J10 footprint 陈旧） | 既有册**无**（仅 OPEN-1 J1 / OPEN-2 U10） | **真新** ✅ |
| `K1-D11`（R35/R36 = 56K） | **`K1-BUILD C-G2-1` FAIL**（`L3/BUILD_REPORT_v2.md`：*『CC 宣告 3A（Rp=10k）… R35=56K R36=56K（目标 10000Ω±5%）』*） | **重复** ✗ |
| `K2-REG-1`（注册册 `DCDC_12V_*` 误挂 TLV61046） | **`K1-GAP G-5`**（`L1/frozen/L1_BID_v2_k1.md §5`：*『`DCDC_12V_5V.yaml` 引脚表实为 **TLV61046(boost)**；`U8` footprint 声明 SOIC-8 而真源 **SOT-23-6** ⇒ **②原理图前必须修**』*） | **重复** ✗ |
| `K1-D10`（U8 声明 vs 符号） | `G-5` + `K1-SYNC G1`（声明变更已记） | **基本重复** ✗ |
| `K1-D8`（Q1/U12 **VBIAS 未接**） | 全册未见（`grep VBIAS` 仅 2 份手册 YAML） | **真新** ✅ |

**结论**：本会话对 K1 的**真新贡献仅 2 条** —— **K1-D8（VBIAS 未接·功能级）** 与 **K1-S6（J10 footprint）**；`D10/D11/K2-REG-1` **已更正为在册引用**。

## 1. 索引（『先查册再声明』）
`PRIOR_ART_REGISTRY_INDEX_20260921_v1.json` 收录**权威登记册**（路径 + 范围 + 关键条目）：
`K1-GAP`(G-1..G-10) · `K1-OPEN`(OPEN-1/2) · `K1-BUILD`(判据判定) · `K1-SYNC`(②声明) ·
`K2-E2PAD`(余量焊盘逐条登记) · `K2-LAND`(land pattern 差异 + 供裁) · `K2-CAP`(C-1..C-25) ·
`K2-PEND`(待裁) · `K2-DEFREG` · `K1-WORKLIST`。

**用法**：声明「新发现/风险」前逐册 grep（器件号/网名/现象）；若已登 ⇒ 只引用编号与状态；确为新 ⇒ 在产物写 `prior_art_checked: true`。

## 2. 本次更正落地
- `K1_BOARD_LEVEL_DEFECT_WORKLIST`：`K1-D10`/`K1-D11` 加 `prior_art` 字段（标注已在册）；新增 `prior_art_crosscheck` 块；`corrections` 追加。
- `PENDING_RULINGS_DELTA_v6`：`K2-REG-1` 与 `K1-D10/D11` **撤回为『新事项』**（改标已在册），并新增 **PRIOR-ART 索引**条目。
- **对监理的净请求因此收窄**：K1 侧**仅 D8(VBIAS) 与 S6(J10)** 属新待裁；其余为在册项复核。

## 3. 边界
只读；未动 `k1/`/`_shared`/`criteria`/交付锚；未新增判据维/检查齿。**监理自裁面。**
