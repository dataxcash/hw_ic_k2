#!/usr/bin/env python3
"""P3 v57 F8 — independent validator for the R3 gap-candidate artifact.

Re-parses the frozen sources (page manifest / SPEC / drc_rules) and re-derives
the R3 domain WITHOUT importing the generator, then asserts agreement on every
pad's gap candidates, the conservation verdict and the conflict graph. It also
asserts the artifact contains no allocation / W3 selection field.
"""
import hashlib
import json
import sys
from pathlib import Path

K2 = Path("/home/fila/jqdDev_2025/ic_hw/k2")
L3 = K2 / "pm_gate" / "artifacts" / "k2_v4" / "L3"
STEP2 = L3 / "mcio_feas_step2"
MANIFEST = STEP2 / "m13_v57_s1_page_manifest.json"
SPEC = L3 / "SPEC_k2_v4.json"
RULES = K2 / "_shared" / "eda_core" / "drc_rules.json"
ARTIFACT = STEP2 / "m13_v57_f8_r3_gap_candidates.json"
GENERATOR = Path(__file__).resolve().with_name("p3_v57_f8_r3_gap_candidates.py")
PAD_W = {"J2": 1.3, "J3": 0.3, "J4": 0.3}
REV = "R3GEN-F8.1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def r3(v: float) -> float:
    return round(v, 3)


def gather(manifest: dict) -> list[dict]:
    pads = []
    for pg in manifest["pages"]:
        sides = (("conn",)) if pg["kind"] == "data" else ("conn", "conn2")
        for side in sides:
            for pol in ("P", "N"):
                a = pg["anchors"][side][pol]
                pads.append({"ref": a["ref"], "x": r3(a["pad_global"][0]),
                             "y": r3(a["pad_global"][1]), "net": a["net"],
                             "pol": pol, "kind": "data" if pg["kind"] == "data"
                             else "refclk"})
    return pads


def expected_gaps(cols: list[float], w: float, need: float, clr: float,
                  via_od: float) -> dict:
    gaps = [(r3(cols[0] - (w / 2 + clr + via_od / 2)), "left", [None, cols[0]],
             True)]
    for a, b in zip(cols, cols[1:]):
        gapw = round((b - a) - w, 3)
        gaps.append((r3((a + b) / 2), "between", [a, b], gapw >= need - 1e-9))
    gaps.append((r3(cols[-1] + (w / 2 + clr + via_od / 2)), "right",
                 [cols[-1], None], True))
    return {c: [(g[0], g[3]) for g in gaps if c in g[2]] for c in cols}


def main() -> int:
    art = json.load(open(ARTIFACT))
    mf = json.load(open(MANIFEST))
    spec = json.load(open(SPEC))
    rules = json.load(open(RULES))
    via_od = spec["vias"]["std"]["outer"]
    clr = next(nc["clearance"] for nc in rules["clearance"]["net_classes"]
               if nc["name"] == "PCIe85")
    need = via_od + 2 * clr
    req_dy = round(via_od + clr, 3)
    bad = []

    def eq(a, b, tag):
        if a != b:
            bad.append(f"{tag}: {a!r} != {b!r}")

    eq(art["inputs_sha"]["manifest"], sha(MANIFEST), "manifest_sha")
    eq(art["inputs_sha"]["spec"], sha(SPEC), "spec_sha")
    eq(art["inputs_sha"]["rules"], sha(RULES), "rules_sha")
    eq(art["producer"]["generator"]["sha256"], sha(GENERATOR), "producer_sha")

    pads = gather(mf)
    for ref in sorted({p["ref"] for p in pads}):
        rp = [p for p in pads if p["ref"] == ref]
        cols = sorted({p["x"] for p in rp})
        cand = expected_gaps(cols, PAD_W[ref], need, clr, via_od)
        for p in rp:
            entry = next(e for c in art["connectors"][ref]["columns"].values()
                         for e in c["entries"]
                         if e["net"] == p["net"] and e["kind"] == p["kind"])
            eq(entry["gap_candidates"],
               [gx for gx, ok in cand[p["x"]] if ok],
               f"{ref}:{p['net']}:gap_candidates")

    # conservation: each pad exactly once, all with >=1 candidate
    all_entries = [e for c in art["connectors"].values()
                   for col in c["columns"].values() for e in col["entries"]]
    eq(len(all_entries), len(pads), "entry_count")
    eq(art["conservation"]["n_pads"], len(pads), "conservation_n_pads")
    eq(art["conservation"]["n_without_candidate"], 0, "conservation_violations")
    eq(art["conservation"]["verdict"], "FEASIBLE", "conservation_verdict")

    # conflict graph: re-derive independently
    exp_edges = set()
    for ref in sorted({p["ref"] for p in pads}):
        rp = [p for p in pads if p["ref"] == ref]
        cols = sorted({p["x"] for p in rp})
        cand = expected_gaps(cols, PAD_W[ref], need, clr, via_od)
        for gx, ok in {g for gs in cand.values() for g in gs}:
            if not ok:
                continue
            members = [p for p in rp if gx in [g for g, _ in cand[p["x"]]]]
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    if abs(members[i]["y"] - members[j]["y"]) < req_dy - 1e-9:
                        exp_edges.add((gx, tuple(sorted(
                            (members[i]["net"], members[j]["net"])))))
    got_edges = {(e["gap_x"], tuple(sorted((e["pad_a"], e["pad_b"]))))
                 for e in art["conflict_graph"]["edges"]}
    eq(got_edges, exp_edges, "conflict_edges")
    eq(art["conflict_graph"]["required_mm"], req_dy, "required_dy")

    # REFCLK presence
    eq(len(art["refclk_pads"]), sum(1 for p in pads if p["kind"] == "refclk"),
       "refclk_count")
    eq({p["net"] for p in art["refclk_pads"]},
       {p["net"] for p in pads if p["kind"] == "refclk"}, "refclk_nets")

    # no allocation / W3 selection
    forbidden = {"selected", "assigned", "allocation", "lane", "track_y"}
    leaked = [k for k in forbidden if k in json.dumps(art)]

    ok = not bad and not leaked
    print("FAIL" if not ok else "PASS",
          "| checks:", "all" if ok else f"{len(bad)} mismatches, leak={leaked}")
    for b in bad[:20]:
        print("  ", b)
    if leaked:
        print("   forbidden key leaked:", leaked)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
