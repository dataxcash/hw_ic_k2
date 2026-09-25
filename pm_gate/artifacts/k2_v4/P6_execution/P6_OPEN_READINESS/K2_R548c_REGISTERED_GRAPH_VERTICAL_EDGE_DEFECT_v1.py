#!/usr/bin/env python3
"""K2 · R548c —— **在册画图图的实现缺陷证书**：整族"竖直边"被静默丢弃 ⇒ 任何"在同一列里上下走"都不存在。
（承监理停止令：本件是**一次只读根因取证**，非搜索、非调参、非重跑；不改生成器、不改任何在册件。）

【发现】
 在册图源链：`K2_R497`（BFS 用全 8 邻域，正确）→ `K2_R498_..._v2` / `K2_R499_..._v3._build_edges`（首次造显式边表）
 → 被 `K2_R512/R515/…` 全盘继承（含 Gen2 · R541/R543/R545/R548 所有联合/构造模型都跑在它上面）。
 `_build_edges` 里的去重过滤器写成：
     m2 = aa < ba          # aa=起列, ba=终列
 它只保留"列号严格变大"的边 ⇒ **(0,+1) 与 (0,-1) 两族竖直边全部命中 aa == ba ⇒ 被整族丢掉**；
 边表里因此只剩 (东, 东北/东南) 两族。
【后果（机核）】
 · 全图**没有任何竖直边** ⇒ 一根线**不可能沿同一列上下移动**；
 · 每个"在入口列下钻到目标行"的动作（R529 入口动作 / 任何人手扇出方案的前提）在这个图里**做不到**，
   只能绕（东+对角），往北走还要"西+北"补偿 ⇒ 极度受限；
 · 早前一切"不可行 / 带内无通路 / 入口带 ≤10 走廊 / 余量"读数（R543 0.2s INFEASIBLE · R541 3/16 ·
   R546 卡点报告 · R548 未收敛 · R548b 第 1 根线被挡）**都是在这个缺边图上算出来的**，**不得**当作板级结论。
【修复（一行 · 属生成器，须监理授权）】
     m2 = (aa < ba) | ((aa == ba) & (ab < bb))      # 无向边按字典序去重 ⇒ 恢复整族竖直边
【边界】只读 · 0 求解器 · 0 受证配额 · 未改生成器/SPEC/原理图/criteria/R540/R529 · 停线维持。
"""
import argparse, collections, hashlib, importlib, json, os, sys, time, types
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
OWN_OUT = "K2_R548c_REGISTERED_GRAPH_VERTICAL_EDGE_DEFECT_v1.json"
LOGF = "/tmp/opencode/r548/r548c_edge_defect.log"
MODEL = "/tmp/opencode/archer/model_l8.json"


def log(m):
    os.makedirs(os.path.dirname(LOGF), exist_ok=True); open(LOGF, "a").write(str(m) + "\n"); print(m, flush=True)


def shim():
    if "ortools" in sys.modules: return
    for nm in ("ortools", "ortools.sat", "ortools.sat.python"): sys.modules.setdefault(nm, types.ModuleType(nm))
    cm = types.ModuleType("ortools.sat.python.cp_model")
    class _D:
        def __init__(self, *a, **k): pass
    cm.CpModel = _D; cm.CpSolver = _D; sys.modules["ortools.sat.python.cp_model"] = cm
    sys.modules["ortools.sat.python"].cp_model = cm


shim()
W = importlib.import_module("K2_R515_FREETERMINALS_v1")
NX, NY, NID = W.NX, W.NY, W.NID
NB = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def build(as_registered=True):
    """re-derive the base edge list with the registered filter (aa<ba) or the intended undirected dedupe."""
    ai = np.repeat(np.arange(NX), NY); aj = np.tile(np.arange(NY), NX)
    pairs = []
    for di, dj in NB:
        bi = ai + di; bj = aj + dj
        m = (bi >= 0) & (bi < NX) & (bj >= 0) & (bj < NY)
        aa, ab, ba, bb = ai[m], aj[m], bi[m], bj[m]
        m2 = (aa < ba) if as_registered else ((aa < ba) | ((aa == ba) & (ab < bb)))
        pairs += list(zip(aa[m2].tolist(), ab[m2].tolist(), ba[m2].tolist(), bb[m2].tolist()))
    return pairs


def hist(pairs):
    c = collections.Counter((abs(a - b2), abs(b - d)) for (a, b, b2, d) in pairs)
    return {("%d,%d" % k): v for k, v in sorted(c.items())}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, OWN_OUT))
    a = ap.parse_args()
    if os.path.basename(a.out) != OWN_OUT:
        raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7)")
    open(LOGF, "w").close(); t0 = time.time()
    reg = build(True); intended = build(False)
    log("[edge] registered pairs=%d histogram=%s" % (len(reg), hist(reg)))
    log("[edge] intended(undirected-dedupe) pairs=%d histogram=%s" % (len(intended), hist(intended)))
    vert = [p for p in intended if p[0] == p[2]]         # same column = vertical family
    vert_reg = [p for p in reg if p[0] == p[2]]
    rep = {"artifact": "k2_r548c_registered_graph_vertical_edge_defect_v1",
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "stop-order response: back to Plan + machine root-cause probe (read-only, one run, no search)",
           "source": "K2_R498_CONFLICT_TABLE_ONE_IMPLEMENTATION_v2._build_edges (line 'm2 = aa < ba') "
                     "inherited by K2_R499_..._v3 -> K2_R512 -> K2_R515 Gen2 -> every joint/construction model",
           "registered_edge_histogram": hist(reg),
           "intended_undirected_dedupe_histogram": hist(intended),
           "vertical_pairs_intended": len(vert), "vertical_pairs_present_in_registered": len(vert_reg),
           "defect": "the de-dup filter 'm2 = aa < ba' compares only the COLUMN index, so both vertical families "
                     "(delta_col = 0, delta_row = +-1) satisfy aa == ba and are DROPPED ENTIRELY; the edge set keeps "
                     "only the east (1,0) and diagonal (1,1) families.",
           "one_line_fix": "m2 = (aa < ba) | ((aa == ba) & (ab < bb))",
           "consequence": "no lane graph in the registered model can move between two nodes in the SAME column; every "
                          "'descend in your own entrance column' step (R529 entrance actions; any human fan-out plan) "
                          "is impossible; northbound progress needs west+north compensation. Hence earlier infeasibility "
                          "/blocked readings are artifacts of a broken graph and MUST be recomputed."}
    log("[stage] gen2 building (for lane-arc histogram + same-column adjacency check) ...")
    g2 = W.Gen2(json.load(open(MODEL)), l1scope="full"); names = list(g2.names)
    lanes = {nm: g2.build_lane(nm) for nm in names}
    vcheck = {}
    for nm in names:
        segs = 0; same_col_pairs = 0; same_col_edges = 0
        for u, lst in lanes[nm]["adj"].items():
            if u >= NID: continue
            cu, ru = (u % NID) // NY, (u % NID) % NY
            for (v, _w) in lst:
                if v >= NID: continue
                cv, rv = (v % NID) // NY, (v % NID) % NY
                if cu == cv and abs(ru - rv) == 1: same_col_edges += 1
        # how many same-column adjacent pairs are BOTH legal nodes but NOT edges
        n0 = g2._nok[(nm, 0)]
        for c in range(NX):
            for r in range(NY - 1):
                p, q = c * NY + r, c * NY + r + 1
                if n0[p] and n0[q]:
                    same_col_pairs += 1
                    if (0 * NID + q) in lanes[nm]["adj"].get(0 * NID + p, ()): pass
        vcheck[nm] = {"same_col_adjacent_legal_pairs": same_col_pairs, "same_col_edges_in_graph": same_col_edges}
    rep["per_lane_vertical_edges"] = vcheck
    rep["all_lanes_have_zero_vertical_edges"] = all(v["same_col_edges_in_graph"] == 0 for v in vcheck.values())
    rep["buildability"] = {"mode": "no_witness_until_fixed",
                          "note": "no drawing verdict is valid on the registered graph; fix the edge enumeration, "
                                  "re-run the pre-gates, then draw"}
    rep["elapsed_s"] = round(time.time() - t0, 1); rep["fail_loud_log"] = LOGF
    body = json.dumps({k: v for k, v in rep.items() if k != "artifact_hash16"}, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    log("[verdict] vertical edges present in registered graph = %s ; all-lanes-zero = %s"
        % (len(vert_reg), rep["all_lanes_have_zero_vertical_edges"]))
    log("WROTE %s" % a.out); log("OWNER-ITEMS: 0")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as _e:
        import traceback; traceback.print_exc(); print('FAIL_LOUD: {"error": %r}' % (str(_e),), flush=True); sys.exit(3)
