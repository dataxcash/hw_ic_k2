# L2 canonical 指引（#K2-16 §三 立；版本 bump 新件，**v2.0 原件字节不动**）

> 本件 = **L2 侧 canonical 声明 + 口径澄清**（#K2-12 §三 `L3/README-canonical.md` 的**同型处置**）。
> **不改冻结件**：`L1/frozen/L1_TOPOLOGY_v2.0.md`、`L2/frozen/L2_STRUCTURE_v2.0.md`（0444）**逐字节不动**；本件只在其外部作口径更正。
> **修订留痕（2026-09-16）**：v1（`1ad55180c4c74e65`）→ 本版：§3 由「待监理裁」改为**已收口**（In5/In6 层角色，L2 自裁，引 `L2_RULING_in5_in6_role_v1.md`）。

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

## 3. **In5/In6 层角色口径 —— 已收口**（2026-09-16；L2 自裁，**不新增决策**）

| 项 | 判定 |
|---|---|
| **canonical 层角色** | 平面 `GND = In1/In3/In6`；信号 = `F/In2/In5/B`；电源 = `In4`（双区拆分） |
| owner 裁决件 `stackup_8layer_decision.md`（`552b2fb922cd8f53`）的 `F/G/S/G/P/G/S/B` 表 | **历史口径（层名旧标）** ⇒ 仅逐层字母表作废；「8L 定案」本体 / 料号 `JLC08161H` / SI·成本背书**继续有效** |

- **依据**：`In5 = signal / In6 = GND` 系 **2026-09-12 L2 叠层分配自裁**（CO-67 / CO-68 / CO-73），
  已在 SPEC `rev-5 / rev-6 / rev-7` 在册（`_spec_rev_5.authority`、`_spec_rev_6` 层名更正、
  `_spec_rev_7`「In6=GND 平面（在册）」）；交付板 `d4e81f647be7f980` 实测 `In5.Cu 2008 段 / In6.Cu 0 段`
  且 `In1/In3/In6 = GND` 铜区；`criteria/` 两份对层角色**零引用**。
- **件**：`L2_RULING_in5_in6_role_v1.md`（本目录，sha256 `5835d392151a0b1946c750f805212ed3ebc66f0c235ea5065bdd05a735eeb1c5`）；
  `L2-ERRATA-8L-v1.md` §4 的「请监理裁」项由本件收口。
- 若 owner 主张按 owner 表实作 ⇒ 属 **L1 拓扑变更**（需全板重布）⇒ 走 owner 复议。

## 4. 与 P3/P4 的关系

- **P3 图集**按本指引出（`k2/pm_gate/artifacts/k2_v4/L3/drawings/04_layer_assignment.svg`、`03_corridor_occupancy.svg`）。
- **P4 输入前置**见 `k2/docs/K2-P4-INPUT-PREREQUISITES-v1.md`。
