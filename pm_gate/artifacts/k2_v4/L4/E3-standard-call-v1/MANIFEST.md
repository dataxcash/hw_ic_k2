# MANIFEST · E-3 标准调用输入件（判据锚 rev=2 · #K2-29 §六-2/§六-3）

- 受审板：`k2/hw/k2_v4_8L.l5.kicad_pcb` **`dae8dc8d48ff5b81`**（本 MANIFEST 内全部测量件 `board_sha16` 须与之相等；不等 ⇒ 判定器 fail-closed）
- 判据锚：**rev=2 COUNTERSIGNED** — `criteria/manifest.k2.yaml d251bea7c2cb1873` · `criteria/adjudicate.py 1cda68521d0e56be` · `criteria/CHANGELOG 568d2e93d53f854c`
- 标准调用 verdict：**15 OK / 2 FAIL**（FAIL = `drc_warning_dispositions` · `lib_electrical_level`；同根 = 受审板 `lib_id` 未重指）
- 证据件：`k2/docs/K2-P4-E3-STANDARD-CALL-WIRING-AND-CARRIER-DELTA-v1.md` `e861fd9d8bfce7c7`

| 件 | sha16 | bytes |
|---|---|---|
| `density_board_dae8dc8d.json` | `6b5bc395f434a157` | 5,750 |
| `drc_violations_clean_workdir.json` | `7b96ed94546f5c71` | 34,193 |
| `drc_violations_reused_stale_workdir.json` | `1c19eaeadccc44d4` | 36,245 |
| `min_clearance_drc_board_dae8dc8d.json` | `41eacaf4eb6d194d` | 1,544 |
| `pads_within_outline_board_dae8dc8d.json` | `7e9b637ac142fbc5` | 167,371 |
| `ref_plane_continuity_board_dae8dc8d.json` | `e2863c81d80f9238` | 1,841,970 |
| `verdict_19dim_board_dae8dc8d.json` | `8e12ecff879362b3` | 2,656 |
| `w8_audit_board_dae8dc8d.json` | `365d77cf73935615` | 38,188 |
| `w8_audit_generator_output_d67c0f04.json` | `f1289a2b2c1c07c1` | 21,956 |

- `verdict_19dim_board_dae8dc8d.json`：`passed=False` · `oks=15` · `fails=2`（`provisional=False`）
- ⚠ **DRC 环境口径**（具名坑，见证据件 §4）：`drc_violations_clean_workdir.json`（全新 work-dir）= **69 违规 / 3 类**（courtyard 39 + mismatch 28 + issues 2）；`drc_violations_reused_stale_workdir.json`（复用旧目录，其 `lib/` = 9-14 旧件）= **73 违规 / 2 类**（courtyard 39 + mismatch 34）。**标准调用须显式给全新 `--drc-work-dir`**。

—— ENG（ARCHER）· 2026-09-18 · 只读取证件（无 `verdict` 字段的测量件；C4）

⚠ **本目录件是 `--w8-audit-json` / `--pads-outline-json` / `--v3-plane-json` / `--density-json` / `--min-clearance-json` 的「测量输入」，不得作为 `--artifacts` 传入**：
`w8_audit_*.json` 的逐条记录含 `"verdict"` 字段（工具侧标签），会被 `verdict_schema` 的原文正则误判为「产物声明 verdict」。
