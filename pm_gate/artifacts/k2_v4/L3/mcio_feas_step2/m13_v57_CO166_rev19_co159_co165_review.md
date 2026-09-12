# CO-166 — 非执行者对抗复评（CO-159..CO-165）｜as-found @ `e427909`

- verdict：**PASS_WITH_FINDINGS**｜findings：6
- 受评基线：k2 `e427909`（CO-165）｜SPEC `5f72182a2616392c`｜板 `d4e81f647be7f980`

| id | sev | kind | what（摘要） |
|---|---|---|---|
| F-1 | medium | gate-fail-open | `boundary_order_steps()` 以 `lines[-1]` 取「最后一条**含字面子串** `规范复现序 =` 的行」解析序。若更新的 R-COxxx-3 行改用别样措辞（如 `规范复现序（步骤集不变）... |
| F-2 | low | gate-fail-open | 白名单「记录由本次执行产出」用**绝对时间**判据 `st_mtime >= t0-1.0`。若盘上记录 mtime 因时钟回拨/网络盘/异机写入而落在**未来**，则**崩溃（未重写记录）**的白名单步仍被判 `exp... |
| F-3 | low | gate-blindspot | R-CO165-2 只声明「新增产物须落入 `watch_paths()`」，但**无任何牙齿**断言 `EXPECTED_NONZERO[*].record ⊆ watch_paths()`。当前 DFM 记录恰在 `... |
| F-4 | low | gate-false-accept | `binding_param_checks` 用**无锚子串**命中：备注写 `185Ω`/`11.6 mm` 亦分别命中 `85Ω`/`1.6 mm`；且 `tolerance` 记号 `±10%` 可被**厚度公差*... |
| F-5 | low | gate-false-reject | 同一函数对备注**措辞**敏感：`1.6mm`（无空格）/`外层1oz`/`85 Ω` 即令 t09 失败——虽然备注语义正确。属 fail-closed（偏安全），但把「备注排版」与「定值漂移」混为一类，产生噪声失败。... |
| F-6 | low | gate-governance | `EXPECTED_NONZERO` 是收敛判定的**单点信任**：t03/t07 只断言「步骤在序内」+「条目含 verdict/record」，既**不禁止**把 expected `verdict` 写成 `PAS... |

独立确认（非空过证据）：

- 冻结四源 4/4 MATCH（含 drc_rules 0a459839e15960b8）；交付板 = d4e81f647be7f980
- as-found 记录逐条复核成立：co159 PASS_WITH_FINDINGS/12；co124 CO-124.9 PASS/37 牙齿/0 findings；co150 CO-150.2 牙齿 5/5；co106 CO-106.4 PASS/8 牙齿；co120 PASS（12-12）；co77 PASS；co135 CO-135.3；co136 PASS；打样包 CO146-PKG.4 n_files 34/13 牙齿；登记簿 65 项 / OPEN 0（co159:F-1..F-12 全 CLOSED）
- CO-161 单一真值成立：co124 `required_dv_ids`(9) == co153 `KIND_EXPECT` 键集（V2）
- CO-163 t10 正控成立：容器侧监理指令件可达且 sha16 `35aafe268ff52f89` 与声明一致（V4）
- CO-163 t09 正控成立：现行备注 7/7 记号命中（V5）
- CO-162 阶梯独立复核：pin 漂移 ⇒ BASELINE_MISMATCH、teeth 失败 ⇒ FAIL(teeth)、check 失败 ⇒ 非 PASS（V6）
- CO-164 边界文档序 ↔ 执行器 ORDER 一致（34 步）；CO-165 受控集覆盖 ≥20 件且含 co106 记录与打样包 MANIFEST（独立重算）
- co146_boundary_append as-found 源码只读重放**执行成功（rc=0）且仅写 boundary**（V3）⇒ §37..§39 大段 f-string 现行可正确求值（逐字节幂等由 runner sha 跨轮稳定另行保证）
- CO-163 t10 在本容器 `.omo` **不可达**时 fail-closed（P2 注入不存在路径 ⇒ 判据 False，不静默放行）
