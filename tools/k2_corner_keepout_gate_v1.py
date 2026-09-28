#!/usr/bin/env python3
"""k2_corner_keepout_gate_v1.py --- C21 asset (#K2-346 sec.6 / #K2-349): MECHANICAL CORNER-KEEPOUT GATE.

Adds the four corner 6x6 keepout squares to the scheme gate's criteria as a per-corner machine check, so a layout
that routes copper into a corner is caught AT THE SCHEME LAYER (the root cause of the whole H4 episode).

Measurement policy (authority-backed, after the C23 lesson):
  * tracks / vias / pads : EXACT geometric tests (segment sampling 0.05 mm; exact centre tests)
  * copper POURS         : NOT measured by my own polygon code (that reading contradicted the authority and is
                           registered as C23).  The POUR authority is kicad-cli DRC's own `items_not_allowed`
                           count per keepout zone name, passed in via --drc.
Verdict per corner = PASS iff 0 tracks AND 0 vias AND 0 pads AND 0 authority keepout items.

Usage (KiCad python): k2_corner_keepout_gate_v1.py --board <pcb> --drc <kicad-cli drc json> [--out json]
"""
import argparse, collections, json, math, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4", "L2", "C21_CORNER_KEEPOUT_GATE_v1.json")
HALF = 3.0
CORNERS = {"H3_TL": (25.0713, 35.0713), "H2_TR": (140.9287, 35.0713),
           "H1_BL": (25.0713, 76.9287), "H4_BR": (140.9287, 76.9287)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--drc", default="")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    import pcbnew as P
    b = P.LoadBoard(a.board)
    nets = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    # pour authority: per-zone items_not_allowed counts from the kicad-cli report
    auth = collections.Counter()
    if a.drc and os.path.isfile(a.drc):
        dj = json.load(open(a.drc, encoding="utf-8"))
        for v in dj.get("violations", []):
            if v.get("type") != "items_not_allowed":
                continue
            blob = json.dumps(v, ensure_ascii=False)
            m = re.search(r"K2_HOLE_KEEPOUT_(H\d)", blob)
            if m:
                auth[m.group(1)] += 1
    rep = {"artifact": "k2_corner_keepout_gate_v1", "ts": "2026-09-28",
           "authority": "C21 (#K2-346 sec.6, asset ordered after the H4 episode): mechanical corner-keepout gate",
           "criterion": "per corner: 0 tracks AND 0 vias AND 0 pads (exact tests) AND 0 kicad-cli items_not_allowed "
                        "for that keepout zone (pour authority)",
           "measurement_policy": {"tracks_vias_pads": "exact (segment sampling 0.05 mm; exact via/pad centre tests)",
                                 "pours": "NOT my polygon code (C23: my reading contradicted the authority) - the "
                                          "kicad-cli items_not_allowed count per zone name is the authority"},
           "board": a.board, "drc": a.drc or None, "corners": {}, "OWNER-ITEMS": 0}
    for name, (cx, cy) in CORNERS.items():
        x0, x1, y0, y1 = cx - HALF, cx + HALF, cy - HALF, cy + HALF
        trk, via, pad = collections.Counter(), collections.Counter(), collections.Counter()
        for t in b.GetTracks():
            nm = nets.get(t.GetNetCode(), "")
            if t.GetClass() == "PCB_VIA":
                x, y = P.ToMM(t.GetPosition().x), P.ToMM(t.GetPosition().y)
                if x0 <= x <= x1 and y0 <= y <= y1:
                    via[nm] += 1
            else:
                X1, Y1 = P.ToMM(t.GetStart().x), P.ToMM(t.GetStart().y)
                X2, Y2 = P.ToMM(t.GetEnd().x), P.ToMM(t.GetEnd().y)
                n = max(2, int(math.hypot(X2 - X1, Y2 - Y1) / 0.05))
                if any(x0 <= X1 + (X2 - X1) * i / n <= x1 and y0 <= Y1 + (Y2 - Y1) * i / n <= y1
                       for i in range(n + 1)):
                    trk[nm] += 1
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if p.GetNetCode() <= 0:
                    continue
                x, y = P.ToMM(p.GetPosition().x), P.ToMM(p.GetPosition().y)
                if x0 <= x <= x1 and y0 <= y <= y1:
                    pad[fp.GetReference()] += 1
        hole_ref = name.split("_")[0]
        ok = (not trk and not via and not pad and auth.get(hole_ref, 0) == 0)
        rep["corners"][name] = {"hole_ref": hole_ref, "centre": [cx, cy],
                                "bbox": [round(x0, 3), round(y0, 3), round(x1, 3), round(y1, 3)],
                                "tracks_in": dict(trk), "vias_in": dict(via), "pads_in": dict(pad),
                                "authority_items_not_allowed": auth.get(hole_ref, 0),
                                "verdict": "PASS" if ok else "FAIL"}
    rep["summary"] = {"PASS": [k for k, v in rep["corners"].items() if v["verdict"] == "PASS"],
                      "FAIL": [k for k, v in rep["corners"].items() if v["verdict"] == "FAIL"],
                      "gate_verdict": "PASS" if all(v["verdict"] == "PASS" for v in rep["corners"].values()) else "FAIL",
                      "scheme_gate_integration": "P8_mechanical_corner_keepout (SCHEME layer) - add to k2_scheme_gate_v2"}
    json.dump(rep, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"gate_verdict": rep["summary"]["gate_verdict"], "PASS": rep["summary"]["PASS"],
                      "FAIL": rep["summary"]["FAIL"],
                      "corners": {k: {"tracks": v["tracks_in"], "vias": v["vias_in"], "pads": v["pads_in"],
                                      "auth_items": v["authority_items_not_allowed"], "verdict": v["verdict"]}
                                  for k, v in rep["corners"].items()}}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
