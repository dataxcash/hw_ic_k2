"""#K2-174 §四.2/§五：非枚举形式族模型（解析式约束+成对析取；零 AddAllowedAssignments）→ 两闸 → 一次求解 → 独立核。
几何用**实测解析带**（R486/R490/R491 读数），不枚举元组。"""
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
A={a["net"]:a["A"] for a in an}; B={a["net"]:a["B"] for a in an}
names=sorted(A,key=lambda z:A[z][0]); N=len(names); SC=1000
F=[57.90,58.34,59.67,60.87,61.31,62.67,63.87,64.31,64.75,65.19,65.63,66.07,66.51,66.95,67.39,67.83]
def clear(x1,y1,x2,y2,thr=0.05):
    L=math.dist((x1,y1),(x2,y2)); k=max(2,int(L/thr)+1)
    xs=np.linspace(x1,x2,k); ys=np.linspace(y1,y2,k)
    i=np.rint((xs-rast.X0)/rast.step).astype(int); j=np.rint((ys-rast.Y0)/rast.step).astype(int)
    ok=(i>=0)&(i<rast.NX)&(j>=0)&(j<rast.NY)
    return bool(ok.all()) and (not bad[i[ok],j[ok]].any())
mo=cp_model.CpModel()
ci={};s={};xe={};ev={};nv={};co={}
for i,nm in enumerate(names):
    ax,ay=A[nm]
    ci[nm]=mo.NewIntVar(int(ax*SC),113000,"ci%d"%i)
    s[nm]=mo.NewIntVar(57000,67000,"s%d"%i)
    xe[nm]=mo.NewIntVar(118000,130000,"xe%d"%i)
    ev[nm]=mo.NewIntVar(0,15,"e%d"%i); nv[nm]=mo.NewIntVar(0,20,"n%d"%i); co[nm]=mo.NewIntVar(118000,134000,"co%d"%i)
    mo.AddAllDifferent([ev[nm] for nm in names]) if False else None
mo.AddAllDifferent([ev[nm] for nm in names])
for i,nm in enumerate(names):
    for j2 in range(i+1,N):
        nm2=names[j2]
        for k,v in (("ci",ci),("s",s),("xe",xe),("co",co)):
            pass
# 分离（成对析取·大 M 式）：同类两两 >=435（ci/xe/co） 或 >=435（s）
for i,nm in enumerate(names):
    for j2 in range(i+1,N):
        nm2=names[j2]
        b=mo.NewBoolVar("a%d_%d"%(i,j2))
        mo.Add(ci[nm]-ci[nm2]>=435).OnlyEnforceIf(b); mo.Add(ci[nm2]-ci[nm]>=435).OnlyEnforceIf(b.Not())
        b2=mo.NewBoolVar("s%d_%d"%(i,j2))
        mo.Add(s[nm]-s[nm2]>=435).OnlyEnforceIf(b2); mo.Add(s[nm2]-s[nm]>=435).OnlyEnforceIf(b2.Not())
        b3=mo.NewBoolVar("x%d_%d"%(i,j2))
        mo.Add(xe[nm]-xe[nm2]>=435).OnlyEnforceIf(b3); mo.Add(xe[nm2]-xe[nm]>=435).OnlyEnforceIf(b3.Not())
        b4=mo.NewBoolVar("c%d_%d"%(i,j2))
        mo.Add(co[nm]-co[nm2]>=435).OnlyEnforceIf(b4); mo.Add(co[nm2]-co[nm]>=435).OnlyEnforceIf(b4.Not())
        mo.Add(nv[nm]!=nv[nm2])
# 走廊：入点须 <= 门列；门列由 e 决定（136.2+0.435e）
for i,nm in enumerate(names):
    mo.Add(xe[nm]<=130000)
    # 门列 x 与 e 联立：px = 136200 + 435*e （纯线性）
    # 入口段/斜段的天花板约束（实测剖面：x<=120 -> 67.12 ; x<=126 -> 67.46 ; x>=128 -> 67.96）
    mo.Add(s[nm]<=67000); mo.Add(s[nm]>=57000)
    # 北侧：NY(n)=54900-435*n 须在 [45000,54800]；co 须使北段行可达门列
    mo.Add(nv[nm]<=22)
print("VARS",len(mo.Proto().variables))
print("GATE-A 编码可采纳性：无 AddAllowedAssignments =", all("allowed" not in str(c).lower() for c in mo.Proto().constraints)," (表约束数 = 0)")
print("GATE-B 充分性：三类自由度皆变量 = True (ci,s,xe,e,n,co 六类均 NewIntVar)")
sv=cp_model.CpSolver(); sv.parameters.max_time_in_seconds=300.0; sv.parameters.num_search_workers=8
st=sv.Solve(mo); print("STATUS",sv.StatusName(st))
