#!/usr/bin/env python3
"""K2 · R514 —— 承 handoff-K2-514 §0（受证额度 1 · 一次实现窗）：给 R512 的**精确净距联合 MCF**
加**唯一一个新自由度 = 「层换工序」（layer hop）**：

  · 走线层集合 `{In5.Cu, In4.Cu}`（第二层取 In4，依据 R513《层余量审计》）；
  · 每根车道**至多 2 对过孔**（下去一对、上来一对）；孔径/外径取**车道锚同类值**（r=0.175 · drill=0.1
    ⇒ 净空半径项 VR = max(0.175+eff, 0.1+0.25) = 0.35）；
  · 过孔落点**限定在四个在册宽区**（R513 层余量审计 `boxes_mm`：COMB / BELT / WALL / FIELD）；
  · 换序发生在 In4（**跨层不相交 = 合法**）；In5 窄段顺序自然不变；
  · 净距编码**逐层独立**沿用 R512（节点占用＝以该点为头的弧 ＋ 该点为 src），跨层不设净距约束
    （不同层不相冲），过孔＝**同时占用两层的同一格点**（故孔径/间距由跨层占用 ＋ 过孔间距约束给出）。

**前置硬闸（fail-closed）**：R512 `gate_preexisting` ＋ 声明集自检 `selfcheck` ＋ `Validate()`；
**规模闸**：`--plan` 先算 bool/约束数；> 1.2M bool ⇒ 先缩层窗口（`--l1 zones`），不得盲跑。
**恰一次** `Solve()`。得解 ⇒ 渲染 ⇒ 在册 `exact_gate`（逐层）＋ **跨层/过孔判据** ⇒ 里程碑。

具名偏离（相对 R512，逐条登记）：
 (D1) 第二层 In4 的**可用范围**由 `--l1` 决定（默认 `full`；`zones` = 仅四宽区）。二者皆为**保守**模型
      （子集 ⇒ 只会排除合法解，不会放行非法解）。
 (D2) **不加** R512 的三个显式序变量（门列/院行/缝位）。理由：T3 已机器证明净距编码与在册判据**逐对等价**
      ⇒ 序变量对**合法性**是冗余的；而它们在「车道于该格点处位于 In4」时会**伪不可行**（linking 要求
      In5 弧终止于该点）。合法性由渲染后的 `exact_gate` 独立复验（缺一 fail-closed）。
 (D3) 东南区域约定（东道禁入 NW 迷宫 cols24-112/rows<=32）只施加在 **In5**（承 R512）；In4 为**新层**，
      无此约定（T8 已证该约定非绑定资源）。
"""
import argparse, collections, heapq, importlib, json, math, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
PREV = importlib.import_module("K2_" + "R" + "499" + "_CONFLICT_TABLE_ONE_IMPLEMENTATION_v3")
R512 = importlib.import_module("K2_" + "R" + "512" + "_JOINT_MCF_NODECAP_FIX_v1")
import k2_p4_b2_in5_lane_router_v3 as RT
from k2_p4_b2_in5_lane_router_v3 import (build_base, eff, HOLE_CLR, is_lane, exact_gate,
                                         _seg_seg_batch, _pt_seg_pts, _seg_rect_dists)

P, HW, NY, NX, X0, Y0 = PREV.P, PREV.HW, PREV.NY, PREV.NX, PREV.X0, PREV.Y0
XY = PREV.XY
EPS = PREV.EPS
NID = NX * NY
BOUND = 1.6
VIA_R, VIA_DRILL = 0.175, 0.1
VR = max(VIA_R + 0.175, VIA_DRILL + HOLE_CLR)      # 0.35 （车道锚同类值）
VIA_SEP = 2.0 * VR                                  # 0.70 过孔—过孔 / 过孔—他线锚 中心距下限
VIA_LANE = VR + HW                                  # 0.43 过孔—他线走线 中心距下限（= P）
MAX_VIA_PAIRS = 2
LAYER_OF = {0: "In5.Cu", 1: "In4.Cu"}
# R513 层余量审计 boxes_mm（梳齿区 / 南带 / 墙洞带 / 焊盘场）
ZONES = [(83.0, 53.5, 96.0, 57.5), (96.0, 57.5, 133.0, 66.0),
         (132.5, 43.0, 135.0, 55.0), (125.0, 41.0, 142.6, 54.6)]
SCALE_GATE = 1_200_000


def nl(L, pos):
    return L * NID + pos


def rc(n):
    return n // NY, n % NY


class Gen2:
    """两层（In5 / In4）图源：逐层障碍栅 + 锚禁近圈 + 过孔站点 + 区域约定。"""

    def __init__(self, model, l1scope="full", verbose=False):
        self.m = model
        self.l1scope = l1scope
        g = PREV.Gen(model)                      # In5 baseline（栅/基/锚/边表）
        self.g0 = g
        self.rast = g.rast
        self.an = g.an
        self.names = g.names
        self.A, self.B = g.A, g.B
        self.edge_u, self.edge_v = g.edge_u, g.edge_v
        self.edge_len, self.edge_h = g.edge_len, g.edge_h
        self.esamp, self.emask = g.esamp, g.emask
        self.rNX, self.rNY = g.rNX, g.rNY
        RT.PAD_EXTRA = EPS
        self.free_node = {0: g.free_node}
        self.edge_base_ok = {0: g.edge_base_ok}
        b4 = build_base(self.rast, model, "In4.Cu", set(), set(), HW, frozenset())
        self.free_node[1] = self._cell_free(b4)
        self.edge_base_ok[1] = self._edge_free(b4)
        self.free_via = {}
        for L in (0, 1):
            bv = build_base(self.rast, model, LAYER_OF[L], set(), set(), VR, frozenset())
            self.free_via[L] = self._cell_free(bv)
        RT.PAD_EXTRA = EPS
        # 四宽区掩码
        z = np.zeros((NX, NY), bool)
        for (x0, y0, x1, y1) in ZONES:
            i0 = int(math.ceil((x0 - X0) / P - 1e-9)); i1 = int(math.floor((x1 - X0) / P + 1e-9))
            j0 = int(math.ceil((y0 - Y0) / P - 1e-9)); j1 = int(math.floor((y1 - Y0) / P + 1e-9))
            i0 = max(0, i0); j0 = max(0, j0)
            z[i0:i1 + 1, j0:j1 + 1] = True
        self.zone2d = z
        self.zonemask = z.reshape(-1)
        # 他车道锚 keepout（半径项 = max(via_r+eff, drill+HOLE_CLR)，未加本线半宽）
        self.pt_keep = {}
        for nm in self.names:
            pts = []
            for a in self.an:
                if a["net"] == nm:
                    continue
                rad = max(a["via_r"] + eff(a["net"]), a["drill"] + HOLE_CLR)
                pts.append((a["A"][0], a["A"][1], rad)); pts.append((a["B"][0], a["B"][1], rad))
            self.pt_keep[nm] = np.array(pts, float).reshape(-1, 3)
        wall_x = X0 + 114.0 * P
        self.grp = {nm: ("west" if g.B[nm][0] < wall_x else "east") for nm in self.names}
        self._nok, self._eok, self._viaok = {}, {}, {}
        for nm in self.names:
            for L in (0, 1):
                self._nok[(nm, L)] = self._node_ok(nm, L)
                self._eok[(nm, L)] = self._edge_ok(nm, L)
            self._viaok[nm] = self._via_ok(nm)
        if verbose:
            t = np.meshgrid(np.arange(NX), np.arange(NY), indexing="ij")
            print("  free(In5)=%d free(In4)=%d zone=%d via-any=%d" % (
                int(self.free_node[0].sum()), int(self.free_node[1].sum()), int(self.zonemask.sum()),
                int(self._viaany().sum())))

    # ---------- raster sampling ----------
    def _cell_free(self, bad):
        r = self.rast
        ii, jj = np.meshgrid(np.arange(NX), np.arange(NY), indexing="ij")
        ci = np.rint((X0 + ii * P - r.X0) / r.step).astype(int)
        cj = np.rint((Y0 + jj * P - r.Y0) / r.step).astype(int)
        oob = (ci < 0) | (ci >= r.NX) | (cj < 0) | (cj >= r.NY)
        ci = np.clip(ci, 0, r.NX - 1); cj = np.clip(cj, 0, r.NY - 1)
        return (~oob) & (bad[ci, cj] == False)          # noqa: E712

    def _edge_free(self, bad):
        r = self.rast
        si = np.rint((self.esamp[:, :, 0] - r.X0) / r.step).astype(int)
        sj = np.rint((self.esamp[:, :, 1] - r.Y0) / r.step).astype(int)
        ob = (si < 0) | (si >= self.rNX) | (sj < 0) | (sj >= self.rNY)
        si = np.clip(si, 0, self.rNX - 1); sj = np.clip(sj, 0, self.rNY - 1)
        return ~(((bad[si, sj] | ob) & self.emask).any(1))

    # ---------- per-lane per-layer legality ----------
    def _node_ok(self, nm, L):
        ok = self.free_node[L].copy()
        if L == 1 and self.l1scope == "zones":
            ok &= self.zone2d
        ii, jj = np.meshgrid(np.arange(NX), np.arange(NY), indexing="ij")
        xs = X0 + ii * P; ys = Y0 + jj * P
        for x, y, rad in self.pt_keep[nm]:
            ok &= (np.hypot(xs - x, ys - y) >= HW + rad + EPS)
        return ok.reshape(-1)

    def _edge_ok(self, nm, L):
        pts = self.pt_keep[nm]
        if not len(pts):
            return self.edge_base_ok[L].copy()
        need = HW + pts[:, 2] + EPS
        ok = self.edge_base_ok[L].copy()
        CH = 2048
        for c0 in range(0, len(ok), CH):
            c1 = min(len(ok), c0 + CH)
            xs = self.esamp[c0:c1, :, 0][:, :, None]; ys = self.esamp[c0:c1, :, 1][:, :, None]
            d = np.hypot(xs - pts[None, None, :, 0], ys - pts[None, None, :, 1])
            d = np.where(self.emask[c0:c1][:, :, None], d, 1e9)
            ok[c0:c1] &= (d >= need[None, None, :]).all(2).all(1)
        return ok

    def _via_ok(self, nm):
        ok = (self.free_via[0] & self.free_via[1] & self.zone2d)
        ii, jj = np.meshgrid(np.arange(NX), np.arange(NY), indexing="ij")
        xs = X0 + ii * P; ys = Y0 + jj * P
        for x, y, rad in self.pt_keep[nm]:
            ok &= (np.hypot(xs - x, ys - y) >= VR + rad + EPS)
        return ok.reshape(-1)

    def _viaany(self):
        v = np.zeros(NID, bool)
        for nm in self.names:
            v |= self._viaok[nm]
        return v

    def region_ok(self, nm, L):
        if L == 0 and self.grp[nm] == "east":
            m = np.ones((NX, NY), bool)
            m[24:113, 0:33] = False
            return m.reshape(-1)
        return np.ones(NID, bool)

    def via_positions(self, nm):
        return np.nonzero(self._viaok[nm] & self._nok[(nm, 0)] & self._nok[(nm, 1)])[0]

    # ---------- per-lane 2-layer graph ----------
    def build_lane(self, nm):
        n0 = self._nok[(nm, 0)] & self.region_ok(nm, 0)
        n1 = self._nok[(nm, 1)] & self.region_ok(nm, 1)
        e0 = self._eok[(nm, 0)] & n0[self.edge_u] & n0[self.edge_v]
        e1 = self._eok[(nm, 1)] & n1[self.edge_u] & n1[self.edge_v]
        g = self.g0
        n2d = g.node_ok(nm)
        pts = g.pt_by_net[nm]
        s0 = g.nearest_node(self.A[nm], n2d, pts)
        t0 = g.nearest_node(self.B[nm], n2d, pts, taken=() if s0 is None else (s0,))
        if s0 is None or t0 is None:
            return None
        src = nl(0, s0[0] * NY + s0[1]); snk = nl(0, t0[0] * NY + t0[1])
        au, av = [], []
        for L, eok in ((0, e0), (1, e1)):
            uu = self.edge_u[eok]; vv = self.edge_v[eok]
            au.append(L * NID + uu); av.append(L * NID + vv)
            au.append(L * NID + vv); av.append(L * NID + uu)
        AU = np.concatenate(au); AV = np.concatenate(av)
        pw = np.hypot(((AU % NID) // NY - (AV % NID) // NY) * P, ((AU % NID) % NY - (AV % NID) % NY) * P)
        lat = []
        for u, v, w in zip(AU.tolist(), AV.tolist(), pw.tolist()):
            lat.append((u, v, w))
        # via arcs (0-length, both directions) must be present BEFORE the prune so that the In4 layer
        # is reachable from src (otherwise every In4 node looks unreachable and is pruned away)
        vp = self.via_positions(nm)
        via_cand = []
        for p in vp.tolist():
            u0 = nl(0, p); u1 = nl(1, p)
            via_cand.append((u0, u1, 0.0, ("d", p)))
            via_cand.append((u1, u0, 0.0, ("u", p)))
        adj = collections.defaultdict(list)
        for u, v, w in lat:
            adj[u].append((v, w))
        for u, v, w, _t in via_cand:
            adj[u].append((v, w))
        # prune: declared detour budget around the shortest src->snk path (2-layer graph)
        ds = self._dij(adj, src); dt = self._dij(adj, snk)
        sp = ds.get(snk, float("inf"))
        if not math.isfinite(sp):
            return None
        keep = {n for n in ds if n in dt and ds[n] + dt[n] <= BOUND * sp + 1e-9}
        adj2 = collections.defaultdict(list)
        for u, v, w in lat:
            if u in keep and v in keep:
                adj2[u].append((v, w))
        via_arcs = {}                                  # (u,v) -> ('d'|'u', pos)
        for u, v, w, t in via_cand:
            if u in keep and v in keep:
                adj2[u].append((v, w)); via_arcs[(u, v)] = t
        return {"nm": nm, "src": src, "snk": snk, "adj": dict(adj2), "sp": sp,
                "vias": sorted(via_arcs.keys()), "via_arcs": via_arcs, "nkeep": len(keep)}

    @staticmethod
    def _dij(adj, st):
        best = {st: 0.0}; pq = [(0.0, st)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > best.get(u, 1e18) + 1e-12:
                continue
            for (v, w) in adj.get(u, ()):
                nd = d + w
                if nd < best.get(v, 1e18) - 1e-12:
                    best[v] = nd; heapq.heappush(pq, (nd, v))
        return best


# ============================ gate (2-layer) ============================
def _obstacles(model, L):
    """per-layer obstacle arrays: segs (n,2,2)+rad, vias (m,2)+rad, pads (k,4)+rad."""
    lay = LAYER_OF[L]
    sg, sr, vp, vrad, pb, pr = [], [], [], [], [], []
    for s in model["segs"][lay]:
        net = s[5]
        if is_lane(net):
            continue
        sg.append(((s[0], s[1]), (s[2], s[3]))); sr.append(s[4] + eff(net))
    for v in model["vias"]:
        if lay not in v["layers"] or is_lane(v["net"]):
            continue
        vp.append((v["x"], v["y"])); vrad.append(max(v["r"] + eff(v["net"]), v["drill"] + HOLE_CLR))
    for p in model["pads"]:
        if is_lane(p["net"]):
            continue
        if lay not in p["layers"] and not p["pth"]:
            continue
        b = p["box"]; pb.append(b); pr.append(eff(p["net"]))
        if p["pth"] and p.get("drill"):
            vp.append((p["cx"], p["cy"])); vrad.append(p["drill"] + HOLE_CLR)
    return (np.array(sg, float).reshape(-1, 2, 2), np.array(sr, float).reshape(-1),
            np.array(vp, float).reshape(-1, 2), np.array(vrad, float).reshape(-1),
            np.array(pb, float).reshape(-1, 4), np.array(pr, float).reshape(-1))


def gate_vias(model, vias, lane_polys, anchors, hw=HW):
    """跨层/过孔判据：过孔 vs 他线走线（两层）· 过孔 vs 过孔 · 过孔 vs 静态障碍（两层）。"""
    obs = {L: _obstacles(model, L) for L in (0, 1)}
    bad = []
    V = np.array([[v[0], v[1]] for v in vias], float).reshape(-1, 2)
    for L in (0, 1):
        S, SR, OV, OVR, PB2, PR2 = obs[L]
        if len(S):
            d = _pt_seg_pts(V, S[:, 0, :], S[:, 1, :])
            mg = d - VR - (SR[None, :] + HW)
            k = int(np.argmin(mg) % mg.shape[1])
            if mg.min() < -1e-6:
                bad.append(("via-obstacle-seg", L, round(float(mg.min()), 4)))
        if len(OV):
            d = np.linalg.norm(V[:, None, :] - OV[None, :, :], axis=-1)
            mg = d - VR - OVR[None, :]
            if mg.min() < -1e-6:
                bad.append(("via-obstacle-via", L, round(float(mg.min()), 4)))
        if len(PB2):
            mg = _seg_rect_dists(np.stack([V[:, None, :], V[:, None, :]], 1), PB2) - VR - PR2[None, :]
            if mg.min() < -1e-6:
                bad.append(("via-obstacle-pad", L, round(float(mg.min()), 4)))
        # via vs other lanes' tracks on layer L
        for nm, polys in lane_polys.items():
            sg = []
            for p in polys.get(L, []):
                sg += [[(p[k][0], p[k][1]), (p[k + 1][0], p[k + 1][1])] for k in range(len(p) - 1)]
            if not sg:
                continue
            mine = np.array([v[2] == nm for v in vias], bool)
            if not mine.any():
                continue
            d = _pt_seg_pts(V[mine], np.array(sg, float)[:, 0, :], np.array(sg, float)[:, 1, :])
            mg = d - VR - hw
            if mg.min() < -1e-6:
                bad.append(("via-lane-%s" % nm, L, round(float(mg.min()), 4)))
    # via vs via (different nets)
    if len(V) > 1:
        for i in range(len(V)):
            for j in range(i + 1, len(V)):
                if vias[i][2] == vias[j][2]:
                    continue
                dd = float(np.linalg.norm(V[i] - V[j]))
                if dd < VIA_SEP - 1e-6:
                    bad.append(("via-via", (vias[i][2], vias[j][2]), round(dd, 4)))
    # via vs other lanes' A/B anchors (lane copper is 'movable' in the frozen baseline convention,
    # so only the declared A/B anchor points are treated as fixed, exactly as in R499/R512)
    for (x, y, net) in vias:
        for a in anchors:
            if a["net"] == net:
                continue
            rad = max(a["via_r"] + eff(a["net"]), a["drill"] + HOLE_CLR)
            for (ax, ay) in (a["A"], a["B"]):
                if math.hypot(x - ax, y - ay) < VR + rad - 1e-6:
                    bad.append(("via-anchor", (net, a["net"]), round(math.hypot(x - ax, y - ay), 4)))
    return {"n_via_viol": len(bad), "via_violations": bad[:20], "n_vias": len(vias)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="/tmp/opencode/archer/model_l8.json")
    ap.add_argument("--out", default=None)
    ap.add_argument("--maxtime", type=float, default=1500.0)
    ap.add_argument("--l1", choices=("full", "zones"), default="full", help="第二层 In4 的可用范围")
    ap.add_argument("--plan", action="store_true", help="只建图并报规模（0 次 Solve）")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--build-only", action="store_true", help="建模型 + Validate，不 Solve（0 额度）")
    a = ap.parse_args()
    out = a.out or os.path.join(HERE, "K2_R514_LAYERHOP_JOINT_MCF_v1.json")
    t00 = time.time()
    model = json.load(open(a.model))
    rep = {"artifact": "k2_r514_layerhop_joint_mcf_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "handoff-K2-514 sec.0 (monitor stop-order reply => one implementation window) · "
                        "quota 1 · exactly one Solve()",
           "paradigm": "two-layer joint MCF (In5 + In4) with the R512 exact per-layer clearance encoding; "
                       "layer changes only via <=2 via pairs per lane, via sites restricted to the 4 "
                       "registered wide zones; cross-layer crossing legal",
           "deviations": {"D1": "In4 scope = %s (full=all free nodes / zones=4 wide boxes only)" % a.l1,
                          "D2": "R512 explicit order vars (gate cols / yard rows / wall gaps) NOT added: "
                                "T3 proved the clearance encoding pair-exactly equals the registered ruler, so "
                                "they are redundant for legality, and they would spuriously forbid a lane being "
                                "on In4 at a gate/yard/gap node (linking requires an In5 arc to end there)",
                          "D3": "SE region convention (east lanes excluded from NW maze) applied on In5 only"},
           "params": {"P": P, "HW": HW, "VIA_R": VIA_R, "VIA_DRILL": VIA_DRILL, "VR": VR,
                      "VIA_SEP": VIA_SEP, "VIA_LANE": VIA_LANE, "MAX_VIA_PAIRS": MAX_VIA_PAIRS,
                      "BOUND": BOUND, "zones": ZONES}}
    g2 = Gen2(model, l1scope=a.l1, verbose=True)
    rep["preexisting_gates"] = PREV.gate_preexisting(model, g2.g0, 16)
    rep["selfcheck_soundness"] = R512.selfcheck()
    pre_ok = bool(rep["preexisting_gates"]["all_pass"] and rep["selfcheck_soundness"]["pass"])
    rep["preconditions_all_green"] = pre_ok
    if not pre_ok:
        rep["decision"] = "STOP-BEFORE-BUILD: 前置硬闸/自检未过 ⇒ fail-closed"
        json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
        print("FAIL-FAST", out); return
    lanes = []
    for nm in g2.names:
        L = g2.build_lane(nm)
        if L is None:
            rep["decision"] = "STOP-BEFORE-BUILD: lane %s 端点/连通性失败 ⇒ fail-closed" % nm
            json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
            print("FAIL-FAST(lane)", nm, out); return
        lanes.append(L)
    narc = sum(sum(len(v) for v in L["adj"].values()) for L in lanes)
    nvia = sum(len(L["vias"]) for L in lanes)
    rep["graph"] = {"lattice": [NX, NY], "l1_scope": a.l1,
                    "pruned_directed_arcs_per_lane": [sum(len(v) for v in L["adj"].values()) for L in lanes],
                    "total_pruned_directed_arcs": narc, "via_arcs": nvia,
                    "shortest_path_mm": {L["nm"]: round(L["sp"], 3) for L in lanes},
                    "kept_nodes_per_lane": [L["nkeep"] for L in lanes]}
    # NOTE: `narc` already contains the via arcs; the literal x-var count = narc (+1 for lit_clr).
    rep["scale"] = {"bool_vars_estimate": narc + 1, "gate": SCALE_GATE,
                    "under_gate": (narc + 1) <= SCALE_GATE, "via_arcs_subset_of_arcs": nvia}
    if a.plan:
        rep["decision"] = "PLAN-ONLY（只建图报规模 · Solve() 0 次 · 额度未耗）"
        rep["elapsed_s"] = round(time.time() - t00, 1)
        json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
        print(json.dumps(rep["graph"]["pruned_directed_arcs_per_lane"], ensure_ascii=False))
        print(json.dumps({"scale": rep["scale"], "shortest_path_mm": rep["graph"]["shortest_path_mm"]},
                         ensure_ascii=False, indent=1))
        print("WROTE", out); return
    from ortools.sat.python import cp_model
    mo = cp_model.CpModel(); ASSUMP = {}
    x = {}
    for li, L in enumerate(lanes):
        for u, lst in L["adj"].items():
            for (v, w) in lst:
                x[(li, u, v)] = mo.NewBoolVar("x_%d_%d_%d" % (li, u, v))
    ncons = 0
    for li, L in enumerate(lanes):
        ins = collections.defaultdict(list); outs = collections.defaultdict(list); nodes = set()
        for u, lst in L["adj"].items():
            nodes.add(u)
            for (v, w) in lst:
                nodes.add(v); ins[v].append(x[(li, u, v)]); outs[u].append(x[(li, u, v)])
        for n in nodes:
            if n == L["src"]:
                mo.Add(sum(outs[n]) == 1); mo.Add(sum(ins[n]) == 0)
            elif n == L["snk"]:
                mo.Add(sum(ins[n]) == 1); mo.Add(sum(outs[n]) == 0)
            else:
                mo.Add(sum(ins[n]) == sum(outs[n]))
            ncons += 1
        mo.Add(sum(x[(li, u, v)] for u, lst in L["adj"].items() for (v, w) in lst)
               <= int(math.ceil(BOUND * L["sp"] / P)) + 8)
        ncons += 1
        mo.Add(sum(x[(li, k[0], k[1])] for k in L["vias"]) <= 2 * MAX_VIA_PAIRS); ncons += 1
    # ---- 节点占用容量（逐层）：以该格点为头的弧 ＋ 该格点为 src 的车道  ≤ 1 ----
    inc = collections.defaultdict(list); srccount = collections.defaultdict(int)
    for (li, u, v), var in x.items():
        inc[(u // NID, v % NID)].append(var)
    for L in lanes:
        srccount[(L["src"] // NID, L["src"] % NID)] += 1
    for key in set(inc) | set(srccount):
        users = inc.get(key, []); const = srccount.get(key, 0)
        if len(users) + const > 1:
            mo.Add(sum(users) + const <= 1); ncons += 1
    # ---- 精确净距声明集（逐层独立）----
    E = collections.defaultdict(list); S2 = collections.defaultdict(list)
    for (li, u, v), var in x.items():
        L = u // NID; pu = u % NID; pv = v % NID
        for c in R512.claim_of(pu, pv):
            key = (L, c)
            (E if c in (pu, pv) else S2)[key].append((li, var))
    lit_clr = mo.NewBoolVar("clr"); ASSUMP["clearance_exact_per_layer"] = lit_clr
    nclr = 0
    for key in set(E) & set(S2):
        byE = collections.defaultdict(list); byS = collections.defaultdict(list)
        for li, v_ in E[key]:
            byE[li].append(v_)
        for li, v_ in S2[key]:
            byS[li].append(v_)
        for li, vs in byE.items():
            others = [v_ for l2, ws in byS.items() if l2 != li for v_ in ws]
            y = sum(vs) + (1 if lanes[li]["src"] == nl(key[0], key[1]) else 0)
            if others:
                M = len(others) + 1
                mo.Add(sum(others) + M * y <= M).OnlyEnforceIf(lit_clr); nclr += 1
    # ---- 过孔：同一格点上下不得同用；过孔—过孔中心距 ≥ VIA_SEP ----
    for li, L in enumerate(lanes):
        dvar, uvar = {}, {}
        for (u, v) in L["vias"]:
            tag, p = L["via_arcs"][(u, v)]
            (dvar if tag == "d" else uvar)[p] = x[(li, u, v)]
        for p in set(dvar) & set(uvar):
            mo.Add(dvar[p] + uvar[p] <= 1); ncons += 1
    vbynode = collections.defaultdict(list)
    for li, L in enumerate(lanes):
        for (u, v) in L["vias"]:
            vbynode[u % NID].append(x[(li, u, v)])
    vps = sorted(vbynode)
    cell = collections.defaultdict(list)
    for p in vps:
        x_, y_ = XY(*rc(p))
        cell[(int(x_ // VIA_SEP), int(y_ // VIA_SEP))].append(p)
    seen = set()
    for (cx, cy), ps in cell.items():
        cand = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                cand += cell.get((cx + dx, cy + dy), [])
        for p in ps:
            for q in cand:
                if q == p:
                    continue
                key = (min(p, q), max(p, q))
                if key in seen:
                    continue
                seen.add(key)
                if math.dist(XY(*rc(p)), XY(*rc(q))) < VIA_SEP - 1e-9:
                    mo.Add(sum(vbynode[p]) + sum(vbynode[q]) <= 1); ncons += 1
    v = mo.Validate()
    rep["model"] = {"bool_vars": len(mo.Proto().variables), "constraints": len(mo.Proto().constraints),
                    "clearance_constraints": nclr, "ncons_other": ncons,
                    "assumption_groups": list(ASSUMP), "validate": v or "OK",
                    "via_sep_pairs_constrained": len(seen)}
    if a.build_only:
        rep["decision"] = "BUILD-ONLY（模型建好 · Validate %s · Solve() 0 次 · 额度未耗）" % (v or "OK")
        rep["elapsed_s"] = round(time.time() - t00, 1)
        json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
        print(json.dumps(rep["model"], ensure_ascii=False, indent=1))
        print("WROTE", out); return
    if v:
        rep["decision"] = "STOP-BEFORE-SOLVE: 模型 Validate 未过 ⇒ fail-closed"
        json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
        print("MODEL-INVALID", out); return
    for nm, lit in ASSUMP.items():
        mo.AddAssumption(lit)
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = a.maxtime
    sv.parameters.num_search_workers = 8
    ts = time.time(); st = sv.Solve(mo)
    if st == cp_model.INFEASIBLE:
        try:
            idx = set(sv.SufficientAssumptionsForInfeasibility())
            rep["unsat_core_sufficient"] = sorted(nm for nm, lit in ASSUMP.items() if lit.Index() in idx)
        except Exception as e:                                             # pragma: no cover
            rep["unsat_core_sufficient"] = "unavailable: %s" % e
    rep["solve"] = {"status": sv.StatusName(st), "wall_s": round(time.time() - ts, 1),
                    "quota_consumed": 1, "solve_calls": 1}
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        lane_polys = {}; all_vias = []; per_lane_len = {}; ok_extract = True
        for li, L in enumerate(lanes):
            used = collections.defaultdict(list)
            for u, lst in L["adj"].items():
                for (v_, w) in lst:
                    if sv.Value(x[(li, u, v_)]) == 1:
                        used[u].append(v_)
            prev = {L["src"]: None}; dq = collections.deque([L["src"]])
            while dq:
                u = dq.popleft()
                if u == L["snk"]:
                    break
                for w2 in used[u]:
                    if w2 not in prev:
                        prev[w2] = u; dq.append(w2)
            if L["snk"] not in prev:
                ok_extract = False; rep["solve"]["extract_fail"] = L["nm"]; break
            path = []; cur = L["snk"]
            while cur is not None:
                path.append(cur); cur = prev[cur]
            path.reverse()
            runs = []; vias = []; run = [path[0]]
            for n in path[1:]:
                if n // NID == run[-1] // NID:
                    run.append(n)
                else:
                    vias.append([XY(*rc(run[-1] % NID))[0], XY(*rc(run[-1] % NID))[1]])
                    runs.append(run); run = [n]
            runs.append(run)
            polys = {}
            for run in runs:
                Lr = run[0] // NID
                polys.setdefault(Lr, []).append([list(XY(*rc(p % NID))) for p in run])
            if 0 in polys:
                polys[0][0] = [list(L["A"])] + polys[0][0]
                polys[0][-1] = polys[0][-1] + [list(L["B"])]
            else:
                ok_extract = False; rep["solve"]["no_in5_run"] = L["nm"]; break
            lane_polys[L["nm"]] = polys
            for q in vias:
                all_vias.append((q[0], q[1], L["nm"]))
            per_lane_len[L["nm"]] = round(sum(
                math.dist(p[k], p[k + 1]) for Lr in polys for p in polys[Lr] for k in range(len(p) - 1)), 3)
        if ok_extract:
            # (1) 逐层在册 exact_gate（同层车道互斥 + 同层障碍）
            gate_per_layer = {}; viol_same_net = 0
            for Lr in (0, 1):
                rt = {}
                for nm, polys in lane_polys.items():
                    for k, p in enumerate(polys.get(Lr, [])):
                        if len(p) >= 2:
                            rt["%s#%d" % (nm, k)] = {"pts": p, "layer_cu": LAYER_OF[Lr], "n_vias": len(all_vias)}
                if not rt:
                    continue
                gg = exact_gate(model, rt, [], LAYER_OF[Lr], HW, set(), set(), P, frozenset())
                vp2 = [t for t in gg["lane_pitch_violations"] if t[0].split("#")[0] != t[1].split("#")[0]]
                viol_same_net += gg["n_lane_pitch_viol"] - len(vp2)
                gate_per_layer[LAYER_OF[Lr]] = {
                    "n_lane_pitch_viol": len(vp2), "lane_pitch_min_gap_mm": gg["lane_pitch_min_gap_mm"],
                    "n_clearance_viol": gg["n_clearance_viol"], "clearance_min_mm": gg["clearance_min_mm"],
                    "clearance_violations": gg["clearance_violations"][:10],
                    "lane_pitch_violations": vp2[:10], "n_obs": gg["n_obs"]}
            # (2) 跨层/过孔判据
            gv = gate_vias(model, all_vias, lane_polys, g2.an)
            # (3) 端点（锚）偏差
            edev = {}
            for nm, polys in lane_polys.items():
                p0 = polys[0][0][0]; p1 = polys[0][-1][-1]
                edev[nm] = round(max(math.dist(p0, list(g2.A[nm])), math.dist(p1, list(g2.B[nm]))), 6)
            rep["exact_gate_per_layer"] = gate_per_layer
            rep["gate_vias"] = gv
            rep["same_net_pitch_pairs_ignored"] = viol_same_net
            rep["endpoint_max_dev_mm"] = max(edev.values()) if edev else None
            rep["per_lane_len_mm"] = per_lane_len
            rep["vias_per_lane"] = {nm: sum(1 for v in all_vias if v[2] == nm) for nm in lane_polys}
            ok = (all(gate_per_layer[ln]["n_lane_pitch_viol"] == 0 and gate_per_layer[ln]["n_clearance_viol"] == 0
                      for ln in gate_per_layer)
                  and gv["n_via_viol"] == 0 and (rep["endpoint_max_dev_mm"] or 0) <= 1e-6
                  and all(v <= 2 * MAX_VIA_PAIRS for v in rep["vias_per_lane"].values()))
            rep["requirement_level_gate"] = "PASS" if ok else "FAIL"
            if ok:
                json.dump({"lanes": lane_polys, "vias": all_vias},
                          open(os.path.join(HERE, "K2_R514_LAYERHOP_ROUTES_v1.json"), "w"),
                          ensure_ascii=False, indent=1)
                rep["decision"] = ("TERMINAL SAT: 16/16 双层联合 MCF（层换工序）解 + 逐层在册 exact_gate + "
                                   "跨层/过孔判据 全绿 ⇒ 里程碑")
            else:
                rep["decision"] = "NON-TERMINAL: 独立核 FAIL（见 gate 明细）"
        else:
            rep["decision"] = "NON-TERMINAL: 路径提取不全"
    else:
        rep["decision"] = ("NON-TERMINAL: solver=%s（保守双层模型下未找到可行解；不作板级不可能主张）"
                           % sv.StatusName(st))
    rep["elapsed_s"] = round(time.time() - t00, 1)
    json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: rep[k] for k in ("model", "solve", "requirement_level_gate", "gate_vias",
                                          "decision", "elapsed_s") if k in rep},
                     ensure_ascii=False, indent=1)[:3000])
    print("WROTE", out)


if __name__ == "__main__":
    main()
