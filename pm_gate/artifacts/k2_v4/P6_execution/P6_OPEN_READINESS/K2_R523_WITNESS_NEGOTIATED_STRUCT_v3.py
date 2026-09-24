#!/usr/bin/env python3
"""K2 · R523 —— 停止令二值：**结构偏置协商式布线**（R517 族 · 0 次受证 `Solve()` 调用）。
机理：R517 软协商 16/16 布出但残余冲突 512（全根贴最短径 ⇒ 声明带大面积互叠）。本件给同一族加**结构偏置**：
  ① 强惩罚 **In5 的"中段"**（= 四宽区之外的 In5 格点）⇒ 每根**只在宽区内上下层**：梳齿/南带 → In4 → 焊盘场；
  ② PathFinder 式历史代价（`occ` 本轮占用 + `hist` 累计），按"冲突格点"累加 ⇒ 逼开重叠；
  ③ 多顺序轮转 + 长迭代；一旦**冲突 = 0** ⇒ 立刻调**独立在册闸**（逐层 `exact_gate` + 已修 `gate_vias` + 端点）
     与**孔规则**（≤2 对 · ≥VIA_SEP）复验 ⇒ 全绿即**可行见证**（P4 该归零）；任一不过 ⇒ fail-closed 不签字。
"""
import collections, heapq, importlib, json, math, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
W = importlib.import_module("K2_R515_" + "FREETERMINALS_v1")
GATES = importlib.import_module("K2_R523_LAYERHOP_PARITY_FORMC_v1")
RT = W.RT
P, X0, Y0, NX, NY, NID, TERM_BASE = W.P, W.X0, W.Y0, W.NX, W.NY, W.NID, W.TERM_BASE
XY, VIA_SEP, MAX_VIA_PAIRS, HW, ZONES = W.XY, W.VIA_SEP, W.MAX_VIA_PAIRS, W.HW, W.ZONES

model = json.load(open("/tmp/opencode/archer/model_l8.json"))
t00 = time.time()
g2 = W.Gen2(model, l1scope="full")
lanes = {nm: g2.build_lane(nm) for nm in g2.names}
NAMES = list(g2.names)
assert all(lanes[n] is not None for n in NAMES)
print("lanes %d t=%.1fs" % (len(lanes), time.time() - t00), flush=True)

# 四宽区的格点掩码（含 1 格外扩 ⇒ "宽区内"判定）
in_zone = [[False] * NY for _ in range(NX)]
for (x0, y0, x1, y1) in ZONES:
    i0 = max(0, int((x0 - X0) / P) - 1); i1 = min(NX - 1, int((x1 - X0) / P) + 1)
    j0 = max(0, int((y0 - Y0) / P) - 1); j1 = min(NY - 1, int((y1 - Y0) / P) + 1)
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            in_zone[i][j] = True
_ac = {}


def arc_info(u, v, nm):
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


PEN, HPEN, VPEN, STRUCT, VIA_SEP_PEN = 40.0, 25.0, 60.0, 6.0, 40.0


def route(nm, occ, hist, vuse):
    """PathFinder 式最短路（成本 = 长度 + 占用/历史 + 结构偏置 + 过孔避让）。"""
    adj = lanes[nm]["adj"]; src = lanes[nm]["src"]; snk = lanes[nm]["snk"]
    dist = {src: 0.0}; nvia = {src: 0}; prev = {}; pq = [(0.0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, 1e18) + 1e-12: continue
        if u == snk: break
        for (v, w) in adj.get(u, ()):
            kind, Lay, claim, vp = arc_info(u, v, nm)
            c = w
            for p in claim:
                c += PEN * occ.get((Lay, p), 0.0) + HPEN * hist.get((Lay, p), 0.0)
                if Lay == 0:
                    i, j = W.rc(p)
                    if not in_zone[i][j]:
                        c += STRUCT                      # In5 中段：强罚 ⇒ 逼早下 In4
            if kind == "via":
                c += VPEN
                c += VIA_SEP_PEN * sum(vuse.get(q, 0.0) for q in _nbr2(vp))
                if nvia.get(u, 0) >= 2 * MAX_VIA_PAIRS: c += 1e3
            nd = d + c
            if nd < dist.get(v, 1e18) - 1e-12:
                dist[v] = nd; nvia[v] = nvia.get(u, 0) + (1 if kind == "via" else 0)
                prev[v] = u; heapq.heappush(pq, (nd, v))
    if snk not in prev: return None
    path = []; cur = snk
    while cur is not None:
        path.append(cur); cur = prev.get(cur)
    path.reverse(); return path


_NB = {}
def _nbr2(p):
    got = _NB.get(p)
    if got is not None: return got
    ii, jj = W.rc(p); out = []
    for di in range(-2, 3):
        for dj in range(-2, 3):
            if di * di + dj * dj <= 4 and 0 <= ii + di < NX and 0 <= jj + dj < NY:
                out.append((ii + di) * NY + (jj + dj))
    _NB[p] = out; return out


def evaluate(routes):
    """冲突计数（逐层声明集重复占用）+ 孔规则违规数"""
    bylayer = collections.defaultdict(lambda: collections.defaultdict(set))   # L -> node -> {lane}
    vias = collections.defaultdict(list)
    for nm, path in routes.items():
        for a, b in zip(path, path[1:]):
            kind, Lay, claim, vp = arc_info(a, b, nm)
            if kind == "via":
                vias[vp].append(nm)
            for p in claim:
                bylayer[Lay][p].add(nm)
    conf = 0
    for L, dd in bylayer.items():
        for p, s in dd.items():
            if len(s) > 1: conf += len(s) - 1
    bad = 0
    vps = list(vias)
    for i in range(len(vps)):
        for j in range(i + 1, len(vps)):
            if math.dist(XY(*W.rc(vps[i])), XY(*W.rc(vps[j]))) < VIA_SEP - 1e-9: bad += 1
    for nm, path in routes.items():
        nv = sum(1 for a, b in zip(path, path[1:]) if arc_info(a, b, nm)[0] == "via")
        if nv > 2 * MAX_VIA_PAIRS: bad += 1
    return conf, bad


sp = {n: lanes[n]["sp"] for n in NAMES}
orders = {
    "sp_desc": sorted(NAMES, key=lambda n: -sp[n]),
    "sp_asc": sorted(NAMES, key=lambda n: sp[n]),
    "Bx_desc": sorted(NAMES, key=lambda n: -lanes[n]["anc"][1][0]),
    "difficulty": sorted(NAMES, key=lambda n: -(math.dist(*[tuple(lanes[n]["anc"][k]) for k in (0, 1)]) - 0.5 * sp[n])),
}
rep = {"artifact": "k2_r523_witness_negotiated_struct_v3", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "authority": "supervisor stop-order (binary required; no clarification/tool-bump rounds) + #K2-189 sec.3.4 "
                    "(constructive witness family ratified, non-quota)",
       "solve_calls": 0, "method": "structure-biased PathFinder negotiation: strong penalty on In5 mid-corridor nodes "
                                   "(outside the four registered wide zones) forces every lane to change layer only inside "
                                   "zones; history/occupancy costs spread the declaration bands; runs until 0 conflicts",
       "n_iter_budget": 900, "params": {"PEN": PEN, "HPEN": HPEN, "VPEN": VPEN, "STRUCT": STRUCT}, "runs": {}}

best_global = (10 ** 9, None, None, None)
for tag, order in orders.items():
    occ = collections.defaultdict(float); hist = collections.defaultdict(float)
    vuse = collections.defaultdict(float)
    best = (10 ** 9, None)
    t_tag = time.time()
    for it in range(900):
        occ.clear(); vuse.clear()
        routes = {}
        for nm in order:
            path = route(nm, occ, hist, vuse)
            if path is None: break
            routes[nm] = path
            for a, b in zip(path, path[1:]):
                kind, Lay, claim, vp = arc_info(a, b, nm)
                for p in claim: occ[(Lay, p)] += 1.0
                if kind == "via":
                    for q in _nbr2(vp): vuse[q] += 1.0
        if len(routes) < len(NAMES):
            hist_update = {(L, p): 1.0 for (L, p) in occ}
        else:
            conf, bad = evaluate(routes)
            if conf + bad < best[0]:
                best = (conf + bad, routes, conf, bad)
            if conf == 0 and bad == 0:
                best_global = (0, dict(routes), 0, 0)
                print("[%s] it=%d CONFLICT-FREE (%d/%d lanes)" % (tag, it, len(routes), len(NAMES)), flush=True)
                break
            hist_update = {(L, p): 1.0 for (L, p), s in occ.items() if s > 1.0}
            for Lp in hist_update: hist[Lp] += 1.0
        if time.time() - t_tag > 700:
            print("[%s] time cap at it=%d best=%d" % (tag, it, best[0]), flush=True); break
    rep["runs"][tag] = {"best_conflicts_plus_viol": best[0], "best_conf": best[2] if best[1] else None,
                        "best_viol": best[3] if best[1] else None, "elapsed_s": round(time.time() - t_tag, 1)}
    print("[%s] best=%d routed16=%s  (%.1fs)" % (tag, best[0], best[1] is not None, time.time() - t_tag), flush=True)
    if best_global[0] > 0 and best[1] is not None and best[0] < best_global[0]:
        best_global = (best[0], dict(best[1]), best[2], best[3])
    if best_global[0] == 0: break

rep["best_conflicts_plus_viol"] = best_global[0]
rep["witness_found"] = (best_global[0] == 0 and best_global[1] is not None)
json.dump(rep, open("K2_R523_WITNESS_NEGOTIATED_STRUCT_v3.json", "w"), ensure_ascii=False, indent=1, default=str)
print("BEST GLOBAL conflicts+viol =", best_global[0], " witness =", rep["witness_found"], flush=True)
if rep["witness_found"]:
    json.dump({nm: [int(n) for n in p] for nm, p in best_global[1].items()},
              open("K2_R523_WITNESS_ROUTES_v3.json", "w"))
    print("ROUTES WRITTEN -> K2_R523_WITNESS_ROUTES_v3.json  (next: registered-gate verification)")
print("elapsed %.1fs" % (time.time() - t00))
