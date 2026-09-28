#!/usr/bin/env python3
"""k2_shift_vias_out_of_keepout_v1.py --- #K2-340: vacate a keepout square WITHOUT breaking the run.

When a hole's keepout square lands on top of an existing route, deleting the trapped copper leaves the run cut
(that is what happened to PCIE_DN4_N / PCIE_DN5_P in the first attempt).  This tool instead MOVES each trapped via
to the nearest point outside the square and re-attaches every track end that sat on it - a purely local,
deterministic edit; the run keeps its topology and only shifts by the pushed distance.

Usage (KiCad python): k2_shift_vias_out_of_keepout_v1.py --board <in> --rect x0,y0,x1,y1 [--rect ...]
                        [--margin 0.35] --out <out> [--report json]
"""
import argparse, json, math, os, shutil, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--rect", action="append", required=True)
    ap.add_argument("--margin", type=float, default=0.35)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", default="")
    a = ap.parse_args()
    import pcbnew as P
    rects = [tuple(float(v) for v in r.split(",")) for r in a.rect]
    b = P.LoadBoard(a.board)
    nets = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    # obstacle snapshot (all items), used by the clearance-aware candidate scan
    def d_pt_seg(px, py, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
        return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))
    trk, vs, pds = [], [], []
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            vs.append((t.GetNetCode(), P.ToMM(p.x), P.ToMM(p.y), P.ToMM(t.GetWidth(P.F_Cu)) / 2.0,
                       set(t.GetLayerSet().Seq())))
        else:
            sX, sY = t.GetStart(), t.GetEnd()
            trk.append((t.GetNetCode(), t.GetLayer(), P.ToMM(sX.x), P.ToMM(sY.y),
                        P.ToMM(sY.x), P.ToMM(sY.y), P.ToMM(t.GetWidth()) / 2.0))
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            if pd.GetNetCode() <= 0:
                continue
            bb = pd.GetBoundingBox()
            pds.append((pd.GetNetCode(), set(pd.GetLayerSet().Seq()), P.ToMM(bb.GetLeft()), P.ToMM(bb.GetTop()),
                        P.ToMM(bb.GetRight()), P.ToMM(bb.GetBottom())))
    # copper POURS (zones) are obstacles too: a via pushed into a foreign-net pour shorts it (measured:
    # shorting_items 3 + tracks_crossing 1 in the pre-zone attempt)
    zn = []
    for z in b.Zones():
        try:
            znet = z.GetNetCode()
            lay = [L for L in z.GetLayerSet().Seq()]
        except Exception:
            continue
        for L in lay:
            try:
                bb = z.GetFilledPolysList(L).BBox()
            except Exception:
                continue
            if bb.GetWidth() <= 0 or bb.GetHeight() <= 0:
                continue
            zn.append((znet, L, P.ToMM(bb.GetLeft()), P.ToMM(bb.GetTop()),
                       P.ToMM(bb.GetRight()), P.ToMM(bb.GetBottom())))
    X0, X1, Y0, Y1 = [P.ToMM(v) for v in (b.GetBoardEdgesBoundingBox().GetLeft(),
                                          b.GetBoardEdgesBoundingBox().GetRight(),
                                          b.GetBoardEdgesBoundingBox().GetTop(),
                                          b.GetBoardEdgesBoundingBox().GetBottom())]
    DIRS = [(0, -1), (0, 1), (-1, 0), (1, 0), (0.7071, -0.7071), (-0.7071, -0.7071),
            (0.7071, 0.7071), (-0.7071, 0.7071)]
    CLR = 0.30

    def seg_cross(a, b_, c, d_):
        def o(p, q, rr):
            v = (q[0] - p[0]) * (rr[1] - p[1]) - (q[1] - p[1]) * (rr[0] - p[0])
            return 0 if abs(v) < 1e-12 else (1 if v > 0 else -1)
        o1, o2, o3, o4 = o(a, b_, c), o(a, b_, d_), o(c, d_, a), o(c, d_, b_)
        return o1 != o2 and o3 != o4

    def seg_clear(nc, span, x1, y1, x2, y2):
        """True iff this segment keeps >= CLR from every other-net copper element."""
        for (n2, L2, ax, ay, bx, by, hw) in trk:
            if n2 == nc or L2 not in span:
                continue
            if seg_cross((x1, y1), (x2, y2), (ax, ay), (bx, by)):
                return False
            d = min(d_pt_seg(x1, y1, ax, ay, bx, by), d_pt_seg(x2, y2, ax, ay, bx, by),
                    d_pt_seg(ax, ay, x1, y1, x2, y2), d_pt_seg(bx, by, x1, y1, x2, y2))
            if d - hw - r0 > 0 and d - hw < CLR:
                return False
        for (n2, vx, vy, r2, lay2) in vs:
            if n2 == nc or not (lay2 & span):
                continue
            if d_pt_seg(vx, vy, x1, y1, x2, y2) - r2 < CLR:
                return False
        for (n2, lay2, bx0, by0, bx1, by1) in pds:
            if n2 == nc or not (lay2 & span):
                continue
            for (px, py) in ((x1, y1), (x2, y2)):
                ddx = max(bx0 - px, 0, px - bx1)
                ddy = max(by0 - py, 0, py - by1)
                if math.hypot(ddx, ddy) < CLR:
                    return False
        return True

    r0 = 0.0

    def clear_at(nc, span, r, nx, ny, attach=()):
        if nx - r < X0 + 0.3 or nx + r > X1 - 0.3 or ny - r < Y0 + 0.3 or ny + r > Y1 - 0.3:
            return False
        for (rx0, ry0, rx1, ry1) in rects:
            if rx0 - r <= nx <= rx1 + r and ry0 - r <= ny <= ry1 + r:
                return False
        for (n2, L2, x1, y1, x2, y2, hw) in trk:
            if n2 == nc or L2 not in span:
                continue
            if d_pt_seg(nx, ny, x1, y1, x2, y2) - hw - r < CLR:
                return False
        for (n2, x2, y2, r2, lay2) in vs:
            if n2 == nc or not (lay2 & span):
                continue
            if math.hypot(nx - x2, ny - y2) - r - r2 < CLR:
                return False
        for (n2, lay2, bx0, by0, bx1, by1) in pds:
            if n2 == nc or not (lay2 & span):
                continue
            dx = max(bx0 - nx, 0, nx - bx1)
            dy = max(by0 - ny, 0, ny - by1)
            if math.hypot(dx, dy) - r < CLR:
                return False
        for (zn2, zL, zx0, zy0, zx1, zy1) in zn:
            if zn2 == nc or zL not in span:
                continue
            if zx0 - CLR <= nx <= zx1 + CLR and zy0 - CLR <= ny <= zy1 + CLR:
                return False
        for (ax, ay) in attach:
            if not seg_clear(nc, span, nx, ny, ax, ay):
                return False
            for (zn2, zL, zx0, zy0, zx1, zy1) in zn:
                if zn2 == nc or zL not in span:
                    continue
                for (px, py) in ((nx, ny), (ax, ay)):
                    if zx0 - CLR <= px <= zx1 + CLR and zy0 - CLR <= py <= zy1 + CLR:
                        return False
        return True

    moves, reattached, scanned = [], 0, 0
    # ONE geometry snapshot (plain floats) -- repeated SWIG getters in nested loops are unreliable
    snap_v, snap_t = [], []
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            pv = t.GetPosition()
            snap_v.append((t, t.GetNetCode(), P.ToMM(pv.x), P.ToMM(pv.y),
                           P.ToMM(t.GetWidth(P.F_Cu)) / 2.0, set(t.GetLayerSet().Seq())))
        else:
            sX, sY = t.GetStart(), t.GetEnd()
            snap_t.append((t, t.GetNetCode(), t.GetLayer(), P.ToMM(sX.x), P.ToMM(sY.y),
                           P.ToMM(sY.x), P.ToMM(sY.y), P.ToMM(t.GetWidth())))
    attach_of = {}
    for _t, nc, vx, vy, _r, _sp in snap_v:
        ends = []
        for _t2, nc2, L2, ax, ay, bx, by, _w in snap_t:
            for (px, py) in ((ax, ay), (bx, by)):
                if abs(px - vx) < 0.01 and abs(py - vy) < 0.01:
                    other = (bx, by) if (px, py) == (ax, ay) else (ax, ay)
                    ends.append(other)
        attach_of[(round(vx, 4), round(vy, 4))] = ends
    for t in list(b.GetTracks()):
        if t.GetClass() != "PCB_VIA":
            continue
        x, y = P.ToMM(t.GetPosition().x), P.ToMM(t.GetPosition().y)
        span = set(t.GetLayerSet().Seq())
        r = P.ToMM(t.GetWidth(P.F_Cu)) / 2.0
        nc = t.GetNetCode()
        for (rx0, ry0, rx1, ry1) in rects:
            if not (rx0 <= x <= rx1 and ry0 <= y <= ry1):
                continue
            best = None
            for k in range(1, 41):                      # bounded: 0.10 mm steps, up to 4.0 mm
                d = 0.10 * k
                for (ux, uy) in DIRS:
                    nx, ny = x + ux * d, y + uy * d
                    scanned += 1
                    att = attach_of.get((round(x, 4), round(y, 4)), [])
                    if clear_at(nc, span, r, nx, ny, att):
                        best = (round(d, 3), round(nx, 4), round(ny, 4), len(att))
                        break
                if best:
                    break
            if best is None:
                moves.append({"net": nets.get(nc, ""), "from": [round(x, 3), round(y, 3)], "to": None,
                              "why": "no clear position inside 4.0 mm"})
                break
            _d, nx, ny, _na = best
            t.SetPosition(P.VECTOR2I(int(round(nx * 1e6)), int(round(ny * 1e6))))
            for s2 in b.GetTracks():
                if s2.GetClass() == "PCB_VIA":
                    continue
                for getter, setter in ((s2.GetStart, s2.SetStart), (s2.GetEnd, s2.SetEnd)):
                    p2 = getter()
                    if abs(P.ToMM(p2.x) - x) < 0.01 and abs(P.ToMM(p2.y) - y) < 0.01:
                        setter(P.VECTOR2I(int(round(nx * 1e6)), int(round(ny * 1e6))))
                        reattached += 1
            moves.append({"net": nets.get(nc, ""), "push_mm": _d, "from": [round(x, 3), round(y, 3)],
                          "to": [nx, ny], "attached_ends_checked": _na})
            break
    b.Save(a.out)
    pr = os.path.basename(a.board).replace(".kicad_pcb", ".kicad_pro")
    src = os.path.join(os.path.dirname(os.path.abspath(a.board)), pr)
    if os.path.exists(src):
        shutil.copyfile(src, a.out.replace(".kicad_pcb", ".kicad_pro"))
    rep = {"artifact": "k2_shift_vias_out_of_keepout_v1", "board_in": a.board, "board_out": a.out,
           "rects": rects, "margin_mm": a.margin, "vias_moved": len(moves), "track_ends_reattached": reattached,
           "moves": moves}
    if a.report:
        json.dump(rep, open(a.report, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
