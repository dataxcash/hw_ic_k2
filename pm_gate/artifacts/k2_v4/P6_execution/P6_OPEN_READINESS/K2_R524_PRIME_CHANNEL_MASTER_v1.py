#!/usr/bin/env python3
"""K2 · R524 —— 丙′（通道化分解）**小主问题**（#K2-192 §三.3.b · 建模型 + Validate · `Solve()` 默认 0 次）。

主问题（小 · 整数）＝**在册槽位 ＋ 换位/行程账本**：
  ① 院行 `y_i ∈ YARD_ROWS(38..57)`（col60 断面 · 横向=行）—— 16 根线、all-different、**按登记声明序非交叉**；
  ② 门列 `c_i ∈ GATE_COLS(115..135)`（row36 断面 · 横向=列）—— 仅**东组 8 根**、all-different、非交叉；
  ③ 墙缝 `g_i ∈ GAPS(7,11,12,13,15,24,25,28)`（col114 断面 · 横向=行）—— 仅**西组 8 根**、all-different、非交叉；
  ④ **行程账本**（本窗新产）：`EXC_i ∈ {0,1}` = 该线使用**一段** In4 行程（在册 `MAX_VIA_PAIRS=2` ⇒ 至多一段）；
     对被院序→出口序**反序**的每一对 (i,j)：要求 `EXC_i ∨ EXC_j`（同层不可交叉 ⇒ 反序对至少一方须在 In4）。
     目标 = **最小化 Σ EXC**（"能少走一层就少走"）。

在册依据：R512 §c 的 门列/院行/缝位 三组序变量 + R523 §二 的断面口径；非交叉 = 声明序单调（R512 原式）。
**本件只建模型 + Validate（0 求解）**；受证额度由 `--solve` 显式开启，且**须先过** `K2_R524_PRIME_CHANNEL_SELFCHECK_v1`
的保真自检（#K2-192 §三.3.a）。
"""
import argparse, importlib, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
F = importlib.import_module("K2_R523_LAYERHOP_PARITY_FORMC_v1")
P, X0, Y0 = F.P, F.X0, F.Y0
MODEL = "/tmp/opencode/archer/model_l8.json"
YARD_COL, YARD_ROWS = 60, list(range(38, 58))
GATE_ROW, GATE_COLS = 36, list(range(115, 136))
WALL_COL, GAPS = 114, [7, 11, 12, 13, 15, 24, 25, 28]
SCALE_GATE = 1_200_000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "K2_R524_MASTER_PLAN_v1.json"))
    ap.add_argument("--solve", action="store_true", help="显式开启那**恰一次**受证求解（默认 0 次）")
    ap.add_argument("--maxtime", type=float, default=1200.0)
    a = ap.parse_args()
    t0 = time.time()
    rep = {"artifact": "k2_r524_prime_channel_master_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-192 sec.3.3.b (build-only, 0 solves) · sec.4 method directive (decomposition)",
           "stages": {"a_selfcheck": "K2_R524_SELFCHECK_v1.json (restriction/partition PASS)",
                      "b_master": "this file (build-only)", "c_one_solve": "explicit --solve only"},
           "sections": {"yard": {"col": YARD_COL, "rows": YARD_ROWS}, "gate": {"row": GATE_ROW, "cols": GATE_COLS},
                        "wall": {"col": WALL_COL, "gaps": GAPS}}}
    from ortools.sat.python import cp_model
    mo = cp_model.CpModel()
    model = json.load(open(MODEL))
    g2 = F.Gen2(model, l1scope="full")
    names = g2.names
    A = {nm: g2.A[nm] for nm in names}; B = {nm: g2.B[nm] for nm in names}
    order = sorted(range(len(names)), key=lambda i: A[names[i]][0])       # registered declared order (by A.x)
    grp = [g2.grp[names[i]] for i in range(len(names))]
    east = [i for i in order if grp[i] == "east"]
    west = [i for i in order if grp[i] == "west"]
    rep["groups"] = {"declared_order_by_Ax": [names[i] for i in order],
                     "east": [names[i] for i in east], "west": [names[i] for i in west],
                     "east_count": len(east), "west_count": len(west),
                     "gate_cols_available": len(GATE_COLS), "wall_gaps_available": len(GAPS)}

    zy = {i: {r: mo.NewBoolVar("zy_%d_%d" % (i, r)) for r in YARD_ROWS} for i in range(len(names))}
    for i in range(len(names)):
        mo.AddExactlyOne(zy[i].values())
    for r in YARD_ROWS:
        mo.Add(sum(zy[i][r] for i in range(len(names))) <= 1)
    pos_y = {}
    for i in range(len(names)):
        pos_y[i] = mo.NewIntVar(0, len(YARD_ROWS) - 1, "py_%d" % i)
        mo.Add(pos_y[i] == sum(k * zy[i][r] for k, r in enumerate(YARD_ROWS)))
    for oa, ob in zip(order, order[1:]):                     # 非交叉（登记声明序单调）
        mo.Add(pos_y[oa] <= pos_y[ob] - 1)

    zc = {i: {c: mo.NewBoolVar("zc_%d_%d" % (i, c)) for c in GATE_COLS} for i in east}
    for i in east:
        mo.AddExactlyOne(zc[i].values())
    for c in GATE_COLS:
        mo.Add(sum(zc[i][c] for i in east) <= 1)
    pos_c = {}
    for i in east:
        pos_c[i] = mo.NewIntVar(0, len(GATE_COLS) - 1, "pc_%d" % i)
        mo.Add(pos_c[i] == sum(k * zc[i][c] for k, c in enumerate(GATE_COLS)))
    for oa, ob in zip(east, east[1:]):
        mo.Add(pos_c[oa] <= pos_c[ob] - 1)

    zg = {i: {g: mo.NewBoolVar("zg_%d_%d" % (i, g)) for g in GAPS} for i in west}
    for i in west:
        mo.AddExactlyOne(zg[i].values())
    for g in GAPS:
        mo.Add(sum(zg[i][g] for i in west) <= 1)
    pos_g = {}
    for i in west:
        pos_g[i] = mo.NewIntVar(0, len(GAPS) - 1, "pg_%d" % i)
        mo.Add(pos_g[i] == sum(k * zg[i][g] for k, g in enumerate(GAPS)))
    for oa, ob in zip(west, west[1:]):
        mo.Add(pos_g[oa] <= pos_g[ob] - 1)

    # ---- 行程账本：反序对 ⇒ 至少一方 EXC（在册 MAX_VIA_PAIRS=2 ⇒ 至多一段行程）
    EXC = {i: mo.NewBoolVar("exc_%d" % i) for i in range(len(names))}
    exitpos = {}
    for i in range(len(names)):
        exitpos[i] = pos_c[i] if grp[i] == "east" else pos_g[i]
    ninv = 0
    for x in range(len(names)):
        for y_ in range(x + 1, len(names)):
            i, j = order[x], order[y_]
            # declared-yard order is i before j; if the exit order puts j before i => inverted pair
            b = mo.NewBoolVar("lt_%d_%d" % (i, j))
            mo.Add(exitpos[j] <= exitpos[i] - 1).OnlyEnforceIf(b)
            mo.Add(exitpos[j] >= exitpos[i]).OnlyEnforceIf(b.Not())
            mo.Add(EXC[i] + EXC[j] >= 1).OnlyEnforceIf(b)
            ninv += 1
    mo.Minimize(sum(EXC.values()))
    rep["master_model"] = {"bool_vars": len(mo.Proto().variables), "constraints": len(mo.Proto().constraints),
                           "inversion_indicator_pairs": ninv,
                           "yard_slots": len(YARD_ROWS), "gate_slots": len(GATE_COLS), "gap_slots": len(GAPS),
                           "objective": "min sum(EXC)"}
    rep["scale_gate"] = {"bool_vars": len(mo.Proto().variables), "gate": SCALE_GATE,
                         "under_gate": len(mo.Proto().variables) <= SCALE_GATE}
    v = mo.Validate()
    rep["validate"] = (v if v else "OK")
    rep["build_only"] = True
    if not rep["scale_gate"]["under_gate"] or (v and v != ""):
        rep["decision"] = "FAIL-CLOSED: 规模闸/Validate 未过 ⇒ 不求解"
    elif not a.solve:
        rep["decision"] = ("BUILD-ONLY GREEN（规模闸 + Validate 过 · Solve() 0 次 · 受证额度**未消耗**）"
                           " ⇒ 由 --solve 显式开启那恰一次")
    else:
        solver = cp_model.CpSolver(); solver.parameters.max_time_in_seconds = a.maxtime
        st = solver.Solve(mo)
        rep["solve"] = {"status": solver.StatusName(st), "wall_s": round(solver.WallTime(), 1),
                        "objective_min_sum_EXC": (int(solver.ObjectiveValue()) if solver.ObjectiveValue() is not None else None)}
        rep["solve_value"] = {names[i]: {"yard_row": (solver.Value(pos_y[i]) if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None)}
                              for i in range(len(names))}
        rep["decision"] = "SOLVED: %s" % solver.StatusName(st)
    rep["elapsed_s"] = round(time.time() - t0, 1)
    json.dump(rep, open(a.out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: rep[k] for k in ("groups", "master_model", "scale_gate", "validate", "decision") if k in rep},
                     ensure_ascii=False, indent=1)[:2500])
    print("WROTE", a.out)


if __name__ == "__main__":
    main()
