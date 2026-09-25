#!/usr/bin/env python3
"""K2 · R545 —— 前置闸 (iii) **单线标定**（#K2-211 §三.3 / #K2-212 §三.3 · 零受证配额）。
逐线（16 条）在**固定域**（带 ∪ 固定航点 ∪ 逐段最短路膨胀走廊）内解一次单线精确子模型（连通 ＋ 每线 <=2 对孔）⇒ 须 16/16 SAT。"""
import argparse, collections, heapq, importlib, json, math, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
W = importlib.import_module("K2_R515_FREETERMINALS_v1")
P, X0, Y0, NX, NY, NID, TERM_BASE = W.P, W.X0, W.Y0, W.NX, W.NY, W.NID, W.TERM_BASE
XY, MAXV = W.XY, 2 * W.MAX_VIA_PAIRS
OWN_OUT = "K2_R545_SINGLE_LANE_CALIB_v1.json"
SPEC = os.path.join(HERE, "K2_R540_CORRIDOR_SPEC_v1.json")
RB = 3


def xy_of(nd):
    return XY(*W.rc(nd % NID))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, OWN_OUT))
    a = ap.parse_args()
    if os.path.basename(a.out) != OWN_OUT:
        raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7)")
    from ortools.sat.python import cp_model
    t0 = time.time()
    spec = json.load(open(SPEC))
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names); lanes = {nm: g2.build_lane(nm) for nm in names}
    rep = {"artifact": "k2_r545_single_lane_calib_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-211 sec.3.3 / #K2-212 sec.3.3 pre-gate (iii) single-lane calibration; ZERO certified quota",
           "certified_solve_calls": 0, "per_lane": {}}
    for nm in names:
        wps = spec["per_lane"][nm]["waypoints"]
        chain = [lanes[nm]["src"]] + [w["node"] for w in wps[1:-1]] + [lanes[nm]["snk"]]
        fixed = set(x for x in chain if x < TERM_BASE)
        m = cp_model.CpModel(); xs = []; via_count = []
        for s in range(len(chain) - 1):
            src, dst = chain[s], chain[s + 1]
            if src == dst:
                continue
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
                        for di in range(-RB, RB + 1):
                            for dj in range(-RB, RB + 1):
                                u2, v2 = i0 + di, j0 + dj
                                if 0 <= u2 < NX and 0 <= v2 < NY:
                                    sp.add(u2 * NY + v2)
                    x = prev[x]
            sx, sy = (xy_of(src) if src < TERM_BASE else (0, 0)); tx, ty = (xy_of(dst) if dst < TERM_BASE else (0, 0))

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
                    adm = ((u < TERM_BASE and (u in fixed or (u % NID) in sp)) or
                           (v < TERM_BASE and (v in fixed or (v % NID) in sp)) or
                           (band_ok(u) and band_ok(v)))
                    if adm:
                        cand.append((u, v, iv))
            xseg = [m.NewBoolVar("y_%s_%d_%d" % (nm.replace("-", "_"), s, k)) for k in range(len(cand))]
            inl, outl = collections.defaultdict(list), collections.defaultdict(list)
            for k, (u, v, iv) in enumerate(cand):
                outl[u].append(xseg[k]); inl[v].append(xseg[k])
            m.Add(sum(outl[src]) == 1); m.Add(sum(inl[src]) == 0)
            m.Add(sum(inl[dst]) == 1); m.Add(sum(outl[dst]) == 0)
            for nd in set(inl) | set(outl):
                if nd not in (src, dst):
                    m.Add(sum(inl[nd]) == sum(outl[nd]))
            xs.extend(xseg); via_count += [xseg[k] for k, (u, v, iv) in enumerate(cand) if iv]
        m.Add(sum(via_count) <= MAXV)
        s2 = cp_model.CpSolver(); s2.parameters.max_time_in_seconds = 120
        st = s2.Solve(m)
        rep["per_lane"][nm] = {"status": s2.StatusName(st), "wall_s": round(s2.WallTime(), 2),
                               "vars": len(m.Proto().variables), "cons": len(m.Proto().constraints)}
        print("[stage] %-22s %s (%.2fs)" % (nm, s2.StatusName(st), s2.WallTime()), flush=True)
    ok = sum(1 for nm in names if rep["per_lane"][nm]["status"] in ("OPTIMAL", "FEASIBLE"))
    rep["summary"] = {"n_sat": ok, "n_lanes": len(names), "verdict": "PASS(16/16 SAT)" if ok == len(names) else "FAIL"}
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print("[stage] (iii) verdict:", rep["summary"]["verdict"], flush=True)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as _e:
        import traceback; traceback.print_exc(); print('FAIL_LOUD: {"error": %r}' % (str(_e),), flush=True); sys.exit(3)
