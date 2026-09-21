#!/usr/bin/env python3
"""K2 · #K2-70 §五-1 之 **F.Cu 扇出精确可达性**（R-A ①）· 只读 · 确定性。

目的：对每条 PCIE 车道，回答「U6 球焊盘（A 侧）/ 连接器焊盘（B 侧）在 **F.Cu 自由空间** 中可达哪些位置」
——即**新锚位可放在哪**（锚孔笼重构设计之硬前提；探针 `--mode reloc` 未建模此项）。

口径（= 判据/DRC 语义 · `--caliber nets_max`）：
- 障碍 = F.Cu 上**其他网**铜（线/孔/盘，按 `max(0.175, netclass(net))` 膨胀；孔另受 `hole_clearance 0.25`
  与 `hole_to_hole 0.25`）+ 禁布线区（`no_tracks`）；
- **本车道自身 F.Cu 铜视为可拆**（扇出要重布）· **可腾挪网**（默认 5 个信号网；可加 GND/P3V3）之走线亦可拆，
  其**孔/盘仍为障碍**（除非以 `--movable-stitch` 指定可腾挪）；
- 源 = 该车道之 F.Cu 焊盘（U6 球 / 连接器端）中心所在自由格；输出**连通域**（8 邻接）。

CLI:
  python3 k2/tools/k2_p4_b2_fcu_fanout_reach_v1.py --model <dump.json> --out <out.json> \
      [--cell 0.2] [--movable-nets a,b] [--movable-stitch c,d] [--json-npz <npz>]
"""
from __future__ import annotations
import argparse, json, math, sys

import numpy as np
from scipy import ndimage

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from k2_p4_b2_in5_capacity_probe_v1 import req, is_lane  # noqa: E402

HW_FCU = 0.20 / 2.0      # 车道 F 扇出线宽口径 0.20 → hw 0.10
EFF_MIN = 0.175
HOLE_CLR = 0.25
HOLE2HOLE = 0.25
LANE_PREFIX = ("PCIE_UP_OUT", "PCIE_DN_OUT")


def eff(net):
    return max(EFF_MIN, req(net))


class R:
    def __init__(self, model, step=0.20):
        x0, y0, x1, y1 = model["bbox"]
        self.X0, self.Y0, self.step = x0, y0, step
        self.NX = int((x1 - x0) / step) + 2
        self.NY = int((y1 - y0) / step) + 2
        self.GX, self.GY = np.meshgrid(x0 + np.arange(self.NX) * step,
                                       y0 + np.arange(self.NY) * step, indexing="ij")

    def _win(self, ax, ay, bx, by, rad):
        return (max(0, int((min(ax, bx) - rad - self.X0) / self.step)),
                min(self.NX - 1, int((max(ax, bx) + rad - self.X0) / self.step) + 1),
                max(0, int((min(ay, by) - rad - self.Y0) / self.step)),
                min(self.NY - 1, int((max(ay, by) + rad - self.Y0) / self.step) + 1))

    def seg(self, bad, ax, ay, bx, by, rad):
        i0, i1, j0, j1 = self._win(ax, ay, bx, by, rad)
        if i1 < i0 or j1 < j0:
            return
        X = self.GX[i0:i1+1, j0:j1+1]; Y = self.GY[i0:i1+1, j0:j1+1]
        dx, dy = bx-ax, by-ay; L2 = dx*dx + dy*dy
        t = np.zeros_like(X) if L2 == 0 else np.clip(((X-ax)*dx + (Y-ay)*dy) / L2, 0, 1)
        bad[i0:i1+1, j0:j1+1] |= (np.hypot(X-(ax+t*dx), Y-(ay+t*dy)) < rad)

    def cir(self, bad, cx, cy, rad):
        i0, i1, j0, j1 = self._win(cx, cy, cx, cy, rad)
        if i1 < i0 or j1 < j0:
            return
        X = self.GX[i0:i1+1, j0:j1+1]; Y = self.GY[i0:i1+1, j0:j1+1]
        bad[i0:i1+1, j0:j1+1] |= (np.hypot(X-cx, Y-cy) < rad)

    def rect(self, bad, x0, y0, x1, y1, rad):
        i0, i1, j0, j1 = self._win(x0, y0, x1, y1, rad)
        if i1 < i0 or j1 < j0:
            return
        X = self.GX[i0:i1+1, j0:j1+1]; Y = self.GY[i0:i1+1, j0:j1+1]
        dx = np.maximum(np.maximum(x0-X, 0), X-x1); dy = np.maximum(np.maximum(y0-Y, 0), Y-y1)
        bad[i0:i1+1, j0:j1+1] |= (np.hypot(dx, dy) < rad)

    def poly(self, bad, pts):
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        i0, i1, j0, j1 = self._win(min(xs), min(ys), max(xs), max(ys), 0.0)
        if i1 < i0 or j1 < j0:
            return
        sub = bad[i0:i1+1, j0:j1+1]
        X = self.GX[i0:i1+1, j0:j1+1].ravel(); Y = self.GY[i0:i1+1, j0:j1+1].ravel()
        inside = np.zeros(X.shape, dtype=bool)
        n = len(pts)
        for k in range(n):
            x1_, y1_ = pts[k]; x2_, y2_ = pts[(k + 1) % n]
            cond = ((y1_ > Y) != (y2_ > Y))
            with np.errstate(divide="ignore", invalid="ignore"):
                xin = (x2_-x1_)*(Y-y1_)/(y2_-y1_) + x1_
            inside ^= cond & (X < xin)
        sub |= inside.reshape(sub.shape)

    def cell(self, x, y):
        return int(round((x - self.X0) / self.step)), int(round((y - self.Y0) / self.step))


def build_fcu(rast, model, movable_tracks, movable_stitch, movable_copper=frozenset()):
    """F.Cu 障碍：其他网铜（孔/盘按同口径）。本批车道之**走线**与 movable 网之走线可拆。"""
    bad = np.zeros((rast.NX, rast.NY), dtype=bool)
    for s in model["segs"]["F.Cu"]:
        net = s[5]
        if is_lane(net) or net in movable_tracks:
            continue
        rast.seg(bad, s[0], s[1], s[2], s[3], HW_FCU + s[4] + eff(net))
    for v in model["vias"]:
        if "F.Cu" not in v["layers"]:
            continue
        net = v["net"]
        if is_lane(net) or net in movable_stitch or net in movable_copper:
            continue
        rad = max(v["r"] + eff(net), v["drill"] + HOLE_CLR)
        rast.cir(bad, v["x"], v["y"], HW_FCU + rad)
    for p in model["pads"]:
        net = p["net"]
        if net in movable_stitch:
            continue
        if "F.Cu" not in p["layers"] and not p["pth"]:
            continue
        if is_lane(net):
            continue                      # 车道自身焊盘：源/端，不作障碍（其扇出可重布）
        b = p["box"]
        rast.rect(bad, b[0], b[1], b[2], b[3], HW_FCU + eff(net))
        if p["pth"] and p.get("drill"):
            rast.cir(bad, p["cx"], p["cy"], HW_FCU + p["drill"] + HOLE_CLR)
    for ra in model["ruleareas"]:
        if not (ra["no_tracks"] and "F.Cu" in ra["layers"]):
            continue
        for poly in ra["polys"]:
            rast.poly(bad, poly)
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cell", type=float, default=0.20)
    ap.add_argument("--movable-nets", default="")
    ap.add_argument("--movable-stitch", default="")
    ap.add_argument("--movable-copper", default="", help="可腾挪网：**孔**可移 · **盘**仍冻结")
    ap.add_argument("--npz", default=None)
    a = ap.parse_args()
    model = json.load(open(a.model))
    movable = set(x for x in a.movable_nets.split(",") if x)
    mstitch = set(x for x in a.movable_stitch.split(",") if x)
    mcopper = set(x for x in a.movable_copper.split(",") if x)
    rast = R(model, a.cell)
    bad = build_fcu(rast, model, movable, mstitch, mcopper)
    free = ~bad
    lab, n = ndimage.label(free, structure=np.ones((3, 3), bool))
    sizes = np.bincount(lab.ravel())

    # 每车道两端焊盘（F.Cu）+ 现锚孔（F–B / F–In2）位置
    lanes = {}
    for v in model["vias"]:
        nm = v["net"]
        if is_lane(nm):
            lanes.setdefault(nm, {"vias": {}, "pads": []})["vias"]["%s-%s" % (v["top"], v["bot"])] = (v["x"], v["y"])
    for p in model["pads"]:
        if is_lane(p["net"]):
            lanes.setdefault(p["net"], {"vias": {}, "pads": []})["pads"].append(
                {"ref": p["ref"], "num": p["num"], "x": p["cx"], "y": p["cy"], "box": p["box"]})

    def comp_of(x, y):
        i, j = rast.cell(x, y)
        if not (0 <= i < rast.NX and 0 <= j < rast.NY):
            return 0
        if lab[i, j]:
            return int(lab[i, j])
        # 就近自由格（至多 1.0mm）
        for r in range(1, int(1.0 / a.cell) + 1):
            best = None
            for di in range(-r, r + 1):
                for dj in range(-r, r + 1):
                    if max(abs(di), abs(dj)) != r:
                        continue
                    ii, jj = i + di, j + dj
                    if 0 <= ii < rast.NX and 0 <= jj < rast.NY and lab[ii, jj]:
                        d = di * di + dj * dj
                        if best is None or d < best[0]:
                            best = (d, int(lab[ii, jj]))
            if best:
                return best[1]
        return 0

    rep = {"artifact": "k2_p4_b2_fcu_fanout_reach_v1", "model": a.model, "cell_mm": a.cell,
           "hw_fcu_mm": HW_FCU, "movable_nets": sorted(movable), "movable_stitch": sorted(mstitch),
           "movable_copper": sorted(mcopper),
           "board": model.get("board"), "n_free_cells": int(free.sum()), "n_components": int(n), "lanes": {}}
    for nm in sorted(lanes):
        d = lanes[nm]
        vA = d["vias"].get("F.Cu-B.Cu"); vB = d["vias"].get("F.Cu-In2.Cu")
        # U6（A 侧）焊盘 = 名字 U6.*；连接器侧 = 其余（J2/J3/MCIO…）
        pA = [p for p in d["pads"] if p["ref"].startswith("U6")]
        pB = [p for p in d["pads"] if not p["ref"].startswith("U6")]
        rec = {"A_anchor": vA, "B_anchor": vB, "pads_A": pA, "pads_B": pB}
        for tag, pads, anchor in (("A", pA, vA), ("B", pB, vB)):
            if not pads:
                rec["%s_reach" % tag] = {"status": "NO_PAD"}; continue
            # 以焊盘中心为源（可能被自身焊盘以外的障碍压住 ⇒ 取最近自由格）
            best = None
            for p in pads:
                c = comp_of(p["x"], p["y"])
                if c:
                    sz = int(sizes[c])
                    if best is None or sz > best[1]:
                        best = (c, sz)
            if best is None:
                rec["%s_reach" % tag] = {"status": "NO_FREE_SOURCE"}; continue
            comp, sz = best
            ii, jj = np.nonzero(lab == comp)
            xs = rast.X0 + ii * a.cell; ys = rast.Y0 + jj * a.cell
            anch_ok = None
            if anchor:
                anch_ok = comp_of(anchor[0], anchor[1]) == comp
            rec["%s_reach" % tag] = {"status": "OK", "comp": comp, "comp_cells": sz,
                                     "bbox": [round(float(xs.min()), 2), round(float(ys.min()), 2),
                                              round(float(xs.max()), 2), round(float(ys.max()), 2)],
                                     "anchor_in_comp": anch_ok}
        rep["lanes"][nm] = rec
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, sort_keys=True)
    okA = sum(1 for r in rep["lanes"].values() if r.get("A_reach", {}).get("anchor_in_comp"))
    okB = sum(1 for r in rep["lanes"].values() if r.get("B_reach", {}).get("anchor_in_comp"))
    print("F.Cu 自由域 %d 格 · 连通域 %d" % (rep["n_free_cells"], rep["n_components"]))
    print("A 侧现锚可达 %d/%d · B 侧现锚可达 %d/%d" % (okA, len(rep["lanes"]), okB, len(rep["lanes"])))
    for nm in sorted(rep["lanes"])[:6]:
        r = rep["lanes"][nm]
        print("  %-26s A:%s B:%s" % (nm, r.get("A_reach"), r.get("B_reach")))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
