import pcbnew, math, json
from collections import defaultdict
BOARD='/home/fila/jqdDev_2025/ic_hw/k2/k2_v4.kicad_pcb'
bd=pcbnew.LoadBoard(BOARD)
fps={fp.GetReference():fp for fp in bd.GetFootprints()}
# gather all pads w/ ref,pos,radius(min dim/2)
allpads=[]
for ref,fp in fps.items():
    for p in fp.Pads():
        sz=p.GetSize(); c=p.GetPosition()
        allpads.append((ref,p.GetNumber(),c.x/1e6,c.y/1e6,min(sz.x,sz.y)/2e6, max(sz.x,sz.y)/2e6))
viols=[]
MINCLR=0.10
n=len(allpads)
for i in range(n):
    r1,no1,x1,y1,ra1,rb1=allpads[i]
    if r1=='U6': continue
    for j in range(n):
        if j<=i: continue
        r2,no2,x2,y2,ra2,rb2=allpads[j]
        if r2=='U6': continue
        d=math.hypot(x1-x2,y1-y2)
        need=ra1+ra2+MINCLR
        if d<need: viols.append((r1,no1,r2,no2,round(d,3),round(need,3)))
print('NON-U6 pad-pad violations:', len(viols))
for v in viols[:15]: print('  ',v)
# U6 vs all (already done): recompute summary
u6viols=[]
u6pad_geo=[(p.GetNumber(),p.GetPosition().x/1e6,p.GetPosition().y/1e6,p.GetSize().x/2e6) for p in fps['U6'].Pads()]
for ref,fp in fps.items():
    if ref=='U6': continue
    for p in fp.Pads():
        sz=p.GetSize(); c=p.GetPosition()
        pr=min(sz.x,sz.y)/2e6; pcx,pcy=c.x/1e6,c.y/1e6
        for (no,ux,uy,ur) in u6pad_geo:
            d=math.hypot(pcx-ux,pcy-uy)
            if d<ur+pr+MINCLR: u6viols.append((ref,p.GetNumber(),no,round(d,3),round(ur+pr+MINCLR,3)))
print('U6-vs-others pad violations:', len(u6viols))
for v in sorted(set(u6viols))[:20]: print('  ',v)
json.dump({'non_u6':viols,'u6_vs_others':sorted(set(u6viols))}, open('/tmp/opencode/eco_clearance_report.json','w'), indent=1)
