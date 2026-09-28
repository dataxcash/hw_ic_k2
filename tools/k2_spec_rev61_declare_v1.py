#!/usr/bin/env python3
"""k2_spec_rev61_declare_v1.py --- #K2-340 sec.4 + sec.2: declare SPEC rev-61.

Leaves: H1 -> bottom-left corner, H2 -> top-right corner (each WITH its keepout square, atomic; this also repairs
H2's stale keepout square).  Provenance card records the FULL chain of the local-edit boards (source edit ->
C17 v1 re-route -> DRC) as ordered by #K2-340 sec.2.1, and names the H4 blocker with its numbers.
"""
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L3 = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4", "L3")
H1 = {"ref": "H1", "old": [26.1, 75.6], "new": [25.0713, 76.9287]}
H2 = {"ref": "H2", "old": [136.6, 35.1], "new": [140.9287, 35.0713]}
KO_HALF = 3.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.join(L3, "SPEC_k2_v4.spec-rev-60.json"))
    ap.add_argument("--out", default=os.path.join(L3, "SPEC_k2_v4.spec-rev-61.json"))
    a = ap.parse_args()
    s = json.load(open(a.src, encoding="utf-8"))
    leaf = {}
    for H in (H1, H2):
        for h in s["mounting_holes"]["holes"]:
            if h["ref"] == H["ref"]:
                leaf["mounting_holes.holes[%s].at" % H["ref"]] = {"old": list(h["at"]), "new": list(H["new"])}
                h["at"] = list(H["new"])
                oldbb = list(h["keepout_bbox"])
                h["keepout_bbox"] = [round(H["new"][0] - KO_HALF, 3), round(H["new"][1] - KO_HALF, 3),
                                     round(H["new"][0] + KO_HALF, 3), round(H["new"][1] + KO_HALF, 3)]
                leaf["mounting_holes.holes[%s].keepout_bbox" % H["ref"]] = {"old": oldbb, "new": list(h["keepout_bbox"])}
        for z in s["keepout_geometry"]["zones"]:
            if z["name"] == "K2_HOLE_KEEPOUT_%s" % H["ref"]:
                pts = [(float(p[0]), float(p[1])) for p in z["pts"]]
                cx = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2.0
                cy = (min(p[1] for p in pts) + max(p[1] for p in pts)) / 2.0
                dx, dy = H["new"][0] - cx, H["new"][1] - cy
                z["pts"] = [["%.6f" % (float(p[0]) + dx), "%.6f" % (float(p[1]) + dy)] for p in z["pts"]]
                leaf["keepout_geometry.zones[K2_HOLE_KEEPOUT_%s].pts" % H["ref"]] = {
                    "old_centre": [round(cx, 3), round(cy, 3)], "new_centre": list(H["new"]),
                    "translation": [round(dx, 3), round(dy, 3)],
                    "note": "RE-CENTRED on the hole: this also repairs the stale square (M-ENG-HOLE-KEEPOUT-STALE)"}
                break
    s["_spec_rev_61"] = {
        "card": "SPEC-REV-61（H1/H2 落四角 ＋ 禁区随动补正 ＋ l13/l14 溯源卡）",
        "at": "2026-09-28",
        "authority": "#K2-340 sec.4 (same treatment for the remaining holes) + sec.2.1 (provenance card)",
        "leaf_diff": leaf,
        "rule_basis": {"H1/H2": "#K2-322 sec.3.1 corner rule (corner_max 3.0) + SPEC constraints.edge_copper_min; "
                                  "inset = 3.0/sqrt(2) = 2.1213 mm; TI EVM NOT cited (#K2-339 sec.2.3)"},
        "board_provenance": {
            "l13 (accepted by #K2-340)": {
                "kind": "LOCAL EDIT (not a full chain rerun) - shortening approved by #K2-340 sec.2.1",
                "chain": ["hole move + keepout move (tools/k2_apply_hole_relocation_v1.py)",
                          "C17 v1 re-route of J12's nets (tools/k2_reroute_affected_v2.py: clip rip-up -> local "
                          "island-MST stitch with the in-register exact gate at a 0.20 mm clearance floor -> "
                          "maze-router fallback -> snap -> bounded DRC-verified repair -> normalize)",
                          "zone refill (k2_p4_mroute_v1.py --fill)",
                          "kicad-cli DRC 168 vs 170 baseline, no type increased, unconnected 0"],
                "why_not_chain_rerun": "the chain HS router is placement-independent (#K2-332 machine-proved): a rerun "
                                       "yields a ZERO routing diff and destroys the accepted chamfer/equalisation. "
                                       "Chain source IS updated (PLACEMENT_SOLUTION refs.J12, project.yaml).",
                "hs_inheritance": "HS copper segment-for-segment identical to l12 (1974 segs, 678 45-degree segs) -> "
                                  "chamfer 166 + 8/8 equalisation provably inherited"},
            "l14 (this rev)": {
                "chain": ["H1 + H2 hole/keepout atomic moves (tools/k2_apply_hole_relocation_v1.py)",
                          "zone refill", "kicad-cli DRC 168, no type increased, unconnected 0"],
                "no_reroute_needed": "both new corner keepout squares were copper-free (machine-checked before the move)"}},
        "H4_blocker": {
            "id": "NAMED-BLOCKER-H4-CORNER",
            "position": [140.8, 76.8], "corner_dist_mm": 3.18, "rule": 3.0,
            "why": "the bottom-right corner keepout square [137.93,73.93,143.93,79.93] traps 2 high-speed vias plus "
                   "4 track pieces of PCIE_DN4_N / PCIE_DN5_P (the MCIO fan-out runs on In5, ~48 mm long).",
            "attempts": [{"method": "rect-clip + C17 v1 (6x6 square)", "result": "unconnected 3, dangling +2/+2"},
                         {"method": "rect-clip + C17 v1 (wider 9x9 corridor)", "result": "unconnected 6, dangling +7/+8"},
                         {"method": "clearance-aware via push (k2_shift_vias_out_of_keepout_v1.py)", "result":
                          "vias move 0.5/0.6 mm but the re-attached segments then violate clearance (53) + shorting (2)"}],
            "fix_options": ["(i) rip the whole two runs and re-route them with the maze router in a dedicated pass "
                            "(needs a stronger re-route mode = a capability step)",
                            "(ii) owner-declared deviation: H4 stays at 3.18 mm (6% over the rule) while the other "
                            "three corners are exactly on it",
                            "(iii) leave H4's stale keepout square as-is until (i) - it is already registered"]},
        "rollback": "restore project.yaml spec_name=SPEC_k2_v4.spec-rev-60.json and board_path=hw/k2_v4_8L.l13.kicad_pcb; "
                    "l13/l12 are untouched.",
    }
    json.dump(s, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"wrote": a.out, "leaves": sorted(leaf.keys())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
