# cap_wall_v8 — session report（2026-08-27）

## 1. 结论（一句话）

**cap_wall_solver 对 DN/UP 两面墙各一次确定性求解均显式失败（0/16），无布局产出 → 未落板、板未动 → 本卡停机，输出工具证据 + 模型/输入缺口报告（非成功）。**

## 2. 任务与输入核验（step 1）

- 板在盘：`/tmp/opencode/boards/k2_v6.kicad_pcb`（101 器件，32 颗目标电容 C17-C32/C49-C64 全 rot=0，sha256 已记录）。
- 轨道在盘：`channel_alloc_v4/` 18 网全 SOLVED；tracks_y 按 band 分组：
  - U_TO_MCIO lower（DN 墙所属）= 58.7, 59.9, 61.1, 62.3, 63.5, 64.7, 65.9, 67.1
  - J2_TO_U upper（UP 墙所属）= 40.3, 41.5, 42.7, 43.9, 45.1, 46.3, 47.5, 48.7
- 工具链可读：`cap_wall_solver.py`/`cap_wall_apply.py`/`cap_wall_stub_geom.py` 源码与 CLI 头已读（sharun python3.11 + pcbnew 10.0.5 可导入）。

## 3. 求解输入（先画图后算数，全部来自板实测 + SPEC + alloc）

| 输入 | DN 墙 C17-C32 | UP 墙 C49-C64 |
|---|---|---|
| side | down（芯片右/MCIO 左） | up（芯片左 U7/J2 右） |
| net_order | DN_OUT0-7 P/N（MCIO 端网，板 pad 映射权威） | UP_OUT0-7 P/N（J2 端网） |
| rows | [lanes0-3, lanes4-7] | [lanes4-7, lanes0-3]（U7 TX y 随 lane 递减，物理 y 序反转） |
| band_y | (60,66) SPEC lower_band_y | (44,47) SPEC upper_band_y |
| x_corridor | (75,90) SPEC mcio_side_x | (99,128) = SPEC j2_side_x[93,128] ∩ 物理（U7 TX 列 98.825 右侧，v7 session 走廊口径 [99,133]） |
| u3_pad_y | U3 TX 实测（x=88.825, y=58.5..67.3） | U7 TX 实测（x=98.825, y=40.1..48.9） |
| min_pitch / min_row_sep | 1.3 / 2.5（SPEC/裁决，不动） | 同左 |

- 网↔电容映射、芯片 TX pad y 全部从板文件提取（权威），非手工转录。
- 工具缺口声明：`solve_cap_wall` 内部 `place_stubs` 缺省 `cap_nets=CAP_NETS`（硬编码旧 8 颗墙 C25-C32），
  16 颗墙无法正确验桩 → 驱动在运行时注入本墙 cap_nets（`/tmp/opencode/cap_wall_v8_solve.py`），源码零改动。
- **每次求解恰跑 1 次，无改参重跑**（同参重跑 ≥2 = 违规，未发生）。

## 4. 求解结果（step 2，原样证据）

```
[down] solved=0/16   固定障碍 279 个 → 显式失败
[up]   solved=0/16   固定障碍 293 个 → 显式失败
```
原始输出全文在 `solve.json`（含 input 快照 + input_fp + report）。

## 5. 卡死点取证（只读障碍场解剖，非重跑）

### DN 墙：行1 首候选 y=60.5
- PAD-CLEAR 8/8 全过；**STUB 失败**：末槽（x=84.6）MCIO 侧 pad2 @(84.25,60.5) 方向阶梯全碰撞：
  - 竖向 ±0.7 → 撞**固定 U3 芯片侧逃逸桩段 `PCIE_DN_OUT2_N_U3` seg(84.51,59.48)→(84.51,61.08)**，d=0.26 < 0.375（需求）
  - −x 0.7/0.5/0.4 → 撞邻 cap pad；+x 2.5 → 撞 U3 桩扇出
- 根因：SPEC `mcio_side_x[75,90]` 走廊右端槽位 x=84.6 与 **U3 TX 逃逸桩扇出（已达 x=84.51）重叠**；
  求解器 x 网格固定 `x_corridor[0]+0.5+1.3i`，无 x 平移能力，且 8/8 全部落桩才放行 → 显式失败。

### UP 墙：行1 首候选 y=44.2
- **PAD-CLEAR 失败**：C58(UP_OUT4_N) x=99.50 → pad 距**固定 U7 芯片侧逃逸桩段 `PCIE_UP_OUT4_P_U7`** d=0.246（需求 ≥0.5）
- 根因：UP 墙最左列 x=99.5（x_corridor[0]+0.5）**落入 U7 TX 逃逸桩扇出带**；
  另 band[44,47] 内 2 行 ≥2.5 间距的轨带错开窗口（[44.34,44.66]∪[45.54,45.86]∪[46.74,47.06]）
  在 0.3 步进网格上**无两行可行组合**（最大可行跨距 2.72 > 2.5 但网格落点对不上）→ 双死锁。

## 6. 根因归类（模型/输入缺口，非算法可绕）

1. **spec 电容墙走廊与芯片逃逸扇出重叠**：mcio_side_x 右端（84.6+）被 U3 桩带占用、
   j2_side_x 左端（99.5 起）被 U7 桩带占用——SPEC 走廊约束未排除芯片自身逃逸桩扇出区。
2. **求解器缺 x 向自由度**：cap 槽位 x 硬编码 `x_corridor[0]+0.5+i·pitch`，走廊被桩带侵占时无法整行平移/压缩避让。
3. **求解器缺轨道错开约束**：v7 根因①（压轨 -0.075）未编码进模型——即使求解成功，
   行 y 落点也无 track_y±0.19 净空约束（本卡 step 5 校验公式即为该缺口）。
4. **UP 墙 band+行距+轨带三方几何不可行**：band[44,47] 高度 3mm vs 2 行 ≥2.5mm vs 轨带 0.44 净空窗口，
   0.3 网格无两行组合（单行 16 颗 x 跨 19.5mm 可落单行，但求解器 rows 结构/桩阶梯不支持单行 16 颗全桩验证）。

## 7. 落板与校验（step 3/4）——未执行

- 无布局 → `cap_wall_apply` 无可落坐标 → **板保持任务开始前原样**（101 器件/32 颗原位/rot 0，
  sha256 已核对），无备份/无回滚需求（`restore.md` 含一行重建命令）。
- step 4 校验项（32 颗移动/pad 网络一致/旋转零改/器件 101）标记 N/A（见 apply_report.json）。

## 8. 净空校验（step 5）——新布局 N/A；现状板 annex 证实任务必要性

- 新布局：VACUOUS（无坐标可校验）。
- 现状板 32 颗旧位：**DN 墙 16/16 违规（最差 −0.34，C17/C18@y66 vs 轨 65.9）；UP 墙 8/16 违规（最差 −0.24，C55/C56@48.3/48.9 vs 轨 48.7，即 v7 根因①同型）**——逐颗数值在 clearance_verify.json。

## 9. 停机与后续（按铁律：冲突即停机 / INFEASIBLE=输入缺口证明 / 禁暴力迭代）

- 处置建议（方案级，禁自打补丁，待 PM 裁决）：
  A. SPEC 输入修订：capacitor_walls x 走廊排除芯片桩扇出区（DN 右限 <84.5 / UP 左限 >桩带外）+ band 与轨带错开；
  B. 求解器能力升级（通用零特判）：cap 槽位 x 引入平移/压缩自由度；行 y 候选加 track_y±0.19 净空约束；
     行结构与单行大行支持；
  C. 若走廊/band 物理容量不足 → 方案级缺口（电源垫/布局层）报告。
- 本卡未改任何 *.py / SPEC / alloc / yaml；未摸 git；未跑 hs_route_model --all-v4。
- 透明声明：子模块工作树中 `revA/gate_reports/sch_k2.gate.json` / `gate_reports_manifest.yaml` /
  `pm_gate/state_k2_v4.json` 的 M 状态为**并发外部活动**（Card 1.3 PM 重签 07:22:36 +
  RISK-002 记录，见 diff 时间戳），与本 session 无关；本 session 写盘仅
  `/tmp/opencode/*` 与 `cap_wall_v8/` 产物目录。

## 10. 产物清单（cap_wall_v8/）

| 文件 | 内容 |
|---|---|
| solve.json | 双侧求解原始结果 + 输入快照 + input_fp + 取证 annex |
| apply_report.json | NOT_APPLIED（无布局）+ 板 sha + 不变量核对 |
| clearance_verify.json | 新布局 N/A + 现状板逐颗净空 annex（24/32 违规） |
| restore.md | 一行重建命令（板未动，无回滚） |
| session_report.md | 本文件 |
