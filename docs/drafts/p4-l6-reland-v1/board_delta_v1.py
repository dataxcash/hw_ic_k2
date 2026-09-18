#!/usr/bin/env python3
"""board_delta_v1.py — l5 vs 现行生成器产物 的逐件 delta 取证器（只读；pcbnew）。
用法: AppDir/usr/bin/python3.11 board_delta_v1.py <boardA> <boardB>
输出: JSON（nets/fps/tracks/zones/draw 五类的 A/B 计数 + only_A / only_B / diff 名单）。
"""
import sys, pcbnew, collections, json
def mm(v): return round(pcbnew.ToMM(v),4)
def pad_sig(p):
    ls=p.GetLayerSet()
    return (str(p.GetNumber()), int(p.GetShape()), mm(p.GetSize().x), mm(p.GetSize().y),
            mm(p.GetPosition().x-p.GetParent().GetPosition().x), mm(p.GetPosition().y-p.GetParent().GetPosition().y),
            mm(p.GetDrillSize().x), ls.FmtHex()[:12])
def board(path):
    b=pcbnew.LoadBoard(path); o={}
    o['nets']=sorted(str(n) for n in b.GetNetInfo().NetsByName().keys())
    o['fps']={}
    for fp in b.GetFootprints():
        o['fps'][str(fp.GetReference())]=(str(fp.GetFPID().GetLibNickname())+':'+str(fp.GetFPID().GetLibItemName()),
            mm(fp.GetPosition().x), mm(fp.GetPosition().y), fp.GetOrientationDegrees(), fp.GetLayer(),
            tuple(sorted(pad_sig(p) for p in fp.Pads())))
    segs=[]
    for t in b.GetTracks():
        if t.Type()==pcbnew.PCB_VIA_T:
            segs.append(('via', t.GetPosition().x, t.GetPosition().y, t.GetDrillValue(), t.GetNetname()))
        else:
            segs.append(('seg', str(t.GetLayerName()), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y, t.GetWidth(), t.GetNetname()))
    o['tracks']=sorted(map(str,segs))
    z=[]
    for zz in b.Zones():
        try:
            fl=str(zz.GetLayerSet().FmtHex())[:12]
        except Exception: fl='?'
        nfill=0
        try:
            for lid in zz.GetLayerSet().Seq():
                nfill+=zz.GetFilledPolysList(lid).OutlineCount()
        except Exception: pass
        z.append((fl, zz.GetIsRuleArea(), zz.IsFilled(), nfill, str(zz.GetNetname()), zz.Outline().OutlineCount(), sum(zz.Outline().COutline(i).PointCount() for i in range(zz.Outline().OutlineCount()))))
    o['zones']=z
    o['draw']=sorted(collections.Counter(str(x.GetClass())+'@'+x.GetLayerName() for x in b.GetDrawings()).items())
    return o
if __name__=='__main__':
    a=board(sys.argv[1]); b=board(sys.argv[2]); out={}
    for k in ['nets','fps','tracks','zones','draw']:
        va,vb=a[k],b[k]
        if k=='nets': out[k]=dict(A=len(va),B=len(vb),only_A=sorted(set(va)-set(vb))[:20],only_B=sorted(set(vb)-set(va))[:20])
        elif k=='fps':
            ka,kb=set(va),set(vb)
            out[k]=dict(A=len(ka),B=len(kb),only_A=sorted(ka-kb),only_B=sorted(kb-ka),
                        diff=sorted(r for r in ka&kb if va[r]!=vb[r]))
        else:
            sa,sb=set(va),set(vb)
            out[k]=dict(A=len(va),B=len(vb),only_A_n=len(sa-sb),only_B_n=len(sb-sa),
                        only_A=sorted(sa-sb)[:6],only_B=sorted(sb-sa)[:6])
    print(json.dumps(out,ensure_ascii=False,indent=1))
