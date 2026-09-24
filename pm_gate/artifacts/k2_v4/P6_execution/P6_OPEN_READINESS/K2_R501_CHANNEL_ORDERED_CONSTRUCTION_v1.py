#!/usr/bin/env python3
"""K2 · R501 —— 遵《方法教令 #4》（#K2-178 §四）**一次实现窗**：**有序（次序）构造**：
把「谁先谁后 / 谁里谁外」当**决策变量**处理 —— 逐车道在**残差自由通道图**上取最短走线，
并按**通道次序**（先西侧需穿墙窄门的车道、后东侧车道）逐条落位；
**域 = 自由栅格节点/弧（非候选族枚举）**，最小间距由**节点容量**＋**胞内 5 类线性净距形态**保证。

权威：#K2-178 §四（换范式 · 序变量＋连续位置/次序 · 一次实现窗 · §七 非终局处置）·
#K2-177 §一/§三（真终局三分支）· #K2-175 §四.5（单遍纪律）· handoff-K2-499 §0 · R494 先例（实现缺陷可修一次）。

## 与 #K2-178 §四 的落点
| 教令 | 本件 |
|---|---|
| ① 次序题 | 车道**次序**是构造的显式决策（谁先占位、谁走哪条通道/哪个墙缝）|
| ② 域 = 决策变量，非穷举候选表 | 域 = **自由栅格弧**；无 `AddForbiddenAssignments`、无候选族 |
| ③ 在册学习案例 | R455（序/单调）· R362/C-B2UP-1（有序多商品流）· 在册 `exact_gate`（要求级谓词）|
| ④ 验收硬判据 | 前置全绿 → 同窗一次构造 → 渲染 → **独立在册 `exact_gate`**（fail-closed）|

## 结构性发现（本窗的设计读数，只读）
1. **两条独立通道**：a) 北西**竖直通道**（列 51–78，行 17–36 自由）；b) **皮带＋门**（行 ≥37 大自由区 → 列 115–137 行 36 门）。
2. **墙（列 114–115，行 17–37）上有 8 个 1 格宽墙缝**（行 7,11,12,13,15,24,25,28）——**正好 8 个「西侧 B」车道**（B 列 99–110）须穿越；东侧 8 个（B 列 119–132）不穿越。
   ⇒ R497/R498/R499 的族（单皮带行＋单门位子＋单街道）**表达不了**「每条车道各自走自己的墙缝」⇒ 族级筛必零相容（具名解释 5 次撞墙）。
3. 故本窗不再枚举族，而**逐条按次序构造**：先西侧（需墙缝）后东侧；每条取残差图最短路（长度 ＋ 轻度拥塞斥力）。
4. 最小间距保证：**节点容量 1**（两线不可同格）＋ **胞内 5 类**（对角↔邻点 ×4 ＋ 两对角互交）——与 R500 §二.2 同族，本件按序构造时逐步施加。

**纪律**：一次实现、同窗只构造一次、前置不全绿 fail-closed、不改参重跑、不在半成品上开跑。

## IMPLEMENTATION NOTE（据实披露 · 2026-09-24）
- **D1（已修 · 只修一次）**：首跑把「flat index 递增取向」当成搜索用的弧，反向只塞进未使用的 `radj`
  ⇒ 出闸北上（递减跳）不可达 ⇒ 16/16 报 no legal path（退化执行，非本窗有效执行）。已改为两向都放。
- **D2（未再跑）**：本件 §3 声明的构造次序是「先西侧（需墙缝）后东侧」；实现实际按 `free_around_B` 升序
  （最紧者先）⇒ **被执行的并非声明的方法**。依单遍纪律（已用掉一次缺陷修复）**不再自转第 3 次**；
  正确次序已冻结于《R501 读数与缺陷》§四(1)，待一句话授权后恰跑一次。
**本窗读数**：前置全绿；执行 #1 = 0/16（D1）；执行 #2（修 D1 后）= **2/16**，无终局主张；`Solve()` 0 次。
"""
import argparse, collections, hashlib, heapq, json, math, os, sys, time
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
PREV = __import__("K2_" + "R" + "499" + "_CONFLICT_TABLE_ONE_IMPLEMENTATION_v3")
P, HW, NY, NX = PREV.P, PREV.HW, PREV.NY, PREV.NX
XY = PREV.XY
NID = NX * NY

NB8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))

# ---- 冻结的构造参数（本窗前定，非搜索） ----
REF_R = 2          # repulsion radius (lattice steps)
REF_LAM = 0.45     # repulsion weight (mm per step of deficit)


def cell_of_diag(u, v):
    """return (i, j, orient) for a diagonal lattice edge; orient=+1 for (i,j)-(i+1,j+1)."""
    iu, ju = u // NY, u % NY
    iv, jv = v // NY, v % NY
    i, j = min(iu, iv), min(ju, jv)
    orient = 1 if ju == jv else -1
    return i, j, orient


def offdiag_nodes(i, j, orient):
    if orient == 1:                      # a-c diagonal
        return i * NY + (j + 1), (i + 1) * NY + j          # d, b
    return i * NY + j, (i + 1) * NY + (j + 1)              # a, c


def simplify(pts):
    out = [pts[0]]
    for q in pts[1:]:
        out.append(q)
    res = [out[0]]
    for k in range(1, len(out) - 1):
        a, b, c = res[-1], out[k], out[k + 1]
        cr = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if abs(cr) > 1e-12:
            res.append(b)
    if len(out) > 1:
        res.append(out[-1])
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="/tmp/opencode/archer/model_l8.json")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    code = "R" + "501"
    out = a.out or os.path.join(HERE, "K2_%s_CHANNEL_ORDERED_CONSTRUCTION_v1.json" % code)
    t00 = time.time()
    model = json.load(open(a.model))
    rep = {"artifact": "k2_%s_channel_ordered_construction_v1" % code.lower(),
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-178 §四 方法教令#4（次序＋连续位置/有序范式）· 一次实现窗 · #K2-177 §一/§三 · #K2-175 §四.5",
           "paradigm": "ordered sequential construction on the free lattice (domain = free arcs, NOT a candidate family); "
                       "node capacity 1 + within-cell 5 linear clearance patterns"}

    g = PREV.Gen(model)
    rep["preexisting_gates"] = PREV.gate_preexisting(model, g, 16)
    pre_ok = bool(rep["preexisting_gates"]["all_pass"])
    rep["preconditions_all_green"] = pre_ok
    if not pre_ok:
        rep["decision"] = "STOP-BEFORE-CONSTRUCT: 前置硬闸未全绿 ⇒ fail-closed"
        json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
        print("FAIL-FAST", out)
        return

    # ---- per-lane legal graph ----
    lanes = []
    for nm in g.names:
        n2 = g.node_ok(nm); nok = n2.reshape(-1); eok = g.edge_ok(nm)
        pts = g.pt_by_net[nm]
        s0 = g.nearest_node(g.A[nm], n2, pts)
        t0 = g.nearest_node(g.B[nm], n2, pts, taken=(s0,))
        src = s0[0] * NY + s0[1]; snk = t0[0] * NY + t0[1]
        keep = eok & nok[g.edge_u] & nok[g.edge_v]
        eu, ev, el = g.edge_u[keep].tolist(), g.edge_v[keep].tolist(), g.edge_len[keep].tolist()
        adj = collections.defaultdict(list); radj = collections.defaultdict(list)
        for u, v, L in zip(eu, ev, el):
            # SYMMETRIC arcs -- every lattice edge stored once must be added in BOTH orientations
            # (defect fixed: the first execution of this window only added the flat-index-increasing
            #  orientation to the graph the search actually uses, so the northbound decreasing-index
            #  hops were unreachable and every lane reported 'no legal path'.)
            adj[u].append((v, L)); adj[v].append((u, L))
        # snk free-space difficulty (for the deterministic lane order)
        ii, jj = snk // NY, snk % NY
        w = 0
        for di in range(-2, 3):
            for dj in range(-2, 3):
                x, y = ii + di, jj + dj
                if 0 <= x < NX and 0 <= y < NY and nok[x * NY + y]:
                    w += 1
        lanes.append({"nm": nm, "nok": nok, "adj": adj, "radj": radj, "src": src, "snk": snk,
                      "A": tuple(g.A[nm]), "B": tuple(g.B[nm]), "free_around_B": w,
                      "Bx": g.B[nm][0]})
    # deterministic order: most-constrained B anchor first (fewest legal nodes in its 5x5 box)
    lanes.sort(key=lambda d: (d["free_around_B"], d["Bx"], d["nm"]))
    rep["lane_order"] = [d["nm"] for d in lanes]

    # ---- ordered residual construction ----
    used_node = {}                    # node -> lane index
    diag_block_node = set()           # nodes too close to an already-placed diagonal
    diag_cell_used = set()            # cells whose diagonal is already placed
    routes = {}; placed = []
    feasible = True
    for li, L in enumerate(lanes):
        if li:
            mask = np.zeros((NX, NY), bool)
            for n in used_node:
                mask[n // NY, n % NY] = True
            dist = ndimage.distance_transform_edt(~mask)      # lattice-step distance to nearest placed lane node
        else:
            dist = None
        INF = float("inf")
        best = {L["src"]: 0.0}; prev = {}; pq = [(0.0, L["src"])]
        while pq:
            d, u = heapq.heappop(pq)
            if d > best.get(u, INF) + 1e-12:
                continue
            if u == L["snk"]:
                break
            for v, Ln in L["adj"][u]:
                if v in used_node:
                    continue
                if v in diag_block_node:
                    continue
                du, ju = u // NY, u % NY; dv, jv = v // NY, v % NY
                if du != dv and ju != jv:                      # diagonal move
                    i, j, orient = cell_of_diag(u, v)
                    if (i, j) in diag_cell_used:
                        continue
                    n1, n2_ = offdiag_nodes(i, j, orient)
                    if n1 in used_node or n2_ in used_node:
                        continue
                pen = 0.0
                if dist is not None:
                    pen = REF_LAM * max(0.0, REF_R - float(dist[v // NY, v % NY]))
                nd = d + Ln + pen
                if nd < best.get(v, INF) - 1e-12:
                    best[v] = nd; prev[v] = u
                    heapq.heappush(pq, (nd, v))
        if L["snk"] not in best:
            feasible = False
            placed.append({"nm": L["nm"], "routed": False, "reason": "no legal path in residual graph"})
            continue
        path = []; cur = L["snk"]
        while cur is not None:
            path.append(cur); cur = prev.get(cur)
        path.reverse()
        # register usage + clearance patterns
        for n in path:
            used_node[n] = li
        for u, v in zip(path, path[1:]):
            du, ju = u // NY, u % NY; dv, jv = v // NY, v % NY
            if du != dv and ju != jv:
                i, j, orient = cell_of_diag(u, v)
                diag_cell_used.add((i, j))
                n1, n2_ = offdiag_nodes(i, j, orient)
                diag_block_node.add(n1); diag_block_node.add(n2_)
        pts = [L["A"]] + [XY(q // NY, q % NY) for q in path] + [L["B"]]
        pts = [tuple(round(c, 4) for c in p) for p in simplify([tuple(x) for x in pts])]
        routes[L["nm"]] = {"pts": [list(p) for p in pts], "layer_cu": "In5.Cu", "n_vias": 2}
        placed.append({"nm": L["nm"], "routed": True, "n_pts": len(pts),
                       "len_mm": round(sum(math.dist(pts[k], pts[k + 1]) for k in range(len(pts) - 1)), 3)})
    rep["construction"] = {"feasible_all": feasible, "routed": sum(1 for q in placed if q["routed"]),
                           "n_lanes": len(lanes), "per_lane": placed}

    if not feasible or len(routes) != len(lanes):
        rep["decision"] = "NON-TERMINAL: 构造未覆盖全部车道（无终局主张；顺序构造不完备 ⇒ 不构成不可行证据）"
        rep["elapsed_s"] = round(time.time() - t00, 1)
        json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
        print(json.dumps(rep["construction"], ensure_ascii=False, indent=1)[:2500]); print("WROTE", out)
        return

    json.dump(routes, open(os.path.join(HERE, "K2_%s_CONSTRUCTION_ROUTES_v1.json" % code), "w"),
              ensure_ascii=False)
    gg = PREV.exact_gate(model, routes, g.an, "In5.Cu", HW, set(), set(), P, frozenset())
    rep["exact_gate"] = {k: gg[k] for k in ("n_lane_pitch_viol", "lane_pitch_min_gap_mm", "lane_pitch_min_pair",
                                            "n_clearance_viol", "clearance_min_mm", "endpoint_max_dev_mm")
                         if k in gg}
    rep["per_lane_margin"] = gg.get("per_lane")
    ok = (gg.get("n_lane_pitch_viol") == 0 and gg.get("n_clearance_viol") == 0
          and gg.get("endpoint_max_dev_mm") == 0)
    rep["requirement_level_gate"] = "PASS" if ok else "FAIL"
    rep["decision"] = ("TERMINAL SAT: 16/16 构造 + 在册 exact_gate 全绿 ⇒ P3 过（#K2-177 §三 分支一）"
                       if ok else "NON-TERMINAL: 独立核 FAIL")
    rep["elapsed_s"] = round(time.time() - t00, 1)
    json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: rep[k] for k in ("construction", "exact_gate", "requirement_level_gate",
                                          "decision", "elapsed_s")}, ensure_ascii=False, indent=1)[:2500])
    print("WROTE", out)


if __name__ == "__main__":
    main()
