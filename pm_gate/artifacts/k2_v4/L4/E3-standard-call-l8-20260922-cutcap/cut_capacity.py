#!/usr/bin/env python3
"""割线容量严格上界（#K2-132 §二 (乙)①/③ · 松弛安全 = 必要条件）：
**任一**竖直割线 x=c（c∈(93.70,127.01)）必被全部 16 条 UP_OUT In5 车道各穿一次；
其自由集（刚性 keepout 0.5300）内之 0.435-打包点数 = 该割线容量 ⇒ min_c 容量 ≥ 真实可布条数。
若 min < 16 ⇒ (b) 严格上界证书。用法: python3 cut_capacity.py [cell=0.03]"""
import json,sys,importlib.util,numpy as np
HERE="/home/fila/jqdDev_2025/ic_hw/k2"
spec=importlib.util.spec_from_file_location("v3m",HERE+"/tools/k2_p4_b2_in5_lane_router_v3.py")
v3=importlib.util.module_from_spec(spec); spec.loader.exec_module(v3)
LANES=[f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N","P")]
v3.is_lane=lambda n: n in set(LANES); v3.PAD_EXTRA=0.100
cell=float(sys.argv[1]) if len(sys.argv)>1 else 0.03
model=json.load(open("model_crop.json")); A=json.load(open("sites_phys.json")); B=json.load(open("sites_b_board_v1.json"))
rast=v3.Raster(model["bbox"],cell)
base=v3.build_base(rast,model,"In5.Cu",frozenset(),frozenset(),0.08,frozenset()); free=~base
PITCH=0.435
def pack(vals):
    vals=sorted(vals); out=[]
    for v in vals:
        if not out or v-out[-1]>=PITCH-1e-9: out.append(v)
    return len(out)
lo=max(A[n][0] for n in LANES); hi=min(B[n][0] for n in LANES)
c0=int(round((lo-rast.X0)/cell))+2; c1=int(round((hi-rast.X0)/cell))-1
best=None; series=[]
for i in range(c0,c1+1):
    ys=[rast.Y0+j*cell for j in range(rast.NY) if free[i,j]]
    # 取最长连续段（同一割线上车道可分布多处，用总可容纳数=逐段 pack 之和）
    tot=0; run=[]
    for j in range(rast.NY):
        if free[i,j]: run.append(rast.Y0+j*cell)
        else:
            if run: tot+=pack(run); run=[]
    if run: tot+=pack(run)
    series.append((round(rast.X0+i*cell,2),tot))
    if best is None or tot<best[1]: best=(round(rast.X0+i*cell,2),tot)
xs=[s for s,_ in series]; cs=[c for _,c in series]
print("割线区间 x∈(%.2f,%.2f) · cell %.2f · 割线数 %d"%(lo,hi,cell,len(xs)))
print("  min 容量 = %d  @x=%.2f"%(best[1],best[0]))
print("  分位: p05 %d · p25 %d · p50 %d · max %d"%(int(np.percentile(cs,5)),int(np.percentile(cs,25)),int(np.percentile(cs,50)),max(cs)))
print("  低于16之割线数 = %d"%sum(1 for c in cs if c<16))
print("  ⇒ %s"%("**(b) 严格上界证书 U=%d < 16**"%best[1] if best[1]<16 else "无 U<16 ⇒ (b) 割线容量型仍不可得"))
json.dump({"cut_range":[lo,hi],"cell":cell,"min_capacity":best,"series":series[:400]},open("cut_capacity.json","w"))
