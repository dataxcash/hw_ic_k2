# m13 v57 — W3 (G4) 联合指派 Boundary Declaration

> Revision **W3-JA.1**｜Schema 1｜Artifact `m13_v57_w3_joint_assignment.json`
> 契约 `m13_v57_w3_kickoff_card.md`（W3-C1，sha `97a8084bb73f3af2…`）
> Producer `k2/tools/p3_v57_w3_joint_assign.py`
> Independent verifier `k2/tools/p3_v57_w3_validator.py`（不 import 引擎，仅黑盒重跑做序无关性）

## 0. 冻结指纹（运行期硬校验，drift → exit 2）

9 输入 + card 全 64hex：SPEC `0bd52ed48e720b8c…` / rules `0a459839e15960b8…` /
manifest `a8ef3ea8ecff99d7…` / W0-R `80ee9adb78a7e9ad…` / F-3 `ff804e1edfacbf02…` /
F-13 trace `e288ffa5421c2297…` / F-13 pair `82e11c4cbdb4e8d4…` / F-8 `8a31632907b17148…` /
F-6b `9070ed53f970f480…`；`frozen_sha_check.drift = []`。

## 1. Verdict and result

**`verdict = "CERTIFICATE"`**（全有或证书）：W3-C1 §7 构造域内 **2 个层不可行**，故按 F-12
**不重发射** `chip_landing_rows`（`landing_rows=null`，`landing_rows_status="NOT_REEMITTED"`）、
**不发射节点图纸**（`pages[*].nodes = {}`，全有或证书）。层判定：

| 层 | status | 方法 | 结果 |
|---|---|---|---|
| R1 chip 出逃列对 | **FEASIBLE** | 规范序精确 DFS（跨页并列 ≥0.525），33 节点 | 64 via 两两 ≥0.525，域 `0.525+0.38` 双约束 |
| R2 走廊 lane | **FEASIBLE** | 精确保序最小代价 DP（字典序 tie-break） | EAST 11.92mm + WEST 30.90mm = 42.82mm |
| R3 连接器落点 | **CERTIFICATE** | 精确 CSP（MRV+前向检查） | J2 可行（36/36）；**J3/J4 不可行**（鸽笼核心） |
| R1.5 芯片侧过渡段 | **CERTIFICATE** | 构造族枚举（4 变体/走廊） | 每走廊最小交叉 17/19；x 序逆 lane 序 36/28 处 |
| REFCLK | FEASIBLE_DECLARED_OPEN_CROSS_SEGMENT | W0-R 域 | 2 页 F.Cu，页间 5.4/15.7 ≥ 1.46；跨走廊段无权威承载 |

## 2. 证书（4 张）

1. **W3-R1_5-PLANARITY-EAST_CHIP_TO_J2**：构造族 `{V_at_viax, Z_r15} × {P,N}` 交叉数
   `{P:17, N:21, Z-P:20, Z-N:26}`，最小 17；`x_order_inversions_vs_lane_order=36`。
2. **W3-R1_5-PLANARITY-WEST_MCIO_TO_CHIP**：`{P:19, N:19, Z-P:43, Z-N:48}`，最小 19；逆序 28。
3. **W3-R3-JOINT-CONSERVATION-J3**：最小核 `['PCIE_UP2_N','PCIE_UP3_P']`（同 y=43.25、唯一候选列
   55.9）→ W3-C1「落点 y := pad y」下 0.525 互斥不可能（鸽笼）；**放宽探针 feasible=True（19 节点）**。
4. **W3-R3-JOINT-CONSERVATION-J4**：最小核 `['PCIE_DN_OUT4_N_MCIO','PCIE_DN_OUT5_P_MCIO']`；
   放宽探针 feasible=True。

> 证书口径：R1.5 = **构造域枚举证书**（域大小 4 变体/走廊，非全局不可能性证明）；
> R3 = **鸽笼证明**（单候选列 + 同 y，确定性最小核）。

## 3. 验收谓词实测（`gate_status.predicates`）

| 谓词 | 结果 | 说明 |
|---|---|---|
| A-W3.1 R3 每 pad 恰 1 落点 | **FAIL（归因证书）** | 72 entries，J2 36 已解；J3/J4 由证书归因 |
| A-W3.1b R1 每页 2 via | PASS 64 | — |
| A-W3.2a R1 64 via 两两 ≥0.525 | PASS 0 违例 | 联合 DFS（非逐页选择） |
| A-W3.2b R2 lane 严格递增 | PASS | 按 F-5 键 |
| A-W3.2c R3 同 gap 列 ≥0.525 | PASS（已解部分） | J2 |
| A-W3.2d REFCLK ≥1.46 且在 span | PASS | 5.4 / 15.7 |
| A-W3.3 双端 |Δ| ≤ reach_avail 45.4 | PASS | Δ0-4 修订口径 |
| A-W3.4 层语义 / 每线 via≤2 | PASS | F.Cu→In2.Cu→F.Cu；REFCLK F.Cu |
| A-W3.5 序无关（3 枚举序） | PASS | `natural/reverse/hash` 输出逐字节一致（`1997416e6a686768`） |
| A-W3.6 全有或证书 | PASS | CERTIFICATE ⇒ landing null、节点空 |
| A-W3.7 白名单 | PASS | 引擎与工件零 `x_window/max_x/tracks_y/EscapeTable/...` |
| A-W3.8 指纹 | PASS | 9 输入 + card 全 64hex MATCH |

## 4. 非断言 / 禁反演

- 不宣称 R1.5 全平面不可行（仅构造域枚举）；不宣称 R3 物理不可建（仅 W3-C1 规则下不可行）。
- 不从 R1 DFS 解反推"唯一指派"；不把 R2 最小代价解当几何唯一解。
- 未做 DRC/板级几何；未写板；未改冻结件与已发布契约。
- 未发射任何 `chip_landing_rows`（F-12：证书态禁中间态入 S2）。

## 5. 逃生门（上游输入变更，重跑全链）

1. R1.5：把「R1 via x 序与 R2 lane 序同向」升为 **R1 准入约束**（F-13 域需重发，加 x-序维）。
2. R1.5：允许过渡段使用第二铜层（层链 F→In2→?→F，`vias.high_speed.max_per_line` 需放宽）。
3. R3：落点 y 放宽为 F-8 已给的 `y_band`（probe 已证可行）→ 需 **W3-C1 v1.1** 版本 bump。
4. REFCLK：L2 裁跨走廊段层/路径（D0-2 只裁了 REFCLK 承载层）。
