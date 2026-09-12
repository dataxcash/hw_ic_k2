# CO-150 卡 · K9 热/压降域闸硬化

- co124 revision = **CO-124.5**｜verdict = PASS｜findings = 0
- 新增域：`thermal_option_domain`（∃ 声明散热方案覆盖最重工况；现状不达标须显式声明缓解）、`drop_domain`（每轨 ΔV% ≤ 预算%）
- 负控：{'T10_thermal_option_domain_teeth': True, 'T10b_thermal_domain_no_false_positive': True, 'T11_drop_domain_teeth': True, 'T11b_drop_domain_no_false_positive': True}
- 登记项 `tool_defect:co124_k9_has_no_thermal_or_drop_domain_model` → **CLOSED**；登记簿 OPEN 余 0
