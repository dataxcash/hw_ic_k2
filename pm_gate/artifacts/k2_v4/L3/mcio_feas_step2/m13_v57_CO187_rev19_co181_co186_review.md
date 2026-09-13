# CO-187 — 非执行者对抗复评（CO-181..CO-186）｜as-found @ `4c581c7`

- verdict：**PASS_WITH_FINDINGS**｜findings：3
- 方法：正控 V1..V6（独立复算）+ 负控 P1..P6（内存注入、零落盘）

| 控 | 结论 |
|---|---|
| V1_CO181_teeth_pinned_and_fail_closed | True |
| V2_CO182_scan_follows_refresh_and_realign | True |
| V3_CO183_ratchet_zero_violation_and_count_floor | True |
| V4_CO184_anchor_unique_and_windowed | True |
| V5_CO185_nonpass_declared_and_rc_binds_verdict | True |
| V6_CO186_md_products_controlled | True |
| P1_ratchet_catches_evasions_current | True |
| P1_as_found_misses_aliased_and_ctor_forms | True |
| P2_md_scan_current_forms | True |
| P2_as_found_misses_md_forms | True |
| P3_boundary_read_scan | True |
| P4_nonpass_undeclared_caught | True |
| P5_anchor_context_controls | True |
| P6_as_found_undercounts_co81 | True |
| P6_current_counts_co81 | True |

## Findings（as-found）

| id | sev | 对象 | what |
|---|---|---|---|
| F-1 | low | CO-183 | `teeth_hygiene_scan()` 容器形态覆盖不完备：别名容器下标（`tooth[k]=…`，实测 co81 5 齿仅计 2）、`AnnAssign` / `dict(...)` / `.update({...})` / `.setdefault(k,v)` / 字面恒真式（`1==1`）一律漏计 ⇒ 以这些形态加入常量齿不被 t18 截。 |
| F-2 | low | CO-186 | `md_write_scan()` 仅认 `write_text` ⇒ `open(...,'w')` / `shutil.copy*` 目的 `.md` 产物不在 pin、t20 亦不截 ⇒ 此类 md 产物可落出受控集（R-CO186-1 静默违反）。 |
| F-3 | low | CO-182 | `BOUNDARY_SCAN_GUARDED` 为**手工枚举**，无「boundary 读取者全集」机判 ⇒ 新增读取/扫描步可静默绕开 t17。 |

## 处置（CO-187，L2 自裁）

CO-187（L2 自裁）：runner 升 CO-187.1 —— `teeth_hygiene_scan` 容器形态全覆盖 + t18 逐工具齿数下限；`md_write_scan` 覆盖 open-w/copy-dst + `ORDER_MD_PRODUCT_EXEMPT` 显式豁免 + t20 加固；`BOUNDARY_READ_DECLARED` + t21（boundary 读取者全集机判）。findings 均 CLOSED。
