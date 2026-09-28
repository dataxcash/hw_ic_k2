#!/usr/bin/env python3
"""k2_reroute_affected_v2.py --- C17 v1 (obstacle-aware re-route).  #K2-338 next-window hard deliverable.

For a placement change this driver:
  1. applies the move  (phase RIP)
  2. RIP-UP BY CLIPPING: an affected-net track crossing the damage zone is SPLIT at the zone boundary and only
     the inside part is deleted (v0 deleted whole tracks -> dangling stubs far away).  Vias are never ripped.
  3. kicad-cli DRC on the damaged board -> the unconnected gaps
  4. hands the gaps to the in-register OBSTACLE-AWARE maze router (tools/k2_p4_mroute_v1.py: exact layer-aware
     seg_exact / span-aware via_exact release gate) which BRIDGES them  (phase ROUTE, external)
  5. SNAP: new track endpoints are moved exactly onto the new via centres (kills "not centered on via")
  6. kicad-cli DRC on the final board -> acceptance: routing diff != 0, ZERO NEW violations vs the baseline,
     intra-pair skew 8/8 <= 0.15, unconnected == 0

v0 (k2_reroute_affected_v1.py) = 652 violations on a 3-net smoke (obstacle-blind).  This uses the exact gate.

Phases are separate PROCESSES on purpose: pcbnew/SWIG state gets corrupted by in-process track removal, and the
phases are then individually re-runnable and auditable.

Usage (KiCad python):
  k2_reroute_affected_v2.py --board <in> --moved U5=+2.0,0 --baseline-drc <base.json> \
      --work <dir> --out <final.kicad_pcb> --report <json>          # orchestrator (default)
"""
import argparse, collections, hashlib, json, math, os, re, shutil, subprocess, sys, uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MROUTE = os.path.join(ROOT, "tools", "k2_p4_mroute_v1.py")
ROUTER_FLOOR = os.path.join(ROOT, "tools", "k2_reroute_router_floor_v1.py")
KICAD_CLI = os.environ.get("KICAD_CLI", "/tmp/k2kicad/squashfs-root/usr/bin/kicad-cli")
HS_PAIRS = [("PCIE_UP_OUT%d_P_J2" % i, "PCIE_UP_OUT%d_N_J2" % i) for i in range(8)]
SELF = os.path.abspath(__file__)


def _pcbnew():
    import pcbnew
    return pcbnew


def V(P, x, y):
    return P.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6)))


def clip_keep_outside(x1, y1, x2, y2, discs):
    """Sub-segments of (x1,y1)-(x2,y2) lying OUTSIDE every disc (cx,cy,r)."""
    dx, dy = x2 - x1, y2 - y1
    if math.hypot(dx, dy) < 1e-9:
        return []
    inside = []
    for (cx, cy, r) in discs:
        fx, fy = x1 - cx, y1 - cy
        A = dx * dx + dy * dy
        B = 2 * (fx * dx + fy * dy)
        C = fx * fx + fy * fy - r * r
        disc = B * B - 4 * A * C
        if disc <= 0:
            continue
        s = math.sqrt(disc)
        t0, t1 = max(0.0, min(1.0, (-B - s) / (2 * A))), max(0.0, min(1.0, (-B + s) / (2 * A)))
        if t1 > t0:
            inside.append((t0, t1))
    if not inside:
        return [(x1, y1, x2, y2)]
    inside.sort()
    merged = []
    for (t0, t1) in inside:
        if merged and t0 <= merged[-1][1] + 1e-9:
            merged[-1] = (merged[-1][0], max(merged[-1][1], t1))
        else:
            merged.append((t0, t1))
    out, cur = [], 0.0
    for (t0, t1) in merged:
        if t0 - cur > 1e-6:
            out.append((x1 + dx * cur, y1 + dy * cur, x1 + dx * t0, y1 + dy * t0))
        cur = max(cur, t1)
    if 1.0 - cur > 1e-6:
        out.append((x1 + dx * cur, y1 + dy * cur, x2, y2))
    return [(ax, ay, bx, by) for (ax, ay, bx, by) in out if math.hypot(bx - ax, by - ay) >= 0.02]


def clip_keep_outside_rect(x1, y1, x2, y2, rects):
    """Sub-segments of (x1,y1)-(x2,y2) lying OUTSIDE every axis-aligned rect (rx0,ry0,rx1,ry1)."""
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    if L < 1e-9:
        return []
    inside = []
    for (rx0, ry0, rx1, ry1) in rects:
        t0, t1 = 0.0, 1.0
        ok = True
        for (p0, d, lo, hi) in ((x1, dx, rx0, rx1), (y1, dy, ry0, ry1)):
            if abs(d) < 1e-12:
                if p0 < lo or p0 > hi:
                    ok = False
                    break
            else:
                ta, tb = (lo - p0) / d, (hi - p0) / d
                ta, tb = min(ta, tb), max(ta, tb)
                t0, t1 = max(t0, ta), min(t1, tb)
        if ok and t1 > t0:
            inside.append((t0, t1))
    if not inside:
        return [(x1, y1, x2, y2)]
    inside.sort()
    merged = []
    for (t0, t1) in inside:
        if merged and t0 <= merged[-1][1] + 1e-9:
            merged[-1] = (merged[-1][0], max(merged[-1][1], t1))
        else:
            merged.append((t0, t1))
    out, cur = [], 0.0
    for (t0, t1) in merged:
        if t0 - cur > 1e-6:
            out.append((x1 + dx * cur, y1 + dy * cur, x1 + dx * t0, y1 + dy * t0))
        cur = max(cur, t1)
    if 1.0 - cur > 1e-6:
        out.append((x1 + dx * cur, y1 + dy * cur, x2, y2))
    return [(ax, ay, bx, by) for (ax, ay, bx, by) in out if math.hypot(bx - ax, by - ay) >= 0.02]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="all", choices=["all", "rip", "stitch", "snap", "repair", "normalize", "verify"])
    ap.add_argument("--rects", default="[]", help="internal: JSON list of [x0,y0,x1,y1] passed to the rip phase")
    ap.add_argument("--board", required=True)
    ap.add_argument("--moved", action="append", default=[])
    ap.add_argument("--clear-rect", action="append", default=[],
                    help="x0,y0,x1,y1 -- additionally rip the copper of ANY net inside this rect (a keepout square "
                         "that a moved hole drags with it must be vacated, then re-connected)")
    ap.add_argument("--radius", type=float, default=3.0)
    ap.add_argument("--margin", type=float, default=3.0, help="router search window (mm) around the gap")
    ap.add_argument("--baseline-drc", default="")
    ap.add_argument("--work", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--skew-limit", type=float, default=0.15)
    ap.add_argument("--clearance-floor", type=float, default=0.20,
                    help="minimum inter-net copper clearance the re-router must honour; the ACCEPTANCE authority is "
                         "kicad-cli DRC, whose project netclass default is 0.20 mm, while the frozen drc_rules.json "
                         "model says 0.10 mm for LOW_SPEED/GND (M-ENG-CLEARANCE-MODEL-DIVERGENCE)")
    ap.add_argument("--stage1", default="")
    a = ap.parse_args()
    os.makedirs(a.work, exist_ok=True)
    if not a.moved and not a.clear_rect and a.phase in ("all", "rip"):
        print(json.dumps({"error": "need --moved and/or --clear-rect"})); return 4
    if a.phase == "all":
        return orchestrate(a)
    P = _pcbnew()
    if a.phase == "rip":
        return phase_rip(a, P)
    if a.phase == "stitch":
        return phase_stitch(a, P)
    if a.phase == "snap":
        return phase_snap(a, P)
    if a.phase == "repair":
        return phase_repair(a, P)
    if a.phase == "normalize":
        return phase_normalize(a)
    return phase_verify(a, P)


def _pro(a):
    """The design .kicad_pro to sit next to an output board (net classes live there)."""
    src = getattr(a, "stage1", "") or a.board
    want = os.path.basename(src).replace(".kicad_pcb", ".kicad_pro")
    p = os.path.join(a.work, want)
    if os.path.exists(p):
        return p
    for f in sorted(os.listdir(a.work)):
        if f.endswith(".kicad_pro"):
            return os.path.join(a.work, f)
    return None


def _mirror(a):
    hw = os.path.dirname(os.path.abspath(a.board))
    for f in os.listdir(hw):
        if f == "fp-lib-table" or f == "lib" or f.endswith(".kicad_pro"):
            src, dst = os.path.join(hw, f), os.path.join(a.work, f)
            if os.path.exists(dst) or os.path.islink(dst):
                continue
            (os.symlink(src, dst) if os.path.isdir(src) else shutil.copyfile(src, dst))


def phase_rip(a, P):
    _mirror(a)
    b = P.LoadBoard(a.board)
    nets = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    rects = [tuple(float(v) for v in r) for r in (json.loads(a.rects) if a.rects else [])]
    discs, aff, moved_info = [], set(), []
    for spec in a.moved:
        ref, d = spec.split("=")
        dx, dy = [float(x) for x in d.replace("+", "").split(",")]
        fp = b.FindFootprintByReference(ref.strip())
        if fp is None:
            print(json.dumps({"error": "no such ref %s" % ref})); return 4
        old = [(P.ToMM(p.GetPosition().x), P.ToMM(p.GetPosition().y)) for p in fp.Pads() if p.GetNetCode() > 0]
        fp.SetPosition(V(P, P.ToMM(fp.GetPosition().x) + dx, P.ToMM(fp.GetPosition().y) + dy))
        new = [(P.ToMM(p.GetPosition().x), P.ToMM(p.GetPosition().y)) for p in fp.Pads() if p.GetNetCode() > 0]
        for p in fp.Pads():
            if p.GetNetCode() > 0:
                aff.add(p.GetNetCode())
        for (x, y) in old + new:
            discs.append((x, y, a.radius))
        moved_info.append({"ref": ref.strip(), "d_mm": [dx, dy],
                           "nets": sorted({nets[p.GetNetCode()] for p in fp.Pads() if p.GetNetCode() > 0})})
    # nets that live inside a clear-rect also count as affected (their copper must vacate the keepout)
    if rects:
        for t in b.GetTracks():
            x1, y1 = P.ToMM(t.GetStart().x), P.ToMM(t.GetStart().y)
            x2, y2 = P.ToMM(t.GetEnd().x), P.ToMM(t.GetEnd().y)
            for (rx0, ry0, rx1, ry1) in rects:
                if min(x1, x2) <= rx1 and max(x1, x2) >= rx0 and min(y1, y2) <= ry1 and max(y1, y2) >= ry0:
                    aff.add(t.GetNetCode())
                    break
    removed = kept = 0
    detail = []
    for t in list(b.GetTracks()):
        if t.GetClass() == "PCB_VIA":
            if t.GetNetCode() in aff:                      # a via inside a keepout square cannot stay
                vx, vy = P.ToMM(t.GetPosition().x), P.ToMM(t.GetPosition().y)
                if any(rx0 <= vx <= rx1 and ry0 <= vy <= ry1 for (rx0, ry0, rx1, ry1) in rects):
                    b.Remove(t); removed += 1
                    detail.append({"net": nets.get(t.GetNetCode()), "kind": "via", "at": [round(vx, 3), round(vy, 3)]})
            continue
        if t.GetNetCode() not in aff:
            continue
        x1, y1 = P.ToMM(t.GetStart().x), P.ToMM(t.GetStart().y)
        x2, y2 = P.ToMM(t.GetEnd().x), P.ToMM(t.GetEnd().y)
        if rects:
            hitr = any(min(x1, x2) <= rx1 and max(x1, x2) >= rx0 and min(y1, y2) <= ry1 and max(y1, y2) >= ry0
                       for (rx0, ry0, rx1, ry1) in rects)
            if hitr:
                keep = clip_keep_outside_rect(x1, y1, x2, y2, rects)
                lay_, nc_, w_ = t.GetLayer(), t.GetNetCode(), t.GetWidth()
                b.Remove(t); removed += 1
                for (ax, ay, bx, by) in keep:
                    n = P.PCB_TRACK(b)
                    n.SetStart(V(P, ax, ay)); n.SetEnd(V(P, bx, by)); n.SetLayer(lay_); n.SetWidth(w_); n.SetNetCode(nc_)
                    b.Add(n); kept += 1
                detail.append({"net": nets.get(nc_), "kind": "rect-clip", "at": [round(x1, 3), round(y1, 3)],
                               "kept_parts": len(keep)})
                continue
        hit = False
        for (cx, cy, r) in discs:                       # cheap filter then exact clip
            if min(math.hypot(x1 - cx, y1 - cy), math.hypot(x2 - cx, y2 - cy),
                   math.hypot((x1 + x2) / 2 - cx, (y1 + y2) / 2 - cy)) <= r + math.hypot(x2 - x1, y2 - y1) / 2:
                hit = True
                break
        if not hit:
            continue
        lay, nc, w = t.GetLayer(), t.GetNetCode(), t.GetWidth()
        keep = clip_keep_outside(x1, y1, x2, y2, discs)
        b.Remove(t)
        removed += 1
        for (ax, ay, bx, by) in keep:
            n = P.PCB_TRACK(b)
            n.SetStart(V(P, ax, ay)); n.SetEnd(V(P, bx, by)); n.SetLayer(lay); n.SetWidth(w); n.SetNetCode(nc)
            b.Add(n); kept += 1
        detail.append({"net": nets.get(nc), "layer": lay, "len_mm": round(math.hypot(x2 - x1, y2 - y1), 3),
                       "kept_parts": len(keep)})
    st = os.path.join(a.work, os.path.basename(a.board))
    P.SaveBoard(st, b)
    pr = _pro(a)
    if pr:
        dst = st.replace(".kicad_pcb", ".kicad_pro")
        if os.path.abspath(pr) != os.path.abspath(dst):
            shutil.copyfile(pr, dst)
    json.dump({"affected_nets": sorted(nets[n] for n in aff), "moves": moved_info,
               "tracks_removed": removed, "parts_kept": kept, "detail": detail,
               "affected_netcodes": sorted(aff), "stage1": st},
              open(os.path.join(a.work, "rip.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"phase": "rip", "affected_nets": sorted(nets[n] for n in aff),
                      "removed": removed, "kept": kept}))
    return 0


def _load_mroute():
    import importlib.util
    sp = importlib.util.spec_from_file_location("k2mr", MROUTE)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    return m


def phase_stitch(a, P):
    """LOCAL REPAIR: reconnect every ISLAND of each affected net to its NEAREST other island with the
    in-register exact gate (seg_exact / via_exact).  This replaces DRC's canonical-anchor pairing, which picks the
    FAR end of a long remnant and makes the router wander 16-21 mm across layers (that wander is what produced the
    dangling/off-centre residue).  Deterministic minimal-spanning repair, bounded passes per net.
    """
    mr = _load_mroute()
    # ACCEPTANCE AUTHORITY = kicad-cli DRC (project netclass clearance 0.20 mm).  The in-register gate uses the
    # frozen drc_rules.json model, which says 0.10 mm for LOW_SPEED/GND (M-ENG-CLEARANCE-MODEL-DIVERGENCE);
    # raise the gate floor so the re-router is never looser than the acceptance authority.
    _cv = mr.cv
    _orig_req = _cv._req
    _FLOOR = float(getattr(a, "clearance_floor", 0.20))
    _cv._req = lambda x, y: max(_orig_req(x, y), _FLOOR)
    rip = json.load(open(os.path.join(a.work, "rip.json"), encoding="utf-8"))
    affnets = set(rip["affected_nets"])
    b = P.LoadBoard(a.board)
    ctx = mr.f3.Ctx(b)
    holes = []
    for u, v in ctx.vias.items():
        holes.append((v["x"], v["y"], v["hole"], v["net"], frozenset(v["lay"])))
    for u, pd in ctx.pads.items():
        if pd["hole"] > 0:
            holes.append((pd["x"], pd["y"], pd["hole"], pd["net"], frozenset(pd["lay"])))
    ctx.holes = holes
    bb = b.GetBoardEdgesBoundingBox()
    inset = 0.3 + mr.HW + 0.4
    mr.EDGE_IN = (P.ToMM(bb.GetLeft()) + inset, P.ToMM(bb.GetTop()) + inset,
                  P.ToMM(bb.GetRight()) - inset, P.ToMM(bb.GetBottom()) - inset)
    find = mr.f1.islands(mr.f1.M(b))

    items = []          # (comp, key, net, layer, x, y)  -- key = 'p:'+uuid / 'v:'+uuid / 't:'+uuid
    for u, pd in ctx.pads.items():
        if pd["net"] in affnets:
            L = next((x for x in mr.LAYERS if x in pd["lay"]), None)
            if L is not None:
                items.append([find("p:" + u), "p:" + u, pd["net"], L, pd["x"], pd["y"], None])
    for u, v in ctx.vias.items():
        if v["net"] in affnets:
            L = next((x for x in mr.LAYERS if x in v["lay"]), None)
            if L is not None:
                items.append([find("v:" + u), "v:" + u, v["net"], L, v["x"], v["y"], None])
    for t in ctx.tracks:
        if t["net"] in affnets and t["layer"] in mr.LAYERS:
            items.append([find("t:" + t["uuid"]), "t:" + t["uuid"], t["net"], t["layer"],
                          (t["x1"] + t["x2"]) / 2, (t["y1"] + t["y2"]) / 2, (t["x1"], t["y1"], t["x2"], t["y2"])])

    UF = {}

    def root(c):
        UF.setdefault(c, c)
        while UF[c] != c:
            UF[c] = UF[UF[c]]
            c = UF[c]
        return c

    def union(x, y):
        rx, ry = root(x), root(y)
        if rx != ry:
            UF[ry] = rx

    def pt_seg(x, y, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / L2))
        px, py = x1 + t * dx, y1 + t * dy
        return math.hypot(x - px, y - py), px, py

    def seg_seg(ax, ay, bx, by, cx, cy, dx, dy):
        cands = [pt_seg(ax, ay, cx, cy, dx, dy)] + [pt_seg(bx, by, cx, cy, dx, dy)]
        for (px, py) in ((cx, cy), (dx, dy)):
            d, qx, qy = pt_seg(px, py, ax, ay, bx, by)
            cands.append((d, qx, qy))
        return min(cands, key=lambda z: z[0])

    def pair_dist(i1, i2):
        """closest approach between two items as (distance, point_on_i1, point_on_i2)."""
        s1, s2 = i1[6], i2[6]
        if s1 and s2:
            cands = []
            for (px, py) in ((s1[0], s1[1]), (s1[2], s1[3])):
                d, qx, qy = pt_seg(px, py, s2[0], s2[1], s2[2], s2[3])
                cands.append((d, (px, py), (qx, qy)))
            for (px, py) in ((s2[0], s2[1]), (s2[2], s2[3])):
                d, qx, qy = pt_seg(px, py, s1[0], s1[1], s1[2], s1[3])
                cands.append((d, (qx, qy), (px, py)))
            return min(cands, key=lambda z: z[0])
        if s1:
            d, qx, qy = pt_seg(i2[4], i2[5], *s1)
            return d, (qx, qy), (i2[4], i2[5])
        if s2:
            d, qx, qy = pt_seg(i1[4], i1[5], *s2)
            return d, (i1[4], i1[5]), (qx, qy)
        return math.hypot(i1[4] - i2[4], i1[5] - i2[5]), (i1[4], i1[5]), (i2[4], i2[5])

    blocks, added, blocked = [], [], []
    for net in sorted(affnets):
        mine = [it for it in items if it[2] == net]
        for _pass in range(8):
            groups = {}
            for it in mine:
                groups.setdefault(root(it[0]), []).append(it)
            if len(groups) <= 1:
                break
            cands, seen_pairs = [], set()
            for gi in range(len(mine)):
                for gj in range(gi + 1, len(mine)):
                    ca_, cb_ = root(mine[gi][0]), root(mine[gj][0])
                    if ca_ == cb_:
                        continue
                    d, pa, pb = pair_dist(mine[gi], mine[gj])
                    if d > 20.0:
                        continue
                    key = (min(ca_, cb_), max(ca_, cb_), round(d, 3))
                    if key in seen_pairs:
                        continue
                    seen_pairs.add(key)
                    cands.append((d, gi, gj, pa, pb))
            cands.sort(key=lambda z: (round(z[0], 3), z[1], z[2]))
            if not cands:
                break
            sol = None
            tried = []
            for (d, gi, gj, pa, pb) in cands[:3]:          # bounded retry: the 3 nearest anchor pairs
                a1, a2 = mine[gi], mine[gj]
                for (x1, l1, p1, x2, l2, p2) in ((a1, a1[3], pa, a2, a2[3], pb),
                                                 (a2, a2[3], pb, a1, a1[3], pa)):   # also swapped roles
                    try:
                        sol, why = mr.solve_edge(ctx, find, root(a1[0]), root(a2[0]), net, l1, p1, l2, p2, 6.0, 0.25)
                    except Exception as ex:
                        sol, why = None, "exception:%s" % type(ex).__name__
                    tried.append({"dist": round(d, 3), "why": why})
                    if sol is not None:
                        break
                if sol is not None:
                    break
            if sol is None:
                blocked.append({"net": net, "dist": round(cands[0][0], 3), "why": tried[-1]["why"] if tried else "no-cand",
                                "tried": tried}) 
                break
            d, gi, gj = cands[0][0], cands[0][1], cands[0][2]
            a1, a2 = mine[gi], mine[gj]
            ca, cb = root(a1[0]), root(a2[0])
            nseg = nvia = 0; ln = 0.0
            for (L, pl) in sol["legs"]:
                for k in range(len(pl) - 1):
                    x1, y1 = pl[k]; x2, y2 = pl[k + 1]
                    if math.hypot(x2 - x1, y2 - y1) < 0.001:
                        continue
                    uu = mr.seg_uuid(net, L, x1, y1, x2, y2)
                    blocks.append(mr.SEG_BLOCK.format(x1=mr._fmt(x1), y1=mr._fmt(y1), x2=mr._fmt(x2),
                                                      y2=mr._fmt(y2), layer=mr.LNAME[L], net=net, u=uu))
                    ctx.tracks.append(dict(uuid=uu, net=net, layer=L, x1=x1, y1=y1, x2=x2, y2=y2, hw=mr.HW))
                    mine.append([ca, "t:" + uu, net, L, (x1 + x2) / 2, (y1 + y2) / 2, (x1, y1, x2, y2)])
                    nseg += 1; ln += math.hypot(x2 - x1, y2 - y1)
            for (x, y, span, l1, l2) in sol["vias"]:
                uu = mr.via_uuid(net, l1, l2, x, y)
                blind = "" if span == mr.SPAN_OF[frozenset((mr.F_CU, mr.B_CU))] else " blind"
                blocks.append(mr.VIA_BLOCK.format(blind=blind, x=mr._fmt(x), y=mr._fmt(y), l1=mr.LNAME[l1],
                                                  l2=mr.LNAME[l2], net=net, u=uu))
                ctx.vias[uu] = dict(net=net, x=x, y=y, r=mr.VIA_R, hole=mr.HOLE_R, lay=set(span))
                ctx.holes.append((x, y, mr.HOLE_R, net, span))
                Lv = next((L for L in mr.LAYERS if L in span), None)
                if Lv is not None:
                    mine.append([ca, "v:" + uu, net, Lv, x, y, None])
                nvia += 1
            union(ca, cb)
            added.append({"net": net, "dist_mm": round(d, 3), "segs": nseg, "vias": nvia, "len_mm": round(ln, 3)})
    txt = open(a.board, encoding="utf-8").read()
    anchor = txt.index("\t(segment\n")
    tmp = a.out + ".stitch_tmp.kicad_pcb"
    open(tmp, "w", encoding="utf-8").write(txt[:anchor] + "".join(blocks) + txt[anchor:])
    pr = _pro(a)
    if pr:
        for nm in (tmp, a.out):
            dd = nm.replace(".kicad_pcb", ".kicad_pro")
            if os.path.abspath(pr) != os.path.abspath(dd):
                shutil.copyfile(pr, dd)
    if blocks:
        _run([sys.executable, MROUTE, "--fill", tmp, a.out], "fill")
        try:
            os.remove(tmp)
        except OSError:
            pass
    else:
        shutil.copyfile(a.board, a.out)
    json.dump({"added": added, "blocked": blocked},
              open(os.path.join(a.work, "stitch.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"phase": "stitch", "nets": len(affnets), "added": len(added), "blocked": len(blocked),
                      "segs": sum(x["segs"] for x in added), "vias": sum(x["vias"] for x in added)}))
    return 0


def phase_snap(a, P):
    """Move NEW track endpoints exactly onto NEW via centres (same net, layer in the via span)."""
    aff = set(json.load(open(os.path.join(a.work, "rip.json"), encoding="utf-8"))["affected_netcodes"])
    st1 = a.stage1 or os.path.join(a.work, os.path.basename(a.board))
    b = P.LoadBoard(a.board)

    def sig(t):
        x1, y1, x2, y2 = P.ToMM(t.GetStart().x), P.ToMM(t.GetStart().y), P.ToMM(t.GetEnd().x), P.ToMM(t.GetEnd().y)
        if (x1, y1) > (x2, y2):
            x1, y1, x2, y2 = x2, y2, x1, y1
        return (t.GetLayer(), t.GetNetCode(), round(x1, 3), round(y1, 3), round(x2, 3), round(y2, 3))
    pre = {sig(t) for t in load_tracks(P, st1)}
    vias = []
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" and t.GetNetCode() in aff:
            vias.append((P.ToMM(t.GetPosition().x), P.ToMM(t.GetPosition().y), t.GetNetCode(),
                         set(t.GetLayerSet().Seq())))
    snaps = 0
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" or t.GetNetCode() not in aff or sig(t) in pre:
            continue
        for (vx, vy, vnc, vlay) in vias:
            if vnc != t.GetNetCode() or t.GetLayer() not in vlay:
                continue
            for getter, setter in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
                p = getter()
                d = math.hypot(P.ToMM(p.x) - vx, P.ToMM(p.y) - vy)
                if 0 < d <= 0.06:
                    setter(V(P, vx, vy)); snaps += 1
    P.SaveBoard(a.out, b)
    pr = _pro(a)
    if pr:
        dst = a.out.replace(".kicad_pcb", ".kicad_pro")
        if os.path.abspath(pr) != os.path.abspath(dst):
            shutil.copyfile(pr, dst)
    print(json.dumps({"phase": "snap", "snaps": snaps, "out": a.out}))
    return 0


def load_tracks(P, path):
    return [t for t in P.LoadBoard(path).GetTracks() if t.GetClass() != "PCB_VIA"]


def _newv(drc_now, drc_base):
    """NEW violations vs the baseline (multiset difference), as a list of (type, items)."""
    vsig = lambda v: (v.get("type"), v.get("severity"), v.get("description"),
                      tuple(sorted(i.get("description", "") for i in v.get("items", []))))
    bc = collections.Counter(vsig(v) for v in drc_base["violations"])
    rc = collections.Counter(vsig(v) for v in drc_now["violations"])
    out = []
    for k, c in (rc - bc).items():
        for v in drc_now["violations"]:
            if vsig(v) == k:
                out.append(v)
                break
    return out


def phase_repair(a, P):
    """ONE bounded, DRC-verified residue-repair round (the orchestrator repeats this in FRESH processes, because
    pcbnew/SWIG state is corrupted by in-process track removal).
      via_dangling        -> delete the orphaned via
      track_dangling      -> delete the fragment
      track_not_centered  -> snap the flagged endpoint exactly onto the via centre
    The round is REVERTED unless the violation count strictly improves AND unconnected stays 0.
    Returns 0 = clean / accepted, 2 = reverted or nothing to do.
    """
    base = json.load(open(a.baseline_drc, encoding="utf-8"))
    dj = os.path.join(a.work, "repair_drc.json")
    subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "-o", dj, a.board],
                   capture_output=True, text=True)
    dnow = json.load(open(dj, encoding="utf-8"))
    newv = _newv(dnow, base)
    rec = {"board_in": a.board, "violations_before": len(dnow["violations"]), "new_before": len(newv),
           "types_before": sorted({v["type"] for v in newv})}
    if not newv:
        rec["action"] = "clean"
        json.dump(rec, open(os.path.join(a.work, "repair.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        shutil.copyfile(a.board, a.out)
        print(json.dumps({"phase": "repair", **rec}, ensure_ascii=False))
        return 0
    b = P.LoadBoard(a.board)
    pos2uuid = {"PCB_VIA": [], "PCB_TRACK": []}
    for t in b.GetTracks():
        q = t.GetPosition()
        pos2uuid[t.GetClass()].append((P.ToMM(q.x), P.ToMM(q.y), t.m_Uuid.AsString(),
                                       P.ToMM(t.GetStart().x), P.ToMM(t.GetStart().y),
                                       P.ToMM(t.GetEnd().x), P.ToMM(t.GetEnd().y)))
    plan = []
    for v in newv:
        pos = next((i.get("pos") for i in v.get("items", []) if i.get("pos")), None)
        if pos is None:
            continue
        if v["type"] == "via_dangling":
            for (x, y, u, *_r) in pos2uuid["PCB_VIA"]:
                if abs(x - pos["x"]) < 0.02 and abs(y - pos["y"]) < 0.02:
                    plan.append({"act": "delvia", "uuid": u, "at": [x, y]}); break
        elif v["type"] == "track_dangling":
            done = False
            for (x, y, u, x1, y1, x2, y2) in pos2uuid["PCB_TRACK"]:
                for (px, py) in ((x1, y1), (x2, y2)):
                    if abs(px - pos["x"]) < 0.05 and abs(py - pos["y"]) < 0.05:
                        plan.append({"act": "deltrack", "uuid": u, "at": [px, py]}); done = True; break
                if done:
                    break
        elif v["type"] == "track_not_centered_on_via":
            # language-independent: one item is the track end, the other the via -> snap the track end onto
            # whichever of the two positions is NOT a track endpoint.
            cand = [i.get("pos") for i in v.get("items", []) if i.get("pos")]
            if len(cand) == 2:
                for (src, dst) in ((cand[0], cand[1]), (cand[1], cand[0])):
                    hit = False
                    for (x, y, u, x1, y1, x2, y2) in pos2uuid["PCB_TRACK"]:
                        for (xy, tag) in (((x1, y1), "s"), ((x2, y2), "e")):
                            if abs(xy[0] - src["x"]) < 0.25 and abs(xy[1] - src["y"]) < 0.25:
                                plan.append({"act": "snap", "uuid": u, "end": tag, "to": [dst["x"], dst["y"]]})
                                hit = True; break
                        if hit:
                            break
                    if hit:
                        break
    rec["plan"] = plan
    if not plan:
        rec["action"] = "no-plan"
        json.dump(rec, open(os.path.join(a.work, "repair.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        shutil.copyfile(a.board, a.out)
        print(json.dumps({"phase": "repair", **rec}, ensure_ascii=False))
        return 2
    b2 = P.LoadBoard(a.board)
    targets = {x["uuid"]: x for x in plan}
    applied = 0
    for t in list(b2.GetTracks()):
        u = t.m_Uuid.AsString()
        if u not in targets:
            continue
        act = targets[u]
        if act["act"] in ("delvia", "deltrack"):
            b2.Remove(t)
        else:
            (t.SetStart if act["end"] == "s" else t.SetEnd)(V(P, act["to"][0], act["to"][1]))
        applied += 1
    P.SaveBoard(a.out, b2)
    pr = _pro(a)
    if pr:
        dst = a.out.replace(".kicad_pcb", ".kicad_pro")
        if os.path.abspath(pr) != os.path.abspath(dst):
            shutil.copyfile(pr, dst)
    dj2 = os.path.join(a.work, "repair_drc_after.json")
    subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "-o", dj2, a.out],
                   capture_output=True, text=True)
    d2 = json.load(open(dj2, encoding="utf-8"))
    rec.update({"applied": applied, "violations_after": len(d2["violations"]),
                "new_after": len(_newv(d2, base)), "unconnected_after": len(d2.get("unconnected_items", []))})
    ok = applied > 0 and len(d2["violations"]) < len(dnow["violations"]) and len(d2.get("unconnected_items", [])) == 0
    rec["action"] = "accepted" if ok else "reverted"
    if not ok:
        shutil.copyfile(a.board, a.out)
    json.dump(rec, open(os.path.join(a.work, "repair.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"phase": "repair", **rec}, ensure_ascii=False)[:700])
    return 0 if ok else 2


def phase_normalize(a):
    """C21: make the saved board DETERMINISTIC (KiCad auto-generates uuids for objects created via the python API
    and its track save order varies between processes).  Text-level, semantics-preserving:
      * every (segment ...)/(via ...) uuid is rewritten from its own geometry (uuid5),
      * the contiguous track region is re-emitted sorted by that uuid.
    KiCad ignores the order; a DRC re-run afterwards re-validates the result.
    """
    _uuid = uuid
    NS = _uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
    txt = open(a.board, encoding="utf-8").read()
    blocks, spans = [], []
    for m in re.finditer(r"\t\((?:segment|via)(?: blind)?\n(?:.|\n)*?\n\t\)\n", txt):
        b = m.group(0)
        if b.startswith("\t(segment"):
            s_ = re.search(r"\(start ([^\s]+) ([^\s]+)\)", b)
            e_ = re.search(r"\(end ([^\s]+) ([^\s]+)\)", b)
            L_ = re.search(r'\(layer "([^"]+)"\)', b)
            N_ = re.search(r'\(net "([^"]*)"\)', b)
            if not (s_ and e_ and L_):
                continue
            key = "segnorm|%s|%s|%s|%s|%s|%s" % (N_.group(1) if N_ else "", L_.group(1),
                                                 s_.group(1), s_.group(2), e_.group(1), e_.group(2))
        else:
            at_ = re.search(r"\(at ([^\s]+) ([^\s]+)\)", b)
            N_ = re.search(r'\(net "([^"]*)"\)', b)
            Ls_ = re.search(r"\(layers ((?:\"[^\"]+\"\s*)+)\)", b)
            if not (at_ and N_):
                continue
            key = "vianorm|%s|%s|%s|%s" % (N_.group(1), Ls_.group(1) if Ls_ else "", at_.group(1), at_.group(2))
        u = str(_uuid.uuid5(NS, key))
        b = re.sub(r'\(uuid "[0-9a-fA-F-]+"\)', '(uuid "%s")' % u, b, count=1)
        blocks.append((u, b))
        spans.append((m.start(), m.end()))
    out = txt
    if blocks:
        gaps = "".join(txt[spans[i][1]:spans[i + 1][0]] for i in range(len(spans) - 1))
        if gaps.strip() == "":                      # the track region is contiguous -> we may reorder it
            region = "".join(b for _, b in sorted(blocks, key=lambda z: z[0]))
            out = txt[:spans[0][0]] + region + txt[spans[-1][1]:]
        else:                                        # fall back: rewrite uuids in place only
            out, off = [], 0
            for (u, b), (st, en) in zip(blocks, spans):
                out.append(txt[off:st]); out.append(b); off = en
            out.append(txt[off:])
            out = "".join(out)
    open(a.out, "w", encoding="utf-8").write(out)
    pr = _pro(a)
    if pr:
        dst = a.out.replace(".kicad_pcb", ".kicad_pro")
        if os.path.abspath(pr) != os.path.abspath(dst):
            shutil.copyfile(pr, dst)
    print(json.dumps({"phase": "normalize", "blocks": len(blocks), "reordered": True,
                      "sha16": hashlib.sha256(out.encode()).hexdigest()[:16]}))
    return 0



def phase_verify(a, P):
    rip = json.load(open(os.path.join(a.work, "rip.json"), encoding="utf-8"))

    def tracks_of(path):
        b = P.LoadBoard(path)
        out = set()
        for t in b.GetTracks():
            if t.GetClass() == "PCB_VIA":
                continue
            x1, y1 = P.ToMM(t.GetStart().x), P.ToMM(t.GetStart().y)
            x2, y2 = P.ToMM(t.GetEnd().x), P.ToMM(t.GetEnd().y)
            if (x1, y1) > (x2, y2):
                x1, y1, x2, y2 = x2, y2, x1, y1
            out.add((t.GetLayer(), t.GetNetCode(), round(x1, 3), round(y1, 3), round(x2, 3), round(y2, 3)))
        return out
    b0, b1 = tracks_of(a.board), tracks_of(a.out)
    lens = collections.defaultdict(float)
    for t in P.LoadBoard(a.out).GetTracks():
        if t.GetClass() == "PCB_VIA":
            continue
        ln = math.hypot(t.GetEnd().x - t.GetStart().x, t.GetEnd().y - t.GetStart().y) / 1e6
        lens[t.GetNetCode()] += ln
    names = {c: ni.GetNetname() for c, ni in P.LoadBoard(a.out).GetNetInfo().NetsByNetcode().items()}
    skews = []
    for (pn, nn) in HS_PAIRS:
        cps = [c for c, n in names.items() if n == pn]
        cns = [c for c, n in names.items() if n == nn]
        if cps and cns:
            lp, ln_ = lens[cps[0]], lens[cns[0]]
            skews.append({"pair": pn.replace("PCIE_UP_OUT", "OUT").replace("_P_J2", ""),
                          "len_P_mm": round(lp, 3), "len_N_mm": round(ln_, 3), "skew_mm": round(abs(lp - ln_), 4),
                          "pass": abs(lp - ln_) <= a.skew_limit + 1e-9})
    base = json.load(open(a.baseline_drc, encoding="utf-8"))
    fin = json.load(open(os.path.join(a.work, "final_drc.json"), encoding="utf-8"))
    vsig = lambda v: (v.get("type"), v.get("severity"), v.get("description"),
                      tuple(sorted(i.get("description", "") for i in v.get("items", []))))
    bc, rc = collections.Counter(vsig(v) for v in base["violations"]), collections.Counter(vsig(v) for v in fin["violations"])
    new, gone = rc - bc, bc - rc
    # PRIMARY criterion: per-TYPE counts must not increase (robust: an item description embeds a track LENGTH,
    # so simply re-routing a track changes its identity text without creating any new defect).
    bt = collections.Counter(v["type"] for v in base["violations"])
    ft = collections.Counter(v["type"] for v in fin["violations"])
    type_table = {t: {"baseline": bt[t], "final": ft[t], "delta": ft[t] - bt[t]} for t in sorted(set(bt) | set(ft))}
    increased = {t: v for t, v in type_table.items() if v["delta"] > 0}
    add, dele = len(b1 - b0), len(b0 - b1)
    unconn = len(fin.get("unconnected_items", []))
    acc = {"routing_diff_nonzero": (add + dele) > 0, "routing_diff_added": add, "routing_diff_deleted": dele,
           "drc_total": len(fin["violations"]), "drc_baseline_total": len(base["violations"]),
           "drc_zero_new": len(increased) == 0, "drc_types_increased": increased, "drc_per_type": type_table,
           "drc_identity_new": [{"type": k[0], "sev": k[1], "desc": k[2][:70]} for k in new],
           "drc_identity_removed": [{"type": k[0], "desc": k[2][:70]} for k in gone],
           "drc_identity_note": "identity diff is text-sensitive (a description embeds the track length); the per-TYPE table is the criterion",
           "unconnected": unconn, "skew_8of8_pass": bool(skews) and all(s["pass"] for s in skews), "skews": skews}
    acc["PASS"] = bool(acc["routing_diff_nonzero"] and acc["drc_zero_new"] and unconn == 0 and acc["skew_8of8_pass"])
    dest = a.report or (a.out + ".acceptance.json")
    json.dump(acc, open(dest, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"phase": "verify", "acceptance": acc}, ensure_ascii=False, indent=1))
    return 0 if acc["PASS"] else 1


def _run(cmd, what):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("[%s] rc=%d\n%s\n%s" % (what, r.returncode, r.stdout[-500:], r.stderr[-300:]))
    return r


def _drc(board, out_json, what):
    _run([KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "-o", out_json, board], what)
    return json.load(open(out_json, encoding="utf-8"))


def orchestrate(a):
    py = sys.executable
    _mirror(a)
    r = _run([py, SELF, "--phase", "rip", "--board", a.board, "--work", a.work, "--out", a.out]
             + sum([["--moved", m] for m in a.moved], [])
             + sum([["--clear-rect", x] for x in a.clear_rect], [])
             + ["--radius", str(a.radius),
                "--rects", json.dumps([list(map(float, x.split(","))) for x in a.clear_rect])], "rip")
    rip = json.load(open(os.path.join(a.work, "rip.json"), encoding="utf-8"))
    stage1 = rip["stage1"]
    d0 = _drc(stage1, os.path.join(a.work, "stage1_drc.json"), "drc-stage1")
    stitched = os.path.join(a.work, os.path.basename(a.board).replace(".kicad_pcb", "_stitched.kicad_pcb"))
    _run([py, SELF, "--phase", "stitch", "--board", stage1, "--work", a.work, "--out", stitched], "stitch")
    dst = os.path.join(a.work, "stitched_drc.json")
    d1 = _drc(stitched, dst, "drc-stitched")
    merged = os.path.join(a.work, os.path.basename(a.board).replace(".kicad_pcb", "_rerouted.kicad_pcb"))
    mroute = {"unconnected_after_rip": len(d0.get("unconnected_items", [])),
              "unconnected_after_stitch": len(d1.get("unconnected_items", [])), "skipped": not bool(d1.get("unconnected_items"))}
    if d1.get("unconnected_items"):
        rr = _run([py, ROUTER_FLOOR, "--in", stitched, "--drc", dst,
                   "--out", merged, "--ledger", os.path.join(a.work, "mroute_ledger.json"),
                   "--margin", str(a.margin), "--floor", str(getattr(a, "clearance_floor", 0.20))], "mroute")
        mroute["stdout"] = rr.stdout.strip()[-300:]
    else:
        shutil.copyfile(stitched, merged)
    snap_out = os.path.join(a.work, os.path.basename(a.board).replace(".kicad_pcb", "_snapped.kicad_pcb"))
    _run([py, SELF, "--phase", "snap", "--board", merged, "--work", a.work, "--out", snap_out,
          "--stage1", stage1], "snap")
    shutil.copyfile(snap_out, a.out)
    pr = _pro(a)
    if pr:
        dst = a.out.replace(".kicad_pcb", ".kicad_pro")
        if os.path.abspath(pr) != os.path.abspath(dst):
            shutil.copyfile(pr, dst)
    rounds = []
    for k in range(4):
        rr = subprocess.run([py, SELF, "--phase", "repair", "--board", a.out, "--work", a.work, "--out", a.out,
                             "--stage1", stage1, "--baseline-drc", a.baseline_drc],
                            capture_output=True, text=True)
        try:
            rec = json.load(open(os.path.join(a.work, "repair.json"), encoding="utf-8"))
        except Exception:
            rec = {"action": "error", "stderr": rr.stderr[-200:]}
        rounds.append(rec)
        if rec.get("action") != "accepted":
            break
    json.dump({"rounds": rounds}, open(os.path.join(a.work, "repair_rounds.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    norm_out = os.path.join(a.work, os.path.basename(a.board).replace(".kicad_pcb", "_final.kicad_pcb"))
    _run([py, SELF, "--phase", "normalize", "--board", a.out, "--work", a.work, "--out", norm_out,
          "--stage1", stage1], "normalize")
    shutil.copyfile(norm_out, a.out)
    pr2 = _pro(a)
    if pr2:
        dst2 = a.out.replace(".kicad_pcb", ".kicad_pro")
        if os.path.abspath(pr2) != os.path.abspath(dst2):
            shutil.copyfile(pr2, dst2)
    _drc(a.out, os.path.join(a.work, "final_drc.json"), "drc-final")
    acc_path = os.path.join(a.work, "acceptance.json")
    _run([py, SELF, "--phase", "verify", "--board", a.board, "--work", a.work, "--out", a.out,
          "--report", acc_path, "--baseline-drc", a.baseline_drc], "verify")
    acc = json.load(open(acc_path, encoding="utf-8"))
    rep = {"artifact": "k2_reroute_affected_v2", "ts": "2026-09-28", "board_in": a.board, "board_out": a.out,
           "phase_helpers": {"rip": "phase rip", "router": "tools/k2_p4_mroute_v1.py (exact gate)",
                             "snap": "phase snap", "verify": "phase verify"},
           "rip_up": {k: rip[k] for k in ("affected_nets", "moves", "tracks_removed", "parts_kept")},
           "stitch": json.load(open(os.path.join(a.work, "stitch.json"), encoding="utf-8")) if os.path.exists(os.path.join(a.work, "stitch.json")) else None,
           "repair_rounds": rounds,
           "mroute": mroute,
           "acceptance": acc, "OWNER-ITEMS": 0}
    if a.report:
        json.dump(rep, open(a.report, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"affected_nets": rip["affected_nets"], "rip": {"removed": rip["tracks_removed"],
                      "kept": rip["parts_kept"]}, "mroute": mroute, "acceptance": acc}, ensure_ascii=False, indent=1))
    return 0 if acc["PASS"] else 1


if __name__ == "__main__":
    sys.exit(main())
