#!/usr/bin/env python3
"""K2 · R530 —— **见证落格：在册格点/闸模型上的受证可行性求解**（#K2-196 §三.3–5《方法教令》）。

## 令（原文要点）
见证**必须**由**在册格点/闸模型上的受证可行性求解**产出：**得 16/16 见证** 或 **非空 unsat core**；
**贪心/构造性的"best k/16"两不作为**。**闸 f 升级**：不只要证"变量集闭合"，**须证"模型充分"**（约束集足以保证落地可施工）。

## 本件（一次实现，分三步）
1. **抽象→落格的"格胞"（cell）**：取**在册 R529 主问题解**（入口动作 ＋ 三断面槽位 ＋ 行程时刻表）算出每根线的
   **走廊骨架折线**，再取 `cell_i = 自己网逐层合法节点 ∩ 骨架折线 L1 带(R_BAND)`，**按登记序贪心占有**
   ⇒ **cell ⊆ 自己网** ∧ **逐层两两不交**（**由构造保证 ＋ 本件机核**）。格胞只是**变量域**（限制），不是见证。
2. **闸 f（升级版 · 模型充分性 · 只读 · `Solve()=0`）**：三机核 —— (i) 格胞 ⊆ 自己网逐层合法；(ii) 格胞逐层两两不交；
   (iii) **每根线在其格胞内、≤`2*MAX_VIA_PAIRS` 个换层弧、从真源可到真汇**（状态 (node,nvia) 可达性）
   ⇒ 三条全过 ⇒ **"受证求解必得 16/16"** 已被前置证明（**模型充分**）。
3. **恰一次受证求解（CP-SAT · 精确）**：每根线在**自己的格胞弧集**上做**单商品流**（守恒 ＋ 源汇 ＋ 换层弧计数 ≤4），
   整题**一次**求解；解得即 **16 条在册格点上的路径** ⇒ 再用**在册闸**（逐层 `exact_gate` ＋ `gate_vias` ＋ 端点）签字。
   若某线格胞不可行 ⇒ 以该线需求为**假设**取 **非空 unsat core**（格胞级更弱不可行 · 非设计级证书）。
**写保护**：#K2-195 §三.7 `guard_out()`（只允许写自身输出名）。
"""
import argparse, collections, heapq, importlib, json, math, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
W = importlib.import_module("K2_R515_FREETERMINALS_v1")
G = importlib.import_module("K2_R523_LAYERHOP_PARITY_FORMC_v1")
P, X0, Y0, NX, NY, NID, TERM_BASE = W.P, W.X0, W.Y0, W.NX, W.NY, W.NID, W.TERM_BASE
XY, VIA_SEP, MAX_VIA_PAIRS, HW = W.XY, W.VIA_SEP, W.MAX_VIA_PAIRS, W.HW
OWN_OUT = "K2_R530_WITNESS_CERTIFIED_v1.json"
R529 = os.path.join(HERE, "K2_R529_WOVEN_COMPLETE_MASTER_v1.json")
R_BAND = 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, OWN_OUT))
    ap.add_argument("--band", type=int, default=R_BAND)
    ap.add_argument("--build-only", action="store_true")
    ap.add_argument("--solve", action="store_true", help="恰一次受证求解（#K2-196 §三.4 新授一次）")
    ap.add_argument("--maxtime", type=float, default=900.0)
    a = ap.parse_args()
    if os.path.basename(a.out) != OWN_OUT:
        raise SystemExit("REFUSED (write-protection): target is not this artifact's own output (%s)" % OWN_OUT)
    t0 = time.time()
    rep = {"artifact": "k2_r530_witness_certified_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-196 sec.3.3-5 (witness MUST come from a certified feasibility solve on the registered "
                        "lattice/gate model: 16/16 witness OR non-empty unsat core; gate f upgraded to model "
                        "SUFFICIENCY; one newly granted solve)", "solve_calls": 0}
    from ortools.sat.python import cp_model

    master = json.load(open(R529))
    schedule, entrance, sect = master["schedule"], master["entrance_actions"], master["section_slots"]
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names)
    order_ax = sorted(names, key=lambda nm: g2.A[nm][0])
    lanes = {}
    for nm in names:
        L = g2.build_lane(nm)
        if L is None:
            print("FAIL-CLOSED: lane build", nm); sys.exit(3)
        lanes[nm] = L
    rep["source_master"] = os.path.basename(R529)

    def seg_dist_all(xs, ys, ax, ay, bx, by):
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        if L2 <= 0:
            return __import__("numpy").hypot(xs - ax, ys - ay)
        import numpy as np
        t = np.clip(((xs - ax) * dx + (ys - ay) * dy) / L2, 0.0, 1.0)
        return np.hypot(xs - (ax + t * dx), ys - (ay + t * dy))

    import numpy as np
    ii, jj = np.meshgrid(np.arange(NX), np.arange(NY), indexing="ij")
    xs = (X0 + ii * P).reshape(-1).astype(float)
    ys = (Y0 + jj * P).reshape(-1).astype(float)

    # ---------- step 1: cell = own-legal ∩ L1 band of the solved corridor polyline, greedy-claimed ----------
    def polyline(nm):
        A = tuple(g2.A[nm]); B = tuple(g2.B[nm]); east = g2.grp[nm] == "east"
        sl = sect[nm]; ent = entrance[nm]
        e0 = (node_xy_(ent["via"] if ent["kind"] == "DIVE" else ent["node"]))
        pts = [A, e0, (X0 + 33 * P, Y0 + sl["col33"] * P), (X0 + 60 * P, Y0 + sl["col60"] * P)]
        if east:
            pts.append((X0 + sl["exit"] * P, Y0 + 36 * P)); pts.append((B[0], Y0 + 36 * P))
        else:
            pts.append((X0 + 114 * P, Y0 + sl["exit"] * P)); pts.append((B[0], Y0 + sl["exit"] * P))
        pts.append(B)
        return pts

    def node_xy_(p):
        return (X0 + (p // NY) * P, Y0 + (p % NY) * P)

    RB = a.band
    claimed = {0: set(), 1: set()}
    cells = {}
    for nm in order_ax:
        pts = polyline(nm)
        touch = set()
        for k in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[k], pts[k + 1]
            steps = max(1, int(math.ceil(max(abs(bx - ax), abs(by - ay)) / P)))
            for t in range(steps + 1):
                cx = ax + (bx - ax) * t / steps; cy = ay + (by - ay) * t / steps
                ci, cj = int(round((cx - X0) / P)), int(round((cy - Y0) / P))
                for di in range(-RB, RB + 1):
                    for dj in range(-RB, RB + 1):
                        u, v = ci + di, cj + dj
                        if 0 <= u < NX and 0 <= v < NY:
                            touch.add(u * NY + v)
        cell = {}
        for L in (0, 1):
            own = set(np.nonzero(g2._nok[(nm, L)].reshape(-1))[0].tolist())
            c = (own & touch) - claimed[L]
            cell[L] = c
            claimed[L] |= c
        cells[nm] = cell
    a1 = all(cells[nm][L] <= set(np.nonzero(g2._nok[(nm, L)].reshape(-1))[0].tolist()) for nm in names for L in (0, 1))
    a2 = True
    for L in (0, 1):
        seen = set()
        for nm in names:
            if cells[nm][L] & seen:
                a2 = False
            seen |= cells[nm][L]

    # ---------- step 2 (gate f upgraded): per-lane sufficiency inside its own cell ----------
    def cell_arcs(nm):
        """directed arcs (u,v,w,kind,via_pos) inside the lane's cell (legs allowed if their node is in cell)."""
        out = []
        for u, lst in lanes[nm]["adj"].items():
            for (v, w) in lst:
                if u >= TERM_BASE:
                    if (v % NID) in cells[nm][v // NID]:
                        out.append((u, v, w, "leg", None))
                    continue
                if v >= TERM_BASE:
                    if (u % NID) in cells[nm][u // NID]:
                        out.append((u, v, w, "leg", None))
                    continue
                if u // NID != v // NID:
                    if (u % NID) in cells[nm][u // NID] and (v % NID) in cells[nm][v // NID]:
                        out.append((u, v, w, "via", u % NID))
                    continue
                if (u % NID) in cells[nm][u // NID] and (v % NID) in cells[nm][v // NID]:
                    out.append((u, v, w, "lat", None))
        return out

    arcs = {nm: cell_arcs(nm) for nm in names}
    rep["cells"] = {"R_BAND": RB,
                    "cell_nodes": {nm: {"In5": len(cells[nm][0]), "In4": len(cells[nm][1])} for nm in names},
                    "cell_arcs": {nm: len(arcs[nm]) for nm in names}}

    def suff(nm):
        """(node,nvia) reachability src->snk inside the cell, <=2*MAX_VIA_PAIRS via arcs (exact, polynomial)."""
        adj = collections.defaultdict(list)
        for (u, v, w, kind, vp) in arcs[nm]:
            adj[u].append((v, 1 if kind == "via" else 0))
        src, snk = lanes[nm]["src"], lanes[nm]["snk"]
        best = {(src, 0): 0.0}; pq = [(0.0, src, 0)]
        while pq:
            d, u, nv = heapq.heappop(pq)
            if d > best.get((u, nv), 1e18) + 1e-12:
                continue
            if u == snk:
                return True, nv
            for (v, isvia) in adj[u]:
                n2 = nv + isvia
                if n2 > 2 * MAX_VIA_PAIRS:
                    continue
                if (v, n2) not in best:
                    best[(v, n2)] = d + 1
                    heapq.heappush(pq, (d + 1, v, n2))
        return False, None

    suff_res = {}
    for nm in names:
        ok, nv = suff(nm)
        suff_res[nm] = {"cell_connects_src_to_snk_within_via_budget": bool(ok), "min_via_arcs": nv,
                        "cell_arcs": len(arcs[nm])}
    n_ok = sum(1 for nm in names if suff_res[nm]["cell_connects_src_to_snk_within_via_budget"])
    rep["F_model_sufficiency"] = {
        "i_cells_subset_of_own_registered_legal_per_layer": bool(a1),
        "ii_cells_pairwise_disjoint_per_layer": bool(a2),
        "iii_every_lane_connected_inside_its_own_cell_within_via_budget": "%d/%d" % (n_ok, len(names)),
        "per_lane": suff_res,
        "so": ("if all three hold, the certified solve on these variables MUST return 16/16 paths on the "
               "registered lattice; if any lane's cell is insufficient => fail-closed, do NOT spend the shot"),
        "verdict": "PASS" if (a1 and a2 and n_ok == len(names)) else "FAIL"}

    if not (a1 and a2):
        rep["decision"] = "FAIL-CLOSED: 格胞两性质未过 ⇒ 不求解"
    elif n_ok != len(names):
        bad = [nm for nm in names if not suff_res[nm]["cell_connects_src_to_snk_within_via_budget"]]
        rep["decision"] = "FAIL-CLOSED(闸 f 充分性): 下列线在自己格胞内不可达 ⇒ 不花那一枪（先修格胞构造）: %s" % bad
    elif not a.solve:
        rep["decision"] = ("BUILD-ONLY GREEN（格胞 ⊆自己网 ∧ 逐层不交 ∧ 16/16 格胞内可达 ⇒ **模型充分**）"
                           "⇒ 由 --solve 开启**恰一次**受证求解")
    else:
        # ---------- step 3: the single certified solve (exact flow per lane inside its own cell) ----------
        mo = cp_model.CpModel()
        chosen = {}
        ass = []
        for nm in names:
            x = {}
            inflow, outflow = collections.defaultdict(list), collections.defaultdict(list)
            for k, (u, v, w, kind, vp) in enumerate(arcs[nm]):
                b = mo.NewBoolVar("x_%s_%d" % (nm.replace("-", "_"), k))
                x[k] = b; outflow[u].append(b); inflow[v].append(b)
            src, snk = lanes[nm]["src"], lanes[nm]["snk"]
            mo.Add(sum(outflow[src]) == 1); mo.Add(sum(inflow[src]) == 0)
            mo.Add(sum(inflow[snk]) == 1); mo.Add(sum(outflow[snk]) == 0)
            nodes = set(outflow) | set(inflow)
            for nd in nodes:
                if nd in (src, snk):
                    continue
                mo.Add(sum(inflow[nd]) == sum(outflow[nd]))
            lv = mo.NewBoolVar("dem_%s" % nm.replace("-", "_"))
            mo.Add(sum(x[k] for k, (u, v, w, kind, vp) in enumerate(arcs[nm]) if kind == "via")
                   <= 2 * MAX_VIA_PAIRS).OnlyEnforceIf(lv)
            mo.Add(sum(x[k] for k, (u, v, w, kind, vp) in enumerate(arcs[nm])) >= 1).OnlyEnforceIf(lv)
            ass.append(lv)
            chosen[nm] = (x, arcs[nm], lv)
        mo.Minimize(sum(len(arcs[nm]) * 0 for nm in names))
        solver = cp_model.CpSolver(); solver.parameters.max_time_in_seconds = a.maxtime
        mo.add_assumptions(ass)
        st = solver.Solve(mo)
        rep["solve_calls"] = 1
        rep["solve"] = {"status": solver.StatusName(st), "wall_s": round(solver.WallTime(), 1),
                        "model_vars": len(mo.Proto().variables), "model_cons": len(mo.Proto().constraints)}
        if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            paths = {}
            for nm in names:
                x, ar, lv = chosen[nm]
                sel = [k for k in x if solver.Value(x[k])]
                # rebuild node sequence from the selected arcs
                nxt = {}
                for k in sel:
                    u, v, w, kind, vp = ar[k]
                    nxt[u] = (v, kind, vp)
                seq = [lanes[nm]["src"]]
                while seq[-1] in nxt:
                    seq.append(nxt[seq[-1]][0])
                paths[nm] = seq
            rep["paths"] = {nm: len(paths[nm]) for nm in names}
            # ---- registered gate signature ----
            lane_polys, all_vias = {}, []
            for nm in names:
                seq = paths[nm]
                TERMINALS = {}
                for Lj in names:
                    TA_, TB_ = lanes[Lj]["terminals"]
                    TERMINALS[TA_] = list(lanes[Lj]["anc"][0]); TERMINALS[TB_] = list(lanes[Lj]["anc"][1])

                def nxy(node):
                    return list(TERMINALS[node - TERM_BASE]) if node >= TERM_BASE else list(XY(*W.rc(node % NID)))
                runs, run = [], [seq[0]]
                for nd in seq[1:]:
                    lay = 0 if nd >= TERM_BASE else nd // NID
                    layp = 0 if run[-1] >= TERM_BASE else run[-1] // NID
                    if lay == layp:
                        run.append(nd)
                    else:
                        all_vias.append((XY(*W.rc(run[-1] % NID))[0], XY(*W.rc(run[-1] % NID))[1], nm))
                        runs.append(run); run = [nd]
                runs.append(run)
                polys = {}
                for run in runs:
                    lay = 0 if run[0] >= TERM_BASE else run[0] // NID
                    polys.setdefault(lay, []).append([nxy(p) for p in run])
                lane_polys[nm] = polys
            model_json = json.load(open("/tmp/opencode/archer/model_l8.json"))
            gate_per_layer = {}
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
                gate_per_layer[G.LAYER_OF[Lr]] = {"n_lane_pitch_viol": len(vp2),
                                                  "lane_pitch_min_gap_mm": gg["lane_pitch_min_gap_mm"],
                                                  "n_clearance_viol": gg["n_clearance_viol"],
                                                  "clearance_min_mm": gg["clearance_min_mm"]}
            gv = G.gate_vias(model_json, all_vias, lane_polys, g2.an)
            edev = {}
            for nm, polys in lane_polys.items():
                p0 = polys[0][0][0]; p1 = polys[0][-1][-1]
                edev[nm] = round(max(math.dist(p0, list(g2.A[nm])), math.dist(p1, list(g2.B[nm]))), 6)
            ok = (all(gate_per_layer[ln]["n_lane_pitch_viol"] == 0 and gate_per_layer[ln]["n_clearance_viol"] == 0
                      for ln in gate_per_layer) and gv["n_via_viol"] == 0
                  and (max(edev.values()) if edev else 1) <= 1e-6
                  and all(sum(1 for v in all_vias if v[2] == nm) <= 2 * MAX_VIA_PAIRS for nm in names))
            rep["exact_gate_per_layer"] = gate_per_layer; rep["gate_vias"] = gv
            rep["endpoint_max_dev_mm"] = max(edev.values()) if edev else None
            rep["vias_per_lane"] = {nm: sum(1 for v in all_vias if v[2] == nm) for nm in names}
            rep["requirement_level_gate"] = "PASS" if ok else "FAIL"
            rep["buildability"] = ({"mode": "relocation_listed",
                                    "relocation_list": sorted(names),
                                    "note": "16/16 lanes' In5/In4 copper + via pairs as listed; no other object moved"}
                                   if ok else {"mode": "no_move", "note": "闸未过 ⇒ 无搬迁清单"})
            rep["decision"] = ("TERMINAL SAT: 16/16 受证见证（在册格点/闸模型上求解得到）＋ 逐层 exact_gate ＋ gate_vias ＋ 端点 全绿 ⇒ 里程碑"
                               if ok else "NON-TERMINAL: 受证求解得 16/16 路径，但在册闸 FAIL（见明细）")
        elif st == cp_model.INFEASIBLE:
            rep["unsat_core"] = [a_.Name() for a_ in solver.sufficient_assumptions_for_infeasibility()][:20]
            rep["decision"] = ("非空 unsat core（%d 条 · 格胞级更弱不可行 · 非设计级证书）：受证求解确认在这些格胞内无 16/16 路径"
                               % len(rep["unsat_core"]))
        else:
            rep["decision"] = "受证求解 %s（无结论）⇒ 按 #K2-196 §三.6 具名停手报监理" % solver.StatusName(st)
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: rep[k] for k in ("cells", "F_model_sufficiency", "solve", "requirement_level_gate",
                                          "endpoint_max_dev_mm", "vias_per_lane", "unsat_core", "decision") if k in rep},
                     ensure_ascii=False, indent=1)[:2500])
    print("WROTE", a.out)


if __name__ == "__main__":
    main()
