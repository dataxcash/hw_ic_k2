# RETIRED · 遗留分配锚（channel_alloc_v2）

> [批2·S4 血缘标注 · ARCHER 2026-09-20 · 零行为改动]（#K2-41 §三-①：N-05 卫生）

- **状态：RETIRED（退役）** —— 不得再作为任何测试/判据/工具的运行锚。
- 由来：2026-08-28 字节导入；**自导入起从未重生成**；现役链（`SolvePipeline.run_alloc`）不读本件。
- 陈旧面：走廊 id 旧代（`J2_TO_U` / `U_TO_MCIO`，108 处）、band 名旧代（`lower`/`upper`）、
  track 值三代错位 ⇒ 作为锚时 `_track_y_for` 解析为 None，制造 NO_CORRIDOR/INFEASIBLE 假象。
- 替代锚：现行 pipeline alloc 具名冻结载体
  `k2/pm_gate/artifacts/k2_v4/L3/model_solves/pipeline_alloc_current_v1/alloc.json`（血缘见同目录 LINEAGE.json）。
- 保留理由：历史取证可读；**只读留存**，禁参与判定。
