# K2 · `k2_p4_*` 工具 **RETIRED（离链）清单**

> 授权：监理 **#K2-28 §四**（裁定：E-2 的「退役」要求 = **离链 + 收敛证明**（已满足）；**物理退役采「清单标记」**——**不物理删除/移动**（44 件被既有证据件按精确路径引用，移动将使复跑命令失效，违宪法第三条可追溯））。
> 事实基础：构造链 `python3 k2/tools/k2_gen_v5.py` 的输入 = 真源 YAML / SPEC / `ForgeOS.refmap.json` / `ForgeOS.pretty` mod / `L2/PLACEMENT_SOLUTION_v1.json` / JLC 模板 —— **不含任何 `k2_p4_*`**（strace 零板读 + E-2 三臂实证，见 P3 证据件）。
> `k2_p4_build_l5_v1.py`（读 `l4`）与 `k2_p4_composed_land_v2.py`（板→板）为**旧修补链**的两件，**已离链**。

| # | 文件 | 用途（首行 docstring） | 读板? | sha16 | 状态 |
|---|---|---|---|---|---|
| 1 | `k2_p4_bom_gen_v1.py` | k2_p4_bom_gen_v1.py — K2 · P4 · `k2/fab/k2_v4_bom.csv` 生成器（**ref 集 BOM**；判据消费口径）。 | 否 | `9921dbae67af97ce` | **RETIRED（离链）** |
| 2 | `k2_p4_build_l5_v1.py` | k2_p4_build_l5_v1 — **P4 施工执行器**（#K2-18 §五 U3 / §九-3）。 | **是** | `e8083b771aa20685` | **RETIRED（离链）** |
| 3 | `k2_p4_c86_relocate_v1.py` | K2 P4 · **C86 重落位 + 平面接入 v1**（L2：placement/机械 + 布线/过孔策略）—— 清除 C86 ⊂ U2 实体碰撞。 | **是** | `1da5a23ba139c751` | **RETIRED（离链）** |
| 4 | `k2_p4_composed_land_v1.py` | K2 · P4 · **复合落件器 v1**（supersedes `k2_p4_w7_land_v1.py`；dry-run 默认）。 | **是** | `41740377fd2dca19` | **RETIRED（离链）** |
| 5 | `k2_p4_composed_land_v2.py` | K2 · P4 · **复合落件器 v2**（supersedes `k2_p4_composed_land_v1.py`；dry-run 默认）。 | **是** | `f702bf8be289358d` | **RETIRED（离链）** |
| 6 | `k2_p4_converge_v1.py` | k2_p4_converge_v1.py — K2 P4 收敛增量 1（**L2 自裁**施工修正；确定性一次算对）。 | **是** | `2d63a6a88bc3afff` | **RETIRED（离链）** |
| 7 | `k2_p4_courtyard_completion_v1.py` | K2 · P4 · courtyard 补全可行性测量（只读，纯 stdlib；W-7 `missing_courtyard` 40 件 + J-8b 联动）。 | **是** | `e1e91289cee3e9a1` | **RETIRED（离链）** |
| 8 | `k2_p4_courtyard_margin_sweep_v1.py` | K2 · P4 · `missing_courtyard` **外扩口径 → 碰撞** 曲线（只读测量；不写仓库）。 | **是** | `c54d64066317d012` | **RETIRED（离链）** |
| 9 | `k2_p4_defect_scan_v1.py` | K2 · P4 · 两个只读缺陷扫描器（不写仓库）。 | **是** | `2eef5647d8fdecd9` | **RETIRED（离链）** |
| 10 | `k2_p4_gate_coverage_v1.py` | K2 · P4 · 「判据集 == manifest 应然集」覆盖率闸（只读，可复跑）。 | 否 | `43acfd15201a390b` | **RETIRED（离链）** |
| 11 | `k2_p4_gnd_vias_v1.py` | K2 · P4 收敛增量 —— GND 平面接入 v2（阶段 E）：层正确净距 + 盘中孔（via-in-pad）。 | **是** | `9a57160f0464a47e` | **RETIRED（离链）** |
| 12 | `k2_p4_hs_baseline_v1.py` | U4-D（G-1）阶段 H · 步骤 1：**冻结折线只读取证 + 守恒基线**（ENG 草案；不改板）。 | **是** | `30e61d49dddb8f4d` | **RETIRED（离链）** |
| 13 | `k2_p4_j8_measure_v1.py` | K2 · P4 · J-8 余项测量件（只读、纯 stdlib）：器件重叠 / 密度分布 / 工艺极限（关键间距侧证据）。 | **是** | `2d77bc8b902f87fb` | **RETIRED（离链）** |
| 14 | `k2_p4_l2_placement_courtyard_v1.py` | K2 P4 · ⑥ **L2 placement 增量 + 40 件 courtyard 补全 v1**（改板，默认 dry-run）。 | **是** | `3de81e5a7f24ceff` | **RETIRED（离链）** |
| 15 | `k2_p4_lib_snapshot_v1.py` | K2 P4 · ⑦ **库侧收口：以板为准的封装库快照 + 全板 `lib_id` 重指** v1（默认 dry-run）。 | **是** | `afa9be4bf599626b` | **RETIRED（离链）** |
| 16 | `k2_p4_ls_in2_v1.py` | K2 · P4 收敛增量 9（阶段 G）—— 低速/边带 **F.Cu→In2.Cu 盲孔 + In2 通道布线**。 | **是** | `557937225ac17fc7` | **RETIRED（离链）** |
| 17 | `k2_p4_ls_local_v1.py` | K2 · P4 收敛增量 —— 低速/电源**局部闭合**（阶段 F1）：把 DRC 未连接的两端「就近」接上。 | **是** | `3eb4331bce9ba0ac` | **RETIRED（离链）** |
| 18 | `k2_p4_ls_route_v1.py` | K2 · P4 收敛增量 —— 低速/电源 **F.Cu 局部通路（A*，阶段 F2）**：把剩余未连接边中「同层可达」的两端接上。 | **是** | `9ad1050e013c97ca` | **RETIRED（离链）** |
| 19 | `k2_p4_ls_xlayer_v1.py` | K2 · P4 收敛增量 —— 低速/电源 **跨层通道布线（阶段 F3）**：IC 侧落孔 F→B → B.Cu 主层通道 → 落点。 | **是** | `92029fe42e6886e2` | **RETIRED（离链）** |
| 20 | `k2_p4_mroute_v1.py` | K2 · P4 增量 15（L2 自裁）—— **多层迷宫布线器 v1**（span 感知孔类 + 扩窗 + 精确放行闸）。 | **是** | `7e5c0bf7bb03269d` | **RETIRED（离链）** |
| 21 | `k2_p4_owner5_del_c89_board_v1.py` | k2_p4_owner5_del_c89_board_v1.py — owner ⑤ 执行（**删 `C89`**）板侧删除器（#K2-24 §三-5）。 | **是** | `eb69e42dd11c9c8a` | **RETIRED（离链）** |
| 22 | `k2_p4_owner5_del_c89_pro_v1.py` | k2_p4_owner5_del_c89_pro_v1.py — owner ⑤ 执行（**删 `PWR_5V_KEY`**）pro 侧 netclass 删除器（#K2-24 § | 否 | `208fa76ccb700d1e` | **RETIRED（离链）** |
| 23 | `k2_p4_owner5_land_v1.py` | k2_p4_owner5_land_v1.py — 沙箱件落仓库（T-41/T-22 纪律；#K2-24 执行链）。 | 否 | `89813b2280887cff` | **RETIRED（离链）** |
| 24 | `k2_p4_owner5_truesource_bump_v1.py` | k2_p4_owner5_truesource_bump_v1.py — owner ⑤ 执行（**删 `C89` + `PWR_5V_KEY`**）真源 bump（#K2-24  | 否 | `250da380e046538c` | **RETIRED（离链）** |
| 25 | `k2_p4_p3v3_col_v1.py` | K2 · P4 增量 14（L2 自裁：**PDN / 走廊 / 过孔策略**）—— P3V3 去耦列 + C82.1 接入 In4 电源面。 | **是** | `5e912b528943a655` | **RETIRED（离链）** |
| 26 | `k2_p4_pdn_in4_v1.py` | K2 · P4 增量 12（L2 自裁，owner #14「PDN = 自裁勿停」）—— **电源面（In4）接入：F→In4 盘中孔**。 | **是** | `ea5af7e41eebd934` | **RETIRED（离链）** |
| 27 | `k2_p4_pdn_stitch_v1.py` | K2 P4 · PDN 接线增量 v1 —— 让「承重支路」dangling 过孔与**同网平面/铜**建立第二层连接。 | **是** | `1d9b76bc3c7a5f1a` | **RETIRED（离链）** |
| 28 | `k2_p4_rev43_declare_v1.py` | k2_p4_rev43_declare_v1 — P4 增量 15 的 SPEC 留痕（rev-42 -> rev-43）+ project.yaml 重指向。 | **是** | `51d3ec8f8b06a682` | **RETIRED（离链）** |
| 29 | `k2_p4_rev44_declare_v1.py` | k2_p4_rev44_declare_v1 — P4 增量 15 的 SPEC 留痕（rev-42 -> rev-43）+ project.yaml 重指向。 | **是** | `93681e886a77d895` | **RETIRED（离链）** |
| 30 | `k2_p4_silk_text_fix_v1.py` | K2 · P4 · ③ 丝印位号残余修复器 v1 —— 字形级几何判定；DRC 只作末检；不写仓库。 | **是** | `ac213369aa0e104c` | **RETIRED（离链）** |
| 31 | `k2_p4_spec_d1d2_pinheader_fix_v1.py` | K2 · P4 · **SPEC D1/D2 排针列补正 + 版本 bump**（`column_x`/`positions[*].x` 26.5 → 27.94）。 | **是** | `1dfba57ddb656331` | **RETIRED（离链）** |
| 32 | `k2_p4_spec_rev50_owner5_del_c89_v1.py` | k2_p4_spec_rev50_owner5_del_c89_v1.py — owner ⑤ 执行（**删 `C89`/`PWR_5V_KEY`**）SPEC bump → re | 否 | `80b618b4c5cbdbe7` | **RETIRED（离链）** |
| 33 | `k2_p4_spec_rev_bump_v1.py` | K2 · P4 · **SPEC 版本 bump + `pd` 几何对齐**（落件前置器；dry-run 默认）。 | **是** | `4bd5931ab9f43806` | **RETIRED（离链）** |
| 34 | `k2_p4_spec_z2_g10_input_layer_v1.py` | K2 · P4 · **写入 Z2/G10 输入层 + 版本 bump**（`keepout_geometry` / `pd.zone_defs.board_realized_zo | **是** | `9b8aad9419441088` | **RETIRED（离链）** |
| 35 | `k2_p4_strap_a0_v1.py` | K2 · P4 —— **strap `DS320_STRAP_A_ADDR0_15-8` 接线（L2 走廊/placement，自裁域）**。 | **是** | `62ff996b8531d385` | **RETIRED（离链）** |
| 36 | `k2_p4_tncv_align_v1.py` | K2 P4 · tncv 对齐增量 v1 —— 清除 `track_not_centered_on_via` 残项（L2：布线/过孔策略，纯几何对齐）。 | **是** | `757c610458702f3d` | **RETIRED（离链）** |
| 37 | `k2_p4_u1c85_v1.py` | K2 · P4 增量 13（L2 自裁：**布局/PDN/过孔策略**）—— U1/C85 PERSTA# 邻域 19 项铜几何归零。 | **是** | `104ae22eebe3cee0` | **RETIRED（离链）** |
| 38 | `k2_p4_u4d_refclk_emit_v1.py` | U4-D 试点：把重派生几何落为板（只写 /tmp），并复跑 DRC。 | **是** | `2de45aba96c3c595` | **RETIRED（离链）** |
| 39 | `k2_p4_u4d_refclk_plan_v1.py` | U4-D 试点（改进版）：REFCLK 两对重派生 0/45/90° + 守恒闸 + 变体搜索（只写 /tmp）。 | **是** | `4325efa06e04f1d0` | **RETIRED（离链）** |
| 40 | `k2_p4_u4d_scale_v1.py` | K2 · P4 增量 11（L2 自裁，owner #14 / #K2-19 / #K2-20）—— **U4-D/G-1 规模化**： | **是** | `328a01acdc4888a0` | **RETIRED（离链）** |
| 41 | `k2_p4_upstream_land_fit_v1.py` | K2 · P4 · 「按所命名上游封装复核实体占位」测量（只读，纯 stdlib）。 | **是** | `25487ec65a1ac1ca` | **RETIRED（离链）** |
| 42 | `k2_p4_w7_land_v1.py` | K2 · P4 · W-7 落件器 v1 —— **dry-run 默认**，只有 `--apply` 才写仓库（须监理批）。 | **是** | `a8a52805e7daac24` | **RETIRED（离链）** |
| 43 | `k2_p4_w7_repair_v1.py` | K2 · P4 · W-7 施工修复器 v2 —— dry-run 默认，**不写仓库**。 | **是** | `78d213e0f1158952` | **RETIRED（离链）** |
| 44 | `k2_p4_w8_option_a_install_v1.py` | K2 · P4 · W-8 选项 (甲′)「以板为准」落件器 —— **dry-run 默认；不改 SPEC / criteria / 冻结件**。 | **是** | `d18dd19ea3595b55` | **RETIRED（离链）** |

**合计 44 件**，全部 **RETIRED（离链）**：均为**一次性载体操作/取证**工具（各带其 ruling 授权留痕），**非构造输入**。
**构造链唯一入口**：`k2/tools/k2_gen_v5.py`（`b27ce0c44bfd1afe` + #K2-28 §2.4 注释更正）。
**若日后确需物理移入 `retired/`**：须同批更新全部引用文档并报前/后清单（#K2-28 §四-3）。

—— ENG（ARCHER）· 2026-09-18 · #K2-28 §四
