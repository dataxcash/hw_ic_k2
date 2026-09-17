#!/usr/bin/env python3
"""K2 · P4 收敛增量 9（阶段 G）—— 低速/边带 **F.Cu→In2.Cu 盲孔 + In2 通道布线**。

依据：
- owner 常设裁定 #14（**走廊/布线 · 过孔策略 = L2 自裁勿停**）+ 《宪法》第四条（改板须 SPEC 留痕）。
- SPEC `layer_plan.low_speed_nets`（rev-36 仍载）：低速/边带层 = **In2/B.Cu（F.Cu 外围）**。
- 板内**既有**孔类：`F.Cu→In2.Cu` 盲孔 **92 支已在板**（HDI 阶数≥2，工艺冻结 = A）⇒ 本阶段**不新开孔类、不放松下限**。

动因（T-9，增量 8 逐端取证）：F→B **通孔**类在电阻阵区已耗尽 —— R36/R37/R38/R39/R45 等端点合法通孔位在
3.8–6.2mm 之外，且其 F.Cu 逃逸被 GND 缝合孔排除圈（孔-铜 0.25 + hr + hw = 0.45）与 In5 PCIe 铜堵死。
In2 为近空信号层（106 段），**盲孔 F→In2 的合规判据只涉 F.Cu / In1(GND 整面) / In2 三层** ⇒ 落孔位充裕，
且面铜由区域填充器自动生成反焊盘（同阶段 E 口径）。

口径（**不放松任何 DRC 下限**）：
- 盲孔 **0.20 孔 / 0.35 盘**（板内唯一合法孔类），span = F.Cu..In2.Cu（含 In1.Cu 铜层）。
- 净距 = net class max（PCIe85 .175 / POWER .2 / LOW_SPEED .1，board_min .1）；孔-铜 0.25；**孔-孔 0.25（无同网豁免）**；
  板边铜 0.3；禁 via/禁 track 禁布区规避；线宽 0.200；新段一律 **0/45/90°** 且单腿 ≥0.05；**纯增**。
- 放行闸 = **精确复核**（T-6）：孔位（span 感知）、F.Cu 引线、In2 走线均逐段/逐孔精确比对；栅格仅剪枝。
- 电源类网（P3V3*/MCU_*/VREG*/PWR_5V*/12V*）**不在本阶段**（其路径 = In4 电源面，另行 PDN 阶段）。
未解边逐条登记（`no-fcu-port` / `no-legal-in2-via` / `no-legal-path-on-in2`），**不静默放弃**。
复跑确定性：排序化 + 几何 uuid5 派生。判定权归监理，本器只交测量。
"""
from __future__ import annotations
import argparse, importlib.util, json, math, os, re, shutil, subprocess, sys, time, uuid
import pcbnew

_HERE = os.path.dirname(os.path.abspath(__file__))
def _load(n, f):
    sp = importlib.util.spec_from_file_location(n, os.path.join(_HERE, f))
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
cv = _load("k2cv", "k2_p4_converge_v1.py")
f1 = _load("k2f1", "k2_p4_ls_local_v1.py")
f3 = _load("k2f3", "k2_p4_ls_xlayer_v1.py")

MM = cv.MM
F_CU, IN1_CU, IN2_CU = pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu
SPAN = frozenset((F_CU, IN1_CU, IN2_CU))          # 盲孔 span 内铜层
TRACE_W, VIA_W, VIA_D = 0.20, 0.35, 0.20
HW, VIA_R, HOLE_R = TRACE_W / 2.0, VIA_W / 2.0, VIA_D / 2.0
STEP, NEAR_R, ESC_R, MAXTRY = 0.10, 2.5, 6.5, 10
TIME_BUDGET = 900.0
POWER_PREFIX = ("P3V3", "MCU_", "VREG", "PWR_5V", "12V")
CU_ALL = [L for L in range(32) if pcbnew.IsCopperLayer(L)]
NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
VIA_BLOCK = ('\t(via blind\n\t\t(at {x} {y})\n\t\t(size 0.35)\n\t\t(drill 0.2)\n'
             '\t\t(layers "F.Cu" "In2.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{u}")\n\t)\n')


def via_uuid(net, x, y):
    return str(uuid.uuid5(NS, "k2p4in2|via|%s|%s|%s" % (net, f1._fmt(x), f1._fmt(y))))


class SpanModel:
    """span 感知的**精确**几何判定（T-10：kicad-cli DRC 的孔-铜为 span 感知，已实测 304 对反例零违规）。

    - 走线（层 L）：只与 **L 层铜** + **span 含 L 的孔**交互（盲孔 F→In1 的孔不阻 In2/B.Cu 走线）。
    - 过孔（span = F..In2）：与 span 内铜层交互；孔-孔对**全部**既有孔取 0.25（保守，深度重叠未细分）。
    """

    def __init__(self, ctx, board):
        self.c = ctx
        self.tr = [t for t in ctx.tracks if t["layer"] in SPAN]
        self.pads = [p for p in ctx.pads.values() if p["lay"] & SPAN]
        self.vias = [v for v in ctx.vias.values() if v["lay"] & SPAN]
        self.holes_all = list(ctx.holes)
        self.holes_by_layer = {}
        for t in board.GetTracks():
            if not isinstance(t, pcbnew.PCB_VIA): continue
            pos, ls = t.GetPosition(), t.GetLayerSet()
            lay = frozenset(L for L in CU_ALL if ls.Contains(L))
            self.holes_all.append((MM(pos.x), MM(pos.y), MM(t.GetDrillValue()) / 2.0, t.GetNetname()))
            for L in lay: self.holes_by_layer.setdefault(L, []).append((MM(pos.x), MM(pos.y), MM(t.GetDrillValue()) / 2.0, t.GetNetname()))
        for fp in board.GetFootprints():
            for pd in fp.Pads():
                dz = pd.GetDrillSize()
                if dz.x <= 0: continue
                pos, ls = pd.GetPosition(), pd.GetLayerSet()
                lay = frozenset(L for L in CU_ALL if ls.Contains(L))
                self.holes_all.append((MM(pos.x), MM(pos.y), MM(dz.x) / 2.0, pd.GetNetname()))
                for L in lay: self.holes_by_layer.setdefault(L, []).append((MM(pos.x), MM(pos.y), MM(dz.x) / 2.0, pd.GetNetname()))

    def add_track(self, rec):
        if rec["layer"] in SPAN: self.tr.append(rec)

    def add_via(self, rec):
        if rec["lay"] & SPAN: self.vias.append(rec)

    def add_hole(self, x, y, net):
        """新落盲孔的孔登记（span = F.Cu..In2.Cu）：供后续边的孔-孔与孔-铜精确判定（否则同轮内互相漏判）。"""
        self.holes_all.append((x, y, HOLE_R, net))
        for L in SPAN: self.holes_by_layer.setdefault(L, []).append((x, y, HOLE_R, net))

    def via_ok(self, net, x, y):
        c = self.c
        for e in c.edge:
            if cv.pt_seg_dist(x, y, *e) < 0.3 + VIA_R: return False
        for poly in c.keep_v:
            if cv.pt_in_poly(x, y, poly): return False
        for t in self.tr:
            if t["net"] == net: continue
            need = max(VIA_R + cv._req(net, t["net"]), HOLE_R + 0.25 + t["hw"]) + t["hw"]
            if x < min(t["x1"], t["x2"]) - need or x > max(t["x1"], t["x2"]) + need: continue
            if y < min(t["y1"], t["y2"]) - need or y > max(t["y1"], t["y2"]) + need: continue
            if cv.pt_seg_dist(x, y, t["x1"], t["y1"], t["x2"], t["y2"]) - t["hw"] < need - t["hw"]: return False
        for p in self.pads:
            if p["net"] == net: continue
            need = max(VIA_R + cv._req(net, p["net"]), HOLE_R + 0.25)
            if x < p["x"] - p["w"] / 2 - need or x > p["x"] + p["w"] / 2 + need: continue
            if y < p["y"] - p["h"] / 2 - need or y > p["y"] + p["h"] / 2 + need: continue
            if p["circ"]:
                if math.hypot(x - p["x"], y - p["y"]) - min(p["w"], p["h"]) / 2.0 < need: return False
            elif cv.pt_in_poly(x, y, p["poly"]) or cv.pt_poly_dist(x, y, p["poly"]) < need: return False
        for v in self.vias:
            if v["net"] == net: continue
            # 过孔-过孔：铜-铜（VIA_R+v.r+req）∪ 本孔-其铜（HOLE_R+v.r+0.25）
            need = max(VIA_R + v["r"] + cv._req(net, v["net"]), HOLE_R + v["r"] + 0.25)
            if math.hypot(x - v["x"], y - v["y"]) < need: return False
        for (hx, hy, hr, hnet) in self.holes_all:      # 孔-孔 0.25（**无同网豁免**，含同网 PTH 自身的孔）
            if abs(x - hx) > 1.0 or abs(y - hy) > 1.0: continue
            if math.hypot(x - hx, y - hy) < HOLE_R + 0.25 + hr: return False
        return True

    def seg_ok(self, layer, net, x1, y1, x2, y2, hw=HW):
        c = self.c
        if math.hypot(x2 - x1, y2 - y1) < 1e-9: return True
        for e in c.edge:
            if cv.seg_seg_dist(x1, y1, x2, y2, *e) < 0.3 + hw: return False
        for poly in c.keep_t:
            if cv.seg_poly_dist(x1, y1, x2, y2, poly) <= 0: return False
        for t in self.tr:
            if t["layer"] != layer or t["net"] == net: continue
            need = hw + t["hw"] + cv._req(net, t["net"])
            if max(x1, x2) + need < min(t["x1"], t["x2"]) or min(x1, x2) - need > max(t["x1"], t["x2"]): continue
            if max(y1, y2) + need < min(t["y1"], t["y2"]) or min(y1, y2) - need > max(t["y1"], t["y2"]): continue
            if cv.seg_seg_dist(x1, y1, x2, y2, t["x1"], t["y1"], t["x2"], t["y2"]) < need: return False
        for p in self.pads:
            if layer not in p["lay"] or p["net"] == net: continue
            need = hw + cv._req(net, p["net"])
            if max(x1, x2) + need < p["x"] - p["w"] / 2 or min(x1, x2) - need > p["x"] + p["w"] / 2: continue
            if max(y1, y2) + need < p["y"] - p["h"] / 2 or min(y1, y2) - need > p["y"] + p["h"] / 2: continue
            if p["circ"]:
                if cv.pt_seg_dist(p["x"], p["y"], x1, y1, x2, y2) - min(p["w"], p["h"]) / 2.0 < need: return False
            elif cv.seg_poly_dist(x1, y1, x2, y2, p["poly"]) < need: return False
        for v in self.vias:
            if layer not in v["lay"] or v["net"] == net: continue
            if cv.pt_seg_dist(v["x"], v["y"], x1, y1, x2, y2) - v["r"] < hw + cv._req(net, v["net"]): return False
        for (hx, hy, hr, hnet) in self.holes_by_layer.get(layer, ()):
            if hnet == net: continue
            if cv.pt_seg_dist(hx, hy, x1, y1, x2, y2) < hw + 0.25 + hr: return False
        return True

    def poly_ok(self, layer, net, pts):
        for k in range(len(pts) - 1):
            if not self.seg_ok(layer, net, pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1]): return False
        return True

    def bad_grid(self, net, layer, a, b, extra=()):
        """层 L 的栅格剪枝集（格心，no-margin）。返回 (bad, gx0, gx1, gy0, gy1)。"""
        gx0 = math.floor((min(a[0], b[0]) - 1.0) / STEP); gx1 = math.ceil((max(a[0], b[0]) + 1.0) / STEP)
        gy0 = math.floor((min(a[1], b[1]) - 1.0) / STEP); gy1 = math.ceil((max(a[1], b[1]) + 1.0) / STEP)
        rb = (min(a[0], b[0]) - 1.0, max(a[0], b[0]) + 1.0, min(a[1], b[1]) - 1.0, max(a[1], b[1]) + 1.0)
        def hits(xa, xb, ya, yb, rad):
            return not (xb + rad < rb[0] or xa - rad > rb[1] or yb + rad < rb[2] or ya - rad > rb[3])
        bad = set()
        def cand(cx, cy, rad):
            for i in range(math.floor((cx - rad) / STEP), math.ceil((cx + rad) / STEP) + 1):
                for j in range(math.floor((cy - rad) / STEP), math.ceil((cy + rad) / STEP) + 1):
                    if gx0 <= i <= gx1 and gy0 <= j <= gy1 and (i * STEP - cx) ** 2 + (j * STEP - cy) ** 2 <= rad * rad:
                        bad.add((i, j))
        def cseg(ax, ay, bx, by, rad):
            for i in range(math.floor((min(ax, bx) - rad) / STEP), math.ceil((max(ax, bx) + rad) / STEP) + 1):
                for j in range(math.floor((min(ay, by) - rad) / STEP), math.ceil((max(ay, by) + rad) / STEP) + 1):
                    if gx0 <= i <= gx1 and gy0 <= j <= gy1 and cv.pt_seg_dist(i * STEP, j * STEP, ax, ay, bx, by) <= rad:
                        bad.add((i, j))
        for t in self.tr:
            if t["layer"] != layer or t["net"] == net: continue
            rad = t["hw"] + HW + cv._req(net, t["net"])
            if not hits(min(t["x1"], t["x2"]), max(t["x1"], t["x2"]), min(t["y1"], t["y2"]), max(t["y1"], t["y2"]), rad): continue
            cseg(t["x1"], t["y1"], t["x2"], t["y2"], rad)
        for p in self.pads:
            if layer not in p["lay"] or p["net"] == net: continue
            r = HW + cv._req(net, p["net"])
            if not hits(p["x"] - p["w"] / 2, p["x"] + p["w"] / 2, p["y"] - p["h"] / 2, p["y"] + p["h"] / 2, r): continue
            if p["circ"]:
                cand(p["x"], p["y"], min(p["w"], p["h"]) / 2.0 + r)
            else:
                for k in range(len(p["poly"])):
                    q1, q2 = p["poly"][k], p["poly"][(k + 1) % len(p["poly"])]
                    cseg(q1[0], q1[1], q2[0], q2[1], r)
                xa = [q[0] for q in p["poly"]]; ya = [q[1] for q in p["poly"]]
                for i in range(max(gx0, math.floor(min(xa) / STEP)), min(gx1, math.ceil(max(xa) / STEP)) + 1):
                    for j in range(max(gy0, math.floor(min(ya) / STEP)), min(gy1, math.ceil(max(ya) / STEP)) + 1):
                        if cv.pt_in_poly(i * STEP, j * STEP, p["poly"]): bad.add((i, j))
        for v in self.vias:
            if layer not in v["lay"] or v["net"] == net: continue
            rad = v["r"] + HW + cv._req(net, v["net"])
            if not hits(v["x"], v["x"], v["y"], v["y"], rad): continue
            cand(v["x"], v["y"], rad)
        for (hx, hy, hr, hnet) in self.holes_by_layer.get(layer, ()):
            if hnet == net: continue
            rad = hr + 0.25 + HW
            if not hits(hx, hx, hy, hy, rad): continue
            cand(hx, hy, rad)
        for e in self.c.edge:
            if not hits(min(e[0], e[2]), max(e[0], e[2]), min(e[1], e[3]), max(e[1], e[3]), HW + 0.3): continue
            cseg(e[0], e[1], e[2], e[3], HW + 0.3)
        for poly in self.c.keep_t:
            xa = [q[0] for q in poly]; ya = [q[1] for q in poly]
            if not (min(xa) <= rb[1] and max(xa) >= rb[0] and min(ya) <= rb[3] and max(ya) >= rb[2]): continue
            for i in range(max(gx0, math.floor(min(xa) / STEP)), min(gx1, math.ceil(max(xa) / STEP)) + 1):
                for j in range(max(gy0, math.floor(min(ya) / STEP)), min(gy1, math.ceil(max(ya) / STEP)) + 1):
                    if cv.pt_in_poly(i * STEP, j * STEP, poly): bad.add((i, j))
        for (i, j) in extra: bad.add((i, j))
        return bad, gx0, gx1, gy0, gy1

    def astar(self, net, layer, a, b, cap=200000, attempts=4):
        """层 `layer` 的 0/45/90° 通道搜索：栅格（no-margin）剪枝 → 精确复核 → 失败段回灌重试。"""
        extra = set()
        for _ in range(attempts):
            pts = self._astar_once(net, layer, a, b, extra, cap)
            if pts is None: return None
            pts = f3.simplify(pts)
            bad_seg = []
            for k in range(len(pts) - 1):
                x1, y1, x2, y2 = pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1]
                if math.hypot(x2 - x1, y2 - y1) < 1e-9: continue
                if not self.seg_ok(layer, net, x1, y1, x2, y2): bad_seg.append((x1, y1, x2, y2))
            if not bad_seg: return pts
            for (x1, y1, x2, y2) in bad_seg:     # 回灌：把失败段邻域（0.5mm）标为障碍
                gx0 = math.floor((x1 - 0.5) / STEP); gx1 = math.ceil((x1 + 0.5) / STEP)
                for i in range(min(math.floor((x1 - 0.5) / STEP), math.floor((x2 - 0.5) / STEP)),
                               max(math.ceil((x1 + 0.5) / STEP), math.ceil((x2 + 0.5) / STEP)) + 1):
                    for j in range(min(math.floor((y1 - 0.5) / STEP), math.floor((y2 - 0.5) / STEP)),
                                   max(math.ceil((y1 + 0.5) / STEP), math.ceil((y2 + 0.5) / STEP)) + 1):
                        if cv.pt_seg_dist(i * STEP, j * STEP, x1, y1, x2, y2) <= 0.5: extra.add((i, j))
        return None

    def _astar_once(self, net, layer, a, b, extra, cap):
        import heapq
        bad, gx0, gx1, gy0, gy1 = self.bad_grid(net, layer, a, b, extra)
        i0, j0 = int(round(a[0] / STEP)), int(round(a[1] / STEP))
        if (i0, j0) in bad: return None
        gi, gj = b[0] / STEP, b[1] / STEP
        def seg_clear(x1, y1, x2, y2):
            n = int(max(abs(x2 - x1), abs(y2 - y1)) / STEP * 2) + 2
            for k in range(n + 1):
                t = k / n
                i = int(round((x1 + (x2 - x1) * t) / STEP)); j = int(round((y1 + (y2 - y1) * t) / STEP))
                if (i, j) in bad: return False
            return True
        def conn(x, y):
            cands = [(x, b[1]), (b[0], y)]
            for s_ in (1.0, -1.0):
                cands.append((x + s_ * (b[1] - y), b[1]))
                cands.append((b[0], y + s_ * (b[0] - x)))
            for cx, cy in cands:
                if seg_clear(x, y, cx, cy) and seg_clear(cx, cy, b[0], b[1]): return [(cx, cy)]
            dx, dy = b[0] - x, b[1] - y
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
                return [(p[0] * STEP, p[1] * STEP) for p in path] + c + [(b[0], b[1])]
            for dx, dy in DIRS:
                nb = (cur[0] + dx, cur[1] + dy)
                if not (gx0 <= nb[0] <= gx1 and gy0 <= nb[1] <= gy1) or nb in bad: continue
                ng = g + STEP * (math.sqrt(2) if dx and dy else 1.0)
                if ng < gsc.get(nb, 1e18) - 1e-9:
                    gsc[nb] = ng; came[nb] = cur
                    heapq.heappush(openq, (ng + h(*nb), ng, nb))
        return None


def _in_pad(p, x, y, tol=0.002):
    if p["circ"]:
        return math.hypot(x - p["x"], y - p["y"]) <= min(p["w"], p["h"]) / 2.0 + tol
    return cv.pt_in_poly(x, y, p["poly"]) or cv.pt_poly_dist(x, y, p["poly"]) <= tol


def near_via_list(sm, ctx, net, anchor, target, k=2):
    """anchor（同网 F.Cu 接点）附近的合法 F→In2 盲孔候选（最多 k 个，按离 target 距离升序）。
    次序：① 盘中孔（SMD 盘内 · 零长引线）→ ② 环状候选 + ≤2 腿 45° 引线 → ③ F.Cu A* 多腿逃逸。
    **候选多样化**：同一锚点给出多个落孔位，供上层尝试不同走廊（贪心单点会误堵后续边）。"""
    def rank(lst):
        lst.sort(key=lambda t: t[0])
        return [(v, l) for _d, v, l in lst[:k]]
    for p in ctx.pads.values():
        if p["net"] != net or p["hole"] > 0: continue
        if abs(p["x"] - anchor[0]) > 1e-6 or abs(p["y"] - anchor[1]) > 1e-6: continue
        out = []; r = 0.0
        while r <= 0.50 + 1e-9:
            n = 1 if r < 1e-9 else 72
            for kk in range(n):
                a = 0.0 if r < 1e-9 else math.radians(5.0 * kk)
                x, y = p["x"] + r * math.cos(a), p["y"] + r * math.sin(a)
                if not _in_pad(p, x, y): continue
                if not sm.via_ok(net, x, y): continue
                out.append((math.hypot(x - target[0], y - target[1]), (x, y), [(x, y)]))
            if out: return rank(out)
            r = round(r + 0.025, 4)
    out = []; r = 0.0
    while r <= NEAR_R + 1e-9:
        for kk in range(36):
            a = math.radians(10.0 * kk)
            x, y = anchor[0] + r * math.cos(a), anchor[1] + r * math.sin(a)
            if not sm.via_ok(net, x, y): continue
            for pp in cv._paths45(anchor, (x, y)):
                pts = list(pp)
                if sm.poly_ok(F_CU, net, pts):
                    out.append((math.hypot(x - target[0], y - target[1]), (x, y), pts))
                    break
        if out: return rank(out)
        r = round(r + 0.05, 4)
    out = []; tried = 0; r = round(STEP, 4)
    while r <= ESC_R + 1e-9:
        cands = []
        for kk in range(72):
            a = math.radians(5.0 * kk)
            x, y = anchor[0] + r * math.cos(a), anchor[1] + r * math.sin(a)
            if not sm.via_ok(net, x, y): continue
            cands.append((math.hypot(x - target[0], y - target[1]), x, y))
        cands.sort()
        for _d, x, y in cands:
            if tried >= MAXTRY: return rank(out)
            tried += 1
            pts = sm.astar(net, F_CU, anchor, (x, y))
            if pts is None: continue
            out.append((math.hypot(x - target[0], y - target[1]), (x, y), pts))
            if len(out) >= k: return rank(out)
        r = round(r + STEP, 4)
    return rank(out)


def _centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def run(src, drc_path, out_path, ledger_path):
    b = pcbnew.LoadBoard(src)
    ctx = f3.Ctx(b)
    sm = SpanModel(ctx, b)
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
    added, blocked, blocks, skipped_power = [], [], [], []
    t0 = time.time()
    for dist, net, ka, kb in edges:
        if net.startswith(POWER_PREFIX):
            skipped_power.append({"net": net, "dist": dist}); continue
        if time.time() - t0 > TIME_BUDGET:
            blocked.append({"net": net, "dist": dist, "why": "deferred-time-budget"}); continue
        ca, cb = find(ka), find(kb)
        if ca == cb: continue
        ba, fa = f3._ports(ctx, find, ca)
        bb, fb = f3._ports(ctx, find, cb)
        if not fa or not fb:
            blocked.append({"net": net, "dist": dist, "why": "no-fcu-port"}); continue
        ra = _centroid(bb or fb); rb = _centroid(ba or fa)
        # ⓪ 同层 F.Cu 直连（免孔，最简）：只在近端若干对端口上试（有界）
        direct = None
        pa_s = sorted(fa, key=lambda q: math.hypot(q[0] - rb[0], q[1] - rb[1]))[:3]
        pb_s = sorted(fb, key=lambda q: math.hypot(q[0] - ra[0], q[1] - ra[1]))[:3]
        pairs = sorted([(math.hypot(p[0] - q[0], p[1] - q[1]), p, q) for p in pa_s for q in pb_s])
        for _d, p, q in pairs[:6]:
            r0 = sm.astar(net, F_CU, p, q)
            if r0 is not None:
                direct = (p, q, r0); break
        # ① In2：两端候选孔位（每端 ≤4），按总距升序尝试
        cand_a, cand_b = [], []
        for p in sorted(fa, key=lambda q: math.hypot(q[0] - rb[0], q[1] - rb[1]))[:4]:
            cand_a += [(v, l, p) for (v, l) in near_via_list(sm, ctx, net, p, rb, k=2)]
            if len(cand_a) >= 4: break
        for p in sorted(fb, key=lambda q: math.hypot(q[0] - ra[0], q[1] - ra[1]))[:4]:
            cand_b += [(v, l, p) for (v, l) in near_via_list(sm, ctx, net, p, ra, k=2)]
            if len(cand_b) >= 4: break
        if not direct and (not cand_a or not cand_b):
            blocked.append({"net": net, "dist": dist, "why": "no-legal-in2-via"}); continue
        solved = None
        if direct:
            solved = ("direct", direct[2], None)
        else:
            combos = sorted([(math.hypot(a[0][0] - b[0][0], a[0][1] - b[0][1]), a, b) for a in cand_a for b in cand_b])
            for _d, a, b in combos[:16]:
                r2 = sm.astar(net, IN2_CU, a[0], b[0])
                if r2 is not None:
                    solved = ("in2", r2, (a, b)); break
        if not solved:
            blocked.append({"net": net, "dist": dist, "why": "no-legal-path-on-in2"}); continue
        # ── 落账（同步更新模型，供后续边精确判定） ──
        placed = []
        ends = () if solved[0] == "direct" else solved[2]
        for (vxy, legs, _anchor) in ends:
            u = via_uuid(net, vxy[0], vxy[1])
            blocks.append(VIA_BLOCK.format(x=f1._fmt(vxy[0]), y=f1._fmt(vxy[1]), net=net, u=u))
            rec = dict(net=net, x=vxy[0], y=vxy[1], r=VIA_R, hole=HOLE_R, lay=set(SPAN))
            ctx.vias[u] = rec; ctx.holes.append((vxy[0], vxy[1], HOLE_R, net))
            sm.add_via(rec); sm.add_hole(vxy[0], vxy[1], net)
            placed.append([round(vxy[0], 3), round(vxy[1], 3)])
        for legs in ([],) if solved[0] == "direct" else (ends[0][1], ends[1][1]):
            for k in range(len(legs) - 1):
                x1, y1, x2, y2 = legs[k][0], legs[k][1], legs[k + 1][0], legs[k + 1][1]
                if math.hypot(x2 - x1, y2 - y1) < 0.05: continue
                u = f1.seg_uuid(net, "F.Cu", x1, y1, x2, y2)
                blocks.append(f1.SEG_BLOCK.format(x1=f1._fmt(x1), y1=f1._fmt(y1), x2=f1._fmt(x2), y2=f1._fmt(y2),
                                                  layer="F.Cu", net=net, u=u))
                rec = dict(uuid=u, net=net, layer=F_CU, x1=x1, y1=y1, x2=x2, y2=y2, hw=HW)
                ctx.tracks.append(rec); sm.add_track(rec)
        route = solved[1]
        route_layer = F_CU if solved[0] == "direct" else IN2_CU
        route_tag = "F.Cu" if solved[0] == "direct" else "In2.Cu"
        for k in range(len(route) - 1):
            x1, y1, x2, y2 = route[k][0], route[k][1], route[k + 1][0], route[k + 1][1]
            if math.hypot(x2 - x1, y2 - y1) < 0.05: continue
            u = f1.seg_uuid(net, route_tag, x1, y1, x2, y2)
            blocks.append(f1.SEG_BLOCK.format(x1=f1._fmt(x1), y1=f1._fmt(y1), x2=f1._fmt(x2), y2=f1._fmt(y2),
                                              layer=route_tag, net=net, u=u))
            rec = dict(uuid=u, net=net, layer=route_layer, x1=x1, y1=y1, x2=x2, y2=y2, hw=HW)
            ctx.tracks.append(rec); sm.add_track(rec)
        added.append({"net": net, "dist": dist, "vias": placed, "kind": solved[0],
                      "in2_legs": len(route) - 1,
                      "fcu_stub_legs": 0 if solved[0] == "direct" else sum(len(l) - 1 for l in (ends[0][1], ends[1][1]))})
    led = {"stage": "G", "edges": len(edges), "added": added, "blocked": blocked, "skipped_power": skipped_power,
           "G_summary": {"added": len(added), "blocked": len(blocked), "skipped_power": len(skipped_power),
                         "reasons": {k: sum(1 for x in blocked if x["why"] == k) for k in sorted({x["why"] for x in blocked})},
                         "vias_placed": sum(len(a["vias"]) for a in added)}}
    json.dump(led, open(ledger_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if blocks:
        txt = open(src, encoding="utf-8").read()
        anchor = txt.index("\t(segment\n")
        tmp = out_path + ".g_tmp.kicad_pcb"
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
    return led["G_summary"]


def _fill(tmp, out_path):
    b2 = pcbnew.LoadBoard(tmp)
    if b2 is None:
        raise SystemExit("_fill: LoadBoard -> None")
    pcbnew.ZONE_FILLER(b2).Fill(b2.Zones())
    b2.Save(out_path)
    print(json.dumps({"fill": "ok"}))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="K2 P4 阶段 G：低速/边带 F.Cu→In2.Cu 盲孔 + In2 通道布线")
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
