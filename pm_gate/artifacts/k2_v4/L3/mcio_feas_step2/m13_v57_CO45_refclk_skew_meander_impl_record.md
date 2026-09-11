# CO-45 — 【L2 自裁】REFCLK 对内间距 0.5 / ECS dip 解耦 / P 轨等长幂绕 / 图纸-nodes 一致化 ⇒ **G7 DFM new 38→0**

> 2026-09-12｜性质：**L2 实施**（叠层内走线/过孔策略/等长窗口，均属自裁范围；无 L1 变更）｜前置：CO-44 `aff1f3905ed37c67`（残余 38 定位）
> 引擎 rev：**W3-CN.40**｜板：`k2_v4_8L.l4.kicad_pcb` `4d36212f6492262b`｜**G7/L5 PASS（DFM new=0）**
> 执行说明：本条前半由前序 ARCHER 会话（pane 8）实施；该会话于 G5 复跑途中被看门狗（`.omo/supervision/watch.py` 探询超时）硬重启。续接会话（本件）定位并修复其遗留的 G-M3 探针缺陷（§3），随后重跑全链并收官。

## 1. 残余 38 的成因（承 CO-44）
- 对内 0.38 中线 ⇒ 边距 0.175，KiCad 实测 0.1734 < 0.175 ⇒ 判违规（clearance/shorting）。
- J2 P 侧 0.19 出线 jog vs `pad 9/27[GND]`：0.1325。
- `N` via#2 vs 同页 P 轨：0.1025（需 ≥ `ECS_DX=0.4525`）。
- 远端 `REFCLK*_N` 链横越 J3/J4 连接器阻焊开窗 ⇒ mask_bridge 18；REFCLK vs `DN_OUT*_MCIO` 交越。

## 2. 实施（引擎 `tools/p3_v57_w3_constructive.py`，rev W3-CN.40）
1. **对内偏移重定**：`REFCLK_OFF = {P: 0.0, N: -0.5}`（取代 ROOT-21 的 ±0.19）。
   - `P=0.0`：内列 P 由 pad 中心线直出 ⇒ **J2 侧 jog=0**，消 0.1325×2；
   - `N=-0.5`：N 轨北移，与 P 轨中心距 0.5（边距 0.295）⇒ **消 via#2 vs P 轨 0.1025 与对内 0.1734**；
   - 抬升列以 P 列为基准，N 偏移量计入 U6 余量（`_off_lo`）。
2. **ECS-001 dip 解耦**：`refclk_transit_nodes()` 将 `via1_y`（pad 直出 stub 端，受 pad10/14 净距）与 `dip_y`（N 轨 y）解耦，绕行量由封堵列端部闭式给出。
3. **远端口径闭式化（取代 CO-43 的 2 选 1 启发）**：`refclk_far_transit()` 固定分配 —— N 走北线、P 走南线，P 取西抬升列 `xj_near`、N 取东列 `xj_far`；带内间距 `FAR_LINE_STEP 0.38 → 0.5`（边距 0.175→0.295）。函数内做**真实线段相交自检**，相交即 `RuntimeError`（停机，禁静默回退）。
4. **图纸/nodes 一致化**：远端接入折线由调用方统一追加，修补 CO-43 中 `nodes` 丢失远端 waypoint（图纸与 nodes 不一致）的缺陷。
5. **等长补偿（幂绕）**：`refclk_meander()` 在 P 轨水平段插入南向三角幂绕，闭式解 `(n, h, A)`（幅值上界 `REFCLK_MEANDER_A_MAX=2.0`），实测额外长度 == 所需值；残余 skew 超 `0.15` 即 `RuntimeError`（SPEC `PCIe85.intra_pair_skew_mm` 不放宽）。
6. **REFCLK 交叉自检**（教训 1：引擎既有 crossing/净距套件不含 REFCLK）：引擎新增 `A-CN.5d`、独立验证器 v2 复算 —— REFCLK 同层 P/N（含页间）交叉必须 = 0。
7. **L5 SI 覆盖 REFCLK**：`p3_v57_l5_signoff.py` 原跳过非 data 页 ⇒ REFCLK 对（同属 net_class `PCIe85`）未受 skew 判据；现纳入，`skew_pages` 覆盖全 34 页。

## 3. 续接会话修复的 G-M3 探针缺陷（方法门，非判据放宽）
`--scale` 黑盒探针（G-M3 线性性）构造的副本不自洽，CO-45 幂绕上线后暴露 `RuntimeError`：
- **症状 1**：副本仅平移 pad 锚点 `+300*c`，而 REFCLK 构造消费**绝对板框常量**（ECS via 列 x、走廊边界、In2 列墙）⇒ 幂绕带 `span_max` 变负 ⇒ 误报不可行。修复：探针**不复刻 REFCLK 页的 x 坐标**（工作单元仍按页线性计）。
- **症状 2**：探针把 data 页从 manifest 剔除 ⇒ `_far_row_span()` 只取到**单排** pad 行 ⇒ 远端折叠成直线 stub（未真正构造远端接入）。修复：**全页进 manifest**（`refclk_place` 内部本就只迭代 non-data 页）。
- 两处均为**探针保真度**修复，真实板路径（`--scale 1`）逐字节不变（drawing `dfa1d7c4…`）；G-M3 现 `K=2 work=1076`、`K=4 work=2152`、`per_copy=538`，线性成立。

## 4. 门禁实测（全链重跑）
| 门 | 判定 | 证据 |
|---|---|---|
| G4/W3 | **PASS（FEASIBLE_ALL）** | `m13_v57_w3_joint_assignment.json` **`dfa1d7c4a811b0da`**（W3-CN.40）；`A-CN.1..9` 全 PASS（含 `A-CN.5a=0`、**`A-CN.5d=0`**）、`crossings=0`、`work 546/546`；landing `ef5704eb18c5e6d5`；resource_gate `dd373428fab1e7da` |
| G5/W4 | **PASS** | `m13_v57_w3_validation.json` `aeddea9e82b26e9e`：G-M1..6 全 True、A1.2 序无关 True、A1.3 0 viol、A1.4 True、`frozen=True` |
| G6/L4 | **PASS** | 板 `4d36212f6492262b`（68 网 / 2441 段 / 252 via）；`m13_v57_l4_validation.json` `50dd2f4f7177d3d2`：L4-A..E 全 True、viol=0；drawing `dfa1d7c4a811b0da` |
| G7/L5 | **FAB ok / SI PASS / DFM PASS** | fab `12d1f3944944550a`；si `a3187aed93c48b6b`（max intra-pair skew **0.0031 ≤ 0.15**，34 页）；dfm `2536493073df3df8`（**verdict=PASS, new_total=0**） |

**DFM 收敛轨迹**：60（D3a 基线）→ 54（CO-41 ECS-001）→ 38（CO-43 远端带内接入）→ **0（CO-45）**。
**DFM 诚实性核对**：`drc.l4_applied.by_type = {lib_footprint_issues:12, lib_footprint_mismatch:29, silk_edge_clearance:1}`（= 冻结基线 42 条 lib/silk，计入不计），**铜层违规 = 0**（clearance/shorting/solder_mask_bridge/tracks_crossing 全 0）；`.kicad_dru` `3148703240d54420` **未改**，逃逸区规则显式排除 `PCIE_REFCLK*` ⇒ REFCLK 仍按 shop 判据（0.175）判定，未被放宽掩盖。
**EMC**：solder_mask_bridge_violations=0、copper_edge_violations=0。**SI**：全 PCIE 轨 0.205mm 达标。

## 5. 修正 CO-44 的缺口判读
CO-44 判「对内 ≥0.45 须 witness v2 keepout 校正（元件体→铜包络）」「远端须先取阻焊开窗几何」。实测表明：两项**并非真缺口** —— 对内间距改由**北移 N 0.5**（而非南抬撞 C80 盒）达成，`A-CN.5a=0` 即未触 keepout；远端 mask 18 随带内线北移出开窗、并经 `A-CN.5d`/DRC 复核归零。故 CO-25 v1 的 witness v2 请求**不再阻塞 D3a**（保留存档，若后续 L1 级变更仍可复用）。

## 6. 红线核对
四冻结源 **4/4 MATCH**（`0bd52ed48e720b8c / a8ef3ea8ecff99d7 / fb07d25ac426ff84 / 0a459839e15960b8`，原件未动）；`intra_pair_skew_mm`/净距阈值**未放宽**；GND/PWR 平面未改信号；`while=0`、零坐标搜索、一次求解；无 partial pass。

## 7. 指纹
engine `tools/p3_v57_w3_constructive.py` `d095f9abf6a35cf3`｜validator v2 `6c112d3ad30c9424`｜l5_signoff `74f4ec01d704293a`｜canonical **W3-CN.40 `dfa1d7c4a811b0da`**｜landing `ef5704eb18c5e6d5`｜board `4d36212f6492262b`｜dru `3148703240d54420`｜spec-rev-3 `2d6dbd8bd8d667d7`
