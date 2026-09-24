#!/usr/bin/env python3
"""K2 · R508 —— 遵 #K2-181 §三.6（**只许**三处改动 (a)(b)(c)）· 承 R504 联合 MCF 骨架：
(a) 通道放宽到最小必要（取消贴墙列独占）(b) 净距改精确 per-lane 编码 (c) 加次序/非交叉显式变量

原 R504 说明： —— 遵《方法教令 #5》（#K2-179 §四）**联合方法一次实现窗（唯一）**：
**两通道分解 ＋ 两级（各向异性）格网 ＋ 联合多商品流（MCF · CP-SAT · 恰一次受证求解）**。

| 教令 #5 | 本件 |
|---|---|
| ① 问题类别＝联合（同时）定位 | 16 条车道的**整条路径**当 16 条流**同时**求解（不是逐条贪心） |
| ② 主范式＝联合 MCF | 流守恒（每网单位流 A→B）＋ **节点声明容量 1**（线性互斥）＋ 长度上界（灭环） |
| ② 必做＝两级格网粗化 | **各向异性**：x 方向在"开阔区"用 2 格步（0.87），y 方向**保持 0.435**（16 条车道在门/院子需 1 格间距） |
| ② 或＝二通道分解 | 西 8（B 在墙西）＝**墙缝＋西迷宫**通道；东 8＝**东门**通道（互不越界，除共用 A 梳齿/院子） |
| ③ 净距编码 | 弧的**声明集 K(e)** = 与线段真最近距 **< P** 的全部格点；**节点声明容量 1**（线性，非候选表） |
| ④ 验收 | 前置硬闸全绿 → **恰一次** CP-SAT 受证求解 → 渲染 → **在册 `exact_gate`** ＋ R495 闸（缺一 fail-closed） |

**净距模型的可靠性**（承 R503 §一 的局部等价证明）：`K(e)` 取"距线段 < P 的格点"是**保守且可靠**（sound）的：
任何被本模型判为合法的解，其任两线最近距 ≥ P（因若某格点同时进入两线之 K，则该点各距两线 < P ⇒ 冲突已排除）；
本件**另做**一次局部枚举自检（`--selfcheck`）验证「真最近距 < P ⇒ K 相交」不漏项（含 step-2 弧）。
**声明**：本模型相对真几何是**保守**的（可能排除某些合法解，不会放行非法解）；最终以**在册 `exact_gate`** 为准。

**纪律**：前置不全绿 fail-closed；**恰一次** `Solve()`（消耗受证额度 1）；至多一次实现缺陷修复（R494 先例）；不改参扫参。
"""
import argparse, collections, heapq, json, math, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
PREV = __import__("K2_" + "R" + "499" + "_CONFLICT_TABLE_ONE_IMPLEMENTATION_v3")
P, HW, NY, NX, X0, Y0 = PREV.P, PREV.HW, PREV.NY, PREV.NX, PREV.X0, PREV.Y0
XY = PREV.XY
NID = NX * NY
WALLC = 114.0                      # wall columns 114-115
MOVE1 = [(di, dj) for di in (-1, 0, 1) for dj in (-1, 0, 1) if not (di == 0 and dj == 0)]
MOVE2 = [(di, dj) for di in (-2, 2) for dj in (-1, 0, 1)]
BOUND = 1.6                        # declared: keep nodes with ds+dt <= BOUND * ds(snk) (cyclable-path budget)


def nid(i, j):
    return i * NY + j


def rc(n):
    return n // NY, n % NY


_CLAIM = {}


def claim_of(u, v):
    """all lattice nodes whose true (point-segment) distance to segment u-v is < P -- the arc's
    clearance declaration set (exact, no lattice-step shortcut)."""
    key = (u, v) if u < v else (v, u)
    got = _CLAIM.get(key)
    if got is not None:
        return got
    iu, ju = rc(key[0]); iv, jv = rc(key[1])
    ax, ay = X0 + iu * P, Y0 + ju * P
    bx, by = X0 + iv * P, Y0 + jv * P
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    lim = P - 1e-9
    out = set()
    for i in range(min(iu, iv) - 2, max(iu, iv) + 3):
        if not (0 <= i < NX):
            continue
        for j in range(min(ju, jv) - 2, max(ju, jv) + 3):
            if not (0 <= j < NY):
                continue
            px, py = X0 + i * P, Y0 + j * P
            if L2 <= 0:
                d2 = (px - ax) ** 2 + (py - ay) ** 2
            else:
                t = ((px - ax) * dx + (py - ay) * dy) / L2
                t = 0.0 if t < 0 else (1.0 if t > 1 else t)
                d2 = (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2
            if d2 < lim * lim:
                out.add(nid(i, j))
    _CLAIM[key] = out
    return out


def selfcheck(steps=(1, 2), K=5, verbose=False):
    """local enumeration: every truly conflicting arc pair must share a declaration node (soundness, no miss)."""
    arcs = []
    for i in range(K):
        for j in range(K):
            for (di, dj) in MOVE1 + MOVE2:
                a, b = (i, j), (i + di, j + dj)
                if 0 <= b[0] < K and 0 <= b[1] < K and a < b:
                    arcs.append((nid(*a), nid(*b)))
    cl = {e: claim_of(*e) for e in arcs}
    miss = 0; n = 0; ex = []
    for x in range(len(arcs)):
        for y in range(x + 1, len(arcs)):
            iu, ju = rc(arcs[x][0]); iv, jv = rc(arcs[x][1])
            kw, lw = rc(arcs[y][0]); ks, ls = rc(arcs[y][1])
            sa = np.array([[X0 + iu * P, Y0 + ju * P], [X0 + iv * P, Y0 + jv * P]])
            sb = np.array([[X0 + kw * P, Y0 + lw * P], [X0 + ks * P, Y0 + ls * P]])
            d = float(PREV._seg_seg_batch(np.array([sa]), np.array([sb])).min())
            n += 1
            if d < P - 1e-9 and not (cl[arcs[x]] & cl[arcs[y]]):
                miss += 1
                if verbose and len(ex) < 8:
                    ex.append([arcs[x], arcs[y], round(d, 4)])
    return {"pairs": n, "missed": miss, "pass": miss == 0, "examples": ex,
            "criterion": "no missed conflict: true closest distance < P  =>  declaration sets intersect"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="/tmp/opencode/archer/model_l8.json")
    ap.add_argument("--maxtime", type=float, default=1500.0)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--triage", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or os.path.join(HERE, "K2_R508_JOINT_MCF_SCOPED_ABC_v1.json")
    t00 = time.time()
    model = json.load(open(a.model))
    rep = {"artifact": "k2_r504_joint_mcf_cp_sat_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-179 §四《方法教令 #5》(联合定位/有序多商品流族) · 一次实现窗(唯一) · §三.6 恰一次受证求解",
           "paradigm": "two-channel decomposition + anisotropic two-tier lattice + joint multi-commodity flow "
                       "(node-declaration capacity 1, linear), solved once by CP-SAT"}
    g = PREV.Gen(model)
    rep["preexisting_gates"] = PREV.gate_preexisting(model, g, 16)
    rep["selfcheck_soundness"] = selfcheck()
    pre_ok = bool(rep["preexisting_gates"]["all_pass"] and rep["selfcheck_soundness"]["pass"])
    rep["preconditions_all_green"] = pre_ok
    if not pre_ok:
        rep["decision"] = "STOP-BEFORE-BUILD: 前置硬闸/自检未过 ⇒ fail-closed"
        json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
        print("FAIL-FAST", out); return
    free = g.free_node
    # ---- anisotropic "wide" test (open-area interior): 5x5 base-free window -> coarse along x (even columns) ----
    wide = np.zeros((NX, NY), bool)
    for i in range(2, NX - 2):
        for j in range(2, NY - 2):
            if free[i, j] and free[i - 2:i + 3, j - 2:j + 3].all():
                wide[i, j] = True
    band = np.zeros((NX, NY), bool)
    band[:, 37:] = wide[:, 37:]            # x-coarsening only south of the gate (rows >= 37) where lanes travel east
    coarse = np.zeros((NX, NY), bool)
    coarse[0::2, :] = band[0::2, :]
    excl = band.copy(); excl[0::2, :] = False    # odd-x nodes inside the band are removed from the model
    rep["tier"] = {"coarse_nodes": int(coarse.sum()), "wide_nodes": int(wide.sum()), "free_nodes": int(free.sum())}
    # ---- lane groups (two-channel decomposition) ----
    wall_x = X0 + WALLC * P
    grp = {nm: ("west" if g.B[nm][0] < wall_x else "east") for nm in g.names}
    rep["lane_group"] = grp

    eu0, ev0 = g.edge_u.tolist(), g.edge_v.tolist()
    lanes = []
    for nm in g.names:
        n2 = g.node_ok(nm); nok = n2.reshape(-1); eok = g.edge_ok(nm)
        pts = g.pt_by_net[nm]
        s0 = g.nearest_node(g.A[nm], n2, pts)
        t0 = g.nearest_node(g.B[nm], n2, pts, taken=(s0,))
        src = nid(*s0); snk = nid(*t0)
        west = grp[nm] == "west"

        def allowed_vec():
            ok = nok.copy()
            if west:
                pass                      # (a) CHANNEL RELAXED (per #K2-181 sec.3.6a): west lanes share the whole east
                                          # gate with the east lanes; the old "wall-adjacent columns only" rule is REMOVED
            else:                         # east lane: not the west maze above row 32 (the A comb columns 0..23 stay open)
                for i in range(24, 113):
                    ok[i * NY:i * NY + 33] = False
            ok = ok & ~excl.reshape(-1)
            return ok
        av = allowed_vec()
        # step-1 arcs from the registered edge table
        keep = eok & av[g.edge_u] & av[g.edge_v]
        _bc = np.array([bool(coarse[u // NY, u % NY] and coarse[v // NY, v % NY])
                        for u, v in zip(eu0, ev0)], bool)
        _dx1 = np.array([abs(u // NY - v // NY) >= 1 for u, v in zip(eu0, ev0)], bool)
        keep &= ~(_bc & _dx1)   # |dx|=1 step between two coarse nodes => superseded by the step-2 moves
        arcs = [(int(u), int(v)) for u, v in zip(g.edge_u[keep].tolist(), g.edge_v[keep].tolist())]
        # step-2 arcs between coarse nodes (rigorous registered-ruler segment check)
        cand = []
        ci, cj = np.nonzero(coarse)
        for i, j in zip(ci.tolist(), cj.tolist()):
            u = nid(i, j)
            if not av[u]:
                continue
            for (di, dj) in ((2, 0), (2, 1), (2, -1)):
                ii, jj = i + di, j + dj
                if not (0 <= ii < NX and 0 <= jj < NY):
                    continue
                v = nid(ii, jj)
                if not (coarse[ii, jj] and av[v]):
                    continue
                cand.append((u, v))
        if cand:
            U = np.array([XY(*rc(u)) for u, v in cand]); V = np.array([XY(*rc(v)) for u, v in cand])
            okc = g.seg_ok_many(U, V, pts)
            arcs += [c for c, o in zip(cand, okc.tolist()) if o]
        adj = collections.defaultdict(list)
        for (u, v) in arcs:
            w = math.dist(XY(*rc(u)), XY(*rc(v)))
            adj[u].append((v, w)); adj[v].append((u, w))
        lanes.append({"nm": nm, "src": src, "snk": snk, "adj": dict(adj), "A": g.A[nm], "B": g.B[nm], "west": west})
    rep["graph"] = {"candidate_arcs_per_lane": [sum(len(x) for x in l["adj"].values()) // 2 for l in lanes]}
    # ---- prune: on-path with a declared detour budget ----
    tot = 0
    for L in lanes:
        def dij(st, A):
            best = {st: 0.0}; pq = [(0.0, st)]
            while pq:
                d, u = heapq.heappop(pq)
                if d > best.get(u, 1e18) + 1e-12: continue
                for (v, w) in A.get(u, ()):
                    nd = d + w
                    if nd < best.get(v, 1e18) - 1e-12:
                        best[v] = nd; heapq.heappush(pq, (nd, v))
            return best
        ds = dij(L["src"], L["adj"]); dt = dij(L["snk"], L["adj"])
        L["sp"] = ds.get(L["snk"], float("inf"))
        keep = {n for n in ds if n in dt and ds[n] + dt[n] <= BOUND * L["sp"] + 1e-9}
        adj2 = collections.defaultdict(list)
        for u in keep:
            for (v, w) in L["adj"][u]:
                if v in keep:
                    adj2[u].append((v, w))
        L["adj"] = adj2
        L["keep"] = keep
        tot += sum(len(x) for x in adj2.values())
    rep["graph"]["pruned_directed_arcs_per_lane"] = [sum(len(x) for x in l["adj"].values()) for l in lanes]
    rep["graph"]["total_pruned_directed_arcs"] = tot
    rep["graph"]["shortest_path_mm"] = {l["nm"]: round(l["sp"], 3) for l in lanes}
    if a.triage:
        # ---- READ-ONLY SKELETON TRIAGE (no Solve, no quota): locate WHY the skeleton is infeasible ----
        import heapq as _hq
        tri = {"per_lane": [], "verdict": None}
        for L in lanes:
            out_arcs = L["adj"].get(L["src"], [])
            in_arcs = [1 for u, lst in L["adj"].items() for (v, w) in lst if v == L["snk"]]
            # hop count of the shortest path in the PRUNED graph
            hops = {L["src"]: 0}; pq = [(0, L["src"])]
            while pq:
                d, u = _hq.heappop(pq)
                if d > hops.get(u, 10 ** 9): continue
                for (v, w) in L["adj"].get(u, ()): 
                    if d + 1 < hops.get(v, 10 ** 9):
                        hops[v] = d + 1; _hq.heappush(pq, (d + 1, v))
            nb = int(math.ceil(1.6 * L["sp"] / P)) + 4
            tri["per_lane"].append({"nm": L["nm"], "src_out_arcs": len(out_arcs), "snk_in_arcs": len(in_arcs),
                                    "shortest_hops": hops.get(L["snk"]), "arc_count_bound": nb,
                                    "bound_ok": (hops.get(L["snk"], 10 ** 9) <= nb)})
        # union-graph max node-disjoint paths: 16 srcs -> 16 snks (valid relaxation: node capacity 1)
        U = collections.defaultdict(list); nodes = set()
        for L in lanes:
            for u, lst in L["adj"].items():
                nodes.add(u)
                for (v, w) in lst:
                    nodes.add(v); U[u].append(v)
        NIDS = sorted(nodes)
        idx = {n: i for i, n in enumerate(NIDS)}
        NN = 2 * len(NIDS); S = NN; T = NN + 1
        cap = collections.defaultdict(dict)
        def add(u, v, c):
            cap[u][v] = cap[u].get(v, 0) + c; cap[v].setdefault(u, 0)
        for n in NIDS:
            add(2 * idx[n], 2 * idx[n] + 1, 1)
            for v in U.get(n, ()):
                add(2 * idx[n] + 1, 2 * idx[v], 1)
        for L in lanes:
            add(S, 2 * idx[L["src"]], 1)
            add(2 * idx[L["snk"]] + 1, T, 1)
        flow = 0
        while True:
            prev = {S: None}; dq = collections.deque([S])
            while dq and T not in prev:
                u = dq.popleft()
                for v, c in cap[u].items():
                    if c > 0 and v not in prev:
                        prev[v] = u; dq.append(v)
            if T not in prev: break
            x = T; path = []
            while x is not None:
                path.append(x); x = prev[x]
            for a1, b1 in zip(path[::-1], path[::-1][1:]):
                cap[a1][b1] -= 1; cap[b1][a1] += 1
            flow += 1
        # min-cut localisation: residual reachable set from S -> saturated node-splits are the bottleneck
        seen = {S}; dq = collections.deque([S])
        while dq:
            u = dq.popleft()
            for v, c in cap[u].items():
                if c > 0 and v not in seen:
                    seen.add(v); dq.append(v)
        cut = []
        for u in list(seen):
            for v, c in cap[u].items():
                if c == 0 and v not in seen and u % 2 == 0 and v == u + 1:
                    n = NIDS[u // 2]; cut.append([n // NY, n % NY])
        tri["bottleneck_cut_nodes_col_row"] = sorted(cut)
        tri["union_max_node_disjoint_paths_src_to_snk"] = flow
        tri["verdict"] = ("SKELETON CAPACITY < 16 => the discrete-node skeleton itself is infeasible "
                          "(a MODEL infeasibility core; NOT a board infeasibility claim)" if flow < 16 else
                          "skeleton capacity >= 16 => connectivity is NOT the culprit; suspect the arithmetic "
                          "constraints: per-lane exclusion (zero out/in arcs) or the length bound")
        rep["skeleton_triage"] = tri
        rep["decision"] = "TRIAGE-ONLY (read-only; no Solve(); no quota consumed)"
        json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
        print(json.dumps(tri, ensure_ascii=False, indent=1)[:2500]); print("WROTE", out); return

    if a.dry:
        rep["decision"] = "DRY: 只读规模读数（未建模型、未求解）"
        rep["elapsed_s"] = round(time.time() - t00, 1)
        json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
        print(json.dumps({k: rep[k] for k in ("tier", "graph", "selfcheck_soundness", "lane_group")},
                         ensure_ascii=False, indent=1)[:2500])
        print("WROTE", out); return
    # ---- joint MCF model ----
    from ortools.sat.python import cp_model
    mo = cp_model.CpModel()
    ASSUMP = {}
    x = {}
    for li, L in enumerate(lanes):
        for u, lst in L["adj"].items():
            for (v, w) in lst:
                x[(li, u, v)] = mo.NewBoolVar("x_%d_%d_%d" % (li, u, v))
    for li, L in enumerate(lanes):
        ins = collections.defaultdict(list); outs = collections.defaultdict(list); nodes = set()
        for u, lst in L["adj"].items():
            nodes.add(u)
            for (v, w) in lst:
                nodes.add(v); ins[v].append(x[(li, u, v)]); outs[u].append(x[(li, u, v)])
        for n in nodes:
            if n == L["src"]:
                mo.Add(sum(outs[n]) == 1); mo.Add(sum(ins[n]) == 0)
            elif n == L["snk"]:
                mo.Add(sum(ins[n]) == 1); mo.Add(sum(outs[n]) == 0)
            else:
                mo.Add(sum(ins[n]) == sum(outs[n]))
        mo.Add(sum(x[(li, u, v)] for u, lst in L["adj"].items() for (v, w) in lst)
               <= int(math.ceil(BOUND * L["sp"] / P)) + 4)
    # node declaration capacity (linear mutual exclusion)
    # ---- (b) EXACT per-lane clearance encoding (fixes R504's D2 permissiveness) ----
    #   E(r) = chosen arcs having r as an ENDPOINT ; PS(l,r) = lane l has an arc with r as a STRICT shadow
    #   constraints:  sum_E(r) <= 1   AND   for each lane l:  sum_{l'!=l} PS(l',r) + M*y(l,r) <= M
    #   (a lane may pass r and shadow r itself = legal; another lane shadowing r while someone passes r = violation)
    E = collections.defaultdict(list); S2 = collections.defaultdict(list)
    for li, L in enumerate(lanes):
        for u, lst in L["adj"].items():
            for (v, w) in lst:
                for c in claim_of(u, v):
                    (E if c in (u, v) else S2)[c].append((li, x[(li, u, v)]))
    ncons = 0
    for c, lst in E.items():
        if len(lst) > 1:
            mo.Add(sum(v for _, v in lst) <= 1); ncons += 1
    lit_clr = mo.NewBoolVar("clr"); ASSUMP["clearance_exact_per_lane"] = lit_clr
    for c in set(E) & set(S2):
        byE = collections.defaultdict(list); byS = collections.defaultdict(list)
        for li, v in E[c]:
            byE[li].append(v)
        for li, v in S2[c]:
            byS[li].append(v)
        for li, vs in byE.items():
            others = [v for l2, ws in byS.items() if l2 != li for v in ws]
            y = sum(vs) + (1 if lanes[li]["src"] == c else 0)
            if others:
                M = len(others) + 1
                mo.Add(sum(others) + M * y <= M).OnlyEnforceIf(lit_clr); ncons += 1
    # ---- (c) EXPLICIT ORDER / NON-CROSSING variables (gate column / yard row / wall gap) ----
    GATE_COLS = list(range(115, 136)); YARD_ROWS = list(range(38, 58)); GAPS = [7, 11, 12, 13, 15, 24, 25, 28]
    order = sorted(range(len(lanes)), key=lambda i: lanes[i]["A"][0])          # declared order: by A-anchor x
    wl = [i for i in order if lanes[i]["west"]]                                # west lanes in that order
    lit_c = mo.NewBoolVar("oc"); ASSUMP["order_gate_columns"] = lit_c
    lit_y = mo.NewBoolVar("oy"); ASSUMP["order_yard_rows"] = lit_y
    lit_g = mo.NewBoolVar("og"); ASSUMP["order_wall_gaps"] = lit_g
    norder = 0

    def link_slot(li, cands, node_of, lit, tag):
        z = {}
        for c in cands:
            z[c] = mo.NewBoolVar("z%s_%d_%d" % (tag, li, c))
        mo.Add(sum(z.values()) == 1)
        return z

    zc = {}; zy = {}
    for li in range(len(lanes)):
        zc[li] = link_slot(li, GATE_COLS, None, lit_c, "c")
        zy[li] = link_slot(li, YARD_ROWS, None, lit_y, "y")
    for c in GATE_COLS:
        mo.Add(sum(zc[li][c] for li in range(len(lanes))) <= 1).OnlyEnforceIf(lit_c); norder += 1
    for r in YARD_ROWS:
        mo.Add(sum(zy[li][r] for li in range(len(lanes))) <= 1).OnlyEnforceIf(lit_y); norder += 1
    for oa, ob in zip(order, order[1:]):                                # monotone non-crossing (gate columns)
        mo.Add(sum(c * zc[oa][c] for c in GATE_COLS) + 1 <= sum(c * zc[ob][c] for c in GATE_COLS)).OnlyEnforceIf(lit_c)
        mo.Add(sum(r * zy[oa][r] for r in YARD_ROWS) + 1 <= sum(r * zy[ob][r] for r in YARD_ROWS)).OnlyEnforceIf(lit_y)
        norder += 2
    byhead = collections.defaultdict(list)                              # per-lane arcs by head node (fast linking)
    for k in x:
        byhead[(k[0], k[2])].append(x[k])

    def linking(li, cands, node, z, lit):
        for cc in cands:
            arcs_in = byhead.get((li, node(cc)), [])
            mo.Add((sum(arcs_in) >= z[cc]) if arcs_in else (z[cc] == 0)).OnlyEnforceIf(lit)

    for li in range(len(lanes)):
        linking(li, GATE_COLS, lambda c: nid(c, 36), zc[li], lit_c)
        linking(li, YARD_ROWS, lambda r: nid(60, r), zy[li], lit_y)
    zg = {}
    for li in wl:
        zg[li] = link_slot(li, GAPS, None, lit_g, "g")
        linking(li, GAPS, lambda g: nid(114, g), zg[li], lit_g)
    for g in GAPS:
        mo.Add(sum(zg[li][g] for li in wl) <= 1).OnlyEnforceIf(lit_g); norder += 1
    for oa, ob in zip(wl, wl[1:]):
        mo.Add(sum(g * zg[oa][g] for g in GAPS) + 1 <= sum(g * zg[ob][g] for g in GAPS)).OnlyEnforceIf(lit_g); norder += 1
    rep["order_vars"] = {"gate_cols": GATE_COLS, "yard_rows": YARD_ROWS, "gaps": GAPS,
                         "lane_order_by_Ax": [lanes[i]["nm"] for i in order],
                         "west_order": [lanes[i]["nm"] for i in wl], "order_constraints": norder}
    v = mo.Validate()
    rep["model"] = {"bool_vars": len(mo.Proto().variables), "constraints": len(mo.Proto().constraints),
                    "clearance_constraints": ncons, "assumption_groups": list(ASSUMP), "validate": v or "OK", "bound_factor": BOUND}
    if v:
        rep["decision"] = "STOP-BEFORE-SOLVE: 模型 Validate 未过 ⇒ fail-closed"
        json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str); print("MODEL-INVALID", out); return
    for nm, lit in ASSUMP.items():
        mo.AddAssumption(lit)
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = a.maxtime
    sv.parameters.num_search_workers = 8
    ts = time.time(); st = sv.Solve(mo)
    if st == cp_model.INFEASIBLE:
        try:
            core = sv.SufficientAssumptionsForInfeasibility()
            idx = set(core)
            rep["unsat_core_sufficient"] = sorted(nm for nm, lit in ASSUMP.items() if lit.Index() in idx)
        except Exception as e:                                          # pragma: no cover
            rep["unsat_core_sufficient"] = "unavailable: %s" % e
    rep["solve"] = {"status": sv.StatusName(st), "wall_s": round(time.time() - ts, 1),
                    "quota_consumed": 1, "solve_calls": 1}
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        routes = {}
        for li, L in enumerate(lanes):
            used = collections.defaultdict(list)
            for u, lst in L["adj"].items():
                for (v, w) in lst:
                    if sv.Value(x[(li, u, v)]) == 1:
                        used[u].append(v)
            prev = {L["src"]: None}; dq = collections.deque([L["src"]]); path = None
            while dq:
                u = dq.popleft()
                if u == L["snk"]: break
                for w2 in used[u]:
                    if w2 not in prev:
                        prev[w2] = u; dq.append(w2)
            if L["snk"] in prev:
                path = []; cur = L["snk"]
                while cur is not None:
                    path.append(cur); cur = prev[cur]
                path.reverse()
            if not path:
                rep["solve"]["extract_fail"] = L["nm"]; break
            pts = [tuple(L["A"])] + [XY(*rc(n)) for n in path] + [tuple(L["B"])]
            o = [pts[0]]
            for q in pts[1:]:
                if math.dist(q, o[-1]) > 1e-9: o.append(q)
            routes[L["nm"]] = {"pts": [list(p) for p in o], "layer_cu": "In5.Cu", "n_vias": 2}
        if len(routes) == len(lanes):
            gg = PREV.exact_gate(model, routes, g.an, "In5.Cu", HW, set(), set(), P, frozenset())
            rep["exact_gate"] = {k: gg[k] for k in ("n_lane_pitch_viol", "lane_pitch_min_gap_mm", "lane_pitch_min_pair",
                                                    "n_clearance_viol", "clearance_min_mm", "endpoint_max_dev_mm") if k in gg}
            ok = (gg.get("n_lane_pitch_viol") == 0 and gg.get("n_clearance_viol") == 0 and gg.get("endpoint_max_dev_mm") == 0)
            rep["requirement_level_gate"] = "PASS" if ok else "FAIL"
            if ok:
                json.dump(routes, open(os.path.join(HERE, "K2_R504_JOINT_MCF_ROUTES_v1.json"), "w"), ensure_ascii=False)
                rep["per_lane_len_mm"] = {nm: round(sum(math.dist(r["pts"][k], r["pts"][k + 1])
                                                        for k in range(len(r["pts"]) - 1)), 3) for nm, r in routes.items()}
                rep["decision"] = "TERMINAL SAT: 16/16 联合 MCF 解 + 在册 exact_gate 全绿（#K2-177 §三 分支一）"
            else:
                rep["decision"] = "NON-TERMINAL: 独立核 FAIL"
        else:
            rep["decision"] = "NON-TERMINAL: 路径提取不全"
    else:
        rep["decision"] = "NON-TERMINAL: solver=%s（保守模型下未找到可行解；不作不可行主张）" % sv.StatusName(st)
    rep["elapsed_s"] = round(time.time() - t00, 1)
    json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: rep[k] for k in ("model", "solve", "exact_gate", "requirement_level_gate",
                                          "decision", "elapsed_s") if k in rep}, ensure_ascii=False, indent=1)[:2500])
    print("WROTE", out)


def _eidx(g, u, v):
    return 0


if __name__ == "__main__":
    main()
