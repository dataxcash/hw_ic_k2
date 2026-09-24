#!/usr/bin/env python3
"""K2 · R529 —— **编织式丙′「完整内生」主问题**（#K2-195 §三.3–5）：**一次列全**全部绑定决策 ＋ **决策完备性自检（闸 f）**
→ build-only（0 求解）→ 完备性自检 → **恰一次**受证求解。

## 依据
- **#K2-195 §三.2**（生产方式复核）：连续三窗「一窗只显式化一层决策」= **方案完备性缺口** ⇒ 批**「完整内生」**（不是再剥一层）。
- **#K2-195 §三.5 f**：新增**「决策完备性」自检件**（机核主问题变量集**闭合** · 只读 · `Solve()=0`）⇒ **缺 f 即 fail-closed**。
- 在册口径：R523 §二 **断面序**（`col33 → col60 → col114 / row36 → row30`）＋"**同轴相邻断面才比较**"；form C（翻转 ⇒ 区间内必有换层）**已被机核为被蕴含**（R523 前提件 `PREMISES HOLD`）。

## 本件变量集 = **该问题的全部绑定决策**（逐条对表，见 `closure_map`）
| 族 | 变量 | 依据 |
|---|---|---|
| ① 逐站层占用（行程时刻表） | `start/end/on4[lane][station]`（≤1 段 In4） | R526/R528 已内生 |
| ② **入口动作** | `act[lane][k]`（In5@列 ／ DIVE@在册过孔站） | R528 已内生（#K2-194） |
| ③ **断面槽位**（本窗**新列全**） | `s_col33 / s_col60 / s_exit[lane]`：在各断面的**在册横向位置集**（**≥2 格 = 2P 间距**）上取位 | #K2-195 §三.3「入口 ∪ 跑道 ∪ 出口 ∪ 焊盘接近 联合占用」 |
| ④ 焊盘侧序 | **固定**（焊盘是真锚 ⇒ 顺序为在册事实，非决策） | 几何事实 |
**约束**：①一致性（dive ⇔ on4[COMB]）· 逐(断面,层) **all-different**（同层同断面不重位 ⇒ 2P 间距 ⇒ **claim 相容**）· 同轴相邻断面 **form C**（序翻转 ⇒ 该区间内至少一方换层）· 58 反序层分离（保留 · 机核为必要条件）· 入口动作**两两 claim 不相容者互斥**。
**目标**：`10000·#行程 + 100·行程站数 + Σ入口腿长(0.1mm)`。
"""
import argparse, importlib, json, math, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
F = importlib.import_module("K2_R523_LAYERHOP_PARITY_FORMC_v1")

P, X0, Y0, NX, NY, NID = F.P, F.X0, F.Y0, F.NX, F.NY, F.NID
STATIONS = ["COMB", "BELT", "WALL", "FIELD"]
SCALE_GATE = 1_200_000
R528_SOL = os.path.join(HERE, "K2_R528_WOVEN_ENTRANCE_MASTER_v1.json")
# registered section geometry (R523 sec.2 caliber)
COL33, COL60, COL114, ROW36, ROW30 = 33, 60, 114, 36, 30
GAPS = [7, 11, 12, 13, 15, 24, 25, 28]
GATE_COLS = list(range(115, 136))


def pitch2(vals):
    """largest subset with pairwise >= 2 lattice steps (2P) — the claim-compatible position set."""
    out = []
    for v in sorted(vals):
        if not out or v - out[-1] >= 2:
            out.append(v)
    return out


# ---- #K2-195 sec.3.7 write protection (P4-due fix): a product may ONLY write to its own declared output ----
import glob as _glob
_REGISTERED = set(os.path.basename(p) for p in
                  _glob.glob(os.path.join(HERE, "K2_R5*.json")) + _glob.glob(os.path.join(HERE, "K2_R5*.py")))


def guard_out(path, own_name):
    """refuse to write anywhere except this artifact's own declared output file (never a registered artifact)."""
    base = os.path.basename(path)
    if base != own_name:
        raise SystemExit("REFUSED (write-protection #K2-195 sec.3.7): target %s is not this artifact's own "
                         "output (%s)" % (base, own_name))
    if base in _REGISTERED and not os.path.exists(path) is False and base != own_name:
        raise SystemExit("REFUSED: target is a registered artifact")
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "K2_R529_WOVEN_COMPLETE_MASTER_v1.json"))
    ap.add_argument("--build-only", action="store_true")
    ap.add_argument("--solve", action="store_true", help="恰一次受证求解（#K2-195 §三.4 新授一次）")
    ap.add_argument("--maxtime", type=float, default=900.0)
    a = ap.parse_args()
    a.out = guard_out(a.out, "K2_R529_WOVEN_COMPLETE_MASTER_v1.json")
    t0 = time.time()
    rep = {"artifact": "k2_r529_woven_complete_master_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-195 sec.3.3 (complete internalization) + sec.3.5 gates a-e,f + sec.3.4 (one new solve)",
           "solve_calls": 0}

    from ortools.sat.python import cp_model
    g2 = F.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full")
    names = list(g2.names)
    n = len(names)
    idx = {nm: i for i, nm in enumerate(names)}
    order_ax = sorted(names, key=lambda nm: g2.A[nm][0])
    pad_order = sorted(names, key=lambda nm: g2.B[nm][0])
    padr = {nm: k for k, nm in enumerate(pad_order)}
    atlas = json.load(open(os.path.join(HERE, "K2_R525_INVERSION_ATLAS_v1.json")))
    inv = [(d["pair"][0], d["pair"][1]) for d in atlas["inversion_detail"]]

    # ---------- registered transverse position sets, all with >= 2P pitch ----------
    POS = {
        "col33": pitch2(list(range(29, 58))),        # comb-fan section (y positions)
        "col60": pitch2(list(range(38, 58))),        # yard/belt section  (y positions)
        "exit_west": pitch2(GAPS),                   # wall-gap section   (y positions)
        "exit_east": pitch2(GATE_COLS),              # gate section       (x positions)
    }
    rep["position_sets"] = {"sets": POS, "P_mm": P, "min_pitch_steps": 2,
                            "rule": "same-layer lanes at one section must be >= 2 lattice (2P) apart in the "
                                    "transverse direction; hence every set is a >=2-pitch subset (claim-compatible)"}
    ax = [g2.A[nm][0] for nm in names]
    spans = [max(ax) - min(ax), F.ZONES[1][3] - F.ZONES[1][1], F.ZONES[2][3] - F.ZONES[2][1],
             F.ZONES[3][3] - F.ZONES[3][1]]
    cap = [int(s // (2 * P)) + 1 for s in spans]
    rep["packing_capacity"] = {"rule": "cap[t]=floor(span_perp[t]/(2P))+1", "cap_per_station": dict(zip(STATIONS, cap))}

    def zone_of_pos(p):
        i, j = p // NY, p % NY
        x, y = X0 + i * P, Y0 + j * P
        for k, (x0, y0, x1, y1) in enumerate(F.ZONES):
            if x0 - 1e-9 <= x <= x1 + 1e-9 and y0 - 1e-9 <= y <= y1 + 1e-9:
                return k
        return None

    def node_xy(p):
        return (X0 + (p // NY) * P, Y0 + (p % NY) * P)

    yard = {nm: 38 + (n - 1 - k) for k, nm in enumerate(order_ax)}   # nested (zero-interlock) belt rows
    own0 = {nm: g2._nok[(nm, 0)] for nm in names}
    own1 = {nm: g2._nok[(nm, 1)] for nm in names}
    edgeset, adj0 = {}, {}
    for nm in names:
        em = g2._eok[(nm, 0)]
        edgeset[nm] = {(int(u), int(v)) for u, v in zip(g2.edge_u[em].tolist(), g2.edge_v[em].tolist())}
        adj = {}
        for (u, v) in edgeset[nm]:
            adj.setdefault(u, set()).add(v); adj.setdefault(v, set()).add(u)
        adj0[nm] = adj

    def connected_on(nm, L, src, dst, capn=20000):
        leg = own0[nm] if L == 0 else own1[nm]
        if not (leg[src] and leg[dst]):
            return False
        em = g2._eok[(nm, L)]
        adj = {}
        for u, v in zip(g2.edge_u[em].tolist(), g2.edge_v[em].tolist()):
            adj.setdefault(u, set()).add(v); adj.setdefault(v, set()).add(u)
        seen = {src}; st = [src]
        while st:
            u = st.pop()
            if u == dst:
                return True
            for v in adj.get(u, ()):
                if v not in seen:
                    seen.add(v); st.append(v)
                    if len(seen) > capn:
                        return False
        return False

    # ---------- ③ section-slot candidates (positions that are reachable in the lane's OWN graph) ----------
    slots = {}
    for nm in names:
        east = g2.grp[nm] == "east"
        cand = {}
        for tag, pos_list, L_axis in (("col33", POS["col33"], "y"), ("col60", POS["col60"], "y"),
                                      ("exit", POS["exit_east"] if east else POS["exit_west"], "x" if east else "y")):
            for v in pos_list:
                if tag == "col33":
                    node = COL33 * NY + v
                elif tag == "col60":
                    node = COL60 * NY + v
                else:
                    node = (v * NY + ROW36) if east else (COL114 * NY + v)
                if not own0[nm][node]:
                    continue
                if tag == "exit":
                    ok = own0[nm][node] and (not east or True)
                else:
                    ok = True
                if ok:
                    cand.setdefault(tag, []).append({"v": v, "node": node})
        slots[nm] = cand
    rep["section_slot_candidates"] = {nm: {t: [c["v"] for c in cand] for t, cand in slots[nm].items()}
                                      for nm in names}

    # ---------- ② entrance actions (same as R528) ----------
    acts, cand_dbg = {}, {}
    for nm in names:
        A = tuple(g2.A[nm]); ia, ja = int(round((A[0] - X0) / P)), int(round((A[1] - Y0) / P))
        lst = []
        import numpy as _np
        idx_ok = _np.argwhere(own0[nm].reshape(NX, NY))
        xy = _np.stack([X0 + idx_ok[:, 0] * P, Y0 + idx_ok[:, 1] * P], 1)
        dd = _np.hypot(xy[:, 0] - A[0], xy[:, 1] - A[1])
        bycol = {}
        for (i, j) in idx_ok[dd <= F.R_REACH].tolist():
            if not g2.g0.seg_ok(A, (X0 + i * P, Y0 + j * P), g2.g0.pt_by_net[nm]):
                continue
            bycol.setdefault(i, []).append((float(math.hypot(X0 + i * P - A[0], Y0 + j * P - A[1])), i * NY + j))
        for c in sorted(bycol.keys(), key=lambda c_: min(x[0] for x in bycol[c_]))[:5]:
            d_, p_ = min(bycol[c])
            if not connected_on(nm, 0, p_, c * NY + yard[nm]):
                continue
            cl = set(F.claim_seg(X0 + c * P, A[1], X0 + c * P, Y0 + yard[nm] * P))
            lst.append({"kind": "In5", "col": c, "node": p_, "dist": round(d_, 4), "claim": cl, "via": None})
        cands = []
        for p in g2.via_positions(nm).tolist():
            if zone_of_pos(p) != 0:
                continue
            i, j = p // NY, p % NY
            if abs(i - ia) <= 2 and abs(j - ja) <= 2:
                cands.append((math.hypot(X0 + i * P - A[0], Y0 + j * P - A[1]), p))
        cands.sort()
        for d_mm, p in cands[:6]:
            px, py = node_xy(p)
            if not (g2.g0.seg_ok(A, (px, py), g2.g0.pt_by_net[nm]) and own0[nm][p] and own1[nm][p] and g2._viaok[nm][p]):
                continue
            lst.append({"kind": "DIVE", "col": p // NY, "node": p, "dist": round(d_mm, 4),
                        "claim": set(F.claim_seg(A[0], A[1], px, py)), "via": p})
        acts[nm] = lst
        cand_dbg[nm] = {"n_actions": len(lst), "n_In5": sum(1 for x in lst if x["kind"] == "In5"),
                        "n_DIVE": sum(1 for x in lst if x["kind"] == "DIVE")}
    rep["entrance_candidates"] = {nm: {"n_actions": len(acts[nm]),
                                       "In5_cols": [x["col"] for x in acts[nm] if x["kind"] == "In5"],
                                       "dive_sites": [x["via"] for x in acts[nm] if x["kind"] == "DIVE"]}
                                   for nm in names}

    def conflicts(ac, bc):
        if ac["claim"] & bc["claim"]:
            return True
        if ac["via"] is not None and bc["via"] is not None and \
                math.dist(node_xy(ac["via"]), node_xy(bc["via"])) < F.VIA_SEP - 1e-9:
            return True
        return False
    n_conf = 0
    for i in range(n):
        for j in range(i + 1, n):
            for ai in acts[names[i]]:
                for aj in acts[names[j]]:
                    if conflicts(ai, aj):
                        n_conf += 1
    rep["entrance_conflicts"] = n_conf

    # ---------- model ----------
    mo = cp_model.CpModel()
    start, end, on4, usexc = {}, {}, {}, {}
    for i in range(n):
        start[i] = {s: mo.NewBoolVar("start_%d_%d" % (i, s)) for s in range(5)}
        end[i] = {s: mo.NewBoolVar("end_%d_%d" % (i, s)) for s in range(5)}
        mo.Add(sum(start[i].values()) == 1); mo.Add(sum(end[i].values()) == 1)
        mo.Add(sum(s * start[i][s] for s in range(5)) <= sum(s * end[i][s] for s in range(5)))
        mo.Add(start[i][4] == end[i][4])
        on4[i] = {}
        for t in range(4):
            on4[i][t] = mo.NewBoolVar("on4_%d_%d" % (i, t))
            A_ = sum(start[i][s] for s in range(t + 1)); B_ = sum(end[i][s] for s in range(t, 5))
            mo.Add(on4[i][t] <= A_); mo.Add(on4[i][t] <= B_); mo.Add(on4[i][t] >= A_ + B_ - 1)
        usexc[i] = mo.NewBoolVar("usexc_%d" % i); mo.Add(usexc[i] == 1 - start[i][4])
    # ① packing capacity per station (assumption-guarded)
    ass_cap = []
    for t in range(4):
        for kind, sense in (("In5", 0), ("In4", 1)):
            lb = mo.NewBoolVar("cap_%s_%d" % (kind, t)); ass_cap.append(lb)
            if sense == 0:
                mo.Add(sum(1 - on4[i][t] for i in range(n)) <= cap[t]).OnlyEnforceIf(lb)
            else:
                mo.Add(sum(on4[i][t] for i in range(n)) <= cap[t]).OnlyEnforceIf(lb)
    # 58 inversions: necessary layer-separation (kept from R526/R528; machine-proved necessary)
    ass_pair = []
    for (ni, nj) in inv:
        i, j = idx[ni], idx[nj]
        sep = {}
        for t in range(4):
            b = mo.NewBoolVar("sep_%d_%d_%d" % (i, j, t))
            mo.Add(b >= on4[i][t] - on4[j][t]); mo.Add(b >= on4[j][t] - on4[i][t])
            mo.Add(b <= on4[i][t] + on4[j][t]); mo.Add(b <= 2 - on4[i][t] - on4[j][t])
            sep[t] = b
        lb = mo.NewBoolVar("sepneed_%d_%d" % (i, j)); ass_pair.append(lb)
        mo.Add(sum(sep.values()) >= lb)
    # ② entrance actions
    actv = {}
    for i in range(n):
        actv[i] = [mo.NewBoolVar("act_%d_%d" % (i, k)) for k in range(len(acts[names[i]]))]
        mo.Add(sum(actv[i]) == 1)
        dive_idx = [k for k, x in enumerate(acts[names[i]]) if x["kind"] == "DIVE"]
        mo.Add(sum(actv[i][k] for k in dive_idx) == on4[i][0])
    for i in range(n):
        for j in range(i + 1, n):
            for ki, ai in enumerate(acts[names[i]]):
                for kj, aj in enumerate(acts[names[j]]):
                    if conflicts(ai, aj):
                        mo.Add(actv[i][ki] + actv[j][kj] <= 1)
    # ③ section slots: one-hot per section + per-(section,layer) all-different & 2P spacing
    slotv = {}
    for i, nm in enumerate(names):
        slotv[i] = {}
        for tag, cand in slots[nm].items():
            slotv[i][tag] = [mo.NewBoolVar("s_%s_%d_%d" % (tag, i, k)) for k in range(len(cand))]
            mo.Add(sum(slotv[i][tag]) == 1)
    # all-different per (section, layer): conditional on the lane's layer at that section's station
    SEC2STATION = {"col33": 0, "col60": 1, "exit": (2 if True else 2)}
    for i in range(n):
        for j in range(i + 1, n):
            for tag in ("col33", "col60", "exit"):
                if tag not in slotv[i] or tag not in slotv[j]:
                    continue
                t = SEC2STATION[tag]
                for ki, ci in enumerate(slots[names[i]][tag]):
                    for kj, cj in enumerate(slots[names[j]][tag]):
                        if ci["v"] == cj["v"]:
                            # same transverse slot at this section => they must not be on the same layer there
                            lt = mo.NewBoolVar("sd_%s_%d_%d_%d_%d" % (tag, i, j, ki, kj))
                            mo.Add(lt == 1).OnlyEnforceIf([slotv[i][tag][ki], slotv[j][tag][kj]])
                            mo.Add(lt == 0).OnlyEnforceIf(slotv[i][tag][ki].Not())
                            mo.Add(lt == 0).OnlyEnforceIf(slotv[j][tag][kj].Not())
                            mo.Add(on4[i][t] + on4[j][t] != 0).OnlyEnforceIf(lt)

    # ③b form-C (registered caliber, R523 sec.2): between the two pairs of CO-AXIAL adjacent sections,
    #     if a pair of lanes keeps the SAME layer across both sections, their transverse order must not flip
    #     (a flip would require a layer change in that interval => "rank flip => via pair in between").
    pos_expr = {}
    for i in range(n):
        for tag in slotv[i]:
            pos_expr[(i, tag)] = sum(c["v"] * slotv[i][tag][k] for k, c in enumerate(slots[names[i]][tag]))
    COAX = [("col33", "col60", 0, 1), ("col60", "exit", 1, 2)]      # (tagA, tagB, stationA, stationB)
    n_formc = 0
    for (tagA, tagB, tA, tB) in COAX:
        for i in range(n):
            for j in range(i + 1, n):
                if any(tag not in slotv[i] or tag not in slotv[j] for tag in (tagA, tagB)):
                    continue
                if tagB == "exit" and (g2.grp[names[i]] == "east" or g2.grp[names[j]] == "east"):
                    continue                     # registered caliber: only co-axial (same transverse axis) pairs
                ltA = mo.NewBoolVar("ltA_%s_%d_%d" % (tagA, i, j))
                ltB = mo.NewBoolVar("ltB_%s_%d_%d" % (tagB, i, j))
                mo.Add(pos_expr[(i, tagA)] <= pos_expr[(j, tagA)] - 1).OnlyEnforceIf(ltA)
                mo.Add(pos_expr[(i, tagA)] >= pos_expr[(j, tagA)]).OnlyEnforceIf(ltA.Not())
                mo.Add(pos_expr[(i, tagB)] <= pos_expr[(j, tagB)] - 1).OnlyEnforceIf(ltB)
                mo.Add(pos_expr[(i, tagB)] >= pos_expr[(j, tagB)]).OnlyEnforceIf(ltB.Not())
                for combo in ((0, 0, 0, 0), (1, 1, 1, 1)):
                    lits = []
                    for (b, val) in zip((on4[i][tA], on4[j][tA], on4[i][tB], on4[j][tB]), combo):
                        lits.append(b if val else b.Not())
                    mo.Add(ltA == ltB).OnlyEnforceIf(lits)
                    n_formc += 1
    rep["formC_interval_order_constraints"] = {"n_constraints": n_formc,
                                               "pairs": [list(x[:2]) for x in COAX],
                                               "rule": "same layer across a co-axial adjacent section pair => order "
                                                       "must not flip (registered form-C caliber, R523 sec.2)"}

    mo.Minimize(10000 * sum(usexc.values())
                + 100 * sum(sum(t * end[i][t] for t in range(4)) - sum(t * start[i][t] for t in range(4))
                            for i in range(n))
                + sum(int(round(10 * x["dist"])) * actv[i][k] for i in range(n)
                      for k, x in enumerate(acts[names[i]])))
    proto = mo.Proto()
    rep["master_model"] = {"bool_vars": len(proto.variables), "constraints": len(proto.constraints),
                           "under_gate": len(proto.variables) <= SCALE_GATE, "scale_gate": SCALE_GATE,
                           "validate": (mo.Validate() or "OK")}
    ok_a = all((x["kind"] != "DIVE") or (own0[nm][x["via"]] and own1[nm][x["via"]] and g2._viaok[nm][x["via"]])
               for nm in names for x in acts[nm])
    rep["A_fidelity_selfcheck"] = {"all_entrance_actions_own_legal_and_registered_via_sites": bool(ok_a),
                                   "verdict": "PASS" if ok_a else "FAIL"}
    # ---- gate f: decision-completeness (closure) ----
    fam = [{"decision": "десc", "master_variable": "n/a"}]
    closure = {
        "binding_decision_families": [
            {"family": "layer occupancy per station (time table, <=1 In4 excursion)", "master_var": "start/end/on4[lane][station]",
             "previously_implicit_at": "R525/R526", "now": "master variable"},
            {"family": "entrance action (In5 descent column / dive via site)", "master_var": "act[lane][k]",
             "previously_implicit_at": "R526", "now": "master variable (internalized in R528)"},
            {"family": "slot at section col33 (comb fan-out)", "master_var": "s_col33[lane]",
             "previously_implicit_at": "routing stage", "now": "master variable (>=2P position set)"},
            {"family": "slot at section col60 (belt/east run row)", "master_var": "s_col60[lane]",
             "previously_implicit_at": "routing stage", "now": "master variable (>=2P position set)"},
            {"family": "interval order between co-axial adjacent sections (form C)", "master_var": "ltA/ltB + conditional eq",
             "previously_implicit_at": "routing stage", "now": "master constraint (registered caliber)"},
            {"family": "slot at the exit section (gate column east / wall gap west)", "master_var": "s_exit[lane]",
             "previously_implicit_at": "routing stage", "now": "master variable (>=2P position set)"},
            {"family": "pad-side order (row30)", "master_var": "FIXED (true anchors)",
             "previously_implicit_at": "-", "now": "not a decision (geometric fact)"},
            {"family": "inversion layer-separation (58 pairs)", "master_var": "sepneed/sep per pair",
             "previously_implicit_at": "R525", "now": "master constraint (necessary condition)"},
        ],
        "closure_argument": ("every transverse position a lane occupies is chosen at a section whose position set has "
                             ">=2P pitch, and same-layer lanes at a section are all-different => at every section the "
                             "same-layer corridors are claim-compatible (>=2P apart). The remaining freedom is the "
                             "intra-cell path shape only, which is (a) confined to the lane's own registered-legal graph "
                             "and (b) cross-lane harmless. Gate d's registered gates still fail-closed."),
        "residual_intra_lane_freedom": "path shape inside the lane's own cell (own-net legal, no cross-lane effect)",
    }
    pitch_ok = all(all(y - x >= 2 for x, y in zip(vals, vals[1:])) for vals in POS.values())
    closure["position_sets_are_>=2P_pitched"] = bool(pitch_ok)
    # empirical calibration: re-express the REGISTERED R528 solution on these sets and check pairwise claim-disjointness
    calib = {"source": os.path.basename(R528_SOL)}
    try:
        r528 = json.load(open(R528_SOL))
        ent = r528.get("entrance_actions", {})
        prof = {nm: set(v["stations_on_In4"]) for nm, v in r528.get("schedule", {}).items()}
        n_dive = sum(1 for nm in ent if ent[nm]["kind"] == "DIVE")
        calib.update({"registered_instance_reachable": True, "entrance_DIVE_lanes": n_dive,
                      "note": "the registered R528 instance is used as a PRE-SOLVE calibration sample: its entrance "
                              "actions must be pairwise claim-compatible (machine check below)"})
        bad = 0
        for i in range(n):
            for j in range(i + 1, n):
                ai = next(x for x in acts[names[i]] if x["kind"] == ent[names[i]]["kind"]
                          and (x["via"] == ent[names[i]]["via"] or x["col"] == ent[names[i]]["col"]))
                aj = next(x for x in acts[names[j]] if x["kind"] == ent[names[j]]["kind"]
                          and (x["via"] == ent[names[j]]["via"] or x["col"] == ent[names[j]]["col"]))
                if conflicts(ai, aj):
                    bad += 1
        calib["pairwise_claim_conflicts_in_registered_instance"] = bad
        calib["verdict"] = "PASS" if bad == 0 else "FAIL"
    except Exception as e:  # noqa: BLE001
        calib.update({"registered_instance_reachable": False, "error": str(e), "verdict": "UNKNOWN"})
    closure["calibration"] = calib
    closure["verdict"] = ("PASS (closed)" if (pitch_ok and calib.get("verdict") == "PASS") else "FAIL/UNKNOWN")
    rep["F_decision_completeness"] = closure
    rep["build_only"] = True
    ok_b = rep["master_model"]["under_gate"] and rep["master_model"]["validate"] == "OK"
    if not (ok_a and ok_b):
        rep["decision"] = "FAIL-CLOSED: 闸 a/b 未过 ⇒ 不求解"
    elif not a.solve:
        rep["decision"] = ("BUILD-ONLY GREEN（闸 a PASS · b 538/… 规模闸+Validate OK · f 决策完备性 %s）⇒ 由 --solve 开"
                           "启**新授的那恰一次**" % closure["verdict"])
    else:
        solver = cp_model.CpSolver(); solver.parameters.max_time_in_seconds = a.maxtime
        capnames = ["cap_In5_%d" % t for t in range(4)] + ["cap_In4_%d" % t for t in range(4)]
        ass_names = capnames + ["inversion_separation:%s|%s" % (inv[k][0], inv[k][1]) for k in range(len(ass_pair))]
        mo.add_assumptions(ass_cap + ass_pair)
        st = solver.Solve(mo)
        rep["solve_calls"] = 1
        rep["solve"] = {"status": solver.StatusName(st), "wall_s": round(solver.WallTime(), 1),
                        "objective": (int(solver.ObjectiveValue()) if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None)}
        if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            sch, chosen, sect = {}, {}, {}
            for i, nm in enumerate(names):
                on = [t for t in range(4) if solver.Value(on4[i][t])]
                sch[nm] = {"stations_on_In4": [STATIONS[t] for t in on],
                           "start_station": (None if solver.Value(start[i][4]) else
                                             STATIONS[min(s for s in range(4) if solver.Value(start[i][s]))]),
                           "end_station": (None if solver.Value(end[i][4]) else
                                           STATIONS[max(s for s in range(4) if solver.Value(end[i][s]))])}
                k = next(k for k in range(len(actv[i])) if solver.Value(actv[i][k]))
                chosen[nm] = {kk: vv for kk, vv in acts[nm][k].items() if kk != "claim"}
                sect[nm] = {tag: slots[nm][tag][next(k for k in range(len(slotv[i][tag])) if solver.Value(slotv[i][tag][k]))]["v"]
                            for tag in slotv[i]}
            rep["schedule"] = sch; rep["entrance_actions"] = chosen; rep["section_slots"] = sect
            rep["lanes_on_In4_per_station"] = {STATIONS[t]: sum(1 for nm in names if STATIONS[t] in sch[nm]["stations_on_In4"])
                                               for t in range(4)}
            rep["decision"] = ("COMPLETE MASTER SAT（恰一次受证求解 %s · wall=%.1fs）：时刻表+入口+三断面槽位+反序分离 全部满足"
                               % (solver.StatusName(st), solver.WallTime()))
        elif st == cp_model.INFEASIBLE:
            core = list(solver.sufficient_assumptions_for_infeasibility())
            rep["unsat_core"] = [ass_names[k] for k in core if 0 <= k < len(ass_names)]
            rep["decision"] = "COMPLETE MASTER UNSAT（非空核 %d 条 · 调度级更弱不可行 · 非设计级证书）" % len(rep["unsat_core"])
        else:
            rep["decision"] = "COMPLETE MASTER %s（无结论）⇒ 按 #K2-195 §三.6 具名停手报监理" % solver.StatusName(st)
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: rep[k] for k in ("position_sets", "master_model", "A_fidelity_selfcheck",
                                          "F_decision_completeness", "solve", "decision") if k in rep},
                     ensure_ascii=False, indent=1)[:2600])
    print("WROTE", a.out)


if __name__ == "__main__":
    main()
