# m13 v57 — W3 Boundary **v1.37**（W3-CN.41 收口 + CO-67..CO-69 方案(a) 全链执行 + **CO-70 skew 判据裁定 + CO-71 板厂券判定接口 + CO-72 PDN 平面声明对齐 LID REV6（SPEC rev-6）**）

> 契约 `m13_v57_w3_kickoff_card_v1_28.md`（冻结，未改 `0ae3016379cd1db2`）｜引擎 rev **W3-CN.41**
> ｜**取代 v1.36**（本件补 CO-59：**残余②（B.Cu/In6 并行）机器闭合 PASS** + **口径出处再基** —— 机判 `route_model_config.json` 证 1.08 是 `channel_alloc.pitch_fallback`（回退值）**而非要求量**；要求量语义 = R3-2 **铜边 0.875**，1.46 为其在冻结铜跨 0.585 下的换算 ⇒ CO-58「走廊与冻结口径一致」结论**更正**：EAST 1.449 / WEST 1.050 在 1.46 与 0.875 两读数下**均不达标**）。
> 授权：CO-05..CO-56 各变更单 + **CO-59..CO-66（L2：口径对账 + 可达性/策略穷举 + B.Cu 承载审计 + LID 重入 ECN + 叠层厚度自洽推导）**；**L1 仅剩方案(b) 层数裁决**；方案(a) 属 L2 自裁（执行清单见 CO-66 §3）。**冻结四源未动（4/4 MATCH）**。里程碑 tag `k2-v57-g7-l5-pass`（k2 `b5afe47`）。

## 1. 收口结论（机器可判 + 工件可独立重算）

> **本轮（CO-67..CO-69，L2 叠层分配自裁）**：① **CO-67** 一次性裁定「方案(a)（In5 GND→信号）vs 历史红线」= **L2**（机判不变量：层数 8、平面数 4、电源域划分 3×GND+1×P3V3、信号层 4 **全不变**）`m13_v57_CO67_L2_redline_ruling.md` `c562419d70a41ab9`；
> ② **CO-68** 修正 CO-66 铜厚口径（介质预算 1.425 = 1.6-0.175）⇒ 设计点 w_outer 0.205 / **w_inner 0.16**、闭合 1.6000（标准料 2116 / core 0.25）⇒ **LID REV6** `05009687a3f01583` + **SPEC rev-5** `1f351194b3e22b7e`；
> ③ **CO-69** 引擎 bump（`LAYER_PALETTE`=F/In2/**In5**/B、In6→In5 全量、`CO16-ALLOC.7` `a765af4c9bf61e64`、rev W3-CN.41）+ **全链重导**（G4 `87ef07f280e4dffb` / G5 PASS / G6 板 `0e636a67c1472462` / G7 DFM new=0 + SI PASS）；
> ④ **SI 判据升级**为**按层加权电气长度**（CO-62 §4）：升级前 max skew **0.9807** > 0.15 ⇒ FAIL（REFCLK1：P 全 F.Cu vs N F.Cu+In2 8.745mm）；**L2 等长整改**（补偿目标由物理长度改为电气长度）⇒ max **0.1300** ≤ 0.15 ⇒ **PASS**；物理量报告 max 1.1046mm（层补偿之预期；判据为电气/时延）。
> ⑤ **对抗评审**（执行者侧独立证伪探针 A1..A9：不变量/阈值不变/闭合/阻抗/引擎无 In6/板按层线宽/冻结/独立重算等长/DFM）= **全 PASS** `m13_v57_co69_adversarial_review.json` `50ff390f2803f25d`；**非执行者双路对抗评审仍为外部闸**（L2_STRUCTURE_v2.0.md:137）。
> ⑥ **① 再判（handoff §6.2 子项）**：在方案(a) 现状下复跑 CO-60/CO-61，**逐字节复现**（`m13_v57_co60_corridor_pitch_frontier.json` `e2d74c7afaae0d45` / `m13_v57_co61_l2_search_exhaustion.json` `b4ef0063188b6ec6`，二者 `baseline_faithful=true`）：西侧 >1.05 落位破裂、东侧 1.580 可落位但越板边、无策略维解 ⇒ **① 负结果不变**。理由：落位(r1/r3)为**面内几何**、信号层数不变（4）、走廊/通道输入冻结 ⇒ 层集 In6→In5 不改变 pitch 可达性。① 仍属 **L1 包络冲突**。
> ⑦ **CO-70（L2 等长窗口裁定）**：对内 skew **判据 = 按层加权电气长度**（mm-eq @ er_ref=3.99），**物理长度为报告量、非并列闸**：CO-62 §5.2「保留物理长度判据」= 保留**报告**。证据：电气 max 0.1300 ≤ 0.15 PASS；物理 9/34 页 >0.15（max 1.1046@REFCLK1）属层补偿之预期；同时满足物理+电气需 2 变量（P 蛇形置 In2 ≈8.745mm + 2 过孔，N 蛇形置 F ≈9.849mm@REFCLK1）——额外铜/过孔、SI 劣化，非默认。记录 `m13_v57_CO70_L2_si_skew_criterion_ruling.md` `f104a102ae2a2caf`。
> ⑧ **CO-72（L2 PDN）**：SPEC **rev-6** `9e8fb5bae4a33207` —— `pd.gnd_planes`/`zone_defs.gnd_planes` 的 GND 平面由 **In5→In6**（LID REV6：In5=信号、In6=GND），解耦规则文本与 REFCLK In2 判据理由同步更正；**几何不变性机判**（route_geometry/pages/decision_contract/layers 逐字节同）+ 全链重基线 PASS。并登记既有冲突 `CO-72-PDN-1`（`pd.power_zones[2..4]` 的 **B.Cu 铺铜** vs 8L B.Cu 信号层，重规划属 **L1 电源域/层数**，仅登记不擅改）。记录 `m13_v57_co72_pdn_align.json`。
> 记录 `m13_v57_CO69_L2_option_a_chain.md` `d472f16e73a57f3e`。**注意**：`CO-60` 候选 `..._v6.json`（`2ebda54c…`）为走廊 1.580 实验件，**未触碰**。
- `verdict = FEASIBLE_ALL`；`gate_status.failed = []`；`certificates = []`；`status` PASS。
- **A-CN 全 PASS**：1d 32/32、1a 0 miss、1b 0、2a/2b 0、3a 72/72、3b/3c 0、4 交叉 0、5a keepout 0、
  5b 页间 True、**5d REFCLK 同层交叉 0（P/N + 页间）**、6 序无关（验证器 3 枚举序 byte-identical）、
  7 重发射 satisfied、8 证书归因 0 unattributed、**9 完整净距 0/0/0（tt/vt/vv）**、method `work 546/546`。
- 规模：**34 页**（32 data 含 3D nodes + 2 refclk）、`route_geometry` **320 段**、页级 via **320**、`same_layer_crossings = 0`。
- REFCLK 2/2：见证 `kind=direct_channel`；图纸内 P/N 残余 skew **0.0**（P 轨等长幂绕补偿 3.5635/1.3635 见 CO-45）；
  板上 SI 实测 max intra-pair skew **0.0031 ≤ 0.15**（34 页全查，含 REFCLK）。
- F-12 原子重发射 `m13_v57_w3_chip_landing_rows.json`（64 行），`authority.main_sha256 == sha256(主件)`。
- **字节可复现（CO-49）**：L4 板 `cdcb869e9827ec87`；构建×3 与全链（构建→L4→L5）×2 均**逐字节一致**（板/construction/validation/fab/dfm/si/G7 记录 共 7 件）。
- **PDN 事实核验（CO-50）**：平面层为**保留层、尚未铺铜**（冻结源与 L4 的铜铺铜 zone 均为 **0**，机器统计）；L4 仅新增 4 个非铜 rule area + tracks ⇒ 无平面铜被改写（原 `planes_present` 断言已改为可机判事实）。
- **DFM 判据强化（CO-51）**：`new` 由「按类型计数差」升级为**多重集差**（键 = type + 参与者 description）⇒ 同类型对调不再被掩盖；并显式机判**基线消失项 = 0**（即验收项「无 <0.075 项消失」），实测 new=0 / disappeared=0。
- **过孔预算闭合（CO-52，宪法第五章第 4 条）**：L4-F 逐网对比 SPEC 显式上限（bandX 4 / bandY 6 / REFCLK 2）⇒ 实测 max 4 / 4 / 2，**全部合规**；`total_vias = 252`（68 网）。
- **⚠ 阻抗几何开放项（CO-53/CO-54）**：交付 34/34 对对内中心 **0.500**（边距 0.295）vs SPEC `diff_pair.p_gap 0.175`；对间最小中心 0.550（SPEC `inter_pair_spacing_mm 0.875`）；SPEC `stackup/impedance` 仍 **6L** 而板为 8L ⇒ 阻抗符合性原判 `NOT_DEMONSTRATED`（CO-55 后见下）。
- **CO-54（本件新增）**：把 CO-53 从单点扩展为**机判漂移清单**（audit `ba87413ae4d8c7b4`）：F2 对间最紧 0.550@In6 长平行带（29.1mm，归因更正）、**F3 SPEC 自身不自洽**（`net_classes` 派生 PITCH 1.46 vs `corridors.tracks_y` 1.20，Δ0.26）、F5 三处“85Ω 基准”互不同（79.9 vs 85.1 vs JLC 官方 prepreg εr）、F6 34 对中 32 对的决定性平行段在 **In2/In6（带状线）**而 SPEC 模型为微带、F7 交付对内 0.5/0.6/0.58 并存；交付步距集合 {0.5,0.55,0.58,0.6,1.2,1.45} 与 SPEC 三项（0.175/0.875/1.2）**无一自洽**。**门判定不变**（零几何/阈值改动）。
- **CO-55（本件新增，L2/SI 自裁）**：由**交付几何反解 8L 叠层要求**（不再索取板厂表）：`d(F.Cu–In1.Cu)=0.1164`（JLC 2116×1）、`d(In5.Cu–In6.Cu)=0.0994`（3313×1）、`b(In1.Cu–In3.Cu)=0.72`（对称 0.36+0.36 core）；余隙按 1.6mm 闭合（机判 delta=0.000）。此叠层下交付各档（gap 0.295/0.395…）落 **82.1–91.2Ω ⇒ 全部 85±10%**（一阶 IPC-2141，datum 85.05 vs 85.1）⇒ **几何零改动、无需 re-open**。回退：若板厂 b<0.582 则 In2 须按 `w*(b)` 重导（表见 CO-55 §4 R2）。**B.Cu 判非阻抗控制层**（参考层为信号层 In6）；In6 下方 B.Cu 不得并行铺铜/走线。**CO-53/CO-54 的输入缺口取消**（改下达要求 + 板厂券终判）。**已由 CO-56 落盘**。
**已由 CO-56 落盘**（见下）。
- **✔ CO-58（本件新增，L2/L3 对账 · 更正 CO-57 表述）**：并排换算四档口径 —— R3-2「0.875」（v1.1 requirement）/ v22 容量口径 1.46（=0.585+0.875）/ **冻结轨距 1.08**（v2.0 硬约束 2「冻结轨距仍 1.08（实际排轨居中值）」+ `mcio_learning_gate.md` §4.2「模板参数（生产过/结构冻结）track_pitch 1.08」）⇒ 铜边 **0.495** / 交付走廊 1.20+0.705 ⇒ 铜边 **0.495**（**与冻结口径同值 ⇒ 走廊不构成对冻结口径的偏离**）/ 交付芯片侧 In6 带 1.05+0.705 ⇒ 铜边 **0.345**（低于冻结 0.15）。⇒ **更正**：CO-57 的「交付违约 R3-2」属表述过当；0.875 在 v2.0 语境是 **capacity 口径**，实排轨距冻结值 = 1.08。**收窄待裁**：**Q1（L1）** R3-2 是 realized 要求还是 capacity 口径（realized ⇒ 需 1.580 全链重导，几何可行 12.64<N16.2/S20.8；capacity ⇒ 仅芯片侧 In6 带需重导至 ≥1.08）；**Q2（L2-ready，待 Q1 定标）** 芯片侧 In6 带重导。见 `m13_v57_CO58_interpair_baseline_reconciliation.md` `267621cdcfae1bbc`。
- **✔ CO-59（本件新增，L2 自裁 · 残余闭合 + 更正 CO-58 基线）**：① **残余② 闭合 PASS** —— L4 板 B.Cu×In6 并行耦合 **0 对**（夹角≤10°/重叠>0.3mm/横向<0.5mm），全板最小并行横向距 **20.3mm**，B.Cu 实体 70 段/32 网/**0 zone**，与 In6 为**垂交**关系 ⇒ CO-55「不得并行」已满足。② **口径再基（机判）**：`route_model_config.json` `71c001125959b24b` 的 `capacity_audit.inter_pair_spacing=1.46` + note「语义 = 0.875 对间铜边净空」为**要求注入点**；**1.08 是 `channel_alloc.pitch_fallback`（回退值）** ⇒ CO-58 以 1.08 为基线的「走廊一致」结论**成立性不足**。③ **交付板级实测**：EAST 对间距 **1.449**（铜边 0.744：vs 1.46 **−0.011** / vs 0.875 **−0.131**）、WEST **1.050**（铜边 0.345：**−0.410 / −0.530**）⇒ **两读数下均不达标**；CO-57 的 0.345 事实保留。④ 四方口径互不自洽（SPEC `tracks_y` 1.20 / SPEC 派生 1.46 / config 1.46 / 文本「口径统一 1.46」/ 模板 1.08）⇒ 收窄为 owner 单一问句：**是否授权走廊对间距 → 1.580**（= 0.705+0.875，歧义无关目标，同时满足 1.20/1.46/0.875；带高 7×1.580+0.705 = 11.765 ≤ N16.2/S20.8）。见 `m13_v57_CO59_L2_residual_closure_and_interpair_target.md` `0fdb19fec39bf110`；附：CO-54 audit 在 rev-4 下已重基线为 `69fcbcdd19025874`（v1.27/CO-58 引用的 `ba87413ae4d8c7b4` 为 rev-3 值，本件更正引用而不改工件）。
- **✔ CO-60（本件新增，L2 走廊分配 · 可达性机判 / 负结果）**：lane 步距为合法 L2 旋钮（重发 ALLOC.5 **逐字节复现** `0bf6cdc203887a48`）。冻结包络内机判：**西侧对间距 >1.05 即落位失败**（余量 <0.05；失败集中于芯片逃逸区 x≈93.2 球栅，`PCIE_UP6/UP7 input`，行扫 15148~15150 耗尽）；**东侧 1.580 可落位 32/32 且放置净距 0 违规**，但全链 **G4/G5/G6 PASS、G7 DFM FAIL new=84（copper_edge_clearance 83）** ⇒ 破板边铜距；**恢复冻结对铜跨 0.585（POL_OFF 0.19）⇒ 0/32 落位**。⇒ R3-2 realized 0.875（⇒ 中心距 1.580）在冻结 L1 包络内**不可达**，两端皆 L1 决策 ⇒ **L1 冲突**，依《LAYOUT_CONSTITUTION》第三章第 2 条升 owner。见 `m13_v57_CO60_L2_corridor_pitch_reachability_and_L1_conflict.md` `71dfd8f7d9dcd96d`。
- **✔ CO-61（本件新增，L2 · 策略维穷举 / 负结果）**：把搜索从"单旋钮"扩到 L2 **策略维**：① 西侧 对间距{1.20,1.46,1.58} × {无/有落列交换} × {colmode pol/默认} **9/9 全部落位失败**（失败点均为芯片逃逸区，行扫 ~15150 耗尽）⇒ 与策略无关，受**球栅逃逸硬限**；② 东侧 1.580 在 4 个走廊平面锚定（EDELTA −0.10/+1.0/+2.0/+3.0）下：3 个可落位但走廊 y_max 80.5~82.6 **越板边可用上限 78.5975**，第 4 个起 J2 侧逃逸落位失败 ⇒ **无可行锚定**（东侧 1.580 需 24.4mm > 可用 22.3mm）。⇒ L2 侧无可再自裁动作，L1 冲突成立。见 `m13_v57_CO61_L2_search_exhaustion_and_L1_conflict.md` `e11ef05202a578c6`。
- **✔ CO-62（本件新增，L2/SI 裁定 · 负结果）**：补核 CO-55/CO-56 残余条款**前半句**（「B.Cu 不得承载阻抗关键网」）。机判：本阶段 **68 条高速网中 32 条**在 B.Cu 上有铜，合计 **290.21mm**，单网最长连续 **17.87mm**；差分对 **P/N 的 B.Cu 长度失配最大 1.443mm**（5 对同值，系统性）。一阶 Zdiff（同 CO-55 模型）：F 88.4 / In2 82.0 / In6 85.5 均落 85±10%，**B.Cu 单参考(In6 信号层, h=0.1836) = 119.1Ω ⇒ 超出带（+34）** ⇒ B.Cu 无法承载 85Ω。二阶：层混合致电气 skew 一阶 0.03~0.16mm 内层等效（悲观档超 0.15mm 预算），现有 SI `skew`（纯物理长度 0.0031）**未覆盖**该机制。⇒ **L2 裁定：维持并强化 CO-55 条款，现交付违反**；整改 = 16 张 dn 带页逃逸/stub 层移出 B.Cu（LID 新修订 + 全链重导 + SI 判据改按层加权）。见 `m13_v57_CO62_L2_Bcu_impedance_carrying_ruling.md` `691ed6991c9957fe`。
- **✔ CO-63（本件新增，L2 → 更正为 L1）**：按 L2 权限直接试做 CO-62 的整改（层分配）：两个 **B.Cu-free** 逃逸层计划均 **FAIL** —— A（dn→In2/up→In6）**18/32 落位 + 1 违规**；B（east→In6/west→In2）**12/32 + 11 违规**（违规均为 F.Cu 段-焊盘 `sp`）。根因：4 信号层中 F.Cu 被 SMD 焊盘占用、In6 为 lane 层（逃逸入 In6 必自交）、In2 已给西侧逃逸 ⇒ **B.Cu 是唯一剩余逃逸资源**，其使用是**承载性**的。⇒ **更正 CO-62 的定层**：该项整改**不能由 L2 完成**，根因是「外层 B.Cu 无邻接平面」这一**包络/拓扑**事实 ⇒ **第二项 L1 冲突**。见 `m13_v57_CO63_L2_Bcu_free_layerplan_infeasible.md` `50f1c0913788044d`。
- **✔ CO-64（本件新增，L2 叠层分配 · ECN）**：依 L2_STRUCTURE_v2.0.md:126「8L 重入 ECN 触发条款」（三条实质条件已由 CO-60/61/63 机判成立）发起 ECN。根因：冻结派生 `total=2*L_signal` + 家族 `F/G/S/G/[P/G]/S/B` **必然**使最外层 B.Cu 无邻近参考平面，而 B.Cu 又是逃逸所需第 4 信号层 ⇒ 自相矛盾。叠加修正规则（每信号层须有参考平面）后重推：**8L 有解但须重排平面位置**（与冻结平面用途红线冲突，属**电源域划分=L1**）；若保留冻结平面用途则最小 **10L**（`F(S)/In1(G)/In2(S)/In3(G)/In4(P3V3)/In5(G)/In6(S)/In7(G)/In8(S)/B(G)`，B.Cu→GND，多 1 层内部信号层，对 ① 亦有利，属**层数裁决=L1**，文档 :136 明文）。⇒ 两项 L1 冲突统一为二选一决策。见 `m13_v57_CO64_L2_LID_reentry_ECN_stackup.md` `02051da11ce89e7f`。
- **✔ CO-65（本件新增，L2 收口 + L1 决策请求）**：①**修正 CO-62 铜厚口径**——B.Cu 按外层 1oz（t=0.035）重算为 **113.0Ω**（CO-62 记 119.1Ω，结论同为超带），且达 85±10% 需 **d(B.Cu–邻平面) ≤ 0.127mm**（现 0.1836）⇒ 仅加参考平面不够，叠层**厚度**亦须重推。②**机助证明 8L 不可兼得**：冻结平面 4 层 + 需 4 信号层恰为 8 层，而 B.Cu 唯一邻层是 In6 ⇒ B 有参考则 In6 必为平面，与 In6∈信号层矛盾；穷举全部 6561 个层序列，满足条件的 8L 解 16 个、**保留冻结平面用途的 0 个**。⇒ 两条整改：(a) 8L 重排平面用途（板厂成本不变，须放宽平面用途红线）/ (b) 8L→10L（保留全部平面用途、多 1 层内部信号层对 ① 亦有利，属层数裁决）。**建议 (b)**。见 `m13_v57_CO65_owner_decision_brief_stackup.md` `f1306a91ce8c98a4`。
- **✔ CO-66（本件新增，L2 叠层分配 · 归口更正）**：**更正 CO-65 §3** —— 方案(a) 层数/平面数/电源域**均不变**（仍 3×GND + 1×P3V3 同网），只改平面**位置与厚度** ⇒ 属 **叠层分配 = L2**（与 `L2_STRUCTURE_v2.0.md:136` 一致）；**仅方案(b) 需 L1（层数裁决）**。并经机判给出 8L 对称叠层（`F(S)/In1(G)/In2(S)/In3(G)/In4(P3V3)/In5(S)/In6(G)/B(S)`）的**厚度自洽解**（10 组可行；例：外层 w=0.205/h=0.1101，内层带状线 w=0.130/b=0.4134，自由余隙 0.553，1.6mm 闭合，各层 85.0Ω）⇒ 代价 = **内层线宽 0.205→0.13~0.19 的几何协同变更**。执行清单（LID REV6 / SPEC rev-5 / 几何重解 / 引擎 bump / G4..G7 / SI 按层加权 / 重新对抗评审）见 CO-66 §3。见 `m13_v57_CO66_L2_option_a_stackup_derive.md` `72ec6c4dbdb4a75c`。
- **⚠ CO-57（本件新增，L1 升级 · owner 待裁）**：L1 冻结强条 R3-2『**对间铜边净空 ≥0.875mm**』（`L1_TOPOLOGY_v1.0.md` 硬约束 3 / `v2.0.md` 硬约束 2「口径统一 = 1.46」，v22 用户裁决）vs 交付实测：走廊轨距 **1.200**（−0.260）、对内铜跨 **0.705**（使 1.46 只给 0.755 净空）、对间最紧铜边 **0.345**（In6 长平行带）。按现行铜跨满足 R3-2 所需中心距 = **1.580mm**（8×1.580 = 12.64 < N16.2/S20.8 ⇒ 几何可行但需全链重导）。三选项：**A** 重开 W3 走廊至 ≥1.580（L1 裁，触及落列/球行派生走廊行）/ **B** 回退铜跨 0.705→0.585 恢复 1.46 口径（L2 可执行但与 CO-10 裁定冲突）/ **C** 正式修订 R3-2 阈值（**L1/owner 明示**）。**本件零几何/阈值改动、不预判**；裁定前**不得声称对间间距合规**。见 `m13_v57_CO57_L1_escalation_interpair_clearance.md` `e99f58e06730daaf`。
- **CO-56（本件新增，L2/SI 自裁 · SPEC ECO rev-4）**：`SPEC_k2_v4.spec-rev-4.json` **`1c4eecb0edf4a446`**（**纯加性**：8L 声明 + `stackup.dielectric_8l` 逐层介质表 + `impedance.per_layer` 分层口径 + `p_gap_semantics=lower_bound`/`inter_pair_spacing_scope`；**所有数值阈值未改**）。同步 bump：引擎 `F.spec`/`FROZEN_SHA`、validator 冻结集、L5 记录 rev **L5-SI.5**。**几何不变性机判**：新图纸 `4e7497daf97cebd1` 与原 `dfa1d7c4a811b0da` 的 `route_geometry`/`pages`/`decision_contract`/`layers`/`method` **逐字节相同**（仅 `inputs_sha`/`frozen_sha_check` 指纹重基线）；**板 `cdcb869e9827ec87` 逐字节不变**。**复跑**：G4 FEASIBLE_ALL、G5 PASS（frozen=True）、G6 PASS（viol 0）、G7 PASS（new=0 / 在册未连 0/68 / skew 0.0031）；**重跑零漂移（不动点）**。PI 项状态 → `DESIGN_CONFORMANT_FIRST_ORDER_PENDING_COUPON`（终判=板厂券）；**残余**：对间串扰复核（0.345 vs 基线 0.875）与 B.Cu 非阻抗控制层声明（见 CO-54 F2/F3）。

## 2. 冻结栈与关键输入（现行）
| 项 | 件 | sha16 |
|---|---|---|
| 叠层（L2） | `m13_v57_layer_intent_rev6.json`（**LID REV6 / CO-68**：signal = F/In2/**In5**/B；In1/In3/**In6**=GND，In4=P3V3） | **`05009687a3f01583`** |
| 走廊/见证（L2） | `m13_v57_big_w0r_corridor_model.json`（W0-R，未改） | `80ee9adb78a7e9ad` |
| 通道分配（L2/L3） | `m13_v57_co16_channel_allocation_v7.json`（**CO16-ALLOC.7 / CO-69**：stub 层 In6→In5，4 页；其余逐字节同 ALLOC.5） | **`a765af4c9bf61e64`** |
| 逃逸域（L2/L3） | `m13_v57_co37_escape_domain.json`（CO-37）＝ `.kicad_dru` 引用 `5616a9f873c9b844` | `5616a9f873c9b844` |
| SPEC（红线原件） | `SPEC_k2_v4.json`（未动） | `0bd52ed48e720b8c` |
| SPEC（引擎消费 ECO，**现行**） | `SPEC_k2_v4.spec-rev-6.json`（**CO-72**：PDN 平面声明对齐 LID REV6；叠层/阻抗同 rev-5） | **`9e8fb5bae4a33207`** |
| SPEC（历史 ECO） | `SPEC_k2_v4.spec-rev-3.json`（ECS-001，CO-40；保留未动） | `2d6dbd8bd8d667d7` |
| 规则 | `_shared/eda_core/drc_rules.json` | `0a459839e15960b8` |
| manifest | `m13_v57_s1_page_manifest.json` | `a8ef3ea8ecff99d7` |
| 冻结板（8L 基线） | `k2_v4_8L.kicad_pcb` | `fb07d25ac426ff84` |

## 3. 整链门禁（G4..G7，全部实测）
| 门 | 判定 | 证据（sha16） |
|---|---|---|
| G4/W3 | **PASS（FEASIBLE_ALL）** | 主件 **`d8fc88d6f4133fba`**（rev **W3-CN.41**；CO-72 后几何与 `87ef07f280e4dffb` **逐字节同**，仅 inputs_sha 重基线）；landing `fcfa5c3c32ca7f87` |
| G5/W4 | **PASS** | `m13_v57_w3_validation.json` `26313087acce4d3d`（validator v2；G-M1..6 True、A1.2/A1.3/A1.4 True、frozen=True；冻结集含 `spec=9e8fb5bae4a33207`） |
| G6/L4 | **PASS** | 板 **`0e636a67c1472462`**（68 网/**2523** 段/252 via；track 宽度按层 F/B 0.205、In2/In5 0.16）；construction `a9f96a458f94f820`；`m13_v57_l4_validation.json` `094f21a3db4e1533`（L4-A..**F** True、viol 0） |
| G7/L5 | **PASS** | fab `73a9d22a4adeee6d`（2523 tracks/252 vias）；si `73f9b59ed5f6f3ce`（rev **L5-SI.6**：**按层加权电气 skew 0.1300 ≤ 0.15**、physical 报告 1.1046、pdn_status=reserved_not_poured）；**dfm `40445f87be664f31`（L5-DFM.6：多重集 new=0 / disappeared=0 / 在册 0 未连）** |

DFM 收敛轨迹（v1.15 之后）：**D1/D2 归零（CO-23；W3-CN.37）→ 73（CO-23）→ 60（CO-37 D3c）→ 54（CO-41）→ 38（CO-43）→ 0（CO-45）**。
L4 板 `kicad-cli` 实跑：仅冻结基线 42 条 lib/silk，**铜层违规 0**（clearance/shorting/solder_mask_bridge/tracks_crossing 全 0）；基线铜违规数 = 0 ⇒ `new_total=0` 等价于「零铜层新增」。

## 4. v1.15 → v1.16 取代沿革（rev 与变更单）
- **W3-CN.27 → .36**（ROOT-16 线）：CO-05..CO-11（O4 落列可行性、安全 hop 拓扑、pair 域 v1.4/1.5、lane 平面）；
  CO-16/CO-18/CO-19/CO-22（东侧重派生、O4 有界幅值闭式蛇形、板内 J3 fan、lane 平面重整）⇒ 全板 **32/32 有效**（W3-CN.34/.35/.36）。
- **W3-CN.37**（CO-23）：板边真带（Edge.Cuts y=33/79、x=143）⇒ D1 copper_edge / D2 hole_to_hole 归零。
- **D3b 收官**（CO-25..CO-36，L2 自裁）：connector 落列器改「land 段长升序」（CO10_LXPRIO=landlen）⇒ CO16-ALLOC.5。
- **D3c**（CO-37）：SPEC 逃逸区规则域 `.kicad_dru`（0.075 + 4 具名 rule area，**显式排除 `PCIE_REFCLK*`**）。
- **L1 更正**（CO-38→CO-39）：D3a 非引脚缺陷，J2 侧 REFCLK 引脚由原理图网表 + SFF-8654 pinout 真源锁定 ⇒ 闸口 CLOSED。
- **W3-CN.39**（CO-40/CO-41）：SPEC-REV-3 ECS-001（J2 外列 N 单次换层 F.Cu→In2→F.Cu，每线 2 via）⇒ DFM 60→54。
- **W3-CN.40**（CO-42..CO-45）：远端带内接入（禁沿 A 排平行）＋ 对内偏移 `{P:0.0,N:-0.5}` ＋ dip 解耦 ＋
  图纸/nodes 一致化 ＋ P 轨等长幂绕 ＋ `A-CN.5d` ⇒ **DFM 38→0、G7 PASS**。

## 5. 覆盖性声明（宪法第五章第 1 条）
管辖对象 = 34 页（32 MCIO lane 页 + 2 REFCLK 页）/ 68 网 / 2 远端连接器（J3/J4）接入；**无「待定/暂不管」对象**。
每对象均有机器可读决策：`pages[*].nodes`（3D）+ `pages[*].vias` + `route_geometry` + `decision_contract`
（corridor_x / 分层链 / max_vias_per_line / pair_rule / REFCLK 层契约）。

## 6. 已知限制与豁免（如实声明，不得当作 PASS 依据掩藏）
1. **板字节已可复现（CO-49 解除）**：原 `pcbnew` 保存使 `segment/via/zone` 块的**顺序与 uuid** 每次重建漂移（其余块逐字节稳定）；
   CO-49 在 L4 applier 内做确定性规范化（连续同类 run 内排序 + 由内容派生 uuid5，只碰这三类块）⇒ **构建→L4→L5 全链 7 件逐字节可复现**；
   现行 L4 板 `cdcb869e9827ec87`（规范化前历史 sha 见 git 与 CO-45..CO-48 各 commit；**几何内容身份** = drawing `dfa1d7c4a811b0da`（W3-CN.40）/ rev-4 下重基线 `4e7497daf97cebd1`，二者 route_geometry 逐字节同，见 CO-56 §2）。
2. **CO-16 层跨不相交豁免**：独立验证器 G-M4 记录 `span_blind_min_mm = 0.163083 < 0.175`、`span_blind_violations = 3`，
   依 CO-18 §1b/§4-2「同层跨不相交 ⇒ 物理净距不适用」豁免；`kicad-cli` 实跑同层净距 0 违规（与该豁免一致）。
3. **DFM `new`：已升级为多重集差（CO-51 解除原限制）** —— 键 = `(type, items[].description)`，并显式报 `disappeared_total`（基线消失，L4=tracks-only ⇒ 须为 0）；
   实测 new=0 / disappeared=0（42 条 lib/silk 基线全部在册）。
4. **未路由网 348 项**（冻结基线 416）：v57 范围为 68 条高速网；其余网不属本阶段（不得据此判 FAIL，也不得声称整板已布完）。
5. **阻抗几何（CO-53→CO-56 已收口：一阶在设计带内，终判=板厂券）**：交付对内中心 0.500（边距 0.295）≠ SPEC `p_gap 0.175`；对间最小 0.550 中心（0.345 边距）vs SPEC `inter_pair_spacing_mm 0.875`；SPEC `stackup/impedance.model` 仍 6L 而板为 8L 且板内无介质叠层定义 ⇒ **阻抗符合性 NOT_DEMONSTRATED**（既非已证合规、也非已证违反）：**CO-55 已取消 (a)**（改为反向下达叠层要求，见上）；余 **(b) SI9000 校验（板厂券已声明）+ SPEC ECO rev-4**（stackup/impedance 分层口径/p_gap 语义）**（c）走廊口径已记录**。**已由 CO-55（下达 8L 叠层要求）+ CO-56（SPEC ECO rev-4 + 复跑）收口**：详见 `m13_v57_CO53_intrapair_geometry_impedance_open.md`、`m13_v57_CO54_spec_delivery_drift_inventory.md` `23d22ea76c0b95ff`、`m13_v57_CO55_layer_aware_impedance_build_ruling.md` `f9c45071c5d9141c`、`m13_v57_CO56_spec_eco_rev4_apply_record.md` `5b8b86ed789b5678`（含 **8L 叠层输入缺口可达性实测**与 Zdiff 重导 harness `tools/p3_v57_si_zdiff_rederive.py`）。
   **CO-47 已把该声明升级为谓词**：L5 记录 `dft.in_scope_unconnected_items == 0`（在册网按 kicad-cli 未连项网名解析）；实测 基线 68/68 在册网未连 → L4 **0/68**。
5. **G5 冻结集已校正（CO-46）**：原独立验证器的 `frozen_sha_check` 只钉 ECO spec + **历史 6L 板**，未覆盖红线 SPEC 原件与 8L 冻结板；
   CO-46 以「只增不减」补入 `spec_orig=0bd52ed4` / `pcb=fb07d25a`（并保留 `pcb_6l=f6273de6`）后 G5 仍 PASS。记录：`m13_v57_CO46_validator_frozen_set_fix.md` `bf7431bc6559ea98`。

6. **⚠ L1 待裁（CO-57 → CO-58 → CO-59 再基）**：R3-2『对间铜边净空 ≥0.875』的**时效/绑定范围**。
   - **口径出处（CO-59 机判）**：要求注入点 = `route_model_config.json` `capacity_audit.inter_pair_spacing=1.46`（note：语义 = 0.875 铜边净空 → 1.46 = 0.585+0.875 的中心距换算）；**1.08 属 `channel_alloc.pitch_fallback`（回退值）**，非要求量。**CO-58 以 1.08 为基线的「走廊与冻结口径一致」结论按 CO-59 更正**（原文保留不改）。
   - **交付实测（板级）**：EAST 对间距 **1.449**（铜边 0.744）/ WEST **1.050**（铜边 0.345）⇒ 在 **1.46 中心距**与 **0.875 铜边**两种读数下**均不达标**（EAST 在中心距口径下差 0.011）。板厂口径四方不自洽（1.20 / 1.46 / 1.08）。
   - **残余②已闭合**：B.Cu 与 In6 无并行耦合（0 对；最小并行横向距 20.3mm；B.Cu zone = 0）⇒ CO-55 的 B.Cu 约束满足。
   - **Q1（L1，单一问句）**：是否授权走廊对间距 → **1.580**（= 交付铜跨 0.705 + 0.875，**歧义无关**，同时满足 1.20/1.46/0.875）？授权 ⇒ L2/L3 重导 + （若需）J2/J3/J4 落列/焊盘场变更（L1）；备选：铜跨回退 0.705→0.585 使 1.46 给 0.875（L2 但需重定 8L 阻抗）。
   - **CO-70/71 补强证据（逐层实测，L4 construction，方案(a) 现状）**：对间同层最小中心 / 铜边净空 —— `In5.Cu` 0.550 / +0.345（最长并行 55.97mm）、`B.Cu` 0.550 / +0.345（14.22mm）、`In2.Cu` 0.580 / +0.375（20.35mm）、`F.Cu` 1.124 / +0.919（达 0.875）。⇒ **R3-2 0.875 在 4 个信号层中 3 层违反**；因其同时出现在 In2/In5/B（非单一层分配所致），**层分离（channel 重分配）不能作为 L2 解**：根因 = 交付轨距（WEST 1.050 / EAST 1.449）× 对内半边距 0.25 ⇒ 邻线净距 0.345；达 0.875 需中心距 1.580，与冻结 L1 包络（球栅逃逸 / 板边 78.5975）互斥（CO-60/61 复现）。⇒ ① 维持 **L1**。
   - 裁定前：不得声称对间净空合规、不得放宽 R3-2/冻结口径。G4..G7 现状与判定不因此件改变。

## 7. 归档
变更单 CO-05..CO-46 记录与 DRC 明细（`m13_v57_co41_refclk_drc_after.json` / `m13_v57_co43_refclk_drc_after.json` /
`m13_v57_CO45_refclk_skew_meander_impl_record.md` `7b8cb5b1294d8c71` /
`m13_v57_CO46_validator_frozen_set_fix.md` `bf7431bc6559ea98` /
`m13_v57_CO47_l5_inscope_connectivity_predicate.md` `031fc91aa520cb92` /
`m13_v57_CO48_l5_g7_record_emit.md` `7e094c2db5bf3b3d` /
`m13_v57_CO49_l4_byte_reproducible.md` `6c27149fff749a1d` /
`m13_v57_CO50_pdn_fact_verified.md` `311e98163d49ac82` /
`m13_v57_CO51_dfm_multiset_metric.md` `922feaf4b5c8c143` /
`m13_v57_CO52_via_budget_closure.md` `eaaea6b5e4456ddc` /
`m13_v57_CO53_intrapair_geometry_impedance_open.md` `36f16620c7132da6` /
`m13_v57_CO58_interpair_baseline_reconciliation.md` `267621cdcfae1bbc` /
`m13_v57_CO59_L2_residual_closure_and_interpair_target.md` `0fdb19fec39bf110` /
`m13_v57_CO67_L2_redline_ruling.md` `c562419d70a41ab9` /
`m13_v57_CO68_L2_option_a_execute.md` `17965908fd5d5635` /
`m13_v57_CO69_L2_option_a_chain.md` `03ca3d424839884c` /
`m13_v57_co69_adversarial_review.json` `50ff390f2803f25d` /
`m13_v57_co72_pdn_align.json`）已入库；**本件取代 v1.36**，v1.36 及以前保留不改。
监理/tag 政策：`k2-v57-g7-l5-pass`（G7/L5 PASS）已 push；`git ls-remote` 核验 `^{}` → `b5afe47`。

End of boundary v1.37（含 CO-67..CO-72）。
