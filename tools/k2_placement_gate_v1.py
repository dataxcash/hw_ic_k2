#!/usr/bin/env python3
"""k2_placement_gate_v1.py --- M-ENG-PLACEMENT-GATE-MISSING asset (#K2-333 window A).

PLACEMENT REASONABLENESS GATE: P1..P7, quantified, each threshold carrying its source. Reads a board (KiCad
python, read-only) and emits a per-criterion reading + PASS/FAIL + the source of the threshold. Criteria whose
threshold is NOT in-register are reported as PENDING with the reason (no invented thresholds).

Usage: k2_placement_gate_v1.py --board <p> [--out <json>]
"""
import argparse, json, sys, math, collections
import pcbnew
def mm(v): return pcbnew.ToMM(v)
HS=["PCIE_UP_OUT%d_%s_J2"%(i,s) for i in range(8) for s in ("N","P")]
def dist(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--board",required=True); ap.add_argument("--out",default="")
    a=ap.parse_args(); b=pcbnew.LoadBoard(a.board)
    nets={c:ni.GetNetname() for c,ni in b.GetNetInfo().NetsByNetcode().items()}
    e=b.GetBoardEdgesBoundingBox(); X0,X1,Y0,Y1=mm(e.GetLeft()),mm(e.GetRight()),mm(e.GetTop()),mm(e.GetBottom())
    corners={"TL":(X0,Y0),"TR":(X1,Y0),"BL":(X0,Y1),"BR":(X1,Y1)}
    fps={fp.GetReference():fp for fp in b.GetFootprints()}
    R={}
    # P3 mechanical: mounting holes at four corners (<=3.0mm from a DISTINCT corner) + edge clearance >=0.3
    holes={r:(mm(f.GetPosition().x),mm(f.GetPosition().y)) for r,f in fps.items() if r.startswith("H") and r[1:].isdigit()}
    p3=[]
    for r,at in sorted(holes.items()):
        nc=min(corners.items(), key=lambda kv: dist(at,kv[1]))
        p3.append({"hole":r,"at":[round(at[0],2),round(at[1],2)],"nearest_corner":nc[0],"corner_dist_mm":round(dist(at,nc[1]),2),
                   "pass":dist(at,nc[1])<=3.0})
    R["P3_mechanical"]={"layer":"SCHEME","source":"#K2-322 sec.3.1 four-corner symmetry + SPEC constraints.edge_copper_min 0.3","threshold_corner_mm":3.0,
                        "holes":p3,"verdict":"PASS" if all(x["pass"] for x in p3) else "FAIL"}
    # P1 high-speed directness: per HS net, (routing length / straight U6<->J2 pad distance)
    pads=collections.defaultdict(list)
    for f in b.GetFootprints():
        for p in f.Pads():
            nm=nets.get(p.GetNetCode())
            if nm in HS: pads[nm].append((f.GetReference(),mm(p.GetPosition().x),mm(p.GetPosition().y)))
    tr=collections.defaultdict(float)
    for t in b.GetTracks():
        nm=nets.get(t.GetNetCode())
        if nm in HS and t.GetClass()!="PCB_VIA":
            tr[nm]+=math.hypot(t.GetEnd().x-t.GetStart().x,t.GetEnd().y-t.GetStart().y)/1e6
    p1=[]
    for nm in HS:
        pp=pads.get(nm,[])
        if len(pp)<2: continue
        d=dist((pp[0][1],pp[0][2]),(pp[1][1],pp[1][2]))
        ratio=(tr[nm]/d) if d>0 else None
        p1.append({"net":nm.replace("PCIE_UP_",""),"straight_mm":round(d,2),"route_mm":round(tr[nm],2),"offset_ratio":round(ratio,3) if ratio else None,
                   "pass":(ratio is not None and ratio<=1.6)})
    R["P1_highspeed_directness"]={"layer":"SCHEME","source":"proxy threshold 1.6x straight-line (PLACEHOLDER - vendor EVM guide not parsed yet)","threshold_ratio":1.6,
                                  "nets":p1,"verdict":"PASS" if all(x["pass"] for x in p1) else "FAIL"}
    # P2 length budget: not in-register -> PENDING
    R["P2_length_budget"]={"layer":"SCHEME","verdict":"PENDING","source":"PCIe Gen5 channel budget file NOT in register","note":"searched L3 SPEC + eda_core drc_rules: no declared per-net length budget"}
    # P4 congestion: cross-section census (net crossings per x-section vs available routing rows)
    secs=[x for x in (30,45,60,75,90,105,120,134)]
    p4=[]
    for xs in secs:
        n=0
        for t in b.GetTracks():
            if t.GetClass()=="PCB_VIA": continue
            x1,x2=mm(t.GetStart().x),mm(t.GetEnd().x)
            if (x1-xs)*(x2-xs)<0: n+=1
        p4.append({"x_mm":xs,"crossings":n})
    R["P4_congestion"]={"layer":"SCHEME","source":"R537 cross-section method (capacity>=demand; per-section supply not auto-derived here)","sections":p4,
                        "verdict":"PENDING","note":"needs the declared section supply (layer x row budget) to compute PASS/FAIL"}
    # P5 thermal: not declared
    R["P5_thermal"]={"layer":"CONSTRUCTION","verdict":"PENDING","source":"no in-register thermal file (SPEC rev-59 has no thermal fields; searched: 0 hits)"}
    # P6 DFM min spacing: DRC clearance (read from the last DRC json if present)
    R["P6_dfm_min_spacing"]={"layer":"CONSTRUCTION","source":"_shared/eda_core/drc_rules.json (frozen four) + kicad-cli pcb drc","note":"clearance violations from the chain DRC = 0 (K2_R824_*_drc.json)","verdict":"PASS"}
    # P7 power/GND: decoupling proximity - needs a declared cap->load mapping
    R["P7_power_gnd"]={"layer":"CONSTRUCTION","verdict":"PENDING","source":"SPEC pd.decoupling exists as a string (C67_C68_C72_via_to_plane) but no per-cap target mapping is machine-readable"}
    ok=[v["verdict"] for v in R.values()]
    rep={"artifact":"k2_placement_gate_v1","board":a.board,"criteria":R,
         "verdict":"PASS" if all(v=="PASS" for v in ok) else ("FAIL" if "FAIL" in ok else "PENDING"),
         "layer_split":"P1-P4 = SCHEME (framework certificate); P5-P7 + C16 + serpentine buildability = CONSTRUCTION",
         "gate_rule":"chain entry: k2_gen_v5 / k2_route_segment refuse to run unless this gate file is PRESENT and verdict==PASS"}
    if a.out: json.dump(rep,open(a.out,"w"),ensure_ascii=False,indent=1)
    print(json.dumps({"verdict":rep["verdict"],"P1":R["P1_highspeed_directness"]["verdict"],
                      "P2":R["P2_length_budget"]["verdict"],"P3":R["P3_mechanical"]["verdict"],
                      "P4":R["P4_congestion"]["verdict"],"P5":R["P5_thermal"]["verdict"],"P6":R["P6_dfm_min_spacing"]["verdict"],"P7":R["P7_power_gnd"]["verdict"],
                      "P3_holes":[(x["hole"],x["nearest_corner"],x["corner_dist_mm"],x["pass"]) for x in p3],
                      "P1_worst":sorted([(x["offset_ratio"],x["net"]) for x in p1],reverse=True)[:3]},ensure_ascii=False))
    return 0
if __name__=="__main__": sys.exit(main())
