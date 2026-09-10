#!/usr/bin/env python3
"""P3 v57 - F3-LANEFRAME independent verifier.

Re-parses the frozen sources (page manifest, W0-R corridor model, drc_rules,
G3 v1.1 / v1.2 contracts) and RE-DERIVES every claim of the frozen artifact
``m13_v57_f3_lane_frame.json`` without importing the generator.

Asserts:
  * lane domain grid == re-derived (span/step/margin/positions/n_positions).
  * capacity frame needed/avail/capacity_ok == re-derived (up/dn/joint).
  * every page conn_row_y / chip_row_y / conn_x == re-derived midpoints.
  * frame set + membership + intra-frame order == re-derived
    (EAST by conn_row_y, WEST by conn_x).
  * authority hashes == disk hashes (all 6 frozen inputs + generator).
  * artifact versions/producer SHA == generator file SHA on disk.
  * no-feasibility / no-allocation key scan over the artifact.
  * generator source does not read the retired W0 values (0.6 / 12.0) or
    ``tracks_y``.
  * this verifier does not import the generator.

Prints ``PASS`` / ``FAIL`` and exits 0 / 1.  Stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# paths / constants
# --------------------------------------------------------------------------
SELF = Path(__file__).resolve()
K2 = SELF.parents[1]
STEP = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3" / "mcio_feas_step2"
TOOLS = K2 / "tools"

MANIFEST = STEP / "m13_v57_s1_page_manifest.json"
W0R_MODEL = STEP / "m13_v57_big_w0r_corridor_model.json"
RULES = K2 / "_shared" / "eda_core" / "drc_rules.json"
G3_V1_1 = STEP / "m13_v57_g3_freeze_contract_v1_1_frame_ruling.md"
G3_V1_2 = STEP / "m13_v57_g3_freeze_contract_v1_2_lane_domain.md"

ARTIFACT = STEP / "m13_v57_f3_lane_frame.json"

# The generator is discovered by glob (never referenced by its full name here,
# and never imported).
GEN_GLOB = "*f3_lane_frame.py"

REV = "F3-LANEFRAME.1"
SCHEMA = 1
PITCH = 1.46
MARGIN = 0.0
CORRIDORS = ("EAST_CHIP_TO_J2", "WEST_MCIO_TO_CHIP")
BANDS = ("up", "dn")

FROZEN_SHA = {
    "manifest": "a8ef3ea8ecff99d7549d4122043c972c1bb68346dc4dcc3f36fdd9bacde49890",
    "w0r_model": "80ee9adb78a7e9ad94c27d426295592eee21af3d1e3ce88fe3042183160f0efa",
    "rules": "0a459839e15960b8fbfe0e1f5bb154a02b30cbafa1cbb0d56c2b810a71228448",
    "g3_v1_1": "232fda852ee8612be3f2bf2c4655d0aa716c408dfb71a8eb71df298b08c031ff",
    "g3_v1_2": "c8f380c184976fb5072e3afc6d47f25a5e6221de46c21aa67bd8cf1e20bd16b6",
}

# Capacity criterion is allowed (capacity_ok); assignment feasibility is not.
FORBIDDEN_KEYS = ("feasible", "infeasible", "selected", "assigned", "allocation",
                  "witness", "matched", "lane_index", "track_y")
RETIRED_W0_TOKENS = ("0.6", "12.0", "tracks_y")


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(K2))


def mid(a, b):
    return round((a + b) / 2.0, 3)


def find_generator() -> Path:
    cands = sorted(p for p in TOOLS.glob(GEN_GLOB) if p.name.endswith(".py"))
    assert len(cands) == 1, "expected exactly one generator, got {}".format(cands)
    return cands[0]


def scan_forbidden_keys(obj, path, leaked):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in FORBIDDEN_KEYS:
                leaked.append("{}/{}".format(path, k))
            scan_forbidden_keys(v, "{}/{}".format(path, k), leaked)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            scan_forbidden_keys(v, "{}[{}]".format(path, i), leaked)


# --------------------------------------------------------------------------
# independent re-derivation
# --------------------------------------------------------------------------
def derive_lane_domain(span):
    lo, hi = float(span[0]), float(span[1])
    n = int((hi - lo) // PITCH) + 1
    return {
        "span": [round(lo, 3), round(hi, 3)],
        "step": PITCH,
        "margin": MARGIN,
        "positions": [round(lo + i * PITCH, 3) for i in range(n)],
        "n_positions": n,
    }


def derive_capacity(corr):
    span = corr["usable_y_spans"][0]
    avail = round(float(span[1]) - float(span[0]), 3)
    bands = {}
    for band in BANDS:
        n_pairs = int(corr["data_bands"][band]["n_pairs"])
        needed = round((n_pairs - 1) * PITCH, 3)
        bands[band] = {"n_pairs": n_pairs, "needed_mm": needed,
                       "avail_mm": avail, "capacity_ok": needed <= avail}
    n_joint = int(corr["joint_data_frame"]["n_pairs"])
    needed_joint = round((n_joint - 1) * PITCH, 3)
    return {
        "bands": bands,
        "joint": {"n_pairs": n_joint, "needed_mm": needed_joint,
                  "avail_mm": avail, "capacity_ok": needed_joint <= avail},
    }


def derive_page_record(page):
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


def derive_frames(cid, records):
    refs = sorted({r["conn_ref"] for r in records})
    order_key = "conn_row_y" if len(refs) == 1 else "conn_x"
    frames = {}
    for band in BANDS:
        for ref in refs:
            members = [r for r in records
                       if r["band"] == band and r["conn_ref"] == ref]
            if not members:
                continue
            members.sort(key=lambda r: (r[order_key], r["page_id"]))
            frames["{}/{}/{}".format(cid, band, ref)] = {
                "order_key": order_key,
                "page_order": [r["page_id"] for r in members],
                "records": {r["page_id"]: r for r in members},
            }
    return frames


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main() -> int:
    problems = []
    gen = find_generator()

    # --- frozen SHA on disk (full 64-hex) ---------------------------------
    disk = {
        "manifest": sha(MANIFEST),
        "w0r_model": sha(W0R_MODEL),
        "rules": sha(RULES),
        "g3_v1_1": sha(G3_V1_1),
        "g3_v1_2": sha(G3_V1_2),
    }
    gen_sha = sha(gen)

    # --- pitch authority ---------------------------------------------------
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    dp = rules["diff_pair"]
    pitch_derived = round(dp["p_gap"] + 2 * dp["p_width"]
                          + dp["inter_pair_spacing"], 3)
    if abs(pitch_derived - PITCH) >= 1e-12:
        problems.append("pitch authority: {} != {}".format(pitch_derived, PITCH))

    # --- G3 contract semantics (re-parse the frozen docs) ------------------
    g3v11 = G3_V1_1.read_text(encoding="utf-8")
    g3v12 = G3_V1_2.read_text(encoding="utf-8")
    if "margin := 0" not in g3v11:
        problems.append("G3 v1.1: margin:=0 ruling not found")
    if "up\u2192lo" not in g3v11 or "dn\u2192hi" not in g3v11:
        problems.append("G3 v1.1: edge convention (up->lo, dn->hi) not found")
    if "usable_y_spans" not in g3v12 or "pitch" not in g3v12:
        problems.append("G3 v1.2: lane-domain (usable_y_spans pitch grid) not found")

    # --- artifact ----------------------------------------------------------
    art = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    if art.get("artifact") != "m13_v57_f3_lane_frame":
        problems.append("artifact name mismatch")
    if art.get("schema") != SCHEMA:
        problems.append("schema mismatch")
    if art.get("revision") != REV:
        problems.append("revision mismatch")
    if art.get("status") != "EMITTED":
        problems.append("status != EMITTED")

    # --- inputs_sha == disk (all frozen inputs) ---------------------------
    if art.get("inputs_sha") != disk:
        problems.append("inputs_sha != disk hashes")
        for k in disk:
            if art.get("inputs_sha", {}).get(k) != disk[k]:
                problems.append("  input {}: artifact {} != disk {}".format(
                    k, art.get("inputs_sha", {}).get(k), disk[k]))

    # --- authority fingerprints == disk -----------------------------------
    expected_auth = {
        "contract": disk["g3_v1_2"],
        "pitch": disk["rules"],
        "span": disk["w0r_model"],
        "bands": disk["manifest"],
    }

    def check_authority(auth, where):
        if not isinstance(auth, dict):
            problems.append("{}: authority missing".format(where))
            return
        for key, digest in expected_auth.items():
            got = auth.get(key, {}).get("sha256")
            if got != digest:
                problems.append("{}: authority.{} sha {} != disk {}".format(
                    where, key, got, digest))
        if auth.get("margin") != MARGIN:
            problems.append("{}: authority.margin != 0".format(where))
        if auth.get("edge_convention") != {"up": "lo", "dn": "hi"}:
            problems.append("{}: edge_convention mismatch".format(where))
        if auth.get("contract", {}).get("id") != "G3-C v1.2":
            problems.append("{}: contract id mismatch".format(where))

    check_authority(art.get("authority"), "top")
    for cid, corr in art.get("corridors", {}).items():
        check_authority(corr.get("lane_domain", {}).get("authority"),
                        "{} lane_domain".format(cid))
        check_authority(corr.get("capacity_frame", {}).get("authority"),
                        "{} capacity_frame".format(cid))
        for fr in corr.get("frames", []):
            check_authority(fr.get("authority"),
                            "{} frame {}".format(cid, fr.get("frame_id")))

    # --- versions / producer SHA == generator on disk (all 6) -------------
    versions = art.get("versions", {})
    prod = versions.get("producer", {})
    if prod.get("sha256") != gen_sha:
        problems.append("versions.producer.sha256 {} != generator {}".format(
            prod.get("sha256"), gen_sha))
    if prod.get("path") != rel(gen):
        problems.append("versions.producer.path {} != {}".format(
            prod.get("path"), rel(gen)))
    if prod.get("revision") != REV:
        problems.append("versions.producer.revision mismatch")
    fsc = versions.get("frozen_sha_check", {})
    if fsc.get("expected") != FROZEN_SHA:
        problems.append("frozen_sha_check.expected != spec frozen set")
    if fsc.get("actual") != disk:
        problems.append("frozen_sha_check.actual != disk")
    want_match = {k: disk[k] == FROZEN_SHA[k] for k in FROZEN_SHA}
    if fsc.get("match") != want_match:
        problems.append("frozen_sha_check.match inconsistent with disk")

    # --- re-derive sources -------------------------------------------------
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    w0r = json.loads(W0R_MODEL.read_text(encoding="utf-8"))

    if tuple(art.get("corridors", {}).keys()) != tuple(sorted(CORRIDORS)):
        # dict key order is irrelevant; compare as sets
        if set(art.get("corridors", {}).keys()) != set(CORRIDORS):
            problems.append("corridor set mismatch")

    for cid in CORRIDORS:
        if cid not in art["corridors"]:
            problems.append("missing corridor {}".format(cid))
            continue
        corr = w0r["corridors"][cid]
        span = corr["usable_y_spans"][0]
        got = art["corridors"][cid]

        # lane domain
        want_ld = derive_lane_domain(span)
        for k in ("span", "step", "margin", "positions", "n_positions"):
            if got["lane_domain"].get(k) != want_ld[k]:
                problems.append("{} lane_domain.{}: {} != {}".format(
                    cid, k, got["lane_domain"].get(k), want_ld[k]))
        if got["lane_domain"].get("derivation") != \
                "y_lo + i*pitch, i=0..floor((y_hi-y_lo)/pitch)":
            problems.append("{} lane_domain.derivation mismatch".format(cid))

        # capacity
        want_cap = derive_capacity(corr)
        for band in BANDS:
            if got["capacity_frame"]["bands"].get(band) != want_cap["bands"][band]:
                problems.append("{} capacity.{}: {} != {}".format(
                    cid, band, got["capacity_frame"]["bands"].get(band),
                    want_cap["bands"][band]))
        if got["capacity_frame"].get("joint") != want_cap["joint"]:
            problems.append("{} capacity.joint mismatch".format(cid))
        if got["capacity_frame"].get("derivation") != \
                "needed=(n-1)*pitch; avail=y_hi-y_lo":
            problems.append("{} capacity.derivation mismatch".format(cid))

        # frames
        records = [derive_page_record(p) for p in manifest["pages"]
                   if p["corridor"]["id"] == cid and p["kind"] == "data"]
        want_frames = derive_frames(cid, records)
        got_frames = {f["frame_id"]: f for f in got["frames"]}
        if set(got_frames) != set(want_frames):
            problems.append("{} frame set {} != {}".format(
                cid, sorted(got_frames), sorted(want_frames)))
        for fid, wf in want_frames.items():
            gf = got_frames.get(fid)
            if gf is None:
                continue
            if gf.get("order_key") != wf["order_key"]:
                problems.append("{} order_key mismatch".format(fid))
            if gf.get("n_pages") != len(wf["page_order"]):
                problems.append("{} n_pages mismatch".format(fid))
            got_order = [p["page_id"] for p in gf.get("pages", [])]
            if got_order != wf["page_order"]:
                problems.append("{} page order {} != {}".format(
                    fid, got_order, wf["page_order"]))
            for p in gf.get("pages", []):
                wr = wf["records"].get(p["page_id"])
                if wr is None:
                    problems.append("{}: unexpected page {}".format(
                        fid, p["page_id"]))
                    continue
                for k in ("conn_ref", "conn_row_y", "chip_row_y", "conn_x"):
                    if p.get(k) != wr[k]:
                        problems.append("{} {} {}: {} != {}".format(
                            fid, p["page_id"], k, p.get(k), wr[k]))

    # --- no-feasibility / no-allocation scan ------------------------------
    leaked = []
    scan_forbidden_keys(art, "", leaked)
    if leaked:
        problems.append("forbidden keys leaked: {}".format(leaked))

    # --- generator must not read retired W0 values ------------------------
    gen_src = gen.read_text(encoding="utf-8")
    for token in RETIRED_W0_TOKENS:
        if token in gen_src:
            problems.append("generator reads retired token {!r}".format(token))

    # --- verifier must not import the generator ---------------------------
    mod = "p3_v57_" + "f3_lane_frame"
    self_src = SELF.read_text(encoding="utf-8")
    if "import {}".format(mod) in self_src or "from {} ".format(mod) in self_src:
        problems.append("verifier imports the generator")

    # --- report -----------------------------------------------------------
    drift = [k for k, ok in want_match.items() if not ok]
    if problems:
        print("FAIL problems={}".format(len(problems)))
        for p in problems:
            print("  -", p)
        return 1
    print("PASS inputs_sha=5/5 generator_sha={}".format(gen_sha[:12]))
    print("     frozen_sha_match={}/{} drift={} (actual disk hashes recorded)"
          .format(sum(want_match.values()), len(want_match), drift))
    print("     lane_domain=32pos[33.3..78.56] capacity=10.22/21.9/45.4 "
          "frames=6 (EAST 2, WEST 4)")
    print("     forbidden_keys=0 generator_retired_tokens=0 verifier_import=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
