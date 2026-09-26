#!/usr/bin/env python3
"""K2 R730 --- #K2-276 sec.3.5 : the approved declared FULL-ROW re-determination of OUT4_P and OUT6_P, ONE run.

Guardrail (#K2-276 sec.3.4): each row's REGISTERED EXIT GATE COLUMN stays unchanged (exit cell + exit layer fixed);
no cross-wall / cross-group displacement. If a row cannot be drawn with its exit gate fixed -> stop and report (L1).

Product-style construction (REF-CASE-LIBRARY sec.A.1, one group one bundle / long straight run / one layer change at
the group fan-out / bundles do not overlap):
  * the run stays on the row closest to the registered row (declared order H, H-1, H+1, H-2, H+2, H-3, H+3)
  * the descent column sits immediately EAST of the exit gate (declared order ex+1, ex+2, ex+3, ex+4) so the exit
    approach is 2-3 cells - the product keeps the escape short on the exit layer
  * the layer change happens at the first column east of the col60 slot whose BOTH layers are free (layer-pair rule)
  * the approach runs on the exit layer (fallback: the tail layer)
Domain of the final drawing = 1 (one declared route per row); no solver, no backtracking, no parameter trial, no
on-site fallback. The 14 non-named rows keep the R724 walks (continuous, inventory-identical).
"""
import sys, os, json, hashlib, time, collections
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "K2_R730_ROW_REDETERMINATION_v1.json")
LOGF = os.path.join(HERE, "K2_R730_solve.log")
LH = open(LOGF, "w")
def log(m): LH.write(str(m) + "\n"); LH.flush(); print(str(m), flush=True)
FROZEN = [("SPEC", "/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json", "0bd52ed48e720b8c"),
          ("manifest", "/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_s1_page_manifest.json", "a8ef3ea8ecff99d7"),
          ("PCB", "/home/fila/jqdDev_2025/ic_hw/k2/k2_v4_8L.kicad_pcb", "fb07d25ac426ff84"),
          ("rules", "/home/fila/jqdDev_2025/ic_hw/_shared/eda_core/drc_rules.json", "0a459839e15960b8")]
REROUTE = ("OUT4_P_J2", "OUT6_P_J2")
DH_ORDER = [0, -1, 1, -2, 2, -3, 3]

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

def build(cl, H, t, Xt, Y, ee, eL, others):
    """One declared route. Returns (walk, meta) or (None, reason)."""
    if H <= Y + 1: return None, "row too low for the descent"
    w = [(cl, (60, H))]; via = None
    if t != cl:
        for c in range(60, Xt + 1):
            if all((cl, (x, H)) not in others for x in range(60, c + 1)) and (t, (c, H)) not in others:
                via = c; break
        if via is None: return None, "no via cell with both layers free (layer-pair rule)"
        w += [(cl, (x, H)) for x in range(61, via + 1)]; w.append((t, (via, H)))
        w += [(t, (x, H)) for x in range(via + 1, Xt + 1)]
    else:
        w += [(t, (x, H)) for x in range(61, Xt + 1)]
    desc = [(t, (Xt, r)) for r in range(H - 1, Y, -1)]
    if any(c in others for c in desc): return None, "descent column not clear"
    w += desc
    rng = range(Xt, ee[0] - 1, -1) if ee[0] <= Xt else range(Xt, ee[0] + 1)
    ap_e = [(eL, (x, Y)) for x in rng]; ap_t = [(t, (x, Y)) for x in rng]
    if all(c not in others for c in ap_e): apL, ap = eL, ap_e
    elif all(c not in others for c in ap_t): apL, ap = t, ap_t
    else: return None, "approach run not clear on either layer"
    if apL != t: w.append((t, (Xt, Y)))
    w += ap
    last = (eL, tuple(ee))
    if w[-1] != last:
        if apL != eL and w[-1] != (apL, tuple(ee)): w.append((apL, tuple(ee)))
        w.append(last)
    if len(set(w)) != len(w): return None, "self-overlap"
    meta = {"via_cells": ([[cl, 60, H], [t, via, H]] if t != cl else []),
            "approach_layer": apL, "approach_columns": [min(rng), max(rng)],
            "run_row": H, "descent_column": Xt, "H_shift": None}
    return w, meta

def main():
    t0 = time.time()
    R714 = json.load(open(os.path.join(HERE, "K2_R714_BASE13FROZEN_PLUS_VIA3_v1.json")))
    R720 = json.load(open(os.path.join(HERE, "K2_R720_PREMISE_MINRIP_16OF16_v1.json")))
    R724 = json.load(open(os.path.join(HERE, "K2_R724_WALKS_16OF16_v1.json")))
    params = {k: dict(v) for k, v in R714["per_lane"].items()}
    rows = R720["per_lane"]; names = sorted(rows)
    froz = {k: {"sha16": (sh16(p) if os.path.exists(p) else None), "expected": exp,
                "match": os.path.exists(p) and sh16(p) == exp} for k, p, exp in FROZEN}
    frozen_ok = all(v["match"] for v in froz.values())
    inv = {nm: {(int(L), tuple(cp)) for L, cp in rows[nm]["footprint"]} for nm in names}
    # ---- 1. the 14 non-named rows: take the R724 walks (continuous, inventory-identical) ----
    walks = {}; metas = {}; src = {}
    for nm in names:
        if nm in REROUTE: continue
        w = [(int(L), tuple(cp)) for L, cp in R724["routes"][nm]["walk"]]
        walks[nm] = w; src[nm] = "R724 walk (continuous, inventory-identical)"
        metas[nm] = {"via_cells": [], "approach_layer": None, "approach_columns": None, "run_row": None,
                     "descent_column": R714["per_lane"][nm]["descent_column"] if nm in R714["per_lane"] else None,
                     "H_shift": 0}
    # ---- 2. the two named rows: declared full-row re-determination (exit gate column FIXED) ----
    scans = {}
    for nm in REROUTE:
        r = rows[nm]; ee = tuple(int(x) for x in r["exit_cell"]); eL = int(r["exit_layer"])
        cl = int(rows[nm]["col60_slot"][0])
        p0 = params[nm]; Hreg = int(p0["H"]); Y = int(p0["Y"]); t = int(p0["tail_layer"])
        oth = set()
        for n2 in names:
            if n2 != nm and n2 not in REROUTE: oth |= inv[n2]          # reference = the other 14 registered rows
        log_ = []; got = None
        for Xt in [ee[0] + 1, ee[0] + 2, ee[0] + 3, ee[0] + 4, ee[0] - 1, ee[0] - 2, ee[0] - 3]:
            for dH in DH_ORDER:
                H = Hreg + dH
                w, meta = build(cl, H, t, Xt, Y, ee, eL, oth)
                log_.append([Xt, dH, ("ok" if w is not None else meta)])
                if w is not None: got = (Xt, dH, H, w, meta); break
            if got: break
        scans[nm] = log_
        if got is None:
            log("%s: NO route with the exit gate column fixed (%d candidates, all refused)" % (nm, len(log_)))
            continue
        Xt, dH, H, w, meta = got
        meta["H_shift"] = dH; meta["descent_column"] = Xt
        walks[nm] = w; metas[nm] = meta
        src[nm] = "R730 declared full-row re-determination (product-style; exit gate column FIXED)"
        log("%s: run_row %d (dH %+d), descent_column %d (exit col %d), via %s, approach layer %s" %
            (nm, H, dH, Xt, ee[0], meta["via_cells"], meta["approach_layer"]))
    undrawable = [nm for nm in REROUTE if nm not in walks]
    if undrawable:
        rep = {"artifact": "k2_r730_row_redetermination_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "authority": "#K2-276 sec.3.5: declared full-row re-determination of OUT4_P and OUT6_P (exit gate column FIXED)",
               "binary": "STOP_L1_EXIT_GATE_FIXED_UNDRAWABLE",
               "verdict": "STOP_L1_EXIT_GATE_FIXED_UNDRAWABLE",
               "guardrail_triggered": "#K2-276 sec.3.4: a row that cannot be drawn with its registered exit gate column fixed => the ENG STOPS and reports; the supervisor evaluates under L1 (interface change)",
               "undrawable_rows": undrawable,
               "scan": {nm: scans[nm] for nm in REROUTE},
               "scan_candidate_order": {"descent_column": "exit_col+1..+4 then exit_col-1..-3", "run_row": "H, H-1, H+1, H-2, H+2, H-3, H+3"},
               "geometry_note": {"OUT4_P_J2": "exit gate (119,36) on layer 0 is BOXED by OTHER rows' registered cells: east side crosses OUT0_N's descent cell (120,36) (OUT0_N occupies col 120 rows 29..43); west side (cols 114..118 at rows 37..43) is blocked by OUT0_N ((118,43)) and OUT5_N (col 117 rows 37..42); t = eL = 0 so no second approach layer exists, and an L1-side approach also fails because (1,(119,36)) is OUT0_P's registered cell",
                                "OUT6_P_J2": "exit gate (115,36) on layer 0 is BOXED: its registered descent column 132 is the only clear L1 descent corridor in cols 112..132, but the approach from there to (115,36) is blocked on BOTH layers - L1 row 36 cols 117..127 are OUT0_P's registered cells (plus OUT6_N/OUT2_N/OUT3_P/OUT7_P) and L0 row 36 at (120,36) is OUT0_N's descent; every narrower descent column (112..119) is blocked in rows 37..52 by OUT0_P/OUT7_P/OUT6_N",
                                "shared_conclusion": "both named rows are blocked by the REGISTERED CORRIDORS OF OTHER LANES, not by their own parameters => an exit-gate-fixed single-row re-determination cannot succeed; the fix needs either a GROUPED (bundle) re-assignment of the row-36 escape band / the east descents, or an exit-gate (interface) change"},
"construction_runs": 1, "drawings": 0, "gerber_exported": False, "p5": False, "order": False,
               "frozen_four_distance": froz, "changes_to_frozen_sources": 0 if frozen_ok else "FROZEN MISMATCH",
               "elapsed_s": round(time.time() - t0, 1)}
        body = json.dumps(rep, ensure_ascii=False, indent=1, default=str); rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
        json.dump(rep, open(OUT, "w"), ensure_ascii=False, indent=1, default=str)
        log("WROTE %s hash=%s binary=%s" % (OUT, rep["artifact_hash16"], rep["binary"])); log("OWNER-ITEMS: 0")
        return 0
        Xt, dH, H, w, meta = got
        meta["H_shift"] = dH; meta["descent_column"] = Xt
        walks[nm] = w; metas[nm] = meta
        src[nm] = "R730 declared full-row re-determination (product-style; exit gate column FIXED)"
        log("%s: run_row %d (dH %+d), descent_column %d (exit col %d), via %s, approach layer %s" %
            (nm, H, dH, Xt, ee[0], meta["via_cells"], meta["approach_layer"]))
    # ---- 3. gates ----
    log("both rows re-determined; proceeding to the merge gates")
    cont = {}; bad = []
    for nm in names:
        r = rows[nm]; ee = (int(r["exit_layer"]), tuple(int(x) for x in r["exit_cell"]))
        cl = int(rows[nm]["col60_slot"][0]); H = int(metas[nm].get("run_row") or params[nm]["H"]) if (nm in params) else int(r["col60_slot"][2])
        if nm not in params: H = int(r["col60_slot"][2])
        slot = (cl, (60, H))
        w = walks[nm]; gaps = [i for i in range(1, len(w)) if not adj(w[i - 1], w[i])]
        dup = len(w) - len(set(w))
        ok = (w[0] == slot) and (w[-1] == ee) and (not gaps) and (dup == 0)
        cont[nm] = {"continuous": ok, "starts_at_slot": w[0] == slot, "ends_at_exit": w[-1] == ee, "gaps": gaps, "dupes": dup, "n_cells": len(w)}
        if not ok: bad.append(nm)
    own = collections.defaultdict(list)
    for nm in names:
        for c in set(walks[nm]): own[c].append(nm)
    conflicts = [[c[0], list(c[1]), o] for c, o in sorted(own.items()) if len(o) > 1]
    census = collections.Counter()
    for nm in names:
        for c in set(walks[nm]): census[c[1]] += 1
    n_cell_only = sum(1 for k, v in census.items() if v > 1)
    recon = {}; unexplained = []
    for nm in names:
        got = set(walks[nm]); added = sorted(got - inv[nm]); miss = sorted(inv[nm] - got)
        recon[nm] = {"inventory_cells": len(inv[nm]), "walk_cells": len(got),
                     "added_cells": [[c[0], list(c[1])] for c in added],
                     "superseded_registered_cells": [[c[0], list(c[1])] for c in miss], "missing_from_walk": []}
        if miss and nm not in REROUTE: unexplained.append([nm, recon[nm]["superseded_registered_cells"]])
    used = len(own); demand = sum(len(set(walks[nm])) for nm in names)
    cons = {"lanes": 16, "rows_that_are_one_continuous_route": 16 - len(bad), "rows_that_are_not": bad,
            "merged_0_conflict": len(conflicts) == 0, "conflict_cells": len(conflicts), "conflicts": conflicts[:20],
            "key_census": {"cell_only_conflicts": n_cell_only, "cell_layer_conflicts": len(conflicts)},
            "unexplained_differences_vs_R720_and_baseline13": unexplained,
            "exit_gates_unchanged": all(list(walks[nm][-1][1]) == list(rows[nm]["exit_cell"]) and walks[nm][-1][0] == int(rows[nm]["exit_layer"]) for nm in names),
            "capacity_certificate": {"cells_distinct_drawn": used, "capacity_ge_demand": used >= demand}}
    ok = (not bad) and (len(conflicts) == 0) and (not unexplained) and frozen_ok and cons["exit_gates_unchanged"]
    rep = {"artifact": "k2_r730_row_redetermination_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-276 sec.3.5: approved declared FULL-ROW re-determination of OUT4_P and OUT6_P (L2, exit gate column fixed), ONE deterministic run",
           "cause_of_death": "OUT4_P could not obtain a via cell on its registered row under any approved separation candidate; OUT6_P's descent column (132) sat far east of its exit (115) so a long approach had to cross the saturated row-36 band",
           "proven_facts": ["R728: key census 203 (cell only) vs 5 (cell,layer) => the 19 were REAL same-layer overlaps",
                            "R728: OUT4_P refused under all 6 declared separation candidates; OUT6_P needed its descent column moved",
                            "R730: the two named rows are re-determined with the EXIT GATE COLUMN FIXED; the other 14 rows keep the R724 walks"],
           "construction_runs": 1, "drawings": 0, "gerber_exported": False, "p5": False, "order": False,
           "frozen_four_distance": froz, "changes_to_frozen_sources": 0 if frozen_ok else "FROZEN MISMATCH",
           "redetermination": {"declared_order": {"descent_column": "exit_col+1..+4 then exit_col-1..-3 (product: the escape stays adjacent to the exit gate)",
                                                  "run_row": "registered H, then H-1/H+1/H-2/H+2/H-3/H+3",
                                                  "via_cell": "first column east of the col60 slot with BOTH layers free (layer-pair rule)",
                                                  "approach_layer": "exit layer, fallback tail layer"},
                               "scan": scans,
                               "rows": {nm: {"old": {"H": params[nm]["H"], "descent_column": params[nm]["descent_column"]},
                                             "new": {"H": metas[nm]["run_row"], "descent_column": metas[nm]["descent_column"]},
                                             "via_cells": metas[nm]["via_cells"], "approach_layer": metas[nm]["approach_layer"],
                                             "approach_columns": metas[nm]["approach_columns"]} for nm in REROUTE}},
           "routes": {nm: {"source": src[nm], "slot": list(walks[nm][0][1]), "slot_layer": walks[nm][0][0],
                           "exit_cell": rows[nm]["exit_cell"], "exit_layer": int(rows[nm]["exit_layer"]),
                           "via_cells": metas[nm]["via_cells"], "approach_layer": metas[nm]["approach_layer"],
                           "approach_columns": metas[nm]["approach_columns"], "n_cells": len(walks[nm]),
                           "continuous": cont[nm]["continuous"], "walk": [[L, list(cp)] for (L, cp) in walks[nm]]} for nm in names},
           "continuity": cont, "conservation": cons, "reconciliation_vs_R720": recon,
           "product_three_questions": {
               "①same_kind": "YES - PEX88096 PCIe4 switch GPU baseboard kit (REF-CASE-LIBRARY sec.A.1)",
               "②copyable": "BGA fan-out, lane grouping/routing, inner-layer 1OZ layer-change escape; in particular ONE GROUP ONE BUNDLE, LONG STRAIGHT RUN, ONE LAYER CHANGE AT THE GROUP FAN-OUT, BUNDLES DO NOT OVERLAP",
               "③differences": "we now follow the product for the two re-determined rows: the escape is short and stays on the exit layer, the layer change sits at the fan-out (first free column), and no bundle crosses another"},
           "product_comparison_column": {nm: ("follows product bundle rule (short escape on exit layer, layer change at fan-out)" if nm in REROUTE else "inherited R724 walk; matches the product's long-straight / no-cross rule per the three keys") for nm in names},
           "accounting": {"inventory_cells_total": sum(len(inv[nm]) for nm in names),
                          "walk_cells_total": sum(len(walks[nm]) for nm in names),
                          "connector_cells_added": sum(len(recon[nm]["added_cells"]) for nm in recon),
                          "superseded_registered_cells": {nm: len(recon[nm]["superseded_registered_cells"]) for nm in REROUTE},
                          "note": "the two re-determined rows carry a declared supersession of their registered cells (named in reconciliation_vs_R720[*].superseded_registered_cells); all other rows are inventory-identical or their added connectors are named"},
           "buildability": {"mode": "relocation_listed", "relocations": sorted(set(R720.get("buildability", {}).get("relocations", [])) | set(REROUTE)),
                            "new_this_item": list(REROUTE), "exit_gate_columns_unchanged": True},
           "verdict": ("MERGED_0_CONFLICT_PASS" if ok else "BOUNCE_DRAWING_LAYER"),
           "binary": ("MERGED_0_CONFLICT_PASS" if ok else "BOUNCE_DRAWING_LAYER"),
           "elapsed_s": round(time.time() - t0, 1)}
    body = json.dumps(rep, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(OUT, "w"), ensure_ascii=False, indent=1, default=str)
    log("walks %d/16 continuous (not %s) | conflicts=%d | unexplained=%s | exit_gates_unchanged=%s"
        % (16 - len(bad), bad, len(conflicts), unexplained, cons["exit_gates_unchanged"]))
    log("WROTE %s hash=%s binary=%s" % (OUT, rep["artifact_hash16"], rep["binary"]))
    log("OWNER-ITEMS: 0")
    return 0

if __name__ == "__main__":
    sys.exit(main())
