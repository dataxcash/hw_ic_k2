# CO-69 — 【L2 叠层分配】方案(a) 全链执行：引擎 bump + G4..G7 + SI 判据升级

> 2026-09-12｜定层 **L2**（CO-67 裁定）｜工具 `tools/p3_v57_co69_option_a_chain.py`
> 记录 `df00fccf674ed6bb`｜LID REV6 `05009687a3f01583`｜SPEC rev-5 `1f351194b3e22b7e`｜ALLOC.6 `2ebda54c7b917ef9`

## 1. 引擎 bump（版本化输入）
- `LAYER_PALETTE` -> `['F.Cu', 'In2.Cu', 'In5.Cu', 'B.Cu']`；引擎全量 `In6.Cu -> In5.Cu`；`REVISION_CO16` -> **W3-CN.40 -> W3-CN.41**。
- `F.spec` -> **SPEC rev-5**；`F.layer_intent` -> **LID REV6**；`CO16_ALLOC` -> **ALLOC.6**（stub 层 In6->In5，4 页）。
- L4 applier：track 宽度改**按层**（`impedance.width_mm_by_layer`：F/B 0.205、In2/In5 0.16）。
- L5：SI 判据升级为**按层加权电气长度**；planes 集合 -> In1/In3/In4/**In6**。

## 2. 整链门禁（实测）
| 门 | 判定 | 证据 |
|---|---|---|
| G4 | **FEASIBLE_ALL** | 图纸 `87ef07f280e4dffb`（None crossings）、landing `6b2f73bd014c6eb4` |
| G5 | **PASS**（frozen=None） | validation `14f6d92e0d17cadf` |
| G6 | **PASS** | 板 `0e636a67c1472462`（68 网/2523 段/252 via）、construction `fa5c055b5911d611` |
| G7 | FAB ok / DFM **PASS** / SI **PASS** | new=0 / vanished=0 / 在册未连 0/68；SI `73f9b59ed5f6f3ce` |

**SI（对内等长）**：判据 = 按层加权电气长度（mm-eq @ er_ref=3.99）。
- 升级**前**（仅物理等长）：max **0.9807** > 0.15 ⇒ **FAIL**（REFCLK1：P 全 F.Cu vs N F.Cu+In2 8.745mm）。
- 整改（CO-69，L2 等长）：补偿目标由物理长度改为层加权电气长度 ⇒ max **0.13** ≤ 0.15 ⇒ **PASS**。
- 物理量报告 max 1.1046 mm（层补偿之预期；判据为电气/时延）。

## 3. 复现
- 全链连跑 ×2：11 件产出逐字节一致；板 **0e636a67c1472462** / 图纸 **87ef07f280e4dffb**。

## 4. 开放项
- 板厂阻抗券（SPEC coupon_required=true）——一阶 IPC-2141 未替代 SI9000/券
- ① 对间净空 0.875（中心距 1.580）：本方案(a) 未解（瓶颈 = 板边/球栅逃逸，属 L1 包络冲突，非本件范围）
- 物理 skew 报告量升至 1.1046mm（电气已达标）——若验收方要求物理量亦 ≤0.15，需双变量补偿/重构，属新 L2 议题

## 5. 指纹（冻结四源 4/4 MATCH）
`0bd52ed48e720b8c / a8ef3ea8ecff99d7 / fb07d25ac426ff84 / 0a459839e15960b8`
