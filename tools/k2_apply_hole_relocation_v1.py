#!/usr/bin/env python3
"""k2_apply_hole_relocation_v1.py --- #K2-339: move a mounting hole AND its keepout square together.

A moved hole whose keepout square stays behind is a silent defect (registered M-ENG-HOLE-KEEPOUT-STALE: the
in-register board already has H2 H4 keepouts parked at their OLD positions).  This tool moves hole + keepout
as one atomic edit.  Read-only w.r.t. inputs; writes one board.

Usage (KiCad python): k2_apply_hole_relocation_v1.py --board <in> --hole H3=25.0713,35.0713 --out <out>
"""
import argparse, json, math, os, shutil, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--hole", required=True, help="REF=x,y")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import pcbnew as P
    ref, xy = a.hole.split("=")
    nx, ny = [float(v) for v in xy.split(",")]
    b = P.LoadBoard(a.board)
    fp = b.FindFootprintByReference(ref.strip())
    if fp is None:
        print(json.dumps({"error": "no such ref %s" % ref})); return 4
    ox, oy = P.ToMM(fp.GetPosition().x), P.ToMM(fp.GetPosition().y)
    dx, dy = nx - ox, ny - oy
    fp.SetPosition(P.VECTOR2I(int(round(nx * 1e6)), int(round(ny * 1e6))))
    moved_zones = []
    for z in b.Zones():
        nm = z.GetZoneName()
        if nm == "K2_HOLE_KEEPOUT_%s" % ref.strip():
            bb = z.GetBoundingBox()
            try:
                z.Move(P.VECTOR2I(int(round(dx * 1e6)), int(round(dy * 1e6))))
                moved_zones.append(nm)
            except Exception as e:                                    # fallback: move the outline points
                try:
                    o = z.Outline()
                    for i in range(o.OutlineCount()):
                        c = o.COutline(i)
                        for j in range(c.PointCount()):
                            pt = c.CPoint(j)
                            c.SetPoint(j, P.VECTOR2I(pt.x + int(round(dx * 1e6)), pt.y + int(round(dy * 1e6))))
                    moved_zones.append(nm + "(outline)")
                except Exception as e2:
                    print(json.dumps({"error": "zone move failed", "zone": nm, "e": str(e), "e2": str(e2)}))
                    return 5
            nb = z.GetBoundingBox()
            print(json.dumps({"zone": nm, "bbox_before": [P.ToMM(bb.GetLeft()), P.ToMM(bb.GetTop()),
                                                          P.ToMM(bb.GetRight()), P.ToMM(bb.GetBottom())],
                              "bbox_after": [round(P.ToMM(nb.GetLeft()), 3), round(P.ToMM(nb.GetTop()), 3),
                                             round(P.ToMM(nb.GetRight()), 3), round(P.ToMM(nb.GetBottom()), 3)]},
                             ensure_ascii=False))
    b.Save(a.out)
    pr = os.path.basename(a.board).replace(".kicad_pcb", ".kicad_pro")
    src_pro = os.path.join(os.path.dirname(os.path.abspath(a.board)), pr)
    if os.path.exists(src_pro):
        shutil.copyfile(src_pro, a.out.replace(".kicad_pcb", ".kicad_pro"))
    print(json.dumps({"hole": ref, "from": [round(ox, 3), round(oy, 3)], "to": [nx, ny],
                      "delta": [round(dx, 3), round(dy, 3)], "zones_moved": moved_zones, "out": a.out},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
