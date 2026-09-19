# MANIFEST · E-3 标准调用输入件 —— **受审板换 `l7` 后重锚册**（判据锚 rev=2 在岗 · rev=3 **候选**并行呈报 · #K2-34 §三-2/4）

- 受审板：`k2/hw/k2_v4_8L.l7.kicad_pcb` **`c5a7df90aadb66e0`**（本册测量件 `board_sha16` 须与之相等；不等 ⇒ 判定器 **fail-closed**）
- 配套 pro：`k2/hw/k2_v4_8L.l7.kicad_pro` **`33b4eb6cae8359a9`**（`rule_severities` ignore **0/62**）
- 判据锚（**在岗**）：**rev=2 COUNTERSIGNED** — `criteria/manifest.k2.yaml d251bea7c2cb1873` · `criteria/adjudicate.py 1cda68521d0e56be` · `criteria/CHANGELOG 568d2e93d53f854c`
- 受审板换锚：`l6 30fa849641323f98` → **`l7 c5a7df90aadb66e0`**（链：`k2_gen_v5 bc5dbda2` → `k2_route_segment_v1 f28a4b5a --upto all`；3 跑逐字节同，含撤 `l4`/`l5` 三臂）
- **在岗判据（rev=2）标准调用 verdict**：**15 OK / 2 FAIL**（`passed=False` · `provisional=False`）· FAIL = `drc_warning_dispositions`（7/9 未登记）· `lib_electrical_level`（电气级差异 **2** + 仅 pad 名 **1**）
- **`criteria` rev=3 候选（ENG 草案，影子复算；未安装）** verdict：**19 OK / 0 FAIL** —— `lib_electrical_level` 电气级 **0**（(B) 口径豁免 2）＋ pad 名 **0**（无号 `F.Paste` 豁免 1）；`ref_plane_continuity` `non_antipad_gap = 0.0` @ `R=0.5mm`；`density_and_clearance` 峰 7≤8 · 铜间距 0.1≥0.1 —— 草案 = `k2/docs/drafts/p4-k234-criteria-rev3-v1/`
- **旧册**（`E3-standard-call-l6-20260920/` `l6 30fa8496`；`E3-standard-call-v1/` `l5 dae8dc8d`）**保留**；各册**不可逐数直比**（板 + pro + 判据口径均不同）

| 件 | sha16 | bytes |
|---|---|---|
| `w8_audit_board_l7_c5a7df90.json` | `0551daa3ee912566` | 16,842 |
| `pads_within_outline_board_l7_c5a7df90.json` | `af77f48fa5d0e46e` | 165,139 |
| `ref_plane_continuity_board_l7_c5a7df90.json` | `bbb4534ea0bf8df7` | 1,909,418 |
| `density_board_l7_c5a7df90.json` | `95034499aad26454` | 5,749 |
| `min_clearance_drc_board_l7_c5a7df90.json` | `ee0ca672ad46a87e` | 1,529 |
| `refplane_nonantipad_board_l7_c5a7df90.json` | `cc50ba870089a13b` | 3,077 |
| `drc_violations_clean_workdir.json` | `dec66912493eaf06` | 96,313 |
| `verdict_19dim_board_l7_c5a7df90.json` | `02341510ad28f641` | 2,771 |
| `verdict_19dim_rev3cand_board_l7_c5a7df90.json` | `29835548d965f9e4` | 3,645 |
| `measure_raw_board_l7_c5a7df90.json` | `2573ea49c06e8263` | 2,252,441 |

## 1. 读数（本册）

- **DRC（全新 work-dir）**：违规 **167**（**全 warning**）· `error` **0** · `unconnected` **0**；逐类 = `missing_courtyard` 54 · `silk_over_copper` 37 · `track_not_centered_on_via` 33 · `lib_footprint_mismatch` 20 · `silk_overlap` 15 · `via_dangling` 4 · `silk_edge_clearance` 2 · `track_dangling` 1 · `copper_sliver` 1
  - ⚠ 环境口径（承旧册 §4）：标准调用**须显式给全新 `--drc-work-dir`**（复用旧目录会静默沿用旧库件）。
  - `track_not_centered_on_via` 30→**33**（`l6`→`l7`；µm 精度修复后走线相对过孔微移，属 #K2-34 §一-7 已登记 7 类内，登记制不豁免）。
- **W-8 电气级**：`identical 51 / electrical_diff 2 / pad_name_set_only 1 / no_link 4`（diff refs = `C85 J3 U1`）⇒ 量化类（`L1`/`U6`/`U1` 坐标）**归零**；残余 = (B) 口径三项（详见 rev=3 候选 verdict）。
- **出框**：AABB 0 · 接口件 0 · 真外框多边形 0（676 pad）。
- **ref_plane_continuity（新口径）**：`non_antipad_gap = 0.0` mm² @R=0.5（归因 `antipad 20.9552` / `split_or_cutout 0.0` / `keepout 0.0062`）；**信息项** V3 名义全长覆盖 `3795/3795`；正控（严格全长覆盖段）`n=3176` 且 gap 0。
- **density_and_clearance**：10mm/frame_origin 峰值 **7**（≤8）· 最小铜间距 bracket **[0.10,0.105] ≥ 0.100** · 横带占用 **0.07586** · 孔环 0.075 · pad 到边 0.38。

## 2. `C1` / `C2` / `L-1` 复核（#K2-34 §三-4；本笔零改动）

| 项 | 件 | sha16 | 判 |
|---|---|---|---|
| **C1** | `L3/drawings/p3_placement_solution.json`（rev=2） | **`dfbf65c5b456cdd2`** | 与 #K2-29 登记值**逐字节同**（未动）✅ |
| **C2 / L-1** | `L2/PLACEMENT_SOLUTION_v1.json` | **`086d453d23c5fbff`** | 同上（canonical 捕获、非独立求解；54 = 11 SPEC + 15 L3 + **28 仅板来源**）✅ |

## 3. fail-closed 自检（本册，ENG 实跑）

- 逐件扫 `board_sha16`：与受审板 `l7 c5a7df90aadb66e0` 不等者 = **0**（无）⇒ 判定器陈旧检查可通过。
- `drc_violations_clean_workdir.json` / `verdict_19dim_*.json` 无 `board_sha16` 字段（按设计）。

## 4. 待办（**非 ENG**）

1. **`criteria` rev=3 安装**（gate 属主 + 监理签认 + 锚 rev=3；#K2-34 §三-3）—— 草案 `k2/docs/drafts/p4-k234-criteria-rev3-v1/`（影子复算 19/0）。
2. 安装后：以**在岗 rev=3 判据**重跑标准调用，**替换本册 `verdict_19dim_*.json` 并更新本 MANIFEST**（§三-4 正式重锚）；随后 §三-7 闭环 9 条 + L-1 具名接受（C4）⇒ P4 关门判定。
3. ⚠ **本目录件是测量输入**，不得作为 `--artifacts` 传入（`w8_audit_*.json` 逐条记录含工具侧 `"verdict"` 标签，会被 `verdict_schema` 原文正则误判）。

—— ENG（ARCHER）· 2026-09-19 · 只读取证件（测量件无顶层 `verdict` 字段；C4）· k2 `793cbcf`（前一笔）+ 本册落件笔
