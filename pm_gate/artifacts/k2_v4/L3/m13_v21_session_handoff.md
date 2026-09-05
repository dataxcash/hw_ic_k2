# M13 v21 续接 — 真实 6L 路由验证（INDETERMINATE 结论 + 对抗评审 FAIL → 层数未定案）

> 状态：v20 §6 下 session A 项（真实 6L 路由验证）**已执行但未得出"6L 闭合"**——决定性逃逸项未做
> 工具精确验证，初始"闭合"判定被**非执行者对抗评审 FAIL**。本 session 产出 = 引擎资产覆盖审计 +
> footprint 实破（Intel common）+ 摆放竞标 + 评审记录 + **诚实修正的冻结态（6L 试用/8L 兜底）**。
> **承接必读（按序）**：① EXECUTION_PROCESS + EXECUTION_GATES ② 本文件 ③ m13_v20_session_handoff.md
> ④ `L3/mcio_feas_step2/v21_realroute/*`（AUDIT_G1_G2 / L2_PLACEMENT_BID / ROUTE_6L_VERDICT /
> REVIEW_ADVERSARIAL）⑤ L1_TOPOLOGY_v2.0 + L2_STRUCTURE_v2.0（已冻结，含"层数定案闸"）。

## 0. 本 session 产出（commit 见 git log；引擎/宪法/真板 v1.0 冻结零改动）

- `mcio_feas_step2/v21_realroute/AUDIT_G1_G2_coverage_v21.md`：G1/G2 引擎资产覆盖审计 + 两发现。
- `mcio_feas_step2/v21_realroute/L2_PLACEMENT_BID_v21.md`：摆放候选 ≥2 竞标裁决 = P-A（orient-0 @ 93.8,53.7）。
- `mcio_feas_step2/v21_realroute/ROUTE_6L_VERDICT_v21.md`：原始 6L 判定（已被修正为 INDETERMINATE）。
- `mcio_feas_step2/v21_realroute/REVIEW_ADVERSARIAL_v21.md`：非执行者对抗评审（FAIL + 修正）。
- `L1/frozen/L1_TOPOLOGY_v2.0.md`、`L2/frozen/L2_STRUCTURE_v2.0.md`：**ECN 冻结（新架构）**，
  状态=层数未定案（6L 试用 + 8L 兜底，逃逸验证为 L3 开工前硬门），替代 v1.0。
- kb 回写：模板 `corridor_pair_ds320pr1601_dual_band`（produced=false，含 known_gap）。

## 1. 关键突破（footprint 实破，Step1 球栅问题彻底澄清）

- **DS320PR1601 = Intel PCIe5 retimer common footprint**（354 球 8.9×22.8mm，TI 官方标
  "Intel retimer common footprint compatible"；Broadcom BCM85657 / Astera PT5161L / Microchip 同遵）。
- datasheet 的 A·FJ×1·35（130 行）**是逻辑引脚图，非物理网格**——并非标度/内部不一致，而是 TI 自家
  Fig 5-x / 机械图 / UL footprint 全画在同一张拉伸逻辑格上（130×0.6=78mm 物理不可能）。
- **物理形态 = 非均匀分组/balls-anywhere 逃逸优化阵列**（Intel 专利 US20170351640：lane 分组 +
  组间 0.3/0.4/0.8/1.2mm 布线通道，设计目标=每差分对单层逃逸；短轴球跨 ~7.88mm ≈14–15 名义 0.6 位）。
- **列带结构（确定性，不依赖行距）**：全 16 lane 一致 = A_PER@col1-2 / B_PET@col7-10 / A_PET@col26-29 /
  B_PER@col34-35。25% 外环 F.Cu 直出、75% 需 via、50%（16 对=32 网）穿越——由列位驱动，稳健确认。
- **利好信号**：precheck 的"0.6 均匀网格 knife-edge"是过度保守；真封装每 lane 分组留通道。但——
  **精确逐球 X/Y 无任何公开源**（GitHub/UL/SnapEDA/EasyEDA 全空或同为拉伸逻辑格；真源=Intel spec
  (registration-gated)/TI EVM 受限目录）。**librarian: won't guess**。

## 2. 层数判定（修正后 = 未定案 INDETERMINATE）

| 项 | 状态 |
|---|---|
| 器件 DS320PR1601 nfBGA-354 | **已冻结**（v19 用户裁决；Intel common footprint） |
| 板框 46mm（y33-79）单面贴 | **已冻结**（v20 用户裁决） |
| 结构预检（precheck） | 闭合（结构数学） |
| 走廊横截/x净跨 | 闭合（独立复核通过，宏观算术✓） |
| **决定性逃逸项**（75% via/50% 穿越密度） | **未工具验证** = known_gap（工具缺 Intel footprint 物理坐标资产） |
| **层数 6L vs 8L** | **未定案**：6L 试用 + 8L 兜底；逃逸验证 = **L3 开工前硬门** |

**为什么不是"6L 闭合"**：对抗评审 FAIL——置信度提升≠验证能力提升。装备=Intel 逃逸优化封装（真证据）
但验证能力（精确坐标）未变；结论却从"INDETERMINATE"跳到"CLOSED"。= 项目历史事故认知签名（假成功）。

## 3. 传导下 session（按序）

1. **裁决 inter_pair_spacing 语义**（0.875 中心距 / 0.875 铜边→1.46 / 1.08 轨距）——L3 跑引擎容量类
   工具前必裁；用户/架构裁决并回写冻结文档（禁不确定性下传，禁令7）。
2. **取得 Intel footprint 物理坐标资产**（Intel PCIe5 retimer spec 图 / TI EVM / 竞品 datasheet 共享
   footprint）——决定逃逸验证可行性。若取得 → 引擎 `escape_landing`+`capacity_audit` 跑一次精确求解
   （禁暴力迭代）→ 过闸则 6L 正式冻结、不过则改 8L。
3. **6L corridor SPEC + capacity_audit 运行工件**（替代 precheck 手推 1.46 口径）——走廊闭合须工具背书。
4. **补齐对象**：8-of-16 lane 行位选择 + 去耦对象清单（冻结前给决策行）。
5. 上述完才能正式冻结层数（L1/L2），再进 L3。

## 4. 学习闭环（kb 已回写）

- `cap_wall_ac`：本板关闭（AC 集成芯片，32×0402 墙移除）——已记入新模板 provenance。
- `DS320PR1601` 选型落库：模板 `corridor_pair_ds320pr1601_dual_band`（produced=false，known_gap
  =逃逸精确解待 Intel footprint 资产 + inter_pair_spacing 语义待裁定）。
- known_gap "MCIO 端逃逸区垂直爬升容量未实证" → 更新为 **"DS320PR1601 逃逸精确解未实证（工具缺
  Intel retimer common footprint 物理球栅坐标资产，无公开源）；现=封装设计级（Intel 逃逸优化）"**。

## 5. G5 收尾自检

- 消费资产：kb.sqlite3 模板、datasheet SNLS683（逐球解析）、真板 BoardParser、edacore G1/G2 审计、
  v18/v19/v20 handoff、librarian 外部核实（Intel common footprint）、Oracle 对抗评审。
- 未消费/缺口：**未做工具精确终裁**（决定性逃逸项，资产缺）；inter_pair_spacing 未裁定；
  6L corridor SPEC/容量审计工具运行未产出（评审列为阻塞项）。
- 熔断/停转记录：G1/G2 触发（逃逸形态未覆盖→缺口）；对抗评审 FAIL（已接受并修正冻结）；
  未触发 G4（无暴力迭代）；未违反 G0（按序读全权威清单后才动手）。

## 6. commit

见容器 git log（c33a589 之后）。本 session 改动 = k2 v21 工件 + L1/L2 v2.0 冻结 + _shared kb 回写 +
容器 submodule 指针。
