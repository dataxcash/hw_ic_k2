#!/usr/bin/env python3
"""k2_p4_converge_v1.py — K2 P4 收敛增量 1（**L2 自裁**施工修正；确定性一次算对）。

依据：owner 指令 #14（L2 = 叠层/PDN/走廊/**过孔策略**/等长/热机械 = 自裁勿停）
     + 《宪法》第四条（每次改板须有对应 SPEC 修订）。
输入：前驱件 `k2/hw/k2_v4_8L.l5.kicad_pcb`（P4 增量 3，sha16 5c1b0442）。
输出：新 l5 板 + 机读台账 JSON（逐项 before/after）。

阶段（无搜索式自由：候选序固定、判决式取首个合法者）：
  A 语义/构造归一
    A1 NC 脚网语义：真源 m13 生成器把 NC 脚写成**同名网 `NO_CONNECT`**（27 pad）⇒ DRC 26 条
       **假未连接**（登记册 M-17）。归一 = 该 27 pad **不属任何网**（NC = 无网，非互连网）。
    A2 固定孔 keepout（`K2_HOLE_KEEPOUT_H1..H4`）**不得禁用 pad**：区心即孔位，禁 pad 会命中
       自己的 NPTH pad（自门禁）。
    A3 `B.SilkS` 上的接插件参考文字须镜像（J6/J9/J11/J12/J13）。
  B 旧铜避让新 pad（**锚点保持重布**）：P4 新件/移位件落在既有走线/过孔上（DRC shorting /
    clearance / solder_mask_bridge / hole_clearance）。对每个冲突取**可动侧**（过孔或 ≤1.5mm
    短段）的连通铜簇；只有能**保持连通**（锚点保持、由锚点重布至新位）且满足净距 / 孔净距 /
    板边 / keepout 时施加；新段一律 0/45/90°。
  C 丝印离框（silk_edge_clearance）：被板框截断的丝印件内移 1.0mm。

CLI:
  python3 k2_p4_converge_v1.py --in <前驱板> --drc <前驱板 DRC json> --out <新板> --ledger <json>

边界：不改冻结件（l4 交付板 / 设计源板 / 真源 yaml / SPEC rev-19..28 原件 / criteria/）；
      不派 WORKER；临时仅 /tmp。**判定权归监理**（本器只交测量）。
"""
from __future__ import annotations
import argparse, json, math, collections
import pcbnew

VIA_R, HOLE_R = 0.175, 0.1
CLEAR = {"PCIe85": 0.175, "POWER": 0.2, "LOW_SPEED": 0.1}
MM = pcbnew.ToMM
TYPES = {"hole_clearance", "shorting_items", "clearance", "solder_mask_bridge", "hole_to_hole"}


# ───────────────────────── 几何（与 drc_rules.json 语义一致） ─────────────────────────
def _nc(net):
    if not net: return "LOW_SPEED"
    if net.startswith(("PCIE", "REFCLK")): return "PCIe85"
    if net.startswith(("P3V3", "MCU_", "VREG", "PWR_5V")): return "POWER"
    return "LOW_SPEED"

def _req(a, b): return max(CLEAR[_nc(a)], CLEAR[_nc(b)], 0.1)

def _rot(px, py, cx, cy, deg):
    if not deg: return px, py
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    dx, dy = px - cx, py - cy
    return cx + dx * c - dy * s, cy + dx * s + dy * c

def rect_corners(cx, cy, w, h, rot):
    hw, hh = w / 2.0, h / 2.0
    return [_rot(x, y, cx, cy, rot) for x, y in
            ((cx - hw, cy - hh), (cx + hw, cy - hh), (cx + hw, cy + hh), (cx - hw, cy + hh))]

def pt_seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1; L2 = dx * dx + dy * dy
    if L2 == 0.0: return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))

def _ccw(ax, ay, bx, by, cx, cy): return (cy - ay) * (bx - ax) - (by - ay) * (cx - ax)

def segs_intersect(x1, y1, x2, y2, x3, y3, x4, y4):
    d1 = _ccw(x3, y3, x4, y4, x1, y1); d2 = _ccw(x3, y3, x4, y4, x2, y2)
    d3 = _ccw(x1, y1, x2, y2, x3, y3); d4 = _ccw(x1, y1, x2, y2, x4, y4)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))

def seg_seg_dist(x1, y1, x2, y2, x3, y3, x4, y4):
    if segs_intersect(x1, y1, x2, y2, x3, y3, x4, y4): return 0.0
    return min(pt_seg_dist(x1, y1, x3, y3, x4, y4), pt_seg_dist(x2, y2, x3, y3, x4, y4),
               pt_seg_dist(x3, y3, x1, y1, x2, y2), pt_seg_dist(x4, y4, x1, y1, x2, y2))

def pt_in_poly(px, py, poly):
    inside = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > py) != (y2 > py) and px < x1 + (py - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside

def pt_poly_dist(px, py, poly):
    n = len(poly)
    return min(pt_seg_dist(px, py, poly[i][0], poly[i][1], poly[(i + 1) % n][0], poly[(i + 1) % n][1]) for i in range(n))

def seg_poly_dist(x1, y1, x2, y2, poly):
    best = min(pt_seg_dist(px, py, x1, y1, x2, y2) for px, py in poly)
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]; bx, by = poly[(i + 1) % n]
        best = min(best, seg_seg_dist(x1, y1, x2, y2, ax, ay, bx, by))
    return best


# ───────────────────────── 板模型 ─────────────────────────
class Board:
    def __init__(self, path):
        self.b = pcbnew.LoadBoard(path)
        self.pads, self.tracks, self.vias = [], [], []
        for fp in self.b.GetFootprints():
            for p in fp.Pads():
                pos, sz = p.GetPosition(), p.GetSize()
                circ = p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE
                self.pads.append(dict(uuid=p.m_Uuid.AsString(), ref=fp.GetReference(), num=p.GetNumber(),
                                      net=p.GetNetname(), x=MM(pos.x), y=MM(pos.y), w=MM(sz.x), h=MM(sz.y),
                                      rot=p.GetOrientationDegrees(), circ=circ, obj=p,
                                      poly=None if circ else rect_corners(MM(pos.x), MM(pos.y), MM(sz.x), MM(sz.y), p.GetOrientationDegrees())))
        for t in self.b.GetTracks():
            u = t.m_Uuid.AsString()
            if isinstance(t, pcbnew.PCB_VIA):
                pos = t.GetPosition()
                self.vias.append(dict(uuid=u, net=t.GetNetname(), x=MM(pos.x), y=MM(pos.y),
                                      r=MM(t.GetWidth(pcbnew.F_Cu)) / 2.0, obj=t))
            else:
                s, e = t.GetStart(), t.GetEnd()
                self.tracks.append(dict(uuid=u, net=t.GetNetname(), x1=MM(s.x), y1=MM(s.y), x2=MM(e.x), y2=MM(e.y),
                                        hw=MM(t.GetWidth()) / 2.0, w=MM(t.GetWidth()), layer=t.GetLayer(), obj=t))
        self.keepouts, self.edge, self.zfill = [], [], []
        for z in self.b.Zones():
            if z.GetIsRuleArea():
                for i in range(z.Outline().OutlineCount()):
                    ch = z.Outline().Outline(i)
                    self.keepouts.append(([(MM(ch.CPoint(k).x), MM(ch.CPoint(k).y)) for k in range(ch.PointCount())],
                                          z.GetDoNotAllowVias(), z.GetDoNotAllowTracks(), z.GetZoneName()))
            else:
                net = z.GetNetname()
                if not net: continue
                sps = z.GetFilledPolysList(z.GetFirstLayer())
                for oi in range(sps.OutlineCount()):
                    ch = sps.Outline(oi)
                    poly = [(MM(ch.CPoint(k).x), MM(ch.CPoint(k).y)) for k in range(ch.PointCount())]
                    holes = [[(MM(hc.CPoint(k).x), MM(hc.CPoint(k).y)) for k in range(hc.PointCount())]
                             for hc in (sps.Hole(oi, hi) for hi in range(sps.HoleCount(oi)))]
                    self.zfill.append((net, poly, holes))
        for d_ in self.b.GetDrawings():
            if d_.GetLayer() == pcbnew.Edge_Cuts and hasattr(d_, "GetStart"):
                s, e = d_.GetStart(), d_.GetEnd()
                self.edge.append((MM(s.x), MM(s.y), MM(e.x), MM(e.y)))
        self.by_uuid = {}
        for lst in (self.pads, self.tracks, self.vias):
            for it in lst: self.by_uuid[it["uuid"]] = it
        self.kind = {}
        for p in self.pads: self.kind[p["uuid"]] = "p"
        for t in self.tracks: self.kind[t["uuid"]] = "t"
        for v in self.vias: self.kind[v["uuid"]] = "v"
        self._grid()

    def _grid(self):
        CELL = 1.0
        self.gp, self.gt, self.gv = collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(list)
        def add(g, i, x0, y0, x1, y1):
            for gx in range(int(math.floor(min(x0, x1) / CELL)) - 1, int(math.floor(max(x0, x1) / CELL)) + 2):
                for gy in range(int(math.floor(min(y0, y1) / CELL)) - 1, int(math.floor(max(y0, y1) / CELL)) + 2):
                    g[(gx, gy)].append(i)
        for i, p in enumerate(self.pads): add(self.gp, i, p["x"] - p["w"], p["y"] - p["h"], p["x"] + p["w"], p["y"] + p["h"])
        for i, t in enumerate(self.tracks): add(self.gt, i, t["x1"], t["y1"], t["x2"], t["y2"])
        for i, v in enumerate(self.vias): add(self.gv, i, v["x"], v["y"], v["x"], v["y"])

    def near(self, x0, y0, x1, y1):
        CELL = 1.0; seen = set()
        for gx in range(int(math.floor(min(x0, x1) / CELL)) - 1, int(math.floor(max(x0, x1) / CELL)) + 2):
            for gy in range(int(math.floor(min(y0, y1) / CELL)) - 1, int(math.floor(max(y0, y1) / CELL)) + 2):
                for name, g in (("p", self.gp), ("t", self.gt), ("v", self.gv)):
                    for i in g.get((gx, gy), ()):
                        if (name, i) not in seen:
                            seen.add((name, i)); yield name, i

    def in_zone(self, x, y, net):
        for zn, poly, holes in self.zfill:
            if zn == net and pt_in_poly(x, y, poly) and not any(pt_in_poly(x, y, h) for h in holes):
                return True
        return False

    def in_pad(self, x, y, net=None):
        for p in self.pads:
            if net is not None and p["net"] != net: continue
            if p["circ"]:
                if math.hypot(x - p["x"], y - p["y"]) <= min(p["w"], p["h"]) / 2.0 + 0.03: return True
            elif pt_in_poly(x, y, p["poly"]) or pt_poly_dist(x, y, p["poly"]) <= 0.03: return True
        return False

    def clear_pt(self, x, y, net, excl):
        for es in self.edge:
            if pt_seg_dist(x, y, *es) < 0.3 + VIA_R: return False
        for kind, i in self.near(x, y, x, y):
            if kind == "p":
                p = self.pads[i]
                if p["uuid"] in excl or p["net"] == net: continue
                need = max(VIA_R + _req(net, p["net"]), HOLE_R + 0.25)
                if p["circ"]:
                    if math.hypot(x - p["x"], y - p["y"]) - min(p["w"], p["h"]) / 2.0 < need: return False
                elif pt_in_poly(x, y, p["poly"]) or pt_poly_dist(x, y, p["poly"]) < need: return False
            elif kind == "t":
                t = self.tracks[i]
                if t["uuid"] in excl or t["net"] == net: continue
                need = max(VIA_R + _req(net, t["net"]), HOLE_R + 0.25)
                if pt_seg_dist(x, y, t["x1"], t["y1"], t["x2"], t["y2"]) - t["hw"] < need: return False
            else:
                v = self.vias[i]
                if v["uuid"] in excl or v["net"] == net: continue
                need = max(VIA_R + _req(net, v["net"]), HOLE_R + 0.25)
                if math.hypot(x - v["x"], y - v["y"]) - v["r"] < need: return False
        for poly, dv, dt, _n in self.keepouts:
            if dv and pt_in_poly(x, y, poly): return False
        return True

    def clear_seg(self, x1, y1, x2, y2, net, excl, hw):
        for es in self.edge:
            if seg_seg_dist(x1, y1, x2, y2, *es) < 0.3 + hw: return False
        for kind, i in self.near(x1, y1, x2, y2):
            if kind == "p":
                p = self.pads[i]
                if p["uuid"] in excl or p["net"] == net: continue
                if p["circ"]:
                    if pt_seg_dist(p["x"], p["y"], x1, y1, x2, y2) - min(p["w"], p["h"]) / 2.0 < hw + _req(net, p["net"]): return False
                elif seg_poly_dist(x1, y1, x2, y2, p["poly"]) < hw + _req(net, p["net"]): return False
            elif kind == "t":
                t = self.tracks[i]
                if t["uuid"] in excl or t["net"] == net: continue
                if seg_seg_dist(x1, y1, x2, y2, t["x1"], t["y1"], t["x2"], t["y2"]) < hw + t["hw"] + _req(net, t["net"]): return False
            else:
                v = self.vias[i]
                if v["uuid"] in excl or v["net"] == net: continue
                if pt_seg_dist(v["x"], v["y"], x1, y1, x2, y2) - v["r"] < hw + _req(net, v["net"]): return False
        for poly, dv, dt, _n in self.keepouts:
            if dt and seg_poly_dist(x1, y1, x2, y2, poly) <= 0: return False
        return True

    def comp_of(self, u):
        """与 u 连通的铜簇（走线+过孔；按端点重合 BFS；pad 永不入簇）"""
        byuuid_t = {t["uuid"]: t for t in self.tracks}
        byuuid_v = {v["uuid"]: v for v in self.vias}
        vin = {u} if self.kind[u] == "v" else set()
        tin = set() if self.kind[u] == "v" else {u}
        ch = True
        while ch:
            ch = False
            for tu, t in byuuid_t.items():
                if tu in tin: continue
                if any(abs(t["x1"] - byuuid_v[v]["x"]) <= 0.02 and abs(t["y1"] - byuuid_v[v]["y"]) <= 0.02
                       or abs(t["x2"] - byuuid_v[v]["x"]) <= 0.02 and abs(t["y2"] - byuuid_v[v]["y"]) <= 0.02
                       for v in vin):
                    tin.add(tu); ch = True
            for vu, v in byuuid_v.items():
                if vu in vin: continue
                if any(abs(v["x"] - t["x1"]) <= 0.02 and abs(v["y"] - t["y1"]) <= 0.02
                       or abs(v["x"] - t["x2"]) <= 0.02 and abs(v["y"] - t["y2"]) <= 0.02
                       for t in (byuuid_t[x] for x in tin)):
                    vin.add(vu); ch = True
        return sorted(vin), sorted(tin)

    def anchors_of(self, vin, tin):
        byuuid_v = {v["uuid"]: v for v in self.vias}
        byuuid_t = {t["uuid"]: t for t in self.tracks}
        pts = []
        for tu in tin:
            t = byuuid_t[tu]
            for ex, ey in ((t["x1"], t["y1"]), (t["x2"], t["y2"])):
                if any(abs(ex - byuuid_v[v]["x"]) <= 0.02 and abs(ey - byuuid_v[v]["y"]) <= 0.02 for v in vin): continue
                if self.in_pad(ex, ey, t["net"]) or self.in_zone(ex, ey, t["net"]): pts.append((ex, ey))
        return pts


SEG_RE = None

def canonicalize_new_uuids(path, known_geo):
    """写盘后规范化：新走线/过孔的 uuid 由几何确定性派生（uuid5）——复跑逐字节一致。
    known_geo: 输入件的 (start,end,width,layer,net) 几何指纹集合（不改其 uuid）。"""
    import re, uuid
    txt = open(path, encoding="utf-8").read()
    pat = re.compile(r'\t\(segment\n\t\t\(start ([\-\d.]+) ([\-\d.]+)\)\n\t\t\(end ([\-\d.]+) ([\-\d.]+)\)\n\t\t\(width ([\-\d.]+)\)\n\t\t\(layer "([^"]+)"\)\n\t\t\(net "([^"]*)"\)\n\t\t\(uuid "([^"]+)"\)\n\t\)')
    ns = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
    out = []
    pos = 0
    n_new = 0
    for m in pat.finditer(txt):
        geo = (m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6), m.group(7))
        out.append(txt[pos:m.start()])
        if geo in known_geo:
            out.append(m.group(0))
        else:
            key = "seg|" + "|".join(geo)
            u = str(uuid.uuid5(ns, key))
            out.append(m.group(0).replace(m.group(8), u))
            n_new += 1
        pos = m.end()
    out.append(txt[pos:])
    open(path, "w", encoding="utf-8").write("".join(out))
    return n_new


def _ok45(x1, y1, x2, y2):
    a = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180.0
    return min(abs(a - k) for k in (0, 45, 90, 135, 180)) <= 0.001


# ───────────────────────── 阶段 A ─────────────────────────
def stage_a(B):
    log = {}
    nc = []
    for fp in B.b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() == "NO_CONNECT":
                nc.append((fp.GetReference(), p.GetNumber())); p.SetNetCode(0)
    log["A1_nc_pads_no_net"] = {"n": len(nc), "pads": nc}
    ko = []
    for z in B.b.Zones():
        if z.GetIsRuleArea() and z.GetZoneName().startswith("K2_HOLE_KEEPOUT") and z.GetDoNotAllowPads():
            z.SetDoNotAllowPads(False); ko.append(z.GetZoneName())
    log["A2_hole_keepout_pads_allowed"] = ko
    mir = []
    for fp in B.b.GetFootprints():
        f = fp.Reference()
        if f.GetLayer() == pcbnew.B_SilkS and not f.IsMirrored():
            f.SetMirrored(True); mir.append(fp.GetReference())
    log["A3_mirrored_refs"] = sorted(mir)
    return log


# ───────────────────────── 阶段 B ─────────────────────────
def stage_b(B, drc_path, ledger):
    d = json.load(open(drc_path, encoding="utf-8"))
    byuuid_t = {t["uuid"]: t for t in B.tracks}
    byuuid_v = {v["uuid"]: v for v in B.vias}
    reps, no_sol, skipped, done = [], [], [], set()

    def drop_track(tu):
        B.tracks[:] = [t for t in B.tracks if t["uuid"] != tu]
        B.by_uuid.pop(tu, None); B.kind.pop(tu, None)

    def add_seg(path, w, net):
        import uuid as _uuid
        for i in range(len(path) - 1):
            tr = pcbnew.PCB_TRACK(B.b)
            tr.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(path[i][0]), pcbnew.FromMM(path[i][1])))
            tr.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(path[i + 1][0]), pcbnew.FromMM(path[i + 1][1])))
            tr.SetWidth(pcbnew.FromMM(w)); tr.SetLayer(pcbnew.F_Cu)
            tr.SetNetCode(B.b.GetNetcodeFromNetname(net)); B.b.Add(tr)
            rec = dict(uuid=tr.m_Uuid.AsString(), net=net, x1=path[i][0], y1=path[i][1],
                       x2=path[i + 1][0], y2=path[i + 1][1], hw=w / 2.0, w=w, layer=pcbnew.F_Cu, obj=tr)
            B.tracks.append(rec); B.by_uuid[rec["uuid"]] = rec; B.kind[rec["uuid"]] = "t"
            byuuid_t[rec["uuid"]] = rec

    def apply_move(vin, tin, ddx, ddy):
        for vu in vin:
            v_ = byuuid_v[vu]["obj"]; pp = v_.GetPosition()
            v_.SetPosition(pcbnew.VECTOR2I(pp.x + pcbnew.FromMM(ddx), pp.y + pcbnew.FromMM(ddy)))
        for tu in tin:
            t_ = byuuid_t[tu]["obj"]
            for gs, gg in ((t_.SetStart, t_.GetStart), (t_.SetEnd, t_.GetEnd)):
                pp = gg(); gs(pcbnew.VECTOR2I(pp.x + pcbnew.FromMM(ddx), pp.y + pcbnew.FromMM(ddy)))

    for v in d["violations"]:
        if v["type"] not in TYPES: continue
        us = [i["uuid"] for i in v["items"]]
        if any(u not in B.kind for u in us):
            skipped.append([v["type"], "non-copper-object", [i["description"][:34] for i in v["items"]]]); continue
        mov = [u for u in us if B.kind[u] == "v" or
               (B.kind[u] == "t" and math.hypot(byuuid_t[u]["x2"] - byuuid_t[u]["x1"], byuuid_t[u]["y2"] - byuuid_t[u]["y1"]) <= 1.5)]
        if not mov:
            skipped.append([v["type"], "no-movable", [i["description"][:34] for i in v["items"]]]); continue
        fixed = [u for u in us if u not in mov]
        if not fixed:
            skipped.append([v["type"], "no-anchor"]); continue
        fu = fixed[0]
        if B.kind[fu] == "p":
            ax, ay = B.by_uuid[fu]["x"], B.by_uuid[fu]["y"]
        elif B.kind[fu] == "v":
            ax, ay = byuuid_v[fu]["x"], byuuid_v[fu]["y"]
        else:
            t = byuuid_t[fu]; ax, ay = (t["x1"] + t["x2"]) / 2, (t["y1"] + t["y2"]) / 2
        solved = False
        for mu in mov:
            if mu in done: solved = True; break
            vin, tin = B.comp_of(mu)
            if not (vin or tin) or len(vin) + len(tin) > 8:
                continue
            anchors = sorted(B.anchors_of(vin, tin))
            net = (byuuid_v[mu]["net"] if mu in byuuid_v else byuuid_t[mu]["net"])
            w = 0.2
            for tu in tin: w = byuuid_t[tu]["w"]
            if not anchors:
                for rad in (0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0):
                    if solved: break
                    for k in range(16):
                        a = math.radians(22.5 * k); ddx, ddy = rad * math.cos(a), rad * math.sin(a)
                        if not all(B.clear_pt(byuuid_v[vu]["x"] + ddx, byuuid_v[vu]["y"] + ddy, byuuid_v[vu]["net"], set(vin) | set(tin)) for vu in vin): continue
                        seg_ok = True
                        for tu in tin:
                            t = byuuid_t[tu]
                            if not B.clear_seg(t["x1"] + ddx, t["y1"] + ddy, t["x2"] + ddx, t["y2"] + ddy,
                                               t["net"], set(vin) | set(tin), t["hw"]):
                                seg_ok = False; break
                        if not seg_ok: continue
                        apply_move(vin, tin, ddx, ddy); done |= set(vin) | set(tin)
                        for vu2 in vin: byuuid_v[vu2]["x"] += ddx; byuuid_v[vu2]["y"] += ddy
                        for tu2 in tin:
                            t = byuuid_t[tu2]
                            t["x1"] += ddx; t["y1"] += ddy; t["x2"] += ddx; t["y2"] += ddy
                        reps.append({"type": v["type"], "kind": "translate", "n": len(set(vin) | set(tin)), "d": [round(ddx, 3), round(ddy, 3)]})
                        solved = True; break
                    if solved: break
                if not solved: no_sol.append([v["type"], "isolated-no-legal-translation", [i["description"][:32] for i in v["items"]]])
                if solved: break
                continue
            A = anchors[0]
            if len(vin) != 1:
                no_sol.append([v["type"], "multi-via-cluster", [i2["description"][:30] for i2 in v["items"]]])
                continue
            vu = vin[0]
            vx, vy = byuuid_v[vu]["x"], byuuid_v[vu]["y"]
            ux, uy = vx - ax, vy - ay
            n = math.hypot(ux, uy) or 1.0
            ux, uy = ux / n, uy / n
            for rad in (0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 0.6, 0.8, 1.0, 1.2, 1.5, 2.0):
                if solved: break
                for k in range(16):
                    a = math.radians(22.5 * k)
                    ddx = rad * (ux * math.cos(a) - uy * math.sin(a))
                    ddy = rad * (ux * math.sin(a) + uy * math.cos(a))
                    nx, ny = vx + ddx, vy + ddy
                    dx_, dy_ = nx - A[0], ny - A[1]
                    m_ = min(abs(dx_), abs(dy_))
                    sx = math.copysign(m_, dx_) if dx_ else 0.0
                    sy = math.copysign(m_, dy_) if dy_ else 0.0
                    paths = []
                    if _ok45(A[0], A[1], nx, ny): paths.append([(A[0], A[1]), (nx, ny)])
                    paths += [[(A[0], A[1]), (A[0] + sx, A[1] + sy), (nx, ny)],
                              [(A[0], A[1]), (nx, ny - sy), (nx, ny)],
                              [(A[0], A[1]), (nx - sx, ny), (nx, ny)],
                              [(A[0], A[1]), (nx, A[1]), (nx, ny)],
                              [(A[0], A[1]), (A[0], ny), (nx, ny)]]
                    paths = [pp for pp in paths if all(_ok45(pp[i2][0], pp[i2][1], pp[i2 + 1][0], pp[i2 + 1][1]) for i2 in range(len(pp) - 1))]
                    paths = [pp for pp in paths if all(math.hypot(pp[i2 + 1][0] - pp[i2][0], pp[i2 + 1][1] - pp[i2][1]) >= 0.05 for i2 in range(len(pp) - 1))]
                    good_path = None
                    for pp in paths:
                        if not all(B.clear_seg(pp[i2][0], pp[i2][1], pp[i2 + 1][0], pp[i2 + 1][1], net, set(vin) | set(tin), w / 2.0) for i2 in range(len(pp) - 1)):
                            continue
                        if not B.clear_pt(nx, ny, net, set(vin) | set(tin)):
                            continue
                        good_path = pp; break
                    if good_path is None: continue
                    for tu2 in list(tin):
                        B.b.Remove(byuuid_t[tu2]["obj"]); drop_track(tu2)
                    v_ = byuuid_v[vu]["obj"]; v_.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(nx), pcbnew.FromMM(ny)))
                    byuuid_v[vu]["x"], byuuid_v[vu]["y"] = nx, ny
                    add_seg(good_path, w, net)
                    done |= set(vin) | set(tin)
                    reps.append({"type": v["type"], "kind": "reroute-via", "net": net,
                                 "anchor": [round(A[0], 3), round(A[1], 3)], "via": [round(nx, 3), round(ny, 3)], "legs": len(good_path) - 1})
                    solved = True; break
                if solved: break
    ledger["B"] = {"repairs": reps, "no_solution": no_sol, "skipped": skipped}
    return {"repairs": len(reps), "no_solution": len(no_sol), "skipped": len(skipped)}


# ───────────────────────── 阶段 C ─────────────────────────
def stage_c(B, drc_path, offset=1.0):
    d = json.load(open(drc_path, encoding="utf-8"))
    targets = {i["uuid"] for v in d["violations"] if v["type"] == "silk_edge_clearance"
               for i in v["items"] if "Edge.Cuts" not in i["description"]}
    moved = []
    for fp in B.b.GetFootprints():
        for f in (fp.Reference(), fp.Value()):
            if f.m_Uuid.AsString() in targets:
                p = f.GetPosition(); f.SetPosition(pcbnew.VECTOR2I(p.x, p.y + pcbnew.FromMM(offset)))
                moved.append([fp.GetReference(), "field"])
        for g in fp.GraphicalItems():
            if g.m_Uuid.AsString() in targets and hasattr(g, "Move"):
                g.Move(pcbnew.VECTOR2I(0, pcbnew.FromMM(offset))); moved.append([fp.GetReference(), "shape"])
    return moved


def main(argv=None):
    ap = argparse.ArgumentParser(description="K2 P4 收敛增量 1（L2 自裁施工修正；确定性、分阶段）")
    ap.add_argument("--stage", required=True, choices=["A", "B", "C"], help="施工阶段")
    ap.add_argument("--in", dest="src", required=True, help="输入板")
    ap.add_argument("--drc", help="阶段 B/C 必需：**输入板**的 kicad-cli pcb drc json")
    ap.add_argument("--out", required=True, help="输出板")
    ap.add_argument("--ledger", required=True, help="机读台账 json")
    a = ap.parse_args(argv)
    B = Board(a.src)
    import re as _re
    SEGPAT = _re.compile(r'\t\(segment\n\t\t\(start ([\-\d.]+) ([\-\d.]+)\)\n\t\t\(end ([\-\d.]+) ([\-\d.]+)\)\n\t\t\(width ([\-\d.]+)\)\n\t\t\(layer "([^"]+)"\)\n\t\t\(net "([^"]*)"\)')
    src_txt = open(a.src, encoding="utf-8").read()
    known_geo = {m.group(1, 2, 3, 4, 5, 6, 7) for m in SEGPAT.finditer(src_txt)}
    if a.stage == "A":
        led = {"stage": "A", "A": stage_a(B)}
        pcbnew.ZONE_FILLER(B.b).Fill(B.b.Zones()); B.b.Save(a.out)
        json.dump(led, open(a.ledger, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(json.dumps({"stage": "A", "A1": led["A"]["A1_nc_pads_no_net"]["n"],
                          "A2": len(led["A"]["A2_hole_keepout_pads_allowed"]),
                          "A3": len(led["A"]["A3_mirrored_refs"])}, ensure_ascii=False)); return 0
    if not a.drc:
        print("[infra] 阶段 B/C 须 --drc <输入板 DRC json>"); return 2
    if a.stage == "B":
        led = {"stage": "B"}; led["B_summary"] = stage_b(B, a.drc, led)
        pcbnew.ZONE_FILLER(B.b).Fill(B.b.Zones()); B.b.Save(a.out)
        led["canonicalized_new_uuids"] = canonicalize_new_uuids(a.out, known_geo)
        json.dump(led, open(a.ledger, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(json.dumps({"stage": "B", **led["B_summary"]}, ensure_ascii=False)); return 0
    led = {"stage": "C", "C_silk_moved": stage_c(B, a.drc)}
    pcbnew.ZONE_FILLER(B.b).Fill(B.b.Zones()); B.b.Save(a.out)
    led["canonicalized_new_uuids"] = canonicalize_new_uuids(a.out, known_geo)
    json.dump(led, open(a.ledger, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"stage": "C", "moved": len(led["C_silk_moved"]), "items": led["C_silk_moved"]}, ensure_ascii=False)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
