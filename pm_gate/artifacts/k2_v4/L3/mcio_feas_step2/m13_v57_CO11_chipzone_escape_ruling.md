# CO-11 — 【L2/L3】pair 域 v1.5 落地（变更单）+ chip 区逃逸**容量证明** + 西侧 lane 块重派生路线裁定

> 2026-09-11｜裁判：ARCHER（L2 层角色/走廊分配自裁；L3 域重派生）｜性质：**变更单 + 负结果**
> ｜触发：按 handoff §8-1（F-13 R1 pair 域重派生）+ §8-2（chip 区 via1 (x,y) 联合分配）续做
> ｜证据（只读探针 + 独立复核，全部版本化，冻结四源/canonical **未动**）：
> `tools/p3_v57_f13_pair_coupling_r2_v5.py` → `m13_v57_f13_r1_pair_coupling_v1_5.json`（`6662e0089c88b091`）
> `tools/p3_v57_f13_r1_pair_domain_v1_5_verify.py` → `m13_v57_f13_r1_pair_domain_v1_5_verification.json`（`a93e81e7e7e50f71`）
> `m13_v57_co11_pairv15_probe_fan_engine.json` / `..._wstep1128_...` / `..._wdelta500_...`

## 0. 结论（三句）
1. **pair 域 v1.5 已落地并独立复核**：全 616 pad 障碍场过滤后，冻结 v1.4 的 **440310/537713 行（81.9%）非法**（worst gap 0.0000），v1.5 **0 非法行**（worst gap 0.0750 = ESC 界）。
2. **chip 区残余（UP5/6/7）是闭式容量极限，不是 pair 域污染**：换 v1.5 后 fan 探针仍 **29/32** 且失败页不变 ⇒ 残余 = 西侧 **16 dn via1 + 8 J4-up escape 竖段 = 24 个同层 x 槽**，可用 x 带仅 **9.65mm**，需 ≥10.86mm **⇒ 无解**。**纯 via1 (x,y) 联合分配不可能闭合**（y 自由度无法解耦：J4-up 竖段 y 值域必穿越 dn via1 y 带）。
3. **L2 裁定**：走 **R1 = 西侧 lane 块整体压到 dn via1 带之下（lane_y ≤ 50.198）+ connector 侧 landing 带同步重派生**；R2 = CO-09 §4-3(b) x-band 逃逸横移扇为备选。R1 的 chip 侧已实测闭合，残余在 connector 侧（见 §4）。

## 1. 变更单：F-13 R1 pair 域 v1.5（§8-1 完成）
- **新件** `m13_v57_f13_r1_pair_coupling_v1_5.json`（rev `F13-R1PAIR.7`，sha16 `6662e0089c88b091`），**v1.4 与冻结四源未动**。
- 判据与 W3 运行时 **A-CN.9 全跨距口径同式**：`F.Cu` 段 (chip pad→via1) 与任一 pad 边距 ≥ `escape_clearance` **0.075**；via1 圆 (r=0.175) 与任一 pad 边距 ≥ 0.075；豁免本页自身 4 pad。
- **可分解加速**：单候选合法性只依赖该候选 ⇒ 先算 P/N 合法掩码（~7000 候选 × 616 pad），再在 pair 域做 v1.4 同式 min-dist/max-dist/pad-proximate 归约；wall 32s。
- **独立复核**（非 producer，逐行重建几何）：v1.4 `illegal_rows=440310`（worst gap 0.0000 @PCIE_DN0/input）；v1.5 `illegal_rows=0`（worst gap 0.0750 @PCIE_DN3/input）⇒ **PASS**。机理示例：`pad_seg (92.35,49.76→94.3,49.16) ↔ U6 BY35 (92.95,49.76) 0.0265`（CO-10 §9 实测）。
- **注意（对下游语义）**：v1.5 **不是** v1.4 的行子集——v1.4 的归约被非法行污染（min-dist 落在非法行时该列对被整条丢弃）；v1.5 先过滤后归约，故**列对集合有增有减**（281138 行）。引擎消费时须以 v1.5 为准。

## 2. chip 区容量证明（闭式，L3）
西侧 chip 区同层（In2）竞争实体与 x 值域（`m13_v57_co09_pad_field.json` + manifest 实测）：

| 实体 | n | x 值域（pad_x ± 0.35） | y 带 |
|---|---|---|---|
| 西侧 dn via1（through F↔B，占 In2） | 16 | `[84.25, 93.35]`（dn pad x 84.6–93.0） | `[50.973, 53.066]`（pad_y 51.673/52.366 ± YWIN 0.7） |
| J4-up escape 竖段（In2，pad→lane） | 8 | `[89.30, 93.90]`（J4-up pad x 89.65–93.55） | `[min(vy,ly), max(vy,ly)]`；vy∈[49.06,50.98]、ly∈[50.82,55.20] ⇒ **必含 [50.98, 50.82] 之上整段** |

- J4-up 竖段 y 值域与 dn via1 y 带 **必重叠**（vy ≤ 50.98 < 53.066 ≤ ly 对 idx12–15 恒成立）⇒ 竖段与 via1 **必须 x 分离 ≥ vt 0.4525**（via↔track），via1 之间 ≥ vv 0.525。
- ⇒ 需 **24** 个互异 x 槽，联合 x 带 `[84.25, 93.90] = 9.65mm`，而 `24×0.4525 = 10.86mm > 9.65mm`（按 vv 口径 12.6mm 更劣）⇒ **闭式无解**。
- 与 CO-10 §8.2 的 24 槽/10.9mm 估算一致；本单给出精确值域（9.65mm）并**证明与 pair 域无关**（§3）。
- 注：其余 8 个 up 网（J3-up）竖段只到 pad_y≈50.28 < 50.973−vt，不参与竞争，故为 16+8，非 16+16。

## 3. 实测对照（只读探针；`CO10_*` env 为新增只读旋钮）
| 实验 | 参数 | 落位 | 失败页 | 含义 |
|---|---|---|---|---|
| fan + v1.4（基线） | — | **29/32** | UP5/6/7 | 基线 |
| fan + **v1.5** | pad 场过滤域 | **29/32** | UP5/6/7 | **残余与 pair 域无关**（失败页不变） |
| fan + v1.5 + d3 规则 | — | 28/32 | DN4,UP5/6/7 | D3 落列前提已证伪（CO-10 §0） |
| fan + v1.5 + co10(x 前缀) | — | 25/32 | 7 页 | 纯 x 前缀劣（CO-10 §9 复现） |

## 4. 西侧 lane 块两路线实测（chip 侧闭合 / connector 侧暴露）
| 路线 | 参数 | 落位 | 失败页 | 根因 |
|---|---|---|---|---|
| **R1-a** 整体下移 | west Δy = **−5.0** | 28/32 | DN4–7 | 压到 **connector landing 带**（J3 42.0/44.2/60.2/65.0）下方；lane 端 drop via 落邻页 band |
| **R1-b** 整体压缩 | west STEP **1.128**（16 lane ≤ 50.22） | **29/32** | DN4/5/6 | **chip 侧全闭合**（UP5/6/7 全过）；失败全在 **connector 侧** vv（如 `(55.0,42.574,'P','In6.Cu') ↔ DN3.P 0.0`） |
| R1-b + J4 lx 偏置 | `CO10_FANDX_J4=0.6` | 29/32 | DN4/5/6 | 偏置未能解耦；连接器侧仍需同步重派生 |

**据 R1-b**：把西侧 16 lane 压到 `lane_y ≤ 50.198`（即 `STEP ≤ (50.198−33.3)/15 = 1.1265`）后，up 竖段/角 via 全部落在 dn via1 带之下，chip 侧 **不再需要 24 槽**（降为 dn 16 槽 ⇒ `16×0.4525 = 7.24mm ≤ 9.10mm` 可行）。**代价**：压缩后的 dn lane 端（connector 侧 drop via）落入 J3/J4 landing 带 ⇒ 须**同步重派生 connector 侧 landing（FAN_Y / lx / stub）**，或改用非竖直 stub 的 breakout。

## 5. L2 裁定（下一实现周期的输入，均属 L2/L3，无需 owner）
1. **主路线 R1**：西侧 corridor lane 块 `STEP→≤1.1265`、`LANE_LO=33.3`（16 lane 33.3–50.2），东侧 corridor 块不动（east lane 起 56.66 不变）；**同步重派生** connector 侧 landing：`ll`（J3 42.0/44.2、J4 60.2/65.0）与 lane 端 `ly` 的净距 ≥ vv 0.525，且不同 row 组的 `lx` 须使 drop via 与邻组 land via x 分离 ≥0.525（可用 **FAN_DX 每行组偏置** 或 **非竖直 stub**）。
2. **备选 R2**：CO-09 §4-3(b) **x-band 逃逸横移扇**（西侧 up 竖段 45°/浅角横移到 `x<82.9`），不动 lane 序/O4；须先证 16 条横移扇平面性与浅角 x 净距（CO-09 §4-7 诚实边界）。
3. **POL_OFF 0.19→0.25 仍未落地**（L2 已裁，CO-10 §7.2）——须与 R1 的 lane 重派生**同批**落入引擎（POL_OFF 变化改变 lane 端 y 带，与 R1 的 connector 净距耦合）。
4. **O4 蛇形预算**：R1 改 STEP 后 lane 长度分布变化 ⇒ 与 POL_OFF 一并重派生（L3）。
5. 之后：引擎 rev bump（CO-10 拓扑 + v1.5 域 + R1 lane）→ **一次求解** → G4→G5→G6→G7。

## 6. 红线遵守
只读探针；冻结四源原件未改；canonical `m13_v57_w3_joint_assignment.json`（W3-CN.30 `05f7bd10ab3b45b6`）未动；零坐标搜索；未放宽任何阈值（A-CN.9 vt 0.4525 / vv 0.525 / skew）；无 partial pass；无 sign-off。

---

## 7. 追加实测（第四轮）：**binding constraint 是 connector 侧 landing/stub，不是 chip 侧 lane**
### 7.1 drop via 的 POL_OFF 偏移 ⇒ 避让阈值 0.775（非 0.525）
`build` 中 lane 端 drop via 位于 `(lx, lane_y + pol_off)`（**含 POL_OFF**）⇒ 同一 `lx` 上，
lane 与邻页 land via（`ll`）的净距须满足 `|lane_y − ll| ≥ vv + POL_OFF = 0.525 + 0.25 = 0.775`。
- 原（未压缩）配置 J4-dn `lane=44.98` vs J3-dn `ll=44.2`：`0.78` **恰好** ≥ 0.775（余量 0.005）⇒ 现状本就贴边。
- 压缩后 J4-dn `lane=42.294`（含 −0.25）vs J3-up `ll=42.0`：`0.294` ⇒ 冲突（§4 R1-b 实测）。

### 7.2 闭式不可能性（connector 侧）
以 `|lane_y − ll| ≥ 0.775` 重算：`ll∈{42.0, 44.2}` 的禁带为 `(41.225,42.775) ∪ (43.425,44.975)`
（两带间仅 0.65mm < 单 lane 最小间距）⇒ 合并为 **3.75mm 连续禁带 `(41.225,44.975)`**。
西侧 16 lane 须落在 `[33.3, 50.198]`（chip 侧约束）内、避开该 3.75mm 带 ⇒ 上下两段可用
`7.925mm + 5.223mm`，须塞 16 lane（`STEP≥0.38` 理论可行但 lane 端 drop/land 与邻页 lane 的水平净距同时受约束）
⇒ 实测穷举 `(LO,STEP)` 唯一候选 `LO=33.8/STEP=1.093`（lanes 41.451/42.544/43.637）仍 **29/32**（`vv 0.294–0.313`，§4 失败为 DN4/5/6）。

### 7.3 FAN_DX 与 frame 重排均不足（负结果）
| 手段 | 结果 | 根因 |
|---|---|---|
| `FAN_DX_J4=+0.6`（lx 偏置 0.6） | 29/32 | 不同页映射到**不同连接器 pad**（R3 gap 候选），`pad_x±0.3` 仍可撞同一 x（实测 DN4/J4 与 DN3/J3 的 lx 皆 55.0） |
| frame 重排 `upfirst`（up 占 idx0–7） | **26/32（恶化）** | J4-up lane≤43.52 → connector stub 自 38.9/40.35/42.31 拉到 `ll=65.0`，**纵穿 J3 行/landing**（`vt2_placed ... ↔ DN*.N 0.0`） |

### 7.4 结论（修正 §5 的实现顺序）
1. **binding constraint = connector 侧 landing/stub 架构**（`ll=FAN_Y`、`lx=pad_x−0.3`、竖直 stub）。
   lane 压缩/重排**单独不可能闭合**：任何把 lane 移到 J3 landing 带附近的方案都会在 connector 侧爆掉。
2. ⇒ **R1 的正确形态**：**同时**重派生 (a) connector 侧 landing：`ll` 与 lane 端净距 ≥0.775、
   `lx` **跨页全局唯一**（不依赖 R3 的 pad x 分配，或把 R3 分配一并重派生）、stub 改为**非竖直 breakout**
   （如 CO-09 §4ter 的沿 pad 列竖段 / 或斜段）；(b) 西侧 lane y（可保留原 STEP，仅改映射或小幅压缩）。
3. **R2（x-band 横移扇）不受 connector 侧约束**，是**风险更低的备选**：chip 侧把 up 竖段横移到 `x<82.9`
   即消除 24 槽竞争，且不动 lane/connector ⇒ **建议 R2 优先**（须先证 16 条扇平面性与浅角净距，CO-09 §4-7）。
4. 追加证据（版本化，只读）：`m13_v57_co11_worder_upfirst_probe_fan_engine.json`（26/32，负结果）、
   `m13_v57_co11_wstep1093_wlo338_probe_fan_engine.json`（29/32）。

---

## 8. 第五轮：**32/32 全落位**（存在性证明）+ L2 配置裁定
### 8.1 结果
在只读探针上取得 **32/32**（`PROBE_PLACED_ALL`），并经**非执行者独立复核**：
`m13_v57_co11_placement_verification.json`（`ea85fa2e83b09bf4`）对 320 via / 320 段做**全对全**重算
（vv/vt/tt/全跨距 via 桶 + 全 616 pad 场，仅 F.Cu 段与 pad 比对）⇒ **0 违规 / PASS**。
几何 dump：`m13_v57_co11_placement_probe_rev_geom.json`（`ebd6acc92f3446b4`）；配置：`m13_v57_co11_config.json`（`efc99c51b71e4dc2`）。

### 8.2 L2 配置（四要素，均 L2/L3 自裁）
| 要素 | 值 | 依据 |
|---|---|---|
| **西侧 lane 块压缩** | `lane_y = 33.3 + k*1.1265`（k=0..15 ⇒ 33.3..50.2） | 16 lane 全落在西侧 dn via1 y 带（≥50.973）之下 ⇒ 8 J4-up 竖段不再与 16 dn via1 争 x（24 槽 → 16 槽） |
| **J3 landing 移出 lane 块** | J3-up `ll=31.5`（块下）、J3-dn `ll=51.5`（块上） | 消除 `|lane_y ± POL_OFF − ll| < 0.525`（阈值 0.775，§7.1） |
| **J3 下行组 stub 层 → In2** | `GS_IN2[("J3","L")] = True` | In6 stub 会横切 lane 块；In2 stub 仅需与同层 stub/land 分离 |
| **connector lx 前缀分配** | 同层 stub y 区间重叠时 `lx ≥ 0.525`（`_lx_separate`，零搜索单遍） | 消除 DN/J3 与 UP/J4 的 lx 撞列（§7.3） |
| 落位序 | canonical 逆序（corridor,conn_ref,band,page_id） | 单遍确定性；A1.2 由引擎内部规范排序保证 |

### 8.3 引擎落地的**硬约束**（勿违）
1. **A1.2 序无关**：`--enum-order natural/reverse/hash` 只置换 manifest 输入；引擎内部**必须**按同一 canonical 键排序后再构造（现引擎已如此）。探针的 `order=rev` 即该 canonical 序，须固化进引擎。
2. **零搜索**：探针的「逐行 check 直到通过」是**搜索/回退**，引擎不得采用；须把 chip 区 via1 (x,y) 与 connector lx 做成**闭式前缀分配**（`_lx_separate` 已是闭式单遍，可直接移植；via1 需按 §8.2 的 band 子窗 + 前缀 x 闭合）。
3. **验收**：`FEASIBLE_ALL ∧ same_layer_crossings=0 ∧ A-CN.9 0/0/0（含同页跨极性/全跨距）∧ 对内 skew≤0.15 ∧ wall≤120s`；随后 G4→G5→G6→G7（shop 口径）。
4. **连带重派生**：`POL_OFF 0.19→0.25`（本配置已按 0.25 复算）、O4 蛇形预算（lane STEP 变）、`ll` 变更后的 breakout 长度/等长。

### 8.4 边界（诚实）
- 本结果证明**几何可行**，但**尚未**证明 A1.2（需引擎闭式版）、未过 A1.3 几何不变量（V1–V6）、未跑 L4/L5/DRC/DFM。
- 西侧 lane 块 33.3..50.2 与东侧 56.66..78.56 之间 6.4mm 空档未用（未优化，非缺陷）。
- J3-up `ll=31.5` 是否在板边/keepout 内**未验**（探针不查板边，CO-06 D4 已知缺口）——引擎落地时须与板边 keepout 一并核对。

### 8.5 32/32 解的**闭式规律**（引擎落地的直接输入；从 `..._geom.json` 提取）
西侧 32 网的 via1 实测（x, y），呈现可直接编码的规律：
| band | via1 y | via1 x |
|---|---|---|
| **up**（16 网） | **双行 y-stagger**：{≈49.36, ≈50.58}（行距 1.22 ≥ vv；两行均 ≤50.68 < dn 带 51.37） | `vx ≈ pad_x ± 0.25`；同页 P/N 相差 **0.5**（≥0.4525/≤0.525 边界），跨页前缀 ≈1.3 |
| **dn**（16 网） | ≈51.37–51.67（N）/ 52.366（P），全部 **≥51.373** | `vx ≈ pad_x − 0.3 / +0.1`；前缀 ≈1.3 |

- **band 间 y 净距 = 51.373−50.68 = 0.693 ≥ 0.525** ⇒ up/dn **可共享 x**（这正是把 24 槽降到 16 槽的机制）。
- 每 band 16 网 x 前缀 ≈1.3mm（远大于 0.525）⇒ 充裕余量；同页 P/N 的 0.5 已含 `POL_OFF 0.25`（对内 lane y 偏移 0.5）。
- ⇒ **引擎闭式构造**：up band 取 `y ∈ {pady_lo, pady_hi}` 双行（由 pad 行差决定，天然 1.22）；dn band 取 `y = pad_y`（分别为 51.673/52.366）；x 用 `pad_x + 前缀偏移`（前缀步 1.3 或 0.5 分极性），**全部落在 pair 域 v1.5 的合法窗内**。

### 8.6 ledger/状态
k2 `ff438f0`｜父仓（bump）｜四源 4/4 MATCH｜canonical W3-CN.30 `05f7bd10ab3b45b6` 未动｜引擎仍 W3-CN.30（**未改**）。

---

## 10. L3 通道分配工件（引擎闭式消费）
### 10.1 产物
`m13_v57_co11_channel_allocation.json`（rev `CO11-ALLOC.1`，sha16 **`5b82b5b2add19075`**，21KiB）：
每 (page,pol) 固化 `via1(x,y) / escape_layer / stub_layer / lane_y / landing(lx,ll) / chip_pad / conn_pad`。
生产者 `tools/p3_v57_co11_emit_allocation.py`；与已验证几何 `..._geom.json`（`ebd6acc92f3446b4`）**逐点一致**（32/32 via1 全匹配）。

### 10.2 架构一致性（为何这不是「引擎搜索」）
- 引擎既有契约：**离线域（F-13 pair/xorder、coherent_rows、r3_gaps）→ 执行器闭式消费（零搜索/零 fallback）**。
  本工件与之一致：执行器按 (page,pol) **O(1) 取用**，无运行时自由度。
- 派生方法（记录在案，供复核）：**单遍确定性**——固定键序 `(corridor,conn_ref,band,page_id)` 逆序，
  候选按 `|Δx|+|Δy|` 到 pad 的固定键序排列，**首次通过 A-CN.9 谓词即取，无回溯、无重试**。
- **诚实标注**：该派生含「候选枚举 + 首可行」语义（非纯闭式前缀）。若 PM/owner 要求派生亦须纯闭式，
  则须另立工作周期做闭式推导（§9 实验显示逐页独立闭式目标只到 31/32，残留与 corner via × SMD 列耦合）。

### 10.3 引擎落地清单（下一步，机械接线）
1. `r2_lanes`：西侧 corridor 块 `lane_y = 33.3 + k*1.1265`（东侧不变）。
2. `r3_place`：J3-up `ll=31.5`、J3-dn `ll=51.5`；`lx` 取工件 `landing[0]`。
3. stub 层：按工件 `stub_layer`（J3 下行组=In2）。
4. via1：按工件 `via1`（替代 r1_place 的帧内前缀构造）。
5. 节点发射：CO-11 拓扑（pad→F→via1→escape(In2/B)→corner→lane(In6)→drop→stub(In2/In6)→land(In2↔F)→F→conn）。
6. `clearance_metric` paths 补齐 escape 竖段（现 t2 缺项，CO-06 D2 缺口）；`same_layer_crossings` 覆盖 lane。
7. `REVISION` bump（W3-CN.34+）；A1.2 由工件（与输入序无关）保证。
8. 一次求解 → `FEASIBLE_ALL ∧ crossings=0 ∧ A-CN.9 0/0/0 ∧ skew≤0.15 ∧ wall≤120s` → G4→G7。

---

## 11. 引擎接线的上游解阻项（L2 过孔策略 ECO）
### 11.1 冲突（实测）
| 项 | 现值（冻结） | CO-11 需求 | 出处 |
|---|---|---|---|
| `SPEC.vias.high_speed.max_per_line` | **2** | bandX(**escape=In2**)=**4** / bandY(**escape=B**)=**6** via 跨距/线 | CO-09 §3 安全 hop 链 |
| `vias.high_speed_via_count` | 300（basis 实测 214） | 通道分配实测 **320**（32 线 bandX×4 + 32 线 bandY×6） | `..._channel_allocation.json` 统计 |
| validator A1.3 `max_vias_per_net` | **5**（`p3_v57_w3_constructive_validator_v2.py:345`） | **6** | 同上 |
| 引擎 `max_vias_per_line` 报表 | `4 if shape=="t2" else 2`（`:1615`） | bandX 4 / bandY 6 | 同上 |

### 11.2 ECO 附件（不动冻结原件）
`m13_v57_co11_spec_eco_annex.json`（`b859ab84bea7836b`，rev CO11-ECO.1）：机读列出上述 delta 与 apply 策略
（SPEC 版本 bump + 引擎 `FROZEN_SHA`/阈值断言同步 + validator 规则更新）。
**计数口径**：按 **via 跨距（hop）数**计；bandY 在 (vx,vy) 处为 3 段同轴跨距（F↔In2↔In6↔B），物理为叠孔/通孔。

### 11.3 结论（对监理工）
- CO-11 的**过孔策略/层角色**属 L2（CO-09 §3 已裁），但落地**必须**伴随上表 ECO（SPEC 属冻结输出，需版本 bump）。
- 因此引擎 rev bump 与 SPEC ECO **同批**执行，才能通过 A1.3/A-CN.9 与 SPEC 断言；单改引擎会被 `FROZEN_SHA` 与 `max_vias_per_line` 断言挡下。
- 下一步（同批）：应用 ECO（SPEC v-bump + validator 规则 + 引擎阈值）→ 引擎接线（§10.3）→ 一次求解 → G4→G7。

---

## 12. 【重要修正】§8 的 32/32 解含**同层真交叉**，非有效解
### 12.1 修正事由
引擎副本接线（`co11` shape）复跑时，引擎 `count_crossings`（**proper intersection** 语义）报 **4 处同层真交叉**；
而探针 `check()` 只做 vv/vt/tt 的**距离/共线**判据、**缺 intra-page 段-段真交叉检查**；本会话的独立复核器亦只做距离判据
⇒ 二者均漏检 **transversal crossing**。已修正复核器（补 proper-intersection 判定）并实测复现：**4 处**：
| 层 | 页 | 极性 | 机理 |
|---|---|---|---|
| F.Cu | PCIE_DN5/out_MCIO | P×N | §8 的 `_lx_separate` **独立移动 P/N** 的 lx，使 land 段（对方程）互叉 |
| F.Cu | PCIE_DN7/out_MCIO | P×N | 同上 |
| In6.Cu | PCIE_UP6/input | P×N | J4-L 的 **In6 stub** 横切对面极性 **In6 lane** |
| In6.Cu | PCIE_UP7/input | P×N | 同上 |

### 12.2 修正后的实测
- 探针 `check()` 已补 `cross_intra`（proper intersection）；复核器已补 `cross` 判据。
- 同一配置（`WSTEP 1.1265 / WLO 33.3 / FANY_J3 31.5,51.5 / STUB J3L`）**现为 28/32**（DN5/DN7/UP6/UP7 失败）
  ⇒ §8 的「32/32」是**放过了交叉**的伪结果。`m13_v57_co11_placement_verification.json` 现为 **FAIL（4 violations）**。
- 部分修正尝试（P/N 同步按页偏移；J4L stub 改 In2）分别降到 28/32 与 26/32 ⇒ 需**新的几何推导**（非同一配置微调）。

### 12.3 对结论的影响（诚实标注）
- `m13_v57_co11_channel_allocation.json`（CO11-ALLOC.1）**不是有效解**（含 4 同层真交叉）；不得据此进引擎/G4。
- §8/§8.5 的「存在性证明」**失效**；`same_layer_crossings=0` 尚未达成。
- 仍成立的部分：§8.2 的四要素是**必要方向**（lane 压缩 / landing 移出 / stub 层 / lx 分离），但**不充分**；
  §8.5 的 band 双行 y-stagger 规律仍是有用输入。
- 教训（防再犯）：探针/复核器判据必须含 **proper-intersection 交叉**（引擎 `count_crossings` 语义），不能只有距离判据。
- 红线：冻结四源 4/4 MATCH；canonical `05f7bd10ab3b45b6` 未动；引擎未改；无 sign-off。

---

## 13. 交叉免几何推导（新周期）：(a) 已修 → 30/32 有效；(b) connector In2 拥塞仍阻 2 页
### 13.1 (a) land 互叉已消除（§12 修正项 a）
- 改 `_lx_separate` 为**按页整体偏移**（P/N 同 δ），δ 网格 **0.6mm**（落另一中缝列，页间净距 ≥0.525）⇒
  P/N land 段保持 pad 相对次序 ⇒ **不再互叉**。
- 结果：同配置 **30/32**（原 28/32），失败仅 **UP6/UP7**；几何产物 `m13_v57_co13_perpage_lx_probe_fan_rev.json`
  （`debc3da294d4c7a0`）。
- **非执行者复核（含 proper-intersection 全对全）**：`m13_v57_co13_placement_verification.json`
  **0 违规 PASS**（304 via / 300 段）⇒ 这 30 页**既净距合规、又无同层交叉**。

### 13.2 (b) 剩余 2 页（UP6/UP7）＝ **J4-L In6 stub × 对面极性 In6 lane** 交叉
- 机理：J4-L 的 `ll=65.0` 在 lane 之上，stub 竖直上溯必穿对面极性 lane（同 In6）⇒ 需要 **stub 改 In2**。
- 但 J4-L 改 In2 后，connector 侧 In2 拥塞：按压缩 lane 块，各 row 组的 In2 stub y 区间为
  J3U `[31.5,36.7]`、J3L `[37.8,51.5]`、J4U `[42.3,60.2]`、J4L `[46.8,65.0]`；
  重叠团 **{J3L,J4U,J4L} = 12 页 × 2 pol = 24 项**，而 connector 中缝列仅 **~19**（0.6 pitch），
  且需 ≥0.525 分离 ⇒ **x 维不足**（实测 J4L→In2 掉到 26–28/32）。
- L2 候选（下一周期，需新几何而非微调）：
  1. **非竖直 stub**（斜段/折线）把 In2 竖段移到不同 x 列，降低阶梯团；
  2. **landing 方案重派生**（如 J4 组改用 lane 块**下方** ll + In2 stub，需与 J3 组协调）；
  3. **J4 组 lane 降带**（若能把 J4 组 lane 压到 J3 组同区，stub 变短、团收缩）；
  4. 或对 2 页（UP6/UP7）做**局部拓扑特例**（L2 过孔策略允许逐页混合，CO-09 §4-7）。

### 13.3 结论 / 红线
- 现状：**30/32 有效**（crossing-free + clearance-clean，经修正判据复核）；2 页待 (b) 的新几何。
- 冻结四源 4/4 MATCH；canonical `05f7bd10ab3b45b6` 未动；引擎未改；无 sign-off。
- 判据纪律（§12 教训）已固化：探针 `cross_intra` + 复核器 `cross`（proper intersection）。

---

## 14. (b) 收敛实验：landing 带重派生 + stub 层 + lx δ 扩展（最佳仍 30/32）
### 14.1 实测矩阵（全部经修正复核器；探针默认行为不变）
| 配置 | 落位 | 失败页 | 复核 |
|---|---|---|---|
| FANY_J3 `31.5,51.5` + STUB `J3L`（co13 基线） | **30/32** | UP6, UP7 | PASS |
| FANY_J3 `31.5,44.5` + STUB `all` | **30/32** | DN1, UP6 | PASS（产物 `142beea07e4c9609`）|
| FANY_J3 `31.5,42.0` / `43.0` / `45.0` + STUB `all` | 26–29/32 | DN0–3 等 | — |
| FANY_J3 `31.5,31.5` + STUB `all`/`J3L,J4U,J4L` | 26/32 | DN0–3, UP4, UP6 | — |
| J4L→In2（STUB `J3L,J4L`） | 28/32 | DN1, UP4/5/7 | — |
| lx δ 网格扩至 ±3.6（0.6 步） | 基线不变 | — | — |

### 14.2 两类残余的定量瓶颈
1. **connector 侧 In2 stub 阶梯团**：把 J4L 改 In2 后，In2 stub 的 y 区间
   J3U`[31.5,36.7]`/J3L`[37.8,ll_L]`/J4U`[42.3,ll_U]`/J4L`[46.8,65.0]`；
   需 `|Δx|≥0.525` 的互斥团大小随 `ll_L/ll_U` 变化（最小 ≈16，最大 24），而 connector 中缝列 ≈18
   ⇒ **处于容量边界**；`ll_L` 越界（<42.3）可解耦 J3L×J4，但会与 J3U 的 breakout 在 F.Cu 上互叉（实测 26/32）。
2. **chip 侧 via 间距**：残余页出现 `vv_intra` 0.42–0.52（同页 P/N via1 或 corner 过近）与
   `vt2_placed` 0.21（F.Cu 逃逸段 × 邻页 via）⇒ pair 域**逐页取最近行**不足以避开邻页已落位几何。

### 14.3 结论 / 下一周期
- (a) 已闭环（30/32，crossing-free + clearance-clean，复核 PASS）。
- (b) 需**闭合的列分配器**：以 connector 中缝列为色板、In2 stub/land 的 y 区间为区间图做**确定性贪心着色**
  （引擎 `color_groups` 同范式），并同时纳入 chip 侧 pair 行选择（含 corner/逃逸段避让）——
  二者必须**联立**（当前逐页独立选行是残留的真因）。属新几何推导周期，非微调。
- 红线：冻结四源 4/4 MATCH；canonical `05f7bd10ab3b45b6` 未动；引擎未改；无 sign-off。
