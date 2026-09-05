# M13 v22 续接 — 层数定案预备（决定性逃逸项 = 工具级验证仍被模型资产阻塞 → 层数维持 INDETERMINATE）

> 状态：本 session = 层数定案（6L vs 8L）执行轮。**决定性逃逸项（75% via / 50% 穿越密度）未能本轮由
> 引擎工具精确验证**——因模型层缺 DS320PR1601 机器球栅 mm 坐标资产。**层数仍 INDETERMINATE
> （6L 试用 + 8L 兜底，逃逸验证 = L3 开工前硬门），未宣布"6L 闭合"**。
> 但本 session 有**实质突破**：① inter_pair_spacing 已裁（解除 v21 阻塞项之一）；② 走廊闭合
> 引擎工具背书（解除 v21 阻塞项之二）；③ **v21"物理球栅无公开源"被否决**——TI ZDG0354A 官方
> 机械图为公开物理源，缺口收窄为"机器 CAD 精确 mm 坐标"。
> **承接必读（按序）**：① EXECUTION_PROCESS + EXECUTION_GATES ② 本文件 ③ m13_v21_session_handoff.md
> ④ `v22_layer_gate/*`（CORRIDOR_CLOSURE_v22 / ESCAPE_GAP_v22 / capacity_audit 报告 / 354 球名资产）
> ⑤ L1_TOPOLOGY_v2.0 + L2_STRUCTURE_v2.0（已冻结，inter_pair_spacing 已裁）⑥ v21_realroute/*。

## 0. 本 session 产出（commit 见 git log；引擎/宪法/真板零改动）

- `L3/mcio_feas_step2/v22_layer_gate/`：
  - `CORRIDOR_CLOSURE_v22.md`：6L 走廊闭合工具背书（capacity_audit FEASIBLE，压力 0.64）。
  - `ESCAPE_GAP_v22.md`：决定性逃逸项缺口报告（G2 未覆盖 → STOP + 模型层资产需求）。
  - `capacity_audit_6L_corridor_report.json` + `spec_6L_corridor_audit_input.json`（引擎工件）。
  - `ds320pr1601_ballmap_354name.json`：TI ZDG0354A 官方机械图提取的 354 球名集（n=354，行号1-35，
    列字母 129 个，0.6pitch/8.9×22.8/非均匀分组）。
  - `ds320pr1601_datasheet_ZDG0354A_p40-42.pdf`：物理源存档（TI SNLS683 页40-42）。
- **L1/L2 冻结改动（v22 用户裁决 ECN）**：inter_pair_spacing 语义"待裁定" → 已裁（0.875 铜边净空 →
  对中心距 1.46mm；引擎经 route_model_config.json `capacity_audit.inter_pair_spacing=1.46` 注入）。
- L2 项目配置 `route_model_config.json`：新增 `capacity_audit.inter_pair_spacing=1.46`（引擎注入点）。
- kb：`corridor_pair_ds320pr1601_dual_band` 回写（inter_pair_spacing=1.46；known_gap 更新为
  "ZDG0354A 图公开、精确 mm 需机器 CAD"；produced=false 诚实保留）。

## 1. 关键突破与诚实边界

- **v21 结论修正**：v21 断言"DS320PR1601 物理球栅坐标无公开源（librarian won't guess）"——**证据不足**。
  v21 只读 datasheet 逻辑引脚图（Table 5-1 / 图 5-x，拉伸逻辑格），**漏读 datasheet 末尾的
  ZDG0354A 官方机械包图（页40-42）**。本 session 实读：**公开免费，真实物理球栅几何**（354球、
  8.9×22.8、ball 0.6 TYP、(0.3) TYP gaps、非均匀分组逃逸优化）。→ "无公开源"缺口**否决**。
- **剩余缺口（诚实标注）**：ZDG0354A 图内球位**标签为 tabular/可读布局，非物理定位**（实测列字母轴
  scale ≈ 34.8 pts/mm 为行号轴 4.9 pts/mm 的 7 倍，真实图纸不可能；行号轴 pts/row p50≈2.87 与 0.6mm
  名义不符）→ 图中标签坐标**不能**直接校准为物理 mm。**逐类穷举（librarian，2026-09-05）终判：**
  **无任何公开可得的机器可读逐球 X/Y 资产**——KiCad/grep.app/GitHub 0 命中、SnapEDA/UL/SamacSys
  login-gated、Intel spec 纯 raster figure（无矢量/文本坐标表）、唯一机器资产 =
  Astera `PTx16xx_supplemental_info.xlsx`（**FAE-gated**，vendor-declared，同 footprint）。
- **决定性判定**：`escape_landing.analyze_pad_heap(pads)` 需物理 pad X/Y；逻辑球名集（列字母+行号）
  不能喂入 → **决定性逃逸项未能工具级验证 → 层数维持 INDETERMINATE**。**禁宣布"6L 闭合"。**
  **禁动作（宪法 §8.8）**：禁止用 Intel Fig3-5 raster vision 投影造"派生球栅"喂引擎宣称为工具验证
  （= v21 评审"假成功"复刻：置信度提升≠验证能力提升）。

## 2. 已闭合 vs 待闭合（vs v21 评审 §2 阻塞项）

| # | v21 评审阻塞项 | 本 session 状态 |
|---|---|---|
| 1 | 决定性逃逸项须工具级验证 | ❌ **仍未闭合**（机器球栅资产缺；现为封装设计级/结构级） |
| 2 | inter_pair_spacing 语义须先裁定 | ✅ **已裁**（0.875 铜边→1.46 中心；回写 L1/L2 + 引擎注入） |
| 3 | 走廊闭合需工具背书 | ✅ **已背书**（capacity_audit FEASIBLE，压力 0.64，非循环窗容 11/14 对>8） |
| 4 | 撤回"6L 闭合"表述 | ✅ 一直维持 INDETERMINATE（未闭合，与修正一致） |
| 5 | 调和逃逸模型矛盾（均匀网格 vs Intel 非均匀分组） | 🟡 部分：引擎已证非 knife-edge（窗容 11/14>8）；精确逐球仍待机器资产 |
| 6 | 补齐 8-of-16 lane 行位 + 去耦对象清单 | ⏳ 未做（下传 L2/L3 决策行；非本会话层数定案阻塞项） |

## 3. 传导下 session（按序，禁跳过）

1. **取得 DS320PR1601 机器球栅 mm 坐标资产**（最高可信：Astera `PTx16xx_supplemental_info.xlsx`
   (FAE) > EasyEDA/LCSC footprint（对 ZDG0354A 图验真）> Intel spec（registration））。产出
   `ds320pr1601_ballmap` 球栅 JSON（354 球 (x,y)mm；count 对齐 + 列带结构 A_PER@row1-2 等交叉验证 +
   0.6pitch/8.9×22.8 闭合）。这是模型层资产补足。
2. 资产到位后 `escape_landing` 跑一次**精确逃逸求解**（禁暴力迭代）→ **过闸冻 6L / 不过回 8L**
   （两种情况不重跑，走 L1/L2 层数行 unlock→改→lock）。
3. 补决策行：8-of-16 lane 行位选择 + 去耦对象清单（层数定案后 L3 前）。
4. 上述完才能正式冻结层数（L1/L2），再进 L3。

## 4. 学习闭环（kb 已回写）

- `corridor_pair_ds320pr1601_dual_band`：params.inter_pair_spacing_mm=1.46（已裁）；
  known_gap 更新为"ZDG0354A 图公开（354 球名集已提取），精确逐球 mm 需机器 CAD 交叉验证"；
  produced=false（诚实：精确逃逸求解未实证）。
- `cap_wall_ac`：本板关闭（AC 集成芯片，32×0402 墙移除）——随架构转向保留，非本层刷新对象。

## 5. G5 收尾自检

- **消费资产**：kb.sqlite3（模板 8 条，ds320pr1601_dual_band produced=false 实检）、TI ds320pr1601
  datasheet ZDG0354A（逐球名集提取）、edacore capacity_audit（只读调用）、v21_realroute 全部工件、
  L1/L2 v2.0 冻结、route_model_config.json、drc_rules.json、constitution/PCB_DESIGN_RULES。
- **未消费/缺口**：`escape_landing` **未运行**（缺机器球栅 mm 资产 = 决定性缺口，已上报
  ESCAPE_GAP_v22）；8-of-16 lane 行位/去耦对象未做（非本层阻塞）；未走 oracle 二次对抗评审（本轮
  未声明闭合，INDETERMINATE 状态与 v21 修正一致，无新闭合断言需评审）。
- **熔断/停转记录**：G2 触发（决定性逃逸精确逐球形态未覆盖 → 缺口上报）；G4 触发（球栅 mm 提取
  在同一几何卡点连续多轮无新收敛（tabular 布局 scale 矛盾），停写"问题回模型"）；未违反 G0
  （按序读全权威清单）。**无暴力迭代**（引擎工具一次对：capacity_audit 两次运行=非循环口径复核，
  非同参重跑）。

## 6. commit

容器 git log（b8e72c2 之后）。本 session 改动 = k2 v22 工件（v22_layer_gate/* + L1/L2 冻结
inter_pair_spacing 写回 + route_model_config capacity_audit 注入）+ _shared kb 回写 +
容器 submodule 指针。
