#!/usr/bin/env python3
"""K2 R806 --- #K2-319 sec.2 : piece B rework - OUT4 serpentine under the DUAL constraint
(skew <= 0.15 mm  AND  clearance zero-new). FIXED geometry: spread the correction as low-amplitude
U-bumps (exact, smoke-verified) over ALL straight segments >= 0.40 mm of the shorter line, one side.
One execution (C13; the geometry was selected offline by a bounded DRC-oracle search)."""
import pcbnew, os, sys, json, math, hashlib, collections, subprocess, time, shutil
K2="/home/fila/jqdDev_2025/ic_hw/k2"; HERE=os.path.dirname(os.path.abspath(__file__))
SRC=os.path.join(K2,"hw/k2_v4_8L.l9.kicad_pcb"); DST=os.path.join(K2,"hw/k2_v4_8L.l10.kicad_pcb")
PRO_SRC=os.path.join(K2,"hw/k2_v4_8L.l9.kicad_pro"); PRO_DST=os.path.join(K2,"hw/k2_v4_8L.l10.kicad_pro")
KI=os.environ.get("KI_ROOT","/tmp/k2kicad/squashfs-root"); KCLI=os.path.join(KI,"usr/bin/kicad-cli")
THR_MM=0.40; SIDE=1; AMAX=80000.0
def env(): return {**os.environ,"LD_LIBRARY_PATH":os.path.join(KI,"usr/lib")+":"+os.environ.get("LD_LIBRARY_PATH","")}
def V(x,y): return pcbnew.VECTOR2I(int(x),int(y))
def tl(t): return math.hypot(t.GetEnd().x-t.GetStart().x,t.GetEnd().y-t.GetStart().y)
def ubump(b,t,extra_mm,side,amax):
    L=tl(t)
    if L<3e5: return False
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
    return {"layer":lay_name(lay),"at_mm":[round(pcbnew.ToMM(A.x),3),round(pcbnew.ToMM(A.y),3)],"amp_mm":round(h/1e6,4),"add_mm":round(extra_mm,4)}
_laymap={}
def lay_name(l):
    return _laymap.get(l,str(l))
def main():
    t0=time.time(); b=pcbnew.LoadBoard(SRC)
    global _laymap
    _laymap={i:b.GetLayerName(i) for i in range(pcbnew.PCB_LAYER_ID_COUNT)}
    nd={c:ni.GetNetname() for c,ni in b.GetNetInfo().NetsByNetcode().items()}
    def nl(tg): return sum(tl(t) for t in b.GetTracks() if t.GetClass()!="PCB_VIA" and nd.get(t.GetNetCode())==tg)
    n_="PCIE_UP_OUT4_N_J2"; p_="PCIE_UP_OUT4_P_J2"
    d=nl(n_)-nl(p_); short=n_ if d<0 else p_; need=abs(d)/1e6
    cand=sorted([t for t in b.GetTracks() if t.GetClass()!="PCB_VIA" and nd.get(t.GetNetCode())==short and tl(t)>=THR_MM*1e6],key=tl,reverse=True)
    each=need/len(cand); geom=[]
    for t in cand:
        r=ubump(b,t,each,SIDE,AMAX)
        if r: geom.append(r)
    d2=abs(nl(n_)-nl(p_))/1e6
    pairs={}
    for i in range(8):
        a="PCIE_UP_OUT%d_N_J2"%i; c="PCIE_UP_OUT%d_P_J2"%i
        pairs["OUT%d"%i]=round(abs(nl(a)-nl(c))/1e6,4)
    pcbnew.SaveBoard(DST,b)
    if not os.path.exists(PRO_DST): shutil.copyfile(PRO_SRC,PRO_DST)
    drcp=os.path.join(HERE,"K2_R806_l10_drc.json")
    subprocess.run([KCLI,"pcb","drc","--format","json","--output",drcp,DST],capture_output=True,text=True,env=env())
    D=json.load(open(drcp)); V10=D.get("violations",[])
    base=json.load(open(os.path.join(HERE,"K2_R794_board_drc.json")))["violations"]
    def sig(v): return (v.get("type"),v.get("severity"),v.get("description"),tuple(sorted(str(it.get("uuid")) for it in (v.get("items") or []))))
    new=(collections.Counter(sig(v) for v in V10)-collections.Counter(sig(v) for v in base))
    rep={"artifact":"k2_r806_piece_b_out4_dual_constraint","ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
     "authority":"#K2-319 sec.2 : piece B rework under the dual constraint (skew<=0.15 AND clearance zero-new); fixed geometry, one execution",
     "src_sha16":hashlib.sha256(open(SRC,'rb').read()).hexdigest()[:16],"l10_sha16":hashlib.sha256(open(DST,'rb').read()).hexdigest()[:16],
     "method":"U-bump (exact) spread over ALL straight segments >= %.2f mm of the shorter line; one side (+); amplitude = need/(2N)"%THR_MM,
     "target_lane":short.replace("PCIE_UP_",""),"need_mm":round(need,4),"n_segments":len(geom),
     "amplitude_mm":(round(geom[0]["amp_mm"],4) if geom else None),"added_mm":round(len(geom)*each,4),
     "geometry_fixed":geom,
     "skew_after_mm":{k:round(v,4) for k,v in pairs.items()},
     "skew_max_after_mm":round(max(pairs.values()),4),"skew_threshold_mm":0.15,
     "drc":{"l10_total":len(V10),"baseline_total":len(base),"new":len(new),
            "new_items":[[k[0],k[1],(k[2] or '')[:70]] for k in new.elements()],
            "unconnected":len(D.get("unconnected_items",[])),
            "verdict":("NO_NEW_VIOLATIONS" if not new else "NEW_VIOLATIONS")},
     "conservation":{"lanes":16,"vias_unchanged":True,"note":"meander inserted mid-segment on the same net/layers; connectivity preserved (unconnected=%d)"%len(D.get("unconnected_items",[]))},
     "buildability":{"mode":"relocation_listed","note":"OUT4 shorter line meandered; no topology/pad/via change"},
     "binary":"PIECE_B_PASS" if (not new and max(pairs.values())<=0.15 and len(D.get('unconnected_items',[]))==0) else "PIECE_B_BLOCKER",
     "construction_runs":1,"board_version_bump":"l9 -> l10 (OUT4 length match)","elapsed_s":round(time.time()-t0,2)}
    body=json.dumps(rep,ensure_ascii=False,indent=1,default=str); rep["artifact_hash16"]=hashlib.sha256(body.encode()).hexdigest()[:16]
    json.dump(rep,open(os.path.join(HERE,"K2_R806_PIECE_B_v1.json"),"w"),ensure_ascii=False,indent=1,default=str)
    print("need",round(need,4),"segs",len(geom),"amp",rep["amplitude_mm"],"skew_max",rep["skew_max_after_mm"])
    print("drc l10",len(V10),"new",len(new),"unconnected",rep["drc"]["unconnected"],"->",rep["binary"])
    print("hash16",rep["artifact_hash16"]); print("OWNER-ITEMS: 0")
    return 0
if __name__=="__main__": sys.exit(main())
