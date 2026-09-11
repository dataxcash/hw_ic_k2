# UC-01 追加证据 v3 — 假设 H1 的预登记证伪（A″ 撤回）

> 2026-09-11（20:2x）｜发起：ARCHER｜性质：**UC-01 证据增补（单次预登记实验 + 负结果归档）**｜不改裁决项、不改冻结四源
> ｜被增补件：`..._UC01_stackup_8L_required_v2.md`、`...uc01_addendum_v2_premise_bprime_via.md`｜状态：**待 owner**

## 1. 预登记（运行前固定；§7.1-2 格式）
- **假设 H1**：canonical（形状 `t2`）把走廊 run 强制走 `In2`（内层），因此 up 带出现 `In6↔In2` 内层↔内层跨层（64 埋孔）。
  若改用引擎**已有**的「每组 (corridor,band) 独占派生通道层」构型（`--r1-5-shape channelized`，`else` 发射分支：
  每网仅 2 via，均为 `F↔lay`，`lay=glayer[corridor/band]`），则内层↔内层跨层应为 0 ⇒ 或可免除 HDI。
- **判别观测**：① 探针件 via 层对是否含内层↔内层；② `gate_status.failed`；③ 同层交叉数；④ 独立 A-CN.9 复算。
- **处置规则（先行）**：若 ①=0 且 ②=∅ ⇒ H1 成立，A″ 进 owner 菜单（仍不采用）；
  否则 ⇒ H1 证伪，A″ 撤回，菜单收窄。

## 2. 运行与红线保护
- 命令：`python3 tools/p3_v57_w3_constructive.py --r1-5-shape channelized --out /tmp/opencode/w3_h1_channelized.json --landing-out /tmp/opencode/w3_h1_landing.json`
- wall **42.9s**（≤120s 护栏）；单次运行，**非**参数扫描。
- **canonical 保护**：引擎会无条件改写 `m13_v57_w3_resource_gate.json` 与 `..._W3-CN.27.json`（`p3_v57_w3_constructive.py:1064/1310/1547`）。
  运行前已字节备份，运行后逐字节还原，SHA **前后一致**：
  `resource_gate=9b23c657…`、`_W3-CN.27.json=13dfb9f4…`、`m13_v57_w3_joint_assignment.json=13dfb9f4…`
  （`git status` 跟踪区仅 `? _shared`）。探针输出仅落 `/tmp/opencode`。

## 3. 观测（负结果）
| 项 | canonical（t2） | 探针（channelized） |
|---|---|---|
| verdict | **FEASIBLE_ALL** | **UPSTREAM_CHANGE_REQUEST** |
| `gate_status.failed` | `[]` | **`A-CN.1c` / `A-CN.4` / `A-CN.9`** |
| 同层交叉 | **0** | **324**（要求 0） |
| via 总数 | 256 | **128**（每网 2） |
| via 层对 | `F↔B 64` / `F↔In6 64` / `In2↔B 64` / **`In2↔In6 64`** | `B↔F 64` / `F↔In2 32` / `F↔In6 32` ⇒ **内层↔内层 = 0** |
| 证书 | `[]` | 2 张：`CONSTRUCTION_INFEASIBLE`（crossings=324，planar fan）＋ 净距（`viol_track_track` 等） |

- ⇒ **H1 的"机制"成立**（内层↔内层跨层确实可归零），但 **H1 的"可行性"被证伪**（324 交叉 + 净距违例）。
- ⇒ **互斥结论（本构造族内）**：`同层交叉=0`（canonical，代价 64 埋孔）**与** `埋孔=0`（探针，代价 324 交叉）**不可兼得**。

## 4. 修正 v2 §4 的一处表述
- v2 §4 曾称埋孔是「4 信号层逃逸的**拓扑必然**」——**该表述不成立**（探针证明：单层构型下无需任何内层↔内层跨层）。
- 正确表述：**64 埋孔是"换取同层交叉=0"的价格**，属本构造族内的**取舍**，不是层数的必然推论。

## 5. 处置
- **A″ 从 owner 菜单撤回**（H1 已证伪）。
- 菜单回到 **{A′ , B′}**：A′（8L 派生 + 0 交叉 + 64 埋孔/HDI）／B′（6L binding ⇒ 回 L1 拓扑）。
- 若仍想"0 交叉 ∧ 0 内层↔内层"，唯一未排除的路径是**改 L2 通道层着色/run 层分配（≥3 色、按网选层）**，
  属 **L2 事实 ⇒ 必须走变更单**，且未验证（本次构型仅 2 色且交叉 324，不构成证据）。

## 6. 红线
未改冻结四源；canonical 已逐字节还原（SHA 前后一致）；探针仅 `/tmp/opencode`；单次预登记运行；
未伪造 sign-off；未动 L4/L5。本次运行属"为 owner 变更单取证"（负结果同样归档），非采用、非放行。
