# v53 Phase 2 实现规格 — out_MCIO Local EscapeAllocator（P0/P1 已交付后锁定）

> 前置：m13_v53_session_handoff.md（F20-F27 钉死）+ m13_v53_p0/p1_audit.json +
> _shared/eda_core/{column_book,escape_table,construction_fact}.py（本卡已落码，直接 import）。
> 本文件 = Phase 2 唯一权威规格。所有裁决 v53 已定，**coding 无需再做架构决策**。

---

## 0. 范围边界（勿扩勿缩）

- **做**：新模块 `_shared/eda_core/escape_allocator.py`（MRV + L2 净空 + ColumnBook 写 +
  EscapeTable 产出行）；K2 e2e 前 DN0-7 out_MCIO chip 侧局部列分配（DN5/6 pinned 反演直填，
  DN0/1/3 尝试分配）。
- **不做**：施工 fallback 关闭（Phase 3）；全量 segment（Phase 4）；REFCLK/UP 族 chip 侧；
  alloc/landing 修正；ColumnBook 之外的候选搜索逻辑混入簿。
- **验收不预设 DN0/1/3 必解**：NO_ESCAPE（带 reason/evidence）是合法预期输出（IRG §8）。

## 1. 输入（全部只读）

1. e2e report `stages.*`（solve 16 SOLVED 段 = pinned 反演源；alloc 34；landing 52）。
2. 真板 k2_v4.kicad_pcb（只读探针）+ SPEC corridors + route_model_config（hs_route_model 段）。
3. 27 保锚列掩码 + DN5/6 pinned（P1 已反演 16 行 EscapeTable，几何=SOLVED path，勿重算）。
4. ColumnBook 预载：27 保锚列 + DN5/6 pinned 列 + GND/PWR ball 只读。

## 2. 模块结构（escape_allocator.py，新增单文件）

```
EscapeAllocator
├── __init__(board, spec, rules, config, alloc, landing, escape_pinned,
│             column_book=None)          # column_book 可注入（测试用合成簿）
├── build_forbidden_mask()                # L1 掩码：保锚∪pinned∪GND/PWR∪REFCLK keepout∪reservation
├── level1_candidates(base, segname)      # → 有序 pair 列表（P 升序，同P内 N 升序）
│     domain: corr_edge+0.5 … pad_x-0.3，0.05 步 → snap 0.01
│     keepout ∩ reservation ∩ |xN-xP|>=0.36
├── level2_validate(base, segname, xp, xn) # build_hs_field 逐候选：stub seg_ok→via1
│     point_ok+annulus→竖腿 seg_ok→via2 point_ok→走廊/横走 seg_ok→
│     pn_min_edge>=0.155→与既有 via_positions 间距。唯一 ASSIGNED 门。
├── mrv_allocate()                        # Step1-6（见 §3），零 set 迭代
├── _tie_break_key(seg)                   # (n_cands↑, chip_pad_x_P↑, base_num↑, seg_rank↑)
└── deterministic_assert()                # 同输入双跑 == 逐字节（determinism_seed=0）
```

- 零板级特判：corridor/domain/net 全来自 SPEC+config+真板探针；禁 "84.15" 类字面量。
- EscapeTable 产出行写 chip_side.kind（COL_STACK/PAD_ROW_DIP 依几何）+ via1/via2（L2 场验证后
  定坐标）+ provenance{solve_ref, input_fp, allocator:"v53-p2"}（R17）。

## 3. MRV 确定性（v53 已裁，直接照抄）

1. 候选集：每未 pinned segment 跑 level1 → 有序 pair 列表。
2. 候选数最少者先分。
3. tie-break（固定全序）：`(len(cands)↑, chip_pad_x_P↑, base 数字后缀↑, segment 秩↑)`，
   秩 = [input, out_MCIO, out_J2] 索引。
4. L2 通过 → ColumnBook 原子写（P/N 双 reservation + via_positions）→ EscapeTable 行 ASSIGNED。
5. **全量重算**剩余未分段候选（≤8 段，防陈旧，弃增量）。
6. 候选集归零 → 该段 NO_ESCAPE(reason=PAPER_FILTER_EMPTY, detail=RESERVATION_CONFLICT,
   evidence 含 attempted_domain/attempted_pairs/nearest_obstacle)，排除续分。无 dependency 回退、
   无施工层 backtracking。

## 4. 失败语义（enum 终版，escape_table.py 已导出）

```
EscapeStatus = ASSIGNED | NO_ESCAPE
NoEscapeReason = PAPER_FILTER_EMPTY | HS_FIELD_CLEARANCE_FAIL
NoEscapeDetail = NO_CANDIDATE_DOMAIN | KEEP_OUT_COLLISION | PAIR_SEP_FAIL |
                 RESERVATION_CONFLICT | VIA_COLLISION | FIELD_CLEARANCE | PN_EDGE_FAIL
PINNED_CONFLICT → raise EscapePinnedConflict（程序错误）
evidence 必带 nearest_obstacle{net,dist,req}（I10，禁静默）
```

## 5. 合成板单测（先行，零 K2 依赖，tests/test_escape_allocator.py）

1. forbidden mask（保锚列不可分 / pinned 写==0 断言）。
2. L1 候选：domain 边界、keepout、错列 <0.36 拒、reservation 闭区间含入（0.36 拒 / 0.37 过）。
3. L2：纸面空净空但场拒（构造电容墙式障碍）→ 不 ASSIGNED；场过 → ASSIGNED。
4. MRV 定序：候选少者先；tie-break 元组逐级；双跑逐字节相等。
5. NO_ESCAPE 两 reason + detail 归并正确落 EscapeTable。
6. 16 行 pinned 输入不得被 allocator 触碰（写 pinned → raise，计数==0）。

## 6. K2 真实板 Gate（tools/p3_v53_phase2_gate.py，前台一次性 ≤2）

验收：
- EscapeTable 输出：DN5/6 out_MCIO = ASSIGNED(pinned 直填)；DN0-7 out_MCIO 全 ∈ {ASSIGNED,
  NO_ESCAPE(reason/evidence 齐)}。
- 27 保锚列 + DN5/6 pinned 列 ColumnBook 写操作计数 == 0。
- 无 133.825 类同列 via 新登记（stacked 禁列断言）。
- 已解 16 段字节保集合零变更（git diff segmap HEAD vs new）；alloc/landing checksum==P0。
- 段级真解 ≥17（DN0/1/3 中 ≥+1 加分非硬指标，IRG §7 P2）。
- artifact：m13_v53_p2_audit.json。

## 7. 治理（照 v53 纪律）

- 白名单新增：escape_allocator.py + tests/test_escape_allocator.py + tools/p3_v53_phase2_gate.py
  + p2 audit json + handoff。零改动既有文件（含 P1 三模块）。
- 全前台，零委派，禁 task()/禁 oracle/禁后台。freeze unlock→写→lock 0/0/0。
- 禁暴力迭代：L2 场参数调整 ≤2 次带依据；净空判据一律走 build_hs_field（禁纸面替代）。
- _shared 既有 4 个 mode-only M + .bak 残留勿动勿 stage。
