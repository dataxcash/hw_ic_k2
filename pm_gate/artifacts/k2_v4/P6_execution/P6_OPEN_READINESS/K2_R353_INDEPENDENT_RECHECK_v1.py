#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K2 · R353 · 独立复核（监理可跑）—— 不 import 主件，独立重算只读读数并 MATCH/FAIL。

复现前提：先 dump 模型（只读板件）：
  AppDir/usr/bin/python3.11 k2/tools/k2_p4_b2_board_in5_model_dump_v1.py \
      k2/hw/k2_v4_8L.l8.kicad_pcb /tmp/opencode/archer/model_l8.json
再：python3 <本件>
"""
import json, math, hashlib, sys
import numpy as np

MODEL="/tmp/opencode/archer/model_l8.json"
ART="k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K2_R353_UP_OUT_EXACT_READOUT_v1.json"
PITCH=0.435; CELL=0.03; HW=0.08
X0,Y0,X1,Y1=76.0,30.0,148.0,72.0

m=json.load(open(MODEL)); art=json.load(open(ART))
fails=[]
def chk(name, a, b, tol=1e-6):
    ok = (abs(a-b)<=tol) if isinstance(a,(int,float)) and isinstance(b,(int,float)) else (a==b)
    print(("  OK  " if ok else "  FAIL")+" %-42s got=%s expect=%s"%(name,a,b)); 
    if not ok: fails.append(name)

# --- 独立：lane 锚（自己写，不 import 主件） ---
LANES={f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N","P")}
seen={}
for v in m["vias"]:
    if v["net"] in LANES:
        seen.setdefault(v["net"],{})["%s-%s"%(v["top"],v["bot"])]=(round(v["x"],3),round(v["y"],3))
anch={nm:{"A":d["F.Cu-B.Cu"],"B":d["F.Cu-In2.Cu"]} for nm,d in seen.items()}
order=sorted(anch, key=lambda n: anch[n]["A"][0])
chk("n_lanes", len(order), 16)
chk("riser order lane0", order[0], "PCIE_UP_OUT0_N_J2")
chk("riser order lane15", order[15], "PCIE_UP_OUT7_P_J2")
By=sorted(range(16), key=lambda i: anch[order[i]]["B"][1])
chk("B_y_rank[0]", By.index(0), art["step1_order_invariant"]["B_y_rank_vs_a_rank"]["B_y_rank"][0])
chk("B_y_rank[15]", By.index(15), art["step1_order_invariant"]["B_y_rank_vs_a_rank"]["B_y_rank"][15])
inv=sum(1 for i in range(16) for j in range(i+1,16) if By.index(i)<By.index(j))
chk("inversions_vs_a_rank", inv, art["step1_order_invariant"]["B_y_rank_vs_a_rank"]["inversions_vs_a_rank"])

# --- 独立：自由空间（自写栅格化：seg/via/pad 障碍 + 车道网全剔除 = no-move 全转） ---
NX=int((X1-X0)/CELL)+2; NY=int((Y1-Y0)/CELL)+2
XS=X0+np.arange(NX)*CELL; YS=Y0+np.arange(NY)*CELL
GX,GY=np.meshgrid(XS,YS,indexing="ij")
def req(nm):
    if nm.startswith(("PCIE","REFCLK")): return 0.175
    if nm.startswith(("P3V3","MCU_","VREG","PWR_5V")): return 0.20
    return 0.10
def eff(nm): return max(0.175, req(nm))
bad=np.zeros((NX,NY),bool)
def seg(ax,ay,bx,by,rad):
    i0=max(0,int((min(ax,bx)-rad-X0)/CELL)); i1=min(NX-1,int((max(ax,bx)+rad-X0)/CELL)+1)
    j0=max(0,int((min(ay,by)-rad-Y0)/CELL)); j1=min(NY-1,int((max(ay,by)+rad-Y0)/CELL)+1)
    if i1<i0 or j1<j0: return
    X=GX[i0:i1+1,j0:j1+1]; Y=GY[i0:i1+1,j0:j1+1]
    dx,dy=bx-ax,by-ay; L2=dx*dx+dy*dy
    t=np.zeros_like(X) if L2==0 else np.clip(((X-ax)*dx+(Y-ay)*dy)/L2,0,1)
    bad[i0:i1+1,j0:j1+1] |= (np.hypot(X-(ax+t*dx),Y-(ay+t*dy))<rad)
def cir(cx,cy,rad):
    seg(cx,cy,cx,cy,rad)
for s in m["segs"]["In5.Cu"]:
    if s[5].startswith(("PCIE_UP_OUT","PCIE_DN_OUT")): continue
    seg(s[0],s[1],s[2],s[3], HW+s[4]+eff(s[5]))
for v in m["vias"]:
    if "In5.Cu" not in v["layers"] or v["net"].startswith(("PCIE_UP_OUT","PCIE_DN_OUT")): continue
    cir(v["x"],v["y"], HW+max(v["r"]+eff(v["net"]), v["drill"]+0.25))
for p in m["pads"]:
    if p["net"].startswith(("PCIE_UP_OUT","PCIE_DN_OUT")): continue
    if "In5.Cu" not in p["layers"] and not p["pth"]: continue
    b=p["box"]; 
    # rect as 4 segs (conservative equal to circle-radius method)
    for (ax,ay,bx,by) in ((b[0],b[1],b[2],b[1]),(b[2],b[1],b[2],b[3]),(b[2],b[3],b[0],b[3]),(b[0],b[3],b[0],b[1])):
        seg(ax,ay,bx,by, HW+eff(p["net"]))
    if p["pth"] and p.get("drill"): cir(p["cx"],p["cy"], HW+p["drill"]+0.25)
free=~bad
# seam y=54.88 独立重算
j=int(round((54.880-Y0)/CELL)); row=free[:,j]; ivs=[]; i=0
while i<len(row):
    if row[i]:
        k=i
        while k+1<len(row) and row[k+1]: k+=1
        ivs.append((round(X0+i*CELL,3),round(X0+k*CELL,3))); i=k+1
    else: i+=1
ivs=[(a,b) for a,b in ivs if b-a>0.05]
chk("seam n_intervals", len(ivs), art["step1_cross_seam_enumeration"]["readout"]["54.880"]["n"],
    tol=1)  # 独立栅格化（pad 矩形近似 vs 圆角）容 1 段
disc=[x for x in ivs if 93.4<x[0]<108.0 and (x[1]-x[0])<1.0]
chk("discrete 11-band count", len(disc), art["step1_cross_seam_enumeration"]["discrete_slots_x_93.4_108"]["count"])
# 自算 sha16（约定A）
core=dict(art); core.pop("self_sha16",None)
s16=hashlib.sha256(json.dumps(core,ensure_ascii=False,indent=1,sort_keys=True).encode()).hexdigest()[:16]
chk("artifact self_sha16(约定A)", s16, art["self_sha16"]["convention_A_sha16"])
print("\n%d 项中 FAIL %d 项" % (1, len(fails)))
sys.exit(1 if fails else 0)
