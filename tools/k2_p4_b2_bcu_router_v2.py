#!/usr/bin/env python3
"""K2 · (a) B.Cu 收紧版 —— **配对守恒**布线器 v2（A_x→B_x）· 协商拥塞 + rip-up（确定性）。

背景（2026-09-21 · R126）：`k2_p4_b2_bcu_router_v1.py --algo maxflow` 之输出**不是可施工工作令**：
单商品最大流只保证『A 集合↔B 集合间存在 32 条节点不相交路径』，**不保证 A_x 接 B_x**
（实测 R3K 工作令 **30/32 误配**）⇒ v1 客户套用后靠长 stub 强行接回本网 ⇒ 车道互短/交叉。
本器 = **按网配对**（每网 A_x→B_x）之合法求解器（协商拥塞 + 全量 rip-up）。

口径（与判据一致）：
- 障碍 = B.Cu 上**其他网**铜（线/孔/盘；含 5 个可腾挪网之**孔/盘**，仅其**走线**可挪）
  + 32 条车道之**固定锚孔**（V1/V4；他网车道孔须避让）+ 禁布线区；
- 间隙 = `max(0.175, req(net))`（板 netclass max 规则：PCIe85 0.175 / POWER 0.2 / Default 0.1），
  孔到铜另受 0.25 下限约束；
- 车道线宽 0.205；两两中心距门 **0.38mm** ⇒ 栅格 cell 0.2 / stamp R=1 ⇒ 最小中心距 0.4mm；
- 违规判定 = 某车道**路径格**被 ≥2 个车道之 3x3 stamp 覆盖（⇔ 与他车道路径 Chebyshev ≤1）。

CLI:
  python3 k2/tools/k2_p4_b2_bcu_router_v2.py --model <dump.json> --out <workorder.json> \
      [--cell 0.2] [--iters 16] [--movable-nets a,b,c] [--seed 7] [--no-gate]
"""
from __future__ import annotations
import argparse, json, math, sys

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from k2_p4_b2_in5_capacity_probe_v1 import req, is_lane  # noqa: E402
from k2_p4_b2_bcu_router_v1 import _seg_seg, _seg_rect, _pt_seg, LANE_W  # noqa: E402

LANE_HW = LANE_W / 2.0         # 0.1025
PITCH = 0.38                   # 两两中心距门（= w + 边到边 req 0.175）
EFF_MIN = 0.175                # PCIe85 netclass 间隙（板 netclass max 规则下限）
HOLE_CLR = 0.25                # board.rules min_hole_clearance
NBR = ((1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
       (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2)), (-1, 1, math.sqrt(2)), (-1, -1, math.sqrt(2)))


def eff(net):
    """车道（PCIe85）与 net 之有效边到边间隙 = max(PCIe85 0.175, netclass(net))。"""
    return max(EFF_MIN, req(net))


class Raster:
    def __init__(self, model, step=0.20):
        x0, y0, x1, y1 = model["bbox"]
        self.X0, self.Y0, self.step = x0, y0, step
        self.NX = int((x1 - x0) / step) + 1
        self.NY = int((y1 - y0) / step) + 1
        XS = x0 + np.arange(self.NX) * step
        YS = y0 + np.arange(self.NY) * step
        self.GX, self.GY = np.meshgrid(XS, YS, indexing="ij")

    def _win(self, ax, ay, bx, by, rad):
        i0 = max(0, int((min(ax, bx) - rad - self.X0) / self.step))
        i1 = min(self.NX - 1, int((max(ax, bx) + rad - self.X0) / self.step) + 1)
        j0 = max(0, int((min(ay, by) - rad - self.Y0) / self.step))
        j1 = min(self.NY - 1, int((max(ay, by) + rad - self.Y0) / self.step) + 1)
        return i0, i1, j0, j1

    def seg(self, arr, ax, ay, bx, by, rad):
        i0, i1, j0, j1 = self._win(ax, ay, bx, by, rad)
        if i1 < i0 or j1 < j0:
            return
        X = self.GX[i0:i1 + 1, j0:j1 + 1]; Y = self.GY[i0:i1 + 1, j0:j1 + 1]
        dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
        t = np.zeros_like(X) if L2 == 0 else np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
        arr[i0:i1 + 1, j0:j1 + 1] |= (np.hypot(X - (ax + t * dx), Y - (ay + t * dy)) < rad)

    def cir(self, arr, cx, cy, rad, add=False):
        i0, i1, j0, j1 = self._win(cx, cy, cx, cy, rad)
        if i1 < i0 or j1 < j0:
            return
        X = self.GX[i0:i1 + 1, j0:j1 + 1]; Y = self.GY[i0:i1 + 1, j0:j1 + 1]
        m = np.hypot(X - cx, Y - cy) < rad
        if add:
            arr[i0:i1 + 1, j0:j1 + 1] += m
        else:
            arr[i0:i1 + 1, j0:j1 + 1] |= m

    def rect(self, arr, x0, y0, x1, y1, rad):
        i0, i1, j0, j1 = self._win(x0, y0, x1, y1, rad)
        if i1 < i0 or j1 < j0:
            return
        X = self.GX[i0:i1 + 1, j0:j1 + 1]; Y = self.GY[i0:i1 + 1, j0:j1 + 1]
        dx = np.maximum(np.maximum(x0 - X, 0), X - x1); dy = np.maximum(np.maximum(y0 - Y, 0), Y - y1)
        arr[i0:i1 + 1, j0:j1 + 1] |= (np.hypot(dx, dy) < rad)

    def poly(self, arr, pts):
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        i0, i1, j0, j1 = self._win(min(xs), min(ys), max(xs), max(ys), 0.0)
        if i1 < i0 or j1 < j0:
            return
        sub = arr[i0:i1 + 1, j0:j1 + 1]
        X = self.GX[i0:i1 + 1, j0:j1 + 1].ravel(); Y = self.GY[i0:i1 + 1, j0:j1 + 1].ravel()
        inside = np.zeros(X.shape, dtype=bool)
        n = len(pts)
        for k in range(n):
            x1_, y1_ = pts[k]; x2_, y2_ = pts[(k + 1) % n]
            cond = ((y1_ > Y) != (y2_ > Y))
            with np.errstate(divide="ignore", invalid="ignore"):
                xin = (x2_ - x1_) * (Y - y1_) / (y2_ - y1_) + x1_
            inside ^= cond & (X < xin)
        sub |= inside.reshape(sub.shape)

    def cell(self, x, y):
        return int(round((x - self.X0) / self.step)), int(round((y - self.Y0) / self.step))


def lane_anchors(model):
    """A = F.Cu–B.Cu 孔（SoC 侧）· B = F.Cu–In2.Cu 孔（连接器侧）。"""
    L = {}
    for v in model["vias"]:
        nm = v["net"]
        if not is_lane(nm):
            continue
        L.setdefault(nm, {})["%s-%s" % (v["top"], v["bot"])] = (v["x"], v["y"], v["r"], v["drill"])
    out = []
    for nm in sorted(L):
        a, b = L[nm].get("F.Cu-B.Cu"), L[nm].get("F.Cu-In2.Cu")
        assert a and b, nm
        out.append({"net": nm, "A": a[:2], "B": b[:2], "via_r": max(a[2], b[2]), "drill": max(a[3], b[3])})
    return out


def build_base(rast, model, movable_tracks, movable_vias=()):
    """静态障碍（不含车道锚孔）：其他网铜 + 可腾挪网之孔/盘 + 禁布线区。"""
    bad = np.zeros((rast.NX, rast.NY), dtype=bool)
    for s in model["segs"]["B.Cu"]:
        net = s[5]
        if is_lane(net) or net in movable_tracks:
            continue
        rast.seg(bad, s[0], s[1], s[2], s[3], LANE_HW + s[4] + eff(net))
    for v in model["vias"]:
        if "B.Cu" not in v["layers"]:
            continue
        net = v["net"]
        if is_lane(net) or net in movable_vias:
            continue
        rad = max(v["r"] + eff(net), v["drill"] + HOLE_CLR)
        rast.cir(bad, v["x"], v["y"], LANE_HW + rad)
    for p in model["pads"]:
        if is_lane(p["net"]) or p["net"] in movable_vias:
            continue
        if "B.Cu" not in p["layers"] and not p["pth"]:
            continue
        b = p["box"]
        rast.rect(bad, b[0], b[1], b[2], b[3], LANE_HW + eff(p["net"]))
        if p["pth"] and p.get("drill"):
            rast.cir(bad, p["cx"], p["cy"], LANE_HW + p["drill"] + HOLE_CLR)
    for ra in model["ruleareas"]:
        if not (ra["no_tracks"] and "B.Cu" in ra["layers"]):
            continue
        for poly in ra["polys"]:
            rast.poly(bad, poly)
    return bad


def build_via_counts(rast, anchors):
    """32 条车道固定锚孔（V1/V4）之占位计数：c_all 与每网 own。"""
    c_all = np.zeros((rast.NX, rast.NY), dtype=np.int16)
    own = {}
    for an in anchors:
        rad = LANE_HW + max(EFF_MIN + an["via_r"], an["drill"] + HOLE_CLR)
        c_all_local = np.zeros((rast.NX, rast.NY), dtype=bool)
        rast.cir(c_all_local, an["A"][0], an["A"][1], rad)
        rast.cir(c_all_local, an["B"][0], an["B"][1], rad)
        c_all += c_all_local.astype(np.int16)
        own[an["net"]] = c_all_local
    return c_all, own


def snap_free(rast, bad, pt, max_r=8):
    ci, cj = rast.cell(*pt)
    best = None
    for r in range(0, max_r + 1):
        for di in range(-r, r + 1):
            for dj in range(-r, r + 1):
                if max(abs(di), abs(dj)) != r:
                    continue
                i, j = ci + di, cj + dj
                if 0 <= i < rast.NX and 0 <= j < rast.NY and not bad[i, j]:
                    d = di * di + dj * dj
                    if best is None or d < best[0]:
                        best = (d, i, j)
        if best is not None:
            return best[1], best[2]
    return None, None


def build_graph(allowed, pen, step):
    idx = np.full(allowed.shape, -1, np.int32)
    ii, jj = np.nonzero(allowed)
    n = len(ii)
    idx[ii, jj] = np.arange(n, dtype=np.int32)
    rows, cols, data = [], [], []
    NX, NY = allowed.shape
    for di, dj, dl in NBR:
        ni = ii + di; nj = jj + dj
        m = (ni >= 0) & (ni < NX) & (nj >= 0) & (nj < NY)
        if not m.any():
            continue
        tgt = idx[ni[m], nj[m]]
        ok = tgt >= 0
        if not ok.any():
            continue
        src = np.arange(n, dtype=np.int32)[m][ok]
        rows.append(src); cols.append(tgt[ok])
        data.append(dl * step + pen[ni[m][ok], nj[m][ok]])
    return csr_matrix((np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n)), idx, (ii, jj)


def path_from_pred(pred, s, g):
    if s != g and pred[g] < 0:
        return None
    out = [g]; cur = g
    while cur != s:
        cur = int(pred[cur])
        if cur < 0:
            return None
        out.append(cur)
    out.reverse()
    return out


def simplify(pts):
    if len(pts) < 3:
        return pts
    out = [pts[0]]
    for k in range(1, len(pts) - 1):
        a, b, c = out[-1], pts[k], pts[k + 1]
        d1 = (b[0] - a[0], b[1] - a[1]); d2 = (c[0] - b[0], c[1] - b[1])
        if d1[0] * d2[1] - d1[1] * d2[0] != 0 or d1[0] * d2[0] + d1[1] * d2[1] <= 0:
            out.append(b)
    out.append(pts[-1])
    return out


def exact_gate(model, routes, movable_tracks, anchors):
    """**连续几何精确闸**（不依赖栅格）：① 车道两两中心距 ≥ 0.38 ② 车道 vs 他网铜（含锚孔）≥ eff ③ 端点=锚孔。"""
    segs = {}
    for nm, r in routes.items():
        p = [tuple(q) for q in r["pts"]]
        segs[nm] = [((p[k][0], p[k][1]), (p[k + 1][0], p[k + 1][1])) for k in range(len(p) - 1)]
    names = sorted(segs)
    pair_min = (1e9, None); viol_pair = []
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            best = 1e9
            for (A1, A2) in segs[names[a]]:
                for (B1, B2) in segs[names[b]]:
                    d = _seg_seg(A1, A2, B1, B2)
                    if d < best:
                        best = d
            gap = best - LANE_W
            if gap < pair_min[0]:
                pair_min = (gap, (names[a], names[b]))
            if gap < EFF_MIN - 1e-6:
                viol_pair.append((names[a], names[b], round(gap, 4)))
    obs = []
    for s in model["segs"]["B.Cu"]:
        net = s[5]
        if is_lane(net) or net in movable_tracks:
            continue
        obs.append(("seg", ((s[0], s[1]), (s[2], s[3])), s[4], net))
    for v in model["vias"]:
        if "B.Cu" not in v["layers"]:
            continue
        obs.append(("via", ((v["x"], v["y"]), (v["x"], v["y"])), v["r"], v["net"]))
    for p in model["pads"]:
        if "B.Cu" not in p["layers"] and not p["pth"]:
            continue
        obs.append(("pad", p["box"], 0.0, p["net"]))

    def obs_dist(geo, kind, A, B):
        if kind == "seg":
            return _seg_seg(A, B, geo[0], geo[1])
        if kind == "via":
            return _pt_seg(geo[0][0], geo[0][1], A[0], A[1], B[0], B[1])
        return _seg_rect(A, B, geo[:2], geo[2:])

    per_lane = {}; viol_obs = []
    for nm in names:
        worst = (1e9, None); own = nm
        for (A1, A2) in segs[nm]:
            for (kind, geo, rr, net) in obs:
                if is_lane(net):
                    if net == own:
                        continue                       # 本网锚孔可接
                    need = max(EFF_MIN, req(net))
                    m = obs_dist(geo, kind, A1, A2) - rr - LANE_HW - need
                    if m < worst[0]:
                        worst = (m, net)
                    if m < -1e-6:
                        viol_obs.append((nm, net, "via", round(m, 4)))
                    continue
                if net in movable_tracks:
                    continue                           # 可腾挪网之走线（其孔/盘下面单独算）
                need = eff(net)
                m = obs_dist(geo, kind, A1, A2) - rr - LANE_HW - need
                if m < worst[0]:
                    worst = (m, net)
                if m < -1e-6:
                    viol_obs.append((nm, net, kind, round(m, 4)))
        per_lane[nm] = {"margin_min_mm": round(worst[0], 4), "blocker": worst[1]}
    per_lane2 = {}
    for nm in names:
        worst = (1e9, None)
        for (A1, A2) in segs[nm]:
            for (kind, geo, rr, net) in obs:
                if is_lane(net):
                    continue
                if net not in movable_tracks:
                    continue                           # 已在上段算过
                need = max(EFF_MIN, req(net))
                m = obs_dist(geo, kind, A1, A2) - rr - LANE_HW - need
                if m < worst[0]:
                    worst = (m, net)
                if m < -1e-6:
                    viol_obs.append((nm, net, kind, round(m, 4)))
        per_lane2[nm] = {"margin_min_mm": round(worst[0], 4), "blocker": worst[1]}
    ends = {}
    for an in anchors:
        if an["net"] not in routes:
            continue
        p = routes[an["net"]]["pts"]
        ends[an["net"]] = round(max(math.dist(p[0], an["A"]), math.dist(p[-1], an["B"])), 4)
    allmin = min(list(v["margin_min_mm"] for v in per_lane.values()) + list(v["margin_min_mm"] for v in per_lane2.values()))
    return {"lane_pitch_min_gap_mm": round(pair_min[0], 4), "lane_pitch_min_pair": pair_min[1],
            "lane_pitch_violations": viol_pair[:20], "n_lane_pitch_viol": len(viol_pair),
            "clearance_min_mm": round(allmin, 4), "clearance_violations": viol_obs[:20],
            "n_clearance_viol": len(viol_obs), "endpoint_max_dev_mm": max(ends.values()) if ends else None,
            "per_lane": {k: v for k, v in per_lane.items()}, "per_lane_via_only": per_lane2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cell", type=float, default=0.20)
    ap.add_argument("--iters", type=int, default=16)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--pf0", type=float, default=0.4)
    ap.add_argument("--hf", type=float, default=0.15)
    ap.add_argument("--movable-nets", default="", help="可腾挪网：其**走线**不计入障碍")
    ap.add_argument("--movable-stitch", default="", help="可腾挪网：其**孔/盘**亦不计入障碍（缝合孔腾挪场景）")
    ap.add_argument("--no-gate", action="store_true")
    ap.add_argument("--repair", type=int, default=0, help="协商后 rip-up-and-reroute 修复轮数（违例车道重布）")
    ap.add_argument("--algo", default="negotiate", choices=["negotiate", "hard"],
                    help="negotiate=协商软化（过用罚递增）；hard=严格硬带（cnt>=1 禁行）+ 失败优先 rip-up")
    a = ap.parse_args()
    model = json.load(open(a.model))
    movable = set(x for x in a.movable_nets.split(",") if x)
    rast = Raster(model, step=a.cell)
    movable_vias = set(x for x in a.movable_stitch.split(",") if x)
    base = build_base(rast, model, movable, movable_vias)
    anchors = lane_anchors(model)
    c_all, own = build_via_counts(rast, anchors)
    R = max(1, int(round(PITCH / a.cell)) - 1)
    rng = np.random.RandomState(a.seed)

    tasks = []
    for an in anchors:
        bad = base | ((c_all.astype(np.int32) - own[an["net"]].astype(np.int32)) > 0)
        s = snap_free(rast, bad, an["A"]); g = snap_free(rast, bad, an["B"])
        tasks.append({"an": an, "bad": bad, "status": "PENDING" if s[0] is not None and g[0] is not None else "NO_FREE_ENDPOINT",
                      "s": s, "g": g})
    print("车道 %d · 栅格 %dx%d cell=%.2f · stamp R=%d · 自由端点 %d" %
          (len(tasks), rast.NX, rast.NY, a.cell, R, sum(1 for t in tasks if t["status"] == "PENDING")))

    def route_cells(t, blocker, pen, hard=False):
        allowed = ~t["bad"]
        if hard:
            allowed = allowed & ~blocker
        G, idx, cells = build_graph(allowed, pen, a.cell)
        si = idx[t["s"]]; gi = idx[t["g"]]
        if si < 0 or gi < 0:
            return None
        dist, pred = dijkstra(G, directed=True, indices=int(si), return_predecessors=True)
        dv = dist[0] if dist.ndim == 2 else dist
        pv = pred[0] if pred.ndim == 2 else pred
        if not np.isfinite(dv[gi]):
            return None
        path = path_from_pred(pv, int(si), int(gi))
        if not path:
            return None
        return [(int(cells[0][k]), int(cells[1][k])) for k in path]

    def footprints(paths):
        m = np.zeros((rast.NX, rast.NY), dtype=np.float32)
        for nm, pts in paths.items():
            for (i, j) in pts:
                m[max(0, i - R):i + R + 1, max(0, j - R):j + R + 1] += 1.0
        return m

    def n_viol(paths):
        m = footprints(paths)
        v = 0
        for nm, pts in paths.items():
            for (i, j) in pts:
                if m[i, j] >= 2.0:
                    v += 1
        return v

    hist = np.zeros((rast.NX, rast.NY), dtype=np.float32)
    best = None
    routed_best_names = []
    pf = a.pf0
    for it in range(a.iters):
        cnt = np.zeros((rast.NX, rast.NY), dtype=np.float32)
        routed = {}
        prev_routed = set(routed_best_names) if it else set()
        order = sorted(range(len(tasks)), key=lambda i: -math.dist(tasks[i]["an"]["A"], tasks[i]["an"]["B"]))
        if it > 0:
            if a.algo == "hard":
                prev = prev_routed if it > 1 else []
                order = [i for i in order if tasks[i]["an"]["net"] in prev] + [i for i in order if tasks[i]["an"]["net"] not in prev]
            rng.shuffle(order)
        for t_i in order:
            t = tasks[t_i]
            if t["status"] != "PENDING":
                continue
            pen = pf * cnt + a.hf * hist      # 占位=路径的 R 邻域 ⇒ 任何重叠即过近（须整格避让）
            allowed = ~t["bad"]
            if a.algo == "hard":
                allowed = allowed & (cnt == 0.0)
            G, idx, cells = build_graph(allowed, pen, a.cell)
            si = idx[t["s"]]; gi = idx[t["g"]]
            if si < 0 or gi < 0:
                continue
            dist, pred = dijkstra(G, directed=True, indices=int(si), return_predecessors=True)
            dv = dist[0] if dist.ndim == 2 else dist
            pv = pred[0] if pred.ndim == 2 else pred
            if not np.isfinite(dv[gi]):
                continue
            path = path_from_pred(pv, int(si), int(gi))
            if not path:
                continue
            pts = [(int(cells[0][k]), int(cells[1][k])) for k in path]
            routed[t["an"]["net"]] = pts
            mask = np.zeros((rast.NX, rast.NY), dtype=bool)   # 本车道占位 = 路径的 R 邻域（按**车道**计数）
            for (i, j) in pts:
                mask[max(0, i - R):i + R + 1, max(0, j - R):j + R + 1] = True
            cnt += mask
        viol = 0
        for nm, pts in routed.items():
            for (i, j) in pts:
                if cnt[i, j] >= 2.0:      # 本车道**路径格**被他车道占位覆盖 ⇒ 违例
                    viol += 1
        score = (len(routed), -viol)
        print("  [it %2d] routed=%2d/%d 违规格=%5d pf=%.2f" % (it, len(routed), len(tasks), viol, pf))
        if best is None or score > best[0]:
            best = (score, {k: list(v) for k, v in routed.items()})
            routed_best_names = list(routed.keys())
        if len(routed) == len(tasks) and viol == 0:
            break
        hist += np.maximum(cnt - 1.0, 0.0)
        pf *= 2.0
    routed = best[1]
    # ---- rip-up-and-reroute 修复（针对违例车道）----
    zpen = np.zeros((rast.NX, rast.NY), dtype=np.float32)
    for rep in range(a.repair):
        if not routed:
            break
        fp = footprints(routed)
        bad_lanes = [nm for nm, pts in routed.items() if any(fp[i, j] >= 2.0 for (i, j) in pts)]
        if not bad_lanes:
            break
        for nm in bad_lanes:
            del routed[nm]
        fp = footprints(routed)
        cur = n_viol(routed)
        for nm in bad_lanes:
            t = next(t for t in tasks if t["an"]["net"] == nm)
            p = route_cells(t, fp > 0, zpen, hard=True)
            if p is None:
                p = route_cells(t, fp > 0, pf * fp, hard=False)
            if p is None:
                p = route_cells(t, None, zpen, hard=False)
            if p is None:
                continue
            routed[nm] = p
            for (i, j) in p:
                fp[max(0, i - R):i + R + 1, max(0, j - R):j + R + 1] += 1.0
        nv = n_viol(routed)
        if rep % 5 == 0 or nv == 0:
            print("  [repair %3d] vio=%5d (lanes ripped %d)" % (rep, nv, len(bad_lanes)))
        if nv == 0 and len(routed) == len(tasks):
            break
        if nv >= cur and rep > 3:
            pass
    if a.repair:
        print("  [repair 终] routed=%d/%d vio=%d" % (len(routed), len(tasks), n_viol(routed)))

    routes = {}
    for an in anchors:
        nm = an["net"]
        if nm not in routed:
            continue
        pts = [an["A"]] + [(rast.X0 + i * a.cell, rast.Y0 + j * a.cell) for (i, j) in routed[nm]] + [an["B"]]
        pts = simplify(pts)
        routes[nm] = {"pts": [[round(x, 4), round(y, 4)] for (x, y) in pts],
                      "len_mm": round(sum(math.dist(pts[k], pts[k + 1]) for k in range(len(pts) - 1)), 3)}
    gate = None
    if not a.no_gate and routes:
        gate = exact_gate(model, routes, movable, anchors)
        print("  [精确闸] 车道两两最小间隙 %.4f（违规 %d）· 障碍最小余量 %.4f（违规 %d）· 端点最大偏移 %s" %
              (gate["lane_pitch_min_gap_mm"], gate["n_lane_pitch_viol"], gate["clearance_min_mm"],
               gate["n_clearance_viol"], gate["endpoint_max_dev_mm"]))
    wo = {"artifact": "k2_p4_b2_bcu_router_v2_workorder", "algo": "paired_pathfinder",
          "cell_mm": a.cell, "lane_w_mm": LANE_W, "pitch_mm": PITCH, "stamp_R": R,
          "model": a.model, "movable_nets": sorted(movable), "n_lanes": len(anchors),
          "n_routed": len(routes), "failed": sorted(t["an"]["net"] for t in tasks if t["an"]["net"] not in routes),
          "routes": routes, "cell_paths": {k: [[int(i), int(j)] for (i, j) in v] for k, v in routed.items()},
          "geometric_gate": gate,
          "note": "配对守恒（A_x→B_x 逐网）；无 stub 拉线（首末点=锚孔中心）"}
    json.dump(wo, open(a.out, "w"), ensure_ascii=False, indent=1, sort_keys=True)
    print("routed %d/%d · failed=%s" % (len(routes), len(anchors), wo["failed"]))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
