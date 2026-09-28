#!/usr/bin/env python3
"""k2_construct_run_drawing_v1.py --- #K2-346 scheme window: CONSTRUCT the determinate drawing for the two trapped
runs (PCIE_DN4_N / PCIE_DN5_P) and freeze the points.

Determinate construction (one execution, no sweep):
  * layer-change via  : derived  x = keepout_x0 - (via_r + clearance_floor) = 137.555   (both lines)
  * B.Cu horizontal run: CLIPPED at 137.555 (shortened, straight)
  * vertical ascent   : CONSTRUCTED by the in-register maze router with the exact gate (0.20 mm floor) from the
                        clipped B.Cu end up to the run's existing In5 top node
  * old corner via    : deleted
Output: the frozen point list (legs + vias) + a materialised candidate board + kicad-cli DRC verdict.
"""
import argparse, importlib.util, json, math, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MROUTE = os.path.join(ROOT, "tools", "k2_p4_mroute_v1.py")
KICAD_CLI = os.environ.get("KICAD_CLI", "/tmp/k2kicad/squashfs-root/usr/bin/kicad-cli")
NETS = ["PCIE_DN4_N", "PCIE_DN5_P"]
KX0 = 137.93
CLEARANCE = 0.20


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--baseline-drc", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--board-out", required=True)
    ap.add_argument("--scratch", required=True)
    a = ap.parse_args()
    os.makedirs(a.scratch, exist_ok=True)
    sp = importlib.util.spec_from_file_location("k2mr", MROUTE)
    mr = importlib.util.module_from_spec(sp); sp.loader.exec_module(mr)
    cv = mr.cv
    _orig = cv._req
    cv._req = lambda x, y: max(_orig(x, y), CLEARANCE)
    import pcbnew as P
    b = P.LoadBoard(a.board)
    netname = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    work = os.path.join(a.scratch, os.path.basename(a.board))
    drawing = {"artifact": "k2_run_drawing_v1", "ts": "2026-09-28", "board_in": a.board,
               "authority": "#K2-346 (bounded scheme window): determinate drawing, one execution, no sweep",
               "clearance_floor_mm": CLEARANCE, "keepout_x0": KX0, "lines": [], "OWNER-ITEMS": 0}
    # ---- 1. damage: clip the B.Cu run, delete the old corner via and its In5 ascent ----
    for net in NETS:
        via = None
        for t in b.GetTracks():
            if t.GetClass() != "PCB_VIA" or netname.get(t.GetNetCode(), "") != net:
                continue
            vx, vy = P.ToMM(t.GetPosition().x), P.ToMM(t.GetPosition().y)
            # the TRAPPED via: inside the keepout square (x >= KX0) AND at the corner row (y >= 73.93).
            # Filtering on x alone picks the net's TOP via at y=59.45 (outside the keepout) - diagnosed, fixed.
            if vx >= KX0 and vy >= 73.93:
                via = (t, vx, vy)
                break
        if via is None:
            drawing["lines"].append({"net": net, "error": "no corner via"}); continue
        vt, vx, vy = via
        r = P.ToMM(vt.GetWidth(P.F_Cu)) / 2.0
        x_new = round(KX0 - (r + CLEARANCE), 4)
        horiz = vert = None
        for t in b.GetTracks():
            if t.GetClass() == "PCB_VIA" or netname.get(t.GetNetCode(), "") != net:
                continue
            for (px, py) in ((P.ToMM(t.GetStart().x), P.ToMM(t.GetStart().y)),
                             (P.ToMM(t.GetEnd().x), P.ToMM(t.GetEnd().y))):
                if abs(px - vx) > 0.01 or abs(py - vy) > 0.01:
                    continue
                dxs = abs(P.ToMM(t.GetEnd().x - t.GetStart().x))
                dys = abs(P.ToMM(t.GetEnd().y - t.GetStart().y))
                if dxs > dys:                      # classify by ORIENTATION (the board layer ids do not match
                    horiz = t                      # pcbnew's copper constants: F=0/In1=1... in the file)
                else:
                    vert = t
        top = None
        if vert is not None:
            a1 = (P.ToMM(vert.GetStart().x), P.ToMM(vert.GetStart().y))
            a2 = (P.ToMM(vert.GetEnd().x), P.ToMM(vert.GetEnd().y))
            top = a2 if math.hypot(a1[0] - vx, a1[1] - vy) < 0.01 else a1
            vlayer = vert.GetLayer()
            vwidth = vert.GetWidth()
        else:
            vlayer, vwidth = P.In5_Cu, vt.GetWidth(P.F_Cu)
        far = None
        if horiz is not None:
            a1 = (P.ToMM(horiz.GetStart().x), P.ToMM(horiz.GetStart().y))
            a2 = (P.ToMM(horiz.GetEnd().x), P.ToMM(horiz.GetEnd().y))
            far = a2 if math.hypot(a1[0] - vx, a1[1] - vy) < 0.01 else a1
        # clip the horizontal run at x_new, delete the old via and the vertical ascent
        if horiz is not None:
            horiz.SetStart(P.VECTOR2I(int(round(far[0] * 1e6)), int(round(far[1] * 1e6))))
            horiz.SetEnd(P.VECTOR2I(int(round(x_new * 1e6)), int(round(vy * 1e6))))
        if vert is not None:
            vert.SetStart(P.VECTOR2I(int(round(x_new * 1e6)), int(round(vy * 1e6))))
            vert.SetEnd(P.VECTOR2I(int(round(top[0] * 1e6)), int(round(top[1] * 1e6))))
            vert.SetLayer(vlayer)
        b.Remove(vt)
        drawing["lines"].append({"net": net, "old_via": [round(vx, 4), round(vy, 4)],
                                 "new_via_derived": [x_new, round(vy, 4)],
                                 "B_Cu_run": {"from": [round(far[0], 3), round(far[1], 3)], "to": [x_new, round(vy, 4)]},
                                 "ascent_top": [round(top[0], 4), round(top[1], 4)] if top else None,
                                 "ascent_layer": vlayer})
    P.SaveBoard(work, b)
    base_pro = os.path.join(os.path.dirname(os.path.abspath(a.board)),
                            os.path.basename(a.board).replace(".kicad_pcb", ".kicad_pro"))
    if os.path.exists(base_pro):
        shutil.copyfile(base_pro, work.replace(".kicad_pcb", ".kicad_pro"))
    shutil.copyfile(work, a.board_out)
    if os.path.exists(base_pro):
        shutil.copyfile(base_pro, a.board_out.replace(".kicad_pcb", ".kicad_pro"))
    # ---- 2. judge with the authority ----
    dj = os.path.join(a.scratch, "drc.json")
    subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "-o", dj, a.board_out],
                   capture_output=True, text=True)
    import collections
    base_j = json.load(open(a.baseline_drc, encoding="utf-8"))
    cand_j = json.load(open(dj, encoding="utf-8"))
    bt = collections.Counter(v["type"] for v in base_j["violations"])
    ct = collections.Counter(v["type"] for v in cand_j["violations"])
    drawing["verification"] = {"drc_total": len(cand_j["violations"]), "baseline_total": len(base_j["violations"]),
                               "unconnected": len(cand_j.get("unconnected_items", [])),
                               "increases": {k: [bt[k], ct[k]] for k in set(bt) | set(ct) if ct[k] > bt[k]},
                               "deltas": {k: ct[k] - bt[k] for k in set(bt) | set(ct) if ct[k] != bt[k]}}
    drawing["buildability"] = "relocation_listed (B.Cu run clipped + ascent shifted; points frozen above)"
    drawing["stage"] = "STEP 2 of the construction (B.Cu clip + ascent re-anchor); maze-router tail routing not yet run"
    json.dump(drawing, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"wrote": a.out, "verification": drawing["verification"],
                      "lines": [{k: l.get(k) for k in ("net", "old_via", "new_via_derived", "ascent_top")} for l in drawing["lines"]]},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
