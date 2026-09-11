#!/usr/bin/env python3
"""CO-10 只读探针：CO-09 安全 hop 拓扑 + D2/D3 全 pad 障碍场的**顺序单遍**落位复算。

用途：在**不改冻结四源、不改 canonical 图纸**的前提下，独立复算
  (1) CO-09 §3 安全 hop 层角色（escape=In2/B、lane=In6、stub=In2/In6）能否一次求解；
  (2) CO-09 §4ter D3 落列规则（lx=conn pad x、ll=行间中缝）在西侧是否可行；
  (3) 剩余不可落位页的精确归因（via-via / via-track / track-track / pad 冲突）。
零搜索：候选来自冻结 F-13 pair 域 + 冻结 verdict；单遍确定性 argmin；无回溯。
CLI: --rule {d3,fan,co10}  --order {engine,fewest,laneidx}  --out PATH  --verbose
env（只读旋钮，CO-11 实测用；默认=原行为）:
  CO10_PAIR=<file>      pair 域文件名（默认 v1_4；CO-11 用 v1_5=pad 场合法域）
  CO10_STEP=<mm>        全局 lane STEP
  CO10_WDELTA=<mm>      仅西侧 lane 块整体下移
  CO10_WSTEP/CO10_WLO   仅西侧 lane 块重派生（lane_y=WLO+idx*WSTEP）
  CO10_FANDX_J3/_J4=<mm> 西侧 connector landing lx 偏置
"""
from __future__ import annotations
import argparse, hashlib, json, math, sys
from pathlib import Path
import importlib.util
import numpy as np

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
SPEC = K2 / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2"
_s = importlib.util.spec_from_file_location("w3", str(K2 / "tools/p3_v57_w3_constructive.py"))
W = importlib.util.module_from_spec(_s); _s.loader.exec_module(W)

J = {k: json.load(v.open()) for k, v in W.F.items() if v.suffix == ".json"}
FACTS = W.page_facts(J["manifest"], J["lane_frame"])
FRS = W.frames_of(FACTS)
W.STEP = float(__import__("os").environ.get("CO10_STEP", W.STEP))
LANES = W.r2_lanes(FRS, FACTS)
_WD = float(__import__("os").environ.get("CO10_WDELTA", "0"))
if _WD:
    for _p, _v in LANES.items():
        if FACTS[_p]["corridor"] == "WEST_MCIO_TO_CHIP":
            _v["lane_y"] = W.fp(_v["lane_y"] - _WD)
if __import__("os").environ.get("CO10_WORDER") == "upfirst":
    _west = sorted([p for p in LANES if FACTS[p]["corridor"] == "WEST_MCIO_TO_CHIP"],
                   key=lambda p: (FACTS[p]["band"] == "dn", LANES[p]["lane_index"]))
    for _r, _p in enumerate(_west):
        LANES[_p]["lane_y"] = W.fp(33.3 + _r * 1.46)
_WB = __import__("os").environ.get("CO10_WBLOCK", "")
if _WB:
    _lo1, _st1, _n1, _lo2, _st2, _n2 = (float(v) for v in _WB.split(","))
    for _p, _v in LANES.items():
        if FACTS[_p]["corridor"] == "WEST_MCIO_TO_CHIP":
            _k = _v["lane_index"]
            _v["lane_y"] = W.fp(_lo1 + _k * _st1) if _k < _n1 else W.fp(_lo2 + (_k - _n1) * _st2)
_WS = float(__import__("os").environ.get("CO10_WSTEP", "0"))
_WL = float(__import__("os").environ.get("CO10_WLO", "33.3"))
if _WS:
    for _p, _v in LANES.items():
        if FACTS[_p]["corridor"] == "WEST_MCIO_TO_CHIP":
            _v["lane_y"] = W.fp(_WL + _v["lane_index"] * _WS)
PADF = json.loads((SPEC / "m13_v57_co09_pad_field.json").read_text())
PAIR_ART = __import__("os").environ.get("CO10_PAIR", "m13_v57_f13_r1_pair_coupling_v1_4.json")
PAIR_DOMAIN = json.loads((SPEC / PAIR_ART).read_text())["pages"]

VIA_R, CLEAR, ESC, WID = 0.175, 0.175, 0.075, 0.205
YWIN = 0.7           # via1 只允许落在 pad_y ± 0.7 内（保 up/dn band 隔离）
TT = WID + CLEAR; TT_E = WID + ESC
VT = VIA_R + CLEAR + WID / 2; VT_E = VIA_R + ESC + WID / 2
VV = 2 * VIA_R + CLEAR; TOL = 1e-9
LAYERS = ["B.Cu", "In2.Cu", "In6.Cu", "F.Cu"]; LI = {l: i for i, l in enumerate(LAYERS)}

_p = PADF["pads"]
PXA = np.array([q["x"] for q in _p]); PYA = np.array([q["y"] for q in _p])
PHX = np.array([q["sx"] / 2 for q in _p]); PHY = np.array([q["sy"] / 2 for q in _p])
PRA = np.array([max(q["sx"], q["sy"]) / 2 for q in _p])
PCIRC = np.array([q["shape"] == 0 for q in _p]); PKEY = [(q["ref"], q["pad"]) for q in _p]

ESC_MAP = {("EAST_CHIP_TO_J2", "dn"): "In2.Cu", ("EAST_CHIP_TO_J2", "up"): "B.Cu",
           ("WEST_MCIO_TO_CHIP", "up"): "In2.Cu", ("WEST_MCIO_TO_CHIP", "dn"): "B.Cu"}
GAP = {"J3": 44.5, "J4": 62.7}
J2L, J2R, J2_IN, J2_OUT, J2P = 131.65, 136.0, 132.65, 135.0, 0.525


POL_OFF = 0.25            # L2 参数：对内 lane y 偏移 >= vt(0.4525)/2；0.19->0.25（原 0.38 < 0.4525）
# CO-15 只读旋钮（默认 "" = 原行为）：POLMODE="lx" ⇒ 方向感知 P/N lane 排序。
# 目的：当 stub 层 == lane 层（In6）时，竖直 stub 必穿过对面极性水平 lane（CO-11 §13.2 UP6/UP7 自叉）。
# 规则（闭式，由几何推导）：stub 朝上（ll>lane_y）⇒ landing lx 较大者取上层 lane（+POL_OFF）、较小者取下（-POL_OFF）；
# 朝下（ll<lane_y）反之。仅对 WEST_MCIO_TO_CHIP 生效（stub 全 In2 时该规则不影响可行性，保留一致性）。
POLMODE = __import__("os").environ.get("CO10_POLMODE", "")


def pol_off(f, pol):
    if POLMODE == "lx" and f["corridor"] == "WEST_MCIO_TO_CHIP":
        ll = FAN_Y[row_group(f)]
        ly = LANES[f["page_id"]]["lane_y"]
        big = "P" if f["conn_pad"]["P"][0] > f["conn_pad"]["N"][0] else "N"
        if ll > ly:
            return POL_OFF if pol == big else -POL_OFF
        return -POL_OFF if pol == big else POL_OFF
    d = f["pad"]["N"][1] - f["pad"]["P"][1]
    base = -POL_OFF if d > 0 else POL_OFF
    return base if pol == "P" else -base


def esc_layer(f): return ESC_MAP[(f["corridor"], f["band"])]


def row_lower(f):
    return min(f["conn_pad"]["P"][1], f["conn_pad"]["N"][1]) >= GAP[f["conn_ref"]]


# CO-10 §3.3: 西侧 4 行组 stub 2-着色（按 y 区间，与 band 无关）
#   G0(J3 上排 43.25)->In2 ; G1(J3 下排 45.75)->In6 ; G2(J4 上排 61.45)->In2 ; G3(J4 下排 63.95)->In6
GS_IN2 = {("J3", "U"): True, ("J3", "L"): False, ("J4", "U"): True, ("J4", "L"): False}
_ST = __import__("os").environ.get("CO10_STUB", "")
if _ST == "all":
    for _g in GS_IN2: GS_IN2[_g] = True
elif _ST:
    for _t in _ST.split(","):
        if len(_t) == 3: GS_IN2[(_t[:2], _t[2])] = True


def row_group(f):
    mid = GAP[f["conn_ref"]]
    return (f["conn_ref"], "U" if min(f["conn_pad"]["P"][1], f["conn_pad"]["N"][1]) < mid else "L")


def stub_layer(f):
    if f["conn_ref"] == "J2":
        return "In2.Cu"
    return "In2.Cu" if GS_IN2[row_group(f)] else "In6.Cu"


def r3_build(rule):
    r3 = W.r3_place(J["r3_gaps"], LANES, "y", J.get("r3_base"))
    A = dict(r3["assignment"])
    j2k = [k for k, a in A.items() if a["ref"] == "J2" and a.get("page") in LANES and a.get("kind") == "data"]
    pgs = sorted({A[k]["page"] for k in j2k}, key=lambda p: LANES[p]["lane_index"])
    rank = {p: i for i, p in enumerate(pgs)}
    for k in j2k:
        a = A[k]; r = rank[a["page"]]
        lx = W.fp(J2L - J2P * r) if abs(a["pad_x"] - J2_IN) < 1e-6 else W.fp(J2R + J2P * r)
        A[k] = dict(a, column_x=lx, landing=[lx, a["landing"][1]])
    for k, a in list(A.items()):
        if a["ref"] in ("J3", "J4"):
            mid = GAP[a["ref"]]
            if rule == "d3":            # CO-09 §4ter
                lx, ll = a["pad_x"], (mid - 0.35 if a["pad_y"] < mid else mid + 0.35)
            else:                       # CO-10: 共享 8 列 fan + 每 band 独立 breakout y
                g = (a["ref"], "U" if a["pad_y"] < mid else "L")
                lx = W.fp(a["pad_x"] - 0.3 + FAN_DX[g]); ll = FAN_Y[g]
            A[k] = dict(a, column_x=lx, landing=[lx, W.fp(ll)])
    if rule != "d3":
        _lx_separate(A)
    return {"assignment": A, "certificates": r3["certificates"]}


def _stub_layer_of(a):
    if a["ref"] == "J2":
        return "In2.Cu"
    mid = GAP[a["ref"]]
    g = (a["ref"], "U" if a["pad_y"] < mid else "L")
    return "In2.Cu" if GS_IN2[g] else "In6.Cu"


def _lx_separate(A):
    """CO-11 §13：connector 侧 lx 前缀分配（零搜索单遍，**按页整体偏移**）。
    - P/N 同 δ 平移 => 保持 pad 相对次序 => 不产生 land 段互叉（§12 修正项 a）。
    - δ 网格 0.6mm（=pad pitch，落另一中缝列）=> 页间 lx 净距 >=0.525。
    同层 stub/land 的 y 区间重叠时，要求页间 lx >= VV(0.525)。"""
    ents = []
    for k, a in A.items():
        if a["ref"] not in ("J3", "J4"):
            continue
        page = a.get("page")
        if page not in LANES:
            continue
        ents.append({"key": k, "a": a, "page": page, "S": _stub_layer_of(a)})
    bypage = {}
    for e in ents:
        bypage.setdefault(e["page"], []).append(e)
    pages = sorted(bypage, key=lambda q: (bypage[q][0]["S"], round(LANES[q]["lane_y"], 3), q))
    placed = []
    for pg in pages:
        grp = bypage[pg]
        S = grp[0]["S"]
        ly = LANES[pg]["lane_y"]
        lo = min(min(ly, g["a"]["landing"][1]) for g in grp)
        hi = max(max(ly, g["a"]["landing"][1]) for g in grp)
        best = None
        for d in (0.0, 0.6, -0.6, 1.2, -1.2, 1.8, -1.8, 2.4, -2.4, 3.0, -3.0, 3.6, -3.6):
            xs = [g["a"]["column_x"] + d for g in grp]
            okd = True
            for q in placed:
                if q["S"] != S:
                    continue
                if lo >= q["hi"] - VV or hi <= q["lo"] + VV:
                    continue
                for x in xs:
                    if abs(x - q["lx"]) < VV - TOL:
                        okd = False; break
                if not okd:
                    break
            if okd:
                best = d; break
        d = best if best is not None else 0.0
        for g in grp:
            g["a"]["column_x"] = W.fp(g["a"]["column_x"] + d)
            g["a"]["landing"] = [W.fp(g["a"]["column_x"]), g["a"]["landing"][1]]
            placed.append({"S": S, "lx": g["a"]["column_x"], "lo": lo, "hi": hi})


FAN_Y = {("J3", "U"): 42.0, ("J3", "L"): 44.2, ("J4", "U"): 60.2, ("J4", "L"): 65.0}
_FY = __import__("os").environ.get("CO10_FANY_J3", "")
if _FY:
    _u, _l = (float(v) for v in _FY.split(","))
    FAN_Y[("J3", "U")] = _u; FAN_Y[("J3", "L")] = _l
FAN_DX = {("J3", "U"): 0.0, ("J3", "L"): 0.0, ("J4", "U"): 0.0, ("J4", "L"): 0.0}
_FXG = __import__("os").environ.get("CO10_FANDX", "")
if _FXG:
    for _t in _FXG.split(","):
        _k, _val = _t.split(":"); FAN_DX[(_k[:2], _k[2])] = float(_val)
_FX = float(__import__("os").environ.get("CO10_FANDX_J4", "0"))
_FX3 = float(__import__("os").environ.get("CO10_FANDX_J3", "0"))
if _FX or _FX3:
    for _g in list(FAN_DX):
        if _g[0] == "J4": FAN_DX[_g] += _FX
        if _g[0] == "J3": FAN_DX[_g] += _FX3


def y_bias(f):
    """同 band 内不同 connector 的 escape 竖段在 y 上错开 0.6：
    west-up  J3(+pad_y-0.3) / J4(+pad_y+0.3) => 竖段 y 区间互斥，解耦其 x 分配。"""
    if f["corridor"] == "WEST_MCIO_TO_CHIP" and f["band"] == "up":
        return -0.3 if f["conn_ref"] == "J3" else 0.3
    return 0.0


def land_meta(f):
    out = {}
    for pol in ("P", "N"):
        a = R3["assignment"].get(f["conn_ref"] + "|" + f["nets"][pol])
        out[pol] = None if a is None else (float(a["column_x"]), float(a["landing"][1]))
    return out


def _cross_seg(a, b, c, d):
    """真交叉（proper intersection）判定（与引擎 count_crossings 同语义）。"""
    def o(p, q, r):
        v = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
        return 0 if abs(v) < 1e-12 else (1 if v > 0 else 2)
    def on(p, q, r):
        return (min(p[0], r[0]) - 1e-9 <= q[0] <= max(p[0], r[0]) + 1e-9 and
                min(p[1], r[1]) - 1e-9 <= q[1] <= max(p[1], r[1]) + 1e-9)
    o1, o2, o3, o4 = o(a, b, c), o(a, b, d), o(c, d, a), o(c, d, b)
    if o1 != o2 and o3 != o4:
        return 1
    return 1 if ((o1 == 0 and on(a, c, b)) or (o2 == 0 and on(a, d, b))
                 or (o3 == 0 and on(c, a, d)) or (o4 == 0 and on(c, b, d))) else 0


def pt_seg(px_, py_, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1; L2 = dx * dx + dy * dy
    L2 = np.where(L2 < 1e-12, 1.0, L2)
    t = np.clip(((px_ - x1) * dx + (py_ - y1) * dy) / L2, 0, 1)
    return np.sqrt((px_ - (x1 + t * dx)) ** 2 + (py_ - (y1 + t * dy)) ** 2)


def seg_seg(a, b, X1, Y1, X2, Y2):
    return np.minimum(np.minimum(pt_seg(a[0], a[1], X1, Y1, X2, Y2), pt_seg(b[0], b[1], X1, Y1, X2, Y2)),
                      np.minimum(pt_seg(X1, Y1, a[0], a[1], b[0], b[1]), pt_seg(X2, Y2, a[0], a[1], b[0], b[1])))


def pad_seg_edge(a, b):
    ax, ay = a; bx, by = b; dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
    L2 = np.where(L2 < 1e-12, 1.0, L2)
    t = np.clip(((PXA - ax) * dx + (PYA - ay) * dy) / L2, 0, 1)
    qx, qy = ax + t * dx, ay + t * dy
    ex = np.maximum(np.abs(qx - PXA) - PHX, 0.0); ey = np.maximum(np.abs(qy - PYA) - PHY, 0.0)
    return np.where(PCIRC, np.maximum(np.sqrt((qx - PXA) ** 2 + (qy - PYA) ** 2) - PRA, 0.0),
                    np.sqrt(ex * ex + ey * ey))


def pad_via_edge(x, y):
    ex = np.maximum(np.abs(x - PXA) - PHX, 0.0); ey = np.maximum(np.abs(y - PYA) - PHY, 0.0)
    return np.where(PCIRC, np.maximum(np.sqrt((x - PXA) ** 2 + (y - PYA) ** 2) - PRA, 0.0),
                    np.sqrt(ex * ex + ey * ey))


class Store:
    def __init__(self):
        self.vx = np.zeros(0); self.vy = np.zeros(0); self.vm = np.zeros(0, dtype=int)
        self.S = {l: np.zeros((0, 4)) for l in LAYERS}; self.SP = {l: np.zeros(0, dtype=bool) for l in LAYERS}
        self.vlab = []; self.SLAB = {l: [] for l in LAYERS}

    def add(self, vias, segs, pid="?"):
        for (x, y, pol, lays) in vias:
            self.vlab.append(pid + "." + pol)
            m = 0
            for l in lays: m |= 1 << LI[l]
            self.vx = np.append(self.vx, x); self.vy = np.append(self.vy, y); self.vm = np.append(self.vm, m)
        for (lay, x1, y1, x2, y2, pa, pol) in segs:
            self.S[lay] = np.vstack([self.S[lay], [x1, y1, x2, y2]])
            self.SP[lay] = np.append(self.SP[lay], pa); self.SLAB[lay].append(pid + "." + pol)


def build(f, px, py, nx, ny):
    E = esc_layer(f); S = stub_layer(f); lm = land_meta(f)
    if lm["P"] is None or lm["N"] is None:
        return None
    vias, segs, own = [], [], []
    for pol, vx, vy in (("P", px, py), ("N", nx, ny)):
        lx, ll = lm[pol]
        ly = W.fp(LANES[f["page_id"]]["lane_y"] + pol_off(f, pol))
        own += [(round(f["pad"][pol][0], 3), round(f["pad"][pol][1], 3)),
                (round(f["conn_pad"][pol][0], 3), round(f["conn_pad"][pol][1], 3))]
        vias.append((vx, vy, pol, ("F.Cu", "In2.Cu")))
        if E == "B.Cu":
            vias.append((vx, vy, pol, ("In2.Cu", "In6.Cu")))
            vias.append((vx, vy, pol, ("In6.Cu", "B.Cu")))
        vias.append((vx, ly, pol, (E, "In6.Cu")))
        if S == "In2.Cu":                                   # lane(In6) -> drop -> In2 stub -> land
            vias.append((lx, ly, pol, ("In6.Cu", "In2.Cu")))
        else:                                               # lane(In6) -> In6 stub -> land stack
            vias.append((lx, ll, pol, ("In6.Cu", "In2.Cu")))
        vias.append((lx, ll, pol, ("In2.Cu", "F.Cu")))
        segs.append(("F.Cu", f["pad"][pol][0], f["pad"][pol][1], vx, vy, True, pol))
        segs.append((E, vx, vy, vx, ly, False, pol))
        segs.append(("In6.Cu", vx, ly, lx, ly, False, pol))
        segs.append((S, lx, ly, lx, ll, False, pol))
        segs.append(("F.Cu", lx, ll, f["conn_pad"][pol][0], f["conn_pad"][pol][1], True, pol))
    return vias, segs, np.array(own)


def check(vias, segs, own, st):
    for i in range(len(vias)):
        for j in range(i + 1, len(vias)):
            if vias[i][2] == vias[j][2]: continue
            if math.hypot(vias[i][0] - vias[j][0], vias[i][1] - vias[j][1]) < VV - TOL:
                return ("vv_intra", vias[i][:3], vias[j][:3])
    nv = len(st.vx)
    if nv:
        for (x, y, pol, lays) in vias:
            m = 0
            for l in lays: m |= 1 << LI[l]
            d = np.hypot(st.vx - x, st.vy - y)
            bad = np.nonzero((d < VV - TOL) & ((st.vm & m) != 0))[0]
            if len(bad):
                return ("vv_placed", (x, y, pol), st.vlab[int(bad[0])], round(float(d[bad[0]]), 3))
    for (x, y, pol, lays) in vias:
        for l in lays:
            X = st.S[l]
            if not len(X): continue
            d = pt_seg(x, y, X[:, 0], X[:, 1], X[:, 2], X[:, 3])
            thr = np.where(st.SP[l], VT_E, VT)
            bad = np.nonzero(d < thr - TOL)[0]
            if len(bad):
                return ("vt_placed", (x, y, pol, l), st.SLAB[l][int(bad[0])], round(float(d[bad[0]]), 4))
    if nv:
        for (lay, x1, y1, x2, y2, pa, pol) in segs:
            d = pt_seg(st.vx, st.vy, x1, y1, x2, y2)
            bad = np.nonzero((d < (VT_E if pa else VT) - TOL) & ((st.vm & (1 << LI[lay])) != 0))[0]
            if len(bad):
                return ("vt2_placed", (lay, x1, y1, x2, y2, pol), st.vlab[int(bad[0])], round(float(d[bad[0]]), 4))
    for (x, y, pol, lays) in vias:                      # candidate via vs candidate tracks
        for (lay, x1, y1, x2, y2, pa, pol2) in segs:
            if pol2 == pol or lay not in lays: continue
            if pt_seg(x, y, np.array([x1]), np.array([y1]), np.array([x2]), np.array([y2]))[0] < (VT_E if pa else VT) - TOL:
                return ("vt_intra", (x, y, pol, lay))
    for (lay, x1, y1, x2, y2, pa, pol) in segs:    # candidate seg vs candidate seg（同页异极性真交叉）
        for (lay2, u1, v1, u2, v2, pa2, pol2) in segs:
            if lay != lay2 or pol == pol2:
                continue
            if (_cross_seg((x1, y1), (x2, y2), (u1, v1), (u2, v2))):
                return ("cross_intra", (lay, x1, y1, x2, y2, pol), (lay2, u1, v1, u2, v2, pol2))
    for (lay, x1, y1, x2, y2, pa, pol) in segs:
        X = st.S[lay]
        if not len(X): continue
        d = seg_seg((x1, y1), (x2, y2), X[:, 0], X[:, 1], X[:, 2], X[:, 3])
        bad = np.nonzero(d < np.where(st.SP[lay] | pa, TT_E, TT) - TOL)[0]
        if len(bad):
            return ("tt_placed", (lay, x1, y1, x2, y2, pol), st.SLAB[lay][int(bad[0])], round(float(d[bad[0]]), 4))
    for (lay, x1, y1, x2, y2, pa, pol) in segs:
        if lay != "F.Cu": continue
        d = pad_seg_edge((x1, y1), (x2, y2))
        for idx in np.nonzero(d < ESC - TOL)[0]:
            if len(own) and min(abs(own[:, 0] - PXA[idx]) + abs(own[:, 1] - PYA[idx])) < 0.01: continue
            return ("pad_seg", (x1, y1, x2, y2), PKEY[idx], round(float(d[idx]), 4))
    for (x, y, pol, lays) in vias:
        d = pad_via_edge(x, y)
        for idx in np.nonzero(d < ESC - TOL)[0]:
            if len(own) and min(abs(own[:, 0] - PXA[idx]) + abs(own[:, 1] - PYA[idx])) < 0.01: continue
            return ("pad_via", (x, y, pol), PKEY[idx], round(float(d[idx]), 4))
    return None


def geom_rec(b, f):
    """(vias, segs) -> 可序列化几何（独立复核用）。"""
    vias, segs = b[0], b[1]
    return {"pad": {p: [f["pad"][p][0], f["pad"][p][1]] for p in ("P", "N")},
            "conn": {p: [f["conn_pad"][p][0], f["conn_pad"][p][1]] for p in ("P", "N")},
            "vias": [[float(x), float(y), pol, list(lays)] for (x, y, pol, lays) in vias],
            "segs": [[lay, float(x1), float(y1), float(x2), float(y2), bool(pa), pol]
                     for (lay, x1, y1, x2, y2, pa, pol) in segs]}


def band_key(f): return (f["corridor"], f["band"])


def alloc_x(verbose=False):
    """每 (corridor,band) 16 网的 escape-vertical x 前缀递推（>=0.46），
    x 取自该页 verdict 的合法 escape 窗口 [pad_x-0.35, pad_x+0.35]。"""
    VER = json.loads((SPEC / "m13_v57_s1_r1_via_verdict_r2.json").read_text())["pages"]
    need_avoid = {}                                        # west-up 长竖段须避开 east-up via1 x
    for pid, f in FACTS.items():
        if f["corridor"] == "EAST_CHIP_TO_J2" and f["band"] == "up":
            pass
    out = {}
    groups = {}
    for pid, f in FACTS.items():
        for pol in ("P", "N"):
            groups.setdefault((f["corridor"], f["band"]), []).append((f, pol))
    for key, items in groups.items():
        items.sort(key=lambda t: (t[0]["pad"][t[1]][0], t[0]["page_id"], t[1]))
        boxes = []
        for f, pol in items:
            cands = VER[f["page_id"]][pol]["cands"]
            xs = sorted({round(float(c[0]), 3) for c in cands})
            pad_x = f["pad"][pol][0]
            lo, hi = pad_x - 0.35, pad_x + 0.35
            ok = [x for x in xs if lo - TOL <= x <= hi + TOL] or [min(xs, key=lambda x: abs(x - pad_x))]
            tgt = pad_x - 0.3
            if boxes:
                tgt = max(tgt, boxes[-1] + 0.5)
            x = min(ok, key=lambda v: (abs(v - tgt), v))
            boxes.append(x)
            out[(f["page_id"], pol)] = x
    return out


def alloc_closed_form():
    """CO-11 §8.5：chip 区 via1 闭式目标（**逐页独立**，与落位顺序无关）。
    up band 目标 y 取 pad_y ∓ 0.4（下探至 dn 带之下），dn band 取 pad_y；x 取 pad_x（同页 P/N 分离由 pair 域保证）。
    选择 = pair 域中到目标最近的行（单遍 argmin，无搜索）。"""
    out = {}
    ysub = {("WEST_MCIO_TO_CHIP", "up"): ("le", 50.44), ("WEST_MCIO_TO_CHIP", "dn"): ("ge", 50.973),
            ("EAST_CHIP_TO_J2", "up"): ("le", 55.895), ("EAST_CHIP_TO_J2", "dn"): ("ge", 56.42)}
    for pid, f in FACTS.items():
        key = (f["corridor"], f["band"])
        mode, yv = ysub[key]
        for pol in ("P", "N"):
            py = f["pad"][pol][1]
            ty = py - 0.4 if f["band"] == "up" else py + 0.0
            ty = min(max(ty, py - YWIN), py + YWIN)
            ty = min(ty, yv) if mode == "le" else max(ty, yv)
            out[(pid, pol)] = (f["pad"][pol][0], ty)
    return out


def probe(rule="d3", order="engine", verbose=False):
    global R3
    R3 = r3_build(rule)
    if order == "fewest":
        seq = sorted(FACTS, key=lambda p: (len(PAIR_DOMAIN[p]["pair_rows"]), p))
    elif order == "laneidx":
        seq = sorted(FACTS, key=lambda p: LANES[p]["lane_index"])
    elif order == "rev":
        seq = sorted(FACTS, key=lambda p: (FACTS[p]["corridor"], FACTS[p]["conn_ref"], FACTS[p]["band"], p), reverse=True)
    else:
        seq = sorted(FACTS, key=lambda p: (FACTS[p]["corridor"], FACTS[p]["conn_ref"], FACTS[p]["band"], p))
    st = Store(); placed = {}; failed = {}; GEOM = {}
    global ALLOC
    ALLOC = alloc_closed_form() if (rule != "co10" and __import__("os").environ.get("CO10_ALLOC")) else None
    XALLOC = alloc_x() if rule == "co10" else {}
    VER = json.loads((SPEC / "m13_v57_s1_r1_via_verdict_r2.json").read_text())["pages"] if rule == "co10" else {}
    for pid in seq:
        f = FACTS[pid]
        if rule == "co10":
            cand = []
            for pol in ("P", "N"):
                xa = XALLOC[(pid, pol)]
                pts = [c for c in VER[pid][pol]["cands"] if abs(float(c[0]) - xa) < 0.026]
                pts.sort(key=lambda c: (abs(float(c[1]) - f["pad"][pol][1]), float(c[1])))
                cand.append((pol, pts))
            hit = None; reasons = {}
            for ip in range(len(cand[0][1])):
                for jn in range(len(cand[1][1])):
                    px, py = float(cand[0][1][ip][0]), float(cand[0][1][ip][1])
                    nx, ny = float(cand[1][1][jn][0]), float(cand[1][1][jn][1])
                    if math.hypot(px - nx, py - ny) < VV - TOL: continue
                    b = build(f, px, py, nx, ny)
                    if b is None: continue
                    err = check(*b, st)
                    if err is None:
                        hit = (px, py, nx, ny, b); break
                    reasons.setdefault(err[0], err)
                if hit: break
            if hit is None:
                failed[pid] = {"rule": "co10", "xalloc": [XALLOC[(pid, "P")], XALLOC[(pid, "N")]],
                               "reasons": {k: str(v)[:160] for k, v in reasons.items()}}
                if verbose: print("FAIL", pid, failed[pid]["reasons"])
                continue
            px, py, nx, ny, b = hit
            placed[pid] = {"P_via": [px, py], "N_via": [nx, ny], "escape": esc_layer(f),
                           "stub": stub_layer(f), "xalloc": [XALLOC[(pid, "P")], XALLOC[(pid, "N")]]}
            GEOM[pid] = geom_rec(b, f)
            st.add(b[0], b[1], pid)
            if verbose: print("OK  ", pid, esc_layer(f), stub_layer(f), (px, py), (nx, ny))
            continue
        _by = y_bias(f)
        if ALLOC:
            _xw = float(__import__("os").environ.get("CO10_XWIN", "0"))
            if _xw > 0:
                _all = PAIR_DOMAIN[pid]["pair_rows"]
                _flt = [r for r in _all if abs(float(r[0]) - f["pad"]["P"][0]) <= _xw
                        and abs(float(r[1]) - f["pad"]["N"][0]) <= _xw]
                if _flt:
                    PAIR_DOMAIN[pid]["pair_rows"] = _flt
            if __import__("os").environ.get("CO10_CORNER"):
                _ly = LANES[pid]["lane_y"]
                _own = np.array([list(f["pad"][q]) + list(f["conn_pad"][q]) for q in ("P", "N")], dtype=float)
                _exm = np.zeros(len(PXA), dtype=bool)
                for _q in ("P", "N"):
                    _exm |= (np.abs(PXA - f["pad"][_q][0]) < 0.02) & (np.abs(PYA - f["pad"][_q][1]) < 0.02)
                    _exm |= (np.abs(PXA - f["conn_pad"][_q][0]) < 0.02) & (np.abs(PYA - f["conn_pad"][_q][1]) < 0.02)
                _all = PAIR_DOMAIN[pid]["pair_rows"]
                _flt = []
                for r in _all:
                    ok = True
                    for _q, _x in (("P", float(r[0])), ("N", float(r[1]))):
                        _cy = _ly + pol_off(f, _q)
                        _g = pad_via_edge(np.array([_x]), np.array([_cy]))[0]
                        _gg = np.where(_exm, 999.0, pad_via_edge(np.array([_x]), np.array([_cy])))[0]
                        if min(_g, _gg) < ESC - TOL:
                            ok = False; break
                    if ok:
                        _flt.append(r)
                if _flt:
                    PAIR_DOMAIN[pid]["pair_rows"] = _flt
            rows = sorted(PAIR_DOMAIN[pid]["pair_rows"],
                          key=lambda r: (abs(float(r[0]) - ALLOC[(pid, "P")][0])
                                         + abs(float(r[1]) - ALLOC[(pid, "N")][0])
                                         + abs(float(r[2]) - ALLOC[(pid, "P")][1])
                                         + abs(float(r[3]) - ALLOC[(pid, "N")][1]),
                                         float(r[0]), float(r[1])))
            rows = rows[:2000] + [r for r in sorted(PAIR_DOMAIN[pid]["pair_rows"],
                                                    key=lambda r: (abs(float(r[2]) - ALLOC[(pid, "P")][1])
                                                                   + abs(float(r[3]) - ALLOC[(pid, "N")][1])))[:400]]
            seen = set(); rows = [r for r in rows if not (tuple(r) in seen or seen.add(tuple(r)))]
        else:
            rows = sorted(PAIR_DOMAIN[pid]["pair_rows"],
                          key=lambda r: (abs(float(r[0]) - f["pad"]["P"][0]) + abs(float(r[1]) - f["pad"]["N"][0])
                                         + abs(float(r[2]) - (f["pad"]["P"][1] + _by))
                                         + abs(float(r[3]) - (f["pad"]["N"][1] + _by)),
                                         float(r[0]), float(r[1])))
        hit = None; reasons = {}
        for r in rows:
            px, nx, py, ny, dd = (float(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]))
            if dd < VV - TOL or abs(px - nx) < 0.38 - TOL: continue
            if abs(py - f["pad"]["P"][1]) > YWIN or abs(ny - f["pad"]["N"][1]) > YWIN: continue
            b = build(f, px, py, nx, ny)
            if b is None: continue
            err = check(*b, st)
            if err is None:
                hit = (px, py, nx, ny, b); break
            reasons.setdefault(err[0], err)
        if hit is None:
            failed[pid] = {"n_rows_scanned": len(rows), "reasons": {k: str(v)[:200] for k, v in reasons.items()}}
            if verbose: print("FAIL", pid, failed[pid]["reasons"])
            continue
        px, py, nx, ny, b = hit
        placed[pid] = {"P_via": [px, py], "N_via": [nx, ny], "escape": esc_layer(f),
                       "stub": stub_layer(f), "pair_dist": dd,
                       "land": {"P": land_meta(f)["P"], "N": land_meta(f)["N"]}}
        GEOM[pid] = geom_rec(b, f)
        st.add(b[0], b[1], pid)
        if verbose: print("OK  ", pid, esc_layer(f), stub_layer(f), (px, py), (nx, ny))
    return {"rule": rule, "order": order, "n_pages": len(FACTS), "n_placed": len(placed), "geom": GEOM,
            "n_failed": len(failed), "placed": placed, "failed": failed,
            "verdict": "PROBE_PLACED_ALL" if not failed else "PROBE_RESIDUAL"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule", choices=["d3", "fan", "co10"], default="d3")
    ap.add_argument("--order", choices=["engine", "fewest", "laneidx", "rev"], default="engine")
    ap.add_argument("--out", default=None)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    res = probe(a.rule, a.order, a.verbose)
    res["producer"] = "k2/tools/p3_v57_co10_west_fan_probe.py"
    res["pad_field_sha256"] = hashlib.sha256((SPEC / "m13_v57_co09_pad_field.json").read_bytes()).hexdigest()
    res["redline"] = "只读探针：未改冻结四源；未改 canonical 图纸"
    out = Path(a.out) if a.out else (SPEC / f"m13_v57_co10_west_fan_probe_{a.rule}_{a.order}.json")
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(f"CO-10 probe rule={a.rule} order={a.order}: placed {res['n_placed']}/{res['n_pages']} "
          f"failed={sorted(res['failed'])} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
