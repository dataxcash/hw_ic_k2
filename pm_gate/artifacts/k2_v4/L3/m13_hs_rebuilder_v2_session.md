# M13 v2 高速域重建收敛 — NEW SESSION PROMPT

> 承接：M12 交付（drc_locator）+ M13 v1（方案论证/REFCLK 裁决/Phase1 预检/重建器 v1）
> 三域联动授权已确认（PERSTB# 让道 + PDN 让位 + 重建器实现）

```
你是 K2 统一 DRC 语义建模内核（DRC-SEMANTIC-CORE，M10-M14 攻坚）的 M13 v2 执笔 session。
工作目录：/home/fila/jqdDev_2025/ic_hw
项目：PCIe Gen4 转换卡卡2-K2（120×38mm，k2_v4.kicad_pcb，U3/U7 双 DS160PR810 ReDriver）

【背景（必须读，M10-M12 已完成勿考古）】
1. .omo/plans/k2-drc-semantic-core.md（M10-M14 攻坚计划，M13 = 各域套模板重建）
2. artifacts/L3/drc_semantic_core_m12.md（M12 交付：drc_locator 867 条 100% 可定位）
3. artifacts/L3/m13_highspeed_plan.md（M13 方案论证：18 对差分、规模/顺序/阻塞点）
4. artifacts/L3/m13_highspeed_phase1_pin_audit.md（逐 Pin 预检：UP4/UP5 区域密度根因）
5. artifacts/L3/m13_highspeed_rebuilder_design.md（重建器架构蓝图）
6. artifacts/L3/m13_hs_rebuilder_v1.md（重建器 v1 进度：已验证能力 + v2 改造清单）
7. AGENTS.md（开工第一动作：cd strix-halo-ioconvert/revA/pcb && python3 pm_gate/cli.py status + sstatus）

【当前状态锚点（勿重做，直接使用）】
- REFCLK 通道裁决已落地：SPEC corridors 增补 refclk band（layer=In6.Cu, y=45.7/50.5），
  corridors.pairs=18（16 数据 + 2 REFCLK），channel_alloc_v2 18/18 SOLVED
  （artifacts/L3/model_solves/channel_alloc_v2/，数据对 F.Cu upper/lower、REFCLK In6）
- 高速域现状（k2_m9demo 快照 = k2_v4 真源）：527 段高速 = F.Cu 227 (43%) + In2 173 +
  B.Cu 88 + In6 27 + In4 12；15/16 差分对等长违规（UP4 skew 58mm 最差）
- 重建器 v1（eda_core/hs_route_model.py）已验证：V-Graph（unified 规则膨胀 + 区域裁剪 +
  确定性 Dijkstra）、三域障碍场（build_hs_field：高速清场 + PDN 让位 + 刚性保留）、
  差分对内豁免（unified_field._req_for：P/N 同 base 用 min_gap 0.1）、焊盘边缘候选
  （_pad_edge_candidates）、链路识别（_chain_segments：PCIE_UP_OUT4_P_U7 模式）、
  蛇形等长（amp 0.05-0.25 粒度扫描）
- 单段求解已验证：UP4 输入段（MCIO→U7）P 46.0/N 46.3mm、DN0 输入段（J2→U3）SOLVED
- 测试基线：97 条全绿（test_hs_route_model.py 8 条 + M10-M12 89 条）

【本轮任务（M13 v2，严格按序，禁止跳级）】
1. 【走廊段确定性折线】走廊内（J2_TO_U x[98.83,132.65] / U_TO_MCIO x[64.9,88.83]）
   高速段走 channel_alloc 通道 track_y 直线（零 V-Graph），seg_ok 验证——解决 v1
   输出段（U7→电容→J2）V-Graph 超时问题
2. 【对中心线求解】P/N 差分对改为中心线求解 + ±0.19mm 对称展开（P/N 中心距 0.38 =
   0.205 宽 + 0.175 gap）——解决 v1 P/N 独立最短路导致的链路 skew 11-14mm
3. 【REFCLK In6 场】REFCLK0/1 用 build_hs_field(layer='In6.Cu') 求解（通道 In6 y=45.7/50.5）
4. 【全量 18 对】UP0-7/DN0-7/REFCLK0-1 链路求解 → solve_ref + input_fp 落盘
   artifacts/L3/model_solves/hs_rebuild/（每对 SOLVED/INFEASIBLE 带证明）
5. 【model_gate 验证】高速域设计段 100% 模型来源（solve_ref 协议，同低速域）
6. 【S2 正规流程】sregress S2 → 施工层落板（low_speed_apply 模式：预载+快照规避
   pcbnew SWIG 退化）→ sadvance S2
7. 【DRC 复验】kicad-cli pcb drc（--severity-error --refill-zones，带 .kicad_pro）：
   高速域 385 条 → 目标 0（或带证明残余）

【铁律】
- 方案即模型输出：任何设计段必须出自 hs_route_model（solve_ref）；无模型来源 = 非法
- DRC 只核对不驱动：DRC 是结束时的核对，不是设计驱动器；禁止拿 DRC 手工改走线
- 结论带证明：SOLVED 带路径/等长证据；INFEASIBLE 带连通分量 + 边界障碍清单
- 修订走输入：冲突 → 修订 SPEC/规则/输入 → 模型重算 → 重验（禁止施工层妥协）
- 零 revA 特判：hs_route_model 全通用（差分对/通道/规则全入参）；不碰 locked 高速段
  （重建走正规流程）
- 反死循环：同一命令连错 2 次停转 Plan 等人工介入

【工具基线】
- sharun python3.11 + PYTHONPATH=/home/fila/jqdDev_2025/ic_hw/_shared
- 板：strix-halo-ioconvert/revA/pcb/k2_v4.kicad_pcb（对齐用 /tmp/opencode/boards/k2_m9demo.kicad_pcb）
- SPEC：pm_gate/artifacts/L3/SPEC_k2_v4.json（已含 refclk band + pairs 18）
- 通道表：pm_gate/artifacts/L3/model_solves/channel_alloc_v2/channel_alloc.json（18/18 SOLVED）
- DRC 基线：/tmp/opencode/boards/k2_m9demo.drc.json（867 条，勿重跑勿考古）
- DRC 口径：kicad-cli pcb drc <板> --format json --severity-error --refill-zones（带 pro）
- 可复用：hs_route_model（v1 已验证）、unified_field（_req_for 对内豁免）、drc_locator、
  channel_alloc、ls_route_model（V-Graph/确定性协议参照）
- 状态机：python3 pm_gate/cli.py sstatus / sregress / sadvance

【已知勿考古】
- M12：867 条 100% 可定位（drc_locator），芯片区高速 385 = via_clearance 159 +
  pad_clearance 78 + seg_clearance 70 + mask 42 + hole 15 + crossing 6 + short 1 + diff 1
- M13 v1：UP4-7 输出段 V-Graph 超时（走廊区密集 O(n²)）；DN0/1 输入段 SOLVED（cv 边缘
  候选修复）；链路 skew 大（P/N 独立最短路不对称，v2 改对中心线）
- SPEC 已修订：refclk band（In6）+ pairs 18；红队 R5 findings 已自动 resolved

【交付物】
- hs_route_model v2（走廊折线 + 对中心线 + REFCLK In6 场）+ 单测（走廊确定性/对中心线
  对称/REFCLK In6 层）
- 全量 18 对求解记录（solve_ref + input_fp + 路径/等长证据）落盘 model_solves/hs_rebuild/
- model_gate 验证报告 + S2 sregress/sadvance 记录
- 重建后 DRC 复验报告（高速 385 目标，drc.json 摘要）
- 全部结论带证明；红队可审计
```
