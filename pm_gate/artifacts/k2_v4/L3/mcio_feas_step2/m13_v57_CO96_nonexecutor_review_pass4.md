# CO-96（非执行者侧对抗评审 pass 4/4）— 对象 = rev-11 基线（CO-91/92/93/94/95 + 全链 + 不变量）

> 日期 2026-09-12｜工具 `tools/p3_v57_co96_nonexecutor_review_pass4.py` `75d1d82f1f83a992`
> 记录 `m13_v57_co96_nonexecutor_review_pass4.json` `8b591e5030aca11d`
> 基线：SPEC rev-11 `d85f10f722ba22b0`｜板 `0e636a67c1472462`｜boundary v1.61 `18c55bf4cb1bc77d`｜冻结四源 4/4 MATCH
> **verdict = `REVIEW_DONE_FINDINGS_OPEN`**（基线身份 OK / 牙齿 OK / 6 项发现）
> 本件为**独立会话**（rev-10/rev-11 由 CO-93/CO-95 执行；本会话 context 归零续接）⇒ 满足 `L2_STRUCTURE_v2.0.md:137` 非自评要求。

## 0. handoff §7-1 指定三问的判定
| 问 | 判定 |
|---|---|
| Q1 `plane_reachability_requirement` 是否可机判闭合？ | **否**（当前只能「声明闭合」：几何真覆盖 35/55，14 项待 L3 派生、6 项待 L1 裁决；gate 恒不返回 PASS）|
| Q2 rev-10/rev-11 两次重基线之间是否有未登记的漂移？ | **有 1 处**（F1）+ 1 处陈旧（F5）|
| Q3 CO-95 分类是否完整？ | **是**（55 = 35+8+6+6，恰覆盖全部非 GND entry）|

## 1. 发现（均机判 + 可复现）
### F1（中·红线邻近 / 谱系）rev-10 重建 `power_pad_connect` 时**静默丢弃** `retired_superseded_bom`
- 证据：rev-9 ppc 键含 `retired_superseded_bom`（CO-89 留存：pre-rev-9 冻结 BOM **173 entries / 9 blocked** + 孤儿分析 **55/2**）；rev-10/rev-11 ppc **无该键**；`p3_v57_co93_pdn_rev10_derive.py` 源码**零处**引用该键（重建 ppc 时未搬运）；CO-93 变更说明**未登记**此移除。
- 缓解：数据**未丢失** —— 冻结源 `SPEC_k2_v4.json`（`0bd52ed48e720b8c`，173/9）与 CO-89 记录（`n_orphan=55/2`）均可找回。
- 影响：现行 rev-11 谱系无法追溯 pre-rev-9 BOM 的退役，违红线「退役几何/决策必须**显式留存**（不得静默放弃）」的字面要求。
- 处置：**rev-12 变更单**——回填 `retired_superseded_bom`（由 rev-9 复制）**或**显式登记其移除理由；须写入变更说明。

### F2（中·闸可闭合性）`plane_reachability_requirement` 为「声明可闭合」而非「几何可闭合」
- 证据：`requirement.gate` = `tools/p3_v57_co95_in4_reachability.py`，对 rev-11 返回 `OPEN_needs_region_ruling`（非 PASS）。
- **8 个 `covered_bridge_target` 命中的桥区（`P3V3_BCU_BRIDGE_IN4`/`P3V3_AUX_BCU_BRIDGE_IN4`/`MCU_VDD_BCU_RESISTORS_IN4`）`polygon=None`**（几何未建、属 L3 派生）⇒ 这 8 项被计为「非 gap」，实际是**声明覆盖**而非**几何覆盖**。
- 结论：真几何覆盖 = **35/55**；声明待 L3 = **14**（8 桥区 + 6 band 退役义务）；待 L1 = **6**。⇒ **当前不可机判闭合**（依 L3 几何 + L1 裁决）。
- 处置（建议）：co95 闸改**三分态**输出（geometric / declared-pending-L3 / ruling-pending-L1），避免 `covered_bridge_target` 被读作已满足；`requirement` 文本补闭式判据。
- 非声明：SPEC 文本「含 L3 派生区域」为**声明**支撑，本件**不判其违规**，只登记「不可机判闭合」。

### F3（中·闸脆弱性）`needs_region_ruling` 判定依赖自由文本子串
- 证据：co95 `classify` 中 `declared_status[net]["needs_region_ruling"] = ("需要" in why or "须裁" in why)`。P3V3_AUX 西侧 3 pad（C90.1/R1.2/U1.15）**仅因** `plane_reachability_status[].why` 含「须裁」而被判 `needs_region_ruling`；`P3V3_AUX` 本**有** In4 区（在 `nets_with_region` 内）⇒ 若无该文本子串，3 pad 静默降级为 `l3_obligation`（**L1 → L3 降级**）。
- 12V_IN（3 pad）由独立规则 `net not in nets_with_region` 兜底 ⇒ 稳健。
- 处置（建议）：以机判谓词（如「本网在目标区域内的名义网 ≠ 本网」）替换文本子串。

### F4（中·覆盖范围）可达性要求 scope 仅 `ppc.entries`（非 GND）
- `gnd_stitch_via` 实落 **40**、`power_zones[].vias` **17**、`decoupling_via_to_plane.vias` **0** —— 同依赖平面覆盖，**无任一闸判**。
- 处置（建议）：扩展 requirement scope 或在 SPEC 显式声明排除理由（GND 走 GND 平面、zone via 由 zone 多边形自证等）。

### F5（低·陈旧 live 字段）`power_pad_connect.board_realized` 仍记 CO-89 的 223/86
- rev-11 决策为 **189/120**；该字段由 `old.get("board_realized")` 原样搬运，rev-10/rev-11 均未同步。
- 未被 `pdn_apply.py` 消费 ⇒ **无功能影响**；但属 live 机读块内自相矛盾（易被误读为 223 已实落）。
- 处置（建议）：rev-12 同步或标注 `superseded_by`。

### F6（低·潜在）co95 `in_poly` 用 **bbox** 而非真点在多边形内
- 现行 2 个显式 polygon（`P3V3_EAST`/`MCU_VDD_WEST`）均为**轴对齐矩形** ⇒ bbox == 精确，**无实害**。
- 牙齿：L 形合成多边形 + bbox 内/形外探针 ⇒ bbox 测试假阳（True）、真 PIP 拒绝（False）⇒ 非矩形时确会假阳。

## 2. 复核为 OK（对抗性验证后通过）
- **V1 不变性**：rev-9→rev-10 与 rev-10→rev-11 的 `pd` 之外**递归深比 0 变更**（仅 `/spec_version`）⇒ 两次重基线的「pd 外仅 spec_version 变」声明**成立**。
- **V2 完整性**：co95 分类各行和 = 非 GND entries（55）⇒ 分类**无遗漏/无重复**。
- **V3 blocked schema**：SPEC `gnd_stitch_via.coordinates` 的 60 blocked 以 `blocked`/`status=="blocked"` 标注 ⇒ 与 `pdn_apply.py` 消费口径**对齐**（60 跳过 / 40 施加）。**边界 §6-13/14 所记「blocked schema 未对齐」指上游 `gnd_stitch_gen` 产出，非现行 SPEC**（本件澄清）。
- **V4 重复坐标**：gnd_stitch `(133.83,59.1)` 出现 2 次系**声明共享单孔**（basis 明证：`PCIE_DN3_P` 与 `PCIE_DN4_N` 共享同一 GND via）⇒ **非缺陷**。
- **V5**：冻结四源 4/4 MATCH；板 `0e636a67c1472462` 逐字节不变。

## 3. 牙齿
F1（阳控 rev-9 带键 / 负控回填后不再报）、F2（8/8 桥区几何未建 + gate 非 PASS）、F3（去文本子串即翻转）、F4（scope 计数）、F5（陈旧计数）、F6（合成非矩形 bbox 假阳）——**各检测器均有齿**。

## 4. 非声明
只读评审；**不改 SPEC/板/阈值/冻结源/引擎**；未重跑全链（核对指纹）；零坐标搜索、无 while；
F1 须由**后续变更单（rev-12）**闭合，本件不施加任何 SPEC 改动；rev-11 的既有链门禁（G4..G7、回归闸、CO-91/92）状态**不受本件影响**。
