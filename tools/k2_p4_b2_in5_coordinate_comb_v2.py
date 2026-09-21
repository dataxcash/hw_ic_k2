#!/usr/bin/env python3
"""R263 · 坐标化实现 v2（人画坐标·零搜索·零迭代）：A 侧 no-move 入口(_P 斜下穿 _N 缝) + 南通道梳子
+ 东通道列 + B 侧（东组终止于通道内 · 西组经北开阔区西拐再南落，按 x_B 升序分层）。末闸 v3.exact_gate。"""
import json,math,importlib.util,numpy as np
HERE="/home/fila/jqdDev_2025/ic_hw/k2"
spec=importlib.util.spec_from_file_location("v3m",HERE+"/tools/k2_p4_b2_in5_lane_router_v3.py")
v3=importlib.util.module_from_spec(spec);spec.loader.exec_module(v3)
LS={f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N","P")}
v3.is_lane=lambda n:n in LS
_o=v3.req; v3.req=lambda n:(0.175 if n in LS else _o(n))
v3.PAD_EXTRA=0.100
model=json.load(open('/tmp/opencode/archer/model_crop.json'))
A=json.load(open('/tmp/opencode/archer/sites_phys.json'))
B=json.load(open('/tmp/opencode/archer/sites_b_board_v1.json'))
PITCH=0.435; HW=0.08
Nx=sorted(A[f"PCIE_UP_OUT{i}_N_J2"][0] for i in range(8))
slit=[(Nx[i]+Nx[i+1])/2.0 for i in range(7)]
order=[f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N","P")]
# A 侧入口点 + 落线 x
entry={}
for i in range(8): entry[f"PCIE_UP_OUT{i}_N_J2"]=(Nx[i],55.823,Nx[i])
for i in range(7): entry[f"PCIE_UP_OUT{i}_P_J2"]=(A[f"PCIE_UP_OUT{i}_P_J2"][0],54.880,slit[i])
entry["PCIE_UP_OUT7_P_J2"]=(93.700,55.130,93.700)
# B 侧西组分层（x_B 升序 → y 由北到南）
west=[nm for nm in order if B[nm][0]<135.40]
west.sort(key=lambda nm:B[nm][0])
westY={nm:37.00+0.50*r for r,nm in enumerate(west)}
Y0=59.00
track=lambda k: Y0+PITCH*(16-k)
colx =lambda k: 135.60+PITCH*(16-k)
TURN=41.00   # 东通道内北上到此高度
routes={}
for k,nm in enumerate(order,start=1):
    ax,ay,dx=entry[nm]; yk=track(k); X=colx(k); xb,yb=B[nm]
    pts=[(ax,ay)]
    if abs(dx-ax)>1e-6: pts.append((dx,ay))     # 平移到缝心（同 y）
    pts.append((dx,55.823))                     # 穿缝/直下
    pts.append((dx,yk))                         # 落到本线水平层
    pts.append((X,yk))                          # 东行
    pts.append((X,TURN))                        # 通道内北上
    if xb>=135.40:                              # 东组：通道内横移到锚
        pts.append((X,yb)); pts.append((xb,yb))
    else:                                       # 西组：北拐→西行→南落
        wy=westY[nm]
        pts.append((X,wy)) if wy<TURN else None
        pts=[(a,b) for (a,b) in pts]
        # 从 (X,TURN) 北上到 wy，再西行到 xb，再南落到 yb
        pts=[(ax,ay)]
        if abs(dx-ax)>1e-6: pts.append((dx,ay))
        pts.append((dx,55.823)); pts.append((dx,yk)); pts.append((X,yk))
        pts.append((X,wy)); pts.append((xb,wy)); pts.append((xb,yb))
    routes[nm]={"pts":[[round(a,4),round(b,4)] for a,b in pts],"len_mm":0.0}
anchors=v3.lane_anchors(model)
for an in anchors: an["A"]=tuple(A[an["net"]]); an["B"]=tuple(B[an["net"]])
gate=v3.exact_gate(model,routes,anchors,"In5.Cu",HW,frozenset(),frozenset(),PITCH,frozenset())
print("routed",len(routes),"/16")
print(json.dumps({k:gate[k] for k in ("lane_pitch_min_gap_mm","n_lane_pitch_viol","clearance_min_mm","n_clearance_viol","endpoint_max_dev_mm")},ensure_ascii=False))
print("viol pairs:",gate.get("lane_pitch_violations",[])[:10])
print("clearance viol:",gate.get("clearance_violations",[])[:8])
json.dump({"artifact":"k2_r263_coordinate_comb_v2","routes":routes,"gate":gate},open('/tmp/opencode/archer/r261/wo_comb2.json','w'),ensure_ascii=False,indent=1,sort_keys=True)
