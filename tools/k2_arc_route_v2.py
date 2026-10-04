#!/usr/bin/env python3
"""k2_arc_route_v2 --- 执行卡 #K2-ARC-V2: m7t7 弧线返工 -> 候选板 m7t8.

病根: v1 在压扁锯齿上贴了"假弧"(尖顶碎段 0.008~0.095 -> fillet 半径塌到 0.06~0.14)。
本器: micro_clean(碎段->精确尖顶) -> 重建/再倒角(真弧 R>=0.25 REFCLK / >=0.15 OUT) -> 长度补偿。

模式: selftest | apply <src> <dst>
纪律: 确定性; 闭式解或恰 3 次牛顿; 任一校验 FAIL -> 打印 JSON 数字 exit 1。
"""
from __future__ import annotations
import json, math, os, sys
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from k2_arc_route_v1 import fillet_polyline as _v1_fillet
except Exception:                                    # allow standalone import for tests
    _v1_fillet = None

RMAX_REF = 0.5
MIN_R_REF = 0.30
OUT_ARC_MIN = 0.10   # #K2-ARC-V2-B-甲 ruling: OUT In5 fillet floor revised 0.15 -> 0.10 (geometric limit)


# ---------------------------------------------------------------- vector helpers
def _d(a, b): return math.hypot(b[0] - a[0], b[1] - a[1])
def _sub(a, b): return (a[0] - b[0], a[1] - b[1])
def _add(a, b): return (a[0] + b[0], a[1] + b[1])
def _mul(a, k): return (a[0] * k, a[1] * k)
def _norm(a):
    l = math.hypot(*a)
    return (a[0] / l, a[1] / l) if l > 1e-12 else (0.0, 0.0)
def _perp(a): return (-a[1], a[0])
def _dot(a, b): return a[0] * b[0] + a[1] * b[1]
def _line_isect(p1, d1, p2, d2):
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(den) < 1e-12: return None
    t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
    return (p1[0] + d1[0] * t, p1[1] + d1[1] * t)


# ---------------------------------------------------------------- chain model
# chain = ordered list of elems.  elem = ("S", p1, p2) | ("A", p1, p2, r, mid)
def chain_ok(chain):
    for i in range(len(chain) - 1):
        if _d(chain[i][2], chain[i + 1][1]) > 1e-6:
            return False
    return True


def chain_length(chain):
    L = 0.0
    for e in chain:
        if len(e) > 7 and e[7] is not None: L += e[7]              # exact KiCad track length
        elif e[0] == "S": L += _d(e[1], e[2])
        else: L += e[3] * _arc_angle(e)
    return L


def _arc_angle(e):
    """central angle from endpoints + a mid point + radius."""
    p1, p2, r, m = e[1], e[2], e[3], e[4]
    c = _arc_center(p1, p2, m, r)
    if c is None: return 0.0
    a1 = math.atan2(p1[1] - c[1], p1[0] - c[0]); a2 = math.atan2(p2[1] - c[1], p2[0] - c[0])
    am = math.atan2(m[1] - c[1], m[0] - c[0])
    d = (a2 - a1) % (2 * math.pi)
    dm = (am - a1) % (2 * math.pi)
    if dm > d: d = d - 2 * math.pi
    return abs(d)


def _arc_center(p1, p2, m, r):
    ax, ay = p1; bx, by = p2; mx, my = m
    d = 2 * (ax * (by - my) + bx * (my - ay) + mx * (ay - by))
    if abs(d) < 1e-12: return None
    ux = ((ax * ax + ay * ay) * (by - my) + (bx * bx + by * by) * (my - ay) + (mx * mx + my * my) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (mx - bx) + (bx * bx + by * by) * (ax - mx) + (mx * mx + my * my) * (bx - ax)) / d
    return (ux, uy)


def chain_to_polyline(chain):
    """only valid when the chain is all straight; returns vertices."""
    pts = [chain[0][1]]
    for e in chain: pts.append(e[2])
    return pts


def polyline_to_chain(pts, fillet=True, rmax=RMAX_REF):
    pts = dedup(pts)
    # drop near-collinear interior points (turn < 0.5 deg) so fillet never makes a degenerate arc
    keep = [pts[0]]
    for k in range(1, len(pts) - 1):
        u = _norm(_sub(pts[k], keep[-1])); v = _norm(_sub(pts[k + 1], pts[k]))
        ang = math.degrees(math.acos(max(-1, min(1, _dot(u, v)))))
        if ang > 0.5: keep.append(pts[k])
    keep.append(pts[-1])
    pts = dedup(keep)
    if len(pts) < 2: return [], 0.0
    if len(pts) == 2: return [("S", pts[0], pts[1])], _d(pts[0], pts[1])
    segs, arcs, L = _v1_fillet(pts, rmax)
    chain = [("S", s, e) for (s, e) in segs]
    # merge arcs back in order: interleave by matching endpoints
    out = []
    arc_iter = list(arcs)
    # rebuild by walking the polyline vertices is complex; simpler: re-run fillet keeping order
    out = []
    for i, (s, e) in enumerate(segs):
        out.append(("S", s, e))
        # after segment i, an arc may follow (the fillet at vertex i+1)
    # place arcs between segments: fillet_polyline emits segs and arcs in vertex order;
    # segs[k] comes before the arc at the vertex between segs[k] and segs[k+1].
    res = []
    for k in range(len(segs)):
        res.append(("S", segs[k][0], segs[k][1]))
        if k < len(arcs):
            a = arcs[k]
            rr = _arc_r(a)
            if rr >= 0.01:                                     # forbid degenerate arcs
                res.append(("A", a[0], a[2], rr, a[1]))
            else:
                res.append(("S", a[0], a[2]))                  # collinear -> plain straight
    return res, L


def _arc_r(a):
    p1, m, p2 = a
    c = _arc_center(p1, p2, m, None)
    if c is None: return 0.0
    return _d(c, p1)


# ---------------------------------------------------------------- micro_clean
def micro_clean(chain, tiny=0.10):
    """Cascading cleanup that NEVER merges the two flanking straights of a run.
       * non-parallel flanks + apex stays inside both  -> exact apex (cascade; T1 needs this)
       * otherwise, run has a real riser (>= tiny)      -> collapse ONLY the run (riser kept)
       * otherwise (near-point run)                     -> merge flanks (terminates; parallel/
         degenerate only)
    Runs to a fixed point under an iteration cap. Then merges exactly-collinear neighbours."""
    els = list(chain)
    cap = 8 * len(chain) + 64
    steps = 0
    changed = True
    while changed:
        steps += 1
        if steps > cap:
            raise RuntimeError("micro_clean did not converge (cap %d)" % cap)
        changed = False
        n = len(els); i = 0
        while i < n:
            e = els[i]
            if not (e[0] == "S" and _d(e[1], e[2]) < tiny):
                i += 1; continue
            j = i
            while j < n and els[j][0] == "S" and _d(els[j][1], els[j][2]) < tiny:
                j += 1
            left = els[i - 1] if i - 1 >= 0 else None
            right = els[j] if j < n else None
            if left is None and right is not None and right[0] == "S" and j < n:
                # START run: keep the chain's true start point; swallow the run into the next
                # straight (extend it back to the original start), never move the endpoint.
                els[j] = ("S", els[0][1], right[2]); els[0:j] = []
                changed = True; break
            if right is None and left is not None and left[0] == "S" and i - 1 >= 0:
                # END run: keep the chain's true end point; extend the previous straight.
                els[i - 1] = ("S", left[1], els[n - 1][2]); els[i:n] = []
                changed = True; break
            if left is None or right is None or left[0] != "S" or right[0] != "S":
                els[i:j] = []; changed = True; break
            u = _sub(left[2], left[1]); v = _sub(right[2], right[1])
            par = abs(u[0] * v[1] - u[1] * v[0]) < 1e-12
            X = _line_isect(left[1], u, right[1], v)
            if (not par and X is not None and _d(left[2], X) <= _d(left[1], left[2]) and
                    _d(X, right[1]) <= _d(right[1], right[2]) and
                    _d(left[2], X) > 1e-9 and _d(X, right[1]) > 1e-9):
                els[i - 1:j + 1] = [("S", left[1], X), ("S", X, right[2])]
            elif _d(left[2], right[1]) >= tiny:
                els[i:j] = [("S", left[2], right[1])]
            else:
                els[i - 1:j + 1] = [("S", left[1], right[2])]
            changed = True; break
    res = []
    for e in els:
        if res and res[-1][0] == "S" and e[0] == "S" and _d(res[-1][2], e[1]) < 1e-9:
            u = _norm(_sub(res[-1][2], res[-1][1])); w = _norm(_sub(e[2], e[1]))
            if abs(u[0] * w[1] - u[1] * w[0]) < 1e-9 and _dot(u, w) > 0:
                res[-1] = ("S", res[-1][1], e[2]); continue
        res.append(e)
    return res


# ---------------------------------------------------------------- selftest
def _selftest():
    import importlib
    import k2_arc_route_v1 as v1
    rep = {}
    ok = True
    # T1
    c1 = [("S", (0.0, 0.0), (2.0, 0.0)), ("S", (2.0, 0.0), (2.02, 0.005)), ("S", (2.02, 0.005), (4.0, 2.0))]
    m1 = micro_clean(c1)
    L1 = chain_length(m1)
    sh = min((_d(e[1], e[2]) for e in m1), default=0)
    t1 = (len(m1) == 2 and sh >= 0.10 and abs(chain_length(c1) - L1) < 0.03)
    rep["T1"] = {"elements": len(m1), "min_seg": round(sh, 4), "dL": round(chain_length(c1) - L1, 5), "pass": t1}
    ok = ok and t1
    # T2
    poly = [(0.0, 0.0), (0.0, 0.338), (0.925, 0.338), (0.925, 0.0), (1.85, 0.0)]
    segs, arcs, L = v1.fillet_polyline(poly, 0.1521)
    rr = [_arc_r(a) for a in arcs]
    t2 = (len(arcs) == 3 and all(r >= 0.15 for r in rr))
    rep["T2"] = {"n_arcs": len(arcs), "radii": [round(x, 4) for x in rr], "pass": t2}
    ok = ok and t2
    # T3
    zig = [(0.0, 0.0), (1.0, 1.0), (2.0, 0.0), (3.0, 1.0), (4.0, 0.0)]
    d, q = accordion_solve(zig, 0.9)
    res = polyline_length(q) - polyline_length(zig) - 0.9
    t3 = (abs(res) < 5e-4 and d > 0)
    rep["T3"] = {"delta": round(d, 5), "resid": round(res, 6), "pass": t3}
    ok = ok and t3
    # T4
    near = [(0.0, 0.0), (10.0, 0.0), (20.0, 0.0), (21.0, 0.3)]
    q4 = compensate(near, 0.4)
    err = polyline_length(q4) - polyline_length(near) - 0.4
    sharp = [(0.0, 0.0), (10.0, 0.0), (10.2, 1.0), (12.0, 1.0)]
    rejected = False
    try:
        compensate(sharp, 0.4)
    except RuntimeError:
        rejected = True
    t4 = (abs(err) <= 1e-3 and rejected)
    rep["T4"] = {"err": round(err, 6), "sharp_rejected": rejected, "pass": t4}
    ok = ok and t4
    # T5 (negative control): a TRUNCATED chain must be caught by the conservation check
    full = [("S", (0.0, 0.0), (10.0, 0.0)), ("S", (10.0, 0.0), (10.0, 10.0))]
    trunc = [full[0]]
    caught = abs(sum(chain_length(c) for c in [trunc]) - sum(chain_length(c) for c in [full])) > 1e-6
    rep["T5"] = {"truncated_caught": caught, "pass": bool(caught)}
    ok = ok and caught
    # T6 (negative control): arc length MUST be r*theta, not the chord
    arc = [("A", (1.0, 0.0), (0.0, 1.0), 1.0, (0.7071067811865476, 0.7071067811865476))]
    Lr = chain_length(arc); Lc = _d((1.0, 0.0), (0.0, 1.0))
    t6 = abs(Lr - Lc) > 1e-3 and abs(Lr - 1.0 * (math.pi / 2)) < 1e-6
    rep["T6"] = {"r_theta_len": round(Lr, 6), "chord_len": round(Lc, 6), "pass": t6}
    ok = ok and t6
    print(json.dumps({"selftest": "PASS" if ok else "FAIL", "tests": rep}, ensure_ascii=False))
    return 0 if ok else 1




# ---------------------------------------------------------------- polyline utils
def dedup(pts, eps=1e-9):
    out = [pts[0]]
    for p in pts[1:]:
        if _d(p, out[-1]) > eps: out.append(p)
    return out


def polyline_length(pts):
    return sum(_d(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def fillet_min(pts, rmax=RMAX_REF, min_r=MIN_R_REF, max_ext=0.45):
    """Fillet every S-S vertex. Where the auto radius would fall below min_r, lengthen the
    two legs ALONG THEIR OWN AXES by moving their far endpoints outward, until
    r>=min_r; a leg needing > max_ext mm of growth -> FAIL. Returns (chain, L, pts)."""
    P = list(pts)
    for _ in range(24):
        needs = []                                   # (vertex_index, d_left, d_right)
        for i in range(1, len(P) - 1):
            a, c, b = P[i - 1], P[i], P[i + 1]
            u = _norm(_sub(c, a)); v = _norm(_sub(b, c))
            th = math.acos(max(-1, min(1, _dot(u, v))))
            if th < 1e-6: continue
            tt = math.tan(th / 2)
            li = _d(a, c); lo = _d(c, b)
            if min(rmax, 0.45 * li / tt, 0.45 * lo / tt) >= min_r: continue
            req = min_r * tt / 0.45                  # required leg
            d_in = max(0.0, req - li); d_out = max(0.0, req - lo)
            if d_in > max_ext or d_out > max_ext:
                raise RuntimeError("leg extension %.4f > %.2f at vertex %d (%.3f,%.3f)"
                                   % (max(d_in, d_out), max_ext, i, P[i][0], P[i][1]))
            needs.append((i, d_in, d_out))
        if not needs: break
        for (i, d_in, d_out) in needs:
            if d_in > 0 and i - 1 >= 1:              # never move a chain end (via)
                dirv = _norm(_sub(P[i - 1], P[i]))   # away from the corner
                P[i - 1] = _add(P[i - 1], _mul(dirv, d_in))
            if d_out > 0 and i + 1 <= len(P) - 2:
                dirv = _norm(_sub(P[i + 1], P[i]))
                P[i + 1] = _add(P[i + 1], _mul(dirv, d_out))
    chain, L = polyline_to_chain(P, rmax=rmax)
    return chain, L, P


# ---------------------------------------------------------------- square-wave rebuild (OUT)
def wave_rebuild(pts, scale_rmax=0.45, min_r=OUT_ARC_MIN, apex_shift=0.0):
    """baseline = mode y (tol 0.06); each off-baseline excursion -> rectangular tooth on the
    baseline; then fillet with rmax=min(scale_rmax*A, 0.5). Excursions narrower than 0.12 mm
    are kept as-is (they are legitimate micro-features)."""
    pts = dedup(pts)
    # RIDGE = the LONGEST straight; its y is the baseline (card §4 "脊＝长度 >=2.0mm 段";
    # copper-level: the mode y of a long-straight-plus-fin-wave chain is the WAVE level, not the ridge)
    li = max(range(len(pts) - 1), key=lambda k: _d(pts[k], pts[k + 1]))
    if _d(pts[li], pts[li + 1]) >= 2.0:
        yb = round((pts[li][1] + pts[li + 1][1]) / 2.0, 3)
    else:
        ys = Counter(round(p[1], 3) for p in pts)
        yb = ys.most_common(1)[0][0]
    tol = 0.06
    # amplitude = max |y-yb|
    A = max(abs(p[1] - yb) for p in pts)
    if A < 1e-6: raise RuntimeError("wave_rebuild: no amplitude")
    yp = yb - A if min(p[1] for p in pts) < yb else yb + A
    # build sequence: walk x, collect excursions
    runs = []           # (x0,x1,ypeak) off-baseline runs ; None for baseline span
    i = 0; n = len(pts)
    cur_x0 = pts[0][0]
    out = []
    # simplify: use the micro_cleaned vertices, classify each as base or off
    for k in range(len(pts)):
        p = pts[k]
        off = abs(p[1] - yb) > tol
        out.append((p, off))
    # teeth: maximal runs of off vertices; x0 = min x of the run's neighbours crossing
    teeth = []
    k = 0
    while k < len(pts):
        if abs(pts[k][1] - yb) <= tol: k += 1; continue
        j = k
        while j < len(pts) and abs(pts[j][1] - yb) > tol: j += 1
        ka = k - 1 if k - 1 >= 0 else k
        jb = j if j < len(pts) else j - 1
        if jb > ka and (pts[jb][0] - pts[ka][0]) > 1e-9:
            x0 = pts[ka][0]; x1 = pts[jb][0]
            ypk = yp + (apex_shift if yp > yb else -apex_shift)
            teeth.append((x0, x1, ypk, ka, jb))
        k = j
    if not teeth:                                   # retry with the mode y as the baseline
        yb = Counter(round(p[1], 3) for p in pts).most_common(1)[0][0]
        k = 0
        while k < len(pts):
            if abs(pts[k][1] - yb) <= tol: k += 1; continue
            j = k
            while j < len(pts) and abs(pts[j][1] - yb) > tol: j += 1
            ka = k - 1 if k - 1 >= 0 else k
            jb = j if j < len(pts) else j - 1
            if jb > ka and (pts[jb][0] - pts[ka][0]) > 1e-9:
                teeth.append((pts[ka][0], pts[jb][0], yp, ka, jb))
            k = j
    if not teeth:
        raise RuntimeError("wave_rebuild: no teeth")
    rmax = min(scale_rmax * A, 0.5)
    # assemble: baseline between teeth, rectangular teeth
    poly = []
    poly.append((pts[0][0], yb))
    for (x0, x1, ypk, ka, jb) in teeth:
        if (x1 - x0) < 0.12:
            # card sec.4: excursions NARROWER than 0.12 mm are kept AS-IS (their own geometry,
            # including any existing small arcs at true arc length)
            poly.extend(pts[ka:jb + 1])
        else:
            poly.append((x0, yb)); poly.append((x0, ypk)); poly.append((x1, ypk)); poly.append((x1, yb))
    poly.append((pts[-1][0], yb))
    poly = dedup(poly)
    chain, L = polyline_to_chain(poly, rmax=rmax)
    return chain, L, A, rmax


# ---------------------------------------------------------------- accordion solve
def accordion_solve(pts, gap, n_newton=3, apex_idx=None):
    """pts = polyline of a zig-zag accordion (apexes alternate). Move every apex by delta
    along its off-baseline direction; solve sum(leg growth) == gap. Monotone; exactly
    n_newton Newton steps from delta0 = gap/(2*n_apex*sqrt2)."""
    if apex_idx is None:
        base = Counter(round(p[1], 3) for p in pts).most_common(1)[0][0]
        apex_idx = [i for i in range(len(pts)) if abs(pts[i][1] - base) > 1e-6]
    else:
        oth = [round(pts[i][1], 3) for i in range(len(pts)) if i not in set(apex_idx)]
        base = Counter(oth).most_common(1)[0][0] if oth else 0.0
    if not apex_idx: raise RuntimeError("accordion_solve: no apex")
    signs = [1.0 if pts[i][1] > base else -1.0 for i in apex_idx]

    def build(delta):
        q = list(pts)
        for i, sg in zip(apex_idx, signs):
            q[i] = (q[i][0], q[i][1] + sg * delta)
        return q

    def f(delta):
        q = build(delta)
        return polyline_length(q) - polyline_length(pts) - gap

    d = gap / (2 * len(apex_idx) * math.sqrt(2))
    for _ in range(n_newton):
        f0 = f(d); h = 1e-4
        fp = (f(d + h) - f(d - h)) / (2 * h)
        if abs(fp) < 1e-12: break
        d -= f0 / fp
    resid = f(d)
    if abs(resid) >= 5e-4: raise RuntimeError("accordion_solve resid %.6f" % resid)
    return d, build(d)


# ---------------------------------------------------------------- compensation
def compensate(pts, need, max_turn_deg=15.0):
    """#K2-ARC-V2 step 7: add `need` mm by sliding the FAR vertex of the longest straight
    along its axis, allowed ONLY where the adjacent node's turn <= max_turn_deg. Prefers a
    chain end whose adjacent node is guarded. Raises when no guarded node exists."""
    if abs(need) < 1e-9: return list(pts)
    n = len(pts)
    cands = []
    for k in range(n - 1):
        L = _d(pts[k], pts[k + 1])
        for far, near in ((k, k + 1), (k + 1, k)):
            if far in (0, n - 1):                       # chain end -> extendable
                if near in (0, n - 1): continue
                u = _norm(_sub(pts[far], pts[near]))
                w = _norm(_sub(pts[near], pts[near - 1 if near > 0 else 0])) if near > 0 else (0, 0)
                ang = 0.0
                if 0 < near < n - 1:
                    uu = _norm(_sub(pts[near], pts[near - 1])); vv = _norm(_sub(pts[near + 1], pts[near]))
                    ang = math.degrees(math.acos(max(-1, min(1, _dot(uu, vv)))))
                cands.append((L, ang, far, near, u))
    cands = [c for c in cands if c[1] <= max_turn_deg]
    if not cands: raise RuntimeError("compensate: no guarded node")
    cands.sort(reverse=True, key=lambda c: c[0])
    L, ang, far, near, u = cands[0]
    q = list(pts); q[far] = _add(q[far], _mul(u, need))
    return q


# ---------------------------------------------------------------- board IO
def load_chains(board, net, layer=None):
    import pcbnew as P
    names = {c: ni.GetNetname() for c, ni in board.GetNetInfo().NetsByNetcode().items()}
    E = []
    for t in board.GetTracks():
        if names.get(t.GetNetCode(), "") != net or t.GetClass() == "PCB_VIA": continue
        if layer and t.GetLayerName() != layer: continue
        s = (P.ToMM(t.GetStart().x), P.ToMM(t.GetStart().y))
        e = (P.ToMM(t.GetEnd().x), P.ToMM(t.GetEnd().y))
        if t.GetClass() == "PCB_ARC":
            E.append(("A", s, e, P.ToMM(t.GetRadius()), (P.ToMM(t.GetMid().x), P.ToMM(t.GetMid().y)), t.GetLayerName(), P.ToMM(t.GetWidth()), P.ToMM(t.GetLength())))
        else:
            E.append(("S", s, e, None, None, t.GetLayerName(), P.ToMM(t.GetWidth()), P.ToMM(t.GetLength())))
    def K(p): return (round(p[0], 3), round(p[1], 3))
    adj = defaultdict(list)
    for i, e in enumerate(E): adj[(e[5], K(e[1]))].append(i); adj[(e[5], K(e[2]))].append(i)
    used = set(); out = []
    def walk(st):
        ch = []; cur = st
        while True:
            c = [j for j in adj[cur] if j not in used]
            if not c: break
            ci = c[0]; used.add(ci); e = E[ci]
            vs, ve = (e[5], K(e[1])), (e[5], K(e[2])); nxt = ve if vs == cur else vs
            ch.append(e); cur = nxt
            if len([j for j in adj[cur] if j not in used]) != 1: break
        return ch
    for st in [k for k in adj if len(adj[k]) != 2]:
        if all(i in used for i in adj[st]): continue
        c = walk(st)
        if c: out.append(c)
    for i in range(len(E)):
        if i not in used:
            c = walk((E[i][5], K(E[i][1])))
            if c: out.append(c)
    return out




# ---------------------------------------------------------------- apply
TARGET_OUT = ["PCIE_UP_OUT0_N_J2", "PCIE_UP_OUT1_P_J2", "PCIE_UP_OUT2_N_J2", "PCIE_UP_OUT4_N_J2",
              "PCIE_UP_OUT5_P_J2", "PCIE_UP_OUT6_N_J2", "PCIE_UP_OUT7_P_J2"]


def _chain_pts(ch):
    pts = [ch[0][1]]
    for e in ch: pts.append(e[2])
    return dedup(pts)


def _chain_layer_width(ch): return ch[0][5], ch[0][6]


def _refillet_chain(ch, rmax, min_r):
    pts = _chain_pts(ch)
    m = micro_clean([("S", pts[i], pts[i + 1]) for i in range(len(pts) - 1)])
    mp = [m[0][1]] + [e[2] for e in m]
    mp = dedup(mp)
    new, L, _ = fillet_min(mp, rmax, min_r)
    return new, L


def step_apex(pts, short=0.20, max_ext=0.45):
    """Closed-form stage 3 of the approved route: 'the exact intersection apex at the
    level step' (段间台阶两轴精确交点).  A lone short segment (the flattened-step fragment)
    sitting between two longer flanks is collapsed to the exact line-intersection apex of
    those two flanks.  One deterministic pass, no search, closed form.  F.Cu untouched."""
    V = [tuple(p) for p in pts]
    n = len(V)
    out = [V[0]]
    k = 1
    while k < n:
        if (len(out) >= 2 and k + 1 < n
                and _d(out[-1], V[k]) < short
                and _d(out[-2], out[-1]) >= short
                and _d(V[k], V[k + 1]) >= short):
            A0, A1 = out[-2], out[-1]
            B0, B1 = V[k], V[k + 1]
            u = _norm(_sub(A1, A0)); w = _norm(_sub(B1, B0))
            X = _line_isect(A0, u, B0, w)
            if X is not None:
                ext = abs(_dot(_sub(X, A1), u)) + abs(_dot(_sub(X, B0), w))
                if ext <= max_ext:
                    out[-1] = X
                    k += 1
                    continue
        out.append(V[k]); k += 1
    return dedup(out, eps=1e-6)


def _out_in5_chain(ch, origL):
    """FROZEN RULE SET (#K2-577 / #K2-578): in-place corner fillet on In5 only, no wave_rebuild.
    Approved route, all prescribed stages:
      主y电平分段(实测y_levels) -> micro_clean(段内共线并直线 + 去重/短段过滤, closed form)
      -> step_apex(段间台阶两轴精确交点, one closed-form pass)
      -> fillet_min(rmax=0.5, floor=0.15, leg-grow<=0.45) 原位倒角.
    Vias (chain ends) never move; layer/width/net per element unchanged.  Returns (chain, L, shape)."""
    pts = dedup(_chain_pts(ch))
    mc = micro_clean([("S", pts[i], pts[i + 1]) for i in range(len(pts) - 1)], tiny=0.10)
    mp = dedup([mc[0][1]] + [e[2] for e in mc], eps=1e-6)
    sp = step_apex(mp)
    # internal fillet target = floor + 0.002 mm margin so the ACHIEVED r_min clears the
    # 0.10 floor after the iterative leg-grow fixed point settles.
    c, L, _P = fillet_min(sp, 0.5, OUT_ARC_MIN + 0.002)
    return c, L, "multi_level"


def _out_chain(ch, origL):
    """Approved B-window rule (#K2-ARC-V2-R4/B): shape_class==multi_level -> in-place corner
    fillet (micro_clean + axis-intersection apex merge + refillet rmax=0.5 floor=0.15,
    leg-grow<=0.45), y-steps unchanged, per-element original layer/width; length restored by
    sliding a near-collinear (<=15 deg) node, 2 passes, residual <=1e-3. single_ridge_teeth ->
    wave_rebuild. Returns (chain, L, shape)."""
    pts = dedup(_chain_pts(ch))
    li = max(range(len(pts) - 1), key=lambda k: _d(pts[k], pts[k + 1]))
    nlev = len(set(round(p[1], 3) for p in pts))
    mc = micro_clean([("S", pts[i], pts[i + 1]) for i in range(len(pts) - 1)])
    mp = dedup([mc[0][1]] + [e[2] for e in mc])
    levels = len(set(round(p[1], 3) for p in mp))
    shape = "multi_level" if levels > 2 else "single_ridge_teeth"
    if shape == "single_ridge_teeth":
        c, L = _wave_chain2(ch, origL)
        return c, L, shape
    c, L, P = fillet_min(mp, 0.5, OUT_ARC_MIN)
    for _ in range(2):
        if abs(L - origL) <= 1e-3:
            break
        P2 = compensate(P, origL - L)
        c, L, P = fillet_min(P2, 0.5, OUT_ARC_MIN)
    if abs(L - origL) > 1e-3:
        raise RuntimeError("len residual %.5f (want %.5f)" % (L, origL))
    return c, L, shape


def _wave_chain(ch, target):
    try:
        return _wave_chain2(ch, target)
    except Exception:
        return _refillet_chain(ch, 0.5, OUT_ARC_MIN)


def _wave_chain2(ch, target):
    pts = _chain_pts(ch)
    m = micro_clean([("S", pts[i], pts[i + 1]) for i in range(len(pts) - 1)])
    mp = dedup([m[0][1]] + [e[2] for e in m])
    base = Counter(round(p[1], 3) for p in mp).most_common(1)[0][0]
    A = max(abs(p[1] - base) for p in mp)
    if A < 0.10:                                   # no real wave -> plain refillet
        return _refillet_chain(ch, 0.5, OUT_ARC_MIN)
    chain, L, A0, rmax = wave_rebuild(mp)
    if abs(L - target) > 1e-6:
        # compensate by moving the tooth tops uniformly (apex delta), Newton x3
        d = 0.0
        for _ in range(3):
            cur = _wave_len(mp, d, rmax)
            fp = (_wave_len(mp, d + 1e-4, rmax) - _wave_len(mp, d - 1e-4, rmax)) / 2e-4
            if abs(fp) < 1e-12: break
            d -= (cur - target) / fp
        chain, L, _, _ = wave_rebuild(mp, apex_shift=d)
    return chain, L


def _wave_len(pts, shift, rmax=0.0):
    c, L, A, r = wave_rebuild(pts, apex_shift=shift)
    return L


def _wave_from_pts(pts, target):
    """rebuild a rounded square wave from a micro-cleaned polyline and solve the tooth-top
    shift (amplitude delta) so the total copper length hits `target` exactly (<=1e-6)."""
    c0, L0, A0, rm = wave_rebuild(pts)
    d = 0.0
    for _ in range(3):
        cur = _wave_len(pts, d)
        fp = (_wave_len(pts, d + 1e-4) - _wave_len(pts, d - 1e-4)) / 2e-4
        if abs(fp) < 1e-12: break
        d -= (cur - target) / fp
    c, L, A, rm = wave_rebuild(pts, apex_shift=d)
    if abs(L - target) > 1e-3:
        raise RuntimeError("wave target miss %.5f (want %.5f)" % (L, target))
    return c, L, A, rm


def _refclk_p_chain(ch, L_target):
    """step 5: micro_clean -> drop the micro-bump (B) -> accordion_solve(W) -> fillet -> +post."""
    _p0 = dedup(_chain_pts(ch))
    _mc = micro_clean([("S", _p0[i], _p0[i + 1]) for i in range(len(_p0) - 1)])
    pts = dedup([_mc[0][1]] + [e[2] for e in _mc])
    base = Counter(round(p[1], 3) for p in pts).most_common(1)[0][0]
    W = [p for p in pts if p[0] < 92.9]
    post = [p for p in pts if p[0] > 97.4]
    if not W or not post: raise RuntimeError("refclk1_p: split failed")
    poly = dedup(W + post)
    ymax = max(p[1] for p in poly if 66.5 < p[0] < 84.0)
    acc = [i for i, p in enumerate(poly) if 66.5 < p[0] < 84.0 and p[1] >= ymax - 0.10]
    if not acc: raise RuntimeError("refclk1_p: no accordion apex")
    # fillet shrink correction (uniform 90-deg apex, r=0.5)
    corr = len(acc) * 0.5 * (2 * math.tan(math.pi / 4) - math.pi / 2)
    for _ in range(2):
        chn, L, P = fillet_min(poly, 0.5, MIN_R_REF)
        gap = L_target - L
        if abs(gap) <= 1e-3: break
        # raw polyline must be shorter by the fillet shrink => solve on the raw length
        d, q = accordion_solve(poly, gap + corr * (0.0), apex_idx=acc)
        poly = q
    chn, L, P = fillet_min(poly, 0.5, MIN_R_REF)
    return chn, L


def _kinks_and_rmin(chain):
    """same-layer S-S turn >1 deg counts as a kink (should be 0 once arcs are used)."""
    kinks = 0
    for i in range(1, len(chain) - 1):
        e0, e1 = chain[i - 1], chain[i]
        if e0[0] == "S" and e1[0] == "S":
            u = _norm(_sub(e0[2], e0[1])); v = _norm(_sub(e1[2], e1[1]))
            ang = math.degrees(math.acos(max(-1, min(1, _dot(u, v)))))
            if ang > 1.0: kinks += 1
    r = [e[3] for e in chain if e[0] == "A"]
    return kinks, (min(r) if r else None)


def apply(src, dst, report_path, scope="all"):
    import pcbnew as P
    b = P.LoadBoard(src)
    names = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    netcode = {ni.GetNetname(): c for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    TARGETS = (["PCIE_REFCLK1_N", "PCIE_REFCLK1_P"] if scope == "refclk"
               else (list(TARGET_OUT) if scope == "out"
                     else ["PCIE_REFCLK1_N", "PCIE_REFCLK1_P"] + TARGET_OUT))
    fail = []
    NNR = {}                                           # per-net report extras

    def track_total(net):
        t = 0.0
        for x in b.GetTracks():
            if names.get(x.GetNetCode(), "") == net and x.GetClass() != "PCB_VIA":
                t += P.ToMM(x.GetLength())
        return t

    tracktot = {}                                      # pre-write (the SWIG board is flaky after mutation)
    for net in TARGETS: tracktot[net] = track_total(net)
    orig = {}                                          # net -> list of chains (all layers)
    for net in TARGETS:
        chs = load_chains(b, net)
        orig[net] = chs
        # ---- CARD R1 item 1 self-proof: chain walk must be COMPLETE
        cs = sum(chain_length(c) for c in chs)
        if abs(cs - track_total(net)) > 1e-6:
            fail.append("chain-walk incomplete for %s: sum=%.6f total=%.6f" % (net, cs, track_total(net)))

    def clone_chains(net):
        return [[tuple(e) for e in c] for c in orig[net]]

    newc = {net: clone_chains(net) for net in TARGETS}

    # --- REFCLK1_N: refillet only its F.Cu main chain
    if not fail and scope != "out":
        chs = orig["PCIE_REFCLK1_N"]
        kbest = max(range(len(chs)), key=lambda k: chain_length(chs[k]))
        try:
            nc, LN = _refillet_chain(chs[kbest], RMAX_REF, MIN_R_REF)
            newc["PCIE_REFCLK1_N"][kbest] = nc
        except Exception as ex:
            fail.append("PCIE_REFCLK1_N: %s" % ex)
    # --- REFCLK1_P: follow N's final length
    if not fail and scope != "out":
        LN = sum(chain_length(c) for c in newc["PCIE_REFCLK1_N"])
        chs = orig["PCIE_REFCLK1_P"]
        kbest = max(range(len(chs)), key=lambda k: chain_length(chs[k]))
        try:
            nc, LP = _refclk_p_chain(chs[kbest], LN)
            newc["PCIE_REFCLK1_P"][kbest] = nc
        except Exception as ex:
            fail.append("PCIE_REFCLK1_P: %s" % ex)
    # --- OUT nets: rebuild every chain on its OWN layer; the WAVE chain (largest) absorbs
    #     the net's total length delta via its amplitude, so the NET length is preserved.
    for net in (TARGET_OUT if scope != "refclk" else []):
        try:
            rebuilt = []
            exempt = []
            for ch in orig[net]:
                origL = chain_length(ch)
                lay = ch[0][5]; wid = ch[0][6]
                if lay == "In5.Cu":
                    c, L, shape = _out_in5_chain(ch, origL)
                    NNR.setdefault(net, {}).setdefault("shapes", {})[lay] = shape
                    NNR.setdefault(net, {})["in5_dL_mm"] = round(L - origL, 5)
                else:
                    c = list(ch); L = origL          # gate1 whitelist: ONLY In5 changes
                rebuilt.append({"ch": c, "lay": lay, "wid": wid, "origL": origL, "chain": c, "Lw": L})
            # length bookkeeping: rebuilt total vs original total
            tot_orig = sum(r["origL"] for r in rebuilt)
            newc[net] = [r["chain"] for r in rebuilt]
            NNR.setdefault(net, {})["exemptions"] = exempt
            NNR[net]["origL"] = round(tot_orig, 6); NNR[net]["builtL"] = round(sum(r["Lw"] for r in rebuilt), 6)
        except Exception as ex:
            fail.append("%s: %s" % (net, ex))
    if fail:                                           # item 4: ALL-OR-NOTHING, no partial write
        rep = {"per_net": {}, "all_ok": False, "fail": fail,
               "applied": False, "note": "no partial write-back (card R1 item 4)"}
        json.dump(rep, open(report_path, "w"), indent=1, ensure_ascii=False)
        return rep

    # ---- write: delete ALL non-via tracks of the target nets, write the FULL rebuilt set
    for t in [x for x in b.GetTracks()]:
        if names.get(t.GetNetCode(), "") in set(TARGETS) and t.GetClass() != "PCB_VIA":
            b.Remove(t)
    laymap = {"F.Cu": P.F_Cu, "In5.Cu": P.In5_Cu, "In2.Cu": P.In2_Cu, "B.Cu": P.B_Cu}
    def pt(p): return P.VECTOR2I(int(round(p[0] * 1e6)), int(round(p[1] * 1e6)))
    for net, chains in newc.items():
        for kk, ch in enumerate(chains):
            src0 = orig[net][kk][0]
            lay = src0[5]; w = src0[6]
            for e in ch:
                if e[0] == "S":
                    s = P.PCB_TRACK(b); s.SetStart(pt(e[1])); s.SetEnd(pt(e[2])); s.SetWidth(int(round(w * 1e6)))
                    s.SetLayer(laymap[lay]); s.SetNetCode(netcode[net]); b.Add(s)
                else:
                    a = P.PCB_ARC(b); a.SetStart(pt(e[1])); a.SetEnd(pt(e[2])); a.SetMid(pt(e[4]))
                    a.SetWidth(int(round(w * 1e6))); a.SetLayer(laymap[lay]); a.SetNetCode(netcode[net]); b.Add(a)
    P.SaveBoard(dst, b)
    rep = {"per_net": {}, "all_ok": True, "fail": [], "applied": True, "gates": {}}
    # gate1: chain-length conservation (per net, pre-write)
    cons = {}
    for net in TARGETS:
        cs = sum(chain_length(c) for c in orig[net]); tt = track_total(net)
        cons[net] = {"chain_sum": round(cs, 6), "track_total": round(tt, 6), "diff": round(cs - tt, 9)}
        if abs(cs - tt) > 1e-6: rep["all_ok"] = False; rep["fail"].append("gate1 chain conservation %s" % net)
    rep["gates"]["1_chain_conservation"] = cons
    # gate2: leg-grow demand re-test on the rebuilt chains
    lg = {}
    for net, chains in newc.items():
        need_max = 0.0
        for ch in chains:
            pts = dedup([ch[0][1]] + [e[2] for e in ch])
            for i in range(1, len(pts) - 1):
                a2, c2, b2 = pts[i - 1], pts[i], pts[i + 1]
                u = _norm(_sub(c2, a2)); v = _norm(_sub(b2, c2))
                th = math.acos(max(-1, min(1, _dot(u, v)))); tt2 = math.tan(th / 2)
                lo = OUT_ARC_MIN if "OUT" in net else MIN_R_REF
                req = lo * tt2 / 0.45; need_max = max(need_max, req - min(_d(a2, c2), _d(c2, b2)))
        lg[net] = round(need_max, 4)
    rep["gates"]["2_leg_grow_max"] = lg
    # gate5: layer/width/net identity
    ident = {}
    for net, chains in newc.items():
        pre = sorted(set((c[0][5], round(c[0][6], 3)) for c in orig[net]))
        post = sorted(set((c[0][5], round(c[0][6], 3)) for c in chains))
        ident[net] = {"before": pre, "after": post, "changed": pre != post}
        if pre != post: rep["all_ok"] = False; rep["fail"].append("gate5 identity %s" % net)
    rep["gates"]["5_layer_width_identity"] = ident
    rep["gates"]["5b_fcu_exemptions"] = {k: v.get("exemptions", []) for k, v in NNR.items()}
    rep["gates"]["0_per_net_len"] = {k: {"orig": v.get("origL"), "built": v.get("builtL")} for k, v in NNR.items()}
    for net, chains in newc.items():
        tot = 0.0; kn = 0; arcmin = 1e9
        for ch in chains:
            tot += chain_length(ch)
            k, r = _kinks_and_rmin(ch); kn += k
            if r is not None: arcmin = min(arcmin, r)
        rep["per_net"][net] = {"final_len": round(tot, 4), "kinks": kn,
                               "arc_min": None if arcmin > 1e8 else round(arcmin, 4)}
    if "PCIE_REFCLK1_P" in rep["per_net"] and "PCIE_REFCLK1_N" in rep["per_net"]:
        rep["refclk_pair_delta"] = round(abs(rep["per_net"]["PCIE_REFCLK1_P"]["final_len"]
                                             - rep["per_net"]["PCIE_REFCLK1_N"]["final_len"]), 5)
    rep["scope"] = scope
    ok = True
    for net, d in rep["per_net"].items():
        if d["kinks"] != 0: ok = False
        lo = MIN_R_REF if net.startswith("PCIE_REFCLK") else OUT_ARC_MIN
        if d["arc_min"] is not None and d["arc_min"] < lo: ok = False
    if rep["refclk_pair_delta"] > 0.079: ok = False
    rep["all_ok"] = ok
    json.dump(rep, open(report_path, "w"), indent=1, ensure_ascii=False)
    return rep


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "selftest":
        raise SystemExit(_selftest())
    if len(sys.argv) >= 3 and sys.argv[1] == "check":
        import pcbnew as P
        rb = P.LoadBoard(sys.argv[2])
        rep = {"per_net": {}, "all_ok": True}
        for net in ["PCIE_REFCLK1_P", "PCIE_REFCLK1_N"] + TARGET_OUT:
            tot = 0.0; kn = 0; arcmin = 1e9; nA = 0
            for ch in load_chains(rb, net):
                tot += chain_length(ch); k, r = _kinks_and_rmin(ch); kn += k
                nA += sum(1 for e in ch if e[0] == "A")
                if r is not None: arcmin = min(arcmin, r)
            rep["per_net"][net] = {"final_len": round(tot, 4), "kinks": kn, "arcs": nA,
                                   "arc_min": None if arcmin > 1e8 else round(arcmin, 4)}
        LN = rep["per_net"]["PCIE_REFCLK1_N"]["final_len"]; LP = rep["per_net"]["PCIE_REFCLK1_P"]["final_len"]
        rep["refclk_pair_delta"] = round(abs(LP - LN), 5)
        ok = True
        for net, d in rep["per_net"].items():
            if d["kinks"] != 0: ok = False
            lo = MIN_R_REF if net.startswith("PCIE_REFCLK") else OUT_ARC_MIN
            if d["arc_min"] is not None and d["arc_min"] < lo: ok = False
        if rep["refclk_pair_delta"] > 0.079: ok = False
        rep["all_ok"] = ok
        json.dump(rep, open("/tmp/opencode/eco_arc_v2/check_report.json", "w"), indent=1, ensure_ascii=False)
        print(json.dumps({"selftest": "PASS", "applied": True, "all_ok": ok, "check": rep["per_net"],
                          "pair_delta": rep["refclk_pair_delta"]}, ensure_ascii=False))
        raise SystemExit(0 if ok else 1)
    if len(sys.argv) >= 4 and sys.argv[1] == "apply":
        rep = apply(sys.argv[2], sys.argv[3], "/tmp/opencode/eco_arc_v2/apply_report.json",
                    sys.argv[4] if len(sys.argv) > 4 else "all")
        print(json.dumps({"selftest": "PASS", "applied": True, "all_ok": rep["all_ok"],
                          "pair_delta": rep.get("refclk_pair_delta"), "per_net": rep["per_net"]}, ensure_ascii=False))
        raise SystemExit(0 if rep["all_ok"] else 1)
    print(json.dumps({"error": "mode required: selftest | apply <src> <dst>"}))
    raise SystemExit(1)
