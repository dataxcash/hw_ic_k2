#!/usr/bin/env python3
"""K2 · B2 —— **A 锚笼分组分离派生器 v1**（#K2-72 Q2/Q3 · 判据⑩ 自板派生 · 确定性 · 只读）。

缘起（R140 实测）：DN 与 UP 之 A 锚位若同处一带（y 重叠），则 **DN 侧西行车队之 ±0.5764 硬禁带
封死 UP 侧 A 锚**（实测：pin DN 见证解后 UP 12 条端点不可行 / 端点偏移 14.4mm）⇒ A 锚笼必须
**按 DN/UP 分组分离**：
  · DN 亚带 = 南（y 小）· UP 亚带 = 北（y 大）· 组内 pitch ≥ --sep（默认 1.70 = #K2-72 Q2 下限）
  · 组间净距 ≥ --gap（默认 ≥1.70 · 实测取 3.69 可用）
  · 组内指派 = **最小权指派（Hungarian）**（经典反证保证**非交叉** ⇒ 拓扑正确 · #K2-72 Q3）
输出：a_sites.json（net→A 位）· 只读板件 · 确定性。

CLI:
  python3 tools/k2_p4_b2_a_cage_groupsep_v1.py --model <dump.json> --movable <derive.json> \
      --b-sites <b.json> --out-a <a.json> [--cell 0.2] [--sep 1.70]
"""
from __future__ import annotations
import argparse, json, math, sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import importlib.util
import numpy as np
from scipy.optimize import linear_sum_assignment

spec = importlib.util.spec_from_file_location("aa", __file__.rsplit("/", 1)[0] + "/k2_p4_b2_anchor_alloc_v1.py")
aa = importlib.util.module_from_spec(spec); spec.loader.exec_module(aa)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True); ap.add_argument("--movable", required=True)
    ap.add_argument("--b-sites", required=True); ap.add_argument("--out-a", required=True)
    ap.add_argument("--cell", type=float, default=0.2); ap.add_argument("--sep", type=float, default=1.70)
    ap.add_argument("--margin", type=float, default=0.10)
    ap.add_argument("--dn-y", default="48.0,51.6"); ap.add_argument("--up-y", default="53.2,58.8")
    ap.add_argument("--x", default="83.9,101.0")
    a = ap.parse_args()
    model = json.load(open(a.model)); mov = set(json.load(open(a.movable))["movable_nets"])
    pe = a.margin + 0.5 * a.cell * math.sqrt(2)
    L = aa.Legal(model, mov, pe)
    x0, x1 = [float(t) for t in a.x.split(",")]
    lat = []
    y = 48.0
    while y <= 58.8 + 1e-9:
        x = x0
        while x <= x1 + 1e-9:
            if L.ok(x, y):
                lat.append((round(x, 2), round(y, 2)))
            x += a.cell
        y += a.cell
    lat.sort(key=lambda p: (p[1], p[0]))

    def pick(rng, n):
        ch = []
        for p in rng:
            if all(math.dist(p, c) >= a.sep - 1e-9 for c in ch):
                ch.append(p)
                if len(ch) == n:
                    return ch
        return ch
    dy0, dy1 = [float(t) for t in a.dn_y.split(",")]; uy0, uy1 = [float(t) for t in a.up_y.split(",")]
    A_dn = pick([p for p in lat if dy0 <= p[1] <= dy1], 16)
    A_up = pick([p for p in lat if uy0 <= p[1] <= uy1], 16)
    b = json.load(open(a.b_sites))
    out = {}
    for grp, pts in (("PCIE_DN", A_dn), ("PCIE_UP", A_up)):
        nets = sorted(n for n in b if n.startswith(grp))
        B = np.array([b[n] for n in nets]); P = np.array(pts)
        C = np.linalg.norm(P[:, None, :] - B[None, :, :], axis=2)
        r, c = linear_sum_assignment(C)
        for i, j in zip(r, c):
            out[nets[j]] = [float(P[i][0]), float(P[i][1])]
    json.dump(out, open(a.out_a, "w"), ensure_ascii=False, indent=1, sort_keys=True)
    gap = min(math.dist(p, q) for p in A_dn for q in A_up) if A_dn and A_up else 0
    print("DN 亚带 %d（y %.1f–%.1f）· UP 亚带 %d（y %.1f–%.1f）· 组间最小距 %.2fmm（要求 ≥%.2f）"
          % (len(A_dn), min(p[1] for p in A_dn), max(p[1] for p in A_dn),
             len(A_up), min(p[1] for p in A_up), max(p[1] for p in A_up), gap, a.sep))
    print("wrote", a.out_a)


if __name__ == "__main__":
    main()
