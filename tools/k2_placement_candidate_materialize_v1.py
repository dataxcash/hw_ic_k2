#!/usr/bin/env python3
"""k2_placement_candidate_materialize_v1.py --- #K2-337 window C: draw a candidate placement onto a COPY of the
as-built board so the R1-R6 render review can look at it.  Read-only w.r.t. the repository; the output board is
a /tmp scratch file.  Copper/tracks on the copy are the AS-BUILT (stale) ones - this is a PLACEMENT-only artefact.

Usage: k2_placement_candidate_materialize_v1.py --board hw/k2_v4_8L.l10.kicad_pcb --candidates <json>
        --candidate C1 --out /tmp/k2dev/wc/C1.kicad_pcb
"""
import argparse, json, os, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import pcbnew
    cands = json.load(open(a.candidates, encoding="utf-8"))
    cand = next(c for c in cands["candidates"] if c["id"] == a.candidate)
    b = pcbnew.LoadBoard(a.board)
    moved = []
    for r, at in list(cand["refs"].items()) + list(cand["framework"]["holes"].items()):
        fp = b.FindFootprintByReference(r)
        if fp is None:
            continue
        cur = fp.GetPosition()
        if abs(pcbnew.ToMM(cur.x) - at[0]) < 1e-6 and abs(pcbnew.ToMM(cur.y) - at[1]) < 1e-6:
            continue
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(at[0]), pcbnew.FromMM(at[1])))
        moved.append(r)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    b.Save(a.out)
    print(json.dumps({"candidate": a.candidate, "out": a.out, "n_moved": len(moved), "moved": moved},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
