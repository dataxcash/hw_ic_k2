#!/usr/bin/env python3
"""K2 · R517 v2 —— 遵「收敛停滞停止令」出**二值**：**构造式可行见证**（非 `Solve()`，0 额度）。

为什么不是又一次求解：停止令要求「可行见证 ‖ 守恒级不可行证书」；后者已被 R513-T4/T5/T6-T8 + R515
守恒报告三条独立机核排除（本问题类别不存在资源计数型证书）。⇒ 唯一能出二值的路 = **给出可行见证**。
本器 = 在**完全相同的在册模型图**上（`K2_R515_FREETERMINALS_v1.Gen2(l1scope="full")`，即「甲」= 保真口径：
In4 全板可用、过孔仅在四个在册宽区、≤2 对过孔/根、逐层精确净距声明集、1.6× 绕行预算）做
**确定性构造**：逐根优先级布线 + 冲突割除重布（rip-up-and-reroute，规则见 §heuristic），
不经 CP-SAT、不读 `/tmp` 之外的任何新输入；所得路径**逐条由在册闸独立复验**
（`exact_gate` 逐层 + `gate_vias` 跨层/过孔 + 端点偏差 + 每根过孔数 ≤ 2·MAX_VIA_PAIRS）。

资源语义（与在册模型逐条一致）：
  · 同层两弧冲突 ⇔ 两弧**声明集相交**（`Gen2.claim_seg`：格点到线段真距 < P）—— 与 R512 修好的
    「head-arc 声明集」精确编码同源；
  · 过孔站点：仅四宽区（`_viaok`）；他线过孔中心 ≥ 0.7mm；他线走线中心 ≥ 0.43mm（= VIA_LANE）；
  · 每根 ≤2 对过孔（= ≤4 个跃层弧）。

纪律：本器 `Solve()` **0** 次 · 不改模型参数 · 不换范式 · 只读板件 · 不动冻结四源。
"""
from __future__ import annotations
import collections, heapq, importlib, json, math, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
W = importlib.import_module("K2_R" + "515_FREETERMINALS_v1")
P, NID, NY, NX, X0, Y0, TERM_BASE = W.P, W.NID, W.NY, W.NX, W.X0, W.Y0, W.TERM_BASE
VR, VIA_SEP, VIA_LANE, MAX_VIA_PAIRS = W.VR, W.VIA_SEP, W.VIA_LANE, W.MAX_VIA_PAIRS
BIG = 1.0e6

model = json.load(open("/tmp/opencode/archer/model_l8.json"))
t00 = time.time()
rep = {"artifact": "k2_r517_witness_search_twolayer_v2", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "authority": ("monitor convergence-stall stop-order (must produce a binary: feasible witness OR a "
                     "conservation-grade infeasibility certificate; a clarification round / tool bump is banned)"),
       "method": ("deterministic constructive routing on the REGISTERED 2-layer graph (Gen2 full = faithful lever 甲): "
                  "priority order + rip-up-and-reroute; conflicts use the registered declaration-set semantics; "
                  "every produced path is re-verified by the registered exact_gate (per layer) + gate_vias + endpoint "
                  "deviation + per-lane via count"),
       "solve_calls": 0, "params": {"P": P, "HW": W.HW, "VIA_SEP": VIA_SEP, "VIA_LANE": VIA_LANE,
                                    "MAX_VIA_PAIRS": MAX_VIA_PAIRS, "BOUND": W.BOUND, "l1scope": "full"}}

g2 = W.Gen2(model, l1scope="full", verbose=True)
names = list(g2.names)
lanes, no_leg = {}, []
for nm in names:
    L = g2.build_lane(nm)
    if L is None:
        no_leg.append(nm)
    else:
        lanes[nm] = L
rep["lanes_built"] = len(lanes); rep["lanes_without_legs"] = no_leg

# ---------------- arc geometry caches (declaration sets) ----------------
_acache = {}
def arc_info(u, v, nm):
    """-> (kind, layer, claim_frozenset) ; kind in {'lat','via','legA','legB'}（腿的声明集取本根自己的锚）"""
    key = (u, v, nm)
    got = _acache.get(key)
    if got is not None:
        return got
    L = 0 if u >= TERM_BASE else u // NID
    if u >= TERM_BASE:                      # leg: terminal -> lattice node on In5
        tx, ty = lanes[nm]["anc"][0]
        px, py = W.XY(*W.rc(v % NID))
        cl = W.claim_seg(tx, ty, px, py); cl = cl | {v % NID} if False else cl
        got = ("legA", 0, frozenset(cl))
    elif v >= TERM_BASE:                    # leg: lattice node -> terminal (In5)
        px, py = W.XY(*W.rc(u % NID))
        tx, ty = lanes[nm]["anc"][1]
        cl = W.claim_seg(px, py, tx, ty)
        got = ("legB", 0, frozenset(cl))
    elif u // NID != v // NID:               # via
        got = ("via", L, frozenset([u % NID]))
    else:                                    # lattice arc on layer L
        ax, ay = W.XY(*W.rc(u % NID)); bx, by = W.XY(*W.rc(v % NID))
        got = ("lat", L, frozenset(W.claim_seg(ax, ay, bx, by)))
    _acache[key] = got
    return got


# ---------------- shared resource state (soft/negotiated congestion, PathFinder-style) ----------------
def via_nb(p):
    pi, pj = W.rc(p)
    out = []
    for di in (-2, -1, 0, 1, 2):
        for dj in (-2, -1, 0, 1, 2):
            if di * di + dj * dj <= 4 and 0 <= pi + di < NX and 0 <= pj + dj < NY:
                out.append((pi + di) * NY + (pj + dj))
    return out

PEN, HPEN, VPEN, VMAX = 6.0, 4.0, 8.0, 1.0e3

def route_soft(nm, use, hist, vuse):
    L = lanes[nm]; adj = L["adj"]; src, snk = L["src"], L["snk"]
    dist = {src: 0.0}; vias = {src: 0}; prev = {}
    pq = [(0.0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, 1e18) + 1e-12:
            continue
        if u == snk:
            break
        for (v, w) in adj.get(u, ()):
            kind, Lay, claim = arc_info(u, v, nm)
            c = w
            s = 0.0
            for p in claim:
                s += use.get((Lay, p), 0.0) * PEN + hist.get((Lay, p), 0.0) * HPEN
            c += s
            if kind == "via":
                p = u % NID
                c += VPEN * sum(vuse.get(q, 0.0) for q in via_nb(p))
                if vias[u] >= 2 * MAX_VIA_PAIRS:
                    c += VMAX
            nd = d + c
            nv = vias[u] + (1 if kind == "via" else 0)
            if nd < dist.get(v, 1e18) - 1e-12:
                dist[v] = nd; vias[v] = nv; prev[v] = u; heapq.heappush(pq, (nd, v))
    if snk not in prev:
        return None
    path = []; cur = snk
    while cur is not None:
        path.append(cur); cur = prev.get(cur)
    if path[0] != src:
        return None
    path.reverse()
    return path

def count_conflicts(routes):
    occ = {0: collections.defaultdict(set), 1: collections.defaultdict(set)}
    vpts = collections.defaultdict(list)
    for nm, path in routes.items():
        for a, b in zip(path, path[1:]):
            kind, Lay, claim = arc_info(a, b, nm)
            for p in claim:
                occ[Lay][p].add(nm)
            if kind == "via":
                vpts[nm].append(a % NID)
    conf, detail = 0, collections.Counter()
    for nm, path in routes.items():
        for a, b in zip(path, path[1:]):
            kind, Lay, claim = arc_info(a, b, nm)
            for p in claim:
                others = occ[Lay][p] - {nm}
                if others:
                    conf += len(others); detail[tuple(sorted((nm, next(iter(others)))))] += 1
    for nm, ps in vpts.items():
        for p in ps:
            for q, other in [(q, om) for om, qs in vpts.items() if om != nm for q in qs]:
                if other == nm:
                    continue
                dx = (W.XY(*W.rc(p))[0] - W.XY(*W.rc(q))[0])
                dy = (W.XY(*W.rc(p))[1] - W.XY(*W.rc(q))[1])
                if math.hypot(dx, dy) < VIA_SEP - 1e-9:
                    conf += 1; detail[tuple(sorted((nm, other)))] += 1
    return conf, detail

def difficulty(nm):
    L = lanes[nm]
    nA = sum(1 for (u, v) in L["legs"] if arc_info(u, v, nm)[0] == "legA")
    return (nA, L["nkeep"])

order0 = sorted(lanes, key=lambda nm: (difficulty(nm), nm))
ORDERS = [order0, list(reversed(order0)), order0[::2] + order0[1::2], order0[1::2] + order0[::2],
          sorted(lanes, key=lambda nm: (lanes[nm]["sp"], nm)),
          sorted(lanes, key=lambda nm: (-lanes[nm]["nkeep"], nm))]
rep["order_first_pass"] = [nm.replace("PCIE_UP_OUT", "U") for nm in order0]

t0 = time.time()
hist = {}
best, best_conf, best_it, log = None, 10 ** 9, -1, []
for it in range(18):
    order = ORDERS[it % len(ORDERS)]
    use, vuse, routes = {}, {}, {}
    for nm in order:
        p = route_soft(nm, use, hist, vuse)
        if p is None:
            continue
        routes[nm] = p
        for a, b in zip(p, p[1:]):
            kind, Lay, claim = arc_info(a, b, nm)
            for q in claim:
                use[(Lay, q)] = use.get((Lay, q), 0.0) + 1.0
            if kind == "via":
                for q in via_nb(a % NID):
                    vuse[q] = vuse.get(q, 0.0) + 1.0
    conf, detail = count_conflicts(routes)
    log.append({"it": it, "routed": len(routes), "total_conflicts": conf,
                "top_pairs": [[list(k), v] for k, v in detail.most_common(3)]})
    with open(os.path.join(HERE, "K2_R517_PROGRESS.md"), "a") as fh:
        fh.write("[%s] it=%d routed=%d conflicts=%d\n" % (time.strftime("%H:%M:%S"), it, len(routes), conf)); fh.flush()
    if conf < best_conf:
        best_conf, best, best_it = conf, dict(routes), it
    if conf == 0 and len(routes) == len(lanes):
        break
    for nm, p in routes.items():
        for a, b in zip(p, p[1:]):
            kind, Lay, claim = arc_info(a, b, nm)
            for q in claim:
                hist[(Lay, q)] = hist.get((Lay, q), 0.0) + 1.0
paths = best or {}
rep["search_log"] = log
rep["placed"] = len(paths)
rep["best_iteration"] = best_it
rep["min_total_conflicts"] = best_conf
rep["search_elapsed_s"] = round(time.time() - t0, 1)
# ---------------- independent registered-gate verification ----------------
TERMINALS = {}
for nm in names:
    TA_, TB_ = lanes[nm]["terminals"] if nm in lanes else (None, None)
    if TA_ is None: continue
    TERMINALS[TA_] = list(g2.A[nm]); TERMINALS[TB_] = list(g2.B[nm])

def nxy(node):
    return list(TERMINALS[node]) if node >= TERM_BASE else list(W.XY(*W.rc(node % NID)))

def nlayer(node):
    return 0 if node >= TERM_BASE else node // NID

lane_polys, all_vias, per_lane_len = {}, [], {}
for nm, path in paths.items():
    runs, vias = [], []
    run = [path[0]]
    for n in path[1:]:
        if nlayer(n) == nlayer(run[-1]):
            run.append(n)
        else:
            vias.append(list(W.XY(*W.rc(run[-1] % NID)))); runs.append(run); run = [n]
    runs.append(run)
    polys = {}
    for rr in runs:
        polys.setdefault(nlayer(rr[0]), []).append([nxy(pp) for pp in rr])
    lane_polys[nm] = polys
    for q in vias:
        all_vias.append((q[0], q[1], nm))
    per_lane_len[nm] = round(sum(math.dist(p[k], p[k + 1]) for Lr in polys for p in polys[Lr]
                                 for k in range(len(p) - 1)), 3)

gate_per_layer = {}
if len(paths) == len(lanes):
    for Lr in (0, 1):
        rt = {}
        for nm, polys in lane_polys.items():
            for k, p in enumerate(polys.get(Lr, [])):
                if len(p) >= 2:
                    rt["%s#%d" % (nm, k)] = {"pts": p, "layer_cu": W.LAYER_OF[Lr], "n_vias": len(all_vias)}
        if not rt:
            continue
        gg = W.exact_gate(model, rt, [], W.LAYER_OF[Lr], W.HW, set(), set(), P, frozenset())
        vp2 = [t for t in gg["lane_pitch_violations"] if t[0].split("#")[0] != t[1].split("#")[0]]
        gate_per_layer[W.LAYER_OF[Lr]] = {"n_lane_pitch_viol": len(vp2),
                                          "lane_pitch_min_gap_mm": gg["lane_pitch_min_gap_mm"],
                                          "n_clearance_viol": gg["n_clearance_viol"],
                                          "clearance_min_mm": gg["clearance_min_mm"]}
    gv = W.gate_vias(model, all_vias, lane_polys, g2.an)
    edev = {nm: round(max(math.dist(lane_polys[nm][0][0][0], list(g2.A[nm])),
                          math.dist(lane_polys[nm][0][-1][-1], list(g2.B[nm]))), 6) for nm in lane_polys}
    vpl = {nm: sum(1 for v in all_vias if v[2] == nm) for nm in lane_polys}
    ok = (bool(gate_per_layer) and all(v["n_lane_pitch_viol"] == 0 and v["n_clearance_viol"] == 0
                                       for v in gate_per_layer.values())
          and gv["n_via_viol"] == 0 and max(edev.values()) <= 1e-6
          and all(v <= 2 * MAX_VIA_PAIRS for v in vpl.values()))
    rep.update({"gate_per_layer": gate_per_layer, "gate_vias": gv,
                "endpoint_max_dev_mm": max(edev.values()), "vias_per_lane": vpl,
                "per_lane_len_mm": per_lane_len, "requirement_level_gate": "PASS" if ok else "FAIL"})
    if ok:
        json.dump({"lanes": lane_polys, "vias": all_vias},
                  open(os.path.join(HERE, "K2_R517_WITNESS_ROUTES_v1.json"), "w"), ensure_ascii=False, indent=1)
        rep["decision"] = ("TERMINAL: FEASIBLE WITNESS (构造解) = 16/16 双层联合路由 + 逐层在册 exact_gate + "
                           "跨层/过孔判据 + 端点偏差 全绿 ⇒ 可行见证（非求解得出；0 次 Solve）")
    else:
        rep["decision"] = "NON-TERMINAL: 构造解已得 16/16，但独立核 FAIL（详见 gate）"
else:
    rep["decision"] = ("NON-TERMINAL: 构造式布线 %d/%d 根落位，未能给出可行见证"
                       % (len(paths), len(lanes)))
rep["boundaries"] = ("Solve() 0 calls; no model parameter changed; no paradigm switch (same registered graph, "
                     "constructive instead of CP-SAT); board/SPEC/tools/criteria untouched; frozen four 4/4")
rep["buildability"] = ("PENDING the registered gates in this same artifact (a witness is only a milestone if "
                       "exact_gate + gate_vias + endpoint + via-count all pass; otherwise NOT-APPLICABLE)")
rep["elapsed_s"] = round(time.time() - t00, 1)
out = os.path.join(HERE, "K2_R517_WITNESS_SEARCH_TWOLAYER_v2.json")
json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps({k: rep[k] for k in ("lanes_built", "placed", "search_log", "requirement_level_gate",
                                      "gate_per_layer", "gate_vias", "endpoint_max_dev_mm", "vias_per_lane",
                                      "decision", "elapsed_s") if k in rep}, ensure_ascii=False)[:3000])
print("WROTE", out)
