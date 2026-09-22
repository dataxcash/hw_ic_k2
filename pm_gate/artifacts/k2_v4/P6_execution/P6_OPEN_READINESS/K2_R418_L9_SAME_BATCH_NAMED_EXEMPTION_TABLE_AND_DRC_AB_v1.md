# K2 · R418 —— **l9 同批具名豁免表**（R270 §一 项3）+ **l8↔l9 DRC A/B**（只读）

- **from** ENG·ARCHER（续接会话 · 应监理「按已批准计划推进当前阶段 · **fail-closed**」）· **to** 监理 · **owner 闸口 0**
- **authority**：**R270 §一 项3**（②-DN `#K2-73` EX-1 ✓ · l9 同批豁免表）· #K2-73 §五/§O-4（l9 = 基线 + **具名豁免表** + rev=7 同笔）· #K2-67 · 监理自动续推
- **边界**：只读清算。未出包 · 未烙板 · 未派工 · 未改任何件/判据。受审板 **l9 `77aaa63fe016b450`**。

## 1. 在册具名豁免 × l9 现值（清算）
| ID | 裁定 | 辖域 | 豁免条款 | **l9 现值** | 判 |
|---|---|---|---|---|---|
| **EX-1** | #K2-73 Q1 准 | `PCIE_DN_OUT{0..7}_{P,N}_MCIO` ×16 | 『≤2 孔/线』⇒ 允许 **4 孔/线** | **逐网 4 孔（16/16 一致）** | **deviation 在 ⇒ 豁免生效** ✅ |
| **#K2-67 族** | #K2-67 准（限 2 对） | courtyard 零重叠 `U1↔J9`/`U1↔J13` | 2 对互叠**豁免** | `courtyards_overlap` = **0** · `missing_courtyard` = 54 | **deviation 不在（休眠）** · ⚠ **lineage 差异**：#K2-67 实测板为 `/tmp/opencode/l9`（`39b58aa1` lineage）≠ 现行 landed l9 ⇒ **rev=7 齿化维落地时须按现行板重核** |
| **DRC warning 9 类** | rev=6 manifest | 9 类 disposition | 在册 | l9 出现**恰为此 9 类**（未登记 **0/9**） | 合规 ✅ |

## 2. **未豁免 · 必修项**（不得出包）
- **DRC error 59**：`clearance 21` · `shorting_items 19` · `hole_clearance 13` · `tracks_crossing 6`
- **新增 warning**：`track_dangling` l8 **1** → l9 **5**（**+4**）
⇒ 二者**无任何在册豁免覆盖** ⇒ 属 R410/R411「项2 落搬迁落地缺陷」；**修复前不得出包、不得据以过 P4**。

## 3. l8↔l9 DRC A/B（同会话 · 同仪器 · 同 pro）
| 类型 | l8 | l9 |
|---|---|---|
| **error 合计** | **0** | **59** |
| └ clearance / hole_clearance / shorting_items / tracks_crossing | 0 / 0 / 0 / 0 | 21 / 13 / 19 / 6 |
| warning: missing_courtyard / silk_over_copper / track_not_centered_on_via / lib_footprint_mismatch / silk_overlap / via_dangling / silk_edge_clearance / copper_sliver | 54 / 37 / 34 / 20 / 15 / 6 / 2 / 1 | **逐类相同** |
| warning: **track_dangling** | **1** | **5** |
| unconnected | 0 | 0 |

⇒ **差异完全可归因于落搬迁**（承 R410/R411）。

## 4. 阶段门自查（fail-closed）
**P4 未全绿 ⇒ 不出包 · 不下单 · 不越阶段。** 余阻：
① **item2 ②-UP** = **owner**（#K2-142 在途 · 两选项已带成本标价 · R416/v63）｜② **l9 底图 59 error 落地缺陷** = **监理**（`v62` 处置）｜③ **D1** 正式闸输入抽取值 = **监理**（R417 §D1）｜④ **item10 `criteria` rev=7** = **gate 属主**｜⑤ item13 出包/DFM = 依赖 ①–④。

（owner 侧无需新请示：#K2-142 之选择已在途，本件不含新 owner 项。）

—— ENG（ARCHER）· 2026-09-22 · 只读清算 · owner 闸口 0
