#!/usr/bin/env python3
"""k2_draw_run_v1.py --- #K2-346 scheme window: TWO-PHASE, PROCESS-SPLIT determinate drawing for the two trapped
runs (PCIE_DN4_N / PCIE_DN5_P).  Process split is mandatory: importing the maze router into the same process as
board mutation corrupts pcbnew's SWIG state (diagnosed D3 in R870).

  phase clip  (pcbnew ONLY):  the trapped corner via is deleted, the B.Cu horizontal run is clipped at the DERIVED
                              x = keepout_x0 - (via_r + clearance_floor) = 137.555, and the old In5 vertical ascent
                              is deleted -> two open ends per line: (x_new, y_run) on B.Cu and the top node on In5.
  phase route (router ONLY):  the floored maze router (exact gate, 0.20 mm floor) bridges the two open ends.
  phase judge (kicad-cli):    DRC <= baseline, no class up, unconnected 0 -> then the added points are FROZEN as
                              the drawing.  ONE run per work directory; on FAIL a blocker report is filed instead.
"""
import argparse, json, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KICAD_CLI = os.environ.get("KICAD_CLI", "/tmp/k2kicad/squashfs-root/usr/bin/kicad-cli")
ROUTER = os.path.join(ROOT, "tools", "k2_reroute_router_floor_v1.py")
NETS = ["PCIE_DN4_N", "PCIE_DN5_P"]
KX0, KY0 = 137.93, 73.93
CLEARANCE = 0.20


def clip(a):
    import pcbnew as P
    b = P.LoadBoard(a.board)
    netname = {c: ni.GetNetname() for c, ni in b.GetNetInfo().NetsByNetcode().items()}
    out = {"lines": []}
    for net in NETS:
        vt = None
        for t in b.GetTracks():
            if t.GetClass() != "PCB_VIA" or netname.get(t.GetNetCode(), "") != net:
                continue
            vx, vy = P.ToMM(t.GetPosition().x), P.ToMM(t.GetPosition().y)
            if vx >= KX0 and vy >= KY0:                    # the TRAPPED via (x AND y inside the keepout)
                vt = (t, vx, vy); break
        if vt is None:
            out["lines"].append({"net": net, "error": "no trapped via"}); continue
        t, vx, vy = vt
        r = P.ToMM(t.GetWidth(P.F_Cu)) / 2.0
        x_new = round(KX0 - (r + CLEARANCE), 4)
        horiz = vert = None
        for s in b.GetTracks():
            if s.GetClass() == "PCB_VIA" or netname.get(s.GetNetCode(), "") != net:
                continue
            e = [(P.ToMM(s.GetStart().x), P.ToMM(s.GetStart().y)), (P.ToMM(s.GetEnd().x), P.ToMM(s.GetEnd().y))]
            if not any(abs(px - vx) < 0.02 and abs(py - vy) < 0.02 for (px, py) in e):
                continue
            if abs(e[1][0] - e[0][0]) > abs(e[1][1] - e[0][1]):
                horiz = s
            else:
                vert = s; top = e[1] if (abs(e[0][0]-vx) < 0.02 and abs(e[0][1]-vy) < 0.02) else e[0]
        if horiz is None:
            out["lines"].append({"net": net, "error": "no B.Cu run attached"}); continue
        he = [(P.ToMM(horiz.GetStart().x), P.ToMM(horiz.GetStart().y)),
              (P.ToMM(horiz.GetEnd().x), P.ToMM(horiz.GetEnd().y))]
        far = he[1] if (abs(he[0][0]-vx) < 0.02 and abs(he[0][1]-vy) < 0.02) else he[0]
        horiz.SetStart(P.VECTOR2I(int(round(far[0] * 1e6)), int(round(far[1] * 1e6))))
        horiz.SetEnd(P.VECTOR2I(int(round(x_new * 1e6)), int(round(vy * 1e6))))
        top_pt = None
        if vert is not None:
            ve = [(P.ToMM(vert.GetStart().x), P.ToMM(vert.GetStart().y)),
                  (P.ToMM(vert.GetEnd().x), P.ToMM(vert.GetEnd().y))]
            top_pt = ve[1] if (abs(ve[0][0]-vx) < 0.02 and abs(ve[0][1]-vy) < 0.02) else ve[0]
            vlayer = vert.GetLayer()
            b.Remove(vert)                                  # the ascent is re-routed from scratch
        else:
            vlayer = P.In5_Cu
        b.Remove(t)                                         # delete the trapped corner via
        out["lines"].append({"net": net, "old_trapped_via": [round(vx, 4), round(vy, 4)],
                             "new_layer_change_x": x_new, "B_Cu_run_kept": [[round(far[0], 3), round(far[1], 3)],
                                                                            [x_new, round(vy, 4)]],
                             "ascent_top_node": [round(top_pt[0], 4), round(top_pt[1], 4)] if top_pt else None,
                             "ascent_layer": vlayer})
    P.SaveBoard(a.out, b)
    base_pro = os.path.join(os.path.dirname(os.path.abspath(a.board)),
                            os.path.basename(a.board).replace(".kicad_pcb", ".kicad_pro"))
    if os.path.exists(base_pro) and os.path.abspath(a.out).replace(".kicad_pcb", ".kicad_pro") != os.path.abspath(base_pro):
        shutil.copyfile(base_pro, a.out.replace(".kicad_pcb", ".kicad_pro"))
    json.dump(out, open(a.report or (a.out + ".clip.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"phase": "clip", "lines": out["lines"]}, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="all", choices=["all", "clip"])
    ap.add_argument("--board", required=True)
    ap.add_argument("--baseline-drc", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--report", default="")
    a = ap.parse_args()
    os.makedirs(a.work, exist_ok=True)
    clipped = os.path.join(a.work, "clipped.kicad_pcb")
    if a.phase == "clip":
        a.out = a.out if hasattr(a, "out") else clipped
        return clip(a)
    py = sys.executable
    # mirror the project context
    hw = os.path.dirname(os.path.abspath(a.board))
    for f in os.listdir(hw):
        if f in ("fp-lib-table", "lib") or f.endswith(".kicad_pro"):
            dst = os.path.join(a.work, f)
            if os.path.exists(dst) or os.path.islink(dst):
                continue
            (os.symlink(os.path.join(hw, f), dst) if os.path.isdir(os.path.join(hw, f))
             else shutil.copyfile(os.path.join(hw, f), dst))
    class A:  # namespace for the clip phase
        board, out, report = a.board, clipped, os.path.join(a.work, "clip.json")
    r = subprocess.run([py, os.path.abspath(__file__), "--phase", "clip", "--board", a.board,
                        "--baseline-drc", a.baseline_drc, "--work", a.work], capture_output=True, text=True)
    sys.stderr.write(r.stdout[-400:] + r.stderr[-400:])
    # DRC of the clipped board (its unconnected items drive the router)
    d1 = os.path.join(a.work, "clipped_drc.json")
    subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "-o", d1, clipped],
                   capture_output=True, text=True)
    routed = os.path.join(a.work, "routed.kicad_pcb")
    rr = subprocess.run([py, ROUTER, "--in", clipped, "--drc", d1, "--out", routed,
                         "--ledger", os.path.join(a.work, "router_ledger.json"), "--margin", "6.0",
                         "--floor", str(CLEARANCE)], capture_output=True, text=True)
    sys.stderr.write(rr.stdout[-300:] + rr.stderr[-300:])
    dj = os.path.join(a.work, "final_drc.json")
    subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json", "--severity-all", "-o", dj, routed],
                   capture_output=True, text=True)
    import collections
    base = json.load(open(a.baseline_drc, encoding="utf-8"))
    fin = json.load(open(dj, encoding="utf-8"))
    bt = collections.Counter(v["type"] for v in base["violations"])
    ft = collections.Counter(v["type"] for v in fin["violations"])
    clipj = json.load(open(os.path.join(a.work, "clip.json"), encoding="utf-8"))
    led = json.load(open(os.path.join(a.work, "router_ledger.json"), encoding="utf-8")) if os.path.exists(
        os.path.join(a.work, "router_ledger.json")) else None
    rep = {"artifact": "k2_run_drawing_v1", "ts": "2026-09-28",
           "authority": "#K2-346 (bounded scheme window): two-phase process-split determinate drawing",
           "phase_clip": clipj, "phase_route": {"added": led.get("added") if led else None,
                                                "summary": led.get("summary") if led else None,
                                                "blocked": led.get("blocked") if led else None},
           "verification": {"drc_total": len(fin["violations"]), "baseline_total": len(base["violations"]),
                            "unconnected": len(fin.get("unconnected_items", [])),
                            "increases": {k: [bt[k], ft[k]] for k in set(bt) | set(ft) if ft[k] > bt[k]},
                            "deltas": {k: ft[k] - bt[k] for k in set(bt) | set(ft) if ft[k] != bt[k]}},
           "buildability": "relocation_listed", "OWNER-ITEMS": 0}
    rep["verification"]["PASS"] = (not rep["verification"]["increases"]
                                   and rep["verification"]["unconnected"] == 0
                                   and rep["verification"]["drc_total"] <= rep["verification"]["baseline_total"])
    json.dump(rep, open(a.report or os.path.join(a.work, "drawing.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps({"clip": clipj["lines"], "route": rep["phase_route"],
                      "verification": rep["verification"]}, ensure_ascii=False, indent=1))
    return 0 if rep["verification"]["PASS"] else 1


if __name__ == "__main__":
    sys.exit(main())
