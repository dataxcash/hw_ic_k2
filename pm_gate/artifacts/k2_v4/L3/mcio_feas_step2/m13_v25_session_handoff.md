# M14 v25 — 坐标问题已解决(UltraLibrarian 真实 354 球 x/y mm)+ 决定性逃逸结构证据 + 决定性验证缺口

> 状态：本 session = **破解 4+ 轮阻塞的坐标问题**。经 TI 产品页 → Ultra Librarian TI 内嵌页
> （gpn=DS320PR1601&package=ZDG&pin=354，**免登录**），拿到 **DS320PR1601 nfBGA-354 真实
> 逐球 (x,y) mm 坐标 + 信号名**（vendor-validated，非 raster、非标签网格），已落库
> `ds320pr1601_ballmap.json` + 可复现脚本。**用真实几何复算决定性逃逸结构：新证据显示
> 逃逸密度比 v22 假设（25% 直出/75% via）更紧（88% 需 via / 12% 直出）**。但**决定性逐球
> 逃逸落点求解仍在模型层缺专用工具（G2 缺口）**；**层数（6L vs 8L）仍未定案**——本次是
> "坐标突破 + 证据修正"，不是闭合。

> 承接必读（按序）：① EXECUTION_PROCESS + EXECUTION_GATES ② 本文件 ③ m13_v24_session_handoff.md
> （v25 追加：⑥ 分翼修复）④ `mcio_feas_step2/ds320pr1601_ballmap.json` + `reproduce_ultralibrarian_ballmap.py`
> ＋ `ref/ul_detailed.svg`（原始来源存档）⑤ L1_TOPOLOGY_v2.0 + L2_STRUCTURE_v2.0（层数未定案）
> ⑥ v21_realroute/* + v22_layer_gate/* + v23_layer_gate/*。

## 0. 本 session 关键成果（坐标问题，用户高强度要求"必须解决"）

- ✅ **拿到真实逐球坐标**：UltraLibrarian TI 内嵌页的封装预览为 **SVG 矢量**（`detailed-NFBGA354_ZDG_TEX.svg`），
  354 颗焊盘每颗 = `<rect class="pin">` 带精确 (x,y)（单位 mil，×0.0254→mm）+ 球名（`data-pin_bounding_rect`）
  + 信号名（`data-pin_name`，如 `A_PERP0`/`A_PERN0`/`GND`/`VCC`）。
- ✅ **落库**：`ds320pr1601_ballmap.json`（354 球 `{name,x_mm,y_mm,signal}`，三重验证通过）+ 
  `reproduce_ultralibrarian_ballmap.py`（下载+解析+验证，可复跑）。
- ✅ 源码存档：`ref/ul_detailed.svg`（vendor 原始数据，防上游变更）。

## 1. 交叉验证（三重全过）

| 项 | 结果 |
|---|---|
| ① 354 球 count | 354，unique=354，dup=0 ✓ |
| ② 列带结构 | 4 带沿短轴：A_PER(x=-3.68)→B_PET(-1.78)→A_PET(+1.68)→B_PER(+3.68)，各带 32 球=16 对；带间通道中心距 1.9~3.5mm ✓ |
| ③ 尺寸/间距 | 信号球阵列 x=-3.94..3.94(7.88mm) y=-9.2..9.35(18.55mm) 在 8.9×22.8 体腔内；P/N 对沿短轴 0.52mm 交错；带内 lane 间距 1.2mm=2×0.6 ✓ |

## 2. 决定性逃逸结构证据（真实几何，修正 v22 假设）

用真实坐标复算（full 16-lane 器件，128 信号球）：
- **88% 信号球在内圈（需 via），仅 12%（行1/35=长轴两端）F.Cu 直出**——比 v22 假设的
  "25% 直出 / 75% via" **更紧**（真实封装非均匀逃逸优化阵列，信号球几乎全内圈）。
- 穿越（输入侧 A_PER+B_PER）= 32 对 / 50%，与 v22 一致；K2 取 8-of-16 时 16 对穿越。
- **含义**：F.Cu 直出承担的少，via/In2 承担的多 → **6L 逃逸压力比 v22 预估更大（倾向更紧，非更松）**。

## 3. 决定性验证现状（诚实边界：仍未闭合）

- 坐标已到位 → "逐球逃逸求解"第一次有真实输入。
- **G2 缺口**：`escape_landing.analyze_pad_heap` 是**连接器 pad 堆逃逸到板边**的工具
  （J2 专用语义：单侧→板边，board_edge_x），**不是芯片 BGA 逐球逃逸专用**。芯片 U1 是
  阵列（两侧都要逃逸到走廊），语义不同。**模型层缺"芯片 BGA 逐球逃逸落点"专用工具**——
  禁拿连接器工具硬套假装验证（假成功）。
- ⑥（routing_topology_gate BGA 组带逃逸，v1.2）已交付，但为**拓扑/通道级**，非 per-ball 落点闭合。

## 4. 下一步（两条路径，择一，移交用户/架构裁决）

- **a) 补芯片 BGA 逐球逃逸引擎**（自建，需过 ECN/立法）：以真实球栅为输入，逐信号球判
  F.Cu 直出 vs ball-under-via→In2 + 组带通道/In2 穿越承载判定。产出 = 决定性 FEASIBLE/INFEASIBLE。
- **b) 先用 ⑥ 拓扑级 + 真实 escape_slots 判 6L 倾向性**（快，但只到拓扑/通道级，非 per-ball）。

> 层数定案闸（L2 §）仍适用：6L 逃逸验证 = L3 开工前硬门；在取得真实坐标后的逐球精确求解
> 判定——通过冻 6L / 不闭合回 8L。**未经逐球工具判定不得宣布"6L 闭合"。**

## 5. G5 收尾自检

- **消费资产**：TI 产品页（CAD→UltraLibrarian 链路）、UltraLibrarian TI 内嵌页（SVG 封装预览）、
  `ds320pr1601_ballmap.json`（本 session 落库）、v21/v22 `ds320pr1601_ballmap_signal_balls.json`/`354name.json`
  （对照）、L1/L2 frozen、EXECUTION_PROCESS/GATES。
- **未消费/缺口**：芯片 BGA 逐球逃逸落点**无引擎专用工具**（G2 缺口，见 §3）；
  8-of-16 lane 行位选择（v22 遗留，未做）；去耦对象清单（未做）。
- **停止/熔断**：本轮未触发 G2（已有工具确认：连接器专用 vs 芯片缺口＝覆盖判定）；无暴力迭代。
- **禁违反项**：✅ 零违反（未造坐标、未宣布闭合、未动 L1/L2 frozen 层数行、未改引擎——坐标从
  vendor 来源提取 + 引擎只读）。
- **修正声明**：v22"带结构按行（row1-2 等）"为**错误方向**——真实封装带结构沿**短轴按列**排。

## 6. commit

- `_shared` `805f3cf..79cd37a`（⑥ 分翼 v1.2）；容器 `6c597d8..a082afc`（bump _shared）。
- `k2` `94b1c26..ee39cd6`（坐标资产 + 可复现脚本）；容器 `ce431b3..c5a2583`（bump k2）。
- 本文件 + `ref/ul_detailed.svg` 存档将随下文件一并提交。冻结区复锁 0/0/0。
