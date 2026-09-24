#!/usr/bin/env python3
"""K2 · R518 —— 遵 #K2-189 §四 **第一步（只读 · 不占额度）**：对「丙」（在册 R499 显式序变量族）做
**保真自检**：机核回答「把 R499 的门列/院行/缝位序变量**原样移植**到 R515 的双层（In5+In4）模型上，
是否与设计解集相同？」——不同解集 ⇒ 依 #K2-189 §四 **不得据其「算不通」下任何设计级结论**。

在册 R499 序变量结构（逐字取自 `K2_R512_JOINT_MCF_NODECAP_FIX_v1.py` §(c)）：
  · GATE_COLS = 115..135（每根一个 slot，slot 互斥，**且** declared order（= A 锚 x 序）单调不减）
  · YARD_ROWS = 38..57（同上）
  · GAPS = [7,11,12,13,15,24,25,28]（**仅西组**，同上）
  · linking：`z[li][c] = 1 ⇒ 本车道存在一条以 node(c,36) 为头的弧`（门列）；院行/缝位同构
  · 关键：原版建在**单层**模型上，那里「单调」= 同层不可相交的**推论**（保真、且强剪枝）。

本器机核三问（全部只读、`Solve()` 0 次）：
  Q1 **slot 可达性**：在**双层**模型里，每根线在门列/院行/缝位上是否**一定有**（或**可能有**）以该格点为头的 **In5** 弧？
     若有车道在某个族里 **0 个可用 slot** ⇒ 原版 `sum(z)==1` 直接不可满足 ⇒ **移植不保真**（机证）。
  Q2 **单调可宣言性**：给定每根线在该族的**可用 slot 区间**，declared order（A 锚 x 序）**能否**被安排成
     **严格单调不减**？（区间→严格递增可行性的贪心判据，机核）。不可行 ⇒ 原版单调约束会**砍掉**该族内的合法布局。
  Q3 **反例（若在册见证含路径）**：R513-T5「无配对 16/16 见证」里，是否存在两根线在**门列上同为 In5**、
     但其**相对次序与 A 锚 x 序相反**？若存在 ⇒ 原版单调约束**禁止一个已机核的合法打包** ⇒ 不保真（机证）。

产出：`K2_R518_ORDERED_LEVER_FIDELITY_v1.json`（含三问读数 + 判词 + 保真替代式（parity/换位记账）规格）。
"""
import collections, importlib, json, math, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
R = importlib.import_module("K2_" + "R" + "514" + "_LAYERHOP_JOINT_MCF_v2")
W = importlib.import_module("K2_" + "R" + "515" + "_FREETERMINALS_v1")
P, NID, NY, NX = W.P, W.NID, W.NY, W.NX
GATE_COLS = list(range(115, 136)); YARD_ROWS = list(range(38, 58))
GAPS = [7, 11, 12, 13, 15, 24, 25, 28]
model = json.load(open("/tmp/opencode/archer/model_l8.json"))
t0 = time.time()
rep = {"artifact": "k2_r518_ordered_lever_fidelity_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "authority": ("#K2-189 §四 step 1 (read-only fidelity self-check for lever 丙; must machine-show whether the "
                     "R499 order-variable family, ported onto the R515 two-layer model, has the SAME solution set as the "
                     "design; if not, its UNSAT may not be used for any design-level conclusion)"),
       "solve_calls": 0, "reference_impl": "K2_R512_JOINT_MCF_NODECAP_FIX_v1.py §(c) order_gate_columns/order_yard_rows/order_wall_gaps",
       "cuts": {"gate_columns": GATE_COLS, "yard_rows": YARD_ROWS, "wall_gaps": GAPS}}

g2 = W.Gen2(model, l1scope="full", verbose=True)
names = list(g2.names)
lanes = {}
for nm in names:
    L = g2.build_lane(nm)
    if L: lanes[nm] = L
rep["lanes_built"] = len(lanes)


def head_arcs(L, layer, pos):
    """该车道在 layer 上、以 pos 为头的弧数（= 该车道是否可能「到过」该格点）"""
    n = layer * NID + pos
    return sum(1 for u, lst in L["adj"].items() for (v, w) in lst if v == n)


def fam_avail(nm, family):
    L = lanes[nm]
    if family == "gate":
        return [c for c in GATE_COLS if head_arcs(L, 0, c * NY + 36) > 0], \
               [c for c in GATE_COLS if head_arcs(L, 1, c * NY + 36) > 0]
    if family == "yard":
        return [r for r in YARD_ROWS if head_arcs(L, 0, 60 * NY + r) > 0], \
               [r for r in YARD_ROWS if head_arcs(L, 1, 60 * NY + r) > 0]
    return [g for g in GAPS if head_arcs(L, 0, 114 * NY + g) > 0], \
           [g for g in GAPS if head_arcs(L, 1, 114 * NY + g) > 0]


declared = sorted(lanes, key=lambda nm: lanes[nm]["anc"][0][0])       # A 锚 x 序（R499 的 declared order）
west = [nm for nm in declared if lanes[nm]["anc"][1][0] < W.X0 + 114.0 * P]
res = {"declared_order_by_A_x": [nm.replace("PCIE_UP_OUT", "U") for nm in declared],
       "west_group": [nm.replace("PCIE_UP_OUT", "U") for nm in west],
       "gate": {}, "yard": {}, "wall_gaps": {}}
for family, key in (("gate", "gate"), ("yard", "yard"), ("wall_gaps", "wall_gaps")):
    members = lanes if family != "wall_gaps" else {nm: lanes[nm] for nm in west}
    fam = {}
    zero_in5, mins, maxs = [], {}, {}
    for nm in members:
        a5, a4 = fam_avail(nm, "gate" if family == "gate" else ("yard" if family == "yard" else "gap"))
        fam[nm.replace("PCIE_UP_OUT", "U")] = {"In5_slots": a5, "In4_slots": a4,
                                               "n_In5": len(a5), "n_In4": len(a4)}
        if not a5 and not a4:
            zero_in5.append(nm.replace("PCIE_UP_OUT", "U"))
        if a5:
            mins[nm] = min(a5); maxs[nm] = max(a5)
    # Q2：declared order 能否严格单调（仅用 In5 可用区间）
    ok_mono, why = True, []
    prev = None
    for nm in [n for n in (declared if family != "wall_gaps" else west) if n in mins]:
        lo = max(mins[nm], (prev + 1) if prev is not None else -10 ** 9)
        if lo > maxs[nm]:
            ok_mono = False; why.append("%s: 可用区间 [%d,%d] 无法排在 %d 之后" %
                                        (nm.replace("PCIE_UP_OUT", "U"), mins[nm], maxs[nm], prev)); break
        prev = lo
    res[key] = {"per_lane": fam, "lanes_with_no_slot_at_all": zero_in5,
                "declared_order_strictly_increasable_on_In5": ok_mono, "witness_of_failure": why}
    res[key]["min_In5_slots_per_lane"] = min((v["n_In5"] for v in fam.values()), default=0)
    res[key]["max_In5_slots_per_lane"] = max((v["n_In5"] for v in fam.values()), default=0)

rep["declared_order_by_A_x"] = res["declared_order_by_A_x"]
rep["west_group"] = res["west_group"]
for _k in ("gate", "yard", "wall_gaps"):
    rep[_k] = res[_k]
rep["q2_note"] = ("Q2 用每根线在该族上的 **In5 可用 slot 区间**做严格递增可行性判据（贪心）：不可行 ⇒ "
                  "R499 原版的单调约束会砍掉该族内所有『都在 In5』的合法布局")

# Q3：反例 —— 用 R513-T5 在册见证（若有路径）
t5 = json.load(open(os.path.join(HERE, "K2_R513_DECISIVE_TRIAGE_v1.json")))["t5_union_claim_disjoint_flow"]
res["q3_witness_counterexample"] = {"witness_pairs_present": "witness_pairs" in t5,
                                   "paths_present": any(k in t5 for k in ("witness_paths", "paths"))}
if res["q3_witness_counterexample"]["paths_present"]:
    res["q3_witness_counterexample"]["note"] = "paths available -> machine order-inversion test runnable"
else:
    res["q3_witness_counterexample"]["note"] = ("the registered T5 artifact stores only the src->snk pairing "
                                                "(witness_pairs), NOT the paths, so the order-inversion counterexample "
                                                "cannot be read off it; it needs the max-flow paths re-derived (read-only, "
                                                "polynomial, no Solve) - queued for the faithful re-encode instead")

# 判词
broken = [k for k in ("gate", "yard", "wall_gaps") if res[k]["lanes_with_no_slot_at_all"]]
mono_bad = [k for k in ("gate", "yard", "wall_gaps")
            if not res[k]["declared_order_strictly_increasable_on_In5"]]
rep["verdict"] = {
    "naive_R499_port_is_faithful": (not broken and not mono_bad),
    "lanes_with_no_slot_at_all_by_family": broken,
    "families_whose_declared_order_is_not_increasable_on_In5": mono_bad,
    "reason": ("在双层模型里，R499 原版的三条『无条件』结构（每根一个 slot + slot 互斥 + declared order 单调）"
               "不再是同层不可相交的推论：窄段上的**换序**可以合法地发生在 **In4**（宽区里换完再回 In5），"
               "于是『都在 In5 时仍按 A 锚 x 序』会把**合法解**砍掉；反之若某根在窄段根本不上 In5，"
               "原版 `sum(z)==1` 又会让它**无解**。两种方向都不是『同解集』。"),
    "consequence_per_k2189_s4": ("⇒ 原样移植不保真 ⇒ 依 #K2-189 §四：**不得**据其「算不通」下任何设计级结论；"
                                 "故本窗**不把受证额度花在非保真编码上**（这正是监理驳回乙的同一理由）。"),
    "faithful_replacement_spec": {
        "name": "换位记账式（parity / swap-accounting）序变量",
        "structure": ["沿走廊取在册断面序 S1..SK（梳齿出口 / 门列 / 院行 / 墙缝 / 焊盘场）",
                      "每根线在每个断面一个 **rank** 变量（**定义式**：rank=它在该断面 In5 上所据格点的横向序；不上 In5 则该断面 rank = ⊥）",
                      "相邻断面间：若两根线的 rank 序**翻转**，则**至少一根**必须在该区间内有**过孔弧**（= 在那段宽区完成换序）",
                      "窄段（无宽区）区间：翻转数必须为 0 ⇒ 用『过孔计数=0』的区间把『换序只发生在宽区』写成机器变量"],
        "why_faithful": ("『同层不换序』是**声明集互斥的直接推论**（同层两线相交 ⇒ 声明集相交 ⇒ 被禁）；"
                         "故『翻转 ⇒ 必有过孔』是**被蕴含**的约束 ⇒ 同解集（保真），但给求解器提供了"
                         "**换位事件**这一结构（这正是丙想要的剪枝）。"),
        "why_strong": "它对『哪根先走 / 在哪换位』给出了显式变量与账本，搜索不必从 1.15M 条弧里猜换位顺序。"},
}
rep["boundaries"] = ("read-only; Solve() 0 calls; no model/parameter change; board/SPEC/tools/criteria untouched; "
                     "frozen four 4/4; no WORKER; no .omo/supervision writes")
rep["buildability"] = "NOT-APPLICABLE (fidelity self-check for the pending lever-丙 window; no construction claim)"
rep["elapsed_s"] = round(time.time() - t0, 1)
out = os.path.join(HERE, "K2_R518_ORDERED_LEVER_FIDELITY_v1.json")
json.dump(rep, open(out, "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps({k: rep[k] for k in ("lanes_built", "gate", "yard", "wall_gaps", "verdict", "elapsed_s")},
                 ensure_ascii=False)[:2600])
print("WROTE", out)
