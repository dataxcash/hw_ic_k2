#!/usr/bin/env python3
"""P3 v57 - F3-LANEFRAME: emit the R2 assignment lane domain + capacity frame.

This tool freezes (deterministically) the R2 assignment *candidate domain* and
the independent *capacity frame* for the two W0-R corridors.  It performs NO
allocation and NO feasibility judgement -- assignment feasibility belongs to
F4 / F-6b.

Emits, per corridor (EAST_CHIP_TO_J2, WEST_MCIO_TO_CHIP):

  * ``lane_domain``    -- pitch grid over ``usable_y_spans`` (G3 v1.2 s1);
                          this is the R2 assignment candidate domain.
  * ``capacity_frame`` -- independent capacity criterion (G3 v1.1 s1.4):
                          needed=(n-1)*pitch vs avail=y_hi-y_lo.  This is the
                          CAPACITY criterion ONLY, never assignment feasibility.
  * ``frames``         -- page-level ``conn_row_y`` / ``chip_row_y`` frames;
                          EAST (conn_ref=J2 single) ordered by ``conn_row_y``;
                          WEST (conn_ref in {J3,J4}) ordered by ``conn_x``.
  * ``authority``      -- per-frame authority fingerprint block (G3 v1.1 s3).

The report is canonical JSON: ``json.dumps(rep, indent=1, ensure_ascii=False,
sort_keys=True)`` and is byte-identical across consecutive runs.

Stdlib only.  The independent verifier
``p3_v57_f3_lane_frame_validator.py`` does NOT import this module; it re-parses
the frozen sources and re-derives every claim.
"""

from __future__ import annotations

import hashlib
import json
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

OUT = STEP / "m13_v57_f3_lane_frame.json"

REV = "F3-LANEFRAME.1"
SCHEMA = 1
PITCH = 1.46
MARGIN = 0.0
CORRIDORS = ("EAST_CHIP_TO_J2", "WEST_MCIO_TO_CHIP")
BANDS = ("up", "dn")

# Spec-frozen SHA-256 (verified at runtime; full 64-hex recorded in the report).
# NOTE: the w0r_model entry is the true on-disk digest (the task text carried a
# cache marker inside it); it equals the digest pinned by the W0-R/F6b tools.
FROZEN_SHA = {
    "manifest": "a8ef3ea8ecff99d7549d4122043c972c1bb68346dc4dcc3f36fdd9bacde49890",
    "w0r_model": "80ee9adb78a7e9ad94c27d426295592eee21af3d1e3ce88fe3042183160f0efa",
    "rules": "0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448",
    "g3_v1_1": "232fda852ee8612be3f2bf2c4655d0aa716c408dfb71a8eb71df298b08c031ff",
    "g3_v1_2": "c8f380c184976fb5072e3afc6d47f25a5e6221de46c21aa67bd8cf1e20bd16b6",
}

PREDICATE = (
    "R2 assignment candidate domain (G3 v1.2 s1): pages sorted by "
    "(row_y,page_id) map to strictly increasing lane index; "
    "|lane_y - row_y| <= leg; row_y=(N.y+P.y)/2. "
    "Feasibility is NOT evaluated here (F4/F-6b)."
)

DERIV_LANE = "y_lo + i*pitch, i=0..floor((y_hi-y_lo)/pitch)"
DERIV_CAP = "needed=(n-1)*pitch; avail=y_hi-y_lo"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def sha(path: Path) -> str:
    """SHA-256 of a file, full 64-hex."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    """Path relative to the K2 repo root."""
    return str(path.relative_to(K2))


def mid(a: float, b: float) -> float:
    """Midpoint rounded to 3 decimals (canonical row_y / x)."""
    return round((a + b) / 2.0, 3)


# --------------------------------------------------------------------------
# derivation
# --------------------------------------------------------------------------
def build_authority(inputs_sha):
    """Authority fingerprint block (G3 v1.1 s3) attached to every domain/frame."""
    return {
        "contract": {
            "id": "G3-C v1.2",
            "path": rel(G3_V1_2),
            "sha256": inputs_sha["g3_v1_2"],
        },
        "pitch": {
            "source": rel(RULES),
            "sha256": inputs_sha["rules"],
        },
        "span": {
            "source": ("m13_v57_big_w0r_corridor_model.json "
                       "corridors.*.usable_y_spans"),
            "sha256": inputs_sha["w0r_model"],
        },
        "bands": {
            "source": "m13_v57_s1_page_manifest.json",
            "sha256": inputs_sha["manifest"],
        },
        "margin": MARGIN,
        "edge_convention": {"up": "lo", "dn": "hi"},
    }


def build_lane_domain(corr, authority):
    """Pitch grid over usable_y_spans[0] -- the R2 assignment candidate domain."""
    span = corr["usable_y_spans"][0]
    lo, hi = float(span[0]), float(span[1])
    n = int((hi - lo) // PITCH) + 1
    positions = [round(lo + i * PITCH, 3) for i in range(n)]
    return {
        "span": [round(lo, 3), round(hi, 3)],
        "step": PITCH,
        "margin": MARGIN,
        "positions": positions,
        "n_positions": len(positions),
        "derivation": DERIV_LANE,
        "authority": authority,
    }


def build_capacity_frame(corr, authority):
    """Independent capacity criterion (G3 v1.1 s1.4) -- NOT feasibility."""
    span = corr["usable_y_spans"][0]
    avail = round(float(span[1]) - float(span[0]), 3)
    bands = {}
    for band in BANDS:
        n_pairs = int(corr["data_bands"][band]["n_pairs"])
        needed = round((n_pairs - 1) * PITCH, 3)
        bands[band] = {
            "n_pairs": n_pairs,
            "needed_mm": needed,
            "avail_mm": avail,
            "capacity_ok": needed <= avail,
        }
    n_joint = int(corr["joint_data_frame"]["n_pairs"])
    needed_joint = round((n_joint - 1) * PITCH, 3)
    return {
        "bands": bands,
        "joint": {
            "n_pairs": n_joint,
            "needed_mm": needed_joint,
            "avail_mm": avail,
            "capacity_ok": needed_joint <= avail,
        },
        "derivation": DERIV_CAP,
        "authority": authority,
    }


def page_record(page):
    """Page-level conn/chip row + conn x midpoints and the WEST conn_ref."""
    conn = page["anchors"]["conn"]
    chip = page["anchors"]["chip"]
    return {
        "page_id": page["page_id"],
        "band": page["corridor"]["band"],
        "conn_ref": conn["P"]["ref"],
        "conn_row_y": mid(conn["P"]["pad_global"][1], conn["N"]["pad_global"][1]),
        "chip_row_y": mid(chip["P"]["pad_global"][1], chip["N"]["pad_global"][1]),
        "conn_x": mid(conn["P"]["pad_global"][0], conn["N"]["pad_global"][0]),
    }


def build_frames(cid, records, authority):
    """Frame per band (EAST) / per (band, conn_ref) (WEST), with ordered pages."""
    refs = sorted({r["conn_ref"] for r in records})
    order_key = "conn_row_y" if len(refs) == 1 else "conn_x"
    frames = []
    for band in BANDS:
        for ref in refs:
            members = [r for r in records
                       if r["band"] == band and r["conn_ref"] == ref]
            if not members:
                continue
            members.sort(key=lambda r: (r[order_key], r["page_id"]))
            pages = [
                {
                    "page_id": r["page_id"],
                    "conn_ref": r["conn_ref"],
                    "conn_row_y": r["conn_row_y"],
                    "chip_row_y": r["chip_row_y"],
                    "conn_x": r["conn_x"],
                    "order_index": i,
                }
                for i, r in enumerate(members)
            ]
            frames.append({
                "frame_id": "{}/{}/{}".format(cid, band, ref),
                "band": band,
                "conn_ref": ref,
                "order_key": order_key,
                "n_pages": len(pages),
                "pages": pages,
                "authority": authority,
            })
    return frames


def build_report():
    # --- pitch authority: RULES["diff_pair"] must derive 1.46 --------------
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    dp = rules["diff_pair"]
    pitch_derived = round(dp["p_gap"] + 2 * dp["p_width"]
                          + dp["inter_pair_spacing"], 3)
    assert abs(pitch_derived - PITCH) < 1e-12, (
        "pitch authority drift: derived {} != {}".format(pitch_derived, PITCH))

    # --- frozen fingerprints (recorded full 64-hex; drift flagged) ---------
    inputs_sha = {
        "manifest": sha(MANIFEST),
        "w0r_model": sha(W0R_MODEL),
        "rules": sha(RULES),
        "g3_v1_1": sha(G3_V1_1),
        "g3_v1_2": sha(G3_V1_2),
    }
    match = {k: inputs_sha[k] == FROZEN_SHA[k] for k in FROZEN_SHA}

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    w0r = json.loads(W0R_MODEL.read_text(encoding="utf-8"))

    authority = build_authority(inputs_sha)

    corridors = {}
    for cid in CORRIDORS:
        corr = w0r["corridors"][cid]
        records = [page_record(p) for p in manifest["pages"]
                   if p["corridor"]["id"] == cid and p["kind"] == "data"]
        corridors[cid] = {
            "lane_domain": build_lane_domain(corr, authority),
            "capacity_frame": build_capacity_frame(corr, authority),
            "frames": build_frames(cid, records, authority),
        }

    rep = {
        "artifact": "m13_v57_f3_lane_frame",
        "schema": SCHEMA,
        "revision": REV,
        "predicate": PREDICATE,
        "authority": authority,
        "corridors": corridors,
        "inputs_sha": inputs_sha,
        "versions": {
            "producer": {
                "path": rel(SELF),
                "revision": REV,
                "sha256": sha(SELF),
            },
            "frozen_sha_check": {
                "expected": dict(FROZEN_SHA),
                "actual": dict(inputs_sha),
                "match": match,
            },
        },
        "status": "EMITTED",
    }
    return rep, match


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main() -> int:
    rep, match = build_report()
    OUT.write_text(json.dumps(rep, indent=1, ensure_ascii=False,
                              sort_keys=True), encoding="utf-8")

    east = rep["corridors"]["EAST_CHIP_TO_J2"]
    west = rep["corridors"]["WEST_MCIO_TO_CHIP"]
    ld = east["lane_domain"]
    cap = east["capacity_frame"]
    n_frames = (len(east["frames"]) + len(west["frames"]))
    drifted = [k for k, ok in match.items() if not ok]
    print("F3-LANEFRAME status={} rev={}".format(rep["status"], REV))
    print("lane_domain n_positions={} first={} last={}".format(
        ld["n_positions"], ld["positions"][0], ld["positions"][-1]))
    print("capacity up={} joint={}".format(
        cap["bands"]["up"]["needed_mm"], cap["joint"]["needed_mm"]))
    print("frames={} east={} west={}".format(
        n_frames, len(east["frames"]), len(west["frames"])))
    if drifted:
        print("WARNING frozen SHA drift (actual recorded): {}".format(drifted))
    print("artifact:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
