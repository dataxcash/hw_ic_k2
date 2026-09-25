#!/usr/bin/env python3
"""K2 · R553 —— 第二张表「断面间转移」的**分配表（先写表、判据先行）**（承 #K2-219 §五②）
构造式定序指派 · 单遍：按 π 序，每线只从"当前未被同层占用"的合法深行/东列里取，并**当场登记**。
本件**不调用构造器**（零描线）：只出表 + 机核（① 每格在册合法 ② 同层成对错开＝无重格（轴向腿 ⇒ 无交叉））。
"""
import sys, os, json, collections, hashlib, time
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS")
HERE = os.path.dirname(os.path.abspath(__file__))
LOGF = "/tmp/opencode/r553/table.log"; OWN_OUT = "K2_R553_TRANSFER_ALLOCATION_TABLE_v1.json"
def log(m):
    os.makedirs(os.path.dirname(LOGF), exist_ok=True); open(LOGF, "a").write(str(m) + "\n"); print(str(m), flush=True)

def main():
    os.makedirs(os.path.dirname(LOGF), exist_ok=True); open(LOGF, "w").close(); t0 = time.time()
    import importlib, types
    import numpy as np
    for nm in ("ortools", "ortools.sat", "ortools.sat.python"):
        sys.modules.setdefault(nm, types.ModuleType(nm))
    cm = types.ModuleType("ortools.sat.python.cp_model")
    class _D:
        def __init__(self, *a, **k): pass
    cm.CpModel = _D; cm.CpSolver = _D
    sys.modules["ortools.sat.python.cp_model"] = cm; sys.modules["ortools.sat.python"].cp_model = cm
    M = importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1")
    PREV = M.PREV; PREV.Gen._build_edges = M._build_edges_fixed
    W = M.W; NID = W.NID; NY = W.NY; TERM = W.TERM_BASE
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names)
    lanes = {nm: g2.build_lane(nm) for nm in names}
    master = json.load(open(os.path.join(HERE, "K2_R529_WOVEN_COMPLETE_MASTER_v1.json")))
    l2 = json.load(open(os.path.join(HERE, "K2_R550_L2_SLOT_TABLE_v1.json")))
    r550 = json.load(open(os.path.join(HERE, "K2_R550_CONSTRUCTION_DRAWING_v1.json")))
    ent_tab = r550["entrance_channel_table"]
    def lay0(nm): return 1 if "COMB" in master["schedule"][nm]["stations_on_In4"] else 0
    def cells(nm, L):
        return set(u % NID for u in lanes[nm]["adj"] if u < TERM and u // NID == L)
    CS = {nm: cells(nm, lay0(nm)) for nm in names}
    # π（每层按 d 升序）与断面值取自 R550 的新版 L2 表 + 入口表
    pi = {0: [], 1: []}
    for nm in names: pi[lay0(nm)].append(nm)
    for L in (0, 1):
        pi[L].sort(key=lambda n: ent_tab[n]["d"])
    slot = {nm: {"W": ent_tab[nm]["W"], "col33": ent_tab[nm]["col33_row"], "col60": l2["table"][nm]["col60"]} for nm in names}
    # ---- 构造式定序指派（单遍；取用即登记）----
    X, tbl = {}, []
    for L in (0, 1):
        # 分配律（机核推导，见件内 checks）：D 递减、E 递减 —— 与"下潜列 W 递减 / col60 行 t 递增"成对错开
        free_rows = list(range(64, 53, -1))        # 深行候选（南场），降序取用 ⇒ 早线更深
        free_cols = list(range(70, 59, -1))        # 东列候选（腰带东侧），降序取用 ⇒ 早线更东
        for k, nm in enumerate(pi[L]):
            Wc = slot[nm]["W"]; srow = slot[nm]["col33"]; trow = slot[nm]["col60"]
            T = 33 if srow == 31 else srow
            D = next(r for r in free_rows if r >= 54)
            E = next(c for c in free_cols if c <= 70)
            free_rows.remove(D); free_cols.remove(E)
            X[nm] = {"layer": L, "W": Wc, "T": T, "D": D, "E": E, "col60": trow}
            tbl.append({"lane": nm, "layer": L, "pi_rank": k, "down_leg_col": Wc, "deep_row": D,
                        "up_leg_col": E, "riser_top_row": T, "col60_row": trow})
    # ---- 逐线腿格（声明线逐格）----
    legs = {}
    for nm in names:
        x = X[nm]; Wc, T, D, E, t = x["W"], x["T"], x["D"], x["E"], x["col60"]
        c = []
        c += [(cc, T) for cc in range(34, Wc + 1)]
        c += [(Wc, r) for r in range(T + 1, D + 1)]
        c += [(cc, D) for cc in range(Wc + 1, E + 1)]
        c += [(E, r) for r in range(D - 1, t - 1, -1)]
        c += [(cc, t) for cc in range(E - 1, 59, -1)]
        # 入口走廊（取自 R550 表，逐格已在册核过）
        e = [tuple(int(v) for v in s.split(",")) for s in ent_tab[nm]["corridor_cells"]]
        legs[nm] = {"entrance": e, "transfer": c}
    # ---- 机核 ①：每格在册合法 ----
    ill = []
    for nm in names:
        L = lay0(nm)
        for kind in ("entrance", "transfer"):
            for (cc, rr) in legs[nm][kind]:
                if cc * NY + rr not in CS[nm]:
                    ill.append({"lane": nm, "kind": kind, "cell": [cc, rr]})
    # ---- 机核 ②：同层成对错开（轴向腿 ⇒ 无重格即无交叉，且格距 >= 1 格 = pitch P）----
    clash = []
    for L in (0, 1):
        gg = [n for n in names if lay0(n) == L]
        for i, a in enumerate(gg):
            sa = set(legs[a]["entrance"]) | set(legs[a]["transfer"])
            for b in gg[i + 1:]:
                sb = set(legs[b]["entrance"]) | set(legs[b]["transfer"])
                inter = sa & sb
                if inter:
                    clash.append({"layer": L, "a": a, "b": b, "n": len(inter),
                                  "cells": sorted("%d,%d" % t for t in inter)[:8]})
    rep = {"artifact": "k2_r553_transfer_allocation_table_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-219 sec.5: assignment first (constructive ordered single pass), criteria-first; NO construction run",
           "rule": "per layer, in pi order (entrance d-order): deep row D taken from the currently free rows >=54; "
                   "east column E taken from the currently free columns <=70 (descending); W (down-leg column) inherited "
                   "from the entrance riser (already one per lane); register on take.",
           "table": tbl, "legs": {nm: {"entrance_cells": len(legs[nm]["entrance"]), "transfer_cells": len(legs[nm]["transfer"]),
                                      "transfer": ["%d,%d" % t for t in legs[nm]["transfer"]]} for nm in names},
           "checks": {"all_cells_legal_in_lane_graph": {"verdict": "PASS" if not ill else "FAIL", "n_illegal": len(ill), "illegal": ill[:20]},
                      "same_layer_pairwise_cell_disjoint": {"verdict": "PASS" if not clash else "FAIL", "n_clash_pairs": len(clash), "clash": clash[:12]},
                      "note": "legs are axis-aligned single-cell declared lines => pairwise disjoint cells implies no crossing and min centre distance >= P (pitch)"},
           "conclusion": "", "fail_loud_log": LOGF}
    ok = (not ill) and (not clash)
    rep["conclusion"] = ("分配表成立（同层成对错开）⇒ 可据此一次描线" if ok else
                         "分配表不成立：同一层的绕行腿互相重格 ⇒ 需换分配律（本件只报表，不描线、不重跑）")
    body = json.dumps({k: v for k, v in rep.items() if k != "artifact_hash16"}, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(os.path.join(HERE, OWN_OUT), "w"), ensure_ascii=False, indent=1, default=str)
    log("cells illegal=%d ; same-layer clash pairs=%d" % (len(ill), len(clash)))
    for c in clash[:6]: log("  CLASH %s" % json.dumps(c, ensure_ascii=False))
    log("VERDICT: %s" % ("PASS" if ok else "FAIL")); log("WROTE %s" % OWN_OUT); log("OWNER-ITEMS: 0")
    return 0 if ok else 4
if __name__ == "__main__":
    sys.exit(main())
