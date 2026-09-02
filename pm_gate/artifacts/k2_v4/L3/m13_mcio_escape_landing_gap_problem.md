# MCIO 逃逸落点问题定义（可行性研究 v1）

> **状态**：问题定义定稿（2026-09-02），TASK MGR 与用户已确认理解一致。本文件只定义问题，不含施工方案。
> **定位**：这是「知识库/案例检索」的入口问题陈述——先定义清楚问题，才能检索 AIC/PEX88096 等真实案例该学什么。
> **铁律**：预期必须来自独立可行性研究（真板几何 + SPEC 权威定义），禁止拿模型自产坐标当标准答案。

## 1. 场景（K2 数据面卡）

链路：**MCIO 连接器（J3/J4）→ AC 电容墙（C17-C32）→ redriver 芯片（U3/U7）→（SlimSAS J2）**

- DN_OUT0-7 = 8 组差分信号（每组 P/N 两根线），从 MCIO 插座出来经电容墙到 U3
- UP_OUT0-7 = 另 8 组，到 U7

## 2. 板上空间事实（真板几何实测，BoardParser）

| 元件 | 位置 x | 位置 y | 说明 |
|---|---|---|---|
| J3 MCIO 上排 | 54-65 | **45.8** | DN_OUT0-3 的信号 pad 在这行 |
| J4 MCIO 下排 | 54-65 | **61.5** | DN_OUT4-7 的信号 pad 在这行 |
| C17-C24 电容（上链路） | 75-85 | **57.8** | DN_OUT0-3 的串联 AC 电容 |
| C25-C32 电容（下链路） | 75-85 | **68.0** | DN_OUT4-7 的串联 AC 电容 |
| U3 redriver | 88.8 | 58-67 | WQFN-64 |
| x∈[65,75] 空隙 | — | — | 10mm 净空带（无 pad） |

**串联电容证据**：`PCIE_DN_OUT0_P_MCIO` 网同时连 J3 pad (64.3,45.8) 与 C17 一端 (77.1,57.8)；
`PCIE_DN_OUT0_P_U3` 网连 C17 另一端 (76.5,57.8) 与 U3 pad (88.8,58.5)。
→ 电容 C17 是信号链路上的**必经串联元件**，信号必须先过电容才能继续。

## 3. 预期（SPEC 权威定义）

- 每条走廊有固定轨道带：U_TO_MCIO lower band 8 条（y=58.7~67.1，间距 1.2mm），DN0-7 各占一条
- 每个 DN 网有**预定义换层点**（SPEC layer_plan.in2_crossing_nets 冻结坐标）：
  - DN_OUT2_N_U3: via1=(79.38,57.55) via2=(87.45,61.3) —— via1 在 x≈79（**电容后**，电容 C17-C24 在 x 75-85）
  - DN_OUT4_N_U3: via1=(84.45,62.7) via2=(87.16,63.7)
  - 其余 6 网 via1 x≈83-88（均在电容区或其后）
- **换层点必须位于电容之后**（信号先表层走穿电容，再 via 下 In2）——拓扑顺序铁律

## 4. 实际（模型输出，p3_real_board_e2e_report.json）

- landing 阶段 MCIO 区 16/16 ASSIGNED、polarity_consistent 全 true、verdict FEASIBLE
- solve 阶段 8 段 out_MCIO 全 INFEASIBLE，报「落点净空校验失败（P=(69.8,57.8) N=(69.8,64.1)）fail-closed 不改落点」
- **落点 x=69.8 < 电容 x=75** → 落点在电容**左侧空隙**

## 5. GAP 定义（预期 vs 实际）

**GAP 核心：escape_landing 生成的落点（x≈69.8）位于 AC 电容墙（x=75）之前，信号在该处 via 下 In2 时尚未穿过串联电容——拓扑顺序错误。**

- 预期：via 落点在电容**之后**（x≥75，SPEC in2_crossing_nets 冻结坐标 x≈79-87），信号先穿电容再换层
- 实际：escape_landing 把落点放在电容**之前**（x=69.8 空隙），电容被旁路
- 根因假设：escape_landing 的落点候选序（GAP/OUTSIDE 双区锚定）只感知「连接器 pad 堆 + 障碍」，**未把「AC 电容是链路必经串联元件」编进落点约束**——它不知道中间横着一排必须穿过的电容

## 6. 待验证（下 session 第一步）

1. 跑 escape_landing 单区诊断，拿 DN_OUT0-7 实际分配落点明细
2. 逐个对比 SPEC in2_crossing_nets 的 via1 坐标 → 确认是否全部落在电容前
3. 若确认 → 知识库检索入口明确：「连接器与 AC 耦合电容墙之间的逃逸换层点应排在电容下游侧」在人类成功案例（AIC PEX88096 10×SlimSAS / OpenCAPI）中如何实现
4. 案例库已有：learned_aic_pex88096_10slimsas（AIC，dogbone 82% stub 0.84mm）、learned_opencapi_slimsas_x8、conn_escape_mcio、cap_wall_ac

## 7. 铁律提醒

- 预期 = 独立可行性研究结论，禁止拿模型自产坐标当标准答案（SPEC in2_crossing_nets 是层3 冻结输出，作为「设计意图」参考，需真板验证其可达性）
- 问题回模型：层3 landing 对落点物理可行性负责，层4 施工 fail-closed 不越权
- 学成功案例 ≠ 修引擎：Phase D 从零推导修 _escape_pair 已停，转学人类案例形态
