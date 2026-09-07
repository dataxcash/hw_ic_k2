# M14 v33 — 模型链实测承接：alloc 18/18 通、画线卡 per_ball VIA_IN2 引擎缺口

> 状态：**v33 承接 = v32 决策冻结（strap_domain_v32 + 裁决 A/B/C）后，对 TOPO 模型施工链做真机实测**。
> 结果：**① SPEC corridors 补 tracks_y + band 名统一 → channel_alloc 18/18 SOLVED ✅
> ② hs_route_model 画线 18 对全 INFEASIBLE，单一根因钉死 = 芯片侧 per_ball VIA_IN2 落点
> 未接入施工模型（引擎缺口，非输入缺口）**。
> 执行纪律（用户裁决）：**全部前台自跑，禁委派（task 子代理）、禁后台长跑**。

## 0. 已钉死的根因链（勿重查，直接承接）

1. **现 SPEC v31 corridors 缺 `tracks_y`**（band 轨道 y）→ channel_alloc 读它 `channels=0` → 33/18 网全 no_free_channel。
   这是 v31 §4 登记的 open（翼带 lane 指派）从没生成的直接后果。
2. **修复**：复用老 alloc v4 曾 SOLVED 的 track_y 值（J2/J3/J4 连接器物理位置未变）：
   - EAST `dn`(DN0-7/J2 下排)=[58.3,59.5,60.7,61.9,63.1,64.3,65.5,66.7]；`up`(UP_OUT0-7/J2 上排)=[40.3,41.5,...,48.7]；refclk=[45.7,50.5]
   - WEST `up`(UP0-7/J3·J4)=[40.7,41.9,...,49.1]；`dn`(DN_OUT0-7)=[58.7,59.9,...,67.1]；refclk=[45.7,50.5]
   → **alloc 18/18 SOLVED**。
3. **band 名契约**：模型 `_track_y_from_alloc` 跨走廊**按同 band 名同 idx 取轨**。v31 方向专属名
   （EAST `a_per_dn_in` / WEST `a_pet_dn_out`）断裂 → out 段 INFRA_ERROR"无通道分配"。
   **修复**：统一为跨走廊共享名 `dn`/`up`/`refclk`（保留 band_legacy 字段）→ out 段消失。
4. **画线全 INFEASIBLE（18/18），单一症状**：`flip=True 逃逸 P/N 极性交叉 min_edge -0.205 < 0.175`
   （@ 芯片体内 x≈84-97, y≈40-63；v11 的 30 处交叉同款）。
5. **根因（引擎级，最终）**：DS320 芯片 J2 侧网（per_ball 判定 **32 球 VIA_IN2**：球下 via → **In2 内层东穿**
   → 东走廊 x≥105 上翻 F.Cu → J2）需要"**球旁 via → In2 穿越段**"逃逸形态；但 hs_route_model
   芯片侧逃逸只有老"**贴走廊边 F.Cu 直连**"形态（老芯片引脚恰贴走廊边 x≈98.8 才成立）。DS320 球在
   芯片体内（J2 侧球 x≈82-94，离东走廊 x105 有 20mm+），直连硬套 → P/N 相向交叉全拒。
   **per_ball 落点（method=VIA_IN2/DIRECT_F.Cu + bx/by）从未接入 hs_route_model = solve_pipeline
   断裂点 4 的芯片侧版本（审计文档 MODEL_CONTRACT_AUDIT.md §3 明列）。**

## 1. 本 session 改动清单（未 commit，冻结区 0/0/0 未动）

- `k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json`（可写区）：+6 band `tracks_y` + band 名统一
  dn/up/refclk + strap_domain_v32 块。备份 `.bak_v32_tracks`、`.bak_v32`。
- 新增/更新文档：`m13_v32_session_handoff.md`（裁决/计算书/G5）。
- _shared/eda_core **零改动**（本 session 全程未碰冻结引擎）。

## 2. 下 session 承接（NEW SESSION，全部前台自跑，禁委派）

**目标**：把 per_ball VIA_IN2 落点接进 hs_route_model 芯片侧逃逸 → 重跑 → **18 对 SOLVED 坐标** → 落板 → DRC → QA。

### 步骤 0：环境确认（前台，5 分钟内）
- 板 = `k2/k2_v4.kicad_pcb`（sha f6273de6，444 只读）；引擎源 = 容器根 `_shared/eda_core/`（34983b6，555 冻结）。
- SPEC（已含 tracks_y + dn/up/refclk）→ 直接可用。验证：`python3 -m eda_core.channel_alloc --spec <SPEC> --nets "18base" --out /tmp/a` 应 18/18 SOLVED。

### 步骤 1：读码定位注入点（禁改前先读透，一次想清）
- `_shared/eda_core/hs_route_model.py`：
  - `solve_chain_v4`(L3672) → `_chain_segments(base)` 分段 → `solve_pair_v4(sp,sn,base,segname,...)`（每段调用点）
  - `solve_pair_v4` 内芯片侧/连接器侧端点逃逸调用 `_escape_pair`/`_escape`/`solve_pair_segment` 的位置与方向参数
  - `_escape_pair`(L1153+)：`landing_pair` 已是"连接器侧落点驱动"既有模式（`_landing_escape`），芯片侧调用"恒回退自搜"——**芯片侧 per_ball 落点驱动复用同一模式**
  - `__init__`(L470-496) `landing` 参数 + `_landing_by_net`（status==ASSIGNED + landing.x/y）
- per_ball 落点源：`k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/per_ball_escape_6L_report.json`
  per_ball[]：{name,signal,band,lane,side,method(VIA_IN2|DIRECT_F.Cu),bx,by}
- signal→net 映射：同目录 `c5_chip_level_expect_matrix_v28.json` + `ds320_symbol_pins.json`（机器提取）

### 步骤 2：实现（最小改动，一次改对）
- 芯片侧端点 method==VIA_IN2 的链段：构造"球 pad → 球旁 via（落点=per_ball 给出或按球坐标推导）→
  **In2 段（可穿芯片体下，东穿/西穿）→ 走廊上翻 via → 轨道"**形态；method==DIRECT_F.Cu 保持现状直连。
- 新增正式输入（复用 landing 模式）：per-net 芯片侧落点表 {net: {method, via_x, via_y}}，
  缺省空 = 行为不变。CLI main()(L4058) 加正式入参。
- 连接器侧 landing 语义、走廊/容量/REFCLK 直通逻辑不改。确定性、零随机、零 revA 坐标字面量。

### 步骤 3：合规（引擎改动）
- ECN 记录：`cd k2 && python3 _shared/pm_gate/cli.py --project k2_v4 ecn new "<reason: 芯片侧 per_ball VIA_IN2 落点接入 (断裂点4 芯片侧)>"`
- `bash k2/pm_gate/freeze_ctl.sh unlock` → `cp hs_route_model.py .bak_v33_perball` → 改 → `lock` → 报 0/0/0。禁 chmod。
- 回归：`_shared/eda_core` 单测（test_escape_landing.py 等）无回归。

### 步骤 4：重跑与验证（前台，禁暴力迭代，同参重跑 ≤2）
- `channel_alloc` 18/18 → `hs_route_model --all-v4`。
- 完成判据：18 对（DN0-7/UP0-7/REFCLK0/REFCLK1）SOLVED + skew<0.15 + P/N 净空≥0.175 + 坐标 JSON 落盘。
- 若仍 INFEASIBLE：读 hs_rebuild 证据（哪段/缺口/最近障碍），判定是落点推导错还是形态缺分支，
  修一次再跑；第 3 次不过 = 停，带证据回方案层（禁硬闯）。

### 步骤 5：SOLVED 后（机械施工，仍前台）
- 落板（需 pcbnew 环境）：`AppDir/sharun python3.11` 跑 hs_apply / 既有落板 reproduce 模式（先备份板）
- DRC 归零（kicad-cli pcb drc --severity-error）+ 净空复核 → QA 门禁 G4.x（前置：check_qa PCB_PATH 缺陷 ECN）
- S 状态机 srun/sadvance；SPEC/证据 commit 预备（git 前 unlock、后 lock）。

## 3. 关键文件索引

- SPEC：`k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json`（已含 tracks_y + band dn/up/refclk）
- alloc：`/tmp/alloc_v33c/channel_alloc.json`（18/18；临时，需重生成）
- solve 证据：`/tmp/solve_v33d/hs_rebuild_summary.json`（18 INFEASIBLE + flip 交叉证据）
- per_ball 落点：`k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/per_ball_escape_6L_report.json`
- 引擎：`_shared/eda_core/hs_route_model.py`（`__init__` landing L470 / `_escape_pair` L1153 / `solve_chain_v4` L3672 / `solve_all_v4` L3783 / `main` L4058）
- 审计：`_shared/docs/MODEL_CONTRACT_AUDIT.md`（断裂点4）；契约：`_shared/docs/SOLVE_PIPELINE_CONTRACT.md`

## 4. G5 收尾自检（v33）

- 消费：per_ball_escape_6L_report（落点源）、channel_alloc/hs_route_model 全链真机实测、老 SPEC .bak_v30
  tracks_y、C5 映射源、MODEL_CONTRACT_AUDIT。
- 停止/熔断：无暴力迭代（alloc 2 轮修正均依据模型输出证据）；未触 G4。
- 禁违反项：冻结区 0/0/0 未动；SPEC 改动先备份；未 chmod；未委派后台；根因靠模型原始输出钉死，非猜。
- 边界：引擎缺口已定位到"芯片侧 VIA_IN2 形态缺失 + 落点未接入"；修复 = 步骤 2 的有界改动。
