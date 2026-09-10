# m13 v57 — W3（G4）开工卡

> 卡号：**W3-C1**｜门控位：v2 §2 G4 行（G3 收口后解封，见 `m13_v57_g3_closure_record.md`）。
> 日期：2026-09-10｜基线 HEAD：G3 收口提交（`54587b6` + F-13/G3 文档）。
> 唯一写入：`k2/tools/p3_v57_w3_*.py` + `mcio_feas_step2/m13_v57_w3_*.json/md`。**不改冻结四源/`_shared`/板铜**。

## 1. 输入白名单（权威，全 64hex，运行期硬校验；drift → FAIL）

| 输入 | 路径 | sha256[:16] | 用途 |
|---|---|---|---|
| SPEC | `L3/SPEC_k2_v4.json` | `0bd52ed48e720b8c` | 网类/几何约束/走廊 x 域/连接器拓扑 |
| drc_rules | `_shared/eda_core/drc_rules.json` | `0a459839e15960b8` | pitch 1.46 / clearance 网类 / via 几何 |
| manifest | `mcio_feas_step2/m13_v57_s1_page_manifest.json` | `a8ef3ea8ecff99d7` | 34 页、端点锚、row_y、corridor/band |
| W0-R model | `…/m13_v57_big_w0r_corridor_model.json` | `80ee9adb78a7e9ad` | `usable_y_spans`、refclk 域 |
| F-3 lane frame | `…/m13_v57_f3_lane_frame.json` | `ff804e1edfacbf02` | lane 域 32 位 / 帧序（F-5 键） |
| F-13 param trace | `…/m13_v57_f13_r1_param_trace.json` | `e288ffa5421c2297` | 参数溯源（V-2） |
| F-13 pair coupling | `…/m13_v57_f13_r1_pair_coupling.json` | `82e11c4cbdb4e8d4` | **列对双约束域（V-3）** |
| F-8 R3 gaps | `…/m13_v57_f8_r3_gap_candidates.json` | `8a31632907b17148` | 每 pad 隙列 + 冲突图 |
| F-6b report | `…/m13_v57_f6b_report.json` | `9070ed53f970f480` | 双端谓词 / `required_leg_mm` |

**显式非输入（继承 W0-R I-6 / 矩阵 §4-B）**：旧簿（EscapeTable/ColumnBook/construction_fact）；
SPEC `corridors.*.tracks_y`（v32 求解器反演值）；`j2_escape_topology.outer_escape` 内嵌的
`v25 求解器 vx 区间`；`x-window`/`max-x` 板扫描；**PROVISIONAL `chip_landing_rows` 的逐页选择**（F-12）。
F-13 `admissible_pair_witness` **仅存在性见证，禁作既定指派**。

## 2. 决策契约（已裁，W3 必须消费）

- **D0-1**：R4（AC 墙）**出链**；西页模板 = connector→chip 直连。
- **D0-2**：REFCLK 层 = **F.Cu**（与数据 In2 分离，无同层隔离约束；REFCLK 内部 1.46 守恒）。
- **D0-3**：`EAST=[105.25,132.65]`、`WEST=[65.05,82.35]`（lane 入出口 bound_x）。
- **D0-4（修订）**：`reach = 可用 fan-out 空间`（非预算常数）。判据 `可用 fan-out ≥ required_leg`；
  `reach_avail := span 高度 45.4mm`；k∈{1,2,3,5} 仅作拥塞/逃逸代价指标。
- **F-5**：`row_y=(N.y+P.y)/2`；WEST 按 `conn_ref` 分帧、帧内 `conn_x` 升序。
- **F-6**：双端谓词 `|lane_y−conn_row_y| ≤ reach_avail ∧ |lane_y−chip_row_y| ≤ reach_avail`。
- **F-7**：新增 **R1.5** 过渡段资源层；x 域 EAST `[93.55,105.25]`、WEST `[82.35,93.55]`；
  承载 lane 互斥守恒 + R1.5 的 `no_via` / `no_90deg` 约束域 + 微净空 0.075。
- **F-12**：landing rows 必须与 34 页图纸**原子重发射**；`verdict=CERTIFICATE` 时**不重发射**（全有或证书）。
- **F-13**：R1 列对双约束 `dist ≥ 0.525 ∧ |dx| ≥ 0.38`（真源口径）。

## 3. 层语义与判据

- 数据页层链：`F.Cu (chip stub) → In2.Cu (R1.5 + 走廊 lane) → F.Cu (connector stub)`，**每线 via ≤ 2**。
- R1：每页 P/N 各 1 via（chip 侧 F→In2）；**跨页全部 64 via 两两 ≥ 0.525**（不同网）。
- R2：每走廊（EAST/WEST）16 数据页 → lane 域 32 位中 **严格递增** 注入；目标 = 最小 Σ|lane_y−row_y|。
- R3：每 pad 恰 1 落点；落点 = (gap 列 x, pad y)；同 gap 列内 `|Δy| ≥ 0.525`。
- REFCLK：2 页，F.Cu，lane_y = 锚 row_y（W0-R 域内），页间 ≥ 1.46。

## 4. 输出（冻结 schema）

**`m13_v57_w3_joint_assignment.json`**（`schema=1`, `revision="W3-JA.1"`）
```
artifact, schema, revision, status, verdict ∈ {FEASIBLE_ALL, CERTIFICATE},
contract{id:"W3-C1", card_md, sha256},
inputs_sha{spec,rules,manifest,w0r_model,lane_frame,pair_coupling,param_trace,r3_gaps,f6b_report},
frozen_sha_check{expected,actual,match,drift},
decision_contract{...§2...},
layers: {
  R1   : {status, method, search_nodes, objective{sum_pair_dist_mm}, assignment{<page_id>:{P_via:[x,y],N_via:[x,y],pair_dist_mm,stagger_mm,domain_size}}},
  R1_5 : {status, x_domain{EAST:[lo,hi],WEST:[lo,hi]}, no_via, no_90deg_decl,
          construction_domain_enumeration[], crossing_report{<corridor>:{n_crossings,minimal_cores[]}},
          infeasible_reason|null},
  R2   : {status, method:"exact order-preserving min-cost DP + canonical tie-break",
          objective{total_abs_delta_mm, per_corridor{}}, assignment{<page_id>:{lane_index,lane_y,conn_delta_mm,chip_delta_mm}}},
  R3   : {status, method:"exhaustive per-connector-column enumeration (lex-min feasible)",
          assignment{<net>:{column_x,landing:[x,y],pad:[x,y]}}},
  REFCLK:{status, assignment{<page_id>:{f_cu_lane_y, j2:[x,y], far_ref, far:[x,y], cross_segment{status,reason}}}}
},
pages:[ {page_id,kind,side,corridor,band,conn_ref,row_y,chip_row_y,
         lane{index,y,conn_delta_mm,chip_delta_mm,reach_avail_mm,ok},
         r1{...}|null, r1_5{status,x_domain,entry_x,path[[x,y]...],layer,no_via,corners_deg,crossings[]},
         r2{entry,exit,layer,pol_offset_mm}, r3{pad,landing,column_x,layer_chain},
         vias[{role,x,y,layers,pol}], nodes{P:[[x,y,layer]...],N:[...]}} ],
certificates:[{cert_id,kind,infeasible_layer,corridor,minimal_core,why_no_alloc_possible,escape_hatches[],evidence{}}],
landing_rows:null, landing_rows_status:"NOT_REEMITTED"|"EMITTED",
objective{...}, evidence_protocol{...},
no_first_fit{statement, construction:"canonical-order exact DFS + DP + exhaustive enumeration (no per-net first-fit)",
             enumeration_orders_probed:3, byte_identical:true},
residuals:[...]
```
若 `verdict=FEASIBLE_ALL` 另发 **`m13_v57_w3_chip_landing_rows.json`**（同提交、同 SHA 链，F-12）。

## 5. 验收谓词（A-W3.x，须逐条可观测）

- **A-W3.1 守恒**：R3 每 pad 恰 1 落点（72/72）；R1 每页恰 2 via（64/64）；R2 每页恰 1 lane。
- **A-W3.2 独占**：R1 全部 64 via 两两 ≥ 0.525；R2 同走廊 lane index 严格递增；
  R3 同 gap 列 `|Δy| ≥ 0.525`；REFCLK 页间 ≥ 1.46。
- **A-W3.3 谓词**：双端 `|Δ| ≤ reach_avail(=45.4)`，且 `Σ|lane_y−row_y|` = DP 最优值（独立 DP 复核）。
- **A-W3.4 层语义**：数据页层链仅 `F.Cu/In2.Cu`，每线 via ≤ 2；REFCLK 层 = F.Cu；R4 字段零出现。
- **A-W3.5 序无关**：3 种输入枚举序（正序/倒序/哈希序）→ 输出**逐字节一致**。
- **A-W3.6 全有或证书**：`verdict=CERTIFICATE ⇒ landing_rows=null`；`FEASIBLE_ALL ⇒ 34 页齐 + landing 重发射`。
- **A-W3.7 白名单**：输出与工具代码中零出现反演/旧簿/x-window 键（grep 证据）。
- **A-W3.8 指纹**：9 输入全 64hex MATCH。

## 6. 禁令

禁 per-net first-fit（必须全局序典范式：DFS + DP + 穷举枚举）；禁把 PROVISIONAL landing 当输入；
禁用无源常数否定已签容量帧；禁 DRC 驱动/写板；禁原地改冻结件与已发布契约（改则版本 bump）。

## 7. 逃生门（不可行层的上游变更项）

1. R1.5：允许过渡段使用第二铜层（新增 via，层链变更）；2. R1.5：把「R1 via x 序与 lane 序一致」
   升为 **R1 准入约束**（需 F-13 域重发射）；3. 放宽 R1.5 的 `no_via`/`no_90deg`；
   4. F-5 修订（局部放开 lane 单调序，换 R1.5 平面性）。任一变更 = 上游输入变更 → 重跑全链。

End of W3-C1.
