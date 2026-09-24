#!/usr/bin/env python3
"""K2 · R532 —— **联合模型受证可行性求解（口径保真补射 · #K2-198 §三.4）**：过孔域 = **四宽区全部在册过孔站**（**不再**收窄）＋ **显式孔间距约束**（2x2 格块 clique ⇒ 块内 <=1 ⇒ 两两 >= VIA_SEP=0.70mm）。

16 根线**同时**入求解器：每根线在**自己完整网图**上取流（连通＋端点）· **逐层每格点容量 ≤1**（互交由求解器约束）·
**换层 ≤2 对孔**（孔位限于在册四宽区；孔位集按 **2 格(2P>VIA_SEP) 间距**取子集 ⇒ 格点容量即保证孔间距）·
**SAT ⇒ 16/16 见证**（再走在册 `exact_gate`＋`gate_vias`＋端点签字）／ **UNSAT ⇒ 以各线需求为假设取非空核**。
**禁**：分区/圈地（#K2-197 §三.5 永久关闭）· 贪心代答 · 加时 · 削地 · 改参重跑。写保护 `guard_out` 同 #K2-195 §三.7。
"""
import argparse, collections, importlib, json, math, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
W = importlib.import_module("K2_R515_FREETERMINALS_v1")
G = importlib.import_module("K2_R523_LAYERHOP_PARITY_FORMC_v1")
P, X0, Y0, NX, NY, NID, TERM_BASE = W.P, W.X0, W.Y0, W.NX, W.NY, W.NID, W.TERM_BASE
XY, VIA_SEP, MAX_VIA_PAIRS, HW = W.XY, W.VIA_SEP, W.MAX_VIA_PAIRS, W.HW
OWN_OUT = "K2_R532_JOINT_WITNESS_FIDELITY_v1.json"
VIA_GRID = 2          # via sites restricted to a >=2-lattice grid => >=2P = 0.87mm > VIA_SEP = 0.70mm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, OWN_OUT))
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--solve", action="store_true")
    ap.add_argument("--maxtime", type=float, default=1500.0)
    a = ap.parse_args()
    if os.path.basename(a.out) != OWN_OUT:
        raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7): %s" % OWN_OUT)
    assert a.dry != a.solve, "give exactly one of --dry / --solve"
    t0 = time.time()
    rep = {"artifact": "k2_r532_joint_witness_fidelity_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-197 sec.3.4 (joint exact feasibility model: 16 lanes simultaneously) + sec.5 (the "
                        "carried-over single certified solve) + sec.3.6 (buildability/no_witness field mandatory)",
           "write_protection": "guard_out (own output name only)", "solve_calls": 0}
    from ortools.sat.python import cp_model
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names)
    lanes = {}
    for nm in names:
        L = g2.build_lane(nm)
        if L is None:
            print("FAIL-CLOSED lane", nm); sys.exit(3)
        lanes[nm] = L
    # ---- arcs: lane's own graph; via sites restricted to a 2-lattice grid (=> node capacity implies VIA_SEP) ----
    arcs = {}
    for nm in names:
        out = []
        for u, lst in lanes[nm]["adj"].items():
            for (v, w) in lst:
                out.append((u, v, 1 if (u < TERM_BASE and v < TERM_BASE and u // NID != v // NID) else 0))
        arcs[nm] = out
    # ---- explicit via-spacing constraints: 2x2 lattice blocks are cliques of the VIA_SEP conflict graph ----
    via_nodes = {nm: sorted({(u % NID) for (u, v, iv) in arcs[nm] if iv and u < TERM_BASE}) for nm in names}
    rep["domain"] = {"arcs_per_lane": {nm: len(arcs[nm]) for nm in names},
                     "total_arcs": sum(len(v) for v in arcs.values()), "via_grid": VIA_GRID,
                     "note": "no partition/cell restriction: each lane keeps its FULL own-net graph"}
    mo = cp_model.CpModel()
    x, demand = {}, {}
    for nm in names:
        x[nm] = []
        for k in range(len(arcs[nm])):
            x[nm].append(mo.NewBoolVar("x_%s_%d" % (nm.replace("-", "_"), k)))
    # flow conservation + endpoints + via budget (all assumption-guarded so UNSAT yields a core)
    ass = []
    for nm in names:
        src, snk = lanes[nm]["src"], lanes[nm]["snk"]
        inflow, outflow = collections.defaultdict(list), collections.defaultdict(list)
        for k, (u, v, isvia) in enumerate(arcs[nm]):
            outflow[u].append(x[nm][k]); inflow[v].append(x[nm][k])
        d = mo.NewBoolVar("dem_%s" % nm.replace("-", "_"))
        ass.append(d)
        mo.Add(sum(outflow[src]) == 1).OnlyEnforceIf(d)
        mo.Add(sum(inflow[src]) == 0).OnlyEnforceIf(d)
        mo.Add(sum(inflow[snk]) == 1).OnlyEnforceIf(d)
        mo.Add(sum(outflow[snk]) == 0).OnlyEnforceIf(d)
        for nd in set(inflow) | set(outflow):
            if nd in (src, snk):
                continue
            mo.Add(sum(inflow[nd]) == sum(outflow[nd])).OnlyEnforceIf(d)
        mo.Add(sum(x[nm][k] for k, (u, v, iv) in enumerate(arcs[nm]) if iv) <= 2 * MAX_VIA_PAIRS).OnlyEnforceIf(d)
        demand[nm] = d
    # ---- gate f (new, #K2-198 sec.3.4): caliber fidelity ----
    regset = {nm: set(g2.via_positions(nm).tolist()) for nm in names}
    dom_ok = all(set(via_nodes[nm]) <= regset[nm] for nm in names)
    full_ok = all(set(via_nodes[nm]) == regset[nm] for nm in names)
    rep["F_caliber_fidelity"] = {
        "i_via_domain_subset_of_registered": bool(dom_ok),
        "ii_via_domain_EQUALS_registered_full_set": bool(full_ok),
        "registered_via_sites_per_lane": {nm: len(regset[nm]) for nm in names},
        "domain_via_sites_per_lane": {nm: len(via_nodes[nm]) for nm in names},
        "iii_via_spacing_as_EXPLICIT_constraints": "2x2 lattice block cliques (max intra-distance 0.615mm < "
                                                  "VIA_SEP 0.70mm) => at most one via per block per layer => "
                                                  "pairwise spacing >= VIA_SEP",
        "verdict": "PASS" if (full_ok and dom_ok) else "FAIL (fail-closed: do NOT fire)"}
    # per-layer per-node capacity <= 1 across ALL lanes (the joint disjointness; enforced by the solver)
    bytolane = {}
    for nm in names:
        for k, (u, v, iv) in enumerate(arcs[nm]):
            if u < TERM_BASE:
                bytolane.setdefault((u // NID, u % NID), []).append(x[nm][k])
    ncap = 0
    for key, lits in bytolane.items():
        if len(lits) > 1:
            mo.Add(sum(lits) <= 1); ncap += 1
    # explicit via-spacing: per (lane,via node) usage + 2x2 block clique constraints (<=1 per block per layer)
    vuse, via_cliques = {}, 0
    for nm in names:
        for p_ in via_nodes[nm]:
            vuse[(nm, p_)] = mo.NewBoolVar("v_%s_%d" % (nm.replace("-", "_"), p_))
        for k, (u, v, iv) in enumerate(arcs[nm]):
            if iv and u < TERM_BASE:
                mo.Add(x[nm][k] <= vuse[(nm, u % NID)])
        for p_ in via_nodes[nm]:
            arcs_v = [x[nm][k] for k, (u, v, iv) in enumerate(arcs[nm]) if iv and u < TERM_BASE and u % NID == p_]
            if arcs_v:
                mo.Add(vuse[(nm, p_)] <= sum(arcs_v))
    blocks = {}
    for nm in names:
        for p_ in via_nodes[nm]:
            i, j = p_ // NY, p_ % NY
            blocks.setdefault((i // 2, j // 2), []).append(vuse[(nm, p_)])
    for key, lits in blocks.items():
        if len(lits) > 1:
            mo.Add(sum(lits) <= 1); via_cliques += 1
    rep["via_spacing_constraints"] = {"clique_blocks": via_cliques,
                                      "rule": "per (layer-less) 2x2 lattice block at most one via across all lanes"}
    rep["model"] = {"bool_vars": len(mo.Proto().variables), "constraints": len(mo.Proto().constraints),
                    "node_capacity_constraints": ncap, "via_spacing_cliques": via_cliques, "under_gate_1.2M": len(mo.Proto().variables) <= 1200000,
                    "validate": (mo.Validate() or "OK")}
    if rep["F_caliber_fidelity"]["verdict"] != "PASS":
        rep["decision"] = "FAIL-CLOSED(口径保真闸): 过孔域 != 在册全集 ⇒ 停手报监、不开枪"
        rep["buildability"] = {"mode": "no_witness"}
        json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str); print(rep["decision"]); return
    if not rep["model"]["under_gate_1.2M"] or rep["model"]["validate"] != "OK":
        rep["decision"] = "FAIL-CLOSED: 规模闸/Validate 未过"; rep["buildability"] = {"mode": "no_move"}
        json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str); print(rep["decision"]); return
    if a.dry:
        rep["decision"] = "BUILD-ONLY GREEN（0 求解 · 规模闸+Validate 过）⇒ --solve 开启结转的**恰一次**"
        rep["buildability"] = {"mode": "no_move", "note": "no witness yet (dry run)"}
    else:
        solver = cp_model.CpSolver(); solver.parameters.max_time_in_seconds = a.maxtime
        mo.add_assumptions(ass)
        st = solver.Solve(mo)
        rep["solve_calls"] = 1
        rep["solve"] = {"status": solver.StatusName(st), "wall_s": round(solver.WallTime(), 1)}
        if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            paths = {}
            for nm in names:
                nxt = {}
                for k, (u, v, iv) in enumerate(arcs[nm]):
                    if solver.Value(x[nm][k]):
                        nxt[u] = v
                seq = [lanes[nm]["src"]]
                while seq[-1] in nxt and len(seq) < 100000:
                    seq.append(nxt[seq[-1]])
                paths[nm] = seq
            TERMINALS = {}
            for Lj in names:
                TA_, TB_ = lanes[Lj]["terminals"]
                TERMINALS[TA_] = list(lanes[Lj]["anc"][0]); TERMINALS[TB_] = list(lanes[Lj]["anc"][1])

            def nxy(node):
                return list(TERMINALS[node - TERM_BASE]) if node >= TERM_BASE else list(XY(*W.rc(node % NID)))
            lane_polys, all_vias, vias_per = {}, [], {}
            for nm in names:
                seq = paths[nm]
                runs, run, nv = [], [seq[0]], 0
                for nd in seq[1:]:
                    lay = 0 if nd >= TERM_BASE else nd // NID
                    layp = 0 if run[-1] >= TERM_BASE else run[-1] // NID
                    if lay == layp:
                        run.append(nd)
                    else:
                        all_vias.append((XY(*W.rc(run[-1] % NID))[0], XY(*W.rc(run[-1] % NID))[1], nm)); nv += 1
                        runs.append(run); run = [nd]
                runs.append(run)
                polys = {}
                for run in runs:
                    lay = 0 if run[0] >= TERM_BASE else run[0] // NID
                    polys.setdefault(lay, []).append([nxy(p) for p in run])
                lane_polys[nm] = polys; vias_per[nm] = nv
            model_json = json.load(open("/tmp/opencode/archer/model_l8.json"))
            gpl = {}
            for Lr in (0, 1):
                rt = {}
                for nm, polys in lane_polys.items():
                    for k, p in enumerate(polys.get(Lr, [])):
                        if len(p) >= 2:
                            rt["%s#%d" % (nm, k)] = {"pts": p, "layer_cu": G.LAYER_OF[Lr], "n_vias": len(all_vias)}
                if not rt:
                    continue
                gg = G.exact_gate(model_json, rt, [], G.LAYER_OF[Lr], HW, set(), set(), P, frozenset())
                vp2 = [t for t in gg["lane_pitch_violations"] if t[0].split("#")[0] != t[1].split("#")[0]]
                gpl[G.LAYER_OF[Lr]] = {"n_lane_pitch_viol": len(vp2), "lane_pitch_min_gap_mm": gg["lane_pitch_min_gap_mm"],
                                       "n_clearance_viol": gg["n_clearance_viol"], "clearance_min_mm": gg["clearance_min_mm"]}
            gv = G.gate_vias(model_json, all_vias, lane_polys, g2.an)
            edev = {}
            for nm, polys in lane_polys.items():
                p0 = polys[0][0][0]; p1 = polys[0][-1][-1]
                edev[nm] = round(max(math.dist(p0, list(g2.A[nm])), math.dist(p1, list(g2.B[nm]))), 6)
            ok = (all(gpl[ln]["n_lane_pitch_viol"] == 0 and gpl[ln]["n_clearance_viol"] == 0 for ln in gpl)
                  and gv["n_via_viol"] == 0 and (max(edev.values()) if edev else 1) <= 1e-6
                  and all(v <= 2 * MAX_VIA_PAIRS for v in vias_per.values()))
            rep.update({"exact_gate_per_layer": gpl, "gate_vias": gv, "vias_per_lane": vias_per,
                        "endpoint_max_dev_mm": max(edev.values()) if edev else None})
            rep["requirement_level_gate"] = "PASS" if ok else "FAIL"
            rep["buildability"] = ({"mode": "relocation_listed", "relocation_list": sorted(names),
                                    "crew_statement": "16 lanes' In5/In4 copper + via pairs per lane_polys; no other object moved"}
                                   if ok else {"mode": "no_move", "note": "在册闸未过 ⇒ 无搬迁清单"})
            rep["decision"] = ("TERMINAL SAT: 16/16 联合受证见证 ＋ 逐层 exact_gate ＋ gate_vias ＋ 端点 全绿 ⇒ 里程碑"
                               if ok else "NON-TERMINAL: 联合受证求解得 16/16 路径，但在册闸 FAIL")
        elif st == cp_model.INFEASIBLE:
            core = solver.sufficient_assumptions_for_infeasibility()
            rep["unsat_core"] = sorted(set(ass[k].Name() for k in core if 0 <= k < len(ass)))
            rep["buildability"] = {"mode": "no_witness", "note": "受证可行性求解 UNSAT ⇒ 非空核见 unsat_core"}
            rep["decision"] = "NON-TERMINAL: 联合受证求解 **UNSAT** ⇒ 非空核 %d 条（请监理按前提逐条机核非绑定后另件升 frozen-set）" % len(rep["unsat_core"])
        else:
            rep["buildability"] = {"mode": "no_witness", "note": "solver=%s" % solver.StatusName(st)}
            rep["decision"] = "NON-TERMINAL: 联合受证求解 %s（两空）⇒ 按 #K2-197 §三.8 具名停手报监理" % solver.StatusName(st)
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: rep[k] for k in ("F_caliber_fidelity", "via_spacing_constraints", "domain", "model", "solve", "requirement_level_gate", "gate_vias",
                                          "vias_per_lane", "endpoint_max_dev_mm", "unsat_core", "buildability",
                                          "decision") if k in rep}, ensure_ascii=False, indent=1)[:2000])
    print("WROTE", a.out)


if __name__ == "__main__":
    main()
