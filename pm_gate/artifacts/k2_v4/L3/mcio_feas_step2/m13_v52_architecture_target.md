# M13 v52 架构目标 — "完整施工事实(Complete Construction Fact)" 设计

> 状态：设计稿（零代码改动）。前置：v52 审计（m13_v52_audit_*.json 5 件 + handoff）。
> 审计定案：方案层输出"半事实"（AllocTable + LandingTable 无 chip-side 字段），施工被迫自搜
> 芯片侧逃逸列 → DN0-4 撞同 base input 段 + GND 球。本设计把方案层重定义为
> "ENG 可行性 → 完整施工事实"，施工只做 deterministic connect。

---

## 0. 设计原则（不可妥协）

- **P1 施工零决策**：施工输入必须含全部几何节点（via/列/轨行/层），施工只做"逐段连接 +
  净空复核"，不枚举、不搜索、不 fallback。
- **P2 方案层 FAIL 优先**：任何 Segment 无法在方案层形成完整事实 → 方案层 FAIL，绝不下放。
- **P3 保锚即资源**：27 段保锚 + DN5/6 已解段 = 只读占用源，局部分配读它、永不写它。
- **P4 加性演进**：Schema 扩展全加性，旧字段语义零变更，默认行为不变，显式声明生效。
- **P5 列是一级资源**：chip-side escape column 纳入 alloc 级 reservation，杜绝施工层临时搜索。

---

## 一、Complete Construction Fact — Canonical Schema

### 1.1 目标：每 Segment 一条 `ConstructionFact`（机器可读 JSON）

```jsonc
// construction_fact（每 base×segment 一条，方案层 Phase ②产出）
{
  "fact_id": "PCIE_DN0/out_MCIO",           // 唯一键（base/segname）
  "schema_version": "ccf-v1",
  "net":  {"P": "PCIE_DN_OUT0_P_MCIO", "N": "PCIE_DN_OUT0_N_MCIO"},
  "base": "PCIE_DN0",
  "segment": "out_MCIO",

  // ── 锚（源/目的 pad，绝对坐标，只读自真板）──────────────
  "anchors": {
    "source":      {"P": [63.7, 61.45], "N": [64.3, 61.45], "ref": "J3",  "side": "connector"},
    "destination": {"P": [84.6, 52.366], "N": [85.0, 51.673], "ref": "U6", "side": "chip"}
  },

  // ── 走廊 / 轨行（alloc 已定，原样透传）──────────────────
  "corridor": {
    "id": "WEST_MCIO_TO_CHIP", "band": "dn",
    "x_range": [65.05, 82.35],
    "track_y": {"P": 58.89, "N": 58.51},     // = track_y 58.7 ± half_pitch 0.19
    "layer": "In2.Cu"
  },

  // ── 连接器侧逃逸（connector_side landing，现 LandingTable 正确部分）──
  "connector_side": {
    "kind": "LSWAP_V",                        // 施工不选形态——方案已定
    "via":   {"P": [61.9, 62.1], "N": [62.5, 62.1]},   // 绝对坐标
    "vertical_leg": {"P": [[61.9,62.1],[61.9,66.09]], "N": [[62.5,62.1],[62.5,65.71]]},
    "columns": {"P": 61.9, "N": 62.5},        // 出线列（方案分配）
    "layer_fcu": "F.Cu", "layer_carrier": "In2.Cu",
    "landing_ref": "PCIE_DN_OUT0_P_MCIO"      // 对应旧 LandingTable 记录（兼容指针）
  },

  // ── 芯片侧逃逸（★ 新增核心字段：chip_side_landing）────────
  "chip_side": {
    "kind": "COL_STACK",                      // 或 PAD_ROW_DIP；方案在候选域内确定
    "escape_column": {"P": 84.15, "N": 84.55},// ★ 一级分配资源（alloc 决定）
    "landing": {                               // ★ chip_side landing（via₁ 绝对坐标）
      "via1": {"P": [84.15, 52.816], "N": [84.55, 52.123]},
      "via2": {"P": [84.15, 58.89],  "N": [84.55, 58.51]}   // 轨行 col-top via（COL_STACK）
    },
    "vertical_leg": {"P": [[84.15,52.816],[84.15,58.89]],
                     "N": [[84.55,52.123],[84.55,58.51]]},
    "stub": {"P": [[84.6,52.366],[84.15,52.816]],
             "N": [[85.0,51.673],[84.55,52.123]]},          // F.Cu stub（方案预检净空）
    "drop": null,                              // PAD_ROW_DIP 用：pad 行横走→drop 列
    "layer_fcu": "F.Cu", "layer_leg": "In1.Cu",
    "carrier": {"field": "In2.Cu", "run": "pad_row"}        // dip 载体层语义
  },

  // ── 中段（轨道/trunk 连段）──────────────────────────────
  "trunk": {
    "centerline": {"from_x": 82.35, "to_x": 62.5},          // corridor 内直连段
    "layer": "In2.Cu"
  },

  // ── 归属 / 占用 / 锁 ──────────────────────────────────
  "ownership": {
    "alloc_id": "PCIE_DN_OUT0",                // 轨行分配键
    "landing_id": ["PCIE_DN_OUT0_P_MCIO", "PCIE_DN_OUT0_N_MCIO"],
    "column_reservation_id": "CC-84.15-84.55-DN0-out"       // ★ chip 列 reservation
  },
  "pinned": false,                             // true = 不可被后续 local alloc 改（DN5/6 段 = true）
  "reservations_dep": [                        // 本事实依赖的占用（只读）
    {"type": "anchor_segment", "id": "PCIE_DN0/input", "cols": [84.85, 85.15]},
    {"type": "gnd_ball", "cols": [84.2, 84.25, 84.55, 82.91, 83.43, 83.95]},
    {"type": "via_forbidden", "desc": "DN7 133.825 同列禁区"}
  ],

  // ── 施工执行信息（只读消费，非决策）────────────────────
  "construction": {
    "node_sequence": {                          // ★ 施工只沿此序列连线
      "P": ["anchor_dest", "stub", "via1", "vertical_leg", "via2", "trunk",
            "conn_leg", "conn_via", "anchor_src"],
      "N": ["anchor_dest", "stub", "via1", "vertical_leg", "via2", "trunk",
            "conn_leg", "conn_via", "anchor_src"]
    },
    "connect_only": true,
    "recheck": ["seg_ok per segment", "pn_min_edge >= 0.155"]   // 复核，不搜索
  }
}
```

### 1.2 字段职责矩阵（谁决定 / mandatory / 派生）

| 字段 | 决定方 | mandatory | 可否派生 | 施工可推导？ |
|---|---|---|---|---|
| net/base/segment | 真板+config 链模式 | ✓ | 否（真源） | **禁止** |
| anchors source/dest | 真板 pad 簇 | ✓ | 否 | **禁止** |
| corridor id/band/x_range | SPEC corridors | ✓ | 否 | **禁止** |
| track_y P/N | alloc（channel_alloc） | ✓ | 否 | **禁止** |
| layer | alloc band | ✓ | 否 | **禁止** |
| connector_side.kind/via/columns | **方案层 EscapeAllocator** | ✓（已有段可证） | 可由 landing+归属 | **禁止** |
| chip_side.escape_column | **方案层 EscapeAllocator（一级资源）** | ✓ | 否（分配决策） | **禁止** |
| chip_side.landing via1/via2 | 方案层（由 escape_column + 形态模板定） | ✓ | 由 column+kind 推导 | **禁止** |
| vertical_leg/stub/drop 几何 | 方案层形态模板实例化 | ✓ | 由 landing+column 推导 | **禁止** |
| ownership alloc_id/landing_id | 既有 alloc/landing | ✓ | 否 | 禁止 |
| column_reservation_id | 方案层 | ✓ | 否 | **禁止** |
| pinned | 方案层（保锚段/DN5/6=true） | ✓ | 否 | 禁止 |
| reservations_dep | 方案层汇总 | ✓ | 否 | 禁止 |
| trunk centerline | alloc corridor | ✓ | 由 corridor+轨行推导 | 仅连线 |
| construction.node_sequence | 方案层模板 | ✓ | 由上述全部推导 | 只消费 |

**施工层唯一允许做的事**：按 `node_sequence` 逐段 `seg_ok` 连线 + 组装 P/N + `pn_min_edge≥0.155` 复核。任何"这个列不行试下个列"的循环 = 违例。

---

## 二、三模块职责边界

### ENG feasibility
- **不计算具体 escape_column**（答案 A：NO，不直接算列）。
- 输出：① 每 base/segment 存在性与端点锚；② 走廊/轨行候选（track 容量已证）；③ **每段 chip-side escape requirement = 声明式缺口**：`{segment, chip_pad_cols, corridor_east_x, chip_side_escape: REQUIRED, candidate_domain: 由几何推导}`；④ 约束：keepout（REFCLK 区等）、净距规则、diff-pair 标识、BGA 球阵（chip pad 列+GND 球列掩码）。
- 新增输出字段：`demands[].chip_escape = {required: true, domain: [x_lo, x_hi], avoid_cols: [...]}`。

### Implementation Plan（方案层 = alloc + landing + **新 EscapeAllocator**）
- **负责最终 column allocation（答案 B：YES）**。column reservation 升为一级资源：
  - 资源簿 `ColumnBook`：chip 出线区 x∈[82,104] 逐 0.01 列 → {占用者, 层, pinned}。
  - 占用源：27 保锚段 chip 列、DN5/6 已解列、GND/电源球列、已有 reservation。
- alloc：轨道分配不变（`AllocTable` 原样）；**新增 `EscapeAllocation`**（chip+connector 双端列）。
- landing：保留 `LandingTable`（connector 侧语义正确）→ 修正 10 条 pad 锚错记录（B1 修正：region 派生按 segment 双端各锚，不再取 max-x）。

### 双端 landing vs 独立 EscapeTable（答案 C）
比较：

| 方案 | 优点 | 缺点 | 裁决 |
|---|---|---|---|
| C1 LandingTable 扩双端 | 单一事实源 | connector 语义已由 alloc 消费方锁死，扩字段风险高；landing=连接器落点概念污染 | 否 |
| C2 独立 EscapeTable（推荐） | chip 侧与 connector 侧**本质不同资源**（列 vs 落点）；P3 隔离保锚；可独立演进 | 双表一致性需 fact 层校验 | **推荐** |
| C3 全新统一 SegmentPlan | 最干净 | 重构 blast radius 最大，与现行 alloc/landing/solve 双轨并存复杂 | Phase 4 远期 |

**推荐架构（v53 起点）**：**保留 AllocTable + LandingTable 语义不变，新增 `EscapeTable`**（chip_side 为主，connector_side 现有 landing 记录校验透传），之上加 `ConstructionFact` 装配器（把 alloc+landing+escape → fact），施工消费 fact。

---

## 三、out_MCIO 局部列分配算法（Local Chip-Side Escape Allocation）

> 仅针对 out_MCIO 段族（DN0-7 out_MCIO chip 侧），不动其它域。

1. **输入**
   - 真板 chip pad 簇 + GND 球列掩码（几何只读探针）
   - 27 保锚段 chip 列掩码（audit_geometry_anchors）
   - DN5/6 已解段 chip 列（pinned）
   - alloc track_y（各 out 段 WEST 轨行）
   - corridor x_range（WEST_MCIO_TO_CHIP [65.05,82.35]）
   - 隔离实验证明的可行形态域（COL_STACK 直腿 / PAD_ROW_DIP 横走）
2. **forbidden mask 形成**：锚段列 ∪ GND 球列（含球半径+净距 0.175+半线宽）∪ pinned 列 ∪ DN7 via 禁区（133.825 列仅 J2 域，chip 侧无关但保留全局）。
3. **candidate column 产生**：chip pad 列西移 0.15~1.5（0.05 步）∩ 不在 forbidden ∩ 满足 P/N 错列 ≥0.36 ∩ 竖腿 seg_ok 净空（用场 API 预检，方案层做）。DN0 候选示例：84.15/84.55（避开 input 84.85/85.15 与 GND 84.2/84.55）。**注意**：DN0 chip pad 84.6/85.0 本身就在 GND 84.2/84.25 与 input 段之间，真实候选域可能很窄 → 算法必须能在域空时**报"域不可行"而非 fallback**。
4. **排序**：按 chip pad x 升序（DN0→DN7）或按 track_y idx 升序（= DN0→DN7），先占先得 + 每 base 分配后写 ColumnBook。
5. **资源模型**：差分对 = 2 列（P/N 各一列，错列 ≥0.36）+ 竖腿 via 对；单端 = 1 列。无差分豁免。
6. **防同 base input/out 争列**：ColumnBook 预载同 base input 段列（84.85/85.15）为 forbidden → out 只能在剩余域选（结构性杜绝 F13 型撞车）。
7. **防 DN7 式同列 via**：ColumnBook 的 via 级占用（含列坐标）→ 新 via 必须与既有 via ≥0.35+净距；同列不同层也禁（DN7 是 F.Cu stub 竖线穿落点 via，同列垂直重叠即禁）。
8. **27 段零重分配**：保锚列掩码=只读，EscapeAllocator 无权写；分配结果 diff 断言（audit 复跑）。
9. **DN5/6 pinned**：ColumnBook 标记 `pinned:true` + fact.pinned=true → 算法跳过，且任何冲突报错而非改。
10. **失败语义**：候选域空 / 无满足净距列 / 与 pinned 冲突 → **EscapeTable 标记该段 `status:NO_ESCAPE` → 方案层 FAIL（fact 不产出）**，e2e gap 明示"chip 侧无可用列+原因"，**绝不回退施工搜索**。

---

## 四、连连看不变量（写进代码/测试）

| # | 不变量 | 验证层 |
|---|---|---|
| I1 | 施工层不创建新 escape_column（chip 侧所有 via.x ∈ fact.chip_side 声明集） | 施工断言 + 单测 |
| I2 | 施工层对未知 chip-side landing 不搜索（fact 缺失即抛/FAIL，无 fallback 链） | 施工入口守卫 |
| I3 | 每进入施工的 Segment 必备完整 fact（字段完备性校验 schema） | fact 装配器 validate |
| I4 | 方案层无法形成完整 fact → Plan FAIL（不让决策下放） | EscapeAllocator 返回 NO_ESCAPE |
| I5 | 施工只消费方案节点，不改 alloc/landing/ColumnBook | 施工只读接口 |
| I6 | Pinned segment 不被后续 local alloc 修改 | ColumnBook 写守卫 |

**判定**：I1-I6 全部正确。**补充遗漏**：
- **I7 反向引用完整**：fact 的每节点可回溯到 alloc/landing/reservation id（可审计性）。
- **I8 施工输出 ⊆ 方案节点**：施工 path 的每个拐点必须是 fact 节点（不产生未声明拐点）——防"偷偷多拐一折"。
- **I9 净空复核≠净空搜索**：施工 `seg_ok` 失败 = 方案缺陷证据（FAIL 上报），不是重试入口。
- **I10 域不可行有原因字段**：NO_ESCAPE 必须带最近障碍 net/dist/req（v50 F3 式证据），禁止静默失败。

---

## 五、Migration Path（v52 → 目标，四阶段）

### Phase 0 — 保持现状 + audit/assert（零行为）
- 加：`construction_fact.validate()`（对已解 16 段反演 fact，断言字段齐）；施工入口 assert "无未知 chip landing 时禁止 dip/col_stack 自搜 fallback（当前仍允许=记录计数）"。
- 验证：e2e 复跑字节相等（28 段零变更）；产出"自搜缺口清单"（哪些段仍靠 fallback）。
- 文件：hs_route_model.py（+assert/diag，dormant）、新 audit 脚本。

### Phase 1 — 扩展 Schema（加性）
- 新增字段：`chip_side_landing`/`escape_column`/`column_reservation_id`/`pinned`（ModelConfig + 新 EscapeTable dataclass）。
- 兼容：LandingTable 不动；ModelConfig 旧键不动；escape_env_* 保持。
- 验证：单测 schema round-trip + 旧输入零变化 e2e。

### Phase 2 — out_MCIO local escape allocation
- 新模块 `escape_allocator.py`：ColumnBook + forbidden mask + 候选枚举 + NO_ESCAPE。
- 修正 escape_landing region 派生（B1：pad 锚按 segment 双端，不再 max-x 误锚 10 条）。
- DN0-7 out_MCIO 生成 EscapeTable 记录；DN5/6 反演为 pinned；DN0/1/3 尝试分配。
- 验证：合成板单测（列分配净空/错列/保锚互斥）+ e2e 段级 ≥17 且 DN0/1/3 ≥+1。

### Phase 3 — 施工层关 fallback
- `_escape_pair` 收窄：有 fact → 只消费；无 fact → 直接 INFEASIBLE（删 dip/col_stack 自搜枚举，或加 feature flag 默认关）。
- 验证：单测（构造无 fact 段 → 立即 FAIL 不枚举）；e2e 全量（已解段必须全走 fact 路径字节不变）。

### Phase 4 — 全量 Segment 收敛
- 全部段（含 input/out_J2/REFCLK）经 EscapeAllocator 产 fact；删施工 fallback 链残余。
- 验证：全量 e2e + 不变量测试套件（I1-I10）。

---

## 六、架构模拟 — 新 Schema 实例（真实数据，今日即所得）

> 用 audit 真实几何。★ = 新增字段（当前缺失）；其余字段现有 alloc/landing 已含。

### DN0 out_MCIO（现 INFEASIBLE）
```jsonc
{
  "base": "PCIE_DN0", "segment": "out_MCIO",
  "anchors": { "dest(U6)": {"P":[84.6,52.366],"N":[85.0,51.673]},
               "src(J3)": {"P":[63.7,61.45],"N":[64.3,61.45]} },
  "corridor": { "id":"WEST_MCIO_TO_CHIP", "band":"dn",
                "track_y":{"P":58.89,"N":58.51}, "layer":"In2.Cu" },
  "chip_side": {
    "kind": "COL_STACK",
    "★escape_column": {"P": 84.15, "N": 84.55},
    "★landing.via1": {"P":[84.15,52.816],"N":[84.55,52.123]},
    "★landing.via2": {"P":[84.15,58.89],"N":[84.55,58.51]},
    "stub": {"P":[[84.6,52.366],[84.15,52.816]], "N":[[85.0,51.673],[84.55,52.123]]},
    "★column_reservation_id": "CC-84.15-84.55-DN0-out",
    "reservations_dep": ["PCIE_DN0/input cols[84.85,85.15]",
                         "GND balls [84.2,84.25,84.55]", "corr_east 82.35"]
  },
  "connector_side": { "kind":"LSWAP_V",
    "via":{"P":[61.9,62.1],"N":[62.5,62.1]}, "landing_ref":"PCIE_DN_OUT0_P_MCIO" },
  "ownership": {"alloc_id":"PCIE_DN_OUT0",
                "★escape_id":"ESC-DN0-out-MCIO", "pinned": false },
  "construction.node_sequence": {"P":["U6_pad","stub","via1","leg","via2","trunk","conn","J3_pad"], "N":[…]}
}
```
**DN0/1/3 今天会多出的字段**：`chip_side.escape_column`、`chip_side.landing.via1/via2`、
`column_reservation_id`、`pinned`、`construction.node_sequence`。**施工最终消费**：node_sequence +
各节点绝对坐标 → 逐段连直线，不再枚举（今天施工在 DN0 上是 9361 次 dip pn 枚举，新架构=0 次）。

> ⚠️ 候选列 84.15/84.55 为**示意域**：实际必须经 ColumnBook 冲突检查（84.15 与 GND 84.2 净距
> 0.05 可能不足 → 算法会西移/改 PAD_ROW_DIP 横走形态重试，仍空则 NO_ESCAPE）。设计中不预设
> DN0/1/3 必可解——列域可能真不足（这是"方案层 FAIL"的合法出口，v52 已证 dip drop 域仅 ~2mm）。

### DN1 out_MCIO（现 INFEASIBLE）
```jsonc
{ "base":"PCIE_DN1", "segment":"out_MCIO",
  "anchors":{"dest(U6)":{"P":[85.8,52.366],"N":[86.2,51.673]}},
  "corridor":{"track_y":{"P":60.09,"N":59.71}},           // alloc 59.9 ± 0.19
  "chip_side":{"kind":"COL_STACK",
    "★escape_column":{"P":85.35,"N":85.75},               // 避 input 86.05/86.35 + GND
    "★landing.via1":{"P":[85.35,52.816],"N":[85.75,52.123]},
    "★landing.via2":{"P":[85.35,59.71],"N":[85.75,60.09]}},
  "connector_side":{"via":{"P":[61.9,61.45],"N":[62.5,61.45]}, "landing_ref":"PCIE_DN_OUT1_P_MCIO"},
  "ownership":{"alloc_id":"PCIE_DN_OUT1","★escape_id":"ESC-DN1-out-MCIO","pinned":false} }
```

### DN3 out_MCIO（现 INFEASIBLE）
```jsonc
{ "base":"PCIE_DN3", "segment":"out_MCIO",
  "anchors":{"dest(U6)":{"P":[88.2,52.366],"N":[88.6,51.673]}},
  "corridor":{"track_y":{"P":62.49,"N":62.11}},           // alloc 62.3 ± 0.19
  "chip_side":{"kind":"COL_STACK",
    "★escape_column":{"P":87.75,"N":88.15},
    "★landing.via1":{"P":[87.75,52.816],"N":[88.15,52.123]},
    "★landing.via2":{"P":[87.75,62.11],"N":[88.15,62.49]}},
  "connector_side":{"via":{"P":[61.9,61.45],"N":[62.5,61.45]}, "landing_ref":"PCIE_DN_OUT3_P_MCIO"},
  "ownership":{"alloc_id":"PCIE_DN_OUT3","★escape_id":"ESC-DN3-out-MCIO","pinned":false} }
```

### DN5 out_MCIO（已解，反演为 pinned fact）
```jsonc
{ "base":"PCIE_DN5","segment":"out_MCIO",
  "anchors":{"dest(U6)":{"P":[90.6,52.366],"N":[91.0,51.673]}},
  "corridor":{"track_y":{"P":64.89,"N":64.51}},           // alloc 64.7 ± 0.19
  "chip_side":{"kind":"COL_STACK",
    "escape_column":{"P":90.6,"N":91.0},                  // = pad 列（自搜恰好同列）
    "landing.via1":{"P":[90.6,52.816],"N":[91.0,52.123]},
    "landing.via2":{"P":[90.6,64.89],"N":[91.0,64.51]}},
  "ownership":{"alloc_id":"PCIE_DN_OUT5","pinned":true},  // ★ 反演自 report（勿动）
  "construction.node_sequence": 反演自已解 path }
```

### DN6 out_MCIO（已解，PAD_ROW_DIP，pinned fact）
```jsonc
{ "base":"PCIE_DN6","segment":"out_MCIO",
  "anchors":{"dest(U6)":{"P":[91.8,52.366],"N":[92.2,51.673]}},
  "corridor":{"track_y":{"P":66.09,"N":65.71}},           // alloc 65.9 ± 0.19
  "chip_side":{"kind":"PAD_ROW_DIP",
    "escape_column":{"P":91.2,"N":91.6},                  // stub 0.6 via@pad 行
    "landing.via1":{"P":[91.2,52.366],"N":[91.6,51.673]},  // = dip via（pad 行）
    "drop":{"P":[82.75,52.366→66.09],"N":[82.35,51.673→65.71]},  // drop 列（dip 特有）
    "carrier":{"field":"In2.Cu","run":"pad_row 91.2→82.75"}},
  "ownership":{"alloc_id":"PCIE_DN_OUT6","pinned":true},
  "connector_side":{"via":{"P":[62.5,62.1],"N":[61.9,62.1]}, "landing_ref":"PCIE_DN_OUT6_P_MCIO"} }
```

**模拟回答**："施工层最终消费什么" = `construction.node_sequence` + `anchors` + 各
`chip_side/connector_side` 节点绝对坐标 + `corridor.track_y/layer`。DN0/1/3 相比今天多出
★ 字段 5 项；施工从"9361 次 pn 枚举 + 撞列"变为"沿声明的 9 节点直线连接 + 复核"。

---

## 七、架构裁决

| 维度 | A 扩展现有 Alloc+Landing | B 新增 EscapeTable | C 统一 SegmentPlan |
|---|---|---|---|
| 改动风险 | 中（污染既有消费方） | **低（纯加性）** | 高 |
| 向后兼容 | 低（表语义变宽） | **高（零删改）** | 低 |
| 数据完整性 | 中（一表两义） | **高（每资源一表）** | 高但迁移重 |
| 施工确定性 | 中 | **高（fact 装配显式）** | 高 |
| 长期可扩展 | 中 | 高（U7/U3/输入段族可复用） | **最高** |
| 职责边界清晰 | 中 | **高** | 最高 |

**裁决：方案 B（推荐）**——新增 `EscapeTable`（chip 侧列分配为一级资源）+ `ConstructionFact`
装配层，AllocTable/LandingTable 语义原样保留。理由：本问题根因是"chip-side 几何字段缺失"，
B 用纯加性补字段、零删改，Phase 2 即可局部投用 out_MCIO；C 留作 Phase 4 全量收敛时的远期
整合（届时 EscapeTable 天然升级为 SegmentPlan 的内核，无需另起炉灶）。

---

## 附录：与现行代码的映射（改哪些）

| 概念 | 现行 | 目标 |
|---|---|---|
| 轨行 | `AllocTable.alloc[PCIE_DN_OUT*].track_y` | 不变（透传 fact.corridor） |
| 连接器落点 | `LandingTable.allocation[net].landing` | 不变 + 修 B1 pad 锚（10 条） |
| chip 列 | **不存在** | `EscapeTable`（新） |
| chip landing | **不存在**（施工自搜） | `EscapeTable.landing.via1/via2` |
| 保锚 | 隐式（顺序前馈） | 显式 `ColumnBook.pinned` |
| 施工 escape | `_col_stack_escape/_pad_row_dip_escape/…` 自搜链 | 消费 fact（Phase 3 关 fallback） |
| 消费归属门 | `_landing_pair_usable` | 不变（校验 fact 而非搜索） |
