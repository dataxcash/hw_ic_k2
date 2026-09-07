# M14 v39 承接 — 根因修正（channel_alloc 选道被占轨）+ NEW SESSION PROMPT

> 承接 v38。**根因已由 v38 前台实测修正**（详见 `m13_v38_diag_rootcause_viaflip.md`，
> 已 commit 4cef9f2）。本文件 = v39 唯一必读：状态 + 修正方向 + 省 CONTEXT 清单 + PROMPT。
> 纪律：**全前台自跑，禁 task() 委派，禁后台长跑，禁暴力迭代（同参≤2 带依据），
> 禁 chmod 自解，禁无依据 --all-v4**（延续 v38 铁律，NEW SESSION 必须遵守）。

---

## 0. 一句话状态

v38 实测发现 **17/18 失败真根因不是"P/N 极性错配"（v38 早期判定，已证伪），
而是 `channel_alloc` 把高速对分配到 P/N 半轨被低速 pad 占死的轨道**（如 DN2
out_MCIO 分到 track_y=60.70，N 轨 60.89 被 GND/NO_CONNECT pad 0.135 挡死，要求
净空 0.175）。换到同 band 净空轨（58.30/59.50/63.10）当场 SOLVED。
→ 真正修复 = **治理信道分配选道**（验证 P/N 双轨净空），而非改极性/逃逸形态。

### 关键更正（勿再引用 v38 早期 R3"极性错配"）
| 项 | v38 早期(错) | v39 修正(实测) | 证据 |
|---|---|---|---|
| 17/18 失败根因 | P/N 极性错配 | **channel_alloc 分配被占轨** | §2.6，21 个 base-段两半轨被占 |
| 首要修复 | 极性不变式(拓扑层) | **信道分配 D2 净空验证生效** | `_candidate_window_validation` 需注入才生效 |
| 极性/错配 | 主因 | **次生放大**（可作形态加固） | §2.5 pad-锚定条件化无回归 |

---

## 1. 已钉死事实（勿重推）

| # | 事实 | 依据 |
|---|---|---|
| F6 | 权威板 `k2/k2_v4.kicad_pcb` sha `f6273de6`（rot90，只读） | v36 §9 |
| 引擎源 | **容器根** `_shared/eda_core/`（非 k2 内嵌陈旧副本） | reproduce 脚本头注释 |
| G4 容量 | 引擎 `bga_per_ball_escape` 判 FEASIBLE deficits=[] | 复用 v37 结论 |
| 单测基线 | test_hs_route_model 7 failed / 26 passed（既有）；3 文件合计 9 failed | /tmp/opencode/baseline_failed.txt |
| 冻结 | 0/0/0（全锁） | freeze_ctl status |

---

## 2. 省 CONTEXT 清单（NEW SESSION 强烈遵守）

**必读（唯一）**：
- `m13_v38_diag_rootcause_viaflip.md`（§1-§2.6，本次根因修正全证据；§3 方向；§4 下一步）。
- 本文件（承接）+ `m13_v38_plan_polarity_invariant.md`（原计划，**仅作背景参考，Step 目标已失效**）。

**勿读全文**：
- `m13_v10`~`m13_v37` 任一 handoff/记录全文（只读本文件已提炼的事实）。
- v33 系列 /tmp 中间产物（只引用 v37 已提取的 G4 结论）。
- SNLU300/ds320 文本、page-*.png、ds_ball*/ds_lay*、背景 .md。

**勿整读源码，只 grep**：
- `channel_alloc.py` → `_assign_deterministic` / `alloc_channels_from_input` / `_candidate_window_validation`
- `solve_pipeline.py` → `run_alloc` / `_alloc_static_sources` / `_half_pitch`
- `segment_corridor.py` → `corridor_window_ok` / `segment_x_span` / `band_idx_track`
- `hs_route_model.py` → `_escape_pair` / `_layer_swap_escape` / `_layer_swap_escape_v` / `_dip_side` / `_escape_expand` / `solve_all_v4`
- `routing_topology_gate.py` → `_check_pn_polarity` / `plan`

**勿加载 / 勿重跑**：
- 勿加载已回退的临时诊断（`/tmp/opencode/diag_*.py` 已删）。
- 勿重跑 `bga_per_ball_escape`（已判 FEASIBLE）。
- 勿重跑全量 `--all-v4`（只在方案 B 落地 & 单测零回归后第 1 次）。
- **勿新建独立零散脚本**（v38 教训：用户否决）。探针内联 python -c，用后即弃。

---

## 3. 下一步（v39）执行（按优先级，方案 B 优先）

### 方案 B（更上游，优先）：channel_alloc 选道避让被占轨
1. 用**现行 e2e 管道**（`k2/tools/p3_k2_real_board_e2e.py`）重生成 alloc（内部
   `run_alloc` 已注入 `static_sources`+`half_pitch` → D2 应生效）。检查新 alloc
   是否带回 `_track_validation`（看每个 base 是否分配到净空轨）。
2. 若新 alloc 仍含坏轨（如 DN2 仍拿 60.70）→ 说明 D2 退化：查 `_alloc_static_sources`
   是否返回 None（board_path/rules 缺失）或 `_half_pitch` 是否 None（config/
   SPEC impedance 缺 `gap_mm`/`width_mm`）→ `corridor_window_ok` L142 会 return True 放过。
3. 修注入或推导，使 D2 真生效 → 引擎重分配 → 所有 base 分到 P/N 双轨净空的轨道。
4. 单测：新增"分配轨道 P/N 双轨净空"用例（构造被占轨，断言 skip 到净空轨）。

### 方案 A（残余形态加固，若 B 后仍有缺）：极性 pad-锚定条件化
- 仅当 `pad_n` 提供且 |pad_P.y−pad_N.y|<0.2（水平 x 分离）时，`_escape_expand`
  让 P/N 各锚定自身 pad x；否则回退旧居中。**已实测无回归（horiz_sep 条件化）**。
- 单测：新增 pad 位序定向用例。

### 排除（已证伪，勿改）
- 窗口 per-flip 对称化（§1.3 证伪）。
- 无差别 pad 锚定（§2.5 触发 probe/LSWAP 回归）。

---

## 4. 停止判据

- 方案 B 全量第 2 次仍非 18 SOLVED → **立即停**，带"剩余失败 base 的分配轨道
  净空矩阵"（哪些 base 仍分到被占轨 + 哪些净空轨可用）+ 证据回设计层
  （加层/放宽净空/减 lane/换器件），不续命。
- 单测回归失败 → 回查该步，不带依据不重跑全量。

---

## 5. 合规（ECN-009）

unlock（`bash k2/pm_gate/freeze_ctl.sh unlock`）→ 备份 → 改（方案 B 为主）→
单测零新增回归（对比 /tmp/opencode/baseline_failed.txt 9 failed 同集）→ lock →
status 0/0/0 → 归档 ECN-009 裁决。

---

## 6. NEW SESSION PROMPT（可直接粘贴）

---
承接 M14 v39。只读 `k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v39_session_handoff.md`
（唯一必读 = 本文件）+ `m13_v38_diag_rootcause_viaflip.md`（§1-§2.6 根因修正全证据，
已 commit 4cef9f2）。勿读 m13_v10~v37 全文、勿整读源码（只 grep 本文件 §2 列的符号）。

背景：v38 实测修正极重要——**17/18 失败真根因不是极性错配（早期 R3 已证伪），
而是 channel_alloc 把高速对分配到 P/N 半轨被低速 pad 占死的轨道**。例：DN2
out_MCIO 分到 track_y=60.70，N 轨(60.89)被 GND/NO_CONNECT pad 0.135 挡死(<0.175)；
同 band 净空轨 58.30/59.50/63.10 改分后 LSWAP_v 立即 SOLVED。系统性 21 个
base-段两半轨被占。产出物 = 整体 EDA TOPO ENG（SolvePipeline），K2 是验证项目。

主任务（方案 B 优先）：
1. 用现行 e2e 管道（`k2/tools/p3_k2_real_board_e2e.py`，内含 run_alloc 已注入
   static_sources+half_pitch→D2）重生成 alloc，检查是否带回 `_track_validation`
   且每个 base 分到净空轨。
2. 若仍含坏轨（D2 退化）→ 查 `_alloc_static_sources`（是否 None）与 `_half_pitch`
   （config.channel_alloc.half_pitch / SPEC impedance gap_mm+width_mm）→ 修注入，
   使 `corridor_window_ok` 真验证 P/N 双轨净空（否则 L142 return True 放过）。
3. 引擎重分配 → 18 对分到净空轨。
4. 单测：新增"分配轨道 P/N 双轨净空"用例 + 既有 9 failed 同集零新增回归核对。
5. 全量 ≤2 次（方案 B 落地 & 单测零回归后第 1 次）→ 18 SOLVED + skew<0.15 +
   P/N≥0.175 + 坐标 JSON 落盘。
6. 合规 ECN-009：unlock→备份→改→单测零新增回归→lock→status 0/0/0→归档裁决。

方案 A（残余形态加固，仅当 B 后仍有缺）：`_escape_expand` 在 |pad_P.y−pad_N.y|<0.2
（水平 x 分离）时 P/N 各锚定自身 pad x（已实测无回归，horiz_sep 条件化）。

纪律：**全前台自跑，禁 task() 委派，禁后台长跑，禁暴力迭代（同参≤2 带依据），
禁 chmod，禁无依据 --all-v4**。停止判据：方案 B 全量第 2 次仍非 18 SOLVED → 立即停，
带剩余失败 base 的分配轨道净空矩阵 + 证据回设计层（加层/放宽净空/减 lane/换器件），
不续命。每步原始输出贴出不加工。**不新建独立零散脚本**（探针内联 python -c，用后即弃）。
---

## 7. 本次 v38 产物（已 commit）

- `m13_v38_diag_rootcause_viaflip.md`（根因修正全证据，已 commit 4cef9f2）。
- 本承接文件（v40 时更新）。
- 引擎文件未改动（回退干净，冻结 0/0/0）。
