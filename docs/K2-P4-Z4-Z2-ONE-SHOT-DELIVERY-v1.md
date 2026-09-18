# K2 · P4 · `Z4`+`Z2` **一次投递包**（陈旧刷新 diff ＋ G10 keepout/zone/NPTH 输入块；**单件**）· v1 · 2026-09-18

> 缘起：handoff inc63 §6-3-(k)「把 inc60 的 **12 项陈旧 diff** 与 inc62 的 **zone/keepout 数据块 + emit 段**合并为**单一投递件**（纯文档/草案，不落件），使裁后**一次执行**」。
> 本会话**无监理放行** ⇒ ENlegal 面；**仓库零载体改动**（仅新增本证据件 + inc63 NPTH 件）。
> 锚：SPEC rev-47 `9ba09cbc148d6836` · L3 图纸 `21e8891ea3fc4c06` · 受审板 `6ff49da5678c2108` · l5 pro `d5e0ca067a7b585e` · 真源 `dd794c54f7ce7417` · errata-1 `17d540f058631a5e`。
> 源件：`K2-P4-Z4-STALE-REFRESH-CHECKLIST-v1.md` `feeb7fdb16bee5a5` · `K2-P4-Z2-G10-KEEPOUT-ZONE-DRAFT-v1.md` `37229c94f4b92b7e` · `K2-P4-G10-NPTH-SEGMENT-DRAFT-v1.md`（inc63）。

## 0. 结论（五条）

1. **投递包＝四块，一次裁、一次执行**：
   - **A 块（8 项）**：纯**版本化传播**（既有独立裁定/修复决定 ⇒ **非** C-1 自证）→ SPEC bump + 图纸**整族重生成**即可；
   - **B 块（4 项）**：板为权威、无独立成文应然 → 须 **Z2「以板为准」**口径一并裁；
   - **C 块（1 项）**：`PWR_5V_KEY` → **⑤ owner（L1）**；
   - **G10 段（18 区 + 4 NPTH）**：数据块 + emit 段已成件（inc62/inc63，含回归 + KiCad 级双验证），属 **B 块同源**，随 Z2 裁一次投递。
2. **合并输入块已成件（`/tmp`）**：`/tmp/opencode/inc63/p4_g10_input_block_merged.json` **`e9fac22b084f9b4c`**（`g10_zones` 18 区 ＋ `g10_npth` 4 孔；`counts = zones 18 / keepout 8 / copper 10 / npth 4`）。
3. **已证「一次执行可闭环」**：A 块＝纯值替换（无歧义）；B/G10 块＝**生成器改消费输入层、不读板**（避 C-1 自证，见 inc62 §0-4）；两者**写入面互不重叠**（SPEC `components.pin_headers` / `mounting_holes` / `keepout_geometry` / `pd.zone_defs`）。
4. **依赖与同批性（关键）**：`D5/D6/D7`（`board_pads` / `U1` pad 数）的应然值依赖 **G-ROOT-1 + ⑦ 库↔板名集** 放行；**Z4 整族刷新应与 G-ROOT 放行同批**，否则「刷了又漂」。`C1`（`PWR_5V_KEY`）待 ⑤。
5. **不新增检查齿（owner ②）**：本件**未**定义新阈值/新维度；收敛复用既有维度（`drill_count`（冻结）· `zone_filled`（冻结）· `keepout_active`（草案））。

## 1. `Z4` 陈旧清单（12 项，逐条可执行；＝inc60 §2 全文，加「投递分组」列）

| # | 载体 · 字段 | 现值 | **应然值** | 权威 | 类 | 投递分组 | 动作 |
|---|---|---|---|---|---|---|---|
| **D1** | `SPEC.components.pin_headers.column_x` | `26.5` | **`27.94`** | L2-3 裁定 + #K2-21 §二 守恒闸 | A | ①SPEC bump | SPEC bump |
| **D2** | `SPEC.components.pin_headers.positions[*].x` | `26.5` ×5 | **`27.94`** ×5 | 同上 | A | ①SPEC bump | SPEC bump |
| **D3** | `drawings.mounting_holes.positions.H3` | `(26.1,36.1)` | **`(45.10,75.10)`** | #K2-19 §一-3（L2 热机械自裁） | A | ②图纸整族 | 图纸重生成 |
| **D4** | `drawings.criteria.C2_mounting_holes.per_hole[H3]` | `at=(26.1,36.1)`, `edge_material=1.5` | **`at=(45.10,75.10)`, `edge_material=2.30`** | 同上（`K2-P4-H3-RESOLVE-AND-12V-FEED-v1.md` §2） | A | ②图纸整族 | 同上 |
| **D5** | `drawings.devices.{J6,J9,J11,J12,J13}.board_pads` | `0,0,0,0,0` | **`2,4,4,2,4`**（合计 16） | P4 落件已补 16 pad | A | ②图纸整族 | 同上（依赖 G-ROOT-1/⑦） |
| **D6** | `drawings.devices.U1.board_pads` | **`33`** | **`58`** | IN-4 修复决定（U1 补齐 34..48 + EP(49)） | A | ②图纸整族 | 同上（依赖 G-ROOT-1/⑦） |
| **D7** | `drawings.criteria.C3_pad_eq_symbol_pins.U1.footprint_pads` | **`49`** | **`58`** | 同上（且与 D6 的 33 **族内矛盾**） | A | ②图纸整族 | 同上 |
| **D8** | `drawings.pour_zones.{count,filled_count}` | `13 / 0` | **`10 / 10`** | 板（口径＝#K2-21 §一「有网非 keepout」） | B | ③Z2 数据块 | 图纸重生成（须先裁 Z2） |
| **D9** | `drawings.criteria.C7_pour_zones_filled.{count,filled,pass}` | `9 / 0 / false` | **`10 / 10 / true`** | 同上（#K2-21 §一 口径修正：9→10） | B | ③Z2 数据块 | 同上 |
| **D10** | `drawings.criteria.C5b_board_side_esc_switches.{count,zones_all_allowed}` | `4 / 4`（全 allowed） | **4 区 `copperpour: not_allowed`**（其余 allowed） | 板 | B | ③Z2 数据块 | 同上（Z2） |
| **D11** | `drawings.keepouts`（`KO-5`/`KO-6` 各 `count=1`；`KO-7` `count=4`） | 与板 4 个 F.Cu 区**不 1:1** | **板 4 区**（`ESC_U6/ESC_J3/ESC_J4/ESC_J2`） | 板（bbox 见 inc55 表 B） | B | ③Z2 数据块 | 同上（Z2） |
| **D12** | `drawings.spec`（自指） | `SPEC_k2_v4.spec-rev-25.json` `74f31d08a8be2f17` | **`rev-47` `9ba09cbc148d6836`**（`project.yaml::spec_name`） | 配置 | A | ①SPEC bump | 图纸重生成 |
| **C1** | `SPEC.layer_plan.low_speed_nets.nets` 含 `PWR_5V_KEY` | 19 网含之 | **待 ⑤ owner 裁定**（inc59） | L1/电源域口径 | **C** | ④owner | 待裁后同步 |

> 汇总：**A 类 8**（D1–D7、D12）· **B 类 4**（D8–D11）· **C 类 1**（C1）。**C1 不阻塞 A/B 执行**（A/B 未引用该网）。

## 2. 族内自相矛盾（三组；证明「必须整族重生成」）

| 事实 | 矛盾 A | 矛盾 B | 外部真值 |
|---|---|---|---|
| `column_x` | `drawings.criteria.D1….column_x = 27.94`（`C4` min 余量 0.08 @`J9` 即按 27.94 复算） | `SPEC.components.pin_headers.column_x = 26.5` | 板 `fp.at.x = 27.94`（5/5） |
| `U1` pad 数 | `drawings.devices.U1.board_pads = 33` | `drawings.criteria.C3….footprint_pads = 49` | 板 = **58** |
| 铜区 | `drawings.pour_zones = 13`（filled 0） | `drawings.criteria.C7 = 9`（filled 0） | 板 = **10**（filled 10/10） |

⇒ 逐项打补丁会留下「同一族两个真相」；**应以 rev-48 SPEC + P4 受审板为唯一基线整族重生成**。

## 3. 一致项（**无需改**；列出以防误刷）

| 项 | 值 | 核对 |
|---|---|---|
| `drawings.board_frame` | `x[23,143] y[33,79]` = 120×46 | 板实测一致 ✓ |
| 铜层集合/角色 | 8 层（`F/In1..In6/B`）；`gnd_planes=In1/In3/In6`、`power=In4`、`signal=F/In2/In5/B` | 板 ✓、`SPEC.stackup` ✓ |
| `drawings.nets_yaml` | `errata-1` `17d540f058631a5e` | 与 `project.yaml` 一致 ✓（随 §5-8 裁定可能变） |
| SPEC 5 处网名清单 | 全为真源网集子集 | **无其他 K1 残留**；K1 节点名（`U8/VOUT`…）在 SPEC/图纸 **0 命中** ✓ |
| `drawings.criteria.C6_corridor_basis` | `pass:true`、`bases_found_in_spec:[]` | 已由 IN-10/rev-25 回写 ✓ |

## 4. `Z2` / `G10` 数据块（B 块；已成件，随 Z2 裁一次投递）

**4.1 输入层候选（合并件）** `/tmp/opencode/inc63/p4_g10_input_block_merged.json` **`e9fac22b084f9b4c`**

| 子块 | 内容 | 计数 | 源件 sha |
|---|---|---|---|
| `g10_zones` | 8 keepout（4 全层孔 keepout + 4 F.Cu `ESC_*`）+ 10 有网铜区 | 18 | `zones_input.json` `2edb6eec2d600494` |
| `g10_npth` | H1–H4 逐座标 + Ø3.2 + keepout 6.00×6.00 | 4 | `npth_input.json` `ab053d17b8580308` |

**4.2 关键口径（全部取自受审板实测；裁「以板为准」后直接投递）**

- **孔 keepout（4）**：全 8 层 · 6.00×6.00 · **精确居中于孔心 d=0.00** · `tracks`/`vias`/`copperpour` `not_allowed`、**`pads`/`footprints` `allowed`**（图纸 `KO-1..4` 为五开关全 blocked ⇒ **口径差**）。
- **ESC keepout（4）**：F.Cu · `copperpour not_allowed` · `ESC_U6 (82.10,49.11,105.34,58.29)` · `ESC_J3 (53.45,42.40,65.55,46.60)` · `ESC_J4 (53.45,60.60,65.55,64.80)` · `ESC_J2 (131.50,42.23,136.15,65.17)`（图纸 `KO-5`/`KO-6` 各 count=1 ⇒ **枚举陈旧**）。
- **有网铜区（10）**：`In1/In3/In6=GND` + `In4 {12V_IN×2(priority 1/2), P3V3_AUX×2, P3V3×2, MCU_VDD×1}`；板 **10/10 全填充**（图纸 `power_partition` 仅 2 区、`pour_zones 13/0` ⇒ **陈旧**）。
- **NPTH（4）**：`H1(26.10,75.60) · H2(139.60,39.60) · H3(45.10,75.10) · H4(114.60,36.10)`，`np_thru_hole circle`，`size=drill=3.2`，`layers "*.Cu" "*.Mask"`（**通配写法**，勿枚举 32 层）。
- **KO-7 板边**：板**无独立实体 zone**，由规则 `min_copper_edge_clearance=0.3` 承载（inc61 §3 建议**不补实体 zone**，须登记理由）。
- **填充**：草案**不**产 `filled_polygon`，由既有「出图前 `ZONE_FILLER`」强制填充（inc62 §4 实测有效）。

**4.3 已验证事实（可复跑，见各件 §7）**

| 验证 | 结果 |
|---|---|
| zone/keepout 回归自证（inc62 §3） | `zones=18 field-mismatches=0 ⇒ PASS` |
| zone/keepout KiCad 级（inc62 §4） | 剥区→插区→`ZONE_FILLER`：`keepout_active` PASS（全 allowed=0）· `zone_filled` **10/10** · 铜网集逐名一致 |
| NPTH 回归自证（inc63 §3） | `holes=4 mismatches=0 ⇒ PASS` |
| NPTH KiCad 级（inc63 §4） | 剥 4 footprint→插 emit→Load→量测 4/4 匹配→Save→重载 4/4（原 18 区仍在） |
| emit 确定性（T-38） | `zones_emit.txt` `53b47d754916c6c2`（两次同 sha）· `npth_emit.txt` `03ef8ef22d4525f3`… | 

## 5. 一次执行序（裁后；每步唯一输入源 ⇒ 零返工）

```
Step 0  监理一次裁：① Z4 权威源（刷新至 P4 后真值 / 以受审板为准，是否触 C-1）
                       ② Z2 口径（keepout 枚举/层集/开关 · In4 分区粒度 · KO-7 是否补实体 zone）
                       ③ G-ROOT-1/⑦ 是否与 Z4 同批（D5/D6/D7 应然值依赖）
                       （④ ⑤ C1 单独 owner，不阻塞本序）
Step 1  SPEC bump → rev-48：D1/D2（column_x/positions = 27.94）；D12（图纸自指 spec）；C1 视 ⑤
Step 2  写入 Z2/G10 输入层：`keepout_geometry.zones` / `pd.zone_defs.board_realized_zones` / `mounting_holes`
        （数据＝§4.1 合并件；**来源具名登记**「受审板实测 + 监理以板为准裁定」）
Step 3  生成器改**消费输入层、不读板**（避 C-1）：`emit_zone()`（inc62 §2）+ `emit_footprint()`（inc63 §2）
        （同批：G-ROOT-3 去锚板依赖 + §5-8 真源路径甲/乙）
Step 4  图纸**整族重生成**于同一基线（rev-48 SPEC + 受审板）：D3–D12 一次归零
Step 5  /tmp 复跑：A 块逐值比对 + B 块 emit/round-trip/KiCad 级 + 判据复算（期望 **19P/0F**，两维阈值由监理给）
Step 6  四方一致验收（§6）→ 落件 → 以**落件板 sha** 重跑五件测量 + 判定器 + DRC + 守恒
Step 7  （仅 Step 6 全绿后）`criteria/manifest.k2.yaml` 方可 `not_countersigned:false` 签认
```

## 6. 验收（Step 6 判据；机检项）

1. **四方一致**：`SPEC rev-48 ↔ 图纸新 rev ↔ 受审板/落件板 ↔ 真源` 逐项机检 —— D1–D12 全归零、§3 五项**未漂**。
2. **判据复算**：**19P/0F**（PROVISIONAL 现状 → 签认后转正式）；两维（密度/间距）阈值由监理给。
3. **DRC 违反 = 0**（T-8：取**同名 pro**）。
4. **守恒复算**（受审板基线，待落件板 sha 重跑）：`tracks 4722 / vias 711 / zones 18 / nets 102 / pads 687`。
5. **测量件必带 `board_sha16`**（陈旧即 fail-closed）；**落件板 sha16 == 受审板 sha16** 才可宣称等价。

## 7. 复跑（每处实测；仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw; export SHARUN=$PWD/AppDir/sharun
# Z4 陈旧扫描（12 项 + 3 组族内矛盾）：见 K2-P4-Z4-STALE-REFRESH-CHECKLIST-v1.md §6
# Z2 keepout/zone 草案（回归 18/0 + KiCad 级）：见 K2-P4-Z2-G10-KEEPOUT-ZONE-DRAFT-v1.md §7
# NPTH 段草案（回归 4/0 + KiCad 级）：见 K2-P4-G10-NPTH-SEGMENT-DRAFT-v1.md §7
# 合并输入块（本件 §4.1）：/tmp/opencode/inc63/p4_g10_input_block_merged.json（sha16 e9fac22b084f9b4c）
```

## 8. 边界

本件**只读 + `/tmp` 草案**：未改 SPEC/图纸/板/pro/真源/生成器/模板/库/`fp-lib-table`/`pm_gate/**`/`criteria/**`/`_shared/**`/闭环表；
未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode`；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 受审板 `6ff49da5678c2108` · SPEC rev-47 `9ba09cbc148d6836` · 图纸 `21e8891ea3fc4c06`
