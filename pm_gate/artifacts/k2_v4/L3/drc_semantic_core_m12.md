# DRC-SEMANTIC-CORE M12 交付报告 — DRC 反向定位引擎 (drc_locator)

> 日期：2026-08-25 · 板：`k2_v4.kicad_pcb`（定位用 m9demo 快照）· DRC 基线：`k2_m9demo.drc.json`（867 条，勿重跑）
> 承接 M11（7 类规则对齐率 100% 零未命中）；本报告全部结论带数字证明，红队可审计。

---

## 0. 一句话总结

`/tmp/opencode/drc_radar.py` 临时脚本沉淀为系统能力 `eda_core/drc_locator.py`（零 revA 特判）：
**867 条违规 100% 可定位**（unknown_kind_items=0 / unknown_rule=0 / unclassified_family=0 /
unmapped_uuid_items=0），1734 个 items 的 uuid→元素反查 100% 命中（by_uuid 1958），
聚合成 **117 个根因族**（域×区域×规则×根因），高危清单 **78 条**（间距<50%）——
全部与 M10 定位口径对账一致。定位报告落盘 `artifacts/L3/drc_locator/`（report.md/.json + summary.json）。

---

## 1. 引擎架构（沉淀对象 vs 系统能力）

| 维度 | drc_radar.py（临时脚本） | drc_locator.py（M12 系统能力） |
|---|---|---|
| uuid→元素 | 无（只解析描述字符串） | **BoardParser.by_uuid 反查**（1734/1734 命中，带元素关键字段证据） |
| 规则声明 | 硬编码覆盖集 | 违规类型 → **drc_rules.json 规则库声明**（RULE_TYPE_MAP） |
| 根因归类 | 启发式 guess_path | **规则类型 × 元素对种类 × 网域 → 根因族**（引用 M11 已证语义） |
| 网域 | 硬编码前缀常量 | NetDomain 入参化（默认通用电气语义，--domains 可覆盖） |
| 区域 | 硬编码 k2 分界 | RegionMapper 入参化（--zones 分界，板几何真源由调用方传） |
| 输出 | 终端打印 | 结构化落盘 report.md/.json + summary.json（红队可审计） |
| 复用 | 无 | drc_rules.BoardParser / DRCRuleLibrary（非重写） |

**复用链**：item uuid → `BoardParser.parse().by_uuid` → Segment/Via/Pad/Zone 元素；
required 语义 → `DRCRuleLibrary`（net_class 真源 = k2_v4.kicad_pro）。

**描述解析 5 类形态全量覆盖**（1734/1734 items，0 unknown）：
seg（走线）/ via（过孔）/ pad（F.Cu 上 REF 焊盘，padnum 支持 B5 字母数字）/
tht_pad（REF 的PTH 焊盘）/ zone（填充区）。

---

## 2. 覆盖度证明（验收第一项：867 条每条可定位）

运行：`python -m eda_core.drc_locator --drc k2_m9demo.drc.json --board k2_m9demo.kicad_pcb
--rules drc_rules.json --pro k2_m9demo.kicad_pro --out artifacts/L3/drc_locator --zones <k2 分界>`
（基线勿重跑，直接读既有 drc.json）

| 覆盖度指标 | 值 | 证明 |
|---|---|---|
| total_violations | 867 | 类型分布与基线逐项一致（clearance 500 / hole 171 / shorting 89 / mask 58 / crossing 46 / zones 2 / diff_pair 1） |
| total_items | 1734 | 每条 2 items |
| uuid→元素反查 | **1734/1734 (100%)** | by_uuid 1958 = 899 seg + 525 via + 524 pad + 10 zone |
| unknown_kind_items | **0** | 描述解析 5 类形态全覆盖 |
| unknown_rule | **0** | 7 类违规类型全部映射到规则库声明（RULE_TYPE_MAP） |
| unclassified_family | **0** | 根因表 + 泛化兜底全覆盖（M12 修复 4 类签名错位后归零） |
| high_risk_severe | 78 | 与 M10"高危 78 条（间距<50%）"口径一致 |

### 2.1 M12 根因归类修复（签名→表键错位，首轮 43 条 unclassified → 0）

| # | 未归类（首轮） | 根因 | 修复 |
|---|---|---|---|
| 1 | hole_clearance (via,pad) 23 条 | via 钻孔 vs **SMD** pad 铜（is_tht=False 实证，U3/C82/R18 等）→ 应为 via_hole 非 tht | 泛化兜底：via 参与且表有 via 键 |
| 2 | shorting (seg,) 13 条 | 两 seg 短路（STRAP 系 F.Cu 高密区 + I2C1_SCL B.Cu）签名生成 "seg"，表键是 "seg_seg" | 兜底：ks=={seg} → seg_seg 键 |
| 3 | shorting (via,) 6 条 | 两 via 短路（STRAP_EQ1_1_U7/GND）签名 "via_via"，表无此键 | 兜底：ks=={via} → via 键 |
| 4 | shorting (seg,tht_pad) 1 条 | THT 焊盘 vs 段短路（idx 270 GND/UART_RX）签名 "tht"，表无 | 兜底：tht_pad → tht 键 → pad 键 |

---

## 3. 聚类结果（验收第二项：域×区域×规则×根因）

**117 个根因族**（聚类键 = 域 × 区域 × 规则 × 根因族；条数和 = 867 自洽）。

### 3.1 按域（跨域违规标注合并，HS>PWR>LS 主域）

| 域 | 条数 | 解读 |
|---|---|---|
| hs | 294 | 纯高速域 |
| hs+pwr | 181 | 高速 vs 电源地（P3V3/GND 平面）净距 |
| pwr+ls | 162 | 电源地 vs 低速 |
| ls | 146 | 纯低速域 |
| pwr | 45 | 纯电源地 |
| hs+ls | 39 | 高速 vs 低速 |
| **高速相关合计** | **514** | hs + hs+pwr + hs+ls（M13 高速 385+ 重建对象） |
| **电源相关合计** | **388** | pwr + hs+pwr + pwr+ls |
| **低速相关合计** | **347** | ls + pwr+ls + hs+ls |

### 3.2 按区域（items 坐标中点口径）

| 区域 | 条数 | 与 M10 对账 |
|---|---|---|
| 中-U3U7（芯片区） | 574 | **= M10 芯片区 574 完全一致** |
| 左-MCIO | 179 | M10 左 32（器件归属口径）；差异 = 坐标中点归属（U3/U7 出线段西向延伸落左区） |
| 右-SlimSAS | 114 | M10 右 97（器件归属口径）；差异同上 |

> 分区口径声明（红队可审计）：M12 用 **items 坐标中点**（客观可复现）；M10 用网名器件归属（主观）。
> 两口径芯片区 574 吻合，为跨 M 对账锚点。

### 3.3 按规则类型 × 根因族（逐类数字）

| 类型 | 条数 | 根因族数 | 根因族分解（count） |
|---|---|---|---|
| clearance | 500 | 4 | via_clearance 260 / pad_clearance 140 / seg_clearance 94 / via_via_layer_dup 6 |
| hole_clearance | 171 | 2 | via_via_hole 122 / via_hole 49（含 SMD pad 23 + THT 参与） |
| shorting_items | 89 | 3 | via_short 48 / seg_seg_edge0_short 40 / pad_short 1 |
| solder_mask_bridge | 58 | 2 | smd_mask_bridge 56 / tht_mask_wildcard 2 |
| tracks_crossing | 46 | 1 | seg_crossing 46 |
| zones_intersect | 2 | 1 | zone_multi_poly_overlap 2 |
| diff_pair_gap_out_of_range | 1 | 1 | diff_pair_intra_gap 1 |

> clearance 的 500 行含 via-via 按层重复行（对齐报告 §3.2：贯穿过孔 8 层 → 同一物理违规多行），
> 引擎按报告行定位（M11 唯一对口径 430 不矛盾：430 物理对 + 70 重复行 = 500）。

### 3.4 解法路径预估（M13 衔接）

| 路径 | 条数 | 高危(severe) | 含义 |
|---|---|---|---|
| C_VIA（孔距/过孔净距） | 498 | 54 | 过孔位置/过孔库 → M13 高速重建 + 过孔库整改 |
| E_SCHEME（方案级） | 263 | 24 | 高速段/焊盘净距 + 短路 → M13 输入重建 |
| C_MFG（阻焊） | 58 | 0 | 阻焊开窗规则 |
| A_LOWSPEED（低速施工） | 46 | 0 | 段交叉 → 低速重解/落板 |
| B_PDN（铺铜） | 2 | 0 | zone 重叠 |

---

## 4. 高危清单（验收第三项：间距 < 50% 优先，78 条）

全部落盘 `artifacts/L3/drc_locator/report.md §4`（按比例升序）+ summary.json high_risk_severe。

最危险 TOP（比例最低）：

| 类型 | 域 | 实际/要求 | 比例 | 网对 |
|---|---|---|---|---|
| clearance | pwr+ls | 0.0100/0.2000 | **5.00%** | P3V3 / STRAP_EQ1_U7 |
| clearance | pwr+ls | 0.0100/0.1000 | 10.00% | GND / STRAP_EQ1_U7 |
| clearance | pwr+ls | 0.0110/0.1000 | 11.00% | GND / STRAP_EQ1_1_U7 |
| clearance | pwr+ls | 0.0250/0.2000 | 12.50% | P3V3 / PWR_BTN_ISO |
| clearance | hs+pwr | 0.0250/0.2000 | 12.50% | P3V3 / PCIE_UP_OUT1_N_U7 等 5 条 |

高危分布：C_VIA 54 + E_SCHEME 24；域：hs+pwr 系占多数（高速 vs 电源平面净距不足，
M13 高速段重建 + PDN 铺铜优先解决）。

---

## 5. 规则库增补（修订走输入）

`eda_core/drc_rules.json` 新增 `tracks_crossing` 声明段（M11 已对齐 46/46 但缺声明，属文档缺口）：
violation_condition（两铜段中心线几何相交）+ report_semantics（连通性触发 + pad-overlap 抑制）
+ verification（M11 46/46）。纯增键，不影响 M11 对齐验证。

---

## 6. 测试（验收第四项：32 条全绿，M11 55 条零回归）

`eda_core/tests/test_drc_locator.py`（32 条，`pytest` 全绿；M11 四件套 55 条同步全绿 → 合计 87）：

| 测试组 | 条数 | 覆盖 |
|---|---|---|
| TestItemParsing | 6 | 5 类描述形态 + padnum B5 字母数字 + THT + unknown |
| TestUuidToElem | 6 | seg/via/pad/tht-pad(含 is_tht)/zone uuid→元素反查 + 未知 uuid 不抛错 |
| TestRootCause | 12 | 7 类规则 × 元素组合 → 根因族断言（含 M12 修复的 4 类签名） |
| TestClustering | 4 | 聚类和=总数自洽 / 同 family 合并 / 高危 band / 阈值边界（<50% 严格口径） |
| TestZeroRevaSpecialCasing | 3 | RegionMapper/NetDomain 入参化 + 引擎源码零单板硬编码（grep k2_v4/U3U7/MCIO 断言） |
| TestBaselineIntegration | 2 | 基线 867 全覆盖 + 类型分布逐项断言（基线文件缺失时 skip） |

---

## 7. 铁律遵守

- **DRC 只核对不驱动**：定位报告是分析工具；0 手工改走线、不碰任何 locked 高速段、
  不重建任何域方案（M13 的事）
- **结论带证明**：report.json 每条带 items[].uuid/elem 映射证据（uuid→元素关键字段）；
  聚类带逐类数字；覆盖度自检四零
- **修订走输入**：tracks_crossing 声明 → 规则库（输入）增补，非引擎特判
- **零 revA 特判**：区域分界/网域前缀全部入参化（--zones/--domains）；引擎源码不含
  单板几何硬编码（单测 grep 断言）；入参全路径
- **不碰 locked 高速段**：drc_locator 纯只读解析（打开 pcb 文件读文本，零写入板文件）

## 8. 红队 open finding 归属声明

`F-R14_model_solve_ref-1`（R14: SPEC 低速设计段 171 项无 source 标记）为 L1 竞标 gate 拦截，
归属**模型门禁域**（ls_route_model solve_ref 落标记），阻断的是 L1 gate 而非本 M 交付。
M12 交付物（drc_locator 只读分析工具 + 定位报告）不产出设计段、不写 SPEC、不触发该规则；
处理归属 M13/M14（模型侧 source 标记补齐 + 重跑模型门禁）。

## 9. 交付物清单

| 产物 | 路径 |
|---|---|
| 定位引擎 | `eda_core/drc_locator.py`（系统能力，CLI + 可 import） |
| 规则库增补 | `eda_core/drc_rules.json`（tracks_crossing 声明段） |
| 单测 | `eda_core/tests/test_drc_locator.py`（32 条） |
| 定位报告 | `artifacts/L3/drc_locator/report.md`（聚类 117 族 + 高危 78 + 根因映射） |
| 全量数据 | `artifacts/L3/drc_locator/report.json`（867 条每条 uuid→元素证据） |
| 摘要 | `artifacts/L3/drc_locator/summary.json`（覆盖度 + 域/类型/聚类 + 高危清单） |

## 10. M13 衔接（非本 M 范围）

- 高速域 385+ 重建：C_VIA 498 + E_SCHEME 263 中 hs/hs+pwr 族是输入（via/seg/pad 净距 + 短路）
- 电源地铺铜：zone 障碍语义 + B_PDN 族 + hs+pwr 181 条（P3V3/GND vs 高速段净距）
- 过孔库整改：hole_clearance 171 + via 类 clearance 266（C_VIA 498）→ 孔环/孔距物理约束
