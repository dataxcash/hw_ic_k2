#!/usr/bin/env python3
"""K2 · ②(ii) 几何级 —— 用 `k2_p4_b2_plane_layer_extract_v1.py` 之平面层模型，
逐网核**新走线**之参考层回流通路（相邻平面层 net + 是否跨分割）。只读。"""
import json,math,sys
import numpy as np
P=json.load(open('/tmp/opencode/k2r372/planes_planes.json'))
CELL=P['cell_mm']; X0,Y0=P['bbox'][0],P['bbox'][1]
ID={v:k for k,v in P['netid'].items()}
R={}
for L in ('In1.Cu','In3.Cu','In4.Cu','In6.Cu'):
    R[L]=np.load('/tmp/opencode/k2r372/planes_%s.npy'%L.replace('.','_'))
def net_at(L,x,y):
    a=R[L]; i=int(round((x-X0)/CELL)); j=int(round((y-Y0)/CELL))
    if i<0 or j<0 or j>=a.shape[0] or i>=a.shape[1]: return None
    return ID.get(int(a[j,i]),'?') or 'NONE'
ADJ={'In5.Cu':('In4.Cu','In6.Cu'),'In2.Cu':('In1.Cu','In3.Cu'),'F.Cu':(None,'In1.Cu'),'B.Cu':('In6.Cu',None),'In1.Cu':(None,'In2.Cu')}
def scan(name,layer,pts):
    up,dn=ADJ[layer]; prof=[]
    for k in range(len(pts)-1):
        x1,y1=pts[k];x2,y2=pts[k+1]
        n=max(2,int(math.hypot(x2-x1,y2-y1)/0.1)+1)
        for t in range(n+1):
            x=x1+(x2-x1)*t/n; y=y1+(y2-y1)*t/n
            prof.append((net_at(up,x,y) if up else 'N/A', net_at(dn,x,y) if dn else 'N/A'))
    def runs(seq):
        out=[];cur=None;n=0
        for v in seq:
            if v!=cur: 
                if cur is not None: out.append((cur,n))
                cur=v;n=1
            else: n+=1
        if cur is not None: out.append((cur,n))
        return out
    upr=runs([p[0] for p in prof]); dnr=runs([p[1] for p in prof])
    tot=len(prof)
    res={"layer":layer,"n_samples":tot,
      "above(up)": {k:round(v/tot,4) for k,v in upr},
      "below(dn)": {k:round(v/tot,4) for k,v in dnr},
      "n_splits_up": max(0,len(upr)-1), "n_splits_dn": max(0,len(dnr)-1),
      "up_runs": upr[:6], "dn_runs": dnr[:6]}
    print("  %-46s %-7s n=%5d  above=%s  below=%s  splits up/dn=%d/%d"%(
        name,layer,tot,res["above(up)"],res["below(dn)"],res["n_splits_up"],res["n_splits_dn"]))
    return res
ST=json.load(open('/tmp/opencode/k2r135/stubs.json'))
NC=json.load(open('/tmp/opencode/k2r135b/nc_fixed.json'))
out={}
print("== ②(ii) 参考层回流通路（新走线）==")
out['DS320_STRAP_B_ADDR1_7-0']={"new_trace_In2":scan('ADDR1_7-0 new In2 trace','In2.Cu',ST['netA_in2_direct']['polyline_simplified'])}
print("== N-B ==")
out['DS320_STRAP_B_ADDR0_15-8']={"stub_F_Cu":scan('ADDR0_15-8 stub F.Cu','F.Cu',json.load(open('/tmp/opencode/k2r135b/final_reloc.json'))['netB']['stub_top_polyline']),
  "stub_B_Cu":scan('ADDR0_15-8 stub B.Cu','B.Cu',json.load(open('/tmp/opencode/k2r135b/final_reloc.json'))['netB']['stub_bot_polyline'])}
print("== N-C ==")
out['I2C1_SDA']={"stub_In5":scan('I2C1_SDA stub In5','In5.Cu',NC['stub_top_polyline']),
  "stub_B_Cu":scan('I2C1_SDA stub B.Cu','B.Cu',NC['stub_bot_polyline'])}
print("== PERSTA# (R337) ==")
P337=json.load(open('/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K2_R337_CW_PERSTA_DESTINATION_ROUTE_v1.json'))
out['PERSTA#']={"alt_In5":scan('PERSTA# alt In5 (R337)','In5.Cu',[list(p) for p in P337['route_pts']])}
# 保留之 In5 铜（窗外）也扫一遍
for nm,flag in (('DS320_STRAP_B_ADDR1_7-0',0),('I2C1_SDA',0)):
    pass
json.dump({"cell_mm":CELL,"plane_source":"k2_p4_b2_plane_layer_extract_v1.py（纯文本解析 .kicad_pcb zone fill）",
           "plane_nets":{"In4.Cu":list(P['layers']['In4.Cu']['nets']),"In6.Cu":list(P['layers']['In6.Cu']['nets']),
                          "In1.Cu":list(P['layers']['In1.Cu']['nets']),"In3.Cu":list(P['layers']['In3.Cu']['nets'])},
           "per_net":out},open('/tmp/opencode/k2r372/refcheck.json','w'),ensure_ascii=False,indent=1)
print("saved")
