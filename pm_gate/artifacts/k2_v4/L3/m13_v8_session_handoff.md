# M13 v8 Session 交接文档（2026-08-26，权威状态存档）

> 承接链：`m13_hs_rebuilder_v7_session.md` + `topology_routability_gate_plan.md` +
> `m13_v7_capacity_conflict_report.md`（旧裁决框架，已被本文档 §2.1 模型裁决取代）+
> `m13_v8_directionality_addendum.md`（方向性实证）。
> 本文档 = 新会话唯一入口。工作目录 `/home/fila/jqdDev_2025/ic_hw/strix-halo-ioconvert/revA/pcb`。

## 0. 一句话现状

TOPO 模型算出方向唯一解（纯方向分工、零旋转改动）→ 网表回退已落 → 8-21 以来原理图全链
首次真实绿 → k2_v6 板重建零漂移 + channel_alloc_v4 18/18 SOLVED + 容量地图（跨区逃逸
8 网中 UP5/DN2 被芯片电源垫 BLOCKED，待方案级处置）→ **下一步 = Card 3：电容墙复摆 +
M-E 重解一次**。

## 1. 铁律（继承，禁止违反）

七步法（先画图后算数/先单条后全量/先算容量再布线/失败带证据/先理解再修改/问题=模型改进机会/
验证闭环）；分析走模型 API（禁临时手算）；DRC 只核对不驱动；修订走输入；零 revA 特判；
假成功零容忍；反暴力迭代（同输入重跑 ≥2 次即暴力，INFEASIBLE=输入缺口证明，出方案级报告）；
冲突即停机；AGENTS.md §5/§11 全文约束。

## 2. 本会话已完成（证据均在盘）

### 2.1 TOPO 模型 PLAN 能力建成 + 唯一解裁决（用户核心诉求的交付）

- **新能力**：`_shared/eda_core/topology_gate.py`（方向性审计 + 确定性拓扑提议器：
  旋转枚举 × 流向类分配 × 计分元组 (cross_zone, alignment, rotation_changes, utilization)，
  INFEASIBLE 带证明）。单测 5/5。
- **模型裁决**（`/tmp/opencode/topo_propose_k2/topology_proposal.json`）：
  **RECOMMENDED = U7 rot=0 承载 UP0-7 / U3 rot=180 承载 DN0-7，rotation_changes=0**；
  lane 分工（M-C/M-D）、方案 A（仅 U3 rot=0）、全互换等全部 `DIRECTION_CONFLICT` 拒绝（带证明）。
- **物理根据**：DS160PR810 RX=pads1-24 一侧列 / TX=pads33-56 对侧列，通道单向
  （RX_i→TX_i）→ 每芯只能整体服务单一流向。PM 已裁决：**不存在"双向通道"芯片**
  （PS8480/PI3EQX16000 同为单向通道堆叠），换芯片调研已搁置，专注原方案。
- 旧报告 §6 的 A/B/C 三选一裁决框架**作废**——模型直接给出唯一解，不再需要人工选。

### 2.2 输入修订已落（纯方向分工）

- `revA/boards/ioconvert_v2.yaml`：32 个 PCIE 网回退为纯方向分工
  （`git diff 048dea4` == 0 字节级）；Connectors 页 columns 3→2、Power 页 columns 2→3
  （页容量验算：BIG_COL_START=50+columns×80+70/STEP=100，余量 ≥26）。
- `SPEC_k2_v4.json`（= artifacts/k2_v4/L3/，artifacts/L3 为符号链接）：
  corridors bands 方向分组（upper=UP0-7 / lower=DN0-7，J2_TO_U 与 U_TO_MCIO 均同）；
  components.redriver 注入 `pad_groups`（rx/tx 16 脚×2，真源=符号库引脚名）+ `channel_count=8`。
- 归属文档：`card1_0_loader_fix_attribution.md` / `card1_1_connectors_columns_attribution.md` /
  `card1_2_fix_attribution.md`。

### 2.3 原理图链三层排雷（8-21 起潜藏缺陷，被逐层揭开）——首次真实全链绿

| 层 | 缺陷 | 修复（位置） |
|---|---|---|
| loader | 双卡同 refdes U1 双符号（K1=QFN-32/K2=LQFP-48）崩溃 | `_shared/schlib/loader/yamlloader.py` (ref,card) 实例化 |
| 渲染 | 标签按卡无关 net.pins 遍历致碰撞 | `_shared/schlib/layout/wirerouter.py` 标签源=实例 comp.nets |
| 页容量 | Connectors/Power 页溢出 | yaml columns 修订（见 2.2） |

结果（真实首跑，非陈旧产物）：`pytest revA/tests/test_v5_invariants.py` **50/50 绿**
（含修订的 ECO#31 超驰类 10 断言 + I2C2 卡域断言 + 纯方向断言）；ERC **0 error / 372 warning**
（endpoint_off_grid，新基线）；结构三基础 6/6；split_sch 自证 K1 86网/K2 166网 零悬空；
节点归属 4 断言全 PASS（UP→U7 RX0-7/TX0-7、DN→U3、各 32 脚、J2 端映射）；
出图门禁 22 PASS / 5 STALE / 3 SKIP；gen_card_nets 对 048dea4 锚点 **字节级一致**；
ECO 状态机 S2→S3→S4 全 PASS 推进至终态。

**测试附带修订**（`revA/tests/test_v5_invariants.py`，均带归属注释）：
① M-D 方向断言改纯方向口径；② ECO#31 超驰 ECO#10 的 USB/SBU 块 10 条按真源修订
（真源=doc/ECO31 + README + yaml 交叉核对，非恒真）；③ I2C2/U1 断言卡域化
（卡1=KBU6 无 I2C2 守卫 + 卡2=CBT6 I2C2↔J11 正向断言）。

**重大发现（假成功）**：M-D（dfc76cb）宣称的"全链绿"是对 8-20 陈旧产物的验证——
8-21（ECO#31 加 U8/U11/U12 等）起生成器必崩，master 从未真实绿过。本次为 8-21 后首次。

### 2.4 Card 2 完成（产物在盘，经我复核）

- `k2_gen_v5.py` 输出路径环境变量覆盖（`K2_OUT_PCB/K2_OUT_JSON`，默认零变化）。
- **k2_v6 板重建**（`/tmp/opencode/boards/k2_v6.kicad_pcb`，⚠ 易失）：
  `model_solves/k2_v5_v6_diff_report.json` verdict=PASS — 101 器件/508 pads 相同、
  layout_drift diff_count=0、**rotation_changes=0**、net_rebind 64 断言 0 失败。
- **channel_alloc_v4**（`model_solves/channel_alloc_v4/`，方向分组）：**18 网全 SOLVED**。
- **容量地图**（`model_solves/capacity_map_v6/`）：
  - 区域：U3_region 8/8 OK；J2_region 7/8（UP_OUT7 blocked）；U7_region 4/8；MCIO_region 5/8
  - **8 跨区网逃逸专查（cross_region_8nets_escape.json）**：
    | 逃逸区 | OK | BLOCKED（障碍：实测距/需求） |
    |---|---|---|
    | J4→U7 输入（UP4-7 跨区） | UP4/UP6/UP7 | **UP5 ← VREG2_U7（0.40/0.2）** |
    | U3→J3 输出（DN0-3 跨区） | DN0/DN1/DN3 | **DN2 ← VREG2_U3（0.35/0.2）** |
    | J3→U7 输入（UP0-3 本区对照） | UP0-2 | UP3 ← GND（0.40/0.175） |
    | U3→J4 输出（DN4-7 本区对照） | DN6/DN7 | DN4 ← GND（0.31/0.175）、DN5 ← GND（0.07/0.175） |
  - BLOCKED 共性：**芯片电源垫排（VREG2/GND）挤占逃逸净空**，距需求差 0.075-0.325，
    非跨区拓扑本身的问题（本区对照组同样有 BLOCKED）→ 方案级处置空间在逃逸形态/轨道/电源垫。

### 2.5 Card 1.3 完成：出图门禁 STALE 重签包（待 PM 执行）

`m13_v8_resign_package.md`：5 条 C 类（LAYOUT-03/04、POWER-02、LAYOUT-06、DOC-01）
STALE 机制代码级钉死（签署账本锚点哈希 ≠ 现图哈希；语义失效机器层不可见）；
重签命令已备好（§三，PM 亲自执行，禁代签）→ 复跑门禁刷新落盘 → `verify_signature` 复核。

## 3. 待做清单（新会话按序执行）

### Card 3（立即，主线大考）

```
【任务】电容墙复摆 + 容量 BLOCKED 处置 + M-E 重解一次（纯方向分工最终验证）
【工作目录】/home/fila/jqdDev_2025/ic_hw（求解用 _shared + sharun python3.11）
【输入现状】k2_v6 板（/tmp，若失则 k2_gen_v5.py 重生成，K2_OUT_PCB 覆盖）+
channel_alloc_v4（18 SOLVED）+ SPEC 方向分组 bands + 上表容量证据
【步骤】
1. 处置容量 BLOCKED（先探针后动手，方案级口径）:
   对 UP5←VREG2_U7、DN2←VREG2_U3、UP3←GND、DN4/DN5←GND 五处，逐个用模型探针
   枚举逃逸形态（flip/In2 换层/轨道错位）——容量探针已输出 fail_forms，先查现有
   形态库是否有解；有解→记录形态参数进求解输入；五处全无解→出方案级缺口报告
   （电源垫排挤占 = 布局/封装输入层缺口），停机上报，禁止硬挤
2. 电容墙复摆: cap_wall_solver（side=up/down 已泛化）对 C17-C32（DN，U3 J2 侧下带）
   与 C49-C64（UP，U7 J2 侧上带）按 k2_v6 + channel_alloc_v4 轨道重摆——
   必须与已分配轨道错开（v7 根因①=电容压轨道 -0.075 的教训）→ cap_wall_apply 落板
3. M-E 重解一次（同输入禁跑第二次）:
   cd _shared && sharun python3.11 -m eda_core.hs_route_model --all-v4
   --board /tmp/opencode/boards/k2_v6.kicad_pcb
   --spec strix-halo-ioconvert/revA/pcb/pm_gate/artifacts/L3/SPEC_k2_v4.json
   --alloc strix-halo-ioconvert/revA/pcb/pm_gate/artifacts/k2_v4/L3/model_solves/channel_alloc_v4/channel_alloc.json
   --rules eda_core/drc_rules.json --pro <k2_v4.kicad_pro 见 v6 用法>
   --config strix-halo-ioconvert/revA/pcb/pm_gate/artifacts/k2_v4/L2/route_model_config.json
   --out strix-halo-ioconvert/revA/pcb/pm_gate/artifacts/k2_v4/L3/model_solves/hs_rebuild_v8/
   验收: 16 对数据对 SOLVED + P/N 断言 + 等长 <0.15 + 单对 <5s；INFEASIBLE→证据表停机
【产出】五处 BLOCKED 处置结论 + 电容墙落位证据 + 求解 summary + 逐对时长/等长
【MUST NOT】同参重跑；为求解改 SPEC/alloc 无证据；手补走线；动旋转/布局
```

### Card 1.3 执行段（PM 签署，可与 Card 3 并行）

按 `m13_v8_resign_package.md` §三：PM 亲自跑 5 条签署命令 → 复跑 gate_schematic 刷新
落盘签名（预期 27/0/3，锚定新哈希）→ verify_signature 复核。

### Card 4（Card 3 绿后）

hs_apply 落板副本 → `check_s2_locked`（226/226 locked）→ kicad-cli pcb drc --format json →
drc.json 口径：高速 0 违规 + unconnected_items==0；残余→trace 到 L1/L2/L3 规范层。

### Card 5A（门禁固化）∥ 5B（指纹修复）

- 5A：`topology_gate`（方向性+提议器）接入 `pm_gate` 为 L1/L2 阶段 gate（仿 G2.6，
  K1/K2 通用零特判）；同时把本次会话的**页容量预扫**沉淀为 `probe_sheet_capacity`
  探针（Card 7 内容，用户已背书"原理图也是模型的一部分"）。
- 5B：`verify_cli --quick` 场指纹漂移修复（SPEC 声明 37082605138128e7 ≠ 当前
  0aaccfbad00613a0，SPEC 编辑前已存在）→ 查漂移源（escape_spec/in2/j2/入口板/工具链），
  走正规重签流程，**禁手改指纹字段**。

### Card 6（归档/提交——须用户明示后执行）

### 既有基建备注

- `_shared` 测试基线：`sch_gate/tests/test_baseline_regression.py` 3 项既有失败
  （子进程 ModuleNotFoundError: eda_core，环境/路径问题，A/B 对照确认与代码改动无关）；
  `test_pre_receive_server.py` 1 项既有跳过（key_v2 产物缺失）。
- ERC warning 基线 372（endpoint_off_grid）；`test_v5_invariants.py` 基线 50 绿。

## 4. 关键物理事实（实测，勿重新论证）

- U7@(93.825,44.7) rot=0：RX 列 x=88.85（左/朝 MCIO）、TX 列 x=98.85（右/朝 J2）
- U3@(93.825,62.7) rot=180：RX 列 x=98.85（右/朝 J2）、TX 列 x=88.85（左/朝 MCIO）
- RX pads=[1,2,4,5,7,8,10,11,13,14,16,17,19,20,22,23]，TX pads=[33,34,36,37,39,40,42,43,
  45,46,48,49,51,52,54,55]，channel_count=8，单向通道
- J2@(133.825,53.7)：RX0-7 上半 y42.9-53.1（UP 输出落点）、TX0-7 下半 y54.3-64.5（DN 输入源）
- J3@(59.5,44.5)/J4@(59.5,62.7)：lanes 0-3↔J3、lanes 4-7↔J4
- 板边 x∈[23,143] y∈[33,71]；片间缝 y≈49.3-58.1（U7 下缘-U3 上缘）
- 网表语义：UP0-7 输入→U7 RX0-7、UP_OUT0-7←U7 TX0-7；DN0-7 输入→U3 RX0-7、
  DN_OUT0-7←U3 TX0-7；J2 端 UP→RX 上半、DN←TX 下半（方向映射不变）

## 5. 工具基线

- 求解：见 Card 3 命令块（--all-v4）
- 板重生成：`cd strix-halo-ioconvert/revA/pcb && python3 eda_core/k2_gen_v5.py`
  （`K2_OUT_PCB=... K2_OUT_JSON=...` 覆盖输出；输入=revA/boards/ioconvert_v2.yaml + k2_v4 布局锚）
- 拓扑探针/提议：`python3 -m eda_core.topology_gate --board B --spec S --links L --out DIR`
- 电容墙：`cap_wall_solver.py`（side=up/down）+ `cap_wall_apply.py`
- 单测：`pytest eda_core/tests/test_hs_route_model.py -q`（基线 30 passed/8 红例既有）、
  `pytest eda_core/tests/test_topology_gate.py -q`（5 绿）、
  `pytest revA/tests/test_v5_invariants.py -q`（50 绿）
- ECO：`sharun python3.11 -m eda_core.eco_gate.cli status|run|advance`（ic_hw 根；现终态 S4）
- PM 门禁：`cd revA/pcb && python3 pm_gate/cli.py status && python3 pm_gate/cli.py sstatus`
  （L3 passed、QA in_progress、S2 PASS/S3 BLOCKED——M-F 落板 DRC 后推进）

## 6. 提交状态

- `_shared`（ic_hw-shared）：本提交 = M13 v8 拓扑模型 PLAN 能力 + schlib 卡域泛化补完
  （见提交日志）；基线 0e70bd7 → 新 HEAD。
- `strix-halo-ioconvert`（ic_hw-ioconvert）：本提交 = 网表回退纯方向 + 全链首绿 +
  Card 2 产物 + 重签包 + 本文档；基线 2e8eb11 → 新 HEAD。
- 容器 `ic_hw`：submodule 指针随更。
- 未跟踪不提交：`pm_gate/artifacts/k1/*`（另一工作流）。
- ⚠ `/tmp/opencode/boards/k2_v5.kicad_pcb / k2_v6.kicad_pcb` 易失——丢失即按 §5 重生成。
