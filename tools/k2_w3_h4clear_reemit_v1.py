#!/usr/bin/env python3
"""k2_w3_h4clear_reemit_v1.py --- #K2-351 sec.4(a): re-emit the DN input lane plan so the H4 corner is clear.

WHY: R912 machine-proved that the copper inside the H4 corner square is the DN4/DN5 (+DN6/DN7) 'input' lane-plan
detour and its landing column, and that k2_gen_v5.py emits no DN geometry while stage 2a copies the drawing
verbatim -> a chain rerun with an unchanged drawing cannot clear H4.

HARD CONSTRAINT (from R912, endorsed by #K2-351): for every DN input lane whose column crosses the keepout band,
column_x + via_radius(0.175) + margin(0.10) <= 137.9287  =>  column_x <= 137.6537.

RE-EMISSION (closed form, no search):
  * the four deepest east columns (pad-west polarity, In5 leg + F.Cu landing run both shorten by the shift) are
    moved west, uniformly spaced, order preserved;
  * the pad-east polarity of the SAME page carries the length-matching serpentine on its In5 lane, and its length is
    invariant to its own column_x (the In5 leg and the F.Cu landing run change in opposite directions), so the pair
    length is restored EXACTLY by shrinking the serpentine amplitude:
        n_edges * sqrt(s^2 + a'^2) = n_edges * sqrt(s^2 + a^2) - loss   =>   a' = sqrt((sqrt(s^2+a^2) - loss/n)^2 - s^2)
  * every endpoint (chip pad, connector pad) is untouched, so the FROZEN page manifest stays byte-identical.

OUTPUT: a NEW drawing file (consumed via the L4_MAIN env override of tools/p3_v57_l4_apply_drawing.py); the
canonical drawing, the engine, k2_gen_v5.py, the schematic and the frozen four are all untouched.

CLI: python3 tools/k2_w3_h4clear_reemit_v1.py [--src ...] [--out ...] [--report ...]
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEP2 = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4", "L3", "mcio_feas_step2")
SRC_DEFAULT = os.path.join(STEP2, "m13_v57_w3_joint_assignment.json")
OUT_DEFAULT = os.path.join(STEP2, "m13_v57_w3_joint_assignment_H4CLEAR_v1.json")
REP_DEFAULT = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4", "L2", "W3_H4CLEAR_REEMISSION_REPORT_v1.json")
KEEPOUT_X0, KEEPOUT_Y0, KEEPOUT_X1, KEEPOUT_Y1 = 137.9287, 73.9287, 143.9287, 79.9287
VIA_R, MARGIN = 0.175, 0.10
TOL = 1e-6            # mm; 1 nm - far below any DRC/manufacturing meaning (node coords are stored rounded)
X_MAX = KEEPOUT_X0 - VIA_R - MARGIN
# plan: net -> new column_x (uniform 0.70 pitch, deepest four east columns; all <= X_MAX, order preserved)
PLAN = {"PCIE_DN4_N": 137.60, "PCIE_DN5_P": 136.90, "PCIE_DN6_N": 136.20, "PCIE_DN7_P": 135.50}
PAD_WEST = 135.0     # the pad of the east column


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def d2(a, b):
    return math.dist(a[:2], b[:2])


def nodes_len(nd):
    return sum(d2(nd[i], nd[i + 1]) for i in range(len(nd) - 1)) - \
           sum(d2(nd[i], nd[i + 1]) for i in range(len(nd) - 1) if d2(nd[i], nd[i + 1]) == 0)


def ideal_len(nd):
    """length of the drawn polyline (zero-length layer-change points contribute nothing)"""
    return sum(d2(nd[i], nd[i + 1]) for i in range(len(nd) - 1))


def load(p):
    return json.load(open(p, encoding="utf-8"))


def reemit(d):
    rows = d["layers"]["R3"]["assignment"]
    pages = {p["page_id"]: p for p in d["pages"]}
    report = {"plan": {}, "pairs": {}}
    for net, new_x in PLAN.items():
        key = "J2|" + net
        row = rows[key]
        page_id, pol = row["page"], row["pol"]
        old_x = float(row["column_x"])
        assert abs(old_x - row["landing"][0]) < 1e-9
        assert new_x <= X_MAX + 1e-9, (net, new_x, X_MAX)
        assert new_x > PAD_WEST, (net, new_x)
        pg = pages[page_id]
        nd = pg["nodes"][pol]
        lane_y = next(n[1] for n in nd if n[2] == "In5.Cu")
        idx = [i for i, n in enumerate(nd) if abs(n[0] - old_x) < 1e-9]
        assert idx, (net, old_x)
        old_f = d2(nd[-2], nd[-1])                        # F.Cu landing run (column top -> pad)
        new_f = math.dist((new_x, nd[-2][1]), nd[-1][:2])
        loss = (old_x - new_x) + (old_f - new_f)
        for i in idx:
            nd[i][0] = new_x
        # ---- partner polarity: shrink its serpentine amplitude by exactly `loss` ----
        ppol = "P" if pol == "N" else "N"
        pnd = pg["nodes"][ppol]
        pl_y = next(n[1] for n in pnd if n[2] == "In5.Cu")
        dips = [i for i, n in enumerate(pnd) if n[2] == "In5.Cu" and abs(n[1] - pl_y) > 1e-9]
        assert len(dips) >= 3, (net, ppol, len(dips))
        a = pl_y - pnd[dips[0]][1]
        assert all(abs((pl_y - pnd[i][1]) - a) < 1e-9 for i in dips), "non-uniform dips"
        first, last = dips[0] - 1, dips[-1] + 1           # serpentine spans first..last (edges first->last)
        n_edges = last - first
        span = pnd[last][0] - pnd[first][0]
        s = span / n_edges                                 # per-edge x-step (from the span; file values are rounded)
        s_file = pnd[dips[0] + 1][0] - pnd[dips[0]][0]
        assert abs(s - s_file) < 1e-4, "serpentine x-step inconsistent"
        L0 = n_edges * math.hypot(s, a)
        need = L0 - loss
        t = need / n_edges
        assert t > s, ("length budget cannot close (would need a<=0)", net, t, s, loss)
        a_new = math.sqrt(t * t - s * s)
        for i in dips:
            pnd[i][1] = pl_y - a_new          # full precision: keeps the pair delta exact
        pair = {"page": page_id, "moved_pol": pol, "partner_pol": ppol,
                "old_column_x": old_x, "new_column_x": new_x, "shift_mm": round(old_x - new_x, 6),
                "old_landing_run_mm": round(old_f, 6), "new_landing_run_mm": round(new_f, 6),
                "length_loss_mm": round(loss, 6),
                "serpentine": {"n_edges": n_edges, "x_step_mm": round(s, 6),
                               "amp_old_mm": round(a, 6), "amp_new_mm": round(a_new, 6),
                               "extra_old_mm": round(L0 - n_edges * s, 6),
                               "extra_new_mm": round(need - n_edges * s, 6)},
                "ideal_len_moved": round(ideal_len(nd), 9), "ideal_len_partner": round(ideal_len(pnd), 9)}
        report["pairs"][key] = pair
        # ---- keep the meta rows consistent ----
        row["column_x"] = new_x
        row["landing"] = [new_x, row["landing"][1]]
        pg["r3_by_pol"][pol]["column_x"] = new_x
        pg["r3_by_pol"][pol]["landing"] = [new_x, pg["r3_by_pol"][pol]["landing"][1]]
        for v in pg.get("vias", []):
            if v.get("pol") == pol and abs(v["x"] - old_x) < 1e-9:
                v["x"] = new_x
        report["plan"][key] = {"old_column_x": old_x, "new_column_x": new_x}
    return report


def certify(src, out):
    d = load(out)
    s = load(src)
    pages = {p["page_id"]: p for p in d["pages"]}
    spages = {p["page_id"]: p for p in s["pages"]}
    cert = {"pairs_equal": [], "endpoints_unchanged": True, "untouched_pages_identical": True,
            "no_copper_in_keepout": {}, "columns_ok": True, "notes": []}
    touched = set()
    for net in PLAN:
        pg = pages[next(r["page"] for k, r in d["layers"]["R3"]["assignment"].items() if k == "J2|" + net)]
        touched.add(pg["page_id"])
    for pid, pg in pages.items():
        if "nodes" not in pg:
            continue
        for pol in ("N", "P"):
            cert["pairs_equal"].append({"page": pid, "pol": pol, "ideal_len_mm": round(ideal_len(pg["nodes"][pol]), 9)})
    # INVARIANT: every page's intra-pair delta (L_N - L_P) must be EXACTLY preserved by the re-emission.
    # (The canonical drawing's deltas are non-zero on most pages by design - the downstream chain closes them -
    #  so the correct invariant is "delta unchanged", not "delta == 0".)
    bad = []
    for pid, pg in pages.items():
        if "nodes" not in pg:
            continue
        sp = spages[pid]
        ds = ideal_len(sp["nodes"]["N"]) - ideal_len(sp["nodes"]["P"])
        do = ideal_len(pg["nodes"]["N"]) - ideal_len(pg["nodes"]["P"])
        if abs(ds - do) > TOL:
            bad.append({"page": pid, "src_delta": round(ds, 9), "out_delta": round(do, 9),
                        "shift": round(do - ds, 9)})
    cert["pair_delta_violations"] = bad
    # touched pairs: both polarities must shorten by the SAME amount (pair stays matched at its original delta)
    for net in PLAN:
        key = "J2|" + net
        pid = d["layers"]["R3"]["assignment"][key]["page"]
        sp = spages[pid]
        dn = round(ideal_len(pages[pid]["nodes"]["N"]) - ideal_len(sp["nodes"]["N"]), 9)
        dp = round(ideal_len(pages[pid]["nodes"]["P"]) - ideal_len(sp["nodes"]["P"]), 9)  # rounded for the report only
        cert.setdefault("touched_pair_shortening", {})[pid] = {"dL_N": dn, "dL_P": dp, "equal": abs(dn - dp) < TOL}
    # endpoints
    for pid, pg in pages.items():
        if "nodes" not in pg:
            continue
        sp = spages[pid]
        for pol in ("N", "P"):
            if pg["nodes"][pol][0][:2] != sp["nodes"][pol][0][:2] or pg["nodes"][pol][-1][:2] != sp["nodes"][pol][-1][:2]:
                cert["endpoints_unchanged"] = False
                cert["notes"].append("endpoint changed on %s/%s" % (pid, pol))
    # untouched pages byte-identical
    for pid, pg in pages.items():
        if pid in touched:
            continue
        if json.dumps(pg, sort_keys=True) != json.dumps(spages[pid], sort_keys=True):
            cert["untouched_pages_identical"] = False
            cert["notes"].append("untouched page changed: %s" % pid)
    # no affected-net copper inside the keepout square (segment sampling 0.05 mm; exact via test)
    for net in PLAN:
        key = "J2|" + net
        pid = d["layers"]["R3"]["assignment"][key]["page"]
        pol = d["layers"]["R3"]["assignment"][key]["pol"]
        nd = pages[pid]["nodes"][pol]
        hits = 0
        for i in range(len(nd) - 1):
            a, b = nd[i], nd[i + 1]
            L = d2(a, b); n = max(2, int(L / 0.05) + 1)
            for k in range(n + 1):
                x = a[0] + (b[0] - a[0]) * k / n; y = a[1] + (b[1] - a[1]) * k / n
                if KEEPOUT_X0 <= x <= KEEPOUT_X1 and KEEPOUT_Y0 <= y <= KEEPOUT_Y1:
                    hits += 1; break
            if hits:
                break
        cert["no_copper_in_keepout"][net] = (hits == 0)
    for key, r in d["layers"]["R3"]["assignment"].items():
        if key.startswith("J2|PCIE_DN") and r["column_x"] > 135.0:
            nm = key.split("|")[1]
            if nm in PLAN:
                if not (r["column_x"] <= X_MAX + 1e-9):
                    cert["columns_ok"] = False
    xs = sorted([d["layers"]["R3"]["assignment"]["J2|" + n]["column_x"] for n in PLAN], reverse=True)
    cert["new_columns"] = xs
    cert["min_pitch_mm"] = round(min(xs[i] - xs[i + 1] for i in range(len(xs) - 1)), 6)
    cert["x_max_allowed"] = round(X_MAX, 4)
    cert["via_clearance_to_keepout_mm"] = round(KEEPOUT_X0 - (xs[0] + VIA_R), 6)
    return cert


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC_DEFAULT)
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--report", default=REP_DEFAULT)
    a = ap.parse_args()
    src, out = a.src, a.out
    s = load(src)
    assert s.get("status") == "EMITTED" and s.get("verdict") == "FEASIBLE_ALL", "canonical drawing not FEASIBLE_ALL"
    rep = reemit(s)
    cert = certify(src, out) if False else None          # certify() reads --out; write first then certify
    s["_h4clear_reemission"] = {
        "authority": "#K2-351 sec.4(a) (bounded window) + R912 repair spec",
        "source_drawing": os.path.relpath(src, ROOT), "source_sha16": sha16(src),
        "constraint": {"keepout_square": [KEEPOUT_X0, KEEPOUT_Y0, KEEPOUT_X1, KEEPOUT_Y1],
                       "via_radius_mm": VIA_R, "margin_mm": MARGIN, "x_max_allowed": round(X_MAX, 4)},
        "plan": rep["plan"], "pairs": rep["pairs"],
        "method": ("closed form: the four deepest east columns move west (uniform 0.70 pitch, order preserved) and the "
                   "pad-east polarity of the same page restores the pair length EXACTLY by shrinking its In5 serpentine "
                   "amplitude (n_edges * sqrt(s^2+a^2) - loss); no search, no iteration, endpoints untouched."),
        "canonical_untouched": True}
    json.dump(s, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cert = certify(src, out)
    verdict = (cert["endpoints_unchanged"] and cert["untouched_pages_identical"]
               and not cert["pair_delta_violations"]
               and all(v["equal"] for v in cert.get("touched_pair_shortening", {}).values())
               and all(cert["no_copper_in_keepout"].values()) and cert["columns_ok"])
    rep_out = {"artifact": "k2_w3_h4clear_reemission_report_v1", "ts": "2026-09-28",
               "authority": "#K2-351 sec.4(a)", "source_sha16": sha16(src), "out_sha16": sha16(out),
               "verdict": "CERTIFIED" if verdict else "FAIL",
               "constraint": s["_h4clear_reemission"]["constraint"], "pairs": rep["pairs"],
               "certification": cert, "OWNER-ITEMS": 0}
    json.dump(rep_out, open(a.report, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"out": out, "out_sha16": sha16(out), "verdict": rep_out["verdict"],
                      "pair_delta_violations": cert["pair_delta_violations"],
                      "touched_pair_shortening": cert.get("touched_pair_shortening"),
                      "keepout_clear": cert["no_copper_in_keepout"],
                      "new_columns": cert["new_columns"], "min_pitch_mm": cert["min_pitch_mm"],
                      "via_clearance_to_keepout_mm": cert["via_clearance_to_keepout_mm"]}, ensure_ascii=False))
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
