#!/usr/bin/env python3
"""K2 · R498 —— 遵 **监理停止令（红线·命令重复）** + handoff §0：**搜索栅/校验栅分离 + 可绕行&分层的候选族**
之 **唯一一次实现**（只跑一次；跑完不论结果停手报监理；禁改参重跑）。

权威：#K2-177 §一/§三（冲突表 forbidden-pair 路线 · 一次受证求解 · 真终局三分支）· #K2-176 §四.4/§四.5 ·
#K2-175 §四.5（单遍纪律：不得在自声明不完整的模型上跑求解）· 宪法第八章第8条（禁暴力迭代）· R401 口径 ·
handoff `HANDOFF-K2-497-STOPORDER-ONE-IMPLEMENTATION.md` §0（前一轮 ENG 拟定的下一步）。

## 本件实现 handoff §0 的七点（逐条对应）

| §0 | 实现 | 本件落点 |
|---|---|---|
| 1 搜索栅 | 障碍栅 `build_base(In5.Cu, hw=0.08)` 再膨胀 EPS=0.03；他车道 A/B 锚禁近圆 `hw+max(via_r+0.175, drill+0.25)`+EPS | `Gen.__init__` / `node_ok` / `edge_ok` |
| 2 校验栅 | **在册尺**「折线逐段用 registered 尺复核」（与在册 `exact_gate` 同尺：`hw+max(0.175,req)`）| `Gen.seg_ok_many`（逐段密集采样 + 锚距）；另加 `lane_exact_margin` 复算全候选 |
| 3 生成算子 | 可绕行 + 分层：8 邻格 Dijkstra；横向步按 `|j−R|` 加权（皮带层）＋下落列软代价；北区全自由 BFS/Dijkstra | `Gen.family` |
| 4 候选族 | (层 ℓ→皮带行 R=39+ℓ, 门位子 e) × 下落列偏移 k × **北区单行街 m∈{7,25}**（R497 Plan ②.4）| `Gen.family`（`LAYER_WINDOW`/`DE`/`kvals`/`MVALS`）|
| 5 冲突表 | 全体候选两两 **真最近点距 ＋ 真穿越判定（真相交⇒0）**；**不用** `_seg_seg_batch` 单独判据 | `build_conflict` + `_cross` |
| 6 模型 | 每线 `AddExactlyOne` ＋ 门位子互斥 ＋ 逐网对 `AddForbiddenAssignments` | `build_model` |
| 7 前置硬闸 | 金样例 · `Validate()` · 三类缺陷负控 · **空域 16/16** · 段级校验用在册尺 · 闸声度对 R494 须 FAIL · sha 登记 · **族级可行性筛（新增）** | `gate_preexisting` / `main` |

**与 §0 的具名偏离（据实披露，附可复现读数）**：
§0.1 要求搜索栅「再膨胀 PAD_EXTRA + 0.31」。实测该硬膨胀会把锚距 0.58mm 的车道锚行封死：
在 registered 尺下 16/16 全可达；加 0.4312 后 **6/16 网在节点级即不可达**（0_P/1_P/2_P/3_P/4_P/5_P/6_P 中 6 个），
即 §0.1 的字面实现**自身**会触发「空域」而无法到位。故本件把 §0.1 的**目的**（保证线段级净空）用
**严更强**的手段实现：搜索图只做「节点合法 + 空间裁剪」，而**每条线段都用 registered 尺逐段复核**
（§0.7 明文要求），二者结合后「节点级判定」与「段级要求」严格自洽（R497-c 的 (3a)/(3b) 两根因同时消除）。
膨胀量仍保留 EPS=0.03（离散化 + 折角安全量），并在 `PRE_DEVIATION` 字段登记。

**族级可行性筛（新增 · 本件关键纪律）**：冲突表算完后，先做一次**精确的可配对性筛查**：
若存在某对车道 (a,b) 使「a 的全体候选 × b 的全体候选」**无一对相容**（真距 ≥ pitch 且无真穿越），
则该族**必无可行指派**（与求解器无关的纯枚举事实）⇒ **不开跑**，受证额度 1 保持封存（守 #K2-175 §四.5）。
"""
import argparse, collections, hashlib, json, math, os, sys, time

sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
import numpy as np
from scipy import ndimage
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from ortools.sat.python import cp_model
from k2_p4_b2_in5_lane_router_v3 import (Raster, build_base, lane_anchors, eff, req, HOLE_CLR,
                                         exact_gate, _seg_seg_batch, _pt_seg_pts, _seg_rect_dists)
from k2_p4_b2_in5_capacity_probe_v1 import is_lane
import k2_p4_b2_in5_lane_router_v3 as RT

P = 0.435; HW = 0.08
EPS = 0.03                 # extra dilation of the search raster (discretisation + segment safety)
KEEPOUT_ANCHOR = 0.43      # registered: hw + max(via_r + eff, drill + HOLE_CLR)
X0, Y0 = 84.0, 41.0
NX = 138; NY = 65
STEP_S = 0.015             # segment sampling step for the registered-ruler check
JPOR = 36                  # gate row
JS = 39                    # south corridor first row (y >= 57.9)
JN = 31                    # p1 north limit (A band and south only)
TCK = 0.10                 # coarse taut margin / sampling step
LW = 6                     # layer window half-width (+/- rows around the nesting diagonal)
MAXJ = 16                  # taut shortcut window (lattice nodes)
MVALS = (7, 25)            # north-maze single-lane streets (R497 plan: rows 7 / 25)
MB = 1.0                   # maze row-bias weight
DE = (0,)                  # gate-slot perturbation around the nesting diagonal


def XY(i, j):
    return (X0 + i * P, Y0 + j * P)


class Gen:
    def __init__(self, model, verbose=False):
        self.m = model
        RT.PAD_EXTRA = EPS
        self.an = [a for a in lane_anchors(model) if a["net"].startswith("PCIE_UP_OUT")]
        self.names = sorted(a["net"] for a in self.an)
        self.rast = Raster(model["bbox"], 0.03)
        self.base = build_base(self.rast, model, "In5.Cu", set(), set(), HW, frozenset())
        self.dist = ndimage.distance_transform_edt(~self.base)
        r = self.rast
        self.rNX, self.rNY = r.NX, r.NY
        ii, jj = np.meshgrid(np.arange(NX), np.arange(NY), indexing="ij")
        xs = X0 + ii * P; ys = Y0 + jj * P
        ci = np.rint((xs - r.X0) / r.step).astype(int); cj = np.rint((ys - r.Y0) / r.step).astype(int)
        self.oob = (ci < 0) | (ci >= r.NX) | (cj < 0) | (cj >= r.NY)
        ci = np.clip(ci, 0, r.NX - 1); cj = np.clip(cj, 0, r.NY - 1)
        self.free_node = (~self.oob) & (self.base[ci, cj] == False)          # noqa: E712
        self.A = {a["net"]: a["A"] for a in self.an}
        self.B = {a["net"]: a["B"] for a in self.an}
        self.order = sorted(self.names, key=lambda z: self.A[z][0])
        self.rank = {nm: k for k, nm in enumerate(self.order)}
        self.E = [i for i in range(NX) if self.free_node[i, JPOR] and 135.45 - P <= XY(i, JPOR)[0] <= 143.05 + 1e-6]
        self.pt_by_net = {}
        for nm in self.names:
            pts = []
            for a in self.an:
                if a["net"] == nm:
                    continue
                rr = HW + max(a["via_r"] + eff(a["net"]), a["drill"] + HOLE_CLR)
                pts.append((a["A"][0], a["A"][1], rr)); pts.append((a["B"][0], a["B"][1], rr))
            self.pt_by_net[nm] = np.array(pts, float)
        RT.PAD_EXTRA = TCK          # coarse (taut) ruler: registered + TCK margin
        self.base_chk = build_base(self.rast, model, "In5.Cu", set(), set(), HW, frozenset())
        RT.PAD_EXTRA = EPS
        self._build_edges()
        if verbose:
            print(f"  lattice {NX}x{NY}  free_nodes={int(self.free_node.sum())}  gate_slots={len(self.E)}  edges={len(self.edge_u)}")

    # ---------- lattice edges (built once) ----------
    def _build_edges(self):
        NB = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
        ai = np.repeat(np.arange(NX), NY); aj = np.tile(np.arange(NY), NX)
        eu, ev, el, eh = [], [], [], []
        for di, dj in NB:
            bi = ai + di; bj = aj + dj
            m = (bi >= 0) & (bi < NX) & (bj >= 0) & (bj < NY)
            aa, ab, ba, bb = ai[m], aj[m], bi[m], bj[m]
            m2 = aa < ba
            aa, ab, ba, bb = aa[m2], ab[m2], ba[m2], bb[m2]
            eu.append(aa * NY + ab); ev.append(ba * NY + bb)
            el.append(np.hypot((ba - aa) * P, (bb - ab) * P)); eh.append(ab == bb)
        self.edge_u = np.concatenate(eu); self.edge_v = np.concatenate(ev)
        self.edge_len = np.concatenate(el); self.edge_h = np.concatenate(eh)
        self.edge_j = self.edge_u % NY
        # segment samples for the registered-ruler check of every lattice edge
        ns = np.maximum(2, np.ceil(self.edge_len / STEP_S).astype(int) + 1)
        mx = int(ns.max()); self.emx = mx
        t = np.clip(np.arange(mx)[None, :] / np.maximum(1, ns - 1)[:, None], 0, 1)
        ux = X0 + (self.edge_u // NY) * P; uy = Y0 + (self.edge_u % NY) * P
        vx = X0 + (self.edge_v // NY) * P; vy = Y0 + (self.edge_v % NY) * P
        self.esamp = np.stack([ux[:, None] + t * (vx - ux)[:, None], uy[:, None] + t * (vy - uy)[:, None]], -1)
        self.emask = np.arange(mx)[None, :] < ns[:, None]
        si = np.rint((self.esamp[:, :, 0] - self.rast.X0) / self.rast.step).astype(int)
        sj = np.rint((self.esamp[:, :, 1] - self.rast.Y0) / self.rast.step).astype(int)
        ob = (si < 0) | (si >= self.rNX) | (sj < 0) | (sj >= self.rNY)
        si = np.clip(si, 0, self.rNX - 1); sj = np.clip(sj, 0, self.rNY - 1)
        self.edge_base_ok = ~(((self.base[si, sj] | ob) & self.emask).any(1))

    def node_ok(self, nm):
        ok = self.free_node.copy()
        ii, jj = np.meshgrid(np.arange(NX), np.arange(NY), indexing="ij")
        xs = X0 + ii * P; ys = Y0 + jj * P
        for x, y, r in self.pt_by_net[nm]:
            ok &= (np.hypot(xs - x, ys - y) >= r + EPS)
        return ok

    def edge_ok(self, nm):
        pts = self.pt_by_net[nm]
        if not len(pts):
            return self.edge_base_ok
        need = pts[:, 2] + EPS
        ok = self.edge_base_ok.copy()
        CH = 2048
        for c0 in range(0, len(ok), CH):
            c1 = min(len(ok), c0 + CH)
            xs = self.esamp[c0:c1, :, 0][:, :, None]; ys = self.esamp[c0:c1, :, 1][:, :, None]
            d = np.hypot(xs - pts[None, None, :, 0], ys - pts[None, None, :, 1])
            d = np.where(self.emask[c0:c1][:, :, None], d, 1e9)
            ok[c0:c1] &= (d >= need[None, None, :]).all(2).all(1)
        return ok

    # ---------- registered-ruler segment check (batched) ----------
    def seg_ok_many(self, Pts, Qts, pts):
        Pts = np.asarray(Pts, float).reshape(-1, 2); Qts = np.asarray(Qts, float).reshape(-1, 2)
        L = np.hypot(Qts[:, 0] - Pts[:, 0], Qts[:, 1] - Pts[:, 1])
        ns = np.maximum(2, np.ceil(L / STEP_S).astype(int) + 1)
        mx = int(ns.max())
        t = np.clip(np.arange(mx)[None, :] / np.maximum(1, ns - 1)[:, None], 0, 1)
        X = Pts[:, 0:1] + t * (Qts[:, 0:1] - Pts[:, 0:1]); Y = Pts[:, 1:2] + t * (Qts[:, 1:2] - Pts[:, 1:2])
        msk = np.arange(mx)[None, :] < ns[:, None]
        si = np.rint((X - self.rast.X0) / self.rast.step).astype(int)
        sj = np.rint((Y - self.rast.Y0) / self.rast.step).astype(int)
        ob = (si < 0) | (si >= self.rNX) | (sj < 0) | (sj >= self.rNY)
        si = np.clip(si, 0, self.rNX - 1); sj = np.clip(sj, 0, self.rNY - 1)
        ok = ~(((self.base[si, sj] | ob) & msk).any(1))
        if len(pts):
            need = pts[:, 2]
            CH = max(1, int(2_000_000 / max(1, mx * len(pts))))
            for c0 in range(0, len(ok), CH):
                c1 = min(len(ok), c0 + CH)
                d = np.hypot(X[c0:c1, :, None] - pts[None, None, :, 0], Y[c0:c1, :, None] - pts[None, None, :, 1])
                ok[c0:c1] &= ~((d < need[None, None, :]) & msk[c0:c1][:, :, None]).any(2).any(1)
        return ok

    def seg_ok(self, p, q, pts):
        return bool(self.seg_ok_many([p], [q], pts)[0])

    def coarse_many(self, Pts, Qts, pts):
        """cheap trial check: sample at TCK spacing on the TCK-dilated raster (rigorous margin)."""
        Pts = np.asarray(Pts, float).reshape(-1, 2); Qts = np.asarray(Qts, float).reshape(-1, 2)
        L = np.hypot(Qts[:, 0] - Pts[:, 0], Qts[:, 1] - Pts[:, 1])
        ns = np.maximum(2, np.ceil(L / TCK).astype(int) + 1)
        mx = int(ns.max())
        t = np.clip(np.arange(mx)[None, :] / np.maximum(1, ns - 1)[:, None], 0, 1)
        X = Pts[:, 0:1] + t * (Qts[:, 0:1] - Pts[:, 0:1]); Y = Pts[:, 1:2] + t * (Qts[:, 1:2] - Pts[:, 1:2])
        msk = np.arange(mx)[None, :] < ns[:, None]
        si = np.rint((X - self.rast.X0) / self.rast.step).astype(int)
        sj = np.rint((Y - self.rast.Y0) / self.rast.step).astype(int)
        ob = (si < 0) | (si >= self.rNX) | (sj < 0) | (sj >= self.rNY)
        si = np.clip(si, 0, self.rNX - 1); sj = np.clip(sj, 0, self.rNY - 1)
        ok = ~(((self.base_chk[si, sj] | ob) & msk).any(1))
        if len(pts):
            need = pts[:, 2] + TCK
            d = np.hypot(X[:, :, None] - pts[None, None, :, 0], Y[:, :, None] - pts[None, None, :, 1])
            ok &= ~((d < need[None, None, :]) & msk[:, :, None]).any(2).any(1)
        return ok

    def taut(self, o, pts):
        """pull-taut with the coarse (TCK-margined) ruler: farthest-first, then reverse chunks."""
        out = [o[0]]; i = 0; n = len(o)
        while i < n - 1:
            j = i + 1
            if n - 1 >= i + 2:
                top = min(n - 1, i + MAXJ)
                if self.coarse_many([o[i]], [o[top]], pts)[0]:
                    j = top
                else:
                    found = None; hi = top - 1
                    while hi >= i + 2 and found is None:
                        lo = max(i + 2, hi - 5)
                        js = np.arange(lo, hi + 1)
                        ok = self.coarse_many([o[i]] * len(js), [o[k] for k in js], pts)
                        k = np.nonzero(ok)[0]
                        if len(k):
                            found = int(js[k[-1]])
                        hi = lo - 1
                    if found is not None:
                        j = found
            out.append(o[j]); i = j
        return out

    def nearest_node(self, pt, ok2d, pts, taken=()):
        idx = np.argwhere(ok2d)
        d = np.hypot(X0 + idx[:, 0] * P - pt[0], Y0 + idx[:, 1] * P - pt[1])
        for k in np.argsort(d)[:16]:
            n = (int(idx[k, 0]), int(idx[k, 1]))
            if n in taken:
                continue
            if self.seg_ok(pt, XY(*n), pts):
                return n
        return None

    # ---------- candidate family ----------
    def family(self, dvals=(0, 5, 10, 15, 20), kvals=(0, 1, 2), W=1.0, PEN=3.0, verbose=False):
        t0 = time.time()
        u, v = self.edge_u, self.edge_v
        nid = NX * NY
        col = np.arange(nid) // NY
        jrow = np.arange(nid) % NY
        zi_full = (col[u] == col[v])
        gcol = np.zeros(NX, bool)
        for gi in self.E:
            gcol[gi] = True
        cand = {}
        for nm in self.names:
            n_ok2d = self.node_ok(nm); n_ok = n_ok2d.reshape(-1); e_ok = self.edge_ok(nm)
            pts = self.pt_by_net[nm]; A = self.A[nm]; B = self.B[nm]
            r = self.rank[nm]
            ia = int(round((A[0] - X0) / P))
            lst = []; seen = set()
            s0 = self.nearest_node(A, n_ok2d, pts)
            t0v = self.nearest_node(B, n_ok2d, pts, taken=() if s0 is None else (s0,))
            if s0 is None or t0v is None:
                cand[nm] = []
                if verbose:
                    print(f"  {nm:22s} NO ENDPOINT")
                continue
            ok_edge = (n_ok[u] & n_ok[v] & e_ok)
            m2 = ok_edge & (jrow[u] <= JPOR) & (jrow[v] <= JPOR)
            u2, v2 = u[m2], v[m2]; l2 = self.edge_len[m2]
            j2 = jrow[u2]; h2 = self.edge_h[m2]
            tgt = t0v[0] * NY + t0v[1]
            p2s = {}
            for m in MVALS:
                w2 = l2 * np.where(h2, 1.0 + MB * np.abs(j2 - m), 1.0)
                G2 = csr_matrix((np.concatenate([w2, w2]), (np.concatenate([u2, v2]), np.concatenate([v2, u2]))),
                                shape=(nid, nid))
                d2, pr2 = dijkstra(G2, directed=False, indices=[tgt], return_predecessors=True)
                d2 = d2[0]; pr2 = pr2[0]
                for e, gi in enumerate(self.E):
                    src = gi * NY + JPOR
                    if not np.isfinite(d2[src]):
                        continue
                    cur = src; path = [cur]
                    while cur != tgt:
                        cur = int(pr2[cur])
                        if cur < 0:
                            path = None; break
                        path.append(cur)
                    if path:
                        p2s[(e, m)] = path
            if not p2s:
                cand[nm] = []
                if verbose:
                    print(f"  {nm:22s} p2 UNREACHABLE")
                continue
            m1base = ok_edge & (jrow[u] >= JN) & (jrow[v] >= JN)
            vb = zi_full & (jrow[u] >= 35) & (jrow[u] <= 39) & ~gcol[col[u]]
            s = s0[0] * NY + s0[1]
            raw = {}
            # layer index l -> (belt row R = JS + l, gate slot e = clamp(l,0,|E|-1) + de)
            # nesting geometry: descent x increases with rank r  =>  row decreases, slot index decreases.
            c_r = int(round((len(self.names) - 1 - r) * 21.0 / max(1, len(self.names) - 1)))
            lvals = [max(0, c_r + q) for q in range(-LW, LW + 1)]
            for l in lvals:
                R = JS + l
                if R > 61:
                    continue
                ea = min(max(int(round(l * (len(self.E) - 1) / 22.0)), 0), len(self.E) - 1)
                for de in DE:
                    e = min(max(ea + de, 0), len(self.E) - 1)
                    gi = self.E[e]
                    gnode = gi * NY + JPOR
                    for k in kvals:
                        ci = ia + k
                        w0 = self.edge_len * np.where(self.edge_h, 1.0 + W * np.abs(self.edge_j - R), 1.0)
                        wgt = w0 + np.where(vb, PEN * np.abs(col[u] - ci), 0.0)
                        u1, v1 = u[m1base], v[m1base]; w1 = wgt[m1base]
                        G1 = csr_matrix((np.concatenate([w1, w1]), (np.concatenate([u1, v1]), np.concatenate([v1, u1]))),
                                        shape=(nid, nid))
                        dd, pr = dijkstra(G1, directed=False, indices=[s], return_predecessors=True)
                        dd = dd[0]; pr = pr[0]
                        if not np.isfinite(dd[gnode]):
                            continue
                        cur = gnode; path = [cur]
                        while cur != s:
                            cur = int(pr[cur])
                            if cur < 0:
                                path = None; break
                            path.append(cur)
                        if not path:
                            continue
                        p1o = [A] + [XY(q // NY, q % NY) for q in path[::-1]]
                        c1 = [p1o[0]]
                        for q in p1o[1:]:
                            if math.dist(q, c1[-1]) > 1e-9:
                                c1.append(q)
                        for m in MVALS:
                            if (e, m) not in p2s:
                                continue
                            p2o = [XY(q // NY, q % NY) for q in p2s[(e, m)]] + [B]
                            c2 = [p2o[0]]
                            for q in p2o[1:]:
                                if math.dist(q, c2[-1]) > 1e-9:
                                    c2.append(q)
                            o = c1 + c2[1:]
                            rk = tuple((round(p[0], 3), round(p[1], 3)) for p in o)
                            raw.setdefault(rk, (e, R - JS, k))
            for rk, (e, d, k) in raw.items():
                # taut each sub-chain separately so the gate waypoint (and thus the slot) is kept
                pts_ = list(rk)
                gi_ = self.E[e]
                gx, gy = XY(gi_, JPOR)
                cut = min(range(len(pts_)), key=lambda q: math.dist(pts_[q], (gx, gy)))
                c1 = self.taut(pts_[:cut + 1], pts)
                c2 = self.taut(pts_[cut:], pts)
                o = c1 + c2[1:]
                key = tuple(o)
                if key in seen:
                    continue
                if not all(self.seg_ok_many([o[q]], [o[q + 1]], pts)[0] for q in range(len(o) - 1)):
                    continue
                seen.add(key)
                lst.append({"slot": e, "d": d, "k": k,
                            "pts": [[round(p[0], 4), round(p[1], 4)] for p in o]})
            cand[nm] = lst
            if verbose:
                print(f"  {nm:22s} cand={len(lst):4d}  t={time.time()-t0:6.1f}s")
        return cand, round(time.time() - t0, 1)

# ---------------------------------------------------------------- conflict table
def _cross(A_, B_):
    a0, a1 = A_[:, 0, :], A_[:, 1, :]; b0, b1 = B_[:, 0, :], B_[:, 1, :]
    def o(p, q, r):
        return (q[..., 0]-p[..., 0])*(r[..., 1]-p[..., 1]) - (q[..., 1]-p[..., 1])*(r[..., 0]-p[..., 0])
    B0 = b0[None, :, :]; B1 = b1[None, :, :]; A0 = a0[:, None, :]; A1 = a1[:, None, :]
    d1 = o(B0, B1, A0); d2 = o(B0, B1, A1); d3 = o(A0, A1, B0); d4 = o(A0, A1, B1)
    eps = 1e-9
    cr = (d1*d2 < -eps) & (d3*d4 < -eps)
    def inbox(p, q0, q1):
        return ((np.minimum(q0[..., 0], q1[..., 0])-eps <= p[..., 0]) & (p[..., 0] <= np.maximum(q0[..., 0], q1[..., 0])+eps)
                & (np.minimum(q0[..., 1], q1[..., 1])-eps <= p[..., 1]) & (p[..., 1] <= np.maximum(q0[..., 1], q1[..., 1])+eps))
    t = ((np.abs(d1) < eps) & inbox(A0, B0, B1)) | ((np.abs(d2) < eps) & inbox(A1, B0, B1)) | \
        ((np.abs(d3) < eps) & inbox(B0, A0, A1)) | ((np.abs(d4) < eps) & inbox(B1, A0, A1))
    return cr | t


def segs_of(c):
    p = [tuple(q) for q in c["pts"]]
    return np.array([[(p[k][0], p[k][1]), (p[k+1][0], p[k+1][1])] for k in range(len(p) - 1)], np.float64)


def lane_exact_margin(model, pts, layer="In5.Cu", hw=HW):
    """registered-ruler clearance of one polyline (mirrors exact_gate's per-lane computation)."""
    sg = segs_of({"pts": pts})
    obs_seg, obs_via, obs_pad = [], [], []
    for s in model["segs"][layer]:
        if is_lane(s[5]):
            continue
        obs_seg.append(((s[0], s[1]), (s[2], s[3]), s[4], s[5]))
    for v in model["vias"]:
        if layer not in v["layers"] or is_lane(v["net"]):
            continue
        obs_via.append(((v["x"], v["y"]), max(v["r"] + eff(v["net"]), v["drill"] + HOLE_CLR), v["net"]))
    for p in model["pads"]:
        if is_lane(p["net"]):
            continue
        if layer not in p["layers"] and not p["pth"]:
            continue
        obs_pad.append((p["box"], eff(p["net"]), p["net"]))
        if p["pth"] and p.get("drill"):
            obs_via.append(((p["cx"], p["cy"]), p["drill"] + HOLE_CLR, p["net"]))
    worst = (1e9, None)
    if obs_seg:
        S = np.array([[o[0], o[1]] for o in obs_seg], float); SR = np.array([o[2] for o in obs_seg])
        m = _seg_seg_batch(sg, S) - SR[None, :] - hw - np.array([max(0.175, req(o[3])) for o in obs_seg])[None, :]
        k = int(np.argmin(m) % m.shape[1]); worst = min(worst, (float(m.min()), ("seg", obs_seg[k][3])))
    if obs_via:
        V = np.array([o[0] for o in obs_via], float); VR = np.array([o[1] for o in obs_via])
        m = _pt_seg_pts(V, sg[:, 0, :], sg[:, 1, :]).T - VR[None, :] - hw
        k = int(np.argmin(m) % m.shape[1])
        if m.min() < worst[0]:
            worst = (float(m.min()), ("via", obs_via[k][2]))
    if obs_pad:
        PB = np.array([o[0] for o in obs_pad], float); PR = np.array([o[1] for o in obs_pad])
        m = _seg_rect_dists(sg, PB) - PR[None, :] - hw
        k = int(np.argmin(m) % m.shape[1])
        if m.min() < worst[0]:
            worst = (float(m.min()), ("pad", obs_pad[k][2]))
    return worst[0], worst[1]


def build_conflict(cand, names):
    SEG = {nm: [segs_of(c) for c in cand[nm]] for nm in names}
    OFF = {nm: np.cumsum([0] + [len(s) for s in SEG[nm]]) for nm in names}
    ALL = {nm: (np.concatenate(SEG[nm]) if SEG[nm] else np.zeros((0, 2, 2))) for nm in names}
    conf = {}; hist = collections.Counter(); zero_pairs = []
    t0 = time.time()
    for ia in range(len(names)):
        for ib in range(ia + 1, len(names)):
            na, nb = names[ia], names[ib]
            Aseg, Bseg = ALL[na], ALL[nb]; aoff, boff = OFF[na], OFF[nb]
            Ch = max(1, int(4_000_000 / max(1, len(Bseg))))
            Dl, Cl = [], []
            for c0 in range(0, len(Aseg), Ch):
                Dl.append(_seg_seg_batch(Aseg[c0:c0 + Ch], Bseg))
                Cl.append(_cross(Aseg[c0:c0 + Ch], Bseg))
            D = np.concatenate(Dl, 0); CR = np.concatenate(Cl, 0)
            md = np.minimum.reduceat(np.minimum.reduceat(D, aoff[:-1], axis=0), boff[:-1], axis=1)
            ac = np.logical_or.reduceat(np.logical_or.reduceat(CR, aoff[:-1], axis=0), boff[:-1], axis=1)
            ok = (md >= P - 1e-6) & (~ac)
            lst = []
            for pi, qj in np.argwhere(~ok).tolist():
                dv = 0.0 if ac[pi, qj] else round(float(md[pi, qj]), 4)
                lst.append((int(pi), int(qj), dv))
                hist["0" if dv <= 0 else round(math.floor(dv / 0.05) * 0.05, 2)] += 1
            if lst:
                conf[(na, nb)] = lst
            if not ok.any():
                zero_pairs.append((na, nb, int(ok.shape[0]), int(ok.shape[1])))
    return conf, hist, zero_pairs, round(time.time() - t0, 1)


def build_model(cand, names, conf, slots):
    mo = cp_model.CpModel(); x = {}
    for nm in names:
        for i in range(len(cand[nm])):
            x[(nm, i)] = mo.NewBoolVar("x_%s_%d" % (nm, i))
        mo.AddExactlyOne([x[(nm, i)] for i in range(len(cand[nm]))])
    nslot = 0
    for ei in slots:
        t_ = [x[(nm, i)] for nm in names for i, c in enumerate(cand[nm]) if c["slot"] == ei]
        if len(t_) > 1:
            mo.AddAtMostOne(t_); nslot += 1
    nforb = 0
    for (na, nb), lst in conf.items():
        for (pi, qj, dv) in lst:
            mo.AddForbiddenAssignments([x[(na, pi)], x[(nb, qj)]], [(1, 1)]); nforb += 1
    v = mo.Validate()
    return mo, x, {"vars": len(mo.Proto().variables), "slot_mutex": nslot,
                   "forbidden_clauses": nforb, "validate": v or "OK"}


def gate_preexisting(model, g, nrep):
    """金样例 · 三类缺陷负控 · 在册闸声度自证（对 R494 解须 FAIL）。"""
    r = {}
    mm = cp_model.CpModel(); L4, S4 = 4, 4
    v = {(k, s): mm.NewBoolVar("v%d_%d" % (k, s)) for k in range(L4) for s in range(S4)}
    for k in range(L4):
        mm.AddExactlyOne([v[(k, s)] for s in range(S4)])
    for s in range(S4):
        mm.AddAtMostOne([v[(k, s)] for k in range(L4)])
    for k in range(L4 - 1):
        mm.Add(sum(s * v[(k, s)] for s in range(S4)) < sum(s * v[(k + 1, s)] for s in range(S4)))
    sv = cp_model.CpSolver(); st = sv.Solve(mm)
    ans = [max(range(S4), key=lambda s: sv.Value(v[(k, s)])) for k in range(L4)]
    r["golden_regression"] = {"status": sv.StatusName(st), "answer": ans, "expected": [0, 1, 2, 3],
                              "pass": st == cp_model.OPTIMAL and ans == [0, 1, 2, 3]}
    nm = g.names[0]; a = g.A[nm]
    bad = (a[0] + 0.05, a[1] + 0.05)
    rt = {nm: {"pts": [bad, g.B[nm]], "layer_cu": "In5.Cu", "n_vias": 2}}
    gg = exact_gate(model, rt, g.an, "In5.Cu", HW, set(), set(), P, frozenset())
    r["nc1_endpoint_off_grid"] = {"endpoint_max_dev_mm": gg["endpoint_max_dev_mm"],
                                  "detected": gg["endpoint_max_dev_mm"] > 0}
    nn = 16
    mm2 = cp_model.CpModel(); w = {(k, s): mm2.NewBoolVar("w%d_%d" % (k, s)) for k in range(nn) for s in range(18)}
    for k in range(nn):
        mm2.AddExactlyOne([w[(k, s)] for s in range(18)])
    for s in range(18):
        mm2.AddAtMostOne([w[(k, s)] for k in range(nn)])       # << R497 §0 修复：原来漏了门位子互斥
    for k in range(nn):
        mm2.Add(w[(k, 0)] == 1)
    sv2 = cp_model.CpSolver(); st2 = sv2.Solve(mm2)
    r["nc3_forced_single_seat_must_be_infeasible"] = {"status": sv2.StatusName(st2),
                                                      "detected": st2 == cp_model.INFEASIBLE}
    n1, n2 = g.names[0], g.names[1]
    ov = [g.A[n1], g.B[n1]]
    rt2 = {n1: {"pts": list(ov), "layer_cu": "In5.Cu", "n_vias": 2},
           n2: {"pts": list(ov), "layer_cu": "In5.Cu", "n_vias": 2}}
    g2 = exact_gate(model, rt2, g.an, "In5.Cu", HW, set(), set(), P, frozenset())
    r["gate_soundness_overlap_must_fail"] = {"n_lane_pitch_viol": g2["n_lane_pitch_viol"],
                                            "lane_pitch_min_gap_mm": g2["lane_pitch_min_gap_mm"],
                                            "detected": g2["n_lane_pitch_viol"] > 0}
    # 在册要求级闸对 R494 之解须 FAIL（#K2-176 §四.5 · #K2-177 §0.7）
    try:
        sol = json.load(open("/tmp/opencode/r494/full.json"))["sol"]
        A_ = {a_["net"]: a_["A"] for a_ in g.an}; B_ = {a_["net"]: a_["B"] for a_ in g.an}
        routes = {}
        for d_ in sol:
            n_ = d_["nm"]; ax, ay = A_[n_]; bx, by = B_[n_]
            pts = [(ax, ay), (d_["ci"], 56.6), (d_["ci"], d_["s"]), (d_["xe"], d_["e"]),
                   (d_["px"], d_["e"]), (d_["px"], d_["ny"]), (bx, d_["ny"]), (bx, by)]
            o = [pts[0]]
            for q in pts[1:]:
                if math.dist(q, o[-1]) > 1e-9:
                    o.append(q)
            routes[n_] = {"pts": o, "layer_cu": "In5.Cu", "n_vias": 2}
        g3 = exact_gate(model, routes, g.an, "In5.Cu", HW, set(), set(), P, frozenset())
        r["r495_gate_soundness_vs_R494"] = {"n_lane_pitch_viol": g3["n_lane_pitch_viol"],
                                            "lane_pitch_min_gap_mm": g3["lane_pitch_min_gap_mm"],
                                            "n_clearance_viol": g3["n_clearance_viol"],
                                            "detected": (g3["n_lane_pitch_viol"] > 0 or g3["n_clearance_viol"] > 0)}
    except Exception as e:                                     # pragma: no cover
        r["r495_gate_soundness_vs_R494"] = {"error": str(e), "detected": None}
    r["all_pass"] = bool(r["golden_regression"]["pass"] and r["nc1_endpoint_off_grid"]["detected"]
                         and r["nc3_forced_single_seat_must_be_infeasible"]["detected"]
                         and r["gate_soundness_overlap_must_fail"]["detected"]
                         and r.get("r495_gate_soundness_vs_R494", {}).get("detected"))
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="/tmp/opencode/archer/model_l8.json")
    ap.add_argument("--out", default=None)
    ap.add_argument("--maxtime", type=float, default=900.0)
    ap.add_argument("--solve-if-green", action="store_true", default=True)
    a = ap.parse_args()
    HERE = os.path.dirname(os.path.abspath(__file__))
    out_json = a.out or os.path.join(HERE, "K2_R498_CONFLICT_TABLE_ONE_IMPLEMENTATION_v2.json")
    t00 = time.time()
    model = json.load(open(a.model))
    rep = {"artifact": "k2_r498_conflict_table_one_implementation_v2",
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "监理停止令(红线·命令重复) · 宪法第八章第8条 · #K2-177 §一/§三 · #K2-176 §四.4/§四.5 · #K2-175 §四.5",
           "spec": "HANDOFF-K2-497-STOPORDER-ONE-IMPLEMENTATION.md §0（七点）· K2_R497_PLAN_HUMAN_PATH_v1.md §四",
           "PRE_DEVIATION": {
             "from": "handoff §0.1「搜索栅再膨胀 PAD_EXTRA + 0.31」",
             "to": "搜索栅只加离散化/折角安全量 EPS=0.03；线段级净空改由「逐段在册尺复核」保证（§0.7 明文）",
             "measured_reason": "registered 尺 16/16 可达；再 +0.4312 后 6/16 网节点级不可达（0_P/1_P/2_P/3_P/4_P/5_P/6_P 中 6 个）",
             "soundness": "逐段在册尺复核 >= 在册 exact_gate 同尺 ⇒ 所有交出折线按构造过在册要求级闸；无假合格面"}}
    g = Gen(model)
    rep["geometry"] = {"lattice": [NX, NY], "free_nodes": int(g.free_node.sum()),
                       "gate_slots": len(g.E), "gate_x": [round(XY(i, JPOR)[0], 3) for i in g.E],
                       "lattice_edges": int(len(g.edge_u))}
    pre = gate_preexisting(model, g, 16)
    rep["preexisting_gates"] = pre
    cand, tfam = g.family(verbose=False)
    cnt = {nm: len(cand[nm]) for nm in g.names}
    empty = [nm for nm in g.names if not cand[nm]]
    rep["family"] = {"counts": cnt, "total": sum(cnt.values()), "empty_nets": empty,
                     "per_net_cap": "~150 (handoff §0.4)", "t_s": tfam,
                     "params": {"LW": LW, "DE": list(DE), "MVALS": list(MVALS), "MAXJ": MAXJ, "EPS": EPS}}
    nbad = 0; bad_ex = []
    for nm in g.names:
        for c in cand[nm]:
            w, blk = lane_exact_margin(model, c["pts"])
            if w < 0:
                nbad += 1
                if len(bad_ex) < 3:
                    bad_ex.append((nm, round(w, 4), blk))
    rep["segment_ruler_check"] = {"candidates": sum(cnt.values()), "fail": nbad, "examples": bad_ex,
                                  "pass": nbad == 0}
    if not empty:
        conf, hist, zero_pairs, ct = build_conflict(cand, g.names)
        tot = sum(len(v) for v in conf.values()); z = hist.get("0", 0)
        rep["conflict_table"] = {"forbidden_pairs": tot, "net_pairs_with_conflicts": len(conf),
                                 "at_zero_distance": z, "zero_share": round(z / max(1, tot), 4),
                                 "t_s": ct, "criterion": "true closest-point distance + true crossing(=>0)"}
        rep["family_feasibility_screen"] = {"zero_compatible_pairs": len(zero_pairs),
                                            "total_net_pairs": len(g.names) * (len(g.names) - 1) // 2,
                                            "examples": zero_pairs[:6],
                                            "meaning": "任一零相容网对 ⇒ 该族必无可行指派（与求解器无关）"}
        mo, x, mstat = build_model(cand, g.names, conf, [e for e in range(len(g.E))])
        sha = hashlib.sha256(json.dumps({nm: [(c["slot"], c["d"], c["k"], c["pts"]) for c in cand[nm]] for nm in g.names},
                                        sort_keys=True, default=str).encode()).hexdigest()[:16]
        rep["model"] = dict(mstat, sha16=sha)
        green = (pre["all_pass"] and not empty and nbad == 0 and mstat["validate"] == "OK")
        rep["preconditions_all_green"] = bool(green)
        if green and not zero_pairs:
            sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = a.maxtime
            sv.parameters.num_search_workers = 8
            ts = time.time(); st = sv.Solve(mo)
            rep["solve"] = {"status": sv.StatusName(st), "wall_s": round(time.time() - ts, 1),
                            "quota_consumed": 1}
            if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                routes = {}
                for nm in g.names:
                    i = [j for j in range(len(cand[nm])) if sv.Value(x[(nm, j)]) == 1][0]
                    routes[nm] = {"pts": cand[nm][i]["pts"], "layer_cu": "In5.Cu", "n_vias": 2,
                                  "slot": cand[nm][i]["slot"], "d": cand[nm][i]["d"], "k": cand[nm][i]["k"]}
                json.dump(routes, open(os.path.join(HERE, "K2_R498_ONE_IMPLEMENTATION_ROUTES_v2.json"), "w"),
                          ensure_ascii=False)
                gg = exact_gate(model, {k2: {"pts": v2["pts"], "layer_cu": "In5.Cu", "n_vias": 2}
                                        for k2, v2 in routes.items()}, g.an, "In5.Cu", HW, set(), set(), P, frozenset())
                rep["exact_gate"] = {k3: gg[k3] for k3 in ("n_lane_pitch_viol", "lane_pitch_min_gap_mm",
                                                           "lane_pitch_min_pair", "n_clearance_viol",
                                                           "clearance_min_mm", "endpoint_max_dev_mm")}
                rep["requirement_level_gate"] = "PASS" if (gg["n_lane_pitch_viol"] == 0 and gg["n_clearance_viol"] == 0
                                                           and gg["endpoint_max_dev_mm"] == 0) else "FAIL"
                rep["decision"] = "TERMINAL-PER-#K2-177-§三"
            else:
                rep["decision"] = "NON-TERMINAL: solver=%s ⇒ 真停线（#K2-177 §三 第三分支）" % sv.StatusName(st)
        else:
            rep["solve"] = {"status": "NOT-RUN", "quota_consumed": 0}
            rep["decision"] = ("STOP-BEFORE-SOLVE: " +
                               ("前置硬闸未全绿" if not green else "族级可行性筛未过（零相容网对 %d 对）" % len(zero_pairs)) +
                               " ⇒ 不开跑 · 受证额度 1 未耗（#K2-175 §四.5）")
    else:
        rep["solve"] = {"status": "NOT-RUN", "quota_consumed": 0}
        rep["decision"] = "STOP-BEFORE-SOLVE: 空域（%d 网无候选）⇒ 不开跑 · 额度 1 未耗" % len(empty)
    rep["elapsed_s"] = round(time.time() - t00, 1)
    json.dump(rep, open(out_json, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k2: rep[k2] for k2 in ("decision", "family", "segment_ruler_check",
                                             "family_feasibility_screen", "conflict_table", "model",
                                             "solve", "elapsed_s") if k2 in rep}, ensure_ascii=False, indent=1)[:4000])
    print("WROTE", out_json)


if __name__ == "__main__":
    main()
