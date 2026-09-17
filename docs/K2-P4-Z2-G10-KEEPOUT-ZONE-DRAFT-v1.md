# K2 · P4 · `Z2` 候选口径 **G10 keepout/zone 生成段草案**（「以板为准」；含回归自证 + KiCad 级验证）· v1 · 2026-09-18

> 缘起：handoff inc61 §6-3-(j)「`Z2` 候选口径 `/tmp` 预演：按『以板为准』生成 keepout/zone 段草案（G10 Step 5 段），**仅 `/tmp`、不落件**」。
> 本会话**无监理放行** ⇒ ENlegal 面；**仓库零载体改动**（仅新增本证据件）。锚：受审板 `6ff49da5678c2108` · l5 pro `d5e0ca067a7b585e`。
> 草案装置（`/tmp`，易失）：`/tmp/opencode/inc62/g10_zone_keepout_draft.py` **`8a31ad20ec520e32`** · `zones_input.json` **`2edb6eec2d600494`**（18 区数据块）· `board_filled.kicad_pcb` `26dc63a598be3d3e` · emit 产物 `zones_emit.txt` **`53b47d754916c6c2`**（**两次 emit 同 sha ⇒ 确定性 ✓**，T-38）。

## 0. 结论（五条）

1. **草案已成件（`/tmp`）**：① **候选输入层数据块**（18 区＝8 keepout + 10 有网铜区，值取自受审板实测）② **生成段** `emit_zone()`
   （产出 KiCad `(zone …)` s-expr；填充仍由既有「出图前 `ZONE_FILLER`」承担）。
2. **回归自证 PASS**：`emit → 解析回比` 数据块 ⇒ **18 区、0 字段差异**（比对项：`kind`/`layers`/`name`/`net`/`connect_pads`(+clearance)/`min_thickness`/`priority`/keepout 五开关/**polygon 逐顶点**）。
3. **KiCad 级验证 PASS**：把原板 18 区**剥离** → 插入 emit 结果 → `pcbnew.LoadBoard` **成功（18 区）** → `ZONE_FILLER.Fill()` → 量测：
   `keepout_active` **PASS**（8 keepout、**0 个全 allowed**）· `zone_filled` **10/10 PASS** · 铜网集 `{12V_IN,GND,MCU_VDD,P3V3,P3V3_AUX}` 与原板**逐名一致**。
   ⇒ 产出**语法有效、可填充、结构等价**；且**不放松**任何已裁维度。
4. **口径依赖（`Z2` 未裁）**：数据块**取自受审板**；「以板为准」须监理裁定（并说明是否触 C-1）。
   **若采纳，正确落法是「写输入层」**：把本数据块写入 SPEC（如 `keepout_geometry.zones` / `pd.zone_defs.board_realized_zones`），生成器**消费输入层、不读板**
   ⇒ 避免「判据真源＝被验对象」（C-1）。**ENG 未写 SPEC、未落件。**
5. **不新增检查齿（owner ②）**：收敛仍复用已裁维度 `keepout_active`（草案）· `zone_filled`（冻结，口径＝有网非 keepout）· `drill_count`（冻结）；本件**未**定义新阈值/新维度。

## 1. 候选输入层数据块（18 区；值＝受审板实测）

**keepout（8）**

| name | layers | bbox (x0,y0,x1,y1) | 尺寸 | 顶点数 | `not_allowed` 开关 |
|---|---|---|---|---|---|
| `ESC_U6` | F.Cu | (82.10,49.11,105.34,58.29) | 23.24×9.18 | 4 | `copperpour` |
| `ESC_J3` | F.Cu | (53.45,42.40,65.55,46.60) | 12.10×4.20 | 4 | `copperpour` |
| `ESC_J4` | F.Cu | (53.45,60.60,65.55,64.80) | 12.10×4.20 | 4 | `copperpour` |
| `ESC_J2` | F.Cu | (131.50,42.23,136.15,65.17) | 4.65×22.95 | 4 | `copperpour` |
| `K2_HOLE_KEEPOUT_H1` | 全 8 层 | (23.10,72.60,29.10,78.60) | 6.00×6.00 | 36 | `tracks` `vias` `copperpour` |
| `K2_HOLE_KEEPOUT_H2` | 全 8 层 | (136.60,36.60,142.60,42.60) | 6.00×6.00 | 36 | 同上 |
| `K2_HOLE_KEEPOUT_H3` | 全 8 层 | (42.10,72.10,48.10,78.10) | 6.00×6.00 | 36 | 同上 |
| `K2_HOLE_KEEPOUT_H4` | 全 8 层 | (111.60,33.10,117.60,39.10) | 6.00×6.00 | 36 | 同上 |

> 4 孔 keepout 的 bbox **精确居中于 H1–H4**（d=0.00，见 inc55 表 B）；`pads`/`footprints` 保持 `allowed`（**与图纸 KO-1..4「五开关全 blocked」口径不同** ⇒ 属 Z2 待裁项）。

**有网铜区（10；口径＝有网非 keepout）**

| net | layer | bbox | 尺寸 | priority | 顶点数 |
|---|---|---|---|---|---|
| `GND` | In1.Cu | (23.30,33.30,142.70,78.70) | 119.40×45.40 | — | 4 |
| `GND` | In3.Cu | (23.30,33.30,142.70,78.70) | 119.40×45.40 | — | 4 |
| `12V_IN` | In4.Cu | (25.02,36.84,35.98,41.75) | 10.95×4.91 | 1 | 22 |
| `12V_IN` | In4.Cu | (24.60,34.90,29.40,41.20) | 4.80×6.30 | **2** | 4 |
| `P3V3_AUX` | In4.Cu | (27.95,35.98,52.75,54.27) | 24.80×18.30 | — | 18 |
| `P3V3_AUX` | In4.Cu | (52.20,52.02,59.15,62.52) | 6.95×10.50 | 1 | 14 |
| `P3V3` | In4.Cu | (34.27,34.02,58.42,40.25) | 24.15×6.23 | 1 | 34 |
| `MCU_VDD` | In4.Cu | (23.30,33.30,57.75,78.70) | 34.45×45.40 | — | 4 |
| `P3V3` | In4.Cu | (57.95,33.30,142.70,78.70) | 84.75×45.40 | — | 4 |
| `GND` | In6.Cu | (23.30,33.30,142.70,78.70) | 119.40×45.40 | — | 4 |

> `12V_IN` 的 priority 2 区＝H3 重解后解锁的 12V 面延伸（`K2-P4-H3-RESOLVE-AND-12V-FEED-v1.md` §1）；与图纸 `power_partition`（仅 2 区）粒度不同 ⇒ Z2 待裁项。

## 2. 生成段（emit 形状；与板内原始格式逐项对应）

- keepout：`(zone (layer|layers …) (uuid) (name "…") (hatch edge 0.5) (connect_pads (clearance 0)) (min_thickness 0.25) (keepout ((tracks|vias|pads|copperpour|footprints) allowed|not_allowed) ×5) (placement (enabled no) (sheetname "")) (fill …) (polygon (pts …)))`
- 铜区：`(zone (net "…") (layer "…") (uuid) (hatch edge 0.5) (connect_pads yes (clearance 0.2)) (min_thickness 0.25) [(priority N)] (fill yes (thermal_gap 0.2) (thermal_bridge_width 0.3) (island_removal_mode 0)) (polygon (pts …)))`
- **uuid 确定性**：`uuid5(NAMESPACE_URL, f'k2/g10/{kind}/{name}/{net}/{首顶点}')` ⇒ 满足 T-38 固定种子（两次生成同 sha）。
- **填充**：草案**不**产 `filled_polygon`；由既有「出图前 `ZONE_FILLER`」强制填充（本件 §4 实测该步有效）。

## 3. 回归自证（round-trip，`--roundtrip`）

```
emit → (解析回来) → 与 ZONES 逐字段比对
round-trip: zones=18 field-mismatches=0 ⇒ PASS
```
比对字段：`kind` · `layers`（集合序）· `name` · `net` · `connect_pads`(+`clearance`) · `min_thickness` · `priority` · `keepout`（五开关逐值）· `pts`（**逐顶点字符串精确**）。
⇒ 「数据块 → 生成段 → 解析」**无损**。

## 4. KiCad 级验证（剥离→插入→填充→量测）

| 步 | 结果 |
|---|---|
| 剥离原板 18 区（`board_nozones.kicad_pcb`） | 残留 `(zone` = **0** |
| 插入 emit 结果（`board_draft.kicad_pcb`） | 写入 18 区 |
| `pcbnew.LoadBoard` | **成功**，`len(b.Zones()) == 18` ⇒ **语法有效** |
| `ZONE_FILLER.Fill(b.Zones())` + `SaveBoard` | **成功**（`board_filled.kicad_pcb`） |
| 量测（原板 vs 草案+fill） | 原板：18/8/10 · `keepout_active` PASS（全 allowed=0）· `zone_filled` **10/10** · nets `{12V_IN,GND,MCU_VDD,P3V3,P3V3_AUX}`<br>草案+fill：**逐项相同**（18/8/10 · PASS · 10/10 · 同 nets） |

## 5. 与「G10 全量」的差距（本件只覆盖 zone/keepout 半边）

| G10 组成 | 状态 |
|---|---|
| **NPTH 4 孔段**（H1–H4 逐座标 + Ø3.2） | **未在本件**（须与 inc55 表 B 及 H3 裁定同批；孔位座标属 L2 自裁/已落板） |
| **keepout 段**（8 区） | **本件已成件**（§1/§2） |
| **有网铜区段**（10 区） | **本件已成件**（§1/§2） |
| **出图前 `ZONE_FILLER`** | 既有（P4 板侧已 10/10；本件实测该步对 emit 结果亦有效） |
| 判据在岗（`keepout_active`/`zone_filled`） | 待 `criteria/` 安装 + manifest 签认（**与 Z4/⑤ 同批**） |

## 6. `Z2` 裁定后的执行序（一次投递）

```
Step 0  裁 Z2：keepout/zone 是否「以板为准」（＋是否触 C-1 的说明）
Step 1  把 §1 数据块写入**输入层**（SPEC `keepout_geometry.zones` / `pd.zone_defs.board_realized_zones`；SPEC bump）
        ※ 若判「不补 KO-7 实体 zone」（inc61 §3），此处不加边带 zone，仅登记规则口径
Step 2  生成器加 §2 生成段（消费 Step 1 输入；**禁读板**）
Step 3  /tmp 复跑：emit → round-trip（§3）→ KiCad fill（§4）→ 量测 `keepout_active`/`zone_filled` 全绿
Step 4  与 G10 的 NPTH 段、G9/G11 合批落库（须放行）+ 判据安装 + 落件板 sha 复算
```

## 7. 复跑（每处实测；仓库零写入）

```bash
cd /home/fila/jqdDev_2025/ic_hw; W=/tmp/opencode/inc62
# ① 草案重建：见 §2 的 emit 形状（或直接复制 /tmp/opencode/inc62/g10_zone_keepout_draft.py 8a31ad20ec520e32）
# ② 回归自证（期望 18/0 PASS）
python3 $W/g10_zone_keepout_draft.py --roundtrip; echo "rc=$?"
# ③ 导出候选数据块 + emit
python3 $W/g10_zone_keepout_draft.py --json $W/zones_input.json --emit $W/zones_emit.txt
# ④ KiCad 级：剥区→插区→填充→量测（见 §4；用 AppDir/usr/bin/python3.11 的 pcbnew）
AppDir/usr/bin/python3.11 -c "
import pcbnew;b=pcbnew.LoadBoard('$W/board_draft.kicad_pcb');print('zones',len(b.Zones()))
f=pcbnew.ZONE_FILLER(b);f.Fill(b.Zones());pcbnew.SaveBoard('$W/board_filled.kicad_pcb',b);print('filled+saved')"
```
（`board_draft.kicad_pcb` 的构造＝原板剥离 18 区 + 插入 `--emit` 结果，配方见 §4。）

## 8. 边界

本件**只读 + `/tmp` 草案/变体板**：未改 SPEC/板/pro/生成器/模板/库/`fp-lib-table`/`pm_gate/**`/真源/图纸/`criteria/**`/`_shared/**`；
未创建 `k2/pipeline.yaml`、未创建 `k2/fab/**`；未落件；未出 Gerber；未派 WORKER；临时仅 `/tmp/opencode/inc62`；**未新增仓库内判据/脚本**（避新增检查齿，owner ②）。
—— ENG（ARCHER）· 2026-09-18 · 受审板 `6ff49da5678c2108` · 草案 `8a31ad20ec520e32`
