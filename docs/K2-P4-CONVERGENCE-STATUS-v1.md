# K2 · P4 收敛增量 1 状态件 v1 —— 交监理核

> **依据**：owner 指令 **#14**（L2 = 叠层/PDN/走廊/**过孔策略**/等长/热机械 = **自裁勿停**）+ 《宪法》第四条（改板须有对应 SPEC 修订）。
> **性质**：ENG 施工报告（**交测量**；判定权归监理）。**P4 未完工**，本件**不宣称任何门通过**。

## 1. **DRC 基线更正（重要）**

| 板 | 命令（同一条） | 违规 | 未连接 |
|---|---|---|---|
| `k2_v4_8L.l4.kicad_pcb`（`d4e81f64`） | `kicad-cli pcb drc --format json --severity-error --severity-warning` | **42** | **364** |
| `k2_v4_8L.l5.kicad_pcb`（**增量 3**，`5c1b0442`） | 同上 | **157** | **236** |
| handoff §6 所载「l5 = 202 / 208」 | — | = **增量 2 板**（`1b8400a2`）之数，**非增量 3** | 同左 |

- l4 与 l5 两数**今日实跑均可复现**（同日连跑逐项一致；`/tmp/opencode/p4/l4_today.json` · `l5_today.json`）。
- ⇒ handoff §6/§12 的 DRC 归因（「新件 97／既有 105」）系**增量 2** 口径，续接不沿用；本件用**可复现的 157/236** 作基线。
- 另：增量 3（IN-12/13/14）只赋网不改几何，**赋网本身会新增未连接项**（新声明网未布线）⇒ 236 > 208 属**预期**，不表示退化。

## 2. 本增量做了什么（确定性施工；L2 自裁）

执行器：`k2/tools/k2_p4_converge_v1.py`（新件；sha256 前 16 见 SPEC rev-29 留痕）。三阶段：

| 阶段 | 修正 | 性质 |
|---|---|---|
| **A1** | NC 脚网语义：真源 m13 生成器把 NC 脚写成**同名网 `NO_CONNECT`**（27 pad）⇒ 26 条**假未连接**（登记册 **M-17**）。归一 = 该 27 pad **不属任何网** | 输入数据缺陷的板侧归一（不改真源 yaml） |
| **A2** | 固定孔 keepout（`K2_HOLE_KEEPOUT_H1..H4`）**不得禁用 pad**：区心即孔位，禁 pad 会命中自己的 NPTH pad（自门禁） | 施工自冲突修正 |
| **A3** | `B.SilkS` 上的接插件参考文字镜像（J6/J9/J11/J12/J13） | 丝印口径（J-4 方向） |
| **B** | **旧铜避让新 pad**：P4 新件/移位件落在既有走线/过孔上（shorting / clearance / mask / hole_clearance）。取**可动侧**单一过孔铜簇，**锚点保持**、由锚点重布至新位；新段一律 **0/45/90°**；不合法即登记 `no_solution`（不静默放弃） | 过孔策略/走廊（L2） |
| **C** | 丝印离框（`silk_edge_clearance`）内移 1.0mm | 丝印口径 |

**复跑链（确定性）**：
```bash
K=k2/tools/k2_p4_converge_v1.py; F="--severity-error --severity-warning"
python3 $K --stage A --in <前驱 l5 5c1b0442> --out a.pcb --ledger a.json
AppDir/bin/kicad-cli pcb drc --format json $F --output da.json a.pcb
python3 $K --stage B --in a.pcb --drc da.json --out b.pcb --ledger b.json
AppDir/bin/kicad-cli pcb drc --format json $F --output db.json b.pcb
python3 $K --stage C --in b.pcb --drc db.json --out c.pcb --ledger c.json
```
**复跑同一性**：阶段 A 两次同（`cd2822e7f64879d7`）；阶段 B 中间件因**区域填充非确定性（登记 T-1）**字节可不同（`f5fc21096bdb15e6` / `43ffdc5737a6283c`，DRC 项一致）；**最终件两次逐字节同**（`eed837f4a3a2316b`）。新几何的 uuid 一律由几何确定性派生（uuid5）。

## 3. before / after（可复现口径）

| 指标 | 前驱 l5（`5c1b0442`） | 本增量（`eed837f4`） |
|---|---|---|
| DRC 违规 | **157** | **76** |
| — 其中 `lib_footprint_mismatch/issues`（J-7，warning） | 35 | 35（未动） |
| — 铜几何项（shorting/clearance/mask/hole_*) | **106** | **41** |
| DRC 未连接 | **236** | **209** |
| `criteria/adjudicate.py` | PASS 5 / FAIL 5 | **PASS 5 / FAIL 5（集合未变）** |
| `non45_segments` | 2051 / 2512 | **2051 / 2517**（非 45° 数**未增**；总段 +5 = 重布新段） |
| 新增违规类型 | — | **无**（`track_dangling` 0；未连接未增项） |

判定器（ENG 实跑，非裁定）：`device_has_pads` · `drill_count` · `net_declared_realized` · `pin_map_complete` · `verdict_schema` **OK**；`zone_filled 9/17` · `non45_segments` · `rule_severity_manifest 9/62` · `refdes_sets_equal` · `pipeline_present` **FAIL**（同前驱集合）。

## 4. 剩余项与性质（不改口径，如实登记）

| # | 项 | 性质 / 阻塞 |
|---|---|---|
| 1 | **H3 与排针列冲突**（`H3 的 NPTH 焊盘 ↔ J12 pad1` 孔互overlap 1.13mm；连项 `pth_inside_courtyard 3` · `courtyards_overlap 2` · `hole_to_hole 1` · `items_not_allowed 3`） | P3 两份解冲突：**L2-2 孔位** `H3=(26.10,36.10)`（图纸 `01_board_frame_and_holes.svg`，孔边距**已=下限 1.5mm**，x/y 两向皆无余量）vs **P3-4 排针列** `column_x=27.94`（SPEC `components.pin_headers.column_x` 仍为 **26.5**，两者不一致）。孔位属**机械接口**（对接载板/standoff）、排针列属**电气接口** ⇒ 建议**裁后再动**（ENG 不擅移任一界面） |
| 2 | **`lib_footprint_mismatch 29` + `lib_footprint_issues 6`**（`fp-lib-table` 缺失） | **J-7 权威侧**（板实作 m13 真源生成 vs 库文件），前件已附证据待裁 |
| 3 | **U6/J3 BGA GND 球连通**（GND 未连接 137 项中 U6 75 + J3 14） | 需**逃逸域联合重解**（W-5「mini per-ball 域」）：既有 0.6/0.5mm 格内 PCIe 逃逸已占满 0.3mm 通道，本增量实测**无法**在本层新增合法过孔位（`no_solution` 已登记）⇒ 须按 W-1..W-5 授权重解走廊/逃逸 |
| 4 | **LS/电源信号布线**（NO_CONNECT 已消；余 PERSTA# 5 · I2C 12 · strap 9 · 杂 8 · P3V3/P3V3_AUX/MCU_VDD 13） | SPEC `layer_plan.low_speed_nets.segs` = **"L3 open"**（未冻结折线）⇒ 需先解 LS 域再落板 |
| 5 | `zone_filled`（9/17） | **U4-A**（owner 批判据补丁；口径 = 有网且非 keepout 的铜区 ⇒ 9/9） |
| 6 | `refdes_sets_equal`（板有图无 `H1..H4`） | **U4-C**（机械件是否入图 / 判据排除） |
| 7 | `pipeline_present`（6 目录） | **W-9/J-9** scope（k2 侧可出；其余属 k1/pciesw4） |
| 8 | `rule_severity_manifest`（9 条 ignore） | **W-7/J-1·J-4**（修掉后开检 / 豁免裁定；manifest 属判据，ENG 只读） |

## 5. 完整性备注（本轮）

- **弃用一个更"漂亮"的变体**：本轮曾出现「违规 76 / 未连接 211」的板（重布时破坏了 3 处 pad 连接，出现 `track_dangling` 3）。**该变体已弃**，改以「不破连通」为准（未连接 209）。⇒ 不以外观数字换假绿。
- 阶段 B 的候选序、簇提取、终结端选择、uuid 派生全部**排序化/派生化**（禁用 set 迭代序）；`no_solution`/`skipped` 逐条登记（不静默放弃）。
- **T-1（工具侧，仍开放）**：`pcbnew` 区域填充在 `J9` 紧邻 0.08mm 余量区有顶点/岛归属非确定性 ⇒ 中间件字节可不同；**最终件两次同**（本件实测）。
- 边界：未动 `l4` / 设计源板 / 真源 yaml / SPEC rev-19..28 原件 / `criteria/` 两份；未派 WORKER；临时仅 `/tmp/opencode`。

## 6. 证据（易失，需数字时读本件）

`/tmp/opencode/p4/`：`l4_today.json` · `l5_today.json`（基线）· `final2_drc.json`（本增量）· `meas_f2.json`/`verdict_f2.json`（判定器）· `w/r9/{ledA,ledB,ledC}*.json`（逐项台账）· `w/r9/c{1,2}.kicad_pcb`（复跑同一性）。
