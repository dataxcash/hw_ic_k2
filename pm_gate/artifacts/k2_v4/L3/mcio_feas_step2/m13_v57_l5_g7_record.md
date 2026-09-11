# m13 v57 — **G7（L5 sign-off + 知识提升）记录：FAIL → REOPEN owning layer**

> 2026-09-11｜卡：`m13_v57_l5_kickoff_card_v1.md`｜检查器：`tools/p3_v57_l5_signoff.py`（只读取证；KiCad pcbnew/kicad-cli 10.0.5）
> ｜主体：L4 板 `k2_v4.l4.kicad_pcb`（sha `33ded90443f2e2c2`）vs 冻结基线 `k2_v4.kicad_pcb`（`f6273de6…`）

## 1. 结论
- **G7 = FAIL**（记录已出，证据如下）。按 rollback 规约：**reopen owning layer（W3/L4）**；**不得在 L5 就地修**。

## 2. 记录与证据
| 记录 | verdict | 关键数 |
|---|---|---|
| `m13_v57_l5_fab_record.json`（`51f6a759…`）| n/a | 6 铜层；track/via/net 计数 + 钻孔表 + 指纹 |
| `m13_v57_l5_dfm_dft_record.json`（`23c2b327…`）| **FAIL** | DRC：冻结基线 43 → L4 **496**；**新增 453** = `{clearance:171, shorting_items:117, hole_clearance:26, copper_edge_clearance:26, solder_mask_bridge:110, hole_to_hole:3}`；未连项 416→352 |
| `m13_v57_l5_si_pi_emc_record.json`（`c2bf87a8…`）| **FAIL** | 线宽 0.205 合规 ✓；**对内等长 max skew = 24.476mm ≫ 0.15mm（FAIL）**；hole/mask/edge 见 DRC |

## 3. 根因（闭式、指向 W3 口径）
- **W3 度量不完整**：`same_layer_crossings` 计了「真交叉 + 共线重叠（段-段）」与「via-via 间距」，
  **未计** ① **track↔track 净距（平行最小间距）** ② **via↔track 净距** ③ 孔-铜 / 板边铜 / 阻焊桥。
  453 条新增违例**全部涉及本 66 网**（已逐条按网名分类核实），即图纸几何在真实铜（0.205 线宽 / 0.35 via）下
  不满足净距 ⇒ **并非既有铜的旧账**。
- **SI 对内等长未纳入 W3 构造**：P/N 落点（J2 内侧/外侧槽、J3/J4 全局槽）未做长度匹配 ⇒ skew 最高 24.5mm。

## 4. 影响 / 回退
- G6（L4）的**连通性 DOD 达成**（每节点按处方连接；图纸只读；板消费一致），但其产物**不满足制造/信号签核**。
- 回退：**reopen W3**（补全度量口径 = 净距/孔铜/板边/阻焊；并纳入对内等长约束），重跑 W3→W4→L4→L5。
- L5 不修：本轮仅出证据。

## 5. 指纹
- L4 板 `k2_v4.l4.kicad_pcb` `33ded90443f2e2c2`｜图纸 `caa516abdaf8e823`（rev W3-CN.22）｜冻结四源 MATCH
- 记录：fab `51f6a759…` / dfm `23c2b327…` / si `c2bf87a8…`

## 6. 下一步（阻塞上报）
- 依宪法：**发现上游问题立即停机回上层**。W3 需补全 **净距类度量（track/via/孔铜/板边/阻焊）+ 对内等长**，
  属新的 W3 修订周期（版本化、预授权域内可实施；触及契约口径须按 ROOT-1 记录）。

## ROOT-21 修订（O1b + O3 实施；2026-09-11）
- 图纸 rev **W3-CN.25**（`c17c5a42`）：**REFCLK 差分对 P/N 补齐**（原只布 P；现 2 页 × P/N = 4 条，P/N 分离
  ≥0.38、成对中心取见证 `pair_centre_window_y`/`channel_y`、keepout 零交 A-CN.5a PASS）；net 名取
  manifest（`PCIE_REFCLK*_P/N`）。
- L4 重发：**68 网 / 338 段 / 256 via**（construction `6fb043a1`；validation `9abcc836` PASS；板 `b63e6c09`）。
- D8/G5 验证器 v2：**PASS**（G-M1..G-M6 + 双度量 0 + A1.2/A1.3/A1.4；A1.3 现覆盖 REFCLK P/N）。
- L5 重测：DFM **479**（含新增 N 轨的 26 条）；SI 等长 **skew 24.476mm** 不变 ⇒ **G7 仍 FAIL**；
  **O1**（净距不可行，已实证与域/序无关）与 **O2**（板既有铜/读板）仍待 owner。


---

# G7 复核（ROOT-22: O4/R1-R2 收口后重跑；引擎 W3-CN.30；2026-09-11）


> 2026-09-11｜图纸 rev **W3-CN.30**（sha16 `05f7bd10ab3b45b6`）｜板 `k2_v4_8L.l4.kicad_pcb`（sha16 `225fccb23c5b1b5f`）
> ｜工具 `AppDir/bin/python3.11 tools/p3_v57_l5_signoff.py`（L5-FAB.2 / L5-DFM.2 / L5-SI.2，8L 口径）

## 1. 结论
- **SI（对内等长）：PASS** — `max_intra_pair_skew_mm = 0.0574 ≤ 0.15`（O4 长度侧保持闭合）。
- **DFM/DFT：FAIL** — `new_total = 426`（shop 规则 `k2_v4_8L.kicad_pro` 口径）。**G7 保持 OPEN**。
- 处置：**CO-06 变更单**（D1 跨层过孔桶短路触 L2；D2..D6 为 L3 净距模型缺口）。

## 2. 量（8L）
| 项 | 值 |
|---|---|
| copper layers | 8 = F/B/In1..In6 |
| tracks / vias | 1710 / 256（drill 全部 0.2）|
| SI | width 0.205 ✓；skew 0.0574 ✓（rule 0.15）|
| EMC | 平面 In1/In3/In4/In5；信号层 F/In2/In6/B（LID.1 8L）|
| DRC baseline（冻结 8L 空板）| 73（lib_footprint/silk，既有）|
| DRC L4 | 499（=73 既有 + 426 新）|
| **new violations** | **426** = shorting 108 / clearance 176 / solder_mask_bridge 103 / hole_clearance 24 / copper_edge 10 / tracks_crossing 4 / hole_to_hole 1 |

## 3. 门禁口径说明
初跑用板侧 `k2_v4_8L.l4.kicad_pro`（**过时 6L 规则**：min_via 0.5/drill 0.3/edge 0.5/仅 Default netclass）⇒ 伪阳性 1026。
改用 **`k2_v4_8L.kicad_pro`**（规则取自冻结 `drc_rules.json` 语义 + `k2_v4.kicad_pro` 网络类，含 PCIe85 0.175）后 `new=426`。
**判据不放松**：426 全部为真实几何（样本见 CO-06 §2）。

## 4. 独立复算
- `verify_w3_acn9_independent.py`（自带几何核/阈值）：tt/vt/vv = **0/0/0**（同层端点层口径）。
- 跨层口径由 `kicad-cli pcb drc`（KiCad 10.0.5）给出；两者口径差即 CO-06 D1/D2（跨层/自对不在当前 W3 契约内）。

## 5. 指纹
图纸 `05f7bd10ab3b45b6`｜landing `8fa507a8cc765264`｜G5 validation `44372895944abd78`（W3-VALv2.3 PASS）
｜L4 construction `aa25f636c5468f97`｜L4 validation `69d3dea9aa4253fe`（L4-A..E PASS）
｜fab `136048baf1c8fbdf`｜dfm `cd20e835118f4469`｜si `ae94efdfc99e5e2a`
冻结四源 `0bd52ed48e720b8c / a8ef3ea8ecff99d7 / fb07d25ac426ff84 / 0a459839e15960b8`（未改）。
