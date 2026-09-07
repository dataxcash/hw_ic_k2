# M14 v38 session 记录（最终版）— G4 判定 + 根因深化到极性

> 承接：m13_v37_session_handoff.md。本 session 主任务 = 建确定性可行性命门（容量模型）+ 定位 16 对失败根因。
> 纪律：全前台自跑、禁 task() 委派、禁后台长跑、禁暴力迭代（同参≤2 带依据）、禁 chmod、禁无依据 --all-v4。
> 只读计算 + 引擎调用（`bga_per_ball_escape`），未改引擎 → 冻结保持 0/0/0。

---

## 0. 一句话结论（最终版，v37 判定已达成，根因已实测钉死）

**G4 容量判定 = 可解（引擎 `bga_per_ball_escape` 判 FEASIBLE，deficits=[]）。**
**但 16 对全量失败的真根因不是"容量/列槽"，而是 P/N 极性错配**——已实测确认（详见 §6 R3）。
→ 方向：**在引擎拓扑层建"极性不变式"（三端 P/N 位序统一），而非改容量/列槽分配**。详 `m13_v38_plan_polarity_invariant.md`。

> ⚠️ 本文件头部早期版本（§0-§5）曾把根因归为"走廊零余量/共享列槽"——**该判断被后续实测证伪**，
> 属本 session 认知迭代。**以 §6 根因 + §7 结论为准**，勿引用早期 §0 的"零余量=命门"定性。

---

## 1. 存量容量产品评估（handoff 前置）

| 存量 | scope | 复用 |
|---|---|---|
| `model_solves/capacity_map_v6/v7` | 旧板 k2_v6，U3/U7/J2/J3/J4 走廊探针 | ❌ 旧板场景，仅口径参照 |
| `cap_wall_v8` | 电容墙 + 走廊 BLOCKED | ❌ 旧板，教训同族参照 |
| `per_ball_escape_6L_report.json` | **本板 U6 权威逐球逃逸** | ✅ **核心输入** |

→ 无现成 U6 容量模型可复用，故先建容量模型，后经引擎实测证伪"容量是命门"。

## 2. G2/G3/G4 容量计算（早期成果，保留数字供参照）

- 对中心距 = 0.205+0.175+0.205+0.875 = **1.46mm**（route_model_config capacity_audit 口径）
- G2：东 16 对（A_PER 8 + B_PET 8）穿 In2 gutter = 32 单端；西 16 对（A_PET 8 + B_PER 8）direct
- G3：In2 穿越 N=16.2/S=18.8mm → 对槽 N=11/S=12 → **ΣC=23 槽**
- G4：ΣD=16 对 ≤ ΣC=23 槽 → 可解，余量 +7 槽（引擎 per_band/per_wing 亦全 ok=True）

## 3. 引擎 G4 容量判定（权威）

`reproduce_per_ball_escape.py` → `bga_per_ball_escape`（引擎本体）跑 K2：

```
verdict: FEASIBLE  signal_balls=64  direct=32  via=32  crossing_pairs=16  deficits=[]
per_band: A_PER/B_PET/A_PET/B_PER 各 pairs=8 needed=11.68mm corridor=23.36mm fit=True fanout_ok=True
per_wing: N crossing=8 need=11.68mm in2=16.2mm ok=True | S crossing=8 need=11.68mm in2=18.8mm ok=True
```

→ **引擎判"装得下"(FEASIBLE)，无缺口。G4=可解。**（引擎原始输出已贴，见本 session 对话）

## 4. 早期方向错误（坦白）

- 曾手写 `cap_model_v38.py`（零散脚本）算容量 → **用户否决"独立零散脚本"**；已删除。
- 曾把根因归为"走廊零余量/共享列槽" → **被引擎实测证伪**（见 §6）。

## 5. 认知纠偏（用户三连）

1. 说人话 → 用大白话解释容量。
2. 用 ENG 跑 → 用 `bga_per_ball_escape`（引擎）判 G4，不手算。
3. **产出物 = 整体 EDA TOPO ENG（`SolvePipeline`）**；K2 只是验证项目；不接受零散脚本。→ 极性不变式方案落在引擎拓扑层。

## 6. 引擎现状基线 + 根因实测（§最终结论，勿被 §0 早期误导）

**引擎 = `SolvePipeline`（EDA TOPO ENG）** 五阶段：①routing_topology_gate 可行性 → ②capacity 容量门 → ③channel_alloc 分配 → ④escape_landing 落点 → ⑤hs_route_model solve_all_v4 求解。

**`solve_all_v4` 现状**（`/tmp/solve_v33g`，base fpsha=`f6273de6`=当前权威板）：

```
solved: 仅 PCIE_UP1（1 对）
失败 17 对，reason 高度同质：
  flip=True via 换层 P/N 极性不一致（相向交叉 min 边缘距 -0.2050 < 0.175 @ 逃逸点）
  或 落点驱动逃逸 P/N 相向交叉（min 边缘距 -0.2050 < 0.175）
```

**根因 = P/N 极性错配**：
- 芯片侧（A_PER 系）：N 上 P 下（`PCIE_DN0_N` R1 y=57.64 / `_P` N2 y=57.12）← chip_landing+ballmap
- 轨道侧：`_expand_pair`(L740) 写死 "P=track_y-0.19(上)、N=track_y+0.19(下)"
- 连接器侧：`_check_pn_polarity`(L592) 只测 x 侧符号，未与芯片/轨道拟合
→ 芯片侧(N上P下) ↔ 轨道侧(P上N下) → 逃逸出口遭跨相交 → min 边缘距 -0.2050（P/N 重叠）→ INFEASIBLE。

## 7. 结论 + 实施方向

- **G4 容量门已达标**（引擎 FEASIBLE）；**失败根因 = 极性**，非容量/列槽。
- **方案**：`m13_v38_plan_polarity_invariant.md` —— 引擎拓扑层建**每 base 全链一致极性不变式**（三端位序统一），轨道 `_expand_pair` 不再写死、布线 flip 由极性派生，向下游（③⑤）传递。
- 用户已认可方向。

## 8. 产物

- `m13_v38_plan_polarity_invariant.md`（细化实施计划，NEW SESSION 核心）
- `m13_v38_capacity_gate_record.md`（本记录，最终版）
- `m13_v38_branch_summary.md`（状态总结 + NEW SESSION PROMPT）

## 9. 纪律核对
- 未改引擎/板/SPEC（冻结 0/0/0）✅；未跑 --all-v4 ✅；未暴力迭代 ✅；引擎判定（`bga_per_ball_escape`）+ 现状基线（复用 v37 已跑的 v33g）✅。
