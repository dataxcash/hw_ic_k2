"""#K2-176 §四.5 闸声度自证：以**在册 exact_gate**（要求级谓词）对 R494 之模型解**复跑** ⇒ 须 FAIL。
（不重跑求解器：只从 R494 落件之解重建折线，再用要求级尺量。）"""
import json,sys,math
sys.path.insert(0,"/home/fila/jqdDev_2025/ic_hw/k2/tools")
from k2_p4_b2_in5_lane_router_v3 import lane_anchors, exact_gate
m=json.load(open("/tmp/opencode/archer/model_l8.json"))
an=[a for a in lane_anchors(m) if a["net"].startswith("PCIE_UP_OUT")]
A={a["net"]:a["A"] for a in an}; B={a["net"]:a["B"] for a in an}
sol=json.load(open("/tmp/opencode/r494/full.json"))["sol"]
P=0.435; routes={}
for d in sol:
    nm=d["nm"]; ax,ay=A[nm]; bx,by=B[nm]
    pts=[(ax,ay),(d["ci"],56.6),(d["ci"],d["s"]),(d["xe"],d["e"]),(d["px"],d["e"]),(d["px"],d["ny"]),(bx,d["ny"]),(bx,by)]
    o=[pts[0]]
    for q in pts[1:]:
        if math.dist(q,o[-1])>1e-9: o.append(q)
    routes[nm]={"pts":o,"layer_cu":"In5.Cu","n_vias":2}
g=exact_gate(m,routes,an,"In5.Cu",0.08,set(),set(),P,frozenset())
out={"GATE_SOUNDNESS":{"n_lane_pitch_viol":g["n_lane_pitch_viol"],
     "lane_pitch_min_gap_mm":g["lane_pitch_min_gap_mm"],"lane_pitch_min_pair":g["lane_pitch_min_pair"],
     "n_clearance_viol":g["n_clearance_viol"],"endpoint_max_dev_mm":g["endpoint_max_dev_mm"],
     "verdict":"FAIL" if (g["n_lane_pitch_viol"]>0 or g["n_clearance_viol"]>0 or g["endpoint_max_dev_mm"]>0) else "PASS"},
     "soundness_proved":(g["n_lane_pitch_viol"]>0 or g["n_clearance_viol"]>0)}
print(json.dumps(out,ensure_ascii=False,indent=1))
print("⇒ 新闸（要求级 · 复用在册 exact_gate）对 R494 模型 =",out["GATE_SOUNDNESS"]["verdict"],
      "⇒ 闸声度自证",("成立（拦得住 R494 那类假合格）" if out["soundness_proved"] else "不成立 ⇒ 打回"))
json.dump(out,open("/tmp/opencode/r495/gatesound.json","w"),ensure_ascii=False,default=str)
