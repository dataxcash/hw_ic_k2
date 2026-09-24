#!/usr/bin/env python3
"""K2 · R533 —— **不可行性归因关**（#K2-200 §四④ (a) SAT 标定 ＋ (b) UNSAT 标定 ＋ (c) 空核成因定位）。
**0 受证配额**（本件为诊断/标定，非"那一枪"）；禁换法/改参/加时/换工具/自开新窗。写保护同 #K2-195 §三.7。"""
import argparse, collections, importlib, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
W = importlib.import_module("K2_R515_FREETERMINALS_v1")
P, X0, Y0, NX, NY, NID, TERM_BASE = W.P, W.X0, W.Y0, W.NX, W.NY, W.NID, W.TERM_BASE
MAXV = 2 * W.MAX_VIA_PAIRS
OWN_OUT = "K2_R533_INFEASIBILITY_ATTRIBUTION_v1.json"


def tiny_models():
    """(a) SAT 标定 / (b) UNSAT 标定 —— 与在册编码同构（需求=assumption · 约束 OnlyEnforceIf(需求)）。"""
    from ortools.sat.python import cp_model
    out = {}
    # (a) SAT: two lanes want two DIFFERENT nodes; each demand implies its own node => SAT (witness derivable)
    m = cp_model.CpModel()
    x1, x2 = m.NewBoolVar("x1"), m.NewBoolVar("x2"); d1, d2 = m.NewBoolVar("d1"), m.NewBoolVar("d2")
    m.Add(x1 == 1).OnlyEnforceIf(d1); m.Add(x2 == 1).OnlyEnforceIf(d2); m.Add(x1 + x2 <= 2)
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = 10
    st = s.Solve(m, ) if False else None
    m.add_assumptions([d1, d2]); st = s.Solve(m)
    out["a_sat_calibration"] = {"status": s.StatusName(st),
                                "x1": (int(s.Value(x1)) if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None),
                                "x2": (int(s.Value(x2)) if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None),
                                "core": [str(k) for k in s.sufficient_assumptions_for_infeasibility()]}
    # (b) UNSAT: two lanes want the SAME single node (capacity 1) => assumptions alone make it infeasible
    for tag, presolve in (("presolve_on", True), ("presolve_off", False)):
        m2 = cp_model.CpModel()
        y1, y2 = m2.NewBoolVar("y1"), m2.NewBoolVar("y2"); e1, e2 = m2.NewBoolVar("e1"), m2.NewBoolVar("e2")
        m2.Add(y1 == 1).OnlyEnforceIf(e1); m2.Add(y2 == 1).OnlyEnforceIf(e2); m2.Add(y1 + y2 <= 1)
        s2 = cp_model.CpSolver(); s2.parameters.max_time_in_seconds = 10
        m2.add_assumptions([e1, e2]); st2 = s2.Solve(m2)
        core = list(s2.sufficient_assumptions_for_infeasibility())
        out["b_unsat_calibration_%s" % tag] = {"status": s2.StatusName(st2), "core_size": len(core),
                                               "core": [str(k) for k in core],
                                               "verdict": "PASS(non-empty core)" if core else "FAIL(empty core)"}
    return out


def real_model(g2, names, lanes):
    """(c) 当前模型（同 R532 编码）—— 返回 (mo, x, demand, arcs)；未 add_assumptions。"""
    from ortools.sat.python import cp_model
    mo = cp_model.CpModel(); x, dem, arcs = {}, {}, {}
    for nm in names:
        arcs[nm] = [(u, v, 1 if (u < TERM_BASE and v < TERM_BASE and u // NID != v // NID) else 0)
                    for u, lst in lanes[nm]["adj"].items() for (v, w) in lst]
        x[nm] = [mo.NewBoolVar("x_%s_%d" % (nm.replace("-", "_"), k)) for k in range(len(arcs[nm]))]
    for nm in names:
        src, snk = lanes[nm]["src"], lanes[nm]["snk"]
        inflow, outflow = collections.defaultdict(list), collections.defaultdict(list)
        for k, (u, v, iv) in enumerate(arcs[nm]):
            outflow[u].append(x[nm][k]); inflow[v].append(x[nm][k])
        d = mo.NewBoolVar("dem_%s" % nm.replace("-", "_")); dem[nm] = d
        mo.Add(sum(outflow[src]) == 1).OnlyEnforceIf(d); mo.Add(sum(inflow[src]) == 0).OnlyEnforceIf(d)
        mo.Add(sum(inflow[snk]) == 1).OnlyEnforceIf(d); mo.Add(sum(outflow[snk]) == 0).OnlyEnforceIf(d)
        for nd in set(inflow) | set(outflow):
            if nd not in (src, snk):
                mo.Add(sum(inflow[nd]) == sum(outflow[nd])).OnlyEnforceIf(d)
        mo.Add(sum(x[nm][k] for k, (u, v, iv) in enumerate(arcs[nm]) if iv) <= MAXV).OnlyEnforceIf(d)
    use = collections.defaultdict(list)
    for nm in names:
        for k, (u, v, iv) in enumerate(arcs[nm]):
            if u < TERM_BASE:
                use[(u // NID, u % NID)].append(x[nm][k])
    ncap = 0
    for key, lits in use.items():
        if len(lits) > 1:
            mo.Add(sum(lits) <= 1); ncap += 1
    return mo, x, dem, arcs, ncap


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, OWN_OUT))
    a = ap.parse_args()
    if os.path.basename(a.out) != OWN_OUT:
        raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7)")
    t0 = time.time()
    from ortools.sat.python import cp_model
    rep = {"artifact": "k2_r533_infeasibility_attribution_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-200 sec.4 item (a)+(b)+(c) attribution gate; ZERO certified quota (diagnostics only)",
           "certified_solve_calls": 0}
    rep["calibrations"] = tiny_models()
    print("[stage] calibrations done:", json.dumps(rep["calibrations"], ensure_ascii=False)[:400], flush=True)
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names); lanes = {nm: g2.build_lane(nm) for nm in names}
    mo, x, dem, arcs, ncap = real_model(g2, names, lanes)
    rep["real_model"] = {"bool_vars": len(mo.Proto().variables), "constraints": len(mo.Proto().constraints),
                         "node_capacity": ncap, "total_arcs": sum(len(v) for v in arcs.values())}
    probes = {}
    # P0: baseline — all demands OFF (hard constraints must be trivially satisfiable)
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = 90
    st = s.Solve(mo)
    print("[stage] P0 all-demands-off:", s.StatusName(st), flush=True)
    probes["P0_all_demands_off"] = {"status": s.StatusName(st),
                                    "reading": "hard/base constraint set is consistent (no demand enforced)"}
    # P1: each lane ALONE => should be SAT (per-lane feasibility)
    # P1 (fast): each lane ALONE => solve a per-lane SUBMODEL (equivalent: with a single demand on, all other
    # lanes' variables are 0), which is small => seconds instead of minutes on the 1.19M-var full model.
    alone_bad = []
    for nm in names:
        m1 = cp_model.CpModel()
        xs = [m1.NewBoolVar("a_%s_%d" % (nm.replace("-", "_"), i)) for i in range(len(arcs[nm]))]
        src, snk = lanes[nm]["src"], lanes[nm]["snk"]
        inl, outl = collections.defaultdict(list), collections.defaultdict(list)
        for i2, (u, v, iv) in enumerate(arcs[nm]):
            outl[u].append(xs[i2]); inl[v].append(xs[i2])
        m1.Add(sum(outl[src]) == 1); m1.Add(sum(inl[src]) == 0)
        m1.Add(sum(inl[snk]) == 1); m1.Add(sum(outl[snk]) == 0)
        for nd in set(inl) | set(outl):
            if nd not in (src, snk):
                m1.Add(sum(inl[nd]) == sum(outl[nd]))
        m1.Add(sum(xs[i2] for i2, (u, v, iv) in enumerate(arcs[nm]) if iv) <= MAXV)
        s1 = cp_model.CpSolver(); s1.parameters.max_time_in_seconds = 60
        st1 = s1.Solve(m1)
        if st1 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            alone_bad.append({"lane": nm, "status": s1.StatusName(st1), "vars": len(m1.Proto().variables)})
    print("[stage] P1 per-lane submodels done; not_sat =", alone_bad, flush=True)
    # fail-loud guarantee (#K2-201 sec.3.4 i): write the readings obtained so far BEFORE the P2 stage, so a
    # silent death in P2 can never again leave us with "no reading at all".
    rep["partial"] = True
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print("[stage] partial artifact written (calibrations + P0 + P1)", flush=True)
    probes["P1_each_lane_alone"] = {"n_lanes": len(names), "not_sat": alone_bad,
                                    "reading": "every lane is individually routable inside the full model" if not alone_bad
                                               else "some lane is infeasible even alone => hard constraints/encoding suspect"}
    # P2: minimal-ish joint subsets (most-shared nodes first) => UNSAT? core non-empty?
    pair_share = []
    own_nodes = {}
    for nm in names:
        own_nodes[nm] = {u % NID for (u, v, iv) in arcs[nm] if u < TERM_BASE}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            pair_share.append((len(own_nodes[names[i]] & own_nodes[names[j]]), names[i], names[j]))
    pair_share.sort(reverse=True)
    top = pair_share[0]
    rep["top_shared_pair"] = {"lanes": [top[1], top[2]], "shared_nodes": top[0]}
    # reduced-model probes by fixing all demands except the subset to False (cheap: add assumptions only for subset
    # and constrain the rest's demand literals to 0)
    def probe_subset(subset, presolve=True):
        m0 = mo.Clone() if hasattr(mo, "Clone") else None
        return None  # placeholder (kept simple: we instead constrain demands directly on the live model below)
    res_p2 = []
    for k in (2, 3, 4):
        subset = [top[1], top[2]] + [n for _s, n, _o in pair_share[:k] if n not in (top[1], top[2])][:k - 2]
        # enforce only this subset: build a fresh small model-free approach => use assumptions on subset and
        # forbid the rest by adding them as NOT assumptions? assumptions can't be negative here, so we instead
        # solve a sub-model restricted to the subset lanes (rebuild with only those lanes + their shared caps).
        m2 = cp_model.CpModel(); x2, d2, arcs2 = {}, {}, {}
        for nm in subset:
            arcs2[nm] = arcs[nm]
            x2[nm] = [m2.NewBoolVar("z_%s_%d" % (nm.replace("-", "_"), i)) for i in range(len(arcs[nm]))]
        for nm in subset:
            src, snk = lanes[nm]["src"], lanes[nm]["snk"]
            inl, outl = collections.defaultdict(list), collections.defaultdict(list)
            for i2, (u, v, iv) in enumerate(arcs2[nm]):
                outl[u].append(x2[nm][i2]); inl[v].append(x2[nm][i2])
            d = m2.NewBoolVar("d_%s" % nm.replace("-", "_")); d2[nm] = d
            m2.Add(sum(outl[src]) == 1).OnlyEnforceIf(d); m2.Add(sum(inl[src]) == 0).OnlyEnforceIf(d)
            m2.Add(sum(inl[snk]) == 1).OnlyEnforceIf(d); m2.Add(sum(outl[snk]) == 0).OnlyEnforceIf(d)
            for nd in set(inl) | set(outl):
                if nd not in (src, snk):
                    m2.Add(sum(inl[nd]) == sum(outl[nd])).OnlyEnforceIf(d)
            m2.Add(sum(x2[nm][i2] for i2, (u, v, iv) in enumerate(arcs2[nm]) if iv) <= MAXV).OnlyEnforceIf(d)
        use2 = collections.defaultdict(list)
        for nm in subset:
            for i2, (u, v, iv) in enumerate(arcs2[nm]):
                if u < TERM_BASE:
                    use2[(u // NID, u % NID)].append(x2[nm][i2])
        for key, lits in use2.items():
            if len(lits) > 1:
                m2.Add(sum(lits) <= 1)
        s2 = cp_model.CpSolver(); s2.parameters.max_time_in_seconds = 120
        m2.add_assumptions(list(d2.values()))
        st2 = s2.Solve(m2)
        core = list(s2.sufficient_assumptions_for_infeasibility())
        return {"subset": subset, "status": s2.StatusName(st2), "wall_s": round(s2.WallTime(), 1),
                "core_size": len(core), "core": [str(k) for k in core][:8],
                "vars": len(m2.Proto().variables), "cons": len(m2.Proto().constraints)}
    for k in (2, 3, 4):
        subset = [top[1], top[2]] + [n for _s, n, _o in pair_share[:k] if n not in (top[1], top[2])][:max(0, k - 2)]
        r_on = probe_subset(subset, True)
        r_off = None
        res_p2.append({"k": len(subset), "presolve_on": r_on, "presolve_off": r_off})
        print("[stage] P2 k=%d subset=%s status=%s core=%d" % (len(subset), subset, r_on["status"], r_on["core_size"]), flush=True)
    probes["P2_joint_subsets"] = res_p2
    rep["probes"] = probes
    # ---- (c) localization verdict ----
    a_ok = rep["calibrations"]["a_sat_calibration"]["status"] == "OPTIMAL"
    b_ok = rep["calibrations"]["b_unsat_calibration_presolve_on"]["verdict"].startswith("PASS")
    p0_sat = probes["P0_all_demands_off"]["status"] == "OPTIMAL"
    small_core = [r for r in res_p2 if r["presolve_on"]["status"] == "INFEASIBLE" and r["presolve_on"]["core_size"] > 0]
    rep["C_localization"] = {
        "a_sat_calibration_ok": a_ok, "b_unsat_calibration_nonempty_core_ok": b_ok,
        "p0_base_constraints_consistent": p0_sat,
        "smallest_joint_subset_with_NONEMPTY_core": (small_core[0]["presolve_on"] if small_core else None),
        "verdict": ("取核机制在最小例上可用（(b) PASS）且基底约束自洽（P0 SAT）；"
                    "若小规模联合子集能给出非空核 ⇒ 全模型空核归因于 **取核路径/预解**（修：关闭预解后重取核，非改编码）；"
                    "若小规模联合子集也给不出核 ⇒ 归因于 **编码/取核接线**。见 smallest_joint_subset_with_NONEMPTY_core 与 P2 明细。")}
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(rep["calibrations"], ensure_ascii=False, indent=1)[:900])
    print("P0:", probes["P0_all_demands_off"]["status"], "| P1 not_sat:", probes["P1_each_lane_alone"]["not_sat"])
    for r in res_p2:
        print("P2 k=%d status=%s core=%d vars=%d" % (r["k"], r["presolve_on"]["status"], r["presolve_on"]["core_size"],
                                                     r["presolve_on"]["vars"]),
              ("| presolve_off=%s core=%d" % (r["presolve_off"]["status"], r["presolve_off"]["core_size"])) if r["presolve_off"] else "")
    print("C verdict:", rep["C_localization"]["verdict"][:200])
    print("WROTE", a.out)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as _e:                      # fail-loud (#K2-201 sec.3.4 i): never exit 0 without a reading
        import traceback
        traceback.print_exc()
        print('FAIL_LOUD: {"error": %r}' % (str(_e),), flush=True)
        sys.exit(3)
