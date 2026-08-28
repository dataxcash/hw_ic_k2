# M13 v5 高速域模型加强 — NEW SESSION PROMPT（2026-08-25 交接）

承接：`m13_hs_rebuilder_v5_plan.md`（本会话唯一权威计划）+ `m13_hs_rebuilder_v4_session.md`（v4 续接）
工作目录：`/home/fila/jqdDev_2025/ic_hw`
铁律：AGENTS.md §5 七步法 / 对称优先 / 累积障碍+段级清出 / 方案即模型输出 / DRC 只核对 /
修订走输入 / 零 revA 特判 / 反死循环 / 冲突即停机 / 单对>5s 停转 Plan / 分析走模型探针
（禁一次性脚本手算）/ 同输入重跑 ≥2 次即暴力迭代 / **假成功零容忍（原子性断言全过才算 SOLVED）**
并发：K1 v8.2 session 并行改 `_shared/eda_core/hs_route_model.py`（K1 区 k1_escape*）——
改前 git status、小步快改、勿覆盖 K1 区、运行前 ast.parse 验语法、求解落盘独立目录
`model_solves/hs_rebuild_v5/`

0. 开工第一动作
cd strix-halo-ioconvert/revA/pcb && python3 pm_gate/cli.py status && python3 pm_gate/cli.py sstatus
（红队 open findings 逐条处理；当前无阻断，S2 高速锁定态）

1. 已完成（勿重做，已提交 v6.11-k2-m13v4-hs-rebuild）
1.1 链级原子事务（v4.3）：solve_all_v4 整链 SOLVED 才并全局/落板，失败链全回滚。
1.2 REFCLK In6 贯穿（v4.4）：走廊 band 合并（同 track_y/layer 多走廊 x_range 合并）+
    pad-on-channel 延伸（l_on/r_on 几何判别：pad 距通道 y<0.3 时走廊段延伸至 pad 对中心）
    + left_x 段净空内滑（点净空+段净空双判据，防 pad 间隙欺骗）+ esc_layer 参数化
    （逃逸段层可指定，REFCLK 走 In6 零 In2 长段）+ _snake_k1 target 参数化 + 最接近需求增益。
1.3 via 障碍累积（v4.4 修复 A）：solve_chain_v4/solve_all_v4 增加 shared_vias
    （层变点即 via，贯穿全层障碍），_solve_pair_centerline_v4 _field 与补偿 fields add_via
    ——防后解段穿越先解 via（REFCLK0 曾穿 UP via 假 SOLVED，现已真实回退）。
1.4 P/N 间距断言（v4.4 修复 B）：solve_chain_v4 返回前 _pn_spacing_check（同层段距-线宽
    = 边缘距 ≥0.155 容差）；蛇形单侧向（off_dir 远离对侧轨，防蛇形侵入）。
1.5 hs_apply 缺陷 3：落板前删与高速新段冲突的 PDN 段（阈值 (w1+w2)/2+clearance，
    clearance 从 drc_rules.json 读取 net_classes PCIe85/POWER 取 max，--rules 参数），
    登记 pdn_conflicts.json → S3 铺铜接管。

2. 重大事实（真实基线，勿用声称值）
2.1 真实 SOLVED：仅 REFCLK0（1/18，In6 贯穿 P/N 0.175 构造保持）。其余 17 对：
    - 8 链被 P/N 断言拦截（flip=True 段 P/N 交叉中心距 0.0000）——**假 SOLVED**
    - UP0/1/2/4/5/7、DN0/1/3/5/6/7 逃逸失败（探针证据在 layout_gap_report.md）
2.2 flip=True P/N 交叉根因：P 接下轨（track_y-0.19）但 pad 在上侧 → P 竖线穿越 N 走廊轨。
    差分对内豁免 → P/N 互不检测 → seg_ok 放行。**方案级缺陷，v5 必须重设计（计划 §2-B）**。
2.3 "空间不够"无证据（v4.4 教训）：单候选探针 nearF=-0.075 是固定顺序产物非物理容量。
    几何粗算：0.4 脚距×16 引脚=3.2mm<引脚区 4mm，相邻线边缘距 0.195≥0.175；4 信号层容量
    64 对 vs 需求 18 对——**空间富裕**。一切"不够"必须由容量地图（probe_region_capacity）
    输出 INSUFFICIENT 带集合证明。
2.4 PM 裁决（2026-08-25）：①任何器件可动（满足 TOPO 合理性即可）②层无约束
    ——均无需逐次批准；判断以模型输出为准，禁止向用户讨裁决。
2.5 缺口报告已落盘：artifacts/k2_v4/L3/layout_gap_report.md（12 对探针数据/供需量化/停机声明）。

3. 任务（按 v5 计划 M1→M7 执行，勿跳级）
M1 容量地图：实现 probe_region_capacity（HSRouteModel 方法，与 probe_escape_capacity 同族）
   → 四区两走廊容量验证（U7 引脚区 UP 8 对 / U3 引脚区 DN 8 对 / J2 连接器 / J3-J4 连接器 /
   J2_TO_U / U_TO_MCIO）→ 落盘 model_solves/hs_rebuild_v5/capacity_map.json。
   判定：CAPACITY_OK（N 对可同时出列，组合枚举净空）/ INSUFFICIENT（最小冲突对集合：
   哪几对同时布必撞、撞哪个障碍、距离多少）。与几何粗算交叉核对。
M2 flip 重设计：flip 适用性几何约束（pad 对中心位于 P/N 轨之间才允许 flip）+
   P/N 分侧接入（竖线不同 x 汇入）或换层替代。验收：P/N 断言全过（无 0.0000）。
M3 全局通道分配：容量地图结果 → 引脚区轨道分配表（net→track_y→形态）→ 求解输入修订。
   验收：无"先解占位后解无路"型失败。
M4 数据对换层扩展：esc_layer 参数化已就绪，数据对走廊/逃逸段支持 In2/In4
   （受控过孔 ≤2/侧、P/N 同层、等长）。
M5 全量验证：solve_all_v4 18 对（链级事务+shared 累积+断言）→ SOLVED 最大化。
M6 落板验收：SOLVED 对落板副本（/tmp/opencode/boards/k2_v4_hsapply_test.kicad_pcb）
   → kicad-cli DRC 高速 0 违规（或带证明残余，PDN 冲突登记 S3）→ 落真板复验。
M7 交付：单测全绿 + 求解记录 hs_rebuild_v5/ + capacity_map + 缺口报告更新
   （剩余对带集合级证明）+ 状态机记录。提交走正规流程（commit 前 git status/diff）。

4. 关键物理事实（保留 v4 + 新增）
1. diff_pair_dimensions 空 → P/N via 中心距 ≥0.525；P/N 边缘距 ≥0.175（断言 0.155 容差）。
2. 引脚区 0.4 脚距：双 via 不可能 → F.Cu 直连（_direct_escape）或 In2 错开 via（stagger_steps）；
   P/N 中心距 0.4 < 0.525 时双 via 物理不可行。
3. 走廊轨 = track_y±0.19；flip=True = P 接下轨（v5 将加适用性几何约束）。
4. U7 pad 区 In6 净空（实测 58→135 全净空，最近障碍 via dist>1.3mm）——REFCLK In6 走廊贯穿可行。
5. 链=最小求解单元：整链 SOLVED 才落板/进 shared；失败链全回滚。
6. via 贯穿全层（F.Cu→B.Cu）：shared_vias 必须累积，防后解段穿越。
7. U3/U7 引脚区 0.4 脚距相邻线边缘距 0.195≥0.175——**理论可住 8 对**（容量地图验证）。

5. 工具基线
- 求解：cd _shared && <sharun> python3.11 -m eda_core.hs_route_model --all-v4 --board ... --out <dir>
- 落板：python -m eda_core.hs_apply --board <PCB> --solves <hs_rebuild> --rules eda_core/drc_rules.json
- DRC：<sharun> kicad-cli pcb drc <板> --format json --severity-error --refill-zones
- 状态机：python3 pm_gate/cli.py sstatus / sregress S2 / sadvance
- 探针：probe_escape_capacity / probe_path_clearance(clear_nets=) / probe_region_capacity(v5 新)
- 单测：cd _shared && <sharun> python3.11 -m pytest eda_core/tests/test_hs_route_model.py -q
- 分析一律走模型 API（禁一次性脚本手算）

6. 铁律速查（勿违反）
七步法（先容量后布线/先单条后全量/失败带证据）/ 对称优先 / 累积障碍+段级清出 /
方案即模型输出 / DRC 只核对不驱动 / 修订走输入 / 零 revA 特判 / 反死循环 /
冲突即停机（出报告等人工）/ 单对>5s 停转 Plan / 禁止暴力迭代（同输入重跑≥2 次即暴力）/
假成功零容忍（断言全过才算 SOLVED，禁口头声称）

续接状态总结：v4.4 完成三大正确性修复（via 累积/P-N 断言/REFCLK In6 贯穿），
真实 SOLVED 仅 1/18；flip=True P/N 交叉为方案级缺陷；"空间不够"无证据（容量地图未建）。
v5 目标 = 模型分析能力（容量地图）+ 形态重设计（flip/分配/换层），使 18 对全部真实可解
或带集合级证明不可解——不再有任何假成功。
