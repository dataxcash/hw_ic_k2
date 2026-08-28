# M13 v7 M-E 卡点冲突报告（最终版，含修复方案与推理证据）— 2026-08-26

> 承接 `m13_hs_rebuilder_v7_session.md` §2 卡点。v7 session 将 17/18 INFEASIBLE
> 归因于"flip 预检恒失败（轨道对齐 pad 对中心后 pad 距对侧轨 0.19 < 0.38）"。
> 本报告经模型 API 逐段诊断（非手算），**三层根因**：① flip 预检仅 flip=True 失败，
> flip=False 预检通过但走廊撞 AC 电容墙；② 上行电容墙 C49-C64 未随 M-D 网表修订
> 迁移（y 错位 10-19mm）；③ **根本矛盾：U3 rot=180 使 TX 输出朝左（x=88.825），
> 而 UP_OUT4-7 目标 J2 在右侧（x=133）——芯片旋转方向与 lane 角色冲突**。
> 修复方案选项 A/B/C 见 §6，需 PM 裁决后在新 session 按"修订输入→重生成→重解一次"执行。

---

## 1. 现象（与 v7 一致）

- 新拓扑（U7=lane0-3、U3=lane4-7）全量求解 17/18 INFEASIBLE（26.5s），仅 REFCLK0 SOLVED。
- 失败段 reason 均为 `对级对称逃逸无净空（M=… → cv=… flip=True/False pn_dist=0.400）`。
- 证据：`model_solves/hs_rebuild_v6/hs_rebuild_summary_newtopo.json` + `hs_rebuild_newtopo/`。

## 2. 诊断方法与证据落盘

所有结论来自模型 API 调用（HSRouteModel 探针/求解 + 求解器入口），禁一次性手算：
- `/tmp/opencode/diag_flip.py`：flip=False/True 两分支预检 + `_direct_escape`/`_escape_pair` 失败点
- `/tmp/opencode/diag_flip2.py`：flip=False 走廊段逐段 seg_ok 定位
- `/tmp/opencode/diag_flip3.py` / `diag_capwall.py`：U7 输出 pad 列 + 走廊内 AC 电容坐标
- `/tmp/opencode/diag_field.py` / `diag_field2.py`：障碍场坐标与 `nearest_obstacle` 语义核实
- `/tmp/opencode/diag_alltracks.py`：全 lane 轨道对 vs 电容墙冲突扫描
- `/tmp/opencode/diag_up4.py`：UP4（U3 输出侧）flip 两分支失败点
- `/tmp/opencode/solve_upstream.py` / `diag_solver_up.py` / `diag_stub_up.py`：上行电容墙接入求解器验证（含 side 泛化后单行可解、两行组合失败定位）
- `/tmp/opencode/upstream_input.py`：芯片端 pad 对中心 + 电容↔net 映射自动提取

## 3. 根因 ①：flip 预检非恒失败，真失败点在走廊撞 AC 电容（UP0-2）

### 3.1 flip 预检实测（U7 输出 UP_OUT0，track_y=48.7 = pad 对中心）

真实 pad：P=(98.825,48.9) N=(98.825,48.5)（PN 同 x，y 差 0.4 = pn_dist 0.4）

| flip | ty_P | ty_N | 预检 P | 预检 N | 后续 |
|---|---|---|---|---|---|
| False | 48.89 | 48.51 | **PASS** (48.9 ≥ 48.51+0.38=48.89, 余量 0.01) | **PASS** (48.5 ≤ 48.89-0.38=48.51) | 竖线/水平段全过 → **走廊 seg_ok FAIL** |
| True | 48.51 | 48.89 | FAIL (48.9 ≤ 48.89-0.38=48.51 不成立) | FAIL | — |

**v7 §2 归因错误**：flip 预检并非"恒失败"。flip=False 预检通过（余量 0.01），
**真正失败点 = 走廊轨道 (99.48, 48.89)→(132.65, 48.89) 被 AC 电容 pad 拦截**。

### 3.2 走廊 seg_ok 失败证据（UP0 out_U7 段）

```
corr_P 障碍: {'kind': 'pad', 'net': 'PCIE_UP_OUT3_N_U7',
             'desc': 'pad:PCIE_UP_OUT3_N_U7 (F.Cu)', 'dist': -0.075, 'req': 0.175}
```

障碍 pad 实为 **AC 电容 C56 @ (115.825, 48.9)（0402 0.4×0.5）**，y 中心 48.9 恰在
UP0 flip 展开 P 轨 48.89 上（重叠 -0.075）。`nearest_obstacle` 报告 net 名取自电容网。

### 3.3 系统性冲突：AC 电容墙 C49-C64 y 行 vs flip 展开轨道带

**k2_v5 板 C49-C64（上行 AC 耦合）y 行 = 42.9…53.4**，落在 J2_TO_U 走廊带内：

| lane | 轨道 track_y | flip 展开带 | 走廊内电容行 | 冲突 |
|---|---|---|---|---|
| UP0 | 48.7 | 48.51/48.89 | C55/C56 @ 48.3/48.9 | **重叠 -0.075**（实证） |
| UP1 | 47.5 | 47.31/47.69 | C57/C58 @ 47.7/48.0 | 重叠 |
| UP2 | 46.3 | 46.11/46.49 | C59/C60 @ 46.5/47.1 | 重叠 |
| UP3 | 45.1 | 44.91/45.29 | （44.1/44.4 与 46.5/47.1 之间） | 净空 OK（失败为另一类） |

## 4. 根因 ②：上行电容墙 C49-C64 未随 M-D 网表修订迁移

**M-D 网表修订**（v6 已提交）：`UP_OUT4-7→U3/TX0-3`（U3 输出）。但 k2_gen_v5
C49-C64 位置**继承 k2_v4 旧产物锚点**（实证 k2_v4 vs k2_v5 坐标逐项一致），未迁移：

| net | 芯片输出 pad（新拓扑真源） | AC 电容（k2_v5 现状） | y 错位 |
|---|---|---|---|
| UP_OUT0 | U7 (98.825, 48.9) | C49 (127.825, 53.1) | 4.2mm |
| UP_OUT4 | **U3 (88.825, 58.5)** | C57 (111.825, 47.7) | **10.8mm** |
| UP_OUT5 | **U3 (88.825, 59.7)** | C59 (105.825, 46.5) | 13.2mm |
| UP_OUT6 | **U3 (88.825, 60.9)** | C61 (103.825, 44.1) | 16.8mm |
| UP_OUT7 | **U3 (88.825, 62.1)** | C63 (100.800, 42.9) | **19.2mm** |

UP_OUT4-7 电容在 U7 侧走廊（y 42.9-48.0），信号源在 U3 输出（y 58.5-62.5），
**跨 U7 器件区 15-19mm，物理不可达**。下行侧 C17-C32 有求解器（cap_wall_solver）
自动摆位且位置合理（y 60-66 U3 侧），**上行侧未接入求解器**——系统缺口。

## 5. 根因 ③（根本）：U3 rot=180 使 TX 输出朝左，与 UP_OUT4-7→J2 方向矛盾

### 5.1 实测芯片方位

```
U3 @ (93.825, 62.7) rot=180.0  →  TX 输出 pad 全部在 x=88.825（U3 左侧）
U7 @ (93.825, 44.7) rot=0.0    →  TX 输出 pad 全部在 x=98.825（U7 右侧）
```

- U3 pad 55 (88.825, 58.5) = PCIE_UP_OUT4_P_U7（TX 输出，物理左侧）
- U3 pad 45-55 全部 (x=88.825) = UP_OUT4-7 + DN_OUT4-7（TX 输出全在左侧）
- U3 pad 1-24 全部 (x=98.825) = UP4-7/DN4-7 输入（RX 全在右侧）

### 5.2 矛盾

M-D 拓扑：`UP4-7 | J4/TX0-3 | U3/RX0-3 | U3/TX0-3 → J2/RX4-7`（方向 UP，MCIO→J2）。
J2 在 x=133（右侧）。**U3 的 TX0-3 物理在 x=88.825（左侧），UP_OUT4-7 从 U3 输出
要横穿 U3 本体 + U7 区域才能到右侧 J2**。唯一绕行通道（U7 与 U3 之间 y 49.7-57.7
约 8mm 窄缝）被 U7 去耦/电源器件占据，布线模型无此绕行能力（逃逸段仅支持
直连/via 换层确定性折线）→ 布线层无解。

### 5.3 rot 来源（历史遗留）

- k2_v4（旧产物）：U3 @ (93.825,62.7) rot=180（旧拓扑 U3 只做 DN 下行去左侧 MCIO，rot=180 合理）
- k2_v5：U3 rot=180 原样继承（`ref_anchors` 锚点提取，零设计决策）
- **M-D 修订改了网表（UP_OUT4-7→U3）却没改 U3 旋转方向** —— 配套输入修订遗漏。

### 5.4 影响范围

- UP4-7（U3 输出→J2 右）：全部 INFEASIBLE（out_U7 段失败，M=(88.825,58.7) 等）
- DN0-3（J2/TX 下半→U7 上排输入）：INFEASIBLE（input 段失败）——同类方向问题
- U7 侧 UP0-3：flip=False 预检过但走廊撞电容（根因 ①）

## 6. 修复方案（PM 裁决，禁止自行改模型重跑）

| 选项 | 内容 | 判定 |
|---|---|---|
| **A（推荐）** | **U3 旋转改 0**（TX 翻到右侧朝 J2）+ 上行电容墙 C49-C64 接入 cap_wall_solver（side="up" 已泛化）迁移到 U3 输出侧 | 改输入（旋转 + 电容墙布局）→ 重生成 → 重解。需同步核 DN_OUT4-7（去 MCIO 左）方向是否仍匹配（rot=0 后 TX 在右，DN_OUT 去 MCIO 需绕行）——**DN 方向配套复核** |
| **B** | lane 重新分工（UP4-7 回 U7、DN0-3 回 U3） | 违背 M-C 冻结分组，重审拓扑，代价大 |
| **C** | 保持分工，扩展布线模型绕行能力（U3 输出→J2 斜穿走廊） | 模型大改 + 8mm 窄缝容量未验证，风险高，违背"改输入优先" |

**本 session 已完成的系统能力**（可保留，勿回退）：
- `cap_wall_stub_geom.py`：侧别判定泛化（`_U3/_U7` 芯片端 vs `_MCIO/_J2` 连接器端，
  不再写死 `endswith("_U3")`）+ `place_stubs(side="down"|"up")` 方向翻转（CHIP/CONN
  LADDER 按侧别，下行行为字节不变）
- `cap_wall_solver.py`：`solve_cap_wall(side=...)` 透传桩方向

**验证**（side 泛化后）：上行单行 8 颗可解（x=99.5+1.3i, y=46.9，桩全落位）；
两行组合在 U3 输出侧 x 域失败（C57@99.85 桩撞 U3 输入 pad 区）——即根因 ③ 的
U3 rot 方向矛盾在求解器层面同样体现，**确认需先裁决 U3 rot 再谈电容墙**。

## 7. 停机声明

按铁律"冲突即停机 + INFEASIBLE = 模型输入缺口证明 + 禁止暴力迭代"，本报告为
**方案级缺口报告**。等待 PM 裁决 §6（A/B/C）后，新 session 按
"修订输入（U3 rot / lane 分工 / 电容墙布局）→ 重生成 PCB → 重解一次"执行。
禁止改模型参数重跑（同输入重跑 ≥2 次即暴力）。
