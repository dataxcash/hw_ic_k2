# 变更单 CO-02 — W3(L3) 逃逸不可行 **升级 L1/L2 结构裁决**（宪法 Ch.3 §2/§5 + Ch.7 §3）

> 2026-09-11｜发出：L3（施工层，ARCHER）｜收件层级：**L2 结构（主）/ L1 整体（层数）**
> 依据：`LAYOUT_CONSTITUTION` Ch.3 §2（下层无权私下妥协，走变更单升级）、§5（L1 结构预检缺失须补后重冻结）、
> Ch.7 §3（变更单制度）、Ch.9 第 2/3 行；`L2_STRUCTURE_v2.0.md`「8L 重入 ECN 触发条款」（L1 冻结件引用）；整改通知 #02。
> **本单不改冻结四源、不改 canonical W3-CN.25。**

## 1. 触发事实（可复核）
| # | 事实 | 证据 |
|---|---|---|
| F1 | 完整净距套件下构造域 R1 29/32（去净距 32/32） | `m13_v57_w3_full_clearance_infeasibility_cert.json` W3-FCC.1 P4/P7/P8 |
| F2 | 逃逸族级穷尽：域扩/序变体/T-5/T-5′/共线行/相干字段/净距放宽 全部不可行或退化 | 同上 P2..P8；`m13_v57_w3_reopen_probe_v1.md` §5 |
| F3 | 连接器 landing-stub 净距为残余瓶颈 | `m13_v57_w3_reopen_probe_v1.md` §5.3/§5.4 |
| F4 | L1/L2 冻结包络内部不一致（拓扑=8L 冻结，叠层=6L） | SPEC `/constraints.j2_escape_topology`、`/pd.gnd_planes`（含 In5）；`in6_usage` |
| F5 | L2 包络未内嵌完整净距套件；对内等长仅文本未机检 | `m13_v57_l1_struct_preflight_v2.json` P4；L5 SI skew 24.476mm |
| F6 | L1 结构预检 v2 = PREFLIGHT_FAIL | `m13_v57_l1_struct_preflight_report_v2.md` |

## 2. 变更请求（请 L2/L1 裁决）
- **R-01（L2）**：重开**叠层分配**裁决——6L（1 内部信号层）vs 8L（In2+In6，第二内部信号层 + 额外 GND）。
  ≥2 结构候选竞标记录见 `m13_v57_l2_structural_bid_v1.md`。
- **R-02（L2）**：重开**走廊矩阵 / 过孔策略 / 等长窗口**，将**强条内嵌为硬门禁**
  （JLC 极限 + 完整净距 0.38/0.4525/0.525 + 对内等长 ≤0.15mm）。
- **R-03（L1）**：若 L2 竞标选中 8L，则须**层数裁决重开**（触 SPEC `stackup`/`pd`，属 system design）→
  依 `L2_STRUCTURE_v2.0.md` 8L 重入条款重跑对抗评审后**重冻结 L1/L2**。
- **R-04**：重冻结后重跑 **W3→W4→L4→L5**（L3 只执行已冻结包络，禁止再发明决策）。

## 3. 归属与边界
- 归属：**L2 = 信号/电源完整性工程师**（叠层/走廊/过孔/等长）；**L1 = 系统架构/owner**（层数，触冻结四源）。
- 边界：不改冻结四源（R-03 重冻结为 L1/owner 授权后动作）；不改层用途红线（In4=P3V3、In1/In3=GND）；
  每线 via≤2；零搜索/零暴力迭代。
- 本单**不实施**任何 stackup/加层；仅升级裁决。

## 4. 产物指针
| 件 | 路径 |
|---|---|
| L1 结构预检（机读） | `m13_v57_l1_struct_preflight_v2.json` |
| L1 结构预检（人读） | `m13_v57_l1_struct_preflight_report_v2.md` |
| L2 结构候选竞标 | `m13_v57_l2_structural_bid_v1.md` |
| L2 冻结包络（候选，含硬门禁） | `m13_v57_l2_structural_envelope_v1.json` |
