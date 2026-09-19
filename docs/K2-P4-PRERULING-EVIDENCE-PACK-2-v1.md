# K2 · P4 · **裁定前纯证据包 #2**（#1 `R` 钉值 · #3 `M-14` fail-OPEN + 消费者 · #6-⑦/#11 `lib_id` 重指）· v1 · 2026-09-19

> 授权：handoff `k2-p4-handoff-20260920-inc114-context-handoff.md` **§7-3「裁定前可做的纯证据项」**（重跑既有仪器复算 · 补消费者盘点 · 新增待裁定项取证）。
> **未改任何载体**（生成器/SPEC/原理图/板/库/判据/`criteria/**` 均不动）；演算在 `/tmp/opencode/arc_r2/` 与 `/tmp/opencode/inc114/`。
> ENG（ARCHER）· 2026-09-19 · 判据锚 rev=2 · 受审板 `l6 30fa849641323f98`

---

## 0. 一句话

- **#1（`ref_plane_continuity` 判别半径 `R`）**：R 网格扫描实测 **闭锁点 `R* ∈ (0.35, 0.40]`**（`R=0.35 ⇒ 20.8445 mm² FAIL`；`R=0.40 ⇒ 0.0063`≈仅固定孔 keepout；`R≥0.5 ⇒ 0.000000 PASS`）；**钉 `R=0.5` 有 ≥0.1mm 余量且非任意**（腔尺度 = 反焊盘环 ~0.7–0.8mm，`max_contiguous_gap` 最大 **0.611mm**）；负控冻结板 `l4` 在 **R=0.25/0.5/1.0 全 FAIL（798.17 mm²）** ⇒ **非缩口径**。
- **#3（`M-14` 无判据类）**：**fail-OPEN 复现**——坏指针时 `red_team.R13` 静默返回 **`[]`**（无 finding = 「通过」），且 `check_qa.PCB_PATH` 基址 = **模块相对 `_shared/`**（非项目根）⇒ 同一板在两种工作目录下可给出两种结论。**消费者盘点 = 6 处**（逐处具名）。修法 = 钉「基址 = 项目根」+ 既有消费者加 fail-closed 断言（**非新增齿**）。
- **#6-⑦ / #11（`lib_id` 重指）**：54 placed ref 中 **52 解析 / 仅 `J3`·`J4` 未解析**；根因 = YAML 符号 `MCIO_4i.footprint = ForgeOS:MCIO_4i_SFF-1016_RASide`（**无 `__N`**）而库/refmap/板实作为 `…_RASide__1`（J3）/`__2`（J4）；**真源符号层修不可行**（J3/J4 共用一个符号）⇒ ⑦ = **`k2_p3_drawings_v1.py` 1 处**：以**板侧 as-built FPID**（该器已采集，`anchors()` 里现成）为解析源、YAML 串降为交叉核对；**无真源改动**。

---

## 1. #1 `ref_plane_continuity` 判别半径 `R` —— 既有仪器 R 网格复算

仪器：`k2/docs/drafts/p4-refplane-nonantipad-v1/measure_non_antipad_gap.py`（只读；/tmp 副本仅把 `R_SENS` 扩为 6 点，**其余逐字节同**）。

**复现核对**（canonical 三点）：`R=0.25 ⇒ 20.890482`（在册 `20.89048155152594` ✓）· `R=0.5 ⇒ 0.0` ✓ · `R=1.0 ⇒ 0.0` ✓。

| `R` (mm) | `non_antipad_gap` (mm²，`l6`) | 判 |
|---|---|---|
| 0.25 | 20.890482 | FAIL |
| 0.30 | 20.869360 | FAIL |
| 0.35 | 20.844535 | FAIL |
| **0.40** | **0.006330** | ≈PASS（余量 = 固定孔 keepout `0.0062`） |
| 0.50 | **0.000000** | **PASS** |
| 1.00 | 0.000000 | PASS |

- **闭锁点 `R* ∈ (0.35, 0.40]`**（R≥0.40 即闭）⇒ 钉 **R=0.5** 留 **≥0.10mm** 余量；`R=0.25`（= 在册 FAIL 点）**恰在闭锁点之下**。
- **物理一致**：`max_contiguous_gap_mm`：缺口段 n=**619**，p50 0.0938 · p90/p95 0.3755 · **max 0.611**（mm）⇒ 最大腔横向 ≈0.61mm，与「0.3mm 过孔 + 两侧 clearance ≈0.7mm 反焊盘环」同尺度；`2R=0.8mm > 0.611mm` ⇒ R=0.4 起可闭合。
- **成因归属（R=0.5）**：`antipad 20.9552 / split_or_cutout 0.0 / hole_keepout 0.0062 / board_outside 0.0`（`A_gap 20.9552`，守恒 Δ=0）⇒ **缺口 100% 归反焊盘**，**零平面分割/整片开孔**。
- **负控（冻结板 `l4 d4e81f64`）**：R=0.25/0.5/1.0 **恒 798.17 mm² FAIL**（attribution：split_or_cutout 798.1724）⇒ 判据对「未铺铜/平面退缩」**不放行**（**非缩口径**，C-12 合规）。
- ⇒ 供 #1 一句话裁定：**① 钉 `R=0.5`**（本件给依据）／② 成因派生定义（ENG 实现须授权；本件实测「反焊盘占 100%」说明两法应收敛）。

---

## 2. #3 `M-14`「无判据类」—— fail-OPEN 复现 + 消费者盘点

### 2.1 复现（两臂，同一探针）
| 臂 | `PM_GATE_PROJECT_ROOT` | `board_path` 可解析 | `red_team.R13` 返回值 | `check_qa.PCB_PATH` |
|---|---|---|---|---|
| A（**坏指针**） | `/tmp/opencode/inc114/m14root`（`k2_v4.kicad_pcb` 不存在） | **否** | **`[]`（静默「无 finding」= fail-OPEN）** | `<cwd>/_shared/k2_v4.kicad_pcb`（不存在） |
| B（正确根） | `…/ic_hw/k2` | 是 | `[]` | `<cwd>/_shared/k2_v4.kicad_pcb`（不存在） |

- **fail-OPEN 判据**：指针坏 ⇒ 应 **fail-closed 报错**，实测 **零 finding**（「缺路径判据」= 闭环表 §15.3 `M-14` 的未闭点）。
- **基址缺陷**：`check_qa.py:22-23` 的 `PCB_PATH = dirname(dirname(__file__))/<board_path>` 是**模块相对**（`_shared/`），与 `PM_GATE_PROJECT_ROOT` **无关** ⇒ 同一板可因 cwd/import 面不同给出两种结论（两臂均指向不存在的 `_shared/k2_v4.kicad_pcb`）。

### 2.2 消费者盘点（6 处，逐处具名）
| # | 位置 | 用法 | 现状 |
|---|---|---|---|
| 1 | `_shared/pm_gate/config.py:82` | `board_path(project)` 产出 | 生产侧（相对路径） |
| 2 | `_shared/pm_gate/red_team.py:346` | R13 板守卫 | **坏指针 ⇒ `[]`（fail-OPEN）** |
| 3 | `_shared/pm_gate/red_team.py:395` | 另一规则同源取板 | 同上 |
| 4 | `_shared/pm_gate/check_qa.py:22-23`(+`:117`) | `PCB_PATH` 恒基址 | **基址 = 模块相对（错）** |
| 5 | `_shared/pm_gate/falsify_service.py:290` | `join(pcb_root, board_path)` | **显式根（正例，可作范式）** |
| 6 | `_shared/pm_gate/cli.py:367`·`:530` | CLI 覆写/默认 | 需随口径统一 |

⇒ 建议口径（**非新增齿**）：把**基址钉死 = 项目根**（`PM_GATE_PROJECT_ROOT` / 探测根），既有 6 处消费者各加**一条 fail-closed 断言**（目标不存在 ⇒ 报错，禁静默 `[]`）；`falsify_service.py:290` 已符合，可直接对齐。

---

## 3. #6-⑦ / #11 —— `lib_id` 重指面盘点（P3 图集重发的前置）

扫描法：YAML `sheets[].placements`（54 placed ref）× 符号 `footprint` 串 → 按 `k2_p3_drawings_v1.py::footprint_pads()` **同序**候选（`k2/hw/lib/<lib>.pretty>` + `AppDir/share/kicad/footprints/<lib>.pretty>`）解析。

| 量 | 值 |
|---|---|
| placed ref 总数 | **54** |
| 可解析 | **52** |
| **不可解析** | **2 —— `J3` · `J4`（仅此二件）** |
| `J3` 解析目标（板 as-built `lib_id`） | `ForgeOS:MCIO_4i_SFF-1016_RASide__1` |
| `J4` 解析目标 | `ForgeOS:MCIO_4i_SFF-1016_RASide__2` |
| YAML 符号 `MCIO_4i.footprint` | `ForgeOS:MCIO_4i_SFF-1016_RASide`（**缺 `__N`**） |
| 库快照实际件 | `MCIO_4i_SFF-1016_RASide__1.kicad_mod` · `__2.kicad_mod` |
| refmap `ref_to_mod` | `J3→…__1` · `J4→…__2`（**已有正确映射**） |

- **真源符号层修不可行**：`J3`/`J4` 共用符号 `MCIO_4i` ⇒ 单值 `footprint` 无法同时表达 `__1`/`__2`（除非新增**逐 placement 覆写**字段 = 真源 schema 改动）。
- **⑦ 最小修（无真源改动）**：`k2_p3_drawings_v1.py` 已用 `anchors()` 采集板侧 as-built `FPID.GetLibItemName()`（`anch["<ref>"]["footprint"]`）⇒ 令解析**以板侧 as-built 名为准**、YAML 串**降为交叉核对**（不一致即登记，非静默 None）。影响面 = **1 文件**；其余 52 件逐件同值 ⇒ **零行为变化**（可作落件前 diff 断言）。
- 与 #6 的收口联动：#6 选定 (A)/(B) 后，本 ⑦ 方可与**图集重发**（#11）同批落件。

---

## 4. 复现

```bash
# #1 R 网格（/tmp 副本，仅扩 R_SENS）
AppDir/usr/bin/python3.11 /tmp/opencode/arc_r2/measure_r_sweep.py \
  --board hw/k2_v4_8L.l6.kicad_pcb --spec pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-51.json \
  --json /tmp/opencode/arc_r2/sweep_l6.json          # 输出: /tmp/opencode/arc_r2/sweep_l6.json（另 .log）
# #3 fail-OPEN 两臂
PM_GATE_PROJECT_ROOT=/tmp/opencode/inc114/m14root python3 /tmp/opencode/inc114/m14_probe.py
PM_GATE_PROJECT_ROOT=$PWD/k2 python3 /tmp/opencode/inc114/m14_probe.py
# #6-⑦ 解析面盘点：以 placements × symbol.footprint 按 footprint_pads() 同序候选择一
```
读数件：`/tmp/opencode/arc_r2/sweep_l6.json` · `/tmp/opencode/inc114/m14_probe.py` · `/tmp/opencode/inc114/refplane/nonanti_l4.json`（均**易失**，可由上列命令重建）。

---

## 5. 边界

未改生成器/SPEC/原理图/板/库/判据/`criteria/**`/`_shared/**`；**未写 `.omo/supervision/**`**；未派 WORKER；未新增检查齿；未放松下限；未以「接近 0」充绿（`R=0.40` 的 `0.0063` 已具名 = 固定孔 keepout，非归零）；后台等待用 `k2/tools/k2_wait_pid.sh`（#K2-33，实测 **0s 返回**）。临时仅 `/tmp/opencode/arc_r2/`。
