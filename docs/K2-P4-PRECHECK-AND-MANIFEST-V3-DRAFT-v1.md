# K2 · P4 · 阶段内推进：三项「P4 前置」实测 + 转写缺口收口（draft v3）

| 项 | 值 |
|---|---|
| 件 | `k2/docs/K2-P4-PRECHECK-AND-MANIFEST-V3-DRAFT-v1.md`（ENG 交件，**待监理**） |
| 阶段 | **P4**（计划 §②；handoff `k2-p4-handoff-20260918-ctx423k-inc20` §0/§7）。**未越阶段**：未下单、未出交付 Gerber |
| 依据 | 已批准《K2 整体整改计划》§P4 完工判据（三项「前置」）+ #K2-20 §二（转写补齐：ENG 起草 → 监理复验 → 版本 bump 安装 → 签认） |
| 板态 | `k2/hw/k2_v4_8L.l5.kicad_pcb` = `37019705ef994ccc`（**未改**）· pro = `f68a5fb2f82bd02d`（**未改**） |
| 动作性质 | 只读测量 + `/tmp` Gerber 导出（**非交付件**）+ ENG 草案交付；**未安装任何判据**、未改 `criteria/` |

## 1. 三项 P4 前置实测（计划 §P4 原文逐条）

| 前置（计划 §P4 原文） | 实测 | 结论 |
|---|---|---|
| **铺铜前置**：`有 filled_polygon 的 zone 数 == zone 总数` | 板共 **18** 个 zone 节点 = **10 个铜区** + **8 个 F.Cu keepout/rule area**；10/10 铜区均有 `filled_polygon`（计 11 个 polygon，In4 的 12V_IN 区含 2 个） | **板侧满足**；现判定器 `zone_filled 10/18` 是**分母含 keepout** 的实现缺口（见 §2-1） |
| **钻孔前置**：`NPTH ≥ 4` 且 `PTH ≥ 插件件引脚数` | `NPTH = 4`（H1–H4 Ø3.2）· `PTH = 16` · 插件引脚需求 = **16**（H1–H4 各 1 + J6 2 + J9 4 + J11 4 + J12 2 + J13 4，其中 H1–H4 记为 NPTH） | **满足**（NPTH 4≥4；PTH 16≥16） |
| **平面落图前置**：平面层在 Gerber 中 `G36 > 0` | `/tmp` 导出 8 铜层：**In1=1（GND）· In3=1（GND）· In6=1（GND）· In4=8（12V_IN/P3V3_AUX/P3V3/MCU_VDD）**；F.Cu/B.Cu/In2/In5 = 0（非平面层，符合层分配） | **满足**（4 个平面层全 G36 > 0；计划所指「8 层铜全 0」的起点状态已消除） |

铜区清单（10 个，净名实测）：`In1 GND` · `In3 GND` · `In6 GND` · `In4: 12V_IN ×2 / P3V3_AUX ×2 / P3V3 ×2 / MCU_VDD ×1`。

> Gerber 为**测量用途**导出到 `/tmp/opencode/k2p4plane2/`（8 铜层 `.gtl/.gbl/.g1/.g2/.g3/.g4/.g5/.g6`），**未打包、未交付、未下单**（守 §P4「未全绿不下单」）。

## 2. 顺带实测的四项转写/实现事实（供监理 rev 收口）
1. **`zone_filled` 分母含 keepout ⇒ 结构不可达**：8 个 keepout 区**永远不会有 `filled_polygon`**，故 `zones_filled(10) == zones_total(18)` 恒不成立。更正实现（草案 v2 **U4-A 已含**）= `filled_fillable_zones == fillable_zones`（分母 = 非 keepout）。本板该式实测 **10/10 绿**。
2. **`refdes_sets_equal` 板有图无 4 = `H1 H2 H3 H4`**（NPTH 固定孔，计划 §P3 要求其存在，天然无原理图符号；图有板无 = 0）。草案 v2 **U4-C 已含** `board_set - mechanical_refdes`，本件实测与登记 `mechanical_refdes: [H1..H4]` 逐字一致。
3. **`drill_count` 现冻结式弱于计划**：现实现 `npth >= 1`（计划 §P4 = `≥ 4`）。#K2-20 §二.6 已列；**今日 NPTH=4 ⇒ 判定不变**（v2 已按 `drill_npth_min: 4` 补正）。
4. **`measure_gerber_planes` 双重缺陷（本次新发现，v2 仍在）**：
   (a) **glob 错**：只匹配 `*.gbr`，而 KiCad 实际扩展名 = `.gtl/.gbl/.g1..gN` ⇒ 本板命中 **0** 个文件；
   (b) **该测量未被任何 check 消费**（v2 manifest 无 plane 项）⇒ **平面落图前置在原 manifest 下不可判**。
   实测对照：同一目录下 v2 助手返回 `[]`；v3 助手返回 8 层（G36 见 §1）。
5. 附带：8 个 keepout 区**各 ≥1 个开关 ≠ allowed**（`keepout_all_allowed = 0`）⇒ 计划 §P3-5/C5b 口径达标（该口径与 #K2-17 §五 对齐）。

## 3. 交付：ENG 草案 **v3** = v2 + 平面落图前置转写

`k2/docs/drafts/p4-manifest-completion-v3/`

| 文件 | sha256(16) | 与 v2 的关系 |
|---|---|---|
| `adjudicate.draft-v3.py` | `e6c2489a87890046` | v2 + **修 `measure_gerber_planes` 扩展名** + 新增 `gerber_plane_g36` 判定块 |
| `manifest.k2.draft-v3.yaml` | `1d4a6b4585fcdedc` | v2 + `gerber_plane_g36` 项 + `gerber_plane_layers`（转写计划 §P4 原文） |
| `make_negatives_v3.py` | `1c46bd1bd58f5bb5` | 与 v2 **逐字节相同**（未改；负控脚本沿用） |

- **未新增判据维度**：`gerber_plane_g36` = 计划 §P4 已冻「平面落图前置」的转写；层集合取计划原文（`In1/In3/In6 的 GND、In4 的电源`）。阈值/口径（如是否更严、是否纳入 F/B）**归监理**。
- 判定式：`每个 gerber_plane_layers 条目 → 对应 Gerber 文件存在且 G36 > 0`；**缺 `--gerber-dir` ⇒ fail-closed**（不因缺测量而放行）。

### 3.1 正控 / 负控（本会话实测，命令见 §5）

| 控制 | 构造 | 结果 |
|---|---|---|
| **正控 POS** | 真 Gerber 目录（§1） | **PASS 14 / FAIL 5**；`gerber_plane_g36` OK（`In1=1 · In3=1 · In6=1 · In4=8`）；**FAIL 集合与 v2 逐项相同**（`rule_severity_manifest`/`pipeline_present`/`drc_warning_disposition`/`lib_footprint_electrical`/`density_and_spacing`）⇒ **无回归，v3 = v2 + 1 绿** |
| 负控 A | 不给 `--gerber-dir` | FAIL 6；`未提供 --gerber-dir（fail-closed）` |
| 负控 B | 目录内缺 4 个平面文件（只放 F.Cu） | FAIL 6；具名 `缺文件 ['In1.Cu','In3.Cu','In6.Cu','In4.Cu']` |
| 负控 C | 文件在但 **G36=0**（以 F.Cu 冒名 `In1_Cu.g1`，模拟未铺铜） | FAIL 6；`In1.Cu=0 …；G36=0 ['In1.Cu']` |

## 4. P4 门态（据实，不宣称全绿）
- 三项**前置**（计划 §P4）：铺铜 ✅（板侧）· 钻孔 ✅ · 平面落图 ✅（v3 判定式下绿）。
- 冻结判定器（`criteria/adjudicate.py 897e8bfde60e2cfa`）仍 **PASS 6 / FAIL 4**；其中 `zone_filled`（分母缺口，§2-1）与 `refdes_sets_equal`（机械件口径，§2-2）**属实现/口径缺口而非板缺陷**，已由草案 v2/v3 修实现；`rule_severity_manifest`（W-7 九条逐条批）与 `pipeline_present`（W-9 真源 bump）**须监理裁定**。
- 草案 v3 仍 **PASS 14 / FAIL 5**（PROVISIONAL）：余 5 项中 3 项待监理（W-7 处置、W-9、W-8/J-7 政策 + `drc_warning_disposition` 登记）、1 项待阈值（J-8 密度）、1 项 = J-7 电气级（本会话已交成因隔离件 `K2-P4-W8-J7-TRIGGER-ISOLATION-v1.md`）。
- ⇒ **P4 未全绿，仍不下单、不出交付 Gerber**（fail-closed）。

## 5. 复跑（确定性）
```bash
cd /home/fila/jqdDev_2025/ic_hw
# 前置 1/2：铺铜 + 钻孔（stdlib 直读板）
python3 - <<'PY'
import importlib.util
s=importlib.util.spec_from_file_location('a','criteria/adjudicate.py'); a=importlib.util.module_from_spec(s); s.loader.exec_module(a)
b=a.measure_board('k2/hw/k2_v4_8L.l5.kicad_pcb')
print('copper zones filled', b['zones_filled'], 'total nodes', b['zones_total'], 'keepouts', b['zones_total']-b['zones_filled'])
print('NPTH', b['npth'], 'PTH', b['pth'])
print('板有图无', sorted(set(r['ref'] for r in b['_fp_rows'])-set(a.measure_sch_refdes('k2/hw/sch'))))
PY
# 前置 3：平面落图（/tmp 导出，非交付）
AppDir/bin/kicad-cli pcb export gerbers --output /tmp/opencode/k2p4plane2/ \
  --layers "F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,In5.Cu,In6.Cu,B.Cu" k2/hw/k2_v4_8L.l5.kicad_pcb
# v3 草案（正控）
DR=k2/docs/drafts/p4-manifest-completion-v3
python3 $DR/adjudicate.draft-v3.py --project k2 --manifest $DR/manifest.k2.draft-v3.yaml \
  --board k2/hw/k2_v4_8L.l5.kicad_pcb --pro k2/hw/k2_v4_8L.l5.kicad_pro \
  --nets k2/hw/data/k2_sch.errata-1.yaml --sch-dir k2/hw/sch --kicad-cli AppDir/bin/kicad-cli \
  --gerber-dir /tmp/opencode/k2p4plane2 --out /tmp/opencode/v3_POS.json    # 期望 PASS 14 / FAIL 5，plane OK
```

## 6. 边界
未改板（`37019705ef994ccc`）/ pro（`f68a5fb2f82bd02d`）/ SPEC / 真源 / 生成器 / `criteria/`；**未安装** v3（待监理正负控复验 → `ic_hw_gate` 侧版本 bump 安装 → 签认）；未改冻结件 `d4e81f64…`；
未派 WORKER；未写 `.omo/supervision/**`；**未新增判据维度**（仅转写计划 §P4 已冻前置）；临时件仅 `/tmp/opencode/`（Gerber 导出为测量，非交付）。

—— ENG（ARCHER）· 2026-09-18
