# M13 v52 承接 — DN0/1/3 out_MCIO chip 侧：取证停机 → 架构审计 → 目标架构 + CCF + IRG(READY_WITH_CHANGES)，v53 从 Phase 0/1 开工

> 承接 v51（F8-F12）。任务（NEW_SESSION_PROMPT_v52.md）：DN0/1/3 out_MCIO chip 侧差分取证 →
> R1/R2 最小修复。
> **v52 演进结论**：
> (1) 取证**推翻 v52 卡片前提**（R1 dip 扩展 / R2 段族清网均被实测否决——R2 清网解与
> 同 base input 段互距 **-0.055mm 真撞=假解**；R1 不解决 P/N 错列结构性死因）→ G4 停机；
> (2) 架构审计（外部 AI 主导）定位**真因 = 方案层"半事实"**：Alloc/Landing 无 chip-side 字段，
> 施工被迫自搜芯片侧逃逸列 → 职责越界；
> (3) 目标架构 + CCF schema + out_MCIO 局部列分配 + migration + invariants 已成文；
> (4) **Implementation Readiness Gate = READY_WITH_CHANGES**（3 项修订 R1/R2/R3），
> **v53 Phase 0/1 可安全开工**。本卡零生产代码（全部为设计/审计产物）。

---

## 1. 钉死事实（v52 增量；勿重推勿重探）

| # | 事实 | 依据 |
|---|---|---|
| F13 | DN0 out_MCIO chip 侧被**同 base 自身 input 段**（PCIE_DN0_P/N 真物理网，先解保锚）挡：col_stack 竖腿 In1 seg (84.6,52.82)→(84.6,58.89) 拒 dist 0.0/0.05 n=36480；via 点 (85.0,58.51) 拒 dist -0.1 | 探针 A（场 API 包装，58.5k 拒中 >50k obs=自身 input 网） |
| F14 | dip 同构死：DN0 dip 9361 pn_ok 9360 拒 @(82.35,52.366) min_edge -0.205；场级障碍仅 2 次 → 不是缺候选档位，是 drop 区间 ~2mm 内 P/N 错列结构性无解 | 探针 A pn_ok 包装 |
| F15 | **(b) 隔离决定性**：剥离同 base input 段共享（shared=[]）→ DN0/1/3/6 out_MCIO **全 COL_STACK SOLVED**（DN0 via 84.6/85.0 竖腿 52.8→58.5/58.9）→ 形态存在、物理可行 | 探针 B |
| F16 | **R2=假解**：隔离解与 input 段已解路径互距 min **-0.055** @(84.925,58.5) → input 段不可清（真网），清网=真板重叠 | 探针 B 互测 |
| F17 | R1 否决：dip 死因=drop 列区间 < P/N 错列+input 段占位最小需求，加档不改变"无净空错列" | F13+F14 |
| F18 | 归因（架构审计定案）：**方案层输出"半事实"**——Schema 无 chip_side_landing/escape_column；MCIO landing 16 条全为连接器侧表达且 DN0-4 十条 pad 锚错（pad=chip pad 84.6/85.0、via=连接器隙列 66.555，stub 18-23mm）→ 归属门正确拒绝 → 施工自搜芯片列 → 撞 input 段 | audit_mcio_landing_all |
| F19 | 施工职责越界=症状非病因：DN5/6 恰好"撞运气"自搜成功（chip 列 x≥90.6 域宽）；DN0-4 芯片列 84.6-89.8 被 input 段竖腿（84.85/85.15…）+ GND 球阵挤压 | audit_coverage_matrix |

## 2. 审计与架构产物（本卡交付物，全落 k2 artifacts）

| 文件 | 内容 |
|---|---|
| m13_v52_audit_schema_dataflow.json | Q1 Schema 字段归属 + Q2 ENG 输入 + Q3 数据流（feasibility 7 约束、DN0 调用链） |
| m13_v52_audit_coverage_matrix.json | Q4 13 关键段 solve/alloc/landing 对照 |
| m13_v52_audit_geometry_anchors.json | Q5 27 段保锚列掩码 + DN7 133.825 堆叠 + clearance |
| m13_v52_audit_alloc_landing.json | Q6 DN0-7 alloc+landing raw（逐字段） |
| m13_v52_audit_mcio_landing_all.json | 16 条 MCIO landing pad 锚审计（10 CHIP 错锚 / 6 CONN） |
| m13_v52_forensics_probe.py | 取证探针（一次性诊断，非引擎结论；零引擎改动） |
| m13_v52_architecture_target.md | 目标架构：Complete Construction Fact + 三模块职责 + out_MCIO 局部列分配 + invariants I1-I10 + migration P0-P4 + 架构模拟 DN0-7 + 裁决=方案 B（EscapeTable） |
| m13_v52_ccf_schema_v1.json | canonical schema 机器可读版 |
| m13_v52_irg_readiness.md | **IRG = READY_WITH_CHANGES**（3 修订 + 7 节 + 回归门槛） |

## 3. IRG 裁决（v53 开工前必读，勿重推）

**READY_WITH_CHANGES** — 3 项阻塞修订（Phase 1 编码前落文档，均已写入 IRG §8）：
- **R1 schema**：chip_side.landing.via1/via2 唯一事实源 = EscapeTable（allocator 场验证产出）；CCF 只引用 id + 派生几何，禁坐标副本。
- **R2 粒度**：ColumnBook = 中心线占列 ±0.36 reserved 区间 + 独立 via_positions[]；差分对原子分配；净空判据=消费 build_hs_field（纸面 clearance 算术不可靠，F15 实证）；0.01 bookkeeping 仅审计。
- **R3 排序**：MRV（最少候选先分）+ deterministic tie-break (chip_pad_x, base)，替代 DN0→DN7 固定序（防窄域段被 DN5/7 抢共享横走带）。
- 非阻塞：DN0/1/3 NO_ESCAPE 为合法预期输出（域真实窄 [82.85,84.3]），v53 验收不预设必解。
- 保锚资源（只读）：27 段 + DN5/6 pinned；alloc/landing 语义零改动（EscapeTable 纯加性）。

## 4. 下一卡（v53 = NEW_SESSION_PROMPT_v53.md，勿本卡续）

- **v53 范围 = Phase 0 + Phase 1**（IRG §7 门槛）：
  - P0：fact_validate() 反演已解 16 段（只读断言）；施工自搜 fallback 计数记录；e2e 字节 diff==0 基线。
  - P1：EscapeTable dataclass + ColumnBook + EscapeAllocator 骨架（纯加性，空输入零行为）；R1-R3 落 schema。
  - DN0/1/3 是否 ASSIGNED 属 Phase 2，**v53 不承诺**。

## 5. G5 自检

- 消费资产：v52 prompt + v51 F8-F12 + v50 F1-F7 + e2e report + 取证探针（自校验 reason/几何与 report 逐字一致）+ 外部 AI 审计/架构/IRG（沉淀为 9 文件）。
- 纪律：**零生产代码改动**（本卡纯设计）；零 alloc/landing 引擎改动；零 task()/oracle 后台依赖（取证全前台）；净空证据全走 ENG 场 API。
- 待 commit：k2 9 件设计产物（见 §2）；_shared 工作树 dirty 均 v49 前既有残留（frozen chmod 假 dirty + .bak untracked，内容零变化，勿动勿 stage）。
- 未 commit 状态：freeze 后 commit + push（仅 k2 仓）。
