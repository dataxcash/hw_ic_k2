#!/usr/bin/env python3
"""K2 · R514-v2 归因（只读 · Solve() 0 次）—— v2 的 INFEASIBLE **假设核为空** ⇒ 矛盾在**硬约束**里。
本件用**纯图论最大流**（非 CP-SAT）在**同一个已剪枝双层图**上数：**放松"规定身份配对"**后，
16 条**节点不相交**流是否放得下（节点容量 1 = 模型里的 claim/节点占用语义）。
  · = 16 ⇒ 容量不是墙 ⇒ 墙 = **规定身份配对本身**（⇒ 二层亦未化解 ⇒ 下一支 = L1 球重映射，须 owner）
  · < 16 ⇒ 我的图/剪枝把容量掐了 ⇒ 属**模型过保守**，需先修再谈配对
"""
import argparse, collections, importlib, json, os, sys, time
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_flow

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
R514 = importlib.import_module("K2_" + "R" + "514" + "_LAYERHOP_JOINT_MCF_v2")


def maxflow_of(lanes, NID, use_via=True):
    nodes = set()
    arcs = set()
    via_arcs = set()
    for L in lanes:
        for u, lst in L["adj"].items():
            nodes.add(u)
            for (v, w) in lst:
                nodes.add(v)
                (via_arcs if (u % NID) == (v % NID) else arcs).add((u, v))
    if use_via:
        arcs |= via_arcs
    N = sorted(nodes); idx = {n: i for i, n in enumerate(N)}
    NN = 2 * len(N)
    S = NN; T = NN + 1
    rows = []; cols = []; cap = []
    for n in N:
        rows.append(2 * idx[n]); cols.append(2 * idx[n] + 1); cap.append(1)      # node capacity 1
    for (u, v) in arcs:
        rows.append(2 * idx[u] + 1); cols.append(2 * idx[v]); cap.append(1)
    for L in lanes:
        rows.append(S); cols.append(2 * idx[L["src"]]); cap.append(1)
        rows.append(2 * idx[L["snk"]] + 1); cols.append(T); cap.append(1)
    g = csr_matrix((np.array(cap, np.int32), (np.array(rows), np.array(cols))), shape=(NN + 2, NN + 2))
    r = maximum_flow(g, S, T)
    flow = int(r.flow_value)
    # min cut localisation (residual reachable from S)
    try:
        res = r.residual
    except AttributeError:
        res = (g - r.flow).tocsr()
    seen = np.zeros(NN + 2, bool); seen[S] = True
    stack = [S]
    coo = res.tocoo()
    adj = collections.defaultdict(list)
    for u, v, c in zip(coo.row.tolist(), coo.col.tolist(), coo.data.tolist()):
        if c > 0:
            adj[u].append(v)
    while stack:
        u = stack.pop()
        for v in adj[u]:
            if not seen[v]:
                seen[v] = True; stack.append(v)
    cut = [rc for n, rc in ((N[i // 2], (N[i // 2] // NID, N[i // 2] % NID)) for i in range(len(N)))
           if seen[2 * idx[n]] and not seen[2 * idx[n] + 1]]
    return {"n_nodes": len(N), "n_arcs": len(arcs), "n_via_arcs": len(via_arcs),
            "pairing_free_max_node_disjoint_paths": flow,
            "cut_nodes_sample": [[R514.LAYER_OF[c[0]], *list(R514.rc(c[1]))] for c in cut[:12]],
            "n_cut_nodes": len(cut)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or os.path.join(HERE, "K2_R514_V2_HARD_ATTRIBUTION_v1.json")
    model = json.load(open("/tmp/opencode/archer/model_l8.json"))
    t0 = time.time()
    g2 = R514.Gen2(model, l1scope="full", verbose=True)
    lanes = [g2.build_lane(nm) for nm in g2.names]
    rep = {"artifact": "k2_r514_v2_hard_attribution_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "attribution of the v2 INFEASIBLE (empty assumption core) -- read-only; Solve() 0 calls",
           "question": "on the SAME pruned 2-layer graph, with the prescribed identity pairing RELAXED, "
                       "how many pairwise node-disjoint lanes fit (node capacity 1 per node per layer)?",
           "n_via_arcs_per_lane": [sum(1 for (u, v) in L['vias']) for L in lanes]}
    rep["with_via_arcs"] = maxflow_of(lanes, R514.NID, use_via=True)
    rep["without_via_arcs_in5_only"] = maxflow_of(lanes, R514.NID, use_via=False)
    rep["verdict"] = ("capacity >= 16 => the wall is the PRESCRIBED IDENTITY PAIRING (multi-commodity), "
                      "not capacity" if rep["with_via_arcs"]["pairing_free_max_node_disjoint_paths"] >= 16
                      else "capacity < 16 => my graph/pruning over-constrains; fix before blaming the pairing")
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(rep, ensure_ascii=False, indent=1)[:2500]); print("WROTE", out)
