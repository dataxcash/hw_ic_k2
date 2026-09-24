#!/usr/bin/env python3
"""K2 · R527 —— **入口带过孔可用性实测**（只读 · 零额度 · `Solve()` 0 次 · **测事实，不实现方法**）。

缘起：R526 具名结论（`K2_R526_WOVEN_WITNESS_v1.json` · `access_band_analysis`）把卡点定位到**梳齿口入口带**：
16 根自然下降走廊里**最多 10 根**能同时在 In5 离开，⇒ **≥6 根必须在入口带内换到 In4**；
而本窗需监理裁决的第 ② 项是**在册口径事实**：「**COMB 区内是否存在每根线可达的合法过孔站**」。
本件**只测这个事实**（不改口径、不实现新法、不求解、不主张任何见证/不可行）：

  ① **几何可用性（与他线无关）**：每根线的 A 锚到**最近在册过孔站**（`via_positions`：两层均合法 ＋ 在册四宽区内 ＋ 满足他锚 keepout）的**距离与格数**，以及该站是否落在 **COMB 宽区**内；
  ② **可达性（在册声明集口径下）**：把**其余 15 根的自然下降走廊**（A 锚 → 各自院行，沿 A.x）的**声明集**全部占用后，
     从该线 A 锚的接触点出发、**只在 In5**做有界 BFS（≤4 格），看能否走到**任一在册过孔站**（= 能否"在带内下沉"）；
  ③ **汇总读数**：几何可用 / 声明集下可达 的**线数**（⇒ 直接回答监理第 ② 项：在册模型**够不够**）。

**口径**：只写件、只读数；`Solve()` = 0；**不 import** 无 `__main__` 保护的在册件；不改任何在册件。
"""
import argparse, collections, importlib, json, math, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
F = importlib.import_module("K2_R523_LAYERHOP_PARITY_FORMC_v1")

P, X0, Y0, NX, NY, NID = F.P, F.X0, F.Y0, F.NX, F.NY, F.NID
YARD_ROWS = list(range(38, 58))
ZONE_COMB = 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "K2_R527_ACCESS_BAND_VIA_AVAILABILITY_v1.json"))
    ap.add_argument("--reach", type=int, default=4, help="In5 有界 BFS 半径（格）")
    a = ap.parse_args()
    t0 = time.time()
    rep = {"artifact": "k2_r527_access_band_via_availability_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-193 sec.3.6 (report-and-wait) + R526 named conclusion; READ-ONLY fact finding, "
                        "zero-quota, 0 solves, NO method implementation, NO witness/certificate claim",
           "solve_calls": 0, "boundaries": "read-only; no board/SPEC/generator/criteria writes"}

    g2 = F.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names)
    order = sorted(names, key=lambda nm: g2.A[nm][0])
    # natural descent corridors (same convention as R526 access_band_analysis): nested yard rows, A.x columns
    yard = {nm: YARD_ROWS[len(order) - 1 - k] for k, nm in enumerate(order)}

    def zone_idx_of(pos):
        i, j = pos // NY, pos % NY
        x, y = X0 + i * P, Y0 + j * P
        for k, (x0, y0, x1, y1) in enumerate(F.ZONES):
            if x0 - 1e-9 <= x <= x1 + 1e-9 and y0 - 1e-9 <= y <= y1 + 1e-9:
                return k
        return None

    via_pos = {nm: set(g2.via_positions(nm).tolist()) for nm in names}
    via_comb = {nm: {p for p in via_pos[nm] if zone_idx_of(p) == ZONE_COMB} for nm in names}
    claim = {}
    for nm in order:
        A = tuple(g2.A[nm]); wy = Y0 + yard[nm] * P
        claim[nm] = set(F.claim_seg(A[0], A[1], A[0], wy))

    # per-lane contact nodes on In5: own-legal nodes whose straight leg from the anchor is legal (registered F1)
    g0 = g2.g0
    pts = g0.pt_by_net
    contact = {}
    for nm in names:
        A = tuple(g2.A[nm])
        idx = np.argwhere(g2._nok[(nm, 0)].reshape(NX, NY))
        xy = np.stack([X0 + idx[:, 0] * P, Y0 + idx[:, 1] * P], 1)
        d = np.hypot(xy[:, 0] - A[0], xy[:, 1] - A[1])
        cand = {}
        for (i, j) in idx[d <= F.R_REACH].tolist():
            if g0.seg_ok(A, (X0 + i * P, Y0 + j * P), pts[nm]):
                cand[i * NY + j] = float(math.hypot(X0 + i * P - A[0], Y0 + j * P - A[1]))
        contact[nm] = cand

    eu, ev = g2.edge_u, g2.edge_v
    rows = {}
    n_geo_ok = n_reach_ok = 0
    for nm in names:
        A = tuple(g2.A[nm])
        # (1) pure geometry: nearest registered via site, ignoring other lanes
        if via_pos[nm]:
            best = min(via_pos[nm], key=lambda p: math.hypot(X0 + (p // NY) * P - A[0], Y0 + (p % NY) * P - A[1]))
            d_mm = math.hypot(X0 + (best // NY) * P - A[0], Y0 + (best % NY) * P - A[1])
            steps = int(round(d_mm / P))
            in_comb = best in via_comb[nm]
        else:
            best, d_mm, steps, in_comb = None, None, None, False
        # (2) reachability with ALL OTHER lanes' natural corridors claimed (In5-only, bounded BFS)
        res0 = set().union(*[claim[o] for o in names if o != nm])
        bfs = collections.deque(); seen = set()
        for p in contact[nm]:
            if p not in res0:
                seen.add(p); bfs.append((p, 0))
        hit = None
        while bfs:
            p, dep = bfs.popleft()
            if p in via_comb[nm]:
                hit = p; break
            if dep >= a.reach:
                continue
            i, j = p // NY, p % NY
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                u, v = i + di, j + dj
                if not (0 <= u < NX and 0 <= v < NY):
                    continue
                q = u * NY + v
                if q in seen or q in res0 or not g2._nok[(nm, 0)][q]:
                    continue
                seen.add(q); bfs.append((q, dep + 1))
        # registered edge-based variant: only through own-layer-0 legal edges, also claim-free
        emask = g2._eok[(nm, 0)]
        adj = collections.defaultdict(set)
        for u, v in zip(eu[emask].tolist(), ev[emask].tolist()):
            if u in res0 or v in res0:
                continue
            adj[u].add(v); adj[v].add(u)
        bfs2 = collections.deque(); seen2 = set()
        for p in contact[nm]:
            if p not in res0:
                seen2.add(p); bfs2.append((p, 0))
        hit2 = None
        while bfs2:
            p, dep = bfs2.popleft()
            if p in via_comb[nm]:
                hit2 = p; break
            if dep >= a.reach:
                continue
            for q in adj[p]:
                if q not in seen2:
                    seen2.add(q); bfs2.append((q, dep + 1))
        rows[nm] = {"A_anchor_mm": [round(v, 3) for v in A], "yard_row": yard[nm],
                    "n_via_sites_all": len(via_pos[nm]), "n_via_sites_in_COMB": len(via_comb[nm]),
                    "nearest_via_site": (None if best is None else
                                         {"node": best, "x_mm": round(X0 + (best // NY) * P, 3),
                                          "y_mm": round(Y0 + (best % NY) * P, 3), "dist_mm": round(d_mm, 3),
                                          "lattice_steps": steps, "in_COMB_zone": in_comb}),
                    "reach_via_in_band_under_others_corridor_claims_lattice_bfs": hit is not None,
                    "reach_via_in_band_under_others_corridor_claims_registered_edges": hit2 is not None,
                    "n_contact_nodes": len(contact[nm])}
        if rows[nm]["nearest_via_site"] and rows[nm]["nearest_via_site"]["lattice_steps"] <= 2:
            n_geo_ok += 1
        if hit2 is not None:
            n_reach_ok += 1
    rep["per_lane"] = rows
    rep["summary"] = {
        "lanes": len(names),
        "lanes_with_registered_via_site_within_2_lattice_of_anchor": n_geo_ok,
        "lanes_that_can_reach_a_COMB_via_site_within_%d_lattice_steps_while_ALL_other_15_natural_corridors_are_claimed" % a.reach: n_reach_ok,
        "R526_access_band_limit_max_In5_descents": 10,
        "question_answered": ("在册模型内、'入口腿仅 In5' 这条编码**未放宽**的前提下：有 %d/16 根线能从自己的 A 锚走到 "
                              "COMB 区内的在册过孔站（其余 15 根自然走廊已按在册声明集占用）⇒ 与 R526 要求的"
                              "'≥6 根在带内下沉'相比，**在册口径下%s**" % (
                                  n_reach_ok, "够用" if n_reach_ok >= 6 else "**不够用**（事实读数，供监理裁第②项）")),
        "claim_class": "read-only measurement of the registered model · NOT a witness, NOT a certificate"}
    rep["decision"] = ("ACCESS-BAND VIA AVAILABILITY MEASURED (read-only, Solve() 0): geometric<=2 steps=%d/16 · "
                       "reachable in-band COMB via site under others' corridor claims=%d/16"
                       % (n_geo_ok, n_reach_ok))
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({"summary": rep["summary"], "decision": rep["decision"]}, ensure_ascii=False, indent=1))
    print("WROTE", a.out)


if __name__ == "__main__":
    main()
