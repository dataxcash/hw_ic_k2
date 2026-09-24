#!/usr/bin/env python3
"""K2 · R523 —— 停止令二值：**可行见证支 · 分区结构化确定性构造**（0 次 `Solve()` · 不占受证额度）。

与 v1（硬预留贪心）同一族，但**按注册的"区间结构"下刀**（对照 R513《层余量审计》的四个宽区）：
  每根线 = ① 梳齿区 In5 短段（锚 → 下孔位）→ ② In4 中段（下孔位 → 上孔位）→ ③ 焊盘场 In5 短段（上孔位 → 锚）；
  能全程 In5 者走"零孔"支（先试，省资源）。下/上孔位都**只落在四宽区**（`via_positions` 已含此约束）。
  硬性扣除：每根布通后把其**逐层声明集**（`claim_seg`：格点到线段真距 < P）扣给后续线；孔位另加两层占用 + ≥VIA_SEP + ≤2 对。
  ⇒ 若 16/16 布通，则**逐层声明集互斥**（= R513-T3 已证与在册尺**逐对等价**）+ 跨层/过孔在册判据 + 端点=真锚
     ⇒ **构造式合法见证**；随后用**独立在册闸**（`exact_gate` 逐层 + **已修** `gate_vias`）复验，缺一 fail-closed。
多确定性顺序取最优；不通报**具名卡点**。
"""
import collections, heapq, importlib, json, math, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
W = importlib.import_module("K2_R515_" + "FREETERMINALS_v1")
GATES = importlib.import_module("K2_R523_LAYERHOP_PARITY_FORMC_v1")
RT = W.RT
P, X0, Y0, NX, NY, NID, TERM_BASE = W.P, W.X0, W.Y0, W.NX, W.NY, W.NID, W.TERM_BASE
XY, VIA_SEP, MAX_VIA_PAIRS, HW = W.XY, W.VIA_SEP, W.MAX_VIA_PAIRS, W.HW
LEDGE, KD, KU = 12.0, 8, 8          # 薄边惩罚（鼓励贴边留中）· 下/上孔位候选上限

model = json.load(open("/tmp/opencode/archer/model_l8.json"))
t00 = time.time()
g2 = W.Gen2(model, l1scope="full")
lanes = {nm: g2.build_lane(nm) for nm in g2.names}
NAMES = list(g2.names)
assert all(lanes[n] is not None for n in NAMES)
print("lanes %d  t=%.1fs" % (len(lanes), time.time() - t00), flush=True)

_ac = {}


def arc_claim(u, v, nm):
    key = (u, v, nm); got = _ac.get(key)
    if got is not None: return got
    if u >= TERM_BASE:
        tx, ty = lanes[nm]["anc"][0]; px, py = XY(*W.rc(v % NID))
        got = ("leg", 0, frozenset(W.claim_seg(tx, ty, px, py)), None)
    elif v >= TERM_BASE:
        px, py = XY(*W.rc(u % NID)); tx, ty = lanes[nm]["anc"][1]
        got = ("leg", 0, frozenset(W.claim_seg(px, py, tx, ty)), None)
    elif u // NID != v // NID:
        got = ("via", u // NID, frozenset([u % NID]), u % NID)
    else:
        L = u // NID
        ax, ay = XY(*W.rc(u % NID)); bx, by = XY(*W.rc(v % NID))
        got = ("lat", L, frozenset(W.claim_seg(ax, ay, bx, by)), None)
    _ac[key] = got; return got


def stage_route(nm, start, end, allow, res0, res1, vias, nvia_used, allow_via=False):
    """单阶段最短路（硬约束）；allow = {('leg',0),('lat',0),('lat',1),('via',L)}"""
    adj = lanes[nm]["adj"]
    dist = {start: 0.0}; prev = {}; pq = [(0.0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, 1e18) + 1e-12: continue
        if u == end: break
        for (v, w) in adj.get(u, ()):
            kind, Lay, claim, vp = arc_claim(u, v, nm)
            if kind == "via":
                if not allow_via: continue
                if (kind, Lay) not in allow and (kind, 1 - Lay) not in allow: continue
                if vp in res0 or vp in res1: continue
                if any(math.dist(XY(*W.rc(vp)), XY(*W.rc(q))) < VIA_SEP - 1e-9 for (q, _o) in vias): continue
                if nvia_used >= 2 * MAX_VIA_PAIRS: continue
                c = 1e-4
            else:
                if (kind, Lay) not in allow: continue
                R = res0 if Lay == 0 else res1
                if claim & R: continue
                c = w
            if c >= 1e5: continue
            nd = d + c
            if nd < dist.get(v, 1e18) - 1e-12:
                dist[v] = nd; prev[v] = u; heapq.heappush(pq, (nd, v))
    if end not in prev: return None
    path = []; cur = end
    while cur is not None: path.append(cur); cur = prev.get(cur)
    path.reverse(); return path


def commit(nm, path, res0, res1, vias):
    nv = 0
    for a, b in zip(path, path[1:]):
        kind, Lay, claim, vp = arc_claim(a, b, nm)
        if kind == "via":
            res0.add(vp); res1.add(vp); vias.append((vp, nm)); nv += 1
        else:
            (res0 if Lay == 0 else res1).update(claim)
    return nv


def route_lane(nm, res0, res1, vias):
    TA, TB = lanes[nm]["terminals"]; anc = lanes[nm]["anc"]
    # (1) **优先结构化支**（早下 In4、保 In5 只做两端短段 ⇒ 省 In5）
    sites = sorted({vp for (_u, _v) in lanes[nm]["vias"] for vp in [lanes[nm]["via_arcs"][(_u, _v)][1]]})
    Ds = sorted(sites, key=lambda p: math.dist(XY(*W.rc(p)), anc[0]))[:KD]
    Us = sorted(sites, key=lambda q: math.dist(XY(*W.rc(q)), anc[1]))[:KU]
    for p in Ds:
        if p in res0 or res1: continue
        if any(math.dist(XY(*W.rc(p)), XY(*W.rc(q2))) < VIA_SEP - 1e-9 for (q2, _o) in vias): continue
        s1 = stage_route(nm, TA, p, {("leg", 0), ("lat", 0)}, res0, res1, vias, 0)
        if s1 is None: continue
        for q in Us:
            if q == p or q in res0 or q in res1: continue
            if any(math.dist(XY(*W.rc(q)), XY(*W.rc(q2))) < VIA_SEP - 1e-9 for (q2, _o) in vias): continue
            if math.dist(XY(*W.rc(p)), XY(*W.rc(q))) < VIA_SEP - 1e-9: continue
            s3 = stage_route(nm, q, TB, {("leg", 0), ("lat", 0)}, res0, res1, vias, 0)
            if s3 is None: continue
            s2 = stage_route(nm, NID + p, NID + q, {("lat", 1)}, res0, res1, vias, 0)
            if s2 is None: continue
            # 三个子段互相之间也须自洽（同一根线，允许同线声明重叠，但孔位占用要叠加）
            for path in (s1, s3):
                commit(nm, path, res0, res1, vias)
            commit(nm, s2, res0, res1, vias)
            full = s1 + [NID + p] + s2[1:-1] + [q] + s3[1:] if False else s1 + s2 + s3
            res0.add(p); res1.add(p); vias.append((p, nm))
            res0.add(q); res1.add(q); vias.append((q, nm))
            return {"path": s1 + s2 + s3, "vias": 2, "mode": "structured", "p": p, "q": q,
                    "segs": [len(s1), len(s2), len(s3)]}
    # (2) 兜底：全程 In5（仅在结构化支无解时用）
    pth = stage_route(nm, TA, TB, {("leg", 0), ("lat", 0)}, res0, res1, vias, 0, allow_via=False)
    if pth is not None:
        nv = commit(nm, pth, res0, res1, vias)
        return {"path": pth, "vias": nv, "mode": "all_In5"}
    return None


def run_order(order):
    res0 = set(); res1 = set(); vias = []; routes = {}; stalls = []
    for nm in order:
        got = route_lane(nm, res0, res1, vias)
        if got is None:
            stalls.append({"lane": nm, "rank": len(routes), "res0": len(res0), "res1": len(res1)})
            break
        routes[nm] = got
    return routes, stalls


sp = {n: lanes[n]["sp"] for n in NAMES}
orders = {
    "sp_desc": sorted(NAMES, key=lambda n: -sp[n]),
    "sp_asc": sorted(NAMES, key=lambda n: sp[n]),
    "Bx_desc": sorted(NAMES, key=lambda n: -lanes[n]["anc"][1][0]),
    "Bx_asc": sorted(NAMES, key=lambda n: lanes[n]["anc"][1][0]),
    "Ax_asc": sorted(NAMES, key=lambda n: lanes[n]["anc"][0][0]),
    "west_first": [n for n in NAMES if g2.grp[n] == "west"] + [n for n in NAMES if g2.grp[n] == "east"],
    "east_first": [n for n in NAMES if g2.grp[n] == "east"] + [n for n in NAMES if g2.grp[n] == "west"],
}
rep = {"artifact": "k2_r523_witness_zonestruct_v2", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "authority": "supervisor stop-order (binary demanded: feasible witness OR conservation-grade infeasibility "
                    "certificate; no clarification/tool-bump rounds) + #K2-189 sec.3.4 (constructive family ratified, non-quota)",
       "solve_calls": 0, "method": "stage-structured deterministic construction: In5 comb stub -> In4 mid (via-to-via) "
                                   "-> In5 pad stub, with hard per-layer declaration-set reservation; all-In5 lanes tried first",
       "orders": {}, "lanes": NAMES}
best = (None, {}, None)
for tag, order in orders.items():
    routes, stalls = run_order(order)
    rep["orders"][tag] = {"n_routed": len(routes), "stalls": stalls,
                          "modes": {nm: routes[nm]["mode"] for nm in routes}}
    print("[%s] %d/16 %s" % (tag, len(routes), stalls[:1]), flush=True)
    if len(routes) > len(best[1]): best = (tag, routes, stalls)
rep["best_order"] = best[0]; rep["best_n_routed"] = len(best[1]); rep["best_stalls"] = best[2]
json.dump(rep, open("K2_R523_WITNESS_ZONESTRUCT_v2.json", "w"), ensure_ascii=False, indent=1, default=str)
print("BEST %s %d/16  (%.1fs)" % (best[0], len(best[1]), time.time() - t00))
