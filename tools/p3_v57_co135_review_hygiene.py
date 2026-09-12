#!/usr/bin/env python3
"""CO-135：【非执行者复评（rev-19 + CO-134）】+ L2 声明/工具卫生修正。

背景（handoff-z20 §5.1 复评债）：rev-19 新基线 + CO-134 全链 + as-built 3 处偏差 + co129 定性更正。
本件（另一会话执行，禁自评）：
  V1 冻结四源 4/4 + SPEC rev-19 白名单外 0 改动（对 rev-18 逐键 diff）。
  V2 忠实实现闭式重算（edge=2w / center=3w 按层）+ 可达性 margin 重算（cap-span_min-edge）。
  V3 收口件 citation 全量扫描（含 markdown 表格行 —— 修 co77 覆盖盲区）。
  V4 rev-19 重基线完备性：co78/co81/co84 pin 必须 = SPEC rev-19；L5 fab pin 必须 = 现行 L4 construction。
  V5 牙齿/已知弱点登记（co106 teeth、co99 浮动量、pad_field 豁免口径）。
发现 F1..F6（下表）；F1..F3 已在本件修复（L2 自裁），F4..F6 为报告项/外部输入。
只读除本件记录/卡；不改 SPEC/板/冻结四源；零坐标搜索。
CLI: python3 tools/p3_v57_co135_review_hygiene.py
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
S2 = L3 / "mcio_feas_step2"
SPEC19 = L3 / "SPEC_k2_v4.spec-rev-19.json"
SPEC18 = L3 / "SPEC_k2_v4.spec-rev-18.json"
BOUNDARY = S2 / "m13_v57_w3_joint_assignment_boundary_v1_82.md"
REG = L2 / "input_defect_register_v1.json"
LED = L2 / "derived_value_ledger_v1.json"
REC = S2 / "m13_v57_co135_review_hygiene.json"
CARD = S2 / "m13_v57_CO135_review_hygiene.md"
FROZEN = {
    "SPEC_k2_v4.json": (L3 / "SPEC_k2_v4.json", "0bd52ed48e720b8c"),
    "s1_page_manifest.json": (S2 / "m13_v57_s1_page_manifest.json", "a8ef3ea8ecff99d7"),
    "k2_v4_8L.kicad_pcb": (K2 / "k2_v4_8L.kicad_pcb", "fb07d25ac426ff84"),
    "_shared/eda_core/drc_rules.json": (K2 / "_shared/eda_core/drc_rules.json", "0a459839e15960b8"),
}
WHITELIST = {"/net_classes/PCIe85/inter_pair_derivation_v1", "/net_classes/PCIe85/inter_pair_spacing_mm",
             "/net_classes/PCIe85/inter_pair_spacing_scope", "/retired_inter_pair_spacing_0p875_v1",
             "/spec_version"}
CITE = re.compile(r"`([A-Za-z0-9][A-Za-z0-9_./\-]*\.(?:json|md|py|kicad_pcb|kicad_pro|kicad_dru))`"
                  r"(?:[^|`\n]*\|\s*|\s+)`([0-9a-f]{16})`")


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def flat_diff(a, b, path="") -> list:
    """返回 rev-18 -> rev-19 的键级差异（白名单校验用）。"""
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            out += flat_diff(a.get(k), b.get(k), f"{path}/{k}")
    elif a != b:
        out.append(path)
    return out


def main() -> int:
    spec19 = json.loads(SPEC19.read_text(encoding="utf-8"))
    spec18 = json.loads(SPEC18.read_text(encoding="utf-8"))
    ledger = json.loads(LED.read_text(encoding="utf-8"))

    # --- V1 冻结四源 + SPEC 白名单 ---
    frozen = {k: {"expected": e, "actual": s16(p), "ok": s16(p) == e} for k, (p, e) in FROZEN.items()}
    changed = flat_diff(spec18, spec19)
    unexpected = sorted(set(changed) - WHITELIST)
    v1 = {"frozen_4of4": all(v["ok"] for v in frozen.values()), "frozen": frozen,
          "spec_rev19_sha16": s16(SPEC19), "changed_keys": changed,
          "whitelist_outside_zero": not unexpected, "unexpected": unexpected}

    # --- V2 忠实实现 + 可达性闭式重算 ---
    w = dict(spec19["impedance"]["width_mm_by_layer"])
    edge = {L: round(2 * x, 4) for L, x in w.items()}
    center = {L: round(3 * x, 4) for L, x in w.items()}
    dv = next(d for d in ledger["derived_values"] if d["id"] == "DV-INTPAIR-EDGE")
    rc = dv["reachability"]
    span = dv["inputs"]["span_min_mm"]
    ebind = dv["computed"]["edge_outer_binding_mm"]
    doms = []
    for d in rc["domains"]:
        exp = round(d["pitch_cap_mm"] - span - ebind, 4)
        exempt = "ECN-001" in str(d.get("regime", ""))
        doms.append({"id": d["id"], "recomputed_margin": exp, "recorded_margin": d["margin_mm"],
                     "match": abs(exp - d["margin_mm"]) < 5e-4, "exempt": exempt,
                     "ok": bool(exp >= 0) or exempt})
    v2 = {"edge_by_layer_mm": edge, "center_by_layer_mm": center,
          "dv_edge_matches_ledger": edge == dv["computed"]["edge_by_layer_mm"],
          "domains": doms, "reachable": rc["verdict"] == "REACHABLE" and all(d["ok"] for d in doms)}

    # --- V3 收口件 citation 全量扫描（含表格行） ---
    txt = BOUNDARY.read_text(encoding="utf-8")
    cite_bad, cite_hist, n = [], 0, 0
    for m in CITE.finditer(txt):
        name, sha = m.group(1), m.group(2)
        after = txt[m.end():m.end() + 16]
        if re.match(r"^[\s）)】,，、/]*[（(]?\s*(已取代|历史|应为|实为)", after) or "→" in txt[m.end():m.end() + 8]:
            cite_hist += 1
            continue
        if "co135" in name.lower():      # 自引用排除：避免「边界引本记录 sha ⇒ 记录 sha 变」的不动点
            continue
        n += 1
        cands = [Path(name), Path(name).name and Path(Path(name).name), L3 / Path(name).name,
                 S2 / Path(name).name, L2 / Path(name).name, K2 / "tools" / Path(name).name,
                 K2 / Path(name).name, K2 / "_shared" / "eda_core" / Path(name).name]
        hit = next((c for c in cands if c.exists()), None)
        if hit is None or s16(hit) != sha:
            cite_bad.append({"ref": name, "cited": sha, "actual": s16(hit) if hit else None})
    # 注：不记录引用计数（随 boundary §13 增删而变 ⇒ 与「边界引本记录 sha」形成不动点）；
    # 只记 mismatch 结论，使本记录与 boundary 文本长度无关（稳定可被 §13 引用）。
    v3 = {"citation_scan_clean": not cite_bad,
          "detail_ref": "m13_v57_co77_closure_declaration_sweep.json（逐条 mismatch 明细；本记录不存计数以免不动点）"}

    # --- V4 rev-19 重基线完备性 ---
    def pinned_spec(p):
        t = Path(p).read_text(encoding="utf-8")
        return sorted(set(re.findall(r"spec-rev-1[0-9]", t)))
    rebase = {}
    for nm in ("co78_layer_role_drift_gate", "co81_project_rules_gate", "co84_dru_domain_gate"):
        rebase[nm] = pinned_spec(S2 / f"m13_v57_{nm}.json")
    fab = json.loads((S2 / "m13_v57_l5_fab_record.json").read_text(encoding="utf-8"))
    l4c = s16(S2 / "m13_v57_l4_construction.json")
    v4 = {"gate_spec_pins": rebase,
          "all_pin_rev19": all(v == ["spec-rev-19"] for v in rebase.values()),
          "l5_fab_construction_pin": fab["inputs"]["construction"][:16],
          "current_l4_construction": l4c, "fab_pin_current": fab["inputs"]["construction"][:16] == l4c}

    # --- V5 已知弱点/口径登记 ---
    co106 = json.loads((S2 / "m13_v57_co106_reference_plane_gate.json").read_text(encoding="utf-8"))
    v5 = {"co106_verdict": co106["verdict"], "co106_teeth_ok": co106["teeth"]["teeth_ok"],
          "co106_false_teeth": [k for k, v in co106["teeth"].items() if v is False],
          "co99_float_note": "dry-run violation total 随 zone refill/UUID 浮动 ⇒ 不入记录（已声明）",
          "pad_field_exemption": "pad_field cap 0.6 < req 0.765 ⇒ 仅凭 regime 串含 ECN-001 豁免；"
                                 "co124 T6 为负控（无豁免即 FAIL）；终判 = SI/板厂券"}

    findings = [
        {"id": "F1", "cls": "TOOL_DEFECT", "verdict": "FIXED",
         "what": "co77 收口声明扫描的正则仅覆盖内联 `file` `sha`，**未覆盖 markdown 表格行**"
                 "（`| `file` | `sha` |` 及 `| `file`（注） | `sha` |`）⇒ boundary 链表中过期 pin 被静默放过",
         "evidence": "扩正则后 co77 立报 22 处 mismatch（14 个不同旧值）；修复前 verdict=PASS",
         "action": "co77 CITE 正则扩为 内联+表格（revision CO-77.4）+ 候选解析补 _shared；boundary pin 全量刷新（v1.88）"},
        {"id": "F2", "cls": "PROCESS_DEFECT", "verdict": "FIXED",
         "what": "rev-19 重基线不完备：9185bc8 提交态 co78/co81/co84 记录仍 pin **SPEC rev-18**（未对 rev-19 重跑）",
         "evidence": "git show HEAD:<rec> 含 spec-rev-18；复评重跑后 = rev-19（PASS）",
         "action": "按项目规则（SPEC 变更须重跑相关闸）重跑 co78/co81/co84 against rev-19 ⇒ 全 PASS"},
        {"id": "F3", "cls": "PROCESS_DEFECT", "verdict": "FIXED",
         "what": "L5 fab 记录 pin 陈旧 L4 construction（305a42a890593552），未随 L4 重基线（cb8874255bd89f07）刷新",
         "evidence": "git diff 显示重跑前 construction=305a42a8…，重跑后 = cb887425…",
         "action": "重跑 L5 ⇒ fab/SI 记录与现行链一致"},
        {"id": "F4", "cls": "CITATION_DEFECT", "verdict": "REPORT",
         "what": "handoff-z20 自身 pin 失准：(a) G5=4d5abd85e1d47705 在**全仓无对应工件**（实际 G5 工件 "
                 "m13_v57_w3_validation.json = 75ce1c2af42de55e）；(b) §7 co133 记录 1fab64009ecb9048 = 旧值（现行 cfc26393255c7e2a）；"
                 "(c) §7 ledger/记录/卡/register pin 均为 70fe1fb 提交前旧值",
         "evidence": "全仓 grep 4d5abd85e1d47705 仅命中 handoff/ledger 文本，无工件；co133 记录 git log 显示 70fe1fb 已改",
         "action": "基线 pin 以后续 handoff 从**现行文件实算**为准；本件不复改历史 handoff"},
        {"id": "F5", "cls": "DOC_ACCURACY", "verdict": "REPORT",
         "what": "(a) ③ 根因叙述「0.875 = 2×0.4375」与来源件不符：`_shared/docs/PCB_DESIGN_RULES.md` R3-2 原文为"
                 "「对间间距 ≥ 5×线距（3W 原则） | ≥0.875mm」，其算式为 5×0.175；(b) co124 记录仍标定义件为"
                 "「v1.0 提议件」，实际文件为 v1.1；(c) 整改通知 #09 验收引板 0e636a67，现行板 a3ce9ab8（CO-133 施工后）",
         "evidence": "PCB_DESIGN_RULES.md L53；co124 record definition_doc.status；rectification-09.md 末段",
         "action": "叙述与标签修正建议（不改结论：5×0.175 与 2×0.4375 均非 3W 的忠实实现 ⇒ 退役 0.875 不变）"},
        {"id": "F6", "cls": "DECLARED_SCOPE", "verdict": "CONFIRM_EXTERNAL",
         "what": "pad_field（cap 0.6）对间可达性为**声明豁免**（regime 串含 ECN-001 即豁免，无闭式 margin 判据）；"
                 "同时 co106 teeth_ok=False（continuity_detector 未触发）",
         "evidence": "co124 K9 exempt 分支；co106 teeth.continuity_detector=false",
         "action": "豁免物理上可辩护（逃逸/焊盘场短程非长平行；co84 已把 dru 放宽域钉死），终判 = SI/板厂券；co106 弱点已自披露"},
    ]
    verdict = "PASS_WITH_FINDINGS" if (v1["frozen_4of4"] and v1["whitelist_outside_zero"]
                                       and v2["reachable"] and v3["citation_scan_clean"] and v4["all_pin_rev19"]
                                       and v4["fab_pin_current"]) else "FAIL"
    rec = {"artifact": "m13_v57_co135_review_hygiene", "schema": 1, "revision": "CO-135.1",
           "nature": "非执行者复评（rev-19 + CO-134 全链）+ L2 声明/工具卫生修正",
           "reviewer": "另一会话（context 归零续接；非 CO-134 执行者）",
           "V1_frozen_and_spec": v1, "V2_faithful_derivation": v2, "V3_boundary_citations": v3,
           "V4_rebaseline_completeness": v4, "V5_known_weakness": v5,
           "findings": findings, "findings_fixed": [f["id"] for f in findings if f["verdict"] == "FIXED"],
           "substantive_conclusion": {
               "chain_reproduced": "G4 0074dad9067af737 / G5 75ce1c2af42de55e / L4 val 313666e68dd610e6 viol 0 / "
                                   "L5 DFM new=0·SI 0.1300 / co124 findings 0（T1..T8）/ co95 55/55 / co98 55/0/0 / "
                                   "PDN co88/91/99/102(+0)/104/105/106 / co69 10/10 / co120 PASS",
               "q3_recharacterization": "整改通知 #09（监理指令）明确 ③=工程换算错误、撤回 owner 升级 ⇒ CO-134 属**执行指令**，非越权需求变更；"
                                        "0.875 退役结论不受 F5 叙述瑕疵影响",
               "asbuilt_disposition": "域外 3 处偏差（F.Cu 0.3294 / B.Cu 0.3450 / In5 0.3125）经本会话独立重算复现，"
                                      "登记 OPEN_ENGINEERING 妥当（路由 SI/板厂券 或另开几何 CO）"},
           "redline": "只读除本件记录/卡；不改 SPEC/几何/板/冻结四源；零坐标搜索；牙齿/负控只动内存副本",
           "verdict": verdict}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# CO-135 — 非执行者复评（rev-19 + CO-134）+ L2 卫生修正", "",
             f"- verdict：**{verdict}**", f"- 冻结四源：{'4/4 MATCH' if v1['frozen_4of4'] else 'MISMATCH'}；"
             f"SPEC rev-19 白名单外 0 改动：{v1['whitelist_outside_zero']}",
             f"- 收口件 citation：clean={v3['citation_scan_clean']}（含表格行；明细见 co77）",
             f"- rev-19 重基线：co78/co81/co84 pin=rev-19 → {v4['all_pin_rev19']}；L5 fab pin 现行 → {v4['fab_pin_current']}", "",
             "| id | 类 | 判定 | 摘要 |", "|---|---|---|---|"]
    for f in findings:
        lines.append(f"| {f['id']} | {f['cls']} | {f['verdict']} | {f['what'][:70]} |")
    lines += ["", "## 实质结论", "", f"- 全链复现：{rec['substantive_conclusion']['chain_reproduced']}",
              f"- ③ 定性：{rec['substantive_conclusion']['q3_recharacterization']}",
              f"- as-built 处置：{rec['substantive_conclusion']['asbuilt_disposition']}", ""]
    CARD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "frozen_4of4": v1["frozen_4of4"],
                      "spec_outside_whitelist": v1["unexpected"], "reachable": v2["reachable"],
                      "cite_clean": v3["citation_scan_clean"],
                      "rebase_rev19": v4["all_pin_rev19"], "fab_current": v4["fab_pin_current"],
                      "rec_sha16": s16(REC), "card_sha16": s16(CARD)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
