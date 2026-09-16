# L2 canonical 指引（#K2-16 §三 立；版本 bump 新件，**v2.0 原件字节不动**）

> 本件 = **L2 侧 canonical 声明 + 口径澄清**（#K2-12 §三 `L3/README-canonical.md` 的**同型处置**）。
> **不改冻结件**：`L1/frozen/L1_TOPOLOGY_v2.0.md`、`L2/frozen/L2_STRUCTURE_v2.0.md`（0444）**逐字节不动**；本件只在其外部作口径更正。

## 1. canonical 判定

| 项 | canonical（现行） | 依据 |
|---|---|---|
| **叠层** | **8L**（信号 `F/In2/In5/B`；平面 GND `In1/In3/In6`；电源 `In4`） | owner 裁决 `k2/pm_gate/artifacts/k2_v4/L2/stackup_8layer_decision.md`（`552b2fb922cd8f53`，2026-08-19「用户裁决定案 8 层」）+ canonical SPEC（`317140048c80a569`）+ 交付板 13 zone 实测 |
| **走廊净跨口径** | **焊盘外接框净距**：西 **17.55mm**（`J3/J4` 焊盘东缘 65.05 → `U6` 焊盘外接框西缘 82.60）、东 **27.81mm**（`U6` 焊盘外接框东缘 104.84 → `J2` 侧东端 132.65） | 审计 §10.4 **L2-4 裁定**；逐端点 basis 见 canonical SPEC `corridors_clearance_basis_v24`（`317140048c80a569`）|
| **过孔策略** | ≤2/网（单次换层）；`0.20/0.35`；环宽 ≥0.075；背钻；差分对称 + GND 伴行 ≥1 | 审计 §10.6（L2-6）/ SPEC `vias` |
| **等长窗口** | 对内 ≤0.15mm；对间 ≤1.0mm | 审计 §10.7（L2-7）|

## 2. **作废表述**（`L2_STRUCTURE_v2.0.md` 内的历史文本，禁再作为依据）

| 位置（v2.0） | 作废表述 | 现行口径 |
|---|---|---|
| L1 行 / L6 行 / L95 节 | 「**6 层** × 单芯片走廊」「层数 = **6L 判定流程终定**」 | **8L**（§1）|
| **L55–56 行** | 走廊「**17.30 / 27.40**」（器件体宽口径） | **17.55 / 27.81**（焊盘外接框净距，§1）|
| L25 行 | 「`In2.Cu` = **唯一**内部信号层」 | 信号层 4 层：`F/In2/In5/B` |
| 同件「8L 重入 ECN 触发条款」 | 6L 时代机制说明 | 保留为**历史机制说明**（不再作为层数依据）|

> `L1_TOPOLOGY_v2.0.md` 内「6L 试用 / 6L 判定流程终定」同属历史（详见 `k2/pm_gate/artifacts/k2_v4/L2/L2-ERRATA-8L-v1.md` `eb9354a6b8ffd535`）。
> `k2/docs/01-architecture.md` 已正确（6L 标历史）⇒ **不动**。

## 3. **待监理裁（本指引未收口项）**

owner 裁决件 `stackup_8layer_decision.md` 的**逐层角色表**写作 `F/G/S/G/P/G/S/B`（GND = `In1/In3/In5`、信号含 `In6`），与 canonical/交付板（GND = `In1/In3/In6`、信号含 `In5`）**In5/In6 互换** ⇒ 请监理裁定以何方为准（若 owner 表为准 ⇒ 属层角色/拓扑变更，需 owner）。详见 `L2-ERRATA-8L-v1.md` §4。

## 4. 与 P3/P4 的关系

- **P3 图集**按本指引出（`k2/pm_gate/artifacts/k2_v4/L3/drawings/04_layer_assignment.svg`、`03_corridor_occupancy.svg`）。
- **P4 输入前置**见 `k2/docs/K2-P4-INPUT-PREREQUISITES-v1.md`。
