# K2 · R341 · 交付包之 **1 ACCEPT 项具名**（= 阻焊桥）+ 修法之**铜层中性证明**（只读）

**件**：`K2_R341_DFM_ACCEPT_ITEM_NAMED_AND_MASK_FIX_COPPER_NEUTRALITY_v1.json`（约定A `388df269275e8eb4`）

## 具名
| 项 | 值 |
|---|---|
| ACCEPT 项 | **阻焊桥 / 阻焊-铜净距**（`solder_mask_bridge`） |
| 实测 | JLC 限 DRC **9** 处 <0.09mm（4∈[0.05,0.06)·1∈[0.06,0.07)·4∈[0.08,0.09)） |
| 包内判 | `machine_std=FAIL` · `hdi=ACCEPT_L2_WITH_FAB_REVIEW`（`06_rulings/jlc_dfm_hdi_l8.json`） |
| 包内说明 | JLC 0.10mm 系**最小可保证桥宽**（非必须存在桥）⇒ 板厂按『无阻焊坝』印制；承 CO-147 R3 先例 |

## 修法 + 中性证明（本件实测）
`(pad_to_mask_clearance 0.05)` → `0.02` ⇒ 阻焊桥 **9→0**（既有 `mask_accept_fix_proof.json`）。
本件进一步在 `/tmp` **重出 Gerber**（l8 原板 vs 0.02 变体 · 同法归一化日期后逐字节比对）：

| 层组 | 结论 |
|---|---|
| **铜层** F.Cu/In1..In6/B.Cu | **逐字节相同**（零铜变化） |
| 丝印 F/B.Silkscreen · 边框 Edge.Cuts | **逐字节相同** |
| **阻焊** F.Mask/B.Mask | **唯一变化**（F_Mask 15813→15213 行 · B_Mask 1301→789 行） |

⇒ 该修法 **铜/丝印/边框中性**，只改阻焊 Gerber（正是要修的对象）。
**旁证**：本次重跑之 Gerber **13/13 层与已交付包逐字节一致** ⇒ 交付包可复现。

## 待监理口径（属监理自裁面）
owner #14③『DFM 逐项全 PASS』与包内『1 ACCEPT』之差：
- **(i) 认等效** ⇒ 现状 P5 冻结交付（成本 0）；
- **(ii) 重出 rev（0.02）** ⇒ DFM 17/17 全 PASS，但板 sha16 变更 ⇒ 须重跑 P4（预期仍 19/19，须含 R340 之 (B')）并重建包。

ENG **不自行改板**（未获批 · rev 级决策）。

## 边界
只读 · 实验副本在 `/tmp` · **仓库板件/包件未动** · 未改 `criteria/`/生成器/SPEC/原理图 · 未派 WORKER · 未写 `.omo/supervision/**`。冻结四源 4/4 未动。

---
—— ENG（ARCHER）· 2026-09-22 · owner 闸口 **0**
