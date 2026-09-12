# CO-81（L2 可审计性 · 回归闸）— 受控工程文件设计规则 = 红线规则源

> 日期 2026-09-12｜工具 `tools/p3_v57_co81_project_rules_gate.py`｜记录 `m13_v57_co81_project_rules_gate.json` `1f25c6a9db6923f0`｜boundary **v1.46**

## 1. 判据（把 CO-80 的 F-80-1 固化为闸）

`kicad-cli` 对 `<board>.kicad_pcb` 做 DRC 时会**自动选取**同名 `<board>.kicad_pro`。
若该受控文件的规则与意图不符，**最自然的独立核查命令**会大面积误报（F-80-1 实测 880 条），
审计者据此误判板子不合格。故立闸：

> 每个**受版本控制**的 `*.kicad_pro` 的 DRC 设计规则，必须等于**红线规则源**
> `_shared/eda_core/drc_rules.json`（`manufacturing` + `hole_clearance:min`）；
> 且 `rule_severities` 必须等于 JLC 模板 `tools/k2_jlc_template.kicad_pro`。

键映射：`min_via_annular_width` ↔ `manufacturing.min_annular_width`；其余同名；
另含 `min_hole_clearance` ↔ `hole_clearance.min`（共 7 项）。

## 2. 结果（PASS，5/5 受控工程文件）

| 工程文件 | 判定 |
|---|---|
| `k2_v4.kicad_pro` | PASS |
| `k2_v4.l4.kicad_pro` | PASS |
| `k2_v4_8L.kicad_pro`（意图/现行） | PASS |
| `k2_v4_8L.l4.kicad_pro`（CO-80 修复后） | PASS |
| `tools/k2_jlc_template.kicad_pro`（模板 = 规则载体） | PASS |

期望值（= 红线规则源）：`min_track_width 0.09` / `via 0.35` / `annular 0.075` / `through-hole 0.2` /
`copper-edge 0.3` / `clearance 0.1` / `hole 0.25`。

## 3. 牙齿（可执行负控）

| 控制 | 输入 | 期望/实测 |
|---|---|---|
| 负控 | `min_track_width=0.2` | 抓 1 项失配（`(0.2, 0.09)`） |
| 正控 | 期望值原样 | 0 失配 |
| **历史对照 F-80-1** | CO-80 修复前的实测原值（0.2 / 0.5 / 0.1 / 0.3 / 0.5 / 0.0 + hole 0.25） | **抓 6 项失配**（`min_hole_clearance` 原本即一致） |

⇒ 闸对**真实发生过的缺陷状态**可复现报警，非事后构造。

## 4. 性质与限制

- 只读判据；不改任何工件；阈值全部取自**红线规则源**，不放宽。
- 闸为**工程文件/声明层**检查，不替代 G4..G7 几何门；建议与 G5 同批运行。
- ① 对间净空仍为 **L1**；非执行者 pass 2/2、板厂券仍欠（外部）。
