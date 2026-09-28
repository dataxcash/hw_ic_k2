#!/usr/bin/env python3
"""k2_relocate_j12_h3_v1.py --- #K2-339 sec.2.1 law-only resolution of the corner conflict.

DECIDES (ENG autonomous: layout/mechanical = the #K2-322 charter's autonomous layer):
  * H3 -> the top-left corner, ON the N3/P3 threshold: inset = corner_max/sqrt(2) (the same derivation already
    used for the other corners) -- i.e. the corner-distance rule is met exactly, with edge clearance left over.
  * J12 (the 12V power input header) -> SLIDE DOWN THE LEFT EDGE just enough to vacate the corner keepout
    ("power input hugs the edge, clear of the corner hole" = mechanical norm + product practice).
Bounded deterministic 1-D scan (0.05 mm) for the SMALLEST downward move that is feasible under:
   (a) C16 component-level keepout  = pad-bbox pairwise, EVERY item at its candidate position, margin 0.20 mm
   (b) the H3/Hole keepout squares (6x6 mm, all layers, from SPEC keepout_geometry) must not swallow a pad
   (c) board-edge clearance >= 0.3 mm (SPEC constraints.edge_copper_min)
REPORT SCOPE (the #K2-339 sec.2.3 discipline: every citation declares its applicable scope):
   * cited: mechanical norm (mounting-hole corner rule, #K2-322 sec.3.1) + SPEC edge rule  -> PRODUCT/mechanical
   * cited: header-column spacing practice (2.54 mm header pitch, in-register library geometry) -> PRODUCT/library
   * NOT cited: the TI EVM (its authority is limited to the redriver escape paradigm only)
Writes L2/RELOCATE_J12_H3_v1.json.  Read-only w.r.t. the board.

Usage (KiCad python): k2_relocate_j12_h3_v1.py --board hw/k2_v4_8L.l12.kicad_pcb --spec <SPEC.json> [--out json]
"""
import argparse, json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4")
CORNER_MAX = 3.0
EDGE_MIN = 0.3
MARGIN = 0.20
H3_FIXED = None            # computed from the frame


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", default=os.path.join(ART, "L2", "RELOCATE_J12_H3_v1.json"))
    ap.add_argument("--step", type=float, default=0.05)
    ap.add_argument("--y0", type=float, default=36.0)
    ap.add_argument("--y1", type=float, default=75.0)
    a = ap.parse_args()
    import pcbnew as P
    b = P.LoadBoard(a.board)
    e = b.GetBoardEdgesBoundingBox()
    X0, X1, Y0, Y1 = [round(P.ToMM(v), 4) for v in (e.GetLeft(), e.GetRight(), e.GetTop(), e.GetBottom())]
    spec = json.load(open(a.spec, encoding="utf-8"))
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    nets = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    hole_kos = {}
    for z in spec.get("keepout_geometry", {}).get("zones", []):
        nm = z.get("name", "")
        if nm.startswith("K2_HOLE_KEEPOUT_"):
            pts = [(float(p[0]), float(p[1])) for p in z["pts"]]
            hole_kos[nm.replace("K2_HOLE_KEEPOUT_", "")] = (min(p[0] for p in pts), min(p[1] for p in pts),
                                                            max(p[0] for p in pts), max(p[1] for p in pts))
    cur = {r: (round(P.ToMM(f.GetPosition().x), 3), round(P.ToMM(f.GetPosition().y), 3)) for r, f in fps.items()}
    boxes = {}
    for r, f in fps.items():
        boxes[r] = []
        for p in f.Pads():
            bb = p.GetBoundingBox()
            boxes[r].append((round(P.ToMM(bb.GetLeft()) - cur[r][0], 4), round(P.ToMM(bb.GetTop()) - cur[r][1], 4),
                             round(P.ToMM(bb.GetRight()) - cur[r][0], 4), round(P.ToMM(bb.GetBottom()) - cur[r][1], 4),
                             P.ToMM(p.GetSize().x), P.ToMM(p.GetSize().y)))

    def at_boxes(r, x, y):
        return [(bx0 + x, by0 + y, bx1 + x, by1 + y) for (bx0, by0, bx1, by1, _w, _h) in boxes[r]]

    def overlap(A, B, m=MARGIN):
        return not (A[2] + m <= B[0] or B[2] + m <= A[0] or A[3] + m <= B[1] or B[3] + m <= A[1])

    def check(moves):
        """moves = {ref: (x,y)}; returns (ok, [named collisions], [oob])"""
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
                        if overlap(A, B):
                            coll.append({"a": r, "b": r2, "a_box": [round(v, 3) for v in A]})
        return (not coll and not oob), coll, oob

    def in_hole_keepout(x, y, halfs):
        for nm, (kx0, ky0, kx1, ky1) in hole_kos.items():
            if kx0 - halfs[0] <= x <= kx1 + halfs[0] and ky0 - halfs[1] <= y <= ky1 + halfs[1]:
                return nm
        return None

    ins = round(CORNER_MAX / math.sqrt(2.0), 4)
    h3 = (round(X0 + ins, 4), round(Y0 + ins, 4))
    j12x = cur["J12"][0]
    scan, feasible = [], []
    y = a.y0
    while y <= a.y1 + 1e-9:
        y = round(y, 4)
        moves = {"H3": h3, "J12": (j12x, y)}
        ok, coll, oob = check(moves)
        # hole-keepout squares: the moved pads must not land inside any hole keepout square
        ko_hit = []
        for r in ("H3", "J12"):
            for bb in at_boxes(r, *moves[r]):
                for nm, (kx0, ky0, kx1, ky1) in hole_kos.items():
                    if not (bb[2] <= kx0 or bb[0] >= kx1 or bb[3] <= ky0 or bb[1] >= ky1):
                        ko_hit.append({"ref": r, "hole_keepout": nm})
        scan.append({"j12_y": y, "ok": ok, "n_coll": len(coll), "n_oob": len(oob), "ko_hit": sorted({k["hole_keepout"] for k in ko_hit})})
        if ok and not ko_hit:
            feasible.append((y, coll, oob))
        y += a.step
    feasible.sort(key=lambda z: (abs(z[0] - cur["J12"][1]), z[0]))
    chosen = feasible[0][0] if feasible else None
    # final proof at the chosen position
    proof = None
    if chosen is not None:
        moves = {"H3": h3, "J12": (j12x, chosen)}
        ok, coll, oob = check(moves)
        ko = []
        for r in ("H3", "J12"):
            for bb in at_boxes(r, *moves[r]):
                for nm, (kx0, ky0, kx1, ky1) in hole_kos.items():
                    if not (bb[2] <= kx0 or bb[0] >= kx1 or bb[3] <= ky0 or bb[1] >= ky1):
                        ko.append({"ref": r, "hole_keepout": nm})
        proof = {"moves": {k: list(v) for k, v in moves.items()}, "c16_ok": ok and not ko,
                 "collisions": coll[:8], "out_of_board": oob[:8], "hole_keepout_hits": ko,
                 "h3_corner_dist_mm": round(math.hypot(h3[0] - X0, h3[1] - Y0), 3),
                 "h3_edge_margin_mm": round(min(h3[0] - X0, h3[1] - Y0), 3),
                 "j12_down_mm": round(chosen - cur["J12"][1], 3)}
    rep = {
        "artifact": "k2_relocate_j12_h3_v1", "ts": "2026-09-28",
        "authority": "#K2-339 sec.2.1: law-only resolution of the corner conflict (ENG autonomous: layout/mechanical)",
        "board": a.board, "spec": a.spec,
        "board_frame": {"x": [X0, X1], "y": [Y0, Y1]},
        "rule": {"H3": "top-left corner at inset = corner_max/sqrt(2) = %.4f mm (N3/P3 threshold met exactly)" % ins,
                 "J12": "bounded 1-D downward scan (step %.2f mm) along x=%.2f; smallest move that is C16-clean, "
                        "clear of every hole keepout square, and >= %.1f mm from the edge" % (a.step, j12x, EDGE_MIN)},
        "reference_scope_declarations": [
            {"cited": "mechanical norm: mounting holes at the four corners (#K2-322 sec.3.1) + SPEC constraints.edge_copper_min",
             "scope": "PRODUCT / mechanical - applies to this board"},
            {"cited": "in-register library geometry: 2.54 mm header pitch / 1.5 mm pin pads",
             "scope": "PRODUCT / library - applies to this board"},
            {"cited": "TI DS320PR1601 EVM", "scope": "NOT cited here - its authority is limited to the redriver escape paradigm (#K2-339 sec.2.3)"}],
        "current": {r: list(cur[r]) for r in ("J12", "H3")},
        "hole_keepout_squares": {k: list(v) for k, v in hole_kos.items()},
        "scan": {"n": len(scan), "feasible_ys": [z[0] for z in feasible][:20], "first_20": scan[:20]},
        "decision": {"H3": list(h3), "J12": [j12x, chosen] if chosen is not None else None,
                     "delta": {"H3": [round(h3[0] - cur["H3"][0], 3), round(h3[1] - cur["H3"][1], 3)],
                               "J12": [0.0, round(chosen - cur["J12"][1], 3)] if chosen is not None else None}},
        "proof": proof,
        "verdict": "PASS" if (chosen is not None and proof and proof["c16_ok"]) else "FAIL",
        "OWNER-ITEMS": 0,
    }
    json.dump(rep, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"verdict": rep["verdict"], "H3": rep["decision"]["H3"], "J12": rep["decision"]["J12"],
                      "delta": rep["decision"]["delta"], "n_feasible": len(feasible),
                      "proof": {k: proof[k] for k in ("c16_ok", "h3_corner_dist_mm", "h3_edge_margin_mm", "j12_down_mm")} if proof else None},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
