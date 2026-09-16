# K2 · **P4 施工状态（增量 1+2+3）+ 距绿取证 + 出图链核** v5 —— 交监理核

> **依据**：监理 **#K2-18 §五（U3 = P4 开工令）** + **§九-3（P4 施工）**；输入清单 `K2-P4-INPUT-PREREQUISITES-v1.md` v4（IN-1..IN-11）。
> **性质**：施工执行报告（ENG「交测量」，判定权归监理）。**P4 未完工**；本件 = 增量 1 + 增量 2。
> **修订留痕（v5）**：v4（`944b9ee3c4912630`）→ 本版：新增 §14（**平面落图前置 = PASS**：Gerber/钻孔链实测）+ §15（J-7 封装=库：证据）。
> **修订留痕（v4）**：v3（`4071abba5eb1ddea`）→ 本版：新增 §12（**DRC 归因**：新件 97 / 既有 105；连通 364→208）+ §13（P4 剩余作业面清册）。
> **修订留痕（v3）**：v2（`0e147b34d80b53bc`）→ 本版：新增 §10（增量 3 = 真源补网 IN-12/13/14）+ §11（剩余 FAIL 的结构性质 / U4-D / J-9 口径）。
> **修订留痕（v2）**：v1（`68f73746f4609ffc`）→ 本版：新增 §7（增量 2 = **IN-5** 落板赋网）+ §8（DRC 现状）+ §9（**T-1 复跑同一性**）。
> **冻件**：`k2/hw/k2_v4_8L.l4.kicad_pcb`（`d4e81f647be7f980`）**未动**；`criteria/` 两份只读未动。

## 1. 本轮落地（增量 1）

| IN | 动作 | 实测结果 |
|---|---|---|
| **IN-4** | `U1` land pattern 补齐 | pad **33 → 58**（带号 `1..49` = LQFP48 + EP；另 9 个无名 paste-only 开窗）；`EP(49) → GND`；原 33 网按 pad 号迁移 |
| **IN-11** | 5 件接口件 pad 补齐 | `J6/J12`（1x02）+ `J9/J11/J13`（1x04）= **16 pad**（板原 **0**）；`device_has_pads` 已 PASS |
| **IN-8** | 排针列守值 | 5 件 `x: 26.5 → 27.94`（P3-4 余量 0.08 口径） |
| **IN-6** | 固定孔施工 | **4×Ø3.2 NPTH**（H1..H4，L2-2 坐标）+ **Ø6.0 keepout**（8 铜层 rule area，禁 zone_fill/via/track/pad） |
| **IN-7** | `ESC_*` 开关 | 4 个无网 `F.Cu` rule area：`zone_fills = disallow` ⇒ 每区 ≥1 非 allowed（**C5b 达成**） |
| **IN-3** | 9 铜区填充 | **9/9 铜区 `filled_polygon ≥ 1`**（C7 达成；`In1/In3/In6 = GND` + `In4×6`） |

- **件**：`k2/hw/k2_v4_8L.l5.kicad_pcb` = **`13cf989059c414ed`**（新 revision；`k2_v4_8L.l5.kicad_pro` 同批）+ 机读台账 `pm_gate/artifacts/k2_v4/L4/p4_construction_increment1.json` + 执行器 `k2/tools/k2_p4_build_l5_v1.py`。
- **复跑确定性**：**两次连跑 sha 相同**（`13cf989059c414ed`，逐字节一致）；本版绑定无 UUID setter ⇒ 执行器内置三步写盘后规范化（footprint 按 ref 排序 / 新增 keepout zone 按名排序 / 新增件 UUID 确定性派生）。

## 2. 冻结仪器实测（`criteria/adjudicate.py` `897e8bfde60e2cfe`，l5，带 `--nets/--sch-dir/--pro`）

```
--board k2/hw/k2_v4_8L.l5.kicad_pcb --manifest criteria/manifest.k2.yaml
--nets k2/hw/data/k2_sch.errata-1.yaml --sch-dir k2/hw/sch --pro k2/hw/k2_v4_8L.l5.kicad_pro
```

| 判据 | 结果 | 说明 |
|---|---|---|
| `device_has_pads` | **PASS** | `0 焊盘器件 = []`（IN-4/IN-11） |
| `drill_count` | **PASS** | `NPTH = 4`、`PTH = 16`（IN-6/IN-11） |
| `verdict_schema` | **PASS** | 产物无 `verdict` 字段 |
| `zone_filled` | FAIL `9/17` | **口径问题 ⇒ U4-A**（见 §3） |
| `non45_segments` | FAIL `2051/2512` | 登记册 **J-5** 已录现值 2051 ⇒ 待 45° 归一（下一增量） |
| `rule_severity_manifest` | FAIL `9/62` ignore 未登记豁免 | 登记册 **J-1/J-4**（DRC/丝印全开）⇒ 需豁免裁定或整改 |
| `net_declared_realized` | FAIL（0 焊盘网 10 / <2 焊盘网 17） | 随 **IN-5**（13 件落板 + 赋网）收敛 |
| `pin_map_complete` | FAIL（无对应焊盘 26） | 同上（IN-5） |
| `refdes_sets_equal` | FAIL（图 55 / 板 46） | 图有板无 13 = **IN-5**；板有图无 4 = **H1..H4 固定孔** ⇒ **U4-C**（见 §4） |
| `pipeline_present` | FAIL | **J-9** ⇒ 需出 `pipeline.yaml`（下一增量） |

## 3. **U4-A 实证（供 owner 批判据修正）**

- 现判据 `filled_zones == total_zones` ⇒ l5 实测 **`9/17`**（17 = 9 铜区 + **4 个无网 `ESC_*` keepout** + **4 个新增 Ø6.0 固定孔 keepout**）⇒ **结构上永久 FAIL**（keepout 不可能有 `filled_polygon`）。
- 按 **#K2-18 §六-3 待批补丁**口径（仅计**有网且非 keepout** 的铜区）⇒ **`9/9` PASS**。
- ⇒ 本件为 U4-A 提供**双口径实测证据**；`criteria/` 由 ENG **只读**，修正仍须 owner 批 + `ic_hw_gate` 属主落件。

## 4. **U4-C（新发现，请监理裁）：`refdes_sets_equal` 与「必需 NPTH 固定孔」冲突**

- **事实**：IN-6 要求板侧 4×Ø3.2 NPTH（P3-2 判据），落地后板侧 refdes 多出 `H1..H4`；而原理图 refdes 集 = 55（无 `H*`）⇒ `板有图无 4` ⇒ 判据**不可达**。
- **性质**：**判据口径**问题（非板缺陷）—— NPTH 机械孔按行业惯例**不进原理图**。
- **请裁**（二选一）：① 判据口径澄清：`refdes_sets_equal` 排除**非电气/机械件**（如 `attr board_only` 或 refdes 前缀 `H*`，须显式列名口径）；② 或要求原理图侧补 `H1..H4`（属源侧变更，须另批）。
- 现有 `device_has_pads`（每件 ≥1 pad）与 NPTH 不冲突（已 PASS）。

## 5. 下一增量（**未落地**，按序）

1. **IN-5**：13 件补件落板 + `C73/C86` 移位（消费 `p3_placement_solution.json` `15/15`）+ **按 errata 网表赋网** + 布线 ⇒ 收敛 `net_declared_realized` / `pin_map_complete` / `refdes_sets_equal`(13)；
2. **J-5**：`non45_segments 2051 → 0`（走线 45° 归一）；
3. **J-1/J-4**：DRC / 丝印 severity 全开 + 9 条 ignore 逐项裁定或整改；
4. **J-9**：`pipeline.yaml`（门禁接入）；
5. **U4-A**（owner 批后）复算 `zone_filled = 9/9`；**U4-C** 裁定后复算 `refdes_sets_equal`；
6. Gerber 出图前置：**平面层 `G36 > 0`**。

## 6. 复跑 / 边界

```bash
cd /home/fila/jqdDev_2025/ic_hw
# 施工（确定性；输出默认 /tmp/opencode/p4）
K2_P4_OUT=<dst>.kicad_pcb K2_P4_LEDGER=<dst>.json AppDir/usr/bin/python3.11 k2/tools/k2_p4_build_l5_v1.py
# 判定（监理权）
python3 criteria/adjudicate.py --board k2/hw/k2_v4_8L.l5.kicad_pcb --manifest criteria/manifest.k2.yaml \
  --nets k2/hw/data/k2_sch.errata-1.yaml --sch-dir k2/hw/sch --pro k2/hw/k2_v4_8L.l5.kicad_pro \
  --measure-out /tmp/opencode/p4/meas.json --out /tmp/opencode/p4/verdict.json
```
- **边界**：未改冻结件（`d4e81f64`/`fb07d25a`/`dd794c54`/SPEC `rev-19..24` 原件/`criteria/` 两份）· 未派 WORKER · 临时仅 `/tmp/opencode` · **P4 未完工**（不得据本件宣称 P4 绿）。

## 7. **增量 2：IN-5 落板 + 真源赋网**（2026-09-17）

- **动作**：13 件补件（`R35–R39`/`R42–R45` 0603 应变阻 ×9、`L1`、`D2`、`R40`/`R41` 0402）按落位解 `at/rot` 落板；`C73`/`C86` 按 L2-3 解**移位**（→ `(28.0,47.9)` / `(32.4,36.0)`）。
- **赋网口径（禁猜）**：网名取自**真源网表**（`hw/data/k2_sch.errata-1.yaml`，经 `project.yaml:nets_yaml`）；**引脚名→pad 号**一律取符号 `pins` 定义（实测既有件交叉验证 `A→1 / B→2`，如 `C86`/`R33`/`D1`）。15/15 件 `unmapped = []`；执行器自检 `in5_pad_net_ok = true`（逐 pad 复核 pad 号↔网名）。
- **板**：`k2/hw/k2_v4_8L.l5.kicad_pcb` = **`1b8400a255fe90fd`**（59 件 = 42 + 13 补件 + 4 固定孔；0 焊盘件 = ∅）；台账 `L4/p4_construction_increment2.json`。
- **冻结仪器实测变化（增量 1 → 增量 2）**：`pin_map_complete` **FAIL(26) → PASS(0)**；`refdes_sets_equal` 的「图有板无」**13 → 0**（余「板有图无 4」= `H1..H4` ⇒ **U4-C**）；`net_declared_realized` 0 焊盘网 **10 → 1**、<2 焊盘网 **17 → 15**。总计 **PASS 4 / FAIL 6**（余项见 §2 表 + 下节）。

## 8. DRC 现状（`kicad-cli pcb drc`，l5；J-1 证据）

```
AppDir/bin/kicad-cli pcb drc --format json --severity-error --severity-warning k2/hw/k2_v4_8L.l5.kicad_pcb
```
- **违规 202**：`hole_clearance 54` · `solder_mask_bridge 38` · `shorting_items 33` · `lib_footprint_mismatch 29` · `clearance 18` · `items_not_allowed 7` · `lib_footprint_issues 6` · `nonmirrored_text_on_back_layer 5`
- **未连接项 208**（`unconnected_items`）；`schematic_parity = 0`（网表-板一致性由判定器另判）
- ⇒ 属 **P4/P5 布线/DRC 收敛**作业面（含 `C73/C86` 移位后的旧走线残段、13 件补件布线、`lib_footprint_*` 封装库对齐）。

## 9. **T-1（工具侧，登记待修）：复跑同一性**

- **事实**：增量 1 板（`13cf989059c414ed`）两次连跑**逐字节一致**；增量 2 板两次连跑**sha 不同**，差异**仅限**：① 件/段/zone 的**写盘顺序**；② **zone fill 多边形**在 `x≈30, y≈56`（`J9` 紧邻 0.08mm 余量区）处的顶点序列/岛归属（实测 `(net "MCU_VDD")` ↔ `(net "GND")` 归属互换）⇒ 属 **pcbnew zone filler 的非确定性**（非本执行器逻辑随机：几何/网/层/焊盘/keepout/NPTH 项均确定）。
- **影响**：不影响判据测量（`copper_zones_filled = 9` 两次一致）；影响**复跑 sha 相同**这项纪律。**登记 T-1**，处置候选：填充后固定 polygon 为工件 / 或 fill 前固定连通性构建顺序 / 或对 fill 段做确定性规范化。

## 10. **增量 3：真源补网（IN-12/13/14）**（2026-09-17）

- **IN-12（U1 新 pad 34..48）**：按真源网表赋值 **7 个** pad（含 `35 → SWDIO`、`36 → SWCLK_BOOT0`、`47 → I2C1_SCL`、`48 → I2C1_SDA`；其余为 GND/EP）。
- **IN-13（5 接口件）**：`J6 2 / J9 4 / J11 4 / J12 2 / J13 4` = **16 pad 全赋网**（此前只有 pad、无网）。
- **IN-14（U6 侧带球 / gap E）**：**15 个侧带球赋网**（strap 9 网的板侧另一端 + PD/SDA/SCL 类）—— 板侧此前 `net=∅`。
- **板**：`k2/hw/k2_v4_8L.l5.kicad_pcb = 5c1b044241fa6b08`；台账 `L4/p4_construction_increment3.json`；`SPEC rev-28 = 9f067b237c2da6dd`。
- **判定变化**：**PASS 5 / FAIL 5**（`net_declared_realized` FAIL → **PASS**：0 焊盘声明网 1 → **0**；<2 焊盘网 15 → **1**）。当前 OK：`device_has_pads`·`drill_count`·`net_declared_realized`·`pin_map_complete`·`verdict_schema`。

## 11. **剩余 5 项 FAIL 的结构性质（请监理裁）**

| 项 | 现状 | 性质 / 归属 |
|---|---|---|
| `zone_filled` | 9/17 | **U4-A**（判据口径；owner 批后 = 9/9） |
| `non45_segments` | 2051/2512 | **U4-D（新，结构）**：按层 `In5 1906` / `F.Cu 126` / `In2 13` / `B.Cu 6`；In5 走廊段系引擎**按冻结 W3 图纸折线原样落段**（引擎自述「原样消费图纸…不改图纸；图纸 sha 作输入校验」+ 宪法「零运行时自由度」）⇒ 45° 归一须**改图纸/重解走廊**（设计层变更）⇒ 请裁：(a) 授权重解走廊折线；(b) 或 J-5 口径收窄（如仅适用指定网类/长度阈值） |
| `rule_severity_manifest` | 9/62 ignore 未登记豁免 | **J-1/J-4**：`copper_sliver`·`footprint_filters_mismatch`·`footprint_type_mismatch`·`missing_courtyard`·`silk_over_copper`·`silk_overlap`·`track_not_centered_on_via`·`tuning_profile_track_geometries`·`via_dangling` ⇒ 每条**二选一**：修掉违规后开检 / 出**豁免裁定**（manifest 属判据，ENG 只读）。DRC 现状（l5）：**违规 202 + 未连接 208** |
| `refdes_sets_equal` | 图 55 / 板 59（板有图无 4） | **U4-C**（必需 NPTH `H1..H4` 与原理图口径） |
| `pipeline_present` | 6 目录无 `pipeline.yaml` | **J-9**：判定器要求**每个含 `.kicad_sch` 的目录**均有该文件 —— `k2/hw/sch` 可出（schema 参照 `key_v2/key_v2/pipeline.yaml` + `_shared/eda_core/pipeline/checks.py`）；**其余 5 个属 k1/pciesw4** ⇒ 请裁 J-9 是否 k2-scoped，或授权跨项目补件 |

**注记**：`PWR_5V_KEY` 真源仅 **1 节点** ⇒ 登记册「每条声明网 ≥2 焊盘」对其不可达（判定器现按 `nets_with_zero == 0` 判 ⇒ 已 PASS）；登记为口径注记，无需改件。

## 12. **DRC 归因（新件 vs 既有）与连通改善**（2026-09-17，`kicad-cli pcb drc`）

| 对象 | 违规 | 未连接 |
|---|---|---|
| **l4（冻结交付板，P4 前基线）** | **42**（`lib_footprint_mismatch 29` / `lib_footprint_issues 12` / `silk_edge_clearance 1`） | **364** |
| **l5（P4 增量 3）** | **202** | **208** |

**归因（按违规项是否涉及本件新增对象 `H1..H4` / `K2_HOLE_KEEPOUT` / 5 接口件 / 13 补件）**：
- **涉及新件 97**：`hole_clearance 42` · `shorting_items 14` · `solder_mask_bridge 10` · `clearance 8` · `items_not_allowed 7` · `nonmirrored_text_on_back_layer 5` · `pth_inside_courtyard 3` · `silk_edge_clearance 3` · `hole_to_hole 3` · `courtyards_overlap 2`
- **既有/其他 105**：`lib_footprint_mismatch 29` · `solder_mask_bridge 28` · `shorting_items 19` · `hole_clearance 12` · `clearance 10` · `lib_footprint_issues 6` · `silk_edge_clearance 1`

**根因（实例，均非「判据/口径」问题，而是**施工顺序**问题）**：
1. `shorting_items`（例：`GND` 走线 0.675mm @(31.85,54.5) 与 `U1` pad 11 `PERSTA#` 相碰）⇒ **l4 的既有走线是在 `U1` 只有 33 pad 的前提下画的**；`IN-4` 补齐 `34..49` 后，新 pad 落在既有走线上。
2. `hole_clearance`（例：`J9` PTH pad 3 与 `GND` via @(30.275,56.0) 净距 **0.2157 < 0.25**）⇒ **`IN-8` 排针列 `+1.44mm` 移位**把 pad 移进既有 via/走线旁。
3. 4×NPTH + Ø6.0 keepout：孔周既有铜需让位（`hole_clearance` 大头 + `items_not_allowed 7`）。
- ⇒ **连通性净改善 364 → 208**（真源补网 + 补件落板生效）；**违规上升 42 → 202 全属「新增对象 vs 既有走线」的施工冲突**，须由**重布 U1 周圈 / 排针列周圈 / 孔周 / 补件走线**收敛。

## 13. **P4 剩余作业面清册（供监理排布/授权）**

| # | 作业面 | 规模（实测） | 前置/性质 |
|---|---|---|---|
| W-1 | **U1 周圈重布**（34..49 新 pad 与既有 GND/信号走线冲突） | `shorting 14`（新件）+ `clearance 8` + `mask 10` 部分 | 需布线（引擎链外或需批准） |
| W-2 | **排针列周圈重布**（`column_x 26.5→27.94` 后 pad↔via/走线冲突） | `hole_clearance` 部分 + `clearance` 部分 | 同上 |
| W-3 | **固定孔周让位**（4×Ø3.2 + Ø6.0 keepout 与既有铜） | `hole_clearance 42` 大头 + `items_not_allowed 7` | 同上 |
| W-4 | **补件走线**（13 补件 + `C73/C86` 移位后旧段残线） | **未连接 208 主体** | 同上 |
| W-5 | **U6 侧带球逃逸**（gap E；L2 已裁「球隙 via→In2→南带」） | 15 球 | 实现 = **引擎链外 mini per-ball 域**（m13 §3c：须按宪法确定性实现或登记引擎扩展）⇒ **需批准** |
| W-6 | **J-5 非 45° 归一**（`In5 1906` 等） | 2051 段 | 源头 = 冻结 W3 图纸折线 ⇒ **U4-D 待裁**（授权重解 or 口径收窄） |
| W-7 | **J-1/J-4 九条 ignore** | 9 条（DRC/丝印全开口径） | 修 or 豁免裁定（manifest 属判据，ENG 只读） |
| W-8 | **J-7 封装=库**（`lib_footprint_mismatch 29` + `issues 6` + `fp-lib-table`） | 35 | 需先裁**权威侧**（板实作 vs 库文件；K2 板件由 m13 真源生成，库可能陈旧）⇒ 口径问题 |
| W-9 | **J-9 `pipeline.yaml`** | 6 目录（k2 + k1/pciesw4 等） | `k2/hw/sch` 侧可出；其余属他项目 ⇒ **待裁 scope** |
| W-10 | **P4 出 Gerber**（平面层 `G36 > 0`） | 8 铜层 + 钻孔 + 叠层/阻抗 | **须待 W-1..W-4 收敛后**（现状 DRC 未绿不得出图交付） |

**ENG 就绪声明**：W-1..W-4 的**执行方式**（既有引擎链 vs 授权新写确定性执行器）与 W-5/W-6/W-7/W-8/W-9 的**口径/授权**均需监理裁示；未获裁示前 ENG 不擅自布线或改生成器（红线：未获批不得改生成器/SPEC/原理图）。

## 14. **平面落图前置（P4 完工前置 4）= PASS**（2026-09-17 实测，`kicad-cli pcb export gerbers`）

```
AppDir/bin/kicad-cli pcb export gerbers -o <dir> -l F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,In5.Cu,In6.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts \
    k2/hw/k2_v4_8L.l5.kicad_pcb
AppDir/bin/kicad-cli pcb export drill -o <dir>/drill/ k2/hw/k2_v4_8L.l5.kicad_pcb
```

| 层 | `%G36` 区域填充 | 判定 |
|---|---|---|
| `In1.Cu`（GND 平面） | **1** | ✅ |
| `In3.Cu`（GND 平面） | **1** | ✅ |
| `In6.Cu`（GND 平面） | **1** | ✅ |
| `In4.Cu`（电源分区） | **7** | ✅ |
| `F.Cu` / `B.Cu` | 0 / 0 | 符合设计（该两层无铜 zone；`ESC_*` 为 rule area 非铜） |
| `F.Mask` / `B.Mask` | 674 / 19 | — |

- **钻孔**：Excellon 导出成功 = `front-in2` · `in2-in5` · `front-in5` · `back-in5` · `l5`（**含 HDI 盲/埋孔**分孔带）+ 通孔。
- ⇒ P4 完工前置「平面层 Gerber `G36 > 0`」**已满足**；**出图/钻孔链本身可用**（W-10 就绪），但**出图交付仍须待 DRC 绿**（现状 202 违规 + 208 未连接，见 §12/§13）。

## 15. **J-7「封装 = 库」证据（供裁权威侧）**

- DRC `lib_footprint_mismatch` + `lib_footprint_issues` 涉及 **35 件**（`C73–C84` 等去耦件为主）。
- 实例（`J2`）：**板实作 pad 74 = 库 74** ✅（电气几何一致），但**板实作缺库的图形项**（`(fp_line`：板 **0** / 库 **8**），且 `(property` 板 **4** / 库 **2**。
- ⇒ 板实作系 m13 真源生成（pads 权威、图形/属性精简），**库文件含完整图元** —— 二者非「谁错」而是**权威侧口径**问题：① 以板为准 ⇒ 判据应容忍图形级差异（或库对齐板）；② 以库为准 ⇒ 需按库重落全部 35 件（会改动丝印/属性，属源侧变更）。
- **请监理裁 ①/②**（ENG 在裁示前不动库、不重落件）。
