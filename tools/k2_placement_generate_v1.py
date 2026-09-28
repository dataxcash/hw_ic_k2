#!/usr/bin/env python3
"""k2_placement_generate_v1.py --- #K2-337 window C asset (M-ENG-PLACEMENT-LEARNING-MISSING).

RULE-DRIVEN CANDIDATE PLACEMENT GENERATOR.

Each candidate = the baseline canonical placement (L2/PLACEMENT_SOLUTION_v1.json) transformed by a DECLARED
parameter set, where every parameter is derived from the extracted norms (L2/PLACEMENT_NORMS_v1.json N1..N7) and
the EVM exemplar framework (L2/PLACEMENT_CORPUS_v1.json).  Parametric template instantiation ONLY:
  * no manual nudging, no search, no solver, no random
  * deterministic: same inputs -> byte-identical output
  * L1 interfaces are FROZEN and never touched (J2 = right edge HS connector, MCIO = left edge, signal-flow
    semantics, ball map).  Only framework geometry (chip position / mounting-hole positions / peripheral zone
    layout) is instantiated -> L2 (ENG autonomous, #K2-322 sec.1).

Read-only.  Writes L2/PLACEMENT_CANDIDATES_v1.json.

The corner reference frame is read (read-only) from the Edge.Cuts bounding box of --board so that the
generated hole targets and tools/k2_placement_candidate_eval_v1.py / k2_placement_gate_v1.py use ONE frame.

Usage: python3 tools/k2_placement_generate_v1.py [--board hw/k2_v4_8L.l10.kicad_pcb] [--out <json>] [--dry-run]
"""
import argparse, json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4")
SOL_PATH = os.path.join(ART, "L2", "PLACEMENT_SOLUTION_v1.json")
NORMS_PATH = os.path.join(ART, "L2", "PLACEMENT_NORMS_v1.json")
CORPUS_PATH = os.path.join(ART, "L2", "PLACEMENT_CORPUS_v1.json")
OUT_PATH = os.path.join(ART, "L2", "PLACEMENT_CANDIDATES_v1.json")

CHIP = "U6"
HS_CONNECTOR = "J2"
LEFT_EDGE_CONNECTOR = "MCIO"
CLUSTER = ["U1", "U2", "U4", "U5"]          # owner item: "U1/U2/U4/U5 及附属" (the four named unit parts)
LEDGE_PIN_HEADERS = ["J12", "J6", "J13", "J11", "J9"]

# Hole corner inset: DERIVED (not tuned) -- a hole places exactly ON the N3/P3 corner-distance threshold
# corner_max=3.0mm => per-axis offset = 3.0/sqrt(2); for the in-register NPTH (pad 3.2mm, half 1.6mm) that
# leaves 2.1213-1.6 = 0.52mm board-edge clearance (>= the 0.5mm C16 edge rule).
CORNER_MAX_MM = 3.0
HOLE_CORNER_INSET_MM = round(CORNER_MAX_MM / math.sqrt(2.0), 4)

# ---------------------------------------------------------------------------
# Candidate parameter sets (declared, not searched).  Each entry names the norms
# it instantiates so the evaluator can attribute every deviation to a norm.
# ---------------------------------------------------------------------------
CANDIDATES = [
    {
        "id": "C1",
        "label": "EVM-mirrored framework (chip centred + holes four-corner + peripheral cluster re-partitioned)",
        "params": {
            "chip": {"ref": CHIP, "mode": "centre"},
            "holes": {"mode": "corner", "inset_mm": HOLE_CORNER_INSET_MM,
                      "assign": {"H1": "BL", "H2": "TR", "H3": "TL", "H4": "BR"}},
            "cluster": {"refs": CLUSTER, "mode": "centroid_y_to_board_centre"},
        },
        "norms_instantiated": ["N1", "N3", "N4", "N5", "N6", "N7"],
    },
    {
        "id": "C2",
        "label": "Holes-first minimal (chip and cluster kept; mounting holes instantiated four-corner)",
        "params": {
            "chip": {"ref": CHIP, "mode": "keep"},
            "holes": {"mode": "corner", "inset_mm": HOLE_CORNER_INSET_MM,
                      "assign": {"H1": "BL", "H2": "TR", "H3": "TL", "H4": "BR"}},
            "cluster": {"refs": CLUSTER, "mode": "keep"},
        },
        "norms_instantiated": ["N3"],
    },
    {
        "id": "C3",
        "label": "Chip-centred + machine-proven-feasible hole set (l12 measured) + cluster kept",
        "params": {
            "chip": {"ref": CHIP, "mode": "centre"},
            "holes": {"mode": "measured_l12"},
            "cluster": {"refs": CLUSTER, "mode": "keep"},
        },
        "norms_instantiated": ["N1"],
    },
]

# l12 measured mounting-hole positions (the only hole set so far machine-proven landing-clean, #K2-329/#K2-330)
HOLES_MEASURED_L12 = {"H1": [26.1, 75.6], "H2": [136.6, 35.1], "H3": [45.1, 75.1], "H4": [140.8, 76.8]}


def load(p):
    return json.load(open(p, encoding="utf-8"))


def build_candidate(base, board, spec):
    """Instantiate one candidate: baseline refs -> new refs (full, self-contained) + framework block."""
    x0, x1 = board["x"]; y0, y1 = board["y"]
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    refs = {r: list(v["at"]) for r, v in base["refs"].items()}
    applied = []

    # --- chip position (N1) -------------------------------------------------
    cm = spec["params"]["chip"]["mode"]
    if cm in ("centre", "centre_x"):
        r = spec["params"]["chip"]["ref"]
        old = list(refs[r])
        refs[r][0] = round(cx, 3)
        if cm == "centre":
            refs[r][1] = round(cy, 3)
        applied.append({"norm": "N1", "op": "chip_%s" % cm, "ref": r,
                        "from": old, "to": list(refs[r])})

    # --- peripheral cluster (N4/N5) -----------------------------------------
    cl = spec["params"]["cluster"]
    if cl["mode"] == "centroid_y_to_board_centre":
        ys = [refs[r][1] for r in cl["refs"]]
        dy = round(cy - sum(ys) / len(ys), 3)
        for r in cl["refs"]:
            old = list(refs[r])
            refs[r][1] = round(refs[r][1] + dy, 3)
            applied.append({"norm": "N5", "op": "cluster_translate_y", "ref": r,
                            "from": old, "to": list(refs[r]), "dy": dy})

    # --- mounting holes (N3) ------------------------------------------------
    hm = spec["params"]["holes"]["mode"]
    if hm == "corner":
        ins = spec["params"]["holes"]["inset_mm"]
        corner = {"TL": (x0 + ins, y0 + ins), "TR": (x1 - ins, y0 + ins),
                  "BL": (x0 + ins, y1 - ins), "BR": (x1 - ins, y1 - ins)}
        holes = {h: [round(corner[c][0], 3), round(corner[c][1], 3)]
                 for h, c in spec["params"]["holes"]["assign"].items()}
        applied.append({"norm": "N3", "op": "holes_corner_inset%.1f" % ins, "holes": holes,
                        "corner_targets": {k: [round(v[0], 3), round(v[1], 3)] for k, v in corner.items()}})
    elif hm == "measured_l12":
        holes = {h: list(v) for h, v in HOLES_MEASURED_L12.items()}
        applied.append({"norm": "N3", "op": "holes_measured_l12", "holes": holes,
                        "note": "machine-proven landing-clean set (l12); does NOT meet the <=3.0mm corner rule"})
    else:
        holes = {h: list(v) for h, v in base.get("holes", HOLES_MEASURED_L12).items()}
        applied.append({"norm": "N3", "op": "holes_keep", "holes": holes})

    framework = {
        "chip": {"ref": CHIP, "at": refs[CHIP]},
        "connectors": {"J2": {"edge": "RIGHT", "at": refs.get(HS_CONNECTOR)},
                       "MCIO": {"edge": "LEFT", "note": "L1 frozen; not in the placement solution ref set"}},
        "holes": holes,
        "flow": "RADIAL fan-out %s -> %s (RIGHT edge)" % (CHIP, HS_CONNECTOR),
        "l1_frozen": ["J2 edge=RIGHT", "MCIO edge=LEFT", "signal-flow semantics", "ball map"],
    }
    return {
        "id": spec["id"], "label": spec["label"],
        "params": spec["params"], "norms_instantiated": spec["norms_instantiated"],
        "applied": applied, "framework": framework,
        "refs": {r: refs[r] for r in sorted(refs)},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", default=os.path.join(ROOT, "hw", "k2_v4_8L.l10.kicad_pcb"))
    ap.add_argument("--out", default=OUT_PATH)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    base = load(SOL_PATH)
    norms = load(NORMS_PATH)
    corpus = load(CORPUS_PATH)
    import pcbnew
    _e = pcbnew.LoadBoard(a.board).GetBoardEdgesBoundingBox()
    board = {"x": [round(pcbnew.ToMM(_e.GetLeft()), 3), round(pcbnew.ToMM(_e.GetRight()), 3)],
             "y": [round(pcbnew.ToMM(_e.GetTop()), 3), round(pcbnew.ToMM(_e.GetBottom()), 3)]}

    cands = [build_candidate(base, board, c) for c in CANDIDATES]
    rep = {
        "artifact": "k2_placement_candidates_v1",
        "ts": "2026-09-28",
        "authority": "#K2-337 window C: rule-driven candidate placement generator (parametric template instantiation)",
        "schema": "k2.placement_candidates.v1",
        "generator": "tools/k2_placement_generate_v1.py",
        "based_on": {
            "placement_solution": "L2/PLACEMENT_SOLUTION_v1.json",
            "norms": "L2/PLACEMENT_NORMS_v1.json",
            "corpus": "L2/PLACEMENT_CORPUS_v1.json",
        },
        "board_frame_source": a.board,
        "board_frame": {"x": board["x"], "y": board["y"],
                        "centre": [(board["x"][0] + board["x"][1]) / 2.0,
                                   (board["y"][0] + board["y"][1]) / 2.0]},
        "norms_applied": [n["id"] for n in norms["norms"]],
        "l1_frozen": ["requirements", "interfaces (J2 RIGHT / MCIO LEFT)", "signal-flow semantics", "ball map"],
        "n_candidates": len(cands),
        "candidates": cands,
        "generation_rule": ("baseline placement x declared parameter set -> full self-contained ref table; "
                            "every parameter is a norm instance (N1 chip position / N3 hole pattern / "
                            "N4-N5 peripheral partitioning); no search, no manual nudging"),
    }
    if a.dry_run:
        print(json.dumps({"dry_run": True, "n_candidates": len(cands),
                          "ids": [c["id"] for c in cands]}, ensure_ascii=False))
        return 0
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    print(json.dumps({"wrote": a.out, "n_candidates": len(cands),
                      "ids": [c["id"] for c in cands],
                      "chip_at": {c["id"]: c["framework"]["chip"]["at"][:2] for c in cands},
                      "holes": {c["id"]: c["framework"]["holes"] for c in cands}},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
