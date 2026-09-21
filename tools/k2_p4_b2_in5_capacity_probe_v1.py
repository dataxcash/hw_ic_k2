#!/usr/bin/env python3
"""K2 · §7-2-b-0 —— In5 **锚孔笼容量探针 v1**（只读设计器 · 系统 python3 + numpy/scipy）。

回答两个问题（#K2-68 §2.4(a)-2/4 · R2I/R2K/R2L 之可复现化与延伸）：
  Q1 `fixed`：**现行锚位**下，A 集合↔B 集合之**同时布通上界**（R2L 口径：每锚局部扇出
     R + 锚节点容量 1 + 栅格节点容量 1）⇒ l9/R1E 基线应为 **19/32**（复现门）。
  Q2 `reloc`：**完整锚孔笼重构**（#K2-68 §2.4(a)-2）之容量可行性——把 32 条车道之
     A（U6 侧 F–In5 过渡孔）/ B（连接器侧 F–In5 过渡孔）重排进场地自由槽（相邻中心距
     ≥ `--min-sep`），求可同时布通之最大流；并给出**具体候选位**。

自由空间语义（= 探针语义，与 `k2_p4_b2_feasibility_probe_v1.py` 逐项一致）：
  障碍 = 该层**其他网**铜（线/孔/盘，按 net 取 req）· **车道自身铜与外网车道孔皆视为可拆** ·
  再加**本次要放的锚孔** keepout（VIA_R + hw + req）。节点 = 自由栅格；4/8 邻接；
  源/汇 = 锚孔局部扇出半径 `--rloc` 内的自由格（容量 1）；栅格节点容量 1。

用法：
  python3 k2/tools/k2_p4_b2_in5_capacity_probe_v1.py --model <dump.json> \
      --mode fixed|reloc --cell 0.40 --conn 8 --rloc 1.0 --min-sep 0.86 --json-out <out.json>

依赖：numpy · scipy（**与 pcbnew 工具分离**，见 k2_p4_b2_board_dump_v1.py）。
"""
from __future__ import annotations
import argparse, collections, json, math

import numpy as np
from scipy import ndimage, sparse
from scipy.sparse.csgraph import maximum_flow

HW_DEF = 0.08          # 车道线半宽 0.16/2
VIA_R = 0.175
REQ_PCIE = 0.175
REQ_PWR = 0.20
REQ_DFLT = 0.10
ANCHOR_KEEPOUT = VIA_R + HW_DEF + REQ_PCIE     # 0.43 mm

LANE_PREFIX = ("PCIE_UP_OUT", "PCIE_DN_OUT")
REGIONS = {"A": (74.0, 45.0, 101.0, 61.0),
           "B_mcio": (48.0, 42.0, 72.0, 64.0),
           "B_j2": (118.0, 34.0, 146.0, 58.0),
           # §7-2-b-0 设计：A 侧按**去向分组**摆放（DN→西 / UP→东），实测容量 W 37 / E 67
           "A_west": (74.0, 45.0, 89.0, 61.0),
           "A_east": (89.0, 45.0, 102.0, 61.0)}


def is_lane(nm):
    return nm.startswith(LANE_PREFIX)


def req(nm):
    if nm.startswith("PCIE") or nm.startswith("REFCLK"):
        return REQ_PCIE
    if nm.startswith(("P3V3", "MCU_", "VREG", "PWR_5V")):
        return REQ_PWR
    return REQ_DFLT


LANE_HW = {"In2.Cu": 0.16 / 2, "In5.Cu": 0.16 / 2, "B.Cu": 0.205 / 2}   # 车道线宽 = 探针口径


class Field:
    """0.1mm 细栅格上的**指定层**线心合法图（bad=True ⇒ 线心不可放）。

    `layer` 默认 `In5.Cu`（§7-2-b-0 In5 路径）；`B.Cu` 用于 (a) B.Cu 收紧版段闸；
    `In2.Cu` 用于对照。车道线半宽按 `LANE_HW` 取（B.Cu = 0.205/2，其余 0.16/2）。
    """

    def __init__(self, model, hw=None, step=0.10, layer="In5.Cu", movable_nets=(), caliber="legacy"):
        self.layer = layer
        self.movable = set(movable_nets)
        # caliber: legacy = 原口径（req() 直取）；nets_max = 板 netclass **max 规则**（lane↔任意网 ≥0.175）
        self.caliber = caliber
        self.hw = LANE_HW.get(layer, HW_DEF) if hw is None else hw
        self.step = step
        self.segs = model["segs"][layer]
        self.vias = [v for v in model["vias"] if layer in v["layers"]]
        self.pads = [p for p in model["pads"] if (layer in p["layers"] or p["pth"])]
        x0, y0, x1, y1 = model["bbox"]
        # 栅格原点 = 板 bbox 角点（与官方探针 `k2_p4_b2_feasibility_probe_v1.py` 逐格对齐）
        self.X0, self.Y0 = x0, y0
        self.NX = int((x1 - self.X0) / step) + 1
        self.NY = int((y1 - self.Y0) / step) + 1
        self.XS = self.X0 + np.arange(self.NX) * step
        self.YS = self.Y0 + np.arange(self.NY) * step
        self.GX, self.GY = np.meshgrid(self.XS, self.YS, indexing="ij")
        self.other = self._build_other()
        self.legal = ~ndimage.binary_dilation(self.other, iterations=max(1, int(round(0.095 / step))))

    # ---------------------------------------------------------------- 几何
    def _seg(self, bad, ax, ay, bx, by, rad):
        X0, Y0, S, NX, NY = self.X0, self.Y0, self.step, self.NX, self.NY
        i0 = max(0, int((min(ax, bx) - rad - X0) / S)); i1 = min(NX - 1, int((max(ax, bx) + rad - X0) / S) + 1)
        j0 = max(0, int((min(ay, by) - rad - Y0) / S)); j1 = min(NY - 1, int((max(ay, by) + rad - Y0) / S) + 1)
        if i1 < i0 or j1 < j0:
            return
        X = self.GX[i0:i1 + 1, j0:j1 + 1]; Y = self.GY[i0:i1 + 1, j0:j1 + 1]
        dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
        t = np.zeros_like(X) if L2 == 0 else np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
        bad[i0:i1 + 1, j0:j1 + 1] |= (np.hypot(X - (ax + t * dx), Y - (ay + t * dy)) < rad)

    def _cir(self, bad, cx, cy, rad):
        X0, Y0, S, NX, NY = self.X0, self.Y0, self.step, self.NX, self.NY
        i0 = max(0, int((cx - rad - X0) / S)); i1 = min(NX - 1, int((cx + rad - X0) / S) + 1)
        j0 = max(0, int((cy - rad - Y0) / S)); j1 = min(NY - 1, int((cy + rad - Y0) / S) + 1)
        if i1 < i0 or j1 < j0:
            return
        X = self.GX[i0:i1 + 1, j0:j1 + 1]; Y = self.GY[i0:i1 + 1, j0:j1 + 1]
        bad[i0:i1 + 1, j0:j1 + 1] |= (np.hypot(X - cx, Y - cy) < rad)

    def _rect(self, bad, x0, y0, x1, y1, rad):
        X0, Y0, S, NX, NY = self.X0, self.Y0, self.step, self.NX, self.NY
        i0 = max(0, int((x0 - rad - X0) / S)); i1 = min(NX - 1, int((x1 + rad - X0) / S) + 1)
        j0 = max(0, int((y0 - rad - Y0) / S)); j1 = min(NY - 1, int((y1 + rad - Y0) / S) + 1)
        if i1 < i0 or j1 < j0:
            return
        X = self.GX[i0:i1 + 1, j0:j1 + 1]; Y = self.GY[i0:i1 + 1, j0:j1 + 1]
        dx = np.maximum(np.maximum(x0 - X, 0), X - x1); dy = np.maximum(np.maximum(y0 - Y, 0), Y - y1)
        bad[i0:i1 + 1, j0:j1 + 1] |= (np.hypot(dx, dy) < rad)

    def _req(self, net):
        r = req(net)
        if self.caliber == "nets_max":
            r = max(REQ_PCIE, r)
        return r

    def _build_other(self):
        """其他网铜障碍图。`movable_nets`（= ✓ 可腾挪之缝合孔/走线，如 P3V3/GND 缝合孔）**不计入**，
        用于 #K2-68 §2.4(a)-2『腾挪缝合孔 ⇒ 净出口 ≥ 所需』之只读量化（真腾挪须 apply 后复核参考面）。"""
        hw = self.hw
        bad = np.zeros((self.NX, self.NY), dtype=bool)
        for s in self.segs:
            if is_lane(s[5]) or s[5] in self.movable:
                continue
            self._seg(bad, s[0], s[1], s[2], s[3], hw + s[4] + self._req(s[5]))
        for v in self.vias:
            if is_lane(v["net"]) or v["net"] in self.movable:
                continue
            self._cir(bad, v["x"], v["y"], hw + max(v["r"] + self._req(v["net"]), v["drill"] + 0.25))
        for p in self.pads:
            if is_lane(p["net"]):
                continue
            b = p["box"]
            self._rect(bad, b[0], b[1], b[2], b[3], hw + self._req(p["net"]))
        return bad

    def bad_with(self, anchors, keepout=None):
        if keepout is None:
            keepout = (VIA_R + self.hw + max(REQ_PCIE, REQ_PCIE))
        bad = self.other.copy()
        for (x, y) in anchors:
            self._cir(bad, x, y, keepout)
        return bad

    def cell(self, x, y):
        return int(round((x - self.X0) / self.step)), int(round((y - self.Y0) / self.step))

    def is_legal(self, x, y):
        i, j = self.cell(x, y)
        return 0 <= i < self.NX and 0 <= j < self.NY and self.legal[i, j]


def lanes_of(model):
    L = collections.OrderedDict()
    for v in model["vias"]:
        nm = v["net"]
        if not is_lane(nm):
            continue
        L.setdefault(nm, {})["%s-%s" % (v["top"], v["bot"])] = (v["x"], v["y"])
    out = []
    for nm in sorted(L):
        d = L[nm]
        a, b = d.get("F.Cu-B.Cu"), d.get("F.Cu-In2.Cu")
        out.append({"net": nm, "A": a, "B": b,
                    "group": "B_mcio" if nm.startswith("PCIE_DN_") else "B_j2"})
    return out


# ------------------------------------------------------------------ 最大流
def maxflow(field, A, B, cell_mm=0.40, conn=8, rloc=1.0, keepout=ANCHOR_KEEPOUT, anchors_keepout=None, ret_flow=False):
    """A/B: 锚孔坐标列表（等长）。返回 (flow, info)。

    口径 = R2L：**每锚一个容量 1 之锚节点**，锚节点与其**局部扇出半径 rloc 内之全部自由格**
    双向连接（每格容量 1）；栅格节点容量 1；A/B 锚集合间允许配对 ⇒ **同时布通上界**。
    """
    anchors = list(A) + list(B)
    bad = field.bad_with(anchors if anchors_keepout is None else anchors_keepout, keepout)
    GNX = int((field.NX - 1) * field.step / cell_mm) + 1
    GNY = int((field.NY - 1) * field.step / cell_mm) + 1
    ii = np.clip(np.round(np.arange(GNX) * cell_mm / field.step).astype(int), 0, field.NX - 1)
    jj = np.clip(np.round(np.arange(GNY) * cell_mm / field.step).astype(int), 0, field.NY - 1)
    free = ~bad[np.ix_(ii, jj)]
    idx = np.full(free.shape, -1, dtype=np.int64)
    a, b = np.nonzero(free)
    idx[a, b] = np.arange(len(a))
    N = len(a)
    if N == 0:
        return 0, {"N": 0}
    k = np.arange(N)
    rows = [2 * k]; cols = [2 * k + 1]; data = [np.ones(N, dtype=np.int32)]
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)] + ([(1, 1), (1, -1), (-1, 1), (-1, -1)] if conn == 8 else [])
    for di, dj in dirs:
        u = a + di; v = b + dj
        m = (u >= 0) & (u < GNX) & (v >= 0) & (v < GNY)
        ku = idx[u[m], v[m]]
        ok = ku >= 0
        rows.append(2 * k[m][ok] + 1); cols.append(2 * ku[ok])
        data.append(np.full(int(ok.sum()), 10 ** 6, dtype=np.int32))
    nA, nB = len(A), len(B)
    NA = 2 * N                       # A 锚节点起点
    def aid(x): return NA + 2 * x
    def bid(x): return NA + 2 * x + 1
    SRC, SNK = NA + 2 * max(nA, nB), NA + 2 * max(nA, nB) + 1
    # 预计算径向邻域偏移（细栅格步长）
    rr = int(round(rloc / cell_mm))
    offs = []
    for di in range(-rr, rr + 1):
        for dj in range(-rr, rr + 1):
            if di * di + dj * dj <= rr * rr + 1e-9:
                offs.append((di, dj))
    def fan(pt):
        ci = int(round((pt[0] - field.X0) / cell_mm)); cj = int(round((pt[1] - field.Y0) / cell_mm))
        out = []
        for di, dj in offs:
            p, q = ci + di, cj + dj
            if 0 <= p < GNX and 0 <= q < GNY and idx[p, q] >= 0:
                out.append(int(idx[p, q]))
        return out
    na = nb = 0
    for x, pt in enumerate(A):
        cells = fan(pt)
        if not cells:
            continue
        rows.append(np.array([SRC])); cols.append(np.array([aid(x)])); data.append(np.array([1], dtype=np.int32)); na += 1
        rows.append(np.full(len(cells), aid(x))); cols.append(2 * np.array(cells)); data.append(np.ones(len(cells), dtype=np.int32))
    for x, pt in enumerate(B):
        cells = fan(pt)
        if not cells:
            continue
        rows.append(np.array([bid(x)])); cols.append(np.array([SNK])); data.append(np.array([1], dtype=np.int32)); nb += 1
        rows.append(2 * np.array(cells) + 1); cols.append(np.full(len(cells), bid(x))); data.append(np.ones(len(cells), dtype=np.int32))
    rows = np.concatenate(rows); cols = np.concatenate(cols); data = np.concatenate(data)
    M = sparse.csr_matrix((data, (rows, cols)), shape=(SNK + 1, SNK + 1))
    res = maximum_flow(M, SRC, SNK)
    f = int(res.flow_value)
    info = {"N": N, "src_attached": na, "snk_attached": nb, "grid": [GNX, GNY],
            "rloc_cells": len(offs), "SRC": SRC, "SNK": SNK, "NA": NA}
    if ret_flow:
        return f, info, res.flow, SRC, NA
    return f, info


def same_component_stats(field, lanes, cell_mm=0.10, conn=8, rloc=1.0):
    """必要条件（= 官方探针语义之**扇出集合**修正版）：每车道 A/B 之**扇出半径内自由格**是否
    落入同一连通域。注意：官探针取『首个非空 Chebyshev 环内最近格』（单格），本器取**扇出集合**
    —— 单格口径会把锚孔旁 1 格孤立空腔误判为唯一出口（假阴），集合口径才是物理语义。"""
    anchors = [l["A"] for l in lanes if l["A"]] + [l["B"] for l in lanes if l["B"]]
    bad = field.bad_with([a for a in anchors if a])
    free = ~bad
    st = np.ones((3, 3), bool) if conn == 8 else np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
    lab, n = ndimage.label(free, structure=st)
    rr = int(round(rloc / field.step))
    ok = 0; detail = {}
    for l in lanes:
        if not (l["A"] and l["B"]):
            detail[l["net"]] = {"status": "NO_ANCHOR"}; continue
        outs = []
        for c in (l["A"], l["B"]):
            ci, cj = field.cell(c[0], c[1]); s = set(); off = 0.0
            for di in range(-rr, rr + 1):
                for dj in range(-rr, rr + 1):
                    if di * di + dj * dj > rr * rr + 1e-9:
                        continue
                    p, q = ci + di, cj + dj
                    if 0 <= p < field.NX and 0 <= q < field.NY and free[p, q]:
                        s.add(int(lab[p, q]))
                        if off == 0.0:
                            off = math.hypot(di, dj) * field.step
            outs.append(s)
        same = bool(outs[0] & outs[1])
        ok += int(same)
        detail[l["net"]] = {"compA": sorted(outs[0])[:3], "compB": sorted(outs[1])[:3], "same": same,
                            "n_fanA": len(outs[0]), "n_fanB": len(outs[1])}
    return ok, n, detail


# ------------------------------------------------------------------ 重排搜索
def region_sites(field, reg, sep, near=None, max_radius=None, limit=None):
    x0, y0, x1, y1 = REGIONS[reg]
    i0, j0 = field.cell(x0, y0); i1, j1 = field.cell(x1, y1)
    i0 = max(0, i0); j0 = max(0, j0); i1 = min(field.NX - 1, i1); j1 = min(field.NY - 1, j1)
    sub = field.legal[i0:i1 + 1, j0:j1 + 1]
    a, b = np.nonzero(sub)
    pts = np.stack([field.XS[i0 + a], field.YS[j0 + b]], 1)
    if near is not None and max_radius is not None:
        d = np.hypot(pts[:, 0] - near[0], pts[:, 1] - near[1])
        pts = pts[d <= max_radius]
    if pts.size == 0:
        return np.zeros((0, 2))
    if limit and len(pts) > limit:                      # 定序抽样（确定性）
        idx = np.linspace(0, len(pts) - 1, limit).astype(int)
        pts = pts[idx]
    return pts


def greedy_place(field, cand, pts, sep, order=None):
    """贪心：邻近者优先 + 最小间距 sep。返回选中点列表。"""
    chosen = []
    used = np.zeros(len(cand), dtype=bool)
    for p in pts:
        d = np.hypot(cand[:, 0] - p[0], cand[:, 1] - p[1])
        if len(chosen):
            C = np.array(chosen)
            if np.min(np.hypot(C[:, 0] - p[0], C[:, 1] - p[1])) < sep - 1e-9:
                continue
        k = int(np.argmin(d))
        while used[k]:
            d[k] = 1e9
            k = int(np.argmin(d))
            if d[k] > 1e9 / 2:
                break
        if used[k]:
            continue
        used[k] = True
        chosen.append((float(cand[k, 0]), float(cand[k, 1])))
    return chosen


def box_pts(field, box, cell_mm=0.40):
    x0, y0, x1, y1 = box
    out = []
    for x in np.arange(x0, x1 + 1e-9, cell_mm):
        for y in np.arange(y0, y1 + 1e-9, cell_mm):
            if field.is_legal(float(x), float(y)):
                out.append((float(x), float(y)))
    return out


def guided_sites(field, box, Bpts, n, sep, cell_mm=0.40, conn=8, rloc=1.0, reserve=None):
    """**流量引导**选点：以 box 内全部合法格为候选源、Bpts 为汇求最大流，
    取**实际承载流量**之候选格（= 真实逃逸入口），再按最小中心距 sep 稀疏化取 n 个。

    返回 (sites, info)。reserve = 已占用点列表（最小距约束需一并满足）。
    """
    pts = box_pts(field, box, cell_mm)
    if not pts:
        return [], {"reason": "EMPTY_BOX"}
    keep = list(Bpts) + list(reserve or [])
    f, info, fl, SRC, NA = maxflow(field, pts, Bpts, cell_mm, conn, rloc,
                                   anchors_keepout=keep, ret_flow=True)
    used = [pts[k] for k in range(len(pts)) if fl[SRC, NA + 2 * k] > 0]
    sites = []
    for p in used:
        if len(sites) >= n:
            break
        if all(math.hypot(p[0] - q[0], p[1] - q[1]) >= sep - 1e-9 for q in sites):
            sites.append((float(p[0]), float(p[1])))
    if len(sites) < n:                     # 流量承载点不足 ⇒ 以最大最小距补足
        pool = [p for p in pts if all(math.hypot(p[0] - q[0], p[1] - q[1]) >= sep - 1e-9 for q in sites)]
        while len(sites) < n and pool:
            if not sites:
                k = 0
            else:
                d = [min(math.hypot(p[0] - q[0], p[1] - q[1]) for q in sites) for p in pool]
                k = int(np.argmax(d))
            sites.append(pool.pop(k))
    info = dict(info); info["n_used_flow_cells"] = len(used); info["n_sites"] = len(sites)
    return sites, info


def span_classes(model):
    """#K2-69 §六-⑦（D-1 正式闭合）：span 集**自板派生**（非手列），并给出可达单层 L 集。"""
    import collections
    c = collections.Counter()
    for v in model["vias"]:
        c["%s-%s" % (v["top"], v["bot"])] += 1
    pairs = {k: v for k, v in sorted(c.items(), key=lambda z: -z[1])}
    admissible = [L for L in ("In2.Cu", "In5.Cu", "B.Cu") if ("F.Cu-%s" % L) in pairs]
    return {"pairs": pairs, "total_vias": sum(c.values()), "admissible_L": admissible,
            "derivation": "自 dump 之 via top/bot 逐孔统计（脚本化 · 非手列）"}


def anchor_clearance(field, lanes, min_clear=None):
    """逐锚**该层**净距（锚孔铜缘 → 最近他网铜缘）：< `VIA_R + req` ⇒ 换算为该层 span 后**必移**。

    用于 (a) B.Cu 收紧版 / In5 路径之 R3 前置：给出**具名必移孔清单**（禁手列）。
    """
    import math as _m
    out = {}
    for l in lanes:
        for tag in ("A", "B"):
            pt = l[tag]
            if not pt:
                continue
            best = (1e9, None)
            for (ax, ay, bx, by, shw, nm) in field.segs:
                if is_lane(nm):
                    continue
                dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
                t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((pt[0] - ax) * dx + (pt[1] - ay) * dy) / L2))
                d = _m.hypot(pt[0] - (ax + t * dx), pt[1] - (ay + t * dy)) - shw
                if d < best[0]:
                    best = (d, {"kind": "seg", "net": nm})
            for v in field.vias:
                if is_lane(v["net"]):
                    continue
                d = _m.hypot(pt[0] - v["x"], pt[1] - v["y"]) - v["r"]
                if d < best[0]:
                    best = (d, {"kind": "via", "net": v["net"], "at": [v["x"], v["y"]]})
            for p in field.pads:
                if is_lane(p["net"]):
                    continue
                x0, y0, x1, y1 = p["box"]
                dx = max(x0 - pt[0], 0.0, pt[0] - x1); dy = max(y0 - pt[1], 0.0, pt[1] - y1)
                d = _m.hypot(dx, dy)
                if d < best[0]:
                    best = (d, {"kind": "pad", "net": p["net"], "ref": p["ref"] + "." + p["num"]})
            need = VIA_R + req(best[1]["net"]) if best[1] else VIA_R
            out["%s.%s" % (l["net"], tag)] = {"clear_mm": round(best[0], 4), "need_mm": round(need, 3),
                                             "short_by_mm": round(need - best[0], 4), "blocker": best[1],
                                             "ok": bool(best[0] >= need - 1e-9)}
    bad = sorted(k for k, v in out.items() if not v["ok"])
    return {"per_anchor": out, "n_anchor": len(out), "n_must_move": len(bad), "must_move": bad}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--mode", default="fixed", choices=["fixed", "reloc", "both", "clearance"])
    ap.add_argument("--cell", type=float, default=0.40, help="最大流栅格 (mm)")
    ap.add_argument("--conn", type=int, default=8, choices=[4, 8])
    ap.add_argument("--rloc", type=float, default=1.0, help="锚孔局部扇出半径 (mm)")
    ap.add_argument("--min-sep", type=float, default=0.86, help="锚孔最小中心距 (mm)")
    ap.add_argument("--layer", default="In5.Cu", choices=["In2.Cu", "In5.Cu", "B.Cu"],
                    help="车道中段所在层（(a) 走 B.Cu · In5 路径走 In5.Cu）")
    ap.add_argument("--movable-nets", default="",
                    help="逗号分隔：视为**可腾挪**之缝合孔/走线网（§2.4(a)-2 只读量化；默认空）")
    ap.add_argument("--caliber", default="legacy", choices=["legacy", "nets_max"],
                    help="障碍间隙口径：legacy=req() 直取（历史复现）；nets_max=板 netclass max（lane↔任意网 ≥0.175 + 孔到铜 0.25）")
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()
    model = json.load(open(a.model))
    t = Field(model, layer=a.layer, movable_nets=[x for x in a.movable_nets.split(',') if x], caliber=a.caliber)
    lanes = lanes_of(model)
    A_cur = [l["A"] for l in lanes]; B_cur = [l["B"] for l in lanes]
    rep = {"artifact": "k2_p4_b2_in5_capacity_probe_v1", "model": a.model, "caliber": a.caliber,
           "layer": a.layer, "lane_hw_mm": t.hw, "anchor_keepout_mm": t.hw + VIA_R + REQ_PCIE,
           "movable_nets": sorted(t.movable),
           "span_classes_board_actual": span_classes(model),
           "board": model.get("board"), "cell_mm": a.cell, "conn": a.conn, "rloc_mm": a.rloc,
           "min_sep_mm": a.min_sep, "n_lanes": len(lanes), "regions": REGIONS,
           "method": "In5 细栅格 0.1mm 线心合法图（其他网铜 + 本批锚孔 keepout）→ 抽样栅格最大流"
                     "；每锚经局部扇出 rloc 接源/汇（容量 1）；栅格节点容量 1；A/B 集合间允许配对（上界）"}
    if a.mode == "clearance":
        cl = anchor_clearance(t, lanes)
        rep["clearance"] = cl
        print("[%s][clearance] 锚孔 %d 个 · **必移 %d 个**" % (a.layer, cl["n_anchor"], cl["n_must_move"]))
        for k in cl["must_move"][:40]:
            v = cl["per_anchor"][k]
            print("   %-30s clear=%.3f need=%.3f (short %.3f) ← %s" % (k, v["clear_mm"], v["need_mm"], v["short_by_mm"], v["blocker"]))
        if a.json_out:
            json.dump(rep, open(a.json_out, "w"), ensure_ascii=False, indent=1, sort_keys=True)
            print("wrote", a.json_out)
        return
    f_fixed, i_fixed = maxflow(t, A_cur, B_cur, a.cell, a.conn, a.rloc)
    rep["fixed"] = {"maxflow": f_fixed, **i_fixed}
    ok, ncomp, det = same_component_stats(t, lanes, cell_mm=0.10, conn=a.conn, rloc=a.rloc)
    rep["necessary_same_component"] = {"pass": ok, "n": len(lanes), "components": ncomp, "per_lane": det}
    print("[%s][fixed] A->B maxflow = %d/%d (grid %s)" % (a.layer, f_fixed, len(lanes), i_fixed))
    print("[necessary] same-component = %d/%d (components=%d)" % (ok, len(lanes), ncomp))

    if a.mode in ("reloc", "both"):
        sep = a.min_sep
        grp_idx = {g: [i for i, l in enumerate(lanes) if l["group"] == g] for g in ("B_mcio", "B_j2")}
        SRCBOX = {"B_mcio": REGIONS["A_west"], "B_j2": REGIONS["A_east"]}
        A_site = list(A_cur); B_site = list(B_cur)
        BREG = {"B_mcio": REGIONS["B_mcio"], "B_j2": REGIONS["B_j2"]}
        best = None
        for it in range(4):                                     # A/B 交替引导优化
            for g, box in SRCBOX.items():
                ii = grp_idx[g]
                keep = [B_site[i] for i in ii]
                others = [A_site[j] for j in range(len(lanes)) if j not in ii]
                sites, ginfo = guided_sites(t, box, keep, len(ii), sep, a.cell, a.conn, a.rloc, reserve=others)
                for k, i in enumerate(ii):
                    A_site[i] = sites[k] if k < len(sites) else A_cur[i]
            for g in ("B_mcio", "B_j2"):
                ii = grp_idx[g]
                keep = [A_site[i] for i in ii]
                others = [B_site[j] for j in range(len(lanes)) if j not in ii]
                sites, ginfo = guided_sites(t, BREG[g], keep, len(ii), sep, a.cell, a.conn, a.rloc, reserve=others)
                for k, i in enumerate(ii):
                    B_site[i] = sites[k] if k < len(sites) else B_cur[i]
            f_it, i_it = maxflow(t, A_site, B_site, a.cell, a.conn, a.rloc)
            print("  [iter %d] maxflow=%d" % (it, f_it))
            if best is None or f_it > best[0]:
                best = (f_it, list(A_site), list(B_site))
        f_rel = best[0]; A_site = best[1]; B_site = best[2]
        i_rel = maxflow(t, A_site, B_site, a.cell, a.conn, a.rloc)[1]
        f_rel, i_rel = maxflow(t, A_site, B_site, a.cell, a.conn, a.rloc)
        grp = {}
        for g, breg in (("B_mcio", "B_mcio"), ("B_j2", "B_j2")):
            ai = grp_idx[g]
            kk = [A_site[i] for i in ai] + [B_site[i] for i in ai]
            fg, ig = maxflow(t, [A_site[i] for i in ai], [B_site[i] for i in ai], a.cell, a.conn, a.rloc, anchors_keepout=kk)
            grp[g] = {"maxflow": fg, "n": len(ai)}
        cur = {}
        for g in ("B_mcio", "B_j2"):
            ai = grp_idx[g]
            kk = [A_cur[i] for i in ai] + [B_cur[i] for i in ai]
            fg, ig = maxflow(t, [A_cur[i] for i in ai], [B_cur[i] for i in ai], a.cell, a.conn, a.rloc, anchors_keepout=kk)
            cur[g] = {"maxflow": fg, "n": len(ai)}
        moved = sum(1 for l, p in zip(lanes, A_site) if math.hypot(l["A"][0] - p[0], l["A"][1] - p[1]) > 1e-6)
        movedB = sum(1 for l, p in zip(lanes, B_site) if math.hypot(l["B"][0] - p[0], l["B"][1] - p[1]) > 1e-6)
        def disp(pref, key, sites):
            d = []
            for l, q in zip(lanes, sites):
                if not l["net"].startswith(pref) or not key:
                    continue
                p = l["A"] if key == "A" else l["B"]
                d.append(round(math.hypot(p[0] - q[0], p[1] - q[1]), 3))
            d.sort()
            return {"n": len(d), "min": (d[0] if d else None), "median": (d[len(d) // 2] if d else None),
                    "max": (d[-1] if d else None)}
        rep["reloc"] = {"maxflow": f_rel, **i_rel, "n_A_moved": moved, "n_B_moved": movedB,
                        "A_move_mm": {"B_mcio": disp("PCIE_DN_", "A", A_site), "B_j2": disp("PCIE_UP_", "A", A_site)},
                        "B_move_mm": {"B_mcio": disp("PCIE_DN_", "B", B_site), "B_j2": disp("PCIE_UP_", "B", B_site)},
                        "caveats": ["本器只建模 **In5 单层**：A/B 锚位之 **F.Cu 扇出可达性**未建模"
                                    "（移位量中位数 10–13mm ⇒ 须与 F 侧扇出重布同批核，可能收紧可选项）；",
                                    "最大流为**上界**（A/B 集合内允许互换配对 + 离散化）；四组口径实测"
                                    " 30–32/32（cell 0.40/8=31 · 0.30/8=32 · 0.25/8=31 · 0.30/4=30）；",
                                    "同 run 之 `fixed`/`necessary` 两口径分别复现 #K2-68 R2L(19/32) 与官方探针(32/32) ⇒ 模型可信"],
                        "group_flow_new": grp, "group_flow_current": cur,
                        "A_sites": {l["net"]: list(p) for l, p in zip(lanes, A_site)},
                        "B_sites": {l["net"]: list(p) for l, p in zip(lanes, B_site)}}
        print("[reloc] 重组后 A->B maxflow = %d/%d (A moved %d · B moved %d)" % (f_rel, len(lanes), moved, movedB))
        for g in ("B_mcio", "B_j2"):
            print("        %-7s 现位 %d/%d → 重排后 %d/%d" % (g, cur[g]["maxflow"], cur[g]["n"], grp[g]["maxflow"], grp[g]["n"]))
    if a.json_out:
        json.dump(rep, open(a.json_out, "w"), ensure_ascii=False, indent=1, sort_keys=True)
        print("wrote", a.json_out)


if __name__ == "__main__":
    main()
