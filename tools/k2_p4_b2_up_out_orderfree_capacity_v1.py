#!/usr/bin/env python3
"""K2 · R273 —— ②-UP **与顺序无关的守恒级容量复核**（只读 · 零搜索 · 零重跑布线器）

目的（监理停止令 · 本 tick）：判定能否签「守恒级不可行证书」。
方法：**不假定任何列序、不假定固定列位**。对每一高度 y，比较
  ① 该高度**必须存在**的车道数  |P(y)| = #{j : y_B,j ≤ y}   （全 In5 长走：车道自南(y≈55.5)北行至其 B 锚 y_B）
  ② 该高度 In5 的免费横截面槽位数（x∈[130.0,143.05] · 0.435 节距 · 板边距 0.300 + 半线宽 0.08）
结论：|P(y)| ≤ 槽位 · **最小余量 +12** ⇒ **不存在 <16 的容量/割障碍** ⇒ (b) 不可得。

复现（两步 · 全只读）：
  $ AppDir/usr/bin/python3.11 k2/tools/k2_p4_b2_board_in5_model_dump_v1.py k2/hw/k2_v4_8L.l8.kicad_pcb /tmp/opencode/archer/model_l8.json
  $ python3 k2/tools/k2_p4_b2_up_out_orderfree_capacity_v1.py /tmp/opencode/archer/model_l8.json
退出码 0 = 余量全为正（= 无守恒级障碍 / (b) 不可得）。
"""
import json, math, sys
import numpy as np

PITCH, EDGE_CLR, HW, EFF = 0.435, 0.300, 0.080, 0.175
XLO, XHI = 130.0, 143.05
YS = [55.5, 54.0, 53.0, 52.85, 52.0, 51.65, 50.0, 49.25, 48.05, 47.45, 46.25, 44.0, 43.85, 42.65]


def lane_anchors(model):
    LANES = {f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N", "P")}
    seen = {}
    for v in model["vias"]:
        if v["net"] in LANES:
            seen.setdefault(v["net"], {})["%s-%s" % (v["top"], v["bot"])] = (v["x"], v["y"])
    return {n: {"A": d["F.Cu-B.Cu"], "B": d["F.Cu-In2.Cu"]} for n, d in seen.items()}


def free_bands(model, y, x0=XLO, x1=XHI, step=0.01):
    L = "In5.Cu"
    xs = np.arange(x0, x1 + 1e-9, step)
    block = np.zeros((len(xs),), dtype=bool)
    for s in model["segs"][L]:
        ax, ay, bx, by, w, net = s
        rad = HW + w + EFF
        if min(ax, bx) - rad - step > x1 or max(ax, bx) + rad + step < x0: continue
        if min(ay, by) - rad - step > y or max(ay, by) + rad + step < y: continue
        ddx, ddy = bx - ax, by - ay; l2 = ddx * ddx + ddy * ddy
        t = 0.0 if l2 == 0 else np.clip(((xs - ax) * ddx + (y - ay) * ddy) / l2, 0, 1)
        block |= np.hypot(xs - (ax + t * ddx), y - (ay + t * ddy)) < rad
    for v in model["vias"]:
        if L not in v["layers"] or abs(v["y"] - y) > 1.0: continue
        rad = HW + max(v["r"] + EFF, v["drill"] + 0.25)
        block |= np.hypot(xs - v["x"], y - v["y"]) < rad
    for p in model["pads"]:
        if L not in p["layers"] and not p["pth"]: continue
        bx0, by0, bx1, by1 = p["box"]
        rad = HW + EFF
        if by0 - rad - step > y or by1 + rad + step < y: continue
        ddx = np.maximum(np.maximum(bx0 - xs, 0), xs - bx1)
        ddy = np.maximum(np.maximum(by0 - y, 0), y - by1)
        block |= np.hypot(ddx, ddy) < rad
    bands, cur = [], None
    for x, f in zip(xs, ~block):
        if f and cur is None: cur = x
        if not f and cur is not None: bands.append((float(cur), float(x))); cur = None
    if cur is not None: bands.append((float(cur), float(xs[-1])))
    return [(a, b) for a, b in bands if b - a > 0.05]


def main():
    m = json.load(open(sys.argv[1], "rb"))
    anch = lane_anchors(m)
    xhi = m["bbox"][2] - EDGE_CLR - HW
    rows, ok = [], True
    for y in YS:
        n = sum(1 for j in anch if anch[j]["B"][1] <= y + 1e-9)
        slots = 0
        for a, b in free_bands(m, y):
            b = min(b, xhi)
            if b > a: slots += int(math.floor((b - a) / PITCH + 1e-9)) + 1
        rows.append({"y": y, "present": n, "slots": slots, "margin": slots - n})
        ok = ok and (slots - n) > 0
    print(json.dumps({"tool": "k2_p4_b2_up_out_orderfree_capacity_v1",
                      "caliber": {"pitch": PITCH, "edge_clr": EDGE_CLR, "hw": HW, "eff": EFF,
                                  "x_span": [XLO, XHI]}, "rows": rows,
                      "min_margin": min(r["margin"] for r in rows)}, ensure_ascii=False, indent=1))
    print("\n[VERDICT] min_margin=%d (>0 ⇒ 无守恒级容量障碍 ⇒ (b) 守恒级不可行证书不可得) => %s"
          % (min(r["margin"] for r in rows), "NO_CONSERVATION_BOUND" if ok else "BOUND_EXISTS"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
