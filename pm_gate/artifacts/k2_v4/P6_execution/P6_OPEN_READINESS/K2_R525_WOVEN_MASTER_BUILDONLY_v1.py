#!/usr/bin/env python3
"""K2 · R525 (W-1) —— **编织式丙′ 主问题**：规格细化 + 机器规模估算（**build-only** · `Solve()` **硬拒**）。

缘起：`HANDOFF-K2-525-WOVEN-PRIME-NEXT.md` §3 **(W-1)**：「编织式主问题的**规格细化与规模估算**（只读：由
π / 58 反序 / 6 条保序组推导变量数与时刻表编码）」。

## 为什么必须是"编织式"（在册事实，不再重走）
R524 机核：均匀行程族（全体"梳齿→带 = In5、带→场 = In4、场→焊盘 = In5"）**不可行** ⇒ 主问题除槽位外
**还必须选每根线的行程时刻表**（谁在哪个轴向站上二层）。本件把该时刻表**编码写死**并**只建模型不求解**。

## 编码（本件即规格）
- **站序（stations）**：把每根线沿"轴向行军"方向的**在册宽区**离散成有序站点。两种粒度：
  · **粗**（zone 级）：`COMB(0) < BELT(1) < WALL(2) < FIELD(3)`（在册 `ZONES` 四区）；
  · **细**（格点级）：每站 = 该线在某宽区内**过孔可用格点**的 (zone, 轴向格坐标) 去重后按轴向排序。
- **时刻表变量**：每根线选 `dn_i`（下孔站）与 `up_i`（上孔站）：one-hot over stations；`dn` 站序 ≤ `up` 站序
  ⇒ **至多一段 In4 行程**（在册 `MAX_VIA_PAIRS=2`）。`on4_i[s]` = 「i 在站 s 处于 In4」由 dn/up 线性推出。
- **槽位变量**（在册，同 R524）：`zy_i`（院行 38..57 @col60）· `zc_i`（门列 115..135 @row36 · 仅东 8）·
  `zg_i`（墙缝 @col114 · 仅西 8）：all-different ＋ **登记声明序非交叉**。
- **编织约束（本件新产 · 必要条件的松弛编码）**：对**每一对反序对** (i,j)（58 对，取自 R525 反序图谱）：
  `OR_{s ∈ 窗(i,j)} [ on4_i[s] ≠ on4_j[s] ]` —— 即**该对必须在窗内某一站被层分离**。
  （必要：同一轴向位置上同层的两线不得交叉 ⇒ 相对序必须一致；若在册序与该对要求相反，则该对至少一方须离开本层。
   本编码是**必要条件**，写死为**松弛**：SAT 仍须子问题+在册闸复核；UNSAT 的**设计级**含义**须先过**
   §三.3.a 保真自检方可主张 —— 本件**不主张**任何结论。）
- **目标**：`min Σ_i (up_i 站序 − dn_i 站序)`（行程越短越好 ⇒ 少挤占用带）。

## 边界（fail-closed）
`Solve()` **硬拒**：本文件**只**建模型 + `Validate()`；即便显式 `--solve` 也**拒绝**（编织式变体**尚未获监理一字裁**，
见 #K2-192 §三.4「停手报监理、由监理再裁」）。**不** import 任何无 `__main__` 保护的在册件（只读 JSON）。
"""
import argparse, importlib, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
F = importlib.import_module("K2_R523_LAYERHOP_PARITY_FORMC_v1")

MODEL = "/tmp/opencode/archer/model_l8.json"
P, X0, Y0, NX, NY = F.P, F.X0, F.Y0, F.NX, F.NY
YARD_COL, YARD_ROWS = 60, list(range(38, 58))
GATE_ROW, GATE_COLS = 36, list(range(115, 136))
WALL_COL, GAPS = 114, [7, 11, 12, 13, 15, 24, 25, 28]
ZONES = list(F.ZONES)
ZN = ["COMB", "BELT", "WALL", "FIELD"]
SCALE_GATE = 1_200_000
MAX_VIA_PAIRS = F.MAX_VIA_PAIRS


def zone_of(x, y):
    for k, (x0, y0, x1, y1) in enumerate(ZONES):
        if x0 - 1e-9 <= x <= x1 + 1e-9 and y0 - 1e-9 <= y <= y1 + 1e-9:
            return k
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "K2_R525_WOVEN_MASTER_BUILDONLY_v1.json"))
    ap.add_argument("--solve", action="store_true",
                    help="**拒绝**：编织式变体尚未获监理一字裁（#K2-192 §三.4）")
    a = ap.parse_args()
    if a.solve:
        print("REFUSED: woven master is NOT authorized to solve (awaiting supervisor one-word ruling, "
              "#K2-192 sec.3.4). Build-only artifact.")
        sys.exit(2)
    t0 = time.time()
    atlas_path = os.path.join(HERE, "K2_R525_INVERSION_ATLAS_v1.json")
    rep = {"artifact": "k2_r525_woven_master_buildonly_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "HANDOFF-K2-525 sec.3 (W-1) · build-only · Solve() hard-refused",
           "authorization_status": "woven variant AWAITING supervisor one-word ruling (#K2-192 sec.3.4)",
           "boundaries": "Solve() 0 calls (and refused by design); no board/SPEC/generator/criteria writes",
           "solve_calls": 0}

    from ortools.sat.python import cp_model
    model_json = json.load(open(MODEL))
    g2 = F.Gen2(model_json, l1scope="full")
    names = list(g2.names)
    n = len(names)
    order = sorted(names, key=lambda nm: g2.A[nm][0])            # comb order (A.x)
    padr = {nm: r for r, nm in enumerate(sorted(names, key=lambda nm: g2.B[nm][0]))}
    grp = {nm: g2.grp[nm] for nm in names}
    east = [nm for nm in order if grp[nm] == "east"]
    west = [nm for nm in order if grp[nm] == "west"]

    # ---- stations (machine-derived from registered wide zones + per-lane via-capable nodes) ----
    fine, coarse_ok = {}, {}
    for nm in names:
        vp = g2.via_positions(nm)
        zmap = {}
        for p in vp.tolist():
            i, j = int(p) // NY, int(p) % NY
            z = zone_of(X0 + i * P, Y0 + j * P)
            if z is None:
                continue
            zmap.setdefault(z, set()).add((i, j))
        # fine stations: (zone, axial lattice coordinate) — axial = x for COMB/BELT/WALL, y for FIELD
        st = set()
        for z, cells in sorted(zmap.items()):
            for (i, j) in cells:
                st.add((z, i if ZN[z] != "FIELD" else j))
        fine[nm] = len(st)
        coarse_ok[nm] = sorted(zmap.keys())
    rep["station_grid"] = {
        "definition": "station = (wide-zone, axial lattice coordinate) of a lane's via-capable node",
        "zones_mm": {ZN[k]: list(z) for k, z in enumerate(ZONES)},
        "fine_stations_per_lane": fine, "fine_stations_total": sum(fine.values()),
        "fine_shared_stations": None, "coarse_stations_per_lane": {nm: [ZN[z] for z in coarse_ok[nm]] for nm in names},
        "coarse_station_count": 4}

    # fine shared stations (needed for the pair-wise weave constraints) + pair windows
    fine_sets = {}
    for nm in names:
        vp = g2.via_positions(nm)
        st = set()
        for p in vp.tolist():
            i, j = int(p) // NY, int(p) % NY
            z = zone_of(X0 + i * P, Y0 + j * P)
            if z is None:
                continue
            st.add((z, i if ZN[z] != "FIELD" else j))
        fine_sets[nm] = st
    shared_fine = set()
    from collections import Counter
    cc = Counter()
    for nm in names:
        for s in fine_sets[nm]:
            cc[s] += 1
    shared_fine = {s for s, v in cc.items() if v >= 2}
    rep["station_grid"]["fine_shared_stations"] = len(shared_fine)
    rep["station_grid"]["fine_max_lanes_per_station"] = max(cc.values()) if cc else 0

    atlas = json.load(open(atlas_path))
    inv = atlas["inversion_detail"]
    for d in inv:
        ni, nj = d["pair"]
        lo, hi = d["x_overlap_window_mm"]
        fs = set()
        for nm in (ni, nj):
            for (z, t) in fine_sets[nm]:
                # station lattice x (COMB/BELT/WALL: x; FIELD: x too) for the x-window test
                x = X0 + t * P if ZN[z] in ("COMB", "BELT", "WALL") else None
                if x is None:
                    # FIELD: station axial coordinate is y; use the zone's x-range midpoint for the window test
                    x = (ZONES[z][0] + ZONES[z][2]) / 2.0
                if lo - 1e-9 <= x <= hi + 1e-9:
                    fs.add((z, t))
        d["fine_shared_stations_in_window"] = len(fs & shared_fine)
        d["coarse_stations_in_window"] = len(d["zones_intersecting_window"])

    # ================= coarse woven master (fully instantiated, build-only) =================
    mo = cp_model.CpModel()
    # (1) registered slot variables
    zy = {i: {r: mo.NewBoolVar("zy_%d_%d" % (i, r)) for r in YARD_ROWS} for i in range(n)}
    for i in range(n):
        mo.AddExactlyOne(zy[i].values())
    for r in YARD_ROWS:
        mo.Add(sum(zy[i][r] for i in range(n)) <= 1)
    pos_y = {i: sum(k * zy[i][r] for k, r in enumerate(YARD_ROWS)) for i in range(n)}
    oi = {nm: i for i, nm in enumerate(names)}
    for oa, ob in zip(order, order[1:]):
        mo.Add(pos_y[oi[oa]] <= pos_y[oi[ob]] - 1)
    zc = {nm: {c: mo.NewBoolVar("zc_%d_%d" % (oi[nm], c)) for c in GATE_COLS} for nm in east}
    for nm in east:
        mo.AddExactlyOne(zc[nm].values())
    for c in GATE_COLS:
        mo.Add(sum(zc[nm][c] for nm in east) <= 1)
    zg = {nm: {g: mo.NewBoolVar("zg_%d_%d" % (oi[nm], g)) for g in GAPS} for nm in west}
    for nm in west:
        mo.AddExactlyOne(zg[nm].values())
    for g in GAPS:
        mo.Add(sum(zg[nm][g] for nm in west) <= 1)
    n_slot = sum(len(zy[i]) for i in range(n)) + sum(len(zc[nm]) for nm in east) + sum(len(zg[nm]) for nm in west)

    # (2) time-table variables: dn/up one-hot over the lane's coarse zone stations (station index = zone id)
    dn, up, on4 = {}, {}, {}
    for nm in names:
        zs = sorted(coarse_ok[nm])
        dn[nm] = {z: mo.NewBoolVar("dn_%s_%d" % (nm, z)) for z in zs}
        up[nm] = {z: mo.NewBoolVar("up_%s_%d" % (nm, z)) for z in zs}
        on4[nm] = {}
        mo.AddExactlyOne(dn[nm].values()); mo.AddExactlyOne(up[nm].values())
        mo.Add(sum(z * dn[nm][z] for z in zs) <= sum(z * up[nm][z] for z in zs))     # <=1 excursion
        for z in zs:                                                                # on4 = (dn<=z) AND (up>=z)
            on4[nm][z] = mo.NewBoolVar("on4_%s_%d" % (nm, z))
            a_dn = sum(dn[nm][z2] for z2 in zs if z2 <= z)          # 1 iff down-station <= z
            a_up = sum(up[nm][z2] for z2 in zs if z2 >= z)          # 1 iff up-station   >= z
            mo.Add(on4[nm][z] <= a_dn)
            mo.Add(on4[nm][z] <= a_up)
            mo.Add(on4[nm][z] >= a_dn + a_up - 1)

    # (3) weave constraints: each inverted pair must be layer-separated at some station in its window
    n_weave = 0
    for d in inv:
        ni, nj = d["pair"]
        zs = [ZN.index(z) for z in d["zones_intersecting_window"]]
        zs = [z for z in zs if z in on4[ni] and z in on4[nj]]
        seps = []
        for z in zs:
            b = mo.NewBoolVar("sep_%d_%d_%d" % (oi[ni], oi[nj], z))   # 1 iff exactly one of the pair is on In4
            mo.Add(b >= on4[ni][z] - on4[nj][z])
            mo.Add(b >= on4[nj][z] - on4[ni][z])
            mo.Add(b <= on4[ni][z] + on4[nj][z])
            mo.Add(b <= 2 - on4[ni][z] - on4[nj][z])
            seps.append(b)
            n_weave += 1
        if seps:
            mo.Add(sum(seps) >= 1)

    # objective: minimise total excursion width (in station counts)
    mo.Minimize(sum(sum(z * up[nm][z] for z in coarse_ok[nm]) - sum(z * dn[nm][z] for z in coarse_ok[nm])
                    for nm in names))

    proto = mo.Proto()
    n_bool = len(proto.variables)
    n_cons = len(proto.constraints)
    v = mo.Validate()
    rep["coarse_master"] = {
        "station_granularity": "zone-level (4 stations: COMB<BELT<WALL<FIELD)",
        "slot_bool_vars": n_slot, "timetable_bool_vars": n_bool - n_slot - n_weave,
        "weave_separation_bool_vars": n_weave,
        "bool_vars_total": n_bool, "constraints_total": n_cons,
        "scale_gate": SCALE_GATE, "under_gate": n_bool <= SCALE_GATE,
        "validate": (v if v else "OK"),
        "objective": "min sum_i (up_station - down_station)",
        "decision": "BUILD-ONLY GREEN (规模闸 + Validate 过 · Solve() 0)" if (n_bool <= SCALE_GATE and not v) else "FAIL-CLOSED"}

    # ---- fine-granularity scale estimate (analytic, machine-derived counts) ----
    fs_shared = len(shared_fine)
    est_dnup = 2 * sum(fine[nm] for nm in names)
    est_on4 = sum(fine[nm] for nm in names)
    est_weave = sum(d["fine_shared_stations_in_window"] for d in inv)
    est_cons = est_on4 * 4 + est_weave + 3 * n + (len(YARD_ROWS) + len(GATE_COLS) + len(GAPS)) + 2 * (n - 2) \
        + 2 * (len(east) - 1) + 2 * (len(west) - 1)
    rep["fine_master_estimate"] = {
        "station_granularity": "lattice-level (per-lane via-capable stations, deduped by axial coordinate)",
        "stations_per_lane_total": sum(fine.values()), "shared_stations": fs_shared,
        "dn_up_bool_vars": est_dnup, "on4_bool_vars": est_on4, "weave_bool_vars": est_weave,
        "bool_vars_estimate": n_slot + est_dnup + est_on4 + est_weave,
        "constraints_estimate": est_cons,
        "note": "analytic estimate (not instantiated in this window); fine grid is ~%dx the coarse station count"
                % (max(1, round(sum(fine.values()) / (2 * 4 * n))))}
    rep["readings"] = {
        "inversions": len(inv),
        "inv_pairs_with_fine_shared_station_in_window": sum(1 for d in inv if d["fine_shared_stations_in_window"] > 0),
        "inv_pairs_with_coarse_station_in_window": sum(1 for d in inv if d["coarse_stations_in_window"] > 0),
        "station_counts_in_window_fine_min_avg_max": (
            min(d["fine_shared_stations_in_window"] for d in inv),
            round(sum(d["fine_shared_stations_in_window"] for d in inv) / len(inv), 1),
            max(d["fine_shared_stations_in_window"] for d in inv)),
        "encode_class": "necessary-condition relaxation (SAT still needs subproblems + registered gates; "
                        "UNSAT's design-level meaning requires the fidelity self-check first)",
        "claim_class": "spec + scale estimate only · NO conclusion, NO certificate, NO witness"}
    rep["inversion_with_windows"] = [{"pair": d["pair"], "window_mm": d["x_overlap_window_mm"],
                                      "zones": d["zones_intersecting_window"],
                                      "fine_shared_stations_in_window": d["fine_shared_stations_in_window"]}
                                     for d in inv]
    rep["decision"] = ("WOVEN MASTER SPEC + SCALE ESTIMATE DONE (build-only, Solve() 0, --solve REFUSED): "
                       "coarse=%d bool / %d cons · fine-estimate=%d bool / %d cons · awaiting supervisor word"
                       % (n_bool, n_cons, rep["fine_master_estimate"]["bool_vars_estimate"],
                          rep["fine_master_estimate"]["constraints_estimate"]))
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({"coarse": rep["coarse_master"], "fine_estimate": rep["fine_master_estimate"],
                      "readings": rep["readings"], "decision": rep["decision"]}, ensure_ascii=False, indent=1))
    print("WROTE", a.out)


if __name__ == "__main__":
    main()
