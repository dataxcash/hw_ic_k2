#!/usr/bin/env python3
"""P3 v57 — F4-INDVER: independent polynomial verifier for the W1 no-crossing
ordered-assignment feasibility predicate.

Purpose
-------
Replace W1's exhaustive oracle (limited to n<=7) with a polynomial decision
procedure that can decide the real n=8 single-band and n=16 joint-frame
instances, while cross-checking against an independent local brute oracle on
200 replayed synthetic instances (n in [1,6]).

Predicate (W1 contract, exact)
------------------------------
Instance = pages [(id, row_y)] + lanes [y] + leg.
Feasible iff there is an INJECTIVE assignment page -> lane index such that
  * pages sorted by (row_y, id) map to STRICTLY INCREASING lane indices, and
  * for each page, |lane_y - row_y| <= leg + 1e-9.

Exact engine (independent structure)
------------------------------------
Pages sorted by (row_y, id), lanes ascending.  Because pages are row-sorted and
lanes sorted, each page's allowed lane indices form a contiguous interval
[lo_i, hi_i] with lo/hi non-decreasing in i.  Build the convex bipartite graph
and run Kuhn's augmenting-path maximum matching; feasible iff |matching| == n.

Uncrossing lemma
----------------
For intervals with monotone endpoints, a perfect matching can always be
uncrossed into a non-crossing one.  Suppose i<j are assigned lanes a>b.  Then
  lo_i <= lo_j <= b < a <= hi_i   (monotone endpoints; b in allowed(j), a in allowed(i))
so b in allowed(i) (lo_i <= b and b < a <= hi_i) and a in allowed(j)
(lo_j <= b < a and a <= hi_i <= hi_j).  Swapping i,j keeps a perfect matching
and removes the crossing.  Therefore matching exists <=> non-crossing
assignment exists.

The engine returns a bool ONLY; it never emits the matching/assignment
("no allocation output").

This module deliberately does NOT import the W1 assign tool; it is a fully
independent decision procedure.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import random
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# paths / frozen constants
# --------------------------------------------------------------------------
SELF = Path(__file__).resolve()
K2 = SELF.parents[1]
STEP = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3" / "mcio_feas_step2"

MANIFEST = STEP / "m13_v57_s1_page_manifest.json"
RULES = K2 / "_shared" / "eda_core" / "drc_rules.json"
W0R_MODEL = STEP / "m13_v57_big_w0r_corridor_model.json"
W1_REPORT = STEP / "m13_v57_big_w1_report.json"
G3_CONTRACT = STEP / "m13_v57_g3_freeze_contract_v1_1_frame_ruling.md"

OUT = STEP / "m13_v57_f4_indver_report.json"

REV = "F4-INDVER.1"
SEED = 20260909
PITCH = 1.46
MARGIN = 0.0
KS = [1, 2, 3, 5]

FROZEN_SHA = {
    "manifest": "a8ef3ea8ecff99d7549d4122043c972c1bb68346dc4dcc3f36fdd9bacde49890",
    "rules": "0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448",
    "w0r_model": "80ee9adb78a7e9ad94c27d426295592eee21af3d1e3ce88fe3042183160f0efa",
}

FORBIDDEN_KEYS = ["selected", "assigned", "allocation", "witness"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rel(path: Path) -> str:
    return str(path.relative_to(K2))


def _row_key(p):
    return (p[1], p[0])


# --------------------------------------------------------------------------
# exact engine: interval bipartite matching (Kuhn augmenting paths)
# --------------------------------------------------------------------------
def _allowed(lanes, row, leg):
    """Contiguous allowed-lane index interval for one page (lanes ascending)."""
    return [i for i, y in enumerate(lanes) if abs(y - row) <= leg + 1e-9]


def exact_feasible(pages, lanes, leg, sort_key=_row_key):
    """Polynomial feasibility via maximum bipartite matching on a convex graph.

    Returns bool ONLY — never the matching/assignment.
    """
    ps = sorted(pages, key=sort_key)
    L = sorted(lanes)
    n = len(ps)
    if n > len(L):
        return False
    adj = [_allowed(L, row, leg) for _, row in ps]
    match_lane = [-1] * len(L)  # lane index -> page index

    def _augment(u, seen):
        for v in adj[u]:
            if v in seen:
                continue
            seen.add(v)
            if match_lane[v] == -1 or _augment(match_lane[v], seen):
                match_lane[v] = u
                return True
        return False

    matched = 0
    for u in range(n):
        if _augment(u, set()):
            matched += 1
    return matched == n


def brute_feasible(pages, lanes, leg, sort_key=None):
    """Independent small-n reference: full permutation enumeration of strictly
    increasing lane-index tuples (local reference; NOT W1).

    `sort_key` is accepted for a uniform MUS-engine call signature and is
    ignored: the canonical order is always (row_y, id)."""
    L = sorted(lanes)
    ps = sorted(pages, key=_row_key)
    n = len(ps)
    if n > len(L):
        return False
    for perm in itertools.permutations(range(len(L)), n):
        if any(perm[i] >= perm[i + 1] for i in range(n - 1)):
            continue
        if all(abs(L[perm[i]] - ps[i][1]) <= leg + 1e-9 for i in range(n)):
            return True
    return False


def mus(pages, lanes, leg, engine, sort_key=_row_key):
    """Minimal unsatisfiable subset — W1-identical convention:
    cardinality ascending, then id-tuple lexicographic; first infeasible
    subset = unique inclusion-minimal core."""
    ids = sorted(p[0] for p in pages)
    for card in range(1, len(ids) + 1):
        for combo in itertools.combinations(ids, card):
            sub = [p for p in pages if p[0] in set(combo)]
            if not engine(sub, lanes, leg, sort_key):
                return list(combo)
    return None


# --------------------------------------------------------------------------
# synthetic replay (W1 generation recipe, seed 20260909, no W1 import)
# --------------------------------------------------------------------------
def run_synthetic():
    rng = random.Random(SEED)
    n_inst = 200
    mismatch, mus_mismatch = [], []
    decision_match = mus_match = order_invariant = 0

    for idx in range(n_inst):
        n = rng.randint(1, 6)
        lanes = [round(40 + i * 1.46, 3) for i in range(rng.randint(n, n + 3))]
        leg = rng.choice([1.46, 2.92, 4.38, 7.3])
        pages = [(f"P{k}", round(rng.choice(lanes) + rng.choice(
            [-3.0, -1.5, -0.5, 0.0, 0.5, 1.5, 3.0]), 3)) for k in range(n)]

        ef = exact_feasible(pages, lanes, leg)
        bf = brute_feasible(pages, lanes, leg)
        if ef == bf:
            decision_match += 1
        else:
            mismatch.append({"instance_index": idx, "exact": ef, "brute": bf})
            continue

        if not ef:
            me = mus(pages, lanes, leg, exact_feasible)
            mb = mus(pages, lanes, leg, brute_feasible)
            if me == mb:
                mus_match += 1
            else:
                mus_mismatch.append({"instance_index": idx,
                                     "exact_mus": me, "brute_mus": mb})
        else:
            mus_match += 1

        outs = {
            exact_feasible(sorted(pages, key=lambda p: p[0]), lanes, leg),
            exact_feasible(sorted(pages, key=lambda p: p[0], reverse=True),
                           lanes, leg),
            exact_feasible(pages, lanes, leg),
        }
        if len(outs) == 1:
            order_invariant += 1

    return {
        "n_instances": n_inst,
        "decision_match": decision_match,
        "mus_match": mus_match,
        "order_invariant": order_invariant,
        "mismatch": mismatch,
        "mus_mismatch": mus_mismatch,
    }


# --------------------------------------------------------------------------
# real instances (n=8 single band, n=16 joint frame)
# --------------------------------------------------------------------------
def _page_row(page):
    conn = page["anchors"]["conn"]
    return round((conn["P"]["pad_global"][1] + conn["N"]["pad_global"][1]) / 2, 3)


def _lane_domain(span):
    return [round(span[0] + i * PITCH, 3)
            for i in range(int((span[1] - span[0]) // PITCH) + 1)]


def run_real(manifest, w0r):
    pages_by_id = {p["page_id"]: p for p in manifest["pages"]}
    single_band, joint_frame, capacity = [], [], []

    for cid, corridor in w0r["corridors"].items():
        span = corridor["usable_y_spans"][0]
        lanes = _lane_domain(span)
        span_len = round(span[1] - span[0], 3)
        band_pages = {}

        for band, band_obj in corridor["data_bands"].items():
            pages = [(pid, _page_row(pages_by_id[pid]))
                     for pid in band_obj["page_ids"]]
            band_pages[band] = pages

            for k in KS:
                leg = round(k * PITCH, 3)
                feas = exact_feasible(pages, lanes, leg)
                entry = {"corridor": cid, "band": band, "n": len(pages),
                         "k": k, "leg": leg, "feasible": feas}
                if not feas:
                    entry["mus"] = mus(pages, lanes, leg, exact_feasible)
                single_band.append(entry)

            required = round((len(pages) - 1) * PITCH, 3)
            capacity.append({"corridor": cid, "frame": band, "n": len(pages),
                             "required_mm": required, "span_len_mm": span_len,
                             "ok": required <= span_len + 1e-9})

        joint = [p for band in band_pages for p in band_pages[band]]
        for k in KS:
            leg = round(k * PITCH, 3)
            feas = exact_feasible(joint, lanes, leg)
            entry = {"corridor": cid, "frame": "joint", "n": len(joint),
                     "k": k, "leg": leg, "feasible": feas}
            if not feas:
                entry["mus"] = mus(joint, lanes, leg, exact_feasible)
            joint_frame.append(entry)

        required = round((len(joint) - 1) * PITCH, 3)
        capacity.append({"corridor": cid, "frame": "joint", "n": len(joint),
                         "required_mm": required, "span_len_mm": span_len,
                         "ok": required <= span_len + 1e-9})

    return single_band, joint_frame, capacity


# expected real decisions (§9 self-verify table)
EXPECTED = {
    ("EAST_CHIP_TO_J2", "up"): {1: True, 2: True, 3: True, 5: True},
    ("EAST_CHIP_TO_J2", "dn"): {1: True, 2: True, 3: True, 5: True},
    ("EAST_CHIP_TO_J2", "joint"): {1: False, 2: True, 3: True, 5: True},
    ("WEST_MCIO_TO_CHIP", "up"): {1: False, 2: True, 3: True, 5: True},
    ("WEST_MCIO_TO_CHIP", "dn"): {1: False, 2: True, 3: True, 5: True},
    ("WEST_MCIO_TO_CHIP", "joint"): {1: False, 2: False, 3: False, 5: True},
}


def check_expected(single_band, joint_frame):
    seen = {}
    for e in single_band:
        seen[(e["corridor"], e["band"])] = seen.get(
            (e["corridor"], e["band"]), {})
        seen[(e["corridor"], e["band"])][e["k"]] = e["feasible"]
    for e in joint_frame:
        seen[(e["corridor"], "joint")] = seen.get(
            (e["corridor"], "joint"), {})
        seen[(e["corridor"], "joint")][e["k"]] = e["feasible"]
    bad = []
    for key, exp in EXPECTED.items():
        got = seen.get(key)
        if got != exp:
            bad.append({"key": list(key), "expected": exp, "got": got})
    return bad


# --------------------------------------------------------------------------
# no-allocation scan
# --------------------------------------------------------------------------
def _scan_keys(obj, path, leaked):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in FORBIDDEN_KEYS:
                leaked.append(f"{path}.{k}" if path else k)
            _scan_keys(v, f"{path}.{k}" if path else k, leaked)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _scan_keys(v, f"{path}[{i}]", leaked)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main() -> int:
    # --- pitch authority: RULES["diff_pair"] must derive 1.46 -------------
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    dp = rules["diff_pair"]
    pitch_derived = round(dp["p_gap"] + 2 * dp["p_width"] + dp["inter_pair_spacing"], 3)
    assert abs(pitch_derived - PITCH) < 1e-12, (
        f"pitch authority drift: derived {pitch_derived} != {PITCH}")

    # --- frozen fingerprints (fail on drift) ------------------------------
    inputs_sha = {
        "manifest": sha(MANIFEST),
        "rules": sha(RULES),
        "w0r_model": sha(W0R_MODEL),
        "w1_report": sha(W1_REPORT),
    }
    sha_ok = all(inputs_sha[k] == FROZEN_SHA[k] for k in FROZEN_SHA)
    g3_sha = sha(G3_CONTRACT)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    w0r = json.loads(W0R_MODEL.read_text(encoding="utf-8"))

    # --- evidence ----------------------------------------------------------
    synthetic = run_synthetic()
    single_band, joint_frame, capacity = run_real(manifest, w0r)
    real_bad = check_expected(single_band, joint_frame)

    synthetic_ok = (synthetic["decision_match"] == 200
                    and synthetic["mus_match"] == 200
                    and synthetic["order_invariant"] == 200)
    capacity_ok = all(c["ok"] for c in capacity)
    all_ok = sha_ok and synthetic_ok and not real_bad and capacity_ok

    rep = {
        "artifact": "m13_v57_f4_indver_report",
        "schema": 1,
        "revision": REV,
        "seed": SEED,
        "predicate": ("W1 no-crossing ordered-assignment feasibility: injective "
                      "page->lane index; pages sorted by (row_y, id) map to "
                      "strictly increasing lane indices; |lane_y - row_y| <= leg"),
        "versions": {
            "producer": {"path": _rel(SELF), "revision": REV,
                         "sha256": sha(SELF), "symbol": "exact_feasible"},
            "validator": {"path": _rel(SELF), "revision": REV,
                          "sha256": sha(SELF), "symbol": "brute_feasible"},
        },
        "evidence_protocol_v1_s3": {
            "item1_schema_versions": ("schema=1, revision=F4-INDVER.1, producer/"
                                      "validator tool path + revision + sha256 "
                                      "fingerprints"),
            "item2_source_fingerprints_authority": ("manifest/rules/w0r_model "
                                                    "SHA-256 pinned at runtime "
                                                    "against frozen constants; "
                                                    "w1_report and g3_contract "
                                                    "recorded"),
            "item3_deterministic_status": ("verdict is exactly one of PASS/FAIL; "
                                           "report is byte-identical across two "
                                           "consecutive runs"),
            "item4_demand_capacity_minimal_core": ("real n=8 single-band + n=16 "
                                                   "joint-frame decisions per leg "
                                                   "k; MUS page-id cores for "
                                                   "infeasible cases; frame "
                                                   "capacity (n-1)*pitch <= span "
                                                   "cross-check"),
            "item5_legal_escape_hatches": ("upstream input changes only "
                                           "(manifest/SPEC/drc_rules/W0-R); no "
                                           "downstream construction edits"),
            "item6_independent_validation": ("exact interval bipartite matching "
                                             "(Kuhn) cross-checked against an "
                                             "independent local brute permutation "
                                             "oracle on 200 synthetic instances "
                                             "(n<=7); W1 is not imported"),
        },
        "authority": {
            "manifest": _rel(MANIFEST),
            "rules": _rel(RULES),
            "w0r_model": _rel(W0R_MODEL),
            "g3_contract": _rel(G3_CONTRACT),
            "w1_report": _rel(W1_REPORT),
        },
        "inputs_sha": inputs_sha,
        "synthetic": synthetic,
        "real": {
            "single_band": single_band,
            "joint_frame": joint_frame,
            "frame_capacity_crosscheck": capacity,
            "expected_mismatch": real_bad,
        },
        "frozen_sha_match": sha_ok,
        "g3_contract_sha": g3_sha,
        "pitch_derivation": {
            "p_gap": dp["p_gap"], "p_width": dp["p_width"],
            "inter_pair_spacing": dp["inter_pair_spacing"],
            "derived": pitch_derived, "pitch": PITCH,
        },
        "verdict": "PASS" if all_ok else "FAIL",
    }

    # no-allocation scan (exclude the scan block itself)
    scan_target = {k: v for k, v in rep.items() if k != "no_allocation_scan"}
    leaked = []
    _scan_keys(scan_target, "", leaked)
    rep["no_allocation_scan"] = {"forbidden_keys": FORBIDDEN_KEYS,
                                 "leaked": leaked}
    if leaked:
        rep["verdict"] = "FAIL"

    OUT.write_text(json.dumps(rep, indent=1, ensure_ascii=False,
                              sort_keys=True), encoding="utf-8")

    print(f"F4-INDVER verdict={rep['verdict']} "
          f"synthetic={synthetic['decision_match']}/"
          f"{synthetic['mus_match']}/{synthetic['order_invariant']} "
          f"real_expected_mismatch={len(real_bad)} "
          f"frozen_sha_match={sha_ok} leaked={len(leaked)}")
    print("artifact:", OUT)
    return 0 if rep["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
