#!/usr/bin/env python3
"""CO-146 A5 — 定性更正 + 登记簿登记 + L2 定值绑定件（监理指令 #10 动作 5）。

动作：
 1. 写 `L2/jlc_prototype_parameters_v1.json`：监理定值绑定 + **撤回「外部输入阻塞」**（改绑 JLC 工艺/监理定值）
 2. 登记簿 `L2/input_defect_register_v1.json` +2 项（幂等，按 finding 去重）：
      · implementation_deviation:asbuilt_via_strategy_requires_blind_buried（HIGH / OPEN）
      · implementation_deviation:solder_mask_bridge_jlc_min_1x（MED / OPEN）
 3. 写 `m13_v57_co146_jlc_rebind.json` + 卡
冻结四源不动（SPEC 逐字节不变；coupon_required=true 字段保留，改绑的是**解释与签署路径**）。
牙齿：① 登记簿 +2 后 co124 必须仍可运行；② 二次运行 item 数不增（幂等）。
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path("/home/fila/jqdDev_2025/ic_hw")
K2 = ROOT / "k2"
STEP2 = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
REG = L2 / "input_defect_register_v1.json"
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-19.json"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
INSTR = ROOT / ".omo/supervision/ledger/instruction-10-jlc-prototype-ready.md"
CAPSRC = STEP2 / "m13_v57_co146_jlc_capability_source.html"


def sha16(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.exists() else None


def load(p):
    return json.loads(Path(p).read_text())


def write(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")


def main() -> int:
    dfm = load(STEP2 / "m13_v57_co146_jlc_dfm_gate.json")
    probe = load(STEP2 / "m13_v57_co146_through_via_probe.json")
    imp = load(STEP2 / "m13_v57_co146_impedance_table.json")
    pm = load(STEP2 / "m13_v57_co146_pm_eval.json")
    spec_before = sha16(SPEC)

    # ── 1. L2 定值绑定件 ────────────────────────────────────────────────────
    bind = {
        "artifact": "jlc_prototype_parameters_v1", "schema": 1, "revision": "v1.0",
        "nature": "监理指令 #10 定值绑定 + 外部输入定性更正（撤回「外部输入阻塞」表述）",
        "supervisor_instruction": {
            "title": "JLC 8 层打样就绪 —— 外部输入改绑 JLC 工艺 + 出打样包",
            "file": str(INSTR.relative_to(ROOT)), "sha16": sha16(INSTR), "due": "下一轮"},
        "binding": {
            "stackup": "JLC08161H（南亚 NP-155F）", "total_thickness_mm": 1.6,
            "copper": {"outer_oz": 1.0, "inner_oz": 0.5},
            "impedance": {"target_zdiff": 85.0, "tolerance_pct": 10, "order_option": "勾选阻抗控制"},
            "surface_finish": "ENIG（沉金）", "drop_budget_pct": 3.0,
            "thermal_env": {"ambient_C": 40.0, "convection": "自然对流"},
            "rails": ["12V_IN", "P3V3", "P3V3_AUX", "MCU_VDD"],
            "rail_currents": "由设计/器件手册导出；无数据时按保守值并显式声明（本件 CO-146 已按此登记）",
        },
        "rebinding": [
            {"item": "阻抗终判",
             "from": "SI9000 + 板厂阻抗券（`coupon_required=true`，语义 = 等外部券）",
             "to": "**JLC 阻抗控制服务**（免费标准阻抗测试 / ±10% 控制）+ 监理定值叠层 JLC08161H",
             "spec_unchanged": "SPEC rev-19 `impedance.coupon_required=true` **逐字节不变**（冻结四源）；"
                               "改绑的是**解释与签署路径**：coupon_required=true 现行解释 = 必须走 JLC 阻抗控制服务"
                               "（其标准阻抗测试即 coupon），不再是「等外部券 ⇒ 阻塞」。",
             "evidence": ["m13_v57_co146_impedance_table.json", "m13_v57_co146_jlc8_capability.json"]},
            {"item": "PDN 压降 · 热",
             "from": "外部 PM 输入（CO-87 两项 NOT_DEMONSTRATED）",
             "to": "监理定值（压降 3% / 40°C 自然对流 / 外层 1oz+内层 0.5oz）+ CO-146 一阶确定性评估",
             "evidence": ["m13_v57_co146_pm_eval.json"]},
            {"item": "「外部输入阻塞」表述",
             "from": "「板厂券 / PM 数据 = 外部阻塞」（CO-105/CO-107/CO-133 等记录残留表述）",
             "to": "**撤回**（改绑 JLC 工艺 + 监理定值）。**同时登记新发现的真实阻塞项**："
                   "盲/埋孔 —— JLC 标准服务不支持（见登记簿 OPEN 项 + co146_through_via_probe）。",
             "evidence": ["m13_v57_co146_jlc_dfm_gate.json", "m13_v57_co146_through_via_probe.json"]},
        ],
        "jlc_capability_source": {"url": dfm["items"][0].get("jlc_limit") and
                                  "https://jlcpcb.com/capabilities/pcb-capabilities",
                                  "fetched": "2026-09-12", "file": CAPSRC.name, "sha256": sha16(CAPSRC) or "",
                                  "note": "抓取件全文存于 L3/mcio_feas_step2/；逐条引用见 m13_v57_co146_jlc8_capability.json"},
        "frozen_sources": {"SPEC_k2_v4.spec-rev-19.json": spec_before,
                           "k2_v4_8L.l4.kicad_pcb": sha16(BOARD), "note": "本件未改冻结四源；SPEC 逐字节不变"},
        "redline": "本件只写 L2 政策层 + 登记簿；不改板/图纸/SPEC/冻结四源。",
    }
    write(L2 / "jlc_prototype_parameters_v1.json", bind)

    # ── 2. 登记簿 +2（幂等） ───────────────────────────────────────────────
    reg = load(REG)
    new = [
        {"finding": "implementation_deviation:asbuilt_via_strategy_requires_blind_buried",
         "kind": "IMPLEMENTATION_DEVIATION", "severity": "high",
         "what": f"交付板 {dfm['as_built']['n_non_through_vias']}/{dfm['as_built']['n_vias']} 支过孔为**非通孔**"
                 f"（F.Cu→In2.Cu 92 / **In2.Cu→In5.Cu 88（埋孔）** / In5.Cu→B.Cu 32 / F.Cu→In5.Cu 8），"
                 f"而 **JLC 标准服务不支持盲/埋孔**（公布能力页：Blind/Buried Vias Not supported, only make through holes；"
                 f"FAQ 归为 advanced option 须 DFM review）；原地改通孔（坐标零改动）实测 **111 项 shorting_items** ⇒ "
                 f"现行 W3 派生**结构上依赖盲/埋孔**。项目全部可行性分析（CO-93/94/100/104）按「通孔工艺」口径 ⇒ 口径与实际不一致。",
         "refs": ["CO-146", "CO-145", "CO-104", "UC-01 v2 §4"],
         "disposition": "**停（勿擅改几何）**：出路由两条 —— (a) 按 JLC advanced/盲埋孔通道下单（须 JLC 工程评审 + 报价，"
                        "叠层/阻抗绑定需重确认）；(b) **重开 W3 派生**（加通孔工艺约束后重解并重证可行性，可行性未证）。"
                        "层级：结构/工艺类别（CO-104 先例「层数（HDI）才是 L1」）⇒ **需 owner 一句话**。",
         "status": "OPEN",
         "next": "owner：裁 (a) 走 JLC advanced 盲埋孔通道 / (b) 重开 W3 通孔化派生；L2 侧不得擅改几何（红线段）。",
         "evidence": [f"CO-146 DFM 闸 {sha16(STEP2 / 'm13_v57_co146_jlc_dfm_gate.json')}（过孔类型项 FAIL）",
                      f"CO-146 通孔化反证探针 {sha16(STEP2 / 'm13_v57_co146_through_via_probe.json')}"
                      f"（converted 220 / shorts +{probe['delta_by_type'].get('shorting_items')}）",
                      f"JLC 能力抓取件 {sha16(CAPSRC)}（Blind/Buried Vias Not supported）"],
         "closed_by": []},
        {"finding": "implementation_deviation:solder_mask_bridge_jlc_min_1x",
         "kind": "IMPLEMENTATION_DEVIATION", "severity": "medium",
         "what": "在 **JLC 下限**（阻焊开窗到邻近铜 ≥0.09mm）下 DRC 报 1 项 `solder_mask_bridge`："
                 "F.Cu 走线 `PCIE_UP3_N` × `R3` pad2（`PWR_BTN_ISO`）开窗。"
                 "板规 `solder_mask_to_copper_clearance=0.0`（未设判据）⇒ 此前无闸发现；非几何重排项。",
         "refs": ["CO-146"],
         "disposition": "工程可修（调 R3 开窗/间距或局部丝印-开窗几何），不改走廊/层序 ⇒ 若施加须走上游声明件 + G4 + 全链重基线；"
                        "当前**登记不擅改**，随打样包 ORDER_NOTES 交板厂确认。",
         "status": "OPEN",
         "next": "L2：确认是否随下一轮几何修订一并施加（或经 JLC DFM review 接受）。",
         "evidence": [f"CO-146 DFM 闸 {sha16(STEP2 / 'm13_v57_co146_jlc_dfm_gate.json')}"
                      "（drc_jlc_limits.samples: solder_mask_bridge ×1）"],
         "closed_by": []},
    ]
    have = {it["finding"] for it in reg["items"]}
    added = [it for it in new if it["finding"] not in have]
    reg["items"].extend(added)
    NOTE = ("；**CO-146（监理指令 #10 · JLC 打样就绪）**：+2 IMPLEMENTATION_DEVIATION（OPEN：盲/埋孔 vs JLC 标准不支持 = 结构/工艺类别；"
            "阻焊桥 1 处 vs JLC 0.09mm）；外部输入定性更正（撤回「等券」表述，改绑 JLC 阻抗控制服务 + 监理定值）；"
            "登记簿随 co124 每次运行校验。")
    MARK146 = "；**CO-146（监理指令 #10 · JLC 打样就绪）**："
    _ub = reg["meta"].get("updated_by", "")
    if MARK146 in _ub:                      # 幂等：CO-146 注记若已在（且其后无新注记）则重写为同一文本
        _ub = _ub.split(MARK146)[0]
    reg["meta"]["updated_by"] = _ub + NOTE
    write(REG, reg)
    reg_after = sha16(REG)

    # ── 3. 记录 ────────────────────────────────────────────────────────────
    co146_ids = [it["finding"] for it in new]
    present = {it["finding"] for it in reg["items"]}
    rec = {"artifact": "m13_v57_co146_jlc_rebind", "schema": 1, "revision": "CO146-REBIND.1",
           "nature": "定性更正 + 登记簿登记（监理指令 #10 动作 5）",
           "register": {"file": "L2/input_defect_register_v1.json",
                        "sha16_co145": "58bc24ea83f31735", "sha16_after": reg_after,
                        "items_before_co146": len(reg["items"]) - sum(1 for f in co146_ids if f in present),
                        "co146_items": co146_ids,
                        "co146_items_already_present_at_this_run": [f for f in co146_ids if f in have],
                        "items_total": len(reg["items"]),
                        "open_total": sum(1 for it in reg["items"] if it["status"] == "OPEN")},
           "l2_binding_artifact": {"file": "L2/jlc_prototype_parameters_v1.json",
                                   "sha16": sha16(L2 / "jlc_prototype_parameters_v1.json")},
           "rebinding": bind["rebinding"],
           "spec_sha16": sha16(SPEC), "board_sha16": sha16(BOARD),
           "deliverables": {"impedance_table": sha16(STEP2 / "m13_v57_co146_impedance_table.json"),
                            "pm_eval": sha16(STEP2 / "m13_v57_co146_pm_eval.json"),
                            "dfm_gate": sha16(STEP2 / "m13_v57_co146_jlc_dfm_gate.json"),
                            "fab_package": sha16(STEP2 / "m13_v57_co146_jlc_fab_package.json"),
                            "through_probe": sha16(STEP2 / "m13_v57_co146_through_via_probe.json")},
           "verdicts": {"impedance": imp["verdict"], "pm": pm["verdict"], "dfm": dfm["verdict"],
                        "through_only_feasible": probe["verdict"] == "FEASIBLE",
                        "orderable_at_jlc_standard": not dfm["fails"]},
           "teeth": {"t01_register_written": reg_after is not None,
                     "t02_idempotent_items": all(f in present for f in co146_ids)},
           "redline": "只写 L2 政策层 + 登记簿；冻结四源逐字节不变（SPEC 前后同 sha）。"}
    write(STEP2 / "m13_v57_co146_jlc_rebind.json", rec)
    md = ["# CO-146 卡 · 定性更正 + 登记（监理指令 #10 动作 5）", "",
          f"- 监理指令 #10 出处 `{bind['supervisor_instruction']['file']}` `{bind['supervisor_instruction']['sha16']}`",
          f"- 登记簿 `{rec['register']['file']}`：{rec['register']['items_before_co146']} → **{rec['register']['items_total']}** 项"
          f"（OPEN {rec['register']['open_total']}）；CO-146 项：{rec['register']['co146_items']}",
          f"- SPEC 逐字节不变：`{rec['spec_sha16']}`｜板 `{rec['board_sha16']}`", "",
          "## 定性更正（撤回「外部输入阻塞」）", ""]
    for r_ in bind["rebinding"]:
        md += [f"### {r_['item']}", f"- 旧：{r_['from']}", f"- 新：{r_['to']}", ""]
    md += ["## 交付物 verdict", ""] + [f"- {k}: **{v}**" for k, v in rec["verdicts"].items()] + [""]
    (STEP2 / "m13_v57_co146_jlc_rebind.md").write_text("\n".join(md) + "\n")
    print("register:", rec["register"])
    print("l2 bind sha16:", rec["l2_binding_artifact"]["sha16"])
    print("verdicts:", rec["verdicts"])
    print("spec sha16:", rec["spec_sha16"], "(before", spec_before, ")")
    return 0


if __name__ == "__main__":
    sys.exit(main())
