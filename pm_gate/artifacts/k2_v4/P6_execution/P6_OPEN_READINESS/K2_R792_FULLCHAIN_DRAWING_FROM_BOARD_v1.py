#!/usr/bin/env python3
"""K2 R792 --- #K2-312 sec.2 (Route A) : extract the EXISTING canonical-board copper as the FULL-CHAIN
construction drawing (device ball -> inlet -> corridor -> gate -> connector pad) + replacement list vs the
R778 model table + P4 board-DRC check (criterion: NO NEW violations vs the classified 170 baseline).

Run under the KiCad-bundled python (pcbnew). ONE execution (offline smoke ran first, per C13 asset 4).
Board is READ-ONLY here (Route A adopts the existing copper; no board change).
"""
import sys, os, json, hashlib, collections, subprocess, time
K2 = "/home/fila/jqdDev_2025/ic_hw/k2"
HERE = os.path.dirname(os.path.abspath(__file__))
BRD = os.path.join(K2, "hw/k2_v4_8L.l8.kicad_pcb")
OUT = os.path.join(HERE, "K2_R792_FULLCHAIN_DRAWING_FROM_BOARD_v1.json")
DRCJ = os.path.join(HERE, "K2_R792_board_drc.json")
KI = os.environ.get("KI_ROOT", "/tmp/opencode/kiapp/squashfs-root")
KCLI = os.path.join(KI, "usr/bin/kicad-cli")
import pcbnew
def mm(p): return [round(pcbnew.ToMM(p.x),3), round(pcbnew.ToMM(p.y),3)]
def s16(p): return hashlib.sha256(open(p,"rb").read()).hexdigest()[:16]
def main():
    t0=time.time()
    b=pcbnew.LoadBoard(BRD)
    nets={}
    for code,ni in b.GetNetInfo().NetsByNetcode().items(): nets[code]=ni.GetNetname()
    names=["PCIE_UP_OUT%d_%s_J2"%(i,s) for i in range(8) for s in ("N","P")]
    code2name={c:n for c,n in nets.items() if n in names}
    tr=collections.defaultdict(list); vi=collections.defaultdict(list)
    for t in b.GetTracks():
        nm=code2name.get(t.GetNetCode())
        if not nm: continue
        if t.GetClass()=="PCB_VIA": vi[nm].append({"at":mm(t.GetPosition()),"drill":round(pcbnew.ToMM(t.GetDrillValue()),3)})
        else: tr[nm].append({"a":mm(t.GetStart()),"b":mm(t.GetEnd()),"layer":b.GetLayerName(t.GetLayer()),"w":round(pcbnew.ToMM(t.GetWidth()),3)})
    pads=collections.defaultdict(list)
    for fp in b.GetFootprints():
        for p in fp.Pads():
            nm=nets.get(p.GetNetCode())
            if nm in names: pads[nm].append({"ref":fp.GetReference(),"at":mm(p.GetPosition())})
    REG=json.load(open(os.path.join(HERE,"K2_L1_A_EXIT_REGISTRATION_REVISION_v2.json")))
    reggates=[tuple(g) for g in REG["openings_kept_routable"]]+[tuple(REG["opening_added"]["cell"])]
    r778={}
    for short,r in json.load(open(os.path.join(HERE,"K2_R778_CERTIFIED_16OF16_v1.json")))["witness"].items():
        r778["PCIE_UP_"+short]=r["gate"]
    r782=json.load(open(os.path.join(HERE,"K2_R782_PB_P4_PRECHECK_v1.json")))
    lanes={}; repl=[]
    for nm in names:
        t=tr[nm]; v=vi[nm]; pp=pads.get(nm,[])
        L=sum(((s["a"][0]-s["b"][0])**2+(s["a"][1]-s["b"][1])**2)**.5 for s in t)
        dev=[p for p in pp if p["ref"].startswith("U")]; conn=[p for p in pp if p["ref"].startswith("J")]
        sh=nm.replace("PCIE_UP_","")
        lanes[sh]={"device_pin":dev[0] if dev else None,"connector_pad":conn[0] if conn else None,
                   "n_tracks":len(t),"n_vias":len(v),"layers_used":sorted(set(s["layer"] for s in t)),
                   "length_mm":round(L,3),"vias":v,"segments":t,
                   "r778_assigned_gate":r778.get(nm),
                   "coverage":"FULL_CHAIN (device ball -> ... -> connector pad)" if (dev and conn) else "INCOMPLETE"}
        repl.append({"lane":sh,"r778_planned_gate":r778.get(nm),
                     "board_copper_full_chain":bool(dev and conn),
                     "disposition":"ADOPT BOARD COPPER (route A): the R778 model-plan row is NOT applied to the board; no copper replacement performed",
                     "board_tracks":len(t),"board_vias":len(v)})
    # P4 board DRC (board unchanged -> must equal the classified baseline; NEW violations must be 0)
    drc={"available":False}
    if os.path.exists(KCLI):
        subprocess.run([KCLI,"pcb","drc","--format","json","--output",DRCJ,BRD],capture_output=True,text=True,
                       env={**os.environ,"LD_LIBRARY_PATH":os.path.join(KI,"usr/lib")+":"+os.environ.get("LD_LIBRARY_PATH","")})
        j=json.load(open(DRCJ)); c=collections.Counter(x.get("type","?") for x in j.get("violations",[]))
        drc={"available":True,"tool":"kicad-cli","violations_total":len(j.get("violations",[])),
             "unconnected_items":len(j.get("unconnected_items",[])),"by_type":dict(c.most_common()),
             "baseline_total":r782["baseline_board_drc"]["violations_total"],
             "new_violations":len(j.get("violations",[]))-r782["baseline_board_drc"]["violations_total"]}
    rep={"artifact":"k2_r792_fullchain_drawing_from_board","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
      "authority":"#K2-312 sec.2 Route A: existing board copper as the FULL-CHAIN witness -> full-chain construction drawing + replacement list + P4 (criterion: no NEW DRC violations)",
      "cause_of_death":"the R778 model certification covered the MID-SEGMENT only; the full-chain joint solve is not closable in the tried candidate families (R790) - the correct lever is the copper already on the board",
      "proven_facts":["R788 census: 249/256 (lane,gate) full-chain pairs reachable standalone",
                      "canonical l8 board: unconnected_items=0, clearance violations=0 (R782 baseline)",
                      "R786: OUT6_N outlet infeasible for ALL 16 gates under the frozen 15 lanes => bottleneck is the outlet corridor"],
      "board_identity":{"path":"hw/k2_v4_8L.l8.kicad_pcb","sha16":s16(BRD),"tracks":len(b.GetTracks()),"zones":len(b.Zones())},
      "coverage_declaration":"source ball (device) -> inlet -> corridor -> gate -> target pad (connector) - FULL CHAIN; here the chain is the EXISTING copper",
      "lanes":lanes,
      "conservation":{"lanes":len(names),"lanes_full_chain":sum(1 for sh in lanes if lanes[sh]["coverage"].startswith("FULL_CHAIN")),
                      "total_tracks":sum(lanes[sh]["n_tracks"] for sh in lanes),"total_vias":sum(lanes[sh]["n_vias"] for sh in lanes),
                      "total_length_mm":round(sum(lanes[sh]["length_mm"] for sh in lanes),3)},
      "replacement_list":repl,
      "p4_board_drc":drc,
      "buildability":{"mode":"no_move","note":"route A: no board geometry change; the existing copper IS the full-chain drawing"},
      "binary":("FULLCHAIN_DRAWING_PASS" if (all(lanes[sh]["coverage"].startswith("FULL_CHAIN") for sh in lanes)
                 and drc.get("unconnected_items")==0 and drc.get("new_violations")==0) else "NAMED_BLOCKER"),
      "construction_runs":1,"drawings":1,"gerber_exported":False,"p5":False,"order":False,
      "board_untouched":True,"changes_to_frozen_sources":0,"elapsed_s":round(time.time()-t0,1)}
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(OUT,"w"),ensure_ascii=False,indent=1,default=str)
    print("binary",rep["binary"]); print("lanes_full_chain",rep["conservation"]["lanes_full_chain"],"/",len(names))
    print("p4_drc",drc.get("violations_total"),"new",drc.get("new_violations"),"unconnected",drc.get("unconnected_items"))
    print("hash16",rep["artifact_hash16"]); print("OWNER-ITEMS: 0")
    return 0
if __name__=="__main__": sys.exit(main())
