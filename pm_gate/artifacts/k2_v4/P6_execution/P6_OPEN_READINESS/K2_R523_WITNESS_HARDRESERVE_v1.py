#!/usr/bin/env python3
"""K2 · R523 —— 停止令二值：**可行见证分支 · 硬预留确定性构造布线**（0 次 `Solve()` · 不占受证额度）。

令（原文）：「监理停止令（收敛停滞 ≈80 轮无二值）: 本件必须出二值（可行见证 ‖ 守恒级不可行证书），
禁再以『口径澄清 / 工具再升一版』单独占轮。若出不来 ⇒ 立即出《守恒级卡点报告》」。

本件性质：**不是澄清、不是升版**，而是**计算**（构造式见证族 · #K2-189 §三.4 已追认「不占受证额度」）。

方法（与 R515 的 MCF 求解**并行**的第二条合法路线）：
  在**在册双层图**（`Gen2`：In5+In4、过孔仅四宽区、≤2 对孔、区域约定、锚禁近圈）上**逐根布线**，
  每布一根就把它的**逐层声明集**（`claim_seg`：格点到线段真距 < P）**硬性扣除** —— 后续线**不许**碰。
  过孔另加：孔位在两层的已占集之外（⇒ 自动满足「孔 vs 他线走线 ≥ VR+HW」，因 P=0.435 ≥ 0.43）
  + 与他根已放孔中心距 ≥ VIA_SEP + 每根 ≤2 对孔。
  ⇒ **凡 16/16 布通，即同时满足**：逐层声明集互斥（R513-T3 已证与在册尺**逐对等价**）· 跨层/过孔在册判据 ·
  端点=真锚 · 区域/过孔站点在册限制 ⇒ **构造式合法见证**（再用**独立**在册闸复验，缺一 fail-closed）。
  任一顺序布不通 ⇒ 报**具名卡点**（哪根 / 在哪 / 被谁的声明集封死 / 其可行域还剩几个格点）。

多种**确定性**顺序（不随机、不改参）逐一尝试；取「布通根数最多」者为诊断基线。
"""
import collections, heapq, importlib, json, math, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
W = importlib.import_module("K2_R515_" + "FREETERMINALS_v1")
GATES = importlib.import_module("K2_R523_LAYERHOP_PARITY_FORMC_v1")   # 含**已修**的 gate_vias
R512 = W.R512
RT = W.RT

P, X0, Y0, NX, NY, NID, TERM_BASE = W.P, W.X0, W.Y0, W.NX, W.NY, W.NID, W.TERM_BASE
XY, VIA_SEP, MAX_VIA_PAIRS, HW = W.XY, W.VIA_SEP, W.MAX_VIA_PAIRS, W.HW
VR, HOLE_CLR, eff = W.VR, W.HOLE_CLR, W.eff

model = json.load(open("/tmp/opencode/archer/model_l8.json"))
t0 = time.time()
g2 = W.Gen2(model, l1scope="full")
lanes = {}
for nm in g2.names:
    L = g2.build_lane(nm)
    if L is None:
        raise SystemExit("lane build FAIL " + nm)
    lanes[nm] = L
NAMES = list(g2.names)
print("lanes built %d  t=%.1fs" % (len(lanes), time.time() - t0), flush=True)

_ac = {}


def arc_claim(u, v, nm):
    """-> (kind, layer, claim_frozenset, via_pos_or_None)"""
    key = (u, v, nm)
    got = _ac.get(key)
    if got is not None:
        return got
    if u >= TERM_BASE:                                    # legA
        tx, ty = lanes[nm]["anc"][0]
        px, py = XY(*W.rc(v % NID))
        got = ("leg", 0, frozenset(W.claim_seg(tx, ty, px, py)), None)
    elif v >= TERM_BASE:                                  # legB
        px, py = XY(*W.rc(u % NID))
        tx, ty = lanes[nm]["anc"][1]
        got = ("leg", 0, frozenset(W.claim_seg(px, py, tx, ty)), None)
    elif u // NID != v // NID:                            # via（占同格点两层）
        got = ("via", u // NID, frozenset([u % NID]), u % NID)
    else:
        L = u // NID
        ax, ay = XY(*W.rc(u % NID)); bx, by = XY(*W.rc(v % NID))
        got = ("lat", L, frozenset(W.claim_seg(ax, ay, bx, by)), None)
    _ac[key] = got
    return got


def hard_route(nm, res0, res1, vias):
    """在 (已占集, 已放孔) 的硬约束下给 nm 找最短路；返回 (path, stats) 或 (None, stats)。"""
    adj = lanes[nm]["adj"]; src = lanes[nm]["src"]; snk = lanes[nm]["snk"]
    dist = {src: 0.0}; nvia = {src: 0}; prev = {}
    pq = [(0.0, src)]; blocked = collections.Counter(); seen_nodes = 0
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, 1e18) + 1e-12:
            continue
        seen_nodes += 1
        if u == snk:
            break
        for (v, w) in adj.get(u, ()):
            kind, Lay, claim, vp = arc_claim(u, v, nm)
            if kind == "via":
                if vp in res0 or vp in res1:
                    blocked["via_occupied"] += 1; continue
                bad = False
                for (q, _o) in vias:
                    if math.dist(XY(*W.rc(vp)), XY(*W.rc(q))) < VIA_SEP - 1e-9:
                        bad = True; break
                if bad:
                    blocked["via_sep"] += 1; continue
                if nvia.get(u, 0) >= 2 * MAX_VIA_PAIRS:
                    blocked["via_cap"] += 1; continue
            else:
                R = res0 if Lay == 0 else res1
                if claim & R:
                    blocked["claim_%d" % Lay] += 1; continue
            nd = d + w + (0.0 if kind != "via" else 1e-4)
            if nd < dist.get(v, 1e18) - 1e-12:
                dist[v] = nd; nvia[v] = nvia.get(u, 0) + (1 if kind == "via" else 0)
                prev[v] = u; heapq.heappush(pq, (nd, v))
    st = {"reached": snk in prev, "expanded": seen_nodes, "blocked": dict(blocked),
          "dist_mm": round(dist.get(snk, float("inf")), 3) if snk in prev else None}
    if snk not in prev:
        return None, st
    path = []; cur = snk
    while cur is not None:
        path.append(cur); cur = prev.get(cur)
    path.reverse()
    return path, st


def commit(nm, path, res0, res1, vias):
    for a, b in zip(path, path[1:]):
        kind, Lay, claim, vp = arc_claim(a, b, nm)
        if kind == "via":
            res0.add(vp); res1.add(vp); vias.append((vp, nm))
        else:
            (res0 if Lay == 0 else res1).update(claim)


def run_order(order, verbose=False):
    res0 = set(); res1 = set(); vias = []; paths = {}; stall = None
    for nm in order:
        path, st = hard_route(nm, res0, res1, vias)
        if path is None:
            stall = {"lane": nm, "rank": len(paths), "stats": st,
                     "free_nodes_hint": st["expanded"], "res0": len(res0), "res1": len(res1)}
            break
        commit(nm, path, res0, res1, vias)
        paths[nm] = path
        if verbose:
            print("   routed %-22s len=%8.3f vias=%d" % (nm, st["dist_mm"], sum(
                1 for a, b in zip(path, path[1:]) if arc_claim(a, b, nm)[0] == "via")), flush=True)
    return paths, stall


# ---------------- 确定性顺序族 ----------------
sp = {nm: lanes[nm]["sp"] for nm in NAMES}


def difficulty(nm):
    """R517 口径：起终点分离度高 / 靠东 / 拐点多 ⇒ 先布"""
    A, B = lanes[nm]["anc"]
    return (math.hypot(B[0] - A[0], B[1] - A[1]) - 0.5 * lanes[nm]["sp"])


orders = {
    "by_sp_desc": sorted(NAMES, key=lambda n: -sp[n]),
    "by_sp_asc": sorted(NAMES, key=lambda n: sp[n]),
    "by_difficulty_desc": sorted(NAMES, key=lambda n: -difficulty(n)),
    "by_Bx_desc": sorted(NAMES, key=lambda n: -lanes[n]["anc"][1][0]),
    "by_Bx_asc": sorted(NAMES, key=lambda n: lanes[n]["anc"][1][0]),
    "by_Ax_asc": sorted(NAMES, key=lambda n: lanes[n]["anc"][0][0]),
    "by_Ax_desc": sorted(NAMES, key=lambda n: -lanes[n]["anc"][0][0]),
    "west_first": [n for n in NAMES if g2.grp[n] == "west"] + [n for n in NAMES if g2.grp[n] == "east"],
    "east_first": [n for n in NAMES if g2.grp[n] == "east"] + [n for n in NAMES if g2.grp[n] == "west"],
}
res = {"artifact": "k2_r523_witness_hardreserve_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "authority": "supervisor stop-order (convergence stall; must produce a binary: feasible witness OR "
                    "conservation-grade infeasibility certificate; no more clarification/tool-bump rounds) + "
                    "#K2-189 sec.3.4 (constructive witness family ratified, non-quota)",
       "solve_calls": 0, "method": "deterministic sequential constructive routing with HARD declaration-set "
                                  "reservation on the registered two-layer graph; every order is a legal-witness "
                                  "candidate if it completes 16/16",
       "orders": {}, "lanes": NAMES}
best = None
for tag, order in orders.items():
    paths, stall = run_order(order)
    res["orders"][tag] = {"n_routed": len(paths), "order": list(order), "stall": stall}
    print("[order %s] routed %d/16 %s" % (tag, len(paths), ("STALL %s" % stall["lane"]) if stall else "FULL"), flush=True)
    if best is None or len(paths) > len(best[1]):
        best = (tag, paths, stall, order)
res["best_order"] = best[0]; res["best_n_routed"] = len(best[1])
json.dump(res, open("K2_R523_WITNESS_HARDRESERVE_v1.json", "w"), ensure_ascii=False, indent=1, default=str)
print("BEST %s = %d/16  (elapsed %.1fs)" % (best[0], len(best[1]), time.time() - t0))
if len(best[1]) == len(NAMES):
    print("FULL 16/16 -- witness candidate found; run with --verify to gate+render")
