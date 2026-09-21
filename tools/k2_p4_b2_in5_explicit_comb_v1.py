#!/usr/bin/env python3
"""R262 · **显式梳子构造**（人画坐标 · 零搜索）—— ②-UP：A 侧 no-move 入口（`_P` 穿 `_N` 缝）+ 南通道梳子 + 东通道列 + B 侧。核心闸 v3.exact_gate。"""
import json,math,sys,importlib.util,numpy as np
HERE="/home/fila/jqdDev_2025/ic_hw/k2"
spec=importlib.util.spec_from_file_location("v3m",HERE+"/tools/k2_p4_b2_in5_lane_router_v3.py")
v3=importlib.util.module_from_spec(spec);spec.loader.exec_module(v3)
LS={f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N","P")}
v3.is_lane=lambda n:n in LS
_o=v3.req; v3.req=lambda n:(0.175 if n in LS else _o(n))
v3.PAD_EXTRA=0.100
model=json.load(open('/tmp/opencode/archer/model_crop.json'))
A=json.load(open('/tmp/opencode/archer/sites_phys.json'))      # l8 板载实位（no-move）
B=json.load(open('/tmp/opencode/archer/sites_b_board_v1.json'))
PITCH=0.435; HW=0.08
# --- A 侧入口点（板载实位）---
# _N 行 y=55.823 ；_P 行 y=54.880（0..6：穿 _N 缝；7_P 于 x=93.70 直接南下）
Nx=sorted(A[f"PCIE_UP_OUT{i}_N_J2"][0] for i in range(8))
slit=[(Nx[i]+Nx[i+1])/2 for i in range(7)]                    # 7 条缝中心 x
entry={}
for i in range(8):
    entry[f"PCIE_UP_OUT{i}_N_J2"]=("N", Nx[i], 55.823)
for i in range(7):
    entry[f"PCIE_UP_OUT{i}_P_J2"]=("P", slit[i], 54.880)      # 需先斜下穿缝
entry["PCIE_UP_OUT7_P_J2"]=("P7", 93.700, 55.130)
order=[f"PCIE_UP_OUT{i}_{s}_J2" for i in range(8) for s in ("N","P")]   # A.x 序 = k=1..16
# --- 南通道梳子：k=1 最深 ---
Y0=59.00
def track(k): return Y0+PITCH*(16-k)
def colx(k):  return 135.60+PITCH*(16-k)
routes={}
for k,nm in enumerate(order,start=1):
    typ,xe,ye=entry[nm]
    yk=track(k); Xk=colx(k)
    pts=[(xe,ye)]
    if typ=="P":                       # 从 _P 锚斜下到缝中心（在 y=55.823 处正好于缝内）
        pts.append((xe,55.823))        # 竖直段（xe≈缝心）
    pts.append((xe,yk))                # 落到本线水平层
    pts.append((Xk,yk))                # 东行
    pts.append((Xk,56.20))             # 北上进入东通道列
    pts.append((Xk,41.70))             # 通道内北行到顶
    xb,yb=B[nm]
    if xb>=135.40:                     # 东组：通道内直接横移到锚
        pts.append((Xk,yb)); pts.append((xb,yb))
    else:                              # 西组：顶部西行 → 再南下到锚
        pts.append((xb,41.70)); pts.append((xb,yb))
    routes[nm]={"pts":[[round(a,4),round(b,4)] for a,b in pts],"len_mm":0.0}
anchors=v3.lane_anchors(model)
for an in anchors:
    an["A"]=tuple(A[an["net"]]); an["B"]=tuple(B[an["net"]])
gate=v3.exact_gate(model,routes,anchors,"In5.Cu",HW,frozenset(),frozenset(),PITCH,frozenset())
print("routed",len(routes),"/16")
print(json.dumps({k:gate[k] for k in ("lane_pitch_min_gap_mm","n_lane_pitch_viol","clearance_min_mm","n_clearance_viol","endpoint_max_dev_mm")},ensure_ascii=False))
vp=gate.get("lane_pitch_violations",[])[:12]
print("前 12 对互距违规:",vp)
json.dump({"artifact":"k2_r262_explicit_comb_v1","routes":routes,"gate":gate},open('/tmp/opencode/archer/r261/wo_comb.json','w'),ensure_ascii=False,indent=1,sort_keys=True)
