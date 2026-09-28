#!/usr/bin/env python3
"""k2_spec_rev62_declare_v1.py --- #K2-351 sec.4(b): declare SPEC rev-62 (H4 leaf ONLY).

Leaf: H4 -> the bottom-right corner, WITH its keepout square/circle moved atomically. The H4 keepout in rev-61 was
STALE (square [111.6,33.1,117.6,39.1], i.e. a 6x6 centred on 114.6,36.1), so this edit also repairs
M-ENG-HOLE-KEEPOUT-STALE for H4 (H2 was repaired by rev-61).
No other leaf is touched: J9/J6/J11 header leaves stay OUT (their governance needs a schematic instance and is NOT on
the H4 critical path). New file only: the frozen base SPEC_k2_v4.json is byte-untouched.
"""
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L3 = os.path.join(ROOT, "pm_gate", "artifacts", "k2_v4", "L3")
H4 = {"ref": "H4", "old_at": [140.8, 76.8], "new_at": [140.9287, 76.9287]}
KO_HALF = 3.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.join(L3, "SPEC_k2_v4.spec-rev-61.json"))
    ap.add_argument("--out", default=os.path.join(L3, "SPEC_k2_v4.spec-rev-62.json"))
    a = ap.parse_args()
    s = json.load(open(a.src, encoding="utf-8"))
    leaf = {}
    for h in s["mounting_holes"]["holes"]:
        if h["ref"] != "H4":
            continue
        leaf["mounting_holes.holes[H4].at"] = {"old": list(h["at"]), "new": list(H4["new_at"])}
        h["at"] = list(H4["new_at"])
        oldbb = list(h["keepout_bbox"])
        h["keepout_bbox"] = [round(H4["new_at"][0] - KO_HALF, 3), round(H4["new_at"][1] - KO_HALF, 3),
                             round(H4["new_at"][0] + KO_HALF, 3), round(H4["new_at"][1] + KO_HALF, 3)]
        leaf["mounting_holes.holes[H4].keepout_bbox"] = {"old": oldbb, "new": list(h["keepout_bbox"]),
                                                         "note": "repairs the stale square (M-ENG-HOLE-KEEPOUT-STALE, H4 arm)"}
    for z in s["keepout_geometry"]["zones"]:
        if z["name"] == "K2_HOLE_KEEPOUT_H4":
            pts = [(float(p[0]), float(p[1])) for p in z["pts"]]
            cx = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2.0
            cy = (min(p[1] for p in pts) + max(p[1] for p in pts)) / 2.0
            dx, dy = H4["new_at"][0] - cx, H4["new_at"][1] - cy
            z["pts"] = [["%.6f" % (float(p[0]) + dx), "%.6f" % (float(p[1]) + dy)] for p in z["pts"]]
            leaf["keepout_geometry.zones[K2_HOLE_KEEPOUT_H4].pts"] = {
                "old_centre": [round(cx, 3), round(cy, 3)], "new_centre": list(H4["new_at"]),
                "translation": [round(dx, 3), round(dy, 3)], "n_pts": len(z["pts"]),
                "note": "RE-CENTRED on the hole (radius 3.0 polygon, 36 pts): atomic with the hole move"}
            break
    if len(leaf) != 3:
        raise SystemExit("expected exactly 3 leaves, got %d: %s" % (len(leaf), sorted(leaf)))
    s["_spec_rev_62"] = {
        "card": "SPEC-REV-62（仅 H4 leaf：落四角 ＋ 禁区原子随动 ＋ 补 stale）",
        "at": "2026-09-28",
        "authority": "#K2-351 sec.4(b) (bounded window: re-emit -> rev-62 -> chain rerun once -> judge once)",
        "leaf_diff": leaf,
        "scope": {"in": ["mounting_holes.holes[H4] (at + keepout_bbox)", "keepout_geometry.zones[K2_HOLE_KEEPOUT_H4].pts"],
                  "out": ["J9 / J6 / J11 header leaves (schematic-gated, NOT on the H4 critical path)",
                          "every other leaf is byte-identical to rev-61"]},
        "lane_plan_reemission": {
            "required_because": "R912 machine-proof: the H4 intruding copper is the DN4/DN5 'input' lane-plan detour "
                                "plus its landing column inside m13_v57_w3_joint_assignment.json; k2_gen_v5.py emits no "
                                "DN geometry and stage 2a copies the drawing verbatim, so a chain rerun with an "
                                "unchanged drawing reproduces the identical fan (W2PRIME_EXECUTION_SPEC_v1 E5 premise is "
                                "false for the DN fan).",
            "hard_constraint": "column_x + via_radius(0.175) + margin(0.10) <= 137.9287  =>  column_x <= 137.6537",
            "artifact": "pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/m13_v57_w3_joint_assignment_H4CLEAR_v1.json",
            "consumer": "tools/p3_v57_l4_apply_drawing.py honors L4_MAIN, so stage 2a reads the re-emitted drawing "
                        "without overwriting the canonical one",
            "length_closure": "per pair the re-emission restores ideal_len(N) == ideal_len(P) exactly by shrinking the "
                              "serpentine amplitude of the pad-east polarity lane (see the re-emission tool's card)."},
        "rollback": "restore project.yaml spec_name=SPEC_k2_v4.spec-rev-61.json and "
                    "board_path=hw/k2_v4_8L.l14.kicad_pcb; l14 and every earlier board are untouched; the canonical "
                    "drawing is untouched (a chain rerun without L4_MAIN reproduces the l14-generation fan).",
    }
    json.dump(s, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"wrote": a.out, "leaves": sorted(leaf.keys())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
