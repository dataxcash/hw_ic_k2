#!/usr/bin/env python3
"""K2 · P4 收敛增量 —— 低速/电源 **跨层通道布线（阶段 F3）**：IC 侧落孔 F→B → B.Cu 主层通道 → 落点。

依据 owner 常设裁定 #14（**走廊/布线 · 过孔策略 = L2 自裁勿停**）+ 《宪法》第四条（改板须 SPEC 留痕）。
动因（T-6）：F.Cu 同层域近耗尽（33 条 ≤20mm 边中仅 3 条有合法 F.Cu 通路）⇒ 出路在跨层 + B.Cu（近空层）。

口径（与 `_shared/eda_core/drc_rules.json` 一致，**不放松任何下限**）：
- 过孔类沿用板内既有唯一合法类 **0.20 孔 / 0.35 盘**（跨层过孔 F→B 通孔，或按端点层对落孔）。
- 净距 = net class max（PCIe85 0.175 / POWER 0.2 / LOW_SPEED 0.1，board_min 0.1）；孔-铜 0.25；
  **孔-孔 0.25（无同网豁免）**；板边铜 0.3；禁 via/禁 track 的禁布区规避；线宽 0.200。
- **放行闸 = 精确复核**（T-6 教训）：任何候选（过孔位置、F.Cu 短引线、B.Cu 走线）都必须通过**逐段/逐孔精确比对**，
  任一不符即弃（栅格仅作剪枝）。新段一律 0/45/90° 且单腿 ≥0.05；纯增（不动既有铜）。
- 未解边逐条登记（`no-legal-via-slot` / `no-legal-path-on-bcu` / `no-legal-fcu-stub`），**不静默放弃**。
复跑确定性：排序化 + 几何 uuid5 派生。判定权归监理，本器只交测量。
"""
from __future__ import annotations
import argparse, heapq, importlib.util, json, math, os, re, shutil, subprocess, sys, uuid
import pcbnew

_HERE = os.path.dirname(os.path.abspath(__file__))
def _load(n, f):
    sp = importlib.util.spec_from_file_location(n, os.path.join(_HERE, f))
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
cv = _load("k2cv", "k2_p4_converge_v1.py")
f1 = _load("k2f1", "k2_p4_ls_local_v1.py")
MM, F_CU, B_CU = cv.MM, pcbnew.F_Cu, pcbnew.B_Cu
CU = {}
for i in range(32):
    if pcbnew.IsCopperLayer(i): CU[i] = pcbnew.LayerName(i)
TRACE_W, VIA_W, VIA_D = 0.20, 0.35, 0.20
HW, VIA_R, HOLE_R = TRACE_W / 2.0, VIA_W / 2.0, VIA_D / 2.0
STEP, MAXVIA_R = 0.10, 1.5       # 0.10mm 栅格（仅剪枝；几何合规由精确复核保证）
TIME_BUDGET = 900.0               # 总时限（秒）：超时后剩余边登记 deferred-time-budget
NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
VIA_BLOCK = ('\t(via\n\t\t(at {x} {y})\n\t\t(size 0.35)\n\t\t(drill 0.2)\n\t\t(layers "{l1}" "{l2}")\n'
             '\t\t(net "{net}")\n\t\t(uuid "{u}")\n\t)\n')


def via_uuid(net, l1, l2, x, y):
    return str(uuid.uuid5(NS, "k2p4xl|via|%s|%s|%s|%s|%s" % (net, l1, l2, f1._fmt(x), f1._fmt(y))))


class Ctx:
    """布线上下文：同网豁免之外的**全部**障碍 + 精确判定（层感知）。"""

    def __init__(self, b):
        self.pads = {}; self.tracks = []; self.vias = {}; self.holes = []
        self.keep_v, self.keep_t, self.edge = [], [], []
        for fp in b.GetFootprints():
            for p in fp.Pads():
                ls = p.GetLayerSet(); pos, sz = p.GetPosition(), p.GetSize()
                circ = p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE
                dz = p.GetDrillSize()
                rec = dict(net=p.GetNetname(), x=MM(pos.x), y=MM(pos.y), w=MM(sz.x), h=MM(sz.y), circ=circ,
                           hole=MM(dz.x) / 2.0 if dz.x > 0 else 0.0, lay=set(L for L in CU if ls.Contains(L)),
                           poly=None if circ else cv.rect_corners(MM(pos.x), MM(pos.y), MM(sz.x), MM(sz.y), p.GetOrientationDegrees()))
                self.pads[p.m_Uuid.AsString()] = rec
                if rec["hole"] > 0:
                    self.holes.append((rec["x"], rec["y"], rec["hole"], rec["net"]))
        for t in b.GetTracks():
            u = t.m_Uuid.AsString()
            if isinstance(t, pcbnew.PCB_VIA):
                pos = t.GetPosition(); ls = t.GetLayerSet()
                rec = dict(net=t.GetNetname(), x=MM(pos.x), y=MM(pos.y), r=MM(t.GetWidth(F_CU)) / 2,
                           hole=MM(t.GetDrillValue()) / 2.0, lay=set(L for L in CU if ls.Contains(L)))
                self.vias[u] = rec
                self.holes.append((rec["x"], rec["y"], rec["hole"], rec["net"]))
            else:
                s, e = t.GetStart(), t.GetEnd()
                self.tracks.append(dict(uuid=u, net=t.GetNetname(), layer=t.GetLayer(), x1=MM(s.x), y1=MM(s.y),
                                        x2=MM(e.x), y2=MM(e.y), hw=MM(t.GetWidth()) / 2))
        for z in b.Zones():
            if not z.GetIsRuleArea(): continue
            polys = []
            for i in range(z.Outline().OutlineCount()):
                ch = z.Outline().Outline(i)
                polys.append([(MM(ch.CPoint(k).x), MM(ch.CPoint(k).y)) for k in range(ch.PointCount())])
            if z.GetDoNotAllowVias(): self.keep_v += polys
            if z.GetDoNotAllowTracks(): self.keep_t += polys
        for d in b.GetDrawings():
            if d.GetLayer() == pcbnew.Edge_Cuts and hasattr(d, "GetStart"):
                s, e = d.GetStart(), d.GetEnd()
                self.edge.append((MM(s.x), MM(s.y), MM(e.x), MM(e.y)))

    @staticmethod
    def _bb_hit(bb, x1, y1, x2, y2, rad=0.0):
        return not (bb[1] + rad < min(x1, x2) or bb[0] - rad > max(x1, x2) or
                    bb[3] + rad < min(y1, y2) or bb[2] - rad > max(y1, y2))

    # ── 精确：段（某层） ──
    def seg_exact(self, layer, net, x1, y1, x2, y2, hw=HW):
        for e in self.edge:
            if cv.seg_seg_dist(x1, y1, x2, y2, *e) < 0.3 + hw: return False
        for poly in self.keep_t:
            if cv.seg_poly_dist(x1, y1, x2, y2, poly) <= 0: return False
        rb = (min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2))
        for t in self.tracks:
            if t["layer"] != layer or t["net"] == net: continue
            rad = hw + t["hw"] + cv._req(net, t["net"])
            if not self._bb_hit(rb, t["x1"], t["y1"], t["x2"], t["y2"], rad): continue
            if cv.seg_seg_dist(x1, y1, x2, y2, t["x1"], t["y1"], t["x2"], t["y2"]) < rad: return False
        for p in self.pads.values():
            if layer not in p["lay"] or p["net"] == net: continue
            rad = hw + cv._req(net, p["net"])
            if not self._bb_hit(rb, p["x"] - p["w"] / 2, p["y"] - p["h"] / 2, p["x"] + p["w"] / 2, p["y"] + p["h"] / 2, rad + 0.8): continue
            if p["circ"]:
                if cv.pt_seg_dist(p["x"], p["y"], x1, y1, x2, y2) - min(p["w"], p["h"]) / 2 < rad: return False
            elif cv.seg_poly_dist(x1, y1, x2, y2, p["poly"]) < rad: return False
        for v in self.vias.values():
            if layer not in v["lay"] or v["net"] == net: continue
            rad = hw + cv._req(net, v["net"])
            if not self._bb_hit(rb, v["x"], v["y"], v["x"], v["y"], rad + v["r"]): continue
            if cv.pt_seg_dist(v["x"], v["y"], x1, y1, x2, y2) - v["r"] < rad: return False
        for (hx, hy, hr, hnet) in self.holes:
            if hnet == net: continue
            rad = hr + 0.25 + hw
            if not self._bb_hit(rb, hx, hy, hx, hy, rad): continue
            if cv.pt_seg_dist(hx, hy, x1, y1, x2, y2) < rad: return False
        return True

    # ── 精确：过孔（此处为 F→B 通孔：铜存在于**全部**铜层） ──
    def via_exact(self, net, x, y):
        for e in self.edge:
            if cv.pt_seg_dist(x, y, *e) < 0.3 + VIA_R: return False
        for poly in self.keep_v:
            if cv.pt_in_poly(x, y, poly): return False
        for t in self.tracks:
            if t["net"] == net: continue
            need = max(VIA_R + cv._req(net, t["net"]), HOLE_R + 0.25 + t["hw"])
            if not self._bb_hit((x, x, y, y), t["x1"], t["y1"], t["x2"], t["y2"], need + t["hw"]): continue
            if cv.pt_seg_dist(x, y, t["x1"], t["y1"], t["x2"], t["y2"]) - t["hw"] < need: return False
        for p in self.pads.values():
            if p["net"] == net: continue
            need = max(VIA_R + cv._req(net, p["net"]), HOLE_R + 0.25)
            if p["circ"]:
                if math.hypot(x - p["x"], y - p["y"]) - min(p["w"], p["h"]) / 2 < need: return False
            elif cv.pt_in_poly(x, y, p["poly"]) or cv.pt_poly_dist(x, y, p["poly"]) < need: return False
        for v in self.vias.values():
            if v["net"] == net: continue
            need = max(VIA_R + v["r"] + cv._req(net, v["net"]), HOLE_R + 0.25, HOLE_R + 0.25 + v["hole"] - HOLE_R)
            if math.hypot(x - v["x"], y - v["y"]) < need: return False
        for (hx, hy, hr, hnet) in self.holes:          # 孔-孔 0.25（**无同网豁免**）
            if abs(x - hx) > 1.0 or abs(y - hy) > 1.0: continue
            if math.hypot(x - hx, y - hy) < HOLE_R + 0.25 + hr: return False
        return True


def blocked_layer(ctx, net, layer, a, b):
    """栅格剪枝集（0.05mm 格心）：该层异网铜 + 孔 + 板边 + 禁 track 区（含安全余量）。"""
    MARGIN = 0.08
    bad = set()
    gx0, gy0 = math.floor((min(a[0], b[0]) - 1.0) / STEP), math.floor((min(a[1], b[1]) - 1.0) / STEP)
    gx1, gy1 = math.ceil((max(a[0], b[0]) + 1.0) / STEP), math.ceil((max(a[1], b[1]) + 1.0) / STEP)
    def cand(cx, cy, rad):
        for i in range(math.floor((cx - rad) / STEP), math.ceil((cx + rad) / STEP) + 1):
            for j in range(math.floor((cy - rad) / STEP), math.ceil((cy + rad) / STEP) + 1):
                if gx0 <= i <= gx1 and gy0 <= j <= gy1:
                    px, py = i * STEP, j * STEP
                    if (px - cx) ** 2 + (py - cy) ** 2 <= rad * rad: bad.add((i, j))
    def cseg(ax, ay, bx, by, rad):
        for i in range(math.floor((min(ax, bx) - rad) / STEP), math.ceil((max(ax, bx) + rad) / STEP) + 1):
            for j in range(math.floor((min(ay, by) - rad) / STEP), math.ceil((max(ay, by) + rad) / STEP) + 1):
                if gx0 <= i <= gx1 and gy0 <= j <= gy1:
                    px, py = i * STEP, j * STEP
                    if cv.pt_seg_dist(px, py, ax, ay, bx, by) <= rad: bad.add((i, j))
    for t in ctx.tracks:
        if t["layer"] != layer or t["net"] == net: continue
        rad = t["hw"] + HW + cv._req(net, t["net"]) + MARGIN
        if not ctx._bb_hit((min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])), t["x1"], t["y1"], t["x2"], t["y2"], rad): continue
        cseg(t["x1"], t["y1"], t["x2"], t["y2"], rad)
    for p in ctx.pads.values():
        if layer not in p["lay"] or p["net"] == net: continue
        r = HW + cv._req(net, p["net"]) + MARGIN
        if p["circ"]:
            cand(p["x"], p["y"], min(p["w"], p["h"]) / 2 + r)
        else:
            for k in range(len(p["poly"])):
                q1, q2 = p["poly"][k], p["poly"][(k + 1) % len(p["poly"])]
                cseg(q1[0], q1[1], q2[0], q2[1], r)
            xa = [q[0] for q in p["poly"]]; ya = [q[1] for q in p["poly"]]
            for i in range(math.floor(min(xa) / STEP), math.ceil(max(xa) / STEP) + 1):
                for j in range(math.floor(min(ya) / STEP), math.ceil(max(ya) / STEP) + 1):
                    if cv.pt_in_poly(i * STEP, j * STEP, p["poly"]): bad.add((i, j))
    for v in ctx.vias.values():
        if layer not in v["lay"] or v["net"] == net: continue
        cand(v["x"], v["y"], max(v["r"] + HW + cv._req(net, v["net"]), v["hole"] + 0.25 + HW) + MARGIN)
    for (hx, hy, hr, hnet) in ctx.holes:
        if hnet == net: continue
        cand(hx, hy, hr + 0.25 + HW + MARGIN)
    for e in ctx.edge:
        cseg(e[0], e[1], e[2], e[3], HW + 0.3 + MARGIN)
    rb = (min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1]))
    for poly in ctx.keep_t:
        xa = [q[0] for q in poly]; ya = [q[1] for q in poly]
        if not ctx._bb_hit(rb, min(xa), min(ya), max(xa), max(ya), 0.0): continue
        for i in range(max(gx0, math.floor(min(xa) / STEP)), min(gx1, math.ceil(max(xa) / STEP)) + 1):
            for j in range(max(gy0, math.floor(min(ya) / STEP)), min(gy1, math.ceil(max(ya) / STEP)) + 1):
                if cv.pt_in_poly(i * STEP, j * STEP, poly): bad.add((i, j))
    return bad, gx0, gx1, gy0, gy1


def astar(ctx, net, layer, a, b, cap=80000):
    bad, gx0, gx1, gy0, gy1 = blocked_layer(ctx, net, layer, a, b)
    i0, j0 = int(round(a[0] / STEP)), int(round(a[1] / STEP))
    if (i0, j0) in bad: return None
    gi, gj = b[0] / STEP, b[1] / STEP
    def seg_clear(x1, y1, x2, y2):
        n = int(max(abs(x2 - x1), abs(y2 - y1)) / STEP) + 2
        for k in range(n + 1):
            t = k / n
            i = int(round((x1 + (x2 - x1) * t) / STEP)); j = int(round((y1 + (y2 - y1) * t) / STEP))
            if (i, j) in bad: return False
        return True
    def conn(x, y):
        for cx, cy in ((x, b[1]), (b[0], y)):
            if seg_clear(x, y, cx, cy) and seg_clear(cx, cy, b[0], b[1]):
                return [(cx, cy)]
        dx, dy = b[0] - x, b[1] - y            # 直连仅在 0/45/90° 时才合法（否则会引入非 45° 段）
        if (abs(dx) < 1e-9 or abs(dy) < 1e-9 or abs(abs(dx) - abs(dy)) < 1e-9) and seg_clear(x, y, b[0], b[1]):
            return []
        return None
    h = lambda i, j: max(abs(i - gi), abs(j - gj)) * STEP * math.sqrt(2)
    openq = [(h(i0, j0), 0.0, (i0, j0))]
    gsc = {(i0, j0): 0.0}; came = {(i0, j0): None}
    DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
    n = 0
    while openq:
        f, g, cur = heapq.heappop(openq)
        if g > gsc.get(cur, 1e18) + 1e-9: continue
        n += 1
        if n > cap: return None
        x, y = cur[0] * STEP, cur[1] * STEP
        c = conn(x, y)
        if c is not None:
            path = []
            q = cur
            while q is not None:
                path.append(q); q = came[q]
            path.reverse()
            pts = [(p[0] * STEP, p[1] * STEP) for p in path]
            return pts + c + [(b[0], b[1])]
        for dx, dy in DIRS:
            nb = (cur[0] + dx, cur[1] + dy)
            if not (gx0 <= nb[0] <= gx1 and gy0 <= nb[1] <= gy1) or nb in bad: continue
            ng = g + STEP * (math.sqrt(2) if dx and dy else 1.0)
            if ng < gsc.get(nb, 1e18) - 1e-9:
                gsc[nb] = ng; came[nb] = cur
                heapq.heappush(openq, (ng + h(*nb), ng, nb))
    return None


def simplify(pts):
    out = [pts[0]]
    for k in range(1, len(pts)):
        out.append(pts[k])
        while len(out) >= 3:
            (x0, y0), (x1, y1), (x2, y2) = out[-3], out[-2], out[-1]
            v1 = (round(x1 - x0, 6), round(y1 - y0, 6)); v2 = (round(x2 - x1, 6), round(y2 - y1, 6))
            if v1[0] * v2[1] == v1[1] * v2[0] and (v1[0] * v2[0] + v1[1] * v2[1]) > 0: out.pop(-2)
            else: break
    return out


def _poly_ok(ctx, layer, net, pts):
    for k in range(len(pts) - 1):
        x1, y1, x2, y2 = pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1]
        if math.hypot(x2 - x1, y2 - y1) < 0.05:
            if math.hypot(x2 - x1, y2 - y1) > 1e-9: return False
            continue
        if not ctx.seg_exact(layer, net, x1, y1, x2, y2): return False
    return True


def _ports(ctx, find, comp):
    """(B.Cu 既有铜点, F.Cu 铜点) —— 铜岛在两层上各自的可用接点。"""
    bp, fp = [], []
    for u, p in ctx.pads.items():
        if find("p:" + u) != comp: continue
        if B_CU in p["lay"]: bp.append((p["x"], p["y"]))
        if F_CU in p["lay"]: fp.append((p["x"], p["y"]))
    for t in ctx.tracks:
        if find("t:" + t["uuid"]) != comp: continue
        if t["layer"] == B_CU: bp += [(t["x1"], t["y1"]), (t["x2"], t["y2"])]
        if t["layer"] == F_CU: fp += [(t["x1"], t["y1"]), (t["x2"], t["y2"])]
    for u, v in ctx.vias.items():
        if find("v:" + u) != comp: continue
        if B_CU in v["lay"]: bp.append((v["x"], v["y"]))
        if F_CU in v["lay"]: fp.append((v["x"], v["y"]))
    return sorted(set(bp)), sorted(set(fp))


def _via_near(ctx, net, anchor, target):
    """在 anchor 附近找合法 F→B 通孔位 + F.Cu 短引线（精确复核）。返回 (via_xy, legs) 或 None。"""
    best = None
    r = 0.0
    while r <= MAXVIA_R + 1e-9:
        for k in range(36):
            a = math.radians(10.0 * k)
            x, y = anchor[0] + r * math.cos(a), anchor[1] + r * math.sin(a)
            if not ctx.via_exact(net, x, y): continue
            for pp in cv._paths45(anchor, (x, y)):
                pts = list(pp)
                if _poly_ok(ctx, F_CU, net, pts):
                    d = math.hypot(x - target[0], y - target[1])
                    if best is None or d < best[0] - 1e-9:
                        best = (d, (x, y), pts)
        if best is not None: return best[1], best[2]
        r = round(r + 0.05, 4)
    return None


def run(src, drc_path, out_path, ledger_path):
    b = pcbnew.LoadBoard(src)
    ctx = Ctx(b)
    m = f1.M(b)
    find = f1.islands(m)
    drc = json.load(open(drc_path, encoding="utf-8"))

    def locate(uu):
        if uu in ctx.pads: return "p:" + uu, ctx.pads[uu]["net"]
        if uu in ctx.vias: return "v:" + uu, ctx.vias[uu]["net"]
        for t in ctx.tracks:
            if t["uuid"] == uu: return "t:" + uu, t["net"]
        return None, None
    edges = []
    for e in drc.get("unconnected_items", []):
        its = e.get("items", [])
        if len(its) != 2: continue
        (ka, na), (kb, nb) = locate(its[0]["uuid"]), locate(its[1]["uuid"])
        if not ka or not kb or na != nb or not na: continue
        d = math.hypot(its[0]["pos"]["x"] - its[1]["pos"]["x"], its[0]["pos"]["y"] - its[1]["pos"]["y"])
        edges.append((round(d, 3), na, ka, kb))
    edges.sort()
    added, blocked, blocks = [], [], []
    import time as _t
    t0 = _t.time()
    for dist, net, ka, kb in edges:
        if _t.time() - t0 > TIME_BUDGET:
            blocked.append({"net": net, "dist": dist, "why": "deferred-time-budget"}); continue
        ca, cb = find(ka), find(kb)
        if ca == cb: continue
        ba, fa = _ports(ctx, find, ca)
        bb, fb = _ports(ctx, find, cb)
        if not ba and not fa: blocked.append({"net": net, "dist": dist, "why": "no-port"}); continue
        if not bb and not fb: blocked.append({"net": net, "dist": dist, "why": "no-port"}); continue
        sol = None
        # 候选对：既有 B.Cu 点优先（免落孔）；不足则就该端落孔（F→B）
        ref_b = (sum(p[0] for p in (bb or fb)) / len(bb or fb), sum(p[1] for p in (bb or fb)) / len(bb or fb))
        ref_a = (sum(p[0] for p in (ba or fa)) / len(ba or fa), sum(p[1] for p in (ba or fa)) / len(ba or fa))
        cand_a = [(p, False, None, None) for p in sorted(ba, key=lambda q: math.hypot(q[0] - ref_b[0], q[1] - ref_b[1]))[:3]]
        if not cand_a and fa:
            for p in sorted(fa, key=lambda q: math.hypot(q[0] - ref_b[0], q[1] - ref_b[1]))[:3]:
                got = _via_near(ctx, net, p, ref_b)
                if got: cand_a = [(got[0], True, got[1], p)]; break
        cand_b = [(p, False, None, None) for p in sorted(bb, key=lambda q: math.hypot(q[0] - ref_a[0], q[1] - ref_a[1]))[:3]]
        if not cand_b and fb:
            for p in sorted(fb, key=lambda q: math.hypot(q[0] - ref_a[0], q[1] - ref_a[1]))[:3]:
                got = _via_near(ctx, net, p, ref_a)
                if got: cand_b = [(got[0], True, got[1], p)]; break
        if not cand_a:
            blocked.append({"net": net, "dist": dist, "why": "no-legal-via-slot"}); continue
        if not cand_b:
            blocked.append({"net": net, "dist": dist, "why": "no-legal-via-slot"}); continue
        for pa in cand_a:
            if sol: break
            for pb in cand_b:
                if sol: break
                A = pa[0]; B2 = pb[0]
                route_pts = astar(ctx, net, B_CU, A, B2)
                if route_pts is None: continue
                route_pts = simplify(route_pts)
                if not _poly_ok(ctx, B_CU, net, route_pts): continue
                stubs = []
                ok = True
                for (pt, need, stub_pts, anchor) in (pa, pb):
                    if need:
                        for k in range(len(stub_pts) - 1):
                            if not ctx.seg_exact(F_CU, net, stub_pts[k][0], stub_pts[k][1], stub_pts[k + 1][0], stub_pts[k + 1][1]): ok = False
                        stubs.append((stub_pts, anchor, pt))
                if not ok: continue
                sol = dict(a=pa, b=pb, route=route_pts, stubs=stubs)
        if not sol:
            why = "no-legal-path-on-bcu"
            if not cand_a or not cand_b: why = "no-legal-via-slot"
            blocked.append({"net": net, "dist": dist, "why": why}); continue
        # ── 落账（同步更新 ctx，供后续边精确判定） ──
        placed = []
        for (pt, need, stub_pts, anchor) in (sol["a"], sol["b"]):
            if not need: continue
            vxy = pt
            u = via_uuid(net, "F.Cu", "B.Cu", vxy[0], vxy[1])
            blocks.append(VIA_BLOCK.format(x=f1._fmt(vxy[0]), y=f1._fmt(vxy[1]), l1="F.Cu", l2="B.Cu",
                                           net=net, u=u))
            ctx.vias[u] = dict(net=net, x=vxy[0], y=vxy[1], r=VIA_R, hole=HOLE_R, lay={F_CU, B_CU})
            ctx.holes.append((vxy[0], vxy[1], HOLE_R, net))
            placed.append([round(vxy[0], 3), round(vxy[1], 3)])
        for pts in [s[0] for s in sol["stubs"]]:
            for k in range(len(pts) - 1):
                x1, y1, x2, y2 = pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1]
                if math.hypot(x2 - x1, y2 - y1) < 0.001: continue
                u = f1.seg_uuid(net, "F.Cu", x1, y1, x2, y2)
                blocks.append(f1.SEG_BLOCK.format(x1=f1._fmt(x1), y1=f1._fmt(y1), x2=f1._fmt(x2), y2=f1._fmt(y2),
                                                  layer="F.Cu", net=net, u=u))
                ctx.tracks.append(dict(uuid=u, net=net, layer=F_CU, x1=x1, y1=y1, x2=x2, y2=y2, hw=HW))
        for k in range(len(sol["route"]) - 1):
            x1, y1, x2, y2 = sol["route"][k][0], sol["route"][k][1], sol["route"][k + 1][0], sol["route"][k + 1][1]
            if math.hypot(x2 - x1, y2 - y1) < 0.001: continue
            u = f1.seg_uuid(net, "B.Cu", x1, y1, x2, y2)
            blocks.append(f1.SEG_BLOCK.format(x1=f1._fmt(x1), y1=f1._fmt(y1), x2=f1._fmt(x2), y2=f1._fmt(y2),
                                              layer="B.Cu", net=net, u=u))
            ctx.tracks.append(dict(uuid=u, net=net, layer=B_CU, x1=x1, y1=y1, x2=x2, y2=y2, hw=HW))
        added.append({"net": net, "dist": dist, "vias": placed,
                      "bcu_legs": len(sol["route"]) - 1,
                      "fcu_stub_legs": sum(len(s[0]) - 1 for s in sol["stubs"])})
    led = {"stage": "F3", "edges": len(edges), "added": added, "blocked": blocked,
           "F3_summary": {"added": len(added), "blocked": len(blocked),
                          "reasons": {k: sum(1 for x in blocked if x["why"] == k) for k in sorted({x["why"] for x in blocked})},
                          "vias_placed": sum(len(a["vias"]) for a in added)}}
    json.dump(led, open(ledger_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if blocks:
        txt = open(src, encoding="utf-8").read()
        anchor = txt.index("\t(segment\n")
        tmp = out_path + ".f3_tmp.kicad_pcb"
        open(tmp, "w", encoding="utf-8").write(txt[:anchor] + "".join(blocks) + txt[anchor:])
        src_pro = re.sub(r"\.kicad_pcb$", ".kicad_pro", src)
        if os.path.exists(src_pro):
            shutil.copyfile(src_pro, re.sub(r"\.kicad_pcb$", ".kicad_pro", tmp))
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "--fill", tmp, out_path], capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError("fill failed rc=%d %s" % (r.returncode, r.stderr[-300:]))
        if os.path.exists(src_pro):
            shutil.copyfile(src_pro, re.sub(r"\.kicad_pcb$", ".kicad_pro", out_path))
        os.remove(tmp)
    else:
        shutil.copyfile(src, out_path)
    return led["F3_summary"]


def _fill(tmp, out_path):
    b2 = pcbnew.LoadBoard(tmp)
    if b2 is None:
        raise SystemExit("_fill: LoadBoard -> None")
    pcbnew.ZONE_FILLER(b2).Fill(b2.Zones())
    b2.Save(out_path)
    print(json.dumps({"fill": "ok"}))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="K2 P4 阶段 F3：低速/电源跨层通道布线（IC 侧落孔 + B.Cu）")
    ap.add_argument("--fill", nargs=2, metavar=("TMP", "OUT"))
    ap.add_argument("--in", dest="src"); ap.add_argument("--drc"); ap.add_argument("--out"); ap.add_argument("--ledger")
    a = ap.parse_args(argv)
    if a.fill:
        return _fill(a.fill[0], a.fill[1])
    if not (a.src and a.drc and a.out and a.ledger):
        ap.error("--in/--drc/--out/--ledger 必填")
    print(json.dumps(run(a.src, a.drc, a.out, a.ledger), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
