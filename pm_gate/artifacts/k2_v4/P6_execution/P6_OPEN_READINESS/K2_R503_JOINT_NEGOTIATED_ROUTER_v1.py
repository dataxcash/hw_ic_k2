#!/usr/bin/env python3
"""K2 · R503 —— 《方法教令 #4》**联合（同时定位）**方法：**两通道 + 协商式联合绕线**（PathFinder 型）。

## 为什么是这个范式（对 #K2-178 §四 的落点）
| 教令 | 本件 |
|---|---|
| ① 次序题（排序＋指派＋绕行） | 16 条车道**同时**在场：每轮把所有通道的占用当**压力**，各车道在**同一张资源表**上重定位 |
| ② 域＝决策变量，非穷举候选表 | 域 = **自由栅格弧**（每网 ~2e4 条）；无候选族、无 `AddForbiddenAssignments` |
| ③ 在册学习案例 | R362/C-B2UP-1（多商品流）· R455（序/单调）· 在册 `exact_gate`（要求级谓词） |
| ④ 验收硬判据 | 前置全绿 → 联合定位 → **在册 `exact_gate`（独立核）** ＋ R495 要求级闸；缺一 fail-closed |

## 净距模型（**可核 · 局部精确**）
在册判据 = 两线**最近距离 ≥ P=0.435mm**。一条走线给出两类资源：
**路径节点集 N** 与**对角步影子节点集 S**（每个对角步把它两个"离对角节点"纳入影子）。
- **局部枚举证明**（本件自检 step，可复核）：在 5×5 格网补丁上**穷举所有弧对**，逐对用**在册
  `_seg_seg_batch`** 算真最近距，验证恒等式
  `真最近距 < P  ⟺  两弧的 (N,S) 满足  N∩N≠∅ 或 N∩S≠∅ 或 S∩N≠∅`。
  ⚠ 影子↔影子**不算**冲突：两条平行对角步若只共享一个影子节点，其距离 = 0.6152mm > P，**合法**
  （R503 修正了 R500「逐胞 5 条约束即完备」的漏项与过度约束）。
- ⇒ 节点 r 上的**精确**冲突判据：`|LN[r]| ≥ 2` 或 (`LN[r]≠∅` 且 `LS[r] \ LN[r] ≠ ∅`)，
  其中 `LN[r]`/`LS[r]` = 把 r 当**路径节点**/**影子节点**的车道集合。这是**线性**编码，不是候选表。

## 联合定位算法（declared · 固定参数 · 只跑一次）
协商式（PathFinder）：每轮**拆掉全部 16 条**、按"最长路优先"次序在同一资源表上重算最短路：
`cost(arc) = 边长 + PMUL·(邻居占用) + 历史罚`（节点占用与影子占用分账）；每轮对**仍冲突的节点**
`histN/histS += 1`；`PMUL` 按预声明的升级表增长（0.5 → ×1.25 每 4 轮，上限 4.0）。
收敛判据 = **无冲突节点**（⇒ 净距全 ≥ P），随后**渲染 → 独立在册 `exact_gate`**。
**纪律**：一次实现、恰跑一次、不改参重跑、前置不全绿 fail-closed、超时即停手报读数。
"""
import argparse, collections, heapq, json, math, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
PREV = __import__("K2_" + "R" + "499" + "_CONFLICT_TABLE_ONE_IMPLEMENTATION_v3")
P, HW, NY, NX, X0, Y0 = PREV.P, PREV.HW, PREV.NY, PREV.NX, PREV.X0, PREV.Y0
XY = PREV.XY
NID = NX * NY

# ---- declared algorithm parameters (frozen before the single run; NOT swept) ----
PMUL0, PMUL_MAX, PMUL_GROWTH, PMUL_EVERY = 0.5, 4.0, 1.25, 4
HINC = 1.0
MAXIT = 200


def shadow(u, v):
    """off-diagonal lattice nodes (< P from the diagonal step u->v); () for orthogonal steps."""
    iu, ju = u // NY, u % NY
    iv, jv = v // NY, v % NY
    if iu != iv and ju != jv:
        return (iu * NY + jv, iv * NY + ju)
    return ()


def arc_res(u, v):
    return (u, v) + shadow(u, v)


def seg_min(a, b):
    return float(PREV._seg_seg_batch(np.array([[a[0], a[1]]], float),
                                     np.array([[b[0], b[1]]], float)).min())


def arc_sets(u, v):
    """(node set, shadow set) of a lattice arc -- the exact clearance resource of the arc."""
    return frozenset((u, v)), frozenset(shadow(u, v))


def pair_violates(a, b):
    """exact local conflict predicate: both are nodes of one arc and node/shadow of the other."""
    n1, s1 = a; n2, s2 = b
    return bool((n1 & n2) or (n1 & s2) or (n2 & s1))


def check_local_equivalence(K=5, verbose=False):
    """exhaustive local proof of the resource model:

        true closest distance of two lattice arcs  <  P      <=>      pair_violates(arc1, arc2)

    (node-vs-node | node-vs-shadow; two parallel diagonals 0.6152mm apart that only share a
     SHADOW node are geometrically legal and are NOT a violation.)"""
    nodes = sorted((i, j) for i in range(K) for j in range(K))
    nset = set(nodes)
    arcs = []
    for (i, j) in nodes:
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == dj == 0:
                    continue
                t = (i + di, j + dj)
                if t in nset and (i, j) < t:
                    arcs.append(((i, j), t))
    sets = [arc_sets(a[0][0] * NY + a[0][1], a[1][0] * NY + a[1][1]) for a in arcs]
    geo = [[XY(*a[0]), XY(*a[1])] for a in arcs]
    bad = 0
    n = 0
    examples = []
    for x in range(len(arcs)):
        for y in range(x, len(arcs)):
            d = seg_min(geo[x], geo[y])
            v = pair_violates(sets[x], sets[y])
            n += 1
            if (d < P - 1e-9) != v:
                bad += 1
                if verbose and len(examples) < 8:
                    examples.append([arcs[x], arcs[y], round(d, 4), v])
    return {"pairs_checked": n, "mismatches": bad, "pass": bad == 0, "examples": examples,
            "criterion": "true closest distance (registered _seg_seg_batch) < P=%s  <=>  "
                         "node-vs-node or node-vs-shadow" % P}


def simplify(pts):
    o = [tuple(pts[0])]
    for p in pts[1:]:
        if math.dist(p, o[-1]) > 1e-9:
            o.append(tuple(p))
    out = [o[0]]
    for i in range(1, len(o) - 1):
        a, b, c = out[-1], o[i], o[i + 1]
        if abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) > 1e-12:
            out.append(b)
    out.append(o[-1])
    return [tuple(round(c, 4) for c in p) for p in out]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="/tmp/opencode/archer/model_l8.json")
    ap.add_argument("--budget", type=float, default=1500.0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or os.path.join(HERE, "K2_R503_JOINT_NEGOTIATED_ROUTER_v1.json")
    t00 = time.time()
    model = json.load(open(a.model))
    rep = {"artifact": "k2_r503_joint_negotiated_router_v1",
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-178 §四（方法教令#4：次序/联合范式）· §七（非终局处置）· #K2-177 §一/§三 · R501/R502 读数",
           "paradigm": "JOINT simultaneous relocation of all 16 lanes on the free lattice with a "
                       "capacity-1 resource table (path nodes + diagonal off-diagonal shadows); "
                       "no candidate family, no forbidden-assignment table",
           "declared_parameters": {"PMUL0": PMUL0, "PMUL_MAX": PMUL_MAX, "PMUL_GROWTH": PMUL_GROWTH,
                                   "PMUL_EVERY": PMUL_EVERY, "HINC": HINC, "MAXIT": MAXIT,
                                   "lane_order": "longest shortest-path first (deterministic, fixed)"}}
    g = PREV.Gen(model)
    rep["preexisting_gates"] = PREV.gate_preexisting(model, g, 16)
    pre_ok = bool(rep["preexisting_gates"]["all_pass"])
    rep["preconditions_all_green"] = pre_ok
    rep["local_equivalence_proof"] = check_local_equivalence()
    if not pre_ok or not rep["local_equivalence_proof"]["pass"]:
        rep["decision"] = "STOP-BEFORE-ROUTE: 前置硬闸/局部等价证明未过 ⇒ fail-closed"
        json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
        print("FAIL-FAST", out)
        return
    # ---- per-lane symmetric legal graph ----
    lanes = []
    for nm in g.names:
        n2 = g.node_ok(nm); nok = n2.reshape(-1); eok = g.edge_ok(nm)
        pts = g.pt_by_net[nm]
        s0 = g.nearest_node(g.A[nm], n2, pts)
        t0 = g.nearest_node(g.B[nm], n2, pts, taken=(s0,))
        src = s0[0] * NY + s0[1]; snk = t0[0] * NY + t0[1]
        keep = eok & nok[g.edge_u] & nok[g.edge_v]
        adj = collections.defaultdict(list)
        for u, v, L in zip(g.edge_u[keep].tolist(), g.edge_v[keep].tolist(), g.edge_len[keep].tolist()):
            adj[u].append((v, L)); adj[v].append((u, L))
        lanes.append({"nm": nm, "src": src, "snk": snk, "adj": adj, "A": g.A[nm], "B": g.B[nm],
                      "n_nodes": len(adj), "n_arcs": sum(len(x) for x in adj.values())})
    rep["graph"] = {"nodes_per_lane": [l["n_nodes"] for l in lanes],
                    "directed_arcs_per_lane": [l["n_arcs"] for l in lanes],
                    "total_directed_arcs": sum(l["n_arcs"] for l in lanes)}
    # deterministic order: longest shortest path first
    def shortest(l, w=None):
        INF = float("inf"); best = {l["src"]: 0.0}; pq = [(0.0, l["src"])]
        while pq:
            d, u = heapq.heappop(pq)
            if d > best.get(u, INF) + 1e-12: continue
            for (v, ln) in l["adj"][u]:
                nd = d + ln
                if nd < best.get(v, INF) - 1e-12:
                    best[v] = nd; heapq.heappush(pq, (nd, v))
        return best
    base = []
    for l in lanes:
        b = shortest(l); l["sp"] = b.get(l["snk"], float("inf"))
        base.append(l["sp"])
    order = sorted(range(len(lanes)), key=lambda i: (-lanes[i]["sp"], lanes[i]["nm"]))
    rep["lane_order"] = [lanes[i]["nm"] for i in order]
    rep["lane_shortest_path_mm"] = {lanes[i]["nm"]: round(base[i], 3) for i in order}

    # ---- EXACT clearance resources (locally proven in check_local_equivalence) ----
    #   LN[r] = lanes using node r as a PATH NODE ; LS[r] = lanes SHADOWING node r
    #   violation(r)  <=>  |LN[r]| >= 2   OR   (LN[r] != {} and LS[r] - LN[r] != {})
    #   (two parallel diagonals 0.6152mm apart that only share a shadow node are LEGAL)
    LN = collections.defaultdict(set)
    LS = collections.defaultdict(set)
    histN = collections.defaultdict(float)
    histS = collections.defaultdict(float)
    claim = {}   # lane -> (node set, shadow set)
    path = {}    # lane -> node list

    def claims_of(p):
        sh = []
        for u, v in zip(p, p[1:]):
            sh.extend(shadow(u, v))
        return set(p), set(sh)

    def place(l, p):
        n, sh = claims_of(p)
        claim[l] = (n, sh); path[l] = p
        for r in n:
            LN[r].add(l)
        for r in sh:
            LS[r].add(l)

    def rip(l):
        if l in claim:
            n, sh = claim[l]
            for r in n:
                LN[r].discard(l)
            for r in sh:
                LS[r].discard(l)
            del claim[l]
            del path[l]

    def route(l, pmul):
        L = lanes[l]
        INF = float("inf"); best = {L["src"]: 0.0}; prev = {}; pq = [(0.0, L["src"])]
        while pq:
            d, u = heapq.heappop(pq)
            if d > best.get(u, INF) + 1e-12:
                continue
            if u == L["snk"]:
                break
            for (v, ln) in L["adj"][u]:
                oth = LN[v] - {l}; osh = LS[v] - {l}
                pen = pmul * (len(oth) + len(osh)) + histN[v] + (histS[v] if osh else 0.0)
                for sx in shadow(u, v):
                    pen += pmul * len(LN[sx] - {l}) + histN[sx] + histS[sx]
                nd = d + ln + pen
                if nd < best.get(v, INF) - 1e-12:
                    best[v] = nd; prev[v] = u; heapq.heappush(pq, (nd, v))
        if L["snk"] not in best:
            return None
        p = []; cur = L["snk"]
        while cur != L["src"]:
            p.append(cur); cur = prev[cur]
        p.append(L["src"]); p.reverse()
        return p

    def violating_nodes():
        out = set()
        for r, ns in LN.items():
            if len(ns) >= 2:
                out.add(r)
            elif ns and (LS.get(r, set()) - ns):
                out.add(r)
        return out

    it = 0
    hist_trace = []
    best = None
    while it < MAXIT and time.time() - t00 < a.budget:
        it += 1
        pmul = min(PMUL_MAX, PMUL0 * (PMUL_GROWTH ** (it // PMUL_EVERY)))
        for l in order:
            rip(l)
            p = route(l, pmul)
            if p is None:
                rep["decision"] = "NON-TERMINAL: 某网在合法弧图上无非空路（异常）"
                rep["elapsed_s"] = round(time.time() - t00, 1)
                json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
                print("NO-PATH", lanes[l]["nm"], out)
                return
            place(l, p)
        bad = violating_nodes()
        if best is None or len(bad) < best[0]:
            best = (len(bad), it, {l: list(path[l]) for l in order}, set(bad))
        hist_trace.append({"it": it, "pmul": round(pmul, 3), "violating_nodes": len(bad),
                           "t": round(time.time() - t00, 1)})
        if it % 5 == 0 or not bad:
            print("it=%d pmul=%.3f violating_nodes=%d t=%.1fs" % (it, pmul, len(bad), time.time() - t00))
        if not bad:
            break
        for r in bad:
            histN[r] += HINC
            if LS.get(r):
                histS[r] += HINC
    rep["negotiation"] = {"iterations": it, "final_violating_nodes": best[0] if best else None,
                          "best_iteration": best[1] if best else None,
                          "trace_tail": hist_trace[-6:], "converged": bool(best and best[0] == 0)}
    if not (best and best[0] == 0):
        rep["decision"] = ("NON-TERMINAL: 协商未收敛（联合定位未给出无冲突解）⇒ 交监理生产方式复核（#K2-178 §七）")
        rep["elapsed_s"] = round(time.time() - t00, 1)
        json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
        print(json.dumps(rep["negotiation"], ensure_ascii=False, indent=1)[:1500]); print("WROTE", out)
        return
    # ---- render + independent registered requirement gate ----
    routes = {}
    for l in order:
        L = lanes[l]
        p = best[2][l]
        pts = [tuple(L["A"])] + [XY(n // NY, n % NY) for n in p] + [tuple(L["B"])]
        routes[L["nm"]] = {"pts": [list(q) for q in simplify(pts)], "layer_cu": "In5.Cu", "n_vias": 2}
    gg = PREV.exact_gate(model, routes, g.an, "In5.Cu", HW, set(), set(), P, frozenset())
    rep["exact_gate"] = {k: gg[k] for k in ("n_lane_pitch_viol", "lane_pitch_min_gap_mm", "lane_pitch_min_pair",
                                            "n_clearance_viol", "clearance_min_mm", "endpoint_max_dev_mm")
                         if k in gg}
    ok = (gg.get("n_lane_pitch_viol") == 0 and gg.get("n_clearance_viol") == 0
          and gg.get("endpoint_max_dev_mm") == 0)
    rep["requirement_level_gate"] = "PASS" if ok else "FAIL"
    rep["per_lane_len_mm"] = {nm: round(sum(math.dist(r["pts"][i], r["pts"][i + 1])
                                            for i in range(len(r["pts"]) - 1)), 3) for nm, r in routes.items()}
    LN2 = collections.defaultdict(set); LS2 = collections.defaultdict(set)
    for l, (n, sh) in claim.items():
        for r in n:
            LN2[r].add(l)
        for r in sh:
            LS2[r].add(l)
    viol = 0
    for r, ns in LN2.items():
        if len(ns) >= 2 or (ns and (LS2.get(r, set()) - ns)):
            viol += 1
    rep["resource_check"] = {"violating_nodes": viol,
                             "node_claim_lane_slots": sum(len(v) for v in LN2.values()),
                             "shadow_claim_lane_slots": sum(len(v) for v in LS2.values()),
                             "max_node_sharers": max((len(v) for v in LN2.values()), default=0),
                             "max_shadow_sharers": max((len(v) for v in LS2.values()), default=0)}
    if ok:
        json.dump(routes, open(os.path.join(HERE, "K2_R503_JOINT_ROUTES_v1.json"), "w"), ensure_ascii=False)
        rep["decision"] = ("TERMINAL SAT: 16/16 联合定位解 + 在册 exact_gate 全绿（#K2-177 §三 分支一）"
                           if rep["resource_check"]["violating_nodes"] == 0 else
                           "NON-TERMINAL: 资源冲突残留")
    else:
        rep["decision"] = "NON-TERMINAL: 独立核 FAIL"
    rep["elapsed_s"] = round(time.time() - t00, 1)
    json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: rep[k] for k in ("negotiation", "exact_gate", "requirement_level_gate",
                                          "resource_check", "decision", "elapsed_s")},
                     ensure_ascii=False, indent=1)[:2500])
    print("WROTE", out)


if __name__ == "__main__":
    main()
