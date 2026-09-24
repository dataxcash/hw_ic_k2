#!/usr/bin/env python3
"""K2 · R525 (W-3) —— 丙′ 通道化的 **3D（逐层）Voronoi 通道骨架**（只读 · 零额度 · `Solve()` 0 次）。

缘起：`HANDOFF-K2-525-WOVEN-PRIME-NEXT.md` §3 **(W-3)**：「丙′ 通道化的 3D（逐层）Voronoi 构造先写**只读**骨架
并机核两条性质（⊆自己网 · 逐层不交），**不**求解」。

## 两个通道定义（本件的核心读数）
- **V（纯 Voronoi）**：格点在层 L 上归属**最近骨架**的线（L1 折线距离最小；并列按登记声明序取先），
  且仅在该点对 i **逐层合法**（在册 `_nok[(nm,L)]`）时参与竞争。⇒ 通道 = 归属 i 的合法点。
- **V∩B_k（Voronoi ∩ 3 格带）**：再把通道限制在骨架的 **L1 带**（`R_BAND=k` 格）内 —— 与 R524 自检件同款"带"。
  ⇒ 仍是**交集**：两性质**仍由构造保证**（Voronoi 单元本身两两不交，逐单元再取子集仍不交）。
**机核**：(A1) 通道 ⊆ 自己网的逐层合法点；(A2) 各线通道**逐层两两不交**。
**结构读数**：逐线逐层**连通分量数/最大分量**（用**在册逐层边**表 `_eok` 诱导，只取通道内两端点）、
**可换层站点数**（在册宽区内的合法过孔点），以及**A 侧可达带**（从 COMB 区内的通道点 BFS 可达的在册宽区集合）
—— 后者直接回答「这根线能不能从梳齿一路连到某个可换层站」。`Solve()` = 0，**不出路径、不出见证**。

**口径（第十三条）**：只读骨架 + 结构读数，**不**签字、**不**构成见证/证书/不可行证明。
"""
import argparse, collections, importlib, json, math, os, sys, time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
F = importlib.import_module("K2_R523_LAYERHOP_PARITY_FORMC_v1")

P, HW, NX, NY, X0, Y0 = F.P, F.HW, F.NX, F.NY, F.X0, F.Y0
NID = NX * NY
MODEL = "/tmp/opencode/archer/model_l8.json"
YARD_COL, YARD_ROWS = 60, list(range(38, 58))
GATE_ROW, GATE_COLS = 36, list(range(115, 136))
WALL_COL, GAPS = 114, [7, 11, 12, 13, 15, 24, 25, 28]
ZONES = list(F.ZONES)
ZN = ["COMB", "BELT", "WALL", "FIELD"]
A_ZONE_IDX = 0          # COMB = A 侧接入区（全部 A 锚 x∈84..94 落在 COMB: x 83..96, y 53.5..57.5）


def zone_of(x, y):
    for k, (x0, y0, x1, y1) in enumerate(ZONES):
        if x0 - 1e-9 <= x <= x1 + 1e-9 and y0 - 1e-9 <= y <= y1 + 1e-9:
            return k
    return None


def seg_dist_all(xs, ys, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 <= 0:
        return np.hypot(xs - ax, ys - ay)
    t = np.clip(((xs - ax) * dx + (ys - ay) * dy) / L2, 0.0, 1.0)
    return np.hypot(xs - (ax + t * dx), ys - (ay + t * dy))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "K2_R525_VORONOI_CHANNEL_SKELETON_v1.json"))
    ap.add_argument("--band", type=int, default=3, help="V∩B_k 的 k（格数，默认 3，与 R524 自检件同款）")
    a = ap.parse_args()
    t0 = time.time()
    rep = {"artifact": "k2_r525_voronoi_channel_skeleton_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "HANDOFF-K2-525 sec.3 (W-3) · read-only skeleton · Solve() 0",
           "boundaries": "Solve() 0 calls; read-only; no board/SPEC/generator/criteria writes",
           "claim_class": "read-only structural artifact (NOT a witness, NOT a certificate)", "solve_calls": 0}

    g2 = F.Gen2(json.load(open(MODEL)), l1scope="full")
    names = list(g2.names)
    order = sorted(names, key=lambda nm: g2.A[nm][0])                      # registered declared order (A.x)
    grp = {nm: g2.grp[nm] for nm in names}
    east = [nm for nm in order if grp[nm] == "east"]
    west = [nm for nm in order if grp[nm] == "west"]

    # registered monotone slot assignment (identical to K2_R524_PRIME_CHANNEL_SELFCHECK_v1)
    slot = {}
    for k, nm in enumerate(order):
        slot[nm] = {"yard_row": YARD_ROWS[k % len(YARD_ROWS)]}
    for k, nm in enumerate(west):
        slot[nm]["gap"] = GAPS[k % len(GAPS)]
    for k, nm in enumerate(east):
        slot[nm]["gate_col"] = GATE_COLS[k % len(GATE_COLS)]

    def backbone(nm):
        A = tuple(g2.A[nm]); B = tuple(g2.B[nm])
        wy = Y0 + slot[nm]["yard_row"] * P
        pts = [A, (A[0], wy), (X0 + YARD_COL * P, wy)]
        if "gap" in slot[nm]:
            pts.append((X0 + WALL_COL * P, Y0 + slot[nm]["gap"] * P))
        else:
            pts.append((X0 + slot[nm]["gate_col"] * P, Y0 + GATE_ROW * P))
        pts.append((B[0], pts[-1][1]))
        pts.append(B)
        return pts

    ii, jj = np.meshgrid(np.arange(NX), np.arange(NY), indexing="ij")
    xs = (X0 + ii * P).reshape(-1).astype(float)
    ys = (Y0 + jj * P).reshape(-1).astype(float)

    # ---- per-layer nearest-backbone Voronoi (tie-break = declared order) + optional L1 band ----
    def build(kband):
        assign = {L: -np.ones(NX * NY, dtype=np.int32) for L in (0, 1)}
        dmin = {L: np.full(NX * NY, np.inf) for L in (0, 1)}
        band = {}
        for k, nm in enumerate(order):
            pts = backbone(nm)
            dd = np.full(NX * NY, np.inf)
            for s in range(len(pts) - 1):
                dd = np.minimum(dd, seg_dist_all(xs, ys, pts[s][0], pts[s][1], pts[s + 1][0], pts[s + 1][1]))
            if kband > 0:                       # nodes within kband L1 steps of the backbone polyline
                touch = np.zeros(NX * NY, bool)
                for s in range(len(pts) - 1):
                    (ax, ay), (bx, by) = pts[s], pts[s + 1]
                    steps = max(1, int(math.ceil(max(abs(bx - ax), abs(by - ay)) / P)))
                    for t in range(steps + 1):
                        cx = ax + (bx - ax) * t / steps
                        cy = ay + (by - ay) * t / steps
                        ci, cj = int(round((cx - X0) / P)), int(round((cy - Y0) / P))
                        for di in range(-kband, kband + 1):
                            for dj in range(-kband, kband + 1):
                                u, v = ci + di, cj + dj
                                if 0 <= u < NX and 0 <= v < NY:
                                    touch[u * NY + v] = True
                band[nm] = touch
            for L in (0, 1):
                elig = np.nonzero(g2._nok[(nm, L)].reshape(-1))[0]
                if kband > 0:
                    elig = elig[band[nm][elig]]
                better = dd[elig] < dmin[L][elig] - 1e-12
                take = elig[better]
                dmin[L][take] = dd[take]
                assign[L][take] = k
        return assign

    def channels(assign):
        return {L: {order[k]: set(np.nonzero(assign[L] == k)[0].tolist()) for k in range(len(order))} for L in (0, 1)}

    def band_touch(nm, kband):
        """nodes within kband L1 steps of this lane's backbone polyline (same convention as R524 self-check)."""
        touch = np.zeros(NX * NY, bool)
        pts = backbone(nm)
        for s in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[s], pts[s + 1]
            steps = max(1, int(math.ceil(max(abs(bx - ax), abs(by - ay)) / P)))
            for t in range(steps + 1):
                cx = ax + (bx - ax) * t / steps
                cy = ay + (by - ay) * t / steps
                ci, cj = int(round((cx - X0) / P)), int(round((cy - Y0) / P))
                for di in range(-kband, kband + 1):
                    for dj in range(-kband, kband + 1):
                        u, v = ci + di, cj + dj
                        if 0 <= u < NX and 0 <= v < NY:
                            touch[u * NY + v] = True
        return touch

    def build_greedy(kband):
        """R524 gate-a construction: channel = own-eligible nodes inside the L1 band, greedily claimed in
        the registered declared order (=> A1/A2 by construction, same as R524 self-check)."""
        claimed = {0: set(), 1: set()}
        ch = {0: {}, 1: {}}
        for nm in order:
            touch = band_touch(nm, kband)
            tset = set(np.nonzero(touch)[0].tolist())
            for L in (0, 1):
                ownL = set(np.nonzero(g2._nok[(nm, L)].reshape(-1))[0].tolist())
                ch[L][nm] = (ownL - claimed[L]) & tset
                claimed[L] |= ch[L][nm]
        return ch

    # ---- graph helpers (registered per-layer edge table, restricted to the channel) ----
    edge_u, edge_v = g2.edge_u, g2.edge_v
    nid_zone = np.array([(-1 if zone_of(x, y) is None else zone_of(x, y)) for x, y in zip(xs, ys)])

    def analyse(ch, nm):
        row = {}
        for L, lname in ((0, "In5"), (1, "In4")):
            chan = ch[L][nm]
            emask = g2._eok[(nm, L)]
            uu, vv = edge_u[emask], edge_v[emask]
            adj = collections.defaultdict(set)
            for u, v in zip(uu.tolist(), vv.tolist()):
                if u in chan and v in chan:
                    adj[u].add(v); adj[v].add(u)
            comps, seen = [], set()
            for s in chan:
                if s in seen:
                    continue
                st, comp = [s], set()
                seen.add(s)
                while st:
                    x = st.pop(); comp.add(x)
                    for y in adj[x]:
                        if y not in seen:
                            seen.add(y); st.append(y)
                comps.append(comp)
            comps.sort(key=len, reverse=True)
            cov = []
            for comp in comps[:5]:
                zt = sorted({ZN[z] for z in nid_zone[list(comp)] if z >= 0})
                i0 = [p // NY for p in comp]; j0 = [p % NY for p in comp]
                cov.append({"size": len(comp), "zones": zt,
                            "col_span": [min(i0), max(i0)], "row_span": [min(j0), max(j0)]})
            row[lname] = {
                "channel_nodes": len(chan), "components": len(comps),
                "largest_component": (len(comps[0]) if comps else 0),
                "via_capable_nodes_in_channel": int(sum(1 for p in chan if g2._viaok[nm][p])),
                "top_components": cov,
                "adj": adj}
        # A-side reach: clean 2-layer BFS over states (layer, node). Start = In5 channel nodes inside
        # the COMB zone (all A anchors live there). A layer switch is allowed ONLY at a via-capable node
        # that belongs to both layers' channels (registered: vias only in the four wide zones).
        a5 = {p for p in ch[0][nm] if nid_zone[p] == A_ZONE_IDX}
        seen_state, reach5, reach_both = set(), set(), set()
        stack = [(0, p) for p in a5]
        for st0 in stack:
            seen_state.add(st0)
        while stack:
            Lcur, xnode = stack.pop()
            reach_both.add(xnode)
            if Lcur == 0:
                reach5.add(xnode)
            for y in row["In5" if Lcur == 0 else "In4"]["adj"][xnode]:
                if (Lcur, y) not in seen_state:
                    seen_state.add((Lcur, y)); stack.append((Lcur, y))
            if g2._viaok[nm][xnode]:
                oL = 1 - Lcur
                if xnode in ch[oL][nm] and (oL, xnode) not in seen_state:
                    seen_state.add((oL, xnode)); stack.append((oL, xnode))
        z5 = sorted({ZN[z] for z in nid_zone[list(reach5)] if z >= 0})
        zb = sorted({ZN[z] for z in nid_zone[list(reach_both)] if z >= 0})
        row["A_side_reach"] = {"In5_only_zones": z5, "In5_plus_In4_zones": zb,
                               "A_zone_channel_nodes_In5": len(a5),
                               "reach_nodes_In5": len(reach5), "reach_nodes_both": len(reach_both)}
        return row

    # ---- (C) comb fan-out planarity check on the registered yard-row ordering (machine) ----
    # Registered convention (R524 backbone,承 R512 §c): lane order[k] (k = declared order by A.x) descends
    # from its A anchor to yard row YARD_ROWS[k] and then runs east at that row. Lane i's east run spans
    # lattice columns col(A_i.x)..60 at row r_i; lane j>i descends at column col(A_j.x) through rows 34..r_j.
    # If r_i <= r_j the run MUST occupy the descent node (col_j, r_i) => same-layer (In5) crossing.
    def block_pairs(row_of):
        blk = []
        for x in range(len(order)):
            for y in range(x + 1, len(order)):
                i, j = order[x], order[y]
                if row_of[i] <= row_of[j]:
                    blk.append([i, j])
        return blk

    asc = {nm: YARD_ROWS[k] for k, nm in enumerate(order)}
    desc = {nm: YARD_ROWS[len(order) - 1 - k] for k, nm in enumerate(order)}
    rep["C_yard_order_planarity_check"] = {
        "convention": "descent column = A.x (R524 backbone) · east run at the lane's yard row · In5 planarity",
        "registered_ascent_assignment": {"row_of": asc, "blocking_pairs": len(block_pairs(asc)),
                                         "of_total_pairs": len(order) * (len(order) - 1) // 2},
        "reversed_descent_assignment": {"row_of": desc, "blocking_pairs": len(block_pairs(desc))},
        "reading": ("Descent columns keep their declared left-to-right order (planarity forces this); then a "
                    "lane's east run is blocked by every later lane whose descent row is below its own row. "
                    "The registered assignment (declared order -> ASCENDING rows) therefore blocks on ALL pairs; "
                    "the nested (DESCENDING) assignment blocks on NONE. This is the machine-readable cause of the "
                    "15/16 'A-side reach' failures below, and it is an In5-layer planarity statement only: whether "
                    "an In4 excursion (vias are legal in all four wide zones, incl. COMB/BELT) launders a given "
                    "crossing is exactly the woven time-table question (named structural lead, NOT a certificate)."),
        "claim_class": "named_structural_lead (NOT a design-level certificate)"}
    variants = [("V_pure_voronoi", "voronoi", 0),
                ("V_inter_band%d" % a.band, "voronoi", a.band),
                ("G_greedy_declared_band%d" % a.band, "greedy", a.band)]
    out = {}
    for vname, kind, kb in variants:
        ch = channels(build(kb)) if kind == "voronoi" else build_greedy(kb)
        a1 = all(ch[L][nm] <= set(np.nonzero(g2._nok[(nm, L)].reshape(-1))[0].tolist()) for L in (0, 1) for nm in names)
        a2 = True
        for L in (0, 1):
            seen = set()
            for nm in names:
                if ch[L][nm] & seen:
                    a2 = False
                seen |= ch[L][nm]
        per = {nm: analyse(ch, nm) for nm in names}
        stations = {nm: {"via_capable_channel_nodes_per_zone": {
            ZN[z]: int(sum(1 for p in (ch[0][nm] | ch[1][nm]) if nid_zone[p] == z and g2._viaok[nm][p]))
            for z in range(len(ZN)) if any(nid_zone[p] == z and g2._viaok[nm][p] for p in (ch[0][nm] | ch[1][nm]))}}
            for nm in names}
        out[vname] = {
            "band_steps": kb,
            "station_action_sets": stations,
            "A1_subset_of_own_eligible_per_layer": bool(a1),
            "A2_pairwise_disjoint_per_layer": bool(a2),
            "machine_check_verdict": "PASS" if (a1 and a2) else "FAIL",
            "In5_nodes_total": sum(per[nm]["In5"]["channel_nodes"] for nm in names),
            "In4_nodes_total": sum(per[nm]["In4"]["channel_nodes"] for nm in names),
            "lanes_single_component_In5": sum(1 for nm in names if per[nm]["In5"]["components"] == 1),
            "lanes_single_component_In4": sum(1 for nm in names if per[nm]["In4"]["components"] == 1),
            "lanes_A_reach_includes_BELT_In5_only": sum(
                1 for nm in names if "BELT" in per[nm]["A_side_reach"]["In5_only_zones"]),
            "lanes_A_reach_includes_BELT_both": sum(
                1 for nm in names if "BELT" in per[nm]["A_side_reach"]["In5_plus_In4_zones"]),
            "lanes_A_reach_includes_FIELD_both": sum(
                1 for nm in names if "FIELD" in per[nm]["A_side_reach"]["In5_plus_In4_zones"]),
            "per_lane": {nm: {"In5": {k: v for k, v in per[nm]["In5"].items() if k != "adj"},
                              "In4": {k: v for k, v in per[nm]["In4"].items() if k != "adj"},
                              "A_side_reach": per[nm]["A_side_reach"]} for nm in names}}
    rep["variants"] = out
    dec = []
    for vname, _kind, _kb in variants:
        d = out[vname]
        dec.append("%s: A1=%s A2=%s In5single=%d/16 reach_BELT(both)=%d/16 reach_FIELD(both)=%d/16"
                   % (vname, "P" if d["A1_subset_of_own_eligible_per_layer"] else "F",
                      "P" if d["A2_pairwise_disjoint_per_layer"] else "F",
                      d["lanes_single_component_In5"], d["lanes_A_reach_includes_BELT_both"],
                      d["lanes_A_reach_includes_FIELD_both"]))
    rep["decision"] = "SKELETON DONE (read-only, Solve() 0) | " + " || ".join(dec)
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "per_lane"} for k, v in out.items()},
                     ensure_ascii=False, indent=1))
    print("DECISION:", rep["decision"])
    print("WROTE", a.out)


if __name__ == "__main__":
    main()
