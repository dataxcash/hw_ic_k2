#!/usr/bin/env python3
"""k2_p6_b2t_combined_probe_v1.py — B2-T 续作 (m) 只读探针：**跨廊道 0.4mm 偏移 × 层换位** 组合性质。

合成 fixture（零真板依赖）：U7 侧 PCIE_X1_P/N（异排 0.4）+ J2 连接器；SPEC 两走廊 `C_MAIN`(48.7)
与 `C_ALT`(49.1 = +0.4)；alloc `seg_tracks={input:48.7, out_J2:49.1}`、分配廊道 = C_MAIN。
实测（本工具打印）：
  · `_track_y_for(..., "C_ALT", "out_J2")` = (49.1, F.Cu)  ← 跨廊道同 band 索引映射
  · `_track_y_for(..., "C_MAIN", "out_J2")` = None        ← fail-closed 负例（seg 轨道不在该廊道 band 内）
  · `_layer_swap_escape(..., track_y=48.7)` = SOLVED/LSWAP 且两次调用逐字节同
  · `_layer_swap_escape(..., track_y=49.1)` = SOLVED/LSWAP 且两次调用逐字节同
用途：为下一轮 A15（合成组合性质用例）提供**已实测期望值**；本脚本不写仓库、写 /tmp。
用法：python3 k2/tools/k2_p6_b2t_combined_probe_v1.py
"""
import json, sys
from pathlib import Path
REPO=Path("/home/fila/jqdDev_2025/ic_hw"); sys.path.insert(0,str(REPO/"k2/_shared"))
from eda_core.hs_route_model import HSRouteModel, pair_endpoints, build_hs_field, _path_pn_min_edge_pt
T=Path("/tmp/opencode/m_probe"); T.mkdir(parents=True, exist_ok=True)
pcb=T/"b.kicad_pcb"
pcb.write_text('''
(kicad_pcb (version 20260306) (generator "test")
\t(footprint "U7" (layer "F.Cu") (at 100 55.2 0)
\t\t(pad "1" smd rect (at 0 0) (size 0.45 0.25) (layers "F.Cu" "F.Paste" "F.Mask") (net "PCIE_X1_P") (uuid "u1"))
\t\t(pad "2" smd rect (at 0 0.4) (size 0.45 0.25) (layers "F.Cu" "F.Paste" "F.Mask") (net "PCIE_X1_N") (uuid "u2"))
\t)
\t(footprint "J2" (layer "F.Cu") (at 133.825 55.2 0)
\t\t(pad "1" smd rect (at 1.175 -0.3) (size 1.3 0.35) (layers "F.Cu" "F.Paste" "F.Mask") (net "PCIE_X1_P") (uuid "j1"))
\t\t(pad "2" smd rect (at -1.175 0.3) (size 1.3 0.35) (layers "F.Cu" "F.Paste" "F.Mask") (net "PCIE_X1_N") (uuid "j2"))
\t)
)
''', encoding="utf-8")
spec=T/"s.json"
spec.write_text(json.dumps({"spec_version":"1.0",
  "components":{"redriver":{},"connectors":{"J2":{"pos":[133.825,55.2],"footprint":"MCIO_4i_SFF-1016_RASide"}}},
  "corridors":[
    {"id":"C_MAIN","x_range":[98.83,131.5],"y_range":[46.0,52.0],
     "bands":[{"band":"upper","layer":"F.Cu","tracks_y":[48.7],"pairs":8}]},
    {"id":"C_ALT","x_range":[98.83,131.5],"y_range":[46.0,52.0],
     "bands":[{"band":"upper","layer":"F.Cu","tracks_y":[49.1],"pairs":8}]}],
  "impedance":{"width_mm":0.205}}), encoding="utf-8")
alloc=T/"a.json"
alloc.write_text(json.dumps({"alloc":{"PCIE_X1":{"band":"upper","track_y":48.7,"corridor":"C_MAIN",
  "layer":"F.Cu","status":"SOLVED","seg_tracks":{"input":48.7,"out_J2":49.1}}}}), encoding="utf-8")
m=HSRouteModel(str(pcb),str(spec),str(alloc),str(REPO/"k2/_shared/eda_core/drc_rules.json"))
out={}
tv=m._track_y_for("PCIE_X1_P","C_ALT","out_J2"); out["track_y_C_ALT_out_J2"]=list(tv) if tv else None
tv2=m._track_y_for("PCIE_X1_P","C_MAIN","out_J2"); out["track_y_C_MAIN_out_J2"]=list(tv2) if tv2 else None
ep=pair_endpoints(m.board,"PCIE_X1_P","PCIE_X1_N")
j2_p,j2_n=ep["P"][1],ep["N"][1]
fcu=build_hs_field(m.board,m.rules,layer="F.Cu",clear_hs_pads=True,config=m.config,clear_hs_nets=("PCIE_X1_P","PCIE_X1_N"))
in2=build_hs_field(m.board,m.rules,layer="In2.Cu",clear_hs_pads=True,config=m.config,clear_hs_nets=("PCIE_X1_P","PCIE_X1_N"))
pn_ok=lambda p,l,n,ln:(lambda me:(me is None or me>=0.155))(_path_pn_min_edge_pt(p,l,n,ln,0.205)[0])
for ty in (48.7,49.1):
    args=dict(corr_x=131.5,track_y=ty,bound_x=98.83,direction=-1,net_p="PCIE_X1_P",net_n="PCIE_X1_N",
              flip=False,esc_layer="In2.Cu",pn_ok=pn_ok)
    r=m._layer_swap_escape(fcu,fcu,in2,j2_p,j2_n,**args)
    r2=m._layer_swap_escape(fcu,fcu,in2,j2_p,j2_n,**args)
    out[f"lswap_track_{ty}"]={"status":None if r is None else r.get("status"),"kind":None if r is None else r.get("kind"),
                              "deterministic":json.dumps(r,sort_keys=True)==json.dumps(r2,sort_keys=True)}
print(json.dumps(out,ensure_ascii=False,indent=1,default=str))
