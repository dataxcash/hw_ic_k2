# CO-82（L2 可审计性）— L4 工程文件网类缺失；并补 CO-81 闸的覆盖盲区

> 日期 2026-09-12｜工具 `tools/p3_v57_co82_l4_project_netclass_align.py`（修复）+ `tools/p3_v57_co81_project_rules_gate.py`（补闸）｜记录 `0c8745064785ee57` / 闸 `a9161a86271c068b`｜boundary **v1.47**

## 1. 缺陷 F-82-1（F-80-1 同族；**且是 CO-81 闸的覆盖盲区**）

`k2_v4_8L.l4.kicad_pro` 的 `net_settings` 与意图件不一致：

| 项 | 意图 `k2_v4_8L.kicad_pro` | `.l4.kicad_pro`（原） |
|---|---|---|
| 网类 | `Default` / `LOW_SPEED` / `PCIe85` / `POWER` | **仅 `Default`** |
| 网-类指派 | **146 条** | **0 条** |
| `Default.clearance` | 0.1 | 0.2 |
| `Default.track_width` | 0.09 | 0.2 |
| `Default.via_diameter / drill` | 0.35 / 0.2 | 0.6 / 0.3 |

后果：用该工程文件跑 DRC 时 **PCIe85（clearance 0.175 / diff_pair_gap 0.175 / width 0.205）、
LOW_SPEED、POWER 语义完全不生效**，而 `Default` 又偏严 ⇒ 该受控文件不但误导审计，还**丢失网类语义**。

**自认疏漏**：CO-81 的闸只覆盖 `design_settings.rules` + `rule_severities`，**未覆盖 `net_settings`**，
因此这条同类缺陷从闸下漏过。本件一并补闸（见 §3）。

## 2. 修复与验证

- 修复：把意图件的 `net_settings.classes` + `netclass_assignments` 对齐进 `.l4.kicad_pro`
  （`4704dec4dd043c59` → **`ce2c2bf0da79a1ff`**；网类 1→4、指派 0→146）。
- **关键验证（是否掩盖了真实板缺陷）**：对齐后用**最自然的命令**重跑 —— 基线 **42** / L4 **42**，
  **new=0 / disappeared=0** ⇒ 即便施加完整 netclass 语义，板仍零新增违规，缺陷确系**工件层**。
- 链不受影响：L4 apply 后板 **`0e636a67c1472462` 逐字节不变**；DFM `40445f87` / SI `73f9b59e` 逐字节不变；
  L4 applier 不覆写工程文件（仍 `ce2c2bf0da79a1ff`）。

## 3. 补闸（CO-81 gate 扩展至 net_settings）

新增 `netclass_guard(ns, intent_ns)`：按**网类名**逐字段比对 + 比对 `netclass_assignments` 全量。
覆盖范围 = `design_settings.rules`（7 项）+ `rule_severities` + **`net_settings`（网类 + 指派）**。
模板 `tools/k2_jlc_template.kicad_pro` 显式豁免网类检查（只承载规则），豁免理由写入记录。

| 控制 | 输入 | 实测 |
|---|---|---|
| 负控（rules） | `min_track_width=0.2` | 抓 1 项 |
| 历史对照 F-80-1 | 修复前规则原值 | 抓 **6 项** |
| **历史对照 F-82-1** | 修复前网类状态（仅 `Default`、指派 `{}`） | **抓 4 个网类键 + 146 条指派失配** |
| 正控 | 意图值原样 | 0 失配 |

结果：**5/5 受控工程文件 PASS**；`teeth_ok=true`。

## 4. 残余

- ① 对间净空 0.875 仍为 **L1**；非执行者 pass 2/2、板厂券仍欠（外部）。

## 5. 附带补强：CO-77 闸从「12 项 claim」扩展为「全量 sha16 引用」（并自捕获一个转义 bug）

本轮发现我**自己**在 v1.47 里把 CO-82 卡片的 sha 写错（`8f1b70d3…` vs 实际 `4e4f1128…`），而 CO-77 闸的 12 项 claim 模式**覆盖不到** —— 又一次「闸覆盖不全」。
故把 CO-77 扩展为：**文中任何 `file` `sha16` 引用都必须等于实际文件**，除非该行显式标注历史
（原/已取代/历史/应为/实为）或为「before → after」变更记法（引用后紧跟 `→`）。

- v1.47：**65 条引用全数匹配，PASS**。
- 牙齿：v1.46（引用了被 CO-82 取代的 CO-81 闸记录 `1f25c6a9…`）→ **CITATION_MISMATCH**，正是该类缺陷。

**过程中我犯并自捕获的错**：首次给该闸写正则时把 `\\.`/`\\s` 双重转义，导致正则匹配不到任何引用 ⇒ v1.46 反而「PASS」（**又一次空真**）。
修法：改正转义，并给闸加**非空真下限**（`CITE_FLOOR = 30`：引用总数低于下限一律判 FAIL）。
教训与服务化：**闸自身也必须有非空真下限与负控**，否则修复动作会退化成空真。
