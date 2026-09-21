# K2 · R342 · **P4 19 维「rev=7 候选」端到端重判** ⇒ **19/19 PASS**（只读 · `criteria/` 未碰）

**件**：`K2_R342_P4_REV7CAND_19DIM_REJUDGE_v1.json`（约定A `974104228f3fae78`）· 测量 `K2_R342_P4_REV7CAND_MEASURE_v1.json`

## 做法（全链真跑）
`adjudicate.main()` + **真 DRC**（`kicad-cli pcb drc --severity-all`）+ 真板解析 + canonical 测量输入；判定器 = `/tmp` 副本（rev=6 + R317-A/B + R340-(B') + R343-(B'')）。`criteria/` **未修改**。

## 读数（同一份测量）
| 判定器 | n_pass | n_fail | passed |
|---|---|---|---|
| 基线 rev=6 | 18 | 1 | False（唯一 FAIL = `lib_electrical_level` · 电气差异 7） |
| **rev=7 候选** | **19** | **0** | **True** |

## 19 维逐项（候选）
- `zone_filled`：铜区（有网非 keepout）已填充 10/10；keepout 规则区 8 个另计（不入分母）
- `device_has_pads`：0 焊盘器件 0: []
- `drill_count`：NPTH=4（应 ≥4）PTH=16
- `non45_segments`：非 45° 段 0/5180
- `rule_severity_manifest`：未登记豁免的 ignore 0/62: []
- `net_declared_realized`：板上 0 焊盘的声明网 = 0；<2 焊盘 = 0
- `pin_map_complete`：网表节点无对应焊盘 = 0
- `refdes_sets_equal`：排除纯机械件 H*（4 条逐条列名: ['H1', 'H2', 'H3', 'H4']）⇒ 原理图 54 / 板 54；图有板无 []，板有图无 []
- `pipeline_present`：scope=k2：含 .kicad_sch 但无 pipeline.yaml 的目录 0 个（fail-closed）: []；范围外（他项目阶段门判）6 个: ['k1/sch', 'key_v2/key_v2/sch
- `drc_errors`：DRC error=0（违规总 170）: []
- `drc_warning_dispositions`：未登记 warning 类型 0/9: []；已登记 ['copper_sliver', 'lib_footprint_mismatch', 'missing_courtyard', 'silk_edge_clearan
- `unconnected_zero`：unconnected_items = 0
- `fp_lib_table_present`：fp-lib-table @ /home/fila/jqdDev_2025/ic_hw/k2/hw: 存在
- `lib_electrical_level`：电气级差异 0（原 7，B 口径豁免 7） + 仅 pad 名差异 0（原 None，非电气无号 F.Paste 豁免 0）（须 0）；B 口径=生效；审计板 sha16=7a5c89913d6e5d0a vs 受审板 
- `keepout_active`：keepout 区 8 个；其中无生效开关（全 allowed / 无 flag）0 个
- `pads_within_outline`：出框：全 pad(AABB)=0 · 接口件(P3-4)=0 · 全 pad(真外框多边形)=0（须全 0）；测量板 sha16=7a5c89913d6e5d0a vs 受审板 7a5c89913d6e5d0a ⇒ 一致
- `ref_plane_continuity`：口径 non_antipad_gap==0 @ R=0.5mm：non_antipad_gap = 0.0 mm²（须 == 0）；归因 antipad=20.9552 / split_or_cutout=0.0 / k
- `density_and_clearance`：密度[10mm/frame_origin] 峰值 7（≤8）· 最小铜间距 0.1（≥0.1）mm · 横带占用 0.07586（≤None）· 孔环 0.075（≥None）· pad 到边 0.38（≥None）mm
- `verdict_schema`：产物中出现 verdict 字段的文件: []

## 边界
只读 · 未烙板 · 未改 `criteria/`/生成器/SPEC/原理图 · 未派 WORKER · 未写 `.omo/supervision/**`。冻结四源 4/4 未动。**本件非门禁 verdict**；门禁 verdict 须 gate 属主落 rev=7 后由 `criteria/` 产出。

---
—— ENG（ARCHER）· 2026-09-22 · owner 闸口 **0**
