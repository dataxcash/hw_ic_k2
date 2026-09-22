#!/usr/bin/env python3
"""K2 · 收口窗口 项2 —— 依 v55 清单将 C-w 搬迁**落件**：l8 -> l9（文本级 S-expr 编辑 · 只增删指定对象）。
不改冻结四源（本脚本只读 l8、写 l9 新实例）。"""
import re,sys,json,hashlib,math,uuid
SRC='/home/fila/jqdDev_2025/ic_hw/k2/hw/k2_v4_8L.l8.kicad_pcb'
DST='/home/fila/jqdDev_2025/ic_hw/k2/hw/k2_v4_8L.l9.kicad_pcb'
NECK=(93.0,44.0,112.0,58.0)
inN=lambda x,y: NECK[0]-1e-9<=x<=NECK[2]+1e-9 and NECK[1]-1e-9<=y<=NECK[3]+1e-9
t=open(SRC,encoding='utf-8').read()
def blocks(text,key):
    out=[];pat='('+key;i=0
    while True:
        i=text.find(pat,i)
        if i<0: break
        k=i;d=0;ins=False
        while k<len(text):
            c=text[k]
            if ins:
                if c=='"' and text[k-1]!='\\': ins=False
            elif c=='"': ins=True
            elif c=='(': d+=1
            elif c==')':
                d-=1
                if d==0: break
            k+=1
        out.append((i,k+1,text[i:k+1])); i=k+1
    return out
def parse_seg(b):
    m=re.search(r'\(start ([\d.-]+) ([\d.-]+)\)\s*\(end ([\d.-]+) ([\d.-]+)\)',b)
    lay=re.search(r'\(layer "([^"]+)"\)',b); net=re.search(r'\(net "([^"]*)"\)',b)
    w=re.search(r'\(width ([\d.]+)\)',b)
    if not(m and lay and net): return None
    return dict(x1=float(m.group(1)),y1=float(m.group(2)),x2=float(m.group(3)),y2=float(m.group(4)),
                layer=lay.group(1),net=net.group(1),w=float(w.group(1)) if w else None)
def parse_via(b):
    m=re.search(r'\(at ([\d.-]+) ([\d.-]+)\)',b); net=re.search(r'\(net "([^"]*)"\)',b)
    lay=re.findall(r'\(layers "([^"]+)" "([^"]+)"\)',b)
    if not(m and net and lay): return None
    return dict(x=float(m.group(1)),y=float(m.group(2)),net=net.group(1),layers=list(lay[0]))
segB=blocks(t,'segment'); viaB=blocks(t,'via')
SEG=[(i,j,parse_seg(b)) for i,j,b in segB]; VIA=[(i,j,parse_via(b)) for i,j,b in viaB]
print('l8: segments',len(SEG),' vias',len(VIA))
# ---- 待删 ----
DEL=[]
def mark_seg(net,layer,pts):
    for i,j,s in SEG:
        if not s or s['net']!=net or s['layer']!=layer: continue
        for (ax,ay),(bx,by) in [(pts[0],pts[1]),(pts[1],pts[0])]:
            if abs(s['x1']-ax)<0.01 and abs(s['y1']-ay)<0.01 and abs(s['x2']-bx)<0.01 and abs(s['y2']-by)<0.01:
                DEL.append((i,j,s,'seg')); return True
    return False
def mark_via(net,x,y,tol=0.01):
    for i,j,v in VIA:
        if v and v['net']==net and abs(v['x']-x)<tol and abs(v['y']-y)<tol:
            DEL.append((i,j,v,'via')); return True
    return False
# v55 清单之窗内对象（坐标取 R331 全表）
R331=json.load(open('/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K2_R331_CW_RELOCATION_OBJECT_LIST_v1.json'))
nA='DS320_STRAP_B_ADDR1_7-0'
for s in R331['objects'][nA]['in5_segments_in_neck']:
    mark_seg(nA,'In5.Cu',[(s[0],s[1]),(s[2],s[3])])
for v in R331['objects'][nA]['in5_vias']: mark_via(nA,v[0],v[1])
nB='DS320_STRAP_B_ADDR0_15-8'
for v in R331['objects'][nB]['in5_vias']:
    if inN(v[0],v[1]): mark_via(nB,v[0],v[1])
nC='I2C1_SDA'
for s in R331['objects'][nC]['in5_segments_in_neck']:
    mark_seg(nC,'In5.Cu',[(s[0],s[1]),(s[2],s[3])])
for v in R331['objects'][nC]['in5_vias']:
    if inN(v[0],v[1]): mark_via(nC,v[0],v[1])
nP='PERSTA#'
for s_ in R331['objects'][nP]['in5_segments_in_neck']:
    mark_seg(nP,'In5.Cu',[(s_[0],s_[1]),(s_[2],s_[3])])
P337=json.load(open('/home/fila/jqdDev_2025/ic_hw/k2/pm_gate/artifacts/k2_v4/P6_execution/P6_OPEN_READINESS/K2_R337_CW_PERSTA_DESTINATION_ROUTE_v1.json'))
print('to delete:',len(DEL))
for i,j,o,k in DEL: print('  DEL',k,o)
# ---- 待加 ----
ST=json.load(open('/tmp/opencode/k2r135/stubs.json')); NC=json.load(open('/tmp/opencode/k2r135b/nc_fixed.json'))
FR=json.load(open('/tmp/opencode/k2r135b/final_reloc.json'))
ADD=[]
def seg(net,layer,p,q,w=0.1):
    ADD.append(('segment',net,layer,p,q,w))
def via(net,x,y,top,bot,size=0.35,drill=0.2):
    ADD.append(('via',net,(x,y),(top,bot),size,drill))
na=ST['netA_in2_direct']['polyline_simplified']
for k in range(len(na)-1): seg('DS320_STRAP_B_ADDR1_7-0','In2.Cu',tuple(na[k]),tuple(na[k+1]),0.1)
via('DS320_STRAP_B_ADDR0_15-8',FR['netB']['site'][0],FR['netB']['site'][1],'F.Cu','B.Cu')
for k in range(len(FR['netB']['stub_top_polyline'])-1): seg('DS320_STRAP_B_ADDR0_15-8','F.Cu',tuple(FR['netB']['stub_top_polyline'][k]),tuple(FR['netB']['stub_top_polyline'][k+1]),0.1)
for k in range(len(FR['netB']['stub_bot_polyline'])-1): seg('DS320_STRAP_B_ADDR0_15-8','B.Cu',tuple(FR['netB']['stub_bot_polyline'][k]),tuple(FR['netB']['stub_bot_polyline'][k+1]),0.1)
via('I2C1_SDA',NC['site'][0],NC['site'][1],'In5.Cu','B.Cu')
for k in range(len(NC['stub_top_polyline'])-1):
    p,q=NC['stub_top_polyline'][k],NC['stub_top_polyline'][k+1]
    if math.dist(p,q)>1e-6: seg('I2C1_SDA','In5.Cu',tuple(p),tuple(q),0.1)
for k in range(len(NC['stub_bot_polyline'])-1): seg('I2C1_SDA','B.Cu',tuple(NC['stub_bot_polyline'][k]),tuple(NC['stub_bot_polyline'][k+1]),0.1)
_pp=P337['route_pts']
for k in range(len(_pp)-1):
    p=tuple(_pp[k]); q=tuple(_pp[k+1])
    if math.dist(p,q)>1e-6: seg('PERSTA#','In5.Cu',p,q,0.1)
print('to add:',len(ADD))
def uu(*parts): return str(uuid.uuid5(uuid.NAMESPACE_DNS,'k2-r373-cw-relocation:'+'|'.join(str(x) for x in parts)))
def fmt_seg(net,layer,p,q,w):
    return ('\t(segment\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(width %s)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'
            %(p[0],p[1],q[0],q[1],w,layer,net,uu('seg',net,layer,p[0],p[1],q[0],q[1])))
def fmt_via(net,pt,lp,size,drill):
    return ('\t(via\n\t\t(at %s %s)\n\t\t(size %s)\n\t\t(drill %s)\n\t\t(layers "%s" "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'
            %(pt[0],pt[1],size,drill,lp[0],lp[1],net,uu('via',net,lp[0],lp[1],pt[0],pt[1])))
# ---- 执行：先收集删除区间，再重建文本 ----
i,_=[b[0] for b in segB][0],None
segs_range=(min(i for i,j,o in SEG), max(j for i,j,o in SEG))
out=[];last=0
ranges=sorted([(i,j) for i,j,o,k in DEL])
for i,j in ranges:
    out.append(t[last:i]); last=j
out.append(t[last:])
newt=''.join(out)
# 追加新对象：插在最后一个 segment 之后
segs2=blocks(newt,'segment'); anchor=segs2[-1][1]
adds=''.join(fmt_seg(*a[1:]) if a[0]=='segment' else fmt_via(*a[1:]) for a in ADD)
newt=newt[:anchor]+'\n'+adds.rstrip('\n')+'\n'+newt[anchor:]
open(DST,'w',encoding='utf-8').write(newt)
print('written',DST)
print('l9 segments',newt.count('(segment'),'vias',newt.count('(via\n'))
print('l9 sha256[:16]',hashlib.sha256(open(DST,'rb').read()).hexdigest()[:16])
print('l8 sha256[:16]',hashlib.sha256(open(SRC,'rb').read()).hexdigest()[:16])
