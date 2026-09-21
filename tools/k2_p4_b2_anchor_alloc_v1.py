#!/usr/bin/env python3
"""K2 · B2 —— **锚位协同指派器 v1**（A/B 双侧 · 成对/全局 · 确定性 · 只读）。

缘起（R136 根因 + r136b 反例）：32 条车道之差分对锚位在 margin 0.100 口径下**互封锁**
（对间距 0.600mm < 2×(via_r + (0.175+margin) + hw) = 1.06mm）；且**逐车道贪心候选位不可用**
（锚孔掩码静态 ⇒ 位移不生效 + 差分对须协同外移）。本器改为**先联合指派、后布线**：
  ① 以**合法晶格**（via 口径 ∩ 规则派生 movable 口径）为候选；
  ② **全局贪心**排布 A 侧 32 位 / B 侧每组 16 位，约束 = **两两中心距 ≥ --min-sep**（默认 1.40mm）；
  ③ 输出**单一锚位集**（无候选）⇒ 交给 `k2_p4_b2_in5_lane_router_v3.py`（其掩码依最终锚位一次算定 ⇒ 无静态掩码缺陷）。

CLI:
  python3 tools/k2_p4_b2_anchor_alloc_v1.py --model <dump.json> --movable <derive.json> \
      --out-a <a_sites.json> --out-b <b_sites.json> [--cell 0.2] [--min-sep 1.40] [--margin 0.10] \
      [--a-region x0,y0,x1,y1] [--b-radius 3.0]
"""
from __future__ import annotations
import argparse, json, math, sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from k2_p4_b2_in5_capacity_probe_v1 import req, is_lane  # noqa: E402

EFF_MIN, HOLE_CLR, HW = 0.175, 0.25, 0.08
LANE_PREFIX = ("PCIE_UP_OUT", "PCIE_DN_OUT")
REG_ORC = (78.0, 45.0, 100.0, 66.0)


def eff(n):
    return max(EFF_MIN, req(n))


def in_orc(x, y):
    return REG_ORC[0] <= x <= REG_ORC[2] and REG_ORC[1] <= y <= REG_ORC[3]


def in_region(ax, ay, bx, by, R):
    return (max(ax, bx) >= R[0] and min(ax, bx) <= R[2]
            and max(ay, by) >= R[1] and min(ay, by) <= R[3])


class Legal:
    def __init__(self, model, mov, pad_extra):
        self.segs, self.vias, self.pads = [], [], []
        for s in model["segs"]["In5.Cu"]:
            n = s[5]
            if is_lane(n) or (n in mov and in_region(s[0], s[1], s[2], s[3], REG_ORC)):
                continue
            self.segs.append((s[0], s[1], s[2], s[3], s[4], n))
        for v in model["vias"]:
            if "In5.Cu" not in v["layers"]:
                continue
            n = v["net"]
            if is_lane(n) or (n in mov and in_orc(v["x"], v["y"])):
                continue
            self.vias.append((v["x"], v["y"], max(v["r"], v["drill"]), n))
        for p in model["pads"]:
            n = p["net"]
            if is_lane(n) or (n in mov and in_orc(p["cx"], p["cy"])):
                continue
            if "In5.Cu" not in p["layers"] and not p["pth"]:
                continue
            b = p["box"]
            self.pads.append((b[0], b[1], b[2], b[3], n))
        self.pe = pad_extra

    def ok(self, X, Y):
        need_seg = HW + self.pe
        for (ax, ay, bx, by, r, n) in self.segs:
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((X - ax) * dx + (Y - ay) * dy) / L2))
            if math.hypot(X - (ax + t * dx), Y - (ay + t * dy)) < r + need_seg + eff(n):
                return False
        for (vx, vy, vr, n) in self.vias:
            if math.hypot(X - vx, Y - vy) < vr + need_seg + eff(n):
                return False
        for (x0, y0, x1, y1, n) in self.pads:
            dxx = max(x0 - X, 0.0, X - x1); dyy = max(y0 - Y, 0.0, Y - y1)
            if math.hypot(dxx, dyy) < need_seg + eff(n):
                return False
        return True


def greedy_pick(pts, n, sep):
    chosen = []
    for p in pts:
        if all(math.dist(p, c) >= sep - 1e-9 for c in chosen):
            chosen.append(p)
            if len(chosen) == n:
                return chosen
    return chosen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--movable", required=True)
    ap.add_argument("--out-a", required=True)
    ap.add_argument("--out-b", required=True)
    ap.add_argument("--cell", type=float, default=0.2)
    ap.add_argument("--min-sep", type=float, default=1.40)
    ap.add_argument("--margin", type=float, default=0.10)
    ap.add_argument("--a-region", default="83.95,49.40,101.00,58.60")
    ap.add_argument("--b-radius", type=float, default=3.0)
    a = ap.parse_args()
    model = json.load(open(a.model))
    mov = set(json.load(open(a.movable))["movable_nets"])
    pe = a.margin + 0.5 * a.cell * math.sqrt(2)
    L = Legal(model, mov, pe)
    import importlib.util
    spec = importlib.util.spec_from_file_location("v3", __file__.rsplit("/", 1)[0] + "/k2_p4_b2_in5_lane_router_v3.py")
    v3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v3)
    anchors = v3.lane_anchors(model)
    AR = tuple(float(x) for x in a.a_region.split(","))

    # ---- A 侧：全局晶格 → 合法 → 贪心 32 位 ----
    lat = []
    y = AR[1]
    while y <= AR[3] + 1e-9:
        x = AR[0]
        while x <= AR[2] + 1e-9:
            if L.ok(x, y):
                lat.append((round(x, 2), round(y, 2)))
            x += a.cell
        y += a.cell
    lat.sort(key=lambda p: (p[1], p[0]))
    A32 = greedy_pick(lat, 32, a.min_sep)
    print("A 侧：合法格 %d ⇒ 贪心 ≥%.2fmm 得 %d 位" % (len(lat), a.min_sep, len(A32)))

    # ---- B 侧：每组在其焊盘附近取合法格，组内互距 ≥ min-sep ----
    def group(pref):
        return [an for an in anchors if an["net"].startswith(pref)]
    outB = {}
    for pref, tag in (("PCIE_DN_OUT", "DN"), ("PCIE_UP_OUT", "UP")):
        g = group(pref)
        pool = []
        for an in g:
            bx, by = an["B"]
            r = a.cell
            while r <= a.b_radius + 1e-9:
                for k in range(0, 24):
                    th = 2 * math.pi * k / 24
                    x = bx + r * math.cos(th); y = by + r * math.sin(th)
                    if L.ok(x, y):
                        pool.append((round(x, 2), round(y, 2), an["net"]))
                r += a.cell
        # 全局贪心：按「距本车道 B 之距离」升序取，互距 ≥ min_sep
        pool.sort(key=lambda q: (math.dist(q[:2], [dict((x["net"], x["B"]) for x in g)[q[2]]][0]), q[2]))
        picked = {}
        for (x, y, net) in pool:
            if net in picked:
                continue
            if all(math.dist((x, y), p) >= a.min_sep - 1e-9 for p in picked.values()):
                picked[net] = [x, y]
            if len(picked) == len(g):
                break
        outB.update(picked)
        print("B 侧 %s：%d/%d 位（≥%.2fmm）" % (tag, len(picked), len(g), a.min_sep))

    # ---- 分配 A32 给 32 条车道：DN 取下 16（y 小 / x 小优先），UP 取上 16 ----
    A32s = sorted(A32, key=lambda p: (p[1], p[0]))
    dn = sorted(an["net"] for an in group("PCIE_DN_OUT"))
    up = sorted(an["net"] for an in group("PCIE_UP_OUT"))
    outA = {}
    for net, p in zip(dn, A32s[:len(dn)]):
        outA[net] = [p[0], p[1]]
    for net, p in zip(up, A32s[len(dn):len(dn) + len(up)]):
        outA[net] = [p[0], p[1]]
    json.dump(outA, open(a.out_a, "w"), ensure_ascii=False, indent=1, sort_keys=True)
    json.dump(outB, open(a.out_b, "w"), ensure_ascii=False, indent=1, sort_keys=True)
    allA = list(outA.values())
    mnA = min(math.dist(x, y) for i, x in enumerate(allA) for y in allA[i + 1:]) if len(allA) > 1 else 0
    allB = list(outB.values())
    mnB = min(math.dist(x, y) for i, x in enumerate(allB) for y in allB[i + 1:]) if len(allB) > 1 else 0
    print("A 位集 %d（min %.3f）· B 位集 %d（min %.3f）" % (len(outA), mnA, len(outB), mnB))
    print("wrote", a.out_a, a.out_b)


if __name__ == "__main__":
    main()
