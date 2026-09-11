# CO-78（L2 声明一致性 · 回归闸）— 层角色漂移机判闸；F1 缺陷类**关闭**

> 日期 2026-09-12｜工具 `tools/p3_v57_co78_layer_role_drift_gate.py`｜记录 `m13_v57_co78_layer_role_drift_gate.json` `2e5127c91e0b8e00`｜boundary **v1.43**

## 1. 判据（把 CO-72/73/76 的缺陷类固化为闸）

LID REV6 口径：**signal = F/In2/In5/B；GND 平面 = In1/In3/In6；电源平面 = In4(P3V3)**。
在**当前态**工件中，任何**角色错配声明**判 FAIL：

- `plane-as-signal`：平面层（In1/In3/In4/In6）被声明为 lane/stub/escape/river/信号层/通道/走线带；
- `signal-as-plane`：信号层（F/In2/In5/B）被声明为 GND/平面/参考/pour 且不含信号语义。

**关键实现点**：角色声明常编码为 **JSON `key -> value`**（如 `{"In6.Cu": "transition_eligible"}`）。
首版 walker 只扫字符串*值*，因此**对照件 0 命中 ⇒ 闸无齿**；修正为同时扫 `key`（`K:<layer> V:<role>`）后才成立。
本件特别记录该自检：**无阳性对照的闸不得宣称有效**。

豁免（显式）：历史/provenance/已退役几何/既往裁决原文/更正说明
（`_spec_rev_*` / `supersedes` / `retired_*` / `ecn_pending_items` / `ruled*` / `appendix` / `rollback` / 「更正」「已失效」「原」「禁止」「PROHIBITED」「历史」）。

## 2. 范围与结果

范围 = boundary §2 **现行输入**（红线 SPEC 原件 / SPEC rev-8 / `route_model_config` / LID REV6 / W0-R 走廊 /
ALLOC.7 / 逃逸域 / manifest）+ **链输出**（drawing / landing / G5 / L4 construction+validation / L5 fab+dfm+si）
+ **引擎源码**。

| 对象 | 判定 |
|---|---|
| 当前态工件（22 件） | **PASS，0 flag** |
| 阳性对照 `SPEC_k2_v4_8L_LID1.json`（历史，LID.1 下 In6=信号层） | **DETECTED**：`/stackup/In6.Cu` = `"signal (PCIe + escape)"` → `plane-as-signal` |

**结论**：当前态无层角色错配。残余的 In6 提及全部为**合法**：GND/参考平面（`layers`、`plane_layers_reserved`、
`reference_plane_adjacency`、`refs`）、dielectric 表、8 层铜层清单，或**显式豁免**的历史/退役/更正语境
（T2-ECN-1/2 既往裁决原文、`retired_in6_segments_bcu`、`_spec_rev_*` provenance）。

⇒ CO-72/73（SPEC）、CO-76（引擎/图纸）、CO-78（全范围回归闸）合起来**关闭 F1 缺陷类**，并留下可重复闸。

## 3. 性质与限制

- **只读**判据：不改任何工件、零几何/阈值改动；四冻结源 4/4 MATCH 未动。
- 闸为**声明层**检查，不替代 G4..G7 几何门；建议与 G5 同批运行（本件未接线，避免改动链上工件）。
- ① 对间净空仍为 **L1**；非执行者 pass 2/2、板厂券仍欠（外部）。
