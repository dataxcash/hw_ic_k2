import json,hashlib,datetime,os,time
from ortools.sat.python import cp_model
# 小实例（≤4 线 × 小域）· 同一套约束形态：序变量 + AllDifferent + 单调序
# 手算已知答案：4 线按【西→东】各占座位 0,1,2,3；层 0,1,2,3（层=洋葱嵌套）
def build(nlane,nseat,nlayer,force=None):
    m=cp_model.CpModel()
    seat={i:m.NewIntVar(0,nseat-1,f"seat{i}") for i in range(nlane)}
    layer={i:m.NewIntVar(0,nlayer-1,f"layer{i}") for i in range(nlane)}
    m.AddAllDifferent([seat[i] for i in range(nlane)])
    m.AddAllDifferent([layer[i] for i in range(nlane)])
    for i in range(nlane-1):
        m.Add(seat[i]<seat[i+1])      # 座次随 A 锚 x 序单调
        m.Add(layer[i]<layer[i+1])    # 层随 x 序单调（洋葱嵌套）
    if force:
        for (k,s,l) in force: m.Add(seat[k]==s); m.Add(layer[k]==l)
    return m,seat,layer
def solve(m):
    sv=cp_model.CpSolver(); sv.parameters.max_time_in_seconds=10.0
    t0=time.time(); st=sv.Solve(m); dt=(time.time()-t0)*1000
    return sv,st,dt
out={"form":"ordinal vars + AllDifferent + monotone order (CP-SAT standard form)",
     "no_candidate_sets":True}
# 1) 可解见证（手算答案 = seat 0..3 / layer 0..3 一一对应）
m,seat,layer=build(4,4,4)
sv,st,dt=solve(m)
hand=[0,1,2,3]
got={"seat":[sv.Value(seat[i]) for i in range(4)],"layer":[sv.Value(layer[i]) for i in range(4)]}
out["witness"]={"status":sv.StatusName(st),"wall_ms":round(dt,2),"got":got,
                "hand_known":hand,"match":got["seat"]==hand and got["layer"]==hand}
# 2) 负控 A：座位不足（5 线 4 座）⇒ 应 INFEASIBLE
m2,_,_=build(5,4,5); sv2,st2,_=solve(m2)
out["neg_A_seats_shortage"]={"status":sv2.StatusName(st2),"expect":"INFEASIBLE","ok":st2==cp_model.INFEASIBLE}
# 3) 负控 B：层不足（5 线 4 层）⇒ 应 INFEASIBLE
m3,_,_=build(5,5,4); sv3,st3,_=solve(m3)
out["neg_B_layers_shortage"]={"status":sv3.StatusName(st3),"expect":"INFEASIBLE","ok":st3==cp_model.INFEASIBLE}
# 4) 负控 C：强制同位（与 AllDifferent 冲突）⇒ 应 INFEASIBLE
m4,_,_=build(4,4,4,force=[(0,0,0),(1,0,1)]); sv4,st4,_=solve(m4)
out["neg_C_forced_same_seat"]={"status":sv4.StatusName(st4),"expect":"INFEASIBLE","ok":st4==cp_model.INFEASIBLE}
# 5) 负控 D：强制同层 ⇒ 应 INFEASIBLE
m5,_,_=build(4,4,4,force=[(0,0,0),(1,1,0)]); sv5,st5,_=solve(m5)
out["neg_D_forced_same_layer"]={"status":sv5.StatusName(st5),"expect":"INFEASIBLE","ok":st5==cp_model.INFEASIBLE}
# 6) Validate 零错（全模型）
out["validate"]={ "m1":build(4,4,4)[0].Validate()=="" , "neg_ok": all(out[k]["ok"] for k in ("neg_A_seats_shortage","neg_B_layers_shortage","neg_C_forced_same_seat","neg_D_forced_same_layer"))}
out["verdict"]="小实例见证 " + ("PASS（可解 + 手算一致 + 四类负控全拦）" if (out["witness"]["match"] and out["validate"]["neg_ok"]) else "FAIL")
print(json.dumps(out,ensure_ascii=False,indent=1))
json.dump(out,open("/tmp/opencode/r455_toy_out.json","w"),ensure_ascii=False,indent=1)
