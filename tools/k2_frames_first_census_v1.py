#!/usr/bin/env python3
"""k2_frames_first_census_v1.py --- #K2-348 W2' step 1: load the FRAMES layer (four corner keepout squares as
hard placement inputs) and measure the CONSTRUCTIVE criterion's baseline: how much copper / how many holes sit
inside each square TODAY.  Read-only.

Constructive criterion (the acceptance of W2'): each corner square must contain NO copper and NO hole because the
placement/router never put any there - explicitly NOT "sculpt the copper around the hole clean".

Usage (KiCad python): k2_frames_first_census_v1.py --board hw/k2_v4_8L.l14.kicad_pcb [--out json]
"""
import argparse, json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4", "L2", "FRAMES_FIRST_CENSUS_v1.json")
HALF = 3.0
CORNERS = {"H3_TL": (25.0713, 35.0713), "H2_TR": (140.9287, 35.0713),
           "H1_BL": (25.0713, 76.9287), "H4_BR": (140.9287, 76.9287)}   # H4: the frames-first target position


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    import pcbnew as P
    b = P.LoadBoard(a.board)
    nets = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    e = b.GetBoardEdgesBoundingBox()
    X0, X1, Y0, Y1 = [P.ToMM(v) for v in (e.GetLeft(), e.GetRight(), e.GetTop(), e.GetBottom())]

    def pt_seg(px, py, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
        return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))

    def pt_in_poly(x, y, pts):
        inside = False
        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % n]
            if (y1 > y) != (y2 > y):
                if x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                    inside = not inside
        return inside

    fills = []                                     # (netcode, layer, [pts])  filled pours
    for z in b.Zones():
        try:
            zn, lays = z.GetNetCode(), [L for L in z.GetLayerSet().Seq()]
        except Exception:
            continue
        for L in lays:
            try:
                pl = z.GetFilledPolysList(L)
            except Exception:
                continue
            for i in range(pl.OutlineCount()):
                c = pl.COutline(i)
                pts = [(P.ToMM(c.CPoint(j).x), P.ToMM(c.CPoint(j).y)) for j in range(c.PointCount())]
                if len(pts) >= 3:
                    fills.append((zn, L, pts))
    res = {"artifact": "k2_frames_first_census_v1", "ts": "2026-09-28", "board": a.board,
           "authority": "#K2-348 W2' step 1: frames layer (four corner 6x6 squares as HARD placement inputs) + the "
                        "constructive criterion baseline",
           "constructive_criterion": "each square must contain NO copper and NO hole BY CONSTRUCTION (not sculpted); "
                                     "measured here as: tracks/vias/pads/zone-fill hits == 0",
           "squares": {}}
    holes = [(fp.GetReference(), P.ToMM(fp.GetPosition().x), P.ToMM(fp.GetPosition().y))
             for fp in b.GetFootprints() if fp.GetReference().startswith("H") and fp.GetReference()[1:].isdigit()]
    for name, (cx, cy) in CORNERS.items():
        x0, x1_ = cx - HALF, cx + HALF
        y0, y1_ = cy - HALF, cy + HALF
        trk, via, pad = {}, {}, {}
        for t in b.GetTracks():
            nm = nets.get(t.GetNetCode(), "")
            if t.GetClass() == "PCB_VIA":
                x, y = P.ToMM(t.GetPosition().x), P.ToMM(t.GetPosition().y)
                if x0 <= x <= x1_ and y0 <= y <= y1_:
                    via[nm] = via.get(nm, 0) + 1
            else:
                x1, y1 = P.ToMM(t.GetStart().x), P.ToMM(t.GetStart().y)
                x2, y2 = P.ToMM(t.GetEnd().x), P.ToMM(t.GetEnd().y)
                n = max(2, int(math.hypot(x2 - x1, y2 - y1) / 0.05))
                if any(x0 <= x1 + (x2 - x1) * i / n <= x1_ and y0 <= y1 + (y2 - y1) * i / n <= y1_
                       for i in range(n + 1)):
                    trk[nm] = trk.get(nm, 0) + 1
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if p.GetNetCode() <= 0:
                    continue
                x, y = P.ToMM(p.GetPosition().x), P.ToMM(p.GetPosition().y)
                if x0 <= x <= x1_ and y0 <= y <= y1_:
                    pad[fp.GetReference()] = pad.get(fp.GetReference(), 0) + 1
        fl = {}
        for (zn, L, pts) in fills:
            gx = x0
            while gx <= x1_:
                gy = y0
                while gy <= y1_:
                    if pt_in_poly(gx, gy, pts):
                        nm2 = nets.get(zn, "")
                        fl[nm2] = fl.get(nm2, 0) + 1
                        break
                    gy += 0.5
                gx += 0.5
        hole_in = [h for (h, hx, hy) in holes if x0 <= hx <= x1_ and y0 <= hy <= y1_]
        res["squares"][name] = {"centre": [cx, cy], "bbox": [round(x0, 3), round(y0, 3), round(x1_, 3), round(y1_, 3)],
                                "tracks_in": trk, "vias_in": via, "pads_in": pad, "zone_fill_net_hits": fl,
                                "holes_in": hole_in,
                                "constructive_PASS": (not trk and not via and not pad and not fl)}
    res["summary"] = {"passing": [k for k, v in res["squares"].items() if v["constructive_PASS"]],
                      "failing": [k for k, v in res["squares"].items() if not v["constructive_PASS"]],
                      "square_convention": "bbox = [x0, y0, x1, y1]; hit test uses x0<=x<=x1 and y0<=y<=y1 (R884 fix: the first version mis-indexed the bbox)",
                      "note": "H4's square is measured at its frames-first TARGET position; today's board has H4 at "
                              "(140.8,76.8) so its own keepout square is elsewhere (M-ENG-HOLE-KEEPOUT-STALE, H4 branch)"}
    res["OWNER-ITEMS"] = 0
    json.dump(res, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"board": os.path.basename(a.board), "summary": res["summary"],
                      "squares": {k: {"tracks": v["tracks_in"], "vias": v["vias_in"], "pads": v["pads_in"],
                                      "fills": v["zone_fill_net_hits"], "holes": v["holes_in"],
                                      "PASS": v["constructive_PASS"]} for k, v in res["squares"].items()}},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
