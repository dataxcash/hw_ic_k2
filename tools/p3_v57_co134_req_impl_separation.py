#!/usr/bin/env python3
"""CO-134：【L2 自裁 · 需求/实现分家】③ 重新定性 = 工程换算错误（撤回 owner 升级）+ 忠实实现 + 规矩入库。

整改通知 #09：
  需求（目的）= R3-2「3W 原则」：对间中心距 ≥ 3×线宽 w（对间不串扰）。
  0.875 = 工程换算定值，且按**错误线宽**（0.4375）算得 ⇒ **工程问题，非需求变更** ⇒ 不作 owner 决策项。
本件：
  A. 立「需求/实现分家」规矩（新件 v1.0）：需求（目的/原则）冻结；实现（定值/几何/派生）在工程内迭代；
     任何工程定值须记录「来源原则 + 派生式 + 可达性」。
  B. 派生值台账 `derived_value_ledger_v1.json`：REQ-R3-2 + 忠实实现（铜边 ≥ 2w / 中心 ≥ 3w，按层）+ 可达性（闭式）
     + 0.875 退役留存（legacy 换算，非忠实实现）。
  C. SPEC rev-18 → **rev-19**：`net_classes.PCIe85.inter_pair_spacing_mm` 0.875 → **0.410**（= 2×0.205 外层，最严层）
     + `inter_pair_derivation_v1`（原则/派生式/按层/口径）+ 0.875 退役留存块；位白名单外零改动。
  D. 交付板**板实实测**（pcbnew，零搜索）：逐层对间铜边最小净空 + 位置 + 逃逸域归属 ⇒ 偏差显式登记（不静默）。
只读除 SPEC_L2/台账/规矩件；**不动几何/板/冻结四源**。CLI: ../AppDir/usr/bin/python3.11 <此文件>
"""
from __future__ import annotations
import hashlib, json, math, re, sys
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L2 = K2 / "pm_gate/artifacts/k2_v4/L2"
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP2 = L3 / "mcio_feas_step2"
SPEC_IN = L3 / "SPEC_k2_v4.spec-rev-18.json"
SPEC_OUT = L3 / "SPEC_k2_v4.spec-rev-19.json"
RULE = L2 / "REQUIREMENT_IMPLEMENTATION_SEPARATION_v1.0.md"
LEDGER = L2 / "derived_value_ledger_v1.json"
REC = STEP2 / "m13_v57_co134_req_impl_separation.json"
CARD = STEP2 / "m13_v57_CO134_req_impl_separation.md"
BOARD = K2 / "k2_v4_8L.l4.kicad_pcb"
CO37 = STEP2 / "m13_v57_co37_escape_domain.json"
CO129 = STEP2 / "m13_v57_co129_threshold_selfproof.json"
LEGACY = 0.875


def s16(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def d_pt_seg(px, py, sx, sy, ex, ey):
    vx, vy, wx, wy = ex - sx, ey - sy, px - sx, py - sy
    L2v = vx * vx + vy * vy
    t = 0.0 if L2v == 0 else max(0.0, min(1.0, (wx * vx + wy * vy) / L2v))
    return math.hypot(px - (sx + t * vx), py - (sy + t * vy))


def d_seg_seg(ax, ay, bx, by, cx, cy, dx, dy):
    rx, ry, sx, sy = bx - ax, by - ay, dx - cx, dy - cy
    den = rx * sy - ry * sx
    if abs(den) > 1e-12:
        t = ((cx - ax) * sy - (cy - ay) * sx) / den
        u = ((cx - ax) * ry - (cy - ay) * rx) / den
        if 0 <= t <= 1 and 0 <= u <= 1:
            return 0.0
    return min(d_pt_seg(ax, ay, cx, cy, dx, dy), d_pt_seg(bx, by, cx, cy, dx, dy),
               d_pt_seg(cx, cy, ax, ay, bx, by), d_pt_seg(dx, dy, ax, ay, bx, by))


def stem(n):
    m = re.match(r"^(.*)_(P|N)(_\w+)?$", n)
    return (m.group(1) + (m.group(3) or "")) if m else None


def measure_asbuilt(rects):
    import pcbnew
    import collections
    b = pcbnew.LoadBoard(str(BOARD))
    segs = collections.defaultdict(list)
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK":
            continue
        s = stem(t.GetNetname())
        if not s:
            continue
        segs[b.GetLayerName(t.GetLayer())].append(
            (s, t.GetNetname(), pcbnew.ToMM(t.GetWidth()), pcbnew.ToMM(t.GetStart().x),
             pcbnew.ToMM(t.GetStart().y), pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y)))

    def in_dom(x, y):
        return any(x0 - 1e-9 <= x <= x1 + 1e-9 and y0 - 1e-9 <= y <= y1 + 1e-9
                   for _, x0, y0, x1, y1 in rects)

    out = {}
    for L, items in segs.items():
        best_all = best_out = None
        for i in range(len(items)):
            s1, n1, w1, ax, ay, bx, by = items[i]
            for j in range(i + 1, len(items)):
                s2, n2, w2, cx, cy, dx, dy = items[j]
                if s1 == s2:
                    continue
                d = d_seg_seg(ax, ay, bx, by, cx, cy, dx, dy) - w1 / 2 - w2 / 2
                loc = (round((ax + bx) / 2, 3), round((ay + by) / 2, 3))
                rec = (round(d, 4), n1, n2, loc, in_dom(*loc) or in_dom((cx + dx) / 2, (cy + dy) / 2))
                if best_all is None or d < best_all[0]:
                    best_all = rec
                if rec[4]:
                    continue
                if best_out is None or d < best_out[0]:
                    best_out = rec
        out[L] = {"all": best_all, "outside_escape": best_out}
    return out


def main() -> int:
    spec = json.loads(SPEC_IN.read_text(encoding="utf-8"))
    nc = spec["net_classes"]["PCIe85"]
    w_by_layer = dict(spec["impedance"]["width_mm_by_layer"])
    edge_by_layer = {L: round(2 * w, 4) for L, w in w_by_layer.items()}
    center_by_layer = {L: round(3 * w, 4) for L, w in w_by_layer.items()}
    edge_outer = round(2 * max(w_by_layer.values()), 4)      # 最严层（外层 0.205）
    co129 = json.loads(CO129.read_text(encoding="utf-8"))
    span_min = co129["self_proof_4"]["inputs"]["span_min_mm"]
    caps = {r["domain"]: r["pitch_cap_mm"] for r in co129["domain_caps"]}
    w_min = co129["impedance_resolution"]["w_min_mm"]
    req_pitch = round(span_min + edge_outer, 4)
    doms = []
    for did, cap in sorted(caps.items()):
        m = round(cap - req_pitch, 4)
        exempt = (did == "pad_field")
        doms.append({"id": did, "pitch_cap_mm": cap, "required_pitch_mm": req_pitch, "margin_mm": m,
                     "ok": bool(m >= 0) or exempt,
                     "regime": "ECN-001 escape_transition_zone 放宽（已声明，非该原则适用域）" if exempt else "R3-2 适用域"})
    reachable = all(d["ok"] for d in doms)

    rects = [(d["id"], *d["rect_mm"]) for d in json.loads(CO37.read_text(encoding="utf-8"))["domains"]]
    ab = measure_asbuilt(rects)
    ab_rows, devs = [], []
    for L in sorted(ab):
        req = edge_by_layer.get(L)
        for key, r in ab[L].items():
            if r is None:
                continue
            d, n1, n2, loc, inesc = r
            row = {"layer": L, "scope": key, "min_edge_mm": d, "pairs": [n1, n2], "at": list(loc),
                   "inside_escape_xy": inesc, "required_edge_mm": req,
                   "margin_mm": round(d - req, 4), "ok": bool(d >= req - 1e-9)}
            ab_rows.append(row)
            if key == "outside_escape" and not row["ok"]:
                devs.append({"layer": L, "min_edge_mm": d, "required_edge_mm": req, "margin_mm": row["margin_mm"],
                             "pairs": [n1, n2], "at": list(loc),
                             "disposition": "OPEN_ENGINEERING：域外实测低于忠实口径 ⇒ SI/板厂券复核（外部输入，CO-53/54）或后续几何迭代（须另开 CO）"})

    legacy_why = (f"legacy 换算定值：{LEGACY} = 2×0.4375（等价 5×0.175 线距）；本板 w_by_layer={w_by_layer} "
                  f"与带内 w_min={w_min} 均无 0.4375 ⇒ 非 REQ-R3-2 的忠实实现")
    ledger = {
        "schema": 1, "artifact": "derived_value_ledger_v1",
        "rule_doc": {"path": str(RULE.relative_to(K2)), "sha16": s16(RULE) if RULE.exists() else None},
        "requirements": [
            {"id": "REQ-R3-2", "statement": "对间不串扰 ⇒ R3-2「3W 原则」：对间中心距 ≥ 3×线宽 w（对间铜边 ≥ 2×w）",
             "source_principle_ref": "_shared/docs/PCB_DESIGN_RULES.md R3-2（目的=对间串扰控制）",
             "frozen": True}
        ],
        "derived_values": [
            {"id": "DV-INTPAIR-EDGE", "requirement": "REQ-R3-2",
             "form": "edge_min(layer) = 2×w(layer)　⇔　center_min(layer) = 3×w(layer)",
             "inputs": {"w_by_layer": w_by_layer, "w_source": "SPEC impedance.width_mm_by_layer",
                        "span_min_mm": span_min, "band_w_min_mm": w_min},
             "computed": {"edge_by_layer_mm": edge_by_layer, "center_by_layer_mm": center_by_layer,
                          "edge_outer_binding_mm": edge_outer, "band_edge_min_mm": round(2 * w_min, 4)},
             "reachability": {"predicate": "∃ 设计：pitch_cap(域) ≥ span_min + edge_outer",
                              "domains": doms, "verdict": "REACHABLE" if reachable else "UNREACHABLE"},
             "supersedes": {"value": LEGACY, "kind": "LEGACY_DERIVED", "why": legacy_why}},
            {"id": "DV-ENGINE-INT_PAIR_PITCH", "requirement": "REQ-R3-2",
             "form": "capacity/新布线 对中心距（工程保守实现，本件不改几何）",
             "inputs": {"span_mm": 0.585, "w_outer_mm": 0.205},
             "computed": {"value_mm": 1.46, "faithful_min_mm": round(0.585 + edge_outer, 4)},
             "reachability": {"predicate": "value ≥ span + edge_min(外层)", "verdict": "CONSERVATIVE_OK"},
             "note": "route_model_config.capacity_audit.inter_pair_spacing；≥ 忠实下界 ⇒ 保守（安全）；几何口径不动"}
        ],
        "as_built": {"source": f"L4 board {s16(BOARD)}（CO-134 实测，零搜索）", "rows": ab_rows,
                     "deviations_open_engineering": devs,
                     "note": "域外实测对间铜边 vs 忠实口径（逐层）；域内（ECN-001 escape 域）适用声明放宽 0.075"},
        "separation_rules": {
            "R1": "需求（目的/原则）冻结：只可被 owner 变更",
            "R2": "实现（定值/几何/派生）在工程内迭代，无需 owner",
            "R3": "任何工程定值必须记录：来源原则 id + 派生式 + 输入 + 可达性（闭式）",
            "R4": "派生值不得作为需求冻结；需求条目不得携带定值（conflation 即 FAIL）",
            "R5": "机判：tools/p3_v57_co124_input_selfcheck_gate.py K9（+ 负控 T5/T6/T7）"},
        "verdict": "PASS" if reachable else "FAIL",
    }
    LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    rule_md = f"""# L2 规矩：需求 / 实现分家（v1.0）

> 立件缘起：整改通知 #09 —— ③「0.875 对间铜边净空不可达」被误升 owner；根因 = 把**工程换算定值**当**需求**冻结
> （需求 = R3-2「3W 原则」= 对间不串扰；0.875 = 按错误线宽 0.4375 的换算结果）。

## §1 规矩
- **R1 需求冻结**：需求 = 目的/原则（如 R3-2 3W：对间中心距 ≥ 3×线宽）。只可 owner 变更。
- **R2 实现迭代**：实现 = 定值/几何/派生式。在工程内自裁迭代（L2），**不得升 owner**。
- **R3 定值溯源**：任何工程定值必须记录 ① 来源原则 id ② 派生式 ③ 输入 ④ 可达性（闭式/确定性）。
- **R4 禁止混同**：派生值不得作为需求冻结；需求条目不得携带定值。
- **R5 机判**：`tools/p3_v57_co124_input_selfcheck_gate.py` **K9**（+ 负控 T5/T6/T7）逐条校验本件台账。

## §2 本板需求
| id | 需求（目的/原则） | 来源 | 冻结 |
|---|---|---|---|
| `REQ-R3-2` | 对间不串扰 ⇒ **3W 原则**：对间中心距 ≥ 3×线宽 w | `_shared/docs/PCB_DESIGN_RULES.md` R3-2（目的层） | 是 |

## §3 本板实现（派生值，工程内迭代）
台账（机读、逐值可溯）：`L2/derived_value_ledger_v1.json` → `derived_values[]`。
- `DV-INTPAIR-EDGE`：**edge_min(layer) = 2×w(layer)**（⇔ center ≥ 3w）。按层：外层 0.410 / 内层 0.320；
  带内下界（w_min={w_min}）⇒ {round(2*w_min,4)}（可行性用最有利界）。
- `DV-ENGINE-INT_PAIR_PITCH`：容量/新布线对中心距 1.46（= 0.585 + 0.875 的旧口径；本件保留为**保守实现**，≥ 忠实下界
  {round(0.585+edge_outer,4)}）——几何口径不动。

## §4 被取代的定值（退役留存，不销毁）
| 值 | 来源 | 为何非忠实实现 |
|---|---|---|
| `0.875` | R3-2 旧换算（`_shared/docs/PCB_DESIGN_RULES.md` 表内定值「5×线距」/ 2×0.4375） | {legacy_why} |

## §5 可达性与板实
- **可达性（闭式）**：{'REACHABLE' if reachable else 'UNREACHABLE'} —— 域外：pitch_cap {span_min}+{edge_outer}={req_pitch}；
  WEST {caps.get('WEST_MCIO_TO_CHIP')} ✓ / EAST {caps.get('EAST_CHIP_TO_J2')} ✓；焊盘场（cap {caps.get('pad_field')}）属
  **ECN-001 escape_transition_zone**（已声明放宽 0.075）⇒ 非该原则适用域。
- **板实（实测，见 CO-134 记录 `as_built`）**：域外偏差 {len(devs)} 处（显式登记为工程开放项，路由 = SI/板厂券 或后续几何迭代）。
"""
    RULE.write_text(rule_md, encoding="utf-8")

    # ---- SPEC rev-19（白名单外零改动）----
    new = json.loads(SPEC_IN.read_text(encoding="utf-8"))
    new["spec_version"] = "1.1.spec-rev-19"
    n19 = new["net_classes"]["PCIe85"]
    n19["inter_pair_spacing_mm"] = edge_outer
    n19["inter_pair_derivation_v1"] = {
        "requirement_id": "REQ-R3-2",
        "requirement": "对间不串扰 ⇒ 3W 原则：对间中心距 ≥ 3×线宽 w",
        "implementation_form": "对间铜边净空 ≥ 2×w（⇔ 中心距 ≥ 3×w）；w = 该对在该层的线宽",
        "by_layer_edge_mm": edge_by_layer, "by_layer_center_mm": center_by_layer,
        "w_source": "impedance.width_mm_by_layer", "binding_outer_mm": edge_outer,
        "band_edge_min_mm": round(2 * w_min, 4),
        "scope": "域外对间长平行；域内（SPEC constraints.escape_transition_zone，ECN-001）按声明放宽 0.075",
        "ledger_ref": "L2/derived_value_ledger_v1.json DV-INTPAIR-EDGE",
        "separation_rule_ref": "L2/REQUIREMENT_IMPLEMENTATION_SEPARATION_v1.0.md",
    }
    n19["inter_pair_spacing_scope"] = (
        f"{edge_outer} = REQ-R3-2（3W 原则）的忠实实现定值（外层 w=0.205 ⇒ 2w=0.410；内层 w=0.16 ⇒ 0.320，见 "
        "inter_pair_derivation_v1）。旧 0.875 为 legacy 换算（=2×0.4375），已退役留存。as-built 走廊轨距 1.20（CO-10）⇒ "
        "交付对间最小铜边实测见 CO-134 as_built；对间串扰终判 = 领域求解器/板厂券（CO-53/CO-54）。")
    new["retired_inter_pair_spacing_0p875_v1"] = {
        "value": LEGACY, "kind": "LEGACY_DERIVED", "why": legacy_why,
        "replaced_by": "net_classes.PCIe85.inter_pair_derivation_v1（CO-134，rev-19）",
        "note": "退役留存（红线：退役决策须显式留存，不销毁）"}
    # 白名单校验
    a, b = json.loads(SPEC_IN.read_text(encoding="utf-8")), new
    allow = {"/spec_version", "/net_classes/PCIe85/inter_pair_spacing_mm", "/net_classes/PCIe85/inter_pair_derivation_v1",
             "/net_classes/PCIe85/inter_pair_spacing_scope", "/retired_inter_pair_spacing_0p875_v1"}

    def diff(p, x, y, out):
        if type(x) is not type(y):
            out.add(p); return
        if isinstance(x, dict):
            for k in set(x) | set(y):
                if k not in x or k not in y: out.add((p + "/" + k).replace("//", "/"))
                else: diff(p + "/" + k, x[k], y[k], out)
        elif isinstance(x, list):
            if x != y: out.add(p)
        elif x != y:
            out.add(p)
    dd = set(); diff("", a, b, dd)
    unexpected = sorted(p for p in dd if p not in allow)
    assert not unexpected, f"CO-134 SPEC 白名单外改动: {unexpected}"
    SPEC_OUT.write_text(json.dumps(b, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    rec = {"artifact": "m13_v57_co134_req_impl_separation", "schema": 1, "revision": "CO-134",
           "nature": "L2 自裁（需求/实现分家）：③ 重新定性 = 工程换算错误（撤回 owner 升级）+ REQ-R3-2 忠实实现 + 规矩入库",
           "redline": "零坐标搜索；不动几何/板；冻结四源不动；派生值全部可机判溯源",
           "remove_owner_escalation": {"item": "③ 对间铜边净空 0.875", "prior": "co129 §4 自证 + P1/P2 提案（待 owner 批准）",
                                       "now": "工程问题（非需求）：0.875 = legacy 换算（错误线宽 0.4375）⇒ 忠实实现 = 2×w（按层）",
                                       "owner_decision_required": False,
                                       "p1_adopted": "P1（3W 原义：铜边 ≥ 2·w）作为**工程实现**落地（无需 owner 批准）",
                                       "p2_not_needed": True},
           "inputs": {"spec_in": s16(SPEC_IN), "board": s16(BOARD), "co129": s16(CO129), "co37": s16(CO37)},
           "outputs": {"spec_out": s16(SPEC_OUT), "ledger": s16(LEDGER), "rule_doc": s16(RULE)},
           "faithful_derivation": {"edge_by_layer_mm": edge_by_layer, "center_by_layer_mm": center_by_layer,
                                   "binding_outer_mm": edge_outer, "band_edge_min_mm": round(2 * w_min, 4),
                                   "legacy_retired": LEGACY, "why": legacy_why},
           "reachability": {"domains": doms, "verdict": "REACHABLE" if reachable else "UNREACHABLE"},
           "as_built": ledger["as_built"],
           "spec_change_whitelist": sorted(dd), "unexpected_changes": unexpected,
           "verdict": "PASS" if (reachable and not unexpected) else "FAIL"}
    REC.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    card = f"""# CO-134（L2 自裁 · 需求/实现分家）：③ = 工程换算错误；REQ-R3-2 忠实实现

- **撤回 owner 升级**：③ 定性 = 工程问题（0.875 = legacy 换算，按错误线宽 0.4375）⇒ 不作 owner 决策项。
- **忠实实现**（REQ-R3-2「3W 原则」= 对间中心距 ≥ 3×线宽）：**edge_min(layer) = 2×w(layer)** ⇒ 外层 {edge_outer} / 内层 0.320；
  带内下界 {round(2*w_min,4)}；旧 0.875 退役留存。SPEC **rev-19** `{s16(SPEC_OUT)}`（白名单外 0 改动）。
- **可达性**：{'REACHABLE' if reachable else 'UNREACHABLE'} —— 域外 {span_min}+{edge_outer}={req_pitch} ≤ cap（WEST {caps.get('WEST_MCIO_TO_CHIP')} / EAST {caps.get('EAST_CHIP_TO_J2')}）；
  焊盘场属 ECN-001 escape 域（已声明放宽）。
- **板实实测**：域外偏差 **{len(devs)}** 处（见记录 `as_built`；显式登记为工程开放项，路由 = SI/板厂券 或后续几何迭代）。
- **规矩入库**：`L2/REQUIREMENT_IMPLEMENTATION_SEPARATION_v1.0.md` `{s16(RULE)}` + 台账 `L2/derived_value_ledger_v1.json` `{s16(LEDGER)}`；
  机判 = co124 **K9**（负控 T5/T6/T7）。
"""
    CARD.write_text(card, encoding="utf-8")
    print("CO-134 verdict=%s | SPEC rev-19 %s | edge_by_layer %s | reachable=%s | as-built devs=%d"
          % (rec["verdict"], s16(SPEC_OUT), edge_by_layer, reachable, len(devs)))
    print("devs:", json.dumps(devs, ensure_ascii=False))
    return 0 if rec["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
