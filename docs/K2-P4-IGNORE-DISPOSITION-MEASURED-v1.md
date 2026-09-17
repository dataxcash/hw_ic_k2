# K2 · P4 · 9 条 `ignore` 逐条实测处置（施工后实况）· v1 · 2026-09-17

> 目的：把《K2 整体整改计划》§P4 判据 `rule_severity_manifest`（「任何 `ignore` 无台账 → FAIL」）的缺口
> 从 **9 条**收敛到 **1 条**，并给出**可机判**证据。
> 对象 = 五步复合板 `/tmp/opencode/silk-6/silk-fixed.kicad_pcb`（sha256/16 **`6ff49da5678c2108`**）；
> 舞台 `/tmp/opencode/ignore-proof/`（同名 pro + `fp-lib-table` + `lib/`，T-8/T-40）。**未改仓库 pro、未改板、未落件。**

## 1. 逐条实测处置表（对**当前复合板**计数）
| # | 规则 | 源板(探针) | 现计数 | 归零于（证据链） | 处置 |
|---|---|---|---|---|---|
| 1 | `via_dangling` | 12 | **0** | W-7 `12→6` → **PDN 接线增量** `6→0`（`k2_p4_pdn_stitch_v1.py`） | **摘除 ignore** |
| 2 | `track_not_centered_on_via` | 30 | **0** | W-7 `30→11` → **tncv 对齐增量** `11→0`（`k2_p4_tncv_align_v1.py`） | **摘除 ignore** |
| 3 | `silk_over_copper` | 43 | **0** | W-7 silk 组 `43→3` → **③ 字形级修复** `3→0`（`k2_p4_silk_text_fix_v1.py`） | **摘除 ignore** |
| 4 | `silk_overlap` | 21 | **0** | W-7 silk 组 `21→1` → **③ 字形级修复** `1→0` | **摘除 ignore** |
| 5 | `copper_sliver` | 0 | **0** | 源头即 0（W-7 报告 before 亦无此项） | **摘除 ignore** |
| 6 | `footprint_filters_mismatch` | 0 | **0** | 源头即 0 | **摘除 ignore** |
| 7 | `footprint_type_mismatch` | 0 | **0** | 源头即 0 | **摘除 ignore** |
| 8 | `tuning_profile_track_geometries` | 0 | **0** | 源头即 0 | **摘除 ignore** |
| 9 | `missing_courtyard` | 40 | **40（存活）** | **未归零** | **唯一待裁项**（见 §3） |

（源板列对 1–4 取 `/tmp/opencode/reb1/wd1/report.json` 的 `before`；5–8 在该报告中不存在 ⇒ 0；9 全程 40 不变。）

## 2. 可机判实证：8 条已死规则**设为最严 `error`** 仍零违规
把 1–8 号规则 severity 设为**最严 `error`**（若最严仍 0 条 ⇒ 任何 severity 皆 0 ⇒ `ignore` 可摘），
`missing_courtyard` 保持 `warning` 以便计数，其余同仓库 pro：
```bash
D=/tmp/opencode/ignore-proof   # 已建：板 6ff49da5 的同名副本 + pro(8 条→error) + fp-lib-table + lib/
AppDir/bin/kicad-cli pcb drc --format json --severity-all --output $D/drc.json $D/k2_v4_8L.l5.kicad_pcb
```
**实测**（与探针语义基线 `/tmp/opencode/silk-4/verify/drc.json` 对比）：

| 口径 | 违规构成 | 总数 | error 级 | 未连接 |
|---|---|---|---|---|
| 8 条=**error**（最严） | `warning:missing_courtyard` 40 · `warning:lib_footprint_mismatch` 35 | 75 | **0** | 0 |
| 探针语义（9 条=warning） | 同上 | 75 | 0 | 0 |

逐项比较结果：**完全相同**（`ca == cb` True）⇒ 1–8 号规则的 severity 取值对结果**无任何影响**。

## 3. 结论
1. `rule_severity_manifest` 缺口：**9 → 1**。8 条摘除属**零成本、零风险、不改板、不新增检查齿**（owner ②）——它们本就是 0 条。
2. **唯一存活 `missing_courtyard` 40**（与既有 ④ 议题同一）：T-39 已证「与 `courtyards_overlap`=0 联合不可满足（最小 3 对）」。
   出路仍是三条：(a) 接受 ≥3 对 overlap error · (b) placement 重解（L2，可执行）· (c) 具名豁免。**属监理口径。**
3. 缺口的**监理签认范围因此缩到 1 条**（或 0 条：若 ④ 走 (b)/(c) 并登记）。
4. 仓库 `k2/hw/k2_v4_8L.l5.kicad_pro` 的 severity 落改属 ⑤（监理侧登记动作）；本件只在 `/tmp` 出候选 pro 与证据。

## 4. 复跑命令（确定性；全部只读仓库）
```bash
cd /home/fila/jqdDev_2025/ic_hw
D=/tmp/opencode/ignore-proof; mkdir -p $D
cp <五步复合板> $D/k2_v4_8L.l5.kicad_pcb; cp k2/hw/fp-lib-table $D/; ln -sfn $(pwd)/k2/hw/lib $D/lib
python3 - <<'PY'
import json; p=json.load(open('k2/hw/k2_v4_8L.l5.kicad_pro'))
s=p['board']['design_settings']['rule_severities']
for r in ['copper_sliver','footprint_filters_mismatch','footprint_type_mismatch','tuning_profile_track_geometries',
          'silk_over_copper','silk_overlap','track_not_centered_on_via','via_dangling']: s[r]='error'
s['missing_courtyard']='warning'
json.dump(p,open('/tmp/opencode/ignore-proof/k2_v4_8L.l5.kicad_pro','w'),indent=2)
PY
AppDir/bin/kicad-cli pcb drc --format json --severity-all --output $D/drc.json $D/k2_v4_8L.l5.kicad_pcb
# 期望：75 = missing_courtyard 40 + lib 35；error 级 0
```

## 5. 边界
未改仓库 pro/板/SPEC/判据/生成器；未落件；未下单；临时仅 `/tmp/opencode`。
本件**取代** `K2-P4-W7-W8-DISPOSITION-PLAN-v1.md` §「P1（4 条零违规规则 ⇒ 9→5）」的计数口径：施工后已死规则为 **8 条 ⇒ 9→1**。
