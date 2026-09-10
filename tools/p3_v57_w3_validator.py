#!/usr/bin/env python3
"""Independent adversarial validator for the W3 (G4) joint assignment.

Written from contract card **W3-C1 v1.1** (``m13_v57_w3_kickoff_card_v1_1.md``,
sha256 4555f8b6...) and the frozen inputs it names.  It does NOT import
``p3_v57_w3_joint_assign.py`` and does not copy its code; the engine is only
executed as a black box (``subprocess``) for the order-invariance check.

v1.1 deltas handled here:
  * A-W3.1 (72/72) is conditional on verdict == FEASIBLE_ALL; under
    verdict == CERTIFICATE each gap must be certificate-attributed (A-W3.6).
  * R3 landing rule is F-8 ``y_band``: landing = (gap column x, y) with
    y in entries[*].y_band (pad_y +/- half_row); same gap column |dy| >= 0.525.
    The superseded strict rule (y := pad y) is retained as ``strict_rule_finding``
    evidence.
  * R2 assignment is corridor-nested; objective = {objective_mm, per_corridor}.

Usage:
    python3 tools/p3_v57_w3_validator.py                 # verify the real artifact
    python3 tools/p3_v57_w3_validator.py --artifact P --out Q --no-probe

Exit status is 0 iff every check passes (verdict PASS), else 1.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
import time
from pathlib import Path

EPS = 1e-9
TOL6 = 1e-6
PITCH = 1.46
LANE_BASE = 33.3
N_POS = 32
VIA_MIN = 0.525
REFCLK_MIN = 1.46
REACH = 45.4
N_CONNECTOR_PADS = 72
N_DATA_PAGES = 32
N_REFCLK_PAGES = 2
VAL_REV = "W3-VAL.2"

SELF = Path(__file__).resolve()
K2 = SELF.parents[1]
L3 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3"
STEP = L3 / "mcio_feas_step2"

CARD = STEP / "m13_v57_w3_kickoff_card_v1_1.md"
CARD_V1 = STEP / "m13_v57_w3_kickoff_card.md"
CARD_SHA = "4555f8b65abeb1a3a1743002f91f9ddbd2bda2462a1480d87bde23dedadc4ed2"
CARD_V1_SHA = "97a8084bb73f3af2b6996d58e616354c1941f2dc1b507e88725abe7a26f84a97"
ARTIFACT_DEFAULT = STEP / "m13_v57_w3_joint_assignment.json"
LANDING = STEP / "m13_v57_w3_chip_landing_rows.json"
VALIDATION_DEFAULT = STEP / "m13_v57_w3_validation.json"
ENGINE = K2 / "tools" / "p3_v57_w3_joint_assign.py"

INPUTS = [
    ("spec", L3 / "SPEC_k2_v4.json", "0bd52ed48e720b8c"),
    ("rules", K2 / "_shared" / "eda_core" / "drc_rules.json", "0a459839e15960b8"),
    ("manifest", STEP / "m13_v57_s1_page_manifest.json", "a8ef3ea8ecff99d7"),
    ("w0r_model", STEP / "m13_v57_big_w0r_corridor_model.json", "80ee9adb78a7e9ad"),
    ("lane_frame", STEP / "m13_v57_f3_lane_frame.json", "ff804e1edfacbf02"),
    ("param_trace", STEP / "m13_v57_f13_r1_param_trace.json", "e288ffa5421c2297"),
    ("pair_coupling", STEP / "m13_v57_f13_r1_pair_coupling.json", "82e11c4cbdb4e8d4"),
    ("r3_gaps", STEP / "m13_v57_f8_r3_gap_candidates.json", "8a31632907b17148"),
    ("f6b_report", STEP / "m13_v57_f6b_report.json", "9070ed53f970f480"),
]
CORR = ["EAST_CHIP_TO_J2", "WEST_MCIO_TO_CHIP"]
FORBIDDEN_R4 = ["capacitor_walls", "wall_pad", "wall gap", "wall_gap",
                "downstream_refs", "upstream_refs"]


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(p: Path):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def dg(d, *keys, default=None):
    cur = d
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur


def num(x):
    if isinstance(x, bool):
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def approx(a, b, tol=TOL6):
    return a is not None and b is not None and abs(a - b) <= tol


def dist2d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def seg_intersect(a, b, c, d):
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    def on_seg(p, q, r):
        return (min(p[0], r[0]) - EPS <= q[0] <= max(p[0], r[0]) + EPS and
                min(p[1], r[1]) - EPS <= q[1] <= max(p[1], r[1]) + EPS)

    o1, o2 = orient(a, b, c), orient(a, b, d)
    o3, o4 = orient(c, d, a), orient(c, d, b)
    if ((o1 > EPS > o2) or (o1 < -EPS < o2)) and \
       ((o3 > EPS > o4) or (o3 < -EPS < o4)):
        return True
    if abs(o1) <= EPS and on_seg(a, c, b):
        return True
    if abs(o2) <= EPS and on_seg(a, d, b):
        return True
    if abs(o3) <= EPS and on_seg(c, a, d):
        return True
    if abs(o4) <= EPS and on_seg(c, b, d):
        return True
    return False


def polyline_crossings(path_a, path_b):
    n = 0
    for i in range(len(path_a) - 1):
        for j in range(len(path_b) - 1):
            if seg_intersect(path_a[i], path_a[i + 1],
                             path_b[j], path_b[j + 1]):
                n += 1
    return n


# --------------------------------------------------------------------------
# frozen-input re-derivation
# --------------------------------------------------------------------------
def derive_manifest_pages(manifest):
    recs = {}
    for pg in dg(manifest, "pages", default=[]):
        conn = dg(pg, "anchors", "conn", default={})
        chip = dg(pg, "anchors", "chip", default={})
        rec = {"page_id": pg.get("page_id"), "kind": pg.get("kind"),
               "side": pg.get("side"), "corridor": dg(pg, "corridor", "id"),
               "band": dg(pg, "corridor", "band"),
               "conn_ref": dg(conn, "P", "ref") or dg(conn, "N", "ref"),
               "conn_x": None, "conn_row_y": None, "chip_row_y": None}
        if dg(conn, "P", "pad_global") and dg(conn, "N", "pad_global"):
            rec["conn_row_y"] = (conn["P"]["pad_global"][1] +
                                 conn["N"]["pad_global"][1]) / 2.0
            rec["conn_x"] = (conn["P"]["pad_global"][0] +
                             conn["N"]["pad_global"][0]) / 2.0
        if dg(chip, "P", "pad_global") and dg(chip, "N", "pad_global"):
            rec["chip_row_y"] = (chip["P"]["pad_global"][1] +
                                 chip["N"]["pad_global"][1]) / 2.0
        recs[rec["page_id"]] = rec
    return recs


def f5_order(cid, page_recs):
    """Contract F-5 (G3 v1 §2): row_y=(N.y+P.y)/2; WEST framed by conn_ref, key
    (conn_ref, row_y) + in-frame conn_x asc -> (conn_ref, row_y, conn_x, page_id)."""
    pages = [r for r in page_recs.values()
             if r["corridor"] == cid and r["kind"] == "data"]
    pages.sort(key=lambda r: (r["conn_ref"], round(r["conn_row_y"], 3),
                              round(r["conn_x"], 3), r["page_id"]))
    return pages


def alt_orders(cid, page_recs):
    pages = [r for r in page_recs.values()
             if r["corridor"] == cid and r["kind"] == "data"]
    refs = sorted({r["conn_ref"] for r in pages})
    lit = sorted(pages, key=lambda r: (r["conn_ref"], r["conn_x"], r["page_id"]))
    band = []
    for b in ("up", "dn"):
        for ref in refs:
            mem = [r for r in pages if r["band"] == b and r["conn_ref"] == ref]
            mem.sort(key=lambda r: (r["conn_x"], r["page_id"]))
            band += mem
    return {"literal_(conn_ref,conn_x)": lit, "file_order_band_major": band}


def lane_positions(lane_frame):
    pos = dg(lane_frame, "corridors", "EAST_CHIP_TO_J2", "lane_domain", "positions")
    if not pos:
        raise ValueError("lane_frame lane_domain.positions missing")
    return [float(v) for v in pos]


def connector_pads(f8):
    """ref -> list of pad dicts with F-8 gap_candidates and y_band."""
    out = {}
    for ref, cinfo in dg(f8, "connectors", default={}).items():
        pads = []
        for col_x, col in dg(cinfo, "columns", default={}).items():
            for e in dg(col, "entries", default=[]):
                yb = e.get("y_band")
                pads.append({"ref": ref, "col_x": float(col_x),
                             "y": float(e["y"]), "net": e["net"],
                             "pol": e.get("pol"), "kind": e.get("kind"),
                             "pad_num": e.get("pad_num"), "page": e.get("page"),
                             "cands": [float(g) for g in e.get("gap_candidates", [])],
                             "y_band": [float(yb[0]), float(yb[1])] if yb else None})
        out[ref] = pads
    return out


def r3_connector_feasible_strict(pads):
    """OLD v1 rule: landing y := pad y. Exact backtracking; (feasible, assign)."""
    n = len(pads)
    order = sorted(range(n), key=lambda i: len(pads[i]["cands"]))
    col_ys = {}
    assign = [None] * n

    def bt(k):
        if k == n:
            return True
        i = order[k]
        y = pads[i]["y"]
        for c in pads[i]["cands"]:
            key = round(c, 6)
            ys = col_ys.get(key, [])
            if all(abs(c0 - y) >= VIA_MIN - EPS for c0 in ys):
                col_ys.setdefault(key, []).append(y)
                assign[i] = c
                if bt(k + 1):
                    return True
                col_ys[key].pop()
                assign[i] = None
        return False

    ok = bt(0)
    return ok, ({pads[i]["net"]: assign[i] for i in range(n)} if ok else {})


def find_strict_cores(pads_by_ref):
    """Minimal 2-net hard cores under the OLD strict rule: two pads with the
    same pad y forced into a common single-candidate gap column."""
    cores = []
    for ref, pads in pads_by_ref.items():
        for i in range(len(pads)):
            for j in range(i + 1, len(pads)):
                a, b = pads[i], pads[j]
                if abs(a["y"] - b["y"]) > EPS:
                    continue
                if len(a["cands"]) == 1 and len(b["cands"]) == 1 and \
                        abs(a["cands"][0] - b["cands"][0]) <= EPS:
                    cores.append({"ref": ref, "gap_column_x": a["cands"][0],
                                  "y": a["y"],
                                  "minimal_core": sorted([a["net"], b["net"]])})
    return cores


def is_genuine_core(mc, gx, y, all_pads):
    """True if two pads named by mc share a ref, the same pad y, and both have a
    single gap candidate equal to gx (a forced collision under the strict rule)."""
    if not (isinstance(mc, list) and len(mc) == 2 and gx is not None and y is not None):
        return False
    for a in all_pads:
        if a["net"] != mc[0]:
            continue
        for b in all_pads:
            if b["net"] != mc[1] or b["ref"] != a["ref"]:
                continue
            if abs(a["y"] - b["y"]) <= EPS and abs(a["y"] - y) <= EPS and \
                    len(a["cands"]) == 1 and len(b["cands"]) == 1 and \
                    abs(a["cands"][0] - gx) <= EPS and abs(b["cands"][0] - gx) <= EPS:
                return True
    return False


def r2_map(art):
    r2 = dg(art, "layers", "R2", "assignment", default={})
    by_corr, flat = {}, {}
    if not isinstance(r2, dict):
        return by_corr, flat
    for k, v in r2.items():
        if not isinstance(v, dict):
            continue
        if "lane_index" in v or "lane_y" in v:
            flat[k] = v
        else:
            inner = {pk: pv for pk, pv in v.items()
                     if isinstance(pv, dict) and
                     ("lane_index" in pv or "lane_y" in pv)}
            if inner:
                by_corr[k] = inner
                for pk, pv in inner.items():
                    flat[pk] = pv
    return by_corr, flat


def dp_min_cost(rows, positions):
    n, m = len(rows), len(positions)
    if n == 0:
        return 0.0, []
    INF = float("inf")
    prev = [abs(positions[j] - rows[0]) for j in range(m)]
    prev_idx = [[j] for j in range(m)]
    for i in range(1, n):
        cur = [INF] * m
        cur_idx = [None] * m
        best, best_arg = INF, None
        for j in range(m):
            if j > 0 and prev[j - 1] < best:
                best, best_arg = prev[j - 1], prev_idx[j - 1]
            if best < INF:
                cur[j] = best + abs(positions[j] - rows[i])
                cur_idx[j] = best_arg + [j] if best_arg is not None else [j]
        prev, prev_idx = cur, cur_idx
    k = min(range(m), key=lambda j: prev[j])
    return prev[k], prev_idx[k]


def layer_status_not_feasible(art, name):
    layers = dg(art, "layers", default={})
    best = None
    for key in layers:
        if name == key or name.startswith(key):
            if best is None or len(key) > len(best):
                best = key
    if best is None:
        return None, None
    st = dg(layers, best, "status")
    if st is None:
        statuses = [v.get("status") for v in dg(layers, best, default={}).values()
                    if isinstance(v, dict)]
        st = "CERTIFICATE" if any(s and s != "FEASIBLE" for s in statuses) else \
            (statuses[0] if statuses else None)
    return best, st


# --------------------------------------------------------------------------
# engine black-box order test
# --------------------------------------------------------------------------
def engine_order_check(tmp_dir: Path):
    obs = {"engine": str(ENGINE), "exists": ENGINE.exists()}
    if not ENGINE.exists():
        obs["reason"] = "engine source not found"
        return False, obs
    try:
        hp = subprocess.run([sys.executable, str(ENGINE), "--help"],
                            cwd=str(K2), capture_output=True, text=True, timeout=120)
    except Exception as exc:  # noqa: BLE001
        obs["reason"] = "help failed: %r" % (exc,)
        return False, obs
    help_text = (hp.stdout or "") + (hp.stderr or "")
    obs["help_excerpt"] = help_text[:600]
    flags = re.findall(r"--[A-Za-z0-9][A-Za-z0-9_-]*", help_text)
    order_flag = None
    for cand in ("--enum-order", "--enum_order", "--order"):
        if cand in flags:
            order_flag = cand
            break
    if order_flag is None:
        for f in flags:
            if "order" in f:
                order_flag = f
                break
    obs["order_flag"] = order_flag
    out_flag = "--out" if "--out" in flags else None
    obs["out_flag"] = out_flag

    results = []
    for order in ["natural", "reverse", "hash"]:
        cmd = [sys.executable, str(ENGINE)]
        if order_flag:
            cmd += [order_flag, order]
        tgt = tmp_dir / ("w3_order_%s.json" % order)
        if out_flag:
            cmd += [out_flag, str(tgt)]
        obs.setdefault("commands", []).append(
            " ".join(cmd).replace(str(tmp_dir), "<TMPDIR>"))
        try:
            rp = subprocess.run(cmd, cwd=str(K2), capture_output=True,
                                text=True, timeout=1800)
        except Exception as exc:  # noqa: BLE001
            results.append({"order": order, "error": repr(exc)})
            continue
        if out_flag and tgt.exists():
            results.append({"order": order, "rc": rp.returncode,
                            "sha256": sha256_file(tgt)})
        else:
            results.append({"order": order, "rc": rp.returncode,
                            "sha256": sha256_file(ARTIFACT_DEFAULT)
                            if ARTIFACT_DEFAULT.exists() else None,
                            "note": "no --out support; hashed canonical artifact"})
    obs["runs"] = results
    shas = [r.get("sha256") for r in results]
    obs["sha256s"] = shas
    obs["distinct"] = len(set(shas))
    obs["canonical_artifact_sha256"] = sha256_file(ARTIFACT_DEFAULT) \
        if ARTIFACT_DEFAULT.exists() else None
    obs["equals_canonical"] = (sha256_file(ARTIFACT_DEFAULT)
                               if ARTIFACT_DEFAULT.exists() else None) in set(shas)
    ok = (order_flag is not None and len(shas) == 3 and
          all(s is not None for s in shas) and len(set(shas)) == 1 and
          all(r.get("rc") == 0 for r in results) and obs["equals_canonical"])
    return ok, obs


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main(argv):
    artifact_path = ARTIFACT_DEFAULT
    out_path = VALIDATION_DEFAULT
    run_probe = True
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--artifact":
            artifact_path = Path(argv[i + 1]); i += 2; continue
        if a == "--out":
            out_path = Path(argv[i + 1]); i += 2; continue
        if a == "--no-probe":
            run_probe = False; i += 1; continue
        if a in ("-h", "--help"):
            print(__doc__); return 0
        i += 1

    checks, probes, runtimes = [], [], {}

    def add(cid, assertion, expected, observed, ok):
        checks.append({"id": cid, "assertion": assertion, "expected": expected,
                       "observed": observed, "ok": bool(ok)})

    def probe(key, desc, result, ok):
        probes.append({"key": key, "probe": desc, "result": result, "ok": bool(ok)})

    actual = {name: (sha256_file(p) if p.exists() else None)
              for name, p, _pf in INPUTS}
    card_sha = sha256_file(CARD) if CARD.exists() else None
    card_v1_sha = sha256_file(CARD_V1) if CARD_V1.exists() else None
    frozen = {"expected": {name: pref for name, _p, pref in INPUTS},
              "actual": actual, "card_v1_1_sha256": card_sha,
              "card_v1_1_sha256_expected": CARD_SHA,
              "card_v1_sha256": card_v1_sha,
              "card_v1_sha256_expected": CARD_V1_SHA}
    validator_sha = sha256_file(SELF)

    if not artifact_path.exists():
        missing = "artifact missing"
        for cid in ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10"]:
            add(cid, "artifact present and verifiable", "artifact file exists",
                missing, False)
        report = {"artifact": str(artifact_path), "schema": 1, "revision": VAL_REV,
                  "verdict": "FAIL", "frozen_sha_check": frozen, "checks": checks,
                  "adversarial_probes": probes,
                  "certificate_recheck": {"applicable": False, "reason": missing},
                  "producer_sha256": None, "validator_sha256": validator_sha,
                  "notes": "artifact missing"}
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=1, ensure_ascii=False,
                                       sort_keys=True) + "\n", encoding="utf-8")
        print("VERDICT FAIL: artifact missing")
        return 1

    art = load_json(artifact_path)
    producer_sha = sha256_file(artifact_path)
    verdict_art = art.get("verdict")

    manifest = load_json(STEP / "m13_v57_s1_page_manifest.json")
    lane_frame = load_json(STEP / "m13_v57_f3_lane_frame.json")
    f8 = load_json(STEP / "m13_v57_f8_r3_gap_candidates.json")
    page_recs = derive_manifest_pages(manifest)
    positions = lane_positions(lane_frame)
    orders = {cid: f5_order(cid, page_recs) for cid in CORR}
    data_pages = [r["page_id"] for r in page_recs.values() if r["kind"] == "data"]
    refclk_pages = [r["page_id"] for r in page_recs.values()
                    if r["kind"] == "refclk_pass"]
    by_corr_r2, flat_r2 = r2_map(art)
    pads_by_ref = connector_pads(f8)
    all_pads = [p for pads in pads_by_ref.values() for p in pads]

    # ================= V1 fingerprint chain =================
    t0 = time.time()
    try:
        art_inputs = dg(art, "inputs_sha", default={})
        drift, key_obs = [], {}
        for name, _p, pref in INPUTS:
            got = actual[name]
            in_art = art_inputs.get(name)
            key_obs[name] = {"on_disk_prefix16": got[:16] if got else None,
                             "card_prefix16": pref,
                             "disk_matches_card": bool(got and got.startswith(pref)),
                             "artifact_matches_disk": got == in_art,
                             "artifact_inputs_sha": in_art}
            if got is None or not got.startswith(pref) or got != in_art:
                drift.append(name)
        fsc = dg(art, "frozen_sha_check", default={})
        contract = dg(art, "contract", default={})
        sup = dg(contract, "supersedes", default={})
        card11_ok = (card_sha == CARD_SHA and contract.get("sha256") == CARD_SHA)
        card1_ok = (card_v1_sha == CARD_V1_SHA and sup.get("sha256") == CARD_V1_SHA)
        ok = (not drift and fsc.get("drift") == [] and card11_ok and card1_ok and
              all(v["artifact_matches_disk"] for v in key_obs.values()))
        extra_inputs = sorted(set(art_inputs) - {n for n, _p, _pf in INPUTS})
        add("V1", "9 frozen inputs + W3-C1 v1.1 card sha256 chain: on-disk == "
                  "card prefix == artifact.inputs_sha; artifact.frozen_sha_check."
                  "drift == []; card v1.1 sha256 pinned and artifact.contract."
                  "supersedes.sha256 == frozen v1 card sha",
            "drift=[]; v1.1 card %s; supersedes v1 card %s" %
            (CARD_SHA[:16], CARD_V1_SHA[:16]),
            {"drift": drift, "per_key": key_obs,
             "artifact_frozen_sha_check_drift": fsc.get("drift"),
             "card_v1_1_recomputed": card_sha, "card_v1_1_ok": card11_ok,
             "artifact_contract_sha256": contract.get("sha256"),
             "card_v1_recomputed": card_v1_sha, "card_v1_ok": card1_ok,
             "artifact_contract_supersedes": sup,
             "extra_inputs_sha_keys": extra_inputs}, ok)
    except Exception as exc:  # noqa: BLE001
        add("V1", "fingerprint chain", "all match", repr(exc), False)
    runtimes["V1"] = time.time() - t0

    # ================= V2 conservation =================
    t0 = time.time()
    try:
        r1 = dg(art, "layers", "R1", "assignment", default={})
        missing1, badvia = [], []
        for pid in data_pages:
            ent = r1.get(pid)
            if not isinstance(ent, dict):
                missing1.append(pid); continue
            for pol in ("P_via", "N_via"):
                v = ent.get(pol)
                if not (isinstance(v, (list, tuple)) and len(v) == 2 and
                        num(v[0]) is not None and num(v[1]) is not None):
                    badvia.append({"page": pid, "pol": pol, "value": v})
        r1_ok = (len(r1) == N_DATA_PAGES and not missing1 and not badvia and
                 not [k for k in r1 if k not in data_pages])
        add("V2_R1", "R1: 32 data pages x P/N = 64 vias, each with a position",
            "32 pages / 64 vias with [x,y]",
            {"artifact_r1_keys": len(r1), "missing_pages": missing1,
             "bad_via": badvia[:5]}, r1_ok)
    except Exception as exc:  # noqa: BLE001
        add("V2_R1", "R1 conservation", "64 vias", repr(exc), False)

    try:
        missing2, dup = [], {}
        for cid in CORR:
            seen = {}
            sub = by_corr_r2.get(cid, {})
            for rec in orders[cid]:
                ent = sub.get(rec["page_id"])
                if not isinstance(ent, dict) or num(ent.get("lane_index")) is None:
                    missing2.append(rec["page_id"]); continue
                li = int(ent["lane_index"])
                seen.setdefault(li, []).append(rec["page_id"])
            dup[cid] = {k: v for k, v in seen.items() if len(v) > 1}
        extra2 = [k for k in flat_r2 if k not in data_pages]
        r2_ok = (len(flat_r2) == N_DATA_PAGES and not missing2 and
                 not any(dup.values()) and not extra2)
        add("V2_R2", "R2: each of 32 data pages has exactly one lane entry "
                     "(corridor-nested); lane_index distinct per corridor",
            "32 lane entries, distinct lane_index within each corridor",
            {"n_entries": len(flat_r2),
             "per_corridor_counts": {c: len(by_corr_r2.get(c, {})) for c in CORR},
             "missing": missing2, "duplicate_lane_index": dup,
             "extra_keys": extra2[:5]}, r2_ok)
    except Exception as exc:  # noqa: BLE001
        add("V2_R2", "R2 conservation", "32 lanes", repr(exc), False)

    # -- R3 (v1.1 y_band rule) --
    try:
        exp_keys = {"%s|%s" % (p["ref"], p["net"]): p for p in all_pads}
        r3 = dg(art, "layers", "R3", "assignment", default={})
        missing = sorted(k for k in exp_keys if k not in r3)
        extra = sorted(k for k in r3 if k not in exp_keys)
        bad = []
        for k, p in exp_keys.items():
            v = r3.get(k)
            if not isinstance(v, dict):
                continue
            cx = num(v.get("column_x"))
            land = v.get("landing") if isinstance(v.get("landing"), list) else [None, None]
            lx, ly = num(land[0]), num(land[1])
            yb = p["y_band"]
            if not any(approx(cx, c) for c in p["cands"]):
                bad.append({"key": k, "why": "column_x not in F-8 gap_candidates",
                            "column_x": cx, "cands": p["cands"]})
            if not approx(lx, cx):
                bad.append({"key": k, "why": "landing[0] != column_x",
                            "landing_x": lx, "column_x": cx})
            if ly is None or yb is None or not (yb[0] - EPS <= ly <= yb[1] + EPS):
                bad.append({"key": k, "why": "landing y outside F-8 y_band",
                            "y": ly, "y_band": yb})
            gcc = v.get("gap_column_candidates")
            if gcc is not None and sorted(round(g, 6) for g in gcc) != \
                    sorted(round(c, 6) for c in p["cands"]):
                bad.append({"key": k, "why": "gap_column_candidates != F-8 set",
                            "artifact": gcc, "f8": p["cands"]})
        n_nets = len({p["net"] for p in all_pads})
        ok = (len(exp_keys) == N_CONNECTOR_PADS and len(r3) == N_CONNECTOR_PADS and
              not missing and not extra and not bad)
        add("V2_R3", "R3 (v1.1): all 72 connector pads have exactly one landing, "
                     "keyed <ref>|<net> (REFCLK duplicate net names kept separate); "
                     "each landing x in the pad's F-8 gap_candidates and each "
                     "landing y inside the pad's F-8 y_band (tol 1e-9). The "
                     "emitted assignment is a constructive v1.1 feasibility witness.",
            "72/72 landings; keyed ref|net; x in gap_candidates; y in y_band",
            {"frozen_pad_count": len(all_pads), "unique_nets_if_collapsed": n_nets,
             "artifact_r3_key_count": len(r3), "expected_key_count": len(exp_keys),
             "missing_keys": missing[:6], "extra_keys": extra[:6],
             "landing_violations": bad[:6]}, ok)
    except Exception as exc:  # noqa: BLE001
        add("V2_R3", "R3 v1.1 conservation", "72/72", repr(exc), False)

    # -- R3 strict-rule finding (independently confirmed) --
    try:
        strict_feas = {ref: r3_connector_feasible_strict(pads)[0]
                       for ref, pads in pads_by_ref.items()}
        my_cores = find_strict_cores(pads_by_ref)
        srf = dg(art, "layers", "R3", "strict_rule_finding", default={})
        rep = dg(art, "layers", "R3", "report", default={})
        art_strict = {ref: dg(rep, ref, "strict_v1_rule", "feasible")
                      for ref in pads_by_ref}
        art_cores = srf.get("infeasible_cores") or []
        genuine = [is_genuine_core(c.get("minimal_core"), num(c.get("gap_column_x")),
                                   num(c.get("y")), all_pads) for c in art_cores]
        have_up2 = any(set(c.get("minimal_core") or []) ==
                       {"PCIE_UP2_N", "PCIE_UP3_P"} and
                       approx(num(c.get("gap_column_x")), 55.9) and
                       approx(num(c.get("y")), 43.25) for c in art_cores)
        my_up2 = any(set(c["minimal_core"]) == {"PCIE_UP2_N", "PCIE_UP3_P"} and
                     approx(c["gap_column_x"], 55.9) and approx(c["y"], 43.25)
                     for c in my_cores)
        ok = (not all(strict_feas.values()) and art_strict == strict_feas and
              srf.get("feasible_all") is False and bool(art_cores) and
              all(genuine) and have_up2 and my_up2)
        add("V2_R3_strict",
            "Superseded strict rule (v1: landing y := pad y) independently "
            "re-solved: J2 feasible, J3/J4 infeasible; artifact "
            "layers.R3.strict_rule_finding cores are genuine minimal 2-net "
            "forced collisions (same single gap column + identical pad y), "
            "including PCIE_UP2_N/PCIE_UP3_P @ 55.9 / y=43.25",
            "strict feasibility {J2:True,J3:False,J4:False}; cores genuine; "
            "example core present",
            {"independent_strict_feasible": strict_feas,
             "artifact_strict_feasible": art_strict,
             "my_cores_count": len(my_cores),
             "artifact_cores_count": len(art_cores),
             "all_artifact_cores_genuine": all(genuine),
             "artifact_has_PCIE_UP2_N_PCIE_UP3_P_core": have_up2,
             "independent_has_PCIE_UP2_N_PCIE_UP3_P_core": my_up2}, ok)
    except Exception as exc:  # noqa: BLE001
        add("V2_R3_strict", "strict-rule finding", "genuine", repr(exc), False)

    v2_ok = all(c["ok"] for c in checks if c["id"].startswith("V2"))
    add("V2", "aggregate conservation (R1 64 via / R2 32 lanes / R3 72 landings "
              "or certified infeasibility)", "all sub-checks pass",
        {"aggregate_ok": v2_ok}, v2_ok)
    runtimes["V2"] = time.time() - t0

    # ================= V3 exclusivity =================
    t0 = time.time()
    try:
        pts = []
        r1 = dg(art, "layers", "R1", "assignment", default={})
        for pid in data_pages:
            ent = r1.get(pid, {})
            for pol in ("P_via", "N_via"):
                v = ent.get(pol)
                if isinstance(v, (list, tuple)) and len(v) == 2:
                    pts.append({"page": pid, "pol": pol,
                                "xy": [num(v[0]), num(v[1])]})
        worst, worstpair, viol = None, None, []
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                d = dist2d(pts[i]["xy"], pts[j]["xy"])
                if worst is None or d < worst:
                    worst, worstpair = d, (pts[i], pts[j])
                if d < VIA_MIN - EPS:
                    viol.append({"a": pts[i]["page"] + "/" + pts[i]["pol"],
                                 "b": pts[j]["page"] + "/" + pts[j]["pol"], "dist": d})
        f13 = load_json(STEP / "m13_v57_f13_r1_pair_coupling.json")
        f13_pages = dg(f13, "pages", default={})
        dual_bad, dom_bad = [], []
        for pid in data_pages:
            ent = r1.get(pid, {})
            P, N = ent.get("P_via"), ent.get("N_via")
            if not (isinstance(P, list) and isinstance(N, list)):
                continue
            dd, dx = dist2d(P, N), abs(P[0] - N[0])
            if dd < VIA_MIN - EPS or dx < 0.38 - EPS:
                dual_bad.append({"page": pid, "dist": dd, "dx": dx})
            pd = dg(f13_pages, pid, "pair_domain", default={})
            xp, xn = pd.get("x_columns_P"), pd.get("x_columns_N")
            if xp and not any(approx(P[0], c) for c in xp):
                dom_bad.append({"page": pid, "pol": "P", "x": P[0]})
            if xn and not any(approx(N[0], c) for c in xn):
                dom_bad.append({"page": pid, "pol": "N", "x": N[0]})
        a_ok = (len(pts) == 64 and not viol and not dual_bad and not dom_bad)
        add("V3a", "R1: all 64 vias pairwise >= 0.525 - 1e-9; plus the F-13 "
                   "col-pair dual constraint dist>=0.525 & |dx|>=0.38 and via x "
                   "inside the frozen F-13 admissible columns", ">= 0.525",
            {"n_vias": len(pts), "min_pair_dist": worst,
             "min_pair": [worstpair[0]["page"] + "/" + worstpair[0]["pol"],
                          worstpair[1]["page"] + "/" + worstpair[1]["pol"]]
             if worstpair else None,
             "n_violations": len(viol), "violations": viol[:5],
             "f13_dual_violations": dual_bad[:5],
             "f13_domain_violations": dom_bad[:5]}, a_ok)
    except Exception as exc:  # noqa: BLE001
        add("V3a", "R1 pairwise", ">=0.525", repr(exc), False)

    try:
        detail, alts = {}, {}
        b_ok = True
        for cid in CORR:
            seq = [(r["page_id"], num(dg(flat_r2, r["page_id"], "lane_index")))
                   for r in orders[cid]]
            inc = all(seq[i][1] is not None and seq[i + 1][1] is not None and
                      seq[i][1] < seq[i + 1][1] for i in range(len(seq) - 1))
            b_ok = b_ok and inc
            detail[cid] = {"key": "(conn_ref,row_y,conn_x,page_id)",
                           "strict_increasing": inc,
                           "lane_seq": [s[1] for s in seq]}
            alt = {}
            for name, lst in alt_orders(cid, page_recs).items():
                ls = [num(dg(flat_r2, r["page_id"], "lane_index")) for r in lst]
                alt[name] = all(a is not None and b is not None and a < b
                                for a, b in zip(ls, ls[1:]))
            alts[cid] = alt
        add("V3b", "R2: lane_index strictly increasing within each corridor under "
                   "the contract F-5 key recomputed from the frozen manifest "
                   "(G3 v1 §2: row_y=(N.y+P.y)/2; WEST framed by conn_ref, key "
                   "(conn_ref,row_y) + in-frame conn_x asc)",
            "strictly increasing in both corridors",
            {"primary_f5": detail, "alternative_keys_also_increasing": alts}, b_ok)
    except Exception as exc:  # noqa: BLE001
        add("V3b", "R2 monotonic", "strictly increasing", repr(exc), False)

    try:
        r3 = dg(art, "layers", "R3", "assignment", default={})
        bycol = {}
        for k, v in r3.items():
            if not isinstance(v, dict):
                continue
            cx, ly = num(v.get("column_x")), num(dg(v, "landing", default=[None, None])[1])
            if cx is None or ly is None:
                continue
            bycol.setdefault(round(cx, 6), []).append((k, ly))
        viol, worst = [], None
        for cx, lst in bycol.items():
            for i in range(len(lst)):
                for j in range(i + 1, len(lst)):
                    dy = abs(lst[i][1] - lst[j][1])
                    if worst is None or dy < worst:
                        worst = dy
                    if dy < VIA_MIN - EPS:
                        viol.append({"column_x": cx, "a": lst[i][0], "b": lst[j][0], "dy": dy})
        c_ok = (len(bycol) > 0 and not viol)
        add("V3c", "R3 (v1.1): any two landings sharing the same gap column_x have "
                   "|dy| >= 0.525 - 1e-9", ">= 0.525",
            {"n_gap_columns": len(bycol), "n_landings": sum(len(v) for v in bycol.values()),
             "min_same_column_dy": worst, "n_violations": len(viol),
             "violations": viol[:5]}, c_ok)
    except Exception as exc:  # noqa: BLE001
        add("V3c", "R3 column separation", ">=0.525", repr(exc), False)

    try:
        rc = dg(art, "layers", "REFCLK", "assignment", default={})
        ys = []
        for pid in refclk_pages:
            y = num(dg(rc, pid, "f_cu_lane_y"))
            if y is None:
                y = num(dg(rc, pid, "lane_y"))
            ys.append({"page": pid, "y": y})
        seps = [abs(ys[i]["y"] - ys[j]["y"]) for i in range(len(ys))
                for j in range(i + 1, len(ys))
                if ys[i]["y"] is not None and ys[j]["y"] is not None]
        d_ok = (len(ys) == N_REFCLK_PAGES and len(seps) >= 1 and
                min(seps) >= REFCLK_MIN - EPS)
        add("V3d", "REFCLK: page-to-page F.Cu lane separation >= 1.46", ">= 1.46",
            {"refclk_pages": ys, "separations": seps,
             "min_separation": min(seps) if seps else None}, d_ok)
    except Exception as exc:  # noqa: BLE001
        add("V3d", "REFCLK separation", ">=1.46", repr(exc), False)

    v3_ok = all(c["ok"] for c in checks if c["id"].startswith("V3"))
    add("V3", "aggregate exclusivity (V3a-V3d geometric recompute)",
        "all sub-checks pass", {"aggregate_ok": v3_ok}, v3_ok)
    runtimes["V3"] = time.time() - t0

    # ================= V4 predicate / deltas =================
    t0 = time.time()
    try:
        bad_reach, bad_match, rows = [], [], []
        for cid in CORR:
            for rec in orders[cid]:
                pid = rec["page_id"]
                ent = flat_r2.get(pid)
                if not isinstance(ent, dict):
                    bad_reach.append({"page": pid, "why": "no R2 entry"}); continue
                ly = num(ent.get("lane_y"))
                conn_d = ly - rec["conn_row_y"] if ly is not None else None
                chip_d = (ly - rec["chip_row_y"]) if (ly is not None and
                          rec["chip_row_y"] is not None) else None
                rc_rep, rh_rep = num(ent.get("conn_delta_mm")), num(ent.get("chip_delta_mm"))
                rows.append({"page": pid, "lane_y": ly, "conn_delta": conn_d,
                             "chip_delta": chip_d, "reported_conn": rc_rep,
                             "reported_chip": rh_rep})
                if conn_d is None or chip_d is None or abs(conn_d) > REACH + EPS \
                        or abs(chip_d) > REACH + EPS:
                    bad_reach.append({"page": pid, "conn_delta": conn_d,
                                      "chip_delta": chip_d})
                if (rc_rep is None or abs(rc_rep - conn_d) > TOL6 or
                        rh_rep is None or abs(rh_rep - chip_d) > TOL6):
                    bad_match.append({"page": pid, "recomputed_conn": conn_d,
                                      "reported_conn": rc_rep,
                                      "recomputed_chip": chip_d, "reported_chip": rh_rep})
        ok = (len(rows) == N_DATA_PAGES and not bad_reach and not bad_match)
        add("V4", "F-6 predicate/deltas recomputed from frozen anchors + emitted "
                  "lane_y: |conn_delta|,|chip_delta| <= 45.4+1e-9 and reported "
                  "deltas match to 1e-6",
            "32 pages, all |delta| <= 45.4, reported == recomputed",
            {"n_pages": len(rows), "reach_violations": bad_reach[:5],
             "delta_mismatch": bad_match[:5],
             "max_abs_conn_delta": max((abs(r["conn_delta"]) for r in rows
                                        if r["conn_delta"] is not None), default=None),
             "max_abs_chip_delta": max((abs(r["chip_delta"]) for r in rows
                                        if r["chip_delta"] is not None), default=None)}, ok)
    except Exception as exc:  # noqa: BLE001
        add("V4", "predicate/deltas", "<=45.4", repr(exc), False)
    runtimes["V4"] = time.time() - t0

    # ================= V5 R2 optimality (independent DP) =================
    t0 = time.time()
    try:
        obj = dg(art, "layers", "R2", "objective", default={})
        per = dg(obj, "per_corridor", default={})
        opt = {}
        for cid in CORR:
            rows = [rec["conn_row_y"] for rec in orders[cid]]
            val, idx = dp_min_cost(rows, positions)
            emitted = None
            if isinstance(per, dict) and cid in per:
                pv = per[cid]
                emitted = pv if isinstance(pv, (int, float)) else \
                    num(dg(pv, "objective_mm", default=dg(pv, "total_abs_delta_mm")))
            opt[cid] = {"independent": val, "emitted": emitted}
        my_total = sum(v["independent"] for v in opt.values())
        emitted_total = num(dg(obj, "objective_mm", default=dg(obj, "total_abs_delta_mm")))
        if emitted_total is None:
            emitted_total = num(dg(art, "objective", "r2_total_mm"))
        per_ok = all(v["emitted"] is not None and
                     abs(v["emitted"] - v["independent"]) <= TOL6 for v in opt.values())
        ok = per_ok and emitted_total is not None and \
            abs(emitted_total - my_total) <= TOL6
        add("V5", "R2 order-preserving min-cost DP re-solved independently "
                  "(grid 33.3+1.46*i, in F-5 order, minimize sum|lane_y-row_y|); "
                  "compare to artifact objective (tol 1e-6)",
            "artifact objective == independent DP optimum per corridor and total",
            {"independent_per_corridor": {k: v["independent"] for k, v in opt.items()},
             "independent_total": my_total,
             "emitted_per_corridor": {k: v["emitted"] for k, v in opt.items()},
             "emitted_total": emitted_total, "per_corridor_match": per_ok,
             "total_diff": None if emitted_total is None else emitted_total - my_total,
             "grid_head": positions[:3], "grid_tail": positions[-2:]}, ok)
    except Exception as exc:  # noqa: BLE001
        add("V5", "R2 optimality", "DP match", repr(exc), False)
    runtimes["V5"] = time.time() - t0

    # ================= V6 layer semantics + R4 out-of-chain =================
    t0 = time.time()
    try:
        def collect_layers(obj, acc, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    collect_layers(v, acc, path + "/" + str(k))
            elif isinstance(obj, list):
                for i2, v in enumerate(obj):
                    collect_layers(v, acc, path + "/%d" % i2)
            elif isinstance(obj, str):
                for m in re.findall(r"[A-Za-z0-9_]+\.[A-Za-z0-9_]+", obj):
                    if m.endswith(".Cu"):
                        acc.setdefault(m, []).append(path)

        data_layer_hits = {}
        for pg in dg(art, "pages", default=[]):
            if pg.get("kind") == "data" and pg.get("page_id") in data_pages:
                collect_layers(pg, data_layer_hits, pg["page_id"])
        bad_layers = {k: v[:3] for k, v in data_layer_hits.items()
                      if k not in ("F.Cu", "In2.Cu")}

        via_viol, via_counts = [], []
        for pg in dg(art, "pages", default=[]):
            if pg.get("kind") != "data" or pg.get("page_id") not in data_pages:
                continue
            vias = pg.get("vias") or []
            chain = dg(pg, "r3", "layer_chain") or []
            transitions = max(0, len(chain) - 1)
            via_counts.append({"page": pg["page_id"], "vias_list": len(vias),
                               "layer_chain": chain, "chain_transitions": transitions})
            per_pol = {}
            for v in vias:
                pol = dg(v, "pol") or dg(v, "role")
                per_pol[pol] = per_pol.get(pol, 0) + 1
            if len(vias) > 4:
                via_viol.append({"page": pg["page_id"], "n_vias": len(vias)})
            for pol, c in per_pol.items():
                if pol and c > 2:
                    via_viol.append({"page": pg["page_id"], "pol": pol, "n": c})

        refclk_layer_hits = {}
        for pg in dg(art, "pages", default=[]):
            if pg.get("kind") == "refclk_pass":
                collect_layers(pg, refclk_layer_hits, pg.get("page_id", "?"))
        collect_layers(dg(art, "layers", "REFCLK", default={}), refclk_layer_hits,
                       "layers/REFCLK")
        refclk_bad = {k: v[:3] for k, v in refclk_layer_hits.items() if k != "F.Cu"}

        raw = artifact_path.read_text(encoding="utf-8")
        r4_hits = {k: raw.count(k) for k in FORBIDDEN_R4}
        r4_bad = {k: c for k, c in r4_hits.items() if c > 0}
        ok = (not bad_layers and not via_viol and not refclk_bad and not r4_bad)
        add("V6", "layer semantics: data pages only F.Cu/In2.Cu; <=2 vias per "
                  "line; REFCLK only F.Cu; forbidden R4 keys zero occurrences",
            "no bad layers, no via>2, no R4 keys",
            {"data_layers_seen": {k: len(v) for k, v in data_layer_hits.items()},
             "bad_data_layers": bad_layers, "via_violations": via_viol[:8],
             "via_chain_sample": via_counts[:2],
             "max_chain_transitions": max((c["chain_transitions"] for c in via_counts),
                                          default=None),
             "refclk_layers_seen": list(refclk_layer_hits.keys()), "refclk_bad": refclk_bad,
             "forbidden_r4_hits": r4_hits, "forbidden_r4_violations": r4_bad}, ok)
    except Exception as exc:  # noqa: BLE001
        add("V6", "layer semantics", "clean", repr(exc), False)
    runtimes["V6"] = time.time() - t0

    # ================= V7 all-or-certificate =================
    t0 = time.time()
    try:
        landing_rows = art.get("landing_rows")
        lrs = art.get("landing_rows_status")
        pages = dg(art, "pages", default=[])
        if verdict_art == "CERTIFICATE":
            ok = (landing_rows is None and lrs == "NOT_REEMITTED")
            obs = {"verdict": verdict_art, "landing_rows": landing_rows,
                   "landing_rows_status": lrs}
        elif verdict_art == "FEASIBLE_ALL":
            missing_nodes = [pg.get("page_id") for pg in pages
                             if not (dg(pg, "nodes", "P") and dg(pg, "nodes", "N"))]
            ok = (len(pages) == 34 and not missing_nodes and LANDING.exists())
            obs = {"verdict": verdict_art, "n_pages": len(pages),
                   "pages_without_node_chains": missing_nodes[:8],
                   "landing_file_exists": LANDING.exists(),
                   "landing_rows_status": lrs}
        else:
            ok, obs = False, {"verdict": verdict_art, "why": "unknown verdict"}
        add("V7", "all-or-certificate: CERTIFICATE => landing_rows null + "
                  "NOT_REEMITTED; FEASIBLE_ALL => 34 pages with node chains + "
                  "landing file re-emitted",
            "artifact verdict consistent with landing emission", obs, ok)
    except Exception as exc:  # noqa: BLE001
        add("V7", "all-or-certificate", "consistent", repr(exc), False)
    runtimes["V7"] = time.time() - t0

    # ================= V8 certificate recheck =================
    t0 = time.time()
    cert_recheck = {"applicable": False}
    try:
        if verdict_art != "CERTIFICATE":
            cert_recheck = {"applicable": False, "reason": "verdict=%s" % verdict_art}
            add("V8", "certificate recheck (only if verdict=CERTIFICATE)", "n/a",
                {"applicable": False, "verdict": verdict_art}, True)
        else:
            r15 = dg(art, "layers", "R1_5", default={})
            recount, under = [], []
            for cid, blk in (r15.items() if isinstance(r15, dict) else []):
                if not isinstance(blk, dict):
                    continue
                claimed_min = num(blk.get("min_crossings_over_domain"))
                variants = dg(blk, "variants", default={}) or {}
                my_min = None
                for vname, v in variants.items():
                    paths = dg(v, "paths", default={}) or {}
                    pls = [[[num(pt[0]), num(pt[1])] for pt in poly]
                           for poly in paths.values() if isinstance(poly, list)]
                    mine = 0
                    for i2 in range(len(pls)):
                        for j2 in range(i2 + 1, len(pls)):
                            mine += polyline_crossings(pls[i2], pls[j2])
                    claimed = num(v.get("n_crossings"))
                    if claimed is None:
                        claimed = len(v.get("crossings") or [])
                    row = {"corridor": cid, "variant": vname, "n_paths": len(pls),
                           "claimed_n_crossings": claimed, "independent_recount": mine,
                           "no_under_reporting": claimed is None or mine >= claimed}
                    recount.append(row)
                    if claimed is not None and mine < claimed:
                        under.append(row)
                    my_min = mine if my_min is None else min(my_min, mine)
                if claimed_min is not None and my_min is not None and \
                        my_min < claimed_min:
                    under.append({"corridor": cid, "min_claimed": claimed_min,
                                  "independent_min": my_min})
            certs = dg(art, "certificates", default=[])
            cert_ok = bool(certs) and isinstance(certs, list)
            cert_rows = []
            for cert in (certs if isinstance(certs, list) else []):
                il = cert.get("infeasible_layer")
                key, st = layer_status_not_feasible(art, il) if il else (None, None)
                row = {"cert_id": cert.get("cert_id"), "kind": cert.get("kind"),
                       "infeasible_layer": il, "resolved_layer_key": key,
                       "resolved_status": st,
                       "has_escape_hatches": bool(cert.get("escape_hatches")),
                       "has_why_no_alloc_possible": bool(
                           isinstance(cert.get("why_no_alloc_possible"), str) and
                           cert.get("why_no_alloc_possible").strip()),
                       "has_minimal_core": bool(cert.get("minimal_core"))}
                row["ok"] = (row["has_escape_hatches"] and
                             row["has_why_no_alloc_possible"] and
                             st is not None and st != "FEASIBLE")
                cert_ok = cert_ok and row["ok"]
                cert_rows.append(row)
            # A-W3.1(v1.1): under CERTIFICATE, unmet capabilities must be attributed.
            # R3 is FEASIBLE 72/72 here, so the only attributed layer is R1_5.
            attributed = sorted({r["resolved_layer_key"] for r in cert_rows})
            ok = (not under) and cert_ok and bool(recount) and \
                "R1_5" in attributed
            cert_recheck = {"applicable": True, "crossing_recount": recount,
                            "under_reporting": under,
                            "certificate_rows": cert_rows,
                            "certificates_valid": cert_ok,
                            "attributed_infeasible_layers": attributed,
                            "residual_uncertainty": (
                                "The R1_5 planarity certificate enumerates a "
                                "4-variant construction family (shape x pol) that "
                                "holds the R1 via selection fixed at the emitted "
                                "lex-min DFS choice.  Its crossing recount is "
                                "independently confirmed (min 17 EAST / 19 WEST), "
                                "and crossings on a no-via single layer do imply "
                                "infeasibility; however the family does NOT sweep "
                                "alternative R1 via selections inside the F-13 "
                                "domain, so exhaustiveness of the 'no alloc' claim "
                                "w.r.t. R1 selection is NOT independently "
                                "established by this validator.")}
            add("V8", "CERTIFICATE: independent segment-segment recount on emitted "
                      "R1_5 variant paths >= claimed crossings (no under-reporting); "
                      "escape_hatches + why_no_alloc_possible present; "
                      "infeasible_layer resolves to a non-FEASIBLE layer and the "
                      "unmet capability (R1_5) is certificate-attributed (A-W3.1 v1.1)",
                "no under-reporting; all certificate fields valid; R1_5 attributed",
                cert_recheck, ok)
    except Exception as exc:  # noqa: BLE001
        add("V8", "certificate recheck", "valid", repr(exc), False)
    runtimes["V8"] = time.time() - t0

    # ================= V9 order invariance (black box) =================
    t0 = time.time()
    try:
        import tempfile
        with tempfile.TemporaryDirectory(prefix="w3order_") as td:
            ok, obs = engine_order_check(Path(td))
        add("V9", "order-invariance: engine run 3x with permuted input "
                  "enumeration orders (natural/reverse/hash) -> byte-identical "
                  "outputs equal to the canonical artifact",
            "3 outputs byte-identical AND equal to on-disk artifact sha256",
            obs, ok)
    except Exception as exc:  # noqa: BLE001
        add("V9", "order-invariance", "3x byte identical", repr(exc), False)
    runtimes["V9"] = time.time() - t0

    # ================= V10 no per-net first-fit =================
    t0 = time.time()
    try:
        nf = dg(art, "no_first_fit", default={})
        block_ok = (isinstance(nf, dict) and bool(nf.get("statement")) and
                    nf.get("enumeration_orders_probed") == 3 and
                    nf.get("byte_identical") is True)
        greps = {}
        suspicious = False
        if ENGINE.exists():
            import io
            import tokenize
            src = ENGINE.read_text(encoding="utf-8", errors="replace")
            hits = ["%d: %s" % (i2 + 1, ln.rstrip())
                    for i2, ln in enumerate(src.splitlines())
                    if re.search(r"first|greedy", ln, re.I)]
            names, tok_err = [], None
            try:
                for tok in tokenize.generate_tokens(io.StringIO(src).readline):
                    if tok.type == tokenize.NAME and tok.string.lower() in (
                            "first_fit", "firstfit", "greedy"):
                        names.append({"line": tok.start[0], "name": tok.string})
            except Exception as exc:  # noqa: BLE001
                tok_err = repr(exc)
            greps = {"grep_first_or_greedy": hits, "n_hits": len(hits),
                     "first_fit_greedy_NAME_tokens": names, "tokenize_error": tok_err,
                     "engine_missing": False}
            suspicious = bool(names)
        else:
            greps = {"engine_missing": True}
        ok = block_ok and not suspicious
        add("V10", "no per-net first-fit: artifact.no_first_fit block consistent "
                   "AND engine source shows no per-net greedy/first-fit allocation "
                   "identifier",
            "block valid (probed=3, byte_identical=true); no first-fit/greedy identifier",
            {"no_first_fit_block": nf, "block_ok": block_ok,
             "engine_source_grep": greps,
             "static_decidability": "identifier/comment grep is heuristic: a "
                                    "per-net loop without the words first-fit/greedy "
                                    "would not be caught statically",
             "suspicious_identifiers": suspicious}, ok)
    except Exception as exc:  # noqa: BLE001
        add("V10", "no-first-fit declaration", "clean", repr(exc), False)
    runtimes["V10"] = time.time() - t0

    # ================= adversarial probes =================
    try:
        git_status = subprocess.run(["git", "-C", str(K2), "status", "--short"],
                                    capture_output=True, text=True, timeout=120)
        git_head = subprocess.run(["git", "-C", str(K2), "rev-parse", "HEAD"],
                                  capture_output=True, text=True, timeout=120)
        art_inputs = dg(art, "inputs_sha", default={})
        stale_bad = [n for n, _p, _pf in INPUTS if actual[n] != art_inputs.get(n)]
        probe("stale_state",
              "confirm artifact.inputs_sha equals CURRENT on-disk frozen inputs "
              "and record git HEAD/worktree state",
              {"git_head": git_head.stdout.strip(),
               "git_status_short": git_status.stdout.strip().splitlines(),
               "inputs_mismatch": stale_bad}, not stale_bad)
    except Exception as exc:  # noqa: BLE001
        probe("stale_state", "git/worktree state", repr(exc), False)

    try:
        git_status = subprocess.run(["git", "-C", str(K2), "status", "--short"],
                                    capture_output=True, text=True, timeout=120)
        lines = git_status.stdout.strip().splitlines()
        known = [l for l in lines if "_shared" in l or ".bak_v32" in l or
                 "model_solves" in l]
        probe("dirty_worktree",
              "report pre-existing untracked artifacts (gitlink deviation, "
              "*.bak_v32*, model_solves/*); they are NOT part of the verdict",
              {"known_untracked_count": len(known), "known_untracked": known[:20],
               "total_status_lines": len(lines)}, True)
    except Exception as exc:  # noqa: BLE001
        probe("dirty_worktree", "list untracked", repr(exc), False)

    if run_probe:
        try:
            import tempfile
            with tempfile.TemporaryDirectory(prefix="w3probe_") as td:
                td = Path(td)
                mut = json.loads(json.dumps(art))
                mutation = None
                r1 = dg(mut, "layers", "R1", "assignment", default={})
                if isinstance(r1, dict) and r1:
                    k = sorted(r1.keys())[0]
                    ent = r1[k]
                    if isinstance(ent, dict) and isinstance(ent.get("N_via"), list) \
                            and isinstance(ent.get("P_via"), list):
                        ent["N_via"] = list(ent["P_via"])  # dist 0 -> V3a must fail
                        mutation = "set R1[%s].N_via = P_via (pair dist 0 < 0.525)" % k
                if mutation is None:
                    # certificate path: flip one R3 landing y out of its y_band
                    r3 = dg(mut, "layers", "R3", "assignment", default={})
                    if isinstance(r3, dict) and r3:
                        k = sorted(r3.keys())[0]
                        e = r3[k]
                        if isinstance(e, dict) and isinstance(e.get("landing"), list):
                            e["landing"] = [e["landing"][0], e["landing"][1] + 5.0]
                            mutation = "shift R3[%s].landing y by +5 (outside y_band)" % k
                if mutation is None:
                    mut["verdict"] = "FEASIBLE_ALL"
                    mutation = "set verdict=FEASIBLE_ALL while landing_rows=%r" % mut.get("landing_rows")
                mpath = td / "mutated.json"
                vpath = td / "mutated_validation.json"
                mpath.write_text(json.dumps(mut, indent=1, ensure_ascii=False,
                                            sort_keys=True) + "\n", encoding="utf-8")
                rp = subprocess.run([sys.executable, str(SELF), "--artifact", str(mpath),
                                     "--out", str(vpath), "--no-probe"],
                                    cwd=str(K2), capture_output=True, text=True, timeout=1800)
                got_verdict, first_failed = None, None
                try:
                    mv = load_json(vpath)
                    got_verdict = mv.get("verdict")
                    first_failed = next((c["id"] for c in mv["checks"] if not c["ok"]), None)
                except Exception:  # noqa: BLE001
                    pass
                ok = (rp.returncode != 0 and got_verdict == "FAIL")
                probe("misleading_success_output",
                      "TEMPORARY copy of the artifact in /tmp with one mutated field "
                      "(%s); validator must return FAIL and exit non-zero "
                      "(the real artifact is never touched)" % mutation,
                      {"mutation": mutation, "temp_artifact": "<TMPDIR>/mutated.json",
                       "validator_returncode": rp.returncode, "emitted_verdict": got_verdict,
                       "first_failed_check": first_failed}, ok)
        except Exception as exc:  # noqa: BLE001
            probe("misleading_success_output", "mutated-copy negative control", repr(exc), False)
    else:
        probe("misleading_success_output", "skipped (--no-probe)", "skipped", True)

    long_checks = sorted(k for k, v in runtimes.items() if v > 60)
    probe("hung_or_long_commands",
          "report per-check runtime; flag any check > ~60s (raw timings are "
          "printed to stdout, not stored, so the report stays byte-identical)",
          {"checks_over_60s": long_checks, "raw_runtimes_stdout_only": True}, True)
    print("runtimes_s=%s" % {k: round(v, 3) for k, v in runtimes.items()})

    all_checks_ok = all(c["ok"] for c in checks)
    all_probes_ok = all(p["ok"] for p in probes)
    final_verdict = "PASS" if (all_checks_ok and all_probes_ok) else "FAIL"
    failed = [c["id"] for c in checks if not c["ok"]]
    failed_probes = [p["key"] for p in probes if not p["ok"]]
    report = {"artifact": str(artifact_path), "schema": 1, "revision": VAL_REV,
              "verdict": final_verdict, "frozen_sha_check": frozen,
              "checks": checks, "adversarial_probes": probes,
              "certificate_recheck": cert_recheck, "producer_sha256": producer_sha,
              "validator_sha256": validator_sha,
              "artifact_revision": art.get("revision"),
              "uncertainties": [
                  "R1_5 planarity certificate: crossing counts confirmed (>=), "
                  "but the 4-variant construction family fixes the R1 via "
                  "selection; exhaustiveness over alternative R1 via choices in "
                  "the F-13 domain is not independently established.",
                  "certificates use descriptive infeasible_layer labels "
                  "(R1_5_chip_transition) rather than the canonical layer key "
                  "R1_5; resolved by prefix match.",
                  "artifact.inputs_sha carries an extra key 'verdict' "
                  "(m13_v57_s1_r1_via_verdict.json) beyond the 9-item card "
                  "whitelist; it is an upstream input to F-13, not a frozen "
                  "whitelist drift, but it is outside the literal whitelist.",
                  "pages[].r1_5 omits the card's path/layer/corners_deg/"
                  "crossings fields (the R1.5 polylines live under "
                  "layers.R1_5[cid].variants[*].paths; each `crossings` list is "
                  "truncated to 20 entries while n_crossings is the full count).",
                  "R3 v1.1 landings are boundary-tight: many sit exactly on an "
                  "F-8 y_band edge with 0.000000 mm margin (e.g. "
                  "J2|PCIE_DN0_N y=54.0 in [54.0,54.6]; J3|PCIE_UP2_N y=42.0 in "
                  "[42.0,44.5]). The v1.1 rule 'y in y_band' is inclusive, so it "
                  "PASSes at 1e-9 tolerance, but the solution rides the "
                  "construction boundary rather than an interior."],
              "notes": ("artifact_verdict=%s; artifact_revision=%s; checks=%d "
                        "failed=%s; probes=%d failed=%s" %
                        (verdict_art, art.get("revision"), len(checks),
                         failed or "none", len(probes), failed_probes or "none"))}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=1, ensure_ascii=False,
                                   sort_keys=True) + "\n", encoding="utf-8")
    print("VERDICT %s (artifact verdict=%s revision=%s; failed checks: %s; failed probes: %s)" %
          (final_verdict, verdict_art, art.get("revision"), failed or "none",
           failed_probes or "none"))
    return 0 if final_verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
