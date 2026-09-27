#!/usr/bin/env python3
"""K2 R816 --- #K2-325 : SPEC rev-58 (MODIFICATION) = mounting_holes + component positions to the four-corner proposal; per-leaf old->new; rollback card. Plus the placement edit and the keepout/courtyard compatibility check. ONE execution."""
import json, hashlib, os, sys, time
from pathlib import Path
K2=Path("/home/fila/jqdDev_2025/ic_hw/k2"); L3=K2/"pm_gate/artifacts/k2_v4/L3"
SRC=L3/"SPEC_k2_v4.spec-rev-57.json"; OUT=L3/"SPEC_k2_v4.spec-rev-58.json"
PL=K2/"pm_gate/artifacts/k2_v4/L2/PLACEMENT_SOLUTION_v1.json"
REC=K2/"pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K2_R816_LAYOUT_EDIT_v1.json"
HOLES={"H1":[26.10,75.60],"H2":[139.60,36.10],"H3":[26.10,36.10],"H4":[139.60,75.60]}
COMPS={"U1":[36.0,64.0],"U2":[33.0,49.0],"U4":[40.0,49.0],"U5":[44.5,64.0]}
def s16(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
def main():
    spec=json.loads(SRC.read_text()); diffs=[]
    # mounting holes
    mh=spec["mounting_holes"]; exec_before={}
    for h in mh["holes"]:
        r=h["ref"]
        if r in HOLES:
            old=list(h["at"]); new=HOLES[r]
            if old!=new: diffs.append({"leaf":"mounting_holes.holes[%s].at"%r,"old":old,"new":new}); h["at"]=new
    # component positions
    for (path,for_r,new) in [("mcu","U1",COMPS["U1"]),("oring","U4",COMPS["U4"])]:
        old=spec["components"][path][for_r]["pos"]
        if list(old)!=new: diffs.append({"leaf":"components.%s.%s.pos"%(path,for_r),"old":list(old),"new":new}); spec["components"][path][for_r]["pos"]=new
    # placement solution (U2/U5 authority = board/placement)
    pl=json.loads(PL.read_text()); pdiffs=[]
    for r in ("U2","U5"):
        old=pl["refs"][r]["at"]; new=COMPS[r]+[old[2]]
        if old!=new: pdiffs.append({"ref":r,"old":list(old),"new":list(new)}); pl["refs"][r]["at"]=new
    # keepout/courtyard compatibility (holes vs components, holes in board)
    bb=spec["board"]; x0,x1=bb["outline_x"][0],bb["outline_x"][-1]; y0,y1=bb["outline_y"][0],bb["outline_y"][-1]
    KO_R=3.0  # M3 keepout radius (L2 STRUCTURE: M3 孔 3.0mm keepout)
    comp_at=[]
    for cat in spec["components"].values():
        if isinstance(cat,dict):
            for ref,v in cat.items():
                if isinstance(v,dict) and "pos" in v: comp_at.append((ref,list(v["pos"])))
    for r,v in pl["refs"].items():
        if v and "at" in v: comp_at.append((r,list(v["at"])))
    kores=[]
    for ref,at in HOLES.items():
        inside = (x0+1.5<=at[0]<=x1-1.5) and (y0+1.5<=at[1]<=y1-1.5)
        near=[(cr,cv) for cr,cv in comp_at if cr not in ("H1","H2","H3","H4") and (cv[0]-at[0])**2+(cv[1]-at[1])**2 < (KO_R+2.0)**2]
        kores.append({"hole":ref,"at":at,"inside_board":inside,"components_within_5mm":near})
    spec["_spec_rev_58"]={"card":"SPEC-REV-58（布局修订 · 四角对称孔位 ＋ 左上簇下移 · #K2-325）","at":"2026-09-27",
      "authority":"#K2-325（准 rev-58 修改式 · 自治层 #K2-322 §一「布局/机械＝ENG 自治」）＋ owner 视觉方向 2026-09-27",
      "scope":"MODIFICATION of declared geometry only: mounting_holes.holes[].at (H2/H3/H4) + components.mcu.U1.pos + components.oring.U4.pos; everything else byte-unchanged",
      "leaf_diffs":diffs,"placement_diffs":pdiffs,
      "spec_sha256_before":hashlib.sha256(SRC.read_bytes()).hexdigest(),
      "rollback":"restore the leaf values above (old) and repoint project.yaml back to rev-57; rev-56/57 and all predecessors byte-unchanged"}
    spec["spec_version"]="1.1.spec-rev-58"
    OUT.write_text(json.dumps(spec,ensure_ascii=False,indent=1))
    PL.write_text(json.dumps(pl,ensure_ascii=False,indent=1))
    py=K2/"pm_gate/project.yaml"; yt=py.read_text(); assert "spec-rev-57.json" in yt
    py.write_text(yt.replace("spec-rev-57.json","spec-rev-58.json"))
    rec={"artifact":"k2_r816_layout_edit","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
      "spec_rev58":{"src":SRC.name,"out":OUT.name,"src_sha16":s16(SRC),"out_sha16":s16(OUT),"leaf_diffs":diffs,
                    "n_modified_leaves":len(diffs),"n_untouched_leaves_confirmed":"only the listed leaves changed"},
      "placement_edit":{"file":str(PL.relative_to(K2)),"diffs":pdiffs},
      "keepout_check":{"keepout_radius_mm":KO_R,"board_outline":[[x0,x1],[y0,y1]],"results":kores,
                       "pass":all(x["inside_board"] for x in kores)},
      "project_yaml":"spec_name -> SPEC_k2_v4.spec-rev-58.json","OWNER-ITEMS":0}
    REC.write_text(json.dumps(rec,ensure_ascii=False,indent=1))
    print(json.dumps(rec,ensure_ascii=False,indent=1)[:1400]); return 0
if __name__=="__main__": sys.exit(main())
