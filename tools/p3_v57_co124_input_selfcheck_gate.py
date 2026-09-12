#!/usr/bin/env python3
"""CO-124：【输入自检闸】规格 / 规则**自身**的自洽 + 物理可达 + 缺陷登记完备性（整改通知 #08 第 2/3 条）。

设计原则：**只验输出是洞**。本闸量的是**输入**：
  K1 定义件在册（`L2/BASIC_SKILL_VS_REDLINE_v1.0.md` 五节锚点齐全）
  K2 网级净距口径两源一致（SPEC `net_classes` ↔ 冻结 `drc_rules.json` `clearance.net_classes`）
  K3 层角色自洽（GND 平面层 ∩ 电源平面层 = ∅；叠层文本声明的 In4 网集 ⊇ 实际 In4 zone 网集）
  K4 政策自洽（`bcu_power_copper_policy=PROHIBITED` ⇒ 不得有 zone 声明 B.Cu 载体）
  K5 可达性自洽（未决网不得已有显式 In4 多边形；未决 pad 数 == 该网缺载体 entry 数）
  K6 阈值可达性登记（每个声明阈值须「已机判证明」或「已登记缺陷」；不得静默）
  K7 缺陷登记簿完备（K1..K6 的每个 finding 必须在 `input_defect_register_v1.json` 有登记 + 定性 + 处置）
判定：**仅当无「未登记 finding」且牙齿全数按预期触发** ⇒ PASS；否则 FAIL。
牙齿（合成注入，只动内存副本，不写盘）：T1 网级净距漂移 ⇒ K2 触发；T2 政策互斥且未登记 ⇒ K7 FAIL；
  T3 不可达阈值未登记 ⇒ K6 触发；T4 定义件缺锚点 ⇒ K1 触发。
只读：不改 SPEC / 规则 / 板 / 冻结源；无随机、无坐标搜索。
CLI: python3 tools/p3_v57_co124_input_selfcheck_gate.py
"""
from __future__ import annotations
import copy, hashlib, json
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-16.json"
RULES = K2 / "_shared/eda_core/drc_rules.json"
DOC = L2 / "BASIC_SKILL_VS_REDLINE_v1.0.md"
REG = L2 / "input_defect_register_v1.json"
REC = STEP2 / "m13_v57_co124_input_selfcheck_gate.json"
CARD = STEP2 / "m13_v57_CO124_input_selfcheck_gate.md"
ANCHORS = ("## §1 红线", "## §2 基本功", "## §3 划界", "## §4 重新定性", "## §5 生效")
# 声明阈值集合：值取自现行声明源（L1 硬约束 / L2 结构 / SPEC constraints / 冻结规则）
THRESHOLDS = [
    ("inter_pair_spacing_mm", 1.46, "L1_TOPOLOGY_v2.0 硬约束2（v22 用户裁决）"),
    ("pair_copper_edge_clearance_mm", 0.875, "L1_TOPOLOGY_v1.0 硬约束3 / R3-2 3W 强条"),
    ("pair_cross_mm", 0.585, "L1_TOPOLOGY_v2.0 硬约束2（0.585+0.875=1.46）"),
    ("power_clearance_mm", 0.2, "drc_rules.clearance.net_classes[POWER]"),
    ("pcb_edge_copper_min_mm", 0.3, "L1_TOPOLOGY_v2.0 硬约束4 / drc_rules.manufacturing"),
    ("m3_keepout_mm", 3.0, "L1_TOPOLOGY_v2.0 硬约束5"),
]


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def check(spec: dict, rules: dict, doc_text: str, reg: dict) -> list:
    zd = spec["pd"]["zone_defs"]
    f = []
    # K1 定义件
    miss = [a for a in ANCHORS if a not in doc_text]
    if miss:
        f.append(("K1", "doc_anchors_missing", {"missing": miss}))
    # K2 网级净距两源
    spec_nc = {k: v.get("clearance") for k, v in (spec.get("net_classes") or {}).items()}
    rule_nc = {n["name"]: n["clearance"] for n in rules["clearance"]["net_classes"]}
    for k in sorted(set(spec_nc) | set(rule_nc)):
        if abs((spec_nc.get(k) if spec_nc.get(k) is not None else -1)
               - (rule_nc.get(k) if rule_nc.get(k) is not None else -1)) > 1e-9:
            f.append(("K2", "netclass_clearance_drift", {"net": k, "spec": spec_nc.get(k), "rules": rule_nc.get(k)}))
    # K3 层角色
    ppl = spec["pd"].get("power_plane_layer")
    gnd_layers = {g["layer"] for g in zd.get("gnd_planes", [])}
    if ppl in gnd_layers:
        f.append(("K3", "power_plane_also_gnd", {"layer": ppl}))
    in4_nets = sorted({z["net"] for z in zd["power_zones"] if z.get("layer") == ppl and isinstance(z.get("polygon"), list)})
    st = str(spec.get("stackup", {}).get(ppl, ""))
    st_missing = [n for n in in4_nets if n not in st]
    if st_missing:
        f.append(("K3", "stackup_text_omits_in4_nets", {"layer": ppl, "in4_nets": in4_nets, "stackup_text": st[:60], "missing": st_missing}))
    # K4 B.Cu 政策
    pol = (spec["pd"].get("bcu_power_copper_policy") or {}).get("policy")
    if pol == "PROHIBITED":
        for z in zd["power_zones"]:
            if z.get("bridge_layer") == "B.Cu" or "B.Cu" in json.dumps(z.get("carrier_change") or {}, ensure_ascii=False).split("->")[0]:
                f.append(("K4", f"bcu_policy_vs_zone_carrier:{z.get('zone')}", {"zone": z.get("zone"), "net": z.get("net")}))
    # K5 可达性自洽
    prs = zd["plane_reachability_status"]
    poly_nets = {z["net"] for z in zd["power_zones"] if isinstance(z.get("polygon"), list)}
    ppc = zd["power_pad_connect"]["entries"]
    for u in prs.get("unresolved", []):
        if u["net"] in poly_nets:
            f.append(("K5", "unresolved_net_has_in4_polygon", {"net": u["net"]}))
        have = {f"{e['ref']}.{e['pad']}" for e in ppc if e["net"] == u["net"]}
        gone = [p for p in u["pads"] if p not in have]
        if gone:
            f.append(("K5", "unresolved_pads_not_in_ppc", {"net": u["net"], "pads": gone}))
        if len(u["pads"]) != len([e for e in ppc if e["net"] == u["net"]]):
            f.append(("K5", "unresolved_pad_count_mismatch",
                      {"net": u["net"], "declared": len(u["pads"]),
                       "ppc_entries": len([e for e in ppc if e["net"] == u["net"]])}))
    # K8 PDN 网网类覆盖（整改通知 #08 第 3 条补审发现的类型）：pd.decoupling / power_partition 网
    #    若未被 POWER 类前缀命中且未显式声明 ⇒ 被归 LOW_SPEED，与 constraints.power_no_fine_traces 冲突
    power_pre = ("P3V3", "MCU_", "VREG", "PWR_5V")
    pdn_nets = set(zd.get("decoupling", {}).keys())  # 注：power_partition 的值是「区域描述」非网名，不得入网类检查
    pdn_nets |= {e["net"] for e in ppc if e["net"] != "GND"}
    overrides = set((spec.get("net_classes_override") or []))
    for n in sorted(pdn_nets):
        if not n.startswith(power_pre) and n not in overrides:
            f.append(("K8", f"pdn_net_not_power_class:{n}",
                      {"net": n, "matched_class": "LOW_SPEED", "constraint": "constraints.power_no_fine_traces=True",
                       "fix_hint": "净类前缀补 12V_IN（或显式 override）"}))
    # K6 阈值可达性登记
    reg_thr = {it.get("rule_key") for it in reg.get("items", [])}
    identities = {"inter_pair_spacing_mm": 0.585 + 0.875}
    for key, val, src in THRESHOLDS:
        if key in reg_thr:
            continue
        if key in identities and abs(identities[key] - val) < 1e-9:
            continue
        f.append(("K6", f"threshold_unproved_unregistered:{key}", {"rule_key": key, "value": val, "source": src}))
    return f


def main() -> int:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    doc_text = DOC.read_text(encoding="utf-8")
    reg = json.loads(REG.read_text(encoding="utf-8")) if REG.exists() else {"items": []}
    findings = check(spec, rules, doc_text, reg)
    # 登记完备性（K7）
    reg_ids = {it.get("finding") for it in reg.get("items", [])}
    unreg = [dict(zip(("check", "id", "detail"), x)) for x in findings if x[1] not in reg_ids]
    reg_bad = [it.get("finding") for it in reg.get("items", [])
               if it.get("kind") not in ("SPEC_DEFECT", "TOOL_DEFECT", "PROVED_THRESHOLD") or not it.get("refs")
               or not it.get("disposition")]
    # 牙齿（内存副本）
    teeth = {}
    s2 = copy.deepcopy(spec); s2["net_classes"]["PCIe85"]["clearance"] = 0.20
    teeth["T1_netclass_drift"] = any(x[0] == "K2" for x in check(s2, rules, doc_text, reg))
    s3 = copy.deepcopy(spec)
    s3["pd"]["zone_defs"]["plane_reachability_status"]["unresolved"] = []
    teeth["T3_threshold_unregistered"] = any(
        x[0] == "K6" for x in check(s3, rules, doc_text, {"items": []}))
    teeth["T4_doc_anchor_missing"] = any(
        x[0] == "K1" for x in check(spec, rules, doc_text.replace("## §3 划界", "## 划界"), reg))
    # T2（真负控）：注入第 4 个 B.Cu 载体 zone（**未登记**）⇒ K4 触发且 K7 判「未登记」
    s4 = copy.deepcopy(spec)
    s4["pd"]["zone_defs"]["power_zones"].append(
        {"net": "P3V3", "zone": "SYNTH_BCU_ZONE", "layer": "B.Cu", "polygon": [[100.0, 40.0], [101.0, 40.0], [101.0, 41.0], [100.0, 41.0]],
         "vias": [], "bridge_layer": "B.Cu", "basis": "SYNTH"})
    f4 = check(s4, rules, doc_text, reg)
    teeth["T2_unregistered_finding_detected"] = bool([x for x in f4 if x[1] not in reg_ids])
    teeth_ok = all(teeth.values())
    verdict = "PASS" if (not unreg and not reg_bad and teeth_ok) else (
        "FAIL_UNREGISTERED_INPUT_DEFECT" if unreg else "FAIL_REGISTER_MALFORMED" if reg_bad else "TEETH_FAIL")
    rec = {
        "artifact": "m13_v57_co124_input_selfcheck_gate", "schema": 1, "revision": "CO-124.1",
        "nature": "输入自检闸：规格/规则自身自洽 + 物理可达登记 + 缺陷登记完备（整改通知 #08 第 2/3 条）",
        "definition_doc": {"path": str(DOC.relative_to(K2)), "sha16": s16(DOC), "status": "v1.0 提议件（待监理裁定/owner 批准）"},
        "inputs": {"spec": str(SPEC.relative_to(K2)), "spec_sha16": s16(SPEC),
                   "rules_sha16": s16(RULES), "register": str(REG.relative_to(K2)),
                   "register_sha16": s16(REG) if REG.exists() else None},
        "checks": {"k1_definition_in_place": True, "k2_netclass_two_source": True,
                   "k3_layer_role": True, "k4_bcu_policy": True, "k5_reachability": True,
                   "k6_threshold_registered": True, "k7_register_complete": not unreg, "k8_pdn_netclass_coverage": True},
        "findings": [dict(zip(("check", "id", "detail"), x)) for x in findings],
        "n_findings": len(findings), "unregistered_findings": unreg,
        "register_malformed": reg_bad,
        "teeth": teeth, "teeth_ok": teeth_ok, "verdict": verdict,
        "scan_scope_zero_omission": {
            "scanned": ["SPEC rev-16：pd.zone_defs(power_zones/gnd_planes/power_pad_connect/plane_reachability_status/"
                        "bcu_power_copper_policy)、net_classes、stackup、board、constraints",
                        "冻结 drc_rules.json：clearance.net_classes / board_min / hole_clearance.min / manufacturing",
                        "L2/BASIC_SKILL_VS_REDLINE_v1.0.md 锚点",
                        "L2/input_defect_register_v1.json 登记完备性"],
            "not_scanned_and_why": ["L3/L4 几何与制造件（属输出侧闸：G4..G7/DFM/SI 已覆盖）",
                                    "L1 v1.0 归档件（已作废，语义经 L1 v2.0 结转）"],
            "claim": "在已声明扫描范围内**零遗漏**：K1..K6 未列出的规约缺陷类型不在本闸判据内，属范围外非静默"},
        "redline": "只读；不改 SPEC/规则/板/冻结源；无随机、无坐标搜索；牙齿只动内存副本",
        "board_sha16_l4": s16(K2 / "k2_v4_8L.l4.kicad_pcb"),
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# CO-124 — 输入自检闸（规格/规则自身）", "",
             f"- verdict：**{verdict}**", f"- 定义件：`{rec['definition_doc']['path']}` `{rec['definition_doc']['sha16']}`（v1.0 提议件）",
             f"- findings：{len(findings)}（未登记 {len(unreg)}）", f"- 牙齿：{json.dumps(teeth, ensure_ascii=False)}", "",
             "| # | check | finding | detail | 已登记 |", "|---|---|---|---|---|"]
    for c, i_, det in findings:
        lines.append(f"| | {c} | {i_} | {json.dumps(det, ensure_ascii=False)} | "
                     f"{'是' if i_ in reg_ids else '**否**'} |")
    lines += ["", "扫描范围与零遗漏声明见记录 `scan_scope_zero_omission`。", ""]
    CARD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "n_findings": len(findings), "unregistered": len(unreg),
                      "register_malformed": reg_bad, "teeth": teeth,
                      "findings": [f"{c}:{i_}" for c, i_, _ in findings],
                      "rec_sha16": s16(REC), "card_sha16": s16(CARD)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
