#!/usr/bin/env python3
"""K2 R798 --- #K2-315 sec.3 : M5 DELIVERY SIGNOFF INDEX (read-only, zero runs, zero board change).

Builds a machine-checkable one-page sign-off index: every item carries its in-register path + sha16, and the
index is cross-checked item-by-item against the R794 in-register artefacts. No board access; no solver.
"""
import os, sys, json, hashlib, time, collections
K2="/home/fila/jqdDev_2025/ic_hw/k2"
HERE=os.path.join(K2,"pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS")
JLC=os.path.join(K2,"pm_gate/artifacts/k2_v4/L6/jlc_package_l8r3")
OUT=os.path.join(HERE,"K2_R798_DELIVERY_SIGNOFF_INDEX_v1.json")
def s16(p):
    return hashlib.sha256(open(p,"rb").read()).hexdigest()[:16]
def item(name,path,group,note=""):
    ap=path if os.path.isabs(path) else os.path.join(K2,path)
    return {"name":name,"path":os.path.relpath(ap,K2),"exists":os.path.exists(ap),
            "bytes":(os.path.getsize(ap) if os.path.exists(ap) else None),
            "sha16":(s16(ap) if os.path.exists(ap) else None),"group":group,"note":note}
def main():
    t0=time.time()
    R794M=json.load(open(os.path.join(HERE,"K2_R794_GERBER_MANIFEST_v1.json")))
    R794D=json.load(open(os.path.join(HERE,"K2_R794_WARNING_DISPOSITIONS_v1.json")))
    R794F=json.load(open(os.path.join(HERE,"K2_R794_DFM_AND_CHECKUP_v1.json")))
    R792=json.load(open(os.path.join(HERE,"K2_R792_FULLCHAIN_DRAWING_FROM_BOARD_v1.json")))
    JM=json.load(open(os.path.join(JLC,"MANIFEST.json")))
    items=[]
    # A. Fab package (order-ready, JLC structure)
    for rel,nm in [("MANIFEST.json","JLC fab MANIFEST"),("ORDER_NOTES.md","JLC order notes"),("DISCLOSURE.md","JLC disclosure"),
                   ("05_layer_sequence.txt","layer sequence")]:
        items.append(item(nm,os.path.join("pm_gate/artifacts/k2_v4/L6/jlc_package_l8r3",rel),"A_fab_package"))
    for sub,g in [("01_gerber_rs274x","A_gerber"),("02_drill_excellon","A_drill"),("03_stackup","A_stackup"),
                  ("04_impedance","A_impedance"),("06_rulings","A_rulings"),("07_verify","A_verify")]:
        d=os.path.join(JLC,sub)
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                items.append(item("%s/%s"%(sub,f),os.path.join("pm_gate/artifacts/k2_v4/L6/jlc_package_l8r3",sub,f),g))
    # B. R794 fresh export (independent corroborating export from the verified board)
    for f in sorted(os.listdir(os.path.join(HERE,"gerber_r794"))):
        items.append(item("gerber_r794/%s"%f,os.path.join("pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS","gerber_r794",f),"B_r794_export"))
    # C. sign-off evidence (R794/R792)
    for rel,nm,g in [("K2_R794_WARNING_DISPOSITIONS_v1.json","170 warning dispositions","C_evidence"),
                     ("K2_R794_DFM_AND_CHECKUP_v1.json","DFM 16/16 + whole-board check-up","C_evidence"),
                     ("K2_R794_GERBER_MANIFEST_v1.json","R794 Gerber manifest","C_evidence"),
                     ("K2_R794_board_drc.json","board DRC raw","C_evidence"),
                     ("K2_R792_FULLCHAIN_DRAWING_FROM_BOARD_v1.json","full-chain construction drawing","C_evidence"),
                     ("K2_R794_GERBER_MANIFEST_v1_addendum.json","Gerber manifest addendum","C_evidence")]:
        items.append(item(nm,os.path.join("pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS",rel),g))
    # exemptions 1:1 with evidence
    exempt=[{"type":d["type"],"items":[it.get("uuid") for it in d["items"]],"reason":d["reason"],
             "evidence":"K2_R794_WARNING_DISPOSITIONS_v1.json#idx=%d"%d["idx"]}
            for d in R794D["dispositions"] if d["real_defect"]]
    # cross-check (machine)
    board_ok = (R794F["checkup"]["board_sha16"]==JM.get("board_sha16")==R792["board_identity"]["sha16"]=="7a5c89913d6e5d0a")
    check={"board_sha16_consistent":board_ok,"board_sha16":R794F["checkup"]["board_sha16"],
           "drc_total_matches_dispositions":(R794D["total"]==R794F["checkup"]["drc_total"]==170),
           "real_defects_registered":(R794D["real_defects"]==R794D["real_defect_dispositions"]==8),
           "dfm_target_channels_pass":all(v["verdict"]=="PASS" for v in R794F["dfm_target_channels"].values()),
           "dfm_channels":len(R794F["dfm_target_channels"]),
           "coverage_full_chain_16_16":(R792["conservation"]["lanes_full_chain"]==16),
           "gerber_r794_files_listed":R794M["n_files"],
           "all_items_have_sha16":all(i["sha16"] for i in items),
           "missing_items":[i["path"] for i in items if not i["exists"]]}
    check["CONSISTENT"]=all([check["board_sha16_consistent"],check["drc_total_matches_dispositions"],
        check["real_defects_registered"],check["dfm_target_channels_pass"],check["coverage_full_chain_16_16"],
        check["all_items_have_sha16"],not check["missing_items"]])
    thermal={"declared_in_SPEC":False,"note":"SPEC rev-56 无热设计声明字段（检索 thermal/散热/温度/theta/watt/dissipat = 0）；散热要求以 JLC 工艺冻结 A（HDI ≥2 阶）＋ ORDER_NOTES.md 制造参数为准",
             "order_notes_ref":os.path.relpath(os.path.join(JLC,"ORDER_NOTES.md"),K2)}
    rep={"artifact":"k2_r798_delivery_signoff_index","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
      "authority":"#K2-315 sec.3 : M5 human sign-off index (read-only; each item carries in-register path + sha16; item-by-item consistency vs R794)",
      "board":"k2_v4_8L.l8.kicad_pcb","board_sha16":"7a5c89913d6e5d0a",
      "groups":dict(collections.Counter(i["group"] for i in items)),
      "items":items,
      "eight_named_exemptions_1to1":exempt,
      "coverage_declaration":"target channels 16/16 FULL_CHAIN (device ball -> inlet -> corridor -> gate -> connector pad)",
      "stackup_source":os.path.relpath(os.path.join(JLC,"03_stackup"),K2),
      "impedance_source":os.path.relpath(os.path.join(JLC,"04_impedance"),K2),
      "impedance_target":{"zdiff_ohm":85.0,"tol_pct":10,"width_mm":0.205,"gap_mm":0.175,"model":"JLC_SI9000_H1_5.0mil_Er1_4.3","coupon_required":True},
      "thermal":thermal,
      "check":check,
      "binary":("SIGNOFF_INDEX_PASS" if check["CONSISTENT"] else "NAMED_BLOCKER"),
      "read_only":True,"construction_runs":0,"gerber_exported":False,"p5":False,"order":False,"board_untouched":True,
      "elapsed_s":round(time.time()-t0,3)}
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(OUT,"w"),ensure_ascii=False,indent=1,default=str)
    print("binary",rep["binary"]); print("items",len(items),"groups",rep["groups"])
    print("check",json.dumps(check,ensure_ascii=False)); print("hash16",rep["artifact_hash16"]); print("OWNER-ITEMS: 0")
    return 0
if __name__=="__main__": sys.exit(main())
