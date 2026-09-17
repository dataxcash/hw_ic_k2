# K2 · P4 · 判据覆盖率闸 + W-8 选项(甲′) 落件包（ENG 交件，待监理）

| 项 | 值 |
|---|---|
| 阶段 | **P4**（计划 §②）。**未越阶段**：未下单、未出交付 Gerber |
| 依据 | 已批准《K2 整体整改计划》§P4（完工判据 = 全 J 类 + V1/V2/V3 绿 **且 判据集 == manifest 应然集** + 三前置）+ #K2-20 §二（ENG 起草 → 监理复验 → 版本 bump 安装 → 签认） |
| 板态 | `k2/hw/k2_v4_8L.l5.kicad_pcb` = `37019705ef994ccc`（**未改**）· pro = `f68a5fb2f82bd02d`（**未改**） |
| 件 | `k2/tools/k2_p4_gate_coverage_v1.py` `9898781cd1fb9764` · `k2/tools/k2_p4_w8_option_a_install_v1.py` `d18dd19ea3595b55`（**dry-run 默认**） |

## 1. 判据覆盖率闸：「判据集 == manifest 应然集」= **缺失 0 / 越界 0**

应然集来源：登记册 §C（J-1..J-10，冻结维度）+ 计划 §3.3（V1..V3 可机判）+ 计划 §P4（三前置）。转写映射（**映射本身归监理确认**）：

| 权威判据 | → v3 manifest check | 现板 | (甲′) 预览 |
|---|---|---|---|
| J-1 DRC error=0（warning 逐条处置） | `drc_errors` + `drc_warning_disposition` | OK/**FAIL** | OK/**OK** |
| J-2 连通=0（补铜后） | `unconnected_zero` | OK | OK |
| J-3 铺铜全填充 | `zone_filled` | OK | OK |
| J-4 丝印检查全开且 0 违规 | `rule_severity_manifest` + `drc_warning_disposition` | **FAIL**/FAIL | **FAIL**/OK |
| J-5 非 45° = 0 | `non45_segments` | OK | OK |
| J-6 板↔图一致（refdes/封装/pad 集） | `refdes_sets_equal` + `pin_map_complete` | OK/OK | OK/OK |
| J-7 封装=库 且 fp-lib-table 存在 | `lib_footprint_electrical` + `fp_lib_table_present` | **FAIL**/OK | **OK**/OK |
| J-8a 每器件 pad ≥1 | `device_has_pads` | OK | OK |
| J-8b 器件不重叠 | （经 DRC `courtyards_overlap`=error 现 0 条，由 `drc_errors` 覆盖） | OK | OK |
| J-8c 出框 = 0（P3-4） | `board_frame_and_keepout` | OK | OK |
| J-8d 回避区/密度/关键间距 | `board_frame_and_keepout` + `density_and_spacing` | OK/**FAIL** | OK/**FAIL** |
| J-8e 固定孔/钻孔（NPTH≥4、PTH≥插件引脚数） | `drill_count` | OK | OK |
| J-9 pipeline.yaml 存在且 ④段全机判 | `pipeline_present` | **FAIL** | **FAIL** |
| J-10 完工定义可复现 | `verdict_schema` | OK | OK |
| V1 网表闭合（每条声明网有实现 + 全量 unconnected=0） | `net_declared_realized` + `unconnected_zero` | OK/OK | OK/OK |
| V2 引脚映射（每 (ref,pin) 有焊盘；pad 数==符号引脚数） | `pin_map_complete` | OK | OK |
| V3 参考连续性（逐段投影 0.2mm） | `v3_reference_continuity` | OK（0/3653） | OK |
| §P4-1 铺铜前置 | `zone_filled` | OK（10/10 可填充） | OK |
| §P4-2 钻孔前置 | `drill_count` | OK（NPTH 4 / PTH 16） | OK |
| §P4-3 平面落图前置（平面层 Gerber G36>0） | `gerber_plane_g36` | OK（In1/In3/In6=1 · In4=8） | OK |

**覆盖结论（机判）**：应然 check id（去重）**19** = manifest v3 check id **19**；**缺失 = []、越界 = []**。
判定态：现板 **PASS 14 / FAIL 5**；选项(甲′) 预览 **PASS 16 / FAIL 3**。

## 2. W-8 选项(甲′) 落件包（`k2_p4_w8_option_a_install_v1.py`，dry-run 默认）

**三件事，均为文本/元数据改动 + 新库件（不动 pad、不动铜）**：
1. 由**板自身**生成项目 land pattern 库：按 `FootprintNeedsUpdate` **等价内容**分组
   （pad 几何/层集合/pad attr/图形项/封装层/**自转**），每组一条目（Reference→`REF**`；去 pad `(net …)`、归一 uuid/tstamp/锚点 x,y）。
2. 改 **59 处链接名**：`(footprint "<原链接>")` → `(footprint "ForgeOS:<组名>")`。
3. **35 件 `attr=0`** 补 `(attr smd|through_hole)`（元数据；KiCad 库装载无法产出 0，见隔离件 §4）。
另出 `fp-lib-table`（ForgeOS → `${KIPRJMOD}/boardlib.pretty`）。

**实测（`/tmp/opencode/oa_run1`，非交付）**：

| 指标 | 值 |
|---|---|
| 封装数 → 等价组数 | 59 → **25 条库条目**（F.Cu 54 / B.Cu 5 件） |
| 板文本改动 | 59 个链接头 + 35 行 `(attr …)`；**pro 逐字节未变**（`f68a5fb2f82bd02d`） |
| 铜 | **逐字节相同**：`segment`(4705)`f08fe520c4a45147` · `via`(715)`31add10a8a63668f` · `zone`(18)`88a9e2d13090adf8` · `gr_line`(4)`e9ae8ed80f9c45b6`；59 封装块剥除「链接头+attr 行」后逐字节相同 |
| DRC（T-8 同目录 pro+table） | **0 违规 / 未连接 0 / parity 0**（现板：35 条 `lib_footprint_mismatch`） |
| 草案 v3 判定（`link_policy=require`） | **PASS 16 / FAIL 3**；`drc_warning_disposition` 0/0 · `lib_footprint_electrical` **0/59 差异、0 不可判**（现板：33/35 差异 + 24 不可判） |
| 幂等 | 连跑两次：条目集相同、板 sha 同 = `9c6bfc24cd40fed0`（本器只清自己的 `K2_*.kicad_mod`） |

**(甲′) 的固有性质（请监理知悉）**：条目是 **(pattern × 面 × 自转) 特定的 parity 快照**，不是「标准库」形态
—— 因 `FootprintNeedsUpdate` 比较封装层/自转/pad 层集合。实证：`C85`(0402, rot 180) 与同 pattern 的 rot 0 件混组时
产生 **1 条残留 mismatch**；分组键保留自转后归零。条目名形如 `K2_C_0402_1005Metric_FCu_v2`、`K2_PinHeader_1x02_BCu_v19`。
**(甲′) 会把生成器简化 land（SOIC-8 体下 pad、0603 趾外伸 −0.05mm）固化为「权威」** —— 可焊性风险见
`k2/docs/K2-P4-W8-J7-TRIGGER-ISOLATION-v1.md` §7；(乙) 才消除该风险。**ENG 不择一。**

## 3. 剩余 FAIL 归属（全部在监理，无 ENG 可动项）
| FAIL | 关闭条件 | 归属 |
|---|---|---|
| `rule_severity_manifest` | W-7 九条逐条批（4 条零成本可即批即装；另 5 条含丝印 64 项须施工或具名豁免） | 监理 |
| `pipeline_present` | W-9：安装 `k2/pipeline.yaml`（草案在库 `k2/docs/drafts/j9-wiring-option-a/pipeline.k2.draft.yaml`）+ 真源 bump | 监理 |
| `density_and_spacing` | J-8 密度/关键间距阈值（现 `null` ⇒ fail-closed） | 监理 |
> 注：这两项**不额外引入新裁定**，其关闭路径由已待裁的 W-8 口径决定：`drc_warning_disposition` 随落件后 warning 归零而自然绿
> （若监理对 35 条 warning 另有「具名豁免」处置，则由台账关闭）；`lib_footprint_electrical` 随 (甲′) 落件而绿，
> 若选 (乙) 则须先改写 33 件 pad 并重解受影响的走线（铜级联），须另立增量。

## 4. 落件步骤（**获批后**才执行；本件未安装）
```bash
# ① 备份 + T-22（src pro 字节备份 + 同名 pro 配对 + 落板后 dst pro 逐字节校验）
# ② 生成（先 dry-run 到 /tmp 复核，再 --apply 指向仓库）
AppDir/usr/bin/python3.11 k2/tools/k2_p4_w8_option_a_install_v1.py --apply \
    --board k2/hw/k2_v4_8L.l5.kicad_pcb --pro k2/hw/k2_v4_8L.l5.kicad_pro \
    --out k2/hw/k2_v4_8L.l5.kicad_pcb \
    --pretty-dir k2/hw/lib/ForgeOS.pretty --table k2/hw/fp-lib-table \
    --table-uri '${KIPRJMOD}/lib/ForgeOS.pretty'   # 仓库既有表口径（KIPRJMOD=k2/hw）
# ③ SPEC rev-(N+1) 新文件 + pm_gate/project.yaml bump（既有约定）
# ④ ZONE_FILLER 重填（T-25）+ DRC（T-8）+ 判定器复跑；报 sha
```
**待批的处置决定**：现 `k2/hw/lib/ForgeOS.pretty` 20 件中 6 件被引用；落件后新 25 件 `K2_*` 取代其角色，
旧 20 件是否删除（清库）或保留（历史）**须监理批**（本器不删非自身产物）。

## 5. 复跑（确定性）
```bash
cd /home/fila/jqdDev_2025/ic_hw
python3 k2/tools/k2_p4_gate_coverage_v1.py            # 覆盖率闸（缺 /tmp 判定件时对应列显示 -）
AppDir/usr/bin/python3.11 k2/tools/k2_p4_w8_option_a_install_v1.py --out /tmp/oa/K2ISO.kicad_pcb \
    --pretty-dir /tmp/oa/boardlib.pretty --table /tmp/oa/fp-lib-table   # dry-run，默认不写仓库
```

## 6. 边界
未安装任何判据/库件；板（`37019705ef994ccc`）/ pro（`f68a5fb2f82bd02d`）/ SPEC / 真源 / 生成器 / 冻结件 `d4e81f64…` / `criteria/` **逐字节未动**；
未派 WORKER；未写 `.omo/supervision/**`；**未新增判据维度**（覆盖率映射仅转写已冻 J/V/前置）；Gerber 仅 `/tmp` 测量，未打包/未交付/未下单。

—— ENG（ARCHER）· 2026-09-18
