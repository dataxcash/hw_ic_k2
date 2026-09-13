# CO-181 — 非执行者对抗复评（CO-166..CO-180）｜as-found @ `6bf482d`

- verdict：**PASS_WITH_FINDINGS**｜findings：5｜独立正控 10 项（全 True=True）｜负控 8 项（全翻转=True）

| id | sev | kind | what（摘要） |
|---|---|---|---|
| co181:F-1 | medium | TOOL_DEFECT | CO-180 G-1 已将各步声明齿纳入判决，但被纳入的牙齿存在**非判别齿**：`co146_pm_eval` t01 代数恒真（(2IR)/(IR)≡2）、t02 字面 `True`、t03 `bool(非空 dict)` 近恒真 ⇒ 5 齿中 3 齿永不翻转；`co98` `integrity... |
| co181:F-2 | medium | TOOL_DEFECT | `step_declared_teeth` 对**不可解析**的声明 json 静默 `continue` ⇒ 返回 None（不判），违反 R-CO180-1「不可判一律 fail-closed」（白名单路径已 fail-closed，非白名单未）。... |
| co181:F-3 | low | TOOL_DEFECT | `step_declared_teeth` 判据**自指**：仅要求「现有齿全 True」，无齿集/齿数下界 ⇒ **静默删齿**（缩减自检）不被判。对照 co150/co136 对特定键集点名的做法。... |
| co181:F-4 | low | TOOL_DEFECT | 规范序步 `co81`/`co84` 自检以 `teeth_ok`（bool）+ 控制项暴露，**无 `teeth` 布尔齿 dict** ⇒ 不参与 R-CO180-1 判决（仅 rc 覆盖）。CO-180 G-3 只扫了 co78，漏同族两件。... |
| co181:F-5 | low | TOOL_DEFECT | **固有一轮 pin 滞后（既有 co180:G-4）**：R-CO180-3 仍为「循环至 sha 稳定」而非「任意态单次收敛」；复评方实测本次（未变更态）2 轮收敛且 182 件逐字节幂等 ⇒ 滞后仅在 upstream 记录变更后首轮出现。... |

独立确认（正控）：

- V0_frozen_four_sources_4of4：4/4 MATCH（含 drc_rules）+ 工作树与 as-found commit 逐字节一致
- V1_register_98_open0_counts_rederived：items=98 OPEN=0 counts 复算一致；register_consistency==[]
- V2_tool_pins_match_boundary：6/6 MATCH；不符={}
- V3_order_matches_boundary：boundary 序 49 步 == ORDER 49 步
- V4_step_declared_teeth_census：as-found 含声明齿步 17/49（CO-180 G-1 覆盖）；以 teeth_ok 暴露但无 teeth 者=['co81_project_rules_gate', 'co84_dru_domain_gate']（F-4 证据）
- V5_co106_judgment_completeness：verdict 阶梯 fail-closed；teeth 9 全 bool；C/D judging=False 已排除折算
- V6_co78_teeth_bool_dict：teeth={'control_historical_detected': True}；散文已移 teeth_note
- V7_canonical_order_converged：**as-found 复跑（复评方实测，captured）**：converged / iters=2 / sha=6fb50b4038f7bb25；逐 step did_work 全 True / stray 全空（现行报告结构：converged=True，iters=2）
- V8_fab_dfm_teeth_counts：fab 29 齿全 True；DFM 8 齿全 True / verdict FAIL（预期）
- V9_repro_idempotent_no_drift：181 受控件（tracked）复跑后与 as-found commit 逐字节一致（0 漂移）

负控（内存注入）：

- P1_step_declared_teeth_matrix：全 True→True；含 False→False；散文→False；空→False；无 teeth→None（不适用）
- P2_silent_tooth_deletion_undetected：只留 1 齿仍判 True ⇒ 缺齿不被判（判据自指：由记录自定齿集）
- P3_unparsable_declared_json_fails_open：不可解析 ⇒ None（不判）；R-CO180-1 要求「不可判一律 fail-closed」
- P4_teeth_ok_only_not_judged：自检以 teeth_ok 暴露（无 teeth 布尔齿 dict）⇒ 不参与 R-CO180-1 判决
- P5_co98_integrity_tooth_tautology：intact/injected/missing/clsdrift 四态恒 True ⇒ 注入 +1 检测未真正实现
- P6_pm_eval_teeth_non_judging：t01 代数恒真；t02 字面 True；t03 bool(非空 dict) 近恒真 ⇒ 5 齿中 3 齿永不翻转
- P7_whitelist_teeth_failclosed：白名单齿不可判/False ⇒ 停机；True ⇒ 放行（预期 FAIL）
- P8_register_drift_detected：counts 漂移 / status 越词汇 ⇒ register_consistency 必报（R-CO168 有效）
