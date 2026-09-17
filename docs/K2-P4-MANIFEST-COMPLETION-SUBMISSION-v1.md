# K2 · P4 · 判据缺口「补齐草案」正式提交（ENG → 监理正/负控复验）· v1 · 2026-09-17

## 0. 提交物、依据与边界

- **依据**：监理 `#K2-20 §二`（`criteria/manifest` **不予签认** ⇒ P4 完工判定有结构缺口，须先补齐转写）+ `§五-2`（ENG 起草 → 监理正/负控复验 → 版本 bump 安装 → 监理签认）+ `§三`（U4-A / U4-C）。
- **本件性质**：ENG **草案 + 自测证据**。判据**语义/应然值/阈值归监理**（草案中 `null` = 待监理填，ENG 不代填）；判据**实现**由 ENG 起草。**判别权归监理**。
- **边界**：`criteria/adjudicate.py`（`897e8bfde60e2cfe`）与 `criteria/manifest.k2.yaml`（`7ce08757eff25557`，0444, owner=ic_hw_gate）**逐字节未动**；本次只把草案**落为仓库耐久件**（此前仅存在于 `/tmp` 易失区）+ 在当前板重出正/负控证据。
- **口径**：板 `k2/hw/k2_v4_8L.l5.kicad_pcb` = **`d9813bc554a2d611`**（增量 16）· 同名 pro `f68a5fb2f82bd02d` · `kicad-cli` 10.0.5 · **T-8**（仓库路径 + 同名 `.kicad_pro`；库解析须 `fp-lib-table` 同目录）。

### 草案件（`k2/docs/drafts/p4-manifest-completion-v2/`）

| 件 | sha256(16) | 说明 |
|---|---|---|
| `manifest.k2.draft-v2.yaml` | `360b3d1cf377bedb` | 转写补齐版清单草案（**v2.2**：+W-9 `pipeline_scope`；C5b/IN-7 口径对齐） |
| `adjudicate.draft-v2.py` | `f7b23e99dc277ec6` | 判定器草案（**v2.2**：+W-9 scoped、C5b 口径；`--kicad-cli` 自跑 DRC 防伪造绿） |
| `make_negatives_v2.py` | `8a000f5c294e3a8d` | 负控造件 v2（**本件新修**：增量 16 板封装头已为新格式 ⇒ 旧正则致 m6 静默未注入） |

---

## 1. 补齐转写（`#K2-20 §二` 五项 + 1 处补正 + U4-A/U4-C/U4-C/**W-9**）

| # | 检查项 | 表达式（manifest） | 转写来源 | 实现要点 |
|---|---|---|---|---|
| 1 | `drc_errors` | `drc_errors == 0` | J-1 前半 | 判定器**自跑** DRC；报告 `source` 与板不一致 ⇒ FAIL（防伪造绿） |
| 1b | `drc_warning_disposition` | `warnings_without_disposition == 0` | J-1 后半 | warning 逐条须有处置台账（`drc_warning_dispositions`，**监理登记**） |
| 2 | `unconnected_zero` | `unconnected == 0` | J-2 / V1 | 自跑 DRC `unconnected_items`，**全量、禁裁剪** |
| 3 | `lib_footprint_electrical` | `lib_footprint_mismatch + lib_footprint_issues == 0` | J-7 前半 | 自跑 DRC 计数（**见 §3.3 覆盖缺口**） |
| 3b | `fp_lib_table_present` | `fp-lib-table exists` | J-7 后半 / W-8 / F-12 | 存在性 |
| 4 | `board_frame_and_keepout` | `footprints_outside_outline == 0 and esc_keepout_unrestricted == 0` | J-8 出框(P3-4) / 回避区(P3-5·C5b·IN-7·**#K2-17 §五**) | 器件含 pad bbox vs `Edge.Cuts`；ESC_* 四区须各 **≥1 开关非 allowed，开关集 = tracks/vias/pads/copperpour/footprints（5 项，含 copperpour）** —— 与已裁口径对齐，见 §3.5 |
| 4b | `density_and_spacing` | `（阈值待监理填）` | J-8 密度/关键间距 | 密度 = 10mm 格峰值；**关键间距未实现**（口径待监理给，见 §4） |
| 5 | `v3_reference_continuity` | `unreferenced_hs_segments == 0` | V3 | 高速段投影（0.2mm 采样）∩ 相邻参考层平面（zone 外形 ∧ 该 zone 已 filled） |
| 6 | `drill_count`（**补正**） | `npth >= 4 and pth >= drill_pth_min` | 计划 §P4 / 审计 §10.8 L2-8 8e | `npth >= 1` → **`>= 4`**（现板 NPTH=4 ⇒ 判定不变） |
| 7 | `zone_filled` | `filled_fillable_zones == fillable_zones` | J-3 / **U4-A** | 分母 = 非 keepout zone（keepout 结构上不可能 filled） |
| 8 | `refdes_sets_equal` | `sch_set == board_set - mechanical_refdes` | J-6 / **U4-C** | `mechanical_refdes: [H1..H4]`；**未登记**的多余 refdes 仍判 FAIL |

---

## 2. 正控（当前板 `d9813bc554a2d611` 实跑，判定器自跑 DRC）

**结论**：`passed=false` · **PASS 11 / FAIL 7** · `provisional=true`（manifest 未签认）。

### 2.1 PASS 11

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
| `board_frame_and_keepout` | 出框器件 **0**；C5b/IN-7 不达标区 **0**（其中「仅 copperpour 受限」= 4；更严 4 开关口径 = 4，**本板不可达**，见 §3.5）；全 allowed keepout 区 **0** |

### 2.2 FAIL 7（与门禁口径一致）

| 检查项 | 实测 | 性质 |
|---|---|---|
| `drc_errors` | error **15**（hole_clearance 8 · courtyards_overlap 2 · pth_inside_courtyard 3 · solder_mask_bridge 2）；warning **36**（lib_footprint_mismatch 35 · hole_to_hole 1）；全板违规 **51** | **owner 闸**：H3 组 **16**（hole_clearance 8 + hole_to_hole 1 + pth_inside_courtyard 3 + courtyards_overlap 2 + solder_mask_bridge 2）+ W-8/J-7 **35** |
| `drc_warning_disposition` | 未登记处置 warning **36/36**（hole_to_hole 1 + lib_footprint_mismatch 35） | 待监理登记台账 |
| `unconnected_zero` | 未连接 **2**（`12V_IN` @H3闸 · `DS320_STRAP_A_ADDR0_15-8` @端点局部不可解） | **owner 闸** |
| `lib_footprint_electrical` | mismatch **35** + issues **0** = **35** | **owner 闸**（W-8/J-7，T-26） |
| `density_and_spacing` | 密度峰值 **5 件/10mm 格**；阈值 `null` ⇒ fail-closed | 待监理填阈值 |
| `rule_severity_manifest` | 未登记豁免的 ignore **9/62** | 见 W-7 九条方案（`k2/docs/K2-P4-W7-IGNORE-DISPOSITION-v1.md`） |
| `pipeline_present` | **1 目录**：`k2/hw/sch`（**W-9 已实现**：k2-scoped；此前报 6 目录含 `k1/sch`·`pciesw4/*`） | **J-9 / M-13**：k2 无 `pipeline.yaml` ⇒ 见 §3.4 |

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

### 3.4 ⚠️ **发现：`pipeline_present`（J-9 / M-13）不是「加一个文件」可闭合 —— 有实测阻断**

**W-9 已实现**（本件 v2.1）：`pipeline_present` 现按 `manifest.pipeline_scope: [k2]` 只判 k2 目录 ⇒ 报 **1 目录 `k2/hw/sch`**（此前 6 目录，含 `k1/sch` / `pciesw4/*`）。

**闭合 J-9 需要 `k2/pipeline.yaml`，但该件受三道硬约束（实测）**：

1. **仓库 meta-gate 要求声明必选 sch checks**（`_shared/eda_core/pipeline/required.py`：`REQUIRED_SCH_CHECKS = ("sch_structural","netlist_connect","bom_consistent")`）。一旦 `k2/pipeline.yaml` 被 `find_all_projects()` 发现，k2 即被纳入 meta-gate。
2. **`engine.py verify <proj>` 会跑 `verify:` 声明的**全部** check，且 pre-commit 对任何触及 k2 的提交强制执行**（`_shared/eda_core/pipeline/hooks/pre-commit`）⇒ 声明的 check 必须**真能过**，否则 **k2 全部提交被拒**。
3. **实测三项必选 check 对 k2 的现状**：

| check | 参数 | 实测 | 说明 |
|---|---|---|---|
| `sch_structural` | `k2/hw/sch/k2_sch.kicad_sch` | **PASS**（0 warnings） | 结构三基础 OK |
| `netlist_connect` | 同上 + `nets_yaml: k2/hw/data/k2_sch.errata-1.yaml` | **FAIL · 106 处** | ① 声明网 `PWR_5V_KEY` 在 KiCad netlist **不存在**（1 处，= #K2-19 §二 已登记口径注记）② **反向断言**：KiCad `unconnected-*` 网节点须 ⊆ YAML `nc` 白名单 —— k2 有 **105** 个 `unconnected-*` 网（105 引脚），而 errata 的 **`nc` 白名单 = 0 条** ⇒ 全判「非声明悬空」 |
| `bom_consistent` | 需 `bom_csv` | **不可跑** | k2 仓内**无任何 BOM csv**（`find k2 -iname '*bom*'` = 空）⇒ 声明即 FAIL |

**⇒ 结论（需监理一句话裁，**非 owner 项**）**：把 k2 接进 `eda_core/pipeline` 门禁（= J-9/M-13 的应然）**不能只加文件**；在 `netlist_connect` 的 `nc` 白名单与 BOM 就位前，接线会 **fail-closed 堵死 k2 的 P4 提交**（自伤）。三条出路：

- **(A) 真源侧补录**：给 k2 的 `nc` 白名单（105 条）+ `PWR_5V_KEY` 处置出**版本 bump 新文件**（`k2_sch.errata-2.yaml`；`errata-1` 原件不动），并生成 k2 的 BOM csv ⇒ 接线后 check 可过。**触及真源 ⇒ 版本 bump 须批**。
- **(B) 收窄必选集**：监理裁定 k2 的必选 sch checks ≠ 全仓常量（例如 k2 不适用 `netlist_connect` 反向断言 / `bom_consistent`）⇒ 属**判据语义/范围**（#K2-19 §一 二分：监理自有权）。
- **(C) 分阶段接线**：P4 内只声明 `sch_structural`（已 PASS），`netlist_connect`/`bom_consistent` 挂 P5（bring-up/交付包）再开 ⇒ 须监理明示「J-9 在 P4 按此口径判 PASS」。

**注**：在监理给出口径前，ENG **不**创建 `k2/pipeline.yaml`。**理由**：把必选 check 声明在 `checks:`（引擎 `cmd_run`/`cmd_verify` 均不执行该字段）即可让 meta-gate 表面通过，但那是**只满足字面、不产生强制力**的空声明 = 以口径达成绿，本件拒绝采用。

### 3.5 ⚠️ **自查纠正：`board_frame_and_keepout` 的回避区腿曾比已裁口径更严，且在该板永不可达**

**事由**：本件 v2.1 的该 check 曾注「copperpour 不计」（只数 tracks/vias/pads/footprints），实测报 `4/4` 不达标 ⇒ 会把**已达成**项判 FAIL，使 P4 **结构上不可闭**（与 C7「13 区」、U4-A「13 区」同类：判据自指/不可达）。**本件 v2.2 已更正**。

**已裁口径（三处一致，均以 5 开关为准，无 copperpour 除外）**：
- `#K2-17 §三 补正 2`：缺陷定义为「板侧 `ESC_J2/J3/J4/U6` **4 区 × 5 开关（tracks/vias/pads/copperpour/footprints）全部 allowed** = 空操作」；
- `#K2-17 §五`（P4 施工项）：**「4 个 `ESC_*` keepout 开关落为 ≥1 非 `allowed`」**；
- `K2-RULING-p3-closure-and-p4-open-v1` §C5b：「板侧每区 ≥1 非 `allowed`」；ENG `K2-P4-CONSTRUCTION-STATUS-v1.md` 已据此记 **IN-7 达成**（`zone_fills = disallow`）。

**板侧现状（l5 实测）**：4 区均为 `copperpour not_allowed` + 其余 4 开关 `allowed` ⇒ 按已裁口径 **不达标区 = 0（达成）**。

**「更严读法」不可达证明（实测，非推理）**：

| 更严选项 | 结果 |
|---|---|
| `pads → not_allowed` | DRC **`items_not_allowed` 199 条**，全板违规 **51 → 250** ⇒ **不可行**（U6 球阵 354 pad 与 J2/J3/J4 焊盘即在区内） |
| `tracks → not_allowed` | 区内 F.Cu 段 **181 / 125 / 213 / 336**（4 区）⇒ 必然海量违规，**不可行** |
| `vias → not_allowed` | 区内 via **46 / 15 / 17 / 258** ⇒ **不可行** |
| `footprints → not_allowed` | 区正是 `U6`/`J2`/`J3`/`J4` 的逃逸走廊，封装/庭院在区内 ⇒ 不可行 |

⇒ 本板唯一可行的非 `allowed` 开关 = **`copperpour`**（语义亦正当：**逃逸走廊不得被铺铜填死**）。
> 方法学更正留痕：本件初测「区内 pad = 0」是**错的** —— 封装内 pad 的 `at` 为**相对坐标**，须先加封装原点；**判据以 DRC 为权威**（0→199 即由此暴露）。

**处置**：v2.2 按已裁口径（5 开关）判定，并**并列上报**两个强度指标（`仅 copperpour 受限 = 4` / `更严 4 开关不达标 = 4`），**不做任何静默收窄**。
**结果**：正控随之为 **PASS 11 / FAIL 7**，唯一变化项 = 本项；7 件负控逐件复跑**无回归**。
**交监理（口径强度，不是你我能默定）**：① 认已裁口径（本项即 PASS，J-8 回避区腿闭合）；② 若要更强齿 ⇒ 须把 `ESC_*` 区内铜**移出走廊**（L2 走廊重解，代价大且与「南侧唯一长距离通道」用途冲突）⇒ 另裁。

## 4. 待监理给口径（**不静默** · 7 项）

1. **J-8「关键间距」**：未实现 —— 需监理给「哪类间距 / 阈值 / 口径」（现仅出框 + ESC_* 回避区 + 密度峰值）。
2. **`density_max_per_10mm_cell`** 阈值 `null` ⇒ 该项恒 FAIL（fail-closed），待监理填。
3. **`drill_pth_min`**（计划 §P4「PTH ≥ 插件件引脚数」）算式待监理给；草案暂为 `0`（不虚判）。
4. **V3 语义选择**：草案用「zone **外形** ∧ 该 zone 已 `filled_polygon`」（filled 多边形上万点，纯 Python 逐点判会超时）；若要求严格口径须改栅格化实现。
5. **J-7 覆盖缺口**（§3.3）：是否采纳覆盖守卫，或具名豁免 24 件无 nickname 封装。
6. **J-9 / M-13 接线口径**（§3.4）：选 (A) 真源 bump 补 `nc` 白名单+BOM / (B) 收窄必选集 / (C) 分阶段接线 —— 未裁前 ENG 不建 `k2/pipeline.yaml`。
7. **C5b/IN-7 口径强度**（§3.5）：认已裁 5 开关口径（现状 PASS）／或要更强齿（须走廊级移铜，另裁）。

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
