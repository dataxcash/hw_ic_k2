#!/usr/bin/env python3
"""K2 R724 --- #K2-273 sec.3.5 : the ONE authorised DETERMINISTIC WALK RE-EMISSION (zero search / zero trial / zero fallback).

① cause of death (one line): the per-cell inventories are segment-concatenated OCCUPANCY sets, not routes -- they
   omit the col60-slot layer-pair cell AND the via cell, so a row cannot be drawn as one line.

Method (deterministic; no solver, no search of the solution space, no parameter trial, no on-site fallback):
  * the 12 non-relocated base rows: re-emit ONE continuous walk from their R714 REGISTERED structural parameters
    (col60_layer / H / tail_layer / descent_column / Y / exit), repairing the two template defects (descent order
    + the approach run's off-by-one) and inserting the layer-pair cell at the col60 slot;
  * the 4 relocated/relaxed rows: recover their ordered walk by a deterministic segment stitch of their REGISTERED
    R720 record (pure serialisation of already-determined geometry);
  * then reconcile cell-for-cell against the R720 occupancy inventory and run the merged-board conflict census.
"""
import sys, os, json, hashlib, time, collections
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "K2_R724_WALKS_16OF16_v1.json")
LOGF = os.path.join(HERE, "K2_R724_solve.log")
LH = open(LOGF, "w")
def log(m): LH.write(str(m) + "\n"); LH.flush(); print(str(m), flush=True)

def adj(a, b):
    if a[0] == b[0]: return abs(a[1][0] - b[1][0]) + abs(a[1][1] - b[1][1]) == 1
    return a[1] == b[1]

def emit(cl, H, t, Xt, Y, ee, eL):
    """deterministic single walk col60 slot -> exit (adds the layer-pair cell the inventory omitted)."""
    w = [(cl, (60, H))]
    if t != cl: w.append((t, (60, H)))                       # layer-pair cell at the col60 slot
    w += [(t, (c, H)) for c in range(61, Xt + 1)]
    w += [(t, (Xt, r)) for r in range(H - 1, Y, -1)]         # descent H-1 .. Y+1 (order repaired)
    rng = range(Xt, ee[0] - 1, -1) if ee[0] <= Xt else range(Xt, ee[0] + 1)
    w += [(t, (c, Y)) for c in rng]                           # approach run, incl. the exit column
    last = (eL, tuple(ee))
    if w[-1] != last:
        if t != eL and w[-1] != (t, tuple(ee)): w.append((t, tuple(ee)))
        w.append(last)
    return w

def stitch(fp, prefer=None):
    """deterministic serialisation: chop into maximal connected runs, chain greedily from the run holding `prefer`."""
    segs = []; cur = [fp[0]]
    for i in range(1, len(fp)):
        if adj(fp[i - 1], fp[i]): cur.append(fp[i])
        else: segs.append(cur); cur = [fp[i]]
    segs.append(cur)
    order = list(range(len(segs)))
    if prefer is not None:
        order.sort(key=lambda j: 0 if prefer in (segs[j][0], segs[j][-1]) else 1)
    used = [False] * len(segs); i0 = order[0]; used[i0] = True
    chain = list(segs[i0]) if prefer in (None, segs[i0][0]) or segs[i0][-1] != prefer else list(reversed(segs[i0]))
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

def main():
    t0 = time.time()
    R714 = json.load(open(os.path.join(HERE, "K2_R714_BASE13FROZEN_PLUS_VIA3_v1.json")))
    R720 = json.load(open(os.path.join(HERE, "K2_R720_PREMISE_MINRIP_16OF16_v1.json")))
    params = R714["per_lane"]; rows = R720["per_lane"]; names = sorted(rows)
    relocated = set(R720.get("buildability", {}).get("relocations", []))
    errs = []
    if len(names) != 16: errs.append("rows != 16")
    if R720.get("binary") != "SAT_16of16": errs.append("R720 binary != SAT_16of16")
    if errs: log("FAIL_LOUD: %s" % errs); return 3
    # ---- build one ordered walk per row ----
    walks = {}; src = {}; notes = []
    for nm in names:
        r = rows[nm]; slot = (int(r["col60_slot"][0]), (int(r["col60_slot"][1]), int(r["col60_slot"][2])))
        ee = tuple(int(x) for x in r["exit_cell"]); eL = int(r["exit_layer"])
        rec = [(int(L), tuple(cp)) for L, cp in r["footprint"]]
        st, uns = stitch(rec, prefer=slot)
        if uns == 0 and st and st[-1] == slot and st[0] == (eL, ee): st = list(reversed(st))   # orient slot -> exit
        rec_is_walk = (uns == 0 and len(st) > 1 and st[0] == slot and st[-1] == (eL, ee))
        if rec_is_walk:
            walks[nm] = st; src[nm] = "registered R720 record, deterministically stitched (already a walk)"
        elif nm in params and nm not in relocated:
            p = params[nm]
            w = [(int(L), tuple(cp)) for L, cp in emit(int(p["col60_layer"]), int(p["H"]), int(p["tail_layer"]),
                                                       int(p["descent_column"]), int(p["Y"]), ee, eL)]
            walks[nm] = w; src[nm] = "re-emitted from R714 REGISTERED structural parameters"
        else:
            walks[nm] = rec; src[nm] = "registered R720 record (used verbatim)"
            notes.append([nm, "record is not a walk and no R714 parameters exist"])
    # ---- gate 1: continuity ----
    cont = {}; bad = []
    for nm in names:
        r = rows[nm]; slot = (int(r["col60_slot"][0]), (int(r["col60_slot"][1]), int(r["col60_slot"][2])))
        exitc = (int(r["exit_layer"]), tuple(int(x) for x in r["exit_cell"])); w = walks[nm]
        gaps = [i for i in range(1, len(w)) if not adj(w[i - 1], w[i])]
        dup = len(w) - len(set(w))
        ok = (w[0] == slot) and (w[-1] == exitc) and (not gaps) and (dup == 0)
        cont[nm] = {"continuous": ok, "starts_at_slot": w[0] == slot, "ends_at_exit": w[-1] == exitc,
                    "gaps": gaps, "dupes": dup, "n_cells": len(w)}
        if not ok: bad.append(nm)
    # ---- gate 2: merged conflict census ----
    own = collections.defaultdict(list)
    for nm in names:
        for c in set(walks[nm]): own[c].append(nm)
    inv_all = {}
    for nm in names: inv_all[nm] = {(int(L), tuple(cp)) for L, cp in rows[nm]["footprint"]}
    conflicts = []
    for c, owners in sorted(own.items()):
        if len(owners) < 2: continue
        cls = "other"
        for nm in owners:
            r = rows[nm]; slot = (int(r["col60_slot"][0]), (int(r["col60_slot"][1]), int(r["col60_slot"][2])))
            if c[1] == slot[1] and c[0] != slot[0]:
                cls = "SLOT_LAYER_SWAP: two rows claim the SAME (col60,H) cell on opposite layers and both need a layer change there (the registered 'col60_slots_distinct' key is layer-aware but not layer-PAIR aware)"
        conflicts.append([c[0], list(c[1]), owners, cls])
    # ---- gate 3: reconciliation vs the R720 inventory ----
    recon = {}; unexplained = []
    for nm in names:
        got = set(walks[nm]); inv = inv_all[nm]
        added = sorted(got - inv); miss = sorted(inv - got)
        recon[nm] = {"inventory_cells": len(inv), "walk_cells": len(got),
                     "added_cells": [[c[0], list(c[1])] for c in added],
                     "missing_from_walk": [[c[0], list(c[1])] for c in miss]}
        if miss: unexplained.append([nm, [[c[0], list(c[1])] for c in miss]])
    # ---- gate 4: conservation ----
    used = len(own)
    demand = sum(len(set(walks[nm])) for nm in names)
    cons = {"lanes": len(names), "rows_that_are_one_continuous_route": len(names) - len(bad),
            "rows_that_are_not": bad, "merged_0_conflict": len(conflicts) == 0,
            "conflict_cells": len(conflicts), "conflicts": conflicts[:40],
            "unexplained_differences_vs_R720": unexplained,
            "capacity_certificate": {"cells_distinct_drawn": used,
                                     "capacity_ge_demand": used >= demand,
                                     "note": "capacity = distinct cells on the merged 2-layer board; demand = union of the 16 walks"}}
    build = {"mode": "relocation_listed" if relocated else "no_move", "relocations": sorted(relocated),
             "note": "this item adds NO relocation; it only draws the registered routes and inserts the layer-pair cells they left implicit"}
    structural = [c for c in conflicts if str(c[3]).startswith("SLOT_LAYER_SWAP")]
    ok = (not bad) and (len(conflicts) == 0) and (not unexplained)
    rep = {"artifact": "k2_r724_walks_16of16_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-273 sec.3.5: ONE deterministic walk re-emission (zero search / zero trial / zero fallback); formal product in k2/",
           "cause_of_death": "the per-cell inventories are segment-concatenated OCCUPANCY sets, not routes: they omit the col60-slot layer-pair cell and the via cell, so a row cannot be drawn as one line",
           "proven_facts": ["R722: merged 0 conflicts over 1479 distinct cells",
                            "R722: row-for-row cell identity with R720 16/16 TRUE",
                            "R722: every row slot+exit present (exit on its own exit layer)",
                            "R722: evidence accounting self-balanced 1479 + 4 named = 1483 = R720 cells_raw",
                            "R722: only 5/16 rows stitch into one walk; 11 rows named, 80 candidate connector cells",
                            "R724: the two template defects are (a) the descent emitted bottom-up and (b) the approach run's off-by-one; both repaired here"],
           "construction_runs": 1, "drawings": 0, "gerber_exported": False, "p5": False, "order": False,
           "accounting": {"cells_sum_of_walks": sum(len(walks[nm]) for nm in names),
                          "cells_distinct_drawn": len(own),
                          "connector_cells_added_vs_R720": sum(len(recon[nm]["added_cells"]) for nm in names),
                          "inventory_cells_total": sum(len(inv_all[nm]) for nm in names),
                          "balance": "%d (R720 inventory, deduplicated) + %d (connector/approach cells the inventory omitted) = %d (walk cells before dedup); recomputable from this artifact"
                                     % (sum(len(inv_all[nm]) for nm in names), sum(len(recon[nm]["added_cells"]) for nm in names), sum(len(walks[nm]) for nm in names)),
                          "all_inventory_cells_covered": all(not recon[nm]["missing_from_walk"] for nm in names)},
           "routes": {nm: {"source": src[nm], "slot": rows[nm]["col60_slot"], "exit_cell": rows[nm]["exit_cell"],
                           "exit_layer": int(rows[nm]["exit_layer"]), "n_cells": len(walks[nm]),
                           "continuous": cont[nm]["continuous"],
                           "walk": [[L, list(cp)] for (L, cp) in walks[nm]]} for nm in names},
           "continuity": cont, "conservation": cons,
           "reconciliation_vs_R720": recon, "buildability": build, "notes": notes,
           "structural_finding": {"slot_layer_swap_conflicts": len(structural), "detail": structural[:16],
                                  "meaning": "the registered 'col60_slots_distinct' key only makes (layer,H) distinct; it does NOT prevent two rows from claiming the SAME (col60,H) cell on OPPOSITE layers - undrawable when both must change layer there"},
           "verdict": ("WALKS_16OF16_PASS" if ok else "BOUNCE_DRAWING_LAYER"),
           "binary": ("WALKS_16OF16_PASS" if ok else "BOUNCE_DRAWING_LAYER"),
           "elapsed_s": round(time.time() - t0, 1)}
    body = json.dumps(rep, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(OUT, "w"), ensure_ascii=False, indent=1, default=str)
    log("walks continuous %d/%d (not: %s); conflict cells=%d (slot-layer-swap=%d); unexplained=%s"
        % (len(names) - len(bad), len(names), bad, len(conflicts), len(structural), unexplained))
    log("WROTE %s hash=%s binary=%s" % (OUT, rep["artifact_hash16"], rep["binary"]))
    log("OWNER-ITEMS: 0")
    return 0

if __name__ == "__main__":
    sys.exit(main())
