# K2 · P4 · `Z4` **图纸整族刷新（图集 v10）验收件** · v1 · 2026-09-18

> 授权：监理 **#K2-23 §二-1**（Z4 权威源 **裁「整族刷新至 P4 真值（版本 bump）」**，驳回「以受审板为准」的拓扑用法；
> **放行**：按一次投递包 (k) §7 七步一次执行，12 项陈旧（D1–D12+C1）整族重生成，四载体一致后报**逐件前后 sha**）。
> 执行序位置：**优先序 4 · Step 4**（handoff inc81 §6-2；不被 G-ROOT-1/⑦ 阻塞）。
> 权威链（不可倒置）：真源 yaml `dd794c54…`/乙 `17d540f0…` → SPEC（canonical）→ **受审板（仅实测类字段的量测源）**。
> ENG（ARCHER）· 2026-09-18 · k2 `6cae23a`（动作前）· `_shared` `a266851`

## 0. 结论（四句）

1. **整族刷新已落件（v10）**：基线 = **SPEC rev-49** `b8f4a7cb67b575f0` + **受审板 l5** `6ff49da5678c2108`；`p3_drawings.json` `21e8891ea3fc4c06` → **`d6613754a7382c99`**，7 张 SVG 整族重出（4 张变、3 张逐字节未漂）。
2. **D1–D6、D8–D12 归零**（见 §2）；**D7 具名上报**（§3）：其「应然 58」是**原始 pad 块口径**，与 **R-1（#K2-18 §二-1）已裁**的「pad 计数 = 带号 pad；paste-only 钢网开窗不计」冲突 ⇒ 按可复现口径 `U1` = `49`，且**库↔板逐值一致**（非陈旧）。
3. **四方一致机检 34/34 PASS**（真源 ↔ SPEC rev-49 ↔ 受审板 ↔ 图集），**Z4 §3 五项未漂**（板框/铜层集/`nets_yaml`/SPEC 网名子集/`C6`）。
4. **同轮复算**：判定器 **PASS 7 / FAIL 3（PROVISIONAL，与动作前逐项同名）** · DRC **75 违反全 warning / 0 error / 0 unconnected** · 守恒 `tracks 4721 / vias 711 / zones 18 / nets 102 / pads 687`（见 §5-③ 一处具名差异）。**板未动**（受审板 sha 不变）。

## 1. 基线 + 逐件前后 sha（sha256 前 16）

| 件 | 前（v9 / 动作前） | **后（v10 / 落件）** |
|---|---|---|
| `k2/tools/k2_p3_drawings_v1.py` | `59ab211fc37c2a48` | **`eb7ea771a1645c01`** |
| `L3/drawings/p3_drawings.json` | `21e8891ea3fc4c06` | **`d6613754a7382c99`** |
| `L3/drawings/01_board_frame_and_holes.svg` | `096a61c81201123d` | **`ae84c110a4d27b0e`** |
| `L3/drawings/02_device_coordinates.svg` | `48f92c6b9dd16042` | **`caddcf3fbecebff3`** |
| `L3/drawings/03_corridor_occupancy.svg` | `e54c3b34782003db` | 同（**未漂**） |
| `L3/drawings/04_layer_assignment.svg` | `124c7c3b6bc72e68` | 同（**未漂**） |
| `L3/drawings/05_pour_strategy.svg` | `273910d6c820326e` | **`41453c89f007d59e`** |
| `L3/drawings/06_keepouts.svg` | `6ee00985779e7d76` | **`fb6d9b6aaffe187f`** |
| `L3/drawings/07_interface_pads_inframe.svg` | `0b10a71326cb3e99` | 同（**未漂**） |
| `L3/drawings/p3_placement_solution.json` | `faddc9de5519c5ec` | 同（**只读，未改写**） |
| `L3/drawings/README.md`（索引） | `a523265be3734597` | **`0b26d038dbb93115`** |

锚（**未动**）：受审板 `6ff49da5678c2108` · 设计源板 `fb07d25ac426ff84` · 冻结交付板 `d4e81f647be7f980` · 真源 `dd794c54f7ce7417` ·
errata-1 `17d540f058631a5e` · SPEC rev-47 `9ba09cbc148d6836` / rev-48 `11ad1da3818b379d` / rev-49 `b8f4a7cb67b575f0` ·
`project.yaml` `c887422e68ac5885` · `criteria/` `897e8bfde60e2cfe` + `7ce08757eff25557`（**只读**）。
**T-22 备份**：v9 全件 → `/tmp/opencode/backup-drawings-20260918T130750/`（逐件旧 sha 已在落盘日志打印）。

## 2. D1–D12 逐条归零（值 → 载体 → 权威）

| # | 载体 · 字段 | v9 现值 | **v10 值** | 权威 / 动作 |
|---|---|---|---|---|
| D1 | `criteria.D1_pinheader_interference.column_x` | `27.94` | `27.94` | SPEC rev-48 已对齐（G9 载体动作）；v10 保持并复检 |
| D2 | `SPEC.components.pin_headers.column_x/positions[].x` | — | `27.94` ×6 | rev-48 已落（本件只读核对，**未再改 SPEC**） |
| **D3** | `drawings.mounting_holes.positions.H3` | `(26.1,36.1)` | **`(45.10,75.10)`** | SPEC rev-49 `mounting_holes` 输入层（#K2-19 §一-3 L2 自裁） |
| **D4** | `criteria.C2_mounting_holes.per_hole[H3]` | `at=(26.1,36.1)`,`edge=1.5` | **`at=(45.10,75.10)`,`edge=2.30`** | 同上；**逐孔按框几何复算 == SPEC 声明**（H1/H2/H3/H4 = 1.5/1.8/2.3/1.5，`spec_match=True`） |
| **D5** | `devices.{J6,J9,J11,J12,J13}.board_pads` | `0,0,0,0,0` | **`2,4,4,2,4`** | 受审板 as-built（P4 已补 16 pad）；并与 lib 带号数逐件交叉核对 `5/5` |
| **D6** | `devices.U1.board_pads` | `33` | **`58`**（原始 pad 块口径） | 受审板 as-built（IN-4 已落）；同时登记 `board_pads_numbered=49` |
| **D7** | `criteria.C3….U1.footprint_pads` | `49` | **`49`（R-1 带号口径；`58` 登记于 `count_basis`）** | **具名上报**（§3） |
| **D8** | `pour_zones.{count,filled_count}` | `13 / 0` | **`10 / 10`** | 受审板实测（口径 = 有网非 keepout，`#K2-21 §一`）；`total_zones=18`、`keepout_zone_count=8` |
| **D9** | `criteria.C7_pour_zones_filled` | `9 / 0 / false` | **`10 / 10 / true`** | 同上；`pass=True` |
| **D10** | `criteria.C5b_board_side_esc_switches` | `count 4 / zones_all_allowed 4` | **`count 4 / zones_all_allowed 0`** | 受审板实测：4 区 `copperpour=not_allowed`、其余 4 开关 `allowed`（P4 施工项 IN-11 已落） |
| **D11** | `keepouts`（枚举） | `KO-1..7` 硬编码，与板 4 区不 1:1 | **SPEC 输入层 8 区**（`ESC_U6/ESC_J3/ESC_J4/ESC_J2` + `K2_HOLE_KEEPOUT_H1..H4`）**+ `KO-7` 规则承载** | SPEC `keepout_geometry.zones`；**与板实逐区 5 开关 + bbox 交叉核对全一致**（`all_match=true`） |
| **D12** | `drawings.spec`（自指） | `rev-25` `74f31d08a8be2f17` | **`rev-49` `b8f4a7cb67b575f0`** | `pm_gate.config`（`project.yaml::spec_name`） |
| C1 | `SPEC.layer_plan…nets` 含 `PWR_5V_KEY` | 19 网含之 | **未动（留待 ⑤ owner L1）** | owner ⑤ |

## 3. D7 **具名上报**（口径缺口，ENG 不自行择一）

**事实（实测，两载体各双口径互证）**

| 载体 | 原始 pad 块 | **带号 pad（电气）** | 无名 paste-only |
|---|---|---|---|
| 库 `ForgeOS.pretty/MCU_STM32G0_LQFP48.kicad_mod` | `58` | **`49`** | `9`（`F.Paste`，EP 3×3 钢网阵列） |
| 受审板 `U1` 实例 | `58` | **`49`** | `9`（`F.Paste`） |

⇒ 库 ↔ 板**两种口径逐值一致**（`58=58`、`49=49`）；`C3` 按 **R-1（#K2-18 §二-1）**「pad 计数 = 带号 pad；无名 paste-only 钢网开窗**不计**（无电气性）」⇒ `U1.footprint_pads = 49`。
**R-1 原文已点名 58**：「ENG 计 **49**（带号），而我朴素计数得 **50 / 58**」；R-1 判据 = 「按声明口径重算 = 件中数字」。
**结论**：Z4 清单 D7 的「应然 **58**」= **原始 pad 块口径**，与 R-1 已裁口径冲突；**Z4 清单 §3 记的「族内矛盾 33/49/58」是口径混用**（33 = 锚板 as-built 原始计数、49 = 库带号、58 = 板原始块数）——**非真缺陷**。
**本件处置**：`C3` 口径值保持 `49`（可复现、与 R-1 一致）；**同时**在 `C3.count_basis.per_footprint[U1]` 登记 `board_pads_raw=58`、`board_pads_numbered=49`、`blocks_total=58` ⇒ 「58」在件内可见且带具名口径，**未静默保留旧值**。
**请监理裁**：(a) 认可 D7 结案（口径混合声明件，非陈旧）＝ENG 现行动作；或 (b) 裁定 `C3` 比较口径改「原始 pad 块」⇒ ENG 再 bump（届时 `U1` 变 58，同时须重裁 `U1` 有向余量 22→31 与 E2 登记件）。

## 4. 验收：四方一致机检 + 未漂

**四方一致 34/34 PASS**（真源 yaml ↔ SPEC rev-49 ↔ 受审板 ↔ 图集；机检清单见 §6 复跑链）。关键项：

- `SPEC.mounting_holes / keepout_geometry` 自述 `board_sha16 == 6ff49da5678c2108`；图纸 `board_sha16` 同值。
- SPEC 铜区 `(net,layer)` 集 **==** 板实测 10 区（`GND×In1/In3/In6` + `In4{12V_IN×2,P3V3_AUX×2,P3V3×2,MCU_VDD×1}`），且 SPEC 声明 `filled=true` == 板 `10/10`。
- SPEC 孔位/孔径（H1–H4，Ø3.2）== 板实测；图纸逐孔边料 == SPEC 声明。
- 图纸器件集 == 真源 55 件（`at` 全非空）；`nets_yaml` = errata-1 `17d540f058631a5e`。
- declared keepout 8 区 ↔ 板 realized rule area **逐区开关 + bbox 一致**（`all_match=true`）。
- 排针 pad：板实 `2,4,4,2,4` == lib 带号数；排针 pad AABB 板实 == lib 几何 @`column_x=27.94`（`5/5`）。

**Z4 §3 五项未漂**：板框 `120×46 / x[23,143] y[33,79]` · 铜层集（`F/In1..In6/B`；GND `In1/In3/In6`、电源 `In4`、信号 `F/In2/In5/B`）· `nets_yaml` `17d540f058631a5e` · SPEC 网名子集（层名外文本无 K1 残留：`VOUT/U8` 0 命中）· `C6`（`pass=true`、`stale=[]`、`x_range_vs_L2-4` 逐值同 v9）。
**P3-4 余量**：最小 `0.08 @J9` 保持（= P4 须守 `27.94` 的既有结论，v10 复算一致）。

## 5. 附带发现（本件顺带登记，均已具名）

1. **坐标陈旧（Z4 清单未列）**：v9 的 `devices` 坐标由「锚板 + L2 落位解」合成，**3 件与受审板 as-built 不符** —— `C86 (32.4,36.0)→(31.55,58.85)`、`C85 (31.5,54.5)→(29.7,54.5)`、`R42 (86.6,59.55)→(93.3,61.55)`（v10 已刷新为板实；`solution_vs_board_drift` 逐件登记）。⇒ **图纸坐标权威自 v10 起 = 受审板 as-built**（落位解只留约束/来源，不覆写）。
2. **旧 README 索引 sha 勘误**：旧表把 `01` / `p3_drawings.json` 记为 `67614e57…` / `a6841cd7…`，与 v9 实际落件（`096a61c8…` / `21e8891e…`）不符；v10 README 已列「v10 现行 + v9 历史」双列。
3. **守恒 1 处差异（具名）**：`tracks 4721`（在库判定器 `non45_segments` 亦报 `0/4721`）vs 一次投递包 §6 期望 `4722`；`tracks 4721 + vias 711 = 5432 = GetTracks()` ⇒ 差异为**分类计数口径**（非板变动；板 sha 未变）。
4. **口径统一带来的连带刷新**：`pour_zones.count` 由「全部 zone（13）」改为「**有网非 keepout 铜区（10）**」，与判定器 `zone_filled` 口径（`#K2-21 §一`）一致；keepout 区另以 `keepout_zone_count=8` 登记，**未丢信息**。
5. **本会话 sha 记录勘误（具名，勿循）**：k2 首笔提交 `fa8ce60` 的**提交信息**把生成器 sha 记为 `15438b5fbc52a4e5`（= 中间草稿值，edit4 后测得）；**落件/入库实际工具 sha = `eb7ea771a1645c01`**（后续 edit5/6/7 改动所致），本件与本目录 README 已按实际值订正。**图集内容与工具一致性无影响**（`p3_drawings.json` 等均由 `eb7ea771a1645c01` 产出，T-38 两次同 sha 已验）。
6. **多层层 keepout 的 KiCad 断言**（工程踩坑）：`GetFilledPolysList()` 对「全 8 层 rule area」抛 C++ 断言（`map::at`）且 `try/except` **不捕获**；v10 生成器改按 `GetIsRuleArea()` 分流 ⇒ 出图硬化（同时避免"静默跳过"）。

## 6. 复跑链（确定性）

```bash
cd /home/fila/jqdDev_2025/ic_hw
# ① 生成器（沙箱；解与图同目录）→ 期望与落件同 sha：p3_drawings.json d6613754a7382c99
mkdir -p /tmp/opencode/p3x && cp k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_placement_solution.json /tmp/opencode/p3x/
K2_P3_OUT=/tmp/opencode/p3x AppDir/usr/bin/python3.11 k2/tools/k2_p3_drawings_v1.py
# ② T-38 确定性：连跑两次，8 件 sha 逐件相同（本会话已实跑）
# ③ 四方一致机检（34/34 详表 = 本会话 /tmp/opencode/inc82/four_way_report.json；下方为可复跑抽查，需 AppDir 解释器）
AppDir/usr/bin/python3.11 - <<'PY'
import json,hashlib,yaml,pcbnew
ROOT='/home/fila/jqdDev_2025/ic_hw'
sha=lambda p:hashlib.sha256(open(p,'rb').read()).hexdigest()[:16]
D=json.load(open(ROOT+'/k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_drawings.json'))
S=json.load(open(ROOT+'/k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-49.json'))
Y=yaml.safe_load(open(ROOT+'/k2/hw/data/k2_sch.errata-1.yaml'))
B=pcbnew.LoadBoard(ROOT+'/k2/hw/k2_v4_8L.l5.kicad_pcb')
fps={f.GetReference():f for f in B.GetFootprints()}
plac={p['ref'] for sh in Y['sheets'] for p in sh['placements']}
cu=[z for z in B.Zones() if z.GetNetname()]; ko=[z for z in B.Zones() if z.GetIsRuleArea()]
assert sha(ROOT+'/k2/hw/k2_v4_8L.l5.kicad_pcb')=='6ff49da5678c2108'
assert D['spec']['sha16']=='b8f4a7cb67b575f0' and D['board_sha16']=='6ff49da5678c2108'
assert set(D['devices'])==plac and len(plac)==55
assert len(S['keepout_geometry']['zones'])==8 and len(ko)==8 and len(cu)==10 and len(S['pd']['zone_defs']['board_realized_zones']['zones'])==10
assert D['keepout_realized_crosscheck']['all_match'] and D['criteria']['C7_pour_zones_filled']['pass']
assert (D['pour_zones']['count'],D['pour_zones']['filled_count'])==(10,10)
assert [D['devices'][r]['board_pads'] for r in ('J6','J9','J11','J12','J13')]==[2,4,4,2,4]
assert D['devices']['U1']['board_pads']==58 and D['devices']['U1']['board_pads_numbered']==49
assert D['mounting_holes']['positions']['H3']==[45.1,75.1]
print('四方一致抽查 PASS（详表见 K2-P4-Z4-DRAWINGS-V10-REFRESH-ACCEPTANCE §4）')
PY
# ④ 判定器（期望 PASS 7 / FAIL 3，PROVISIONAL）
python3 criteria/adjudicate.py --project k2 --board k2/hw/k2_v4_8L.l5.kicad_pcb --nets k2/hw/data/k2_sch.errata-1.yaml --sch-dir k2/hw/sch --pro k2/hw/k2_v4_8L.l5.kicad_pro --root k2
# ⑤ DRC（同名 pro；期望 75 warning / 0 error / 0 unconnected）
AppDir/bin/kicad-cli pcb drc --severity-all -o /tmp/opencode/drc.rpt k2/hw/k2_v4_8L.l5.kicad_pcb
```

## 7. 边界

**本件已改（均有 #K2-23 §二-1 授权）**：`k2/tools/k2_p3_drawings_v1.py`（P4 基线化：受审板量测源 + SPEC 输入层消费 + fail-closed 板 sha + T-41/T-22 写闸 + 口径登记）·
`L3/drawings/{p3_drawings.json,01,02,05,06_*.svg,README.md}`。
**未改**：SPEC 族（rev-47/48/49 原件逐字节不动）· 受审板/设计源板/冻结交付板 · 真源 yaml/errata-1 · `criteria/**`（仍只读、rev=1）· `project.yaml` ·
`_shared/**` · 生成器 `k2_gen_v5.py` · 模板/库/`fp-lib-table` · 闭环表；未建 `k2/pipeline.yaml`、未建 `k2/fab/**`；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode`；**未新增检查齿**（owner ②）。
**未闭（具名）**：D7（§3，待监理裁）· C1（⑤ owner）· ⑦ 库快照重建（G-ROOT-1 硬前置）· `pipeline.yaml` 安装（⑤ 硬前置）。
—— ENG（ARCHER）· 2026-09-18 · 图集 v10 · 生成器 `eb7ea771a1645c01` · 受审板 `6ff49da5678c2108`
