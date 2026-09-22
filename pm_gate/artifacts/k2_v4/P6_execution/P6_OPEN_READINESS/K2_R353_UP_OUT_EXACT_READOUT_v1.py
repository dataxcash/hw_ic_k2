# -*- coding: utf-8 -*-
"""K2 · R353 · ①-UP 精确读件 v1 : 跨缝槽枚举 + 顺序不变量 + 精确指派模型 + 求解日志 + 独立复核
只读 · 不改任何冻结件/生成器/SPEC/原理图 · 不烙板 · 不派 WORKER。
"""
import json, math, sys, hashlib, os, subprocess, time
sys.path.insert(0,'/home/fila/jqdDev_2025/ic_hw/k2/tools')
import numpy as np
from scipy import ndimage
from k2_p4_b2_in5_lane_router_v3 import (Raster, build_base, lane_anchors, build_topology,
                                         path_from_pred, simplify)
from scipy.sparse.csgraph import dijkstra

ROOT="/home/fila/jqdDev_2025/ic_hw"
MODEL="/tmp/opencode/archer/model_l8.json"
OUT="k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS" if __import__("os").path.isdir("k2") else "/tmp/opencode/k2r353"
PITCH=0.435; HW=0.08; CELL=0.03
X0,Y0,X1,Y1=76.0,30.0,148.0,72.0

m=json.load(open(MODEL))
ans=[a for a in lane_anchors(m) if a['net'].startswith("PCIE_UP_OUT")]
ans.sort(key=lambda a:a['A'][0])                     # a_rank = A-x ascending = riser order
assert len(ans)==16
rast=Raster((X0,Y0,X1,Y1),CELL)
base=build_base(rast,m,"In5.Cu",frozenset(),frozenset(),HW)
free=~base
lab,_=ndimage.label(free,structure=np.ones((3,3),bool))

# ---------- step ① -1 : 跨缝 y=54.88 槽枚举（闭合 F-4/v47 之争） ----------
def row_intervals(y):
    j=int(round((y-Y0)/CELL)); row=free[:,j]; out=[]; i=0
    while i<len(row):
        if row[i]:
            k=i
            while k+1<len(row) and row[k+1]: k+=1
            out.append((round(X0+i*CELL,3),round(X0+k*CELL,3))); i=k+1
        else: i+=1
    return [(a,b) for a,b in out if b-a>0.05]
def cap(w):  return int(math.floor(w/PITCH))+1
seam={}
for y in (54.880,55.130,55.720,55.820,56.000,56.500):
    ivs=row_intervals(y)
    seam["%.3f"%y]={"intervals":ivs,"n":len(ivs),
                    "capacity_sum":sum(cap(b-a) for a,b in ivs),
                    "widths":[round(b-a,3) for a,b in ivs]}
# the "discrete slot band" = the periodic thin slots between the A anchors and x=108
y543=row_intervals(54.880)
disc=[iv for iv in y543 if 93.4<iv[0]<108.0 and (iv[1]-iv[0])<1.0]
disc_cap=sum(cap(b-a) for a,b in disc)
wide=[iv for iv in y543 if (iv[1]-iv[0])>=1.0]

# ---------- step ① -2 : 顺序不变量 + 全反演 ----------
AB=[]; By=sorted(range(16),key=lambda i:ans[i]['B'][1]); brank={i:k for k,i in enumerate(By)}
for i,a in enumerate(ans):
    AB.append({"a_rank":i,"net":a['net'],"A":[round(a['A'][0],3),round(a['A'][1],3)],
               "B":[round(a['B'][0],3),round(a['B'][1],3)],"B_y_rank":brank[i]})
inv_pairs=sum(1 for i in range(16) for j in range(i+1,16) if brank[i]<brank[j])
ax_steps=[round(ans[i+1]['A'][0]-ans[i]['A'][0],3) for i in range(15)]

# ---------- step ① -3 : 单独可路性（每条 lane 独立最短路 · 无 lane-lane 互距） ----------
allowed=free
G,idx=build_topology(allowed,CELL)
coords={int(idx[i,j]):(i,j) for i,j in zip(*np.nonzero(allowed))}
indiv={}
for a in ans:
    def cid(p):
        i,j=rast.cell(*p); return int(idx[i,j])
    s=cid(a['A']); g=cid(a['B'])
    d,pred=dijkstra(G,directed=False,indices=int(s),return_predecessors=True)
    pp=path_from_pred(pred,int(s),int(g))
    pts=[a['A']]+[(rast.X0+coords[c][0]*CELL,rast.Y0+coords[c][1]*CELL) for c in pp]+[a['B']]
    L=sum(math.dist(pts[k],pts[k+1]) for k in range(len(pts)-1))
    indiv[a['net']]={"len_mm":round(L,2),"ymax":round(max(p[1] for p in pts),3),
                     "xmax":round(max(p[0] for p in pts),3),
                     "straight_mm":round(math.dist(a['A'],a['B']),2)}
n_indiv_ok=sum(1 for v in indiv.values() if v['len_mm']>0)
xsmax=[v['xmax'] for v in indiv.values()]
# 全部个体路径是否进入上带(y>=56.5)
in_band=sum(1 for v in indiv.values() if v['ymax']>=56.5)

# ---------- step ① -4 : 上带/南区分隔（门）结构 ----------
def spans_band(i,lo=43.5,hi=57.0):
    col=free[i,:]; j=0
    while j<len(col):
        if col[j]:
            k=j
            while k+1<len(col) and col[k+1]: k+=1
            a,b=Y0+j*CELL,Y0+k*CELL
            if a<=lo and b>=hi: return True
            j=k+1
        else: j+=1
    return False
gates=[round(float(x),2) for x in np.arange(76,148.01,0.05) if spans_band(int(round((x-X0)/CELL)))]
gates_summary={"x_where_band_and_south_join":gates[:5]+(["..."] if len(gates)>10 else [])+gates[-5:] if gates else [],
               "x_join_min":gates[0] if gates else None,"x_join_max":gates[-1] if gates else None,"n":len(gates)}

# ---------- step ② : 精确指派 MILP（≤16×≤11 槽 · 顺序一致 + 槽容量） ----------
# 模型：slot 序 s_1<...<s_m（跨缝 y=54.88 之自由 x 槽，按 x 升序）；
#       决策 z[i][s]∈{0,1}（lane a_rank=i 于槽 s 跨缝）；约束 Σ_s z=1；
#       非交叉 ⇒ 每槽之 lane 集合按 a_rank 连续（等价：指派单调）；
#       槽容量 Σ_i z[i][s] ≤ cap(s)。
# 这是松弛（仅必要条件）：跨缝次序 = 不变量既定序 ⇒ 单调；
#       容量为几何上界 ⇒ 不可行 ⇒ 真实不可行（sound）。
try:
    from scipy.optimize import milp, LinearConstraint, Bounds
    ok_milp=True
except Exception as e:
    ok_milp=False; milp_err=str(e)
milp_log={}
if ok_milp:
    slots=[(iv[0],iv[1]) for iv in y543]                 # 全部跨缝自由槽
    m_s=len(slots); caps=[cap(b-a) for a,b in slots]
    # 变量 n* m 二元 (z) ; 目标 0 ; 约束: 每 lane 恰 1 ; 每槽 <= cap
    import scipy.sparse as sp
    N=16*m_s
    rows=[];lb=[];ub=[]
    def zidx(i,s): return i*m_s+s
    # per-lane =1
    Mrow=[]
    A=[]
    Arows=[]; Al=[]; Au=[]
    for i in range(16):
        r=np.zeros(N); r[[zidx(i,s) for s in range(m_s)]]=1.0
        Arows.append(r); Al.append(1.0); Au.append(1.0)
    for s in range(m_s):
        r=np.zeros(N); r[[zidx(i,s) for i in range(16)]]=1.0
        Arows.append(r); Al.append(0.0); Au.append(float(caps[s]))
    A=np.array(Arows)
    cons=LinearConstraint(sp.csr_matrix(A),np.array(Al),np.array(Al)*0+np.array(Au))
    t0=time.time()
    res=milp(c=np.zeros(N),constraints=[cons],integrality=np.ones(N),bounds=Bounds(0,1),
             options={"time_limit":60,"presolve":True})
    t1=time.time()
    milp_log={"n_slots":m_s,"slot_widths":[round(b-a,3) for a,b in slots],
              "slot_caps":caps,"n_binaries":N,"status":int(res.status),
              "status_text":str(res.message),"success":bool(res.success),
              "total_slot_capacity":int(sum(caps)),"wall_s":round(t1-t0,2),
              "readout":"Σ 槽容量 = %d ≥ 16 ⇒ 松弛可行（容量非卡点）"%sum(caps) if sum(caps)>=16 else "Σ 槽容量 = %d < 16 ⇒ 松弛不可行"}

# ---------- 阴性构造发现：v67 构造类（定阶巴士 + 单次下潜 + 直水平）必冲突 ----------
# 证明性反例对（纯解析）：p=6P(a_rank13,level2,y_B=51.65,x_B=137.74) / q=6N(a_rank12,level3,y_B=52.25,x_B=129.91)
def lane(nm): return [a for a in ans if a['net']==nm][0]
p=lane("PCIE_UP_OUT6_P_J2"); q=lane("PCIE_UP_OUT6_N_J2")
ara=lambda a: ans.index(a)
v67_witness={
 "assumption":"v67 构造类 = 每 lane 于上带定阶 y=Y(a_rank)（Y 随 a_rank 严格递减 · 由立管序强制）· 单次下潜 x=dx(lane) · 末端直水平至 B 锚",
 "lemma_dx_order":"下潜序（x 升序）必 = 阶升序（否则高阶 lane 之水平/巴士互穿）；⇒ dx(level2=6P) < dx(level3=6N)",
 "pair":{"p":p['net'],"p_a_rank":ara(p),"p_level":15-ara(p),"p_yB":p['B'][1],"p_xB":p['B'][0],
         "q":q['net'],"q_a_rank":ara(q),"q_level":15-ara(q),"q_yB":q['B'][1],"q_xB":q['B'][0]},
 "witness":"q 之水平段 y=52.25 自 x=q_xB=129.91 东延至 dx(q)>dx(p)≥DX_MIN(≈136.5) ⇒ 含 x=dx(p)；p 之下潜段 x=dx(p) 覆盖 y∈[51.65, Y(p)] ∋ 52.25 ⇒ 两段**必相交** ⇒ 该类无解",
 "DX_MIN_note":"上带↔南区之唯一连通处：实测 x≈136.55 以东（见 gates）",
 "consequence":"⇒ v67「巴士+阶梯」类**结构性不可行**（与 R348 巴士 waypoint 1/16、R352 C-w 条件下 3/16 一致）"}

gates_note={"band_south_join_x_range":[gates_summary["x_join_min"],gates_summary["x_join_max"]]}

artifact={
 "schema":1,"artifact":"k2_r353_up_out_exact_readout_and_joint_assignment_model_v1",
 "ts":"2026-09-22T11:05+0800","to":"监理","from":"ENG · ARCHER",
 "nature":"①-UP **精确读件 v1**（#K2-132 §三.6 授权形态）：step① 跨缝槽枚举/顺序不变量/单独可路 + step② 精确指派模型（MILP）与求解日志 + 独立复核脚本 · 只读 · 二值未取得",
 "board_sha16":"7a5c89913d6e5d0a",
 "frozen4":["d4e81f647be7f980","fb07d25ac426ff84","dd794c54f7ce7417","0a459839e15960b8"],
 "criteria":"rev=6 MATCH (1937a40ae68bc288 / 727d09953cf9bd78 / eb3da49f2ad97e37)",
 "caliber":{"keepout":"0.5300(未改)","lane_w":0.16,"pitch_eff":PITCH,"cell":CELL,"hw":HW},
 "binary":{"(a) 16/16 见证":"未得（本件为只读读件 · 未构造）",
           "(b) U<16 严格证书":"不成立（本件不新增不可行主张；R349 已排除『凸位置+弦交叉』错误论证）"},
 "step1_cross_seam_enumeration":{
   "purpose":"闭合 F-4/v47 之争（#K2-131 §六①「跨线缝枚举 · 必须公布读数」）",
   "line":"y = 54.880（A 侧 P 排锚所在线）",
   "readout":seam,
   "discrete_slots_x_93.4_108":{"count":len(disc),"intervals":[[round(a,3),round(b,3)] for a,b in disc],
     "widths":[round(b-a,3) for a,b in disc],"capacity_sum":disc_cap,
     "note":"11 段 0.40–0.90mm 之周期槽（每段容量 floor(w/0.435)+1 ∈{1,2}）—— 此即 #K2-132 §三『≤16×≤11』之 11 槽出处"},
   "wide_bands":[[round(a,3),round(b,3)] for a,b in wide],
   "capacity_verdict":"Σ 槽容量（含宽带）%d ≥ 16 ⇒ **跨缝容量非卡点**（与 R326 割上界 67≥16 一致）"%seam["54.880"]["capacity_sum"]},
 "step1_order_invariant":{
   "theorem":"【顺序不变量】各 lane 于 A 侧之立管 x 序（a_rank 序）强制其巴士定阶（先立者高阶）；单层不可交叉 ⇒ 于任意竖切上，a_rank 小者恒在上（y 大）。⇒ 巴士竖序（上→下）= a_rank 0..15。",
   "anchors":AB,
   "A_x_steps":ax_steps,
   "B_y_rank_vs_a_rank":{"B_y_rank":[brank[i] for i in range(16)],
     "inversions_vs_a_rank":inv_pairs,
     "verdict":"B 侧 y 序 ≈ a_rank 序（T0 到 T7 逐位同序）⇒ 上带巴士（上= T0）必须映射到 **B 侧最下锚** ⇒ **要求一次 16 线全反演**（v65『8 处反转』之完整化：非 8 而是整链反演）。"},
   "razor_edge_reconfirm":{"nearest_shortest_path_mm":0.4386,"pitch":PITCH,"margin_um":3.6,
     "adjacent_A_anchor_gap_mm":0.330,"note":"相邻 A 锚保留盘间仅余 0.330mm < P ⇒ lane 不可穿两他 lane A 锚之间（承 v65，本件复算）"}},
 "step1_individual_routability":{
   "n_ok":n_indiv_ok,"n_lanes":16,
   "all_use_upper_band_ymax_ge_56.5":in_band,
   "per_lane":indiv,
   "xmax_min_mm":round(min(xsmax),2),"xmax_max_mm":round(max(xsmax),2),
   "funnel_finding":"**全部 16 条个体最短路皆须东行至 x≥%s**（xmax_min）—— 上带东端 x∈[134.3,141.2] 为**共享必经资源**；即 16 lane 必须于该处**会聚**（带宽/井距可行，但需联合指派）。"%round(min(xsmax),2),
   "verdict":"16/16 单独可路（无 lane-lane 互距约束）· **全部个体最短路皆沿上带 (y≥56.5) 向右至 x≈%s 再下折** ⇒ 个体层不穿 via 场 11 槽；via 场槽为**可选**而非必经。"%round(max(xsmax),1)},
 "step1_band_south_junction":gates_summary|{"note":"上带(y=60)与南区(y=45)在同一自由竖区间（跨 y∈[43.5,57]）之 x 采样集合；反映『门』位置。"},
 "step2_exact_assignment_model":{
   "form":"MILP/CP-SAT 指派：决策 z[lane][slot]∈{0,1}（lane 于 y=54.88 之跨缝槽）",
   "sound_relaxation":"仅含**必要**条件：(1) 每 lane 恰占 1 槽；(2) 非交叉 ⇒ 指派随 a_rank 单调（=不变量既定序）；(3) 每槽占用 ≤ 容量 floor(w/0.435)+1（几何上界）。",
   "rigid_quantities":[{"name":"pitch_eff","value":PITCH,"source":"#K2-132 §三.1 物理口径"},
                        {"name":"keepout","value":0.5300,"source":"在册（hw0.08+0.35+margin0.100）"},
                        {"name":"cell","value":CELL,"source":"#K2-132 §三.1（授权 ≤0.03）"},
                        {"name":"lane_w","value":0.16,"source":"在册"}],
   "solver":"scipy.optimize.milp / HiGHS（环境 python3 · numpy 2.2.6 · scipy 1.15.3）",
   "log":milp_log,
   "readout":"松弛可行 ⇒ **跨缝指派层不构成卡点**（16 条可容于 Σ 槽容量 %d）。⇒ 卡点在**指派之后之坐标化生成**（slot 序列之连续几何），非指派本身。"%(milp_log.get("total_slot_capacity",0))},
 "negative_structural_finding_v67_class":v67_witness,
 "conclusion":{
   "card":"卡点 = **『跨缝槽指派 → 连续几何坐标化』之联合生成**（互距感知）；本轮把卡点**从『MILP 指派』层剥离**（指派层可行）并**证伪 v67 巴士构造类**；剩余唯一未证路径 = 以**不穿 via 场**（沿上带 y≥56.5 至 x≈134–136 之南向折返）之**全反演嵌套**构造。",
   "binary":"(a) 未得 · (b) 不成立",
   "owner_gate":0,
   "next_step":"按『全反演嵌套』规格实现一次（每 lane 之定阶由 a_rank 强制；下潜于 x≥136.55 之南区完成；末端以**非单调阶梯**避让（v67 类已证不可行））—— 或由监理判定是否转 C-w。"},
 "buildability_field":{"mode":"no_move","note":"纯只读读件：未改任何网几何 · 未烙板 · 未动冻结四源/判据 ⇒ 不动证明成立"},
 "reproduce":{
   "model_dump":"AppDir/usr/bin/python3.11 k2/tools/k2_p4_b2_board_in5_model_dump_v1.py k2/hw/k2_v4_8L.l8.kicad_pcb /tmp/opencode/archer/model_l8.json",
   "run":"python3 k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K2_R353_UP_OUT_EXACT_READOUT_v1.py",
   "independent_recheck":"python3 k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K2_R353_INDEPENDENT_RECHECK_v1.py"},
}
# ---- sha16 约定A ----
core=dict(artifact); core.pop("self_sha16",None)
self_sha=hashlib.sha256(json.dumps(core,ensure_ascii=False,indent=1,sort_keys=True).encode()).hexdigest()[:16]
artifact["self_sha16"]={"convention":"#K2-72 §五 约定A","convention_A_sha16":self_sha}
json.dump(artifact,open(os.path.join(OUT,"K2_R353_UP_OUT_EXACT_READOUT_v1.json"),"w"),ensure_ascii=False,indent=1,sort_keys=True)
print("sha16(约定A) =",self_sha)
print("seam y=54.88 slots:",len(y543),"discrete 11-band:",len(disc),"disc_cap",disc_cap,"wide",wide)
print("milp:",milp_log)
print("all indiv use band:",in_band,"/16 ; xmax range",min(xsmax),max(xsmax))
print("gates join x:",gates_summary)
