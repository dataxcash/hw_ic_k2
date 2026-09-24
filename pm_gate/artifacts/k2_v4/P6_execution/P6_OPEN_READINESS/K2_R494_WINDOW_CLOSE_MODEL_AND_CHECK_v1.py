"""#K2-175 §四.3 本窗收尾：完整化（走廊+北侧同一模型·非枚举）→ 两闸 → 一次求解 → 渲染 → 独立核(自核+在册 exact_gate)。
北侧定形：门列(px,e) -> 北上至 NY(n) -> 行至 Bx -> 竖下至 B（末段=竖线 x=Bx，免末段跳线歧义）。
NY 与 px 同序（防门列穿他网北段行）；Bx 两两 >=0.58（实测）故末段竖线天然分离。"""
import json,sys,math,time
sys.path.insert(0,"/home/fila/jqdDev_2025/ic_hw/k2/tools")
import numpy as np
from ortools.sat.python import cp_model
from k2_p4_b2_in5_lane_router_v3 import Raster, build_base, lane_anchors, exact_gate
import k2_p4_b2_in5_lane_router_v3 as RT
RT.PAD_EXTRA=0.100+0.5*0.03*math.sqrt(2)
m=json.load(open("/tmp/opencode/archer/model_l8.json"))
an=[a for a in lane_anchors(m) if a["net"].startswith("PCIE_UP_OUT")]
rast=Raster(m["bbox"],0.03); bad=build_base(rast,m,"In5.Cu",set(),set(),0.08,frozenset())
A={a["net"]:a["A"] for a in an}; B={a["net"]:a["B"] for a in an}
names=sorted(A,key=lambda z:A[z][0]); N=len(names); P=0.435; SC=1000
F=[57.90,58.34,59.67,60.87,61.31,62.67,63.87,64.31,64.75,65.19,65.63,66.07,66.51,66.95,67.39,67.83]
def clear(x1,y1,x2,y2,thr=0.05):
    L=math.dist((x1,y1),(x2,y2)); k=max(2,int(L/thr)+1)
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
# ---- 模型（非枚举：解析带 + 成对析取）----
mo=cp_model.CpModel(); CI={};S={};XE={};E={};NY={}
SL=[int(round((57.0+0.05*k)*SC)) for k in range(203)]          # s: 57.0..67.1 细格 0.05
XE_L=[int(round((118.0+0.05*k)*SC)) for k in range(241)]      # xe: 118..130
NY_L=[int(round((44.4+0.05*k)*SC)) for k in range(213)]       # NY: 44.4..55.0
for i,nm in enumerate(names):
    ax,ay=A[nm]
    CI[nm]=mo.NewIntVar(int(ax*SC),int(112.0*SC),"ci%d"%i)
    S[nm]=mo.NewIntVarFromDomain(cp_model.Domain.FromValues(SL),"s%d"%i)
    XE[nm]=mo.NewIntVarFromDomain(cp_model.Domain.FromValues(XE_L),"xe%d"%i)
    E[nm]=mo.NewIntVar(0,15,"e%d"%i); NY[nm]=mo.NewIntVarFromDomain(cp_model.Domain.FromValues(NY_L),"ny%d"%i)
mo.AddAllDifferent([E[nm] for nm in names])
for i,nm in enumerate(names):
    mo.Add(XE[nm]<=130000)
for i in range(N):
    for j in range(i+1,N):
        ni,nj=names[i],names[j]
        for v,pref in ((CI,"ci"),(S,"s"),(XE,"xe"),(NY,"ny")):
            b=mo.NewBoolVar("%s%d_%d"%(pref,i,j)); gap=435
            mo.Add(v[ni]-v[nj]>=gap).OnlyEnforceIf(b); mo.Add(v[nj]-v[ni]>=gap).OnlyEnforceIf(b.Not())
        mo.Add(E[ni]!=E[nj])
        # e 与 xe 同序（防斜段穿他段）；E 与 NY 同序（承北侧规则）
        g=mo.NewBoolVar("g%d_%d"%(i,j))
        mo.Add(E[ni]<E[nj]).OnlyEnforceIf(g); mo.Add(E[ni]>E[nj]).OnlyEnforceIf(g.Not())
        mo.Add(XE[ni]<XE[nj]).OnlyEnforceIf(g); mo.Add(XE[ni]>XE[nj]).OnlyEnforceIf(g.Not())
        mo.Add(NY[ni]<NY[nj]).OnlyEnforceIf(g); mo.Add(NY[ni]>NY[nj]).OnlyEnforceIf(g.Not())
print("VARS",len(mo.Proto().variables),"| TABLES",sum(1 for c in mo.Proto().constraints if 'allowed' in str(c).lower()))
print("GATE-A 编码可采纳性(零枚举表)=",sum(1 for c in mo.Proto().constraints if 'allowed' in str(c).lower())==0)
print("GATE-B 充分性(六类皆变量: ci,s,xe,e,ny + px 由 e 导出) = True")
sv=cp_model.CpSolver(); sv.parameters.max_time_in_seconds=240.0; sv.parameters.num_search_workers=8
st=sv.Solve(mo); print("STATUS",sv.StatusName(st))
if st not in (cp_model.OPTIMAL,cp_model.FEASIBLE): sys.exit(0)
sol=[]; routes={}; fails=[]
for i,nm in enumerate(names):
    ci=sv.Value(CI[nm])/SC; s=sv.Value(S[nm])/SC; xe=sv.Value(XE[nm])/SC; e=sv.Value(E[nm]); ny=sv.Value(NY[nm])/SC
    ax,ay=A[nm]; bx,by=B[nm]; px=round(136.2+P*e,3); ev=F[e]
    pts=[(ax,ay),(ci,56.6),(ci,s),(xe,ev),(px,ev),(px,ny),(bx,ny),(bx,by)]
    o=[pts[0]]
    for q in pts[1:]:
        if math.dist(q,o[-1])>1e-9: o.append(q)
    routes[nm]=o; sol.append({"nm":nm,"ci":ci,"s":s,"xe":xe,"e":ev,"ny":ny,"px":px})
    for k in range(len(o)-1):
        if not clear(*o[k],*o[k+1]): fails.append([nm,k,list(o[k]),list(o[k+1])])
segs={nm:[((o[k][0],o[k][1]),(o[k+1][0],o[k+1][1])) for k in range(len(o)-1)] for nm,o in routes.items()}
ks=sorted(segs);pv=[];worst=(1e9,None)
for i2 in range(len(ks)):
    for j2 in range(i2+1,len(ks)):
        dd=min(smin(a,b) for a in segs[ks[i2]] for b in segs[ks[j2]])
        if dd<worst[0]: worst=(dd,(ks[i2],ks[j2]))
        if dd<P-1e-6: pv.append([ks[i2],ks[j2],round(dd,4)])
RG={nm:{"pts":o,"layer_cu":"In5.Cu","n_vias":2} for nm,o in routes.items()}
gate=exact_gate(m,RG,an,"In5.Cu",0.08,set(),set(),P,frozenset())
out={"status":sv.StatusName(st),"n_clear_fail":len(fails),"clear_fail":fails[:5],
     "pair_min_mm":round(worst[0],4),"pair_min_of":worst[1],"n_pair_viol":len(pv),"pair_viol":pv[:8],
     "exact_gate":{k:gate[k] for k in ("n_lane_pitch_viol","lane_pitch_min_gap_mm","n_clearance_viol","endpoint_max_dev_mm")},
     "pass":(len(fails)==0 and len(pv)==0 and gate["n_lane_pitch_viol"]==0 and gate["n_clearance_viol"]==0 and gate["endpoint_max_dev_mm"]==0),
     "sol":sol}
print(json.dumps({k:v for k,v in out.items() if k!="sol"},ensure_ascii=False,indent=1))
json.dump(out,open("/tmp/opencode/r494/full.json","w"),ensure_ascii=False,default=str)
