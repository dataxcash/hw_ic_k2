# M13 v22 — 决定性逃逸项缺口报告（G2 未覆盖 → STOP + 模型层资产需求）

> 状态：**模型缺口报告（EXECUTION_GATES G2 未覆盖 → STOP）**。本工件 = 层数定案（6L vs 8L）的
> **决定性逃逸项**（75% via / 50% 穿越密度）为何未能在本 session 由引擎工具精确验证，
> 以及模型层需要补什么。**不宣布"6L 闭合"，层数维持 INDETERMINATE（6L 试用 / 8L 兜底）。**

## 1. 本次资产推进（相较 v21 的关键进展）

- **v21 结论"DS320PR1601 物理球栅坐标无公开源"被否决**：TI DS320PR1601 datasheet SNLS683
  **PDF 页 40-42 = TI 官方封装机械图 ZDG0354A**（Package Outline / Example Board Layout /
  Example Stencil Design），**公开免费**，含真实物理球栅几何：
  - 354 球、8.9×22.8mm、**ball 0.6 TYP pitch、(0.3) TYP gaps**、非均匀分组/balls-anywhere
    逃逸优化阵列（Intel PCIe5 retimer common footprint 判定一致）。
  - **完整 354 球名集已提取**（`ds320pr1601_ballmap_354name.json`，n=354，行号 1-35，列字母 A-FJ 129 个）。
    命名 [列字母][行号]，行号 1-35 = 长轴(22.8mm)，列字母 = 短轴(8.9mm)分组列。
- v21 只读 datasheet **逻辑引脚表 Table 5-1 / 图 5-x**（拉伸逻辑格），**漏了末尾的 ZDG0354A
  机械包图** → 得出过早的"无公开源"。本 session 修正。

## 2. 剩余缺口（为何仍不能工具精确求解）

| 缺口 | 描述 | 处置 |
|---|---|---|
| **精确逐球 mm X/Y** | ZDG0354A 图中球位**标签为可读性/tabular 布局，非物理定位**——实测：列字母轴 scale ~34.8 pts/mm 是行号轴 ~4.9 pts/mm 的 7 倍（真实图纸不可能）；行号轴 pts/row p50≈2.87 与 0.6mm 名义 pitch 不符 → 标签坐标不能直接校准为物理 mm。**精确 X/Y 需解析非均匀分组通道（0.3/0.4/0.8/1.2mm per Intel 专利）+ 机器 CAD footprint** | **模型层资产需求**：需补 DS320PR1601 机器球栅 CAD（EasyEDA/Ultra Librarian/Intel retimer footprint）或 Astera `PTx16xx_supplemental_info.xlsx`（唯一已知电子表格形态，最高可信，但 gated），经 TI 官方 ZDG0354A 图交叉验证 |
| **引擎 escape_landing 输入** | `analyze_pad_heap(pads)` 需要物理 pad X/Y 列表（聚类成 cols/rows/row_pitch）；逻辑球名集（列字母+行号）**不能**喂入（无物理坐标） | 机器球栅 JSON 到位后，`escape_landing` 才能跑决定性逃逸求解 |

## 3. 决定性逃逸项现状（诚实定位）

- **封装设计级 ✓**（Intel 专利 US20170351640 设计目标 = 每差分对单层逃逸；lane 分组 + 组间通道）
  与 **结构级 ✓**（25% 外环 F.Cu 直出 / 75% 需 via / 50% 穿越 = 列位驱动，确定性确认）。
- **工具精确解 ✗**（决定性项）：缺物理逐球 X/Y → `escape_landing` 无法运行。
- **层数（6L vs 8L）**：**维持 INDETERMINATE**。6L 试用 + 8L 兜底；逃逸验证 = **L3 开工前硬门**。

## 4. 模型层/工具待补（"问题回模型"——下一步动作）

1. **取得机器球栅资产**（按可信度）：Astera `PTx16xx_supplemental_info.xlsx`（FAE 分享，最高）>
   EasyEDA/LCSC 的 DS320PR1601 footprint（坐标现成，须对 TI ZDG0354A 图验真）> Intel PCIe5
   retimer spec（registration-gated）。目标是 354 球 (x,y)mm。
2. **球栅 JSON 落为模型层资产**（`ds320pr1601_ballmap` → produced 可转 true），供
   `escape_landing` 消费。验证必须含：354 球 count 对齐 + 列带结构（A_PER@row1-2 等）交叉确认 +
   0.6 pitch/8.9×22.8 尺寸闭合。
3. 资产到位后，用 `escape_landing` 跑一次精确逃逸求解（禁暴力迭代）→ 过闸冻 6L / 不过回 8L。

## 5. 本轮已闭合的阻塞项（vs v21 评审 §2）

- ✅ inter_pair_spacing 语义已裁（见 CORRIDOR_CLOSURE_v22 §0 / L1-L2 frozen 写回）。
- ✅ 走廊闭合工具背书（capacity_audit FEASIBLE，见 CORRIDOR_CLOSURE_v22）。
- ✅ "物理球栅无公开源"被否决 → 缺口收窄为"机器 CAD 精确 mm 坐标"（模型层资产）。
- ❌ 决定性逃逸逐球求解：仍阻塞（机器球栅资产缺）→ 层数未定案。
