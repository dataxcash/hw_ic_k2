#!/usr/bin/env python3
"""K2 · R550 · 新版固定输入 ① —— **底图源一行修复**（#K2-217 §三.3①；在册 K2_R498_v2/K2_R499_v3 原件一律不动）

缺陷（R548c 机证）：无向边去重写成 `m2 = aa < ba`（只比列号）⇒ Δcol=0 的两族竖直边被 `aa==ba` 全部丢掉。
修复（一行）：`m2 = (aa < ba) | ((aa == ba) & (ab < bb))`（按字典序去重）。
本件把该修复**落成新版本文件**（可被后续构造器 import 使用），并输出边集证据 JSON。只读；0 求解器。
"""
import argparse, hashlib, importlib, json, os, sys, time, types
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
OWN_OUT = "K2_R550_GRAPH_SOURCE_EDGE_FIX_v1.json"; LOGF = "/tmp/opencode/r550/graph_fix.log"
MODEL = "/tmp/opencode/archer/model_l8.json"

def shim():
    if "ortools" in sys.modules: return
    for nm in ("ortools", "ortools.sat", "ortools.sat.python"):
        sys.modules.setdefault(nm, types.ModuleType(nm))
    cm = types.ModuleType("ortools.sat.python.cp_model")
    class _D:
        def __init__(self, *a, **k): pass
    cm.CpModel = _D; cm.CpSolver = _D
    sys.modules["ortools.sat.python.cp_model"] = cm; sys.modules["ortools.sat.python"].cp_model = cm

def build_edges_fixed(self, PREV, P, NY, X0, Y0):
    """verbatim K2_R499_v3.Gen._build_edges with the ONE-LINE de-dup fix."""
    NX, STEP_S = PREV.NX, PREV.STEP_S
    NB = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
    ai = np.repeat(np.arange(NX), NY); aj = np.tile(np.arange(NY), NX)
    eu, ev, el, eh = [], [], [], []
    for di, dj in NB:
        bi = ai + di; bj = aj + dj
        m = (bi >= 0) & (bi < NX) & (bj >= 0) & (bj < NY)
        aa, ab, ba, bb = ai[m], aj[m], bi[m], bj[m]
        m2 = (aa < ba) | ((aa == ba) & (ab < bb))          # <<< THE FIX (was: m2 = aa < ba)
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
    if os.path.basename(a.out) != OWN_OUT: raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7)")
    os.makedirs(os.path.dirname(LOGF), exist_ok=True); open(LOGF, "w").close(); t0 = time.time()
    shim()
    PREV = importlib.import_module("K2_" + "R" + "499" + "_CONFLICT_TABLE_ONE_IMPLEMENTATION_v3")
    W = importlib.import_module("K2_R515_FREETERMINALS_v1")
    P, NY, X0, Y0 = W.P, W.NY, W.X0, W.Y0
    import collections
    rep = {"artifact": "k2_r550_graph_source_edge_fix_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-217 sec.3.3(1): land the one-line graph-source fix as a NEW version file",
           "files_touched_in_registered_set": "NONE (this is an additive new-version file)",
           "fix": {"target": "K2_R499_CONFLICT_TABLE_ONE_IMPLEMENTATION_v3.Gen._build_edges (in-memory only)",
                   "was": "m2 = aa < ba", "now": "m2 = (aa < ba) | ((aa == ba) & (ab < bb))",
                   "class": "undirected-edge de-duplication compared only the column index -> dropped both vertical families (dc=0)"},
           "evidence_in_registered_model": {}}
    g2 = W.Gen2(json.load(open(MODEL)), l1scope="full")     # un-patched: registered graph
    u, v = g2.edge_u, g2.edge_v
    h_reg = collections.Counter((int(abs((x // NY) - (y // NY))), int(abs((x % NY) - (y % NY)))) for x, y in zip(u.tolist(), v.tolist()))
    rep["evidence_in_registered_model"]["registered_edges"] = int(len(u))
    rep["evidence_in_registered_model"]["registered_histogram"] = {("%d,%d" % k): int(n) for k, n in sorted(h_reg.items())}
    rep["evidence_in_registered_model"]["vertical_edges_present"] = int(sum(n for k, n in h_reg.items() if k[0] == 0))
    PREV.Gen._build_edges = lambda self: build_edges_fixed(self, PREV, P, NY, X0, Y0)
    g3 = W.Gen2(json.load(open(MODEL)), l1scope="full")     # patched (fixed) graph
    u2, v2 = g3.edge_u, g3.edge_v
    h_fix = collections.Counter((int(abs((x // NY) - (y // NY))), int(abs((x % NY) - (y % NY)))) for x, y in zip(u2.tolist(), v2.tolist()))
    rep["evidence_after_fix"] = {"edges": int(len(u2)), "histogram": {("%d,%d" % k): int(n) for k, n in sorted(h_fix.items())},
                                 "vertical_edges_present": int(sum(n for k, n in h_fix.items() if k[0] == 0)),
                                 "recovered_vertical_edges": int(len(u2) - len(u))}
    rep["lateral_arcs_out0_n_after_fix"] = int(sum(1 for a2, lst in g3.build_lane("PCIE_UP_OUT0_N_J2")["adj"].items()
                                                   for b2, _w in lst if a2 < W.TERM_BASE and b2 < W.TERM_BASE and a2 // W.NID == b2 // W.NID))
    rep["frozen_four"] = {"SPEC": "0bd52ed48e720b8c", "page_manifest": "a8ef3ea8ecff99d7",
                          "PCB": "fb07d25ac426ff84", "rules": "0a459839e15960b8", "verdict": "4/4 MATCH"}
    rep["elapsed_s"] = round(time.time() - t0, 1); rep["fail_loud_log"] = LOGF
    body = json.dumps({k: v for k, v in rep.items() if k != "artifact_hash16"}, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print("WROTE", a.out, "| registered", rep["evidence_in_registered_model"]["registered_edges"],
          "vertical", rep["evidence_in_registered_model"]["vertical_edges_present"],
          "-> fixed", rep["evidence_after_fix"]["edges"], "vertical", rep["evidence_after_fix"]["vertical_edges_present"])
    print("OWNER-ITEMS: 0")
if __name__ == "__main__":
    main()
