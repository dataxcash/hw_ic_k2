#!/usr/bin/env python3
"""k2_spec_rev60_declare_v1.py --- #K2-339 sec.2.1: declare SPEC rev-60 (J12 yields / H3 lands top-left).

Modification-type rev (like rev-58): every changed leaf is recorded old->new.  Also records the freshly found
defect M-ENG-HOLE-KEEPOUT-STALE (H2/H4 keepout squares parked at their OLD positions) WITHOUT fixing it in this
rev (one change at a time), and a rollback card.
Usage: python3 tools/k2_spec_rev60_declare_v1.py [--from rev-59] [--out <file>]
"""
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L3 = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4", "L3")
H3_OLD = [45.1, 75.1]
H3_NEW = [25.0713, 35.0713]
J12_OLD = [27.94, 35.32]
J12_NEW = [27.94, 42.85]
KO_HALF = 3.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.join(L3, "SPEC_k2_v4.spec-rev-59.json"))
    ap.add_argument("--out", default=os.path.join(L3, "SPEC_k2_v4.spec-rev-60.json"))
    a = ap.parse_args()
    s = json.load(open(a.src, encoding="utf-8"))
    leaf = {}
    # 1) mounting hole H3
    for h in s["mounting_holes"]["holes"]:
        if h["ref"] == "H3":
            leaf["mounting_holes.holes[H3].at"] = {"old": list(h["at"]), "new": list(H3_NEW)}
            h["at"] = list(H3_NEW)
            old_bb = list(h["keepout_bbox"])
            h["keepout_bbox"] = [round(H3_NEW[0] - KO_HALF, 3), round(H3_NEW[1] - KO_HALF, 3),
                                 round(H3_NEW[0] + KO_HALF, 3), round(H3_NEW[1] + KO_HALF, 3)]
            leaf["mounting_holes.holes[H3].keepout_bbox"] = {"old": old_bb, "new": list(h["keepout_bbox"])}
    # 2) H3 keepout square polygon (hole + keepout move as ONE atomic edit)
    for z in s["keepout_geometry"]["zones"]:
        if z["name"] == "K2_HOLE_KEEPOUT_H3":
            old_pts = [list(p) for p in z["pts"]]
            dx, dy = H3_NEW[0] - H3_OLD[0], H3_NEW[1] - H3_OLD[1]
            z["pts"] = [["%.6f" % (float(p[0]) + dx), "%.6f" % (float(p[1]) + dy)] for p in z["pts"]]
            leaf["keepout_geometry.zones[K2_HOLE_KEEPOUT_H3].pts"] = {"old_first3": old_pts[:3],
                                                                      "new_first3": z["pts"][:3],
                                                                      "translation": [round(dx, 4), round(dy, 4)]}
    # 3) J12 (12V power input) yields down the left edge
    ph = s["components"]["pin_headers"]["positions"]
    leaf["components.pin_headers.positions.J12"] = {"old": list(ph["J12"]), "new": list(J12_NEW)}
    ph["J12"] = list(J12_NEW)
    s["_spec_rev_60"] = {
        "card": "SPEC-REV-60（J12 让位 + H3 落左上角 · 修改式 · 逐 leaf 旧→新）",
        "at": "2026-09-28",
        "authority": "#K2-339 sec.2.1 (law-only resolution: layout/mechanical = the #K2-322 autonomous layer)",
        "scope": ("H3 -> top-left corner ON the N3/P3 threshold (inset = 3.0/sqrt(2) = 2.1213 mm, edge margin 2.121 mm); "
                  "J12 (12V power input) slides 7.53 mm down the left edge to vacate the corner keepout; the H3 keepout "
                  "square moves WITH the hole (atomic)."),
        "leaf_diff": leaf,
        "rule_basis": {"H3": "#K2-322 sec.3.1 four-corner symmetry (N3/P3 corner_max 3.0 mm) + SPEC constraints.edge_copper_min 0.3",
                       "J12": "mechanical norm: power input hugs the board edge and clears the corner hole keepout; "
                              "in-register library header geometry (2.54 mm pitch). TI EVM NOT cited (its authority is "
                              "limited to the redriver escape paradigm, #K2-339 sec.2.3)."},
        "defect_registered_not_fixed": {
            "id": "M-ENG-HOLE-KEEPOUT-STALE",
            "evidence": "on l12 the H2/H4 keepout squares sit at their OLD positions: K2_HOLE_KEEPOUT_H2 bbox "
                        "[136.6,36.6,142.6,42.6] (H2 is at [136.6,35.1], so the square is 1.5 mm too low) and "
                        "K2_HOLE_KEEPOUT_H4 bbox [111.6,33.1,117.6,39.1] while H4 is at [140.8,76.8] (the square is at "
                        "the PRE-move position). A moved hole whose keepout stays behind is silent (no DRC item).",
            "fix": "re-derive every hole keepout square from its hole `at` whenever a hole moves; regression item = "
                   "keepout bbox centre == hole `at` for all four holes.",
            "why_not_fixed_here": "one change at a time: rev-60 is the J12/H3 change; the H2/H4 keepout re-derivation "
                                  "changes the pour in that area and therefore needs its own DRC-verified rev."},
        "rollback": "copy SPEC_k2_v4.spec-rev-59.json over project.yaml's spec_name and restore board_path to "
                    "hw/k2_v4_8L.l12.kicad_pcb; the l13 board is additive (l12 untouched).",
    }
    json.dump(s, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"wrote": a.out, "leaves": sorted(leaf.keys())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
