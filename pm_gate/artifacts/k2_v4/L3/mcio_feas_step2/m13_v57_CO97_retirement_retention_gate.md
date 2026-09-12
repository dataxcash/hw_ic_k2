# CO-97（L2 自裁 · 可审计性）退役留存完整性闸 + 显式登记册 — 关闭 CO-96 F1 的「静默」面

> 日期 2026-09-12｜工具 `tools/p3_v57_co97_retirement_retention_gate.py` `64f8d17f427d597b`
> 登记册 `m13_v57_retirement_registry.json` `4b13b538ba8e28ce`｜记录 `m13_v57_co97_retirement_retention_gate.json` `9675c3de56cd9f49`
> 基线：SPEC rev-11 `d85f10f722ba22b0`｜板 `0e636a67c1472462`｜冻结源 4/4 MATCH｜**零 SPEC/几何/阈值改动**

## 1. 问题（CO-96 F1）
CO-96 机判：rev-10 以固定键集重建 `power_pad_connect` 时**静默丢弃** CO-89 的退役留存键
`retired_superseded_bom`（pre-rev-9 冻结 BOM 173/9 + 孤儿 55/2）；`p3_v57_co93_pdn_rev10_derive.py` 源码零引用、
CO-93 变更说明未登记。红线「退役几何/决策必须**显式留存**（不得静默放弃）」在**字面**上被违反（数据未丢失，可在冻结源 + CO-89 记录找回）。

## 2. L2 自裁（本件）
**选 CO-96 F1 给出的『或显式登记其移除』分支**，而非「为纯溯源字段单独触发一次 SPEC 重基线」：
- 该键与 `board_realized` 均**不被 `pdn_apply.py` 消费**（消费键 = `power_zones`/`decoupling_via_to_plane.vias`/`gnd_stitch_via.coordinates`/`power_pad_connect.entries`）⇒ 无几何/功能影响；
- 重基线会使**刚出具的 CO-96（rev-11）证书失效**并新增 CO-97 复评债，而与几何/功能无涉 ⇒ **不成比例**；
- 故：① 机判化「不得静默退役」为**可重复闸**（本件）；② 以**显式登记册**登记该移除 + 找回指针（消除「静默」）；
  ③ 其「SPEC 内留存（回填）」列为**可选后续**，随下一次构建期 SPEC bump 一并处理（不单独重基线）。

## 3. 闸判据（机判，无几何）
- **A** 逐版枚举退役留存块（路径首段 = 首个含 `retired` 的段；剥离 list 下标）；
- **B** 逐相邻版本求 **drop = prev − cur**；
- **C** 每个 drop 必须在登记册有匹配项（键 + `from_rev→to_rev` + reason + recovery）；
- **D** 登记册不得有**无对应 drop 的陈旧项**；
- **E**（advisory）退役块为空仅记录、不判 FAIL（如 MCU_VDD 只退役 segments 不退役 polygons `[]` 属合法）。

## 4. 结果（rev-1..rev-11 + 冻结）
- 退役留存块：rev-8 起 5 → rev-9 **8** → rev-10 **13** → rev-11 **15**（逐版明细见记录 `retention_blocks_per_rev`）。
- **drop 恰 1 处**：`/pd/zone_defs/power_pad_connect/retired_superseded_bom`（rev-9 → rev-10）⇒ **已登记**（reason + 3 条找回指针，全部可解析）。
- **verdict = PASS**（undeclared 0 / stale 0 / recovery_bad 0），**牙齿 3/3**：未登记 drop 必被抓、已登记 drop 必放行、陈旧登记项必被抓（均合成注入、自洽）。

## 5. 附带（登记册同时消除 CO-96 F5 的歧义）
`power_pad_connect.board_realized` 仍记 CO-89 的 223/86（非 rev-11 决策 189/120）系**来源溯源字段**、未被 `pdn_apply` 消费；
登记册 + 本卡显式记为「CO-89 派生记录，非现行决策」，消除「223 已实落」的误读。其同步列入可选后续。

## 6. 非声明 / 处置归口
- **零 SPEC/板/阈值/冻结源/引擎改动**；不重跑链路（无 SPEC 变更）；只读机判 + 声明册。
- **仍未闭合（登记待办，非 PASS）**：**F2/F4**（可达性要求的几何闭合 35/55 与 scope 扩展）属 **L3 施工期**派生 + 闸扩展；
  **F6**（co95 `in_poly` 用 bbox 非真 PIP）属 latent，随构建期 tooling 一并修。
- **`_shared` 引擎处置（L2 自裁）**：**不解冻冻结副本**；施工侧三项（`gnd_stitch_gen` 障碍集改交付板实际铜 /
  `pdn_apply` 短段宽度读 SPEC / blocked schema 对齐）**改由项目内引擎承载**，且**仅在 PDN 施工期激活**（当前交付板逐字节不变、PDN 未施工 ⇒ 非在役缺口）。
- **L1（停并升级）**：**F3 的根因 = 区域归属**（`12V_IN` 无 In4 区需裁承载；`P3V3_AUX` 西侧 3 pad 与西区名义网 MCU_VDD 冲突需裁归属）⇒ 属 L1，需 owner。
