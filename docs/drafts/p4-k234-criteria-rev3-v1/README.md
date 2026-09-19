# `criteria` **rev=3 安装候选**（ENG 起草；**未落件**）· 依据 **#K2-34 §一-1/6/7/9 + §三-3**

> 本目录是 **ENG 起草**的 rev=3 可安装候选 —— 循 rev=2 前例（`criteria/*` ← `docs/drafts/**`）。
> **ENG 只读 `criteria/`、不落件**（#K2-34 §三-3 明文）：安装 = **gate 属主（`ic_hw_gate`）原子覆写 + 监理签认 + 锚 rev=3**。
> 基线 = rev=2（`manifest.k2.yaml d251bea7c2cb1873` · `adjudicate.py 1cda68521d0e56be` · `CHANGELOG 568d2e93d53f854c`）。

## 0. 文件

| 文件 | 由 | 说明 |
|---|---|---|
| `manifest.k2.rev3-draft.yaml` | rev=2 `criteria/manifest.k2.yaml` | 19 维全 `enabled`；+7 登记；`board→l7`；`ref_plane_continuity` 新增 `caliber`/`radius_R_mm`；**`not_countersigned: true`（安装时签认后置 false）** |
| `adjudicate.rev3.py` | rev=2 `criteria/adjudicate.py` | ① 新增 `--refplane-gap-json` + 新口径判定；② `lib_electrical_level` 落 **(B)** 三条具名口径 |

## 1. rev=3 六项（#K2-34 §三-3 逐条对位）

1. **`density_and_clearance` 启用**（#K2-34 §一-9）：`enabled:true`，删 `pending`；阈值承 #K2-23 §二-9（`cell_mm=10`·`cell_origin=frame_origin`·`max_fp_per_cell=8`·`min_copper_clearance_mm=0.100`）。判定器既有机制直接消费。
2. **`ref_plane_continuity` 启用**（#K2-34 §一-1）：口径 = **`non_antipad_gap == 0`**，**判别半径 `R=0.5 mm` 具名写入** `thresholds.ref_plane_continuity.{caliber,radius_R_mm}`；消费者 = `measure_non_antipad_gap.py`（`2f5591352c5974d3`）输出。面积覆盖率降**信息项**。
3. **`drc_warning_dispositions` +7**（#K2-34 §一-7）：`silk_over_copper`·`silk_overlap`·`silk_edge_clearance`·`track_not_centered_on_via`·`via_dangling`·`track_dangling`·`copper_sliver`；**登记制、均不豁免**（90 条保持可见；丝印图形级 P5 出图前处置；布线级归链内路由器/PDN）。
4. **(B) 判据侧具名口径**（#K2-34 §一-6）：`adjudicate.rev3.py::_reclassify_w8()` —— ① 容差 `≤0.0005mm`（表示差异）；② 中心对称 pad（circle/rect/oval/roundrect）`rot` 差 ∈ {0,180} ⇒ 铜形全同（`rel_geom_same≠False`；方形/圆形出现 rot 差**不豁免**）；③ 无号 `F.Paste`（`pad_name_set` ∧ `board_only==[]` ∧ `lib_only` 全 `""`）⇒ 非电气。**records 缺失 ⇒ 退回 summary（fail-closed）**。
5. **`board: k2_v4_8L.l7.kicad_pcb`**（#K2-34 §三-3⑤）。
6. **签认/版本/留痕**：`manifest_version` bump · `countersigned_scope.covered` 19 / `uncovered: []` · `criteria/CHANGELOG` 追加 `rev=3` 条 · **安装后锚 rev=3**（三件新 sha）。

## 2. 证明（`l7`，ENG 侧影子复跑；`criteria/` 未动）

命令（cwd=容器根；`--manifest` 指向本草案，判据器为本目录副本）：
```bash
python3 k2/docs/drafts/p4-k234-criteria-rev3-v1/adjudicate.rev3.py \
  --project k2 --manifest k2/docs/drafts/p4-k234-criteria-rev3-v1/manifest.k2.rev3-draft.yaml \
  --board k2/hw/k2_v4_8L.l7.kicad_pcb --pro k2/hw/k2_v4_8L.l7.kicad_pro \
  --nets k2/hw/data/k2_sch.errata-2.yaml --sch-dir k2/hw/sch --root . \
  --drc-cli AppDir/bin/kicad-cli --drc-work-dir <全新> \
  --w8-audit-json <w8_l7> --pads-outline-json <pads_l7> --v3-plane-json <v3_l7> \
  --refplane-gap-json <nonantipad_l7> --density-json <density_l7> --min-clearance-json <minclr_l7>
```

| 臂 | 布景 | 读数 |
|---|---|---|
| **正控** | rev=2 判据 × `l7` | **15 OK / 2 FAIL**（`drc_warning_dispositions` · `lib_electrical_level` 2+1） |
| **rev=3 候选** | 草案 × `l7` | **19 OK / 0 FAIL**（`lib_electrical_level`：电气级 0（原 2，B 口径豁免 2）+ pad 名 0（原 1，无号 F.Paste 豁免 1）；`ref_plane_continuity`：`non_antipad_gap = 0.0` @R=0.5） |
| **NC-A** | 草案 × **冻结 `l4`** | `ref_plane_continuity` **FAIL** `non_antipad_gap = 798.172376 mm²`（= evidence-pack #2 §1 记录值）⇒ **非缩口径** |
| **NC-B** | 草案 × `l4` 板 + `l7` 的 W-8 证据 | `lib_electrical_level` **FAIL**「证据陈旧，fail-closed」 |
| **NC-C** | 缺 `--refplane-gap-json` | `ref_plane_continuity` **FAIL** fail-closed |
| **NC-D** | `thresholds.density_and_clearance` 缺 | `density_and_clearance` **FAIL**「阈值未定 ⇒ fail-closed」 |

> `--manifest` 允许覆写 ⇒ 本草案可**在不触碰 `criteria/` 的前提下**被任意复算（ENG 侧已复算）。

## 3. 安装程序（gate 属主；原子）

1. 备份 rev=2 三件 → 覆写 `criteria/manifest.k2.yaml` ← 本目录 manifest（**把 `not_countersigned` 置 `false`**、`countersigned_by` 记监理裁定号）、`criteria/adjudicate.py` ← 本目录 `adjudicate.rev3.py`。
2. `criteria/CHANGELOG` 追加 `rev=3` 条（含 6 项 + 前后 sha）。
3. `chown ic_hw_gate` + `chmod 0555/0444`；**重出三件 sha16**；**锚 rev=3**（`criteria/adjudication-ledger.jsonl`）。
4. 安装后 **ENG 复跑 19 维**（§三-4），期望 **0 FAIL**；随后收 §三-7。

## 4. ⚠ 须监理在安装时确认的一处口径张力（具名，非停机级）

- **#K2-34 §一-1**：本维口径 = **`non_antipad_gap == 0`**（`R=0.5`）⇒ 本草案据此实现，消费者 = `measure_non_antipad_gap.py`。
- **#K2-34 §三-4** 括注仍写「参考连续性（**V3 覆盖口径**）」⇒ 该括注系 #K2-32 旧列表口径；本草案按 **§一-1（判定条款）** 实现 V3 覆盖**降为信息项**。
- 实测两者 `l7` **皆 PASS**：`non_antipad_gap = 0.0` **且** V3 名义全长覆盖 **3795/3795**。
- 若监理要求 V3 覆盖**并列为门**（而非信息项）⇒ 请一句话下达，ENG 按 `AND` 合并（属**收紧**，非缩口径）。

## 5. 边界

ENG **起草件**：未写 `criteria/**`、未改 `_shared/**`、未改冻结件、未出 Gerber、未派 WORKER、未新增检查齿（(B) 为裁决口径、`ref_plane_continuity` 为既有维换口径实现）。**唯一落件** = 本草案目录（`k2/docs/drafts/**`）。
