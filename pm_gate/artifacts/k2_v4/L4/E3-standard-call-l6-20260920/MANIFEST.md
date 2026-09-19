# MANIFEST · E-3 标准调用输入件 —— **受审板换 `l6` 后重锚册**（判据锚 rev=2 · #K2-32 §一-5 / #K2-31 §五-2）

- 受审板：`k2/hw/k2_v4_8L.l6.kicad_pcb` **`30fa849641323f98104f`**（本册全部测量件 `board_sha16` 须与之相等；不等 ⇒ 判定器 **fail-closed**）
- 配套 pro：`k2/hw/k2_v4_8L.l6.kicad_pro` **`12ad219b9f66b7b3`**（`rule_severities` ignore **0/62**）
- 判据锚：**rev=2 COUNTERSIGNED** — `criteria/manifest.k2.yaml d251bea7c2cb1873` · `criteria/adjudicate.py 1cda68521d0e56be` · `criteria/CHANGELOG 568d2e93d53f854c`
- 标准调用 verdict：**15 OK / 2 FAIL**（`passed=False` · `provisional=False`）· FAIL = **同前册两类**：`drc_warning_dispositions`（7/9 未登记）· `lib_electrical_level`（电气级差异 **5**）
- **旧册**（`E3-standard-call-v1/`，受审板 `dae8dc8d48ff5b81` + `l5.kicad_pro`）**保留**；两册**不可逐数直比**（板不同 + pro 不同）

| 件 | sha16 | bytes |
|---|---|---|
| `w8_audit_board_l6_30fa8496.json` | `e71ef48e9f18e4af` | 21,950 |
| `w8_audit_seg1_output_d67c0f04.json` | `7118be18ef487bed` | 21,959 |
| `pads_within_outline_board_l6_30fa8496.json` | `1359b320f41ec0b5` | 164,825 |
| `ref_plane_continuity_board_l6_30fa8496.json` | `39b5ae46f818ff89` | 1,909,418 |
| `density_board_l6_30fa8496.json` | `a43fb92626f2e20d` | 5,749 |
| `min_clearance_drc_board_l6_30fa8496.json` | `4c06afcffc66a86e` | 1,615 |
| `drc_violations_clean_workdir.json` | `ad472105c88b2256` | 93,883 |
| `verdict_19dim_board_l6_30fa8496.json` | `67cbe1adc919696c` | 2,771 |
| `measure_raw_board_l6_30fa8496.json` | `c534a2cb2b738a1c` | 2,257,654 |

- `verdict_19dim_board_l6_30fa8496.json`：`passed=False` · `oks=15` · `fails=2`（无顶层 `verdict` 键）
- **DRC（全新 work-dir）读数**：违规 **164**（**全 warning**）· `error` **0** · `unconnected` **0**；逐类 = `missing_courtyard` 54 · `silk_over_copper` 37 · `track_not_centered_on_via` 30 · `lib_footprint_mismatch` 20 · `silk_overlap` 15 · `via_dangling` 4 · `silk_edge_clearance` 2 · `track_dangling` 1 · `copper_sliver` 1
- ⚠ **DRC 环境口径**（具名坑，承旧册 §4）：`criteria/adjudicate.py::measure_drc` 对 `fp-lib-table`/`lib` 仅在「目标不存在」时复制 ⇒ **复用旧 `--drc-work-dir` 会静默沿用旧库件**（同一受审板可给出两种读数）。**标准调用须显式给全新 `--drc-work-dir`**；本册 `drc_violations_clean_workdir.json` 取自全新目录 `/tmp/opencode/inc114/e5/adj_drc_l6b/`。
- ⚠ **本目录件是 `--w8-audit-json` / `--pads-outline-json` / `--v3-plane-json` / `--density-json` / `--min-clearance-json` 的「测量输入」，不得作为 `--artifacts` 传入**：`w8_audit_*.json` 的逐条记录含 `"verdict"` 字段（工具侧标签），会被 `verdict_schema` 的原文正则误判为「产物声明 verdict」。

—— ENG（ARCHER）· 2026-09-19 · 只读取证件（测量件无 `verdict` 字段；C4）· k2 `e241ba5`

## fail-closed 自检（本册，ENG 实跑）

逐件扫描 `board_sha16`：`density` / `min_clearance` / `pads_within_outline` / `ref_plane_continuity` / `w8_audit_board` 全部 = **`30fa849641323f98`**（== 受审板 `l6`）；`w8_audit_seg1_output` = **`d67c0f048f0d0423`**（== 段1 产物，按设计）；`drc_violations_clean_workdir` / `verdict_19dim` 无该字段。⇒ **BAD = 0，本册与受审板同锚**（判定器陈旧检查可通过）。
