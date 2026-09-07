# M14 v43 承接 — 走廊层声明修正(REFCLK 全解) + 学习管线消费端接通 v1/v2 + NEW SESSION PROMPT

> 承接 v42。唯一必读 = 本文件。v42 handoff 只作背景（本文件已提炼，勿整读）。
> 产出物 = 整体 EDA TOPO ENG；K2 仅验证；能力都是 ENG 的。

---

## 0. 一句话状态

学习管线消费端已接通（引擎会查档案柜 + 失败段吐需求单），并按模板知识修正
SPEC 走廊层声明（数据带 In2.Cu / refclk In6.Cu）→ **REFCLK0/1 两 base 全链首次
SOLVED（solved_pairs 0→2）**。剩余 16/18 bases：chip 侧出脚下钻点被 F.Cu 球列挡
（8 段）+ connector 侧落点对级（16 段）。

---

## 1. 钉死事实（勿重推；v42 §1 仍有效，此处只记增量）

| # | 事实 | 依据 |
|---|---|---|
| N1 | F8 证伪：段名数据驱动（板网存在性），无旧走廊语义；solve base 双簿记已修（34→18 报告行） | v42 e2e |
| N2 | **SPEC corridors band layer 已修正**：EAST/WEST dn+up→In2.Cu、refclk→In6.Cu（照 corridor_pair_dual_band 模板 layer_plan）。勿回退 | k2 da4569c |
| N3 | 层修正后：alloc 34 无损、REFCLK0/1 全 SOLVED（模板 refclk In6 经验首次落地）、seg 10→12/34、e2e 2m31→1m18 | k2 da4569c e2e |
| N4 | ENG 已加：solve_all_v4 空链 base 跳过；fail_forms（flip 双极性证据落段）；escape_gap（段失败需求规格：required_template_domain=midfield_obstacle_hop / landing_pair_geometric）；template_match/board_template_query（板级查库 4/4 seed 命中） | _shared c0b5fe6/8e3bb50/5ab697a |
| N5 | escape_learner 铁律修订：学习期可 LLM（形态归纳/失败归因/样本遴选），运行期+五要素几何提取零 LLM | _shared ca35e0c |
| N6 | 模板库资产：seed_k2_templates 4 模板（conn_escape_slimsas_x8/conn_escape_mcio/cap_wall_ac/corridor_pair_dual_band）+ cases/ 2 开源板（OpenCAPI_to_PCIe.kicad_pcb 可用=no_via 直逃型；PEX8748=oshwhub eda_pro 格式打不开，勿再试）。kb.sqlite3 在 _shared/knowledge/（WAL 只读需 immutable 或拷 /tmp） | v42 实测 |
| N7 | **/tmp/opencode/boards 已被清理**：基线板 k2_m9demo.kicad_pcb 丢失 → test_hs_route_model 7 failed + routing_topology 1 failed 转 skip（非回归，勿尝试恢复/勿纠结）。可跑基线：test_solve_pipeline 1 failed 同款复现 + 其余全绿 | v42 实测 |
| N8 | chip 侧失败真因收敛：走廊 In2 化后轨道平走净空，**卡在 pad→In2 的端部下钻点**（F.Cu 表层 stub 横穿球列 x90.2-90.9 / via 落点被邻球挤） | v43 e2e fail 表 |
| N9 | connector 侧（out_MCIO/out_J2 全 16 段）：LANDING 落点无净空，MCIO pad 行(y45.75/61.45)→轨行(y58.7-67.1) 竖向 12.95mm；DN6 落点 P/N 垂距 7.5mm（落点分配未对级成对） | v42 fail_forms |
| N10 | DN0 input = lane0 特例：轨行 58.3 净空仍失败（极西球列 x84.85 pad 对角几何，flip 构造即交叉） | v42 轨行扫描 |

---

## 2. 剩余卡点（16/18 bases，seg 12/34）精确归因

| 段群 | 数量 | 失败形态 | 已证真因 |
|---|---|---|---|
| chip 侧 input（DN0-3,5 / UP2,4,7） | 8 | flip 双极性 VIA 交叉 @球列区 | pad 出脚 F.Cu stub / 下钻 via 位被 U6 P3V3/GND 球列(x90.2-90.9,y59-64; y40-49)挡；col_stack 候选失败点未定点 |
| connector 侧 out_MCIO/out_J2 | 16 | LANDING 无净空 / VIA 交叉 | MCIO pad-轨行竖爬 12.95mm 落点区拥挤 + 落点 P/N 未对级成对（DN6 垂距 7.5mm） |

已 SOLVED：DN4/6/7 input、UP0/1/3/5/6 input、UP4/7 out_J2、REFCLK0/1 input。
规律：轨行/落点避开球列与低密度区即解 → **不是形态缺，是端部几何/落点分配细节**。

---

## 3. 下一步主线（新 session 唯一工作）

1. **chip 侧定点**（先做，8 段）：探针跑 DN1 input（走廊已 In2）→ 打 col_stack/_escape_pair
   候选失败点（via 候选 x/y 序 + 每候选被哪个障碍拒）→ 判定：是"pad stub 横穿球列缺
   via 位"还是"col_stack 尾段/竖爬参数没覆盖"。可能修正方向：chip 端下钻 via 候选沿
   pad 列缝（x_jog 扩大/列缝定位数据驱动），或直接对照 DN4（同列族成功）的差异参数。
2. **connector 侧落点对级**（16 段）：MCIO/J2 landing 分配 P/N 不成对（DN6 垂距 7.5mm）
   → 查 _landing_escape 失败证据链：落点区障碍是谁（邻 pad/via 密度）→ 判断修
   escape_landing 落点分配（对级成对约束）还是 _landing_escape 形态。勿动 capacity。
3. 目标：18 bases SOLVED + skew<0.15 + P/N≥0.175 + 坐标 JSON 落盘。
4. 单测：可跑集全绿（test_solve_pipeline 1 failed 为 pre-existing 同款，勿修）。
5. ECN-009：unlock→备份→改→单测→lock 0/0/0→commit+push。

---

## 4. 省 CONTEXT 清单（新 session 强制）

**必读（唯一）**：本文件。**v42 handoff §1-§2 可选**（事实已提炼，除非需 fail_forms
原始矩阵再翻 v42）。

**勿读/勿做**：m13_v10~v41 任一 md 全文；v42 全量 handoff（除非查 fail_forms 原始值）；
capacity/alloc/landing 阶段代码与报告（全绿锁定，勿重跑勿重读）；route_input/
channel_alloc/capacity_audit/segment_corridor（closed）；/tmp 基线板恢复（已丢，接受
8 个 skip）；PEX8748 eda_pro 转换（死路）；"找开源板/扩样本"（需求驱动，等 escape_gap
清单累积，本轮不做）；全量 e2e（定点段级调试，≤2 次）；hs_route_model 整读（只
grep：_escape_pair/_col_stack_escape/_landing_escape/_solve_pair_centerline_v4/
solve_all_v4/fail_forms/escape_gap/template_match/board_template_query）。

**纪律**：全前台自跑、禁 task() 委派、禁后台、同参≤2 带依据、探针内联 python -c
用后即弃、能力进 ENG（_shared）K2 只消费、每步原始输出贴出。
停止判据：chip 侧定点第 2 次仍不 SOLVED → 带 col_stack 候选失败矩阵（via 候选序×拒因
×pad/球几何）停。

---

## 5. 资产（全部 commit+push，freeze 0/0/0）

| 资产 | commit | 内容 |
|---|---|---|
| _shared | c0b5fe6 | fail_forms + solve_all_v4 空链 base 跳过 |
| _shared | ca35e0c | escape_learner 铁律修订（学习期可 LLM） |
| _shared | 8e3bb50 | 模板消费端 v1：template_match/board_template_query |
| _shared | 5ab697a | 消费端 v2：escape_gap 段失败需求规格 |
| k2 | da4569c | SPEC 走廊层修正 In2/In6 → REFCLK 全解 |
| ic_hw 容器 | 721289a | bump 两仓 |
| _shared pre-existing 脏 | escape_closure_analysis.py / install.sh（mode-only，历史遗留，勿 commit） | — |

---

## 6. NEW SESSION PROMPT

---
承接 M14 v43。只读 `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v43_session_handoff.md`（唯一必读）。

背景：capacity/alloc/landing 全绿（勿碰）。学习管线消费端已接通（_shared
c0b5fe6/8e3bb50/5ab697a：fail_forms、空链 base 跳过、template_match 板级查库、
escape_gap 段失败需求规格）。SPEC 走廊层已按模板修正（k2 da4569c：dn/up→In2.Cu、
refclk→In6.Cu）→ **REFCLK0/1 全链 SOLVED（2/18 bases、12/34 seg）**，e2e 1m18。
F8 已证伪钉死。剩余 16/18 bases 两类精确归因（N8/N9）：
(1) chip 侧 input 8 段：pad→In2 端部下钻点被 U6 球列挡，col_stack 候选失败点未定点；
(2) connector 侧 out_* 16 段：MCIO pad-轨行竖爬 12.95mm + landing 落点 P/N 未对级成对。

任务（唯一主线，先 1 后 2）：
1. chip 侧定点（8 段）：探针跑 DN1 input（走廊 In2 已生效）→ 打 col_stack/_escape_pair
   候选失败点（每 via 候选被哪个障碍拒），对照同列族成功 DN4 差异参数 → 修（方向：
   chip 端下钻 via 沿 pad 列缝定位数据驱动 / col_stack 竖爬参数覆盖）。目标 DN0-3,5+
   UP2,4,7 input SOLVED。
2. connector 侧落点对级（16 段）：查 _landing_escape 失败证据链 → 判断修 escape_landing
   落点分配（P/N 对级成对约束，DN6 垂距 7.5mm 证据）还是 _landing_escape 形态。勿动
   capacity/alloc。
3. 目标：18 bases SOLVED + skew<0.15 + P/N≥0.175 + 坐标 JSON 落盘。
4. 单测：可跑集全绿（test_solve_pipeline 1 failed 为 pre-existing 同款勿修；/tmp 基线
   板已丢 → hs 8 failed 转 skip，勿恢复勿纠结）。
5. ECN-009：unlock→备份→改→单测→lock 0/0/0→commit+push。

省 CONTEXT：必读仅本文件；勿读 m13_v10~v42 全文/勿重跑 capacity/alloc/landing/勿动
SPEC 层修正(勿回退)/勿试 PEX8748/勿扩样本(需求驱动等 escape_gap)/hs_route_model 只
grep 定点符号/全量 e2e ≤2 次。纪律：全前台自跑、禁 task() 委派、禁后台、同参≤2 带
依据、探针内联 python -c 用后即弃、能力进 ENG K2 只消费、每步原始输出贴出。
停止判据：chip 侧定点第 2 次仍不 SOLVED → 带 col_stack 候选失败矩阵（via 候选序×拒因
×pad/球几何）停，不续命。
---
