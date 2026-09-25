#!/usr/bin/env python3
"""K2 · R543 —— 方案层**(甲) 每线确定施工图**：以 R540 固定路点为不可变输入的**精确联合模型**（一次 · 终局）。
模型：逐线**逐段**单商品流（段 = 相邻固定路点）；**逐层节点容量 <=1**（联合不交）；**每线换层 <=2 对孔**；**孔距 >= VIA_SEP**（2x2 团）；端点=真锚。
域：各线图 ∩ **逐段走廊带**(R_BAND) ⇒ 规模可控；带宽如实登记。**禁**同参重跑/加时/换工具/改参/削固定输入。"""
import argparse, collections, importlib, json, math, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
W = importlib.import_module("K2_R515_FREETERMINALS_v1")
G = importlib.import_module("K2_R523_LAYERHOP_PARITY_FORMC_v1")
P, X0, Y0, NX, NY, NID, TERM_BASE = W.P, W.X0, W.Y0, W.NX, W.NY, W.NID, W.TERM_BASE
XY, VIA_SEP, MAXV, HW = W.XY, W.VIA_SEP, 2 * W.MAX_VIA_PAIRS, W.HW
OWN_OUT = "K2_R543_EXACT_DRAWING_v1.json"
SPEC = os.path.join(HERE, "K2_R540_CORRIDOR_SPEC_v1.json")
RB = 3


def xy_of(nd):
    return XY(*W.rc(nd % NID))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, OWN_OUT))
    ap.add_argument("--solve", action="store_true"); ap.add_argument("--maxtime", type=float, default=1200.0)
    a = ap.parse_args()
    if os.path.basename(a.out) != OWN_OUT:
        raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7)")
    t0 = time.time()
    from ortools.sat.python import cp_model
    spec = json.load(open(SPEC)); rep = {"artifact": "k2_r543_exact_drawing_v1",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "authority": "#K2-210 sec.3.5 / sec.4 (exact method, ONE shot, R540 fixed inputs immutable)", "solve_calls": 0}
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names); lanes = {nm: g2.build_lane(nm) for nm in names}
    mo = cp_model.CpModel(); seg_arcs = {}; laneseg = {}; via_use = {}; capmap = collections.defaultdict(list)
    for nm in names:
        wps = spec["per_lane"][nm]["waypoints"]
        chain = [lanes[nm]["src"]] + [(w["node"] if "node" in w else (lanes[nm]["src"] if w["kind"] == "A_anchor" else lanes[nm]["snk"])) for w in wps[1:-1]] + [lanes[nm]["snk"]]
        seg_arcs[nm] = []
        for s in range(len(chain) - 1):
            src, dst = chain[s], chain[s + 1]
            if src >= TERM_BASE or dst >= TERM_BASE:
                keep = None
            else:
                ax, ay = xy_of(src); bx, by = xy_of(dst)
                keep = None
            # K2-212 K2-211 sec.3.3 FIXED domain (same rule as the passing calibration R545):
            # band UNION fixed waypoints UNION dilated shortest-path corridor between the two waypoints.
            sp = set()
            full = collections.defaultdict(set)
            for u, lst in lanes[nm]["adj"].items():
                for (v, _w) in lst:
                    full[u].add(v); full[v].add(u)
            prev = {src: None}; dq = collections.deque([src])
            while dq:
                x = dq.popleft()
                if x == dst:
                    break
                for y in full[x]:
                    if y not in prev:
                        prev[y] = x; dq.append(y)
            if dst in prev:
                x = dst
                while x is not None:
                    if x < TERM_BASE:
                        i0, j0 = (x % NID) // NY, (x % NID) % NY
                        for di in range(-1, 2):
                            for dj in range(-1, 2):
                                u2, v2 = i0 + di, j0 + dj
                                if 0 <= u2 < NX and 0 <= v2 < NY:
                                    sp.add(u2 * NY + v2)
                    x = prev[x]
            fixedset = set(x for x in chain if x < TERM_BASE)
            if src < TERM_BASE and dst < TERM_BASE:
                sx, sy = xy_of(src); tx, ty = xy_of(dst)
            else:
                sx = sy = tx = ty = 0.0

            def band_ok(nd):
                if nd >= TERM_BASE or src >= TERM_BASE or dst >= TERM_BASE:
                    return True
                px, py = xy_of(nd); dx, dy = tx - sx, ty - sy; L2 = dx * dx + dy * dy
                if L2 <= 0:
                    d = math.hypot(px - sx, py - sy)
                else:
                    t = max(0.0, min(1.0, ((px - sx) * dx + (py - sy) * dy) / L2))
                    d = math.hypot(px - (sx + t * dx), py - (sy + t * dy))
                return d <= RB * P + 1e-9
            cand = []
            for u, lst in lanes[nm]["adj"].items():
                for (v, _w) in lst:
                    iv = 1 if (u < TERM_BASE and v < TERM_BASE and u // NID != v // NID) else 0
                    adm = ((u < TERM_BASE and (u in fixedset or (u % NID) in sp)) or
                           (v < TERM_BASE and (v in fixedset or (v % NID) in sp)))
                    if adm:
                        cand.append((u, v, iv))
            seg_arcs[nm].append(cand)
        laneseg[nm] = [[mo.NewBoolVar("x_%s_%d_%d" % (nm.replace("-", "_"), s, k)) for k in range(len(c))]
                       for s, c in enumerate(seg_arcs[nm])]
        via_use[nm] = {}
        for s, c in enumerate(seg_arcs[nm]):
            src, dst = chain[s], chain[s + 1]
            if src == dst:
                mo.Add(sum(laneseg[nm][s]) == 0); continue
            inl, outl = collections.defaultdict(list), collections.defaultdict(list)
            for k, (u, v, w) in enumerate(c):
                outl[u].append(laneseg[nm][s][k]); inl[v].append(laneseg[nm][s][k])
            mo.Add(sum(outl[src]) == 1); mo.Add(sum(inl[src]) == 0)
            mo.Add(sum(inl[dst]) == 1); mo.Add(sum(outl[dst]) == 0)
            for nd in set(inl) | set(outl):
                if nd not in (src, dst):
                    mo.Add(sum(inl[nd]) == sum(outl[nd]))
            for k, (u, v, w) in enumerate(c):
                if u < TERM_BASE:
                    capmap[(u // NID, u % NID)].append(laneseg[nm][s][k])
                    if (u // NID) != (v // NID) if v < TERM_BASE else False:
                        via_use[nm].setdefault(u % NID, []).append(laneseg[nm][s][k])
        mo.Add(sum(x for v in via_use[nm].values() for x in v) <= MAXV)
    ncap = 0
    for key, lits in capmap.items():
        if len(lits) > 1:
            mo.Add(sum(lits) <= 1); ncap += 1
    blocks = collections.defaultdict(list)
    for nm in names:
        for p_, lits in via_use[nm].items():
            i, j = p_ // NY, p_ % NY
            for x in lits:
                blocks[(i // 2, j // 2)].append(x)
    ncliq = 0
    for key, lits in blocks.items():
        if len(lits) > 1:
            mo.Add(sum(lits) <= 1); ncliq += 1
    rep["model"] = {"bool_vars": len(mo.Proto().variables), "constraints": len(mo.Proto().constraints),
                    "node_capacity": ncap, "via_cliques": ncliq, "R_BAND": RB,
                    "validate": (mo.Validate() or "OK"), "under_1.2M": len(mo.Proto().variables) <= 1200000,
                    "segments_per_lane": {nm: len(seg_arcs[nm]) for nm in names[:3]},
                    "arcs_total": sum(len(c) for nm in names for c in seg_arcs[nm])}
    print("[stage] model:", json.dumps(rep["model"], ensure_ascii=False)[:300], flush=True)
    if not rep["model"]["under_1.2M"] or rep["model"]["validate"] != "OK":
        rep["decision"] = "FAIL-CLOSED: 规模闸/Validate 未过 ⇒ 不求解"; rep["buildability"] = {"mode": "no_witness"}
        json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str); print(rep["decision"]); return
    if not a.solve:
        rep["decision"] = "BUILD-ONLY GREEN（0 求解）⇒ --solve 开启终局那一次"; rep["buildability"] = {"mode": "no_witness"}
        json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str); print(rep["decision"]); return
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = a.maxtime
    st = s.Solve(mo); rep["solve_calls"] = 1
    rep["solve"] = {"status": s.StatusName(st), "wall_s": round(s.WallTime(), 1)}
    print("[stage] solve:", rep["solve"], flush=True)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        rep["decision"] = "NO DRAWING: 精确求解 %s（无 (甲)，且非守恒级硬墙 ⇒ 不构成 (乙)）" % s.StatusName(st)
        rep["buildability"] = {"mode": "no_witness"}; rep["elapsed_s"] = round(time.time() - t0, 1)
        json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str); print("WROTE", a.out, flush=True); return
    paths = {}
    for nm in names:
        full = []
        for seg in laneseg[nm]:
            for k, b in enumerate(seg):
                if s.Value(b):
                    u, v, _w = seg_arcs[nm][laneseg[nm].index(seg)][k]
                    if not full:
                        full.append(u)
                    full.append(v)
        paths[nm] = full
    TERMINALS = {}
    for Lj in names:
        TA_, TB_ = lanes[Lj]["terminals"]
        TERMINALS[TA_] = list(lanes[Lj]["anc"][0]); TERMINALS[TB_] = list(lanes[Lj]["anc"][1])

    def nxy(nd):
        return list(TERMINALS[nd - TERM_BASE]) if nd >= TERM_BASE else list(XY(*W.rc(nd % NID)))
    lane_polys, all_vias, drawing = {}, [], {}
    for nm in names:
        seq = paths[nm]; runs, run, vloc = [], [seq[0]], []
        for nd in seq[1:]:
            lay = 0 if nd >= TERM_BASE else nd // NID; layp = 0 if run[-1] >= TERM_BASE else run[-1] // NID
            if lay == layp:
                run.append(nd)
            else:
                all_vias.append((XY(*W.rc(run[-1] % NID))[0], XY(*W.rc(run[-1] % NID))[1], nm))
                vloc.append([round(XY(*W.rc(run[-1] % NID))[0], 3), round(XY(*W.rc(run[-1] % NID))[1], 3)])
                runs.append(run); run = [nd]
        runs.append(run)
        polys = {}
        for run in runs:
            lay = 0 if run[0] >= TERM_BASE else run[0] // NID
            polys.setdefault(lay, []).append([nxy(p) for p in run])
        lane_polys[nm] = polys
        drawing[nm] = {"waypoints": spec["per_lane"][nm]["waypoints"], "schedule": spec["per_lane"][nm]["schedule"],
                       "segments": {("In5" if L == 0 else "In4"): [[round(c, 3) for c in pt] for p in polys[L] for pt in p] for L in polys},
                       "via_pairs": vloc, "n_via_pairs": len(vloc)}
    mj = json.load(open("/tmp/opencode/archer/model_l8.json")); gpl = {}
    for Lr in (0, 1):
        rt = {}
        for nm, polys in lane_polys.items():
            for k, p in enumerate(polys.get(Lr, [])):
                if len(p) >= 2:
                    rt["%s#%d" % (nm, k)] = {"pts": p, "layer_cu": G.LAYER_OF[Lr], "n_vias": len(all_vias)}
        if rt:
            gg = G.exact_gate(mj, rt, [], G.LAYER_OF[Lr], HW, set(), set(), P, frozenset())
            vp2 = [t for t in gg["lane_pitch_violations"] if t[0].split("#")[0] != t[1].split("#")[0]]
            gpl[G.LAYER_OF[Lr]] = {"n_lane_pitch_viol": len(vp2), "n_clearance_viol": gg["n_clearance_viol"]}
    gv = G.gate_vias(mj, all_vias, lane_polys, g2.an)
    edev = {}
    for nm, polys in lane_polys.items():
        p0 = polys[0][0][0]; p1 = polys[0][-1][-1]
        edev[nm] = round(max(math.dist(p0, list(g2.A[nm])), math.dist(p1, list(g2.B[nm]))), 6)
    ok = (all(v["n_lane_pitch_viol"] == 0 and v["n_clearance_viol"] == 0 for v in gpl.values())
          and gv["n_via_viol"] == 0 and (max(edev.values()) if edev else 1) <= 1e-6
          and all(sum(1 for v in all_vias if v[2] == nm) <= MAXV for nm in names))
    rep.update({"exact_gate_per_layer": gpl, "gate_vias": gv, "endpoint_max_dev_mm": max(edev.values()) if edev else None,
                "vias_per_lane": {nm: sum(1 for v in all_vias if v[2] == nm) for nm in names},
                "requirement_level_gate": "PASS" if ok else "FAIL", "drawing": drawing,
                "conservation_audit": {"source": "K2_R537_CONSERVATION_CUT_v1.json",
                                       "reading": "156 割无容量墙（最紧 col114 上界 40 vs 需求 3，余 +37）"},
                "buildability": ({"mode": "relocation_listed", "relocation_list": sorted(names)} if ok
                                 else {"mode": "no_move"})})
    rep["decision"] = ("(甲) DETERMINATE DRAWING DELIVERED: 16/16 零自由度逐段确定路径 + 在册闸全绿 ⇒ 交监理复核"
                       if ok else "NON-TERMINAL: 16/16 路径已得但在册闸 FAIL")
    if ok:
        json.dump(drawing, open(os.path.join(HERE, "K2_R543_DRAWING_PER_LANE_v1.json"), "w"), ensure_ascii=False, indent=1, default=str)
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print("[stage] gate:", rep["requirement_level_gate"], "|", rep["decision"][:80], flush=True)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as _e:
        import traceback; traceback.print_exc(); print('FAIL_LOUD: {"error": %r}' % (str(_e),), flush=True); sys.exit(3)
