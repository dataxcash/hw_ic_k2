#!/usr/bin/env python3
"""K2 · R513 — READ-ONLY layer-headroom audit (Solve() 0 calls; quota 0).

Human-plan prerequisite (see K2_R513_BLOCKER_REPORT_v1.md sec.3): the prescribed identity pairing
cannot be realised while all 16 lanes stay on ONE layer, because disjoint curves on one layer cannot
cross, so the pairing's order swaps (weaving) must be paid in lateral space.  The standard human fix
is to pay one or two of those swaps with a VIA HOP to a second routing layer.

This audit grounds that fix by measuring, per copper layer of the frozen board model, how much free
head-room exists in the four regions a swap needs:
  COMB    x 83.0..96.0  y 53.5..57.5   (A-side comb / weaving yard)
  BELT    x 96.0..133.0 y 57.5..66.0   (south belt where lanes can re-order)
  WALL    x 132.5..135.0 y 43.0..55.0  (wall gaps, x=133.59)
  FIELD   x 125.0..142.6 y 41.0..54.6  (J2 pad field)
For each (layer, box): free-fraction and the max number of parallel 0.435 mm lanes that fit across
the box's short side. This is a DESIGN-INPUT measurement only; it makes no routing claim.
"""
import json, os, sys, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import K2_R512_JOINT_MCF_NODECAP_FIX_v1 as R512
PREV = R512.PREV
RT_ = PREV.RT
P = R512.P

LAYERS = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]
BOXES = {"COMB": (83.0, 53.5, 96.0, 57.5), "BELT": (96.0, 57.5, 133.0, 66.0),
         "WALL": (132.5, 43.0, 135.0, 55.0), "FIELD": (125.0, 41.0, 142.6, 54.6)}


def main():
    m = json.load(open("/tmp/opencode/archer/model_l8.json"))
    HW = R512.HW
    rep = {"artifact": "k2_r513_layer_headroom_audit_v1",
           "ts": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-183 sec.3.5 (read-only) · monitor stop-order reply (Plan-before-implementation)",
           "boundaries": "Solve() 0 calls; quota 0; read-only obstacle-raster measurement; no model edits",
           "method": "obstacle raster built by the registered build_base() for each layer; free = ~base; "
                     "lanes_fit = floor(free_len / P) + 1 taken on the short side of each box",
           "boxes_mm": BOXES, "layers": {}}
    for layer in LAYERS:
        rast = RT_.Raster(m["bbox"], 0.03)
        base = RT_.build_base(rast, m, layer, set(), set(), HW, frozenset())
        free = ~base
        per = {}
        for nm, (x0, y0, x1, y1) in BOXES.items():
            i0 = max(0, int((x0 - rast.X0) / rast.step)); i1 = min(rast.NX - 1, int((x1 - rast.X0) / rast.step))
            j0 = max(0, int((y0 - rast.Y0) / rast.step)); j1 = min(rast.NY - 1, int((y1 - rast.Y0) / rast.step))
            sub = free[i0:i1 + 1, j0:j1 + 1]
            if sub.size == 0:
                continue
            wid_mm = (i1 - i0) * rast.step; hei_mm = (j1 - j0) * rast.step
            short_mm = min(wid_mm, hei_mm)
            # longest free run across the short side (max lanes that could pass the box)
            best = 0
            arr = sub if hei_mm <= wid_mm else sub.T
            for line in arr:
                idx = np.nonzero(line)[0]
                if len(idx) == 0:
                    continue
                run = 1; mx = 1
                for k in range(1, len(idx)):
                    run = run + 1 if idx[k] == idx[k - 1] + 1 else 1
                    mx = max(mx, run)
                best = max(best, mx)
            best_mm = best * rast.step
            per[nm] = {"free_fraction": round(float(sub.mean()), 3),
                       "max_free_run_across_short_side_mm": round(best_mm, 3),
                       "lanes_fit_pitch_0p435": int(best_mm // P) + 1 if best_mm > 0 else 0}
        rep["layers"][layer] = per
    json.dump(rep, open(os.path.join(HERE, "K2_R513_LAYER_HEADROOM_AUDIT_v1.json"), "w"),
              ensure_ascii=False, indent=1, default=str)
    print("%-8s %s" % ("layer", " ".join("%-22s" % b for b in BOXES)))
    for layer in LAYERS:
        row = []
        for b in BOXES:
            d = rep["layers"][layer].get(b, {})
            row.append("%5.2f/%6.2fmm/L%2d" % (d.get("free_fraction", 0), d.get("max_free_run_across_short_side_mm", 0), d.get("lanes_fit_pitch_0p435", 0)))
        print("%-8s %s" % (layer, " ".join("%-22s" % c for c in row)))
    print("(cell = free_fraction / longest free run across short side / lanes at 0.435 pitch)")


if __name__ == "__main__":
    main()
