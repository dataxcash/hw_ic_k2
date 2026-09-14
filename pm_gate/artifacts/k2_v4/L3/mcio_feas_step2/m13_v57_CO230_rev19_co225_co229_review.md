# CO-230 — 非执行者对抗复评 **CO-225..CO-229**（+ 同会话处置）

复评者 = **非执行者**（context 归零之**新会话**；**未参与 CO-225..CO-229 之任何撰写** ⇒ 五节全在对象内，无自评豁免面）；as-found 逐件钉 `fdb72a2`；扰动一律内存注入、零落盘。
判决 = **PASS_WITH_FINDINGS**（findings 1，mid；负控 P1..P5 全触发；正控 V1..V7 全 True）。**未**改动冻结四源/板/SPEC。

## 1. as-found（逐件 sha16，`git show fdb72a2` 重放）

| 件 | as-found sha16 | 重放 |
|---|---|---|
| `tools/p3_v57_co164_order_runner.py` | `5dc43f6e3aedd50d` | MATCH |
| `pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_joint_assignment_boundary_v1_82.md` | `e5fe950356777eff` | MATCH |
| `pm_gate/artifacts/k2_v4/L2/input_defect_register_v1.json` | `ecf2963e9165f6f4` | MATCH |
| `tools/p3_v57_l5_signoff.py` | `7618070712518194` | MATCH |
| `tools/p3_v57_co120_provenance_pin_gate.py` | `28d6211f32318d9b` | MATCH |
| `tools/p3_v57_co195_fixpoint_uniqueness_oracle.py` | `c24f3e983c31e589` | MATCH |
| `k2_v4_8L.l4.kicad_pcb` | `d4e81f647be7f980` | MATCH |

## 2. 正控（本会话独立实测）

- 冻结四源 **4/4 MATCH**；`drc_rules` 副本同字节 = **True**；交付板 `d4e81f647be7f980` 逐字节未变 = **True**
- 实件路径：t36 域 `ok` / 语义 `ok`；t37 域 `ok`（命中 8 面，声明 8 面）
- t38 页等式 `ok`（34 vs 34 页）/ 词表 `ok`；t39 身份 pin `True` / 锚点 `ok`（16 键）
- `--check` **41/41 True**；序收敛 rc=0 / 2 轮；oracle PASS（11 齿 / rc=0 / 受控件复原）；co120 PASS（19 齿）；co124 PASS；L5 签署 FAB/DFM/SI PASS（skew 0.1300）；co206 7/7（A=FEASIBLE_PENDING_DFM 不变）

## 3. findings

### F-1（TOOL_DEFECT · 中 · CLOSED）**节集枚举域由被判对象自述 ⇒ 整节删除不被检出（空真）**

`boundary_sections_with_fp()` 之域 = boundary **文档自身**实存节集 ⇒ 整节删除后该节**同时**从域与现实中消失。实测：
删 §95 ⇒ 旧臂 `[]`（**PASS**）；删 §98..§102 ⇒ 仍 PASS；现声明集 100 节，
实测缺号 = [8, 9, 10]（无任何齿声明之）。承 **R-CO219-1**（枚举面须名集等式）/ **R-CO225-1**（判定面完整性须名集钉定）。
**处置**：`BOUNDARY_SECTIONS_DECLARED` + `boundary_section_set_decision()`（双向）扩 t35 臂①；**不新增齿**（仍 41）；runner report revision → **CO-203.8**。
**修后判别力**：同一注入 ⇒ 删 §95 `section_missing` / 删 §95..§102 `section_missing` / 增 §900 `section_undeclared`

## 4. 观测

- O-1（在册项复核，**非新发现**）：§98 之「标签 `CO-203.3` ↔ pin = 现行 `5dc43f6e3aedd50d`」属 boundary**现行态 pin 再对齐**之已在册形态（该行于 `e4a65f7` 时 = `2a99e5fb3d9b32a6`）；在册处置 = 判版本须读该节现行版本注或对应 CO 节，不得以同排历史标签为 sha 之版本判据。本件独立复现同现象。
- O-2（正控通过）：t36/t37/t38/t39 之**实件路径**（非仅合成控）在真数据上皆 `ok`，且实件数据 + 内存扰动皆按预期 fail-closed；t37 之载明面域经全树扫描 = 恰为声明 8 面（`.archer_tmp/` 等未跟踪工作区不在域内，属设计）⇒ CO-225 F-4 之域收窄已闭。
- O-3（诚实边界）：本件**不**复评 B 路 10L 实做与外部工艺/报价面（外部输入）；**不**判 boundary 节内叙述之完备性；CO-230 自身须下一轮复评（禁自评）。

## 5. 红线

**R-CO230-1**：凡以**文档/工件自述**为其**枚举域**之判定面，须另立 `*_DECLARED` 名集做**双向等式**（缺项 ⇒ `*_missing`；未声明之新增 ⇒ `*_undeclared`）—— 判据面之**域**不得由**被判对象自身**给出（承 R-CO219-1 / R-CO225-1）。
