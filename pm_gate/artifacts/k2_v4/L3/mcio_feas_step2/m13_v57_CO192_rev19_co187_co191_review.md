# CO-192 — 非执行者对抗复评（CO-187..CO-191）｜as-found @ `52235b5`

- verdict：**PASS_WITH_FINDINGS**｜findings：4
- 方法：正控 V1..V8（独立复算）+ 负控 P1..P6c（内存注入、零落盘）

| 控 | 结论 |
|---|---|
| V1_CO187_teeth_ratchet_live_clean_and_floor | True |
| V2_CO187_md_products_controlled_and_exempt_bound | True |
| V3_CO187_boundary_readers_enumerated | True |
| V4_CO188_stray_write_fail_closed | True |
| V5_CO189_write_shadow_visible | True |
| V6_CO190_step_timeout_fail_closed | True |
| V7_CO191_judgment_basis_declared | True |
| V8_frozen_4of4_and_order_matches_and_check_green | True |
| P1_as_found_teeth_miss_new_forms | True |
| P2_current_teeth_catch_new_forms | True |
| P3_as_found_md_miss_new_forms | True |
| P4_current_md_catch_new_forms | True |
| P5_as_found_boundary_read_miss | True |
| P5b_current_boundary_read_catch | True |
| P6_as_found_expected_nonzero_leaks_undeclared_verdict | True |
| P6b_current_gate_catches_on_release_classes | True |
| P6c_current_scanners_specific | True |

## Findings（as-found）

| id | sev | 对象 | what |
|---|---|---|---|
| F-1 | low | CO-187 | 牙齿卫生棘轮容器形态仍漏计：`|=`（AugAssign）/ 嵌套下标 `rec["teeth"][k]` / dict 推导 `{k: True for k in …}` / `__setitem__` / Attribute 目标 `self.teeth[k]` / 下标赋别名 `rec["teeth"]=<Name>` 一律 n_teeth=0（既不计数亦不报 constant）⇒ 恒真齿可经这些形态加入而不被 t18 截；R-CO187-1「**全部**容器形态」为过强声明。 |
| F-2 | low | CO-187 | md 写/拷形态仍漏计：`Path.open(w)` / `shutil.move` / `os.replace|rename` 目的一律 `md_write_scan()`==[] ⇒ 此类 `.md` 产物既不在 pin、t20 亦不截（可落出受控集）；R-CO187-2「**全部**写/拷形态」为过强声明。实测现行 ORDER 工具 0 命中（潜在面）。 |
| F-3 | low | CO-187 | boundary 读取者判据仍可绕过：`D.open().read()` / `io.open(B).read()` 形态（源内无 `read_text`/`read_bytes` 字面）判 False ⇒ t21 读取者全集可被此形态静默绕过。 |
| F-4 | low | CO-191 | 「**全部**声明 verdict 一律判决」对白名单步不生效：主循环以 `if cls == "ok"` 为门槛 ⇒ `expected_nonzero` 步（co146_jlc_dfm_gate）的**副**声明产物 verdict 不被运行期判决；副值为其声明 FAIL 之外的非 PASS 值（如 ERROR）即静默逃逸，违 R-CO191-1。 |

## 处置（CO-192，L2 自裁）

CO-192（L2 自裁）：runner 升 **CO-192.1** —— ① `teeth_hygiene_scan` 形态覆盖续加固（`|=`/嵌套下标/推导/`__setitem__`/Attribute/下标赋别名）；② `md_write_scan` 补 `Path.open(w)`/`shutil.move`/`os.replace|rename`；③ `boundary_read_scan` 补 `.open().read()`/`io.open`；④ 新增 `all_verdicts_gate`：**放行档**（`ok` **与** `expected_nonzero`）一律判**全**声明 verdict ⇒ 白名单步副 verdict 不得逃逸；t18/t20/t21/t25 合成控同步扩展。findings 均 CLOSED。
