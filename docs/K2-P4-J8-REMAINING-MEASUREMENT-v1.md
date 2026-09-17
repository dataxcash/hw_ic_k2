# K2 · P4 · J-8 余项测量件（重叠 / 密度分布 / 关键间距）+ 对上一件 J-8b 断言的更正

| 项 | 值 |
|---|---|
| 阶段 | **P4**（计划 §②；未越阶段、未下单、未出交付 Gerber） |
| 依据 | 计划 §P4（全 J 类绿）、登记册 §C J-8（器件位置合理性：重叠/出框/密度分布/关键间距/固定孔/回避区，登记册注「本轮重点」）；#K2-20 §二（ENG 起草实现 → 监理复验） |
| 性质 | **ENG 只交测量**（无阈值/无裁定）；阈值与口径归监理 |
| 板态 | `k2/hw/k2_v4_8L.l5.kicad_pcb` = `37019705ef994ccc`（**未改**）· pro = `f68a5fb2f82bd02d`（**未改**） |
| 工具 | `k2/tools/k2_p4_j8_measure_v1.py` `2d77bc8b902f87fb`（纯 stdlib，只读） |

## 1. 更正登记（对 `K2-P4-GATE-COVERAGE-AND-OPTION-A-v1.md` §1 的 J-8b 行）
- 旧断言（本会话前一轮）：「J-8b 器件不重叠 —— 由 DRC `courtyards_overlap`（error，现 0 条）经 J-1/`drc_errors` 覆盖」。
- **更正**：本板 **59 件中 40 件无 courtyard**（cross-check：令 `missing_courtyard=warning` 的 /tmp DRC 副本实跑 = **40 条**，refs 与无 courtyard 件逐一相同）。
  ⇒ 对这 40 件，`courtyards_overlap` **结构上不可判**；且实测 **6 个 AABB 候选重叠对中，两侧皆有 courtyard 的 = 0** ⇒ 对**全部候选**都不可判。
- 修正后的诚实表述：**「器件不重叠」在本板目前无法宣称已由判据验证**；下表给出 courtyard-free 的**上界**测量，供监理择口径。

## 2. J-8b 器件重叠（测量，courtyard-free + courtyard 交叉）
| 项 | 实测 |
|---|---|
| courtyard 覆盖 | **19 有 / 40 无**（courtyard 层名 = `F.CrtYd`/`B.CrtYd`；全板 44 个 `F.CrtYd` 图元集中在 19 件） |
| 封装 AABB 重叠候选（铜+图形外接框，**上界**） | **6 对**：`U4↔D2`(2.5×1.55mm) · `D2↔U2`(0.06×2.605) · `C86↔U2`(1.5×0.7) · `L1↔U2`(3.5×0.005) · `U1↔J13`(1.65×0.44) · `U1↔J9`(1.65×1.5) |
| 其中**两侧皆有 courtyard**（可用 DRC 判真重叠） | **0 对** ⇒ DRC `courtyards_overlap` 对本板 6 个候选**均不可判** |
| **跨封装 pad 交叠**（铜级，逐层 AABB） | **同网 0 对 · 异网 0 对** ⇒ **电气级重叠 = 0**（无铜级交叠；与 `drc_errors=0` 一致） |
> 口径提示（归监理）：欲令 J-8b 真可判，须 (i) 补 40 件的 courtyard（即 W-7 `missing_courtyard` 改「修」）后由 DRC 判，或 (ii) 明示采纳「pad/图形 AABB 上界」口径。ENG 不择一。

## 3. J-8d 密度分布（测量）
| 网格 | 峰值 | 峰值格坐标 | 分布 |
|---|---|---|---|
| 封装 / 10mm | **5 件/格** | (90,60) 与 (50,60) 各 5；次 (90,40)=4 | 直方图 {1:11, 2:6, 3:6, 4:2, 5:2} |
| pad / 10mm | **141 pad/格** | (90,50)=141；次 (80,50)=111 | — |
> 阈值 `thresholds.density_max_per_10mm_cell` 现为 `null` ⇒ `density_and_spacing` fail-closed；本表为其取值依据（来源 M-12「三横带 19–27%」复现不出，已在册）。

## 4. J-8d 关键间距 / 工艺极限（实测；关键间距用 DRC 引擎 bracket）
方法：在 `/tmp` 复制 pro 并**仅上调** netclass/`min_clearance`，用 `kicad-cli drc` 实跑计数（仓库 pro/板逐字节未动）：

| 阈（mm） | clearance 违规数 | 含义 |
|---|---|---|
| 0.100（板规现值） | **0** | 板侧达标（≥0.100） |
| 0.105 | 3 | 实际 0.1000 ⇒ **实达最小间距 = 0.100mm** |
| 0.110 / 0.115 / 0.120 / 0.150 / 0.200 | 3 / 5 / 9 / 19 / 198 | 单调 ⇒ 0.100 即全板最小值 |

- 最紧处样本：`[I2C1_SCL]` F.Cu @ (99.915, 66.6)，实际 0.1000mm。
- ⇒ **本板实达最小铜间距 = 0.100mm，恰等于声明下限（min_clearance / netclass 0.1）= 零余量**。

| 工艺极限（板实达） | 实达值 | 板规阈值 | 余量 |
|---|---|---|---|
| 最小线宽 | **0.16mm** | 0.09 | +0.07（有） |
| 最小过孔直径 | **0.35mm** | 0.35 | **0** |
| 最小过孔钻孔 | **0.20mm** | 0.20（min_through_hole） | **0** |
| 最小孔环 | **0.075mm** | 0.075 | **0** |
| 最小孔钻（THT/NPTH） | 0.80mm | — | 孔 20 个（H1–H4 Ø3.2 NPTH + 排针） |
> ⇒ 过孔/钻孔/孔环三项**全部压在声明下限**；若监理为 J-8d/JLC HDI 设「留余量」口径，本板不满足；若采「≥ 声明下限」口径，本板达标。**ENG 不择一。**

## 5. 复跑
```bash
cd /home/fila/jqdDev_2025/ic_hw
python3 k2/tools/k2_p4_j8_measure_v1.py --json /tmp/opencode/j8.json        # §2/§3/§4 工艺极限
# §4 关键间距 bracket（/tmp pro 副本；仓库 pro 不动）
python3 - <<'PY'
import json, subprocess, collections
src=json.load(open('k2/hw/k2_v4_8L.l5.kicad_pro'))
for T in (0.100, 0.105, 0.110, 0.115, 0.120, 0.150, 0.200):
    d=json.loads(json.dumps(src)); d['board']['design_settings']['rules']['min_clearance']=T
    for c in d.get('net_settings',{}).get('classes',[]): c['clearance']=T
    json.dump(d, open('/tmp/opencode/clr/K2CLR.kicad_pro','w'))
    subprocess.run(['AppDir/bin/kicad-cli','pcb','drc','--format','json','--severity-error',
        '--severity-warning','--output','/tmp/opencode/clr/drc.json','/tmp/opencode/clr/K2CLR.kicad_pcb'],capture_output=True)
    v=json.load(open('/tmp/opencode/clr/drc.json'))['violations']
    print(T, collections.Counter(x['type'] for x in v).get('clearance',0))
PY
```
（`/tmp/opencode/clr/` 需含同名 pro/板 + `fp-lib-table` + `lib/ForgeOS.pretty` 链接，T-8 口径。）

## 6. 边界
只读测量 + `/tmp` 导出；板（`37019705ef994ccc`）/ pro（`f68a5fb2f82bd02d`）/ 冻结件 `d4e81f64…` / SPEC / 真源 / 生成器 / `criteria/` **逐字节未动**；
未安装任何判据；未新增判据维度；未派 WORKER；未写 `.omo/supervision/**`；未下单、未出交付 Gerber。
本件为**测量**，不含任何阈值或裁定。

—— ENG（ARCHER）· 2026-09-18
