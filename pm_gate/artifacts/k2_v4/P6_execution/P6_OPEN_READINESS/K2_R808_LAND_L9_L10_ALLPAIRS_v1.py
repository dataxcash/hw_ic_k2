#!/usr/bin/env python3
"""K2 R808 --- #K2-320 sec.2.2/2.3 : land l9 (chamfer) then l10 (ALL pairs >0.15mm length-matched, 0.15 end-to-end caliber). ONE execution (C13: the micro-amplitude multi-bump method was proven offline at R806)."""
import pcbnew, os, sys, json, math, hashlib, collections, subprocess, time, shutil
K2="/home/fila/jqdDev_2025/ic_hw/k2"; HERE=os.path.dirname(os.path.abspath(__file__))
SRC=os.path.join(K2,"hw/k2_v4_8L.l8.kicad_pcb"); L9=os.path.join(K2,"hw/k2_v4_8L.l9.kicad_pcb"); L10=os.path.join(K2,"hw/k2_v4_8L.l10.kicad_pcb")
KI=os.environ.get("KI_ROOT","/tmp/k2kicad/squashfs-root"); KCLI=os.path.join(KI,"usr/bin/kicad-cli")
THR=0.30e6; SIDE=1; AMAX=80000.0; SKEW=0.15
def env(): return {**os.environ,"LD_LIBRARY_PATH":os.path.join(KI,"usr/lib")+":"+os.environ.get("LD_LIBRARY_PATH","")}
def V(x,y): return pcbnew.VECTOR2I(int(x),int(y))
def tl(t): return math.hypot(t.GetEnd().x-t.GetStart().x,t.GetEnd().y-t.GetStart().y)
def ubump(b,t,extra_mm,side,amax):
    L=tl(t)
    if L<2e5: return False
    h=(extra_mm*1e6)/2.0; a=max(50000.0,min(amax,L*0.3))
    if L<2*a+2e4: return False
    _a=t.GetStart(); _b=t.GetEnd(); A=V(_a.x,_a.y); B=V(_b.x,_b.y)
    ux,uy=(B.x-A.x)/L,(B.y-A.y)/L; nx,ny=-uy*side,ux*side
    A0=V(A.x+ux*a,A.y+uy*a); B0=V(B.x-ux*a,B.y-uy*a)
    D1=V(A0.x+nx*h,A0.y+ny*h); D2=V(B0.x+nx*h,B0.y+ny*h)
    lay=t.GetLayer(); w=t.GetWidth(); nc=t.GetNetCode()
    t.SetStart(A); t.SetEnd(A0)
    for (p,q) in [(A0,D1),(D1,D2),(D2,B0),(B0,B)]:
        nt=pcbnew.PCB_TRACK(b); nt.SetStart(p); nt.SetEnd(q); nt.SetLayer(lay); nt.SetWidth(w); nt.SetNetCode(nc); b.Add(nt)
    return {"layer":b.GetLayerName(lay),"at_mm":[round(pcbnew.ToMM(A.x),3),round(pcbnew.ToMM(A.y),3)],"seg_mm":round(L/1e6,3),"amp_mm":round(h/1e6,4),"add_mm":round(extra_mm,4)}
def main():
    t0=time.time()
    def load(p): return pcbnew.LoadBoard(p)
    def ndof(b): return {c:ni.GetNetname() for c,ni in b.GetNetInfo().NetsByNetcode().items()}
    def nlen(b,nd,tg): return sum(tl(t) for t in b.GetTracks() if t.GetClass()!="PCB_VIA" and nd.get(t.GetNetCode())==tg)
    # ---- l9 = chamfer ----
    b=load(SRC); nd=ndof(b); NETS=["PCIE_UP_OUT%d_%s_J2"%(i,s) for i in range(8) for s in ("N","P")]
    by=collections.defaultdict(list)
    for t in b.GetTracks():
        if t.GetClass()=="PCB_VIA": continue
        n=nd.get(t.GetNetCode())
        if n in NETS: by[n].append(t)
    nch=0
    for n,tr in by.items():
        ends=collections.defaultdict(list)
        for t in tr:
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
            nt=pcbnew.PCB_TRACK(b); nt.SetStart(pa); nt.SetEnd(pb); nt.SetLayer(t1.GetLayer()); nt.SetWidth(t1.GetWidth()); nt.SetNetCode(t1.GetNetCode()); b.Add(nt); nch+=1
    pcbnew.SaveBoard(L9,b); log9=os.path.join(HERE,"K2_R808_l9_drc.json")
    subprocess.run([KCLI,"pcb","drc","--format","json","--output",log9,L9],capture_output=True,text=True,env=env())
    d9=json.load(open(log9)).get("violations",[])
    # ---- l10 = + all-pair length match ----
    skew9={}; mead={}
    for i in range(8):
        a="PCIE_UP_OUT%d_N_J2"%i; c="PCIE_UP_OUT%d_P_J2"%i
        skew9["OUT%d"%i]=round(abs(nlen(b,nd,a)-nlen(b,nd,c))/1e6,4)
    for i in range(8):
        a="PCIE_UP_OUT%d_N_J2"%i; c="PCIE_UP_OUT%d_P_J2"%i; d=nlen(b,nd,a)-nlen(b,nd,c)
        if abs(d)/1e6<=SKEW: continue
        short=a if d<0 else c; need=abs(d)/1e6
        cand=sorted([t for t in b.GetTracks() if t.GetClass()!="PCB_VIA" and nd.get(t.GetNetCode())==short and tl(t)>=THR],key=tl,reverse=True)
        each=need/len(cand); g=[]
        for t in cand:
            r=ubump(b,t,each,SIDE,AMAX)
            if r: g.append(r)
        mead["OUT%d"%i]={"lane":short.replace("PCIE_UP_",""),"need_mm":round(need,4),"segments":len(g),"amp_mm":(g[0]["amp_mm"] if g else None),"geometry":g,
                         "remaining_mm":round(abs(nlen(b,nd,a)-nlen(b,nd,c))/1e6,4)}
    pcbnew.SaveBoard(L10,b)
    for f,src in [(os.path.join(K2,"hw/k2_v4_8L.l9.kicad_pro"),os.path.join(K2,"hw/k2_v4_8L.l8.kicad_pro")),(os.path.join(K2,"hw/k2_v4_8L.l10.kicad_pro"),os.path.join(K2,"hw/k2_v4_8L.l8.kicad_pro"))]:
        if not os.path.exists(f): shutil.copyfile(src,f)
    log10=os.path.join(HERE,"K2_R808_l10_drc.json")
    subprocess.run([KCLI,"pcb","drc","--format","json","--output",log10,L10],capture_output=True,text=True,env=env())
    D10=json.load(open(log10)); V10=D10.get("violations",[])
    base=json.load(open(os.path.join(HERE,"K2_R794_board_drc.json")))["violations"]
    def sig(v): return (v.get("type"),v.get("severity"),v.get("description"),tuple(sorted(str(it.get("uuid")) for it in (v.get("items") or []))))
    newc=collections.Counter(sig(v) for v in V10)-collections.Counter(sig(v) for v in base)
    new=list(newc.elements())
    skew10={}
    for i in range(8):
        a="PCIE_UP_OUT%d_N_J2"%i; c="PCIE_UP_OUT%d_P_J2"%i
        skew10["OUT%d"%i]=round(abs(nlen(b,nd,a)-nlen(b,nd,c))/1e6,4)
    # renders
    for nm,lay in [("top","F.Cu,Edge.Cuts"),("bottom","B.Cu,Edge.Cuts")]:
        subprocess.run([KCLI,"pcb","export","svg","-o",os.path.join(HERE,"K2_R808_l10_%s.svg"%nm),"-l",lay,"--page-size-mode","2",L10],capture_output=True,text=True,env=env())
    # full-chain re-verify: 16 nets have device(U*)+connector(J*) pads and unconnected==0
    pads=collections.defaultdict(set)
    for fp in b.GetFootprints():
        for p in fp.Pads():
            nn=nd.get(p.GetNetCode())
            if nn in NETS: pads[nn].add(fp.GetReference())
    fc={n.replace("PCIE_UP_",""):{"pads":sorted(pads[n]),"full_chain":any(r.startswith("U") for r in pads[n]) and any(r.startswith("J") for r in pads[n])} for n in NETS}
    rep={"artifact":"k2_r808_land_l9_l10_allpairs","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
     "authority":"#K2-320 sec.2.2/2.3 : land l9 (chamfer) then l10 (ALL pairs >0.15mm length-matched, end-to-end caliber). ONE execution.",
     "src_sha16":hashlib.sha256(open(SRC,'rb').read()).hexdigest()[:16],
     "l9_sha16":hashlib.sha256(open(L9,'rb').read()).hexdigest()[:16],"l10_sha16":hashlib.sha256(open(L10,'rb').read()).hexdigest()[:16],
     "chamfers":nch,"l9_drc_total":len(d9),
     "skew_l9_mm":skew9,"meanders":mead,"skew_l10_mm":skew10,"skew_max_l10":max(skew10.values()),
     "drc_l10":{"total":len(V10),"baseline":len(base),"new":len(new),"unconnected":len(D10.get("unconnected_items",[])),
                "new_items":[[k[0],k[1],(k[2] or '')[:70]] for k in newc.elements()]},
     "full_chain_reverify":fc,"renders":["K2_R808_l10_top.svg","K2_R808_l10_bottom.svg"],
     "binary":"FINAL_PASS" if (max(skew10.values())<=SKEW and not new and len(D10.get('unconnected_items',[]))==0 and all(v["full_chain"] for v in fc.values())) else "NAMED_BLOCKER",
     "construction_runs":1,"board_version_bump":"l8 -> l9 -> l10","elapsed_s":round(time.time()-t0,2)}
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(os.path.join(HERE,"K2_R808_LAND_L9_L10_v1.json"),"w"),ensure_ascii=False,indent=1,default=str)
    print("chamfers",nch,"l9 drc",len(d9)); print("skew_l9",skew9); print("skew_l10",skew10,"max",rep["skew_max_l10"])
    print("drc l10",len(V10),"new",len(new),"unconnected",rep["drc_l10"]["unconnected"]); print("binary",rep["binary"]); print("hash16",rep["artifact_hash16"]); print("OWNER-ITEMS: 0")
    return 0
if __name__=="__main__": sys.exit(main())
