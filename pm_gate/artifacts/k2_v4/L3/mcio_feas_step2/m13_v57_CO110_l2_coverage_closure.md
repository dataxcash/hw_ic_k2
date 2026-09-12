# CO-110 — L2 自裁施加：参考平面判据入 CO-87 矩阵（F-C）+ CO-106 D 读径修复（F-E）+ In4 走廊空洞按设计定案（F-D / R5'）

- 判定：**`L2_CLOSED_NO_SPEC_CHANGE_NO_REBASELINE`**
- 触发：CO-108 **F-C/F-D** + 本件新发现 **F-E**
- 变更：仅 2 个**闸工具**（`p3_v57_co87_l2_acceptance_coverage.py`、`p3_v57_co106_reference_plane_gate.py`）——**零 SPEC/板/阈值/冻结源改动 ⇒ 不重基线**（先例 CO-105）
- 复现：`python3 tools/p3_v57_co110_l2_coverage_closure.py`

## 1. 三项施加

**(a) F-C —— ch.2 判据「参考平面」正式入矩阵**
CO-87 覆盖矩阵原 5 行（容量/长度/过孔/PDN 压降/热），而宪法 ch.2 L2 裁判标准 = 「走廊闭合、等长预算、**参考平面**、PDN 压降、热」⇒ **登记册缺一行**。现补入第 4 行：

| item | status | evidence（机取自 CO-106 记录，非手填） |
|---|---|---|
| 参考平面（ch.2 L2 裁判标准） | `INDETERMINATE` | CO-106 verdict=`INDETERMINATE_REGION_SCOPED`；`declared_copper_missing=0`；残余 `In5←In4` 54 段 ⇒ CO-110 判为按设计 In4 走廊空洞（bridge zone = B.Cu） |

新增牙齿 `ch2_criteria_all_have_rows=true`（ch.2 五项均有行，反空真）。n_closed=3 / n_open=**3**。

**(b) F-E —— CO-106 D 项读径修复（新发现缺陷）**
CO-106 的 D 项原读 `co87["inputs"]["matrix"]`，而 CO-87 记录**无 `inputs` 键**（`matrix`/`constitution` 在顶层）⇒ `KeyError` 被 `except` 吞掉 ⇒ 覆盖性检查**恒空真**（`co87_has_reference_plane_row: null`、items=[]），「参考平面」行缺失**从未被校验**。已改为读 `constitution.ch2_l2_criteria` + 顶层 `matrix`；复跑后 D 项机读 `co87_has_reference_plane_row=**true**`、items=6。

**(c) F-D / R5' —— In4 走廊空洞按设计定案（L2）**
- **R5'（L2）**：**不开 In4 走廊铜** —— 这是**确认** PM T2-ECN-1/2 既有设计，**非反转** ⇒ CO-109 的 OWNER 升级**撤回**。
- In5 在走廊 x∈(49.8,88.37) = **In6-单参考域**；SI 终判 = 外部（SI9000 + 板厂阻抗券）。
- 证据（承接 CO-109，机判复核）：声明 bridge band 覆盖 In5←In4 miss 点 **6.0%**（75/1260）；走廊多边形覆盖 **100.0%**（1260/1260）。

## 2. 机判（全 True）+ 牙齿
- `A_r5_prime_ruled` / `B_fc_reference_plane_row` / `C_fe_co106_d_readpath` / `D_fd_by_design_void` 全 True
- 牙齿 3/3：`row_absent_detector`（负控：无行必被检出）、`ch2_keyword_floor`（五项关键词齐全）、经 CO-109 的覆盖检测器

## 3. 结论与残余
- F-C / F-D / F-E **三项关闭**；CO-87 覆盖矩阵现覆盖 ch.2 全部五项判据。
- **未闭合（外部/owner）**：走廊 In5 的 SI 终判（SI9000 + 板厂券）；PDN 压降/热（PM）；②c bridge zone B.Cu 几何声明（缺 palette）；L1 三项（12V_IN 承载 / P3V3_AUX 西区归属 / L1① 0.875）。
- 非声明：不做 SI/阻抗数值计算；不改 CO-106 分类字节（by-design 叠加由本件承载，改判属后续 rev）。
