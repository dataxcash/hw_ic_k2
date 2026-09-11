# m13 v57 — W3 Boundary **v1.23**（W3-CN.40 收口 + 连通性/可复现/PDN/DFM 多重集差/过孔预算 + **CO-53/CO-54 阻抗几何开放项**：G4..G7 判定不变）

> 契约 `m13_v57_w3_kickoff_card_v1_28.md`（冻结，未改 `0ae3016379cd1db2`）｜引擎 rev **W3-CN.40**
> ｜**取代 v1.22**（本件补 CO-54：SPEC↔交付几何**机判漂移清单**（7 项）+ 走廊 PITCH 复核 + 8L 叠层输入缺口**可达性实测** + Zdiff 重导 harness；CO-53 开放项不变）。
> 授权：CO-05..CO-54 各变更单（L2 自裁；CO-53/CO-54 属 L2/SI 记录 + 制造输入缺口，非 L1）。**冻结四源未动（4/4 MATCH）**。里程碑 tag `k2-v57-g7-l5-pass`（k2 `b5afe47`）。

## 1. 收口结论（机器可判 + 工件可独立重算）
- `verdict = FEASIBLE_ALL`；`gate_status.failed = []`；`certificates = []`；`status` PASS。
- **A-CN 全 PASS**：1d 32/32、1a 0 miss、1b 0、2a/2b 0、3a 72/72、3b/3c 0、4 交叉 0、5a keepout 0、
  5b 页间 True、**5d REFCLK 同层交叉 0（P/N + 页间）**、6 序无关（验证器 3 枚举序 byte-identical）、
  7 重发射 satisfied、8 证书归因 0 unattributed、**9 完整净距 0/0/0（tt/vt/vv）**、method `work 546/546`。
- 规模：**34 页**（32 data 含 3D nodes + 2 refclk）、`route_geometry` **320 段**、页级 via **320**、`same_layer_crossings = 0`。
- REFCLK 2/2：见证 `kind=direct_channel`；图纸内 P/N 残余 skew **0.0**（P 轨等长幂绕补偿 3.5635/1.3635 见 CO-45）；
  板上 SI 实测 max intra-pair skew **0.0031 ≤ 0.15**（34 页全查，含 REFCLK）。
- F-12 原子重发射 `m13_v57_w3_chip_landing_rows.json`（64 行），`authority.main_sha256 == sha256(主件)`。
- **字节可复现（CO-49）**：L4 板 `cdcb869e9827ec87`；构建×3 与全链（构建→L4→L5）×2 均**逐字节一致**（板/construction/validation/fab/dfm/si/G7 记录 共 7 件）。
- **PDN 事实核验（CO-50）**：平面层为**保留层、尚未铺铜**（冻结源与 L4 的铜铺铜 zone 均为 **0**，机器统计）；L4 仅新增 4 个非铜 rule area + tracks ⇒ 无平面铜被改写（原 `planes_present` 断言已改为可机判事实）。
- **DFM 判据强化（CO-51）**：`new` 由「按类型计数差」升级为**多重集差**（键 = type + 参与者 description）⇒ 同类型对调不再被掩盖；并显式机判**基线消失项 = 0**（即验收项「无 <0.075 项消失」），实测 new=0 / disappeared=0。
- **过孔预算闭合（CO-52，宪法第五章第 4 条）**：L4-F 逐网对比 SPEC 显式上限（bandX 4 / bandY 6 / REFCLK 2）⇒ 实测 max 4 / 4 / 2，**全部合规**；`total_vias = 252`（68 网）。
- **⚠ 阻抗几何开放项（CO-53/CO-54）**：交付 34/34 对对内中心 **0.500**（边距 0.295）vs SPEC `diff_pair.p_gap 0.175`；对间最小中心 0.550（SPEC `inter_pair_spacing_mm 0.875`）；SPEC `stackup/impedance` 仍 **6L** 而板为 8L ⇒ **阻抗符合性 NOT_DEMONSTRATED**（开放项 + 8L 介质叠层输入缺口）。
- **CO-54（本件新增）**：把 CO-53 从单点扩展为**机判漂移清单**（audit `ba87413ae4d8c7b4`）：F2 对间最紧 0.550@In6 长平行带（29.1mm，归因更正）、**F3 SPEC 自身不自洽**（`net_classes` 派生 PITCH 1.46 vs `corridors.tracks_y` 1.20，Δ0.26）、F5 三处“85Ω 基准”互不同（79.9 vs 85.1 vs JLC 官方 prepreg εr）、F6 34 对中 32 对的决定性平行段在 **In2/In6（带状线）**而 SPEC 模型为微带、F7 交付对内 0.5/0.6/0.58 并存；交付步距集合 {0.5,0.55,0.58,0.6,1.2,1.45} 与 SPEC 三项（0.175/0.875/1.2）**无一自洽**。**门判定不变**（零几何/阈值改动）。

## 2. 冻结栈与关键输入（现行）
| 项 | 件 | sha16 |
|---|---|---|
| 叠层（L2） | `m13_v57_layer_intent_rev5.json`（LID.1：signal = F/In2/In6/B；In1/In3/In5=GND，In4=P3V3） | `da4c3e4da37c6f94` |
| 走廊/见证（L2） | `m13_v57_big_w0r_corridor_model.json`（W0-R，未改） | `80ee9adb78a7e9ad` |
| 通道分配（L2/L3） | `m13_v57_co16_channel_allocation_v5.json`（CO16-ALLOC.5，CO-36） | `0bf6cdc203887a48` |
| 逃逸域（L2/L3） | `m13_v57_co37_escape_domain.json`（CO-37）＝ `.kicad_dru` 引用 `5616a9f873c9b844` | `5616a9f873c9b844` |
| SPEC（红线原件） | `SPEC_k2_v4.json`（未动） | `0bd52ed48e720b8c` |
| SPEC（引擎消费 ECO） | `SPEC_k2_v4.spec-rev-3.json`（ECS-001，CO-40） | `2d6dbd8bd8d667d7` |
| 规则 | `_shared/eda_core/drc_rules.json` | `0a459839e15960b8` |
| manifest | `m13_v57_s1_page_manifest.json` | `a8ef3ea8ecff99d7` |
| 冻结板（8L 基线） | `k2_v4_8L.kicad_pcb` | `fb07d25ac426ff84` |

## 3. 整链门禁（G4..G7，全部实测）
| 门 | 判定 | 证据（sha16） |
|---|---|---|
| G4/W3 | **PASS（FEASIBLE_ALL）** | 主件 **`dfa1d7c4a811b0da`**；landing `ef5704eb18c5e6d5`；resource_gate `dd373428fab1e7da` |
| G5/W4 | **PASS** | `m13_v57_w3_validation.json` `23b2b6d161f9bea1`（validator v2 `8f8ed665b645e8f7`；G-M1..6 True、A1.2/A1.3/A1.4 True、frozen=True，冻结集 = 红线四源 + 引擎 spec-rev-3 + 6L 上游，见 CO-46） |
| G6/L4 | **PASS** | 板 `cdcb869e9827ec87`（68 网/2441 段/252 via）；`m13_v57_l4_validation.json` `9521321baf7ff2b0`（rev **L4-V2**：L4-A..**F** True、viol 0；via_budget.all_within=true） |
| G7/L5 | **PASS（几何/DFM 项）** | fab `9a223923b029a1f9`；si `b16293f842ecf712`（rev L5-SI.4：skew 0.0031、pdn_status=reserved_not_poured、**`netclass_geometry.conformance = NOT_DEMONSTRATED`（CO-53 开放项）**）；**dfm `de14f887a7819c11`（L5-DFM.5：多重集 new=0 / disappeared=0 / 在册 0 未连）** |

DFM 收敛轨迹（v1.15 之后）：**D1/D2 归零（CO-23；W3-CN.37）→ 73（CO-23）→ 60（CO-37 D3c）→ 54（CO-41）→ 38（CO-43）→ 0（CO-45）**。
L4 板 `kicad-cli` 实跑：仅冻结基线 42 条 lib/silk，**铜层违规 0**（clearance/shorting/solder_mask_bridge/tracks_crossing 全 0）；基线铜违规数 = 0 ⇒ `new_total=0` 等价于「零铜层新增」。

## 4. v1.15 → v1.16 取代沿革（rev 与变更单）
- **W3-CN.27 → .36**（ROOT-16 线）：CO-05..CO-11（O4 落列可行性、安全 hop 拓扑、pair 域 v1.4/1.5、lane 平面）；
  CO-16/CO-18/CO-19/CO-22（东侧重派生、O4 有界幅值闭式蛇形、板内 J3 fan、lane 平面重整）⇒ 全板 **32/32 有效**（W3-CN.34/.35/.36）。
- **W3-CN.37**（CO-23）：板边真带（Edge.Cuts y=33/79、x=143）⇒ D1 copper_edge / D2 hole_to_hole 归零。
- **D3b 收官**（CO-25..CO-36，L2 自裁）：connector 落列器改「land 段长升序」（CO10_LXPRIO=landlen）⇒ CO16-ALLOC.5。
- **D3c**（CO-37）：SPEC 逃逸区规则域 `.kicad_dru`（0.075 + 4 具名 rule area，**显式排除 `PCIE_REFCLK*`**）。
- **L1 更正**（CO-38→CO-39）：D3a 非引脚缺陷，J2 侧 REFCLK 引脚由原理图网表 + SFF-8654 pinout 真源锁定 ⇒ 闸口 CLOSED。
- **W3-CN.39**（CO-40/CO-41）：SPEC-REV-3 ECS-001（J2 外列 N 单次换层 F.Cu→In2→F.Cu，每线 2 via）⇒ DFM 60→54。
- **W3-CN.40**（CO-42..CO-45）：远端带内接入（禁沿 A 排平行）＋ 对内偏移 `{P:0.0,N:-0.5}` ＋ dip 解耦 ＋
  图纸/nodes 一致化 ＋ P 轨等长幂绕 ＋ `A-CN.5d` ⇒ **DFM 38→0、G7 PASS**。

## 5. 覆盖性声明（宪法第五章第 1 条）
管辖对象 = 34 页（32 MCIO lane 页 + 2 REFCLK 页）/ 68 网 / 2 远端连接器（J3/J4）接入；**无「待定/暂不管」对象**。
每对象均有机器可读决策：`pages[*].nodes`（3D）+ `pages[*].vias` + `route_geometry` + `decision_contract`
（corridor_x / 分层链 / max_vias_per_line / pair_rule / REFCLK 层契约）。

## 6. 已知限制与豁免（如实声明，不得当作 PASS 依据掩藏）
1. **板字节已可复现（CO-49 解除）**：原 `pcbnew` 保存使 `segment/via/zone` 块的**顺序与 uuid** 每次重建漂移（其余块逐字节稳定）；
   CO-49 在 L4 applier 内做确定性规范化（连续同类 run 内排序 + 由内容派生 uuid5，只碰这三类块）⇒ **构建→L4→L5 全链 7 件逐字节可复现**；
   现行 L4 板 `cdcb869e9827ec87`（规范化前历史 sha 见 git 与 CO-45..CO-48 各 commit；稳定内容身份仍为 drawing `dfa1d7c4a811b0da`）。
2. **CO-16 层跨不相交豁免**：独立验证器 G-M4 记录 `span_blind_min_mm = 0.163083 < 0.175`、`span_blind_violations = 3`，
   依 CO-18 §1b/§4-2「同层跨不相交 ⇒ 物理净距不适用」豁免；`kicad-cli` 实跑同层净距 0 违规（与该豁免一致）。
3. **DFM `new`：已升级为多重集差（CO-51 解除原限制）** —— 键 = `(type, items[].description)`，并显式报 `disappeared_total`（基线消失，L4=tracks-only ⇒ 须为 0）；
   实测 new=0 / disappeared=0（42 条 lib/silk 基线全部在册）。
4. **未路由网 348 项**（冻结基线 416）：v57 范围为 68 条高速网；其余网不属本阶段（不得据此判 FAIL，也不得声称整板已布完）。
5. **⚠ 阻抗几何未调和（CO-53，开放项 / 交付阻塞）**：交付对内中心 0.500（边距 0.295）≠ SPEC `p_gap 0.175`；对间最小 0.550 中心（0.345 边距）vs SPEC `inter_pair_spacing_mm 0.875`；SPEC `stackup/impedance.model` 仍 6L 而板为 8L 且板内无介质叠层定义 ⇒ **阻抗符合性 NOT_DEMONSTRATED**（既非已证合规、也非已证违反）：需 **(a) 8L 介质叠层输入**（材料+逐层介质厚度，缺失）**(b) SI9000 重导 + SPEC ECO rev-4**（更新 stackup/impedance/p_gap 语义）**（c）走廊 PITCH 前提复核**。详见 `m13_v57_CO53_intrapair_geometry_impedance_open.md` 与 `m13_v57_CO54_spec_delivery_drift_inventory.md` `5c6cba3ca4785c29`（含 **8L 叠层输入缺口可达性实测**：仓库/板/公开源 `jlcpcb.com/impedance` 仅 4L/6L 有逐层表 ⇒ **8L 逐层厚度非检索可得，须板厂/上游供给**；Zdiff 重导 harness `tools/p3_v57_si_zdiff_rederive.py` 已就绪：模型保真度 85.05 vs 自陈 85.1，`--stackup` 通路实测，输入到位即产 ECO rev-4 提议）。
   **CO-47 已把该声明升级为谓词**：L5 记录 `dft.in_scope_unconnected_items == 0`（在册网按 kicad-cli 未连项网名解析）；实测 基线 68/68 在册网未连 → L4 **0/68**。
5. **G5 冻结集已校正（CO-46）**：原独立验证器的 `frozen_sha_check` 只钉 ECO spec + **历史 6L 板**，未覆盖红线 SPEC 原件与 8L 冻结板；
   CO-46 以「只增不减」补入 `spec_orig=0bd52ed4` / `pcb=fb07d25a`（并保留 `pcb_6l=f6273de6`）后 G5 仍 PASS。记录：`m13_v57_CO46_validator_frozen_set_fix.md` `bf7431bc6559ea98`。

## 7. 归档
变更单 CO-05..CO-46 记录与 DRC 明细（`m13_v57_co41_refclk_drc_after.json` / `m13_v57_co43_refclk_drc_after.json` /
`m13_v57_CO45_refclk_skew_meander_impl_record.md` `7b8cb5b1294d8c71` /
`m13_v57_CO46_validator_frozen_set_fix.md` `bf7431bc6559ea98` /
`m13_v57_CO47_l5_inscope_connectivity_predicate.md` `031fc91aa520cb92` /
`m13_v57_CO48_l5_g7_record_emit.md` `7e094c2db5bf3b3d` /
`m13_v57_CO49_l4_byte_reproducible.md` `6c27149fff749a1d` /
`m13_v57_CO50_pdn_fact_verified.md` `311e98163d49ac82` /
`m13_v57_CO51_dfm_multiset_metric.md` `922feaf4b5c8c143` /
`m13_v57_CO52_via_budget_closure.md` `eaaea6b5e4456ddc` /
`m13_v57_CO53_intrapair_geometry_impedance_open.md` `36f16620c7132da6`）已入库；本件取代 v1.21，v1.21 保留不改。
监理/tag 政策：`k2-v57-g7-l5-pass`（G7/L5 PASS）已 push；`git ls-remote` 核验 `^{}` → `b5afe47`。

End of boundary v1.23.
