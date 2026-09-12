# M13 v52 → v53 Implementation Readiness Gate（零代码）

> 前置：v52 架构目标（m13_v52_architecture_target.md）+ CCF schema v1 + audit 5 件 + 本 IRG
> 纸面模拟（真实几何，一次性只读分析）。**结论先行：READY_WITH_CHANGES**（3 项明确修订，见 §8）。

---

## 1. CCF / EscapeTable 一致性审查（唯一事实源）

| 字段 | 唯一事实源(producer) | consumer | 重复表达？ | 反向推导？ |
|---|---|---|---|---|
| net/base/segment/anchors | 真板（只读） | CCF 装配器 | 禁（从真板派生一次） | 禁 |
| corridor.id/band/layer/x_range | SPEC corridors（真源） | alloc 消费时读 | 禁 | 禁 |
| track_y P/N | **AllocTable**（channel_alloc） | CCF.alloc_view | 禁 | 禁 |
| connector_side.kind/via/columns | **LandingTable**（escape_landing） | CCF.landing_view | 禁 | **禁**（Landing 已解段实证，不从 CCF 反推） |
| chip_side.escape_column | **EscapeTable**（新，EscapeAllocator） | CCF.chip_view | 禁 | 禁 |
| chip_side.kind | EscapeTable（allocator 在候选域内定形态） | CCF.chip_view | 禁 | 禁（kind 是决策，非推导） |
| chip_side.landing.via1/via2 | EscapeTable（=column+kind 的**实例化产物**，producer=allocator 用场 API 定坐标） | CCF.chip_view | **EscapeTable 存，CCF 不另存（引用）** | 可由 column+kind+几何重算=**同确定性**（允许：值必须逐位相等，加断言） |
| stub/vertical_leg/drop | **派生**（由 landing+column+kind+track_y 确定性生成） | CCF | 派生值仅 CCF 有 | 是（存于 CCF，源=上面字段） |
| trunk centerline | 派生（corridor+track_y） | CCF | 仅 CCF | 是 |
| node_sequence | 派生（kind 模板实例化） | 施工 | 仅 CCF | 是 |
| ownership alloc_id/landing_id/escape_id | 各表 producer | CCF | 各表原生+CCF 引用 | 禁 |
| pinned | **EscapeTable**（allocator 设；保锚段/dn56=true） | CCF, ColumnBook | 禁（EscapeTable 权威） | 禁 |
| column_reservation_id | EscapeTable | ColumnBook | 禁 | 禁 |

**关键裁决**：
- **CCF = assembly/view，不是新事实源**。它只引用 alloc/landing/escape 三表 id + 存派生几何。
- chip_side.via1/via2 事实源是 EscapeTable（allocator 用场 API 验证后写）；CCF 引用其 id。
  **禁止**"CCF 里再存一份坐标副本"——派生段(stub/leg/drop)由装配器确定性生成并校验，唯一落点是
  CCF.construction（施工唯一消费物），但它不是"独立事实"而是"编译产物"，可由源字段重放校验。
- 防不一致手段：`fact_validate()` 对派生字段做**重放断言**（重算==存值，差>1e-6 即 FAIL）。

## 2. 事实 vs 派生 最终边界

| 字段 | 类别 | 谁决策/生成 |
|---|---|---|
| escape_column | **allocation decision** | EscapeAllocator（唯一） |
| chip_side.kind | **allocation decision** | EscapeAllocator（形态=列方案的一部分） |
| via1/via2 坐标 | **geometry instantiation** | allocator 场 API 验证后定（=column 的具体化） |
| vertical_leg | deterministic derivation | CCF 装配器（由 via1/via2 直连） |
| stub | deterministic derivation | 装配器（pad→via1，需场预检记录） |
| drop（PAD_ROW_DIP） | deterministic derivation | 装配器（via1→横走→drop→ty） |
| trunk_centerline | deterministic derivation | 装配器（corridor+track_y） |
| node_sequence | deterministic derivation | 装配器（kind 模板） |
| **施工允许** | 计算线段终点 | 沿声明节点连 line；拐点坐标**必须等于**声明节点（±1e-9） |
| **施工禁止** | 按几何重选节点/换列/换形态 | I1/I2/I8 |

## 3. ColumnBook 压力测试（真实几何纸面模拟，非硬编码示例）

**真实数据**（irg_geom / audit）：
- out pad 行：DN0 P84.6/N85.0、DN1 85.8/86.2、DN2 87.0/87.4、DN3 88.2/88.6、DN4 89.4/89.8、
  DN5 90.6/91.0、DN6 91.8/92.2、DN7 93.0/93.4（P@y52.366, N@y51.673）
- 同 base input 竖腿列（In1/In2 chip 侧）：DN0 84.85/85.15、DN1 86.05/86.35/86.8、
  DN2 87.25/87.55/88.0、DN3 88.45/88.75/89.2、DN4 89.65/89.95/90.4、DN6 92.05/92.35/92.8；
  **DN5/DN7 input 未解 → 无同 base 占用**
- GND/电源球（chip 西带 x82-95）：竖列 83.43/83.95/84.2/84.55/85.4/85.45/85.75/86.6… + 阵内
  90.2/91.4…，**密集栅格**（0.4/0.6 节距）

**模拟结论**：
1. **初始 forbidden mask** = 同 base input 竖腿列 ±(0.175+0.1025=0.28 边距 → 中心 0.36) ∪
   GND/电源球（**F.Cu 层 via/stub 净空**，In1/In2 竖腿 seg 与 F.Cu 球异层不互挡）∪ corr 东界
   82.35+0.5 以西禁入。
2. **pinned mask** = DN5/6 已解列（90.6/91.0、91.2/91.6 或列分配后落点）+ 27 段保锚竖腿列。
3. **candidate domain 宽度随 pad 西移而增**：DN0 [82.85,84.3] 最窄(~1.5mm)，DN6 最宽；DN5/7
   因无同 base 占用可从 pad 列直下（域含 pad 列本身）。
4. **P/N 错列组合**：DN0 理论 506、DN1 2162…DN7 36290（0.05 步进）→ **低编号紧、高编号松**。
5. **纸面 clearance 判据不可靠**：我试算 via_pad 0.5 中心距 → 全 NO_ESCAPE，但隔离实验实证
   DN0 col_stack@pad 列可 SOLVED（真实 build_hs_field 中 GND 84.2/53 与 via 84.6/52.816 间距
   0.44 被允许——规则口径是 RULE_CLEARANCE+膨胀，非我的简化）。**→ 逐列净空唯一可信判据 =
   消费 build_hs_field.seg_ok/point_ok（与 v51 引擎同场），纸面只做域粗筛**。
6. **DN0/1/3 真风险**：域窄 + 场障碍（除同 base input 外还有异 base 邻族 pad/via 与
   PAD_ROW_DIP 所需 In2 pad 行横走带）→ **NO_ESCAPE 是真实可能输出，设计必须接受**。

## 4. ColumnBook 粒度模型（不可歧义）

- **col = 单个 X 列资源**（bookkeeping 单位 0.01mm），但**分配以差分对原子组**发出：
  P/N 两列一起占、一起释放（I：单极不允许，差分对不可拆）。
- **P/N 错列约束**：中心距 ≥ 0.36mm（= 2×PAIR_HALF 0.19 余量，防同列 via 堆叠的 col_stack
  既有阈值，v51 实证）。纵向无需额外，因 P/N 轨行差 0.38。
- 0.01 bookkeeping **≠ clearance**：bookkeeping 用于"分配簿唯一性/审计"，净空判据是
  场 API 几何（0.01 列只是候选采样步进）。候选步进 0.05mm，写入簿按实际分配列。
- column reservation = **中心线占用 + 关联 keepout 区间**（占列±0.36 为该 pair 的
  reserved 区间，禁止他 pair 中心落入），非纯点。
- via clearance 独立维度：ColumnBook 同时记 `via_positions[]`（绝对坐标），新 via 落点须
  与既有 via ≥0.35+netclear（DN7 式同列堆叠即此级拦截，见 §6 VIA_COLLISION）。

## 5. Allocation 顺序：MRV（推荐）覆盖固定序

**问题确认**：固定 DN0→DN7 会把低编号（窄域 DN0/1/3）的**真实需求**暴露在"高编号抢列"之前，
但高编号域宽（DN5/6/7 大域）本可让路 → 固定序可能让 DN0 抢到唯一可用列而 DN1（更窄或更
敏感）反而 NO_ESCAPE。**DN5/7 input 未解（无同 base 约束）域含 pad 列 → 若先分，可能与低编号
西行横走带冲突**（异 base 也互不占用的 In2 pad 行带）。

**推荐：策略 B（MRV + deterministic tie-break）**：
1. 候选计数：每段候选 pair 数（域宽-同 base 占用-GND 级净空，用场 API 粗扫）。
2. 升序分配（候选最少先分）——把最紧的 DN0/1/3 排最前，避免被 DN5/7 抢走共享横走/列资源。
3. tie-break：`(chip_pad_x 升序, base 数字升序)` 全定序。
4. **确定性**：候选集用 list 排序（禁 set 迭代）；ColumnBook 用 dict（插入序=分配序）；
   全流程无 `for x in set` 式枚举。加 `determinism_seed=0` 断言：同输入两次运行
   allocation 序列 == 逐字节相等（e2e 复用指纹）。

## 6. NO_ESCAPE 语义（统一状态码 + reason enum）

```
EscapeTable.status = ASSIGNED | NO_ESCAPE
NO_ESCAPE.reason ∈ {
  NO_CANDIDATE_DOMAIN,    // 域空：pad 西侧 0.5~2.0mm 内无采样列（corr_east+0.5 到 pad_x-0.3）
  PAIR_CLEARANCE_FAIL,    // 域有单列但无 |P−N|≥0.36 的合法组合
  KEEP_OUT_COLLISION,     // 域内列全落保锚/GND/refclk keepout 区间
  VIA_COLLISION,          // 域内列 via 落点全与既有 via/pad 冲突（DN7 同列堆叠类）
  PINNED_CONFLICT         // 算法欲占的列已被 pinned 段持有（= 程序错误，直接抛）
}
NO_ESCAPE.evidence = {
  nearest_obstacle: {net, dist, req},
  forbidden_mask_snapshot: [...],
  attempted_domain: [lo, hi],
  attempted_pairs: n
}
```
Plan FAIL 输出该对象，e2e gap 记录（完全可复现，禁静默）。

## 7. Phase 0→3 回归门槛（自动化 acceptance）

| Phase | 自动化 gate |
|---|---|
| P0 | e2e 字节 diff（HEAD report vs new）== 0；新增 `fact_validate()` 对已解 16 段全过；自搜 fallback 计数只记录不拦截 |
| P1 | EscapeTable 空输入 → 全链行为逐字节==P0；非空 → alloc/landing dataclass 字段零改动（schema 加性断言）、旧消费方读旧键值相等 |
| P2 | out_MCIO allocator：DN0-7 输出 ∈ {ASSIGNED, NO_ESCAPE(带 reason/evidence)}；ColumnBook 断言：27 保锚列 + DN5/6 pinned 列写操作计数==0；无 133.825 类同列 via 新登记 |
| P3 | 施工入口 `fact 缺失 → 立即 FAIL`（抛 NO_CONSTRUCTION_FACT）；**fallback enumeration count==0**（dip/col_stack 自搜路径不可达，单测注入证明）；已解 16 段走 fact 路径字节==P2 |
| P4 | 全量 segment fact 覆盖率==100%；I1-I10 测试套件全绿；e2e solved_pairs/段级 == P3 或更好 |

## 8. 裁决：READY_WITH_CHANGES

架构/职责边界/资源模型**均已收敛可开工**，但有 3 项必须在 Phase 1 coding 前修订进设计：

1. **修订 R1（schema）**：`chip_side.landing.via1/via2` 由 EscapeTable 持有（allocator 产出，
   场 API 验证）；CCF 只引用 id + 存派生几何，**不存 via 坐标副本**（消除双写源）。
2. **修订 R2（粒度）**：ColumnBook 记**中心线占列 ±0.36 reserved 区间 + 独立 via_positions[]**，
   差分对原子分配；0.01 bookkeeping 仅审计，净空判据=场 API（§3.5 教训固化）。
3. **修订 R3（排序）**：默认 **MRV + (chip_pad_x, base) tie-break**，替代 DN0→DN7 固定序；
   实现须显式确定性（list 序 + dict 插入序 + determinism 断言）。

**非阻塞但应记录**：DN0/1/3 的 NO_ESCAPE 为**合法预期输出**（域真实窄），v53 验收不预设
三者必解；P2 后按实际 ASSIGNED/NO_ESCAPE 分布决定是否进入"西行横走带共享协调"子问题。

**结论：v53 Phase 0/1 可以安全开工**（Phase 0 纯审计零行为；Phase 1 纯加性 schema +
上列 3 修订落文档）；Phase 2 依赖 R1-R3 修订后即可编码。
