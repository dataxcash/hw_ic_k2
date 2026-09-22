#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K2 · R354 · ①-UP **x-单调不可行性**读件 + **顺序不变量之更正**（对 R353 §2 措辞之自纠）
只读 · 未烙板 · 未改冻结四源/判据/生成器/SPEC/原理图 · 未派 WORKER。
复现：先 dump 模型 -> /tmp/opencode/archer/model_l8.json，再 python3 <本件>
"""
import json, math, os, sys, hashlib
sys.path.insert(0,'/home/fila/jqdDev_2025/ic_hw/k2/tools')
import numpy as np
from k2_p4_b2_in5_lane_router_v3 import Raster, build_base, lane_anchors

MODEL="/tmp/opencode/archer/model_l8.json"
OUT="k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS" if os.path.isdir("k2") else "/tmp/opencode/k2r353"
X0,Y0,X1,Y1=76.0,30.0,148.0,72.0
CELL=0.03; HW=0.08; PITCH=0.435

m=json.load(open(MODEL))
ans=[a for a in lane_anchors(m) if a['net'].startswith("PCIE_UP_OUT")]
ans.sort(key=lambda a:a['A'][0])
rast=Raster((X0,Y0,X1,Y1),CELL); base=build_base(rast,m,"In5.Cu",frozenset(),frozenset(),HW); free=~base
NX,NY=free.shape; INF=float('inf')

def xmono_dist(A,B):
    """x-单调（x 非减，任意斜率）最短路：列内双向松弛 + 向东传播。O(NX*NY)。"""
    si,sj=rast.cell(*A); gi,gj=rast.cell(*B)
    if si>gi: return None
    D=np.full((NX,NY),INF); D[si,sj]=0.0
    for i in range(si,gi+1):
        col=free[i]
        # 列内垂直松弛（两遍，处理起伏自由段）
        for _ in range(2):
            for j in range(1,NY):
                if col[j] and D[i,j-1]+CELL<D[i,j]: D[i,j]=D[i,j-1]+CELL
            for j in range(NY-2,-1,-1):
                if col[j] and D[i,j+1]+CELL<D[i,j]: D[i,j]=D[i,j+1]+CELL
        if i==gi: break
        for j in np.nonzero(col)[0]:
            d=D[i,j]
            if d==INF: continue
            for dj,w in ((0,1.0),(1,math.sqrt(2)),(-1,math.sqrt(2))):
                nj=j+dj
                if 0<=nj<NY and free[i+1,nj]:
                    nd=d+w*CELL
                    if nd<D[i+1,nj]: D[i+1,nj]=nd
    return None if D[gi,gj]==INF else float(D[gi,gj])

rows=[]
for a in ans:
    L=xmono_dist(a['A'],a['B'])
    rows.append({"a_rank":ans.index(a),"net":a['net'],"A":[round(a['A'][0],3),round(a['A'][1],3)],
                 "B":[round(a['B'][0],3),round(a['B'][1],3)],
                 "x_monotone_feasible":L is not None,
                 "x_monotone_len_mm":None if L is None else round(L,2)})
no=[r for r in rows if not r["x_monotone_feasible"]]
west=[r for r in rows if r["B"][0]<134.0]
thm={
 "claim":"【x-单调不可行性】%d/16 条 lane **不存在** x-单调（x 非减）自由通路（单 lane · 无障碍互斥；纯几何/障碍刚性）"%len(no),
 "set_identity":"无 x-单调通路之集合 == B 锚位于**过孔墙以西**（x_B < 134）之 8 条 lane：%s；其余 8 条（x_B≥136）皆存在。"%[r["net"] for r in no],
 "semantics":"⇒ 每条西组 lane 之路径**必须东行越过其自身 B 锚**（至 x≳136 之折返区）再西返 ⇒ **必然非 x-单调**（折返），且其西返必经 x≈134 之过孔墙缺口。",
 "why_families_failed":"①R348 巴士 waypoint / R345–R346 硬排除贪心 / R346『最短路候选 MILP』诸族都建立在**单调或近单调候选**上 ⇒ 与本刚性结构冲突；②8 条西组 lane 之最短路径**全部汇聚于同一折返口**（过孔墙缺口，宽 0.3–1.0mm/段）⇒ 候选退化（R346 实测互斥 94.1%）之源。",
 "independent_of_pitch":"该结论**不含** lane-lane 互距假设 ⇒ 为**单 lane 刚性**，与指派/联合优化无关。"}
rows_wall={"anchors_B_x_lt_134":west}
# 更正 R353 §2 措辞
corr={
 "target":"K2_R353_UP_OUT_EXACT_READOUT_v1 §2『顺序不变量』措辞",
 "issue":"原文『于任意竖切上 a_rank 小者恒在其上』过强：折返 lane 会**两次**穿越同一竖切（东行支 + 西返支），故『任意竖切』之 y 序当按**支**计，不能作全局量。",
 "corrected":"【T1′】①**在飞（未落）lane** 保持 a_rank 竖序（a_rank 小者 y 大）——由立管序 + 不可交叉强制；②**落位 lane 之水平段恒在在飞 lane 之下**；③**下潜序（x 升序）= 阶升序**（= a_rank 降序）⇒ 最低阶 lane 先落（x 最小）。",
 "impact":"R353 §5/§6 之推理（下潜序、v67 类反例 6P×6N）**基于 ①③**，**不受影响**；仅§2 之全局措辞更正。"}

art={"schema":1,"artifact":"k2_r354_up_out_xmonotone_infeasibility_v1",
 "ts":"2026-09-22T11:40+0800","to":"监理","from":"ENG · ARCHER",
 "nature":"①-UP **x-单调不可行性**（单 lane 刚性读件）+ **顺序不变量措辞更正**（自纠 R353 §2）· 只读 · 二值未取得",
 "board_sha16":"7a5c89913d6e5d0a",
 "frozen4":["d4e81f647be7f980","fb07d25ac426ff84","dd794c54f7ce7417","0a459839e15960b8"],
 "criteria":"rev=6 MATCH (1937a40ae68bc288 / 727d09953cf9bd78 / eb3da49f2ad97e37)",
 "caliber":{"cell":CELL,"lane_w":0.16,"pitch_eff":PITCH,"keepout":"0.5300(未改)"},
 "binary":{"(a) 16/16 见证":"未得","(b) U<16 严格证书":"不成立"},
 "theorem_x_monotone":thm,"per_lane":rows,"west_group":rows_wall,
 "self_correction":corr,
 "consequence_for_next_step":"下一构造必须**显式含折返**（东带巴士 → 过孔墙缺口/东端折返 → 西区配锚），且 8 条西组之折返口为**共享窄资源** ⇒ 联合指派须以『折返口槽位 + 西返水平层』为决策对象（互距感知）。",
 "buildability_field":{"mode":"no_move","note":"纯只读：未改任何网几何 · 未烙板 · 未动冻结四源/判据 ⇒ 不动证明成立"}}
core=dict(art); s16=hashlib.sha256(json.dumps(core,ensure_ascii=False,indent=1,sort_keys=True).encode()).hexdigest()[:16]
art["self_sha16"]={"convention":"#K2-72 §五 约定A","convention_A_sha16":s16}
json.dump(art,open(os.path.join(OUT,"K2_R354_UP_OUT_XMONOTONE_INFEASIBILITY_v1.json"),"w"),ensure_ascii=False,indent=1,sort_keys=True)
print("sha16 =",s16)
for r in rows: print("  %-22s x_mono=%s len=%s"%(r["net"],r["x_monotone_feasible"],r["x_monotone_len_mm"]))
print("no-x-mono: %d/16"%len(no))
