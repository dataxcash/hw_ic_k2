"""P3 证明级（定稿 · 一次执行）：CP-SAT 全局单模型（序变量+AllDifferent+单调，承 R455/R362）。
ci=实测净竖列(定标1000) · s=走廊行高(候选 0.435 步) · e=夹缝层位(0..15 升序) · p 由 e 导出(保证 e/p 同序)。
约束：ci/s/e 互异且 **ci,s,e 同序**（⇒ 斜段互不相交、竖列不被初段横穿）；|ci|≥0.435。解出 → 独立核。"""
import json,sys,math
sys.path.insert(0,"/home/fila/jqdDev_2025/ic_hw/k2/tools")
import numpy as np
from ortools.sat.python import cp_model
from k2_p4_b2_in5_lane_router_v3 import Raster, build_base, lane_anchors
import k2_p4_b2_in5_lane_router_v3 as RT
RT.PAD_EXTRA=0.100+0.5*0.03*math.sqrt(2)
m=json.load(open("/tmp/opencode/archer/model_l8.json"))
an=[a for a in lane_anchors(m) if a["net"].startswith("PCIE_UP_OUT")]
rast=Raster(m["bbox"],0.03); bad=build_base(rast,m,"In5.Cu",set(),set(),0.08,frozenset())
A={a["net"]:a["A"] for a in an}; names=sorted(A,key=lambda z:A[z][0])
P=0.435; YE=56.6; SC=1000; N=len(names)
F=[round(57.90+0,2),58.34,59.67,60.87,61.31,62.67,63.87,64.31,64.75,65.19,65.63,66.07,66.51,66.95,67.39,67.83]
def clear(x1,y1,x2,y2,step=0.05):
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
CAND=[]
for nm in names:
    ax,ay=A[nm]; cs=[]; x=round(ax,3)
    while x<=ax+2.4:
        if clear(x,YE,x,67.0) and clear(ax,ay,x,YE): cs.append(int(round(x*SC)))
        x=round(x+0.05,3)
    CAND.append(cs)
LV=[int(round((57.0+0.435*k)*SC)) for k in range(22)]
mo=cp_model.CpModel()
ci={i:mo.NewIntVarFromDomain(cp_model.Domain.FromValues(CAND[i]),"ci%d"%i) for i in range(N)}
si={i:mo.NewIntVarFromDomain(cp_model.Domain.FromValues(LV),"s%d"%i) for i in range(N)}
ei={i:mo.NewIntVar(0,15,"e%d"%i) for i in range(N)}
mo.AddAllDifferent([ci[i] for i in range(N)]); mo.AddAllDifferent([si[i] for i in range(N)]); mo.AddAllDifferent([ei[i] for i in range(N)])
for i in range(N):
    for j in range(i+1,N):
        a=mo.NewBoolVar("a%d_%d"%(i,j)); b=mo.NewBoolVar("b%d_%d"%(i,j))
        mo.Add(ci[i]-ci[j]>=435).OnlyEnforceIf(a); mo.Add(ci[j]-ci[i]>=435).OnlyEnforceIf(a.Not())
        mo.Add(si[i]-si[j]>=1).OnlyEnforceIf(b); mo.Add(si[j]-si[i]>=1).OnlyEnforceIf(b.Not())
        g=mo.NewBoolVar("g%d_%d"%(i,j))          # g ⟺ ci_i < ci_j
        mo.Add(ci[i]<ci[j]).OnlyEnforceIf(g); mo.Add(ci[i]>ci[j]).OnlyEnforceIf(g.Not())
        mo.Add(si[i]<si[j]).OnlyEnforceIf(g); mo.Add(si[i]>si[j]).OnlyEnforceIf(g.Not())
        mo.Add(ei[i]<ei[j]).OnlyEnforceIf(g); mo.Add(ei[i]>ei[j]).OnlyEnforceIf(g.Not())
sv=cp_model.CpSolver(); sv.parameters.max_time_in_seconds=300.0; sv.parameters.num_search_workers=8
st=sv.Solve(mo); print("STATUS",sv.StatusName(st))
if st in (cp_model.OPTIMAL,cp_model.FEASIBLE):
    sol=[]
    for i in range(N):
        sol.append(dict(nm=names[i],ax=A[names[i]][0],ay=A[names[i]][1],ci=sv.Value(ci[i])/SC,s=sv.Value(si[i])/SC,e=sv.Value(ei[i])))
    order=sorted(range(N),key=lambda i:sol[i]["ci"]); rank={order[k]:k for k in range(N)}
    routes={};fails=[]
    for i,d in enumerate(sol):
        r=rank[i]; xe=round(118.0+0.5*r,2); ev=F[d["e"]]; px=round(136.2+0.435*d["e"],3)
        pts=[(d["ax"],d["ay"]),(d["ci"],YE),(d["ci"],d["s"]),(xe,ev),(px,ev),(px,55.0)]
        o=[pts[0]]
        for q in pts[1:]:
            if math.dist(q,o[-1])>1e-9: o.append(q)
        routes[d["nm"]]=o
        for k in range(len(o)-1):
            if not clear(*o[k],*o[k+1]): fails.append([d["nm"],k,list(o[k]),list(o[k+1])])
    segs={nm:[((o[k][0],o[k][1]),(o[k+1][0],o[k+1][1])) for k in range(len(o)-1)] for nm,o in routes.items()}
    ks=sorted(segs);pv=[];worst=(1e9,None)
    for i2 in range(len(ks)):
        for j2 in range(i2+1,len(ks)):
            dd=min(smin(a,b) for a in segs[ks[i2]] for b in segs[ks[j2]])
            if dd<worst[0]: worst=(dd,(ks[i2],ks[j2]))
            if dd<P-1e-6: pv.append([ks[i2],ks[j2],round(dd,4)])
    out={"status":sv.StatusName(st),"n_clear_fail":len(fails),"clear_fail":fails[:6],
         "pair_min_mm":round(worst[0],4),"pair_min_of":worst[1],"n_pair_viol":len(pv),"pair_viol":pv[:10],
         "pass":(len(fails)==0 and len(pv)==0),
         "assignment":[{"nm":d["nm"],"ci":d["ci"],"s":d["s"],"e":F[d["e"]]} for d in sol]}
    print(json.dumps(out,ensure_ascii=False,indent=1))
    json.dump({"routes":routes,"out":out},open("/tmp/opencode/r490/proof.json","w"),ensure_ascii=False,default=str)
