# M13 v7 高速域重建续接 — NEW SESSION PROMPT（2026-08-26 交接）

承接：`m13_hs_rebuilder_v6_session.md` + `topology_routability_gate_plan.md`（权威计划）
      + `m13_v6_topology_precheck_report.md`（M-B/M-C 预检报告，含 J2 端方向修正）
工作目录：`/home/fila/jqdDev_2025/ic_hw`
铁律：AGENTS.md §5 七步法 / 先画图后算数 / 方案即模型输出 / 分析走模型 API（禁临时脚本）/
DRC 只核对不驱动 / 修订走输入 / 零 revA 特判 / 假成功零容忍 / 可重复可追溯 /
**反暴力迭代（同输入重跑 ≥2 次即暴力，求解失败必须出方案级缺口报告，禁止改参数重跑）**/
冲突即停机（任何一步不过即停，禁止"改了再说"）

---

## 0. 开工第一动作
```
cd strix-halo-ioconvert/revA/pcb && python3 pm_gate/cli.py status && python3 pm_gate/cli.py sstatus
```
（红队 open findings 逐条处理；状态机当前 S2 高速锁定）

## 1. 上一会话完成状态（已提交，勿重做）

**M-A 探针建成**（`_shared/eda_core/hs_route_model.py`）：
- `probe_link_topology`（单链路逐段判定 ALIGNED/CROSSING/LONG_SPAN + EVIDENCE_ONLY 回填 +
  R2 串扰/ R3 电容墙/ R4 平面连续性证据，数据驱动阈值，确定性）
- `link_topology_map`（全量地图，CLI `--link-topology`）
- `link_topology_virtual_map`（新拓扑预检，CLI `--link-topology-mapping`）
- 单测 TestV6LinkTopology 4 个全绿（含 M-B 8 CROSSING 断言）；全量 30 passed（8 红例为既有基线）

**M-B 验尺子**：旧拓扑 8 对 CROSSING（UP4-7 + DN0-3）精确命中，障碍证据（U3/U7 区域+电容墙）吻合复盘。

**M-C 预检**：新拓扑（U7=lane0-3、U3=lane4-7）16 链路全 ALIGNED（虚拟映射，交叉验证防假成功）。

**M-D 原理图 ECO 完成**（网表修订 + 全链验证 PASS）：
- `revA/boards/ioconvert_v2.yaml` nets 修订（48+16 处）：DN0-3→U7/RX4-7、UP4-7→U3/RX0-3、
  DN_OUT0-3→U7/TX4-7、UP_OUT4-7→U3/TX0-3；**J2 端保持方向映射**（UP 输出→J2/RX、DN 输入←J2/TX，
  方向语义非 lane 分组——LOGIC-05 差分链驱动检查驱动修正）
- split_sch 双卡生成自证 PASS（166 网零悬空 + 2038 文本零重叠）；结构三基础 valid；
  节点归属 10 网全 PASS + 100 PCIE 网完整 + U7/U3 各 32 引脚全接入
- ECO 状态机 S3/S4 PASS + 确定性（两次生成 diff 空）；ERC error=0（304 off-grid warning 非阻断）；
  出图门禁 PASS（27/0/3 + PM-M13v6 签署 5 条 STALE）；LOGIC-05 PASS
- **修复的既有缺陷**（通用，勿回退）：yamlloader pin 唯一性校验按 (ref,card,pin) 区分 @N 卡实例；
  sym-lib-table IOCONVERT URI 路径修正；sharun 补装 pyyaml 6.0.3（eco_gate 依赖）

**M-E 部分完成**（新拓扑输入 + 求解，卡点在最后一步）：
- k2_gen_v5.py 重生成 PCB（修复 OLD_REF_MAP refdes 查找优先级 bug）→ `/tmp/opencode/boards/k2_v5.kicad_pcb`
  （101 器件/508 pads，新网表验证：DN0→U7 输入、UP4→U3 输入 ✓）
- channel_alloc v3 重算（SPEC corridors bands.nets 修订为 upper=U7 lane0-3、lower=U3 lane4-7 →
  band 归属硬约束）→ 18 网全 SOLVED + seg_tracks 数据驱动补充（芯片端 pad 对中心→带内轨道）
- 容量地图：**U_TO_MCIO 全 CAPACITY_OK（vs v5 0/8——MCIO 端交叉修复见效）**；J2_TO_U 4/8+3/8
  （J2 连接器 GND 伴行 pad -0.075 压线，既有物理瓶颈）、U7 引脚区 1/4、MCIO 区 3/4
- **全量求解 PARTIAL：17/18 INFEASIBLE（仅 REFCLK0 SOLVED）**——卡点详见 §2

## 2. M-E 卡点（冲突报告，须方案裁决后继续）

**现象**：新拓扑全量求解 17 对全 INFEASIBLE（26.5s），失败模式全部为
`flip=True 对级对称逃逸无净空（对级对称逃逸无净空 M=(98.825,48.700) → cv=(116.825...)）`。

**根因**（模型能力 × 输入修订语义冲突）：
- v6.13 输入修订（M3 段级轨道）：SPEC corridors tracks_y 对齐 pad 对中心
  （J2_TO_U upper=[40.3..48.7]=U7 输出 pad 对中心）——v5 停机声明的出路
- v5 M2 flip 适用性预检（`_direct_escape` 行 980-985）：要求"两 pad 距对侧轨 ≥ 0.38
  （pad 对整体在轨道带外）"才允许 flip 直连
- **冲突**：轨道对齐 pad 对中心后 pad 对中心落在轨道上 → flip 预检（pad 距对侧轨 0.19 < 0.38）
  恒失败 → 引脚区 flip 直连全被否 → via 换层（0.525→0.38 汇聚）v5 已证数学不可行 → 布线层无解

**方案选项（PM 裁决，禁止自行改模型重跑）**：
- **A（推荐）**：修订 flip 适用性预检——轨道对齐 pad 对中心时，适用条件改为
  "P/N 竖线不穿对侧轨道段"（新判据，v5 M2 条件是旧轨道语义）。需先出方案论证
  （新判据几何证明 + 回归单测：32 passed 基线不破坏 + 新增 flip 对齐用例），再改代码
- **B**：轨道带加宽（0.4 轨距或 P/N 轨距=pad 对距），flip 预检保持——SPEC 输入修订
  （v5 停机声明另一出路）
- C（已证伪勿重试）：引脚区 via 换层 0.525→0.38 汇聚必交叉

**建议**：选项 A 符合 v6.13 设计意图（"轨道对齐 pad 对中心时 flip 直连可用，余量 0.02"）。
v6.13 提交时标注"M3 实验性未验证"，本会话证实 flip 预检与新轨道语义不匹配。

## 3. 待做（M-E 裁决后按序）

1. **M-E 续**：裁决 A/B → 模型或输入修订 → 重解一次（禁 ≥2 次同参数重跑）→
   16 对 SOLVED + P/N 断言全过 + 等长 <0.15 + 单对 <5s
2. **M-F**：落板副本（hs_apply）→ kicad-cli DRC 高速 0 违规 + 0 未连接
3. **M-G**：topo_routability_check 门禁固化进 pipeline（L1/L2 阶段仿 G2.6，K1/K2 通用零 revA 特判；
   探针能力已在 hs_route_model，gate 接线见 pm_gate/gates.py REGISTRY + check_l*.py register + state.py STAGE_GATES）
4. 剩余风险：J2 连接器 GND 伴行 pad（-0.075 压线，J2_TO_U 走廊既有瓶颈）——逃逸桩重规划或方案裁决；
   ReDriver EQ/极性配置随通道角色变化（strap_intents 复核）；DN0-3 输入 J2 下半→U7 上排走廊斜走（布线层验证）

## 4. 关键物理事实（实测，勿重新论证）
- U7 输入 pads（x=88.83）对中心 y=49.1..40.7（步进 1.2）；输出（x=98.83）48.7..40.3
- U3 输入 pads（x=98.83）58.3..66.7；输出（x=88.83）58.7..67.1
- J2 引脚：RX0-7 物理上半（y 42.9..53.1，host 接收=UP 输出用）、TX0-7 下半（54.3..64.5，host 发送=DN 输入用）
- J3 上排（UP0-3 输入 y 43.25、DN0-3 输出 y 45.75）；J4 下排（UP4-7 y 63.95、DN4-7 y 61.45）
- 引脚区 0.4 脚距 vs 0.38 轨距 vs 0.525 via 距：flip 直连需"轨道对齐 pad 对中心"（余量 0.02）
- 新拓扑：U7=lanelane0-3（J3 上排）、U3=lane4-7（J4 下排）；J2 端方向保持（RX=UP 输出/TX=DN 输入）

## 5. 工具基线
- 求解：`cd _shared && <sharun> python3.11 -m eda_core.hs_route_model --all-v4 --board /tmp/opencode/boards/k2_v5.kicad_pcb --spec <artifacts/k2_v4/L3/SPEC_k2_v4.json> --alloc <model_solves/channel_alloc_v3/channel_alloc.json> --rules eda_core/drc_rules.json --pro <k2_v4.kicad_pro> --config <L2/route_model_config.json> --out <dir>`
- 容量地图：`--capacity-map`；PCB 重生成：`python3 eda_core/k2_gen_v5.py`（输出 k2_v5.kicad_pcb）
- 通道分配：`python3 -m eda_core.channel_alloc --spec <SPEC> --nets <18 base 逗号分隔> --out <dir>`（seg_tracks 需数据驱动补充）
- 原理图链：`cd revA && python3 split_sch.py`（filter_yaml 按卡拆分 + 自证闸门）
- 单测：`cd _shared && <sharun> python3.11 -m pytest eda_core/tests/test_hs_route_model.py -q`（基线 30 passed/8 红例既有）
- 分析一律走模型 API（探针/求解），禁一次性脚本手算

## 6. 已落盘证据（artifacts/k2_v4/L3/）
- `model_solves/hs_rebuild_v6/`：link_topology_old_topology.json（M-B）、
  link_topology_new_topology_precheck.json（M-C）、capacity_map_newtopo.json（M-E 容量）、
  hs_rebuild_summary_newtopo.json + hs_rebuild_newtopo/（M-E 求解 17 INFEASIBLE 证据）
- `model_solves/channel_alloc_v3/`：新拓扑通道分配（18 SOLVED + seg_tracks）
- `m13_v6_topology_precheck_report.md`：M-B/M-C 报告（修订版含 J2 端方向修正）
- `topology_routability_gate_plan.md`：权威计划（M-A..M-G）

## 7. 提交状态（本会话已 commit/push/tag）
- _shared：v6.14-k2-m13v6-topo-gate（probe_link_topology 家族 + 单测 + yamlloader card 校验）
- strix-halo-ioconvert：v6.14-k2-m13v6-topo-gate（网表修订 + 原理图 ECO + 报告 + M-E 证据）
- 容器根：submodule 指针更新
