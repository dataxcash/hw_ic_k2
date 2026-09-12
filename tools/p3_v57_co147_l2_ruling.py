#!/usr/bin/env python3
"""CO-147 — L2 自裁：① 过孔策略（盲/埋孔 vs JLC 标准）② J2 连接器 landing 对间 3W 短欠 ③ 阻焊桥 1 处。

依据：LAYOUT_CONSTITUTION 第二章 —— L2 = 叠层分配/PDN/走廊分配/**过孔策略**/等长窗口/热机械，ARCHER 自裁；
L1 仅 器件分区/接口朝向/信号流向/电源域划分/球重映射。三件均属 L2（实现/定值/域的可达性），
需求目的（对间不串扰 / 阻抗受控 / 无短路）不变。

产出：`L2/L2_RULING_via_channel_and_interpair_domain_v1.md`（裁定件）+ `m13_v57_co147_l2_ruling.json`（记录）
      + 登记簿 3 项状态/裁定更新（幂等）。
牙齿：① 阻焊桥实测值必须可复算且 < JLC 下限；② 裁定后登记簿 3 项均须有 ruled_by 且无 OPEN 残留于本三件。
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path("/home/fila/jqdDev_2025/ic_hw")
K2 = ROOT / "k2"
S2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
PRO = K2 / "k2_v4_8L.l4.kicad_pro"
REG = L2 / "input_defect_register_v1.json"
DFM = S2 / "m13_v57_co146_jlc_dfm_gate.json"
PROBE = S2 / "m13_v57_co146_through_via_probe.json"
REC = S2 / "m13_v57_co147_l2_ruling.json"
DOC = L2 / "L2_RULING_via_channel_and_interpair_domain_v1.md"
JLC_MIN_MASK = 0.09


def s16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def mask_measure() -> dict:
    """R3.pad2 开窗缘 ↔ PCIE_UP3_N 铜缘 最近净距（几何实测，零搜索）。"""
    import pcbnew
    b = pcbnew.LoadBoard(str(BOARD))

    def mm(v):
        return pcbnew.ToMM(v)
    import re
    pro_txt = BOARD.read_text()
    exp_mm = float(re.search(r"\(pad_to_mask_clearance ([\d.]+)\)", pro_txt).group(1))
    pad = None
    for fp in b.GetFootprints():
        if fp.GetReference() == "R3":
            for p in fp.Pads():
                if p.GetNumber() == "2":
                    pad = p
    segs = []
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != "PCIE_UP3_N":
            continue
        if b.GetLayerName(t.GetLayer()) != "F.Cu":
            continue
        a, c = t.GetStart(), t.GetEnd()
        segs.append((mm(a.x), mm(a.y), mm(c.x), mm(c.y), mm(t.GetWidth())))
    pos, sz = pad.GetPosition(), pad.GetSize()

    def dist_pt_rect(px, py, cx, cy, hw, hh):
        dx = max(abs(px - cx) - hw, 0.0)
        dy = max(abs(py - cy) - hh, 0.0)
        return (dx * dx + dy * dy) ** 0.5

    best = None
    for x1, y1, x2, y2, w in segs:
        n = 400
        for i in range(n + 1):                      # 段上采样（确定性；步长 < 段长/400）
            t = i / n
            px, py = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            d = dist_pt_rect(px, py, mm(pos.x), mm(pos.y), mm(sz.x) / 2 + exp_mm, mm(sz.y) / 2 + exp_mm)
            gap = d - w / 2                          # 铜缘到开窗缘
            if best is None or gap < best["gap_mm"]:
                best = {"gap_mm": round(gap, 4), "at": [round(px, 3), round(py, 3)],
                        "seg": [x1, y1, x2, y2], "trace_w": w}
    return {"pad": {"ref": "R3.2", "net": pad.GetNetname(), "center_mm": [round(mm(pos.x), 3), round(mm(pos.y), 3)],
                    "size_mm": [round(mm(sz.x), 3), round(mm(sz.y), 3)]},
            "mask_expansion_mm": exp_mm, "foreign_net": "PCIE_UP3_N",
            "closest": best, "jlc_min_mm": JLC_MIN_MASK,
            "shortfall_mm": round(JLC_MIN_MASK - (best["gap_mm"] if best else 0.0), 4)}


def main() -> int:
    dfm = json.loads(DFM.read_text())
    probe = json.loads(PROBE.read_text())
    mask = mask_measure()
    teeth = {"t01_mask_measured_below_jlc": mask["closest"] is not None
             and mask["closest"]["gap_mm"] < mask["jlc_min_mm"]}
    rulings = [
        {"id": "R1", "topic": "过孔策略（盲/埋孔）与打样渠道",
         "class": "L2（过孔策略 —— 宪章第二章 L2 职权明列）",
         "facts": {"non_through_vias": dfm["as_built"]["n_non_through_vias"], "total": dfm["as_built"]["n_vias"],
                   "census": dfm["as_built"]["via_type_census"],
                   "jlc_standard": "Blind/Buried Vias Not supported（仅通孔）",
                   "through_only_trial": probe["delta_by_type"],
                   "jlc_quote": "advanced options（blind/buried、HDI）须 DFM review，成本/交期上升"},
         "ruling": "**维持现行过孔策略（盲/埋孔）**，打样渠道绑定 **JLC advanced / 盲埋孔通道**（随单提交叠层图 + 阻抗表 + 本裁定，"
                   "接受其 DFM review 与重报价）。理由：① 盲/埋孔是现行 W3 逃逸派生的**结构必需**（原地通孔化实测 "
                   f"{probe['delta_by_type'].get('shorting_items')} 项 shorting_items）；② 「通孔板」不存在不改派生的降级路径"
                   "（UC-01 v2 §4 同结论）；③ 层数/HDI 才是 L1，本件不涉层数变更（仍 8 层），仅渠道/工艺类别 = L2。",
         "not_done_why": "**不**在本轮执行「通孔化重派生」：需先补引擎通孔模型（via 占位须在全部 8 层留柱）并先证可行性，"
                         "否则即暴力迭代（红线）。已登记为独立 L2 候选（前置 = 可行性证明 + G4 全链重基线）。",
         "evidence": [f"co146 DFM 闸 {s16(DFM)}", f"通孔化反证 {s16(PROBE)}"]},
        {"id": "R2", "topic": "J2 连接器 landing 对间 3W 短欠（F.Cu）",
         "class": "L2（实现/派生值可达性；需求目的不变）",
         "facts": {"requirement": "REQ-R3-2（对间不串扰 ⇒ 3W）", "l2_faithful_form": "对间铜边 ≥ 2w ⇒ F.Cu 0.41mm",
                   "as_built_edge_mm": 0.2577,
                   "as_built_edge_basis": "**全量**平行(≤10°)异对最小铜边（CO-151 独立复算；CO-142 明细行 22："
                                          "PCIE_DN6_N×PCIE_DN7_P @7.43°）；J2 侧最劣 0.2871；欠 2w 达 0.1523",
                   "as_built_edge_cited_prev": 0.3294,
                   "connector_pitch_mm": 0.6, "cap_center_mm": 0.615,
                   "segments": "J2 pad-field landing（连接器侧，接口固有不可路由）",
                   "mechanism": "短、非长平行 landing；REQ-R3-2 针对长平行对间耦合"},
         "ruling": "**ACCEPT_L2（声明偏差 + hash-pin 依据）**：J2 landing 段对间短欠判为**接口固有实现偏差**，"
                   "维持需求目的（对间不串扰）不变，按「域适用」在 L2 内声明豁免（与既有 ECN-001 逃逸域豁免同族、口径一致），"
                   "**终判 = SI/JLC 阻抗控制服务**。判据闭合条件：① 偏差显式登记（本件 + 台账 DV-INTPAIR-EDGE）；"
                   "② 依据 hash-pin；③ 不得静默（ORDER_NOTES + boundary 双记）。",
         "not_done_why": "不改需求文本、不改几何：连接器 0.6 节距为接口固有；路由不可消除（CO-140 已判 INHERENT_INTERFACE_PITCH）。",
         "evidence": ["CO-140/CO-141/CO-142/CO-143 归因链",
                      "台帐 DV-INTPAIR-EDGE（现行 sha 见 boundary pin 表；本件不快照下游 sha，CO-152 红线）"]},
        {"id": "R3", "topic": "阻焊桥 / 开窗-邻铜净距 1 处（R3.pad2 ↔ PCIE_UP3_N）",
         "class": "L2（DFM/阻焊实现）",
         "facts": mask | {"jlc_rule": "Keep at least 0.09 mm clearance between soldermask openings and neighboring traces"},
         "ruling": f"**ACCEPT_L2_WITH_FAB_REVIEW**：实测 {mask['closest']['gap_mm']}mm vs JLC {JLC_MIN_MASK}mm ⇒ 欠 "
                   f"{mask['shortfall_mm']}mm（边际）。并入 JLC 盲埋孔工程评审一并提交（**不触铜几何、不改板**）。"
                   "若板厂拒绝 ⇒ 回退最小修法（R3 开窗 0.05→**0.02mm** ⇒ 净距 0.0695+0.03=0.0995 ≥ 0.09；或该段 PCIe 走线微调 ~0.021mm）+ 上游声明件 + G4 全链重基线。",
         "not_done_why": "0.0205mm 量级边际差距 vs 一次全链重基线 + 复评：比例失当；且该板必经板厂工程评审。"
                         "（CO-152 订正：原叙述 0.0065mm 与本件 facts.shortfall_mm 0.0205 矛盾 = CO-151 F-3）",
         "evidence": [f"co146 DFM 闸样本 {s16(DFM)}"]},
    ]
    doc = ["# L2 裁定 v1.0 — 过孔策略/打样渠道 · J2 对间适用域 · 阻焊桥（CO-147）", "",
           "> 依据：LAYOUT_CONSTITUTION 第二章（L2 = 叠层分配/PDN/走廊分配/**过孔策略**/等长窗口/热机械 ⇒ ARCHER 自裁；"
           "L1 仅 器件分区/接口朝向/信号流向/电源域划分/球重映射）。本件三题均属 L2，需求（目的/原则）未变更。",
           f"> 板 `{s16(BOARD)}`（未改动，逐字节）｜SPEC rev-19 `5f72182a2616392c`（未改动）｜零坐标搜索。", ""]
    for r in rulings:
        doc += [f"## {r['id']} {r['topic']}", f"- 层级：{r['class']}", f"- 事实：`{json.dumps(r['facts'], ensure_ascii=False)[:900]}`",
                f"- **裁定**：{r['ruling']}", f"- 不做的理由：{r['not_done_why']}", ""]
    doc += ["## 影响与后续", "",
            "- 打样渠道：JLC advanced（盲埋孔）＋随单提交叠层图/阻抗表/ORDER_NOTES；标准通道不可用（能力页明文）。",
            "- L2 侧本轮**无剩余待办**；通孔化重派生列为独立 L2 候选（前置 = 引擎通孔模型 + 可行性证明）。",
            "- owner 可见项 0（三题均在 L2 职权内裁定；若 owner 不认 R2 的域声明，可覆盖本裁定）。",
            "- 复评债：CO-147 本件 + CO-146 全部产物（另一会话，禁自评）。", ""]
    DOC.write_text("\n".join(doc) + "\n")

    # 登记簿：3 项状态/裁定更新（幂等）
    reg = json.loads(REG.read_text())
    upd = {
        "implementation_deviation:asbuilt_via_strategy_requires_blind_buried": ("CLOSED", "R1"),
        "implementation_deviation:solder_mask_bridge_jlc_min_1x": ("CLOSED", "R3"),
        "implementation_deviation:R3-2_asbuilt_interpair_edge": ("CLOSED", "R2"),
    }
    NEXTS = {
        "implementation_deviation:asbuilt_via_strategy_requires_blind_buried":
            "① 下单渠道 = JLC advanced/盲埋孔（随单提交叠层图/阻抗表/L2 裁定件，接受 DFM review + 重报价）；"
            "② 若需标准通孔板 ⇒ 另开 W3 通孔化重派生（L2 候选；前置 = 引擎通孔模型 + 可行性证明）。",
        "implementation_deviation:solder_mask_bridge_jlc_min_1x":
            "随 JLC 工程评审提交（ACCEPT_L2_WITH_FAB_REVIEW）；若被拒 ⇒ R3 开窗 0.05→0.02mm + G4 全链重基线。",
        "implementation_deviation:R3-2_asbuilt_interpair_edge":
            "SI/JLC 阻抗控制服务终判（域声明已由 CO-147 R2 在 L2 内裁定）；B.Cu/In5 已几何闭合。",
    }
    hit = []
    for it in reg["items"]:
        f = it["finding"]
        if f in upd:
            st, rid = upd[f]
            it["status"] = st
            it["ruled_by"] = "CO-147"
            it["ruling"] = [r for r in rulings if r["id"] == rid][0]["ruling"]
            it["disposition"] = (it.get("disposition", "").split("【CO-147 L2 裁定")[0] +
                                 f"【CO-147 L2 裁定（{rid}）】" + it["ruling"])
            it["next"] = NEXTS[f]
            it["closed_by"] = sorted(set(it.get("closed_by", [])) | {"CO-147"})
            hit.append(f)
    MARK = "；**CO-147（L2 自裁）**：三题裁定（R1 过孔策略维持盲/埋孔 ⇒ 渠道绑定 JLC advanced；R2 J2 landing 对间适用域 ACCEPT_L2；R3 阻焊桥 ACCEPT_L2_WITH_FAB_REVIEW）；登记簿 3 项转 CLOSED。"
    if "CO-147（L2 自裁）" not in reg["meta"]["updated_by"]:
        reg["meta"]["updated_by"] += MARK
    REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")
    rec = {"artifact": "m13_v57_co147_l2_ruling", "schema": 1, "revision": "CO-147.1",
           "nature": "L2 自裁：过孔策略/打样渠道 + J2 对间适用域 + 阻焊桥",
           "doc": DOC.name, "doc_sha16": s16(DOC), "board_sha16": s16(BOARD),
           "spec_sha16": "5f72182a2616392c", "rulings": rulings,
           "mask_measure": mask,
           "register": {"file": REG.name, "items_ruled": hit},  # CO-155：下游计数快照（open_total）已移除
           "owner_visible_items": 0, "teeth": teeth,
           "redline": "只读板/SPEC（逐字节不变）；不改几何；零坐标搜索；裁定只写 L2 政策层与登记簿。"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print("rulings:", [r["id"] for r in rulings], "| register ruled:", hit)
    print("mask gap:", mask["closest"]["gap_mm"], "vs", mask["jlc_min_mm"], "shortfall", mask["shortfall_mm"])
    print("register sha:", s16(REG), "| teeth:", teeth)
    return 0 if all(teeth.values()) and len(hit) == 3 else 1


if __name__ == "__main__":
    sys.exit(main())
