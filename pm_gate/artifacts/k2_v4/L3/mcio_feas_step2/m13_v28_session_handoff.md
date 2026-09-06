# M14 v28 — 层数定案流程终定：C3/C5 处置路径裁决（c = 维持缺口登记 + 对齐准备）

> 状态：**本 session = 承接 v27 未闭条件 C3/C5（同根 = DS320PR1601 原理图 ECO 未落地）的
> 路径裁决 + 模型驱动对齐准备（TASK MGR 终定流程）**。
> 用户裁决（2026-09-06）：**路径 c** —— C3/C5 如实登记缺口、不假闭合，mcio_feas 维持
> planned/S0 不 advance；本 session 只做可做的对齐准备（SPEC 再生草案到 /tmp + 注入样张
> 校验 = 生产模型真执行）。6L 判定维持引擎级 FEASIBLE 不变，**未流程终定，禁下传 L3**。
> 本 session 结果：**C3/C5 仍 ⏳（L3 前置/ECO 依赖）；对齐准备完成 = 生产 SPEC 本体级
> ⑦ 真执行机器证明（REGEN_DRAFT_PASS）+ 可复跑资产落盘**。

## 0. 裁决与授权（用户/架构）

- **裁决点（开工先问）**：DS320PR1601 原理图 ECO 是否已/将落地？现场核实：sch 全目录
  **0 命中 DS320PR1601**（DS160PR810/WQFN-64 旧符号仍在 v5 upstream/downstream 两页）、
  真板 k2_v4.kicad_pcb **0 命中** → **路径 a 不成立**（原理图未改）。用户未授权路径 b
  （本 session 生成原理图 ECO = 改冻结区 L0）→ **用户裁决走路径 c**：维持缺口登记 +
  对齐准备，不假闭合。mcio_feas 维持 planned/S0。

## 1. 现场基线（模型驱动前提核实，全部只读）

| 项 | 实测 | 意义 |
|---|---|---|
| sch DS320PR1601 命中 | 0（DS160PR810/WQFN-64 旧符号仍在） | C3/C5 依赖的 ECO 未落地 |
| k2_v4.kicad_pcb DS320PR1601 | 0；U3/U7 旧网名 `PCIE_DN_OUT*_U3/U7` 16 仍在 | 芯片级网表 = 旧双芯片布局 |
| 生产 SPEC redriver | 仅 U3/U7（role/pos/caps/footprint/channel_count/pad_groups，**无 bga_escape**）；stackup 8L、capacitor_walls 在位 | C3 本体对象 = 旧拓扑 |
| freeze_ctl.sh status | 0/0/0 全锁 | 冻结纪律维持 |
| k2/容器 git | v27 已 commit，工作区无 tracked 改动 | 真板数据源未变 → v27 核对有效 |

## 2. G1 学习闸（资产检索先行，模型驱动第一步）

- 命中 `corridor_pair_ds320pr1601_dual_band` **v5**（produced=true，per_ball_verdict=
  FEASIBLE，machine_ballmap_asset=ds320pr1601_ballmap.json 引用，known_gaps=C3/C5 +
  去耦 L3 项）= **已覆盖形态**，消费为先例（注入契约/口径/数字 1:1 引用 kb validation：
  ipair 1.46、32/32/16、11.68≤16.2/18.8、net 全 354 球 worst 0.6≥0.427）。
- 未覆盖/缺口：C3（SPEC 本体再生依赖 ECO）、C5（芯片级网表依赖 ECO）—— 与 kb known_gaps
  一致，本 session 维持登记，不发明替代结论。

## 3. C3 对齐准备（模型驱动：喂输入 → 生产模型真执行 → 读输出断言）

> 纪律：**不新写求解器、不自算判定**。全部几何/容量/净空判定出自生产 TOPO 模型
> `RoutingTopologyGate.plan()` v1.4（容器根 `_shared/eda_core` 权威引擎，C2 已入）；
> 新脚本仅做「spec 文档变换（注入）+ 调模型 + 断言模型输出」的壳（G3 证书边界）。

1. **/tmp 再生草案**：生产 `SPEC_k2_v4.json`（sha16 `7eaad223`）深拷贝 + 注入
   `components.redriver.DS320PR1601.bga_escape.per_ball`（354 ballmap 节点 **1:1 契约复用
   v27 POC 注入**，逐字节不手造；U3/U7 遗留项保留——ECO 完成换名前不覆盖，见
   C3_SPEC_REGEN_v27.md §4 注入注意）→ `/tmp/opencode/c3_spec_regen_draft/
   SPEC_k2_v4_ds320_draft.json`（sha16 `2f8ca81f`，260,724 B）。**边界**：草案 = 对齐准备
   样张，非终态再生（终态 = ECO 落地后 U3/U7 移除 + 8L→6L + 46mm 单面 + cap_wall 移除的
   全量对齐）；草案只落 /tmp，不碰生产 SPEC（冻结纪律）。
2. **生产模型真执行（本体级）**：`RoutingTopologyGate.plan()` v1.4 消费草案 →
   ```
   version=1.4  verdict=FEASIBLE_WITH_MORPH_GAP
   ⑦ BGA_PER_BALL_ESCAPE ok=True status=evaluated level=per_ball
     DS320PR1601: verdict=FEASIBLE signal=64 direct=32 via=32 crossing=16 deficits=0
   ```
   → **not_configured 假静默消除的 SPEC 本体级机器证明**（v27 POC 基于 SPEC 副本；本 session
   以当前生产 SPEC 本体深拷贝复证，比 v27 更贴近生产基线）。
3. **可复跑资产落盘（禁删）**：`reproduce_c3_spec_regen_draft.py`（本目录，确定性复跑输出
   REGEN_DRAFT_PASS，exit 0；sha 逐次一致）——下 session（ECO 后 SPEC 真再生）可直接复用：
   改 `--spec` 指向再生后 SPEC 并移除 U3/U7 遗留项重跑即可。
4. **v27 POC 资产复跑**：`reproduce_c3_plan_poc.py` → `POC_PASS`（exit 0），证据链延续。

## 4. C5 复核（真板网表核对 = 可核部分维持 + 芯片级缺口维持）

- **可核部分 ✅（无变化，结论有效）**：真板 `k2_v4.kicad_pcb` git 无 diff（数据源未变）→
  v27 BoardParser 核对结论（J3=DN_OUT0-3+UP0-3+REFCLK0 / J4=DN_OUT4-7+UP4-7+REFCLK1 =
  L1 frozen 一致）**仍有效**；抽样复核 `PCIE_DN_OUT0-7_{P,N}_MCIO` 16 网 + `PCIE_UP0-7_{P,N}`
  16 网 + `PCIE_REFCLK0/1` 在位，无漂移 → 引擎无需重跑 lane 子集。
- **不可核对 ⏳（缺口维持）**：DS320PR1601 ball→ASIC 内部 lane 映射——真板仍 U3/U7 旧网名
  （`PCIE_DN_OUT*_U3/U7` 16 实测在位），无 DS320PR1601 芯片网表对象 → **与 C3 同根：原理图
  ECO 落地后一次核对**。v26 评审已背书引擎对 lane 子集不敏感（最坏 64≤69），将来映射微调
  引擎单次重跑即可（禁暴力）。

## 5. 流程状态（如实登记，不假闭合）

- **C3 ⏳**（SPEC 本体再生 = L3 前置/ECO 依赖；本 session 完成 = 对齐草案 + 生产模型 ⑦
  evaluated FEASIBLE 的机器路径证明，未以草案冒充再生完成）。
- **C5 ⏳**（芯片级网表核对 = L3 前置/ECO 依赖；连接器级已核一致）。
- **mcio_feas 维持 planned/S0，不 advance**（条件未全闭，禁假推进）。
- **6L 判定**：维持引擎级 FEASIBLE（PASS_WITH_CONDITIONS），未流程终定，**禁以"6L 已终定"
  下传 L3**；L1/L2 frozen 表述（v27 降级版）无需再改。

## 6. G5 收尾自检

- **消费资产**：m13_v27 handoff §4/§5（缺口登记）+ REVIEW_ADVERSARIAL_v26（C3/C5 原条件）；
  kb `corridor_pair_ds320pr1601_dual_band` v5（produced 先例，只读 cp 副本查询，未写源库）；
  生产 RoutingTopologyGate v1.4 + escape_landing.bga_per_ball_escape（⑦ 判定唯一来源）；
  ds320pr1601_ballmap.json（354 ballmap 资产）；SPEC_k2_v4_c3poc.json（注入节点契约源）；
  reproduce_c3_plan_poc.py（POC 复跑）；C5_NETLIST_CHECK_v27.md（连接器级核对记录）；
  L1/L2 v2.0 frozen；EXECUTION_GATES G0-G5（G1 学习闸/G3 证书边界/G5 自检）；
  LAYOUT_CONSTITUTION（冻结纪律/禁自写求解器）；KNOWLEDGE_REUSE_SDD（kb 唯一事实源）。
- **未消费/缺口**：C3（SPEC 本体再生）、C5（芯片级网表）= 依赖 DS320PR1601 原理图 ECO 落地
  → 登记 L3 前置，非本 session 假闭合（与 kb known_gaps 一致）。mcio_feas 维持 planned/S0。
- **停止/熔断**：G4 未触发（无几何卡点空转——本 session 无几何求解，全为模型确定性执行）；
  模型执行均一次过（草案 ⑦ evaluated、POC_PASS、REGEN_DRAFT_PASS），无重试。
- **禁违反项**：✅ 未翻 6L 判定；未假闭合 C3/C5；未把"6L 已流程终定"下传 L3；未动冻结区
  （freeze 维持 0/0/0；kb 仅 cp 副本只读查询，未写源库）；引擎零改动（零 ECN）；
  生产 SPEC_k2_v4.json 未改（草案只落 /tmp）；新脚本 = 模型调用壳（G3），无新增求解逻辑；
  未把 L0-L3 已有答案抛用户（裁决点属 ECO 落地权属的产品/流程决策，按 brief 开工先问）。
- **边界声明**：本 session 后 6L = 引擎级 FEASIBLE + C1/C2/C4 闭合 + C3/C5 缺口登记 +
  **对齐准备 = 生产 SPEC 本体级 ⑦ 真执行机器证明（草案 sha 2f8ca81f + 可复跑资产
  reproduce_c3_spec_regen_draft.py REGEN_DRAFT_PASS）**；流程终定（= mcio_feas advance +
  kb produced 终态 + 可下传 L3）**仍待 DS320PR1601 真板 ECO → SPEC 全量再生（U3/U7 移除/
  6L/46mm/cap_wall 移除）→ ⑦ evaluated + C5 芯片级网表核对**。

## 7. commit 预备

- `_shared`（容器根 ic_hw_eda）：**无改动**（引擎零 ECN，kb 未写）→ 不 commit、不 bump。
- `k2`：`m13_v28_session_handoff.md`（本文件）+ `reproduce_c3_spec_regen_draft.py`
  （C3 对齐可复跑资产，v28 落盘）→ commit → 容器根 bump k2 gitlink。
- 注意：k2 内嵌 `_shared`（`?? _shared` untracked）为陈旧镜像/游离态，**不纳入本 commit**
  （历史惯例）；既有 untracked 文件（v10-v23 handoff、channel_alloc_diag、hs_rebuild_v11/v12
  等）为既往 session 未纳入项，**不夹带**，仅 add 本 session 2 文件。
- 冻结区在 git 前 unlock、后 lock（freeze_ctl.sh status = 0/0/0）。

## 8. v28 补记（同 session 延续：C3 对齐准备深化，2026-09-06）

> 用户「继续」后追加。仍在路径 c 授权范围（对齐准备），未越冻结区、未假闭合。产出 2 项：

1. **SPEC 再生差异清单**（`spec_regen_diff_checklist_v28.json`，本目录落盘）：生产 SPEC
   （sha `7eaad223`）现状 vs L1/L2 v2.0 冻结要求的逐字段对照 = ECO 后全量再生的**工作底稿**。
   机器提取现状 + 冻结出处引用：8 项 BLOCKED_BY_ECO（board 38→46mm / 8L→6L /
   `layer_plan.in6_usage`+`u3_side_bridges`+`chip_side_routes` 8L 语义残留 / capacitor_walls
   移除 / redriver U3+U7→DS320PR1601 / `*_U3/_U7` 网名 42 处 / per_ball 注入（PATH_PROVEN）/
   corridors 口径 1.46 校验）+ 1 项 NO_DIFF（impedance）。
2. **ECO 前置新缺口登记**（差异清单 item 10）：**DS320PR1601 符号/封装资产仓内缺失**——
   `_shared/schlib` 无、`k2/schlib` 不存在、现行 sch 仅 DS160PR810 WQFN-64 旧符号 →
   ECO 落地前置 = 先取得/建 DS320PR1601（nfBGA-354 ZDG）KiCad 符号+封装（354 球，来源与
   kb machine_ballmap_source 同源 TI 资产）。此缺口 kb known_gaps 未单列，补记于此；
   ECO 落地 session 首步即此。

   验证（模型驱动延续）：注入路径已由 v28 主 session 机器证明（草案 sha `2f8ca81f` →
   生产 plan() v1.4 ⑦ evaluated FEASIBLE；REGEN_DRAFT_PASS）。本补记不新增求解、不改任何
   冻结/引擎/生产 SPEC 文件。
3. **C5 芯片级核对期望矩阵**（`gen_c5_chip_expect_matrix.py` + `c5_chip_level_expect_matrix_v28.json`，
   本目录落盘）：C5 不可核部分（DS320PR1601 ball→ASIC lane）的前置准备。从
   `ds320pr1601_ballmap.json` 提取 K2 lanes 0-7 的 **64 信号球全名**（4 带 × 16 球，与 per_ball
   引擎 signal=64 口径完全自洽），结合 L1 v2.0 §信号流（A_PORT=host/J2、B_PORT=device/MCIO）
   生成 5 条 ECO 后核对断言（含"网表若 A 端口实接 MCIO → 冲突即停机回 L1/L2 对账"条款）。
   边界：期望矩阵派生自已冻结文档 + 已验资产，**非芯片实测**；真实映射以 ECO 后网表为唯一
   裁决源（C3 同批一次核对）。

- v28 补记 commit 面：`m13_v28_session_handoff.md`（本节）+ `spec_regen_diff_checklist_v28.json`
  + `gen_c5_chip_expect_matrix.py` + `c5_chip_level_expect_matrix_v28.json` → k2 commit →
  容器 bump。_shared 仍无改动。路径 c 对齐准备至此穷尽（草案/注入校验/差异清单/符号缺口/
  C5 期望矩阵），下 session 触发器不变（ECO 落地 → 差异清单逐项再生 → ⑦ evaluated →
  C5 期望矩阵一次核对）。
