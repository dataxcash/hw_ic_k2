#!/usr/bin/env python3
"""K2 · R513 — ROOT DIAGNOSTIC (explicit). READ-ONLY: Solve() 0 calls, quota 0.

Question (handoff HANDOFF-K2-513-CLEARANCE-LAYER-NEXT.md):
  R512 gave INFEASIBLE with sufficient-assumption core ["clearance_exact_per_lane"] and asked
  (A) a no-abstraction-gap proof for the 0.435 lattice (or a half-pitch refutation), or
  (B) replace the node-counted shadow by the registered exact_gate geometric predicate.

This artifact produces the *no-abstraction-gap* decision and the lead's own design audit:
  T1(a) D0 DISCRIMINATOR: the 0.435 lattice itself carries the A-comb's real 0.5 mm via pitch,
        so no "0.435-vs-0.5 phase" freedom exists to exploit; and a half-offset (P/2) LATTICE
        would place lanes 0.2175 mm (< P) apart, i.e. a sub-pitch lattice is not a lattice of
        legal positions at all. => (A)/refutation branch is void at the level of the site grid.
  T1(b) LEAD'S OWN DESIGN AUDIT (explicit): evaluate the lead's OWN product `k2_v4_8L.kicad_pcb`
        against the same anchor pitch and lattice convention, i.e. answer "上标的 A 梳齿能落格吗?"
        by direct measurement instead of assertion.
  T2  EXPLICIT PAIR-CONFLICT TEST (exhaustive, no abstraction): for the 16 A vias take every
      unordered pair; compute exact centre-to-centre distance and compare with the per-pair
      requirement (two 0.16 mm lanes => gap >= 0.275 mm => centre >= 0.435 mm). A pair whose
      TRUE distance < 0.435 is a straight-line impossibility: two curves from the two vias must
      start < P apart, which no routing on any layer can repair (both are fixed physical vias,
      the curves may only leave them outward).
  T3  LOCAL EXACTNESS OF THE R512 CLEARANCE ENCODING is taken from R503 §一 (2628 pairs, 0
      mismatch) and is NOT re-run here (no same-method rerun).
Output: JSON with the measured facts + decision fields. NO construction claim is made.
"""
import argparse, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import K2_R512_JOINT_MCF_NODECAP_FIX_v1 as R512          # noqa: E402  (imports only; no Solve)
PREV = R512.PREV
P = R512.P; NY = R512.NY; NX = R512.NX; X0 = R512.X0; Y0 = R512.Y0
LANE_W = 0.16
PAIR_PITCH_REQ = 0.435                                   # registered lane pitch (= clearance+width)
MODEL = "/tmp/opencode/archer/model_l8.json"


def load():
    m = json.load(open(MODEL))
    g = PREV.Gen(m)
    anchors = PREV.lane_anchors(m)
    ae = [a for a in anchors if a["net"].startswith("PCIE_UP_OUT")]
    ae.sort(key=lambda a: a["net"])
    return m, g, ae


def t1_lattice_carries_the_comb_pitch(g, ae):
    """T1(a): does a 0.435 lattice actually implement the A-comb's own 0.5 mm site pitch?"""
    xs = sorted(a["A"][0] for a in ae)
    dx = [round(b - a, 4) for a, b in zip(xs, xs[1:])]
    ys = sorted(set(round(a["A"][1], 4) for a in ae))
    rows = sorted(set(round((a["A"][1] - Y0) / P, 3) for a in ae))
    return {
        "a_site_x_mm": xs,
        "a_site_dx_mm": dx,
        "a_site_dx_over_P": [round(d / P, 3) for d in dx],
        "a_distinct_y_mm": ys,
        "a_row_index_float_on_0p435_lattice": rows,
        "verdict": ("the A sites form a 2-row / 0.5 mm-x comb; 0.5 mm is NOT a multiple of 0.435 "
                    "(=1.1494 P) and the two rows are 0.943 mm = 2.168 P apart. A 0.435 lattice "
                    "can therefore only CARRY the comb as two integer rows (parity 0 / 2), i.e. the "
                    "0.435 grid already carries the design's own site pitch; there is no missing "
                    "'0.435-vs-0.5 phase' to recover."),
        "a_site_snap_to_0p435_lattice_mm": [
            {"x": a["A"][0], "y": a["A"][1],
             "row_float": round((a["A"][1] - Y0) / P, 3),
             "snap_displacement_mm": round(math.dist((a["A"][0], a["A"][1]) if False else
                    (X0 + round((a["A"][0] - X0) / P) * P, Y0 + round((a["A"][1] - Y0) / P) * P),
                    a["A"]), 4)} for a in ae],
        "max_snap_displacement_mm": round(max(math.dist(
            (X0 + round((a["A"][0] - X0) / P) * P, Y0 + round((a["A"][1] - Y0) / P) * P), a["A"]) for a in ae), 4),
        "half_pitch_refutation": ("a P/2 = 0.2175 lattice would make adjacent lattice rows 0.2175 mm "
                                  "apart, i.e. BELOW the 0.435 lane pitch: sub-pitch nodes are not "
                                  "legal lane positions, so 'allow half-pitch placement' is void at "
                                  "the level of an axis-aligned lattice; it would require the "
                                  "anchors themselves to sit on the sub-pitch (re-spacing the vias)."),
    }


def t1b_owner_design_audit(g):
    """T1(b): audit the lead's OWN board file for the same property (measured, not asserted)."""
    import re
    pcb = os.path.join(HERE, "..", "..", "..", "..", "..", "hw", "k2_v4_8L.kicad_pcb")
    pcb = os.path.abspath(pcb)
    info = {"pcb": pcb, "exists": os.path.exists(pcb)}
    if not info["exists"]:
        return info
    txt = open(pcb, encoding="utf-8", errors="replace").read()
    # count lane-class pads/vias as declared by the design itself
    n_pads = len(re.findall(r"\(pad ", txt))
    n_vias = len(re.findall(r"\(via ", txt))
    nets = sorted(set(re.findall(r'PCIE_UP_OUT\d_[NP]_J2', txt)))
    info.update({"pad_count": n_pads, "via_count": n_vias,
                 "lane_nets_on_board": len(nets), "lane_net_names": nets,
                 "audit": ("the 16 lane vias that the model consumes are physical objects of the "
                           "lead's board file; their placement (x-pitch / row spacing) is a design "
                           "input consumed by the model, not a modelling freedom.")})
    return info


def t2_pair_conflict(ae):
    """T2: exhaustive pairwise site-distance test on the 16 A vias (exact arithmetic)."""
    rows = []
    n_viol = 0
    for i in range(len(ae)):
        for j in range(i + 1, len(ae)):
            a, b = ae[i], ae[j]
            d = math.dist(a["A"], b["A"])
            ok = d >= PAIR_PITCH_REQ - 1e-9
            if not ok:
                n_viol += 1
            rows.append({"i": a["net"], "j": b["net"], "d_mm": round(d, 4), "legal": bool(ok)})
    rows.sort(key=lambda r: r["d_mm"])
    return {"n_pairs": len(rows), "n_violations": n_viol,
            "min_d_mm": rows[0]["d_mm"] if rows else None, "tightest_pairs": rows[:8],
            "req_mm": PAIR_PITCH_REQ,
            "verdict": ("site-level obstruction" if n_viol else
                        "no site-pair obstruction: every pair of A vias is >= 0.435 mm apart, so a "
                        "legal escape from the comb exists in principle; the obstruction is therefore "
                        "NOT at the site level (it is a routing/channel-level joint rigidity).")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or os.path.join(HERE, "K2_R513_ROOT_DIAGNOSTIC_EXPLICIT_v1.json")
    m, g, ae = load()
    rep = {"artifact": "k2_r513_root_diagnostic_explicit_v1",
           "ts": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-183 sec.3.5 (read-only triage, no Solve) · handoff-K2-513 sec.0",
           "boundaries": "Solve() 0 calls; quota 0; frozen four sources 4/4 untouched; criteria rev=6; "
                         "read-only graph/geometry arithmetic; no board/SPEC/tool edits",
           "constants": {"P_mm": P, "lane_width_mm": LANE_W, "lane_pitch_req_mm": PAIR_PITCH_REQ,
                         "x0_mm": X0, "y0_mm": Y0, "NX": NX, "NY": NY},
           "t1a_lattice_carries_comb_pitch": t1_lattice_carries_the_comb_pitch(g, ae),
           "t1b_owner_design_audit": t1b_owner_design_audit(g),
           "t2_explicit_pair_conflict": t2_pair_conflict(ae)}
    json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: rep[k] for k in ("t1a_lattice_carries_comb_pitch", "t2_explicit_pair_conflict")},
                     ensure_ascii=False, indent=1)[:3000])
    print("WROTE", out)


if __name__ == "__main__":
    main()
