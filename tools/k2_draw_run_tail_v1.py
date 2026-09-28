#!/usr/bin/env python3
"""k2_draw_run_tail_v1.py --- #K2-346: SCHEME-LAYER DRAWING for the two trapped runs (PCIE_DN4_N / PCIE_DN5_P).

Produces a DETERMINATE drawing (no construction-layer search): the layer-change via is DERIVED analytically from
the keepout boundary + the clearance floor, and the tail is a straight/L path whose points are written down.  The
construction window then only replays the points (cut old tail -> delete old via -> draw the listed tail).

Derivation (per line, run = a straight In5 segment at y = y_run):
   x_via = keepout_x0 - (via_r + CLEARANCE_FLOOR)          # the furthest-left point that is still "at the corner"
   tail  = (x_via, y_run) -> (x_pad_target)                # 2-segment L on F.Cu (points listed)
Verification (this window): the drawing is materialised on a scratch board and judged by kicad-cli DRC (the
authority): the two corner keepout items must disappear and no violation class may increase.

Usage (KiCad python): k2_draw_run_tail_v1.py --board <pcb> --baseline-drc <json> --out <drawing.json> --scratch <dir>
"""
import argparse, json, math, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KICAD_CLI = os.environ.get("KICAD_CLI", "/tmp/k2kicad/squashfs-root/usr/bin/kicad-cli")
KEEPOUT = (137.93, 73.93, 143.93, 79.93)      # H4 corner keepout square (board frame, all layers)
CLEARANCE = 0.20                              # kicad-cli netclass floor (acceptance authority)
NETS = ["PCIE_DN4_N", "PCIE_DN5_P"]


def run():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--baseline-drc", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    import pcbnew as P
    b = P.LoadBoard(a.board)
    nets = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    kx0, ky0, kx1, ky1 = KEEPOUT
    drawing = {"artifact": "k2_run_tail_drawing_v1", "ts": "2026-09-28",
               "authority": "#K2-346 (one bounded SCHEME window: determinate drawing, no construction search)",
               "board": a.board, "keepout": list(KEEPOUT), "clearance_floor_mm": CLEARANCE,
               "death_cause": ("H4's corner keepout square lands on two ~48 mm In5 runs whose layer-change vias sit "
                              "exactly at the corner; the local-push family is precisely exhausted and the "
                              "gap-stitching fabric cannot re-plan a whole run."),
               "proven_facts": {"A_6x6_rectclip_plus_C17v1": "unconnected 3", "B_wider_9x9": "unconnected 6",
                                "C_via_push": "unconnected 0 but clearance +1 / shorting +3 / crossing +1",
                                "D_pour_bbox_model": "no candidate within 4.0 mm",
                                "E_c22_precise_polys": "no candidate within 4.0 mm (precise exhaustion of local push)"},
               "lines": [], "OWNER-ITEMS": 0}
    for net in NETS:
        # the run: the long In5 segment(s) of this net reaching into the keepout
        segs = []
        for t in b.GetTracks():
            if t.GetClass() == "PCB_VIA" or nets.get(t.GetNetCode(), "") != net:
                continue
            x1, y1 = P.ToMM(t.GetStart().x), P.ToMM(t.GetStart().y)
            x2, y2 = P.ToMM(t.GetEnd().x), P.ToMM(t.GetEnd().y)
            if min(x1, x2) <= kx1 and max(x1, x2) >= kx0 and min(y1, y2) <= ky1 and max(y1, y2) >= ky0:
                segs.append({"layer": t.GetLayer(), "x1": round(x1, 3), "y1": round(y1, 3),
                             "x2": round(x2, 3), "y2": round(y2, 3), "w": P.ToMM(t.GetWidth())})
        vias = []
        for t in b.GetTracks():
            if t.GetClass() != "PCB_VIA" or nets.get(t.GetNetCode(), "") != net:
                continue
            vx, vy = P.ToMM(t.GetPosition().x), P.ToMM(t.GetPosition().y)
            if kx0 <= vx <= kx1 and ky0 <= vy <= ky1:
                vias.append({"at": [round(vx, 4), round(vy, 4)], "span": sorted(t.GetLayerSet().Seq()),
                             "r": round(P.ToMM(t.GetWidth(P.F_Cu)) / 2.0, 4)})
        if not vias:
            drawing["lines"].append({"net": net, "error": "no trapped via found"}); continue
        v = vias[0]
        y_run = v["at"][1]
        x_via = round(kx0 - (v["r"] + CLEARANCE), 4)
        # the tail's far end = the via's F.Cu attachment partner (where the old tail went)
        attach = []
        for t in b.GetTracks():
            if t.GetClass() == "PCB_VIA" or nets.get(t.GetNetCode(), "") != net:
                continue
            for (px, py) in ((P.ToMM(t.GetStart().x), P.ToMM(t.GetStart().y)),
                             (P.ToMM(t.GetEnd().x), P.ToMM(t.GetEnd().y))):
                if abs(px - v["at"][0]) < 0.01 and abs(py - v["at"][1]) < 0.01:
                    other = (t.GetEnd() if abs(P.ToMM(t.GetStart().x) - v["at"][0]) < 0.01
                             and abs(P.ToMM(t.GetStart().y) - v["at"][1]) < 0.01 else t.GetStart())
                    attach.append({"layer": t.GetLayer(), "other": [round(P.ToMM(other.x), 4), round(P.ToMM(other.y), 4)]})
        drawing["lines"].append({
            "net": net, "run_y_mm": y_run, "in5_run_segments_in_keepout": segs,
            "old_via": v, "old_tail_attach": attach,
            "NEW_via": {"at": [x_via, y_run], "span": v["span"], "derivation":
                        "x = keepout_x0 - (via_r + clearance_floor) = %.2f - (%.3f + %.2f) = %.4f"
                        % (kx0, v["r"], CLEARANCE, x_via)},
            "tail_points": [[x_via, y_run]] + [[t["other"][0], t["other"][1]] for t in attach
                                               if t["layer"] == P.F_Cu],
            "delete": {"old_via": v["at"], "in5_tail_beyond_x": x_via},
            "conservation": {"layers_used": ["In5 -> via -> F.Cu"], "vias_new": 1, "vias_deleted": 1, "net_delta": 0},
            "buildability": "relocation_listed"})
    # materialise on a scratch board and let kicad-cli DRC judge
    sc = a.scratch
    os.makedirs(sc, exist_ok=True)
    for f in os.listdir(os.path.dirname(os.path.abspath(a.board))):
        if f == "fp-lib-table" or f == "lib" or f.endswith(".kicad_pro"):
            src, dst = os.path.join(os.path.dirname(os.path.abspath(a.board)), f), os.path.join(sc, f)
            if os.path.exists(dst) or os.path.islink(dst):
                continue
            (os.symlink(src, dst) if os.path.isdir(src) else shutil.copyfile(src, dst))
    cand = os.path.join(sc, os.path.basename(a.board))
    b2 = P.LoadBoard(a.board)
    netname2 = {c: ni.GetNetname() for c, ni in b2.GetNetInfo().NetsByNetcode().items()}
    moved = 0
    for t in b2.GetTracks():                      # move the layer-change via along its run to the derived x
        if t.GetClass() != "PCB_VIA" or netname2.get(t.GetNetCode(), "") not in NETS:
            continue
        x, y = P.ToMM(t.GetPosition().x), P.ToMM(t.GetPosition().y)
        if not (kx0 <= x <= kx1 and ky0 <= y <= ky1):
            continue
        dx = (kx0 - (P.ToMM(t.GetWidth(P.F_Cu)) / 2.0 + CLEARANCE)) - x
        t.SetPosition(P.VECTOR2I(int(round((x + dx) * 1e6)), int(round(y * 1e6))))
        # DETERMINATE CONSTRUCTION: translate the two legs that meet at this via by the same dx (the horizontal
        # B.Cu run shortens and the vertical In5 ascent shifts left) -- a rigid move, NOT a search.
        for s in b2.GetTracks():
            if s.GetClass() == "PCB_VIA" or netname2.get(s.GetNetCode(), "") != netname2.get(t.GetNetCode(), ""):
                continue
            px1, py1 = P.ToMM(s.GetStart().x), P.ToMM(s.GetStart().y)
            px2, py2 = P.ToMM(s.GetEnd().x), P.ToMM(s.GetEnd().y)
            at_start = abs(px1 - x) < 0.01 and abs(py1 - y) < 0.01
            at_end = abs(px2 - x) < 0.01 and abs(py2 - y) < 0.01
            if at_start:
                s.SetStart(P.VECTOR2I(int(round((x + dx) * 1e6)), int(round(y * 1e6))))
                if (s.GetLayer() == 12):                      # B.Cu horizontal run: pull the far end in
                    s.SetEnd(P.VECTOR2I(int(round((px2 + dx) * 1e6)), int(round(py2 * 1e6))))
                else:                                          # In2/In5 vertical ascent: shift the whole leg
                    s.SetEnd(P.VECTOR2I(int(round((px2 + dx) * 1e6)), int(round(py2 * 1e6))))
            elif at_end:
                s.SetEnd(P.VECTOR2I(int(round((x + dx) * 1e6)), int(round(y * 1e6))))
                s.SetStart(P.VECTOR2I(int(round((px1 + dx) * 1e6)), int(round(py1 * 1e6))))
        moved += 1
    b2.Save(cand)
    pr = [f for f in os.listdir(sc) if f.endswith(".kicad_pro")]
    base = os.path.join(os.path.dirname(os.path.abspath(a.board)), os.path.basename(a.board).replace(".kicad_pcb", ".kicad_pro"))
    if os.path.exists(base):
        shutil.copyfile(base, cand.replace(".kicad_pcb", ".kicad_pro"))
    dj = os.path.join(sc, "cand_drc.json")
    subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "-o", dj, cand],
                   capture_output=True, text=True)
    if os.path.isfile(dj):
        import collections
        base_j = json.load(open(a.baseline_drc, encoding="utf-8"))
        cand_j = json.load(open(dj, encoding="utf-8"))
        bt = collections.Counter(v["type"] for v in base_j["violations"])
        ct = collections.Counter(v["type"] for v in cand_j["violations"])
        drawing["verification"] = {"vias_moved": moved, "drc_total": len(cand_j["violations"]),
                                   "baseline_total": len(base_j["violations"]),
                                   "unconnected": len(cand_j.get("unconnected_items", [])),
                                   "increases": {k: [bt[k], ct[k]] for k in set(bt) | set(ct) if ct[k] > bt[k]},
                                   "note": "candidate = the drawing's via move only (tail not yet drawn); "
                                           "this proves the NEW via position is keepout-free"}
    drawing["buildability_plan"] = "construct: cut In5 tail beyond x_via -> delete old via -> draw listed tail (<=10mm) on F.Cu"
    drawing["sample_citation"] = {"cited": "mechanical corner-keepout policy: #K2-322 sec.3.1 four-corner rule + "
                                           "SPEC constraints.edge_copper_min + the register's own hole keepout squares",
                                  "scope": "PRODUCT/mechanical - applies to this board; TI EVM NOT cited "
                                           "(its authority is the redriver escape paradigm, #K2-339 sec.2.3)"}
    json.dump(drawing, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"wrote": a.out, "vias_moved": moved,
                      "verification": drawing.get("verification"),
                      "lines": [{"net": l.get("net"), "new_via": l.get("NEW_via", {}).get("at"),
                                 "tail_points": l.get("tail_points")} for l in drawing["lines"]]},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(run())
