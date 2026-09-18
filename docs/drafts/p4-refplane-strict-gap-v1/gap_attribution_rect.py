"""V3 严口径缺口清单 + 守恒级归因（只读；复用 measure_ref_plane_continuity 同口径）。"""
import json, math, sys
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

planes={}; planes_nom={}
for lay in INNER:
    fl=_union(lay, lambda z: z.GetFilledPolysList(lay) if z.IsFilled() else None)
    if fl is not None: planes[lay]=fl
    nm=_union(lay, lambda z: z.Outline())
    if nm is not None: planes_nom[lay]=nm
idx={l:i for i,(n,l) in enumerate(STACK)}
def nearest(li,d):
    i=idx[li]+d
    while 0<=i<len(STACK):
        if STACK[i][1] in planes: return STACK[i][1]
        i+=d
    return None

def rect_poly(x0,y0,x1,y1):
    ps=pcbnew.SHAPE_POLY_SET(); ch=pcbnew.SHAPE_LINE_CHAIN()
    for x,y in ((x0,y0),(x1,y0),(x1,y1),(x0,y1)): ch.Append(int(x*NM),int(y*NM))
    ch.SetClosed(True); ps.AddOutline(ch); return ps

def seg_rect(t):
    s,e,w=t.GetStart(),t.GetEnd(),t.GetWidth()
    x1,y1,x2,y2=s.x,s.y,e.x,e.y
    dx,dy=x2-x1,y2-y1; L=math.hypot(dx,dy)
    if L==0: return None,0.0
    nx,ny=-dy/L*w/2.0, dx/L*w/2.0
    ps=pcbnew.SHAPE_POLY_SET(); ch=pcbnew.SHAPE_LINE_CHAIN()
    for x,y in ((x1+nx,y1+ny),(x2+nx,y2+ny),(x2-nx,y2-ny),(x1-nx,y1-ny)): ch.Append(int(x),int(y))
    ch.SetClosed(True); ps.AddOutline(ch); return ps,abs(ps.Area())

def cover(body,plane,area):
    if plane is None: return None
    rem=pcbnew.SHAPE_POLY_SET(body); rem.BooleanSubtract(plane)
    if rem.OutlineCount()==0: return 1.0
    return 1.0-(abs(rem.Area())/area if area else 0.0)

def residual(body,plane):
    rem=pcbnew.SHAPE_POLY_SET(body); rem.BooleanSubtract(plane); return rem

def isect_area(ps,poly):
    if ps is None or ps.OutlineCount()==0 or poly is None: return 0.0
    t=pcbnew.SHAPE_POLY_SET(ps); t.BooleanIntersection(poly); return abs(t.Area())

# 归因类别
import os as _os
_ROOT=_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))))
S=json.load(open(_os.path.join(_ROOT,'k2/pm_gate/artifacts/k2_v4/L3/SPEC_k2_v4.spec-rev-49.json')))
holes=[rect_poly(h['keepout_bbox'][0],h['keepout_bbox'][1],h['keepout_bbox'][2],h['keepout_bbox'][3])
       for h in S['mounting_holes']['holes']]
hole_union=None
for h in holes:
    if hole_union is None: hole_union=pcbnew.SHAPE_POLY_SET(h)
    else: hole_union.BooleanAdd(h)
bb=bd.GetBoardEdgesBoundingBox()
edge_out=rect_poly(pcbnew.ToMM(bb.GetLeft())-1,pcbnew.ToMM(bb.GetTop())-1,
                   pcbnew.ToMM(bb.GetRight())+1,pcbnew.ToMM(bb.GetBottom())+1)

segs=[t for t in bd.GetTracks() if t.Type()==pcbnew.PCB_TRACE_T and t.GetNetname().startswith('PCIE_')]
tot_area=0.0; cov_area=0.0; rows=[]; gaps=[]
cls={'hole_keepout':0.0,'plane_outside':0.0}
for t in segs:
    body,area=seg_rect(t)
    if body is None: continue
    tot_area+=area
    lay=t.GetLayer(); tags={}
    for tag,pl_lay in (('above',nearest(lay,-1)),('below',nearest(lay,+1))):
        tags[tag]=(pl_lay, cover(body,planes[pl_lay],area) if pl_lay else None)
    best_tag=None; best_cov=-1.0
    for tag,(pl_lay,cov) in tags.items():
        if cov is not None and cov>best_cov: best_tag,best_cov=tag,cov
    if best_tag is None:          # 无相邻平面（本板不出现）⇒ 记 0 覆盖
        best_tag='above'; best_cov=0.0
        tags['above']=(None,0.0)
    cov_area+=best_cov*area
    rec={'net':t.GetNetname(),'layer':pcbnew.LayerName(lay),'w_mm':round(t.GetWidth()/NM,3),
         'start_mm':[round(t.GetStart().x/NM,3),round(t.GetStart().y/NM,3)],
         'end_mm':[round(t.GetEnd().x/NM,3),round(t.GetEnd().y/NM,3)],
         'best_tag':best_tag,'best_cov':round(best_cov,6),
         'plane_mm':{k:(pcbnew.LayerName(v[0]) if v[0] else None) for k,v in tags.items()},
         'cov':{k:(None if v[1] is None else round(v[1],6)) for k,v in tags.items()}}
    if best_cov < 1.0-1e-9:
        pl=planes[tags[best_tag][0]] if tags[best_tag][0] in planes else None
        rem=residual(body,pl); rem_a=abs(rem.Area()) if rem.OutlineCount() else 0.0
        rec['residual_mm2']=round(rem_a/NM/NM,6)
        # 归因：孔 keepout ∩ 残差；板外 ∩ 残差；其余 = 反焊盘/分区/间隙
        _pll=tags[best_tag][0]
        inner=pcbnew.SHAPE_POLY_SET(planes_nom.get(_pll) or planes.get(_pll) or pcbnew.SHAPE_POLY_SET())
        outside=pcbnew.SHAPE_POLY_SET(edge_out)
        if inner.OutlineCount(): outside.BooleanSubtract(inner)
        a_hole=isect_area(rem,hole_union); a_out=isect_area(rem,outside)
        cls['hole_keepout']+=a_hole/NM/NM; cls['plane_outside']+=a_out/NM/NM
        rec['attr']={'hole_keepout_mm2':round(a_hole/NM/NM,6),'plane_outside_mm2':round(a_out/NM/NM,6),
                     'antipad_split_mm2':round((rem_a-a_hole-a_out)/NM/NM,6)}
        gaps.append(rec)
        rows.append(rec)
gap_area=tot_area-cov_area
sum_hole=cls['hole_keepout']; sum_out=cls['plane_outside']
sum_anti=sum(g['attr']['antipad_split_mm2'] for g in gaps)
gaps_sorted=sorted(gaps,key=lambda r:-r['residual_mm2'])
by_net={}
for g in gaps:
    by_net.setdefault(g['net'],{'segs':0,'residual_mm2':0.0,'min_cov':1.0,'layer':g['layer']})
    d=by_net[g['net']]; d['segs']+=1; d['residual_mm2']+=g['residual_mm2']; d['min_cov']=min(d['min_cov'],g['best_cov'])
by_layer={}
for g in gaps: by_layer[g['layer']]=by_layer.get(g['layer'],0)+1
res={'board':BOARD,'board_sha16':__import__('hashlib').sha256(open(BOARD,'rb').read()).hexdigest()[:16],
     'scope':{'net_prefix':'PCIE_','n_segments':len(rows)+ (len(segs)-len(rows)) },
     'totals':{'n_segments':len(segs),'n_full_cover_strict':len(segs)-len(gaps),'n_gap':len(gaps),
               'strict_full_cover_pct':round(100.0*(len(segs)-len(gaps))/len(segs),3),
               'area_total_mm2':round(tot_area/NM/NM,4),'area_covered_mm2':round(cov_area/NM/NM,4),
               'area_gap_mm2':round(gap_area/NM/NM,4)},
     'conservation':{'identity':'A_total = A_covered + A_gap',
                     'check_mm2':round((cov_area+gap_area-tot_area)/NM/NM,6),
                     'attribution':{'hole_keepout_mm2':round(sum_hole,4),'plane_outside_edge_mm2':round(sum_out,4),
                                    'antipad_clearance_split_mm2':round(sum_anti,4),
                                    'attributed_sum_mm2':round(sum_hole+sum_out+sum_anti,4),
                                    'residual_unattributed_mm2':round(gap_area/NM/NM-(sum_hole+sum_out+sum_anti),6)}},
     'gap_by_layer':by_layer,'gap_by_net_top':sorted(by_net.items(),key=lambda kv:-kv[1]['residual_mm2'])[:12],
     'gaps_top20':gaps_sorted[:20],'n_gaps_total':len(gaps),'gaps_all':gaps_sorted}
import csv as _csv
with open(OUT.replace('.json','_gap_list.csv'),'w',newline='') as fh:
    w=_csv.writer(fh); w.writerow(['net','layer','w_mm','x1','y1','x2','y2','best_plane','best_cov',
                                   'cov_above','cov_below','residual_mm2','attr_hole_mm2','attr_outside_mm2','attr_antipad_split_mm2'])
    for g in gaps_sorted:
        w.writerow([g['net'],g['layer'],g['w_mm'],g['start_mm'][0],g['start_mm'][1],g['end_mm'][0],g['end_mm'][1],
                    g['plane_mm'].get(g['best_tag']),g['best_cov'],g['cov'].get('above'),g['cov'].get('below'),
                    g['residual_mm2'],g['attr']['hole_keepout_mm2'],g['attr']['plane_outside_mm2'],g['attr']['antipad_split_mm2']])
print('csv rows:',len(gaps_sorted))
json.dump(res,open(OUT,'w'),ensure_ascii=False,indent=1)
print(json.dumps({k:res[k] for k in ('scope','totals','conservation','gap_by_layer')},ensure_ascii=False,indent=1))
print('top nets:'); [print('  ',n,d) for n,d in res['gap_by_net_top'][:8]]
print('top segs:'); [print('  ',g['net'],g['layer'],g['start_mm'],g['end_mm'],'cov=',g['best_cov'],'res=',g['residual_mm2'],g['attr']) for g in gaps_sorted[:8]]
