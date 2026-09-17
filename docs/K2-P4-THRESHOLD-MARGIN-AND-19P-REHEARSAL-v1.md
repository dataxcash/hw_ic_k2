# K2 · P4 · **阈值裕量表 + 两维判据「启用后」复算**（19 PASS / 0 FAIL）· 证据件 v1 · 2026-09-18

> 缘起：① `density_and_clearance`（J-8 余项）与 `ref_plane_continuity`（V3）在安装件里恒为 `enabled:false`，
> **只差监理定阈值/口径**；② 既有测量 JSON 的 `board_sha16` 钉在**仓库板**上，判据要求「测量板 sha16 == 受审板」
> ⇒ 阈值一旦定下，必须用**最终板 sha 钉住**的测量。本件把五件测量全部钉到复合候选板，并用示例阈值做启用后复算。
> **只做测量与复算；阈值/口径归监理；仓库零写入。**

## 1. 测量钉板（全部 `board_sha16 = 9682dd026f48c04a`）

| 件 | 值（复合候选 `9682dd026f48c04a`） |
|---|---|
| 板框 | `[23, 33, 143, 79] mm` · 59 件 · 687 pad |
| **密度峰值**（件中心分格） | 5mm：`absolute_zero` **5** / `frame_origin` 4 · **10mm：`absolute_zero` 5 / `frame_origin` 7** · 20mm：9 / 13 |
| **三横带占用**（焊盘 AABB 口径，y 三等分） | 带1 `4.775%` · **带2 `7.586%`** · 带3 `2.190%` |
| 异网 pad AABB 最小间隙 | **0.25 mm**（`R41.1 (FB_U2)` ↔ `J12.2 (GND)`） |
| **全板最小铜间距（DRC bracket）** | 实达区间 **`[0.100, 0.105] mm`**（`0.100 ⇒ 0 违规`；`0.105 ⇒ 3`；`0.110 ⇒ 3`；`0.120 ⇒ 9`；`0.150 ⇒ 19`；`0.200 ⇒ 196`）；最紧样本 `I2C1_SCL` ↔ `I2C1_SDA`（F.Cu，0.1000） |
| 孔-孔最小边距 | 1.74 mm（20 孔） |
| 工艺实达 | 线宽 0.16 · 过孔 Ø0.35 / 钻 0.20 / **孔环 0.075（零余量）** · 最小孔钻 0.80 · pad 到边 0.38 |
| **V3**（`PCIE_` 高速段 5 530 段） | **名义口径（zone 轮廓）全长覆盖 `3653/3653`**；按「最大覆盖 ≥ 阈值」计：`≥1.0 ⇒ 3051` · `≥0.99 ⇒ 3071` · `≥0.95 ⇒ 3162` · `≥0.9 ⇒ 3196` · `≥0.5 ⇒ 3249`；平面层 `In1/In3/In4/In6` |

## 2. 两维**启用后**复算（示例阈值；用控制件 `manifest.k2.control-v4.yaml`，非安装件）

树 = 关门预演树（落件板复合候选 + 快照库 27 件 + `fp-lib-table` + SPEC rev-48 + 合规 `k2/pipeline.yaml`）。

```
[OK] ref_plane_continuity: 名义口径(zone 轮廓) 全长覆盖 3653/3653（scope=nominal, min_coverage=1.0）；
     平面层=['In1.Cu','In3.Cu','In4.Cu','In6.Cu']；测量板 sha16=9682dd026f48c04a vs 受审板同 ⇒ 一致
[OK] density_and_clearance: 密度[10mm/absolute_zero] 峰值 5（≤6）· 最小铜间距 0.1（≥0.1）mm ·
     横带占用 0.07586（≤0.1）· 孔环 0.075（≥0.075）· pad 到边 0.38（≥0.3）mm；两测量板 sha16 均 == 受审板
=> PASS（PROVISIONAL：manifest 未经监理签认）   —— 全判据 **19 PASS / 0 FAIL**
```

## 3. ⚠️ 阈值 / 口径的**判据后果**（监理决策要看的裕量）

| 判据项 | 实达 | 示例阈值 | 裕量 | 换口径/加严的后果 |
|---|---|---|---|---|
| 密度峰值（10mm） | `absolute_zero` **5** / `frame_origin` **7** | `max_fp_per_cell: 6` | +1 / **−1** | **选 `frame_origin` + 上限 6 ⇒ FAIL（7>6）**；口径必须先定（S-6a） |
| 三横带占用 | 焊盘口径 max **7.586%** | `max_band_occupancy_ratio: 0.10` | +2.4 pt | 若改 **courtyard 口径**（inc41：本板中带 **27.84%**）⇒ 上限 0.10 必 FAIL、0.30 才过 ⇒ 口径与阈值不可分离 |
| 最小铜间距 | `[0.100, 0.105]` | `min_copper_clearance_mm: 0.10` | **≈0（阈值处 0 违规）** | 阈值 **0.105 ⇒ 3 违规**、0.12 ⇒ 9、0.15 ⇒ 19 ⇒ 上限只能取 ≤0.100 |
| 孔环 | **0.075** | `min_via_annular_mm: 0.075` | **0（零余量）** | 加严到 0.08 ⇒ FAIL（工艺实达零余量，属板/工艺既有事实） |
| pad 到边 | 0.38 | `min_pad_to_edge_mm: 0.30` | +0.08 | — |
| V3 | 名义 **3653/3653**；严格（含反焊盘空洞）按 `≥1.0` 仅 **3051/3653 = 83.5%** | `scope: nominal, min_coverage: 1.0` | 0（恰好满覆盖） | **strict 口径 + `min_coverage: 1.0` 不可同时成立**（83.5%<1.0）；strict 需阈值 ≤0.835 才过 |

## 4. 复跑链（确定性；`/tmp` 易失须重建）

```bash
cd /home/fila/jqdDev_2025/ic_hw
K=AppDir/usr/bin/python3.11; CLI=AppDir/bin/kicad-cli
C=/tmp/opencode/p4final/b7/k2_v4_8L.l5.l2-placed.libsnap.kicad_pcb   # 复合候选（inc40）
P=k2/hw/k2_v4_8L.l5.kicad_pro; D=/tmp/opencode/p4final/meas
$K k2/docs/drafts/p4-j8-density-clearance-v1/measure_density_and_clearance.py --board $C --json $D/dc.json
$K k2/docs/drafts/p4-j8-density-clearance-v1/measure_min_clearance_drc.py --board $C --pro $P \
      --kicad-cli $CLI --work-dir $D/clr --json $D/mc.json
$K k2/docs/drafts/p4-j8-v3-measurement-v1/measure_ref_plane_continuity.py --board $C --json $D/v3.json
$K k2/docs/drafts/p4-j8-v3-measurement-v1/measure_pads_within_outline.py --board $C --json $D/pads.json
$K k2/docs/drafts/p4-j7b-w8-pose-normalized-v1/w8_audit.draft-v2.py --board $C --proj-lib /tmp/opencode/p4final/b7/lib \
      --out-json $D/w8v2.json --out-md $D/w8v2.md
# 启用后复算（控制件 + 预演树，--root 指向预演树见 inc42 §3）
```

## 5. 边界

仓库板/pro/库/`fp-lib-table`/`pm_gate/**`/`criteria/` 两份/`_shared/**`/SPEC 原件/`k2/pipeline.yaml`（未创建）**均未动**；
测量副本仅 `/tmp`；未派 WORKER。控制件 `manifest.k2.control-v4.yaml` 为**正负控/示例**用途，**非政策提案、非安装件**。

—— ENG（ARCHER）· 2026-09-18 · 19P/0F（PROVISIONAL）· 板 `9682dd026f48c04a`
