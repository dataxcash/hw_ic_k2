# CO-46 — 【L2/L3 自裁】G5 独立验证器冻结集校正：补宪法红线 SPEC 原件 + 8L 冻结板（保留 6L 上游钉扎）

> 2026-09-12｜性质：**验证模型修正**（不改几何/不改判据阈值；只增冻结项）｜无 L1 变更
> 前置：CO-45 `7b8cb5b1294d8c71`，里程碑 tag `k2-v57-g7-l5-pass`（k2 `b5afe47`）
> 触发：撰写 W3 boundary v1.16（冻结文档同步）时对 `tools/p3_v57_w3_constructive_validator_v2.py` 冻结校验做交叉核对。

## 1. 现象（缺陷）
G5 独立验证器的 `frozen_sha_check` 仅钉 4 项：
`spec = SPEC_k2_v4.spec-rev-3.json`（引擎消费的 ECO spec）、`manifest`、`rules`、
**`pcb = k2_v4.kicad_pcb`（旧 6L，`f6273de613f43d05`）**。
⇒ 既**未覆盖宪法红线 SPEC 原件** `SPEC_k2_v4.json`（`0bd52ed48e720b8c`），
也**未覆盖 CO-03 版本 bump 后的 8L 冻结板** `k2_v4_8L.kicad_pcb`（`fb07d25ac426ff84`）——
后者是 L4 施工的真实源（`p3_v57_l4_apply_drawing.py` / `p3_v57_l4_validator.py` 的 `SRC_PCB`）。
后果：验证器宣称「frozen=True」，但其冻结集与实际冻结链不同源，可追溯性有缺口（宪法第五章/第七章）。

## 2. 修正（只增不减，判据强度只升不降）
`FROZEN` / `FROZEN_SHA_PREFIX` 扩为 6 项：

| 键 | 文件 | sha16 | 角色 |
|---|---|---|---|
| `spec` | `SPEC_k2_v4.spec-rev-3.json` | `2d6dbd8bd8d667d7` | 引擎消费的 ECO spec（CO-40 ECS-001） |
| `spec_orig` | `SPEC_k2_v4.json` | `0bd52ed48e720b8c` | **宪法红线 SPEC 原件**（新增） |
| `rules` | `_shared/eda_core/drc_rules.json` | `0a459839e15960b8` | 规则 |
| `manifest` | `m13_v57_s1_page_manifest.json` | `a8ef3ea8ecff99d7` | 页清单 |
| `pcb` | `k2_v4_8L.kicad_pcb` | `fb07d25ac426ff84` | **宪法红线 8L 冻结板（CO-03）**（新增） |
| `pcb_6l` | `k2_v4.kicad_pcb` | `f6273de613f43d05` | 8L 派生的上游历史件（保留原钉扎） |

## 3. 验证（实测）
`python3 tools/p3_v57_w3_constructive_validator_v2.py` ⇒
`verdict=PASS`，`G-M1..G-M6` 全 True，`A1.2/A1.3/A1.4` True，**`frozen=True`**；
`frozen_sha_check.actual` 逐项实测匹配上表 6 项（含 `pcb=fb07d25a…`、`spec_orig=0bd52ed4…`）。
指纹：validator `8f8ed665b645e8f7`｜`m13_v57_w3_validation.json` `23b2b6d161f9bea1`。

## 4. 未改物 / 红线
零几何改动：drawing 仍 `dfa1d7c4a811b0da`、板仍由此构造、G4/G6/G7 判定不变（本件不触碰引擎与 L4/L5）；
四冻结源原件未动；无阈值放宽；无搜索/迭代。

## 5. 备注（时点）
本件为 **tag 之后的验证模型强化**，不改写已发布段（TAG_POLICY 禁 amend/rebase）：
`b5afe47`（tag `k2-v57-g7-l5-pass`）在其 rev 上仍有效（其红线四源由独立 sha256sum 实测 4/4 MATCH）；
本件使 G5 的冻结证据与红线四源同源，供后续 rev 与复核直接引用。
