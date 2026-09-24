"""核（kernel）：②-UP 单层 In5 之守恒级容量核算 —— 机器可核的不等式链。
只读几何（在册 Raster/build_base · 与闸/判据同口径）· 不打求解器。
"""
import json,sys,math
sys.path.insert(0,"/home/fila/jqdDev_2025/ic_hw/k2/tools")
import numpy as np
from k2_p4_b2_in5_lane_router_v3 import Raster, build_base
import k2_p4_b2_in5_lane_router_v3 as RT
RT.PAD_EXTRA=0.100+0.5*0.03*math.sqrt(2)
m=json.load(open("/tmp/opencode/archer/model_l8.json"))
rast=Raster(m["bbox"],0.03); bad=build_base(rast,m,"In5.Cu",set(),set(),0.08,frozenset())
P=0.435
def clear(y,x0,x1,st=0.01):
    xs=np.arange(x0,x1+1e-9,st); i=np.rint((xs-rast.X0)/rast.step).astype(int); j=int(round((y-rast.Y0)/rast.step))
    if not(0<=j<rast.NY): return False
    ok=(i>=0)&(i<rast.NX)
    return bool(ok.all()) and (not bad[i,j].any())
def pack(lo,hi,x0,x1):
    lv=[y for y in np.arange(lo,hi,0.01) if clear(y,x0,x1)]
    out=[];last=None
    for y in lv:
        if last is None or y-last>=P-1e-9: out.append(round(y,2)); last=y
    return out
# (1) 夹缝带 x∈[132.1,136] 可穿层位（= 唯一通路的"门缝层位"）
FENCE=pack(56.0,68.4,132.1,136.0)
# (2) 长跨（锚侧直达门）可穿层位
LONG =pack(56.0,68.4,95.745,135.45)
# (3) 西侧自由带上沿（西段行不碰夹缝 ⇒ 上沿由 x=98 处决定）
XS=[]
for y in np.arange(56.0,69.0,0.01):
    xs=np.arange(95.0,99.0,0.02); i=np.rint((xs-rast.X0)/rast.step).astype(int); j=int(round((y-rast.Y0)/rast.step))
    if 0<=j<rast.NY and (i<rast.NX).all() and not bad[i,j].any(): XS.append(round(y,2))
WEST_CAP=max(XS)
ONLY=[y for y in FENCE if y not in LONG]          # 只有"东跨"才能用的层位
CAP=WEST_CAP-P                                              # 西段行上沿
BELOW=[y for y in LONG if y <= CAP-P]                       # 受迫降到此带以下的长跨层位
out={"fence_levels_n":len(FENCE),"fence_levels":FENCE,
     "long_span_levels_n":len(LONG),"long_span_levels":LONG,
     "east_only_levels":ONLY,
     "west_band_cap_mm":WEST_CAP,
     "block_band_lower_bound_mm":round(CAP,3),
     "others_level_upper_bound_mm":round(CAP-P,3),
     "long_levels_at_or_below_that_n":len(BELOW),"long_levels_at_or_below_that":BELOW,
     "max_lanes":len(BELOW)+len(ONLY),"required":16}
print(json.dumps(out,ensure_ascii=False,indent=1))
print("\n==> cap = %d + %d = %d  <  16"%(len(BELOW),len(ONLY),out["max_lanes"]))
open("/tmp/opencode/r481/kernel.json","w").write(json.dumps(out,ensure_ascii=False,indent=1))
