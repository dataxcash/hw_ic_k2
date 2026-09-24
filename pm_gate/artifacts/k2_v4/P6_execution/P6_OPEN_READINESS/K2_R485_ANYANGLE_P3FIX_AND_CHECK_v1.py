"""P3 图纸核（走廊段·定稿）：any-angle 扇入 + 三处根因修正，构造与独立核同脚本，只执行一次。
修正：① ci 东移出西侧障碍块（仅 OUT0_N 需移）；② 门列 x>=136.2 且 **e 与 px 同序**（R482 该项写反）；
     ③ 斜段沿用 s、e 同向递减（保证不相交），逐对核端点距>=0.435 且不相交。
仅核走廊段（A→下落→斜段→水平→门列北上至 y=55.0）；北侧段另件。只读几何，不打求解器。"""
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
names=sorted(A,key=lambda z:A[z][0])                 # 按 A.x 升序
F=[67.83,67.39,66.95,66.51,66.07,65.63,65.19,64.75,64.31,63.87,62.67,61.31,60.87,59.67,58.34,57.90]
P=0.435; CI_MIN=85.45
def clear(x1,y1,x2,y2,step=0.04):
    L=math.dist((x1,y1),(x2,y2)); k=max(2,int(L/step)+1)
    xs=np.linspace(x1,x2,k); ys=np.linspace(y1,y2,k)
    i=np.rint((xs-rast.X0)/rast.step).astype(int); j=np.rint((ys-rast.Y0)/rast.step).astype(int)
    ok=(i>=0)&(i<rast.NX)&(j>=0)&(j<rast.NY)
    return bool(ok.all()) and (not bad[i[ok],j[ok]].any())
def seg_min(s1,s2):
    (a,b),(c,d)=s1,s2
    def pd(p,q,r):
        vx,vy=r[0]-q[0],r[1]-q[1]; wx,wy=p[0]-q[0],p[1]-q[1]; L2=vx*vx+vy*vy
        t=0.0 if L2==0 else max(0.0,min(1.0,(wx*vx+wy*vy)/L2))
        return math.dist(p,(q[0]+t*vx,q[1]+t*vy))
    def cross(p1,p2,p3,p4):
        def o(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        o1,o2,o3,o4=o(p1,p2,p3),o(p1,p2,p4),o(p3,p4,p1),o(p3,p4,p2)
        return (o1>0)!=(o2>0) and (o3>0)!=(o4>0)
    if cross(a,b,c,d): return 0.0
    return min(pd(a,c,d),pd(b,c,d),pd(c,a,b),pd(d,a,b))
routes={}; fails=[]
for u,nm in enumerate(names):                        # u=0..15
    ax,ay=A[nm]
    ci=max(ax,CI_MIN)                                # 修正①：西端东移出障碍块
    s=round(66.9-P*u,3)                              # s 随 u 递减（与 ci 反序）
    e=F[u]                                           # e 随 u 递减
    xe=129.0 if e>67.13 else 126.5
    px=round(142.725-P*u,3)                          # 修正②：p 与 e 同序（= 门列自东向西）
    pts=[(ax,ay),(ci,ay),(ci,s),(xe,e),(px,e),(px,55.0)]
    o=[pts[0]]
    for q in pts[1:]:
        if math.dist(q,o[-1])>1e-9: o.append(q)
    routes[nm]=o
    for k in range(len(o)-1):
        if not clear(*o[k],*o[k+1]): fails.append((nm,k,o[k],o[k+1]))
segs={nm:[((o[k][0],o[k][1]),(o[k+1][0],o[k+1][1])) for k in range(len(o)-1)] for nm,o in routes.items()}
ks=sorted(segs); pv=[]; worst=(1e9,None)
for i in range(len(ks)):
    for j in range(i+1,len(ks)):
        d=min(seg_min(a,b) for a in segs[ks[i]] for b in segs[ks[j]])
        if d<worst[0]: worst=(d,(ks[i],ks[j]))
        if d<P-1e-6: pv.append((ks[i],ks[j],round(d,4)))
out={"n_clear_fail":len(fails),"clear_fail":[[f[0],f[1],list(f[2]),list(f[3])] for f in fails[:6]],
     "pair_min_mm":round(worst[0],4),"pair_min_of":worst[1],"n_pair_viol":len(pv),"pair_viol":pv[:8],
     "pass":(len(fails)==0 and len(pv)==0)}
print(json.dumps(out,ensure_ascii=False,indent=1))
json.dump({"routes":routes,"out":out},open("/tmp/opencode/r485/p3fix.json","w"),ensure_ascii=False,default=str)
