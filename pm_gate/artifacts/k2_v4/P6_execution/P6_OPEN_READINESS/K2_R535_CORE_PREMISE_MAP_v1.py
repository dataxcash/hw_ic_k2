#!/usr/bin/env python3
"""K2 · R535 —— **(c) 收尾：核心字面量逐前提映射 ＋ 承重结构探针**（#K2-202 §三.3 / §四④ · **0 受证配额** · 只读 · fail-loud）。
做法：复建 R534 的 k=4 子集模型 ⇒ 取核 ⇒ 把核内字面量映射到**命名前提类别**（本例 = 各线"需求"假设）；再做 **leave-one-out** 三子集（4 个）
⇒ 判定该冲突是 **2/3 路（可滑）** 还是 **真 4 路联合（张力或硬墙）**；并给出**守恒级一阶读数**（共享格点规模）。
"""
import argparse, collections, importlib, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
W = importlib.import_module("K2_R515_FREETERMINALS_v1")
P2 = importlib.import_module("K2_R534_P2_JOINT_PROBE_v1")
NID, TERM_BASE = W.NID, W.TERM_BASE
OWN_OUT = "K2_R535_CORE_PREMISE_MAP_v1.json"
SUBSET4 = ["PCIE_UP_OUT0_P_J2", "PCIE_UP_OUT1_N_J2", "PCIE_UP_OUT4_P_J2", "PCIE_UP_OUT2_P_J2"]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, OWN_OUT))
    ap.add_argument("--budget", type=float, default=120.0)
    a = ap.parse_args()
    if os.path.basename(a.out) != OWN_OUT:
        raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7)")
    from ortools.sat.python import cp_model
    t0 = time.time()
    rep = {"artifact": "k2_r535_core_premise_map_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-202 sec.3.3 (approved read-only premise attribution, 0 quota) + sec.4 item (i)-(iii)",
           "certified_solve_calls": 0}
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names); lanes = {nm: g2.build_lane(nm) for nm in names}
    arcs, own = {}, {}
    for nm in names:
        arcs[nm] = [(u, v, 1 if (u < TERM_BASE and v < TERM_BASE and u // NID != v // NID) else 0)
                    for u, lst in lanes[nm]["adj"].items() for (v, w) in lst]
        own[nm] = {u % NID for (u, v, iv) in arcs[nm] if u < TERM_BASE}
    # ---- (i) core -> named premise mapping on the k=4 subset ----
    m, dem, nc = P2.build_subset(SUBSET4, arcs, lanes)
    m.add_assumptions(list(dem.values()))
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = a.budget
    st = s.Solve(m); core = list(s.sufficient_assumptions_for_infeasibility())
    byidx = {v.Index(): v.Name() for v in dem.values()}
    bypos = {i: dem[nm].Name() for i, nm in enumerate(SUBSET4)}
    rep["i_core_premise_mapping"] = {
        "subset": SUBSET4, "status": s.StatusName(st), "wall_s": round(s.WallTime(), 1),
        "core_raw": core,
        "mapping_by_variable_index": {str(k): byidx.get(k, "UNMAPPED") for k in core},
        "mapping_by_assumption_position": {str(k): bypos.get(k, "UNMAPPED") for k in core},
        "premise_class": "DEMAND assumption(s) of the named lanes (the only assumptions in this model)",
        "unmapped_items": [k for k in core if k not in byidx and k not in bypos]}
    print("[stage] core:", core, "->", rep["i_core_premise_mapping"]["mapping_by_variable_index"], flush=True)
    # ---- (ii) leave-one-out 3-subsets: is the conflict 2/3-way (mobile) or true 4-way joint? ----
    loo = []
    for drop in SUBSET4:
        sub = [x for x in SUBSET4 if x != drop]
        m2, dem2, nc2 = P2.build_subset(sub, arcs, lanes)
        m2.add_assumptions(list(dem2.values()))
        s2 = cp_model.CpSolver(); s2.parameters.max_time_in_seconds = a.budget
        st2 = s2.Solve(m2)
        row = {"dropped": drop, "subset": sub, "status": s2.StatusName(st2), "wall_s": round(s2.WallTime(), 1),
               "core_size": len(list(s2.sufficient_assumptions_for_infeasibility()))}
        print("[stage] leave-one-out drop=%s -> %s" % (drop, row["status"]), flush=True)
        loo.append(row)
    rep["ii_leave_one_out_3subsets"] = loo
    all3_sat = all(x["status"] in ("OPTIMAL", "FEASIBLE") for x in loo)
    # ---- (iii) conservation-level first-order reading (shared node geography) ----
    sh = {}
    for i in range(4):
        for j in range(i + 1, 4):
            sh["%s|%s" % (SUBSET4[i], SUBSET4[j])] = len(own[SUBSET4[i]] & own[SUBSET4[j]])
    union = set().union(*[own[nm] for nm in SUBSET4])
    rep["iii_conservation_first_order"] = {
        "pairwise_shared_nodes": sh, "union_legal_nodes": len(union),
        "reading": ("4 线共享格点规模极大（见 pairwise_shared_nodes）⇒ 冲突**不是**（没地方），属**多线联合占用**问题；"
                    "逐前提判定需在此基础上做**该区断面容量 vs 4 线需求的守恒级核对**。"),
        "binary_verdict_so_far": ("TENSION-CLASS (no conservation wall found yet): every 3-subset is routable "
                                  "=> the conflict is a joint 4-way occupancy tension, not a pairwise/triple one"
                                  if all3_sat else "4-way conflict already appears at 3 lanes => inspect that triple")}
    rep["iv_minimal_relaxation_candidates"] = {
        "note": "candidate premise relaxations to put to the supervisor (NOT self-applied)",
        "candidates": ["raise the per-lane via budget (2 via pairs) only for this 4-lane set (authorised? in-register MAX_VIA_PAIRS=2)",
                       "widen the allowed via zone set for these lanes (in-register: four wide zones)",
                       "allow re-pairing / re-slotting the 4 lanes' section slots (the R529 complete-master decisions)"]}
    rep["verdict"] = {"all_three_subsets_routable": all3_sat,
                      "class": ("tension" if all3_sat else "joint-4way-or-triple"),
                      "gate_A": ("PASS (tension-class => per K2-202 sec.3.4 the shot may be fired with the repaired "
                                 "extraction path and formal premise relaxation list)" if all3_sat else
                                 "STOP (report to supervisor)")}
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print("[stage] verdict:", rep["verdict"], flush=True)
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
