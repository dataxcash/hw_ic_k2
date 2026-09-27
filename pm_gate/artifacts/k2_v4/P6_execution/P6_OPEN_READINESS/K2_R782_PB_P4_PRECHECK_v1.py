#!/usr/bin/env python3
"""K2 R782 --- #K2-306 sec.2 : P-b / P4 precheck + NAMED BLOCKER (fail-closed, no self-iteration).

Run with the KiCad-bundled python (pcbnew 10.0.5), e.g.:
  LD_LIBRARY_PATH=$KI/usr/lib PYTHONPATH=$KI/usr/lib/python3.11/site-packages $KI/usr/bin/python3.11 this.py
Facts gathered (machine):
  * canonical board = hw/k2_v4_8L.l8.kicad_pcb (project.yaml board_path); frozen PCB = placement-only (0 track).
  * the "wall" = a GND stitching via fence at x ~ 133.59 (row 114); an "opening" = a GAP in that fence.
  * target opening W[114,47] lands in an EXISTING 1.8mm gap -> ZERO physical board change needed.
  * baseline kicad-cli board DRC on l8 = 170 violations, 0 unconnected.
  * the R778 certified witness is a MID-SEGMENT (slot row60 -> gate cell); it carries no ball<->cell / gate<->pad
    access segment -> direct landing yields electrically-open copper while the board already has 0 unconnected.
"""
import sys, os, json, hashlib, subprocess, collections, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
K2 = "/home/fila/jqdDev_2025/ic_hw/k2"
BRD = os.path.join(K2, "hw/k2_v4_8L.l8.kicad_pcb")
BRD_FROZEN = os.path.join(K2, "hw/k2_v4_8L.kicad_pcb")
OUT = os.path.join(HERE, "K2_R782_PB_P4_PRECHECK_v1.json")
DRCJSON = os.path.join(HERE, "K2_R782_l8_baseline_drc.json")
KI = os.environ.get("KI_APPIMAGE_ROOT", "/tmp/opencode/kiapp/squashfs-root")
KICAD_CLI = os.path.join(KI, "usr/bin/kicad-cli")
def s16(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
import pcbnew
def main():
    import time; t0=time.time()
    b = pcbnew.LoadBoard(BRD)
    bb = b.GetBoardEdgesBoundingBox()
    nets = {}
    for code, ni in b.GetNetInfo().NetsByNetcode().items(): nets[code] = ni.GetNetname()
    target = ["PCIE_UP_OUT%d_%s_J2"%(i,s) for i in range(8) for s in ("N","P")]
    per_net = collections.Counter()
    for t in b.GetTracks():
        nm = nets.get(t.GetNetCode(), "")
        if nm in target: per_net[nm] += 1
    P, X0, Y0 = 0.435, 84.0, 41.0
    XW = X0 + 114*P
    fence = []
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" and abs(pcbnew.ToMM(t.GetPosition().x) - XW) < 0.6:
            fence.append({"y": round(pcbnew.ToMM(t.GetPosition().y),3), "net": nets.get(t.GetNetCode(),"?"),
                          "_pad_mm": round(pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)),3), "drill_mm": round(pcbnew.ToMM(t.GetDrillValue()),3)})
    fence.sort(key=lambda z: z["y"])
    REG = json.load(open(os.path.join(HERE, "K2_L1_A_EXIT_REGISTRATION_REVISION_v2.json")))
    R776 = json.load(open(os.path.join(HERE, "K2_R776_MINIMAL_CORE_IIS_v1.json")))
    reach = set(tuple(g) for g in R776["reachable_gates"])
    declared = [tuple(g) for g in REG["openings_kept_routable"]] + [tuple(g) for g in REG["openings_dead_excluded"] and [o["cell"] for o in REG["openings_dead_excluded"]]] + [tuple(REG["opening_added"]["cell"])]
    WIDTH = 0.205; CLR = 0.1
    census = []
    for g in sorted(set(declared)):
        if g[0] == 114:
            y = Y0 + g[1]*P
            near = min(fence, key=lambda z: abs(z["y"]-y)) if fence else None
            dist = abs(near["y"]-y) if near else None
            edge_clr = (dist - WIDTH/2 - near["_pad_mm"]/2) if near else None
            census.append({"opening":[g[0],g[1]], "kind":"W(wall)", "cell_mm":[round(XW,3), round(y,3)],
                           "nearest_fence_via": near, "center_dist_mm": round(dist,3) if dist is not None else None,
                           "edge_clearance_mm": round(edge_clr,3) if edge_clr is not None else None,
                           "physically_open": bool(edge_clr is not None and edge_clr >= CLR),
                           "model_routable": g in reach})
        else:
            census.append({"opening":[g[0],g[1]], "kind":"E(row36 band)", "model_routable": g in reach,
                           "note":"E group sits on the row-36 escape band, not on the GND via fence"})
    added = tuple(REG["opening_added"]["cell"])
    # baseline board DRC via kicad-cli
    drc = {"available": False}
    if os.path.exists(KICAD_CLI):
        r = subprocess.run([KICAD_CLI, "pcb", "drc", "--format", "json", "--output", DRCJSON, BRD],
                           capture_output=True, text=True, env={**os.environ, "LD_LIBRARY_PATH": os.path.join(KI,"usr/lib")+":"+os.environ.get("LD_LIBRARY_PATH","")})
        j = json.load(open(DRCJSON))
        c = collections.Counter()
        for it in j.get("violations", []): c[it.get("type","?")] += 1
        drc = {"available": True, "tool": "kicad-cli " + subprocess.run([KICAD_CLI,"version"],capture_output=True,text=True).stdout.strip(),
               "violations_total": len(j.get("violations", [])), "unconnected_items": len(j.get("unconnected_items", [])),
               "by_type": dict(c.most_common()), "report": os.path.basename(DRCJSON)}
    rep = {"artifact": "k2_r782_pb_p4_precheck", "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
      "authority": "#K2-306 sec.2 : P-b physical-opening landing + P4 board-level integration & kicad-cli DRC (fail-closed precheck)",
      "boarding_toolchain": {"kicad_cli": KICAD_CLI, "kicad_version": "10.0.5", "pcbnew": pcbnew.GetBuildVersion(),
                             "note": "no pcbnew/kicad-cli on PATH; both are usable from the on-box KiCad AppImage (extracted)"},
      "board_identity": {"canonical": {"path": "hw/k2_v4_8L.l8.kicad_pcb", "sha16": s16(BRD), "tracks": len(b.GetTracks()),
                                        "zones": len(b.Zones()), "footprints": len(b.GetFootprints()), "copper_layers": b.GetCopperLayerCount()},
                         "frozen_placement_only": {"path": "hw/k2_v4_8L.kicad_pcb", "sha16": s16(BRD_FROZEN),
                                                   "tracks": 0, "note": "placement-only source board; 0 copper tracks"}},
      "bbox_mm": [round(pcbnew.ToMM(bb.GetLeft()),2), round(pcbnew.ToMM(bb.GetRight()),2), round(pcbnew.ToMM(bb.GetTop()),2), round(pcbnew.ToMM(bb.GetBottom()),2)],
      "wall": {"kind": "GND stitching via fence", "x_mm": round(XW,3), "n_vias": len(fence),
               "y_min": fence[0]["y"] if fence else None, "y_max": fence[-1]["y"] if fence else None,
               "nets": sorted(set(z["net"] for z in fence))},
      "opening_census": census,
      "target_opening": {"cell": list(added), "physically_open": next(c for c in census if c["opening"]==[added[0],added[1]])["physically_open"]},
      "per_net_board_tracks": {nm: per_net[nm] for nm in target},
      "baseline_board_drc": drc,
      "pb_verdict": "ZERO_PHYSICAL_BOARD_CHANGE_REQUIRED (the target opening W[114,47] already exists as a 1.8mm gap in the GND via fence; registration v2 adds a ROUTE through it, not copper geometry)",
      "p4_named_blockers": [
        {"id":"B1","name":"baseline DRC not green","detail":"kicad-cli board DRC on the canonical l8 board = 170 violations (0 clearance, 0 unconnected); 'all-green' cannot be reached by landing 16 lanes"},
        {"id":"B2","name":"access map missing","detail":"the R778 certified witness is a MID-SEGMENT (slot row60 -> gate cell); no ball<->cell / gate<->pad access segments => direct landing would create electrically-open copper"},
        {"id":"B3","name":"board already fully connected","detail":"canonical l8 reports 0 unconnected items; replacing the 16 nets' routing is a REPLACEMENT whose scope (which segments) is not declared in the order"}],
      "requested_rulings": ["(1) P-b 判据：确认目标口[114,47]的“物理落板”=零改动（既有空隙）？或指明“开口”的物理载体（本席侦察未见被堵载体）。",
                             "(2) P4 通过判据：是“不新增违例”还是“全清现状 170 违例”？",
                             "(3) 是否授权新增《接入映射》工序（球/焊盘↔格点）后再落线？"],
      "construction_runs": 1, "drawings": 0, "gerber_exported": False, "p5": False, "order": False,
      "changes_to_frozen_sources": 0, "elapsed_s": round(time.time()-t0,1)}
    body = json.dumps(rep, ensure_ascii=False, indent=1, default=str); rep["artifact_hash16"] = hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep, open(OUT, "w"), ensure_ascii=False, indent=1, default=str)
    print("hash16", rep["artifact_hash16"])
    print("target opening physically_open:", rep["target_opening"]["physically_open"])
    print("baseline DRC:", drc.get("violations_total"), "unconnected:", drc.get("unconnected_items"))
    print("OWNER-ITEMS: 0")
    return 0
if __name__ == "__main__": sys.exit(main())
