#!/usr/bin/env python3
"""K2 · R534 —— 归因关 **(c) 联合子集取核探针**（#K2-201 §四② 分层探针 · **0 受证配额** · **fail-loud**）。
只做：对"共享格点最多"的少数几条线，建**独立小子模型**（不求全模型），取 **assumption 核**；UNSAT 时**关预解复取核**。
写保护（只写自身输出名）· 任何异常 ⇒ 打印 `FAIL_LOUD {...}` 并 **exit 3**（禁"exit 0 且无读数"）。"""
import argparse, collections, importlib, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
W = importlib.import_module("K2_R515_FREETERMINALS_v1")
P, X0, Y0, NX, NY, NID, TERM_BASE = W.P, W.X0, W.Y0, W.NX, W.NY, W.NID, W.TERM_BASE
MAXV = 2 * W.MAX_VIA_PAIRS
OWN_OUT = "K2_R534_P2_JOINT_PROBE_v1.json"


def build_subset(subset, arcs, lanes):
    from ortools.sat.python import cp_model
    m = cp_model.CpModel(); x, dem = {}, {}
    for nm in subset:
        x[nm] = [m.NewBoolVar("x_%s_%d" % (nm.replace("-", "_"), i)) for i in range(len(arcs[nm]))]
    for nm in subset:
        src, snk = lanes[nm]["src"], lanes[nm]["snk"]
        inl, outl = collections.defaultdict(list), collections.defaultdict(list)
        for i, (u, v, iv) in enumerate(arcs[nm]):
            outl[u].append(x[nm][i]); inl[v].append(x[nm][i])
        d = m.NewBoolVar("dem_%s" % nm.replace("-", "_")); dem[nm] = d
        m.Add(sum(outl[src]) == 1).OnlyEnforceIf(d); m.Add(sum(inl[src]) == 0).OnlyEnforceIf(d)
        m.Add(sum(inl[snk]) == 1).OnlyEnforceIf(d); m.Add(sum(outl[snk]) == 0).OnlyEnforceIf(d)
        for nd in set(inl) | set(outl):
            if nd not in (src, snk):
                m.Add(sum(inl[nd]) == sum(outl[nd])).OnlyEnforceIf(d)
        m.Add(sum(x[nm][i] for i, (u, v, iv) in enumerate(arcs[nm]) if iv) <= MAXV).OnlyEnforceIf(d)
    use = collections.defaultdict(list)
    for nm in subset:
        for i, (u, v, iv) in enumerate(arcs[nm]):
            if u < TERM_BASE:
                use[(u // NID, u % NID)].append(x[nm][i])
    nc = 0
    for key, lits in use.items():
        if len(lits) > 1:
            m.Add(sum(lits) <= 1); nc += 1
    return m, dem, nc


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, OWN_OUT))
    ap.add_argument("--ks", default="2,3,4")
    ap.add_argument("--budget", type=float, default=90.0)
    a = ap.parse_args()
    if os.path.basename(a.out) != OWN_OUT:
        raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7): %s" % OWN_OUT)
    from ortools.sat.python import cp_model
    t0 = time.time()
    rep = {"artifact": "k2_r534_p2_joint_probe_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-201 sec.4 item (c) layered probes; ZERO certified quota; fail-loud required",
           "certified_solve_calls": 0}
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names); lanes = {nm: g2.build_lane(nm) for nm in names}
    arcs, own = {}, {}
    for nm in names:
        arcs[nm] = [(u, v, 1 if (u < TERM_BASE and v < TERM_BASE and u // NID != v // NID) else 0)
                    for u, lst in lanes[nm]["adj"].items() for (v, w) in lst]
        own[nm] = {u % NID for (u, v, iv) in arcs[nm] if u < TERM_BASE}
    share = sorted(((len(own[a] & own[b]), a, b) for i, a in enumerate(names) for b in names[i + 1:]), reverse=True)
    rep["top_shared_pairs"] = [{"shared_nodes": s, "lanes": [a_, b_]} for (s, a_, b_) in share[:5]]
    print("[stage] top shared pairs:", rep["top_shared_pairs"][:3], flush=True)
    res = []
    for k in [int(v) for v in a.ks.split(",")]:
        subset = list(dict.fromkeys([share[0][1], share[0][2]] + [b for (_s, _a, b) in share if b not in (share[0][1], share[0][2])]))[:k]
        print("[stage] k=%d subset=%s" % (k, subset), flush=True)
        m, dem, nc = build_subset(subset, arcs, lanes)
        nv = len(m.Proto().variables)
        print("[stage] k=%d built vars=%d cons=%d cap=%d" % (k, nv, len(m.Proto().constraints), nc), flush=True)
        s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = a.budget
        m.add_assumptions(list(dem.values()))
        st = s.Solve(m)
        core = list(s.sufficient_assumptions_for_infeasibility())
        row = {"k": k, "subset": subset, "vars": nv, "cap_cons": nc, "status": s.StatusName(st),
               "wall_s": round(s.WallTime(), 1), "core_size": len(core), "core": [str(z) for z in core]}
        print("[stage] k=%d -> %s core=%d wall=%.1fs" % (k, row["status"], row["core_size"], row["wall_s"]), flush=True)
        if row["status"] == "INFEASIBLE":
            s2 = cp_model.CpSolver(); s2.parameters.max_time_in_seconds = a.budget
            s2.parameters.cp_model_presolve = False
            st2 = s2.Solve(m)
            core2 = list(s2.sufficient_assumptions_for_infeasibility())
            row["presolve_off"] = {"status": s2.StatusName(st2), "wall_s": round(s2.WallTime(), 1),
                                   "core_size": len(core2), "core": [str(z) for z in core2]}
            print("[stage] k=%d presolve_OFF -> %s core=%d" % (k, row["presolve_off"]["status"], row["presolve_off"]["core_size"]), flush=True)
        res.append(row)
        rep["partial"] = True
        rep["probes_k"] = res
        json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)   # increment
    first_core = next((r for r in res if r["status"] == "INFEASIBLE" and r["core_size"] > 0), None)
    rep["C_localization"] = {
        "smallest_subset_with_NONEMPTY_core": (first_core or None),
        "reading": ("若小规模联合子集给出**非空核** ⇒ 取核机制在真实约束上可用 ⇒ 全模型空核归因于**规模/取核路径**"
                    "（修法：关预解或分层取核，**非**改编码）；若连小子集也给不出核 ⇒ 归因于**编码/取核接线**。"),
        "verdict": ("NONEMPTY CORE OBTAINED => attribution = extraction-path/scale (fix extraction, not encoding)"
                    if first_core else "no nonempty core at any probed size (see rows) => encoding/extraction wiring suspect")}
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print("[stage] C verdict:", rep["C_localization"]["verdict"], flush=True)
    print("WROTE", a.out, flush=True)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as _e:
        import traceback; traceback.print_exc()
        print('FAIL_LOUD: {"error": %r}' % (str(_e),), flush=True)
        sys.exit(3)
