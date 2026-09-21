#!/usr/bin/env python3
"""K2 · #K2-132 §三 —— §六②『精确指派解』（一次 · 只读 · 无扫描 · 松弛可靠）
① 跨线 y=54.88 缝枚举（公布读数）② 精确指派（松弛：仅含**必要**条件；刚性量具名）
用法: python3 six2_exact_assignment.py <out.json> [cell=0.03] [dilate=1]
"""
import json, math, sys, importlib.util, numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
HERE="/home/fila/jqdDev_2025/ic_hw/k2"
spec=importlib.util.spec_from_file_location("v3m",HERE+"/tools/k2_p4_b2_in5_lane_router_v3.py")
v3=importlib.util.module_from_spec(spec); spec.loader.exec_module(v3)
LANES=[f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N","P")]
Nn=[n for n in LANES if n.split("_")[3]=="N"]; Pp=[n for n in LANES if n.split("_")[3]=="P"]
v3.is_lane=lambda n: n in set(LANES)                     # no-move 全转：自网旧铜不作障碍
cell=float(sys.argv[2]) if len(sys.argv)>2 else 0.03
DIL=int(sys.argv[3]) if len(sys.argv)>3 else 1
hw=0.16/2; margin=0.100; PITCH=0.435; LINE=54.88
v3.PAD_EXTRA=margin
model=json.load(open("/tmp/opencode/archer/model_crop.json"))
A=json.load(open("/tmp/opencode/archer/sites_phys.json")); B=json.load(open("/tmp/opencode/archer/sites_b_board_v1.json"))
rast=v3.Raster(model["bbox"],cell)
anchors=v3.lane_anchors(model)
for an in anchors: an["A"]=tuple(A[an["net"]]); an["B"]=tuple(B[an["net"]])
AN={a["net"]:a for a in anchors}
base=v3.build_base(rast,model,"In5.Cu",frozenset(),frozenset(),hw,frozenset())
free=~base
# ---- ① 跨线 y=54.88 缝枚举：刚性 = keepout 0.5300（PAD_EXTRA=margin 已含）----
jL=int(round((LINE-rast.Y0)/cell))
jrow_free=[bool(free[i,jL]) for i in range(rast.NX)]
runs=[]; i=0
while i<rast.NX:
    if jrow_free[i]:
        k=i
        while k+1<rast.NX and jrow_free[k+1]: k+=1
        x0=rast.X0+i*cell; x1=rast.X0+k*cell
        if 80.0<=x0<=100.0 or 80.0<=x1<=100.0: runs.append((round(x0,3),round(x1,3),round(x1-x0,3)))
        i=k+1
    else: i+=1
PXK=0.5300  # 刚性 keepout（#K2-130 §四 · hw0.08+0.35+margin0.10）
Px=[round(A[n][0],3) for n in Pp]
def cap(w): return int(math.floor(w/PITCH+1e-9))+1
# 扣除 8 条 P 跨点之 0.435 邻域后，N 可用缝
def sub(runs,px):
    out=[]
    for a,b,_ in runs:
        segs=[(a,b)]
        for p in px:
            ns=[]
            for s0,s1 in segs:
                lo,hi=p-PXK,p+PXK
                if hi<=s0 or lo>=s1: ns.append((s0,s1)); continue
                if lo>s0: ns.append((s0,lo))
                if hi<s1: ns.append((hi,s1))
            segs=ns
        for s0,s1 in segs:
            if s1-s0>1e-9: out.append((round(s0,3),round(s1,3),round(s1-s0,3),cap(s1-s0)))
    return out
Nruns=sub(runs,Px)
# ---- 可达性 R_i（松弛向 = **过近似**：free 膨胀 DIL 格后在 4-邻域 BFS）----
fd=free.copy()
for _ in range(DIL):
    g=fd.copy()
    g[1:,:]|=fd[:-1,:]; g[:-1,:]|=fd[1:,:]; g[:,1:]|=fd[:,:-1]; g[:,:-1]|=fd[:,1:]
    fd=g
G,idx=v3.build_topology(fd,cell)
n=G.shape[0]; GG=(G+G.T).tocsr()
ncc,lab=connected_components(GG,directed=False)
def cellof(x,y): return rast.cell(x,y)
Acomp={}
for nm in LANES:
    ci,cj=cellof(*A[nm]); Acomp[nm]=int(lab[idx[ci,cj]]) if idx[ci,cj]>=0 else -1
# 各 N 条：可达之缝（过近似：只要其 A 所在连通域触及该缝区间）
Reach={}
for nm in Nn:
    ok=[]
    c=Acomp[nm]
    for a,b,w,cp in Nruns:
        hit=False
        i0=int((a-rast.X0)/cell); i1=int((b-rast.X0)/cell)
        for i in range(max(0,i0),min(rast.NX,i1+1)):
            if jrow_free[i] and idx[i,jL]>=0 and lab[idx[i,jL]]==c: hit=True; break
        if hit: ok.append((a,b))
    Reach[nm]=ok
# ---- ② 精确指派（松弛 = 必要条件的多商品容量流；max-flow = 指派最大数）----
# 条件:(N1) 每线须跨 y=54.88 一次【拓扑必要】(N2) 跨点互距>=0.435【刚性 pitch_eff】
#      (N3) 跨点在刚性 keepout 自由集内【刚性 keepout 0.5300】(N4) x in R_i（过近似 ⇒ 松弛安全）
#      P 条跨点 = 自身 A 孔位（固定）
capby=[[k,a,b,w,cp] for k,(a,b,w,cp) in enumerate(Nruns)]
# max-flow: source->N lane->(缝)容量 cp->sink ; 用朴素增广（规模极小）
NI=[(k,a,b,w,cp) for k,(a,b,w,cp) in enumerate(Nruns)]
lanes=[nm for nm in Nn]
# 边：lane -> interval if interval in Reach
adj={nm:[k for k,(a,b,w,cp) in enumerate(Nruns) if (a,b) in Reach[nm]] for nm in lanes}
flow={}
def maxflow():
    f={nm:{} for nm in lanes}; used={k:0 for k in range(len(Nruns))}
    def dfs(nm,vis):
        for k in adj[nm]:
            if (nm,k) in f[nm]: continue
            if used[k]<Nruns[k][3]:
                f[nm][k]=1; used[k]+=1; return True
        for k in adj[nm]:
            for om in lanes:
                if om!=nm and om in f and k in f[om] :
                    del f[om][k]; used[k]-=1
                    for k2 in adj[om]:
                        if k2!=k and used[k2]<Nruns[k2][3] and (om,k2) not in f[om]:
                            f[om][k2]=1; used[k2]+=1
                            if dfs(nm,vis): return True
                            del f[om][k2]; used[k2]-=1
                    f[om][k]=1; used[k]+=1
        return False
    cnt=0
    for nm in lanes:
        if dfs(nm,set()): cnt+=1
    return cnt,f,used
cnt,f,used=maxflow()
out={"artifact":"k2_six2_exact_assignment","ts":None,"caliber":{"keepout":0.5300,"cell":cell,"lane_w":0.16,"pitch_eff":PITCH,
      "line_y":LINE,"own_copper":"excluded (no-move 全转)","reach_dilate_cells":DIL},
 "step1_seam_enum":{"line_y":LINE,"free_runs_raw":runs,"P_cross_x":Px,"N_runs_after_P_exclusion":Nruns,
      "N_capacity_sum":sum(r[3] for r in Nruns),"P_rigid_keepout":0.5300,"demand_N":len(Nn),"demand_P":len(Pp)},
 "step2_exact_assignment":{"model":"relaxation: only NECESSARY conditions (N1 topology, N2 pitch_eff 0.435, N3 rigid keepout 0.5300, N4 x in over-approx reachable set)",
      "max_N_assignable":cnt,"required":len(Nn),
      "reach_by_lane":{nm:[f"{a}-{b}" for a,b in Reach[nm]] for nm in Nn},
      "assignment":{nm:[Nruns[k][0],Nruns[k][1]] for nm in f for k in f[nm]},
      "verdict":"FEASIBLE(松弛可行 ⇒ 未排除 (a))" if cnt>=len(Nn) else "INFEASIBLE(松弛不可行 ⇒ 真实不可行 ⇒ (b) 证书)"}}
json.dump(out,open(sys.argv[1],'w'),ensure_ascii=False,indent=1)
print("① 自由缝(原始)：",len(runs),"段；P 跨点 8")
for a,b,w in runs: print(f"     [{a},{b}] w={w}")
print("   扣 P 跨点 ±0.435 后 N 可用缝：")
for a,b,w,cp in Nruns: print(f"     [{a},{b}] w={w} cap={cp}")
print("   N 容量合计 =",sum(r[3] for r in Nruns),"  需求 N =",len(Nn))
print("② 可达（过近似 · dilate=%d）："%DIL)
for nm in Nn: print("     %-22s %s"%(nm,[f"{a}-{b}" for a,b in Reach[nm]] or "NONE"))
print("② 精确指派最大数 =",cnt,"/ 需求",len(Nn),"⇒",out['step2_exact_assignment']['verdict'])
