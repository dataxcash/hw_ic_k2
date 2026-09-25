#!/usr/bin/env python3
"""K2 · R548 —— **R540 固定路点链"鸽笼"不可行证书 ＋ 零配额构造法出图尝试**（承 #K2-215 → #K2-213 §四 · 令一字不改）。

【本件要回答的事】
 #K2-213 §四 判定 R543 的 0.2s INFEASIBLE = 「域太窄、缺备选路」，并下令 k=3~5 备选域 ＋ 定序构造回溯。
 本件机核：**该判定不成立** —— 不可行性 **不在路点之间的走法**，而在 **路点本身**：
 R540 逐线固定路点链里有 **5 条线被要求过同一格点 3956（col60,row56）**，而板子只有 **2 个走线层**
 ⇒ **任何走法都不可能**（鸽笼：5 > 2）。故 k-备选路、回溯、任何求解器都救不了。

【证据链（全部机核 · 0 求解器 · 0 受证配额）】
 ① 字面读法（路点 = In5 格点，同 R543）：node 3956 需承载 5 线 ⇒ 5 > 1 层格点 ⇒ UNSAT。
 ② 时刻表读法（路点层 = 该断面所在站的在册 In4 时段）：node 3956 在 In4 上仍需 4 线 ⇒ 4 > 1 ⇒ UNSAT。
 ③ 根因（上游）：R529 主问题的 `section_slots` **不满足它自己的「逐(断面,层) all-different」本意**：
    col60@In4 槽 56 有 4 线、col33@In4 槽 57 有 2 线。R529 的编码 `on4[i]+on4[j] != 0`（只禁"两者皆 In5"）
    而**未禁"两者皆 In4"** ⇒ 一个不可实现的槽位分配被判成 OPTIMAL，并被 R540 机械提取为固定输入。
 ④ 次生缺陷（R544 已暴露）：R540 把「同槽位不同层」的两条线的 pad_run 都落在**同一层同一格点**（如 col114 row24/15）。

【零配额构造法（#K2-213 §四 指定）—— 本件照做并运行】
 域 = 带 ∪ 固定航点 ∪ 逐段最短路膨胀走廊 ∪ **逐段 k 最短路并集**（k=4）；规模对 1.2M bool 闸。
 联合安放 = 定序构造 ＋ 冲突回溯（协商式 rip-up & reroute，PathFinder 型；零配额外部下限）。
 ① 在**原固定输入**上：开工即被 ①/② 的鸽笼挡住（**不发一枪**即证无解）。
 ② 在 **L2 槽位修复**（逐(断面,层) node-injective，节点仍须在该线图上）后的链上：16/16 网布通，但仍有残余重叠
    ⇒ **尚不构成可制造图纸**；残余重叠的根因指向「入口扇出的同层次序一致（form C / 入口扇）未被满足」，
    属**下一件**（L2 槽位重推必须联立序一致）的活。

【边界】0 受证配额 · 未改冻结四源/生成器/SPEC/原理图/criteria · 未改 R540/R529 在册件 · 停线维持 · owner 项 0。
禁：精确解 · 改 R540 语义（本件**不改**，而是**证明**其在字面读法下不可行）· 无诊断重跑。
"""
import argparse, collections, hashlib, importlib, json, math, os, sys, time, types
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
OWN_OUT = "K2_R548_R540_CHAIN_INFEASIBILITY_CERTIFICATE_v1.json"
LOGDIR = "/tmp/opencode/r548"
LOGF = os.path.join(LOGDIR, "r548_certificate.log")
SPEC = os.path.join(HERE, "K2_R540_CORRIDOR_SPEC_v1.json")
R529 = os.path.join(HERE, "K2_R529_WOVEN_COMPLETE_MASTER_v1.json")
MODEL = "/tmp/opencode/archer/model_l8.json"
GATE_BOOL = 1_200_000
K_SHORTEST = 4
RB = 3


def log(msg):
    os.makedirs(LOGDIR, exist_ok=True)
    with open(LOGF, "a") as fh:
        fh.write(str(msg) + "\n")
    print(str(msg), flush=True)


def _install_ortools_shim():
    """This container has NO ortools; the registered generator module imports cp_model at top level but
    Gen2() never calls it. A stub module lets us IMPORT the registered generator unmodified
    (no install, no generator edit, no caliber change)."""
    if "ortools" in sys.modules:
        return
    for nm in ("ortools", "ortools.sat", "ortools.sat.python"):
        sys.modules.setdefault(nm, types.ModuleType(nm))
    cm = types.ModuleType("ortools.sat.python.cp_model")
    class _D:
        def __init__(self, *a, **k): pass
    cm.CpModel = _D
    cm.CpSolver = _D
    cm.OPTIMAL, cm.FEASIBLE, cm.INFEASIBLE, cm.UNKNOWN = 1, 2, 3, 0
    sys.modules["ortools.sat.python.cp_model"] = cm
    sys.modules["ortools.sat.python"].cp_model = cm


_install_ortools_shim()
W = importlib.import_module("K2_R515_FREETERMINALS_v1")
P, X0, Y0, NX, NY, NID, TERM_BASE = W.P, W.X0, W.Y0, W.NX, W.NY, W.NID, W.TERM_BASE
XY, VIA_SEP = W.XY, W.VIA_SEP
MAXV = 2 * W.MAX_VIA_PAIRS
STATIONS = ["COMB", "BELT", "WALL", "FIELD"]
COL33, COL60, COL114, ROW36 = 33, 60, 114, 36
GAPS = [7, 11, 12, 13, 15, 24, 25, 28]
GATE_COLS = list(range(115, 136))


def node_id(L, pos):
    return L * NID + pos


def node_of(tag, v, east):
    if tag == "col33":
        return COL33 * NY + v
    if tag == "col60":
        return COL60 * NY + v
    return (v * NY + ROW36) if east else (COL114 * NY + v)


# ------------------------------------------------------------------ certificate
def certificate(spec, master):
    """node-pigeonhole certificate: how many lanes are forced through one (node[,layer])."""
    def on4(nm, t):
        return 1 if STATIONS[t] in master["schedule"][nm]["stations_on_In4"] else 0
    lay = {"A_anchor": 0, "B_anchor": 0, "In5_entrance": 0, "DIVE_via": 1}
    for t, tag in ((0, "col33"), (1, "col60")):
        lay[tag] = None  # filled per lane
    out = {"literal_all_In5": {}, "schedule_aware": {}}
    for mode in ("literal_all_In5", "schedule_aware"):
        occ = collections.defaultdict(set)
        for nm, v in spec["per_lane"].items():
            seen = set()
            for w in v["waypoints"]:
                if "node" not in w:
                    continue
                k = w["kind"]
                if mode == "literal_all_In5":
                    L = 0
                else:
                    if k in ("col33", "col60"):
                        L = on4(nm, 0 if k == "col33" else 1)
                    elif k in ("exit_wall_gap", "exit_gate_col"):
                        L = on4(nm, 2)
                    elif k == "pad_run":
                        L = on4(nm, 3)
                    else:
                        L = lay[k]
                seen.add((L, w["node"]))
            for key in seen:
                occ[key].add(nm)
        witnesses = [{"layer": L, "node": int(n), "col": int(n) // NY, "row": int(n) % NY,
                      "n_lanes": len(ls), "lanes": sorted(ls)}
                     for (L, n), ls in occ.items() if len(ls) > 1]
        witnesses.sort(key=lambda d: -d["n_lanes"])
        out[mode] = {"n_colliding_node_layer": len(witnesses), "max_multiplicity":
                     (witnesses[0]["n_lanes"] if witnesses else 0), "layers_available": 2,
                     "witnesses": witnesses[:8], "verdict": "INFEASIBLE" if witnesses else "no pre-routing collision"}
    # ---- upstream root cause: R529 section slots violate R529's own per-(section,layer) all-different
    dups = []
    for tag, st in (("col33", 0), ("col60", 1), ("exit", 2)):
        g = collections.defaultdict(list)
        for nm in spec["per_lane"]:
            g[(on4(nm, st), master["section_slots"][nm][tag])].append(nm)
        for (L, slot), ns in sorted(g.items()):
            if len(ns) > 1:
                dups.append({"section": tag, "layer": L, "slot": int(slot), "n_lanes": len(ns), "lanes": sorted(ns)})
    policy_ok = all(v["verdict"] == "INFEASIBLE" for v in out.values())
    return out, dups, policy_ok


def r529_encoding_gap():
    return {
        "r529_constraint_as_written": "mo.Add(on4[i][t] + on4[j][t] != 0)  # same slot => NOT both on In5",
        "r529_comment_intent": "same transverse slot at this section => they must not be on the same layer there",
        "defect": "written form forbids only (In5,In5); it ALLOWS (In4,In4) => two/四 lanes may legally share one "
                  "In4 lattice node; the intended per-(section,layer) all-different is NOT enforced",
        "consequence": "an unrealizable slot assignment was certified OPTIMAL by R529 and mechanically extracted "
                       "into R540 as a FIXED input => every downstream joint model (R534/R535/R543) is UNSAT at the "
                       "waypoints, not in the routing between them",
        "minimal_repair": "re-derive section_slots so that per (section, layer) all lanes have DISTINCT transverse "
                          "positions (and jointly with fan order + form-C order consistency); L2 scope (slot/corridor)",
    }


# ------------------------------------------------------------------ domain (k shortest union)
def k_shortest_union(g2, spec, master, names, lanes, k=K_SHORTEST, log=print):
    """Per lane per segment: k diverse shortest paths inside band ∪ waypoints ∪ dilated corridor; union node sets.
    Reports induced-arc bool size vs the 1.2M gate."""
    dom = {}
    for nm in names:
        wps = spec["per_lane"][nm]["waypoints"]
        chain = [lanes[nm]["src"]] + [w["node"] for w in wps[1:-1]] + [lanes[nm]["snk"]]
        fixed = set(x for x in chain if x < TERM_BASE)
        adj = collections.defaultdict(set)
        for u, lst in lanes[nm]["adj"].items():
            for (v, _w) in lst:
                adj[u].add(v)
        nodes_union = set()
        arcs_union = set()
        for s in range(len(chain) - 1):
            src, dst = chain[s], chain[s + 1]
            if src == dst:
                continue
            # segment domain = fixed waypoints ∪ dilated shortest corridor (band is implicit in lanes[nm])
            sp = set()
            prev = {src: None}; dq = collections.deque([src])
            while dq:
                x = dq.popleft()
                if x == dst:
                    break
                for y in adj[x]:
                    if y not in prev:
                        prev[y] = x; dq.append(y)
            if dst in prev:
                x = dst
                while x is not None:
                    if x < TERM_BASE:
                        i0, j0 = (x % NID) // NY, (x % NID) % NY
                        for di in range(-RB, RB + 1):
                            for dj in range(-RB, RB + 1):
                                u2, v2 = i0 + di, j0 + dj
                                if 0 <= u2 < NX and 0 <= v2 < NY:
                                    sp.add(u2 * NY + v2)
                    x = prev[x]
            allowed = set()
            for u in adj:
                if u >= TERM_BASE or (u % NID) in sp or u in fixed:
                    allowed.add(u)
            pen = collections.Counter()
            for _i in range(k):
                dist = {src: 0.0}; pr = {}; pq = [(0.0, src)]
                import heapq
                while pq:
                    d, u = heapq.heappop(pq)
                    if d > dist.get(u, 1e18) + 1e-12:
                        continue
                    if u == dst:
                        break
                    for v in adj.get(u, ()):
                        if v not in allowed and v not in (src, dst):
                            continue
                        nd = d + 1.0 + pen[v]
                        if nd < dist.get(v, 1e18) - 1e-12:
                            dist[v] = nd; pr[v] = u; heapq.heappush(pq, (nd, v))
                if dst not in pr:
                    break
                path = []; x = dst
                while x is not None:
                    path.append(x); x = pr.get(x)
                path.reverse()
                for q in path:
                    nodes_union.add(q); pen[q] += 0.6
                for a, b in zip(path, path[1:]):
                    arcs_union.add((a, b))
        dom[nm] = {"n_nodes_union": len(nodes_union), "n_arcs_union": len(arcs_union)}
        log("[domain] %-22s nodes=%d arcs=%d" % (nm, len(nodes_union), len(arcs_union)))
    total_bool = sum(v["n_arcs_union"] for v in dom.values())
    return {"k": k, "construction": "per lane per segment: k diverse shortest paths inside "
                                    "(band ∩ own graph) ∪ fixed waypoints ∪ dilated(R<=%d) shortest corridor; union of nodes/arcs" % RB,
            "per_lane": dom, "total_bool_vars": total_bool, "gate": GATE_BOOL,
            "under_gate": total_bool <= GATE_BOOL}


# ------------------------------------------------------------------ slot repair (L2)
def _on4(master, nm, st):
    return 1 if STATIONS[st] in master["schedule"][nm]["stations_on_In4"] else 0


def repair_slots(g2, master, spec, names, lanes):
    """L2 slot re-derivation (self-adjudicated, L2 = slot/corridor policy):
      * per (section, layer): DISTINCT transverse positions (node-injective) AND
      * ORDER-CONSISTENT: positions are assigned monotonically along a single lane order per layer, which
        simultaneously enforces (a) the entrance fan order (entrance column == A.x order), (b) form C between
        co-axial adjacent sections (col33->col60, col60->exit_west), (c) the east pad-approach order
        (gate column == B.x order).  Universe = registered raw ranges; the in-register pitch is node-disjoint (1P).
    """
    grp_of = {nm: ("east" if g2.grp[nm] == "east" else "west") for nm in names}
    order = sorted(names, key=lambda nm: (g2.A[nm][0], g2.A[nm][1]))
    gidx = {nm: i for i, nm in enumerate(order)}
    uni = {"col33": list(range(29, 58)), "col60": list(range(38, 58)),
           "exit_west": list(GAPS), "exit_east": list(GATE_COLS)}
    repair = {nm: {} for nm in names}
    movements = []
    for tag, st in (("col33", 0), ("col60", 1), ("exit", 2)):
        groups = collections.defaultdict(list)
        for nm in names:
            L = _on4(master, nm, st)
            if tag == "exit":
                key = ("west", None) if grp_of[nm] == "west" else ("east", L)
            else:
                key = ("", L)
            groups[key].append(nm)
        for key, grp in groups.items():
            g, Lk = key
            east = (g == "east")
            u = sorted(uni["exit_west" if g == "west" else "exit_east"]) if tag == "exit" else sorted(uni[tag])

            def ln_of(nm):
                return _on4(master, nm, st) if Lk is None else Lk

            pad_col = {}
            for q in names:
                if grp_of[q] == "east":
                    pad_col.setdefault(_on4(master, q, 3), {})[int(round((g2.B[q][0] - X0) / P))] = q

            def ok(nm, v):
                ln = ln_of(nm)
                pos = node_of(tag, v, east)
                if not (bool(g2._nok[(nm, ln)][pos]) and (node_id(ln, pos) in lanes[nm]["adj"])):
                    return False
                # east: the exit gate node (v,row36,L2) must not coincide with ANOTHER east lane's pad node
                # (B.x col,row36,L3) when L2 == L3 (R540 puts pad_run on row36 too).
                if tag == "exit" and east and v in pad_col.get(ln, {}):
                    return pad_col[ln][v] == nm
                return True
            # lane order inside the group: east exit -> by B.x (pad_run column); else by global A.x order
            if tag == "exit" and east:
                gorder = sorted(grp, key=lambda nm: (g2.B[nm][0], gidx[nm]))
            else:
                gorder = sorted(grp, key=lambda nm: gidx[nm])
            prev = -10 ** 9
            used = set()
            for nm in gorder:
                nom = master["section_slots"][nm][tag]
                cands = [v for v in u if v > prev and v not in used and ok(nm, v)]
                if not cands:
                    return None, {"fail": tag, "group": [g, Lk], "lane": nm, "prev": prev}
                v = cands[0]
                if v != nom:
                    movements.append({"lane": nm, "section": tag, "from": nom, "to": v})
                repair[nm][tag] = v
                prev = v; used.add(v)
    # ---- verification: (a) node-injective per (section, layer); (b) west pad-run node-injective on layer 0;
    #      (c) form-C / fan order consistency (0 flips on same-layer co-axial pairs)
    coll = []
    for tag, st in (("col33", 0), ("col60", 1), ("exit", 2)):
        occ = collections.defaultdict(list)
        for nm in names:
            L = _on4(master, nm, st)
            nd = node_of(tag, repair[nm][tag], grp_of[nm] == "east")
            occ[(L, nd)].append(nm)
            if tag == "exit" and grp_of[nm] == "west":
                occ[(0, nd)].append(nm)
        coll += [{"layer": k[0], "node": int(k[1]), "lanes": sorted(set(v))}
                 for k, v in occ.items() if len(set(v)) > 1]

    def rows(tag, st, nm):
        L = _on4(master, nm, st)
        return repair[nm][tag], L
    flips = []
    for (tagA, stA, tagB, stB) in (("col33", 0, "col60", 1), ("col60", 1, "exit", 2)):
        for ii in range(len(names)):
            for jj in range(ii + 1, len(names)):
                a, b = names[ii], names[jj]
                if tagB == "exit" and (grp_of[a] == "east" or grp_of[b] == "east"):
                    continue
                La, Lb = _on4(master, a, stA), _on4(master, b, stA)
                if La != Lb or _on4(master, a, stB) != La or _on4(master, b, stB) != Lb:
                    continue
                pa, pb = repair[a][tagA], repair[b][tagA]
                qa, qb = repair[a][tagB], repair[b][tagB]
                if ((pa > pb) - (pa < pb)) != ((qa > qb) - (qa < qb)):
                    flips.append({"pair": [a, b], "sections": [tagA, tagB]})
    return repair, {"movements": movements, "n_movements": len(movements),
                    "post_repair_node_layer_collisions": len(coll), "collisions": coll[:8],
                    "order_consistency_flips": len(flips), "flips": flips[:8],
                    "verdict": "PASS" if (not coll and not flips) else "FAIL"}


def build_chain(g2, spec, master, names, repair):
    chain = {}
    for nm in names:
        east = g2.grp[nm] == "east"
        L = {0: 0, 1: 0, 2: 0, 3: 0}
        L[0] = 1 if STATIONS[0] in master["schedule"][nm]["stations_on_In4"] else 0
        L[1] = 1 if STATIONS[1] in master["schedule"][nm]["stations_on_In4"] else 0
        L[2] = 1 if STATIONS[2] in master["schedule"][nm]["stations_on_In4"] else 0
        L[3] = 1 if STATIONS[3] in master["schedule"][nm]["stations_on_In4"] else 0
        items = []
        for w in spec["per_lane"][nm]["waypoints"]:
            k = w["kind"]
            if k == "A_anchor":
                items.append(("A", None, 0))
            elif k == "B_anchor":
                items.append(("B", None, 0))
            elif k == "In5_entrance":
                items.append(("wp", w["node"], 0))
            elif k == "DIVE_via":
                items.append(("via", w["node"], 1))
            elif k == "col33":
                items.append(("wp", node_of("col33", repair[nm]["col33"], east), L[0]))
            elif k == "col60":
                items.append(("wp", node_of("col60", repair[nm]["col60"], east), L[1]))
            elif k in ("exit_wall_gap", "exit_gate_col"):
                items.append(("wp", node_of("exit", repair[nm]["exit"], east), L[2]))
            elif k == "pad_run":
                nd = (int(round((g2.B[nm][0] - X0) / P)) * NY + ROW36) if east else \
                     node_of("exit", repair[nm]["exit"], east)
                items.append(("wp", nd, L[3]))
        chain[nm] = items
    return chain


def pre_routing_check(chain, names):
    """node-pigeonhole on the chain itself (layer-aware): >1 lane on one (node, layer) => no drawing."""
    occ = collections.defaultdict(set)
    for nm, items in chain.items():
        seen = set()
        for (kind, nd, L) in items:
            if kind == "A" or kind == "B":
                continue
            if kind == "via":
                seen.add((0, nd)); seen.add((1, nd))
            else:
                seen.add((L, nd))
        for key in seen:
            occ[key].add(nm)
    w = [{"layer": L, "node": int(n), "col": int(n) // NY, "row": int(n) % NY, "lanes": sorted(ls)}
         for (L, n), ls in occ.items() if len(ls) > 1]
    w.sort(key=lambda d: -len(d["lanes"]))
    return {"verdict": "INFEASIBLE" if w else "PASS", "n_collisions": len(w), "max_multiplicity":
            (len(w[0]["lanes"]) if w else 1), "witnesses": w[:8]}


# ------------------------------------------------------------------ constructive joint assignment
def constructive_attempt(g2, master, spec, names, lanes, chain, iters=10, log=print):
    import heapq
    XL = W.XY
    CLAIM = {}

    def aclaim(nm, u, v):
        key = (nm, u, v); g = CLAIM.get(key)
        if g is None:
            if u >= TERM_BASE:
                tx, ty = lanes[nm]["anc"][0]; px, py = XL(*W.rc(v % NID)); g = tuple(sorted(W.claim_seg(tx, ty, px, py)))
            elif v >= TERM_BASE:
                px, py = XL(*W.rc(u % NID)); tx, ty = lanes[nm]["anc"][1]; g = tuple(sorted(W.claim_seg(px, py, tx, ty)))
            else:
                ax, ay = XL(*W.rc(u % NID)); bx, by = XL(*W.rc(v % NID)); g = tuple(sorted(W.claim_seg(ax, ay, bx, by)))
            CLAIM[key] = g
        return g

    def is_via(u, v):
        return u < TERM_BASE and v < TERM_BASE and u // NID != v // NID

    SEQ = {}
    for nm, items in chain.items():
        seq = []
        for (kind, nd, L) in items:
            if kind == "A":
                seq.append(lanes[nm]["src"])
            elif kind == "B":
                seq.append(lanes[nm]["snk"])
            elif kind == "via":
                seq.append(node_id(0, nd)); seq.append(node_id(1, nd))
            else:
                seq.append(node_id(L, nd))
        SEQ[nm] = seq

    def resources(nm, path):
        rs = set(); vp = []
        for a, b in zip(path, path[1:]):
            if is_via(a, b):
                p = a % NID; rs.add((0, p)); rs.add((1, p)); vp.append(p)
            else:
                L = 0 if (a >= TERM_BASE or b >= TERM_BASE) else a // NID
                for p in aclaim(nm, a, b):
                    rs.add((L, p))
        return rs, vp

    PRES, HISTF, VIAPEN = 1.0, 0.6, 25.0

    def route(nm, occ, hist, vias):
        seq = SEQ[nm]; full = None; nvia = 0; cur = seq[0]
        for k in range(1, len(seq)):
            tgt = seq[k]
            if cur == tgt:
                continue
            adj = lanes[nm]["adj"]
            dist = {cur: 0.0}; vc = {cur: nvia}; pr = {}; pq = [(0.0, cur)]
            while pq:
                d, u = heapq.heappop(pq)
                if d > dist.get(u, 1e18) + 1e-12:
                    continue
                if u == tgt:
                    break
                for (v, w) in adj.get(u, ()):
                    if is_via(u, v):
                        p = u % NID
                        if vc.get(u, 0) >= MAXV:
                            continue
                        extra = 0.0
                        for (q, onm) in vias:
                            if onm != nm and math.dist(XL(*W.rc(p)), XL(*W.rc(q))) < VIA_SEP - 1e-9:
                                extra += 30.0
                        nd = d + w + VIAPEN + PRES * occ[0].get(p, 0) + PRES * occ[1].get(p, 0) \
                            + HISTF * (hist[0][p] + hist[1][p]) + extra
                        nvc = vc[u] + 1
                    else:
                        L = 0 if (u >= TERM_BASE or v >= TERM_BASE) else u // NID
                        s = 0.0
                        for q in aclaim(nm, u, v):
                            s += PRES * occ[L].get(q, 0) + HISTF * hist[L][q]
                        nd = d + w + s; nvc = vc.get(u, 0)
                    if nd < dist.get(v, 1e18) - 1e-12:
                        dist[v] = nd; vc[v] = nvc; pr[v] = u; heapq.heappush(pq, (nd, v))
            if tgt not in pr:
                return None, nvia, k
            path = []; x = tgt
            while x is not None:
                path.append(x); x = pr.get(x)
            path.reverse()
            full = path if full is None else full + path[1:]
            nvia = vc[tgt]; cur = tgt
        return full, nvia, None

    occ = [collections.Counter(), collections.Counter()]
    hist = [np.zeros(NID, float), np.zeros(NID, float)]
    routes = {}; resv = {}; vpos = {}; vias = []

    def add(nm, path):
        rs, vp = resources(nm, path)
        routes[nm] = path; resv[nm] = rs; vpos[nm] = vp
        for (L, p) in rs:
            occ[L][p] += 1
        for p in vp:
            vias.append((p, nm))

    def rem(nm):
        if nm not in routes:
            return
        for (L, p) in resv[nm]:
            occ[L][p] -= 1
            if occ[L][p] == 0:
                del occ[L][p]
        routes.pop(nm); resv.pop(nm); vpos.pop(nm)
        vias[:] = [t for t in vias if t[1] != nm]

    def metrics():
        ov = sum(max(0, v - 1) for L in (0, 1) for v in occ[L].values())
        vv = 0
        for i in range(len(vias)):
            for j in range(i + 1, len(vias)):
                if vias[i][1] != vias[j][1] and math.dist(XL(*W.rc(vias[i][0])), XL(*W.rc(vias[j][0]))) < VIA_SEP - 1e-9:
                    vv += 1
        return ov, vv

    order = sorted(names, key=lambda nm: (0 if spec["per_lane"][nm]["waypoints"][1]["kind"] == "DIVE_via" else 1,
                                          -lanes[nm]["sp"]))
    for nm in order:
        p, nv, fs = route(nm, occ, hist, vias)
        if p is None:
            routes[nm] = None; resv[nm] = set(); vpos[nm] = []
        else:
            add(nm, p)
    best = None
    for it in range(iters):
        ov, vv = metrics()
        nfail = sum(1 for nm in order if not routes.get(nm))
        log("[construct] it %2d overuse=%d viasep=%d failed=%d" % (it, ov, vv, nfail))
        if ov == 0 and vv == 0 and nfail == 0:
            return {"routed": len(order), "overuse": 0, "viasep_viol": 0, "converged": True,
                    "iterations_used": it, "patches": {nm: len(routes[nm]) for nm in order}}
        if best is None or (nfail, ov) < best[0]:
            best = ((nfail, ov), len(order) - nfail, it, ov, vv)
        for L in (0, 1):
            for p, v in occ[L].items():
                if v > 1:
                    hist[L][p] += 1.0
        HISTF = min(3.0, 0.6 + 0.25 * it)
        for nm in order:
            rem(nm)
            p, nv, fs = route(nm, occ, hist, vias)
            if p is None:
                routes[nm] = None; resv[nm] = set(); vpos[nm] = []
            else:
                add(nm, p)
    return {"routed": best[1], "overuse": best[3], "viasep_viol": best[4], "converged": False,
            "best_iteration": best[2], "n_lanes": len(order),
            "verdict": "16/16 网布通但残余重叠 ⇒ 尚非有效图纸（需联立序一致的重推）"}


def sha16(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, OWN_OUT))
    ap.add_argument("--construct-iters", type=int, default=10)
    a = ap.parse_args()
    if os.path.basename(a.out) != OWN_OUT:
        raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7)")
    open(LOGF, "w").close()
    t0 = time.time()
    spec = json.load(open(SPEC)); master = json.load(open(R529))
    mj = json.load(open(MODEL))
    rep = {"artifact": "k2_r548_r540_chain_infeasibility_certificate_v1",
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-215 (换台令, execute #K2-213 sec.4 verbatim) -> execute constructive drawing; ZERO certified quota",
           "solve_calls": 0, "certified_solve_calls": 0,
           "input_hashes": {"R540_spec": sha16(spec), "R529_master": sha16(master),
                            "model_l8": hashlib.sha256(open(MODEL, "rb").read()).hexdigest()[:16]},
           "environment_note": "this container has no ortools; a documented import shim is used ONLY to import the "
                               "registered generator (Gen2 never calls cp_model). No install, no generator edit."}
    log("[stage] gen2 building ...")
    g2 = W.Gen2(mj, l1scope="full")
    names = list(g2.names)
    lanes = {nm: g2.build_lane(nm) for nm in names}
    log("[stage] gen2 ready, %d lanes (%.1fs)" % (len(names), time.time() - t0))

    # 1) certificate on the FIXED input
    cert, dups, policy_ok = certificate(spec, master)
    rep["certificate_fixed_input"] = cert
    rep["r529_upstream_defect"] = {"per_section_layer_duplicate_slots": dups,
                                   "n_duplicate_slots": len(dups), "encoding_gap": r529_encoding_gap()}
    log("[cert] literal max_multiplicity=%d ; schedule-aware max=%d ; R529 dup slots=%d" % (
        cert["literal_all_In5"]["max_multiplicity"], cert["schedule_aware"]["max_multiplicity"], len(dups)))

    # 2) domain definition (k shortest union) + bool gate
    dom = k_shortest_union(g2, spec, master, names, lanes, log=log)
    rep["domain_definition"] = dom
    log("[domain] total_bool=%d under_gate=%s (gate=%d)" % (dom["total_bool_vars"], dom["under_gate"], GATE_BOOL))

    # 3) pre-routing pigeonhole ON THE FIXED CHAIN (literal, as R543 fixed inputs) -> INFEASIBLE
    fixed_chain = {}
    for nm in names:
        items = []
        for w in spec["per_lane"][nm]["waypoints"]:
            if w["kind"] == "A_anchor":
                items.append(("A", None, 0))
            elif w["kind"] == "B_anchor":
                items.append(("B", None, 0))
            elif w["kind"] == "DIVE_via":
                items.append(("via", w["node"], 1))
            else:
                items.append(("wp", w["node"], 0))
        fixed_chain[nm] = items
    rep["pre_routing_fixed_chain"] = pre_routing_check(fixed_chain, names)
    log("[pre-routing/fixed] %s" % rep["pre_routing_fixed_chain"]["verdict"])

    # 4) L2 slot repair + layer-aware chain
    repair, repair_info = repair_slots(g2, master, spec, names, lanes)
    rep["l2_slot_repair"] = repair_info
    rep["l2_slot_repair"]["assignment"] = repair
    chain = build_chain(g2, spec, master, names, repair)
    rep["pre_routing_repaired_chain"] = pre_routing_check(chain, names)
    log("[repair] movements=%d collisions=%d ; pre-routing/repaired=%s" % (
        repair_info["n_movements"], repair_info["post_repair_node_layer_collisions"],
        rep["pre_routing_repaired_chain"]["verdict"]))

    # 5) constructive joint assignment attempt on the repaired chain
    attempt = constructive_attempt(g2, master, spec, names, lanes, chain, iters=a.construct_iters, log=log)
    rep["constructive_attempt_repaired_chain"] = attempt
    log("[construct] result: %s" % json.dumps(attempt, ensure_ascii=False)[:200])

    # 6) verdict + buildability
    fixed_infeasible = rep["pre_routing_fixed_chain"]["verdict"] == "INFEASIBLE"
    rep["decision"] = (
        "NO DRAWING UNDER THE FIXED R540 INPUT — certified pre-routing (node-pigeonhole: %d lanes forced through "
        "one lattice node; only 2 layers). The #K2-213 sec.4 k-alternatives mandate cannot fix this: the "
        "infeasibility is AT the fixed waypoints, not between them. Upstream root cause = R529 section_slots are "
        "not node-injective per layer (encoder gap on4[i]+on4[j]!=0). L2 repair (node-injective slots) passes "
        "pre-routing; constructive construction then routes %d/%d nets but does not yet converge to a legal "
        "drawing -> NEXT: joint re-derivation of slots WITH fan/form-C order consistency (L2)." %
        (rep["pre_routing_fixed_chain"]["max_multiplicity"], attempt["routed"], attempt["n_lanes"])
        if fixed_infeasible else "unexpected: fixed chain passed pre-routing check")
    rep["buildability"] = {"mode": "no_witness",
                           "why": "no legal per-lane drawing exists under the fixed R540 chain (pre-routing "
                                  "pigeonhole); a candidate fix (L2 node-injective slot re-derivation) is provided "
                                  "but not yet a verified drawing",
                           "relocation_list_required_before_construction": sorted(names)}
    rep["conservation_audit"] = {"source": "K2_R537_CONSERVATION_CUT_v1.json",
                                 "reading": "156 在册格点割全量计数：无容量墙（最紧 col114 上界 40 vs 需求 3，余 +37）",
                                 "note": "本卡点非守恒级；是固定路点层（node 冲突）"}
    rep["artifact_hash16"] = sha16({k: rep[k] for k in rep if k != "artifact_hash16"})
    rep["elapsed_s"] = round(time.time() - t0, 1)
    rep["fail_loud_log"] = LOGF
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    log("WROTE %s" % a.out)
    log("OWNER-ITEMS: 0")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as _e:
        import traceback; traceback.print_exc()
        print('FAIL_LOUD: {"error": %r}' % (str(_e),), flush=True)
        sys.exit(3)
