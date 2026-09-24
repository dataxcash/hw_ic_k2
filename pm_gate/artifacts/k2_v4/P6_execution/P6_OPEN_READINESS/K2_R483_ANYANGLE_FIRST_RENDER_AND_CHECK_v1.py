"""P3 图纸核（走廊段）：any-angle 扇入首段 —— 独立核（栅格净距 + 两两中心距）。只读几何，不打求解器。"""
import json,sys,math
sys.path.insert(0,"/home/fila/jqdDev_2025/ic_hw/k2/tools")
import numpy as np
from k2_p4_b2_in5_lane_router_v3 import Raster, build_base, lane_anchors
import k2_p4_b2_in5_lane_router_v3 as RT
RT.PAD_EXTRA=0.100+0.5*0.03*math.sqrt(2)
m=json.load(open("/tmp/opencode/archer/model_l8.json"))
an=[a for a in lane_anchors(m) if a["net"].startswith("PCIE_UP_OUT")]
rast=Raster(m["bbox"],0.03); bad=build_base(rast,m,"In5.Cu",set(),set(),0.08,frozenset())
A={a["net"]:a["A"] for a in an}; B={a["net"]:a["B"] for a in an}
names=sorted(A,key=lambda z:A[z][0])          # u=1..16 by A.x
F=[67.83,67.39,66.95,66.51,66.07,65.63,65.19,64.75,64.31,63.87,62.67,61.31,60.87,59.67,58.34,57.90]
P=0.435; STEP=0.05
def clear(x1,y1,x2,y2):
    L=math.dist((x1,y1),(x2,y2)); k=max(2,int(L/STEP)+1)
    xs=np.linspace(x1,x2,k); ys=np.linspace(y1,y2,k)
    i=np.rint((xs-rast.X0)/rast.step).astype(int); j=np.rint((ys-rast.Y0)/rast.step).astype(int)
    ok=(i>=0)&(i<rast.NX)&(j>=0)&(j<rast.NY)
    if not ok.all(): return False
    return not bad[i[ok],j[ok]].any()
def seg_dist(s1,s2):
    (a,b),(c,d)=s1,s2
    def pd(p,q,r):
        vx,vy=r[0]-q[0],r[1]-q[1]; wx,wy=p[0]-q[0],p[1]-q[1]
        L2=vx*vx+vy*vy
        t=0 if L2==0 else max(0,min(1,(wx*vx+wy*vy)/L2))
        return math.dist(p,(q[0]+t*vx,q[1]+t*vy))
    def inter(p1,p2,p3,p4):
        d1=(p2[0]-p1[0])*(p3[1]-p1[1])-(p2[1]-p1[1])*(p3[0]-p1[0])
        d2=(p2[0]-p1[0])*(p4[1]-p1[1])-(p2[1]-p1[1])*(p4[0]-p1[0])
        d3=(p4[0]-p3[0])*(p1[1]-p3[1])-(p4[1]-p3[1])*(p1[0]-p3[0])
        d4=(p4[0]-p3[0])*(p2[1]-p3[1])-(p4[1]-p3[1])*(p2[0]-p3[0])
        return ((d1>0)!=(d2>0)) and ((d3>0)!=(d4>0))
    if inter(a,b,c,d): return 0.0
    return min(pd(a,c,d),pd(b,c,d),pd(c,a,b),pd(d,a,b))
routes={}
NC={"clear_fail":[],"seg_min":1e9}
for u,nm in enumerate(names):
    ax,ay=A[nm]; bx,by=B[nm]
    s=round(66.5-P*(u-1),3); e=F[u-1]
    xe=129.0 if e>67.13 else 126.5
    p=0.435
    px=round(136.2+P*(u-1),3)
    pts=[(ax,ay),(ax,s),(xe,e),(px,e),(px,55.0)]
    o=[pts[0]]
    for q in pts[1:]:
        if math.dist(q,o[-1])>1e-9: o.append(q)
    routes[nm]=o
    for k in range(len(o)-1):
        if not clear(*o[k],*o[k+1]): NC["clear_fail"].append((nm,k,o[k],o[k+1]))
segs={}
for nm,o in routes.items():
    segs[nm]=[((o[k][0],o[k][1]),(o[k+1][0],o[k+1][1])) for k in range(len(o)-1)]
ks=sorted(segs); worst=(1e9,None)
for i in range(len(ks)):
    for j in range(i+1,len(ks)):
        d=min(seg_dist(a,b) for a in segs[ks[i]] for b in segs[ks[j]])
        if d<worst[0]: worst=(d,(ks[i],ks[j]))
        if d<P-1e-6: NC.setdefault("pair_viol",[]).append((ks[i],ks[j],round(d,4)))
out={"n_lanes":len(names),"clear_fail":NC["clear_fail"][:6],"n_clear_fail":len(NC["clear_fail"]),
     "pair_min_mm":round(worst[0],4),"pair_min_of":worst[1],
     "n_pair_viol":len(NC.get("pair_viol",[])),"pair_viol":NC.get("pair_viol",[])[:8]}
print(json.dumps(out,ensure_ascii=False,indent=1,default=str))
json.dump({"routes":routes,"out":out},open("/tmp/opencode/r483/fan.json","w"),ensure_ascii=False,default=str)
