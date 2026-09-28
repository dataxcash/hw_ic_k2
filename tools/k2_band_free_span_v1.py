#!/usr/bin/env python3
"""k2_band_free_span_v1.py --- read-only x-band free-span analyser (asset for #K2-352 C26/C27 follow-up).

WHY: the R914 judge failure proved that a LANDING COLUMN can only be re-placed by a JOINT solve, because the
right-edge In2 x-band is shared by the DN input columns and the UP output landing columns/vias. This tool measures,
for a given net's corridor, which x positions are actually free (no foreign In2 item within clearance), so the next
window can be planned from measured occupancy instead of from an assumed "free band" (the exact error R914 exposed).

Method (pure geometry, no solver): for every foreign In2 track/via/pad, treat it as an x-interval
[x - (r_item + clearance), x + (r_item + clearance)] valid over its y-extent; a candidate column x is BLOCKED for
the target net when the x-interval contains x AND the y-extent overlaps the target corridor [landing_y, lane_y].
Limits: In2-layer geometry only (a real DRC must still confirm F.Cu/In5/pour effects) - stated in the output.

CLI: python3 tools/k2_band_free_span_v1.py --board <pcb> --xmax 137.6537 --json-out <out>
"""
from __future__ import annotations
import argparse, json, os, sys

# the four deepest DN input landing columns and their corridors (landing_y, lane_y, pad_x, pad_y)
TARGET = {"PCIE_DN4_N": (59.45, 74.222, 135.0, 59.7), "PCIE_DN5_P": (60.05, 75.671, 135.0, 60.3),
          "PCIE_DN6_N": (63.05, 77.12, 135.0, 63.3), "PCIE_DN7_P": (63.65, 78.569, 135.0, 63.9)}
BAND = (128.0, 141.0, 56.0, 81.0)
STEP = 0.01


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--xmin", type=float, default=133.0)
    ap.add_argument("--xmax", type=float, default=137.6537)
    ap.add_argument("--clearance", type=float, default=0.175)
    ap.add_argument("--via-radius", type=float, default=0.175)
    ap.add_argument("--track-radius", type=float, default=0.08)
    ap.add_argument("--min-pitch", type=float, default=0.525)
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()
    import pcbnew as P
    b = P.LoadBoard(a.board)
    nets = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    x0b, x1b, y0b, y1b = BAND
    items = []
    for t in b.GetTracks():
        nm = nets.get(t.GetNetCode(), "")
        if t.GetClass() == "PCB_VIA":
            x, y = P.ToMM(t.GetPosition().x), P.ToMM(t.GetPosition().y)
            if "In2.Cu" in [b.GetLayerName(l) for l in t.GetLayerSet().Seq()] and x0b <= x <= x1b and y0b <= y <= y1b:
                items.append((x, y - a.via_radius, y + a.via_radius, nm, a.via_radius))
            continue
        if t.GetLayerName() != "In2.Cu":
            continue
        s, e = t.GetStart(), t.GetEnd()
        ax, ay, bx, by = P.ToMM(s.x), P.ToMM(s.y), P.ToMM(e.x), P.ToMM(e.y)
        if abs(ax - bx) > 1e-6 or not (x0b <= ax <= x1b):
            continue
        lo, hi = min(ay, by), max(ay, by)
        if hi < y0b or lo > y1b:
            continue
        items.append((ax, lo - a.track_radius, hi + a.track_radius, nm, a.track_radius))
    for p in b.GetPads():
        nm = nets.get(p.GetNetCode(), "")
        pos = p.GetPosition(); x, y = P.ToMM(pos.x), P.ToMM(pos.y)
        if "In2.Cu" not in [b.GetLayerName(l) for l in p.GetLayerSet().Seq()]:
            continue
        if not (x0b <= x <= x1b and y0b <= y <= y1b):
            continue
        h = P.ToMM(p.GetSize().y) / 2
        items.append((x, y - h, y + h, nm, max(P.ToMM(p.GetSize().x), P.ToMM(p.GetSize().y)) / 2))
    rep = {"artifact": "k2_band_free_span_v1", "ts": "2026-09-28", "board": a.board,
           "authority": "asset built after the R914 judge failure (#K2-351 window; #K2-352 C26/C27 follow-up)",
           "method": "per foreign In2 item: blocked x-interval [x-(r+clearance), x+(r+clearance)] over its y-extent; "
                     "a candidate is blocked iff the interval contains x AND the y-extent overlaps the corridor",
           "limits": "In2-layer geometry only - a real DRC must still confirm F.Cu / In5 / pour effects",
           "constraint": {"x_max": a.xmax, "clearance_mm": a.clearance, "via_radius_mm": a.via_radius,
                          "track_radius_mm": a.track_radius, "min_pitch_mm": a.min_pitch},
           "n_foreign_items": len(items), "nets": {}, "OWNER-ITEMS": 0}
    for nm, (yl, yh, padx, pady) in TARGET.items():
        free, x = [], a.xmin
        while x <= a.xmax + 1e-9:
            blocked = None
            for fx, lo, hi, fnet, r in items:
                if fnet == nm:
                    continue
                if abs(fx - x) < (r + a.clearance) and not (hi < yl - 1e-9 or lo > yh + 1e-9):
                    blocked = {"x": round(fx, 3), "net": fnet, "y": [round(lo, 3), round(hi, 3)]}
                    break
            if blocked is None:
                free.append(round(x, 3))
            x = round(x + STEP, 3)
        spans = []
        for v in free:
            if spans and abs(v - spans[-1][1] - STEP) < 1e-9:
                spans[-1][1] = v
            else:
                spans.append([v, v])
        rep["nets"][nm] = {"corridor_y": [yl, yh], "pad": [padx, pady], "free_x_spans_le_xmax": spans}
    print(json.dumps({"n_items": len(items), "free": {k: v["free_x_spans_le_xmax"] for k, v in rep["nets"].items()}},
                     ensure_ascii=False))
    if a.json_out:
        json.dump(rep, open(a.json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("wrote", a.json_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
