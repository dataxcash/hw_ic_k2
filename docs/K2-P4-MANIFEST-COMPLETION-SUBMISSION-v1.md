# K2 · P4 · 判据缺口「补齐草案」正式提交（ENG → 监理正/负控复验）· v1 · 2026-09-17

## 0. 提交物、依据与边界

- **依据**：监理 `#K2-20 §二`（`criteria/manifest` **不予签认** ⇒ P4 完工判定有结构缺口，须先补齐转写）+ `§五-2`（ENG 起草 → 监理正/负控复验 → 版本 bump 安装 → 监理签认）+ `§三`（U4-A / U4-C）。
- **本件性质**：ENG **草案 + 自测证据**。判据**语义/应然值/阈值归监理**（草案中 `null` = 待监理填，ENG 不代填）；判据**实现**由 ENG 起草。**判别权归监理**。
- **边界**：`criteria/adjudicate.py`（`897e8bfde60e2cfe`）与 `criteria/manifest.k2.yaml`（`7ce08757eff25557`，0444, owner=ic_hw_gate）**逐字节未动**；本次只把草案**落为仓库耐久件**（此前仅存在于 `/tmp` 易失区）+ 在当前板重出正/负控证据。
- **口径**：板 `k2/hw/k2_v4_8L.l5.kicad_pcb` = **`d9813bc554a2d611`**（增量 16）· 同名 pro `f68a5fb2f82bd02d` · `kicad-cli` 10.0.5 · **T-8**（仓库路径 + 同名 `.kicad_pro`；库解析须 `fp-lib-table` 同目录）。

### 草案件（`k2/docs/drafts/p4-manifest-completion-v2/`）

| 件 | sha256(16) | 说明 |
|---|---|---|
| `manifest.k2.draft-v2.yaml` | `46298fa966844f0d` | 转写补齐版清单草案 |
| `adjudicate.draft-v2.py` | `041f37b6eecdfaab` | 判定器草案（`--kicad-cli` 自跑 DRC，防伪造绿） |
| `make_negatives_v2.py` | `8a000f5c294e3a8d` | 负控造件 v2（**本件新修**：增量 16 板封装头已为新格式 ⇒ 旧正则致 m6 静默未注入） |

---

## 1. 补齐转写（`#K2-20 §二` 五项 + 1 处补正 + U4-A/U4-C）

| # | 检查项 | 表达式（manifest） | 转写来源 | 实现要点 |
|---|---|---|---|---|
| 1 | `drc_errors` | `drc_errors == 0` | J-1 前半 | 判定器**自跑** DRC；报告 `source` 与板不一致 ⇒ FAIL（防伪造绿） |
| 1b | `drc_warning_disposition` | `warnings_without_disposition == 0` | J-1 后半 | warning 逐条须有处置台账（`drc_warning_dispositions`，**监理登记**） |
| 2 | `unconnected_zero` | `unconnected == 0` | J-2 / V1 | 自跑 DRC `unconnected_items`，**全量、禁裁剪** |
| 3 | `lib_footprint_electrical` | `lib_footprint_mismatch + lib_footprint_issues == 0` | J-7 前半 | 自跑 DRC 计数（**见 §3.3 覆盖缺口**） |
| 3b | `fp_lib_table_present` | `fp-lib-table exists` | J-7 后半 / W-8 / F-12 | 存在性 |
| 4 | `board_frame_and_keepout` | `footprints_outside_outline == 0 and esc_keepout_unrestricted == 0` | J-8 出框(P3-4) / 回避区(P3-5·C5b·IN-7) | 器件含 pad bbox vs `Edge.Cuts`；ESC_* 四区 tracks/vias/pads/footprints 须各 ≥1 非 allowed |
| 4b | `density_and_spacing` | `（阈值待监理填）` | J-8 密度/关键间距 | 密度 = 10mm 格峰值；**关键间距未实现**（口径待监理给，见 §4） |
| 5 | `v3_reference_continuity` | `unreferenced_hs_segments == 0` | V3 | 高速段投影（0.2mm 采样）∩ 相邻参考层平面（zone 外形 ∧ 该 zone 已 filled） |
| 6 | `drill_count`（**补正**） | `npth >= 4 and pth >= drill_pth_min` | 计划 §P4 / 审计 §10.8 L2-8 8e | `npth >= 1` → **`>= 4`**（现板 NPTH=4 ⇒ 判定不变） |
| 7 | `zone_filled` | `filled_fillable_zones == fillable_zones` | J-3 / **U4-A** | 分母 = 非 keepout zone（keepout 结构上不可能 filled） |
| 8 | `refdes_sets_equal` | `sch_set == board_set - mechanical_refdes` | J-6 / **U4-C** | `mechanical_refdes: [H1..H4]`；**未登记**的多余 refdes 仍判 FAIL |

---

## 2. 正控（当前板 `d9813bc554a2d611` 实跑，判定器自跑 DRC）

**结论**：`passed=false` · **PASS 10 / FAIL 8** · `provisional=true`（manifest 未签认）。

### 2.1 PASS 10

| 检查项 | 实测 |
|---|---|
| `zone_filled` | 已填充 **9/9**（可填充 = 非 keepout；keepout 8 个结构不可填） |
| `device_has_pads` | 0 焊盘器件 **0** |
| `drill_count` | NPTH=**4**（≥4）· PTH=**16** |
| `non45_segments` | **0 / 4701**（增量 10+ 走廊重解后；增量 9 时为 2051/2921） |
| `net_declared_realized` | 0 焊盘的声明网 **0**；<2 焊盘 **1** |
| `pin_map_complete` | 网表节点无对应焊盘 **0** |
| `refdes_sets_equal` | 图 55 / 板 59；图有板无 **0**；板有图无 **4**（= 登记机械件 H1..H4）；未登记 **[]** |
| `fp_lib_table_present` | **True**（`k2/hw/fp-lib-table`） |
| `v3_reference_continuity` | 未覆盖高速段 **0 / 3653** |
| `verdict_schema` | 产物含 `verdict` 键的文件 **[]** |

### 2.2 FAIL 8（与门禁口径一致）

| 检查项 | 实测 | 性质 |
|---|---|---|
| `drc_errors` | error **15**（hole_clearance 8 · courtyards_overlap 2 · pth_inside_courtyard 3 · solder_mask_bridge 2）；warning **36**（lib_footprint_mismatch 35 · hole_to_hole 1）；全板违规 **51** | **owner 闸**：H3 组 **16**（hole_clearance 8 + hole_to_hole 1 + pth_inside_courtyard 3 + courtyards_overlap 2 + solder_mask_bridge 2）+ W-8/J-7 **35** |
| `drc_warning_disposition` | 未登记处置 warning **36/36**（hole_to_hole 1 + lib_footprint_mismatch 35） | 待监理登记台账 |
| `unconnected_zero` | 未连接 **2**（`12V_IN` @H3闸 · `DS320_STRAP_A_ADDR0_15-8` @端点局部不可解） | **owner 闸** |
| `lib_footprint_electrical` | mismatch **35** + issues **0** = **35** | **owner 闸**（W-8/J-7，T-26） |
| `board_frame_and_keepout` | 出框器件 **0**；ESC_* 全 allowed 区 **4** | 待处置（C5b/IN-7 语义） |
| `density_and_spacing` | 密度峰值 **5 件/10mm 格**；阈值 `null` ⇒ fail-closed | 待监理填阈值 |
| `rule_severity_manifest` | 未登记豁免的 ignore **9/62** | 见 W-7 九条方案（`k2/docs/K2-P4-W7-IGNORE-DISPOSITION-v1.md`） |
| `pipeline_present` | 6 目录（`k1/sch` · `k2/hw/sch` · `pciesw4/*`） | 解析 `pipeline.yaml` 的实现口径（跨项目目录含入） |

> **与 `#K2-20 §〇` 监理复算（增量 9 板）的差异**：`non45 2051→0`（G-1 走廊重解已落）· `unconnected 19→2` · `drc error 39→15`；其余 FAIL 项**集合未变**。

---

## 3. 负控（定向缺陷注入 · 逐件实测）

> 每件在 `/tmp/opencode/p4/draft/neg/<name>/` 自带**同名 `.kicad_pro`**（T-8）+ **`fp-lib-table` + `lib/ForgeOS.pretty`**（否则库解析退化 ⇒ 假 `lib_footprint_issues`，见 §3.3）。

| 造件 | 注入 | 期望命中 | **实测变化**（vs 正控） | 判定 |
|---|---|---|---|---|
| `m1_unconnected` | 删 1 条 F.Cu 走线 | `unconnected_zero` | `unconnected 2→3` | ✅ 抓住 |
| `m2_unfilled` | 清空 In3.Cu GND 区 `filled_polygon` | `zone_filled` | `zones_filled 9→8` | ✅ 抓住 |
| `m3_non45` | 注入 1 条 30° 走线 | `non45_segments` | `non45 0→1` · warning 36→37（连带 `track_dangling`）· unconnected 2→3 | ✅ 抓住 |
| `m4_no_ref_in6` | 删 In6.Cu 平面外形 polygon | `v3_reference_continuity`（+ fail-closed） | `unreferenced_hs_segments 0→54`；且板不可解析 ⇒ DRC 三项判 **FAIL（缺报告，fail-closed）** | ✅ 抓住 |
| `m5_refdes` | C85 → X99 | `refdes_sets_equal` + `pin_map_complete` | 板有图无 **4→5**（未登记 `X99`）· `missing_nodes 0→2` | ✅ 抓住 |
| `m6_u1_pad` | U1.11 pad 尺寸 `1.475→1.525` | `lib_footprint_electrical` | **无变化（未抓住）** | ❌ **见 §3.3** |
| `m7_no_fp_lib_table` | 移走 `fp-lib-table` | `lib_footprint_electrical`（issues 腿） | `issues 0→6` · `mismatch 35→29`（**和恒为 35**） | ⚠️ 部分（见 §3.3） |

### 3.1 结论（可复算）

- **m1..m5：全部按预期被抓住**，且变化量可逐项归因（非「PASS/FAIL 已 FAIL 所以算命中」）。
- **m4 另证 fail-closed**：注入致板不可解析时，`drc_errors` / `unconnected_zero` / `lib_footprint_electrical` 全部以「缺少 DRC 实跑报告」判 FAIL，**不静默放行**。

### 3.2 负控构造口径（重要）

正控与负控的 DRC 数字**只有在库可解析时可比**：`m1..m6` 目录内已放 `fp-lib-table` + `lib/ForgeOS.pretty`（`${KIPRJMOD}` 相对解析）。缺此二者时（`m7`），6 个 `ForgeOS:*` 封装从 `lib_footprint_mismatch` 转入 `lib_footprint_issues` ⇒ **mismatch 35→29 / issues 0→6**。

### 3.3 ⚠️ **发现：`lib_footprint_electrical` 转写存在覆盖缺口（m6 未命中的根因）**

**事实（实测）**：本板 **59** 个封装中——

- **35 件带库 nickname**（`Capacitor_SMD:*` · `Resistor_SMD:*` · `ForgeOS:*` · `Package_SO:*` · `LED_SMD:*`），**全部已判 `lib_footprint_mismatch`**；
- **24 件无库 nickname**（`MCU_STM32G0_LQFP48` · `DS320PR1601` · `PinHeader_*` · `D_SMA` · `L_0805_2012Metric` · `R_0603_1608Metric`，refdes = `D2 · H1..H4 · J6 · J9 · J11..J13 · L1 · R35..R45 · U1 · U6`），**KiCad 完全不做库比对**（既不计 mismatch，也不计 issues）。

**推论**：`lib_footprint_mismatch + lib_footprint_issues == 0` 这条表达式——

1. **对无 nickname 的 24 件（41%）静默跳过**；其中含 **P4 新增/连接件**（`U1 · U6 · J6 · J9..J13 · R35..R45 · D2 · L1`）⇒「以板为准、电气级必须 0」（W-8/J-7）在此**不可证**；
2. 因 35 件带 nickname 者**已全部 mismatch**，**任何**「向已失配件再注入 pad 级差异」都不会改变计数 ⇒ **计数增量型负控在此板上不可构造**（m6 即因此未命中，非判据失效）。

**ENG 建议（语义由监理裁）**：给 J-7 加一条**覆盖守卫**，例如

```
lib_footprint_electrical:
  (lib_footprint_mismatch + lib_footprint_issues == 0)
  AND (footprints_without_library_nickname ⊆ mechanical_refdes ∪ registered_exemptions)
```

> 现状板：无 nickname 24 件 ⊄ {H1..H4} ⇒ 该守卫**判 FAIL**（与 W-8 未决一致）；机械孔 H1..H4 属合法豁免。
> 若监理认为「板为准 ⇒ 无 nickname 即无需比对」，则须**具名登记**该 24 件为豁免（不得静默通过）。

---

## 4. 待监理给口径（**不静默** · 5 项）

1. **J-8「关键间距」**：未实现 —— 需监理给「哪类间距 / 阈值 / 口径」（现仅出框 + ESC_* 回避区 + 密度峰值）。
2. **`density_max_per_10mm_cell`** 阈值 `null` ⇒ 该项恒 FAIL（fail-closed），待监理填。
3. **`drill_pth_min`**（计划 §P4「PTH ≥ 插件件引脚数」）算式待监理给；草案暂为 `0`（不虚判）。
4. **V3 语义选择**：草案用「zone **外形** ∧ 该 zone 已 `filled_polygon`」（filled 多边形上万点，纯 Python 逐点判会超时）；若要求严格口径须改栅格化实现。
5. **J-7 覆盖缺口**（§3.3）：是否采纳覆盖守卫，或具名豁免 24 件无 nickname 封装。

## 5. 复跑链（确定性）

```bash
cd /home/fila/jqdDev_2025/ic_hw
DR=k2/docs/drafts/p4-manifest-completion-v2
# 正控（判定器自跑 DRC）
python3 $DR/adjudicate.draft-v2.py --project k2 --manifest $DR/manifest.k2.draft-v2.yaml \
  --board k2/hw/k2_v4_8L.l5.kicad_pcb --pro k2/hw/k2_v4_8L.l5.kicad_pro \
  --nets k2/hw/data/k2_sch.errata-1.yaml --sch-dir k2/hw/sch --kicad-cli AppDir/bin/kicad-cli \
  --measure-out /tmp/m.json --out /tmp/v.json      # 期望 PASS 10 / FAIL 8
# 负控造件（仅 /tmp）+ 逐件判定（每件须带同名 pro + fp-lib-table + lib/）
cp $DR/make_negatives_v2.py /tmp/opencode/p4/draft/make_negatives.py
python3 /tmp/opencode/p4/draft/make_negatives.py
for n in m1_unconnected m2_unfilled m3_non45 m4_no_ref_in6 m5_refdes m6_u1_pad; do
  d=/tmp/opencode/p4/draft/neg/$n
  cp k2/hw/fp-lib-table $d/ ; mkdir -p $d/lib ; cp -r k2/hw/lib/ForgeOS.pretty $d/lib/
  python3 $DR/adjudicate.draft-v2.py --project k2 --manifest $DR/manifest.k2.draft-v2.yaml \
    --board $d/$n.kicad_pcb --pro $d/$n.kicad_pro --nets k2/hw/data/k2_sch.errata-1.yaml \
    --sch-dir k2/hw/sch --kicad-cli AppDir/bin/kicad-cli \
    --measure-out $d/meas.json --out $d/verdict.json
done
```

## 6. 与其它在办项的关系

- 本件是 **P4 完工前置**（`#K2-20 §二`「P4 完工判定不可达」），**不阻**布线/连通收敛。
- 本件**不改** DRC 门禁结果、**不改**任何冻结件；`rule_severity_manifest` 的处置仍走 **W-7 九条**（`k2/docs/K2-P4-W7-IGNORE-DISPOSITION-v1.md`，待监理逐条批）。
- 剩余 P4 阻断（未连接 2 · 违规 16 条 H3 · 35 条 W-8）**全在 owner 闸口**，ENG 侧无动作。

—— ENG（ARCHER）· 2026-09-17 · 判据锚 = `#K2-20`
