# M13 v53 承接 — Phase 0/1 完成：零行为门 PASS + 加性 schema 三模块 + 26 单测

> 承接 v52（IRG=READY_WITH_CHANGES，R1/R2/R3 修订）。本卡 = v53 Phase 0 + Phase 1
> **纯加性实现**（零生产文件改动）。Phase 2（escape_allocator.py）**本卡禁止实现**。
> 全前台，零委派，冻结区 unlock→写→lock（终态 0/0/0）。

---

## 1. 钉死事实（v53 增量；勿重推勿重探）

| # | 事实 | 依据 |
|---|---|---|
| F20 | **Golden 真实存在**：git HEAD report（tracked，sha `5fb604e7…`，228345B）== 工作树 == e2e 重跑字节一致（input_fp `5113681d…` 三段输入指纹稳定） | P0 preflight + e2e 复跑 |
| F21 | **Phase 0 零行为门全绿**：byte-identical / AllocTable checksum `fab63768…` / LandingTable `4f9f24db…` / SolveResults `cc711d6c…` / 段 tally 18 bases·34 段·16 SOLVED 全不变；CountingModel 复跑结果与 report solve **逐字节一致**（= wrapper 透明自证） | m13_v53_p0_audit.json |
| F22 | **fallback gap 量化**：总 form calls 235（escape_pair 107 / col_stack 49 / layer_swap 31 / layer_swap_v 29 / pad_row_dip 19）；pn_ok col_stack 42384call/42360rej、dip 331744/331740、lswap_v 209/188 → **dip/col_stack 自搜枚举量即 P3 要清零的对象** | P0 audit fallback 段 |
| F23 | **16 SOLVED 段重放全过**：按引擎场语义+shared 注入序重验 seg_ok/via point_ok/pn_min_edge≥0.155/链级间距 = 16/16 PASS | P0 fact_validate |
| F24 | **16 段 = 27 保锚中已解 14 段 + DN5/6 out_MCIO，全部 pinned**；chip 侧判定：`EAST_CHIP_*` corridor → left，`WEST_MCIO_TO_CHIP` → right（DN5/6 out_MCIO chip 在右） | P1 反演 |
| F25 | **REFCLK0/input 为 DIRECT 直连形态**（chip pad 落轨行、无 chip via1）——CCF 装配 15/16 即含此 1 直连，不虚构几何 | P1 audit rows_direct=1 |
| F26 | **反演 16 pinned 全带 provenance**（solve_ref/input_fp/source_path=`stages.solve.results[…].segments[…]/reverse_derived`），DN5/DN6 明确证明几何来自 SOLVED path 非 allocator 重算 | P1 audit dn5_dn6_traceable |
| F27 | **dup-via 断言落实**：CCF chip via 58 坐标逐一 == EscapeTable（≤1e-6）；故意漂移 +0.001/+0.002 → replay FAIL + fact_validate 定位（单测证明，R1 真落实非纸面） | test_construction_fact 漂移用例 |

## 2. 交付物（本卡落盘）

| 文件 | 内容 |
|---|---|
| k2/tools/p3_v53_phase0_audit.py | CountingModel（6 白名单入口 wrapper/counter + pn_ok per-form）+ fact_validate 重放 + fallback 归属（库模块） |
| k2/tools/p3_v53_phase0_gate.py | P0 机器门：preflight/golden→e2e→字节→checksum→透明性→artifact；BASELINE_MISSING/MISMATCH 分支 |
| k2/tools/p3_v53_phase1_gate.py | P1 机器门：空表 byte==P0 + 16 反演 pinned + CCF 装配 + fact_validate/replay/dup-via + checksum==P0 |
| _shared/eda_core/column_book.py | R2 资源模型纯数据层：lattice 0.01/snap/reserved 闭区间 ±0.36/diff-pair 原子/via_positions 独立/ball=immutable obstacle；零候选枚举（test_t10 断言） |
| _shared/eda_core/escape_table.py | EscapeTable：status ASSIGNED\|NO_ESCAPE；reason PAPER_FILTER_EMPTY\|HS_FIELD_CLEARANCE_FAIL + detail 7 类；evidence/provenance(R17)；PINNED_CONFLICT=异常非 status |
| _shared/eda_core/construction_fact.py | CCF materialized view + Assembler（三表+锚，deepcopy 防共享引用）+ fact_validate（dup-via/完备性/conn-vs-chip 不混）+ replay_equals |
| tests/test_{column_book,escape_table,construction_fact}.py | 26 用例全绿（合成 fixture，零 K2 坐标/网名） |
| m13_v53_p0_audit.json / m13_v53_p1_audit.json | 双 gate PASS 证据 |

## 3. 关键语义裁决（v53 落定，Phase 2 直接消费）

- **R1**：EscapeTable=chip-side via 唯一事实源；CCF=materialized view 不存第二份；dup-via 断言已代码化。
- **R2**：ColumnBook 语义 = 0.01 lattice（仅簿记）· reservation=中心±0.36 **闭区间**（整数索引含端点，出界须整步）· 差分对原子一次写/整撤 · via 与列分离（≥0.35+netclear / stacked 禁列）· ball 非 owner。
- **R2 两级净空**：L1 paper 粗筛（domain/keepout/错列≥0.36/reservation）→ L2 `build_hs_field` 逐候选 seg_ok·point_ok·pn_min_edge≥0.155 才 ASSIGNED；**纸面算术永不单独产生 ASSIGNED**。
- **R3 MRV**：候选最少先分；tie-break 固定元组 `(len(cands)↑, chip_pad_x_P↑, base 数字↑, segment 秩 input<out_MCIO<out_J2)`；分配后**全量重算**剩余候选；候选集归零 → 该段 `NO_ESCAPE`（detail RESERVATION_CONFLICT）排除续分，**无 backtrack**。
- 旧 5 类 NO_ESCAPE reason 归并：`NO_CANDIDATE_DOMAIN/KEEP_OUT_COLLISION/PAIR_SEP_FAIL/RESERVATION_CONFLICT → PAPER_FILTER_EMPTY`；`VIA_COLLISION/FIELD_CLEARANCE/PN_EDGE_FAIL → HS_FIELD_CLEARANCE_FAIL`；`PINNED_CONFLICT → raise`。
- 本卡四禁重申：不实现 escape_allocator.py / 不接 fallback / 不改 ModelConfig / 零板级特判入 _shared。

## 4. 治理门（终态实测）

- _shared：仅 6 新文件 untracked；4 个 mode-only M（v52 前 freeze-chmod 残留，content diff=0）+ `.bak_v33_perball` 勿动勿 stage。
- k2：仅 3 tools + 2 audit 新增；`_shared` 子模块指针行既有 dirty 排除。
- 冻结区 lock 终态 **0/0/0**。
- 禁项扫描 OK：无 escape_allocator/hs_route_model/ModelConfig/solver/alloc/landing 任何改动。

## 5. 下一卡（Phase 2 = out_MCIO Local EscapeAllocator，勿本卡续）

范围与验收见 NEW_SESSION_PROMPT_v54.md + m13_v53_p01_spec.md（已落盘同目录）。DN0/1/3 是否 ASSIGNED 不预设（IRG §8 非阻塞条款：NO_ESCAPE 为合法预期）。

## 6. G5 自检

- 消费资产：v52 prompt+IRG+architecture_target+ccf_schema_v1+audit 5 件（R1-R3 裁决真源）；v51 引擎 ce9bb87 现场签名。
- 纪律：零生产代码改动（全新增）；零委派（全前台）；冻结区 unlock→lock 0/0/0；_shared 既有残留勿动。
- 待 commit：_shared 6 新文件 + k2（3 tools + 2 audit + 本 handoff + spec + 下一卡 prompt）双仓。
