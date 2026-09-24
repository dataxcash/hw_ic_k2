#!/usr/bin/env python3
"""K2 · R519 v2 —— 关闭 #K2-189 §四第一步的 **Q3**：R499 序变量族（declared order = A 锚 x 序，无条件单调）
移植到本几何后，**是否与设计同解集**？本器给**机核反例**（v1 的首稿几何被在册判据自己判为不合法 ⇒ 已弃，v1 归档）。

反例：两根线**全程 In5**、**合法**（逐对声明集互斥 = 在册判据），但其**门列（row 36）横向次序与 A 锚 x 序相反**：
  W1（A 锚 x=84.6，declared 序在前）：In5 南行 → 东行（较深 y=59.0）→ 在 **x=125** 转北
  W2（A 锚 x=85.8，declared 序在后）：In5 南行 → 东行（较浅 y=58.0）→ 在 **x=120** 转北
⇒ 门列上 W2(x=120) 在 W1(x=125) **之西** ⇒ **逆序**。原版 R499 的无条件单调约束**禁止**该配置
⇒ 其解集 ⊂ 设计解集 ⇒ **不同解集**（机证）。**无需任何过孔**（连"宽区换位"都省了）。
只读 · `Solve()` 0 次 · 不改任何在册件。
"""
import importlib, json, math, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
W = importlib.import_module("K2_" + "R" + "515" + "_FREETERMINALS_v1")
claim_seg, P = W.claim_seg, W.P
rep = {"artifact": "k2_r519_q3_equivalence_counterexample_v2", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "authority": "#K2-189 §四 step-1 (machine-show whether lever 丙's encoding has the SAME solution set as the design)",
       "solve_calls": 0, "supersedes": "v1 (its draft geometry was judged ILLEGAL by the registered rule itself - kept archived)"}

W1 = [(84.60, 55.823), (84.60, 59.0), (125.0, 59.0), (125.0, 36.5)]
W2 = [(85.80, 55.823), (85.80, 58.0), (120.0, 58.0), (120.0, 36.5)]

def seg_seg_dist(a, b, c, d):
    def pt_seg(p, q, r):
        px, py = p; qx, qy = q; rx, ry = r
        dx, dy = qx - px, qy - py
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((rx - px) * dx + (ry - py) * dy) / L2))
        return math.hypot(rx - (px + t * dx), ry - (py + t * dy))
    return min(pt_seg(a, b, c), pt_seg(a, b, d), pt_seg(c, d, a), pt_seg(c, d, b))

viol, mind = [], 9e9
for i in range(len(W1) - 1):
    for j in range(len(W2) - 1):
        a1, a2, b1, b2 = W1[i], W1[i + 1], W2[j], W2[j + 1]
        if claim_seg(a1[0], a1[1], a2[0], a2[1]) & claim_seg(b1[0], b1[1], b2[0], b2[1]):
            viol.append({"W1_seg": [list(a1), list(a2)], "W2_seg": [list(b1), list(b2)]})
        mind = min(mind, seg_seg_dist(a1, a2, b1, b2))
rep["counterexample_configuration"] = {"W1_anchor_x": 84.60, "W2_anchor_x": 85.80,
    "declared_order": ["W1", "W2"], "W1_In5_polyline": W1, "W2_In5_polyline": W2,
    "layers_used": ["In5.Cu only"], "vias": 0}
rep["machine_checks"] = {
    "In5_declaration_set_conflicts": {"n_viol": len(viol), "pass": not viol, "first": viol[:2]},
    "min_true_seg_seg_distance_mm": {"value": round(mind, 4), "required_P_mm": P, "pass": mind >= P - 1e-9},
    "both_on_In5_at_the_gate_cut_row36": True,
    "via_pairs_per_lane": {"W1": 0, "W2": 0},
    "in_zone_requirement": "NOT APPLICABLE (no vias at all)",
}
rep["order_at_the_gate_cut"] = {"W1_column_x": 125.0, "W2_column_x": 120.0,
                                "order_west_to_east_at_cut": ["W2", "W1"],
                                "declared_order": ["W1(anchor_x=84.60)", "W2(anchor_x=85.80)"],
                                "inverted": True}
rep["all_legality_checks_pass"] = (not viol) and (mind >= P - 1e-9)
rep["verdict"] = {
    "Q3": ("NON-EQUIVALENT (counterexample found; legal by the registered declaration-set rule itself, with zero vias)"
           if rep["all_legality_checks_pass"] else "counterexample draft still illegal - see checks"),
    "meaning": ("R499's unconditional monotone order constraint (declared A-anchor-x order) forbids a legal configuration "
                "=> the naive port's solution set is a PROPER SUBSET of the design's set => per #K2-189 §四 its UNSAT may "
                "NOT be used for any design-level conclusion (the same defect class for which lever 乙 was rejected)."),
    "consequence": ("do NOT spend the single certified solve on the naive port. Lever 丙 must be implemented in the FAITHFUL "
                    "form: swap-accounting / parity order variables (per-section rank + 'a rank inversion between adjacent "
                    "sections requires a via arc in that interval'), which IS implied by per-layer declaration-set exclusivity "
                    "=> same solution set, while still making 'which lane goes first / where it swaps' an explicit machine variable."),
    "certified_quota": "UNSPENT (deliberately) - burning it here would recreate the rejected-乙 trap",
}
rep["boundaries"] = ("read-only; Solve() 0; no model/parameter change; board/SPEC/tools/criteria untouched; frozen four 4/4; "
                     "no WORKER; no .omo/supervision writes; construction stop-line maintained")
rep["buildability"] = "NOT-APPLICABLE (encoding-equivalence counterexample; no construction/feasibility claim)"
out = os.path.join(HERE, "K2_R519_Q3_EQUIVALENCE_COUNTEREXAMPLE_v2.json")
json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps({k: rep[k] for k in ("machine_checks", "order_at_the_gate_cut", "all_legality_checks_pass", "verdict")},
                 ensure_ascii=False)[:1800]); print("WROTE", out)
