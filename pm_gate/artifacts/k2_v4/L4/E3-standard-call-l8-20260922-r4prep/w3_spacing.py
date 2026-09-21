#!/usr/bin/env python3
"""3W 前置测量（R4 闸 · ENG 只交测量 · 无 verdict）：l8 In5 上 16 条 UP_OUT 走线之**同层异网最小间距**。
只读解析 .kicad_pcb · 走廊 bbox [82,41,146,60] · 用法: python3 w3_spacing.py <board> [out.json]"""
import re,sys,json,math
t=open(sys.argv[1],encoding='utf-8').read()
segs=[]
for blk in re.split(r'\n\s*\(segment\n', t)[1:]:
    blk=blk.split('\n\t)')[0]
    m=re.search(r'\(start ([\-\d\.]+) ([\-\d\.]+)\)',blk); n=re.search(r'\(end ([\-\d\.]+) ([\-\d\.]+)\)',blk)
    lay=re.search(r'\(layer "([^"]+)"\)',blk); net=re.search(r'\(net "([^"]+)"\)',blk)
    if not(m and n and lay and net) or lay.group(1)!='In5.Cu': continue
    x1,y1,x2,y2=float(m.group(1)),float(m.group(2)),float(n.group(1)),float(n.group(2))
    if not(82<=min(x1,x2) and max(x1,x2)<=146 and 41<=min(y1,y2) and max(y1,y2)<=60): continue
    segs.append((net.group(1),x1,y1,x2,y2))
def d_ps(px,py,ax,ay,bx,by):
    dx,dy=bx-ax,by-ay; L=dx*dx+dy*dy
    if L==0: return math.hypot(px-ax,py-ay)
    tt=max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L)); return math.hypot(px-(ax+tt*dx),py-(ay+tt*dy))
def d_ss(a,b):
    ax,ay,bx,by=a; cx,cy,dx_,dy_=b
    if (max(ax,bx)<min(cx,dx_)-1e-9 or max(cx,dx_)<min(ax,bx)-1e-9 or max(ay,by)<min(cy,dy_)-1e-9 or max(cy,dy_)<min(ay,by)-1e-9):
        return min(d_ps(ax,ay,cx,cy,dx_,dy_),d_ps(bx,by,cx,cy,dx_,dy_),d_ps(cx,cy,ax,ay,bx,by),d_ps(dx_,dy_,ax,ay,bx,by))
    # 相交或包围 ⇒ 0
    def cr(o,p,q): return (p[0]-o[0])*(q[1]-o[1])-(p[1]-o[1])*(q[0]-o[0])
    A=(ax,ay);B=(bx,by);C=(cx,cy);D=(dx_,dy_)
    if cr(A,B,C)*cr(A,B,D)<=0 and cr(C,D,A)*cr(C,D,B)<=0: return 0.0
    return min(d_ps(ax,ay,cx,cy,dx_,dy_),d_ps(bx,by,cx,cy,dx_,dy_),d_ps(cx,cy,ax,ay,bx,by),d_ps(dx_,dy_,ax,ay,bx,by))
UP=lambda n: n.startswith('PCIE_UP_OUT')
ups=[s for s in segs if UP(s[0])]; oth=[s for s in segs if not UP(s[0])]
best=(9e9,None,None); besto=(9e9,None)  # 他网最近
for s in ups:
    for o in oth:
        dd=d_ss(s[1:],o[1:])
        if dd<besto[0]: besto=(dd,(s[0],o[0]))
# 16 网内部互距（异网）
for i in range(len(ups)):
    for j in range(i+1,len(ups)):
        if ups[i][0]==ups[j][0]: continue
        dd=d_ss(ups[i][1:],ups[j][1:])
        if dd<best[0]: best=(dd,(ups[i][0],ups[j][0]))
out={"board":sys.argv[1],"layer":"In5.Cu","scope_bbox":[82,41,146,60],
     "n_upout_segs":len(ups),"n_other_segs":len(oth),
     "min_lane_to_lane_mm":round(best[0],4),"min_pair":best[1],
     "min_lane_to_othernet_mm":round(besto[0],4),"min_pair_other":besto[1],
     "note":"ENG 测量件 · 无 verdict 字段 · 3W 阈值归 SPEC/监理"}
print(json.dumps(out,ensure_ascii=False,indent=1))
if len(sys.argv)>2: json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
