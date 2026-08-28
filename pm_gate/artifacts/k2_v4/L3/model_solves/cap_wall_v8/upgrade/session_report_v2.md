# cap_wall_v8 upgrade（v2）— session report（2026-08-27）

## 1. 结论（一句话）

**B+A 裁决执行完成：cap_wall_solver 通用能力升级（轨道感知摆位 + x 平移自由度）→ 7/7 单测全绿 → k2_v6 双墙有序重解一次通过 32/32（逐颗轨净空 0.1825>0）→ 落板校验全过（恰 32 颗移动/网络一致/旋转零改/101 器件/逐颗轨+桩净空数值全>0）。板已更新，原停机证据保留。**

## 2. v8 失败签名 → v2 根因修复对照

| v8 失败签名 | 根因 | v2 修复 |
|---|---|---|
| DN/UP 各 0/16，行 y 只能落 SPEC band [60,66]/[44,47]（全在轨道带内） | 行 y 枚举域 = SPEC band，无轨道净空约束 | 行 y 只从"带外合法窗口"枚举（轨道排除带补集 ∩ 板内 ∩ 非器件区），带内构造性禁止 |
| DN：x=84.6 槽位撞 U3 桩扇出，x 网格固定无法让位 | 求解器缺 x 自由度 | 行起点固定步长序滑动（0.5mm），撞桩/撞垫让位 |
| UP：x=99.5 撞 U7 桩扇出 + band 内双行无网格组合 | 同上 + 行结构僵化 | 单行优先（UP 16 颗单行落 y=39.4），放不下才确定性拆双行（DN 双行 57.8/68.0） |

## 3. 窗口公式与参数真源（全数据驱动，零字面量）

```
row_excl = 轨半带 + 线半宽 + 净距 + cap半高
         = (p_width+p_gap)/2 + p_width/2 + clearance(PCIe85) + PAD_H/2
         = 0.19 + 0.1025 + 0.175 + 0.25 = 0.7175 mm
窗口 = [板框 y 域] − ∪[track_y ± row_excl] − 器件条带（侵入走廊≥2mm 的非容器件）
via_excl = via_r + 线半宽 + 净距 = 0.4525（桩 via ↔ 轨中心线）
seg_excl = 桩线半宽 + 线半宽 + 净距 = 0.38 （桩段 ↔ 轨中心线）
```
- 参数真源：`_shared/eda_core/drc_rules.json`（diff_pair.p_width/p_gap、clearance.net_classes[PCIe85]、manufacturing.min_via_diameter），经 `load_track_clearance_params()` 读取。
- 轨道真源：`channel_alloc_v4/channel_alloc.json` meta.channels（layer=F.Cu ∩ 走廊 x 相交）；走廊 x_range 取 SPEC corridors。DN 墙 16 轨（U_TO_MCIO upper 40.7-49.1 + lower 58.7-67.1），UP 墙 16 轨（J2_TO_U upper 40.3-48.7 + lower 58.3-66.7）；refclk（In6.Cu）层过滤排除。
- 实测窗口：DN `[33,39.9825] [49.8175,57.9825] [67.8175,71]`；UP `[33,39.5825] [49.4175,57.5825] [67.4175,71]` —— 与复核人独立推算（57.98/67.82/39.58/49.42）一致。器件条带两墙均为空（U3 侵入 1.4mm<2mm 阈值，由障碍场逐点净距处理）。
- SPEC `capacitor_walls.band_y` 在 v2 模式下不参与枚举报废口径（[60,66]⊂轨带，无合法位）；SPEC 文件本身未改（MUST NOT 遵守）。

## 4. 升级 diff 摘要（源码 3 文件，CLI/数据契约形态不变，新增可选入参）

- `eda_core/cap_wall_stub_geom.py`：pad 几何由布局 rot 派生（`pad_sign_of_rot`：rot=0 → pad1 在 −0.35，与板实测一致）；桩阶梯改"pad 外向符号"参数化（CHIP/CONN 规范形 ×外向符号，旧下行 rot=180 语义逐字节兼容）；新增 `track_band` 障碍类型（via/段双口径）；新增 `load_track_clearance_params()`（drc_rules 数据驱动）、`wall_obstacles()`（已解墙→障碍注入）。
- `eda_core/cap_wall_solver.py`：新增 `load_track_bands / board_outline_y / board_device_strips / legal_row_windows / _window_row_cands / _x0_cands / _split_rows_by_pad_y / track_margins`；`solve_cap_wall` 增可选入参（alloc_path/drc_rules_path/rot/cap_nets/extra_obstacles/x_slide_step…）：带外窗口确定性枚举 + x 平移 + 单行优先 + 双墙注入 + 逐颗轨净空断言 + 失败取证（前 40 条阻塞明细）；无 alloc 时走旧 band 模式（legacy 契约保留）。
- `eda_core/cap_wall_apply.py`：`--board/--escape-spec/--groups/--spec` 参数化（默认=旧路径）；旋转零改契约（板原 rot 逐颗读回保留，布局 rot≠板 rot → 拒绝）；任意 refs 集（32 颗双墙）；stubs 内嵌优先（求解器权威产出）+几何复核；ac_caps at 同步；groups 泛化同步（仅含 cap_x/cap_y 字段的网）。
- 通用性：零 `if net=='xxx'`，坐标/规则全从板+alloc+drc_rules 读取；K1/K2 通用（侧别仅经 side 参数与走廊入参表达）。

## 5. 求解（阶段 2，门控通过）

- 驱动 `/tmp/opencode/cap_wall_v8_upgrade_solve.py`：输入=板实测（net 映射/TX pad y/rot=0）+ SPEC 走廊（DN [75,90]、UP [99,128]=v8 口径）+ alloc_v4 + drc_rules。DN 先解 → 落位（pad+64 桩中 32 条）注入 UP 障碍场；每墙恰求解 1 次，无同参重跑。
- 结果：**DN 16/16**（双行 y=57.8/68.0，x0=75.5）+ **UP 16/16**（单行 y=39.4，x 99.5→119.0）；容量断言全 PASS；逐颗轨净空 32/32 = 0.1825>0（门控数值见 solve_v2.json gate_pre_apply）。

## 6. 落板与校验（阶段 3，全过）

- `cap_wall_apply --board /tmp/opencode/boards/k2_v6.kicad_pcb`：32/32 at 变更、括号平衡、无其他 diff、旋转零改（全 0）、备份 `/tmp/opencode/apply_backup/apply_20260827_094638`、回读复验通过；64 桩重生成 + ac_caps 32 同步 + same_dn 8 网 cap 坐标同步。板 sha：aa8b3f07…→9b6e28c3…。
- 独立校验（`/tmp/opencode/cap_wall_v8_upgrade_verify.py`，落板后文件重新解析，不复用求解器自述）：恰 32 颗移动 ✓ / 网络名前后一致 ✓ / 旋转零改 ✓ / 器件 101 ✓ / 目标外 footprint 未动 ✓；**逐颗轨净空全>0（最差 0.1825）+ 逐颗桩净空全>0（最差 0.025：DN 行1 相邻 cap pad↔桩段，距 0.400 vs 需求 0.375，口径=既有 STUB_VIA_DIST 中心线约定）**。

## 7. 单测清单（7/7 绿，`eda_core/tests/test_cap_wall_upgrade.py`）

| # | 测试 | 覆盖要求 |
|---|---|---|
| 1 | test_window_computation_synthetic | 窗口计算正确性（相邻轨 1.2<2×0.7175 → 轨间无窗口） |
| 2 | test_window_params_k2_data_driven | K2 真源校准：参数全从 drc_rules 读；窗口边界=复核人推算（57.9825/67.8175/39.5825/49.4175） |
| 3 | test_in_band_row_rejected | 带内行位被拒（求解结果 |y−轨|>row_excl） |
| 4 | test_in_band_position_pad_check_rejects | track_band 障碍显式拒绝带内位置（双重拦截） |
| 5 | test_two_wall_mutual_exclusion | 双墙互斥（先解墙注入后不得压垫，落位必须差异） |
| 6 | test_determinism | 确定性（同输入两次求解字节一致） |
| 7 | test_legacy_band_mode_contract | legacy 契约保持（无 alloc → 旧 band 模式 rot=180） |

运行：`cd strix-halo-ioconvert/revA/pcb && /home/fila/jqdDev_2025/ic_hw/AppDir/sharun python3.11 -m pytest eda_core/tests/test_cap_wall_upgrade.py -v`

## 8. 合规声明

- 每墙求解恰 1 次；无同参重跑（单测确定性用例为任务书要求的测试项，非生产重跑）。
- 未改 hs_route_model/SPEC/alloc/yaml；未改电容网络绑定（仅位置）；未动旋转；未摸 git；未跑 --all-v4。
- rot 契约冲突（旧工具 rot=180 输出 vs 板 rot=0 + "旋转零改"）按任务升级范围在 apply 侧解决（保持板原值），无自决设计变更。
- 子模块工作树中 `gate_reports/*`、`state_k2_v4.json` 的 M 状态为并发外部活动（v8 报告已声明），与本 session 无关；本 session 写盘 = 3 个 eda_core 源码 + tests/ + upgrade/ 产物 + escape_spec/wp1_groups（apply 契约写入）+ /tmp 工件。

## 9. 产物清单（cap_wall_v8/upgrade/）

| 文件 | 内容 |
|---|---|
| solve_v2.json | 双墙求解原始结果 + 输入快照 + input_fp + 逐颗轨净空门控数值 |
| apply_report_v2.json | 落板不变量校验（32 移动/网络/旋转/101 器件/板 sha） |
| clearance_verify_v2.json | 逐颗轨净空 + 逐颗桩净空数值（32 颗全量明细） |
| session_report_v2.md | 本文件 |
| （原停机证据）../solve.json 等 5 件 | 保留未删 |
