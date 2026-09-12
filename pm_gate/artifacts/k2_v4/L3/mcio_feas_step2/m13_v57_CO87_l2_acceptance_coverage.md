# CO-87（L2 自裁）— L2 合格标准覆盖性机判：宪法 ch.5 §4「PDN 压降」与 ch.2「热」= NOT_DEMONSTRATED（缺输入）

> 日期 2026-09-12｜工具 `tools/p3_v57_co87_l2_acceptance_coverage.py`（只读/确定性）
> 记录 `m13_v57_co87_l2_acceptance_coverage.json` `5d07348d71d7a13e`｜依据 `_shared/docs/LAYOUT_CONSTITUTION.md` `3b0a8550e61a7637`

## 1. 为何立本件
宪法 **第五章第 4 条（数学闭合）**明文：*"容量总和 ≥ 需求；长度预算闭合；过孔预算闭合；**PDN 压降达标**。
任何一条不等式不闭合，整层作废"*；**第二章**把 **热** 列为 L2 裁判标准（L2 裁判权 = 电源完整性工程师）。
L2 侧 CO-63..CO-86 的闸覆盖了 容量/长度/过孔/PDN **架构**，但 **PDN 压降** 与 **热** 全仓无输入、无证据、
也从未在 boundary 登记 —— 属"静默未闭合"。本件把它机判化，**不允许当作已闭合**。

## 2. 覆盖矩阵（`n_closed=3 / n_open=2`）
| ch.5 §4 / ch.2 项 | 状态 | 机判证据 |
|---|---|---|
| 容量总和 ≥ 需求（走廊闭合）| **CLOSED** | drawing `verdict=FEASIBLE_ALL`、`gate_status.failed=[]`（A-CN.1d 32/32、2a/2b 0）|
| 长度预算闭合（等长窗口）| **CLOSED** | L5 SI `max intra-pair skew = 0.13 mm ≤ 0.15`（CO-70 判据 = 按层加权电气长度）|
| 过孔预算闭合 | **CLOSED** | L4-F `checks['L4-F']=True`、`via_budget.over=[]`、`total_vias=252` |
| **PDN 压降达标** | **NOT_DEMONSTRATED** | SPEC rev-8 全字段扫描 **0 命中**（扫描 3962 字段；电流/压降预算/载流判据皆缺）|
| **热** | **NOT_DEMONSTRATED** | 同上 0 命中（功耗/热阻/环境温度/温升判据皆缺）|

## 3. 缺的不是"算"而是"输入"（机器提取的需求清单）
`required_inputs_for_PDN_and_thermal` 由 SPEC `pd.zone_defs.power_zones[*].targets` **自动提取**（非手写）：

| 分区 | 网 | 层 | L3 几何状态 | targets |
|---|---|---|---|---|
| P3V3_EAST | P3V3 | In4.Cu | L3_CONSTRUCTION_DERIVED | U3/U7 P3V3 pads、C65-C83 去耦、C67/68/72 |
| MCU_VDD 西区等 | MCU_VDD | In4.Cu | L3_CONSTRUCTION_DERIVED | MCU U1、U2/U4、C84-C92、E2 |
| P3V3 西区源桥 | P3V3 | In4.Cu | L3_CONSTRUCTION_DERIVED | U2.pad5、U4.pad3、C84.pad1（原 6L 走 B.Cu，CO-74 退役）|
| P3V3_AUX → MCIO | P3V3_AUX | In4.Cu | L3_CONSTRUCTION_DERIVED | J3.A9、J4.A9 |
| MCU_VDD 上拉 | MCU_VDD | In4.Cu | L3_CONSTRUCTION_DERIVED | R29/R31-34（μA 级，SPEC 有 0.3mm 依据）|

**需 PM/owner 提供（数据与需求，非 L1 拓扑裁决）**：① 各轨负载电流（U3/U7 redriver 静态+动态、MCU/存储、
J3/J4 MCIO A9 供电、去耦/上拉）；② 允许压降预算（V 或 %）与采样点定义；③ In4 铜厚/温度修正 + L3 平面几何；
④ 热：各器件功耗、环境温度/风速、可接受温升与热阻路径判据。

## 4. 牙齿 / 反空真
- **阳性对照**：注入合成件 `{"pd":{"load_currents":{"P3V3":1.2},"note":"≤ 3.3V 2.5A"}}` ⇒ 扫描器命中 ≥2 项（`synthetic_current_detected=true`）⇒ 0 命中是**真缺**，不是扫描器失灵。
- **需求存在性对照**：宪法文本确含 `PDN 压降达标` / `PDN 压降、热`（`requirement_text_found_in_constitution=true`）⇒ 不是在追一条不存在的条款。
- **非空真下限**：SPEC 实扫字段数 **3962**（>0）⇒ 不允许"因为没扫到东西而 PASS"。
- **记录复跑两次逐字节一致**（确定性）。

## 5. 结论与非声明
- 结论：**L2 的六域结构决策已终结（CO-63..CO-86）**；但**宪法 ch.5 §4 的 PDN 压降子项与 ch.2 的热项
  为 NOT_DEMONSTRATED（缺输入）**，本件显式登记为已知限制 —— 既不宣称 PASS，也不判 FAIL。
- **非声明**：不代填假设值（禁止伪造 sign-off）；不改 SPEC/板/图纸/阈值；不做 L1 裁定；本件不改变 G4..G7 判定。
