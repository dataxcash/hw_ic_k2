#!/usr/bin/env python3
"""k2_reroute_exam_v1.py --- #K2-356 sec.2: the RIP-UP & REROUTE ENGINE EXAM (criteria first).

The supervisor ordered: criteria first, and "if the engine cannot pass, no board work" ("考不过禁上板").
This tool IS the machine judge for the two standard exams (sec.2.2):

  EXAM A : lift the left cluster U1/U2/U4/U5 by 5 mm -> engine re-routes
  EXAM B : land the H4 hole exactly in its corner -> local rip-up & reroute

Both are graded by the SAME five machine criteria (sec.2.1/2.2), each binary:
  C1 connectivity        : kicad-cli DRC unconnected_items == 0   (machine proxy for "16/16 fully connected")
  C2 DRC no new increase : total <= reference total AND no class present above the reference class set
  C3 skew                : max per-pair copper-length skew <= 0.15 mm   (project intra_pair_skew_mm)
  C4 chamfer preserved   : count of 45-degree segments >= reference count (the 166 accepted chamfers)
  C5 routing changed     : segment-level set difference vs the reference is NON-ZERO (a no-op is not a re-route)
Verdict = PASS iff all five hold.  A criterion that cannot fail cannot grade, so the tool is exercised below on
both a passing reference (self-grade) and the two recorded FAILED attempts.

CLI: python3 tools/k2_reroute_exam_v1.py --board <pcb> --drc <json> --ref <pcb> --ref-drc <json> --out <json>
"""
from __future__ import annotations
import argparse, collections, json, math, os, sys

PAIRS = [(k, "PCIE_DN%d_N" % k, "PCIE_DN%d_P" % k) for k in range(8)]
SKEW_MAX = 0.15


def load_drc_classes(p):
    d = json.load(open(p, encoding="utf-8"))
    c = collections.Counter(v.get("type") for v in d.get("violations", []))
    return {"total": sum(c.values()), "classes": dict(c),
            "unconnected": len(d.get("unconnected_items", [])),
            "schematic_parity": len(d.get("schematic_parity", []))}


def geometry(path):
    import pcbnew as P
    b = P.LoadBoard(path)
    nets = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    lens = collections.defaultdict(float)
    chamfer = 0
    elems = collections.Counter()
    for t in b.GetTracks():
        nm = nets.get(t.GetNetCode(), "")
        if nm[:4] == "PCIE":
            lens[nm] += P.ToMM(t.GetLength())
        if t.GetClass() == "PCB_VIA":
            x, y = P.ToMM(t.GetPosition().x), P.ToMM(t.GetPosition().y)
            elems[(nm, "VIA", round(x, 3), round(y, 3))] += 1
            continue
        s, e = t.GetStart(), t.GetEnd()
        ax, ay, bx, by = P.ToMM(s.x), P.ToMM(s.y), P.ToMM(e.x), P.ToMM(e.y)
        dx, dy = abs(bx - ax), abs(by - ay)
        if dx > 0.01 and dy > 0.01 and abs(dx - dy) < 0.005:
            chamfer += 1
        elems[(nm, t.GetLayerName(), round(ax, 3), round(ay, 3), round(bx, 3), round(by, 3))] += 1
    return {"lens": dict(lens), "chamfer_45deg": chamfer, "elems": elems}


def grade(board, drc, ref, ref_drc):
    d, r = load_drc_classes(drc), load_drc_classes(ref_drc)
    g, gr = geometry(board), geometry(ref)
    new_classes = sorted(k for k in d["classes"] if k not in r["classes"])
    skews = {}
    for tag, n, p in PAIRS:
        if g["lens"].get(n) and g["lens"].get(p):
            skews[tag] = round(abs(g["lens"][n] - g["lens"][p]), 6)
    max_skew = max(skews.values()) if skews else None
    only_res = [k for k in g["elems"] if k not in gr["elems"]]
    only_ref = [k for k in gr["elems"] if k not in g["elems"]]
    c = {
        "C1_connectivity": {"unconnected": d["unconnected"], "pass": d["unconnected"] == 0},
        "C2_drc_no_new_increase": {"total": d["total"], "ref_total": r["total"],
                                   "new_classes": new_classes,
                                   "pass": d["total"] <= r["total"] and not new_classes},
        "C3_skew": {"per_pair_mm": skews, "max_mm": max_skew, "limit_mm": SKEW_MAX,
                    "pass": (max_skew is not None and max_skew <= SKEW_MAX)},
        "C4_chamfer_preserved": {"count": g["chamfer_45deg"], "ref_count": gr["chamfer_45deg"],
                                 "pass": g["chamfer_45deg"] >= gr["chamfer_45deg"]},
        "C5_routing_changed": {"elements_only_in_result": len(only_res), "only_in_ref": len(only_ref),
                              "pass": (len(only_res) + len(only_ref)) > 0},
    }
    return {"board": board, "ref": ref, "criteria": c,
            "verdict": "PASS" if all(v["pass"] for v in c.values()) else "FAIL"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True); ap.add_argument("--drc", required=True)
    ap.add_argument("--ref", required=True); ap.add_argument("--ref-drc", required=True)
    ap.add_argument("--exam", default="A/B (same five criteria)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    rep = {"artifact": "k2_reroute_exam_v1", "ts": "2026-09-28", "exam": a.exam,
           "authority": "#K2-356 sec.2 (rip-up & reroute engine, criteria first, fail => no board work)",
           "criteria_source": "sec.2.1/2.2; skew limit = project intra_pair_skew_mm",
           "note": "C1 is the machine proxy for '16/16 fully connected' (kicad-cli unconnected == 0)",
           "result": grade(a.board, a.drc, a.ref, a.ref_drc), "OWNER-ITEMS": 0}
    print(json.dumps(rep["result"], ensure_ascii=False, indent=1))
    if a.out:
        json.dump(rep, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0 if rep["result"]["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
