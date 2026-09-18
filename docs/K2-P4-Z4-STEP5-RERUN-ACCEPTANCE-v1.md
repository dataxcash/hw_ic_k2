# K2 · P4 · `Z4` **Step 5 复跑验收**（A 块逐值 + B 块 emit/KiCad 级）· v1 · 2026-09-18

> 授权：**#K2-23 §二-1**（Z4 放行 = 一次投递包 (k) §7 **七步一次执行**）· 执行序 = handoff inc81 §6-3「优先序 4 · Step 5」。
> 前置：Step 4（图集 v10）已落件（k2 `8dc51e7`；本件 A 块即对该落件复扫）。
> 红线（本件遵守）：冻结件不改 · `criteria/**` ENG **只读** · 未获批不改生成器/SPEC/原理图 · 禁派 WORKER · 临时仅 `/tmp/opencode` · 未新增检查齿。
> ENG（ARCHER）· 2026-09-18 · k2 `8dc51e7` · `_shared` `a266851`

## 0. 结论（三句）

1. **A 块（Z4 逐值比对）PASS**：对**落件 v10 图集**全项机检 = **19/20 无陈旧 · `stale=[]`**；余 1 项 = `C1`（`PWR_5V_KEY`，**L1 待 ⑤ owner**，非陈旧）；**族内矛盾三组全部消解**（三者同值/双口径互证）。
2. **B 块（emit / round-trip / KiCad 级）PASS**：生成器 `k2_gen_v5.py` `796bd7a48947ec7c` 两次运行**逐字节同 sha**（T-38）；自检 **S1/S2/S4/S5/S6/S8 PASS**；`G10 输入层 keepout=8 copper=10 npth=4`（**源 = SPEC 输入层，不读板**）；KiCad 级 `zones=18 / keepout=8 / NPTH=4`、`ZONE_FILLER` 后 **`zone_filled 10/10`**、`keepout_active=True`、存盘重载 18/10/8 + 10/10 + NPTH 4 全保持。
3. **判据复算（期望 19P/0F）**：**未执行，fail-closed 停等** —— 在库判据仍 `manifest.k2.yaml` `7ce08757eff25557`（**rev=1，9 维 enabled，`not_countersigned:true`**）⇒ 复算结果只能是 **PASS 7 / FAIL 3**；**canonical 19 维装件 = `criteria/**` 写入 = owner 唯一通道**（`criteria-ownership §二`；红线「判据 ENG 只读」），**ENG 不写**。**请 owner/监理装件**（构成与阈值 `#K2-23 §二-9` 已裁，见 §3）。

## 1. A 块 · Z4 逐值比对（机检；对落件图集 `d6613754a7382c99`）

装置：只读脚本（内联 §4-①），对 `p3_drawings.json` / SPEC rev-49 / 受审板 / 真源四方逐项比对；`stale = (现值 != 真值)`。

| # | 项 | 结果 | 现值 |
|---|---|---|---|
| D1 | `SPEC.pin_headers.column_x` | OK | `27.94` |
| D2 | `SPEC.pin_headers.positions[*].x` | OK | `27.94` ×5 |
| D3 | `drawings.mounting_holes.positions.H3` | OK | `[45.1, 75.1]` |
| D4 | `drawings.criteria.C2.per_hole[H3] at/edge` | OK | `[45.1,75.1] / 2.3` |
| D4b | `criteria.C2` 逐孔边料 == SPEC 声明 | OK | H1..H4 = `1.5/1.8/2.3/1.5` 全 match |
| D5 | `devices.{J6,J9,J11,J12,J13}.board_pads` | OK | `2,4,4,2,4` == 板实 |
| D6 | `devices.U1.board_pads`（原始口径） | OK | `58` == 板实 |
| D6b | `devices.U1.board_pads_numbered`（R-1 口径） | OK | `49` == 板实带号 |
| D7 | `C3.U1.footprint_pads` == 库带号（R-1） | OK | `49`（口径缺口已具名上报，见 v10 验收件 §3） |
| D7b | `C3.count_basis` 登记原始块 `58` | OK | `blocks_total=58 / board_pads_raw=58`（**口径可见，非静默**） |
| D8 | `drawings.pour_zones.count/filled_count` | OK | `10/10` == 板实 |
| D9 | `drawings.criteria.C7` | OK | `10/10/true` == 板实 |
| D10 | `drawings.criteria.C5b.count/zones_all_allowed` | OK | `4/0` == 板实（4 区 `copperpour=not_allowed`） |
| D11 | `drawings.keepouts` 声明名称集 == 板 rule area 名称集 | OK | 8 区逐名一致 |
| D11b | declared ↔ realized 开关/bbox 交叉核对 | OK | `all_match=true` |
| D12 | `drawings.spec` == `project.yaml::spec_name` | OK | `rev-49 b8f4a7cb67b575f0` |
| C1 | `SPEC.layer_plan` 含 `PWR_5V_KEY` | **PEND（非陈旧）** | L1 待 ⑤ owner |
| F1 | 族内矛盾① `column_x`：图纸 D1 == SPEC == 板 | OK | `27.94` 三者同 |
| F2 | 族内矛盾② `U1` pad：双载体双口径互证 | OK | `58=58`（块）& `49=49`（带号） |
| F3 | 族内矛盾③ 铜区：图纸 `pour` == 图纸 `C7` == 板 | OK | `10` 三者同 |

⇒ **`stale=[]`；19/20 无陈旧 + 1 项 pending(⑤)**。报告件：`/tmp/opencode/inc83/z4_scan_report.json`。

## 2. B 块 · 生成器 emit / round-trip / KiCad 级

| 验证 | 结果 |
|---|---|
| 生成器 sha | `k2/tools/k2_gen_v5.py` `796bd7a48947ec7c`（未改） |
| 输入 | SPEC **rev-49** `b8f4a7cb67b575f0` + 真源 **乙** `errata-1` `17d540f058631a5e` |
| T-38 确定性（两次运行） | `g1.kicad_pcb` == `g2.kicad_pcb` = `1252bd2e74957d82`；`g1.json` == `g2.json` = `960a6e354d143c72` |
| 自检 | **S1 焊盘重叠 / S2 refdes / S4 缺失器件 / S5 坐标范围 / S6 网表一致 / S8 排针坐标冻结 = 6/6 PASS**（生成器自报口径 = 6 项，非 8；D-6 声称修正后一致） |
| G10 输入层 | `keepout=8 copper=10 npth=4`，**源 = SPEC 输入层（不读板）** |
| KiCad 级（LoadBoard `g1.kicad_pcb`） | `zones=18`（`keepout=8` / `copper=10`）· `NPTH=4` footprint × 4 pad，drill `Ø3.2` |
| 填充（`ZONE_FILLER`） | 填充前 `0/10` → 填充后 **`10/10`**；`keepout_active = True`（每区 ≥1 非 `allowed`） |
| 存盘 + 重载 | `g1_filled.kicad_pcb` 重载：`zones 18 / copper 10 / keepout 8 / filled 10/10 / NPTH 4` 全保持 |
| 已知未闭（非本步失败） | 生成器**器件侧 pad 几何仍继承旧锚板**（`器件数 42 / pads 262`；`U1` 33→G-ROOT-1 未做）⇒ **产物不得替代受审板**（旁证②，待 **⑦** 后才可改）；G-ROOT-1 未闭 |

## 3. 判据复算：**fail-closed 停等**（请 owner/监理装件）

- 在库判据：`criteria/adjudicate.py` `897e8bfde60e2cfe`（只读）· `criteria/manifest.k2.yaml` `7ce08757eff25557`（**rev=1**；enabled = `zone_filled / device_has_pads / drill_count / net_declared_realized / pin_map_complete / non45_segments / refdes_sets_equal / pipeline_present / verdict_schema`；`not_countersigned: true`）。
- 该表复算必然是 **PASS 7 / FAIL 3**（见 Step 4 同轮复算）：`zone_filled 10/18`（口径=全部 zone，未按 `#K2-21 §一` 修正）· `refdes_sets_equal 图 55/板 59`（原理图侧，待原理图补 H1..H4 或口径澄清）· `pipeline_present`（`hw/sch` 未覆盖，`k2/pipeline.yaml` 未装且硬前置为 ⑤）。
- **19P/0F 的前置**：#K2-23 §二-9 已裁「canonical = v4 族命名（`manifest.k2.v4.yaml` / `control-v4.yaml`）；**18 维全 enabled + `rule_severity_manifest` 为无条件第 19**；别名钉死；**安装后锚 rev=2**」，两维阈值亦已给（`density_and_clearance enable(10/frame_origin/8/0.100)` · `ref_plane_continuity enable(高速网集/1.0)`）。
- 但**装件动作 = 写 `criteria/**` = owner 唯一通道**（`criteria-ownership §二`）+ 红线「判据 ENG 只读」⇒ **ENG 不写、不自判**。**请 owner/监理按 §二-9 装件并给新 sha**；装毕 ENG 立即可复算（脚本与期望值已在手）。
- 候选件（ENG 侧已备，供装件参考，**未入库为主判据**）：`k2/docs/drafts/p4-criteria-19dim-canonical-v1/` · `k2/docs/drafts/p4-j8-density-clearance-v1/manifest.k2.v4.yaml`。

## 4. 复跑链（确定性；只读）

```bash
cd /home/fila/jqdDev_2025/ic_hw; export SHARUN=$PWD/AppDir/sharun
# ① A 块（Z4 逐值扫描；需 AppDir 解释器）——期望 19/20 无陈旧 · pending=C1 · stale=[]
AppDir/usr/bin/python3.11 - <<'PY'
import json,hashlib,yaml,pcbnew
R='/home/fila/jqdDev_2025/ic_hw'
D=json.load(open(R+'/k2/pm_gate/artifacts/k2_v4/L3/drawings/p3_drawings.json'))
S=json.load(open(R+'/k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-49.json'))
B=pcbnew.LoadBoard(R+'/k2/hw/k2_v4_8L.l5.kicad_pcb'); fps={f.GetReference():f for f in B.GetFootprints()}
cu=[z for z in B.Zones() if z.GetNetname()]; ko=[z for z in B.Zones() if z.GetIsRuleArea()]
assert S['components']['pin_headers']['column_x']==27.94
assert D['mounting_holes']['positions']['H3']==[45.1,75.1]
assert [D['devices'][r]['board_pads'] for r in ('J6','J9','J11','J12','J13')]==[2,4,4,2,4]
assert D['devices']['U1']['board_pads']==58 and D['devices']['U1']['board_pads_numbered']==49
assert (D['pour_zones']['count'],D['pour_zones']['filled_count'])==(len(cu),10)
assert D['criteria']['C7_pour_zones_filled']['pass'] and D['keepout_realized_crosscheck']['all_match']
assert {k['id'] for k in D['keepouts'] if k.get('kind')=='keepout_zone'}=={z.GetZoneName() for z in ko}
assert D['spec']['sha16']=='b8f4a7cb67b575f0'
print('A 块抽查 PASS（详表见 /tmp/opencode/inc83/z4_scan_report.json）')
PY
# ② B 块（生成器 + KiCad 级）
K2_OUT_PCB=/tmp/opencode/inc83/g1.kicad_pcb K2_OUT_JSON=/tmp/opencode/inc83/g1.json python3 k2/tools/k2_gen_v5.py
AppDir/usr/bin/python3.11 -c "
import pcbnew;b=pcbnew.LoadBoard('/tmp/opencode/inc83/g1.kicad_pcb');print('zones',len(b.Zones()))
f=pcbnew.ZONE_FILLER(b);f.Fill(b.Zones());pcbnew.SaveBoard('/tmp/opencode/inc83/g1_filled.kicad_pcb',b)"
# 期望 zones 18 / NPTH pads 4 / fill 后 zone_filled 10/10 / keepout_active PASS
# ③ 判据复算（**待装 canonical 19 维后**方有意义；当前在库表仍 7P/3F）
python3 criteria/adjudicate.py --project k2 --board k2/hw/k2_v4_8L.l5.kicad_pcb --nets k2/hw/data/k2_sch.errata-1.yaml --sch-dir k2/hw/sch --pro k2/hw/k2_v4_8L.l5.kicad_pro --root k2
```

## 5. 边界 + 未闭

**本件未改任何载体**（零仓库写入）：只读复跑 + `/tmp/opencode/inc83/**` 仪器（易失）。
**未闭（具名）**：`C1`/⑤（L1 owner）· `D7` 口径裁定（监理）· **canonical 19 维装件 + 锚 rev=2**（owner 唯一通道）· `pipeline_present`（`k2/pipeline.yaml` 未装，硬前置 ⑤）· `refdes_sets_equal`（原理图侧）· **G-ROOT-1/⑦**（生成器器件侧 pad 几何）· 闭环表（#K2-22 §三）。
fail-closed：**P4 未全绿不下单、不出交付 Gerber**。
—— ENG（ARCHER）· 2026-09-18 · 图集 v10 `d6613754a7382c99` · 生成器 `796bd7a48947ec7c`
