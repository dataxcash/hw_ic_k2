# m13 v57 — W3 (G4) 联合指派 Boundary Declaration **v1.1**

> Revision **W3-JA.2**｜Schema 1｜Artifact `m13_v57_w3_joint_assignment.json`
> 契约 `m13_v57_w3_kickoff_card_v1_1.md`（W3-C1 v1.1，sha `4555f8b65abeb1a3…`；supersedes v1 `97a8084b…`）
> 生产者 `k2/tools/p3_v57_w3_joint_assign.py`（rev W3-JA.2）
> 独立验证器 `k2/tools/p3_v57_w3_validator.py`（不 import 引擎；仅黑盒重跑做序无关性）
> **本文件取代 `m13_v57_w3_joint_assignment_boundary.md`（v1，W3-JA.1）**；v1 原文与指纹不动。

## 0. 冻结指纹（运行期硬校验，drift → exit 2）

9 输入 + card v1.1：SPEC `0bd52ed48e720b8c…` / rules `0a459839e15960b8…` / manifest `a8ef3ea8ecff99d7…` /
W0-R `80ee9adb78a7e9ad…` / F-3 `ff804e1edfacbf02…` / F-13 trace `e288ffa5421c2297…` /
F-13 pair `82e11c4cbdb4e8d4…` / F-8 `8a31632907b17148…` / F-6b `9070ed53f970f480…` / card v1.1 `4555f8b6…`；
`frozen_sha_check.drift = []`。

## 1. 结果（W3-JA.2）

**`verdict = "CERTIFICATE"`**（全有或证书）：仅 **R1.5 单层平面性** 不可行，故 F-12 下
`landing_rows = null` / `NOT_REEMITTED`，`pages[*].nodes = {}`（不发射中间态图纸）。

| 层 | status | 方法（禁 per-net first-fit） | 结果 |
|---|---|---|---|
| R1 chip 出逃列对 | **FEASIBLE** | 规范序精确 DFS（跨页并列 ≥0.525） | 33 节点；64 via 两两 ≥0.525；双约束 0.525/0.38 |
| R2 走廊 lane | **FEASIBLE** | 精确保序最小代价 DP（字典序 tie-break） | **EAST 11.92 + WEST 30.90 = 42.82 mm**（独立 DP 复核一致） |
| R3 连接器落点 | **FEASIBLE** | 精确 CSP（MRV + 前向检查，y ∈ F-8 `y_band`） | **72/72 落点**；J2 37 / J3 19 / J4 19 节点 |
| R1.5 芯片侧过渡段 | **CERTIFICATE** | 构造族枚举（4 变体/走廊）+ 交叉重算 | 最小交叉 17（EAST）/ 19（WEST） |
| REFCLK | FEASIBLE_DECLARED_OPEN_CROSS_SEGMENT | W0-R 域 | 2 页 F.Cu；页间 5.4 / 15.7 ≥ 1.46 |

## 2. 证书（2 张，均 R1.5）

- **W3-R1_5-PLANARITY-EAST_CHIP_TO_J2**：变体交叉 `{V_at_viax/P:17, N:21, Z_r15/P:20, N:26}` → 最小 17；
  R1 via x 序相对 lane 序逆序 **36** 处。
- **W3-R1_5-PLANARITY-WEST_MCIO_TO_CHIP**：`{P:19, N:19, Z-P:43, Z-N:48}` → 最小 19；逆序 **28** 处。
- 口径：**构造域枚举证书**（域 = 2 shape × 2 极性/走廊），非全局不可能性证明；每条含
  `minimal_core` / `why_no_alloc_possible` / `escape_hatches`（A-W3.6 归因要求）。

## 3. R3 口径变更（v1 → v1.1，重要）

- **v1 规则**（落点 y := pad y）：J3/J4 **鸽笼不可行**——最小核 `['PCIE_UP2_N','PCIE_UP3_P']`
  （同 y=43.25、唯一候选列 55.9）与 `['PCIE_DN_OUT2_N_MCIO','PCIE_DN_OUT3_P_MCIO']`（y=45.75）。
  该结论**保留为取证**（`layers.R3.strict_rule_finding`，J3/J4 各 `feasible=false`，cores 见上）。
- **v1.1 规则**（F-8 原始口径）：落点 `y ∈ entries[*].y_band`（pad 行 ± 半行距；J2 half 0.3 / J3-J4 half 1.25）
  → **72/72 可行**，同 gap 列 `|Δy| ≥ 0.525` 全部满足。
- 变更性质：**修正本卡 v1 的过度收窄**，与 F-8 定义对齐；不是放宽既有验收（v1 严格规则的不可行性仍被
  记录与证明）。触发协议：版本 bump（v1.1 新文件），v1 原地不动。

## 4. 验收谓词（`gate_status.predicates`，W3-JA.2 全 PASS）

| 谓词 | 结果 |
|---|---|
| A-W3.1 R3 72/72 落点（v1.1 条件化） | **PASS 72/72** |
| A-W3.1b R1 每页 2 via（64） | PASS |
| A-W3.2a R1 64 via 两两 ≥0.525 | PASS（0 违例） |
| A-W3.2b R2 lane 严格递增 | PASS |
| A-W3.2c R3 同 gap 列 ≥0.525 | PASS |
| A-W3.2d REFCLK ≥1.46 且在 span 内 | PASS |
| A-W3.3 双端 \|Δ\| ≤ reach_avail 45.4 | PASS |
| A-W3.4 层语义 / 每线 via ≤ 2 / R4 出链 | PASS（R4 键 grep = 0） |
| A-W3.5 序无关（3 枚举序） | **PASS：`natural/reverse/hash` 逐字节一致 `d081618c7b961d77…`** |
| A-W3.6 全有或证书 | PASS（CERTIFICATE ⇒ landing null + 节点空） |
| A-W3.7 白名单 | PASS（引擎零 `x_window/max_x/tracks_y/EscapeTable/ColumnBook`） |
| A-W3.8 指纹 | PASS（9 输入 + card v1.1 全 64hex MATCH） |

## 5. 非断言 / 禁反演

- 不宣称 R1.5 全局不可行（仅构造域枚举）；不宣称 R3 在任何口径下都可行（v1 口径下 J3/J4 已证不可行）。
- 不从 R1 DFS 解反推唯一指派；不把 R2 最小代价解当几何唯一解；不把 R3 的 CSP 解当容量证明。
- 未做 DRC/板级几何、未写板、未改冻结件与已发布契约（v1 契约/工件原样保留）。
- 未发射 `chip_landing_rows`（F-12：证书态禁中间态入 S2）。

## 6. 逃生门（上游输入变更 → 重跑全链）

1. **R1.5（阻塞项）**：① 把「R1 via x 序与 R2 lane 序同向」升为 **R1 准入约束**（F-13 域重发，加 x-序维）；
   ② 允许过渡段使用第二铜层（须放宽 `vias.high_speed.max_per_line`）；③ 放宽 R1.5 的 `no_via`/`no_90deg`；
   ④ F-5 修订（局部放开 lane 单调序换平面性）。
2. **REFCLK**：L2 裁跨走廊段层/路径（D0-2 仅裁了承载层）。
3. **R1.5 微净空 0.075 / 折角 legality**：属 DRC 阶段（`W3-RES-3` DEFERRED-TO-DRC）。
