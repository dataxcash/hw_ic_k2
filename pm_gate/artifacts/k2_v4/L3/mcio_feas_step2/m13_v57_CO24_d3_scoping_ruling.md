# CO-24 — 【L2 自裁 + 1 项 owner 闸口】D3 归因更正与范围界定：DFM new 73 ≠ 单一 REFCLK 问题

> 2026-09-12｜裁判：ARCHER（续接会话 ARCHER-2）｜输入：CO-23 入库态 `a7de961`｜性质：**归因裁定 / 变更单范围界定（不落地几何）**

## 0. 结论（先说）
CO-19 §1 / CO-23 §4 把 DFM 残留 73 **全部**归因于「既有 `PCIE_REFCLK0/1` 路线」——**不成立**。
实测（CO-23 板 `k2_v4_8L.l4.kicad_pcb` `70f3fdc4149db146`，`kicad-cli 10.0.5`，判据 `k2_v4_8L.kicad_pro`）按「是否涉及 REFCLK 网」分类：

| 类别 | clearance | shorting | crossing | mask | 小计 |
|---|---|---|---|---|---|
| 仅 REFCLK | 4 | 4 | 1 | 22 | **31** |
| REFCLK × 数据 | 6 | 3 | 4 | 16 | **29** |
| 仅数据 / 其他 | 8 | 1 | 0 | 4 | **13** |
| 合计 | 18 | 8 | 5 | 42 | **73** |

⇒ **60 条**与 REFCLK 相关（可望由 refclk 变更单消除）；**13 条与 REFCLK 无关**（数据逃逸/阻焊），refclk 变更单消不掉。
⇒ 因此「D3 消 REFCLK ⇒ DFM new=0 ⇒ milestone」的链路**断裂**；D3 必须拆成 D3a/D3b，且 D3c 需 owner。

## 1. D3a（L2）：REFCLK 走线几何 —— 2 个根因，均为引擎可控
**(a) REFCLK 差分对自短路/自交叉（P/N 几何 bug）。** `refclk_place()`（引擎 L1125）把 P/N 各自做
`j2.y ± POL_OFF`、`run_y ± POL_OFF`、`rise_x ± POL_OFF` 三次独立偏移；当 P/N 的**段结构不同**
（如 P 只有 0.19mm 竖段、N 有 28.24mm 长 run）时，两线包络中心距仍为 0.19 < width 0.205 ⇒ **铜重叠**。
实测样例：`PCIE_REFCLK0_P`(0.19mm stub @132.65,45.9) × `PCIE_REFCLK0_N`(28.243mm run @135.0,46.09) 短路；
`REFCLK1_P × REFCLK1_N` `tracks_crossing` + `clearance 0.1734`。（对照 SPEC `refclk_isolated` 要求对间隔离。）
**(b) 连接器侧「pad-field transit」未建模。** 见证件 `m13_v57_big_w0r_corridor_model.json`
`refclk_passage_witness.per_page[*].kind` 明确写 `pad_field_transit: "delegated to connector side (W2/R3-R4)"`，
但引擎把最后一段直接画成 `[west=82.35, run_y+off] → far_pad` **一条斜线**：
- `REFCLK0`：`(82.35,46.09) → (58.3,45.75)`（J3 侧），横穿 J3 数据扇；
- `REFCLK1`：`(82.35,63.47) → (60.7,61.45)`（J4 侧），横穿 J4 数据扇。
实测该斜线造成 `REFCLK0_N × DN_OUT0/1` `tracks_crossing` ×4、`REFCLK1_P × DN_OUT6/7` `shorting` ×3、
以及 J3/J4 pad 上的 `shorting`（`REFCLK0_N × J3 A1[GND]`、`REFCLK1_N × J4 A18[DN7_N]`）。
**处置（L2，允许自裁）**：按见证窗口 `chain_windows_y`（REFCLK1：`[62.525,63.575]`）实现连接器侧 Manhattan 接入
（先降到 pad 行再水平接入 / 或经见证窗竖直下降），并重写 P/N 为**全程等距平行**（同一段结构 + 统一偏移），
使 A-CN.5（keepout 零交）扩展到「数据 F.Cu pad-access 段 + J3/J4 pad 场」。
预计消除 60/73（31 + 29）。

## 2. D3b（L2）：逃逸区净距**判据单位错误**（引擎 + 独立验证器同错；W3/W4 假阴性）
SPEC `escape_transition_zone`（ECN-001）语义 = **铜距**下限 0.075（实测接入段铜距 0.1725）；
引擎按其派生 `TT_ESC = width + 0.075 = 0.28`、`VT_ESC = 0.3525`（**中心距**口径，等价铜距 0.075，✓ 自洽）。
但独立复核器 `tools/p3_v57_co11_placement_verify.py` 的 `seg_pad_gap()` 返回的是**中心距**，
却直接与 `ESC = 0.075` 比较（`if g < ESC - TOL`）——**少减 width/2 = 0.1025** ⇒ 判据放宽 0.1025。
**实证**：`DN_OUT5_N` F.Cu pad-access `(58.0,60.2)→(57.1,61.45)` 对 `J4 A7[GND]`（0.3×0.7 @57.7,61.45）
中心距 = **0.1607**（⇒ 复核器判 PASS），实际铜距 = 0.1607 − 0.1025 = **0.0582** ⇒ shop DRC 报错（要求 0.175）。
⇒ W3/W4 的「320/320 0 违规 PASS」对 **pad 净距**是**假阴性**；A-CN.9 亦不含 pad 项。
**处置（L2）**：验证器 pad 判据改为**铜距**（≥ `escape_clearance_mm`，若采纳 D3c(a)）；重导数据扇接入段，
使逃逸区铜距 ≥ 判据。**注意**：0.4mm 节距 + 0.3mm pad + 0.205mm 线 ⇒ 双净距需 0.555 > 0.4，**0.175 铜距物理不可行**（见 D3c）。

## 3. D3c（**owner 闸口候选**）：冻结 SPEC 逃逸区 vs shop DRC 判据冲突 ⇒ DFM new=0 目前不可达
- `k2_v4_8L.kicad_pro`：netclass `PCIe85` clearance **0.175**、`POWER` **0.2**，`rules.min_clearance 0.1`，
  **无 `.kicad_dru` 自定义规则、无 rule area、`drc_exclusions=[]`** ⇒ 全板统一 0.175，**不含 SPEC 逃逸区松弛**。
- 而 SPEC（冻结）明确 J2/J3/J4 与 U6 0.4mm 节距接入段采用 **逃逸区微净距**（ECN-001）。
- 二者**不可同时满足**：接入段铜距 ~0.06–0.17 必然 < 0.175；把逃逸段压到 0.175 需 0.555 包络，不可能。
⇒ **红线「不得放宽净距阈值」**禁止 ARCHER 自行改判据。二选一，需 **owner** 裁定：
  (a) **推荐**：把 SPEC 已冻结的 `escape_transition_zone`（铜距 0.075）编码为 `.kicad_dru` 规则域
      （scope = J2/J3/J4/U6 pad 场矩形，域外仍 0.175/0.2）——实现 SPEC，而非放宽 SPEC；
  (b) 修 SPEC 要求接入段 ≥0.175（物理不可行；或须改窄逃逸线宽 → 破坏 85Ω 阻抗）。
**在 (a) 落地前，G7/DFM `new=0` 不可能达成，D4 milestone tag 不可打**（不得 partial pass / 伪造 sign-off）。

## 4. D3d：`solder_mask_bridge 42` 的构成
`42` = refclk 相关 **38**（22 仅 refclk + 16 refclk×数据，随 D3a 消除）+ 数据相关 **4**
（`DN_OUT4/6_P × GND`、`DN_OUT4/6_P × DN_OUT4/6_N`，0.4mm 节距 + 阻焊开窗扩张的固有效应）。
后 4 条同属 D3c 判据域（阻焊桥与逃逸区同源），随 (a) 或 owner 裁定一并处置。

## 5. 建议的 D3 执行顺序（下一会话）
1. **D3b 判据修正**（先修，保证不再假阴性）：验证器 pad 判据改铜距口径；A-CN.9 增 pad 项（逃逸段按 SPEC 值）。
2. **D3a 引擎几何**：连接器侧 Manhattan 接入 + P/N 全等距平行 → 目标消 60。
3. **D3c**：拿 owner 裁定 (a) 后落地 `.kicad_dru`；随后 **D3d** 复核 mask。
4. 全链重跑 G4→G7（新 rev W3-CN.38+ / ALLOC.5+），new=0 后打 milestone tag（`pm_gate/TAG_POLICY.md`）。

## 6. 红线 / 未改物
本裁定**不落地任何几何**：未改四冻结源（`0bd52ed48e720b8c / a8ef3ea8ecff99d7 / fb07d25ac426ff84 / 0a459839e15960b8`）、
未改 `k2_v4_8L.kicad_pro`、未改引擎/验证器、未改任何板/图纸、零坐标搜索。
