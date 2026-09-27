#!/usr/bin/env python3
"""K2 R808 --- #K2-320 sec.2.1 : SPEC rev-57 (append-only) - record the board version bump l8->l9(chamfer)->l10(all-pair length match) + repoint project.yaml. ONE execution."""
import json, hashlib, os, sys, time
from pathlib import Path
K2=Path("/home/fila/jqdDev_2025/ic_hw/k2"); L3=K2/"pm_gate/artifacts/k2_v4/L3"
SRC=L3/"SPEC_k2_v4.spec-rev-56.json"; OUT=L3/"SPEC_k2_v4.spec-rev-57.json"
REC=K2/"pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K2_R808_SPEC_REV57_DECLARE.json"
def s16(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
def flat(o,p=""):
    if isinstance(o,dict):
        for k,v in o.items(): yield from flat(v,f"{p}.{k}")
    elif isinstance(o,list):
        for i,v in enumerate(o): yield from flat(v,f"{p}[{i}]")
    else: yield p,o
def main():
    spec=json.loads(SRC.read_text()); before=dict(flat(spec))
    spec["board_version_record_v57"]={
      "board_file":"hw/k2_v4_8L.l10.kicad_pcb","previous":"hw/k2_v4_8L.l8.kicad_pcb (board_sha16 7a5c89913d6e5d0a)",
      "chain":["l8 (=as-built 受审板)","l9 (= l8 + 166 x 45-deg chamfer, DRC 170 / 0 new)",
               "l10 (= l9 + all-pair intra-pair length match to <= 0.15 mm, DRC 170 / 0 new)"],
      "authorisation_chain":["#K2-306","#K2-316","#K2-317","#K2-318","#K2-319","#K2-320"],
      "rule":"append-only declaration; no existing scalar/geometry/threshold/net/layer role changed",
      "rollback":"repoint pm_gate/project.yaml board_path back to hw/k2_v4_8L.l8.kicad_pcb; rev-56 and all predecessors byte-unchanged"}
    spec["_spec_rev_57"]={"card":"SPEC-REV-57（板版本 bump l8→l9→l10 · #K2-320 §二.1）","at":"2026-09-27",
      "authority":"监理 #K2-320（准 SPEC rev-57：纯追加记录板 bump ＋ project.yaml 重指向）",
      "scope":"ONLY new keys: board_version_record_v57 + this card + spec_version bump. No existing field changed.",
      "basis":["R806 piece A PASS (166 chamfers; DRC 170, 0 new)","R806 piece B PASS (OUT4 skew 0.0000; DRC 170, 0 new; 33-segment 0.0223 mm amplitude meander)",
               "#K2-320 (2) all-pair scope: the 0.15 mm caliber applies end-to-end; l9 leaves 8/8 pairs over; fix every pair"],
      "unchanged":"all pre-existing fields; other frozen sources (manifest / PCB l8 / drc_rules) untouched",
      "spec_sha256_before":hashlib.sha256(SRC.read_bytes()).hexdigest(),"spec_backup":"git-tracked %s (byte-unchanged)"%SRC.name,
      "rollback":spec["board_version_record_v57"]["rollback"]}
    spec["spec_version"]="1.1.spec-rev-57"
    after=dict(flat(spec))
    added={k:v for k,v in after.items() if k not in before}; removed=[k for k in before if k not in after]
    changed={k:(before[k],after[k]) for k in before if k in after and before[k]!=after[k]}
    OUT.write_text(json.dumps(spec,ensure_ascii=False,indent=1))
    py=K2/"pm_gate/project.yaml"; yt=py.read_text(); assert "spec-rev-56.json" in yt
    py.write_text(yt.replace("spec-rev-56.json","spec-rev-57.json"))
    rec={"artifact":"k2_r808_spec_rev57_declare","src":SRC.name,"out":OUT.name,"src_sha16":s16(SRC),"out_sha16":s16(OUT),
         "added_leaves":len(added),"removed_keys":removed,"changed_existing":[k for k in changed if k!='.spec_version'],
         "spec_version":("1.1.spec-rev-56","1.1.spec-rev-57"),"project_yaml":"spec_name -> SPEC_k2_v4.spec-rev-57.json",
         "appendonly_ok":(len(removed)==0 and not [k for k in changed if k!='.spec_version']),"OWNER-ITEMS":0}
    REC.write_text(json.dumps(rec,ensure_ascii=False,indent=1))
    print(json.dumps(rec,ensure_ascii=False)); return 0
if __name__=="__main__": sys.exit(main())
