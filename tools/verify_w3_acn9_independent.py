#!/usr/bin/env python3
"""Independent re-computation of A-CN.9 (L5-exposed clearance suite) from the emitted W3 artifact
ONLY (route_geometry + pages[*].nodes/vias).  No import of the engine; own geometry kernels and own
thresholds.  Purpose: falsify the engine's self-reported FEASIBLE_ALL."""
import json, sys, math

MAIN = sys.argv[1]
d = json.load(open(MAIN))
TT, TT_ESC, VT, VT_ESC, VV = 0.38, 0.28, 0.4525, 0.3525, 0.525

def pt_seg(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 <= 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

def seg_seg(p1, p2, p3, p4):
    d1 = pt_seg(p1, p3, p4); d2 = pt_seg(p2, p3, p4)
    d3 = pt_seg(p3, p1, p2); d4 = pt_seg(p4, p1, p2)
    return min(d1, d2, d3, d4)

# ---- rebuild typed paths from pages[*].nodes ----
paths = {}      # (page, pol, kind) -> (layer, [pts])
vias = {}       # (x,y) -> set(layers), set(nets)
verts = {}      # (x,y) -> set(layers), set(nets)
for pg in d["pages"]:
    if pg.get("kind") != "data":
        continue
    pid = pg["page_id"]
    for pol in ("P", "N"):
        nd = pg["nodes"].get(pol) or []
        if len(nd) < 2:
            continue
        seq = [(round(float(x), 4), round(float(y), 4), lay) for x, y, lay in nd]
        # split into runs of constant layer
        runs = []
        for p in seq:
            if runs and runs[-1][0] == p[2]:
                runs[-1][1].append((p[0], p[1]))
            else:
                runs.append([p[2], [(p[0], p[1])]])
        kinds = []
        for i, (lay, pts) in enumerate(runs):
            kinds.append((lay, pts, i))
        for i, (lay, pts, _) in enumerate(kinds):
            kind = {0: "#fcu_pad", len(kinds) - 1: "#fcu_land"}.get(i, "mid%d" % i)
            paths[(pid, pol, kind)] = (lay, pts)
        for x, y, lay in seq:
            verts.setdefault((x, y), [set(), set()])
            verts[(x, y)][0].add(lay); verts[(x, y)][1].add(pid)
    for v in pg.get("vias", []):
        key = (round(float(v["x"]), 4), round(float(v["y"]), 4))
        vias.setdefault(key, [set(), set()])
        vias[key][0].update(v["layers"]); vias[key][1].add(pid)

def is_padaccess(kind):
    return "#fcu_pad" in kind or "#fcu_land" in kind

items = list(paths.items())
# ---- tt ----
v_tt = []
for i in range(len(items)):
    (p1, q1, k1), (l1, s1) = items[i]
    for j in range(i + 1, len(items)):
        (p2, q2, k2), (l2, s2) = items[j]
        if l1 != l2 or p1 == p2:
            continue
        thr = TT_ESC if (is_padaccess(k1) or is_padaccess(k2)) else TT
        for a in range(len(s1) - 1):
            for b in range(len(s2) - 1):
                dd = seg_seg(s1[a], s1[a + 1], s2[b], s2[b + 1])
                if dd < thr - 1e-9:
                    v_tt.append([p1, p2, round(dd, 4)])
# ---- vt: vertex vs same-layer segment of a foreign net ----
v_vt = []
for key, (lays, nets) in verts.items():
    for (p, q, k), (lay, s) in items:
        if lay not in lays or p in nets:
            continue
        thr = VT_ESC if is_padaccess(k) else VT
        for b in range(len(s) - 1):
            dd = pt_seg(key, s[b], s[b + 1])
            if dd < thr - 1e-9:
                v_vt.append([p, round(dd, 4), list(key)])
# ---- vv: drill-to-drill between multi-layer points of disjoint nets ----
vk = [k for k, (lays, nets) in vias.items() if len(lays) > 1]
v_vv = []
for i in range(len(vk)):
    for j in range(i + 1, len(vk)):
        if vias[vk[i]][1] & vias[vk[j]][1]:
            continue
        dd = math.hypot(vk[i][0] - vk[j][0], vk[i][1] - vk[j][1])
        if dd < VV - 1e-9:
            v_vv.append([list(vk[i]), list(vk[j]), round(dd, 4)])

print(json.dumps({
    "artifact": MAIN, "verdict_in_artifact": d.get("verdict"),
    "n_segments": sum(len(s) - 1 for _, (_, s) in items),
    "viol_track_track": len(v_tt), "viol_via_track": len(v_vt), "viol_via_via": len(v_vv),
    "sample_tt": v_tt[:6], "sample_vt": v_vt[:6], "sample_vv": v_vv[:6],
    "n_via_points": len(vk),
}, ensure_ascii=False, indent=1))
