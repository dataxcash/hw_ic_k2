#!/usr/bin/env python3
"""K2 · 真实几何闸（crossing-aware）—— 对 #K2-72 §二 `exact_gate` 的**加严**复核器。

动机（R161 实测 D-4）：v3 `exact_gate` 之 `_seg_seg_batch` 仅取「4 个端点到对侧段」之最小距离，
**不含两段内部真交点判定** ⇒ 两条车道**真实交叉（短路）时可报出 >0 之距离**（R159 实测：3 对真交叉
被报为 0.0707 而非 0.0）。本器按**精确段-段最小距离（含真交点 ⇒ 0）**复算，只加严、不放松。

用法：python3 true_gate.py <wo.json> [pitch]
"""
import json, math, sys

def pt_seg(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
    if L2 == 0: return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

def cross(o, p, q):
    return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])

def seg_seg(p1, p2, p3, p4):
    """returns (dist, is_true_crossing)."""
    d1 = cross(p3, p4, p1); d2 = cross(p3, p4, p2)
    d3 = cross(p1, p2, p3); d4 = cross(p1, p2, p4)
    if ((d1 > 1e-12) != (d2 > 1e-12)) and ((d3 > 1e-12) != (d4 > 1e-12)):
        return 0.0, True
    m = min(pt_seg(p1, p3, p4), pt_seg(p2, p3, p4), pt_seg(p3, p1, p2), pt_seg(p4, p1, p2))
    return m, False

def main():
    wo = json.load(open(sys.argv[1]))
    pitch = float(sys.argv[2]) if len(sys.argv) > 2 else 0.435
    R = {n: [(float(a), float(b)) for a, b in r["pts"]] for n, r in wo["routes"].items()}
    names = sorted(R)
    viol = []; ncross = 0; minall = (1e9, None)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            A = R[names[i]]; B = R[names[j]]
            best = 1e9; ncr = 0
            for k in range(len(A) - 1):
                for l in range(len(B) - 1):
                    dd, c = seg_seg(A[k], A[k + 1], B[l], B[l + 1])
                    if c: ncr += 1
                    if dd < best: best = dd
            if ncr: ncross += 1
            if best < minall[0]: minall = (best, (names[i], names[j]))
            if best < pitch - 1e-6:
                viol.append((names[i], names[j], round(best, 4), ncr))
    out = {"wo": sys.argv[1], "n_lanes": len(names), "n_routed": wo.get("n_routed"),
           "pitch_req_mm": pitch, "min_exact_pair_mm": round(minall[0], 4),
           "min_pair": minall[1], "n_pairs_below_pitch": len(viol),
           "n_pairs_true_crossing": ncross, "violations": viol,
           "v3_gate_n_lane_pitch_viol": (wo.get("geometric_gate") or {}).get("n_lane_pitch_viol"),
           "v3_gate_min_gap_mm": (wo.get("geometric_gate") or {}).get("lane_pitch_min_gap_mm"),
           "obstacle_clearance_min_mm": (wo.get("geometric_gate") or {}).get("clearance_min_mm")}
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
