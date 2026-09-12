# CO-159 — 非执行者对抗复评（CO-156 + CO-157 + CO-158）｜as-found @ `c4e951c`

- verdict：**PASS_WITH_FINDINGS**｜findings：12
- 受评基线：k2 `c4e951c`（CO-158）｜SPEC `5f72182a2616392c`｜板 `d4e81f647be7f980`

| id | sev | kind | what（摘要） |
|---|---|---|---|
| F-1 | medium | gate-weakness | CO-156（F-6）的 `declared` 值-证据绑定可被**省略值**绕过：`_contains(evidence[key_path], dv.computed)` 在 `computed` ... |
| F-10 | low | drift-risk | CO-158（J-2）把 L5 包补进了 **co77 与 co135 各自维护**的 citation 候选表：两份表已现分歧面（co77 含 container-parent `_shared` ... |
| F-11 | medium | rule-unenforced | handoff §6「复现命令」块内的回归闸 co106_reference_plane_gate/co78_layer_role_drift_gate/co81_project_rules_gate... |
| F-12 | low | record-hygiene | CO-135 复评件虽是规范序内**现行**闸，却内嵌 CO-134 时点**硬编码链 pin**（如 `G4 0074dad9067af737 / G5 75ce1c2af42de55e`，现行为 ... |
| F-2 | medium | gate-weakness | CO-156（F-7）的权威交叉校验**仅在权威 DV 存在时生效**：`auth_edge`/`auth_span` 从台账现取，缺失（如 upsert 误删、手工编辑）时两处 `isinstanc... |
| F-3 | medium | gate-coverage | CO-157（H-1）的元牙齿 T18 只断言「**合成电池触发集 == K9_FINDER_IDS**」，不比对**源码**可产出的 finder 集：在 k9_findings 里新增一个**电池... |
| F-4 | medium | rule-vs-machine | CO-157（H-4）的 `H4_ledger_upsert_only` 只拦「写台账但未先读台账」；**读后整表重写**（正是 R-CO156-3 条文所禁、F-4 的原始失败模式）仍判无违规。规则... |
| F-5 | low | gate-coverage | CO-156（F-2b）的下游快照键判据依赖**嵌套容器**（path 段 ∈ {register,ledger}）：顶层或其它容器下的 `register_sha16`/`open_total`/`... |
| F-6 | low | gate-weakness | CO-157（H-3）把 `board_superseded` 收严为「16-hex 且 ≠ 交付板」，仍是**格式判**：任意 16-hex（`0000…`、`deadbeef…`）即成立豁免，未与... |
| F-7 | medium | rule-unenforced | **R-CO158-3（CO-158 J-3 自定）对规范序内的 `co146_jlc_dfm_gate` 不成立**：其 verdict 允许 FAIL（当前即 FAIL 两项 DFM 阻塞），但 ... |
| F-8 | low | gate-coverage | CO-158（J-1）新增 `06_rulings/` 后，牙齿 t05 只验**存在**、t06 只验包内可解析：若 L2 裁定件/DFM 记录在打包后修订，包内副本陈旧**无任何牙齿**（J-1 ... |
| F-9 | low | gate-coverage | ORDER_NOTES 的**目录级声明**（`01_`..`06_`，如「叠层图(03_) + 阻抗表(04_)」）不在 t06 覆盖内（t06 只解析 `06_rulings/*` 文件引用）；当... |

独立确认（非空过证据）：

- 冻结四源 4/4 MATCH（含 drc_rules 0a459839e15960b8）；交付板 = d4e81f647be7f980
- as-found 记录逐条复核成立：co124 CO-124.7 PASS/29 牙齿/0 findings；co120 CO-120.4 PASS（teeth 9-9）；co77 CO-77.6 PASS（mismatches []）；co135 CO-135.2 citation clean；co136 CO-136.1 PASS；MANIFEST CO146-PKG.2 n_files 34/teeth 6-6；登记簿 44 项 OPEN 0；台账 9 DV / 七域
- CO-158 的「gerber/drill 逐字节未变」经 CO-157→CO-158 MANIFEST 差分独立复核：25 件 gerber/drill 全同、新增 4 件 06_rulings、n_files 30→34、仅 04_impedance 副本与 ORDER_NOTES 变（与声明一致）
- co134 upsert 收窄成立（源码读台账后按 id 合并、非字面整表重写）；co77/co135 现行 boundary 引用解析一致（divergent=0）
