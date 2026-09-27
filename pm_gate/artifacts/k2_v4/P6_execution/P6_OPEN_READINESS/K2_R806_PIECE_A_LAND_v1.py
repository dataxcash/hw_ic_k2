#!/usr/bin/env python3
"""K2 R806 --- #K2-319 sec.1(2) : LAND piece A (45-deg chamfer only) as l9 + before/after diff + post-landing DRC (must be 170, 0 new). ONE execution (C13)."""
import pcbnew, os, sys, json, math, hashlib, collections, subprocess, time, shutil
K2="/home/fila/jqdDev_2025/ic_hw/k2"; HERE=os.path.dirname(os.path.abspath(__file__))
SRC=os.path.join(K2,"hw/k2_v4_8L.l8.kicad_pcb"); DST=os.path.join(K2,"hw/k2_v4_8L.l9.kicad_pcb")
PRO_SRC=os.path.join(K2,"hw/k2_v4_8L.l8.kicad_pro"); PRO_DST=os.path.join(K2,"hw/k2_v4_8L.l9.kicad_pro")
KI=os.environ.get("KI_ROOT","/tmp/k2kicad/squashfs-root"); KCLI=os.path.join(KI,"usr/bin/kicad-cli")
NETS=["PCIE_UP_OUT%d_%s_J2"%(i,s) for i in range(8) for s in ("N","P")]
def env(): return {**os.environ,"LD_LIBRARY_PATH":os.path.join(KI,"usr/lib")+":"+os.environ.get("LD_LIBRARY_PATH","")}
def V(x,y): return pcbnew.VECTOR2I(int(x),int(y))
def tl(t): return math.hypot(t.GetEnd().x-t.GetStart().x,t.GetEnd().y-t.GetStart().y)
def main():
    t0=time.time(); b=pcbnew.LoadBoard(SRC)
    nd={c:ni.GetNetname() for c,ni in b.GetNetInfo().NetsByNetcode().items()}
    pre={n:round(sum(tl(t) for t in b.GetTracks() if t.GetClass()!="PCB_VIA" and nd.get(t.GetNetCode())==n)/1e6,3) for n in NETS}
    by=collections.defaultdict(list)
    for t in b.GetTracks():
        if t.GetClass()=="PCB_VIA": continue
        n=nd.get(t.GetNetCode())
        if n in NETS: by[n].append(t)
    chs=[]
    for n,tracks in by.items():
        ends=collections.defaultdict(list)
        for t in tracks:
            ends[(t.GetStart().x,t.GetStart().y)].append((t,'s')); ends[(t.GetEnd().x,t.GetEnd().y)].append((t,'e'))
        for pt,ls in list(ends.items()):
            if len(ls)!=2: continue
            (t1,w1),(t2,w2)=ls
            if t1 is t2 or t1.GetLayer()!=t2.GetLayer(): continue
            A=t1.GetEnd() if w1=='s' else t1.GetStart(); B=t2.GetEnd() if w2=='s' else t2.GetStart()
            v1=(A.x-pt[0],A.y-pt[1]); v2=(B.x-pt[0],B.y-pt[1]); l1=math.hypot(*v1); l2=math.hypot(*v2)
            if l1<1 or l2<1 or abs(v1[0]*v2[0]+v1[1]*v2[1])>0.06*l1*l2: continue
            lg=min(200000.0,l1*0.4,l2*0.4)
            if lg<50000: continue
            pa=V(pt[0]+v1[0]/l1*lg,pt[1]+v1[1]/l1*lg); pb=V(pt[0]+v2[0]/l2*lg,pt[1]+v2[1]/l2*lg)
            if w1=='s': t1.SetStart(pa)
            else: t1.SetEnd(pa)
            if w2=='s': t2.SetStart(pb)
            else: t2.SetEnd(pb)
            nt=pcbnew.PCB_TRACK(b); nt.SetStart(pa); nt.SetEnd(pb); nt.SetLayer(t1.GetLayer()); nt.SetWidth(t1.GetWidth()); nt.SetNetCode(t1.GetNetCode()); b.Add(nt)
            chs.append({"net":n.replace("PCIE_UP_",""),"layer":t1.GetLayerName(),"at_mm":[round(pcbnew.ToMM(pt[0]),3),round(pcbnew.ToMM(pt[1]),3)],"leg_mm":round(lg/1e6,3)})
    post={n:round(sum(tl(t) for t in b.GetTracks() if t.GetClass()!="PCB_VIA" and nd.get(t.GetNetCode())==n)/1e6,3) for n in NETS}
    pcbnew.SaveBoard(DST,b)
    if not os.path.exists(PRO_DST): shutil.copyfile(PRO_SRC,PRO_DST)
    drcp=os.path.join(HERE,"K2_R806_l9_land_drc.json")
    subprocess.run([KCLI,"pcb","drc","--format","json","--output",drcp,DST],capture_output=True,text=True,env=env())
    V9=json.load(open(drcp)).get("violations",[])
    base=json.load(open(os.path.join(HERE,"K2_R794_board_drc.json")))["violations"]
    def sig(v): return (v.get("type"),v.get("severity"),v.get("description"),tuple(sorted(str(it.get("uuid")) for it in (v.get("items") or []))))
    new=list((collections.Counter(sig(v) for v in V9)-collections.Counter(sig(v) for v in base)).elements())
    diff={n.replace("PCIE_UP_",""):{"len_before_mm":pre[n],"len_after_mm":post[n],"delta_mm":round(post[n]-pre[n],3)} for n in NETS}
    rep={"artifact":"k2_r806_piece_a_land","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
     "authority":"#K2-319 sec.1(2) : LAND piece A (chamfer-only) as l9; before/after diff; post-landing DRC must be 170 with 0 new",
     "src_sha16":hashlib.sha256(open(SRC,'rb').read()).hexdigest()[:16],"l9_sha16":hashlib.sha256(open(DST,'rb').read()).hexdigest()[:16],
     "chamfers_total":len(chs),"chamfer_list":chs,"per_net_length_diff":diff,
     "drc":{"l9_total":len(V9),"baseline_total":len(base),"new":len(new),"new_items":[[x[0],x[1],(x[2] or '')[:70]] for x in new[:10]]},
     "binary":"PIECE_A_LANDED" if len(new)==0 else "PIECE_A_LAND_BLOCKER",
     "construction_runs":1,"board_version_bump":"l8 -> l9 (chamfer only)","elapsed_s":round(time.time()-t0,2)}
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(os.path.join(HERE,"K2_R806_PIECE_A_LAND_v1.json"),"w"),ensure_ascii=False,indent=1,default=str)
    print("chamfers",len(chs),"l9 drc",len(V9),"new",len(new),"->",rep["binary"]); print("hash16",rep["artifact_hash16"]); print("OWNER-ITEMS: 0")
    return 0
if __name__=="__main__": sys.exit(main())
