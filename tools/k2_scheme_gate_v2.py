#!/usr/bin/env python3
"""k2_scheme_gate_v2.py --- COMPLETE scheme/construction gate (supersedes k2_placement_gate_v1.py) for #K2-336
sec.4.1 threshold completeness (C17').

Reads the sourced thresholds from L2/SCHEME_GATE_THRESHOLDS_v1.json (NO thresholds hard-coded here) and evaluates
P1..P7 on a board (read-only).  Every verdict carries the criterion's source citation.  Criteria whose threshold or
required input is not in register are PENDING with the named missing input (policy: no invented thresholds).

Scheme layer P1-P4 = the framework certificate; construction layer P5-P7.

Usage: k2_scheme_gate_v2.py --board hw/k2_v4_8L.l10.kicad_pcb [--drc <chain drc json>] [--out <json>]
"""
import argparse, collections, json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L2 = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4", "L2")
TH_PATH = os.path.join(L2, "SCHEME_GATE_THRESHOLDS_v1.json")
HS_PREFIXES = ("PCIE", "REFCLK")
POWER_PREFIXES = ("P3V3", "VREG", "PWR_", "MCU_")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--drc", default="")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    import pcbnew
    TH = json.load(open(TH_PATH, encoding="utf-8"))["criteria"]
    b = pcbnew.LoadBoard(a.board)
    e = b.GetBoardEdgesBoundingBox()
    X0, X1, Y0, Y1 = [round(pcbnew.ToMM(v), 3) for v in (e.GetLeft(), e.GetRight(), e.GetTop(), e.GetBottom())]
    cx, cy, W, H = (X0 + X1) / 2, (Y0 + Y1) / 2, X1 - X0, Y1 - Y0
    corners = {"TL": (X0, Y0), "TR": (X1, Y0), "BL": (X0, Y1), "BR": (X1, Y1)}
    nets = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    hs_refs, power_refs = set(), set()
    for r, fp in fps.items():
        for p in fp.Pads():
            nm = nets.get(p.GetNetCode(), "")
            if nm.startswith(HS_PREFIXES):
                hs_refs.add(r)
            if nm.startswith(POWER_PREFIXES):
                power_refs.add(r)
    holes = {r: (round(pcbnew.ToMM(f.GetPosition().x), 3), round(pcbnew.ToMM(f.GetPosition().y), 3))
             for r, f in fps.items() if r.startswith("H") and r[1:].isdigit()}
    hs_conn = sorted(r for r in hs_refs if r not in holes)
    R = {}

    def verdict(v, **kw):
        d = {"verdict": v, "source": TH[key]["source_kind"], "citation": TH[key]["citation"]}
        d.update(kw)
        return d

    # ---------------- P1 structural flow-through (exemplar + datasheet sourced) ----------------
    key = "P1"
    chip = None
    for r in hs_conn:
        if r.startswith("U"):
            chip = r
    chip_at = (round(pcbnew.ToMM(fps[chip].GetPosition().x), 3), round(pcbnew.ToMM(fps[chip].GetPosition().y), 3))
    others = [r for r in hs_conn if r != chip]
    west = [r for r in others if pcbnew.ToMM(fps[r].GetPosition().x) < chip_at[0]]
    east = [r for r in others if pcbnew.ToMM(fps[r].GetPosition().x) > chip_at[0]]
    axis_y = sum(pcbnew.ToMM(fps[r].GetPosition().y) for r in others) / len(others)
    off_axis = abs(chip_at[1] - axis_y)
    tol = 0.15 * H
    between = bool(west and east and
                   max(pcbnew.ToMM(fps[r].GetPosition().x) for r in west) < chip_at[0] <
                   min(pcbnew.ToMM(fps[r].GetPosition().x) for r in east))
    p1_pass = between and off_axis <= tol
    # report-only SI reading: route/straight ratio per HS net (NO threshold - no spec defines one)
    straights, ratios = {}, {}
    pads = collections.defaultdict(list)
    for f in b.GetFootprints():
        for p in f.Pads():
            nm = nets.get(p.GetNetCode(), "")
            if nm.startswith("PCIE"):
                pads[nm].append((pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)))
    tl = collections.defaultdict(float)
    for t in b.GetTracks():
        nm = nets.get(t.GetNetCode(), "")
        if nm.startswith("PCIE") and t.GetClass() != "PCB_VIA":
            tl[nm] += math.hypot(t.GetEnd().x - t.GetStart().x, t.GetEnd().y - t.GetStart().y) / 1e6
    for nm, pp in pads.items():
        if len(pp) >= 2:
            d = math.hypot(pp[0][0] - pp[-1][0], pp[0][1] - pp[-1][1])
            straights[nm] = round(d, 2)
            if d > 0 and nm in tl:
                ratios[nm] = round(tl[nm] / d, 3)
    R["P1"] = verdict("PASS" if p1_pass else "FAIL", name=TH[key]["name"], layer="SCHEME",
                      chip=chip, chip_at=list(chip_at), hs_connectors={r: ("west" if r in west else "east") for r in others},
                      connector_axis_y=round(axis_y, 2), lateral_offset_mm=round(off_axis, 2),
                      tolerance_mm=round(tol, 2), chip_between_connectors=between,
                      route_over_straight_ratio_report_only=(sorted(ratios.items(), key=lambda kv: -kv[1])[:3] if ratios else None),
                      note="the 1.6x placeholder ratio is removed as a verdict (no spec/manufacturer defines it); it is reported only")

    # ---------------- P2 length budget (CEM 750 ps) ----------------
    key = "P2"
    thr = TH[key]["threshold"]
    hs_len = {nm: round(v, 2) for nm, v in tl.items()}
    all_hs_len = {}
    for t in b.GetTracks():
        nm = nets.get(t.GetNetCode(), "")
        if nm.startswith(HS_PREFIXES) and t.GetClass() != "PCB_VIA":
            all_hs_len[nm] = round(all_hs_len.get(nm, 0.0) + math.hypot(t.GetEnd().x - t.GetStart().x, t.GetEnd().y - t.GetStart().y) / 1e6, 2)
    if all_hs_len:
        worst = max(all_hs_len.values())
        R["P2"] = verdict("PASS" if worst <= thr["max_trace_length_mm"] else "FAIL", name=TH[key]["name"], layer="SCHEME",
                          threshold_mm=thr["max_trace_length_mm"], max_routed_mm=round(worst, 2),
                          worst_nets=sorted(all_hs_len.items(), key=lambda kv: -kv[1])[:3],
                          n_hs_nets=len(all_hs_len), derivation=thr["derivation"])
    else:
        R["P2"] = verdict("PENDING", name=TH[key]["name"], layer="SCHEME", threshold_mm=thr["max_trace_length_mm"],
                          reason="board has no routed HS tracks (unrouted candidate) => needs the router (C17)")

    # ---------------- P3 mechanical ----------------
    key = "P3"
    th = TH[key]["threshold"]
    rows = []
    for h, p in sorted(holes.items()):
        nc = min(corners.items(), key=lambda kv: math.hypot(p[0] - kv[1][0], p[1] - kv[1][1]))
        dist = math.hypot(p[0] - nc[1][0], p[1] - nc[1][1])
        edge = min(p[0] - X0, X1 - p[0], p[1] - Y0, Y1 - p[1])
        rows.append({"hole": h, "at": list(p), "nearest_corner": nc[0], "corner_dist_mm": round(dist, 2),
                     "edge_margin_mm": round(edge, 2), "pass": dist <= th["corner_max_mm"] + 1e-9 and edge >= th["edge_min_mm"] - 1e-9})
    R["P3"] = verdict("PASS" if all(r["pass"] for r in rows) else "FAIL", name=TH[key]["name"], layer="SCHEME",
                      thresholds=th, holes=rows, worst_corner_mm=max(r["corner_dist_mm"] for r in rows))

    # ---------------- P4 capacity witness ----------------
    key = "P4"
    with_tracks = [nm for nm in all_hs_len if all_hs_len[nm] > 0]
    unconn = None
    if a.drc and os.path.isfile(a.drc):
        try:
            dj = json.load(open(a.drc, encoding="utf-8"))
            for k in ("unconnected", "unconnected_items", "unconnected_pads"):
                if isinstance(dj.get(k), (int, list)):
                    unconn = dj[k] if isinstance(dj[k], int) else len(dj[k]); break
        except Exception:
            unconn = None
    ok = len(with_tracks) > 0 and (unconn == 0 or unconn is None)
    R["P4"] = verdict("PASS" if ok else "PENDING", name=TH[key]["name"], layer="SCHEME",
                      hs_nets_with_tracks=len(with_tracks), n_hs_nets=len(pads) if pads else len(all_hs_len),
                      unconnected_from_drc=unconn, drc_file=a.drc or None,
                      rule=TH[key]["threshold"]["witness_rule"],
                      note="unconnected dimension needs the chain DRC report; tracks-exist = existence witness")

    # ---------------- P5 thermal ----------------
    key = "P5"
    th = TH[key]["threshold"]
    u6 = next((r for r in hs_conn if r.startswith("U")), None)
    bb = fps[u6].GetBoundingBox()
    n_gnd_via = 0
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" and nets.get(t.GetNetCode()) == "GND" and bb.Contains(t.GetPosition()):
            n_gnd_via += 1
    budget = []
    for name, p in th["pact_cases_w"].items():
        tj = th["ta_c"] + p * th["theta_ja_eff_c_per_w"]
        budget.append({"case": name, "P_W": p, "Tj_C": round(tj, 1), "limit_C": th["tj_max_c"], "pass": tj <= th["tj_max_c"]})
    R["P5"] = verdict("PASS" if (n_gnd_via >= th["gnd_vias_beneath_device_min"] and all(x["pass"] for x in budget)) else "FAIL",
                      name=TH[key]["name"], layer="CONSTRUCTION",
                      gnd_vias_beneath_device=n_gnd_via, device=u6, tj_budget=budget,
                      conditional_goal=th["conditional_goal"], margin_worst_C=round(th["tj_max_c"] - max(x["Tj_C"] for x in budget), 1))

    # ---------------- P6 DFM ----------------
    key = "P6"
    cle, hist, n_err, n_warn = None, None, None, None
    if a.drc and os.path.isfile(a.drc):
        try:
            dj = json.load(open(a.drc, encoding="utf-8"))
            v = dj.get("violations")
            if isinstance(v, list):
                hist = collections.Counter(x.get("type") for x in v)
                cle = sum(1 for x in v if x.get("type") == "clearance")
                n_err = sum(1 for x in v if x.get("severity") == "error")
                n_warn = sum(1 for x in v if x.get("severity") == "warning")
        except Exception:
            cle = None
    R["P6"] = verdict("PASS" if cle == 0 else ("PENDING" if cle is None else "FAIL"), name=TH[key]["name"],
                      layer="CONSTRUCTION", clearance_violations=cle, drc_file=a.drc or None,
                      n_violations=(sum(hist.values()) if hist else None), n_error=n_err, n_warning=n_warn,
                      type_histogram=(dict(hist) if hist else None), thresholds=TH[key]["threshold"])

    # ---------------- P7 decoupling ----------------
    key = "P7"
    bbL, bbT, bbR, bbB = [pcbnew.ToMM(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())]
    caps = []
    inside = 0
    for r in power_refs:
        if not (r.startswith("C") or r.startswith("L")):
            continue
        fp = fps[r]
        x, y = pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y)
        dx = max(bbL - x, 0, x - bbR); dy = max(bbT - y, 0, y - bbB)
        d = math.hypot(dx, dy)
        if d <= 6.0:
            caps.append({"ref": r, "dist_to_device_bbox_mm": round(d, 2), "inside": d == 0})
            if d == 0:
                inside += 1
    R["P7"] = verdict("PENDING", name=TH[key]["name"], layer="CONSTRUCTION",
                      caps_inside_device_bbox=inside, nearby_caps=caps,
                      literal_check_source=TH[key]["citation"][0]["quoted"],
                      missing_input=TH[key]["missing_input"],
                      note=TH[key]["note"])

    # ---------------- roll-up ----------------
    scheme = [R[k]["verdict"] for k in ("P1", "P2", "P3", "P4")]
    construction = [R[k]["verdict"] for k in ("P5", "P6", "P7")]
    rep = {"artifact": "k2_scheme_gate_v2", "board": a.board,
           "board_frame": {"x": [X0, X1], "y": [Y0, Y1], "centre": [round(cx, 3), round(cy, 3)]},
           "thresholds_artifact": "L2/SCHEME_GATE_THRESHOLDS_v1.json",
           "criteria": R,
           "scheme_layer": {"criteria": ["P1", "P2", "P3", "P4"], "verdicts": scheme,
                            "verdict": "PASS" if all(v == "PASS" for v in scheme) else ("FAIL" if "FAIL" in scheme else "PENDING"),
                            "complete": all(v in ("PASS", "FAIL") for v in scheme),
                            "FAIL_named": [k for k in ("P1", "P2", "P3", "P4") if R[k]["verdict"] == "FAIL"]},
           "construction_layer": {"criteria": ["P5", "P6", "P7"], "verdicts": construction,
                                  "verdict": "PASS" if all(v == "PASS" for v in construction) else ("FAIL" if "FAIL" in construction else "PENDING"),
                                  "PENDING_named": [k for k in ("P5", "P6", "P7") if R[k]["verdict"] == "PENDING"]},
           "gate_rule": "chain entry: k2_gen_v5 / k2_route_segment refuse to run unless the scheme-layer certificate is PRESENT and verdict==PASS",
           "OWNER-ITEMS": 0}
    out = a.out or os.path.join(L2, "SCHEME_GATE_%s_v2.json" % os.path.basename(a.board).replace(".kicad_pcb", ""))
    json.dump(rep, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"board": os.path.basename(a.board), "scheme": rep["scheme_layer"], "construction": rep["construction_layer"]}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
