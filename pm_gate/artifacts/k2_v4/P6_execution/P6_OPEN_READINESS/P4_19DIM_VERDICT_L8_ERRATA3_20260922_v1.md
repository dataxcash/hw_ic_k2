# K2 · **P4 判定器 verdict（受审板 l8 @ errata-3）** · 2026-09-22

**件**：`P4_19DIM_VERDICT_L8_ERRATA3_20260922_v1.json`（约定A **`e37c8f1cc2d1f057`**）+ `P4_MEASUREMENTS_L8_20260922/`（5 件测量输入）
**据**：《K2 整体整改计划》§P4「**完工判据 —— 由判定器出 verdict，ENG 只交测量**」· 监理自动续推（按已批准计划推进当前阶段 P4 · fail-closed）
**锚**：冻结四源 **4/4 未动**（`fb07d25a` / `d4e81f64` / `dd794c54` / `0a459839`）· `criteria` **rev=6 MATCH**（`adjudicate.py 1937a40ae68bc288` · `manifest.k2 727d09953cf9bd78` · `CHANGELOG eb3da49f2ad97e37` · ENG 只读）· 受审板 l8 **`7a5c89913d6e5d0a`** · 网表口径 `errata-3 5dc7b82a901d11c8`（D2 已批）· **owner 闸口 0**

---

## 〇、一句话

**P4 判定器首度以完整输入跑出 19 维 verdict：`n_pass = 18` · `n_fail = 1` ⇒ `passed = False`（fail-closed 维持，不得下单）。**
唯一 FAIL = `lib_electrical_level`，已**逐条具名归因**为**判据侧过度严格之伪差异（非板缺陷）**：370 个**圆形 pad 之 rot 伪差异** + U1 的 **9 个无号 F.Paste**。

## 一、P4 三条结构前置（计划 §P4 明文）—— 受审板 l8 实测

| 前置 | 判 | 读数 |
|---|---|---|
| **铺铜** | **OK** | `zone_filled`：铜区（有网非 keepout）已填充 **10/10**；keepout 规则区 8 个另计（不入分母） |
| **钻孔** | **OK** | `drill_count`：**NPTH = 4（应 ≥4）· PTH = 16** |
| **平面落图** | **OK** | Gerber `G36>0`：`In1_Cu`=1 · `In3_Cu`=1 · `In4_Cu`=9 · `In6_Cu`=1 |

> 计划原文所记「现状 0/13 · 0/0 · 8 层铜全 0」系 **2026-09-15 冻结板**时点；本表为受审板 l8 之**实测复跑**。

## 二、19 维 verdict（`criteria/adjudicate.py` 输出，ENG 未改判据）

**`n_pass = 18` · `n_fail = 1` · `passed = False`**

| # | 维 | 判 | 读数（摘要） |
|---|---|---|---|
| 1 | `zone_filled` | OK | 10/10（keepout 8 另计） |
| 2 | `device_has_pads` | OK | 0 焊盘器件 0 个 |
| 3 | `drill_count` | OK | NPTH=4（≥4）PTH=16 |
| 4 | `non45_segments` | OK | 非 45° 段 0/5180 |
| 5 | `rule_severity_manifest` | OK | 未登记豁免之 ignore 0/62 |
| 6 | `net_declared_realized` | OK | 0 焊盘声明网 0；<2 焊盘 0（**@errata-3**） |
| 7 | `pin_map_complete` | OK | 网表节点缺焊盘 0（**@errata-3**） |
| 8 | `refdes_sets_equal` | OK | 排除纯机械件 H1..H4 ⇒ 原理图 54 / 板 54 |
| 9 | `pipeline_present` | OK | 范围 k2 内缺 pipeline 目录 0（fail-closed） |
| 10 | `drc_errors` | OK | DRC error = 0（违规总 170 · 已登记） |
| 11 | `drc_warning_dispositions` | OK | 未登记 warning 类型 0/9 |
| 12 | `unconnected_zero` | OK | unconnected_items = 0 |
| 13 | `fp_lib_table_present` | OK | `k2/hw/fp-lib-table` 存在 |
| 14 | `keepout_active` | OK | keepout 8 个，全有生效开关 |
| 15 | `pads_within_outline` | OK | 出框：AABB 0 · 接口件 0 · 真外框多边形 0 |
| 16 | `ref_plane_continuity` | OK | `non_antipad_gap = 0.0 mm²` @R=0.5mm（平面层 In1/In3/In4/In6） |
| 17 | `density_and_clearance` | OK | 密度[10mm/frame_origin] 峰值 **7**（≤8）· 最小铜间距 **0.1**（≥0.1）mm |
| 18 | `verdict_schema` | OK | 产物无 verdict 字段 |
| 19 | **`lib_electrical_level`** | **FAIL** | 电气级差异 **7**（见 §三） |

## 三、唯一 FAIL 之逐条归因（判据侧 ⇒ 请监理裁定）

**A · 6 个 ref / 370 pads：圆形 pad 之 rot 伪差异**

| 项 | 值 |
|---|---|
| refs | `U6`（354 pads）· `J11`(4) · `J9`(4) · `J13`(4) · `J6`(2) · `J12`(2) |
| 差异字段 | **仅 `rot`**：板 `0.0°` vs 库 `90.0°` |
| 其余字段 | `shape` 板/库同为 **0（圆形）**；`sx/sy/dx/dy/drill_d/layer` **逐字段全同** |
| 判据事实 | **圆形 pad 绕中心旋转任意角度，铜形完全不变** ⇒ 铜几何**全同**，属表示差异 |
| 现有规则 | 判定器 `_reclassify_w8` 规则② 已承认「中心对称 pad rot 0≡180」；**圆形之等价类应为任意旋转**，现未覆盖 0 vs 90 |

**B · U1：9 个无号 F.Paste**

- 库件 `k2/hw/lib/ForgeOS.pretty/MCU_STM32G0_LQFP48.kicad_mod` 含 **9 个无号 pad**，逐条 `(pad "" smd roundrect … (layers "F.Paste"))` ⇒ **仅 F.Paste、无铜层** ⇒ **非电气**。
- 判定器规则③ 明文本意即豁免「无号 F.Paste（lib_only 全空串）⇒ 非电气」，但其守卫限定 `kind=='pad_name_set'`；本处审计产出 `kind='pad_set'` ⇒ **未被覆盖**（实现面未跟上规则本意）。

**性质**：二者均为**数学恒等 / 非电气**之判据侧口径问题，**铜形几何逐字节等同** ⇒ **不是缩口径**、**不是板缺陷**。
**处置**：判据 ENG **只读**，**不得自改** ⇒ 报监理裁定（属监理自裁面）。

## 四、P4 状态

**P4 未全绿（18/19）⇒ 阶段门 fail-closed 维持**：不得进 P5、不得下单。唯一 FAIL 归因清晰、无板侧可动项。

## 五、复现

```bash
# 测量（5 件；全部含 board_sha16 = 7a5c89913d6e5d0a）
AppDir/usr/bin/python3.11 k2/tools/k2_w8_footprint_audit_pose_v2_layeraware.py --board k2/hw/k2_v4_8L.l8.kicad_pcb --proj-lib k2/hw/lib --out-json m/w8_l8.json --out-md m/w8_l8.md
AppDir/usr/bin/python3.11 k2/docs/drafts/p4-j8-v3-measurement-v1/measure_pads_within_outline.py --board k2/hw/k2_v4_8L.l8.kicad_pcb --json m/pads_outline_l8.json
AppDir/usr/bin/python3.11 k2/docs/drafts/p4-j8-density-clearance-v1/measure_density_and_clearance.py --board k2/hw/k2_v4_8L.l8.kicad_pcb --cell-mm 5,10,20 --json m/density_l8.json
AppDir/usr/bin/python3.11 k2/docs/drafts/p4-j8-density-clearance-v1/measure_min_clearance_drc.py --board k2/hw/k2_v4_8L.l8.kicad_pcb --pro k2/tools/k2_jlc_template.kicad_pro --kicad-cli AppDir/usr/bin/kicad-cli --json m/minclr_l8.json
AppDir/usr/bin/python3.11 k2/docs/drafts/p4-refplane-nonantipad-v1/measure_non_antipad_gap.py --board k2/hw/k2_v4_8L.l8.kicad_pcb --spec k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-54.json --json m/refplane_l8.json
# 判定（唯一 verdict 产地）
python3 criteria/adjudicate.py --project k2 --board k2/hw/k2_v4_8L.l8.kicad_pcb --pro k2/tools/k2_jlc_template.kicad_pro \
  --nets k2/hw/data/k2_sch.errata-3.yaml --sch-dir k2/hw/sch \
  --gerber-dir k2/pm_gate/artifacts/k2_v4/L6/jlc_package_l8r3/01_gerber_rs274x \
  --drc-cli AppDir/usr/bin/kicad-cli --drc-work-dir /tmp/opencode/drc \
  --w8-audit-json m/w8_l8.json --pads-outline-json m/pads_outline_l8.json --refplane-gap-json m/refplane_l8.json \
  --density-json m/density_l8.json --min-clearance-json m/minclr_l8.json \
  --measure-out /tmp/opencode/p4m/measure.json --out /tmp/opencode/p4m/adj.json
# 期望：n_pass=18 · n_fail=1（唯 lib_electrical_level）· passed=False
```

## 六、边界

冻结四源不改 · `criteria/` 只读未碰 · 未烙板 · 未派 WORKER · 未改生成器/SPEC/原理图 · 临时仅 `/tmp/opencode` · 未写 `.omo/supervision/**` · **阶段门 fail-closed 维持**。

—— ENG（ARCHER）· 2026-09-22 · owner 闸口 **0** · 待裁 **0**
