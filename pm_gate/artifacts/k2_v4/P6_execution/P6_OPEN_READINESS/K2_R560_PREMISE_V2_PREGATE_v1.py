#!/usr/bin/env python3
"""K2 · R560 —— 前提 v2（阶梯断面 + 北巴士 + 东列）**前置核验器**（只核不描线 · 新命令）
机核三件（#K2-220 §三.3(b) 的 (i)(ii) 与 (iii) 的静态代理）：
 (i)  域完备：每线声明格（入口/断面/转移）在其在册图上合法；
 (ii) 链连通：每线相邻声明格在在册图上**是弧**；
 (iii)单线可通（静态代理）：声明链逐段为在册弧且无跨线共用（单线时无障碍）。
外加上层互斥：同一层内，两两声明格集合**不相交**（轴向声明线 ⇒ 无重格即无交叉）。
"""
import sys, os, json, collections, hashlib, time, types, importlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
for nm in ("ortools", "ortools.sat", "ortools.sat.python"):
    sys.modules.setdefault(nm, types.ModuleType(nm))
cm = types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self, *a, **k): pass
cm.CpModel = _D; cm.CpSolver = _D
sys.modules["ortools.sat.python.cp_model"] = cm; sys.modules["ortools.sat.python"].cp_model = cm
LOGF = "/tmp/opencode/r560/pregate.log"; os.makedirs(os.path.dirname(LOGF), exist_ok=True)
def log(m): open(LOGF, "a").write(str(m) + "\n"); print(str(m), flush=True)

def main():
    open(LOGF, "w").close()
    M = importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1")
    PREV = M.PREV; PREV.Gen._build_edges = M._build_edges_fixed
    W = M.W; NID, NY, TERM = W.NID, W.NY, W.TERM_BASE
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names)
    master = json.load(open(os.path.join(HERE, "K2_R529_WOVEN_COMPLETE_MASTER_v1.json")))
    r550 = json.load(open(os.path.join(HERE, "K2_R550_CONSTRUCTION_DRAWING_v1.json")))
    ent = r550["entrance_channel_table"]
    l2 = json.load(open(os.path.join(HERE, "K2_R550_L2_SLOT_TABLE_v1.json")))["table"]
    def lay0(nm): return 1 if "COMB" in master["schedule"][nm]["stations_on_In4"] else 0
    adj = {nm: g2.build_lane(nm)["adj"] for nm in names}
    def cells(nm, L): return set(u % NID for u in adj[nm] if u < TERM and u // NID == L)
    def arcs(nm, L):
        A = set()
        for u, lst in adj[nm].items():
            if u >= TERM or u // NID != L: continue
            for v, _w in lst:
                if v < TERM and v // NID == L: A.add((u % NID, v % NID))
        return A
    # ---- 前提 v2 表（构造式定序指派；逐层按 π 序）----
    pi = {0: [], 1: []}
    for nm in names: pi[lay0(nm)].append(nm)
    for L in (0, 1): pi[L].sort(key=lambda n: ent[n]["d"])
    T = {}
    for L in (0, 1):
        n = len(pi[L])
        for i, nm in enumerate(pi[L]):
            T[nm] = {"layer": L, "d": ent[nm]["d"],
                     "s": 41 + i, "c": 42 + i,          # 断面阶梯点 (c_i, s_i)：c↑、s↑
                     "R": 64 - i,                        # 腰带行 R↓
                     "b": 37 - i,                        # 北巴士行 b↓（<=37 全部在墙之上）
                     "E": 75 - i,                        # 东列 E↓（>=60）
                     "t": int(l2[nm]["col60"])}          # col60 行（R540 取值、同序）
    # ---- 逐线声明格（逐格写死；单格步）----
    legs = {}
    for nm in names:
        L = T[nm]["layer"]; c, s, R, b, E, t, d = T[nm]["c"], T[nm]["s"], T[nm]["R"], T[nm]["b"], T[nm]["E"], T[nm]["t"], T[nm]["d"]
        seq = [tuple(int(x) for x in p.split(",")) for p in ent[nm]["corridor_cells"]]   # 入口段（已在册核过）
        seq += [(c, r) for r in range(s + 1, R + 1)]          # 上升梯（自断面点上行? -> 实际自 R 上到 s；方向无关，只核合法性）
        seq += [(c, r) for r in range(s - 1, b - 1, -1)]      # 北上腿
        seq += [(cc, b) for cc in range(c + 1, E + 1)]        # 巴士东行
        seq += [(E, r) for r in range(b + 1, t + 1)]          # 东列南下
        seq += [(cc, t) for cc in range(E - 1, 59, -1)]       # 收尾东/西向 col60
        legs[nm] = seq
    # ---- 机核 ----
    ill, nonarc = [], []
    for nm in names:
        L = T[nm]["layer"]; CS = cells(nm, L); AR = arcs(nm, L)
        for (cc, rr) in legs[nm]:
            if cc * NY + rr not in CS: ill.append({"lane": nm, "cell": [cc, rr]})
        for a, b2 in zip(legs[nm], legs[nm][1:]):
            if (a[0]*NY+a[1], b2[0]*NY+b2[1]) not in AR and (b2[0]*NY+b2[1], a[0]*NY+a[1]) not in AR:
                nonarc.append({"lane": nm, "u": list(a), "v": list(b2)})
    clash = []
    for L in (0, 1):
        gg = [n for n in names if T[n]["layer"] == L]
        for i, a in enumerate(gg):
            sa = set(legs[a])
            for b2 in gg[i+1:]:
                inter = sa & set(legs[b2])
                if inter: clash.append({"layer": L, "a": a, "b": b2, "n": len(inter), "cells": sorted("%d,%d" % t for t in inter)[:6]})
    ok = not ill and not nonarc and not clash
    rep = {"artifact": "k2_r560_premise_v2_pregate_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-220 sec.3.3(b) pregate on premise v2 (R559.1); table+check only, NO drawing",
           "premise_v2_table": {nm: T[nm] for nm in names},
           "checks": {"(i)_all_declared_cells_legal": {"verdict": "PASS" if not ill else "FAIL", "n": len(ill), "sample": ill[:10]},
                      "(ii)_all_consecutive_steps_are_registered_arcs": {"verdict": "PASS" if not nonarc else "FAIL", "n": len(nonarc), "sample": nonarc[:10]},
                      "(iii)_single_lane_static_proxy": {"verdict": "PASS" if (not ill and not nonarc) else "FAIL",
                                                         "note": "declared chain fully legal+arc-connected per lane => each lane routable alone against static obstacles"},
                      "same_layer_pairwise_cell_disjoint": {"verdict": "PASS" if not clash else "FAIL", "n": len(clash), "sample": clash[:8]}},
           "verdict": "PASS (premise v2 admissible on the declared tables)" if ok else "FAIL (premise v2 needs a table fix)",
           "fail_loud_log": LOGF}
    body = json.dumps({k: v for k, v in rep.items() if k != "artifact_hash16"}, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(os.path.join(HERE, "K2_R560_PREMISE_V2_PREGATE_v1.json"), "w"), ensure_ascii=False, indent=1, default=str)
    log("illegal cells=%d non-arc steps=%d clash pairs=%d => %s" % (len(ill), len(nonarc), len(clash), rep["verdict"]))
    for c in clash[:5]: log("  CLASH %s" % json.dumps(c, ensure_ascii=False))
    for c in ill[:5]: log("  ILL %s" % json.dumps(c, ensure_ascii=False))
    return 0 if ok else 4
if __name__ == "__main__":
    sys.exit(main())
