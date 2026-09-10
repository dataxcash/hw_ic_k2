#!/usr/bin/env python3
"""Independent verifier for the W3 (G4) *constructive* deliverable (rev W3-CN.1).

Contract (authoritative) : pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_kickoff_card_v1_2.md
Plan of record           : .omo/plans/k2-v57-w3-feasible-all.md

This verifier intentionally does **not** import the engine module
(`tools/p3_v57_w3_constructive.py`) and does not copy its code.  It consumes the
engine only as a black box via subprocess for the scaling probe (G-M3) and the
order-invariance probe (A-CN.6).  All geometry / placements are independently
re-derived from the card text and the frozen inputs.

Exit code is non-zero if ANY check, method gate or adversarial probe fails.
Never weakens a check to make it pass.
"""
from __future__ import annotations

import ast
import hashlib
import json
import statistics
import subprocess
import sys
import time
import tokenize
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3"
STEP2 = L3 / "mcio_feas_step2"

ENGINE = K2 / "tools" / "p3_v57_w3_constructive.py"
ART_MAIN = STEP2 / "m13_v57_w3_joint_assignment.json"
ART_LANDING = STEP2 / "m13_v57_w3_chip_landing_rows.json"
CARD = STEP2 / "m13_v57_w3_kickoff_card_v1_2.md"

FILES = {
    "spec": L3 / "SPEC_k2_v4.json",
    "rules": K2 / "_shared" / "eda_core" / "drc_rules.json",
    "manifest": STEP2 / "m13_v57_s1_page_manifest.json",
    "w0r_model": STEP2 / "m13_v57_big_w0r_corridor_model.json",
    "lane_frame": STEP2 / "m13_v57_f3_lane_frame.json",
    "param_trace": STEP2 / "m13_v57_f13_r1_param_trace.json",
    "pair_coupling": STEP2 / "m13_v57_f13_r1_pair_coupling.json",
    "pair_xorder": STEP2 / "m13_v57_f13_r1_pair_coupling_v1_1.json",
    "r3_gaps": STEP2 / "m13_v57_f8_r3_gap_candidates.json",
    "f6b_report": STEP2 / "m13_v57_f6b_report.json",
    "verdict": STEP2 / "m13_v57_s1_r1_via_verdict.json",
    "card": CARD,
}
# sha256[:16] as pinned by the W3-C1 v1 card §1 whitelist (full 64-hex where known).
EXPECTED_SHA = {
    "spec": "0bd52ed48e720b8cb6a7869379f6c0a220f3e141e1514ab159f9f5f3b8b02233",
    "rules": "0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448",
    "manifest": "a8ef3ea8ecff99d7549d4122043c972c1bb68346dc4dcc3f36fdd9bacde49890",
    "w0r_model": "80ee9adb78a7e9ad94c27d426295592eee21af3d1e3ce88fe3042183160f0efa",
    "lane_frame": "ff804e1edfacbf02e4227f10359a9217347ecdf0473801d655ef3a71ddf5cb6c",
    "param_trace": "e288ffa5421c22972075a7a3bef503a4b472aa32ea148c2ed0502090a3d98cae",
    "pair_coupling": "82e11c4cbdb4e8d44df1997f660c97fb75a47d33661223c9e5cf5fb0cb9c0d14",
    "pair_xorder": "662c7839185260ae9c0d68edf6a323ac79743707a913cc1bd5f90b62714ebce3",
    "r3_gaps": "8a31632907b171483cd40a053231c702e378f944af33f92598a6141bd052cdeb",
    "f6b_report": "9070ed53f970f480e88b1de3aa19792f8b637de51857935fa6b7c51fa8a015d6",
    "verdict": "2a3c8cf465c0ac1f808c1fdf7409725ab04862e4a8002f7ff71cfa299770bb5b",
    "card": "78a96a7fc4daaa9f700dc9852d2e8114e7a214afc249cee1e587a8f719108f15",
}

# ---- closed-form constants (card v1.2 R-4 / plan §1) -------------------------
PITCH = 1.46
LANE_LO = 33.3
N_LANES = 32
N_USED = 16
LANE_BASE = (N_LANES - N_USED) // 2            # 8, card R-4
VIA_VIA = 0.525
STAGGER = 0.38
MIN_XSTEP = 0.6
GRID = 0.05
R3_OFF = -0.3
R3_STEP = 0.6
POL_OFF = 0.19
REACH = 45.4
TOL = 1e-9
CORRIDOR_BOUNDS = {"EAST_CHIP_TO_J2": (105.25, 132.65),
                   "WEST_MCIO_TO_CHIP": (65.05, 82.35)}
ENTRY_X = {"EAST_CHIP_TO_J2": 105.25, "WEST_MCIO_TO_CHIP": 82.35}

FORBIDDEN_NAMES = {
    "dfs", "backtrack", "csp", "branch_and_bound", "search", "enumerate",
    "permutations", "combinations", "product", "itertools", "random", "shuffle",
    "while", "recursion", "node_cap", "alternatives", "candidates_tried",
}
FORBIDDEN_SUBSTR = ("dfs", "backtrack", "csp", "branch_and_bound", "search",
                    "enumerate", "permutations", "combinations", "product",
                    "itertools", "random", "shuffle", "recursion", "node_cap",
                    "alternatives", "candidates_tried")
FORBIDDEN_ARTIFACT_KEYS = {"alternatives", "options", "tried", "branch", "attempts", "node"}
CERT_FIELDS = {"kind", "layer", "rule", "closed_form_condition", "observed",
               "required", "page_or_pad", "scope_note"}

REV = "W3-CN-VAL.1"


# =============================================================================
# helpers
# =============================================================================
def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def load_json_retry(p, tries=4):
    last = None
    for _ in range(tries):
        try:
            return load_json(p)
        except Exception as e:  # concurrent writer
            last = e
            time.sleep(0.5)
    raise last


def r6(v):
    return round(float(v), 6)


def near(a, b, tol=1e-9):
    return abs(float(a) - float(b)) <= tol


def dist2d(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def run_engine(extra, out_main, out_landing=None, timeout=300):
    cmd = [sys.executable, str(ENGINE)] + list(extra) + ["--out", str(out_main)]
    if out_landing is not None:
        cmd += ["--landing-out", str(out_landing)]
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, cwd=str(K2), capture_output=True, text=True, timeout=timeout)
    dt = time.perf_counter() - t0
    return {"cmd": cmd, "rc": proc.returncode, "stdout": proc.stdout,
            "stderr": proc.stderr, "seconds": dt}


def parse_work_units(text):
    for line in text.splitlines():
        if "work_units=" in line:
            tok = line.split("work_units=", 1)[1].split()[0]
            return int(tok.split("/")[0])
    return None


# =============================================================================
# G-M1  static zero-search token gate
# =============================================================================
def gm1_token_scan(src_path):
    hits = []
    with open(src_path, "rb") as fh:
        try:
            for tok in tokenize.tokenize(fh.readline):
                if tok.type in (tokenize.COMMENT, tokenize.NL, tokenize.STRING):
                    continue
                if tok.type == tokenize.NAME and tok.string in FORBIDDEN_NAMES:
                    hits.append({"line": tok.start[0], "token": tok.string})
        except tokenize.TokenError as e:
            hits.append({"line": -1, "token": "TOKENIZE_ERROR:" + str(e)})
    tree = ast.parse(Path(src_path).read_text(encoding="utf-8"))
    attrs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            for sub in FORBIDDEN_SUBSTR:
                if sub in node.attr:
                    attrs.append({"line": node.lineno, "attr": node.attr, "sub": sub})
    return hits, attrs


# =============================================================================
# G-M2  AST structure
# =============================================================================
def _called_names(fn):
    # only bare-name calls are followed for the in-module call graph; attribute
    # calls (e.g. hashlib.sha256) are library calls, not local recursion.
    names = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            names.add(node.func.id)
    return names


def _branch_counts(fn):
    """if/elif/else *chains* (top-level If constructs) + conditional expressions."""
    chains = 0
    ifexps = 0
    for node in ast.walk(fn):
        if isinstance(node, ast.If):
            # a chain head: not the orelse of a parent If
            chains += 1  # counted per If below; corrected by parent subtraction
        if isinstance(node, ast.IfExp):
            ifexps += 1
    # subtract elif/else members (If nodes that are the .orelse of a parent If)
    child_ifs = 0
    for node in ast.walk(fn):
        if isinstance(node, ast.If) and isinstance(node.orelse, list) and node.orelse:
            for sub in node.orelse:
                if isinstance(sub, ast.If):
                    child_ifs += 1
    chains -= child_ifs
    return {"chains": chains, "ifexps": ifexps, "branch_sites": chains + ifexps}


def gm2_ast_scan(src_path):
    src = Path(src_path).read_text(encoding="utf-8")
    tree = ast.parse(src)
    funcs = {n.name: n for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    graph = {name: _called_names(fn) for name, fn in funcs.items()}
    # recursion cycle detection (direct or via a helper it defines)
    cycles = []
    for start in graph:
        stack = [(start, [start])]
        seen = set()
        while stack:
            cur, path = stack.pop()
            for callee in graph.get(cur, ()):
                if callee == start and len(path) >= 1:
                    cycles.append(path + [start])
                elif callee in graph and callee not in seen:
                    seen.add(callee)
                    stack.append((callee, path + [callee]))
    self_direct = [n for n, c in graph.items() if n in c]
    whiles = [{"line": n.lineno} for n in ast.walk(tree) if isinstance(n, ast.While)]
    bad_imports = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name in ("itertools", "random"):
                    bad_imports.append({"line": n.lineno, "import": a.name})
        elif isinstance(n, ast.ImportFrom):
            if n.module in ("itertools", "random"):
                bad_imports.append({"line": n.lineno, "from": n.module})
    per_fn = {}
    for name, fn in funcs.items():
        per_fn[name] = _branch_counts(fn)
        per_fn[name]["line"] = fn.lineno
    return {"functions": sorted(funcs), "self_direct": self_direct,
            "recursion_cycles": cycles, "whiles": whiles,
            "bad_imports": bad_imports, "branch_sites": per_fn}


# =============================================================================
# independent closed-form re-derivation (G-M4)
# =============================================================================
def build_frames(manifest, lane_frame):
    """frame = (corridor, conn_ref, band); in-frame order = F-5 lane order."""
    order = {}
    for cid, cd in lane_frame["corridors"].items():
        for fr in cd["frames"]:
            for p in fr["pages"]:
                order[p["page_id"]] = p["order_index"]
    data = [p for p in manifest["pages"] if p["kind"] == "data"]
    groups = {}
    for p in data:
        cid = "EAST_CHIP_TO_J2" if p["side"] == "east" else "WEST_MCIO_TO_CHIP"
        cref = p["anchors"]["conn"]["P"]["ref"]
        band = None
        for cd in lane_frame["corridors"].values():
            for fr in cd["frames"]:
                if any(q["page_id"] == p["page_id"] for q in fr["pages"]):
                    band = fr["band"]
        groups.setdefault((cid, cref, band), []).append(p["page_id"])
    out = []
    for key, ids in groups.items():
        ids = sorted(ids, key=lambda pid: (order.get(pid, 10 ** 9), pid))
        rows = [(p["anchors"]["conn"]["P"]["pad_global"][1] +
                 p["anchors"]["conn"]["N"]["pad_global"][1]) / 2
                for p in data if p["page_id"] in ids]
        out.append({"corridor": key[0], "conn_ref": key[1], "band": key[2],
                    "pages": ids, "row_span": [min(rows), max(rows)]})
    out.sort(key=lambda fr: (fr["corridor"], fr["row_span"][0], fr["conn_ref"], fr["band"]))
    return out


def derive_r2(frames):
    out = {}
    for cid in ("EAST_CHIP_TO_J2", "WEST_MCIO_TO_CHIP"):
        cursor = LANE_BASE
        for fr in [f for f in frames if f["corridor"] == cid]:
            for j, pid in enumerate(fr["pages"]):
                idx = cursor + j
                out[pid] = {"lane_index": idx, "lane_y": r6(LANE_LO + idx * PITCH)}
            cursor += len(fr["pages"])
    return out


def derive_r1(facts, frames, xorder, verdict, manifest):
    """Card R-4 R1: frame prefix-monotone x (min step 0.6) + band-escape y.

    Interpretation fixed from the card text:
      * direction s = sign(pad_x[P][last] - pad_x[P][first]) in F-5 order;
      * per polarity prefix (seed = first column in direction);
      * P_x = first admissible x >= prev+0.6 (decreasing frame: <= prev-0.6);
      * N_x = first admissible partner of P_x meeting the same prefix bound;
      * at most one closed-form fallback (next P column) if P_x has no partner;
      * y  = candidate at (x) closest to pad_y + e_band*0.05 (grid k in {0,1}),
             e_band = -1 (up) / +1 (dn);
      * at most one pair-distance correction (farthest y) if dist<0.525 or |dx|<0.38.
    """
    vpages = verdict.get("pages", verdict) if isinstance(verdict, dict) else verdict
    out, certs = {}, []
    ycands = {}
    for pid, f in facts.items():
        for pol in ("P", "N"):
            d = {}
            for c in vpages[pid][pol]["cands"]:
                d.setdefault(r6(c[0]), []).append(r6(c[1]))
            for k in d:
                d[k] = sorted(set(d[k]))
            ycands[(pid, pol)] = d
    for fr in frames:
        ids = fr["pages"]
        px_first = facts[ids[0]]["pad"]["P"][0]
        px_last = facts[ids[-1]]["pad"]["P"][0]
        s = 1 if px_last >= px_first else -1
        e_band = -1.0 if fr["band"] == "up" else 1.0
        prev = {"P": None, "N": None}
        for pid in ids:
            f = facts[pid]
            cols = {}
            for row in xorder[pid]["x_column_pairs"]:
                cols.setdefault(r6(row[0]), []).append(r6(row[1]))
            for k in cols:
                cols[k] = sorted(set(cols[k]))
            px_all = sorted(cols)
            chosen = None
            for attempt in (0, 1):
                if prev["P"] is None:
                    pool = list(px_all)
                elif s > 0:
                    pool = [x for x in px_all if x >= prev["P"] + MIN_XSTEP - TOL]
                else:
                    pool = [x for x in px_all if x <= prev["P"] - MIN_XSTEP + TOL]
                if not pool:
                    break
                pool = sorted(pool)
                px = pool[0] if s > 0 else pool[-1]
                if attempt == 1:
                    # move one step further along the direction
                    if s > 0:
                        nxt = [x for x in pool if x > px + TOL]
                    else:
                        nxt = [x for x in pool if x < px - TOL]
                    if not nxt:
                        break
                    px = min(nxt) if s > 0 else max(nxt)
                nxs = cols[px]
                if prev["N"] is None:
                    nsel = nxs
                elif s > 0:
                    nsel = [x for x in nxs if x >= prev["N"] + MIN_XSTEP - TOL]
                else:
                    nsel = [x for x in nxs if x <= prev["N"] - MIN_XSTEP + TOL]
                if not nsel:
                    continue
                nx = sorted(nsel)[0] if s > 0 else sorted(nsel)[-1]
                chosen = (px, nx)
                break
            if chosen is None:
                certs.append({"page": pid, "frame": [fr["corridor"], fr["conn_ref"], fr["band"]]})
                prev["P"], prev["N"] = prev["P"], prev["N"]
                continue
            px, nx = chosen
            pair = {}
            for pol, x in (("P", px), ("N", nx)):
                ys = ycands[(pid, pol)].get(x)
                if not ys:
                    continue
                pair[pol] = min(ys, key=lambda y: (abs(y - (f["pad"][pol][1] + e_band * GRID)), y))
            if "P" not in pair or "N" not in pair:
                certs.append({"page": pid, "frame": [fr["corridor"], fr["conn_ref"], fr["band"]]})
                continue
            pv = [px, pair["P"]]
            nv = [nx, pair["N"]]
            d = dist2d(pv, nv)
            if d < VIA_VIA - TOL or abs(pv[0] - nv[0]) < STAGGER - TOL:
                for pol, x, other in (("N", nx, pv), ("P", px, nv)):
                    ys = ycands[(pid, pol)].get(x) or []
                    if ys:
                        y1 = max(ys, key=lambda y: (abs(y - other[1]), -y))
                        if pol == "N":
                            nv = [nx, y1]
                        else:
                            pv = [px, y1]
                d = dist2d(pv, nv)
            out[pid] = {"P_via": [r6(pv[0]), r6(pv[1])], "N_via": [r6(nv[0]), r6(nv[1])],
                        "pair_dist_mm": r6(d), "stagger_mm": r6(abs(pv[0] - nv[0])),
                        "frame": [fr["corridor"], fr["conn_ref"], fr["band"]],
                        "direction": "increasing" if s > 0 else "decreasing"}
            prev["P"], prev["N"] = pv[0], nv[0]
    return {"assignment": out, "certificates": certs}


def _pol_off(f, pol):
    d = f["pad"]["N"][1] - f["pad"]["P"][1]
    base = -POL_OFF if d > 0 else POL_OFF
    return base if pol == "P" else -base


def derive_r15(facts, r1, r2):
    out = {}
    for pid, f in facts.items():
        if pid not in r1["assignment"]:
            continue
        entry = ENTRY_X[f["corridor"]]
        segs = {}
        for pol in ("P", "N"):
            src = r1["assignment"][pid][pol + "_via"]
            tgt = [r6(entry), r6(r2[pid]["lane_y"] + _pol_off(f, pol))]
            segs[pol] = [src, tgt]
        out[pid] = {"entry_x": r6(entry), "lane_entry_y": r2[pid]["lane_y"],
                    "segments": segs}
    return out


def derive_r3(gaps):
    pads = []
    for cref in sorted(gaps["connectors"]):
        for xc, col in sorted(gaps["connectors"][cref]["columns"].items(),
                              key=lambda kv: float(kv[0])):
            for en in col["entries"]:
                band = en.get("y_band") or [en["y"] - 0.3, en["y"] + 0.3]
                pads.append({"ref": cref, "net": en["net"], "y": r6(en["y"]),
                             "cands": sorted(float(c) for c in en["gap_candidates"]),
                             "band": [r6(band[0]), r6(band[1])], "pol": en["pol"],
                             "page": en["page"], "kind": en["kind"], "pad_x": float(xc)})
    groups = {}
    for pd in pads:
        groups.setdefault((pd["ref"], pd["cands"][0]), []).append(pd)
    out = {}
    for (cref, colx) in sorted(groups):
        grp = sorted(groups[(cref, colx)], key=lambda q: (q["y"], q["net"]))
        prev = None
        for pd in grp:
            y = pd["y"] + R3_OFF if prev is None else max(pd["y"] + R3_OFF, prev + R3_STEP)
            out[cref + "|" + pd["net"]] = {
                "ref": cref, "net": pd["net"], "pad_y": pd["y"], "pad_x": r6(pd["pad_x"]),
                "y_band": pd["band"], "column_x": r6(colx), "landing": [r6(colx), r6(y)],
                "kind": pd["kind"], "page": pd["page"], "pol": pd["pol"],
                "gap_column_candidates": pd["cands"]}
            prev = y
    return out


def derive_refclk(manifest, w0r):
    pw = w0r["refclk_passage_witness"]
    eu = pw["transition_columns"]["east_rise"]["x_centre_range"]
    rise_x = r6(eu[0] + 0.5)
    chan = pw["per_page"]["PCIE_REFCLK1/input"]["alternative_windows_same_side"][0]
    west = CORRIDOR_BOUNDS["WEST_MCIO_TO_CHIP"][1]
    east = CORRIDOR_BOUNDS["EAST_CHIP_TO_J2"][0]
    out = {}
    for pg in sorted([p for p in manifest["pages"] if p["kind"] != "data"],
                     key=lambda p: p["page_id"]):
        pid = pg["page_id"]
        j2 = [r6(pg["anchors"]["conn"]["P"]["pad_global"][0]),
              r6(pg["anchors"]["conn"]["P"]["pad_global"][1])]
        far = [r6(pg["anchors"]["conn2"]["P"]["pad_global"][0]),
               r6(pg["anchors"]["conn2"]["P"]["pad_global"][1])]
        crossing_y = j2[1] if abs(far[1] - j2[1]) <= 3.2 else r6(max(far[1], chan[0]) + GRID)
        pts = [j2, [r6(east), j2[1]], [rise_x, j2[1]], [rise_x, crossing_y],
               [r6(west), crossing_y], [far[0], far[1]]]
        path = [pts[0]]
        for pt in pts[1:]:
            if abs(pt[0] - path[-1][0]) > TOL or abs(pt[1] - path[-1][1]) > TOL:
                path.append(pt)
        out[pid] = {"layer": "F.Cu", "lane_y": j2[1], "path": path}
    return out


def derive_nodes(facts, r1, r2, r3, verdict):
    """Re-derive the per-page P/N node chains from the card layer semantics."""
    out = {}
    for pid, f in sorted(facts.items()):
        a = r1["assignment"].get(pid)
        if not a:
            out[pid] = {}
            continue
        cid = f["corridor"]
        ent, ext = CORRIDOR_BOUNDS[cid]
        r3a = r3.get(f["conn_ref"] + "|" + f["nets"]["P"])
        nodes = {}
        for pol in ("P", "N"):
            ly = r6(r2[pid]["lane_y"] + _pol_off(f, pol))
            v1 = a[pol + "_via"]
            nodes[pol] = [
                [f["pad"][pol][0], f["pad"][pol][1], "F.Cu"],
                [v1[0], v1[1], "F.Cu"], [v1[0], v1[1], "In2.Cu"],
                [ent, ly, "In2.Cu"], [ext, ly, "In2.Cu"], [ext, ly, "In2.Cu"],
                [ext, ly, "F.Cu"],
                [r3a["landing"][0], r3a["landing"][1], "F.Cu"] if r3a else None,
                [f["conn_pad"][pol][0], f["conn_pad"][pol][1], "F.Cu"],
            ]
            nodes[pol] = [n for n in nodes[pol] if n is not None]
        out[pid] = nodes
    return out


# geometry helpers
def seg_cross(p, q, r, s):
    def o(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2, d3, d4 = o(r, s, p), o(r, s, q), o(p, q, r), o(p, q, s)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def seg_box_hit(p, q, box):
    (x0, y0), (x1, y1) = box
    slo = [min(p[i], q[i]) for i in (0, 1)]
    shi = [max(p[i], q[i]) for i in (0, 1)]
    return slo[0] <= x1 and shi[0] >= x0 and slo[1] <= y1 and shi[1] >= y0


def count_crossings(segs):
    keys = sorted(segs)
    n = 0
    pairs = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            pa, pb = segs[keys[i]], segs[keys[j]]
            for s1 in zip(pa, pa[1:]):
                for s2 in zip(pb, pb[1:]):
                    if seg_cross(s1[0], s1[1], s2[0], s2[1]):
                        n += 1
                        pairs.append([keys[i], keys[j]])
    return n, pairs


# =============================================================================
# checks
# =============================================================================
def chk(cid, assertion, expected, observed, ok):
    return {"id": cid, "assertion": assertion, "expected": expected,
            "observed": observed, "ok": bool(ok)}


def check_acn1(doc, verdict, manifest):
    """R1: 64 vias in frozen candidate lists, pair dist>=0.525, |dx|>=0.38,
    pairwise >=0.525, frame per-polarity x strictly monotone."""
    out = []
    r1 = doc.get("layers", {}).get("R1", {}).get("assignment", {}) or {}
    misses = []
    pairs_bad = []
    vias = []
    for pid, a in sorted(r1.items()):
        for pol in ("P", "N"):
            x, y = a[pol + "_via"]
            vias.append((pid + "." + pol, [x, y]))
            hit = any(near(c[0], x) and near(c[1], y)
                      for c in verdict["pages"][pid][pol]["cands"])
            if not hit:
                misses.append([pid, pol, x, y])
        d = dist2d(a["P_via"], a["N_via"])
        dx = abs(a["P_via"][0] - a["N_via"][0])
        if d < VIA_VIA - TOL or dx < STAGGER - TOL:
            pairs_bad.append([pid, r6(d), r6(dx)])
    vv_bad = []
    for i in range(len(vias)):
        for j in range(i + 1, len(vias)):
            dd = dist2d(vias[i][1], vias[j][1])
            if dd < VIA_VIA - TOL:
                vv_bad.append([vias[i][0], vias[j][0], r6(dd)])
    # frame monotonicity (independent frame build)
    frames = build_frames(manifest, load_json(FILES["lane_frame"]))
    facts = {}
    for p in manifest["pages"]:
        facts[p["page_id"]] = p
    mono_bad = []
    order = {}
    lf = load_json(FILES["lane_frame"])
    for cd in lf["corridors"].values():
        for fr in cd["frames"]:
            for q in fr["pages"]:
                order[q["page_id"]] = q["order_index"]
    for fr in frames:
        ids = [pid for pid in fr["pages"] if pid in r1]
        if len(ids) < 2:
            continue
        p0 = facts[ids[0]]["anchors"]["chip"]["P"]["pad_global"][0]
        p1 = facts[ids[-1]]["anchors"]["chip"]["P"]["pad_global"][0]
        s = 1 if p1 >= p0 else -1
        for pol in ("P", "N"):
            xs = [r1[pid][pol + "_via"][0] for pid in ids]
            for i in range(len(xs) - 1):
                bad = xs[i + 1] <= xs[i] + TOL if s > 0 else xs[i + 1] >= xs[i] - TOL
                if bad:
                    mono_bad.append([fr["conn_ref"], fr["band"], pol, r6(xs[i]), r6(xs[i + 1])])
    out.append(chk("A-CN.1.count", "R1 emits exactly 64 vias (32 pages x P/N)",
                   "64", str(len(vias)), len(vias) == 64))
    out.append(chk("A-CN.1.cands", "every R1 via in frozen verdict candidate list (exact)",
                   "0 miss", str(len(misses)) + (" first=" + str(misses[0]) if misses else ""),
                   not misses))
    out.append(chk("A-CN.1.pair", "per page pair dist>=0.525 and |dx|>=0.38",
                   "0 bad", str(len(pairs_bad)) + (" first=" + str(pairs_bad[0]) if pairs_bad else ""),
                   not pairs_bad))
    out.append(chk("A-CN.1.allpairs", "all 64 vias pairwise >=0.525",
                   "0 bad", str(len(vv_bad)) + (" first=" + str(vv_bad[0]) if vv_bad else ""),
                   not vv_bad))
    out.append(chk("A-CN.1.mono", "frame=(corridor,conn_ref,band) per-polarity x strictly monotone in F-5 order",
                   "0 bad", str(len(mono_bad)) + (" first=" + str(mono_bad[0]) if mono_bad else ""),
                   not mono_bad))
    return out, {"misses": misses, "pair_bad": pairs_bad, "via_via_bad": vv_bad,
                 "mono_bad": mono_bad, "n_vias": len(vias)}


def check_acn2(doc, manifest, lane_frame):
    out = []
    lanes = doc.get("layers", {}).get("R2", {}).get("assignment", {}) or {}
    facts = {}
    for p in manifest["pages"]:
        if p["kind"] == "data":
            facts[p["page_id"]] = {
                "conn_row_y": (p["anchors"]["conn"]["P"]["pad_global"][1] +
                               p["anchors"]["conn"]["N"]["pad_global"][1]) / 2,
                "chip_row_y": (p["anchors"]["chip"]["P"]["pad_global"][1] +
                               p["anchors"]["chip"]["N"]["pad_global"][1]) / 2,
                "corridor": "EAST_CHIP_TO_J2" if p["side"] == "east" else "WEST_MCIO_TO_CHIP",
            }
    seq_bad = []
    pred_bad = []
    frames = build_frames(manifest, lane_frame)   # card order: EAST up->dn; WEST by conn row
    for cid in ("EAST_CHIP_TO_J2", "WEST_MCIO_TO_CHIP"):
        ids = [pid for fr in frames if fr["corridor"] == cid for pid in fr["pages"]]
        idxs = [lanes[pid]["lane_index"] for pid in ids if pid in lanes]
        for i in range(len(idxs) - 1):
            if idxs[i + 1] <= idxs[i]:
                seq_bad.append([cid, ids[i], ids[i + 1], idxs[i], idxs[i + 1]])
    for pid, f in facts.items():
        if pid not in lanes:
            continue
        ly = lanes[pid]["lane_y"]
        if abs(ly - f["conn_row_y"]) > REACH + TOL or abs(ly - f["chip_row_y"]) > REACH + TOL:
            pred_bad.append([pid, r6(ly - f["conn_row_y"]), r6(ly - f["chip_row_y"])])
    n_lane = len(lanes)
    out.append(chk("A-CN.2.count", "R2 assigns exactly 32 data-page lanes",
                   "32", str(n_lane), n_lane == 32))
    out.append(chk("A-CN.2.mono", "per-corridor lane_index strictly increasing in F-5 lane order",
                   "0 bad", str(len(seq_bad)) + (" first=" + str(seq_bad[0]) if seq_bad else ""),
                   not seq_bad))
    out.append(chk("A-CN.2.reach", "|lane_y-conn_row_y|<=45.4 and |lane_y-chip_row_y|<=45.4",
                   "0 bad", str(len(pred_bad)) + (" first=" + str(pred_bad[0]) if pred_bad else ""),
                   not pred_bad))
    return out, {"seq_bad": seq_bad, "pred_bad": pred_bad, "n_lanes": n_lane}


def check_acn3(doc, gaps):
    out = []
    r3 = doc.get("layers", {}).get("R3", {}).get("assignment", {}) or {}
    pads = {}
    for cref in gaps["connectors"]:
        for xc, col in gaps["connectors"][cref]["columns"].items():
            for en in col["entries"]:
                band = en.get("y_band") or [en["y"] - 0.3, en["y"] + 0.3]
                pads[(cref, en["net"])] = {"cands": [float(c) for c in en["gap_candidates"]],
                                           "band": [float(band[0]), float(band[1])]}
    landing_by_pad = {}
    x_bad, band_bad, dup_bad = [], [], []
    for key, a in r3.items():
        net = a.get("net")
        if net is None and "|" in key:
            net = key.split("|", 1)[1]
        cref = a.get("ref")
        if cref is None and "|" in key:
            cref = key.split("|", 1)[0]
        info = pads.get((cref, net))
        if info is None:
            continue
        landing_by_pad.setdefault((cref, net), []).append(a)
        lx, ly = a["landing"]
        if not any(near(c, lx) for c in info["cands"]):
            x_bad.append([cref, net, lx, info["cands"]])
        if ly < info["band"][0] - TOL or ly > info["band"][1] + TOL:
            band_bad.append([cref, net, ly, info["band"]])
    # same-column separation over emitted landings
    by_col = {}
    for key, a in r3.items():
        by_col.setdefault(r6(a["column_x"]), []).append((key, a["landing"][1]))
    for cxk, items in by_col.items():
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if abs(items[i][1] - items[j][1]) < VIA_VIA - TOL:
                    dup_bad.append([cxk, items[i][0], items[j][0],
                                    r6(abs(items[i][1] - items[j][1]))])
    for k, v in landing_by_pad.items():
        if len(v) != 1:
            x_bad.append(["dup-or-missing", k, len(v)])
    missing = [k for k in pads if k not in landing_by_pad]
    extra = [k for k in landing_by_pad if k not in pads]
    n_land = len(r3)
    out.append(chk("A-CN.3.count", "R3 exactly 72 landings (one per F-8 pad)",
                   "72", str(n_land) + (f" missing={len(missing)} extra={len(extra)}" if (missing or extra) else ""),
                   n_land == 72 and not missing and not extra))
    out.append(chk("A-CN.3.column", "every landing x in that pad's F-8 gap_candidates",
                   "0 bad", str(len(x_bad)) + (" first=" + str(x_bad[0]) if x_bad else ""),
                   not x_bad))
    out.append(chk("A-CN.3.band", "every landing y inside that pad's F-8 y_band",
                   "0 bad", str(len(band_bad)) + (" first=" + str(band_bad[0]) if band_bad else ""),
                   not band_bad))
    out.append(chk("A-CN.3.sep", "landings sharing column_x are >=0.525 apart",
                   "0 bad", str(len(dup_bad)) + (" first=" + str(dup_bad[0]) if dup_bad else ""),
                   not dup_bad))
    return out, {"x_bad": x_bad, "band_bad": band_bad, "sep_bad": dup_bad,
                 "missing": missing, "extra": extra, "n_land": n_land}


def _extract_r15_segments(doc, manifest):
    sign = {}
    for p in manifest["pages"]:
        if p["kind"] != "data":
            continue
        dy = p["anchors"]["chip"]["N"]["pad_global"][1] - p["anchors"]["chip"]["P"]["pad_global"][1]
        base = -POL_OFF if dy > 0 else POL_OFF
        sign[p["page_id"]] = {"P": base, "N": -base}
    segs = {}
    for pg in doc.get("pages", []):
        pid = pg.get("page_id")
        if pg.get("kind") != "data":
            continue
        r15 = pg.get("r1_5")
        r1 = pg.get("r1")
        if not r15 or not r1:
            continue
        entry = r15.get("entry_x")
        ly = r15.get("lane_entry_y")
        for pol in ("P", "N"):
            v = (r1.get(pol) or {}).get("via")
            if v is None:
                continue
            tgt = [entry, r6(ly + sign.get(pid, {"P": POL_OFF, "N": -POL_OFF})[pol])]
            segs[f"{pid}.{pol}"] = [[v[0], v[1]], [tgt[0], tgt[1]]]
    return segs


def check_acn4(doc, manifest):
    segs = _extract_r15_segments(doc, manifest)
    n, pairs = count_crossings(segs)
    return [chk("A-CN.4.cross", "R1.5 emitted segment-segment crossings == 0 (independent O(n^2))",
                "0", str(n) + (" first=" + str(pairs[0]) if pairs else ""), n == 0)], \
           {"n_segments": len(segs), "n_crossings": n, "crossing_pairs": pairs[:10]}


def check_acn5(doc, w0r):
    out = []
    pw = w0r["refclk_passage_witness"]
    boxes = []
    for b in pw["blockers"]:
        boxes.append((b["ref"], ([b["keepout_x"][0], b["keepout_y"][0]],
                                 [b["keepout_x"][1], b["keepout_y"][1]])))
    rfc = doc.get("layers", {}).get("REFCLK", {}).get("assignment", {}) or {}
    hits = []
    segs_by_page = {}
    for pid, v in sorted(rfc.items()):
        path = v.get("path") or []
        segs_by_page[pid] = path
        for s1 in zip(path, path[1:]):
            for ref, box in boxes:
                if seg_box_hit(s1[0], s1[1], box):
                    hits.append([pid, ref, [r6(s1[0][0]), r6(s1[0][1])],
                                 [r6(s1[1][0]), r6(s1[1][1])]])
    # free-window containment: every segment must be countable to a W0-R witness window
    slices = pw.get("slices", [])
    free_bad = []
    for pid, path in segs_by_page.items():
        for s1 in zip(path, path[1:]):
            x0, x1 = sorted([s1[0][0], s1[1][0]])
            y0, y1 = sorted([s1[0][1], s1[1][1]])
            ok = False
            for sl in slices:
                xr = sl["x_range"]
                if x1 < xr[0] - TOL or x0 > xr[1] + TOL:
                    continue
                for w in sl["free_channels_ge_extent"]:
                    if y0 >= w[0] - TOL and y1 <= w[1] + TOL:
                        ok = True
            # transition columns (east rise / west descent) also count as free windows
            for tc in pw.get("transition_columns", {}).values():
                for w in tc.get("free_y", []) or tc.get("free_y_channels", []) or []:
                    if y0 >= w[0] - TOL and y1 <= w[1] + TOL:
                        ok = True
            if not ok:
                free_bad.append([pid, [r6(s1[0][0]), r6(s1[0][1])],
                                 [r6(s1[1][0]), r6(s1[1][1])]])
    lane_ys = sorted(v.get("lane_y") for v in rfc.values() if v.get("lane_y") is not None)
    sep_ok = all(lane_ys[i + 1] - lane_ys[i] >= PITCH - TOL for i in range(len(lane_ys) - 1))
    out.append(chk("A-CN.5.keepout", "no REFCLK segment intersects any of the 11 keepout boxes",
                   "0 hits", str(len(hits)) + (" first=" + str(hits[0]) if hits else ""),
                   not hits))
    out.append(chk("A-CN.5.window", "every REFCLK segment lies inside a W0-R witness free window",
                   "0 bad", str(len(free_bad)) + (" first=" + str(free_bad[0]) if free_bad else ""),
                   not free_bad))
    out.append(chk("A-CN.5.sep", "REFCLK page-to-page lane separation >=1.46",
                   "True", str(sep_ok) + " " + str([r6(y) for y in lane_ys]), sep_ok))
    return out, {"keepout_hits": hits, "window_bad": free_bad, "lane_y": lane_ys,
                 "sep_ok": sep_ok, "n_boxes": len(boxes)}


def check_certificates(doc):
    certs = doc.get("certificates", []) or []
    kind_bad, field_bad, global_bad = [], [], []
    for i, c in enumerate(certs):
        if c.get("kind") != "CONSTRUCTION_INFEASIBLE":
            kind_bad.append([i, c.get("kind")])
        extra = set(c.keys()) - CERT_FIELDS
        if extra:
            field_bad.append([i, sorted(extra)])
        note = str(c.get("scope_note", ""))
        if ("global" in note.lower() and "not" not in note.lower()
                and "非全局" not in note and "非 全局" not in note):
            global_bad.append([i, note[:80]])
        if not note.strip():
            global_bad.append([i, "<empty scope_note>"])
    has = len(certs) > 0
    res = [chk("A-CN.cert.discipline",
               "certificates (if any) are CONSTRUCTION_INFEASIBLE only, fields limited, scope=construction-only",
               "0 violations", f"n_certs={len(certs)} kind_bad={len(kind_bad)} "
               f"field_bad={len(field_bad)} global_bad={len(global_bad)}",
               not kind_bad and not field_bad and not global_bad)]
    return res, {"n_certs": len(certs), "kind_bad": kind_bad,
                 "field_bad": field_bad, "global_bad": global_bad, "has_certs": has}


def check_acn7(doc, main_path):
    out = []
    verdict = doc.get("verdict")
    pages = doc.get("pages", [])
    if verdict == "FEASIBLE_ALL":
        node_bad = [p.get("page_id") for p in pages if not (p.get("nodes") or {})]
        n_pages = len(pages)
        out.append(chk("A-CN.7.pages", "FEASIBLE_ALL => 34 pages with non-empty node chains",
                       "34 pages, 0 empty", f"{n_pages} pages, empty={len(node_bad)}",
                       n_pages == 34 and not node_bad))
        land_ok = ART_LANDING.exists()
        chain_ok = False
        land_sha = None
        if land_ok:
            try:
                land = load_json_retry(ART_LANDING)
                land_sha = land.get("authority", {}).get("main_sha256")
                chain_ok = (land_sha == sha256_file(main_path))
            except Exception as e:
                land_ok = False
                land_sha = "ERR:" + str(e)
        out.append(chk("A-CN.7.landing",
                       "FEASIBLE_ALL => chip_landing_rows.json present, sha chain main_sha256 == main artifact sha256",
                       "present + sha match",
                       f"present={land_ok} land.main_sha256={str(land_sha)[:16]}",
                       land_ok and chain_ok))
    else:
        out.append(chk("A-CN.7.pages", "FEASIBLE_ALL required for A-CN.7 (verdict mode)",
                       "FEASIBLE_ALL", str(verdict), verdict == "FEASIBLE_ALL"))
        out.append(chk("A-CN.7.landing", "FEASIBLE_ALL required for re-emission",
                       "FEASIBLE_ALL + landing file",
                       f"verdict={verdict} landing_file={ART_LANDING.exists()}",
                       verdict == "FEASIBLE_ALL" and ART_LANDING.exists()))
    return out, {"verdict": verdict}


# ---- G-M4 comparison --------------------------------------------------------
def check_gm4(doc, manifest, lane_frame, gaps, w0r, verdict):
    mism = []
    facts = {}
    for p in manifest["pages"]:
        if p["kind"] != "data":
            continue
        c = p["anchors"]["chip"]
        co = p["anchors"]["conn"]
        facts[p["page_id"]] = {
            "pad": {"P": list(c["P"]["pad_global"]), "N": list(c["N"]["pad_global"])},
            "conn_pad": {"P": list(co["P"]["pad_global"]), "N": list(co["N"]["pad_global"])},
            "nets": {"P": co["P"]["net"], "N": co["N"]["net"]},
            "conn_ref": co["P"]["ref"],
            "corridor": "EAST_CHIP_TO_J2" if p["side"] == "east" else "WEST_MCIO_TO_CHIP",
        }
    frames = build_frames(manifest, lane_frame)

    def note(kind, pid, field, mine, theirs):
        mism.append({"kind": kind, "page": pid, "field": field,
                     "derived": mine, "artifact": theirs})

    # R2
    r2d = derive_r2(frames)
    r2a = doc.get("layers", {}).get("R2", {}).get("assignment", {}) or {}
    for pid, v in r2d.items():
        a = r2a.get(pid)
        if a is None:
            note("R2", pid, "missing", v, None)
            continue
        if int(a.get("lane_index", -1)) != v["lane_index"]:
            note("R2", pid, "lane_index", v["lane_index"], a.get("lane_index"))
        if not near(a.get("lane_y", 1e9), v["lane_y"]):
            note("R2", pid, "lane_y", v["lane_y"], a.get("lane_y"))

    # R1
    xorder = {pid: load_json(FILES["pair_xorder"])["pages"][pid] for pid in facts}
    # reload once (avoid repeated IO)
    xo_all = load_json(FILES["pair_xorder"])["pages"]
    xorder = {pid: xo_all[pid] for pid in facts}
    r1d = derive_r1(facts, frames, xorder, verdict, manifest)
    r1a = doc.get("layers", {}).get("R1", {}).get("assignment", {}) or {}
    for pid, v in r1d["assignment"].items():
        a = r1a.get(pid)
        if a is None:
            note("R1", pid, "missing", v, None)
            continue
        for pol in ("P", "N"):
            if not (near(a[pol + "_via"][0], v[pol + "_via"][0]) and
                    near(a[pol + "_via"][1], v[pol + "_via"][1])):
                note("R1", pid, pol + "_via", v[pol + "_via"], a[pol + "_via"])
    for pid in r1a:
        if pid not in r1d["assignment"]:
            note("R1", pid, "unexpected", None, r1a[pid])

    # R3
    r3d = derive_r3(gaps)
    r3a = doc.get("layers", {}).get("R3", {}).get("assignment", {}) or {}
    for pid, v in r3d.items():
        a = r3a.get(pid)
        if a is None:
            note("R3", pid, "missing", v["landing"], None)
            continue
        if not (near(a["landing"][0], v["landing"][0]) and near(a["landing"][1], v["landing"][1])):
            note("R3", pid, "landing", v["landing"], a["landing"])

    # R1.5
    r15d = derive_r15(facts, r1d, r2d) if r1d["assignment"] else {}
    for pg in doc.get("pages", []):
        pid = pg.get("page_id")
        if pid not in r15d:
            continue
        a = pg.get("r1_5")
        if not a:
            note("R1.5", pid, "missing", r15d[pid], None)
            continue
        if not near(a.get("entry_x", 1e9), r15d[pid]["entry_x"]):
            note("R1.5", pid, "entry_x", r15d[pid]["entry_x"], a.get("entry_x"))
        if not near(a.get("lane_entry_y", 1e9), r15d[pid]["lane_entry_y"]):
            note("R1.5", pid, "lane_entry_y", r15d[pid]["lane_entry_y"], a.get("lane_entry_y"))

    # nodes
    nodes_d = derive_nodes(facts, r1d, r2d, r3d, doc.get("verdict"))
    for pg in doc.get("pages", []):
        pid = pg.get("page_id")
        if pid not in nodes_d:
            continue
        mine = nodes_d[pid]
        theirs = pg.get("nodes") or {}
        if set(mine.keys()) != set(theirs.keys()):
            note("nodes", pid, "keys", sorted(mine.keys()), sorted(theirs.keys()))
            continue
        for pol in mine:
            if len(mine[pol]) != len(theirs[pol]):
                note("nodes", pid, pol + ".len", len(mine[pol]), len(theirs[pol]))
                continue
            for i, (mn, th) in enumerate(zip(mine[pol], theirs[pol])):
                if not (near(mn[0], th[0]) and near(mn[1], th[1]) and mn[2] == th[2]):
                    note("nodes", pid, f"{pol}[{i}]", mn, th)

    # REFCLK
    rfcd = derive_refclk(manifest, w0r)
    rfca = doc.get("layers", {}).get("REFCLK", {}).get("assignment", {}) or {}
    for pid, v in rfcd.items():
        a = rfca.get(pid)
        if a is None:
            note("REFCLK", pid, "missing", v["path"], None)
            continue
        ap = a.get("path") or []
        if len(ap) != len(v["path"]):
            note("REFCLK", pid, "path.len", len(v["path"]), len(ap))
            continue
        for i, (mn, th) in enumerate(zip(v["path"], ap)):
            if not (near(mn[0], th[0]) and near(mn[1], th[1])):
                note("REFCLK", pid, f"path[{i}]", mn, th)
    return mism, {"mismatch_count": len(mism), "derived_r1": len(r1d["assignment"]),
                  "derived_r3": len(r3d), "derived_r2": len(r2d),
                  "derived_r15": len(r15d)}




# =============================================================================
# method gates
# =============================================================================
def gate_gm1(engine):
    hits, attrs = gm1_token_scan(engine)
    lines = "\n".join(f"  line {h['line']}: NAME '{h['token']}'" for h in hits) or "  (none)"
    ok = not hits and not attrs
    return {"ok": ok, "forbidden_name_hits": hits, "forbidden_attr_hits": attrs,
            "scan_output": lines}, ok


def gate_gm2(engine):
    r = gm2_ast_scan(engine)
    rule_fns = ["r1_place", "r2_lanes", "r3_place", "refclk_place"]
    over = {n: r["branch_sites"][n] for n in rule_fns if n in r["branch_sites"]
            and r["branch_sites"][n]["branch_sites"] > 2}
    ok = (not r["self_direct"] and not r["recursion_cycles"] and not r["whiles"]
          and not r["bad_imports"] and not over)
    r["rule_functions"] = {n: r["branch_sites"].get(n) for n in rule_fns}
    r["rule_functions_over_2"] = over
    r["ok"] = ok
    return r, ok


def gate_gm3(engine, doc):
    runs = {}
    for K in (1, 2, 4):
        times, wus = [], []
        for rep in range(3):
            out = Path(f"/tmp/w3cn_scale_{K}_{rep}.json")
            if out.exists():
                out.unlink()
            try:
                r = run_engine(["--scale", str(K), "--enum-order", "natural"], out)
            except subprocess.TimeoutExpired:
                times.append(1e9)
                continue
            times.append(r["seconds"])
            wu = parse_work_units(r["stdout"])
            if wu is None and out.exists():
                try:
                    wu = int(load_json_retry(out)["method"]["work_units"]["total"])
                except Exception:
                    wu = None
            wus.append(wu)
        wu = next((w for w in reversed(wus) if w is not None), None)
        runs[K] = {"median_s": statistics.median(times) if times else None,
                   "times_s": [round(t, 6) for t in times], "work_units": wu}
    w1, w2, w4 = runs[1]["work_units"], runs[2]["work_units"], runs[4]["work_units"]
    linear_ok = (None not in (w1, w2, w4)) and (w2 - w1 == w1) and (w4 == 3 * w2 - 2 * w1)
    # declared formula evaluated at scaled n
    declared = doc.get("method", {}).get("work_units", {}) or {}
    formula = declared.get("formula") or ""
    declared_vals = {}
    formula_ok = True
    try:
        for K in (1, 2, 4):
            env = {"n_pages": 32 * K, "n_landing": 72 * K, "n_refclk": 2 * K, "n_frames": 6 * K}
            declared_vals[K] = eval(formula, {"__builtins__": {}}, env)
            if declared_vals[K] != runs[K]["work_units"]:
                formula_ok = False
    except Exception as e:
        formula_ok = False
        declared_vals = {"error": str(e)}
    t1 = runs[1]["median_s"]
    time_ratios = {}
    time_ok = True
    for K in (2, 4):
        ratio = (runs[K]["median_s"] / t1) if (t1 and runs[K]["median_s"] is not None) else None
        time_ratios[K] = None if ratio is None else round(ratio, 3)
        if ratio is None or ratio > 2 * K:
            time_ok = False
    src_uses_scale = "args.scale" in ENGINE.read_text(encoding="utf-8")
    ok = bool(linear_ok and formula_ok and time_ok and src_uses_scale)
    return {"ok": ok, "runs": runs, "w1": w1, "w2": w2, "w4": w4,
            "work_units_ratio_2": None if not w1 else (w2 / w1 if w2 is not None else None),
            "work_units_ratio_4": None if not w1 else (w4 / w1 if w4 is not None else None),
            "linear_a_n_b_ok": linear_ok, "declared_formula": formula,
            "declared_formula_values": declared_vals, "declared_formula_ok": formula_ok,
            "time_ratio_2": time_ratios.get(2), "time_ratio_4": time_ratios.get(4),
            "time_ratio_ok": time_ok, "engine_source_uses_args_scale": src_uses_scale}, ok


def gate_gm6(doc, engine):
    def walk(o, path=""):
        hits = []
        if isinstance(o, dict):
            for k, v in o.items():
                if k in FORBIDDEN_ARTIFACT_KEYS:
                    hits.append(path + "/" + k)
                hits += walk(v, path + "/" + k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                hits += walk(v, path + f"[{i}]")
        return hits
    key_hits = walk(doc)
    src = engine.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
        fn_names = [n.name for n in ast.walk(tree)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    except Exception:
        fn_names = []
    fn_hits = [n for n in fn_names if n in FORBIDDEN_ARTIFACT_KEYS or n in FORBIDDEN_NAMES]
    grep_cmd = (f"grep -nE 'alternatives|options|tried|branch|attempts|node' "
                f"{engine.name}")
    g = subprocess.run(["grep", "-nE", "alternatives|options|tried|branch|attempts|node",
                        str(engine)], capture_output=True, text=True)
    ok = not key_hits and not fn_hits
    return {"ok": ok, "artifact_key_hits": key_hits, "engine_function_hits": fn_hits,
            "engine_function_names": fn_names,
            "grep_cmd": grep_cmd,
            "grep_output": g.stdout.strip().splitlines()}, ok


def probe_order_invariance(engine):
    shas = {}
    detail = {}
    for order in ("natural", "reverse", "hash"):
        out = Path(f"/tmp/w3cn_order_{order}.json")
        if out.exists():
            out.unlink()
        r = run_engine(["--enum-order", order, "--quiet"], out)
        shas[order] = sha256_file(out) if out.exists() else None
        detail[order] = {"rc": r["rc"], "seconds": round(r["seconds"], 3),
                         "sha256": shas[order]}
    uniq = set(v for v in shas.values() if v)
    ok = len(uniq) == 1 and all(shas.values())
    return {"ok": ok, "shas": shas, "detail": detail,
            "byte_identical": ok}, ok


# =============================================================================
# main
# =============================================================================
def main():
    t_start = time.perf_counter()
    checks = []
    gates = {}
    probes = []
    notes = []

    if not ENGINE.exists() or not ART_MAIN.exists():
        missing = []
        if not ENGINE.exists():
            missing.append(str(ENGINE))
        if not ART_MAIN.exists():
            missing.append(str(ART_MAIN))
        result = {
            "artifact": str(ART_MAIN), "schema": 1, "revision": REV, "verdict": "FAIL",
            "frozen_sha_check": {"drift": ["ARTIFACT_MISSING"]},
            "checks": [], "method_gates": {},
            "adversarial_probes": [{"key": "artifact_missing",
                                    "probe": "engine/artifact existence",
                                    "result": "MISSING: " + ", ".join(missing), "ok": False}],
            "producer_sha256": sha256_file(ENGINE) if ENGINE.exists() else None,
            "validator_sha256": sha256_file(__file__),
            "notes": ["artifact missing -> FAIL"],
        }
        _write(result)
        print("FAIL artifact missing:", ", ".join(missing))
        return 1

    engine_sha = sha256_file(ENGINE)
    doc = load_json_retry(ART_MAIN)
    manifest = load_json(FILES["manifest"])
    lane_frame = load_json(FILES["lane_frame"])
    gaps = load_json(FILES["r3_gaps"])
    w0r = load_json(FILES["w0r_model"])
    verdict = load_json(FILES["verdict"])

    # ---- frozen sha check
    actual = {k: (sha256_file(v) if v.exists() else None) for k, v in FILES.items()}
    drift = [k for k in EXPECTED_SHA if actual.get(k) != EXPECTED_SHA[k]]
    frozen = {"expected": EXPECTED_SHA, "actual": actual, "drift": drift,
              "match": not drift}
    checks.append(chk("FROZEN.sha", "all frozen inputs match pinned sha256",
                      "0 drift", f"drift={drift}", not drift))

    # ---- G-M1 / G-M2 / G-M6 (static)
    gm1, gm1_ok = gate_gm1(ENGINE)
    gates["G-M1"] = gm1
    gm2, gm2_ok = gate_gm2(ENGINE)
    gates["G-M2"] = gm2
    gm6, gm6_ok = gate_gm6(doc, ENGINE)
    gates["G-M6"] = gm6

    # ---- G-M3 (black box scaling)
    gm3, gm3_ok = gate_gm3(ENGINE, doc)
    gates["G-M3"] = gm3

    # ---- G-M4 (independent re-derivation)
    t0 = time.perf_counter()
    mism, m4meta = check_gm4(doc, manifest, lane_frame, gaps, w0r, verdict)
    m4_secs = time.perf_counter() - t0
    first = mism[0] if mism else None
    gates["G-M4"] = {"ok": not mism, "mismatch_count": len(mism),
                     "first_mismatch": first, "meta": m4meta, "seconds": round(m4_secs, 3)}

    # ---- G-M5 (invariants + certificates)
    a1, a1meta = check_acn1(doc, verdict, manifest)
    a2, a2meta = check_acn2(doc, manifest, lane_frame)
    a3, a3meta = check_acn3(doc, gaps)
    a4, a4meta = check_acn4(doc, manifest)
    a5, a5meta = check_acn5(doc, w0r)
    cdis, cmeta = check_certificates(doc)
    a7, a7meta = check_acn7(doc, ART_MAIN)
    checks += a1 + a2 + a3 + a4 + a5 + cdis + a7
    gm5_ok = all(c["ok"] for c in (a1 + a2 + a3 + a4 + a5 + cdis)) and a7[0]["ok"]
    gates["G-M5"] = {"ok": gm5_ok, "acn1": a1meta, "acn2": a2meta, "acn3": a3meta,
                     "acn4": a4meta, "acn5": a5meta, "certificates": cmeta, "acn7": a7meta,
                     "r1_5_crossings_independent": a4meta["n_crossings"]}

    # ---- A-CN.6 order invariance (black box)
    gm_oi, oi_ok = probe_order_invariance(ENGINE)
    gates["A-CN.6"] = gm_oi

    # ---- adversarial probes
    # stale_state
    art_inputs = doc.get("inputs_sha", {}) or {}
    stale = []
    for k, sh in art_inputs.items():
        p = FILES.get(k)
        cur = sha256_file(p) if (p and p.exists()) else None
        if cur != sh:
            stale.append({"key": k, "artifact": sh, "current": cur})
    git_head = subprocess.run(["git", "-C", str(K2), "rev-parse", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
    git_status = subprocess.run(["git", "-C", str(K2), "status", "--short"],
                                capture_output=True, text=True).stdout.strip().splitlines()
    probes.append({"key": "stale_state",
                   "probe": "artifact inputs_sha vs CURRENT on-disk frozen inputs; git status/HEAD recorded as-is",
                   "result": {"stale_count": len(stale), "stale": stale,
                              "head": git_head, "git_status": git_status},
                   "ok": not stale})

    # dirty_worktree (informational, not part of verdict)
    untracked = [l for l in git_status if l.startswith("??")]
    probes.append({"key": "dirty_worktree",
                   "probe": "pre-existing untracked artifacts (_shared gitlink deviation, *.bak_v32*, model_solves/*) recorded, NOT part of verdict",
                   "result": {"untracked_count": len(untracked), "untracked": untracked},
                   "ok": True})

    # misleading_success_output: mutate a temp copy and prove detection
    import copy as _copy
    tampered = _copy.deepcopy(doc)
    mutated = None
    r1a = tampered.get("layers", {}).get("R1", {}).get("assignment", {})
    for pid in sorted(r1a):
        r1a[pid]["P_via"][0] = round(r1a[pid]["P_via"][0] + 0.4, 6)
        mutated = pid
        break
    tmp_art = Path("/tmp/w3cn_tampered_via.json")
    tmp_art.write_text(json.dumps(tampered), encoding="utf-8")
    t1, t1m = check_acn1(tampered, verdict, manifest)
    detected = any(not c["ok"] for c in t1)
    probes.append({"key": "misleading_success_output",
                   "probe": f"temp copy with {mutated}.P_via shifted +0.4mm -> validator must return FAIL",
                   "result": {"temp_path": str(tmp_art),
                              "detected": detected,
                              "failed_checks": [c["id"] for c in t1 if not c["ok"]]},
                   "ok": detected})

    # hung_or_long_commands
    per_check_seconds = {"gm2_ast": None, "gm3_scaling": runs_total(gm3) if False else None}
    long_cmds = []
    for K, v in gm3.get("runs", {}).items():
        if v["median_s"] is not None and v["median_s"] > 60:
            long_cmds.append(f"gm3 scale={K} median={v['median_s']:.1f}s")
    for order, v in gm_oi.get("detail", {}).items():
        if v.get("seconds", 0) > 60:
            long_cmds.append(f"order={order} {v['seconds']}s")
    probes.append({"key": "hung_or_long_commands",
                   "probe": "per-command runtime; flag any > 60s",
                   "result": {"long_commands": long_cmds,
                              "gm3_medians_s": {str(K): v["median_s"] for K, v in gm3.get("runs", {}).items()},
                              "order_invariance_s": {k: v["seconds"] for k, v in gm_oi.get("detail", {}).items()},
                              "gm4_seconds": round(m4_secs, 3)},
                   "ok": not long_cmds})

    # ---- aggregate
    all_checks_ok = all(c["ok"] for c in checks)
    all_gates_ok = all(g.get("ok") for g in gates.values())
    all_probes_ok = all(p["ok"] for p in probes)
    verdict_str = "PASS" if (all_checks_ok and all_gates_ok and all_probes_ok) else "FAIL"

    notes.append(f"artifact verdict field = {doc.get('verdict')}; gate_status.failed = "
                 f"{doc.get('gate_status', {}).get('failed')}")
    notes.append("G-M4 re-derivation implements CARD v1.2 R-4 text; where the card is "
                 "silent (R1 seed/tie-break, y-grid selection) the interpretation is "
                 "documented in derive_r1() and is compared byte-exactly.")
    if not gm3.get("engine_source_uses_args_scale"):
        notes.append("ENGINE does not reference args.scale -> --scale is accepted but not "
                     "used; G-M3 scaling probe therefore cannot scale work_units.")
    if mism:
        notes.append(f"G-M4 first mismatch: {json.dumps(first, ensure_ascii=False)[:400]}")

    result = {
        "artifact": {"path": str(ART_MAIN.relative_to(K2)), "sha256": sha256_file(ART_MAIN),
                     "verdict_field": doc.get("verdict"), "revision_field": doc.get("revision")},
        "schema": 1,
        "revision": REV,
        "verdict": verdict_str,
        "frozen_sha_check": frozen,
        "checks": checks,
        "method_gates": gates,
        "adversarial_probes": probes,
        "producer_sha256": engine_sha,
        "validator_sha256": sha256_file(__file__),
        "notes": notes,
        "total_seconds": round(time.perf_counter() - t_start, 3),
    }
    _write(result)

    # console report
    print("=" * 100)
    print(f"W3 constructive validator {REV}  engine_sha={engine_sha[:16]}  artifact_sha={sha256_file(ART_MAIN)[:16]}")
    print("=" * 100)
    print(f"{'ID':<26}{'OK':<6}{'EXPECTED':<28}OBSERVED")
    for c in checks:
        print(f"{c['id']:<26}{str(c['ok']):<6}{str(c['expected'])[:26]:<28}{str(c['observed'])[:90]}")
    print("-" * 100)
    for name, g in gates.items():
        print(f"GATE {name:<8} ok={g.get('ok')}")
    for p in probes:
        print(f"PROBE {p['key']:<28} ok={p['ok']}")
    print("-" * 100)
    print(f"VERDICT = {verdict_str}  (checks_ok={all_checks_ok} gates_ok={all_gates_ok} probes_ok={all_probes_ok})")
    print("=" * 100)
    return 0 if verdict_str == "PASS" else 1


def runs_total(gm3):
    return None


def _write(result):
    out = STEP2 / "m13_v57_w3_validation.json"
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False, sort_keys=True),
                   encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
