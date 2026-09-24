#!/usr/bin/env python3
"""K2 · R526 —— **编织式丙′ 主问题**（#K2-193 §三.2–3 已批「不改向」· 实例修正）：
**打捆（逐站逐层容量）＋ 行程时刻表 ＋ 次序内生化**；build-only 先过闸，**恰一次**受证求解。

## 为什么是这三样（在册事实，不再重走）
- **R525 W-3（本仓机核）**：三种**静态**通道分法（纯 Voronoi / ∩3 格带 / R524 gate-a 逐字贪心）**A1/A2 都过**，
  但**起点区能走到终点区的线仅 1/16**；机读病因 = 在册那条「声明序 ⇒ 院行**递增**」的**写死次序**规则，
  把 16 根线的"下楼道"与"横向跑道"**互锁 120/120**（嵌套递减则 **0/120**）。
- **R523 §一（在册）**：卡点 = **打捆 / 装箱**（"梳齿区只有 13×4mm，16 条锚脚必须在此扇出"；"必须打捆，贪心打不紧"）。
- **R525 W-2（本仓机核）**：必需置换 π 有 **58 对反序**（`LIS=LDS=6`，6 条最小保序组）。

## 本件模型（小 · 整数 · 一次实现）
**变量**：每根线 i 的**行程时刻表** `start_i / end_i`（一站次区间；含"不下二层"空档）⇒ `on4_i[t]`＝该线在站 t 是否在 In4
（`t ∈ {COMB, BELT, WALL, FIELD}`）；**至多一段** In4 行程（在册 `MAX_VIA_PAIRS=2`）。
**约束**：
  1. **打捆容量**（逐站逐层）：`Σ_i (1−on4_i[t]) ≤ C_In5[t]` 且 `Σ_i on4_i[t] ≤ C_In4[t]`；
  2. **反序对层分离**（被蕴含的必要条件）：58 对反序，每对**至少在一站**处于不同层：`OR_t [on4_i[t] ≠ on4_j[t]]`；
  3. **`Solve()` = 恰一次**（#K2-193 §三.3；中途不得改参/换法/同法重跑）。
**目标**：`min Σ_i (行程站数)`（少走二层 ⇒ 少挤占用带）。
**次序内生化**：本件**不写死任何次序**；次序由 §"路由"阶段的**槽位/骨架**按解出的时刻表**算出**，
并在**路由阶段**由"线序 = 由**难度与时刻表**决定（确定性枚举取最优）"实现。

## 容量 `C[t]` 的**机核来源**（本件打印推导，写死值可复核）
一条线的**声明带**宽度 = `2P`（格点到线段真距 < P ⇒ 轨迹两侧各 ~P）；同层两条**平行**轨迹的轴线至少 **2P** 才互斥。
⇒ 站 t 的**可容轴数** = `floor(span_⊥ / (2P)) + 1`，`span_⊥` = 该站内轨迹的**横向可用跨度**（机核取值）：
  · COMB（下降段·横向 = x）：锚脚 x 跨度 `84.35..93.70` = **9.35mm** ⇒ `C=11`（*不*用整区 13mm，保守）
  · BELT（东向跑道·横向 = y）：区跨 `57.5..66.0` = **8.5mm** ⇒ `C=10`
  · WALL（过墙·横向 = y）：区跨 `43..55` = 12mm ⇒ `C=14`（不紧）
  · FIELD（焊盘扇入·横向 = y）：区跨 `41..54.6` = 13.6mm ⇒ `C=16`（不紧）
⇒ **结合**：`Σon4[COMB] ∈ [5,11]` · `Σon4[BELT] ∈ [6,10]`（**≥N 必须走 In4** = 打捆要求）。

## 闸（承 #K2-192 §三.3 a–e，缺一 fail-closed）
a 前置**只读**保真自检（限制性：路由只用**自己网**的在册合法图；节点不交由**硬预留**保证 —— 本件机核其**结构前提**，`Solve()=0`）；
b build-only = **0 求解**（规模闸 ＋ `Validate()`）；c **恰一次**受证求解；d 在册闸签字（路由件执行）；e `buildability`（路由件出具）。
"""
import argparse, importlib, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
F = importlib.import_module("K2_R523_LAYERHOP_PARITY_FORMC_v1")

MODEL = "/tmp/opencode/archer/model_l8.json"
STATIONS = ["COMB", "BELT", "WALL", "FIELD"]
SCALE_GATE = 1_200_000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "K2_R526_WOVEN_SCHEDULE_v1.json"))
    ap.add_argument("--build-only", action="store_true")
    ap.add_argument("--solve", action="store_true", help="**恰一次**受证求解（#K2-193 §三.3）")
    ap.add_argument("--maxtime", type=float, default=900.0)
    a = ap.parse_args()
    t0 = time.time()
    rep = {"artifact": "k2_r526_woven_schedule_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-193 sec.3.2-3 (woven bing-prime instance fix approved, NOT a method switch; "
                        "same window, same single certified solve) + #K2-192 sec.3.3 a-e hard gates",
           "stations": STATIONS, "solve_calls": 0}

    from ortools.sat.python import cp_model
    model_json = json.load(open(MODEL))
    g2 = F.Gen2(model_json, l1scope="full")
    names = list(g2.names)
    n = len(names)
    atlas = json.load(open(os.path.join(HERE, "K2_R525_INVERSION_ATLAS_v1.json")))
    inv = [(d["pair"][0], d["pair"][1]) for d in atlas["inversion_detail"]]
    idx = {nm: i for i, nm in enumerate(names)}

    # ---- machine-derived packing capacities (see module docstring for the derivation) ----
    P = F.P
    ax = [g2.A[nm][0] for nm in names]
    span_comb = max(ax) - min(ax)                       # anchor x spread (conservative)
    span_belt = F.ZONES[1][3] - F.ZONES[1][1]           # BELT y extent
    span_wall = F.ZONES[2][3] - F.ZONES[2][1]
    span_field = F.ZONES[3][3] - F.ZONES[3][1]
    cap = {0: int(span_comb // (2 * P)) + 1, 1: int(span_belt // (2 * P)) + 1,
           2: int(span_wall // (2 * P)) + 1, 3: int(span_field // (2 * P)) + 1}
    rep["packing_capacity"] = {
        "rule": "cap[t] = floor(span_perp[t] / (2P)) + 1   (declaration band of a track is 2P wide; parallel "
                "tracks need >= 2P axis separation)",
        "P_mm": P, "spans_mm": {"COMB(anchor x)": round(span_comb, 3), "BELT(y)": span_belt,
                                "WALL(y)": span_wall, "FIELD(y)": span_field},
        "cap_In5": {STATIONS[t]: cap[t] for t in range(4)},
        "cap_In4": {STATIONS[t]: cap[t] for t in range(4)},
        "derived": {"min_lanes_on_In4_COMB": max(0, n - cap[0]), "min_lanes_on_In4_BELT": max(0, n - cap[1])}}

    # ---- fidelity self-check (gate a, read-only, Solve() 0): the routing graph is the net's OWN registered graph
    own_ok = True
    per_layer_nodes = {}
    for nm in names:
        legal = {L: set(g2._nok[(nm, L)].reshape(-1).nonzero()[0].tolist()) for L in (0, 1)}
        Lg = g2.build_lane(nm)
        if Lg is None:
            own_ok = False
            continue
        cnt = {0: 0, 1: 0}
        for u in list(Lg["adj"].keys()):
            if u >= F.TERM_BASE:
                continue
            Lay, pos = u // F.NID, u % F.NID
            if pos not in legal[Lay]:
                own_ok = False
            cnt[Lay] += 1
        per_layer_nodes[nm] = cnt
    rep["A_fidelity_selfcheck"] = {
        "routing_graph_subset_of_own_registered_legal_per_layer": bool(own_ok),
        "disjointness_mechanism": "hard declaration-set reservation (each committed lane's claim is removed from "
                                  "later lanes' graphs) => node-disjoint by construction, machine-checked in the "
                                  "route artifact (gate d runs the registered exact_gate + gate_vias anyway)",
        "so": "schedule SAT => any completed routing is a genuine legal witness; schedule UNSAT => SCHEDULE-LEVEL "
              "(weaker) infeasibility, NOT a design-level certificate (#K2-192 sec.3.3.a)",
        "per_lane_graph_nodes_per_layer": per_layer_nodes,
        "verdict": "PASS" if own_ok else "FAIL"}

    # ---- master model ----
    mo = cp_model.CpModel()
    start, end, on4, usexc = {}, {}, {}, {}
    for i in range(n):
        start[i] = {s: mo.NewBoolVar("start_%d_%d" % (i, s)) for s in range(5)}   # 4 = no excursion
        end[i] = {s: mo.NewBoolVar("end_%d_%d" % (i, s)) for s in range(5)}
        mo.Add(sum(start[i].values()) == 1)
        mo.Add(sum(end[i].values()) == 1)
        mo.Add(sum(s * start[i][s] for s in range(5)) <= sum(s * end[i][s] for s in range(5)))
        mo.Add(start[i][4] == end[i][4])                                          # both-or-neither "no excursion"
        on4[i] = {}
        for t in range(4):
            on4[i][t] = mo.NewBoolVar("on4_%d_%d" % (i, t))
            A = sum(start[i][s] for s in range(t + 1))                            # excursion started by t
            B = sum(end[i][s] for s in range(t, 5))                               # not yet ended at t
            mo.Add(on4[i][t] <= A)
            mo.Add(on4[i][t] <= B)
            mo.Add(on4[i][t] >= A + B - 1)
        usexc[i] = mo.NewBoolVar("usexc_%d" % i)
        mo.Add(usexc[i] == 1 - start[i][4])
    # (1) packing capacity per station & layer (assumption-guarded for a non-empty core)
    ass_cap = []
    for t in range(4):
        for kind, tot in (("In5", n - cap[t]), ("In4", cap[t])):
            lb = mo.NewBoolVar("cap_%s_%d" % (kind, t))
            ass_cap.append(lb)
            if kind == "In5":
                mo.Add(sum(1 - on4[i][t] for i in range(n)) <= cap[t]).OnlyEnforceIf(lb)
            else:
                mo.Add(sum(on4[i][t] for i in range(n)) <= cap[t]).OnlyEnforceIf(lb)
    # (2) every inversion pair must be layer-separated at some station (necessary condition)
    ass_pair = []
    for (ni, nj) in inv:
        i, j = idx[ni], idx[nj]
        sep = {}
        for t in range(4):
            b = mo.NewBoolVar("sep_%d_%d_%d" % (i, j, t))
            mo.Add(b >= on4[i][t] - on4[j][t])
            mo.Add(b >= on4[j][t] - on4[i][t])
            mo.Add(b <= on4[i][t] + on4[j][t])
            mo.Add(b <= 2 - on4[i][t] - on4[j][t])
            sep[t] = b
        lb = mo.NewBoolVar("sepneed_%d_%d" % (i, j))
        ass_pair.append(lb)
        mo.Add(sum(sep.values()) >= lb)
    # objective: minimise excursion usage & length
    mo.Minimize(100 * sum(usexc.values()) + sum(sum(t * end[i][t] for t in range(4))
                                                - sum(t * start[i][t] for t in range(4)) for i in range(n)))
    proto = mo.Proto()
    n_bool = len(proto.variables); n_cons = len(proto.constraints)
    v = mo.Validate()
    rep["master_model"] = {"bool_vars": n_bool, "constraints": n_cons, "inversion_pairs": len(inv),
                           "scale_gate": SCALE_GATE, "under_gate": n_bool <= SCALE_GATE,
                           "validate": (v if v else "OK"),
                           "objective": "min 100*#excursions + total_excursion_stations"}
    rep["build_only"] = True
    if n_bool > SCALE_GATE or v:
        rep["decision"] = "FAIL-CLOSED: 规模闸/Validate 未过 ⇒ 不求解"
        json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
        print(rep["decision"]); return
    if not a.solve:
        rep["decision"] = ("BUILD-ONLY GREEN（规模闸 + Validate 过 · Solve() 0 次）⇒ 由 --solve 显式开启那**恰一次**")
        json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
        print(json.dumps({"packing_capacity": rep["packing_capacity"], "A_fidelity_selfcheck": rep["A_fidelity_selfcheck"],
                          "master_model": rep["master_model"], "decision": rep["decision"]},
                         ensure_ascii=False, indent=1))
        print("WROTE", a.out); return
    # ---- the single certified solve (assumption-guarded => a non-empty core on UNSAT) ----
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = a.maxtime
    # ortools 9.15: assumptions are attached to the model; the core comes back as assumption INDICES
    assumptions = ass_cap + ass_pair
    capnames = ["cap_In5_%s" % STATIONS[t] for t in range(4)] + ["cap_In4_%s" % STATIONS[t] for t in range(4)]
    ass_names = capnames + ["inversion_separation:%s|%s" % (inv[k][0], inv[k][1]) for k in range(len(ass_pair))]
    mo.add_assumptions(assumptions)
    st = solver.Solve(mo)
    rep["solve_calls"] = 1
    rep["solve"] = {"status": solver.StatusName(st), "wall_s": round(solver.WallTime(), 1),
                    "objective": (int(solver.ObjectiveValue()) if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None)}
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        names_cap = ["cap_In5_%s" % STATIONS[t] for t in range(4)] + ["cap_In4_%s" % STATIONS[t] for t in range(4)]
        sch = {}
        for i in range(n):
            on = [t for t in range(4) if solver.Value(on4[i][t])]
            sch[names[i]] = {"stations_on_In4": [STATIONS[t] for t in on],
                             "start_station": (None if solver.Value(start[i][4]) else
                                               STATIONS[min(s for s in range(4) if solver.Value(start[i][s]))]),
                             "end_station": (None if solver.Value(end[i][4]) else
                                             STATIONS[max(s for s in range(4) if solver.Value(end[i][s]))]),
                             "uses_excursion": bool(solver.Value(usexc[i]))}
        rep["schedule"] = sch
        rep["inversions_separated"] = len(inv)
        rep["lanes_on_In4_per_station"] = {STATIONS[t]: sum(1 for nm in names if STATIONS[t] in sch[nm]["stations_on_In4"])
                                           for t in range(4)}
        rep["decision"] = ("SCHEDULE SAT（恰一次受证求解 %s · wall=%.1fs）：打包+时刻表+反序分离 全部满足 ⇒ 交路由件执行"
                           % (solver.StatusName(st), solver.WallTime()))
    elif st == cp_model.INFEASIBLE:
        core = list(solver.sufficient_assumptions_for_infeasibility())
        rep["unsat_core_indices"] = core
        rep["unsat_core"] = [ass_names[k] for k in core if 0 <= k < len(ass_names)]
        rep["decision"] = ("SCHEDULE UNSAT（恰一次受证求解返回 INFEASIBLE）：非空核 %d 条 —— 属**调度级**（更弱）不可行，"
                           "**不是**设计级证书（#K2-192 §三.3.a）" % len(rep["unsat_core"]))
    else:
        rep["decision"] = ("SCHEDULE %s（无结论）：按 #K2-193 §三.6 出具名结论、停手报监理（禁自选换法/延预算/自开窗）"
                           % solver.StatusName(st))
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: rep[k] for k in ("solve", "lanes_on_In4_per_station", "unsat_core", "decision") if k in rep},
                     ensure_ascii=False, indent=1)[:2500])
    print("WROTE", a.out)


if __name__ == "__main__":
    main()
