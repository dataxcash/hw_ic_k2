# m13 v57 — **L1 结构可行性预检 v2**（整改通知 #02：定层纠正）

> 2026-09-11｜作者：ARCHER（执行侧）｜层级：**L1（整体方案结构可行性预检）**，非 L3 施工
> 依据：`_shared/docs/LAYOUT_CONSTITUTION.md` Ch.3 §5 + Ch.9 第 2/3 行 + 整改通知 #02
> 机器件：`m13_v57_l1_struct_preflight_v2.json`（rev **L1-PF.2**，producer `k2/tools/p3_v57_l1_struct_preflight_v2.py`）
> **本件不修改冻结四源、不改 canonical W3-CN.25、不动层叠**；仅为 L1/L2 变更单提供结构预检证据。

## 0. 定位更正（#02）
W3(L3) 在完整净距套件下 R1 29/32 的瓶颈 = **连接器/chip fan-out 逃逸**（ledger [76]/[77]）。
依宪法 Ch.3 §2「下层发现问题无权私下妥协，必须走变更单升级对应上层」+ Ch.9「走廊放不下/逃逸不可达 =
L2 否决性事实 + 暴露 L1 结构预检缺失」——**本问题定层 = L1/L2 结构方案，非 L3 施工补丁**；
#01 的「owner 加层与否二选一」表述**作废**（已由本件取代）。

## 1. L1 结构预检（四项；全部 O(n) 闭式，零搜索）
数据源 = 冻结 manifest 实测 pad 坐标 + 冻结 SPEC 参数（四源 SHA 见 JSON `inputs_sha`）。

### P1 走廊宏观闭合 ✓（唯一闭合项）
| 走廊 | x 净跨 | 对/带 | 对中心距 | 单带需求 | 可用翼带 |
|---|---|---|---|---|---|
| EAST_CHIP_TO_J2 | 27.40mm | 8 | 1.46mm | **10.805mm** | N 16.2 / S 20.8mm |
| WEST_MCIO_TO_CHIP | 17.30mm | 8 | 1.46mm | **10.805mm** | N 16.2 / S 20.8mm |
- 单带 10.805mm < min(16.2, 20.8) ⇒ **横截闭合**；x 净跨 > 逃逸过渡深度(~10-12mm) ⇒ **闭合**。
- 与 v20 预检口径一致（v20 §2 亦得 10.80mm）。

### P2 焊盘墙穿透 — **全部不可穿**（P2 结论为"墙不可穿"，非闭合判据）
线道需求 `lane_needed = w + 2·clr = 0.205 + 2×0.175 = 0.555mm`。
| 墙 | pad 中心距 | pad Ø | 行内 pad 间隙 | 可穿? |
|---|---|---|---|---|
| chip 逃逸区(64 pad) | 0.6003 | 0.305 | **0.2953** | ✗ |
| 连接器 J2(32p) | 0.600 | 0.305 | **0.295** | ✗ |
| 连接器 J3(18p) | 0.600 | 0.305 | **0.295** | ✗ |
| 连接器 J4(18p) | 0.600 | 0.305 | **0.295** | ✗ |
- **可穿墙数 = 0**：行内 0.295mm < 0.555mm（缺口仅够 0.53 道）⇒ **所有高速 pad 一律需层转移（via）**，
  不存在"行内直接穿越"的布线可能。

### P3 pin 逃逸可达性 — **6L 内部信号层资源不足**
- 有效信号 pad：chip 64 + 连接器 68；数据对 32（东 16 + 西 16）。
- P2 ⇒ 高速 pad 一律需 via；**6L 内部信号层仅 1 个（In2.Cu）**承接全部逃逸 + 穿越 + REFCLK + 低速。
- In2 翼带容量 = (16.2+20.8)/1.46 ≈ **25.3 对**；而逃逸/穿越 + REFCLK 需求已达该层上限 ⇒ 无余量。
- 8L 才有第二内部信号层（In2 + In6）+ 额外 GND ⇒ 才有多层分配自由度。
- **实证**：W3-FCC.1 在 6L/3 信号层 + 完整净距套件下 R1 29/32（P8：净距关 32/32 ⇒ 放宽/域扩/序均无效）。

### P4 强条内嵌核查（**#02 根因：L2 冻结包络带缺陷**）
| 强条 | 是否进 L2 包络 | 证据 |
|---|---|---|
| 完整净距套件 0.38/0.4525/0.525 | **否** | `L2_STRUCTURE_v2.0.md` 无此三值；L5 才暴露（track↔track / via↔track / 孔铜/板边/阻焊） |
| 对内等长 skew ≤0.15 | **仅文本声明，无机检** | L2 §38 写「对内等长 <0.15mm」，但 L3 口径未含 → L5 skew **24.476mm** |
- ⇒ v20「6L 结构预检 闭合 ✓」是在**不含完整净距 + 不含机检等长**的口径下作出的 ⇒ **该结论不成立**。
- 这正是宪法序言「655 条制造错误在布线完成后才发现」的重演：**强条未在设计阶段内嵌**。

## 2. 附加证据：L1/L2 冻结包络**内部不一致**（8L→6L 未再推导）
| 证据 | 位置 | 冲突 |
|---|---|---|
| `stackup` = F/G/S/G/P/B（**6L**） | SPEC `/stackup` | 层叠=6L |
| `j2_escape_topology.rule` = 「**2026-08-19 8 层定案**…UP_OUT 16 网经 In2 单内层走廊，不再走 B.Cu」；`outer_basis`=「**8 层**：In2 独立走廊容纳全部 UP_OUT，B.Cu 释放给低速」 | SPEC `/constraints` | **拓扑按 8L 冻结** |
| `gnd_stitch_via.rule` = 「…（**2026-08-19 8 层定案**）」 | SPEC `/pd` | **过孔策略按 8L 冻结** |
| `pd.gnd_planes` = `["In1.Cu","In3.Cu","**In5.Cu**"]` | SPEC `/pd` | **引用了 8L 层 In5**（6L 无 In5） |
| `in6_usage` = 「removed: 8L In6.Cu semantics（6L…In2 only internal signal layer）」 | SPEC `/layer_plan` | 仅文档记录删除，**拓扑/平面语义未随 6L 再推导** |
- ⇒ **L1 拓扑（8L）与 L2 叠层（6L）冻结在互不一致状态**；G4/G5/G6 在"旧口径"下放行，G7 真制造签核才暴露。

## 3. 结论 / 升级
- **verdict = PREFLIGHT_FAIL**（P1 ✓；P2 全墙不可穿；P3 6L 单内部信号层资源不足；P4 强条未内嵌）。
- 依宪法 Ch.3 §5 + Ch.9 + `L2_STRUCTURE_v2.0.md`「8L 重入 ECN 触发条款」（L126-137；`L1_TOPOLOGY_v2.0.md` L14/L24/L114 引用）之触发 1「L3 逃逸逐段布线实证不可路由 + via 预算超支」、触发 2「In2 穿越 + stub 实测超载」）⇒ **走变更单 CO-02 回 L2/L1 重开层数/结构裁决**。
- **禁止**在 L3 打补丁（加层/放宽/换构造）；**禁止**据本件宣称全局不可行（本件为**构造域/包络级**证据，非全局证明）。
- 处置：见 `m13_v57_change_order_CO-02.md` + `m13_v57_l2_structural_bid_v1.md`。

## 4. 可复现
```bash
cd /home/fila/jqdDev_2025/ic_hw/k2
python3 tools/p3_v57_l1_struct_preflight_v2.py --out /tmp/opencode/l1_pf_v2.json
# verdict=PREFLIGHT_FAIL; P1 closure=true; P2 penetrable_wall_count=0
# P4 full_clearance_suite_in_L2=false; length_match_machine_gate_in_L2=false
```
指纹：四源 `0bd52ed48e720b8c / a8ef3ea8ecff99d7 / f6273de613f43d05 / 0a459839e15960b8`（4/4 MATCH）；
canonical `m13_v57_w3_joint_assignment.json` = `W3-CN.25 / FEASIBLE_ALL`（未改）。
