#!/usr/bin/env python3
"""K2 · R540 —— **方案层固定输入：逐线走廊规格件**（#K2-206 §三.2–4 的"已定断面/时刻表为固定输入"落地）。
**纯提取 · 0 求解 · 不改任何在册件**：读取在册 `K2_R529_WOVEN_COMPLETE_MASTER_v1.json`，把每根线的
入口动作 / col33 / col60 / exit 三断面槽位 / 行程时刻表 **机械地**翻成**逐线路点链**（含 mm 坐标与格点号），
供那**一次**（已授权 · 方案层专用）求解把"每线逐段确定路径"画完。"""
import argparse, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
W = __import__("importlib").import_module("K2_R515_FREETERMINALS_v1")
P, X0, Y0, NX, NY, NID = W.P, W.X0, W.Y0, W.NX, W.NY, W.NID
OWN_OUT = "K2_R540_CORRIDOR_SPEC_v1.json"
R529 = os.path.join(HERE, "K2_R529_WOVEN_COMPLETE_MASTER_v1.json")
COL33, COL60, COL114, ROW36 = 33, 60, 114, 36


def node_xy(p):
    return (round(X0 + (p // NY) * P, 3), round(Y0 + (p % NY) * P, 3))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, OWN_OUT))
    a = ap.parse_args()
    if os.path.basename(a.out) != OWN_OUT:
        raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7)")
    t0 = time.time()
    m = json.load(open(R529))
    ent, sec, sch = m["entrance_actions"], m["section_slots"], m["schedule"]
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names)
    out = {"artifact": "k2_r540_corridor_spec_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-206 sec.3.2-4: fixed inputs for the ONE authorised scheme-layer solve "
                        "(extraction only; ZERO solves; no writes to any registered artifact)",
           "certified_solve_calls": 0, "source_master": os.path.basename(R529),
           "P_mm": P, "lattice": {"X0": X0, "Y0": Y0, "NX": NX, "NY": NY},
           "sections": {"col33": COL33, "col60": COL60, "wall_col": COL114, "gate_row": ROW36},
           "per_lane": {}}
    for nm in names:
        east = g2.grp[nm] == "east"
        A = [round(v, 3) for v in g2.A[nm]]; B = [round(v, 3) for v in g2.B[nm]]
        e = ent[nm]
        e_node = e["via"] if e.get("kind") == "DIVE" else e["node"]
        wp = [{"kind": "A_anchor", "xy_mm": A},
              {"kind": ("DIVE_via" if e.get("kind") == "DIVE" else "In5_entrance"), "node": e_node,
               "xy_mm": list(node_xy(e_node)), "dist_mm": e.get("dist")},
              {"kind": "col33", "node": COL33 * NY + sec[nm]["col33"], "xy_mm": list(node_xy(COL33 * NY + sec[nm]["col33"]))},
              {"kind": "col60", "node": COL60 * NY + sec[nm]["col60"], "xy_mm": list(node_xy(COL60 * NY + sec[nm]["col60"]))}]
        if east:
            nd = sec[nm]["exit"] * NY + ROW36
            wp.append({"kind": "exit_gate_col", "node": nd, "xy_mm": list(node_xy(nd))})
            wp.append({"kind": "pad_run", "node": int(round((B[0] - X0) / P)) * NY + ROW36,
                       "xy_mm": [B[0], round(Y0 + ROW36 * P, 3)]})
        else:
            nd = COL114 * NY + sec[nm]["exit"]
            wp.append({"kind": "exit_wall_gap", "node": nd, "xy_mm": list(node_xy(nd))})
            wp.append({"kind": "pad_run", "node": COL114 * NY + 0 + sec[nm]["exit"],
                       "xy_mm": [round(X0 + COL114 * P, 3), round(Y0 + sec[nm]["exit"] * P, 3)]})
        wp.append({"kind": "B_anchor", "xy_mm": B})
        out["per_lane"][nm] = {"group": g2.grp[nm], "waypoints": wp, "schedule": sch[nm],
                               "n_waypoints": len(wp)}
    out["handoff_to_the_one_solve"] = {
        "task": "per-lane per-segment determinate lattice path through the fixed waypoint chain above",
        "fixed_inputs": ["entrance action", "col33/col60/exit section slots", "time table (In4 stations)"],
        "must_not": ["re-run the old free-degree models (proved infeasible)",
                     "change any fixed input", "retry after failure (K2-206 sec.3.5)"],
        "acceptance": ["per-lane zero-freedom drawing", "conservation audit", "buildability",
                       "two artefacts (raw solve product with fail-loud log on disk + derived drawing)",
                       "committed inside the k2 repo with a hash (K2-206 sec.3.6)"]}
    out["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(out, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print("[stage] corridor spec written: %d lanes, waypoints/lane = %s" % (len(names), [out["per_lane"][n]["n_waypoints"] for n in names[:4]]), flush=True)
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
