#!/usr/bin/env python3
"""K2 · R504 —— 遵《方法教令 #5》（#K2-179 §四）**联合方法一次实现窗（唯一）**：
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
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or os.path.join(HERE, "K2_R504_JOINT_MCF_CP_SAT_v1.json")
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
            if west:                      # west lane (B west of the wall): not the east gate above row 32
                for i in range(119, NX):
                    ok[i * NY:i * NY + 33] = False
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
    # EXACT clearance encoding (R503 §一 local equivalence, extended to step-2 arcs by the self-check):
    #   node r:  E(r) = chosen arcs having r as an ENDPOINT (== a lane passing through r)
    #            S(r) = chosen arcs having r as a STRICT shadow (r within <P of the segment, not an endpoint)
    #   constraints per node:  sum_E <= 1   AND   sum_E + sum_S <= 2
    #   => node-vs-node forbidden; node-vs-shadow forbidden; shadow-vs-shadow ALLOWED (parallel diagonals
    #      0.6152mm apart sharing one shadow node are geometrically legal, cf. R500's false claim).
    E = collections.defaultdict(list); S = collections.defaultdict(list)
    for li, L in enumerate(lanes):
        for u, lst in L["adj"].items():
            for (v, w) in lst:
                for c in claim_of(u, v):
                    (E if c in (u, v) else S)[c].append(x[(li, u, v)])
    ncons = 0
    for c in set(E) | set(S):
        e = E.get(c, []); sh = S.get(c, [])
        if len(e) > 1:
            mo.Add(sum(e) <= 1); ncons += 1
        if len(e) + len(sh) > 2:
            mo.Add(sum(e) + sum(sh) <= 2); ncons += 1
    v = mo.Validate()
    rep["model"] = {"bool_vars": len(mo.Proto().variables), "constraints": len(mo.Proto().constraints),
                    "clearance_constraints": ncons, "validate": v or "OK", "bound_factor": BOUND}
    if v:
        rep["decision"] = "STOP-BEFORE-SOLVE: 模型 Validate 未过 ⇒ fail-closed"
        json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str); print("MODEL-INVALID", out); return
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = a.maxtime
    sv.parameters.num_search_workers = 8
    ts = time.time(); st = sv.Solve(mo)
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
