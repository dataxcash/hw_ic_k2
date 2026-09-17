# K2 · P4 · **W-7（9 条 ignore 逐条方案）+ W-8（`J-7` 电气级审计更正）** ENG 交件 · v1 · 2026-09-17

> 性质：**ENG 只交「测量 + 方案」**（W-7 逐条 `修 / 具名豁免 + 证据`；W-8 电气级审计）。**批准/判定归监理**。
> 本件**不改板 / 不改 `criteria/` / 不改 `k2/hw/*.kicad_pro`**；probe 只在 `/tmp/opencode/w7/`。
> 板 = `k2/hw/k2_v4_8L.l5.kicad_pcb` `37019705ef994ccc`。依据：监理 #K2-19 §二 W-7/W-8、#K2-20 §二（J-7 转写）、handoff `ctx425k-inc17` §4-2/§4-3。

## 0. 两处**前提更正**（先读）

| 项 | 在册表述 | 本件实测 | 影响 |
|---|---|---|---|
| W-7 `track_not_centered_on_via` | handoff §4-2 注「余 **2** 条（同网偏心 0.035mm）」 | **30 条**（10 网：`I2C2_SDA` 10 · `P3V3_AUX` 8 · `PERSTA#` 6 · `PCIE_REFCLK0_N` 6 · `GND` 4 · `I2C2_SCL` 4 · `NRST` 4 · `MCU_VDD` 2 · `P3V3` 2 · `I2C1_*` 4 · `DS320_STRAP_B_ADDR1_15-8` 2） | 工作量从「2 条豁免」变「30 条修」 |
| W-8 `J-7` | 监理 #K2-19 §二「板实作 pad **电气几何 = 库**，差异仅图形/属性级；**电气级必须 0**」 | **35 件可库比对件中 33 件电气级存在差异**（31 件 pad 几何 + 2 件 pad 名集合）；仅 2 件电气级一致 | 「电气级 = 0」**不成立** ⇒ 该裁定之**依据**须重裁（见 §2） |

> 说明：两处更正均为**只读实测**，非口径主张；ENG 不据此改任何判据。

## 1. W-7：9 条 `ignore` 逐条方案（实测于 probe pro：9 条全置 `warning`，`--severity-all`）

probe 口径：板 + 同名 pro（仅改 `board.design_settings.rule_severities` 9 条 `ignore → warning`）+ 同目录 `fp-lib-table`/`lib/`（T-8）。
DRC 总账 = **181 warning**（= 既有 35 `lib_footprint_mismatch` + **新增 146**），`unconnected = 0`，error = 0。

| # | rule | 启用后违规 | 方案 | 施工方式（如「修」） | 风险 |
|---|---|---|---|---|---|
| 1 | `copper_sliver` | **0** | **修**（零成本） | 仅把 severity `ignore → warning`；实测 0 条 ⇒ **不多出任何 warning、不需处置** | 无 |
| 2 | `footprint_filters_mismatch` | **0** | **修**（零成本） | 仅把 severity `ignore → warning`；实测 0 条 ⇒ **不多出任何 warning、不需处置** | 无 |
| 3 | `footprint_type_mismatch` | **0** | **修**（零成本） | 仅把 severity `ignore → warning`；实测 0 条 ⇒ **不多出任何 warning、不需处置** | 无 |
| 4 | `tuning_profile_track_geometries` | **0** | **修**（零成本） | 仅把 severity `ignore → warning`；实测 0 条 ⇒ **不多出任何 warning、不需处置** | 无 |
| 5 | `missing_courtyard` | **40** | **修** | 为 40 件补 `F.CrtYd` 矩形（按 pad/本体外扩 0.25mm）；须同时复算 `courtyards_overlap`（error 级）不新增 | 中：40 件机械层；院界交叠风险 |
| 6 | `silk_over_copper` | **43** | **修** | 43 条绝大多数为**参考字段文本压在铜/盘上** ⇒ 移/缩 refdes 文本（纯丝印，不动铜） | 低：纯丝印位移 |
| 7 | `silk_overlap` | **21** | **修** | 21 条为 refdes 文本互叠 / 文本压本体丝印线段 ⇒ 同上（移/缩文本） | 低 |
| 8 | `track_not_centered_on_via` | **30** | **修** | 30 条同网偏心（含 4 条 `GND` 盘中孔）⇒ 把走线端点对齐到孔心（或移孔 0.0x mm）；须复算净距 + 单腿 ≥0.05 + 非 45°=0 | 中：端点微移，须逐条守恒 |
| 9 | `via_dangling` | **12** | **修** | 12 条 = 电源域冗余缝合孔（`MCU_VDD` 4 / `P3V3_AUX` 4 / `P3V3` 3 / `SW_U2` 1，F→B 贯孔但两端无铜）⇒ 删除（PDN 面连接由 In4 区自身承担）或加同网短线 | 中：删孔须证 PDN 不退化 |

**结论（W-7）**：9 条**全部建议「修」**（无一条申请具名豁免）⇒ 与 #K2-19 §二 W-7「deny-by-default、登记册 J-1/J-4 应然 = 全开检 + 违规 0」一致。
**分期**：
- **P1（零成本、零新增 warning、不改板）**：4 条零违规规则 `copper_sliver` · `footprint_filters_mismatch` · `footprint_type_mismatch` · `tuning_profile_track_geometries` 直接启用 ⇒ `rule_severity_manifest` 未登记 ignore **9 → 5**，DRC 总数 **35 → 35 不变**。
- **P2（146 项施工）**：其余 5 条按上表逐条修 ⇒ DRC 总数保持 35（`lib_footprint_mismatch`）＋ 5 条规则全绿。

复现：`cp k2/hw/k2_v4_8L.l5.kicad_pcb{,.prebak} ; python3 - <<…9 条置 warning…>> ; kicad-cli pcb drc --severity-all`（probe = `/tmp/opencode/w7/`）。

## 2. W-8：`J-7`（封装=库）**电气级审计**——接线前的必要更正

工具：`k2/tools/k2_w8_footprint_audit_v1.py`（只读；`--std-root AppDir/share/kicad/footprints --proj-lib k2/hw/lib`）。
逐件比 pad **数 / 名 / 形状 / 尺寸 / 钻孔 / 自转 / 局部位置**（W-8 电气级定义）。

| 电气级结论 | 件数 |
|---|---|
| 电气级完全一致 | **2** |
| **电气级存在差异** | **31** |
| 仅 pad 名集合不同 | 2 |
| 板侧无库链接（裸封装名，无法比对） | 24 |
| 合计 | 59 |

**典型差异（可复算，非版本噪声）**：
- 被动件：板 pad `0.6×0.7 RECT @ ∓0.45` vs 库 `0.8×0.95 ROUNDRECT @ ∓0.825`（`R_0603_1608Metric` 标准库原文实测 `(size 0.8 0.95)`）⇒ **板侧为收紧后的自定 land pattern**，非「图形级」。
- `J2`（SlimSAS 74pin）：板 pad `1.3×0.35` vs 库 `0.35×1.0` ⇒ 板侧 pad 为**预旋转/预置**布局。
- `E2`（SOIC8）：板 pad 5..8 `dy` 符号翻转 ⇒ 局部布局镜像。
- `J3`/`J4`：**pad 名集合**不同。

**根因（决定性）**：`k2/tools/k2_gen_v5.py:135` = `G_0603 = {"1": (-0.45, 0.0, 0.6, 0.7), "2": (0.45, 0.0, 0.6, 0.7)}`，而生成器把该封装**冠名为** `Capacitor_SMD:C_0603_1608Metric` / `Resistor_SMD:R_0603_1608Metric`（`k2_gen_v5.py:268-279`）。⇒ 板侧 land pattern 是**项目自定（收紧）**，**封装链接名却是上游标准库** —— 差异是**链接名与实体不符**，既非库版本噪声、亦非图形级差异。

⇒ 「板实作 pad 电气几何 = 库 / 电气级 = 0」**不成立**。因此 `lib_footprint_electrical` **不能**按字面「电气级 == 0」直接接绿；须由监理二择一重裁：

| 出路 | 内容 | 代价/后果 |
|---|---|---|
| **(甲′) 以板为准 = 发布「项目 land pattern 库」+ 改正 33 件的链接名** | 把板侧自定 land pattern 落为**项目库耐久件**（`lib/<Nick>.pretty` + `fp-lib-table` 条目），并把 33 件的封装链接从上游名（`Capacitor_SMD:*` 等）改为项目库名 ⇒ `封装=库` 对**独立入库件**成立、且**可检漂移**；DRC `lib_footprint_mismatch` → 0 | 需改 33 处**链接名**（不改 pad、不动铜）⇒ 电气零影响；库成为**受审耐久件**（非自指） |
| **(乙) 按库重落 33 件** | 用标准库 land pattern 重落 33 件 pad ⇒ 电气级真为 0 | 板级几何大变：需重跑净距/阻抗/DFM/扇出；部分为 PCIe/PDN 相关 ⇒ 破坏面大 |

ENG 建议（附根因证据）：**按 (甲′) 走** —— 落「项目 land pattern 库」耐久件 + 改正 33 处链接名，并在库件内 **逐条登记**「板侧 land pattern ≠ 上游标准库」（逐条表见 §2.1）。**不采纳**任何自动缩口径（含把库设为板侧同源快照后即宣称恒等）。**仍待监理就此重裁**（本件不改判据）。


### 2.1 电气级差异**逐条登记**（33 件；`37019705ef994ccc`）

| ref | 库 ID | 电气级结论 | 差异字段（首 4 组） |
|---|---|---|---|
| `C73` | `Capacitor_SMD:C_0402_1005Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `C74` | `Capacitor_SMD:C_0402_1005Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `C75` | `Capacitor_SMD:C_0402_1005Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `C76` | `Capacitor_SMD:C_0402_1005Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `C77` | `Capacitor_SMD:C_0402_1005Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `C78` | `Capacitor_SMD:C_0603_1608Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `C79` | `Capacitor_SMD:C_0402_1005Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `C80` | `Capacitor_SMD:C_0402_1005Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `C81` | `Capacitor_SMD:C_0402_1005Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `C82` | `Capacitor_SMD:C_0402_1005Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `C83` | `Capacitor_SMD:C_0603_1608Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `C84` | `Capacitor_SMD:C_0805_2012Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `C85` | `Capacitor_SMD:C_0402_1005Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `C86` | `Capacitor_SMD:C_0603_1608Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `C87` | `Capacitor_SMD:C_0402_1005Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `C88` | `Capacitor_SMD:C_0603_1608Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `C89` | `Capacitor_SMD:C_0603_1608Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `C90` | `Capacitor_SMD:C_0402_1005Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `D1` | `LED_SMD:LED_0603_1608Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `E2` | `ForgeOS:SOIC8_FRU` | **差异** | pad:5/dy, pad:6/dy, pad:7/dy, pad:8/dy |
| `J2` | `ForgeOS:SlimSAS_x8_SFF-8654_74pin_RASide` | **差异** | pad:1/sx/sy/dx/dy, pad:10/sx/sy/dx/dy, pad:11/sx/sy/dx/dy, pad:12/sx/sy/dx/dy |
| `J3` | `ForgeOS:MCIO_4i_SFF-1016_RASide` | 名集合差异 | pad_name_set |
| `J4` | `ForgeOS:MCIO_4i_SFF-1016_RASide` | 名集合差异 | pad_name_set |
| `R1` | `Resistor_SMD:R_0603_1608Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `R21` | `Resistor_SMD:R_0603_1608Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `R28` | `Resistor_SMD:R_0603_1608Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `R29` | `Resistor_SMD:R_0603_1608Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `R3` | `Resistor_SMD:R_0603_1608Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `R31` | `Resistor_SMD:R_0603_1608Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `R32` | `Resistor_SMD:R_0603_1608Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `R33` | `Resistor_SMD:R_0603_1608Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `R34` | `Resistor_SMD:R_0603_1608Metric` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx |
| `U2` | `Package_SO:SOIC-8_5.3x5.3mm_P1.27mm` | **差异** | pad:1/shape/sx/sy/dx, pad:2/shape/sx/sy/dx, pad:3/shape/sx/sy/dx, pad:4/shape/sx/sy/dx |

**覆盖缺口登记**：板上 **24 件**封装头为**裸名**（无 `LIB:NAME` 链接）⇒ J-7 对其**不可判**（含 `U6`/`U1`/`H1..H4`/`J6`/`J9`/`J11`/`J12`/`J13`/`D2`/`L1`/`R35..R45` 等生成器件）。「同时建 `fp-lib-table`（F-12）」应一并覆盖这 24 件，否则 J-7 的**判定域 < 板件全域**（本件并列登记，不主张口径）。

## 3. 复现与耐久件

```bash
cd /home/fila/jqdDev_2025/ic_hw
# W-7 probe：9 条 ignore → warning（仅 /tmp 的 pro 副本），再跑 DRC
AppDir/bin/kicad-cli pcb drc --format json --severity-all --output /tmp/w7.json /tmp/opencode/w7/k2_v4_8L.l5.kicad_pcb
# W-8 电气级审计（只读）
AppDir/usr/bin/python3.11 k2/tools/k2_w8_footprint_audit_v1.py --board k2/hw/k2_v4_8L.l5.kicad_pcb \
  --std-root AppDir/share/kicad/footprints --proj-lib k2/hw/lib --out-json /tmp/w8.json --out-md /tmp/w8.md
```

- 本件不改任何判据/板/pro；`criteria/` 逐字节未动。
- 施工（P1/P2）**待监理逐条批**后由 ENG 执行，并与 W-7 口径一致：**不新增检查齿、不缩口径**。
