# M13 v6 拓扑可布性门禁 — NEW SESSION PROMPT（2026-08-26 交接）

承接：`topology_routability_gate_plan.md`（本会话唯一权威计划，必读）
       + `m13_hs_rebuilder_v5_session.md`（v5 复盘：五轮布线层死磕 → 拓扑层根因）
工作目录：`/home/fila/jqdDev_2025/ic_hw`
铁律：AGENTS.md §5 七步法 / 先画图后算数（TOP VIEW 前置）/ 方案即模型输出 /
分析走模型 API（禁临时脚本）/ DRC 只核对不驱动 / 修订走输入 / 零 revA 特判 /
假成功零容忍（断言全过才算 SOLVED）/ 可重复可追溯（红队可审计）/
反暴力迭代（同输入重跑 ≥2 次即暴力）/ 单对 >5s 停转 Plan / 冲突即停机

---

## 0. 开工第一动作
```
cd strix-halo-ioconvert/revA/pcb && python3 pm_gate/cli.py status && python3 pm_gate/cli.py sstatus
```
（红队 open findings 逐条处理；状态机当前 S2 高速锁定）

## 1. 背景（为什么做这个——大白话）
M13 v1→v5 五轮都在"布线算法"层优化，18 对高速线真实布通仅 1 对。
TOP VIEW 复盘定位**根因在拓扑层**（非布线层）：
- 网表按"信号方向"分工（U7 管全部上行 UP0-7、U3 管全部下行 DN0-7）
- 连接器按"物理位置"分布（J3 上排 y≈44.5、J4 下排 y≈62.7，lane 双向 TX+RX 捆绑）
- 交叉：UP4-7 从下排 J4 斜穿到上排 U7；DN0-3 从上排 J3 斜穿到下排 U3（共 8 对）
- 斜穿路径撞 U3 区域 + 32 颗 AC 耦合电容墙 → 布线层无解
- **体系缺口：原理图→PCB 之间无"网表 vs 布局"可布性检查**
  （原理图模型管"图对不对"，PCB 模型管"线通不通"，中间无人管"接法+摆法会不会交叉"）

**修复方向**：新拓扑（U7 管 lane0-3 双向、U3 管 lane4-7 双向、J2 引脚按上下排重映射）
→ 全同排零交叉。**改造核心 = 建"拓扑可布性门禁"模型能力**（可重复/可追溯），
并把"先画图后算数"固化为正式门禁。

## 2. 权威计划
`strix-halo-ioconvert/revA/pcb/pm_gate/artifacts/k2_v4/L3/topology_routability_gate_plan.md`
（问题复盘/架构缺口/三层改造/里程碑 M-A..M-G/验证标准/风险）——本 session 按 M-A→M-G 顺序执行，勿跳级。

## 3. 当前状态锚点（已提交 v6.13-k2-m13v6-topology-gate-plan，勿重做）
- **已落地（v6.11/v6.12/v6.13）**：
  - v6.11（v4.4）：链级原子事务 / REFCLK In6 贯穿 / via 障碍累积 / P-N 间距断言 / hs_apply PDN 冲突登记
  - v6.12（v5）：容量地图（probe_region_capacity/capacity_map/_capacity_regions/_corridor_clear_span）+
    flip 双极性重设计（适用性几何预检，消除 P/N 交叉 -0.205 假 SOLVED）+
    换层形态（Form C 错开 via + 方向一致性 + _sym_via 循环结构 bug 修复 v4.3 隐藏）
  - v6.13（M3 段级轨道）：_track_y_for 支持 segname 参数（alloc.seg_tracks[segname] 优先）
  - 单测 32 passed（M1/M2/M4 回归锁）
- **未验证的输入修订（v6.13 提交，M3 实验性，须按规划复验）**：
  - SPEC_k2_v4.json corridors tracks_y 已改为"对齐 pad 对中心"（J2_TO_U upper=[40.3..48.7] 对齐
    U7 输出、lower=[58.3..66.7] 对齐 U3 输入；U_TO_MCIO upper=[40.7..49.1] 对齐 U7 输入、
    lower=[58.7..67.1] 对齐 U3 输出）
  - channel_alloc_v2.json 每 base 已加 seg_tracks（input/out 段各自轨道）
  - **注意**：这两处修订是"旧拓扑（方向分工）下的轨道对齐"，新拓扑（lane 分工）确定后
    需按新拓扑重新推导——勿直接沿用
- **v5 交付物（v6.12 提交）**：capacity_map.json（旧拓扑 4 区容量证据）/ layout_gap_report.md
  （v5 缺口报告，含 0.4/0.38/0.525 数学不可行性证明）/ hs_rebuild_v5/ 求解记录

## 4. 任务（按规划 M-A→M-G 执行，勿跳级）
- **M-A 造尺子**：实现 `probe_link_topology`（HSRouteModel 方法，与 probe_region_capacity 同族；
  输入=网表+器件位置+引脚分布，逐链路判定 ALIGNED/CROSSING/LONG_SPAN，落盘 JSON，确定性）；
  单测覆盖
- **M-B 验尺子**：对**当前网表**（旧拓扑）出拓扑报告 → 必须抓住 UP4-7/DN0-3 共 8 对
  CROSSING（证明探针真能发现问题）
- **M-C 预验证**：对**新拓扑**（U7=lane0-3、U3=lane4-7、J2 引脚重排）出预检报告 →
  16 链路全 ALIGNED（改网表前零成本验证，通过才允许动网表）
- **M-D 改网表**：ECO（接线分工重排：U7/U3 角色按 lane、J2 引脚重映射）→
  原理图模型验证（结构三基础 + ERC 0 + 出图门禁全绿）
- **M-E 重布**：重生成 PCB → 容量地图 → 全量求解（16 对全 SOLVED + P/N 断言全过 +
  等长 <0.15 + 单对 <5s）
- **M-F 落板**：副本落板 → kicad-cli DRC 高速 0 违规 + 0 未连接（或带证明残余登记）
- **M-G 固化**：topo_routability_check 门禁接入 pipeline（原理图→PCB 必经环节，
  K1/K2 通用，零 revA 特判）

**验收总原则**：每一步结论出自模型输出、落盘、可追溯；任何一步不过即停（冲突即停机），
禁止"改了再说"。

## 5. 关键物理事实（实测，勿重新论证）
- U7 输入 pads（x=88.83）：对中心 y=49.1..40.7（步进 1.2）；输出 pads（x=98.83）：48.7..40.3
- U3 输入 pads（x=98.83）：58.3..66.7；输出 pads（x=88.83）：58.7..67.1
- J3（上排 y=45.8 引脚）：UP0-3 输入 + DN0-3 输出；J4（下排 y=61.5）：UP4-7 + DN4-7
- J2（y=53.7）：UP 引脚 y=43.2..53.1（上半）、DN 引脚 y=54.3..64.2（下半）
- 引脚区 0.4 脚距：F.Cu 直连（flip）需 pad 对在轨道带外（v5 已证）；via 换层 0.525→0.38 汇聚必交叉
- 轨道对齐 pad 对中心时 flip 直连可用（pad 对距 0.4 > 轨距 0.38，余量 0.02）——M3 段级轨道基础

## 6. 工具基线
- 求解：`cd _shared && <sharun> python3.11 -m eda_core.hs_route_model --all-v4 --board ... --spec ... --alloc ... --rules eda_core/drc_rules.json --pro ... --out <dir>`
- 容量地图：`--capacity-map`（落盘 capacity_map.json）
- 落板：`python -m eda_core.hs_apply --board <PCB> --solves <hs_rebuild> --rules eda_core/drc_rules.json`
- DRC：`<sharun> kicad-cli pcb drc <板> --format json --severity-error --refill-zones`
- 状态机：`python3 pm_gate/cli.py sstatus / sregress S2 / sadvance`
- 单测：`cd _shared && <sharun> python3.11 -m pytest eda_core/tests/test_hs_route_model.py -q`
- 分析一律走模型 API（禁一次性脚本手算）——新能力 probe_link_topology 建成后
  拓扑判定必须用它，禁止回退到 python -c 手查

## 7. 待 PM 确认（计划 §7，本 session 开头确认）
1. 新拓扑信号映射表：由模型（L2 布局分析）输出建议 → PM 确认 → 作为网表修订输入
2. 门禁接入位置（L1/L2 阶段，仿 G2.6）→ PM 确认
3. 其余无（器件可动/层无约束已裁决）
