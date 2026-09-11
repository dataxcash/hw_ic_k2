# CO-54 — 【L2/SI 自裁】SPEC↔交付 几何**机判漂移清单**（收 CO-53 未覆盖面）+ 走廊 PITCH 复核 + 8L 叠层输入缺口**可达性实测** + Zdiff 重导 harness

> 2026-09-12｜定层：**L2/SI**（LAYOUT_CONSTITUTION 第二章：叠层/走廊/等长/**SI 物理承载**；裁判权 = SI/PI 工程师）⇒ **自裁，无 owner 闸口**
> 依据：handoff `k2-v57-co53-impedance-open-20260912r.md` §5 收口路径 (1)(2)(3) + CO-53 §3.3 + 教训 ④「SPEC 字段与交付几何可能长期脱节 ⇒ 任何"看起来合规"的字段都要机判比对」
> 性质：**机判事实审计 + 缺口可达性实测 + 重导 harness**。零几何改动、零阈值改动、**不 bump SPEC**、不改门判定、不伪造 sign-off。

## 1. 机判事实（工具 `tools/p3_v57_co54_spec_delivery_audit.py`；消费 `m13_v57_l4_construction.json` + `SPEC_k2_v4.spec-rev-3.json`）

| # | 项 | SPEC 口径 | 交付实测 | 判定 |
|---|---|---|---|---|
| F1 | 对内平行段中心距 | `p_gap = 0.175`（边距） | 中心 **0.500**（边距 0.295）为最小；另见 **0.600**（边距 0.395）等 | 不一致（**加宽** ⇒ 耦合↓ ⇒ Zdiff↑）；判者 = L5-SI.4 `netclass_geometry`（CO-53 新增） |
| F2 | 对间平行段中心距 | `inter_pair_spacing_mm = 0.875`（边距） | **0.550**（边距 0.345）@ **In6.Cu**，`PCIE_UP2_N‖PCIE_UP4_P`，平行重叠 **29.1mm**，x∈[54.4, 90.1]（芯片侧长平行带，非连接器扇出） | 不一致；**无门禁机判**（本件首个测量项） |
| F3 | 走廊 PITCH | `p_gap+2·p_width+inter_pair = 1.46` | `corridors[].bands[].tracks_y` 实际步距 = **1.20** | **SPEC 自身不自洽**（Δ0.26，见 §2） |
| F4 | 叠层 | `stackup.material = "JLC 6L … JLC06161H …"` | 板 **8L**（LID.1）且 `(setup)` **无 `(stackup)` 介质定义** | 缺失（输入缺口，见 §3） |
| F5 | 阻抗基准 | `model = JLC_SI9000_H1_5.0mil_Er1_4.3`（⇒ 85.1Ω @0.205/0.175） | 仓内模型层 6L 叠构等效 **H=0.1175 / Er=4.5 ⇒ 79.9Ω**；JLC 官方 prepreg εr（3313=4.1 / 2116=4.16 / 1080=3.91 / 7628=4.4）与该模型注释（4.05/4.25/3.91?/4.6）亦不同 | 三处"85Ω 基准"互不同 ⇒ 模型输入漂移 |
| F6 | 模型适用层 | 微带（H1）口径 = F.Cu | 34 对中 **32 对**的决定性平行段在 **In2/In6（带状线）**；仅 REFCLK 2 对在 F.Cu | 同 `p_width=0.205` 同时标称微带/带状线 85Ω（L2 v2.0「与 F.Cu 相同」），**未经分层重导** |
| F7 | 对内几何一致性 | `p_gap` 单字段 | 交付**非单一值**（机器实测 `delivered.grid`）：对内 **0.500**（In2 东走廊 x 84.75→93.65；In6 全带）与 **0.600**（In2 西走廊 x 53.2→65.2；B.Cu x 84.3→93.7）并存；J2 侧 In2 扇出列距 **0.58**（x 125.85→131.65） | 单字段无法表达（0.5/0.6/0.58 并存） |

**归因更正（对 CO-53 F2）**：CO-53 记 0.550 出现在「连接器扇出密集区」；机判证据显示最紧项为 **In6.Cu 长平行带**（29.1mm 重叠，x∈[54.4,90.1]），⇒ 归因更正为「内层长平行带」，非仅扇出局部。
（CO-53 的 F1 数值 0.500/0.295 与本件重算**一致**，谓词与 `p3_v57_l5_signoff.py::_pair_geometry` 相同。）

## 2. 走廊 PITCH 公式复核（CO-53 §3.3 落地）

- 公式：`PITCH = p_gap + 2·p_width + inter_pair_spacing`。以 SPEC 现值为前提：`0.175 + 2(0.205) + 0.875 = **1.46**`。
- 但 SPEC `corridors[].bands[].tracks_y` 冻结步距（EAST dn/up、WEST dn/up **四带全为 1.20**；refclk 2 对 4.80）⇒ **公式前提与冻结几何不一致（Δ0.26）⇒ SPEC 自身不自洽**。
- 交付实测网格（`|段长|≥3mm` 轴对齐；audit `delivered.grid`）：

| 区域 | 层/轴 | 对内中心 | 步距/对中心距 |
|---|---|---|---|
| 西走廊（MCIO） | In2 竖列 x 53.2→65.2 | **0.600** | 网格步 0.6（对中心 1.2） |
| 东走廊中段（芯片侧） | In2 竖列 x 84.75→93.65 | **0.500** | 同极性 1.2 |
| J2 侧扇出 | In2 竖列 x 125.85→131.65 / 136.0→142.38 | — | 列距 **0.58** |
| J2 侧带（In6） | In6 横排 y 56.33→78.57 | **0.500** | 对中心距 **≈1.45**（0.5+0.949 交替） |
| 芯片侧带（In6/B.Cu） | In6 横排 y 33.45→49.70；B.Cu 竖列 x 84.3→93.7 | **0.500**（B.Cu 0.6） | 网格 0.5/0.55 交替；**对间最紧 0.55**（=F2） |

- ⇒ 交付步距集合 = **{0.5, 0.55, 0.58, 0.6, 1.2, 1.45}**：与 SPEC 的 (`p_gap 0.175` / `inter_pair 0.875` / `tracks_y 1.2`) **无一自洽**；走廊口径下对间铜边净空 = 0.345（F2 最紧）…0.744，**皆 < 0.875**。
- 结论：`p_gap` / `inter_pair_spacing_mm` / 走廊步距 **三者互为函数**，只能**一次 ECO 一并裁定**（不可单项放宽）。

## 3. 8L 介质叠层输入缺口：**可达性实测**（CO-53 §3.1 的"取得输入"落地）

| 路径 | 实测 | 结果 |
|---|---|---|
| 仓库（全容器 grep `JLC08161`/`3313`/`2116`/`NP-155F`/`prepreg`） | 仅 `k2/…/L2/stackup_8layer_decision.md`（"JLC08161H（南亚 NP-155F, 3313/2116）"）与 `SPEC_k2_v4_c3poc.json:stackup.material` 同源记录 | **无逐层介质厚度** |
| 板 `k2_v4_8L.kicad_pcb` | `(setup)` 无 `(stackup)` 段 | 无介质表 |
| 公开源 `jlcpcb.com/impedance`（实抓 303KB SSR-HTML） | 官方**逐层**叠构：4L（17 个）+ 6L（16 个，含 JLC06161H-3313/-2116/-1080/-7628 变体）；官方 prepreg εr：**7628=4.4 / 3313=4.1 / 1080=3.91 / 2116=4.16** | **无 8L/JLC08161H** |
| `jlcpcb.com/pcb-stackup`、`/8-layer-pcb`、`/multilayer-pcb`、`/capabilities/pcb-stackup`、`/help/article/stackup` | HTTP 404 / 200 但无 `08161` 命中 | 无 8L 逐层表 |

**裁定（L2，非 L1）**：8L 逐层介质厚度**非检索可得**（制造输入，属板厂文档），必须由上游/板厂给出（或 owner 指定叠层表文件）。这是 CO-53/CO-54 的**唯一阻塞**；在此之前不得声称阻抗合规，也不得以"放宽判据"替代 ECO。附带待核项：仓库/SPEC 的 prepreg εr 与 JLC 官方值不一致（F5），随同一 ECO 校订。

## 4. Zdiff 重导 harness（`tools/p3_v57_si_zdiff_rederive.py`）

- **模型层复用（非本工具自创）**：`_shared/eda_core/stackup.py` 的 IPC-2141 边缘耦合微带/对称带状线。
- **模型保真度自检**：以 SPEC 自陈基准（H=0.127/Er=4.3, w=0.205, s=0.175）投入 ⇒ **85.05Ω vs 自陈 85.1Ω（Δ0.05）** ⇒ 与 SPEC 同源，可用作一阶重导（fail-fast 门：|Δ|>0.5Ω 即非零退出）。
- **敏感性（一阶，默认模式）**：交付 s=0.295 vs SPEC s=0.175 ⇒ ΔZ% 随 H：`+6.7%(0.10) / +8.7%(0.127) / +10.0%(0.15) / +11.4%(0.20) / +12.0%(≥0.25)`（对 Er 不敏感）。**方向**：交付对内加宽 ⇒ Zdiff 抬高。**此表不是合规结论**（`conformance` 后由 CO-56 记为 `DESIGN_CONFORMANT_FIRST_ORDER_PENDING_COUPON`）。
- **`--stackup <json>` 通路已实测**（合成探针，**非**真实 8L 叠层）：微带 (0.20, 0.17)→85.86Ω；带状线 h=0.25/Er=4.16 ⇒ 85Ω 需 **w≈0.07**（对照交付 0.205）⇒ 印证 **F6**「0.205 同时满足微带与带状线 85Ω」不成立，须分层重导。
- 输入到位后同一命令产出 **ECO rev-4 提议**（`applied: false`，含 `stackup.material / impedance{model,width_mm,gap_mm} / net_classes.PCIe85.diff_pair.p_gap` 及 p_gap 语义裁定提示）⇒ 届时再走"变更单 + 引擎 `F`/`FROZEN_SHA` + validator 冻结集 bump → 重跑 G4..G7"。

## 5. 判据覆盖矩阵（制度性结论：CO-53 为何能长期隐藏）

| SPEC 字段 | 机判者 | 状态 |
|---|---|---|
| `PCIe85.clearance 0.175` | `drc_semantic_core` + L4 DRC + W3 A-CN | JUDGED |
| `PCIe85.width / p_width 0.205` | L5-SI `all_pcie_tracks_0p205` | JUDGED |
| `PCIe85.intra_pair_skew_mm 0.15` | L5-SI `max_intra_pair_skew`（0.0031） | JUDGED |
| `PCIe85.diff_pair.p_gap 0.175`（**下界**） | `drc_semantic_core` clearance | JUDGED_LOWER_BOUND |
| `PCIe85.diff_pair.p_gap`（**目标/上界**） | L5-SI.5 `netclass_geometry`（CO-53 新增；**CO-56 已把语义定为 lower_bound + 交付几何真源**） | JUDGED_CLOSED_PENDING_COUPON |
| `PCIe85.inter_pair_spacing_mm 0.875` | **无** | **NOT_JUDGED**（本件首次测量） |
| `corridors.tracks_y` 与 PITCH 公式一致性 | **无** | **NOT_JUDGED**（本件首次测量） |
| `impedance.{target,model,width,gap}` | **无**（`coupon_required=true`，板厂券路径） | **NOT_JUDGED** |
| `stackup.*` | **无**（板无 `(stackup)`） | **NOT_JUDGED** |
| `vias.*`（drill/outer/annular/max_per_line/pad_edge_clearance） | L4 validator via budget（CO-52）+ FAB 极值 | JUDGED |
| `constraints.edge_copper_min 0.3` | L5 DFM `copper_edge` | JUDGED |
| `constraints.escape_transition_zone`（0.075/0.1025） | 引擎逃逸域 + L4 DRC | JUDGED |
| `board.outline_x/outline_y` | L4 板框自检（CO-03） | JUDGED |

⇒ 三个 **NOT_JUDGED 空洞**（对间距、走廊公式一致性、阻抗/叠层）现各有首个机判项（本件 §1/§2/§4）；**门禁未新增**（不预判、不放宽）。

## 6. 裁定（L2/SI 自裁，取代"等 owner"态）

1. ~~CO-53/CO-54 各事实项 全部 OPEN~~ → **CO-55/CO-56 收口**：F1/F4 由叠层反解 + SPEC rev-4 关闭；F3 由 rev-4 scope 注记记录（数值未改）；F2（对间串扰）**保留为残余**（领域求解器/券）；`conformance = DESIGN_CONFORMANT_FIRST_ORDER_PENDING_COUPON`。
2. **门判定不变**：G4/W3、G5/W4、G6/L4、G7/L5 的几何/DFM 结论**不受影响**（本件零改动 canonical；drawing `dfa1d7c4a811b0da`、板 `cdcb869e9827ec87` 未动）。
3. **无 owner 闸口**：本项 = L2/SI 记录 + **制造输入缺口**（非 L1 拓扑/接口/信号流向/球重映射）。
4. ~~ECO rev-4 前置 = 8L 介质叠层输入~~ → **已由 CO-55 反向下达叠层要求 + CO-56 落盘 SPEC rev-4 并复跑 G4..G7（全 PASS、板逐字节不变、重跑零漂移）**。

## 7. 未改物 / 红线 / 复现 / 指纹

- 零几何/阈值改动；四冻结源 **4/4 MATCH**（`0bd52ed4 / a8ef3ea8 / fb07d25a / 0a459839`）；`SPEC_k2_v4.spec-rev-3.json` `2d6dbd8b` 未动；`.l4.kicad_dru` `3148703240` 未动。
- 复现：
  ```bash
  cd /home/fila/jqdDev_2025/ic_hw/k2
  python3 tools/p3_v57_co54_spec_delivery_audit.py                          # → m13_v57_co54_spec_delivery_audit.json
  python3 tools/p3_v57_si_zdiff_rederive.py                                 # → m13_v57_co54_zdiff_sensitivity.json（敏感性包络）
  python3 tools/p3_v57_si_zdiff_rederive.py --stackup <8L叠层.json>          # → 分层 85Ω 重导 + ECO rev-4 提议（applied:false）
  ```
  两工具均**字节确定性**（重跑同 sha16）。
- 指纹：audit `m13_v57_co54_spec_delivery_audit.json` **69fcbcdd19025874**（rev-4 下复算；CO-56 前为 ba87413ae4d8c7b4）｜sensitivity `m13_v57_co54_zdiff_sensitivity.json` **137ad69ac39aee86**｜boundary 本件 → v1.25。
