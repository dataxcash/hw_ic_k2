# K2 · P4 收敛增量 1+2 状态件 **v2** —— 交监理核

> **修订留痕（v5）**：v4 → 本版新增 §11（**增量 5：F.Cu 通道搜索 = 阶段 F2**，含「F.Cu 域近耗尽」结论）。
>
> **修订留痕（v4）**：v3 → 本版新增 §10（**增量 4：低速/电源局部闭合 = 阶段 F1**；含 needs-router 48 条登记）。
>
> **修订留痕（v3）**：v1（`e1a34350d2429643`）→ v2（`41feb559f532bd6c`，§7 增量 2）→ 本版新增 §9（**增量 3：GND 平面接入 v2 = 阶段 E，真盲孔 F.Cu→In1 盘中孔**；含 T-2/T-3/T-4 登记）。

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

## 7. **增量 2：GND 平面接入（阶段 D）**（2026-09-17）

**目的**：未连接 196~209 项中 **GND 占 124~137**，主体是 U6/J3 BGA 地球无平面通路。阶段 D 对每个 DRC 未连接的 GND pad 所在**同网铜岛**，加 **1 支盲孔 F.Cu→In1.Cu（0.20 孔 / 0.35 盘）** + 0/45/90° 同网引线（宽 0.20）。

- **过孔类**：新增的只是**跨度**（F→In1），孔径/盘径**沿用板内既有 std 类 0.20/0.35**（板内已有 92 支 F→In2 同类盲孔）⇒ **未放松任何 DRC 下限**。（先前 0.10/0.25 激光微孔方案会触发 `drill_out_of_range`/`via_diameter` 20+20 项，**已弃用**，不以放松下限换连通。）
- **判决条件**：净距（net class max）· 孔-铜 0.25 · **孔-孔 0.25（无同网豁免）** · 板边铜 0.3 · keepout 禁 via · 新段仅 0/45/90° 且单腿 ≥0.05。纯增（不动既有铜）。
- **实测**：未连接 **209 → 196**（GND 137 → 124），违规 **76 → 76（不变）**，**无新增违规类型**。
- **登记不可行者**：115 个铜岛 `no-legal-slot`（U6/J3 格内 0.3mm 通道被既有 PCIe 逃逸占满）· 6 个铜岛 `island-has-via`（岛内已有 GND via 但 DRC 仍判未连接 ⇒ 属**接触口径**存疑，另行取证）。⇒ U6/J3 地球主体仍须**逃逸域联合重解**（W-5），本条不掩盖。

## 8. 累计口径（增量 1+2）

| 指标 | 前驱 l5 `5c1b0442` | 增量 1 `eed837f4` | **增量 2 `10753591`** |
|---|---|---|---|
| DRC 违规 | 157 | 76 | **75** |
| DRC 未连接 | 236 | 209 | **196** |
| 判定器 | PASS5/FAIL5 | PASS5/FAIL5 | **PASS5/FAIL5（集合未变）** |
| 非 45° 段 | 2051 | 2051 | **2051（未退化）** |

级联复跑（A→B→D→C，含 4 次 DRC）**最终件两次逐字节同**（`10753591dc6967d5`）。SPEC rev-30 留痕。

## 9. **增量 3：GND 平面接入 v2（阶段 E）**（2026-09-17）

**结论：U6/J3 BGA 地球主体 = 闭合；无需重解 W3 逃逸走廊，PCIe 85Ω 与等长未被触碰。**

- **动因（T-3，v1 过保守）**：`k2_p4_converge_v1.py` 阶段 D 的 `clear_pt`/`clear_seg` **不分层**，
  把 In2/In5/B.Cu 走线也当作 F→In1 孔的障碍 ⇒ 系统性命中 `no-legal-slot`（115 铜岛）。
  按层重算（F.Cu→In1 盲孔的铜只存在于 F.Cu / In1.Cu）后，同一几何下 **139/140 有合法位，133 支即在焊盘中心**。
- **执行（阶段 E，新器 `k2/tools/k2_p4_gnd_vias_v1.py 9a57160f0464a47e`）**：对每个 DRC 未连接 GND 焊盘加
  **1 支真盲孔 F.Cu→In1.Cu（0.20 孔 / 0.35 盘，板内既有唯一类）**；圆心首选焊盘中心（**盘中孔 128/129**），
  余者以 0/45/90° 同网引线（宽 0.20）接入。**未放松任何 DRC 下限**（0.10/0.25 类仍弃用）。
- **真盲孔落法（T-2 实证）**：本 build 的 pcbnew API（`SetLayerSet`/`SetLayerPair`）**无法置盲孔跨度**
  （任意组合恒落 F.Cu→B.Cu 通孔）⇒ 真盲孔改由**文件级 `(via blind ...)` token** 写入，load/save 往返实核
  `span = F.Cu/In1.Cu`。**同时更正留痕**：增量 2 的 12 支自称 F→In1，经核为 **F→B 通孔**（通孔数 273→285、
  F.Cu/In1 盲孔 0 支）；其**现态合法**（DRC 无新增），是否改真盲孔不影响连通。
- **实测（同一条 DRC 命令）**：

| 指标 | 增量 2（l5 `10753591`） | **增量 3（l5 `9efdcc3c`）** |
|---|---|---|
| DRC 违规 | 75 | **75（类型集不变 9 类；无新增类型）** |
| DRC 未连接 | 196 | **72** |
| — 其中 GND 未连接 | 124 | **0** |
| 判定器 | PASS 5 / FAIL 5 | **PASS 5 / FAIL 5（集合未变）** |
| 非 45° 段 / 总段 | 2051 / 2535 | **2051 / 2537**（非 45° 未退化） |

- **复跑同一性**：阶段 E 两次运行**逐字节同**（`9efdcc3c8c791d65`）；SPEC **rev-31** 留痕；`project.yaml` 指向 rev-31。
- **剩余 72 未连接 = 全部为低速/电源信号网**（P3V3 12 · P3V3_AUX 11 · PERSTA# 5 · MCU_VDD 4 ·
  I2C1/I2C2 共 12 · NRST/FB_U2/SW_U2/12V_IN/SWCLK_BOOT0/strap 等）⇒ 属
  `layer_plan.low_speed_nets.segs = "L3 open"` 的**布线域**（独立工作流），**与 GND/平面接入无关**。
- **T-4（工具，已规避）**：本 build pcbnew 在**同进程内加载第二块板即 segfault**，且 `LoadBoard` 依扩展名分发
  ⇒ 阶段 E 的区域填充**另起子进程**、tmp 保持 `.kicad_pcb` 后缀、`.kicad_pro` 随件同重复制（取 DRC/netclass 设置）。
- **边界**：未动 `l4` / 设计源板 / 真源 yaml / `criteria/` 两份 / SPEC rev-19..30 原件；未派 WORKER；临时仅 `/tmp/opencode`。

## 10. **增量 4：低速/电源局部闭合（阶段 F1）**（2026-09-17）

**目标（P4/V1 连通归零的中间步）**：把 DRC 未连接的两端「就近」接上。剩余 72 条未连接边中，绝大多数是
**裸 pad↔pad**（两端铜岛都没有过孔）⇒ 属低速/电源**布线域**（SPEC `layer_plan.low_speed_nets.segs = "L3 open"`）。

- **执行（阶段 F1，新器 `k2/tools/k2_p4_ls_local_v1.py 3eb4331bce9ba0ac`）**：对每条未连接边，取两端**铜岛**在
  **指定层**上最近的可用接点，试 ① 同层 **F.Cu 0/45/90° 直连**；② 两端铜岛**都已在 B.Cu 有铜**
  （既有跨层过孔 / 插件孔）时 **B.Cu 直连**。线宽 **0.200**（= 板内既有低速/电源走线口径）；净距 = net class max；
  板边 0.3；禁 track 禁布区规避；纯增。
- **实测**：未连接 **72 → 49**（+23 条闭合：F.Cu 21 / B.Cu 2）；违规 **75 → 75（类型集不变，无新增）**；
  判定器 **PASS 5 / FAIL 5（集合未变）**；非 45° 段 **2051 未增**（总段 2537→2579）。复跑两次**逐字节同**
  （`7f57f9bfd2283193`）。
- **本轮修过的一个真缺陷（记录）**：F1 首跑曾引入 1 条 `track_dangling`（B.Cu 走线端点选到了该铜岛**仅 F.Cu 有铜**的接点）
  ⇒ 已改为**按层取接点**（`ports_of(comp, layer)`）后归零。
- **声明边界（不静默放弃）**：**48 条**未解边登记 `needs-router` —— 长距离（10–80mm）或需在 IC 侧落孔换层
  （U1/U6/E2 pad→via→B.Cu→插件件 B.Cu 焊盘）。固化为：**B.Cu 近乎空层**（39 走线 / 0 铜区）、西侧插件件
  （J6/J9/J11/J12/J13）为 **PTH ⇒ B.Cu 可达** ⇒ 后续布线增量有明确落点。
- **边界**：未动 `l4` / 设计源板 / 真源 yaml / `criteria/` 两份 / SPEC rev-19..31 原件；未派 WORKER；临时仅 `/tmp/opencode`。

## 11. **增量 5：低速/电源 F.Cu 通道搜索（阶段 F2）**（2026-09-17）

- **执行（新器 `k2/tools/k2_p4_ls_route_v1.py 9ad1050e013c97ca`）**：对剩余未连接边中**两端铜岛皆在 F.Cu 有铜**且
  **距离 ≤20mm** 者，做同层 F.Cu **0/45/90° 通道搜索**（0.05mm 网格八方向 A*，L 形收尾保证段角合法）；线宽 0.200。
- **放行闸 = 精确复核（不依赖栅格）**：候选路径逐段与**全部异网 F.Cu 铜 / 全部孔（孔-铜 0.25）/ 板边 0.3 /
  禁 track 禁布区**精确比对，任一不符即弃并继续试下一接点对。
  - **过程记录（重要）**：首版**无**精确复核时曾落 16 条、但 DRC 违规 75→**208**（shorting 48 / clearance 26 /
    mask-bridge 67 / tracks_crossing 14 / hole_clearance 12）——根因 = 栅格只标了多边形焊盘**边缘**（内部漏标）、
    未含**孔-铜**、且格心量化误差可达半个对角。⇒ 改为「栅格剪枝 + **精确复核放行**」后，同样的搜索**回归合规**。
- **实测**：未连接 **49 → 46**（+3：`P3V3_AUX` 1.235mm · `PERSTA#` 6.705mm · `SWCLK_BOOT0` 13.762mm）；
  违规 **75 → 75（类型集不变，无新增）**；判定器 **PASS 5 / FAIL 5（集合未变）**；复跑两次**逐字节同**
  （`77658bed7efaf508`）。
- **结论（对本阶段最关键）**：33 条 ≤20mm 边中**仅 3 条**存在合法 F.Cu 同层通路 ⇒ **F.Cu 同层域已近耗尽**；
  剩余 46 条的几何出路在**跨层**（B.Cu 近乎空层）+ **IC 侧落孔**，登记 `needs-cross-layer-router` 16 条 /
  `no-legal-path-in-fcu` 30 条。
