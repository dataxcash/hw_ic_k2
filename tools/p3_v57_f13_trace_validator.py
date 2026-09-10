#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Independent adversarial validator for the F-13-R1TRACE deliverable
(m13_v57_f13_r1_param_trace.json + m13_v57_f13_r1_pair_coupling.json).

Independence contract (per m13_v57_f13_r1_param_trace_boundary.md):
  * the F-13 producer tool is NEVER imported and NEVER executed; it is
    treated as a black box and touched only to record its sha256 identity;
  * every numeric / structural fact is re-derived from the frozen read-only
    sources with this file's own parsing and numpy computation;
  * the frozen sources are opened read-only; nothing outside this validator
    and its emitted validation json is written.

Exit code: 0 iff verdict == "PASS", else 1.
The emitted report is byte deterministic (sort_keys=True + trailing newline),
so two consecutive runs must produce a byte-identical file.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import traceback
from pathlib import Path

import numpy as np

# --------------------------------------------------------------------------
# constants
# --------------------------------------------------------------------------
REVISION = "F13-VAL.1"
SCHEMA = 1
SEED = 0                  # fixed determinism seed; no RNG is used
TOL = 1e-9                # exactness tolerance for candidate/witness arrays
NUM_TOL = 1e-12           # tolerance for scalar constant identities
ROUND4_TOL = 5e-5         # frozen rounding of dist_min/dist_max (4 decimals)

FORBIDDEN_KEYS = ("assigned", "allocation", "selected_lane", "lane_assignment")
# the only permitted occurrence of a forbidden token: the explicit false
# declaration pair["field_spec"]["allocation"] (mandated by check C5).
ALLOCATION_DECL_PATH = ("field_spec", "allocation")

ROOT = Path(__file__).resolve().parent.parent

SPEC_P = ROOT / "pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.json"
MANIFEST_P = ROOT / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_s1_page_manifest.json"
RULES_P = ROOT / "_shared/eda_core/drc_rules.json"
VERDICT_P = ROOT / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_s1_r1_via_verdict.json"
TRACE_P = ROOT / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_f13_r1_param_trace.json"
PAIR_P = ROOT / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_f13_r1_pair_coupling.json"
# producer is referenced ONLY for its file hash (black-box identity); no import.
PRODUCER_P = ROOT / "tools/p3_v57_f13_r1_param_trace.py"
OUT_P = ROOT / "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_f13_r1_param_trace_validation.json"

SQL = "sqrt(dx^2+dy^2)"  # documentation of the distance computation used below


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(Path(p).read_bytes())


def load_json(p: Path):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def close(a, b, tol=NUM_TOL) -> bool:
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return a == b


def resolve_ptr(doc, ptr: str):
    """Resolve a tiny JSON-pointer dialect: /a/b and list selectors a[NAME]."""
    cur = doc
    for tok in [t for t in ptr.split("/") if t != ""]:
        if "[" in tok and tok.endswith("]"):
            key = tok[: tok.index("[")]
            sel = tok[tok.index("[") + 1 : -1]
            cur = cur[key]
            if isinstance(cur, list):
                if sel.lstrip("-").isdigit():
                    cur = cur[int(sel)]
                else:
                    hit = None
                    for e in cur:
                        if isinstance(e, dict) and e.get("name") == sel:
                            hit = e
                            break
                    if hit is None:
                        raise KeyError(f"selector {sel!r} not found in {key!r}")
                    cur = hit
            else:
                cur = cur[sel]
        else:
            cur = cur[tok]
    return cur


def parse_source(src: str):
    """Split a producer source string into (file_token, json_pointer)."""
    parts = src.split(None, 1)
    fname = parts[0]
    ptr = None
    if len(parts) > 1:
        for tok in parts[1].split():
            if tok.startswith("/"):
                ptr = tok
                break
    return fname, ptr


FILE_KEY = {"SPEC_k2_v4.json": "spec", "drc_rules.json": "rules"}


def walk_keys(obj, path=()):
    """Yield (path_tuple, value) for every dict key in the tree."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield path + (k,), v
            yield from walk_keys(v, path + (k,))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_keys(v, path + (i,))


# --------------------------------------------------------------------------
# C1 - frozen fingerprints
# --------------------------------------------------------------------------
def check_c1(trace, pair, computed):
    expected = trace.get("frozen_sha_check", {}).get("expected", {})
    actual = trace.get("frozen_sha_check", {}).get("actual", {})
    match = trace.get("frozen_sha_check", {}).get("match", {})
    pair_inputs = pair.get("inputs_sha", {})
    pair_verdict_sha = pair.get("authority", {}).get("verdict_sha256")
    trace_verdict_sha = trace.get("verdict_artifact", {}).get("sha256")

    keys = ("spec", "manifest", "rules", "verdict")
    drift = [
        k
        for k in keys
        if not (
            expected.get(k) == computed[k]
            and actual.get(k) == computed[k]
        )
    ]
    structural = (
        sorted(expected) == sorted(keys)
        and sorted(actual) == sorted(keys)
        and sorted(match) == sorted(keys)
        and all(match.get(k) is True for k in keys)
        and trace.get("frozen_sha_check", {}).get("drift") == []
        and pair_inputs == computed
        and pair_verdict_sha == computed["verdict"]
        and trace_verdict_sha == computed["verdict"]
    )
    ok = (not drift) and structural
    observed = {
        "recomputed": {k: computed[k] for k in keys},
        "trace_expected": expected,
        "trace_actual": actual,
        "trace_match": match,
        "trace_drift_field": trace.get("frozen_sha_check", {}).get("drift"),
        "pair_inputs_sha": pair_inputs,
        "pair_authority_verdict_sha256": pair_verdict_sha,
        "trace_verdict_artifact_sha256": trace_verdict_sha,
        "recomputed_drift": drift,
        "structural_ok": structural,
    }
    return {
        "id": "C1",
        "assertion": "four frozen sha256 (SPEC/manifest/rules/verdict) recomputed and equal to FROZEN_SHA declared inside trace and pair_coupling; drift == []",
        "expected": "all four 64-hex equal in trace.expected, trace.actual, pair.inputs_sha, pair.authority.verdict_sha256; match all true; drift []",
        "observed": observed,
        "ok": bool(ok),
    }


# --------------------------------------------------------------------------
# C2 - parameter mapping re-derivation
# --------------------------------------------------------------------------
def check_c2(trace, pair, docs, computed):
    spec, rules = docs["spec"], docs["rules"]
    spec_outer = spec["vias"]["std"]["outer"]
    rules_min_via = rules["manufacturing"]["min_via_diameter"]
    power_clr = next(
        e["clearance"] for e in rules["clearance"]["net_classes"] if e["name"] == "POWER"
    )
    pcie_clr = spec["net_classes"]["PCIe85"]["clearance"]
    board_min = rules["clearance"]["board_min"]
    p_gap = spec["net_classes"]["PCIe85"]["diff_pair"]["p_gap"]
    p_width = spec["net_classes"]["PCIe85"]["diff_pair"]["p_width"]

    entries = {e.get("param"): e for e in trace.get("params_mapping", [])}
    problems = []

    # (i) every entry: holds true, and every listed source sha256 + value correct
    for e in trace.get("params_mapping", []):
        pname = e.get("param")
        if e.get("holds") is not True:
            problems.append(f"{pname}: holds != true")
        srcs = e.get("sources", [])
        if not isinstance(srcs, list) or not srcs:
            problems.append(f"{pname}: no sources")
        for s in srcs:
            fname, ptr = parse_source(s.get("source", ""))
            key = FILE_KEY.get(fname)
            if s.get("sha256") is None:
                # design reference: must not masquerade as a frozen file source
                if key is not None:
                    problems.append(f"{pname}: null sha but frozen source {fname}")
                elif not isinstance(s.get("value"), str):
                    problems.append(f"{pname}: null sha with non-string value")
                continue
            if key is None:
                problems.append(f"{pname}: unknown source file {fname!r}")
                continue
            if s.get("sha256") != computed[key]:
                problems.append(
                    f"{pname}: source sha mismatch for {s.get('source')!r} "
                    f"({s.get('sha256')} != {computed[key]})"
                )
            if ptr is None:
                problems.append(f"{pname}: no json pointer in {s.get('source')!r}")
                continue
            try:
                resolved = resolve_ptr(docs[key], ptr)
            except Exception as exc:  # noqa: BLE001
                problems.append(f"{pname}: pointer {ptr!r} unresolved ({exc})")
                continue
            if isinstance(s.get("value"), str):
                if not isinstance(resolved, str):
                    problems.append(f"{pname}: expected rule_text, got {resolved!r}")
            elif not close(resolved, s.get("value")):
                problems.append(
                    f"{pname}: source value mismatch at {ptr!r} "
                    f"({s.get('value')} != {resolved})"
                )

    # (ii) re-derived parameter identities
    ident = []
    if "via_od" in entries:
        v = entries["via_od"]["value"]
        ident.append(("via_od==0.35", close(v, 0.35) and close(spec_outer, 0.35) and close(rules_min_via, 0.35)))
    else:
        ident.append(("via_od present", False))

    if "clr" in entries:
        v = entries["clr"]["value"]
        ident.append((
            "clr==POWER 0.2 >= PCIe85 0.175 >= board_min 0.1",
            close(v, 0.2) and close(power_clr, 0.2) and close(pcie_clr, 0.175)
            and close(board_min, 0.1) and v >= pcie_clr >= board_min,
        ))
    else:
        ident.append(("clr present", False))

    if "via_via" in entries:
        v = entries["via_via"]["value"]
        ident.append(("via_via==via_od+pcie_clr==0.525", close(v, 0.525) and close(spec_outer + pcie_clr, 0.525)))
    else:
        ident.append(("via_via present", False))

    if "col_pair_stagger_min" in entries:
        e = entries["col_pair_stagger_min"]
        v = e["value"]
        binding = e.get("derived_binding")
        ident.append((
            "col_pair_stagger_min==0.36 and binding==max(0.36,p_gap+p_width)==0.38",
            close(v, 0.36) and close(binding, 0.38) and close(max(0.36, p_gap + p_width), 0.38),
        ))
    else:
        ident.append(("col_pair_stagger_min present", False))

    params_ok = all(x[1] for x in ident)
    ok = (not problems) and params_ok
    return {
        "id": "C2",
        "assertion": "re-derive parameter mapping from raw SPEC/rules: via_od, clr (POWER==0.2 >= PCIe85 0.175 >= board_min 0.1), via_via==0.35+0.175==0.525, col_pair_stagger_min 0.36/binding 0.38; all holds true; every source sha256+value correct",
        "expected": "4/4 params hold; 0 source discrepancies",
        "observed": {
            "params_found": sorted(k for k in entries if k is not None),
            "identities": [{"name": n, "ok": bool(v)} for n, v in ident],
            "problems": problems,
            "n_params": len(entries),
            "n_holds_true": sum(1 for e in trace.get("params_mapping", []) if e.get("holds") is True),
        },
        "ok": bool(ok),
    }


# --------------------------------------------------------------------------
# C3 - column-stagger caliber identities
# --------------------------------------------------------------------------
def check_c3(trace, pair, docs):
    spec = docs["spec"]
    p_width = spec["net_classes"]["PCIe85"]["diff_pair"]["p_width"]      # 0.205
    p_gap = spec["net_classes"]["PCIe85"]["diff_pair"]["p_gap"]          # 0.175

    id1 = close(0.36 - p_width, 0.155)          # 0.36 - 0.205 == 0.155
    id2 = close((p_gap + p_width) - p_width, 0.175)  # (0.175+0.205)-0.205 == 0.175

    gc = trace.get("governing_constants", {})
    pc_con = pair.get("constraints", {})
    declared = (
        close(gc.get("col_stagger_design_text_mm"), 0.36)
        and close(gc.get("p_gap_mm"), p_gap)
        and close(gc.get("track_width_mm"), p_width)
        and close(pc_con.get("col_stagger_design_text_mm"), 0.36)
        and close(pc_con.get("design_text_edge_clearance_mm"), 0.155)
        and close(pc_con.get("leg_edge_clearance_mm"), 0.175)
    )
    ok = id1 and id2 and declared
    return {
        "id": "C3",
        "assertion": "column-stagger caliber identities: 0.36-p_width==0.155 and (p_gap+p_width)-p_width==0.175, with p_width=0.205, p_gap=0.175 from SPEC PCIe85",
        "expected": "0.36-0.205==0.155 and (0.175+0.205)-0.205==0.175; constraints 0.36/0.155/0.175 recorded",
        "observed": {
            "p_width": p_width,
            "p_gap": p_gap,
            "0.36-0.205": 0.36 - p_width,
            "0.36-0.205==0.155": bool(id1),
            "(0.175+0.205)-0.205": (p_gap + p_width) - p_width,
            "(0.175+0.205)-0.205==0.175": bool(id2),
            "trace_governing_constants_ok": bool(declared),
            "pair_constraints": pc_con,
        },
        "ok": bool(ok),
    }


# --------------------------------------------------------------------------
# C4 - pair-domain recomputation (numpy, own implementation)
# --------------------------------------------------------------------------
def build_page_arrays(verdict):
    pages = {}
    for pid, vp in verdict["pages"].items():
        P = np.asarray(vp["P"]["cands"], dtype=np.float64)
        N = np.asarray(vp["N"]["cands"], dtype=np.float64)
        pages[pid] = (P, N)
    return pages


def count_domain(P, N, dist_min, stagger):
    dx = np.abs(P[:, None, 0] - N[None, :, 0])
    dy = np.abs(P[:, None, 1] - N[None, :, 1])
    dist = np.hypot(dx, dy)
    dist_ok = dist >= dist_min
    return dx, dist, dist_ok, dist_ok & (dx >= stagger)


def check_c4(trace, pair, docs):
    verdict = docs["verdict"]
    spec = docs["spec"]
    rules = docs["rules"]
    p_width = spec["net_classes"]["PCIe85"]["diff_pair"]["p_width"]
    p_gap = spec["net_classes"]["PCIe85"]["diff_pair"]["p_gap"]
    dist_min = pair["constraints"]["dist_min_mm"]              # 0.525
    stagger_binding = pair["constraints"]["col_stagger_mm"]     # 0.38
    stagger_text = pair["constraints"]["col_stagger_design_text_mm"]  # 0.36

    # cross-check the constraints themselves against raw sources
    derived_dist_min = spec["vias"]["std"]["outer"] + spec["net_classes"]["PCIe85"]["clearance"]
    derived_binding = max(stagger_text, p_gap + p_width)
    constraint_ok = (
        close(dist_min, derived_dist_min)
        and close(stagger_binding, derived_binding)
        and close(stagger_text, 0.36)
        and close(rules["clearance"]["net_classes"][0]["clearance"], 0.175)
    )

    arrays = build_page_arrays(verdict)
    vpages = verdict["pages"]

    mismatches = []
    count_rows = []
    adm38_pages = 0
    adm36_pages = 0
    total_adm38 = 0
    for pid in sorted(vpages):
        P, N = arrays[pid]
        dx, dist, dist_ok, adm38 = count_domain(P, N, dist_min, stagger_binding)
        _, _, _, adm36 = count_domain(P, N, dist_min, stagger_text)
        n_dist = int(dist_ok.sum())
        n36 = int(adm36.sum())
        n38 = int(adm38.sum())
        total_adm38 += n38
        adm38_pages += 1 if n38 > 0 else 0
        adm36_pages += 1 if n36 > 0 else 0
        pd = pair["pages"][pid]["pair_domain"]
        got = (
            pd.get("n_pairs_dist_ok"),
            pd.get("n_pairs_admissible_stagger_036"),
            pd.get("n_pairs_admissible_stagger_038"),
        )
        want = (n_dist, n36, n38)
        if got != want:
            mismatches.append({"page": pid, "expected": list(want), "observed": list(got)})
        count_rows.append((pid, want))

    counts_ok = (not mismatches) and (len(count_rows) == 32) and constraint_ok

    # summary recomputation
    summ = pair.get("summary", {})
    verdict_pair_stagger_ok_036 = 0
    for pid, vp in vpages.items():
        Pv = np.asarray(vp["pair"][0], dtype=np.float64)
        Nv = np.asarray(vp["pair"][1], dtype=np.float64)
        if abs(Pv[0] - Nv[0]) >= stagger_text:
            verdict_pair_stagger_ok_036 += 1
    summ_expected = {
        "n_pages": len(vpages),
        "n_pages_with_admissible_pair_stagger_036": adm36_pages,
        "n_pages_with_admissible_pair_stagger_038": adm38_pages,
        "n_verdict_pairs_stagger_036_ok": verdict_pair_stagger_ok_036,
        "n_verdict_pairs_total": len(vpages),
    }
    summ_observed = {k: summ.get(k) for k in summ_expected}
    summary_ok = summ_observed == summ_expected

    observed_counts = {
        "pages_compared": len(count_rows),
        "counts_per_page": 3,
        "mismatches": mismatches,
        "constraints_ok": bool(constraint_ok),
        "derived_constraints": {
            "dist_min_mm": derived_dist_min,
            "col_stagger_binding_mm": derived_binding,
            "col_stagger_design_text_mm": stagger_text,
        },
    }
    row = {
        "id": "C4",
        "assertion": "recompute 32x3 pair-domain counts (n_pairs_dist_ok / admissible_stagger_036 / admissible_stagger_038) with own numpy implementation and compare exactly",
        "expected": "32 pages x 3 counts identical to pair_coupling.pages[pid].pair_domain",
        "observed": observed_counts,
        "ok": bool(counts_ok),
    }

    row_sum = {
        "id": "C4-summary",
        "assertion": "recompute pair_coupling.summary counts",
        "expected": summ_expected,
        "observed": summ_observed,
        "ok": bool(summary_ok),
    }

    # ---- witnesses ----
    wit_problems = []
    min_margin = None
    for pid in sorted(vpages):
        P, N = arrays[pid]
        w = pair["pages"][pid].get("admissible_pair_witness")
        if not isinstance(w, dict):
            wit_problems.append(f"{pid}: missing witness")
            continue
        wP = np.asarray(w.get("P"), dtype=np.float64)
        wN = np.asarray(w.get("N"), dtype=np.float64)
        if wP.shape != (2,) or wN.shape != (2,):
            wit_problems.append(f"{pid}: witness shape bad")
            continue
        # in frozen cands (L-inf tolerance = TOL)
        mP = float(np.min(np.max(np.abs(P - wP[None, :]), axis=1)))
        mN = float(np.min(np.max(np.abs(N - wN[None, :]), axis=1)))
        for m in (mP, mN):
            min_margin = m if min_margin is None else min(min_margin, m)
        inP = mP <= TOL
        inN = mN <= TOL
        dx = abs(float(wP[0] - wN[0]))
        dist = float(np.hypot(wP[0] - wN[0], wP[1] - wN[1]))
        dual = (dist >= dist_min - TOL) and (dx >= stagger_binding - TOL)
        # declared rounded fields
        decl_dist_ok = close(w.get("dist_mm"), round(dist, 4), 1e-9)
        decl_stg_ok = close(w.get("stagger_mm"), round(dx, 4), 1e-9)
        if not (inP and inN and dual and decl_dist_ok and decl_stg_ok):
            wit_problems.append(
                f"{pid}: inP={inP} inN={inN} dual={dual} dist={dist} dx={dx}"
            )
    wit_ok = not wit_problems and min_margin is not None
    row_wit = {
        "id": "C4-witness",
        "assertion": "every admissible_pair_witness satisfies dist>=0.525 AND |dx|>=0.38 and lies in the frozen cands lists (tolerance 1e-9)",
        "expected": "32/32 witnesses valid; smallest coordinate tolerance margin reported",
        "observed": {
            "witnesses_checked": len(vpages),
            "problems": wit_problems,
            "smallest_tolerance_margin": min_margin,
            "tolerance": TOL,
        },
        "ok": bool(wit_ok),
    }

    # ---- verdict_pair ----
    vp_problems = []
    vp_stagger038_ok = 0
    for pid, vp in sorted(vpages.items()):
        vpd = pair["pages"][pid].get("verdict_pair", {})
        fP = np.asarray(vp["pair"][0], dtype=np.float64)
        fN = np.asarray(vp["pair"][1], dtype=np.float64)
        dP = np.asarray(vpd.get("P"), dtype=np.float64)
        dN = np.asarray(vpd.get("N"), dtype=np.float64)
        dx = abs(float(fP[0] - fN[0]))
        dist = float(np.hypot(fP[0] - fN[0], fP[1] - fN[1]))
        if not (dP.shape == (2,) and dN.shape == (2,)):
            vp_problems.append(f"{pid}: verdict_pair shape bad")
            continue
        good = (
            np.all(np.abs(dP - fP) <= TOL)
            and np.all(np.abs(dN - fN) <= TOL)
            and close(vpd.get("dist_mm"), round(dist, 4), 1e-9)
            and close(vpd.get("stagger_mm"), round(dx, 4), 1e-9)
            and bool(vpd.get("dist_ok")) == (dist >= dist_min)
            and bool(vpd.get("stagger_ok_036")) == (dx >= stagger_text)
            and bool(vpd.get("stagger_ok_038")) == (dx >= stagger_binding)
        )
        if vpd.get("stagger_ok_038"):
            vp_stagger038_ok += 1
        if not good:
            vp_problems.append(f"{pid}: verdict_pair mismatch")
    row_vp = {
        "id": "C4-verdictpair",
        "assertion": "verdict_pair P/N coordinates equal the frozen verdict page pair coordinates; derived dist/stagger flags recomputed",
        "expected": "32/32 exact coordinate match and consistent dist_ok/stagger_ok flags",
        "observed": {
            "pairs_checked": len(vpages),
            "problems": vp_problems,
            "recomputed_stagger_ok_038": vp_stagger038_ok,
            "summary_stagger_036_ok": verdict_pair_stagger_ok_036,
        },
        "ok": bool(not vp_problems),
    }

    # ---- extra frozen rounded fields: dist_hist / min / max / x columns ----
    extra_problems = []
    margin_to_threshold = None
    for pid in sorted(vpages):
        P, N = arrays[pid]
        dx, dist, dist_ok, adm38 = count_domain(P, N, dist_min, stagger_binding)
        pd = pair["pages"][pid]["pair_domain"]
        for t, key in ((0.525, "0.525"), (0.6, "0.600"), (0.8, "0.800"), (1.0, "1.000")):
            # producer histogram conditions on the column-stagger constraint too:
            # count(dist >= t AND |dx| >= 0.38) == (adm38 & dist>=t).sum()
            want = int((adm38 & (dist >= t)).sum())
            if pd.get("dist_hist_mm", {}).get(key) != want:
                extra_problems.append(f"{pid}: dist_hist_mm[{key}]")
        if dist_ok.any():
            adm_dist = dist[adm38]
            if adm_dist.size:
                dmin = float(adm_dist.min())
                dmax = float(adm_dist.max())
                if not close(pd.get("dist_min_mm"), round(dmin, 4), ROUND4_TOL):
                    extra_problems.append(f"{pid}: dist_min_mm {pd.get('dist_min_mm')} != {round(dmin,4)}")
                if not close(pd.get("dist_max_mm"), round(dmax, 4), ROUND4_TOL):
                    extra_problems.append(f"{pid}: dist_max_mm")
        # smallest margin of any pair distance to the 0.525 threshold
        m = float(np.abs(dist - dist_min).min())
        margin_to_threshold = m if margin_to_threshold is None else min(margin_to_threshold, m)
        xsP = sorted({float(x) for x in P[:, 0]})
        xsN = sorted({float(x) for x in N[:, 0]})
        if not (
            np.all(np.abs(np.asarray(pd.get("x_columns_P", []), dtype=float) - np.asarray(xsP)) <= TOL)
            and np.all(np.abs(np.asarray(pd.get("x_columns_N", []), dtype=float) - np.asarray(xsN)) <= TOL)
        ):
            extra_problems.append(f"{pid}: x_columns")
    row_extra = {
        "id": "C4-extra",
        "assertion": "frozen derived fields dist_hist_mm / dist_min_mm / dist_max_mm / x_columns_P/N recomputed",
        "expected": "all 32 pages consistent (dist_min/max rounded 4dp)",
        "observed": {
            "problems": extra_problems,
            "smallest_abs(dist-0.525)": margin_to_threshold,
        },
        "ok": bool(not extra_problems),
    }
    return [row, row_sum, row_wit, row_vp, row_extra]


# --------------------------------------------------------------------------
# C5 - zero allocation
# --------------------------------------------------------------------------
def check_c5(trace, pair):
    hits_t, hits_p = [], []
    for path, val in walk_keys(trace):
        if path and path[-1] in FORBIDDEN_KEYS:
            hits_t.append((path, val if not isinstance(val, (dict, list)) else type(val).__name__))
    for path, val in walk_keys(pair):
        if path and path[-1] in FORBIDDEN_KEYS:
            hits_p.append((path, val if not isinstance(val, (dict, list)) else type(val).__name__))

    allowed = [h for h in hits_p if h[0] == ALLOCATION_DECL_PATH and h[1] is False]
    leaks = [h for h in hits_t if h[0] != ALLOCATION_DECL_PATH]
    leaks += [h for h in hits_p if h[0] != ALLOCATION_DECL_PATH]

    decl = pair.get("field_spec", {}).get("allocation", None)
    decl_ok = decl is False
    leaked_field = trace.get("no_allocation_scan", {}).get("leaked", None)
    leaked_field_ok = leaked_field == []
    ok = (not leaks) and decl_ok and leaked_field_ok and len(allowed) == 1
    return {
        "id": "C5",
        "assertion": "zero allocation: no forbidden key (assigned/allocation/selected_lane/lane_assignment) anywhere except the explicit false field_spec.allocation declaration",
        "expected": "leaks==[] and pair.field_spec.allocation is false",
        "observed": {
            "forbidden_hits_trace": [[list(p), v] for p, v in hits_t],
            "forbidden_hits_pair": [[list(p), v] for p, v in hits_p],
            "permitted_declaration": [[list(p), v] for p, v in allowed],
            "field_spec_allocation": decl,
            "trace_no_allocation_scan_leaked": leaked_field,
        },
        "ok": bool(ok),
    }


# --------------------------------------------------------------------------
# C6 - F-13 scope: frozen verdict result unchanged
# --------------------------------------------------------------------------
def check_c6(trace, docs, computed):
    verdict = docs["verdict"]
    va = trace.get("verdict_artifact", {})
    verdict_sha = computed["verdict"]
    params_ok = verdict.get("params") == va.get("params_as_frozen")
    n_pages_ok = verdict.get("n_pages") == va.get("n_pages") == 32
    n_esc_ok = verdict.get("n_escapable") == va.get("n_escapable") == 32
    inputs_ok = verdict.get("inputs_sha") == va.get("inputs_sha_as_frozen")
    sha_ok = va.get("sha256") == verdict_sha
    unchanged_ok = va.get("verdict_result_unchanged") is True
    ok = params_ok and n_pages_ok and n_esc_ok and inputs_ok and sha_ok and unchanged_ok
    return {
        "id": "C6",
        "assertion": "F-13 scope: frozen verdict file bytes re-hashed and n_pages/n_escapable/params match trace.verdict_artifact; verdict result unchanged",
        "expected": "sha matches; n_pages==32; n_escapable==32; params=={clr:0.2,via_od:0.35,via_via:0.525}; inputs_sha unchanged",
        "observed": {
            "recomputed_verdict_sha256": verdict_sha,
            "trace_verdict_artifact_sha256": va.get("sha256"),
            "verdict_n_pages": verdict.get("n_pages"),
            "verdict_n_escapable": verdict.get("n_escapable"),
            "trace_n_pages": va.get("n_pages"),
            "trace_n_escapable": va.get("n_escapable"),
            "verdict_params": verdict.get("params"),
            "trace_params_as_frozen": va.get("params_as_frozen"),
            "verdict_inputs_sha": verdict.get("inputs_sha"),
            "trace_inputs_sha_as_frozen": va.get("inputs_sha_as_frozen"),
            "verdict_result_unchanged": va.get("verdict_result_unchanged"),
        },
        "ok": bool(ok),
    }


# --------------------------------------------------------------------------
# X1 - manifest cross-check (extra evidence)
# --------------------------------------------------------------------------
def check_x1(pair, docs):
    manifest = docs["manifest"]
    m = {p.get("page_id"): p for p in manifest.get("pages", [])}
    problems = []
    for pid, pg in pair.get("pages", {}).items():
        mp = m.get(pid)
        if mp is None:
            problems.append(f"{pid}: missing from manifest")
            continue
        if mp.get("kind") != pg.get("kind") or mp.get("side") != pg.get("side"):
            problems.append(f"{pid}: kind/side mismatch")
    data_pages = sum(1 for p in manifest.get("pages", []) if p.get("kind") == "data")
    ok = not problems and data_pages == len(pair.get("pages", {}))
    return {
        "id": "X1-manifest",
        "assertion": "pair_coupling page ids/kind/side consistent with frozen s1_page_manifest; page set == manifest data pages",
        "expected": "32 data pages, 0 mismatches",
        "observed": {"problems": problems, "manifest_data_pages": data_pages, "pair_pages": len(pair.get("pages", {}))},
        "ok": bool(ok),
    }


# --------------------------------------------------------------------------
# core evaluation
# --------------------------------------------------------------------------
def core_checks(trace, pair, docs, computed):
    rows = []
    rows.append(check_c1(trace, pair, computed))
    rows.append(check_c2(trace, pair, docs, computed))
    rows.append(check_c3(trace, pair, docs))
    rows.extend(check_c4(trace, pair, docs))
    rows.append(check_c5(trace, pair))
    rows.append(check_c6(trace, docs, computed))
    rows.append(check_x1(pair, docs))
    return rows


# --------------------------------------------------------------------------
# C7 - in-memory mutation tests
# --------------------------------------------------------------------------
def _find_param(trace, name):
    for e in trace.get("params_mapping", []):
        if e.get("param") == name:
            return e
    raise KeyError(name)


MUTATIONS = [
    ("MUT-A", "trace.params_mapping[via_via].value 0.525 -> 0.5"),
    ("MUT-B", "trace.params_mapping[clr] POWER source value 0.2 -> 0.19"),
    ("MUT-C", "pair_coupling.pages[PCIE_DN0/input].pair_domain.n_pairs_admissible_stagger_038 += 1"),
    ("MUT-D", "pair_coupling.pages[PCIE_DN0/input].admissible_pair_witness.N -> [0.0, 0.0] (not in cands)"),
    ("MUT-E", "trace.frozen_sha_check.actual.spec -> 64x'0' (corrupt frozen sha)"),
]


def apply_mutation(mid, trace, pair):
    t = copy.deepcopy(trace)
    p = copy.deepcopy(pair)
    if mid == "MUT-A":
        _find_param(t, "via_via")["value"] = 0.5
    elif mid == "MUT-B":
        e = _find_param(t, "clr")
        hit = False
        for s in e.get("sources", []):
            if "net_classes[POWER]" in str(s.get("source", "")):
                s["value"] = 0.19
                hit = True
        if not hit:
            raise RuntimeError("MUT-B could not find POWER source")
    elif mid == "MUT-C":
        pg = p["pages"]["PCIE_DN0/input"]["pair_domain"]
        pg["n_pairs_admissible_stagger_038"] = pg["n_pairs_admissible_stagger_038"] + 1
    elif mid == "MUT-D":
        p["pages"]["PCIE_DN0/input"]["admissible_pair_witness"]["N"] = [0.0, 0.0]
    elif mid == "MUT-E":
        t["frozen_sha_check"]["actual"]["spec"] = "0" * 64
    else:
        raise KeyError(mid)
    return t, p


def run_mutation_tests(trace, pair, docs, computed):
    out = []
    for mid, desc in MUTATIONS:
        try:
            t2, p2 = apply_mutation(mid, trace, pair)
            rows = core_checks(t2, p2, docs, computed)
            failing = [r["id"] for r in rows if not r["ok"]]
            observed = "FAIL" if failing else "PASS"
            out.append({
                "id": mid,
                "mutation": desc,
                "expected_verdict": "FAIL",
                "observed_verdict": observed,
                "ok": observed == "FAIL",
                "failing_checks": failing,
            })
        except Exception as exc:  # noqa: BLE001
            out.append({
                "id": mid,
                "mutation": desc,
                "expected_verdict": "FAIL",
                "observed_verdict": "ERROR",
                "ok": False,
                "failing_checks": [f"error: {exc}"],
            })
    c7 = {
        "id": "C7",
        "assertion": "at least 5 in-memory mutations each flip the independent checker to FAIL",
        "expected": f"{len(MUTATIONS)}/5 rejected (observed_verdict FAIL)",
        "observed": {
            "n_mutations": len(MUTATIONS),
            "n_rejected": sum(1 for m in out if m["ok"]),
            "outcomes": [{k: m[k] for k in ("id", "observed_verdict", "failing_checks")} for m in out],
        },
        "ok": all(m["ok"] for m in out) and len(out) >= 5,
    }
    return c7, out


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main() -> int:
    docs = {
        "spec": load_json(SPEC_P),
        "manifest": load_json(MANIFEST_P),
        "rules": load_json(RULES_P),
        "verdict": load_json(VERDICT_P),
    }
    trace = load_json(TRACE_P)
    pair = load_json(PAIR_P)
    computed = {
        "spec": sha256_file(SPEC_P),
        "manifest": sha256_file(MANIFEST_P),
        "rules": sha256_file(RULES_P),
        "verdict": sha256_file(VERDICT_P),
    }
    producer_sha = sha256_file(PRODUCER_P)
    validator_sha = sha256_file(Path(__file__).resolve())

    rows = core_checks(trace, pair, docs, computed)
    c7, muts = run_mutation_tests(trace, pair, docs, computed)
    rows.append(c7)

    # tolerance-margin evidence row (C4-witness already carries it; keep a flat row)
    wit_row = next(r for r in rows if r["id"] == "C4-witness")
    tol_row = {
        "id": "TOL-1e-9",
        "assertion": "candidate/witness coordinate comparison uses tolerance 1e-9; smallest observed margin reported",
        "expected": "smallest observed L-inf margin <= 1e-9 (witness coords drawn from cands)",
        "observed": {
            "tolerance": TOL,
            "smallest_observed_margin": wit_row["observed"]["smallest_tolerance_margin"],
        },
        "ok": (wit_row["observed"]["smallest_tolerance_margin"] is not None
               and wit_row["observed"]["smallest_tolerance_margin"] <= TOL),
    }
    rows.append(tol_row)

    verdict = "PASS" if all(r["ok"] for r in rows) else "FAIL"

    fs_expected = trace.get("frozen_sha_check", {}).get("expected", {})
    fs_match = {k: fs_expected.get(k) == computed.get(k) for k in ("spec", "manifest", "rules", "verdict")}
    fs_drift = [k for k, v in fs_match.items() if not v]

    report = {
        "artifact": "m13_v57_f13_r1_param_trace_validation",
        "schema": SCHEMA,
        "revision": REVISION,
        "verdict": verdict,
        "frozen_sha_check": {
            "expected": fs_expected,
            "actual": computed,
            "match": fs_match,
            "drift": fs_drift,
        },
        "checks": rows,
        "producer_sha256": producer_sha,
        "validator_sha256": validator_sha,
        "seed": SEED,
        "mutation_tests": muts,
        "notes": (
            "Independent adversarial validator (F13-VAL.1). The producer "
            "The F-13 producer tool was NOT imported, executed, or read for logic; "
            "only its sha256 is recorded (producer_sha256). All numeric facts are re-derived "
            "from the frozen read-only sources (SPEC_k2_v4.json, drc_rules.json, "
            "m13_v57_s1_page_manifest.json, m13_v57_s1_r1_via_verdict.json) with this file's own "
            f"parsing and numpy (distance = {SQL}). Coordinate comparisons use tolerance {TOL:g}; "
            "scalar constant identities use " + f"{NUM_TOL:g}. seed={SEED} is a fixed determinism "
            "constant; no RNG is used. C5 nuance: the token 'allocation' appears exactly once, as the "
            "mandated declaration pair.field_spec.allocation == false; every other occurrence of the "
            "forbidden keys is treated as a leak. C4-extra validates producer-rounded fields "
            "(dist_min_mm/dist_max_mm to 4 decimals, tolerance " + f"{ROUND4_TOL:g}). "
            "Mutations are applied to in-memory deep copies only; the real artifacts are never written."
        ),
    }

    OUT_P.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_P, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")

    print(f"verdict={verdict} checks={sum(1 for r in rows if r['ok'])}/{len(rows)} "
          f"mutations={sum(1 for m in muts if m['ok'])}/{len(muts)} -> {OUT_P}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        sys.exit(2)
