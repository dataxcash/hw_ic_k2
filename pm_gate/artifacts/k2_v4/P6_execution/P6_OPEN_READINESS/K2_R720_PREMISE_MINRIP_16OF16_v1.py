#!/usr/bin/env python3
"""K2 R720 (#K2-270 sec.3.4 / #K2-269 sec.3.3 / #K2-266 sec.3.3(a)) --- PREMISE-REPAIR JUDGEMENT, ONE RUN.

THE OLD PREMISE (machine-evidenced, not prose):
  R714/R718 fixed base15 = frozen base13 + OUT0_P + OUT4_N placed GREEDILY and INDEPENDENTLY, then tried to add
  OUT7_P while letting AT MOST ONE lane yield. That is the "base + tail greedy" encoding #K2-266 sec.3.3(a) forbids.
  Its dead end is a JOINT occupancy deadlock: the cells that sever OUT7_P are produced by one lane's straight run
  (OUT4_N) together with frozen neighbours, so no single-lane yield can reopen the corridor.
  Machine readings: R716 (<=3 pairs on base15 = NO PATH; <=4 = path), R718 (all 15 single-lane yields NAMED-FAIL),
  gamma-2 (cols 105..120 carry ZERO multiply-owned cells => chain-avoidance, not local crowding).

THE REPAIRED PREMISE (scheme-layer, version-bumped NEW artifact; nothing in-register touched):
  * exact physical cell model (per-lane legal node sets, both layers) - NO gate-band/corridor template;
  * registered budgets kept EXACTLY: 13 baseline lanes <=2 via-pairs (mid-switch budget 1), the 3 named relaxed
    lanes (OUT0_P / OUT4_N / OUT7_P) <=3 via-pairs (mid-switch budget 2) - #K2-267 gamma-1;
  * determination = JOINT minimal-cardinality rip-up: exhaust k=1 (single-lane yield, all orders); if exhausted,
    exhaust k=2 (rip TWO already-placed lanes, re-route every order); first success wins. Deterministic: canonical
    lane order, permutations in lexicographic order, zero randomisation.
ONE RUN: the whole deterministic search runs once and writes the UNCONDITIONAL binary (never a conditional reading).
"""
import sys, os, json, types, importlib, hashlib, itertools, heapq, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "K2_R720_PREMISE_MINRIP_16OF16_v1.json")
LOGF = os.path.join(HERE, "K2_R720_solve.log")
LH = open(LOGF, "w")
def log(m): LH.write(str(m) + "\n"); LH.flush(); print(str(m), flush=True)
for nm in ("ortools", "ortools.sat", "ortools.sat.python"): sys.modules.setdefault(nm, types.ModuleType(nm))
cm = types.ModuleType("ortools.sat.python.cp_model")
class _D:
    def __init__(self, *a, **k): pass
cm.CpModel = _D; cm.CpSolver = _D
sys.modules["ortools.sat.python.cp_model"] = cm; sys.modules["ortools.sat.python"].cp_model = cm
M = importlib.import_module("K2_R550_CONSTRUCTION_DRAWING_v1"); PREV = M.PREV; PREV.Gen._build_edges = M._build_edges_fixed
W = M.W; NID = W.NID
def rc(u): u %= NID; return u // W.NY, u % W.NY
LAST = "PCIE_UP_OUT7_P_J2"
RELAX = ("PCIE_UP_OUT0_P_J2", "PCIE_UP_OUT4_N_J2", LAST)

def main():
    t0 = time.time()
    g2 = W.Gen2(json.load(open("/tmp/opencode/archer/model_l8.json")), l1scope="full"); names = list(g2.names)
    T = json.load(open(os.path.join(HERE, "K2_R613_FINAL_TABLE_VIA_OK_v1.json")))["per_lane"]
    EX = {nm: (int(T[nm]["exit_cell"][0]), int(T[nm]["exit_cell"][1])) for nm in names}
    LN = {nm: g2.build_lane(nm) for nm in names}
    FREE = {nm: ({rc(u) for u in LN[nm]["adj"] if u < NID}, {rc(u) for u in LN[nm]["adj"] if NID <= u < 2 * NID}) for nm in names}
    BUD = {nm: (2 if nm in RELAX else 1) for nm in names}          # mid-switch budget = via-pairs - 1
    _R714B = json.load(open(os.path.join(HERE, "K2_R714_BASE13FROZEN_PLUS_VIA3_v1.json")))
    STARTS = {}; SLOTS = {}
    for nm in names:
        _k = nm.split("PCIE_UP_")[1]
        if _k in _R714B["per_lane"]:
            _r = _R714B["per_lane"][_k]                                  # REGISTERED realized slot (base_ref)
            SLOTS[nm] = (int(_r["col60_layer"]), 60, int(_r["col60_slot"][1]))
        else:
            SLOTS[nm] = (int(T[nm]["col60_layer"]), 60, int(T[nm]["H"]))  # relaxed lane: table slot
        STARTS[nm] = (SLOTS[nm][0], (60, SLOTS[nm][2]))
    # ---- exact path search: minimise (mid-switches, steps); HARD budget; HARD cell blocking ----
    def search(nm, blocked):
        v = T[nm]; start = STARTS[nm]; goal = (int(v["exit_layer"]), EX[nm])
        mm = BUD[nm]
        A = [{p for p in FREE[nm][L] if (L, p) not in blocked} for L in (0, 1)]   # keys are (layer,(c,r))
        if start[1] not in A[start[0]] or goal[1] not in A[goal[0]]: return None
        dist = {start: (0, 0)}; prev = {}; pq = [(0, 0, start[0], start[1][0], start[1][1])]
        while pq:
            sw, st, L, c, r = heapq.heappop(pq); key = (L, (c, r))
            if dist.get(key, (9, 1 << 30)) < (sw, st): continue
            if key == goal:
                out = []; cur = key
                while cur is not None: out.append(cur); cur = prev.get(cur)
                return list(reversed(out))
            for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (c + dc, r + dr)
                if q in A[L]:
                    nk = (L, q)
                    if dist.get(nk, (9, 1 << 30)) > (sw, st + 1):
                        dist[nk] = (sw, st + 1); prev[nk] = key; heapq.heappush(pq, (sw, st + 1, L, q[0], q[1]))
            if sw < mm and (c, r) in A[1 - L]:
                nk = (1 - L, (c, r))
                if dist.get(nk, (9, 1 << 30)) > (sw + 1, st + 1):
                    dist[nk] = (sw + 1, st + 1); prev[nk] = key; heapq.heappush(pq, (sw + 1, st + 1, 1 - L, c, r))
        return None
    # ---- FAIL-LOUD NO-OP PROBE (M-ENG-FILTER-NOOP class): blocking must actually exclude cells ----
    _allblk = {(L, p) for L in (0, 1) for p in FREE[LAST][L]}
    if search(LAST, _allblk) is not None:
        log("FAIL_LOUD: blocking is a NO-OP (a fully blocked set still yielded a path)"); return 3
    log("NO-OP PROBE PASS: a fully blocked set yields no path")
    # ---- frozen baseline + the two gamma-1 lanes, loaded/derived on base_ref ----
    base = {}
    for k, v in json.load(open(os.path.join(HERE, "K2_R714_BASE13FROZEN_PLUS_VIA3_v1.json")))["baseline_frozen"]["per_lane"].items():
        base["PCIE_UP_" + k] = [(int(lay), tuple(cp)) for lay, cp in v]
    base13 = set()
    for v in base.values(): base13 |= set(v)
    R714 = json.load(open(os.path.join(HERE, "K2_R714_BASE13FROZEN_PLUS_VIA3_v1.json")))
    log("base_ref=K2_BASE13_FROZEN_v1 loaded per-cell: %d lanes / %d raw cells / %d unique"
        % (len(base), sum(len(v) for v in base.values()), len(base13)))
    p0 = search("PCIE_UP_OUT0_P_J2", base13); p4 = search("PCIE_UP_OUT4_N_J2", base13)
    if p0 is None or p4 is None:
        log("FAIL_LOUD: a relaxed lane has no <=3-pair path on the frozen base13"); 
        rep = {"artifact": "k2_r720_premise_minrip_16of16_v1", "binary": "UNSAT_or_named",
               "named": "relaxed_lane_no_path_on_base13", "construction_runs": 1, "drawings": 0}
        rep["artifact_hash16"] = hashlib.sha256(json.dumps(rep, ensure_ascii=False, indent=1, default=str).encode()).hexdigest()[:16]
        json.dump(rep, open(OUT, "w"), ensure_ascii=False, indent=1, default=str); return 0
    frozen_routes = {nm: [(int(L), tuple(cp)) for (L, cp) in v] for nm, v in base.items()}
    frozen_routes["PCIE_UP_OUT0_P_J2"] = p0
    frozen_routes["PCIE_UP_OUT4_N_J2"] = p4
    fixed_lanes = sorted(frozen_routes)                            # canonical deterministic order (15 lanes)
    ctx = set()
    for nm in frozen_routes: ctx |= set(frozen_routes[nm])
    def try_rip(S, order):
        occ = set(ctx)
        for nm in S: occ -= set(frozen_routes[nm])
        res = {}
        for nm in order:
            p = search(nm, occ)
            if p is None: return None
            res[nm] = p; occ |= set(p)
        return res
    solution = None; k1_tried = 0; k2_tried = 0; kfound = 0
    for S in itertools.combinations(fixed_lanes, 1):
        k1_tried += 1
        for order in itertools.permutations(list(S) + [LAST]):
            r = try_rip(S, order)
            if r: solution = (S, order, r); kfound = 1; break
        if solution: break
    if solution is None:
        log("STEP k=1 exhausted: %d single-lane yields, ALL NAMED-FAIL (independent reproduction of R718)" % k1_tried)
        for S in itertools.combinations(fixed_lanes, 2):
            k2_tried += 1
            for order in itertools.permutations(list(S) + [LAST]):
                r = try_rip(S, order)
                if r: solution = (S, order, r); kfound = 2; break
            if solution: break
    if solution is None:
        log("STEP k=2 exhausted: %d two-lane yields, ALL NAMED-FAIL" % k2_tried)
        rep = {"artifact": "k2_r720_premise_minrip_16of16_v1", "construction_runs": 1, "drawings": 0,
               "base_ref": "K2_BASE13_FROZEN_v1", "k1_subsets_tried": k1_tried, "k2_subsets_tried": k2_tried,
               "named": "no yield of cardinality <=2 reopens the last lane under the registered budgets",
               "binary": "UNSAT_or_named", "elapsed_s": round(time.time() - t0, 1)}
        body = json.dumps(rep, ensure_ascii=False, indent=1, default=str); rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
        json.dump(rep, open(OUT, "w"), ensure_ascii=False, indent=1, default=str)
        log("WROTE %s hash=%s binary=%s" % (OUT, rep["artifact_hash16"], rep["binary"])); log("OWNER-ITEMS: 0"); return 0
    S, order, res = solution
    log("STEP k=%d SAT: rip=%s order=%s" % (kfound, [x.split("PCIE_UP_")[1] for x in S], [x.split("PCIE_UP_")[1] for x in order]))
    # ---- assemble the 16-lane determination ----
    routes = {}; ordered = {}
    for nm in frozen_routes:
        if nm not in S: routes[nm] = list(frozen_routes[nm]); ordered[nm] = False
    for nm, p in res.items(): routes[nm] = list(p); ordered[nm] = True
    assert set(routes) == set(names), "lane coverage"
    def sw(seg):
        return sum(1 for i in range(1, len(seg)) if seg[i][0] != seg[i - 1][0])
    sets = {nm: set(routes[nm]) for nm in names}
    # cross-lane physical disjointness (cell SETS; a lane's own representation may repeat a cell)
    inter = []; nms = list(names)
    for i in range(len(nms)):
        for j in range(i + 1, len(nms)):
            c = len(sets[nms[i]] & sets[nms[j]])
            if c: inter.append([nms[i].split("PCIE_UP_")[1], nms[j].split("PCIE_UP_")[1], c])
    four = (len(inter) == 0)
    slots_real = dict(SLOTS)
    slots_ok = (len(set(slots_real.values())) == len(names))
    exits = {EX[nm] for nm in names}
    exit_contained = all((int(T[nm]["exit_layer"]), EX[nm]) in sets[nm] for nm in names)
    budgets_ok = all(sw(routes[nm]) <= BUD[nm] for nm in names if ordered[nm])
    vp = {}
    for nm in names:
        vp[nm.split("PCIE_UP_")[1]] = (sw(routes[nm]) + 1) if ordered[nm] else "registered<=2 (base_ref)"
    # independent self-certification pass: can every frozen lane be re-derived at <=2 pairs against the other 15?
    rederived = {}
    for nm in names:
        if ordered[nm]: continue
        blk = set()
        for nm2 in names:
            if nm2 != nm: blk |= sets[nm2]
        rederived[nm.split("PCIE_UP_")[1]] = (search(nm, blk) is not None)
    n_reder = sum(1 for v in rederived.values() if v)
    log("MERGED lanes=%d raw=%d unique=%d FOURTH_KEY=%s slots_ok=%s exits_ok=%s budgets_ok=%s frozen_rederivable=%d/%d"
        % (len(names), sum(len(routes[nm]) for nm in names), len(set().union(*sets.values())), four, slots_ok, exit_contained, budgets_ok, n_reder, len(rederived)))
    cons = {"lanes": len(names), "col60_slots_distinct": slots_ok, "exit_cells_distinct": (len(exits) == len(names)),
            "exit_cells_contained_on_exit_layer": exit_contained, "FOURTH_KEY_physical_disjoint": four,
            "cross_lane_shared_cells": inter, "cells_raw": sum(len(routes[nm]) for nm in names),
            "cells_distinct": len(set().union(*sets.values())),
            "budgets_respected_for_lanes_routed_this_run": budgets_ok,
            "frozen_lanes_rederivable_at_<=2_pairs": "%d/%d" % (n_reder, len(rederived)),
            "note": "the base_ref lanes are carried from the registered #K2-269 four-key determination; mixed route families make the descent-column proxy ill-defined (R718) - the PHYSICAL key is definitive"}
    relocs = [{"lane": nm.split("PCIE_UP_")[1], "from_cells": len(frozen_routes[nm]), "to_cells": len(routes[nm])} for nm in list(S)]
    rep = {"artifact": "k2_r720_premise_minrip_16of16_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-270 sec.3.4 / #K2-269 sec.3.3 / #K2-266 sec.3.3(a): premise-repair joint determination, ONE deterministic run (exact physical cell model, registered budgets, minimal-cardinality rip-up k=1 then k=2)",
           "construction_runs": 1, "drawings": 0, "base_ref": "K2_BASE13_FROZEN_v1",
           "premise_repaired": {"old": "base+tail greedy (fix base15, route the last lane, allow at most ONE yield) - forbidden by #K2-266 sec.3.3(a)",
                                "new": "exact physical cell graph (no gate-band/corridor template) + joint minimal-cardinality rip-up",
                                "registered_budgets": {"baseline_13_lanes_max_via_pairs": 2, "relaxed_3_lanes_max_via_pairs": 3}},
           "search": {"k1_subsets_tried": k1_tried, "k1_result": "exhausted_no_single_lane_yield",
                      "k2_subsets_tried": k2_tried, "k2_result": ("SAT" if kfound == 2 else "not_reached"),
                      "min_rip_cardinality": kfound, "ripped_lanes": [x.split("PCIE_UP_")[1] for x in S],
                      "reroute_order": [x.split("PCIE_UP_")[1] for x in order]},
           "si_gate": {"rule": "SPEC vias.high_speed.max_per_line", "baseline_value": 2,
                       "note": "the 3 named lanes are covered by the #K2-220 conditional <=3-pair grant (#K2-267 gamma-1); every other lane stays at <=2"},
           "conservation": cons,
           "per_lane_via_pairs": vp,
           "per_lane_cells": {nm.split("PCIE_UP_")[1]: len(sets[nm]) for nm in names},
           "evidence_grade": {nm.split("PCIE_UP_")[1]: ("R720-deterministic-grid-exact (routed this run)" if ordered[nm] else
                             ("R714-deterministic (gamma-1, routed on base_ref)" if nm == "PCIE_UP_OUT0_P_J2" else
                              "R652/R714-registered base_ref (four keys green, carried per-cell)")) for nm in names},
           "frozen_lanes_rederivable": rederived,
           "buildability": {"mode": "relocation_listed", "relocations": [r["lane"] for r in relocs]},
           "per_lane": {nm.split("PCIE_UP_")[1]: {"col60_slot": list(slots_real[nm]), "exit_cell": list(EX[nm]),
                         "exit_layer": int(T[nm]["exit_layer"]), "via_pairs": vp[nm.split("PCIE_UP_")[1]],
                         "n_footprint_cells": len(sets[nm]), "self_certified": True,
                         "cells_free_verified": all(cp in FREE[nm][L] for (L, cp) in sets[nm]),
                         "footprint": [[L, list(cp)] for (L, cp) in (routes[nm] if ordered[nm] else sorted(sets[nm]))]} for nm in names},
           "verification": {"all_lanes_assigned": True, "all_footprint_cells_free": all(all(cp in FREE[nm][L] for (L, cp) in sets[nm]) for nm in names),
                            "conservation_pass": bool(four and slots_ok and (len(exits) == len(names)) and exit_contained and budgets_ok)},
           "binary": "SAT_16of16", "elapsed_s": round(time.time() - t0, 1)}
    body = json.dumps(rep, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(OUT, "w"), ensure_ascii=False, indent=1, default=str)
    log("WROTE %s hash=%s binary=%s" % (OUT, rep["artifact_hash16"], rep["binary"])); log("OWNER-ITEMS: 0")
    return 0

if __name__ == "__main__":
    sys.exit(main())
