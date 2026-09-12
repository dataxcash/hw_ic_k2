# CO-102（L2 自裁 · 项目内引擎承载）修正版 PDN 施加器 —— 施工侧缺陷闭合（冻结 `_shared` 不解冻）

> 日期 2026-09-12｜工具 `tools/p3_v57_co102_pdn_apply_local.py` `17783c4141fa982a`
> 记录 `m13_v57_co102_pdn_local_apply.json` `865b7336966e1186`
> 基线：SPEC rev-12 `1a381b06454dbe2c`｜板 `0e636a67c1472462`（**交付板逐字节不变**；验证用 scratch）

## 1. 问题（CO-99 根因②③）
冻结 `_shared/eda_core/pdn_apply.py`（容器副本只读）三处施工侧缺陷：
① `add_track(..., width=0.5)` **字面量**，不读 SPEC `stub_width_mm`（rev-12 = 0.2）；
② via **不去重**（同网同址重复落孔）；
③ blocked 口径与生成器不一致。
⇒ rev-12 的 dry-run（冻结引擎）仍 **+34**。

## 2. L2 自裁（既定：`_shared` **不解冻**，施工侧**改由项目内引擎承载**）
新增**项目内**施加器 `p3_v57_co102_pdn_apply_local.py`：坐标**逐字取自 SPEC**（零搜索、零自由度），仅修正上述三处：
- **短段宽** = `pd.zone_defs.power_pad_connect.stub_width_mm`（rev-12 → **0.2**）；
- **via 去重**（键 = `(net, x, y)`，同址同网只落一次）；
- **blocked 口径** = 与 SPEC 一致（`blocked`/`status=="blocked"` 跳过）。

## 3. 验证（scratch 三态 DRC，确定性）
| 态 | kicad-cli DRC violations | Δ vs baseline |
|---|---|---|
| baseline（未施工） | **42** | — |
| **冻结引擎** `pdn_apply` | **76** | **+34** |
| **项目内引擎**（本件） | **42** | **+0** |

施加统计（项目内）：zones 5 / vias **241** / tracks **185** / stub_w **0.2** / deduped **0** / 跳 blocked **61**。
⇒ **rev-12 PDN 在项目内引擎下施工 DRC-clean（+0）**；CO-99 的 dry-run 残差（+34）**全部来自冻结引擎**，已由本件闭合（项目内路径）。

## 4. 非声明 / 归口
- **不改冻结 `_shared` 副本**（未 chmod/未写）；不改 SPEC/板/阈值/冻结源；零坐标搜索（坐标全来自 SPEC）。
- 本件提供**施工期**使用的施加器（CLI 同冻结件：`--spec --board --stage`）；`--verify` 为 scratch 对比。
- `gnd_stitch_gen` 的**生成端**缺陷（障碍集取 `layer_plan` 而非交付板实际铜、`ok:False` schema）**不在本件范围**：施工期只用 SPEC 的 `gnd_stitch_via.coordinates`（rev-12 已重导），故该生成端不在在役路径；如未来重生成须同批修（登记为后续）。
- 复核：`candidate`/`blocked` 数的变化属 rev-12 计划（见 CO-101）；本件只改**施加口径**，不改计划。
