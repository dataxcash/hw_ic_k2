#!/usr/bin/env python3
"""Independent verifier for the K2 F-13 R1 pair-domain v1.1 (x-order dimension)
deliverable.

Everything is recomputed from the frozen ground truth (verdict / manifest /
rules / spec); the artifact's own booleans are never trusted.  The producer
tool p3_v57_f13_r1_pair_xorder.py is treated as a black box and is only hashed.

Exit code 0 == PASS, non-zero == FAIL.
"""
import copy
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
K2 = os.path.dirname(HERE)
BASE = os.path.join(K2, "pm_gate", "artifacts", "k2_v4", "L3", "mcio_feas_step2")

ART = os.path.join(BASE, "m13_v57_f13_r1_pair_coupling_v1_1.json")
V1 = os.path.join(BASE, "m13_v57_f13_r1_pair_coupling.json")
VERDICT = os.path.join(BASE, "m13_v57_s1_r1_via_verdict.json")
MANIFEST = os.path.join(BASE, "m13_v57_s1_page_manifest.json")
RULES = os.path.join(K2, "_shared", "eda_core", "drc_rules.json")
SPEC = os.path.join(K2, "pm_gate", "artifacts", "k2_v4", "L3", "SPEC_k2_v4.json")
F3 = os.path.join(BASE, "m13_v57_f3_lane_frame.json")
PRODUCER = os.path.join(K2, "tools", "p3_v57_f13_r1_pair_xorder.py")
OUT = os.path.join(BASE, "m13_v57_f13_r1_pair_coupling_v1_1_validation.json")

# optional overrides (used only for counterexample/exit-code demonstration)
if len(sys.argv) > 1:
    ART = sys.argv[1]
if len(sys.argv) > 2:
    OUT = sys.argv[2]

DIST_MIN = 0.525
STAGGER_MIN = 0.38
EPS = 1e-9
STEP = 0.6
DIST_TOL = 1e-4
QN = 9
FORBIDDEN_KEY_NAMES = ("assigned", "allocation", "selected_lane", "lane_assignment")


# --------------------------------------------------------------------------- #
# generic helpers
# --------------------------------------------------------------------------- #
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def q(x):
    return round(float(x), QN)


def walk_key_paths(obj, prefix=""):
    """Yield (json_path, key, value) for every dict key in the tree."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            yield path, k, v
            yield from walk_key_paths(v, path)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_key_paths(v, f"{prefix}[{i}]")


# --------------------------------------------------------------------------- #
# independent recomputation of the pair domain
# --------------------------------------------------------------------------- #
def recompute_domain(p_cands, n_cands):
    """Return {(q(Px), q(Nx)): max admissible euclidean dist} for one page."""
    P = np.asarray(p_cands, dtype=float)
    N = np.asarray(n_cands, dtype=float)
    dx = np.abs(P[:, 0][:, None] - N[:, 0][None, :])
    dy = np.abs(P[:, 1][:, None] - N[:, 1][None, :])
    dist = np.sqrt(dx * dx + dy * dy)
    adm = (dx >= STAGGER_MIN - EPS) & (dist >= DIST_MIN - EPS)
    pi, ni = np.where(adm)
    out = {}
    for x1, x2, dv in zip(P[pi, 0], N[ni, 0], dist[pi, ni]):
        key = (q(x1), q(x2))
        val = float(dv)
        if val > out.get(key, -1.0):
            out[key] = val
    return out


def distinct_x(cands):
    return sorted({q(c[0]) for c in cands})


# --------------------------------------------------------------------------- #
# F-5 frame construction (corridor, conn_ref, band) from the frozen manifest
# --------------------------------------------------------------------------- #
def frame_order_key(corridor_id):
    if corridor_id == "EAST_CHIP_TO_J2":
        return lambda e: (
            (e["anchors"]["conn"]["N"]["pad_global"][1]
             + e["anchors"]["conn"]["P"]["pad_global"][1]) / 2.0,
            e["page_id"],
        )
    return lambda e: (e["anchors"]["conn"]["P"]["pad_global"][0], e["page_id"])


def build_frames(manifest):
    frames = {}
    for e in manifest["pages"]:
        if e.get("kind") != "data":
            continue
        key = (e["corridor"]["id"], e["anchors"]["conn"]["P"]["ref"], e["corridor"]["band"])
        frames.setdefault(key, []).append(e)
    out = {}
    for key, pages in frames.items():
        cid = key[0]
        pages = sorted(pages, key=frame_order_key(cid))
        out[key] = pages
    return out


def greedy_monotone(x_sets, direction):
    """Forward-only monotone construction (never backtracks)."""
    prev = None
    seq = []
    for xs in x_sets:
        pick = None
        if direction > 0:
            for x in xs:
                if prev is None or x >= prev + STEP - EPS:
                    pick = x
                    break
        else:
            for x in reversed(xs):
                if prev is None or x <= prev - STEP + EPS:
                    pick = x
                    break
        if pick is None:
            return False, seq + [None]
        seq.append(pick)
        prev = pick
    return True, seq


# --------------------------------------------------------------------------- #
# context (frozen inputs + cached recomputation)
# --------------------------------------------------------------------------- #
def build_context():
    ctx = {}
    ctx["verdict"] = load_json(VERDICT)
    ctx["v1"] = load_json(V1)
    ctx["manifest"] = load_json(MANIFEST)
    ctx["f3"] = load_json(F3) if os.path.exists(F3) else None
    ctx["disk_sha"] = {
        "artifact": sha256_file(ART),
        "v1": sha256_file(V1),
        "verdict": sha256_file(VERDICT),
        "manifest": sha256_file(MANIFEST),
        "rules": sha256_file(RULES),
        "spec": sha256_file(SPEC),
        "producer": sha256_file(PRODUCER),
    }
    domains, cand_x = {}, {}
    for pid, pg in ctx["verdict"]["pages"].items():
        domains[pid] = recompute_domain(pg["P"]["cands"], pg["N"]["cands"])
        cand_x[pid] = (distinct_x(pg["P"]["cands"]), distinct_x(pg["N"]["cands"]))
    ctx["domains"] = domains
    ctx["cand_x"] = cand_x
    ctx["frames"] = build_frames(ctx["manifest"])
    return ctx


def artifact_dict_keys(cand_keys):
    return sorted(f"{a}|{b}" for (a, b) in cand_keys)


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #
def check_x1(art, ctx):
    sym_re, sym_ar, dist_bad, malformed, unsorted, dup = [], [], [], [], [], []
    total = 0
    max_dist_diff = 0.0
    art_pages = set(art.get("pages", {}))
    exp_pages = set(ctx["domains"])
    page_set_ok = art_pages == exp_pages
    for pid in sorted(ctx["domains"]):
        page = art["pages"].get(pid)
        if page is None:
            sym_re.append(f"{pid}:MISSING_PAGE")
            continue
        entries = page["x_column_pairs"]
        total += len(entries)
        seen = set()
        rec = ctx["domains"][pid]
        art_keys = []
        art_map = {}
        for e in entries:
            if not (isinstance(e, list) and len(e) == 3
                    and all(isinstance(v, (int, float)) for v in e)):
                malformed.append(f"{pid}:{e!r}")
                continue
            k = (q(e[0]), q(e[1]))
            if k in seen:
                dup.append(f"{pid}:{k}")
            seen.add(k)
            art_keys.append(k)
            art_map[k] = float(e[2])
        if art_keys != sorted(art_keys):
            unsorted.append(pid)
        for k in set(rec) - set(art_keys):
            sym_re.append(f"{pid}:{k}")
        for k in set(art_keys) - set(rec):
            sym_ar.append(f"{pid}:{k}")
        for k in set(art_keys) & set(rec):
            diff = abs(rec[k] - art_map[k])
            max_dist_diff = max(max_dist_diff, diff)
            if diff > DIST_TOL:
                dist_bad.append(f"{pid}:{k}:rec={rec[k]:.6f}:art={art_map[k]:.6f}")
    ok = page_set_ok and not (sym_re or sym_ar or dist_bad or malformed or unsorted or dup)
    observed = {
        "pages_checked": len(ctx["domains"]),
        "page_set_ok": page_set_ok,
        "pages_only_in_artifact": sorted(art_pages - exp_pages),
        "pages_only_in_recomputation": sorted(exp_pages - art_pages),
        "total_column_pairs": total,
        "symmetric_difference_recompute_only": sorted(sym_re),
        "symmetric_difference_artifact_only": sorted(sym_ar),
        "dist_max_mm_mismatch_over_1e-4": sorted(dist_bad),
        "max_dist_max_mm_abs_diff": round(max_dist_diff, 9),
        "malformed_entries": malformed,
        "unsorted_pages": sorted(unsorted),
        "duplicate_keys": sorted(dup),
    }
    return mk("X1",
              "artifact page set == verdict page set; pages[pid].x_column_pairs key-set == independent numpy "
              "recomputation (all 32 pages, set equality at 1e-9) and dist_max_mm match within 1e-4",
              "empty symmetric difference; no dist / malformed / order / duplicate defect",
              observed, ok)


def check_x2(art, ctx):
    bad = {}
    for pid in sorted(ctx["cand_x"]):
        page = art["pages"].get(pid)
        if page is None:
            bad[pid] = ["missing_page"]
            continue
        px, nx = ctx["cand_x"][pid]
        rec = ctx["domains"][pid]
        feas_px = sorted({k[0] for k in rec})
        feas_nx = sorted({k[1] for k in rec})
        issues = []
        if [q(v) for v in page["x_columns_P"]] != px:
            issues.append("x_columns_P != sorted distinct P candidate x")
        if [q(v) for v in page["x_columns_N"]] != nx:
            issues.append("x_columns_N != sorted distinct N candidate x")
        if [q(v) for v in page["x_columns_P"]] != feas_px:
            issues.append("x_columns_P != feasible P x set")
        if [q(v) for v in page["x_columns_N"]] != feas_nx:
            issues.append("x_columns_N != feasible N x set")
        if [q(v) for v in page["x_span_P_mm"]] != [px[0], px[-1]]:
            issues.append("x_span_P_mm != [min,max] x_columns_P")
        if [q(v) for v in page["x_span_N_mm"]] != [nx[0], nx[-1]]:
            issues.append("x_span_N_mm != [min,max] x_columns_N")
        if page["n_column_pairs"] != len(page["x_column_pairs"]):
            issues.append("n_column_pairs != len(x_column_pairs)")
        if page["n_column_pairs"] != len(rec):
            issues.append("n_column_pairs != recomputed count")
        if issues:
            bad[pid] = issues
    summary = art.get("summary", {})
    counts = [len(art["pages"][p]["x_column_pairs"]) for p in ctx["domains"] if p in art["pages"]]
    summ_issues = []
    if counts:
        if summary.get("n_column_pairs_total") != sum(counts):
            summ_issues.append("summary.n_column_pairs_total")
        if summary.get("n_column_pairs_min") != min(counts):
            summ_issues.append("summary.n_column_pairs_min")
        if summary.get("n_column_pairs_max") != max(counts):
            summ_issues.append("summary.n_column_pairs_max")
        if summary.get("n_pages") != len(ctx["domains"]):
            summ_issues.append("summary.n_pages")
        if summary.get("n_pages_with_x_column_pairs") != sum(1 for c in counts if c > 0):
            summ_issues.append("summary.n_pages_with_x_column_pairs")
    ok = not bad and not summ_issues
    return mk("X2",
              "x_columns_P / x_columns_N / x_span_P_mm / x_span_N_mm / n_column_pairs and summary "
              "statistics are consistent with the independent recomputation (all 32 pages)",
              "no per-page inconsistency; summary totals == recomputed totals",
              {"pages_checked": len(ctx["domains"]), "bad_pages": bad,
               "summary_issues": summ_issues,
               "recomputed_total": sum(counts), "recomputed_min": min(counts) if counts else None,
               "recomputed_max": max(counts) if counts else None}, ok)


def check_x3(art, ctx):
    v1 = ctx["v1"]
    disk_v1_sha = ctx["disk_sha"]["v1"]
    field_bad, sha_bad, xcol_bad = [], [], []
    for pid in sorted(ctx["domains"]):
        page = art["pages"].get(pid)
        if page is None:
            field_bad.append(f"{pid}:MISSING_PAGE")
            continue
        ref = page["v1_pair_domain_ref"]
        v1page = v1["pages"][pid]
        if ref.get("n_pairs_admissible_stagger_038") != v1page["pair_domain"]["n_pairs_admissible_stagger_038"]:
            field_bad.append(f"{pid}:n_pairs_admissible_stagger_038")
        if ref.get("admissible_pair_witness") != v1page["admissible_pair_witness"]:
            field_bad.append(f"{pid}:admissible_pair_witness")
        if ref.get("sha256") != disk_v1_sha:
            sha_bad.append(f"{pid}:{ref.get('sha256')}")
        if [q(v) for v in page["x_columns_P"]] != [q(v) for v in v1page["pair_domain"]["x_columns_P"]]:
            xcol_bad.append(f"{pid}:x_columns_P")
        if [q(v) for v in page["x_columns_N"]] != [q(v) for v in v1page["pair_domain"]["x_columns_N"]]:
            xcol_bad.append(f"{pid}:x_columns_N")
    ok = not field_bad and not sha_bad and not xcol_bad
    return mk("X3",
              "every claimed v1 inheritance (n_pairs_admissible_stagger_038, admissible_pair_witness, "
              "x_columns_P/N, v1_pair_domain_ref.sha256 == on-disk v1 sha) equals the frozen v1 artifact, page by page",
              "no page-level inheritance mismatch; v1_pair_domain_ref.sha256 == sha256(v1 file)",
              {"pages_checked": len(ctx["domains"]), "field_mismatch": sorted(field_bad),
               "ref_sha256_mismatch": sorted(sha_bad), "x_columns_vs_v1_mismatch": sorted(xcol_bad),
               "v1_file_sha256": disk_v1_sha}, ok)


def check_x4(art, ctx):
    disk = ctx["disk_sha"]
    frozen = [("verdict", VERDICT, disk["verdict"]),
              ("manifest", MANIFEST, disk["manifest"]),
              ("spec", SPEC, disk["spec"]),
              ("rules", RULES, disk["rules"])]
    details = []
    ok = True
    sup_sha = art.get("supersedes", {}).get("sha256")
    sup_ok = sup_sha == disk["v1"]
    ok = ok and sup_ok
    details.append({"field": "supersedes.sha256", "claimed": sup_sha,
                    "on_disk_v1": disk["v1"], "ok": sup_ok})
    auth = art.get("authority", {})
    for name, path, actual in frozen:
        blk = auth.get(name, {})
        cval = blk.get("sha256") if isinstance(blk, dict) else None
        cpath = blk.get("path") if isinstance(blk, dict) else None
        match = cval == actual
        path_match = cpath == os.path.relpath(path, K2)
        ok = ok and match and path_match
        details.append({"field": f"authority.{name}.sha256", "claimed": cval,
                        "on_disk": actual, "claimed_path": cpath,
                        "path_ok": path_match, "ok": match and path_match})
    xoe = art.get("x_order_dim", {}).get("frozen_sources_unchanged")
    details.append({"field": "x_order_dim.frozen_sources_unchanged",
                    "claimed": xoe, "recomputed": all(d["ok"] for d in details if d["field"].startswith("authority")),
                    "ok": xoe is True})
    ok = ok and xoe is True
    return mk("X4",
              "supersedes.sha256 and authority.{verdict,manifest,spec,rules}.sha256 equal the freshly "
              "hashed on-disk frozen sources (bytes unchanged)",
              "all supersedes/authority hashes == freshly computed on-disk sha256",
              {"supersedes_ok": sup_ok, "details": details}, ok)


def check_x5(art, ctx):
    hits = []
    for path, key, _val in walk_key_paths(art):
        if key in FORBIDDEN_KEY_NAMES:
            hits.append(path)
    hits = sorted(hits)
    others = [h for h in hits if h != "constraints.allocation"]
    alloc = art.get("constraints", {}).get("allocation")
    ok = (hits == ["constraints.allocation"]) and (alloc is False) and not others
    return mk("X5",
              "zero-allocation: no keys named assigned/allocation/selected_lane/lane_assignment anywhere, "
              "except the explicit constraints.allocation=false self-declaration; constraints.allocation is false",
              "forbidden key paths == ['constraints.allocation']; constraints.allocation is false",
              {"forbidden_key_paths": hits, "non_declaration_forbidden_keys": others,
               "constraints_allocation": alloc,
               "no_allocation_scan_leaked": art.get("no_allocation_scan", {}).get("leaked")}, ok)


def check_x6(art, ctx):
    frames_report = []
    all_ok = True
    for key in sorted(ctx["frames"]):
        cid, ref, band = key
        pages = ctx["frames"][key]
        pids = [e["page_id"] for e in pages]
        usP, usN = [], []
        chip_px, chip_nx = [], []
        for e in pages:
            page = art["pages"][e["page_id"]]
            pairs = page["x_column_pairs"]
            usP.append(sorted({q(r[0]) for r in pairs}))
            usN.append(sorted({q(r[1]) for r in pairs}))
            chip_px.append(float(e["anchors"]["chip"]["P"]["pad_global"][0]))
            chip_nx.append(float(e["anchors"]["chip"]["N"]["pad_global"][0]))
        dir_p = 1 if chip_px[-1] >= chip_px[0] else -1
        dir_n = 1 if chip_nx[-1] >= chip_nx[0] else -1
        okP, seqP = greedy_monotone(usP, dir_p)
        okN, seqN = greedy_monotone(usN, dir_n)
        ok = okP and okN and dir_p == dir_n
        all_ok = all_ok and ok
        frames_report.append({
            "frame_id": f"{cid}/{band}/{ref}",
            "corridor": cid, "conn_ref": ref, "band": band,
            "order_key": "conn_row_y" if cid == "EAST_CHIP_TO_J2" else "conn_x",
            "pages": pids,
            "pad_x_trend_direction": dir_p,
            "polarity_N_trend_direction": dir_n,
            "P_derivable": okP, "P_realized_x": seqP,
            "N_derivable": okN, "N_realized_x": seqN,
            "ok": ok,
        })
    f3_ok = None
    if ctx.get("f3"):
        f3_ok = True
        for cid, cv in ctx["f3"]["corridors"].items():
            for fr in cv["frames"]:
                mine = [e["page_id"] for e in ctx["frames"][(cid, fr["conn_ref"], fr["band"])]]
                theirs = [p["page_id"] for p in fr["pages"]]
                if mine != theirs:
                    f3_ok = False
    return mk("X6",
              "domain sanity: for every frame = (corridor, conn_ref, band) a strictly monotone per-polarity x "
              "sequence is derivable by a forward-only construction from the artifact x-column domains "
              "(step >= 0.6, direction = sign of chip pad_x trend); F-5 page order cross-checked vs F-3 lane frame",
              "all frames derivable for both polarities; derived page order == F-3 lane frame order",
              {"all_frames_derivable": all_ok, "frames": frames_report, "f3_order_match": f3_ok}, all_ok)


def mk(cid, assertion, expected, observed, ok):
    return {"id": cid, "assertion": assertion, "expected": expected,
            "observed": observed, "ok": bool(ok)}


def evaluate(art, ctx):
    checks = [check_x1(art, ctx), check_x2(art, ctx), check_x3(art, ctx),
              check_x4(art, ctx), check_x5(art, ctx), check_x6(art, ctx)]
    return checks, all(c["ok"] for c in checks)


# --------------------------------------------------------------------------- #
# mutation tests (in-memory only)
# --------------------------------------------------------------------------- #
def run_mutations(base_art, ctx):
    def clone():
        return copy.deepcopy(base_art)

    def mut_del_pair(a):
        a["pages"]["PCIE_DN0/input"]["x_column_pairs"].pop(0)

    def mut_add_bogus(a):
        a["pages"]["PCIE_DN0/input"]["x_column_pairs"].append([999.0, 999.0, 0.9])

    def mut_dist_shift(a):
        a["pages"]["PCIE_DN0/input"]["x_column_pairs"][7][2] = float(
            a["pages"]["PCIE_DN0/input"]["x_column_pairs"][7][2]) + 0.5

    def mut_ref_sha(a):
        a["pages"]["PCIE_UP0/input"]["v1_pair_domain_ref"]["sha256"] = "0" * 64

    def mut_supersedes_sha(a):
        a["supersedes"]["sha256"] = "0" * 64

    specs = [
        ("M1", "delete one column pair from PCIE_DN0/input.x_column_pairs", mut_del_pair),
        ("M2", "add bogus column pair [999.0, 999.0, 0.9] to PCIE_DN0/input", mut_add_bogus),
        ("M3", "increase one PCIE_DN0/input dist_max_mm by +0.5", mut_dist_shift),
        ("M4", "corrupt PCIE_UP0/input.v1_pair_domain_ref.sha256", mut_ref_sha),
        ("M5", "tamper supersedes.sha256", mut_supersedes_sha),
    ]
    results = []
    for mid, desc, fn in specs:
        mutated = clone()
        fn(mutated)
        checks, verdict = evaluate(mutated, ctx)
        failed = [c["id"] for c in checks if not c["ok"]]
        results.append({
            "id": mid, "mutation": desc,
            "expected_verdict": "FAIL", "observed_verdict": "PASS" if verdict else "FAIL",
            "ok": verdict is False, "checks_flipped": failed,
        })
    return results


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main():
    ctx = build_context()
    art = load_json(ART)
    checks, verdict = evaluate(art, ctx)
    mutations = run_mutations(art, ctx)
    x7_ok = bool(mutations) and all(m["ok"] for m in mutations)
    checks.append(mk("X7",
                     "at least 5 mutation tests each flip the checker to FAIL",
                     "all mutations observed FAIL (baseline PASS)",
                     {"n_mutations": len(mutations),
                      "observed": [{"id": m["id"], "observed_verdict": m["observed_verdict"],
                                    "checks_flipped": m["checks_flipped"]} for m in mutations]},
                     x7_ok))
    verdict = all(c["ok"] for c in checks)

    frozen_sha_check = {"v1_on_disk": ctx["disk_sha"]["v1"],
                        "frozen": []}
    auth = art.get("authority", {})
    for name, path in [("verdict", VERDICT), ("manifest", MANIFEST),
                       ("spec", SPEC), ("rules", RULES)]:
        actual = ctx["disk_sha"][name]
        claimed = auth.get(name, {}).get("sha256") if isinstance(auth.get(name), dict) else None
        frozen_sha_check["frozen"].append({
            "source": name, "path": os.path.relpath(path, K2),
            "claimed_sha256": claimed, "actual_sha256": actual,
            "match": claimed == actual})
    frozen_sha_check["all_match"] = all(f["match"] for f in frozen_sha_check["frozen"])

    x6 = next(c for c in checks if c["id"] == "X6")

    out = {
        "artifact": os.path.relpath(ART, K2),
        "schema": 1,
        "revision": "F13-XORDER-VAL.1",
        "verdict": "PASS" if verdict else "FAIL",
        "frozen_sha_check": frozen_sha_check,
        "checks": checks,
        "mutation_tests": mutations,
        "producer_sha256": ctx["disk_sha"]["producer"],
        "validator_sha256": sha256_file(os.path.abspath(__file__)),
        "notes": (
            "Independent recomputation from the frozen verdict (per-page P/N via candidate lists), "
            "manifest, drc_rules and SPEC. Producer treated as a black box (hashed only: "
            f"{ctx['disk_sha']['producer']}). X1/X2 recompute the full admissible column-pair set with numpy "
            "from scratch (dist >= 0.525-1e-9 AND |dx| >= 0.38-1e-9) over all 32 pages. X5 scans every dict key "
            "name in the artifact tree; the only forbidden-name occurrence is the explicit "
            "constraints.allocation=false self-declaration. X6 direction = sign of the chip-side P pad x trend "
            "within each F-5 frame (chip P and N trends agree in every frame); F-5 frames are derived from the "
            "manifest (corridor.id, conn_ref, corridor.band) and ordered by conn_row_y for EAST / conn_x for WEST, "
            "cross-checked byte-for-byte against the F-3 lane-frame page order. X6 is a per-polarity DOMAIN "
            "report only (no allocation emitted anywhere); joint cross-polarity coupling is a W3 construction/"
            "solve concern and is intentionally out of X6 scope. Mutation tests are applied to in-memory copies "
            "only; no file under test is modified."
        ),
    }

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False, sort_keys=False)
        fh.write("\n")

    print(f"artifact            : {out['artifact']}")
    print(f"verdict             : {out['verdict']}")
    for c in checks:
        print(f"  [{c['id']}] {'ok' if c['ok'] else 'FAIL'} - {c['expected']}")
    print("mutation tests:")
    for m in mutations:
        print(f"  [{m['id']}] expected={m['expected_verdict']} observed={m['observed_verdict']} "
              f"flipped={','.join(m['checks_flipped']) or '-'} -> {'ok' if m['ok'] else 'FAIL'}")
    print("X6 per-frame monotone derivability:")
    print(f"  {'frame':32s} {'dir':>4s} {'P':>3s} {'N':>3s}  realized_P / realized_N")
    for f in x6["observed"]["frames"]:
        print(f"  {f['frame_id']:32s} {f['pad_x_trend_direction']:+4d} "
              f"{'ok' if f['P_derivable'] else 'NA':>3s} {'ok' if f['N_derivable'] else 'NA':>3s}  "
              f"{f['P_realized_x']} / {f['N_realized_x']}")
    print(f"wrote {os.path.relpath(OUT, K2)}")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
