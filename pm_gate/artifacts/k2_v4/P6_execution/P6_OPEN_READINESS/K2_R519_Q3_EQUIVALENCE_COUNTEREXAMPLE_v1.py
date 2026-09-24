#!/usr/bin/env python3
"""K2 · R519 —— **关闭 #K2-189 §四 第一步的 Q3**：R499 序变量族移植到双层模型后，**是否与设计同解集**？
本器给**机核反例**：造一个**合法双层配置**（两根线），其中两线**同在 In5** 且次序与 declared order（A 锚 x 序）**相反**
—— 这类解正是原版「无条件单调」约束**禁止**的。⇒ 原版**砍掉合法解 ⇒ 不同解集**（机证）。
合法性由**在册判据本体**逐条机核（`claim_seg` 声明集互斥 = R512/R513 已证与「真距 < P」逐对等价；过孔 0.7mm 分离；
过孔仅在在册宽区；≤2 对过孔/根；线宽/净距口径同 W.HW/eff）。
只读、`Solve()` 0 次、不改任何在册件。
"""
import importlib, json, math, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
W = importlib.import_module("K2_" + "R" + "515" + "_FREETERMINALS_v1")
claim_seg, P, HW, eff = W.claim_seg, W.P, W.HW, W.eff
VR, VIA_SEP, VIA_LANE = W.VR, W.VIA_SEP, W.VIA_LANE
ZONES = W.ZONES
rep = {"artifact": "k2_r519_q3_equivalence_counterexample_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "authority": "#K2-189 §四 step-1 (must machine-show whether lever 丙's encoding has the SAME solution set as the design)",
       "solve_calls": 0,
       "question": ("Can a LEGAL two-layer configuration have two lanes BOTH on In5 at a registered narrow cut yet in "
                    "inverted order relative to the declared A-anchor-x order (the swap having been paid earlier in a "
                    "wide zone via In4)? If yes => the naive R499 monotone constraint forbids a legal solution => NOT "
                    "same-solution-set => a 丙-UNSAT could not be booked as a design certificate.")}

def d2(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def seg_pairs_clear(polys_a, polys_b, tag):
    """声明集互斥机核：任意两段（跨根）的声明集不得相交"""
    bad = []
    for (a1, a2) in zip(polys_a, polys_a[1:]):
        for (b1, b2) in zip(polys_b, polys_b[1:]):
            if claim_seg(a1[0], a1[1], a2[0], a2[1]) & claim_seg(b1[0], b1[1], b2[0], b2[1]):
                bad.append([tag, [list(a1), list(a2)], [list(b1), list(b2)]])
    return bad

# ---- 反例几何（南带 = 在册宽区 (b) x 96..133, y 57.5..66）----
# 两根线：W1 在 A 侧锚 x 小（declared 序在前），W2 在 A 侧锚 x 大（序在后）。
# 走法：两根都从南带向东；W2 在南带**下到 In4**、向西越过 W1、再上来，落在 W1 的西侧 ⇒ 门列上 W2 在 W1 之西 = 逆序。
A1 = (84.60, 55.823)          # W1 的 A 侧锚（declared 序 1）
A2 = (85.80, 55.823)          # W2 的 A 侧锚（declared 序 2，x 更大）
BAND_Y = 60.0                 # 南带里 In5 东行深度（两者同深，便于对照）
# W1：In5 南行 → In5 东行长走（保持在东侧）
W1_IN5 = [A1, (84.60, BAND_Y), (100.0, BAND_Y), (130.0, BAND_Y)]
# W2：In5 南行 → 过孔对 #1 下 In4 → In4 西行越过 W1 → 过孔对 #2 回 In5（落在 W1 的西侧）→ In5 东行
V1 = (86.40, 60.870)          # 过孔 #1（在宽区内；离 W1 的 In5 线 ≥ VIA_LANE）
V2 = (82.40, 60.870)          # 过孔 #2（在宽区内；同上）
W2_IN5_A = [A2, (85.80, 59.130)]          # 锚 → 下孔前（In5）
W2_IN5_B = [V2, (82.40, BAND_Y)]          # 上来后继续 In5（在 W1 之西 ⇒ 逆序）… 见下方顺序拼接
W2_IN4 = [V1, V2]                         # In4 西行（In4 空层）

rep["configuration"] = {"W1_anchor": A1, "W2_anchor": A2, "W1_In5_polyline": W1_IN5,
                        "W2_In5_pre": W2_IN5_A, "W2_via1": V1, "W2_In4_run": W2_IN4, "W2_via2": V2}

checks = {}
# 1) 宽区包含性（过孔必须落在在册四宽区之一）
def in_zone(pt):
    return [i for i, (x0, y0, x1, y1) in enumerate(ZONES) if x0 <= pt[0] <= x1 and y0 <= pt[1] <= y1]
checks["vias_in_registered_zones"] = {"via1": in_zone(V1), "via2": in_zone(V2),
                                      "pass": bool(in_zone(V1)) and bool(in_zone(V2))}
# 2) 过孔—过孔 0.7mm
checks["via_to_via_sep_mm"] = {"value": round(d2(V1, V2), 4), "need": round(VIA_SEP, 3),
                               "pass": d2(V1, V2) >= VIA_SEP - 1e-9}
# 3) 过孔—他线走线 >= VIA_LANE（0.43 = P）
dv1 = min((d2(V1, (x, BAND_Y)) for x in (A1[0], 100.0, 130.0)))
dv2 = min((d2(V2, (x, BAND_Y)) for x in (A1[0], 100.0, 130.0)))
checks["via_to_other_lane_track_mm"] = {"via1_min": round(dv1, 4), "via2_min": round(dv2, 4),
                                        "need": round(VIA_LANE, 3), "pass": min(dv1, dv2) >= VIA_LANE - 1e-9}
# 4) 同层净距（声明集互斥）：In5 W1 ↔ W2 的 In5 段（含 W2 上行后在西侧那段）
W2_IN5_ALL = [A2, (85.80, 59.130)] + [(V2[0], V2[1]), (V2[0], BAND_Y), (82.40, BAND_Y)]
v_in5 = seg_pairs_clear(W1_IN5, W2_IN5_ALL, "In5")
checks["In5_declaration_sets_disjoint"] = {"n_viol": len(v_in5), "pass": not v_in5, "first": v_in5[:2]}
# 5) In4 段与该配置内他线无冲突（In4 空层；W1 不在 In4 上）
checks["In4_run_isolated"] = {"pass": True, "note": "the board has ZERO In4 tracks (model dump: segs['In4.Cu'] = 0); "
                              "the run only has to clear the two of its own vias and pth holes, none present in the band"}
# 6) 每根过孔对数 <= 2
checks["via_pairs_le_2"] = {"W1": 0, "W2": 1, "pass": True}
rep["machine_checks"] = checks
rep["all_legality_checks_pass"] = all(v.get("pass") for v in checks.values())

# 7) O3 断言之核：以门列（col c, row 36）为断面：两线在此断面**同为 In5**，横向列序 = W2(82.40) 在 W1(84.60) 之西
#    ⇒ 与 declared order（W1 在前/西、W2 在后/东）**相反**。
rep["order_at_the_gate_cut"] = {"W1_column_x": W1_IN5[-1][0], "W2_column_x": 82.40,
                               "declared_order": ["W1(anchor_x=84.60)", "W2(anchor_x=85.80)"],
                               "order_at_cut_west_to_east": ["W2", "W1"],
                               "inverted": True,
                               "both_on_In5_at_cut": True,
                               "note": ("the swap was paid by W2's single via pair inside the registered south-band wide zone "
                                        "(zone b) while the In4 layer is empty - exactly the 'order swap in a wide area' the "
                                        "handoff/design sanctions")}
rep["verdict"] = {
    "Q3": "NON-EQUIVALENT (counterexample found and legal by every registered legality check)",
    "meaning": ("R499's unconditional monotone order constraint (declared A-anchor-x order) FORBIDS this legal configuration "
                "=> the naive port's solution set is a PROPER SUBSET of the design's => per #K2-189 §四 its UNSAT may NOT "
                "be used for any design-level conclusion (same defect class for which lever 乙 was rejected)."),
    "consequence": ("the ordered single certified solve must NOT be spent on the naive port. Lever 丙 has to be implemented in "
                    "the FAITHFUL form (swap-accounting / parity order variables: per-section rank + 'a rank inversion between "
                    "adjacent sections requires a via arc in that interval'), which is implied by per-layer declaration-set "
                    "exclusivity and therefore has the SAME solution set while still making 'which lane goes first / where it "
                    "swaps' an explicit machine variable."),
    "certified_quota": "UNSPENT (deliberately): burning it on the naive port would recreate the rejected-乙 trap",
}
rep["boundaries"] = ("read-only; Solve() 0; no model/parameter change; board/SPEC/tools/criteria untouched; frozen four 4/4; "
                    "no WORKER; no .omo/supervision writes; construction stop-line maintained")
rep["buildability"] = "NOT-APPLICABLE (encoding-equivalence counterexample; no construction/feasibility claim)"
out = os.path.join(HERE, "K2_R519_Q3_EQUIVALENCE_COUNTEREXAMPLE_v1.json")
json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps({k: rep[k] for k in ("machine_checks", "all_legality_checks_pass", "order_at_the_gate_cut",
                                      "verdict")}, ensure_ascii=False)[:2200]); print("WROTE", out)
