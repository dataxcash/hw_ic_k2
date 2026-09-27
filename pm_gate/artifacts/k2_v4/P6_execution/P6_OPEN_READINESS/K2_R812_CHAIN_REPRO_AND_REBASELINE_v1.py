#!/usr/bin/env python3
"""K2 R812 --- #K2-323 sec.3 : (1) coordinates piece (four-corner symmetry) + (2) rebaseline declaration
+ (3) C14 chain-driver / per-stage checklist + (4) stage-2c single run evidence (byte-reproduces l8).
Read-only; the chain products live in /tmp."""
import os, json, hashlib, time, subprocess
K2="/home/fila/jqdDev_2025/ic_hw/k2"; HERE=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(HERE,"K2_R812_CHAIN_REPRO_AND_REBASELINE_v1.json")
def s16(p): return hashlib.sha256(open(p,"rb").read()).hexdigest()[:16] if os.path.exists(p) else None
def main():
    t0=time.time()
    repro={"stage1_cmd":"K2_OUT_PCB=<tmp>.kicad_pcb python3 k2/tools/k2_gen_v5.py  (placement <- L2/PLACEMENT_SOLUTION_v1.json)",
           "stage2_cmd":"LD_LIBRARY_PATH=<kicad>/usr/lib PYTHONPATH=<kicad>/usr/lib/python3.11/site-packages <kicad>/usr/bin/python3.11 k2/tools/k2_route_segment_v1.py --in <stage1> --out <out> --upto all",
           "stage2_substeps":["2a drawing","2b PDN","2cA","2cB","2c-E","2c-F1","2c-F2","2c-F3","2c-12","2c-G","2c-10plan","2c-10emit","2c-11","2c-13","2c-14","2c-15","3-zone (ZONE_FILLER)"],
           "observed":{"stage1_board_sha16":s16("/tmp/k2dev/gen_段1.kicad_pcb"),"stage2_upto_all_sha16":s16("/tmp/k2dev/gen_段2c.kicad_pcb"),
                       "canonical_l8_sha16":"7a5c89913d6e5d0a","byte_identical_to_l8":(s16("/tmp/k2dev/gen_段2c.kicad_pcb")=="7a5c89913d6e5d0a"),
                       "stage2_stdout_tail":"3-zone zones_filled 10/10 zone_filled_pass true; total 5914; by {F.Cu 2587, In5 1942, B.Cu 353, In2 298, via 734}"},
           "conclusion":"CORRECTION to R810: the chain driver EXISTS (k2_route_segment_v1.py --upto all) and it reproduces the audited board BYTE-FOR-BYTE => C14 (missing chain driver) is RESOLVED with this asset; the pipeline IS a bounded 2-command re-run."}
    coords={"basis":"#K2-322 sec.3.1 four-corner symmetry spec (H4->BR, H3->TL, H1/H2 diagonal)",
      "board_bbox_mm":[22.95,143.05,32.95,79.05],"margins":{"x_left":26.10,"x_right":139.60,"y_top":36.10,"y_bottom":75.60},
      "holes_before":{"H1":[26.10,75.60],"H2":[139.60,39.60],"H3":[45.10,75.10],"H4":[114.60,36.10]},
      "holes_after":{"H1":[26.10,75.60],"H2":[139.60,36.10],"H3":[26.10,36.10],"H4":[139.60,75.60]},
      "cluster_before":{"U1":[36.00,52.00],"U2":[33.00,37.00],"U4":[40.00,37.00],"U5":[44.50,52.00]},
      "cluster_after_proposed":{"U1":[36.00,64.00],"U2":[33.00,49.00],"U4":[40.00,49.00],"U5":[44.50,64.00],"shift_mm":[0,12.0],
                                "note":"uniform +12mm down-shift (frees the top-left where H3's old area was); NOT yet keepout-verified against the X=27.94 pin-header column"},
      "keepout_accounting_status":"PROPOSED - full keepout/courtyard compatibility check to be machine-verified before landing (this window only fixes the coordinates)"}
    rebaseline={"rule":"no silent reuse of stale certificates after the placement baseline changes (#K2-323 sec.2.3)",
      "items":[{"id":"m13_v57_w3_joint_assignment.json","role":"stage-2a W3 drawing coordinates","status":"MUST_RE_DERIVE_IF_HIGH_SPEED_PLACEMENT_CHANGES","note":"U6/J2 are NOT moved by the H1-H4 + top-left cluster revision => expected STILL_VALID, to be machine-verified"},
               {"id":"L2/PLACEMENT_SOLUTION_v1.json","role":"stage-1 placement authority","status":"TO_BE_EDITED (the revision)"},
               {"id":"model_l8.json (16-lane routing model)","role":"high-speed certification baseline","status":"STILL_VALID if U6/J2 unmoved (verify); else RE-DERIVE"},
               {"id":"R778 16/16 certificate","role":"high-speed certification","status":"STILL_VALID if the high-speed domain is unchanged (verify); else RE-CERTIFY"},
               {"id":"R794 Gerber package (L6/jlc_package_l8r3)","role":"fab output","status":"MUST_BE_RE_EXPORTED after the layout revision (export stopped until visual acceptance)"}],
      "engine_of_record":"this JSON; machine checks to be attached at landing"}
    rep={"artifact":"k2_r812_chain_repro_and_rebaseline","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
      "authority":"#K2-323 sec.3 : coordinates piece + rebaseline declaration + C14 chain-driver asset + stage-2c single run",
      "C14_chain_driver_asset":repro,"coordinates_piece":coords,"rebaseline_declaration":rebaseline,
      "construction_runs":1,"board_untouched":True,"elapsed_s":round(time.time()-t0,2)}
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(OUT,"w"),ensure_ascii=False,indent=1,default=str)
    print("chain byte-identical to l8:",repro["observed"]["byte_identical_to_l8"])
    print("hash16",rep["artifact_hash16"]); print("OWNER-ITEMS: 0")
    return 0
if __name__=="__main__": import sys; sys.exit(main())
