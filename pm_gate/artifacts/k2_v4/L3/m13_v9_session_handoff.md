# M13 v8 续接 — 迁移后 NEW SESSION PROMPT（2026-08-28）

> 权威承接：`/home/fila/jqdDev_2025/ic_hw/MIGRATION_GUIDE_OLD_SESSIONS.md`（repo 拆分路径映射/命令变化/踩坑）
> + 本文档。工作模式：**TASK MGR 拆卡 → 用户转发 WORKER → 我复核**（不启动后台、不亲自施工）。
> 主线：通过 K2 高速域实施，持续完善 eda_core（可行性门禁 + 施工模型）。

## 0. 开工第一动作
```bash
cd /home/fila/jqdDev_2025/ic_hw/k2 && /home/fila/jqdDev_2025/ic_hw/AppDir/sharun python3.11 \
  /home/fila/jqdDev_2025/ic_hw/_shared/pm_gate/cli.py --project k2_v4 sstatus
# 红队（开工必查）：
#   ... --project k2_v4 falsify list   （open finding 必须逐条驳回）
```

## 1. 迁移事实（勿混淆）
- 容器 4 平级子模块：`_shared`(ic_hw_eda 框架) / `key_v2` / `k1` / `k2`(ic_hw-k2)。
- 老目录 `strix-halo-ioconvert/` 已归档冻结，**禁止向老 repo 提交**。
- M13 在途工作全部迁到 `k2/pm_gate/artifacts/k2_v4/`。
- 命令用**脚本路径**（`_shared/pm_gate/cli.py`），禁用 `-m pm_gate.cli`（k2/pm_gate 是纯配置目录会遮蔽框架）。
- import：`board_model` → `eda_core.board_model`；`board_model.geometry` → `eda_core.geo`。
- 废弃：run_pipeline.py / layout_engine / routing_engine / drc_checker / eda_core/k2_*.py。

## 2. 已定案（勿重做、勿再选方案）
1. **TOPO 唯一解**：U7 rot=0 承载 UP0-7 / U3 rot=180 承载 DN0-7，rotation_changes=0。
2. **原理图**：8-21 以来首次真实绿；出图门禁重签 27 PASS/0 FAIL/3 SKIP（锚点 8e1810ac）。
3. **电容墙复摆**：32/32 落位、轨道感知（cap_wall_solver 升级 + escape_spec/wp1_groups 同步）。
4. **SPEC 走廊 x_range 修订**：J2_TO_U `[98.83,131.5]`、U_TO_MCIO `[65.5,88.83]`
   （清掉走廊口连接器 GND 列冲突）。
5. **类 A 修复**：hs_route_model P/N 极性交叉双几何门（逃逸级构造期 + 段组装级复检），
   假 SOLVED 归零，零交叉契约（edge≥0.155）。
6. **类 B 判定**：DN0/DN3/DN7 = 模型排序缺陷（同链 cap 两段逃逸未协同），**非物理缺口**
   （DN1 垂直错开实证可解）。
7. **可行性门禁裁决（W5-A，核心结论）**：`routing_topology_gate.py` 定性判定——
   **资源全够**（6 逃逸区 demand==capacity 精确闭合：CAP_WALL 32/32、CHIP_U3/U7 16/16、
   CONN_J2 18/18、J3/J4 9/9；①②④⑤ 全过），**唯一缺口 = ③ J2 极性交错**。

## 3. 待做（按序，主线）
### W6-A 门禁三档裁决口径（我的判读已定，待 WORKER 落地）
把 ③ 极性从"硬失败"改为"**模型形态缺口**"警告，裁决三档：硬不可行 / 可行 / 可行+形态缺口。
J2 交错极性是标准引脚排法，物理可布（层换位），判硬不可行=把模型锅甩给板子=假警报。
### W6-B 补"层换位"引线姿势（施工层，唯一剩余形态缺口）
参数化模板，处理连接器交错极性扇出（P 走表层、N 下穿 In2 换位）。零 revA 特判，先探针后施工。
### W6-C M-E 重解一次（--all-v4，同输入禁第二次）
验收：16 数据对 SOLVED + P/N 断言 + 等长<0.15 + 单对<5s；INFEASIBLE→证据表停机。
### 后续
Card 4（hs_apply 落板→S2 gate→kicad-cli DRC 零违规）→ Card 5A/5B → 提交归档（待明示）。

## 4. 关键物理事实（实测，勿重新论证）
- U7@(93.825,44.7) rot=0：RX 列 x=88.85 朝 MCIO / TX 列 x=98.85 朝 J2
- U3@(93.825,62.7) rot=180：RX 列 x=98.85 朝 J2 / TX 列 x=88.85 朝 MCIO
- J2@(133.825,53.7)、J3@(59.5,44.5)、J4@(59.5,62.7)；板边 x∈[23,143] y∈[33,71]
- RX pads=[1,2,4,5,7,8,10,11,13,14,16,17,19,20,22,23]、TX pads=[33,34,36,37,...]，channel_count=8
- 连接器 P/N **水平并排同 y**（J2 双列 x=132.65/135.0、J3/J4 x=54.7/55.3 列），轨道 P/N **垂直上下**（track_y±0.19）
- 电容墙复摆后：DN 墙 C17-C32 双行 y=57.8/68.0（x 75.5-84.6）、UP 墙 C49-C64 单行 y=39.4（x 99.5-119.0）

## 5. 工具基线（新路径）
- PM Gate：`cd k2 && sharun python3.11 /home/.../_shared/pm_gate/cli.py --project k2_v4 <sstatus|falsify|risk>`
- 求解（M-E）：`cd k2 && sharun python3.11 -c "import sys;sys.path.insert(0,'/home/.../_shared')" ...` 或沿用 --all-v4（板用 k2 仓库 k2_v4.kicad_pcb 或确认 /tmp 工作板落位）
- verify_cli：PYTHONPATH 注入 _shared（见迁移文档 §2.3）
- 门禁：`_shared/eda_core/routing_topology_gate.py`（已入 dfb1053/ad41353）

## 6. 已落盘证据（k2/pm_gate/artifacts/k2_v4/L3/model_solves/）
- cap_wall_v8/（求解+落板+净空验证）
- capacity_map_v7/（复摆后容量 + disposition + revision_verify）
- hs_rebuild_v8/v9/v10/（M-E 求解三代证据 + classB_analysis.md）
- channel_alloc_v4/（18/18 SOLVED）

## 7. 提交状态（迁移后，均已推送）
- `_shared`(ic_hw_eda) @ ad41353（含 M13 类A修复 8f58466 + 门禁 dfb1053 + 阶段2/4 归位）
- `k2`(ic_hw-k2) @ 42cc7e0（干净工作树，M13 工作含 x_range 修订已迁入）
- S 状态机：S2（226/226 locked）、S3 blocked（无 DRC，待 Card 4）

## 8. 遗留/待办项
- **工作板落位**：电容墙复摆后的 k2_v6 板在 /tmp（易失），须确认是否已落 k2 仓库板或需重生成。
- **Card 5B 指纹重签**：源已定位（电容墙重生成 escape_spec + SPEC x_range 修订），走正规重签，禁手改字段。
- **GARY 补视巡**：Card 1.3 代签后的 PDF 视巡遗留义务。
- **ECO 状态机**：`eco_gate/state_machine.py` 仍引用老目录路径（迁移文档坑⑥，ECO 使用前须修）。
- k1/* 属另一工作流，勿混入 k2 提交。

## 9. 铁律（继承）
七步法 / 先算容量再布线 / 分析走模型 API / DRC 只核对不驱动 / 修订走输入 / 零 revA 特判 /
假成功零容忍 / 反暴力迭代（同输入重跑≥2 即暴力）/ 冲突即停机 / 可行性(定性)与施工(定量)分离 /
未经明确要求不 commit。
