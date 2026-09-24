"""#K2-172 §四.4 放行：证明级**补全**模型 + 前置质检闸 + 一次求解（脚本先定稿 · 只执行一次）。
补全：锚区逃逸与下落**均为决策变量**（ci 自网格取 · s 自 0.435 阶梯取 · e 取 F）；生成器=纯投影。
几何真值（在册 Raster/build_base）：(i) 斜逃逸 (A_x,A_y)->(ci,YE) 净；(ii) 下落 (ci,YE)->(ci,s) 净；(iii) 走廊斜段 (ci,s)->(xe(e),F[e]) 净。"""
import json,sys,math,time
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
F=[57.90,58.34,59.67,60.87,61.31,62.67,63.87,64.31,64.75,65.19,65.63,66.07,66.51,66.95,67.39,67.83]
YE=56.6; STEP=0.2; SC=100
def clear(x1,y1,x2,y2,thr=0.06):
    L=math.dist((x1,y1),(x2,y2)); k=max(2,int(L/thr)+1)
    xs=np.linspace(x1,x2,k); ys=np.linspace(y1,y2,k)
    i=np.rint((xs-rast.X0)/rast.step).astype(int); j=np.rint((ys-rast.Y0)/rast.step).astype(int)
    ok=(i>=0)&(i<rast.NX)&(j>=0)&(j<rast.NY)
    return bool(ok.all()) and (not bad[i[ok],j[ok]].any())
N=len(names); SS=[round(57.0+0.435*k,3) for k in range(22)]
mo=cp_model.CpModel(); CIV={}; SV={}; EV={}; tables={}
t0=time.time()
for i,nm in enumerate(names):
    ax,ay=A[nm]; xs=[]; x=round(ax,3)
    while x<=113.0:
        if clear(ax,ay,x,YE): xs.append(int(round(x*SC)))
        x=round(x+STEP,3)
    allowed=[]
    for xv in xs:
        x=xv/SC
        for si,s in enumerate(SS):
            if s<=YE+1e-9 or not clear(x,YE,x,s): continue
            for e in range(16):
                if clear(x,s,round(120.0+0.435*e,3),F[e]): allowed.append((xv,si,e))
    tables[nm]=len(allowed)
    if not allowed: print("EMPTY_TABLE",nm); sys.exit(3)
    civ=mo.NewIntVarFromDomain(cp_model.Domain.FromValues(sorted(xs)),"ci%d"%i)
    siv=mo.NewIntVar(0,21,"s%d"%i); eiv=mo.NewIntVar(0,15,"e%d"%i)
    mo.AddAllowedAssignments([civ,siv,eiv],allowed)
    CIV[nm]=civ; SV[nm]=siv; EV[nm]=eiv
print("TABLE_SIZES",json.dumps(tables),"build %.0fs"%(time.time()-t0))
for i in range(N):
    for j in range(i+1,N):
        ni,nj=names[i],names[j]
        mo.Add(CIV[ni]!=CIV[nj]); mo.Add(SV[ni]!=SV[nj]); mo.Add(EV[ni]!=EV[nj])
        a=mo.NewBoolVar("c%d_%d"%(i,j)); b=mo.NewBoolVar("s%d_%d"%(i,j))
        mo.Add(CIV[ni]-CIV[nj]>=44).OnlyEnforceIf(a); mo.Add(CIV[nj]-CIV[ni]>=44).OnlyEnforceIf(a.Not())
        mo.Add(SV[ni]-SV[nj]>=1).OnlyEnforceIf(b); mo.Add(SV[nj]-SV[ni]>=1).OnlyEnforceIf(b.Not())
        g=mo.NewBoolVar("g%d_%d"%(i,j))
        mo.Add(CIV[ni]<CIV[nj]).OnlyEnforceIf(g); mo.Add(CIV[ni]>CIV[nj]).OnlyEnforceIf(g.Not())
        mo.Add(SV[ni]<SV[nj]).OnlyEnforceIf(g); mo.Add(SV[ni]>SV[nj]).OnlyEnforceIf(g.Not())
        mo.Add(EV[ni]<EV[nj]).OnlyEnforceIf(g); mo.Add(EV[ni]>EV[nj]).OnlyEnforceIf(g.Not())
print("VALID:",mo.Validate() or "OK")
sv=cp_model.CpSolver(); sv.parameters.max_time_in_seconds=300.0; sv.parameters.num_search_workers=8
st=sv.Solve(mo); print("STATUS",sv.StatusName(st),"wall %.0fs"%(time.time()-t0))
if st in (cp_model.OPTIMAL,cp_model.FEASIBLE):
    sol=[{"nm":nm,"ci":sv.Value(CIV[nm])/SC,"s":SV[nm] and SS[sv.Value(SV[nm])],
          "e":F[sv.Value(EV[nm])]} for nm in names]
    print(json.dumps(sol,ensure_ascii=False))
    json.dump({"status":sv.StatusName(st),"sol":sol},open("/tmp/opencode/r491/full.json","w"),ensure_ascii=False)
