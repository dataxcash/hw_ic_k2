#!/usr/bin/env python3
"""K2 · R523 —— 机核反例：HANDOFF-K2-522 §0「字面版形态 C」**不保真**（只读 · Solve() 0 次）。

字面版：竖向族断面 = 院列 (col 60, 行 38..57) 与 墙洞行 (col 114, 行 7..28)，rank = 行，
         断言「两线 rank 序翻转 ⇒ 区间 x∈(x60,x114) 内至少一根有过孔弧」。
反例：两根线**零过孔**、**全程 In5**、**逐层声明集互斥（合法）**，却在 col 60 处 a 在北、在 col 114(墙洞行) 处 a 在南
⇒ 序翻转。⇒ 该断言**非被蕴含** ⇒ 其 UNSAT 不可作设计级证书（同 R519 对 A/B 的结论）。
第 4 条机核（断面可用性）引 R518-Q1：三条族上每根线都有 In5 slot ⇒ 该反例在编码的 slot 结构内**可满足**。
"""
import importlib, json, math, sys, time

HERE = "."
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/fila/jqdDev_2025/ic_hw/k2/tools")
R515 = importlib.import_module("K2_R515_" + "FREETERMINALS_v1")
P, X0, Y0, NY, NX, NID = R515.P, R515.X0, R515.Y0, R515.NY, R515.NX, R515.NID
XY = R515.XY


def node(i, j):
    return (X0 + i * P, Y0 + j * P)


def poly(offsets):
    """offsets = [(col,row), ...] ⇒ 格点折线"""
    return [node(i, j) for (i, j) in offsets]


def segs(pl):
    return [((pl[k][0], pl[k][1]), (pl[k + 1][0], pl[k + 1][1])) for k in range(len(pl) - 1)]


def claim_of_poly(pl, cache):
    s = set()
    for (a, b) in segs(pl):
        key = (round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3))
        got = cache.get(key)
        if got is None:
            got = R515.claim_seg(a[0], a[1], b[0], b[1])
            cache[key] = got
        s |= got
    return s


def seg_seg_min(A, B):
    """精确段-段最小距离（端点-段 4 项）"""
    def pt_seg(p, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        if L2 <= 0:
            return math.dist(p, a)
        t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2
        t = max(0.0, min(1.0, t))
        return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)
    return min(pt_seg(A[0], B[0], B[1]), pt_seg(A[1], B[0], B[1]),
               pt_seg(B[0], A[0], A[1]), pt_seg(B[1], A[0], A[1]))


# ---- 反例几何（格点；锚点即折线端点）----
# a：南带贴北(行 41) → 在 col 120 俯冲到焊盘场南侧(行 7) → 向西穿 col 114(行 7, 墙洞行)
la = poly([(5, 34), (5, 41), (120, 41), (120, 7), (100, 7)])
# b：南带贴南(行 38) → 在 col 118 俯冲到焊盘场北侧(行 25) → 向西穿 col 114(行 25, 墙洞行)
lb = poly([(10, 34), (10, 38), (118, 38), (118, 25), (100, 25)])

cache = {}
res = {"artifact": "k2_r523_literal_formc_counterexample_v1",
       "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "authority": "HANDOFF-K2-522 sec.0 (implement form C) + its own 'ning qian wu lan' clause; "
                    "#K2-189 sec.4 step-1 (a lever whose solution set differs from the design may not be "
                    "used for any design-level UNSAT conclusion)",
       "solve_calls": 0, "target": "HANDOFF literal form C: yard rows (col 60, rows 38..57) vs wall-gap rows "
                                   "(col 114, rows 7,11,12,13,15,24,25,28), rank = row",
       "a_polyline": la, "b_polyline": lb,
       "a_route": "A-anchor near comb (col 5,row 34) -> north -> belt row 41 -> east -> descend col 120 -> "
                  "field row 7 -> west across col 114 (wall-gap row 7) -> B-anchor",
       "b_route": "A-anchor near comb (col 10,row 34) -> north -> belt row 38 -> east -> descend col 118 -> "
                  "field row 25 -> west across col 114 (wall-gap row 25) -> B-anchor"}
ca = claim_of_poly(la, cache); cb = claim_of_poly(lb, cache)
inter = sorted(ca & cb)
mind = min(seg_seg_min(A, B) for A in segs(la) for B in segs(lb))
res["machine_checks"] = {
    "declaration_set_nodes_a": len(ca), "declaration_set_nodes_b": len(cb),
    "declaration_set_intersection": len(inter), "intersection_first": inter[:8],
    "declaration_sets_disjoint": len(inter) == 0,
    "min_true_seg_seg_distance_mm": round(mind, 6), "required_P_mm": P,
    "declaration_rule_pass": len(inter) == 0 and mind >= P - 1e-9,
    "vias": 0, "layers_used": ["In5.Cu only"],
}
GAPS = [7, 11, 12, 13, 15, 24, 25, 28]
YARD = list(range(38, 58))
xc60 = X0 + 60 * P
xc114 = X0 + 114 * P
inv = []  # 两个断面各自只收「在册行范围内」的横穿
sec_defs = [("col 60 (yard, rows 38..57)", xc60, YARD, "v"),
            ("col 114 (wall-gap rows)", xc114, GAPS, "v")]
hits_by = {}
for (label, xc, rows_ok, kind) in sec_defs:
    hits = {"a": [], "b": []}
    for nm, pl in (("a", la), ("b", lb)):
        for k in range(len(pl) - 1):
            (x1, y1), (x2, y2) = pl[k], pl[k + 1]
            if abs(y1 - y2) < 1e-12 and ((x1 < xc < x2) or (x2 < xc < x1)):
                r = round((y1 - Y0) / P, 2)
                if r in [float(v) for v in rows_ok]:
                    hits[nm].append(r)
    inv.append({"section": label, "crossings_in_section_rows": hits})
    hits_by[label] = hits
res["order_at_sections"] = inv
ra = inv[0]["crossings_in_section_rows"]["a"][0]; rb = inv[0]["crossings_in_section_rows"]["b"][0]
qa = inv[1]["crossings_in_section_rows"]["a"][0]; qb = inv[1]["crossings_in_section_rows"]["b"][0]
res["rank_inversion"] = {"col60_rank": {"a": ra, "b": rb}, "col114_gap_rank": {"a": qa, "b": qb},
                         "sign_at_col60": (ra > rb) - (ra < rb), "sign_at_col114": (qa > qb) - (qa < qb),
                         "inverted": ((ra - rb) * (qa - qb)) < 0,
                         "via_arcs_in_interval_x60_x114": 0}
res["verdict"] = ("NON-IMPLIED => the literal form is NOT faithful (solution set proper subset of the design): "
                  "a legal, zero-via, all-In5 pair realises a rank inversion between the yard rows and the "
                  "wall-gap rows => per #K2-189 sec.4 its UNSAT may NOT be used for any design-level conclusion; "
                  "per HANDOFF sec.0 ('ning qian wu lan') that interval definition must be dropped/corrected")
res["correction_used"] = ("R523 uses instead the corridor-adjacent, same-strip sections: V = col 60 <-> col 114 "
                          "(rank = row, interval x in (x60,x114)), H = row 36 (southbound gate) <-> row 30 "
                          "(pad-field entry row, rank = col, interval y in (y30,y36)); see K2_R523_PARITY_FORMC_v1.py")
res["boundaries"] = ("read-only geometry + registered declaration predicate; Solve() 0; no model/parameter/"
                     "board/SPEC/tools/criteria change; no WORKER; no .omo/supervision writes")
res["buildability"] = "NOT-APPLICABLE (fidelity counterexample; no construction/feasibility claim; nothing moved)"
json.dump(res, open("K2_R523_LITERAL_FORMC_COUNTEREXAMPLE_v1.json", "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps({k: res[k] for k in ("machine_checks", "order_at_sections", "rank_inversion", "verdict")},
                 ensure_ascii=False, indent=1))
print("WROTE K2_R523_LITERAL_FORMC_COUNTEREXAMPLE_v1.json")
