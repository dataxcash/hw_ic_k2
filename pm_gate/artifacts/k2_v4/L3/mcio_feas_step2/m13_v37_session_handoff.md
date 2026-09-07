# M14 v37 NEW SESSION 承接 — 确定性可行性命门 Step1（容量模型）

> 承接文件（唯一必读）。上接 `m13_v36_orient_rootcause_fix.md`（本案记录，**§9 为最终结论**）。
> 本文件 = 状态总结 + 确定性命门计划 + 勿加载清单 + NEW SESSION PROMPT。
> 执行纪律：**全前台自跑，禁 task() 委派，禁后台长跑，禁暴力迭代（同参≤2 带依据），禁 chmod 自解**。

---

## 0. 一句话状态

问题已**确定性归约为纯容量/调度**：v34 已证「每段孤立单跑全 SOLVED」= 画法够；18 对差 =
① **16 对**共享 In1/In2 gutter 的**分配顺序冲突**（非布线能力）；
② **REFCLK0/1** = MCIO 连接器区**独立缺口**。
DS320 逃逸密度已**确定**（0.100<0.450 → 必走内层）。**芯片摆向 rot90→rot180 已两次全量证伪（非解，勿再考虑）**。
→ 唯一解 = **确定性可行性命门（容量模型）** 定「可解/不可解」+ 全局 gutter 分配器。

## 1. 已钉死的确定事实（勿重推，违反即浪费 CONTEXT）

| # | 事实 | 依据 |
|---|---|---|
| F1 | 逃逸密度：球距0.4−球径0.3=**0.100mm** < 2×0.175+0.10=**0.450mm** → 单层直穿不可行，逃逸**必走 In 层 gutter**（定形态） | datasheet 球图 × drc_rules 确定性乘法 |
| F2 | 球列带：host=列1-10(A_PER+B_PET)、device=列26-35(A_PET+B_PER)；本板 U6 rot90 两族**同列仅沿 Y 分带** | Table 5-1 + 本板 pad 解析 |
| F3 | **rot180 证伪**：run#1(0解18IFF) run#2(仅DN6,17IFF) → 旋转不解决且打破走廊对齐 → **勿再考虑摆向** | /tmp/solve_v35_rot180、solve_v36_rot180_landing |
| F4 | 每段孤立单跑**全 SOLVED** → 画法够，残留=共享调度 + REFCLK | v34 §3 |
| F5 | col_stack（方向分层 In1西/In2东）已接入 ECN-008，**未铺满全 lane + gutter 分配未分净** | ECN-008 |
| F6 | 权威板 sha `f6273de6`（rot90）；冻结 0/0/0；ECN-009 open | 本 session 实测 |

## 2. 本 session 主任务 = 建确定性可行性命门（容量模型）

> **原则：一切「可解/不可解」由容量模型给出，禁用「跑一遍求解器试试」。**

- **输入**（确定性）：datasheet 球图（球距/球径/GND分布/列带）、`drc_rules.json`（0.175 净空/线宽）、
  `route_model_config.json`（In1/In2 分层）、层叠（6L 信号层）、`channel_alloc`（网络表）、SPEC（tracks_y/band）。
- **计算**：
  - **G1 逃逸密度**：已证（F1）→ 逃逸必走内层。
  - **G2 逃逸需求 D**：18 base × 每 base 差分对 × P/N → 芯片侧须穿内层 gutter 的单端根数 + 每 base 走廊段数。
  - **G3 逃逸容量 C**：In1/In2 可用 gutter 列数 × 每列通道（净空/线宽/间距）× 信号层数。
  - **G4 判定**：每 base D≤C 且全局 ΣD ≤ 全局 gutter 用量上界 → **可解（余量 C−D）/ 不可解（缺口 D−C）**。
- **前置**：先查现有 `model_solves/capacity_map_v*` / `cap_wall_v*` 是否可复用（避免重造）。

## 3. 求解方案（仅 G4/G5 判「可解」才启用）

1. **深 escape 形态**：col_stack + 方向分层（In1西/In2东）铺满**全 lane**（ECN-008 已起，需深化）。
2. **全局 gutter 分配器**：用容量模型输出做**确定性互斥分配**（按方向分 In1/In2 + 按 lane 序在 gutter 列错开），
   取代固定 UP0→DN0→DN7 顺序 → 解 16 对共享冲突。
3. **走廊串联**：复用 SPEC 现有 tracks_y/band（rot90 布局）串通芯片侧↔连接器侧段。
4. **REFCLK0/1**：MCIO 连接器区走廊腾挪/微调，独立处理（G5 独立门）。
5. **全量验证 ≤2 次** → 18 对 SOLVED + skew<0.15 + P/N 净空≥0.175 + 坐标 JSON 落盘。
6. **合规**：ECN-009 裁决/归档；unlock→备份→引擎改→单测 43 passed 零回归(7 failed 既有)→lock→status 0/0/0。

## 4. 勿加载清单（省 CONTEXT，违规即浪费）

- **勿读**：`m13_v10`~`m13_v35` 任一 handoff/报告全文——只读**本文件 + `m13_v36_orient_rootcause_fix.md` §9**；
  （如需 run#1/run#2 细节，grep 该文件 §5-§6）。
- **勿重读原始扫描产物**：SNLU300.pdf/.txt、ds320_ds.pdf/.txt、page-*.png、ds_ball*/ds_lay*、u6_pads_*.json——
  **只需已提取事实（F1-F6）**，不重读文件。
- **勿整读 hs_route_model.py**——只 grep 定位 `_col_stack_escape` / `_escape_pair` / `_landing_escape` / `_layer_swap_escape` 段落。
- **勿整读 SPEC_k2_v4.json**——只 grep `tracks_y`/`band`/`components.redriver`/`bga_escape`。
- **勿重推**：F1-F6（已钉死）。
- **勿重跑**：无依据 `--all-v4`（上次已满 2 次；只在容量模型/分配器改动、且 G4 判可解后才跑）。

## 5. 运行与合规形态（必用）

- 环境：`AppDir/sharun python3.11`，`sys.path` 加 `_shared`（或 `PYTHONPATH=_shared`）。
- 引擎改动合规：ECN-009 挂 → `bash k2/pm_gate/freeze_ctl.sh unlock` → 备份 → 改 → 单测无新增回归 → lock → status 0/0/0。
- 输入：alloc=`/tmp/alloc_v33e/channel_alloc.json`；chip-landing=`chip_landing_v33.json`（勿随意重生成，除非摆向改）。

## 6. 完成/停止判据

- **完成（Go）**：容量模型给出确定性「可解(余量)/不可解(缺口)」数字；若可解 → 分配器 + 全量 18 对 SOLVED + 三项指标 + JSON 落盘。
- **停止（No-Go）**：G4 判**不可解（缺口明确）** → **立即停**，带缺口数字 + 证据回设计层
  （加层/放宽净空/减 lane/换器件），**不再「跑试试」续命**。

## 7. NEW SESSION 启动 PROMPT（可直接粘贴）

---
承接 M14 v37。只读 `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v37_session_handoff.md`（唯一必读），
勿读 m13_v10~v35 全文（其 §1 已钉死 F1-F6）。纪律：**全前台自跑，禁 task() 委派，禁后台长跑，
禁暴力迭代（同参≤2 带依据），禁 chmod 自解，禁无依据 --all-v4**。

主任务：建「确定性可行性命门」容量模型。先查 `model_solves/capacity_map_v*`/`cap_wall_v*` 是否可复用；
再计算 G2 逃逸需求 D / G3 逃逸容量 C / G4 判定（可解余量 or 不可解缺口）。输入=datasheet 球图(球距0.4/球径0.3/GND/列带)
+ drc_rules.json(0.175/线宽) + route_model_config.json(In1/In2分层) + channel_alloc_v33e + SPEC tracks_y/band。
输出=每 base 的 D/C + 全局判定数字。

判定分流：
- G4 判可解 → 再实现全局 gutter 分配器（确定性互斥分配，替代固定 UP0→DN0→DN7 序）+ col_stack 全 lane 深化；
  接引擎 → 全量验证 ≤2 次 → 18 对 SOLVED + skew<0.15 + P/N 净空≥0.175 + 坐标 JSON 落盘 → 合规(ECN-009 裁决/归档)。
- G4 判不可解（缺口明确）→ **立即停**，带缺口+证据回设计层（加层/放宽净空/减 lane/换器件），不续命。

合规：引擎改动走 ECN-009 → unlock(`bash k2/pm_gate/freeze_ctl.sh unlock`)→备份→改→单测 43 passed 零回归(7 failed 既有同集)→lock→status 0/0/0。
完成判据见 handoff §6。全程禁止暴力迭代；每步原始输出贴出不加工。
---
