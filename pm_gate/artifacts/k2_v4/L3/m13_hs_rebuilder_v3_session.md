# M13 v3 高速域重建收敛 — NEW SESSION PROMPT

> 承接：M13 v2 核心实现（走廊折线 + 对中心线 + P/N 展开 + REFCLK In6 场已验证）
> 路线修正（PM 讨论 2026-08-25）：禁止暴力求解铁律已写入 AGENTS.md §5
> 三域联动授权已确认（PERSTB# 让道 + PDN 让位 + 重建器实现）

```
你是 K2 统一 DRC 语义建模内核（DRC-SEMANTIC-CORE，M10-M14 攻坚）的 M13 v3 执笔 session。
工作目录：/home/fila/jqdDev_2025/ic_hw
项目：PCIe Gen4 转换卡卡2-K2（120×38mm，k2_v4.kicad_pcb，U3/U7 双 DS160PR810 ReDriver）

【背景（必须读，M10-M12 已完成勿考古）】
1. .omo/plans/k2-drc-semantic-core.md（M10-M14 攻坚计划，M13 = 各域套模板重建）
2. artifacts/L3/drc_semantic_core_m12.md（M12 交付：drc_locator 867 条 100% 可定位）
3. artifacts/L3/m13_highspeed_plan.md（M13 方案论证：18 对差分、规模/顺序/阻塞点）
4. artifacts/L3/m13_highspeed_phase1_pin_audit.md（逐 Pin 预检：UP4/UP5 区域密度根因）
5. artifacts/L3/m13_hs_rebuilder_v1.md（重建器 v1：V-Graph 超时根因 + v2 改造清单）
6. artifacts/L3/m13_hs_rebuilder_v2_session.md（v2 session prompt + 状态锚点）
7. artifacts/L3/m13_hs_rebuilder_v3_session.md（本文件）
8. AGENTS.md（开工第一动作：cd strix-halo-ioconvert/revA/pcb && python3 pm_gate/cli.py status + sstatus；
   铁律含 2026-08-25 新增"禁止暴力求解"——单对求解 >5s 即停转 Plan）

【当前状态锚点（v2 已交付，勿重做）】
- REFCLK 通道裁决已落地：SPEC corridors 增补 refclk band（layer=In6.Cu, y=45.7/50.5），
  corridors.pairs=18，channel_alloc_v2 18/18 SOLVED（artifacts/L3/model_solves/channel_alloc_v2/）
- hs_route_model.py v2 核心已实现并单对验证 SOLVED（k2_m9demo 板）：
  - 走廊段确定性折线（channel track_y 直线 + seg_ok，零 V-Graph）——UP4/DN0/UP0-3/REFCLK0-1 链路 SOLVED
  - 对中心线求解 + P/N ±0.19 对称展开（PAIR_HALF_PITCH=0.19，同源路径等长）
  - 蛇形等长补偿（_snake_compensate_v2，target 侧单侧 zigzag）
  - REFCLK In6.Cu 场（build_hs_field layer='In6.Cu'）
  - clear_hs_pads=True 重建场（高速 pad 清出，板上旧 pad 非障碍）
  - 单测：test_hs_route_model.py 新增 TestV2*（走廊确定性/对中心线对称/REFCLK In6 层）
- v2 实测（部分）：UP4 skew 0.063 / REFCLK0 skew 0.027，全部 skew_ok=True

【v2 遗留问题（v3 必须修复）】
- 逃逸段用 F.Cu 场 + V-Graph 6 候选扫描 → REFCLK1 单对 102s、全量 18 对 >5 分钟。
  PM 裁决：禁止暴力求解。根因 = 逃逸段错误地用 F.Cu 单层场硬穿 J4/U7 引脚密集区，
  V-Graph 节点数百 → O(n²) 全图搜索。板上真源早就给了答案：
    PCIE_UP_OUT4_N_J2: F.Cu→via→In2.Cu 长链→via→F.Cu（数据对逃逸换层走 In2）
    PCIE_UP4_N 输入段: 17 段大部分 In2.Cu
- F-R14 红队 finding 已驳回（低速域历史遗留，登记专项），G1.1 解除阻断

【本轮任务（M13 v3，严格按序，禁止跳级）】
1. 【逃逸段换层确定性折线】逃逸段改 In2.Cu 场（clear_hs_pads=True）+ L 形确定性折线
   （固定候选序 H-V / V-H / DIAG + seg_ok 验证，零 V-Graph）——解决 v2 逃逸 CPU 疯狂
2. 【V-Graph 降级兜底】确定性折线全部 seg_ok 失败才允许 V-Graph 单次求解
   （非多候选扫描）；判据：单对求解 >5s 即停转 Plan 报告路线
3. 【全量 18 对】UP0-7/DN0-7/REFCLK0-1 链路求解 → solve_ref + input_fp 落盘
   artifacts/L3/model_solves/hs_rebuild/（每对 SOLVED/INFEASIBLE 带证明，总耗时目标 <60s）
4. 【model_gate 验证】高速域设计段 100% 模型来源（solve_ref 协议，同低速域）
5. 【S2 正规流程】sregress S2 → 施工层落板（low_speed_apply 模式：预载+快照规避
   pcbnew SWIG 退化）→ sadvance S2
6. 【DRC 复验】kicad-cli pcb drc（--severity-error --refill-zones，带 .kicad_pro）：
   高速域 385 条 → 目标 0（或带证明残余）

【铁律】
- 禁止暴力求解（AGENTS.md §5，PM 裁决 2026-08-25）：主路径 = 确定性折线
  （固定候选序 + seg_ok 验证，O(段数×障碍数) 毫秒级）；V-Graph/Dijkstra 全图搜索
  仅最后兜底单次调用；禁止"多候选 × 全图搜索"嵌套。单对 >5s → 停转 Plan
- 方案即模型输出：任何设计段必须出自 hs_route_model（solve_ref）；无模型来源 = 非法
- DRC 只核对不驱动：DRC 是结束时的核对，不是设计驱动器；禁止拿 DRC 手工改走线
- 结论带证明：SOLVED 带路径/等长证据；INFEASIBLE 带连通分量 + 边界障碍清单
- 修订走输入：冲突 → 修订 SPEC/规则/输入 → 模型重算 → 重验（禁止施工层妥协）
- 零 revA 特判：hs_route_model 全通用（差分对/通道/规则全入参）；不碰 locked 高速段
- 反死循环：同一命令连错 2 次停转 Plan 等人工介入

【工具基线】
- sharun python3.11 + PYTHONPATH=/home/fila/jqdDev_2025/ic_hw/_shared
- 板：strix-halo-ioconvert/revA/pcb/k2_v4.kicad_pcb（对齐用 /tmp/opencode/boards/k2_m9demo.kicad_pcb）
- SPEC：pm_gate/artifacts/L3/SPEC_k2_v4.json（已含 refclk band + pairs 18）
- 通道表：pm_gate/artifacts/L3/model_solves/channel_alloc_v2/channel_alloc.json（18/18 SOLVED）
- DRC 基线：/tmp/opencode/boards/k2_m9demo.drc.json（867 条，勿重跑勿考古）
- DRC 口径：kicad-cli pcb drc <板> --format json --severity-error --refill-zones（带 pro）
- 可复用：hs_route_model v2（走廊折线/对中心线/蛇形/In6 场）、unified_field（skip_nets）、
  drc_locator、channel_alloc、ls_route_model（solve_ref 协议参照）、low_speed_apply（落板模式）
- 状态机：python3 pm_gate/cli.py sstatus / sregress / sadvance

【已知勿考古】
- M12：867 条 100% 可定位（drc_locator），芯片区高速 385 = via_clearance 159 +
  pad_clearance 78 + seg_clearance 70 + mask 42 + hole 15 + crossing 6 + short 1 + diff 1
- M13 v1：UP4-7 输出段 V-Graph 超时（走廊区密集 O(n²)）；链路 skew 大（P/N 独立最短路）
- M13 v2：走廊段确定性折线 + 对中心线 + P/N ±0.19 展开 + REFCLK In6 场已验证；
  逃逸段 V-Graph 候选扫描 CPU 疯狂（REFCLK1 102s）→ v3 换层折线
- 板上逃逸换层真源：PCIE_UP_OUT4_N_J2 走 In2.Cu、PCIE_UP4_N 输入段 17 段大部分 In2.Cu
- F-R14 已驳回（低速域遗留：SPEC low_speed_nets 162 段无 source 标记，T2.5.2 冻结段，
  修复归属低速域专项，不阻断 M13）

【交付物】
- 逃逸段换层确定性折线（In2.L 形）+ V-Graph 兜底降级 + 单测（逃逸折线确定性）
- 全量 18 对求解记录（solve_ref + input_fp + 路径/等长证据）落盘 model_solves/hs_rebuild/
- model_gate 验证报告 + S2 sregress/sadvance 记录
- 重建后 DRC 复验报告（高速 385 目标，drc.json 摘要）
- 全部结论带证明；红队可审计；单对求解耗时记录（证明非暴力求解）
```
