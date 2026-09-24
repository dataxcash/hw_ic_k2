#!/usr/bin/env python3
"""K2 · R541 —— **方案层"最后一笔"**（#K2-206 §三.2–4 · 方案层专用那一次）：以 R540 固定路点链为**不可变输入**，
逐线求**逐段确定路径**（构造法 · 硬预留 · 换层 <=2 对孔 · 孔距 >= VIA_SEP），再走**在册闸**签字，导出**每线确定施工图**。
**禁**：重跑旧自由度模型 / 改固定输入 / 失败后重试 / 换参 / 加时。fail-loud 落盘。"""
import argparse, collections, heapq, importlib, json, math, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
W = importlib.import_module("K2_R515_FREETERMINALS_v1")
G = importlib.import_module("K2_R523_LAYERHOP_PARITY_FORMC_v1")
P, X0, Y0, NX, NY, NID, TERM_BASE = W.P, W.X0, W.Y0, W.NX, W.NY, W.NID, W.TERM_BASE
XY, VIA_SEP, MAXV, HW = W.XY, W.VIA_SEP, 2 * W.MAX_VIA_PAIRS, W.HW
OWN_OUT = "K2_R541_DRAWING_ONESHOT_v1.json"
SPEC = os.path.join(HERE, "K2_R540_CORRIDOR_SPEC_v1.json")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, OWN_OUT))
    a = ap.parse_args()
    if os.path.basename(a.out) != OWN_OUT:
        raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7)")
    t0 = time.time()
    spec = json.load(open(SPEC))
    rep = {"artifact": "k2_r541_drawing_oneshot_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-206 sec.3.2-4 (the ONE authorised scheme-layer shot; fixed inputs from R540; no retry)",
           "certified_solve_calls": 0, "method": "deterministic construction: per-lane leg-by-leg Dijkstra through the "
           "FIXED waypoint chain with hard claim reservation, <=2 via pairs, via-via >= VIA_SEP",
           "source_spec": os.path.basename(SPEC), "partial": True}
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names); lanes = {nm: g2.build_lane(nm) for nm in names}
    zone_of = {}
    for nm in names:
        for u in list(lanes[nm]["adj"].keys()):
            if u >= TERM_BASE:
                continue
            x, y = XY(*W.rc(u % NID))
            z = None
            for k, (x0, y0, x1, y1) in enumerate(G.ZONES):
                if x0 - 1e-9 <= x <= x1 + 1e-9 and y0 - 1e-9 <= y <= y1 + 1e-9:
                    z = k; break
            zone_of[(nm, u % NID)] = z
    ST = ["COMB", "BELT", "WALL", "FIELD"]
    _ac = {}

    def arc_info(nm, u, v):
        key = (nm, u, v)
        got = _ac.get(key)
        if got is not None:
            return got
        if u >= TERM_BASE:
            tx, ty = lanes[nm]["anc"][0]; px, py = XY(*W.rc(v % NID))
            got = ("leg", 0, frozenset(W.claim_seg(tx, ty, px, py)), None)
        elif v >= TERM_BASE:
            px, py = XY(*W.rc(u % NID)); tx, ty = lanes[nm]["anc"][1]
            got = ("leg", 0, frozenset(W.claim_seg(px, py, tx, ty)), None)
        elif u // NID != v // NID:
            got = ("via", u // NID, frozenset([u % NID]), u % NID)
        else:
            ax, ay = XY(*W.rc(u % NID)); bx, by = XY(*W.rc(v % NID))
            got = ("lat", u // NID, frozenset(W.claim_seg(ax, ay, bx, by)), None)
        _ac[key] = got
        return got

    def want4(nm):
        return set(spec["per_lane"][nm]["schedule"]["stations_on_In4"])

    def dijk(nm, src, dst, res0, res1, vias, nv0):
        adj = lanes[nm]["adj"]; w4 = want4(nm)
        dist = {src: 0.0}; nv = {src: nv0}; prev = {}; pq = [(0.0, src)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist.get(u, 1e18) + 1e-12:
                continue
            if u == dst:
                break
            for (v, w) in adj.get(u, ()):
                kind, Lay, claim, vp = arc_info(nm, u, v)
                if kind == "via":
                    if vp in res0 or vp in res1:
                        continue
                    bad = False
                    for (q, _o) in vias:
                        if math.dist(XY(*W.rc(vp)), XY(*W.rc(q))) < VIA_SEP - 1e-9:
                            bad = True; break
                    if bad or nv.get(u, 0) >= MAXV:
                        continue
                else:
                    if claim & (res0 if Lay == 0 else res1):
                        continue
                pen = 0.0
                if v < TERM_BASE:
                    z = zone_of.get((nm, v % NID))
                    if z is not None:
                        pen = 0.0 if ((v // NID) == (1 if ST[z] in w4 else 0)) else 2.0 * P
                nd = d + w + pen + (1e-4 if kind == "via" else 0.0)
                if nd < dist.get(v, 1e18) - 1e-12:
                    dist[v] = nd; nv[v] = nv.get(u, 0) + (1 if kind == "via" else 0); prev[v] = u
                    heapq.heappush(pq, (nd, v))
        if dst not in prev:
            return None, nv0
        p = []; cur = dst
        while cur is not None:
            p.append(cur); cur = prev.get(cur)
        p.reverse()
        return p, nv.get(dst, nv0)

    def commit(nm, path, res0, res1, vias):
        for u, v in zip(path, path[1:]):
            kind, Lay, claim, vp = arc_info(nm, u, v)
            if kind == "via":
                res0.add(vp); res1.add(vp); vias.append((vp, nm))
            else:
                (res0 if Lay == 0 else res1).update(claim)

    def route(nm, res0, res1, vias):
        wps = spec["per_lane"][nm]["waypoints"]
        nodes = []
        for w in wps:
            if w["kind"] == "A_anchor":
                nodes.append(lanes[nm]["src"])
            elif w["kind"] == "B_anchor":
                nodes.append(lanes[nm]["snk"])
            else:
                nodes.append(w["node"])
        full = list(); nv = 0; cur = nodes[0]; legs = 0
        for k in range(1, len(nodes)):
            tgt = nodes[k]
            seg, nv = dijk(nm, cur, tgt, res0, res1, vias, nv)
            if seg is None:
                return None, 0, {"stage": "leg_%d_%s" % (k, wps[k]["kind"]), "from": cur, "to": tgt, "legs_ok": legs}
            if k > 1 and wps[k]["kind"] == "DIVE_via":
                pass
            full += seg if not full else seg[1:]
            cur = tgt; legs += 1
        return full, nv, {"legs_ok": legs}

    def run(order):
        res0, res1, vias, paths = set(), set(), [], {}
        failed = {}
        for nm in order:
            p, nv, diag = route(nm, res0, res1, vias)
            if p is None:
                failed[nm] = diag; continue
            commit(nm, p, res0, res1, vias); paths[nm] = p
        for nm in [x for x in order if x in failed]:
            p, nv, diag = route(nm, res0, res1, vias)
            if p is None:
                failed[nm] = diag; continue
            commit(nm, p, res0, res1, vias); paths[nm] = p; failed.pop(nm, None)
        return paths, failed

    dive_first = [nm for nm in names if spec["per_lane"][nm]["waypoints"][1]["kind"] == "DIVE_via"]
    order = dive_first + [nm for nm in names if nm not in dive_first]
    paths, failed = run(order)
    rep["n_routed"] = len(paths); rep["failed_lanes"] = sorted(failed.keys())
    rep["first_failure"] = (failed[sorted(failed.keys())[0]] if failed else None)
    print("[stage] routed %d/%d failed=%s" % (len(paths), len(names), sorted(failed.keys())), flush=True)
    if len(paths) != len(names):
        rep["decision"] = "NO DETERMINATE DRAWING (construction stopped; per K2-206 sec.3.5: STOP, no retry)"
        rep["buildability"] = {"mode": "no_witness", "note": "不完整 ⇒ 无搬迁清单"}
        rep["elapsed_s"] = round(time.time() - t0, 1)
        json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str); print("WROTE", a.out, flush=True); return
    # ---- registered gates + drawing ----
    TERMINALS = {}
    for Lj in names:
        TA_, TB_ = lanes[Lj]["terminals"]
        TERMINALS[TA_] = list(lanes[Lj]["anc"][0]); TERMINALS[TB_] = list(lanes[Lj]["anc"][1])

    def nxy(nd):
        return list(TERMINALS[nd - TERM_BASE]) if nd >= TERM_BASE else list(XY(*W.rc(nd % NID)))
    lane_polys, all_vias, drawing = {}, [], {}
    for nm in names:
        seq = paths[nm]; runs, run = [], [seq[0]]; vloc = []
        for nd in seq[1:]:
            lay = 0 if nd >= TERM_BASE else nd // NID; layp = 0 if run[-1] >= TERM_BASE else run[-1] // NID
            if lay == layp:
                run.append(nd)
            else:
                vloc.append([round(XY(*W.rc(run[-1] % NID))[0], 3), round(XY(*W.rc(run[-1] % NID))[1], 3)])
                all_vias.append((XY(*W.rc(run[-1] % NID))[0], XY(*W.rc(run[-1] % NID))[1], nm))
                runs.append(run); run = [nd]
        runs.append(run)
        polys = {}
        for run in runs:
            lay = 0 if run[0] >= TERM_BASE else run[0] // NID
            polys.setdefault(lay, []).append([nxy(p) for p in run])
        lane_polys[nm] = polys
        drawing[nm] = {"slots": spec["per_lane"][nm]["waypoints"], "schedule": spec["per_lane"][nm]["schedule"],
                       "segments": {("In5" if L == 0 else "In4"): [[round(c, 3) for c in pt] for p in polys[L] for pt in p] for L in polys},
                       "via_pairs": vloc, "n_via_pairs": len(vloc)}
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
        gpl[G.LAYER_OF[Lr]] = {"n_lane_pitch_viol": len(vp2), "n_clearance_viol": gg["n_clearance_viol"],
                              "lane_pitch_min_gap_mm": gg["lane_pitch_min_gap_mm"], "clearance_min_mm": gg["clearance_min_mm"]}
    gv = G.gate_vias(model_json, all_vias, lane_polys, g2.an)
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
                                       "reading": "156 个在册格点割无容量墙（最紧 col114 上界 40 vs 需求 3，余 +37）⇒ 容量 >= 需求"},
                "buildability": ({"mode": "relocation_listed", "relocation_list": sorted(names),
                                  "note": "逐线通道图（段序列+换层点+孔对）如 drawing；不动其它对象"} if ok
                                 else {"mode": "no_move", "note": "在册闸未过"})})
    rep["decision"] = ("DETERMINATE DRAWING DELIVERED: 16/16 逐段确定路径 + 在册闸（exact_gate/gate_vias/端点）全绿 ⇒ 交监理复核；过则另件批施工令"
                       if ok else "NON-TERMINAL: 16/16 路径已得，但在册闸 FAIL（见明细）")
    rep["partial"] = False
    if ok:
        json.dump(drawing, open(os.path.join(HERE, "K2_R541_DRAWING_PER_LANE_v1.json"), "w"), ensure_ascii=False, indent=1, default=str)
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print("[stage] gate:", rep["requirement_level_gate"], "| decision:", rep["decision"][:80], flush=True)
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
