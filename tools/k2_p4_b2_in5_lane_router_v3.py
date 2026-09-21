#!/usr/bin/env python3
"""K2 · B2 —— **In5 车道布线器 v3**：精确各向同性净距（非 Chebyshev stamp）· 协商拥塞 + rip-up + 硬修复。

缘起（2026-09-21 · R-A 无见证归因）：
  `k2_p4_b2_bcu_router_v2.py` 之力场为 **3x3/方形 stamp**（Chebyshev），且 `cell 0.1 + stamp R=3`
  ⇒ 实强制 **0.4mm 方形**中心距（对角实际 0.566mm），远严于 In5 实需 **0.335mm（0.16+0.175）** 各向同性
  ⇒ 0.05–0.24mm 级锚间通道被系统性误封 ⇒ "违规格" 恒不收敛，R-A 无法出见证。本器替换为：
    · **各向同性圆盘占位**（半径 = 目标中心距 PITCH，默认 0.335mm）+ 更细栅格（默认 0.1mm）；
    · 障碍膨胀按网逐项 `max(0.175, netclass)` + 孔到铜 0.25（与 DRC 实测口径一致）；
    · 协商软罚 + 全量 rip-up + 违例车道硬修复（rip-up-and-reroute）；
    · 末闸 = **连续几何精确闸**（逐段精确距离，层取本器 `--layer`，修正 v2 之 B.Cu 硬编码缺陷）。

口径：间隙 = `max(0.175, req(net))`；车道线宽默认 0.16（In5）；车道两两中心距 ≥ `--pitch`（默认 0.335）。
输出：工作令 JSON（含 routes / cell_paths / geometric_gate），**只读板件**。

CLI：
  python3 tools/k2_p4_b2_in5_lane_router_v3.py --model <dump.json> --out <wo.json> \
      [--layer In5.Cu] [--cell 0.10] [--lane-w 0.16] [--pitch 0.335] [--iters 12] \
      [--a-sites a.json] [--b-sites b.json] [--movable-nets ...] [--movable-stitch ...] [--seed 7]
"""
from __future__ import annotations
import argparse, json, math, sys
import numpy as np
from scipy import ndimage
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from k2_p4_b2_in5_capacity_probe_v1 import req, is_lane  # noqa: E402

EFF_MIN = 0.175
HOLE_CLR = 0.25
NBR = ((1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
       (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2)), (-1, 1, math.sqrt(2)), (-1, -1, math.sqrt(2)))


def eff(net):
    return max(EFF_MIN, req(net))


class Raster:
    def __init__(self, bbox, step):
        x0, y0, x1, y1 = bbox
        self.X0, self.Y0, self.step = x0, y0, step
        self.NX = int((x1 - x0) / step) + 2
        self.NY = int((y1 - y0) / step) + 2
        XS = x0 + np.arange(self.NX) * step
        YS = y0 + np.arange(self.NY) * step
        self.GX, self.GY = np.meshgrid(XS, YS, indexing="ij")

    def _win(self, ax, ay, bx, by, rad):
        i0 = max(0, int((min(ax, bx) - rad - self.X0) / self.step))
        i1 = min(self.NX - 1, int((max(ax, bx) + rad - self.X0) / self.step) + 1)
        j0 = max(0, int((min(ay, by) - rad - self.Y0) / self.step))
        j1 = min(self.NY - 1, int((max(ay, by) + rad - self.Y0) / self.step) + 1)
        return i0, i1, j0, j1

    def seg(self, arr, ax, ay, bx, by, rad, mode="or"):
        i0, i1, j0, j1 = self._win(ax, ay, bx, by, rad)
        if i1 < i0 or j1 < j0:
            return
        X = self.GX[i0:i1 + 1, j0:j1 + 1]; Y = self.GY[i0:i1 + 1, j0:j1 + 1]
        dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
        t = np.zeros_like(X) if L2 == 0 else np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
        m = (np.hypot(X - (ax + t * dx), Y - (ay + t * dy)) < rad)
        if mode == "or":
            arr[i0:i1 + 1, j0:j1 + 1] |= m
        else:
            arr[i0:i1 + 1, j0:j1 + 1] += m

    def cir(self, arr, cx, cy, rad, mode="or"):
        i0, i1, j0, j1 = self._win(cx, cy, cx, cy, rad)
        if i1 < i0 or j1 < j0:
            return
        X = self.GX[i0:i1 + 1, j0:j1 + 1]; Y = self.GY[i0:i1 + 1, j0:j1 + 1]
        m = (np.hypot(X - cx, Y - cy) < rad)
        if mode == "or":
            arr[i0:i1 + 1, j0:j1 + 1] |= m
        else:
            arr[i0:i1 + 1, j0:j1 + 1] += m

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
            xa, ya = pts[k]; xb, yb = pts[(k + 1) % n]
            cond = ((ya > Y) != (yb > Y))
            with np.errstate(divide="ignore", invalid="ignore"):
                xin = (xb - xa) * (Y - ya) / (yb - ya) + xa
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


def build_base(rast, model, layer, movable_tracks, movable_vias, hw):
    """静态障碍（不含车道锚孔）：其他网铜 + 可腾挪网之孔/盘 + 禁布线区；净距 = hw + max(0.175, req)。"""
    bad = np.zeros((rast.NX, rast.NY), dtype=bool)
    for s in model["segs"][layer]:
        net = s[5]
        if is_lane(net) or net in movable_tracks:
            continue
        rast.seg(bad, s[0], s[1], s[2], s[3], hw + s[4] + eff(net))
    for v in model["vias"]:
        if layer not in v["layers"]:
            continue
        net = v["net"]
        if is_lane(net) or net in movable_vias:
            continue
        rad = max(v["r"] + eff(net), v["drill"] + HOLE_CLR)
        rast.cir(bad, v["x"], v["y"], hw + rad)
    for p in model["pads"]:
        if is_lane(p["net"]) or p["net"] in movable_vias:
            continue
        if layer not in p["layers"] and not p["pth"]:
            continue
        b = p["box"]
        rast.rect(bad, b[0], b[1], b[2], b[3], hw + eff(p["net"]))
        if p["pth"] and p.get("drill"):
            rast.cir(bad, p["cx"], p["cy"], hw + p["drill"] + HOLE_CLR)
    for ra in model["ruleareas"]:
        if not (ra["no_tracks"] and layer in ra["layers"]):
            continue
        for poly in ra["polys"]:
            rast.poly(bad, poly)
    return bad


def anchor_keepout(rast, anchors, hw):
    """每车道锚孔 keepout 计数（走线中心须避让他车道锚孔）。"""
    c_all = np.zeros((rast.NX, rast.NY), dtype=np.int16)
    own = {}
    for an in anchors:
        local = np.zeros((rast.NX, rast.NY), dtype=bool)
        rad = hw + max(EFF_MIN + an["via_r"], an["drill"] + HOLE_CLR)
        rast.cir(local, an["A"][0], an["A"][1], rad)
        rast.cir(local, an["B"][0], an["B"][1], rad)
        c_all += local.astype(np.int16)
        own[an["net"]] = local
    return c_all, own


def build_topology(allowed, step):
    """固定单元集（allowed 为 True）之 8 邻接边表（只建一次）。"""
    idx = np.full(allowed.shape, -1, np.int32)
    ii, jj = np.nonzero(allowed)
    idx[ii, jj] = np.arange(len(ii), dtype=np.int32)
    rows, cols, dl = [], [], []
    NX, NY = allowed.shape
    for di, dj, d in NBR:
        ni = ii + di; nj = jj + dj
        m = (ni >= 0) & (ni < NX) & (nj >= 0) & (nj < NY)
        if not m.any():
            continue
        tgt = idx[ni[m], nj[m]]
        ok = tgt >= 0
        rows.append(idx[ii[m][ok], jj[m][ok]]); cols.append(tgt[ok])
        dl.append(np.full(ok.sum(), d * step, np.float64))
    return csr_matrix((np.concatenate(dl), (np.concatenate(rows), np.concatenate(cols))),
                      shape=(idx.max() + 1, idx.max() + 1)), idx


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


def disk_offsets(step, radius):
    r = int(math.floor(radius / step + 1e-9))
    off = []
    for di in range(-r, r + 1):
        for dj in range(-r, r + 1):
            if math.hypot(di * step, dj * step) <= radius + 1e-9:
                off.append((di, dj))
    return off


# ---------------- 连续几何精确闸（numpy 向量化 · 层正确） ----------------
def _seg_seg_batch(A, B):
    """A: (n,2,2) · B: (m,2,2) ⇒ (n,m) 段-段最小距离（2D 精确：4 端点-段距离之最小值）。"""
    d = _pt_seg_pts(A[:, 0, :], B[:, 0, :], B[:, 1, :])
    d = np.minimum(d, _pt_seg_pts(A[:, 1, :], B[:, 0, :], B[:, 1, :]))
    d = np.minimum(d, _pt_seg_pts(B[:, 0, :], A[:, 0, :], A[:, 1, :]).T)
    d = np.minimum(d, _pt_seg_pts(B[:, 1, :], A[:, 0, :], A[:, 1, :]).T)
    return d


def _pt_seg_pts(P, A, B):
    """P (n,2) 点集 vs 段 (A,B) 各 (m,2) ⇒ (n,m) 距离。"""
    d = B - A
    L2 = (d * d).sum(-1)
    L2 = np.where(L2 < 1e-18, 1e-18, L2)
    w = P[:, None, :] - A[None, :, :]
    t = np.clip((w * d[None, :, :]).sum(-1) / L2[None, :], 0.0, 1.0)
    proj = A[None, :, :] + t[:, :, None] * d[None, :, :]
    return np.linalg.norm(P[:, None, :] - proj, axis=-1)


def _seg_rect_dists(segs, boxes):
    """segs (n,2,2) vs boxes (m,4) ⇒ (n,m) 段-矩形外距（0 = 相交）。"""
    n = segs.shape[0]; m = boxes.shape[0]
    out = np.empty((n, m), np.float64)
    corners_cache = []
    for j in range(m):
        x0, y0, x1, y1 = boxes[j]
        c = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], np.float64)
        segs_rect = np.stack([c, np.roll(c, -1, axis=0)], axis=1)  # (4,2,2)
        out[:, j] = _seg_seg_batch(segs, segs_rect).min(axis=1)
    return out


def exact_gate(model, routes, anchors, layer, hw, movable_tracks, movable_vias, pitch):
    segs = {}
    for nm, r in routes.items():
        p = [tuple(q) for q in r["pts"]]
        segs[nm] = np.array([[(p[k][0], p[k][1]), (p[k + 1][0], p[k + 1][1])]
                             for k in range(len(p) - 1)], np.float64)
    names = sorted(segs)
    pair_min = (1e9, None); viol_pair = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            dd = _seg_seg_batch(segs[names[i]], segs[names[j]]).min()
            if dd < pitch - 1e-6:
                viol_pair.append((names[i], names[j], round(float(dd), 4)))
            if dd < pair_min[0]:
                pair_min = (dd, (names[i], names[j]))
    obs_seg = []; obs_via = []; obs_pad = []
    for s in model["segs"][layer]:
        net = s[5]
        if is_lane(net) or net in movable_tracks:
            continue
        obs_seg.append(((s[0], s[1]), (s[2], s[3]), s[4], net))
    for v in model["vias"]:
        if layer not in v["layers"]:
            continue
        net = v["net"]
        if is_lane(net) or net in movable_vias:
            continue
        obs_via.append(((v["x"], v["y"]), max(v["r"] + eff(net), v["drill"] + HOLE_CLR), net))
    for p in model["pads"]:
        if is_lane(p["net"]) or p["net"] in movable_vias:
            continue
        if layer not in p["layers"] and not p["pth"]:
            continue
        obs_pad.append((p["box"], eff(p["net"]), p["net"]))
        if p["pth"] and p.get("drill"):
            obs_via.append(((p["cx"], p["cy"]), p["drill"] + HOLE_CLR, p["net"]))
    S = np.array([[o[0], o[1]] for o in obs_seg], np.float64) if obs_seg else np.zeros((0, 2, 2))
    SR = np.array([o[2] for o in obs_seg], np.float64) if obs_seg else np.zeros(0)
    V = np.array([o[0] for o in obs_via], np.float64) if obs_via else np.zeros((0, 2))
    VR = np.array([o[1] for o in obs_via], np.float64) if obs_via else np.zeros(0)
    PB = np.array([o[0] for o in obs_pad], np.float64) if obs_pad else np.zeros((0, 4))
    PR = np.array([o[1] for o in obs_pad], np.float64) if obs_pad else np.zeros(0)
    per_lane = {}; viol_obs = []
    for nm in names:
        sg = segs[nm]
        worst = (1e9, None)
        if len(S):
            d = _seg_seg_batch(sg, S)
            need = np.maximum(EFF_MIN, np.array([req(o[3]) for o in obs_seg]))
            margin = d - SR[None, :] - hw - need[None, :]
            k = int(np.argmin(margin) % margin.shape[1]); worst = min(worst, (float(margin.min()), obs_seg[k][3]))
            if margin.min() < -1e-6:
                viol_obs.append((nm, obs_seg[k][3], "seg", round(float(margin.min()), 4)))
        if len(V):
            A = sg[:, 0, :]; Bp = sg[:, 1, :]
            d = _pt_seg_pts(V, A, Bp).T
            margin = d - VR[None, :] - hw - EFF_MIN
            k = int(np.argmin(margin) % margin.shape[1])
            if margin.min() < worst[0]:
                worst = (float(margin.min()), obs_via[k][2])
            if margin.min() < -1e-6:
                viol_obs.append((nm, obs_via[k][2], "via", round(float(margin.min()), 4)))
        if len(PB):
            d = _seg_rect_dists(sg, PB)
            margin = d - PR[None, :] - hw - EFF_MIN
            k = int(np.argmin(margin) % margin.shape[1])
            if margin.min() < worst[0]:
                worst = (float(margin.min()), obs_pad[k][2])
            if margin.min() < -1e-6:
                viol_obs.append((nm, obs_pad[k][2], "pad", round(float(margin.min()), 4)))
        per_lane[nm] = {"margin_min_mm": round(worst[0], 4), "blocker": worst[1]}
    ends = {}
    for an in anchors:
        if an["net"] not in routes:
            continue
        p = routes[an["net"]]["pts"]
        ends[an["net"]] = round(max(math.dist(p[0], an["A"]), math.dist(p[-1], an["B"])), 4)
    mins = [v["margin_min_mm"] for v in per_lane.values()]
    return {"lane_pitch_req_mm": pitch, "lane_pitch_min_gap_mm": round(float(pair_min[0]), 4),
            "lane_pitch_min_pair": pair_min[1], "n_lane_pitch_viol": len(viol_pair),
            "lane_pitch_violations": viol_pair[:20],
            "clearance_min_mm": round(min(mins), 4) if mins else None,
            "clearance_violations": viol_obs[:20], "n_clearance_viol": len(viol_obs),
            "endpoint_max_dev_mm": max(ends.values()) if ends else None,
            "per_lane": per_lane, "n_obs": {"seg": len(obs_seg), "via": len(obs_via), "pad": len(obs_pad)}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--layer", default="In5.Cu")
    ap.add_argument("--cell", type=float, default=0.10)
    ap.add_argument("--lane-w", type=float, default=0.16)
    ap.add_argument("--pitch", type=float, default=0.335)
    ap.add_argument("--iters", type=int, default=12)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--pf0", type=float, default=1.0)
    ap.add_argument("--hf", type=float, default=0.05)
    ap.add_argument("--repair", type=int, default=60)
    ap.add_argument("--movable-nets", default="")
    ap.add_argument("--movable-stitch", default="")
    ap.add_argument("--a-sites", default=None)
    ap.add_argument("--b-sites", default=None)
    ap.add_argument("--no-gate", action="store_true")
    ap.add_argument("--algo", default="negotiate", choices=["negotiate", "hard"])
    ap.add_argument("--groups", default=None, help="只跑指定前缀之车道（逗号分隔）")
    ap.add_argument("--restarts", type=int, default=40)
    a = ap.parse_args()
    model = json.load(open(a.model))
    movable = set(x for x in a.movable_nets.split(",") if x)
    movable_vias = set(x for x in a.movable_stitch.split(",") if x)
    hw = a.lane_w / 2.0
    rast = Raster(model["bbox"], a.cell)
    base = build_base(rast, model, a.layer, movable, movable_vias, hw)
    anchors = lane_anchors(model)
    for src, key in ((a.a_sites, "A"), (a.b_sites, "B")):
        if src:
            ov = json.load(open(src))
            for an in anchors:
                if an["net"] in ov:
                    an[key] = tuple(float(x) for x in ov[an["net"]][:2])
    if a.groups:
        pre = tuple(x for x in a.groups.split(",") if x)
        anchors = [an for an in anchors if an["net"].startswith(pre)]
    c_all, own = anchor_keepout(rast, anchors, hw)
    fixed_ok = ~base
    G, idx = build_topology(fixed_ok, a.cell)
    NN = idx.max() + 1
    print("车道 %d · 栅格 %dx%d cell=%.2f · 固定单元 %d · pitch=%.3f lane_w=%.3f" %
          (len(anchors), rast.NX, rast.NY, a.cell, NN, a.pitch, a.lane_w))

    tasks = []
    blk2d = {}
    for an in anchors:
        blocked = base | ((c_all.astype(np.int32) - own[an["net"]].astype(np.int32)) > 0)
        blk2d[an["net"]] = blocked
        tasks.append({"an": an, "blocked": blocked, "status": "PENDING"})
    ii, jj = np.nonzero(fixed_ok)
    cellid = idx[ii, jj].astype(np.int64)
    NN = int(cellid.max()) + 1
    cell_of = np.full(NN, -1, np.int64); cell_of[cellid] = np.arange(len(ii))
    coo = G.tocoo()
    e_src = cell_of[coo.row].astype(np.int64); e_tgt = cell_of[coo.col].astype(np.int64)
    e_dl = coo.data.astype(np.float64)
    del coo

    def snap(cell, blk, max_r=12):
        """就近平移到非障碍之固定单元；返回 (i,j,r, 位移 mm)。"""
        ci, cj = cell; best = None
        for r in range(0, max_r + 1):
            for di in range(-r, r + 1):
                for dj in range(-r, r + 1):
                    if max(abs(di), abs(dj)) != r:
                        continue
                    i, j = ci + di, cj + dj
                    if 0 <= i < rast.NX and 0 <= j < rast.NY and not blk[i, j]:
                        d = math.hypot(di, dj) * a.cell
                        if best is None or d < best[0]:
                            best = (d, i, j)
            if best is not None:
                return best[1], best[2], best[0]
        return None, None, None

    for t in tasks:
        an = t["an"]; blk = t["blocked"]
        si, sj, ds = snap(rast.cell(*an["A"]), blk)
        gi, gj, dg = snap(rast.cell(*an["B"]), blk)
        t["disp_mm"] = {"A": round(ds, 4) if ds is not None else None,
                        "B": round(dg, 4) if dg is not None else None}
        if si is None or gi is None or idx[si, sj] < 0 or idx[gi, gj] < 0:
            t["status"] = "NO_FREE_ENDPOINT"
            continue
        t["s"] = (si, sj); t["g"] = (gi, gj)
        if ds and ds > 1e-9:
            an["A"] = (rast.X0 + si * a.cell, rast.Y0 + sj * a.cell)
        if dg and dg > 1e-9:
            an["B"] = (rast.X0 + gi * a.cell, rast.Y0 + gj * a.cell)
        t["blk1d"] = blk[ii, jj]
    bad_end = [t["an"]["net"] for t in tasks if t["status"] != "PENDING"]
    if bad_end:
        print("  ⚠ 端点不可行：", bad_end)
    disp = {t["an"]["net"]: t["disp_mm"] for t in tasks}
    nz = {k: v for k, v in disp.items() if (v["A"] or 0) > 1e-9 or (v["B"] or 0) > 1e-9}
    print("  端点就近平移（B 侧可滑 · 需 F.Cu 扇出覆盖）：%d 条非零" % len(nz))
    for k in sorted(nz)[:40]:
        print("     %-28s A=%.3f B=%.3f" % (k, nz[k]["A"], nz[k]["B"]))

    offs = disk_offsets(a.cell, a.pitch)

    def stamp(occ1d, path_ij):
        pi = np.array([p[0] for p in path_ij], np.int64)
        pj = np.array([p[1] for p in path_ij], np.int64)
        for di, dj in offs:
            ci = pi + di; cj = pj + dj
            m = (ci >= 0) & (ci < rast.NX) & (cj >= 0) & (cj < rast.NY)
            if not m.any():
                continue
            c2 = idx[ci[m], cj[m]]
            v = c2 >= 0
            if v.any():
                np.add.at(occ1d, c2[v], 1)

    def route_one_fast(t, occ1d, pen_scale, hist1d, hard=False):
        blk = t["blk1d"]
        ok = (~blk[e_src]) & (~blk[e_tgt])
        if hard:
            ok &= (occ1d[e_tgt] == 0)
        w = np.where(ok, e_dl + pen_scale * occ1d[e_tgt].astype(np.float64) + hist1d[e_tgt], np.inf)
        G2 = csr_matrix((w, (e_src, e_tgt)), shape=G.shape)
        s = t["s"]; g = t["g"]
        si = idx[s[0], s[1]]; gi = idx[g[0], g[1]]
        if si < 0 or gi < 0:
            return None, None
        dist, pred = dijkstra(G2, directed=True, indices=int(si), return_predecessors=True)
        if not np.isfinite(dist[gi]):
            return None, None
        pp = path_from_pred(pred, int(si), int(gi))
        if not pp:
            return None, None
        cells = [(int(ii[k]), int(jj[k])) for k in pp]
        return cells, float(dist[gi])

    def nviol(occ1d, routed):
        return sum(1 for nm, cells in routed.items()
                   for (i, j) in cells if occ1d[idx[i, j]] >= 2)

    hist1d = np.zeros(len(ii), dtype=np.float32)
    routed = {}
    if a.algo == "hard":
        rng = np.random.RandomState(a.seed)
        best = None
        for r in range(a.restarts):
            occ1d = np.zeros(len(ii), dtype=np.int16)
            cur = {}
            order = list(range(len(tasks)))
            if r == 0:
                order.sort(key=lambda k: -math.dist(tasks[k]["an"]["A"], tasks[k]["an"]["B"]))
            elif r == 1:
                order.sort(key=lambda k: math.dist(tasks[k]["an"]["A"], tasks[k]["an"]["B"]))
            else:
                rng.shuffle(order)
            for k in order:
                t = tasks[k]
                if t["status"] != "PENDING":
                    continue
                cells, _ = route_one_fast(t, occ1d, 0.0, hist1d, hard=True)
                if not cells:
                    continue
                cur[t["an"]["net"]] = cells
                stamp(occ1d, cells)
            print("  [hard r %2d] routed=%2d/%d" % (r, len(cur), len(tasks)))
            if best is None or len(cur) > len(best):
                best = {k: list(v) for k, v in cur.items()}
            if len(cur) == len(tasks):
                break
        routed = best or {}
    else:
        best = None; pf = a.pf0
        rng = np.random.RandomState(a.seed)
        for it in range(a.iters):
            occ1d = np.zeros(len(ii), dtype=np.int16)
            routed = {}
            order = list(range(len(tasks)))
            if it == 0:
                order.sort(key=lambda k: -math.dist(tasks[k]["an"]["A"], tasks[k]["an"]["B"]))
            else:
                rng.shuffle(order)
            for k in order:
                t = tasks[k]
                if t["status"] != "PENDING":
                    continue
                cells, _ = route_one_fast(t, occ1d, pf, hist1d, hard=False)
                if not cells:
                    continue
                routed[t["an"]["net"]] = cells
                stamp(occ1d, cells)
            viol = nviol(occ1d, routed)
            print("  [it %2d] routed=%2d/%d vio=%5d pf=%.3f" % (it, len(routed), len(tasks), viol, pf))
            score = (len(routed), -viol)
            if best is None or score > best[0]:
                best = (score, {k: list(v) for k, v in routed.items()})
            if len(routed) == len(tasks) and viol == 0:
                break
            hist1d += np.maximum(occ1d.astype(np.float32) - 1.0, 0.0)
            pf *= 1.8
        routed = best[1]
        print("  协商终（best）：routed=%d/%d vio=%d" % (len(routed), len(tasks), -best[0][1]))

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
        try:
            gate = exact_gate(model, routes, anchors, a.layer, hw, movable, movable_vias, a.pitch)
        except Exception as e:  # noqa: BLE001
            print("  ⚠ 闸异常：%s: %s" % (type(e).__name__, e))
            gate = {"error": "%s: %s" % (type(e).__name__, e)}
        print("  [精确闸] 车道最小中心距 %.4f（<%.3f 违规 %d）· 障碍最小余量 %.4f（违规 %d）· 端点最大偏移 %s" %
              (gate["lane_pitch_min_gap_mm"], a.pitch, gate["n_lane_pitch_viol"],
               gate["clearance_min_mm"], gate["n_clearance_viol"], gate["endpoint_max_dev_mm"]))
    wo = {"artifact": "k2_p4_b2_in5_lane_router_v3_workorder", "layer": a.layer, "cell_mm": a.cell,
          "lane_w_mm": a.lane_w, "pitch_mm": a.pitch, "model": a.model, "movable_nets": sorted(movable),
          "n_lanes": len(anchors), "n_routed": len(routes),
          "failed": sorted(t["an"]["net"] for t in tasks if t["an"]["net"] not in routes),
          "routes": routes, "geometric_gate": gate,
          "anchors": [{"net": an["net"], "A": [round(an["A"][0], 4), round(an["A"][1], 4)],
                       "B": [round(an["B"][0], 4), round(an["B"][1], 4)],
                       "disp_mm": t["disp_mm"]} for an, t in zip(anchors, tasks)],
          "note": "逐网配对（A_x→B_x）· 各向同性圆盘间距 · 首末点=锚孔中心"}
    json.dump(wo, open(a.out, "w"), ensure_ascii=False, indent=1, sort_keys=True)
    print("routed %d/%d · failed=%s" % (len(routes), len(anchors), wo["failed"]))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
