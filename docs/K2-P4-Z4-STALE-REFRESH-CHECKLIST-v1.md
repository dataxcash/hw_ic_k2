# K2 · P4 · `Z4` **陈旧读数刷新核对表**（L3 图纸族 + SPEC；全字段扫描，非抽样）· v1 · 2026-09-18

> 缘起：handoff inc59 §6-3-(h)「为 §5-1（Z4 权威源）预置『SPEC/图纸刷新对照表』：把陈旧读数 ↔ 应然值 ↔ 载体位置逐条列成可执行 diff 清单」。
> 本会话**无监理放行** ⇒ ENlegal 面；**只读扫描**，仓库零载体改动（仅新增本证据件）。
> 锚：SPEC rev-47 `9ba09cbc148d6836` · L3 图纸 `21e8891ea3fc4c06` · 受审板 `6ff49da5678c2108` · 真源 `dd794c54f7ce7417` · errata-1 `17d540f058631a5e`。

## 0. 结论（四条）

1. **全字段扫描（非抽样）得 12 项陈旧 + 4 项一致**（§2/§4）。陈旧项**不止**先前已知的 3–6 例；`drawings.devices` 的 pad 数即 **6 件全错**（先前未被点出）。
2. **L3 图纸族内部自相矛盾（关键结构发现）**：同一族内对同一事实给出**三个不同值** ——
   ① `column_x`：图纸 `criteria.D1…= 27.94` ↔ SPEC `components.pin_headers= 26.5`；
   ② `U1` pad 数：`devices.U1.board_pads = 33` ↔ `criteria.C3….footprint_pads = 49` ↔ 板实 **58**；
   ③ 铜区：`pour_zones = {count:13, filled:0}` ↔ `criteria.C7 = {count:9, filled:0}` ↔ 板实 **10/10**。
   ⇒ **结论：图纸族必须「由同一基线整族重生成」，不得逐项打补丁**（逐项修只会把矛盾留在族内）。
3. **权威分三类 ⇒ Z4 裁定后即可分头执行**：**A 类 8 项**（权威＝既有独立裁定/修复决定 ⇒ 纯版本化传播，**非** C-1 自证）· **B 类 4 项**（板为权威、无独立成文应然 ⇒ 需 Z2「以板为准」口径一并裁）· **C 类 1 项**（`PWR_5V_KEY` ⇒ ⑤ owner 裁定，inc59）。
4. **刷新的实际收益**：只有整族刷新后，「SPEC ↔ 图纸 ↔ 板 ↔ 真源」四方才自洽，`criteria/manifest.k2.yaml` 的 `not_countersigned:false` 签认才有意义（否则是给**陈旧应然值**签认）。

## 1. 扫描方法（确定性；全字段，非抽样）

对 `SPEC_k2_v4.spec-rev-47.json` 与 `p3_drawings.json` 的**每个叶级字段**做三向比对：① 与受审板实测（pad 数/层/框/孔/keepout/铜区）② 与真源（网集/节点）③ 与 `project.yaml`（`spec_name`）。凡 SPEC/图纸**自称是"实测/板实"**的字段（`board_pads`/`filled`/`count`/`per_hole`/`footprint_pads`）必须与板一致，否则记为陈旧。
**判定口径**：`写下来源是设计意图的字段`（`stackup`/`impedance`/`corridors`/`net_classes`）以 SPEC 自身为权威，**不**与板比对（避免反向污染）；只比对「自称实测」类字段。

## 2. 陈旧清单（12 项，逐条可执行）

| # | 载体 · 字段 | 现值 | **应然值** | 权威 | 类 | 动作 |
|---|---|---|---|---|---|---|
| **D1** | `SPEC.components.pin_headers.column_x` | `26.5` | **`27.94`** | L2-3 裁定 + #K2-21 §二 守恒闸（图纸 `D1_pinheader_interference` / `C4` 已按 27.94 复算，min 余量 0.08 @`J9`） | **A** | SPEC bump |
| **D2** | `SPEC.components.pin_headers.positions[*].x` | `26.5` ×5 | **`27.94`** ×5 | 同上 | **A** | SPEC bump |
| **D3** | `drawings.mounting_holes.positions.H3` | `(26.1,36.1)` | **`(45.10,75.10)`** | #K2-19 §一-3（H3 = L2 热机械 = 自裁域） | **A** | 图纸重生成 |
| **D4** | `drawings.criteria.C2_mounting_holes.per_hole[H3]` | `at=(26.1,36.1)`, `edge_material=1.5` | **`at=(45.10,75.10)`, `edge_material=2.30`** | 同上（`K2-P4-H3-RESOLVE-AND-12V-FEED-v1.md` §2） | **A** | 同上 |
| **D5** | `drawings.devices.{J6,J9,J11,J12,J13}.board_pads` | `0,0,0,0,0` | **`2,4,4,2,4`**（合计 16） | P4 落件已补 16 pad（G-ROOT-1 载体侧尚未修 ⇒ 见 §5） | **A** | 同上 |
| **D6** | `drawings.devices.U1.board_pads` | **`33`** | **`58`** | IN-4 修复决定（U1 补齐 34..48 + EP(49)） | **A** | 同上 |
| **D7** | `drawings.criteria.C3_pad_eq_symbol_pins.U1.footprint_pads` | **`49`** | **`58`** | 同上（且与 D6 的 33 **族内矛盾**） | **A** | 同上 |
| **D8** | `drawings.pour_zones.{count,filled_count}` | `13 / 0` | **`10 / 10`** | 板（口径＝#K2-21 §一「有网非 keepout」） | **B** | 图纸重生成（须先裁 Z2） |
| **D9** | `drawings.criteria.C7_pour_zones_filled.{count,filled,pass}` | `9 / 0 / false` | **`10 / 10 / true`** | 同上（#K2-21 §一 口径修正：9→10） | **B** | 同上 |
| **D10** | `drawings.criteria.C5b_board_side_esc_switches.{count,zones_all_allowed}` | `4 / 4`（全 allowed） | **4 区 `copperpour: not_allowed`**（其余 allowed） | 板 | **B** | 同上（Z2） |
| **D11** | `drawings.keepouts`（`KO-5`/`KO-6` 各 `count=1`；`KO-7` `count=4`） | 与板 4 个 F.Cu 区**不 1:1** | **板 4 区**（`ESC_U6/ESC_J3/ESC_J4/ESC_J2`，bbox 实测见 inc55 表 B） | 板 | **B** | 同上（Z2） |
| **D12** | `drawings.spec`（自指） | `SPEC_k2_v4.spec-rev-25.json` `74f31d08a8be2f17` | **`rev-47` `9ba09cbc148d6836`**（`project.yaml::spec_name`） | 配置 | **A** | 图纸重生成 |
| **C1** | `SPEC.layer_plan.low_speed_nets.nets` 含 `PWR_5V_KEY` | 19 网含之 | **待 ⑤ owner 裁定**（inc59） | L1/电源域口径 | **C** | 待裁后同步 |

## 3. 族内自相矛盾（三组，证明「必须整族重生成」）

| 事实 | 矛盾 A | 矛盾 B | 外部真值 |
|---|---|---|---|
| `column_x` | `drawings.criteria.D1_pinheader_interference.column_x = **27.94**`（且 `C4` 的 min 余量 0.08 @`J9` 即按 27.94 复算） | `SPEC.components.pin_headers.column_x = **26.5**` | 板 `fp.at.x = 27.94`（5/5） |
| `U1` pad 数 | `drawings.devices.U1.board_pads = **33**` | `drawings.criteria.C3….footprint_pads = **49**` | 板 = **58** |
| 铜区 | `drawings.pour_zones = **13**（filled 0）` | `drawings.criteria.C7 = **9**（filled 0）` | 板 = **10**（filled 10/10） |

⇒ 三组均**族内不一致** ⇒ 逐项打补丁会留下「同一族两个真相」；**应以 rev-48 SPEC + P4 受审板为唯一基线整族重生成**。

## 4. 一致项（**无需改**；列出以防误刷）

| 项 | 值 | 核对 |
|---|---|---|
| `drawings.board_frame` | `x[23,143] y[33,79]` = 120×46 | 板实测一致 ✓ |
| 铜层集合/角色 | 8 层（`F/In1..In6/B`）；`gnd_planes=In1/In3/In6`、`power=In4`、`signal=F/In2/In5/B` | 板 ✓、`SPEC.stackup` ✓ |
| `drawings.nets_yaml` | `errata-1` `17d540f058631a5e` | 与 `project.yaml` 一致 ✓（随 §5-8 裁定可能变） |
| SPEC 5 处网名清单 | 全为真源网集子集（`low_speed_nets` 19 网等） | **无其他 K1 残留**；K1 节点名（`U8/VOUT`…）在 SPEC/图纸 **0 命中** ✓ |
| `drawings.criteria.C6_corridor_basis` | `pass:true`、`bases_found_in_spec:[]` | 已由 IN-10/rev-25 回写 ✓ |

## 5. 刷新顺序与验收（Z4 裁定后一次可做）

```
Step 0  裁 Z4 权威源：①「刷新 SPEC/图纸至 P4 后真值」 或 ②「明示以受审板为准」（并裁是否触 C-1）
Step 1  裁 Z2 口径（B 类 4 项）：keepout 枚举/层集/开关以板为准？是否补 KO-7 实体 zone？
Step 2  SPEC bump → rev-48：D1/D2（column_x/positions=27.94）；C1 视 ⑤ 裁定
Step 3  图纸**整族重生成**（新 rev）于同一基线（rev-48 SPEC + 受审板）：D3–D12 一次归零
Step 4  验收：SPEC↔图纸↔板↔真源**四方一致**（逐项机检）+ 判据复算（期望 19P/0F，两维阈值由监理给）
Step 5  （仅 Step 4 全绿后）`criteria/manifest.k2.yaml` 方可 `not_countersigned:false` 签认
```
**风险与依赖**：D5/D6/D7 的「应然值」依赖 **G-ROOT-1/⑦** 的载体侧裁定（生成器去锚板依赖 + 库/板名集）；若 G-ROOT 未放行，图纸即使刷新也只反映**当前板实**，生成器仍会产出旧值 ⇒ **Z4 刷新与 G-ROOT 放行宜同批**（否则刷了又漂）。

## 6. 复跑（每处实测；仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw
python3 - <<'PY'
import json,re,pathlib
S=json.load(open('k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-47.json'))
D=json.load(open('k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_drawings.json'))
print("D1 SPEC.column_x =",S['components']['pin_headers']['column_x'])
print("D1' drawings.D1.column_x =",D['criteria']['D1_pinheader_interference']['column_x'])
print("D3 drawings.H3 =",D['mounting_holes']['positions']['H3'])
print("D4 C2 H3 =",[h for h in D['criteria']['C2_mounting_holes']['per_hole'] if h['hole']=='H3'])
print("D5 devices.board_pads =",{r:D['devices'][r]['board_pads'] for r in ('J6','J9','J11','J12','J13')})
print("D6/D7 U1 =",D['devices']['U1']['board_pads'],"vs C3:",[x for x in D['criteria']['C3_pad_eq_symbol_pins']['literal_mismatch'] if x['ref']=='U1'])
print("D8/D9 pour =",D['pour_zones']['count'],D['pour_zones']['filled_count'],"| C7:",D['criteria']['C7_pour_zones_filled']['count'],D['criteria']['C7_pour_zones_filled']['filled'])
print("D10 C5b =",D['criteria']['C5b_board_side_esc_switches']['count'],D['criteria']['C5b_board_side_esc_switches']['zones_all_allowed'])
print("D12 drawings.spec =",D['spec'])
PY
# 板侧对照（U1=58 / 排针 16 / 10 铜区 10 填充 / H3=(45.1,75.1) / column_x=27.94）：
#   见 inc55 §2–§3 的解析配方（tokenizer + kids/one），或本件 §6 的落件测量件
```

## 7. 边界

本件**只读扫描**：未改 SPEC/图纸/板/pro/真源/生成器/模板/库/`fp-lib-table`/`pm_gate/**`/`criteria/**`/`_shared/**`；
未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode`；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · SPEC rev-47 `9ba09cbc148d6836` · 图纸 `21e8891ea3fc4c06` · 受审板 `6ff49da5678c2108`
