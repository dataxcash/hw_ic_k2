# C-1 残面（2 维）落件提案 · v1

**背景**：`#K2-43 §二 C-1` 要求每判据维声明 `source_of_truth`（外部件；禁被验对象自身产物）。
批 4 已落 17 维（`02459f5`，含 `check-dimensions` 自证即拦）；**残面 = 下述 2 维**（ENG 无权改 `criteria/`）。

| 维 | 现行真源 | 问题 | 本提案 |
|---|---|---|---|
| `density_and_clearance` | 交付包内 `06_rulings/jlc_dfm_hdi_l7.json` | **包内自证**（负控已实测被拦） | `jlc_hdi_capability.yaml`（能力表外部件 `m13_v57_co146_jlc8_capability.json`）|
| `lib_electrical_level` | W-8 审计（**板派生**） | 与 C-1 相悖 | `parts_electrical_truth.yaml`（库侧快照 + 手册出处）|

**落件动作（gate 属主）**：① 置 `criteria/jlc_hdi_capability.yaml`；② 跑 `k2_p4_lib_snapshot_v1.py` 生成 `criteria/parts_electrical_truth.yaml` 并补 `datasheet_refs`；③ 在 `criteria/manifest.k2.yaml` 两维填 `source_of_truth` 指向上述两件；④ 跑 `check-dimensions` 正控（预期 19/19 已声明 · 违规 0 · PASS）与负控（真源指向被验对象 ⇒ 被拦）。

**ENG 侧只读声明**：本目录仅提案件，ENG **未**触碰 `criteria/`；不改变任何判据读数。
