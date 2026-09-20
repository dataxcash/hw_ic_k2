#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────────────────────
# [批2·S4 血缘标注 · ARCHER 2026-09-20 · 零行为改动]
# 类别    : HIST(历史分析/复现脚本)
# 作者期板: k2/k2_v4.kicad_pcb（2026-09-16 起为 → hw/k2_v4_8L.kicad_pcb 的符号链接；sha16 fb07d25ac426ff84）
# 别名风险: 无旧板身份字面量；重跑前须自核板身份（解析后 sha 随板文件而变）
# 判定    : 仅标注，零行为改动（#K2-41 §三-⑤）
# ────────────────────────────────────────────────────────────────────────────
"""
mcio_q2_solve.py — K2 MCIO Q2 核心求解：走廊矩形内 16 线无交叉扇出可行性
（v19 改造版：peeling/阶梯路由族 + 簇 x 逐对独立搜索 + 布线序变体 + 精确几何验证）

口径（与任务/v17/Oracle Q1 一致，勿翻案）：
  - 上排 8 源自走廊顶边 y=58.05 下潜（DN0-3），下排 8 源自底边 y=67.75 上浮（DN4-7）
  - via keepout r=0.275；via 中心距 pad 铜 ≥0.475；P/N via 距 ∈[0.55,2.0]
  - 异对 via 中心距 ≥1.225（0.35 铜径 + 0.875 对间铜净空）
  - 对级下游界：cluster x ≥ 该对自身 MCIO pad +x 铜边 +0.475（逐对 stagger）
  - 线宽 0.205；异对中心线距 ≥1.08；同对 P/N 中心线距 ≥0.60
  - 线中心距 pad 铜 ≥0.35；线中心距异网 via 中心 ≥0.2775（铜不重叠物理下限，防短路）
  - 布线域 = 走廊 + 墙后条；障碍 = 真板 pad（扩张）+ 已布线（扩张净空）+ 本对/异对规则
  - 上/下带分离（Oracle Q2 充分条件）：上带线 y ≤ 62.9，下带线 y ≥ 63.1；
    y=63.0 分隔线 x∈[75,88.5] 无任何 pad 铜穿越（实测校验，见 separator_scan）

v19 关键改动（相对 v18）：
  1. 路由族 = peeling/阶梯：簇不再是"贴 min-x 钉死"，簇 x 逐对独立（阶梯+右推，
     簇间 x 距优先 ≥1.5，搜索窗随失败自动放宽）；簇 y 在带内可下沉，让出顶部浅车道
     （后对西侧线可先浅层东行越过前一簇，再于前簇右侧下潜到本对车道深度）。
  2. 布线序变体（fwd_NP / fwd_PN / rev_NP / rev_PN / allN_thenP），逐布局轮询。
  3. verify 增补：线↔异网 via 物理下限 0.2775；上带线 max_y ≤62.9 / 下带线 min_y ≥63.1；
     分隔线 pad 扫描（BoardParser 全 pad 场）。
  4. 搜索 = 结构族随机采样 + 失败定位（每对簇 x/y/极性），成功即构造性证书
     （找不到 ≠ 无解，仅限"该参数族 + 该布线序"）。

用法: python3 mcio_q2_solve.py [mode] [attempts] [seed]
  mode=single  仅上排 DN0-3（快验证）
  mode=all    (default) 16 线全量（上/下带分治 + 全局联合校验）
"""
from __future__ import annotations
import sys, math, heapq, json, os, random
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/_shared")
from eda_core.drc_rules import BoardParser

BOARD = "/home/fila/jqdDev_2025/ic_hw/k2/k2_v4.kicad_pcb"
HERE  = os.path.dirname(os.path.abspath(__file__))

VIA_OCC, VR = 0.55, 0.275
VIA_CU_R = 0.175
REQ      = 0.475          # via 中心距 pad 铜
INTER_CU = 0.875
PN_LO, PN_HI = 0.55, 2.0
TR_W     = 0.205
DIFF_SEP = TR_W + INTER_CU   # 1.08 异对线中心距
PAIR_SEP = 0.60              # 同对 P/N 线中心距
PAD_LN   = 0.35              # 线中心距 pad 铜
VIA_LN   = VIA_CU_R + TR_W/2 # 0.2775 线中心距异网 via 中心（铜不重叠物理下限）
VIA_PN_DY = 0.7              # P/N via 同簇 y 差（默认 0.7 ∈ [0.55,2.0]）
COR_Y0, COR_Y1 = 58.05, 67.75
VIA_Y0, VIA_Y1 = COR_Y0+REQ, COR_Y1-REQ      # 58.525 / 67.275
BAND_Y      = 63.0          # 上/下带分隔线目标
UP_MAX_Y    = 62.9          # 上带线 y 上限
LO_MIN_Y    = 63.1          # 下带线 y 下限
STEP = 0.05
DOM_X0, DOM_X1 = 74.60, 88.40
DOM_Y0, DOM_Y1 = 57.60, 68.40

# 簇 x 搜索：右推量（对 via_minx 的增量），与簇间最小 x 距
X_PUSH_MAX = 2.0
X_STEP     = 0.25
X_GAP_MIN  = 1.5            # 簇间 x 距首选 ≥1.5（失败自动放款到 1.0）

# ─────────────────────────────────────────────────────────────
def load_geometry():
    b = BoardParser(BOARD).parse()
    cap_refs = {f"C{i}" for i in range(17, 33)}
    cap_u3, cap_mcio, cap_rects = {}, {}, []
    u3_rects = []
    for p in b.pads:
        x, y = p.pos; w, h = p.size
        r = (x-w/2, y-h/2, x+w/2, y+h/2)
        if p.footprint_ref in cap_refs:
            cap_rects.append(r)
            n = p.net or ""
            if n.endswith("_U3"):
                cap_u3[n] = dict(ref=p.footprint_ref, x=x, y=y, rect=r)
            elif n.endswith("_MCIO"):
                cap_mcio[p.footprint_ref] = dict(x=x, y=y, rect=r)
        elif p.footprint_ref == "U3":
            u3_rects.append(r)
    u3_left = min(r[0] for r in u3_rects)
    wall_x1 = max(r[2] for r in cap_rects)
    u3_sig = {}
    for p in b.pads:
        if p.footprint_ref == "U3":
            n = p.net or ""
            if n.startswith("PCIE_DN_OUT") and n.endswith("_U3"):
                u3_sig[n] = p.pos[1]
    return dict(cap_u3=cap_u3, cap_mcio=cap_mcio, u3_sig=u3_sig,
                u3_left=u3_left, wall_x1=wall_x1, all_pads=b.pads)

def build_nets(geo):
    nets = {}
    for n, d in geo["cap_u3"].items():
        if not n.startswith("PCIE_DN_OUT"):
            continue
        stem = n[:-3]; pol = stem[-1]; base = stem[:-2]
        m = geo["cap_mcio"][d["ref"]]
        nets[n] = dict(netname=n, pair=base, pol=pol, ref=d["ref"],
                       src_x=d["x"], src_y=d["y"],
                       via_minx=m["rect"][2] + REQ,
                       u3y=geo["u3_sig"].get(n))
    return nets

def pair_meta(nets):
    pm = {}
    for n, d in nets.items():
        pm.setdefault(d["pair"], []).append(d)
    out = {}
    for base, ms in pm.items():
        out[base] = dict(nets=ms, row_y=ms[0]["src_y"],
                         via_minx=max(m["via_minx"] for m in ms),
                         src_xmin=min(m["src_x"] for m in ms),
                         src_xmax=max(m["src_x"] for m in ms),
                         u3_top=min(m["u3y"] for m in ms),
                         u3_bot=max(m["u3y"] for m in ms))
    return out

# ─────────────────────────────────────────────────────────────
# 精确几何
# ─────────────────────────────────────────────────────────────
def pt_seg_dist(p, a, b):
    vx, vy = b[0]-a[0], b[1]-a[1]
    wx, wy = p[0]-a[0], p[1]-a[1]
    L2 = vx*vx + vy*vy
    t = 0.0 if L2 < 1e-14 else max(0.0, min(1.0, (wx*vx+wy*vy)/L2))
    return math.hypot(p[0]-(a[0]+t*vx), p[1]-(a[1]+t*vy))

def seg_seg_dist(a, b, c, d):
    """两线段（轴对齐）精确最短距离：4 端点对折线距离。"""
    best = min(pt_seg_dist(a, c, d), pt_seg_dist(b, c, d),
               pt_seg_dist(c, a, b), pt_seg_dist(d, a, b))
    # 轴对齐共线/交叉的精确修正：若两段正交且投影重叠 → 距离为 0
    ax1, ax2 = min(a[0], b[0]), max(a[0], b[0])
    ay1, ay2 = min(a[1], b[1]), max(a[1], b[1])
    cx1, cx2 = min(c[0], d[0]), max(c[0], d[0])
    cy1, cy2 = min(c[1], d[1]), max(c[1], d[1])
    if ax1 <= cx2 and cx1 <= ax2 and ay1 <= cy2 and cy1 <= ay2:
        return 0.0
    return best

def rect_dist(px, py, r):
    x0, y0, x1, y1 = r
    return math.hypot(max(x0-px, 0, px-x1), max(y0-py, 0, py-y1))

def pad_rect_exp(p, m):
    x, y = p.pos; w, h = p.size
    return (x-w/2-m, y-h/2-m, x+w/2+m, y+h/2+m)

def poly_pad_min(poly, pads, skip_ref=None):
    """折线各段到所有 pad 的最小距离（可排除自己源 pad）。"""
    best = 1e9
    for (a, b) in zip(poly, poly[1:]):
        for p in pads:
            if skip_ref and p.footprint_ref == skip_ref:
                continue
            x, y = p.pos; w, h = p.size
            r = (x-w/2, y-h/2, x+w/2, y+h/2)
            d = min(pt_seg_dist((r[0], r[1]), a, b), pt_seg_dist((r[2], r[1]), a, b),
                    pt_seg_dist((r[2], r[3]), a, b), pt_seg_dist((r[0], r[3]), a, b))
            best = min(best, d)
    return best

def separator_scan(geo, yd=BAND_Y):
    """实测 y=yd 分隔线在 x∈[75,88.5] 是否有 pad 铜穿越。返回穿越列表。"""
    hits = []
    for p in geo["all_pads"]:
        x, y = p.pos; w, h = p.size
        r = (x-w/2, y-h/2, x+w/2, y+h/2)
        if r[3] > yd > r[1] and r[2] > 75.0 and r[0] < 88.5:
            hits.append((p.footprint_ref, p.net or "", r))
    return hits

# ─────────────────────────────────────────────────────────────
# A* 顺序布线器（走廊域内，障碍=pad+已布线；每网带内界 y 硬约束）
# ─────────────────────────────────────────────────────────────
class Router:
    def __init__(self, geo, x0=DOM_X0, x1=DOM_X1, y0=DOM_Y0, y1=DOM_Y1,
                 net_ymax=None, net_ymin=None):
        """net_ymax: netname→y 硬上限(含, 用于上带线 ≤62.9)；net_ymin 同理(下带 ≥63.1)。"""
        self.geo = geo
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.nx = int(round((x1-x0)/STEP))+1
        self.ny = int(round((y1-y0)/STEP))+1
        self.net_ymax = net_ymax or {}
        self.net_ymin = net_ymin or {}
        # pad 扩张 PAD_LN 的静态阻挡（每网格是否被某 pad 阻挡）
        self.pad_block = [[False]*self.ny for _ in range(self.nx)]
        self._build_pad_block()
        self.placed = []   # dict(netname, pair, segs=[(x1,y1,x2,y2)], poly)

    def _build_pad_block(self):
        for p in self.geo["all_pads"]:
            r = pad_rect_exp(p, PAD_LN)
            i0 = max(0, int(math.floor((r[0]-self.x0)/STEP)))
            i1 = min(self.nx-1, int(math.ceil((r[2]-self.x0)/STEP)))
            j0 = max(0, int(math.floor((r[1]-self.y0)/STEP)))
            j1 = min(self.ny-1, int(math.ceil((r[3]-self.y0)/STEP)))
            for ix in range(i0, i1+1):
                for iy in range(j0, j1+1):
                    self.pad_block[ix][iy] = True

    def _idx(self, x, y):
        ix = int(round((x-self.x0)/STEP)); iy = int(round((y-self.y0)/STEP))
        if ix < 0 or iy < 0 or ix >= self.nx or iy >= self.ny:
            return None
        return ix, iy

    def _in_own_pad(self, ix, iy, mynet):
        """该格是否落在自己网 pad（同 net 铜）扩张区内 → 放行。"""
        px = self.x0 + ix*STEP; py = self.y0 + iy*STEP
        for p in self.geo["all_pads"]:
            if p.net == mynet:
                r = pad_rect_exp(p, PAD_LN)
                if r[0] <= px <= r[2] and r[1] <= py <= r[3]:
                    return True
        return False

    def _blocked(self, ix, iy, mypair, mynet):
        if self.pad_block[ix][iy] and not self._in_own_pad(ix, iy, mynet):
            return True
        py = self.y0 + iy*STEP
        mymax = self.net_ymax.get(mynet); mymin = self.net_ymin.get(mynet)
        if mymax is not None and py > mymax + 1e-9:
            return True
        if mymin is not None and py < mymin - 1e-9:
            return True
        for pl in self.placed:
            if pl["netname"] == mynet:
                continue
            need = PAIR_SEP if pl["pair"] == mypair else DIFF_SEP
            px = self.x0 + ix*STEP
            for (x1, y1, x2, y2) in pl["segs"]:
                # 轴对齐段到点距离快速判定
                if x1 == x2:  # vertical
                    if y1 > y2: y1, y2 = y2, y1
                    if y1 - need <= py <= y2 + need and abs(px-x1) < need:
                        return True
                else:         # horizontal
                    if x1 > x2: x1, x2 = x2, x1
                    if x1 - need <= px <= x2 + need and abs(py-y1) < need:
                        return True
        return False

    def route(self, start, goal, mypair, mynet):
        si = self._idx(*start); gi = self._idx(*goal)
        if si is None or gi is None:
            return None
        # goal 需避开 pad（via 需 ≥REQ 到 pad 铜）——由外部 cluster 预检保证；
        # 这里只保证网格可达
        if self._blocked(*gi, mypair, mynet):
            return None
        if self._blocked(*si, mypair, mynet):
            return None
        def heur(a, b): return abs(a[0]-b[0]) + abs(a[1]-b[1])
        open_h = [(heur(si, gi), 0, si)]
        gcost = {si: 0}
        prev = {}
        closed = set()
        found = False
        while open_h:
            f, g, cur = heapq.heappop(open_h)
            if cur in closed:
                continue
            if cur == gi:
                found = True
                break
            closed.add(cur)
            for (dx, dy, w) in ((1,0,1.0), (0,1,1.0), (0,-1,1.0), (-1,0,1.6)):
                nx_, ny_ = cur[0]+dx, cur[1]+dy
                if nx_ < 0 or ny_ < 0 or nx_ >= self.nx or ny_ >= self.ny:
                    continue
                if self._blocked(nx_, ny_, mypair, mynet):
                    continue
                ng = g + w
                if (nx_, ny_) not in gcost or ng < gcost[(nx_, ny_)]:
                    gcost[(nx_, ny_)] = ng
                    prev[(nx_, ny_)] = cur
                    heapq.heappush(open_h, (ng + heur((nx_, ny_), gi), ng,
                                            (nx_, ny_)))
        if not found:
            return None
        path = [gi]
        while path[-1] != si:
            path.append(prev[path[-1]])
        path.reverse()
        poly = []
        for (ix, iy) in path:
            pt = (self.x0 + ix*STEP, self.y0 + iy*STEP)
            if not poly:
                poly.append(pt)
            else:
                dx = pt[0]-poly[-1][0]; dy = pt[1]-poly[-1][1]
                if len(poly) >= 2:
                    pdx = poly[-1][0]-poly[-2][0]
                    pdy = poly[-1][1]-poly[-2][1]
                    if abs(dx*pdy - dy*pdx) < 1e-9:
                        poly[-1] = pt
                        continue
                poly.append(pt)
        return poly

    def add_route(self, netname, pair, poly):
        segs = []
        for (a, b) in zip(poly, poly[1:]):
            segs.append((a[0], a[1], b[0], b[1]))
        self.placed.append(dict(netname=netname, pair=pair, segs=segs, poly=poly))

# ─────────────────────────────────────────────────────────────
# 簇布局
# ─────────────────────────────────────────────────────────────
def band_of(pair_row_y):
    return "up" if pair_row_y < 63.0 else "lo"

def y_band_clamp(band, yP, pn_dy=VIA_PN_DY):
    """P-via 目标 y 收进带内；返回 (yP, yN)（P 上 N 下，PN 取向）。"""
    if band == "up":
        ylo, yhi = VIA_Y0, UP_MAX_Y - pn_dy
    else:
        ylo, yhi = LO_MIN_Y, VIA_Y1 - pn_dy
    if yP < ylo: yP = ylo
    if yP > yhi: yP = yhi
    return yP, yP + pn_dy

def make_clusters(pmeta, base_list, xpos, ypos, orient="PN", pn_dy=VIA_PN_DY):
    """base_list: x 序对列表；xpos[base]=簇 x(≥via_minx)；ypos[base]=上 via 目标 y。
    orient: "PN"→P 在上；"NP"→N 在上。返回 {base: {P:(x,y), N:(x,y)}}。"""
    cl = {}
    for base in base_list:
        pr = pmeta[base]
        band = band_of(pr["row_y"])
        yU, yL = y_band_clamp(band, ypos[base], pn_dy)
        cx = xpos[base]
        if orient == "PN":
            cl[base] = {"P": (cx, yU), "N": (cx, yL)}
        else:
            cl[base] = {"N": (cx, yU), "P": (cx, yL)}
    return cl

def cluster_precheck(geo, pmeta, base_list, clusters):
    """簇几何预检（via↔pad ≥REQ / P/N∈[.55,2] / 异对 via ≥1.225 / 窗口）→ 违规串/None"""
    vias = {}
    for base in base_list:
        for pol in ("P", "N"):
            vias[f"{base}.{pol}"] = clusters[base][pol]
    vio = []
    for base in base_list:
        (px, py) = clusters[base]["P"]; (nx, ny) = clusters[base]["N"]
        d = math.hypot(px-nx, py-ny)
        if not (PN_LO-1e-9 <= d <= PN_HI+1e-9):
            vio.append(f"{base} P/N {d:.3f}")
        pr = pmeta[base]
        for pol in ("P", "N"):
            cx, cy = clusters[base][pol]
            if cx < pr["via_minx"] - 1e-9:
                vio.append(f"{base}.{pol} x<下游界")
            band = band_of(pr["row_y"])
            if band == "up" and not (VIA_Y0-1e-9 <= cy <= UP_MAX_Y+1e-9):
                vio.append(f"{base}.{pol} y出上带")
            if band == "lo" and not (LO_MIN_Y-1e-9 <= cy <= VIA_Y1+1e-9):
                vio.append(f"{base}.{pol} y出下带")
            for p in geo["all_pads"]:
                px_, py_ = p.pos; w, h = p.size
                d2 = rect_dist(cx, cy, (px_-w/2, py_-h/2, px_+w/2, py_+h/2))
                if d2 < REQ - 1e-9:
                    vio.append(f"{base}.{pol} via距pad {d2:.3f}")
    for i in range(len(base_list)):
        for j in range(i+1, len(base_list)):
            for p1 in ("P", "N"):
                for p2 in ("P", "N"):
                    a = clusters[base_list[i]][p1]; b = clusters[base_list[j]][p2]
                    d = math.hypot(a[0]-b[0], a[1]-b[1])
                    need = 2*VIA_CU_R + INTER_CU
                    if d < need - 1e-9:
                        vio.append(f"异对via {base_list[i]}.{p1}-{base_list[j]}.{p2} {d:.3f}")
    return vio or None

# ─────────────────────────────────────────────────────────────
# 布线序变体
# ─────────────────────────────────────────────────────────────
def order_variants(base_list, src_of):
    """base_list = 带内 x 序；src_of[base] = 对内西网 pol（=N）。返回多种 (base,pol) 序列。"""
    np_fwd = [(b, "N") for b in base_list] + [(b, "P") for b in base_list]
    # 标准：x 序逐对 N→P
    std = []
    for b in base_list:
        std += [(b, "N"), (b, "P")]
    # 逐对 P→N（P 短 stub 先占浅层，N 后绕）——常不利但列入
    pn_fwd = []
    for b in base_list:
        pn_fwd += [(b, "P"), (b, "N")]
    rev_np = []
    for b in reversed(base_list):
        rev_np += [(b, "N"), (b, "P")]
    # 全 N（西→东）再全 P（东→西）
    alln = [(b, "N") for b in base_list] + [(b, "P") for b in reversed(base_list)]
    return [std, rev_np, pn_fwd, np_fwd, alln]

# ─────────────────────────────────────────────────────────────
# 逐布局 布线 + 精确验证
# ─────────────────────────────────────────────────────────────
def route_layout(geo, nets, pmeta, base_list, clusters, order, net_ymax, net_ymin):
    """按给定序布线。返回 (routes, fail_net) 或 (None, fail)。routes={net:poly}"""
    r = Router(geo, net_ymax=net_ymax, net_ymin=net_ymin)
    routes = {}
    for (base, pol) in order:
        pr = pmeta[base]
        m = [z for z in pr["nets"] if z["pol"] == pol][0]
        top = pr["row_y"] < 63.0
        edge = COR_Y0 if top else COR_Y1
        sx = m["src_x"]
        vx, vy = clusters[base][pol]
        start = (sx, edge)
        goal = (vx, vy)
        poly = r.route(start, goal, base, m["netname"])
        if poly is None:
            return None, m["netname"], (base, pol)
        routes[m["netname"]] = poly
        r.add_route(m["netname"], base, poly)
    return routes, None, None

def verify_full(geo, nets, pmeta, clusters, routes, need_band=True):
    """全约束精确验证（含 v19 新增：线↔via / 带内线界）。返回 (vio, margin)。"""
    vio = []
    margin = {"via_pad": 1e9, "pn": 1e9, "inter_via": 1e9, "line_cross": 1e9,
              "line_diff": 1e9, "line_pair": 1e9, "line_pad": 1e9,
              "line_via": 1e9, "band_up": 1e9, "band_lo": 1e9}
    vias = {}
    for base, cv in clusters.items():
        for pol in ("P", "N"):
            for m in pmeta[base]["nets"]:
                if m["pol"] == pol:
                    vias[m["netname"]] = cv[pol]
    # via vs pad / P-N / 异对 via
    for n, (x, y) in vias.items():
        for p in geo["all_pads"]:
            px, py = p.pos; w, h = p.size
            d = rect_dist(x, y, (px-w/2, py-h/2, px+w/2, py+h/2))
            margin["via_pad"] = min(margin["via_pad"], d)
            if d < REQ - 1e-9:
                vio.append(f"via {n} 距 pad {d:.3f}<{REQ}")
    for base, pr in pmeta.items():
        if base not in clusters:
            continue
        vp = vias[[m["netname"] for m in pr["nets"] if m["pol"]=="P"][0]]
        vn = vias[[m["netname"] for m in pr["nets"] if m["pol"]=="N"][0]]
        d = math.hypot(vp[0]-vn[0], vp[1]-vn[1])
        margin["pn"] = min(margin["pn"], d)
        if not (PN_LO-1e-9 <= d <= PN_HI+1e-9):
            vio.append(f"pair {base} P/N dist {d:.3f}∉[.55,2]")
        for m in pr["nets"]:
            if vias[m["netname"]][0] < m["via_minx"]-1e-9:
                vio.append(f"via {m['netname']} x<下游界 {m['via_minx']:.2f}")
    names = list(vias)
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            if nets[names[i]]["pair"] == nets[names[j]]["pair"]:
                continue
            d = math.hypot(vias[names[i]][0]-vias[names[j]][0],
                           vias[names[i]][1]-vias[names[j]][1])
            need = 2*VIA_CU_R + INTER_CU
            margin["inter_via"] = min(margin["inter_via"], d)
            if d < need - 1e-9:
                vio.append(f"异对 via {names[i]}-{names[j]} {d:.3f}<{need:.3f}")
    # 折线两两 + vs pad + vs via + 带界
    rn = list(routes)
    for i in range(len(rn)):
        n1 = rn[i]
        poly1 = routes[n1]
        if need_band:
            pr1 = pmeta[nets[n1]["pair"]]
            band = band_of(pr1["row_y"])
            for (a, b) in zip(poly1, poly1[1:]):
                if band == "up":
                    ymax = max(a[1], b[1])
                    margin["band_up"] = min(margin["band_up"], UP_MAX_Y - ymax)
                    if ymax > UP_MAX_Y + 1e-9:
                        vio.append(f"上带线 {n1} 越 {UP_MAX_Y} (y={ymax:.3f})")
                else:
                    ymin = min(a[1], b[1])
                    margin["band_lo"] = min(margin["band_lo"], ymin - LO_MIN_Y)
                    if ymin < LO_MIN_Y - 1e-9:
                        vio.append(f"下带线 {n1} 越 {LO_MIN_Y} (y={ymin:.3f})")
        for j in range(i+1, len(rn)):
            n2 = rn[j]
            same = nets[n1]["pair"] == nets[n2]["pair"]
            need = PAIR_SEP if same else DIFF_SEP
            dmin = 1e9
            for (a, b) in zip(poly1, poly1[1:]):
                for (c, d) in zip(routes[n2], routes[n2][1:]):
                    dmin = min(dmin, seg_seg_dist(a, b, c, d))
            key = "line_pair" if same else "line_diff"
            margin[key] = min(margin[key], dmin)
            if dmin < need - 1e-6:
                vio.append(f"线 {n1}-{n2} 中心距 {dmin:.3f}<{need:.3f}"
                           + ("(同对)" if same else "(异对)"))
        # line vs pad（跳过自身源 cap ref；注意 U3 pad 不豁免——同网也按 PAD_LN）
        myref = nets[n1]["ref"]
        for p in geo["all_pads"]:
            if p.footprint_ref == myref:
                continue
            px, py = p.pos; w, h = p.size
            r0 = (px-w/2, py-h/2, px+w/2, py+h/2)
            for (a, b) in zip(poly1, poly1[1:]):
                d = min(pt_seg_dist((r0[0], r0[1]), a, b),
                        pt_seg_dist((r0[2], r0[1]), a, b),
                        pt_seg_dist((r0[2], r0[3]), a, b),
                        pt_seg_dist((r0[0], r0[3]), a, b))
                margin["line_pad"] = min(margin["line_pad"], d)
                if d < PAD_LN - 1e-6:
                    vio.append(f"线 {n1} 距 {p.footprint_ref} pad {d:.3f}")
        # line vs 异网 via（物理下限，防短路；自身 via 豁免）
        for n2, (vx, vy) in vias.items():
            if n2 == n1:
                continue
            for (a, b) in zip(poly1, poly1[1:]):
                d = pt_seg_dist((vx, vy), a, b)
                margin["line_via"] = min(margin["line_via"], d)
                if d < VIA_LN - 1e-6:
                    vio.append(f"线 {n1} 距 via {n2} {d:.3f}<{VIA_LN:.3f}")
    return vio, margin

# ─────────────────────────────────────────────────────────────
# 搜索：带内逐对 x/y/极性 随机采样 + 布线序轮询
# ─────────────────────────────────────────────────────────────
def sample_x(base_list, pmeta, rng, x_gap_min):
    """阶梯+右推采样：返回 {base: 簇 x}，x ≥ via_minx，簇间 x 距 ≥ x_gap_min（尽力）。"""
    xpos = {}
    for k, base in enumerate(base_list):
        mn = pmeta[base]["via_minx"]
        hi = min(mn + X_PUSH_MAX, 88.0)
        lo = mn
        if k == 0:
            pass
        else:
            prev = xpos[base_list[k-1]]
            lo = max(lo, prev + x_gap_min)
            if lo > hi:                     # 放款到 ≥1.0
                lo = max(mn, prev + 1.0)
            if lo > hi:
                lo = mn
        hi = max(hi, lo)
        # 候选 = 从 lo 起的少量离散 x（间隔 ~0.25-0.5），含随机右推
        step = X_STEP
        cands = [round(lo + m*step, 2) for m in range(9)]
        cands = [c for c in cands if c <= hi + 1e-9]
        if not cands:
            cands = [lo]
        # 偏向 lo（少推）但保留右推尾
        w = [4, 3, 2, 2, 1, 1, 1, 1, 1][:len(cands)]
        xpos[base] = max(mn, round(rng.choices(cands, weights=w, k=1)[0], 2))
    return xpos

def sample_y(base_list, pmeta, rng):
    """带内簇 y：浅车道剥离族要求前对簇足够深（P-via ≥~59.8，让出 58.45-58.6
    顶浅车道给后对西线东行越过），故对上带设下限 59.8、上限 62.9-pn_dy。"""
    ypos = {}
    for base in base_list:
        pr = pmeta[base]
        band = band_of(pr["row_y"])
        nat = pr["u3_top"]
        if band == "up":
            nat = max(nat, 59.8)
            offs = [-0.2, -0.1, 0.0, 0.15, 0.3, 0.5, 0.7, 0.9]
            hi = UP_MAX_Y - VIA_PN_DY
        else:
            offs = [-0.7, -0.5, -0.3, -0.15, 0.0, 0.15, 0.3]
            hi = VIA_Y1 - VIA_PN_DY
        y = nat + rng.choice(offs)
        if y < VIA_Y0:
            y = VIA_Y0
        if y > hi:
            y = hi
        ypos[base] = y
    return ypos

def solve_band(geo, nets, pmeta, base_list, attempts, seed, orders_extra=None,
               x_gap_min=X_GAP_MIN, verbose=True):
    """对带内 base_list 做簇布局搜索 + 布线序轮询。
    返回 (clusters, routes, vio, margin, order_used, fails_log) or (None,..., 卡点诊断)。"""
    net_ymax = {m["netname"]: UP_MAX_Y for b in base_list for m in pmeta[b]["nets"]}
    net_ymin = {m["netname"]: LO_MIN_Y for b in base_list for m in pmeta[b]["nets"]}
    if band_of(pmeta[base_list[0]]["row_y"]) == "up":
        net_ymin = {}
    else:
        net_ymax = {}
    variants = order_variants(base_list, None)
    rng = random.Random(seed)
    fails_log = []
    best_fail = None   # (net, base, pol, 最远进展)
    for a in range(attempts):
        xpos = sample_x(base_list, pmeta, rng, x_gap_min)
        ypos = sample_y(base_list, pmeta, rng)
        orient = rng.choice(["PN", "PN", "PN", "NP"])
        clusters = make_clusters(pmeta, base_list, xpos, ypos, orient)
        pv = cluster_precheck(geo, pmeta, base_list, clusters)
        if pv:
            fails_log.append(("precheck", pv[0]))
            continue
        for oi, order in enumerate(variants):
            routes, fnet, fwho = route_layout(geo, nets, pmeta, base_list,
                                              clusters, order, net_ymax, net_ymin)
            if routes is None:
                if best_fail is None or True:
                    fails_log.append(("route", fnet, fwho,
                                      {b: clusters[b] for b in base_list}))
                continue
            vio, margin = verify_full(geo, nets, pmeta, clusters, routes)
            if not vio:
                if verbose:
                    print(f"✔ 第 {a} 布局 / 序 {oi} 全绿 "
                          f"(簇x={[round(xpos[b],2) for b in base_list]}, "
                          f"margin line_diff={margin['line_diff']:.3f} "
                          f"line_pad={margin['line_pad']:.3f} "
                          f"via_pad={margin['via_pad']:.3f})")
                return clusters, routes, vio, margin, order, fails_log
            else:
                fails_log.append(("verify", len(vio), vio[0]))
    if verbose:
        print(f"✗ {attempts} 布局搜索未全绿（x_gap_min={x_gap_min}）。"
              f"样本失败分布: " + str([f[:2] for f in fails_log[:12]]))
    return None, None, None, None, None, fails_log

# ─────────────────────────────────────────────────────────────
def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    attempts = int(sys.argv[2]) if len(sys.argv) > 2 else 600
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 7
    geo = load_geometry()
    nets = build_nets(geo)
    pmeta = pair_meta(nets)
    up = sorted([b for b in pmeta if pmeta[b]["row_y"] < 63.0],
                key=lambda b: pmeta[b]["src_xmin"])
    lo = sorted([b for b in pmeta if pmeta[b]["row_y"] > 63.0],
                key=lambda b: pmeta[b]["src_xmin"])

    # 分隔线 pad 扫描（BoardParser 全 pad 场，权威）
    hits = separator_scan(geo)
    print(f"分隔线 y={BAND_Y} x∈[75,88.5] pad 穿越: {len(hits)} 处")
    for h in hits[:8]:
        print("   ", h)

    if mode == "single":
        cu, cr, cv, cm, co, cf = solve_band(geo, nets, pmeta, up, attempts, seed)
        if cu is None:
            # 放宽簇间 x 距再试
            print("→ 放宽簇间 x 距 ≥1.0 再搜一轮")
            cu, cr, cv, cm, co, cf = solve_band(geo, nets, pmeta, up,
                                                attempts, seed+1, x_gap_min=1.0)
        if cu is None:
            # 故障现场诊断输出
            dump_failure(geo, nets, pmeta, up, cf)
            return 1
        emit_solution(geo, nets, pmeta, cu, cr, cm, mode, {"up": cu, "lo": None})
        return 0
    else:
        # mode=all：上/下带分治求解 → 全局联合验证（跨带线距仍按 1.08）
        res_up = solve_band(geo, nets, pmeta, up, attempts, seed)
        if res_up[0] is None:
            res_up = solve_band(geo, nets, pmeta, up, attempts, seed+1, x_gap_min=1.0)
        if res_up[0] is None:
            dump_failure(geo, nets, pmeta, up, res_up[5])
            return 1
        cu, cr_u, _, cm_u, _, _ = res_up
        res_lo = solve_band(geo, nets, pmeta, lo, attempts, seed+1000)
        if res_lo[0] is None:
            res_lo = solve_band(geo, nets, pmeta, lo, attempts, seed+1001, x_gap_min=1.0)
        if res_lo[0] is None:
            dump_failure(geo, nets, pmeta, lo, res_lo[5])
            return 1
        cl, cr_l, _, cm_l, _, _ = res_lo
        # 全局联合验证：全部 16 线放一起（各自带内界）+ 簇不变 → 路由已含跨带互斥
        clusters = dict(cu); clusters.update(cl)
        net_ymax = {m["netname"]: UP_MAX_Y for b in up for m in pmeta[b]["nets"]}
        net_ymin = {m["netname"]: LO_MIN_Y for b in lo for m in pmeta[b]["nets"]}
        base_all = up + lo
        order = order_variants(up, None)[0] + order_variants(lo, None)[0]
        routes, fnet, fwho = route_layout(geo, nets, pmeta, base_all, clusters,
                                          order, net_ymax, net_ymin)
        if routes is None:
            print(f"联合布线失败 {fnet} {fwho} —— 上/下带独立解在联合域不共存，"
                  f"尝试全带联合搜索（attempts={attempts}）")
            # 全带联合搜索
            cu2, cr2, cv2, cm2, co2, cf2 = solve_band(geo, nets, pmeta, up+lo,
                                                      attempts, seed+777)
            if cu2 is None:
                dump_failure(geo, nets, pmeta, up+lo, cf2)
                return 1
            emit_solution(geo, nets, pmeta, cu2, cr2, cm2, mode,
                          {"up": {b: cu2[b] for b in up}, "lo": {b: cu2[b] for b in lo}})
            return 0
        vio, margin = verify_full(geo, nets, pmeta, clusters, routes)
        if vio:
            print(f"联合验证违规 {len(vio)} 条（独立解不共存）：")
            for v in vio[:20]:
                print("  ✗", v)
            return 2
        print("==== mode=all 全绿（16 线构造性证书，分治+联合验证通过） ====")
        emit_solution(geo, nets, pmeta, clusters, routes, margin, mode,
                      {"up": cu, "lo": cl})
        return 0

def dump_failure(geo, nets, pmeta, base_list, fails_log):
    print("\n==== 有限搜索全失败：卡点诊断（供 Q3 摆件改动量化） ====")
    rfail = [f for f in fails_log if f[0] == "route"]
    print(f"路由失败样本 {len(rfail)} 个；precheck {len([f for f in fails_log if f[0]=='precheck'])}")
    seen = {}
    for f in rfail[:40]:
        net = f[1]; base = f[2][0]; pol = f[2][1]
        key = (base, pol)
        seen[key] = seen.get(key, 0) + 1
    if seen:
        worst = max(seen, key=seen.get)
        print(f"  最常失败: 对 {worst[0]} {worst[1]} 线（{seen[worst]}/{min(len(rfail),40)} 样本）")
        pr = pmeta[worst[0]]
        print(f"    该对 via_minx={pr['via_minx']:.2f} 源 N/P x=({pr['src_xmin']:.2f},{pr['src_xmax']:.2f}) "
              f"U3 目标 y=({pr['u3_top']:.2f},{pr['u3_bot']:.2f})")
    else:
        print("  全部失败在 precheck 或 verify 阶段（簇几何违规），样本:", fails_log[:5])

def emit_solution(geo, nets, pmeta, clusters, routes, margin, mode, bands):
    print("\n==== 全绿布局（构造性证书） ====")
    print("via 坐标（每对 P/N）与最小 margin：")
    print("  via↔pad:", round(margin["via_pad"], 3), "| P/N:", round(margin["pn"], 3),
          "| 异对via:", round(margin["inter_via"], 3))
    print("  异对线:", round(margin["line_diff"], 3), "| 同对线:", round(margin["line_pair"], 3),
          "| 线↔pad:", round(margin["line_pad"], 3), "| 线↔via:", round(margin["line_via"], 3))
    for b in sorted(pmeta, key=lambda x: (pmeta[x]["row_y"], pmeta[x]["src_xmin"])):
        if b not in clusters:
            continue
        cv = clusters[b]; pr = pmeta[b]
        print(f"  {b:16s} row={pr['row_y']:5.1f} 下游x≥{pr['via_minx']:6.2f} "
              f"P=({cv['P'][0]:.2f},{cv['P'][1]:.2f}) "
              f"N=({cv['N'][0]:.2f},{cv['N'][1]:.2f})")
    out = {"mode": mode,
           "separator": {"y": BAND_Y, "up_max_y": UP_MAX_Y, "lo_min_y": LO_MIN_Y,
                          "pad_crossing": len(separator_scan(geo))},
           "clusters": {b: {"P": list(clusters[b]["P"]), "N": list(clusters[b]["N"])}
                        for b in clusters},
           "routes": {n: [list(pt) for pt in poly] for n, poly in routes.items()},
           "margins": {k: round(v, 4) for k, v in margin.items()},
           "band_up": {b: {"P": list(bands["up"][b]["P"]), "N": list(bands["up"][b]["N"])}
                       for b in (bands["up"] or {})},
           "band_lo": {b: {"P": list(bands["lo"][b]["P"]), "N": list(bands["lo"][b]["N"])}
                       for b in (bands["lo"] or {})}}
    path = os.path.join(HERE, "mcio_q2_solution.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    print(f"\n构造已存 {path}（可复算）")

if __name__ == "__main__":
    sys.exit(main())
