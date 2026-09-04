# M13 v20 续接 — 器件选型冻结(DS320PR1601) + 板框/层数 ECO 候选 + 芯片实底

> **状态**：本 session 完成四件里程碑，**布局最终裁决未出（等 ECN 正式化 + 6L 路由实测）**：
> ① 器件选型竞标并**冻结 = TI DS320PR1601**（v19 §6 #1-#5 用户裁决）；
> ② **用户新方向裁决**：板可加高、**单面贴**、层数 6/8 重估（6L 试跑不过回 8L）；
> ③ ECO 变更单候选落盘 `eco_v20_board_geometry.md`（板高 H1=46 / H2=52、层数重开、单面）；
> ④ DS320PR1601 datasheet 实底 + ball map 朝向**已确认**（切换多模态视觉直接读 TI Fig 5-1~5-3）。
> **承接必读（按序）**：① `k2/pm_gate/EXECUTION_PROCESS.md` + `EXECUTION_GATES.md`
> ② 本文件 ③ `m13_v19_session_handoff.md` ④ `L3/mcio_feas_step2/mcio_parts_selection_v19.md`（已冻结）
> ⑤ `L3/mcio_feas_step2/eco_v20_board_geometry.md` ⑥ `_shared/docs/LAYOUT_CONSTITUTION.md` +
> `KNOWLEDGE_REUSE_SDD.md`。

## 0. 本 session 产出（commit 号见 git log；引擎/宪法/真板零改动，冻结区全程锁定）

- `mcio_parts_selection_v19.md`：选型候选 + 竞标打分 + **冻结记录**（DS320PR1601）。
- `eco_v20_board_geometry.md`：板框/叠层/贴面重开 ECO 候选（未正式化，未解锁）。
- 本 handoff。

## 1. 器件选型冻结（v19 §6 #1-#5 全裁，已入工件 §3）

| # | 裁决 | 关键依据 |
|---|---|---|
| 1 | **REDRIVER**（非 retimer） | 板内通道 ~60mm@Gen4 由 L1 candidate_A 预算背书；retimer 需 refclk/配置且 JLC 无现货 |
| 2 | **双向 + 集成 AC** | DS320PR1601 **64 颗 220nF 集成于 TX 脚内**（datasheet Features/§6.6）→ 板上 32×0402 墙拆除 |
| 3 | **DS320PR1601**（Gen1-5 16-lane 双向） | LCSC 现货 94 颗 $44-46；nfBGA-354 **22.9×9.0mm**，0.6 pitch |
| 4 | **真板非单口 16-lane 汇聚** | 网表 = J3/J4 两独立 MCIO x4（DN0-3/DN4-7）；"16-lane"为 16 对差分术语漂移 |
| 5 | **Gen4 16GT/s（文档锁定）** | DS320PR1601 向后兼容 Gen1-4，留 Gen5 头寸 |

淘汰项已记录（2×DS160PR810 现状 / DS160PT801 / PS8926 / M88RT / PT4161L / 89HT0832P）——未来翻案依据在工件 §3。

## 2. 用户新方向裁决（本 session，进 ECO）

1. **板子可以加高**（38 → 测算最小可行值；旧 38mm 是被电容墙方案挤出来的，非机械约束）。
2. **不需要双面贴**（真板 101 件本就在 F.Cu 单面，B.Cu 全空；拆 32 电容 + 两芯片合一后只会更空）。
3. **层数 6/8 重估**：**先试 6 层；路由验证不闭合 → 回 8 层**（旧板 8 层已验证，成本 +50~100% 可接受）。
4. 加高幅度：按 TASK MGR 测算，H1(46mm) 优先，H2(52mm) 备选，路由全通取最小。

## 3. 芯片实底（DS320PR1601，SNLS683/MPBGAV1C 双源核实）

- 封装 nfBGA-354（ZDG0354A）22.9×9.0×1.4mm，pitch 0.6，球 Ø0.37/0.27，NSMD Ø0.3 焊盘（首选）。
- **单 3.3V 供电**（VCC1-4=30 球，GND 152 球）；内部 LDO，无 0.85/1.0V 外轨。
- **线性 redriver：零 REFCLK**（协议透明，CTLE+线性驱动）；I2C/SMBus + 2Kb EEPROM 配置，
  strap = MODE/READ_EN#/PD 组/地址脚（5 电平），EQ 无 strap（走寄存器）。
- 64 TX 球全带集成 AC cap（220nF typ）→ **板上电容墙消除成立**。
- 信号布局（ball map 已确认，2026-09-04 多模态直读 TI Fig 5-1~5-3）：**列号 1..35 沿长轴(22.9mm)**、
  行 A-FJ 沿短轴(8.9mm)。lane n 八球分布（以 lane0 为例）：A_PER(主机收)=col1-2、B_PET(设备发)=col7-10、
  B_PER(设备收)=col34-35、A_PET(主机发)=col26-29。**非"A 侧全左/B 侧全右"**——而是**主机→设备方向
  在 col1-10 半段、设备→主机方向在 col26-35 半段**，lane 球跨全长度 → 内部须 In2 内层逃逸+换层
  汇至两侧短端。
- **朝向结论（已确认，不再残留）**：摆放 0/180（短端分别贴 J2 / J3J4 侧），实际路由验证为准；
  此项不挡板高/层数裁决。

## 4. 真板几何实底（BoardParser census，本 session 产出）

- 板框 x∈[23,143] y∈[33,71]（120×38）；**8 层** F/G/S/G/P/G/S/B 语义；101 件全 F.Cu 单面。
- J2(SlimSAS x8,74p)：x∈[132.65,135] y∈[42.9,64.5]（右缘，高度带 21.6mm）；
  J3/J4(MCIO x4,38p)：x∈[54.1,64.9]，J3 y∈[43.25,45.75]（上）、J4 y∈[61.45,63.95]（下）。
- 高速对：J2 侧 16 对（DN0-7+UP_OUT0-7）+ MCIO 侧 16 对（DN_OUT0-7+UP0-7）+ REFCLK0/1；
  低速/边带 24 网（I2C/UART/PERST#/USB/PWR…）。**共 56 高速信号网 + 24 低速**。
- 墙区（将被释放）：x∈[74.95,85.15] 两行 y=57.8/68.0，32×220nF；旧两芯片区 x∈[88.8,98.8]。

## 5. ECO v20 状态（候选 → 待正式化）

- 板高 H1(46) / H2(52)；层数 6L 先试（判据：新板路由闭合 + via≤2/网 + 0.875 + REFCLK 包地 + GND 伴行）；
  6L 不过 → 回 8L（旧决策文档仍有效兜底）。
- **下 session 第一步 = 用户签 ECN**：`freeze_ctl.sh unlock` → 更新 L1_TOPOLOGY（板框/分区/器件）与
  L2 叠层决策（6/8 定案）→ `lock`。未签前不触碰冻结区。
- 8L 旧决策（stackup_8layer_decision 2026-08-19）负载前提 = 电容墙+两芯片+36 网 J2 侧；新负载下
  **6L 有重开空间**，但 354-BGA 扇出（0.6 pitch，~64 信号球/向）是否逼回 8L = **必须真实路由验证**，
  不拍脑袋。此为该 ECO 的核心待验项。

## 6. 下 session 入口（按序）

1. 等用户对 ECO 正式签核（板高起点 46 / 6L 试跑授权）→ 走 unlock → 改 L1/L2 冻结 → lock。
2. **BoardParser 新拓扑测算**（v19 §7(a) 分支）：摆 DS320PR1601（22.9 长轴沿 x）+ 无电容墙 +
   J2/J3/J4 接口 → 6L 路由一次求解（禁暴力迭代，放不下 = 判定缺口回包络或升 8L）。
3. 6L 若闭合 → 冻结 46mm+6L；若不闭合 → 判定缺口 → 回包络（H2 52mm 或 8L）→ 再解一次。
4. **ball map 朝向已确认**（多模态直读 TI Fig 5-1~5-3）：列沿长轴、方向分两半段 → 摆放 0/180，
   短端分别贴 J2 / J3J4 侧；锁摆放角进入布局测量。
5. kb 回写（cap_wall_ac 本板关闭 / DS320PR1601 选型落库 / known_gap 更新）→ 学习闭环。
6. 结论过对抗评审（完整性/一致性/可验证/物理闭合/裁决性）才算数。

## 7. G5 收尾自检

- 消费资产：kb.sqlite3 模板、SPEC_k2_v4.json、L1/L2 冻结、真板 BoardParser、DS320PR1601 datasheet
  (SNLS683)+MPBGAV1C（librarian 双源核实）、v18/v19 handoff。
- 未消费/缺口：外部线缆段 dB 预算（k2 文档无，若将来引入 retimer 判据需补）；6L 真实路由验证
  （下 session，ECN 后）。
- 熔断/停转记录：朝向项经由多模态切换**已闭环**（无残留）；Q2 求解器 120 布局作废方向未复辟。
