# M14 v45 承接 — 结论沉淀进知识库（不 commit 非绿态）；C-1 候选 + REFCLK1 跨带协调缺口已入 kb，v46 按档案施工

> 承接 v44。唯一必读 = 本文件 + kb 两条新模板（见 §1）。v43/v44 事实仍有效勿重推。
> **纪律复盘（本 session 教训）**：v45 曾陷入手工"重建 shared→逐 via 消融→再打点"的
> 暴力循环，且**临时重建脚本产出 0 via 却当真解**误导归因 —— 违反"能力进 ENG、禁临时
> 脚本做事"。收尾改为：把结论写进学习档案（kb.sqlite3），修复规格留档待 v46 一次性施工。

---

## 0. 一句话状态

ENG `_shared` **零代码改动**（还原 HEAD + freeze 0/0/0）；知识库 **+2 模板**（学习沉淀，
_shared 784034b 已 commit）。核心实证：C-1（col-stack 尾段载体两轮）段级可解 DN0-3 input
且 DN4 无回归，但**全量 e2e 下 greedy 序把 REFCLK1 挤出**（REFCLK1 孤立可解 = 顺序假象），
且 REFCLK-first 反全灭 —— 需"逃逸 via 清所有 alloc 走廊带净空包络"的**带协调能力**（C-3）
与 C-1 一并施工才可收口。非绿态 → 未 commit，规格在 kb。

---

## 1. 学习档案（v45 落库，v46 施工前必读）

| template_id | 类别 | 内容 |
|---|---|---|
| `chip_col_stack_band_tail_carrier`（新） | bga_fanout | **缺陷**：col-stack F.Cu 水平尾段横穿 U6 东侧去耦电容墙 C79-C83（x90.45-91.55, y58.75-64.25；0402/0603 P3V3/GND）。**修复 C-1**：尾段载体层两轮 = F.Cu（已解 lane 字节不变）→ band_field.layer（走廊层 In2）；col 竖腿仍 In1、col-top F.Cu via 检查保留。**限制**：DN5 pad 列恰在 C82 列位 → col-top via 净空 0.24<0.475 死局（需 ty≥64.54 或列东移，涉 alloc 另卡）。代码候选指向 `HSRouteModel._col_stack_escape tail_layer 两轮` |
| `refclk_band_data_via_coordination`（新） | corridor_pair | **缺口**：REFCLK1（In6 ty50.5，行 50.31/50.69，x 60-133）被先解 lane PCIE_UP7 input 的 chip 列 col-top through-via (93.25,50.73) 挤出（距 N 行 0.04 < via keepout ~0.37）。孤立解 SOLVED；drop 该单 via → 立解（消融实证）。**C-3 协调规格**：逃逸 via 落位须清所有 alloc 声明走廊带（异层但 x-span 重叠）净空包络 `|via.y - band_row| ≥ via_keepout + track_half`，否则 greedy 末位 lane 必被挤出。REFCLK-first 反全灭 → 非换序，需 via 包络预检。**教训**：消融必须基于真 run shared（v45 重建脚本 0-via bug） |

---

## 2. 钉死事实（v45 增量）

| # | 事实 | 依据 |
|---|---|---|
| P1 | C-1 全量 e2e：seg 12→17（+DN0-3 input、+UP2 out_J2、+UP7 全链），**base solved_pairs 2 = REFCLK0+UP7**（UP7 顶替 REFCLK1，非净增） | v45 e2e（C-1 临时落码，已还原） |
| P2 | REFCLK1 回归 = 纯 UP7 input chip 列贡献所致（消融：drop UP7 input → 立解；drop 单 via (93.25,50.73) → 立解）；NEW 码对 REFCLK1 零影响（同 shared 字节级同路径） | v45 逐 via 消融 + NEW/OLD 模块对照 |
| P3 | C-1 只改 `_col_stack_escape`（tail_layer 两轮 + `_side` 层参），未触及 REFCLK 路径形态 | git diff 单文件 |
| P4 | 临时脚本教训：从报告路径重建 shared vias 曾产出 0（bug）→ 旧模块"复现 SOLVED"不可信；凡 shared 依赖的归因一律以真 e2e run 的累积为准 | v45 自证 |

---

## 3. 下一步主线（v46 唯一工作：C-1+C-3 一并施工）

1. **读 kb 两条模板**（`chip_col_stack_band_tail_carrier` / `refclk_band_data_via_coordination`），
   按 structure.fix / structure.coordination_need 施工，勿重新考古。
2. **C-1 落地**：`_col_stack_escape` 加 `tail_layer` 两轮（backup 参照
   `/tmp/opencode/hs_route_model.py.bak_v44`；代码规格见 kb 模板）。
3. **C-3 落地**：逃逸 via 落位预检清 alloc 全走廊带净空包络（数据驱动：alloc/SPEC 全带已知；
   把 REFCLK In6 带行 50.31/50.69 的包络纳入 chip 列 col-top via 检查）→ 目标：C-1 增益 +
   REFCLK0/1 全保 SOLVED。
4. ECN-009 全流程（unlock→备份→改→单测→e2e 净增→lock 0/0/0→commit+push）。
5. 目标：18 bases SOLVED + skew<0.15 + P/N≥0.175 + 坐标 JSON 落盘；可跑单测全绿
   （test_solve_pipeline 1 failed pre-existing 勿修）。

---

## 4. 资产 / 停止态

| 项 | 状态 |
|---|---|
| ENG `_shared` | 零改动（git diff 空）；freeze 0/0/0 已 lock；pre-existing 脏仅 escape_closure_analysis.py/install.sh（勿 commit） |
| knowledge kb | **+2 模板已 commit**（_shared 784034b，待 push） |
| k2 报告/板 | 还原 v43 态（p3 report 备份 /tmp/opencode/report.bak_v44.json）；板 sha f6273de6 |
| 探针 | /tmp/opencode/（probe_refclk1*.py 等，用后即弃，勿再信其归因口径——P4） |

**勿做**：勿单独 commit C-1 后跑 e2e 当绿（P1/P2：REFCLK1 必被挤出）；勿再手写 shared
重建脚本做消融归因（P4）；勿动 capacity/alloc/landing/SPEC 走廊层。
