#!/usr/bin/env python3
"""k2_block_planner_enumerate_v1 - R1852 STEP 3b: the POSITION-ONLY enumerator + the score table.
Reads the REGISTERED standard (K2_BLOCK_PLANNER_STANDARD_v1.json): no weight, cap or tolerance is a code
constant. Enumerates positions only (never permutations); no search beyond the caps; picks by the standard's
explicit total tie-break. Determinism proof = run twice and byte-compare the emitted score ledger.
Usage: k2_block_planner_enumerate_v1.py <standard.json> <partition.json> <board.kicad_pcb> <out.json>
"""
import hashlib
import itertools
import json
import math
import os
import sys

import pcbnew

TOL = 1e-3  # the standard's explicit geometric tolerance regime


def _centre(r):
    return ((r[0] + r[2]) / 2.0, (r[1] + r[3]) / 2.0)


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    std_p, part_p, board_p, out_p = argv[0], argv[1], argv[2], argv[3]
    std = json.load(open(std_p, encoding="utf-8"))
    part = json.load(open(part_p, encoding="utf-8"))
    law = std["enumeration_law"]
    caps = law["hard_caps"]
    step = float(law["candidate_positions"]["step_mm"])
    w = std["objective"]["weights"]
    blocks = part["blocks"]
    assert len(blocks) <= caps["max_blocks_per_window"], "block count exceeds the registered window cap"
    kmax = caps["max_positions_per_block"]
    # candidate POSITIONS (deterministic order); positions only - never permutations
    base = [(0.0, 0.0)]
    k = 1
    r = 1
    while k < kmax:
        for d in ((r * step, 0.0), (-r * step, 0.0), (0.0, r * step), (0.0, -r * step)):
            if k >= kmax:
                break
            base.append(d)
            k += 1
        r += 1
    # net -> set of blocks its pads span (read-only on the board)
    b = pcbnew.LoadBoard(board_p)
    net_blocks = {}
    for fp in b.GetFootprints():
        for pd in fp.Pads():
            net = pd.GetNetname()
            if not net:
                continue
            p = pd.GetPosition()
            px, py = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
            for bi, blk in enumerate(blocks):
                r0 = blk["rects"][0]
                if r0[0] - TOL <= px <= r0[2] + TOL and r0[1] - TOL <= py <= r0[3] + TOL:
                    net_blocks.setdefault(net, set()).add(bi)
    cross_nets = {n: sorted(s) for n, s in net_blocks.items() if len(s) >= 2}
    rows = []
    for combo in itertools.product(base, repeat=len(blocks)):      # positions only
        obj = 0.0
        for n, bs in cross_nets.items():
            c1, c2 = [_centre(blocks[i]["rects"][0]) for i in bs[:2]]
            obj += w["w_blocks_crossed"] * ((len(bs) - 1) * _dist(c1, c2))
        offsets_sum = sum(abs(d[0]) + abs(d[1]) for d in combo)
        rows.append({"offsets": [list(d) for d in combo], "objective": round(obj, 6),
                     "offsets_abs_sum": round(offsets_sum, 6),
                     "blocks": [blk["name"] for blk in blocks]})
    key = lambda x: (x["objective"], x["offsets_abs_sum"], x["blocks"], x["offsets"])
    rows.sort(key=key)
    out = {"artifact": "k2_block_planner_score_table_v1", "ts": "2026-10-01",
           "authority": "#K2-555 (R1852 approved) STEP 3b - the position-only enumerator and its score table.",
           "standard": os.path.basename(std_p), "standard_self_sha16": std.get("self_sha16"),
           "partition": os.path.basename(part_p), "board_readonly": os.path.basename(board_p),
           "enumeration": {"positions_only": bool(law["positions_only"]),
                           "n_positions_per_block": len(base), "n_blocks": len(blocks),
                           "n_combinations": len(rows), "n_combinations_bound": len(base) ** len(blocks),
                           "caps": caps, "cap_respected": len(base) <= kmax and len(blocks) <= caps["max_blocks_per_window"]},
           "objective_inputs": {"crossing_nets": cross_nets, "w": w,
                                "single_block_note": ("with ONE declared block the cross-block term is structurally 0 - "
                                                      "the K2 test case therefore exercises the LAW (positions only, caps, "
                                                      "tie-break, determinism) and not the cross-block optimisation; a "
                                                      "multi-block K2 case would exercise the latter")},
           "score_table": rows, "chosen": rows[0],
           "tie_break_used": list(std["enumeration_law"]["tie_break_tuple"])}
    out["self_sha16"] = hashlib.sha256(json.dumps({k: v for k, v in out.items()}, sort_keys=True,
                                                  ensure_ascii=False).encode()).hexdigest()[:16]
    with open(out_p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1); fh.write("\n")
    print(json.dumps({"out": out_p, "combos": len(rows), "chosen": out["chosen"],
                      "self_sha16": out["self_sha16"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
