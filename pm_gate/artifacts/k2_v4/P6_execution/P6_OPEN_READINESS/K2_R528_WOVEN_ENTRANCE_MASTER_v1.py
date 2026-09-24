#!/usr/bin/env python3
"""K2 · R528 —— **编织式丙′ 精化主问题**（#K2-194 §三.3 已批：把「入口站选择」升为主问题变量）：
打捆容量 ＋ 行程时刻表 ＋ 反序层分离 ＋ **入口动作（在册过孔站 / In5 下降列）选择**；build-only 先过闸 → **恰一次**受证求解。

## 依据（在册 · 不重走）
- **R526**（受理 · 未完成）：排程层 **SAT/OPTIMAL**；卡点移到**入口带**；构造式路由 5/16，残余仅 7–9 弧。
- **R527**（受理 · 零额度事实）：每根线锚点旁 **0.03–0.26mm** 即有在册合法过孔站（**16/16** 近距 · **15/16** 最坏情形带内可达）
  ⇒ **在册口径够用**，**不**放宽任何编码（#K2-194 §三.7② 明确不准放宽）。
- **#K2-194 §三.3**：把「谁用哪个入口孔」**交给方案算** —— 本件即该精化（**非换族/非改判据/非动冻结件**）。

## 本件主问题（精化后 · 仍是小整数问题）
原 R526 三族（打捆容量 · 时刻表 · 58 反序层分离）**不变**；**新增**：
- 每根线一个**入口动作**（one-hot）：
  · `In5@c`：在 `c` 列（锚列 ±2 内，且在册合法）下降 —— 动作 1 个；
  · `DIVE@v`：在**在册过孔站** `v`（COMB 区内、锚点 ≤2 格内、在册合法）**带内下沉到 In4** —— 至多 6 个候选。
- **一致性**：`Σ_{dive 动作} act = on4_i[COMB]`（时刻表说它在 COMB 在 In4 ⇒ 必须有个入口孔；反之必须走 In5 列）。
- **两两不冲突**（机核预计算 · 声明集口径）：两条入口动作的**逐层声明集**相交、或两孔中心距 < `VIA_SEP` ⇒ 二者互斥。
  （`act[i][k] + act[j][l] <= 1`）—— 这正是 R526 残余 7–9 弧的**机核根因约束**，现在**前置到主问题**。
**目标**：`100000·#行程 + 1000·行程站数 + Σ入口腿长(0.1mm 计)`（少走二层 ≫ 行程短 ≫ 入口腿短）。
**闸**：a 前置只读保真自检（`Solve()=0`）· b build-only **0 求解** · c **恰一次**（#K2-194 §三.4 **新授一次**）· d/e 由路由件出。
"""
import argparse, importlib, itertools, json, math, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
F = importlib.import_module("K2_R523_LAYERHOP_PARITY_FORMC_v1")

P, X0, Y0, NX, NY, NID = F.P, F.X0, F.Y0, F.NX, F.NY, F.NID
YARD_ROWS = list(range(38, 58))
STATIONS = ["COMB", "BELT", "WALL", "FIELD"]
SCALE_GATE = 1_200_000
MAX_DIVE_CANDS = 6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "K2_R528_WOVEN_ENTRANCE_MASTER_v1.json"))
    ap.add_argument("--build-only", action="store_true")
    ap.add_argument("--solve", action="store_true", help="**恰一次**受证求解（#K2-194 §三.4 新授一次）")
    ap.add_argument("--maxtime", type=float, default=900.0)
    a = ap.parse_args()
    t0 = time.time()
    rep = {"artifact": "k2_r528_woven_entrance_master_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-194 sec.3.3 (promote entrance-station selection into the master; same approved family) "
                        "+ sec.3.4 (ONE newly granted certified solve) + sec.3.5 gates a-e",
           "stations": STATIONS, "solve_calls": 0}

    from ortools.sat.python import cp_model
    g2 = F.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names)
    n = len(names)
    idx = {nm: i for i, nm in enumerate(names)}
    order_ax = sorted(names, key=lambda nm: g2.A[nm][0])
    atlas = json.load(open(os.path.join(HERE, "K2_R525_INVERSION_ATLAS_v1.json")))
    inv = [(d["pair"][0], d["pair"][1]) for d in atlas["inversion_detail"]]

    # ---------- machine-derived packing capacities (same rule as R526) ----------
    ax = [g2.A[nm][0] for nm in names]
    spans = [max(ax) - min(ax), F.ZONES[1][3] - F.ZONES[1][1], F.ZONES[2][3] - F.ZONES[2][1],
             F.ZONES[3][3] - F.ZONES[3][1]]
    cap = [int(s // (2 * P)) + 1 for s in spans]
    rep["packing_capacity"] = {"rule": "cap[t]=floor(span_perp[t]/(2P))+1", "cap_per_station": dict(zip(STATIONS, cap))}

    # ---------- entrance-action candidates per lane (machine, from the registered geometry) ----------
    def zone_of_pos(p):
        i, j = p // NY, p % NY
        x, y = X0 + i * P, Y0 + j * P
        for k, (x0, y0, x1, y1) in enumerate(F.ZONES):
            if x0 - 1e-9 <= x <= x1 + 1e-9 and y0 - 1e-9 <= y <= y1 + 1e-9:
                return k
        return None

    def node_xy(p):
        return (X0 + (p // NY) * P, Y0 + (p % NY) * P)

    yard = {}          # nested yard row per lane (the R525/R526 "zero-interlock" structure)
    for k, nm in enumerate(order_ax):
        yard[nm] = YARD_ROWS[len(order_ax) - 1 - k]

    own0 = {nm: g2._nok[(nm, 0)] for nm in names}
    own1 = {nm: g2._nok[(nm, 1)] for nm in names}
    edgeset = {}
    for nm in names:
        em = g2._eok[(nm, 0)]
        edgeset[nm] = {(int(u), int(v)) for u, v in zip(g2.edge_u[em].tolist(), g2.edge_v[em].tolist())}

    def lattice_path(x0, y0, x1, y1):
        """lattice nodes traversed by the segment (rasterised at P), plus its consecutive edges."""
        steps = max(1, int(math.ceil(max(abs(x1 - x0), abs(y1 - y0)) / P)))
        nodes = []
        for t in range(steps + 1):
            i = int(round((x0 + (x1 - x0) * t / steps - X0) / P))
            j = int(round((y0 + (y1 - y0) * t / steps - Y0) / P))
            nd = i * NY + j
            if not nodes or nodes[-1] != nd:
                nodes.append(nd)
        return nodes

    adj0 = {}
    for nm in names:
        adj_one = {}
        for (u, v) in edgeset[nm]:
            adj_one.setdefault(u, set()).add(v)
            adj_one.setdefault(v, set()).add(u)
        adj0[nm] = adj_one

    def connected_on_In5(nm, src, dst, cap=20000):
        """is dst reachable from src inside the lane's OWN registered In5 graph (candidate soundness)?"""
        if not (own0[nm][src] and own0[nm][dst]):
            return False
        seen = {src}; st = [src]
        while st:
            u = st.pop()
            if u == dst:
                return True
            for v in adj0[nm].get(u, ()):
                if v not in seen:
                    seen.add(v); st.append(v)
                    if len(seen) > cap:
                        return False
        return False

    acts = {}          # lane -> list of action dicts
    dropped = {}
    cand_dbg = {}
    for nm in names:
        A = tuple(g2.A[nm])
        ia, ja = int(round((A[0] - X0) / P)), int(round((A[1] - Y0) / P))
        lst = []
        # (1) In5 action: use the lane's REGISTERED free-access leg nodes (F1: nodes within R_REACH whose
        #     straight leg is legal), clustered by lattice column; the chosen column must let the lane's OWN
        #     In5 graph reach its belt row. This replaces "descend at the anchor column" with a *selected*
        #     entrance column => exactly the decision #K2-194 sec.3.3 promotes into the master.
        import numpy as _np
        dbg = {"near": 0, "seg_ok": 0, "cols": 0, "belt_connected": 0}
        idx_ok = _np.argwhere(own0[nm].reshape(NX, NY))
        xy = _np.stack([X0 + idx_ok[:, 0] * P, Y0 + idx_ok[:, 1] * P], 1)
        dd = _np.hypot(xy[:, 0] - A[0], xy[:, 1] - A[1])
        bycol = {}
        dbg["near"] = int((dd <= F.R_REACH).sum())
        for (i, j) in idx_ok[dd <= F.R_REACH].tolist():
            if not g2.g0.seg_ok(A, (X0 + i * P, Y0 + j * P), g2.g0.pt_by_net[nm]):
                continue
            dbg["seg_ok"] += 1
            p_ = i * NY + j
            d_ = float(math.hypot(X0 + i * P - A[0], Y0 + j * P - A[1]))
            bycol.setdefault(i, []).append((d_, p_, j))
        cols = sorted(bycol.keys(), key=lambda c_: min(x[0] for x in bycol[c_]))[:5]
        dbg["cols"] = len(cols)
        for c in cols:
            d_, p_, j_ = min(bycol[c])
            dst_row = yard[nm]
            if not connected_on_In5(nm, p_, c * NY + dst_row):
                continue                    # the lane's own In5 graph must link this leg node to its belt row
            dbg["belt_connected"] += 1
            top = (X0 + c * P, Y0 + j_ * P); bot_y = Y0 + dst_row * P
            cl = set(F.claim_seg(top[0], top[1], top[0], bot_y)) | set(F.claim_seg(A[0], A[1], top[0], top[1]))
            lst.append({"kind": "In5", "col": c, "layer": 0, "node": p_, "dist": round(d_, 4),
                        "claim": cl, "via": None})
        # (2) DIVE at a registered COMB via site within <=2 lattice of the anchor
        cands = []
        for p in g2.via_positions(nm).tolist():
            if zone_of_pos(p) != 0:
                continue
            i, j = p // NY, p % NY
            if abs(i - ia) <= 2 and abs(j - ja) <= 2:
                cands.append((math.hypot(X0 + i * P - A[0], Y0 + j * P - A[1]), p))
        cands.sort()
        for d_mm, p in cands[:MAX_DIVE_CANDS]:
            px, py = node_xy(p)
            cl = set(F.claim_seg(A[0], A[1], px, py))
            # registered free-access leg (F1): the straight leg must be legal, and the dive node must be
            # legal on BOTH layers and registered via-capable (in the four wide zones)
            if not g2.g0.seg_ok(A, (px, py), g2.g0.pt_by_net[nm]):
                continue
            if not (own0[nm][p] and own1[nm][p] and g2._viaok[nm][p]):
                continue
            lst.append({"kind": "DIVE", "col": p // NY, "layer": 1, "node": p, "dist": d_mm, "claim": cl, "via": p})
        acts[nm] = lst
        cand_dbg[nm] = dbg
        if not [x for x in lst if x["kind"] == "In5"] or not [x for x in lst if x["kind"] == "DIVE"]:
            dropped[nm] = {"In5": len([x for x in lst if x["kind"] == "In5"]),
                           "DIVE": len([x for x in lst if x["kind"] == "DIVE"])}
    rep["entrance_candidates"] = {nm: {"n_actions": len(acts[nm]),
                                       "In5_cols": [x["col"] for x in acts[nm] if x["kind"] == "In5"],
                                       "dive_sites": [{"node": x["node"], "x_mm": round(node_xy(x["node"])[0], 3),
                                                       "y_mm": round(node_xy(x["node"])[1], 3),
                                                       "dist_mm": round(x["dist"], 3)}
                                                      for x in acts[nm] if x["kind"] == "DIVE"]}
                                   for nm in names}
    rep["candidate_failures"] = dropped
    rep["candidate_debug"] = cand_dbg

    # ---------- exact pairwise conflict matrix over candidate actions (declaration-set rule) ----------
    conf = {}       # (i,k,j,l) -> reason
    for i in range(n):
        for j in range(i + 1, n):
            for ki, Ai in enumerate(acts[names[i]]):
                for kj, Aj in enumerate(acts[names[j]]):
                    why = None
                    if Ai["claim"] & Aj["claim"]:
                        why = "claim_overlap"
                    elif Ai["via"] is not None and Aj["via"] is not None and \
                            math.dist(node_xy(Ai["via"]), node_xy(Aj["via"])) < F.VIA_SEP - 1e-9:
                        why = "via_sep"
                    if why:
                        conf[(i, ki, j, kj)] = why
    rep["entrance_conflicts"] = {"n_conflicting_action_pairs": len(conf),
                                 "by_reason": {r: sum(1 for v in conf.values() if v == r)
                                               for r in sorted(set(conf.values()))}}

    # ---------- model ----------
    mo = cp_model.CpModel()
    start, end, on4, usexc = {}, {}, {}, {}
    for i in range(n):
        start[i] = {s: mo.NewBoolVar("start_%d_%d" % (i, s)) for s in range(5)}
        end[i] = {s: mo.NewBoolVar("end_%d_%d" % (i, s)) for s in range(5)}
        mo.Add(sum(start[i].values()) == 1); mo.Add(sum(end[i].values()) == 1)
        mo.Add(sum(s * start[i][s] for s in range(5)) <= sum(s * end[i][s] for s in range(5)))
        mo.Add(start[i][4] == end[i][4])
        on4[i] = {}
        for t in range(4):
            on4[i][t] = mo.NewBoolVar("on4_%d_%d" % (i, t))
            A_ = sum(start[i][s] for s in range(t + 1)); B_ = sum(end[i][s] for s in range(t, 5))
            mo.Add(on4[i][t] <= A_); mo.Add(on4[i][t] <= B_); mo.Add(on4[i][t] >= A_ + B_ - 1)
        usexc[i] = mo.NewBoolVar("usexc_%d" % i); mo.Add(usexc[i] == 1 - start[i][4])
    ass_cap = []
    for t in range(4):
        lb = mo.NewBoolVar("cap_In5_%d" % t); ass_cap.append(lb)
        mo.Add(sum(1 - on4[i][t] for i in range(n)) <= cap[t]).OnlyEnforceIf(lb)
        lb2 = mo.NewBoolVar("cap_In4_%d" % t); ass_cap.append(lb2)
        mo.Add(sum(on4[i][t] for i in range(n)) <= cap[t]).OnlyEnforceIf(lb2)
    ass_pair = []
    for (ni, nj) in inv:
        i, j = idx[ni], idx[nj]
        sep = {}
        for t in range(4):
            b = mo.NewBoolVar("sep_%d_%d_%d" % (i, j, t))
            mo.Add(b >= on4[i][t] - on4[j][t]); mo.Add(b >= on4[j][t] - on4[i][t])
            mo.Add(b <= on4[i][t] + on4[j][t]); mo.Add(b <= 2 - on4[i][t] - on4[j][t])
            sep[t] = b
        lb = mo.NewBoolVar("sepneed_%d_%d" % (i, j)); ass_pair.append(lb)
        mo.Add(sum(sep.values()) >= lb)
    # ---- NEW: entrance action variables ----
    act = {}
    for i in range(n):
        act[i] = [mo.NewBoolVar("act_%d_%d" % (i, k)) for k in range(len(acts[names[i]]))]
        mo.Add(sum(act[i]) == 1)
        dive_idx = [k for k, x in enumerate(acts[names[i]]) if x["kind"] == "DIVE"]
        in5_idx = [k for k, x in enumerate(acts[names[i]]) if x["kind"] == "In5"]
        mo.Add(sum(act[i][k] for k in dive_idx) == on4[i][0])       # dive iff the time table says In4 at COMB
        mo.Add(sum(act[i][k] for k in in5_idx) == 1 - on4[i][0])
    for (i, ki, j, kj), _why in conf.items():
        mo.Add(act[i][ki] + act[j][kj] <= 1)
    mo.Minimize(100000 * sum(usexc.values())
                + 1000 * sum(sum(t * end[i][t] for t in range(4)) - sum(t * start[i][t] for t in range(4))
                             for i in range(n))
                + sum(int(round(10 * x["dist"])) * act[i][k] for i in range(n)
                      for k, x in enumerate(acts[names[i]])))
    proto = mo.Proto()
    rep["master_model"] = {"bool_vars": len(proto.variables), "constraints": len(proto.constraints),
                           "under_gate": len(proto.variables) <= SCALE_GATE, "scale_gate": SCALE_GATE,
                           "validate": (mo.Validate() or "OK")}
    # fidelity self-check (gate a, read-only, 0 solves): every candidate action is inside the lane's OWN legal set
    # The claim tube is a KEEP-OUT FOOTPRINT (used for the pairwise conflict matrix), NOT a legality
    # requirement: the actual track only occupies the nodes it passes. What must be machine-verified is:
    #  - In5 action: the leg node is own-legal and its own In5 graph links it to the lane's belt row;
    #  - DIVE action: the registered free-access leg is legal and the node is own-legal on BOTH layers and
    #    registered via-capable (four wide zones).
    ok_a = True
    fail_detail = []
    for nm in names:
        A_ = tuple(g2.A[nm])
        for x in acts[nm]:
            if x["kind"] == "In5":
                if not (own0[nm][x["node"]] and connected_on_In5(nm, x["node"], x["col"] * NY + yard[nm])):
                    ok_a = False; fail_detail.append((nm, "In5", x["col"]))
            else:
                p_ = x["via"]
                if not (own0[nm][p_] and own1[nm][p_] and g2._viaok[nm][p_]
                        and g2.g0.seg_ok(A_, node_xy(p_), g2.g0.pt_by_net[nm])):
                    ok_a = False; fail_detail.append((nm, "DIVE", p_))
    rep["A_fidelity_selfcheck"] = {
        "all_candidate_actions_within_own_registered_legal_per_layer": bool(ok_a),
        "so": "master SAT => the chosen entrance actions are own-legal and pairwise claim-compatible by "
              "construction; the routing then only needs to realise them (registered gates still fail-closed)",
        "failures": fail_detail[:20], "verdict": "PASS" if ok_a else "FAIL"}
    rep["build_only"] = True
    if not rep["master_model"]["under_gate"] or rep["master_model"]["validate"] != "OK" or not ok_a:
        rep["decision"] = "FAIL-CLOSED: 规模闸/Validate/保真自检 未过 ⇒ 不求解"
        json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str); print(rep["decision"]); return
    if not a.solve:
        rep["decision"] = "BUILD-ONLY GREEN（规模闸 + Validate + 保真自检过 · Solve() 0 次）⇒ 由 --solve 开启**新授的那恰一次**"
        json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
        print(json.dumps({k: rep[k] for k in ("packing_capacity", "entrance_conflicts", "candidate_failures",
                                             "master_model", "A_fidelity_selfcheck", "decision")},
                         ensure_ascii=False, indent=1)[:2500])
        print("WROTE", a.out); return
    solver = cp_model.CpSolver(); solver.parameters.max_time_in_seconds = a.maxtime
    assumptions = ass_cap + ass_pair
    capnames = (["cap_In5_%d" % t for t in range(4)] + ["cap_In4_%d" % t for t in range(4)])
    ass_names = capnames + ["inversion_separation:%s|%s" % (inv[k][0], inv[k][1]) for k in range(len(ass_pair))]
    mo.add_assumptions(assumptions)
    st = solver.Solve(mo)
    rep["solve_calls"] = 1
    rep["solve"] = {"status": solver.StatusName(st), "wall_s": round(solver.WallTime(), 1),
                    "objective": (int(solver.ObjectiveValue()) if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None)}
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        sch, chosen = {}, {}
        for i, nm in enumerate(names):
            on = [t for t in range(4) if solver.Value(on4[i][t])]
            sch[nm] = {"stations_on_In4": [STATIONS[t] for t in on],
                       "start_station": (None if solver.Value(start[i][4]) else
                                         STATIONS[min(s for s in range(4) if solver.Value(start[i][s]))]),
                       "end_station": (None if solver.Value(end[i][4]) else
                                       STATIONS[max(s for s in range(4) if solver.Value(end[i][s]))])}
            k = next(k for k in range(len(act[i])) if solver.Value(act[i][k]))
            x = acts[nm][k]
            chosen[nm] = {kk: vv for kk, vv in x.items() if kk != "claim"}
            chosen[nm]["action_index"] = k
        rep["schedule"] = sch; rep["entrance_actions"] = chosen
        rep["lanes_on_In4_per_station"] = {STATIONS[t]: sum(1 for nm in names if STATIONS[t] in sch[nm]["stations_on_In4"])
                                           for t in range(4)}
        rep["decision"] = ("REFINED MASTER SAT（恰一次受证求解 %s · wall=%.1fs）：打捆+时刻表+反序分离+**入口动作两两不冲突** 全部满足"
                           % (solver.StatusName(st), solver.WallTime()))
    elif st == cp_model.INFEASIBLE:
        core = list(solver.sufficient_assumptions_for_infeasibility())
        rep["unsat_core"] = [ass_names[k] for k in core if 0 <= k < len(ass_names)]
        rep["decision"] = ("REFINED MASTER UNSAT（INFEASIBLE）：非空核 %d 条（调度级更弱不可行 · 非设计级证书）"
                           % len(rep["unsat_core"]))
    else:
        rep["decision"] = "REFINED MASTER %s（无结论）⇒ 按 #K2-194 §三.6 具名停手报监理" % solver.StatusName(st)
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: rep[k] for k in ("solve", "lanes_on_In4_per_station", "entrance_actions",
                                          "unsat_core", "decision") if k in rep}, ensure_ascii=False, indent=1)[:2500])
    print("WROTE", a.out)


if __name__ == "__main__":
    main()
