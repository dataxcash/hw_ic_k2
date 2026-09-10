# m13 v57 — R1-REVIEW

> **架构师审核注记（2026-09-10，W0R-FIX.1 终态对齐，审核签收）**
> 本矩阵快照于 11:55，基于旧 W0-R（model sha `2a2dfdf7…`，`resource_kind=candidate_only`，
> verdict=`FEASIBLE_RESOURCE_ENVELOPE`）。W0R-FIX.1（15:01）已关闭 W0R-G1/G2/G3：
> REFCLK 升级为 `conservation_certificate`（required/available/shortage/conflicting_resources/
> minimal_core 齐备），verdict=`B1.5 PASS`（verdict_rule: no_third_state），
> `projection_evidence` 真实枚举 42 封装；validator 同步修订 W0R-FIX.1（F-10b 已闭）。
> 因此：C-5/C-6/C-7 对 W0-R 的候选态描述已过时，以 W0R-FIX.1 产物为准；
> §5 台账中 W0R-G1/G2/G3 三项 = **已闭**；I-3/C-4/F-A 与门链阻塞仍有效；
> F-1 = 已闭（条件性，条件见 D0 决策卡）；F-10 层语义裁决 = 仍待 D0。
> 其余 F-A/F-B(层)/F-2..F-13 判定不变，进入 D0/G3。

**副标题（原文）**：W1/W2 接口复核 × Schema Gap Matrix（manifest / W0-R / W1 / W2 → W3）

> 卡：**R1-REVIEW**（EDA_AUTONOMOUS_EXECUTION_PLAN_v2 §5；门控位 = G3 前置，v2 §2 G3 行）。
> 性质：**只读复核**。零委派、零分配输出、零冻结文件改动；本卡唯一写入 = 本文件。
> 日期：2026-09-10 ｜ k2 HEAD：**24e4cfd**（工作树隔离项保持不动：`M _shared` + 142 untracked，
> 依 m13_v57_baseline_correction §3）。
> 方法：对冻结源做**只读重放**（re-parse / 重聚合 / hash 链互证 / 几何包围盒实测），
> 不运行任何生成器写路径，不产出 page→lane/via/gap 的任何选择。

## 被复核源与指纹（sha256 前 16 hex，本卡实测）

| 文件 | sha256[:16] | 链上互证 |
|---|---|---|
| m13_v57_s1_page_manifest.json | `87c4c97378ff6f15` | = w0r_inputs.inputs_sha256.manifest = w2.inputs_sha.manifest(12hex) = landing.inputs_sha.manifest(12hex) ✓ |
| m13_v57_big_w0r_inputs.json | `4ca3e134407634dd` | = w0r_model.input_artifact_sha256 ✓ |
| m13_v57_big_w0r_corridor_model.json | `2a2dfdf76ffbb3b5` | = w0r_validation.model_sha256 ✓ |
| m13_v57_big_w0r_validation.json | `25c959eea9aa6d31` | verdict PASS / failures [] |
| m13_v57_big_w1_report.json | `554094cae313dfa6` | verdict PASS 200/200 |
| tools/p3_v57_big_w1_assign.py | `9e12fd794b57f663` | seed 20260909（仅在码内，未落报告 → F-11） |
| m13_v57_big_w2_connector_cols.json | `b3bbbfe26d9f6c55` | inputs_sha 仅 manifest、12hex 截断、缺 SPEC → F-11 |
| tools/p3_v57_big_w2_connector_cols.py | `1a7c2d9adaa5e7d2` | 读 manifest+SPEC，零板读 ✓ |
| m13_v57_s1_r1_via_verdict.json | `f20cfe24fcb7986b` | = landing.inputs_sha.verdict(12hex) ✓ |
| m13_v57_s1_chip_landing_rows.json | `08e2b8348e715257` | 64 行，PROVISIONAL（baseline_correction §4） |

hash 链结论：**manifest→W0-R→validation 与 manifest→W2、verdict→landing 的指纹链完整可重放**。
但 W2/landing 用 12hex 截断、W2 漏 SPEC 指纹（其 ac_wall 段实读 SPEC）——证据协议（v1 §3 条 2）不满。

---

## 0. 结论摘要（verdict）

1. **W1 = 合成契约核，非数据源**。200 合成实例（n≤6）上 kernel↔穷举 oracle↔MUS↔序无关全 PASS，
   契约形状（单射+无交叉+LEG 可达）可被 W3 复用；但**零真实绑定**：真实 lane 列、真实 row_y、
   真实 LEG 三个入参在生态中**均无权威发射者**（与架构师 v1 初查一致）。
2. **W2 = 可重放的列/簇原料块，非 R3/R4 候选域**。列/行/条目可从 manifest 纯重聚合复现；
   缺：R3 隙候选、出逃拓扑消费、R4 墙 pad 锚、冲突图/守恒、REFCLK pad（kind≠data 被过滤）。
3. **34 页可表示性**：32 数据页在 manifest/W0-R band/W2/R1 verdict/landing 五源**全有源**（§3 表
   逐页 YYYY）；2 REFCLK 页在 manifest/W0-R 锚有源且重放断言过，但 W3 级字段（层裁决、资源域、
   连接器落点）**有缺**（§3 表 Y---，逐项见 §2）。
4. **W0-R 阻塞传播**：G1 = BLOCKED（W0R-G1/G2/G3 未闭 + verdict 非终态）。凡依赖 W0-R 的 W3 字段
   **一律 BLOCKED-DEPENDENT**（§5 台账）；G2/G3/G4 sealed → **W3 整体不可开工**。
5. **本卡新增实测事实**（全部只读重放，供 W0R-FIX / D0 取证，不构成裁决）：
   - **F-A** AC 墙电容 **0/32 已放置**（C17-C32/C49-C64 不在板：18 个已放电容无一落于墙带或两走廊
     x 区间），且**不在 k2_sch 网表**（网表中 `AC17` 等为 U6 球名，非电容 refdes）→ R4 为
     “L2 声明、L1/L3 无实体”的悬空层。
   - **F-B** REFCLK 层语义**三处冲突**且被验证器锁死（§2.3 行 C-7 / F-10）。
   - **F-C** WEST 带 row_y **简并**（每带仅 2 个 distinct y，4 页同 y）→ W1 契约键退化（S-1）。
   - **F-D** J2 页 P/N pad **错位双列**（同页两 y）→ 页级 row_y 代表键未定（S-2）。
   - **F-E** 64 chip 锚全部落于 x∈[84.60,93.55]（U6 体 x[82.00,105.60] 的**西半**），含 EAST 走廊
     16 页 → “chip 出逃侧 ↔ 走廊侧”一致性无任何源断言（S-3）。
   - **F-F** 真实带实例 n=8 / 联合 n=16 **超出 W1 穷举 oracle 上限（n≤7）**，从未被独立对照（S-5）。

---

## 1. W3 目标接口形状（冻结依据，非本卡发明）

依据：`m13_v57_s1_generator_design.md` §1-§5（R1-R4 编码 / 守恒 / 发射模板 / 证书 / chip_landing
接口）、`m13_v57_board_intent_generator_design.md` §2-§5、v1 §6 G4-G7、v2 §2 G3/G4 行。

**W3 消费**（每资源层所需字段 → 应然来源）：

| 层 | W3 所需字段 | 应然来源 |
|---|---|---|
| R1 芯片出逃列域 | chip 锚 pad_global、via 候选列 cands、列对错距≥0.36、escape_transition_zone 规则（pitch0.4/no_via/no_90deg/微净空0.075） | manifest.anchors.chip + r1_verdict + SPEC.constraints |
| R2 走廊 lane | usable_y_spans、lane 帧（bands[{id,n,edge}]、margin、band_base）、lane_y[]、LEG 可达预算、page→row_y 键 | W0-R（span）+ **lane 帧发射者（缺，F-3）** + W1 契约 |
| R3 连接器出逃隙 | 列/行/条目、隙候选（pad 行 y±半行距可落 via 的 x 列）、出逃拓扑（内列左出/外列右绕）、每 pad 恰 1 落点守恒 | W2（原料）+ SPEC.constraints.j2_escape_topology + **隙候选生成（缺，F-8）** |
| R4 AC 墙穿越隙 | 墙 pad 锚（每网 1 pad，强节点）、min_center_pitch、墙隙微净空域 | **无权威源（缺，F-9：未放置+不在网表）**；SPEC.capacitor_walls 仅声明带 |
| REFCLK | 层裁决、每走廊资源域（In2 隔离带 或 F.Cu 带外+禁入谓词）、量化证书、J2/J3/J4 落点、跨走廊跨越段 | W0-R.refclk_resource_domain（BLOCKED）+ W2（不含 REFCLK pad → 缺） |
| 输出 | drawings[34]{nodes{P,N}有序点列, 段层, via 表, 强节点索引} + chip_landing_rows 重发射；或单一全局最小证书 | S1 设计 §3/§4/§5；证书 canonical schema 待统一（F-2） |

---

## 2. 字段级 gap matrix

状态词表：**OK**（已冻结可直接消费）｜**OK-REPLAY**（可被独立验证器重放断言）｜**GAP**（字段缺失/
语义未定，需 G3 前补齐或裁决）｜**PROVISIONAL**（存在但临时，禁止作约束性输入）｜
**BLOCKED-DEPENDENT**（依赖 W0-R 终态，G1 未闭即不可消费）｜**CONFLICT**（多源冲突需裁决）｜
**FORBIDDEN-REVERSE**（派生物/反演值，永禁当权威，见 §4-B）。

### 2.1 manifest（`m13_v57_s1_page_manifest.json`，87c4c973…）→ W3

| # | 字段 | 事实源 | W3 消费者 | 状态 | 缺口 / 说明 |
|---|---|---|---|---|---|
| M-1 | pages[].page_id/base/segname/kind/side | manifest（S0 端点模型 614bc907…×sch 70448241…派生） | 全层键控 | OK-REPLAY | 34 页、tally{16/8/8/2} 与页面枚举一致（本卡重放 ✓） |
| M-2 | nets{P,N} | 同上 | 图纸网名、landing 命名空间键 | OK-REPLAY | — |
| M-3 | anchors.chip.P/N{ball,ball_grid,net,pad_global,source} | s0_endpoint_model.chip_audit（64/64 对证） | R1 | OK | 但**侧向一致性无断言**：全部 x∈[84.60,93.55] 西半簇（F-E/S-3）→ 需 corridor 入口映射字段或裁决（F-7） |
| M-4 | anchors.conn.P/N{ref,pin,pad_num,pad_global,source}（数据页） | s0_endpoint_model.connector_audit | R2 row_y、R3 | OK | 页级单 row_y 代表键未定（J2 P/N 错位，S-2 → F-5） |
| M-5 | anchors.conn + conn2（REFCLK 页；conn2.source=s0_method_net_join 补录） | connector_audit + 网表双端成员补录 | REFCLK 模板 | OK-REPLAY | v2 §1 已清 WEST 端点疑虑；W0-R validator 重放锚断言过 ✓ |
| M-6 | corridor{id,band} | manifest 派生规则 | R2 带成员 | OK | WEST band 语义 vs J3/J4 双簇未裁（S-1 → F-5） |
| M-7 | **req_layers** | S1 设计 §0.1 声明的 manifest 字段 | 层选择 | **GAP** | 设计文档列出但**工件未发射**；现行层语义散落 S1 §2.3（数据 F→In2→F；REFCLK In2 替代 In6）与 W0-R（REFCLK F.Cu candidate）→ 并入 F-10 裁决后补字段 |
| M-8 | authority/basis/inputs_sha/n_pages/tally | manifest | 证据协议 | OK-REPLAY | 12hex 截断（同 F-11 口径统一） |

### 2.2 W0-R inputs（`m13_v57_big_w0r_inputs.json`，4ca3e134…）→ W3

| # | 字段 | 事实源 | W3 消费者 | 状态 | 缺口 / 说明 |
|---|---|---|---|---|---|
| I-1 | authority{4 源分类} | inputs.authority | 输入白名单 | OK | SPEC/manifest/PCB(放置+体几何)/drc_rules |
| I-2 | board.outline_y[33,79]/inner_y[33.3,78.7]/stackup 6L | SPEC.board（3bdecb10…） | R2 span 基线 | OK-REPLAY | validator 以 outline±0.3 重算 inner ✓ |
| I-3 | **corridor_x_ranges_pending_l2_ruling** EAST[105.25,132.65]/WEST[65.05,82.35] | 现 SPEC 值作参数（v58 §a“待几何核验”） | R2 lane 入出口 bound_x、体投影域、REFCLK x_range | **BLOCKED-DEPENDENT** | 待 L2 裁决。本卡只读实测（供裁决取证）：WEST.west 65.05 = J3/J4 体包围盒东缘（精确）；WEST.east 82.35 ≈ U6 西缘 82.00+0.35；EAST.east 132.65 = J2 内列 pad x；EAST.west 105.25 ≈ U6 东缘 105.60−0.35 —— 与放置几何一致，但**裁决权在 D0/L2，非本卡** |
| I-4 | rules.pair_pitch 1.46 / body_clearance 0.175 / edge_clearance 0.3 | drc_rules.json（0a459839…） | R2 守恒、投影 | OK-REPLAY | — |
| I-5 | keepouts{m3_absent, policy} | SPEC.constraints.m3_keepout_mm + PCB 重扫 | span 减除 | OK-REPLAY | validator 断言 m3_presence ✓ |
| I-6 | explicit_non_inputs[5] | 卡面纪律（A1.4/L4） | W3 输入白名单继承 | OK | W3 冻结契约必须原样继承此表（§4-B） |
| I-7 | inputs_sha256（全 64hex ×4） | W0-R | 证据协议 | OK-REPLAY | **W3 契约应以此为指纹标准**（W2/landing 的 12hex 需对齐，F-11） |

### 2.3 W0-R corridor model（`m13_v57_big_w0r_corridor_model.json`，2a2dfdf7…）→ W3

| # | 字段 | 事实源 | W3 消费者 | 状态 | 缺口 / 说明 |
|---|---|---|---|---|---|
| C-1 | corridors.*.usable_y_spans [[33.3,78.7]] | 板框−体投影（生成器）；validator 独立重算（bodies()+subtract） | R2 lane 帧 span | **BLOCKED-DEPENDENT** | W0R-G3：生成器侧未发射投影谓词/源 hash/被检器件清单（空结果无证明）；且其值以 I-3 pending x_range 为条件 —— **若 D0 裁令放置 AC 墙（F-A），j2_side 带 x[93,128]∩EAST、mcio_side 带 x[75,90]∩WEST 的电容体将把 span 切成多段，联合帧 21.9mm 连续需求可能翻转为不可行** → span 消费必须等 G1 终态+D0 |
| C-2 | data_bands.{up,dn}{n_pairs=8,centre_span_needed_mm=10.22,feasible,candidate_spans,page_ids} | manifest 成员 + (n−1)·1.46 守恒 | R2 带需求 | OK-REPLAY / 终态 BLOCKED-DEPENDENT | 数值可重放（本卡复算 ✓：10.22=(8−1)×1.46）；但 feasible 的终态性随 C-6 非终态而悬置 |
| C-3 | joint_data_frame{band_order[up,dn],n_pairs=16,centre_span_needed_mm=21.9,feasible} | 同上 | R2 联合帧 | **GAP + BLOCKED-DEPENDENT** | 缺 **edge(lo/hi) 映射** 与 **band_base 对齐规则**（lane_kernel 需 bands[{id,n,edge}]；board-intent §3.2 的“端锚 y 带投影+对齐规则定 band_base_y”从未机器发射）。WEST 联合帧在 row 简并（S-1）下 band_order 语义未定 → F-3/F-5 |
| C-4 | **lane_y[]（真实 lane 位）** | 应由 W0-R（或其后继）经 lane_kernel(frame) 构造发射 | R2 指派、W1 实绑定、图纸走廊段 | **GAP（生态级缺失）** | 全生态无任何工件发射真实 K2 lane 位；lane_kernel 已具备构造能力但 frame 入参（margin、edge、band_base）无权威源：旧 W0 margin=0.6 与 reach 12.0 已被 v1 初查判定“无锁定权威” → F-3 + BLOCKED-DEPENDENT |
| C-5 | refclk_resource_domain{anchors×2,layer=F.Cu,resource_kind=candidate_only,x_range,reason} | manifest conn/conn2 重放（validator ✓） | REFCLK 页全部 W3 字段 | **BLOCKED-DEPENDENT + CONFLICT** | W0R-G1：无 required/available/shortage/conflicts/minimal_core 量化证书；层语义三处冲突（S1 设计 §2.3=In2.Cu；board-intent §2={F.Cu,In2} 分配器裁决；W0-R=F.Cu candidate）→ F-10 |
| C-6 | certificates[] = 空 + verdict=FEASIBLE_RESOURCE_ENVELOPE | W0-R | G1/G2 门 | **BLOCKED-DEPENDENT** | W0R-G2：非两终态（B1.5 PASS / B1.5 INFEASIBLE_CERT）之一；W3 的“全 34 页 or 全局证书”入口条件悬置 |
| C-7 | validator 证书 schema {kind,blocked,corridor,band,required,available,shortage,conflicts,canonical_core,escape_hatches} | p3_v57_big_w0r_validator.py | W0R-FIX 目标 schema | **CONFLICT（接口风险）** | ① 与 S1 设计 §4 证书（cert_id/infeasible_layer/page_id/resources/demand/blockers/minimal_core/why_no_alloc_possible）及 board-intent §4（demand{needed_mm,avail_mm,short_mm}/why/escape_hatches）**三格式字段名不一致** → G3 必须裁单一 canonical（F-2）；② validator 现锁死 `resource_kind=="candidate_only"`（refclk_overclaim 检查）且 `refclk_layer != data_layer`（即 **In2.Cu REFCLK 结构性无法过验**）——W0R-FIX 升级为量化证书/In2 隔离带时**必须同步修 validator**，否则修复即违约（F-10b） |
| C-8 | blocked_component_projections[] | PCB 体投影（validator 独立重算=空 ✓） | span 减除证明 | **BLOCKED-DEPENDENT** | W0R-G3：生成器侧证据（谓词+源 hash+被检清单）未发射；validator 侧已独立重放为空（本卡确认其 bodies() 不含未放置电容 → 与 F-A 一致：空是“真减除的空”，但**条件是墙不放置**） |
| C-9 | schema=1 / input_artifact_sha256 / double_run_contract | W0-R | 证据协议 | OK-REPLAY | 双跑契约声明在案；重放链 ✓ |

### 2.4 W1（`tools/p3_v57_big_w1_assign.py` 9e12fd79… + `m13_v57_big_w1_report.json` 554094ca…）→ W3

| # | 字段 | 事实源 | W3 消费者 | 状态 | 缺口 / 说明 |
|---|---|---|---|---|---|
| W1-1 | 契约 pages=[(id,row_y)] | 应然：manifest conn 锚 y | R2 指派左端 | **GAP（绑定）** | 真实 row_y 代表键未定：J2 页 P/N 错位双列（EAST 每带 16 pad 仅 12 distinct y；UP0：N 43.5@内列 / P 42.9@外列）→ 页级键需裁决（P pad y？对中点？）（S-2/F-5） |
| W1-2 | 契约 lanes=[y] | 应然：W0-R lane 帧 | R2 指派右端 | **GAP + BLOCKED-DEPENDENT** | 真实 lane 列不存在（C-4）；依赖 W0-R 终态 |
| W1-3 | 契约 leg（LEG 可达预算） | **无权威源** | R2 可达准入 | **GAP + BLOCKED-DEPENDENT** | 合成值 {1.46,2.92,4.38,7.3}；旧 W0 的 12.0 已被 v1 判“无锁定权威”；真实 LEG 需两端（chip_row_y + conn_row_y → lane_y）预算，而 W1 契约**只建模 conn 单端**（S-4/F-6） |
| W1-4 | kernel_feasible（贪心最早可行，区间严格递增=该结构精确） | W1 码内 | W3 判定核 | OK（算法级） | 结构精确性主张仅经 n≤6 合成对照；n=8/16 未对照（S-5/F-4） |
| W1-5 | oracle_feasible（全排列，n≤7 上限） | W1 码内 | 独立验证 | **GAP（真实规模不可用）** | 16!/(16−n)! 组合爆炸 → 真实带 n=8、联合 n=16 的独立验证器**必须换结构**（区间二分匹配/Hall 判据/独立 DP），且 MUS 口径须与 W1 一致（基数升序、id 元组字典序）（F-4） |
| W1-6 | mus()（inclusion-min，两实现同口径） | W1 码内 | 证书最小核 | OK（算法级） | 真实实例 MUS 发射依赖 W1-1..3 绑定 → BLOCKED-DEPENDENT |
| W1-7 | 序无关（3 枚举序同判定，200/200） | w1_report.order_invariant | A1.2 同纪律 | OK-REPLAY | 固定 seed 20260909 重放可断言；**seed 未落报告**（F-11） |
| W1-8 | 报告证据字段 | w1_report | 证据协议 v1 §3 | **GAP** | 缺 schema/version、producer/validator 版本、seed 落盘；合成件无源指纹可理解，但 G3 冻结契约须补齐字段位 |
| W1-9 | WEST 行键简并 | manifest/W2 实测 | R2+R3 联合 | **GAP（语义）** | WEST 每带 distinct row_y = 2（dn：45.75×4页@J3、61.45×4页@J4；up：43.25×4、63.95×4；同 y 页仅 x 列不同）→ (row,id) 排序下 4 页并列，lane 序退化为纯 id 序，**几何上不可辨**；需按簇分帧或行键=(cluster_y,x) 裁决（S-1/F-5） |

### 2.5 W2（`tools/p3_v57_big_w2_connector_cols.py` 1a7c2d9a… + `m13_v57_big_w2_connector_cols.json` b3bbbfe2…）→ W3

| # | 字段 | 事实源 | W3 消费者 | 状态 | 缺口 / 说明 |
|---|---|---|---|---|---|
| W2-1 | connectors.J2{132.65,135.0}×{n_pads=16,rows,entries[net,pin,pad_num,y,pol,page]} | manifest conn 锚纯重聚合（round3） | R3 原料（EAST 16 页） | OK-REPLAY | 本卡重放 ✓：J2 32 pad = 16 页×P/N；内列 x=SPEC.j2_escape_topology.inner_col_x ✓ |
| W2-2 | connectors.J3/J4 8 列×2 pad | 同上 | R3 原料（WEST 16 页） | OK-REPLAY | J3=UP0-3/input(y43.25)+DN0-3/out_MCIO(y45.75)；J4=DN4-7/out_MCIO(y61.45)+UP4-7/input(y63.95)；行简并见 W1-9 |
| W2-3 | ac_wall_declared{mcio_side_x[75,90],j2_side_x[93,128],upper[44,47],lower[60,66],pitch1.3} | SPEC.capacitor_walls 复读 | R4 声明带 | **PROVISIONAL** | ① 声明≠实体：**墙电容 0/32 放置、0/32 在网表**（F-A 实测）；② SPEC 自检 FAIL 38 含 G2 lane1.2×28（声明 1.3 vs 实测 1.2 口径）；③ pitch_basis 自注“实测 1.2 中心距→pad 间距 0.1<…”——R4 守恒依赖声明间距成立，声明本身待 D0（F-9） |
| W2-4 | **R3 隙候选**（每 pad 行 y±半行距可落 via 的 x 列，经 pad 铜+净空判据） | 应然：S1 设计 §R3 推导 3 | R3 资源域 | **GAP** | W2 未派生（架构师 v1 初查同判：“data block, not R3/R4 candidate domains”）→ F-8 |
| W2-5 | **出逃拓扑消费**（内列左出 F.Cu / 外列右绕 In2、outer_route_x 142.5 等） | SPEC.constraints.j2_escape_topology（存在，11 键） | R3 方向语义 | **GAP（未消费）+ 部分 FORBIDDEN-REVERSE** | W2/W1 均未读取；且其中 `outer_escape` 内嵌 “v25 求解器分配 vx∈[131.7,136.0]” = **求解器反演值**，消费时只可取拓扑语义（内/外列方向），禁取 vx 区间当权威（§4-B） |
| W2-6 | **R4 墙 pad 锚**（每网 1 墙 pad = 强节点坐标） | 应然：SPEC refdes ∩ 网表 `_MCIO` 网（derive_cap_wall_pads 语义） | R4 强节点 | **GAP（硬）** | 物理未放置+网表无成员 → 无任何冻结源可发射 pad 坐标；W3 西页模板“F.Cu pad(R4) 微净空接入→墙 pad”**当前不可表示** → 只能由 D0/L2 补输入（放置+网表）或裁 R4 出链（F-9） |
| W2-7 | REFCLK 连接器 pad（J2 11/12/29/30、J3 A11/A12、J4 A11/A12） | manifest conn/conn2（有源） | REFCLK R3 落点 | **GAP（W2 过滤）** | W2 `kind!="data"` 跳过 → REFCLK 落点列/行数据缺失；manifest 侧坐标在（§3 REFCLK 行），需 W2 后继纳入（F-8b） |
| W2-8 | 冲突图/守恒（同列相邻落点 y 距 ≥ via_od+clearance；每 pad 恰 1 落点） | 应然：S1 设计 §R3 守恒 | R3 判定 | **GAP** | 未发射（F-8） |
| W2-9 | inputs_sha{manifest:12hex} | W2 | 证据协议 | **GAP** | 缺 SPEC 指纹（ac_wall 实读 SPEC）、12hex 截断、无 schema/producer 字段（F-11） |

### 2.6 R1 verdict + landing（f20cfe24… / 08e2b834…）→ W3

| # | 字段 | 事实源 | W3 消费者 | 状态 | 缺口 / 说明 |
|---|---|---|---|---|---|
| V-1 | pages.{32 页}.P/N.cands（0.05 步 via 候选场，0.15..1.5mm） | ballmap（3f096af1…）×放置×params | R1 候选 | OK-REPLAY | 32/32 ESCAPABLE；参数已录 {clr0.2,via_od0.35,via_via0.525} |
| V-2 | params 口径映射 | r1_verdict.params | R1 判据 | **GAP（溯源）** | 设计口径 = clearance0.175+半线宽0.1025 膨胀、列对错距≥0.36；verdict 用 clr0.2 —— 参数↔规则文件的映射断言未发射（inputs_sha 仅 ballmap，缺 rules/manifest 指纹）→ F-11/F-13 |
| V-3 | **列对耦合**（P/N 两列错距≥0.36 的成对约束） | 应然：S1 设计 §R1 | R1 联合判定 | **GAP** | cands 按单网发射，无 pair 级约束字段；W3 联合指派需自行施加 → 契约字段应在 G3 冻结（F-13） |
| V-4 | landing rows{net,method:VIA_IN2,pad,landing,signal,ball,status}×64 | verdict cands 的**逐页 canonical 选择** | S2 chip_landing 命名空间 | **PROVISIONAL** | baseline_correction §4：逐页选择=临时，**W3 联合指派必须取代之并重发射**；禁作 W3 约束性输入（顺序耦合禁入）（F-12） |

---

## 3. 34 页可表示性枚举（真实页，逐页）

覆盖标记：**M**=manifest 页记录｜**W0**=W0-R 带成员/REFCLK 锚｜**W2**=连接器列条目｜
**R1**=via verdict 候选｜**LD**=landing 行（PROVISIONAL）。数据页 32 全部 M/W0/W2/R1/LD 五源齐；
REFCLK 2 页 M/W0 两源齐（W2/R1/LD 按设计不适用——无 chip 端、被 W2 kind 过滤，属 F-8b 缺口而非违例）。

| # | page_id | kind | corridor/band | M | W0 | W2 | R1 | LD | W3 级缺口摘要（字段号） |
|---|---|---|---|---|---|---|---|---|---|
| 0 | PCIE_DN0/input | data | EAST/dn | Y | Y | Y | Y | Y | R2:C-3/C-4/W1-2·R3:W2-4/W1-1·过渡段:S-3 |
| 1 | PCIE_DN0/out_MCIO | data | WEST/dn | Y | Y | Y | Y | Y | R2:W1-9·R3:W2-4·**R4:W2-6 硬缺** |
| 2 | PCIE_DN1/input | data | EAST/dn | Y | Y | Y | Y | Y | 同 #0 |
| 3 | PCIE_DN1/out_MCIO | data | WEST/dn | Y | Y | Y | Y | Y | 同 #1 |
| 4 | PCIE_DN2/input | data | EAST/dn | Y | Y | Y | Y | Y | 同 #0 |
| 5 | PCIE_DN2/out_MCIO | data | WEST/dn | Y | Y | Y | Y | Y | 同 #1 |
| 6 | PCIE_DN3/input | data | EAST/dn | Y | Y | Y | Y | Y | 同 #0 |
| 7 | PCIE_DN3/out_MCIO | data | WEST/dn | Y | Y | Y | Y | Y | 同 #1 |
| 8 | PCIE_DN4/input | data | EAST/dn | Y | Y | Y | Y | Y | 同 #0 |
| 9 | PCIE_DN4/out_MCIO | data | WEST/dn | Y | Y | Y | Y | Y | 同 #1（J4 簇） |
| 10 | PCIE_DN5/input | data | EAST/dn | Y | Y | Y | Y | Y | 同 #0 |
| 11 | PCIE_DN5/out_MCIO | data | WEST/dn | Y | Y | Y | Y | Y | 同 #1（J4 簇） |
| 12 | PCIE_DN6/input | data | EAST/dn | Y | Y | Y | Y | Y | 同 #0 |
| 13 | PCIE_DN6/out_MCIO | data | WEST/dn | Y | Y | Y | Y | Y | 同 #1（J4 簇） |
| 14 | PCIE_DN7/input | data | EAST/dn | Y | Y | Y | Y | Y | 同 #0 |
| 15 | PCIE_DN7/out_MCIO | data | WEST/dn | Y | Y | Y | Y | Y | 同 #1（J4 簇） |
| 16 | PCIE_REFCLK0/input | refclk_pass | EAST+WEST/refclk | Y | Y(锚×2廊) | — | — | — | 层裁决 C-5/F-10·资源域 W0R-G1·落点 W2-7·跨越段:C-4 |
| 17 | PCIE_REFCLK1/input | refclk_pass | EAST+WEST/refclk | Y | Y(锚×2廊) | — | — | — | 同 #16 |
| 18 | PCIE_UP0/input | data | WEST/up | Y | Y | Y | Y | Y | R2:W1-9·R3:W2-4·**R4:W2-6 硬缺** |
| 19 | PCIE_UP0/out_J2 | data | EAST/up | Y | Y | Y | Y | Y | R2:C-3/C-4/W1-1·R3:W2-4/W2-5·过渡段:S-3 |
| 20 | PCIE_UP1/input | data | WEST/up | Y | Y | Y | Y | Y | 同 #18 |
| 21 | PCIE_UP1/out_J2 | data | EAST/up | Y | Y | Y | Y | Y | 同 #19 |
| 22 | PCIE_UP2/input | data | WEST/up | Y | Y | Y | Y | Y | 同 #18 |
| 23 | PCIE_UP2/out_J2 | data | EAST/up | Y | Y | Y | Y | Y | 同 #19 |
| 24 | PCIE_UP3/input | data | WEST/up | Y | Y | Y | Y | Y | 同 #18（J3 簇） |
| 25 | PCIE_UP3/out_J2 | data | EAST/up | Y | Y | Y | Y | Y | 同 #19 |
| 26 | PCIE_UP4/input | data | WEST/up | Y | Y | Y | Y | Y | 同 #18（J4 簇） |
| 27 | PCIE_UP4/out_J2 | data | EAST/up | Y | Y | Y | Y | Y | 同 #19 |
| 28 | PCIE_UP5/input | data | WEST/up | Y | Y | Y | Y | Y | 同 #18（J4 簇） |
| 29 | PCIE_UP5/out_J2 | data | EAST/up | Y | Y | Y | Y | Y | 同 #19 |
| 30 | PCIE_UP6/input | data | WEST/up | Y | Y | Y | Y | Y | 同 #18（J4 簇） |
| 31 | PCIE_UP6/out_J2 | data | EAST/up | Y | Y | Y | Y | Y | 同 #19 |
| 32 | PCIE_UP7/input | data | WEST/up | Y | Y | Y | Y | Y | 同 #18（J4 簇） |
| 33 | PCIE_UP7/out_J2 | data | EAST/up | Y | Y | Y | Y | Y | 同 #19 |

**计数断言（本卡重放）**：data=32（tally 16 input + 8 out_J2 + 8 out_MCIO ✓）+ refclk_pass=2 = **34 页全部可表示**；
W0-R 带覆盖 32/32 + REFCLK 锚 2/2（双走廊各 2 锚，validator 对 manifest 重放断言过）；W2 覆盖 32/32；
R1 verdict 32/32；landing 32 页×P/N=64 行。

### 3.1 带几何事实（重放自 manifest/W2，供 F 项裁决；非分配）

| 带（corridor/band） | 页数 | conn 行 y（distinct） | chip 锚 y | chip 锚 x |
|---|---|---|---|---|
| EAST/dn（DN*/input→J2） | 8 | 12 个（54.3..64.5，P/N 错位） | 57.12-57.64 | 84.85-93.55 |
| EAST/up（UP*/out_J2→J2） | 8 | 12 个（42.9..53.1，P/N 错位） | 55.13-55.82 | 84.60-93.40 |
| WEST/dn（DN*/out_MCIO→J3/J4） | 8 | **2 个**（45.75×4页@J3、61.45×4页@J4） | 51.67-52.37 | 84.60-93.40 |
| WEST/up（UP*/input←J3/J4） | 8 | **2 个**（43.25×4、63.95×4） | 49.76-50.28 | 84.85-93.55 |
| REFCLK×2 | 2 | J3 A11/A12(45.75)↔J2 11/12(45.9)；J4 A11/A12(61.45)↔J2 29/30(51.3) | 无 chip 端 | — |

### 3.2 结构性发现（S-x，字段级，全部只读实测）

- **S-1 WEST 行键简并**：W1 契约键 row_y 在 WEST 每带只有 2 个值、4 页并列（区分维是 x 列与簇归属，
  非 y）→ “row 升序→lane 升序”在 WEST 失去几何含义；需按 J3/J4 簇分帧或复合行键裁决（F-5）。
- **S-2 J2 P/N 错位**：EAST 页 P/N pad 分居内/外列（x 132.65/135.0）且 y 常差 0.6 → 页级单 row_y
  代表键未定（F-5）。
- **S-3 chip 锚全西簇 vs EAST 走廊语义**：64 chip pad 全在 U6 体（x[82.00,105.60]）西半
  x∈[84.60,93.55]、四行 y 带；EAST 16 页的 S1 模板“via₁→In2 段至 lane 入口(105.25,lane_y)”
  隐含一段**穿芯片体下方/绕行的过渡段**（x≈93.5→105.25），该过渡区**不在 R1-R4 任何资源层编码内**，
  其碰撞守恒（32 页 In2 过渡段互斥 + escape_transition_zone 的 no_via/no_90deg 约束域）无字段承载
  → F-7。R1 设计文本“芯片每侧（东=入口 105.25/西=入口 82.35）出逃列”与实测锚分布不符，需裁决
  corridor 入口映射或增过渡段模板。
- **S-4 两端可达性未建模**：lane_y 同时受 chip 行 y 与 conn 行 y 两端约束（设计 §3.1“两端锚定”），
  W1 契约仅 conn 单端 + LEG → F-6。
- **S-5 规模越界**：真实带 n=8、联合 n=16 > W1 穷举 oracle 上限 n≤7；200 合成实例 n∈[1,6]
  → 真实规模从未被独立结构对照 → F-4。
- **S-6 REFCLK J2 行落数据行区**：REFCLK J2 行 45.9/51.3 落在 EAST/up 数据行区 [42.9,53.1] 内 →
  若 REFCLK 走 In2（S1 §2.3 口径），其 lane 须与数据 lane 保≥1.46 隔离，位置受 band_base/edge 裁决
  直接影响（旧 W0 曾就此发 4 证书；W0-R 改 F.Cu candidate_only 未量化）→ 并入 F-3/F-10。

---

## 4. 独立验证器边界

### 4-A 可重放断言（独立验证器可从冻结源重算，禁 import 生成器）

| 断言 | 重放方法 | 现状 |
|---|---|---|
| manifest 34 页/tally/锚坐标 ↔ S0 端点模型 | inputs_sha 链 + 逐字段 re-parse | 已有（A1 系/S0 审计） |
| W0-R usable_y_spans / blocked_component_projections | PCB 体包围盒重解析 + 区间减除（validator.bodies/subtract 已独立实现） | 已有 ✓（G3 证据要求：投影谓词+被检清单落盘 → W0R-G3） |
| 带/联合容量守恒 need=(n−1)·1.46 vs span | 闭式重算 | 已有 ✓（本卡复算 10.22/21.9 一致） |
| band.page_ids ↔ manifest (corridor,band) 成员 | 集合对照 | 已有 ✓ |
| REFCLK 锚 ↔ manifest conn/conn2（j2_y/far_ref/far_y） | 逐字段对照 | 已有 ✓ |
| W2 列/行/条目 ↔ manifest conn pad_global 重聚合 | round3 重聚 + 逐条目 diff | 本卡已重放 ✓（应固化为 W2 独立验证器） |
| W2 ac_wall_declared ↔ SPEC.capacitor_walls | 复读对照（须先补 SPEC 指纹） | 半缺（F-11） |
| W1 kernel↔oracle↔MUS↔3 序 | seed 20260909 重放 + 双跑字节一致 | 已有 ✓（seed 落盘缺，F-11） |
| R1 verdict cands ↔ ballmap×params | 0.05 网格重演（params 已录） | 可建（参数溯源 F-13） |
| landing rows ↔ verdict+manifest | 逐行来源对照 | 可建；**行值本身 PROVISIONAL 不得断言为终值** |
| 全部 sha256 链 | 重哈希 | 本卡已过 ✓ |

### 4-B 禁止反推（派生物/反演值，永禁当权威源；W3 输入白名单必须继承 w0r_inputs.explicit_non_inputs）

| 禁项 | 依据 |
|---|---|
| SPEC.corridors.tracks_y（12 处，v32 求解器反演值） | S1 设计 §R2“只作对照参考”；w0r explicit_non_inputs |
| 板铜 tracks/vias/zones | w0r explicit_non_inputs；L4 单向 |
| 旧 lane 簿 v53/v54（EscapeTable/ColumnBook/construction_fact）、escape_spec 几何（S0 已作废：32 坐标帧错+32 stub 网名不在网表） | S1 设计 §5；S0 审计 |
| max-x / x-window 反猜端点 | A1.4；铁律 L4 |
| SPEC.j2_escape_topology.outer_escape 内嵌 “vx∈[131.7,136.0]”（v25 求解器分配记录） | 求解器输出=派生物；仅拓扑语义（内/外列方向）可经裁决后作规则注入 |
| chip_landing_rows 现行 canonical P/N 选择 | PROVISIONAL（baseline_correction §4）；顺序耦合禁入 |
| W2 ac_wall_declared 当“已核验几何” | 声明带；实体 0/32（F-A）；pitch 口径在 SPEC 自检 FAIL 38 之列 |
| W0-R refclk layer=F.Cu 当“已裁层” | resource_kind=candidate_only 自declared；层裁决属 D0/F-10 |
| W0-R verdict=FEASIBLE_RESOURCE_ENVELOPE 当终态 | W0R-G2；两终态之外皆 BLOCKED |

### 4-C 真实规模（n=8/16）独立验证的结构性要求（G4 前置）

排列 oracle 在 n≥8 计算上不可行（W1 自注 n≤7）。W3 的 R2 指派独立验证器必须：
① 与 kernel **结构独立**（禁共享排序/选择逻辑）；② 多项式判据（区间二分图匹配/Hall 型守恒/独立 DP
任一，判定与 kernel 逐实例一致）；③ MUS 口径与 W1 相同（基数升序、id 元组字典序，唯一 inclusion-min）；
④ 3 枚举序字节一致 + 双跑字节一致；⑤ seed/参数/源指纹全部落报告。

---

## 5. W0-R 阻塞传播（BLOCKED-DEPENDENT 台账）

前提（v2 §0/§1，本卡确认未变）：G1 = **BLOCKED**；W0R-G1/G2/G3 开放；verdict 非终态；
G2 sealed → D0 未发；G3 sealed →（本矩阵 = G3 前置件之一）；G4 sealed → **W3 不得开工**。

| 阻塞源 | 被阻塞的 W3 字段（传播闭包） | 状态 |
|---|---|---|
| W0R-G1（REFCLK 无量化证书） | REFCLK 2 页×2 走廊：layer、隔离带/F.Cu 带外谓词、required/available/shortage/minimal_core、REFCLK lane_y、跨越段几何、REFCLK R3 落点 | **BLOCKED-DEPENDENT** |
| W0R-G2（verdict 非终态） | “全 34 页可行”入口、全局证书入口、G4 点火条件 | **BLOCKED-DEPENDENT** |
| W0R-G3（投影空集无生成器侧证明） | usable_y_spans 消费（R2 lane 帧、带/联合 feasible 终值） | **BLOCKED-DEPENDENT**（validator 已独立重放为空；但门纪律=G1 未闭不得消费） |
| I-3 corridor x_range 待 L2 裁决 | lane 入出口 bound_x、图纸走廊段端点、体投影域、REFCLK x_range | **BLOCKED-DEPENDENT** |
| C-4 lane 帧未发射（margin/edge/band_base 无权威） | 全部 R2 lane_y、W1 实绑定（lanes/LEG/row 键）、S-6 REFCLK 隔离位、图纸走廊段 | **BLOCKED-DEPENDENT**（叠加 GAP） |
| F-A 墙电容未放置/不在网表（D0 关联） | WEST 32 墙 pad 强节点、R4 守恒、**以及若 D0 裁令放置 → C-1 span 全量重算（可行性可能翻转）** | **BLOCKED-DEPENDENT**（经 D0/G2） |
| 门链 G1→G2→G3→G4 | **W3 全部输出字段（34 页 drawings、chip_landing 重发射、任何证书）传递闭包** | **BLOCKED-DEPENDENT** |

**总括行**：在 G1 出终态（B1.5 PASS / B1.5 INFEASIBLE_CERT）且 G2=D0 continue 之前，
W3 的每一个依赖 W0/W0-R 的字段 = BLOCKED-DEPENDENT；W1/W2 的算法与原料可先行冻结契约（G3 本职），
但**不构成开工授权**（v1 §5：“Neither is authority to start W3 while W0 remains blocking”）。

---

## 6. G3 冻结前置项（F-1..F-13；裁决需求清单，本卡不做选择、不产分配）

| # | 前置项 | 归属 | 关联字段 |
|---|---|---|---|
| F-1 | W0R-FIX 关闭 G1/G2/G3 → G1 终态 | W0R-FIX 卡 | C-1..C-9 |
| F-2 | **证书 canonical schema 单一化**（validator 10 字段版 vs S1 §4 版 vs board-intent §4 版，三格式字段名对齐或分层映射表冻结） | 架构（G3） | C-7、W3 输出 |
| F-3 | lane 帧发射契约：bands[{id,n,edge}] + margin + band_base 对齐规则的**权威源与发射者**（lane_kernel 为构造器，frame 参数须落权威指纹） | W0R-FIX/D0 + G3 | C-3/C-4、W1-2 |
| F-4 | n=8/16 真实规模独立验证器（§4-C 五条件） | G3→G4 前置 | W1-4/W1-5 |
| F-5 | 行键裁决：J2 页级 row_y 代表键（S-2）+ WEST 簇简并键（cluster 分帧或 (cluster_y,x) 复合键）（S-1） | 架构（G3） | W1-1/W1-9、M-4/M-6 |
| F-6 | 两端可达性：LEG 单端预算 → chip_row+conn_row 两端谓词的契约扩展（S-4） | 架构（G3） | W1-3 |
| F-7 | chip 锚侧向 ↔ corridor 入口映射断言字段 + EAST 页过渡段（穿/绕芯片体）模板与守恒资源层（S-3；含 escape_transition_zone no_via/no_90deg 域归属） | 架构 + L2 取证（G3） | M-3、R1/R2 模板 |
| F-8 | R3 隙候选域生成器（W2 后继）：隙候选 + 每 pad 恰 1 落点守恒 + 冲突图（W2-4/W2-8）；F-8b：纳入 REFCLK pad（W2-7） | G3 后 W3 前置卡 | W2-4..W2-8 |
| F-9 | **R4 墙 pad 锚来源裁决**：墙电容 0/32 放置、0/32 在网表（F-A）→ D0/L2 选择：补网表+放置（触发 C-1 span 重算）或正式裁 R4 出链（SPEC 修订）；pitch 1.3 声明 vs 1.2 实测口径同裁 | **D0（L2）** | W2-3/W2-6 |
| F-10 | REFCLK 层语义三源冲突裁决（S1 §2.3 In2 vs board-intent {F.Cu,In2} 分配器 vs W0-R F.Cu candidate）；F-10b：validator 的 candidate_only/refclk_layer 锁必须与 W0R-FIX 同步修订，禁“修复即违约” | D0 + W0R-FIX | C-5/C-7、M-7 |
| F-11 | 证据协议补齐：W2 加 SPEC 全 64hex 指纹 + schema/producer 字段；W1 报告落 seed/versions/schema；manifest/landing 12hex → 64hex 对齐 | G3 冻结件修订 | W1-8/W2-9/V-2/M-8 |
| F-12 | chip_landing 重发射协议：W3 联合指派取代 PROVISIONAL 选择时，landing 行随图纸原子重发射（禁中间态入 S2） | G3 契约条款 | V-4 |
| F-13 | R1 参数溯源：verdict params{clr0.2,via_od0.35,via_via0.525} ↔ drc_rules/设计口径（0.175+0.1025、错距 0.36）映射断言 + 列对耦合字段（V-2/V-3） | G3 | V-2/V-3 |

---

## 7. 验收自检（对照 v2 §5 R1-REVIEW Acceptance）

- **matrix cites field-level sources** ✓：§2 每行含 文件.字段 + sha16 指纹；§0/§3 实测事实均注明重放方法。
- **34 pages enumerated** ✓：§3 逐页 34 行（32 data 五源齐 + 2 REFCLK 两源齐），计数断言与 tally 一致。
- **W0 block propagated** ✓：§5 台账逐项 BLOCKED-DEPENDENT + 全字段传递闭包总括行。
- **no allocation leaked** ✓：全文无任何 page→lane/via/gap/墙 pad 的选择结果；§3.1 仅为冻结源重聚合
  与包围盒事实；F 项仅为裁决需求，不含建议取值。
- **只读纪律** ✓：未改任何冻结文件；未运行生成器写路径；本卡唯一新文件 = 本矩阵（未 commit，
  提交时机由门控持有者定）。

—— R1-REVIEW 完（read-only；终态裁决权在 architect/G3 与 D0/L2）
