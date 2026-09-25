#!/usr/bin/env python3
"""K2 · R548d —— **缺陷修复后的一次出图**（在册图缺整族竖直边 → 内存修复 → 人类"轨道带拉直线"一次实现）。
（遵监理停止令：本件是**一次**实现；方法/余量与 R548b **完全相同、未调参**；唯一改动 = 修复被机证的边枚举缺陷。）

修复（一行 · 内存 monkey-patch · **不落盘改任何在册件**）：
  原：m2 = aa < ba                        ⇒ 丢掉 (0,±1) 两族竖直边（8832 条，占 25%）
  修：m2 = (aa < ba) | ((aa == ba) & (ab < bb))   ⇒ 无向边按字典序去重，恢复竖直边
依据：R548c《在册图画图缺陷证书》（registered 26441 边 = {1,0:8905, 1,1:17536}，竖直 0 条；
      预期 35273 边含 {0,1:8832}）。
"""
import argparse, hashlib, importlib, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OWN_OUT = "K2_R548d_DEFECT_CORRECTED_DRAWING_v1.json"
LOGF = "/tmp/opencode/r548/r548d_corrected.log"
MODEL = "/tmp/opencode/archer/model_l8.json"

# ---- import the (already committed) single-pass method module; it also installs the ortools import shim ----
B = importlib.import_module("K2_R548b_HUMAN_TRACK_DRAWING_v1")
PREV = B.W.PREV          # K2_R499_CONFLICT_TABLE_ONE_IMPLEMENTATION_v3


def _build_edges_fixed(self):
    """verbatim copy of PREV.Gen._build_edges with the de-dup filter corrected to lexicographic order."""
    NX, NY, X0, Y0, P, STEP_S = PREV.NX, PREV.NY, PREV.X0, PREV.Y0, PREV.P, PREV.STEP_S
    NB = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
    ai = np.repeat(np.arange(NX), NY); aj = np.tile(np.arange(NY), NX)
    eu, ev, el, eh = [], [], [], []
    for di, dj in NB:
        bi = ai + di; bj = aj + dj
        m = (bi >= 0) & (bi < NX) & (bj >= 0) & (bj < NY)
        aa, ab, ba, bb = ai[m], aj[m], bi[m], bj[m]
        m2 = (aa < ba) | ((aa == ba) & (ab < bb))        # <<< FIX (was: m2 = aa < ba)
        aa, ab, ba, bb = aa[m2], ab[m2], ba[m2], bb[m2]
        eu.append(aa * NY + ab); ev.append(ba * NY + bb)
        el.append(np.hypot((ba - aa) * P, (bb - ab) * P)); eh.append(ab == bb)
    self.edge_u = np.concatenate(eu); self.edge_v = np.concatenate(ev)
    self.edge_len = np.concatenate(el); self.edge_h = np.concatenate(eh)
    self.edge_j = self.edge_u % NY
    ns = np.maximum(2, np.ceil(self.edge_len / STEP_S).astype(int) + 1)
    mx = int(ns.max()); self.emx = mx
    t = np.clip(np.arange(mx)[None, :] / np.maximum(1, ns - 1)[:, None], 0, 1)
    ux = X0 + (self.edge_u // NY) * P; uy = Y0 + (self.edge_u % NY) * P
    vx = X0 + (self.edge_v // NY) * P; vy = Y0 + (self.edge_v % NY) * P
    self.esamp = np.stack([ux[:, None] + t * (vx - ux)[:, None], uy[:, None] + t * (vy - uy)[:, None]], -1)
    self.emask = np.arange(mx)[None, :] < ns[:, None]
    si = np.rint((self.esamp[:, :, 0] - self.rast.X0) / self.rast.step).astype(int)
    sj = np.rint((self.esamp[:, :, 1] - self.rast.Y0) / self.rast.step).astype(int)
    ob = (si < 0) | (si >= self.rNX) | (sj < 0) | (sj >= self.rNY)
    si = np.clip(si, 0, self.rNX - 1); sj = np.clip(sj, 0, self.rNY - 1)
    self.edge_base_ok = ~(((self.base[si, sj] | ob) & self.emask).any(1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, OWN_OUT))
    a = ap.parse_args()
    if os.path.basename(a.out) != OWN_OUT:
        raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7)")
    open(LOGF, "w").close()
    PREV.Gen._build_edges = _build_edges_fixed          # in-memory defect fix ONLY
    t0 = time.time()
    spec = json.load(open(B.SPEC)); master = json.load(open(B.R529)); mj = json.load(open(MODEL))
    rep = {"artifact": "k2_r548d_defect_corrected_drawing_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "stop-order response: ONE implementation after Plan; defect-corrected registered graph",
           "defect_fix": {"file_fixed_in_memory_only": "K2_R499_CONFLICT_TABLE_ONE_IMPLEMENTATION_v3.Gen._build_edges",
                          "was": "m2 = aa < ba", "now": "m2 = (aa < ba) | ((aa == ba) & (ab < bb))",
                          "evidence": "K2_R548c_..._VERTICAL_EDGE_DEFECT_v1.json (8832 vertical edges were missing)",
                          "registered_files_touched": "NONE (monkey-patch in memory)"},
           "method": "identical to R548b: allocate one track per lane per cross-section (L2 re-derived slots), then "
                     "draw straight track-band paths; single pass, deterministic, hard reservation, no negotiation",
           "declared_margins": {"row_M_R": B.M_R, "col_M_C": B.M_C}, "solve_calls": 0}
    B.g2_cache = None
    g2 = B.W.Gen2(mj, l1scope="full"); names = list(g2.names)
    lanes = {nm: g2.build_lane(nm) for nm in names}
    # sanity: vertical edges now present in the lane graphs?
    import collections
    ve = 0
    for nm in names:
        for u, lst in lanes[nm]["adj"].items():
            if u >= B.NID: continue
            for (v, _w) in lst:
                if v >= B.NID or u // B.NID != v // B.NID: continue
                if (u % B.NID) // B.NY == (v % B.NID) // B.NY and abs((u % B.NID) % B.NY - (v % B.NID) % B.NY) == 1:
                    ve += 1
    rep["vertical_edges_in_lane_graphs_after_fix"] = ve
    B.log("[fix] vertical lateral arcs present in lane graphs: %d" % ve)
    repair, rinfo = B.repair_slots(g2, master, names, lanes)
    rep["l2_slot_repair"] = dict(rinfo, n_movements=sum(1 for nm in names for t in ("col33", "col60", "exit")
                                                      if master["section_slots"][nm][t] != repair[nm][t]))
    chain = B.build_chain(g2, master, spec, names, repair)
    paths, diag = B.draw(g2, master, spec, names, lanes, chain)
    if paths is None:
        rep["first_blocker"] = diag
        rep["decision"] = ("STILL BLOCKED after the defect fix -- first blocker recorded; per the stop order NO "
                           "parameter change and NO rerun.")
        rep["buildability"] = {"mode": "no_witness", "note": "blocked; see first_blocker"}
    else:
        g = B.gate(g2, master, names, lanes, paths)
        rep["registered_gates"] = g
        rep["n_drawn"] = len(paths)
        rep["decision"] = ("DEFECT-CORRECTED ONE-SHOT DRAWING COMPLETE: %d/%d lanes drawn in one pass; registered "
                           "gates %s" % (len(paths), len(names), g["requirement_level_gate"]))
        rep["buildability"] = {"mode": "no_move" if g["requirement_level_gate"] == "PASS" else "no_witness",
                               "note": "single-pass track-band drawing on the defect-corrected graph; no other object moved"}
        if g["requirement_level_gate"] == "PASS":
            json.dump({nm: {"waypoints": spec["per_lane"][nm]["waypoints"], "repaired_slots": repair[nm],
                            "path_nodes": [int(x) for x in paths[nm]]} for nm in names},
                      open(os.path.join(HERE, "K2_R548d_DRAWING_PER_LANE_v1.json"), "w"), ensure_ascii=False, indent=1)
    rep["conservation_audit"] = {"source": "K2_R537_CONSERVATION_CUT_v1.json", "reading": "156 割无墙，最紧余 +37"}
    rep["elapsed_s"] = round(time.time() - t0, 1); rep["fail_loud_log"] = LOGF
    body = json.dumps({k: v for k, v in rep.items() if k != "artifact_hash16"}, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    B.log("WROTE %s" % a.out); B.log("OWNER-ITEMS: 0")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as _e:
        import traceback; traceback.print_exc(); print('FAIL_LOUD: {"error": %r}' % (str(_e),), flush=True); sys.exit(3)
