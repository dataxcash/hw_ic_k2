# M13 v4 高速域重建引擎 — NEW SESSION PROMPT

> 承接：M13 v3 落板验收失败（v3 引擎缺陷 4 类）+ v4 方案已定稿（二次修订）
> 方案真源：artifacts/k2_v4/L3/m13_hs_rebuilder_v4_plan.md（必读，算法级设计 + 七步法）
> 天条：AGENTS.md §5 人类老工程师结构化布线铁律（七步法，禁止违反）
> 本 session 只做一件事：按 v4 方案把引擎改到"整板一致"——18 对同画 DRC 0 违规

```
你是 K2 统一 DRC 语义建模内核（DRC-SEMANTIC-CORE，M10-M14 攻坚）的 M13 v4 执笔 session。
工作目录：/home/fila/jqdDev_2025/ic_hw
项目：PCIe Gen4 转换卡卡2-K2（120×38mm，k2_v4.kicad_pcb，U3/U7 双 DS160PR810 ReDriver）

【背景（必须读，v4 方案已定稿勿重新设计）】
1. artifacts/k2_v4/L3/m13_hs_rebuilder_v4_plan.md（v4 完整方案：七步法/基本原则/
   布线顺序/约束体系/求解管线/验收关卡/任务分解——本 session 的施工图）
2. AGENTS.md §5 人类老工程师结构化布线铁律（七步法：先画图→先单条→先容量→
   失败带证据→先理解现象→问题即机会→验证闭环）——全流程强制执行
3. artifacts/k2_v4/L3/m13_hs_rebuilder_v3_session.md（v3 session prompt + 状态锚点）
4. artifacts/k2_v4/L3/m13_hs_rebuilder_v1.md + m13_hs_rebuilder_v2_session.md
   （v1 超时根因 + v2 改造清单，仅背景）
5. artifacts/k2_v4/L3/model_solves/hs_rebuild/（v3 求解记录，落板输入，勿手工改）
6. AGENTS.md（开工第一动作：cd strix-halo-ioconvert/revA/pcb && python3 pm_gate/cli.py
   status + sstatus；红队 open findings 逐条处理）

【当前状态锚点（v3 已交付 + v4 探索期实测，勿重做）】
- hs_route_model.py 已有 v4 骨架：solve_pair_v4/solve_chain_v4/solve_all_v4
  （K1 路径 _solve_pair_single_v4 完整；K2 路径 _solve_pair_centerline_v4 半成品——
  _escape_pair/_sym_via/_escape_expand 已实现但 18/18 未达成，**勿当完成**）
- 单测 21/21 通过；关卡测试 test_board_level_consistency 已存在（调 solve_all_v2，
  **需改为调 solve_all_v4**）
- v4 探索期实测事实（已写入 plan，勿重新论证）：
  * v3 落板协议断裂：solve_all_v2 无 layers → hs_apply 全 skip → 关卡测试测的是
    真板固有 DRC（PCIE_ 529/总 883），非引擎重建结果
  * clear_hs_pads 全清 → 先解段穿后解 pad（U3 输出区 out_U3 短段穿 out_MCIO pad）
    → 累积障碍必须段级清出（clear_hs_nets 本段 P/N 清出、他段/他对 pads 保留）
  * 通道分配：channel_alloc 按 base 分配（18 键），同 base 段共享 track_y；
    UP/DN 各占满 8 轨，无空闲轨道 → 逃逸区容量是硬约束
  * 逃逸几何：展开方向须 pad 侧自适应（短段最短不横穿）+ 终点强制回正
    （P→track_y+0.19）+ via 紧贴 pad（半投影+0.3mm）；In2 段锚定展开线（P/N 同弧长）

【本轮任务（严格按序，禁止跳级，v4_plan §7 九步）】
0. 【天条启动】重读 AGENTS.md §5 七步法，本 session 全流程遵守；开工第一动作
   cd strix-halo-ioconvert/revA/pcb && python3 pm_gate/cli.py status + sstatus
1. 【关卡先行】改 test_board_level_consistency 调 solve_all_v4（非 solve_all_v2）：
   全量 18 对求解 → 段输出 path+layers 协议校验（len==path-1）→ hs_apply 落板副本
   → 断言 skipped=0 → kicad-cli DRC → 高速 0 违规/0 未连接。现状必须 FAIL（锁缺陷）。
2. 【手工规划单条链路】（七步法 1/2/3，唯一允许"先不写代码"的步骤）：
   坐标级手工规划 DN0（或 UP0）完整链路：J2/U3/MCIO pads 坐标 → 走廊 → 电容 →
   逐段确认净空；量出 U3/U7 输出区、电容区、J2/MCIO 连接器区逃逸容量
   （线宽 0.205 + 净距 0.175 + via 0.35 vs 可用宽度）；输出
   artifacts/k2_v4/L3/capacity_analysis.md（证据落盘，红队可审计）。
   这一步的结论决定缺陷 1/2 的修复边界（哪些段物理可解、哪些是通道缺口）。
3. 【缺陷 1：对级对称逃逸】_solve_pair_centerline_v4 修到 18/18 段级可解：
   对中心线（H-V/V-H/DIAG + 滑动）+ _escape_expand（pad 侧自适应）+ 终点回正
   + _sym_via（via 紧贴 pad：半投影+0.3mm 阶梯）+ In2 锚定展开线 + 分层 seg_ok。
   删除 P/N 独立逃逸路径。判据：手工规划的那条链路（任务 2）必须先跑通。
4. 【缺陷 2：累积障碍 + 段级清出】build_hs_field(clear_hs_nets=(本段 P/N)) +
   solve_all_v4 固定序（UP0-7→DN0-7→REFCLK0-1，段内 input→out）+ shared_segs
   进各层场。判据：先解段不得穿未解 pad；段间净距 0.175。
5. 【缺陷 3：PDN 落板】hs_apply 落板前删与高速新段冲突的 PDN 段（几何检测，
   阈值 = (w1+w2)/2 + clearance），删除清单登记 → S3 铺铜接管。
6. 【缺陷 4：REFCLK 端点】debug REFCLK0/1 In6↔J3/J2 连接，修 F.Cu 短段/via。
7. 【全量验收】18 对落板到副本 → 整板 DRC 高速 0 违规（关卡绿）→ 落真板
   k2_v4.kicad_pcb → 真板 DRC 复验（高速域目标 0 或带证明残余，PDN 冲突登记 S3）。
8. 【正规流程】model_gate 验证（SPEC 高速段 100% solve_ref）→ sregress S2 →
   施工层落板 → sadvance S2 → S3 PDN 前置登记。
9. 【交付】代码 + 单测全绿 + 关卡绿 + 求解记录更新 + 落板报告 + capacity_analysis
   + 状态机记录。

【铁律（违反即停，转 Plan 等人工介入）】
- 人类老工程师七步法（AGENTS.md §5）：先画图后算数 / 先单条后全量 / 先算容量
  再布线 / 失败带证据 / 先理解现象再修改 / 问题=模型改进机会 / 验证闭环。
  禁止"改参数→全量重跑→看求解率"的算法微调循环（M13 v4 教训：3/18→1/18）。
- 禁止暴力求解（AGENTS.md §5）：主路径 = 确定性折线（固定候选序 + seg_ok，
  O(段数×障碍数) 毫秒级）；V-Graph 仅最后兜底单次；禁止"多候选×全图搜索"嵌套。
  单对 >5s → 停转 Plan。
- 禁止暴力迭代：模型确定性——输入完整 → 一次求解正确；禁止"求解失败→改参数
  →重跑直到通"。INFEASIBLE = 输入缺口证明 → 判定缺口 → 方案级修输入 → 重解一次。
  同参数重跑 ≥2 次即暴力迭代，停转 Plan。
- 对称优先：P/N 恒同一中心线 ±0.19 对称展开（间距 0.38 构造性保证）；
  P/N 独立求解 = 非法（缺陷 1 复发判据）。
- 累积障碍 + 段级清出：已解段是后续段障碍；本段 P/N pads 清出、他段/他对
  HS pads 保留为障碍（缺陷 2 复发判据 = 落板 DRC 高速互撞）。
- 整板一致是验收：局部 SOLVED ≠ 成功；关卡测试（整板 DRC 0 违规 + skipped=0）
  与单测同级，每个改动后必跑。
- 方案即模型输出：任何设计段必须出自 hs_route_model（solve_ref）；无模型来源 = 非法。
- DRC 只核对不驱动：DRC 是结束时的核对；整板一致性由模型关卡保证，禁止拿 DRC 手工改线。
- 结论带证明：SOLVED 带路径/等长/layers 证据；INFEASIBLE 带最近障碍类型/网/距离
  （nearest_obstacle）。
- 修订走输入：冲突 → 修订 SPEC/规则/输入 → 模型重算 → 重验（禁止施工层妥协）。
- 零 revA 特判：hs_route_model 全通用（差分对/通道/规则全入参）；不碰 locked 段。
- 反死循环：同一命令连错 2 次停转 Plan 等人工介入。

【工具基线】
- sharun python3.11 + cwd=_shared 用 python -m（PYTHONPATH 会被 sharun 净化）
- 板：strix-halo-ioconvert/revA/pcb/k2_v4.kicad_pcb（真板，落板目标）
- 副本：/tmp/opencode/boards/k2_v4_hsapply_test.kicad_pcb（+ .kicad_pro，关卡用，
  勿动真板直落）
- SPEC：pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json（vias.high_speed：每线≤2、
  no_via_in_pad 0.3、GND 伴行、背钻；总量 300 上限；corridors 轨道见 plan §2）
- 通道表：artifacts/k2_v4/L3/model_solves/channel_alloc_v2/channel_alloc.json
  （18/18 SOLVED，按 base 分配，同 base 段共享 track_y）
- 求解落盘：python -m eda_core.hs_route_model --all-v4 --out <dir>（K2 走
  solve_all_v4，输出 hs_rebuild/）
- 落板：python -m eda_core.hs_apply --board <PCB> --solves <hs_rebuild>
  （skipped=0 是关卡断言）
- DRC 口径：kicad-cli pcb drc <板> --format json --severity-error --refill-zones
  （kicad-cli 在 AppDir/usr/bin/，经 sharun 调用）
- 手工几何分析（七步法工具）：python -c 内联读 BoardParser pads/segments 坐标、
  unified_field.nearest_obstacle 查最近障碍证据、_point_edge_dist/_seg_seg_dist
  量距离、_path_len 量长度——先分析后改码
- 可复用：_expand_pair/_polyline/_escape_polyline/_escape_smd_via、
  _escape_expand/_sym_via/_proj_arc（v4 骨架已有）、low_speed_apply、
  unified_field、drc_locator、model_gate、channel_alloc
- 状态机：python3 pm_gate/cli.py sstatus / sregress / sadvance

【已知勿考古】
- v3 全量 18/18 SOLVED（0.76s）是"局部可解"，落板副本 DRC 高速违规 1037——
  缺陷分析已定稿在 v4_plan §0.3，勿重新论证
- v3 落板协议断裂（无 layers → hs_apply 全 skip）已定性（v4_plan §0.2），
  关卡测试必须改用 solve_all_v4 + path/layers 校验
- 缺陷 1/2 是模型架构缺陷（非落板 bug）；缺陷 3 属 S3 范畴但需落板登记；
  缺陷 4 是连接细节
- 通道分配按 base（18 键）、同 base 段共享 track_y、无空闲轨道（v4_plan §2）——
  逃逸区容量是硬约束，勿再考古轨道数
- k2_v4 真板 DRC 基线 869 违规 / 124 未连接（非高速，既有遗留勿动）；
  DRC 基线 867 条（k2_m9demo）勿重跑勿考古

【交付物】
- 整板一致性关卡测试（test_board_level_consistency 调 solve_all_v4，v3 状态
  FAIL → v4 全绿；含 path/layers 协议校验 + hs_apply skipped=0 断言）
- capacity_analysis.md（任务 2：DN0/UP0 完整链路手工规划 + 各逃逸区容量计算）
- v4 引擎代码（对级对称逃逸 + 累积障碍 + 段级清出）+ hs_apply 增补
  （PDN 让位删除 + layers 校验）
- 全量 18 对落板真板 + 整板 DRC 报告（高速 0 违规或带证明残余）
- model_gate 验证报告 + S2 sregress/sadvance 记录 + S3 PDN 前置登记
- 全部结论带证明（路径坐标/净距/容量/nearest_obstacle 证据）；红队可审计；
  单对求解耗时记录（证明非暴力求解）
```

---

# ═════════════════════════════════════════════════════════════════════
# 续接状态锚点（v4 session 迭代中，2026-08-25 20:40 交接，NEW SESSION 从这里续）
# 上方为原始 v4 prompt（背景），下方为当前执行态——勿重做已完成部分
# ═════════════════════════════════════════════════════════════════════

## 0. 并发警告（重要）
另一 K1 session（v8.2 逃逸重构）正在**并发修改** `_shared/eda_core/hs_route_model.py`
（`_tpl_a_line`/`_k1_escape_a/b`/`_extend_to` 等 K1 区）。规则：
- 改 _shared 代码前必查 `git status`；小步快改
- 我方区域 = K2 区（`_escape_pair`/`_solve_pair_centerline_v4`/探针）；对方 = K1 区
- 运行前 `python3.11 -c "import ast; ast.parse(open('...hs_route_model.py').read())"` 验语法
- 求解落盘用独立目录（如 `model_solves/hs_rebuild_v4/`）防与 K1 的 `hs_rebuild/` 冲突

## 1. 已完成（勿重做）
### 1.1 关卡先行（任务 1 ✅）
`test_hs_route_model.py::TestBoardLevelConsistency::test_board_level_consistency` 已改为：
solve_all_v4 + path/layers 协议校验（len(layers)==len(path)-1）+ hs_apply skipped=[] 断言
+ 网数≥36 + DRC 高速 0 违规/0 未连接。当前 FAIL（8/18 未解）——继续改到绿。

### 1.2 探针能力（任务 2 前置 ✅，模型能力提升）
hs_route_model.py 新增：`_probe_fields` / `probe_path_clearance` / `probe_escape_capacity`
（4 单测绿）。探针 bug 已修（fields["fcu"]/["in2"]/["band"] 显式解包，勿用 .values() 顺序）。
**用户裁决：分析/探针是模型能力，缺则加强模型——勿用一次性内联脚本手算几何。**

### 1.3 容量分析（任务 2 ✅）
`pm_gate/artifacts/k2_v4/L3/capacity_analysis.md` + `model_solves/probe/dn0_up0_escape_capacity.json`

### 1.4 引擎 v4.2（缺陷 1，进行中 8/18）
- `_direct_escape`：F.Cu 直连（flip=True 构造，P 下轨/N 上轨、竖线异 x 0.38、n_east 枚举、
  走廊起点=direction 侧远端竖线、内侧 jog、每候选验证走廊 (outer,ty)→(bound,ty) 净空）
- `_escape_pair`：形态自适应序 flip=True→DIRECT → via 轴向(_sym_via+侧滑) → LONG 纵向；
  pn_dist<0.525 跳过 via（DRC 实证：0.35 via 需中心距≥0.525）
- `_sym_via`：侧滑 slide_steps=(-0.6,-0.3,0,0.3,0.6) + flip
- `_solve_pair_centerline_v4`：flip 枚举(False→True)、`_need_escape(pad_idx,flip,cur_x)`
  （y 偏差+x 偏差）、corridor P/N 轨随 flip 交换
- slide range 8→30（走廊起点可滑 9mm 跳过电容墙）

### 1.5 channel_alloc 输入修订（✅，可审计脚本）
`model_solves/channel_alloc_v2/channel_alloc.json`：UP 轨正序（UP0→48.48...UP7→40.92，
匹配 U7 芯片端 pad 物理顺序）+ DN0↔DN1 互换（DN1 轨 60.0 与电容行 60.05 冲突）。solve_ref 重生成。

## 2. 关键物理事实（实测，勿重新论证）
1. **diff_pair_dimensions 为空** → DRC 对 PCIE_P/N 强制 0.175（无同对豁免）。实证：
   P/N via 0.38 中心距（0.35 dia）→ 0.0300 违规。**P/N via 中心距须≥0.525**。
2. **引脚区 0.4 脚距**：双 via 不可能（0.05<0.175）→ F.Cu 直连（_direct_escape）。
3. 走廊轨 = track_y±0.19；flip=True = P 接下轨（pad 侧自适应极性）。
4. F.Cu 直连：P/N 竖线异 x 0.38（边距 0.175 构造）；P pad 轨下方/上方适用不同 n_east。
5. LONG 纵向：横排电容 pad（0.4×0.5）via 沿 pad 长轴出线不撞墙。
6. 走廊可"跳过电容墙"（slide 30，如 DN0 out_U3 走廊起点 83.38）。
7. 链级蛇形 zigzag 在工作（_snake_k1 对 K2 生效）。
8. DN0 轨 60.0（线穿 DN1-3 电容行）SOLVED 靠走廊跳过。
9. **布局级缺口（8 对，非算法可解，禁止硬挤/换轨/挪器件）**：
   - UP0/1/2/4/5：UP 电容墙（x 99.48-128.18, y 42.9-53.4）堵轨；可用 UP 轨仅 3 条
     （40.92/42.0/45.24）；46.32 被 UP_OUT5 电容(105.48,46.5)堵、47.4 被 UP_OUT5
     (107.48,47.1)堵、48.48 被 UP_OUT3/4(y48)堵、44.16 被 UP_OUT6(101.48,44.4)堵、
     43.08 被 UP_OUT7(99.48,43.6)堵
   - DN3/6/7：DN 电容行（DN0@66/DN1-3@60.05/DN4-5@62/DN6-7@65）堵轨；可用 DN 轨 4 条
     （58.92/61.08/63.24/64.32）；62.16 被 DN4/5 电容行(62.0)堵、65.4 被 DN6/7(65.0)堵、
     66.48 被 DN0(66.0)堵
   - 处置：出论证报告（轨线 vs 电容行/墙精确净距证据）→ 停机等 PM/人工裁决

## 3. 当前求解（8/18 SOLVED）
SOLVED：DN0/1/2/4/5、UP3/6、REFCLK1
INFEASIBLE：DN3/6/7、UP0/1/2/4/5/7、REFCLK0
全量 solve_all_v4 ~2.7-3.9s（确定性，非暴力）。

## 4. 剩余任务（按序）
1. **UP7 out_U7 短段直连**（可修）：段 3.5mm（U7 输出(98.83,40.1/40.5)→电容(99.48,43.6)/(100.45,42.9)），
   P/N 上下翻转。方案：_solve_pair_centerline_v4 开头加短段判定（两端对中心距<6mm）→
   中心线展开（_escape_expand 沿两端对中心连线）+ 端点锚定 pad + seg_ok。验证 UP7 SOLVED。
2. **REFCLK0 跨走廊**（缺陷 4，可修）：input 左端 MCIO/J3(58.6,45.75)→走廊 J2_TO_U(98.83,45.7)
   40mm 逃逸。REFCLK 走廊 refclk band In6 track 45.7。查 v2 机制（test_refclk0_in6_layer 过）。
3. **8 对布局缺口冲突报告**（UP0/1/2/4/5+DN3/6/7）：出论证报告（净距证据+方案选项）→ 停机等人工。
4. **缺陷 3**：hs_apply 落板前删与高速新段冲突的 PDN 段（阈值 (w1+w2)/2+clearance），登记清单。
5. **全量验收**：18 对落板副本（勿动真板）→ DRC 高速 0 违规 → 落真板 → 真板 DRC 复验。
6. **正规流程**：model_gate 验证 → sregress S2 → 施工层落板 → sadvance S2 → S3 PDN 前置登记。
7. **交付**：单测全绿 + 关卡绿 + 求解记录 + 落板报告 + 状态机记录。

## 5. 工具基线
- 求解：`cd _shared && <sharun> python3.11 -m eda_core.hs_route_model --all-v4 --board <板>
  --spec <SPEC> --alloc <alloc> --rules <drc_rules.json> --pro <pro> --out <dir>`（输出 dir/hs_rebuild/）
- 落板：`python -m eda_core.hs_apply --board <PCB> --solves <hs_rebuild>`（skipped=0 关卡断言）
- DRC：`<sharun> <AppDir/usr/bin/kicad-cli> pcb drc <板> --format json --severity-error --refill-zones`
- 状态机：`cd strix-halo-ioconvert/revA/pcb && python3 pm_gate/cli.py sstatus / sregress S2 / sadvance`
- 真板：`strix-halo-ioconvert/revA/pcb/k2_v4.kicad_pcb`；副本：`/tmp/opencode/boards/k2_v4_hsapply_test.kicad_pcb`
- 几何分析走模型探针（probe_escape_capacity/probe_path_clearance）——勿手算

## 6. 铁律速查
七步法 / 对称优先（P/N 恒同一中心线）/ 累积障碍+段级清出（clear_hs_nets 本段 P/N）/
方案即模型输出（solve_ref）/ DRC 只核对不驱动 / 修订走输入 / 零 revA 特判 /
反死循环（同命令错 2 次停转 Plan）/ 冲突即停机（出报告等人工）/ 单对>5s 暴力嫌疑停转 Plan
