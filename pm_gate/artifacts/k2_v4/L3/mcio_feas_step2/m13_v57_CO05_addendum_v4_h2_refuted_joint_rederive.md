# CO-05 追加 v4 — 假设 H2 证伪：落列单点补丁不可行，CO-05b 须 **R1.5+R3 联合重派生**

> 2026-09-11｜发起：ARCHER｜性质：**单次预登记实验（负结果归档）**｜不改冻结四源、不改 canonical

## 1. 预登记（运行前）
- **假设 H2**：把 `r3_place` 的落列从 R3X2 的 rank 外推改为"**最靠该 pad 连接器列的声明 gap**"（配对局部），
  并改用 BASE F-8 多候选域；估计可在**不破坏构造可行性**的前提下为 O4 的 (via,landing) 配对求解提供几何基础。
- **判别观测**：`W3-CN.28` 的 `verdict` / `gate_status.failed` / `same_layer_crossings` / 证书。
- **处置规则**：若 `FEASIBLE_ALL` 且 `A-CN.9 0/0/0` ⇒ H2 成立，继续接 via 配对求解；否则 H2 证伪、引擎回退。

## 2. 观测（H2 证伪）
命令：`python3 tools/p3_v57_w3_constructive.py --out /tmp/opencode/w3_cn28.json --landing-out /tmp/opencode/w3_cn28_landing.json`
| 项 | 结果 |
|---|---|
| verdict | **UPSTREAM_CHANGE_REQUEST** |
| failed | **A-CN.1d / A-CN.1b / A-CN.4 / A-CN.9** |
| 证书 (4) | ①`R1_chip_escape_column`（frame `J3/up`，rows N/P = **null**）②`R1_5_chip_transition` **crossings=122**（要求 0）③`R1_chip_escape_column`（`|dx| ≥ 0.525`  snapping）④… |
| wall | 36.0s |

**归因**：落列不是独立变量——`r1_place` 把 `r3` 的落列同时当作（a）**净距索引项**（`_va` 列表含 corner/drop/land 的 `(lx, ·)`）
与（b）**障碍**；改落列 ⇒ R1 的 via 行选择改变 ⇒ **平面扇 (R1.5) 失效（crossings 122）**。
⇒ H2 的"落列单点补丁"**不可行**；CO-05b 必须是 **R1.5 与 R3 的联合（joint）重派生**（在保持 planar-fan 约束下同时求解 via 与落列）。

## 3. 处置（回退，无残渣）
- 引擎已**回退**（`REVISION` 回 `W3-CN.27`；`r3_gaps` 回 `…_r3x2.json` + 原 sha `5511c8c3…`）。
- canonical 未动：`m13_v57_w3_joint_assignment.json = 13dfb9f4d74224d9`；`m13_v57_w3_resource_gate.json = 9b23c657dd4d72c1`。
- 探针产物已**隔离**至 `/tmp/opencode/quarantine/`（`…_W3-CN.28.json`、`…upstream_change_request_W3-CN.28.md`）；跟踪区仅 `? _shared`。

## 4. 仍然成立的结论
- **几何可行性**（追加 v3）：在既有合法域内，`(landing=最近声明 gap, via∈verdict 候选框, y_l∈y_band)` ⇒ **32/32 对 `min|ΔL| = 0`（worst 0.0206mm）**。
- **但**该几何必须与 **planar fan（A-CN.1c/1.5）** 联合求解才可实现 ⇒ CO-05b 的构造形态 = R1.5+R3 联合派生（保留扇平面性 + 配对等长）。

## 5. 红线 / 状态
未改冻结四源；canonical 未动；单次预登记运行（非参数扫描）；探针输出仅 `/tmp/opencode`；**G7(O4) 仍 OPEN**。
