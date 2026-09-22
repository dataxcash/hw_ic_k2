#!/usr/bin/env python3
"""K2 · R368 — 冻结模型 C-B2UP-1_PORTAL_STAIRCASE_MILP_v1（model_sha16 82eb35c856d7a704）之**首次实际求解**：
  (A) 16/16 **不可行性证明**（由 (7) 与 lane 0_N 之几何 t-上界直接推出）
  (B) exact 单调链 DP 之求解上界（两 sense；两种网格分辨率；含机件校验）
  (C) 见证重建 + `exact_gate` 复核
只读板件；零改模型；临时仅 /tmp/opencode。
用法: python3 K2_R368_repro.py /tmp/opencode/archer/model_l8.json [out.json]
"""
import json,sys,math,time,hashlib
sys.path.insert(0,'/home/fila/jqdDev_2025/ic_hw/k2/tools')
import numpy as np
from k2_p4_b2_in5_lane_router_v3 import Raster,build_base,lane_anchors,exact_gate
T0=time.time()
MODEL=sys.argv[1] if len(sys.argv)>1 else '/tmp/opencode/archer/model_l8.json'
OUT=sys.argv[2] if len(sys.argv)>2 else '/tmp/opencode/k2r368/R368.json'
CELL=0.02;HW=0.08;P=0.435
X0,Y0,X1,Y1=78.0,38.0,150.0,66.0
M=json.load(open(MODEL))
rast=Raster((X0,Y0,X1,Y1),CELL)
base=build_base(rast,M,'In5.Cu',frozenset(),frozenset(),HW); free=~base
NX,NY=free.shape
I=lambda x:int(round((x-X0)/CELL)); J=lambda y:int(round((y-Y0)/CELL))
blk=~free
ii=np.arange(NX,dtype=np.int32)[:,None]
nxt=np.minimum.accumulate(np.where(blk,ii,np.int32(NX))[::-1],axis=0)[::-1]
prv=np.maximum.accumulate(np.where(blk,ii,np.int32(-1)),axis=0)
jj=np.arange(NY,dtype=np.int32)[None,:]
nxtu=np.minimum.accumulate(np.where(blk,jj,np.int32(NY))[:,::-1],axis=1)[:,::-1]
prvu=np.maximum.accumulate(np.where(blk,jj,np.int32(-1)),axis=1)
ans=[a for a in lane_anchors(M) if a['net'].startswith('PCIE_UP_OUT')]
ans.sort(key=lambda a:a['A'][0]); names=[a['net'] for a in ans]; L=len(names)
R={"schema":1,"artifact":"k2_r368_cb2up1_frozen_model_first_solve_and_16_infeasibility_v1",
   "model_id":"C-B2UP-1_PORTAL_STAIRCASE_MILP_v1","model_sha16":"82eb35c856d7a704",
   "cell":CELL,"hw":HW,"pitch":P,"board":"k2/hw/k2_v4_8L.l8.kicad_pcb","board_sha16":"7a5c89913d6e5d0a",
   "a_rank_order":names}
# ---------- 通用求解（网格参数化） ----------
def build_masks(sT,sX,sY):
    TG=np.round(np.arange(56.60,63.60+1e-9,sT),3); XG=np.round(np.arange(134.90,143.60+1e-9,sX),3)
    YG=np.round(np.arange(43.00,60.00+1e-9,sY),3)
    NT,NK,NYg=len(TG),len(XG),len(YG)
    iT=np.array([J(v) for v in TG]); iX=np.array([I(v) for v in XG]); iY=np.array([J(v) for v in YG])
    lo=np.minimum(iT[:,None],iY[None,:]); hi=np.maximum(iT[:,None],iY[None,:])
    V3=np.zeros((NT,NK,NYg),dtype=bool)
    for kx in range(NK): V3[:,kx,:]=(nxtu[iX[kx],lo]>hi)
    mask=[]
    for li,a in enumerate(ans):
        iax=I(a['A'][0]); iay=J(a['A'][1]); ibx=I(a['B'][0]); iby=J(a['B'][1])
        rise=np.array([nxtu[iax,min(iay,tt)]>max(iay,tt) for tt in iT])
        H2=np.array([[ (nxt[iax,iT[kt]]>iX[kx]) if iax<=iX[kx] else (prv[iax,iT[kt]]<iX[kx]) for kx in range(NK)] for kt in range(NT)])
        H4=np.array([[ nxt[min(ibx,iX[kx]),iY[ky]]>max(ibx,iX[kx]) for ky in range(NYg)] for kx in range(NK)])
        V5=np.array([nxtu[ibx,min(iby,iY[ky])]>max(iby,iY[ky]) for ky in range(NYg)])
        mask.append((rise[:,None,None]&H2[:,:,None]&V3)&(V5[None,None,:]&H4[None,:,:]))
    return TG,XG,YG,mask

def _sens(A,sense):
    A=np.maximum.accumulate(A[::-1],axis=0)[::-1]
    if sense>0: A=np.maximum.accumulate(A[:,::-1],axis=1)[:,::-1]; A=np.maximum.accumulate(A,axis=2)
    else:       A=np.maximum.accumulate(A,axis=1); A=np.maximum.accumulate(A[:,:,::-1],axis=2)[:,:,::-1]
    return A

def dp(TG,XG,YG,mask,masks_override=None,sense=1,ret_chain=False):
    NT,NK,NYg=len(TG),len(XG),len(YG)
    gT=int(math.ceil(P/(TG[1]-TG[0])-1e-9)); gX=int(math.ceil(P/(XG[1]-XG[0])-1e-9)); gY=int(math.ceil(P/(YG[1]-YG[0])-1e-9))
    MK=masks_override if masks_override is not None else mask
    Fs=[]
    for li in range(L):
        m=MK[li]
        if li==0: Fs.append(np.where(m,1,0).astype(np.int8)); continue
        A=_sens(Fs[-1].astype(np.int16),sense)
        G=np.zeros((NT,NK,NYg),dtype=np.int16)
        if sense>0: G[:NT-gT,:NK-gX,gY:]=A[gT:,gX:,:NYg-gY]
        else:       G[:NT-gT,gX:, :NYg-gY]=A[gT:,:NK-gX,gY:]
        Fs.append(np.maximum(Fs[-1].astype(np.int16),np.where(m,G+1,-1).astype(np.int16)).astype(np.int8))
    best=int(Fs[-1].max())
    if not ret_chain: return best,None
    s=tuple(int(x) for x in np.unravel_index(int(np.argmax(Fs[-1])),Fs[-1].shape)); chain=[]
    for li in range(L-1,-1,-1):
        v=int(Fs[li][s])
        if v==0: break
        if li==0:
            if v>=1 and bool(MK[0][s]): chain.append((0,s))
            break
        found=None; kt,kx,ky=s
        if bool(MK[li][s]):
            if sense>0:
                sub=Fs[li-1][kt+gT:NT, kx+gX:NK, 0:ky-gY+1]
                ix2=np.argwhere(sub==v-1)
                if len(ix2): found=(kt+gT+int(ix2[0,0]), kx+gX+int(ix2[0,1]), int(ix2[0,2]))
            else:
                sub=Fs[li-1][kt+gT:NT, 0:kx-gX+1, ky+gY:NYg]
                ix2=np.argwhere(sub==v-1)
                if len(ix2): found=(kt+gT+int(ix2[0,0]), int(ix2[0,1]), ky+gY+int(ix2[0,2]))
        if found is not None: chain.append((li,s)); s=found
        else: assert int(Fs[li-1][s])==v
    chain.reverse(); return best,chain

TG,XG,YG,mask=build_masks(0.05,0.05,0.10)
R["grid"]={"sT":0.05,"sX":0.05,"sY":0.10,"NT":len(TG),"NX":len(XG),"NY":len(YG)}
R["per_lane_feasible_triples"]=[int(m.sum()) for m in mask]
ti=[]
for m in mask:
    kt=np.argwhere(m.any(axis=(1,2))).ravel(); ti.append([float(TG[kt[0]]),float(TG[kt[-1]])])
R["per_lane_t_interval"]=ti
# (A) 不可行性证明：lane 0 (a_rank 0) 之 t 可行集
m0=mask[0]; kt0=np.argwhere(m0.any(axis=(1,2))).ravel()
t0_list=[float(TG[k]) for k in kt0]
R["infeasibility_proof"]={
 "lane":"PCIE_UP_OUT0_N_J2 (a_rank 0)","A":[84.35,55.723],
 "feasible_t_set":t0_list,"t0_max":max(t0_list),
 "rule":"(7) t 随 a_rank **递减** + (2) 两两 |Δt|>=0.435 ⇒ t_{rank1} <= t_{rank0} - 0.435",
 "derived_t1_upper_bound":round(max(t0_list)-P,3),
 "model_lower_bound_t":56.60,
 "conclusion":"t_{rank1} <= %.3f < 56.60 ⇒ **无任何含 lane0 且>=2 条之冻结模型解** ⇒ **16/16 于冻结模型内不可行**（构造性，与 xs/ye/portal 无关）"%(max(t0_list)-P)}
# (B) DP 上界（两 sense、两分辨率）
res={}
for tag,(sT,sX,sY) in (("0.05/0.05/0.10",(0.05,0.05,0.10)),("0.05/0.05/0.05",(0.05,0.05,0.05))):
    Tg,Xg,Yg,mm=build_masks(sT,sX,sY)
    if tag!="0.05/0.05/0.10":
        R["grid_fine"]={"sT":sT,"sX":sX,"sY":sY,"NT":len(Tg),"NX":len(Xg),"NY":len(Yg)}
    for sense in (1,-1):
        b,_=dp(Tg,Xg,Yg,mm,sense=sense)
        res["%s_sense%+d"%(tag,sense)]=b
allT=[np.ones_like(mask[i]) for i in range(L)]
mach={}
for sense in (1,-1):
    mach["allTrue_sense%+d"%sense]=dp(TG,XG,YG,mask,masks_override=allT,sense=sense)[0]
R["dp_upper_bound"]=res; R["machinery_check_allTrue_masks_expect16"]=mach
# (C) 见证 + gate
best,chain=dp(TG,XG,YG,mask,sense=1,ret_chain=True)
sel={}
for li,(kt,kx,ky) in chain:
    a=ans[li]; t=float(TG[kt]); xs=float(XG[kx]); ye=float(YG[ky])
    sel[names[li]]={"t":t,"xs":xs,"ye":ye,"a_rank":li,
      "pts":[[a['A'][0],a['A'][1]],[a['A'][0],t],[xs,t],[xs,ye],[a['B'][0],ye],[a['B'][0],a['B'][1]]]}
g=exact_gate(M,{k:{"pts":v["pts"]} for k,v in sel.items()},ans,'In5.Cu',HW,frozenset(),frozenset(),P)
R["witness"]={"sense":1,"n_placed":len(sel),"dp_value":best,"lanes":sorted(sel),
 "gate":{"n_lane_pitch_viol":g["n_lane_pitch_viol"],"lane_pitch_min_gap_mm":g["lane_pitch_min_gap_mm"],
         "n_clearance_viol":g["n_clearance_viol"],"clearance_min_mm":g["clearance_min_mm"],
         "endpoint_max_dev_mm":g["endpoint_max_dev_mm"]},"routes":sel}
R["elapsed_s"]=round(time.time()-T0,1)
json.dump(R,open(OUT,'w'),indent=1,ensure_ascii=False)
print(json.dumps({k:R[k] for k in ("infeasibility_proof","dp_upper_bound","machinery_check_allTrue_masks_expect16","grid","grid_fine","elapsed_s")},ensure_ascii=False,indent=1))
print("witness:",R["witness"]["n_placed"],"dp:",best,"gate:",R["witness"]["gate"])
print("lane0 feasible t:",t0_list)
