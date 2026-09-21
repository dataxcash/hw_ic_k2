#!/usr/bin/env python3
"""K2 · B2 —— 高速数据车道 In2 重布线器 v1（F→In2→F · ≤2 via/线）。

依据（决定性 · 勿重复推导）：
  #K2-66 §六④「高速线过孔 ≤2/线」；#K2-66 §三 齿化表 B2 行；
  `docs/K2-66-B2-LANE-VIA-REDUCTION-PLAN-v1.md` §八：本板换层 span 类
  = {F–In2, In2–In5, In5–B} ⇒ F↔In5 无直接 span ⇒ 长走在 In5 必 4 via；
  **唯一达 ≤2 之拓扑 = 长走改置 In2 ⇒ F→In2→F（2 via）**（= SPEC vias.high_speed 原文口径）。
  SPEC rev-54 `impedance.per_layer.In2.Cu` = 对称带状线（In1/In3 双 GND 参考）· w=0.16 ·
  gap_delivered 0.34/0.44 ⇒ 与现 In5 交付口径同（w=0.16）。

做法（**只增不改他网**；只动 32 条 `PCIE_(UP|DN)_OUT` 数据车道）：
  1. 锚点：A = U6 侧 F-B 通孔位（BGA escape 端）· B = 连接器侧 F-In2 盲孔位；
     **F.Cu 扇出 / 蛇形长度调谐段原样保留**。
  2. 删除该网 4 孔 + 全部非 F.Cu 段（B/In5/In2）。
  3. In2 上 A→B 布线（0/45/90° · w=0.16）· A/B 各置 1 个 F-In2 盲孔 ⇒ **2 via/线**。
  4. 放行闸：逐段精确铜边净距（`req = max(cls(lane), cls(obs))` = PCIe85 0.175 起）·
     In2 全层 rule-area（DoNotAllowTracks）禁入；栅格仅剪枝，最终以精确闸复核。

CLI:
  PYTHONPATH=AppDir/shared/lib/python3.11/dist-packages AppDir/bin/python3.11 \
    k2/tools/k2_p4_b2_in2_relane_v1.py --in <board> --out <board> --ledger <json> \
      [--only NET] [--dry-run] [--step 0.10] [--limit N]
"""
from __future__ import annotations
import argparse, heapq, json, math, os, sys, uuid

import pcbnew

MM = pcbnew.ToMM
def V(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))

LANE_W, LANE_HW = 0.16, 0.08   # 由 --width 覆写
VIA_D, VIA_DRILL = 0.35, 0.20
VIA_R = VIA_D / 2.0
GRID_DEF, SAFE = 0.10, 0.03
NET_NS = uuid.UUID("3f2504e0-4f89-11d3-9a0c-0305e82c3301")
F_CU = pcbnew.F_Cu
IN2_CU = pcbnew.In2_Cu
B_CU = pcbnew.B_Cu
# ── 可配置：默认 In2；`--layer B.Cu --via-bot B.Cu` 则走 F→B→F（2 via）──
LAYER = "In2.Cu"
VIA_BOT = IN2_CU
# 分域窗口（group-window）：DN 车道西向/北向 · UP 车道东向/南向
GW_DN = (46.0, 34.0, 96.0, 64.5)
GW_UP = (80.0, 38.0, 144.0, 72.0)


def _set_safe(v):
    global SAFE
    SAFE = v


def set_cfg(layer="In2.Cu", width=0.16, via_bot="In2.Cu"):
    global LAYER, LANE_W, LANE_HW, VIA_BOT
    LAYER = layer
    LANE_W = width
    LANE_HW = width / 2.0
    VIA_BOT = {"In2.Cu": IN2_CU, "B.Cu": B_CU, "In5.Cu": pcbnew.In5_Cu}[via_bot]


def is_lane(nm: str) -> bool:
    return nm.startswith("PCIE_UP_OUT") or nm.startswith("PCIE_DN_OUT")


def cls_req(nm: str) -> float:
    if nm.startswith("PCIE") or nm.startswith("REFCLK"):
        return 0.175
    if nm.startswith(("P3V3", "MCU_", "VREG", "PWR_5V")):
        return 0.2
    return 0.1


# ─────────────────────────────── 几何 ───────────────────────────────
def pt_seg(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def seg_seg(a, b, c, d):
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) - (B[1] - A[1]) * (C[0] - A[0])
    d1, d2 = ccw(c, d, a), ccw(c, d, b)
    d3, d4 = ccw(a, b, c), ccw(a, b, d)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(pt_seg(*a, *c, *d), pt_seg(*b, *c, *d),
               pt_seg(*c, *a, *b), pt_seg(*d, *a, *b))


def pt_poly(px, py, poly):
    inside, n = False, len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > py) != (y2 > py):
            xx = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if px < xx:
                inside = not inside
    return inside


def pt_poly_dist(px, py, poly):
    if pt_poly(px, py, poly):
        return 0.0
    n = len(poly)
    return min(pt_seg(px, py, poly[i][0], poly[i][1],
                      poly[(i + 1) % n][0], poly[(i + 1) % n][1]) for i in range(n))


def seg_poly_dist(a, b, poly):
    if pt_poly(a[0], a[1], poly) or pt_poly(b[0], b[1], poly):
        return 0.0
    n = len(poly)
    return min(seg_seg(a, b, poly[i], poly[(i + 1) % n]) for i in range(n))


# ─────────────────────────── 障碍 / 精确闸 ───────────────────────────
def collect_obstacles(b):
    name = {n.GetNetCode(): n.GetNetname() for n in b.GetNetInfo().NetsByNetcode().values()}
    in2 = b.GetLayerID(LAYER)
    obs, keep = [], []
    for t in b.GetTracks():
        nm = name.get(t.GetNetCode(), "")
        if is_lane(nm):
            continue
        if t.GetClass() == "PCB_VIA":
            v = t.Cast()
            if in2 in set(v.GetLayerSet().Seq()):
                obs.append({"k": "cir", "net": nm, "extra": 0.0,
                            "c": (MM(v.GetPosition().x), MM(v.GetPosition().y)), "r": VIA_R})
            continue
        if b.GetLayerName(t.GetLayer()) != LAYER:
            continue
        obs.append({"k": "seg", "net": nm, "extra": 0.0,
                    "a": (MM(t.GetStart().x), MM(t.GetStart().y)),
                    "b": (MM(t.GetEnd().x), MM(t.GetEnd().y)), "hw": MM(t.GetWidth()) / 2.0})
    for fp in b.GetFootprints():
        for p in fp.Pads():
            nm = p.GetNetname()
            if is_lane(nm):
                continue
            pth = p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
            if in2 not in set(p.GetLayerSet().Seq()) and not pth:
                continue
            bx = p.GetBoundingBox()
            obs.append({"k": "rect", "net": nm, "extra": 0.0,
                        "lo": (MM(bx.GetX()), MM(bx.GetY())),
                        "hi": (MM(bx.GetRight()), MM(bx.GetBottom()))})
    for z in b.Zones():
        try:
            if not z.GetIsRuleArea() or not z.GetDoNotAllowTracks():
                continue
        except Exception:
            continue
        out = z.Outline()
        for i in range(out.OutlineCount()):
            ch = out.Outline(i)
            pts = [(MM(ch.CPoint(j).x), MM(ch.CPoint(j).y)) for j in range(ch.PointCount())]
            keep.append({"k": "poly", "net": "\x00keepout", "extra": 0.0, "pts": pts})
    return obs, keep


def obs_rad(o, req, hw=LANE_HW):
    ex = o.get("extra", 0.0)
    k = o["k"]
    if k == "seg":
        return hw + o["hw"] + req + ex
    if k == "cir":
        return hw + o["r"] + req + ex
    return hw + req + ex


def seg_min_clear(o, a, b, hw=LANE_HW):
    k = o["k"]
    if k == "seg":
        return seg_seg(a, b, o["a"], o["b"]) - hw - o["hw"]
    if k == "cir":
        return pt_seg(o["c"][0], o["c"][1], a[0], a[1], b[0], b[1]) - hw - o["r"]
    if k == "rect":
        lo, hi = o["lo"], o["hi"]
        cs = [(lo[0], lo[1]), (hi[0], lo[1]), (hi[0], hi[1]), (lo[0], hi[1])]
        return min(seg_seg(a, b, cs[i], cs[(i + 1) % 4]) for i in range(4)) - hw
    return seg_poly_dist(a, b, o["pts"]) - hw


def via_min_clear(o, c):
    x, y = c
    k = o["k"]
    if k == "seg":
        return pt_seg(x, y, o["a"][0], o["a"][1], o["b"][0], o["b"][1]) - VIA_R - o["hw"]
    if k == "cir":
        return math.hypot(x - o["c"][0], y - o["c"][1]) - VIA_R - o["r"]
    if k == "rect":
        lo, hi = o["lo"], o["hi"]
        return pt_poly_dist(x, y, [(lo[0], lo[1]), (hi[0], lo[1]), (hi[0], hi[1]), (lo[0], hi[1])]) - VIA_R
    return pt_poly_dist(x, y, o["pts"]) - VIA_R


# ─────────────────────────── 栅格 + A* ───────────────────────────
class Grid:
    def __init__(self, x0, y0, x1, y1, step):
        self.step = step
        self.x0, self.y0 = x0, y0
        self.nx = int(math.floor((x1 - x0) / step)) + 1
        self.ny = int(math.floor((y1 - y0) / step)) + 1
        self.bad = bytearray(self.nx * self.ny)
        self.wi = None
        self.wj = None

    def idx(self, x, y):
        return (int(round((x - self.x0) / self.step)), int(round((y - self.y0) / self.step)))

    def pt(self, i, j):
        return (self.x0 + i * self.step, self.y0 + j * self.step)

    def set_window(self, xa, ya, xb, yb):
        self.wi = (max(0, self.idx(xa, 0)[0]), max(0, self.idx(xb, 0)[0]))
        self.wj = (max(0, self.idx(0, ya)[1]), max(0, self.idx(0, yb)[1]))

    def inside(self, i, j):
        if not (0 <= i < self.nx and 0 <= j < self.ny):
            return False
        if getattr(self, "wi", None) is None:
            return True
        return self.wi[0] <= i <= self.wi[1] and self.wj[0] <= j <= self.wj[1]

    def mark(self, o, req, extra=0.0):
        rad = obs_rad(o, req) + extra
        k = o["k"]
        if k == "seg":
            ax, ay = o["a"]; bx, by = o["b"]
            i0 = max(0, int((min(ax, bx) - rad - self.x0) / self.step))
            i1 = min(self.nx - 1, int((max(ax, bx) + rad - self.x0) / self.step) + 1)
            j0 = max(0, int((min(ay, by) - rad - self.y0) / self.step))
            j1 = min(self.ny - 1, int((max(ay, by) + rad - self.y0) / self.step) + 1)
            for i in range(i0, i1 + 1):
                px = self.x0 + i * self.step
                for j in range(j0, j1 + 1):
                    if pt_seg(px, self.y0 + j * self.step, ax, ay, bx, by) < rad:
                        self.bad[i * self.ny + j] = 1
        elif k == "cir":
            cx, cy = o["c"]
            i0 = max(0, int((cx - rad - self.x0) / self.step)); i1 = min(self.nx - 1, int((cx + rad - self.x0) / self.step) + 1)
            j0 = max(0, int((cy - rad - self.y0) / self.step)); j1 = min(self.ny - 1, int((cy + rad - self.y0) / self.step) + 1)
            for i in range(i0, i1 + 1):
                px = self.x0 + i * self.step
                for j in range(j0, j1 + 1):
                    if math.hypot(px - cx, self.y0 + j * self.step - cy) < rad:
                        self.bad[i * self.ny + j] = 1
        elif k == "rect":
            lo, hi = o["lo"], o["hi"]
            i0 = max(0, int((lo[0] - rad - self.x0) / self.step)); i1 = min(self.nx - 1, int((hi[0] + rad - self.x0) / self.step) + 1)
            j0 = max(0, int((lo[1] - rad - self.y0) / self.step)); j1 = min(self.ny - 1, int((hi[1] + rad - self.y0) / self.step) + 1)
            for i in range(i0, i1 + 1):
                px = self.x0 + i * self.step
                for j in range(j0, j1 + 1):
                    py = self.y0 + j * self.step
                    dx = max(lo[0] - px, 0.0, px - hi[0]); dy = max(lo[1] - py, 0.0, py - hi[1])
                    if math.hypot(dx, dy) < rad:
                        self.bad[i * self.ny + j] = 1
        else:
            pts = o["pts"]
            xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
            i0 = max(0, int((min(xs) - rad - self.x0) / self.step)); i1 = min(self.nx - 1, int((max(xs) + rad - self.x0) / self.step) + 1)
            j0 = max(0, int((min(ys) - rad - self.y0) / self.step)); j1 = min(self.ny - 1, int((max(ys) + rad - self.y0) / self.step) + 1)
            for i in range(i0, i1 + 1):
                px = self.x0 + i * self.step
                for j in range(j0, j1 + 1):
                    if pt_poly_dist(px, self.y0 + j * self.step, pts) < rad:
                        self.bad[i * self.ny + j] = 1

    def disc_cells(self, c, rad):
        i0, j0 = self.idx(*c)
        rr = int(math.ceil(rad / self.step)) + 1
        out = []
        for di in range(-rr, rr + 1):
            for dj in range(-rr, rr + 1):
                i, j = i0 + di, j0 + dj
                if not self.inside(i, j):
                    continue
                p = self.pt(i, j)
                if math.hypot(p[0] - c[0], p[1] - c[1]) <= rad:
                    out.append(i * self.ny + j)
        return out

    def nearest_free(self, x, y, maxr=5):
        i0, j0 = self.idx(x, y)
        if self.inside(i0, j0) and not self.bad[i0 * self.ny + j0]:
            return (i0, j0)
        for r in range(1, maxr + 1):
            cand = []
            for di in range(-r, r + 1):
                for dj in range(-r, r + 1):
                    if max(abs(di), abs(dj)) != r:
                        continue
                    i, j = i0 + di, j0 + dj
                    if self.inside(i, j) and not self.bad[i * self.ny + j]:
                        cand.append((math.hypot(di, dj), i, j))
            if cand:
                cand.sort()
                return (cand[0][1], cand[0][2])
        return None


DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
SQ2 = math.sqrt(2.0)


def astar(g, s, t, turn_pen=0.30):
    ny = g.ny
    def hv(i, j):
        dx, dy = abs(i - t[0]), abs(j - t[1])
        return SQ2 * min(dx, dy) + abs(dx - dy)
    INF = float("inf")
    dist = {(s, -1): 0.0}
    prev = {}
    pq = [(hv(*s), 0.0, s, -1)]
    goal = None
    while pq:
        f, gc, cell, pd = heapq.heappop(pq)
        st = (cell, pd)
        if gc > dist.get(st, INF) + 1e-12:
            continue
        if cell == t:
            goal = st
            break
        i, j = cell
        for di, dj in DIRS:
            ni, nj = i + di, j + dj
            if not g.inside(ni, nj) or g.bad[ni * ny + nj]:
                continue
            if di and dj and (g.bad[(i + di) * ny + j] or g.bad[i * ny + (j + dj)]):
                continue
            step = SQ2 if (di and dj) else 1.0
            turn = 0.0 if (pd == -1 or (di, dj) == pd) else turn_pen
            ng = gc + step + turn
            nst = ((ni, nj), (di, dj))
            if ng < dist.get(nst, INF) - 1e-12:
                dist[nst] = ng
                prev[nst] = st
                heapq.heappush(pq, (ng + hv(ni, nj), ng, (ni, nj), (di, dj)))
    if goal is None:
        return None
    path, st = [], goal
    while st is not None:
        path.append(st[0])
        st = prev.get(st)
    path.reverse()
    return path


def _dir01(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return None
    if abs(dx) < 1e-9 or abs(dy) < 1e-9 or abs(abs(dx) - abs(dy)) < 1e-6:
        return (dx, dy)
    return None


def _grid_line_free(g, a, b):
    ia, ja = g.idx(*a); ib, jb = g.idx(*b)
    n = max(abs(ib - ia), abs(jb - ja))
    for k in range(n + 1):
        tt = 0.0 if n == 0 else k / n
        i = int(round(ia + (ib - ia) * tt)); j = int(round(ja + (jb - ja) * tt))
        if not g.inside(i, j) or g.bad[i * g.ny + j]:
            return False
    return True


def _turn_points(path):
    """把栅格路径压成拐点序列（方向变化处）。"""
    if len(path) < 2:
        return list(path)
    out = [path[0]]
    prev = None
    for k in range(1, len(path)):
        d = (path[k][0] - path[k - 1][0], path[k][1] - path[k - 1][1])
        if prev is None:
            prev = d
        elif d != prev:
            out.append(path[k - 1])
            prev = d
    out.append(path[-1])
    return out


def string_pull(g, path, max_look=400):
    """拐点级拉直（只保留 0/45/90 且栅格自由之段）。"""
    tp = _turn_points(path)
    if len(tp) <= 2:
        return tp
    out = [tp[0]]
    i = 0
    while i < len(tp) - 1:
        pick = i + 1
        a = g.pt(*tp[i])
        hi = min(len(tp) - 1, i + max_look)
        for j in range(hi, i, -1):
            b = g.pt(*tp[j])
            if _dir01(a, b) is None:
                continue
            if _grid_line_free(g, a, b):
                pick = j
                break
        out.append(tp[pick])
        i = pick
    return out


def poly_from_path(g, path):
    pts = [g.pt(*c) for c in path]
    # 去共线
    out = [pts[0]]
    for k in range(1, len(pts) - 1):
        a, b, c = out[-1], pts[k], pts[k + 1]
        if abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) < 1e-9:
            continue
        out.append(b)
    out.append(pts[-1])
    return out


# ─────────────────────────── 主流程 ───────────────────────────
def _fmt(v):
    s = "%.6f" % v
    s = s.rstrip("0").rstrip(".")
    return s or "0"


def lane_uuid(nm, kind, *args):
    return str(uuid.uuid5(NET_NS, "b2in2|%s|%s|%s" % (nm, kind, "|".join(_fmt(a) for a in args))))


def run(src, out_path, ledger_path, only=None, step=GRID_DEF, limit=None, dry=False,
        margin=12.0, order_mode="dn_first", group_window=False):
    b = pcbnew.LoadBoard(src)
    name = {n.GetNetCode(): n.GetNetname() for n in b.GetNetInfo().NetsByNetcode().values()}
    lanes = {}
    for t in b.GetTracks():
        nm = name.get(t.GetNetCode(), "")
        if not is_lane(nm):
            continue
        d = lanes.setdefault(nm, {"t": [], "v": []})
        if t.GetClass() == "PCB_VIA":
            v = t.Cast()
            d["v"].append(v)
        else:
            d["t"].append(t)
    if only:
        lanes = {k: v for k, v in lanes.items() if k == only}
    anchors = {}
    for nm, d in lanes.items():
        A = B = None
        for v in d["v"]:
            top, bot = int(v.TopLayer()), int(v.BottomLayer())
            if top == F_CU and bot == B_CU:
                A = (MM(v.GetPosition().x), MM(v.GetPosition().y))
            if top == F_CU and bot == IN2_CU:
                B = (MM(v.GetPosition().x), MM(v.GetPosition().y))
        anchors[nm] = (A, B)
    missing = [nm for nm, (A, B) in anchors.items() if A is None or B is None]
    if missing:
        raise SystemExit("锚点缺失: %s" % missing)

    # 1) 拆线（删孔 + 非 F.Cu 段）
    n_rm_t = n_rm_v = 0
    for nm, d in lanes.items():
        for t in d["t"]:
            if t.GetLayer() != F_CU:
                b.Remove(t); n_rm_t += 1
        for v in d["v"]:
            b.Remove(v); n_rm_v += 1

    base_obs, keep_obs = collect_obstacles(b)
    bb = b.GetBoardEdgesBoundingBox()
    x0 = max(MM(bb.GetLeft()) + 0.5, 22.0); y0 = max(MM(bb.GetTop()) + 0.5, 32.0)
    x1 = min(MM(bb.GetRight()) - 0.5, 144.0); y1 = min(MM(bb.GetBottom()) - 0.5, 80.0)

    order = []
    for i in range(8):
        for suf in ("_N_MCIO", "_P_MCIO"):
            order.append("PCIE_DN_OUT%d%s" % (i, suf))
    for i in range(8):
        for suf in ("_N_J2", "_P_J2"):
            order.append("PCIE_UP_OUT%d%s" % (i, suf))
    order = [nm for nm in order if nm in anchors]
    if order_mode == "up_first":
        up = [n for n in order if "UP_OUT" in n]
        dn = [n for n in order if "DN_OUT" in n]
        order = up + dn
    elif order_mode == "interleave":
        up = [n for n in order if "UP_OUT" in n]
        dn = [n for n in order if "DN_OUT" in n]
        order = [x for pair in zip(dn, up) for x in pair]
    if limit:
        order = order[:limit]

    LED = {"tool": "k2_p4_b2_in2_relane_v1", "src": src, "step": step,
           "removed_tracks": n_rm_t, "removed_vias": n_rm_v,
           "n_lanes": len(order), "lanes": [], "failed": []}
    ANCH_RAD = VIA_R + LANE_HW + 0.175          # 孔面相对**他网走线**之禁入半径
    prev_segs = []

    def build(except_nm):
        g = Grid(x0, y0, x1, y1, step)
        for o in base_obs:
            g.mark(o, 0.175, SAFE)
        for o in keep_obs:
            g.mark(o, 0.175, SAFE)
        for (a, c) in prev_segs:
            g.mark({"k": "seg", "net": "\x00lane", "a": a, "b": c,
                    "hw": LANE_HW, "extra": 0.0}, 0.175, SAFE)
        # 他网锚孔（本网除外）
        for nm2, (A2, B2) in anchors.items():
            if nm2 == except_nm:
                continue
            for c in (A2, B2):
                for cell in g.disc_cells(c, ANCH_RAD):
                    g.bad[cell] = 1
        # 本网锚点邻域：清出（其精确净距由终检把关）
        return g

    for nm in order:
        A, B = anchors[nm]
        g = build(nm)
        if group_window:
            if "DN_OUT" in nm:
                g.set_window(GW_DN[0], GW_DN[1], GW_DN[2], GW_DN[3])
            else:
                g.set_window(GW_UP[0], GW_UP[1], GW_UP[2], GW_UP[3])
        else:
            g.set_window(min(A[0], B[0]) - margin, min(A[1], B[1]) - margin,
                         max(A[0], B[0]) + margin, max(A[1], B[1]) + margin)
        for c in (A, B):
            for cell in g.disc_cells(c, LANE_HW + 0.175 + 0.02):
                g.bad[cell] = 0
        s = g.nearest_free(*A, maxr=4)
        t = g.nearest_free(*B, maxr=4)
        rec = {"net": nm, "A": A, "B": B, "start_cell": s, "goal_cell": t}
        if not s or not t:
            rec["status"] = "NO_CELL"
            LED["failed"].append(nm); LED["lanes"].append(rec); continue
        path = astar(g, s, t)
        if not path:
            rec["status"] = "NO_PATH"
            LED["failed"].append(nm); LED["lanes"].append(rec); continue
        sp = string_pull(g, path)
        pts = poly_from_path(g, sp)
        # 精确闸
        worst = 9e9; wwho = None
        for k in range(len(pts) - 1):
            for o in base_obs + keep_obs:
                c = seg_min_clear(o, pts[k], pts[k + 1]) - 0.175
                if c < worst:
                    worst, wwho = c, o
        rec.update({"status": "OK", "n_vertices": len(pts), "min_clear_margin": round(worst, 4),
                    "blocker": (wwho or {}).get("net")})
        rec["pts"] = [(round(p[0], 4), round(p[1], 4)) for p in pts]
        LED["lanes"].append(rec)
        if worst < 0:
            rec["status"] = "CLEAR_FAIL"
        for k in range(len(pts) - 1):
            prev_segs.append((pts[k], pts[k + 1]))

    LED["summary"] = {"ok": sum(1 for r in LED["lanes"] if r["status"] == "OK"),
                      "fail": len(LED["failed"]),
                      "min_clear_margin": min([r.get("min_clear_margin", 9) for r in LED["lanes"]] or [9])}
    if not dry:
        for r in LED["lanes"]:
            if r["status"] != "OK":
                continue
            nm = r["net"]
            for k in range(len(r["pts"]) - 1):
                p1, p2 = r["pts"][k], r["pts"][k + 1]
                nt = pcbnew.PCB_TRACK(b)
                nt.SetStart(V(*p1)); nt.SetEnd(V(*p2))
                nt.SetWidth(pcbnew.FromMM(LANE_W)); nt.SetLayer(pcbnew.GetLayerID(LAYER))
                nt.SetNetCode(b.GetNetcodeFromNetname(nm))
                b.Add(nt)
            for c in (r["A"], r["B"]):
                vi = pcbnew.PCB_VIA(b)
                vi.SetPosition(V(*c))
                vi.SetWidth(pcbnew.FromMM(VIA_D)); vi.SetDrill(pcbnew.FromMM(VIA_DRILL))
                vi.SetLayerPair(F_CU, VIA_BOT)
                vi.SetNetCode(b.GetNetcodeFromNetname(nm))
                b.Add(vi)
        b.Save(out_path)
    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(LED, f, ensure_ascii=False, indent=1, sort_keys=True)
    return LED


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="out")
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--only")
    ap.add_argument("--step", type=float, default=GRID_DEF)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--layer", default="In2.Cu")
    ap.add_argument("--via-bot", default="In2.Cu")
    ap.add_argument("--width", type=float, default=0.16)
    ap.add_argument("--safe", type=float, default=None)
    ap.add_argument("--margin", type=float, default=12.0)
    ap.add_argument("--order", default="dn_first")
    ap.add_argument("--group-window", action="store_true",
                    help="按 DN(西向)/UP(东向) 分域窗口限流，避免跨域超长迂回")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if a.safe is not None:
        _set_safe(a.safe)
    set_cfg(a.layer, a.width, a.via_bot)
    led = run(a.src, a.out or a.src, a.ledger, a.only, a.step, a.limit, a.dry_run,
              a.margin, a.order, a.group_window)
    print(json.dumps(led["summary"], ensure_ascii=False))
    for r in led["lanes"]:
        if r["status"] != "OK":
            print("  FAIL", r["net"], r["status"], r.get("min_clear_margin"), r.get("blocker"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
