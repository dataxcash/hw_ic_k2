"""双口径：① 保守矩形（在库仪器口径）② 精确铜形胶囊 —— 逐段比对（只读）。"""
import json,math,sys,hashlib
import pcbnew
NM=1_000_000
BOARD=sys.argv[1]; OUT=sys.argv[2]
STACK=[("F.Cu",pcbnew.F_Cu),("In1.Cu",pcbnew.In1_Cu),("In2.Cu",pcbnew.In2_Cu),("In3.Cu",pcbnew.In3_Cu),
       ("In4.Cu",pcbnew.In4_Cu),("In5.Cu",pcbnew.In5_Cu),("In6.Cu",pcbnew.In6_Cu),("B.Cu",pcbnew.B_Cu)]
INNER=[pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.In5_Cu,pcbnew.In6_Cu]
bd=pcbnew.LoadBoard(BOARD)
def _union(layer,getter):
    ps,has=None,False
    for z in bd.Zones():
        if not z.IsOnLayer(layer) or z.GetIsRuleArea(): continue
        try: fl=getter(z)
        except Exception: fl=None
        if fl is None or fl.OutlineCount()==0: continue
        if not has: ps=pcbnew.SHAPE_POLY_SET(fl); has=True
        else: ps.BooleanAdd(fl)
    return ps if has else None
planes={}
for lay in INNER:
    fl=_union(lay, lambda z: z.GetFilledPolysList(lay) if z.IsFilled() else None)
    if fl is not None: planes[lay]=fl
idx={l:i for i,(n,l) in enumerate(STACK)}
def nearest(li,d):
    i=idx[li]+d
    while 0<=i<len(STACK):
        if STACK[i][1] in planes: return STACK[i][1]
        i+=d
    return None
def poly(pts):
    ps=pcbnew.SHAPE_POLY_SET(); ch=pcbnew.SHAPE_LINE_CHAIN()
    for x,y in pts: ch.Append(int(x),int(y))
    ch.SetClosed(True); ps.AddOutline(ch); return ps
def rect_pts(t):
    s,e,w=t.GetStart(),t.GetEnd(),t.GetWidth(); dx,dy=e.x-s.x,e.y-s.y; L=math.hypot(dx,dy)
    nx,ny=-dy/L*w/2.0, dx/L*w/2.0
    return [(s.x+nx,s.y+ny),(e.x+nx,e.y+ny),(e.x-nx,e.y-ny),(s.x-nx,s.y-ny)]
def cap_pts(t,N=24):
    s,e,w=t.GetStart(),t.GetEnd(),t.GetWidth(); dx,dy=e.x-s.x,e.y-s.y; L=math.hypot(dx,dy); r=w/2.0
    ux,uy=dx/L,dy/L; nx,ny=-uy,ux
    pts=[]; a0=math.atan2(ny,nx)
    for i in range(N+1):
        a=a0-math.pi*i/N; pts.append((e.x+r*math.cos(a), e.y+r*math.sin(a)))
    a1=math.atan2(-ny,-nx)
    for i in range(N+1):
        a=a1-math.pi*i/N; pts.append((s.x+r*math.cos(a), s.y+r*math.sin(a)))
    return pts
def cover(body,plane,area):
    if plane is None: return None
    rem=pcbnew.SHAPE_POLY_SET(body); rem.BooleanSubtract(plane)
    if rem.OutlineCount()==0: return 1.0
    return 1.0-(abs(rem.Area())/area if area else 0.0)
segs=[t for t in bd.GetTracks() if t.Type()==pcbnew.PCB_TRACE_T and t.GetNetname().startswith('PCIE_')]
stat={'rect':{'full':0,'area':0.0,'gap_area':0.0,'gap_segs':[]},'cap':{'full':0,'area':0.0,'gap_area':0.0}}
for t in segs:
    lay=t.GetLayer(); ab,be=nearest(lay,-1),nearest(lay,+1)
    res={}
    for tag,pts in (('rect',rect_pts(t)),('cap',cap_pts(t))):
        body=poly(pts); area=abs(body.Area()); covs=[]
        for pl in (ab,be):
            if pl is None: continue
            c=cover(body,planes[pl],area)
            if c is not None: covs.append((pl,c))
        best=max([c for _,c in covs] or [0.0])
        res[tag]=(best,area)
        stat[tag]['area']+=area
        if best>=1.0-1e-9: stat[tag]['full']+=1
        else: stat[tag]['gap_area']+=area*(1.0-best)
    if res['rect'][0]<1.0-1e-9 and res['cap'][0]>=1.0-1e-9:
        stat['rect']['gap_segs'].append({'net':t.GetNetname(),'layer':pcbnew.LayerName(lay),
            'start_mm':[round(t.GetStart().x/NM,3),round(t.GetStart().y/NM,3)],
            'end_mm':[round(t.GetEnd().x/NM,3),round(t.GetEnd().y/NM,3)],
            'rect_cov':round(res['rect'][0],6),'cap_cov':round(res['cap'][0],6)})
n=len(segs)
out={'board':BOARD,'board_sha16':hashlib.sha256(open(BOARD,'rb').read()).hexdigest()[:16],'n_segments':n,
     'rect_caliber':{'n_full':stat['rect']['full'],'pct':round(100*stat['rect']['full']/n,3),
                     'area_mm2':round(stat['rect']['area']/NM/NM,4),'gap_area_mm2':round(stat['rect']['gap_area']/NM/NM,4)},
     'capsule_caliber':{'n_full':stat['cap']['full'],'pct':round(100*stat['cap']['full']/n,3),
                        'area_mm2':round(stat['cap']['area']/NM/NM,4),'gap_area_mm2':round(stat['cap']['gap_area']/NM/NM,4)},
     'rect_only_gaps_n':len(stat['rect']['gap_segs']),'rect_only_gaps_sample':stat['rect']['gap_segs'][:10]}
json.dump(out,open(OUT,'w'),ensure_ascii=False,indent=1)
print(json.dumps({k:v for k,v in out.items() if k!='rect_only_gaps_sample'},ensure_ascii=False,indent=1))
