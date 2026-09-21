#!/usr/bin/env python3
"""R261 · 标准 PathFinder（协商拥塞 + 历史 + 全量 rip-up）· 保留半径 = pitch/2。
用法: pf2.py <out.json> [cell] [iters] [seed]"""
import json, math, sys, time
import numpy as np, importlib.util
from scipy.sparse.csgraph import dijkstra
from scipy.ndimage import distance_transform_edt
HERE="/home/fila/jqdDev_2025/ic_hw/k2"
spec=importlib.util.spec_from_file_location("v3m",HERE+"/tools/k2_p4_b2_in5_lane_router_v3.py")
v3=importlib.util.module_from_spec(spec); spec.loader.exec_module(v3)
LANES=[f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N","P")]
LS=set(LANES)
v3.is_lane=lambda n:n in LS
_o=v3.req; v3.req=lambda n:(0.175 if n in LS else _o(n))
v3.PAD_EXTRA=0.100
OUT=sys.argv[1]; CELL=float(sys.argv[2]); ITERS=int(sys.argv[3]); SEED=int(sys.argv[4])
HW=0.08; PITCH=0.435; RES=PITCH/2.0
model=json.load(open("/tmp/opencode/archer/model_crop.json"))
A=json.load(open("/tmp/opencode/archer/sites_phys.json")); B=json.load(open("/tmp/opencode/archer/sites_b_board_v1.json"))
rast=v3.Raster(model["bbox"],CELL); anchors=v3.lane_anchors(model)
for an in anchors: an["A"]=tuple(A[an["net"]]); an["B"]=tuple(B[an["net"]])
base=v3.build_base(rast,model,"In5.Cu",frozenset(),frozenset(),HW,frozenset())
c_all,own=v3.anchor_keepout(rast,anchors,HW)
free=(~base); NX,NY=free.shape; x0,y0=model["bbox"][0],model["bbox"][1]
G,idx=v3.build_topology(free,CELL); coo=G.tocoo()
ES=coo.row.astype(np.int64); ET=coo.col.astype(np.int64); ED=coo.data.astype(np.float64)
print("cell",CELL,"free",int(free.sum()),"res_rad",RES,flush=True)
def cix(x,y): return int(round((x-x0)/CELL)),int(round((y-y0)/CELL))
def dil(m,rad):
    if not m.any(): return np.zeros_like(m,bool)
    return distance_transform_edt(~m,sampling=(CELL,CELL))<=rad
def cells_of(flat):
    ii,jj=np.nonzero(free); return [(int(ii[k]),int(jj[k])) for k in flat]
def mask_of(flat):
    m=np.zeros((NX,NY),bool)
    for (i,j) in cells_of(flat): m[i,j]=True
    return m
anchor_ko=[]
for an in anchors:
    bad=(c_all-own[an["net"]].astype(np.int16))>0
    anchor_ko.append(bad)
KO={an["net"]:bad for an,bad in zip(anchors,anchor_ko)}
def route(nm,cost2d):
    cv=cost2d[free].astype(np.float64)
    G.data=ED*(0.5*(cv[ES]+cv[ET]))
    an=[a for a in anchors if a["net"]==nm][0]
    si,sj=cix(*an["A"]); gi,gj=cix(*an["B"])
    if not(free[si,sj] and free[gi,gj]): return None
    ns=idx[si,sj]; ng=idx[gi,gj]
    dist,pred=dijkstra(G,directed=True,indices=int(ns),return_predecessors=True)
    if not np.isfinite(dist[ng]): return None
    return v3.path_from_pred(pred,int(ns),int(ng))
rng=np.random.RandomState(SEED)
order=sorted(LANES,key=lambda n:(-B[n][1],-B[n][0]))
hist=np.zeros((NX,NY),np.float64)
pf=1.0; best=None; t0=time.time()
for it in range(ITERS):
    pres=np.zeros((NX,NY),np.float64); paths={}
    ord_it=list(order)
    if it>0: rng.shuffle(ord_it)
    for nm in ord_it:
        cost=np.ones((NX,NY))+pf*pres+hist
        cost[KO[nm]]=1e9
        pp=route(nm,cost)
        if pp is None: continue
        paths[nm]=pp
        pres+=dil(mask_of(pp),RES).astype(np.float64)
    over=np.maximum(0.0,pres-1.0)
    nov=int(over.sum())
    print("it %2d routed=%2d overuse=%.0f pf=%.2f t=%.0fs"%(it,len(paths),over.sum(),pf,time.time()-t0),flush=True)
    if best is None or (len(paths),-over.sum())>(best[0],-best[1]):
        best=(len(paths),over.sum(),{k:list(v) for k,v in paths.items()},it)
    if len(paths)==16 and nov==0: break
    hist+=over
    pf*=1.5
# 末闸
paths=best[2]
routes={}
for nm,pp in paths.items():
    an=[a for a in anchors if a["net"]==nm][0]
    pts=[tuple(an["A"])]+[(x0+i*CELL,y0+j*CELL) for (i,j) in cells_of(pp)]+[tuple(an["B"])]
    pts=v3.simplify(pts)
    routes[nm]={"pts":[[round(a,4),round(b,4)] for a,b in pts],
                "len_mm":round(sum(math.dist(pts[q],pts[q+1]) for q in range(len(pts)-1)),3)}
gate=v3.exact_gate(model,routes,anchors,"In5.Cu",HW,frozenset(),frozenset(),PITCH,frozenset())
print("BEST it=%d overuse=%.0f GATE %s"%(best[3],best[1],json.dumps({k:gate[k] for k in ("lane_pitch_min_gap_mm","n_lane_pitch_viol","clearance_min_mm","n_clearance_viol","endpoint_max_dev_mm")},ensure_ascii=False)),flush=True)
json.dump({"tool":"pf2_pathfinder","cell":CELL,"res_rad":RES,"iters":ITERS,"best_it":best[3],
           "overuse":best[1],"routes":routes,"gate":gate,
           "failed":sorted(LS-set(routes))},open(OUT,"w"),ensure_ascii=False,indent=1,sort_keys=True)
print("wrote",OUT)
