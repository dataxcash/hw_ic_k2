"""P3 单发（定稿·一次执行）：锚区**斜段逃逸**（解 OUT0_N 夹死）+ 链式槽位 + 膝点 + 端点错开。
只核走廊段(A→斜逃逸→下落→走廊斜段→水平→门列北上至 y=55.0)。只读几何，不打求解器。"""
import json,sys,math
sys.path.insert(0,"/home/fila/jqdDev_2025/ic_hw/k2/tools")
import numpy as np
from k2_p4_b2_in5_lane_router_v3 import Raster, build_base, lane_anchors
import k2_p4_b2_in5_lane_router_v3 as RT
RT.PAD_EXTRA=0.100+0.5*0.03*math.sqrt(2)
m=json.load(open("/tmp/opencode/archer/model_l8.json"))
an=[a for a in lane_anchors(m) if a["net"].startswith("PCIE_UP_OUT")]
rast=Raster(m["bbox"],0.03); bad=build_base(rast,m,"In5.Cu",set(),set(),0.08,frozenset())
A={a["net"]:a["A"] for a in an}
names=sorted(A,key=lambda z:A[z][0]); P=0.435
F=[67.83,67.39,66.95,66.51,66.07,65.63,65.19,64.75,64.31,63.87,62.67,61.31,60.87,59.67,58.34,57.90]
def clear(x1,y1,x2,y2,step=0.04):
    L=math.dist((x1,y1),(x2,y2)); k=max(2,int(L/step)+1)
    xs=np.linspace(x1,x2,k); ys=np.linspace(y1,y2,k)
    i=np.rint((xs-rast.X0)/rast.step).astype(int); j=np.rint((ys-rast.Y0)/rast.step).astype(int)
    ok=(i>=0)&(i<rast.NX)&(j>=0)&(j<rast.NY)
    return bool(ok.all()) and (not bad[i[ok],j[ok]].any())
def smin(s1,s2):
    (a,b),(c,d)=s1,s2
    def pd(p,q,r):
        vx,vy=r[0]-q[0],r[1]-q[1]; wx,wy=p[0]-q[0],p[1]-q[1]; L2=vx*vx+vy*vy
        t=0.0 if L2==0 else max(0.0,min(1.0,(wx*vx+wy*vy)/L2))
        return math.dist(p,(q[0]+t*vx,q[1]+t*vy))
    def o(p1,p2,p3): return (p2[0]-p1[0])*(p3[1]-p1[1])-(p2[1]-p1[1])*(p3[0]-p1[0])
    if ((o(a,b,c)>0)!=(o(a,b,d)>0)) and ((o(c,d,a)>0)!=(o(c,d,b)>0)): return 0.0
    return min(pd(a,c,d),pd(b,c,d),pd(c,a,b),pd(d,a,b))
YF=56.6   # 逃逸后高度（锚区下沿：实测 y<=56.6 时 x>=84.14 全通）
routes={};fails=[];ci_used={}
for i,nm in enumerate(names):
    ax,ay=A[nm]; ci=round(ax+0.55,3); ci_used[nm]=ci
    s=round(66.0-0.6*i,3); e=F[i]
    xe=round(120.0+0.5*i,2) if e<=67.13 else 129.0
    px=round(142.725-P*i,3)
    pts=[(ax,ay),(ci,YF),(ci,s)]
    if e>67.13: pts+=[(124.5,66.6),(xe,e)]
    else: pts+=[(xe,e)]
    pts+=[(px,e),(px,55.0)]
    o=[pts[0]]
    for q in pts[1:]:
        if math.dist(q,o[-1])>1e-9: o.append(q)
    routes[nm]=o
    for k in range(len(o)-1):
        if not clear(*o[k],*o[k+1]): fails.append([nm,k,list(o[k]),list(o[k+1])])
segs={nm:[((o[k][0],o[k][1]),(o[k+1][0],o[k+1][1])) for k in range(len(o)-1)] for nm,o in routes.items()}
ks=sorted(segs);pv=[];worst=(1e9,None)
for i in range(len(ks)):
    for j in range(i+1,len(ks)):
        d=min(smin(a,b) for a in segs[ks[i]] for b in segs[ks[j]])
        if d<worst[0]: worst=(d,(ks[i],ks[j]))
        if d<P-1e-6: pv.append([ks[i],ks[j],round(d,4)])
out={"n_clear_fail":len(fails),"clear_fail":fails[:6],"pair_min_mm":round(worst[0],4),
     "pair_min_of":worst[1],"n_pair_viol":len(pv),"pair_viol":pv[:10],
     "pass":(len(fails)==0 and len(pv)==0)}
print(json.dumps(out,ensure_ascii=False,indent=1))
json.dump({"routes":routes,"out":out},open("/tmp/opencode/r488/gate.json","w"),ensure_ascii=False,default=str)
