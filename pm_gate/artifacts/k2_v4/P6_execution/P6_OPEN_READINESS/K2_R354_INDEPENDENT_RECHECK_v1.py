#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K2 · R354 · 独立复核 —— 以 **不同分辨率 (cell=0.02，授权下限内)** 自写栅格化 + 自写 DP 重算
x-单调不可行性分区，并复算 sha16。退出码 0 = 全 MATCH。
"""
import json, math, sys, hashlib, os
import numpy as np
MODEL="/tmp/opencode/archer/model_l8.json"
ART="k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K2_R354_UP_OUT_XMONOTONE_INFEASIBILITY_v1.json"
CELL=0.02; HW=0.08; X0,Y0,X1,Y1=76.0,30.0,148.0,72.0
m=json.load(open(MODEL)); art=json.load(open(ART)); fails=[]
def chk(n,a,b):
    ok=(a==b); print(("  OK  " if ok else "  FAIL")+" %-40s got=%s exp=%s"%(n,a,b))
    if not ok: fails.append(n)
# 自写栅格化
NX=int((X1-X0)/CELL)+2; NY=int((Y1-Y0)/CELL)+2
XS=X0+np.arange(NX)*CELL; YS=Y0+np.arange(NY)*CELL
GX,GY=np.meshgrid(XS,YS,indexing="ij")
def req(nm):
    if nm.startswith(("PCIE","REFCLK")): return 0.175
    if nm.startswith(("P3V3","MCU_","VREG","PWR_5V")): return 0.20
    return 0.10
bad=np.zeros((NX,NY),bool)
def seg(ax,ay,bx,by,r):
    i0=max(0,int((min(ax,bx)-r-X0)/CELL)); i1=min(NX-1,int((max(ax,bx)+r-X0)/CELL)+1)
    j0=max(0,int((min(ay,by)-r-Y0)/CELL)); j1=min(NY-1,int((max(ay,by)+r-Y0)/CELL)+1)
    if i1<i0 or j1<j0: return
    X=GX[i0:i1+1,j0:j1+1]; Y=GY[i0:i1+1,j0:j1+1]
    dx,dy=bx-ax,by-ay; L2=dx*dx+dy*dy
    t=np.zeros_like(X) if L2==0 else np.clip(((X-ax)*dx+(Y-ay)*dy)/L2,0,1)
    bad[i0:i1+1,j0:j1+1]|=(np.hypot(X-(ax+t*dx),Y-(ay+t*dy))<r)
def cir(cx,cy,r): seg(cx,cy,cx,cy,r)
for s in m["segs"]["In5.Cu"]:
    if s[5].startswith(("PCIE_UP_OUT","PCIE_DN_OUT")): continue
    seg(s[0],s[1],s[2],s[3],HW+s[4]+max(0.175,req(s[5])))
for v in m["vias"]:
    if "In5.Cu" not in v["layers"] or v["net"].startswith(("PCIE_UP_OUT","PCIE_DN_OUT")): continue
    cir(v["x"],v["y"],HW+max(v["r"]+max(0.175,req(v["net"])),v["drill"]+0.25))
for p in m["pads"]:
    if p["net"].startswith(("PCIE_UP_OUT","PCIE_DN_OUT")): continue
    if "In5.Cu" not in p["layers"] and not p["pth"]: continue
    b=p["box"]; r=HW+max(0.175,req(p["net"]))
    seg(b[0],b[1],b[2],b[1],r); seg(b[2],b[1],b[2],b[3],r); seg(b[2],b[3],b[0],b[3],r); seg(b[0],b[3],b[0],b[1],r)
    if p["pth"] and p.get("drill"): cir(p["cx"],p["cy"],HW+p["drill"]+0.25)
free=~bad
INF=float('inf')
def xmono(A,B):
    si=int(round((A[0]-X0)/CELL)); sj=int(round((A[1]-Y0)/CELL))
    gi=int(round((B[0]-X0)/CELL)); gj=int(round((B[1]-Y0)/CELL))
    if si>gi: return None
    D=np.full((NX,NY),INF); D[si,sj]=0.0
    for i in range(si,gi+1):
        col=free[i]
        for _ in range(2):
            for j in range(1,NY):
                if col[j] and D[i,j-1]+CELL<D[i,j]: D[i,j]=D[i,j-1]+CELL
            for j in range(NY-2,-1,-1):
                if col[j] and D[i,j+1]+CELL<D[i,j]: D[i,j]=D[i,j+1]+CELL
        if i==gi: break
        for j in np.nonzero(col)[0]:
            d=D[i,j]
            if d==INF: continue
            for dj in (-1,0,1):
                nj=j+dj
                if 0<=nj<NY and free[i+1,nj]:
                    nd=d+(1.0 if dj==0 else math.sqrt(2))*CELL
                    if nd<D[i+1,nj]: D[i+1,nj]=nd
    return None if D[gi,gj]==INF else float(D[gi,gj])
LANES={f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N","P")}
seen={}
for v in m["vias"]:
    if v["net"] in LANES: seen.setdefault(v["net"],{})["%s-%s"%(v["top"],v["bot"])]=(v["x"],v["y"])
res={}
for nm,d in seen.items():
    if "F.Cu-B.Cu" in d and "F.Cu-In2.Cu" in d:
        A=d["F.Cu-B.Cu"]; B=d["F.Cu-In2.Cu"]
        res[nm]=(xmono(A,B) is not None)
chk("n_lanes",len(res),16)
no=[k for k,v in res.items() if not v]
chk("no-x-monotone count",len(no),8)
exp=set(r["net"] for r in art["per_lane"] if not r["x_monotone_feasible"])
chk("no-x-monotone set == artifact",set(no),exp)
chk("west group set == no-x-monotone set",
    set(r["net"] for r in art["per_lane"] if r["B"][0]<134.0),exp)
core=dict(art); core.pop("self_sha16",None)
chk("sha16(约定A)",hashlib.sha256(json.dumps(core,ensure_ascii=False,indent=1,sort_keys=True).encode()).hexdigest()[:16],
    art["self_sha16"]["convention_A_sha16"])
print("\nFAIL %d"%len(fails)); sys.exit(1 if fails else 0)
