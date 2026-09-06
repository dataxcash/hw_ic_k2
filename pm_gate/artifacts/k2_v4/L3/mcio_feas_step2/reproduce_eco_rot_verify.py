import json, math
BM=json.load(open('/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/ds320pr1601_ballmap.json'))
R=json.load(open('/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/L3/mcio_feas_step2/per_ball_escape_6L_report.json'))
CX,CY=93.8,53.7
bm={e['name']:e for e in BM['ballmap']}
eng={e['name']:e for e in R['per_ball']}
def rots(x,y):
    return {'R0':(x,y),'R90':(-y,x),'R180':(-x,-y),'R270':(y,-x)}
def errs(Tname):
    T={'R0':lambda x,y:(x,y),'R90':lambda x,y:(-y,x),'R180':lambda x,y:(-x,-y),'R270':lambda x,y:(y,-x)}[Tname]
    tot=0; worst=0; per=[]
    for name,e in eng.items():
        b=bm[name]; ox,oy=T(b['x_mm'],b['y_mm'])
        ex,ey=e['bx']-CX, e['by']-CY
        d=math.hypot(ox-ex,oy-ey); tot+=d; worst=max(worst,d); per.append((name,d))
    return tot/len(per),worst, sorted(per,key=lambda z:-z[1])[:5]
for T in ['R0','R90','R180','R270']:
    a,w,top=errs(T)
    print(f'{T}: mean_err={a:.4f} worst={w:.4f}  worst-balls={[(n,round(d,3)) for n,d in top]}')
# engine target check: for lane-0-7 of band A_PER where does engine put host group vs each rot
def bandsum(Tname):
    T={'R0':lambda x,y:(x,y),'R90':lambda x,y:(-y,x),'R180':lambda x,y:(-x,-y),'R270':lambda x,y:(y,-x)}[Tname]
    import collections
    agg=collections.defaultdict(lambda:[0,0,0])
    for name,e in eng.items():
        b=bm[name]; band=e['band']
        if e['lane'] in (0,7):
            ox,oy=T(b['x_mm'],b['y_mm'])
            a=agg[band]; a[0]+=ox/8; a[1]+=oy/8
    for band,v in agg.items(): print(f'   {band} lane0-7 centroid {Tname}: ({v[0]:.2f},{v[1]:.2f}) board-rel')
print()
print('Engine per_ball actual centroid per band (board-rel):')
import collections
agg=collections.defaultdict(lambda:[0,0])
cnt=collections.defaultdict(int)
for name,e in eng.items():
    if e['lane'] in (0,7):
        a=agg[e['band']]; a[0]+=e['bx']-CX; a[1]+=e['by']-CY; cnt[e['band']]+=1
for band,(sx,sy) in agg.items(): print(f'   {band}: centroid ({sx/cnt[band]:.2f},{sy/cnt[band]:.2f})')
print()
for T in ['R0','R90','R180','R270']:
    print(f'centroids under real-placement {T}:')
    bandsum(T)
