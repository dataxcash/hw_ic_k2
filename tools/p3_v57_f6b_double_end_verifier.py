#!/usr/bin/env python3
"""P3 v57 — F6B-DE: independent verifier for the G3 v1 §3 / F-6 DOUBLE-END
reach predicate.

Predicate (G3 v1.1 §3 / F-6, exact)
-----------------------------------
Instance = pages [(id, conn_row_y, chip_row_y)] + lanes [y] + leg.
A page's lane index i is allowed iff BOTH ends are within leg:
    |L[i] - conn_row_y| <= leg + 1e-9   AND   |L[i] - chip_row_y| <= leg + 1e-9
Feasible iff there is an INJECTIVE page -> lane-index assignment such that pages
sorted by (conn_row_y, page_id) map to STRICTLY INCREASING lane indices
(no crossing), and every page uses an allowed lane.

Why the increasing-constraint DP is REQUIRED (not bipartite matching)
--------------------------------------------------------------------
In the single-end predicate each page's allowed lane-index set is a contiguous
interval with monotone endpoints, so a maximum matching exists iff a
non-crossing assignment exists (the classical uncrossing argument).  Under the
DOUBLE-END predicate the allowed set is the intersection of two distance
intervals:
    [conn-leg, conn+leg]  ∩  [chip-leg, chip+leg]
Because chip_row_y varies independently of conn_row_y (in the joint frame a
page's chip row can even DECREASE while conn row increases), the allowed sets
are NOT intervals with monotone endpoints, and the uncrossing / bipartite
matching equivalence does NOT hold.  A matching can exist while no strictly
increasing assignment exists.  Therefore this verifier uses the exact
increasing-constraint reachability DP (reachable-last-lane-index frontier) which
is exact for the ordered (no-crossing) feasibility question.

The DP returns a bool ONLY; it never emits the assignment, matching, witness or
lane list ("no allocation output").

Independent small-n reference
-----------------------------
`brute_feasible` enumerates strictly increasing lane-index tuples (permutation
enumeration, n <= 7) directly against the double-end predicate.  It is used to
self-cross-check 200 deterministic synthetic double-end instances.

This module is stdlib-only and does NOT import the F4 or W1 tools.
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
W0R_MODEL = STEP / "m13_v57_big_w0r_corridor_model.json"
RULES = K2 / "_shared" / "eda_core" / "drc_rules.json"
G3_V1_1 = STEP / "m13_v57_g3_freeze_contract_v1_1_frame_ruling.md"
G3_V1_2 = STEP / "m13_v57_g3_freeze_contract_v1_2_lane_domain.md"
D0_CARD = STEP / "m13_v57_d0_decision_card.md"

OUT = STEP / "m13_v57_f6b_report.json"

REV = "F6B-DE.1"
SEED = 20260909
PITCH = 1.46
MARGIN = 0.0
KS = [1, 2, 3, 5]
LEG_K5 = 7.3

FROZEN_SHA = {
    "manifest": "a8ef3ea8ecff99d7549d4122043c972c1bb68346dc4dcc3f36fdd9bacde49890",
    "w0r_model": "80ee9adb78a7e9ad94c27d426295592eee21af3d1e3ce88fe3042183160f0efa",
    "rules": "0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448",
    "g3_v1_1": "232fda852ee8612be3f2bf2c4655d0aa716c408dfb71a8eb71df298b08c031ff",
    "g3_v1_2": "c8f380c184976fb5072e3afc6d47f25a5e6221de46c21aa67bd8cf1e20bd16b6",
    "d0_card": "a69cc7f5eedab2a19fa6ad5be55e100e1163da71d274ad540192d35b9bfdf79d",
}

FORBIDDEN_KEYS = ["selected", "assigned", "allocation", "witness"]

ESCAPE_HATCHES = [
    "add corridor y (extend usable_y_spans span)",
    "reduce pairs (reduce n)",
    "widen R1.5 chip-side transition zone (increase effective leg)",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rel(path: Path) -> str:
    return str(path.relative_to(K2))


# --------------------------------------------------------------------------
# exact engine: increasing-constraint reachability DP
# --------------------------------------------------------------------------
def _allowed_idx(lanes, conn, chip, leg):
    """Allowed lane indices for one double-end page."""
    return {i for i, y in enumerate(lanes)
            if abs(y - conn) <= leg + 1e-9 and abs(y - chip) <= leg + 1e-9}


def exact_feasible(pages, lanes, leg):
    """Exact double-end ordered-assignment feasibility (bool ONLY).

    Pages are sorted by (conn_row_y, page_id); lanes ascending.  `reach` is the
    set of lane indices at which the current prefix can end.  A lane j is a
    valid new frontier iff it is allowed for the current page and some earlier
    reachable index i < j exists (strictly increasing => no crossing).
    """
    ps = sorted(pages, key=lambda p: (p[1], p[0]))
    L = sorted(lanes)
    reach = set()
    for _pid, conn, chip in ps:
        a = _allowed_idx(L, conn, chip, leg)
        if not reach:
            reach = a
        else:
            reach = {j for j in a if any(i < j for i in reach)}
        if not reach:
            return False
    return bool(reach)


def brute_feasible(pages, lanes, leg):
    """Independent small-n reference: full permutation enumeration of strictly
    increasing lane-index tuples (n <= 7) under the double-end predicate."""
    L = sorted(lanes)
    ps = sorted(pages, key=lambda p: (p[1], p[0]))
    n = len(ps)
    if n > len(L):
        return False
    for perm in itertools.permutations(range(len(L)), n):
        if any(perm[i] >= perm[i + 1] for i in range(n - 1)):
            continue
        if all(abs(L[perm[i]] - ps[i][1]) <= leg + 1e-9
               and abs(L[perm[i]] - ps[i][2]) <= leg + 1e-9
               for i in range(n)):
            return True
    return False


def mus(pages, lanes, leg, engine):
    """Minimal unsatisfiable subset — byte-identical convention: cardinality
    ascending, then id-tuple lexicographic; first infeasible subset = unique
    inclusion-minimal core."""
    ids = sorted(p[0] for p in pages)
    for card in range(1, len(ids) + 1):
        for combo in itertools.combinations(ids, card):
            sub = [p for p in pages if p[0] in set(combo)]
            if not engine(sub, lanes, leg):
                return list(combo)
    return None


def min_leg(pages, lanes, lo=0.0, hi=200.0):
    """Minimal leg leg* making the frame feasible (binary search, exact DP).

    Monotone in leg.  For a case infeasible at `leg` the threshold lies in
    (leg, 200], so searching [0, 200] yields the same leg* as [leg, 200] while
    being computable once per frame (a frame property, identical for all k).
    """
    for _ in range(100):
        mid = (lo + hi) / 2.0
        if exact_feasible(pages, lanes, mid):
            hi = mid
        else:
            lo = mid
    return round(hi, 3)


# --------------------------------------------------------------------------
# 200 synthetic double-end self-cross-check (deterministic recipe, seed)
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
        pages = []
        for k in range(n):
            conn = round(rng.choice(lanes)
                         + rng.choice([-3.0, -1.5, -0.5, 0.0, 0.5, 1.5, 3.0]), 3)
            chip = round(rng.choice(lanes)
                         + rng.choice([-3.0, -1.5, -0.5, 0.0, 0.5, 1.5, 3.0]), 3)
            pages.append((f"P{k}", conn, chip))

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
# real frames (EAST/WEST x up/dn/joint)
# --------------------------------------------------------------------------
def _page_conn_row(page):
    a = page["anchors"]["conn"]
    return round((a["P"]["pad_global"][1] + a["N"]["pad_global"][1]) / 2, 3)


def _page_chip_row(page):
    a = page["anchors"]["chip"]
    return round((a["P"]["pad_global"][1] + a["N"]["pad_global"][1]) / 2, 3)


def _lane_domain(span):
    return [round(span[0] + i * PITCH, 3)
            for i in range(int((span[1] - span[0]) // PITCH) + 1)]


def run_real(manifest, w0r):
    pages_by_id = {p["page_id"]: p for p in manifest["pages"]}
    single_band, joint_frame, certificates = [], [], []

    for cid in sorted(w0r["corridors"]):
        corridor = w0r["corridors"][cid]
        span = corridor["usable_y_spans"][0]
        lanes = _lane_domain(span)
        band_pages = {}

        for band in ("up", "dn"):
            band_obj = corridor["data_bands"][band]
            pages = [(pid, _page_conn_row(pages_by_id[pid]),
                      _page_chip_row(pages_by_id[pid]))
                     for pid in band_obj["page_ids"]]
            band_pages[band] = pages
            leg_star = min_leg(pages, lanes)
            chips = [p[2] for p in pages]
            reach_band = round((max(chips) + LEG_K5) - (min(chips) - LEG_K5), 3)
            req_band = round((len(pages) - 1) * PITCH, 3)

            for k in KS:
                leg = round(k * PITCH, 3)
                feas = exact_feasible(pages, lanes, leg)
                entry = {"corridor": cid, "frame": band, "n": len(pages),
                         "k": k, "leg": leg, "feasible": feas,
                         "reachable_band_mm": reach_band,
                         "required_band_mm": req_band}
                if not feas:
                    core = mus(pages, lanes, leg, exact_feasible)
                    short = round(max(0.0, leg_star - leg), 3)
                    entry.update({"mus": core, "required_leg_mm": leg_star,
                                  "short_mm": short,
                                  "escape_hatches": list(ESCAPE_HATCHES)})
                    certificates.append({
                        "corridor": cid, "frame": band, "k": k,
                        "n": len(pages), "leg": leg, "mus": core,
                        "required_leg_mm": leg_star, "short_mm": short,
                        "escape_hatches": list(ESCAPE_HATCHES),
                        "reachable_band_mm": reach_band,
                        "required_band_mm": req_band})
                single_band.append(entry)

        joint = [p for band in ("up", "dn") for p in band_pages[band]]
        leg_star = min_leg(joint, lanes)
        chips = [p[2] for p in joint]
        reach_band = round((max(chips) + LEG_K5) - (min(chips) - LEG_K5), 3)
        req_band = round((len(joint) - 1) * PITCH, 3)
        for k in KS:
            leg = round(k * PITCH, 3)
            feas = exact_feasible(joint, lanes, leg)
            entry = {"corridor": cid, "frame": "joint", "n": len(joint),
                     "k": k, "leg": leg, "feasible": feas,
                     "reachable_band_mm": reach_band,
                     "required_band_mm": req_band}
            if not feas:
                core = mus(joint, lanes, leg, exact_feasible)
                short = round(max(0.0, leg_star - leg), 3)
                entry.update({"mus": core, "required_leg_mm": leg_star,
                              "short_mm": short,
                              "escape_hatches": list(ESCAPE_HATCHES)})
                certificates.append({
                    "corridor": cid, "frame": "joint", "k": k,
                    "n": len(joint), "leg": leg, "mus": core,
                    "required_leg_mm": leg_star, "short_mm": short,
                    "escape_hatches": list(ESCAPE_HATCHES),
                    "reachable_band_mm": reach_band,
                    "required_band_mm": req_band})
            joint_frame.append(entry)

    return single_band, joint_frame, certificates


# expected real decisions (§8 self-verify table); k order = [1,2,3,5]
EXPECTED = {
    ("EAST_CHIP_TO_J2", "up"): {1: False, 2: False, 3: False, 5: True},
    ("EAST_CHIP_TO_J2", "dn"): {1: False, 2: False, 3: False, 5: True},
    ("EAST_CHIP_TO_J2", "joint"): {1: False, 2: False, 3: False, 5: False},
    ("WEST_MCIO_TO_CHIP", "up"): {1: False, 2: False, 3: False, 5: False},
    ("WEST_MCIO_TO_CHIP", "dn"): {1: False, 2: False, 3: False, 5: False},
    ("WEST_MCIO_TO_CHIP", "joint"): {1: False, 2: False, 3: False, 5: False},
}

# expected k=5 MUS cores (§8); None = feasible (no MUS)
EXPECTED_MUS_K5 = {
    ("EAST_CHIP_TO_J2", "joint"): (
        ["PCIE_DN%d/input" % i for i in range(8)]
        + ["PCIE_UP%d/out_J2" % i for i in range(4)]),
    ("WEST_MCIO_TO_CHIP", "up"): ["PCIE_UP4/input", "PCIE_UP5/input"],
    ("WEST_MCIO_TO_CHIP", "dn"): ["PCIE_DN%d/out_MCIO" % i for i in range(4, 8)],
    ("WEST_MCIO_TO_CHIP", "joint"): ["PCIE_UP4/input", "PCIE_UP5/input"],
}


def check_expected(single_band, joint_frame):
    seen, mus5 = {}, {}
    for e in list(single_band) + list(joint_frame):
        seen.setdefault((e["corridor"], e["frame"]), {})[e["k"]] = e["feasible"]
        if e["k"] == 5:
            mus5[(e["corridor"], e["frame"])] = e.get("mus")
    bad = []
    for key, exp in EXPECTED.items():
        got = seen.get(key)
        if got != exp:
            bad.append({"key": list(key), "expected": exp, "got": got})
    for key, exp in EXPECTED_MUS_K5.items():
        got = mus5.get(key)
        if got != exp:
            bad.append({"key": list(key), "kind": "k5_mus",
                        "expected": exp, "got": got})
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
    pitch_derived = round(dp["p_gap"] + 2 * dp["p_width"]
                          + dp["inter_pair_spacing"], 3)
    assert abs(pitch_derived - PITCH) < 1e-12, (
        f"pitch authority drift: derived {pitch_derived} != {PITCH}")

    # --- frozen fingerprints (fail on drift) ------------------------------
    inputs_sha = {
        "manifest": sha(MANIFEST),
        "w0r_model": sha(W0R_MODEL),
        "rules": sha(RULES),
        "g3_v1_1": sha(G3_V1_1),
        "g3_v1_2": sha(G3_V1_2),
        "d0_card": sha(D0_CARD),
    }
    sha_ok = all(inputs_sha[k] == FROZEN_SHA[k] for k in FROZEN_SHA)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    w0r = json.loads(W0R_MODEL.read_text(encoding="utf-8"))

    # --- evidence ----------------------------------------------------------
    synthetic = run_synthetic()
    single_band, joint_frame, certificates = run_real(manifest, w0r)
    real_bad = check_expected(single_band, joint_frame)

    synthetic_ok = (synthetic["decision_match"] == 200
                    and synthetic["mus_match"] == 200
                    and synthetic["order_invariant"] == 200)
    all_ok = sha_ok and synthetic_ok and not real_bad

    rep = {
        "artifact": "m13_v57_f6b_report",
        "schema": 1,
        "revision": REV,
        "seed": SEED,
        "predicate": ("G3 v1 §3 / F-6 double-end reach: injective page->lane "
                      "index; pages sorted by (conn_row_y, page_id) map to "
                      "strictly increasing lane indices; "
                      "|lane_y - conn_row_y| <= leg AND "
                      "|lane_y - chip_row_y| <= leg"),
        "versions": {
            "producer": {"path": _rel(SELF), "revision": REV,
                         "sha256": sha(SELF), "symbol": "exact_feasible"},
            "validator": {"path": _rel(SELF), "revision": REV,
                          "sha256": sha(SELF), "symbol": "brute_feasible"},
        },
        "evidence_protocol_v1_s3": {
            "item1_schema_versions": ("schema=1, revision=F6B-DE.1, producer/"
                                      "validator tool path + revision + sha256 "
                                      "fingerprints"),
            "item2_source_fingerprints_authority": ("manifest/w0r_model/rules/"
                                                    "g3_v1_1/g3_v1_2/d0_card "
                                                    "SHA-256 pinned at runtime "
                                                    "against frozen constants; "
                                                    "full 64-hex recorded"),
            "item3_deterministic_status": ("verdict is exactly one of PASS/FAIL; "
                                           "report is byte-identical across two "
                                           "consecutive runs"),
            "item4_demand_capacity_minimal_core": ("real n=8 single-band + n=16 "
                                                   "joint-frame double-end "
                                                   "decisions per leg k; MUS "
                                                   "page-id cores + required_leg"
                                                   "_mm/short_mm certificates "
                                                   "for infeasible cases; "
                                                   "reachable_band_mm vs "
                                                   "required_band_mm context"),
            "item5_legal_escape_hatches": ("upstream input changes only (add "
                                           "corridor y / reduce pairs / widen "
                                           "R1.5 chip-side transition zone); no "
                                           "downstream construction edits"),
            "item6_independent_validation": ("exact increasing-constraint DP "
                                             "cross-checked against an "
                                             "independent local brute "
                                             "permutation oracle on 200 "
                                             "synthetic double-end instances "
                                             "(n<=7); no F4/W1 import"),
        },
        "authority": {
            "manifest": _rel(MANIFEST),
            "w0r_model": _rel(W0R_MODEL),
            "rules": _rel(RULES),
            "g3_v1_1": _rel(G3_V1_1),
            "g3_v1_2": _rel(G3_V1_2),
            "d0_card": _rel(D0_CARD),
        },
        "inputs_sha": inputs_sha,
        "synthetic": synthetic,
        "real": {
            "single_band": single_band,
            "joint_frame": joint_frame,
            "certificates": certificates,
            "expected_mismatch": real_bad,
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

    print(f"F6B-DE verdict={rep['verdict']} "
          f"synthetic={synthetic['decision_match']}/"
          f"{synthetic['mus_match']}/{synthetic['order_invariant']} "
          f"real_expected_mismatch={len(real_bad)} "
          f"frozen_sha_match={sha_ok} leaked={len(leaked)} "
          f"certificates={len(certificates)}")
    print("artifact:", OUT)
    return 0 if rep["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
