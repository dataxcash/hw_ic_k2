#!/usr/bin/env python3
"""K2 · R371 —— C-w 补件 ① 之复算脚本（三段 · 顺序执行）：
  S1 = N-A (DS320_STRAP_B_ADDR1_7-0) In5->In2 转层替代走线
  S2 = N-B (DS320_STRAP_B_ADDR0_15-8) 贯通孔最小代价搬迁 + 双侧 stub
  S3 = N-C (I2C1_SDA) In5<->B.Cu 孔最小代价搬迁（碎片受限种子）+ 双侧 stub
只读板件 · 临时仅 /tmp/opencode · 不改任何冻结件。"""

# ===== S1 =====
import json,sys,math
sys.path.insert(0,'/home/fila/jqdDev_2025/ic_hw/k2/tools')
import numpy as np
from k2_p4_b2_in5_lane_router_v3 import Raster,is_lane,eff,HOLE_CLR
from scipy.sparse.csgraph import dijkstra
from scipy.sparse import csr_matrix
M=json.load(open('/tmp/opencode/archer/model_l8.json'))
CELL=0.02;HW=0.08;NECK=(93.0,44.0,112.0,58.0);BB=(78.0,38.0,150.0,66.0)
LANE=lambda n: is_lane(n)
inN=lambda p: NECK[0]-1e-9<=p[0]<=NECK[2]+1e-9 and NECK[1]-1e-9<=p[1]<=NECK[3]+1e-9
def rast_of(layer,movable):
    r=Raster(BB,CELL); bad=np.zeros((r.NX,r.NY),bool)
    for s in M['segs'][layer]:
        if s[5] in movable or LANE(s[5]): continue
        r.seg(bad,s[0],s[1],s[2],s[3],HW+s[4]+eff(s[5]))
    for v in M['vias']:
        if layer not in v['layers'] or v['net'] in movable or LANE(v['net']): continue
        r.cir(bad,v['x'],v['y'],HW+max(v['r']+eff(v['net']),v['drill']+HOLE_CLR))
    for p in M['pads']:
        if p['net'] in movable or LANE(p['net']): continue
        if layer not in p['layers'] and not p['pth']: continue
        b=p['box']; r.rect(bad,b[0],b[1],b[2],b[3],HW+eff(p['net']))
        if p['pth'] and p.get('drill'): r.cir(bad,p['cx'],p['cy'],HW+p['drill']+HOLE_CLR)
    for ra in M['ruleareas']:
        if not (ra['no_tracks'] and layer in ra['layers']): continue
        for poly in ra['polys']: r.poly(bad,poly)
    return r,~bad
def route(layer,movable,p1,p2):
    r,free=rast_of(layer,movable); A=free.copy()
    I=lambda x:int(round((x-r.X0)/r.step)); J=lambda y:int(round((y-r.Y0)/r.step))
    for p in (p1,p2): A[I(p[0]),J(p[1])]=True
    ii,jj=np.nonzero(A); idx=-np.ones(A.shape,np.int32); idx[ii,jj]=np.arange(len(ii))
    rr=[];cc=[];vv=[]
    for dx,dy,w in ((1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.4142),(1,-1,1.4142),(-1,1,1.4142),(-1,-1,1.4142)):
        a=ii+dx;b=jj+dy; m=(a>=0)&(a<A.shape[0])&(b>=0)&(b<A.shape[1])
        ok=np.zeros(len(ii),bool); ok[m]=A[a[m],b[m]]
        rr.append(idx[ii[ok],jj[ok]]); cc.append(idx[a[ok],b[ok]]); vv.append(np.full(int(ok.sum()),float(w)))
    G=csr_matrix((np.concatenate(vv),(np.concatenate(rr),np.concatenate(cc))),shape=(len(ii),len(ii)))
    s=int(idx[I(p1[0]),J(p1[1])]); g=int(idx[I(p2[0]),J(p2[1])])
    d,pred=dijkstra(G,directed=True,indices=s,return_predecessors=True)
    if not np.isfinite(d[g]): return None
    path=[];cur=g
    while cur!=s and cur>=0: path.append([round(r.X0+ii[cur]*r.step,3),round(r.Y0+jj[cur]*r.step,3)]); cur=pred[cur]
    path.append([round(r.X0+ii[s]*r.step,3),round(r.Y0+jj[s]*r.step,3)]); path.reverse()
    return {"layer":layer,"len_mm":round(float(d[g])*r.step,2),"n":len(path),"pts":path}
def simp(p,eps=0.02):
    o=[p[0]]
    for q in p[1:]:
        while len(o)>1:
            a=o[-2];b=o[-1]; vx,vy=b[0]-a[0],b[1]-a[1]; wx,wy=q[0]-a[0],q[1]-a[1]
            L=math.hypot(vx,vy) or 1
            if abs(vx*wy-vy*wx)/L<eps and vx*wx+vy*wy>0: o.pop()
            else: break
        o.append(q)
    return [[round(x,3),round(y,3)] for x,y in o]
R={}
# N-A
netA='DS320_STRAP_B_ADDR1_7-0'
rA=route('In2.Cu',frozenset([netA]),(83.650,50.280),(99.850,60.780))
R['netA_in2_direct']={"len_mm":rA['len_mm'],"n":rA['n'],"polyline_simplified":simp(rA['pts'])}
print('N-A In2 direct len=%.2f n=%d pts=%d'%(rA['len_mm'],rA['n'],len(R['netA_in2_direct']['polyline_simplified'])))
# N-C: via -> (92.98,48.06); In5 stub from port (92.5,51.84); B.Cu stub from new site to original (102.5,52.138)
netC='I2C1_SDA'; siteC=(92.98,48.06)
rc1=route('In5.Cu',frozenset([netC]),(92.5,51.84),siteC)
rc2=route('B.Cu',frozenset([netC]),siteC,(102.5,52.138))
R['netC']={"new_via_site":list(siteC),"dist_from_old_mm":round(math.hypot(siteC[0]-102.5,siteC[1]-52.138),3),
  "stub_In5":None if not rc1 else {"len_mm":rc1['len_mm'],"polyline_simplified":simp(rc1['pts'])},
  "stub_B_Cu":None if not rc2 else {"len_mm":rc2['len_mm'],"polyline_simplified":simp(rc2['pts'])}}
print('N-C In5 stub:',None if not rc1 else '%.2fmm'%rc1['len_mm'],' B.Cu stub:',None if not rc2 else '%.2fmm'%rc2['len_mm'])
# N-B: via -> (105.04,43.98); F.Cu stub from pad U6.FJ28 centre (104.69,51.79); B.Cu stub from old (105.125,52.09)
netB='DS320_STRAP_B_ADDR0_15-8'; siteB=(105.04,43.98)
rb1=route('F.Cu',frozenset([netB]),(104.69,51.79),siteB)
rb2=route('B.Cu',frozenset([netB]),siteB,(105.125,52.09))
R['netB']={"new_via_site":list(siteB),"dist_from_old_mm":round(math.hypot(siteB[0]-105.125,siteB[1]-52.09),3),
  "stub_F_Cu":None if not rb1 else {"len_mm":rb1['len_mm'],"polyline_simplified":simp(rb1['pts'])},
  "stub_B_Cu":None if not rb2 else {"len_mm":rb2['len_mm'],"polyline_simplified":simp(rb2['pts'])}}
print('N-B F.Cu stub:',None if not rb1 else '%.2fmm'%rb1['len_mm'],' B.Cu stub:',None if not rb2 else '%.2fmm'%rb2['len_mm'])
json.dump(R,open('/tmp/opencode/k2r135/stubs.json','w'),ensure_ascii=False,indent=1)
for k,v in R.items():
    if isinstance(v,dict):
        for kk,vv in v.items():
            if isinstance(vv,dict) and 'polyline_simplified' in vv:
                print(' ',k,kk,'n_pts=',len(vv['polyline_simplified']),vv['polyline_simplified'][:4])

# ===== S2 / S3 =====
#!/usr/bin/env python3
"""K2 · C-w 补件 ① —— **最小代价搬迁**：为 N-B(贯通孔) / N-C(In5<->B.Cu 孔) 求
   新孔位 = argmin [ geodesic(top 层网铜→站点) + geodesic(bot 层网铜→站点) ]，约束：窗内禁止 · 各跨层合法。
   同时输出可施工折线（stub）。只读。"""
import json,sys,math,time
sys.path.insert(0,'/home/fila/jqdDev_2025/ic_hw/k2/tools')
import numpy as np
from k2_p4_b2_in5_lane_router_v3 import Raster,is_lane,eff,HOLE_CLR
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
M=json.load(open('/tmp/opencode/archer/model_l8.json'))
CELL=0.02;HW=0.08;NECK=(93.0,44.0,112.0,58.0);BB=(78.0,38.0,150.0,66.0)
LANE=lambda n: is_lane(n)
inN=lambda p: NECK[0]-1e-9<=p[0]<=NECK[2]+1e-9 and NECK[1]-1e-9<=p[1]<=NECK[3]+1e-9
T0=time.time()
def rast_of(layer,movable,ban_neck=False):
    r=Raster(BB,CELL); bad=np.zeros((r.NX,r.NY),bool)
    for s in M['segs'][layer]:
        if s[5] in movable or LANE(s[5]): continue
        r.seg(bad,s[0],s[1],s[2],s[3],HW+s[4]+eff(s[5]))
    for v in M['vias']:
        if layer not in v['layers'] or v['net'] in movable or LANE(v['net']): continue
        r.cir(bad,v['x'],v['y'],HW+max(v['r']+eff(v['net']),v['drill']+HOLE_CLR))
    for p in M['pads']:
        if p['net'] in movable or LANE(p['net']): continue
        if layer not in p['layers'] and not p['pth']: continue
        b=p['box']; r.rect(bad,b[0],b[1],b[2],b[3],HW+eff(p['net']))
        if p['pth'] and p.get('drill'): r.cir(bad,p['cx'],p['cy'],HW+p['drill']+HOLE_CLR)
    for ra in M['ruleareas']:
        if not (ra['no_tracks'] and layer in ra['layers']): continue
        for poly in ra['polys']: r.poly(bad,poly)
    if ban_neck: r.rect(bad,NECK[0],NECK[1],NECK[2],NECK[3],0.0)
    return r,~bad
def geom_dist(r,free,seed_mask):
    ii,jj=np.nonzero(free); idx=-np.ones(free.shape,np.int32); idx[ii,jj]=np.arange(len(ii))
    nn=len(ii); SS=nn  # super source
    rr=[];cc=[];vv=[]
    for dx,dy,w in ((1,0,1.),(-1,0,1.),(0,1,1.),(0,-1,1.),(1,1,1.4142),(1,-1,1.4142),(-1,1,1.4142),(-1,-1,1.4142)):
        a=ii+dx;b=jj+dy; m=(a>=0)&(a<free.shape[0])&(b>=0)&(b<free.shape[1])
        ok=np.zeros(nn,bool); ok[m]=free[a[m],b[m]]
        rr.append(idx[ii[ok],jj[ok]]); cc.append(idx[a[ok],b[ok]]); vv.append(np.full(int(ok.sum()),w))
    rs=np.nonzero(seed_mask&free)
    nseed=len(rs[0])
    rr.append(np.full(nseed,SS,dtype=np.int64)); cc.append(idx[rs[0],rs[1]].astype(np.int64)); vv.append(np.zeros(nseed))
    G=csr_matrix((np.concatenate(vv),(np.concatenate(rr).astype(np.int64),np.concatenate(cc).astype(np.int64))),shape=(nn+1,nn+1))
    d,pred=dijkstra(G,directed=True,indices=SS,return_predecessors=True)
    dd=np.full(free.shape,np.inf); dd[ii,jj]=d[:nn]*r.step
    return dd,pred,idx,ii,jj,SS,nn
def path_from(pred,idx,ii,jj,SS,site):
    cur=int(idx[site]); out=[]
    while cur!=SS and cur>=0:
        out.append([round(float(ii[cur]*CELL+BB[0]),3),round(float(jj[cur]*CELL+BB[1]),3)])
        cur=int(pred[cur])
    out.reverse(); return out
def move(net,via,del_pts,ban_neck=False):
    movable=frozenset([net]); top,bot=via['top'],via['bot']
    RS={};FR={}
    for L in M['layers']:
        bn=ban_neck and L in (top,bot)
        RS[L],FR[L]=rast_of(L,movable,ban_neck=bn)
    r0=RS['In5.Cu']; I=lambda x:int(round((x-r0.X0)/r0.step)); J=lambda y:int(round((y-r0.Y0)/r0.step))
    # seeds per endpoint layer (net copper minus moved via and minus del_pts)
    from scipy.ndimage import label as _lab
    def seeds(L):
        m=np.zeros(FR[L].shape,bool)
        for s in M['segs'][L]:
            if s[5]!=net: continue
            p1,p2=(round(s[0],2),round(s[1],2)),(round(s[2],2),round(s[3],2))
            if p1 in del_pts or p2 in del_pts or ((p1,p2) in del_pts): continue
            RS[L].seg(m,s[0],s[1],s[2],s[3],0.03)
        RS[L].cir(m,via['x'],via['y'],max(via['r'],via['drill']/2)+0.01)   # include the moved via's pad
        lab,_=_lab(m,np.ones((3,3),bool))
        ci,cj=I(via['x']),J(via['y'])
        v=int(lab[ci,cj])
        f=(lab==v) if v>0 else m
        return f
    sm_top=seeds(top); sm_bot=seeds(bot)
    dt,pt,it,itx,ity,St,nn_t=geom_dist(RS[top],FR[top],sm_top)
    db,pb,ib,ibx,iby,Sb,nn_b=geom_dist(RS[bot],FR[bot],sm_bot)
    def path(pred,idx,ii,jj,SS,site):
        cur=int(idx[site]); out=[]
        while cur!=SS and cur>=0:
            out.append([round(float(ii[cur]*CELL+BB[0]),3),round(float(jj[cur]*CELL+BB[1]),3)]); cur=int(pred[cur])
        out.reverse(); return out
    # legality: via keepout free on every spanned layer
    rad=HW+max(via['r']+eff(net),via['drill']+HOLE_CLR); di=int(math.ceil(rad/r0.step))
    from scipy.ndimage import binary_dilation
    leg=np.ones(FR[top].shape,bool)
    for L in via['layers']: leg&=~binary_dilation(~FR[L],structure=np.ones((2*di+1,2*di+1),bool))
    # candidate: outside neck, connected both ends
    ii,jj=np.nonzero(leg)
    xs=r0.X0+ii*r0.step; ys=r0.Y0+jj*r0.step
    out_nk=~((xs>=NECK[0])&(xs<=NECK[2])&(ys>=NECK[1])&(ys<=NECK[3]))
    ok=out_nk&np.isfinite(dt[ii,jj])&np.isfinite(db[ii,jj])
    ii,jj=ii[ok],jj[ok]
    if len(ii)==0: return None
    cost=dt[ii,jj]+db[ii,jj]
    k=int(np.argmin(cost)); si,sj=int(ii[k]),int(jj[k])
    site=(round(r0.X0+si*r0.step,3),round(r0.Y0+sj*r0.step,3))
    return {"site":site,"cost_mm":round(float(cost[k]),3),
            "dist_top_mm":round(float(dt[si,sj]),3),"dist_bot_mm":round(float(db[si,sj]),3),
            "top":top,"bot":bot,"n_cand":int(len(ii)),
            "stub_top":path(pt,it,itx,ity,St,(si,sj)),"stub_bot":path(pb,ib,ibx,iby,Sb,(si,sj)),
            "seed_top_cells":int(sm_top.sum()),"seed_bot_cells":int(sm_bot.sum())}
# --- N-B: through via F.Cu->B.Cu, delete the via only ---
netB='DS320_STRAP_B_ADDR0_15-8'
VB=[v for v in M['vias'] if v['net']==netB and inN((v['x'],v['y']))][0]
rB=move(netB,VB,frozenset())
print('   B stub_toplayer=%s botlayer=%s'%(rB['top'],rB['bot']))
print("N-B:",json.dumps({k:v for k,v in rB.items() if k!='stub_top'},ensure_ascii=False))
netC='I2C1_SDA'
VC=[v for v in M['vias'] if v['net']==netC and inN((v['x'],v['y']))][0]
delC=frozenset([(round(s[0],2),round(s[1],2)) for s in M['segs']['In5.Cu'] if s[5]==netC and (inN((s[0],s[1])) or inN((s[2],s[3])))]) | \
     frozenset([(round(s[2],2),round(s[3],2)) for s in M['segs']['In5.Cu'] if s[5]==netC and (inN((s[0],s[1])) or inN((s[2],s[3])))])
rC=move(netC,VC,delC,ban_neck=True)
print("N-C:",json.dumps({k:v for k,v in rC.items() if k!='stub_top'},ensure_ascii=False))
json.dump({"netB":rB,"netC":rC},open('/tmp/opencode/k2r135b/mc.json','w'),ensure_ascii=False,indent=1)
print("elapsed",round(time.time()-T0,1),"s")

# ===== S3 (corrected) =====
import json,math,sys
sys.path.insert(0,'/home/fila/jqdDev_2025/ic_hw/k2/tools')
import numpy as np
src=open('reloc_mc2.py').read().split("# --- N-B")[0]
exec(src)
netC='I2C1_SDA'; VC=[v for v in M['vias'] if v['net']==netC and inN((v['x'],v['y']))][0]
r0=RS if False else None
movable=frozenset([netC])
RS={};FR={}
for L in M['layers']: RS[L],FR[L]=rast_of(L,movable)
# In5: ban neck, seed = In5 copper outside neck connected to port (92.5,51.84)
RS['In5.Cu'],FR['In5.Cu']=rast_of('In5.Cu',movable,ban_neck=True)
from scipy.ndimage import label as _lab
def frag_mask(L,pt,pts_pad=None):
    m=np.zeros(FR[L].shape,bool)
    for s in M['segs'][L]:
        if s[5]!=netC: continue
        if L=='In5.Cu' and (inN((s[0],s[1])) or inN((s[2],s[3]))): continue   # delete in-neck In5 segs
        RS[L].seg(m,s[0],s[1],s[2],s[3],0.03)
    ci,cj=int(round((pt[0]-RS[L].X0)/RS[L].step)),int(round((pt[1]-RS[L].Y0)/RS[L].step))
    lab,_=_lab(m,np.ones((3,3),bool)); v=int(lab[ci,cj])
    return (lab==v) if v>0 else m
sm_in5=frag_mask('In5.Cu',(92.5,51.84))
sm_bcu=frag_mask('B.Cu',(VC['x'],VC['y']))
print('seed In5 cells(west fragment, out-neck):',int(sm_in5.sum()),' seed B.Cu cells:',int(sm_bcu.sum()))
dt,pt,it,itx,ity,St,_=geom_dist(RS['In5.Cu'],FR['In5.Cu'],sm_in5)
db,pb,ib,ibx,iby,Sb,_=geom_dist(RS['B.Cu'],FR['B.Cu'],sm_bcu)
from scipy.ndimage import binary_dilation
rad=HW+max(VC['r']+eff(netC),VC['drill']+HOLE_CLR); di=int(math.ceil(rad/RS['In5.Cu'].step))
leg=np.ones(FR['In5.Cu'].shape,bool)
for L in VC['layers']: leg&=~binary_dilation(~FR[L],structure=np.ones((2*di+1,2*di+1),bool))
ii,jj=np.nonzero(leg); X=RS['In5.Cu'].X0+ii*RS['In5.Cu'].step; Y=RS['In5.Cu'].Y0+jj*RS['In5.Cu'].step
outk=~((X>=NECK[0])&(X<=NECK[2])&(Y>=NECK[1])&(Y<=NECK[3]))
ok=outk&np.isfinite(dt[ii,jj])&np.isfinite(db[ii,jj]); ii,jj=ii[ok],jj[ok]
cost=dt[ii,jj]+db[ii,jj]; k=int(np.argmin(cost)); si,sj=int(ii[k]),int(jj[k])
site=[round(float(RS['In5.Cu'].X0+si*RS['In5.Cu'].step),3),round(float(RS['In5.Cu'].Y0+sj*RS['In5.Cu'].step),3)]
def path(pred,idx,ii,jj,SS,sp):
    cur=int(idx[sp]);o=[]
    while cur!=SS and cur>=0: o.append([round(float(ii[cur]*0.02+BB[0]),3),round(float(jj[cur]*0.02+BB[1]),3)]);cur=int(pred[cur])
    o.reverse();return o
st=path(pt,it,itx,ity,St,(si,sj)); sb=path(pb,ib,ibx,iby,Sb,(si,sj))
def rdp(p,eps=0.06):
    if len(p)<3: return p
    d=lambda q,a,b: (lambda L: math.hypot(q[0]-a[0],q[1]-a[1]) if L<1e-9 else abs((b[0]-a[0])*(q[1]-a[1])-(b[1]-a[1])*(q[0]-a[0]))/L)(math.hypot(b[0]-a[0],b[1]-a[1]))
    def rec(i,j):
        if j<=i+1: return [i,j]
        k=max(range(i+1,j),key=lambda t:d(p[t],p[i],p[j]))
        return rec(i,k)[:-1]+rec(k,j) if d(p[k],p[i],p[j])>eps else [i,j]
    I=rec(0,len(p)-1); return [p[i] for i in I]
S=rdp(st);Sb=rdp(sb)
L1=round(sum(math.dist(st[i],st[i+1]) for i in range(len(st)-1)),2)
L2=round(sum(math.dist(sb[i],sb[i+1]) for i in range(len(sb)-1)),2)
print("N-C corrected: site",site,"cost=%.2f"%(L1+L2),"In5 stub %.2fmm"%L1,"B.Cu stub %.2fmm"%L2,"cands",len(ii))
print("  in5 poly",S); print("  bcu poly",Sb)
json.dump({"site":site,"cost_mm":round(L1+L2,2),"stub_top_mm":L1,"stub_bot_mm":L2,"stub_top_polyline":S,"stub_bot_polyline":Sb,
           "n_cand":int(len(ii)),"seed_cells":[int(sm_in5.sum()),int(sm_bcu.sum())]},open('/tmp/opencode/k2r135b/nc_fixed.json','w'),ensure_ascii=False,indent=1)
