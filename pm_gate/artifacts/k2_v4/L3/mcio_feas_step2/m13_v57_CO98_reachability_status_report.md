# CO-98（L2 自裁 · PDN 可审计性）In4 平面可达性**义务状态报告** — 机判化 CO-96 F2/F3/F4，并关闭 F6

> 日期 2026-09-12｜工具 `tools/p3_v57_co98_reachability_status_report.py` `126f890d4a596062`
> 记录 `m13_v57_co98_reachability_status_report.json` `d3a903d9296daa83`
> 基线（fail-closed）：SPEC rev-11 `d85f10f722ba22b0`｜co95 记录 `61db48a283beeaae`｜板 `0e636a67c1472462`
> **零 SPEC/板/阈值/冻结源改动**；**不改 co95 权威记录字节**。

## 1. 角色（与 co95 的分工）
- **co95**（`p3_v57_co95_in4_reachability.py` + 其记录）仍是**逐 entry 分类的权威闸**；本件**只读**之。
- **co98** 把 CO-96 的三项发现**机判化 + 显式化**：F2（义务分态与可闭合性）、F4（scope 排除）、F3（裁决依据是否机判）。
- 本件 verdict **永不 PASS**（只要存在 `declared_pending_l3` 或 `ruling_pending_l1`）。

## 2. L2 自裁（本件）
**F6 修复**：co95 的 `in_poly` 由 **bbox 近似**改为**真·射线法 PIP**（工具 `d5b102a1f23bb5dd`，取代 `a2e16d6e08eef731`）。
- 现行 2 个显式 polygon（`P3V3_EAST`/`MCU_VDD_WEST`）均为轴对齐矩形 ⇒ **输出逐字节不变**（co95 记录 sha 仍 `61db48a283beeaae`，CO-95/CO-96 引用不失效）⇒ 属**行为中性加固**（消除非矩形多边形的潜在假阳）。
**F2/F4**：不改 requirement（改 scope/谓词属 SPEC 变更 = rev-12），改为**机判化其义务状态**（下表），使「声明覆盖 ≠ 几何覆盖」与 scope 排除不再隐含。

## 3. 结果（机判）
| 量 | 值 |
|---|---|
| 分类完整性 | 55 = 35 + 8 + 6 + 6（`integrity.ok = true`）|
| `geometric_covered` | **35**（真几何覆盖，PIP 判定）|
| `declared_pending_l3` | **14**（8 桥区 target 声明 + 6 band 退役义务；几何待 L3 确定性派生、当前未建）|
| `ruling_pending_l1` | **6**（区域/电源域裁决）|
| `machine_closable_today` | **false** |
| scope 排除（F4） | `gnd_stitch_via_realized` **40**、`power_zones_vias` **17**、`decoupling_vias` **0**（本 requirement 不判）|

**裁决依据分解（F3）**：6 项 `ruling_pending_l1` 中 **5 项机判可判**（3× `machine:net_has_no_in4_region`（12V_IN）+ 2× `machine:via_inside_other_net_in4_polygon(MCU_VDD:MCU_VDD_WEST)`（P3V3_AUX 西侧 C90.1/U1.15）），
**1 项仅文本**（`P3V3_AUX R1.2` @[51.725,37.0] 不在任一异网显式 In4 多边形内）⇒ 建议以机判谓词替换文本子串并补 R1.2 判据。

## 4. 牙齿
`pip_rejects_bbox_approx`（L 形合成多边形内 bbox 点被 PIP 拒绝）+ `integrity_detects_miscount`（注入 +1 必判不完整）⇒ **2/2**。

## 5. 非声明 / 归口
- 只读；不改 SPEC/板/阈值/冻结源/co95 记录；零坐标搜索。
- **仍未闭合（非 PASS）**：F2 的**几何闭合**（14 项 = L3 施工期派生）、F4 的 **scope 扩展**（属 SPEC 变更）、F3 的 **R1.2 判据**。
- **L1（停并升级 owner，一句话）**：`ruling_pending_l1` 6 项 = 电源域/区域归属——`12V_IN` 承载（C88.1/U2.4/U2.6）与 `P3V3_AUX` 西区归属（C90.1/R1.2/U1.15 vs 名义 MCU_VDD）需 owner 裁。
