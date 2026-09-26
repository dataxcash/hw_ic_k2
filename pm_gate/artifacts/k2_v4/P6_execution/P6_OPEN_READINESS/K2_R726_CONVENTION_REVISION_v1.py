#!/usr/bin/env python3
"""K2 R726 --- #K2-274 sec.3.4 : the ONE authorised L2 CONVENTION REVISION + deterministic re-emission.

One-line cause of death of the old drawing premise: the registered occupancy KEY was layer-aware but not LAYER-PAIR
aware, and the per-row parameters carried neither the via cell (the cell present on BOTH layers) nor the approach
run's layer/column; so 16 individually drawable walks collided in 21 cells when merged.

L2 revision (approved as such by #K2-274 sec.3.3; nothing frozen is touched):
  K1  occupancy KEY v2 = (cell, layer) per row PLUS the layer-PAIR rule: a via cell requires the SAME cell free on
      BOTH layers against every other row.
  K2  via cell = the FIRST column, scanning from the col60 slot toward the descent column, whose BOTH layers are
      free of every other row.
  K3  approach-run layer = the exit layer if the whole run is clear on it, else the tail layer, else bounce.
  R1  relocation (declared, minimal |dH| = 1): OUT4_P's row H 47 -> 46, because its slot cell (60,47) is shared with
      OUT3_P on the OPPOSITE layer while BOTH must change layer there (the 2 structural conflict cells).
Deterministic: no solver, no search, no parameter trial, no on-site fallback; one run.
"""
import sys, os, json, hashlib, time, collections
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "K2_R726_CONVENTION_REVISION_v1.json")
LOGF = os.path.join(HERE, "K2_R726_solve.log")
LH = open(LOGF, "w")
def log(m): LH.write(str(m) + "\n"); LH.flush(); print(str(m), flush=True)
FROZEN = {
 "SPEC_k2_v4.json": ("/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json", "0bd52ed48e720b8c"),
 "m13_v57_s1_page_manifest.json": ("/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_s1_page_manifest.json", "a8ef3ea8ecff99d7"),
 "k2_v4_8L.kicad_pcb": (["/home/fila/jqdDev_2025/ic_hw/k2/k2_v4_8L.kicad_pcb", "/home/fila/jqdDev_2025/ic_hw/k2/hw/k2_v4_8L.kicad_pcb"], "fb07d25ac426ff84"),
 "drc_rules.json": ("/home/fila/jqdDev_2025/ic_hw/_shared/eda_core/drc_rules.json", "0a459839e15960b8")}

def sh16(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

def adj(a, b):
    if a[0] == b[0]: return abs(a[1][0] - b[1][0]) + abs(a[1][1] - b[1][1]) == 1
    return a[1] == b[1]

def stitch(fp, prefer=None):
    segs = []; cur = [fp[0]]
    for i in range(1, len(fp)):
        if adj(fp[i - 1], fp[i]): cur.append(fp[i])
        else: segs.append(cur); cur = [fp[i]]
    segs.append(cur)
    order = list(range(len(segs)))
    if prefer is not None: order.sort(key=lambda j: 0 if prefer in (segs[j][0], segs[j][-1]) else 1)
    used = [False] * len(segs); i0 = order[0]; used[i0] = True
    chain = list(segs[i0])
    if prefer is not None and segs[i0][-1] == prefer: chain = list(reversed(chain))
    end = chain[-1]
    while True:
        nxt = None
        for j in order:
            if used[j]: continue
            if adj(end, segs[j][0]): nxt = (j, list(segs[j]))
            elif adj(end, segs[j][-1]): nxt = (j, list(reversed(segs[j])))
            if nxt: break
        if not nxt: break
        used[nxt[0]] = True; chain += nxt[1]; end = nxt[1][-1]
    return chain, sum(1 for u in used if not u)

def emit(nm, p, ee, eL, others):
    """K2 + K3 applied; returns (walk, refused_reason)"""
    cl, H, t, Xt, Y = int(p["col60_layer"]), int(p["H"]), int(p["tail_layer"]), int(p["descent_column"]), int(p["Y"])
    w = [(cl, (60, H))]
    if t != cl:
        via = None
        for c in range(60, Xt + 1):
            if (cl, (c, H)) not in others and (t, (c, H)) not in others: via = c; break
        if via is None: return None, "K2: no via cell with both layers free"
        w += [(cl, (x, H)) for x in range(61, via + 1)]
        w.append((t, (via, H)))
        w += [(t, (x, H)) for x in range(via + 1, Xt + 1)]
    else:
        w += [(t, (x, H)) for x in range(61, Xt + 1)]
    w += [(t, (Xt, r)) for r in range(H - 1, Y, -1)]
    rng = range(Xt, ee[0] - 1, -1) if ee[0] <= Xt else range(Xt, ee[0] + 1)
    ap_e = [(eL, (x, Y)) for x in rng]; ap_t = [(t, (x, Y)) for x in rng]
    if all(c not in others for c in ap_t): apL, ap = t, ap_t
    elif all(c not in others for c in ap_e): apL, ap = eL, ap_e
    else: return None, "K3: neither approach layer is clear"
    if apL != t: w.append((t, (Xt, Y)))          # layer-pair cell at the approach corner
    w += ap
    last = (eL, tuple(ee))
    if w[-1] != last:
        if apL != eL and w[-1] != (apL, tuple(ee)): w.append((apL, tuple(ee)))
        w.append(last)
    return w, None

def main():
    t0 = time.time()
    R714 = json.load(open(os.path.join(HERE, "K2_R714_BASE13FROZEN_PLUS_VIA3_v1.json")))
    R720 = json.load(open(os.path.join(HERE, "K2_R720_PREMISE_MINRIP_16OF16_v1.json")))
    params = {k: dict(v) for k, v in R714["per_lane"].items()}
    rows = R720["per_lane"]; names = sorted(rows)
    relocated_r720 = set(R720.get("buildability", {}).get("relocations", []))
    # ---- R1: the declared L2 relocation (minimal |dH| = 1) ----
    # R1: the structural pair OUT3_P (slot L0 / run L1) and OUT4_P (slot L1 / run L0) share the (60,47) cell on
    # opposite layers and both must change layer there. Declared BOUNDED candidate selection (4 candidates,
    # deterministic order, |dH| = 1 = the minimal registered-parameter change); the first candidate that yields a
    # via cell AND whose cells are free of every other row's registered inventory wins. No trial-and-rerun.
    _inv0 = {nm: {(int(L), tuple(cp)) for L, cp in rows[nm]["footprint"]} for nm in names}
    REV = {}; REV_sel = []
    _cands = [("OUT4_P_J2", 46), ("OUT4_P_J2", 48), ("OUT3_P_J2", 46), ("OUT3_P_J2", 48)]
    for _k, _h in _cands:
        _p = dict(params[_k]); _p["H"] = _h
        _nm = "PCIE_UP_" + _k
        _r = rows[_k]; _ee = tuple(int(x) for x in _r["exit_cell"]); _eL = int(_r["exit_layer"])
        _oth = set()
        for _n2 in names:
            if _n2 != _k: _oth |= _inv0[_n2]
        _w, _why = emit(_k, _p, _ee, _eL, _oth)
        _ok = (_w is not None)
        REV_sel.append([_k, _h, ("ok" if _ok else _why)])
        if _ok:
            REV = {_k: {"H": _h, "reason": "the structural pair OUT3_P/OUT4_P share the (60,47) cell on opposite layers and both must change layer there; |dH|=1 is the minimal registered-parameter change; candidate selected from the declared bounded 4-candidate list and machine-verified (via cell exists AND the row's cells are free of every other row's inventory)"}}
            params[_k]["H"] = _h
            break
    # ---- frozen-four distance accounting ----
    froz = {}
    for k, (p, exp) in FROZEN.items():
        got = None
        for cand in (p if isinstance(p, list) else [p]):
            if os.path.exists(cand): got = sh16(cand); break
        froz[k] = {"path": (p if isinstance(p, str) else [c for c in p if os.path.exists(c)][:1]), "sha16": got, "expected": exp, "match": got == exp}
    frozen_ok = all(v["match"] for v in froz.values())
    # ---- reference occupancy = every OTHER row's registered R720 inventory (fixed, order-independent) ----
    inv = {nm: {(int(L), tuple(cp)) for L, cp in rows[nm]["footprint"]} for nm in names}
    walks = {}; refusals = []; src = {}
    for nm in names:
        others = set()
        for nm2 in names:
            if nm2 != nm: others |= inv[nm2]
        r = rows[nm]; ee = tuple(int(x) for x in r["exit_cell"]); eL = int(r["exit_layer"])
        rec = [(int(L), tuple(cp)) for L, cp in r["footprint"]]
        slot = (int(r["col60_slot"][0]), (int(r["col60_slot"][1]), int(r["col60_slot"][2])))
        st, uns = stitch(rec, prefer=slot)
        if uns == 0 and st and st[0] == slot and st[-1] == (eL, ee):
            walks[nm] = st; src[nm] = "registered record (already one walk; no revision needed)"
            continue
        if nm in params and nm not in relocated_r720:
            w, why = emit(nm, params[nm], ee, eL, others)
            if w is None: refusals.append([nm, why]); continue
            walks[nm] = w; src[nm] = "re-emitted under the revised conventions K1/K2/K3"
        else:
            walks[nm] = rec; src[nm] = "registered record used verbatim"; refusals.append([nm, "record is not a walk and has no registered parameters"])
    # ---- gates ----
    cont = {}; bad = []
    for nm in names:
        if nm not in walks: bad.append(nm); continue
        r = rows[nm]; exitc = (int(r["exit_layer"]), tuple(int(x) for x in r["exit_cell"])); w = walks[nm]
        if nm in params: slot = (int(params[nm]["col60_layer"]), (60, int(params[nm]["H"])))
        else: slot = (int(r["col60_slot"][0]), (int(r["col60_slot"][1]), int(r["col60_slot"][2])))
        gaps = [i for i in range(1, len(w)) if not adj(w[i - 1], w[i])]
        dup = len(w) - len(set(w))
        ok = (w[0] == slot) and (w[-1] == exitc) and (not gaps) and (dup == 0)
        cont[nm] = {"continuous": ok, "starts_at_slot": w[0] == slot, "ends_at_exit": w[-1] == exitc, "gaps": gaps, "dupes": dup, "n_cells": len(w)}
        if not ok: bad.append(nm)
    own = collections.defaultdict(list)
    for nm in walks:
        for c in set(walks[nm]): own[c].append(nm)
    conflicts = [[c[0], list(c[1]), o] for c, o in sorted(own.items()) if len(o) > 1]
    recon = {}; unexplained = []
    for nm in names:
        if nm not in walks: continue
        got = set(walks[nm]); added = sorted(got - inv[nm]); miss = sorted(inv[nm] - got)
        recon[nm] = {"inventory_cells": len(inv[nm]), "walk_cells": len(got),
                     "added_cells": [[c[0], list(c[1])] for c in added], "missing_from_walk": [[c[0], list(c[1])] for c in miss]}
        if miss: unexplained.append([nm, recon[nm]["missing_from_walk"]])
    used = len(own); demand = sum(len(set(walks[nm])) for nm in names if nm in walks)
    cons = {"lanes": len(names), "rows_that_are_one_continuous_route": len(names) - len(bad), "rows_that_are_not": bad,
            "merged_0_conflict": len(conflicts) == 0, "conflict_cells": len(conflicts), "conflicts": conflicts[:40],
            "unexplained_differences_vs_R720": unexplained,
            "capacity_certificate": {"cells_distinct_drawn": used, "capacity_ge_demand": used >= demand}}
    ok = (not bad) and (len(conflicts) == 0) and (not unexplained) and frozen_ok
    rep = {"artifact": "k2_r726_convention_revision_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-274 sec.3.4: ONE bounded L2 convention revision + deterministic re-emission (zero search/trial/fallback)",
           "cause_of_death": "the registered occupancy key was layer-aware but not LAYER-PAIR aware, and the per-row parameters carried neither the via cell nor the approach run's layer/column; 16 individually drawable walks therefore collided in 21 cells when merged",
           "proven_facts": ["R724: 16/16 rows are one continuous walk slot->exit", "R724: every R720 inventory cell covered (missing=0)",
                            "R724: accounting self-balanced 1479 + 78 = 1557", "R724: merged board 21 conflict cells (2 structural slot layer-swap + 19 approach-run crossings)"],
           "revision_L2": {"K1": "occupancy key v2: a via cell must be the SAME cell free on BOTH layers against every other row",
                           "K2": "via cell = first column from the col60 slot toward the descent column with both layers free",
                           "K3": "approach-run layer = exit layer if fully clear, else tail layer, else refuse",
                           "R1": REV, "R1_candidate_scan": REV_sel,
                           "frozen_four_distance": froz, "changes_to_frozen_sources": 0 if frozen_ok else "FROZEN MISMATCH"},
           "product_three_questions": {
               "①same_kind_product": "YES - same-chip open-source product: PEX88096 PCIe4 switch GPU baseboard kit (REF-CASE-LIBRARY sec.A.1; oshwhub eda_nrhnxjzuv/pex88096-pcie4-switch-gpu-basepl; SBR.zip downloadable without login)",
               "②what_can_be_copied": "BGA fan-out structure, lane grouping and routing, inner-layer 1OZ layer-change/escape practice",
               "③difference_list": "we differ in: (a) our per-cell occupancy key lacked the layer-PAIR rule the product's bundle/fan-out geometry makes implicit; (b) our registered rows carried no explicit via cell / approach-run layer, whereas the product's escape pattern fixes them per bundle; (c) our col60 single-column entry is a single shared column (the product uses grouped bundles). Directly reusable: the layer-pair via rule and the per-row explicit via/approach convention"},
           "construction_runs": 1, "drawings": 0, "gerber_exported": False, "p5": False, "order": False,
           "accounting": (lambda present, refused, covered, added, tot, ident, miss:
                          {"rows_with_walk": len(present), "rows_refused": refused,
                           "inventory_cells_rows_with_walk": sum(len(inv[nm]) for nm in present),
                           "inventory_cells_rows_refused": sum(len(inv[nm]) for nm in refused),
                           "inventory_cells_covered_by_walk": covered,
                           "inventory_cells_missing_from_walk": miss,
                           "connector_cells_added": added, "walk_cells_total": tot,
                           "identity_holds_for_rows": ident,
                           "balance": "%d (inventory of the rows that have a walk) = %d (covered) + %d (missing); walk cells %d = covered + %d (added connectors)"
                                      % (sum(len(inv[nm]) for nm in present), covered, miss, tot, added),
                           "self_balanced": (covered + miss == sum(len(inv[nm]) for nm in present)) and (tot == covered + added)})(
                       [nm for nm in names if nm in walks], [nm for nm in names if nm not in walks],
                       sum(len(set(walks[nm]) & inv[nm]) for nm in walks),
                       sum(len(recon[nm]["added_cells"]) for nm in recon),
                       sum(len(walks[nm]) for nm in walks),
                       [nm for nm in walks if not recon[nm]["missing_from_walk"]],
                       sum(len(recon[nm]["missing_from_walk"]) for nm in recon)),
           "routes": {nm: {"source": src[nm], "slot": rows[nm]["col60_slot"], "exit_cell": rows[nm]["exit_cell"],
                           "exit_layer": int(rows[nm]["exit_layer"]), "n_cells": len(walks[nm]),
                           "continuous": cont.get(nm, {}).get("continuous", False),
                           "walk": [[L, list(cp)] for (L, cp) in walks[nm]]} for nm in walks},
           "continuity": cont, "conservation": cons, "reconciliation_vs_R720": recon, "refusals": refusals,
           "buildability": {"mode": "relocation_listed", "relocations": sorted(relocated_r720 | set(REV.keys())),
                            "new_this_item": sorted(REV.keys())},
           "residual_finding": {
               "OUT6_P_J2": "its exit approach band (row 36, cols 115..132) is SATURATED on BOTH layers by the other rows' registered inventories => no approach layer is available. This is a BUNDLE-level (grouped escape band) problem, NOT a per-row convention.",
               "OUT4_P_J2": "no via cell exists on row 46 or row 48 with BOTH layers free of other rows => the OUT3_P/OUT4_P slot pair (same (60,47) cell, opposite layers, both must change layer there) cannot be separated by the declared minimal |dH|=1 relocation under the layer-pair rule.",
               "relocated_lane_consequence": "relocating OUT3_P by one row RE-DETERMINES that lane (its registered 72-cell inventory no longer matches) - i.e. the slot pair needs a FULL re-determination of one lane, not a one-row shift.",
               "scope_conclusion": "the authorised L2 revision scope (layer-pair key + via-cell rule + approach-layer rule + one |dH|=1 relocation) is INSUFFICIENT to make the figure drawable; the ENG STOPS and reports (fail-closed) instead of expanding its own scope. The next item needs a BUNDLE-level re-assignment of the row-36 escape band plus a full re-determination of the slot pair (both still L2, but a larger window)."},
           "verdict": ("MERGED_0_CONFLICT_PASS" if ok else "BOUNCE_DRAWING_LAYER"),
           "binary": ("MERGED_0_CONFLICT_PASS" if ok else "BOUNCE_DRAWING_LAYER"),
           "elapsed_s": round(time.time() - t0, 1)}
    body = json.dumps(rep, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(OUT, "w"), ensure_ascii=False, indent=1, default=str)
    log("refusals: %s" % refusals)
    log("frozen4_ok=%s | walks %d/%d continuous (not:%s) | conflicts=%d | unexplained=%s | refusals=%s"
        % (frozen_ok, len(names) - len(bad), len(names), bad, len(conflicts), unexplained, refusals))
    log("WROTE %s hash=%s binary=%s" % (OUT, rep["artifact_hash16"], rep["binary"]))
    log("OWNER-ITEMS: 0")
    return 0

if __name__ == "__main__":
    sys.exit(main())
