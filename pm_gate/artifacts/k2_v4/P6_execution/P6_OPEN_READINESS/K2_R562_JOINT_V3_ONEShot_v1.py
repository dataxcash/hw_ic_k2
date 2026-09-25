#!/usr/bin/env python3
"""K2 · R562 —— 前提 v2 联合（入口重推 R<=60 + 转移北巴士/东列）→ 联合核验 → **一次描线** → 在册闸。
新命令；单遍；零求解器；零改参重跑（失败只落诊断）。"""
import sys, os, json, collections, hashlib, time, importlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
LOGF = "/tmp/opencode/r562/oneshot.log"; os.makedirs(os.path.dirname(LOGF), exist_ok=True)
def log(m): open(LOGF, "a").write(str(m) + "\n"); print(str(m), flush=True)
def main():
    open(LOGF, "w").close(); t0 = time.time()
    M = importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1")
    PREV = M.PREV; PREV.Gen._build_edges = M._build_edges_fixed
    W = M.W; NID, NY, TERM = W.NID, W.NY, W.TERM_BASE
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names)
    master = json.load(open(os.path.join(HERE, "K2_R529_WOVEN_COMPLETE_MASTER_v1.json")))
    r550 = json.load(open(os.path.join(HERE, "K2_R550_CONSTRUCTION_DRAWING_v1.json")))
    ent_old = r550["entrance_channel_table"]; tab = r550["l2_slot_table"] if "l2_slot_table" in r550 else None
    l2 = json.load(open(os.path.join(HERE, "K2_R550_L2_SLOT_TABLE_v1.json")))["table"]
    spec = json.load(open(os.path.join(HERE, "K2_R540_CORRIDOR_SPEC_v1.json")))
    _dord = sorted(names, key=lambda n: ent_old[n]["d"])
    _LAY = {nm: (0 if i < 8 else 1) for i, nm in enumerate(_dord)}   # L2 自裁：重发 COMB 层安排 8/8
    def layL(nm): return _LAY[nm]
    def on4(nm, st): return 1 if ["COMB","BELT","WALL","FIELD"][st] in master["schedule"][nm]["stations_on_In4"] else 0
    adj = {nm: g2.build_lane(nm)["adj"] for nm in names}
    def cells(nm, L): return set(u % NID for u in adj[nm] if u < TERM and u // NID == L)
    # ---- 联合表（构造式定序指派 · 逐层 π 序） ----
    pi = {0: [], 1: []}
    for nm in names: pi[layL(nm)].append(nm)
    for L in (0, 1): pi[L].sort(key=lambda n: ent_old[n]["d"])
    T = {}
    for L in (0, 1):
        for i, nm in enumerate(pi[L]):
            T[nm] = {"L": L, "d": ent_old[nm]["d"], "s": 38 + i, "c": 42 + i, "R": 59 - i,
                     "b": 37 - i, "E": 75 - i, "t": int(l2[nm]["col60"]), "exit": int(l2[nm]["exit"])}
    def seq_of_lane(nm):
        x = T[nm]; d, s, c, R, b, E, t = x["d"], x["s"], x["c"], x["R"], x["b"], x["E"], x["t"]
        out = []
        # 入口 v2：下钻 d → 腰带行 R 东行到 c → 沿 c 上到断面行 s
        out += [(d, r) for r in range(35, R + 1)]
        out += [(cc, R) for cc in range(d + 1, c + 1)]
        out += [(c, r) for r in range(R - 1, s - 1, -1)]
        # 转移 v2：北巴士
        out += [(c, r) for r in range(s - 1, b - 1, -1)]
        out += [(cc, b) for cc in range(c + 1, E + 1)]
        out += [(E, r) for r in range(b + 1, t + 1)]
        out += [(cc, t) for cc in range(E - 1, 59, -1)]
        return out
    legs = {nm: seq_of_lane(nm) for nm in names}
    ill, nonarc, clash = [], [], []
    for nm in names:
        L = T[nm]["L"]; CS = cells(nm, L)
        for p in legs[nm]:
            if p[0]*NY+p[1] not in CS: ill.append({"lane": nm, "cell": list(p)})
        for a, b2 in zip(legs[nm], legs[nm][1:]):
            if (a[0]*NY+a[1], b2[0]*NY+b2[1]) not in adj[nm] and (b2[0]*NY+b2[1], a[0]*NY+a[1]) not in adj[nm]:
                nonarc.append({"lane": nm, "u": list(a), "v": list(b2)})
    for L in (0, 1):
        gg = [n for n in names if T[n]["L"] == L]
        for i, a in enumerate(gg):
            sa = set(legs[a])
            for b2 in gg[i+1:]:
                inter = sa & set(legs[b2])
                if inter: clash.append({"layer": L, "a": a, "b": b2, "n": len(inter), "cells": sorted("%d,%d" % t for t in inter)[:6]})
    ok = not ill and not nonarc and not clash
    rep = {"artifact": "k2_r562_joint_v3_oneshot_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-220 sec.3.3(b)(c): joint premise-v2 tables -> check -> ONE drawing pass; no solver, no rerun",
           "table": {nm: T[nm] for nm in names},
           "pregate": {"(i)_cells_legal": {"verdict": "PASS" if not ill else "FAIL", "n": len(ill), "sample": ill[:8]},
                        "(ii)_arcs": {"verdict": "PASS" if not nonarc else "FAIL", "n": len(nonarc), "sample": nonarc[:8]},
                        "same_layer_pairwise_disjoint": {"verdict": "PASS" if not clash else "FAIL", "n": len(clash), "sample": clash[:6]}},
           "solve_calls": 0, "runs": 1}
    if not ok:
        rep["decision"] = "JOINT PREGATE FAILED - diagnostic only (no drawing, no rerun, per #K2-220 sec.4)"
        log("PREGATE FAIL: ill=%d nonarc=%d clash=%d" % (len(ill), len(nonarc), len(clash)))
        for c in clash[:4]: log("  CLASH %s" % json.dumps(c, ensure_ascii=False))
        for c in ill[:4]: log("  ILL %s" % json.dumps(c, ensure_ascii=False))
    else:
        log("PREGATE PASS -> assembling chain + ONE drawing pass")
        chain = {}
        for nm in names:
            L = T[nm]["L"]; east = (g2.grp[nm] == "east")
            items = [("A", None, 0)]
            seq = legs[nm]
            if L == 1:
                pv = None
                for w in spec["per_lane"][nm]["waypoints"]:
                    if w["kind"] == "DIVE_via": pv = int(w["node"])
                items.append(("via", pv if pv is not None else seq[0][0]*NY+seq[0][1], 1))
            items += [("wp", c*NY+r, L) for (c, r) in seq]
            items.append(("wp", 60*NY+T[nm]["t"], on4(nm,1)))
            ex = (T[nm]["exit"]*NY+36) if east else (114*NY+T[nm]["exit"])
            items.append(("wp", ex, on4(nm,2)))
            pr = int(round((g2.B[nm][0]-W.X0)/W.P))*NY+36 if east else ex
            items.append(("wp", pr, on4(nm,3)))
            items.append(("B", None, 0))
            chain[nm] = items
        paths, diag = M.draw_declared(g2, master, spec, names, g2 and {nm: g2.build_lane(nm) for nm in names}, chain)
        if paths is None:
            rep["first_blocker"] = diag; rep["decision"] = "ONE-SHOT DRAW BLOCKED - diagnostic only (no rerun, per #K2-220 sec.4)"
            log("DRAW BLOCKED %s" % json.dumps(diag, ensure_ascii=False))
        else:
            g = M.B.gate(g2, master, names, {nm: g2.build_lane(nm) for nm in names}, paths)
            rep["registered_gates"] = g; rep["n_drawn"] = len(paths)
            rep["drawing"] = {nm: {"n_nodes": len(paths[nm]),
                                   "via_pairs": [[int((a % NID)//NY), int((a % NID) % NY)] for a, b2 in zip(paths[nm], paths[nm][1:])
                                                 if a < TERM and b2 < TERM and a//NID != b2//NID]} for nm in names}
            rep["decision"] = "JOINT V2 ONE-SHOT DRAWING COMPLETE: %d/%d lanes; registered gates %s" % (len(paths), len(names), g["requirement_level_gate"])
            rep["buildability"] = {"mode": "no_move" if g["requirement_level_gate"] == "PASS" else "no_witness", "note": "declared single-cell lines; single pass; hard reservation"}
            log("GATES: %s" % g["requirement_level_gate"])
    rep["elapsed_s"] = round(time.time()-t0, 1); rep["fail_loud_log"] = LOGF
    body = json.dumps({k: v for k, v in rep.items() if k != "artifact_hash16"}, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(os.path.join(HERE, "K2_R562_JOINT_V3_ONE_SHOT_v1.json"), "w"), ensure_ascii=False, indent=1, default=str)
    log("WROTE K2_R562_JOINT_V3_ONE_SHOT_v1.json"); log("OWNER-ITEMS: 0")
    return 0
if __name__ == "__main__":
    sys.exit(main())
