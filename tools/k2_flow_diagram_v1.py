#!/usr/bin/env python3
"""k2_flow_diagram_v1.py --- C18 asset (#K2-336 sec.4.4: R1/R5 need "P1 quantification + a flow diagram").

Machine-generated signal-flow diagram (SVG) from the AS-BUILT board: device -> high-speed connectors, with the
per-group lane counts and routed-length ranges read off the board.  Read-only.  Turns R5 ("flow consistency")
from "unidentifiable on a render" into a machine artefact.

Usage: k2_flow_diagram_v1.py --board hw/k2_v4_8L.l10.kicad_pcb [--out <svg>]
"""
import argparse, collections, json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4", "L2", "FLOW_DIAGRAM_v1.svg")
HS = ("PCIE", "REFCLK")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--board", required=True); ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    import pcbnew
    b = pcbnew.LoadBoard(a.board)
    e = b.GetBoardEdgesBoundingBox()
    X0, X1, Y0, Y1 = [pcbnew.ToMM(v) for v in (e.GetLeft(), e.GetRight(), e.GetTop(), e.GetBottom())]
    nets = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    tl = collections.defaultdict(float)
    for t in b.GetTracks():
        nm = nets.get(t.GetNetCode(), "")
        if nm.startswith(HS) and t.GetClass() != "PCB_VIA":
            tl[nm] += math.hypot(t.GetEnd().x - t.GetStart().x, t.GetEnd().y - t.GetStart().y) / 1e6
    conn = collections.defaultdict(lambda: {"nets": [], "groups": collections.Counter()})
    for r, fp in fps.items():
        for p in fp.Pads():
            nm = nets.get(p.GetNetCode(), "")
            if nm.startswith(HS) and r not in conn or (nm.startswith(HS) and nm not in conn[r]["nets"]):
                if nm.startswith(HS):
                    conn[r]["nets"].append(nm)
                    g = nm.split("_")[1] if nm.startswith("PCIE_") else "REFCLK"
                    conn[r]["groups"][g] += 1
    chip = [r for r in conn if r.startswith("U")][0]
    S = 6.4   # px per mm
    W = int((X1 - X0) * S) + 40
    Hh = int((Y1 - Y0) * S) + 110

    def px(x, y):
        return (20 + (x - X0) * S, 40 + (y - Y0) * S)

    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (W, Hh, W, Hh),
           '<rect width="100%" height="100%" fill="#ffffff"/>',
           '<text x="20" y="22" font-family="monospace" font-size="13" fill="#111">K2 signal-flow diagram (machine-generated from %s)</text>' % os.path.basename(a.board)]
    x0, y0 = px(X0, Y0); x1, y1 = px(X1, Y1)
    out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#f3f6f4" stroke="#333" stroke-width="1.5"/>' % (x0, y0, x1 - x0, y1 - y0))
    c = px(*[pcbnew.ToMM(fps[chip].GetPosition().x), pcbnew.ToMM(fps[chip].GetPosition().y)])
    out.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#ffd54f" stroke="#333"/>' % (c[0] - 22, c[1] - 14, 44, 28))
    out.append('<text x="%.1f" y="%.1f" font-family="monospace" font-size="11" text-anchor="middle">%s (device)</text>' % (c[0], c[1] + 4, chip))
    legend = []
    for r in sorted(conn):
        if r == chip:
            continue
        p = px(pcbnew.ToMM(fps[r].GetPosition().x), pcbnew.ToMM(fps[r].GetPosition().y))
        side = "EAST" if p[0] > c[0] else "WEST"
        out.append('<rect x="%.1f" y="%.1f" width="10" height="%d" fill="#1e88e5" stroke="#0d47a1"/>' % (p[0] - 5, p[1] - 26, 52))
        out.append('<text x="%.1f" y="%.1f" font-family="monospace" font-size="10" text-anchor="middle">%s</text>' % (p[0], p[1] + 38, r))
        # arrow
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#c62828" stroke-width="2" marker-end="url(#ar)"/>' % (c[0], c[1], p[0], p[1]))
        lens = [tl[nm] for nm in conn[r]["nets"] if nm in tl]
        legend.append((r, side, dict(conn[r]["groups"]),
                       (round(min(lens), 2), round(max(lens), 2)) if lens else None))
    out.insert(2, '<defs><marker id="ar" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 z" fill="#c62828"/></marker></defs>')
    yy = Hh - 52
    out.append('<text x="20" y="%d" font-family="monospace" font-size="11" fill="#111">flow: %s (device) fans out to the HS connectors;  row = ref | side | lane-pair groups | routed length range (mm)</text>' % (Hh - 66, chip))
    for r, side, g, lr in legend:
        out.append('<text x="20" y="%d" font-family="monospace" font-size="11" fill="#111">  %-4s | %-4s | %-30s | %s</text>' % (yy, r, side, json.dumps(g), lr))
        yy += 13
    out.append('</svg>')
    open(a.out, "w", encoding="utf-8").write("\n".join(out))
    print(json.dumps({"wrote": a.out, "device": chip,
                      "flow": [{"connector": r, "side": s, "groups": g, "routed_len_min_max_mm": lr} for r, s, g, lr in legend]},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
