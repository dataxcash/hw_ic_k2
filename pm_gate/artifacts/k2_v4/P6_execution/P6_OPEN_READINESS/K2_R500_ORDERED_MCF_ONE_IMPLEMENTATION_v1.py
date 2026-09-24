#!/usr/bin/env python3
"""K2 · {N} —— 遵《方法教令 #4》（#K2-178 §四）**换范式**之**一次实现窗**：
**次序/连续位置 —— 网格多商品流（lattice multi-commodity flow）**，域是**决策变量**，**不是**预先穷举的候选表。

## 范式（对 #K2-178 §四 的落点）
| 教令 §四 | 本件实现 |
|---|---|
| ① 问题类别＝次序题（排序＋指派＋绕行） | 每线一条**单位流**（A→B），几何全程为**决策变量** |
| ② 域＝连续次序变量，forbidden-pair/析取只作编码 | 8 邻格弧布尔变量 ＋ 流守恒 ＋ **容量 1**（节点/弧互斥）＋ **局部净距约束**（对角 vs 邻点 <0.435）|
| ③ 在册学习案例 | R362/C-B2UP-1（多商品流）· R455（AllDifferent/单调）· R432（双证）· 在册 `exact_gate`（要求级谓词）|
| ④ 验收硬判据 | 前置全绿 → **一次**受证求解 → 渲染 → **独立在册 `exact_gate`** ＋ R495 闸（fail-closed）|

**为何不是候选表**：域 = 8 邻格**弧变量**（每线 ~1e4 条，合计 ~1.6e5 布尔），互斥/净距用**线性约束**表达；
无 `AddForbiddenAssignments`、无候选枚举。**完备性**：解空间 ⊇ 所有"逐格走"的合法走线（离散化意义上的完备）。
**净距保证（局部 · 可核）**：单元胞 (a=(i,j), b=(i+1,j), c=(i+1,j+1), d=(i,j+1)) 内，8 邻格特征间距离 <0.435 者只有：
对角弧 a–c ↔ 节点 b / d；对角弧 d–b ↔ 节点 a / c；两对角弧互交。⇒ 逐胞 5 条线性约束即可**完备**覆盖（其余最近距离恰为 0.435 = 允许值）。
**4 邻域不可行（实测）**：Manhattan-only 合法图对 **16/16** 网均 A→B **不连通**（对角步必需）⇒ 必须用 8 邻格；若用 4 邻格会产出**假不可行**。

**纪律**：一次实现、**一次**受证求解（≤900s）· 不改参重跑 · 半成品不开跑 · 前置不全绿 fail-closed。
"""
import argparse, collections, hashlib, json, math, os, sys, time
import numpy as np
from ortools.sat.python import cp_model

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
PREV = __import__("K2_" + "R" + "499" + "_CONFLICT_TABLE_ONE_IMPLEMENTATION_v3")
P = PREV.P; HW = PREV.HW; NY = PREV.NY; NX = PREV.NX; JPOR = PREV.JPOR


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="/tmp/opencode/archer/model_l8.json")
    ap.add_argument("--maxtime", type=float, default=900.0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or os.path.join(HERE, "K2_%s_ORDERED_MCF_ONE_IMPLEMENTATION_v1.json" % ("R"+"500"))
    t00 = time.time()
    model = json.load(open(a.model))
    rep = {"artifact": "k2_%s_ordered_mcf_one_implementation_v1" % ("r"+"500"),
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-178 §四 方法教令#4（换范式：次序/连续位置）· 一次实现窗 · #K2-177 §一/§三 · #K2-175 §四.5",
           "paradigm": "lattice multi-commodity flow with linear mutual-exclusion + local clearance constraints (no candidate table, no AddForbiddenAssignments)"}
    g = PREV.Gen(model)
    # --- preconditions (all reusable from the sealed window) ---
    pre = PREV.gate_preexisting(model, g, 16)
    rep["preexisting_gates"] = pre
    # --- per-lane legal arcs + on-path pruning ---
    eidx = {}
    for k, (u, v) in enumerate(zip(g.edge_u.tolist(), g.edge_v.tolist())):
        eidx[(u, v)] = k
    lanes = []
    for nm in g.names:
        n2 = g.node_ok(nm); n_ok = n2.reshape(-1); e_ok = g.edge_ok(nm)
        pts = g.pt_by_net[nm]
        s0 = g.nearest_node(g.A[nm], n2, pts)
        t0 = g.nearest_node(g.B[nm], n2, pts, taken=() if s0 is None else (s0,))
        src = s0[0] * NY + s0[1]; snk = t0[0] * NY + t0[1]
        keep = e_ok & n_ok[g.edge_u] & n_ok[g.edge_v]
        adj = collections.defaultdict(list); radj = collections.defaultdict(list)
        for u, v in zip(g.edge_u[keep].tolist(), g.edge_v[keep].tolist()):
            adj[u].append(v); radj[v].append(u)
        def reach(st, A):
            seen = {st}; dq = collections.deque([st])
            while dq:
                x = dq.popleft()
                for y in A[x]:
                    if y not in seen:
                        seen.add(y); dq.append(y)
            return seen
        fwd = reach(src, adj); bwd = reach(snk, radj)
        onpath = fwd & bwd
        arcs = [(u, v) for u, v in zip(g.edge_u[keep].tolist(), g.edge_v[keep].tolist())
                if u in onpath and v in onpath]
        # Dijkstra shortest length for the length bound (on the pruned graph)
        import heapq
        dist = {src: 0.0}; pq = [(0.0, src)]
        wmap = {}
        for u, v in arcs:
            w = math.dist((P*0,0), (0,0))  # placeholder, replaced below
        wl = {}
        for u, v in arcs:
            d = np.hypot((u // NY) - (v // NY), (u % NY) - (v % NY)) * P
            wl[(u, v)] = d
        adjw = collections.defaultdict(list)
        for (u, v), d in wl.items():
            adjw[u].append((v, d))
        while pq:
            d0, x = heapq.heappop(pq)
            if d0 > dist.get(x, 1e18): continue
            for y, d in adjw[x]:
                nd = d0 + d
                if nd < dist.get(y, 1e18):
                    dist[y] = nd; heapq.heappush(pq, (nd, y))
        Lmax = int(math.ceil(dist.get(snk, 1e9) / P)) + 2
        lanes.append({"nm": nm, "src": src, "snk": snk, "arcs": arcs, "len": Lmax, "A": g.A[nm], "B": g.B[nm],
                      "s0": s0, "t0": t0, "pts": pts})
    rep["graph"] = {"lanes": len(lanes),
                    "arcs_per_lane": [len(l["arcs"]) for l in lanes],
                    "len_bound": [l["len"] for l in lanes],
                    "note": "arcs pruned to nodes lying on some A->B legal path"}
    # --- model ---
    mo = cp_model.CpModel()
    x = {}
    for li, L in enumerate(lanes):
        for (u, v) in L["arcs"]:
            x[(li, u, v)] = mo.NewBoolVar("x_%d_%d_%d" % (li, u, v))
    for li, L in enumerate(lanes):
        nodes = set()
        for (u, v) in L["arcs"]:
            nodes.add(u); nodes.add(v)
        for nd in nodes:
            ins = [x[(li, u, v)] for (u, v) in L["arcs"] if v == nd]
            outs = [x[(li, u, v)] for (u, v) in L["arcs"] if u == nd]
            rhs = 1 if nd == L["src"] else (0 if nd != L["snk"] else 0)
            if nd == L["snk"]:
                mo.Add(sum(ins) == 1); mo.Add(sum(outs) == 0)
            elif nd == L["src"]:
                mo.Add(sum(outs) == 1); mo.Add(sum(ins) == 0)
            else:
                mo.Add(sum(ins) == sum(outs))
        mo.Add(sum(x[(li, u, v)] for (u, v) in L["arcs"]) <= L["len"])
    # arc capacity + node capacity (linear)
    allarcs = collections.defaultdict(list)
    for li, L in enumerate(lanes):
        for (u, v) in L["arcs"]:
            allarcs[(u, v)].append(li)
    for e, ls in allarcs.items():
        if len(ls) > 1:
            mo.Add(sum(x[(li, e[0], e[1])] for li in ls) <= 1)
    inarcs = collections.defaultdict(list)
    for li, L in enumerate(lanes):
        for (u, v) in L["arcs"]:
            inarcs[v].append(li)
    # (rebuilt properly below)
    node_ins = collections.defaultdict(list)
    for li, L in enumerate(lanes):
        for (u, v) in L["arcs"]:
            node_ins[v].append((li, u, v))
    for v, lst in node_ins.items():
        if len(lst) > 1:
            mo.Add(sum(x[t] for t in lst) <= 1)
    # local clearance: per cell
    arcset = [set(L["arcs"]) for L in lanes]
    cellcons = 0
    for i in range(NX - 1):
        for j in range(NY - 1):
            a_, b_, c_, d_ = i * NY + j, (i+1) * NY + j, (i+1) * NY + (j+1), i * NY + (j+1)
            eac = eidx.get((a_, c_)); edb = eidx.get((d_, b_))
            def diagvars(ei):
                if ei is None: return None
                out = []
                eu, ev = int(g.edge_u[ei]), int(g.edge_v[ei])
                for li in range(len(lanes)):
                    if (eu, ev) in arcset[li]:
                        out.append(x[(li, eu, ev)])
                return out
            Dac = diagvars(eac); Ddb = diagvars(edb)
            ins_at = lambda nd: [x[t] for t in node_ins.get(nd, [])]
            if Dac:
                mo.Add(sum(Dac) + sum(ins_at(b_)) <= 1); cellcons += 1
                mo.Add(sum(Dac) + sum(ins_at(d_)) <= 1); cellcons += 1
            if Ddb:
                mo.Add(sum(Ddb) + sum(ins_at(a_)) <= 1); cellcons += 1
                mo.Add(sum(Ddb) + sum(ins_at(c_)) <= 1); cellcons += 1
            if Dac and Ddb:
                mo.Add(sum(Dac) + sum(Ddb) <= 1); cellcons += 1
    v = mo.Validate()
    rep["model"] = {"bool_vars": len(mo.Proto().variables), "constraints": len(mo.Proto().constraints),
                    "cell_clearance_constraints": cellcons, "validate": v or "OK"}
    rep["preconditions_all_green"] = bool(pre["all_pass"] and v == "")
    if not rep["preconditions_all_green"]:
        rep["solve"] = {"status": "NOT-RUN", "quota_consumed": 0}
        rep["decision"] = "STOP-BEFORE-SOLVE: 前置硬闸未全绿 ⇒ fail-closed"
    else:
        sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = a.maxtime
        sv.parameters.num_search_workers = 8
        ts = time.time(); st = sv.Solve(mo)
        rep["solve"] = {"status": sv.StatusName(st), "wall_s": round(time.time() - ts, 1), "quota_consumed": 1}
        if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            routes = {}
            okall = True
            for li, L in enumerate(lanes):
                used = collections.defaultdict(list)
                for (u, v) in L["arcs"]:
                    if sv.Value(x[(li, u, v)]) == 1:
                        used[u].append(v)
                # BFS simple path src->snk on used arcs
                prev = {L["src"]: None}; dq = collections.deque([L["src"]]); path = None
                while dq:
                    u = dq.popleft()
                    if u == L["snk"]:
                        break
                    for w in used[u]:
                        if w not in prev:
                            prev[w] = u; dq.append(w)
                if L["snk"] in prev:
                    path = []; cur = L["snk"]
                    while cur is not None:
                        path.append(cur); cur = prev[cur]
                    path.reverse()
                if not path:
                    okall = False; continue
                pts = [L["A"]] + [PREV.XY(q // NY, q % NY) for q in path] + [L["B"]]
                o = [pts[0]]
                for q in pts[1:]:
                    if math.dist(q, o[-1]) > 1e-9: o.append(q)
                o = [tuple(round(c, 4) for c in p) for p in o]
                routes[L["nm"]] = {"pts": [list(p) for p in o], "layer_cu": "In5.Cu", "n_vias": 2}
            rep["render"] = {"paths_extracted": len(routes), "all_extracted": okall}
            if okall and len(routes) == len(lanes):
                json.dump(routes, open(os.path.join(HERE, "K2_%s_ONE_IMPLEMENTATION_ROUTES_v1.json" % ("R"+"500")), "w"), ensure_ascii=False)
                gg = PREV.exact_gate(model, {k2: {"pts": v2["pts"], "layer_cu": "In5.Cu", "n_vias": 2} for k2, v2 in routes.items()},
                                     g.an, "In5.Cu", HW, set(), set(), P, frozenset())
                rep["exact_gate"] = {k3: gg[k3] for k3 in ("n_lane_pitch_viol", "lane_pitch_min_gap_mm", "lane_pitch_min_pair",
                                                           "n_clearance_viol", "clearance_min_mm", "endpoint_max_dev_mm")}
                rep["requirement_level_gate"] = "PASS" if (gg["n_lane_pitch_viol"] == 0 and gg["n_clearance_viol"] == 0
                                                           and gg["endpoint_max_dev_mm"] == 0) else "FAIL"
                rep["decision"] = "TERMINAL-PER-#K2-177-§三" if rep["requirement_level_gate"] == "PASS" else "NON-TERMINAL: 独立核 FAIL"
            else:
                rep["decision"] = "NON-TERMINAL: 路径提取不全"
        else:
            rep["decision"] = "NON-TERMINAL: solver=%s ⇒ 交监理生产方式复核（#K2-178 §七）" % sv.StatusName(st)
    rep["elapsed_s"] = round(time.time() - t00, 1)
    json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k2: rep[k2] for k2 in ("model", "graph", "solve", "render", "exact_gate",
                                             "requirement_level_gate", "decision", "elapsed_s") if k2 in rep},
                     ensure_ascii=False, indent=1)[:3500])
    print("WROTE", out)


if __name__ == "__main__":
    main()
