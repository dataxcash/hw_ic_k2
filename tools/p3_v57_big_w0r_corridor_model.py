#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────────────────────
# [批2·S4 血缘标注 · ARCHER 2026-09-20 · 零行为改动]
# 类别    : HIST(历史分析/复现脚本)
# 作者期板: k2/k2_v4.kicad_pcb（2026-09-16 起为 → hw/k2_v4_8L.kicad_pcb 的符号链接；sha16 fb07d25ac426ff84）
# 别名风险: 无旧板身份字面量；重跑前须自核板身份（解析后 sha 随板文件而变）
# 判定    : 仅标注，零行为改动（#K2-41 §三-⑤）
# ────────────────────────────────────────────────────────────────────────────
"""W0-R — K2 corridor resource model, derived only from frozen upstream inputs.

Revision W0R-FIX.1 closes the architect gaps W0R-G1/G2/G3 recorded in
EDA_AUTONOMOUS_EXECUTION_PLAN_v2.md §1:

  G1: refclk_resource_domain upgraded from resource_kind "candidate_only" to a
      quantitative conservation certificate per page and per corridor
      (required / available / shortage / conflicting_resources / minimal_core),
      plus a chip-zone passage existence witness (constructability guarantee
      per the feasibility iron law — an existence proof, NOT a route).
  G2: verdict re-issued as a terminal status: exactly "B1.5 PASS" or
      "B1.5 INFEASIBLE_CERT" (no third state), with the v1 §3 evidence
      protocol fields present.
  G3: blocked_component_projections is backed by a full projection enumeration
      evidence block: predicate, source hash, every component checked (42
      footprints incl. 5 geometry-less pin headers listed individually), and
      the empty-result justification.

This remains deliberately not a router and does not inspect board copper
(tracks/vias/zones stay declared non-inputs).  Accepted W0-R parts (input
envelope, footprint body proxy, span subtraction, data band capacity) are
unchanged.  All new geometry arithmetic uses integer half-micron units
(1 mm = 2000 hm) so generator and independent validator agree byte-exactly.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

K2 = Path(__file__).resolve().parents[1]
L3 = K2 / "pm_gate/artifacts/k2_v4/L3"
STEP = L3 / "mcio_feas_step2"
SPEC = L3 / "SPEC_k2_v4.json"
BOARD = K2 / "k2_v4.kicad_pcb"
MANIFEST = STEP / "m13_v57_s1_page_manifest.json"
RULES = K2 / "_shared/eda_core/drc_rules.json"
INPUT = STEP / "m13_v57_big_w0r_inputs.json"
OUT = STEP / "m13_v57_big_w0r_corridor_model.json"

GENERATOR = Path(__file__).resolve()
VALIDATOR_TOOL = Path(__file__).resolve().with_name("p3_v57_big_w0r_validator.py")
REV = "W0R-FIX.1"

# Frozen input parameters pending a future L2 placement/geometric ruling.  They
# are listed here (and emitted in INPUT) rather than obtained from SPEC.corridors.
CORRIDORS = {
    "EAST_CHIP_TO_J2": [105.25, 132.65],
    "WEST_MCIO_TO_CHIP": [65.05, 82.35],
}
EDGE_CLEARANCE = 0.30
PITCH = 1.46                         # frozen differential pair centre pitch
BODY_CLEARANCE = 0.175               # copper clearance around non-endpoint body
REFCLK_LAYER = "F.Cu"                # separate from data layer, resource only
DATA_LAYER = "In2.Cu"

# Frozen W0-R endpoint semantics (accepted as shipped, v2 §1): corridor
# longitudinal endpoints are not body blockers inside their own corridor.
ENDPOINT_EXCLUSIONS = ("J2", "J3", "J4", "U6")
# Which manifest anchor side bounds which corridor (frozen corridor topology:
# the EAST corridor's connector face is J2 = manifest key "conn2"; the WEST
# corridor's connector faces are J3/J4 = manifest key "conn").
CORRIDOR_ANCHOR_SIDE = {"EAST_CHIP_TO_J2": "conn2", "WEST_MCIO_TO_CHIP": "conn"}


def hm(v: float) -> int:
    """mm -> integer half-microns (1 mm = 2000 hm).  Exact, byte-deterministic."""
    return int(round(v * 2000))


def mm(h: int) -> float:
    """half-microns -> mm rounded to 3 decimals (single emission convention)."""
    return round(h / 2000.0, 3)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def block(text: str, start: int) -> str:
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "(": depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0: return text[start:i + 1]
    raise ValueError("unclosed KiCad s-expression")


def transform(x: float, y: float, at: tuple[float, float, float]) -> tuple[float, float]:
    # KiCad rotation direction is clockwise in the stored board coordinate system.
    a = math.radians(-at[2])
    return (at[0] + x * math.cos(a) - y * math.sin(a),
            at[1] + x * math.sin(a) + y * math.cos(a))


def footprint_boxes() -> list[dict]:
    """Placement/body boxes from footprints only; never reads tracks, vias or zones.

    ACCEPTED W0-R code — unchanged (span derivation authority for data bands).
    """
    text = BOARD.read_text(encoding="utf-8")
    ans = []
    for m in re.finditer(r"\(footprint ", text):
        b = block(text, m.start())
        prop = dict(re.findall(r'\(property "([^"]+)" "([^"]*)"', b))
        ref = prop.get("Reference", "?")
        at_m = re.search(r"\(at ([\-\d.]+) ([\-\d.]+)(?: ([\-\d.]+))?\)", b)
        if not at_m: continue
        at = tuple(float(x or 0) for x in at_m.groups())
        pts = []
        # Fab/courtyard lines are the body proxy. Pads ensure pad-only footprints
        # still get a physical projection.
        for lm in re.finditer(r"\(fp_(?:line|rect|poly)\b", b):
            gb = block(b, lm.start())
            for xy in re.finditer(r"\((?:start|end|xy) ([\-\d.]+) ([\-\d.]+)\)", gb):
                pts.append(transform(float(xy.group(1)), float(xy.group(2)), at))
        for pm in re.finditer(r"\(pad ", b):
            pb = block(b, pm.start())
            am = re.search(r"\(at ([\-\d.]+) ([\-\d.]+)", pb)
            sm = re.search(r"\(size ([\-\d.]+) ([\-\d.]+)\)", pb)
            if am and sm:
                x, y = float(am.group(1)), float(am.group(2))
                sx, sy = float(sm.group(1))/2, float(sm.group(2))/2
                for dx, dy in ((-sx,-sy), (-sx,sy), (sx,-sy), (sx,sy)):
                    pts.append(transform(x + dx, y + dy, at))
        if pts:
            xs, ys = zip(*pts)
            ans.append({"ref": ref, "bbox": [round(min(xs),3), round(min(ys),3),
                                                round(max(xs),3), round(max(ys),3)]})
    return sorted(ans, key=lambda x: x["ref"])


def footprint_census() -> tuple[list[dict], dict]:
    """FULL enumeration of every footprint in the frozen placement source (W0R-G3).

    Returns (census sorted by ref, primitive_scan).  Census entries carry the
    same body-proxy bbox as footprint_boxes() plus pad-only extent, library and
    at-position; geometry-less footprints are kept (bbox None), never dropped.
    """
    text = BOARD.read_text(encoding="utf-8")
    census = []
    circle_arc_count = 0
    for m in re.finditer(r"\(footprint ", text):
        b = block(text, m.start())
        prop = dict(re.findall(r'\(property "([^"]+)" "([^"]*)"', b))
        ref = prop.get("Reference", "?")
        lib_m = re.search(r'\(footprint "([^"]*)"', b)
        at_m = re.search(r"\(at ([\-\d.]+) ([\-\d.]+)(?: ([\-\d.]+))?\)", b)
        at = [float(x or 0) for x in at_m.groups()] if at_m else None
        circle_arc_count += len(re.findall(r"\(fp_(?:circle|arc)\b", b))
        pts, padpts = [], []
        at_t = tuple(at) if at else (0.0, 0.0, 0.0)
        for lm in re.finditer(r"\(fp_(?:line|rect|poly)\b", b):
            gb = block(b, lm.start())
            for xy in re.finditer(r"\((?:start|end|xy) ([\-\d.]+) ([\-\d.]+)\)", gb):
                pts.append(transform(float(xy.group(1)), float(xy.group(2)), at_t))
        for pm in re.finditer(r"\(pad ", b):
            pb = block(b, pm.start())
            am = re.search(r"\(at ([\-\d.]+) ([\-\d.]+)", pb)
            sm = re.search(r"\(size ([\-\d.]+) ([\-\d.]+)\)", pb)
            if am and sm:
                x, y = float(am.group(1)), float(am.group(2))
                sx, sy = float(sm.group(1))/2, float(sm.group(2))/2
                for dx, dy in ((-sx,-sy), (-sx,sy), (sx,-sy), (sx,sy)):
                    p = transform(x + dx, y + dy, at_t)
                    pts.append(p); padpts.append(p)
        bbox = padbox = None
        if pts:
            xs, ys = zip(*pts)
            bbox = [round(min(xs),3), round(min(ys),3), round(max(xs),3), round(max(ys),3)]
        if padpts:
            xs, ys = zip(*padpts)
            padbox = [round(min(xs),3), round(min(ys),3), round(max(xs),3), round(max(ys),3)]
        census.append({"ref": ref, "library": lib_m.group(1) if lib_m else "?",
                       "at": at, "bbox": bbox, "pad_bbox": padbox})
    census.sort(key=lambda e: e["ref"])
    return census, {"fp_circle_or_arc_primitives_in_source": circle_arc_count}


def subtract(span: list[float], blocked: list[list[float]]) -> list[list[float]]:
    """ACCEPTED W0-R code — unchanged."""
    out = [span]
    for lo, hi in sorted(blocked):
        nxt = []
        for a, b in out:
            if hi <= a or lo >= b: nxt.append([a, b])
            else:
                if a < lo: nxt.append([a, min(lo, b)])
                if hi < b: nxt.append([max(hi, a), b])
        out = nxt
    return [[round(a,3), round(b,3)] for a,b in out if b-a > 1e-9]


def isubtract(span: tuple[int,int], blocked: list[tuple[int,int]]) -> list[tuple[int,int]]:
    """Integer (half-micron) interval subtraction — same semantics as subtract()."""
    out = [span]
    for lo, hi in sorted(blocked):
        nxt = []
        for a, b in out:
            if hi <= a or lo >= b: nxt.append((a, b))
            else:
                if a < lo: nxt.append((a, min(lo, b)))
                if hi < b: nxt.append((max(hi, a), b))
        out = nxt
    return [(a, b) for a, b in out if b - a > 0]


def capacity(spans: list[list[float]], n: int) -> dict:
    """ACCEPTED W0-R code — unchanged."""
    # A band may occupy exactly n pitch-spaced centres; no silent span stitching.
    need = (n - 1) * PITCH
    usable = [s for s in spans if s[1] - s[0] + 1e-9 >= need]
    return {"n_pairs": n, "centre_span_needed_mm": round(need,3),
            "candidate_spans": usable, "feasible": bool(usable)}


def rule_metrics(rules: dict) -> dict:
    """Derive REFCLK row metrics from the declared rules authority (no magic numbers).

    Frozen PITCH must equal p_gap + 2*p_width + inter_pair_spacing; any drift is
    a hard stop (conflict => stop, never silently continue).
    """
    dp = rules["diff_pair"]
    pg, pw, ip = hm(dp["p_gap"]), hm(dp["p_width"]), hm(dp["inter_pair_spacing"])
    extent = pg + 2 * pw                 # pair copper extent across P/N
    pitch_derived = extent + ip          # centre-to-centre lane pitch
    if pitch_derived != hm(PITCH):
        raise SystemExit(f"RULE DRIFT: derived pitch {pitch_derived}hm != frozen {hm(PITCH)}hm")
    cle = None
    for nc in rules["clearance"]["net_classes"]:
        if nc["name"] == "PCIe85":
            cle = hm(nc["clearance"])
    if cle != hm(BODY_CLEARANCE):
        raise SystemExit(f"RULE DRIFT: PCIe85 clearance {cle}hm != frozen body clearance {hm(BODY_CLEARANCE)}hm")
    return {"p_gap_hm": pg, "p_width_hm": pw, "inter_pair_hm": ip,
            "pair_extent_hm": extent, "pitch_hm": pitch_derived, "clearance_hm": cle}


def j2_face_facts() -> dict:
    """J2 connector-face quantitative facts (frozen footprint geometry only)."""
    text = BOARD.read_text(encoding="utf-8")
    pads = []
    j2_pad_bbox = None
    for m in re.finditer(r"\(footprint ", text):
        b = block(text, m.start())
        prop = dict(re.findall(r'\(property "([^"]+)" "([^"]*)"', b))
        if prop.get("Reference") != "J2": continue
        at_m = re.search(r"\(at ([\-\d.]+) ([\-\d.]+)(?: ([\-\d.]+))?\)", b)
        at = tuple(float(x or 0) for x in at_m.groups())
        pts = []
        for pm in re.finditer(r"\(pad ", b):
            pb = block(b, pm.start())
            num = re.search(r'\(pad "([^"]*)"', pb)
            am = re.search(r"\(at ([\-\d.]+) ([\-\d.]+)", pb)
            sm = re.search(r"\(size ([\-\d.]+) ([\-\d.]+)\)", pb)
            if am and sm:
                gx, gy = transform(float(am.group(1)), float(am.group(2)), at)
                w, h = float(sm.group(1)), float(sm.group(2))
                pads.append({"num": num.group(1) if num else "?", "x": gx, "y": gy, "w": w, "h": h})
                pts += [(gx - w/2, gy - h/2), (gx + w/2, gy + h/2)]
        if pts:
            xs, ys = zip(*pts)
            j2_pad_bbox = [round(min(xs),3), round(min(ys),3), round(max(xs),3), round(max(ys),3)]
    west = sorted([p for p in pads if hm(p["x"]) < hm(133.5)], key=lambda p: (hm(p["y"]), p["num"]))
    east = sorted([p for p in pads if hm(p["x"]) >= hm(133.5)], key=lambda p: (hm(p["y"]), p["num"]))
    ys = [hm(p["y"]) for p in west]
    pitch_face = min(b - a for a, b in zip(ys, ys[1:])) if len(ys) > 1 else None
    pad_w, pad_h = hm(west[0]["w"]), hm(west[0]["h"])
    west_xhi = max(hm(p["x"]) + pad_w // 2 for p in west)
    east_xlo = min(hm(p["x"]) - pad_w // 2 for p in east)
    return {"west": west, "east": east, "face_row_pitch_hm": pitch_face,
            "pad_w_hm": pad_w, "pad_h_hm": pad_h,
            "pad_field_y": [hm(j2_pad_bbox[1]), hm(j2_pad_bbox[3])],
            "pad_field_x": [hm(j2_pad_bbox[0]), hm(j2_pad_bbox[2])],
            "inter_column_gap_x": [west_xhi, east_xlo]}


def build_projection_evidence(cid: str, xr: list[float], census: list[dict],
                              prim_scan: dict, board_sha: str, intruders: list[dict]) -> dict:
    """W0R-G3: prove blocked_component_projections is a real enumeration result."""
    checked, overlaps = [], []
    for e in census:
        if e["bbox"] is None:
            ax = e["at"][0] if e["at"] else None
            dist = round(max(xr[0] - ax, ax - xr[1], 0.0), 3) if ax is not None else None
            checked.append({"ref": e["ref"], "library": e["library"], "at": e["at"],
                            "geometry": "none", "x_overlaps_corridor": False,
                            "endpoint_excluded": False, "intruder": False,
                            "disposition": ("no projectable primitive (no fp_line/rect/poly, no pad) in frozen source;"
                                            f" at-position recorded; x-distance to corridor range = {dist} mm;"
                                            " cannot x-overlap under any body extent observed on this board")})
            continue
        x0, y0b, x1, y1b = e["bbox"]
        ov = x0 < xr[1] and x1 > xr[0]
        excl = ov and e["ref"] in ENDPOINT_EXCLUSIONS
        intr = ov and not excl
        checked.append({"ref": e["ref"], "library": e["library"], "at": e["at"],
                        "geometry": "present", "bbox": e["bbox"],
                        "x_overlaps_corridor": ov, "endpoint_excluded": excl, "intruder": intr})
        if ov:
            slab = [round(max(x0, xr[0]), 3), round(min(x1, xr[1]), 3)]
            pb = e["pad_bbox"]
            pad_free = pb is None or slab[1] <= pb[0] or slab[0] >= pb[2]
            overlaps.append({"ref": e["ref"], "bbox": e["bbox"], "slab_x": slab,
                             "overhang_mm": round(slab[1] - slab[0], 3),
                             "endpoint_excluded": excl,
                             "pad_extent_x": [pb[0], pb[2]] if pb else None,
                             "slab_pad_free": pad_free,
                             "kind": "courtyard_only_pad_free" if pad_free else "pad_field"})
    n_total = len(census)
    n_geom = sum(1 for e in census if e["bbox"] is not None)
    n_nogeo = n_total - n_geom
    census_intruder_refs = sorted(c["ref"] for c in checked if c.get("intruder"))
    boxes_intruder_refs = sorted(i["ref"] for i in intruders)
    if not intruders:
        justification = (
            f"All {n_total} footprints of the frozen placement source were enumerated "
            f"({n_geom} with projectable geometry, {n_nogeo} geometry-less listed individually with at-positions). "
            f"Strict x-overlap set = {[o['ref'] + '@' + str(o['slab_x']) for o in overlaps]}. "
            f"Every x-overlapping footprint is a corridor endpoint under the frozen exclusion set "
            f"{list(ENDPOINT_EXCLUSIONS)}; non-endpoint overlaps = 0. Therefore "
            "blocked_component_projections == [] is the genuine result of enumeration + subtraction, "
            "not an empty default.")
    else:
        justification = (f"enumeration found {len(intruders)} non-endpoint intruder(s): "
                         f"{boxes_intruder_refs}; projections are emitted in blocked_component_projections")
    return {
        "claim": "blocked_component_projections is a real enumeration result, not an empty default (W0R-G3)",
        "predicate": {
            "intruder_iff": "STRICT x-overlap (bbox_x0 < corridor_x1 AND bbox_x1 > corridor_x0) AND ref NOT IN endpoint_exclusions; intruder y-projection inflated by body_clearance_mm",
            "endpoint_exclusions": list(ENDPOINT_EXCLUSIONS),
            "endpoint_exclusion_rationale": ("corridor longitudinal endpoints: lane rows terminate on their pads;"
                                             " boundary pad fields / courtyard overhangs are quantified under"
                                             " refclk_resource_domain.conflicting_resources and inherited by"
                                             " W2 connector columns + R3/R4 landing rows"),
            "bbox_construction": "footprint fp_line/fp_rect/fp_poly vertices + pad rectangles transformed by (at x y rot), KiCad clockwise rotation; body proxy = graphics+pads union (accepted W0-R semantics)",
            "primitive_coverage": prim_scan,
            "y_inflation_mm": BODY_CLEARANCE,
            "y_inflation_application": "applied to actual intruders only (none in either corridor); endpoint slabs are recorded un-inflated here and keepout-inflated inside refclk_passage_witness",
        },
        "source": {"file": str(BOARD.relative_to(K2)), "sha256": board_sha,
                   "note": "identical fingerprint to inputs_sha256.board"},
        "enumeration": {"footprints_total": n_total, "with_geometry": n_geom,
                        "without_geometry": [{"ref": e["ref"], "library": e["library"], "at": e["at"]}
                                             for e in census if e["bbox"] is None],
                        "checked": checked},
        "endpoint_overlaps": overlaps,
        "result": {"intruder_count": len(intruders),
                   "census_agrees_with_subtraction_input": census_intruder_refs == boxes_intruder_refs,
                   "empty_justification": justification if not intruders else None,
                   "non_empty_detail": intruders if intruders else None},
    }


def build_passage_witness(census: list[dict], result: dict, inner_hm: tuple[int,int],
                          met: dict) -> dict:
    """Chip-zone passage existence witness for every REFCLK page.

    The chip zone is the x-gap between the two corridors; U6 spans it fully, so
    every east-west REFCLK page must pass north or south of the U6 keepout.
    This is an existence proof over free y-windows (a constructability guarantee
    for the conservation verdict) — it emits no route and assigns nothing;
    construction and window selection belong to W3/R3-R4.
    """
    EXT = met["pair_extent_hm"]; EXT2 = EXT // 2; PITCH_HM = met["pitch_hm"]; CLE = met["clearance_hm"]
    cz = (hm(CORRIDORS["WEST_MCIO_TO_CHIP"][1]), hm(CORRIDORS["EAST_CHIP_TO_J2"][0]))  # (82.35, 105.25)

    blockers = []
    for e in census:
        if e["bbox"] is None: continue
        x0, y0, x1, y1 = e["bbox"]
        if x0 < mm(cz[1]) and x1 > mm(cz[0]):     # strict x-overlap with chip zone
            blockers.append({"ref": e["ref"], "bbox": e["bbox"],
                             "kx": (hm(x0) - CLE, hm(x1) + CLE),
                             "ky": (hm(y0) - CLE, hm(y1) + CLE)})
    blockers.sort(key=lambda b: b["ref"])

    edges = sorted({cz[0], cz[1]} | {v for b in blockers for v in b["kx"] if cz[0] < v < cz[1]})
    slices = []
    for a, b in zip(edges, edges[1:]):
        bl = [q for q in blockers if q["kx"][0] < b and q["kx"][1] > a]
        free = isubtract(inner_hm, [q["ky"] for q in bl])
        slices.append({"x_range": (a, b), "blockers": [q["ref"] for q in bl],
                       "channels": [w for w in free if w[1] - w[0] >= EXT],
                       "sealed_windows": [w for w in free if 0 < w[1] - w[0] < EXT]})

    # sealed / merged keepout pairs (documents WHY windows are unavailable)
    sealed_pairs = []
    for i in range(len(blockers)):
        for j in range(i + 1, len(blockers)):
            A, B = blockers[i], blockers[j]
            if not (A["kx"][0] < B["kx"][1] and B["kx"][0] < A["kx"][1]): continue
            lo, hi = sorted([A, B], key=lambda q: (q["ky"][0], q["ref"]))
            gap = hi["ky"][0] - lo["ky"][1]
            if gap < EXT:
                sealed_pairs.append({"pair": [lo["ref"], hi["ref"]], "gap_mm": mm(gap),
                                     "reason": "keepouts overlap (negative gap)" if gap < 0
                                               else "gap < pair_copper_extent"})
    sealed_pairs.sort(key=lambda s: (s["pair"][0], s["pair"][1]))

    # transition columns (copper half-extent + clearance respected against bounding keepouts)
    u6 = next(b for b in blockers if b["ref"] == "U6")
    cap_kx_lo = min((b["kx"][0] for b in blockers if b["ref"] != "U6"), default=None)
    j2_entry = next(e for e in census if e["ref"] == "J2")
    j2_kx0 = hm(j2_entry["pad_bbox"][0]) - CLE
    east_rise = (u6["kx"][1] + EXT2, j2_kx0 - EXT2)
    west_slice = slices[0]["x_range"]
    west_descent = (west_slice[0] + EXT2,
                    (cap_kx_lo - EXT2) if cap_kx_lo is not None else (west_slice[1] - EXT2))
    j34_kx0 = min(hm(e["bbox"][0]) - CLE for e in census
                  if e["ref"] in ("J3", "J4") and e["bbox"] is not None)
    j34_kx1 = max(hm(e["bbox"][2]) + CLE for e in census
                  if e["ref"] in ("J3", "J4") and e["bbox"] is not None)
    west_rise_in_corridor = (j34_kx1 + EXT2, u6["kx"][0] - EXT2)

    def free_y_in(xlo: int, xhi: int) -> list[tuple[int,int]]:
        bl = [q for q in blockers if q["kx"][0] < xhi and q["kx"][1] > xlo]
        return isubtract(inner_hm, [q["ky"] for q in bl])

    east_rise_free = free_y_in(east_rise[0] - EXT2, east_rise[1] + EXT2)
    west_descent_channels = slices[0]["channels"]
    west_rise_free = free_y_in(west_rise_in_corridor[0] - EXT2, west_rise_in_corridor[1] + EXT2)

    def chain_west(start: tuple[int,int]):
        """Running intersection of `start` through every slice, east->west."""
        run = start
        for sl in slices[-2::-1]:
            inter = [(max(run[0], c[0]), min(run[1], c[1])) for c in sl["channels"]]
            inter = [w for w in inter if w[1] - w[0] >= EXT]
            if not inter: return None
            run = sorted(inter, key=lambda w: (-(w[1] - w[0]), w[0]))[0]
        return run if run[1] - run[0] >= EXT else None

    # per-page resolution -----------------------------------------------------
    per_page = {}
    east_pages = {r["page_id"]: r for r in result["EAST_CHIP_TO_J2"]["_refclk_pages"]}
    west_pages = {r["page_id"]: r for r in result["WEST_MCIO_TO_CHIP"]["_refclk_pages"]}
    for pid in sorted(east_pages):
        ce = east_pages[pid]["_centre_hm"]; cw = west_pages[pid]["_centre_hm"]
        ecop = east_pages[pid]["_copper"]; wcop = west_pages[pid]["_copper"]
        others = [(east_pages[o]["_centre_hm"], west_pages[o]["_centre_hm"])
                  for o in sorted(east_pages) if o != pid]

        def contains(win, cop):
            return win[0] <= cop[0] and cop[1] <= win[1]

        # (1) direct: one window chain containing both coppers, no detour
        direct = None
        for c0 in sorted(c for c in slices[-1]["channels"] if contains(c, ecop)):
            run = chain_west(c0)
            if run is not None and contains(run, ecop) and contains(run, wcop):
                direct = run; break
        if direct is not None:
            per_page[pid] = {
                "status": "WITNESSED",
                "kind": "direct_channel",
                "channel_y": [mm(direct[0]), mm(direct[1])],
                "east_band_copper_y": [mm(ecop[0]), mm(ecop[1])],
                "west_band_copper_y": [mm(wcop[0]), mm(wcop[1])],
                "east_copper_contained": True, "west_copper_contained": True,
                "margins_mm": {"east_copper_to_channel": [mm(ecop[0] - direct[0]), mm(direct[1] - ecop[1])],
                               "west_copper_to_channel": [mm(wcop[0] - direct[0]), mm(direct[1] - wcop[1])]},
                "note": "both corridor band coppers lie inside one chip-zone free channel chain; no detour required",
            }
            continue

        # (2) detour candidates: enter via the east_rise column, chain west,
        #     exit onto the west band (directly or by descent inside the west slice)
        candidates = []
        for c0 in sorted(slices[-1]["channels"]):
            states = [(c0, [c0])]
            for sl in slices[-2::-1]:
                nxt = []
                for w, pth in states:
                    for c in sorted(sl["channels"]):
                        inter = (max(w[0], c[0]), min(w[1], c[1]))
                        if inter[1] - inter[0] >= EXT:
                            nxt.append((inter, pth + [inter]))
                seen = {}
                for w, pth in nxt:
                    if w not in seen: seen[w] = pth
                states = [(w, seen[w]) for w in sorted(seen)]
                if not states: break
            for w, pth in states:
                exit_mode = None
                if contains(w, wcop):
                    exit_mode = "direct_exit"
                else:
                    ch1 = [c for c in west_descent_channels if contains(c, w) and contains(c, wcop)]
                    if ch1 and west_descent[0] < west_descent[1]:
                        exit_mode = "descent_in_west_slice"
                if exit_mode:
                    dist = max(0, w[0] - wcop[1], wcop[0] - w[1])
                    bound = sorted({b["ref"] for b in blockers
                                    if (w[0] - EXT <= b["ky"][1] <= w[1] + EXT)
                                    or (w[0] - EXT <= b["ky"][0] <= w[1] + EXT)})
                    candidates.append({"window": w, "dist": dist, "exit_mode": exit_mode,
                                       "bounding_keepouts": bound, "chain": pth,
                                       "side": "north" if w[0] >= u6["ky"][1] else "south"})
        candidates.sort(key=lambda c: (c["dist"], c["window"][0]))

        # (3) coexistence alternative: chain not exit-reachable, shared with the other page
        alt = None
        for c0 in sorted(slices[-1]["channels"]):
            run = chain_west(c0)
            if run is None or contains(run, wcop): continue
            if any(contains(c, run) and contains(c, wcop) for c in west_descent_channels): continue
            lo, hi = run[0] + EXT2, run[1] - EXT2
            if hi < lo: continue
            forbid = []
            for oe, ow in others:
                forbid += [(oe - PITCH_HM, oe + PITCH_HM), (ow - PITCH_HM, ow + PITCH_HM)]
            allowed = isubtract((lo, hi), forbid)
            if not allowed: continue
            rise_span = (min(run[0], wcop[0]), max(run[1], wcop[1]))
            crosses = any(ow + PITCH_HM // 2 > rise_span[0] and ow - PITCH_HM // 2 < rise_span[1]
                          for oe, ow in others)
            alt = {
                "kind": "coexistence_channel_detour",
                "physical_channel_y": [mm(run[0]), mm(run[1])],
                "coexistence_feasible_centre_windows_y": [[mm(a), mm(b)] for a, b in allowed],
                "coexistence_rule": f"centre separation >= {PITCH} mm from every other REFCLK page band (both of its corridor centres)",
                "west_rise_in_corridor_x": [mm(west_rise_in_corridor[0]), mm(west_rise_in_corridor[1])],
                "west_rise_in_corridor_crossing": ("FORBIDDEN: rising inside the WEST corridor crosses the other page's west row band on the same layer"
                                                    if crosses else "clear"),
                "crossing_free_rise_x_le": mm(j34_kx0 - EXT2),
                "crossing_free_rise_note": ("crossing-free variant: stay in the channel west through the WEST corridor, rise"
                                             " west of the J3/J4 keepout x_lo minus copper half-extent, then J4 west-face"
                                             " pad-field transit (delegated W2/R3-R4)"),
                "status": "EXISTS_WITH_CONSTRAINT (not selected as primary)",
            }
            break

        if candidates:
            best = candidates[0]
            w = best["window"]
            same_side_alts = [c2["window"] for c2 in candidates[1:] if c2["side"] == best["side"]]
            prim = {
                "status": "WITNESSED",
                "kind": "detour",
                "side": best["side"],
                "entry": {"via": "east_rise_column",
                          "x_centre_range": [mm(east_rise[0]), mm(east_rise[1])],
                          "free_y": [[mm(a), mm(b)] for a, b in east_rise_free],
                          "from_band_centre_y": mm(ce)},
                "traverse_window_y": [mm(w[0]), mm(w[1])],
                "pair_centre_window_y": [mm(w[0] + EXT2), mm(w[1] - EXT2)],
                "window_height_mm": mm(w[1] - w[0]),
                "min_required_height_mm": mm(EXT),
                "bounding_keepouts": best["bounding_keepouts"],
                "chain_windows_y": [[mm(a), mm(b)] for a, b in best["chain"]],
                "exit": {"mode": best["exit_mode"],
                         "descent_column_x": [mm(west_descent[0]), mm(west_descent[1])] if best["exit_mode"] == "descent_in_west_slice" else None,
                         "to_band_centre_y": mm(cw),
                         "descent_distance_mm": mm(best["dist"])},
                "alternative_windows_same_side": [[mm(a), mm(b)] for a, b in same_side_alts],
                "selection_rule": "minimal descent distance to the west band, tie-break lowest window; ordering is evidence only — construction choice belongs to W3/R3-R4",
            }
            if alt: prim["coexistence_alternative"] = alt
            per_page[pid] = prim
        else:
            entry = {"status": "NO_WITNESS",
                     "east_band_centre_y": mm(ce), "west_band_centre_y": mm(cw),
                     "detail": "no free window chain connects the two corridor bands under the declared blockers"}
            if alt: entry["coexistence_alternative"] = alt
            per_page[pid] = entry

    witnessed = all(w["status"] == "WITNESSED" for w in per_page.values())
    return {
        "semantics": ("existence proof (a feasibility verdict must carry a constructability guarantee);"
                      " emits free windows only — NO route, NO assignment; construction and final window"
                      " selection belong to W3/R3-R4"),
        "chip_zone_x": [mm(cz[0]), mm(cz[1])],
        "chip_zone_source": "x-gap between the two frozen corridor ranges: WEST_MCIO_TO_CHIP.hi -> EAST_CHIP_TO_J2.lo",
        "pair_copper_extent_mm": mm(EXT),
        "min_channel_height_mm": mm(EXT),
        "keepout_inflation_mm": BODY_CLEARANCE,
        "blockers": [{"ref": b["ref"], "bbox": b["bbox"],
                      "keepout_x": [mm(b["kx"][0]), mm(b["kx"][1])],
                      "keepout_y": [mm(b["ky"][0]), mm(b["ky"][1])]} for b in blockers],
        "slices": [{"x_range": [mm(s["x_range"][0]), mm(s["x_range"][1])],
                    "blockers": s["blockers"],
                    "free_channels_ge_extent": [[mm(a), mm(b)] for a, b in s["channels"]],
                    "sealed_windows_lt_extent": [[mm(a), mm(b)] for a, b in s["sealed_windows"]]}
                   for s in slices],
        "west_slice_channels": [[mm(a), mm(b)] for a, b in slices[0]["channels"]],
        "sealed_or_merged_keepout_pairs": sealed_pairs,
        "transition_columns": {
            "east_rise": {"x_centre_range": [mm(east_rise[0]), mm(east_rise[1])],
                          "free_y": [[mm(a), mm(b)] for a, b in east_rise_free],
                          "bounded_by": ["U6 keepout east edge + copper half-extent",
                                         "J2 pad-field keepout west edge - copper half-extent"]},
            "west_descent": {"x_centre_range": [mm(west_descent[0]), mm(west_descent[1])],
                             "free_y_channels": [[mm(a), mm(b)] for a, b in west_descent_channels],
                             "bounded_by": ["chip-zone west boundary + copper half-extent",
                                            ("capacitor column keepout west edge - copper half-extent"
                                             if cap_kx_lo is not None else "westmost slice east boundary - copper half-extent")]},
            "west_rise_in_corridor": {"x_centre_range": [mm(west_rise_in_corridor[0]), mm(west_rise_in_corridor[1])],
                                      "free_y": [[mm(a), mm(b)] for a, b in west_rise_free],
                                      "caveat": "usable only when it does not cross another REFCLK page's west band (checked per page)"},
        },
        "per_page": per_page,
        "all_pages_witnessed": witnessed,
    }


def main() -> int:
    spec = json.load(open(SPEC, encoding="utf-8"))
    mf = json.load(open(MANIFEST, encoding="utf-8"))
    rules = json.load(open(RULES, encoding="utf-8"))
    y0, y1 = map(float, spec["board"]["outline_y"])
    board_span = [round(y0 + EDGE_CLEARANCE,3), round(y1 - EDGE_CLEARANCE,3)]
    boxes = footprint_boxes()
    # Do not manufacture M3 keepouts: the frozen constraint applies only if a
    # mounting-hole primitive exists.  This is independently recorded for a
    # future board revision to invalidate the envelope when one is added.
    m3_holes_present = "MountingHole" in BOARD.read_text(encoding="utf-8")
    pages = mf["pages"]
    data = [p for p in pages if p["kind"] == "data"]
    refs = sorted([p for p in pages if p["kind"] == "refclk_pass"], key=lambda p: p["page_id"])

    envelope = {"artifact": "m13_v57_big_w0r_inputs", "schema": 1,
      "authority": {"board_outline_stackup_constraints": str(SPEC.relative_to(K2)),
                    "placement_and_body_geometry": str(BOARD.relative_to(K2)),
                    "endpoint_anchors": str(MANIFEST.relative_to(K2)),
                    "rules": str(RULES.relative_to(K2))},
      "inputs_sha256": {"spec": sha(SPEC), "board": sha(BOARD),
                        "manifest": sha(MANIFEST), "rules": sha(RULES)},
      "board": {"outline_y": [y0,y1], "inner_y": board_span,
                "stackup_layers": [k for k in spec["stackup"] if k.endswith(".Cu")]},
      "rules": {"edge_clearance_mm": EDGE_CLEARANCE, "body_clearance_mm": BODY_CLEARANCE,
                "pair_pitch_mm": PITCH, "rule_file_keys": sorted(rules.keys())},
      "keepouts": {"m3_clearance_mm": spec["constraints"]["m3_keepout_mm"],
                   "m3_holes_present": m3_holes_present,
                   "policy": "project a physical M3 primitive only when present; body projections always apply"},
      "corridor_x_ranges_pending_l2_ruling": CORRIDORS,
      "explicit_non_inputs": ["SPEC.corridors", "board tracks", "board vias", "board zones",
                              "legacy lane books"]}
    INPUT.write_text(json.dumps(envelope, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    met = rule_metrics(rules)
    EXT2 = met["pair_extent_hm"] // 2          # copper half extent (585 hm)
    PITCH_HM = met["pitch_hm"]                 # 2920 hm
    census, prim_scan = footprint_census()
    board_sha = sha(BOARD)
    inner_hm = (hm(board_span[0]), hm(board_span[1]))
    face = j2_face_facts()

    result, certificates = {}, []
    for cid, xr in CORRIDORS.items():
        # Endpoint connector pads at a corridor boundary are not bodies in its
        # longitudinal resource; any other footprint overlap is a hard keepout.
        intruders = []
        for b in boxes:
            xlo, ylo, xhi, yhi = b["bbox"]
            if xlo < xr[1] and xhi > xr[0] and b["ref"] not in {"U6", "J2", "J3", "J4"}:
                intruders.append({"ref": b["ref"], "y": [round(ylo-BODY_CLEARANCE,3),
                                                            round(yhi+BODY_CLEARANCE,3)]})
        spans = subtract(board_span, [i["y"] for i in intruders])

        # ---- W0R-G3: full projection enumeration evidence --------------------
        projection_evidence = build_projection_evidence(cid, xr, census, prim_scan, board_sha, intruders)

        groups = {b: [p["page_id"] for p in data if p["corridor"]["id"] == cid
                                      and p["corridor"]["band"] == b] for b in ("up", "dn")}
        band = {b: capacity(spans, len(ids)) for b, ids in groups.items()}
        joint = capacity(spans, sum(len(ids) for ids in groups.values()))

        # ---- W0R-G1: REFCLK conservation certificate (per page, per corridor)
        side = CORRIDOR_ANCHOR_SIDE[cid]
        per_page = []
        for p in refs:
            a = p["anchors"][side]
            yP, yN = a["P"]["pad_global"][1], a["N"]["pad_global"][1]
            xP, xN = a["P"]["pad_global"][0], a["N"]["pad_global"][0]
            centre = hm((yP + yN) / 2)
            band_lo, band_hi = centre - PITCH_HM // 2, centre + PITCH_HM // 2
            cop_lo, cop_hi = centre - EXT2, centre + EXT2
            containing = [s for s in spans if hm(s[0]) <= band_lo and band_hi <= hm(s[1])]
            per_page.append({
                "page_id": p["page_id"],
                "manifest_corridor_id": p["corridor"]["id"],
                "anchor_side_key": side,
                "anchor_ref": a["P"]["ref"],
                "anchor_pads": {"P": {"x": xP, "y": yP, "pad_num": a["P"].get("pad_num"), "net": a["P"]["net"]},
                                "N": {"x": xN, "y": yN, "pad_num": a["N"].get("pad_num"), "net": a["N"]["net"]}},
                "anchor_dy_mm": round(abs(yP - yN), 3),
                "band_centre_y": mm(centre),
                "band_y": [mm(band_lo), mm(band_hi)],
                "copper_y": [mm(cop_lo), mm(cop_hi)],
                "containment": {"single_span_required": True,
                                "containing_span": containing[0] if containing else None,
                                "contained": bool(containing)},
                "_centre_hm": centre, "_band": (band_lo, band_hi), "_copper": (cop_lo, cop_hi),
            })
        separations = []
        for i in range(len(per_page)):
            for j in range(i + 1, len(per_page)):
                d = abs(per_page[i]["_centre_hm"] - per_page[j]["_centre_hm"])
                separations.append({"pages": [per_page[i]["page_id"], per_page[j]["page_id"]],
                                    "separation_mm": mm(d), "required_mm": PITCH,
                                    "ok": d >= PITCH_HM})
        containment_ok = all(r["containment"]["contained"] for r in per_page)
        separation_ok = all(s["ok"] for s in separations)

        # conflicting resources — every class considered, quantified outcome
        conflicting = []
        conflicting.append({"class": "refclk_rows_same_corridor_same_layer", "layer": REFCLK_LAYER,
                            "members": [r["page_id"] for r in per_page],
                            "separations": [{k: v for k, v in s.items()} for s in separations],
                            "outcome": "DISJOINT" if separation_ok else "VIOLATION"})
        conflicting.append({"class": "non_endpoint_body_projections",
                            "count": len(intruders),
                            "outcome": "NONE_IN_CORRIDOR" if not intruders else "PRESENT",
                            "evidence_ref": "projection_evidence (this corridor)"})
        conflicting.append({"class": "m3_keepout", "m3_holes_present": m3_holes_present,
                            "outcome": "ABSENT" if not m3_holes_present else "PRESENT"})
        conflicting.append({"class": "data_bands_cross_layer",
                            "data_layer": DATA_LAYER, "refclk_layer": REFCLK_LAYER,
                            "outcome": "NO_SHARED_COPPER_LAYER",
                            "authority": "drc_rules.json clearance.layer_interaction: elements interact only through a shared copper layer",
                            "note": "all endpoint pads (U6 balls, J2/J3/J4) are SMD on F.Cu per the frozen board; any layer-transition via is R3/R4 construction, not a corridor row resource"})
        overlapping_entries = projection_evidence["endpoint_overlaps"]
        conflicting.append({"class": "endpoint_body_overhang",
                            "entries": [{k: v for k, v in o.items()} for o in overlapping_entries],
                            "outcome": "BOUNDARY_CONDITION_QUANTIFIED",
                            "heir": "W2 connector columns + R3/R4 landing rows"})
        if cid == "EAST_CHIP_TO_J2":
            adjacent = {}
            for r in per_page:
                inband = sorted([p["num"] for p in face["west"]
                                 if r["_band"][0] <= hm(p["y"]) <= r["_band"][1]],
                                key=lambda n: (len(n), n))
                adjacent[r["page_id"]] = inband
            face_clear = face["face_row_pitch_hm"] - face["pad_h_hm"] // 2 - met["p_width_hm"] // 2
            gap = face["inter_column_gap_x"]
            transit_req = met["p_width_hm"] + 2 * met["clearance_hm"]
            inter_pad_window = face["face_row_pitch_hm"] - face["pad_h_hm"]
            pf_y, pf_x = face["pad_field_y"], face["pad_field_x"]
            conflicting.append({"class": "connector_face_row_compression",
                                "face_slice_x": [mm(max(pf_x[0], hm(xr[0]))), mm(min(pf_x[1], hm(xr[1])))],
                                "face_row_pitch_mm": mm(face["face_row_pitch_hm"]),
                                "pad_size_mm": [mm(face["pad_w_hm"]), mm(face["pad_h_hm"])],
                                "row_copper_edge_to_neighbour_pad_mm": mm(face_clear),
                                "required_clearance_mm": BODY_CLEARANCE,
                                "clearance_ok": face_clear >= met["clearance_hm"],
                                "band_neighbour_pads": adjacent,
                                "note": "the anchor pad is the page's own; band reservation applies to the lane run, rows compress to connector face pitch inside the face slice",
                                "outcome": "QUANTIFIED_OK" if face_clear >= met["clearance_hm"] else "VIOLATION",
                                "heir": "W2 + R3/R4"})
            conflicting.append({"class": "connector_pad_field_transit_and_n_escape",
                                "connectors": ["J2"],
                                "inter_column_gap_x": [mm(gap[0]), mm(gap[1])],
                                "inter_column_gap_width_mm": mm(gap[1] - gap[0]),
                                "single_trace_transit_required_mm": mm(transit_req),
                                "inter_column_transit_ok": gap[1] - gap[0] >= transit_req,
                                "inter_pad_window_mm": mm(inter_pad_window),
                                "inter_pad_transit": "BLOCKED (window < single-trace transit requirement)"
                                                     if inter_pad_window < transit_req else "OPEN",
                                "vertical_bypass_windows_y": {
                                    "below": [mm(inner_hm[0]), mm(pf_y[0] - met["clearance_hm"] - met["p_width_hm"] // 2)],
                                    "above": [mm(pf_y[1] + met["clearance_hm"] + met["p_width_hm"] // 2), mm(inner_hm[1])]},
                                "applies_to": "every page with an N anchor in the J2 east column — both REFCLK pages and all accepted data bands share this obligation",
                                "outcome": "DELEGATED_QUANTIFIED",
                                "heir": "W2 (m13_v57_big_w2_connector_cols.json) + R3/R4"})
        else:
            conflicting.append({"class": "connector_pad_field_transit_and_n_escape",
                                "connectors": ["J3", "J4"],
                                "note": ("REFCLK anchors sit inside the J3/J4 SMD pad fields (pad extent reaches the corridor"
                                         " west boundary x=65.05 exactly, zero strict overlap); transit from anchor pads to"
                                         " the corridor crosses same-connector other-net pads and is delegated together with"
                                         " the accepted data bands"),
                                "outcome": "DELEGATED_QUANTIFIED",
                                "heir": "W2 (m13_v57_big_w2_connector_cols.json) + R3/R4"})

        domain_ok = containment_ok and separation_ok
        minimal_unsatisfied_core = ([r["page_id"] for r in per_page if not r["containment"]["contained"]]
                                    + [s["pages"] for s in separations if not s["ok"]])
        shortage_detail = []
        for r in per_page:
            if not r["containment"]["contained"]:
                shortage_detail.append({"page_id": r["page_id"],
                                        "issue": "no_single_usable_span_contains_band",
                                        "band_y": r["band_y"], "usable_y_spans": spans})
        for s in separations:
            if not s["ok"]:
                shortage_detail.append({"pages": s["pages"], "issue": "pitch_separation_violation",
                                        "separation_mm": s["separation_mm"], "required_mm": PITCH})
        ref_domain = {
            "layer": REFCLK_LAYER, "separate_from_data_layer": DATA_LAYER,
            "x_range": xr,
            "resource_kind": "conservation_certificate",
            "certificate_form": "B1.5 (v1 §6 item 4): quantitative conservation per page and per corridor",
            "status": "SATISFIED" if domain_ok else "INFEASIBLE",
            "anchor_side_rule": {"EAST_CHIP_TO_J2": "conn2 (J2 face; J2 west pad column x=132.65 = corridor east bound)",
                                 "WEST_MCIO_TO_CHIP": "conn (J3/J4 face; courtyard east edge x=65.05 = corridor west bound)"}[cid],
            "required": {
                "unit": "pair_row_band (one reserved pitch slot per REFCLK page crossing this corridor x-range on F.Cu)",
                "band_pitch_mm": PITCH,
                "pair_copper_extent_mm": mm(met["pair_extent_hm"]),
                "rows": len(per_page),
                "per_page": [{k: v for k, v in r.items() if not k.startswith("_")} for r in per_page],
            },
            "available": {
                "usable_y_spans_fcu_mm": spans,
                "span_source": ("same subtraction as the data layer: body blockers are layer-independent and"
                                " non-endpoint intruders are zero (projection_evidence); F.Cu adds no declared"
                                " blockers of its own (board copper is a declared non-input)"),
                "per_page_containment": [{"page_id": r["page_id"], **r["containment"]} for r in per_page],
                "pairwise_separations": [{k: v for k, v in s.items()} for s in separations],
                "row_band_capacity_note": (f"single span [{spans[0][0]},{spans[0][1]}] admits "
                                            f"{(hm(spans[0][1])-hm(spans[0][0]))//PITCH_HM + 1} pitch rows >= "
                                            f"{len(per_page)} required") if len(spans) == 1
                                          else "multi-span: per-row single-span containment checked individually",
            },
            "shortage": {
                "unsatisfied_rows": sum(1 for r in per_page if not r["containment"]["contained"]),
                "separation_violations": sum(1 for s in separations if not s["ok"]),
                "containment_violations": sum(1 for r in per_page if not r["containment"]["contained"]),
                "passage_witness": "see top-level refclk_passage_witness",
                "detail": shortage_detail,
            },
            "conflicting_resources": conflicting,
            "minimal_core": {
                "members": minimal_unsatisfied_core,
                "semantics": ("empty ⇒ conservation satisfied: no unsatisfiable subset under the declared inputs;"
                              " non-empty ⇒ the canonical minimal set of row bands / separation pairs that cannot"
                              " be granted simultaneously (v1 §2 escalation invariant)"),
            },
            "anchors": [],   # filled below (accepted anchor rows preserved verbatim)
            "reason": ("quantitative conservation per v1 §6 item 4; F.Cu route/obstacle/return-path construction"
                       " remains R3/R4 — W0-R claims resources and existence, never a route"),
        }
        refrows = []
        for p in refs:
            a = p["anchors"]
            refrows.append({"page_id":p["page_id"], "j2_y": [a["conn2"][q]["pad_global"][1] for q in ("P","N")],
                            "far_ref": a["conn"]["P"]["ref"],
                            "far_y": [a["conn"][q]["pad_global"][1] for q in ("P","N")]})
        ref_domain["anchors"] = refrows

        result[cid] = {"x_range": xr, "usable_y_spans": spans,
                       "blocked_component_projections": intruders,
                       "projection_evidence": projection_evidence,
                       "keepout_application": {"m3_holes_present": m3_holes_present,
                                               "m3_projected": False,
                                               "component_body_clearance_mm": BODY_CLEARANCE},
                       "data_layer": DATA_LAYER,
                       "joint_data_frame": {"band_order": ["up", "dn"], **joint},
                       "data_bands": {b:{"page_ids":groups[b], **band[b]} for b in ("up","dn")},
                       "refclk_resource_domain": ref_domain,
                       "_refclk_pages": per_page}
        for b in ("up", "dn"):
            if not band[b]["feasible"]:
                certificates.append({"kind":"BOARD_INTENT_INFEASIBLE_CERT", "blocked":"R2_lane_frame",
                  "corridor":cid, "band":b, "required":{"pairs":len(groups[b]), "centre_span_mm":band[b]["centre_span_needed_mm"]},
                  "available":{"usable_y_spans":spans}, "shortage":"no_single_usable_span_can_host_band",
                  "conflicts":intruders, "canonical_core":groups[b],
                  "escape_hatches":["change L1 placement/corridor", "add signal layer by L2 ruling", "reduce pair demand"]})
        if not joint["feasible"]:
            certificates.append({"kind":"BOARD_INTENT_INFEASIBLE_CERT", "blocked":"R2_lane_frame",
              "corridor":cid, "band":"joint(up+dn)", "required":{"pairs":joint["n_pairs"], "centre_span_mm":joint["centre_span_needed_mm"]},
              "available":{"usable_y_spans":spans}, "shortage":"no_single_usable_span_can_host_joint_frame",
              "conflicts":intruders, "canonical_core":groups["up"]+groups["dn"],
              "escape_hatches":["change L1 placement/corridor", "add signal layer by L2 ruling", "reduce pair demand"]})
        if not domain_ok:
            certificates.append({"kind":"B1.5_INFEASIBLE_CERT", "blocked":"REFCLK_resource_domain",
              "corridor":cid,
              "required":{"rows":len(per_page), "per_page":[r["page_id"] for r in per_page]},
              "available":{"usable_y_spans":spans},
              "shortage":ref_domain["shortage"],
              "conflicting_resources":conflicting,
              "canonical_core":minimal_unsatisfied_core,
              "escape_hatches":["L1: change REFCLK interface topology/endpoints",
                                "L2: change corridor x-ranges / placement / stackup",
                                "L2: move bodies out of corridor x-ranges",
                                "L2: re-rule REFCLK resource layer"]})

    # ---- chip-zone passage existence witness (constructability guarantee) ----
    witness = build_passage_witness(census, result, inner_hm, met)
    missing = sorted(pid for pid, w in witness["per_page"].items() if w["status"] != "WITNESSED")
    if missing:
        for cid in result:
            rd = result[cid]["refclk_resource_domain"]
            rd["status"] = "INFEASIBLE"
            rd["shortage"]["passage_witness"] = "MISSING"
            rd["shortage"]["detail"].append(f"passage witness missing for: {missing}")
            rd["minimal_core"]["members"] = missing
        certificates.append({"kind":"B1.5_INFEASIBLE_CERT", "blocked":"REFCLK_passage",
          "corridor":"EAST+WEST_CHIP_TO_CONN",
          "required":{"pages":missing},
          "available":{"west_slice_channels":witness["west_slice_channels"],
                       "sealed_or_merged_keepout_pairs":witness["sealed_or_merged_keepout_pairs"]},
          "shortage":"no free window chain connects the corridor bands for the listed pages",
          "conflicting_resources":[b["ref"] for b in witness["blockers"]],
          "canonical_core":missing,
          "escape_hatches":["L1: change REFCLK interface topology/endpoints",
                            "L2: change corridor x-ranges / placement (chip-zone bypass channels)",
                            "L2: move chip-zone decoupling bodies",
                            "L2: re-rule REFCLK resource layer"]})
    for cid in result:
        rd = result[cid]["refclk_resource_domain"]
        rd["passage_witness_ref"] = ("top-level refclk_passage_witness (the chip zone lies between the two"
                                     " corridors; the witness is inherently cross-corridor)")
        rd["per_page_passage_status"] = {pid: w["status"] for pid, w in witness["per_page"].items()}

    refclk_ok = all(result[c]["refclk_resource_domain"]["status"] == "SATISFIED" for c in result)
    verdict = "B1.5 PASS" if (not certificates and refclk_ok) else "B1.5 INFEASIBLE_CERT"

    for cid in result:
        result[cid].pop("_refclk_pages")

    report = {"artifact":"m13_v57_big_w0r_corridor_model", "schema":2, "revision":REV,
              "producer":{
                  "generator":{"path":str(GENERATOR.relative_to(K2)),"revision":REV,"sha256":sha(GENERATOR)},
                  "validator":{"path":str(VALIDATOR_TOOL.relative_to(K2)),"revision":REV,"sha256":sha(VALIDATOR_TOOL)},
                  "split":"the validator does not import this module; it re-parses the frozen sources and re-derives every claim independently"},
              "input_artifact": INPUT.name, "input_artifact_sha256":sha(INPUT),
              "evidence_protocol_v1_s3":{
                  "item1_schema_versions":"schema + revision + producer block (generator/validator tool paths, revisions, sha256 fingerprints)",
                  "item2_source_fingerprints_authority":"input envelope m13_v57_big_w0r_inputs.json: authority classification + inputs_sha256 (spec/board/manifest/rules), pinned here by input_artifact_sha256",
                  "item3_deterministic_status":"verdict: exactly one of B1.5 PASS / B1.5 INFEASIBLE_CERT; double_run_contract below",
                  "item4_demand_capacity_minimal_core":"data_bands + joint_data_frame (demand vs candidate spans); refclk_resource_domain.required/available/shortage/minimal_core per corridor; refclk_passage_witness (existence)",
                  "item5_legal_escape_hatches":"legal_escape_hatches (upstream input changes only) + certificates[].escape_hatches",
                  "item6_independent_validation":"m13_v57_big_w0r_validation.json produced by the separately implemented validator"},
              "verdict_rule":{
                  "B1.5 PASS":"certificates == [] AND every refclk_resource_domain.status == SATISFIED AND every data band/joint frame feasible",
                  "B1.5 INFEASIBLE_CERT":"otherwise; each certificate carries required/available/shortage/conflicts/canonical minimal core/escape hatches",
                  "no_third_state":"any other value is invalid and keeps W0-R BLOCKED (v1 §6)"},
              "legal_escape_hatches":{
                  "principle":"escape hatches are upstream input changes only; downstream construction edits are never a legal hatch (v1 §3 item 5)",
                  "hatches":[
                      {"target_layer":"L1","change":"interface topology / netlist: REFCLK page count, endpoints or pass-through structure"},
                      {"target_layer":"L2","change":"corridor x-ranges (pending-L2 ruling constants), component placement or stackup layer assignment"},
                      {"target_layer":"L2","change":"introduce/move bodies or M3 mounting holes into corridor x-ranges or chip-zone passage channels"},
                      {"target_layer":"L2","change":"REFCLK resource-layer ruling (currently F.Cu, separate from the In2.Cu data layer)"}]},
              "corridors":result,
              "refclk_passage_witness":witness,
              "certificates":certificates, "verdict":verdict,
              "double_run_contract":"canonical JSON (sorted keys, trailing newline) must be byte-identical"}
    OUT.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"verdict":verdict,
                      "refclk_status":{c:result[c]["refclk_resource_domain"]["status"] for c in result},
                      "passage":{pid:w["status"] for pid,w in witness["per_page"].items()},
                      "corridors":{k:v["usable_y_spans"] for k,v in result.items()},
                      "certificate_count":len(certificates)}, indent=1))
    return 0


if __name__ == "__main__": raise SystemExit(main())
