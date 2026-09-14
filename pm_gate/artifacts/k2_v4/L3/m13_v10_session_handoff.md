# M13 v10 续接 — NEW SESSION PROMPT（2026-08-29）

> 权威承接：① `/home/fila/jqdDev_2025/ic_hw/MIGRATION_GUIDE_OLD_SESSIONS.md`
>           ② `k2/pm_gate/artifacts/k2_v4/L3/m13_v9_session_handoff.md`（上一代）
>           ③ 本文档（最新状态）。
> 工作模式：**TASK MGR 拆卡 → 用户转发 WORKER → 我复核 → 整体推进**（不启动后台、不亲自施工）。
> 主线：通过 K2 高速域实施，持续完善 eda_core（可行性门禁 + 施工模型）。

## 0. 开工第一动作
```bash
cd /home/fila/jqdDev_2025/ic_hw/k2 && /home/fila/jqdDev_2025/ic_hw/AppDir/sharun python3.11 \
  /home/fila/jqdDev_2025/ic_hw/_shared/pm_gate/cli.py --project k2_v4 sstatus
# 红队（开工必查）：
#   ... --project k2_v4 falsify list   （open finding 必须逐条驳回）
```

## 1. 迁移要点（继承 m13_v9，勿忘）
- 容器 4 平级子模块：`_shared`(ic_hw_eda) / `key_v2` / `k1` / `k2`(ic_hw-k2) / `pciesw4`(ic_hw-pciesw4，新)。
- 老目录 `strix-halo-ioconvert/` 已归档冻结，禁止提交。
- 命令用**脚本路径**（`_shared/pm_gate/cli.py`），禁 `-m pm_gate.cli`。
- import：`board_model` → `eda_core.board_model`；`board_model.geometry` → `eda_core.geo`。
- 废弃：run_pipeline.py / layout_engine / routing_engine / drc_checker / eda_core/k2_*.py。
- **K2 权威生成器**：`k2/tools/k2_gen_v5.py`（已从老目录迁移，uuid5 确定性化，输入=k2/boards/k2_sch.yaml + SPEC + L2 frozen）。

## 2. 本 session 已完成并 commit/push（勿重做）

**`_shared`（ic_hw_eda）**：
| commit | 内容 |
|---|---|
| `7418f51` | W6-A 门禁三档裁决（③ 极性拆 resource_ok/polarity_ok，verdict 三档） |
| `e4637e0` | W6-B 层换位引线姿势（_escape_pair 增 LSWAP 形态，P F.Cu/N In2 下穿） |
| `5643a21` | 卡0.5b hook 路径修复（_is_spec_change 兼容 artifacts/<proj>/L3/） |

**`k2`（ic_hw-k2）**：
| commit | 内容 |
|---|---|
| `c6d6373` | 卡0.5 生成器迁移 + 复摆落位（k2_v4 87b66fbb→6c387dff，32/32 电容复摆） |
| `2c37248` | m13_v9 session handoff 文档 |

> 另有 `_shared` 上 lceda_import 工作流（`ae52d67` 等）与 `pciesw4` 仓库（LCEDA 迁移）——**另一条工作流，勿混入 K2 主线**。

## 3. W6-C 结果（已跑，停机，未 commit）

**产物落盘**：`k2/pm_gate/artifacts/k2_v4/L3/model_solves/hs_rebuild_v11/`（untracked，未 commit）。

**结论**：停机条件触发 — **17/18 INFEASIBLE**，仅 `PCIE_REFCLK0` SOLVED；16 数据对全 INFEASIBLE。

**通过项**（3/4）：
- 零交叉契约（edge≥0.155）：11 个 SOLVED 段 0 违规 ✅（类A修复真板再确认）
- 单对<5s：max 4.19s（UP6），18/18 ✅，sum==global 单进程证明
- 等长<0.15：不适用（无整链 SOLVED）

**缺口归属**（39 段，全部预存，无 W6-B 回归）：
| 域 | 段 | 类型 |
|---|---|---|
| UP out_J2 左逃逸（cap 墙侧） | 7 | 极性交叉 @ 墙行 y≈39.3-40.2（**W6-B LSWAP 覆盖盲区**：U7 TX 竖排 P/N 对不满足触发条件 \|dx\|≥0.5） |
| UP input（MCIO 侧） | 8 | 极性交叉（预存类A，v10 同构） |
| UP out_U7 | 8 | 净空失败 vs GND/P3V3/VREG（预存） |
| DN out_U3 | 7 | 极性交叉（预存） |
| DN out_MCIO | 8 | 极性交叉（预存） |
| REFCLK1 input | 1 | 极性交叉 vs REFCLK0（预存） |

**W6-B 生效证据**：UP7 out_J2 右（J2 侧）逃逸 = LSWAP SOLVED（edge 0.1732）——v10 时代 UP0-7 out_J2 全 INFEASIBLE，W6-B 为 UP7 解锁 J2 侧。**但整链仍 INFEASIBLE**（input 段预存缺口未解）。

## 4. 待做（按序，主线）

- **W6-C 复核 + 决策**：TASK MGR 复核停机证据表，判定下一步——是开「逃逸形态扩展」卡补齐缺口，还是先归档部分成果。
- **逃逸形态扩展（建议开卡）**：UP out_J2 左逃逸（cap 墙侧，U7 TX 竖排 P/N 对）——LSWAP 触发条件放宽或新增竖排 P/N 换位形态。这是 16 对 SOLVED 的关键瓶颈。
- **Card4**（高速域 SOLVED 后）：hs_apply 落板 → S2 gate → kicad-cli DRC 零违规 → Card5A/5B → 提交归档。**当前被 17/18 INFEASIBLE 阻塞**。

## 5. 关键物理事实（实测，勿重新论证）

- U7@(93.825,44.7) rot0：RX 列 x=88.85 朝 MCIO / TX 列 x=98.85 朝 J2（**TX 列竖排 P/N 对**）
- U3@(93.825,62.7) rot180：RX 列 x=98.85 朝 J2 / TX 列 x=88.85 朝 MCIO
- J2@(133.825,53.7)、J3@(59.5,44.5)、J4@(59.5,62.7)；板边 x∈[23,143] y∈[33,71]
- 连接器 P/N **水平并排同 y**（J2 双列 x=132.65/135.0、J3/J4 x=54.7/55.3），轨道 P/N **垂直上下**（track_y±0.19）
- 电容墙复摆后：DN 墙 C17-C32 双行 y=57.8/68.0（x 75.5-84.6）、UP 墙 C49-C64 单行 y=39.4（x 99.5-119.0）
- **落位板**：k2/k2_v4.kicad_pcb sha=`6c387dff`（k2_gen_v5 权威产物 + 电容墙复摆），是 M13 求解唯一 board 输入。

## 6. 遗留/待办项
- **W6-C 停机证据**：hs_rebuild_v11 目录未 commit，需 TASK MGR 复核后决定归档/继续。
- **UP out_J2 左逃逸（cap 墙侧）缺口**：新识别，建议单独开卡（逃逸形态扩展）。
- **pciesw4 案例借鉴（新讨论，未定案）**：见 §8。
- **ECO 状态机**：`eco_gate/state_machine.py` 仍引用老目录路径（坑⑥，ECO 使用前须修）。
- **GARY 补视巡**：Card 1.3 代签后 PDF 视巡遗留。
- **Card5B 指纹重签**：源已定位（电容墙重生成 escape_spec + SPEC x_range 修订），走正规重签，禁手改字段。
- k1/* 另一工作流勿混入 k2 提交。

## 7. 铁律（继承）
七步法 / 先算容量再布线 / 分析走模型 API / DRC 只核对不驱动 / 修订走输入 / 零 revA 特判 /
假成功零容忍 / 反暴力迭代（同输入重跑≥2 即暴力）/ 冲突即停机 / 可行性(定性)与施工(定量)分离 /
未经明确要求不 commit。

## 8. pciesw4 案例借鉴（新讨论，方向未定案）

- `pciesw4/`（ic_hw-pciesw4 子模块）= 从 JLC 开源库导入的 **PEX88096 PCIe Gen4 交换卡**案例：
  - `aic/`：AIC 卡 10×SlimSAS，898 footprint / 934 net / 703 差分对 / 16.7万走线 / 8层
  - `gpu/`：GPU 扩展卡 5×CEM，1133 footprint / 973 net
- **借鉴价值**：同代 Gen4、同类连接器（SlimSAS=K2 的 J2），成熟差分对扇出/via 换层/AC 耦合/等长姿势可参考。
- **边界（TASK MGR 已定）**：拓扑不同（Switch 星型 vs ReDriver 线性）、层叠不同（8层 vs 小卡）、
  零 revA 特判（坐标不能照搬，须提炼成 eda_core 通用参数化模板）。
- **最直接连接点**：AIC 的 SlimSAS 扇出可作 W6-B LSWAP 的实证对照 + 逃逸形态扩展的参考输入。
- **状态**：待用户定优先级——先对照 SlimSAS 扇出，还是先跑完 W6-C 复核。
