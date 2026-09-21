#!/usr/bin/env python3
"""归因（非证书 · #K2-73 §一 口径）：全转口径下，16 条 UP_OUT In5 车道**逐条** A→B 是否可达。
用法: python3 four_lane_reach.py [cell=0.03]
"""
import json,math,sys,importlib.util,numpy as np
from scipy.sparse.csgraph import dijkstra
HERE="/home/fila/jqdDev_2025/ic_hw/k2"
spec=importlib.util.spec_from_file_location("v3m",HERE+"/tools/k2_p4_b2_in5_lane_router_v3.py")
v3=importlib.util.module_from_spec(spec); spec.loader.exec_module(v3)
LANES=[f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N","P")]
v3.is_lane=lambda n: n in set(LANES)               # 全转：自网旧铜不入障碍
cell=float(sys.argv[1]) if len(sys.argv)>1 else 0.03
hw=0.08; v3.PAD_EXTRA=0.100
model=json.load(open("model_crop.json")); A=json.load(open("sites_phys.json")); B=json.load(open("sites_b_board_v1.json"))
rast=v3.Raster(model["bbox"],cell)
anchors=v3.lane_anchors(model)
base=v3.build_base(rast,model,"In5.Cu",frozenset(),frozenset(),hw,frozenset())
free=~base
G,idx=v3.build_topology(free,cell)
def cs(p):
    i,j=rast.cell(p[0],p[1]); return idx[i,j]
res={}
for nm in LANES:
    s,g=cs(A[nm]),cs(B[nm])
    if s<0 or g<0: res[nm]={"A_free":s>=0,"B_free":g>=0,"dist_mm":None}; continue
    d=dijkstra(G,indices=s,directed=False)[g]
    res[nm]={"A_free":True,"B_free":True,"dist_mm":(round(float(d*cell),3) if np.isfinite(d) else None),
             "straight_mm":round(math.dist(A[nm],B[nm]),3)}
ok=[k for k,v in res.items() if v["dist_mm"]]
bad=[k for k,v in res.items() if not v["dist_mm"]]
print("cell",cell,"| 逐条 A→B 可达 =",len(ok),"/16 ｜ 不可达 =",len(bad))
for k in sorted(res): print(f"   {k:22s} A_free={res[k]['A_free']} B_free={res[k]['B_free']} 路径={res[k]['dist_mm']} 直线={res[k]['straight_mm']}")
print("【归因】4 条未转换网（0_N/0_P/1_P/2_P）逐条可达性：",{k:bool(res[k]['dist_mm']) for k in ['PCIE_UP_OUT0_N_J2','PCIE_UP_OUT0_P_J2','PCIE_UP_OUT1_P_J2','PCIE_UP_OUT2_P_J2']})
json.dump(res,open("four_lane_reach.json","w"),ensure_ascii=False,indent=1)
