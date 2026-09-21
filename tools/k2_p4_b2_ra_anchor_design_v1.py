#!/usr/bin/env python3
"""K2 · #K2-70 §五-1（R-A）之 **锚位集设计**（A 侧 · 只读 · 确定性）。

输入：`k2_p4_b2_fcu_fanout_reach_v1` 之可达性结论（A 侧 = 两条窄带）+ dump。
输出：每车道之 **A 锚候选位**（F.Cu 可达 ∩ **via 合法**）与**具名锚位集**（每带 2 行 · 行内列距 ≥ `--min-sep`）。

口径：
- **via 合法** = F.Cu 上以该点为心的 via 圆（r=`--via-r`=0.175）与**其他网**铜边距 ≥ `max(0.175,netclass)`，
  且**孔到孔** ≥ 0.25mm、孔到铜 ≥ 0.25mm（对 F.Cu 其余网孔洞）；
- **F.Cu 可达** = 复用 `k2_p4_b2_fcu_fanout_reach_v1`：U6 球焊盘 → 该点（本车道扇出可拆）；
- **锚间** 相邻中心距 ≥ `--min-sep`（默认 0.905 = 2×(LANE_HW+via_r) ⇒ 允许他车道从锚间穿越）。

CLI:
  python3 k2/tools/k2_p4_b2_ra_anchor_design_v1.py --model <dump.json> --out <json> \
      [--cell 0.10] [--min-sep 0.905] [--movable-nets a,b]
"""
from __future__ import annotations
import argparse, json, math, sys

import numpy as np
from scipy import ndimage

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import k2_p4_b2_fcu_fanout_reach_v1 as FR  # noqa: E402
from k2_p4_b2_in5_capacity_probe_v1 import req, is_lane  # noqa: E402

VIA_R = 0.175
HOLE_CLR = 0.25
EFF_MIN = 0.175


def build_fcu(rast, model, movable, hw, include_holes=True):
    """F.Cu 障碍：其他网铜按 `hw + eff` 膨胀；车道自身走线与 movable 网走线可拆（孔/盘仍为障碍）。"""
    bad = np.zeros((rast.NX, rast.NY), dtype=bool)
    for s in model["segs"]["F.Cu"]:
        net = s[5]
        if is_lane(net) or net in movable:
            continue
        rast.seg(bad, s[0], s[1], s[2], s[3], hw + s[4] + max(EFF_MIN, req(net)))
    for v in model["vias"]:
        if "F.Cu" not in v["layers"]:
            continue
        net = v["net"]
        if is_lane(net) or net in movable:
            continue
        rad = max(v["r"] + max(EFF_MIN, req(net)), (v["drill"] + HOLE_CLR) if include_holes else 0.0)
        rast.cir(bad, v["x"], v["y"], hw + rad)
    for p in model["pads"]:
        net = p["net"]
        if net in movable or is_lane(net):
            continue
        if "F.Cu" not in p["layers"] and not p["pth"]:
            continue
        b = p["box"]
        rast.rect(bad, b[0], b[1], b[2], b[3], hw + max(EFF_MIN, req(net)))
        if p["pth"] and p.get("drill"):
            rast.cir(bad, p["cx"], p["cy"], hw + p["drill"] + HOLE_CLR)
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
    ap.add_argument("--cell", type=float, default=0.10)
    ap.add_argument("--min-sep", type=float, default=0.905)
    ap.add_argument("--movable-nets", default="")
    a = ap.parse_args()
    model = json.load(open(a.model))
    movable = set(x for x in a.movable_nets.split(",") if x)
    rast = FR.R(model, a.cell)
    # ① 走线口径可达（扇出可达）
    bad_trk = build_fcu(rast, model, movable, hw=0.20 / 2.0)
    # ② via 口径合法（锚孔本体）
    bad_via = build_fcu(rast, model, movable, hw=VIA_R)
    lab, n = ndimage.label(~bad_trk, structure=np.ones((3, 3), bool))
    via_ok = ~bad_via
    ok_component = lab.astype(bool)          # 可达性以走线口径连通域为准
    cand = via_ok & ok_component

    lanes = {}
    for v in model["vias"]:
        nm = v["net"]
        if is_lane(nm):
            lanes.setdefault(nm, {})["%s-%s" % (v["top"], v["bot"])] = (v["x"], v["y"])
    pads = {}
    for p in model["pads"]:
        if is_lane(p["net"]) and p["ref"].startswith("U6"):
            pads.setdefault(p["net"], []).append((p["cx"], p["cy"]))

    rep = {"artifact": "k2_p4_b2_ra_anchor_design_v1", "model": a.model, "cell_mm": a.cell,
           "min_sep_mm": a.min_sep, "via_r_mm": VIA_R, "movable_nets": sorted(movable),
           "method": "A 侧锚候选 = F.Cu 走线口径可达连通域 ∩ via 口径合法；再按带(连通域)做 2 行 × 列距 ≥min_sep 之具名锚位集",
           "bands": {}, "lanes": {}}

    # 按可达连通域（= A 侧窄带）分组
    groups = {}
    for nm, d in lanes.items():
        anchor = d.get("F.Cu-B.Cu")
        if not anchor:
            continue
        i, j = rast.cell(*anchor)
        c = int(lab[i, j]) if (0 <= i < rast.NX and 0 <= j < rast.NY) else 0
        if c == 0:      # 现锚点必须落在可达域（R-A-① 已验证 32/32）
            c = -1
        groups.setdefault(c, []).append(nm)
        rep["lanes"][nm] = {"cur_anchor": anchor, "comp": c, "pad_A": pads.get(nm)}

    for c, nms in sorted(groups.items()):
        # 该带候选格
        mask = cand.copy()
        if c > 0:
            mask &= (lab == c)
        ii, jj = np.nonzero(mask & (lab == c if c > 0 else True))
        pts = sorted([(round(rast.X0 + i * a.cell, 3), round(rast.Y0 + j * a.cell, 3)) for i, j in zip(ii, jj)])
        band = {"comp": c, "n_lanes": len(nms), "n_cand_cells": len(pts),
                "bbox": [min(p[0] for p in pts), min(p[1] for p in pts),
                         max(p[0] for p in pts), max(p[1] for p in pts)] if pts else None,
                "lanes": sorted(nms)}
        # 2 行 × 8 位（贪心：按 y 分两层，层内按 x 等距抽稀至 ≥min_sep）
        if pts:
            ys = sorted(set(p[1] for p in pts))
            ylo, yhi = ys[0], ys[-1]
            rows = [y for y in ys if abs(y - (ylo + 0.25)) <= 0.35] or [ylo]
            rows2 = [y for y in ys if abs(y - (yhi - 0.25)) <= 0.35] or [yhi]
            def pick(rows_):
                out = []
                for y in rows_:
                    xs = sorted(p[0] for p in pts if abs(p[1] - y) < 1e-9)
                    last = None
                    for x in xs:
                        if last is None or x - last >= a.min_sep:
                            out.append([x, y]); last = x
                return out
            slots = pick(rows) + pick(rows2)
            band["rows_y"] = [rows[0], rows2[0]]
            band["n_slots_2row"] = len(slots)
            band["slots"] = slots
        rep["bands"]["comp_%s" % c] = band

    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, sort_keys=True)
    for k, b in rep["bands"].items():
        print("%s: lanes %d · 候选格 %d · bbox %s · 行 y=%s · 2 行槽位 %s" %
              (k, b["n_lanes"], b["n_cand_cells"], b["bbox"], b.get("rows_y"), b.get("n_slots_2row")))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
