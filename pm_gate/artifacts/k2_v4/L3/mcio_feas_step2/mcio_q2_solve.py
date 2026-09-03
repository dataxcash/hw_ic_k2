#!/usr/bin/env python3
"""
mcio_q2_solve.py — K2 MCIO Q2 核心求解：走廊矩形内 16 线无交叉扇出可行性
（A* 顺序布线 + 精确几何验证，输出确定结论与全部 margin）

口径（与任务/v17/Oracle Q1 一致，勿翻案）：
  - 上排 8 源自走廊顶边 y=58.05 下潜（DN0-3），下排 8 源自底边 y=67.75 上浮（DN4-7）
  - via keepout r=0.275；via 中心距 pad 铜 ≥0.475；P/N via 距 ∈[0.55,2.0]
  - 异对 via 中心距 ≥1.225（0.35 铜径 + 0.875 对间铜净空）
  - 对级下游界：cluster x ≥ 该对自身 MCIO pad +x 铜边 +0.475（逐对 stagger）
  - 线宽 0.205；异对中心线距 ≥1.08；同对 P/N 中心线距 ≥0.38（布线时按 0.6 生效）
  - 布线域 = 走廊 + 墙后条；障碍 = 真板 pad（扩张）+ 已布线（扩张净空）

用法: python3 mcio_q2_solve.py [mode]
  mode=single    仅上排 DN0-3（快验证）   mode=all  (default) 16 线全量
"""
from __future__ import annotations
import sys, math, heapq, json, os, random
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/_shared")
from eda_core.drc_rules import BoardParser

BOARD = "/home/fila/jqdDev_2025/ic_hw/k2/k2_v4.kicad_pcb"
HERE  = os.path.dirname(os.path.abspath(__file__))

VIA_OCC, VR = 0.55, 0.275
VIA_CU_R = 0.175
REQ      = 0.475
INTER_CU = 0.875
PN_LO, PN_HI = 0.55, 2.0
TR_W     = 0.205
DIFF_SEP = TR_W + INTER_CU   # 1.08
PAIR_SEP = 0.60              # P/N 同对线中心距（布线用；≥0.38 即可，取裕量）
PAD_LN   = 0.35              # 线中心线距 pad 铜（保守：0.205/2+0.25）
VIA_PN_X = 0.55              # P/N via 同簇 x 相同、y 差 pn_dy
COR_Y0, COR_Y1 = 58.05, 67.75
VIA_Y0, VIA_Y1 = COR_Y0+REQ, COR_Y1-REQ      # 58.525 / 67.275
STEP = 0.05

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

def seg_dist(a, b, c, d):
    return min(pt_seg_dist(a, c, d), pt_seg_dist(b, c, d),
               pt_seg_dist(c, a, b), pt_seg_dist(d, a, b))

def rect_dist(px, py, r):
    x0, y0, x1, y1 = r
    return math.hypot(max(x0-px, 0, px-x1), max(y0-py, 0, py-y1))

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

# ─────────────────────────────────────────────────────────────
# A* 顺序布线器（走廊域内，障碍=pad+已布线）
# ─────────────────────────────────────────────────────────────
class Router:
    def __init__(self, geo, xmin=74.6, xmax=None, ymin=57.6, ymax=68.4):
        self.geo = geo
        self.x0, self.y0 = xmin, ymin
        self.x1 = xmax if xmax is not None else geo["u3_left"] - 0.2
        self.y1 = ymax
        self.nx = int((self.x1-self.x0)/STEP)+1
        self.ny = int((self.y1-self.y0)/STEP)+1
        self.pad_map = [[-1]*self.ny for _ in range(self.nx)]  # -1 空; ref index
        # pad → 网格占用（pad 本体扩张 pad_clear 处理在 route 时做）
        self.placed = []   # list of dict(netname, pair, poly, sep)

    def _idx(self, x, y):
        ix = int(round((x-self.x0)/STEP)); iy = int(round((y-self.y0)/STEP))
        if ix < 0 or iy < 0 or ix >= self.nx or iy >= self.ny:
            return None
        return ix, iy

    def _blocked(self, ix, iy, mypair, mynet, pad_margin, line_clear):
        """(ix,iy) 中心点是否被 pad（扩张 pad_margin）或异网已布线（扩张）阻挡。
        自己的源 pad（同 net）豁免——线从自身 pad 出发允许贴接。"""
        px = self.x0 + ix*STEP; py = self.y0 + iy*STEP
        for p in self.geo["all_pads"]:
            if p.net == mynet:      # 自身 pad（同 net 铜）不视为障碍
                continue
            x, y = p.pos; w, h = p.size
            r = (x-w/2-pad_margin, y-h/2-pad_margin, x+w/2+pad_margin, y+h/2+pad_margin)
            if r[0] <= px <= r[2] and r[1] <= py <= r[3]:
                return True
        for pl in self.placed:
            if pl["pair"] == mypair and pl["netname"] == mynet:
                continue
            need = PAIR_SEP if pl["pair"] == mypair else line_clear
            for (a, b) in zip(pl["poly"], pl["poly"][1:]):
                if pt_seg_dist((px, py), a, b) < need:
                    return True
        return False

    def route(self, start, goal, mypair, mynet, pad_margin=0.30,
              line_clear=DIFF_SEP):
        si = self._idx(*start); gi = self._idx(*goal)
        if si is None or gi is None:
            return None
        if self._blocked(*si, mypair, mynet, pad_margin, line_clear) or \
           self._blocked(*gi, mypair, mynet, pad_margin, line_clear):
            return None
        # A*，4 邻域（允许 x 方向前进为主）
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
                if self._blocked(nx_, ny_, mypair, mynet, pad_margin, line_clear):
                    continue
                ng = g + w
                if (nx_, ny_) not in gcost or ng < gcost[(nx_, ny_)]:
                    gcost[(nx_, ny_)] = ng
                    prev[(nx_, ny_)] = cur
                    heapq.heappush(open_h, (ng + heur((nx_, ny_), gi), ng,
                                            (nx_, ny_)))
        if not found:
            return None
        # 回溯
        path = [gi]
        while path[-1] != si:
            path.append(prev[path[-1]])
        path.reverse()
        # 折线（压缩共线）
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

# ─────────────────────────────────────────────────────────────
# 候选布局 + 布线
# ─────────────────────────────────────────────────────────────
def gen_clusters(pmeta, row, x_offsets, y_shift, pn_dy=0.7):
    """对某行(上/下)的 4 对生成 cluster via 坐标。
    返回 {pair: [(px,py),(nx,ny)]} 按该行 x 序。y 按 U3 序放到可行带。"""
    cl = {}
    for base in sorted([b for b in pmeta if pmeta[b]["row_y"] == row],
                       key=lambda b: pmeta[b]["src_xmin"]):
        pr = pmeta[base]
        xoff = x_offsets.get(base, 0.0)
        cx = pr["via_minx"] + xoff
        # P via y：贴近 u3_top(P 上) + y_shift，但收进 [VIA_Y0, VIA_Y1-pn_dy]
        yP = pr["u3_top"] + y_shift
        if yP < VIA_Y0: yP = VIA_Y0
        yN = yP + pn_dy
        if yN > VIA_Y1:
            yN = VIA_Y1; yP = yN - pn_dy
        cl[base] = {"P": (cx, yP), "N": (cx, yN), "meta": pr}
    return cl

def route_all(geo, nets, pmeta, clusters, mode):
    """逐个布线。先布线每组内浅→深（x 序）；行间：先上排后下排或反之。
    源点=pad 走廊侧边：上排 (sx,58.05)，下排 (sx,67.75)。"""
    r = Router(geo)
    order = []
    if mode == "single":
        for base in sorted([b for b in pmeta if pmeta[b]["row_y"] < 60.0],
                           key=lambda b: pmeta[b]["src_xmin"]):
            order.append(base)
    else:
        # 行序：上排全部再下排全部（各自内部 x 序）
        for row in (57.8, 68.0):
            for base in sorted([b for b in pmeta if pmeta[b]["row_y"] == row],
                               key=lambda b: pmeta[b]["src_xmin"]):
                order.append(base)
    routes = {}
    for base in order:
        pr = pmeta[base]
        top = pr["row_y"] < 60.0
        edge = COR_Y0 if top else COR_Y1
        for m in sorted(pr["nets"], key=lambda z: z["src_x"]):
            sx = m["src_x"]
            vx, vy = clusters[base][m["pol"]]
            start = (sx, edge)
            goal = (vx, vy)
            poly = r.route(start, goal, base, m["netname"])
            if poly is None:
                return None, base, m["netname"]
            routes[m["netname"]] = poly
            r.placed.append(dict(netname=m["netname"], pair=base, poly=poly))
    return routes, None, None

# ─────────────────────────────────────────────────────────────
# 精确全量验证
# ─────────────────────────────────────────────────────────────
def verify(geo, nets, pmeta, clusters, routes):
    vio = []
    margin = {"via_pad": 1e9, "pn": 1e9, "inter_via": 1e9, "line_cross": 1e9,
              "line_diff": 1e9, "line_pair": 1e9, "line_pad": 1e9,
              "down_x": 1e9}
    # via vs pad / 窗口 / 下游界 / P-N / 异对
    vias = {}
    for base, cv in clusters.items():
        for pol in ("P", "N"):
            for m in pmeta[base]["nets"]:
                if m["pol"] == pol:
                    vias[m["netname"]] = cv[pol]
    for n, (x, y) in vias.items():
        for p in geo["all_pads"]:
            px, py = p.pos; w, h = p.size
            d = rect_dist(x, y, (px-w/2, py-h/2, px+w/2, py+h/2))
            margin["via_pad"] = min(margin["via_pad"], d)
            if d < REQ - 1e-9:
                vio.append(f"via {n} 距 pad {d:.3f}<{REQ}")
        if not (VIA_Y0-1e-9 <= y <= VIA_Y1+1e-9):
            vio.append(f"via {n} y={y:.3f} 出窗口")
    for base, pr in pmeta.items():
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
    # 折线两两 + vs pad
    rn = list(routes)
    for i in range(len(rn)):
        for j in range(i+1, len(rn)):
            n1, n2 = rn[i], rn[j]
            same = nets[n1]["pair"] == nets[n2]["pair"]
            need = PAIR_SEP if same else DIFF_SEP
            dmin = 1e9
            for (a, b) in zip(routes[n1], routes[n1][1:]):
                for (c, d) in zip(routes[n2], routes[n2][1:]):
                    dmin = min(dmin, seg_dist(a, b, c, d))
            key = "line_pair" if same else "line_diff"
            margin[key] = min(margin[key], dmin)
            if dmin < need - 1e-6:
                vio.append(f"线 {n1}-{n2} 中心距 {dmin:.3f}<{need:.3f}"
                           + ("(同对)" if same else "(异对)"))
        # line vs pad（跳过自身 ref 源 pad）
        poly = routes[n1]
        myref = nets[n1]["ref"]
        for p in geo["all_pads"]:
            if p.footprint_ref == myref:
                continue
            px, py = p.pos; w, h = p.size
            r = (px-w/2, py-h/2, px+w/2, py+h/2)
            for (a, b) in zip(poly, poly[1:]):
                d = min(pt_seg_dist((r[0], r[1]), a, b),
                        pt_seg_dist((r[2], r[1]), a, b),
                        pt_seg_dist((r[2], r[3]), a, b),
                        pt_seg_dist((r[0], r[3]), a, b))
                margin["line_pad"] = min(margin["line_pad"], d)
                if d < PAD_LN - 1e-6:
                    vio.append(f"线 {n1} 距 {p.footprint_ref} pad {d:.3f}")
    return vio, margin

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    geo = load_geometry()
    nets = build_nets(geo)
    pmeta = pair_meta(nets)
    # 对级 stagger：x_offsets 让左对在走廊内、右对到墙后
    if mode == "single":
        rows = (57.8,)
    else:
        rows = (57.8, 68.0)
    best = None
    # 参数扫描：x 裕量 0..0.8 / y 上移量（让 P 尽量贴近 u3_top 但收进窗口）
    xo_list = [0.0, 0.2, 0.4, 0.6, 0.8]
    # 每对可单独 x 偏移（阶梯式）
    for xg in xo_list:
        for yshift in (-0.4, -0.2, 0.0, 0.2, 0.4):
            xo = {}
            # 依 x 序对做递增错列：k=0..3 -> base+xg*k 已含在 via_minx；这里再统一加
            for row in rows:
                bs = sorted([b for b in pmeta if pmeta[b]["row_y"] == row],
                            key=lambda b: pmeta[b]["src_xmin"])
                for k, base in enumerate(bs):
                    xo[base] = xg   # 统一错列量（增量搜索）
            clusters = gen_clusters(pmeta, None if mode=="all" else 57.8,
                                    xo, yshift)
            if mode == "single":
                clusters = {b: c for b, c in clusters.items()
                            if pmeta[b]["row_y"] == 57.8}
            routes, fnet, fpoly = route_all(geo, nets, pmeta, clusters, mode)
            if routes is None:
                continue
            vio, margin = verify(geo, nets, pmeta, clusters, routes)
            if not vio:
                best = (xo, yshift, clusters, routes, margin)
                print(f"✔ 找到无交叉布局 xg={xg} yshift={yshift} 违规=0")
                break
        if best:
            break
    if not best:
        print("扫描未找到全绿布局（有限参数族）；输出最接近候选的违规模式见下。")
        # 展示一次默认布局的违规明细，供下一轮调参
        xo = {b: 0.4 for b in pmeta}
        clusters = gen_clusters(pmeta, None if mode == "all" else 57.8, xo, 0.0)
        if mode == "single":
            clusters = {b: c for b, c in clusters.items()
                        if pmeta[b]["row_y"] == 57.8}
        routes, fnet, fpoly = route_all(geo, nets, pmeta, clusters, mode)
        if routes is None:
            print(f"布线失败: {fnet} {fpoly}")
        else:
            vio, margin = verify(geo, nets, pmeta, clusters, routes)
            print(f"违规 {len(vio)} 条，最小 margin:",
                  {k: round(v, 3) for k, v in margin.items()})
            for v in vio[:30]:
                print("  ✗", v)
        return
    _, _, clusters, routes, margin = best
    print("\n==== 全绿布局（构造性证明） ====")
    print("via 坐标与最小 margin：")
    print("  via↔pad:", round(margin["via_pad"], 3), "| P/N:",
          round(margin["pn"], 3), "| 异对via:", round(margin["inter_via"], 3))
    print("  异对线:", round(margin["line_diff"], 3), "| 同对线:",
          round(margin["line_pair"], 3), "| 线↔pad:", round(margin["line_pad"], 3))
    print("\n各对 cluster（x, yP, yN）与下游界：")
    for base in sorted(pmeta, key=lambda b: (pmeta[b]["row_y"],
                                             pmeta[b]["src_xmin"])):
        cv = clusters.get(base)
        if not cv:
            continue
        pr = pmeta[base]
        print(f"  {base:13s} row={pr['row_y']:5.1f} 下游x≥{pr['via_minx']:6.2f} "
              f"P=({cv['P'][0]:.2f},{cv['P'][1]:.2f}) "
              f"N=({cv['N'][0]:.2f},{cv['N'][1]:.2f})")
    # 保存构造供报告引用
    out = {"clusters": {b: {"P": cv["P"], "N": cv["N"]}
                        for b, cv in clusters.items()},
           "routes": {n: poly for n, poly in routes.items()},
           "margins": margin}
    with open(os.path.join(HERE, "mcio_q2_solution.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("\n构造已存 mcio_q2_solution.json（可复算）")

if __name__ == "__main__":
    main()
