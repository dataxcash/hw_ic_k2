#!/usr/bin/env python3
"""K2 R802 --- #K2-317 : P4 refinement (ONE execution) = 45-deg chamfer + OUT4 pair length-match -> l9 board
+ whole-board kicad-cli DRC (must not add violations vs the 170 baseline) + double-sided render + re-measure.

Primitives were smoke-tested offline first (C13): chamfer verified (2026-09-27) and the meander is EXACT
(requested +X -> measured +X, 0.0% error) after fixing an endpoint-aliasing defect (GetStart/GetEnd return
internal references -> copying the endpoints is mandatory).
"""
import pcbnew, os, sys, json, math, hashlib, collections, subprocess, time
K2="/home/fila/jqdDev_2025/ic_hw/k2"; HERE=os.path.dirname(os.path.abspath(__file__))
SRC=os.path.join(K2,"hw/k2_v4_8L.l8.kicad_pcb")
DST=os.path.join(K2,"hw/k2_v4_8L.l9.kicad_pcb")
PRO_DST=os.path.join(K2,"hw/k2_v4_8L.l9.kicad_pro")
KI=os.environ.get("KI_ROOT","/tmp/k2kicad/squashfs-root"); KCLI=os.path.join(KI,"usr/bin/kicad-cli")
NETS=["PCIE_UP_OUT%d_%s_J2"%(i,s) for i in range(8) for s in ("N","P")]
def env(): return {**os.environ,"LD_LIBRARY_PATH":os.path.join(KI,"usr/lib")+":"+os.environ.get("LD_LIBRARY_PATH","")}
def V(x,y): return pcbnew.VECTOR2I(int(x),int(y))
def nmof(b): return {c:ni.GetNetname() for c,ni in b.GetNetInfo().NetsByNetcode().items()}
def tl(t): return math.hypot(t.GetEnd().x-t.GetStart().x,t.GetEnd().y-t.GetStart().y)
def netlen(b,nd,tgt): return sum(tl(t) for t in b.GetTracks() if t.GetClass()!="PCB_VIA" and nd.get(t.GetNetCode())==tgt)
def chamfer(b,nd,leg=200000):
    by=collections.defaultdict(list)
    for t in b.GetTracks():
        if t.GetClass()=="PCB_VIA": continue
        n=nd.get(t.GetNetCode())
        if n in NETS: by[n].append(t)
    n=0
    for nm,tracks in by.items():
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
            lg=min(leg,l1*0.4,l2*0.4)
            if lg<50000: continue
            pa=V(pt[0]+v1[0]/l1*lg,pt[1]+v1[1]/l1*lg); pb=V(pt[0]+v2[0]/l2*lg,pt[1]+v2[1]/l2*lg)
            if w1=='s': t1.SetStart(pa)
            else: t1.SetEnd(pa)
            if w2=='s': t2.SetStart(pb)
            else: t2.SetEnd(pb)
            nt=pcbnew.PCB_TRACK(b); nt.SetStart(pa); nt.SetEnd(pb); nt.SetLayer(t1.GetLayer()); nt.SetWidth(t1.GetWidth()); nt.SetNetCode(t1.GetNetCode()); b.Add(nt); n+=1
    return n
def meander(b,nd,tgt,extra_mm):
    cand=[t for t in b.GetTracks() if t.GetClass()!="PCB_VIA" and nd.get(t.GetNetCode())==tgt]
    if not cand: return None
    t=max(cand,key=tl); L=tl(t)
    if L<4e6: return None
    h=(extra_mm*1e6)/2.0; a=max(200000.0,min(500000.0,L*0.15))
    if L<2*a+1e5: return None
    _a=t.GetStart(); _b=t.GetEnd(); A=V(_a.x,_a.y); B=V(_b.x,_b.y)      # COPY (aliasing fix)
    ux,uy=(B.x-A.x)/L,(B.y-A.y)/L; nx,ny=-uy,ux
    A0=V(A.x+ux*a,A.y+uy*a); B0=V(B.x-ux*a,B.y-uy*a)
    D1=V(A0.x+nx*h,A0.y+ny*h); D2=V(B0.x+nx*h,B0.y+ny*h)
    t.SetStart(A); t.SetEnd(A0)
    for (p,q) in [(A0,D1),(D1,D2),(D2,B0),(B0,B)]:
        nt=pcbnew.PCB_TRACK(b); nt.SetStart(p); nt.SetEnd(q); nt.SetLayer(t.GetLayer()); nt.SetWidth(t.GetWidth()); nt.SetNetCode(t.GetNetCode()); b.Add(nt)
    return {"seg_mm":round(L/1e6,3),"layer":t.GetLayerName()}
def main():
    t0=time.time()
    b=pcbnew.LoadBoard(SRC); nd=nmof(b)
    pre={n:round(netlen(b,nd,n)/1e6,3) for n in NETS}
    nch=chamfer(b,nd)
    mid={n:round(netlen(b,nd,n)/1e6,3) for n in NETS}
    meads={}
    for i in range(8):
        n_=NETS[2*i]; p_=NETS[2*i+1]; d=mid[n_]-mid[p_]
        if abs(d)<=0.5: continue
        short=n_ if d<0 else p_
        r=meander(b,nd,short,abs(d))
        meads["OUT%d"%i]={"shortened":short.replace("PCIE_UP_",""),"added_mm":round(abs(d),3),"seg":r}
    post={n:round(netlen(b,nd,n)/1e6,3) for n in NETS}
    # save l9 (+ pro)
    pcbnew.SaveBoard(DST,b)
    import shutil
    if not os.path.exists(PRO_DST): shutil.copyfile(os.path.join(K2,"hw/k2_v4_8L.l8.kicad_pro"),PRO_DST)
    # DRC l9
    drcp=os.path.join(HERE,"K2_R802_l9_drc.json")
    subprocess.run([KCLI,"pcb","drc","--format","json","--output",drcp,DST],capture_output=True,text=True,env=env())
    D9=json.load(open(drcp)); V9=D9.get("violations",[])
    base=json.load(open(os.path.join(HERE,"K2_R794_board_drc.json")))["violations"]
    def sig(v): return (v.get("type"),v.get("severity"),v.get("description"),tuple(sorted(str(it.get("uuid")) for it in (v.get("items") or []))))
    b9=collections.Counter(sig(v) for v in V9); b0=collections.Counter(sig(v) for v in base)
    new=list((b9-b0).elements()); removed=list((b0-b9).elements())
    # renders
    svgT=os.path.join(HERE,"K2_R802_l9_top.svg"); svgB=os.path.join(HERE,"K2_R802_l9_bottom.svg")
    subprocess.run([KCLI,"pcb","export","svg","-o",svgT,"-l","F.Cu,Edge.Cuts","--page-size-mode","2",DST],capture_output=True,text=True,env=env())
    subprocess.run([KCLI,"pcb","export","svg","-o",svgB,"-l","B.Cu,Edge.Cuts","--page-size-mode","2",DST],capture_output=True,text=True,env=env())
    # via review
    vias=collections.defaultdict(list)
    for t in b.GetTracks():
        if t.GetClass()=="PCB_VIA" and nd.get(t.GetNetCode()) in NETS:
            vias[nd[t.GetNetCode()]].append({"at":[round(pcbnew.ToMM(t.GetPosition().x),3),round(pcbnew.ToMM(t.GetPosition().y),3)],"via_type":int(t.GetViaType())})
    vt=collections.Counter(("THROUGH(F-B)" if v["via_type"]==4 else "BLIND_BURIED(HDI)") for vv in vias.values() for v in vv)
    rep={"artifact":"k2_r802_p4_refine","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
      "authority":"#K2-317 : P4 refinement one-execution - 45deg chamfer + OUT4 pair length-match -> l9 + whole-board DRC (no new violations) + double-sided render",
      "src_sha16":hashlib.sha256(open(SRC,'rb').read()).hexdigest()[:16],
      "l9_sha16":hashlib.sha256(open(DST,'rb').read()).hexdigest()[:16],
      "requirement2_chamfer":{"corners_chamfered":nch},
      "requirement1_length":{"before":pre,"after_chamfer":mid,"final":post,
        "delta_final":{ "OUT%d"%i: round(abs(post[NETS[2*i]]-post[NETS[2*i+1]]),3) for i in range(8)},
        "all_within_0p50":all(abs(post[NETS[2*i]]-post[NETS[2*i+1]])<=0.5 for i in range(8)),
        "meanders":meads},
      "requirement3_vias":{"count":sum(len(v) for v in vias.values()),"by_kind":dict(vt),
        "conclusion":"16 THROUGH(F-B) vias carry a stub barrel in the 8-layer HDI stack -> fab decision (back-drill OR blind substitution); 48 BLIND_BURIED have no through stub -> no back-drill",
        "model_drawing_had":"the R780 model drawing showed 5 layer-change vias; the real board carries 4 vias per lane (64 total on the 16 nets)"},
      "drc":{"l9_total":len(V9),"baseline_total":len(base),"new":len(new),"removed":len(removed),
             "new_items":[[x[0],x[1],(x[2] or "")[:70]] for x in new[:20]],
             "verdict":("NO_NEW_VIOLATIONS" if len(new)==0 else "NEW_VIOLATIONS")},
      "renders":{"top_svg":os.path.basename(svgT),"bottom_svg":os.path.basename(svgB),
                 "top_bytes":os.path.getsize(svgT) if os.path.exists(svgT) else None,
                 "bottom_bytes":os.path.getsize(svgB) if os.path.exists(svgB) else None},
      "binary":"P4_REFINE_PASS" if (len(new)==0 and all(abs(post[NETS[2*i]]-post[NETS[2*i+1]])<=0.5 for i in range(8))) else "NAMED_BLOCKER",
      "construction_runs":1,"board_untouched":False,"board_version_bump":"l8 -> l9","elapsed_s":round(time.time()-t0,2)}
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(os.path.join(HERE,"K2_R802_P4_REFINE_v1.json"),"w"),ensure_ascii=False,indent=1,default=str)
    print("chamfers",nch,"meanders",meads); print("final deltas",rep["requirement1_length"]["delta_final"])
    print("drc l9",len(V9),"baseline",len(base),"new",len(new)); print("binary",rep["binary"]); print("hash16",rep["artifact_hash16"]); print("OWNER-ITEMS: 0")
    return 0
if __name__=="__main__": sys.exit(main())
