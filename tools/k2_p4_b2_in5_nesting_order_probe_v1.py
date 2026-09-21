#!/usr/bin/env python3
"""R261 · 硬分离顺序布线器（构造式·可指定洋葱序）。用法: greedy_order.py <out> <order> <cell> <sep>"""
import json, math, sys, time
import numpy as np
import importlib.util
from scipy.sparse.csgraph import dijkstra
from scipy.ndimage import distance_transform_edt
HERE="/home/fila/jqdDev_2025/ic_hw/k2"
spec=importlib.util.spec_from_file_location("v3m",HERE+"/tools/k2_p4_b2_in5_lane_router_v3.py")
v3=importlib.util.module_from_spec(spec); spec.loader.exec_module(v3)
LANES=[f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N","P")]
LANESET=set(LANES)
v3.is_lane=lambda n: n in LANESET
_orig=v3.req
v3.req=lambda n:(0.175 if n in LANESET else _orig(n))
v3.PAD_EXTRA=0.100
MODEL="/tmp/opencode/archer/model_crop.json"
A=json.load(open("/tmp/opencode/archer/sites_phys.json")); B=json.load(open("/tmp/opencode/archer/sites_b_board_v1.json"))
OUT=sys.argv[1]; ORDER=sys.argv[2]; CELL=float(sys.argv[3]); SEP=float(sys.argv[4])
HW=0.08; PITCH=0.435; HALF=SEP
model=json.load(open(MODEL))
rast=v3.Raster(model["bbox"],CELL)
anchors=v3.lane_anchors(model)
for an in anchors:
    an["A"]=tuple(A[an["net"]]); an["B"]=tuple(B[an["net"]])
base=v3.build_base(rast,model,"In5.Cu",frozenset(),frozenset(),HW,frozenset())
c_all,own=v3.anchor_keepout(rast,anchors,HW)
free=(~base); NX,NY=free.shape; x0,y0=model["bbox"][0],model["bbox"][1]
G,idx=v3.build_topology(free,CELL); coo=G.tocoo()
ES=coo.row.astype(np.int64); ET=coo.col.astype(np.int64); ED=coo.data.astype(np.float64)
NF=int(free.sum()); print("cell",CELL,"free",NF,"nodes",int(idx.max())+1,flush=True)
def cellidx(x,y): return int(round((x-x0)/CELL)),int(round((y-y0)/CELL))
def route_one(nm,cost2d,hard2d):
    cv=cost2d[free].astype(np.float64).copy()
    if hard2d is not None and hard2d.any():
        cv[hard2d[free]]=np.inf
    G.data=ED*(0.5*(cv[ES]+cv[ET]))
    an=[a for a in anchors if a["net"]==nm][0]
    si,sj=cellidx(*an["A"]); gi,gj=cellidx(*an["B"])
    s=idx[si,sj]; g=idx[gi,gj]
    if s<0 or g<0: return None
    dist,pred=dijkstra(G,directed=True,indices=int(s),return_predecessors=True)
    if not np.isfinite(dist[g]): return None
    return v3.path_from_pred(pred,int(s),int(g))
def cells_of(flat):
    ii,jj=np.nonzero(free); return [(int(ii[k]),int(jj[k])) for k in flat]
def dil(m,rad):
    if not m.any(): return np.zeros_like(m,bool)
    return distance_transform_edt(~m,sampling=(CELL,CELL))<=rad
key={"Ax_asc":lambda n:(A[n][0],), "Ax_desc":lambda n:(-A[n][0],),
     "By_desc":lambda n:(-B[n][1],-B[n][0]), "By_asc":lambda n:(B[n][1],B[n][0])}[ORDER]
nets=sorted(LANES,key=key)
present_hard=np.zeros((NX,NY),bool); paths={}; t0=time.time()
for nm in nets:
    cost2d=np.ones((NX,NY))
    bad=((c_all-own[nm].astype(np.int16))>0)
    cost2d[bad]=1e9
    pp=route_one(nm,cost2d,present_hard)
    if pp is None:
        print("  FAIL %-28s routed=%2d"%(nm,len(paths)),flush=True); continue
    paths[nm]=pp
    m=np.zeros((NX,NY),bool)
    for (i,j) in cells_of(pp): m[i,j]=True
    present_hard|=dil(m,HALF)
    print("  ok %-28s routed=%2d t=%.0fs"%(nm,len(paths),time.time()-t0),flush=True)
routes={}
for nm,pp in paths.items():
    an=[a for a in anchors if a["net"]==nm][0]
    pts=[tuple(an["A"])]+[(x0+i*CELL,y0+j*CELL) for (i,j) in cells_of(pp)]+[tuple(an["B"])]
    pts=v3.simplify(pts)
    routes[nm]={"pts":[[round(a,4),round(b,4)] for a,b in pts],
                "len_mm":round(sum(math.dist(pts[q],pts[q+1]) for q in range(len(pts)-1)),3)}
gate=v3.exact_gate(model,routes,anchors,"In5.Cu",HW,frozenset(),frozenset(),PITCH,frozenset())
print("ORDER",ORDER,"cell",CELL,"sep",SEP,"routed",len(routes),"/16")
print("GATE",json.dumps({k:gate[k] for k in ("lane_pitch_min_gap_mm","n_lane_pitch_viol","clearance_min_mm","n_clearance_viol","endpoint_max_dev_mm")},ensure_ascii=False))
json.dump({"order":ORDER,"cell":CELL,"sep":SEP,"routes":routes,"gate":gate},open(OUT,"w"),ensure_ascii=False,indent=1,sort_keys=True)
print("wrote",OUT)
