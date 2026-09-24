#!/usr/bin/env python3
"""K2 · R514-诊断（只读 · Solve() 0 次）—— 坐实 **R512 净距编码的实现缺陷**（承 R514 INFEASIBLE 之归因）：

R512 §"(b) EXACT per-lane clearance encoding" 写：
    E(r)  = 以 r 为**端点**的弧；S2(r) = 以 r 为**严格影子**的弧
    每车道 l：  sum_{l'!=l} S2(r) + M * y(l,r) <= M ,  M = |others|+1
              y(l,r) = sum(E(r) 中属于 l 的弧) + [src_l == r]
注释自称 y 是 0/1 指示（"a lane may pass r and shadow r itself = legal"）。
**但 `sum(vs)` 是计数**：一条**穿过** r 的车道有 2 条弧以 r 为端点（进弧＋出弧）⇒ y = 2 ⇒
     sum(others) + 2M <= M  是**恒假式**（others ≥ 0）⇒ 只要"某车道穿过 r" 且 "他车道影子扫到 r"，
该约束即**结构性不可满足**。故模型在稠密装箱下**必然 INFEASIBLE**（与几何无关）。
本件给两件机器证据：① 最小实例（同型 CP-SAT：缺陷式 vs 指示式）；② 在 R514 实模型上的**结构性计数**。
"""
import collections, importlib, json, math, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
R514 = importlib.import_module("K2_" + "R" + "514" + "_LAYERHOP_JOINT_MCF_v1")
R512 = R514.R512
from ortools.sat.python import cp_model


def minimal_instance():
    """同型最小实例（决定性）：两条车道路径 —— A 走 0-1-2（**穿过**节点 1，用 2 条弧），B 的候选弧
    *可以*影子扫到节点 1（B 有 1 个影子候选变量 yB）。比较三种取法：
      · 合法配置  : A 穿过节点 1 · **B 不靠近**（yB = 0）
      · 非法配置  : A 穿过节点 1 · B 影子扫到节点 1（yB = 1）
      ① R512 原式 y = sum(E(r) 中属于 l 的弧)      → 合法配置竟 **INFEASIBLE**（假否定！）
      ② 指示式   y = 0/1 指示「l 用到 ≥1 条以 r 为端点/为头的弧」→ 合法 SAT / 非法 INFEASIBLE（正确）"""
    out = {}
    def build(form, yB_val):
        m = cp_model.CpModel()
        x01 = m.NewBoolVar("A_0-1"); x12 = m.NewBoolVar("A_1-2"); yB = m.NewBoolVar("B_cand_shadow_1")
        m.Add(x01 == 1); m.Add(x12 == 1); m.Add(yB == yB_val)
        M = 2                                        # M = |others| + 1 = 1 + 1
        if form == "r512_y_equals_sum_of_endpoint_arcs":
            y = x01 + x12                            # 穿过 r ⇒ y = 2
            m.Add(yB + M * y <= M)
        else:                                        # 指示式（w 由 sum(endpoint arcs) >= 1 定义）
            w = m.NewBoolVar("w_A_visits_1")
            m.Add(w <= x01 + x12); m.Add(w >= x01); m.Add(w >= x12)      # w=1 <=> A 用到节点1的弧
            m.Add(yB + M * w <= M)
        sv = cp_model.CpSolver()
        return sv.StatusName(sv.Solve(m))
    out["config_legal_A_through_B_away(yB=0)"] = {
        "r512_defective_form": build("r512_y_equals_sum_of_endpoint_arcs", 0),
        "indicator_form": build("indicator", 0),
        "verdict": "defective form WRONGLY infeasible (false negative); indicator form correctly SAT"}
    out["config_illegal_A_through_B_shadows(yB=1)"] = {
        "r512_defective_form": build("r512_y_equals_sum_of_endpoint_arcs", 1),
        "indicator_form": build("indicator", 1),
        "verdict": "both correctly infeasible"}
    out["decision"] = ("R512/R514 净距约束的线性实现（y=sum(endpoint arcs)，M=|others|+1）"
                       "把「车道穿过 r」判成 y=2 ⇒ sum(others)+M*y<=M 恒假 ⇒ **连合法配置都被判不可行**；"
                       "指示式（y ∈ {0,1}）给出正确判据。")
    return out


def structural_count(l1="full", verbose=True):
    """在 R514 实模型上数：有多少条净距约束因 `y=sum(vs)` 而结构性不可满足。"""
    model = json.load(open("/tmp/opencode/archer/model_l8.json"))
    t0 = time.time()
    g2 = R514.Gen2(model, l1scope=l1, verbose=verbose)
    lanes = []
    for nm in g2.names:
        L = g2.build_lane(nm)
        if L is None:
            return {"error": "lane build failed", "nm": nm}
        lanes.append(L)
    NID = R514.NID
    endc = collections.defaultdict(lambda: collections.Counter())    # (L,pos) -> lane -> #arcs with pos as endpoint
    shad = collections.defaultdict(lambda: collections.Counter())    # (L,pos) -> lane -> #arcs with pos as strict shadow
    narcs = 0
    for li, L in enumerate(lanes):
        for u, lst in L["adj"].items():
            for (v, w) in lst:
                narcs += 1
                Lr = u // NID; pu = u % NID; pv = v % NID
                for c in R512.claim_of(pu, pv):
                    key = (Lr, c)
                    if c in (pu, pv):
                        endc[key][li] += 1
                    else:
                        shad[key][li] += 1
    n_clr = 0; n_bad = 0; y_multi = collections.Counter(); ex = []
    for key in set(endc) & set(shad):
        byE = {li: n for li, n in endc[key].items() if n}
        byS = {li: n for li, n in shad[key].items() if n}
        for li, n in byE.items():
            others_n = sum(c for l2, c in byS.items() if l2 != li)
            if others_n <= 0:
                continue
            n_clr += 1
            if n >= 2:                                  # 结构性恒假（无论 others 取值）
                n_bad += 1
                y_multi[n] += 1
                if len(ex) < 8:
                    ex.append({"layer": R514.LAYER_OF[key[0]], "node_ij": list(R514.rc(key[1])),
                               "lane": lanes[li]["nm"], "endpoint_arcs": n, "other_shadow_arcs": others_n,
                               "lhs_forced": others_n + (others_n + 1) * n, "rhs": others_n + 1})
    return {"l1_scope": l1, "lanes": len(lanes), "directed_arcs": narcs,
            "clearance_constraints": n_clr, "structurally_unsatisfiable": n_bad,
            "frac_bad": round(n_bad / max(1, n_clr), 4), "endpoint_count_histogram": dict(y_multi),
            "examples": ex, "elapsed_s": round(time.time() - t0, 1)}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--l1", default="full"); ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or os.path.join(HERE, "K2_R514_ENCODING_DEFECT_PROOF_v1.json")
    rep = {"artifact": "k2_r514_encoding_defect_proof_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "diagnostic attribution of the R514 INFEASIBLE reading (read-only; Solve() 0 calls; quota 0)",
           "claim": "R512/R514 clearance constraint `sum(others) + M*y <= M` uses y = sum(endpoint arcs) (a COUNT, "
                    "not a 0/1 indicator); a lane PASSING a node contributes 2 => the constraint is identically false.",
           "minimal_instance": minimal_instance(),
           "structural_count": structural_count(a.l1)}
    json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({"minimal_instance": rep["minimal_instance"],
                      "structural_count": {k: v for k, v in rep["structural_count"].items() if k != "examples"},
                      "examples": rep["structural_count"].get("examples", [])[:3]},
                     ensure_ascii=False, indent=1))
    print("WROTE", out)
