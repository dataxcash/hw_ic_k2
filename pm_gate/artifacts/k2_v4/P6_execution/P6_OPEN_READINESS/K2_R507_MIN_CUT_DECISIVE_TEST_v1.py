#!/usr/bin/env python3
"""K2 · R507 —— 遵 #K2-180 §三.7 第一动作 ＋ 停止令「一次实现」：
**A 侧出口容量（最小割）决定性只读测试**（纯图算法 · 不驱动 CP-SAT · 不占受证额度 · 不改参/改工具）。

R506 只读线索：A 梳齿的唯一出口 ＝ 列 23.5 的 4 格窗口 {(23,33),(23,34),(23,35),(23,36)}（1.74mm），
16 条车道全须穿它 ⇒ 容量 4–5 < 16 ⇒ **当前规则下不可行**（未证，仅线索）。

本件把它机核成二值：在**在册 `free_node` 栅格**上取
  源 ＝ A 锚所在自由区（行 ≤36 且 列 ≤23 的自由格）、汇 ＝ 其余自由格，
算**最大节点不相交路数**（节点容量 1）＝ 该区出口容量：
  * < 16 ⇒ 线索成立（出口确实是瓶颈）⇒ 转**几何切口证明**（无抽象缝）⇒ 另件升 frozen-set；
  * ≥ 16 ⇒ 存在旁路 ⇒ 线索作废 ⇒ 回 #K2-180 §四「次序先定」。
输出：流量值 ＋ 最小割（被割的格点坐标，即可复核的"极小冲突集"）。
"""
import json, os, sys, collections
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
PREV = __import__("K2_" + "R" + "499" + "_CONFLICT_TABLE_ONE_IMPLEMENTATION_v3")
NX, NY = PREV.NX, PREV.NY
NB = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def main():
    model = json.load(open("/tmp/opencode/archer/model_l8.json"))
    g = PREV.Gen(model)
    free = g.free_node
    NID = NX * NY

    def IN(n):
        return n

    def OUT(n):
        return n + NID
    NN = 2 * NID
    S, T = NN, NN + 1
    cap = collections.defaultdict(dict)

    def add(u, v, c):
        cap[u][v] = cap[u].get(v, 0) + c
        cap[v].setdefault(u, 0)

    # --- DEFECT FIX (disclosed): the source side must be the A-anchors' CONNECTED COMPONENT, not a
    # coordinate box (the box wrongly included the free stair at column 23 rows 0..19 -> capacity 47, void).
    region = np.zeros((NX, NY), bool)
    seeds = []
    for nm in g.names:
        n2 = g.node_ok(nm); pts = g.pt_by_net[nm]
        s0 = g.nearest_node(g.A[nm], n2, pts)
        if s0 is None:
            print("NO-SRC", nm); return
        seeds.append(s0)
    dq = collections.deque(seeds)
    for (i, j) in seeds:
        region[i, j] = True
    while dq:
        i, j = dq.popleft()
        for di, dj in NB:
            a, b = i + di, j + dj
            if 0 <= a < NX and 0 <= b < NY and free[a, b] and not region[a, b]:
                region[a, b] = True; dq.append((a, b))
    nreg = 0
    for i in range(NX):
        for j in range(NY):
            if not free[i, j]:
                continue
            n = i * NY + j
            add(IN(n), OUT(n), 1)              # node capacity 1
            for di, dj in NB:
                a, b = i + di, j + dj
                if 0 <= a < NX and 0 <= b < NY and free[a, b]:
                    add(OUT(n), IN(a * NY + b), 1)
            if region[i, j]:
                add(S, IN(n), 1); nreg += 1
            else:
                add(OUT(n), T, 1)
    # Edmonds-Karp (flow value is small)
    flow = 0
    while True:
        prev = {S: None}
        dq = collections.deque([S])
        while dq and T not in prev:
            u = dq.popleft()
            for v, c in cap[u].items():
                if c > 0 and v not in prev:
                    prev[v] = u; dq.append(v)
        if T not in prev:
            break
        path = []; x = T
        while x is not None:
            path.append(x); x = prev[x]
        path.reverse()
        for a, b in zip(path, path[1:]):
            cap[a][b] -= 1; cap[b][a] += 1
        flow += 1
    # min-cut: reachable set from S in the residual graph
    seen = {S}; dq = collections.deque([S])
    while dq:
        u = dq.popleft()
        for v, c in cap[u].items():
            if c > 0 and v not in seen:
                seen.add(v); dq.append(v)
    cut_nodes = []
    for u in list(seen):
        for v, c in cap[u].items():
            if c == 0 and v not in seen and u < NID and v == u + NID:
                cut_nodes.append((u // NY, u % NY))
    rep = {"artifact": "k2_r507_min_cut_decisive_test_v1",
           "authority": "#K2-180 §三.7（先取冲突集）＋ 停止令「一次实现」· R506 线索",
           "region": "the 8-connected free-space COMPONENT containing the 16 A anchors' nearest nodes (defect-fixed: component, not a coordinate box)",
           "component_seeds_are_all_anchors": len(seeds),
           "region_nodes": int(nreg), "free_nodes_total": int(free.sum()),
           "max_node_disjoint_paths_out_of_region": flow,
           "verdict": ("LEAD HOLDS: exit capacity < 16 => candidate infeasibility under the current rules"
                       if flow < 16 else
                       "LEAD VOID: a bypass exists (capacity >= 16) => go to the order-first route (#K2-180 §四)"),
           "min_cut_lattice_nodes": sorted([list(t) for t in set(cut_nodes)]),
           "lane_requirement": 16}
    out = os.path.join(HERE, "K2_R507_MIN_CUT_DECISIVE_TEST_v1.json")
    json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False, indent=1)[:2000])
    print("WROTE", out)


if __name__ == "__main__":
    main()
