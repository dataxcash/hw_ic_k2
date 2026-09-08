# M14 v46 承接 — 架构转向（无搜索/解析构造/LLM 形态层）+ ①alloc 出厂逃逸包络预检 ENG 能力落地（休眠态）

> 承接 v45。本 session 核心 = **路线裁决 + ①实现**。v45 事实仍有效勿重推。
> **路线（用户 2026-09-08 拍板，取代旧"施工端现场补形态"模式）**：
> 求解层**解析构造（无搜索）**；缺形态=**停机上报**；形态补全=**LLM+案例库+开源
> SAMPLE 直接构造→一次性确定性验证→入库**；alloc **出厂解析预检**（上游消化行位
> 缺陷）；施工端退化为**读施工图纯执行**。建筑业类比：可行性=结构图；实施层=
> 施工图+工程计划（**本层缺位 = v43-45 反复摸的总根因**）；现场不画图不排计划。
> 设计文档：`mcio_feas_step2/m14_alloc_escape_precheck_design.md`（含 v45→v46 转向表）。

---

## 0. 一句话状态

ENG `_shared` **+1 能力 commit `3f33cbc`**（alloc 出厂逃逸包络预检 E2/E3，**缺省休眠**
= config 未声明即旧行为字节不变）；freeze 0/0/0 已 lock。K2 侧**未启用**（escape_check
声明 + alloc 重跑 + e2e 一次性验证 = v47 唯一工作）。C-1/C-3 形态从"待落码补丁"改定位
= **形态库条目**（kb 模板 784034b），供 alloc 预检（行位判据）与②施工图层消费——不在
施工端硬解。

---

## 1. 钉死事实（v46 增量；勿重推）

| # | 事实 | 依据 |
|---|---|---|
| N1 | **alloc D2 只覆盖走廊 x_range**（K2 EAST_CHIP_TO_J2 x∈[105.25,132.65]），三类真实冲突（DN0-3 尾段穿 C79-C83 / DN5 col-top via 撞 C82 / REFCLK1 被 UP7 through-via 挤出）**全在逃逸区 x<105.25** → 结构性不可见 | v46 SPEC corridors 实读 + v44 探针矩阵 |
| N2 | K2 现 alloc 运行 **D2 实际关闭**：`route_model_config.json channel_alloc.half_pitch=None` → static_sources 未启用（alloc v4 meta 无 track_validation） | v46 config 实读 + alloc 产物核对 |
| N3 | `_alloc_static_sources` 只建**走廊 band 层**场（In2/In6）——F.Cu 不在内，电容墙/焊盘列/top via 障碍数据从未喂给 alloc | v46 solve_pipeline 读码 |
| N4 | REFCLK 行 x 域 = 跨走廊间隙/芯片区连续（v45 实证 x60-133）——E3(b) x 重叠须用**带级 band_spans 覆盖**（走廊 x_range 不足），已入 esc 参数 | v46 单测暴露 + 修正 |
| N5 | 新增 9 单测全绿；受动模块 52+53 passed 零新增回归（test_solve_pipeline 1 failed = 既有 pre-existing 勿修；真板缺失 skip 既有） | v46 pytest（plain python + AppDir python3.11 双验） |

---

## 2. 本 session 交付物

| 项 | 位置/状态 |
|---|---|
| 架构转向 + ①设计 | `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m14_alloc_escape_precheck_design.md`（含 E1/E2/E3 规格、接口、范围边界、测试计划、待决 Gate） |
| ENG 能力 commit | `_shared 3f33cbc`：`segment_corridor.escape_envelope_ok`（E2 载体行位净空 / E3(a) col-top via annulus / E3(b) 跨带 through-via 包络，band_spans 覆盖）+ `channel_alloc` escape_check 加性接线（alloc_channels/from_input/_assign_deterministic）+ `solve_pipeline`（static_sources 加 F.Cu+col_stack 层；`_alloc_escape_check` esc 组装；run_alloc 接线） |
| 单测 | `_shared/eda_core/tests/test_escape_envelope.py`（9 用例：E2 拒/过、E3a DN5 型拒、E3b 吞噬拒/存在性过、降级 pass、alloc 集成跳行位 + 加性不变） |
| 备份 | /tmp/opencode/{segment_corridor,channel_alloc,solve_pipeline}.py.bak_v46 |
| freeze | 0/0/0 已 lock |

---

## 3. v47 唯一主线：①K2 启用 + e2e 一次性验证（≤2 次）

1. **启用声明**（数据驱动，K2 侧）：
   - `k2/.../L2/route_model_config.json` `channel_alloc`：`half_pitch: 0.19`（同时激活
     D2=E1，走廊窗口校验——本应开启）+ `escape_check: {via_jogs_x:[0,0.45,...],
     via_jogs_y:[±0.45,±0.75,±1.05], via_od:0.5, keepout:0.37, half_track:0.1,
     fcu_layer:"F.Cu", band_spans:{refclk:[58,134]}}`（数值以 solve 构造常量/rules
     为准，勿照抄猜值——v45 P4：归因以真 shared 为准）。
2. **alloc 重跑**（channel_alloc CLI / solve_pipeline ③）：观察 DN0-3/DN5/REFCLK1 行位
   处置——预期 DN5@64.3 被 E3(a) 拒（C82 annulus 0.24<0.475）、跨带行位被 E3(b)
   预检约束；**证据级记录**（track_validation 含 E2/E3 条目）。
3. **solve 全量 e2e**（--all-v4 或 pipeline，一次性）：目标 18 bases SOLVED +
   REFCLK0/1 全保 + skew<0.15 + P/N≥0.175。失败处置按新路线：实现缺陷→修；**新形态
   缺口→停机上报**（不现场搜索）。
4. 合规：lock 0/0/0 → commit（若行为生效需 e2e 绿后）+ push（含 kb 784034b 待 push）。

---

## 4. 资产 / 停止态

| 项 | 状态 |
|---|---|
| ENG `_shared` | HEAD `3f33cbc`（①能力，休眠态）；freeze 0/0/0 lock；pre-existing 脏仅 escape_closure_analysis.py/install.sh + 未跟踪 .bak_v33_perball（勿 commit） |
| k2 | 未改动（config 未声明 → alloc 行为不变）；板 sha f6273de6 未动 |
| kb | 2 模板（784034b）已 commit **待 push**；v46 新增 0 模板（本 session 为能力建设非案例发现） |
| 文档 | m14_alloc_escape_precheck_design.md（设计+Gate 记录）；本 handoff |

**勿做**：勿把 C-1/C-3 当"现场补丁"落码（已改定位为形态库条目，alloc 行位修正后可能
不必要）；勿搜索式调参（新路线无搜索）；勿动 SPEC/corridor 冻结物；勿在 config 未声明
escape_check 时期待 alloc 行为变化。
