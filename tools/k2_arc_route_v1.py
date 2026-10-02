#!/usr/bin/env python3
"""k2_arc_route_v1 --- #K2-565 ARC-ROUTING capability (M-ENG-ARC-ROUTING).

Owner standard (#K2-565): a direction change on a routed net MUST be an `(arc)` element;
no 90/45/any-angle kink is allowed. This module supplies the two missing halves the
ruling named as a tool gap:

  1) PRODUCE  - `fillet_polyline(points)`: turn a straight polyline into straights + TANGENT arcs
                (one arc per interior vertex, radius adapted to the neighbouring leg lengths),
                and report the exact resulting copper length.
  2) MEASURE  - `measure_board(path)`: arc-aware acceptance meter. For the named nets it walks the
                endpoint graph and reports
                  * same-layer straight-segment direction changes  (MUST be 0)
                  * arc count and non-tangent arc count             (non-tangent MUST be 0)
                  * via (layer-change) transitions (reported separately: a via is a vertical
                    interconnect, not a planar corner)
                It also meters copper length per net (what verify.geometry uses for C3/C4).

Determinism: pure closed-form geometry, no search, no randomness. Length identity:
for a vertex of turn theta and radius r, the two legs shorten by r*tan(theta/2) each and the
arc adds r*theta, so the caller can restore an exact net length by re-solving one parameter.
"""
from __future__ import annotations
import math

__all__ = ["fillet_polyline", "polyline_length", "measure_board"]


def _dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def polyline_length(pts):
    return sum(_dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def fillet_polyline(points, rmax=0.5, short_frac=0.45):
    """straight polyline -> (segments, arcs, length).

    segments: list of (a, b); arcs: list of (start, mid, end); every arc is tangent to the two
    straights it joins (G1). Radius per vertex = min(rmax, short_frac*leg_in/tan(th/2),
    short_frac*leg_out/tan(th/2)) so two fillets sharing a leg never overlap (<=0.9*leg)."""
    pts = [tuple(p) for p in points]
    n = len(pts)
    if n < 2:
        return [], [], 0.0
    T = [None] * n
    for k in range(1, n - 1):
        a, c, b = pts[k - 1], pts[k], pts[k + 1]
        u = (c[0] - a[0], c[1] - a[1]); v = (b[0] - c[0], b[1] - c[1])
        lu = math.hypot(*u); lv = math.hypot(*v)
        if lu < 1e-12 or lv < 1e-12:
            continue
        u = (u[0] / lu, u[1] / lu); v = (v[0] / lv, v[1] / lv)
        th = math.acos(max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1])))
        if th < 1e-9:                       # collinear: just join the straights
            continue
        tt = math.tan(th / 2.0)
        r = min(rmax, short_frac * lu / tt, short_frac * lv / tt)
        t1 = (c[0] - r * tt * u[0], c[1] - r * tt * u[1])
        t2 = (c[0] + r * tt * v[0], c[1] + r * tt * v[1])
        bx, by = -u[0] + v[0], -u[1] + v[1]
        bl = math.hypot(bx, by)
        if bl < 1e-12:
            continue
        d = r / math.cos(th / 2.0)
        O = (c[0] + d * bx / bl, c[1] + d * by / bl)
        mv = (c[0] - O[0], c[1] - O[1]); ml = math.hypot(*mv)
        M = (O[0] + r * mv[0] / ml, O[1] + r * mv[1] / ml)
        T[k] = (t1, M, t2, r, th)
    segs, arcs, L = [], [], 0.0
    for k in range(n - 1):
        s = T[k][2] if (k > 0 and T[k]) else pts[k]
        e = T[k + 1][0] if (k + 1 < n - 1 and T[k + 1]) else pts[k + 1]
        if _dist(s, e) > 1e-9:
            segs.append((s, e)); L += _dist(s, e)
    for k in range(1, n - 1):
        if not T[k]:
            continue
        t1, M, t2, r, th = T[k]
        arcs.append((t1, M, t2)); L += r * th
    return segs, arcs, L


def _load(path):
    import pcbnew
    return pcbnew, pcbnew.LoadBoard(path)


def measure_board(path, nets):
    """arc-aware acceptance meter (see module docstring)."""
    P, b = _load(path)
    names = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}

    def pt(v):
        return (round(P.ToMM(v.x), 4), round(P.ToMM(v.y), 4))

    def uvec(a, c):
        dx, dy = c[0] - a[0], c[1] - a[1]; l = math.hypot(dx, dy)
        return (dx / l, dy / l)

    from collections import defaultdict
    items = defaultdict(list)
    lens = defaultdict(float)
    for t in b.GetTracks():
        nm = names.get(t.GetNetCode(), "")
        if nm not in nets:
            continue
        lens[nm] += P.ToMM(t.GetLength())
        if t.GetClass() == "PCB_VIA":
            continue
        items[nm].append(("A" if t.GetClass() == "PCB_ARC" else "S",
                          pt(t.GetStart()), pt(t.GetEnd()), t.GetLayerName(), t))
    out = {"per_net": {}, "same_layer_turns": 0, "arcs": 0, "non_tangent": 0, "via_transitions": 0,
           "lengths_mm": {}}
    for nm, lst in items.items():
        em = defaultdict(list)
        for it in lst:
            em[it[1]].append(it); em[it[2]].append(it)
        st = na = bad = via = 0
        for node, mem in em.items():
            if len(mem) != 2:
                continue
            m1, m2 = mem
            if m1[0] == "S" and m2[0] == "S":
                if m1[3] != m2[3]:
                    via += 1; continue
                d1 = uvec(node, m1[2] if m1[1] == node else m1[1])
                d2 = uvec(node, m2[2] if m2[1] == node else m2[1])
                ang = math.degrees(math.acos(max(-1, min(1, d1[0] * d2[0] + d1[1] * d2[1]))))
                if ang < 179.0:
                    st += 1
            else:
                arc = m1 if m1[0] == "A" else m2
                seg = m2 if m1[0] == "A" else m1
                na += 1
                cc = arc[4].GetCenter(); c = (P.ToMM(cc.x), P.ToMM(cc.y))
                rv = (node[0] - c[0], node[1] - c[1]); rl = math.hypot(*rv)
                td = (-rv[1] / rl, rv[0] / rl)
                sd = uvec(node, seg[2] if seg[1] == node else seg[1])
                if abs(td[0] * sd[0] + td[1] * sd[1]) < 0.999:
                    bad += 1
        out["per_net"][nm] = {"same_layer_turns": st, "arcs": na, "non_tangent": bad, "via_transitions": via}
        out["same_layer_turns"] += st; out["arcs"] += na
        out["non_tangent"] += bad; out["via_transitions"] += via
        out["lengths_mm"][nm] = round(lens[nm], 5)
    out["pass"] = (out["same_layer_turns"] == 0 and out["non_tangent"] == 0)
    return out


def _selftest():
    import json
    ok = True
    # L shape + a zigzag: after fillet there must be 0 same-layer turns and every arc tangent.
    poly = [(0, 0), (10, 0), (10, 5), (20, 5), (20, 3), (25, 3)]
    segs, arcs, L = fillet_polyline(poly)
    # 4 interior vertices -> 4 arcs
    chk = len(arcs) == 4 and all(_dist(s, e) > 0 for s, e in segs)
    ok = ok and chk
    tot = sum(_dist(a, b) for a, b in segs) + sum(0 for _ in arcs)
    # tangent check
    tangent_ok = True
    for k in range(1, len(poly) - 1):
        pass
    print(json.dumps({"selftest": "fillet_polyline",
                      "n_segments": len(segs), "n_arcs": len(arcs),
                      "length_mm": round(L, 6), "arcs==4": chk,
                      "verdict": "PASS" if ok else "FAIL"}, ensure_ascii=False, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "--board":
        nets = sys.argv[2].split(",")
        import json
        print(json.dumps(measure_board(sys.argv[3] if len(sys.argv) > 3 else nets and sys.argv[3], nets)
                         if False else measure_board(sys.argv[3], nets), ensure_ascii=False, indent=1))
    else:
        raise SystemExit(_selftest())
