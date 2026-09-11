> **已被 CO-08 取代**：本文件 §6/"结论(owner)" 的 owner 升级请求作废（叠层重排/过孔预算 = L2）。

# CO-07 — L2 裁定：8L 层/过孔策略（逃逸拓扑仅允许信号层相邻 hop）

> 2026-09-11｜ARCHER（L2 裁决权内）｜依据：`m13_v57_CO06_dfm_clearance_model_gaps.md` §5 的构造不可行证书

## 裁定
信号层物理序 `F(1)–In2(4)–In6(7)–B(8)`（In1/In3/In4/In5 为 GND/P3V3）下：
1. **允许**过孔：`F↔In2`、`In2↔In6`、`In6↔B`（不穿透任何**其它**信号层）。
2. **禁止**过孔：`F↔In6`、`F↔B`、`In2↔B`（穿透 In2 或 In6 信号层 ⇒ 与 foreign 铜短路）。
3. 由此，**每线 ≤2 过孔（SPEC）⇒ 只能用单一内层 In2**（F→In2→F）。
   W3 的 escape/lane/stub 须重新派生为 **In2 单层平面 river**；R1/R2 的 frame/lane 行序可作为初值。
4. 若单层 river 不可行、或需改每线过孔数 / 信号层次序 / 反钻 ⇒ 属 **L1**，上抛 owner（叠层/拓扑）。

## 影响文件（下一工作周期）
- `tools/p3_v57_w3_constructive.py`：R1.5/R2/R3 拓扑（escape/stub 层、corner/drop via 语义）、`_mk_index`/`_vt_*` 谓词。
- `p3_v57_w3_constructive_validator_v2.py`：合法层对/重导契约同步。
- SPEC `high_speed.max_per_line` 若走 (b) 需 owner 修订（冻结源 → 只走变更单）。
- 冻结四源：**均不改**（走新版本工件 + 变更单）。

## 实测 A：直接层交换（lane↔escape/stub）——**不可行**（单次，已回退）
把 `escape/stub` 由 band 层（B/In6）改为 **In2**、`lane` 由 In2 改为 **In6**（过孔仅 F↔In2、In2↔In6），重解：
- `verdict=UPSTREAM_CHANGE_REQUEST`；`same_layer_crossings=18`（r1_5=2）；`tt 58 / vt 142 / vv 11`；`n_vias=248`。
- 根因：**逃逸竖段密度**。64 条 escape 集中在芯片侧 x≈83–93（约 10mm），同层 x 间距需 ≥0.38 ⇒ 约 24mm，**物理放不下**；
  两带 escape 必须分层才不重叠。故「单层承载 escape+lane」不成立。
- 结论：本层交换**不是**可行解；已回退（引擎恢复 W3-CN.30 `05f7bd10`，探针产物仅 /tmp）。

## 结论：需**平面 river 重派生**（L2 工作周期）或 owner 放宽预算
安全 hop 限制 + 逃逸密度 ⇒ 必须重派生（不是改几个常量）：
1. **候选一（首选，符合 SPEC F→In2→F，2 via/线）**：lane+stub 在 **In2**；escape 在 **F.Cu**（芯片 pad 直接 F.Cu 拉线到 lane 入口，`via1=F↔In2` 落在 lane 上；`land=In2↔F`）。
   需把 R1 的**平面扇（F.Cu breakout 不交叉）**扩到"芯片 pad→lane 入口"的长 escape，并同时管住 conn 侧 breakout。可行性须以 river 平面性判据证明。
2. **候选二（4 via/线，需 owner 改 SPEC `max_per_line`）**：dn=escape/stub In2 + lane In6；up=escape In6 + lane/stub In2（up 芯片侧多一次 F↔In2→In2↔In6）。
   代价：In2 上混合 escape/lane/stub 需排 river；每线 4 via（现设计亦 4 via，故非增量）。
3. 若两者均不可行 ⇒ 触 **L1**（信号层次序/叠层间距/反钻）→ owner。

> 说明：现设计**已是 4 via/线**，故候选一才是回到 SPEC"每线 ≤2"的唯一路线；候选二属"承认现状 + 修安全 hop"。

## 实测 B：escape 密度预检（只读，决定性）→ **触 L1，上抛 owner**
证据：`m13_v57_co07b_escape_density_precheck.json`（基于 canonical W3-CN.30 只读）。

| 组 | n | escape y-overlap clique | 需 x-span | 可用 x-span | 判定 |
|---|---|---|---|---|---|
| EAST/dn | 16 | 16 | 6.08mm | 8.8mm | OK（单带单层）|
| EAST/up | 16 | 16 | 6.08mm | 9.45mm | OK |
| WEST/dn | 16 | 16 | 6.08mm | 8.8mm | OK |
| WEST/up | 16 | 13 | 4.94mm | 10.8mm | OK |
| **两带合并到一层** | 32 | **32** | **12.16mm** | ≤9.45mm | **不可行** |

**推论链（安全 hop 下）**：
1. 从 F.Cu 出发的安全 hop 只有 `F↔In2` ⇒ escape 竖段层**只能**是 In2 ⇒ 两带 escape 必争 In2 ⇒ 需 12.16mm > 9.45mm ⇒ **C1 否证**。
2. escape 与 lane 同层必交叉（escape=芯片侧竖段 x≈84–93，lane=水平 y=lane_y 跨同 x 范围）⇒ escape/lane 必须分层。
3. 于是安全 hop 需：escape 两层 (In2,In6) + lane 第三层 (B)；而 lane→In2 需 `In2↔In6↔B` 多跳 ⇒ **每线 4~6 过孔** > SPEC `max_per_line=2`。

**结论（原误列为 owner/L1 — 已由 CO-08 更正为 L2 自裁）**：现 8L 叠层把信号层用平面隔开，与 SPEC「每线 ≤2 过孔」在本板密度下互斥。
可选项（请 owner 择一）：
- **(A) 叠层重排（L1）**：把信号层相邻化（如 F/In2/In6/B 连续，平面置于外侧），使 `In2↔In6`、`In6↔B` 为**相邻** hop；
  则 escape 可安全落 In6/B，两带分层且 lane 独立一层 ⇒ 2~4 via/线可达。
- **(B) 改 SPEC `high_speed.max_per_line`（2→4~6）**：保留现叠层，接受多跳安全 hop（每线 4~6 via）。
- **(C) 减层/改拓扑（L1）**：减少需要内层逃逸的信号数（如并行走廊/换 pin 映射）——触球重映射。
