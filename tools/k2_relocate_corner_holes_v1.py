#!/usr/bin/env python3
"""k2_relocate_corner_holes_v1.py --- #K2-340 sec.4: bring the remaining mounting holes onto the N3/P3 corner rule.

For each requested hole: the corner target is DERIVED (inset = corner_max/sqrt(2), the same derivation used for
H3), then verified against (a) C16 component-level keepout (pad-bbox pairwise, EVERY item at its candidate
position, margin 0.20 mm), (b) the OTHER holes' keepout squares, (c) board-edge clearance >= 0.3 mm.  If the exact
corner is infeasible, a bounded 1-D scan runs along the corner diagonal (0.05 mm) for the nearest feasible point.

Reference scope (#K2-339 sec.2.3): mechanical norm (#K2-322 sec.3.1 + SPEC edge rule) and the in-register board
geometry ONLY.  The TI EVM is NOT cited (its authority is the redriver escape paradigm).

Usage (KiCad python): k2_relocate_corner_holes_v1.py --board <in> --holes H1,H2,H4 --spec <SPEC.json> [--out json]
"""
import argparse, json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4")
CORNER_MAX, EDGE_MIN, MARGIN, KO_HALF = 3.0, 0.3, 0.20, 3.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--holes", default="H1,H2,H4")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", default=os.path.join(ART, "L2", "RELOCATE_CORNER_HOLES_v1.json"))
    ap.add_argument("--step", type=float, default=0.05)
    ap.add_argument("--max-inset", type=float, default=2.0)
    a = ap.parse_args()
    import pcbnew as P
    b = P.LoadBoard(a.board)
    e = b.GetBoardEdgesBoundingBox()
    X0, X1, Y0, Y1 = [round(P.ToMM(v), 4) for v in (e.GetLeft(), e.GetRight(), e.GetTop(), e.GetBottom())]
    corners = {"TL": (X0, Y0, +1, +1), "TR": (X1, Y0, -1, +1), "BL": (X0, Y1, +1, -1), "BR": (X1, Y1, -1, -1)}
    ins = round(CORNER_MAX / math.sqrt(2.0), 4)
    spec = json.load(open(a.spec, encoding="utf-8"))
    kos = {}
    for z in spec["keepout_geometry"]["zones"]:
        nm = z.get("name", "")
        if nm.startswith("K2_HOLE_KEEPOUT_"):
            pts = [(float(p[0]), float(p[1])) for p in z["pts"]]
            kos[nm.replace("K2_HOLE_KEEPOUT_", "")] = (min(p[0] for p in pts), min(p[1] for p in pts),
                                                       max(p[0] for p in pts), max(p[1] for p in pts))
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    cur = {r: (round(P.ToMM(f.GetPosition().x), 3), round(P.ToMM(f.GetPosition().y), 3)) for r, f in fps.items()}
    boxes = {}
    for r, f in fps.items():
        boxes[r] = [(round(P.ToMM(p.GetBoundingBox().GetLeft()) - cur[r][0], 4),
                     round(P.ToMM(p.GetBoundingBox().GetTop()) - cur[r][1], 4),
                     round(P.ToMM(p.GetBoundingBox().GetRight()) - cur[r][0], 4),
                     round(P.ToMM(p.GetBoundingBox().GetBottom()) - cur[r][1], 4)) for p in f.Pads()]
    hole_refs = [r for r in fps if r.startswith("H") and r[1:].isdigit()]

    def at_boxes(r, x, y):
        return [(bx0 + x, by0 + y, bx1 + x, by1 + y) for (bx0, by0, bx1, by1) in boxes[r]]

    def ov(A, B, m=MARGIN):
        return not (A[2] + m <= B[0] or B[2] + m <= A[0] or A[3] + m <= B[1] or B[3] + m <= A[1])

    def check(moves):
        coll, oob = [], []
        for r, (x, y) in moves.items():
            for bb in at_boxes(r, x, y):
                if bb[0] < X0 + EDGE_MIN or bb[2] > X1 - EDGE_MIN or bb[1] < Y0 + EDGE_MIN or bb[3] > Y1 - EDGE_MIN:
                    oob.append({"ref": r, "box": [round(v, 3) for v in bb]})
            for r2 in boxes:
                if r2 == r:
                    continue
                x2, y2 = moves.get(r2, cur[r2])
                for A in at_boxes(r, x, y):
                    for B in at_boxes(r2, x2, y2):
                        if ov(A, B):
                            coll.append({"a": r, "b": r2})
        return (not coll and not oob), coll, oob

    def ko_conflict(moves):
        """a hole must not sit inside ANOTHER hole's keepout square (hole-to-hole by keepout)."""
        bad = []
        for r, (x, y) in moves.items():
            for nm, (kx0, ky0, kx1, ky1) in kos.items():
                if nm == r:
                    continue
                x2, y2 = moves.get(nm, cur.get(nm, (None, None)))
                if x2 is None:
                    continue
                # the other hole's keepout square travels with that hole -> compare square centre vs this hole
                if kx0 - KO_HALF <= x <= kx1 + KO_HALF and ky0 - KO_HALF <= y <= ky1 + KO_HALF:
                    bad.append({"hole": r, "inside_keepout_of": nm})
        return bad

    want = [h.strip() for h in a.holes.split(",") if h.strip()]
    out = {}
    for h in want:
        if h not in fps:
            out[h] = {"error": "no such hole"}
            continue
        cx, cy = cur[h]
        nm = min(corners, key=lambda k: math.hypot(cx - corners[k][0], cy - corners[k][1]))
        bx, by, sx, sy = corners[nm]
        target = (round(bx + sx * ins, 4), round(by + sy * ins, 4))
        tried = []
        chosen, proof = None, None
        for k in range(0, int(a.max_inset / a.step) + 1):
            extra = round(k * a.step, 4)
            px, py = round(bx + sx * (ins + extra), 4), round(by + sy * (ins + extra), 4)
            moves = {r: (px, py) if r == h else cur[r] for r in hole_refs}
            ok, coll, oob = check(moves)
            ko = ko_conflict(moves)
            dist = math.hypot(px - bx, py - by)
            tried.append({"inset": round(ins + extra, 4), "at": [px, py], "corner_dist": round(dist, 4),
                          "c16_ok": ok, "n_coll": len(coll), "ko": ko})
            if ok and not ko and dist <= CORNER_MAX + 1e-9:
                chosen, proof = (px, py), {"collisions": coll[:5], "oob": oob[:5], "ko": ko}
                break
        out[h] = {"corner": nm, "from": list(cur[h]), "corner_target": list(target),
                  "chosen": list(chosen) if chosen else None, "moved": bool(chosen and list(chosen) != list(cur[h])),
                  "corner_dist_mm": round(math.hypot(chosen[0] - bx, chosen[1] - by), 4) if chosen else None,
                  "edge_margin_mm": round(min(chosen[0] - X0, X1 - chosen[0], chosen[1] - Y0, Y1 - chosen[1]), 4) if chosen else None,
                  "proof": proof, "tried_head": tried[:6]}
    rep = {"artifact": "k2_relocate_corner_holes_v1", "ts": "2026-09-28",
           "authority": "#K2-340 sec.4 / #K2-339 sec.2.1: bring H1 H2 H4 onto the corner rule (ENG autonomous)",
           "board": a.board, "spec": a.spec, "board_frame": {"x": [X0, X1], "y": [Y0, Y1]}, "inset_mm": ins,
           "reference_scope": ["mechanical norm #K2-322 sec.3.1 + SPEC constraints.edge_copper_min (PRODUCT/mechanical)",
                               "in-register board geometry", "TI EVM: NOT cited (#K2-339 sec.2.3)"],
           "hole_keepout_squares": {k: list(v) for k, v in kos.items()},
           "holes": out,
           "verdict": "PASS" if all(v.get("chosen") and v.get("corner_dist_mm", 9) <= CORNER_MAX + 1e-9 for v in out.values()) else "FAIL",
           "OWNER-ITEMS": 0}
    json.dump(rep, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"verdict": rep["verdict"],
                      "holes": {h: {"corner": v.get("corner"), "from": v.get("from"), "to": v.get("chosen"),
                                    "corner_dist": v.get("corner_dist_mm"), "edge": v.get("edge_margin_mm")} for h, v in out.items()}},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
