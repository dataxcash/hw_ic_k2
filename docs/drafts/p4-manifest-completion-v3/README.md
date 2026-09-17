# k2/docs/drafts/p4-manifest-completion-v3/ —— P4 判据缺口补齐草案 **v3**（ENG 草案件）

> 状态：**未安装、未签认**（`not_countersigned: true`）。`criteria/`（0444, owner=ic_hw_gate）逐字节未动。
> 依据：计划 §P4「平面落图前置（平面层 Gerber `G36 > 0`）」+ 监理 `#K2-20 §二`（ENG 起草 → 监理正负控复验 → 版本 bump 安装 → 签认）。
> 证据与复跑命令见：`k2/docs/K2-P4-PRECHECK-AND-MANIFEST-V3-DRAFT-v1.md`。

## 件清单（sha256/16）

| 件 | sha256(16) | 与 v2 的关系 |
|---|---|---|
| `manifest.k2.draft-v3.yaml` | `1d4a6b4585fcdedc` | v2 + `gerber_plane_g36` 项 + `gerber_plane_layers: [In1.Cu, In3.Cu, In6.Cu, In4.Cu]` |
| `adjudicate.draft-v3.py` | `e6c2489a87890046` | v2 + 修 `measure_gerber_planes` 扩展名 + 新增 `gerber_plane_g36` 判定块 |
| `make_negatives_v3.py` | `1c46bd1bd58f5bb5` | 与 v2 **逐字节相同**（未改；负控造件沿用 v2 的 m1..m8） |

## 修订（v3 · 2026-09-18）—— **平面落图前置转写**（`gerber_plane_g36`）

**修的缺陷（本件新增量，v2 仍在）**：

1. `measure_gerber_planes` 只 `glob('*.gbr')`，而 KiCad 实际扩展名 = `.gtl/.gbl/.g1..gN`
   ⇒ 实测对 `k2_v4_8L.l5` 的 8 铜层目录**命中 0 个文件**（返回 `[]`）；
2. 该测量在 v2 中**未被任何 check 消费**（死测量）⇒ 计划 §P4 的「平面落图前置」**不可判**。

**v3 实现**：

- 扩展名集合 = `{.gtl,.gbl,.gbr} ∪ {.g1..g32}`；由文件名派生层名（`…-In1_Cu.g1` → `In1.Cu`）。
- 判定：`manifest.gerber_plane_layers` 每层 → 对应 Gerber 文件**存在且 `G36 > 0`**；**缺 `--gerber-dir` ⇒ fail-closed**。
- 层集合 = 计划 §P4 原文转写（`In1/In3/In6 的 GND、In4 的电源`）；**未新增判据维度**，阈值/口径归监理。

**实测（正/负控，当前板 `37019705ef994ccc`）**：

| 控制 | 结果 |
|---|---|
| 正控（真 Gerber 目录） | **PASS 14 / FAIL 5**；`In1=1 · In3=1 · In6=1 · In4=8`；FAIL 集合与 v2 逐项相同（无回归） |
| 负控 A（不给 `--gerber-dir`） | FAIL 6 · `未提供 --gerber-dir（fail-closed）` |
| 负控 B（目录缺 4 个平面文件） | FAIL 6 · 具名缺件 |
| 负控 C（文件在但 `G36=0`） | FAIL 6 · `G36=0 ['In1.Cu']` |
