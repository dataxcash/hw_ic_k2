#!/usr/bin/env python3
"""K2 · R525 (W-2) —— **必需置换 π 的反序图谱**（只读 · 零额度 · `Solve()` 0 次 · 不就绪任何求解）。

缘起：`HANDOFF-K2-525-WOVEN-PRIME-NEXT.md` §3 **(W-2)**：「把 R524 §C 的反序结构做成**可视化/可查**件
（哪 58 对、各自的轴向区间），供监理判『是否需要 L1』」。本件**只读取**在册实例（Gen2 逐层合法节点 /
A 锚点 / B 锚点）与在册四宽区 `ZONES`，把下列东西**机器算出来**并落盘为**可查件**：

  ① 必需置换 π = 「梳齿序（按 A-锚 x 排序）→ 焊盘序（按 B-锚 x 排序）」；
  ② π 的**逆序对数** / **LIS** / **LDS**（Dilworth：LDS = 覆盖 π 所需的最小**保序组**数）；
  ③ **最小保序组分解**（patience-sorting 贪心）⇒ 「若有 k 层，谁可同层」的可查分组；
  ④ **58 对反序**逐对明细：两线的 A/B 锚坐标、**轴向（x）共存窗**、窗内**覆盖到的在册宽区**
     （过孔对只能落在四宽区内 ⇒ 该窗是否**存在可打孔站**）；
  ⑤ 每根线的**最小必需 In4 行程**下界读数（由 ③ 的分组数推）。

**口径声明（第十三条）**：本件**只做结构读数**，**不构成**设计级证书，**不**声明"无解"。
所有派生量一律标 `named_structural_lead`（承 #K2-192 §三.3.a：解不出 = 通道级更弱不可行，不是证书）。
**不 import** 任何无 `__main__` 保护的在册件（只读其 JSON）。
"""
import argparse, importlib, json, math, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
F = importlib.import_module("K2_R523_LAYERHOP_PARITY_FORMC_v1")

MODEL = "/tmp/opencode/archer/model_l8.json"
ZONES = list(F.ZONES)                     # 在册四宽区（R513 层余量审计 boxes_mm）
ZONE_NAMES = ["COMB", "BELT", "WALL", "FIELD"]


def inv_pairs(seq):
    """all (x,y) with x<y and seq[x] > seq[y]  (seq = pad-rank in comb order)."""
    out = []
    for x in range(len(seq)):
        for y in range(x + 1, len(seq)):
            if seq[x] > seq[y]:
                out.append((x, y))
    return out


def lis_len(seq):
    import bisect
    tails = []
    for v in seq:
        k = bisect.bisect_left(tails, v)
        if k == len(tails):
            tails.append(v)
        else:
            tails[k] = v
    return len(tails)


def lds_len(seq):
    return lis_len([-v for v in seq])


def min_inc_cover(seq):
    """greedy (patience-sorting) cover of the permutation by increasing subsequences = groups.
    Returns list of groups (each = list of positions in comb order), groups sorted by first element."""
    # classic: for each value in increasing order of value, append to the group whose tail is the
    # largest tail < v  (equivalently: build chains in the poset).
    groups = []       # each: list of (pos, val); tail = last val
    for pos in range(len(seq)):
        v = seq[pos]
        best = None
        for gi, g in enumerate(groups):
            if g[-1][1] < v and (best is None or g[-1][1] > groups[best][-1][1]):
                best = gi
        if best is None:
            groups.append([(pos, v)])
        else:
            groups[best].append((pos, v))
    return groups


def point_in_zones(x, y):
    hit = []
    for k, (x0, y0, x1, y1) in enumerate(ZONES):
        if x0 - 1e-9 <= x <= x1 + 1e-9 and y0 - 1e-9 <= y <= y1 + 1e-9:
            hit.append(ZONE_NAMES[k])
    return hit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "K2_R525_INVERSION_ATLAS_v1.json"))
    ap.add_argument("--svg", default=os.path.join(HERE, "K2_R525_INVERSION_ATLAS_v1.svg"))
    a = ap.parse_args()
    t0 = time.time()
    rep = {"artifact": "k2_r525_inversion_atlas_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "HANDOFF-K2-525 sec.3 (W-2) · read-only, zero-quota prep",
           "boundaries": "Solve() 0 calls; no board/SPEC/generator/criteria writes; no .omo/supervision writes",
           "claim_class": "named_structural_lead (NOT a design-level certificate)",
           "zones_mm": {ZONE_NAMES[k]: list(z) for k, z in enumerate(ZONES)}}

    model = json.load(open(MODEL))
    g2 = F.Gen2(model, l1scope="full")
    names = list(g2.names)
    lanes = {}
    for nm in names:
        L = g2.build_lane(nm)
        if L is None:
            rep["decision"] = "FAIL-CLOSED: lane %s build failed" % nm
            json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
            print(rep["decision"]); return
        lanes[nm] = {"A": [float(v) for v in L["anc"][0]], "B": [float(v) for v in L["anc"][1]],
                     "grp": g2.grp[nm],
                     "own_nodes": {"In5": int(g2._nok[(nm, 0)].sum()), "In4": int(g2._nok[(nm, 1)].sum())},
                     "via_capable_nodes": int(len(g2.via_positions(nm)))}

    order = sorted(names, key=lambda nm: lanes[nm]["A"][0])                  # comb order (A.x)
    padr = {nm: r for r, nm in enumerate(sorted(names, key=lambda nm: lanes[nm]["B"][0]))}  # pad order (B.x)
    seq = [padr[nm] for nm in order]
    pairs = inv_pairs(seq)
    LIS, LDS = lis_len(seq), lds_len(seq)
    groups = min_inc_cover(seq)

    # ---- per-lane table (queryable) ----
    lane_tbl = {}
    for r, nm in enumerate(order):
        A, B = lanes[nm]["A"], lanes[nm]["B"]
        lane_tbl[nm] = {"comb_rank": r, "pad_rank": padr[nm], "group_id": None,
                        "A_anchor_mm": A, "B_anchor_mm": B, "group": lanes[nm]["grp"],
                        "A_in_zone": point_in_zones(A[0], A[1]), "B_in_zone": point_in_zones(B[0], B[1]),
                        "own_nodes": lanes[nm]["own_nodes"], "via_capable_nodes": lanes[nm]["via_capable_nodes"]}
    for gi, g in enumerate(groups):
        for pos, _v in g:
            lane_tbl[order[pos]]["group_id"] = gi
    rep["permutation"] = {
        "comb_order_by_Ax": order,
        "pad_order_by_Bx": sorted(names, key=lambda nm: lanes[nm]["B"][0]),
        "pi_pad_rank_in_comb_order": seq,
        "inversions": len(pairs),
        "LIS": LIS, "LDS": LDS,
        "min_order_preserving_groups": LDS,
        "registered_layers": 2,
        "registered_max_via_pairs_per_lane": F.MAX_VIA_PAIRS,
        "level_reading": ("LDS(pi)=%d > registered layers=2 => the permutation cannot be a union of 2 "
                          "order-preserving groups; however this bound applies ONLY to the 'each lane stays "
                          "on one layer' reading. A lane that makes an In4 excursion is absent from its In5 "
                          "order inside that axial interval, so SEQUENCED excursions can realise reversals that "
                          "a fixed 2-way layer split cannot (the naive 'L(pi) <= #layers' lemma is REFUTED, "
                          "see HANDOFF-K2-525 sec.1)." % LDS)}

    # ---- 58 inversion pairs, each with the axial co-presence window + wide-zone coverage ----
    detail = []
    for (x, y) in pairs:
        ni, nj = order[x], order[y]
        Ai, Bi = lanes[ni]["A"], lanes[ni]["B"]
        Aj, Bj = lanes[nj]["A"], lanes[nj]["B"]
        lo = max(min(Ai[0], Bi[0]), min(Aj[0], Bj[0]))     # both lanes can be present only in the x-overlap
        hi = min(max(Ai[0], Bi[0]), max(Aj[0], Bj[0]))
        zx = [ZONE_NAMES[k] for k, (x0, _y0, x1, _y1) in enumerate(ZONES) if min(hi, x1) - max(lo, x0) > 0]
        detail.append({"pair": [ni, nj], "comb_ranks": [x, y], "pad_ranks": [seq[x], seq[y]],
                       "groups": [lane_tbl[ni]["group_id"], lane_tbl[nj]["group_id"]],
                       "group_kind": (lane_tbl[ni]["group"] + "/" + lane_tbl[nj]["group"]),
                       "x_overlap_window_mm": [round(lo, 3), round(hi, 3)],
                       "zones_intersecting_window": zx,
                       "window_has_via_station": bool(zx),
                       "pad_x_mm": [round(Bi[0], 3), round(Bj[0], 3)]})
    nozone = [d for d in detail if not d["window_has_via_station"]]
    rep["inversion_detail"] = detail
    rep["inversion_summary"] = {
        "total": len(detail),
        "by_group_kind": {k: sum(1 for d in detail if d["group_kind"] == k)
                          for k in sorted({d["group_kind"] for d in detail})},
        "with_via_station_in_window": len(detail) - len(nozone),
        "without_via_station_in_window": len(nozone),
        "lead": ("每对反序 ⇒ 该对中至少一方的**同一轴向位置上**不得与另一方同层存活（编织条件）；"
                 "过孔对只能落在在册四宽区内 ⇒ 窗内无宽区的对**无法由窗内打孔解**"
                 "（named structural lead，非证书）")}

    # ---- minimal excursion lower bound (derivation, labelled) ----
    grp_pos = {}   # group index -> comb positions
    for gi, g in enumerate(groups):
        grp_pos[gi] = [p for p, _v in g]
    rep["min_inc_cover_groups"] = {
        "count": len(groups),
        "groups_by_lane": [[order[p] for p, _v in g] for g in groups],
        "reading": ("同一保序组内的线可**同时**停留在同一层（组内相对序不变）；不同组之间必须靠**层或时刻**分离 ⇒ "
                    "若某站只有 2 层可用，则至多 2 组可在该站同时活跃 ⇒ 其余组必须在该站**换走**："
                    "受 = 每根线 ≤%d 对孔（= ≤1 段 In4 行程）约束。" % F.MAX_VIA_PAIRS)}
    per_lane_need = {}
    for nm in names:
        gi = lane_tbl[nm]["group_id"]
        others = [lane_tbl[o]["group_id"] for o in names if o != nm]
        per_lane_need[nm] = {"group_id": gi, "peers_in_same_group": sum(1 for o in others if o == gi),
                             "distinct_other_groups": len(set(others) - {gi})}
    rep["per_lane_excursion_pressure"] = per_lane_need
    rep["lane_table"] = lane_tbl

    # ---- SVG: two-axis chord diagram (comb order -> pad order), group-coloured ----
    COLS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
    W, H, TOP, BOT = 900, 560, 40, 520
    step = (BOT - TOP) / (len(names) - 1)
    ax, bx = 170, 730
    L = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (W, H, W, H),
         '<rect width="%d" height="%d" fill="white"/>' % (W, H),
         '<text x="16" y="22" font-family="monospace" font-size="13">K2 R525 inversion atlas · pi: comb order (A.x) -&gt; pad order (B.x) · '
         '16 lanes · %d inversions · LIS=%d LDS=%d (colour = min order-preserving group)</text>' % (len(pairs), LIS, LDS)]
    for r, nm in enumerate(order):
        y = TOP + r * step
        L.append('<text x="%d" y="%.1f" font-family="monospace" font-size="10" text-anchor="end">%d %s</text>'
                 % (ax - 8, y + 3, r, nm))
        L.append('<circle cx="%d" cy="%.1f" r="3.5" fill="%s"/>' % (ax, y, COLS[lane_tbl[nm]["group_id"] % len(COLS)]))
    for r, nm in enumerate(sorted(names, key=lambda n_: lanes[n_]["B"][0])):
        y = TOP + r * step
        L.append('<text x="%d" y="%.1f" font-family="monospace" font-size="10">%d %s</text>'
                 % (bx + 8, y + 3, r, nm))
        L.append('<circle cx="%d" cy="%.1f" r="3.5" fill="%s"/>' % (bx, y, COLS[lane_tbl[nm]["group_id"] % len(COLS)]))
    for r, nm in enumerate(order):
        y0 = TOP + r * step
        y1 = TOP + lane_tbl[nm]["pad_rank"] * step
        L.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1.1" opacity="0.75"/>'
                 % (ax, y0, bx, y1, COLS[lane_tbl[nm]["group_id"] % len(COLS)]))
    L.append('</svg>')
    open(a.svg, "w").write("\n".join(L))

    rep["artifacts"] = {"json": os.path.basename(a.out), "svg": os.path.basename(a.svg)}
    rep["decision"] = ("ATLAS DONE (read-only, Solve() 0): pi inversions=%d, LDS=%d (>2), min order-preserving "
                       "groups=%d; pairs with no wide-zone in their x-overlap window=%d"
                       % (len(pairs), LDS, len(groups), len(nozone)))
    rep["solve_calls"] = 0
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({"inversions": len(pairs), "LIS": LIS, "LDS": LDS,
                      "min_groups": len(groups), "no_zone_pairs": len(nozone),
                      "by_group_kind": rep["inversion_summary"]["by_group_kind"],
                      "decision": rep["decision"]}, ensure_ascii=False, indent=1))
    print("WROTE", a.out, a.svg)


if __name__ == "__main__":
    main()
