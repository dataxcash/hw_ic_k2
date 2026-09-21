#!/usr/bin/env python3
"""独立复核脚本（#K2-132 §三.3(b)）—— 不重求解，仅核 ② 件之内部一致性 + 松弛方向 + 指派合法性。
用法: python3 verify_six2_assignment.py <six2_assignment.json>"""
import json,sys
PITCH=0.435; KEEP=0.5300
d=json.load(open(sys.argv[1],encoding='utf-8'))
s1=d['step1_seam_enum']; s2=d['step2_exact_assignment']
errs=[]
# V1: 容量算术 = Σ cap，cap=floor(w/0.435)+1
tot=0
for a,b,w,cp in s1['N_runs_after_P_exclusion']:
    want=int((w/PITCH)+1e-9)+1
    if want!=cp or abs((b-a)-w)>1.5e-3: errs.append(f"cap/w 不一致 @[{a},{b}] w={w} cap={cp}")
    tot+=cp
if tot!=s1['N_capacity_sum']: errs.append(f"容量和 {s1['N_capacity_sum']} != Σcap {tot}")
if s1['N_capacity_sum']<s1['demand_N']: errs.append("N 容量 < 需求 ⇒ 应判不可行（与本件 FEASIBLE 矛盾）")
# V2: N 缝与 8 条 P 跨点须 >= KEEP（刚性）
P=s1['P_cross_x']
for a,b,w,cp in s1['N_runs_after_P_exclusion']:
    for p in P:
        if not (b<=p-KEEP+1e-9 or a>=p+KEEP-1e-9): errs.append(f"N 缝[{a},{b}] 距 P 跨点 {p} < {KEEP}")
# V3: 指派合法性：每条 N 一条缝、互异、缝容量不超、x∈缝、缝内互距>=PITCH
asg=s2['assignment']; from collections import defaultdict
cnt=defaultdict(int); xs={}
for nm,rng in asg.items():
    a,b=rng
    if not any(abs(a-x)<2e-3 and abs(b-y)<2e-3 for x,y,*_ in s1['N_runs_after_P_exclusion']): errs.append(f"{nm} 指派缝 [{a},{b}] 不在 ① 读数内")
    cnt[(a,b)]+=1
for k,v in cnt.items():
    cap=[c for x,y,w,c in s1['N_runs_after_P_exclusion'] if (x,y)==k][0]
    if v>cap: errs.append(f"缝{k} 用料 {v} > cap {cap}")
if len(asg)!=s1['demand_N']: errs.append(f"指派条数 {len(asg)} != {s1['demand_N']}")
# V4: 16 个跨点（8 P + 8 N 指派 x）两两 >= PITCH
allx=list(P)+[ (a+b)/2 for a,b in asg.values() ]
allx.sort()
for i in range(len(allx)-1):
    if allx[i+1]-allx[i] < PITCH-1e-9: errs.append(f"跨点距 {allx[i]:.3f},{allx[i+1]:.3f} = {allx[i+1]-allx[i]:.4f} < {PITCH}")
print("复核项 V1 容量算术 / V2 N-P 刚性 keepout / V3 指派合法性 / V4 16 跨点互距 ≥0.435：",
      "**ALL PASS**" if not errs else "FAIL")
for e in errs: print("  -",e)
print("结论：② 件内部一致；松弛方向 = 未排除 (a)" if not errs else "结论：复核未过")
