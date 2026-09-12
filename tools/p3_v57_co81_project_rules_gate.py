#!/usr/bin/env python3
"""CO-81：【L2 可审计性 · 回归闸】受控工程文件设计规则 = 红线规则源（机判闸）。

把 CO-80 的 F-80-1 缺陷类固化为**可重复闸**：
  每个**受版本控制**的 `*.kicad_pro` 的 DRC 设计规则，必须等于**红线规则源**
  `_shared/eda_core/drc_rules.json:manufacturing`（+`hole_clearance:min`）；
  且 `rule_severities` 必须等于 JLC 模板 `tools/k2_jlc_template.kicad_pro`。

理由：`kicad-cli` 对 `<board>.kicad_pcb` 做 DRC 时会**自动选取**同名 `<board>.kicad_pro`；
若该文件规则与意图不符（如实测 F-80-1：kiCad 默认 0.2/0.5/0.3/0.5），
则**最自然的独立核查命令**会大面积误报（880 条），审计者据此误判板子不合格。

用法：python3 tools/p3_v57_co81_project_rules_gate.py
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
RULES = K2.parent / "_shared/eda_core/drc_rules.json"
TEMPLATE = K2 / "tools/k2_jlc_template.kicad_pro"
INTENT_PRO = K2 / "k2_v4_8L.kicad_pro"   # 意图工程（含 4 网类 + 网-类指派）
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-11.json"   # 红线 SPEC（net_classes 权威）
TEMPLATE_EXEMPT = "tools/k2_jlc_template.kicad_pro"
OUT = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_co81_project_rules_gate.json"

# 工程文件键 -> drc_rules.json 路径
KEYMAP = {
    "min_track_width": ("manufacturing", "min_track_width"),
    "min_via_diameter": ("manufacturing", "min_via_diameter"),
    "min_via_annular_width": ("manufacturing", "min_annular_width"),
    "min_through_hole_diameter": ("manufacturing", "min_through_hole_diameter"),
    "min_copper_edge_clearance": ("manufacturing", "min_copper_edge_clearance"),
    "min_clearance": ("manufacturing", "min_clearance"),
    "min_hole_clearance": ("hole_clearance", "min"),
}


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def netclass_guard(ns: dict, intent_ns: dict) -> dict:
    """网类定义 + 网-类指派 与意图件比对；返回失配描述（空 = 通过）。"""
    def byname(classes):
        return {c.get("name"): {k: v for k, v in c.items() if k != "name"} for c in (classes or [])}
    a, b = byname(ns.get("classes")), byname(intent_ns.get("classes"))
    out = {}
    for n in sorted(set(a) | set(b)):
        if a.get(n) != b.get(n):
            ka = a.get(n) or {}
            kb = b.get(n) or {}
            out["class:" + str(n)] = {k: [ka.get(k), kb.get(k)] for k in set(ka) | set(kb)
                                      if ka.get(k) != kb.get(k)}
    asg, iasg = ns.get("netclass_assignments") or {}, intent_ns.get("netclass_assignments") or {}
    if asg != iasg:
        diff = {k: [asg.get(k), iasg.get(k)] for k in set(asg) | set(iasg) if asg.get(k) != iasg.get(k)}
        out["netclass_assignments"] = {"n_file": len(asg), "n_intent": len(iasg),
                                       "n_differing": len(diff), "sample": dict(list(diff.items())[:5])}
    return out


# CO-83：工程网类 -> SPEC net_classes 的 DRC 相关字段映射
NC_SPEC_MAP = {"LOW_SPEED": [("clearance", ("clearance",)), ("track_width", ("width",))],
               "PCIe85": [("clearance", ("clearance",)), ("track_width", ("width",)),
                          ("diff_pair_gap", ("diff_pair", "p_gap")),
                          ("diff_pair_width", ("diff_pair", "p_width"))],
               "POWER": [("clearance", ("clearance",)), ("track_width", ("width",))]}


def netclass_vs_spec(ns: dict, spec_nc: dict) -> dict:
    """工程网类（DRC 相关字段）vs 红线 SPEC net_classes；返回失配（空 = 通过）。"""
    byname = {c.get("name"): c for c in (ns.get("classes") or [])}
    out = {}
    for cls, fields in NC_SPEC_MAP.items():
        c = byname.get(cls)
        if c is None:
            out[cls] = "class missing in project"
            continue
        sp = spec_nc.get(cls) or {}
        for pkey, path in fields:
            v = sp
            for k in path:
                v = (v or {}).get(k) if isinstance(v, dict) else None
            if c.get(pkey) != v:
                out["%s.%s" % (cls, pkey)] = [c.get(pkey), v]
    return out


def guard(pro_rules: dict, expect: dict) -> dict:
    """返回 {key: (actual, expected)} 的失配集；空 = 通过（纯函数，便于负控）。"""
    return {k: (pro_rules.get(k), expect.get(k)) for k in expect if pro_rules.get(k) != expect.get(k)}


def main() -> int:
    rr = json.loads(RULES.read_text(encoding="utf-8"))
    expect = {k: rr[a][b] for k, (a, b) in KEYMAP.items()}
    tmpl = json.loads(TEMPLATE.read_text(encoding="utf-8"))["board"]["design_settings"]
    tmpl_sev = dict(tmpl["rule_severities"])
    intent_ns = json.loads(INTENT_PRO.read_text(encoding="utf-8"))["net_settings"]
    spec_nc = json.loads(SPEC.read_text(encoding="utf-8"))["net_classes"]
    spec_vs = netclass_vs_spec(intent_ns, spec_nc)
    tracked = subprocess.run(["git", "ls-files", "*.kicad_pro"], cwd=str(K2),
                             capture_output=True, text=True).stdout.split()
    rows, bad = [], []
    for rel in sorted(tracked):
        p = K2 / rel
        d = json.loads(p.read_text(encoding="utf-8"))["board"]["design_settings"]
        miss = guard(d["rules"], expect)
        if rel == TEMPLATE_EXEMPT:
            nc = {}          # 模板只承载规则，不含 4 网类/指派（设计如此，显式豁免）
        else:
            nc = netclass_guard(json.loads(p.read_text(encoding="utf-8"))["net_settings"], intent_ns)
            nc.update({"__vs_spec__:" + k: v for k, v in
                       netclass_vs_spec(json.loads(p.read_text(encoding="utf-8"))["net_settings"], spec_nc).items()})
        sev = {k: (d["rule_severities"].get(k), tmpl_sev.get(k))
               for k in tmpl_sev if d["rule_severities"].get(k) != tmpl_sev.get(k)}
        ok = not miss and not sev and not nc
        rows.append({"file": rel, "sha16": s16(p), "ok": ok,
                     "rules_mismatch": miss, "severity_mismatch": sev, "netclass_mismatch": nc})
        if not ok:
            bad.append(rel)
    # 负控（有齿）：喂坏输入必须被抓到
    neg = guard({**expect, "min_track_width": 0.2}, expect)
    pos = guard(dict(expect), expect)
    teeth = (neg == {"min_track_width": (0.2, expect["min_track_width"])}) and (pos == {})
    # 历史对照（F-80-1 实测原值，见 CO-80 记录）：闸必须抓到该状态
    f80_1 = {"min_track_width": 0.2, "min_via_diameter": 0.5, "min_via_annular_width": 0.1,
             "min_through_hole_diameter": 0.3, "min_copper_edge_clearance": 0.5,
             "min_clearance": 0.0, "min_hole_clearance": 0.25}
    hist = guard(f80_1, expect)
    hist_ok = len(hist) == 6      # min_hole_clearance 原本就一致
    # CO-82：网类历史对照 = 修复前状态（仅 Default、无指派）
    nc_hist = netclass_guard({"classes": [{"name": "Default"}], "netclass_assignments": {}}, intent_ns)
    nc_hist_ok = ("netclass_assignments" in nc_hist
                  and nc_hist["netclass_assignments"]["n_differing"] == len(
                      intent_ns.get("netclass_assignments") or {})
                  and any(k.startswith("class:") for k in nc_hist))
    teeth = teeth and nc_hist_ok
    # CO-83 负控：篡改 SPEC 侧期望值必须被抓到
    spec_neg = netclass_vs_spec(intent_ns, {**spec_nc,
                                           "PCIe85": {**spec_nc["PCIe85"], "clearance": 0.2}})
    teeth = teeth and (spec_neg == {"PCIe85.clearance": [0.175, 0.2]})
    teeth = teeth and hist_ok
    rec = {"artifact": "m13_v57_co81_project_rules_gate", "schema": 1, "revision": "CO-81.1",
           "nature": "L2 可审计性：受控工程文件设计规则 = 红线规则源 的回归闸",
           "authority_source": {"file": str(RULES.relative_to(K2.parent)), "sha16": s16(RULES),
                                "section": "manufacturing + hole_clearance:min"},
           "severity_reference": {"file": str(TEMPLATE.relative_to(K2)), "sha16": s16(TEMPLATE)},
           "expected": expect, "files_checked": rows,
           "violations": bad,
           "negative_control": neg, "positive_control": pos,
           "historical_control_F80_1": {"rules": f80_1, "mismatch": hist, "n_mismatch": len(hist)},
           "historical_control_F82_1_netclass": {
               "n_class_keys_flagged": sum(1 for k in nc_hist if k.startswith("class:")),
               "assignments_n_differing": nc_hist.get("netclass_assignments", {}).get("n_differing")},
           "teeth_ok": teeth,
           "verdict": "PASS" if (not bad and teeth) else "FAIL",
           "rationale": "kicad-cli 对 <board>.kicad_pcb 自动选取同名 .kicad_pro；规则不符则自然核查命令大面积误报（F-80-1）；"
                        "网类/指派缺失则 DRC 根本不施加 netclass 语义（F-82-1）。CO-81 原只覆盖 rules/severities，CO-82 补网类后覆盖完整。",
           "netclass_vs_spec": {"spec": str(SPEC.relative_to(K2)), "sha16": s16(SPEC),
                                "intent_project_mismatch": spec_vs,
                                "map": {k: [p for p, _ in v] for k, v in NC_SPEC_MAP.items()}},
           "netclass_reference": {"file": "k2_v4_8L.kicad_pro", "sha16": s16(INTENT_PRO),
                                  "note": "模板 %s 豁免网类检查（只承载规则）" % TEMPLATE_EXEMPT},
           "redline": "只读；不改任何工件；阈值取自红线规则源，不放宽。"}
    OUT.write_text(json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"verdict": rec["verdict"], "files": len(rows), "violations": bad,
                      "teeth_ok": teeth, "record": s16(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
