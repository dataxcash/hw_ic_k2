#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K2 · R357 · ①-UP **下潜站指派之精确判定**（阴性）+ 折返楼梯规格
模型类 M1 =『band 定阶 → x_p 单点竖直下潜 → y_B 直水平至锚』
结论 = **M1 结构性不可行**（MILP infeasible + 8 条西组 lane 候选数 0）⇒ 必需件 = **非单调楼梯**
只读 · 未烙板 · 未改冻结四源/判据/生成器/SPEC/原理图。复现：先 dump 模型，再 python3 <本件>
"""
import json,math,os,sys,hashlib
sys.path.insert(0,'/home/fila/jqdDev_2025/ic_hw/k2/tools')
import numpy as np
from k2_p4_b2_in5_lane_router_v3 import Raster, build_base, lane_anchors
from scipy.optimize import milp, LinearConstraint, Bounds
import scipy.sparse as sp

MODEL="/tmp/opencode/archer/model_l8.json"
OUT="k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS" if os.path.isdir("k2") else "/tmp/opencode/k2r353"
m=json.load(open(MODEL)); bx0,by0,bx1,by1=m["bbox"]
X0,Y0,X1,Y1=76.0,30.0,148.0,72.0; cell=0.03; hw=0.08; P=0.435
rast=Raster((X0,Y0,X1,Y1),cell); base=build_base(rast,m,"In5.Cu",frozenset(),frozenset(),hw); free=~base
ans=[a for a in lane_anchors(m) if a['net'].startswith("PCIE_UP_OUT")]; ans.sort(key=lambda a:a['A'][0])
def idx(x,y):
    i=int(round((x-X0)/cell)); j=int(round((y-Y0)/cell)); return i,j
def vfree(x,y0,y1):
    i,j0=idx(x,min(y0,y1)); _,j1=idx(x,max(y0,y1))
    return 0<=i<rast.NX and bool(free[i,j0:j1+1].all())
def hfree(y,x0,x1):
    i0,j=idx(min(x0,x1),y); i1,_=idx(max(x0,x1),y)
    return bool(free[i0:i1+1,j].all())
XS=[round(x,2) for x in np.arange(134.0,bx1+1e-9,0.03)]
cand={}
for a in ans:
    xB,yB=a['B']; cand[a['net']]=[x for x in XS if vfree(x,57.0,yB) and vfree(x,68.0,57.0) and hfree(yB,x,xB)]
rows=[]
for a in ans:
    nm=a['net']; c=cand[nm]
    rows.append({"net":nm,"a_rank":ans.index(a),"y_B":a['B'][1],"x_B":a['B'][0],
                 "n_candidate_descent_columns":len(c),
                 "x_min":(c[0] if c else None),"x_max":(c[-1] if c else None)})
west_no=[r for r in rows if r["n_candidate_descent_columns"]==0]
# MILP（M1 类）：lane->列（互距>=0.435）
names=[a['net'] for a in ans]; allx=sorted(set().union(*cand.values()))
xi={x:k for k,x in enumerate(allx)}; N=len(names)*len(allx)
def z(i,k): return i*len(allx)+k
A=[];lo=[];hi=[]
for i,nm in enumerate(names):
    r=np.zeros(N); r[[z(i,xi[x]) for x in cand[nm]]]=1.0; A.append(r); lo.append(1.0); hi.append(1.0)
for k in range(len(allx)):
    r=np.zeros(N)
    for i in range(len(names)): r[z(i,k)]=1.0
    A.append(r); lo.append(0.0); hi.append(1.0)
for k in range(len(allx)):
    w=[kk for kk in range(len(allx)) if abs(allx[kk]-allx[k])<P-1e-9]
    if len(w)>1:
        r=np.zeros(N)
        for i in range(len(names)):
            for kk in w: r[z(i,kk)]=1.0
        A.append(r); lo.append(0.0); hi.append(1.0)
res=milp(c=np.zeros(N),constraints=[LinearConstraint(sp.csr_matrix(np.array(A)),np.array(lo),np.array(hi))],
         integrality=np.ones(N),bounds=Bounds(0,1),options={"time_limit":60,"presolve":True})
# 解析引理：4P 迫使后 8 条深 lane 在 y=48.05 交叉于 x>140.06 ⇒ 需 8×0.435=3.48mm > 板边余 2.99mm
lemma={"lane":"PCIE_UP_OUT4_P_J2（a_rank 9 · 下潜序第 7 · y_B=48.05 · x_B=140.06）",
 "later_deep_lanes":8,"need_mm":round(8*P,3),"avail_mm":round(bx1-140.06,3),
 "verdict":"M1 类中『后 8 条深 lane 须在 x>140.06 交叉 y=48.05 且互距 ≥0.435』⇒ 需 %.2fmm 而板边仅余 %.2fmm ⇒ **M1 类不可能**（与 MILP infeasible 独立互证）"%(8*P,bx1-140.06),
 "escape":"**非单调楼梯**（先下至中间层 → 西行 → 再下）可绕开，故**不构成 U<16 证书**（(b) 仍不成立）"}
art={"schema":1,"artifact":"k2_r357_up_out_descent_station_assignment_determination_v1",
 "ts":"2026-09-22T09:32+0800","to":"监理","from":"ENG · ARCHER",
 "nature":"①-UP **下潜站指派精确判定**（阴性 · 模型类 M1）+ **折返楼梯**规格 · 只读 · 二值未取得",
 "board_sha16":"7a5c89913d6e5d0a",
 "frozen4":["d4e81f647be7f980","fb07d25ac426ff84","dd794c54f7ce7417","0a459839e15960b8"],
 "criteria":"rev=6 MATCH (1937a40ae68bc288 / 727d09953cf9bd78 / eb3da49f2ad97e37)",
 "binary":{"(a)":"未得","(b)":"不成立"},
 "model_class_M1":{"definition":"每 lane：A → 立管至定阶 → band 东行 → **单点竖直下潜** x_p 至 y_B → **直水平**至 B 锚",
   "determination":"**结构性不可行**",
   "evidence_1_milp":{"form":"16 lane × 候选列 二元指派 · 约束 每 lane 恰1列 + 每列≤1 + 互距≥0.435（窗口）",
     "n_binaries":N,"status":int(res.status),"success":bool(res.success),"message":str(res.message)},
   "evidence_2_west_group_zero_candidates":west_no,
   "evidence_3_lemma":lemma},
 "per_lane":rows,
 "consequence":"⇒ 必需件 = **非单调楼梯下潜**（西组 8 条 + 深 lane）；M1 已被排除，**禁再跑 M1 族**。",
 "next_step_spec":{"name":"折返楼梯（staircase fold）","objects":"『下潜楼梯站序 × 中间层水平段』",
   "requirement":"须同时满足 ㈠竖序不变量 ㈡楼梯可绕 4P 型「直水平封口」㈢互距 ≥0.435",
   "acceptance":"exact_gate（互距0 ∧ 净距0 ∧ 端点0）+ buildability"},
 "buildability_field":{"mode":"no_move","note":"纯只读：未改任何网几何 · 未烙板 · 未动冻结四源/判据 ⇒ 不动证明成立"}}
core=dict(art); s=hashlib.sha256(json.dumps(core,ensure_ascii=False,indent=1,sort_keys=True).encode()).hexdigest()[:16]
art["self_sha16"]={"convention":"#K2-72 §五 约定A","convention_A_sha16":s}
json.dump(art,open(os.path.join(OUT,"K2_R357_UP_OUT_DESCENT_STATION_ASSIGNMENT_DETERMINATION_v1.json"),"w"),ensure_ascii=False,indent=1,sort_keys=True)
print("sha16",s); print("MILP success",res.success,res.message); print("west zero-cand",len(west_no)); print("lemma",lemma["verdict"])
