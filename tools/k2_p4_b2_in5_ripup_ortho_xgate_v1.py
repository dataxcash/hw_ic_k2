#!/usr/bin/env python3
"""K2 · R163：**正交格路 + 交叉感知（真交点）闸** 版 rip-up。
R162 结论：4 连通消除『格内对角交换』，但**循环之接受判据仍是 v3.exact_gate（盲交叉）**
⇒ 选出的『最佳』解含 5 处**看不见的真交叉**。本驱动把 `v3.exact_gate` 换成
**真交点感知版**（真交叉 ⇒ 距离 0）⇒ 循环的 (routed,-viol) 选择即会把真交叉计为违规。
用法：ortho2_run.py <out.json> <seed> <rout> <cell> [conn=4]"""
import sys, importlib.util, json
import numpy as np
HERE = __file__.rsplit("/",1)[0].rsplit("/",1)[0]
out, seed, rout, cell = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
conn = int(sys.argv[5]) if len(sys.argv) > 5 else 4
spec = importlib.util.spec_from_file_location("v3m", HERE + "/tools/k2_p4_b2_in5_lane_router_v3.py")
v3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v3)
if conn == 4:
    v3.NBR = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0)]

_orig = v3.exact_gate
def _orient(p, q, r):
    return (q[..., 0] - p[..., 0]) * (r[..., 1] - p[..., 1]) - (q[..., 1] - p[..., 1]) * (r[..., 0] - p[..., 0])
def _cross_mask(A, B):
    A0 = A[:, None, 0, :]; A1 = A[:, None, 1, :]; B0 = B[None, :, 0, :]; B1 = B[None, :, 1, :]
    d1 = _orient(B0, B1, A0); d2 = _orient(B0, B1, A1)
    d3 = _orient(A0, A1, B0); d4 = _orient(A0, A1, B1)
    return ((d1 > 0) != (d2 > 0)) & ((d3 > 0) != (d4 > 0))
def patched_gate(model, routes, anchors, layer, hw, movable_tracks, movable_vias, pitch, movable_copper=frozenset()):
    g = _orig(model, routes, anchors, layer, hw, movable_tracks, movable_vias, pitch, movable_copper)
    segs = {nm: np.array([[(p[k][0], p[k][1]), (p[k + 1][0], p[k + 1][1])]
                          for k in range(len(p) - 1)], np.float64)
            for nm, r in routes.items() for p in [ [tuple(q) for q in r["pts"]] ] if len(p) > 1}
    names = sorted(segs); pm = (1e9, None); vp = []; ncr = 0
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            A = segs[names[i]]; B = segs[names[j]]
            d = v3._seg_seg_batch(A, B)
            cm = _cross_mask(A, B)
            if cm.any():
                ncr += 1; dd = 0.0
            else:
                dd = float(d.min())
            if dd < pitch - 1e-6:
                vp.append((names[i], names[j], round(dd, 4)))
            if dd < pm[0]:
                pm = (dd, (names[i], names[j]))
    g["lane_pitch_min_gap_mm"] = round(pm[0], 4); g["lane_pitch_min_pair"] = pm[1]
    g["n_lane_pitch_viol"] = len(vp); g["lane_pitch_violations"] = vp[:20]
    g["n_true_crossing_pairs"] = ncr
    return g
v3.exact_gate = patched_gate

MOV = ",".join(json.load(open("/tmp/opencode/archer/wo_R159.json"))["movable_nets"])
B = HERE + "/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/R149_b_alloc_s2.00.json"
A = HERE + "/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/R149_a_grpsep.json"
sys.argv = ["ripup", "--model", "/tmp/opencode/r1e_dump_v1.json", "--out", out,
  "--cell", cell, "--margin", "0.100", "--iters", "26", "--k0", "8", "--kgrow", "3",
  "--rmin", "0.5057", "--rout", rout, "--seed", seed,
  "--excl", "PCIE_DN_OUT:84.0,53.0,101.0,58.5;PCIE_UP_OUT:84.0,48.0,101.0,53.0",
  "--a-sites", A, "--b-sites", B,
  "--movable-nets", MOV, "--movable-stitch", "GND,P3V3", "--movable-copper", MOV + ",GND,P3V3"]
spec2 = importlib.util.spec_from_file_location("ripup", HERE + "/tools/k2_p4_b2_in5_ripup_v1.py")
m = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(m)
m.v3 = v3
m.main()
