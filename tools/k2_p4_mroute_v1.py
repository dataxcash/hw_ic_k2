#!/usr/bin/env python3
"""K2 · P4 增量 15（L2 自裁）—— **多层迷宫布线器 v1**（span 感知孔类 + 扩窗 + 精确放行闸）。

依据：owner 常设裁定 #14（走廊/布线/过孔策略 = **L2 自裁勿停**）+ 《宪法》第四条（改板须 SPEC 留痕）。

动因（增量 15 取证）：
- 既有 F1/F2/F3/G 四器对残 14 边**全部 0 解**。根因二：
  ① F3 的 A* 搜索窗 = **两端 bbox**（±1mm）⇒ 真实走廊（南侧 y 68..78 的 B.Cu 围裙、
     板 x 23..143 / y 33..79）在窗外，几何上不可能被搜到；
  ② F3/G 的孔判定为**全层通孔口径**（或单 span 硬编码）⇒ 对既有盲/埋孔类（F→In2 / In2→In5 /
     In5→B）系统性过保守。
- 本器：多层 A*（层 = F.Cu / In2.Cu / In5.Cu / B.Cu），过孔转移只用**板内既有孔 span 类**
  （不新开孔类、不放松下限）；窗 = 两端 bbox 扩 `--margin`（默认 14mm，夹在板内）；
  粗搜 0.25mm → 走廊内精搜 0.10mm；**放行闸 = 逐段 `seg_exact`（层感知）+ 逐孔 `via_exact`（span 感知）**，
  任一不符即弃（栅格仅剪枝）。新段一律 0/45/90° 且单腿 ≥0.05；纯增；uuid5 由几何派生（复跑逐字节同）。

CLI: python3 k2_p4_mroute_v1.py --in <board> --drc <drc.json> --out <board> --ledger <json>
     [--margin 14] [--only-net NET] [--dry-run]
"""
from __future__ import annotations
import argparse, importlib.util, json, math, os, re, shutil, subprocess, sys, uuid
from array import array

_HERE = os.path.dirname(os.path.abspath(__file__))
def _load(n, f):
    sp = importlib.util.spec_from_file_location(n, os.path.join(_HERE, f))
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
cv = _load("k2cv", "k2_p4_converge_v1.py")
f1 = _load("k2f1", "k2_p4_ls_local_v1.py")
f3 = _load("k2f3", "k2_p4_ls_xlayer_v1.py")

import pcbnew
F_CU, IN1_CU, IN2_CU, IN3_CU, IN4_CU, IN5_CU, IN6_CU, B_CU = (
    pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu,
    pcbnew.In5_Cu, pcbnew.In6_Cu, pcbnew.B_Cu)
LAYERS = [F_CU, IN2_CU, IN5_CU, B_CU]
LNAME = {F_CU: "F.Cu", IN2_CU: "In2.Cu", IN5_CU: "In5.Cu", B_CU: "B.Cu",
         IN1_CU: "In1.Cu", IN3_CU: "In3.Cu", IN4_CU: "In4.Cu", IN6_CU: "In6.Cu"}
# 板内既有孔 span 类（铜层集合，按叠层序 F,In1,In2,In3,In4,In5,In6,B）
def _span(a, b):
    order = [F_CU, IN1_CU, IN2_CU, IN3_CU, IN4_CU, IN5_CU, IN6_CU, B_CU]
    i, j = order.index(a), order.index(b)
    if i > j: i, j = j, i
    return frozenset(order[i:j + 1])
SPAN_OF = {frozenset((F_CU, IN2_CU)): _span(F_CU, IN2_CU),
           frozenset((F_CU, IN5_CU)): _span(F_CU, IN5_CU),
           frozenset((F_CU, B_CU)): _span(F_CU, B_CU),
           frozenset((IN2_CU, IN5_CU)): _span(IN2_CU, IN5_CU),
           frozenset((IN5_CU, B_CU)): _span(IN5_CU, B_CU)}
TRANS = {(F_CU, IN2_CU), (F_CU, IN5_CU), (F_CU, B_CU), (IN2_CU, IN5_CU), (IN5_CU, B_CU)}
TRACE_W, VIA_W, VIA_D = 0.20, 0.35, 0.20
HW, VIA_R, HOLE_R = TRACE_W / 2.0, VIA_W / 2.0, VIA_D / 2.0
GMARGIN = 0.06          # 栅格安全余量（仅剪枝）
VIA_COST = 2.0          # 过孔代价（mm 当量）
NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
SEG_BLOCK = ('\t(segment\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n\t\t(width 0.2)\n'
             '\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{u}")\n\t)\n')
VIA_BLOCK = ('\t(via{blind}\n\t\t(at {x} {y})\n\t\t(size 0.35)\n\t\t(drill 0.2)\n'
             '\t\t(layers "{l1}" "{l2}")\n\t\t(net "{net}")\n\t\t(uuid "{u}")\n\t)\n')


def _fmt(v):
    s = "%.6f" % v
    s = s.rstrip("0").rstrip(".")
    return s if s else "0"


def seg_uuid(net, layer, x1, y1, x2, y2):
    return str(uuid.uuid5(NS, "k2mroute|seg|%s|%s|%s|%s|%s|%s" % (net, LNAME[layer], _fmt(x1), _fmt(y1), _fmt(x2), _fmt(y2))))


def via_uuid(net, l1, l2, x, y):
    return str(uuid.uuid5(NS, "k2mroute|via|%s|%s|%s|%s|%s" % (net, LNAME[l1], LNAME[l2], _fmt(x), _fmt(y))))


# ─────────────────────── 精确放行闸（层感知 / span 感知） ───────────────────────
def seg_exact(ctx, layer, net, x1, y1, x2, y2, hw=HW):
    for e in ctx.edge:
        if cv.seg_seg_dist(x1, y1, x2, y2, *e) < 0.3 + hw: return False
    for poly in ctx.keep_t:
        if cv.seg_poly_dist(x1, y1, x2, y2, poly) <= 0: return False
    rb = (min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2))
    for t in ctx.tracks:
        if t["layer"] != layer or t["net"] == net: continue
        rad = hw + t["hw"] + cv._req(net, t["net"])
        if not ctx._bb_hit(rb, t["x1"], t["y1"], t["x2"], t["y2"], rad): continue
        if cv.seg_seg_dist(x1, y1, x2, y2, t["x1"], t["y1"], t["x2"], t["y2"]) < rad: return False
    for p in ctx.pads.values():
        if layer not in p["lay"] or p["net"] == net: continue
        rad = hw + cv._req(net, p["net"])
        if p["circ"]:
            if cv.pt_seg_dist(p["x"], p["y"], x1, y1, x2, y2) - min(p["w"], p["h"]) / 2 < rad: return False
        else:
            if cv.seg_poly_dist(x1, y1, x2, y2, p["poly"]) < rad: return False
    for v in ctx.vias.values():
        if layer not in v["lay"] or v["net"] == net: continue
        rad = hw + cv._req(net, v["net"])
        if cv.pt_seg_dist(v["x"], v["y"], x1, y1, x2, y2) - v["r"] < rad: return False
    for (hx, hy, hr, hnet, hlay) in ctx.holes:
        if hnet == net or layer not in hlay: continue
        if cv.pt_seg_dist(hx, hy, x1, y1, x2, y2) < hr + 0.25 + hw: return False
    return True


def via_exact(ctx, net, x, y, span):
    for e in ctx.edge:
        if cv.pt_seg_dist(x, y, *e) < 0.3 + VIA_R: return False
    for poly in ctx.keep_v:
        if cv.pt_in_poly(x, y, poly): return False
    for t in ctx.tracks:
        if t["net"] == net or t["layer"] not in span: continue
        need = max(VIA_R + cv._req(net, t["net"]), HOLE_R + 0.25 + t["hw"])
        if cv.pt_seg_dist(x, y, t["x1"], t["y1"], t["x2"], t["y2"]) - t["hw"] < need: return False
    for p in ctx.pads.values():
        if p["net"] == net or not (p["lay"] & span): continue
        need = max(VIA_R + cv._req(net, p["net"]), HOLE_R + 0.25)
        if p["circ"]:
            if math.hypot(x - p["x"], y - p["y"]) - min(p["w"], p["h"]) / 2 < need: return False
        else:
            if cv.pt_in_poly(x, y, p["poly"]) or cv.pt_poly_dist(x, y, p["poly"]) < need: return False
    for u, v in ctx.vias.items():
        if v["net"] == net or not (v["lay"] & span): continue
        need = max(VIA_R + v["r"] + cv._req(net, v["net"]),   # 铜-铜
                   HOLE_R + 0.25 + v["r"],                    # 本孔-它铜
                   VIA_R + 0.25 + v["hole"],                  # 本铜-它孔
                   HOLE_R + 0.25 + v["hole"])                 # 孔-孔
        if math.hypot(x - v["x"], y - v["y"]) < need: return False
    for u, p in ctx.pads.items():                   # PTH 盘：同心孔（本孔-它铜 / 本铜-它孔）
        if p["net"] == net or p["hole"] <= 0 or not (p["lay"] & span): continue
        if math.hypot(x - p["x"], y - p["y"]) < max(p["hole"] + 0.25 + VIA_R,
                                                    VIA_R + 0.25 + p["hole"]): return False
    for (hx, hy, hr, hnet, hlay) in ctx.holes:      # 孔-孔 0.25（无同网豁免）
        if math.hypot(x - hx, y - hy) < HOLE_R + 0.25 + hr: return False
    return True


def _via_why(ctx, net, x, y, span):
    for e in ctx.edge:
        if cv.pt_seg_dist(x, y, *e) < 0.3 + VIA_R: return "edge"
    for poly in ctx.keep_v:
        if cv.pt_in_poly(x, y, poly): return "keepv"
    for t in ctx.tracks:
        if t["net"] == net or t["layer"] not in span: continue
        need = max(VIA_R + cv._req(net, t["net"]), HOLE_R + 0.25 + t["hw"])
        if cv.pt_seg_dist(x, y, t["x1"], t["y1"], t["x2"], t["y2"]) - t["hw"] < need:
            return "trk:%s@%.2f,%.2f(d=%.3f/%.3f)" % (t["net"], t["x1"], t["y1"],
                        cv.pt_seg_dist(x, y, t["x1"], t["y1"], t["x2"], t["y2"]) - t["hw"], need)
    for p in ctx.pads.values():
        if p["net"] == net or not (p["lay"] & span): continue
        need = max(VIA_R + cv._req(net, p["net"]), HOLE_R + 0.25)
        if p["circ"]:
            d = math.hypot(x - p["x"], y - p["y"]) - min(p["w"], p["h"]) / 2
        else:
            d = 0.0 if cv.pt_in_poly(x, y, p["poly"]) else cv.pt_poly_dist(x, y, p["poly"])
        if d < need: return "pad:%s@%.2f,%.2f(d=%.3f/%.3f)" % (p["net"], p["x"], p["y"], d, need)
    for u, v in ctx.vias.items():
        if v["net"] == net or not (v["lay"] & span): continue
        need = max(VIA_R + v["r"] + cv._req(net, v["net"]), HOLE_R + 0.25 + v["r"],
                   VIA_R + 0.25 + v["hole"], HOLE_R + 0.25 + v["hole"])
        if math.hypot(x - v["x"], y - v["y"]) < need:
            return "via:%s@%.2f,%.2f(d=%.3f/%.3f)" % (v["net"], v["x"], v["y"], math.hypot(x - v["x"], y - v["y"]), need)
    for (hx, hy, hr, hnet, hlay) in ctx.holes:
        if math.hypot(x - hx, y - hy) < HOLE_R + 0.25 + hr:
            return "hole:%s@%.2f,%.2f(d=%.3f/%.3f)" % (hnet, hx, hy, math.hypot(x - hx, y - hy), HOLE_R + 0.25 + hr)
    return "?"


def node_in_island(ctx, find, comp, net, layer, x, y, tol=0.06):
    for u, p in ctx.pads.items():
        if p["net"] != net or layer not in p["lay"]: continue
        if comp is not None and find("p:" + u) != comp: continue
        if p["circ"]:
            if math.hypot(x - p["x"], y - p["y"]) <= min(p["w"], p["h"]) / 2 + tol: return True
        else:
            if cv.pt_in_poly(x, y, p["poly"]) or cv.pt_poly_dist(x, y, p["poly"]) <= tol: return True
    for t in ctx.tracks:
        if t["net"] != net or t["layer"] != layer: continue
        if comp is not None and find("t:" + t["uuid"]) != comp: continue
        if cv.pt_seg_dist(x, y, t["x1"], t["y1"], t["x2"], t["y2"]) <= t["hw"] + tol: return True
    for u, v in ctx.vias.items():
        if v["net"] != net or layer not in v["lay"]: continue
        if comp is not None and find("v:" + u) != comp: continue
        if math.hypot(x - v["x"], y - v["y"]) <= v["r"] + tol: return True
    return False


# ─────────────────────── 栅格（剪枝） ───────────────────────
# **C35 环路内框界**（#K2-378 §三.1）：把作业域**作为搜索约束**传入 —— 域外格一律不可选。
# 事后恢复框外铜已被实测否决（R1020：得 C6=0 但坏连通 C1 14->17 · C2 249->1237）；界必须下在**搜索环路里**。
WALL_RECT = None          # (x0, y0, x1, y1) mm；None = 不设界
RIPUP = 0                 # #K2-456 sec.2.5: pass-2 rounds (0 = off; the chain sets 1). Deterministic and bounded.
# #K2-452 sec.2.4 item 2 —— **软引导（偏好/代价）**：`GUIDE = {"rects":[(x0,y0,x1,y1),...], "penalty":f}`。
#   引导矩形**不是**边界（绝不改 `bad`）：只把**引导之外**的每一步代价乘以 `(1+penalty)` ⇒ 迷宫**偏好**走引导，
#   **但永远可以离开**（⇒ 引导**不可能**造成「构造性无解」—— 这正是 `R1420` 把 0.40mm 带当**硬域**踩到的坑：
#   `C1 2→47`，`no-path-coarse(exhausted-1)=47`）。`None` ⇒ 无引导 ⇒ 既有调用**行为不变**。
GUIDE = None
# #K2-458 sec.2.5 teaching item 2 —— **逐格拥塞代价（present 部分）**：`AVOID = {"rects":[...], "penalty":f}`；
#   落在这些矩形内的**格**每步 ×(1+penalty)（与 `GUIDE` 反向：GUIDE 奖励引导内、AVOID 惩罚已拥塞区）。
#   `None` ⇒ 无代价（既有调用**行为不变**）。确定性（格掩码由矩形集合唯一确定）。
AVOID = None
# #K2-465 sec.2.4 -- HARD KEEPOUT: `KEEPOUT = {net: [(layer_id, (x0,y0,x1,y1)), ...]}`.
# Those cells are UNUSABLE (bad=1) for that net on that layer -> the A* may not claim them. A HARD rule,
# NOT a cost and NOT an ordering preference. None => no keepout (existing callers unchanged).
KEEPOUT = None


class Grid:
    def __init__(self, ctx, net, step, x0, y0, x1, y1, margin=0.0):
        self.step = step; self.x0, self.y0 = x0, y0; self.margin = margin
        self.nx = int(math.floor((x1 - x0) / step)) + 1
        self.ny = int(math.floor((y1 - y0) / step)) + 1
        self.bad = {L: bytearray(self.nx * self.ny) for L in LAYERS}
        self.vb = {}
        import time as _t; _t0 = _t.time()
        self._mark(ctx, net)
        if WALL_RECT:                                     # 界内可走；界外（含边界外一格）一律封死
            wx0, wy0, wx1, wy1 = WALL_RECT
            for L in LAYERS:
                bb2 = self.bad[L]
                for i in range(self.nx):
                    px = self.x0 + i * self.step
                    out_x = (px < wx0 - 1e-9) or (px > wx1 + 1e-9)
                    for j in range(self.ny):
                        if out_x or (self.y0 + j * self.step < wy0 - 1e-9) or (self.y0 + j * self.step > wy1 + 1e-9):
                            bb2[i * self.ny + j] = 1
        # #K2-452 sec.2.4 item 2：软引导**格掩码**（层无关；只影响**代价**，不堵任何格）。
        # #K2-465: HARD keepout cells (only for the named net / named layer)
        for (_ly, (_kx0, _ky0, _kx1, _ky1)) in (KEEPOUT or {}).get(net, []):
            if _ly not in LAYERS:
                continue
            _ki0 = max(0, int(math.floor((_kx0 - x0) / step)))
            _ki1 = min(self.nx - 1, int(math.ceil((_kx1 - x0) / step)))
            _kj0 = max(0, int(math.floor((_ky0 - y0) / step)))
            _kj1 = min(self.ny - 1, int(math.ceil((_ky1 - y0) / step)))
            _bb = self.bad[_ly]
            for _ki in range(_ki0, _ki1 + 1):
                for _kj in range(_kj0, _kj1 + 1):
                    _bb[_ki * self.ny + _kj] = 1
        self.gflag = None
        self.gpen = 0.0
        if GUIDE:
            self.gpen = float(GUIDE.get("penalty") or 0.0)
            gf = bytearray(self.nx * self.ny)
            for (_gx0, _gy0, _gx1, _gy1) in (GUIDE.get("rects") or []):
                _i0 = max(0, int(math.floor((_gx0 - self.x0) / self.step)))
                _i1 = min(self.nx - 1, int(math.ceil((_gx1 - self.x0) / self.step)))
                _j0 = max(0, int(math.floor((_gy0 - self.y0) / self.step)))
                _j1 = min(self.ny - 1, int(math.ceil((_gy1 - self.y0) / self.step)))
                for _i in range(_i0, _i1 + 1):
                    for _j in range(_j0, _j1 + 1):
                        gf[_i * self.ny + _j] = 1
            self.gflag = gf
        # #K2-458：逐格拥塞代价掩码（惩罚区）
        self.aflag = None
        self.apen = 0.0
        if AVOID:
            self.apen = float(AVOID.get("penalty") or 0.0)
            af = bytearray(self.nx * self.ny)
            for (_ax0, _ay0, _ax1, _ay1) in (AVOID.get("rects") or []):
                _ai0 = max(0, int(math.floor((_ax0 - self.x0) / self.step)))
                _ai1 = min(self.nx - 1, int(math.ceil((_ax1 - self.x0) / self.step)))
                _aj0 = max(0, int(math.floor((_ay0 - self.y0) / self.step)))
                _aj1 = min(self.ny - 1, int(math.ceil((_ay1 - self.y0) / self.step)))
                for _ai in range(_ai0, _ai1 + 1):
                    for _aj in range(_aj0, _aj1 + 1):
                        af[_ai * self.ny + _aj] = 1
            self.aflag = af
        if os.environ.get("K2MR_DBG"):
            sys.stderr.write("[grid] step=%.2f %dx%d cells=%d mark=%.1fs\n" %
                             (step, self.nx, self.ny, self.nx * self.ny, _t.time() - _t0))

    def cell(self, x, y):
        i = int(round((x - self.x0) / self.step)); j = int(round((y - self.y0) / self.step))
        return i, j

    def pt(self, i, j):
        return self.x0 + i * self.step, self.y0 + j * self.step

    def vbad(self, ctx, net, span):
        """该 span 类过孔**非法**格（剪枝用；放行闸仍为 via_exact）。"""
        if span in self.vb: return self.vb[span]
        bad = bytearray(self.nx * self.ny)
        step, x0, y0, nx, ny = self.step, self.x0, self.y0, self.nx, self.ny

        def cpt(cx, cy, rad):
            i0 = max(0, int(math.floor((cx - rad - x0) / step)))
            i1 = min(nx - 1, int(math.ceil((cx + rad - x0) / step)))
            j0 = max(0, int(math.floor((cy - rad - y0) / step)))
            j1 = min(ny - 1, int(math.ceil((cy + rad - y0) / step)))
            for i in range(i0, i1 + 1):
                px = x0 + i * step
                for j in range(j0, j1 + 1):
                    py = y0 + j * step
                    if (px - cx) ** 2 + (py - cy) ** 2 <= rad * rad: bad[i * ny + j] = 1

        def cseg(ax, ay, bx, by, rad):
            i0 = max(0, int(math.floor((min(ax, bx) - rad - x0) / step)))
            i1 = min(nx - 1, int(math.ceil((max(ax, bx) + rad - x0) / step)))
            j0 = max(0, int(math.floor((min(ay, by) - rad - y0) / step)))
            j1 = min(ny - 1, int(math.ceil((max(ay, by) + rad - y0) / step)))
            for i in range(i0, i1 + 1):
                px = x0 + i * step
                for j in range(j0, j1 + 1):
                    py = y0 + j * step
                    if cv.pt_seg_dist(px, py, ax, ay, bx, by) <= rad: bad[i * ny + j] = 1

        def fill(poly):
            xa = [q[0] for q in poly]; ya = [q[1] for q in poly]
            i0 = max(0, int(math.floor((min(xa) - x0) / step)))
            i1 = min(nx - 1, int(math.ceil((max(xa) - x0) / step)))
            j0 = max(0, int(math.floor((min(ya) - y0) / step)))
            j1 = min(ny - 1, int(math.ceil((max(ya) - y0) / step)))
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    if cv.pt_in_poly(x0 + i * step, y0 + j * step, poly): bad[i * ny + j] = 1

        for e in ctx.edge: cseg(e[0], e[1], e[2], e[3], 0.3 + VIA_R + self.margin)
        for poly in ctx.keep_v: fill(poly)
        for t in ctx.tracks:
            if t["layer"] not in span or t["net"] == net: continue
            cseg(t["x1"], t["y1"], t["x2"], t["y2"],
                 max(VIA_R + cv._req(net, t["net"]), HOLE_R + 0.25 + t["hw"]) + t["hw"] + self.margin)
        for p in ctx.pads.values():
            if not (p["lay"] & span) or p["net"] == net: continue
            rad = max(VIA_R + cv._req(net, p["net"]), HOLE_R + 0.25) + self.margin
            if p["circ"]:
                cpt(p["x"], p["y"], min(p["w"], p["h"]) / 2 + rad)
            else:
                n = len(p["poly"])
                for k in range(n):
                    q1, q2 = p["poly"][k], p["poly"][(k + 1) % n]
                    cseg(q1[0], q1[1], q2[0], q2[1], rad)
                fill(p["poly"])
        for u, v in ctx.vias.items():
            if not (v["lay"] & span) or v["net"] == net: continue
            cpt(v["x"], v["y"], max(VIA_R + v["r"] + cv._req(net, v["net"]), HOLE_R + 0.25 + v["r"],
                                    VIA_R + 0.25 + v["hole"], HOLE_R + 0.25 + v["hole"]) + self.margin)
        for u, p in ctx.pads.items():
            if p["net"] == net or p["hole"] <= 0 or not (p["lay"] & span): continue
            cpt(p["x"], p["y"], max(p["hole"] + 0.25 + VIA_R, VIA_R + 0.25 + p["hole"]) + self.margin)
        for (hx, hy, hr, hnet, hlay) in ctx.holes:
            # inc105(L2)：**孔-孔无同网豁免**（与板内 DRC 一致）⇒ 同网孔位亦须剪枝，
            #   否则 astar 会把换层点选在既有同网孔上（holes_co_located / 0.050 vs 0.450）
            cpt(hx, hy, hr + 0.25 + HOLE_R + self.margin)
        self.vb[span] = bad
        return bad

    def inside(self, i, j):
        return 0 <= i < self.nx and 0 <= j < self.ny

    def _mark(self, ctx, net):
        def cseg(layer, ax, ay, bx, by, rad):
            bad = self.bad[layer]
            i0 = max(0, int(math.floor((min(ax, bx) - rad - self.x0) / self.step)))
            i1 = min(self.nx - 1, int(math.ceil((max(ax, bx) + rad - self.x0) / self.step)))
            j0 = max(0, int(math.floor((min(ay, by) - rad - self.y0) / self.step)))
            j1 = min(self.ny - 1, int(math.ceil((max(ay, by) + rad - self.y0) / self.step)))
            for i in range(i0, i1 + 1):
                px = self.x0 + i * self.step
                for j in range(j0, j1 + 1):
                    py = self.y0 + j * self.step
                    if cv.pt_seg_dist(px, py, ax, ay, bx, by) <= rad:
                        bad[i * self.ny + j] = 1

        def cpt(layer, cx, cy, rad):
            bad = self.bad[layer]
            i0 = max(0, int(math.floor((cx - rad - self.x0) / self.step)))
            i1 = min(self.nx - 1, int(math.ceil((cx + rad - self.x0) / self.step)))
            j0 = max(0, int(math.floor((cy - rad - self.y0) / self.step)))
            j1 = min(self.ny - 1, int(math.ceil((cy + rad - self.y0) / self.step)))
            for i in range(i0, i1 + 1):
                px = self.x0 + i * self.step
                for j in range(j0, j1 + 1):
                    py = self.y0 + j * self.step
                    if (px - cx) ** 2 + (py - cy) ** 2 <= rad * rad:
                        bad[i * self.ny + j] = 1

        for L in LAYERS:
            for t in ctx.tracks:
                if t["layer"] != L or t["net"] == net: continue
                cseg(L, t["x1"], t["y1"], t["x2"], t["y2"], t["hw"] + HW + cv._req(net, t["net"]) + self.margin)
            for p in ctx.pads.values():
                if L not in p["lay"] or p["net"] == net: continue
                r = HW + cv._req(net, p["net"]) + self.margin
                if p["circ"]:
                    cpt(L, p["x"], p["y"], min(p["w"], p["h"]) / 2 + r)
                else:
                    n = len(p["poly"])
                    for k in range(n):
                        q1, q2 = p["poly"][k], p["poly"][(k + 1) % n]
                        cseg(L, q1[0], q1[1], q2[0], q2[1], r)
                    xa = [q[0] for q in p["poly"]]; ya = [q[1] for q in p["poly"]]
                    i0 = max(0, int(math.floor((min(xa) - self.x0) / self.step)))
                    i1 = min(self.nx - 1, int(math.ceil((max(xa) - self.x0) / self.step)))
                    j0 = max(0, int(math.floor((min(ya) - self.y0) / self.step)))
                    j1 = min(self.ny - 1, int(math.ceil((max(ya) - self.y0) / self.step)))
                    for i in range(i0, i1 + 1):
                        for j in range(j0, j1 + 1):
                            if cv.pt_in_poly(self.x0 + i * self.step, self.y0 + j * self.step, p["poly"]):
                                self.bad[L][i * self.ny + j] = 1
            for u, v in ctx.vias.items():
                if L not in v["lay"] or v["net"] == net: continue
                cpt(L, v["x"], v["y"], v["r"] + HW + cv._req(net, v["net"]) + self.margin)
            for _h in ctx.holes:                              # #K2-483: the in-register gauge interface fix.
                # f3.Ctx yields 4-tuples (x, y, r, net) while _mark expected 5 (with a layer set) => ValueError.
                # A hole with no layer data is conservatively treated as blocking EVERY copper layer.
                if len(_h) >= 5:
                    _hx, _hy, _hr, _hnet, _hlay = _h[0], _h[1], _h[2], _h[3], _h[4]
                else:
                    _hx, _hy, _hr, _hnet, _hlay = _h[0], _h[1], _h[2], _h[3], LAYERS
                if _hnet == net or L not in _hlay: continue
                cpt(L, _hx, _hy, _hr + 0.25 + HW + self.margin)
            for e in ctx.edge:
                cseg(L, e[0], e[1], e[2], e[3], HW + 0.3 + self.margin)
            for poly in ctx.keep_t:
                xa = [q[0] for q in poly]; ya = [q[1] for q in poly]
                i0 = max(0, int(math.floor((min(xa) - self.x0) / self.step)))
                i1 = min(self.nx - 1, int(math.ceil((max(xa) - self.x0) / self.step)))
                j0 = max(0, int(math.floor((min(ya) - self.y0) / self.step)))
                j1 = min(self.ny - 1, int(math.ceil((max(ya) - self.y0) / self.step)))
                for i in range(i0, i1 + 1):
                    for j in range(j0, j1 + 1):
                        if cv.pt_in_poly(self.x0 + i * self.step, self.y0 + j * self.step, poly):
                            self.bad[L][i * self.ny + j] = 1
            for poly in ctx.keep_v:
                xa = [q[0] for q in poly]; ya = [q[1] for q in poly]
                i0 = max(0, int(math.floor((min(xa) - self.x0) / self.step)))
                i1 = min(self.nx - 1, int(math.ceil((max(xa) - self.x0) / self.step)))
                j0 = max(0, int(math.floor((min(ya) - self.y0) / self.step)))
                j1 = min(self.ny - 1, int(math.ceil((max(ya) - self.y0) / self.step)))
                for i in range(i0, i1 + 1):
                    for j in range(j0, j1 + 1):
                        if cv.pt_in_poly(self.x0 + i * self.step, self.y0 + j * self.step, poly):
                            self.bad[L][i * self.ny + j] = 1


# ─────────────────────── 多层 A* ───────────────────────
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


CAP = 3_000_000


def astar(grid, ctx, net, s, g, sl, gl, fine=False):
    """s,g = (i,j)。返回 ([(layer,i,j,viaflag), ...], reason)。"""
    import heapq
    step = grid.step; ny = grid.ny; nc = grid.nx * ny
    LI = {L: k for k, L in enumerate(LAYERS)}
    N = nc * len(LAYERS)
    inf = float("inf")
    dist = array("d", [inf]) * N
    came = array("i", [-1]) * N
    viaf = bytearray(N)
    def nid(L, i, j): return LI[L] * nc + i * ny + j
    W = 1.35
    sx, sy = s; gx, gy = g
    def h(i, j): return math.hypot(i - gx, j - gy) * step * W
    sn = nid(sl, sx, sy)
    if grid.bad[sl][sx * ny + sy]: return None, "start-blocked"
    dist[sn] = 0.0
    q = [(h(sx, sy), 0.0, sn)]
    seen = 0
    import time as _t; _t0 = _t.time()
    while q:
        f, d, n = heapq.heappop(q)
        if d > dist[n] + 1e-9: continue
        seen += 1
        k = n // nc; r = n % nc; i, j = r // ny, r % ny
        L = LAYERS[k]
        if L == gl and i == gx and j == gy:
            path = []
            c = n
            while c != -1:
                kk = c // nc; rr = c % nc; ii, jj = rr // ny, rr % ny
                path.append((LAYERS[kk], ii, jj, bool(viaf[c]))); c = came[c]
            path.reverse()
            if os.environ.get("K2MR_DBG"): sys.stderr.write("[astar] ok exp=%d %.1fs\n" % (seen, _t.time() - _t0))
            return path, "ok"
        px, py = grid.pt(i, j)
        for di, dj in DIRS:
            ni, nj = i + di, j + dj
            if not grid.inside(ni, nj): continue
            if grid.bad[L][ni * ny + nj]: continue
            if di and dj and (grid.bad[L][i * ny + nj] or grid.bad[L][ni * ny + j]): continue
            _gc = 1.0 if (grid.gflag is None or grid.gflag[ni * ny + nj]) else (1.0 + grid.gpen)
            if grid.aflag is not None and grid.aflag[ni * ny + nj]:
                _gc = _gc * (1.0 + grid.apen)                 # #K2-458: present-cost on congested cells
            nd = d + step * (math.sqrt(2) if di and dj else 1.0) * _gc
            nn = nid(L, ni, nj)
            if nd < dist[nn] - 1e-9:
                dist[nn] = nd; came[nn] = n
                heapq.heappush(q, (nd + h(ni, nj), nd, nn))
        if viaf[n]:
            continue          # 禁止同格连续换层（否则同点堆叠孔 ⇒ holes_co_located）
        for (a, b) in TRANS:
            if L == a: oL = b
            elif L == b: oL = a
            else: continue
            if grid.bad[oL][i * ny + j]: continue
            span = SPAN_OF[frozenset((a, b))]
            if grid.vbad(ctx, net, span)[i * ny + j]: continue
            nn = nid(oL, i, j)
            nd = d + VIA_COST
            if nd < dist[nn] - 1e-9:
                dist[nn] = nd; came[nn] = n; viaf[nn] = 1
                heapq.heappush(q, (nd + h(i, j), nd, nn))
        if seen > CAP:
            if os.environ.get("K2MR_DBG"): sys.stderr.write("[astar] cap %d %.1fs\n" % (seen, _t.time() - _t0))
            return None, "cap-%d" % seen
    if os.environ.get("K2MR_DBG"): sys.stderr.write("[astar] exhaust %d %.1fs\n" % (seen, _t.time() - _t0))
    return None, "exhausted-%d" % seen


def simplify(pts):
    out = [pts[0]]
    for p in pts[1:]:
        if math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) < 1e-9: continue
        out.append(p)
    if len(out) <= 2: return out
    res = [out[0]]
    for k in range(1, len(out) - 1):
        a, b, c = res[-1], out[k], out[k + 1]
        d1 = (b[0] - a[0], b[1] - a[1]); d2 = (c[0] - b[0], c[1] - b[1])
        if abs(d1[0] * d2[1] - d1[1] * d2[0]) < 1e-9 and d1[0] * d2[0] + d1[1] * d2[1] > 0: continue
        res.append(b)
    res.append(out[-1])
    return res


def _pt_seg_dist(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 <= 0 else max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / L2))
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))


def _seg_seg_dist(ax, ay, bx, by, cx, cy, dx, dy):
    """Exact segment-segment distance (0.0 when they cross)."""
    def _cr(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    d1 = _cr((ax, ay), (bx, by), (cx, cy)); d2 = _cr((ax, ay), (bx, by), (dx, dy))
    d3 = _cr((cx, cy), (dx, dy), (ax, ay)); d4 = _cr((cx, cy), (dx, dy), (bx, by))
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(_pt_seg_dist(cx, cy, ax, ay, bx, by), _pt_seg_dist(dx, dy, ax, ay, bx, by),
               _pt_seg_dist(ax, ay, cx, cy, dx, dy), _pt_seg_dist(bx, by, cx, cy, dx, dy))


def dangling_ends(items, tol=0.02):
    """#K2-490/#K2-493 ENGINE CAPABILITY (pure, deterministic): find copper ends that connect to NOTHING.

    `items` = [(kind, layer, x1, y1, x2, y2, halfwidth, net), ...]; a via is a zero-length segment. A track end is
    "dangling" when no OTHER item of the SAME net touches it within `tol` (an endpoint-to-endpoint touch) and no
    same-net PAD item covers it - i.e. the end is a free end. Returns a deterministically sorted list of
    {"net","layer","at"} so the engine can NAME (and then prune or connect) floating copper instead of leaving it
    to a human. This is the detector half of the rule 'a short end must not dangle - connect it or do not lay it'.
    """
    # #K2-494: BOUNDED via a grid-bucket index. Each item is registered in every bucket its bbox EXPANDED by
    # (halfwidth + tol) overlaps, so an endpoint's test only has to look at the ONE bucket it sits in: any item
    # that could touch it is guaranteed to be registered there. O(n) build + O(1) lookup per end - no while-loop,
    # fixed bucket size, so the owner's "no CPU spike" rule holds on a 6000-item board.
    _B = 1.0
    _idx = {}

    def _bk(x, y):
        return (int(math.floor(x / _B)), int(math.floor(y / _B)))

    for _i, _it in enumerate(items):
        _k, _l, _x1, _y1, _x2, _y2, _hw, _net = _it
        _pad = _hw + tol
        _i0, _j0 = _bk(min(_x1, _x2) - _pad, min(_y1, _y2) - _pad)
        _i1, _j1 = _bk(max(_x1, _x2) + _pad, max(_y1, _y2) + _pad)
        for _a in range(_i0, _i1 + 1):
            for _b in range(_j0, _j1 + 1):
                _idx.setdefault((_net, _l, _a, _b), []).append(_i)
    out = []
    for i in range(len(items)):
        ka, la, ax1, ay1, ax2, ay2, a_hw, a_net = items[i]
        for (px, py) in ((ax1, ay1), (ax2, ay2)):
            hit = False
            bx, by = _bk(px, py)
            for j in _idx.get((a_net, la, bx, by), ()):
                if j == i:
                    continue
                kb, lb, bx1, by1, bx2, by2, b_hw, b_net = items[j]
                if kb == "PAD":
                    if _pt_seg_dist(px, py, bx1, by1, bx2, by2) <= b_hw + tol:
                        hit = True; break
                elif min(math.hypot(px - bx1, py - by1), math.hypot(px - bx2, py - by2)) <= tol:
                    hit = True; break
            if not hit:
                out.append({"net": a_net, "layer": la, "at": [round(px, 4), round(py, 4)]})
    out.sort(key=lambda r: (str(r["net"]), r["layer"], r["at"][0], r["at"][1]))
    return out


def dangling_items(items, tol=0.02):
    """#K2-494 ENGINE CAPABILITY (pure, deterministic): the PRUNE PLAN.

    Given the same item list as dangling_ends, return the INDICES of every item that OWNS at least one dangling end
    (sorted, deterministic). That is the removable set the registered delete route (netplan -> ripup) consumes, and
    the "connect" alternative is the same set with a stitch target. A fully connected item is never listed.
    """
    bad = dangling_ends(items, tol)
    keys = {(round(d["at"][0], 4), round(d["at"][1], 4), d["layer"], d["net"]) for d in bad}
    out = []
    for i, it in enumerate(items):
        k, l, x1, y1, x2, y2, hw, net = it
        if (round(x1, 4), round(y1, 4), l, net) in keys or (round(x2, 4), round(y2, 4), l, net) in keys:
            out.append(i)
    return out


def floating_items(items, tol=0.02):
    """#K2-501 (narrowing the prune after the R1664 rerun): the CONSERVATIVE prune plan.

    R1664's rerun pruned 40 items and broke 4 connections (C1 0 -> 4): dangling_items lists any item owning ONE
    dangling end, and an escape stub is exactly that (its far end waits to be connected). This function lists only
    items whose BOTH ends dangle - a fully floating island that touches neither another same-net item nor a pad.
    One-ended stubs are PRESERVED (they are escape stubs / pending connections). Pads are never listed.
    """
    bad = dangling_ends(items, tol)
    keys = {(round(d["at"][0], 4), round(d["at"][1], 4), d["layer"], d["net"]) for d in bad}
    out = []
    for i, it in enumerate(items):
        k, l, x1, y1, x2, y2, hw, net = it
        if k == "PAD":
            continue
        end1 = (round(x1, 4), round(y1, 4), l, net) in keys
        end2 = (round(x2, 4), round(y2, 4), l, net) in keys
        if end1 and end2:
            out.append(i)
    return out


def dead_stages(chain):
    """#K2-501 ENGINE CAPABILITY (pure, deterministic): the "a dead segment kills the run" gate.

    Given a chain record list, return the NAMED list of segments that died - any record carrying an "err" key.
    A run whose chain contains a dead segment must never be graded as if it were whole; this is the one
    authoritative test the pipeline and the judge consult, so a swallowed stage error becomes a named FAILURE
    (the closing asset for the night's "stage errors swallowed" defect family, live-reproduced at R1654).
    """
    out = []
    for i, r in enumerate(chain or []):
        if not isinstance(r, dict):
            continue
        if r.get("err"):
            out.append({"at": i, "stage": r.get("stage"), "err": r.get("err")})
    out.sort(key=lambda x: (x["at"], str(x.get("stage"))))
    return out


def board_items(board_path):
    """#K2-500 ENGINE CAPABILITY (the function the chain's audit/prune stage calls): assemble the copper item list
    from a real board - tracks as centre-line+halfwidth, vias as zero-length segments of their radius on EVERY layer
    of their span, pads as true-shape capsules on each layer they are on. Deterministic. R1652's chain wiring
    referenced this name but the function had only ever existed in reverted attempts (R1634..R1644), so the audit
    stage died with AttributeError and the prune never ran (named in R1654). This lands it for real.
    """
    b = pcbnew.LoadBoard(board_path)
    N2I = {LNAME[L]: L for L in LAYERS}
    items = []
    for t in b.GetTracks():
        s, e = t.GetStart(), t.GetEnd()
        if t.GetClass() == "PCB_VIA":
            seq = list(t.GetLayerSet().Seq())
            for L in seq:
                items.append(("VIA", L, pcbnew.ToMM(s.x), pcbnew.ToMM(s.y), pcbnew.ToMM(s.x), pcbnew.ToMM(s.y),
                              pcbnew.ToMM(t.GetWidth(seq[0])) / 2.0, t.GetNetname()))
        else:
            L = N2I.get(b.GetLayerName(t.GetLayer()))
            if L is None:
                continue
            items.append(("TRK", L, pcbnew.ToMM(s.x), pcbnew.ToMM(s.y), pcbnew.ToMM(e.x), pcbnew.ToMM(e.y),
                          pcbnew.ToMM(t.GetWidth()) / 2.0, t.GetNetname()))
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            pos = pd.GetPosition(); x, y = pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)
            sz = pd.GetSize(); sx, sy = pcbnew.ToMM(sz.x), pcbnew.ToMM(sz.y)
            if sy >= sx:
                a, c, hw = (x, y - (sy - sx) / 2.0), (x, y + (sy - sx) / 2.0), sx / 2.0
            else:
                a, c, hw = (x - (sx - sy) / 2.0, y), (x + (sx - sy) / 2.0, y), sy / 2.0
            lys = ([N2I["F.Cu"], N2I["B.Cu"]] if pd.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
                   else ([N2I["F.Cu"]] if pd.IsOnLayer(pcbnew.F_Cu) else [N2I["B.Cu"]]))
            for L in lys:
                items.append(("PAD", L, a[0], a[1], c[0], c[1], hw, pd.GetNetname() or ""))
    return items


def board_dangling(board_path, tol=0.02):
    """#K2-494 ENGINE CAPABILITY: build the item list from a real board and return dangling_ends(...).

    The engine - not an agent - assembles every copper item (tracks as centre-line+halfwidth, vias as zero-length
    segments with their radius on EVERY layer of their span, pads as true-shape capsules on each layer they are on)
    and then names its own floating copper with the bounded detector. Deterministic; bounded (R1624).
    """
    b = pcbnew.LoadBoard(board_path)
    N2I = {LNAME[L]: L for L in LAYERS}
    items = []
    for t in b.GetTracks():
        s, e = t.GetStart(), t.GetEnd()
        if t.GetClass() == "PCB_VIA":
            seq = list(t.GetLayerSet().Seq())
            for L in seq:
                items.append(("VIA", L, pcbnew.ToMM(s.x), pcbnew.ToMM(s.y), pcbnew.ToMM(s.x), pcbnew.ToMM(s.y),
                              pcbnew.ToMM(t.GetWidth(seq[0])) / 2.0, t.GetNetname()))
        else:
            L = N2I.get(b.GetLayerName(t.GetLayer()))
            if L is None:
                continue
            items.append(("TRK", L, pcbnew.ToMM(s.x), pcbnew.ToMM(s.y), pcbnew.ToMM(e.x), pcbnew.ToMM(e.y),
                          pcbnew.ToMM(t.GetWidth()) / 2.0, t.GetNetname()))
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            pos = pd.GetPosition(); x, y = pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)
            sz = pd.GetSize(); sx, sy = pcbnew.ToMM(sz.x), pcbnew.ToMM(sz.y)
            if sy >= sx:
                a, c, hw = (x, y - (sy - sx) / 2.0), (x, y + (sy - sx) / 2.0), sx / 2.0
            else:
                a, c, hw = (x - (sx - sy) / 2.0, y), (x + (sx - sy) / 2.0, y), sy / 2.0
            lys = ([N2I["F.Cu"], N2I["B.Cu"]] if pd.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
                   else ([N2I["F.Cu"]] if pd.IsOnLayer(pcbnew.F_Cu) else [N2I["B.Cu"]]))
            for L in lys:
                items.append(("PAD", L, a[0], a[1], c[0], c[1], hw, pd.GetNetname() or ""))
    return dangling_ends(items, tol)


def gap_violations(items, floor):
    """#K2-490/#K2-491 ENGINE CAPABILITY (pure, deterministic): the CLEARANCE AUDIT.

    `items` = [(kind, layer, x1, y1, x2, y2, halfwidth), ...]; a via is a zero-length segment whose halfwidth is its
    radius. Returns the list of violations "edge_gap < floor" between DIFFERENT nets on the SAME layer, each as
    {"gap","a","b"} with the edge-to-edge distance (the DRC's own measure), sorted deterministically. This makes the
    engine able to NAME a too-close pair itself - the object positions in a DRC report are NOT the closest points
    (R1614), so the closest pair must be computed from the geometry.
    """
    out = []
    for i in range(len(items)):
        ka, la, ax1, ay1, ax2, ay2, a_hw, a_net = (items[i][0], items[i][1], items[i][2], items[i][3],
                                                   items[i][4], items[i][5], items[i][6], items[i][7])
        for j in range(i + 1, len(items)):
            kb, lb, bx1, by1, bx2, by2, b_hw, b_net = (items[j][0], items[j][1], items[j][2], items[j][3],
                                                       items[j][4], items[j][5], items[j][6], items[j][7])
            if la != lb or a_net == b_net:
                continue
            gap = _seg_seg_dist(ax1, ay1, ax2, ay2, bx1, by1, bx2, by2) - a_hw - b_hw
            if gap < floor:
                out.append({"gap": round(gap, 4), "a": [ka, la, a_net], "b": [kb, lb, b_net]})
    out.sort(key=lambda r: (r["gap"], str(r["a"]), str(r["b"])))
    return out


def retry_start(pb, lb, compb, cport):
    """#K2-486/#K2-490 ENGINE CAPABILITY (pure, deterministic): pick the START for a port-directed retry.
    The (out,in) substitution can replace the outside endpoint with the VERY port used as the goal, making
    start == goal so the attempt is skipped by construction (R1592 - this is why the I2C2_SCL edge was never
    rescued). Given the OTHER endpoint (pb, lb, compb) this returns it as the start, or None when even that
    endpoint is the goal port (nothing to try). Single authoritative implementation for the retry decision.
    """
    if compb != cport:
        return (pb, lb, compb)
    return None


def snap_node(grid, ctx, find, comp, net, layer, x, y, maxr=4):
    ci, cj = grid.cell(x, y)
    _dbg = os.environ.get("K2MR_DBG2")
    if _dbg:
        sys.stderr.write("[snap] %s layer=%s (%.3f,%.3f) cell=(%d,%d) maxr=%d margin=%.2f\n"
                         % (net, LNAME[layer], x, y, ci, cj, maxr, grid.margin))
        for r in range(maxr + 1):
            for di in range(-r, r + 1):
                for dj in range(-r, r + 1):
                    if max(abs(di), abs(dj)) != r: continue
                    i, j = ci + di, cj + dj
                    if not grid.inside(i, j): continue
                    px, py = grid.pt(i, j)
                    own = node_in_island(ctx, find, comp, net, layer, px, py)
                    blk = grid.bad[layer][i * grid.ny + j]
                    if own or r <= 1:
                        sys.stderr.write("   r=%d d=(%d,%d) xy=(%.3f,%.3f) own=%s bad=%d\n"
                                         % (r, di, dj, px, py, own, blk))
    for r in range(maxr + 1):
        cands = []
        for di in range(-r, r + 1):
            for dj in range(-r, r + 1):
                if max(abs(di), abs(dj)) != r: continue
                cands.append((di, dj))
        cands.sort()
        for di, dj in cands:
            i, j = ci + di, cj + dj
            if not grid.inside(i, j) or grid.bad[layer][i * grid.ny + j]: continue
            px, py = grid.pt(i, j)
            if node_in_island(ctx, find, comp, net, layer, px, py): return i, j
    # #K2-538 (order): the ANCHOR is the endpoint of this net's OWN laid copper (an escape leg / port stub end,
    # i.e. an extension of the net's island), so it is a LEGAL start whenever its own cell is free. `maxr` is a
    # SEARCH RADIUS, never a legality gate. This fallback only fires when the bounded ring search found nothing.
    if grid.bad[layer][ci * grid.ny + cj] == 0:
        return ci, cj
    return None


def solve_edge(ctx, find, compa, compb, net, la, pa, lb, pb, margin, coarse_step):
    last = "no-attempt"
    for m in MARGINS:
        sol, why = _try_margin(ctx, find, compa, compb, net, la, pa, lb, pb, margin, coarse_step, m)
        if sol is not None: return sol, "ok"
        last = why
    return None, last


def _try_margin(ctx, find, compa, compb, net, la, pa, lb, pb, margin, coarse_step, gm):
    x0 = min(pa[0], pb[0]) - margin; x1 = max(pa[0], pb[0]) + margin
    y0 = min(pa[1], pb[1]) - margin; y1 = max(pa[1], pb[1]) + margin
    bx0, by0, bx1, by1 = EDGE_IN
    x0, y0 = max(x0, bx0), max(y0, by0)
    x1, y1 = min(x1, bx1), min(y1, by1)
    if x1 - x0 < 1.0 or y1 - y0 < 1.0: return None, "window-empty"
    g1 = Grid(ctx, net, coarse_step, x0, y0, x1, y1, gm)
    s = snap_node(g1, ctx, find, compa, net, la, pa[0], pa[1])
    go = snap_node(g1, ctx, find, compb, net, lb, pb[0], pb[1])
    if s is None: return None, "no-free-start-node"
    if go is None: return None, "no-free-goal-node"
    p1, why1 = astar(g1, ctx, net, s, go, la, lb)
    if p1 is None:
        return None, "no-path-coarse(%s)" % why1
    pts = [(ctx_layer, g1.pt(i, j)) for (ctx_layer, i, j, v) in p1]
    xs = [p[1][0] for p in pts]; ys = [p[1][1] for p in pts]
    x0f, x1f = min(xs) - 0.7, max(xs) + 0.7
    y0f, y1f = min(ys) - 0.7, max(ys) + 0.7
    x0f, y0f = max(x0f, bx0), max(y0f, by0)
    x1f, y1f = min(x1f, bx1), min(y1f, by1)
    g2 = Grid(ctx, net, FINE_STEP, x0f, y0f, x1f, y1f, gm)
    s2 = snap_node(g2, ctx, find, compa, net, la, pa[0], pa[1], maxr=6)
    go2 = snap_node(g2, ctx, find, compb, net, lb, pb[0], pb[1], maxr=6)
    if s2 is None or go2 is None: return None, "no-free-node-fine"
    p2, why2 = astar(g2, ctx, net, s2, go2, la, lb, fine=True)
    if p2 is None: return None, "no-path-fine(%s)" % why2
    # 重组：连续同层 = 折线；层变化 = 过孔
    legs = []       # (layer, [(x,y)...])
    vias = []       # (x,y,span,l1,l2)
    cur = None; curL = None
    for (L, i, j, v) in p2:
        x, y = g2.pt(i, j)
        if curL is None:
            curL = L; cur = [(x, y)]
            continue
        if L == curL:
            cur.append((x, y))
        else:
            legs.append((curL, simplify(cur)))
            span = SPAN_OF[frozenset((curL, L))]
            vias.append((cur[-1][0], cur[-1][1], span, curL, L))
            curL = L; cur = [(x, y)]
    legs.append((curL, simplify(cur)))
    # inc103(L2)：与既有**同网**过孔同点且同跨度的「换层」无需新放孔
    # （链内 U1.6↔MCU_VDD 锚 边的路径末端换层恰落在既有锚孔 (30.475,54.5) 上；原式会加重复孔 ⇒ hole 碰撞 0.056/0.450）
    _kept = []
    for (x, y, span, l1, l2) in vias:
        dup = False
        for v in ctx.vias.values():
            if v["net"] != net: continue
            if math.hypot(x - v["x"], y - v["y"]) > 0.15: continue
            if l1 in v["lay"] and l2 in v["lay"]: dup = True; break
        if not dup: _kept.append((x, y, span, l1, l2))
    vias = _kept
    # 精确放行闸
    for (L, pl) in legs:
        for k in range(len(pl) - 1):
            (ax, ay), (bx, by) = pl[k], pl[k + 1]
            if math.hypot(bx - ax, by - ay) < 0.049:
                return None, "leg-too-short"
            if not _ok45(ax, ay, bx, by): return None, "leg-not-45"
            if not seg_exact(ctx, L, net, ax, ay, bx, by): return None, "seg-clearance"
    for (x, y, span, l1, l2) in vias:
        if not via_exact(ctx, net, x, y, span):
            return None, "via-clearance(%s)" % _via_why(ctx, net, x, y, span)
    # 本路由自身孔间（**同网**孔-孔/孔-铜无豁免；KiCad `holes_co_located` 亦为门禁）
    for i in range(len(vias)):
        for j in range(i + 1, len(vias)):
            x1, y1, s1 = vias[i][0], vias[i][1], vias[i][2]
            x2, y2, s2 = vias[j][0], vias[j][1], vias[j][2]
            if not (s1 & s2):          # z 向不重叠 ⇒ 不冲突
                continue
            if math.hypot(x1 - x2, y1 - y2) < HOLE_R + 0.25 + VIA_R:
                return None, "self-via-conflict"
    return dict(legs=legs, vias=vias), "ok"


def _ok45(x1, y1, x2, y2):
    dx, dy = abs(x2 - x1), abs(y2 - y1)
    return dx < 1e-6 or dy < 1e-6 or abs(dx - dy) < 1e-6


FINE_STEP = 0.10
MARGINS = (0.0, 0.03, 0.08, 0.15, 0.25)
# 本板确定性优先序（增量 16 裁定 · L2 走廊/布线自裁）：
# R35..R44 行的南向 F.Cu 缝**唯一**（x≈80.5..82.3，南墙 = PCIE_REFCLK1_P/N 长度匹配对、不可动）
# ⇒ strap 组（7 条）必须先分配走廊；其余边按 dist_asc 序。
PRIORITY_NETS = ("DS320_STRAP_A_ADDR0_15-8", "DS320_STRAP_A_ADDR0_7-0", "DS320_STRAP_A_ADDR1_7-0",
                 "DS320_STRAP_B_ADDR0_7-0", "DS320_STRAP_B_ADDR1_7-0", "DS320_STRAP_B_ADDR0_15-8",
                 "DS320_STRAP_MODE")
EDGE_IN = (0.0, 0.0, 0.0, 0.0)


def run(src, drc_path, out_path, ledger_path, margin, only_net, dry, order="dist_asc", order_list=None):
    global EDGE_IN, AVOID
    b = pcbnew.LoadBoard(src)
    ctx = f3.Ctx(b)
    holes = []
    for u, v in ctx.vias.items():
        holes.append((v["x"], v["y"], v["hole"], v["net"], frozenset(v["lay"])))
    for u, p in ctx.pads.items():
        if p["hole"] > 0:
            holes.append((p["x"], p["y"], p["hole"], p["net"], frozenset(p["lay"])))
    ctx.holes = holes
    bb = b.GetBoardEdgesBoundingBox()
    inset = 0.3 + HW + 0.4
    EDGE_IN = (pcbnew.ToMM(bb.GetLeft()) + inset, pcbnew.ToMM(bb.GetTop()) + inset,
               pcbnew.ToMM(bb.GetRight()) - inset, pcbnew.ToMM(bb.GetBottom()) - inset)
    m = f1.M(b)
    find = f1.islands(m)
    drc = json.load(open(drc_path, encoding="utf-8"))

    def netof(uu):
        if uu in ctx.pads: return ctx.pads[uu]["net"]
        if uu in ctx.vias: return ctx.vias[uu]["net"]
        for t in ctx.tracks:
            if t["uuid"] == uu: return t["net"]
        return None

    def layof(uu):
        if uu in ctx.pads:
            for L in LAYERS:
                if L in ctx.pads[uu]["lay"]: return L
            return F_CU
        if uu in ctx.vias:
            for L in LAYERS:
                if L in ctx.vias[uu]["lay"]: return L
            return F_CU
        for t in ctx.tracks:
            if t["uuid"] == uu:
                return t["layer"] if t["layer"] in LAYERS else F_CU
        return None

    # ── inc107(L2) 根因修复：DRC `unconnected_items` 的**代表项**不确定 ──────────────
    # 实证（kicad-cli 10.0.5；同板 `80c74d19` + 同 pro `419ac6ec`；fresh work-dir）：
    #   ① 两次连跑，`unconnected_items` 的**端点项**不同（同网同岛内任取：
    #      MCU_VDD 岛取 `via(30.475,54.5)` 或 `track(30.05,54.5)0.425`；
    #      P3V3_AUX 岛取 `R1.2(50.95,37)` 或同点 `track`）—— 项数/网集/规则全同；
    #   ② `setarch -R`（关 ASLR）与 `taskset -c 0`（绑单核）均**不能**消除
    #      ⇒ 非 ASLR、非线程调度；DRC 只在**电气等价**候选点里任取代表。
    # ⇒ 直接消费其 uuid 会把该不确定性注入布线（inc106 实测 segs 863 vs 860）。
    # 处置：把每个 DRC 端点**规范化到其铜岛的确定性锚点**（同网同岛节点按 (类型序, uuid)
    #   取最小），再按 (net, 两端锚) 去重。锚点仅作**起点坐标**；放行闸 seg_exact/via_exact 不变。
    def _root(uu):
        if uu in ctx.pads: return find("p:" + uu)
        if uu in ctx.vias: return find("v:" + uu)
        return find("t:" + uu)

    _anch = {}   # (net, root) -> [rank, uuid, x, y, layer]

    def _offer(net, root, rank, uu, x, y, layer):
        if net is None or root is None or layer not in LAYERS: return
        k = (net, root); cur = _anch.get(k)
        if cur is None or (rank, uu) < (cur[0], cur[1]):
            _anch[k] = [rank, uu, x, y, layer]

    for u, p in ctx.pads.items():
        L = next((l for l in LAYERS if l in p["lay"]), None)
        if L is not None: _offer(p["net"], find("p:" + u), 0, u, p["x"], p["y"], L)
    for u, v in ctx.vias.items():
        L = next((l for l in LAYERS if l in v["lay"]), None)
        if L is not None: _offer(v["net"], find("v:" + u), 1, u, v["x"], v["y"], L)
    for t in ctx.tracks:
        _offer(t["net"], find("t:" + t["uuid"]), 2, t["uuid"],
               (t["x1"] + t["x2"]) / 2.0, (t["y1"] + t["y2"]) / 2.0, t["layer"])

    edges = []
    _seen = set()
    for e in drc.get("unconnected_items", []):
        its = e.get("items", [])
        if len(its) != 2: continue
        ua, ub = its[0].get("uuid"), its[1].get("uuid")
        na, nb = netof(ua), netof(ub)
        if not na or na != nb: continue
        if only_net and na != only_net: continue
        ra, rb = _anch.get((na, _root(ua))), _anch.get((nb, _root(ub)))
        if ra is None or rb is None or ra[1] == rb[1]: continue
        k = (na,) + tuple(sorted((ra[1], rb[1])))
        if k in _seen: continue
        _seen.add(k)
        la, pa = ra[4], (ra[2], ra[3])
        lb, pb = rb[4], (rb[2], rb[3])
        d = math.hypot(pa[0] - pb[0], pa[1] - pb[1])
        edges.append((round(d, 3), na, ra[1], rb[1], la, lb, pa, pb))
    led = {"stage": "M15", "edges": len(edges), "added": [], "blocked": [], "summary": {}}
    if order == "list" and not order_list:
        order_list = None
    if order == "list":
        prio = ([l.strip() for l in open(order_list, encoding="utf-8") if l.strip()]
                if order_list else list(PRIORITY_NETS))
        idx = {n: i for i, n in enumerate(prio)}
        edges.sort(key=lambda z: (idx.get(z[1], len(prio)), z[0], z[2]))
        led["priority_order"] = prio
    elif order == "dist_desc":
        edges.sort(key=lambda z: (-z[0], z[1], z[2]))
    elif order == "hard":
        def _score(z):
            _d, _net, ua, ub, la, lb, pa, pb = z
            tot = 0
            for (_u, _L, _p) in ((ua, la, pa), (ub, lb, pb)):
                x0h, x1h = _p[0] - 1.5, _p[0] + 1.5
                y0h, y1h = _p[1] - 1.5, _p[1] + 1.5
                gh = Grid(ctx, _net, 0.10, x0h, y0h, x1h, y1h, 0.0)
                tot += gh.nx * gh.ny - sum(gh.bad[_L])
            return tot
        edges.sort(key=lambda z: (_score(z), -z[0], z[1]))
    else:
        edges.sort(key=lambda z: (z[0], z[1], z[2]))

    # ── #K2-456 (pass-2) **协商式消解：整轮拆线重排（rip-up & reroute · 有界 · 确定性 · 原子回滚）** ────────
    # 病根（本窗对照实验钉死）：主线贪心「先到先得、只进不退」——`ctx` 在每条成功边后**即刻**吸收其新铜，
    # 后服务者被自己人的铜堵死（`I2C2_SCL`：单网 `[astar] ok` / 全网 `exhausted`）。
    # 处置（**最小**、**无搜索**、**无参数试探**、**无回溯爆炸**）：主线跑完后若有阻断边，则
    #   ① **整轮拆线**（把本跑加入 ctx 的铜全撤）；② **重排一次**：阻断边**优先**（其余保原序）；
    #   ③ 只跑**这一次**；④ **取更优者**（阻断数更少才采纳 · 平手回主线）⇒ **原子**，绝不留半成品。
    def _pass(eorder):
        _added, _blocked, _blocks = [], [], []
        for dist, net, ua, ub, la, lb, pa, pb in eorder:
            _trk = {_t["uuid"] for _t in ctx.tracks}

            def _lk(uu):
                if uu in ctx.pads: return find("p:" + uu)
                if uu in ctx.vias: return find("v:" + uu)
                if uu in _trk: return find("t:" + uu)
                return None
            ca, cb = _lk(ua), _lk(ub)
            if ca is None or cb is None:
                _blocked.append({"net": net, "dist": dist,
                                 "why": "endpoint-absent-from-ctx(%s)" % ("a" if ca is None else "b")})
                continue
            if ca == cb: continue
            try:
                sol, why = solve_edge(ctx, find, ca, cb, net, la, pa, lb, pb, margin, 0.25)
            except Exception as ex:
                if os.environ.get("K2MR_EXC_TRACE"):
                    import traceback as _tb; _tb.print_exc()
                sol, why = None, "exception:%s(%s)" % (type(ex).__name__, str(ex)[:60])
            if sol is None:
                _blocked.append({"net": net, "dist": dist, "why": why}); continue
            nseg = 0; nvia = 0; ln = 0.0
            for (L, pl) in sol["legs"]:
                for k in range(len(pl) - 1):
                    x1, y1 = pl[k]; x2, y2 = pl[k + 1]
                    if math.hypot(x2 - x1, y2 - y1) < 0.001: continue
                    _blocks.append(SEG_BLOCK.format(x1=_fmt(x1), y1=_fmt(y1), x2=_fmt(x2), y2=_fmt(y2),
                                                   layer=LNAME[L], net=net,
                                                   u=seg_uuid(net, L, x1, y1, x2, y2)))
                    ctx.tracks.append(dict(uuid=seg_uuid(net, L, x1, y1, x2, y2), net=net, layer=L,
                                           x1=x1, y1=y1, x2=x2, y2=y2, hw=HW))
                    nseg += 1; ln += math.hypot(x2 - x1, y2 - y1)
            for (x, y, span, l1, l2) in sol["vias"]:
                u = via_uuid(net, l1, l2, x, y)
                blind = "" if span == SPAN_OF[frozenset((F_CU, B_CU))] else " blind"
                _blocks.append(VIA_BLOCK.format(blind=blind, x=_fmt(x), y=_fmt(y),
                                                l1=LNAME[l1], l2=LNAME[l2], net=net, u=u))
                ctx.vias[u] = dict(net=net, x=x, y=y, r=VIA_R, hole=HOLE_R, lay=set(span))
                ctx.holes.append((x, y, HOLE_R, net, span))
                nvia += 1
            _added.append({"net": net, "dist": dist, "segs": nseg, "vias": nvia, "len": round(ln, 4),
                           "via_xy": [[round(v[0], 3), round(v[1], 3)] for v in sol["vias"]],
                           "layers": sorted({LNAME[L] for L, _ in sol["legs"]})})
        return _added, _blocked, _blocks

    _b_tr, _b_vi, _b_ho = len(ctx.tracks), set(ctx.vias), len(ctx.holes)

    def _unwind():
        del ctx.tracks[_b_tr:]
        for _u in [u for u in ctx.vias if u not in _b_vi]: del ctx.vias[_u]
        del ctx.holes[_b_ho:]

    # ── #K2-458 **完整协商回路**：**有界迭代** ＋ **拥塞代价（history 历史 ＋ present 当前）驱动排序** ＋ 原子取优 ──
    # 教令 ②（#K2-456 §2.5 / #K2-458 §2.5）：不是「一次重排」，而是**迭代**「拆边—重布」，每轮按**拥塞代价**
    # 重排行序（被饿死边自然提前），并**保留历轮最优**（不更差才采纳）。
    # · 确定性：代价为整数计数；并列按**原序**（稳定）⇒ 同输入同输出。
    # · 有界：**固定 `RIPUP` 轮**（无搜索 · 无参数试探 · 无回溯爆炸）。
    # · 原子：每轮先 `_unwind()` 到跑前快照；最终**只在严格更优时采纳**，否则回主线结果。
    added, blocked, blocks = _pass(edges)
    led["ripup"] = []
    if RIPUP > 0 and blocked:
        _hist = {}                                        # 每网：历轮**被阻断次数**＝history 代价
        _best = (len(blocked), added, blocked, blocks)
        _order = list(edges)
        _CELL = 2.0                                            # 粗格 2mm（固定 · 非试探）
        _x0f, _y0f, _x1f, _y1f = EDGE_IN
        for _r in range(int(RIPUP)):
            _unwind()
            _a, _b, _k = _pass(_order)
            # #K2-458 sec.2.5 教令 ②（present）：由**本轮已加入的真铜**统计粗格占用（≥2 件＝拥塞），
            # 作为**下一轮**的逐格惩罚区 ⇒ 下一轮 A* 会**主动避让**已拥塞区（present 代价），
            # 与每网 history 排序合为 present+history 协商。
            _occ = {}
            for _t in ctx.tracks[_b_tr:]:
                _cx = int((_t["x1"] - _x0f) // _CELL); _cy = int((_t["y1"] - _y0f) // _CELL)
                for _c in {(_cx, _cy), (int((_t["x2"] - _x0f) // _CELL), int((_t["y2"] - _y0f) // _CELL))}:
                    _occ[_c] = _occ.get(_c, 0) + 1
            _avoid = [(_x0f + _k0 * _CELL, _y0f + _k1 * _CELL,
                       _x0f + (_k0 + 1) * _CELL, _y0f + (_k1 + 1) * _CELL)
                      for (_k0, _k1), _c in _occ.items() if _c >= 2]
            mr_avoid = {"rects": _avoid, "penalty": 2.0} if _avoid else None
            AVOID = mr_avoid
            _nb = len(_b)
            _trail = {"round": _r, "blocked": _nb, "best": _best[0],
                      "adopted": None, "history_nets": sorted(_hist)}
            if _nb < _best[0]:
                _best = (_nb, _a, _b, _k); _trail["adopted"] = "round%d" % _r
            else:
                _trail["adopted"] = None
            for _r2 in _b:                                # present（本轮被阻断）→ 计入 history
                _hist[_r2["net"]] = _hist.get(_r2["net"], 0) + 1
            led["ripup"].append(_trail)
            # 下一轮序：**拥塞代价高的网在前**（被饿死者提前占位），并列保原序
            _pos = {_i: _e for _i, _e in enumerate(edges)}
            _order = [_e for _i, _e in sorted(_pos.items(),
                                              key=lambda t: (-_hist.get(t[1][1], 0), t[0]))]
        if _best[0] < len(blocked):                       # **原子取优**：只在严格更优时替换
            added, blocked, blocks = _best[1], _best[2], _best[3]
        else:
            _unwind()
            added, blocked, blocks = _best[1], _best[2], _best[3]
        led["ripup_adopted"] = any(t["adopted"] for t in led["ripup"])
    if not blocks:                                        # 无新铜 ⇒ 无需整轮拆线（保兜底）
        pass
    led.update({"added": added, "blocked": blocked,
           "summary": {"added": len(added), "blocked": len(blocked),
                       "segs": sum(a["segs"] for a in added), "vias": sum(a["vias"] for a in added),
                       "len": round(sum(a["len"] for a in added), 4),
                       "reasons": {k: sum(1 for x in blocked if x["why"] == k)
                                   for k in sorted({x["why"] for x in blocked})}}})
    json.dump(led, open(ledger_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if dry or not blocks:
        return led["summary"]
    txt = open(src, encoding="utf-8").read()
    anchor = txt.index("\t(segment\n")
    tmp = out_path + ".m15_tmp.kicad_pcb"
    open(tmp, "w", encoding="utf-8").write(txt[:anchor] + "".join(blocks) + txt[anchor:])
    src_pro = re.sub(r"\.kicad_pcb$", ".kicad_pro", src)
    if os.path.exists(src_pro):
        shutil.copyfile(src_pro, re.sub(r"\.kicad_pcb$", ".kicad_pro", tmp))
    r = subprocess.run([sys.executable, os.path.abspath(__file__), "--fill", tmp, out_path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("fill failed rc=%d %s" % (r.returncode, r.stderr[-400:]))
    if os.path.exists(src_pro):
        shutil.copyfile(src_pro, re.sub(r"\.kicad_pcb$", ".kicad_pro", out_path))
    os.remove(tmp)
    return led["summary"]


def _fill(tmp, out_path):
    b2 = pcbnew.LoadBoard(tmp)
    if b2 is None:
        raise SystemExit("_fill: LoadBoard -> None")
    pcbnew.ZONE_FILLER(b2).Fill(b2.Zones())
    b2.Save(out_path)
    print(json.dumps({"fill": "ok"}))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="K2 P4 增量 15：多层迷宫布线器（span 感知孔类 + 扩窗）")
    ap.add_argument("--fill", nargs=2, metavar=("TMP", "OUT"))
    ap.add_argument("--in", dest="src"); ap.add_argument("--drc"); ap.add_argument("--out")
    ap.add_argument("--ledger"); ap.add_argument("--margin", type=float, default=14.0)
    ap.add_argument("--only-net"); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--order", default="dist_asc", choices=["dist_asc", "dist_desc", "hard", "list"])
    ap.add_argument("--ripup", type=int, default=0,
                    help="#K2-456 sec.2.5: bounded pass-2 = rip the whole run's copper and re-route ONCE with the "
                         "blocked nets promoted to the front; adopt only if the block count strictly drops (atomic).")
    ap.add_argument("--order-list", dest="order_list")
    ap.add_argument("--bound-rect", dest="bound_rect", default=None,
                    help="C35 in-loop work-domain wall: x0,y0,x1,y1 (mm) - cells outside are NOT selectable")
    a = ap.parse_args(argv)
    if a.fill:
        return _fill(a.fill[0], a.fill[1])
    if not (a.src and a.drc and a.out and a.ledger):
        ap.error("--in/--drc/--out/--ledger 必填")
    global WALL_RECT, RIPUP
    RIPUP = int(a.ripup or 0)
    if a.bound_rect:
        WALL_RECT = tuple(float(v) for v in a.bound_rect.split(","))
    print(json.dumps(run(a.src, a.drc, a.out, a.ledger, a.margin, a.only_net, a.dry_run,
                         a.order, a.order_list), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
