# mcio_feas 器件选型候选与竞标（v19 架构转向，已冻结 = DS320PR1601）

> 状态：**已冻结（2026-09-04 用户裁决）**。本工件 = 生产链 ④候选 + ⑤竞标 输出
> （EXECUTION_PROCESS §2）。v19 §6 #1-#5 用户裁决 = **REDRIVER 族 · DS320PR1601**（见 §3 裁决记录）。
> 数据来源分级标注：L0 真板 netlist/SPEC / L1 冻结 / 外部 datasheet（URL 逐条）。
> 检索执行 2026-09-04（librarian 外部核对 + k2 真板核查）。

## 0. 实底复核结论（本 session 产出，先于选型）

| 项 | 事实 | 来源 |
|---|---|---|
| 链路代次/速率 | **PCIe Gen4 16GT/s**（全库一致，无 Gen5 字样） | L2/constraints.md L14、L2/frozen L2_STRUCTURE v1.2、L2/ruling/assumption_h1_calc L13 |
| 真板拓扑方向（网表级） | DN = J2/TX → U3/RX → U3/TX → **C17-C32** → J3/RX(lane0-3)+J4/RX(lane4-7)；UP = J3/J4/TX → U7/RX → U7/TX → **C49-C64** → J2/RX | k2/boards/k2_nets.yaml；origin K2 checklist A/B |
| 当前器件 | **2× TI DS160PR810**（8ch Gen4 线性 redriver，单向 RX_i→TX_i，WQFN-64 5.5×10）；U3=DN@(93.825,62.7)、U7=UP@(93.825,44.7) | SPEC_k2_v4.json components.redriver；L2_STRUCTURE v1.2 表 |
| 汇聚真相 | **下游 = 2× MCIO x4 独立口（J3/J4，lane0-3/lane4-7），非单口 16-lane**；上游 = 单 SlimSAS x8(J2) → PEX88096 Gen4 交换卡。v19 L42"16-lane"与 SPEC channel_count=8 冲突 = 术语漂移（16 = 两 MCIO 合计 16 对差分） | k2_nets.yaml；L1_TOPOLOGY；origin 03-arch-review-v2 |
| 板上通道预算 | J2↔U ~34mm、U↔MCIO ~24mm、含蛇形各 ~60mm，"满足 PCIe Gen4 通道总长预算"；**不含外部线缆段**（SlimSAS 线/FPC 不在 k2 文档预算内） | L1 candidate_A.md L45；SPEC |
| REFCLK | REFCLK0/1 直通共网，common-clock，由 M.2 侧上行 | k2_nets.yaml L290-301；origin checklist C |

**对选型的三个硬含义**：
1. 板上通道 ~60mm @Gen4 → **redriver 可闭合板内通道**；retimer 仅当外部线缆段（SlimSAS 线/FPC）长度把总预算推出 redriver 能力时才必要 —— 该线缆长度数据 **k2 文档无**，属系统级输入，留用户裁。
2. "单点 16-lane 汇聚"非真板需求 → 单芯片能力按 **8-lane 双向（16ch）** 即可满足当下；选 16-lane 器件 = 为架构/未来冗余，非现网表刚需。
3. v19 L53「DN=MCIO→redriver→下游」与网表相反 → 本工件按**网表/L1/L2/origin 四方一致的方向**（DN=J2→U3→MCIO）为基线；若用户另有新架构意图需显式推翻并出 ECO。

## 1. 候选集（≥2，含淘汰项）

### A 候选 — 维持 redriver 族（线性，无 refclk/无协议参与，板内 ~60mm 通道闭合）

| ID | 器件 | 双向? | 集成 AC? | 封装 | JLC/LCSC | 价档 | 关键点 |
|---|---|---|---|---|---|---|---|
| **A1** | TI **DS160PR1601**（Gen4 16-lane 双向） | ✅ 16-lane 每向 | ✅ **64 颗集成 AC** | nfBGA-354 **8.9×22.8** | LCSC C20345379(JLC C20345378) | $47~118 | 电容墙可消除；**单颗替代 U3+U7 双侧**；16-lane 超配现 x8 但吃"单点汇聚"语义；bidirectional 满足"双向" |
| A2 | TI DS320PR1601（Gen5 16-lane 双向） | ✅ | ✅ 64 颗集成 AC | nfBGA-354 同 A1 | LCSC C22374162 **stock 94** | $44~46 | Gen1-5/CXL 向后兼容；**现货最好**；价格最低 |
| A3 | 2× DS160PR810（现状） | 需成对 | ❌ 需外置 | WQFN-64 | 现货 | $13~17/颗 | 维持 32×0402 电容墙 = 死结源头；仅成本兜底 |
| A4 | 2× DS160PR822（8ch+crosspoint） | 需成对 | ❌ | WQFN-64 | 无 | — | 无 JLC 现货；不解决电容墙 |
| A5 | Parade PS8570 / Diodes PI3EQX16904 | ❌ 单向 4ch | ❌ | 小封装 | — | 低 | 通道数不足，淘汰 |

### B 候选 — retimer 族（重新定时，需 100MHz refclk + 配置/EEPROM，通道预算外延至 ~56dB）

| ID | 器件 | 双向? | 集成 AC? | 封装 | JLC/LCSC | 价档 | 关键点 |
|---|---|---|---|---|---|---|---|
| **B1** | TI **DS160PT801**（8-lane=16ch retimer） | ✅ 8-lane | ❌ 未集成 | FCCSP-332 **8.5×13.4** flow-through | 无现货 | 中 | 与现 x8 匹配；ICC 可 2 片扩 x16；但板上仍需 AC 电容 |
| B2 | Parade **PS8926/PS8926A**（16-lane retimer） | ✅ | ❌（Gen4 无集成 AC 宣传；仅 Gen5 PS8936 宣传） | 354-BGA 8.9×22.8 | 无 | 企业级（整卡 ~$258 参考） | 能力全；**价格/现货双杀**；AC 电容未消 |
| B3 | Montage M88RT41632 / M88RT40816 | ✅ | ❌（TR 集成版仅 Gen5） | 8.9×22.8 / 13.4×8.5 | 无 | 渠道价 | 国内企业级；JLC 不可达 |
| B4 | Astera **PT4161L**（16-lane retimer） | ✅ | ✅ 集成 AC | FC-CSP 354 8.9×22.8 | LCSC C5848559 列示 | $80~150+ | 唯一"retimer+集成AC"可购项；企业价；x16 超配现 x8 |
| B5 | Renesas 89HT0832P | ✅ 16-lane | ❌ | — | LCSC C20350512 | 低 | **Gen3 8GT/s only** —— 不满足 Gen4，淘汰 |

## 2. 竞标打分（裁判工具：同一套，权重 = 用户 v19 §6 准则）

准则（来自用户）：① retimer vs redriver 矛盾化解  ② 双向 + 板上 AC 电容需求极少（电容墙死结消除）
③ 性价比  ④ 是否必须单口汇聚 16 lane（单芯片能力 vs 分口）  ⑤ Gen4 速率满足  ⑥ JLC 可得性（含现货）。
权重：②=25 ③=20 ①=15 ⑥=15 ④=10 ⑤=15（⑤全满足，等分）。

| 候选 | ②电容墙消除 | ③性价比 | ①双向/拓扑 | ⑥JLC可得 | ④能力匹配 | ⑤Gen4 | 总分(100) | 裁决 |
|---|---|---|---|---|---|---|---|---|
| **A1 DS160PR1601** | 25（集成AC，墙消） | 12（$47-118 vs retimer 低，但 >2×810） | 15（单颗双向16-lane=现 U3+U7 合一） | 10（LCSC 有列/JLC 0 现货） | 10（16-lane 覆盖现 x8+单点语义） | 15 | **87** | 🏆 主推 |
| **A2 DS320PR1601** | 25 | 17（$44-46 最低 + 现货 94） | 15 | 15（**LCSC stock 94**） | 10 | 15 | **97** | 🏆 主推（Gen5 向后兼容，性价比+现货最优） |
| A3 2×DS160PR810 现状 | 2（32 墙保留） | 18（$13-17/颗×2） | 5（成对单向，汇聚交叉依旧） | 15（现货） | 5（8ch×2=16ch 够现网表） | 15 | 60 | 淘汰（死结源头；仅成本兜底） |
| A5 小 redriver | 2 | 10 | 3 | 8 | 0（4ch 不足） | 10 | 33 | 淘汰 |
| B1 DS160PT801 retimer | 8（refclk+配置+外AC） | 8 | 12（8-lane 恰配现 x8） | 2（无现货） | 8 | 15 | 53 | 淘汰（板内 60mm 无需 retimer；无现货） |
| B2/B3 retimer | 2-8 | 0-3 | 12 | 0 | 8-10 | 15 | ~35-45 | 淘汰（价格/现货双杀） |
| B4 Astera PT4161L | 25 | 0（企业价） | 15 | 2（列示无现货） | 10 | 15 | 67 | 备选（仅当系统线缆强制 retimer 且预算充足） |
| B5 Gen3 retimer | 2 | 10 | 12 | 10 | 8 | **0**（Gen3） | 42 | 淘汰（不满足 Gen5 判据） |

## 3. 裁决记录（2026-09-04 用户拍板，已冻结）

| # | 待裁 | 裁决 | 备注 |
|---|---|---|---|
| 1 | RETIMER vs REDRIVER | **REDRIVER（DS160PR1601 族）** | 板内 60mm@Gen4 redriver 闭合；retimer 无必要且 JLC 不可达 |
| 2 | 器件须双向 + 板上 AC 极少 | **DS160PR1601 族：双向 16-lane + 64 集成 AC** | 电容墙死结消除，32 墙消失 |
| 3 | 性价比/候选型号 | **DS320PR1601（$44-46, LCSC stock 94）** | Gen5 向后兼容；现货最优 |
| 4 | 下游是否必须单口汇聚 16 lane | **真板非必须**（2× MCIO x4 分口）；16-lane 单芯片作架构冗余采纳 | 网表/L1/L2/origin 四方一致 |
| 5 | PCIe 代次/速率 | **Gen4 16GT/s（文档锁定）**；A2 同时留 Gen5 头寸 | DS320PR1601 满足 |
| 6 | 两面分置坐标 | 器件定后另 session BoardParser 真板测算 | 见本工件 §6 下 session 入口 |

**冻结含义（约束包络，供下 session 消费）**：
1. 目标器件 = **TI DS320PR1601**（nfBGA-354，8.9×22.8mm，16-lane 双向，64 集成 AC，Gen1-5）。
2. 板上 AC 电容墙（32×220nF 0402）= **从新拓扑中移除** → `cap_wall_ac` 形态本板不再产生摆位对
   alloc 压轨问题（前置缺口对**本板**关闭；模板本身保留供其他板复用）。
3. 现行 U3(DN)+U7(UP) 双单向 8ch 架构 → **单颗双向器件替代**（lane 通道按 J2 x8 + J3/J4 x4+x4 分配）。
4. 布局可行性 = v19 §7(a) 分支："连接器(J2/J3/J4)↔DS320PR1601↔下游" 新拓扑测算，**无电容墙走廊死结**。

## 4. TASK MGR 建议（已被用户采纳，留档备查）

**主推 A2 → A1 同族（TI DS160PR1601 / DS320PR1601，16-lane 双向线性 redriver，64 集成 AC）**：

1. **电容墙死结直接消除**（准则②满分）：64 颗 AC 集成于封装内 → 板上 32×220nF 0402 墙消失，
   几何死结源头移除 → 走 v19 §7(a) 分支："连接器↔retimer/redriver↔下游"新拓扑测算，无电容墙走廊。
2. **双向 + 单颗替代 U3/U7**（准则①）：现行 U3(DN)+U7(UP) 单向成对 + 汇聚交叉 的摆位无解
   根源（redriver 单向 = DS160PR810 datasheet "all eight channels flow in same direction"）被单颗
   双向 16-lane 器件解除；每向 lane 独立配置。
3. **不引入 retimer 复杂度**：板上通道 ~60mm @Gen4 由 L1 candidate_A 预算背书，线性 redriver 即可
   闭合 —— 无需 refclk/EEPROM/LTSSM 参与，实现面窄、风险低。
4. **性价比/可得性**：A2 现货（LCSC 94）且 $44-46 < 2×810+电容 综合成本量级相当，但省布局死结；
   若需严格 Gen4-only 或更小通道，A1 同族同封装。
5. **Gen5 头寸**（A2）：若 v19 #5 存在 Gen5 升代意图（现文档无），DS320PR1601 向后兼容 Gen1-4，
   一次选型不锁死代次。

**淘汰项记录（未来决策依据）**：
- A3（现状 2×810 + 32 墙）：唯一优点是单价低；保留 32 墙 = 保留死结，作成本兜底候选。
- B1-B3（Gen4 retimer 无集成 AC + JLC 无现货 + 需 refclk/配置）：仅当外部线缆段（SlimSAS 线/FPC）
  长度被证明 >redriver 闭合能力时才复活；该输入目前**文档缺失**。
- B4（Astera PT4161L）：唯一"retimer+集成AC"可购项，但企业价 + x16 超配 + 无现货 → 备选不主推。
- B5（Gen3 retimer）：Gen4 判据直接淘汰。

## 5. 关联

- 学习闸：cap_wall_ac(produced=false) 前置缺口 —— DS320PR1601 冻结后，该形态**本板不再产生**
  复摆位对 alloc 压轨验证需求（墙消）；kb 回写时更新（unlock → 记 known_gap 关闭/本板不适用 → lock）。
- 下 session（本工件冻结后）：BoardParser 真板解析新拓扑（J2↔器件 8lane + 器件↔J3/J4），
  零硬编码；候选≥2 布局方案 → 竞标 → 冻结。
- 冻结纪律：本文件在任务资产区（可写），未触冻结区；kb 回写须 `freeze_ctl.sh unlock` → lock。
