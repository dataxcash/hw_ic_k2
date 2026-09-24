#!/usr/bin/env python3
"""K2 · R536 —— **放松探针**（#K2-202 §三.4 闸 A 收尾 · **0 受证配额** · 只读 · fail-loud）。
对最小冲突三元 T={OUT0_P,OUT4_P,OUT2_P} 做**必要前提放开**试验：①对孔限额 (2/3/4 对) ②去掉逐层格点容量(互斥)诊断上界
⇒ 判定该冲突是**张力（可放）**还是**守恒级硬墙**。"""
import argparse, collections, importlib, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
W = importlib.import_module("K2_R515_FREETERMINALS_v1")
NID, TERM_BASE = W.NID, W.TERM_BASE
OWN_OUT = "K2_R536_RELAXATION_PROBE_v1.json"
T = ["PCIE_UP_OUT0_P_J2", "PCIE_UP_OUT4_P_J2", "PCIE_UP_OUT2_P_J2"]


def build(subset, arcs, lanes, nv_max, cap_on=True):
    from ortools.sat.python import cp_model
    m = cp_model.CpModel(); x, dem = {}, {}
    for nm in subset:
        x[nm] = [m.NewBoolVar("x_%s_%d" % (nm.replace("-", "_"), i)) for i in range(len(arcs[nm]))]
    for nm in subset:
        src, snk = lanes[nm]["src"], lanes[nm]["snk"]
        inl, outl = collections.defaultdict(list), collections.defaultdict(list)
        for i, (u, v, iv) in enumerate(arcs[nm]):
            outl[u].append(x[nm][i]); inl[v].append(x[nm][i])
        d = m.NewBoolVar("d_%s" % nm.replace("-", "_")); dem[nm] = d
        m.Add(sum(outl[src]) == 1).OnlyEnforceIf(d); m.Add(sum(inl[src]) == 0).OnlyEnforceIf(d)
        m.Add(sum(inl[snk]) == 1).OnlyEnforceIf(d); m.Add(sum(outl[snk]) == 0).OnlyEnforceIf(d)
        for nd in set(inl) | set(outl):
            if nd not in (src, snk):
                m.Add(sum(inl[nd]) == sum(outl[nd])).OnlyEnforceIf(d)
        m.Add(sum(x[nm][i] for i, (u, v, iv) in enumerate(arcs[nm]) if iv) <= nv_max).OnlyEnforceIf(d)
    if cap_on:
        use = collections.defaultdict(list)
        for nm in subset:
            for i, (u, v, iv) in enumerate(arcs[nm]):
                if u < TERM_BASE:
                    use[(u // NID, u % NID)].append(x[nm][i])
        for key, lits in use.items():
            if len(lits) > 1:
                m.Add(sum(lits) <= 1)
    return m, dem


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, OWN_OUT))
    ap.add_argument("--budget", type=float, default=120.0)
    a = ap.parse_args()
    if os.path.basename(a.out) != OWN_OUT:
        raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7)")
    from ortools.sat.python import cp_model
    t0 = time.time()
    rep = {"artifact": "k2_r536_relaxation_probe_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-202 sec.3.4 gate-A closeout (relaxation probe; ZERO certified quota)",
           "certified_solve_calls": 0, "triple": T}
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names); lanes = {nm: g2.build_lane(nm) for nm in names}
    arcs = {nm: [(u, v, 1 if (u < TERM_BASE and v < TERM_BASE and u // NID != v // NID) else 0)
                 for u, lst in lanes[nm]["adj"].items() for (v, w) in lst] for nm in names}
    rows = []
    for tag, nv, cap_on in (("baseline_2pairs_capON", 2 * W.MAX_VIA_PAIRS, True),
                            ("relax_3pairs_capON", 6, True),
                            ("relax_4pairs_capON", 8, True),
                            ("diag_capOFF(2pairs)", 2 * W.MAX_VIA_PAIRS, False)):
        m, dem = build(T, arcs, lanes, nv, cap_on)
        m.add_assumptions(list(dem.values()))
        s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = a.budget
        st = s.Solve(m)
        row = {"probe": tag, "via_budget_arcs": nv, "node_capacity": cap_on, "status": s.StatusName(st),
               "wall_s": round(s.WallTime(), 1), "vars": len(m.Proto().variables)}
        print("[stage] %-24s -> %s (%.1fs)" % (tag, row["status"], row["wall_s"]), flush=True)
        rows.append(row)
        rep["partial"] = True; rep["rows"] = rows
        json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    base = rows[0]["status"]; r3 = rows[1]["status"]; r4 = rows[2]["status"]; off = rows[3]["status"]
    rep["verdict"] = {
        "baseline_unroutable": base == "INFEASIBLE",
        "flips_to_SAT_by_via_budget": (r3 in ("OPTIMAL", "FEASIBLE") or r4 in ("OPTIMAL", "FEASIBLE")),
        "SAT_without_node_capacity": off in ("OPTIMAL", "FEASIBLE"),
        "class": ("TENSION (relaxable: the conflict is carried by the in-register per-lane via budget / by the joint "
                  "node-capacity encoding, not by total space)" if (off in ("OPTIMAL", "FEASIBLE") or r3 in ("OPTIMAL", "FEASIBLE") or r4 in ("OPTIMAL", "FEASIBLE"))
                  else "CONSERVATION-GRADE WALL candidate (no tested relaxation helps => report to supervisor; gate A = STOP)"),
        "gate_A": ("PASS (tension class => per K2-202 sec.3.4 the single carried-over shot may be fired with the "
                   "repaired extraction path + a listed in-register premise relaxation)"
                   if (off in ("OPTIMAL", "FEASIBLE") or r3 in ("OPTIMAL", "FEASIBLE") or r4 in ("OPTIMAL", "FEASIBLE"))
                   else "STOP (report to supervisor)")}
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print("[stage] verdict:", json.dumps(rep["verdict"], ensure_ascii=False), flush=True)
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
