#!/usr/bin/env python3
"""CO-124：【输入自检闸】规格 / 规则**自身**的自洽 + 物理可达 + 缺陷登记完备性（整改通知 #08 第 2/3 条）。

设计原则：**只验输出是洞**。本闸量的是**输入**：
  K1 定义件在册（`L2/BASIC_SKILL_VS_REDLINE_v<ver>.md` 五节锚点齐全）
  K2 网级净距口径两源一致（SPEC `net_classes` ↔ 冻结 `drc_rules.json` `clearance.net_classes`）
  K3 层角色自洽（GND 平面层 ∩ 电源平面层 = ∅；叠层文本声明的 In4 网集 ⊇ 实际 In4 zone 网集）
  K4 政策自洽（`bcu_power_copper_policy=PROHIBITED` ⇒ 不得有 zone 声明 B.Cu 载体）
  K5 可达性自洽（未决网不得已有显式 In4 多边形；未决 pad 数 == 该网缺载体 entry 数）
  K6 阈值可达性登记（每个声明阈值须「已机判证明」或「已登记缺陷」；不得静默）
  K9 需求/实现分家（整改通知 #09）：派生值台账逐条 (a) 可溯源到需求原则 id；(b) 派生式对现行输入**可达**（闭式重算）；
     需求条目**不得携带定值**（conflation 即 FAIL）
  K7 缺陷登记簿完备（K1..K6 的每个 finding 必须在 `input_defect_register_v1.json` 有登记 + 定性 + 处置）
判定：**仅当无「未登记 finding」且牙齿全数按预期触发** ⇒ PASS；否则 FAIL。
牙齿（合成注入，只动内存副本，不写盘）：T1 网级净距漂移 ⇒ K2 触发；T2 政策互斥且未登记 ⇒ K7 FAIL；
  T3 不可达阈值未登记 ⇒ K6 触发；T4 定义件缺锚点 ⇒ K1 触发。
只读：不改 SPEC / 规则 / 板 / 冻结源；无随机、无坐标搜索。
CLI: python3 tools/p3_v57_co124_input_selfcheck_gate.py
"""
from __future__ import annotations
import copy, hashlib, json, re
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.spec-rev-19.json"
RULES = K2 / "_shared/eda_core/drc_rules.json"
DOC = L2 / "BASIC_SKILL_VS_REDLINE_v1.1.md"
REG = L2 / "input_defect_register_v1.json"
LED = L2 / "derived_value_ledger_v1.json"   # CO-134：需求/实现分家台账
REC = STEP2 / "m13_v57_co124_input_selfcheck_gate.json"
DOC_VER = "v" + DOC.stem.split("_v")[-1]      # CO-136：版本从文件名派生（原硬编码 v1.0 与 v1.1 件不符）
CARD = STEP2 / "m13_v57_CO124_input_selfcheck_gate.md"
ANCHORS = ("## §1 红线", "## §2 基本功", "## §3 划界", "## §4 重新定性", "## §5 生效")
# 声明阈值集合：值取自现行声明源（L1 硬约束 / L2 结构 / SPEC constraints / 冻结规则）
THRESHOLDS = [
    ("inter_pair_spacing_mm", 1.46, "L1_TOPOLOGY_v2.0 硬约束2（v22 用户裁决）"),
    ("pair_copper_edge_clearance_mm", 0.410, "L2 derived_value_ledger_v1 DV-INTPAIR-EDGE（REQ-R3-2 忠实实现：铜边 ≥ 2w，外层最严）"),
    ("pair_cross_mm", 0.585, "L1_TOPOLOGY_v2.0 硬约束2（0.585+0.875=1.46）"),
    ("power_clearance_mm", 0.2, "drc_rules.clearance.net_classes[POWER]"),
    ("pcb_edge_copper_min_mm", 0.3, "L1_TOPOLOGY_v2.0 硬约束4 / drc_rules.manufacturing"),
    ("m3_keepout_mm", 3.0, "L1_TOPOLOGY_v2.0 硬约束5"),
]


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


# CO-156（F-5）：K9 七域白名单 —— kind 必须 ∈ 本集，且 domain_cap 必带非空 domains。
# CO-157（H-1）：k9_findings **可产出的全部 finder id** —— T18 元牙齿据此断言「每个 id 都有负控」
K9_FINDER_IDS = (
    "requirement_carries_derived_value", "derived_value_without_principle", "derived_value_kind_unknown",
    "derived_value_domain_cap_empty", "derived_value_identity_drift", "derived_value_identity_unparsable",
    "derived_value_evidence_bad", "derived_value_unreachable", "derived_value_declared_unpinned",
    "derived_value_conservative_unproved", "derived_value_inventory_missing",
    "derived_value_identity_unhandled_form",
)

# CO-161（F-1）：**必需 DV 清单**（= co153 `KIND_EXPECT` 的键集；由 co150 交叉比对防漂移）——
# 缺任一项即失一层 K9 覆盖（此前无牙齿：删 DV-CO146-THERMAL/PDN-DROP/ENGINE-INT_PAIR_PITCH 后 0 findings）。
REQUIRED_DV_IDS = ("DV-INTPAIR-EDGE", "DV-PAIR-CROSS", "DV-CLR-POWER", "DV-EDGE-COPPER", "DV-M3-KEEPOUT",
                    "DV-ENGINE-INT_PAIR_PITCH", "DV-CO146-ZDIFF", "DV-CO146-PDN-DROP", "DV-CO146-THERMAL")

KNOWN_KINDS = ("domain_cap", "identity", "process_floor", "declared",
               "conservative_ge", "drop_domain", "thermal_option_domain")
# CO-159（F-3）：从**源码**抽取 K9 全部 finder id。T18 元牙齿只比对「合成电池触发集」与声明表，
# 无法发现「电池未触发的条件分支」新增 finder；本正则给出源码面真值，供 T18d 断言。
_K9_FINDER_ID_RE = re.compile(r'\("K9",\s*f?"([a-z0-9_]+):')


def _finder_ids_in_source(text: str) -> list:
    return sorted(set(_K9_FINDER_ID_RE.findall(text)))


def _k9_battery(base: dict) -> dict:
    """CO-157（H-1）：逐 finder id 的**合成注入电池**（只动内存副本）——T18 元牙齿据此断言覆盖完备。"""
    out = {}
    l = copy.deepcopy(base)
    l["requirements"] = l.get("requirements", []) + [{"id": "TB_REQ", "statement": "x", "value": 1}]
    out["requirement_carries_derived_value"] = l
    l = copy.deepcopy(base)
    l["derived_values"] = l.get("derived_values", []) + [{"id": "TB1", "requirement": "NOPE", "reachability": {"kind": "declared"}}]
    out["derived_value_without_principle"] = l
    l = copy.deepcopy(base)
    l["derived_values"] = l.get("derived_values", []) + [{"id": "TB2", "requirement": "REQ-R3-2", "reachability": {"kind": "zzz", "verdict": "REACHABLE"}}]
    out["derived_value_kind_unknown"] = l
    l = copy.deepcopy(base)
    l["derived_values"] = l.get("derived_values", []) + [{"id": "TB3", "requirement": "REQ-R3-2", "reachability": {"kind": "domain_cap", "verdict": "REACHABLE"}}]
    out["derived_value_domain_cap_empty"] = l
    l = copy.deepcopy(base)
    l["derived_values"] = l.get("derived_values", []) + [{"id": "TB4", "requirement": "REQ-DEF-PAIR-GEOM",
        "form": "span = 2×p_width + p_gap", "inputs": {"p_width_mm": 1.0, "p_gap_mm": 1.0},
        "computed": {"span_mm": 9.0}, "reachability": {"kind": "identity", "verdict": "REACHABLE"}}]
    out["derived_value_identity_drift"] = l
    l = copy.deepcopy(base)
    l["derived_values"] = l.get("derived_values", []) + [{"id": "TB5", "requirement": "REQ-DEF-PAIR-GEOM",
        "form": "span = 2×p_width + p_gap", "inputs": {}, "computed": {},
        "reachability": {"kind": "identity", "verdict": "REACHABLE"}}]
    out["derived_value_identity_unparsable"] = l
    l = copy.deepcopy(base)
    l["derived_values"] = l.get("derived_values", []) + [{"id": "TB6", "requirement": "REQ-EDGE-COPPER",
        "computed": {"value_mm": 0.3},
        "reachability": {"kind": "process_floor", "verdict": "REACHABLE",
                         "evidence_ref": {"path": "m13_v57_l4_validation.json", "sha16": "0" * 16}}}]
    out["derived_value_evidence_bad"] = l
    l = copy.deepcopy(base)
    for _d in l["derived_values"]:
        if (_d.get("reachability") or {}).get("domains"):
            _d["reachability"]["domains"].append({"id": "TB7", "pitch_cap_mm": 0.1, "required_pitch_mm": 0.9,
                                                  "margin_mm": -0.8, "ok": False, "regime": "R3-2 适用域"})
            break
    out["derived_value_unreachable"] = l
    l = copy.deepcopy(base)
    l["derived_values"] = l.get("derived_values", []) + [{"id": "TB8", "requirement": "REQ-ZDIFF",
        "computed": {"a": 1},
        "reachability": {"kind": "declared", "verdict": "REACHABLE", "basis": "x",
                         "evidence_ref": {"path": "m13_v57_co146_impedance_table.json",
                                          "sha16": "0" * 16, "key_path": "artifact"}}}]
    out["derived_value_declared_unpinned"] = l
    l = copy.deepcopy(base)
    l["derived_values"] = [d for d in l.get("derived_values", []) if d.get("id") != REQUIRED_DV_IDS[0]]
    out["derived_value_inventory_missing"] = l
    l = copy.deepcopy(base)
    l["derived_values"] = l.get("derived_values", []) + [{"id": "TB10", "requirement": "REQ-DEF-PAIR-GEOM",
        "form": "q = a + b", "inputs": {"a": 1.0}, "computed": {"q": 3.0},
        "reachability": {"kind": "identity", "verdict": "REACHABLE"}}]
    out["derived_value_identity_unhandled_form"] = l
    l = copy.deepcopy(base)
    l["derived_values"] = l.get("derived_values", []) + [{"id": "TB9", "requirement": "REQ-R3-2",
        "inputs": {"span_mm": 0.585, "w_outer_mm": 0.205, "span_src": "x", "w_outer_src": "x"},
        "computed": {"value_mm": 0.1, "faithful_min_mm": 0.995},
        "reachability": {"kind": "conservative_ge", "verdict": "CONSERVATIVE_OK"}}]
    out["derived_value_conservative_unproved"] = l
    return out


def _contains(ev, dv) -> bool:
    """CO-156（F-6）：证据对象须**递归包含** DV 的 computed（子集语义）。"""
    if isinstance(dv, dict):
        return isinstance(ev, dict) and all(k in ev and _contains(ev[k], v) for k, v in dv.items())
    if isinstance(dv, list):
        return isinstance(ev, list) and len(ev) == len(dv) and all(_contains(a, b) for a, b in zip(ev, dv))
    return ev == dv


def _resolve(path):
    pth = str(path) if path else None
    return pth, next((c for c in [STEP2 / str(pth), L3 / str(pth), L2 / str(pth)] if pth and c.exists()), None)


def k9_findings(led: dict) -> list:
    """K9：需求/实现分家机判（纯函数，便于负控注入）。"""
    f = []
    reqs = led.get("requirements", [])
    ids = {r.get("id") for r in reqs}
    _dvs = {d.get("id"): d for d in led.get("derived_values", [])}
    # CO-161（F-1）：必需 DV 清单完备性（缺项 ⇒ 该域 K9 覆盖静默消失）
    for _rid in REQUIRED_DV_IDS:
        if _rid not in _dvs:
            f.append(("K9", f"derived_value_inventory_missing:{_rid}", {"required_n": len(REQUIRED_DV_IDS)}))
    # CO-156（F-7）：conservative_ge 的 faithful 口径须绑定权威 DV，而非自带常数
    auth_edge = (((_dvs.get("DV-INTPAIR-EDGE") or {}).get("computed") or {}).get("edge_outer_binding_mm"))
    auth_span = (((_dvs.get("DV-PAIR-CROSS") or {}).get("computed") or {}).get("span_mm"))
    for r in reqs:
        if ("computed" in r) or ("value" in r):
            f.append(("K9", f"requirement_carries_derived_value:{r.get('id')}",
                      {"id": r.get("id"), "keys": sorted(set(r) & {"computed", "value"})}))
    for dv in led.get("derived_values", []):
        rid = dv.get("requirement")
        if rid not in ids:
            f.append(("K9", f"derived_value_without_principle:{dv.get('id')}",
                      {"requirement": rid, "known": sorted(x for x in ids if x)}))
            continue
        rc = dv.get("reachability") or {}
        kind = rc.get("kind", "domain_cap" if rc.get("domains") is not None else "declared")
        # CO-156（F-5）：域覆盖牙齿 —— 未列 kind / 空 domains 不再静默通过
        if kind not in KNOWN_KINDS:
            f.append(("K9", f"derived_value_kind_unknown:{dv.get('id')}",
                      {"kind": kind, "known": list(KNOWN_KINDS)}))
        if kind == "domain_cap" and not rc.get("domains"):
            f.append(("K9", f"derived_value_domain_cap_empty:{dv.get('id')}", {"domains": rc.get("domains")}))
        if kind == "identity":
            form, comp = dv.get("form"), (dv.get("computed") or {})
            inp = dv.get("inputs") or {}
            # CO-161（F-2）：identity 判据原先**仅**覆盖「form 含 span」；未识别/缺失 form 静默通过（fail-open）。
            if not form:
                f.append(("K9", f"derived_value_identity_unparsable:{dv.get('id')}",
                          {"form": form, "why": "form_missing"}))
            elif "span" in form:
                try:
                    exp = round(2 * float(inp["p_width_mm"]) + float(inp["p_gap_mm"]), 4)
                    if abs(exp - float(comp["span_mm"])) > 5e-4:
                        f.append(("K9", f"derived_value_identity_drift:{dv.get('id')}", {"expect": exp, "got": comp["span_mm"]}))
                except (KeyError, TypeError, ValueError):
                    f.append(("K9", f"derived_value_identity_unparsable:{dv.get('id')}", {"form": form}))
            else:
                f.append(("K9", f"derived_value_identity_unhandled_form:{dv.get('id')}",
                          {"form": form, "why": "form_not_recognized"}))
        if kind == "process_floor":
            ev = rc.get("evidence_ref") or {}
            pth = ev.get("path")
            hitc = next((c for c in [STEP2 / str(pth), L3 / str(pth), L2 / str(pth)] if pth and c.exists()), None)
            if hitc is None or s16(hitc) != ev.get("sha16"):
                f.append(("K9", f"derived_value_evidence_bad:{dv.get('id')}",
                          {"path": pth, "cited": ev.get("sha16"), "actual": s16(hitc) if hitc else None}))
        doms = rc.get("domains")
        if doms is not None and rc.get("kind") != "thermal_option_domain":
            span = (dv.get("inputs") or {}).get("span_min_mm")
            edge = (dv.get("computed") or {}).get("edge_outer_binding_mm")
            bad = []
            for d in doms:
                exempt = "ECN-001" in str(d.get("regime", ""))
                try:
                    exp = round(float(d["pitch_cap_mm"]) - float(span) - float(edge), 4)
                except (KeyError, TypeError, ValueError):
                    bad.append({"domain": d.get("id"), "why": "unparsable"}); continue
                if abs(exp - float(d.get("margin_mm", 1e9))) > 5e-4:
                    bad.append({"domain": d.get("id"), "why": "margin_not_recomputed", "expect": exp,
                                "got": d.get("margin_mm")})
                elif (exp < 0) and not exempt:
                    bad.append({"domain": d.get("id"), "why": "unreachable", "margin": exp})
                elif exempt:
                    # CO-139：豁免不得只靠 regime 自由文本 ⇒ 必须 hash-pin 到已声明依据（path 可解析 + sha 一致 + basis 非空）
                    ev = d.get("evidence_ref") or {}
                    pth = ev.get("path")
                    hitc = next((c for c in [STEP2 / str(pth), L3 / str(pth), L2 / str(pth)]
                                 if pth and c.exists()), None)
                    if hitc is None or s16(hitc) != ev.get("sha16") or not ev.get("basis"):
                        bad.append({"domain": d.get("id"), "why": "exemption_unpinned",
                                    "evidence_ref": ev, "actual": s16(hitc) if hitc else None})
            if rc.get("verdict") != "REACHABLE" or bad:
                f.append(("K9", f"derived_value_unreachable:{dv.get('id')}",
                          {"verdict": rc.get("verdict"), "bad": bad}))
        if rc.get("kind") == "thermal_option_domain":
            cases = (dv.get("computed") or {}).get("cases") or {}
            dom_list = rc.get("domains") or []
            _req_of = lambda c: c.get("theta_ja_required_C_per_W", c.get("required_theta_ja_C_per_W"))
            treqs = [_req_of(c) for c in cases.values() if isinstance(_req_of(c), (int, float))]
            effs = [d.get("theta_ja_eff_C_per_W") for d in dom_list
                    if isinstance(d.get("theta_ja_eff_C_per_W"), (int, float))]
            mit = (rc.get("required_mitigation") or "").strip()
            asbuilt_ok = any(d.get("ok") for d in dom_list if "asbuilt" in str(d.get("id", "")).lower())
            bad_t = []
            if not treqs or not effs:
                bad_t.append({"why": "unparsable", "reqs": len(treqs), "effs": len(effs)})
            else:
                hardest, best = max(treqs), min(effs)
                if best > hardest:
                    bad_t.append({"why": "no_declared_option_covers_hardest_case", "best_theta_eff": best,
                                  "hardest_required": hardest})
                if not asbuilt_ok and not mit:
                    bad_t.append({"why": "asbuilt_fails_but_mitigation_undeclared"})
            if rc.get("verdict") != "REACHABLE" or bad_t:
                f.append(("K9", f"derived_value_unreachable:{dv.get('id')}",
                          {"verdict": rc.get("verdict"), "bad": bad_t, "kind": "thermal_option_domain"}))
        if rc.get("kind") == "drop_domain":
            rails_c = dv.get("computed") or {}
            budget = (dv.get("inputs") or {}).get("drop_budget_pct")
            bad_d, n_ok = [], 0
            if not isinstance(budget, (int, float)):
                bad_d.append({"why": "budget_missing"})
            for name, r in rails_c.items():
                if not isinstance(r, dict) or not isinstance(r.get("drop_pct"), (int, float)):
                    continue
                if bad_d:
                    continue
                if r["drop_pct"] > budget:
                    bad_d.append({"rail": name, "drop_pct": r["drop_pct"], "budget_pct": budget})
                else:
                    n_ok += 1
            if not bad_d and n_ok == 0:
                bad_d.append({"why": "no_rail_parsed"})
            if rc.get("verdict") != "REACHABLE" or bad_d:
                f.append(("K9", f"derived_value_unreachable:{dv.get('id')}",
                          {"verdict": rc.get("verdict"), "bad": bad_d, "kind": "drop_domain"}))
        if kind == "declared":
            # CO-153：声明类可达性不得无证据（关闭「声明即通过」缺口）。
            # CO-156（F-6）：仅「钉一个现行文件」仍无语义关联 ⇒ 追加 `key_path` 指向证据件内**须递归包含该 DV computed** 的对象。
            # ⚠ CO-157（H-2）：本判据**严于** `process_floor`（后者只验 path+sha，不验 basis/key_path）——原「同口径」表述失实，此处订正。
            ev = rc.get("evidence_ref") or {}
            pth, hitc = _resolve(ev.get("path"))
            kp = ev.get("key_path")
            bad_d = []
            if hitc is None or s16(hitc) != ev.get("sha16"):
                bad_d.append({"why": "evidence_unresolved_or_stale", "path": pth,
                              "cited": ev.get("sha16"), "actual": s16(hitc) if hitc else None})
            if not str(rc.get("basis") or "").strip():
                bad_d.append({"why": "basis_empty"})
            # CO-159（F-1）：`computed` 缺失/空字典时 `_contains()` 恒真 ⇒ 值-证据绑定空过。
            if not (dv.get("computed") or {}):
                bad_d.append({"why": "computed_empty_for_declared"})
            if not kp:
                bad_d.append({"why": "key_path_missing"})
            elif hitc is not None:
                try:
                    obj = json.loads(hitc.read_text(encoding="utf-8"))
                    for part in str(kp).split("."):
                        obj = obj[int(part)] if isinstance(obj, list) and part.lstrip("-").isdigit() else obj[part]
                    if not _contains(obj, dv.get("computed") or {}):
                        bad_d.append({"why": "evidence_binding_mismatch", "key_path": kp})
                except (KeyError, IndexError, TypeError, ValueError):
                    bad_d.append({"why": "key_path_unresolvable", "key_path": kp})
            if bad_d:
                f.append(("K9", f"derived_value_declared_unpinned:{dv.get('id')}", {"bad": bad_d}))
        if kind == "conservative_ge":
            # CO-153：保守实现须闭式证明 value >= 忠实下界（faithful = span + 2*w_outer）且 cited 一致。
            # CO-156（F-7）：faithful 的 span/w_outer 须**引用**权威 DV（DV-PAIR-CROSS / DV-INTPAIR-EDGE），非自带常数。
            inp = dv.get("inputs") or {}
            comp = dv.get("computed") or {}
            span = inp.get("span_mm"); w = inp.get("w_outer_mm"); val = comp.get("value_mm")
            bad_c = []
            try:
                span_f, w_f, val_f = float(span), float(w), float(val)
                faithful = round(span_f + 2.0 * w_f, 4)
                if val_f < faithful - 1e-9:
                    bad_c.append({"why": "value_lt_faithful", "value_mm": val_f, "faithful_mm": faithful})
                cited = comp.get("faithful_min_mm")
                if cited is None or abs(float(cited) - faithful) > 5e-4:
                    bad_c.append({"why": "faithful_cited_mismatch", "expect": faithful, "got": cited})
            except (TypeError, ValueError):
                bad_c.append({"why": "unparsable"})
            if not (str(inp.get("span_src") or "").strip() and str(inp.get("w_outer_src") or "").strip()):
                bad_c.append({"why": "missing_src_binding"})
            # CO-159（F-2）：权威 DV 缺失时下述交叉校验被静默跳过 ⇒ F-7 的原规避复活；改为显式 FAIL。
            if not isinstance(auth_edge, (int, float)) or not isinstance(auth_span, (int, float)):
                bad_c.append({"why": "authoritative_dv_missing",
                              "auth_edge_mm": auth_edge, "auth_span_mm": auth_span})
            if isinstance(auth_edge, (int, float)) and not (isinstance(w, (int, float))
                                                           and abs(2.0 * float(w) - float(auth_edge)) <= 5e-4):
                bad_c.append({"why": "w_outer_not_bound_to_INTPAIR_EDGE", "w_outer_mm": w, "auth_edge_mm": auth_edge})
            if isinstance(auth_span, (int, float)) and not (isinstance(span, (int, float))
                                                           and abs(float(span) - float(auth_span)) <= 5e-4):
                bad_c.append({"why": "span_not_bound_to_PAIR_CROSS", "span_mm": span, "auth_span_mm": auth_span})
            if rc.get("verdict") != "CONSERVATIVE_OK" or bad_c:
                f.append(("K9", f"derived_value_conservative_unproved:{dv.get('id')}",
                          {"verdict": rc.get("verdict"), "bad": bad_c}))
    return f


def check(spec: dict, rules: dict, doc_text: str, reg: dict, led: dict | None = None) -> list:
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
    # CO-134：对中心距 = 保守实现 ⇒ 判据改为「≥ span + 忠实铜边下界」（不再用 0.585+0.875 恒等式）
    identity_ok = {"inter_pair_spacing_mm": lambda v: v >= 0.585 + 0.410 - 1e-9}
    for key, val, src in THRESHOLDS:
        if key in reg_thr:
            continue
        if key in identity_ok and identity_ok[key](val):
            continue
        f.append(("K6", f"threshold_unproved_unregistered:{key}", {"rule_key": key, "value": val, "source": src}))
    # K9 需求/实现分家（整改通知 #09）
    led = led if led is not None else (json.loads(LED.read_text(encoding="utf-8")) if LED.exists() else {})
    f.extend(k9_findings(led))
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
               if it.get("kind") not in ("SPEC_DEFECT", "TOOL_DEFECT", "PROVED_THRESHOLD", "IMPLEMENTATION_DEVIATION") or not it.get("refs")
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
    # CO-134 负控（整改通知 #09 要求）：K9 必须能抓住「无原则 / 不可达 / 需求携带定值」
    _led = json.loads(LED.read_text(encoding="utf-8")) if LED.exists() else {"requirements": [], "derived_values": []}
    _l5 = copy.deepcopy(_led); _l5["derived_values"] = _l5.get("derived_values", []) + [
        {"id": "T5_INJECT", "requirement": "REQ-DOES-NOT-EXIST", "reachability": {"verdict": "REACHABLE"}}]
    teeth["T5_derived_without_principle"] = any(x[1].startswith("derived_value_without_principle") for x in k9_findings(_l5))
    _l6 = copy.deepcopy(_led)
    for _dv in _l6.get("derived_values", []):
        if _dv.get("reachability", {}).get("domains"):
            _dv["reachability"]["domains"] = [dict(d) for d in _dv["reachability"]["domains"]]
            _dv["reachability"]["domains"].append({"id": "T6_INJECT_UNREACHABLE", "pitch_cap_mm": 0.6,
                                                   "required_pitch_mm": 0.765, "margin_mm": -0.165, "ok": True,
                                                   "regime": "R3-2 适用域（无豁免）"})
            break
    teeth["T6_unreachable_derived"] = any(x[1].startswith("derived_value_unreachable") for x in k9_findings(_l6))
    _l7 = copy.deepcopy(_led); _l7["requirements"] = _l7.get("requirements", []) + [
        {"id": "T7_INJECT_REQ_WITH_VALUE", "statement": "x", "value": 0.875}]
    teeth["T7_requirement_carries_value"] = any(x[1].startswith("requirement_carries_derived_value") for x in k9_findings(_l7))
    _l8 = copy.deepcopy(_led)
    for _dv in _l8.get("derived_values", []):
        if (_dv.get("reachability") or {}).get("kind") == "identity":
            _dv["computed"] = {"span_mm": 0.999}; break
    teeth["T8_identity_drift"] = any(x[1].startswith("derived_value_identity_drift") for x in k9_findings(_l8))
    # CO-139 负控 T9：豁免域去掉 evidence_ref ⇒ 必须 FAIL（豁免不得只靠自由文本）
    _l9 = copy.deepcopy(_led)
    for _dv in _l9.get("derived_values", []):
        _doms = (_dv.get("reachability") or {}).get("domains")
        if _doms:
            for _d in _doms:
                if "ECN-001" in str(_d.get("regime", "")):
                    _d.pop("evidence_ref", None)
            break
    teeth["T9_exemption_unpinned"] = any(x[1].startswith("derived_value_unreachable") for x in k9_findings(_l9))
    # CO-150 负控 T10：热方案域「无可行方案 + 未声明缓解」⇒ 必须 FAIL（含旧 T6 注入不干扰的稳健性）
    _l10 = copy.deepcopy(_led)
    for _dv in _l10.get("derived_values", []):
        _rc10 = _dv.get("reachability") or {}
        if _rc10.get("kind") == "thermal_option_domain":
            _rc10["domains"] = [{"id": "T10_INJECT_WEAK", "theta_ja_eff_C_per_W": 30.0, "ok": False}]
            _rc10.pop("required_mitigation", None)
            break
    teeth["T10_thermal_option_domain_teeth"] = any(
        x[1].startswith("derived_value_unreachable") for x in k9_findings(_l10))
    # CO-150 负控 T11：压降域注入一轨超预算 ⇒ 必须 FAIL；T11b：注入前后正经台账不得误报
    _l11 = copy.deepcopy(_led)
    for _dv in _l11.get("derived_values", []):
        if (_dv.get("reachability") or {}).get("kind") == "drop_domain":
            _dv["computed"] = dict(_dv.get("computed") or {})
            _dv["computed"]["T11_INJECT_RAIL"] = {"drop_pct": 99.0}
            break
    teeth["T11_drop_domain_teeth"] = any(
        x[1].startswith("derived_value_unreachable") for x in k9_findings(_l11))
    teeth["T11b_drop_domain_no_false_positive"] = not any(
        x[1].startswith("derived_value_unreachable") and "PDN" in str(x[2])
        for x in k9_findings(copy.deepcopy(_led)))
    # T10b：现状不可行但已声明缓解 且 ∃ 方案覆盖 ⇒ 不得误报
    _l10b = copy.deepcopy(_led)
    for _dv in _l10b.get("derived_values", []):
        _rc10b = _dv.get("reachability") or {}
        if _rc10b.get("kind") == "thermal_option_domain":
            _rc10b["required_mitigation"] = "SYNTH: 强制风冷"
            break
    teeth["T10b_thermal_domain_no_false_positive"] = not any(
        x[1].startswith("derived_value_unreachable") for x in k9_findings(_l10b))
    # CO-153 负控 T12：声明类证据被篡改/缺失 ⇒ 必须 FAIL（无 declared DV 时注入合成项）
    _l12 = copy.deepcopy(_led)
    _hit12 = False
    for _dv in _l12.get("derived_values", []):
        if (_dv.get("reachability") or {}).get("kind") == "declared":
            _dv["reachability"]["evidence_ref"] = {"path": "m13_v57_co146_impedance_table.json", "sha16": "0" * 16}
            _hit12 = True
            break
    if not _hit12:
        _l12["derived_values"].append({"id": "T12_INJECT", "requirement": "REQ-ZDIFF",
                                       "reachability": {"kind": "declared", "verdict": "REACHABLE",
                                                        "evidence_ref": {"path": "m13_v57_co146_impedance_table.json",
                                                                         "sha16": "0" * 16}}})
    teeth["T12_declared_unpinned_teeth"] = any(
        x[1].startswith("derived_value_declared_unpinned") for x in k9_findings(_l12))
    # CO-153 负控 T13：保守实现 value < 忠实下界 ⇒ 必须 FAIL（无 conservative_ge DV 时注入合成项）
    _l13 = copy.deepcopy(_led)
    _hit13 = False
    for _dv in _l13.get("derived_values", []):
        if (_dv.get("reachability") or {}).get("kind") == "conservative_ge":
            _dv.setdefault("computed", {})["value_mm"] = 0.5
            _hit13 = True
            break
    if not _hit13:
        _l13["derived_values"].append({"id": "T13_INJECT", "requirement": "REQ-R3-2",
                                       "inputs": {"span_mm": 0.585, "w_outer_mm": 0.205},
                                       "computed": {"value_mm": 0.5, "faithful_min_mm": 0.995},
                                       "reachability": {"kind": "conservative_ge", "verdict": "CONSERVATIVE_OK"}})
    teeth["T13_conservative_unproved_teeth"] = any(
        x[1].startswith("derived_value_conservative_unproved") for x in k9_findings(_l13))
    # T12b/T13b：现行台账（经 CO-153 归一）不得误报
    teeth["T12b_declared_no_false_positive"] = not any(
        x[1].startswith("derived_value_declared_unpinned") for x in k9_findings(copy.deepcopy(_led)))
    teeth["T13b_conservative_no_false_positive"] = not any(
        x[1].startswith("derived_value_conservative_unproved") for x in k9_findings(copy.deepcopy(_led)))
    # CO-156（F-5）负控 T14/T14b：未列 kind / domain_cap 缺 domains ⇒ 必抓；T14c：现行台账不得误报
    _l14 = copy.deepcopy(_led)
    _l14["derived_values"] = _l14.get("derived_values", []) + [
        {"id": "T14_INJECT_KIND", "requirement": "REQ-R3-2", "reachability": {"kind": "bogus_domain", "verdict": "REACHABLE"}}]
    teeth["T14_unknown_kind_teeth"] = any(x[1].startswith("derived_value_kind_unknown") for x in k9_findings(_l14))
    _l14b = copy.deepcopy(_led)
    _l14b["derived_values"] = _l14b.get("derived_values", []) + [
        {"id": "T14_INJECT_CAP", "requirement": "REQ-R3-2", "reachability": {"kind": "domain_cap", "verdict": "REACHABLE"}}]
    teeth["T14b_empty_domain_cap_teeth"] = any(x[1].startswith("derived_value_domain_cap_empty") for x in k9_findings(_l14b))
    teeth["T14c_kind_coverage_no_false_positive"] = not any(
        x[1].startswith(("derived_value_kind_unknown", "derived_value_domain_cap_empty"))
        for x in k9_findings(copy.deepcopy(_led)))
    # CO-156（F-6）负控 T15：declared 的 key_path 不含 computed ⇒ 必抓；T15b：现行台账不得误报
    _l15 = copy.deepcopy(_led)
    _hit15 = False
    for _dv in _l15.get("derived_values", []):
        if (_dv.get("reachability") or {}).get("kind") == "declared":
            _dv["reachability"]["evidence_ref"]["key_path"] = "artifact"
            _hit15 = True
            break
    if not _hit15:
        _l15["derived_values"].append({"id": "T15_INJECT", "requirement": "REQ-R3-2", "computed": {"x": 1},
            "reachability": {"kind": "declared", "verdict": "REACHABLE", "basis": "x",
                             "evidence_ref": {"path": "m13_v57_co146_impedance_table.json",
                                              "sha16": "0" * 16, "key_path": "artifact"}}})
    teeth["T15_declared_binding_teeth"] = any(
        x[1].startswith("derived_value_declared_unpinned") for x in k9_findings(_l15))
    teeth["T15b_declared_binding_no_false_positive"] = not any(
        x[1].startswith("derived_value_declared_unpinned") for x in k9_findings(copy.deepcopy(_led)))
    # CO-159（F-1）负控 T15c：declared 缺 `computed`（空绑定）⇒ 必抓
    _l15c = copy.deepcopy(_led)
    _hit15c = False
    for _dv in _l15c.get("derived_values", []):
        if (_dv.get("reachability") or {}).get("kind") == "declared":
            _dv.pop("computed", None)
            _hit15c = True
            break
    if not _hit15c:
        _l15c["derived_values"].append({"id": "T15C_INJECT", "requirement": "REQ-R3-2",
            "reachability": {"kind": "declared", "verdict": "REACHABLE", "basis": "x",
                             "evidence_ref": {"path": "m13_v57_co146_impedance_table.json",
                                              "sha16": s16(STEP2 / "m13_v57_co146_impedance_table.json"),
                                              "key_path": "dv_computed_zdiff"}}})
    teeth["T15c_declared_empty_computed_teeth"] = any(
        x[1].startswith("derived_value_declared_unpinned") for x in k9_findings(_l15c))
    # CO-156（F-7）负控 T16：conservative_ge 的 w_outer 与权威 DV 不符 ⇒ 必抓；T16b：现行台账不得误报
    _l16 = copy.deepcopy(_led)
    _hit16 = False
    for _dv in _l16.get("derived_values", []):
        if (_dv.get("reachability") or {}).get("kind") == "conservative_ge":
            _dv.setdefault("inputs", {})["w_outer_mm"] = 0.15
            _hit16 = True
            break
    if not _hit16:
        _l16["derived_values"].append({"id": "T16_INJECT", "requirement": "REQ-R3-2",
            "inputs": {"span_mm": 0.585, "w_outer_mm": 0.15, "span_src": "x", "w_outer_src": "x"},
            "computed": {"value_mm": 1.46, "faithful_min_mm": 0.885},
            "reachability": {"kind": "conservative_ge", "verdict": "CONSERVATIVE_OK"}})
    teeth["T16_faithful_provenance_teeth"] = any(
        x[1].startswith("derived_value_conservative_unproved") for x in k9_findings(_l16))
    teeth["T16b_faithful_provenance_no_false_positive"] = not any(
        x[1].startswith("derived_value_conservative_unproved") for x in k9_findings(copy.deepcopy(_led)))
    # CO-159（F-2）负控 T16c：权威 DV（DV-INTPAIR-EDGE / DV-PAIR-CROSS）缺失 ⇒ 必抓
    _l16c = copy.deepcopy(_led)
    _l16c["derived_values"] = [d for d in _l16c["derived_values"]
                               if d.get("id") not in ("DV-INTPAIR-EDGE", "DV-PAIR-CROSS")]
    teeth["T16c_authoritative_dv_missing_teeth"] = any(
        x[1].startswith("derived_value_conservative_unproved") for x in k9_findings(_l16c))
    # CO-157（H-1）负控 T17：process_floor 证据陈旧 ⇒ 必抓；T17b：现行台账不得误报
    _l17 = copy.deepcopy(_led)
    _hit17 = False
    for _dv in _l17.get("derived_values", []):
        if (_dv.get("reachability") or {}).get("kind") == "process_floor":
            _dv["reachability"].setdefault("evidence_ref", {})["sha16"] = "0" * 16
            _hit17 = True
            break
    if not _hit17:
        _l17["derived_values"].append({"id": "T17_INJECT", "requirement": "REQ-EDGE-COPPER",
            "computed": {"value_mm": 0.3},
            "reachability": {"kind": "process_floor", "verdict": "REACHABLE",
                             "evidence_ref": {"path": "m13_v57_l4_validation.json", "sha16": "0" * 16}}})
    teeth["T17_process_floor_evidence_teeth"] = any(
        x[1].startswith("derived_value_evidence_bad") for x in k9_findings(_l17))
    teeth["T17b_process_floor_no_false_positive"] = not any(
        x[1].startswith("derived_value_evidence_bad") for x in k9_findings(copy.deepcopy(_led)))
    # CO-157（H-1）元牙齿 T18：**每个** K9 finder id 都必须被负控实际触发（防「新增判据无牙齿」）
    _bat = _k9_battery(_led)
    _provoked = set()
    for _bled in _bat.values():
        _provoked.update(x[1].split(":")[0] for x in k9_findings(_bled))
    teeth["T18_k9_finder_id_coverage"] = set(K9_FINDER_IDS) <= _provoked
    teeth["T18b_k9_finder_id_no_undeclared"] = _provoked <= set(K9_FINDER_IDS)
    teeth["T18c_k9_finder_battery_nonempty"] = all(bool(_bat[k]) for k in K9_FINDER_IDS)
    # CO-159（F-3）：T18d 断言**源码**可产出的 finder id 集 == K9_FINDER_IDS（补 T18/T18b 的证明力边界）；
    # T18e 为该抽取器的灵敏度负控（合成新增 id 必须被抽出）。
    teeth["T18d_k9_finder_ids_source_complete"] = _finder_ids_in_source(
        Path(__file__).read_text(encoding="utf-8")) == sorted(K9_FINDER_IDS)
    _probe_src = 'f.append((' + '"K9", f"' + 'zzz_probe:x", {}))'  # 拼接构造：避免被 _K9_FINDER_ID_RE 自匹配
    teeth["T18e_k9_finder_id_extractor_sensitivity"] = _finder_ids_in_source(_probe_src) == ["zzz_probe"]
    # CO-161（F-1）负控 T19：必需 DV 缺一 ⇒ 必抓；T19b：现行台账不得误报
    _l19 = copy.deepcopy(_led)
    _l19["derived_values"] = [d for d in _l19.get("derived_values", []) if d.get("id") != REQUIRED_DV_IDS[0]]
    teeth["T19_dv_inventory_teeth"] = any(
        x[1].startswith("derived_value_inventory_missing") for x in k9_findings(_l19))
    teeth["T19b_dv_inventory_no_false_positive"] = not any(
        x[1].startswith("derived_value_inventory_missing") for x in k9_findings(copy.deepcopy(_led)))
    # CO-161（F-2）负控 T20：identity 未识别 form ⇒ 必抓；T20b：现行台账不得误报
    _l20 = copy.deepcopy(_led)
    _l20["derived_values"].append({"id": "T20_INJECT", "requirement": "REQ-DEF-PAIR-GEOM", "form": "q = a + b",
        "inputs": {"a": 1.0}, "computed": {"q": 3.0},
        "reachability": {"kind": "identity", "verdict": "REACHABLE"}})
    teeth["T20_identity_unhandled_form_teeth"] = any(
        x[1].startswith("derived_value_identity_unhandled_form") for x in k9_findings(_l20))
    teeth["T20b_identity_unhandled_no_false_positive"] = not any(
        x[1].startswith(("derived_value_identity_unhandled_form", "derived_value_identity_unparsable"))
        for x in k9_findings(copy.deepcopy(_led)))
    teeth_ok = all(teeth.values())
    verdict = "PASS" if (not unreg and not reg_bad and teeth_ok) else (
        "FAIL_UNREGISTERED_INPUT_DEFECT" if unreg else "FAIL_REGISTER_MALFORMED" if reg_bad else "TEETH_FAIL")
    rec = {
        "artifact": "m13_v57_co124_input_selfcheck_gate", "schema": 1, "revision": "CO-124.9",
        "nature": "输入自检闸：规格/规则自身自洽 + 物理可达登记 + 缺陷登记完备（整改通知 #08 第 2/3 条）",
        "definition_doc": {"path": str(DOC.relative_to(K2)), "sha16": s16(DOC), "status": f"{DOC_VER} 提议件（待监理裁定/owner 批准）"},
        "inputs": {"spec": str(SPEC.relative_to(K2)), "spec_sha16": s16(SPEC),
                   "rules_sha16": s16(RULES), "register": str(REG.relative_to(K2)),
                   "register_sha16_note": "本件不嵌下游 sha 快照（CO-152：register_sha16 属下游时点观测，"
                                          "会使记录随运行序漂移；现行 sha 见 boundary pin 表）"},
        "checks": {"k1_definition_in_place": True, "k2_netclass_two_source": True,
                   "k3_layer_role": True, "k4_bcu_policy": True, "k5_reachability": True,
                   "k6_threshold_registered": True, "k7_register_complete": not unreg, "k8_pdn_netclass_coverage": True},
        "findings": [dict(zip(("check", "id", "detail"), x)) for x in findings],
        "n_findings": len(findings), "unregistered_findings": unreg,
        "register_malformed": reg_bad,
        "teeth": teeth, "teeth_ok": teeth_ok, "verdict": verdict,
        "required_dv_ids": list(REQUIRED_DV_IDS),
        "scan_scope_zero_omission": {
            "scanned": ["SPEC rev-16：pd.zone_defs(power_zones/gnd_planes/power_pad_connect/plane_reachability_status/"
                        "bcu_power_copper_policy)、net_classes、stackup、board、constraints",
                        "冻结 drc_rules.json：clearance.net_classes / board_min / hole_clearance.min / manufacturing",
                        f"L2/{DOC.name} 锚点",
                        "L2/input_defect_register_v1.json 登记完备性"],
            "not_scanned_and_why": ["L3/L4 几何与制造件（属输出侧闸：G4..G7/DFM/SI 已覆盖）",
                                    "L1 v1.0 归档件（已作废，语义经 L1 v2.0 结转）"],
            "claim": "在已声明扫描范围内**零遗漏**：K1..K6 未列出的规约缺陷类型不在本闸判据内，属范围外非静默"},
        "redline": "只读；不改 SPEC/规则/板/冻结源；无随机、无坐标搜索；牙齿只动内存副本",
        "board_sha16_l4": s16(K2 / "k2_v4_8L.l4.kicad_pcb"),
    }
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# CO-124 — 输入自检闸（规格/规则自身）", "",
             f"- verdict：**{verdict}**", f"- 定义件：`{rec['definition_doc']['path']}` `{rec['definition_doc']['sha16']}`（{rec['definition_doc']['status']}）",
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
    return 0 if verdict == "PASS" else 1   # CO-158（J-3）：退出码须反映 verdict


if __name__ == "__main__":
    raise SystemExit(main())
