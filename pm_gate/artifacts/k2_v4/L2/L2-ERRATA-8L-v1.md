# L1/L2 文档 errata —— 8L 为 canonical（6L 文本标历史）v1

> **依据**：监理 **#K2-16 §二 R3**（裁「errata 版本 bump 新件，不改原件」）。
> **位置**：本件落 **非冻结** 目录 `k2/pm_gate/artifacts/k2_v4/L2/`（冻结目录 `L1/frozen/`、`L2/frozen/` 为 **0444 只读，ENG 不写**）。
> **性质**：**口径澄清**，不引入新决策；不含几何/网表/器件变更。

## 1. 结论

1. **canonical 叠层 = 8L**（`F/G/S/G/P/S/G/B` 语义见 §4）。
2. `L1_TOPOLOGY_v2.0.md` / `L2_STRUCTURE_v2.0.md` 中的「**层数 = 6L 判定流程终定**」表述 = **历史文本**，**不再作为 L3/P4 的层数依据**。
3. 上述两份冻结件**原件保持不动**（0444），本 errata 仅作外部口径更正。

## 2. 依据（三重）

| 源 | sha256(16) | 内容 |
|---|---|---|
| owner 裁决件 `k2/pm_gate/artifacts/k2_v4/L2/stackup_8layer_decision.md` | `552b2fb922cd8f53` | **2026-08-19**：「状态: 用户裁决定案 **8 层**」 |
| canonical `SPEC_k2_v4.spec-rev-23.json` | `55c5bda7cf172da1` | 8L：`stackup` 8 层键；`layer_plan.in6_usage` 明载 In6 = GND 平面（信号层 = F/In2/In5/B） |
| 交付板 `k2_v4_8L.l4.kicad_pcb` | `d4e81f647be7f980` | 13 zone 实测：In1/In3/In6 = GND 铺铜；In4 = 电源分区；F.Cu 4 区 |

补充：`L2-5 裁定`（审计 §10.5，`c3ee574455cf6633`）已就「In1/In3/In6 = 整板 GND 平面；信号 = F/In2/In5/B」**予以确认**。

## 3. 6L 文本逐处标记（**只读引用，不改原件**）

| 件 | 行 | 原文要义 | 处置 |
|---|---|---|---|
| `L1/frozen/L1_TOPOLOGY_v2.0.md` | L1 标题 / L7-8 / L22 | 「单 DS320PR1601 × 46mm × **6L**」「层数（6L vs 8L）= **6L 判定流程终定**」 | 标 **历史**（层数依据改 canonical 8L） |
| `L2/frozen/L2_STRUCTURE_v2.0.md` | L1 标题 / L6 / L25 / L30-31 / L95 | 「**6 层** × 单芯片走廊」「层数 = **6L 判定流程终定**」「In2 = **唯一**内部信号层」「6L vs 8L 层语义」 | 同上（其「8L 重入 ECN 触发条款」保留为历史机制说明） |

> 说明：6L 文本系 2026-09-05/06 流程产物；8L 系 **2026-08-19 用户裁决在先**（时间上早于 6L 终定文本），本次以 owner 裁决 + canonical SPEC + 交付板实况收口。

## 4. **新增发现（请监理裁 —— 超出 R3 原范围）**：owner 定案件的**逐层角色**与 canonical/板冲突

- **owner 裁决件**（`stackup_8layer_decision.md`，2026-08-19）写：叠层 **`F/G/S/G/P/G/S/B`** ⇒ GND = `In1/In3/In5`、**信号含 `In6`**（含「低速边带独占 In6」「REFCLK 在 In6 独立层」）。
- **canonical `rev-23` + L2-5 裁定 + 交付板实况**：GND = `In1/In3/In6`、信号 = `F/In2/In5/B`（`In5` 承载 PCIe 走线：板实测 y>71 段 292 条中 In5 270 条）。
- ⇒ 二者 **In5/In6 角色互换**。canonical SPEC 侧已有 `CO-73 更正`（将冲突原文标为「6L 时代残留」）。
- **本 P3 图集按 canonical/板 出**（`04_layer_assignment.svg`），与交付板一致；**未自裁属谁权威**。
- **请监理裁**：① 以 canonical/板 为准 ⇒ 请裁定 owner 裁决件该表为历史口径（errata 追加一行即可）；② 以 owner 表为准 ⇒ 属**层角色/拓扑变更**（影响 SPEC 与板）⇒ 需 owner。
