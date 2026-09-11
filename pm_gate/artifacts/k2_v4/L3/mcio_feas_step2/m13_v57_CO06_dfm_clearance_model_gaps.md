# CO-06 — G7(DFM) 阻塞：W3 净距模型缺口（跨层过孔桶 / 自对 / 连接器孔 / 板边 / 同网钻孔 / REFCLK）

> 2026-09-11｜发起：ARCHER（L3 施工方）｜性质：**变更单**（门禁发现下层无权私下妥协 → 修模型输入）
> ｜触发：O4 收口（CO-05 v7，引擎 W3-CN.30）后 G7/L5 重跑，`DFM new=426`（shop 规则口径）
> ｜目标门：G7 `skew ≤ 0.15` **已 PASS(0.0574)** ∧ `DFM new = 0` **未达**。

## 1. 口径修正（先做，避免伪阳性）
L5 初跑 `DFM new=1452` 中约 1026 条为**过时 6L 工程档**（`k2_v4_8L.l4.kicad_pro` 含 min_via 0.5/drill 0.3/annular 0.1/edge 0.5、仅 Default netclass）。
已建 **`k2_v4_8L.kicad_pro`**（规则/网络类取自 `k2_v4.kicad_pro`：min_via 0.35、drill 0.2、annular 0.075、edge 0.3、
Default 0.1 / LOW_SPEED 0.1 / **PCIe85** 0.175 + diff_gap 0.175 + width 0.205 / POWER 0.2），`p3_v57_l5_signoff.py` 指向之。
⇒ 真实新违例 **426**（其余 73 为冻结板既有 lib/silk 警告，非新）。

## 2. 缺陷分类（均有 kicad-cli DRC 实测样本）
| # | 类 | 数 | 样本 | 模型缺口 |
|---|---|---|---|---|
| D1 | **跨层过孔桶短路** | shorting 108（+部分 clearance）| 盲孔 `PCIE_UP_OUT1_P_J2` F↔In6 @(85.85,55.13) 与 `PCIE_UP7_P` In2 走线短路 | W3 仅把 via 视作**端点层**障碍；through/blind via 的桶**穿透其跨距内所有层**。F↔B/F↔In6/In2↔B/In2↔In6 分别穿透 In6/In2 等 |
| D2 | **页内 P/N via↔track** | clearance 176 | 盲孔 `PCIE_DN1_P` In2↔B @(86.0,69.61) 与 `PCIE_DN1_N` B.Cu 走线 0.1025mm(<0.175) | `_mk_index(_exclude=_pid)` 排除本页 ⇒ 页内跨极性 via↔track **从不校核**（`_va` 只校 via↔via）|
| D3 | **连接器焊盘孔/阻焊** | hole_clearance 24 + solder_mask_bridge 103 | 过孔 `PCIE_DN_OUT4_P_MCIO` @(54.2,61.05) vs `J4.A1[GND]` 孔 @(54.1,61.45)（孔距 0）| 障碍场仅含 chip pad（`_PADALL`）；**J2/J3/J4 连接器通孔焊盘不在障碍索引** |
| D4 | **板边净距** | copper_edge_clearance 10 | `PCIE_UP3_N` In2 @(88.8,33.11) vs Edge.Cuts y=33.0（0.0075）| lane 蛇形可越过 `LANE_LO−A`（33.3−0.34=32.96 < 33.0 板边）；缺 edge keepout / 蛇形侧向选择 |
| D5 | **同网钻孔间距** | hole_to_hole 1 | `PCIE_UP4_N` via1 F↔In6 @(89.55,50.63) 与 corner In2↔In6 @(89.55,51.01)（孔边距 0.18<0.25）| 同极性/同网被 `_va` 豁免 0.525，但**钻孔—钻孔**最小值(0.25 边距⇒中心≥0.45)对同网仍成立；POL_OFF=0.19(中心 0.38) 违规 |
| D6 | **REFCLK 交叉** | tracks_crossing 4 | `PCIE_REFCLK1_P` 与 `PCIE_REFCLK1_N` 于 F.Cu 相交；另有 DN*/out_MCIO F.Cu fan 与 REFCLK 相交 | A-CN.4/R1.5 平面扇只覆盖 data 页；**REFCLK P/N 及与 data fan 的同层交叉未纳入门禁** |

## 3. 处置路线（裁定）
- **D2/D3/D4/D5/D6：L3 模型能力补齐**（我方权限）——W3 构造器需：
  (a) 每个 via 作为**跨距内所有层**的圆障碍（点/线段谓词按跨距层集合）；
  (b) 校核**本页跨极性** via↔track；
  (c) 障碍场纳入 **J2/J3/J4 通孔焊盘**（孔 + 铜）；
  (d) lane 加 **板边 keepout**，蛇形方向选择避边；
  (e) 同网 via 也校 `hole_to_hole`（中心 ≥0.45 或改 POL_OFF/落位）；
  (f) REFCLK 交叉纳入 A-CN.4 等价门禁。
  完成后 W3 须重解一次（确定性），重跑 G4→G5→G6→G7。
- **D1 = L2 结构（ARCHER 自裁，见 CO-08；非 owner）**：D1 的根因是 **LID.1 把 up 带竖段放 In6，而 dn 带 via1 为 through(F↔B) 穿透 In6**。
  层集合本身使两条带互相穿透。**须 L2 裁决**其一：
  (1) 交替换层（up→B.Cu / dn→In6）并把 through via 改为 buried（需确认回钻/钻互斥可行性）；或
  (2) 维持 LID.1，但把 through via 的**落位**约束为远离对带 In6 走线（把 D1 退化为纯 L3 避让）；
  或 (3) 修正带竖段层，使带竖段不落在任何 through via 的跨距层。
  **本单不预设 (1)/(2)/(3)**；请 owner/L2 就"过孔策略 × 层分配"给一条裁定，随后 L3 一次实现。

## 4. 证据 / 指纹
- DRC（shop 口径，`k2_v4_8L.kicad_pro`）：`/tmp/o4study/drc_aligned.json`；记录 `m13_v57_l5_dfm_dft_record.json` sha16 `cd20e835118f4469`
- 板 `k2_v4_8L.l4.kicad_pcb` sha16 `225fccb23c5b1b5f`（L4-A..E 全 PASS，256 via）
- 图纸 W3-CN.30 sha16 `05f7bd10ab3b45b6`
- 冻结四源未改；**G7 保持 OPEN**（DFM new=426）。

---

## 5. D1 实测（L3 已证不可闭合 ⇒ L2 结构裁决）

**实验（单次、确定性）**：把「via 桶 = 其跨距内全部信号层障碍」写入 W3 构造器（W3-CN.31probe，副修：经 `_sig_span` 计算
F↔In2/In2↔In6/In6↔B/F↔B/F↔In6/In2↔B 的信号层覆盖；候选 via 点按跨距层全集校核，并补 drop/land 顶点），重解一次：

- **verdict = UPSTREAM_CHANGE_REQUEST**；R1 放置 **31/32**（`PCIE_UP1/input` 无可行 pair_row）。
- 证书：`R1_chip_escape_column:per_frame_hybrid`（UP1/input 无行）、`x_lattice_snap_mutual_clearance`
  （如 `DN1/input.N–UP1/out_J2.N 0.52047`）、`complete_clearance_suite`（tt 18 / vt 34 / vv 11）、`frame_monotone_fan`（3）。
- 结论：在 **LID.1（lanes=In2；dn escape/stub=B.Cu；up escape/stub=In6.Cu）** 下，
  过孔必然穿透信号层（F↔B 穿透 In2+In6；F↔In6 穿透 In2；In2↔B 穿透 In6），而 In2 承载全部 32 条 lane、
  In6 承载 up 竖段 ⇒ **构造域内不可闭合**（非全局不可能性证明）。

**物理根因**：信号层物理序 = `F(1) → In2(4) → In6(7) → B(8)`（In1/In3/In4/In5 为 GND/PWR）。
从 F.Cu 出发**不穿透其它信号层即可达的内层只有 In2**（其间隔仅 In1 平面）；In6/B 均在 In2 之后。
故「每线 ≤2 过孔（SPEC: 单次换层 F→In2→F）」与「4 信号层分流避交叉」在本叠层下**互斥**。

**单层可行性旁证**：把现图纸各网折线投影到 In2 单层计数 → 1009 真交叉（说明现折线假设分层，
不能直接降为单层；单层方案须**重新派生 river**，不能投影）。

## 6. L2 裁定（ARCHER，2026-09-11）与所需决议

- **裁定**：逃逸/落列拓扑只允许**信号层相邻 hop**的过孔：`F↔In2`、`In2↔In6`、`In6↔B`；
  **禁用** `F↔In6 / F↔B / In2↔B`（穿透信号层）。
- 满足该裁定的两条路线：
  - **(a) 单内层 In2 river（2 via/线，符合 SPEC）**：芯片 F→In2 →escape+lane+stub 全在 In2→In2→F conn。
    需**重新派生** 32 网的平面 river（现引擎 frame/lane 序已按 row 对齐，可作初值）。
  - **(b) 双内层 In2↔In6 链（4 via/线）**：`F↔In2 → escape(In2) → In2↔In6 → lane(In6) → In6↔In2 → stub(In2) → In2↔F`。
    全部 hop 安全，但**违反 SPEC `high_speed.max_per_line=2`** ⇒ 需 **owner 修订 SPEC**。
- **决议**：优先执行 **(a)**（L2 我方权限）。若 (a) 的 river 重派生证明不可行（序不兼容），
  或因 (b)/叠层调整需改 **反钻策略 / 叠层信号层次序 / 每线过孔数** ⇒ **触 L1，请 owner 裁决**。

> 现状：**G7 阻塞于 (a)/(b) 决议**；本会话已把 D1 从"猜测"变为"可复现的构造不可行证书 + 物理根因"。
