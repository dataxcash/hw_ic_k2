#!/usr/bin/env python3
"""K2 · B2 —— 逃逸带 GND 缝合孔**最小合法重布放器 v2**（#K2-68 §2.4(a)-2 / §三-2 In5 路径）。

背景（证据链）：
  · 必要条件探针（`k2_p4_b2_feasibility_probe_v1.py`）实测 l9 之 In5 路径 **25/32**：6×`PCIE_DN_OUT*_P`
    之 A 锚落 **513-cell 孤立域**、`PCIE_UP_OUT0_P_J2` 之 A 锚仅 **3-cell** ⇒ 均属 U6 扇出「锚孔笼」。
  · v1（R1C/R1D）用「38 孔全搬出逃逸带」= 敏感度实验**上界**（非最小改动）；12/38 可搬且以长 stub 横穿
    U6 焊盘阵列 ⇒ `shorting_items`/`clearance`/`solder_mask_bridge` 具名 3 项缺陷（R1D）。
  · v2（本件）= 修正 3 项缺陷 + **最小改动**：只搬**开闸必要的那几孔**（本板实测 1 孔即 32/32）。

**v1 → v2 修正（#K2-68 R1D `open_defects_named` ①②③）**
  ① **stub 段-矩形精确距离**：`seg_rect_d()`（含段在矩形内 / 与四边相交判定），替代旧版「只核两端点 vs bbox」。
  ② **阻焊桥判据**：pad 阻焊开窗 = pad bbox + `mask_expansion`；新铜（孔环 / stub）与之净距须 ≥ **0.1mm**（JLC 口径）。
     本板 via 全 tented（无孔开窗）⇒ 只需核 pad 开窗一侧。
  ③ **stub 重接策略**：候选位穷举 + 精确核（孔全层 + 直 stub + DFM 不叠 pad + In5 局部闸门余量）。
     「沿 stub 轴向共线外移」亦在候选集内，但本板实测 **0 合法位**（pad 所在行/列被同列球焊盘堵死）⇒ 按证据择优。

**验收（外部工具核，非本器自证）**
  ① `k2_p4_b2_feasibility_probe_v1.py --layer In5.Cu` ⇒ **32/32**（必要条件）
  ② `kicad-cli pcb drc --severity-all` ⇒ error 仅 #K2-67 具名 3 条 · `unconnected` 0 · `solder_mask_bridge` 0

CLI:
  PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 \
    k2/tools/k2_p4_b2_relocate_stitch_v1.py --in <pcb> --out <pcb> --ledger <json> \
      [--band x0 x1 y0 y1] [--step 0.05] [--search-r 2.0] [--dry-run]
"""
from __future__ import annotations
import argparse, json, math, sys
from collections import deque

import pcbnew

MM = pcbnew.ToMM
def V(x, y): return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))

LAYERS = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "In5.Cu", "In6.Cu", "B.Cu"]
VIA_R, HOLE_R, STUB_HW = 0.175, 0.10, 0.10
BAND = (81.0, 99.0, 48.0, 58.0)
GATE_WINDOW = None      # None ⇒ 由板 bbox + band 自算（与探针栅格对齐：原点 = 板 bbox 角点）
GATE_W = 28.0           # 闸门窗宽 (mm)
GATE_H = 19.0           # 闸门窗高 (mm)
GATE_STEP = 0.10
LANE_PREFIX = ("PCIE_UP_OUT", "PCIE_DN_OUT")


def cls_req(nm):
    if nm.startswith("PCIE") or nm.startswith("REFCLK"): return 0.175
    if nm.startswith(("P3V3", "MCU_", "VREG", "PWR_5V")): return 0.2
    return 0.1


# ------------------------------------------------------------------ 精确几何
def pt_seg_d(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0: return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def pt_rect_d(px, py, lo, hi):
    dx = max(lo[0] - px, 0.0, px - hi[0]); dy = max(lo[1] - py, 0.0, py - hi[1])
    return math.hypot(dx, dy)


def _ccw(p, q, r): return (r[1] - p[1]) * (q[0] - p[0]) - (q[1] - p[1]) * (r[0] - p[0])


def seg_seg_d(A, B, C, D):
    if ((_ccw(C, D, A) > 0) != (_ccw(C, D, B) > 0)) and ((_ccw(A, B, C) > 0) != (_ccw(A, B, D) > 0)): return 0.0
    return min(pt_seg_d(A[0], A[1], C[0], C[1], D[0], D[1]), pt_seg_d(B[0], B[1], C[0], C[1], D[0], D[1]),
               pt_seg_d(C[0], C[1], A[0], A[1], B[0], B[1]), pt_seg_d(D[0], D[1], A[0], A[1], B[0], B[1]))


def seg_rect_d(A, B, lo, hi):
    """**缺陷①**：段-矩形精确距离。"""
    if lo[0] <= A[0] <= hi[0] and lo[1] <= A[1] <= hi[1]: return 0.0
    if lo[0] <= B[0] <= hi[0] and lo[1] <= B[1] <= hi[1]: return 0.0
    for (C, D) in (((lo[0], lo[1]), (hi[0], lo[1])), ((hi[0], lo[1]), (hi[0], hi[1])),
                   ((hi[0], hi[1]), (lo[0], hi[1])), ((lo[0], hi[1]), (lo[0], lo[1]))):
        if seg_seg_d(A, B, C, D) == 0.0: return 0.0
    return min(pt_seg_d(A[0], A[1], *e1, *e2) for e1, e2 in
               (((lo[0], lo[1]), (hi[0], lo[1])), ((hi[0], lo[1]), (hi[0], hi[1])),
                ((hi[0], hi[1]), (lo[0], hi[1])), ((lo[0], hi[1]), (lo[0], lo[1]))))


# ------------------------------------------------------------------ 空间索引
class Idx:
    def __init__(self, items, boxf):
        self.b = {}
        for it in items:
            bx = boxf(it)
            for i in range(int(math.floor(bx[0])) - 1, int(math.floor(bx[2])) + 2):
                for j in range(int(math.floor(bx[1])) - 1, int(math.floor(bx[3])) + 2):
                    self.b.setdefault((i, j), []).append(it)

    def query(self, x0, y0, x1, y1):
        out = []
        for i in range(int(math.floor(x0)) - 1, int(math.floor(x1)) + 2):
            for j in range(int(math.floor(y0)) - 1, int(math.floor(y1)) + 2):
                for it in self.b.get((i, j), ()):
                    if it not in out: out.append(it)
        return out


# ------------------------------------------------------------------ 板级模型
class Board:
    def __init__(self, path):
        self.path = path
        self.b = pcbnew.LoadBoard(path)
        self.name = {n.GetNetCode(): n.GetNetname() for n in self.b.GetNetInfo().NetsByNetcode().values()}
        self.lid = {L: self.b.GetLayerID(L) for L in LAYERS}
        ds = self.b.GetDesignSettings()
        self.ds = {"hole_clearance": MM(ds.m_HoleClearance), "hole_to_hole": MM(ds.m_HoleToHoleMin),
                   "mask_exp": MM(ds.m_SolderMaskExpansion)}
        self.segs = {L: [] for L in LAYERS}
        self.vias, self.holes, self.pads = [], [], []
        for t in self.b.GetTracks():
            nm = self.name.get(t.GetNetCode(), "")
            if t.GetClass() == "PCB_VIA":
                v = t.Cast(); sp = set(v.GetLayerSet().Seq())
                p = (MM(v.GetPosition().x), MM(v.GetPosition().y))
                rec = {"pos": p, "net": nm, "r": MM(v.GetWidth()) / 2.0, "drill": MM(v.GetDrillValue()) / 2.0,
                       "t": v, "layers": [L for L in LAYERS if self.lid[L] in sp],
                       "span": (self.b.GetLayerName(int(v.TopLayer())), self.b.GetLayerName(int(v.BottomLayer())))}
                self.vias.append(rec)
                self.holes.append({"pos": p, "r": rec["drill"], "net": nm, "kind": "via"})
                continue
            L = self.b.GetLayerName(t.GetLayer())
            if L in self.segs:
                self.segs[L].append({"a": (MM(t.GetStart().x), MM(t.GetStart().y)),
                                     "b": (MM(t.GetEnd().x), MM(t.GetEnd().y)),
                                     "hw": MM(t.GetWidth()) / 2.0, "net": nm, "t": t})
        for fp in self.b.GetFootprints():
            for p in fp.Pads():
                nm = p.GetNetname(); pth = p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
                bb = p.GetBoundingBox(); sp = set(p.GetLayerSet().Seq())
                box = (MM(bb.GetX()), MM(bb.GetY()), MM(bb.GetRight()), MM(bb.GetBottom()))
                rec = {"ref": fp.GetReference(), "num": p.GetNumber(), "net": nm, "box": box, "pth": pth,
                       "layers": [L for L in LAYERS if self.lid[L] in sp],
                       "mask": MM(p.GetSolderMaskExpansion(pcbnew.F_Mask)),
                       "pos": (MM(p.GetPosition().x), MM(p.GetPosition().y)), "pad": p}
                self.pads.append(rec)
                if pth:
                    self.holes.append({"pos": rec["pos"], "r": MM(p.GetDrillSize().x) / 2.0, "net": nm,
                                       "kind": "pad", "ref": rec["ref"] + "." + rec["num"]})
        bb = self.b.GetBoardEdgesBoundingBox()
        self.bbox = (MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom()))
        self.isx = {L: Idx(self.segs[L], lambda s: (min(s["a"][0], s["b"][0]), min(s["a"][1], s["b"][1]),
                                                    max(s["a"][0], s["b"][0]), max(s["a"][1], s["b"][1]))) for L in LAYERS}
        self.ipad = Idx(self.pads, lambda p: p["box"])
        self.ivia = Idx(self.vias, lambda v: (v["pos"][0], v["pos"][1], v["pos"][0], v["pos"][1]))
        self.ihole = Idx(self.holes, lambda h: (h["pos"][0], h["pos"][1], h["pos"][0], h["pos"][1]))

    # ---- 新孔合法性（全 8 层铜 + hole_clearance + hole_to_hole）--------------
    def via_violations(self, x, y, self_net="GND", skip_via=None, margin=1.0):
        bad = []
        hc, h2h = self.ds["hole_clearance"], self.ds["hole_to_hole"]
        for L in LAYERS:
            for s in self.isx[L].query(x - margin, y - margin, x + margin, y + margin):
                if s["net"] == self_net: continue
                g = pt_seg_d(x, y, s["a"][0], s["a"][1], s["b"][0], s["b"][1]) - s["hw"]
                if g < VIA_R + cls_req(s["net"]) + 1e-4: bad.append(("cu_seg", L, s["net"], round(g, 4)))
                if g < HOLE_R + hc + 1e-4: bad.append(("hole_seg", L, s["net"], round(g, 4)))
            for p in self.ipad.query(x - margin, y - margin, x + margin, y + margin):
                if p["net"] == self_net: continue
                if L not in p["layers"] and not p["pth"]: continue
                g = pt_rect_d(x, y, p["box"][:2], p["box"][2:])
                if g < VIA_R + cls_req(p["net"]) + 1e-4: bad.append(("cu_pad", L, p["ref"] + "." + p["num"], round(g, 4)))
                if g < HOLE_R + hc + 1e-4: bad.append(("hole_pad", L, p["ref"] + "." + p["num"], round(g, 4)))
            for v in self.ivia.query(x - margin, y - margin, x + margin, y + margin):
                if v["net"] == self_net or v is skip_via: continue
                if L not in v["layers"]: continue
                g = math.hypot(x - v["pos"][0], y - v["pos"][1]) - v["r"]
                if g < VIA_R + cls_req(v["net"]) + 1e-4: bad.append(("cu_via", L, v["net"], round(g, 4)))
                if g < HOLE_R + hc + 1e-4: bad.append(("hole_via", L, v["net"], round(g, 4)))
        for h in self.ihole.query(x - margin, y - margin, x + margin, y + margin):
            if skip_via is not None and abs(h["pos"][0] - skip_via["pos"][0]) < 1e-9 and abs(h["pos"][1] - skip_via["pos"][1]) < 1e-9:
                continue
            g = math.hypot(x - h["pos"][0], y - h["pos"][1]) - h["r"]
            if g < HOLE_R + h2h + 1e-4: bad.append(("hole_to_hole", h["kind"], h.get("ref", ""), round(g, 4)))
        return bad

    # ---- 新直 stub 合法性（F.Cu）------------------------------------------
    def stub_violations(self, A, B, self_net="GND"):
        bad = []
        hc = self.ds["hole_clearance"]
        x0, y0 = min(A[0], B[0]) - 1.5, min(A[1], B[1]) - 1.5
        x1, y1 = max(A[0], B[0]) + 1.5, max(A[1], B[1]) + 1.5
        for s in self.isx["F.Cu"].query(x0, y0, x1, y1):
            if s["net"] == self_net: continue
            g = seg_seg_d(A, B, s["a"], s["b"]) - s["hw"]
            if g < STUB_HW + cls_req(s["net"]) + 1e-4: bad.append(("stub_seg", s["net"], round(g, 4)))
            if g < STUB_HW + hc + 1e-4: bad.append(("stub_hole_cu", s["net"], round(g, 4)))
        for p in self.ipad.query(x0, y0, x1, y1):
            if p["net"] == self_net: continue
            if "F.Cu" not in p["layers"] and not p["pth"]: continue
            g = seg_rect_d(A, B, p["box"][:2], p["box"][2:])              # 缺陷①
            if g < STUB_HW + cls_req(p["net"]) + 1e-4: bad.append(("stub_pad", p["ref"] + "." + p["num"], round(g, 4)))
            e = p["mask"]
            gm = seg_rect_d(A, B, (p["box"][0] - e, p["box"][1] - e), (p["box"][2] + e, p["box"][3] + e))
            if gm < 0.1 - 1e-4: bad.append(("stub_mask_bridge", p["ref"] + "." + p["num"], round(gm, 4)))  # 缺陷②
        for v in self.ivia.query(x0, y0, x1, y1):
            if v["net"] == self_net or "F.Cu" not in v["layers"]: continue
            g = pt_seg_d(v["pos"][0], v["pos"][1], A[0], A[1], B[0], B[1]) - v["r"]
            if g < STUB_HW + cls_req(v["net"]) + 1e-4: bad.append(("stub_via", v["net"], round(g, 4)))
        for h in self.ihole.query(x0, y0, x1, y1):
            if h["net"] == self_net: continue
            g = pt_seg_d(h["pos"][0], h["pos"][1], A[0], A[1], B[0], B[1]) - h["r"]
            if g < STUB_HW + hc + 1e-4: bad.append(("stub_hole", h["kind"], h.get("ref", ""), round(g, 4)))
        return bad

    def stub_of(self, via, tol=0.03, maxlen=2.0, net="GND"):
        out = []
        for s in self.segs["F.Cu"]:
            if s["net"] != net: continue
            if math.hypot(s["b"][0] - s["a"][0], s["b"][1] - s["a"][1]) > maxlen: continue
            for which in ("a", "b"):
                e = s[which]
                if math.hypot(e[0] - via["pos"][0], e[1] - via["pos"][1]) <= tol:
                    out.append((s, which)); break
        return out


# ------------------------------------------------------------------ In5 局部闸门
class Gate:
    """`probe_layer`（In5）之**局部窗口**复刻：只测连通（必要条件），不判定。"""
    @staticmethod
    def auto_window(bd, band, step=GATE_STEP, w=GATE_W, h=GATE_H):
        """与探针栅格对齐（原点 = 板 bbox 左上角）的闸门窗口。"""
        bx0, by0 = bd.bbox[0], bd.bbox[1]
        gx0 = bx0 + math.floor((band[0] - 4.0 - bx0) / step) * step
        gy0 = by0 + math.floor((band[2] - 4.0 - by0) / step) * step
        return (round(gx0, 4), round(gy0, 4), round(gx0 + w, 4), round(gy0 + h, 4))

    def __init__(self, bd: Board, window=None, step=GATE_STEP):
        self.bd = bd; self.x0, self.y0, self.x1, self.y1 = (window or GATE_WINDOW); self.step = step
        self.nx = int(round((self.x1 - self.x0) / step)) + 1
        self.ny = int(round((self.y1 - self.y0) / step)) + 1
        self.hw = 0.16 / 2.0
        self.circs, self.segs, self.rects, self.anchors = [], [], [], {}
        for v in bd.vias:
            if v["net"].startswith(LANE_PREFIX):
                continue                      # 探针语义：车道自身 via 不作障碍（仅 A/B 锚单独计入）
            if "In5.Cu" in v["layers"] and self.inwin(*v["pos"]):
                self.circs.append((v["pos"][0], v["pos"][1], VIA_R, v["net"], v["t"]))
        for s in bd.segs["In5.Cu"]:
            if s["net"].startswith(LANE_PREFIX):
                continue                      # 探针语义：车道自身铜在重迁中会被拆 ⇒ 不作障碍
            if self.rectwin(s["a"][0], s["a"][1], s["b"][0], s["b"][1]):
                self.segs.append((s["a"][0], s["a"][1], s["b"][0], s["b"][1], s["hw"], s["net"]))
        for p in bd.pads:
            if p["net"].startswith(LANE_PREFIX): continue
            if "In5.Cu" not in p["layers"] and not p["pth"]: continue
            if self.rectwin(*p["box"]): self.rects.append(p["box"] + (p["net"],))
        for v in bd.vias:
            nm = v["net"]
            if not nm.startswith(LANE_PREFIX): continue
            if not self.inwin(*v["pos"]): continue
            d = self.anchors.setdefault(nm, {"A": None, "B": None})
            if v["span"] == ("F.Cu", "B.Cu"): d["A"] = v["pos"]
            elif v["span"] == ("F.Cu", "In2.Cu"): d["B"] = v["pos"]

    def inwin(self, x, y): return self.x0 - 1 <= x <= self.x1 + 1 and self.y0 - 1 <= y <= self.y1 + 1
    def rectwin(self, x0, y0, x1, y1):
        return not (max(x0, x1) < self.x0 - 1 or min(x0, x1) > self.x1 + 1 or max(y0, y1) < self.y0 - 1 or min(y0, y1) > self.y1 + 1)

    def lanes(self): return sorted(self.anchors)

    def _mark_circle(self, bad, cx, cy, r, nm):
        self._mark_circle_raw(bad, cx, cy, self.hw + r + cls_req(nm))

    def _mark_circle_raw(self, bad, cx, cy, rad):
        i0 = max(0, int((cx - rad - self.x0) / self.step)); i1 = min(self.nx - 1, int((cx + rad - self.x0) / self.step) + 1)
        j0 = max(0, int((cy - rad - self.y0) / self.step)); j1 = min(self.ny - 1, int((cy + rad - self.y0) / self.step) + 1)
        for i in range(i0, i1 + 1):
            px = self.x0 + i * self.step
            for j in range(j0, j1 + 1):
                if math.hypot(px - cx, self.y0 + j * self.step - cy) < rad: bad[i * self.ny + j] = 1

    def build(self, skip_vias=(), add_vias=()):
        bad = bytearray(self.nx * self.ny)
        for (ax, ay, bx, by, shw, nm) in self.segs:
            rad = self.hw + shw + cls_req(nm)
            i0 = max(0, int((min(ax, bx) - rad - self.x0) / self.step)); i1 = min(self.nx - 1, int((max(ax, bx) + rad - self.x0) / self.step) + 1)
            j0 = max(0, int((min(ay, by) - rad - self.y0) / self.step)); j1 = min(self.ny - 1, int((max(ay, by) + rad - self.y0) / self.step) + 1)
            for i in range(i0, i1 + 1):
                px = self.x0 + i * self.step
                for j in range(j0, j1 + 1):
                    if pt_seg_d(px, self.y0 + j * self.step, ax, ay, bx, by) < rad: bad[i * self.ny + j] = 1
        for (cx, cy, r, nm, v) in self.circs:
            if v in skip_vias: continue
            self._mark_circle(bad, cx, cy, r, nm)
        for (cx, cy, r, nm, _d) in add_vias: self._mark_circle(bad, cx, cy, r, nm)
        for (rx0, ry0, rx1, ry1, nm) in self.rects:
            rad = self.hw + cls_req(nm)
            i0 = max(0, int((rx0 - rad - self.x0) / self.step)); i1 = min(self.nx - 1, int((rx1 + rad - self.x0) / self.step) + 1)
            j0 = max(0, int((ry0 - rad - self.y0) / self.step)); j1 = min(self.ny - 1, int((ry1 + rad - self.y0) / self.step) + 1)
            for i in range(i0, i1 + 1):
                px = self.x0 + i * self.step
                for j in range(j0, j1 + 1):
                    if pt_rect_d(px, self.y0 + j * self.step, (rx0, ry0), (rx1, ry1)) < rad: bad[i * self.ny + j] = 1
        for nm, d in self.anchors.items():
            for key in ("A", "B"):
                c = d[key]
                if c: self._mark_circle_raw(bad, c[0], c[1], VIA_R + self.hw + 0.175)   # 探针语义：anchors 固定 0.43
        self.bad = bad
        return bad

    def cell(self, x, y): return int(round((x - self.x0) / self.step)), int(round((y - self.y0) / self.step))
    def nearest_free(self, x, y, rmax=12):
        i0, j0 = self.cell(x, y)
        for r in range(0, rmax):
            best = None
            for di in range(-r, r + 1):
                for dj in range(-r, r + 1):
                    if max(abs(di), abs(dj)) != r: continue
                    i, j = i0 + di, j0 + dj
                    if 0 <= i < self.nx and 0 <= j < self.ny and not self.bad[i * self.ny + j]:
                        d = math.hypot(di, dj)
                        if best is None or d < best[0]: best = (d, i, j)
            if best: return best
        return None
    def open(self, nm, border=None):
        A = self.anchors.get(nm, {}).get("A")
        if A is None: return True
        if border is None: border = self._border_reach()
        s = self.nearest_free(*A)
        return bool(s and border[s[1] * self.ny + s[2]])
    def _border_reach(self):
        nx, ny, bad = self.nx, self.ny, self.bad
        seen = bytearray(nx * ny); q = deque()
        for i in range(nx):
            for j in (0, ny - 1):
                k = i * ny + j
                if not bad[k] and not seen[k]: seen[k] = 1; q.append((i, j))
        for j in range(ny):
            for i in (0, nx - 1):
                k = i * ny + j
                if not bad[k] and not seen[k]: seen[k] = 1; q.append((i, j))
        while q:
            i, j = q.popleft()
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ni, nj = i + di, j + dj
                if 0 <= ni < nx and 0 <= nj < ny:
                    k = ni * ny + nj
                    if not bad[k] and not seen[k]: seen[k] = 1; q.append((ni, nj))
        self._reach = seen
        return seen
    def blocked(self):
        br = self._border_reach()
        return [nm for nm in self.lanes() if not self.open(nm, br)]


# ------------------------------------------------------------------ 主流程
def run(src, out_path, ledger_path, band, step, search_r, dry):
    bd = Board(src)
    win = Gate.auto_window(bd, band, step=GATE_STEP)
    g = Gate(bd, win)
    base_bad = bytes(g.build())
    lanes = g.lanes()
    border = g._border_reach()
    blocked0 = [nm for nm in lanes if not g.open(nm, border)]
    led = {"tool": "k2_p4_b2_relocate_stitch_v1 (v2 · 最小改动)",
           "src": src, "band": list(band), "gate_window": list(win), "gate_step": GATE_STEP, "step": step, "search_r": search_r,
           "lanes_in_window": len(lanes), "blocked_before": blocked0,
           "defects_fixed": ["① stub 段-矩形精确距离 (seg_rect_d)", "② solder_mask_bridge ≥0.1mm 入模型",
                             "③ stub 重接改为候选位穷举+精确核（共线外移实测 0 合法位）"],
           "moves": [], "removal_screen": {}}
    # 关键孔筛选：单孔移出（=删除语义）后闸门是否全开
    targets = [v for v in bd.vias if v["net"] == "GND" and v["span"] == ("F.Cu", "B.Cu")
               and band[0] <= v["pos"][0] <= band[1] and band[2] <= v["pos"][1] <= band[3]]
    led["n_targets_in_band"] = len(targets)
    critical = []
    for v in targets:
        bad = g.build(skip_vias=(v["t"],))
        br = g._border_reach()
        if all(g.open(nm, br) for nm in lanes):
            critical.append(v)
            led["removal_screen"][("%.3f,%.3f" % v["pos"])] = "opens_gate"
    led["critical_vias"] = [("%.3f,%.3f" % v["pos"]) for v in critical]
    if not blocked0:
        led["summary"] = {"blocked_before": 0, "blocked_after": 0, "moves": 0}
        _write(led, ledger_path); return led
    if not critical:
        led["summary"] = {"error": "no single via removal opens the gate"}
        _write(led, ledger_path); return led
    # 候选位穷举（只对关键孔）
    scored = []
    nx = int(search_r / step)
    for v in critical:
        stubs = bd.stub_of(v)
        if not stubs: continue
        s0, which = stubs[0]
        anchor = s0["b"] if which == "a" else s0["a"]
        nc = 0
        base_skip = bytes(g.build(skip_vias=(v["t"],)))
        for i in range(-nx, nx + 1):
            for j in range(-nx, nx + 1):
                x, y = v["pos"][0] + i * step, v["pos"][1] + j * step
                d = math.hypot(x - v["pos"][0], y - v["pos"][1])
                if d > search_r or d < 1e-9: continue
                if bd.via_violations(x, y, skip_via=v): continue
                if bd.stub_violations(anchor, (x, y)): continue
                if any(pt_rect_d(x, y, p["box"][:2], p["box"][2:]) < VIA_R + 0.05
                       for p in bd.pads if ("F.Cu" in p["layers"] or p["pth"])): continue   # DFM：不叠 pad
                nc += 1
                sl = -1.0
                for dl in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5):
                    bb = bytearray(base_skip)
                    g._mark_circle(bb, x, y, VIA_R + dl, "GND")
                    g.bad = bb
                    br = g._border_reach()
                    if all(g.open(nm, br) for nm in lanes): sl = dl
                    else: break
                if sl >= 0: scored.append((sl, -d, x, y, v, s0, which, anchor))
        led["removal_screen"][("%.3f,%.3f" % v["pos"])] = "opens_gate; legal_cands=%d" % nc
    led["candidates_legal"] = len(scored)
    if not scored:
        led["summary"] = {"error": "no legal candidate position found"}
        _write(led, ledger_path); return led
    scored.sort(reverse=True, key=lambda z: (z[0], z[1]))
    sl, negd, x, y, v, s0, which, anchor = scored[0]
    move = {"from": [round(v["pos"][0], 3), round(v["pos"][1], 3)], "to": [round(x, 3), round(y, 3)],
            "d_mm": round(-negd, 4), "in5_slack_mm": sl, "stub_anchor": [round(anchor[0], 3), round(anchor[1], 3)],
            "stub_len_mm": round(math.hypot(x - anchor[0], y - anchor[1]), 4), "net": v["net"], "span": v["span"]}
    if not dry:
        for (s, wh) in bd.stub_of(v):
            if wh == "a": s["t"].SetStart(V(x, y))
            else: s["t"].SetEnd(V(x, y))
        v["t"].SetPosition(V(x, y))
        try:
            pcbnew.ZONE_FILLER(bd.b).Fill(list(bd.b.Zones())); led["zone_refilled"] = True
        except Exception as e:  # noqa: BLE001
            led["zone_refilled"] = "ERR:%s" % e
        bd.b.Save(out_path)
    led["moves"] = [move]
    if not dry:
        b2 = Board(out_path); g2 = Gate(b2, Gate.auto_window(b2, band, step=GATE_STEP)); g2.build()
        led["blocked_after"] = g2.blocked()
    led["summary"] = {"blocked_before": len(blocked0), "blocked_after": len(led.get("blocked_after", [])),
                      "moves": 1}
    _write(led, ledger_path)
    return led


def _write(led, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(led, f, ensure_ascii=False, indent=1, sort_keys=True)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="out")
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--band", nargs=4, type=float, default=list(BAND))
    ap.add_argument("--step", type=float, default=0.05)
    ap.add_argument("--search-r", type=float, default=2.0)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    led = run(a.src, a.out or a.src, a.ledger, a.band, a.step, a.search_r, a.dry_run)
    print(json.dumps(led.get("summary", {}), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
