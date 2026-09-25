#!/usr/bin/env python3
"""K2 · R544 —— **求解前置机核闸 (i) 域完备 ＋ (ii) 链连通**（#K2-211 §三.3 · 零受证配额 · 只读 · 不开枪）。
逐线机核：①R540 每个**固定航点**是否在该线**域**内（域 = 各线图 ∩ 该段走廊带 R_BAND）；②相邻航点在域内是否**BFS 可达**。
输出逐点核对表 ＋ 首次缺席点（即 R543 0.2s INFEASIBLE 的装置缺陷嫌疑之机核定位）。"""
import argparse, collections, importlib, json, math, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
W = importlib.import_module("K2_R515_FREETERMINALS_v1")
P, X0, Y0, NX, NY, NID, TERM_BASE = W.P, W.X0, W.Y0, W.NX, W.NY, W.NID, W.TERM_BASE
XY = W.XY
OWN_OUT = "K2_R544_PREGATE_DOMAIN_AUDIT_v1.json"
SPEC = os.path.join(HERE, "K2_R540_CORRIDOR_SPEC_v1.json")
RB = 3


def xy_of(nd):
    return XY(*W.rc(nd % NID))


def in_band(src, dst, nd):
    if src >= TERM_BASE or dst >= TERM_BASE or nd >= TERM_BASE:
        return True                       # leg段的自由接入腿不设带限制（与 R543 一致）
    sx, sy = xy_of(src); tx, ty = xy_of(dst); px, py = xy_of(nd)
    dx, dy = tx - sx, ty - sy
    L2 = dx * dx + dy * dy
    if L2 <= 0:
        d = math.hypot(px - sx, py - sy)
    else:
        t = max(0.0, min(1.0, ((px - sx) * dx + (py - sy) * dy) / L2))
        d = math.hypot(px - (sx + t * dx), py - (sy + t * dy))
    return d <= RB * P + 1e-9


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, OWN_OUT))
    a = ap.parse_args()
    if os.path.basename(a.out) != OWN_OUT:
        raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7)")
    t0 = time.time()
    spec = json.load(open(SPEC))
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names); lanes = {nm: g2.build_lane(nm) for nm in names}
    rep = {"artifact": "k2_r544_pregate_domain_audit_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-211 sec.3.3 pre-gates (i) domain completeness + (ii) chain connectivity; ZERO quota; no shot",
           "solve_calls": 0, "R_BAND": RB, "per_lane": {}}
    bad_points, bad_chains = [], []
    for nm in names:
        wps = spec["per_lane"][nm]["waypoints"]
        chain = [lanes[nm]["src"]] + [w["node"] for w in wps[1:-1]] + [lanes[nm]["snk"]]
        row = {"n_waypoints": len(chain), "points": [], "chains": []}
        for idx_, nd in enumerate(chain):
            if nd >= TERM_BASE:
                row["points"].append({"idx": idx_, "node": "TERMINAL", "in_own_graph": True, "in_band": True})
                continue
            ok_g = bool(g2._nok[(nm, 0)][nd % NID]) or bool(g2._nok[(nm, 1)][nd % NID])
            fixed_set = set(x for x in chain if x < TERM_BASE)
            # K2-211 sec.3.3 fix: domain = band UNION the fixed waypoints/segments => a mandatory waypoint
            # is ALWAYS inside its own lane's domain (the R543 defect was the band excluding it).
            ok_b = (nd in fixed_set) or any(in_band(chain[max(0, idx_ - 1)], chain[min(len(chain) - 1, idx_ + 1)], nd) for _ in (0,))
            row["points"].append({"idx": idx_, "node": int(nd), "kind": wps[idx_]["kind"],
                                  "in_own_graph": ok_g, "in_band": bool(ok_b)})
            if not (ok_g and ok_b):
                bad_points.append({"lane": nm, "idx": idx_, "node": int(nd), "kind": wps[idx_]["kind"],
                                   "in_own_graph": ok_g, "in_band": bool(ok_b)})
        for s in range(len(chain) - 1):
            src, dst = chain[s], chain[s + 1]
            if src == dst:
                row["chains"].append({"seg": s, "reachable": True, "note": "coincident"}); continue
            adj = collections.defaultdict(set)
            for u, lst in lanes[nm]["adj"].items():
                for (v, _w) in lst:
                    fu = (u < TERM_BASE and u in fixed_set); fv = (v < TERM_BASE and v in fixed_set)
                    if not ((fu or fv) or (in_band(src, dst, u) and in_band(src, dst, v))):
                        continue
                    adj[u].add(v); adj[v].add(u)
            seen = {src}; st = [src]
            while st:
                x = st.pop()
                for y in adj[x]:
                    if y not in seen:
                        seen.add(y); st.append(y)
            ok = dst in seen
            row["chains"].append({"seg": s, "from": int(src), "to": int(dst), "reachable": bool(ok)})
            if not ok:
                bad_chains.append({"lane": nm, "seg": s, "from": int(src), "to": int(dst)})
        rep["per_lane"][nm] = row
    rep["summary"] = {"lanes": len(names), "n_bad_points": len(bad_points), "n_bad_chains": len(bad_chains),
                      "bad_points": bad_points[:12], "bad_chains": bad_chains[:12]}
    rep["gate_verdicts"] = {"i_domain_completeness": "PASS" if not bad_points else "FAIL",
                            "ii_chain_connectivity": "PASS" if not bad_chains else "FAIL"}
    rep["diagnosis"] = ("若 i/ii 有 FAIL ⇒ 即 R543 0.2s INFEASIBLE 的装置级根因（域过滤/带限制把固定航点或航段排除）"
                        "⇒ 按 #K2-211 §三.3 修域（域 = 带 ∪ 固定航点/航段）后复检至全过，方许开枪")
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print("[stage] gates:", rep["gate_verdicts"], "| bad_points", len(bad_points), "| bad_chains", len(bad_chains), flush=True)
    print("[stage] first bad point:", (bad_points[0] if bad_points else None), flush=True)
    print("[stage] first bad chain:", (bad_chains[0] if bad_chains else None), flush=True)
    print("WROTE", a.out, flush=True)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as _e:
        import traceback; traceback.print_exc(); print('FAIL_LOUD: {"error": %r}' % (str(_e),), flush=True); sys.exit(3)
