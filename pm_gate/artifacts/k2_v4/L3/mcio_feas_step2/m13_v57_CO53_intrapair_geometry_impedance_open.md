# CO-53 — 【L2/SI 自裁】对内/对间几何 vs SPEC 阻抗几何**未调和**（开放项 + 输入缺口）

> 2026-09-12｜性质：**L2/SI 事实裁定 + 缺口报告 + 变更请求**（本轮零几何改动、零阈值改动、不谎报合规）
> 前置：CO-52 `eaaea6b5e4456ddc`｜触发：按 L2 逐类审计「等长窗口/阻抗几何」时，对 SPEC 与交付几何做机判比对。
> **本件不预判 G 门判定**；它记录一个必须由 ECO 收口的开放项。

## 1. 实测事实（机判；命令可复现）
| # | 事实 | 证据/口径 |
|---|---|---|
| F1 | 交付板 **34/34 对** 对内平行段最小中心距 = **0.500 mm** ⇒ 边距 = 0.500 − 0.205 = **0.295 mm** | 由 `m13_v57_l4_construction.json: segments` 独立重算（同层、平行叉积≈0、投影重叠才计入）；写入 `m13_v57_l5_si_pi_emc_record.json: SI.netclass_geometry.delivered` |
| F2 | 对间最小平行中心距 = **0.550 mm**（边距 0.345），出现在连接器扇出密集区 | 同上（跨对，同层平行） |
| F3 | SPEC（**红线原件与 rev-1/2/3 全部一致**）：`net_classes.PCIe85.diff_pair.p_gap = 0.175`、`p_width = 0.205`、`inter_pair_spacing_mm = 0.875`；`impedance{width 0.205, gap_mm 0.175, target_zdiff 85 ±10 %, coupon_required true, model = "JLC_SI9000_H1_5.0mil_Er1_4.3"}` | `SPEC_k2_v4*.json` 三版逐字段比对 |
| F4 | SPEC `stackup.material = "JLC 6L stackup (JLC06161H …)"`；交付板为 **8L**（LID.1，`k2_v4_8L.kicad_pcb`），且板 `(setup)` **无 `(stackup)` 介质定义**（无逐层介质厚度/材料） | 机读板文件 + `m13_v57_layer_intent_rev5.json` |
| F5 | 对内 0.500 的**出处 = L2 裁定**（非笔误）：CO-10 §7.2 将 `POL_OFF 0.19 → 0.25`（依据 via–track 净距 `vt = 0.4525`），并在 co16 路径落地 | `m13_v57_CO10_west_connector_escape_ruling.md` §7.2 |
| F6 | 8L 采纳（A′）的后果**已含「板厚/叠层/阻抗变更」** | `m13_v57_l4_upstream_UC01_stackup_8L_required_v2.md` §5 |

## 2. 裁定（L2/SI）
1. F1/F2 与 F3/F4 **不一致**（0.295 ≠ 0.175；8L ≠ 6L 模型；对间 0.345 < 0.875）。⇒ **阻抗符合性 NOT_DEMONSTRATED**：
   - 「已证合规」不成立（几何与模型都不同）；
   - 「已证违反」同样不成立（Zdiff 需按 **8L 介质叠层**用 SI9000 重导；且 SPEC 自陈 `coupon_required=true`，属板厂券验证路径）。
2. 处置按宪法第七/九章：**问题回模型 + 变更单**，禁止 partial pass，禁止用"放宽判据"表述（整改 #03 已明文撤销 owner 参数特权）。
3. 本项**列为交付前必须关闭的开放项（delivery blocker）**，由 `.omo/start-work/ledger.jsonl` 跟踪；是否需 reopen 门由 ECO 结论决定（本件不预判）。

## 3. 要求动作（ECO 链）
1. **输入缺口（先行）**：取得 **8L 介质叠层**（材料 + 逐层介质厚度）——仓库/板内均缺（F4）⇒ 属"模型/制造输入缺口"，非 owner 的 L1 裁定；
2. 以该输入按 **SI9000** 重导 8L 下 85Ω 的 (w, gap)，发 **SPEC ECO rev-4**：更新 `stackup`（6L→8L）、`impedance{model, gap_mm}`、`net_classes.PCIe85.diff_pair.p_gap`（或明确其语义为**下限**并把几何真源指向 LID.1/CO-10）；
3. 复核走廊 `PITCH = p_gap + 2·p_width + inter_pair_spacing`（现 1.46 由 0.175 派生）；交付 0.500 对内中心下相邻对边距变小，须与 SI 对间要求一并裁定；
4. L5 SI 记录已机判暴露该项（`SI.netclass_geometry.conformance`），ECO 落地后随之更新并关闭本条。

## 4. 未改物 / 红线
零几何改动（drawing `dfa1d7c4a811b0da`、板 `cdcb869e9827ec87`）；四冻结源未动（本件**不** bump SPEC，只记录）；不改任何阈值/判据；不伪造合规。
指纹：l5_signoff `5b34e0ddc4aab909`｜si `b16293f842ecf712`（L5-SI.4）｜G7 记录 `4a4def9277890735`。
