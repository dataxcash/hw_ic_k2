# M13 v54 承接 — Phase 2 交付：Local EscapeAllocator（MRV + L1/L2 净空 + EscapeTable 产出）

> 承接 v53（F20-F27 钉死 + m13_v53_p01_spec.md 权威规格）。本卡 = Phase 2
> **纯加性方案层模块**（escape_allocator.py + 合成板单测 + 真板 gate），零生产
> 文件改动，全前台零委派，冻结区 unlock→写→lock（终态 0/0/0）。

---

## 1. 交付物（本卡落盘）

| 文件 | 内容 |
|---|---|
| _shared/eda_core/escape_allocator.py | out_MCIO 芯片侧 Local EscapeAllocator：L1 forbidden mask（保锚∪pinned∪GND/PWR∪reservation）+ level1_candidates（corr_edge+0.5…pad_x−0.3，0.05 步，P 升序/同 P 内 N 升序）+ level2_validate（build_hs_field 三层场逐跳 seg_ok/point_ok + pn_min_edge≥0.155 + 与既有 via_positions 间距，唯一 ASSIGNED 门）+ MRV（候选最少先分，tie-break `(len↑, chip_pad_x_P↑, base 数字↑, seg 秩↑)`，分配后全量重算）+ ColumnBook 原子写 + EscapeTable 产出行（R1/R17） |
| _shared/eda_core/tests/test_escape_allocator.py | spec §5 六组合成板用例 15 绿（零 K2 依赖） |
| k2/tools/p3_v53_phase2_gate.py | 真板 gate：反演 pinned→簿预载→DN0-7 out_MCIO 请求→MRV→验收→m13_v53_p2_audit.json |
| k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v53_p2_audit.json | P2 gate PASS 证据 |

## 2. 钉死事实（v54 增量）

| # | 事实 | 依据 |
|---|---|---|
| F28 | **合成板 15 用例 + 26 绿保 41 passed**：forbidden mask（保锚列不可分/pinned 写 raise+计数 0）/ L1 domain·keepout·错列<0.36 拒·reservation 闭区间（0.36 拒 0.37 过）/ L2 场拒（电容墙 OBS_WALL 走廊横走拒）vs 场过 ASSIGNED / MRV 候选少先 + tie-break 元组 + 双跑逐字节 / NO_ESCAPE 两 reason+detail 归并落表 round-trip / pinned 16 行不可触碰 / ball mask | pytest 41 passed |
| F29 | **真板 gate PASS（2 次几何参数调整内）**：DN5/6 out_MCIO = ASSIGNED(pinned 直填，COL_STACK/PAD_ROW_DIP 保持)；DN0-4/7 out_MCIO 全部 NO_ESCAPE(HS_FIELD_CLEARANCE_FAIL, reason/evidence 齐, detail FIELD_CLEARANCE)；report 字节==P0；alloc/landing checksum==P0；pinned 写计数==0；无 stacked/133.825 同列 via；deterministic 双跑逐字节 | m13_v53_p2_audit.json gate_status=PASS |
| F30 | **DN0 拒因真实**（非形态缺）：col_stack stub @(83.1,52.816) 撞 F.Cu GND pad（dist −0.041）；dip stub 沿 pad 行西探最近 col 亦撞 GND pad（dist 0.051<0.175）——pad 西 F.Cu 行被 GND 球阵物理封死，与引擎自搜 331740/42360 rej 同源；DN7 首败最近障碍 = 已解 DN5 via | P2 audit first_fail 证据 |
| F31 | **L1 ball 掩码语义修正**：±(radius+0.175) 纸面掩码在真球阵密度下合并成 [82.58,94.17] 全禁（虚假 PAPER_EMPTY）→ 纸面 keepout 收窄为球铜半径本身，净空全交 L2 场（F.Cu 场本就含 GND ball pad 障碍）；单测同步 | gate 前后对比 + test_extra_ball |
| F32 | **pinned 预载直写簿**：真实已解列不同 y 行可近 <0.36（UP/DN 交叉区）→ reserve_pair 区间冲突会拒合法 pinned → 预载直建 ColumnReservation 入簿（pinned=True 守卫保留，其后任何 escape 写命中即 raise）；ColumnBook 零改动 | gate 运行 |
| F33 | **_fresh_run 复制球障碍**：deterministic_assert 需簿状态一致（balls+pinned），否则双跑分歧 | gate 修复后确定性 True |

## 3. 关键语义落定（Phase 3 直接消费）

- **列域** = 垫西侧 corr_edge+0.5 … pad_x−0.3（0.05 步 lattice）。候选对 P/N 独立列域，|xN−xP|≥0.36。
- **COL_STACK（列≠pad_x）在西 pad 行几何上物理不可行**（F.Cu stub 横越 pad 行撞邻/GND），dip 沿 pad 行 stub 亦受 GND 球阵封——K2 现状真解仅 DN5 col_stack@pad 列 + DN6 dip（P 下钻列 edge+0.4/N 下钻列 edge，防同列垂腿交叉 = 每极性独立枚举 0.1 步）。
- **NO_ESCAPE = 合法预期**（IRG §8）：本卡 DN0-4/7 均落 HS_FIELD_CLEARANCE_FAIL + evidence(attempted_domain/attempted_pairs/first_fail/nearest)。P3 若解须**改输入**（列域/形态/保锚顺序），非引擎特判。
- 保锚/DN5/6 pinned 列写操作计数 == 0 已代码断言（book.pinned_write_count）。

## 4. 治理门（终态实测）

- _shared：仅新增 escape_allocator.py + test_escape_allocator.py；4 个 mode-only M（content diff=0，v52 前残留）+ .bak_v33_perball 勿动未 stage。
- k2：新增 tools/p3_v53_phase2_gate.py + audit json（+ 本 handoff）；_shared 子模块指针 dirty 排除。
- 冻结区 lock 终态 **0/0/0**。
- 禁改扫描 OK：escape_closure/alloc/landing/P1 三模块/hs_route_model/ModelConfig/SPEC/板文件零改动。

## 5. 下一卡（Phase 3 候选：fallback 关闭，勿本卡续）

- 状态：Phase 2 交付完成；fallback 施工路径（dip pn 331740 / col_stack 42360 自搜枚举清零）尚未关闭（Phase 3 禁项）。
- 前置证据：DN0-4/7 已证 chip 侧列分配无净空（F30）；P3 需先裁决是否放宽输入（列域东扩至 pad 列 col_stack、换芯片/换电源 ball 布局、或接受 NO_ESCAPE 为终态）→ 回到模型层改输入，勿在引擎加特判。
- 承接最小集：本 handoff + m13_v53_p01_spec.md + m13_v53_p2_audit.json + NEW_SESSION_PROMPT（同目录）。

## 6. G5 自检

- 消费资产：v53 spec（Phase 2 唯一权威）+ handoff F20-F27 + P1 三模块 import 复用 + build_hs_field 场 API/_path_pn_min_edge_pt 重放。
- 纪律：全新增零改动既有；全前台零委派；freeze unlock→lock 0/0/0；单测先行（合成板）→ 真板 gate ≤2（几何参数调整 1 次=BALL_KEEP 语义，带依据 F31）；NO_ESCAPE 按语义落 evidence 未硬闯。
- 待 commit：_shared（escape_allocator + test）+ k2（gate + audit + 本 handoff）双仓。
