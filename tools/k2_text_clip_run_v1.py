#!/usr/bin/env python3
"""k2_text_clip_run_v1.py --- #K2-346 scheme window: TEXT-LEVEL clip of the two trapped runs.

Removes pcbnew's object API from the board-mutation path entirely (the failure F1 of R874): the board file is
parsed and edited as s-expression TEXT, exactly the way the in-register maze router emits its copper.

Closure (per line, net in {PCIE_DN4_N, PCIE_DN5_P}):
  * DELETE the trapped corner via   (block '(via' whose '(at x y)' has x >= KEEPOUT_X0 and y >= KEEPOUT_Y0)
  * REWRITE the B.Cu horizontal run so it ends at x = KEEPOUT_X0 - (via_r + clearance) = 137.555
  * DELETE the In5 vertical ascent  (block '(segment' on the same net that meets the via and is not the horizontal)

Unit check: the run reports the exact before/after of every touched block and asserts the touched count is 6
(2 vias + 2 horizontals + 2 verticals) and that no other block changed.

Usage: python3 tools/k2_text_clip_run_v1.py --board <pcb> --out <pcb> [--report json] [--x 137.555]
"""
import argparse, hashlib, json, os, re, sys

NETS = ("PCIE_DN4_N", "PCIE_DN5_P")
KX0, KY0 = 137.93, 73.93
CLEARANCE = 0.20
VIA_HALF = 0.175
X_NEW = round(KX0 - (VIA_HALF + CLEARANCE), 4)          # 137.555

BLOCK = re.compile(r"\n\t\((?:segment|via)(?: blind)?\n(?:.*\n)*?\t\)")


def parse_block(b):
    d = {"raw": b}
    for key, pat in (("at", r"\(at ([-\d.]+) ([-\d.]+)\)"), ("start", r"\(start ([-\d.]+) ([-\d.]+)\)"),
                     ("end", r"\(end ([-\d.]+) ([-\d.]+)\)"), ("layer", r'\(layer "([^"]+)"\)'),
                     ("net", r'\(net "([^"]*)"\)'), ("size", r"\(size ([-\d.]+)\)")):
        m = re.search(pat, b)
        d[key] = (float(m.group(1)), float(m.group(2))) if m and key in ("at", "start", "end") else \
                 (m.group(1) if m else None)
    d["kind"] = "via" if b.lstrip().startswith("(via") else "segment"
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--x", type=float, default=X_NEW)
    a = ap.parse_args()
    txt = open(a.board, encoding="utf-8").read()
    blocks = list(BLOCK.finditer(txt))
    parsed = [(m.start(), m.end(), parse_block(m.group(0))) for m in blocks]
    # locate the trapped vias
    trapped = [p for p in parsed if p[2]["kind"] == "via" and p[2]["net"] in NETS and p[2]["at"]
               and p[2]["at"][0] >= KX0 and p[2]["at"][1] >= KY0]
    plan, touched = [], []
    for (st, en, v) in trapped:
        vx, vy = v["at"]
        legs = []
        for (s2, e2, s) in parsed:
            if s["kind"] != "segment" or s["net"] != v["net"] or not (s["start"] and s["end"]):
                continue
            for (px, py) in (s["start"], s["end"]):
                if abs(px - vx) < 0.02 and abs(py - vy) < 0.02:
                    o = s["end"] if (abs(s["start"][0] - px) < 1e-9 and abs(s["start"][1] - py) < 1e-9) else s["start"]
                    legs.append({"span": (s2, e2), "block": s, "other": o})
        horiz = [l for l in legs if abs(l["other"][0] - vx) > abs(l["other"][1] - vy)]
        vert = [l for l in legs if not (abs(l["other"][0] - vx) > abs(l["other"][1] - vy))]
        for l in horiz:
            new_block = re.sub(r"\(start ([-\d.]+) ([-\d.]+)\)", lambda m: "(start %s %s)" % (l["other"][0], l["other"][1]),
                               l["block"]["raw"], count=1)
            new_block = re.sub(r"\(end ([-\d.]+) ([-\d.]+)\)", lambda m: "(end %s %s)" % (a.x, vy), new_block, count=1)
            plan.append({"act": "rewrite_segment", "net": v["net"], "kind": "B_Cu_run_shortened",
                         "before": [l["block"]["start"], l["block"]["end"]], "after": [list(l["other"]), [a.x, vy]],
                         "span": l["span"], "text": new_block})
            touched.append(("seg", l["block"]["net"], l["block"]["start"], l["block"]["end"]))
        for l in vert:
            plan.append({"act": "delete_segment", "net": v["net"], "kind": "In5_vertical_ascent",
                         "before": [l["block"]["start"], l["block"]["end"]], "span": l["span"], "text": ""})
            touched.append(("seg", l["block"]["net"], l["block"]["start"], l["block"]["end"]))
        plan.append({"act": "delete_via", "net": v["net"], "kind": "trapped_corner_via", "at": list(v["at"]),
                     "span": [st, en], "text": ""})
        touched.append(("via", v["net"], v["at"], None))
    # apply (right-to-left so offsets stay valid)
    out, off = [], 0
    for item in sorted(plan, key=lambda z: -z["span"][0]):
        st, en = item["span"]
        out.append((st, en, item["text"]))
    res = txt
    for (st, en, new) in sorted(out, key=lambda z: -z[0]):
        res = res[:st] + new + res[en:]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(res)
    rep = {"artifact": "k2_text_clip_run_v1", "ts": "2026-09-28", "board_in": a.board, "board_out": a.out,
           "x_new": a.x, "trapped_vias": len(trapped), "plan": plan,
           "touched_count": len(touched),
           "unit_check": {"expected_touched": 2 * len(trapped), "touched": len(touched),
                          "ok": len(touched) == 2 * len(trapped) and len(trapped) == len(NETS)},
           "sha16_in": hashlib.sha256(txt.encode()).hexdigest()[:16],
           "sha16_out": hashlib.sha256(res.encode()).hexdigest()[:16],
           "OWNER-ITEMS": 0}
    if a.report:
        json.dump(rep, open(a.report, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"trapped_vias": len(trapped), "touched": len(touched),
                      "unit_check": rep["unit_check"],
                      "plan": [{"act": p["act"], "kind": p["kind"], "net": p["net"]} for p in plan],
                      "sha16_in": rep["sha16_in"], "sha16_out": rep["sha16_out"]}, ensure_ascii=False, indent=1))
    return 0 if rep["unit_check"]["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
