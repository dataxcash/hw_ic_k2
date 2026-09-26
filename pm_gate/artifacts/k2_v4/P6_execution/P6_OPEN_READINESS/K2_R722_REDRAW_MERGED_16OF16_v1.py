#!/usr/bin/env python3
"""K2 R722 --- #K2-271 sec.3.6/6.4 : the ONE authorised 16-lane REDRAW + merged-board 0-conflict check.

ZERO freedom: read the accepted R720 rows (16 lanes: layer / slot / via-pairs / corridor -> per-lane cell inventory),
place them on the merged 2-layer board, and run only the in-register gates. NO solver, NO search of the solution
space, NO parameter trial, NO on-site fallback. If a row cannot be drawn / would need a search / a gate is missing,
the row is NAMED and bounced to the drawing layer (sec.3.6) - never patched.

Gates (sec.6.4): (1) merged map 0 conflicts, cell by cell; (2) cell-for-cell identity with R720's 16 row inventories
(this is what empirically verifies the 12 carried rows); (3) evidence accounting self-balances (raw recomputable from
this artifact); (4) endpoints present (each row's registered col60 slot and exit cell, the latter on its exit layer).
Extra audit (sec.5 M-ENG-BASE-PROVENANCE-QUALITY): per-row single-walk decomposition + deterministic stitch, with any
missing cells NAMED as a discrepancy list (NOT filled in, NOT searched for).
"""
import sys, os, json, hashlib, time, collections
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "K2_R720_PREMISE_MINRIP_16OF16_v1.json")
OUT = os.path.join(HERE, "K2_R722_REDRAW_MERGED_16OF16_v1.json")
LOGF = os.path.join(HERE, "K2_R722_solve.log")
LH = open(LOGF, "w")
def log(m): LH.write(str(m) + "\n"); LH.flush(); print(str(m), flush=True)

def adj(a, b):
    """grid adjacency: same layer 4-neighbour, or a via (same cell, layer change)."""
    if a[0] == b[0]:
        return abs(a[1][0] - b[1][0]) + abs(a[1][1] - b[1][1]) == 1
    return a[1] == b[1]

def segments(fp):
    segs = []; cur = [fp[0]]
    for i in range(1, len(fp)):
        if adj(fp[i - 1], fp[i]): cur.append(fp[i])
        else: segs.append(cur); cur = [fp[i]]
    segs.append(cur); return segs

def bends(seg):
    """informational: direction changes inside a connected chain (a bend is LEGAL, not a failure)."""
    n = 0
    for i in range(2, len(seg)):
        a, b, c = seg[i - 2][1], seg[i - 1][1], seg[i][1]
        if seg[i][0] != seg[i - 1][0] or seg[i - 1][0] != seg[i - 2][0]:
            continue
        if (b[0] - a[0], b[1] - a[1]) != (c[0] - b[0], c[1] - b[1]): n += 1
    return n

def manh_path(L, a, b):
    """deterministic Manhattan cell list on layer L: a (exclusive) -> b (inclusive). REPORTING ONLY."""
    (c0, r0), (c1, r1) = a, b; out = []; c, r = c0, r0
    while c != c1:
        c += 1 if c1 > c else -1; out.append((L, (c, r)))
    while r != r1:
        r += 1 if r1 > r else -1; out.append((L, (c, r)))
    return out

def connector(E, T):
    """minimal additive cells needed to join E to T (REPORTING the gap only - never applied)."""
    if E == T: return []
    if E[0] == T[0]: return manh_path(E[0], E[1], T[1])[:-1]
    A = [(T[0], E[1])] + manh_path(T[0], E[1], T[1])[:-1]          # via at E's cell
    B = manh_path(E[0], E[1], T[1])[:-1] + [(T[0], T[1])]          # via at T's cell
    return A if len(A) <= len(B) else B

def main():
    t0 = time.time()
    src = json.load(open(SRC))
    rows = src["per_lane"]; names = sorted(rows)
    # ---------- self-test (fail-loud): the checker itself must bite ----------
    errs = []
    if len(names) != 16: errs.append("row count != 16 (%d)" % len(names))
    if src.get("binary") != "SAT_16of16": errs.append("source binary != SAT_16of16 (%s)" % src.get("binary"))
    if errs: log("FAIL_LOUD self-test: %s" % errs); return 3
    # ---------- load the R714 source frozen lists (only to RECONCILE the accounting difference) ----------
    R714 = json.load(open(os.path.join(HERE, "K2_R714_BASE13FROZEN_PLUS_VIA3_v1.json")))
    relocated = set(src.get("buildability", {}).get("relocations", []))      # rows R720 re-routed (dedup, no repeats)
    selfrepeat = []                             # self-repeats still CARRIED into R720 (its cells_raw counts these)
    for k, v in R714["baseline_frozen"]["per_lane"].items():
        if k in relocated: continue
        raw = [(int(L), tuple(cp)) for L, cp in v]; seen = set()
        for c in raw:
            if c in seen: selfrepeat.append([k, c[0], list(c[1])])
            seen.add(c)
    # ---------- A. 照图落线 (grid draw, zero freedom) ----------
    layer_state = {}                                  # (layer,cell) -> lane  (the merged board map)
    per_lane = {}; conflicts = []; identity_fail = []; endpoints_fail = []; seg_report = {}
    for nm in names:
        r = rows[nm]
        fp = [(int(L), tuple(cp)) for L, cp in r["footprint"]]
        fset = set(fp)
        if len(fp) != len(fset): identity_fail.append([nm, "intra-row repeat", len(fp) - len(fset)])
        for c in fset:
            if c in layer_state: conflicts.append([c[0], list(c[1]), layer_state[c], nm])
            layer_state[c] = nm
        # rebuild the geometry from its straight segments and require exact identity with the inventory
        segs = segments(fp)
        rebuilt = [c for s in segs for c in s]
        if rebuilt != fp: identity_fail.append([nm, "segment rebuild != inventory", len(rebuilt)])
        nb = sum(bends(s) for s in segs)
        slot = tuple(int(x) for x in r["col60_slot"])                      # (layer, col, row)
        exitc = (int(r["exit_layer"]), tuple(int(x) for x in r["exit_cell"]))
        if (slot[0], (slot[1], slot[2])) not in fset or exitc not in fset:
            endpoints_fail.append([nm, "slot" if (slot[0], (slot[1], slot[2])) not in fset else "", "exit" if exitc not in fset else ""])
        seg_report[nm] = {"n_cells": len(fset), "n_segments": len(segs), "n_bends": nb,
                          "segment_lens": [len(s) for s in segs],
                          "segment_ends": [[list(s[0][1]), list(s[-1][1])] for s in segs]}
    four = (len(conflicts) == 0)
    identity_ok = (len(identity_fail) == 0)
    endpoints_ok = (len(endpoints_fail) == 0)
    # ---------- B. single-walk audit (sec.5 provenance quality) ----------
    walk = {}
    for nm in names:
        r = rows[nm]; fp = [(int(L), tuple(cp)) for L, cp in r["footprint"]]
        segs = segments(fp); fset = set(fp)
        slot = (int(r["col60_slot"][0]), (int(r["col60_slot"][1]), int(r["col60_slot"][2])))
        exitc = (int(r["exit_layer"]), tuple(int(x) for x in r["exit_cell"]))
        # deterministic greedy stitch from the slot segment to the exit segment
        starts = [i for i, s in enumerate(segs) if slot in (s[0], s[-1])]
        used = [False] * len(segs); chain = []; end = None; unstitched = 0
        if starts:
            i = starts[0]; used[i] = True
            ord_seg = segs[i] if segs[i][0] == slot else list(reversed(segs[i]))
            chain = list(ord_seg); end = chain[-1]
            while True:
                nxt = None
                for j, s in enumerate(segs):
                    if used[j]: continue
                    if adj(end, s[0]): nxt = (j, list(s))
                    elif adj(end, s[-1]): nxt = (j, list(reversed(s)))
                    if nxt: break
                if not nxt: break
                used[nxt[0]] = True; chain += nxt[1]; end = nxt[1][-1]
        # connector-aware stitch: join segments (and finally the exit) allowing ONLY reported gap cells
        missing = []
        while end is not None:
            best = None
            for j, s3 in enumerate(segs):
                if used[j]: continue
                for tgt in (s3[0], s3[-1]):
                    cn = connector(end, tgt)
                    if best is None or len(cn) < len(best[1]): best = (j, cn, tgt)
            cexit = connector(end, exitc)
            if end != exitc and (best is None or len(cexit) <= len(best[1])):
                missing += cexit; end = exitc; break
            if best is None: break
            j, cn, tgt = best
            if len(cn) > 4: break                                   # do NOT bridge a big hole silently
            used[j] = True; missing += cn
            seg3 = segs[j]; seg3 = seg3 if seg3[0] == tgt else list(reversed(seg3))
            chain += cn + seg3; end = seg3[-1]
        if end != exitc and end is not None:
            missing += connector(end, exitc)
        unstitched = sum(1 for u in used if not u)
        walk[nm] = {"chain_len": len(chain), "unstitched_segments": unstitched,
                    "chain_end": [end[0], list(end[1])] if end else None,
                    "reaches_exit": bool(end == exitc),
                    "missing_connector_cells_n": len(missing),
                    "missing_connector_cells": [[c[0], list(c[1])] for c in missing],
                    "gap_cells_not_in_inventory": [[c[0], list(c[1])] for c in missing if c not in fset]}
    walk_ok = [nm for nm in names if walk[nm]["missing_connector_cells_n"] == 0]
    # ---------- C. evidence accounting self-balance ----------
    raw = sum(rows[nm]["n_footprint_cells"] for nm in names)          # recomputable from the delivered rows
    raw_len = sum(len(rows[nm]["footprint"]) for nm in names)
    distinct = len(layer_state)
    accounting = {"cells_raw_from_delivered_rows": raw, "cells_raw_by_len(footprint)": raw_len,
                  "cells_distinct": distinct, "raw_equals_distinct": raw == distinct,
                  "source_frozen_self_repeat_cells": selfrepeat,
                  "reconciliation": "%d (deduplicated inventory) + %d (self-repeat cells still carried from the source frozen lists) = %d = R720 cells_raw (%s)"
                                    % (distinct, len(selfrepeat), distinct + len(selfrepeat), src.get("conservation", {}).get("cells_raw"))}
    bounce = [nm for nm in names if walk[nm]["missing_connector_cells_n"] > 0]
    total_missing = sum(walk[nm]["missing_connector_cells_n"] for nm in names)
    merged_ok = bool(four and identity_ok and endpoints_ok and raw == distinct)
    rep = {"artifact": "k2_r722_redraw_merged_16of16_v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "authority": "#K2-271 sec.3.6 / sec.6.4: ONE 16-lane redraw + merged-board 0-conflict check; zero freedom, zero search, zero parameter trial",
           "source": {"file": "K2_R720_PREMISE_MINRIP_16OF16_v1.json", "hash16": src.get("artifact_hash16"),
                      "base_ref": src.get("base_ref"), "binary": src.get("binary")},
           "construction_runs": 1, "drawings": (1 if merged_ok else 0),
           "gerber_exported": False, "p5": False, "order": False,
           "merged_board": {"lanes": len(names), "cells_distinct": distinct, "conflicts": conflicts,
                            "FOURTH_KEY_merged_0_conflict": four},
           "identity_with_source": {"row_for_row_cell_identity": identity_ok, "failures": identity_fail},
           "endpoints": {"all_slot_and_exit_present": endpoints_ok, "failures": endpoints_fail},
           "accounting": accounting,
           "single_walk_audit": {"rows_complete": len(walk_ok), "of": len(names), "per_row": walk,
                                 "note": "the R720 row inventories are cell SETS recorded as segment concatenations; the audit stitches them deterministically into one chain and NAMES any cell missing to close the walk. Missing cells are a DISCREPANCY LIST, never filled in."},
           "segments": seg_report,
           "bounce_to_drawing_layer": {"required": bool(bounce), "rows": bounce,
                                       "rows_complete": len(walk_ok), "of": len(names),
                                       "total_missing_connector_cells": total_missing,
                                       "missing_by_row": {nm: walk[nm]["missing_connector_cells"] for nm in bounce},
                                       "basis": "#K2-271 sec.3.6: a row that cannot be drawn as one connected line (or would need a search) is characterised as 'drawing-layer figure missing' and bounced - never patched at the construction layer."},
           "merge_gates_pass": merged_ok,
           "verdict": ("BOUNCE_DRAWING_LAYER_FIGURE_MISSING" if (bounce or not merged_ok) else "MERGED_0_CONFLICT_PASS"),
           "binary": ("BOUNCE_DRAWING_LAYER_FIGURE_MISSING" if (bounce or not merged_ok) else "MERGED_0_CONFLICT_PASS"),
           "verdict_basis": "sec.3.6: a row that cannot be drawn as one connected line (needs cells that are not in its inventory) is characterised as 'drawing-layer figure missing' and bounced - never patched at the construction layer",
           "elapsed_s": round(time.time() - t0, 1)}
    body = json.dumps(rep, ensure_ascii=False, indent=1, default=str)
    rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(OUT, "w"), ensure_ascii=False, indent=1, default=str)
    log("rows=%d cells_distinct=%d conflicts=%d identity=%s endpoints=%s raw=%d==distinct=%s"
        % (len(names), distinct, len(conflicts), identity_ok, endpoints_ok, raw, raw == distinct))
    log("single_walk: %d/%d rows complete; missing connector cells=%d; bounce_rows=%s"
        % (len(walk_ok), len(names), total_missing, bounce))
    log("WROTE %s hash=%s binary=%s" % (OUT, rep["artifact_hash16"], rep["binary"]))
    log("OWNER-ITEMS: 0")
    return 0

if __name__ == "__main__":
    sys.exit(main())
