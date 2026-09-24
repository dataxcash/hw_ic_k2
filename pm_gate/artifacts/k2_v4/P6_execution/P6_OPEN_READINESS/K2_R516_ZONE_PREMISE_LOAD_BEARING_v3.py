#!/usr/bin/env python3
"""K2 · R516-A v3 —— **「乙」杠杆的前提是否承重（load-bearing）**：只读机核 · `Solve()` 0 次。

缘起：R515 §五 向监理请裁三条杠杆（甲 延预算 / 乙 In4 缩到四宽区 / 丙 加在册显式序变量），
并称「乙的两种结果都是落地二值」。本器检验该断言的 **UNSAT 支**：
  #K2-187 §四.⑤ 要求「设计级不可行」须附**非空核**且**各前提逐条机核非绑定**；
  乙相对甲多出的那条前提 = 「In4 只能出现在四个在册宽区内」（D1: l1_scope=zones）。
若该前提**承重**（可测：某些必过断面上，把 In4 限到四宽区后两层合计容量 < 16 根），
则乙的 UNSAT **不是**设计级证书、**不是**「具名不成」，只是「我自己加的沙盒太窄」。

方法（全部在册件）：
  1. 在册 `Gen2(model, l1scope=full|zones)` 建同一张双层保守图的 free-node 栅格；
  2. 对**每一列/每一行割**数「该割上可放车道中心的自由节点数」= 该割的并排容量（上界；保守下界另报最长连续段）；
  3. 逐割比较 full 与 zones 的容量：凡 full ≥ 16 而 zones < 16 ⇒ 该割上「乙前提承重」；
  4. 另引两份**已在册的** BUILD-ONLY 工件（full / zones）之最短路上涨幅度作独立承重证据。

只读：不动板 / SPEC / 工具 / 判据 / 冻结四源；不建模型、不 `Solve()`、不占额度。
"""
import importlib, json, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
R = importlib.import_module("K2_" + "R" + "514" + "_LAYERHOP_JOINT_MCF_v2")
P, NX, NY, X0, Y0 = R.P, R.NX, R.NY, R.X0, R.Y0
DEMAND = 16


def longest_run(v):
    best = cur = 0
    for x in v:
        cur = cur + 1 if x else 0
        best = max(best, cur)
    return best


def build(scope):
    g = R.Gen2(model, l1scope=scope, verbose=False)
    return {L: g.free_node[L].reshape(NX, NY) for L in (0, 1)}


def prof(F, axis):
    """axis='col': 每列 i 计数（垂直割）；axis='row': 每行 j 计数（水平割）"""
    out = {}
    for L in (0, 1):
        nm = R.LAYER_OF[L]
        arr = F[L]
        if axis == "col":
            out[("cnt", nm)] = [int(arr[i, :].sum()) for i in range(NX)]
            out[("run", nm)] = [longest_run(arr[i, :]) for i in range(NX)]
        else:
            out[("cnt", nm)] = [int(arr[:, j].sum()) for j in range(NY)]
            out[("run", nm)] = [longest_run(arr[:, j]) for j in range(NY)]
    return out


def sect(o, a, b, key):
    return [o[key][i] for i in range(a, b + 1)]


def summarize(o, a, b, tag, axis="col"):
    i5 = sect(o, a, b, ("cnt", "In5.Cu")); i4 = sect(o, a, b, ("cnt", "In4.Cu"))
    tot = [x + y for x, y in zip(i5, i4)]
    return {"section": tag, "axis": axis, "cols_or_rows": [a, b],
            "In5_min": int(min(i5)), "In4_min": int(min(i4)), "sum_min_at_same_cut": int(min(tot)),
            "cuts_where_sum_lt_16": [a + k for k, t in enumerate(tot) if t < DEMAND],
            "cuts_where_sum_lt_8": [a + k for k, t in enumerate(tot) if t < 8]}


model = json.load(open("/tmp/opencode/archer/model_l8.json"))
t0 = time.time()
Ff = build("full")

# Gen2 的 zone2d（逐字复刻其 ceil/floor 格点化），用于把 In4 限到四宽区（= 乙的前提）
import math
_z = np.zeros((NX, NY), bool)
for (_x0, _y0, _x1, _y1) in R.ZONES:
    _i0 = max(0, int(math.ceil((_x0 - X0) / P - 1e-9))); _i1 = int(math.floor((_x1 - X0) / P + 1e-9))
    _j0 = max(0, int(math.ceil((_y0 - Y0) / P - 1e-9))); _j1 = int(math.floor((_y1 - Y0) / P + 1e-9))
    _z[_i0:_i1 + 1, _j0:_j1 + 1] = True
Fz = {0: Ff[0], 1: (Ff[1] & _z)}      # 乙 = In4 仅四宽区（Gen2._node_ok 对 L==1 & zones 正是 ok &= zone2d）

# 自由节点总量（机核：乙 = 子集）
tot_free = {"In5": int(Ff[0].sum()), "In4_full": int(Ff[1].sum()), "In4_zones": int(Fz[1].sum()),
            "subset_ok": bool((Fz[1] & ~Ff[1]).sum() == 0), "In4_stripped_by_zones": int((Ff[1] & ~Fz[1]).sum()),
            "zone_mask_nodes": int(_z.sum()), "In4_free_nodes_inside_zones": int(Ff[1][_z].sum()),
            "In4_free_nodes_outside_zones": int(Ff[1][~_z].sum())}

# 四宽区与「必过断面」的空间关系
WALL_COL, GATE = 114, list(range(113, 136))
zs = list(enumerate(R.ZONES))   # [(zone_id, (x0, y0, x1, y1)), ...]
col_in_zone = {}
for i in range(NX):
    x = X0 + i * P
    col_in_zone[i] = [n for n, b in zs if b[0] <= x <= b[2]]

cuts = {"comb_exit_cols_0_33": (0, 33), "mid_cols_34_112": (34, 112),
        "gate_funnel_cols_113_135": (113, 135), "pad_field_cols_113_137": (113, min(137, NX - 1))}
pf, pz = prof(Ff, "col"), prof(Fz, "col")
rep = {
    "artifact": "k2_r516_zone_premise_load_bearing_v3",
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "authority": "#K2-187 sec.3.6 / sec.4.5 (design-level infeasibility requires a non-empty core AND each premise "
                 "machine-shown non-binding) · R515 sec.5 pending lever decision (jia/yi/bing)",
    "question": "Is lever-YI's extra premise (In4 restricted to the 4 registered wide zones) LOAD-BEARING? "
                "If yes, a lever-YI UNSAT is a self-inflicted sandbox verdict, NOT a design certificate.",
    "method": "registered Gen2(full|zones) free-node rasters; per cut, count of nodes where a lane centre may sit "
              "= side-by-side capacity of that cut (upper bound; conservative contiguous-run also reported)",
    "demand_lanes": DEMAND, "lattice": [NX, NY], "P_mm": P, "origin_mm": [X0, Y0],
    "wall_col": {"col": WALL_COL, "x_mm": round(X0 + WALL_COL * P, 3)},
    "free_nodes": tot_free,
    "zone_boxes": [{"id": n, "box": list(b)} for n, b in zs],
    "cuts": {},
}
for tag, (a, b) in cuts.items():
    sf = summarize(pf, a, b, tag + "|full")
    sz = summarize(pz, a, b, tag + "|zones")
    sf["cuts_where_sum_lt_16_zones_variant"] = sz["cuts_where_sum_lt_16"]
    sf["zones_min_sum"] = sz["sum_min_at_same_cut"]
    sf["zones_minus_full_min"] = sf["sum_min_at_same_cut"] - sz["sum_min_at_same_cut"]
    sf["LOAD_BEARING_at_this_section"] = bool(len(sz["cuts_where_sum_lt_16"]) > 0)
    rep["cuts"][tag] = sf

# 墙列：洞带容量（西组 8 根）
wb = {}
for nm, F in (("full", Ff), ("zones", Fz)):
    run5 = longest_run(Ff[0][WALL_COL, :])
    run4 = longest_run(F[1][WALL_COL, :])
    cnt4 = int(F[1][WALL_COL, :].sum())
    wb[nm] = {"In5_longest_run": int(run5), "In4_longest_run": int(run4), "In4_free_nodes": cnt4,
              "sum_runs": int(run5 + run4)}
rep["wall_column_detail"] = wb
rep["wall_column_in_zones"] = col_in_zone.get(WALL_COL, [])

# 全板逐列「乙前提承重」清单
lb_cols = [i for i in range(NX)
           if (pf[("cnt", "In5.Cu")][i] + pf[("cnt", "In4.Cu")][i]) >= DEMAND
           and (pf[("cnt", "In5.Cu")][i] + pz[("cnt", "In4.Cu")][i]) < DEMAND]
lb_cols_generous = [i for i in range(NX)
                    if (pf[("cnt", "In5.Cu")][i] + pf[("cnt", "In4.Cu")][i]) >= DEMAND
                    and (pf[("cnt", "In5.Cu")][i] + pz[("cnt", "In4.Cu")][i]) < DEMAND]
runlb_cols = [i for i in range(NX)
              if (pf[("run", "In5.Cu")][i] + pf[("run", "In4.Cu")][i]) >= DEMAND
              and (pf[("run", "In5.Cu")][i] + pz[("run", "In4.Cu")][i]) < DEMAND]
rep["load_bearing_columns"] = {
    "n_columns": len(lb_cols), "cols": lb_cols,
    "x_mm_range": [round(X0 + min(lb_cols) * P, 3), round(X0 + max(lb_cols) * P, 3)] if lb_cols else None,
    "in_zones": {str(i): col_in_zone.get(i, []) for i in lb_cols[:40]},
    "same_test_with_conservative_run_metric": {"n_columns": len(runlb_cols), "cols": runlb_cols},
}

# 独立承重证据：两份在册 BUILD-ONLY 工件的最短路上涨
try:
    bf = json.load(open(os.path.join(HERE, "K2_R515_BUILDONLY.json")))
    bz = json.load(open(os.path.join(HERE, "K2_R514_BUILDONLY_ZONES.json")))
    sf_ = bf["graph"]["shortest_path_mm"]; sz_ = bz["graph"]["shortest_path_mm"]
    infl = {k: round(sz_[k] - sf_[k], 3) for k in sf_}
    rep["independent_evidence_shortest_path_inflation_mm"] = {
        "full_total_arcs": bf["graph"]["total_pruned_directed_arcs"],
        "zones_total_arcs": bz["graph"]["total_pruned_directed_arcs"],
        "per_lane_delta_mm": infl,
        "min_delta_mm": min(infl.values()), "max_delta_mm": max(infl.values()),
        "mean_delta_mm": round(sum(infl.values()) / len(infl), 3),
        "note": "CAUTION (v2): these two artifacts come from DIFFERENT script generations "
                "(R514 v2 vs R515 v3 with F1 free legs) => their arc/path deltas are NOT attributable to the l1 "
                "scope alone and are reported as a WEAK side-note only; the cut-capacity test above is the "
                "load-bearing criterion. A clean same-script pair is landed as K2_R516_BUILDONLY_ZONES_v3.json."}
except Exception as e:  # noqa: BLE001
    rep["independent_evidence_shortest_path_inflation_mm"] = {"error": str(e)}

verdict_lb = bool(lb_cols)          # 判据只用「割容量」机核；工件代差只作旁证（见下 note）
_sp = rep["independent_evidence_shortest_path_inflation_mm"]
rep["verdict"] = {
    "lever_YI_premise_materiality": {
        "In4_free_nodes_full": tot_free["In4_full"], "In4_free_nodes_zones": tot_free["In4_zones"],
        "stripped": tot_free["In4_stripped_by_zones"],
        "strip_fraction": round(tot_free["In4_stripped_by_zones"] / max(1, tot_free["In4_full"]), 4),
        "wall_column_In4_run_full_vs_zones": [wb["full"]["In4_longest_run"], wb["zones"]["In4_longest_run"]],
        "reading": "乙的前提**不是空操作**：它把第二层（In4）的自由节点从 8258 削到 3046（-5212，即 -63%）；墙列洞带的 In4 连续性 12→5。",
    },
    "must_pass_capacity_test": {
        "count_metric_min_two_layer_capacity_zones": {t: rep["cuts"][t]["zones_min_sum"] for t in rep["cuts"]},
        "count_metric_starved_cuts_zones": [t for t in rep["cuts"] if rep["cuts"][t]["cuts_where_sum_lt_16_zones_variant"]],
        "run_metric_starved_columns_zones": runlb_cols,
        "reading": ("按**计数**口径（割上可放车道中心的自由节点数）所有在册必过断面在 zones 变体下仍 >= 16（梳齿 26 / 中段 64 / 东门 45）；"
                    "按更保守的**连续段**口径，仅两个边缘位置掉到 16 以下：x≈84.0–84.4（梳齿锚以西的板缘，非全体必过）与 x≈133.6（墙列；"
                    "该处本地需求只有西组 8 根，而 In5 连续段 10 >= 8）。"),
    },
    "consequence_for_pending_decision": (
        "本器**既未证明乙前提非承重、也未证明其承重** ⇒ 换二值时："
        "(a) 乙的 **SAT = 有效里程碑**（zones 解 ⊂ full 解的合法解）；"
        "(b) 乙的 **UNSAT 不足以充当设计级证书** —— #K2-187 §四.⑤ 要求「各前提逐条机核非绑定」，而该前提实测削掉第二层 63% 资源，"
        "本器给不出「非绑定」的机核；"
        "(c) 甲（同参延预算）与丙（保真序变量）的 UNSAT 才具备证书路径。"
        "⇒ 建议监理：若要一次换到二值，优先 **丙**（最对症、前提保真）；若用 **乙**，只把它当 SAT-only 探测；"
        "R515 §五「乙的两种结果都是落地二值」一句，**其 UNSAT 支不成立**（本件修正）。"),
    "weak_side_note_generation_gap": {k: _sp.get(k) for k in ("min_delta_mm", "max_delta_mm", "mean_delta_mm")},
    "still_open": "本器只判「前提的材料性/是否可机核为非绑定」，不产出可行见证；二值仍需一次受权求解（本窗额度已用尽）。",
}
rep["boundaries"] = ("read-only; Solve() 0 calls; no model built by this instrument beyond the two registered free-node "
                     "rasters; nothing edited; frozen four sources untouched")
rep["buildability"] = ("NOT-APPLICABLE (premise-bind audit for a pending supervisor decision; no construction/feasibility "
                       "claim; no object moved)")
rep["elapsed_s"] = round(time.time() - t0, 1)
out = os.path.join(HERE, "K2_R516_ZONE_PREMISE_LOAD_BEARING_v3.json")
json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps({k: rep[k] for k in ("free_nodes", "wall_column_detail", "wall_column_in_zones",
                                      "load_bearing_columns")}, ensure_ascii=False)[:1800])
print("--- cuts ---")
for t, v in rep["cuts"].items():
    print(t, {kk: v[kk] for kk in ("In5_min", "In4_min", "sum_min_at_same_cut", "zones_min_sum",
                                   "zones_minus_full_min", "LOAD_BEARING_at_this_section",
                                   "cuts_where_sum_lt_16", "cuts_where_sum_lt_16_zones_variant") if kk in v})
print("--- inflation ---", json.dumps(rep["independent_evidence_shortest_path_inflation_mm"], ensure_ascii=False)[:700])
print("--- verdict ---", json.dumps(rep["verdict"], ensure_ascii=False))
print("WROTE", out)
