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
