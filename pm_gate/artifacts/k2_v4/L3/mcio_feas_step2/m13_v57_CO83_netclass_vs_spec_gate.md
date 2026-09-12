# CO-83（L2 可审计性 · 回归闸）— 工程网类 vs 红线 SPEC net_classes 交叉校验

> 日期 2026-09-12｜工具 `tools/p3_v57_co81_project_rules_gate.py`（CO-83 扩展）｜闸记录 `ebd163058efaad14`｜boundary **v1.48**

## 1. 动机（补最后一个覆盖方向）

CO-81/CO-82 的工程文件闸有两个方向：**规则 ↔ 红线规则源**、**工程 ↔ 意图工程**。
但**网类值的权威源是红线条文**（`SPEC net_classes`），此前**未**与工程文件交叉校验 ——
若工程网类与 SPEC 分歧（例如 clearance / diff_pair gap 被改），闸会因「工程之间一致」而放行。

## 2. 判据与映射

工程网类（DRC 相关字段）必须等于红线 SPEC `SPEC_k2_v4.spec-rev-8.json` `net_classes`：

| 工程类 | 工程字段 | SPEC 路径 |
|---|---|---|
| `LOW_SPEED` | `clearance` / `track_width` | `clearance` / `width` |
| `PCIe85` | `clearance` / `track_width` / `diff_pair_gap` / `diff_pair_width` | `clearance` / `width` / `diff_pair.p_gap` / `diff_pair.p_width` |
| `POWER` | `clearance` / `track_width` | `clearance` / `width` |

## 3. 结果（PASS）

- 意图工程 `k2_v4_8L.kicad_pro` vs SPEC：**0 失配**。
  - `LOW_SPEED` clearance 0.1 / width 0.15；`PCIe85` clearance 0.175 / width 0.205 / `p_gap` 0.175 / `p_width` 0.205；`POWER` clearance 0.2 / width 0.5。
- 5/5 受控工程文件 PASS（模板豁免网类检查，理由已记录）。
- **疑似分歧已排除**：工程网类 `PCIe85.track_width = 0.205`（标量）vs SPEC 内层交付 `0.16` —— SPEC 已**显式声明**这是设计意图
  （`diff_pair.p_width_scope`：netclass 标量保留外层次口径，内层交付线宽 = `p_width_mm_by_layer`，CO-68 对称叠层 85Ω 闭合），非缺陷。

## 4. 牙齿（可执行负控）

| 控制 | 输入 | 实测 |
|---|---|---|
| SPEC 侧负控 | 篡改 SPEC `PCIe85.clearance` 0.175 → 0.2 | 抓 `PCIe85.clearance: [0.175, 0.2]` |
| 规则负控 | `min_track_width=0.2` | 抓 1 项 |
| 历史对照 F-80-1 | 修复前规则原值 | 抓 6 项 |
| 历史对照 F-82-1 | 修复前网类状态（仅 `Default`、指派 `{}`） | 抓 4 网类键 + 146 指派失配 |
| 正控 | 意图/SPEC 原值 | 0 失配 |

## 5. 覆盖小结（工程文件闸现覆盖 4 向）

1. `design_settings.rules` ↔ 红线规则源 `drc_rules.json`（7 项）
2. `rule_severities` ↔ JLC 模板
3. `net_settings`（网类 + 指派）↔ 意图工程
4. **`net_settings` DRC 相关字段 ↔ 红线 SPEC `net_classes`**（本件新增）

## 6. 残余

- ① 对间净空 0.875 仍为 **L1**；非执行者 pass 2/2、板厂券仍欠（外部）。
