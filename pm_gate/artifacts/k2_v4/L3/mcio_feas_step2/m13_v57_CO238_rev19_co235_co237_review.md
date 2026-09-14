# CO-238 — 非执行者对抗复评 **CO-235..CO-237**

复评者 = **非执行者**（context 归零之**新会话**；未参与该三节撰写 ⇒ 无自评豁免面）；as-found 逐件钉 `ab9c421`；只读。
判决 = **PASS_WITH_FINDINGS**（findings 1：F-1 mid；正控 V1..V6）。**未**改动冻结四源/板/SPEC。

## 1. as-found（逐件 sha16，`git show ab9c421` 重放）

| 件 | as-found sha16 | 重放 |
|---|---|---|
| `tools/p3_v57_co164_order_runner.py` | `2c0a68e6979ca102` | MATCH |
| `tools/p3_v57_co146_boundary_append.py` | `0d3ff8dcf676dff6` | MATCH |
| `pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_joint_assignment_boundary_v1_82.md` | `34fe365c4a575dd2` | MATCH |
| `pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json` | `4523da1913ac2e40` | MATCH |
| `tools/p3_v57_co230_rev19_co225_co229_review.py` | `35426723f58445a8` | MATCH |
| `tools/p3_v57_co235_rev19_co231_co234_review.py` | `a04b9eabf0590781` | MATCH |
| `pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_CO230_rev19_co225_co229_review.json` | `3b816ee2247eb7f1` | MATCH |
| `pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_CO235_rev19_co231_co234_review.json` | `d6de768766e927f1` | MATCH |
| `tools/p3_v57_co195_fixpoint_uniqueness_oracle.py` | `585b983de844603d` | MATCH |
| `tools/p3_v57_co120_provenance_pin_gate.py` | `28d6211f32318d9b` | MATCH |
| `tools/p3_v57_l5_signoff.py` | `7618070712518194` | MATCH |
| `tools/p3_v57_co206_process_route_select.py` | `83dba4f108663e6d` | MATCH |
| `k2_v4_8L.l4.kicad_pcb` | `d4e81f647be7f980` | MATCH |

## 2. 正控

- 冻结四源 **4/4**；`drc_rules` 副本同字节 = **True**；交付板 `d4e81f647be7f980` 未变 = **True**
- **V3 漏洞纯复算**（as-found）：子串判据对「真绑定→注释」= **True**（True ⇒ 静默通过）；「改名+注释」= **True** ⇒ 绑定臂可被散文满足
- **V4 修复判据（AST）判别力** = **True**；**V5 记录链派生键** 全清 = **True**；**V6 域−声明** = ∅（14 件 ≥ 下限 12 = True）

## 3. F-1（TOOL_DEFECT · mid · CLOSED）**t44 工具绑定臂 = 原文子串 ⇒ 注释/散文可替代真绑定**

**根因**：`_tool_ok[_rel] = (f'AF = "{_d["as_found"]}"' in _tsrc)` —— 原文子串测试；**注释提及同串即满足**。承 **R-CO202-4**（源内声明之代理判据须 AST 字面量，注释/散文不得满足）与 **CO-215**（同源缺陷：子串即可满足）之既定裁定。

**处置（L2 自裁）**：绑定判据改 **AST 赋值**（`AF` 之 `Assign`/`AnnAssign` 值须为 == rev 之字符串常量；注释/散文/拼接不满足；SyntaxError ⇒ fail-closed）+ 合成正/负控（6 项）；扩 t44 绑定臂（不新增齿，仍 46）；report revision → **CO-203.15**；**R-CO238-1**。

## 4. 观测

- O-1（as-found 诚实性）：CO-235..CO-237 之 canonical 件共 13 件，逐件 sha16 自 `git show ab9c421` 重放 **全 MATCH**；本会话未参与其撰写。
- O-2（CO-235 有效性）：其处置以「声明格式集 + 生成器 realign 同域 + t43 fail-closed」闭合该 F-1；本件 V1/V6 独立经手其产物，未见回归。
- O-3（CO-236 残余之界）：结构臂（as-found.rev 绑定 + 链派生键名集）与实况一致（V5：二记录 rev 合规、零链派生键）；其**工具绑定臂**为本件 F-1。
- O-4（CO-237 之域）：as-found pin 面之 `*_review.json` 受 pin 件 14 件；声明/豁免字面并集 14 件；域−声明 = ∅（V6）⇒ 名集等式成立。
- O-5（残余，未闭，界定）：① 域以**文件名形态**界定（异名逃逸）；② 键名启发式（更名逃逸）；③ 绑定判据认 `AF` 之**字符串常量**赋值（非字面量构造不视为绑定 ⇒ fail-closed）。

## 5. 红线

> R-CO238-1：**源内声明之代理判据须为 AST 绑定** —— 复评/重出件工具之 as-found 绑定（如 `AF = "<rev>"`）须以 **AST 赋值 + 字符串常量** 机判；**注释/散文/拼接一律不得满足**（承 R-CO202-4）；此形态须有机判齿（t44 绑定臂），承 R-CO225-1。
