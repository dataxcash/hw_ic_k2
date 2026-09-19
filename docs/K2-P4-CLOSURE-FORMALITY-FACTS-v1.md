# K2 · P4 · **关门前置复核 + 三条形式口径事实**（P1/P2/P3 复验 · 判据 `board` 字段陈旧 · 图集锚差 · `engine verify` 口径）· v1 · 2026-09-19

> 授权：handoff §7-3（复算/取证）；**只读**。ENG（ARCHER）· 2026-09-19 · 判据锚 rev=2 `d251bea7` · 受审板 `l6 30fa849641323f98`

## 0. 一句话

阶段门前置**复验为绿**（`engine verify k2` 3/3 PASS · 判据 rev=2 已签认）；同时具名**三条形式事实**（① 判据 `manifest.board` 仍写 `l5` ② 在册 P3 图集锚 `dae8dc8d`(l5) ③ `engine verify` 正确调用口径），供 P4 关门时一并裁决/留痕。

## 1. 阶段门前置复验（本轮实地）

| 项 | 命令/依据 | 结果 |
|---|---|---|
| P2/P3 真源·结构·网表·BOM | `cd k2 && PYTHONPATH=<k2>/_shared:<k2> python3 <k2>/_shared/eda_core/pipeline/engine.py verify k2` | **3/3 PASS**（`project_sch_coverage` / `sch_structural` / `netlist_connect` / `bom_consistent`，rc=0） |
| 提交期门禁 | 每笔提交 pre-commit（同引擎） | **PASS**（本会话 6 笔均过） |
| 判据签认 | `criteria/manifest.k2.yaml::not_countersigned` | **false**（`countersigned_by: 监理(OpenCode) · #K2-29 · 2026-09-18`） |
| 判据集 == 应然集 | 见 `K2-P4-GATE-FAILCLOSED-NEGATIVE-CONTROLS-v1.md` §1 | 19/19 名集全等；17 enabled（15 OK + 2 FAIL）+ 2 待启用 |

## 2. 三条形式口径事实（**均不影响现行判定值，但属 P4 关门形式项**）

1. **判据 `board` 字段陈旧**：`criteria/manifest.k2.yaml::board = k2_v4_8L.l5.kicad_pcb`，而现行受审板 = **`l6`**。
   - **消费面核查**：`criteria/adjudicate.py` **不消费** `manifest['board']`（全文无该引用；verdict 的 `board` 取自 `--board` 实参）⇒ **非判定项、无静默影响**。
   - **形式处置**（供监理）：随 rev=3 一并更新为 `l6`（或具名「以 `--board` 实参为准，`board` 字段仅历史留痕」）。
2. **P3 在册图集锚差**：`k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_drawings.json`（`e284e9af`）`board_sha16 = dae8dc8d48ff5b81`（= **l5**），与现行受审板 `l6 30fa8496` **不同板**；其重发被 **⑦ `lib_id` 重指**阻塞（handoff §6 #11，与 #6 同批）。
   - ⇒ P3「图纸核过」的历史锚为 l5；**l6 图集重发**须与 #6 收口同批（证据包 #3 §2 已把 ⑦ 收敛为 tool 1 处）。
3. **`engine verify` 调用口径（本轮 ENG 踩坑自纠）**：必须 **从 k2 仓库根**、`PYTHONPATH=<k2>/_shared:<k2>` 运行；若从**容器根**用容器 `_shared` 运行，==sch 路径按错误基址解析 ⇒ `FileNotFoundError: <container>/hw/sch/k2_sch.kicad_sch`（**调用口径错，非仓库缺陷**；同一引擎经 pre-commit 每次提交均 PASS，本轮按 hook 口径复跑亦 3/3 PASS）。

## 3. 边界

未改生成器/SPEC/原理图/板/库/判据/`criteria/**`/`_shared/**`；未写 `.omo/supervision/**`；未派 WORKER；未新增检查齿；未放松下限；只读运行 `engine verify` 与 `criteria/adjudicate.py`。
