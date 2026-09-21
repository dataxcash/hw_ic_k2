#!/usr/bin/env python3
"""K2 · R328 · ②-UP **硬约束联合指派（一次实现）**：
   每 lane 之候选 = 「过 (B.x, y) 之最短路」（A→(B.x,y) ⊕ (B.x,y)→B，由两株最短路树拼成，精确·端点不动）
   MILP（HiGHS）：每 lane 至多一候选；两候选若折线精确距离 < pitch 则互斥（**硬约束**）⇒ max Σ 选。
   见证只由 `exact_gate` 判。只读 · 不改生成器 · 不写板。
用法: python3 joint_hard_assign.py <model_l8.json> <out.json> [cell] [level_step]
"""
import sys, json, math, importlib.util, hashlib
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.optimize import milp, LinearConstraint, Bounds

V3 = "k2/tools/k2_p4_b2_in5_lane_router_v3.py"
LANES = {f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N", "P")}
spec = importlib.util.spec_from_file_location("v3", V3)
v3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v3)
v3.is_lane = lambda n: n in LANES
MODEL, OUT = sys.argv[1], sys.argv[2]
CELL = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05
LSTEP = float(sys.argv[4]) if len(sys.argv) > 4 else 0.50
HW, P = 0.08, 0.435
model = json.load(open(MODEL))
rast = v3.Raster((82.0, 36.0, 144.0, 66.0), CELL)
bad = v3.build_base(rast, model, "In5.Cu", frozenset(), frozenset(), HW, frozenset())
ad = {a["net"]: a for a in v3.lane_anchors(model)}
NX, NY = rast.NX, rast.NY
anchor_bad = np.zeros((NX, NY), bool); own = {}
for n in LANES:
    a = ad[n]; mm = np.zeros((NX, NY), bool)
    v3.Raster.cir(rast, mm, a["A"][0], a["A"][1], P); v3.Raster.cir(rast, mm, a["B"][0], a["B"][1], P)
    own[n] = mm; anchor_bad |= mm
LANE_ORD = sorted(LANES, key=lambda k: ad[k]["B"][0])

cands = {}          # n -> list of {y, pts(list of (x,y)), cells(set)}
for n in LANE_ORD:
    a = ad[n]
    allowed = (~bad) & (~(anchor_bad & ~own[n]))
    G, idx = v3.build_topology(allowed, CELL)
    ii, jj = np.nonzero(allowed)
    nr = rast.NX  # not used
    m_ = np.full(NX * NY, -1, np.int64); m_[ii * NY + jj] = np.arange(len(ii), dtype=np.int64)
    sA = idx[rast.cell(*a["A"])]; sB = idx[rast.cell(*a["B"])]
    dA, pA = dijkstra(G, directed=True, indices=int(sA), return_predecessors=True)
    Gt = G.transpose().tocsr()
    dB, pB = dijkstra(Gt, directed=True, indices=int(sB), return_predecessors=True)   # dB[k] = dist(k -> B)
    bx = a["B"][0]; col = rast.cell(bx, 0)[0]
    lst = []
    for y in np.arange(38.0, 64.0 + 1e-9, LSTEP):
        j = rast.cell(bx, y)[1]
        if not (0 <= col < NX and 0 <= j < NY): continue
        k = int(idx[col, j])
        if k < 0 or not np.isfinite(dA[k]) or not np.isfinite(dB[k]): continue
        pa = v3.path_from_pred(pA, int(sA), k); pb = v3.path_from_pred(pB, int(sB), k)
        if pa is None or pb is None: continue
        ids = pa + pb[::-1][1:]     # A -> k -> B
        pts = [(a["A"][0], a["A"][1])] + [(rast.X0 + int(ii[t]) * CELL, rast.Y0 + int(jj[t]) * CELL) for t in ids] + [(a["B"][0], a["B"][1])]
        pts = v3.simplify(pts)
        lst.append({"y": round(float(y), 3), "pts": [[round(x, 4), round(yy, 4)] for x, yy in pts]})
    cands[n] = lst
    print("  %-8s cands=%d" % (n[10:-3], len(lst)))

# --- 冲突（折线精确最小距离 < pitch）---
def segs_np(pts):
    return np.array([[(pts[k][0], pts[k][1]), (pts[k + 1][0], pts[k + 1][1])] for k in range(len(pts) - 1)], np.float64)
IDX = {}; var = []
for n in LANE_ORD:
    for c in range(len(cands[n])):
        IDX[(n, c)] = len(var); var.append((n, c))
N = len(var); print("binaries", N)
SEG = {v: segs_np(cands[v[0]][v[1]]["pts"]) for v in var}
rows = []; cols = []
for a in range(len(LANE_ORD)):
    for b in range(a + 1, len(LANE_ORD)):
        n1, n2 = LANE_ORD[a], LANE_ORD[b]
        for c1 in range(len(cands[n1])):
            S1 = SEG[(n1, c1)]; b1 = (S1[:, :, 0].min(), S1[:, :, 0].max(), S1[:, :, 1].min(), S1[:, :, 1].max())
            for c2 in range(len(cands[n2])):
                S2 = SEG[(n2, c2)]; b2 = (S2[:, :, 0].min(), S2[:, :, 0].max(), S2[:, :, 1].min(), S2[:, :, 1].max())
                if b1[0] - b2[1] > P or b2[0] - b1[1] > P or b1[2] - b2[3] > P or b2[2] - b1[3] > P:
                    continue
                if v3._seg_seg_batch(S1, S2).min() < P - 1e-9:
                    rows.append(IDX[(n1, c1)]); cols.append(IDX[(n2, c2)])
print("conflict pairs", len(rows))
cons = []
A1 = np.zeros((len(LANE_ORD), N))
for k, n in enumerate(LANE_ORD):
    for c in range(len(cands[n])): A1[k, IDX[(n, c)]] = 1
cons.append(LinearConstraint(A1, -np.inf, np.ones(len(LANE_ORD))))
if rows:
    Ar = np.zeros((len(rows), N)); Ar[np.arange(len(rows)), rows] = 1.0; Ar[np.arange(len(rows)), cols] = 1.0
    cons.append(LinearConstraint(Ar, -np.inf, np.ones(len(rows))))
res = milp(c=-np.ones(N), constraints=cons, integrality=np.ones(N), bounds=Bounds(0, 1))
sel = {}
if res.status == 0:
    for k, x in enumerate(res.x):
        if x > 0.5: sel[var[k][0]] = var[k][1]
print("MILP status=%s placed=%d/16 missing=%s" % (res.status, len(sel), sorted(n[10:-3] for n in LANES - set(sel))))
routes = {n: {"pts": cands[n][c]["pts"]} for n, c in sel.items()}
anchors = [a for a in v3.lane_anchors(model) if a["net"] in routes]
g = v3.exact_gate(model, routes, anchors, "In5.Cu", HW, frozenset(), frozenset(), P, frozenset())
print("exact_gate: 互距违例=%d(min %.4f) 净距违例=%d(min %.4f) 端点=%.4f" % (
    g["n_lane_pitch_viol"], g["lane_pitch_min_gap_mm"], g["n_clearance_viol"],
    g["clearance_min_mm"] if g["clearance_min_mm"] is not None else -1, g["endpoint_max_dev_mm"]))
LEN = {n: round(sum(math.dist(r["pts"][k], r["pts"][k+1]) for k in range(len(r["pts"])-1)), 3) for n, r in routes.items()}
out = {"schema": 1, "artifact": "k2_r328_joint_hard_assignment_one_shot", "to": "监理", "from": "ENG · ARCHER",
       "method": "硬约束联合指派：候选=过 (B.x,y) 之最短路（两株最短路树拼接 · 端点不动）；MILP 互斥=pitch 硬约束",
       "cell_mm": CELL, "level_step_mm": LSTEP, "pitch_mm": P, "hw_mm": HW, "board_sha16": "7a5c89913d6e5d0a",
       "n_candidates": {n[10:-3]: len(cands[n]) for n in LANE_ORD},
       "milp_status": int(res.status), "placed": len(routes), "missing": sorted(n[10:-3] for n in LANES - set(routes)),
       "assign_y": {n[10:-3]: cands[n][c]["y"] for n, c in sel.items()},
       "exact_gate": {k: g[k] for k in ("lane_pitch_req_mm","lane_pitch_min_gap_mm","lane_pitch_min_pair","n_lane_pitch_viol","clearance_min_mm","n_clearance_viol","endpoint_max_dev_mm")},
       "lengths_mm": {n[10:-3]: LEN[n] for n in sorted(LEN)},
       "routes_pts": {n[10:-3]: routes[n]["pts"] for n in sorted(routes)},
       "self_sha16": {"convention": "#K2-72 §五 约定A", "convention_A_sha16": ""}}
if LEN:
    ls = sorted(LEN.values()); out["length_spread_mm"] = round(ls[-1]-ls[0], 3)
txt = json.dumps(out, indent=1, ensure_ascii=False)
out["self_sha16"]["convention_A_sha16"] = hashlib.sha256(txt.strip().encode()).hexdigest()[:16]
json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("[sha16 约定A]", out["self_sha16"]["convention_A_sha16"], "->", OUT)
